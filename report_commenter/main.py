import os
import streamlit as st
import pandas as pd

import sys
cur_dir = os.path.dirname(__file__)
sys.path.append(cur_dir)
from save_to_csv import convert_messages_to_markdown, markdown_to_html, is_valid_file_name
from drop_file import increment_file_uploader_key, extract_text_from_different_file_types, change_to_prompt_text
from chain_engine import ReportCardCommentor

# Streamlit
st.set_page_config(page_title="Report Cards", page_icon="https://raw.githubusercontent.com/teaghan/educational-prompt-engineering/main/images/rc_favicon.png", layout="wide")

# Title
st.markdown("<h1 style='text-align: center; color: grey;'>Report Card Comment Generator</h1>", unsafe_allow_html=True)

# Title and introduction
st.write("Upload your class CSV file and generate personalized report card comments for your students.")


# Interaction Tips
with st.expander("Instructions and Example"):
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
    4. The file will automatically download to your device.

**Example CSV Description:**
- The "Grade" column uses the following proficiency scale: 
  - Emerging ("Em"), Developing ("D"), Proficient ("P"), Extending ("E").
- The "Student" column is formatted as "Last Name, First Name".
- The "IEP Comment" column includes a note for students with an Individualized Education Plan (IEP). If a student does not have an IEP, the cell is left blank.
- The "Positive Comments" and "Areas to Improve" columns contain brief notes on the student’s strengths and areas needing improvement.

**Example Instructions for Writing the Comments:**
- Each comment should be 4-6 sentences long.
- Highlight both the student’s strengths and areas for improvement.
- Encourage a growth mindset in the comments.
- Use the student's first name only when writing the comments.
    ''')

# FILE UPLOAD
if "drop_file" not in st.session_state:
    st.session_state.drop_file = False
if "zip_file" not in st.session_state:
    st.session_state.zip_file = False
if "file_uploader_key" not in st.session_state:
    st.session_state.file_uploader_key = 0

dropped_files = st.file_uploader("Drop a file or multiple files (.csv, .txt, .rtf)", 
                                            accept_multiple_files=True,
                                            key=st.session_state.file_uploader_key)

if dropped_files is not None:

    st.session_state.drop_file = True
    
    # Load file contents
    student_data =""
    if dropped_files != []:
        for dropped_file in dropped_files:   
            extract = extract_text_from_different_file_types(dropped_file)