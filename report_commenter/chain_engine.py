# Build RAG pipeline

# Function to create an LLM prompt based on student data, CSV description, and instructions
def create_llm_prompt(student_data, csv_description, instructions,
                      warmth, constructiveness, use_pronouns):
    # Placeholder for LangChain code to create the prompt
    llm_prompt = f"{student_data}\n\n{csv_description}\n\n{instructions}\n\n{warmth}\n\n{constructiveness}\n\n{use_pronouns}"
    return llm_prompt

# First LLM 
# - reads the student data, csv description, instructions
# - formats the data in a comprehensive manner that is coherent, complete, and detailed. 
    
# Second LLM (chat with history)
# - receives instructions, parameters, and reformatted data
# - Produces comment for each student, returns makdown list, asks for confirmation

# Third LLM
# - once confirmed, takes last output from second LLM and formats this into a comment for each line in a separate text box with a copy button