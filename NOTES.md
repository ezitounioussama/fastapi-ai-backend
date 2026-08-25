# API reference and design notes

## Project structure

```
fastapi-ai-backend/
├── app/
│   ├── main.py            FastAPI app, router wiring, error handler
│   ├── config.py          version and all validation limits
│   ├── models.py          Pydantic request/response models
│   ├── services.py        placeholder logic (the only file a real model touches)
│   └── routers/
│       ├── health.py      GET  /health
│       ├── chat.py        POST /chat
│       ├── quiz.py        POST /quiz
│       └── summarise.py   POST /summarise
├── tests/                 55 tests (pytest + httpx)
├── docs/
│   ├── api-test-report.md the test report
│   └── screenshots/       Swagger UI evidence
├── main.py                run the server
├── requirements.txt
└── pytest.ini
```

Once the server is running:

| URL | What it is |
|---|---|
| http://127.0.0.1:8000/docs | **Swagger UI** — try every endpoint in the browser |
| http://127.0.0.1:8000/redoc | ReDoc, the alternative documentation view |
| http://127.0.0.1:8000/openapi.json | The raw OpenAPI schema |

The tests need no running server: they talk to the app in-process through
`httpx.ASGITransport`.

## `GET /health`

Service status. **Never calls the AI layer**, so it keeps answering even if the model is down —
which is the whole point of a health check.

```bash
curl http://127.0.0.1:8000/health
```

```json
{"status": "ok", "version": "1.0.0", "timestamp": "2026-08-13T11:13:24.971960Z"}
```

## `POST /chat`

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "What is a Python list?"}'
```

```json
{
  "answer": "A list stores several values in order under one name, written with square brackets: scores = [10, 20, 30]. You reach an item by its position, counting from 0, so scores[0] is 10.",
  "question": "What is a Python list?",
  "source": "placeholder",
  "characters": 178,
  "timestamp": "2026-08-13T11:13:24.978321Z"
}
```

| Field | Rule |
|---|---|
| `message` | required, 1–2000 characters |

## `POST /quiz`

```bash
curl -X POST http://127.0.0.1:8000/quiz \
  -H 'Content-Type: application/json' \
  -d '{"topic": "Python lists", "num_questions": 3}'
```

```json
{
  "topic": "Python lists",
  "count": 3,
  "questions": [
    {
      "number": 1,
      "question": "Which statement best describes Python lists?",
      "options": ["The correct description", "A wrong description",
                  "An unrelated idea", "None of these"],
      "answer_index": 0
    }
  ],
  "source": "placeholder",
  "timestamp": "2026-08-13T11:12:07Z"
}
```

| Field | Rule |
|---|---|
| `topic` | required, 2–100 characters |
| `num_questions` | optional, 1–10, defaults to 5 |

## `POST /summarise`

```bash
curl -X POST http://127.0.0.1:8000/summarise \
  -H 'Content-Type: application/json' \
  -d '{"text": "Python is a high-level programming language. It is known for readable syntax. Many beginners start with Python because the code looks close to plain English. It is widely used for web development, data analysis and automation.", "max_bullets": 2}'
```

```json
{
  "bullets": [
    "Python is a high-level programming language.",
    "Many beginners start with Python because the code looks close to plain English."
  ],
  "bullet_count": 2,
  "original_characters": 226,
  "summary_characters": 123,
  "compression_ratio": 0.54,
  "source": "placeholder",
  "timestamp": "2026-08-13T11:13:36.457193Z"
}
```

| Field | Rule |
|---|---|
| `text` | required, 20–10000 characters |
| `max_bullets` | optional, 1–10, defaults to 3 |

## Validation errors

Invalid requests get `422` with a consistent object — not FastAPI's default bare `detail` list:

```json
{
  "error": "validation_error",
  "detail": "The request was rejected. Check: body.num_questions.",
  "errors": [
    {
      "field": "body.num_questions",
      "message": "Input should be less than or equal to 10",
      "type": "less_than_equal"
    }
  ]
}
```

Every problem is listed, not just the first: sending both a too-short `text` and an out-of-range
`max_bullets` returns two entries in `errors`.

## Design notes

**Nothing returns a bare value.** Every response is an object with named fields, including
errors. A client can add support for a new field without anything breaking, which a plain string
or a raw list makes impossible.

**Limits live in one file.** `app/config.py` holds every bound, and both the Pydantic models and
their descriptions read from it — so the documented limit and the enforced limit cannot drift
apart.

**Validation happens before route code.** The limits are declared on the request models, so
FastAPI rejects bad input and the route body never runs. It also means the bounds appear
automatically in the Swagger schema, where a test asserts `num_questions` shows
`minimum: 1, maximum: 10`.

**The placeholder logic is deterministic.** No randomness anywhere, so the same input always
gives the same output and tests can assert exact values. The summariser is genuinely extractive —
it scores sentences by position and length, then restores their original order — and a test
asserts every returned bullet appears verbatim in the input, so it can never invent text.

**`/health` is deliberately isolated.** It imports nothing from the AI layer beyond the clock. A
health check that fails when the model fails cannot tell you whether the service is up.
