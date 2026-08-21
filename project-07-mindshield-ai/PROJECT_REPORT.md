# Project 7 Report - MindShield AI

## 1. Project identity

- **Title:** MindShield AI - General AI Assistant and Multi-Agent Scam Detection System
- **Domain:** General assistance and cyber-safety
- **Interface:** Streamlit
- **Architecture:** Intent routing plus conditional LangGraph specialist workflow
- **LLM provider:** Groq production models for general chat and optional summary enhancement, with automatic model fallback

## 2. Problem statement

Users want one simple chatbot for broad questions, writing, learning, planning, and calculations. However, a suspicious request involving money, passwords, links, jobs, prizes, or account warnings needs a more controlled process than an ordinary conversational answer. Generic responses may miss evidence, overstate certainty, or fail to account for what the user already clicked or shared.

MindShield combines general conversation with a specialist evidence pipeline. The specialist route makes every signal, tool result, risk contribution, decision branch, and limitation visible.

## 3. Objectives

1. Provide a clean multi-turn chatbot for broad subjects.
2. Route explicit suspicious-content requests to specialist analysis.
3. Extract security-relevant entities without opening links.
4. Detect social-engineering tactics using transparent rules.
5. Retrieve related scam patterns and safety guidance from local data.
6. Produce an explainable bounded risk score.
7. Choose urgent protection or balanced verification conditionally.
8. Continue scam analysis if the LLM or network is unavailable.
9. Protect privacy and avoid false claims of safety or guilt.

## 4. Target users

- Students and families receiving suspicious messages
- Job seekers evaluating unexpected offers
- Online buyers and sellers
- Small organizations educating staff about phishing
- General users who also want an everyday AI assistant

## 5. General chat path

Ordinary questions are kept in a bounded conversation history and passed to Groq with a system policy requiring honesty, privacy protection, concise reasoning, and current-information caution. Arithmetic-looking requests are routed to a safe AST-based calculator that accepts only approved operations and functions.

If the user explicitly asks whether content is a scam, or supplies a link together with payment, OTP, account, prize, or urgency language, the interface routes it to the ScamShield workflow.

## 6. Scam analysis workflow

1. **Intake & Intent Agent:** validates content and detects the source.
2. **Entity & Link Inspector:** extracts URLs, email addresses, phone numbers, amounts, payment services, and secret requests. It inspects URL structure without navigating to it.
3. **Social Engineering Analyst:** detects urgency, threats, secrecy, advance fees, prizes, guaranteed returns, fake jobs, remote access, platform migration, and unusual payment methods.
4. **Scam Pattern Retrieval Agent:** retrieves the closest original patterns and the most relevant safety knowledge.
5. **Evidence & Risk Scoring Agent:** combines message, link, pattern, and reported-exposure points into a 0-100 score.
6. **Conditional Response Agent:** LangGraph selects an urgent-protection branch for strong risk or a balanced-verification branch for lower risk.
7. **Lead Safety Coordinator:** validates the report and adds actions, safe reply, reporting guidance, limitations, trace, and exports.

## 7. Data

`scam_patterns.json` contains ten original demonstration patterns: advance-fee prize, OTP takeover, fake job fee, delivery phishing, bank impersonation, guaranteed investment return, remote technical support, marketplace payment, authority impersonation, and account-verification phishing.

`safety_knowledge.md` contains original guidance about secrets, payments, suspicious links, independent verification, jobs, prizes, investments, remote access, evidence, reporting, and privacy.

The data are synthetic and do not contain personal information.

## 8. Score design

The score has four visible components:

- Message-indicator points, capped at 65
- Link-structure points, capped at 15
- Pattern-similarity points, capped at 15
- Reported-exposure points for opened links, sent money, or shared secrets

The final score is bounded at 100. Scores below 25 are “Low observed risk,” 25-54 are “Caution,” 55-79 are “High risk,” and 80-100 are “Critical risk.” These labels describe observed evidence, not the legal status of a sender.

## 9. Guardrails

- Pydantic validates input and all structured outputs.
- Critical reports must include an immediate action.
- Links are never opened by the specialist analyzer.
- The URL tool identifies only structural warnings, not live reputation.
- The calculator uses AST allow-lists instead of `eval`.
- LLM calls have timeouts and retry limits.
- The scam workflow has a deterministic fallback.
- The UI warns users to redact secrets and full financial identifiers.
- Low risk never means proven legitimate.

## 10. Evaluation

Automated tests cover input limits, normalization, entity extraction, shortened HTTP link scoring, indicators, pattern retrieval, critical prize/OTP scoring, low-risk wording, calculator behavior, missing-key behavior, urgent and balanced branches, post-exposure actions, and exports.

The Streamlit smoke test verifies both workspaces, general calculator conversation, specialist sample submission, six report tabs, and two downloads.

## 11. Limitations

- The analyzer does not open or live reputation-check websites.
- Rules and local patterns may miss new or heavily obfuscated scams.
- General chat cannot know current information without a verified search tool.
- A risk score is decision support, not a legal finding.
- Provider availability affects general chat but not deterministic scam analysis.

## 12. Future work

- Add a verified web-search tool with source citations.
- Add multilingual Urdu and Roman Urdu detection rules.
- Add optional image/OCR analysis for screenshots.
- Add approved domain-reputation and breached-credential services.
- Add organization accounts, privacy-preserving case storage, and audit controls.
- Add feedback labels to evaluate false positives and missed patterns.

## 13. Production orientation

MindShield solves a clear real-world problem with a dual-path architecture, conditional agent decisions, explainable evidence, local RAG, predictable output, privacy boundaries, provider fallbacks, tests, documentation, exports, and a deployable Streamlit interface.
