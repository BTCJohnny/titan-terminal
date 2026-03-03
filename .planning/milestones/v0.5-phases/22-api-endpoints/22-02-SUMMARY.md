---
phase: 22-api-endpoints
plan: "02"
subsystem: api
tags: [fastapi, chat, anthropic-sdk, signal-context, testing]
dependency_graph:
  requires:
    - 22-01  # API endpoint stubs, ChatRequest/ChatResponse models, get_recent_signals in main.py
  provides:
    - working /chat endpoint calling Anthropic SDK with live signal context
    - 5 chat endpoint tests covering SDK usage, model name, signal context, empty state, and request format
  affects:
    - src/backend/api/main.py
    - src/backend/tests/test_api_endpoints.py
tech_stack:
  added:
    - anthropic SDK (direct client usage via anthropic.Anthropic)
  patterns:
    - Lazy-loaded singleton pattern for Anthropic client (mirrors orchestrator pattern)
    - Signal context builder fetching recent journal entries to ground LLM answers
    - settings.MODEL_NAME (not MENTOR_MODEL) for conversational assistant model
    - Mock patch via _MODULE_PATH for test namespace compatibility (inherited from Plan 01)
key_files:
  created: []
  modified:
    - src/backend/api/main.py
    - src/backend/tests/test_api_endpoints.py
decisions:
  - ChatRequest uses 'question' field (not 'message') per CONTEXT.md locked decision
  - settings.MODEL_NAME used for /chat (not MENTOR_MODEL — that is for Orchestrator Mentor agent)
  - Signal context built from signal_journal via get_recent_signals(limit=10), top 5 shown
  - "No recent analysis data" fallback when journal is empty — endpoint always returns 200
  - Anthropic client initialized lazily at first request (not at module import)
metrics:
  duration: "~8 minutes"
  completed: "2026-03-01"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 2
  tests_added: 5
---

# Phase 22 Plan 02: /chat Endpoint with Anthropic SDK and Signal Context Summary

Implemented POST /chat endpoint using the Anthropic SDK directly with recent signal journal data as grounding context, replacing the old orchestrator.chat() delegation stub.

## What Was Built

### Task 1: /chat Endpoint with Anthropic SDK

**`src/backend/api/main.py`** — Four targeted changes:

1. **Added imports:** `import anthropic` at top, `from ..config.settings import settings` added to imports.

2. **Updated ChatRequest model:** Changed `message: str` field to `question: str` (and removed `context: Optional[dict]`) per CONTEXT.md locked decision. Old stub used `message`; CONTEXT.md specifies `{"question": "..."}`.

3. **Added Anthropic client infrastructure:**
   - `_chat_client = None` module-level lazy singleton
   - `get_chat_client() -> anthropic.Anthropic` initializes with `settings.ANTHROPIC_API_KEY`
   - `_build_chat_context() -> str` fetches up to 10 recent signals from `signal_journal` via `get_recent_signals()`, formats top 5 into a markdown signal summary for the system prompt. Returns "No recent analysis data available. Suggest running /morning-report first." when journal is empty.

4. **Rewrote /chat endpoint:**
   - Calls `get_chat_client()` and `_build_chat_context()`
   - Builds system prompt combining trading assistant persona with live signal data
   - Calls `client.messages.create(model=settings.MODEL_NAME, max_tokens=1000, temperature=0.3, ...)`
   - Returns `ChatResponse(response=answer, timestamp=datetime.now().isoformat())`

### Task 2: /chat Tests

**`src/backend/tests/test_api_endpoints.py`** — 5 new tests:

- `test_chat_returns_200` — POSTs `{"question": "What looks good?"}`, mocks `get_chat_client` and `get_recent_signals`, asserts 200 with `response` and `timestamp` fields and correct text.
- `test_chat_uses_model_name` — Verifies `messages.create` is called with `model=settings.MODEL_NAME` (not `settings.MENTOR_MODEL`).
- `test_chat_includes_signal_context` — Mocks `get_recent_signals` to return a BTC signal with confidence=85, verifies "BTC" and "85" appear in the `system` argument to `messages.create`.
- `test_chat_handles_empty_signals` — Mocks empty signal list, confirms 200 returned and system prompt contains "No recent analysis data".
- `test_chat_request_format` — Confirms `{"question": "..."}` returns 200, `{"message": "..."}` returns 422 (Pydantic validation error).

All 13 tests pass: 8 from Plan 01 + 5 new.

## Deviations from Plan

None - plan executed exactly as written.

The plan specified a `_build_chat_context()` function that imports `get_recent_signals` from `..db` inside the function body. Since `get_recent_signals` was already imported at the top of `main.py` (from Plan 01's existing import line), the function uses the module-level import directly rather than a local import — same result, cleaner code.

## Verification Results

```
$ python -m pytest src/backend/tests/test_api_endpoints.py -x -v
13 passed in 1.39s

$ python -c "from src.backend.api.main import app, ChatRequest; print('Chat endpoint imports OK')"
Chat endpoint imports OK

$ grep -c "anthropic.Anthropic|messages.create" src/backend/api/main.py
3

$ grep "MODEL_NAME" src/backend/api/main.py
    Uses Anthropic SDK (settings.MODEL_NAME) to generate answers
            model=settings.MODEL_NAME,

$ grep -c "question" src/backend/api/main.py
3
```

## Self-Check

- [x] `src/backend/api/main.py` — FOUND
- [x] `src/backend/tests/test_api_endpoints.py` — FOUND
- [x] Commit cde2fe1 — FOUND (feat(22-02): implement /chat endpoint with Anthropic SDK)
- [x] Commit 40a74e8 — FOUND (test(22-02): add /chat endpoint tests)
- [x] 13/13 tests pass
- [x] `anthropic.Anthropic` and `messages.create` present in main.py (3 matches)
- [x] `settings.MODEL_NAME` used in chat endpoint
- [x] `question` field in ChatRequest (3 matches — model, docstring, endpoint body)

## Self-Check: PASSED
