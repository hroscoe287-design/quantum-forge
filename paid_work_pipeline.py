from __future__ import annotations
import hashlib, re, time, uuid
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

JOB_QUERIES = {
    "coding": "site:upwork.com/jobs OR site:freelancer.com/projects python bug fix small job paid",
    "data": "site:upwork.com/jobs OR site:freelancer.com/projects data entry spreadsheet cleanup paid",
    "writing": "site:upwork.com/jobs OR site:freelancer.com/projects proofreading technical writing paid",
    "design": "site:upwork.com/jobs OR site:freelancer.com/projects graphic design thumbnail paid",
    "video": "site:upwork.com/jobs OR site:freelancer.com/projects video editing shorts subtitles paid",
    "research": "site:upwork.com/jobs OR site:freelancer.com/projects web research market research paid",
    "ai": "site:upwork.com/jobs OR site:freelancer.com/projects AI evaluation data labeling paid",
    "assistant": "site:upwork.com/jobs OR site:freelancer.com/projects virtual assistant remote paid",
}

SCAM_TERMS = ("pay to apply", "buy equipment", "deposit", "unlock earnings", "crypto deposit",
              "guaranteed income", "money mule", "reshipping", "send money", "gift card")

def _search(query: str, limit: int = 8) -> list[dict]:
    url = "https://html.duckduckgo.com/html/?q=" + quote_plus(query)
    try:
        req = Request(url, headers={"User-Agent": "QuantumForge/paid-work-research"})
        with urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
        out = []
        for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.S|re.I):
            title = re.sub(r"<.*?>", "", m.group(2)).strip()
            if title:
                out.append({"title": title[:300], "url": m.group(1)[:1200]})
            if len(out) >= limit:
                break
        return out
    except Exception as exc:
        return [{"title":"Job-source connector error: "+type(exc).__name__, "url":""}]

def _score(title: str, url: str) -> tuple[float, list[str]]:
    text = (title + " " + url).lower()
    risk = [x for x in SCAM_TERMS if x in text]
    if risk:
        return 0.0, ["REJECT: suspicious compensation language"]
    score = 50.0
    if any(x in text for x in ("small", "quick", "simple", "fixed", "hourly")): score += 10
    if any(x in text for x in ("python", "data", "research", "writing", "design", "video", "testing", "assistant")): score += 10
    if "upwork.com" in url or "freelancer.com" in url: score += 10
    if any(x in text for x in ("telegram", "whatsapp", "cashapp", "gift card")): score -= 35
    return max(0, min(100, score)), ["Public listing discovered; payment and acceptance still require verification"]

def discover_paid_work(existing: list[dict] | None = None, per_category: int = 4) -> list[dict]:
    seen = {x.get("fingerprint") for x in (existing or [])}
    results = []
    for category, query in JOB_QUERIES.items():
        for hit in _search(query, per_category):
            fp = hashlib.sha256((hit["title"] + "|" + hit["url"]).encode()).hexdigest()[:16]
            if fp in seen: continue
            seen.add(fp)
            score, checks = _score(hit["title"], hit["url"])
            results.append({
                "id": str(uuid.uuid4()), "fingerprint": fp, "category": category,
                "title": hit["title"], "source_url": hit["url"], "discovered_at": time.time(),
                "score": score, "verification": "UNVERIFIED", "checks": checks,
                "status": "CANDIDATE" if score >= 50 else "REJECTED",
                "next_action": "Verify scope, compensation, eligibility and platform terms before applying."
            })
    return sorted(results, key=lambda x: x["score"], reverse=True)

def build_work_brief(opportunity: dict) -> dict:
    return {
        "opportunity_id": opportunity["id"],
        "title": opportunity["title"],
        "category": opportunity["category"],
        "source_url": opportunity["source_url"],
        "status": "READY_FOR_OWNER_REVIEW",
        "required_checks": [
            "Confirm listing is still active",
            "Confirm exact compensation and acceptance criteria",
            "Confirm eligibility and required skills",
            "Prepare deliverable/proposal without impersonation",
            "Owner approval required before external submission or account action",
        ],
    }
