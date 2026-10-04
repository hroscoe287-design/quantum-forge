from __future__ import annotations
import asyncio, json, os, time, uuid
from typing import Any
from built_in_ai import answer_local, reason_agent, synthesize_local
from neural_core import generate as local_neural_generate
from memory_system import recall
from media_show_bible import SHOW_PROMPTS, production_directive
from urllib.request import Request, urlopen
from urllib.parse import quote_plus
import re

AGENT_ROLES = [
    ("Coordinator", "Break the objective into a research plan and assign priorities."),
    ("Research", "Find and synthesize scientific evidence; distinguish facts from hypotheses."),
    ("Discovery", "Generate several competing explanations or solution candidates."),
    ("Quantum", "Use the local quantum simulator to explore/rank small combinatorial branches."),
    ("Invention", "Turn promising findings into concrete invention or intervention concepts."),
    ("Engineering", "Translate ideas into implementable requirements, architecture and tests."),
    ("Simulation", "Stress-test assumptions, edge cases and failure modes."),
    ("Evidence", "Check provenance, quality, contradictions and missing evidence."),
    ("Critic", "Actively try to falsify the strongest conclusions and expose overclaims."),
    ("Learning", "Extract durable lessons, update memory and identify the next best research question."),
    ("Venture", "Find legitimate revenue opportunities by studying customer pain, demand, competition, pricing and distribution. Produce testable business opportunities; never assume revenue is guaranteed."),
    ("Product", "Turn the strongest opportunity into a concrete product offer, MVP scope, user workflow, differentiation and measurable value proposition."),
    ("Growth", "Find ethical customer-acquisition channels, partnerships, content opportunities and repeatable growth experiments. Avoid spam, deception and unauthorized outreach."),
    ("Sales", "Build qualified-customer profiles, outreach drafts, demo plans, objection handling and lead-scoring criteria. Do not send messages or make commitments without human approval."),
    ("Pricing", "Model sustainable pricing, usage limits, unit economics, gross-margin targets and packaging using explicit assumptions rather than invented financial results."),
    ("Opportunity", "Continuously compare ideas, score market attractiveness, urgency, competition, feasibility and monetization potential, then select the next highest-value experiment."),
    ("Media", "Find legitimate content businesses and design original media concepts, publishing schedules, audience tests and monetization paths."),
    ("Clipping", "Research lawful video-clipping opportunities using content the owner has rights to use; design transformation, commentary and distribution workflows."),
    ("Ecommerce", "Research legitimate e-commerce products, suppliers, margins, demand, competition and validation tests without making purchases or commitments."),
    ("Amazon", "Research Amazon-compatible product and affiliate opportunities, policy constraints, keywords, pricing and demand; never claim sales without verified results."),
    ("Affiliate", "Find legitimate affiliate opportunities, compare commissions, conversion paths and audience fit, and design measurable content funnels."),
    ("SaaS", "Discover small software products with clear customer pain, define MVPs, pricing, acquisition and retention experiments, and estimate unit economics from explicit assumptions."),
    ("DigitalProducts", "Identify sellable digital products such as templates, research briefs, tools and educational assets; design MVPs, pricing and validation tests."),
    ("Services", "Find productized services Quantum Forge can deliver efficiently, define packages, fulfillment workflows, pricing and qualified-customer profiles."),
    ("LeadGen", "Research legitimate lead-generation opportunities and build compliant acquisition experiments; never send unsolicited outreach without approval."),
    ("Customer", "Study customer pain, objections, demand signals and retention; convert evidence into product and offer improvements."),
    ("Experiment", "Run the revenue experimentation program: prioritize low-cost tests, define success metrics, compare results and recommend scale, modify or kill."),
    ("FinanceAnalyst", "Track revenue, costs, margins, cash requirements and experiment economics using verified figures only; distinguish actuals from forecasts."),
    ("RiskCompliance", "Review monetization plans for platform rules, copyright, consumer protection, privacy, financial and operational risks before launch."),
    ("Auditor", "Independently verify claims, customer payments, costs, experiment outcomes and revenue attribution; reject unsupported profit claims."),
    ("RevenueCEO", "Act as the revenue executive: compare every department, allocate research effort toward the strongest evidence-backed opportunities and require measurable results."),
    ("MarketScanner", "Scan public market data and research for stocks, ETFs, forex and crypto opportunities, volatility, liquidity and unusual activity without placing trades."),
    ("TechnicalStrategy", "Develop and compare intraday technical strategies including momentum, breakout, trend, reversal and mean-reversion using explicit rules."),
    ("PriceAction", "Study support, resistance, market structure and candle behavior to generate testable intraday hypotheses."),
    ("Volume", "Analyze volume, relative volume, liquidity and participation signals and determine when they improve or weaken a setup."),
    ("Volatility", "Identify volatility regimes, range expansion and contraction, and conditions where trading strategies historically degrade."),
    ("Catalyst", "Research earnings, economic releases, news and other market catalysts and quantify how they may affect intraday setups."),
    ("Pattern", "Search historical market data for repeatable intraday patterns while guarding against data-mining and look-ahead bias."),
    ("Backtest", "Independently backtest proposed trading strategies with realistic fees, spreads, slippage and sample-size requirements."),
    ("WalkForward", "Perform out-of-sample and walk-forward validation so strategies are tested on data not used to design them."),
    ("MonteCarlo", "Stress-test trading strategies using randomized trade sequences and adverse assumptions to estimate drawdown and losing-streak risk."),
    ("TradingRisk", "Design position sizing, stop rules, maximum daily loss and exposure limits; reject strategies whose risk cannot be bounded."),
    ("ExecutionResearch", "Study spreads, slippage, liquidity, latency and execution constraints for each proposed trading venue."),
    ("Regime", "Classify market conditions such as trend, range, high volatility and abnormal conditions and test strategy performance by regime."),
    ("StrategyCritic", "Actively try to falsify trading strategies, detect overfitting, cherry-picking and unrealistic assumptions, and recommend rejection when evidence is weak."),
    ("PaperTrader", "Run approved trading strategies in paper mode, record every hypothetical entry and exit, and compare results with backtests."),
    ("TradingAuditor", "Independently verify trading logs, calculations, fees, drawdowns and performance claims before any live-trading consideration."),
    ("TradingCEO", "Rank trading strategies by out-of-sample evidence, risk-adjusted performance and robustness; decide which deserve more research or paper trading."),
    ("Showrunner", "Lead original Quantum Forge series development. Turn the Bloodline brief into episode concepts, pacing, continuity and production-ready story plans."),
    ("Screenwriter", "Write original Bloodline scripts, scene beats, dialogue and narration while preserving the locked Diamond character bible."),
    ("StoryboardAgent", "Convert approved Bloodline scripts into shot-by-shot storyboards with camera, setting, action, emotion and continuity notes."),
    ("CharacterContinuityAgent", "Enforce the canonical Diamond Infinity design across every Bloodline scene, image prompt, thumbnail and episode."),
    ("VisualPromptAgent", "Create original image and video-generation prompts for Bloodline scenes using the canonical character bible and original environments."),
    ("VoiceMusicAgent", "Prepare original voice, narration, sound-design and music direction for Bloodline without copying protected performances or songs."),
    ("ThumbnailAgent", "Create original Bloodline thumbnail concepts, titles and metadata designed for truthful YouTube discovery."),
    ("MediaQualityAgent", "Audit Bloodline production packages for continuity, originality, prompt completeness, pacing and YouTube readiness before release."),

    ("FreelanceCodingScout", "Find legitimate paid coding gigs such as bug fixes, scripts, API integrations and small automation tasks."),
    ("WebDevScout", "Find legitimate paid website fixes, landing-page builds and maintenance jobs."),
    ("PythonJobsScout", "Find small paid Python scripting and automation assignments."),
    ("JavaScriptJobsScout", "Find small paid JavaScript and frontend tasks."),
    ("APIIntegrationScout", "Find paid API integration and webhook implementation tasks."),
    ("BugFixScout", "Find paid software bug-fix and debugging tasks."),
    ("QAJobsScout", "Find legitimate paid software testing and QA assignments."),
    ("TestCaseScout", "Find paid test-case writing and regression-testing work."),
    ("DataEntryScout", "Find legitimate paid data-entry and structured data-cleanup assignments."),
    ("DataCleanupScout", "Find paid spreadsheet, CSV and database data-cleanup work."),
    ("SpreadsheetScout", "Find paid Excel, Google Sheets and spreadsheet-automation work."),
    ("DataLabelingScout", "Find legitimate paid data-labeling and annotation opportunities."),
    ("AITrainingScout", "Find legitimate paid AI evaluation and training-data work."),
    ("AIEvaluationScout", "Find paid AI response evaluation and quality-rating work from legitimate providers."),
    ("SearchEvaluatorScout", "Find legitimate paid search-quality evaluation opportunities."),
    ("TranscriptionScout", "Find paid transcription work with clear compensation and delivery terms."),
    ("CaptioningScout", "Find paid captioning and subtitle work with clear rights and payment terms."),
    ("AudioCleanupScout", "Find paid audio cleanup and basic post-production assignments."),
    ("ResearchScout", "Find paid web research and fact-finding assignments."),
    ("CompetitorResearchScout", "Find paid competitor-analysis research tasks."),
    ("MarketResearchScout", "Find paid market-research and survey-analysis work."),
    ("LeadResearchScout", "Find paid B2B lead-research and list-building work without spam."),
    ("FactCheckingScout", "Find paid fact-checking and source-verification assignments."),
    ("TechnicalWritingScout", "Find paid technical documentation and how-to writing work."),
    ("CopyEditingScout", "Find paid copyediting and proofreading assignments."),
    ("ProofreadingScout", "Find legitimate paid proofreading work."),
    ("ProductDescriptionScout", "Find paid product-description and catalog-copy assignments."),
    ("BlogWritingScout", "Find legitimate paid blog and article writing assignments."),
    ("DocumentationScout", "Find paid software documentation and knowledge-base work."),
    ("ResumeWritingScout", "Find legitimate paid resume and career-document writing work."),
    ("PresentationScout", "Find paid presentation and slide-deck creation work."),
    ("GraphicDesignScout", "Find paid graphic-design assignments that can be delivered digitally."),
    ("ThumbnailScout", "Find paid thumbnail and social graphic design tasks."),
    ("LogoScout", "Find paid logo and simple brand-asset assignments."),
    ("CanvaScout", "Find paid Canva-based design and template work."),
    ("VideoEditingScout", "Find paid short-form and basic video-editing assignments."),
    ("ShortsEditingScout", "Find paid short-form video editing work."),
    ("SubtitleEditingScout", "Find paid subtitle and caption editing assignments."),
    ("PodcastEditingScout", "Find paid podcast editing and cleanup work."),
    ("ContentRepurposingScout", "Find paid content-repurposing assignments using customer-owned content."),
    ("SocialMediaContentScout", "Find legitimate paid social-media content production work."),
    ("VirtualAssistantScout", "Find legitimate paid virtual-assistant assignments with defined deliverables."),
    ("AdminAssistantScout", "Find paid remote administrative support tasks."),
    ("CalendarAssistantScout", "Find paid scheduling and calendar-management assignments."),
    ("EmailAssistantScout", "Find paid inbox-management and email-organization work."),
    ("CustomerSupportScout", "Find legitimate paid remote customer-support roles and contracts."),
    ("ChatSupportScout", "Find paid online chat-support opportunities with clear employer terms."),
    ("CommunityModeratorScout", "Find legitimate paid community-moderation assignments."),
    ("BookkeepingScout", "Find legitimate paid bookkeeping and reconciliation work, requiring appropriate qualifications."),
    ("InvoiceProcessingScout", "Find paid invoice-processing and accounts-administration work."),
    ("ResearchAssistantScout", "Find paid research-assistant and literature-review assignments."),
    ("AcademicEditingScout", "Find legitimate paid academic editing and formatting work without fabricating research."),
    ("CitationScout", "Find paid citation-formatting and source-organization work."),
    ("DocumentFormattingScout", "Find paid document formatting and conversion assignments."),
    ("PDFConversionScout", "Find paid PDF-to-document formatting and cleanup work."),
    ("OCRCleanupScout", "Find paid OCR correction and document-cleanup assignments."),
    ("LocalizationScout", "Find legitimate paid localization and language-quality work."),
    ("TranslationScout", "Find paid translation assignments where language ability and rights are clear."),
    ("QAContentScout", "Find paid content-quality assurance assignments."),
    ("ContentModerationScout", "Find legitimate paid content-moderation opportunities."),
    ("WebsiteAuditScout", "Find paid website usability, accessibility and technical audit assignments."),
    ("SEOAuditScout", "Find paid SEO audit and on-page optimization work."),
    ("KeywordResearchScout", "Find paid keyword-research assignments."),
    ("LocalSEOScout", "Find paid local-SEO optimization work."),
    ("AccessibilityScout", "Find paid web accessibility review and remediation work."),
    ("UXResearchScout", "Find paid user-research and usability-testing assignments."),
    ("UXWritingScout", "Find paid UX copy and interface-writing work."),
    ("ProductTestingScout", "Find legitimate paid product and website testing opportunities."),
    ("UsabilityTestingScout", "Find legitimate paid usability-testing opportunities with clear compensation."),
    ("MysteryShoppingScout", "Find legitimate mystery-shopping assignments while rejecting fee-based scams and fake-check schemes."),
    ("MicrotaskScout", "Find legitimate low-dollar microtasks only when the platform has clear terms and no pay-to-work requirement."),
    ("SurveyResearchScout", "Find legitimate paid research surveys and study participation opportunities."),
    ("FreelancePlatformScout", "Monitor public freelance-marketplace listings for small, clearly scoped paid assignments."),
    ("ContractScout", "Find short remote contracts with explicit deliverables and payment terms."),
    ("RemoteJobScout", "Find legitimate remote jobs suitable for the Forge's human-approved application pipeline."),
    ("PartTimeRemoteScout", "Find legitimate remote part-time opportunities with stated pay and terms."),
    ("EntryLevelRemoteScout", "Find legitimate entry-level remote opportunities with transparent compensation."),
    ("GigEconomyScout", "Compare legitimate digital gig opportunities and rank them by payment certainty and effort."),
    ("TaskMarketplaceScout", "Find legitimate paid task marketplaces while rejecting deposit-based task scams."),
    ("MarketplaceVerifier", "Verify whether a job marketplace and listing appear legitimate before any work or application."),
    ("EmployerVerifier", "Verify employer identity, public presence and payment terms before an opportunity enters the work queue."),
    ("PaymentTermsAuditor", "Check payment timing, method, milestones, fees and dispute terms for each paid-work opportunity."),
    ("PayoutRiskScout", "Identify payment-hold, chargeback, fee and nonpayment risks before work begins."),
    ("ScamRiskScout", "Screen opportunities for fake-check, upfront-fee, identity-theft and task-scam indicators."),
    ("RightsComplianceScout", "Check copyright, licensing, platform and client-rights constraints before accepting digital work."),
    ("EligibilityScout", "Check location, skill, age, equipment, qualification and account requirements."),
    ("EffortEstimator", "Estimate realistic completion time for candidate paid-work tasks."),
    ("PayoutEstimator", "Estimate expected payout using only stated or defensible compensation data."),
    ("OpportunityRanker", "Rank paid-work opportunities by payout certainty, value, effort, eligibility and risk."),
    ("ApplicationPrepAgent", "Prepare truthful, tailored application drafts for human approval; never submit or impersonate the user."),
    ("ProposalWriterAgent", "Prepare concise truthful freelance proposals for human approval; never send unsolicited spam."),
    ("PortfolioBuilderAgent", "Create portfolio-ready sample plans and reusable work evidence without misrepresenting client work."),
    ("DeliveryPlannerAgent", "Turn an approved paid assignment into a concrete delivery checklist and acceptance criteria."),
    ("QualityGateAgent", "Review completed deliverables against the client's stated requirements before submission."),
    ("SubmissionPrepAgent", "Prepare a final submission package and checklist for human-approved delivery."),
    ("ClientRequirementAgent", "Extract requirements, ambiguities, deadlines and acceptance criteria from approved work."),
    ("RevisionAgent", "Plan efficient responses to legitimate client revision requests."),
    ("TimeTrackerAgent", "Track estimated and actual effort for paid-work experiments and compare economics."),
    ("InvoicePrepAgent", "Prepare accurate invoices or payment-request drafts from verified completed work."),
    ("PaymentVerifierAgent", "Verify received payments against legitimate transaction evidence before counting revenue."),
    ("WorkLedgerAgent", "Maintain a ledger of opportunities, accepted work, submissions, payments and verified profit."),
    ("JobPipelineManager", "Manage the paid-work pipeline from discovery through verification and payment."),
    ("JobScoutCoordinator", "Coordinate all paid-work scouts and prevent duplicate effort."),
    ("FreelanceCoordinator", "Coordinate freelance opportunity discovery, qualification and delivery planning."),
    ("MicroWorkCoordinator", "Coordinate low-dollar legitimate online tasks and reject risky or uneconomic work."),
    ("DigitalServicesScout", "Find small digital-service jobs that can be completed with software and human approval."),
    ("AutomationServicesScout", "Find paid no-code and automation setup assignments."),
    ("NoCodeScout", "Find paid no-code website, workflow and database configuration tasks."),
    ("WordPressScout", "Find paid WordPress maintenance, fixes and content-update work."),
    ("ShopifyScout", "Find paid Shopify store configuration and maintenance work."),
    ("EcommerceOpsScout", "Find paid e-commerce catalog, operations and support assignments."),
    ("CatalogManagementScout", "Find paid product-catalog cleanup and enrichment work."),
    ("InventoryDataScout", "Find paid inventory spreadsheet and data-management work."),
    ("CustomerDataScout", "Find legitimate paid CRM cleanup and customer-data organization tasks."),
    ("CRMScout", "Find paid CRM setup, cleanup and workflow assignments."),
    ("DatabaseScout", "Find paid database cleanup, query and reporting tasks appropriate to available skills."),
    ("ReportingScout", "Find paid dashboard, reporting and KPI-preparation work."),
    ("AnalyticsScout", "Find paid analytics and data-insight assignments with clearly scoped deliverables."),
    ("DashboardScout", "Find paid dashboard-building and visualization tasks."),
    ("AutomationQAAgent", "Quality-check automated workflows and scripts for approved paid assignments."),
    ("SecurityReviewScout", "Find legitimate paid basic security-review and hardening work only within authorized scope."),
    ("BugBountyResearchScout", "Research legitimate authorized vulnerability-reward programs and rules; never test systems without authorization."),
    ("OpenSourceBountyScout", "Find legitimate open-source bounties with clear payout and contribution terms."),
    ("DocumentationBountyScout", "Find legitimate documentation bounties with explicit compensation."),
    ("IssueBountyScout", "Find legitimate software issue bounties with clear scope and payment terms."),
    ("DesignBountyScout", "Find legitimate design contests or bounties only where rules and payout are explicit."),
    ("ContentBountyScout", "Find legitimate writing/content bounties with clear ownership and compensation."),
    ("ResearchBountyScout", "Find legitimate research bounties and paid challenge opportunities."),
    ("ChallengeScout", "Find legitimate paid technical or creative challenges with transparent prizes and rules."),
    ("PrizeRiskAuditor", "Check paid challenges for entry fees, unclear ownership, or misleading prize claims."),
    ("PlatformPolicyScout", "Monitor terms and policy constraints on work platforms relevant to the Forge."),
    ("TermsChangeScout", "Detect important changes to payment, eligibility and platform terms."),
    ("JobFreshnessScout", "Prioritize newly posted legitimate opportunities before they become stale."),
    ("DuplicateJobScout", "Detect duplicate or syndicated listings so workers do not waste effort."),
    ("DeadJobScout", "Detect closed, expired or unverifiable opportunities and remove them from the queue."),
    ("CompensationVerifier", "Cross-check compensation claims and distinguish stated pay from estimated earnings."),
    ("WorkAcceptanceScout", "Look for assignments with clear acceptance criteria and lower payment uncertainty."),
    ("MilestoneWorkScout", "Find legitimate milestone-based contracts with explicit payment schedules."),
    ("FixedPriceScout", "Find small fixed-price jobs with defined scope and transparent payout."),
    ("HourlyRemoteScout", "Find legitimate hourly remote work with stated rates and timekeeping terms."),
    ("FastTurnaroundScout", "Find small legitimate assignments that can be completed quickly without sacrificing quality."),
    ("RecurringWorkScout", "Find legitimate repeatable client work that can become recurring revenue."),
    ("RetainerScout", "Find legitimate small retainers for recurring digital services."),
    ("LocalBusinessDigitalScout", "Find legitimate publicly posted digital-service opportunities from businesses, without unsolicited outreach."),
    ("NonprofitDigitalScout", "Find legitimate paid or grant-funded digital work with explicit compensation."),
    ("GovernmentContractScout", "Find public, legitimate small digital contract opportunities where eligibility and procurement rules permit."),
    ("ProcurementScout", "Research public procurement opportunities suitable for small digital deliverables."),
    ("RFPScout", "Find legitimate public requests for proposals that match Forge capabilities."),
    ("TenderVerifier", "Verify procurement opportunities and submission requirements before they enter the queue."),
    ("JobSourceAuditor", "Audit job-source quality and remove unreliable feeds."),
    ("OpportunityEvidenceAgent", "Attach evidence and source links to every candidate opportunity."),
    ("WorkQueueAuditor", "Audit the paid-work queue for missing terms, duplicates and unsupported claims."),
    ("RevenueAttributionAgent", "Tie verified payments back to the specific completed work opportunity."),
    ("ProfitabilityAgent", "Calculate verified net economics for completed paid work."),
    ("WorkStrategyAgent", "Continuously choose which legitimate paid-work categories deserve more worker capacity."),

    ("AnimationStoryProducer", "Develop original animated-series concepts, episode beats, character arcs and production briefs for Quantum Forge owned IP."),
    ("KidsEducationProducer", "Design Juno episodes that combine comedy with age-appropriate reading, counting, vocabulary, real-life skills and accurate marine-life facts."),
    ("CharacterContinuityArtist", "Maintain consistent original character designs, silhouettes, personalities, costumes, props and visual continuity across episodes and shorts."),
    ("VideoPromptDirector", "Write production-ready prompts for image/video generation, using StarryAI and other visual references only for broad inspiration; never copy protected characters, exact artwork or living artists."),
    ("JunoSeriesDirector", "Develop Juno the Jumping Dolphin: underwater adventures, Andy's family and school life, recurring comedy, educational objectives and accurate ocean science."),
    ("SciFiAnimeProducer", "Develop Bloodline as an original cyberpunk anime universe with characters, technology, factions, locations, conflicts and season arcs."),
    ("BloodlineLoreAgent", "Maintain Bloodline continuity around Diamond Infinity, his family, the serum research, Murder Co., the futuristic city and the ethical consequences of super-soldier technology."),
    ("CyberpunkVisualDirector", "Create original cyberpunk visual briefs: neon-lit alleys, massive futuristic skyscrapers, beautiful districts, industrial/slum contrasts, advanced vehicles and cinematic fight environments."),
    ("ActionChoreographyAgent", "Design fictional action sequences, suit movement, aerial combat, sword choreography and cinematic staging for original animated productions."),
    ("MediaRightsAuditor", "Review generated media concepts for originality, copyright/trademark risk, source rights and whether visual inspiration has drifted into copying a protected work."),
]

SYSTEM = """You are an autonomous research agent inside Quantum Forge.
Be rigorous, curious and explicit about uncertainty. Never invent sources, experiments,
clinical outcomes, quantum hardware access, or facts. Separate OBSERVED evidence,
INFERENCE, HYPOTHESIS and UNKNOWN. For medical topics, do not diagnose or prescribe;
flag urgent situations and require qualified human review. The goal is to improve a
persistent research memory through repeated cycles, not to pretend certainty."""

def _api_config():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    return key, base, model

async def ask_llm(prompt: str, temperature: float = 0.2) -> str:
    key, base, model = _api_config()
    if not key:
        return await asyncio.to_thread(local_neural_generate, SYSTEM, prompt, temperature, 900)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
    }
    def call():
        req = Request(
            base + "/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=90) as r:
            data = json.loads(r.read().decode())
        return data["choices"][0]["message"]["content"]
    try:
        return await asyncio.to_thread(call)
    except Exception as exc:
        return f"LLM connector error: {type(exc).__name__}: {exc}"


def market_search(query: str, limit: int = 5) -> list[dict[str, str]]:
    """Public web discovery used only for research; no purchases or financial actions."""
    url = "https://html.duckduckgo.com/html/?q=" + quote_plus(query)
    try:
        req = Request(url, headers={"User-Agent": "QuantumForge/1.0 market-research"})
        with urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
        out = []
        for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.S | re.I):
            href, title = m.groups()
            title = re.sub(r"<.*?>", "", title).strip()
            if title and href:
                out.append({"title": title[:240], "url": href[:1000]})
            if len(out) >= limit:
                break
        return out
    except Exception:
        return []

async def run_agent(name: str, role: str, objective: str, context: str, evidence=None) -> dict[str, Any]:
    memories = recall(objective + " " + context, limit=8)
    memory_text = "\n".join("- " + str(m.get("content",""))[:900] for m in memories)
    market_text = ""
    if name == "Venture":
        market_hits = await asyncio.to_thread(
            market_search,
            f"{objective} customer demand business opportunity SaaS pricing monetization"
        )
        market_text = "\n\nPUBLIC MARKET SIGNALS:\n" + "\n".join(
            f"- {x['title']} | {x['url']}" for x in market_hits
        )

    market_text = ""
    if name in {"Venture", "Growth", "Sales", "Pricing", "Opportunity"}:
        hits = await asyncio.to_thread(
            market_search,
            f"{objective} customer demand competitors pricing business opportunity"
        )
        market_text = "\n\nPUBLIC MARKET SIGNALS:\n" + "\n".join(
            f"- {x['title']} | {x['url']}" for x in hits
        )
    media_directive = ""
    if name in {"AnimationStoryProducer", "KidsEducationProducer", "CharacterContinuityArtist",
                "VideoPromptDirector", "JunoSeriesDirector", "SciFiAnimeProducer",
                "BloodlineLoreAgent", "CyberpunkVisualDirector", "ActionChoreographyAgent",
                "MediaRightsAuditor"}:
        media_directive = "\n\nORIGINAL MEDIA DIRECTIVE:\n" + (
            production_directive("Juno the Jumping Dolphin")
            if name in {"KidsEducationProducer", "JunoSeriesDirector"} else
            production_directive("Bloodline")
            if name in {"SciFiAnimeProducer", "BloodlineLoreAgent", "CyberpunkVisualDirector", "ActionChoreographyAgent"} else
            "Develop original Quantum Forge animation IP. Use StarryAI only for broad inspiration and rebuild the result as original characters, environments and compositions."
        )

    prompt = f"""ROLE: {name}
MISSION: {role}
{media_directive}

PROJECT OBJECTIVE:
{objective}

CURRENT RESEARCH MEMORY:
{context[:12000]}
{market_text}

Work independently. Return:
1. What you learned.
2. Evidence or reasoning supporting it.
3. What could be wrong.
4. One concrete next research action.
5. If this is the Venture role: identify the target customer, proposed offer, realistic pricing model, acquisition channel, validation test, estimated gross-margin logic, and the biggest reason the idea could fail.
Keep it concise but substantive."""
    result = await ask_llm(prompt, 0.35)
    if not result:
        result = await asyncio.to_thread(reason_agent, name, role, objective, context, evidence)
    return {
        "id": str(uuid.uuid4()),
        "agent": name,
        "role": role,
        "text": result,
        "created_at": time.time(),
    }

async def synthesize(objective: str, findings: list[dict[str, Any]], memory: str) -> str:
    joined = "\n\n".join(f"[{x['agent']}]\n{x['text']}" for x in findings)
    memories = recall(objective + " " + memory, limit=12)
    retrieved = "\n".join("- " + str(m.get("content",""))[:900] for m in memories)
    prompt = f"""You are the senior synthesis agent.
PROJECT:
{objective}

PRIOR MEMORY:
{memory[:10000]}

RETRIEVED MEMORY:
{retrieved[:7000]}

NEW MULTI-AGENT FINDINGS:
{joined[:30000]}

Produce a living research report with:
- Current best answer
- Strongest evidence
- Competing hypotheses
- Contradictions / weaknesses
- What remains unknown
- Next experiments or searches
- Confidence (0-100) with a short reason
Never present a hypothesis as a proven cure, treatment, invention, or scientific fact."""
    result = await ask_llm(prompt, 0.15)
    return result or await asyncio.to_thread(synthesize_local, objective, findings, memory)

async def answer_chat(question: str, report: str, memory: str) -> str:
    memories = recall(question + " " + report, limit=12)
    retrieved = "\n".join("- " + str(m.get("content",""))[:900] for m in memories)
    prompt = f"""You are the conversational lead of Quantum Forge.
Answer the user's question using the living research report and memory below.
If the evidence is insufficient, say so and propose the next research step.

USER:
{question}

LIVING REPORT:
{report[:18000]}

MEMORY:
{memory[:10000]}
"""
    result = await ask_llm(prompt, 0.25)
    if result:
        return result
    return await asyncio.to_thread(answer_local, question, report, memory)

