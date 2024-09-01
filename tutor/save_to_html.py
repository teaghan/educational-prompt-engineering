# from https://github.com/tonypeng1/Personal-ChatGPT/blob/main/personal-chatgpt

import re
from typing import List, Dict
import markdown
from markdown_katex import KaTeXExtension
from pygments.formatters import HtmlFormatter
import streamlit as st

def convert_messages_to_markdown(messages: List[Dict[str, str]], code_block_indent='                 ') -> str:
    markdown_lines = []
    for message in messages:
        role = message['role']
        if role == 'assistant':
            role = 'tutor'
        content = message['content']
        indented_content = _indent_content(content, code_block_indent)
        markdown_lines.append(f"###*{role.capitalize()}*:\n{indented_content}\n")
    return '\n\n'.join(markdown_lines)

def _indent_content(content: str, code_block_indent: str) -> str:
    if content is not None:
        lines = content.split('\n')
        indented_lines = []
        in_code_block = False

        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                indented_lines.append(line)
            elif not in_code_block:
                line = f"> {line}"
                indented_lines.append(line)
            else:
                indented_line = code_block_indent + line
                indented_lines.append(indented_line)

        return '\n'.join(indented_lines)
    
    else:
        return ""

def markdown_to_html(md_content: str) -> str:
    # Convert markdown to HTML with syntax highlighting and LaTeX support
    html_content = markdown.markdown(
        md_content, 
        extensions=['fenced_code', 'codehilite', KaTeXExtension()]
    )

    html_content = re.sub(
        r'<code>', 
        '<code style="background-color: #f7f7f7; color: green;">', 
        html_content
    )

    html_content = re.sub(
        r'<h3>', 
        '<h3 style="color: blue;">', 
        html_content
    )

    # Get CSS for syntax highlighting from Pygments
    css = HtmlFormatter(style='tango').get_style_defs('.codehilite')

    # Include KaTeX stylesheet in the output
    katex_css = (
        '<link rel="stylesheet" '
        'href="https://cdn.jsdelivr.net/npm/katex@0.13.18/dist/katex.min.css">'
    )

    return f"{katex_css}<style>{css}</style>{html_content}"

def is_valid_file_name(file_name: str) -> bool:
    """
    Checks if the provided file name is valid based on certain criteria.

    This function checks the file name against a set of rules to ensure it does not contain
    illegal characters, is not one of the reserved words, and does not exceed 255 characters in length.

    Args:
        file_name (str): The file name to validate.

    Returns:
        bool: True if the file name is valid, False otherwise.
    """
    illegal_chars = r'[\\/:"*?<>|]'
    reserved_words = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                      'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 
                      'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']

    # Check for illegal characters, reserved words, and length constraint
    return not (re.search(illegal_chars, file_name) or
                file_name in reserved_words or
                len(file_name) > 255)