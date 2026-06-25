# app.py

# =========================================================
# PDF RAG App using Streamlit + LangChain + FAISS + OpenAI
# Professional UI Version with Retrieve Button
# =========================================================

import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS

from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI

from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# =========================================================
# 1. Load Environment Variables
# =========================================================

load_dotenv("social_eagle.env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# =========================================================
# 2. Streamlit Page Configuration
# =========================================================

st.set_page_config(
    page_title="PDF RAG Assistant",
    page_icon="",
    layout="centered"
)


# =========================================================
# 3. Professional UI Styling
# =========================================================

st.markdown(
    """
    <style>
        .stApp {
            background: linear-gradient(135deg, #0F172A 0%, #111827 45%, #1E293B 100%);
        }

        .block-container {
            padding-top: 2rem;
            max-width: 900px;
        }

        .app-header {
            background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%);
            padding: 24px 28px;
            border-radius: 18px;
            margin-bottom: 22px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.25);
        }

        .app-title {
            color: #FFFFFF;
            font-size: 30px;
            font-weight: 800;
            margin: 0;
            line-height: 1.2;
            letter-spacing: -0.5px;
        }

        .app-subtitle {
            color: #DBEAFE;
            font-size: 15.5px;
            margin-top: 8px;
            line-height: 1.5;
        }

        .welcome-box {
            background-color: #FFFFFF;
            border-left: 6px solid #FACC15;
            padding: 16px 20px;
            border-radius: 14px;
            margin-bottom: 20px;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18);
        }

        .welcome-title {
            color: #0F172A;
            font-size: 19px;
            font-weight: 800;
            margin-bottom: 6px;
        }

        .welcome-text {
            color: #475569;
            font-size: 15px;
            line-height: 1.55;
        }

        .section-label {
            color: #FACC15;
            font-size: 18px;
            font-weight: 800;
            margin-top: 16px;
            margin-bottom: 6px;
        }

        .small-note {
            color: #FDE68A;
            font-size: 14px;
            margin-bottom: 8px;
        }

        .stFileUploader label {
            color: #FFFFFF !important;
            font-weight: 700 !important;
            font-size: 16px !important;
        }

        .stTextInput label {
            color: #FFFFFF !important;
            font-weight: 700 !important;
            font-size: 16px !important;
        }

        .stTextInput input {
            border-radius: 10px;
            border: 1px solid #CBD5E1;
            padding: 10px;
        }

        div.stButton > button {
            background-color: #FACC15;
            color: #0F172A;
            border-radius: 10px;
            padding: 0.65rem 1.2rem;
            border: none;
            font-weight: 800;
            font-size: 15px;
            margin-top: 8px;
        }

        div.stButton > button:hover {
            background-color: #EAB308;
            color: #0F172A;
        }

        .small-answer-title {
            color: #FACC15;
            font-size: 18px;
            font-weight: 800;
            margin-top: 24px;
            margin-bottom: 8px;
        }

        .answer-text {
            color: #FFFFFF;
            font-size: 16px;
            line-height: 1.7;
        }

        .source-title {
            color: #FACC15;
            font-size: 16px;
            font-weight: 700;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 4. Header Section
# =========================================================

st.markdown(
    """
    <div class="app-header">
        <h1 class="app-title">🤖 PDF RAG Assistant</h1>
        <div class="app-subtitle">
            Upload a PDF and ask intelligent questions grounded in your document.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="welcome-box">
        <div class="welcome-title">Welcome to your AI PDF Document Assistant</div>
        <div class="welcome-text">
            This app reads your PDF, splits it into chunks, creates embeddings,
            stores them in a FAISS vector database, and uses OpenAI to answer
            your questions based only on the uploaded document.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 5. Check API Key
# =========================================================

if not OPENAI_API_KEY:
    st.error(
        "OPENAI_API_KEY is missing. Please check your social_eagle.env file."
    )
    st.stop()


# =========================================================
# 6. Build FAISS Vector Database
# =========================================================

def build_faiss_vector_db(uploaded_pdf):
    """
    This function:
    1. Saves the uploaded PDF temporarily.
    2. Loads the PDF.
    3. Splits the text into chunks.
    4. Creates OpenAI embeddings.
    5. Stores embeddings in FAISS.
    """

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(uploaded_pdf.read())
        temp_pdf_path = temp_file.name

    try:
        loader = PyPDFLoader(temp_pdf_path)
        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

        chunks = text_splitter.split_documents(documents)

        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small"
        )

        vector_db = FAISS.from_documents(
            documents=chunks,
            embedding=embeddings
        )

        return vector_db, documents, chunks

    finally:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)


# =========================================================
# 7. Format Retrieved Documents
# =========================================================

def format_documents(docs):
    """
    Converts retrieved documents into a clean text block
    that will be passed to the OpenAI model.
    """

    formatted_text = ""

    for i, doc in enumerate(docs, start=1):
        page_number = doc.metadata.get("page", "Unknown")

        if isinstance(page_number, int):
            page_number = page_number + 1

        formatted_text += f"\n\nSource {i}, Page {page_number}:\n"
        formatted_text += doc.page_content

    return formatted_text


# =========================================================
# 8. Answer Question using FAISS Retriever + OpenAI
# =========================================================

def answer_question(vector_db, question):
    """
    This function:
    1. Retrieves relevant chunks from FAISS.
    2. Sends the retrieved context and user question to OpenAI.
    3. Returns the generated answer and source documents.
    """

    retriever = vector_db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    )

    source_documents = retriever.invoke(question)

    context = format_documents(source_documents)

    prompt = ChatPromptTemplate.from_template(
        """
You are a helpful AI assistant.

Answer the user's question using only the context below.

Do not use outside knowledge.

If the answer is not available in the context, say:
"I could not find the answer in the uploaded PDF."

Context:
{context}

Question:
{question}

Answer:
"""
    )

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0
    )

    chain = prompt | llm | StrOutputParser()

    answer = chain.invoke(
        {
            "context": context,
            "question": question
        }
    )

    return answer, source_documents


# =========================================================
# 9. PDF Upload Section
# =========================================================

uploaded_pdf = st.file_uploader(
    "Choose a PDF file",
    type=["pdf"]
)


# =========================================================
# 10. Main App Logic
# =========================================================

if uploaded_pdf is not None:

    if (
        "uploaded_file_name" not in st.session_state
        or st.session_state.uploaded_file_name != uploaded_pdf.name
    ):

        with st.spinner("Reading PDF, creating embeddings, and building FAISS database..."):

            vector_db, documents, chunks = build_faiss_vector_db(uploaded_pdf)

            st.session_state.vector_db = vector_db
            st.session_state.uploaded_file_name = uploaded_pdf.name
            st.session_state.page_count = len(documents)
            st.session_state.chunk_count = len(chunks)

        st.success("PDF processed successfully. You can now ask questions.")

    st.info(
        f"File name: {st.session_state.uploaded_file_name}\n\n"
        f"Pages loaded: {st.session_state.page_count}\n\n"
        f"Chunks created: {st.session_state.chunk_count}"
    )


    # =========================================================
    # 11. Question Box and Retrieve Button
    # =========================================================

    st.markdown(
        """
        <div class="section-label">
            Ask a question about your PDF
        </div>
        """,
        unsafe_allow_html=True
    )

    user_question = st.text_input(
        "",
        key="pdf_question_input"
    )

    retrieve_button = st.button(
        "Click here to retrieve the information"
    )

    if retrieve_button:

        if not user_question:
            st.warning("Please enter a question before clicking the retrieve button.")

        else:
            with st.spinner("Searching your PDF and generating a grounded answer..."):

                answer, source_documents = answer_question(
                    st.session_state.vector_db,
                    user_question
                )

            st.markdown(
                """
                <div class="small-answer-title">
                    Retrieved Answer
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown(
                f"""
                <div class="answer-text">
                    {answer}
                </div>
                """,
                unsafe_allow_html=True
            )

else:
    st.warning("Please upload a PDF file to begin.")