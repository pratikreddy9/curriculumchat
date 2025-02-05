import streamlit as st
import pymongo
from pymongo import MongoClient
import requests
import json
from urllib.parse import quote_plus

# Load secrets from st.secrets
OPENAI_API_KEY = st.secrets["openai"]["api_key"]
MONGO_USERNAME = st.secrets["mongodb"]["username"]
MONGO_PASSWORD = st.secrets["mongodb"]["password"]
MONGO_HOST = st.secrets["mongodb"]["host"]
MONGO_PORT = st.secrets["mongodb"]["port"]
MONGO_DB = st.secrets["mongodb"]["database"]
MONGO_COLLECTION = st.secrets["mongodb"]["collection"]

# Set up MongoDB connection
mongo_uri = f"mongodb://{quote_plus(MONGO_USERNAME)}:{quote_plus(MONGO_PASSWORD)}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}"
client = MongoClient(mongo_uri)
db = client[MONGO_DB]
collection = db[MONGO_COLLECTION]

# Function to retrieve relevant chunks from MongoDB
def retrieve_context(user_query):
    """Search MongoDB for relevant text chunks based on user query."""
    query_results = collection.find({})  # Fetch all stored documents
    relevant_chunks = []
    
    for doc in query_results:
        for chunk in doc["text_chunks"]:
            if user_query.lower() in chunk["text"].lower():  # Simple keyword match
                relevant_chunks.append(chunk["text"])
    
    return "\n".join(relevant_chunks[:3])  # Return top 3 relevant chunks

# Function to generate OpenAI chat response
def get_openai_response(user_query, context):
    """Calls OpenAI API to generate chatbot responses with context."""
    messages = [
        {"role": "system", "content": "You are a helpful assistant for curriculum-based Q&A."},
        {"role": "user", "content": f"Context:\n{context}\n\nUser Query: {user_query}"}
    ]

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    data = {
        "model": "gpt-4o",
        "messages": messages,
        "temperature": 0.5
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return "Error fetching response from OpenAI."

# Streamlit UI Setup
st.set_page_config(page_title="Curriculum Chatbot", layout="wide")
st.title("📘 Curriculum Chatbot")
st.write("Ask questions related to the curriculum!")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display chat history
for chat in st.session_state.chat_history:
    if chat["role"] == "user":
        st.markdown(f"<div style='border: 2px solid blue; padding: 10px; margin: 10px 0; border-radius: 8px; width: 80%; float: right; clear: both;'>{chat['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='border: 2px solid green; padding: 10px; margin: 10px 0; border-radius: 8px; width: 80%; float: left; clear: both;'>{chat['content']}</div>", unsafe_allow_html=True)

# Input field
user_query = st.text_input("Type your message here:")

# Button to send message
if st.button("Send"):
    if user_query:
        # Append user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_query})

        # Retrieve relevant curriculum data
        context = retrieve_context(user_query)

        # Get chatbot response
        chatbot_response = get_openai_response(user_query, context)

        # Append chatbot response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": chatbot_response})

        # Refresh UI
        st.experimental_rerun()
