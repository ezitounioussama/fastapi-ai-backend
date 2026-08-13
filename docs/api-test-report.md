# API Test Report

**Project:** AI Study Assistant API
**Version:** 1.0.0
**Date tested:** 13 August 2026
**Environment:** Python 3.14, FastAPI 0.141.1, Pydantic 2.13.4, uvicorn on `127.0.0.1:8010`

Every response body in this report was copied from an actual run against the live server, not
written by hand.

---

## Summary

| Suite | Result |
|---|---|
| Automated tests (pytest + httpx) | **55 passed, 0 failed** |
| Manual Swagger UI tests | **2 of 2 as expected** (1 valid, 1 invalid) |
| Endpoints covered | `/health`, `/chat`, `/quiz`, `/summarise`, `/` |
| Validation errors verified | 15 distinct cases |

---

## 1. Manual tests in Swagger UI

Performed at `http://127.0.0.1:8010/docs` using **Try it out → Execute**.
Screenshots are in [`screenshots/`](screenshots/).

### Manual test 1 — valid request (expected 200)

**Endpoint:** `POST /quiz`
**Screenshot:** [`02-swagger-quiz-valid-200.png`](screenshots/02-swagger-quiz-valid-200.png)

Request body:

```json
{
  "num_questions": 3,
  "topic": "Python lists"
}
```

**Expected:** `200`, a `questions` array holding exactly 3 items, each with four options and an
`answer_index` between 0 and 3.

**Actual:** `200`. Response body (truncated to the first two questions):

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
    },
    {
      "number": 2,
      "question": "In which situation would you use Python lists?",
      "options": ["A situation where it does not apply", "The appropriate situation",
                  "Never", "Only in other languages"],
      "answer_index": 1
    }
  ],
  "source": "placeholder",
  "timestamp": "2026-08-13T11:12:07Z"
}
```

**Verdict:** pass. `count` matches the request, the topic is interpolated into every question,
and `answer_index` varies between questions rather than always being 0.

### Manual test 2 — invalid request (expected 422)

**Endpoint:** `POST /quiz`
**Screenshot:** [`03-swagger-quiz-invalid-422.png`](screenshots/03-swagger-quiz-invalid-422.png)

Request body — `num_questions` is 99, above the limit of 10:

```json
{"topic": "Python lists", "num_questions": 99}
```

**Expected:** `422`, and an error body naming `num_questions` as the offending field.

**Actual:** `422`, shown in Swagger as *Error: Unprocessable Content*:

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

**Verdict:** pass. The route function never ran — Pydantic rejected the body first.

> Note for anyone repeating this: editing the request body by scripting
> `textarea.value` does not work, because Swagger UI is a React app and ignores a
> value set that way. The first attempt silently re-sent the previous body and returned
> `200`. Typing into the field (or using a tool that simulates typing) is what registers.

---

## 2. Endpoint reference and verified results

### `GET /health`

Returns service status. Does not touch the AI layer, so it stays useful as a liveness probe.

| | |
|---|---|
| **Expected** | `200` with `status`, `version` and `timestamp` |
| **Actual** | `200` |

```json
{"status": "ok", "version": "1.0.0", "timestamp": "2026-08-13T11:13:24.971960Z"}
```

Also verified: the timestamp carries a timezone, differs between two consecutive calls (so it is
generated per request, not fixed at import), and `POST /health` correctly returns `405 Method Not
Allowed`.

### `POST /chat`

| | |
|---|---|
| **Request** | `{"message": "What is a Python list?"}` |
| **Expected** | `200` with a structured `answer` field |
| **Actual** | `200` |

```json
{
  "answer": "A list stores several values in order under one name, written with square brackets: scores = [10, 20, 30]. You reach an item by its position, counting from 0, so scores[0] is 10.",
  "question": "What is a Python list?",
  "source": "placeholder",
  "characters": 178,
  "timestamp": "2026-08-13T11:13:24.978321Z"
}
```

Also verified: an unrecognised topic returns an honest "running on placeholder logic" reply
rather than an invented answer, and `characters` always equals `len(answer)`.

### `POST /quiz`

Covered by both manual tests above. Additionally verified automatically:

- `num_questions` omitted → defaults to 5
- both boundary values (1 and 10) are accepted, since `ge`/`le` are inclusive
- the requested topic appears in every question
- `answer_index` is not constant across questions

### `POST /summarise`

| | |
|---|---|
| **Request** | 283 characters of text, `max_bullets: 3` |
| **Expected** | `200`, at most 3 bullets, all taken from the source text |
| **Actual** | `200`, 3 bullets, 191 characters, ratio 0.67 |

```json
{
  "bullets": [
    "Python is a high-level programming language.",
    "Many beginners start with Python because the code looks close to plain English.",
    "It is widely used for web development, data analysis and automation."
  ],
  "bullet_count": 3,
  "original_characters": 283,
  "summary_characters": 191,
  "compression_ratio": 0.67,
  "source": "placeholder",
  "timestamp": "2026-08-13T11:13:36.457193Z"
}
```

Note that the second sentence ("It is known for readable syntax.") was dropped — it is the
shortest and therefore scored lowest. The three chosen bullets remain in their original order,
and each one appears verbatim in the input, which is asserted by a test: the summariser selects
sentences and never rewrites them.

---

## 3. Validation errors verified

All limits are declared on the Pydantic request models, so FastAPI rejects bad input before any
route code runs. Every row below was confirmed against the running server.

| Endpoint | Invalid input | Status | Field reported | Message |
|---|---|---|---|---|
| `/chat` | `{"message": ""}` | 422 | `body.message` | String should have at least 1 character |
| `/chat` | `{}` (message missing) | 422 | `body.message` | Field required |
| `/chat` | message of 2001 characters | 422 | `body.message` | String should have at most 2000 characters |
| `/chat` | `{"message": 123}` | 422 | `body.message` | Input should be a valid string |
| `/quiz` | `num_questions: 0` | 422 | `body.num_questions` | Input should be greater than or equal to 1 |
| `/quiz` | `num_questions: 99` | 422 | `body.num_questions` | Input should be less than or equal to 10 |
| `/quiz` | `num_questions: -3` | 422 | `body.num_questions` | Input should be greater than or equal to 1 |
| `/quiz` | `topic: "a"` | 422 | `body.topic` | String should have at least 2 characters |
| `/quiz` | topic missing | 422 | `body.topic` | Field required |
| `/summarise` | `text: "Too short."` | 422 | `body.text` | String should have at least 20 characters |
| `/summarise` | text over 10000 characters | 422 | `body.text` | String should have at most 10000 characters |
| `/summarise` | `max_bullets: 0` | 422 | `body.max_bullets` | Input should be greater than or equal to 1 |
| `/summarise` | `max_bullets: 11` | 422 | `body.max_bullets` | Input should be less than or equal to 10 |
| `/summarise` | text missing | 422 | `body.text` | Field required |
| `/health` | `POST` instead of `GET` | 405 | — | Method Not Allowed |

**Two bad fields at once** are both reported, rather than stopping at the first:

```
POST /summarise  {"text": "short", "max_bullets": 50}   →  422
```

```json
{
  "error": "validation_error",
  "detail": "The request was rejected. Check: body.text, body.max_bullets.",
  "errors": [
    {"field": "body.text", "message": "String should have at least 20 characters",
     "type": "string_too_short"},
    {"field": "body.max_bullets", "message": "Input should be less than or equal to 10",
     "type": "less_than_equal"}
  ]
}
```

---

## 4. Automated tests

```
$ pytest -q
.......................................................                  [100%]
55 passed in 0.15s
```

| File | Tests | Covers |
|---|---|---|
| `tests/test_health.py` | 8 | status/version/timestamp, timezone, freshness, per-request timestamp, 405 on POST |
| `tests/test_chat.py` | 13 | structured reply, echoed question, character count, known and unknown topics, 5 validation cases, custom error shape |
| `tests/test_quiz.py` | 14 | question count, per-question shape, topic interpolation, varying answer index, default, 7 validation cases |
| `tests/test_summarise.py` | 15 | bullet cap, compression, extractive check, original order, short-text case, default, 6 validation cases |
| `tests/test_root_and_docs.py` | 5 | index route, OpenAPI schema, Swagger UI loads, limits present in the schema, 404 |

The client is `httpx.AsyncClient` wired to the app through `ASGITransport`, so requests go
through the real routing, validation and serialisation stack in-process — no server to start and
no network. `fastapi.testclient.TestClient` was avoided on purpose: Starlette now warns that
using it with `httpx` is deprecated in favour of `httpx2`, and calling httpx directly both
sidesteps that and matches the brief's "pytest and httpx" requirement literally.

### Boundary values are tested on both sides

For every numeric limit, the value *at* the limit is asserted valid and the value one past it
asserted invalid. `ge` and `le` are inclusive, so `num_questions: 10` must pass while `11` must
fail — a test asserting only the failure would still pass if the limit were wrongly set to 9.

---

## 5. Issues found and fixed during testing

**`HTTP_422_UNPROCESSABLE_ENTITY` is deprecated.** The suite passed but emitted 17 warnings:
Starlette has renamed the constant to `HTTP_422_UNPROCESSABLE_CONTENT`. Since either name breaks
on some supported version, the handler now uses the literal `422`. Warnings are back to zero.

**Included routers do not appear in `app.routes`.** An early sanity check printed the registered
paths and showed only `/`, `/docs` and friends — the four routers were missing. They were not:
FastAPI 0.141 keeps included routers as `_IncludedRouter` objects and resolves their paths
lazily. Confirmed properly by asserting against `app.openapi()["paths"]`, which is now a test.

**Swagger UI ignores scripted `textarea.value` edits.** Described under manual test 2 above. The
first invalid-request attempt silently re-sent the old body and returned `200`, which would have
been recorded as a false pass had the response body not been read closely.
