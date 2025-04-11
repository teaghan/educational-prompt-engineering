import streamlit as st
import os
import json
from pathlib import Path

# Set page configuration
st.set_page_config(
    page_title="Test",
    page_icon="📚",
    layout="wide"
)

# Create JSON file on button click
if st.button("Create JSON File"):
    # Create the data directory if it doesn't exist
    Path("static").mkdir(exist_ok=True)
    
    # Create a simple JSON file
    data = {
        "message": "Hello from the JSON file!",
        "created_at": "2024-04-10"
    }
    
    with open("static/sample.json", "w") as f:
        json.dump(data, f, indent=4)
    
    st.success("JSON file created at static/sample.json")

    st.write(os.listdir("./static"))
