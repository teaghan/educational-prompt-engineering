import streamlit as st
import pandas as pd
from st_files_connection import FilesConnection

ai_tutors_data_fn = 'ai-tutors/tutor_info.csv'

st.set_page_config(page_title="AI Tutors", page_icon="https://raw.githubusercontent.com/teaghan/educational-prompt-engineering/main/images/science_tutor_favicon_small.png", layout="wide")

st.markdown("<h1 style='text-align: center; color: grey;'>Build an AI Tutor</h1>", unsafe_allow_html=True)

def read_csv(fn):
    # Create connection object and retrieve file contents.
    with st.connection('s3', type=FilesConnection, ttl=0) as conn:
        # Return pandas dataframe
        return conn.read(fn, input_format="csv", ttl=0) 

def write_csv(fn, df):
    # Create connection object and write file contents.
    with st.connection('s3', type=FilesConnection, ttl=0) as conn:
        with conn.open(fn, "wt") as f:
            df.to_csv(f, index=False)


df = read_csv(fn)

st.text(dir(conn))

# Print existing records.
st.write("Existing records:")
for row in df.itertuples():
    st.write(f"Name: {row.Name}")
    st.markdown(f"{row.Instructions}")
    st.markdown(f"{row.Guidelines}")

# Add a new row via user input
st.write("Add a new record:")
new_name = st.text_input("Name")
new_instr = st.text_input("Instructions")
new_guide = st.text_input("Guidelines")

if st.button("Add new tutor"):
    if new_name and new_instr and new_guide:
        # Create a new row as a DataFrame
        new_row = pd.DataFrame({"Name": [new_name], "Instructions": [new_instr], "Guidelines": [new_guide]})
        # Concatenate the new row to the DataFrame
        df = pd.concat([df, new_row], ignore_index=True)
        write_csv(ai_tutors_data_fn, df)

        st.success("New row added and saved to the cloud!")
    else:
        st.error("Please provide all of the info.")
    st.rerun()
