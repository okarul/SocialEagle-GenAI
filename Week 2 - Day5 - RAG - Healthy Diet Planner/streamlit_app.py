# ============================================================
# BASIC LANGCHAIN + STREAMLIT GENAI APP
# Use case: Simple Healthy Diet Planner
# Input: User age and body weight in kg
# Output: Professional readable diet plan table
# ============================================================

import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# ============================================================
# STEP 1: LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv("social_eagle.env")


# ============================================================
# STEP 2: STREAMLIT PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Healthy Diet Planner",
    page_icon="🥗",
    layout="wide"
)


# ============================================================
# STEP 3: PROFESSIONAL CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

        /* Main page background */
        .stApp {
            background-color: #F4F7F5;
        }

        /* Main title */
        .main-title {
            text-align: center;
            color: #12372A;
            font-size: 44px;
            font-weight: 800;
            margin-top: 10px;
            margin-bottom: 5px;
            letter-spacing: 0.3px;
        }

        .subtitle {
            text-align: center;
            color: #4A5568;
            font-size: 20px;
            margin-bottom: 35px;
        }

        /* Input section */
        .input-section {
            background-color: #FFFFFF;
            padding: 28px;
            border-radius: 18px;
            border: 1px solid #D8E2DC;
            box-shadow: 0 4px 14px rgba(0,0,0,0.06);
            margin-bottom: 28px;
        }

        /* Result title */
        .result-title {
            text-align: center;
            color: #12372A;
            font-size: 34px;
            font-weight: 800;
            margin-top: 35px;
            margin-bottom: 25px;
        }

        /* Profile summary */
        .profile-box {
            background-color: #EAF4EE;
            color: #12372A;
            padding: 20px 24px;
            border-radius: 16px;
            border: 1px solid #B7D7C2;
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 28px;
        }

        /* Table styling */
        table {
            width: 100%;
            border-collapse: collapse;
            background-color: #FFFFFF;
            font-size: 20px;
            color: #1A202C;
            margin-top: 20px;
            border: 1px solid #CBD5E0;
            box-shadow: 0 6px 18px rgba(0,0,0,0.08);
        }

        thead tr {
            background-color: #1B5E20;
            color: #FFFFFF;
        }

        th {
            background-color: #1B5E20 !important;
            color: #FFFFFF !important;
            padding: 18px 20px;
            text-align: left;
            font-size: 21px;
            font-weight: 800;
            border: 1px solid #1B5E20;
        }

        td {
            padding: 18px 20px;
            border: 1px solid #D6DEE6;
            vertical-align: top;
            color: #1A202C !important;
            font-size: 20px;
            line-height: 1.6;
            font-weight: 500;
        }

        tbody tr:nth-child(odd) {
            background-color: #FFFFFF;
        }

        tbody tr:nth-child(even) {
            background-color: #F2F7F3;
        }

        tbody tr:hover {
            background-color: #E6F4EA;
        }

        /* Icon column */
        td:first-child, th:first-child {
            text-align: center;
            width: 90px;
            font-size: 25px;
        }

        /* Meal time column */
        td:nth-child(2) {
            font-weight: 800;
            color: #12372A !important;
            width: 220px;
        }

        /* Suggested food column */
        td:nth-child(3) {
            color: #1A202C !important;
            width: 420px;
        }

        /* Why it helps column */
        td:nth-child(4) {
            color: #2D3748 !important;
        }

        /* Health note */
        .note-box {
            background-color: #FFF8E1;
            color: #3D2C00;
            padding: 22px 26px;
            border-radius: 16px;
            border-left: 8px solid #F9A825;
            font-size: 19px;
            line-height: 1.6;
            margin-top: 30px;
            font-weight: 500;
        }

        .note-box b {
            color: #3D2C00;
            font-weight: 800;
        }

        /* Footer */
        .footer-box {
            text-align: center;
            color: #4A5568;
            font-size: 16px;
            margin-top: 35px;
            padding-bottom: 20px;
        }

        /* Button */
        div.stButton > button {
            background-color: #1B5E20;
            color: white;
            font-size: 20px;
            font-weight: 700;
            padding: 14px 24px;
            border-radius: 12px;
            border: none;
        }

        div.stButton > button:hover {
            background-color: #145A32;
            color: white;
        }

        /* Number input label */
        label {
            font-size: 18px !important;
            font-weight: 700 !important;
            color: #12372A !important;
        }

        /* Number input text */
        input {
            font-size: 19px !important;
            color: #111827 !important;
            background-color: #FFFFFF !important;
        }

        /* Print settings */
        @media print {
            .stButton {
                display: none !important;
            }

            .main-title {
                font-size: 34px;
            }

            .subtitle {
                font-size: 16px;
            }

            .profile-box {
                font-size: 16px;
            }

            table {
                font-size: 14px;
                box-shadow: none;
            }

            th {
                font-size: 15px;
                padding: 10px;
            }

            td {
                font-size: 14px;
                padding: 10px;
            }

            .note-box {
                font-size: 14px;
                padding: 14px;
            }

            .footer-box {
                font-size: 12px;
            }
        }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# STEP 4: PAGE TITLE
# ============================================================

st.markdown(
    """
    <div class="main-title">🥗 Healthy Diet Planner</div>
    <div class="subtitle">
        A simple one-day healthy diet plan generated using LangChain and OpenAI
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# STEP 5: INITIALIZE THE LLM MODEL
# ============================================================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)


# ============================================================
# STEP 6: CREATE PROMPT TEMPLATE
# ============================================================

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are a safe and beginner-friendly healthy diet planning assistant.

        Important safety rules:
        - Do not recommend crash dieting.
        - Do not recommend starvation.
        - Do not recommend skipping meals.
        - Do not recommend extreme calorie restriction.
        - If the user is below 18 years old, do not suggest weight-loss dieting.
        - If the user is below 18 years old, suggest balanced meals, growth-supporting nutrition, and healthy habits.
        - If the user is below 18 years old, advise speaking with a parent, guardian, doctor, or qualified dietitian before making major food changes.
        - Recommend speaking with a qualified health professional for personal advice.

        Use simple beginner-friendly English.
        Keep the answer practical and easy to follow.

        Output rule:
        Return only a Markdown table.
        Do not write extra paragraphs before or after the table.
        Keep each cell short, clear, and practical.
        """
    ),
    (
        "human",
        """
        My age is {age} years old.
        My body weight is {weight_kg} kg.

        Please create a simple one-day healthy diet plan suitable for my age.

        Return the answer using this exact table format:

        | Icon | Meal Time | Suggested Food | Why It Helps |
        |---|---|---|---|
        | 🌅 | Breakfast | ... | ... |
        | 🍛 | Lunch | ... | ... |
        | 🍎 | Evening Snack | ... | ... |
        | 🌙 | Dinner | ... | ... |
        | 💧 | Hydration | ... | ... |
        | ⚠️ | Safety Note | ... | ... |
        """
    )
])


# ============================================================
# STEP 7: CREATE OUTPUT PARSER
# ============================================================

parser = StrOutputParser()


# ============================================================
# STEP 8: CREATE LANGCHAIN CHAIN
# ============================================================

chain = prompt | llm | parser


# ============================================================
# STEP 9: GET USER INPUT
# ============================================================

st.markdown('<div class="input-section">', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    age = st.number_input(
        "Enter your age",
        min_value=1,
        max_value=120,
        value=52,
        step=1
    )

with col2:
    weight_kg = st.number_input(
        "Enter your body weight in kg",
        min_value=1.0,
        max_value=300.0,
        value=90.0,
        step=0.5,
        format="%.1f"
    )

st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# STEP 10: GENERATE DIET PLAN
# ============================================================

button_clicked = st.button(
    "🥗 Generate Professional Diet Plan",
    use_container_width=True
)

if button_clicked:

    with st.spinner("Generating your healthy diet plan..."):

        response = chain.invoke({
            "age": age,
            "weight_kg": weight_kg
        })

    st.markdown(
        '<div class="result-title">📋 Generated Healthy Diet Plan</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="profile-box">
            Profile Summary: Age: {age} years | Body Weight: {weight_kg:.1f} kg
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(response, unsafe_allow_html=True)

    st.markdown(
        """
        <div class="note-box">
            <b>Important Health Note:</b><br>
            This diet plan is for learning and general guidance only.
            It is not a medical prescription. If you have diabetes, hypertension,
            heart disease, kidney issues, food allergies, or any medical condition,
            please consult a qualified doctor or dietitian before making major diet changes.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="footer-box">
            Generated using LangChain pipeline: User Input → Prompt Template → LLM → Output Parser → Diet Plan
        </div>
        """,
        unsafe_allow_html=True
    )