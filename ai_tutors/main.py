import streamlit as st
import pandas as pd
from tutor_data import read_csv, select_instructions

st.session_state["ai_tutors_data_fn"] = 'ai-tutors/tutor_info.csv'

st.set_page_config(page_title="AI Tutors", page_icon="https://raw.githubusercontent.com/teaghan/educational-prompt-engineering/main/images/science_tutor_favicon_small.png", layout="wide")

st.markdown("<h1 style='text-align: center; color: grey;'>Build an AI Tutor</h1>", unsafe_allow_html=True)

df_tutors = read_csv(st.session_state["ai_tutors_data_fn"])

switch_page = st.button("Load Tutor")
if switch_page:
    # Switch to the selected page
    tool_name = 'AI Science Tutor'
    st.session_state["instructions"], st.session_state["guidelines"] = select_instructions(df_tutors, 
                                                                                           tool_name=tool_name)
    st.session_state["tool name"] = tool_name
    st.switch_page('pages/tutor_main.py')

create_tutor = st.button("Build an AI Tutor")
if create_tutor:
    st.switch_page('pages/create_tutor_main.py')