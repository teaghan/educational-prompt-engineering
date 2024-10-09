import streamlit as st
from st_files_connection import FilesConnection

# Create connection object and retrieve file contents.
conn = st.connection('s3', type=FilesConnection)
df = conn.read("ai-tutors/myfile.csv", input_format="csv", ttl=0)

# Print results.
for row in df.itertuples():
    st.write(f"{row.Owner} has a :{row.Pet}:")