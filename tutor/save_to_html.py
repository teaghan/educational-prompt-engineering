# from https://github.com/tonypeng1/Personal-ChatGPT/blob/main/personal-chatgpt

import re
from typing import List, Dict
import markdown
from pygments.formatters import HtmlFormatter
import streamlit as st

def convert_messages_to_markdown(messages: List[Dict[str, str]], code_block_indent='                 ') -> str:
    """
    Converts a list of message dictionaries to a markdown-formatted string.

    Each message is formatted with the sender's role as a header and the message content as a blockquote.
    Code blocks within the message content are detected and indented accordingly.

    Args:
        messages (List[Dict[str, str]]): A list of message dictionaries, where each dictionary contains
                                         'role' and 'content' keys.
        code_block_indent (str): The string used to indent lines within code blocks.

    Returns:
        A markdown-formatted string representing the messages.
    """
    markdown_lines = []
    for message in messages:
        role = message['role']
        if role=='assistant':
            role='tutor'
        content = message['content']
        indented_content = _indent_content(content, code_block_indent)
        markdown_lines.append(f"###*{role.capitalize()}*:\n{indented_content}\n")
    return '\n\n'.join(markdown_lines)


def _indent_content(content: str, code_block_indent: str) -> str:
    """
    Helper function to indent the content for markdown formatting.

    Args:
        content (str): The content of the message to be indented.
        code_block_indent (str): The string used to indent lines within code blocks.

    Returns:
        The indented content as a string.
    """
    if content is not None:
        lines = content.split('\n')
        indented_lines = []
        in_code_block = False  # Flag to track whether we're inside a code block

        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                indented_lines.append(line)
            elif not in_code_block:
                line = f"> {line}"
                indented_lines.append(line)
            else:
                indented_line = code_block_indent + line  # Apply indentation
                indented_lines.append(indented_line)

        return '\n'.join(indented_lines)
    
    else:
        return ""


def markdown_to_html(md_content: str) -> str:
    """
    Converts markdown content to HTML with syntax highlighting and custom styling.

    This function takes a string containing markdown-formatted text and converts it to HTML.
    It applies syntax highlighting to code blocks and custom styling to certain HTML elements.

    Args:
        md_content (str): A string containing markdown-formatted text.

    Returns:
        A string containing the HTML representation of the markdown text, including a style tag
        with CSS for syntax highlighting and custom styles for the <code> and <em> elements.
    """

    # Convert markdown to HTML with syntax highlighting
    html_content = markdown.markdown(md_content, extensions=['fenced_code', 'codehilite'])

    html_content = re.sub(
        r'<code>', 
        '<code style="background-color: #f7f7f7; color: green;">', 
        html_content)
    
    html_content = re.sub(
        r'<h3>', 
        '<h3 style="color: blue;">', 
        html_content)
    
    # Get CSS for syntax highlighting from Pygments
    css = HtmlFormatter(style='tango').get_style_defs('.codehilite')

    # Insert MathJax
    html_content = insert_mathjax(f"<style>{css}</style>{html_content}")

    return html_content

def insert_mathjax(html_content: str) -> str:
    """
    Inserts the MathJax script and configuration into the HTML content.

    The MathJax script is placed before the closing </head> tag in the HTML content.

    Args:
        html_content (str): The original HTML content.

    Returns:
        The HTML content with the MathJax script and configuration inserted.
    """
    mathjax_script = """
    <!-- Load MathJax -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/latest.js?config=TeX-AMS_CHTML-full,Safe"></script>
    <!-- MathJax configuration -->
    <script type="text/x-mathjax-config">
      MathJax.Hub.Config({
        TeX: {
          equationNumbers: {
            autoNumber: "AMS",
            useLabelIds: true
          }
        },
        tex2jax: {
          inlineMath: [ ['\\(','\\)'], ['$', '$'] ],
          displayMath: [ ['\\[','\\]'], ['$$','$$'] ],
          processEscapes: true,
          processEnvironments: true,
          inlineMathDelimiter: {
            left: "$",
            right: "$",
            pattern: "\\\\\\(.*?\\\\\\)|\\\\\\[.*?\\\\\\]|[^\\\\](?:\\\\[(?!\\[)|\\\\[(?!\\[)|[^\\\\]|\\$\\$).*?\\$\\$",
            escapeChar: "\\\\"
          },
        },
        displayAlign: 'center',
        CommonHTML: {
          linebreaks: {
            automatic: true
          }
        }
      });
      MathJax.Hub.Queue(["Typeset", MathJax.Hub]);
    </script>
    """

    # Insert the MathJax script before the closing </head> tag
    if "</head>" in html_content:
        html_content = html_content.replace("</head>", f"{mathjax_script}</head>")
    else:
        # If there's no </head> tag, insert the MathJax script at the beginning
        html_content = f"{mathjax_script}\n{html_content}"
    
    return html_content

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