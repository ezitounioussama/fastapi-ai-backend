# AI Study Assistant API

A small FastAPI backend for a study assistant: ask a question (`/chat`), get a quiz on a topic
(`/quiz`), turn a wall of text into bullets (`/summarise`), and check the service is alive
(`/health`).

The three AI-facing endpoints run on placeholder logic — deterministic Python, no model calls, no
API key. That is deliberate: the request and response shapes are the finished contract, so
connecting a real model later means rewriting `app/services.py` and nothing else. It also makes
every response exactly reproducible, which is what lets the tests assert real values instead of
"something came back".

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python main.py     # http://127.0.0.1:8000/docs
pytest -q          # 55 passed
```

## Also in this repo

- **[NOTES.md](NOTES.md)** — every endpoint with curl examples, the validation rules, and the
  design decisions behind them
- **[docs/api-test-report.md](docs/api-test-report.md)** — the test report: manual Swagger runs
  with screenshots, 15 validation cases with their exact messages, and the three issues found
  while testing

---

Author: **Oussama Ezitouni**
