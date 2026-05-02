# TurboQuant by Google: Extensive Paper Survey

**Date:** April 8, 2026  
**Theme:** TurboQuant and the surrounding landscape of KV cache quantization, vector quantization for LLMs, and related compression research.

---

## 1. The Core TurboQuant Paper

### TurboQuant: Online Vector Quantization with Near-optimal Distortion Rate
- **Authors:** Amir Zandieh, Majid Daliri, Majid Hadian, Vahab Mirrokni (Google Research)
- **Venue:** ICLR 2026 (poster, April 25, 2026)
- **arXiv:** [2504.19874](https://arxiv.org/abs/2504.19874)
- **OpenReview:** https://openreview.net/pdf/6593f484501e295cdbe7efcbc46d7f20fc7e741f.pdf
- **Google Blog:** https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/

#### What it does
TurboQuant is an **online, data-oblivious vector quantization** algorithm that simultaneously minimizes:
1. **MSE (mean-squared error) distortion** — for tasks like nearest-neighbor search
2. **Inner product distortion** — critical for attention score fidelity in LLMs

It achieves near-optimal distortion rates (within a constant factor of ~2.7 from the information-theoretic lower bound) across **all bit-widths and dimensions**.

#### Core Algorithm
1. Apply a **random rotation** (random orthogonal matrix / randomized Hadamard transform) to the input vector.
2. After rotation the coordinates follow a **concentrated Beta distribution** and are nearly independent in high dimensions.
3. Apply **MSE-optimal scalar quantizers** (Lloyd-Max quantizers) independently per coordinate.

For **inner product quantization**, TurboQuant applies an MSE quantizer followed by a **1-bit QJL (Quantized Johnson-Lindenstrauss) transform** on the residual, yielding an unbiased inner product estimator.

#### Key Results
| Setting | Bit-width | Result |
|---|---|---|
| KV cache — quality neutral | 3.5 bits/channel | No accuracy degradation |
| KV cache — marginal degradation | 2.5 bits/channel | Marginal drop |
| Memory reduction vs FP16 | 3–3.5 bits | **5–6x** compression |
| H100 GPU speedup (attention logits) | 4-bit TurboQuant | **8x** vs 32-bit unquantized |
| Needle-in-a-Haystack @ 4x compression | Llama-3.1-8B | **0.997** recall |

#### Applications
- **KV cache compression** for LLM inference (primary application, solves the bottleneck for long-context models like Gemini)
- **Nearest neighbor search / ANN indexing** — outperforms product quantization in recall while reducing indexing time to near zero
- **Streaming / online settings** — no training, no calibration data, fully data-oblivious

---

## 2. Direct Companion Papers (Same Research Group)

### 2a. QJL: 1-Bit Quantized JL Transform for KV Cache Quantization with Zero Overhead
- **Authors:** Amir Zandieh, Majid Daliri, Insu Han
- **Venue:** AAAI 2025
- **arXiv:** [2406.03482](https://arxiv.org/abs/2406.03482) (June 2024)
- **GitHub:** https://github.com/amirzandieh/QJL

#### What it does
QJL is the **inner product quantization building block** that TurboQuant builds upon. A JL transform followed by sign-bit (1-bit) quantization creates an **unbiased inner product estimator** with no per-block quantization constants to store.

- Traditional quantization stores a scale + zero-point per block in full precision — this overhead is eliminated.
- Applied to KV cache at **3 bits** → >5x reduction in KV cache memory with no accuracy loss and faster runtime.
- Uses an **asymmetric estimator**: apply QJL to one vector (keys), standard JL (no quantization) to the other (queries).

---

### 2b. PolarQuant: Quantizing KV Caches with Polar Transformation
- **Authors:** Insu Han et al. (KAIST, Google Research, Yale)
- **Venue:** AISTATS 2026 (May 4, 2026)
- **arXiv:** [2502.02617](https://arxiv.org/abs/2502.02617) (February 2025)
- **Google Research page:** https://research.google/pubs/polarquant-quantizing-kv-caches-with-polar-transformation/

#### What it does
PolarQuant is the **MSE compression building block** used in TurboQuant's first step. It converts key vectors from Cartesian to polar coordinates using an efficient recursive algorithm.

- After random preconditioning, angles in polar form have a **tightly bounded, analytically computable distribution**.
- Quantizes the angles directly → **bypasses the normalization step** entirely, eliminating the need to store per-block normalization constants.
- Achieves **4.2x+ KV cache compression** while achieving the best quality scores vs. state-of-the-art at the time.

---

## 3. Predecessor / Structurally Related Quantization Papers

### 3a. HIGGS: Pushing the Limits of Large Language Model Quantization via the Linearity Theorem
- **Authors:** (multiple; published independently)
- **Venue:** NAACL 2025
- **arXiv:** [2411.17525](https://arxiv.org/abs/2411.17525) (November 2024)
- **HuggingFace support:** https://github.com/huggingface/transformers/blob/main/docs/source/en/quantization/higgs.md

#### What it does
HIGGS introduced the **structural pattern that TurboQuant later adapts**: Random Hadamard Transform + MSE-optimal grid quantization on the rotated values, for **LLM weight quantization** (not KV cache).

- Proves a "linearity theorem" relating layer-wise ℓ2 reconstruction error to perplexity increase.
- Outperforms NF4 and all prior zero-shot weight quantization methods at 3–4 bits.
- **Historical note:** HIGGS was the first to propose VQ + Hadamard rotation (Nov 2024, ~5 months before TurboQuant's arXiv posting), but for weights rather than KV caches and without the information-theoretic near-optimality analysis.

---

## 4. Competing / Baseline KV Cache Quantization Papers

These are the methods that TurboQuant directly benchmarks against and outperforms.

### 4a. KIVI: A Tuning-Free Asymmetric 2-bit Quantization for KV Cache
- **Venue:** ICML 2024
- **arXiv:** [2402.02750](https://arxiv.org/abs/2402.02750)
- **GitHub:** https://github.com/jy-yuan/KIVI

Per-channel key quantization + per-token value quantization. Achieves 2.6x peak memory reduction and 2.35–3.47x throughput increase. **TurboQuant outperforms KIVI on Needle-in-a-Haystack** (0.997 vs 0.981 at 4x compression).

---

### 4b. KVQuant: Towards 10 Million Context Length LLM Inference with KV Cache Quantization
- **Venue:** NeurIPS 2024
- **arXiv:** [2401.18079](https://arxiv.org/abs/2401.18079)
- **GitHub:** https://github.com/SqueezeAILab/KVQuant

Per-channel key quantization + pre-RoPE key quantization + non-uniform quantization + per-vector dense-and-sparse quantization. At 3-bit: **4.8x KV cache compression**. At 2-bit (nuq2): 8x compression, enabling LLaMA-7B with 1M context on a single A100.

---

### 4c. SnapKV: LLM Knows What You are Looking for Before Generation
- **arXiv:** [2404.14469](https://arxiv.org/abs/2404.14469) (April 2024)

**Token eviction** (not quantization): compresses KV cache by identifying and retaining only the most important tokens based on attention weights. At 16k sequence length, batch size 2: ~3.6x speedup vs baseline. **TurboQuant outperforms SnapKV** significantly on Needle-in-a-Haystack (0.997 vs 0.858 at comparable compression).

---

### 4d. PyramidKV: Dynamic KV Cache Compression based on Pyramidal Information Funneling
- **Venue:** Findings of ACL 2024 / ICLR 2025
- **arXiv:** [2406.02069](https://arxiv.org/abs/2406.02069)

**Layer-adaptive token eviction**: lower layers keep more KV entries (wide attention), higher layers keep fewer (focused). Retains only 12% of KV cache while matching full-cache quality on some benchmarks. **TurboQuant outperforms PyramidKV** on Needle-in-a-Haystack (0.997 vs 0.895).

---

## 5. Related Techniques and Papers

### 5a. Johnson-Lindenstrauss Transforms (Theoretical Foundation)
The JL transform used in QJL and TurboQuant is a classical result: a random projection from high-dimensional to lower-dimensional space that approximately preserves distances and inner products. TurboQuant's theoretical analysis of near-optimality relies heavily on this foundation.

### 5b. Product Quantization (PQ) — Classical Baseline
Traditional vector quantization approach for ANN (approximate nearest neighbor) search, used in FAISS and similar. TurboQuant outperforms PQ in recall on nearest-neighbor search tasks while reducing indexing time to virtually zero.

---

## 6. Open-Source Implementations

| Repository | Framework | Notes |
|---|---|---|
| [amirzandieh/QJL](https://github.com/amirzandieh/QJL) | PyTorch | Official QJL implementation |
| [tonbistudio/turboquant-pytorch](https://github.com/tonbistudio/turboquant-pytorch) | PyTorch | From-scratch TurboQuant, 5x compression at 3-bit, 99.5% attention fidelity |
| [sharpner/turboquant-mlx](https://github.com/sharpner/turboquant-mlx) | Apple MLX | Proof-of-concept |
| [0xSero/turboquant](https://github.com/0xSero/turboquant) | PyTorch + Triton | 3-bit keys, 2-bit values, Triton kernels, vLLM integration |
| [vivekvar-dl/turboquant](https://github.com/vivekvar-dl/turboquant) | Python (`pip install turbokv`) | First open-source impl, 4-7x compression |
| [yashkc2025/turboquant](https://github.com/yashkc2025/turboquant) | Python | 1–4 bit streaming KV caches |
| [RecursiveIntell/turbo-quant](https://github.com/RecursiveIntell/turbo-quant) | Rust | TurboQuant + PolarQuant + QJL, zero-overhead |
| [scos-lab/turboquant](https://github.com/scos-lab/turboquant) | PyTorch | Reference implementation / ICLR 2026 reproduction |

---

## 7. Benchmark Summary (TurboQuant vs Competitors)

**Task: Needle-in-a-Haystack (Llama-3.1-8B, ~4x compression)**

| Method | Type | Recall Score |
|---|---|---|
| TurboQuant | Quantization (vector, near-optimal) | **0.997** |
| KIVI | Quantization (scalar, asymmetric) | 0.981 |
| PyramidKV | Token eviction (layer-adaptive) | 0.895 |
| SnapKV | Token eviction (attention-based) | 0.858 |

**GPU Performance (H100, attention logit computation)**

| Setting | Speedup vs 32-bit |
|---|---|
| 4-bit TurboQuant | **8x** |

---

## 8. Chronological Timeline

| Date | Paper | Venue |
|---|---|---|
| Jan 2024 | KVQuant | NeurIPS 2024 |
| Feb 2024 | KIVI | ICML 2024 |
| Apr 2024 | SnapKV | arXiv |
| Jun 2024 | PyramidKV | ACL Findings 2024 |
| Jun 2024 | **QJL** (Zandieh et al.) | AAAI 2025 |
| Nov 2024 | HIGGS | NAACL 2025 |
| Feb 2025 | **PolarQuant** (Han et al.) | AISTATS 2026 |
| Apr 2025 | **TurboQuant** (Zandieh et al.) | ICLR 2026 |

---

## Sources

- [TurboQuant arXiv 2504.19874](https://arxiv.org/abs/2504.19874)
- [TurboQuant ICLR 2026 OpenReview](https://openreview.net/pdf/6593f484501e295cdbe7efcbc46d7f20fc7e741f.pdf)
- [TurboQuant Google Research Blog](https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/)
- [TurboQuant ICLR 2026 Poster Page](https://iclr.cc/virtual/2026/poster/10006985)
- [QJL arXiv 2406.03482](https://arxiv.org/abs/2406.03482)
- [QJL AAAI Publication](https://ojs.aaai.org/index.php/AAAI/article/view/34773)
- [PolarQuant arXiv 2502.02617](https://arxiv.org/abs/2502.02617)
- [PolarQuant Google Research page](https://research.google/pubs/polarquant-quantizing-kv-caches-with-polar-transformation/)
- [HIGGS arXiv 2411.17525](https://arxiv.org/abs/2411.17525)
- [KIVI arXiv 2402.02750](https://arxiv.org/abs/2402.02750)
- [KVQuant arXiv 2401.18079](https://arxiv.org/abs/2401.18079)
- [SnapKV arXiv 2404.14469](https://arxiv.org/abs/2404.14469)
- [PyramidKV arXiv 2406.02069](https://arxiv.org/abs/2406.02069)
- [TechCrunch coverage](https://techcrunch.com/2026/03/25/google-turboquant-ai-memory-compression-silicon-valley-pied-piper/)
- [VentureBeat coverage](https://venturebeat.com/infrastructure/googles-new-turboquant-algorithm-speeds-up-ai-memory-8x-cutting-costs-by-50)
- [Tom's Hardware coverage](https://www.tomshardware.com/tech-industry/artificial-intelligence/googles-turboquant-compresses-llm-kv-caches-to-3-bits-with-no-accuracy-loss)
- [Deep Dive blog post (PolarQuant + QJL + TurboQuant explained)](https://darshanfofadiya.com/research-papers/turboquant/)
