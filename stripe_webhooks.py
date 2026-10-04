from __future__ import annotations
import hashlib, hmac, json, time

def verify_signature(payload: bytes, header: str, secret: str, tolerance: int = 300) -> bool:
    if not secret or not header: return False
    try:
        parts={}
        for item in header.split(","):
            k,_,v=item.partition("="); parts.setdefault(k,[]).append(v)
        ts=int(parts.get("t",["0"])[0])
        if abs(int(time.time())-ts)>tolerance:return False
        expected=hmac.new(secret.encode(),f"{ts}.".encode()+payload,hashlib.sha256).hexdigest()
        return any(hmac.compare_digest(expected,v) for v in parts.get("v1",[]))
    except Exception:return False

def parse_event(payload: bytes): return json.loads(payload.decode("utf-8"))
