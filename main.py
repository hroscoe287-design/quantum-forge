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
from agent_org import BOSS_ROLES, DEPARTMENTS, boss_inputs, executive_report
from quantum_cloud import config as quantum_config, job_status as quantum_job_status, status as quantum_status, submit_probe as quantum_submit_probe
from neural_core import status as neural_status
from memory_system import learn_from_cycle, recall, stats as memory_stats
from revenue_engine import build_offer, create_payment_link, offer_html, stripe_configured
from payout_ledger import ensure_ledger, recompute_summary, request_daily_payout, approve_payout, reject_payout

ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
STATE_FILE = DATA / "state.json"
STATE_TMP = DATA / "state.json.tmp"

app = FastAPI(title="Quantum Forge", version="0.8.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

CYCLE_SECONDS = max(60, int(os.getenv("FORGE_CYCLE_SECONDS", "300")))
MAX_PROJECTS_PER_CYCLE = max(1, int(os.getenv("FORGE_PROJECTS_PER_CYCLE", "1")))
REVENUE_MODE = os.getenv("FORGE_REVENUE_MODE", "true").strip().lower() in {"1", "true", "yes", "on"}
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
        "bosses": {n: {"role": r, "department": DEPARTMENTS.get(n, []), "status": "IDLE", "last_run": None,
                       "jobs": 0, "activity": "Standing by", "last_result": ""} for n, r in BOSS_ROLES},
        "executive": {"agent": "SupremeForgeCEO", "status": "IDLE", "last_run": None, "reports": 0,
                      "last_report": "", "verified_revenue_usd": 0.0, "verified_costs_usd": 0.0},
        "projects": [], "discoveries": [], "jobs": [], "evidence": [], "audit": [],
        "memory": [], "report": "", "chat": [],
        "daily_reports": [], "daily_report_date": None,
        "revenue": {"enabled": REVENUE_MODE, "opportunities_found": 0, "experiments": 0, "pipeline_status": "SCANNING", "last_scan": None, "note": "Agents research and prepare revenue opportunities continuously; human approval is required before sales, spending, contracts, or financial transactions.", "proposals": [], "approved": [], "rejected": [], "offers": [], "verified_revenue_usd": 0.0, "checkout_provider": "stripe", "checkout_configured": stripe_configured()},
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
            for n, r in BOSS_ROLES:
                base["bosses"].setdefault(n, default_state()["bosses"][n])
            return base
        except Exception:
            pass
    s = default_state()
    save_state_sync(s)
    return s

state = load_state()
ensure_ledger(state)
recompute_summary(state)

class ProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    objective: str = Field(min_length=3, max_length=10000)
    kind: str = "research"

class AgentRequest(BaseModel):
    project_id: str
    prompt: str = Field(min_length=3, max_length=10000)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)

class RevenueApproval(BaseModel):
    approved_by: str = Field(default="owner", min_length=1, max_length=120)
    note: str = Field(default="", max_length=2000)

def maybe_daily_report_sync():
    """Create one daily operating report from recorded state and verified revenue only."""
    today = time.strftime("%Y-%m-%d", time.gmtime())
    if state.get("daily_report_date") == today:
        return
    rv = state.get("revenue", {})
    offers = rv.get("offers", [])
    live_offers = sum(1 for x in offers if x.get("status") == "LIVE")
    verified = float(rv.get("verified_revenue_usd", 0.0) or 0.0)
    report = {
        "date": today,
        "generated_at": time.time(),
        "cycles_completed": state.get("cycle", 0),
        "agents": len(AGENT_ROLES),
        "bosses": len(BOSS_ROLES),
        "executive_agent": "SupremeForgeCEO",
        "projects": len(state.get("projects", [])),
        "discoveries": len(state.get("discoveries", [])),
        "revenue_opportunities": rv.get("opportunities_found", 0),
        "revenue_experiments": rv.get("experiments", 0),
        "live_offers": live_offers,
        "verified_revenue_usd": verified,
        "verified_costs_usd": float(rv.get("verified_costs_usd", 0.0) or 0.0),
        "verified_profit_usd": verified - float(rv.get("verified_costs_usd", 0.0) or 0.0),
        "boss_reviews": len(BOSS_ROLES),
        "executive_report": state.get("executive", {}).get("last_report", "")[:12000],
        "decision": "Use verified results to scale, modify or kill experiments; forecasts are not counted as revenue.",
    }
    state.setdefault("daily_reports", []).insert(0, report)
    state["daily_reports"] = state["daily_reports"][:90]
    state["daily_report_date"] = today
    add_audit_sync("DAILY_REVENUE_REPORT", f"{today}: verified revenue $"+f"{verified:.2f}"+f"; {live_offers} live offers")

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


def ensure_revenue_project():
    if not REVENUE_MODE:
        return
    existing = next((p for p in state["projects"] if p.get("system") == "REVENUE_LAB"), None)
    if existing:
        return
    p = {
        "id": str(uuid.uuid4()),
        "name": "Forge Revenue Lab",
        "objective": (
            "Continuously discover legitimate, defensible ways Quantum Forge can earn revenue. "
            "Research customer pain, demand, competitors, pricing, distribution and product opportunities. "
            "Turn the best opportunities into concrete experiments and launch-ready assets. "
            "Do not spend money, trade assets, send unsolicited outreach, sign contracts, or claim revenue "
            "without explicit human approval and verification."
        ),
        "kind": "revenue",
        "created_at": time.time(),
        "status": "ACTIVE",
        "evidence_level": "RESEARCH",
        "system": "REVENUE_LAB",
    }
    state["projects"].append(p)
    add_audit_sync("REVENUE_LAB_STARTED", "Continuous revenue-discovery pipeline enabled")
    save_state_sync(state)

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
        result = await run_agent(name, role, objective, ctx, literature)
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
    # Department bosses review their assigned workers before the executive layer decides priorities.
    boss_findings = []
    for boss_name, boss_role in BOSS_ROLES:
        b = state["bosses"][boss_name]
        b["status"] = "WORKING"
        b["activity"] = "Reviewing department findings"
        b["last_run"] = time.time()
        b["jobs"] += 1
        department_context = boss_inputs(findings, DEPARTMENTS.get(boss_name, []))
        boss_prompt = (
            f"DEPARTMENT BOSS: {boss_name}\n"
            f"MISSION: {boss_role}\n"
            f"PROJECT: {objective}\n"
            f"WORKER FINDINGS:\n{department_context}\n\n"
            "Review the workers. Identify strongest evidence, failures, opportunities, "
            "next actions, and what should be scaled, modified or killed. Never count forecasts as revenue."
        )
        result = await run_agent(boss_name, boss_role, objective, boss_prompt, literature)
        boss_findings.append(result)
        b["status"] = "COMPLETE"
        b["activity"] = "Completed department review"
        b["last_result"] = result["text"][:1200]

    report = await synthesize(objective, findings + boss_findings, state.get("report", ""))
    state["executive"]["status"] = "WORKING"
    state["executive"]["last_run"] = time.time()
    state["current_activity"] = "Supreme Forge CEO is reviewing departments and preparing the executive report"
    verified_revenue = float(state.get("revenue", {}).get("verified_revenue_usd", 0.0) or 0.0)
    verified_costs = float(state.get("revenue", {}).get("verified_costs_usd", 0.0) or 0.0)
    exec_report = executive_report(
        boss_findings,
        verified_revenue,
        verified_costs,
        state["cycle"],
        len(findings),
    )
    state["executive"]["last_report"] = exec_report
    state["executive"]["reports"] += 1
    state["executive"]["verified_revenue_usd"] = verified_revenue
    state["executive"]["verified_costs_usd"] = verified_costs
    state["executive"]["status"] = "COMPLETE"
    if project.get("system") == "REVENUE_LAB":
        state["revenue"]["last_scan"] = time.time()
        state["revenue"]["opportunities_found"] += sum(
            1 for f in findings
            if any(k in f.get("text", "").lower() for k in ("revenue", "customer", "pricing", "opportunity", "mvp"))
        )
        state["revenue"]["experiments"] += 1
        state["revenue"]["pipeline_status"] = "OPPORTUNITIES_READY"
        proposal = {
            "id": str(uuid.uuid4()),
            "created_at": time.time(),
            "project_id": project["id"],
            "title": "Forge-selected revenue offer",
            "description": report[:4000],
            "status": "PENDING_APPROVAL",
            "action": "BUILD_AND_PUBLISH_SELLABLE_RESEARCH_OFFER",
            "risk": "No money is spent and no external message, contract, or financial transaction is executed until approval.",
            "requested_scope": "After approval, Forge may build the specific offer, create a Stripe checkout only if STRIPE_SECRET_KEY is configured, and publish the offer page. Customer acquisition remains subject to approved channels."
        }
        state["revenue"].setdefault("proposals", []).insert(0, proposal)
        state["revenue"]["proposals"] = state["revenue"]["proposals"][:100]
        add_audit_sync("REVENUE_APPROVAL_REQUESTED", proposal["title"])
    learned_ids = await asyncio.to_thread(learn_from_cycle, project["id"], objective, report, findings, literature)
    state["report"] = report

    discovery = {
        "id": str(uuid.uuid4()), "project_id": project["id"],
        "title": "Multi-agent research cycle", "summary": report[:1800],
        "confidence": None, "status": "HYPOTHESIS",
        "created_at": time.time(), "quantum_result": q,
        "hardware_quantum_job": hardware_job,
        "agent_findings": findings,
        "evidence": literature,
        "learned_memory_ids": learned_ids,
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
    for n, _ in BOSS_ROLES:
        state["bosses"][n]["status"] = "IDLE"
        state["bosses"][n]["activity"] = "Standing by"
    state["executive"]["status"] = "IDLE"
    state["current_project"] = None
    state["current_activity"] = "Cycle complete — agents standing by"
    maybe_daily_report_sync()
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
            ensure_revenue_project()
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
            "agents": len(AGENT_ROLES), "bosses": len(BOSS_ROLES), "executive_agent": "SupremeForgeCEO", "cycle": state["cycle"],
            "running": state["running"], "cycle_status": state["cycle_status"],
            "last_cycle_completed": state["last_cycle_completed"],
            "llm_configured": bool(os.getenv("OPENAI_API_KEY")),
            "built_in_ai": True,
            "ai_mode": "EXTERNAL_LLM + BUILT_IN_FALLBACK" if os.getenv("OPENAI_API_KEY") else "BUILT_IN_COGNITIVE_CORE",
            "quantum": qs, "neural_core": neural_status(), "memory": memory_stats(), "revenue": state.get("revenue", {})}

@app.get("/api/org")
async def api_org():
    return {"executive": state.get("executive", {}), "bosses": state.get("bosses", {}), "departments": DEPARTMENTS}

@app.get("/api/memory/search")
async def api_memory_search(q: str, limit: int = 12):
    return {"results": recall(q, max(1, min(limit, 50)))}

@app.get("/api/memory/stats")
async def api_memory_stats():
    return memory_stats()

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

@app.get("/api/reports/daily")
async def daily_reports():
    maybe_daily_report_sync()
    save_state_sync(state)
    return state.get("daily_reports", [])

@app.get("/api/reports/daily/latest")
async def latest_daily_report():
    maybe_daily_report_sync()
    save_state_sync(state)
    return (state.get("daily_reports") or [{}])[0]

@app.get("/api/payouts/ledger")
async def payout_ledger():
    ensure_ledger(state)
    return {"summary": recompute_summary(state), "settings": state["payout_settings"], "ledger": state["payout_ledger"][:200]}

@app.get("/api/payouts/status")
async def payout_status():
    ensure_ledger(state)
    return {"summary": recompute_summary(state), "pending_approval": [x for x in state["payout_ledger"] if x.get("type") == "PAYOUT" and x.get("payout_status") == "PENDING_OWNER_APPROVAL"]}

@app.post("/api/payouts/daily/request")
async def daily_payout_request():
    result = request_daily_payout(state)
    add_audit_sync("DAILY_PAYOUT_REQUESTED", str(result)[:1000])
    save_state_sync(state)
    return result

@app.post("/api/payouts/{payout_id}/approve")
async def payout_approve(payout_id: str, req: RevenueApproval):
    result = approve_payout(state, payout_id, req.approved_by, req.note)
    if result.get("ok"):
        add_audit_sync("PAYOUT_APPROVED", payout_id + ": $" + f"{result['payout']['amount_usd']:.2f}")
        save_state_sync(state)
    return result

@app.post("/api/payouts/{payout_id}/reject")
async def payout_reject(payout_id: str, req: RevenueApproval):
    result = reject_payout(state, payout_id, req.approved_by, req.note)
    if result.get("ok"):
        add_audit_sync("PAYOUT_REJECTED", payout_id + ": " + req.note[:180])
        save_state_sync(state)
    return result

@app.get("/api/revenue/proposals")
async def revenue_proposals():
    return state.get("revenue", {}).get("proposals", [])

@app.get("/api/revenue/offers")
async def revenue_offers():
    return state.get("revenue", {}).get("offers", [])

@app.get("/api/revenue/status")
async def revenue_status():
    rv = state.get("revenue", {})
    return {"stripe_configured": stripe_configured(), "offers": rv.get("offers", []), "verified_revenue_usd": rv.get("verified_revenue_usd", 0.0), "note": "Revenue is counted only after a real customer payment is independently verified."}

@app.get("/offer/{proposal_id}")
async def public_offer(proposal_id: str):
    offer = next((x for x in state.get("revenue", {}).get("offers", []) if x.get("proposal_id") == proposal_id), None)
    if not offer:
        return {"error":"Offer not found"}
    from fastapi.responses import HTMLResponse
    return HTMLResponse(offer_html(offer))

@app.post("/api/revenue/proposals/{proposal_id}/approve")
async def approve_revenue(proposal_id: str, req: RevenueApproval):
    proposals = state.get("revenue", {}).setdefault("proposals", [])
    p = next((x for x in proposals if x.get("id") == proposal_id), None)
    if not p:
        return {"error": "Revenue proposal not found"}
    if p.get("status") != "PENDING_APPROVAL":
        return {"error": "Proposal is not awaiting approval", "status": p.get("status")}
    p["status"] = "APPROVED"
    p["approved_at"] = time.time()
    p["approved_by"] = req.approved_by
    p["approval_note"] = req.note
    state["revenue"].setdefault("approved", []).insert(0, p)
    state["revenue"]["approved"] = state["revenue"]["approved"][:100]
    base_url = os.getenv("FORGE_PUBLIC_URL", "https://quantum-forge-v52h.onrender.com")
    offer = build_offer(p, base_url)
    state["revenue"].setdefault("offers", []).insert(0, offer)
    state["revenue"]["offers"] = state["revenue"]["offers"][:100]
    if stripe_configured():
        checkout = create_payment_link(offer["title"], offer["description"], offer["price_usd"], base_url + "/offer/" + p["id"])
        if checkout.get("ok"):
            offer.update({"status":"LIVE","payment_url":checkout.get("payment_url"),"stripe_product_id":checkout.get("product_id"),"stripe_price_id":checkout.get("price_id"),"stripe_payment_link_id":checkout.get("payment_link_id")})
            add_audit_sync("REVENUE_CHECKOUT_CREATED", f"{offer['title']} checkout created at {offer.get('payment_url')}")
        else:
            offer["status"]="CHECKOUT_ERROR"; offer["checkout_error"]=checkout.get("error")
            add_audit_sync("REVENUE_CHECKOUT_ERROR", checkout.get("error","unknown checkout error"))
    else:
        offer["status"]="READY_FOR_CHECKOUT"
        add_audit_sync("REVENUE_OFFER_BUILT", f"{offer['title']} built; Stripe is not configured, so no payment checkout was created.")
    state["revenue"]["checkout_configured"] = stripe_configured()
    save_state_sync(state)
    return {"ok": True, "proposal": p, "offer": offer, "next": "Share the published offer page and use verified customer payments as the revenue source."}

@app.post("/api/revenue/proposals/{proposal_id}/reject")
async def reject_revenue(proposal_id: str, req: RevenueApproval):
    proposals = state.get("revenue", {}).setdefault("proposals", [])
    p = next((x for x in proposals if x.get("id") == proposal_id), None)
    if not p:
        return {"error": "Revenue proposal not found"}
    if p.get("status") != "PENDING_APPROVAL":
        return {"error": "Proposal is not awaiting approval", "status": p.get("status")}
    p["status"] = "REJECTED"
    p["rejected_at"] = time.time()
    p["rejected_by"] = req.approved_by
    p["rejection_note"] = req.note
    state["revenue"].setdefault("rejected", []).insert(0, p)
    state["revenue"]["rejected"] = state["revenue"]["rejected"][:100]
    add_audit_sync("REVENUE_REJECTED", f"{p.get('title','proposal')} rejected by {req.approved_by}")
    save_state_sync(state)
    return {"ok": True, "proposal": p}

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
    ensure_revenue_project()
    global cycle_task
    if cycle_task is None or cycle_task.done():
        cycle_task = asyncio.create_task(autonomous_cycle())

@app.on_event("shutdown")
async def shutdown():
    global cycle_task
    if cycle_task:
        cycle_task.cancel()
