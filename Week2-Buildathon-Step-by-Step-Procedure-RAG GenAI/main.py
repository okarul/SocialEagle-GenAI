# ============================================================
# main.py
# PRODUCTION-QUALITY STREAMLIT RAG CHATBOT
#
# Final improved version:
# - No hardcoded URL
# - Crawls only after user clicks button
# - Fixed max pages = 5
# - Fixed crawl depth = 3
# - No PDF
# - Professional UI
# - Progress updates
# - Shows crawled pages
# - Stronger error handling
# ============================================================

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from ingest import COLLECTION_NAME, run_ingestion

from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_classic.chains.retrieval import create_retrieval_chain

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


# ============================================================
# ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "social_eagle.env"
load_dotenv(dotenv_path=ENV_PATH)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Smart Website Knowledge Assistant",
    page_icon="🌐",
    layout="centered",
)


# ============================================================
# UI STYLE
# ============================================================

st.markdown(
    """
    <style>
        .main-title {
            text-align: center;
            font-size: 34px;
            font-weight: 900;
            margin-bottom: 8px;
            background: linear-gradient(90deg, #00C853, #00B8D4, #7C4DFF);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 0.3px;
            white-space: nowrap;
        }

        .sub-title {
            text-align: center;
            color: #D1D5DB;
            font-size: 18px;
            margin-bottom: 26px;
            line-height: 1.5;
        }

        .info-box {
            background: linear-gradient(135deg, #EAF7EF, #E8F4FF);
            padding: 18px;
            border-radius: 14px;
            border-left: 7px solid #00A86B;
            font-size: 16px;
            color: #1F2937;
            margin-bottom: 22px;
            box-shadow: 0px 4px 16px rgba(0, 0, 0, 0.08);
        }

        .small-note {
            color: #9CA3AF;
            font-size: 14px;
            text-align: center;
            margin-bottom: 24px;
        }

        .section-heading {
            font-size: 26px;
            font-weight: 800;
            color: #F9FAFB;
            margin-top: 20px;
            margin-bottom: 14px;
        }

        .success-card {
            background: linear-gradient(135deg, #123C24, #174B31);
            color: #86EFAC;
            padding: 20px;
            border-radius: 14px;
            border-left: 7px solid #22C55E;
            font-size: 17px;
            margin-top: 20px;
            margin-bottom: 25px;
            box-shadow: 0px 6px 20px rgba(34, 197, 94, 0.18);
        }

        .success-card a {
            color: #86EFAC !important;
            font-weight: 600;
        }

        .stButton > button {
            background: linear-gradient(90deg, #FF4B4B, #FF7A45);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.7rem 1.4rem;
            font-size: 16px;
            font-weight: 700;
            transition: 0.2s ease-in-out;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0px 6px 16px rgba(255, 75, 75, 0.35);
            color: white;
        }

        input {
            font-size: 16px !important;
        }

        @media screen and (max-width: 768px) {
            .main-title {
                font-size: 26px;
                white-space: normal;
            }

            .sub-title {
                font-size: 15px;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="main-title">Smart Website Knowledge Assistant:</div>
    <div class="sub-title">
        Crawl any website, build a RAG knowledge base, and ask intelligent questions instantly.
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# SESSION STATE
# ============================================================

def initialize_session_state():
    defaults = {
        "website_ingested": False,
        "ingestion_result": None,
        "active_chroma_db_folder": None,
        "active_url": "",
        "chat_history": [],
        "display_messages": [],
        "progress_logs": [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


initialize_session_state()


# ============================================================
# URL INPUT
# ============================================================

st.markdown(
    """
    <div class="section-heading">Enter Website URL</div>
    """,
    unsafe_allow_html=True,
)

website_url = st.text_input(
    label="Website URL",
    value="",
    placeholder="Example: https://www.greenplan.gov.sg/",
    label_visibility="collapsed",
)

crawl_clicked = st.button(
    "Crawl Website and Build RAG DB",
    type="primary",
)


def add_progress_log(message: str):
    st.session_state.progress_logs.append(message)


if crawl_clicked:
    if not website_url.strip():
        st.error("Please enter a website URL before clicking the crawl button.")
        st.stop()

    if "." not in website_url.strip():
        st.error("Please enter a valid website URL, for example: https://www.example.com")
        st.stop()

    st.cache_resource.clear()

    st.session_state.website_ingested = False
    st.session_state.ingestion_result = None
    st.session_state.active_chroma_db_folder = None
    st.session_state.active_url = website_url.strip()
    st.session_state.chat_history = []
    st.session_state.display_messages = []
    st.session_state.progress_logs = []

    progress_box = st.empty()

    def streamlit_progress(message: str):
        add_progress_log(message)
        progress_box.info("\n\n".join(st.session_state.progress_logs[-8:]))

    with st.spinner("Crawling website and building RAG knowledge base..."):
        try:
            result = run_ingestion(
                start_url=website_url.strip(),
                progress_callback=streamlit_progress,
            )

            st.session_state.website_ingested = True
            st.session_state.ingestion_result = result
            st.session_state.active_chroma_db_folder = result["chroma_db_folder"]
            st.session_state.active_url = result["start_url"]

            st.success("Website crawled and RAG database created successfully.")
            st.rerun()

        except Exception as error:
            st.error(f"Error during crawling/ingestion:\n\n{error}")
            st.stop()


# ============================================================
# INGESTION SUMMARY
# ============================================================

if st.session_state.ingestion_result:
    result = st.session_state.ingestion_result

  
# ============================================================
# RAG CHAIN
# ============================================================

@st.cache_resource(show_spinner=False)
def build_rag_chain(chroma_db_folder: str):
    """
    Builds LangChain RAG chain from active Chroma DB.
    """
    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY was not found inside social_eagle.env.")

    if not chroma_db_folder or not os.path.exists(chroma_db_folder):
        raise FileNotFoundError(
            "Chroma database folder was not found. Please crawl a website first."
        )

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vector_store = Chroma(
        persist_directory=chroma_db_folder,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
    )

    retriever = vector_store.as_retriever(
        search_kwargs={"k": 5}
    )

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=0,
    )

    contextualize_q_system_prompt = """
Given a chat history and the latest user question, which might refer to earlier conversation,
rewrite the latest question as a standalone question.

Do not answer the question.
Only rewrite it if needed.
If the question is already standalone, return it as it is.
"""

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    history_aware_retriever = create_history_aware_retriever(
        llm,
        retriever,
        contextualize_q_prompt,
    )

    system_prompt = """
You are a helpful RAG assistant for the crawled website.

Use only the retrieved context below to answer the user's question.

Rules:
1. Answer clearly and professionally.
2. Use only the retrieved context.
3. If the answer is not available in the context, say:
   "I don't know based on the provided context."
4. Do not make up information.
5. If the user asks for a summary, provide a structured summary.
6. If the question is a follow-up, use chat history to understand what it refers to.
7. Keep the answer beginner-friendly.
8. Mention that the answer is based only on the crawled pages.

Retrieved Context:
{context}
"""

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    question_answer_chain = create_stuff_documents_chain(
        llm,
        qa_prompt,
    )

    conversational_rag_chain = create_retrieval_chain(
        history_aware_retriever,
        question_answer_chain,
    )

    return conversational_rag_chain


# ============================================================
# CHATBOT AREA
# ============================================================

active_chroma_folder = st.session_state.active_chroma_db_folder

if not active_chroma_folder:
    st.info("Enter a website URL and click **Crawl Website and Build RAG DB** to start.")
    st.stop()


try:
    conversational_rag_chain = build_rag_chain(active_chroma_folder)
except Exception as error:
    st.error(f"Error loading RAG pipeline: {error}")
    st.stop()


if len(st.session_state.display_messages) == 0:
    with st.chat_message("assistant"):
        st.markdown(
            """
Hello! 👋  

I am ready to answer questions about the crawled website.

Try asking:

**Summarize the website**  
**What are the key topics?**  
**What information is available on this website?**
            """
        )


for message in st.session_state.display_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


user_query = st.chat_input("Ask a question about the crawled website...")


if user_query:
    st.session_state.display_messages.append(
        {
            "role": "user",
            "content": user_query,
        }
    )

    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base and generating answer..."):
            try:
                response = conversational_rag_chain.invoke(
                    {
                        "input": user_query,
                        "chat_history": st.session_state.chat_history,
                    }
                )

                answer = response["answer"]
                st.markdown(answer)

            except Exception as error:
                error_message = str(error)

                if "RESOURCE_EXHAUSTED" in error_message or "429" in error_message:
                    answer = (
                        "Gemini free-tier quota has been exceeded. "
                        "Please wait until the quota resets or use another Google API key/project."
                    )
                    st.error(answer)
                else:
                    answer = f"Sorry, an error occurred: {error}"
                    st.error(answer)

    st.session_state.display_messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    st.session_state.chat_history.extend(
        [
            HumanMessage(content=user_query),
            AIMessage(content=answer),
        ]
    )