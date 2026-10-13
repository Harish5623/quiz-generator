"""Streamlit interface for generating and taking AI-created quizzes."""

import uuid

import streamlit as st

from quiz_generator import QuizGenerationError, generate_quiz
from quiz_validator import QuizValidationError, validate_quiz

st.set_page_config(page_title="AI Quiz Generator", page_icon="📝", layout="centered")
st.title("AI Quiz Generator")
st.caption("Build a multiple-choice quiz from a topic and the concepts you need to study.")

if "quiz" not in st.session_state:
    st.session_state.quiz = None
if "quiz_id" not in st.session_state:
    st.session_state.quiz_id = None
if "quiz_difficulty" not in st.session_state:
    st.session_state.quiz_difficulty = None
if "results" not in st.session_state:
    st.session_state.results = None

with st.form("quiz_request"):
    topic = st.text_input("Topic", placeholder="e.g. Python lists")
    syllabus_text = st.text_area(
        "Syllabus / concepts",
        placeholder="Enter one concept per line, for example:\nIndexing and slicing\nList methods\nNested lists",
        help="Separate concepts with new lines or commas. The quiz will be checked against these concepts.",
    )
    question_count = st.slider("Number of questions", min_value=1, max_value=20, value=5)
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
    generate_clicked = st.form_submit_button("Generate Quiz", type="primary", use_container_width=True)

if generate_clicked:
    if not topic.strip():
        st.error("Enter a topic to generate a quiz.")
    else:
        syllabus = [
            concept.strip()
            for line in syllabus_text.splitlines()
            for concept in line.split(",")
            if concept.strip()
        ]
        try:
            with st.spinner("Generating and checking your quiz..."):
                generated_quiz = generate_quiz(topic.strip(), syllabus, question_count, difficulty)
                validate_quiz(generated_quiz, topic.strip(), syllabus, question_count)
            st.session_state.quiz = generated_quiz
            st.session_state.quiz_id = uuid.uuid4().hex
            st.session_state.quiz_difficulty = difficulty
            st.session_state.results = None
            st.rerun()
        except (QuizGenerationError, QuizValidationError) as exc:
            st.error(str(exc))

quiz = st.session_state.quiz
if quiz:
    st.divider()
    st.subheader(f"{quiz['topic']} quiz")
    st.caption(f"{st.session_state.quiz_difficulty} difficulty · {len(quiz['questions'])} questions")

    with st.form("quiz_answers"):
        for index, item in enumerate(quiz["questions"], start=1):
            st.markdown(f"**{index}. {item['question']}**")
            st.radio(
                f"Answer for question {index}",
                item["options"],
                index=None,
                key=f"answer_{st.session_state.quiz_id}_{index}",
                label_visibility="collapsed",
            )
        submitted = st.form_submit_button("Submit Quiz", type="primary", use_container_width=True)

    if submitted:
        answers = [
            st.session_state.get(f"answer_{st.session_state.quiz_id}_{index}")
            for index in range(1, len(quiz["questions"]) + 1)
        ]
        score = sum(
            answer == item["correct_answer"]
            for answer, item in zip(answers, quiz["questions"])
        )
        st.session_state.results = {"answers": answers, "score": score}

    results = st.session_state.results
    if results is not None:
        score = results["score"]
        total = len(quiz["questions"])
        st.subheader(f"Your score: {score} / {total}")
        st.progress(score / total)
        for index, (answer, item) in enumerate(
            zip(results["answers"], quiz["questions"]), start=1
        ):
            st.markdown(f"**{index}. {item['question']}**")
            if answer == item["correct_answer"]:
                st.success(f"Correct: {item['correct_answer']}")
            else:
                response = answer if answer is not None else "No answer selected"
                st.error(f"Your answer: {response} · Correct answer: {item['correct_answer']}")
            st.info(item["explanation"])

    if st.button("Generate Another Quiz", use_container_width=True):
        st.session_state.quiz = None
        st.session_state.quiz_id = None
        st.session_state.quiz_difficulty = None
        st.session_state.results = None
        st.rerun()
