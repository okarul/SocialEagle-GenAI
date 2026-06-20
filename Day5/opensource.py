from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import streamlit as st

st.title("Local Qwen Chatbot")
st.write("Welcome to my local chatbot.")
st.write("(This app uses the Qwen2.5-0.5B-Instruct model.)")

# Because this file is inside the model folder
model_path = "."

@st.cache_resource
def load_model():
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        local_files_only=True
    )

    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        dtype=torch.float32,
        device_map="auto",
        local_files_only=True
    )

    return tokenizer, model

st.write("Loading Qwen model... please wait.")

tokenizer, model = load_model()

st.success("Model loaded successfully.")

user_prompt = st.text_area("Enter your question:", height=120)

if st.button("Ask Qwen"):
    if user_prompt.strip() == "":
        st.warning("Please enter a question first.")
    else:
        with st.spinner("Qwen is thinking..."):

            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Give simple and clear answers."
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]

            text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            inputs = tokenizer(
                text,
                return_tensors="pt"
            ).to(model.device)

            outputs = model.generate(
                **inputs,
                max_new_tokens=200,
                temperature=0.7,
                do_sample=True
            )

            generated_tokens = outputs[0][inputs["input_ids"].shape[-1]:]

            response = tokenizer.decode(
                generated_tokens,
                skip_special_tokens=True
            )

        st.subheader("Qwen Response")
        st.write(response)