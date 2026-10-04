const $=s=>document.querySelector(s);
const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const fmt=t=>t?new Date(t*1000).toLocaleString():"—";
async function load(){
 try{
  const r=await fetch("/api/state?ts="+Date.now()); const s=await r.json();
  $("#cycle").textContent=s.cycle; $("#cycle2").textContent=s.cycle; $("#projectCount").textContent=s.projects.length; $("#discoveryCount").textContent=s.discoveries.length;
  $("#qmode").textContent=s.quantum.mode; $("#qnote").textContent=s.quantum.note;
  $("#cycleStatus").textContent=s.cycle_status||"WAITING"; $("#currentActivity").textContent=s.current_activity||"Agents standing by";
  $("#lastStarted").textContent=fmt(s.last_cycle_started); $("#lastCompleted").textContent=fmt(s.last_cycle_completed); $("#duration").textContent=s.last_cycle_duration!=null?s.last_cycle_duration+"s":"—";
  $("#agentList").innerHTML=Object.entries(s.agents).map(([n,a])=>'<div class="agent '+(a.status==="WORKING"?"working":a.status==="COMPLETE"?"complete":"")+'"><div><b>'+esc(n)+'</b><small>'+esc(a.role)+'</small><em>'+esc(a.activity||"Standing by")+'</em><p class="muted">'+esc(a.last_result||"")+'</p></div><span class="status">'+esc(a.status)+(a.status==="WORKING"?' <i class="pulse"></i>':"")+'</span></div>').join("");
  $("#projectList").innerHTML=s.projects.length?s.projects.map(p=>'<div class="item"><h3>'+esc(p.name)+'</h3><p>'+esc(p.objective)+'</p><span class="muted">'+esc(p.kind)+' • '+esc(p.evidence_level)+' • '+esc(p.status)+'</span></div>').join(""):'<div class="card">No projects yet.</div>';
  $("#discoveryList").innerHTML=s.discoveries.length?s.discoveries.map(d=>'<div class="item"><h3>'+esc(d.title)+'</h3><p>'+esc(d.summary)+'</p><span class="muted">HYPOTHESIS • agents '+(d.agent_findings?.length||0)+' • quantum branches '+(d.quantum_result?.branches||0)+'</span></div>').join(""):'<div class="card">No discovery branches yet.</div>';
  $("#reportText").textContent=s.report||"No synthesis yet. Start a project to create the first living report.";
  $("#memoryList").innerHTML=(s.memory||[]).slice(0,20).map(m=>'<div class="item"><p>'+esc(m.lesson)+'</p><span class="muted">'+fmt(m.time)+'</span></div>').join("")||'<div class="muted">Learning memory is empty.</div>';
  $("#chatLog").innerHTML=(s.chat||[]).map(m=>'<div class="chat '+(m.role==="user"?"user":"ai")+'"><b>'+esc(m.role==="user"?"YOU":"LEAD AI")+'</b><p>'+esc(m.content)+'</p></div>').join("");
  $("#auditList").innerHTML=s.audit.slice(0,30).map(a=>'<div class="item"><b>'+esc(a.action)+'</b><p>'+esc(a.detail)+'</p></div>').join("")||'<div class="card">Audit trail is empty.</div>';
 }catch(e){$("#currentActivity").textContent="Dashboard reconnecting…";}
}
$("#projectForm").addEventListener("submit",async e=>{e.preventDefault();const r=await fetch("/api/projects",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:$("#name").value,kind:$("#kind").value,objective:$("#objective").value})});if(r.ok){e.target.reset();await load();alert("Forge project started.");}});
$("#chatForm").addEventListener("submit",async e=>{e.preventDefault();const input=$("#chatInput"),msg=input.value.trim();if(!msg)return;input.disabled=true;try{await fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:msg})});input.value="";await load();}finally{input.disabled=false;}});
document.querySelectorAll(".tab").forEach(b=>b.onclick=()=>{document.querySelectorAll(".tab,.panel").forEach(x=>x.classList.remove("active"));b.classList.add("active");$("#"+b.dataset.tab).classList.add("active");});
load();setInterval(load,2000);