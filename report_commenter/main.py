import os
import time
import streamlit as st
import sys
cur_dir = os.path.dirname(__file__)
sys.path.append(cur_dir)
from drop_file import increment_file_uploader_key, extract_text_from_different_file_types, change_to_prompt_text
from chain_engine import ReportCardCommentor

# Streamlit
st.set_page_config(page_title="Report Cards", page_icon="https://raw.githubusercontent.com/teaghan/educational-prompt-engineering/main/images/rc_favicon.png", layout="wide")

# Avatar images
avatar = {"user": "https://raw.githubusercontent.com/teaghan/educational-prompt-engineering/main/images/rc_teacher.png",
          "assistant": "https://raw.githubusercontent.com/teaghan/educational-prompt-engineering/main/images/rc_assistant.png"}

# Title
st.markdown("<h1 style='text-align: center; color: grey;'>Report Card Assistant</h1>", unsafe_allow_html=True)

# Text to be displayed with newlines
text = 'Generate personalized report card comments with ease.'
# Function to stream text letter by letter
def stream_text(text):
    sentence = ""
    for letter in text:
        sentence += letter
        yield sentence.replace("\n", "<br>")

cols = st.columns((0.9, 2, 0.9))
if "slow_write_main" not in st.session_state:
    st.session_state["slow_write_main"] = True
if st.session_state.slow_write_main:
    time.sleep(0.7)
    with cols[1]:
        with st.empty():
            for sentence in stream_text(text):
                st.markdown(f"<h4 style='text-align: center; color: grey;'>{sentence}</h4>", unsafe_allow_html=True)
                time.sleep(0.02)
    st.session_state.slow_write_main = False
else:
    with cols[1]:
        st.markdown(f"<h4 style='text-align: center; color: grey;'>{text}</h4>", unsafe_allow_html=True)
st.markdown("----")


# FILE UPLOAD
if "drop_file" not in st.session_state:
    st.session_state.drop_file = False
if "zip_file" not in st.session_state:
    st.session_state.zip_file = False
if "file_uploader_key" not in st.session_state:
    st.session_state.file_uploader_key = 0

st.header('Student Data')

st.markdown('Upload your student data by either dropping a file or pasting the information in the text area.')

# Interaction Tips
with st.expander("How to Export a CSV from Excel"):
    st.markdown('''
**How to Export a CSV from Excel:**
- **For Desktop Version**:
    1. Open your Excel file.
    2. Go to **File** > **Save As**.
    3. Choose **CSV (Comma Delimited) (.csv)** from the file format options.
    4. Save the file to your computer.
- **For Web Version**:
    1. Open your Excel file.
    2. Go to **File** > **Export**.
    3. Choose **Download this sheet as CSV (.csv)**.
    4. The file will automatically download to your device.''')

col1, col2 = st.columns(2)
with col1:
    dropped_files = st.file_uploader("Drop a file or multiple files (.csv, .txt, .rtf)", 
                                            accept_multiple_files=True,
                                            type=["csv", "txt", "rtf"], 
                                            key=st.session_state.file_uploader_key)

with col2:
    text_input_data = st.text_area("Or paste your student data here:")

# Initialize combined student data
student_data = ""

# Check for text input data
if text_input_data.strip():
    student_data = text_input_data +'\n\n'

if dropped_files is not None:
    st.session_state.drop_file = True
    
    if dropped_files != []:
        for dropped_file in dropped_files:   
            extract = extract_text_from_different_file_types(dropped_file)
            if st.session_state.zip_file:  
                student_data = extract  # if it is a .zip file, the return is a list
            else:  
                # Append extracted text only if there's content
                if extract.strip():
                    student_data = (student_data + "\n\n" + extract).strip() if student_data else extract

st.header('Data Description (Optional)')
st.markdown('Provide a description of how your data is formatted (e.g., columns, shorthand keys).')

with st.expander("Description Example"):
    st.markdown('''
- The "Grade" column uses the following proficiency scale: 
  - Emerging ("Em"), Developing ("D"), Proficient ("P"), Extending ("E").
- The "Student" column is formatted as "Last Name, First Name".
- The "IEP Comment" column includes a note for students with an Individualized Education Plan (IEP). If a student does not have an IEP, the cell is left blank.
- The "Positive Comments" and "Areas to Improve" columns contain brief notes on the student’s strengths and areas needing improvement.
    ''')

description = st.text_area("Description:", label_visibility='hidden')

st.header('Comment Instructions')
st.markdown('Provide specific instructions for writing the comments.')

with st.expander("Instructions Example"):
    st.markdown(''' 
- Highlight both the student’s strengths and areas for improvement.
- Encourage a growth mindset in the comments.
- Use the student's first name only when writing the comments.
- Avoid the use of pronouns (he, she, etc.) in the comments.
- For students with an IEP, include a comment on the IEP progress.
    ''')

# Text input for custom instructions
instructions = st.text_area("Instructions:", label_visibility='hidden')

st.header('Length of Comments')
st.markdown('Choose the minimum and maximum number of sentences for each comment.')
# Sliders and checkboxes for preset options
num_sentences = st.slider("Number of Sentences", 
                          label_visibility='hidden',
                          min_value=2, max_value=10, value=(3, 6))

if "model_loaded" not in st.session_state:
    st.session_state.model_loaded = False
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "model_loads" not in st.session_state:
    st.session_state["model_loads"] = 0

# Button to initialize process
if "init_model" not in st.session_state:
    st.session_state["init_model"] = False
def init_model():
    st.session_state.model_loaded = False
    st.session_state.init_model = True

_, col2, _ = st.columns(3)

col2.button("Generate Comments", 
            type="primary", 
            on_click=init_model, 
            use_container_width=True)    

if st.session_state.init_model:
    #if st.button("Generate Comments"):
    # Pass the input data to the first LLM instance
    # Add a validation check before processing
    if student_data.strip():
        if not st.session_state.model_loaded:
            # Reset conversation
            st.session_state["messages"] = []
            # Initialize pipeline
            with st.spinner('Generating initial comments...'):
                # Construct pipiline
                st.session_state['comment_pipeline'] = ReportCardCommentor(student_data,
                                                                           description,
                                                                           instructions,
                                                                           num_sentences,
                                                                           model="gpt-4o-mini")
                st.session_state.model_loads +=1
                # Run initial prompt
                response = st.session_state.comment_pipeline.get_initial_comments()
                st.session_state["report_comments"] = response
                st.session_state.messages.append({"role": "assistant", "content": rf"{response}"})
                st.chat_message("assistant", avatar=avatar["assistant"]).markdown(rf"{response}")
                st.session_state.model_loaded = True
                st.session_state.init_model = False
                st.rerun()
    else:
        st.error("Please either upload a file or paste your student data in the text area.")


if len(st.session_state.messages)>0:
    for msg in st.session_state.messages:
        st.chat_message(msg["role"], avatar=avatar[msg["role"]]).markdown(rf"{msg["content"]}")
    # The following code is for reformatting the final comments
    _, col2, _ = st.columns(3)
    accept_comments = col2.button("Accept Comments", 
            type="primary", 
            use_container_width=True)

    if accept_comments:
        with st.spinner('Formatting comments...'):
            comments = st.session_state.comment_pipeline.produce_list(st.session_state.report_comments)
        st.markdown('#### The comments below are ready to be copied into your table:')
        st.code(comments)
    
# Only show chat if model has been loaded
if st.session_state.model_loaded:
    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": rf"{prompt}"})
        st.chat_message("user", avatar=avatar["user"]).write(prompt)
        with st.spinner('Applying edits...'):
            # Apply edits
            response = st.session_state.comment_pipeline.user_input(prompt)
        st.session_state.report_comments = response
        st.session_state.messages.append({"role": "assistant", "content": rf"{response}"})
        st.chat_message("assistant", avatar=avatar["assistant"]).markdown(rf"{response}")
        st.rerun()
