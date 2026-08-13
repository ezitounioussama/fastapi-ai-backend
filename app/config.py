"""Application settings kept in one place."""

APP_NAME = "AI Study Assistant API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = """
A small learning-focused backend with four endpoints.

The AI-facing endpoints (`/chat`, `/quiz`, `/summarise`) currently run on
**placeholder logic** — deterministic Python, no model calls. The request and
response shapes are the finished contract, so swapping in a real model later
means changing only `app/services.py`.
"""

# Limits used by the request models, gathered here so the API and its
# documentation cannot drift apart.
CHAT_MESSAGE_MIN = 1
CHAT_MESSAGE_MAX = 2000

QUIZ_TOPIC_MIN = 2
QUIZ_TOPIC_MAX = 100
QUIZ_QUESTIONS_MIN = 1
QUIZ_QUESTIONS_MAX = 10
QUIZ_QUESTIONS_DEFAULT = 5

SUMMARY_TEXT_MIN = 20
SUMMARY_TEXT_MAX = 10000
SUMMARY_BULLETS_MIN = 1
SUMMARY_BULLETS_MAX = 10
SUMMARY_BULLETS_DEFAULT = 3
