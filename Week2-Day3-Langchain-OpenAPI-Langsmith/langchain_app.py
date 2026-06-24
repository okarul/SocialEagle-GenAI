# langchain_app.py

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


def load_environment():
    """
    Loads API keys and LangSmith settings from social_eagle.env.
    """

    current_folder = Path(__file__).parent
    env_path = current_folder / "social_eagle.env"

    load_dotenv(dotenv_path=env_path, override=True)

    openai_key = os.getenv("OPENAI_API_KEY")
    langsmith_tracing = os.getenv("LANGSMITH_TRACING")
    langsmith_key = os.getenv("LANGSMITH_API_KEY")
    langsmith_project = os.getenv("LANGSMITH_PROJECT")

    return {
        "env_path": env_path,
        "env_exists": env_path.exists(),
        "openai_key_loaded": openai_key is not None,
        "langsmith_tracing": langsmith_tracing,
        "langsmith_key_loaded": langsmith_key is not None,
        "langsmith_project": langsmith_project,
    }


def get_ai_response(user_input):
    """
    Sends user input to OpenAI model using LangChain
    and returns the model output.
    """

    if not user_input.strip():
        return "Please enter a valid question."

    openai_key = os.getenv("OPENAI_API_KEY")

    if openai_key is None:
        return "OPENAI_API_KEY is missing. Please check your social_eagle.env file."

    llm = ChatOpenAI(
        #model="gpt-4o-mini",
        temperature=0
    )

    response = llm.invoke(user_input)

    return response.content


if __name__ == "__main__":
    env_status = load_environment()

    print("ENV file path:", env_status["env_path"])
    print("ENV file exists:", env_status["env_exists"])
    print("OPENAI_API_KEY loaded:", env_status["openai_key_loaded"])
    print("LANGSMITH_TRACING:", env_status["langsmith_tracing"])
    print("LANGSMITH_API_KEY loaded:", env_status["langsmith_key_loaded"])
    print("LANGSMITH_PROJECT:", env_status["langsmith_project"])

    question = input("\nEnter your question: ")
    answer = get_ai_response(question)

    print("\nModel Output:")
    print(answer)