from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
STATE_FILE = DATA / "state.json"

app = FastAPI(title="Quantum Forge", version="0.1.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

AGENTS = [
    ("Coordinator", "orchestrates research branches"),
    ("Disease Research", "maps mechanisms, targets and therapeutic hypotheses"),
    ("Discovery", "generates competing hypotheses and candidate solutions"),
    ("Quantum", "selects quantum-suitable workloads and simulations"),
    ("Invention", "turns ideas into technical concepts"),
    ("Engineering", "creates requirements and system architecture"),
    ("Simulation", "stress-tests computational designs"),
    ("Blueprint", "creates CAD-ready specifications and BOM plans"),
    ("Critic", "tries to falsify weak conclusions"),
    ("Learning", "records evidence and improves future searches"),
]

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
        "audit": [],
        "quantum": {
            "mode": "SIMULATION",
            "provider": "local",
            "hardware_connected": False,
            "note": "Quantum hardware is optional; the app uses a safe simulation fallback until credentials are configured."
        }
    }

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    state = default_state()
    save_state(state)
    return state

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

state = load_state()

class ProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    objective: str = Field(min_length=3, max_length=5000)
    kind: str = "research"

class AgentRequest(BaseModel):
    project_id: str
    prompt: str = Field(min_length=3, max_length=10000)

def add_audit(action: str, detail: str):
    state["audit"].insert(0, {
        "id": str(uuid.uuid4()),
        "time": time.time(),
        "action": action,
        "detail": detail,
    })
    state["audit"] = state["audit"][:200]
    save_state(state)

@app.get("/")
async def home():
    return FileResponse(ROOT / "static" / "index.html")

@app.get("/api/state")
async def api_state():
    return state

@app.get("/api/health")
async def health():
    return {"ok": True, "service": "quantum-forge", "agents": len(AGENTS), "cycle": state["cycle"]}

@app.post("/api/projects")
async def create_project(req: ProjectRequest):
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
    state["jobs"].insert(0, {
        "id": str(uuid.uuid4()),
        "project_id": project["id"],
        "type": "DISCOVERY_CYCLE",
        "status": "QUEUED",
        "created_at": time.time(),
    })
    add_audit("PROJECT_CREATED", f"{req.name}: {req.objective[:180]}")
    return project

@app.post("/api/agents/run")
async def run_agent(req: AgentRequest):
    project = next((p for p in state["projects"] if p["id"] == req.project_id), None)
    if not project:
        return {"error": "Project not found"}

    job = {
        "id": str(uuid.uuid4()),
        "project_id": req.project_id,
        "type": "TARGETED_AGENT_RUN",
        "status": "RUNNING",
        "prompt": req.prompt,
        "created_at": time.time(),
    }
    state["jobs"].insert(0, job)

    # The MVP creates an auditable research branch rather than pretending to have
    # discovered a medically or physically validated answer.
    discovery = {
        "id": str(uuid.uuid4()),
        "project_id": req.project_id,
        "title": "Research branch generated",
        "summary": f"Explore: {req.prompt[:300]}",
        "confidence": 0.0,
        "evidence": [],
        "status": "HYPOTHESIS",
        "created_at": time.time(),
    }
    state["discoveries"].insert(0, discovery)
    job["status"] = "COMPLETE"
    add_audit("AGENT_RUN", req.prompt[:300])
    save_state(state)
    return {"job": job, "discovery": discovery}

async def autonomous_cycle():
    while True:
        await asyncio.sleep(30)
        state["cycle"] += 1
        state["running"] = True
        now = time.time()
        for name, _ in AGENTS:
            a = state["agents"][name]
            a["status"] = "SCANNING" if name in ("Research", "Learning") else "READY"
            a["last_run"] = now
            a["jobs"] += 1
        # Create a lightweight internal cycle record. Real external research,
        # quantum hardware and model APIs plug into this same orchestration layer.
        state["jobs"].insert(0, {
            "id": str(uuid.uuid4()),
            "type": "AUTONOMOUS_CYCLE",
            "status": "COMPLETE",
            "cycle": state["cycle"],
            "created_at": now,
        })
        state["jobs"] = state["jobs"][:100]
        for a in state["agents"].values():
            a["status"] = "IDLE"
        save_state(state)

@app.on_event("startup")
async def startup():
    asyncio.create_task(autonomous_cycle())
