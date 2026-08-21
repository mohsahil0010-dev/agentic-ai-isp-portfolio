# MindShield AI - 5-Minute Demonstration Script

## 0:00-0:35 - Introduce the project

“My independent Project 7 is MindShield AI. It is one clean chatbot with two paths. Users can ask general questions across many subjects, but suspicious messages are routed to a controlled multi-agent scam investigation. This is a new cyber-safety domain and is not based on my ISP projects.”

## 0:35-1:20 - Demonstrate general chat

Open **Chat**.

Ask:

> Calculate (12500 × 0.10) + 12500.

“The intent router uses the local safe calculator, not an LLM. The trace beneath the answer shows the calculator route and tool.”

Then, with `GROQ_API_KEY` configured, ask:

> Explain Agentic AI in simple words and give one real example.

“The assistant keeps a bounded multi-turn history and can answer broad questions, write, explain, plan, summarize, and help with coding.”

## 1:20-2:10 - Run scam analysis

Open **Scam Check**, select **Prize message**, and press **Check message**.

“The full scam workflow works even without an API key. It does not open the link. It extracts the link, money, payment service, and OTP request, then checks structural link warnings and social-engineering rules.”

## 2:10-3:10 - Show evidence and RAG

Open **Verdict** and explain the risk score and confidence.

Open **Evidence**:

“These are the exact message fragments that contributed to the score. The RAG agent compares them with the private scam-pattern dataset.”

Open **Links & entities**:

“The shortened HTTP link is inspected as text. MindShield does not pretend to have visited it or checked live reputation.”

## 3:10-3:50 - Show actions and conditional routing

Open **Safety actions** and **Agent trace**.

“Because the score is high, LangGraph selects the urgent-protection branch. A low-risk reminder uses a different balanced-verification branch, and even then the system never says it is proven legitimate.”

Run **Low-risk reminder** if time allows.

## 3:50-4:25 - Explain guardrails

“Pydantic validates inputs and outputs. The final report requires immediate action at critical risk. The calculator has an AST allow-list and does not use eval. User secrets are discouraged, links are never opened, scores are bounded, and provider failure does not stop specialist analysis.”

## 4:25-5:00 - Tests, exports, and close

Run:

```bash
pytest -q
```

Download the Markdown report.

“MindShield demonstrates general LLM conversation, intent routing, tools, LangGraph, conditional multi-agent decisions, Agentic RAG, Pydantic structured output, error handling, safety controls, observability, tests, exports, and public Streamlit deployment.”

## Likely viva questions

### Why is this agentic instead of a normal chatbot?

The specialist path has shared state, role-specific agents, tool results, retrieved evidence, a calculated score, conditional routing, and a final coordinator. Later decisions depend on earlier outputs.

### Why does Scam Analyzer work without Groq?

Security-relevant extraction, URL structure, rule detection, retrieval, scoring, actions, and exports are deterministic. Groq only improves language where useful.

### Where is RAG used?

The retrieval agent builds a query from the message and detected indicator categories, then retrieves matching scam patterns and the most relevant safety-knowledge sections.

### How do you avoid false accusations?

The result is labeled observed risk, lists limitations, never says a low score proves legitimacy, and does not identify a sender as criminal. It recommends independent verification.

### What is the conditional LangGraph decision?

After the scoring agent, scores of 55 or higher go to the Urgent Protection Agent; lower scores go to the Balanced Verification Agent. Both routes then pass to the Lead Safety Coordinator.
