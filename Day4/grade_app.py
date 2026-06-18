import streamlit as st

st.title("Student Grading Application")

st.markdown("## Choose your mark (0 - 100) to check the grade.")

marks = st.slider("", 0, 100)

# Selected mark - big but not bold
st.markdown(
    f"<p style='font-size:30px; font-weight:normal;'>Selected Mark: {marks}</p>",unsafe_allow_html=True)

# Make the button bigger
st.markdown(
    """
    <style>
    div.stButton > button {height: 80px;width: 250px;font-size: 30px !important;font-weight;}
div.stButton > button p {font-size: 30px !important;font-weight;}
    </style>
    """,
    unsafe_allow_html=True
)

if st.button("Check Grade"):

    if marks <= 60:
        st.markdown(f"# Mark: {marks} → Grade: 'E'")

    elif marks >= 60 and marks <= 69:
        st.markdown(f"# Mark: {marks} → Grade: 'D'")

    elif marks >= 70 and marks <= 79:
        st.markdown(f"# Mark: {marks} → Grade: 'C'")

    elif marks >= 80 and marks <= 89:
        st.markdown(f"# Mark: {marks} → Grade: 'B'")

    elif marks >= 90 and marks <= 100:
        st.markdown(f"# Mark: {marks} → Grade: 'A'")