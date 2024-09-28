import os
import streamlit as st
import sys
cur_dir = os.path.dirname(__file__)
sys.path.append(cur_dir)
from drop_file import extract_text_from_different_file_types
from tutor_llm import load_tutor
from moderator_llm import load_moderator

# Streamlit
st.set_page_config(page_title="AI Tutor", page_icon="https://raw.githubusercontent.com/teaghan/astronomy-12/main/images/tutor_favicon.png", layout="wide")

# Avatar images
avatar = {"user": "https://raw.githubusercontent.com/teaghan/astronomy-12/main/images/student_avatar_4.png",
          "assistant": "https://raw.githubusercontent.com/teaghan/astronomy-12/main/images/tutor_favicon.png"}

# Title
st.markdown("<h1 style='text-align: center; color: grey;'>AI Science Tutor</h1>", unsafe_allow_html=True)

# Display Tutor Profile Image
tutor_image_url = "https://raw.githubusercontent.com/teaghan/astronomy-12/main/images/tutor_favicon.png"
col1, col2, col3 = st.columns(3)
col2.image(tutor_image_url)

# Interaction Tips
with st.expander("Tips for Interacting with AI Tutors"):
    st.markdown("""
- Aim to learn and understand the material, not just to get the answers.
- Always ask the tutor to explain the process rather than just solve the problem for you.
- To get the best results, be as specific as you can.
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
- Example Prompts to Get Started:
    - "How do I calculate the orbital period of a planet using Kepler’s Third Law?"
    - "How do I calculate the surface gravity of a planet given its mass and radius?"
    - "Can you help me with this assignment on galaxy data? I’m not sure how to start."
    - "How do I calculate the energy released from a single proton-proton chain reaction in the Sun?"
    """)

# The following code handles dropping a file from the local computer
if "drop_file" not in st.session_state:
    st.session_state.drop_file = False
if "zip_file" not in st.session_state:
    st.session_state.zip_file = False
drop_file = st.sidebar.button(r"$\textsf{\normalsize Attach a file}$", 
                              type="primary", 
                              key="drop")
if drop_file:
    st.session_state.drop_file = True
if "file_uploader_key" not in st.session_state:
    st.session_state.file_uploader_key = 0

if st.session_state.drop_file:
    dropped_files = st.sidebar.file_uploader("Drop a file or multiple files (.txt, .rtf, .pdf, .csv, .zip)", 
                                            accept_multiple_files=True,
                                            key=st.session_state.file_uploader_key)
    # Load file contents
    prompt_f =""
    if dropped_files != []:
        for dropped_file in dropped_files:   
            extract = extract_text_from_different_file_types(dropped_file)
            if st.session_state.zip_file:  
                prompt_f = extract  # if it is a .zip file, the return is a list
            else:  # if it is not zip, the return is a string (here we concatenate the strings)
                prompt_f = prompt_f + extract + "\n\n"


if "model_loaded" not in st.session_state:
    st.session_state.model_loaded = False
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "model_loads" not in st.session_state:
    st.session_state["model_loads"] = 0
if "init_model" not in st.session_state:
    st.session_state["init_model"] = False
        
def init_model():
    st.session_state.model_loaded = False
    st.session_state.init_model = True

if len(st.session_state.messages)>0:
    for msg in st.session_state.messages:
        st.chat_message(msg["role"], avatar=avatar[msg["role"]]).markdown(rf"{msg["content"]}")

if not st.session_state.model_loaded:
    with st.spinner('Loading...'):
        # Construct pipiline
        st.session_state['tutor_llm'] = load_tutor()
        st.session_state['moderator_llm'] = load_moderator()
        st.session_state.model_loads +=1
        
        # Grab initial chat history
        st.session_state.messages = st.session_state.tutor_llm.message_history
        
        st.session_state.model_loaded = True
        st.session_state.init_model = False
        
        st.session_state.messages.append({"role": "assistant", "content": st.session_state.messages[-1].content})
        st.chat_message("user", avatar=avatar["user"]).write(prompt)
        st.rerun()

# Only show chat if model has been loaded
if prompt := st.chat_input():
    if st.session_state.drop_file is True:
        prompt_full = prompt + f'\n\n## Uploaded file contents:\n\n{prompt_f}'
        #prompt = change_to_prompt_text(prompt_f, prompt)
    else:
        prompt_full = prompt


    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user", avatar=avatar["user"]).write(prompt)

    # Use a spinner to indicate processing and display the assistant's response after processing
    with st.spinner('Thinking...'):

        response = st.session_state.tutor_llm.get_response(prompt_full)

        st.session_state.messages.append({"role": "assistant", "content": rf"{response}"})    
    st.chat_message("assistant", avatar=avatar["assistant"]).markdown(rf"{response}")
    st.rerun()
