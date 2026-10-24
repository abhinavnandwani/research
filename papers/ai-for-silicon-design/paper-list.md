# AI for Silicon Design Paper List

Initial reading queue. This is intentionally a scaffold, not a finished survey.

## 1. Verification Agents

### FVDebug: An LLM-Driven Debugging Assistant for Automated Root Cause Analysis of Formal Verification Failures

Yunsheng Bai, Ghaith Bany Hamad, Chia-Tung Ho, Syed Suhaib, and Haoxing Ren (NVIDIA), September 2025. [arXiv:2510.15906v1](https://arxiv.org/abs/2510.15906v1); [paper PDF](fvdebug-2510.15906.pdf), distributed under the paper's [CC BY 4.0 license](https://creativecommons.org/licenses/by/4.0/).

- **Problem:** Diagnose formal-verification counterexamples using traces, RTL, and design specifications, then propose fixes.
- **Method:** Build a causal graph through JasperGold queries, scan it with batched arguments for and against suspected faults, explore competing causal explanations, and generate candidate RTL patches.
- **Reported evaluation:** On 38 hardware failures, the authors report 95.6% hypothesis quality, 71.1% Pass@1 and 86.8% Pass@5 fix rates. They also study two proprietary production-scale counterexamples. These are paper-reported results, not measurements reproduced here.
- **Relevance:** A concrete reference for connecting structured waveform evidence to tool-assisted diagnosis and patch validation. Its JasperGold-dependent graph extraction and evaluation scope matter when comparing it with other verification assistants.

Further reading topics:

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
