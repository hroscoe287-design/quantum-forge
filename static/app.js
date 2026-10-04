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
  $("#agentList").innerHTML=Object.entries(s.agents).map(([n,a])=>'<div class="agent '+(a.status==="WORKING"?"working":a.status==="COMPLETE"?"complete":"")+'"><div><b>'+esc(n)+'</b><small>'+esc(a.role)+'</small><em>'+esc(a.activity||"Standing by")+'</em></div><span class="status">'+esc(a.status)+(a.status==="WORKING"?" <i class="pulse"></i>":"")+'</span></div>').join("");
  $("#projectList").innerHTML=s.projects.length?s.projects.map(p=>'<div class="item"><h3>'+esc(p.name)+'</h3><p>'+esc(p.objective)+'</p><span class="muted">'+esc(p.kind)+' • '+esc(p.evidence_level)+' • '+esc(p.status)+'</span></div>').join(""):'<div class="card">No projects yet.</div>';
  $("#discoveryList").innerHTML=s.discoveries.length?s.discoveries.map(d=>'<div class="item"><h3>'+esc(d.title)+'</h3><p>'+esc(d.summary)+'</p><span class="muted">HYPOTHESIS • confidence '+Math.round(d.confidence*100)+'%</span></div>').join(""):'<div class="card">No discovery branches yet.</div>';
  $("#auditList").innerHTML=s.audit.slice(0,30).map(a=>'<div class="item"><b>'+esc(a.action)+'</b><p>'+esc(a.detail)+'</p></div>').join("")||'<div class="card">Audit trail is empty.</div>';
 }catch(e){$("#currentActivity").textContent="Dashboard reconnecting…";}
}
$("#projectForm").addEventListener("submit",async e=>{e.preventDefault();const r=await fetch("/api/projects",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:$("#name").value,kind:$("#kind").value,objective:$("#objective").value})});if(r.ok){e.target.reset();await load();alert("Forge project started.");}});
document.querySelectorAll(".tab").forEach(b=>b.onclick=()=>{document.querySelectorAll(".tab,.panel").forEach(x=>x.classList.remove("active"));b.classList.add("active");$("#"+b.dataset.tab).classList.add("active");});
load();setInterval(load,2000);