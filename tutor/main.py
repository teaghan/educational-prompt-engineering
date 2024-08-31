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

def generate_links(context_list):
    base_url = "https://teaghan.github.io/astronomy-12/"
    links = []

    for context in context_list:
        title = context.metadata['title']
        content = context.page_content

        # Handle README files
        if "_README.md" in title:
            unit_number = re.search(r"# Unit(\d+)_README\.md", title).group(1)
            links.append(f"- [Unit {unit_number}]({base_url}md_files/Unit{unit_number}_README.html)")

        # Handle lesson files
        elif ".md" in title and "_" in title:
            # Extract lesson title from content
            lesson_title_match = re.search(r'# (.*?)\n', content)
            lesson_title = lesson_title_match.group(1) if lesson_title_match else "Lesson"

            lesson_parts = re.search(r"# (\d+)_(\d+)_(\w+)\.md", title)
            if lesson_parts:
                unit, lesson, name = lesson_parts.groups()
                name_formatted = name.replace('_', ' ')  # Assuming names are using underscores instead of spaces
                link_text = f"Lesson {unit}.{lesson} {name_formatted}"
                links.append(f"- [{link_text}]({base_url}md_files/{unit}_{lesson}_{name}.html)")

        # Handle assignments
        elif "Assignment" in title:
            assignment_number = re.search(r"# Unit (\d+) Assignment", title).group(1)
            links.append(f"- [Unit {assignment_number} Assignment]({base_url}Unit{assignment_number}/Unit{assignment_number}_Assignment.pdf)")

    return f"\n".join(links)

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

# Initialize Session State for Course Content Vectors
if "course_content_vecs" not in st.session_state:
    st.session_state.course_content_vecs = Chroma.from_documents(course_content, embedding=embedding_model)
course_content_vecs = st.session_state.course_content_vecs

# Managing Conversation History

def get_session_history(session_id: str):
    if "store" not in st.session_state:
        st.session_state.store = {}
    return st.session_state.store.setdefault(session_id, ChatMessageHistory())

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

st.set_page_config(page_title="AI Tutor", page_icon=":robot_face:", layout="wide")

st.markdown(
    """
<style>
.css-nzvw1x {
    background-color: #061E42 !important;
    background-image: none !important;
}
.css-1aw8i8e {
    background-image: none !important;
    color: #FFFFFF !important
}
.css-ecnl2d {
    background-color: #496C9F !important;
    color: #496C9F !important
}
.css-15zws4i {
    background-color: #496C9F !important;
    color: #FFFFFF !important
}
</style>
""",
    unsafe_allow_html=True
)

# Title
st.title("Astronomy 12 AI Tutor")

# Display Tutor Profile Image
tutor_image_url = "https://raw.githubusercontent.com/teaghan/astronomy-12/main/images/tutor_profile.png"
st.image(tutor_image_url, width=100)

# Interaction Tips
with st.expander("Tips for Interacting with AI Tutors: "):
    st.markdown('''
- Aim to learn and understand the material, not just to get the answers.
- Always ask ChatGPT to explain the process rather than just solve the problem for you.
- Ask follow-up questions if you are still unclear.
- To help type math, use these keyboard shortcuts:
    - Addition (+): Use the + key.
    - Subtraction (-): Use the - key.
    - Multiplication (×): Use the * key.
    - Division (÷): Use the / key.
    - Equals (=): Use the = key.
    - Greater Than (>): Use the > key.
    - Less Than (<): Use the < key.
    - Powers (x²): Use the ^ symbol followed by the exponent. For example: x^2
    - Square Root: Type \sqrt{} using the {} brackets to enclose the argument. For example: \sqrt{4}
    ''')

# Sidebar Links

with st.sidebar:
    st.markdown("[Course Home](https://teaghan.github.io/astronomy-12/)")
    for i in range(1, 6):
        st.markdown(f"[Unit {i}](https://teaghan.github.io/astronomy-12/md_files/Unit{i}_README.html)")

# Initialize Session State for Chat History
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "I'm here to help you navigate your astronomy course, making tricky concepts clearer and guiding you through challenging problems. While I won’t do the work for you, I'll show you how to solve problems on your own, helping you gain confidence as you move forward.\n\nHow can I help you today?"}]
if "store" not in st.session_state:
    st.session_state.store = {}

# Display chat messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).markdown(rf"{msg["content"]}")

# Chat input
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Use a spinner to indicate processing and display the assistant's response after processing
    with st.spinner('Thinking...'):

        response = conversational_rag_chain.invoke({"input": prompt}, config={"configurable": {"session_id": "abc123"}})
        msg = response["answer"]

        msg += '\n\nFor more information take a look at the following course content:\n'
        msg += generate_links(response['context'])

        st.session_state.messages.append({"role": "assistant", "content": rf"{msg}"})    
    st.chat_message("assistant").markdown(rf"{msg}")