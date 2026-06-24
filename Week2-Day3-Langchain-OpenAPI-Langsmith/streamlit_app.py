# streamlit_app.py

import streamlit as st

from langchain_app import load_environment, get_ai_response


st.set_page_config(
    page_title="LangChain OpenAI Demo",
    page_icon="🤖",
    layout="centered"
)

st.title("LangChain + OpenAI + LangSmith Demo")

st.markdown(
    """
     <p style='font-size:18px; line-height:1.6;'>
        <span style='color:yellow;'>User enters Prompt => LangChain sends to OpenAI => Display the response => LangSmith traces the run.</span>
    </p>
    """,
    unsafe_allow_html=True
)

env_status = load_environment()

#with st.expander("Environment Check"):
#    st.write("ENV file path:", str(env_status["env_path"]))
#    st.write("ENV file exists:", env_status["env_exists"])
#    st.write("OPENAI_API_KEY loaded:", env_status["openai_key_loaded"])
#    st.write("LANGSMITH_TRACING:", env_status["langsmith_tracing"])
#    st.write("LANGSMITH_API_KEY loaded:", env_status["langsmith_key_loaded"])
#    st.write("LANGSMITH_PROJECT:", env_status["langsmith_project"])


if not env_status["openai_key_loaded"]:
    st.error("OPENAI_API_KEY is missing. Please check your social_eagle.env file.")
    st.stop()


user_input = st.text_area(
    "Enter your question:",
    placeholder="Example: Explain LangChain in 3 simple bullet points.",
    height=120
)


if st.button("Get AI Response"):
    if user_input.strip() == "":
        st.warning("Please enter a question first.")
    else:
        with st.spinner("AI is thinking..."):
            response = get_ai_response(user_input)

        st.subheader("User Input")
        st.write(user_input)

        st.subheader("Model Output")
        st.write(response)

        st.success("Response generated successfully. Check LangSmith tracing dashboard.")