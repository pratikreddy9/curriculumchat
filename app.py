import streamlit as st
import pymongo
from pymongo import MongoClient
import requests
import json
import numpy as np

# Load OpenAI API key from Streamlit secrets
OPENAI_API_KEY = st.secrets["openai"]["api_key"]

# MongoDB Connection Details (Hardcoded)
MONGO_HOST = "notify.pesuacademy.com"
MONGO_PORT = 27017
MONGO_USERNAME = "admin"
MONGO_PASSWORD = "Ayotta@123"
MONGO_AUTH_DB = "admin"
MONGO_DB_NAME = "knowledge_database"
MONGO_COLLECTION_NAME = "curriculum_data"

# Establish MongoDB Connection
try:
    client = MongoClient(
        host=MONGO_HOST,
        port=MONGO_PORT,
        username=MONGO_USERNAME,
        password=MONGO_PASSWORD,
        authSource=MONGO_AUTH_DB  # Always authenticate against "admin"
    )
    
    # Access database and collection
    db = client[MONGO_DB_NAME]
    collection = db[MONGO_COLLECTION_NAME]
    
    print("✅ Connected successfully to MongoDB!")
except Exception as e:
    st.error(f"❌ MongoDB connection failed: {e}")
    st.stop()  # Prevent further execution if DB fails

# Function to create OpenAI embeddings
def create_embedding(text):
    """Generate embeddings using OpenAI API."""
    data = {"input": text, "model": "text-embedding-3-large"}
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}

    response = requests.post("https://api.openai.com/v1/embeddings", headers=headers, json=data)

    if response.status_code == 200:
        return response.json()['data'][0]['embedding']
    else:
        return None  # If embedding fails, return None

# Function to retrieve relevant text chunks from MongoDB
def retrieve_context(user_query):
    """Finds most relevant stored text chunks using query embedding similarity."""
    
    # Generate query embedding
    query_embedding = create_embedding(user_query)
    if query_embedding is None:
        return "❌ Failed to generate query embedding."

    query_embedding = np.array(query_embedding)  # Convert to numpy array
    results = []
    
    # Fetch all stored text chunks from MongoDB
    for doc in collection.find({}):
        for chunk in doc["text_chunks"]:
            chunk_embedding = np.array(chunk["embedding"])
            
            # Compute cosine similarity
            similarity = np.dot(query_embedding, chunk_embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding))
            results.append((similarity, chunk["text"], doc["page_number"], chunk["chunk_number"]))

    # Sort by highest similarity
    results = sorted(results, key=lambda x: x[0], reverse=True)[:3]  # Top 3 most relevant chunks

    if not results:
        return "No relevant data found in the database."

    # Format retrieved chunks
    context_text = ""
    for sim, text, page, chunk_num in results:
        context_text += f"🔹 **Page {page}, Chunk {chunk_num} (Similarity: {sim:.2f})**\n{text}\n\n"

    return context_text

# Function to generate chatbot response using OpenAI API
def get_openai_response(user_query, context):
    """Generates chatbot response using OpenAI API."""
    messages = [
        {"role": "system", "content": "You are a curriculum chatbot. Use the given context to provide helpful responses."},
        {"role": "user", "content": f"Context:\n{context}\n\nUser Query: {user_query}"}
    ]

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    data = {"model": "gpt-4o", "messages": messages, "temperature": 0.5}

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return "❌ OpenAI API error."

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

# Input field for user query
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

        # Show retrieved chunks
        st.write("### 🔎 Retrieved Chunks Used for Response")
        st.write(context)

        # Refresh UI
        st.experimental_rerun()
