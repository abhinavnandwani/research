# Research Questions from "In-Datacenter Performance Analysis of a Tensor Processing Unit" (Jouppi et al., 2017) — Contextualized for 2026

## Paper Summary

The 2017 paper evaluates Google's first-generation Tensor Processing Unit (TPU), a custom ASIC deployed in datacenters since 2015 for neural network inference. Key findings:

- The TPU's heart is a **65,536 8-bit MAC systolic matrix multiply unit** (256x256) offering 92 TOPS peak, with 28 MiB on-chip memory (Unified Buffer) and 8 GiB off-chip DDR3 Weight Memory (34 GB/s bandwidth).
- Six production workloads (2 MLPs, 2 LSTMs, 2 CNNs) representing **95% of datacenter NN inference** were benchmarked. MLPs dominated at 61%, LSTMs at 29%, and CNNs at only 5%.
- **4 of 6 workloads were memory-bandwidth-bound**, not compute-bound. Increasing memory bandwidth 4x yielded ~3x performance improvement; increasing compute had little effect for most workloads.
- The TPU's **deterministic, single-threaded execution** model was better suited to 99th-percentile latency SLOs than GPUs/CPUs with caches, OoO execution, and multithreading.
- TPU achieved **15-30x faster inference** than the contemporary K80 GPU and Haswell CPU, with **30-80x better TOPS/Watt**.
- Sparse architectural support was explicitly omitted for time-to-deploy reasons.
- A hypothetical TPU' with GDDR5 memory (replacing DDR3) would have tripled performance.
- IPS (inferences per second) was shown to be a misleading metric, varying 75x across workloads on the same hardware.

---

## 2026 Landscape Context

### AI Accelerator Hardware

| Chip | Process | Peak Compute | Memory | Memory BW | TDP |
|------|---------|-------------|--------|-----------|-----|
| **TPU v1** (2015) | 28nm | 92 TOPS (INT8) | 8 GiB DDR3 | 34 GB/s | 75W |
| **TPU v6e Trillium** (2024) | — | 918 TFLOPS (BF16) | 32 GB HBM | 2x v5e | — |
| **TPU v7 Ironwood** (2025) | — | ~4,614 PFLOPS (FP8) | HBM | — | — |
| **NVIDIA K80** (2015) | 28nm | 2.8 TFLOPS (FP32) | 12 GiB GDDR5 | 160 GB/s | 150W |
| **NVIDIA B200** (2025) | 4nm | 9 PFLOPS (FP4) | 192 GB HBM3e | 8 TB/s | 1,000W |
| **NVIDIA B300** (2025) | 4nm | ~15 PFLOPS (FP4) | 288 GB HBM3e | 8 TB/s | 1,400W |
| **AMD MI350X** (2025) | 3nm | ~4x MI300X (FP4/FP6) | 288 GB HBM3e | 6 TB/s | — |
| **Cerebras WSE-3** | 5nm | 125 PFLOPS | 44 GB on-chip SRAM | 21 PB/s on-chip | — |
| **Groq LPU** | — | 750 TOPS (INT8) | 230 MB on-die SRAM | 80 TB/s on-die | — |

### Workload Shift

- **2015-2017:** MLPs (61%), LSTMs (29%), CNNs (5%) dominated datacenter inference.
- **2026:** Transformer/attention-based architectures dominate nearly all modalities (NLP, vision, multimodal, code, speech). Inference accounts for ~2/3 of all AI compute (up from ~1/3 in 2023).

### Key Trends

- **FP4/FP8** are the new precision frontier (replacing the paper's INT8 focus).
- **HBM3e/HBM4** provide 8-20 TB/s system bandwidth (vs. 34 GB/s DDR3 in TPU v1).
- **Advanced packaging (CoWoS)** is the production bottleneck, not lithography.
- **Datacenter power** is a hard constraint: ~96 GW globally by 2026, AI consuming >40%.
- **Custom ASIC shipments** growing at 44.6% vs. 16.1% for GPUs.
- **Sparsity support** remains limited despite 9 years of research (NVIDIA's rigid 2:4 pattern).

---

## Research Questions

### 1. The Workload Shift: From MLPs/LSTMs to Transformers

The paper found that MLPs (61%) and LSTMs (29%) dominated datacenter inference, with CNNs at only 5%. By 2026, transformers dominate almost everything.

**RQ 1.1:** How should the Roofline performance model be extended to characterize transformer/attention workloads on modern accelerators (TPU v7, Blackwell), given that attention's quadratic memory access pattern fundamentally differs from the MLP/LSTM/CNN patterns analyzed in the original paper?

**RQ 1.2:** What fraction of 2026 datacenter inference is now autoregressive LLM decoding (memory-bound, batch-size-1-like) vs. prefill/prompt-processing (compute-bound)? How does this split compare to the paper's finding that 4/6 workloads were memory-bandwidth-bound?

**Why it matters:** The paper's Roofline analysis (Figures 5-8) and operational intensity metric were defined for weight-reuse patterns in MLPs/CNNs/LSTMs. Transformer inference has fundamentally different access patterns: prefill is compute-bound (large matrix multiplies over the prompt), while decode is memory-bound (loading full KV-cache + weight matrices to produce a single token). A unified analytical model for this two-phase workload does not yet exist.

---

### 2. The Memory Wall — Revisited at Scale

The paper's most actionable finding was that memory bandwidth, not compute, was the bottleneck (4/6 apps memory-bound; 4x memory BW yielded 3x speedup via the hypothetical TPU'). This is arguably even more true for LLM inference in 2026.

**RQ 2.1:** Given that LLM autoregressive decoding is almost entirely memory-bandwidth-bound (loading KV-cache + weights each token), what is the optimal ratio of compute (TOPS) to memory bandwidth (TB/s) for a 2026 inference accelerator? How far are current chips (B200: 9 PFLOPS / 8 TB/s vs. TPU v7: ~4.6 PFLOPS / unknown BW) from this optimum?

**RQ 2.2:** Can CXL-based disaggregated memory pooling effectively extend the "Weight Memory" concept from the original TPU to serve models too large for on-chip HBM, without violating 99th-percentile latency SLOs?

**Why it matters:** The paper showed that simply replacing DDR3 with GDDR5 would have tripled TPU performance. In 2026, the equivalent question is whether HBM4 (>2 TB/s per stack), CXL-attached memory tiers, or processing-in-memory can break the memory wall for 100B+ parameter model serving. HBM supply is sold out through 2026, making this a supply-chain question as well as an architectural one.

---

### 3. Determinism vs. Throughput for Tail Latency

The paper argued that the TPU's deterministic, single-threaded execution model was superior for meeting 99th-percentile latency targets vs. GPUs' throughput-oriented, non-deterministic design (no caches, branch prediction, OoO execution, multithreading, etc.).

**RQ 3.1:** With NVIDIA's addition of MIG (Multi-Instance GPU) and inference-optimized software stacks (TensorRT-LLM), have GPUs closed the tail-latency gap that the paper identified? Or does the fundamental architectural argument for deterministic accelerators (like Groq's LPU) still hold for latency-critical LLM serving in 2026?

**RQ 3.2:** Groq's LPU uses compiler-scheduled deterministic execution with 230 MB on-die SRAM — architecturally similar to the TPU v1's philosophy but with 8x the on-chip memory. What is the performance/watt frontier for deterministic vs. throughput-oriented architectures for LLM inference at the 99th-percentile?

**Why it matters:** The paper demonstrated that the K80 GPU operated at only 37% of peak throughput under a 7ms latency constraint (Table 4), while the TPU operated at 80%. In 2026, LLM serving has even stricter latency requirements (time-to-first-token < 500ms, inter-token latency < 50ms) and the question of whether GPUs can efficiently meet these under realistic concurrent load remains open. NVIDIA's acquisition of Groq (late 2025) suggests the industry sees value in the deterministic approach.

---

### 4. Numerical Precision Beyond INT8

The original TPU used 8-bit integers and the paper noted that INT8 multiplies are 6x less energy and 6x less area than FP16. The 2026 frontier is FP4/FP8.

**RQ 4.1:** The original TPU showed that INT8 was "good enough" for inference in 2015. For 2026's LLMs, what is the Pareto frontier of precision (FP4 vs. FP8 vs. INT4-with-dequant vs. mixed-precision) across accuracy, throughput, and energy for production transformer inference? Is there a "good enough" precision for LLMs analogous to INT8 for 2015 CNNs/MLPs?

**RQ 4.2:** NVIDIA Blackwell supports native FP4 but dropped native INT4. Is floating-point low-precision fundamentally superior to integer low-precision for transformer weights/activations, or is this a contingent engineering choice? What does a principled analysis of quantization noise propagation through attention layers suggest?

**Why it matters:** The paper's energy argument (INT8 multiplies = 6x less energy than FP16) was foundational. In 2026, NVIDIA's NVFP4 format claims 3.5x memory reduction vs. FP16 with <1% accuracy loss. But the shift from integer to floating-point low precision represents a fundamental change in the quantization paradigm, and the theoretical justification is underexplored. Understanding whether FP4 is an engineering convenience or a mathematical necessity would inform next-generation accelerator ISA design.

---

### 5. Sparsity — The Unfulfilled Promise

The paper explicitly noted: *"Sparse architectural support was omitted for time-to-deploy reasons. Sparsity will have high priority in future designs."* Nine years later, hardware sparsity support remains limited.

**RQ 5.1:** Why has hardware-accelerated sparsity underdelivered relative to the 2017 paper's expectations? Is the problem architectural (2:4 structured sparsity is too rigid), algorithmic (models don't naturally produce exploitable sparsity patterns), or economic (the area/power cost of sparsity logic doesn't justify the benefit at current model sizes)?

**RQ 5.2:** For transformer attention patterns that exhibit dynamic, input-dependent sparsity (e.g., sparse attention, mixture-of-experts routing), what hardware support would actually deliver speedups in production? Can we design a "sparsity-aware systolic array" that handles both structured and semi-structured sparsity efficiently?

**Why it matters:** NVIDIA has offered 2:4 structured sparsity since Ampere (2020), but adoption remains limited because (a) the 2:4 pattern is too rigid for many models, (b) accuracy degradation is non-trivial for large models, and (c) the software ecosystem (pruning tools, fine-tuning pipelines) is immature. Meanwhile, Mixture-of-Experts (MoE) models like Mixtral represent a form of dynamic structured sparsity that existing hardware doesn't efficiently exploit. Google's TPU v6e includes a 3rd-generation SparseCore, but only for embedding/recommendation workloads. The gap between sparsity's theoretical promise and hardware reality is one of the longest-standing open problems in accelerator design.

---

### 6. The "Cornucopia Corollary" at Chiplet Scale

The paper proposed that *"low utilization of a huge, cheap resource can still deliver high, cost-effective performance"* (the Cornucopia Corollary to Amdahl's Law). It also showed that increasing the matrix unit from 256x256 to 512x512 actually *degraded* performance due to "internal fragmentation" in two dimensions.

**RQ 6.1:** Does the Cornucopia Corollary still hold when the "huge resource" is a 208-billion-transistor dual-die chiplet (B200) or a 4-trillion-transistor wafer (Cerebras WSE-3)? At what scale does the utilization penalty of oversized compute units outweigh the cost advantages?

**RQ 6.2:** What is the optimal MXU/tensor core size for 2026 transformer inference workloads? The paper showed 256x256 was a sweet spot for 2015 NNs. Given that modern transformer hidden dimensions are typically 4096-12288, has the optimal matrix unit size shifted, and should it be dynamically reconfigurable?

**Why it matters:** The paper's finding that 512x512 matrices hurt performance (Section 7, Figure 11) due to 2D internal fragmentation is one of its most nuanced architectural insights. In 2026, TPU v6e/v7 uses 256x256 MXUs (unchanged from v1!), while transformer hidden dimensions have grown 16-48x. This creates a different tiling regime. Cerebras takes the opposite extreme with 900,000 small cores. Understanding the optimal granularity of compute units for modern workloads is critical for next-generation accelerator design.

---

### 7. Energy Proportionality for AI Accelerators

The paper found the TPU had poor energy proportionality (88% power at 10% load vs. 56% for CPUs). Modern accelerators draw 1,000-1,400W per chip.

**RQ 7.1:** As AI accelerators scale to 1,000-1,400W TDP (Blackwell B300) and datacenters approach power constraints (~96 GW globally by 2026), what architectural techniques can improve energy proportionality for inference accelerators without sacrificing peak performance? Can power-gating of MXU sub-arrays or dynamic voltage-frequency scaling at the tile level help?

**RQ 7.2:** The paper used performance/Watt as a proxy for performance/TCO. In 2026, with liquid cooling mandatory and power availability becoming the binding constraint for new datacenter builds, should the primary metric shift to performance/Watt/mm^2 or performance-per-rack-unit to capture cooling and space costs?

**Why it matters:** AI datacenter power consumption is growing at ~30% annually and could reach 980 TWh by 2030. The paper's observation that the TPU's short design schedule prevented energy-saving features (Section 6) foreshadowed a problem that is now existential. At 1,400W per chip (B300), a rack of 8 GPUs draws 11.2 kW in accelerators alone. Energy proportionality — idle power as a fraction of peak — directly impacts electricity costs and cooling infrastructure, which now dominate TCO for many deployments.

---

### 8. Custom ASICs vs. GPUs — The Economic Question Revisited

The paper showed TPU achieved 15-30x speedup over the K80 GPU for inference, vindicating the custom ASIC approach. Custom ASIC shipments are now growing at 44.6% vs. 16.1% for GPUs.

**RQ 8.1:** The original TPU was designed and deployed in 15 months. In 2026, with advanced packaging (CoWoS) as the binding bottleneck and 3nm tape-out costs exceeding $500M, what is the minimum production volume at which a custom inference ASIC is economically justified over renting GPU capacity? How does this calculus change with chiplet-based designs that amortize NRE across multiple products?

**RQ 8.2:** NVIDIA acquired Groq in late 2025. As GPU vendors incorporate ideas from custom inference ASICs (deterministic execution, large SRAM, systolic arrays), is the domain-specific accelerator thesis from the paper converging back toward general-purpose GPU architectures, or are the workload-specific benefits still large enough to justify separate silicon?

**Why it matters:** The paper argued that domain-specific architectures could achieve order-of-magnitude improvements over general-purpose hardware, and predicted the TPU would become "an archetype for domain-specific architectures." Nine years later, every major cloud provider has a custom AI chip program (Google TPU, AWS Trainium/Inferentia, Microsoft Maia, Meta MTIA). But the NRE costs have exploded, and NVIDIA has been incorporating ASIC-like features (tensor cores, transformer engines, FP4 support). The convergence or divergence of these approaches is a central question in computer architecture.

---

### 9. Benchmarking and Metrics for LLM Inference

The paper argued that IPS is a misleading metric (varying 75x across workloads) and called for better benchmark suites.

**RQ 9.1:** MLPerf Inference now exists as the standard benchmark. But for LLM serving, the relevant metrics are tokens/second/dollar, time-to-first-token (TTFT), and inter-token latency (ITL) under concurrent load. How should a "Roofline model for LLM inference" be formulated that captures the prefill vs. decode phases, KV-cache memory scaling, and batching dynamics?

**RQ 9.2:** The paper benchmarked 6 apps representing 95% of datacenter NN inference. What are the equivalent "6 representative workloads" for 2026 datacenter AI, and how diverse are they architecturally? (e.g., LLM chat, code generation, RAG retrieval+generation, multimodal vision-language, speech-to-text, recommendation/ranking)

**Why it matters:** The paper's critique of IPS as a metric was prescient. In 2026, the LLM serving community uses a proliferation of metrics (TTFT, ITL, tokens/s, tokens/s/$, tokens/s/W) with no standardized methodology for measuring them under realistic conditions (varying concurrency, prompt lengths, generation lengths). A principled analytical framework — analogous to the Roofline model that the paper adapted for NN accelerators — would be enormously valuable for both hardware designers and system operators.

---

### 10. On-Chip Memory and the KV-Cache Problem

The paper's TPU had a 28 MiB Unified Buffer sufficient for all 2015 workloads. Modern LLM inference is dominated by KV-cache memory.

**RQ 10.1:** The original TPU's 28 MiB on-chip buffer held all activations for its workloads. For a 70B-parameter LLM serving 256 concurrent requests at 8K context length, the KV-cache alone requires ~100 GB. What on-chip memory architecture (SRAM tiers, eDRAM, processing-in-memory for HBM) would minimize the KV-cache bottleneck while remaining economically viable?

**RQ 10.2:** Techniques like PagedAttention, multi-query attention (MQA), and grouped-query attention (GQA) reduce KV-cache size at the algorithm level. What is the hardware-software co-design space between algorithmic KV-cache compression and accelerator memory hierarchy for inference?

**Why it matters:** The paper's Unified Buffer was designed so that "no DRAM spilling or reloading happens during normal operation" (Section 9). This is impossible for LLM inference in 2026 — KV-caches for long-context models (128K+ tokens) can exceed 1 TB for a single request batch. The memory hierarchy design for KV-cache is arguably the most important open problem in inference accelerator architecture. Groq's approach (230 MB on-die SRAM) works for small models but cannot scale to frontier LLMs without multi-chip orchestration. Understanding this co-design space is critical.

---

## Recommended Research Priorities

Ranked by **impact x tractability** for a 2026 research agenda:

| Priority | Research Question | Impact | Tractability |
|----------|------------------|--------|-------------|
| 1 | **RQ 2.1** — Optimal compute-to-bandwidth ratio for LLM inference | Very High | High |
| 2 | **RQ 10.2** — KV-cache hardware-software co-design | Very High | Medium |
| 3 | **RQ 1.1** — Roofline model for transformer inference | High | High |
| 4 | **RQ 5.2** — Sparsity-aware systolic arrays for MoE/attention | High | Medium |
| 5 | **RQ 6.2** — Optimal matrix unit sizing for transformers | High | High |
| 6 | **RQ 4.2** — FP4 vs. INT4 quantization noise analysis | Medium | High |
| 7 | **RQ 7.1** — Energy proportionality at 1kW+ TDP | High | Low |
| 8 | **RQ 3.1** — Deterministic vs. throughput architectures for tail latency | Medium | Medium |
| 9 | **RQ 9.1** — Roofline model for LLM serving metrics | Medium | High |
| 10 | **RQ 8.1** — Custom ASIC economics at 3nm | Medium | Low |

---

## References

- Jouppi, N.P. et al. "In-Datacenter Performance Analysis of a Tensor Processing Unit." ISCA 2017. arXiv:1704.04760
- Google Cloud Blog. "Introducing Trillium, our 6th-generation TPU." 2024.
- Google. "TPU v7 Ironwood." April 2025.
- NVIDIA. "Blackwell Architecture Technical Brief." 2025.
- Cerebras. "WSE-3 Wafer-Scale Engine." 2024.
- MLCommons. "MLPerf Inference v5.1 Results." September 2025.
- Deloitte. "Technology, Media, and Telecom Predictions 2026: AI Compute Power." 2026.
- IEA. "Energy and AI: Energy Demand from AI." 2025.
- SK Hynix. "2026 Market Outlook: Focus on HBM-led Memory Supercycle." 2026.
- AMD. "Instinct MI350 Series and Beyond." 2025.
