"""Comprehensive test suite for TAMentor agent."""
import json
import pytest
from unittest.mock import Mock, patch

from src.backend.agents.ta_ensemble import TAMentor
from src.backend.models.ta_mentor_signal import TAMentorSignal
from src.backend.models.ta_signal import TASignal


# Mock response fixtures for each conflict scenario


@pytest.fixture
def conflict_scenario_1_response():
    """Mock response for W/D bearish + 4H bullish conflict."""
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
            {"type": "trend", "description": "4H counter-trend bounce", "severity": "medium"}
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
            "key_levels": {"support": 60000.0, "resistance": 70000.0, "invalidation": 72000.0}
        },
        "synthesis_notes": "4H counter-trend bounce in progress. Weekly and Daily bearish structure intact."
    }


@pytest.fixture
def conflict_scenario_2_response():
    """Mock response for W/D bullish + 4H bearish conflict."""
    return {
        "symbol": "BTC",
        "timeframe_alignment": {
            "weekly_bias": "bullish",
            "daily_bias": "bullish",
            "fourhour_bias": "bearish",
            "alignment_score": 40,
            "confluence": "conflicting"
        },
        "conflicts_detected": [
            {"type": "trend", "description": "4H pullback — potential better entry incoming", "severity": "medium"}
        ],
        "confidence_adjustment": {
            "base_confidence": 70,
            "confluence_bonus": 0,
            "conflict_penalty": 20,
            "final_confidence": 50,
            "reasoning": "4H pullback reduces confidence temporarily"
        },
        "unified_signal": {
            "bias": "bullish",
            "strength": "moderate",
            "confidence": 50,
            "recommended_action": "long",
            "entry_timing": "wait_for_pullback",
            "key_levels": {"support": 60000.0, "resistance": 70000.0, "invalidation": 58000.0}
        },
        "synthesis_notes": "4H pullback — potential better entry incoming. Weekly and Daily bullish structure intact."
    }


@pytest.fixture
def conflict_scenario_3_response():
    """Mock response for W vs D conflict."""
    return {
        "symbol": "BTC",
        "timeframe_alignment": {
            "weekly_bias": "bullish",
            "daily_bias": "bearish",
            "fourhour_bias": "neutral",
            "alignment_score": 20,
            "confluence": "conflicting"
        },
        "conflicts_detected": [
            {"type": "trend", "description": "Weekly and Daily timeframes in conflict — genuine uncertainty", "severity": "high"}
        ],
        "confidence_adjustment": {
            "base_confidence": 50,
            "confluence_bonus": 0,
            "conflict_penalty": 30,
            "final_confidence": 20,
            "reasoning": "Major timeframe conflict creates uncertainty"
        },
        "unified_signal": {
            "bias": "neutral",
            "strength": "weak",
            "confidence": 20,
            "recommended_action": "wait",
            "entry_timing": "wait_for_confirmation",
            "key_levels": {"support": 60000.0, "resistance": 70000.0, "invalidation": None}
        },
        "synthesis_notes": "Weekly and Daily timeframes in conflict — genuine uncertainty. Wait for resolution."
    }


@pytest.fixture
def aligned_response():
    """Mock response for aligned timeframes (no conflict)."""
    return {
        "symbol": "BTC",
        "timeframe_alignment": {
            "weekly_bias": "bullish",
            "daily_bias": "bullish",
            "fourhour_bias": "bullish",
            "alignment_score": 100,
            "confluence": "perfect"
        },
        "conflicts_detected": [],
        "confidence_adjustment": {
            "base_confidence": 70,
            "confluence_bonus": 20,
            "conflict_penalty": 0,
            "final_confidence": 90,
            "reasoning": "Perfect alignment across all timeframes"
        },
        "unified_signal": {
            "bias": "bullish",
            "strength": "strong",
            "confidence": 90,
            "recommended_action": "long",
            "entry_timing": "immediate",
            "key_levels": {"support": 60000.0, "resistance": 70000.0, "invalidation": 58000.0}
        },
        "synthesis_notes": "Perfect multi-timeframe alignment. High confidence bullish setup."
    }


# Test cases


class TestTAMentorConflictResolution:
    """Tests for TAMentor conflict resolution logic."""

    def test_conflict_scenario_1_weekly_daily_bearish_4h_bullish(
        self,
        weekly_bearish_signal,
        daily_bearish_signal,
        four_hour_bullish_signal,
        conflict_scenario_1_response
    ):
        """REQ-038, REQ-039: W/D bearish + 4H bullish -> BEARISH, -20 confidence."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps(conflict_scenario_1_response))]
        mock_client.messages.create.return_value = mock_response

        with patch('src.backend.agents.ta_ensemble.ta_mentor.Anthropic', return_value=mock_client):
            mentor = TAMentor()
            result = mentor.synthesize(weekly_bearish_signal, daily_bearish_signal, four_hour_bullish_signal)

        assert isinstance(result, TAMentorSignal)
        assert result.unified_signal.bias == "bearish"  # W/D wins
        assert result.confidence_adjustment.conflict_penalty == 20  # -20 penalty
        assert "4H counter-trend bounce" in result.synthesis_notes

    def test_conflict_scenario_2_weekly_daily_bullish_4h_bearish(
        self,
        weekly_bullish_signal,
        daily_bullish_signal,
        four_hour_bearish_signal,
        conflict_scenario_2_response
    ):
        """REQ-038, REQ-039: W/D bullish + 4H bearish -> BULLISH, -20 confidence."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps(conflict_scenario_2_response))]
        mock_client.messages.create.return_value = mock_response

        with patch('src.backend.agents.ta_ensemble.ta_mentor.Anthropic', return_value=mock_client):
            mentor = TAMentor()
            result = mentor.synthesize(weekly_bullish_signal, daily_bullish_signal, four_hour_bearish_signal)

        assert isinstance(result, TAMentorSignal)
        assert result.unified_signal.bias == "bullish"  # W/D wins
        assert result.confidence_adjustment.conflict_penalty == 20  # -20 penalty
        assert "4H pullback" in result.synthesis_notes

    def test_conflict_scenario_3_weekly_vs_daily_conflict(
        self,
        weekly_bullish_signal,
        daily_bearish_signal,
        four_hour_neutral_signal,
        conflict_scenario_3_response
    ):
        """REQ-040: Weekly vs Daily conflict -> NO SIGNAL (neutral, wait)."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps(conflict_scenario_3_response))]
        mock_client.messages.create.return_value = mock_response

        with patch('src.backend.agents.ta_ensemble.ta_mentor.Anthropic', return_value=mock_client):
            mentor = TAMentor()
            result = mentor.synthesize(weekly_bullish_signal, daily_bearish_signal, four_hour_neutral_signal)

        assert isinstance(result, TAMentorSignal)
        assert result.unified_signal.bias == "neutral"
        assert result.unified_signal.recommended_action == "wait"
        assert "Weekly and Daily timeframes in conflict" in result.synthesis_notes

    def test_4h_entry_timing_only(
        self,
        weekly_bullish_signal,
        daily_bullish_signal,
        four_hour_bearish_signal,
        conflict_scenario_2_response
    ):
        """REQ-041: 4H is for entry timing only, never overrides direction."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps(conflict_scenario_2_response))]
        mock_client.messages.create.return_value = mock_response

        with patch('src.backend.agents.ta_ensemble.ta_mentor.Anthropic', return_value=mock_client):
            mentor = TAMentor()
            result = mentor.synthesize(weekly_bullish_signal, daily_bullish_signal, four_hour_bearish_signal)

        # W/D direction wins (bullish), 4H only affects timing
        assert result.unified_signal.bias == "bullish"
        assert result.unified_signal.entry_timing in ["immediate", "wait_for_pullback", "wait_for_confirmation"]

    def test_conflict_warnings_surfaced(
        self,
        weekly_bearish_signal,
        daily_bearish_signal,
        four_hour_bullish_signal,
        conflict_scenario_1_response
    ):
        """REQ-042: Conflict warnings appear in synthesis_notes."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps(conflict_scenario_1_response))]
        mock_client.messages.create.return_value = mock_response

        with patch('src.backend.agents.ta_ensemble.ta_mentor.Anthropic', return_value=mock_client):
            mentor = TAMentor()
            result = mentor.synthesize(weekly_bearish_signal, daily_bearish_signal, four_hour_bullish_signal)

        assert len(result.synthesis_notes) > 0
        # Conflict warnings should mention 4H or counter-trend
        assert "4H" in result.synthesis_notes or "counter-trend" in result.synthesis_notes


class TestTAMentorSDKIntegration:
    """Tests for Anthropic SDK integration."""

    def test_ta_mentor_uses_anthropic_sdk(self):
        """REQ-035: TAMentor uses Anthropic SDK directly."""
        with patch('src.backend.agents.ta_ensemble.ta_mentor.Anthropic') as mock_anthropic:
            mentor = TAMentor()
            mock_anthropic.assert_called_once()  # Anthropic client instantiated

    def test_ta_mentor_uses_mentor_model(self):
        """REQ-036: TAMentor uses settings.MENTOR_MODEL."""
        with patch('src.backend.agents.ta_ensemble.ta_mentor.settings') as mock_settings:
            mock_settings.MENTOR_MODEL = "test-model-123"
            mock_settings.ANTHROPIC_API_KEY = "test-key"

            with patch('src.backend.agents.ta_ensemble.ta_mentor.Anthropic'):
                mentor = TAMentor()
                assert mentor.model == "test-model-123"


class TestTAMentorOutputValidation:
    """Tests for TAMentorSignal output validation."""

    def test_ta_mentor_returns_valid_signal(
        self,
        weekly_bullish_signal,
        daily_bullish_signal,
        four_hour_neutral_signal,
        aligned_response
    ):
        """REQ-037: Output is valid TAMentorSignal."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps(aligned_response))]
        mock_client.messages.create.return_value = mock_response

        with patch('src.backend.agents.ta_ensemble.ta_mentor.Anthropic', return_value=mock_client):
            mentor = TAMentor()
            result = mentor.synthesize(weekly_bullish_signal, daily_bullish_signal, four_hour_neutral_signal)

        assert isinstance(result, TAMentorSignal)
        assert 0 <= result.unified_signal.confidence <= 100
        assert result.unified_signal.recommended_action in ["long", "short", "wait"]

    def test_ta_mentor_validates_pydantic_model(
        self,
        weekly_bullish_signal,
        daily_bullish_signal,
        four_hour_neutral_signal
    ):
        """REQ-037: Invalid response raises validation error."""
        # Mock invalid response (missing required fields)
        invalid_response = {"symbol": "BTC"}

        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps(invalid_response))]
        mock_client.messages.create.return_value = mock_response

        with patch('src.backend.agents.ta_ensemble.ta_mentor.Anthropic', return_value=mock_client):
            mentor = TAMentor()
            with pytest.raises(Exception):  # Pydantic validation error
                mentor.synthesize(weekly_bullish_signal, daily_bullish_signal, four_hour_neutral_signal)


class TestTAMentorAlignedScenarios:
    """Tests for aligned (no conflict) scenarios."""

    def test_perfect_alignment_high_confidence(
        self,
        weekly_bullish_signal,
        daily_bullish_signal,
        four_hour_bullish_signal,
        aligned_response
    ):
        """Perfect alignment across all timeframes should yield high confidence."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps(aligned_response))]
        mock_client.messages.create.return_value = mock_response

        with patch('src.backend.agents.ta_ensemble.ta_mentor.Anthropic', return_value=mock_client):
            mentor = TAMentor()
            result = mentor.synthesize(weekly_bullish_signal, daily_bullish_signal, four_hour_bullish_signal)

        assert result.timeframe_alignment.confluence in ["perfect", "strong"]
        assert result.unified_signal.confidence >= 70
        assert result.confidence_adjustment.conflict_penalty == 0


class TestTAMentorBackwardCompatibility:
    """Tests for backward compatibility with analyze() wrapper."""

    def test_analyze_wrapper_accepts_dicts(self, aligned_response):
        """Verify analyze() wrapper converts dict inputs to TASignal."""
        context = {
            "weekly_analysis": {
                "symbol": "BTC",
                "timeframe": "weekly",
                "trend": {"direction": "bullish", "strength": "strong", "ema_alignment": "bullish"},
                "momentum": {"rsi": 65.0, "macd_bias": "bullish", "momentum_divergence": False},
                "key_levels": {"major_support": 60000.0, "major_resistance": 70000.0},
                "patterns": {"detected": [], "pattern_bias": "bullish"},
                "overall": {"bias": "bullish", "confidence": 75, "notes": "Weekly uptrend"}
            },
            "daily_analysis": {
                "symbol": "BTC",
                "timeframe": "daily",
                "trend": {"direction": "bullish", "strength": "moderate", "ema_alignment": "bullish"},
                "momentum": {"rsi": 60.0, "macd_bias": "bullish", "momentum_divergence": False},
                "key_levels": {"major_support": 62000.0, "major_resistance": 68000.0},
                "patterns": {"detected": [], "pattern_bias": "bullish"},
                "overall": {"bias": "bullish", "confidence": 70, "notes": "Daily uptrend"}
            },
            "fourhour_analysis": {
                "symbol": "BTC",
                "timeframe": "4h",
                "trend": {"direction": "sideways", "strength": "weak", "ema_alignment": "neutral"},
                "momentum": {"rsi": 50.0, "macd_bias": "neutral", "momentum_divergence": False},
                "key_levels": {"major_support": 63000.0, "major_resistance": 66000.0},
                "patterns": {"detected": [], "pattern_bias": "neutral"},
                "overall": {"bias": "neutral", "confidence": 50, "notes": "4H consolidation"}
            }
        }

        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps(aligned_response))]
        mock_client.messages.create.return_value = mock_response

        with patch('src.backend.agents.ta_ensemble.ta_mentor.Anthropic', return_value=mock_client):
            mentor = TAMentor()
            result = mentor.analyze("BTC", context)

        # Should return dict (not TAMentorSignal object)
        assert isinstance(result, dict)
        assert result["symbol"] == "BTC"
