from chatbot_llm import AITutor
from moderator_llm import ContentModerator

class TutorChain:

    def __init__(self, 
                 instructions_path='science_tutor/tutor_instructions.txt', 
                 guidelines_path='science_tutor/moderation_guidelines.txt'):

        # Load API keys
        openai_api_key = os.environ["OPENAI_API_KEY"]
        hf_token = os.environ["LANGCHAIN_API_KEY"]

        # Initialize the OpenAI embedding model
        embedding_model = OpenAIEmbedding(model='text-embedding-3-small', api_key=openai_api_key)
        
        # Initialize the OpenAI LLM
        llm_model = OpenAI(model='gpt-4o-mini', api_key=openai_api_key)
        
        # Tokenizer for OpenAI's GPT models
        tokenizer = OpenAIGPTTokenizerFast.from_pretrained("openai-community/openai-gpt", token=hf_token)

        # Initialize the tutor with the LLM and instructions
        self.tutor_llm = AITutor(llm_model, instructions_path)
        self.init_request = tutor_llm.message_history[-1].content

        # Create an instance of the ContentModerator class
        self.moderator_llm = ContentModerator(guidelines_path, 
                                             llm_model, 
                                             embedding_model, 
                                             tokenizer, 
                                             chat_mode="openai")

    def get_response(self, prompt, moderate=True):
        # Prompt AI tutor
        response = self.tutor_llm.get_response(prompt)

        if moderate:
            # Moderate response
            result = self.moderator.forward(student_prompt, ai_response)['final_response']
            # Update chat history
            self.message_history[-1].content = result

        return response



            