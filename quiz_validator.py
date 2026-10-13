"""Validation for quizzes returned by the language model."""

import re
from typing import Any


class QuizValidationError(ValueError):
    """Raised when a generated quiz does not match the required format or scope."""


_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "how", "in", "is", "it", "of", "on", "or", "the", "to", "what",
    "when", "which", "with",
}


def _keywords(text: str) -> set[str]:
    return {
        word.lower()
        for word in re.findall(r"[a-zA-Z0-9]+", text)
        if len(word) > 2 and word.lower() not in _STOP_WORDS
    }


def validate_quiz(
    quiz: Any,
    topic: str,
    syllabus: list[str],
    question_count: int,
) -> dict[str, Any]:
    """Validate quiz structure, answers, relevance, and basic syllabus coverage.

    Scope checks use keyword overlap. They catch clearly unrelated output, but do
    not replace a human review of semantic relevance.
    """
    if not isinstance(quiz, dict) or set(quiz) != {"topic", "questions"}:
        raise QuizValidationError("The response must contain only 'topic' and 'questions'.")

    if not isinstance(quiz["topic"], str) or quiz["topic"].strip().casefold() != topic.strip().casefold():
        raise QuizValidationError("The response topic does not match the requested topic.")

    questions = quiz["questions"]
    if not isinstance(questions, list) or len(questions) != question_count:
        raise QuizValidationError(f"The response must contain exactly {question_count} questions.")

    scope_keywords = _keywords(topic)
    for concept in syllabus:
        scope_keywords.update(_keywords(concept))

    question_keyword_sets: list[set[str]] = []
    for index, item in enumerate(questions, start=1):
        if not isinstance(item, dict) or set(item) != {
            "question", "options", "correct_answer", "explanation"
        }:
            raise QuizValidationError(f"Question {index} has an invalid structure.")

        question = item["question"]
        options = item["options"]
        answer = item["correct_answer"]
        explanation = item["explanation"]

        if not isinstance(question, str) or not question.strip():
            raise QuizValidationError(f"Question {index} must have question text.")
        if (
            not isinstance(options, list)
            or len(options) != 4
            or any(not isinstance(option, str) or not option.strip() for option in options)
        ):
            raise QuizValidationError(f"Question {index} must have exactly four non-empty options.")
        if len({option.strip().casefold() for option in options}) != 4:
            raise QuizValidationError(f"Question {index} has duplicate options.")
        if not isinstance(answer, str) or answer not in options:
            raise QuizValidationError(f"Question {index}'s correct answer must exactly match an option.")
        if not isinstance(explanation, str) or not explanation.strip():
            raise QuizValidationError(f"Question {index} must include an explanation.")

        searchable_text = " ".join([question, *options, answer, explanation])
        keywords = _keywords(searchable_text)
        if scope_keywords and not keywords.intersection(scope_keywords):
            raise QuizValidationError(f"Question {index} appears unrelated to the topic and syllabus.")
        question_keyword_sets.append(keywords)

    for concept in syllabus:
        concept_keywords = _keywords(concept)
        if concept_keywords and not any(concept_keywords.intersection(keys) for keys in question_keyword_sets):
            raise QuizValidationError(f"The quiz does not appear to cover syllabus concept: {concept}.")

    return quiz
