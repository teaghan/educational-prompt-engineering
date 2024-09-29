import os
from llama_index.core.llms import ChatMessage
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from transformers import OpenAIGPTTokenizerFast

class ContentModerator:
    """
    A class that moderates and corrects AI-generated responses based on pre-defined guidelines. 
    The ContentModerator uses a Large Language Model (LLM) and an embedding model to ensure 
    AI responses are appropriate, factually correct, and aligned with the given moderation guidelines. 
    If a response is deemed inappropriate, it can be corrected using a separate correction pipeline.

    **Note:** The `llm_model` used in this class must have both `query` and `chat` capabilities.

    Attributes:
        guidelines_path (str): The path to the moderation guidelines text file.
        llm_model (Any): The Large Language Model (LLM) used to process and generate responses. 
                         **Must support both `query` and `chat` functions.**
        embedding_model (Any): The embedding model used to index and query the moderation guidelines.
        tokenizer (Any): Tokenizer for processing text data before sending it to the LLM.
        moderator_engine (Any): The engine responsible for moderating the AI responses based on the guidelines.
        corrector_engine (Any): The engine responsible for correcting inappropriate AI responses.
    
    Methods:
        moderate_response(ai_response):
            Uses the moderation guidelines to determine whether the given AI response is appropriate.
            Returns feedback explaining why the response is (or isn’t) appropriate.

        correct_response(student_prompt, ai_response, moderator_feedback):
            Corrects an inappropriate AI response using the moderator's feedback. 
            The LLM generates a corrected response based on the original student prompt, 
            AI response, and moderator feedback.

        forward(student_prompt, ai_response):
            A high-level method that first moderates the AI response. If the response is inappropriate, 
            it corrects the response. Returns the original AI response, moderator feedback, and the final response.
    
    Example usage:
        moderator = ContentModerator(
            guidelines_path='path_to_guidelines.txt',
            llm_model=OpenAI(model='gpt-4o-mini', api_key=openai_api_key),
            embedding_model=OpenAIEmbedding(model='text-embedding-3-small', api_key=openai_api_key),
            tokenizer=OpenAIGPTTokenizerFast.from_pretrained('openai-community/openai-gpt', token=hf_token),
            chat_mode='openai',
            display_guidelines=True
        )

        student_prompt = "Why do we have day and night?"
        ai_response = "It’s because the Earth revolves around the Sun."
        
        result = moderator.forward(student_prompt, ai_response)
        print(result['final_response'])
    """
    def __init__(self, guidelines_path, llm_model, embedding_model, tokenizer, chat_mode="openai", 
                 display_guidelines=True):
        """
        Initializes the ContentModerator class with the specified LLM models, embedding models, 
        and tokenizer. Loads the moderation guidelines and sets up moderation and correction engines.

        **Note:** The `llm_model` used must have both `query` and `chat` capabilities to enable 
        moderation and correction of responses.

        Arguments:
            guidelines_path (str): Path to the moderation guidelines file.
            llm_model (Any): The Large Language Model (LLM) for querying and generating responses. 
                             **Must support both `query` and `chat` functions.**
            embedding_model (Any): The embedding model used to index the guidelines and assist in moderation tasks.
            tokenizer (Any): Tokenizer to process the input text before sending it to the LLM.
            chat_mode (str, optional): The mode for the correction engine (default is "openai").
            display_guidelines (bool, optional): If True, prints out the loaded moderation guidelines for review.
        """
        
        # Load the moderation guidelines from the specified path
        self.guidelines_path = guidelines_path
        loader = SimpleDirectoryReader(input_files=[guidelines_path])
        self.documents = loader.load_data()

        # Optionally print out the guidelines
        if display_guidelines:
            print(f"The following guidelines will be used from the {guidelines_path} file:\n")
            print(self.documents[0].text)
        
        # Index the moderation guidelines using the embedding model
        index = VectorStoreIndex.from_documents(
            self.documents,
            llm=llm_model,
            embed_model=embedding_model,
            tokenizer=tokenizer)

        # Set up the query engine to retrieve moderation rules and apply them
        self.moderator_engine = index.as_query_engine(llm=llm_model, 
                                                           embed_model=embedding_model, 
                                                           tokenizer=tokenizer)
        
        # Set up the chat engine for correcting responses
        self.corrector_engine = index.as_chat_engine(chat_mode=chat_mode, 
                                                               llm=llm_model,
                                                               embed_model=embedding_model, 
                                                               tokenizer=tokenizer)

    def moderate_response(self, chat_history, ai_response):
        """
        Uses the LLM to moderate the AI tutor's response based on the loaded guidelines and the full chat history.
    
        Arguments:
            chat_history (str): The full chat history (formatted as a string).
            ai_response (str): The response provided by the AI tutor that needs moderation.
    
        Returns:
            tuple: 
                - moderator_response (str): Feedback from the moderator explaining the decision.
                - is_appropriate (bool): Indicates whether the AI response is appropriate or not (True for appropriate, False for inappropriate).
        """
        # Formulate the query for moderation based on the full chat history
        query = f'''
Based on the moderation guidelines, is the following AI response appropriate given the prior conversation?
Begin with "Yes" or "No" followed by your reasoning.\n\n

**Chat History**:\n
{chat_history}

**AI Response**:\n
"{ai_response}"
        '''
        
        # Query the moderator LLM with the response
        moderation_result = self.moderator_engine.query(query)
        
        # Extract the moderator's feedback from the response (first non-empty line)
        moderator_response = next((r.strip() for r in moderation_result.response.split('\n') if r), "")
        
        # Determine if the response is appropriate (check if first word is "yes" or "no")
        is_appropriate = moderator_response.lower().startswith("yes")
        return moderator_response, is_appropriate

    def correct_response(self, chat_history, ai_response, moderator_feedback):
        """
        Generates a corrected response based on the chat history, AI tutor's inappropriate response, and moderator feedback.
    
        Arguments:
            chat_history (str): The full chat history before the AI response.
            ai_response (str): The AI tutor's inappropriate response.
            moderator_feedback (str): Feedback from the moderator explaining why the response was inappropriate.
    
        Returns:
            str: The corrected response generated by the LLM, ensuring alignment with the guidelines.
        """
        # Combine the chat history, AI response, and moderator feedback into a correction prompt
        correction_prompt = f"""
The AI tutor gave the following inappropriate response in this conversation:

    **Chat History**:\n\n{chat_history}\n\n
    **AI Response**: "{ai_response}"\n\n
    **Moderator's Feedback**: "{moderator_feedback}"

Your Task: Provide a corrected response based on the full conversation that is appropriate according to the moderation guidelines. Respond ONLY WITH THE CORRECTED RESPONSE.
        """
    
        # Run the correction prompt through the corrector LLM
        corrected_response = self.corrector_engine.chat(correction_prompt).response
    
        # Optionally remove quotes if they exist in the output
        if corrected_response.startswith('"') and corrected_response.endswith('"'):
            corrected_response = corrected_response[1:-1]
        
        return corrected_response


    def forward(self, chat_history):
        """
        Moderates and potentially corrects the AI tutor's latest response. If the response is deemed inappropriate, 
        it is corrected based on the moderation feedback.
    
        Arguments:
            chat_history (list): The full chat history (a list of dictionaries containing both student and AI messages).
    
        Returns:
            dict: A dictionary containing:
                - previous_conversation (str): The back-and-forth conversation history up to the latest AI response.
                - ai_response (str): The latest AI response from the chat history.
                - moderator_feedback (str): Feedback explaining the moderation decision.
                - final_response (str): The final response provided to the student (either the original or corrected response).
        """
        # Ensure chat_history is not empty
        if not chat_history:
            raise ValueError("Chat history cannot be empty.")
        
        # Separate the last message (assumed to be the AI's response)
        latest_message = chat_history[-1]
        
        # Ensure the latest message is from the AI
        if latest_message.role.value != 'assistant':
            raise ValueError("The latest message in the chat history must be from the AI.")
        
        # Extract the AI response
        ai_response = latest_message.content
        
        # Combine all prior messages (before the last AI response) into the conversation context
        previous_conversation = "\n\n".join([f"{message.role.value}: {message.content}" for message in chat_history[:-1]])
    
        # Moderate the AI response using the full previous conversation context
        moderator_feedback, is_appropriate = self.moderate_response(previous_conversation, ai_response)
        
        # If the response is inappropriate, pass it to the corrector LLM
        if not is_appropriate:
            corrected_response = self.correct_response(previous_conversation, ai_response, moderator_feedback)
            final_response = corrected_response
        else:
            final_response = ai_response
        
        # Return a dictionary detailing the process and result
        return {
            "previous_conversation": previous_conversation,
            "ai_response": ai_response,
            "moderator_feedback": moderator_feedback,
            "final_response": final_response
        }


def load_moderator():
    # Example usage:
    guidelines_path = 'science_tutor/moderation_guidelines.txt'

    openai_api_key = os.environ["OPENAI_API_KEY"]
    hf_token = os.environ["LANGCHAIN_API_KEY"]
        
    # Initialize the OpenAI embedding model used in the correction pipeline
    embedding_model = OpenAIEmbedding(model='text-embedding-3-small', api_key=openai_api_key)
        
    # Initialize the OpenAI LLM for correcting inappropriate AI responses
    llm_model = OpenAI(model='gpt-4o-mini', api_key=openai_api_key)
        
    # Tokenizer for OpenAI's GPT models (used in correction)
    tokenizer = OpenAIGPTTokenizerFast.from_pretrained("openai-community/openai-gpt", token=hf_token)
        
    # Create an instance of the ContentModerator class
    moderator = ContentModerator(guidelines_path, 
                                     llm_model, 
                                     embedding_model, 
                                     tokenizer, 
                                     chat_mode="openai", 
                                     display_guidelines=True)