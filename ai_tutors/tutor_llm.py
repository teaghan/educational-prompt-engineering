import streamlit as st

import os
from chatbot_llm import AITutor
from moderator_llm import ContentModerator

from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from transformers import OpenAIGPTTokenizerFast

class TutorChain:

    def __init__(self, 
                 instructions, 
                 guidelines):

        # Load API keys
        openai_api_key = os.environ["OPENAI_API_KEY"]

        # Initialize the OpenAI LLM
        llm_model = OpenAI(model='gpt-4o-mini', temperature=0.4, api_key=openai_api_key)
        
        # Initialize the tutor with the LLM and instructions
        self.tutor_llm = AITutor(llm_model, instructions)
        self.init_request = self.tutor_llm.message_history[-1].content

        # Create an instance of the ContentModerator class
        self.moderator_llm = ContentModerator(guidelines, 
                                             llm_model)

    def get_response(self, student_prompt, moderate=True):
        # Prompt AI tutor
        with st.spinner('Responding...'):
            ai_response = self.tutor_llm.get_response(student_prompt)

        if moderate:
            needs_checking = True
            while needs_checking:
                # Moderate response
                results = self.moderator_llm.forward(self.tutor_llm.message_history)

                moderated_response = results['final_response']
                # Update chat history
                self.tutor_llm.message_history[-1].content = moderated_response
                if not results['moderated']:
                    # Response is good to go
                    needs_checking = False

        return moderated_response 



            