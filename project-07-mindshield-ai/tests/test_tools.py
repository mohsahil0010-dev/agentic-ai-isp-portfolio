import sys
from types import SimpleNamespace

from scamshield.llm import answer_general_chat, model_candidates, safe_calculate
from scamshield.models import CaseInput, RiskLevel
from scamshield.tools import (
    detect_indicators,
    extract_entities,
    inspect_url,
    retrieve_patterns,
    score_risk,
)


SCAM = (
    "Congratulations! You won Rs. 500,000. Pay a processing fee of Rs. 2,500 through "
    "Easypaisa and send your OTP immediately. Claim now at http://bit.ly/free-prize."
)


def test_extracts_security_relevant_entities():
    entities = extract_entities(SCAM)
    types = {item.entity_type for item in entities}
    assert {"URL", "Amount", "Payment service", "Credential request"}.issubset(types)


def test_shortened_http_link_receives_structural_points():
    result = inspect_url("http://bit.ly/free-prize")
    assert result.hostname == "bit.ly"
    assert result.risk_points >= 20
    assert any("shortening" in finding for finding in result.findings)


def test_indicators_and_patterns_match_prize_scam():
    inspection = inspect_url("http://bit.ly/free-prize")
    indicators = detect_indicators(SCAM, [inspection])
    categories = {item.category for item in indicators}
    assert "Sensitive secret request" in categories
    assert "Advance payment" in categories
    patterns = retrieve_patterns(SCAM, indicators)
    assert patterns[0].pattern_id in {"advance-fee-prize", "otp-account-takeover"}


def test_high_risk_score_for_prize_otp_scam():
    case = CaseInput(content=SCAM)
    inspection = inspect_url("http://bit.ly/free-prize")
    indicators = detect_indicators(SCAM, [inspection])
    patterns = retrieve_patterns(SCAM, indicators)
    assessment = score_risk(case, indicators, [inspection], patterns)
    assert assessment.score >= 80
    assert assessment.level is RiskLevel.CRITICAL


def test_low_risk_text_is_not_declared_legitimate():
    content = "Reminder: Your university workshop begins Monday at 10 AM in Room 4. Please bring your student card."
    case = CaseInput(content=content)
    assessment = score_risk(case, [], [], [])
    assert assessment.level is RiskLevel.LOW
    assert "not proof" in assessment.verdict


def test_safe_calculator_and_chat_route(monkeypatch):
    assert safe_calculate("(12500 * 0.10) + 12500") == 13750
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    result = answer_general_chat([{"role": "user", "content": "Calculate 20 * 5 + 10"}])
    assert result.route == "calculator"
    assert "110" in result.answer


def test_general_chat_explains_missing_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    result = answer_general_chat([{"role": "user", "content": "Explain artificial intelligence to me."}])
    assert result.route == "configuration_help"
    assert "GROQ_API_KEY" in result.answer


def test_chat_falls_back_from_unavailable_configured_model(monkeypatch):
    calls = []

    class UnavailableModel(Exception):
        status_code = 404

    class Completions:
        def create(self, model, **kwargs):
            calls.append(model)
            if model == "old-model":
                raise UnavailableModel("model decommissioned")
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="Fallback model answered."))]
            )

    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=Completions()))
    fake_groq = SimpleNamespace(Groq=lambda **kwargs: fake_client)
    monkeypatch.setitem(sys.modules, "groq", fake_groq)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("MINDSHIELD_MODEL", "old-model")

    result = answer_general_chat([{"role": "user", "content": "Explain AI agents."}])

    assert calls == ["old-model", "openai/gpt-oss-20b"]
    assert result.model == "openai/gpt-oss-20b"
    assert result.answer == "Fallback model answered."


def test_default_models_are_current_production_choices(monkeypatch):
    monkeypatch.delenv("MINDSHIELD_MODEL", raising=False)
    assert model_candidates() == ["openai/gpt-oss-20b", "openai/gpt-oss-120b"]
