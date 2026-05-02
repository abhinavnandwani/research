# TiDAR: Think in Diffusion, Talk in Autoregression

Dummy implementation of TiDAR architecture based on the paper "TiDAR: Think in Diffusion, Talk in Autoregression" (arXiv:2511.08923v1) for training on CHTC.

## Paper Summary

**TiDAR** is a hybrid language model architecture that combines:
- **Diffusion** for parallel token drafting (thinking)
- **Autoregression** for high-quality sampling (talking)

Key innovations:
- Hybrid attention mask enabling both modes in a single forward pass
- Full masking strategy for diffusion section (all tokens = [MASK])
- Dual loss: AR loss (causal) + Diffusion loss (bidirectional)
- Achieves 4.71-5.91× speedup over standard autoregressive models

## Implementation

This is a **simplified dummy implementation** that captures the core architecture:

### Model Components

1. **Hybrid Attention Mask** (`model/tidar_model.py`)
   - Causal attention for AR section (prefix tokens)
   - Bidirectional attention for diffusion section (masked tokens)
   - Combined in single forward pass

2. **Dual-Mode Training**
   - AR loss: Next token prediction on clean tokens (shifted labels)
   - Diffusion loss: Predict all masked tokens (no shift)
   - Combined with balancing factor α (default: 1.0)

3. **Full Masking Strategy**
   - All diffusion tokens set to [MASK] during training
   - Denser loss signal
   - Simpler than random masking strategies

### Files

```
TiDAR/
├── model/
│   └── tidar_model.py          # TiDAR model implementation
├── train_tidar.py               # Training script with WandB
├── run_train.sh                 # CHTC wrapper script
├── tidar.sub                    # HTCondor submit file
└── README.md                    # This file
```

## Training on CHTC

### Setup

1. Upload project to CHTC:
```bash
# From local machine
cd ~/projects/research
scp -r TiDAR chtc:~/tidar-project/
```

2. Create logs directory on CHTC:
```bash
ssh chtc
cd ~/tidar-project
mkdir -p logs
```

### Submit Job

```bash
condor_submit tidar.sub
```

### Monitor Training

Real-time monitoring via WandB:
```bash
# On local machine
cd ~/projects/research/chtc-tools
./bin/chtc wandb monitor --project tidar-chtc
```

Or check WandB dashboard: https://wandb.ai/home (look for project "tidar-chtc")

### Job Configuration

- **GPU**: 1x GPU with ≥8GB VRAM (e.g., RTX 2080 Ti)
- **CPU**: 4 cores
- **Memory**: 16GB
- **Disk**: 30GB
- **Queue**: GPU Lab (medium, <24 hours)
- **Container**: segformer.sif

## Model Configuration

Current settings (dummy/proof-of-concept):
- Vocab size: 256 (character-level)
- Hidden size: 512
- Layers: 8
- Attention heads: 8
- Block size: 4 (diffusion draft length)
- Total params: ~12M

Training:
- Epochs: 20
- Batch size: 64
- Sequence length: 128
- Learning rate: 3e-4
- Loss balancing α: 1.0

## Key Differences from Paper

This is a **simplified demonstration**:

1. **No Parallel Drafting+Sampling**: Full TiDAR inference involves complex parallel drafting with rejection sampling. This implementation uses simple autoregressive generation.

2. **Dummy Data**: Uses character-level text generation instead of real tokenized datasets.

3. **Scale**: Much smaller model (12M params vs paper's 1.5B-8B).

4. **Training**: Simplified training loop without all optimizations (KV cache, flex attention, etc.).

## Paper Key Concepts

### Hybrid Architecture

From paper Section 3:
```
At each generation step (one forward pass):
1. Prefix tokens: Cached from previous step
2. Tokens proposed last step: AR sampling with rejection
3. Pre-drafted tokens: Diffusion for next step

All in single forward pass using structured attention masks!
```

### Attention Mask

Figure 3 from paper:
```
[Clean Prefix] → Causal attention (like normal transformer)
[Mask Tokens]  → Bidirectional within block + causal to prefix
```

### Loss Function

From paper Equation:
```
L_TiDAR = (α·L_AR + L_Diff) / (1 + α)

where:
- L_AR: Cross-entropy on clean tokens (shifted for next-token prediction)
- L_Diff: Cross-entropy on masked tokens (all positions)
- α: Balancing factor (1.0 works well)
```

## WandB Tracking

Metrics logged:
- `train_loss`: Combined TiDAR loss
- `train_ar_loss`: Autoregressive component
- `train_diff_loss`: Diffusion component
- `val_loss`: Validation metrics
- `learning_rate`: Current LR
- `sample_N`: Generated text samples

## Results

Check WandB dashboard for:
- Real-time training curves
- Loss decomposition (AR vs Diffusion)
- Generated text samples
- Model checkpoints

## Next Steps

To extend this implementation:

1. **Use Real Tokenizer**: Replace char-level with BPE/SentencePiece
2. **Better Data**: Use WikiText, OpenWebText, or custom corpus
3. **Larger Model**: Scale to 1B+ parameters
4. **Full Inference**: Implement parallel drafting+sampling from paper
5. **KV Cache**: Add exact KV caching support
6. **Flex Attention**: Use optimized attention kernels

## References

- Paper: [TiDAR: Think in Diffusion, Talk in Autoregression](https://arxiv.org/abs/2511.08923)
- Authors: Jingyu Liu*, Xin Dong*, et al. (NVIDIA, 2025)
- Code: This is an independent implementation based on paper descriptions

## License

Educational/research purposes only.
