import streamlit as st

import os
import re
from langchain_openai import ChatOpenAI
from langchain.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables.history import RunnableWithMessageHistory

### Secure API Key Management

def load_api_key(key_file):
    with open(key_file) as f:
        key = f.read().strip("\n")
    return key

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["OPENAI_API_KEY"] = load_api_key('../key.txt')
os.environ["LANGCHAIN_API_KEY"] = load_api_key(key_file='../langchain_key.txt')
os.environ['USER_AGENT'] = 'myagent'

## Integrating Course Content

def load_text_file(file_path):
    return open(file_path, 'r').read()

tutor_instructions = load_text_file('Tutor_Instructions.txt')
course_content = load_text_file('course_content.txt')

### Structuring the Content

def split_by_files(content, context_window):
    # Define patterns for splitting based on README, lesson files, and assignments
    readme_pattern = r"# Unit\d+_README\.md"
    lesson_pattern = r"# \d+_\d+_[\w_]+\.md"
    assignment_pattern = r"# Unit \d+ Assignment"

    # Combine all patterns
    combined_pattern = f"({readme_pattern}|{lesson_pattern}|{assignment_pattern})"
    
    # Find all matches (file sections) and split the content
    matches = re.split(combined_pattern, content)

    # Collect file content
    chunks = []
    for i in range(1, len(matches), 2):
        chunk_title = matches[i].strip()
        chunk_content = matches[i + 1].strip()

        # Check the length of the chunk_content and split if necessary
        if chunk_content:
            content_length = len(chunk_content)
            if content_length <= context_window:
                chunks.append(Document(page_content=chunk_content, metadata={"title": chunk_title}))
            else:
                # Split the content into smaller chunks if it exceeds the context window
                part_number = 0
                for start in range(0, content_length, context_window):
                    end = start + context_window
                    part_number += 1
                    subtitle = f"{chunk_title} ({part_number})"
                    # Ensure the split does not cut off mid-word
                    if end < content_length and not chunk_content[end].isspace():
                        # Find the nearest space to avoid splitting words
                        end = chunk_content.rfind(' ', start, end)
                    sub_content = chunk_content[start:end].strip()
                    if sub_content:
                        chunks.append(Document(page_content=sub_content, metadata={"title": subtitle}))

    return chunks

## Building the Chatbot

### Initializing AI Models for Embedding and Interaction

model = "gpt-4o-mini"
embedding_model = OpenAIEmbeddings()
llm = ChatOpenAI(model=model)

# Determine max context window for model used
model_context_windows = {
    "gpt-4o": 128000,
    "gpt-4o-2024-05-13": 128000,
    "gpt-4o-2024-08-06": 128000,
    "chatgpt-4o-latest": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4o-mini-2024-07-18": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4-turbo-2024-04-09": 128000,
    "gpt-4-turbo-preview": 128000,
    "gpt-4-0125-preview": 128000,
    "gpt-4-1106-preview": 128000,
    "gpt-4": 8192,
    "gpt-4-0613": 8192,
    "gpt-4-0314": 8192,
    "gpt-3.5-turbo-0125": 16385,
    "gpt-3.5-turbo": 16385,
    "gpt-3.5-turbo-1106": 16385,
    "gpt-3.5-turbo-instruct": 4096
}
context_window = model_context_windows[model]

### Embedding Documents

course_content = split_by_files(course_content, context_window)
tutor_instructions = Document(page_content=tutor_instructions, metadata={"title": "Tutor Instructions"})
course_content_vecs = Chroma.from_documents(course_content, embedding=embedding_model)

### Managing Conversation History

store = {}
def get_session_history(session_id: str):
    return store.setdefault(session_id, ChatMessageHistory())

### Setting Up the Chatbot Interaction

contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)
contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
])

history_aware_retriever = create_history_aware_retriever(llm, course_content_vecs.as_retriever(), contextualize_q_prompt)

### Integrating Document-Based Responses

system_prompt = (
    f"{tutor_instructions.page_content}\n\n"
    "## Your Task\n\n"
    "Following the instructions above, use the following pieces of retrieved context to answer the question. \n\n"
    "# Context"
    "{context}"
)
qa_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
])

question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

### Implementing the Retrieval-Augmented Generation Chain

rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
conversational_rag_chain = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    output_messages_key="answer",
)

# Streamlit

# Streamlit Page Configuration
st.set_page_config(page_title="AI Tutor", page_icon=":robot_face:")

# Title and Description
st.title("Astronomy 12 AI Tutor")
#st.caption("I'm here to help you navigate your astronomy course, making tricky concepts clearer and guiding you through challenging problems. While I won’t do the work for you, I'll show you how to solve problems on your own, helping you gain confidence as you move forward.")

# Initialize Session State for Chat History
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "I'm here to help you navigate your astronomy course, making tricky concepts clearer and guiding you through challenging problems. While I won’t do the work for you, I'll show you how to solve problems on your own, helping you gain confidence as you move forward."}]


for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])


if prompt := st.chat_input():

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    response = conversational_rag_chain.invoke({"input": prompt}, 
                                           config={"configurable": {"session_id": "abc123"}})
    msg = response["answer"]
    
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
    st.chat_message("assistant").write(store)
