from streamlit import st

def display_header():
    st.title("AI Interview Simulator")
    st.subheader("Prepare for your next interview with our mock interview simulator!")

def display_question(question):
    st.write(question)

def display_response_input():
    return st.text_area("Your Response:", height=150)

def display_score(score):
    st.success(f"Your performance score: {score}/100")

def display_button(label, on_click):
    if st.button(label):
        on_click()