import streamlit as st
import requests

st.set_page_config(page_title="My Personal AI Assistant", page_icon="🤖")
st.title("🎙️ My Personal AI Assistant")

# Securely fetch API key from Streamlit Secrets
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except KeyError:
    st.error("Missing GROQ_API_KEY. Please add it to your Streamlit Secrets.")
    st.stop()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

with st.sidebar:
    st.header("🎛️ Controls")
    st.button("Click to Talk")
    st.divider()
    st.header("🎭 Personality")
    st.selectbox("Choose Style:", ["Helpful Assistant 🤓"])
    if st.button("🗑️ Clear History"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Type something..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            # The syntax error was caused by a missing comma in this payload dictionary
            payload = {
                "model": "llama3-8b-8192",
                "messages": st.session_state.messages
            }
            try:
                response = requests.post(GROQ_API_URL, headers=headers, json=payload).json()
                if "error" in response:
                    st.error(response["error"]["message"])
                else:
                    response_text = response["choices"][0]["message"]["content"]
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                st.error(f"Connection Error: {e}")
