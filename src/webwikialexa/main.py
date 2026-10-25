import streamlit as st
from webwikialexa.core import run_llm

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

st.set_page_config(page_title="Assistant ChatBot", page_icon="🤖")
st.title("🤖 Assistant ChatBot")
#st.caption("ℹ️ *This assistant handles inquiries focused strictly on JIM CORBETT PARK Hotels/ Suites availability*")
st.caption("ℹ️ *This assistant handles chit chat for any topic*")
st.divider()

initialPrompt = [
    {
        "role": "assistant", 
        "content": "How can I help you today?"
    }
]

# Initialize Conversation Memory
if("history" not in st.session_state):
    st.session_state["history"] = initialPrompt.copy()

with st.sidebar:
    st.header("⚙️ Controls")
    if st.button("Clear Chat History", use_container_width=True):
        st.session_state["history"] = initialPrompt.copy()
        st.cache_data.clear() 
        st.rerun()        # Force fully fresh UI draw

# Display chat History
for mssg in st.session_state["history"]:
     avatar_choice = "🤖" if mssg["role"] == "assistant" else None
     with st.chat_message(mssg["role"], avatar=avatar_choice):
        st.markdown(mssg["content"])
    
# User Input 
if prompt:= st.chat_input("Type your message here..."):
    # add User message
    template = {
        "role" : "user", 
        "content": prompt         
    }
    st.session_state["history"].append(template)
    
    # to add markdonw
    st.chat_message("user").markdown(prompt)
    
    with st.spinner("Searching response..."):   
        reply = run_llm(st.session_state["history"])

    # add Assitant response also to memory
    template = { "role": "assitant", "content": reply }
    st.session_state["history"].append(template)

    # to add markdown
    st.chat_message("assistant").markdown(reply)


