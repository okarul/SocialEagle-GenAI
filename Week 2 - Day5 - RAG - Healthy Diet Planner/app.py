# ============================================================
# BASIC LANGCHAIN GENAI APP
# Use case: Simple Healthy Diet Planner
# Learning Goal:
# - See the output of each LangChain stage step by step
# ============================================================


# ============================================================
# STEP 1: IMPORT REQUIRED LIBRARIES
# ============================================================

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# ============================================================
# PAUSE FUNCTION
# Purpose:
# - Waits after each step
# - Continues only when user presses Enter
# ============================================================

def wait_for_enter():
    input("\nPress Enter to continue to the next step...")


print("\nSTEP 1 COMPLETED: Required libraries imported successfully.")
wait_for_enter()


# ============================================================
# STEP 2: LOAD ENVIRONMENT VARIABLES
# Purpose:
# - Reads the social_eagle.env file
# - Loads OPENAI_API_KEY
# ============================================================

load_dotenv("social_eagle.env")

print("\nSTEP 2 COMPLETED: Environment variables loaded from social_eagle.env.")
wait_for_enter()


# ============================================================
# STEP 3: INITIALIZE THE LLM MODEL
# Purpose:
# - Creates the LLM object
# - LLM is initialized here
# - LLM is not executed yet
# ============================================================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

print("\nSTEP 3 COMPLETED: LLM initialized.")
print("LLM object created:")
print(llm)
wait_for_enter()


# ============================================================
# STEP 4: CREATE THE PROMPT TEMPLATE
# Purpose:
# - Creates a reusable prompt template
# - {age} and {weight_kg} are placeholders
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
        """
    ),
    (
        "human",
        """
        My age is {age} years old.
        My body weight is {weight_kg} kg.

        Please create a simple one-day healthy diet plan suitable for my age.

        The diet plan should include:
        1. Breakfast
        2. Lunch
        3. Evening snack
        4. Dinner
        5. Hydration reminder
        6. Safety note
        """
    )
])

print("\nSTEP 4 COMPLETED: Prompt template created.")

print("\n--- PROMPT TEMPLATE OBJECT ---")
print(prompt)

wait_for_enter()


# ============================================================
# STEP 5: COLLECT USER INPUT
# Purpose:
# - Gets age and weight from user
# ============================================================

age = input("\nEnter your age: ")
weight_kg = input("Enter your body weight in kg: ")

print("\nSTEP 5 COMPLETED: User input collected.")
print(f"Age entered: {age}")
print(f"Weight entered: {weight_kg} kg")

wait_for_enter()


# ============================================================
# STEP 6: SHOW FINAL PROMPT AFTER VARIABLE REPLACEMENT
# Purpose:
# - Replaces {age} and {weight_kg}
# - Shows the actual prompt that will go to the LLM
# ============================================================

formatted_prompt = prompt.invoke({
    "age": age,
    "weight_kg": weight_kg
})

print("\nSTEP 6 COMPLETED: Final prompt created after replacing variables.")

print("\n--- FINAL PROMPT SENT TO LLM ---")
print(formatted_prompt)

print("\n--- FINAL PROMPT MESSAGES ---")
for message in formatted_prompt.messages:
    print("\nMESSAGE TYPE:", message.type)
    print("MESSAGE CONTENT:")
    print(message.content)

wait_for_enter()


# ============================================================
# STEP 7: SEND PROMPT TO LLM
# Purpose:
# - This is where the LLM is executed
# - Shows the raw AIMessage output
# ============================================================

print("\nSTEP 7 STARTED: Sending prompt to LLM...")
print("This is where the LLM is actually executed.")

llm_response = llm.invoke(formatted_prompt)

print("\nSTEP 7 COMPLETED: Raw response received from LLM.")

print("\n--- RAW LLM RESPONSE OBJECT ---")
print(llm_response)

print("\n--- RAW LLM RESPONSE CONTENT ONLY ---")
print(llm_response.content)

wait_for_enter()


# ============================================================
# STEP 8: CREATE OUTPUT PARSER
# Purpose:
# - Converts AIMessage object into plain text
# ============================================================

parser = StrOutputParser()

print("\nSTEP 8 COMPLETED: Output parser created.")
print("Parser object:")
print(parser)

wait_for_enter()


# ============================================================
# STEP 9: PARSE THE LLM RESPONSE
# Purpose:
# - Converts raw AIMessage into plain string
# ============================================================

final_output = parser.invoke(llm_response)

print("\nSTEP 9 COMPLETED: LLM response parsed into plain text.")

print("\n--- PARSED FINAL OUTPUT ---")
print(final_output)

wait_for_enter()


# ============================================================
# STEP 10: CREATE FULL LANGCHAIN CHAIN
# Purpose:
# - Connects prompt, LLM, and parser
# - This is the shortcut version of the steps above
# ============================================================

chain = prompt | llm | parser

print("\nSTEP 10 COMPLETED: Full LangChain chain created.")
print("Chain flow:")
print("Prompt Template → LLM → Output Parser")

wait_for_enter()


# ============================================================
# STEP 11: RUN FULL CHAIN DIRECTLY
# Purpose:
# - Runs everything in one line using chain.invoke()
# - This should produce the same final answer
# ============================================================

chain_output = chain.invoke({
    "age": age,
    "weight_kg": weight_kg
})

print("\nSTEP 11 COMPLETED: Full chain executed directly.")

print("\n--- FULL CHAIN OUTPUT ---")
print(chain_output)


# ============================================================
# END OF PROGRAM
# ============================================================

print("\nProgram completed successfully.")