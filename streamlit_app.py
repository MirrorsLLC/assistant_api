import os
import time
import datetime

import streamlit as st
import openai
from dotenv import load_dotenv, find_dotenv

from assitant_api import init_assistant, get_response



st.title("Real Estate Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []


# Load environment variables and connect to db
if "chat_initiated" not in st.session_state:
    # Get environment variables
    _ = load_dotenv(find_dotenv()) # read local .env file
    openai_api_key = os.getenv('OPENAI_API_KEY', default=None)
    assistant_id = os.getenv('ASSISTANT_ID', default=None)

    # Initialize assistant
    st.session_state.manager = init_assistant(openai_api_key, assistant_id)

    # Connect to database
    st.session_state.chat_initiated = True

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    if message['role'] != 'system':
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input(""):

    # Add user message to chat history
    message = {"role": "user", "content": prompt}
    st.session_state.messages.append(message)

    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant response generating
    ai_content = get_response(st.session_state.manager, st.session_state.messages)

    # Save assistant response to database
    message = {"role": 'assistant', "content": ai_content}

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        # Simulate stream of response with milliseconds delay
        for chunk in ai_content.split():
            full_response += chunk + " "
            time.sleep(0.05)
            # Add a blinking cursor to simulate typing
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
