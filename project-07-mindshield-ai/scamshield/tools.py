"""Transparent detection, retrieval, scoring, and response tools."""

from __future__ import annotations

import ipaddress
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from .models import (
    CaseInput,
    ExtractedEntity,
    PatternMatch,
    RiskAssessment,
    RiskIndicator,
    RiskLevel,
    SafeAction,
    SourceType,
    UrlInspection,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

URL_PATTERN = re.compile(r"(?:(?:https?://|www\.)[^\s<>'\"]+)", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?92|0)?3\d{2}[\s-]?\d{7}(?!\d)")
AMOUNT_PATTERN = re.compile(
    r"(?<!\w)(?:pkr|rs\.?|usd|\$)\s*[\d,]+(?:\.\d{1,2})?|[\d,]+(?:\.\d{1,2})?\s*(?:pkr|rupees?|rs\.?)",
    re.IGNORECASE,
)

SHORTENER_HOSTS = {
    "bit.ly", "tinyurl.com", "t.co", "rb.gy", "cutt.ly", "is.gd", "shorturl.at", "rebrand.ly"
}
SUSPICIOUS_TLDS = {"zip", "click", "top", "xyz", "work", "support", "live", "cam", "rest"}


def detect_source(case: CaseInput) -> SourceType:
    if case.source_type is not SourceType.AUTO:
        return case.source_type
    text = case.content.casefold()
    if any(word in text for word in ("whatsapp", "wa.me", "forwarded many times")):
        return SourceType.WHATSAPP
    if any(word in text for word in ("subject:", "dear customer", "dear applicant")) and "@" in text:
        return SourceType.EMAIL
    if any(word in text for word in ("job offer", "selected for", "recruitment", "salary")):
        return SourceType.JOB
    if any(word in text for word in ("buyer", "seller", "marketplace", "courier agent")):
        return SourceType.MARKETPLACE
    if URL_PATTERN.search(case.content):
        return SourceType.WEBSITE
    return SourceType.SMS


def extract_entities(content: str) -> list[ExtractedEntity]:
    entities: list[ExtractedEntity] = []
    seen: set[tuple[str, str]] = set()

    def add(entity_type: str, value: str, normalized: str, concern: str) -> None:
        key = (entity_type, normalized.casefold())
        if key not in seen:
            seen.add(key)
            entities.append(
                ExtractedEntity(
                    entity_type=entity_type,
                    value=value[:500],
                    normalized_value=normalized[:500],
                    concern=concern,
                )
            )

    for match in URL_PATTERN.findall(content):
        cleaned = match.rstrip(".,);]}")
        normalized = cleaned if cleaned.lower().startswith("http") else f"https://{cleaned}"
        add("URL", cleaned, normalized, "Links can redirect to credential theft, malware, or fake payment pages.")
    for match in EMAIL_PATTERN.findall(content):
        add("Email", match, match.casefold(), "The visible sender should be verified through an independent official channel.")
    for match in PHONE_PATTERN.findall(content):
        normalized = re.sub(r"\D", "", match)
        add("Phone", match, normalized, "Phone numbers can be spoofed or controlled by an impersonator.")
    for match in AMOUNT_PATTERN.findall(content):
        add("Amount", match, re.sub(r"\s+", " ", match.upper()), "Money is requested or promised in the message.")

    lowered = content.casefold()
    for service in ("easypaisa", "jazzcash", "bank transfer", "crypto", "usdt", "gift card"):
        if service in lowered:
            add("Payment service", service, service.title(), "A payment channel is mentioned and should be independently verified.")
    for credential in ("otp", "pin", "password", "cvv", "verification code", "seed phrase"):
        if re.search(rf"\b{re.escape(credential)}\b", lowered):
            add("Credential request", credential, credential.upper(), "Legitimate support staff should not ask you to disclose this secret.")
    return entities


def inspect_url(url: str) -> UrlInspection:
    normalized = url if re.match(r"https?://", url, re.I) else f"https://{url}"
    parsed = urlparse(normalized)
    hostname = (parsed.hostname or "").casefold()
    findings: list[str] = []
    points = 0

    if parsed.scheme.casefold() == "http":
        findings.append("Uses an unencrypted HTTP link.")
        points += 8
    if hostname in SHORTENER_HOSTS:
        findings.append("Uses a link-shortening service that hides the final destination.")
        points += 14
    try:
        ipaddress.ip_address(hostname)
        findings.append("Uses a raw IP address instead of a recognizable domain.")
        points += 15
    except ValueError:
        pass
    if hostname.startswith("xn--") or ".xn--" in hostname:
        findings.append("Contains Punycode, which can be used for lookalike domains.")
        points += 12
    tld = hostname.rsplit(".", 1)[-1] if "." in hostname else ""
    if tld in SUSPICIOUS_TLDS:
        findings.append(f"Uses a high-abuse-style .{tld} domain ending.")
        points += 7
    if hostname.count("-") >= 3 or len(hostname) > 45:
        findings.append("The hostname is unusually complex.")
        points += 6
    if any(term in hostname for term in ("verify", "secure-login", "account-update", "free-prize", "claim-now")):
        findings.append("The hostname uses pressure or account-verification wording.")
        points += 8
    if "@" in parsed.netloc:
        findings.append("The link contains an @ sign that can disguise the actual destination.")
        points += 15
    if not findings:
        findings.append("No strong structural warning was found, but the destination was not opened or reputation-checked.")
    return UrlInspection(url=url, hostname=hostname or "unknown", risk_points=min(points, 40), findings=findings)


INDICATOR_RULES = [
    ("Urgency and pressure", r"\b(urgent|immediately|act now|within \d+ (?:minutes?|hours?)|today only|last chance|claim now|(?:pay|send|transfer)[^.!?]{0,30}today)\b", 10, "Pressure reduces the time available for independent verification."),
    ("Threat or fear", r"\b(account (?:will be )?(?:blocked|closed|suspended)|legal action|police case|arrest|penalty|service disconnected)\b", 15, "Threats are commonly used to force rushed compliance."),
    ("Secrecy request", r"\b(do not tell|keep (?:this )?secret|confidential transaction|don't inform)\b", 14, "Secrecy prevents the target from checking with a trusted person."),
    ("Sensitive secret request", r"\b(send|share|tell|enter|confirm)[^.!?]{0,35}\b(otp|pin|password|cvv|verification code|seed phrase)\b", 25, "The message asks for information that can enable account takeover or theft."),
    ("Advance payment", r"\b(processing fee|registration fee|security fee|release fee|customs fee|pay first|deposit first|training fee)\b", 18, "An upfront fee is requested before the promised reward, job, or service."),
    ("Prize or lottery", r"\b(winner|won|lottery|lucky draw|cash prize|reward of|congratulations)\b", 14, "Unexpected rewards are a common lure for payment or credential theft."),
    ("Guaranteed return", r"\b(guaranteed profit|double your money|risk-free return|daily profit|100% return)\b", 18, "Guaranteed or unrealistic returns are a strong fraud signal."),
    ("Unexpected job selection", r"\b(selected for (?:the )?(?:job|position)|hired without interview|easy online work|data entry job|earn from home)\b", 13, "Unexpected hiring claims can lead to fee or identity-document theft."),
    ("Remote access request", r"\b(anydesk|teamviewer|remote access|screen share|install this app)\b", 20, "Remote-access software can give an attacker control of the device."),
    ("Move off platform", r"\b(contact me on whatsapp|continue on telegram|outside the platform|private chat only)\b", 9, "Moving away from platform protections can reduce traceability and safeguards."),
    ("Unusual payment method", r"\b(gift card|crypto|usdt|bitcoin|easypaisa|jazzcash)[^.!?]{0,45}\b(send|pay|transfer|deposit)\b", 14, "The requested payment method may be difficult to reverse."),
]


def detect_indicators(content: str, url_inspections: list[UrlInspection]) -> list[RiskIndicator]:
    indicators: list[RiskIndicator] = []
    for category, pattern, weight, explanation in INDICATOR_RULES:
        match = re.search(pattern, content, flags=re.IGNORECASE)
        if match:
            severity = "Critical" if weight >= 22 else "High" if weight >= 15 else "Medium" if weight >= 8 else "Low"
            indicators.append(
                RiskIndicator(
                    category=category,
                    evidence=match.group(0)[:180],
                    explanation=explanation,
                    weight=weight,
                    severity=severity,
                )
            )
    for inspection in url_inspections:
        if inspection.risk_points:
            weight = min(20, max(6, inspection.risk_points))
            indicators.append(
                RiskIndicator(
                    category="Suspicious link structure",
                    evidence=inspection.url[:180],
                    explanation="; ".join(inspection.findings),
                    weight=weight,
                    severity="High" if weight >= 15 else "Medium",
                )
            )
    return indicators


def _load_patterns() -> list[dict]:
    with (DATA_DIR / "scam_patterns.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def retrieve_patterns(content: str, indicators: list[RiskIndicator], top_k: int = 3) -> list[PatternMatch]:
    text_terms = Counter(re.findall(r"[a-z0-9]{3,}", content.casefold()))
    categories = {item.category.casefold() for item in indicators}
    matches: list[tuple[float, PatternMatch]] = []
    for pattern in _load_patterns():
        keywords = {keyword.casefold() for keyword in pattern["keywords"]}
        overlap = {term for term in keywords if text_terms[term]}
        signal_matches = [signal for signal in pattern["signals"] if any(signal.casefold() in category for category in categories)]
        raw = len(overlap) * 2 + len(signal_matches) * 3
        denominator = max(5, len(keywords) + len(pattern["signals"]))
        similarity = min(1.0, raw / denominator)
        if similarity > 0:
            matches.append(
                (
                    similarity,
                    PatternMatch(
                        pattern_id=pattern["id"],
                        name=pattern["name"],
                        category=pattern["category"],
                        similarity=round(similarity, 2),
                        matched_signals=sorted(overlap) + signal_matches,
                        explanation=pattern["description"],
                    ),
                )
            )
    return [item for _, item in sorted(matches, key=lambda pair: pair[0], reverse=True)[:top_k]]


def score_risk(
    case: CaseInput,
    indicators: list[RiskIndicator],
    inspections: list[UrlInspection],
    matches: list[PatternMatch],
) -> RiskAssessment:
    indicator_points = min(65, sum(item.weight for item in indicators))
    link_points = min(15, sum(item.risk_points for item in inspections) // 2)
    pattern_points = min(15, round(sum(item.similarity for item in matches) * 8))
    exposure_points = 0
    if case.clicked_link:
        exposure_points += 8
    if case.shared_sensitive_info:
        exposure_points += 18
    if case.sent_money:
        exposure_points += 18
    score = min(100, indicator_points + link_points + pattern_points + exposure_points)

    if score >= 80:
        level = RiskLevel.CRITICAL
        verdict = "Strong scam indicators are present and the reported interaction may require immediate protective action."
    elif score >= 55:
        level = RiskLevel.HIGH
        verdict = "Multiple strong scam indicators are present. Do not continue until independently verified."
    elif score >= 25:
        level = RiskLevel.CAUTION
        verdict = "Some warning signs are present. Verify the sender and request through an independent official channel."
    else:
        level = RiskLevel.LOW
        verdict = "No strong scam pattern was detected in the supplied text, but this is not proof that it is legitimate."

    evidence_count = len(indicators) + len(inspections) + len(matches)
    confidence = "High" if evidence_count >= 6 else "Medium" if evidence_count >= 3 else "Low"
    return RiskAssessment(
        score=score,
        level=level,
        verdict=verdict,
        confidence=confidence,
        score_breakdown={
            "message_indicators": indicator_points,
            "link_structure": link_points,
            "pattern_similarity": pattern_points,
            "reported_exposure": exposure_points,
        },
    )


def retrieve_safety_guidance(query: str, top_k: int = 4) -> list[str]:
    text = (DATA_DIR / "safety_knowledge.md").read_text(encoding="utf-8")
    chunks = [chunk.strip() for chunk in re.split(r"\n(?=## )", text) if chunk.strip() and chunk.startswith("##")]
    query_terms = Counter(re.findall(r"[a-z]{3,}", query.casefold()))
    scored: list[tuple[int, str]] = []
    for chunk in chunks:
        chunk_terms = Counter(re.findall(r"[a-z]{3,}", chunk.casefold()))
        overlap = sum(min(count, chunk_terms[term]) for term, count in query_terms.items())
        heading = chunk.splitlines()[0].casefold()
        heading_boost = sum(2 for term in query_terms if term in heading)
        scored.append((overlap + heading_boost, chunk))
    selected = sorted(scored, key=lambda item: item[0], reverse=True)[:top_k]
    return [re.sub(r"^##\s*", "", chunk).replace("\n", " ") for _, chunk in selected]


def build_actions(case: CaseInput, assessment: RiskAssessment) -> list[SafeAction]:
    actions: list[SafeAction] = []
    if assessment.score >= 55:
        actions.extend(
            [
                SafeAction(priority="Immediate", action="Stop replying, do not open further links, and do not send money or codes.", reason="Continuing contact can increase pressure and exposure."),
                SafeAction(priority="Next", action="Verify the request using a phone number or website you find independently.", reason="Do not use contact details supplied inside the suspicious message."),
                SafeAction(priority="Next", action="Preserve screenshots, sender details, payment references, and timestamps.", reason="Evidence can help the platform, payment provider, or authorities investigate."),
            ]
        )
    else:
        actions.extend(
            [
                SafeAction(priority="Next", action="Confirm the sender and request through an independent official channel.", reason="A low score does not guarantee legitimacy."),
                SafeAction(priority="Preventive", action="Avoid sharing passwords, OTPs, PINs, CVVs, or recovery codes.", reason="These secrets can enable account takeover or unauthorized transactions."),
            ]
        )
    if case.clicked_link:
        actions.append(SafeAction(priority="Immediate", action="Close the page, do not download anything, and run a trusted device security scan.", reason="A clicked link may have attempted credential theft or a malicious download."))
    if case.shared_sensitive_info:
        actions.append(SafeAction(priority="Immediate", action="Change the affected password from a trusted device, enable multi-factor authentication, and revoke other sessions.", reason="Shared credentials or codes may allow immediate account access."))
    if case.sent_money:
        actions.append(SafeAction(priority="Immediate", action="Contact the bank or payment provider through its official channel and ask whether the transaction can be stopped or disputed.", reason="Fast reporting can improve the chance of limiting loss."))
    actions.append(SafeAction(priority="Preventive", action="Block and report the sender using the platform's built-in controls.", reason="This limits further contact and provides a signal to the platform."))

    seen: set[str] = set()
    deduped: list[SafeAction] = []
    order = {"Immediate": 0, "Next": 1, "Preventive": 2}
    for action in sorted(actions, key=lambda item: order[item.priority]):
        if action.action not in seen:
            seen.add(action.action)
            deduped.append(action)
    return deduped


def reporting_guidance(source: SourceType, case: CaseInput) -> list[str]:
    guidance = [
        f"Use the official report/block feature in {source.value if source is not SourceType.AUTO else 'the originating platform'}.",
        "If money or an account is involved, contact the provider using contact information from its official app, card, or website.",
        "For material loss, identity theft, threats, or repeated targeting, use your country's official cybercrime reporting channel.",
    ]
    if case.sent_money:
        guidance.insert(0, "Report the transaction to the bank or payment service immediately and retain the complaint/reference number.")
    return guidance
