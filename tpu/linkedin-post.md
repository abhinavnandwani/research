elon musk says the next step function after computer use is chip design. having just built AMD's AI agent benchmarking platform for SoC verification, here's my take:

**he's directionally right, but the unlock isn't where people think.**

the narrative is "agents will do full chip design - RTL to GDSII." that's the 2030+ moonshot. the actual step function happening right now is **agentic verification and debug.**
**why verification is the real target:**

verification is **70% of chip design effort.** verification teams are often **3x larger** than design teams.
unlike creative design work, verification is exhaustive search over a constrained space. you're hunting bugs in simulation waveforms, assertion failures, corner cases. agents don't need chip design intuition - they need pattern matching over structured data.
**the infrastructure exists.** simulation outputs are structured (VCD/FSDB waveforms), assertions are programmatic (SVA), coverage metrics are quantifiable. at AMD we built an **FSDB MCP server** that gives agents access to pipeline signals, coherency events, memory traces.
**the question is what agents can actually handle:**

we're benchmarking models on tasks like triaging simulation failures, correlating assertion violations with waveform patterns, navigating large waveform datasets, and proposing targeted testcases.

the real challenge is **programming agentic tool use of EDA tools for scale-out block-level design.** but this gets unblocked as developing the actual software infrastructure for chip design gets easier - better APIs, more accessible tooling, cleaner abstractions.
**why 2025-2026 is pivotal:**

**2025:** verification automation hit production. the tooling exists, the benchmarks are running, verification copilots started working in real chip design workflows.

**2026:** chip design revolution. look at what happened with coding agents - 12 months from "interesting demo" to **cambrian explosion of startups** (Cursor, Windsurf, Cline, Aider, dozens more). same pattern incoming for verification agents. ChipAgents just raised $21M with 6,377% usage surge - **first-mover advantage is massive.**
**why this matters:**

chip design has **18-24 month cycles.** verification is the bottleneck, not RTL creativity.
elon's right that chip design is the next frontier. but the unlock isn't replacing chip designers - it's making verification teams radically more efficient.
**the companies that win build:**
• models trained on proprietary verification data
• agentic frameworks that orchestrate parallel simulations
• verification-specific tooling (not general "coding agents")

**we're closer than people think. the infrastructure is ready. it's already starting.**