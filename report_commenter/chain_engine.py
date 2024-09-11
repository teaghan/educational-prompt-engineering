import nltk
nltk.download('punkt')

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
def create_comment_prompt(instructions, warmth, constructiveness, use_pronouns):
    """
    This function generates a clear and structured prompt based on the instructions
    and parameters for writing personalized report card comments.
    """
    formatted_instructions_prompt = f"""
## Task: Generate a Clear and Comprehensive LLM Prompt for Writing Report Card Comments

Your task is to generate a well-organized, easy-to-understand, and comprehensive prompt that will instruct an LLM to write personalized report card comments. The comments should follow the tone and guidelines provided below.

RESPOND ONLY WITH THE PROMPT.

### Tone and Style Guidelines:

Include ALL of the parameters in the prompt including the relevant ranges.

- **Warmth Level:** {warmth}/10
- **Constructiveness Level:** {constructiveness}/10
- **Use Pronouns:** {'Yes' if use_pronouns else 'No'}

### User Instructions for Writing Comments:

{instructions}
"""
    return formatted_instructions_prompt

class ReportCardCommentor:
    def __init__(self, student_data, csv_description, instructions,
                          warmth, constructiveness, use_pronouns,
                          model="gpt-4o-mini", embedding='text-embedding-3-small'):
    
        # Initializing AI Model Interaction
        self.llm = OpenAI(model=model, api_key=openai_api_key)
    
        # Format initial prompt for LLM to format student data
        data_prompt = format_student_data(student_data, csv_description)
        # Use LLM to format data
        messages = [ChatMessage(role="system", content="You are designed to format data nicely."),
                    ChatMessage(role="user", content=data_prompt),]
        formatted_data = self.llm.chat(messages).message.content

        # Format initial prompt for LLM to generate instruction prompt
        instructions_prompt = create_comment_prompt(instructions, warmth, constructiveness, use_pronouns)
        # Use LLM to format instructions
        messages = [ChatMessage(role="system", content="You are designed to develop effective LLM prompts."),
                    ChatMessage(role="user", content=instructions_prompt),]
        formatted_instructions = self.llm.chat(messages).message.content
    
        # Instance of LLM with chat history
        # - receives reformatted instructions and data
        # - system prompt gives guidelaines for LLM about how to respond (provide formatted comments, ask for feedback),
        #   includes the reformatted data and user instructions
        # - Produces comment for each student, returns makdown list, asks for feedback
    
        system_prompt = f"""
    ## Task: Generate Report Card Comments for Each Student
    
    Your task is to write personalized report card comments for each student, based on the student data and instructions provided by the user. 
    
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
        self.message_history.append(resp.message)
        self.init_comments = response.message.content
    
        # Third LLM
        # - once confirmation button pressed, this takes last output from second instance of LLM
        # - formats this into a comment on each line in a separate text box with a copy button

    def user_input(self, message):
        # Add user prompt to history
        self.message_history.append(ChatMessage(role="user", content=message))
        # Prompt LLM with history
        response = self.llm.chat(self.message_history)
        # Add response to history
        self.message_history.append(resp.message)
        return response.message.content

    def get_initial_comments(self):
        return self.init_comments
        
