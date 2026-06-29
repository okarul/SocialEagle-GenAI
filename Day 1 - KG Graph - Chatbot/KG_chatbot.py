# ============================================================
# STREAMLIT KNOWLEDGE GRAPH RAG APP USING NEO4J DATABASE
#
# Pipeline:
# URL
#   -> Webpage Text Extraction
#   -> Text Chunking
#   -> LLM Entity & Relationship Extraction
#   -> Neo4j Knowledge Base Graph
#   -> Natural Language Question Answering
#
# This version:
# - Lets user enter any URL
# - Lets user set chunk size from 100 onwards
# - Lets user set chunk overlap from 20 onwards
# - Stores Website node in Neo4j
# - Stores Chunk nodes in Neo4j
# - Stores extracted Entity nodes and Relationships in Neo4j
# - Connects Website -> Chunk -> Entity
# - Lets user ask questions from the Neo4j Knowledge Graph
# - Uses light yellow input boxes with black text
# - Does NOT use WebBaseLoader
# - Does NOT require BeautifulSoup / bs4
# ============================================================


# ============================================================
# STEP 1: IMPORT REQUIRED LIBRARIES
# ============================================================

import os
import re
import warnings
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

import streamlit as st
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI

from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_core.prompts import PromptTemplate


# ============================================================
# STEP 2: WARNING CONTROL
# ============================================================

warnings.filterwarnings("ignore", category=DeprecationWarning)


# ============================================================
# STEP 3: STREAMLIT PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Neo4j Knowledge Graph RAG Assistant",
    page_icon="🧠",
    layout="wide"
)


# ============================================================
# STEP 4: CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 34px;
        font-weight: 800;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 17px;
        text-align: center;
        color: #555555;
        margin-bottom: 25px;
    }

    .pipeline-box {
        padding: 16px;
        border-radius: 12px;
        background-color: #f7f9fc;
        border: 1px solid #d9e2ec;
        margin-bottom: 18px;
        font-size: 15px;
        color: #000000;
    }

    .success-box {
        padding: 15px;
        border-radius: 10px;
        background-color: #e8f5e9;
        border-left: 6px solid #2e7d32;
        margin-top: 15px;
        color: #000000;
    }

    .warning-box {
        padding: 15px;
        border-radius: 10px;
        background-color: #fff8e1;
        border-left: 6px solid #f9a825;
        margin-top: 15px;
        color: #000000;
    }

    .answer-box {
        padding: 18px;
        border-radius: 12px;
        background-color: #eef7ff;
        border-left: 6px solid #1565c0;
        margin-top: 15px;
        font-size: 16px;
        line-height: 1.6;
        color: #000000;
    }

    /* URL input box */
    .stTextInput input {
        background-color: #fff9c4 !important;
        color: #000000 !important;
        border: 1px solid #d4c25a !important;
        border-radius: 10px !important;
        font-size: 16px !important;
    }

    /* URL input placeholder */
    .stTextInput input::placeholder {
        color: #444444 !important;
        opacity: 1 !important;
    }

    /* Question text area */
    .stTextArea textarea {
        background-color: #fff9c4 !important;
        color: #000000 !important;
        border: 1px solid #d4c25a !important;
        border-radius: 10px !important;
        font-size: 16px !important;
    }

    /* Question text area placeholder */
    .stTextArea textarea::placeholder {
        color: #444444 !important;
        opacity: 1 !important;
    }

    /* Labels above inputs */
    label {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* Metric cards text */
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
    }

    [data-testid="stMetricLabel"] {
        color: #d9e2ec !important;
    }

    /* Expander text */
    .streamlit-expanderHeader {
        font-weight: 700 !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# STEP 5: SIMPLE HTML TO TEXT CONVERTER
# ============================================================

class SimpleHTMLTextExtractor(HTMLParser):
    """
    Converts HTML webpage content into readable plain text.
    This avoids the need for WebBaseLoader and BeautifulSoup.
    """

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip_content = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()

        if tag in ["script", "style", "noscript", "svg"]:
            self.skip_content = True

        if tag in [
            "p", "br", "div", "section", "article",
            "h1", "h2", "h3", "h4", "li", "tr"
        ]:
            self.text_parts.append("\n")

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag in ["script", "style", "noscript", "svg"]:
            self.skip_content = False

        if tag in [
            "p", "div", "section", "article",
            "h1", "h2", "h3", "h4", "li", "tr"
        ]:
            self.text_parts.append("\n")

    def handle_data(self, data):
        if not self.skip_content:
            cleaned = data.strip()
            if cleaned:
                self.text_parts.append(cleaned + " ")

    def get_text(self):
        text = " ".join(self.text_parts)
        text = text.replace("\xa0", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()


def load_webpage_as_text(url: str) -> str:
    """
    Loads webpage HTML using Python standard library and converts it to text.
    No bs4 required.
    """

    headers = {
        "User-Agent": "SocialEagle-Neo4j-KG-RAG-Streamlit-App/1.0"
    }

    request = Request(url, headers=headers)

    try:
        with urlopen(request, timeout=30) as response:
            html_bytes = response.read()

        html_text = html_bytes.decode("utf-8", errors="ignore")

        parser = SimpleHTMLTextExtractor()
        parser.feed(html_text)

        text = parser.get_text()

        if not text:
            raise ValueError("Webpage loaded, but no readable text was extracted.")

        return text

    except HTTPError as e:
        raise RuntimeError(f"HTTP error while loading webpage: {e.code} - {e.reason}")

    except URLError as e:
        raise RuntimeError(f"URL error while loading webpage: {e.reason}")

    except Exception as e:
        raise RuntimeError(f"Unexpected error while loading webpage: {e}")


# ============================================================
# STEP 6: LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv("social_eagle.env", override=True)

os.environ.setdefault(
    "USER_AGENT",
    "SocialEagle-Neo4j-KG-RAG-Streamlit-App/1.0"
)


# ============================================================
# STEP 7: VALIDATE ENVIRONMENT VARIABLES
# ============================================================

def validate_environment():
    required_env_vars = [
        "OPENAI_API_KEY",
        "NEO4J_URI",
        "NEO4J_USERNAME",
        "NEO4J_PASSWORD"
    ]

    missing_vars = []

    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    return missing_vars


# ============================================================
# STEP 8: CONNECT TO NEO4J
# ============================================================

def connect_to_neo4j():
    """
    Creates Neo4jGraph connection.
    Neo4j is the graph database used for the knowledge base.
    """

    graph = Neo4jGraph(
        url=os.environ["NEO4J_URI"],
        username=os.environ["NEO4J_USERNAME"],
        password=os.environ["NEO4J_PASSWORD"],
        enhanced_schema=True
    )

    return graph


# ============================================================
# STEP 9: NEO4J KNOWLEDGE BASE GRAPH FUNCTIONS
# ============================================================

def clear_neo4j_database(graph):
    """
    Clears all nodes and relationships from Neo4j.
    Use only for demo/testing.
    """

    graph.query("MATCH (n) DETACH DELETE n")


def store_website_and_chunks(graph, url, webpage_text, chunks):
    """
    Creates visible Website and Chunk nodes in Neo4j.

    Graph structure:
    (:Website)-[:HAS_CHUNK]->(:Chunk)
    """

    graph.query(
        """
        MERGE (w:Website {url: $url})
        SET
            w.title = 'User Provided Website',
            w.source_type = 'webpage',
            w.total_characters = $total_characters,
            w.total_chunks = $total_chunks,
            w.created_at = datetime()
        RETURN w
        """,
        {
            "url": url,
            "total_characters": len(webpage_text),
            "total_chunks": len(chunks)
        }
    )

    for i, chunk in enumerate(chunks):
        chunk_id = f"{url}#chunk-{i + 1}"

        graph.query(
            """
            MATCH (w:Website {url: $url})
            MERGE (c:Chunk {chunk_id: $chunk_id})
            SET
                c.chunk_number = $chunk_number,
                c.text = $text,
                c.source_url = $url,
                c.created_at = datetime()
            MERGE (w)-[:HAS_CHUNK]->(c)
            RETURN c
            """,
            {
                "url": url,
                "chunk_id": chunk_id,
                "chunk_number": i + 1,
                "text": chunk.page_content[:2500]
            }
        )


def link_website_to_entities(graph, url):
    """
    Links Website node to all extracted entity nodes.

    LLMGraphTransformer with baseEntityLabel=True usually creates
    entity nodes with the __Entity__ label.

    Graph structure:
    (:Website)-[:HAS_EXTRACTED_ENTITY]->(:__Entity__)
    """

    result = graph.query(
        """
        MATCH (w:Website {url: $url})
        MATCH (e:__Entity__)
        MERGE (w)-[:HAS_EXTRACTED_ENTITY]->(e)
        RETURN count(e) AS linked_entities
        """,
        {
            "url": url
        }
    )

    if result:
        return result[0].get("linked_entities", 0)

    return 0


def link_chunks_to_entities_by_text_match(graph, url):
    """
    Connects Chunk nodes to Entity nodes when the chunk text contains
    the entity id.

    Graph structure:
    (:Chunk)-[:MENTIONS]->(:__Entity__)
    """

    result = graph.query(
        """
        MATCH (c:Chunk {source_url: $url})
        MATCH (e:__Entity__)
        WHERE e.id IS NOT NULL
          AND toLower(c.text) CONTAINS toLower(e.id)
        MERGE (c)-[:MENTIONS]->(e)
        RETURN count(*) AS mention_links
        """,
        {
            "url": url
        }
    )

    if result:
        return result[0].get("mention_links", 0)

    return 0


def get_neo4j_graph_stats(graph):
    """
    Returns total node and relationship counts from Neo4j.
    """

    result = graph.query(
        """
        MATCH (n)
        WITH count(n) AS total_nodes
        MATCH ()-[r]->()
        RETURN total_nodes, count(r) AS total_relationships
        """
    )

    if result:
        return (
            result[0].get("total_nodes", 0),
            result[0].get("total_relationships", 0)
        )

    return 0, 0


def get_node_label_counts(graph):
    """
    Returns count of nodes by labels.
    Useful for demonstrating the Neo4j knowledge base graph.
    """

    result = graph.query(
        """
        MATCH (n)
        UNWIND labels(n) AS label
        RETURN label, count(*) AS count
        ORDER BY count DESC
        """
    )

    return result


def get_relationship_type_counts(graph):
    """
    Returns count of relationships by type.
    """

    result = graph.query(
        """
        MATCH ()-[r]->()
        RETURN type(r) AS relationship_type, count(*) AS count
        ORDER BY count DESC
        """
    )

    return result


# ============================================================
# STEP 10: CYPHER GENERATION PROMPT
# ============================================================

CYPHER_GENERATION_TEMPLATE = """
Task:
Generate a valid Cypher query to answer the user's question
using the Neo4j knowledge graph.

Schema:
{schema}

Instructions:
1. Use ONLY the node labels, relationship types, and properties shown in the schema.
2. Do NOT invent node labels or relationship names.
3. Use MATCH clauses to find graph patterns.
4. NEVER return a pattern expression directly in the RETURN clause.
5. Return useful node properties such as id, name, title, description, text, url, source_url, or source.
6. If the question asks about relationships, traverse the graph using existing relationship types.
7. Generate read-only Cypher queries only.
8. Do NOT use DELETE, CREATE, MERGE, SET, REMOVE, DROP, or any write operation.
9. Use LIMIT where appropriate.

Useful query examples:

Example 1:
MATCH (w:Website)
RETURN w.url AS Website, w.total_chunks AS Chunks
LIMIT 10

Example 2:
MATCH (w:Website)-[:HAS_CHUNK]->(c:Chunk)
RETURN w.url AS Website, c.chunk_number AS ChunkNumber, c.text AS Text
LIMIT 10

Example 3:
MATCH (w:Website)-[:HAS_EXTRACTED_ENTITY]->(e:__Entity__)
RETURN w.url AS Website, e.id AS Entity, labels(e) AS Labels
LIMIT 20

Example 4:
MATCH (a)-[r]->(b)
RETURN a.id AS Source, type(r) AS Relationship, b.id AS Target
LIMIT 20

Question:
{question}
"""


def create_qa_chain(graph, llm):
    """
    Creates a GraphCypherQAChain for asking questions from Neo4j.
    """

    cypher_prompt = PromptTemplate(
        input_variables=["schema", "question"],
        template=CYPHER_GENERATION_TEMPLATE
    )

    chain = GraphCypherQAChain.from_llm(
        graph=graph,
        llm=llm,
        cypher_prompt=cypher_prompt,
        verbose=True,
        allow_dangerous_requests=True
    )

    return chain


# ============================================================
# STEP 11: SESSION STATE
# ============================================================

default_session_values = {
    "graph_ready": False,
    "chain": None,
    "graph_schema": "",
    "webpage_text": "",
    "source_url": "",
    "extracted_nodes_count": 0,
    "extracted_relationships_count": 0,
    "neo4j_total_nodes": 0,
    "neo4j_total_relationships": 0,
    "linked_entities": 0,
    "mention_links": 0,
    "label_counts": [],
    "relationship_counts": [],
    "last_answer": ""
}

for key, value in default_session_values.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# STEP 12: APP HEADER
# ============================================================

st.markdown(
    """
    <div style="
        color: #FFFFFF;
        font-size: 44px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 10px;
    ">
        🧠 Neo4j Knowledge Graph RAG Assistant
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style="
        background-color: #fffde7;
        color: #000000;
        padding: 14px 18px;
        border-radius: 10px;
        text-align: center;
        font-size: 17px;
        font-weight: 500;
        margin-bottom: 20px;
        border: 1px solid #f5e6a1;
    ">
        Enter a website URL, build a Neo4j Knowledge Base Graph, and ask questions from the graph database.
    </div>
    """,
    unsafe_allow_html=True
)

# ============================================================
# STEP 13: SIDEBAR SETTINGS
# ============================================================

with st.sidebar:
    st.header("⚙️ App Settings")

    st.subheader("Chunk Settings")

    chunk_size = st.slider(
        "Chunk Size",
        min_value=100,
        max_value=2500,
        value=1000,
        step=100,
        help="Minimum chunk size is 100 characters. Smaller chunks may create more graph nodes but can increase processing time."
    )

    chunk_overlap = st.slider(
        "Chunk Overlap",
        min_value=20,
        max_value=500,
        value=150,
        step=10,
        help="Minimum chunk overlap is 20 characters. Overlap helps preserve context between chunks."
    )

    st.subheader("Neo4j Settings")

    clear_existing_graph = st.checkbox(
        "Clear existing Neo4j database before building",
        value=False
    )

    show_extracted_text = st.checkbox(
        "Show extracted webpage text",
        value=True
    )

    show_neo4j_schema = st.checkbox(
        "Show Neo4j schema",
        value=True
    )

    show_demo_queries = st.checkbox(
        "Show Neo4j Browser demo queries",
        value=True
    )

    st.markdown("---")

    st.info(
        "Your `social_eagle.env` file must contain "
        "`OPENAI_API_KEY`, `NEO4J_URI`, `NEO4J_USERNAME`, and `NEO4J_PASSWORD`."
    )


# ============================================================
# STEP 14: CHECK ENVIRONMENT VARIABLES
# ============================================================

missing_vars = validate_environment()

if missing_vars:
    st.error(
        f"Missing environment variables in social_eagle.env: {missing_vars}"
    )
    st.stop()


# ============================================================
# STEP 15: URL INPUT
# ============================================================

st.subheader("1️⃣ Enter Website URL")

default_url = "https://northernsolar.com.my/malaysia-renewable-energy-roadmap-what-businesses-must-know/"

url = st.text_input(
    "Website URL",
    value=default_url,
    placeholder="Enter a website URL..."
)

build_button = st.button(
    "🚀 Build Neo4j Knowledge Graph",
    use_container_width=True
)


# ============================================================
# STEP 16: BUILD KNOWLEDGE GRAPH
# ============================================================

if build_button:

    if not url.strip():
        st.error("Please enter a valid URL.")
        st.stop()

    if chunk_overlap >= chunk_size:
        st.error("Chunk Overlap must be smaller than Chunk Size.")
        st.stop()

    try:
        progress_bar = st.progress(0)
        status_box = st.empty()

        # ----------------------------------------------------
        # 1. Load webpage
        # ----------------------------------------------------
        status_box.info("Step 1/8: Loading webpage content from URL...")
        webpage_text = load_webpage_as_text(url)

        st.session_state.webpage_text = webpage_text
        st.session_state.source_url = url

        progress_bar.progress(10)

        # ----------------------------------------------------
        # 2. Convert to LangChain Document
        # ----------------------------------------------------
        status_box.info("Step 2/8: Creating LangChain document...")
        documents = [
            Document(
                page_content=webpage_text,
                metadata={
                    "source": url,
                    "title": "User Provided Website"
                }
            )
        ]

        progress_bar.progress(20)

        # ----------------------------------------------------
        # 3. Split text into chunks
        # ----------------------------------------------------
        status_box.info("Step 3/8: Splitting text into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        chunks = text_splitter.split_documents(documents)

        if not chunks:
            st.error("No chunks were created from the webpage content.")
            st.stop()

        progress_bar.progress(35)

        # ----------------------------------------------------
        # 4. Connect to Neo4j
        # ----------------------------------------------------
        status_box.info("Step 4/8: Connecting to Neo4j graph database...")
        graph = connect_to_neo4j()

        if clear_existing_graph:
            status_box.warning("Clearing existing Neo4j database...")
            clear_neo4j_database(graph)

        progress_bar.progress(45)

        # ----------------------------------------------------
        # 5. Initialize LLM
        # ----------------------------------------------------
        status_box.info("Step 5/8: Initializing OpenAI LLM...")
        llm = ChatOpenAI(
            temperature=0,
            model_name="gpt-4o-mini"
        )

        progress_bar.progress(55)

        # ----------------------------------------------------
        # 6. Extract graph documents
        # ----------------------------------------------------
        status_box.info("Step 6/8: Extracting entities and relationships with LLM...")
        llm_transformer = LLMGraphTransformer(llm=llm)

        graph_documents = llm_transformer.convert_to_graph_documents(chunks)

        if not graph_documents:
            st.error("No graph documents were created by the LLM.")
            st.stop()

        total_extracted_nodes = 0
        total_extracted_relationships = 0

        for graph_doc in graph_documents:
            total_extracted_nodes += len(graph_doc.nodes)
            total_extracted_relationships += len(graph_doc.relationships)

        st.session_state.extracted_nodes_count = total_extracted_nodes
        st.session_state.extracted_relationships_count = total_extracted_relationships

        progress_bar.progress(70)

        # ----------------------------------------------------
        # 7. Store everything into Neo4j
        # ----------------------------------------------------
        status_box.info("Step 7/8: Storing Website, Chunks, Entities, and Relationships into Neo4j...")

        # A. Store extracted entity-relationship graph
        graph.add_graph_documents(
            graph_documents,
            baseEntityLabel=True,
            include_source=True
        )

        # B. Store Website and Chunk nodes for clear demo
        store_website_and_chunks(
            graph=graph,
            url=url,
            webpage_text=webpage_text,
            chunks=chunks
        )

        # C. Link Website to extracted Entities
        linked_entities = link_website_to_entities(
            graph=graph,
            url=url
        )

        # D. Link Chunks to Entities where text contains entity id
        mention_links = link_chunks_to_entities_by_text_match(
            graph=graph,
            url=url
        )

        st.session_state.linked_entities = linked_entities
        st.session_state.mention_links = mention_links

        progress_bar.progress(85)

        # ----------------------------------------------------
        # 8. Refresh schema and create QA chain
        # ----------------------------------------------------
        status_box.info("Step 8/8: Refreshing Neo4j schema and creating Q&A chain...")

        graph.refresh_schema()

        st.session_state.graph_schema = graph.schema

        chain = create_qa_chain(graph, llm)

        st.session_state.chain = chain
        st.session_state.graph_ready = True

        neo4j_nodes, neo4j_relationships = get_neo4j_graph_stats(graph)

        st.session_state.neo4j_total_nodes = neo4j_nodes
        st.session_state.neo4j_total_relationships = neo4j_relationships
        st.session_state.label_counts = get_node_label_counts(graph)
        st.session_state.relationship_counts = get_relationship_type_counts(graph)

        progress_bar.progress(100)
        status_box.success("Neo4j Knowledge Graph built successfully!")

        st.markdown(
            """
            <div class='success-box'>
            ✅ Neo4j Knowledge Base Graph has been created successfully.<br>
            You can now open Neo4j Browser and visually inspect Website, Chunk, Entity, and Relationship nodes.
            </div>
            """,
            unsafe_allow_html=True
        )

    except Exception as e:
        st.session_state.graph_ready = False
        st.error(f"Error while building Neo4j Knowledge Graph: {e}")


# ============================================================
# STEP 17: KNOWLEDGE GRAPH BUILD SUMMARY
# ============================================================

if st.session_state.graph_ready:

    st.subheader("2️⃣ Neo4j Knowledge Graph Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("LLM Extracted Nodes", st.session_state.extracted_nodes_count)

    with col2:
        st.metric("LLM Extracted Relationships", st.session_state.extracted_relationships_count)

    with col3:
        st.metric("Neo4j Total Nodes", st.session_state.neo4j_total_nodes)

    with col4:
        st.metric("Neo4j Total Relationships", st.session_state.neo4j_total_relationships)

    col5, col6 = st.columns(2)

    with col5:
        st.metric("Website → Entity Links", st.session_state.linked_entities)

    with col6:
        st.metric("Chunk → Entity Mention Links", st.session_state.mention_links)

    st.write("Source URL:")
    st.code(st.session_state.source_url)

    with st.expander("View Neo4j Node Label Counts"):
        if st.session_state.label_counts:
            st.table(st.session_state.label_counts)
        else:
            st.write("No label counts available.")

    with st.expander("View Neo4j Relationship Type Counts"):
        if st.session_state.relationship_counts:
            st.table(st.session_state.relationship_counts)
        else:
            st.write("No relationship counts available.")

    if show_extracted_text:
        with st.expander("View Extracted Webpage Text"):
            st.write(st.session_state.webpage_text[:8000])

    if show_neo4j_schema:
        with st.expander("View Neo4j Graph Schema"):
            st.code(st.session_state.graph_schema)

    if show_demo_queries:
        with st.expander("Neo4j Browser Demo Queries"):
            st.markdown("Copy and run these queries in Neo4j Browser:")

            st.code(
                """
MATCH (w:Website)
RETURN w
                """,
                language="cypher"
            )

            st.code(
                """
MATCH p=(w:Website)-[:HAS_CHUNK]->(c:Chunk)
RETURN p
LIMIT 25
                """,
                language="cypher"
            )

            st.code(
                """
MATCH p=(w:Website)-[:HAS_EXTRACTED_ENTITY]->(e:__Entity__)
RETURN p
LIMIT 50
                """,
                language="cypher"
            )

            st.code(
                """
MATCH p=(w:Website)-[:HAS_CHUNK]->(c:Chunk)-[:MENTIONS]->(e:__Entity__)
RETURN p
LIMIT 50
                """,
                language="cypher"
            )

            st.code(
                """
MATCH p=(a)-[r]->(b)
RETURN p
LIMIT 100
                """,
                language="cypher"
            )


# ============================================================
# STEP 18: QUESTION ANSWERING SECTION
# ============================================================

st.markdown(
    """
    <style>
    /* Question text area - user typed query */
    .stTextArea textarea {
        font-size: 17px !important;
        line-height: 1.5 !important;
        background-color: #fffde7 !important;   /* very light yellow */
        color: #000000 !important;              /* black text */
        border: 1px solid #f5e6a1 !important;
        border-radius: 10px !important;
    }

    /* Placeholder text inside question box */
    .stTextArea textarea::placeholder {
        font-size: 17px !important;
        color: #444444 !important;
        opacity: 1 !important;
    }

    /* Label: Enter your question */
    .stTextArea label {
        font-size: 17px !important;
        font-weight: 600 !important;
        color: #003366 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.subheader("3️⃣ Ask a Question from the Neo4j Knowledge Graph")

question = st.text_area(
    "Enter your question",
    placeholder="Example: What renewable energy targets are mentioned in this webpage?",
    height=180
)

ask_button = st.button(
    "🔍 Ask Question",
    use_container_width=True
)

if ask_button:

    if not st.session_state.graph_ready or st.session_state.chain is None:
        st.warning("Please build the Neo4j Knowledge Graph first.")
        st.stop()

    if not question.strip():
        st.warning("Please enter a question.")
        st.stop()

    try:
        with st.spinner("Querying Neo4j Knowledge Graph and generating answer..."):
            response = st.session_state.chain.invoke(
                {
                    "query": question
                }
            )

        result = response.get("result", "No answer returned.")

        st.session_state.last_answer = result

        st.subheader("✅ Answer")

        st.markdown(
            f"""
            <div class='answer-box'>
            {result}
            </div>
            """,
            unsafe_allow_html=True
        )

    except Exception as e:
        st.error(f"Error while answering the question: {e}")


# ============================================================
# STEP 19: SAMPLE QUESTIONS
# ============================================================

with st.expander("💡 Sample Questions You Can Ask"):
    st.markdown(
        """
        - What is this webpage about?
        - What are the main entities in the knowledge graph?
        - What renewable energy targets are mentioned?
        - What should businesses know from this article?
        - What policies, organizations, technologies, or initiatives are mentioned?
        - Which entities are connected to the website?
        - Which chunks mention renewable energy?
        - What are the key opportunities for businesses?
        """
    )


# ============================================================
# STEP 20: FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "Neo4j is used as the graph database. Streamlit is used as the UI. "
    "LangChain connects the webpage, LLM graph extraction, Neo4j storage, and Cypher-based question answering."
)


# ============================================================
# END OF STREAMLIT APP
# ============================================================