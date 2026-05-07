# AI for Silicon Design Paper List

Initial reading queue. This is intentionally a scaffold, not a finished survey.

## 1. Verification Agents

### FVDebug: An LLM-Driven Debugging Assistant for Automated Root Cause Analysis of Formal Verification Failures
- **Citation**: Bai, Bany Hamad, Ho, Suhaib, Ren (NVIDIA). arXiv:2510.15906, Sep 2025. [`pdf`](fvdebug-2510.15906.pdf)
- **Problem setting**: Automating root-cause analysis of formal verification (FV) counter-examples (CEXs) in RTL hardware design. Debugging FV failures currently consumes ~50% of verification engineers' time.
- **Workflow stage**: Formal verification debug loop — post-CEX, pre-fix.
- **Inputs to model**: CEX trace (waveform), RTL source, design spec document, JasperGold TCL setup scripts.
- **Tooling in the loop**: Cadence JasperGold 2023.12 (`visualize -why`, `get_signal_info` via TCL); o3-mini as the LLM backbone.
- **Key ideas**:
  1. *Causal Graph Synthesis* — recursively queries Jasper's `visualize -why` to build a DAG of signal events `(signal, cycle, value)` with causal edges; consolidates reconverging tree paths into a DAG.
  2. *Graph Scanner* — token-aware batched LLM analysis per node using **for-and-against prompting** (forces the model to argue both sides before flagging), preventing confirmation bias where the LLM rubberstamps RTL as "working as designed."
  3. *Insight Rover* — agentic hypothesis exploration initialized from scanner's suspicious nodes; maintains 3+ competing narratives, selects frontier nodes via LLM, iteratively refines with evidence; reduces search space >90% vs BFS.
  4. *Fix Generator* — ensemble of 5 prompting strategies (full context, suspicious focus, narrative focus, minimal, best-of); consensus across strategies boosts fix confidence.
- **Evaluation metric**: Quality@Best, NDCG@5, MRR, Kendall's τ (hypothesis quality); Pass@1, Pass@5 (functional fix correctness validated by re-running Jasper).
- **Claimed results**: 95.6% Quality@Best, 71.1% Pass@1, 86.8% Pass@5 on SVA-Eval-Human (38 real hardware failures). Handles 500K+ LoC industrial designs in ~5 min with 21–25 LLM calls.
- **Main limitation**: Multi-line/cross-module RTL fixes for complex processor designs (e.g. CVA6) remain future work. Currently tightly coupled to JasperGold's `visualize -why` API — not tool-agnostic.
- **Why it matters as a seed**: First end-to-end system closing the CEX→patch loop. Demonstrates that structured causal graphs + balanced LLM reasoning outperform flat-trace prompting by a large margin. Sets a concrete baseline and benchmark (SVA-Eval-Human) for the verification-agent wedge.

---

- Agentic debug for simulation failures, waveform analysis, assertion triage
- LLM tool-use systems that operate over structured logs, traces, and state machines
- Benchmarks for debugging tasks in hardware environments

## 2. LLMs for EDA Copilots

- Work on natural-language interfaces to RTL, constraints, Tcl flows, and simulator tooling
- Agent frameworks that coordinate multi-step design tasks with external tools
- Reliability and evaluation work for domain-specific coding agents

## 3. ML for Physical Design

- Placement optimization
- Routing and congestion prediction
- Timing closure prediction
- IR drop, power, and thermal modeling

## 4. Architecture Search and Co-Design

- Learned cost models for performance, area, and power
- Bayesian optimization / RL / evolutionary search for hardware parameters
- Hardware-software co-design for AI accelerators

## 5. Industry and Systems Case Studies

- TPU / Trainium / Inferentia / Maia / MTIA papers and disclosures
- Synopsys / Cadence / Siemens AI-for-EDA product and research material
- Startup landscape around verification copilots and chip-design agents

## Notes Template

For each paper, capture:

- Citation
- Problem setting
- Workflow stage in the chip lifecycle
- Inputs available to the model
- Tooling in the loop
- Evaluation metric
- Claimed productivity or PPA impact
- Main limitation
