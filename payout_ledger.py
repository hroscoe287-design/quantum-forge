from __future__ import annotations
import os, time, uuid
from typing import Any

def ensure_ledger(state: dict[str, Any]) -> dict[str, Any]:
    state.setdefault("payout_ledger", [])
    state.setdefault("payout_settings", {
        "destination": "Linked Bank Account",
        "destination_label": os.getenv("FORGE_PAYOUT_DESTINATION_LABEL", ""),
        "daily_payout_enabled": True,
        "approval_required": True,
        "minimum_payout_usd": 1.00,
    })
    return state

def record_verified_result(state, amount_usd, kind, source, reference=""):
    ensure_ledger(state); amount=round(float(amount_usd),2)
    if amount<=0: raise ValueError("Verified result must be positive.")
    for x in state["payout_ledger"]:
        if x.get("type")=="REVENUE" and reference and x.get("reference")==reference: return x
    entry={"id":str(uuid.uuid4()),"created_at":time.time(),"type":"REVENUE","kind":kind[:80],
      "source":source[:160],"reference":reference[:200],"amount_usd":amount,
      "verification":"VERIFIED","payout_status":"ELIGIBLE"}
    state["payout_ledger"].insert(0,entry); return entry

def recompute_summary(state):
    ensure_ledger(state)
    revenue=sum(float(x["amount_usd"]) for x in state["payout_ledger"] if x.get("type")=="REVENUE" and x.get("verification")=="VERIFIED")
    costs=sum(float(x["amount_usd"]) for x in state["payout_ledger"] if x.get("type")=="COST" and x.get("verification")=="VERIFIED")
    paid=sum(float(x["amount_usd"]) for x in state["payout_ledger"] if x.get("type")=="PAYOUT" and x.get("payout_status")=="PAID")
    pending=sum(float(x["amount_usd"]) for x in state["payout_ledger"] if x.get("type")=="PAYOUT" and x.get("payout_status")=="APPROVED_PENDING_TRANSFER")
    available=max(0.0,revenue-costs-paid-pending)
    state["payout_summary"]={"verified_revenue_usd":round(revenue,2),"verified_costs_usd":round(costs,2),"available_profit_usd":round(available,2),"pending_payout_usd":round(pending,2),"paid_out_usd":round(paid,2)}
    state["revenue"]["verified_revenue_usd"]=round(revenue,2); state["revenue"]["verified_costs_usd"]=round(costs,2)
    return state["payout_summary"]

def request_daily_payout(state):
    ensure_ledger(state); recompute_summary(state); amount=state["payout_summary"]["available_profit_usd"]
    if next((x for x in state["payout_ledger"] if x.get("type")=="PAYOUT" and x.get("payout_status")=="PENDING_OWNER_APPROVAL"),None):
        return {"ok":False,"reason":"PAYOUT_ALREADY_PENDING","amount_usd":amount}
    if amount<float(state["payout_settings"].get("minimum_payout_usd",1.0)):
        return {"ok":False,"reason":"AVAILABLE_PROFIT_BELOW_MINIMUM","amount_usd":amount}
    entry={"id":str(uuid.uuid4()),"created_at":time.time(),"type":"PAYOUT","kind":"DAILY_PROFIT_PAYOUT","source":"Quantum Forge verified-profit ledger","amount_usd":round(amount,2),"destination":state["payout_settings"].get("destination","Linked Bank Account"),"destination_label":state["payout_settings"].get("destination_label",""),"payout_status":"PENDING_OWNER_APPROVAL"}
    state["payout_ledger"].insert(0,entry); recompute_summary(state); return {"ok":True,"payout":entry,"summary":state["payout_summary"]}

def approve_payout(state,payout_id,approved_by,note=""):
    p=next((x for x in state["payout_ledger"] if x.get("id")==payout_id and x.get("type")=="PAYOUT"),None)
    if not p:return {"ok":False,"error":"Payout not found"}
    if p.get("payout_status")!="PENDING_OWNER_APPROVAL":return {"ok":False,"error":"Payout is not awaiting approval"}
    p.update({"payout_status":"APPROVED_PENDING_TRANSFER","approved_at":time.time(),"approved_by":approved_by,"approval_note":note[:1000]})
    return {"ok":True,"payout":p,"summary":recompute_summary(state),"next":"Execute the authorized bank transfer through the connected payment provider."}

def reject_payout(state,payout_id,rejected_by,note=""):
    p=next((x for x in state.get("payout_ledger",[]) if x.get("id")==payout_id and x.get("type")=="PAYOUT"),None)
    if not p:return {"ok":False,"error":"Payout not found"}
    if p.get("payout_status")!="PENDING_OWNER_APPROVAL":return {"ok":False,"error":"Payout is not awaiting approval"}
    p.update({"payout_status":"REJECTED","rejected_at":time.time(),"rejected_by":rejected_by,"rejection_note":note[:1000]})
    return {"ok":True,"payout":p,"summary":recompute_summary(state)}
