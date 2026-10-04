from __future__ import annotations
import asyncio, json, os, time, uuid
from typing import Any
from built_in_ai import answer_local, reason_agent, synthesize_local
from neural_core import generate as local_neural_generate
from memory_system import recall
from urllib.request import Request, urlopen
from urllib.parse import quote_plus
import re
from urllib.parse import quote_plus
import re

AGENT_ROLES = [
    ("Coordinator", "Break the objective into a research plan and assign priorities."),
    ("Research", "Find and synthesize scientific evidence; distinguish facts from hypotheses."),
    ("Discovery", "Generate several competing explanations or solution candidates."),
    ("Quantum", "Use the local quantum simulator to explore/rank small combinatorial branches."),
    ("Invention", "Turn promising findings into concrete invention or intervention concepts."),
    ("Engineering", "Translate ideas into implementable requirements, architecture and tests."),
    ("Simulation", "Stress-test assumptions, edge cases and failure modes."),
    ("Evidence", "Check provenance, quality, contradictions and missing evidence."),
    ("Critic", "Actively try to falsify the strongest conclusions and expose overclaims."),
    ("Learning", "Extract durable lessons, update memory and identify the next best research question."),
    ("Venture", "Find legitimate revenue opportunities by studying customer pain, demand, competition, pricing and distribution. Produce testable business opportunities; never assume revenue is guaranteed."),
    ("Product", "Turn the strongest opportunity into a concrete product offer, MVP scope, user workflow, differentiation and measurable value proposition."),
    ("Growth", "Find ethical customer-acquisition channels, partnerships, content opportunities and repeatable growth experiments. Avoid spam, deception and unauthorized outreach."),
    ("Sales", "Build qualified-customer profiles, outreach drafts, demo plans, objection handling and lead-scoring criteria. Do not send messages or make commitments without human approval."),
    ("Pricing", "Model sustainable pricing, usage limits, unit economics, gross-margin targets and packaging using explicit assumptions rather than invented financial results."),
    ("Opportunity", "Continuously compare ideas, score market attractiveness, urgency, competition, feasibility and monetization potential, then select the next highest-value experiment."),
    ("Venture", "Find legitimate ways the Forge can create revenue: customer problems, products, pricing, distribution, validation tests and unit economics. Never assume revenue is guaranteed and never take financial actions without human approval."),
]

SYSTEM = """You are an autonomous research agent inside Quantum Forge.
Be rigorous, curious and explicit about uncertainty. Never invent sources, experiments,
clinical outcomes, quantum hardware access, or facts. Separate OBSERVED evidence,
INFERENCE, HYPOTHESIS and UNKNOWN. For medical topics, do not diagnose or prescribe;
flag urgent situations and require qualified human review. The goal is to improve a
persistent research memory through repeated cycles, not to pretend certainty."""

def _api_config():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    return key, base, model

async def ask_llm(prompt: str, temperature: float = 0.2) -> str:
    key, base, model = _api_config()
    if not key:
        return await asyncio.to_thread(local_neural_generate, SYSTEM, prompt, temperature, 900)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
    }
    def call():
        req = Request(
            base + "/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=90) as r:
            data = json.loads(r.read().decode())
        return data["choices"][0]["message"]["content"]
    try:
        return await asyncio.to_thread(call)
    except Exception as exc:
        return f"LLM connector error: {type(exc).__name__}: {exc}"


def market_search(query: str, limit: int = 5) -> list[dict[str, str]]:
    """Lightweight public-market discovery for the Venture agent."""
    url = "https://html.duckduckgo.com/html/?q=" + quote_plus(query)
    try:
        req = Request(url, headers={"User-Agent": "QuantumForge/1.0 market research"})
        with urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
        results = []
        for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.S | re.I):
            href, title = m.groups()
            title = re.sub(r"<.*?>", "", title).strip()
            if title and href:
                results.append({"title": title[:240], "url": href[:1000]})
            if len(results) >= limit:
                break
        return results
    except Exception:
        return []



def market_search(query: str, limit: int = 5) -> list[dict[str, str]]:
    """Public web discovery used only for research; no purchases or financial actions."""
    url = "https://html.duckduckgo.com/html/?q=" + quote_plus(query)
    try:
        req = Request(url, headers={"User-Agent": "QuantumForge/1.0 market-research"})
        with urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
        out = []
        for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.S | re.I):
            href, title = m.groups()
            title = re.sub(r"<.*?>", "", title).strip()
            if title and href:
                out.append({"title": title[:240], "url": href[:1000]})
            if len(out) >= limit:
                break
        return out
    except Exception:
        return []

async def run_agent(name: str, role: str, objective: str, context: str, evidence=None) -> dict[str, Any]:
    memories = recall(objective + " " + context, limit=8)
    memory_text = "\n".join("- " + str(m.get("content",""))[:900] for m in memories)
    market_text = ""
    if name == "Venture":
        market_hits = await asyncio.to_thread(
            market_search,
            f"{objective} customer demand business opportunity SaaS pricing monetization"
        )
        market_text = "\n\nPUBLIC MARKET SIGNALS:\n" + "\n".join(
            f"- {x['title']} | {x['url']}" for x in market_hits
        )

    market_text = ""
    if name in {"Venture", "Growth", "Sales", "Pricing", "Opportunity"}:
        hits = await asyncio.to_thread(
            market_search,
            f"{objective} customer demand competitors pricing business opportunity"
        )
        market_text = "\n\nPUBLIC MARKET SIGNALS:\n" + "\n".join(
            f"- {x['title']} | {x['url']}" for x in hits
        )
    prompt = f"""ROLE: {name}
MISSION: {role}

PROJECT OBJECTIVE:
{objective}

CURRENT RESEARCH MEMORY:
{context[:12000]}
{market_text}

Work independently. Return:
1. What you learned.
2. Evidence or reasoning supporting it.
3. What could be wrong.
4. One concrete next research action.
5. If this is the Venture role: identify the target customer, proposed offer, realistic pricing model, acquisition channel, validation test, estimated gross-margin logic, and the biggest reason the idea could fail.
Keep it concise but substantive."""
    result = await ask_llm(prompt, 0.35)
    if not result:
        result = await asyncio.to_thread(reason_agent, name, role, objective, context, evidence)
    return {
        "id": str(uuid.uuid4()),
        "agent": name,
        "role": role,
        "text": result,
        "created_at": time.time(),
    }

async def synthesize(objective: str, findings: list[dict[str, Any]], memory: str) -> str:
    joined = "\n\n".join(f"[{x['agent']}]\n{x['text']}" for x in findings)
    memories = recall(objective + " " + memory, limit=12)
    retrieved = "\n".join("- " + str(m.get("content",""))[:900] for m in memories)
    prompt = f"""You are the senior synthesis agent.
PROJECT:
{objective}

PRIOR MEMORY:
{memory[:10000]}

RETRIEVED MEMORY:
{retrieved[:7000]}

NEW MULTI-AGENT FINDINGS:
{joined[:30000]}

Produce a living research report with:
- Current best answer
- Strongest evidence
- Competing hypotheses
- Contradictions / weaknesses
- What remains unknown
- Next experiments or searches
- Confidence (0-100) with a short reason
Never present a hypothesis as a proven cure, treatment, invention, or scientific fact."""
    result = await ask_llm(prompt, 0.15)
    return result or await asyncio.to_thread(synthesize_local, objective, findings, memory)

async def answer_chat(question: str, report: str, memory: str) -> str:
    memories = recall(question + " " + report, limit=12)
    retrieved = "\n".join("- " + str(m.get("content",""))[:900] for m in memories)
    prompt = f"""You are the conversational lead of Quantum Forge.
Answer the user's question using the living research report and memory below.
If the evidence is insufficient, say so and propose the next research step.

USER:
{question}

LIVING REPORT:
{report[:18000]}

MEMORY:
{memory[:10000]}
"""
    result = await ask_llm(prompt, 0.25)
    if result:
        return result
    return await asyncio.to_thread(answer_local, question, report, memory)
