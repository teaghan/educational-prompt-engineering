import os
import pandas as pd
from io import BytesIO
from llama_index.core.llms import ChatMessage
from llama_index.core.prompts import PromptTemplate
from llama_index.llms.openai import OpenAI
from llama_index.llms.gemini import Gemini

openai_api_key = os.environ["OPENAI_API_KEY"]
gemini_api_key = os.environ["GEMINI_API_KEY"]

class ReportCardCommentor:
    """
    A class designed to interact with an LLM (Large Language Model) to generate personalized
    report card comments for students based on provided data and user instructions.
    """
    def __init__(self, model="gpt-4o-mini"):

        if 'gpt' in model:
            self.llm = OpenAI(model=model, api_key=openai_api_key)
        elif 'gemini' in model:
            self.llm = Gemini(model=model, api_key=gemini_api_key)
        else:
            raise ValueError(f"Invalid model: {model}")

        self.message_history = [ChatMessage(role="system", content=self.get_system_prompt())]
    
    def get_system_prompt(self) -> str:
        """Generates the system prompt template for the chatbot LLM."""
        return f"""
## Your Role

You are an experienced teacher who excels at writing report card comments.

## Your Task

The user will provide you with student data,instructions for the report card comments, and (potentially) examples of high quality comments.

Your task is to use the student data and apply the user's instructions to write PERSONALIZED, THOUGHTFUL, AND UNIQUE report card comments for each student.

You will NEVER WRITE GENERIC COMMENTS.

If the user provides examples of high quality comments, use them to guide the writing of your comments.

## Response Format

Every response you provide, INCLUDING THE RESPONSES TO THE USER'S FEEDBACK, should start with a consideration of the instructions, data, and feedback provided by the user (if provided). 

Consider your approach to writing the comments as well as the content, number of sentences per comment, and style of the comments.

Then list ALL OF THE STUDENTS that you will be writing comments for and how many comments for each student you will be writing.

Following that, write "## REPORT CARD COMMENTS\n\n" and then write the comments for each student.

The comments should be formatted as a markdown table with column headers (defined by the user in "Output Table Specifications"). 

For example:

| Student Name | Comment |
|--------------|---------|
| John Doe     | Comment text... |
| Jane Smith    | Comment text... |
                              
After providing the comments, write "---\n\n" and then ask the user for feedback on whether the comments meet the requirements or if any adjustments are needed.

This formatting should be followed for every response you provide, INCLUDING THE RESPONSES TO THE USER'S FEEDBACK.
"""
    def initial_prompt_template(self, instructions, comment_examples, sentence_range, 
                                    output_description, student_data, 
                                    input_description) -> str:
        """Generates the initial prompt template for the LLM."""
        return f"""
## User Instructions

{instructions}

EACH COMMENT SHOULD HAVE A MINIMUM OF {sentence_range[0]} AND A MAXIMUM OF {sentence_range[1]} SENTENCES.

### High Quality Comment Examples

USE THESE EXAMPLES TO GUIDE THE WRITING OF YOUR COMMENTS:

{comment_examples}

### Output Table Specifications

{output_description}

The comments should be written in a way that is ALIGNED WITH THE COMMENT EXAMPLES (if provided).                              

## Student Data

{student_data}

### Data Description

{input_description}
"""
    
    def extract_comments(self, message):
        try:
            # Split from the last occurrence of "## REPORT CARD COMMENTS"
            comments_part = message.split("## REPORT CARD COMMENTS", 1)[1]
            # Split from the last occurrence of "---"
            comments_section = comments_part.rsplit("---", 1)[0].strip()
            final_question = comments_part.rsplit("---", 1)[1].strip()
        except:
            lines = message.strip().split('\n')
            comments_section = '\n'.join(lines[:-1])
            final_question = lines[-1]
        return comments_section, final_question

    def get_initial_comments(self, instructions, comment_examples, sentence_range, 
                             output_description, student_data, input_description) -> str:
        """
        Generates report card comments based on student data and user instructions.

        Args:
            instructions (str): Instructions for the report card comments
            comment_examples (str): Examples of high quality comments
            sentence_range (list): The range of sentences per comment
            output_description (str): The description of the output table
            student_data (str): The student data
            input_description (str): The description of the student data
        Returns:
            str: The generated report card comments
        """
        instructions = instructions if instructions else "No specific instructions provided."
        comment_examples = comment_examples if comment_examples else "No comment examples provided."
        output_description = output_description if output_description else "One column for the student name and one column for the comment."
        input_description = input_description if input_description else "The student data formatting is self-explanatory."

        # Create the initial prompt
        prompt = self.initial_prompt_template(instructions, 
                                              comment_examples, 
                                              sentence_range, 
                                              output_description, 
                                              student_data, 
                                              input_description)
        print(prompt)
        self.message_history.append(ChatMessage(role="user", content=prompt))
        # Generate the initial comments
        entire_response = self.llm.chat(self.message_history).message.content
        # Add the initial response to the message history
        self.message_history.append(ChatMessage(role="assistant", content=entire_response))
        # Extract the comments and feedback request
        comments, feedback_request = self.extract_comments(entire_response)
        # Return the initial response, comments, and feedback request
        return entire_response, comments, comments + "\n\n" + feedback_request

    def user_input(self, message):
        """
        Processes user input and generates a response.

        Args:
            message (str): The user's input message
        Returns:
            str: The generated response
        """
        # Add user prompt to history
        self.message_history.append(ChatMessage(role="user", content=message))
        # Prompt LLM with history
        entire_response = self.llm.chat(self.message_history).message.content
        # Extract the comments and feedback request
        comments, feedback_request = self.extract_comments(entire_response)
        # Add the response to the message history
        self.message_history.append(ChatMessage(role="assistant", content=entire_response))
        # Return the response, comments, and feedback request
        return entire_response, comments, comments + "\n\n" + feedback_request

    
    def produce_list(self, comments):
        """Convert markdown table to CSV format."""
        # Split the table into lines and remove empty lines
        lines = [line.strip() for line in comments.split('\n') if line.strip()]
        
        # Remove the header separator line (|----|-----|)
        lines = [line for line in lines if not line.startswith('|-')]
        
        # Process each line into CSV format
        csv_lines = []
        for line in lines:
            if line.startswith('|'):
                # Remove leading/trailing |
                line = line.strip('|')
                # Split by |, strip whitespace, and quote fields
                fields = [f'"{field.strip()}"' for field in line.split('|')]
                csv_lines.append(','.join(fields))
        
        # Join all lines with newlines
        return '\n'.join(csv_lines)

    def get_excel_bytes(self, csv_string):
        # Convert CSV string to DataFrame
        df = pd.read_csv(BytesIO(csv_string.encode()), quotechar='"')
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Report Comments')
            # Auto-adjust columns' width
            worksheet = writer.sheets['Report Comments']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                )
                worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2
        
        output.seek(0)
        return output.getvalue()
        
        
