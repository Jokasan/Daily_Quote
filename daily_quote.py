import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import os
import yaml
import requests

if 'OPENAI_API_KEY' not in st.session_state:
    st.session_state['OPENAI_API_KEY'] = yaml.safe_load(open('/Users/nilsindreiten/Documents/Python/DS4B_301_P2_DEV_SQL/credentials.yml'))['openai']
if 'previous_quotes' not in st.session_state:
    st.session_state['previous_quotes'] = set()

st.set_page_config(page_title="Daily Quote Generator", layout="wide")


# Custom CSS for playful theme
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(120deg, #FF9A8B 0%, #FF6A88 55%, #FF99AC 100%);
    }
    .stButton > button {
        background: linear-gradient(45deg, #2ecc71, #3498db);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-size: 1.1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
    }
    .quote-box {
        background: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    h1 {
        font-family: 'Segoe UI', sans-serif;
        color: white !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    h3 {
        color: #2c3e50;
        font-size: 1.5rem !important;
    }
    .stSidebar {
        background-color: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    </style>
""", unsafe_allow_html=True)


themes = {
    "Inspiration & Motivation": "inspirational and motivational quotes that encourage personal growth",
    "Love & Relationships": "quotes about love, relationships, and human connection",
    "Philosophy & Wisdom": "philosophical quotes about life's deeper meanings",
    "Science & Innovation": "quotes about scientific discovery and innovation",
    "Art & Creativity": "quotes about artistic expression and creativity"
}

decades = [
    "Pre-1900s",
    "1900-1950",
    "1950-1980",
    "1980-2000",
    "2000-Present"
]

with st.sidebar:
    st.markdown("### 🎨 Customize Your Quote")
    selected_theme = st.selectbox("Choose a Theme", list(themes.keys()))
    selected_decade = st.selectbox("Choose an Era", decades)
    
    st.markdown("### ⚙️ Model Settings")
    selected_model = st.selectbox("Model",  ["gpt-4o-mini"])
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.8, step=0.1,
                          help="Higher values make output more random, lower values more deterministic")

st.markdown("<h1 style='text-align: center;'>✨ Daily Quote Generator✨</h1>", unsafe_allow_html=True)

llm = ChatOpenAI(
    model=selected_model,
    temperature=temperature,
    openai_api_key=st.session_state['OPENAI_API_KEY']
)

quote_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a knowledgeable assistant that generates meaningful quotes. Never repeat a previously generated quote. Each quote should be unique and original for the given theme and era."),
    ("user", """Generate a {theme} from the {decade} era. The quote must be different from these previous quotes: {prev_quotes}
    Format the response as:
    Quote: [The quote]
    Author: [Author's name]
    Context: [2-3 sentences of context]""")
])

image_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an assistant that generates image search queries based on quotes."),
    ("user", "Create a specific image search query for a {theme} quote. The query should be descriptive but avoid names. Format: only return the search query.")
])

def get_image_url(query):
    try:
        headers = {'Authorization': yaml.safe_load(open('/Users/nilsindreiten/Documents/Python/Daily_Quote_App/credentials.yaml'))['PEXELS_API_KEY']}
        response = requests.get(
            f"https://api.pexels.com/v1/search?query={query}&per_page=1",
            headers=headers
        )
        return response.json()['photos'][0]['src']['large']
    except:
        return None

def generate_quote():
    prev_quotes_str = ", ".join(st.session_state['previous_quotes'])
    quote_response = llm.invoke(
        quote_prompt.format(
            theme=themes[selected_theme],
            decade=selected_decade,
            prev_quotes=prev_quotes_str
        )
    )
    
    # Store the new quote
    quote_text = quote_response.content.split('\n')[0].split(':', 1)[1].strip()
    st.session_state['previous_quotes'].add(quote_text)
    
    image_query = llm.invoke(
        image_prompt.format(
            theme=themes[selected_theme]
        )
    )
    image_url = get_image_url(image_query.content)
    return quote_response.content, image_url

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("Generate Quote", use_container_width=True):
        with st.spinner("✨ Creating your quote..."):
            try:
                quote_response, image_url = generate_quote()
                
                text_col, image_col = st.columns([3, 2])
                
                with text_col:
                    parts = quote_response.split('\n')
                    for part in parts:
                        if part.startswith("Quote:"):
                            st.markdown(f"### {part.split(':', 1)[1].strip()}")
                        elif part.startswith("Author:"):
                            st.markdown(f"*— {part.split(':', 1)[1].strip()}*")
                        elif part.startswith("Context:"):
                            st.markdown(f"\n{part.split(':', 1)[1].strip()}")
                
                with image_col:
                    if image_url:
                        st.markdown(
                            f"""
                            <div style="display: flex; justify-content: center;">
                                <img src="{image_url}" style="max-width: 100%; height: auto;">
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.warning("Could not generate a relevant image.")
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

st.markdown("---")
st.markdown("<div style='text-align: center;'>Powered by OpenAI and Pexels</div>", unsafe_allow_html=True)
