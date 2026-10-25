import streamlit as st
import re
import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.llms import Ollama
from langchain_google_genai import ChatGoogleGenerativeAI

# --- 1. Initialization ---
@st.cache_resource
def get_embedding_model():
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

@st.cache_resource
def get_vector_db():
    embeddings = get_embedding_model()
    # Loading your pre-existing Chroma DB folder
    return Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

db = get_vector_db()

# Initialize session states for the routing handshake
if "routing_intent" not in st.session_state:
    st.session_state.routing_intent = None
if "current_prompt" not in st.session_state:
    st.session_state.current_prompt = None
if "consent_granted" not in st.session_state:
    st.session_state.consent_granted = False
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 2. The Core Router Engine ---
def predict_routing_intent(prompt: str) -> str:
    # Rule 1: Regex checking for links
    url_pattern = re.compile(r'https?://\S+|www\.\S+')
    if url_pattern.search(prompt):
        return "Web Scraper (BeautifulSoup)"
        
    # Rule 2: Local Semantic Vector Similarity Score Checking
    # similarity_search_with_score returns tuples of (Document, Distance Score)
    # Note: Chroma uses L2 distance by default (0.0 = perfect match, higher = less similar)
    results = db.similarity_search_with_score(prompt, k=1)
    
    if results:
        doc, distance_score = results[0]
        st.sidebar.metric("Closest PDF Chunk Distance", f"{distance_score:.4f}")
        
        # Threshold Tuning: If distance is low, the answer is highly likely in your PDF
        if distance_score < 0.65: 
            return "Local PDF Vector Search"
            
    # Rule 3: Fallback if no URL and no matching PDF content found
    return "Direct LLM (General Knowledge)"

# --- 3. Streamlit Layout & UI ---
st.title("🎯 Verified Intent Hybrid Chatbot")
model_choice = st.sidebar.selectbox("Choose Model", ["Ollama (Local)", "Gemini (Cloud)"])

# Render Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 4. User Prompt Input ---
if user_input := st.chat_input("Ask a question..."):
    # Reset states for the new prompt turn
    st.session_state.current_prompt = user_input
    st.session_state.routing_intent = predict_routing_intent(user_input)
    st.session_state.consent_granted = False
    st.rerun()

# --- 5. The Consent Loop Gate ---
if st.session_state.current_prompt and not st.session_state.consent_granted:
    # Display the user's message pending evaluation
    with st.chat_message("user"):
        st.markdown(st.session_state.current_prompt)
        
    # Trigger routing confirmation card
    with st.status("🛠️ System Routing Pipeline", expanded=True):
        st.write(f"Based on your query, the router intends to use: **{st.session_state.routing_intent}**")
        st.write("Do you want to proceed with this data pathway or manually override it?")
        
        # Allow user to accept or explicitly override the prediction
        chosen_route = st.radio(
            "Confirm or change execution route:",
            ["Local PDF Vector Search", "Web Scraper (BeautifulSoup)", "Direct LLM (General Knowledge)"],
            index=["Local PDF Vector Search", "Web Scraper (BeautifulSoup)", "Direct LLM (General Knowledge)"].index(st.session_state.routing_intent)
        )
        
        if st.button("🟩 Confirm & Execute"):
            st.session_state.routing_intent = chosen_route
            st.session_state.consent_granted = True
            st.rerun()

# --- 6. Verified Execution Phase ---
if st.session_state.consent_granted and st.session_state.current_prompt:
    prompt = st.session_state.current_prompt
    route = st.session_state.routing_intent
    
    # Commit user prompt to persistent visual history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        context = ""
        
        # Branch out safely according to user verified consent
        if route == "Local PDF Vector Search":
            with st.spinner("Extracting localized PDF vectors..."):
                docs = db.similarity_search(prompt, k=3)
                context = "\n".join([d.page_content for d in docs])
                st.info("💡 Context injected using your local documents.")
                
        elif route == "Web Scraper (BeautifulSoup)":
            with st.spinner("Scraping webpage text content..."):
                # Placeholder for your beautifulsoup parsing code block
                context = "Scraped mock context from webpage." 
                st.info("🌐 Context injected using web scraper tool.")
                
        else:
            st.info("🚀 Routing directly to raw LLM workspace.")

        # Initialize designated inference client
        llm = Ollama(model="llama3") if model_choice == "Ollama (Local)" else ChatGoogleGenerativeAI(model="gemini-1.5-flash")
        
        # Package and invoke final context augmented execution
        final_prompt = f"Context:\n{context}\n\nQuestion: {prompt}" if context else prompt
        
        with st.spinner("Generating final response..."):
            # Adjust according to how your original app called the models
            response = llm.invoke(final_prompt)
            # Support text retrieval from both object types gracefully
            output_text = response if isinstance(response, str) else response.content
            
            st.markdown(output_text)
            st.session_state.messages.append({"role": "assistant", "content": output_text})
            
    # Clear active staging variables to prepare for next input prompt loop
    st.session_state.current_prompt = None
    st.session_state.routing_intent = None
    st.session_state.consent_granted = False
