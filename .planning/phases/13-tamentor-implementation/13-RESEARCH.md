# Phase 13: TAMentor Implementation - Research

**Researched:** 2026-02-28
**Domain:** LLM-based signal synthesis, Anthropic SDK integration, conflict resolution logic, Pydantic structured outputs
**Confidence:** HIGH

## Summary

Phase 13 implements TAMentor as an LLM-powered synthesis layer that combines three TASignal objects (weekly, daily, 4h) into a unified TAMentorSignal with explicit conflict resolution rules. Unlike the computational subagents (Phases 11-12), TAMentor uses Claude via Anthropic SDK to reason about multi-timeframe confluence and conflicts.

All dependencies are in place: TASignal and TAMentorSignal Pydantic models exist, Anthropic SDK 0.79.0 is installed, settings.MENTOR_MODEL is configured, and the three subagents produce valid TASignal outputs. The core work is replacing the existing BaseAgent-based TAMentor with a direct SDK implementation that enforces conflict resolution rules through LLM prompting and returns validated Pydantic output.

**Primary recommendation:** Implement TAMentor.synthesize() as a single Anthropic SDK call using client.messages.create() with structured conflict resolution rules in the prompt. Use the SDK's built-in retry logic for rate limits. Output must be parsed and validated against TAMentorSignal Pydantic model. All tests must mock the SDK call to avoid live API dependencies.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Location:**
- TAMentor at `src/backend/agents/ta_ensemble/ta_mentor.py`

**Architecture:**
- Receives three TASignal objects: weekly, daily, four_hour
- Makes single Anthropic SDK call using `settings.MENTOR_MODEL`
- Do NOT average scores — TAMentor reasons independently via LLM

**Conflict Resolution Rules (must be in LLM prompt):**
1. Weekly/Daily bearish + 4H bullish → output BEARISH, confidence -20, warning "4H counter-trend bounce in progress"
2. Weekly/Daily bullish + 4H bearish → output BULLISH, confidence -20, warning "4H pullback — potential better entry incoming"
3. Weekly vs Daily conflict → output NO_SIGNAL
4. 4H is entry timing only, never overrides Weekly or Daily direction

**Output Model:**
- Must be valid TAMentorSignal Pydantic model matching `src/backend/models/`
- Fields: direction, confidence, conflicts, warnings, reasoning, key_levels

**LLM Prompt Requirements:**
- Must include all three TASignal JSON objects
- Must include conflict resolution rules explicitly

**Testing:**
- Unit tests must mock the Anthropic SDK call
- No live API calls in tests

### Claude's Discretion

- Prompt engineering specifics for the TAMentor system prompt
- JSON serialization approach for TASignal objects
- Error handling for SDK failures
- Logging strategy

### Deferred Ideas (OUT OF SCOPE)

None — phase scope is well-defined.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| REQ-035 | TAMentor uses Anthropic SDK directly | Anthropic SDK 0.79 client.messages.create() pattern, bypasses BaseAgent framework |
| REQ-036 | Use MENTOR_MODEL from settings.py | Settings class already has MENTOR_MODEL field (defaults to claude-sonnet-4-20250514) |
| REQ-037 | Output TAMentorSignal Pydantic model | TAMentorSignal model exists with all required fields, model_validate() for parsing |
| REQ-038 | Conflict rule: Weekly/Daily > 4H direction | Higher timeframe priority enforced in system prompt instructions |
| REQ-039 | Conflict rule: -20 confidence penalty on TF conflict | Explicit penalty calculation in prompt, reflected in confidence_adjustment.conflict_penalty |
| REQ-040 | Conflict rule: NO SIGNAL on Weekly vs Daily conflict | System prompt must return neutral bias when W/D disagree, recommended_action="wait" |
| REQ-041 | 4H for entry timing only | System prompt instructs 4H used for entry_timing field, never overrides W/D direction |
| REQ-042 | Surface conflict warnings in synthesis_notes | ConflictDetail objects added to conflicts_detected list, warnings in synthesis_notes string |
| REQ-049 | Unit tests for TAMentor | Mock client.messages.create() return value, verify TAMentorSignal validation |
| REQ-050 | Test TAMentor conflict scenarios | 3 test cases: W/D bearish + 4H bullish, W/D bullish + 4H bearish, W vs D conflict |
| REQ-051 | All existing 28 tests still pass | No changes to existing models or functions, backward compatible |

</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| anthropic | 0.79.0+ | Anthropic SDK for Claude API | Official Python SDK, already installed, supports structured outputs |
| Pydantic | 2.5.0+ | TAMentorSignal validation, nested models | Industry standard, already used throughout project |
| pytest | 7.4.0+ | Unit testing framework | Already used for 28+ existing tests |
| unittest.mock | Built-in | Mocking Anthropic SDK calls | Python standard library, no external deps, test isolation |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| logging | Built-in | Error logging for SDK failures | Standard Python logging, already configured |
| json | Built-in | Serializing TASignal objects for prompt | Built-in JSON encoder, works with Pydantic .model_dump() |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Direct SDK | BaseAgent class | BaseAgent adds overhead, TAMentor needs custom conflict logic that doesn't fit base pattern |
| unittest.mock | pytest-mockllm | pytest-mockllm adds LLM-specific features (token counting, chaos testing) but unnecessary for simple mocking |
| Manual JSON parsing | client.messages.parse() | .parse() is beta feature requiring structured-outputs header, manual parsing more stable for production |

**Installation:**

All dependencies already present:
```bash
# Already installed in requirements.txt:
anthropic>=0.18.0  # (actually 0.79.0 installed)
pydantic>=2.5.0
pytest>=7.4.0
```

## Architecture Patterns

### Recommended Project Structure

Current structure (Phase 13 completes it):
```
src/backend/
├── models/
│   ├── ta_signal.py           # TASignal (extended in Phase 11)
│   └── ta_mentor_signal.py    # TAMentorSignal (already complete)
├── agents/
│   └── ta_ensemble/
│       ├── weekly_subagent.py     # Complete (Phase 11)
│       ├── daily_subagent.py      # Complete (Phase 12)
│       ├── four_hour_subagent.py  # Complete (Phase 12)
│       └── ta_mentor.py           # REIMPLEMENT THIS
└── tests/
    ├── test_weekly_subagent.py    # 16 tests (Phase 11)
    ├── test_daily_subagent.py     # 16 tests (Phase 12)
    ├── test_fourhour_subagent.py  # 16 tests (Phase 12)
    └── test_ta_mentor.py          # EXTEND THIS (2 tests exist)
```

### Pattern 1: Direct Anthropic SDK Call (Not BaseAgent)

**What:** Call Anthropic SDK directly instead of inheriting from BaseAgent

**When to use:** TAMentor needs custom conflict resolution logic that doesn't fit the BaseAgent pattern

**Example:**
```python
# Source: Based on Anthropic SDK 0.79 documentation
from anthropic import Anthropic
from src.backend.config.settings import settings

class TAMentor:
    """Synthesizes multi-timeframe signals with conflict resolution."""

    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.MENTOR_MODEL

    def synthesize(self, weekly: TASignal, daily: TASignal, four_hour: TASignal) -> TAMentorSignal:
        """Synthesize three TASignal objects into unified TAMentorSignal."""
        prompt = self._build_prompt(weekly, daily, four_hour)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2500,
            system=self._get_system_prompt(),
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response and validate against Pydantic model
        response_text = response.content[0].text
        result_dict = self._parse_json_response(response_text)
        return TAMentorSignal.model_validate(result_dict)
```

### Pattern 2: Conflict Resolution in System Prompt

**What:** Embed conflict resolution rules directly in system prompt to ensure LLM enforces them

**When to use:** When rules are critical business logic that cannot be bypassed

**Example:**
```python
# System prompt must include explicit conflict rules
SYSTEM_PROMPT = """You are TAMentor, synthesizing multi-timeframe technical analysis.

CONFLICT RESOLUTION RULES (MANDATORY):
1. If Weekly AND Daily are BEARISH but 4H is BULLISH:
   - Output direction: BEARISH
   - Reduce confidence by 20 points
   - Add warning: "4H counter-trend bounce in progress"

2. If Weekly AND Daily are BULLISH but 4H is BEARISH:
   - Output direction: BULLISH
   - Reduce confidence by 20 points
   - Add warning: "4H pullback — potential better entry incoming"

3. If Weekly CONFLICTS with Daily direction:
   - Output bias: "neutral"
   - recommended_action: "wait"
   - Add conflict: "Weekly and Daily timeframes in conflict — genuine uncertainty"

4. 4H timeframe is for ENTRY TIMING ONLY:
   - Use 4H to set entry_timing: "immediate" | "wait_for_pullback" | "wait_for_confirmation"
   - NEVER let 4H override Weekly or Daily direction

Output ONLY valid JSON matching TAMentorSignal schema."""
```

### Pattern 3: Mocking Anthropic SDK in Tests

**What:** Mock client.messages.create() to return synthetic responses

**When to use:** All unit tests to avoid live API calls

**Example:**
```python
# Source: pytest + unittest.mock best practices
from unittest.mock import Mock, patch
import pytest

@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.content = [Mock(text='{"symbol": "BTC", ...}')]
    mock_client.messages.create.return_value = mock_response
    return mock_client

def test_ta_mentor_conflict_scenario_1(mock_anthropic_client):
    """Test Weekly/Daily bearish + 4H bullish conflict."""
    with patch('src.backend.agents.ta_ensemble.ta_mentor.Anthropic', return_value=mock_anthropic_client):
        mentor = TAMentor()
        result = mentor.synthesize(weekly_bearish, daily_bearish, four_hour_bullish)

    # Verify conflict resolution applied
    assert result.unified_signal.bias == "bearish"
    assert result.confidence_adjustment.conflict_penalty == 20
    assert "4H counter-trend bounce" in result.synthesis_notes
```

### Pattern 4: JSON Serialization of TASignal for Prompt

**What:** Convert TASignal Pydantic models to JSON for LLM prompt

**When to use:** Passing structured data to LLM

**Example:**
```python
def _build_prompt(self, weekly: TASignal, daily: TASignal, four_hour: TASignal) -> str:
    """Build synthesis prompt with all three timeframe signals."""
    # Use model_dump() to convert Pydantic to dict, then json.dumps()
    import json

    return f"""Synthesize multi-timeframe TA analysis.

WEEKLY SIGNAL:
{json.dumps(weekly.model_dump(), indent=2)}

DAILY SIGNAL:
{json.dumps(daily.model_dump(), indent=2)}

4-HOUR SIGNAL:
{json.dumps(four_hour.model_dump(), indent=2)}

Apply conflict resolution rules and output TAMentorSignal JSON."""
```

### Anti-Patterns to Avoid

- **Averaging confidence scores:** TAMentor must reason independently, not mathematically combine scores
- **Inheriting from BaseAgent:** TAMentor needs custom logic that doesn't fit base pattern
- **Allowing 4H to override direction:** 4H is entry timing only, conflict rules enforce this
- **Skipping Pydantic validation:** Always validate response against TAMentorSignal model

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM retry logic | Custom retry with sleep() | Anthropic SDK built-in retry | SDK automatically retries 429 rate limits with exponential backoff (2 retries default) |
| JSON parsing from LLM | Complex regex extraction | json.loads() + error handling | LLM outputs clean JSON when instructed, simple parsing sufficient |
| Response validation | Manual field checking | Pydantic model_validate() | Pydantic validates types, constraints, nested models automatically |
| API key management | Hardcoded keys | settings.MENTOR_MODEL, settings.ANTHROPIC_API_KEY | Centralized config, already implemented |
| Mock LLM responses | Complex fixtures | unittest.mock.Mock() | Simple mocking sufficient for unit tests, no need for pytest-mockllm |

**Key insight:** Anthropic SDK 0.79 provides robust built-in error handling and retry logic. Don't reimplement — use SDK defaults for rate limits, connection errors, and transient failures.

## Common Pitfalls

### Pitfall 1: Not Enforcing Conflict Rules in Prompt

**What goes wrong:** LLM may ignore or misinterpret conflict resolution rules if they're not explicit

**Why it happens:** LLMs follow instructions literally — vague rules lead to inconsistent behavior

**How to avoid:** Include ALL four conflict rules verbatim in system prompt with explicit examples

**Warning signs:** Tests pass but production outputs don't apply -20 penalty or return NO_SIGNAL correctly

### Pitfall 2: Forgetting to Mock SDK in Tests

**What goes wrong:** Tests make live API calls, slow test suite, costs money, fails without internet

**Why it happens:** Forgetting to patch Anthropic client before instantiating TAMentor

**How to avoid:** Always use `@patch('src.backend.agents.ta_ensemble.ta_mentor.Anthropic')` or fixture

**Warning signs:** Tests take >1 second each, ANTHROPIC_API_KEY errors, usage charges on API account

### Pitfall 3: Allowing 4H to Override Direction

**What goes wrong:** 4H bullish signal overrides Weekly/Daily bearish, violating higher-timeframe-wins rule

**Why it happens:** Prompt doesn't emphasize "4H for entry timing ONLY" strongly enough

**How to avoid:** System prompt must state: "4H timeframe is for ENTRY TIMING ONLY. NEVER let 4H override Weekly or Daily direction."

**Warning signs:** Test for conflict scenario 1 fails — output shows bullish instead of bearish

### Pitfall 4: Not Validating Against TAMentorSignal Model

**What goes wrong:** Invalid JSON passes through, runtime errors downstream

**Why it happens:** Skipping Pydantic validation step after parsing LLM response

**How to avoid:** Always call `TAMentorSignal.model_validate(result_dict)` before returning

**Warning signs:** Tests pass with mock data but production throws validation errors

### Pitfall 5: Using client.messages.parse() Beta Feature

**What goes wrong:** Beta structured outputs API may change, requires anthropic-beta header, less stable

**Why it happens:** Temptation to use newest SDK features for "guaranteed schema compliance"

**How to avoid:** Use standard client.messages.create() + manual JSON parsing + Pydantic validation

**Warning signs:** Code depends on anthropic-beta: structured-outputs-2025-11-13 header

## Code Examples

Verified patterns from Anthropic SDK 0.79 and existing codebase:

### Example 1: TAMentor Initialization

```python
# Source: Anthropic SDK 0.79 + existing settings.py pattern
from anthropic import Anthropic
from src.backend.config.settings import settings

class TAMentor:
    """Synthesizes multi-timeframe signals with conflict resolution."""

    def __init__(self):
        """Initialize TAMentor with Anthropic client."""
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.MENTOR_MODEL
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build system prompt with conflict resolution rules."""
        return """You are TAMentor, synthesizing multi-timeframe technical analysis.

CONFLICT RESOLUTION RULES (MANDATORY):
[... full rules here ...]

Output ONLY valid JSON matching TAMentorSignal schema."""
```

### Example 2: Synthesize Method with SDK Call

```python
# Source: Anthropic SDK messages.create() pattern
import json
from src.backend.models.ta_signal import TASignal
from src.backend.models.ta_mentor_signal import TAMentorSignal

def synthesize(self, weekly: TASignal, daily: TASignal, four_hour: TASignal) -> TAMentorSignal:
    """Synthesize three TASignal objects into unified TAMentorSignal.

    Args:
        weekly: Weekly timeframe TASignal
        daily: Daily timeframe TASignal
        four_hour: 4-hour timeframe TASignal

    Returns:
        TAMentorSignal with conflict resolution applied
    """
    # Build prompt with all three signals
    prompt = f"""Synthesize multi-timeframe TA analysis for {weekly.symbol}.

WEEKLY SIGNAL:
{json.dumps(weekly.model_dump(), indent=2)}

DAILY SIGNAL:
{json.dumps(daily.model_dump(), indent=2)}

4-HOUR SIGNAL:
{json.dumps(four_hour.model_dump(), indent=2)}

Apply conflict resolution rules and output TAMentorSignal JSON."""

    # Call Anthropic SDK
    response = self.client.messages.create(
        model=self.model,
        max_tokens=2500,
        system=self.system_prompt,
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse and validate response
    response_text = response.content[0].text
    result_dict = self._parse_json_response(response_text)
    return TAMentorSignal.model_validate(result_dict)
```

### Example 3: JSON Parsing from LLM Response

```python
# Source: Existing base.py pattern + error handling
import json
import logging

logger = logging.getLogger(__name__)

def _parse_json_response(self, response: str) -> dict:
    """Extract JSON from Claude's response.

    Args:
        response: Raw text response from Claude

    Returns:
        Parsed JSON as dict

    Raises:
        ValueError: If JSON cannot be parsed
    """
    try:
        # Look for ```json blocks
        if "```json" in response:
            start = response.index("```json") + 7
            end = response.index("```", start)
            return json.loads(response[start:end].strip())

        # Try parsing whole response as JSON
        return json.loads(response)

    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse JSON from LLM response: {e}")
        logger.error(f"Response text: {response}")
        raise ValueError(f"Invalid JSON in LLM response: {e}")
```

### Example 4: Test with Mocked Anthropic Client

```python
# Source: pytest + unittest.mock best practices
from unittest.mock import Mock, patch
import pytest
import json

from src.backend.agents.ta_ensemble.ta_mentor import TAMentor
from src.backend.models.ta_mentor_signal import TAMentorSignal

@pytest.fixture
def ta_mentor_conflict_response():
    """Mock TAMentorSignal response for conflict scenario."""
    return {
        "symbol": "BTC",
        "timeframe_alignment": {
            "weekly_bias": "bearish",
            "daily_bias": "bearish",
            "fourhour_bias": "bullish",
            "alignment_score": 40,
            "confluence": "conflicting"
        },
        "conflicts_detected": [
            {
                "type": "trend",
                "description": "4H shows bullish while W/D bearish",
                "severity": "medium"
            }
        ],
        "confidence_adjustment": {
            "base_confidence": 70,
            "confluence_bonus": 0,
            "conflict_penalty": 20,
            "final_confidence": 50,
            "reasoning": "4H counter-trend reduces confidence"
        },
        "unified_signal": {
            "bias": "bearish",
            "strength": "moderate",
            "confidence": 50,
            "recommended_action": "short",
            "entry_timing": "wait_for_pullback",
            "key_levels": {
                "support": 60000.0,
                "resistance": 70000.0,
                "invalidation": 72000.0
            }
        },
        "synthesis_notes": "4H counter-trend bounce in progress. Weekly and Daily bearish structure intact."
    }

def test_conflict_scenario_1_weekly_daily_bearish_4h_bullish(
    weekly_bearish_signal,
    daily_bearish_signal,
    four_hour_bullish_signal,
    ta_mentor_conflict_response
):
    """Test conflict rule: W/D bearish + 4H bullish → BEARISH, -20 confidence."""
    # Mock Anthropic client
    mock_client = Mock()
    mock_response = Mock()
    mock_response.content = [Mock(text=json.dumps(ta_mentor_conflict_response))]
    mock_client.messages.create.return_value = mock_response

    # Patch Anthropic constructor to return mock client
    with patch('src.backend.agents.ta_ensemble.ta_mentor.Anthropic', return_value=mock_client):
        mentor = TAMentor()
        result = mentor.synthesize(
            weekly_bearish_signal,
            daily_bearish_signal,
            four_hour_bullish_signal
        )

    # Verify result is valid TAMentorSignal
    assert isinstance(result, TAMentorSignal)

    # Verify conflict resolution rules applied
    assert result.unified_signal.bias == "bearish"  # W/D direction wins
    assert result.confidence_adjustment.conflict_penalty == 20  # -20 penalty
    assert "4H counter-trend bounce" in result.synthesis_notes  # Warning surfaced
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| BaseAgent inheritance | Direct SDK call | Phase 13 (2026-02) | TAMentor needs custom logic incompatible with BaseAgent pattern |
| Manual retry logic | SDK built-in retry | Anthropic SDK 0.79 (2026-02) | Automatic exponential backoff for 429 rate limits, connection errors |
| client.messages.parse() beta | Standard create() + manual parsing | Phase 13 (2026-02) | More stable than beta structured outputs API |
| Mock with pytest-mockllm | unittest.mock.Mock() | Phase 13 (2026-02) | Simple mocking sufficient for TAMentor, no need for LLM-specific features |

**Deprecated/outdated:**
- BaseAgent._call_claude() method: TAMentor bypasses base class for custom conflict logic
- anthropic-beta: structured-outputs header: Beta feature, manual parsing more stable for production

## Open Questions

1. **Max tokens for synthesis?**
   - What we know: Current TAMentor uses max_tokens=2500 in existing code
   - What's unclear: Whether this is sufficient for detailed conflict explanations
   - Recommendation: Start with 2500, monitor if responses get truncated, increase to 3000 if needed

2. **Should we log the full LLM prompt for debugging?**
   - What we know: Useful for troubleshooting conflict resolution logic
   - What's unclear: Whether to log at DEBUG or INFO level, PII concerns with logging signals
   - Recommendation: Log at DEBUG level only, sanitize before production deployment

3. **Handling SDK errors in production?**
   - What we know: SDK retries 429 rate limits automatically (2 retries, exponential backoff)
   - What's unclear: What to return if all retries fail — should TAMentor raise exception or return neutral signal?
   - Recommendation: Raise exception on SDK failure, let caller handle retry policy at orchestration level

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 7.4.0+ |
| Config file | pytest.ini (already exists) |
| Quick run command | `pytest src/backend/tests/test_ta_mentor.py -v` |
| Full suite command | `pytest src/backend/tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-035 | TAMentor uses Anthropic SDK directly | unit | `pytest src/backend/tests/test_ta_mentor.py::test_ta_mentor_uses_anthropic_sdk -xvs` | ✅ Extend existing |
| REQ-036 | Use MENTOR_MODEL from settings.py | unit | `pytest src/backend/tests/test_ta_mentor.py::test_ta_mentor_uses_mentor_model -xvs` | ❌ Wave 0 |
| REQ-037 | Output TAMentorSignal Pydantic model | unit | `pytest src/backend/tests/test_ta_mentor.py::test_ta_mentor_returns_valid_signal -xvs` | ✅ Extend existing |
| REQ-038 | Weekly/Daily > 4H direction | unit | `pytest src/backend/tests/test_ta_mentor.py::test_higher_timeframe_wins -xvs` | ❌ Wave 0 |
| REQ-039 | -20 confidence penalty on conflict | unit | `pytest src/backend/tests/test_ta_mentor.py::test_conflict_penalty_applied -xvs` | ❌ Wave 0 |
| REQ-040 | NO SIGNAL on W vs D conflict | unit | `pytest src/backend/tests/test_ta_mentor.py::test_weekly_daily_conflict_no_signal -xvs` | ❌ Wave 0 |
| REQ-041 | 4H for entry timing only | unit | `pytest src/backend/tests/test_ta_mentor.py::test_4h_entry_timing_only -xvs` | ❌ Wave 0 |
| REQ-042 | Warnings in synthesis_notes | unit | `pytest src/backend/tests/test_ta_mentor.py::test_conflict_warnings_surfaced -xvs` | ❌ Wave 0 |
| REQ-049 | TAMentor unit tests with mocked SDK | unit | `pytest src/backend/tests/test_ta_mentor.py -xvs` | ✅ Extend existing |
| REQ-050 | Test 3 conflict scenarios | unit | `pytest src/backend/tests/test_ta_mentor.py -k conflict -xvs` | ❌ Wave 0 |
| REQ-051 | All 28 existing tests pass | regression | `pytest src/backend/tests/ -v` | ✅ Existing |

### Sampling Rate

- **Per task commit:** `pytest src/backend/tests/test_ta_mentor.py -xvs`
- **Per wave merge:** `pytest src/backend/tests/ -v`
- **Phase gate:** All 28+ tests green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `test_ta_mentor.py` — Add 5 new test cases for conflict scenarios (REQ-038, REQ-039, REQ-040, REQ-041, REQ-042)
- [ ] `test_ta_mentor.py` — Add test for settings.MENTOR_MODEL usage (REQ-036)
- [ ] `conftest.py` — Add fixtures for conflict scenario signals (weekly_bearish, daily_bearish, four_hour_bullish, etc.)

## Sources

### Primary (HIGH confidence)

- Anthropic Python SDK 0.79.0 documentation - Messages API, client.messages.create() pattern
- [GitHub - anthropics/anthropic-sdk-python](https://github.com/anthropics/anthropic-sdk-python) - Official SDK repository
- Existing codebase: `src/backend/agents/base.py` - BaseAgent pattern (to be bypassed)
- Existing codebase: `src/backend/config/settings.py` - MENTOR_MODEL configuration
- Existing codebase: `src/backend/models/ta_mentor_signal.py` - TAMentorSignal Pydantic model
- Existing codebase: `src/backend/tests/test_ta_mentor.py` - Current test structure

### Secondary (MEDIUM confidence)

- [Structured outputs - Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) - Structured output capabilities (NOT using beta feature)
- [How to Fix Claude API 429 Rate Limit Error: Complete Guide 2026](https://www.aifreeapi.com/en/posts/claude-api-429-error-fix) - Rate limit handling, exponential backoff
- [Request Lifecycle and Error Handling | anthropic-sdk-python](https://deepwiki.com/anthropics/anthropic-sdk-python/4.5-request-lifecycle-and-error-handling) - SDK retry logic (2 retries default)
- [pytest-mock Tutorial: A Beginner's Guide to Mocking in Python](https://www.datacamp.com/tutorial/pytest-mock) - Mocking best practices

### Tertiary (LOW confidence)

- [pytest-mockllm v0.2.1](https://www.dhirajdas.dev/blog/pytest-mockllm-true-fidelity) - LLM-specific testing tool (NOT using — unittest.mock sufficient)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Anthropic SDK 0.79.0 verified installed, TAMentorSignal model exists
- Architecture: HIGH - Pattern based on existing BaseAgent but simplified for direct SDK call
- Pitfalls: HIGH - Conflict resolution rules are critical, must be enforced in prompt
- Testing: HIGH - Mock pattern proven in existing test_ta_mentor.py

**Research date:** 2026-02-28
**Valid until:** 2026-03-30 (30 days - stable APIs, Anthropic SDK mature)
