# Quantum Forge

Quantum Forge is an autonomous multi-agent AI research and invention workspace.

## Real agent architecture

- **10 specialized AI agents** run independent research passes.
- **Coordinator** decomposes objectives and organizes the cycle.
- **Research / Evidence / Critic** agents challenge evidence and overclaims.
- **Discovery / Invention / Engineering / Simulation** agents turn findings into competing designs and tests.
- **Quantum** runs a real local state-vector simulator for small search spaces.
- **Learning** writes durable research lessons into the Forge memory.
- A **Lead AI** synthesizes the findings into a living report and answers user questions.
- Public arXiv literature is retrieved and attached to discovery records.
- The dashboard shows actual agent state, last work, research cycles, memory, report and chat.

## Continuous learning

The Forge learns through persistent research memory, new evidence, previous findings, contradictions and repeated research cycles. It does **not** silently modify model weights or claim human-level general intelligence.

The language model is provided through an OpenAI-compatible `/v1/chat/completions` endpoint. Set:

- `OPENAI_API_KEY`
- `OPENAI_MODEL` (default: `gpt-5-mini`)
- optionally `OPENAI_BASE_URL` for another compatible provider.

Without a model key, the orchestration and quantum/literature pipeline still runs, but agents explicitly report that language reasoning is unavailable instead of fabricating results.

## Quantum boundary

The current quantum layer is a genuine local state-vector simulation. It is not physical quantum hardware. The "multiverse" workspace means parallel computational hypothesis branches; it does not communicate with alternate universes.

## Medical/scientific safety

Quantum Forge can organize evidence and generate hypotheses for research. It cannot guarantee cures, prove a treatment is safe, replace clinical trials, diagnose patients, or authorize experiments. Medical conclusions require qualified human review and independent validation.
