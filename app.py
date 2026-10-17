import os
import json
import streamlit as st
from google import genai

st.set_page_config(page_title="AI Technical Sales Copilot", page_icon="⚙️", layout="wide")

company_slug = st.query_params.get("company", "habonim")
demo_file = f"demos/{company_slug}.json"

if not os.path.exists(demo_file):
    st.error(f"Catalog '{company_slug}' not found.")
    st.stop()

with open(demo_file, "r", encoding="utf-8") as f:
    catalog_data = json.load(f)

with st.sidebar:
    st.markdown(f"### ⚙️ {catalog_data['company_name']}")
    st.caption(f"**Loaded Catalog:** {catalog_data['product_category']}")
    st.divider()
    st.markdown("#### 🧪 Click a Test Sizing Query:")
    
    selected_q = None
    for idx, q in enumerate(catalog_data["trojan_horse_questions"]):
        if st.button(f"Test #{idx+1}: {q['buyer_question'][:60]}...", key=f"q_{idx}", use_container_width=True):
            selected_q = q["buyer_question"]

    st.divider()
    st.caption("⚡ Instant SKU matching, spec table lookup & page citations.")

st.title(f"{catalog_data['company_name']} — AI Technical Sales & Sizing Copilot")
st.markdown("Ask any technical question (part numbers, pressure/temperature ratings, dimensions, or actuation sizing). Every response cites the exact catalog page.")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "query_count" not in st.session_state:
    st.session_state.query_count = 0

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_query = st.chat_input("Ask an engineering or part-selection question...")
if selected_q:
    user_query = selected_q

if user_query:
    if st.session_state.query_count >= 25:
        st.warning("Preview limit reached. Reply to our message to unlock unlimited team access.")
        st.stop()

    st.session_state.query_count += 1
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Cross-referencing catalog specification tables..."):
            api_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", None)
            client = genai.Client(api_key=api_key)

            system_prompt = f"""
            You are a Senior Application Engineer for {catalog_data['company_name']}.
            Answer the technical sizing or part-selection question using ONLY the extracted catalog data below.
            
            STRICT RULES:
            1. State the exact Part Number / Ordering Code in bold.
            2. Cite the exact [Page X] where the specification appears.
            3. Show relevant technical ratings in a clean Markdown table.
            4. End with a short "Ready-to-Send Customer Quote Snippet" a sales rep can copy-paste.

            EXTRACTED CATALOG DATA:
            {catalog_data['structured_markdown_catalog']}
            """

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=[system_prompt, f"Question: {user_query}"],
            )
            answer = response.text
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
