# AI Quiz Generator

A small Streamlit app that generates multiple-choice quizzes through an Ollama-compatible, OpenAI-style chat API. It checks the returned JSON and does a basic keyword-based topic and syllabus check before displaying a quiz.

## Requirements

- Python 3.10 or newer
- An Ollama Cloud API key
- A model available to your Ollama Cloud account

The app calls Ollama Cloud at `https://ollama.com/api/chat` and reads the API key from `.env`.

## Run locally

From this directory, create and activate a virtual environment, then install the dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env`, then add your Ollama Cloud API key:

```dotenv
OLLAMA_API_KEY=
OLLAMA_MODEL=gemma4:31b
```

The default `gemma4:31b` model is available to the configured Ollama Cloud account. Set `OLLAMA_MODEL` to another model name if you prefer one your account supports.

Start the app:

```powershell
streamlit run app.py
```

On macOS/Linux, activate the environment with `source .venv/bin/activate` and copy the example with `cp .env.example .env`.

## Use

Enter a topic, add syllabus concepts (one per line or comma-separated), choose the question count and difficulty, then generate the quiz. Answer each question and submit to see your score, correct answers, and explanations. Use **Generate Another Quiz** to start over.

The response must be strict JSON with exactly the expected fields and four options per question. Markdown-fenced JSON is intentionally rejected. Scope validation uses keyword overlap as a basic guard, not semantic proof; review generated questions before relying on them for high-stakes assessment.

## Deployment

Configure `OLLAMA_API_KEY` and `OLLAMA_MODEL` as environment variables or host secrets for deployment. Do not upload or commit your `.env` file.

## Project files

- `app.py`: Streamlit input, quiz display, answers, scoring, and review.
- `quiz_generator.py`: environment configuration, prompt construction, API request, and strict JSON parsing.
- `quiz_validator.py`: response structure, option/answer consistency, topic relevance, and basic syllabus coverage checks.
- `.env.example`: API key placeholder and default model for local setup.
