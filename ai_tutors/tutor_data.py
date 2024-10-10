import streamlit as st
import pandas as pd
from st_files_connection import FilesConnection

def read_csv(fn):
    # Create connection object and retrieve file contents.
    conn = st.connection('s3', type=FilesConnection, ttl=0)
    # Return pandas dataframe
    return conn.read(fn, input_format="csv", ttl=0) 

def write_csv(fn, df):
    # Create connection object and write file contents.
    conn = st.connection('s3', type=FilesConnection, ttl=0)
    with conn.open(fn, "wt") as f:
        df.to_csv(f, index=False)

def select_instructions(df, tool_name):
    # Select the row where the Name matches the given name
    selected_row = df[df["Name"] == tool_name]

    # Extract the Instructions and Guidelines for the selected row
    if not selected_row.empty:
        instructions = selected_row["Instructions"].values[0]
        guidelines = selected_row["Guidelines"].values[0]
        return instructions, guidelines
    else:
        print(f"No entry found for {name_to_find}")