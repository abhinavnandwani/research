#!/usr/bin/env python3
"""
Simplified TiDAR Model Implementation
Based on "TiDAR: Think in Diffusion, Talk in Autoregression" (arXiv:2511.08923v1)

This is a dummy implementation that captures the core hybrid architecture:
- Autoregressive (AR) mode for prefix tokens (causal attention)
- Diffusion mode for draft tokens (bidirectional attention within blocks)
- Hybrid attention mask combining both modes in a single forward pass
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class TiDARConfig:
    """Configuration for TiDAR model"""
    def __init__(
        self,
        vocab_size=32000,
        hidden_size=512,
        num_layers=8,
        num_heads=8,
        intermediate_size=2048,
        max_seq_len=512,
        block_size=4,  # Draft length for diffusion
        dropout=0.1,
        alpha=1.0,  # Loss balancing factor (AR vs Diffusion)
    ):
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.intermediate_size = intermediate_size
        self.max_seq_len = max_seq_len
        self.block_size = block_size
        self.dropout = dropout
        self.alpha = alpha

        assert hidden_size % num_heads == 0


class MultiHeadAttention(nn.Module):
    """Multi-head attention with support for custom attention masks"""
    def __init__(self, config):
        super().__init__()
        self.num_heads = config.num_heads
        self.head_dim = config.hidden_size // config.num_heads
        self.hidden_size = config.hidden_size

        self.q_proj = nn.Linear(config.hidden_size, config.hidden_size)
        self.k_proj = nn.Linear(config.hidden_size, config.hidden_size)
        self.v_proj = nn.Linear(config.hidden_size, config.hidden_size)
        self.o_proj = nn.Linear(config.hidden_size, config.hidden_size)

        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x, attention_mask=None):
        batch_size, seq_len, _ = x.shape

        # Project and reshape
        q = self.q_proj(x).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)

        # Attention scores
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_dim)

        # Apply mask if provided
        if attention_mask is not None:
            scores = scores.masked_fill(attention_mask == 0, float('-inf'))

        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)

        # Apply attention to values
        out = torch.matmul(attn_weights, v)
        out = out.transpose(1, 2).contiguous().view(batch_size, seq_len, self.hidden_size)
        out = self.o_proj(out)

        return out


class TransformerBlock(nn.Module):
    """Transformer block with attention and feedforward"""
    def __init__(self, config):
        super().__init__()
        self.attention = MultiHeadAttention(config)
        self.norm1 = nn.LayerNorm(config.hidden_size)
        self.norm2 = nn.LayerNorm(config.hidden_size)

        self.ffn = nn.Sequential(
            nn.Linear(config.hidden_size, config.intermediate_size),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.intermediate_size, config.hidden_size),
            nn.Dropout(config.dropout)
        )

    def forward(self, x, attention_mask=None):
        # Attention with residual
        x = x + self.attention(self.norm1(x), attention_mask)
        # FFN with residual
        x = x + self.ffn(self.norm2(x))
        return x


class TiDARModel(nn.Module):
    """
    Simplified TiDAR Model

    Key features from paper:
    1. Hybrid attention: causal for AR section, bidirectional for diffusion section
    2. Dual-mode training: AR loss on prefix, diffusion loss on masked tokens
    3. Full masking strategy for diffusion section (all tokens = [MASK])
    """
    def __init__(self, config):
        super().__init__()
        self.config = config

        # Token embeddings
        self.token_embedding = nn.Embedding(config.vocab_size, config.hidden_size)
        self.position_embedding = nn.Embedding(config.max_seq_len * 2, config.hidden_size)
        self.dropout = nn.Dropout(config.dropout)

        # Transformer layers
        self.layers = nn.ModuleList([
            TransformerBlock(config) for _ in range(config.num_layers)
        ])

        # Output projection
        self.norm = nn.LayerNorm(config.hidden_size)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)

        # Tie weights
        self.lm_head.weight = self.token_embedding.weight

        # Special tokens
        self.mask_token_id = config.vocab_size - 1

        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
        elif isinstance(module, nn.LayerNorm):
            torch.nn.init.zeros_(module.bias)
            torch.nn.init.ones_(module.weight)

    def create_hybrid_attention_mask(self, seq_len, ar_len, device):
        """
        Create hybrid attention mask as described in TiDAR paper (Figure 3)

        Args:
            seq_len: Total sequence length (ar_len + diffusion_len)
            ar_len: Length of autoregressive (causal) section
            device: Device to create mask on

        Returns:
            Attention mask of shape (seq_len, seq_len)
        """
        mask = torch.zeros(seq_len, seq_len, device=device)

        # AR section: causal attention (lower triangular)
        if ar_len > 0:
            ar_mask = torch.tril(torch.ones(ar_len, ar_len, device=device))
            mask[:ar_len, :ar_len] = ar_mask

        # Diffusion section: bidirectional attention within block + causal to AR
        diff_len = seq_len - ar_len
        if diff_len > 0:
            # Can attend to all AR tokens
            mask[ar_len:, :ar_len] = 1
            # Bidirectional within diffusion block
            mask[ar_len:, ar_len:] = 1

        return mask.unsqueeze(0).unsqueeze(0)  # Add batch and head dimensions

    def forward(self, input_ids, ar_section_len=None, labels=None):
        """
        Forward pass with hybrid AR-Diffusion training

        Args:
            input_ids: Input token IDs [batch, seq_len]
            ar_section_len: Length of AR section (rest is diffusion)
            labels: Ground truth labels [batch, seq_len * 2] (for AR + Diffusion)
        """
        batch_size, seq_len = input_ids.shape
        device = input_ids.device

        # During training, we double the sequence length (AR section + masked section)
        # as described in paper Section 3.1
        is_training = labels is not None

        if is_training:
            # Training mode: append masked tokens
            if ar_section_len is None:
                ar_section_len = seq_len

            # Create masked section (full masking strategy from Section 3.1)
            mask_section = torch.full(
                (batch_size, ar_section_len),
                self.mask_token_id,
                dtype=torch.long,
                device=device
            )

            # Concatenate: [AR tokens | MASK tokens]
            full_input = torch.cat([input_ids, mask_section], dim=1)
            total_len = full_input.shape[1]

            # Create hybrid attention mask
            attention_mask = self.create_hybrid_attention_mask(
                total_len, ar_section_len, device
            )
        else:
            # Inference mode
            full_input = input_ids
            total_len = seq_len
            ar_section_len = seq_len if ar_section_len is None else ar_section_len
            attention_mask = self.create_hybrid_attention_mask(
                total_len, ar_section_len, device
            )

        # Position IDs
        position_ids = torch.arange(total_len, dtype=torch.long, device=device)
        position_ids = position_ids.unsqueeze(0).expand(batch_size, -1)

        # Embeddings
        token_embeds = self.token_embedding(full_input)
        pos_embeds = self.position_embedding(position_ids)
        hidden_states = self.dropout(token_embeds + pos_embeds)

        # Transformer layers
        for layer in self.layers:
            hidden_states = layer(hidden_states, attention_mask)

        hidden_states = self.norm(hidden_states)
        logits = self.lm_head(hidden_states)

        # Compute loss if labels provided
        loss = None
        if labels is not None:
            # Split into AR and Diffusion sections
            ar_logits = logits[:, :ar_section_len, :]
            diff_logits = logits[:, ar_section_len:, :]

            ar_labels = labels[:, :ar_section_len]
            diff_labels = labels[:, ar_section_len:]

            # AR loss: next token prediction (shifted)
            ar_logits_shifted = ar_logits[:, :-1, :].contiguous()
            ar_labels_shifted = ar_labels[:, 1:].contiguous()
            ar_loss = F.cross_entropy(
                ar_logits_shifted.view(-1, self.config.vocab_size),
                ar_labels_shifted.view(-1),
                ignore_index=-100
            )

            # Diffusion loss: predict all masked tokens (no shift)
            diff_loss = F.cross_entropy(
                diff_logits.contiguous().view(-1, self.config.vocab_size),
                diff_labels.contiguous().view(-1),
                ignore_index=-100
            )

            # Combined loss with balancing factor α (Eq. in Section 3.1)
            alpha = self.config.alpha
            loss = (alpha * ar_loss + diff_loss) / (1 + alpha)

            # Return individual losses for logging
            return {
                'loss': loss,
                'ar_loss': ar_loss,
                'diff_loss': diff_loss,
                'logits': logits
            }

        return {'logits': logits}

    def generate(self, input_ids, max_new_tokens=50, temperature=1.0):
        """
        Simple autoregressive generation
        (Full TiDAR parallel drafting+sampling would be more complex)
        """
        self.eval()

        for _ in range(max_new_tokens):
            # Get predictions
            with torch.no_grad():
                outputs = self.forward(input_ids, ar_section_len=input_ids.shape[1])
                logits = outputs['logits']

                # Get next token logits
                next_token_logits = logits[:, -1, :] / temperature

                # Sample
                probs = F.softmax(next_token_logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)

                # Append
                input_ids = torch.cat([input_ids, next_token], dim=1)

        return input_ids


if __name__ == "__main__":
    # Test the model
    print("Testing TiDAR model...")

    config = TiDARConfig(
        vocab_size=1000,
        hidden_size=256,
        num_layers=4,
        num_heads=4,
        intermediate_size=1024,
        max_seq_len=128,
        block_size=4
    )

    model = TiDARModel(config)

    # Test forward pass
    batch_size = 2
    seq_len = 16
    input_ids = torch.randint(0, config.vocab_size - 1, (batch_size, seq_len))
    labels = torch.randint(0, config.vocab_size - 1, (batch_size, seq_len * 2))

    print(f"Input shape: {input_ids.shape}")

    # Training forward pass
    outputs = model(input_ids, labels=labels)
    print(f"Total loss: {outputs['loss'].item():.4f}")
    print(f"AR loss: {outputs['ar_loss'].item():.4f}")
    print(f"Diffusion loss: {outputs['diff_loss'].item():.4f}")

    # Test generation
    generated = model.generate(input_ids[:1, :8], max_new_tokens=10)
    print(f"Generated shape: {generated.shape}")

    print("\nModel test passed!")
