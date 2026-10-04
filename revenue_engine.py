from __future__ import annotations
import json, os, time, uuid
from html import escape
from urllib.parse import urlencode
from urllib.request import Request, urlopen

STRIPE_API = "https://api.stripe.com/v1"

def stripe_configured() -> bool:
    return bool(os.getenv("STRIPE_SECRET_KEY","").strip())

def _stripe(path: str, data: dict):
    key=os.getenv("STRIPE_SECRET_KEY","").strip()
    if not key:
        return {"ok":False,"error":"STRIPE_SECRET_KEY is not configured"}
    body=urlencode({k:v for k,v in data.items() if v is not None}).encode()
    req=Request(STRIPE_API+path,data=body,headers={"Authorization":"Bearer "+key,"Content-Type":"application/x-www-form-urlencoded"},method="POST")
    try:
        with urlopen(req,timeout=30) as r:
            return {"ok":True,"data":json.loads(r.read().decode())}
    except Exception as exc:
        return {"ok":False,"error":f"{type(exc).__name__}: {exc}"}

def create_payment_link(title: str, description: str, amount_usd: float, success_url: str|None=None) -> dict:
    cents=max(100,int(round(float(amount_usd)*100)))
    product=_stripe("/products",{"name":title[:250],"description":description[:4000]})
    if not product.get("ok"): return product
    price=_stripe("/prices",{"currency":"usd","unit_amount":cents,"product":product["data"]["id"]})
    if not price.get("ok"): return price
    data={"line_items[0][price]":price["data"]["id"],"line_items[0][quantity]":"1"}
    if success_url:
        data["after_completion[type]"]="redirect"
        data["after_completion[redirect][url]"]=success_url
    link=_stripe("/payment_links",data)
    if not link.get("ok"): return link
    return {"ok":True,"product_id":product["data"]["id"],"price_id":price["data"]["id"],
            "payment_link_id":link["data"]["id"],"payment_url":link["data"].get("url"),
            "amount_usd":amount_usd}

def build_offer(proposal: dict, base_url: str) -> dict:
    report=proposal.get("description","").strip()
    title="Quantum Forge Research Brief"
    price=49.0
    if "consult" in report.lower() or "business" in report.lower():
        title="Quantum Forge Strategy & Research Brief"
        price=79.0
    return {"id":str(uuid.uuid4()),"created_at":time.time(),"proposal_id":proposal["id"],
            "title":title,"description":report[:5000],"price_usd":price,"status":"DRAFT",
            "payment_url":None,"public_path":"/offer/"+proposal["id"],"base_url":base_url.rstrip("/")}

def offer_html(offer: dict) -> str:
    pay=offer.get("payment_url")
    if pay:
        button='<a class="buy" href="'+escape(pay)+'">BUY THIS RESEARCH BRIEF — $'+format(offer["price_usd"],".2f")+'</a>'
    else:
        button='<div class="pending">Payment checkout is not connected yet. The owner must configure Stripe and approve the offer.</div>'
    return '<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+escape(offer["title"])+'</title><style>body{font-family:system-ui;background:#080b12;color:#eee;max-width:760px;margin:0 auto;padding:40px}h1{font-size:34px}.box{background:#111827;padding:28px;border-radius:18px}.buy{display:inline-block;padding:15px 20px;background:#f5c542;color:#111;text-decoration:none;font-weight:800;border-radius:10px}.pending{padding:14px;background:#222938;border-radius:10px}</style></head><body><div class="box"><div>⚛ QUANTUM FORGE</div><h1>'+escape(offer["title"])+'</h1><p>'+escape(offer["description"])+'</p><h2>$'+format(offer["price_usd"],".2f")+'</h2>'+button+'</div></body></html>'
