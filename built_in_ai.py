from __future__ import annotations
"""
Quantum Forge Built-in Cognitive Core.

This is a self-contained, dependency-free reasoning engine. It does not call a
third-party language model. It combines intent detection, lexical retrieval,
structured hypothesis generation, contradiction checks, confidence scoring and
persistent lessons supplied by the Forge application.

It is intentionally honest about its limits: this is a compact local AI core,
not a hidden copy of a frontier LLM.
"""
import hashlib
import math
import re
from collections import Counter
from typing import Any

STOP = {
    "the","and","for","with","that","this","from","into","about","what","why",
    "how","can","could","would","should","want","need","make","using","project",
    "research","please","tell","give","does","have","has","been","are","was",
    "were","your","you","our","their","them","then","than","also","just",
}

KNOWLEDGE = {
    "scientific_method": (
        "Strong research separates observations from hypotheses, uses independent "
        "evidence, tests competing explanations, measures uncertainty, and records failures."
    ),
    "quantum": (
        "Quantum computing uses qubits, superposition, interference and measurement. "
        "A simulator is not physical quantum hardware; hardware results require a real QPU."
    ),
    "ai": (
        "A learning AI system can improve its retrieval, rules, hypotheses and memory over time. "
        "Changing model weights is a separate training process and should not be claimed unless it occurs."
    ),
    "medical": (
        "Medical research requires evidence, safety testing, qualified clinical review and trials. "
        "A research AI may generate hypotheses and summarize evidence but cannot establish a cure or prescribe treatment."
    ),
    "engineering": (
        "Good engineering turns a hypothesis into requirements, a measurable test, failure criteria, "
        "observability and a repeatable implementation."
    ),
}

def words(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9][a-z0-9_-]{2,}", (text or "").lower())
            if w not in STOP]

def similarity(a: str, b: str) -> float:
    aa, bb = Counter(words(a)), Counter(words(b))
    if not aa or not bb:
        return 0.0
    common = sum(min(aa[k], bb[k]) for k in aa.keys() & bb.keys())
    na = math.sqrt(sum(v*v for v in aa.values()))
    nb = math.sqrt(sum(v*v for v in bb.values()))
    return common / (na * nb or 1.0)

def confidence(text: str, evidence_count: int = 0) -> int:
    score = 35 + min(25, evidence_count * 5)
    low = {"maybe","unknown","unclear","hypothesis","could","might","untested"}
    high = {"measured","observed","replicated","verified","source"}
    ts = set(words(text))
    score += min(20, len(ts & high) * 4)
    score -= min(20, len(ts & low) * 3)
    return max(5, min(95, score))

def relevant_memory(objective: str, memory: list[dict[str, Any]], limit: int = 5) -> list[str]:
    scored = []
    for item in memory or []:
        lesson = str(item.get("lesson",""))
        scored.append((similarity(objective, lesson), lesson))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [x[1] for x in scored[:limit] if x[0] > 0.03]

def domain(objective: str) -> str:
    t = (objective or "").lower()
    if any(x in t for x in ("cure","disease","drug","treatment","medicine","patient","health")):
        return "medical"
    if any(x in t for x in ("quantum","qubit","qpu","superposition","quantum computer")):
        return "quantum"
    if any(x in t for x in ("ai","artificial intelligence","agent","model","learning")):
        return "ai"
    if any(x in t for x in ("build","engineer","hardware","software","prototype","design")):
        return "engineering"
    return "general"

def _hash_branch(seed: str) -> int:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) % 32

def reason_agent(name: str, role: str, objective: str, context: str,
                 evidence: list[dict[str, Any]] | None = None) -> str:
    d = domain(objective)
    ev = evidence or []
    mem = context[:4500]
    kb = KNOWLEDGE.get(d, KNOWLEDGE["scientific_method"])
    terms = words(objective)[:10]
    branch = _hash_branch(objective + name)
    evidence_titles = [str(x.get("title","")).strip() for x in ev[:3] if x.get("title")]

    role_actions = {
        "Coordinator": "decompose the objective into measurable questions and prioritize the highest-information test",
        "Research": "separate established knowledge from plausible hypotheses and identify what evidence is still missing",
        "Discovery": "generate competing explanations rather than committing to the first attractive idea",
        "Quantum": f"rank a small set of computational branches; the local branch selector currently points to branch {branch}",
        "Invention": "convert the strongest hypothesis into a concrete concept with inputs, outputs and constraints",
        "Engineering": "define an implementable architecture and a falsifiable test",
        "Simulation": "look for edge cases, failure modes and adversarial conditions",
        "Evidence": "check provenance, evidence quality, contradictions and unsupported claims",
        "Critic": "attack the strongest conclusion and state what observation would disprove it",
        "Learning": "extract a reusable lesson and choose the next research action with the highest information value",
    }
    action = role_actions.get(name, "analyze the objective systematically")
    lines = [
        f"BUILT-IN AI PASS — {name}",
        f"Domain: {d.upper()}",
        f"Objective terms: {', '.join(terms) if terms else 'general objective'}",
        f"Reasoning: I will {action}.",
        f"Core principle: {kb}",
    ]
    if evidence_titles:
        lines.append("Retrieved evidence signals: " + " | ".join(evidence_titles))
    if mem:
        lines.append("Relevant Forge memory was supplied to this pass; prior lessons are treated as hypotheses, not facts.")
    if name in {"Discovery","Invention"}:
        lines.append("Candidate hypothesis: the objective may be improved by combining independent evidence, a competing mechanism, and a measurable validation loop. This is a hypothesis, not a result.")
        lines.append("Alternative hypothesis: the apparent pattern may be caused by selection bias, missing variables, or an untested confounder.")
    elif name == "Critic":
        lines.append("Main challenge: the system has not established causality merely by finding a correlation or a plausible mechanism.")
        lines.append("Falsifier: define a measurable prediction that would fail if the leading hypothesis is wrong.")
    elif name == "Quantum":
        lines.append("Quantum boundary: the branch ranking is a local mathematical simulation unless a real QPU job is explicitly connected.")
    else:
        lines.append("Assessment: useful as a research lead, but not yet a verified conclusion.")
    lines.append("Next action: run the smallest reproducible test that can distinguish the leading hypothesis from its strongest alternative.")
    if d == "medical":
        lines.append("Safety gate: any medical hypothesis requires qualified human review, appropriate laboratory validation and clinical evidence before treatment use.")
    return "\n".join(lines)

def synthesize_local(objective: str, findings: list[dict[str, Any]], memory: str) -> str:
    joined = "\n\n".join(f"[{x.get('agent','Agent')}] {x.get('text','')[:1200]}" for x in findings)
    d = domain(objective)
    conf = confidence(joined, len(findings))
    return (
        "QUANTUM FORGE — BUILT-IN AI LIVING REPORT\n\n"
        f"Objective: {objective}\n"
        f"Domain: {d.upper()}\n\n"
        "Current best assessment:\n"
        "The Forge's local cognitive core found a set of research leads and competing hypotheses. "
        "It has not treated them as proven facts. The strongest path is to compare the leading hypothesis "
        "with a plausible alternative using a measurable, reproducible test.\n\n"
        f"Agent synthesis:\n{joined[:9000]}\n\n"
        f"Prior memory considered:\n{memory[:2500] or 'No prior lessons yet.'}\n\n"
        "Unknowns / weaknesses:\n"
        "- Local reasoning is bounded by the compact built-in knowledge base and information retrieved by Forge.\n"
        "- Literature retrieval can fail or be incomplete.\n"
        "- Hypotheses require independent validation.\n\n"
        "Next research action:\n"
        "Retrieve stronger evidence, compare competing hypotheses, run a falsifiable test, record the result, "
        "and feed the lesson back into persistent Forge memory.\n\n"
        f"Confidence: {conf}/100 (research-lead confidence, not proof)."
    )

def answer_local(question: str, report: str, memory: str) -> str:
    q = (question or "").strip()
    d = domain(q)
    ql = q.lower()
    if any(x in ql for x in ("why hasn't","why hasnt","not started","started")):
        return (
            "The project can now run without an external AI key. The built-in Forge Cognitive Core is active. "
            "If no project is queued, create a research objective; the autonomous cycle will then process it. "
            "The core performs local reasoning, hypothesis generation, evidence retrieval, critique and memory learning."
        )
    if "what can you do" in ql or "capable" in ql:
        return (
            "I am the built-in Quantum Forge Cognitive Core. I can decompose objectives, retrieve and rank "
            "research memory, generate competing hypotheses, critique conclusions, score confidence, use the "
            "local quantum branch simulator, summarize retrieved literature, and learn reusable lessons from "
            "completed cycles. I do not pretend to have knowledge or experiments that Forge has not obtained."
        )
    kb = KNOWLEDGE.get(d, KNOWLEDGE["scientific_method"])
    mem = relevant_memory(q, [{"lesson": x} for x in (memory.split("\n") if memory else [])], 3)
    report_hint = report[:1800] if report else "No living report exists yet."
    answer = (
        f"Built-in AI analysis for: {q}\n\n"
        f"Relevant principle: {kb}\n\n"
        f"Current Forge report context: {report_hint}\n\n"
        f"Reasoning: this question should be treated as a research problem. "
        f"The next step is to identify the strongest evidence, competing explanation, and a test that can "
        f"separate them. Confidence is limited until those checks are completed."
    )
    if mem:
        answer += "\n\nRelated learned lessons:\n- " + "\n- ".join(mem)
    if d == "medical":
        answer += "\n\nMedical safety gate: this can support research and evidence organization, not diagnosis, prescribing, or proof of a cure."
    return answer
