"""Markdown and JSON report exporters."""

from __future__ import annotations

import json

from .models import AnalysisReport


def report_to_json(report: AnalysisReport) -> str:
    return json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False)


def report_to_markdown(report: AnalysisReport) -> str:
    a = report.assessment
    lines = [
        "# MindShield AI - Scam Risk Analysis",
        "",
        f"Generated: {report.generated_at:%d %B %Y, %H:%M UTC}",
        f"Detected source: {report.detected_source.value}",
        "",
        "## Verdict",
        "",
        f"**{a.level.value} - {a.score}/100 ({a.confidence} confidence)**",
        "",
        report.summary,
        "",
        "## Warning Indicators",
        "",
        "| Indicator | Severity | Evidence | Explanation |",
        "|---|---|---|---|",
    ]
    for item in report.indicators:
        lines.append(f"| {item.category} | {item.severity} | {item.evidence} | {item.explanation} |")
    if not report.indicators:
        lines.append("| No strong text-rule match | - | - | Independent verification is still required. |")
    lines.extend(["", "## Pattern Matches", ""])
    lines.extend(f"- **{item.name} ({item.similarity:.0%})** - {item.explanation}" for item in report.pattern_matches)
    if not report.pattern_matches:
        lines.append("- No local pattern exceeded the retrieval threshold.")
    lines.extend(["", "## Recommended Actions", ""])
    lines.extend(f"- **{item.priority}:** {item.action} _Why: {item.reason}_" for item in report.recommended_actions)
    lines.extend(["", "## Safe Reply", "", f"> {report.safe_reply}", "", "## Reporting Guidance", ""])
    lines.extend(f"- {item}" for item in report.reporting_guidance)
    lines.extend(["", "## Retrieved Safety Guidance", ""])
    lines.extend(f"- {item}" for item in report.retrieved_guidance)
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report.limitations)
    lines.extend(["", "## Agent Decision Trace", ""])
    for trace in report.agent_trace:
        lines.extend([f"### {trace.agent} ({trace.status})", "", trace.decision, ""])
        lines.extend(f"- {evidence}" for evidence in trace.evidence)
        lines.append("")
    return "\n".join(lines)

