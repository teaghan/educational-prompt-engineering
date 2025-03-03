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

        self.init_prompt = self.initial_prompt_template()
        self.system_prompt = None
        self.message_history = []

    def initial_prompt_template(self) -> PromptTemplate:
        """Generates the initial prompt template for the LLM."""
        return PromptTemplate("""
## Your Task

You are an experienced teacher who excels at writing report card comments.

Your task is to write PERSONALIZED, THOUGHTFUL, AND UNIQUE report card comments for each student.

DO NOT WRITE GENERIC COMMENTS. MAKE EACH COMMENT PERSONALIZED AND UNIQUE TO THE STUDENT.
                              
The comments should be based on the student data and instructions provided by the user. 

## User Instructions

{instructions}

EACH COMMENT SHOULD HAVE A MINIMUM OF {sentence_range[0]} AND A MAXIMUM OF {sentence_range[1]} SENTENCES.

### Comment Examples

{comment_examples}

### Output Table Specifications

{output_description}

## Student Data

{student_data}

## Data Description

{input_description}

## Response Format

Your response should start with a consideration of the instructions and data provided by the user. 

Consider your approach to writing the comments as well as the content, LENGTH, and style of the comments.

Then list ALL OF THE STUDENTS that you will be writing comments for and how many comments for each student you will be writing.

Following that, write "## REPORT CARD COMMENTS\n\n" and then write the comments for each student.

The comments should be formatted as a markdown table with headers. For example:

| Student Name | Comment |
|--------------|---------|
| John Doe     | Comment text... |
| Jane Smith    | Comment text... |
                              
When writing the comments, make sure they are PERSONALIZED, THOUGHTFUL, AND ALIGNED WITH THE COMMENT EXAMPLES PROVIDED.
                              
After providing the comments, write "---\n\n" and then ask the user for feedback on whether the comments meet the requirements or if any adjustments are needed.
""")
    def chat_system_prompt(self, instructions, comment_examples, sentence_range, 
                                    output_description, student_data, 
                                    input_description) -> str:
        """Generates the system prompt template for the chatbot LLM."""
        return f"""
## Your Task

You are an experienced teacher who excels at writing report card comments.

Your task is to write PERSONALIZED, THOUGHTFUL, AND UNIQUE report card comments for each student.

DO NOT WRITE GENERIC COMMENTS. MAKE EACH COMMENT PERSONALIZED AND UNIQUE TO THE STUDENT.
                              
The comments should be based on the student data and instructions provided by the user. 

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

## Data Description

{input_description}

## Response Format

Every response you provide, INCLUDING THE RESPONSES TO THE USER'S FEEDBACK, should start with a consideration of the instructions, data, and feedback provided by the user. 

Consider your approach to writing the comments as well as the content, NUMBER OF SENTENCES, and style of the comments.

Then list ALL OF THE STUDENTS that you will be writing comments for and how many comments for each student you will be writing.

Following that, write "## REPORT CARD COMMENTS\n\n" and then write the comments for each student.

The comments should be formatted as a markdown table with headers. For example:

| Student Name | Comment |
|--------------|---------|
| John Doe     | Comment text... |
| Jane Smith    | Comment text... |
                              
After providing the comments, write "---\n\n" and then ask the user for feedback on whether the comments meet the requirements or if any adjustments are needed.

This formatting should be followed for every response you provide, INCLUDING THE RESPONSES TO THE USER'S FEEDBACK.
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

    def get_initial_comments(self, instructions, comment_examples,sentence_range, 
                         output_description, student_data, input_description) -> str:
        """
        Generates guided notes based on video content and student details.

        Args:
            topic (str): The topic of the lesson
            video_transcript (str): Transcript of the video content
            learning_objective (str): Learning objective of the lesson
            avg_age (str): Average age of students
            student_descr (str): Description of the student group
        Returns:
            str: The generated guided notes
        """
        instructions = instructions if instructions else "No specific instructions provided."
        comment_examples = comment_examples if comment_examples else "No comment examples provided."
        output_description = output_description if output_description else "One column for the student name and one column for the comment."
        input_description = input_description if input_description else "The student data formatting is self-explanatory."

        self.system_prompt = self.chat_system_prompt(instructions, comment_examples, sentence_range, 
                                                output_description, student_data, 
                                                input_description)
        self.message_history.append(ChatMessage(role="system", content=self.system_prompt))

        entire_response = self.llm.predict(
            self.init_prompt,
            instructions=instructions,
            comment_examples=comment_examples,
            sentence_range=sentence_range,
            output_description=output_description,
            student_data=student_data,
            input_description=input_description
        )

        self.message_history.append(ChatMessage(role="assistant", content=entire_response))

        comments, feedback_request = self.extract_comments(entire_response)

        return entire_response, comments, comments + "\n\n" + feedback_request

    def user_input(self, message):

        if self.system_prompt is None:
            raise ValueError("System prompt is not set. Please call get_initial_comments first.")

        # Add user prompt to history
        self.message_history.append(ChatMessage(role="user", content=message))
        # Prompt LLM with history
        entire_response = self.llm.chat(self.message_history).message.content

        comments, feedback_request = self.extract_comments(entire_response)
        # Add response to history
        self.message_history.append(ChatMessage(role="assistant", content=entire_response))
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
        
        
