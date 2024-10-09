import streamlit as st
import pandas as pd
from st_files_connection import FilesConnection

# Create connection object and retrieve file contents.
conn = st.connection('s3', type=FilesConnection)
df = conn.read("ai-tutors/myfile.csv", input_format="csv", ttl=0)

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
        # Create a new row as a dictionary
        new_row = {"Owner": new_owner, "Pet": new_pet}
        # Append the new row to the DataFrame
        df = df.append(new_row, ignore_index=True)
        # Save the updated DataFrame back to the cloud
        conn.write(df, "ai-tutors/myfile.csv", output_format="csv")
        st.success("New row added and saved to the cloud!")
    else:
        st.error("Please provide both Owner and Pet information.")
    st.rerun()