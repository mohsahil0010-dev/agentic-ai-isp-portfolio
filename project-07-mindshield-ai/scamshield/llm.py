"""Optional Groq language services with reliable fallbacks."""

from __future__ import annotations

import ast
import math
import operator
import os
import re
from dataclasses import dataclass

from .models import CaseInput, RiskAssessment


PRODUCTION_MODELS = ("openai/gpt-oss-20b", "openai/gpt-oss-120b")


GENERAL_SYSTEM_PROMPT = """You are MindShield AI, a capable general-purpose assistant.
Answer questions across education, technology, business, writing, coding, planning, and everyday topics.
Be clear, practical, and honest. Never claim to have browsed the web or checked live information unless a tool result is supplied.
If information may have changed recently, say that current verification may be needed.
Do not invent sources, personal experiences, or actions you did not perform.
Protect privacy: never ask for passwords, OTPs, PINs, CVVs, seed phrases, or full payment-card numbers.
For medical, legal, or financial decisions, provide general information and encourage appropriate professional verification.
Do not reveal private chain-of-thought. Give concise conclusions and useful explanations instead.
"""


@dataclass
class ChatResult:
    answer: str
    route: str
    tool_used: str | None = None
    model: str | None = None
    warning: str | None = None


def model_candidates() -> list[str]:
    """Return the configured model followed by current production fallbacks."""

    configured = os.getenv("MINDSHIELD_MODEL", "").strip()
    candidates = [configured, *PRODUCTION_MODELS] if configured else list(PRODUCTION_MODELS)
    return list(dict.fromkeys(model for model in candidates if model))


def _status_code(exc: Exception) -> int | None:
    value = getattr(exc, "status_code", None)
    if isinstance(value, int):
        return value
    response = getattr(exc, "response", None)
    response_code = getattr(response, "status_code", None)
    return response_code if isinstance(response_code, int) else None


def _provider_error_message(exc: Exception, tried_models: list[str]) -> tuple[str, str]:
    code = _status_code(exc)
    detail = str(exc).casefold()
    if code in {401, 403} or any(term in detail for term in ("invalid api key", "invalid_api_key", "authentication")):
        return (
            "Groq rejected the API key. Create or copy a valid key, update `GROQ_API_KEY` in your `.env` file "
            "or Streamlit Secrets, then restart the app.",
            "authentication_error",
        )
    if code == 429 or "rate limit" in detail:
        return (
            "The Groq request limit has been reached. Wait briefly and try again, or check the rate limits for your Groq account.",
            "rate_limit",
        )
    if code in {500, 502, 503, 498} or any(term in detail for term in ("over capacity", "service unavailable", "capacity exceeded")):
        return (
            "Groq is currently busy. MindShield tried its backup production model too. Please try again in a moment.",
            "provider_busy",
        )
    if code == 404 or any(term in detail for term in ("model_not_found", "decommissioned", "does not exist")):
        return (
            "The configured Groq model is unavailable and the backup models also failed. Remove `MINDSHIELD_MODEL` "
            "to use the automatic production defaults, then restart the app.",
            "model_unavailable",
        )
    if any(term in detail for term in ("timeout", "connection", "network")):
        return (
            "MindShield could not connect to Groq. Check the internet connection and try again.",
            "connection_error",
        )
    return (
        f"Groq could not complete the answer after trying {len(tried_models)} production model(s). Please try again.",
        "provider_error",
    )


ALLOWED_BINARY = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
ALLOWED_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
ALLOWED_FUNCTIONS = {"sqrt": math.sqrt, "round": round, "abs": abs}


def safe_calculate(expression: str) -> float | int:
    """Evaluate a small arithmetic expression without using eval."""

    if len(expression) > 120:
        raise ValueError("Expression is too long.")
    tree = ast.parse(expression, mode="eval")

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_BINARY:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and (abs(right) > 10 or abs(left) > 1_000_000):
                raise ValueError("Exponent is outside the safe range.")
            result = ALLOWED_BINARY[type(node.op)](left, right)
            if abs(result) > 1e15:
                raise ValueError("Result is outside the safe range.")
            return result
        if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_UNARY:
            return ALLOWED_UNARY[type(node.op)](visit(node.operand))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ALLOWED_FUNCTIONS:
            return ALLOWED_FUNCTIONS[node.func.id](*(visit(arg) for arg in node.args))
        raise ValueError("Only basic arithmetic, sqrt, round, and abs are supported.")

    return visit(tree)


def _calculator_expression(message: str) -> str | None:
    text = message.strip()
    prefixed = re.match(r"^(?:calculate|solve|what is)\s+(.+?)[?\s]*$", text, re.I)
    candidate = prefixed.group(1) if prefixed else text
    candidate = candidate.replace("×", "*").replace("÷", "/").replace("^", "**")
    if re.fullmatch(r"[\d\s+\-*/().,%a-z]+", candidate, re.I) and re.search(r"\d\s*[+\-*/]", candidate):
        return candidate
    return None


def answer_general_chat(messages: list[dict[str, str]]) -> ChatResult:
    """Answer an open-topic conversation, using a deterministic calculator when appropriate."""

    if not messages:
        return ChatResult(answer="Ask me anything.", route="general_chat")
    latest = messages[-1]["content"]
    expression = _calculator_expression(latest)
    if expression:
        try:
            result = safe_calculate(expression)
            return ChatResult(
                answer=f"The result is **{result:,}**." if isinstance(result, int) else f"The result is **{result:,.10g}**.",
                route="calculator",
                tool_used="Safe calculator",
            )
        except (ValueError, ZeroDivisionError, OverflowError, SyntaxError):
            pass

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return ChatResult(
            answer=(
                "General AI Chat needs a Groq API key. Add `GROQ_API_KEY` to your environment or Streamlit "
                "Secrets, then restart the app. The Scam Analyzer remains fully usable without an API key."
            ),
            route="configuration_help",
            warning="GROQ_API_KEY is not configured.",
        )
    try:
        from groq import Groq
    except ImportError:
        return ChatResult(
            answer="The Groq package is missing. Run `pip install -r requirements.txt`, then restart the app.",
            route="configuration_help",
            warning="groq_package_missing",
        )

    client = Groq(api_key=api_key, timeout=20.0, max_retries=1)
    clean_messages = [
        {"role": item["role"], "content": item["content"][:12_000]}
        for item in messages[-12:]
        if item.get("role") in {"user", "assistant"} and item.get("content")
    ]
    tried: list[str] = []
    last_error: Exception | None = None
    for model in model_candidates():
        tried.append(model)
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": GENERAL_SYSTEM_PROMPT}, *clean_messages],
                temperature=0.35,
                max_completion_tokens=1_200,
            )
            answer = (completion.choices[0].message.content or "").strip()
            if not answer:
                raise RuntimeError("The model returned an empty response.")
            return ChatResult(answer=answer, route="general_chat", model=model)
        except Exception as exc:
            last_error = exc
            if _status_code(exc) in {401, 403}:
                break
    assert last_error is not None
    message, warning = _provider_error_message(last_error, tried)
    return ChatResult(answer=message, route="provider_error", warning=warning)


def scam_summary(case: CaseInput, assessment: RiskAssessment, indicator_count: int) -> tuple[str, bool, str | None]:
    fallback = (
        f"The supplied content received a risk score of {assessment.score}/100 ({assessment.level.value}). "
        f"The analysis found {indicator_count} message or link warning signs. {assessment.verdict}"
    )
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return fallback, False, None
    try:
        from groq import Groq

        client = Groq(api_key=api_key, timeout=12.0, max_retries=1)
        last_error: Exception | None = None
        for model in model_candidates():
            try:
                completion = client.chat.completions.create(
                    model=model,
                    temperature=0.1,
                    max_completion_tokens=220,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Rewrite the supplied verified scam-analysis facts as a concise warning summary. "
                                "Do not add claims, identify a person as a criminal, or say a low score proves legitimacy."
                            ),
                        },
                        {"role": "user", "content": f"Facts: {fallback}\nContent excerpt: {case.content[:700]}"},
                    ],
                )
                text = (completion.choices[0].message.content or "").strip()
                return (text or fallback), bool(text), None
            except Exception as exc:
                last_error = exc
                if _status_code(exc) in {401, 403}:
                    break
        return fallback, False, f"LLM summary fallback: {type(last_error).__name__ if last_error else 'UnknownError'}"
    except Exception as exc:
        return fallback, False, f"LLM summary fallback: {type(exc).__name__}"
