import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import os

# --- PAGE SETUP ---
st.set_page_config(page_title="My AI Assistant", page_icon="🎙️", layout="wide")

# --- API KEY MANAGEMENT ---
# This safely checks if we are on the Cloud or Local
try:
    if "GROQ_API_KEY" in st.secrets:
        groq_api_key = st.secrets["GROQ_API_KEY"]
        tavily_api_key = st.secrets["TAVILY_API_KEY"]
    else:
        # We use empty strings here so GitHub doesn't complain!
        # You will add the real keys in the Cloud Settings later.
        groq_api_key = "placeholder_key" 
        tavily_api_key = "placeholder_key"
except FileNotFoundError:
    groq_api_key = "placeholder_key"
    tavily_api_key = "placeholder_key"

# --- CLIENT SETUP ---
# If keys are missing, stop the app and show a warning
if groq_api_key == "placeholder_key":
    st.warning("⚠️ Application is running, but API Keys are missing.")
    st.info("If you are on Streamlit Cloud, go to Settings -> Secrets and add your keys.")
    st.stop()

client = Groq(api_key=groq_api_key)
tavily = TavilyClient(api_key=tavily_api_key)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🎛️ Controls")
    
    st.subheader("🎤 Voice Input")
    audio_bytes = audio_recorder(text="Click to Talk", icon_size="2x", key="recorder")
    
    st.divider()
    
    st.subheader("🎭 Personality")
    personality = st.selectbox(
        "Choose Style:",
        ["Helpful Assistant 🤖", "Sarcastic Friend 🙄", "Code Wizard 💻", "Explain Like I'm 5 👶"]
    )
    
    if st.button("🗑️ Clear History"):
        st.session_state.messages = []
        st.rerun()

# --- MAIN APP ---
st.title("🎙️ My Personal AI Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- VOICE TRANSCRIPTION ---
voice_prompt = None
if audio_bytes:
    with st.spinner("👂 Listening..."):
        try:
            transcription = client.audio.transcriptions.create(
                file=("temp_audio.wav", audio_bytes),
                model="whisper-large-v3-turbo",
                response_format="json",
                language="en"
            )
            voice_prompt = transcription.text
        except Exception as e:
            st.error(f"Microphone Error: {e}")

# --- DISPLAY MESSAGES ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- INPUT HANDLING ---
prompt = st.chat_input("Type something...")
if voice_prompt:
    prompt = voice_prompt

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        status = st.status("🧠 Thinking...", expanded=True)
        try:
            status.write("🔍 Searching the web...")
            search_results = tavily.search(query=prompt, max_results=2)
            context = ""
            for result in search_results['results']:
                context += f"Source: {result['title']}\nContent: {result['content']}\n\n"
            
            status.write(f"✍️ Drafting response as {personality}...")
            
            if "Sarcastic" in personality:
                sys_msg = "You are a sarcastic, witty AI."
            elif "Code" in personality:
                sys_msg = "You are a senior developer. Focus on code blocks."
            elif "Explain" in personality:
                sys_msg = "You are a kindergarten teacher. Use emojis."
            else:
                sys_msg = "You are a helpful assistant."

            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": f"{sys_msg}\n\nContext: {context}"},
                    {"role": "user", "content": prompt}
                ]
            )
            response = completion.choices[0].message.content
            
            status.update(label="Done!", state="complete", expanded=False)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            tts = gTTS(text=response, lang='en')
            tts.save("response.mp3")
            st.audio("response.mp3", autoplay=False)
            
        except Exception as e:
            st.error(f"Error: {e}")