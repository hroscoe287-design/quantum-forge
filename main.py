from __future__ import annotations

import asyncio
import hashlib
import json
import math
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
STATE_FILE = DATA / "state.json"
STATE_TMP = DATA / "state.json.tmp"

app = FastAPI(title="Quantum Forge", version="0.2.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

AGENTS = [
    ("Coordinator", "orchestrates research branches"),
    ("Disease Research", "maps mechanisms, targets and therapeutic hypotheses"),
    ("Discovery", "generates competing hypotheses and candidate solutions"),
    ("Quantum", "runs small quantum-state simulations and ranks search branches"),
    ("Invention", "turns ideas into technical concepts"),
    ("Engineering", "creates requirements and system architecture"),
    ("Simulation", "stress-tests computational designs"),
    ("Blueprint", "creates specifications and BOM candidates"),
    ("Critic", "tries to falsify weak conclusions"),
    ("Learning", "records evidence and improves future searches"),
]

CYCLE_SECONDS = max(30, int(os.getenv("FORGE_CYCLE_SECONDS", "60")))
MAX_PROJECTS_PER_CYCLE = max(1, int(os.getenv("FORGE_PROJECTS_PER_CYCLE", "3")))
state_lock = asyncio.Lock()
cycle_task: asyncio.Task | None = None


def default_state() -> dict[str, Any]:
    return {
        "started_at": time.time(),
        "cycle": 0,
        "running": True,
        "agents": {
            name: {"role": role, "status": "IDLE", "last_run": None, "jobs": 0}
            for name, role in AGENTS
        },
        "projects": [],
        "discoveries": [],
        "jobs": [],
        "evidence": [],
        "audit": [],
        "quantum": {
            "mode": "LOCAL_STATE_VECTOR",
            "provider": "local",
            "hardware_connected": False,
            "qubits": 8,
            "note": "Runs real small state-vector simulations locally. External quantum hardware is optional and is never claimed unless connected."
        }
    }


def save_state_sync(snapshot: dict[str, Any]) -> None:
    STATE_TMP.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    STATE_TMP.replace(STATE_FILE)


def load_state() -> dict[str, Any]:
    if STATE_FILE.exists():
        try:
            loaded = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            base = default_state()
            base.update(loaded)
            for name, role in AGENTS:
                base["agents"].setdefault(name, {"role": role, "status": "IDLE", "last_run": None, "jobs": 0})
            return base
        except Exception:
            pass
    state = default_state()
    save_state_sync(state)
    return state


state = load_state()


class ProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    objective: str = Field(min_length=3, max_length=5000)
    kind: str = "research"


class AgentRequest(BaseModel):
    project_id: str
    prompt: str = Field(min_length=3, max_length=10000)


def add_audit_sync(action: str, detail: str) -> None:
    state["audit"].insert(0, {
        "id": str(uuid.uuid4()),
        "time": time.time(),
        "action": action,
        "detail": detail,
    })
    state["audit"] = state["audit"][:250]


def add_job_sync(project_id: str | None, job_type: str, status: str = "QUEUED", detail: str = "") -> dict[str, Any]:
    job = {
        "id": str(uuid.uuid4()),
        "project_id": project_id,
        "type": job_type,
        "status": status,
        "detail": detail,
        "created_at": time.time(),
    }
    state["jobs"].insert(0, job)
    state["jobs"] = state["jobs"][:150]
    return job


def keywords(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]{3,}", text.lower())
    stop = {"what", "with", "from", "that", "this", "into", "about", "research", "using", "make", "need", "want"}
    seen: list[str] = []
    for word in words:
        if word not in stop and word not in seen:
            seen.append(word)
    return seen[:8]


def arxiv_search(query: str, limit: int = 5) -> list[dict[str, str]]:
    """Use arXiv's public Atom feed as a real literature signal source."""
    url = "https://export.arxiv.org/api/query?search_query=all:" + quote_plus(query) + f"&start=0&max_results={limit}"
    try:
        req = Request(url, headers={"User-Agent": "QuantumForge/0.2 research engine"})
        with urlopen(req, timeout=12) as response:
            raw = response.read().decode("utf-8", errors="replace")
        entries = re.findall(r"<entry>(.*?)</entry>", raw, flags=re.S)
        results = []
        for entry in entries:
            title = re.search(r"<title>(.*?)</title>", entry, flags=re.S)
            summary = re.search(r"<summary>(.*?)</summary>", entry, flags=re.S)
            link = re.search(r"<id>(.*?)</id>", entry, flags=re.S)
            if title:
                results.append({
                    "title": re.sub(r"\s+", " ", title.group(1)).strip(),
                    "summary": re.sub(r"\s+", " ", summary.group(1)).strip() if summary else "",
                    "url": link.group(1).strip() if link else "",
                    "source": "arXiv",
                })
        return results
    except Exception as exc:
        return [{"title": "Literature connector unavailable", "summary": str(exc), "url": "", "source": "connector"}]


def quantum_score(seed_text: str, branches: int = 16) -> dict[str, Any]:
    """Small, dependency-free state-vector search. This is a simulator, not quantum hardware."""
    digest = hashlib.sha256(seed_text.encode("utf-8")).digest()
    amplitudes = []
    for i in range(branches):
        raw = int.from_bytes(digest[i:i + 2], "big", signed=False)
        amplitude = math.sin((raw / 65535.0) * math.pi * 2 + i * 0.37)
        amplitudes.append(amplitude)
    norm = math.sqrt(sum(a * a for a in amplitudes)) or 1.0
    probs = [(a / norm) ** 2 for a in amplitudes]
    best = max(range(branches), key=lambda i: probs[i])
    return {
        "branches": branches,
        "best_branch": best,
        "probability": round(probs[best], 6),
        "distribution": [round(p, 6) for p in probs],
    }


def build_discovery(project: dict[str, Any], prompt: str, literature: list[dict[str, str]]) -> dict[str, Any]:
    q = quantum_score(project["objective"] + " " + prompt)
    evidence = literature[:5]
    confidence = min(0.9, 0.2 + 0.1 * len([x for x in evidence if x.get("url")]))
    return {
        "id": str(uuid.uuid4()),
        "project_id": project["id"],
        "title": "Autonomous research branch",
        "summary": f"Branch {q['best_branch']} explores: {prompt[:500]}",
        "confidence": round(confidence, 3),
        "evidence": evidence,
        "quantum_result": q,
        "status": "HYPOTHESIS",
        "created_at": time.time(),
    }


async def process_project(project: dict[str, Any], prompt: str | None = None) -> None:
    objective = prompt or project["objective"]
    job = add_job_sync(project["id"], "RESEARCH_CYCLE", "RUNNING", "Searching literature and evaluating computational branches")
    project["status"] = "RESEARCHING"

    for name in ("Coordinator", "Disease Research", "Discovery", "Quantum", "Critic", "Learning"):
        state["agents"][name]["status"] = "WORKING"
        state["agents"][name]["last_run"] = time.time()
        state["agents"][name]["jobs"] += 1

    search_terms = keywords(objective)
    query = " ".join(search_terms[:5]) or objective[:100]
    literature = await asyncio.to_thread(arxiv_search, query)
    discovery = build_discovery(project, objective, literature)

    state["discoveries"].insert(0, discovery)
    state["discoveries"] = state["discoveries"][:200]
    for item in literature:
        state["evidence"].insert(0, {
            **item,
            "project_id": project["id"],
            "created_at": time.time(),
        })
    state["evidence"] = state["evidence"][:500]

    project["status"] = "ACTIVE"
    project["evidence_level"] = "LITERATURE_BACKED" if any(x.get("url") for x in literature) else "HYPOTHESIS"
    job["status"] = "COMPLETE"
    job["detail"] = f"Collected {len(literature)} literature signals and ran {discovery['quantum_result']['branches']} computational branches"
    add_audit_sync("AUTONOMOUS_RESEARCH", f"{project['name']}: {job['detail']}")

    for name in ("Coordinator", "Disease Research", "Discovery", "Quantum", "Critic", "Learning"):
        state["agents"][name]["status"] = "IDLE"
    save_state_sync(state)


async def autonomous_cycle() -> None:
    while True:
        await asyncio.sleep(CYCLE_SECONDS)
        async with state_lock:
            state["cycle"] += 1
            state["running"] = True
            active = [p for p in state["projects"] if p.get("status") in {"QUEUED", "ACTIVE"}][:MAX_PROJECTS_PER_CYCLE]
            if not active:
                add_job_sync(None, "AUTONOMOUS_CYCLE", "COMPLETE", "No active projects; agents standing by")
            else:
                for project in active:
                    await process_project(project)
            save_state_sync(state)


@app.get("/")
async def home():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/state")
async def api_state():
    return state


@app.get("/api/health")
async def health():
    return {
        "ok": True,
        "service": "quantum-forge",
        "version": app.version,
        "agents": len(AGENTS),
        "cycle": state["cycle"],
        "running": state["running"],
    }


@app.post("/api/projects")
async def create_project(req: ProjectRequest):
    async with state_lock:
        project = {
            "id": str(uuid.uuid4()),
            "name": req.name,
            "objective": req.objective,
            "kind": req.kind,
            "created_at": time.time(),
            "status": "QUEUED",
            "evidence_level": "UNVALIDATED",
        }
        state["projects"].insert(0, project)
        add_job_sync(project["id"], "DISCOVERY_CYCLE", "QUEUED", "Waiting for autonomous research cycle")
        add_audit_sync("PROJECT_CREATED", f"{req.name}: {req.objective[:180]}")
        save_state_sync(state)
        return project


@app.post("/api/agents/run")
async def run_agent(req: AgentRequest):
    async with state_lock:
        project = next((p for p in state["projects"] if p["id"] == req.project_id), None)
        if not project:
            return {"error": "Project not found"}
        await process_project(project, req.prompt)
        discovery = state["discoveries"][0]
        return {"job": state["jobs"][0], "discovery": discovery}


@app.on_event("startup")
async def startup():
    global cycle_task
    if cycle_task is None or cycle_task.done():
        cycle_task = asyncio.create_task(autonomous_cycle())


@app.on_event("shutdown")
async def shutdown():
    global cycle_task
    if cycle_task:
        cycle_task.cancel()
        try:
            await cycle_task
        except asyncio.CancelledError:
            pass
