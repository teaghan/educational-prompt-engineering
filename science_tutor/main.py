import os
import streamlit as st
import sys
cur_dir = os.path.dirname(__file__)
sys.path.append(cur_dir)
from drop_file import extract_text_from_different_file_types
from tutor_llm import TutorChain

# Streamlit
st.set_page_config(page_title="AI Science Tutor", page_icon="https://raw.githubusercontent.com/teaghan/educational-prompt-engineering/main/images/science_tutor_favicon_small.png", layout="wide")

# Avatar images
avatar = {"user": "https://raw.githubusercontent.com/teaghan/educational-prompt-engineering/main/images/science_student_avatar.png",
          "assistant": "https://raw.githubusercontent.com/teaghan/educational-prompt-engineering/main/images/science_tutor_avatar.png"}

# Title
st.markdown("<h1 style='text-align: center; color: grey;'>AI Science Tutor</h1>", unsafe_allow_html=True)

# Display Tutor Profile Image
tutor_image_url = "https://raw.githubusercontent.com/teaghan/educational-prompt-engineering/main/images/science_tutor_favicon.png"
col1, col2, col3 = st.columns(3)
col2.image(tutor_image_url)

# Interaction Tips
with st.expander("Tips for Interacting with AI Tutors"):
    st.markdown("""
- Try to learn and understand the material, not just to get the answers.
- Ask the tutor to explain how things work instead of just giving the solution.
- Be as clear as you can when asking questions to get the best help.
- If you're still unsure, don’t be afraid to ask more questions.
- To help type math symbols, use these keyboard shortcuts:
    - Addition (+): Use the + key.
    - Subtraction (-): Use the - key.
    - Multiplication (×): Use the * key.
    - Division (÷): Use the / key.
    - Equals (=): Use the = key.
    - Greater Than (>): Use the > key.
    - Less Than (<): Use the < key.
    - Powers (3²): Use the ^ symbol followed by the exponent. For example: 3^2
    - Square Root: Type \sqrt{} using the {} brackets to enclose the number. For example: \sqrt{4}
- Example Prompts to Get Started:
    - "What role does the Sun play in the water cycle?"
    - "Can you help me understand how photosynthesis works?"
    - "Can you help me with problem 6 on the attached assignment?
    - "Can you help me understand how the states of matter change from one form to another?"
    - "How do living organisms adapt to their environment to survive?"
    - "Can you help me understand how simple machines like levers and pulleys make work easier?"
    - "Can you help me understand how the movement of tectonic plates causes earthquakes?"
    - "Can you help me understand how the digestive system breaks down food in the human body?"
    """)


if "model_loaded" not in st.session_state:
    st.session_state.model_loaded = False
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "model_loads" not in st.session_state:
    st.session_state["model_loads"] = 0

# Display conversation
if len(st.session_state.messages)>0:
    for msg in st.session_state.messages:
        st.chat_message(msg["role"], avatar=avatar[msg["role"]]).markdown(rf"{msg["content"]}")


# Load model
if not st.session_state.model_loaded:
    with st.spinner('Loading...'):
        # Construct pipiline
        st.session_state['tutor_llm'] = TutorChain()
        st.session_state.model_loads +=1

        init_request = st.session_state.tutor_llm.init_request        
        st.session_state.messages.append({"role": "assistant", "content": init_request})

        st.session_state.model_loaded = True
        st.rerun()

# The following code handles dropping a file from the local computer
if "drop_file" not in st.session_state:
    st.session_state.drop_file = False
if "zip_file" not in st.session_state:
    st.session_state.zip_file = False
drop_file = st.sidebar.button(r"$\textsf{\normalsize Attach a file}$", 
                      type="primary")
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
                for filename, content in extract:
                    # Append the file name and content to the prompt text
                    prompt_f += f"File: \n{filename}\n\nContent: \n{content}\n\n"
                    prompt_f += "-----\n"
                    st.session_state.zip_file = False
            else:  # if it is not zip, the return is a string (here we concatenate the strings)
                prompt_f = prompt_f + extract + "\n\n"

if prompt := st.chat_input():
    if st.session_state.drop_file is True:
        prompt_full = prompt + f'\n\n## Uploaded file contents:\n\n{prompt_f}'
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
