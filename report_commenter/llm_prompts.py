# Function to create an LLM prompt based on student data, CSV description, and instructions
def create_llm_prompt(student_data, csv_description, instructions,
                      warmth, constructiveness, use_pronouns):
    # Placeholder for LangChain code to create the prompt
    llm_prompt = f"{student_data}\n\n{csv_description}\n\n{instructions}\n\n{warmth}\n\n{constructiveness}\n\n{use_pronouns}"
    return llm_prompt


