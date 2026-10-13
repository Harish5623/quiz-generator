"""Ollama-compatible chat API client and strict quiz JSON parser."""

import json
import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()


class QuizGenerationError(RuntimeError):
    """Raised when configuration or the quiz API request fails."""


def _build_prompt(topic: str, syllabus: list[str], question_count: int, difficulty: str) -> str:
    concepts = "\n".join(f"- {concept}" for concept in syllabus) or "- Use the requested topic only."
    schema = {
        "topic": topic,
        "questions": [
            {
                "question": "Question text",
                "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                "correct_answer": "Option 1",
                "explanation": "Why the correct answer is correct.",
            }
        ],
    }
    return (
        "Create a multiple-choice quiz strictly limited to the topic and syllabus below. "
        "Do not introduce concepts outside this scope. Cover every listed syllabus concept. "
        f"Write exactly {question_count} questions at {difficulty} difficulty. "
        "Each question must have exactly four distinct options and one correct answer. "
        "The correct_answer value must exactly match one option. Include a concise explanation. "
        "Return ONLY valid JSON: no Markdown fences, comments, or surrounding text. "
        "Use exactly these keys and this structure (the questions array must have the requested count):\n"
        f"{json.dumps(schema, ensure_ascii=False)}\n\n"
        f"Topic: {topic}\nSyllabus concepts:\n{concepts}"
    )


def generate_quiz(topic: str, syllabus: list[str], question_count: int, difficulty: str) -> Any:
    """Request a quiz from Ollama Cloud's native chat endpoint."""
    model = os.getenv("OLLAMA_MODEL", "").strip()
    api_key = os.getenv("OLLAMA_API_KEY", "").strip()
    if not api_key or not model:
        raise QuizGenerationError("Set OLLAMA_API_KEY and OLLAMA_MODEL in your .env file.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You generate accurate, in-scope quizzes and return strict JSON only.",
            },
            {
                "role": "user",
                "content": _build_prompt(topic, syllabus, question_count, difficulty),
            },
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.3},
    }

    try:
        response = requests.post(
            "https://ollama.com/api/chat",
            headers=headers,
            json=payload,
            timeout=90,
        )
        response.raise_for_status()
        response_data = response.json()
        content = response_data["message"]["content"]
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        if status in (401, 403):
            raise QuizGenerationError("Ollama Cloud rejected the API key. Check or replace it in .env.") from None
        if status == 404:
            raise QuizGenerationError(
                f"Ollama Cloud could not find model '{model}'. Check that this model is available to your account."
            ) from None
        raise QuizGenerationError(
            f"Ollama Cloud returned HTTP {status}. Check the model and account usage limits."
        ) from None
    except requests.RequestException:
        raise QuizGenerationError("Could not connect to Ollama Cloud. Check your internet connection and try again.") from None
    except (ValueError, KeyError, IndexError, TypeError):
        raise QuizGenerationError("The quiz API returned an unexpected response format.") from None

    if not isinstance(content, str) or not content.strip():
        raise QuizGenerationError("The quiz API returned an empty response.")
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        raise QuizGenerationError(
            "The model did not return strict JSON. Try again or choose a model that supports JSON output."
        ) from None
