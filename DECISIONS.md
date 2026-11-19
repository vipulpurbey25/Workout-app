# Workout planner decisions

Recorded before implementation. This file has no API keys or other secrets. The Groq key lives only in `.env`, which is gitignored.

## Product

One Streamlit page. No accounts and no saved history. A generated plan stays on screen until the next successful generation.

The page collects:

- Fitness goal: Build muscle, Lose fat, General fitness, Improve endurance
- Experience: Beginner, Intermediate, Advanced
- Days available per week
- Equipment (one or more): No equipment, Home dumbbells, Full gym
- Optional injuries or limitations

"Generate Plan" sends those inputs to Groq and renders a week: one nutrition note, then each training day with a warm-up and exercises (sets, reps, rest, notes).

The number of training days matches "days available." Rest is called out in a short recovery note instead of padding the week out to seven calendar days.

## Trade-offs

| Choice | Taken | Given up |
| --- | --- | --- |
| Model | `openai/gpt-oss-20b` | `llama-3.1-8b-instant` was the first choice for speed, but this Groq key returns 404 for that model. `gpt-oss-20b` is the smallest general chat model on the account, and it accepts JSON mode. `gpt-oss-120b` would likely write steadier plans and use more of the free quota. |
| Response shape | JSON parsed into a plan, then rendered by the app | Free-form markdown would be less code, and a small model will sometimes return JSON we have to reject. |
| Equipment | Multiselect | "No equipment" cannot be combined with dumbbells or a gym. Those plans contradict each other, so that mix is rejected with a friendly message. |
| Plan depth | Warm-up, exercises, and one nutrition note | No meal plan, no video links, no progression across weeks. |
| Invalid days | Values outside 1–7, including 0, never call Groq | The number input allows 0 so that case can be shown. The slider-only range 1–7 would have hidden it. |
| Tests | The Groq client is faked | Unit tests do not prove the live model or the network. |
| Secrets | `.env` plus `python-dotenv` | The key is not read from source. It was pasted into chat, so it should be rotated in the Groq console. |
| Injury disclaimer | A fixed sentence in the app when the injuries box has text | A model-written disclaimer can be dropped or turn into medical advice. |
| Session shape | The system prompt forbids diagnosis and treatment, asks for the limitation on each affected exercise, and caps a day at 4–6 exercises and about 45–60 minutes | The app does not reject a plan that breaks that cap. A hard check would need an exercise list the model does not reliably follow. |

## Errors the user can see

- Days outside 1–7, an empty equipment list, an unknown goal or experience level, or "No equipment" mixed with other gear: a short message, and no API call.
- Missing API key, network failure, a bad key, or a rate limit: one unavailable-service message.
- Empty model output, or JSON that is not the expected week: a fallback asking the user to try again.

The planner function validates first, builds the prompt, calls Groq inside `try/except`, and either returns the plan or raises `PlanGenerationError` with that message. The page catches it and does not show a traceback.
