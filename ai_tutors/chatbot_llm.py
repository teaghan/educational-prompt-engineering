import os
from llama_index.core.llms import ChatMessage
from llama_index.llms.openai import OpenAI

def load_text_file(file_path):
    return open(file_path, 'r').read()

class AITutor:
    """
    A class that facilitates a back-and-forth conversation between a student and an AI tutor.
    It uses an LLM (Large Language Model) to guide students through questions, provide feedback, 
    and help them understand science concepts without directly giving them the answers.

    This class is designed to work with any LLM that has a chat function.

    Attributes:
        llm (Any LLM with a chat function): The LLM model used to interact with the student.
        message_history (list): A history of messages exchanged between the student and the tutor.
    
    Methods:
        initiate_conversation(grade, topic): Initiates the tutoring session by asking the student for more details.
        get_response(student_input): Handles student input and provides a response using the LLM.
        get_message_history(): Returns the history of messages in the conversation.
    """

    def __init__(self, llm_model, instructions_path, display_system=False):
        self.llm = llm_model
        self.message_history = []

        # Load pre-defined instructions for the AI tutor
        instructions = load_text_file(instructions_path)

        # Add these as a "system prompt"
        system_prompt = f"{instructions}\n\n"
        system_prompt += "## Your Task\n\n"
        system_prompt += "You are a tutor for science students in grades 6-8. Following the instructions above, provide supportive assistance to the student user."
        if display_system:
            print(system_prompt)
        
        # Initialize the conversation with the system prompt
        self.message_history.append(ChatMessage(role="system", content=system_prompt))
        
        # Append initial request from AI tutor
        self.initiate_conversation()

    def initiate_conversation(self):
        """
        Initiates the conversation with the student, asking for the grade level and topic they are working on.
        """
        init_message = f"""
Hi! I'm here to help you with your science questions. 

I won't do the work for you, but I'll guide you through each step so you can understand and feel more confident.

To start, **what grade are you in and what do you need help with?**
        """
        self.message_history.append(ChatMessage(role="assistant", content=init_message))

    def get_response(self, student_input):
        """
        Handles student input and provides a response.
        The LLM will respond based on the system instructions, conversation history, and the input provided by the student.
        """
        # Add the student's message to the history
        self.message_history.append(ChatMessage(role="user", content=student_input))
        
        # Get the response from the LLM
        response = self.llm.chat(self.message_history).message.content
        
        # Add the AI's response to the history
        self.message_history.append(ChatMessage(role="assistant", content=response))
        
        return response

def load_tutor():
    # Load OpenAI API key
    openai_api_key = os.environ["OPENAI_API_KEY"]
    # Initialize the tutor with the LLM and instructions
    instructions_path = 'science_tutor/tutor_instructions.txt'
    llm_model = OpenAI(model="gpt-4o-mini", api_key=openai_api_key)
    return AITutor(llm_model, instructions_path)