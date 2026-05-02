# AI for Silicon Design

Notes, paper lists, and research questions for AI-for-silicon-design topics.

## Suggested scope

Focus areas to track:

1. Verification and debug
2. EDA copilots and agentic tool use
3. RTL / microarchitecture exploration
4. Physical design optimization
5. Test, yield, and post-silicon validation
6. Hardware-software co-design for AI accelerators

## Seed questions

### 1. Verification as the first major wedge

- Which verification tasks are already structured enough for agents to handle reliably?
- What benchmark should exist for waveform navigation, assertion triage, root-cause localization, and testcase generation?
- What tool interfaces matter most: FSDB/VCD access, SVA traces, UVM logs, coverage DBs, simulator APIs?

### 2. AI for architecture exploration

- Can LLMs help generate or rank microarchitectural alternatives under explicit PPA constraints?
- Where do learned surrogates beat brute-force simulation in architecture search?
- Which accelerator-design decisions remain bottlenecked by human judgment rather than search?

### 3. AI inside the EDA loop

- Which EDA steps are best framed as copilots versus autonomous agents?
- How should agent systems call commercial EDA tools safely, reproducibly, and at scale?
- What is the right abstraction layer: raw Tcl/tool commands, intermediate design graphs, or domain APIs?

### 4. Data moat and evaluation

- What proprietary data actually creates defensibility: waveforms, bug databases, ECO histories, timing reports, prior layout outcomes?
- How do we evaluate usefulness without leaking sensitive design data?
- What are the equivalent of SWE-bench or terminal benchmarks for silicon workflows?

### 5. Physical design and signoff

- Where can ML meaningfully improve placement, routing, congestion prediction, timing closure, IR-drop mitigation, or DFM?
- Which problems are mature enough for offline prediction, and which require closed-loop optimization with tools in the loop?

### 6. Hardware-software co-design

- How should accelerators be designed when verification, profiling, and debug themselves become AI-assisted workflows?
- Can future chips expose more observability and control specifically for agent-driven debug?

## Candidate files

As this folder grows, useful files may include:

- `landscape.md` for a market and research overview
- `research_questions.md` for long-horizon questions
- `verification-agents.md` for the most immediate wedge
- `physical-design-ml.md` for placement/routing/timing literature
- `paper-list.md` for annotated reading backlog

## Reading buckets

- Google TPU / accelerator papers where verification or compiler co-design leaks through the architecture story
- Classical ML-for-EDA work on placement, routing, and congestion prediction
- Recent LLM-agent systems for code, adapted to EDA tool orchestration
- Industrial benchmark or product material from Synopsys, Cadence, Siemens, NVIDIA, AMD, Intel, Google, and chip-design startups
- Work on surrogate modeling, Bayesian optimization, and RL for hardware design-space exploration

## Immediate next step

Build `paper-list.md` as a curated reading queue with five buckets:

1. Verification agents
2. LLMs for EDA copilots
3. ML for physical design
4. Architecture search and co-design
5. AI-accelerator case studies
