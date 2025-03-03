import os
import time
import streamlit as st
import sys
import random
cur_dir = os.path.dirname(__file__)
sys.path.append(cur_dir)
from drop_file import increment_file_uploader_key, extract_text_from_different_file_types, change_to_prompt_text
from chain_engine import ReportCardCommentor

#model = "gpt-4o-mini"
model = 'models/gemini-2.0-flash-001'

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

###

st.markdown('### Student Data 📄')
st.markdown('Drop a file 📎 or paste 📋 your student data below!')
with st.expander("What information should I include?"):
    st.markdown('''You can format your data in any way you want, just be sure to include enough information to generate meaningful, personalized comments.
  
**Some Column Suggestions (but not required):**
- Student Name
- Overall Grade/Proficiency
- Topic specific evaluations
- Strengths
- Areas for Growth
- IEP Notes (if applicable)
- Additional Comments

💡 **Tip:** Need to explain your data format or abbreviations? Check out the "Optional Settings" section below.''')

with st.expander("Wondering how to export a .csv file from Excel?"):
    st.markdown('''
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
            student_data = (student_data + f"\n\n**{dropped_file.name}**\n\n" + extract).strip()

###

st.markdown('----')
st.markdown('### Comment Instructions 📝')
st.markdown('Tailor the comments to your style!')
with st.expander("Looking for some **examples**?"):
    st.markdown(''' 
- Make the comments unique and personal.
- Highlight both the student's strengths and areas for improvement.
- Encourage a growth mindset in the comments.
- Avoid the use of pronouns (he, she, etc.) in the comments.
- Use the student's first name in the comments.
- For students with an IEP, include a comment on the IEP progress.
    ''')
# Text input for custom instructions
instructions = st.text_area("Instructions:", 
                            label_visibility='hidden', height=200,
                            placeholder='''e.g. 
- Make the comments unique and personal.
- Highlight both the student\'s strengths and areas for improvement. 
- Encourage a growth mindset in the comments.
- Use the student's first name in the comments.''')

###

st.markdown('----')
st.markdown('### Comment Examples (optional but **recommended**!) 💡')
st.markdown('To improve the results, provide some examples of report card comments that you think are awesome!')
comment_examples = st.text_area("Comment Examples:", 
                            label_visibility='hidden', height=200,
                            placeholder='''e.g.
"Sarah demonstrates strong analytical thinking in mathematics, particularly when solving multi-step word problems. During class discussions, Sarah actively contributes creative problem-solving strategies that help peers see alternative approaches. Moving forward, focusing on showing detailed work and checking solutions will help transform good answers into excellent ones."

"Alex has shown steady improvement in reading comprehension this term, especially when working with narrative texts. While Alex can identify main characters and basic plot elements, more practice is needed with making text-to-self connections and drawing deeper inferences. Using the reading strategies we've practiced in class, such as asking questions while reading and making predictions, will help build these higher-level comprehension skills."
''')

_, col2, _ = st.columns(3)

if "more_settings" not in st.session_state:
    st.session_state.more_settings = False

def show_more_settings():
    st.session_state.more_settings = True

if not st.session_state.more_settings:
    more_settings = col2.button("## Optional Settings 🔧", 
                                on_click=show_more_settings,
                                use_container_width=True)  
    input_description = ""
    sentence_range = (3, 6)
    output_description = ""
else:
    ###

    st.markdown('----')
    st.markdown('### Data Description 🔎')
    st.markdown('Need to clarify any formatting or abbreviations in your data? Don\'t worry about it if your data is self-explanatory!')
    with st.expander("Not sure? Check out the **examples** below!"):
        st.markdown('''
    - The "Grade" column uses the following proficiency scale: 
    - Emerging ("Em"), Developing ("D"), Proficient ("P"), Extending ("E").
    - The "Student" column is formatted as "Last Name, First Name".
    - The "IEP Comment" column includes a note for students with an Individualized Education Plan (IEP). If a student does not have an IEP, the cell is left blank.
    - The "Positive Comments" and "Areas to Improve" columns contain brief notes on the student's strengths and areas needing improvement.
        ''')
    input_description = st.text_area("Description:", 
                                    label_visibility='hidden',
                                    placeholder='e.g. The "Grade" column uses the following proficiency scale: Emerging ("Em"), Developing ("D"), Proficient ("P"), Extending ("E").')

    ###

    st.markdown('----')
    st.markdown('### Length of Comments 📏')
    st.markdown('Choose the minimum and maximum number of sentences for each comment.')
    # Sliders and checkboxes for preset options
    sentence_range = st.slider("Number of Sentences", 
                            label_visibility='hidden',
                            min_value=2, max_value=10, value=(3, 6))

    ###

    st.markdown('----')
    st.markdown('### Comment Format 🔠')
    st.markdown('How do you want the comments to be formatted (e.g., column and row names)?')
    with st.expander("Take a look at the **examples** for ideas!"):
        st.markdown('''
    - The output should have the following columns: "Student Name", "Subject", "Comment".
    - The "Student Name" column should contain the student's full name.
    - There should be one row for each subject a student is in. Therefore, each student will three rows in the output (Reading, Writing, and Numeracy).
        ''')
    # Text input for defining the output format
    output_description = st.text_area("Output Format:", 
                                    label_visibility='hidden', 
                                    placeholder='e.g. The output should have the following columns: "Student Name", "Comment".')

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
    # Pass the input data to the first LLM instance
    # Add a validation check before processing
    if student_data.strip():
        if not st.session_state.model_loaded:
            # Reset conversation
            st.session_state["messages"] = []
            # Initialize pipeline
            with st.spinner('Generating initial comments...'):
                # Construct pipiline
                st.session_state['comment_pipeline'] = ReportCardCommentor(model="gpt-4o-mini")
                st.session_state.model_loads +=1
                # Run initial prompt
                entire_response, comments, response = st.session_state.comment_pipeline.get_initial_comments(instructions, 
                                                                                                             comment_examples,
                                                                                                             sentence_range, 
                                                                                                             output_description, 
                                                                                                             student_data, 
                                                                                                             input_description)
                st.session_state["report_comments"] = comments
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
        # Process comments
        comments = st.session_state.comment_pipeline.produce_list(st.session_state.report_comments)
        excel_bytes = st.session_state.comment_pipeline.get_excel_bytes(comments)

        st.markdown('#### Your comments are ready!')
        st.markdown('Use the download button below or click the copy button in the top-right corner of the text area.')
        
        col1, col2 = st.columns(2)

        # Display comments for copying
        col1.code(comments)

        # Generate random string for file name
        random_str = ''.join(random.choices('0123456789', k=6))

        # CSV download button
        col2.download_button(
            label="Download as .csv",
            data=comments,
            file_name=f'report_card_comments_{random_str}.csv',
            mime='text/csv',
            type="primary", 
            use_container_width=True
        )

        # Excel download button
        col2.download_button(
            label="Download as .xlsx (Excel)",
            data=excel_bytes,
            file_name=f'report_card_comments_{random_str}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            type="primary",
            use_container_width=True
        )
    
# Only show chat if model has been loaded
if st.session_state.model_loaded:
    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": rf"{prompt}"})
        st.chat_message("user", avatar=avatar["user"]).write(prompt)
        with st.spinner('Applying edits...'):
            # Apply edits
            entire_response, comments, response = st.session_state.comment_pipeline.user_input(prompt)
        st.session_state.report_comments = comments
        st.session_state.messages.append({"role": "assistant", "content": rf"{response}"})
        st.chat_message("assistant", avatar=avatar["assistant"]).markdown(rf"{response}")
        st.rerun()