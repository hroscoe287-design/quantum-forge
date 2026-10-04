from __future__ import annotations
import asyncio, hashlib, json, math, os, re, time, uuid
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from quantum_agents import AGENT_ROLES, answer_chat, run_agent, synthesize
from quantum_cloud import config as quantum_config, job_status as quantum_job_status, status as quantum_status, submit_probe as quantum_submit_probe

ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
STATE_FILE = DATA / "state.json"
STATE_TMP = DATA / "state.json.tmp"

app = FastAPI(title="Quantum Forge", version="0.6.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

CYCLE_SECONDS = max(60, int(os.getenv("FORGE_CYCLE_SECONDS", "300")))
MAX_PROJECTS_PER_CYCLE = max(1, int(os.getenv("FORGE_PROJECTS_PER_CYCLE", "1")))
state_lock = asyncio.Lock()
cycle_task = None

def default_state():
    return {
        "started_at": time.time(), "cycle": 0, "running": True,
        "cycle_status": "WAITING", "last_cycle_started": None,
        "last_cycle_completed": None, "last_cycle_duration": None,
        "current_project": None, "current_activity": "Agents standing by",
        "agents": {n: {"role": r, "status": "IDLE", "last_run": None, "jobs": 0,
                       "activity": "Standing by", "last_result": ""} for n, r in AGENT_ROLES},
        "projects": [], "discoveries": [], "jobs": [], "evidence": [], "audit": [],
        "memory": [], "report": "", "chat": [],
        "quantum": {
            "mode": "LOCAL_STATE_VECTOR", "provider": "local",
            "hardware_connected": False, "backend": None, "qubits": 8,
            "last_hardware_job": None,
            "note": "Local simulator is the fallback. Real hardware is used only when a provider credential and hardware execution flag are configured."
        }
    }

def save_state_sync(s):
    STATE_TMP.write_text(json.dumps(s, indent=2), encoding="utf-8")
    STATE_TMP.replace(STATE_FILE)

def load_state():
    if STATE_FILE.exists():
        try:
            old = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            base = default_state()
            base.update(old)
            for n, r in AGENT_ROLES:
                base["agents"].setdefault(n, default_state()["agents"][n])
            return base
        except Exception:
            pass
    s = default_state()
    save_state_sync(s)
    return s

state = load_state()

class ProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    objective: str = Field(min_length=3, max_length=10000)
    kind: str = "research"

class AgentRequest(BaseModel):
    project_id: str
    prompt: str = Field(min_length=3, max_length=10000)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)

def add_audit_sync(action, detail):
    state["audit"].insert(0, {"id": str(uuid.uuid4()), "time": time.time(),
                               "action": action, "detail": detail})
    state["audit"] = state["audit"][:300]

def add_job_sync(project_id, job_type, status="QUEUED", detail=""):
    j = {"id": str(uuid.uuid4()), "project_id": project_id, "type": job_type,
         "status": status, "detail": detail, "created_at": time.time(), "completed_at": None}
    state["jobs"].insert(0, j)
    state["jobs"] = state["jobs"][:200]
    return j

def keywords(t):
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]{3,}", t.lower())
    stop = {"what","with","from","that","this","into","about","research","using","make","need","want"}
    return list(dict.fromkeys(x for x in words if x not in stop))[:8]

def arxiv_search(q, limit=6):
    url = "https://export.arxiv.org/api/query?search_query=all:" + quote_plus(q) + f"&start=0&max_results={limit}"
    try:
        req = Request(url, headers={"User-Agent": "QuantumForge/0.5 research engine"})
        with urlopen(req, timeout=15) as r:
            raw = r.read().decode("utf-8", errors="replace")
        out = []
        for e in re.findall(r"<entry>(.*?)</entry>", raw, re.S):
            t = re.search(r"<title>(.*?)</title>", e, re.S)
            s = re.search(r"<summary>(.*?)</summary>", e, re.S)
            l = re.search(r"<id>(.*?)</id>", e, re.S)
            if t:
                out.append({"title": re.sub(r"\s+", " ", t.group(1)).strip(),
                            "summary": re.sub(r"\s+", " ", s.group(1)).strip() if s else "",
                            "url": l.group(1).strip() if l else "", "source": "arXiv"})
        return out
    except Exception as exc:
        return [{"title": "Literature connector unavailable", "summary": str(exc),
                 "url": "", "source": "connector"}]

def quantum_score(seed, branches=32):
    digest = hashlib.sha256(seed.encode()).digest()
    amplitudes = [math.sin((int.from_bytes(digest[i % 24:(i % 24)+2], "big") / 65535) * math.pi * 2 + i * .37)
                  for i in range(branches)]
    norm = math.sqrt(sum(x*x for x in amplitudes)) or 1
    probs = [(x/norm)**2 for x in amplitudes]
    best = max(range(branches), key=lambda i: probs[i])
    return {"branches": branches, "best_branch": best, "probability": round(probs[best], 6),
            "distribution": [round(x, 6) for x in probs]}

def context_for(project):
    memory = state.get("memory", [])[-40:]
    recent = state.get("discoveries", [])[:10]
    parts = [f"Project: {project['name']}\nObjective: {project['objective']}"]
    if memory:
        parts.append("LEARNED MEMORY:\n" + "\n".join(x.get("lesson","") for x in memory))
    if recent:
        parts.append("RECENT DISCOVERIES:\n" + "\n".join(x.get("summary","") for x in recent))
    return "\n\n".join(parts)

async def process_project(project, prompt=None):
    objective = prompt or project["objective"]
    project["status"] = "RESEARCHING"
    state["current_project"] = project["name"]
    state["current_activity"] = "Agents are independently researching and challenging one another"
    job = add_job_sync(project["id"], "MULTI_AGENT_RESEARCH", "RUNNING",
                       "Parallel agents + literature retrieval + quantum simulation + synthesis")

    query = " ".join(keywords(objective)[:5]) or objective[:120]
    literature = await asyncio.to_thread(arxiv_search, query)
    for item in literature:
        state["evidence"].insert(0, {**item, "project_id": project["id"], "created_at": time.time()})
    state["evidence"] = state["evidence"][:600]

    ctx = context_for(project)
    async def one(agent):
        name, role = agent
        a = state["agents"][name]
        a["status"] = "WORKING"; a["activity"] = "Running independent reasoning pass"
        a["last_run"] = time.time(); a["jobs"] += 1
        result = await run_agent(name, role, objective, ctx)
        a["status"] = "COMPLETE"; a["activity"] = "Completed this research pass"
        a["last_result"] = result["text"][:800]
        return result

    findings = await asyncio.gather(*(one(agent) for agent in AGENT_ROLES))
    q = quantum_score(objective + " " + str(findings), 32)
    hardware_job = None
    qcfg = quantum_config()
    if qcfg["enabled"]:
        hardware_job = await asyncio.to_thread(quantum_submit_probe, f"Forge cycle {state['cycle']} project {project['name']}")
        if hardware_job.get("submitted"):
            state["quantum"]["last_hardware_job"] = hardware_job
            state["quantum"]["provider"] = hardware_job.get("provider", "ibm")
            state["quantum"]["backend"] = hardware_job.get("backend")
            state["quantum"]["hardware_connected"] = True
            state["quantum"]["mode"] = "REAL_QPU + LOCAL_FALLBACK"
            state["quantum"]["note"] = "A real QPU job was submitted; local simulation remains available while hardware jobs queue."
        else:
            state["quantum"]["hardware_connected"] = False
    report = await synthesize(objective, findings, state.get("report", ""))
    state["report"] = report

    discovery = {
        "id": str(uuid.uuid4()), "project_id": project["id"],
        "title": "Multi-agent research cycle", "summary": report[:1800],
        "confidence": None, "status": "HYPOTHESIS",
        "created_at": time.time(), "quantum_result": q,
        "hardware_quantum_job": hardware_job,
        "agent_findings": findings,
        "evidence": literature,
    }
    state["discoveries"].insert(0, discovery)
    state["discoveries"] = state["discoveries"][:100]

    lesson = {"id": str(uuid.uuid4()), "time": time.time(),
              "lesson": f"Cycle {state['cycle']} for {project['name']}: " + report[:1200],
              "source_discovery": discovery["id"]}
    state["memory"].insert(0, lesson)
    state["memory"] = state["memory"][:200]

    project["status"] = "ACTIVE"
    project["evidence_level"] = "LITERATURE_BACKED" if any(x.get("url") for x in literature) else "HYPOTHESIS"
    job["status"] = "COMPLETE"; job["completed_at"] = time.time()
    hardware_note = f"; real QPU job {hardware_job.get('job_id')}" if hardware_job and hardware_job.get("submitted") else ""
    job["detail"] = f"{len(findings)} agents completed; {len(literature)} literature signals; {q['branches']} local quantum branches{hardware_note}"
    add_audit_sync("MULTI_AGENT_CYCLE", job["detail"])
    for n, _ in AGENT_ROLES:
        state["agents"][n]["status"] = "IDLE"
        state["agents"][n]["activity"] = "Standing by"
    state["current_project"] = None
    state["current_activity"] = "Cycle complete — agents standing by"
    save_state_sync(state)

async def autonomous_cycle():
    while True:
        await asyncio.sleep(CYCLE_SECONDS)
        if state["cycle_status"] == "WORKING":
            continue
        state["cycle"] += 1
        state["cycle_status"] = "WORKING"
        state["last_cycle_started"] = time.time()
        save_state_sync(state)
        try:
            active = [p for p in state["projects"] if p.get("status") in {"QUEUED", "ACTIVE"}][:MAX_PROJECTS_PER_CYCLE]
            if not active:
                add_job_sync(None, "AUTONOMOUS_CYCLE", "COMPLETE", "No active projects; agents standing by")
                state["current_activity"] = "No active projects — waiting for a research objective"
            else:
                for project in active:
                    await process_project(project)
        except Exception as exc:
            state["cycle_status"] = "ERROR"
            state["current_activity"] = "Cycle error: " + str(exc)[:300]
            add_audit_sync("CYCLE_ERROR", str(exc)[:1000])
        finally:
            state["cycle_status"] = "COMPLETE"
            state["last_cycle_completed"] = time.time()
            if state["last_cycle_started"]:
                state["last_cycle_duration"] = round(time.time() - state["last_cycle_started"], 2)
            save_state_sync(state)

@app.get("/")
async def home():
    return FileResponse(ROOT / "static" / "index.html")

@app.get("/api/state")
async def api_state():
    return state

@app.get("/api/health")
async def health():
    qs = await asyncio.to_thread(quantum_status)
    return {"ok": True, "service": "quantum-forge", "version": app.version,
            "agents": len(AGENT_ROLES), "cycle": state["cycle"],
            "running": state["running"], "cycle_status": state["cycle_status"],
            "last_cycle_completed": state["last_cycle_completed"],
            "llm_configured": bool(os.getenv("OPENAI_API_KEY")),
            "quantum": qs}

@app.get("/api/quantum/status")
async def api_quantum_status():
    qs = await asyncio.to_thread(quantum_status)
    state["quantum"].update({
        "provider": qs.get("provider", state["quantum"].get("provider")),
        "backend": qs.get("backend"),
        "hardware_connected": bool(qs.get("connected")),
        "mode": "REAL_QPU + LOCAL_FALLBACK" if qs.get("connected") else "LOCAL_STATE_VECTOR",
        "connection_message": qs.get("message", "")
    })
    return {**qs, "last_hardware_job": state["quantum"].get("last_hardware_job")}

@app.post("/api/quantum/test")
async def api_quantum_test():
    result = await asyncio.to_thread(quantum_submit_probe, "Manual Quantum Forge hardware connectivity test")
    if result.get("submitted"):
        state["quantum"]["last_hardware_job"] = result
        state["quantum"]["hardware_connected"] = True
        state["quantum"]["provider"] = result.get("provider", "ibm")
        state["quantum"]["backend"] = result.get("backend")
        state["quantum"]["mode"] = "REAL_QPU + LOCAL_FALLBACK"
        add_audit_sync("REAL_QPU_SUBMITTED", f"{result.get('provider')} / {result.get('backend')} / {result.get('job_id')}")
        save_state_sync(state)
    return result

@app.get("/api/quantum/jobs/{job_id}")
async def api_quantum_job(job_id: str):
    return await asyncio.to_thread(quantum_job_status, job_id)

@app.post("/api/projects")
async def create_project(req: ProjectRequest):
    async with state_lock:
        p = {"id": str(uuid.uuid4()), "name": req.name, "objective": req.objective,
             "kind": req.kind, "created_at": time.time(), "status": "QUEUED",
             "evidence_level": "UNVALIDATED"}
        state["projects"].insert(0, p)
        add_job_sync(p["id"], "DISCOVERY_CYCLE", "QUEUED", "Waiting for autonomous research cycle")
        add_audit_sync("PROJECT_CREATED", f"{req.name}: {req.objective[:180]}")
        save_state_sync(state)
        return p

@app.post("/api/agents/run")
async def run_agents(req: AgentRequest):
    async with state_lock:
        p = next((p for p in state["projects"] if p["id"] == req.project_id), None)
        if not p:
            return {"error": "Project not found"}
        await process_project(p, req.prompt)
        return {"job": state["jobs"][0], "discovery": state["discoveries"][0]}

@app.post("/api/chat")
async def chat(req: ChatRequest):
    async with state_lock:
        reply = await answer_chat(req.message, state.get("report",""), "\n".join(x.get("lesson","") for x in state.get("memory", [])[-30:]))
        state["chat"].append({"role":"user","content":req.message,"time":time.time()})
        state["chat"].append({"role":"assistant","content":reply,"time":time.time()})
        state["chat"] = state["chat"][-100:]
        save_state_sync(state)
        return {"reply": reply}

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
