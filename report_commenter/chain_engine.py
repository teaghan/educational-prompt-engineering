import streamlit as st
import os
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.messages import HumanMessage
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain import LLMChain, PromptTemplate

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ['USER_AGENT'] = 'myagent'


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
        #self.embedding_model = OpenAIEmbeddings(model=embedding)
        llm = ChatOpenAI(model=model)
    
        # Format initial prompt for LLM to format student data
        data_prompt = format_student_data(student_data, csv_description)
        # Use LLM to format data
        formatted_data = llm.invoke(data_prompt).content
    
        # Format initial prompt for LLM to generate instruction prompt
        instructions_prompt = create_comment_prompt(instructions, warmth, constructiveness, use_pronouns)
        # Use LLM to format instructions
        formatted_instructions = llm.invoke(instructions_prompt).content
    
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
        '''
        init_chat_prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
        ])
    
        edit_chain = create_stuff_documents_chain(llm, init_chat_prompt)
        self.rag_chain = create_retrieval_chain(history_aware_retriever, edit_chain)
        self.chat_history = []
        '''

        init_chat_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{query}"),
                ]
            )
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.llm_chain = LLMChain(
            llm=ChatOpenAI(model="gpt-4o", temperature=0),
            prompt=init_chat_prompt,
            verbose=False,
            memory=memory,
        )
    
        self.init_prompt = f"""
    Create comments for each student based on the instructions and data below.
    
    ## Instructions
    
    {formatted_instructions}
    
    ## Student Data
    
    {formatted_data}
    """
    
        # Third LLM
        # - once confirmation button pressed, this takes last output from second instance of LLM
        # - formats this into a comment on each line in a separate text box with a copy button

    def user_input(self, message):
        response = llm_chain.run(message)
        #response = self.rag_chain.invoke({"input": message, "chat_history": self.chat_history})
        #self.chat_history.extend([HumanMessage(content=message), response["answer"]])
        return response

    def get_initial_comments(self):
        return user_input(message=self.init_prompt)
        
