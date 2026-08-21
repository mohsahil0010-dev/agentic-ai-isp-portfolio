from scamshield.exporter import report_to_json, report_to_markdown
from scamshield.models import RiskLevel
from scamshield.workflow import analyze_message


SCAM = (
    "Congratulations! You won Rs. 500,000. Pay a processing fee of Rs. 2,500 through "
    "Easypaisa and send your OTP immediately. Claim now at http://bit.ly/free-prize."
)
LOW_RISK = "Reminder: Your university workshop begins Monday at 10 AM in Room 4. Contact the department office for questions."


def test_urgent_workflow_branch(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    report = analyze_message(SCAM)
    assert report.assessment.level is RiskLevel.CRITICAL
    assert len(report.agent_trace) == 7
    assert any(trace.agent == "Urgent Protection Agent" for trace in report.agent_trace)
    assert any(action.priority == "Immediate" for action in report.recommended_actions)


def test_balanced_workflow_branch(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    report = analyze_message(LOW_RISK)
    assert report.assessment.level is RiskLevel.LOW
    assert len(report.agent_trace) == 7
    assert any(trace.agent == "Balanced Verification Agent" for trace in report.agent_trace)
    assert "not proof" in report.assessment.verdict


def test_reported_exposure_adds_immediate_actions(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    report = analyze_message(SCAM, clicked_link=True, sent_money=True, shared_sensitive_info=True)
    actions = " ".join(item.action for item in report.recommended_actions)
    assert "bank or payment provider" in actions
    assert "Change the affected password" in actions
    assert "security scan" in actions


def test_exports_contain_evidence_and_trace(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    report = analyze_message(SCAM)
    markdown = report_to_markdown(report)
    json_text = report_to_json(report)
    assert "## Agent Decision Trace" in markdown
    assert "## Recommended Actions" in markdown
    assert '"score_breakdown"' in json_text

