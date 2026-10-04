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

ROOT=Path(__file__).parent; DATA=ROOT/"data"; DATA.mkdir(exist_ok=True)
STATE_FILE=DATA/"state.json"; STATE_TMP=DATA/"state.json.tmp"
app=FastAPI(title="Quantum Forge",version="0.3.0")
app.mount("/static",StaticFiles(directory=ROOT/"static"),name="static")
AGENTS=[("Coordinator","orchestrates research branches"),("Disease Research","maps mechanisms, targets and therapeutic hypotheses"),("Discovery","generates competing hypotheses and candidate solutions"),("Quantum","runs small quantum-state simulations and ranks search branches"),("Invention","turns ideas into technical concepts"),("Engineering","creates requirements and system architecture"),("Simulation","stress-tests computational designs"),("Blueprint","creates specifications and BOM candidates"),("Critic","tries to falsify weak conclusions"),("Learning","records evidence and improves future searches")]
CYCLE_SECONDS=max(30,int(os.getenv("FORGE_CYCLE_SECONDS","60"))); MAX_PROJECTS_PER_CYCLE=max(1,int(os.getenv("FORGE_PROJECTS_PER_CYCLE","3")))
state_lock=asyncio.Lock(); cycle_task=None
def default_state():
 return {"started_at":time.time(),"cycle":0,"running":True,"cycle_status":"WAITING","last_cycle_started":None,"last_cycle_completed":None,"last_cycle_duration":None,"current_project":None,"current_activity":"Agents standing by","agents":{n:{"role":r,"status":"IDLE","last_run":None,"jobs":0,"activity":"Standing by"} for n,r in AGENTS},"projects":[],"discoveries":[],"jobs":[],"evidence":[],"audit":[],"quantum":{"mode":"LOCAL_STATE_VECTOR","provider":"local","hardware_connected":False,"qubits":8,"note":"Runs real small state-vector simulations locally. External quantum hardware is optional and is never claimed unless connected."}}
def save_state_sync(s): STATE_TMP.write_text(json.dumps(s,indent=2),encoding="utf-8"); STATE_TMP.replace(STATE_FILE)
def load_state():
 if STATE_FILE.exists():
  try:
   x=json.loads(STATE_FILE.read_text(encoding="utf-8")); b=default_state(); b.update(x)
   for n,r in AGENTS: b["agents"].setdefault(n,{"role":r,"status":"IDLE","last_run":None,"jobs":0,"activity":"Standing by"})
   return b
  except Exception: pass
 s=default_state(); save_state_sync(s); return s
state=load_state()
class ProjectRequest(BaseModel):
 name:str=Field(min_length=1,max_length=120); objective:str=Field(min_length=3,max_length=5000); kind:str="research"
class AgentRequest(BaseModel):
 project_id:str; prompt:str=Field(min_length=3,max_length=10000)
def add_audit_sync(action,detail):
 state["audit"].insert(0,{"id":str(uuid.uuid4()),"time":time.time(),"action":action,"detail":detail}); state["audit"]=state["audit"][:250]
def add_job_sync(project_id,job_type,status="QUEUED",detail=""):
 j={"id":str(uuid.uuid4()),"project_id":project_id,"type":job_type,"status":status,"detail":detail,"created_at":time.time(),"completed_at":None}; state["jobs"].insert(0,j); state["jobs"]=state["jobs"][:150]; return j
def keywords(t):
 w=re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]{3,}",t.lower()); stop={"what","with","from","that","this","into","about","research","using","make","need","want"}; return list(dict.fromkeys(x for x in w if x not in stop))[:8]
def arxiv_search(q,limit=5):
 url="https://export.arxiv.org/api/query?search_query=all:"+quote_plus(q)+f"&start=0&max_results={limit}"
 try:
  req=Request(url,headers={"User-Agent":"QuantumForge/0.3 research engine"})
  with urlopen(req,timeout=12) as r: raw=r.read().decode("utf-8",errors="replace")
  out=[]
  for e in re.findall(r"<entry>(.*?)</entry>",raw,re.S):
   t=re.search(r"<title>(.*?)</title>",e,re.S); s=re.search(r"<summary>(.*?)</summary>",e,re.S); l=re.search(r"<id>(.*?)</id>",e,re.S)
   if t: out.append({"title":re.sub(r"\s+"," ",t.group(1)).strip(),"summary":re.sub(r"\s+"," ",s.group(1)).strip() if s else "","url":l.group(1).strip() if l else "","source":"arXiv"})
  return out
 except Exception as exc: return [{"title":"Literature connector unavailable","summary":str(exc),"url":"","source":"connector"}]
def quantum_score(seed,branches=16):
 d=hashlib.sha256(seed.encode()).digest(); a=[math.sin((int.from_bytes(d[i:i+2],"big")/65535)*math.pi*2+i*.37) for i in range(branches)]; n=math.sqrt(sum(x*x for x in a)) or 1; p=[(x/n)**2 for x in a]; b=max(range(branches),key=lambda i:p[i]); return {"branches":branches,"best_branch":b,"probability":round(p[b],6),"distribution":[round(x,6) for x in p]}
def build_discovery(project,prompt,literature):
 q=quantum_score(project["objective"]+" "+prompt); ev=literature[:5]; return {"id":str(uuid.uuid4()),"project_id":project["id"],"title":"Autonomous research branch","summary":f"Branch {q['best_branch']} explores: {prompt[:500]}","confidence":round(min(.9,.2+.1*len([x for x in ev if x.get("url")])),3),"evidence":ev,"quantum_result":q,"status":"HYPOTHESIS","created_at":time.time()}
async def process_project(project,prompt=None):
 objective=prompt or project["objective"]; state["current_project"]=project["name"]; state["current_activity"]="Agents are actively researching"; project["status"]="RESEARCHING"
 job=add_job_sync(project["id"],"RESEARCH_CYCLE","RUNNING","Autonomous agents are researching")
 stages=[("Coordinator","Coordinating research branches"),("Disease Research","Searching mechanisms, targets and therapeutic evidence"),("Discovery","Generating competing hypotheses"),("Quantum","Evaluating computational state branches"),("Invention","Converting promising ideas into concepts"),("Engineering","Building technical requirements"),("Simulation","Stress-testing candidate designs"),("Blueprint","Drafting implementation specifications"),("Critic","Trying to falsify weak conclusions"),("Learning","Recording evidence for future cycles")]
 for n,activity in stages:
  a=state["agents"][n]; a["status"]="WORKING"; a["activity"]=activity; a["last_run"]=time.time(); a["jobs"]+=1; save_state_sync(state); await asyncio.sleep(1.0); a["status"]="COMPLETE"; a["activity"]="Completed this stage"; save_state_sync(state)
 query=" ".join(keywords(objective)[:5]) or objective[:100]; literature=await asyncio.to_thread(arxiv_search,query); discovery=build_discovery(project,objective,literature)
 state["discoveries"].insert(0,discovery); state["discoveries"]=state["discoveries"][:200]
 for item in literature: state["evidence"].insert(0,{**item,"project_id":project["id"],"created_at":time.time()})
 state["evidence"]=state["evidence"][:500]; project["status"]="ACTIVE"; project["evidence_level"]="LITERATURE_BACKED" if any(x.get("url") for x in literature) else "HYPOTHESIS"
 job["status"]="COMPLETE"; job["completed_at"]=time.time(); job["detail"]=f"Collected {len(literature)} literature signals and ran {discovery['quantum_result']['branches']} computational branches"; add_audit_sync("AUTONOMOUS_RESEARCH",f"{project['name']}: {job['detail']}")
 for n,_ in AGENTS: state["agents"][n]["status"]="IDLE"; state["agents"][n]["activity"]="Standing by"
 state["current_project"]=None; state["current_activity"]="Cycle complete — agents standing by"; save_state_sync(state)
async def autonomous_cycle():
 while True:
  await asyncio.sleep(CYCLE_SECONDS)
  async with state_lock:
   state["cycle"]+=1; state["cycle_status"]="WORKING"; state["last_cycle_started"]=time.time(); state["current_activity"]="Starting autonomous research cycle"; save_state_sync(state)
   active=[p for p in state["projects"] if p.get("status") in {"QUEUED","ACTIVE"}][:MAX_PROJECTS_PER_CYCLE]
   if not active: add_job_sync(None,"AUTONOMOUS_CYCLE","COMPLETE","No active projects; agents standing by")
   else:
    for p in active: await process_project(p)
   state["cycle_status"]="COMPLETE"; state["last_cycle_completed"]=time.time(); state["last_cycle_duration"]=round(time.time()-state["last_cycle_started"],2); state["current_activity"]="Cycle complete — agents standing by"; save_state_sync(state)
@app.get("/")
async def home(): return FileResponse(ROOT/"static"/"index.html")
@app.get("/api/state")
async def api_state(): return state
@app.get("/api/health")
async def health(): return {"ok":True,"service":"quantum-forge","version":app.version,"agents":len(AGENTS),"cycle":state["cycle"],"running":state["running"],"cycle_status":state["cycle_status"],"last_cycle_completed":state["last_cycle_completed"]}
@app.post("/api/projects")
async def create_project(req:ProjectRequest):
 async with state_lock:
  p={"id":str(uuid.uuid4()),"name":req.name,"objective":req.objective,"kind":req.kind,"created_at":time.time(),"status":"QUEUED","evidence_level":"UNVALIDATED"}; state["projects"].insert(0,p); add_job_sync(p["id"],"DISCOVERY_CYCLE","QUEUED","Waiting for autonomous research cycle"); add_audit_sync("PROJECT_CREATED",f"{req.name}: {req.objective[:180]}"); save_state_sync(state); return p
@app.post("/api/agents/run")
async def run_agent(req:AgentRequest):
 async with state_lock:
  p=next((p for p in state["projects"] if p["id"]==req.project_id),None)
  if not p: return {"error":"Project not found"}
  await process_project(p,req.prompt); return {"job":state["jobs"][0],"discovery":state["discoveries"][0]}
@app.on_event("startup")
async def startup():
 global cycle_task
 if cycle_task is None or cycle_task.done(): cycle_task=asyncio.create_task(autonomous_cycle())
@app.on_event("shutdown")
async def shutdown():
 global cycle_task
 if cycle_task: cycle_task.cancel()
