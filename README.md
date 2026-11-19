# Workout Planner

A one-page Streamlit app that turns a few structured answers into a weekly workout. Groq writes the plan as JSON. The page renders it day by day, with exercises, sets, reps, and rest, so it reads like a session someone can follow rather than a paragraph of advice.

This is general training guidance, not medical advice.

## What you enter

| Input | Control | Allowed values |
| --- | --- | --- |
| Fitness goal | Dropdown | Build muscle, Lose fat, General fitness, Improve endurance |
| Experience | Dropdown | Beginner, Intermediate, Advanced |
| Days available | Number | 1–7. `0` is rejected and Groq is not called. |
| Equipment | Multiselect | No equipment, Home dumbbells, Full gym |
| Injuries or limitations | Optional text | For example, “bad knees” or “no overhead pressing” |

“No equipment” cannot be combined with dumbbells or a full gym, because those plans contradict each other.

**Generate Plan** returns:

- a short nutrition note for the goal
- a short recovery note
- one section per training day, with a warm-up and exercises (sets, reps, rest, notes)

The number of training days matches the number you entered. Rest is described in the recovery note instead of padding the week out to seven calendar days.

If the injuries box has text, the page adds this fixed line above the plan:

> This plan is general training guidance, not medical advice. Stop if pain increases, and check with a clinician before training through an injury.

The model does not write that sentence, so it cannot be dropped or turned into a diagnosis.

## Run it

Python 3.9 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

```bash
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
```

Get a key from the [Groq console](https://console.groq.com/). Then:

```bash
streamlit run app.py
```

Open the local URL Streamlit prints. `.env` is gitignored. Do not commit the key.

`openai/gpt-oss-20b` is the default because it is on Groq’s free tier for this project and it accepts JSON output. Set `GROQ_MODEL` if your account uses a different chat model.

## What can go wrong

The page shows a short message instead of a traceback.

| Situation | What you see |
| --- | --- |
| Days outside 1–7, no equipment selected, or an unknown goal or level | A validation message. Groq is not called. |
| Missing key, bad key, network failure, or rate limit | The plan service is unavailable. Check the connection and API key. |
| Empty or unreadable model output | A fallback asking you to try again. |

## Tests

```bash
pytest
```

Tests use a fake Groq client, so they do not spend quota or need a key. They cover invalid inputs, the prompt text, a parsed week, API failures, empty or malformed output, the system-prompt limits, and the injury disclaimer.

## How the plan is built

`generate_workout_plan` takes the structured inputs, validates them, builds the prompt, calls Groq inside `try/except`, and returns a parsed week.

The system prompt tells the model to:

- respect the listed equipment, the injury notes, and the day count
- avoid diagnosis, treatment, and medical claims
- name a reported limitation in the notes of each affected exercise
- keep each day to 4–6 exercises and about 45–60 minutes

A plan that ignores the exercise cap is still shown. Rejecting it would depend on the model counting exercises the same way every time.

## Project layout

```text
app.py                 Streamlit page
workout_planner/       validation, prompt, Groq call, parsing, disclaimer
tests/                 unit tests
DECISIONS.md           choices and trade-offs, with no secrets
.env.example           variable names only
```

## Scope

The app does not save plans, offer a regenerate button, download a file, or swap a single exercise. Those were left out on purpose.
