import streamlit as st
import pandas as pd
from st_files_connection import FilesConnection

ai_tutors_data_fn = 'ai-tutors/myfile.csv'

st.set_page_config(page_title="AI Science Tutor", page_icon="https://raw.githubusercontent.com/teaghan/educational-prompt-engineering/main/images/science_tutor_favicon_small.png", layout="wide")

'''
# Create connection object and retrieve file contents.
conn = st.connection('s3', type=FilesConnection, ttl=0)
df = conn.read(ai_tutors_data_fn, input_format="csv", ttl=0)

# Print existing records.
st.write("Existing records:")
for row in df.itertuples():
    st.write(f"{row.Owner} has a :{row.Pet}:")

# Add a new row via user input
st.write("Add a new record:")
new_owner = st.text_input("Owner name")
new_pet = st.text_input("Pet type")

if st.button("Add new row"):
    if new_owner and new_pet:
        # Create a new row as a DataFrame
        new_row = pd.DataFrame({"Owner": [new_owner], "Pet": [new_pet]})
        # Concatenate the new row to the DataFrame
        df = pd.concat([df, new_row], ignore_index=True)
        with conn.open(ai_tutors_data_fn, "wt") as f:
            df.to_csv(f, index=False)
        st.success("New row added and saved to the cloud!")
    else:
        st.error("Please provide both Owner and Pet information.")
    st.rerun()
'''
