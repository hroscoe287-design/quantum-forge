from __future__ import annotations
from typing import Any

BOSS_ROLES = [
    ("ChiefScienceOfficer", "Lead scientific research, evidence quality, criticism and learning. Coordinate Research, Discovery, Evidence, Critic and Learning."),
    ("BiomedicalBoss", "Lead disease and biomedical discovery. Coordinate evidence, computational biology, therapeutic hypotheses and experimental-design work. Never present an unvalidated hypothesis as a cure."),
    ("QuantumTechnologyBoss", "Lead quantum computing and quantum technology research, including simulation, algorithms and qualified hardware experiments."),
    ("InventionBoss", "Lead invention development from discovery through engineering, prototypes, blueprints, prior-art/IP research and commercialization readiness."),
    ("RevenueBoss", "Lead all legitimate monetization programs. Compare actual customer demand, costs, margins and verified revenue across business experiments."),
    ("TradingBoss", "Lead market and trading research. Require backtesting, out-of-sample validation, risk controls and paper-trading evidence before any live-trading consideration."),
    ("CommercializationBoss", "Find organizations and customers that could license, buy or sponsor promising inventions, research, software and services. Prepare compliant commercialization opportunities for approval."),
    ("AuditRiskBoss", "Independently audit scientific, business and trading claims. Reject unsupported results, fabricated revenue, unsafe medical claims and noncompliant actions."),
    ("MediaProductionBoss", "Lead the Bloodline production department from story development through quality control and YouTube-ready packaging. Require original IP and canonical character continuity.");
]

DEPARTMENTS = {
    "ChiefScienceOfficer": ["Coordinator","Research","Discovery","Evidence","Critic","Learning","Simulation"],
    "BiomedicalBoss": ["Research","Discovery","Evidence","Critic","Simulation","Invention"],
    "QuantumTechnologyBoss": ["Quantum","Simulation","Engineering"],
    "InventionBoss": ["Invention","Engineering","Simulation","Evidence","Discovery"],
    "RevenueBoss": ["Venture","Product","Growth","Sales","Pricing","Media","Clipping","Ecommerce","Amazon","Affiliate","SaaS","DigitalProducts","Services","LeadGen","Customer","Experiment","FinanceAnalyst"],
    "TradingBoss": ["MarketScanner","TechnicalStrategy","PriceAction","Volume","Volatility","Catalyst","Pattern","Backtest","WalkForward","MonteCarlo","TradingRisk","ExecutionResearch","Regime","StrategyCritic","PaperTrader","TradingAuditor"],
    "CommercializationBoss": ["Venture","Product","Sales","Pricing","Customer","Opportunity","Services"],
    "AuditRiskBoss": ["RiskCompliance","Auditor","TradingAuditor","Evidence","Critic","StrategyCritic"],
    "MediaProductionBoss": ["Showrunner","Screenwriter","StoryboardAgent","CharacterContinuityAgent","VisualPromptAgent","VoiceMusicAgent","ThumbnailAgent","MediaQualityAgent"],
}

def boss_inputs(findings: list[dict[str, Any]], names: list[str], max_chars: int = 16000) -> str:
    selected = [x for x in findings if x.get("agent") in names]
    return "\n\n".join(f"[{x.get('agent')}]\n{x.get('text','')[:2200]}" for x in selected)[:max_chars]

def executive_report(
    boss_findings: list[dict[str, Any]],
    verified_revenue: float,
    verified_costs: float,
    cycle: int,
    research_count: int,
) -> str:
    lines = [
        f"QUANTUM FORGE EXECUTIVE REPORT — CYCLE {cycle}",
        f"Verified revenue: $"+f"{verified_revenue:.2f}",
        f"Verified costs: $"+f"{verified_costs:.2f}",
        f"Verified profit: $"+f"{verified_revenue - verified_costs:.2f}",
        f"Research findings reviewed: {research_count}",
        "",
        "DEPARTMENT BOSS REPORTS:",
    ]
    for x in boss_findings:
        lines.append(f"\n[{x.get('agent')}]\n{x.get('text','')[:3000]}")
    lines.append(
        "\nEXECUTIVE RULE: actual revenue must be verified from real payment records/results; "
        "forecasts, simulations and proposed opportunities are never counted as income. "
        "Medical discoveries remain hypotheses until qualified validation. Trading remains research/paper mode "
        "unless the owner explicitly authorizes a compliant live-trading connection."
    )
    return "\n".join(lines)[:28000]
