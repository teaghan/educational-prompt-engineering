import streamlit as st
import os
from llama_index.core.llms import ChatMessage
from llama_index.llms.openai import OpenAI

openai_api_key = os.environ["OPENAI_API_KEY"]

def format_student_data(student_data, csv_description):
    """
    This function generates a prompt for the LLM to format the student data
    based on the provided CSV description. The formatted data will be used
    in subsequent steps for generating report card comments.
    """
    formatted_data_prompt = f"""
## Task: Format Student Data Based on CSV Description

You are given student data and a description of the CSV structure. Use the description to properly format the student data in a clear and structured way. DO NOT REMOVE ANY DATA. 

Below is the CSV description, followed by the student data.

### CSV Description:

{csv_description}

### Student Data (to be formatted):

{student_data}

Please format the student data according to the CSV description, ensuring clarity and consistency. RESPOND ONLY WITH THE REFORMATTED DATA TABLE.
"""
    return formatted_data_prompt

# Function to create a prompt for organizing instructions and parameters into a clear, structured prompt
def create_comment_prompt(instructions, formality, specificity, pos_reinf, sentences):
    """
    This function generates a clear and structured prompt based on the instructions
    and parameters for writing personalized report card comments.
    """
    formatted_instructions_prompt = f"""
## Task: Generate a Clear and Comprehensive LLM Prompt for Writing Report Card Comments

Your task is to generate a well-organized, easy-to-understand, and comprehensive prompt that will instruct an LLM to write personalized report card comments for an ENTIRE class. The comments should follow the tone and guidelines provided below.

RESPOND ONLY WITH THE PROMPT.

### Tone and Style Guidelines:

Include ALL of the parameters in the prompt including the relevant ranges.

- **Formality Level:** {formality}/5
- **Specificity Level:** {specificity}/5
- **Positive Reinforcement Level:** {pos_reinf}/5
- **Sentence length:** Between {sentences[0]} and {sentences[1]} for each comment 

### User Instructions for Writing Comments:

{instructions}
"""
    return formatted_instructions_prompt

class ReportCardCommentor:
    def __init__(self, student_data, csv_description, instructions,
                 formality, specificity, pos_reinf, sentences, model="gpt-4o-mini"):
    
        # Initializing AI Model Interaction
        self.llm = OpenAI(model=model, api_key=openai_api_key)
    
        # Format initial prompt for LLM to format student data
        data_prompt = format_student_data(student_data, csv_description)
        # Use LLM to format data
        messages = [ChatMessage(role="system", content="You are designed to format data nicely."),
                    ChatMessage(role="user", content=data_prompt),]
        formatted_data = self.llm.chat(messages).message.content

        # Format initial prompt for LLM to generate instruction prompt
        instructions_prompt = create_comment_prompt(instructions, formality, specificity, pos_reinf, sentences)
        # Use LLM to format instructions
        messages = [ChatMessage(role="system", content="You are designed to develop effective LLM prompts."),
                    ChatMessage(role="user", content=instructions_prompt),]
        formatted_instructions = self.llm.chat(messages).message.content
    
        # Instance of LLM with chat history
        system_prompt = f"""
## Task: Generate Report Card Comments for Each Student

You are an experienced teacher who excels at writing report card comments.

Your task is to write personalized and thoughtful report card comments for each student, based on the student data and instructions provided by the user. 

### Response Formatting

You should produce a comment for each student, formatted in a markdown table. 

After providing the comments, ask the user for feedback on whether the comments meet the requirements, asking if any adjustments are needed.
"""
        
        init_prompt = f"""
Create comments for each student based on the instructions and data below.

## Instructions

{formatted_instructions}

## Student Data

{formatted_data}
"""

        self.message_history = [ChatMessage(role="system", content=system_prompt),
                                ChatMessage(role="user", content=init_prompt),]
        response = self.llm.chat(self.message_history)
        self.message_history.append(response.message)
        self.init_comments = response.message.content

        self.prompt1 = system_prompt
        self.prompt2 = init_prompt

    def user_input(self, message):
        # Add user prompt to history
        self.message_history.append(ChatMessage(role="user", content=message))
        # Prompt LLM with history
        response = self.llm.chat(self.message_history)
        # Add response to history
        self.message_history.append(response.message)
        return response.message.content

    def get_initial_comments(self):
        return self.init_comments

    def produce_list(self, comments):
        system_prompt = f"""
The user will provide you with the output from an LLM.

Your task is to take the report card comments within this output and reformat this information.

The comments should be formatted so that there is ONE STUDENT's COMMENT ON EACH LINE.

Comments should be written in the same order that they are received. 

Ignore any text outside of the original table.

Your response should just be the list of comments without anything else.
"""
    
        user_prompt = f"""
Reformat the comments below into a single list so that I can copy them into a column in Excel - one student per row.
    
## Comments
    
{comments}
"""

        messages = [ChatMessage(role="system", content=system_prompt),
                                ChatMessage(role="user", content=user_prompt),]
        formatted_comments = self.llm.chat(messages).message.content
        return formatted_comments
        
        
