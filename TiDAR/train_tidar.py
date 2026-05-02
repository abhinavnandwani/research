#!/usr/bin/env python3
"""
Training script for TiDAR model on CHTC

Trains a simplified TiDAR model with:
- Text generation task (language modeling)
- Hybrid AR-Diffusion loss
- WandB tracking for real-time monitoring
- GPU support
"""

import argparse
import os
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
import wandb
from tqdm import tqdm
import json

import sys
sys.path.append(os.path.dirname(__file__))
from model.tidar_model import TiDARModel, TiDARConfig


class SimpleTextDataset(Dataset):
    """
    Simple character-level text dataset for demonstration

    In practice, you'd use a proper tokenized dataset like WikiText or custom data
    """
    def __init__(self, text, seq_len=128, vocab_size=256):
        self.seq_len = seq_len
        self.vocab_size = vocab_size

        # Convert text to token IDs (simple char-level)
        self.tokens = [min(ord(c), vocab_size - 2) for c in text]  # Reserve last token for MASK

        # Calculate number of samples
        self.num_samples = max(1, (len(self.tokens) - seq_len) // (seq_len // 2))

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        start_idx = idx * (self.seq_len // 2)
        end_idx = start_idx + self.seq_len

        if end_idx > len(self.tokens):
            # Pad if needed
            tokens = self.tokens[start_idx:] + [0] * (end_idx - len(self.tokens))
        else:
            tokens = self.tokens[start_idx:end_idx]

        input_ids = torch.tensor(tokens, dtype=torch.long)

        # For TiDAR training, labels are doubled (AR section + Diffusion section)
        # Both sections should have the same ground truth
        labels = torch.cat([input_ids, input_ids])

        return {
            'input_ids': input_ids,
            'labels': labels
        }


def generate_dummy_text(num_chars=50000):
    """Generate dummy text for demonstration purposes"""
    sentences = [
        "The quick brown fox jumps over the lazy dog.",
        "Machine learning models learn patterns from data.",
        "Artificial intelligence is transforming the world.",
        "Neural networks consist of layers of interconnected neurons.",
        "Deep learning requires large amounts of training data.",
        "Transformers use attention mechanisms to process sequences.",
        "Language models can generate coherent text.",
        "Training requires significant computational resources.",
        "GPU acceleration speeds up deep learning training.",
        "Research advances enable new capabilities."
    ]

    text = " ".join(sentences * (num_chars // sum(len(s) for s in sentences) + 1))
    return text[:num_chars]


def train_epoch(model, dataloader, optimizer, scheduler, device, epoch, args):
    """Train for one epoch"""
    model.train()
    total_loss = 0
    total_ar_loss = 0
    total_diff_loss = 0
    num_batches = 0

    pbar = tqdm(dataloader, desc=f"Epoch {epoch}")
    for batch_idx, batch in enumerate(pbar):
        input_ids = batch['input_ids'].to(device)
        labels = batch['labels'].to(device)

        # Forward pass
        outputs = model(input_ids, labels=labels)
        loss = outputs['loss']
        ar_loss = outputs['ar_loss']
        diff_loss = outputs['diff_loss']

        # Backward pass
        optimizer.zero_grad()
        loss.backward()

        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(model.parameters(), args.max_grad_norm)

        optimizer.step()
        scheduler.step()

        # Track metrics
        total_loss += loss.item()
        total_ar_loss += ar_loss.item()
        total_diff_loss += diff_loss.item()
        num_batches += 1

        # Update progress bar
        pbar.set_postfix({
            'loss': f'{loss.item():.4f}',
            'ar': f'{ar_loss.item():.4f}',
            'diff': f'{diff_loss.item():.4f}',
            'lr': f'{scheduler.get_last_lr()[0]:.6f}'
        })

        # Log to WandB
        if batch_idx % args.log_interval == 0:
            step = epoch * len(dataloader) + batch_idx
            wandb.log({
                'batch': step,
                'train_loss': loss.item(),
                'train_ar_loss': ar_loss.item(),
                'train_diff_loss': diff_loss.item(),
                'learning_rate': scheduler.get_last_lr()[0],
            })

    avg_loss = total_loss / num_batches
    avg_ar_loss = total_ar_loss / num_batches
    avg_diff_loss = total_diff_loss / num_batches

    return avg_loss, avg_ar_loss, avg_diff_loss


def evaluate(model, dataloader, device):
    """Evaluate the model"""
    model.eval()
    total_loss = 0
    total_ar_loss = 0
    total_diff_loss = 0
    num_batches = 0

    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Evaluating"):
            input_ids = batch['input_ids'].to(device)
            labels = batch['labels'].to(device)

            outputs = model(input_ids, labels=labels)

            total_loss += outputs['loss'].item()
            total_ar_loss += outputs['ar_loss'].item()
            total_diff_loss += outputs['diff_loss'].item()
            num_batches += 1

    avg_loss = total_loss / num_batches
    avg_ar_loss = total_ar_loss / num_batches
    avg_diff_loss = total_diff_loss / num_batches

    return avg_loss, avg_ar_loss, avg_diff_loss


def generate_samples(model, dataset, device, num_samples=3):
    """Generate text samples"""
    model.eval()
    samples = []

    with torch.no_grad():
        for i in range(num_samples):
            # Get a random seed sequence
            sample_data = dataset[i * len(dataset) // num_samples]
            seed = sample_data['input_ids'][:20].unsqueeze(0).to(device)

            # Generate
            generated = model.generate(seed, max_new_tokens=50, temperature=0.8)

            # Convert back to text (simple char-level)
            text = ''.join([chr(min(int(token), 255)) for token in generated[0]])
            samples.append(text)

    return samples


def main():
    parser = argparse.ArgumentParser(description='Train TiDAR model on CHTC')

    # Model args
    parser.add_argument('--vocab-size', type=int, default=256, help='Vocabulary size')
    parser.add_argument('--hidden-size', type=int, default=512, help='Hidden size')
    parser.add_argument('--num-layers', type=int, default=8, help='Number of layers')
    parser.add_argument('--num-heads', type=int, default=8, help='Number of attention heads')
    parser.add_argument('--block-size', type=int, default=4, help='Diffusion block size')
    parser.add_argument('--alpha', type=float, default=1.0, help='Loss balancing factor')

    # Training args
    parser.add_argument('--epochs', type=int, default=10, help='Number of epochs')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    parser.add_argument('--seq-len', type=int, default=128, help='Sequence length')
    parser.add_argument('--lr', type=float, default=1e-4, help='Learning rate')
    parser.add_argument('--max-grad-norm', type=float, default=1.0, help='Max gradient norm')
    parser.add_argument('--warmup-steps', type=int, default=100, help='Warmup steps')

    # Data args
    parser.add_argument('--text-size', type=int, default=100000, help='Size of generated text')
    parser.add_argument('--train-split', type=float, default=0.9, help='Train split ratio')

    # Logging args
    parser.add_argument('--wandb-project', type=str, default='tidar-chtc', help='WandB project')
    parser.add_argument('--wandb-run-name', type=str, default=None, help='WandB run name')
    parser.add_argument('--log-interval', type=int, default=10, help='Logging interval')
    parser.add_argument('--save-dir', type=str, default='./checkpoints', help='Save directory')

    # CHTC args
    parser.add_argument('--no-cuda', action='store_true', help='Disable CUDA')

    args = parser.parse_args()

    # Device setup
    use_cuda = not args.no_cuda and torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")

    print("=" * 60)
    print("TiDAR Training on CHTC")
    print("=" * 60)
    print(f"Device: {device}")

    if use_cuda:
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"CUDA Version: {torch.version.cuda}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

    print(f"Model: {args.hidden_size}h x {args.num_layers}L x {args.num_heads}heads")
    print(f"Block size: {args.block_size}")
    print(f"Batch size: {args.batch_size}")
    print(f"Sequence length: {args.seq_len}")
    print(f"Epochs: {args.epochs}")
    print("=" * 60)

    # Get HTCondor job info
    htcondor_job_id = os.environ.get('CLUSTER', 'local')
    htcondor_process = os.environ.get('PROCESS', '0')

    # Initialize WandB
    run_name = args.wandb_run_name or f"tidar-job-{htcondor_job_id}"

    wandb.init(
        project=args.wandb_project,
        name=run_name,
        config=vars(args),
        tags=['chtc', 'tidar', 'gpu' if use_cuda else 'cpu']
    )

    wandb.config.update({
        'htcondor_job_id': htcondor_job_id,
        'htcondor_process': htcondor_process,
        'device': str(device),
        'gpu_name': torch.cuda.get_device_name(0) if use_cuda else 'none',
    })

    print(f"\nWandB Run: {wandb.run.name}")
    print(f"WandB URL: {wandb.run.url}\n")

    # Create dataset
    print("Creating dataset...")
    text = generate_dummy_text(args.text_size)

    full_dataset = SimpleTextDataset(text, seq_len=args.seq_len, vocab_size=args.vocab_size)

    # Split into train/val
    train_size = int(len(full_dataset) * args.train_split)
    val_size = len(full_dataset) - train_size

    train_dataset, val_dataset = torch.utils.data.random_split(
        full_dataset, [train_size, val_size]
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,  # CHTC may not support multi-process data loading
        pin_memory=use_cuda
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=use_cuda
    )

    print(f"Train samples: {len(train_dataset)}")
    print(f"Val samples: {len(val_dataset)}\n")

    # Create model
    print("Creating TiDAR model...")
    config = TiDARConfig(
        vocab_size=args.vocab_size,
        hidden_size=args.hidden_size,
        num_layers=args.num_layers,
        num_heads=args.num_heads,
        intermediate_size=args.hidden_size * 4,
        max_seq_len=args.seq_len,
        block_size=args.block_size,
        alpha=args.alpha
    )

    model = TiDARModel(config).to(device)

    num_params = sum(p.numel() for p in model.parameters())
    num_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)

    print(f"Total parameters: {num_params:,}")
    print(f"Trainable parameters: {num_trainable:,}\n")

    # Watch model with WandB
    wandb.watch(model, log='all', log_freq=100)

    # Optimizer and scheduler
    optimizer = AdamW(model.parameters(), lr=args.lr, betas=(0.9, 0.999), weight_decay=0.01)

    total_steps = len(train_loader) * args.epochs
    scheduler = CosineAnnealingLR(optimizer, T_max=total_steps, eta_min=args.lr * 0.1)

    # Training loop
    print("Starting training...\n")
    best_val_loss = float('inf')

    for epoch in range(1, args.epochs + 1):
        print(f"\n{'='*60}")
        print(f"Epoch {epoch}/{args.epochs}")
        print(f"{'='*60}")

        # Train
        train_loss, train_ar_loss, train_diff_loss = train_epoch(
            model, train_loader, optimizer, scheduler, device, epoch, args
        )

        # Evaluate
        val_loss, val_ar_loss, val_diff_loss = evaluate(model, val_loader, device)

        print(f"\nEpoch {epoch} Summary:")
        print(f"  Train Loss: {train_loss:.4f} (AR: {train_ar_loss:.4f}, Diff: {train_diff_loss:.4f})")
        print(f"  Val Loss:   {val_loss:.4f} (AR: {val_ar_loss:.4f}, Diff: {val_diff_loss:.4f})")

        # Log to WandB
        wandb.log({
            'epoch': epoch,
            'train_loss_epoch': train_loss,
            'train_ar_loss_epoch': train_ar_loss,
            'train_diff_loss_epoch': train_diff_loss,
            'val_loss': val_loss,
            'val_ar_loss': val_ar_loss,
            'val_diff_loss': val_diff_loss,
        })

        # Generate samples
        if epoch % 2 == 0:
            print("\nGenerating samples...")
            samples = generate_samples(model, full_dataset, device)
            for i, sample in enumerate(samples):
                print(f"  Sample {i+1}: {sample[:100]}...")
                wandb.log({f'sample_{i+1}': sample})

        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            print(f"\n  New best model! Saving checkpoint...")

            os.makedirs(args.save_dir, exist_ok=True)
            checkpoint_path = os.path.join(args.save_dir, 'best_model.pt')

            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss': val_loss,
                'config': config.__dict__,
            }, checkpoint_path)

            # Log as WandB artifact
            artifact = wandb.Artifact(
                name=f'tidar-model-{wandb.run.id}',
                type='model',
                description=f'Best TiDAR model (val_loss: {val_loss:.4f})'
            )
            artifact.add_file(checkpoint_path)
            wandb.log_artifact(artifact)

    print(f"\n{'='*60}")
    print("Training Complete!")
    print(f"Best Validation Loss: {best_val_loss:.4f}")
    print(f"{'='*60}\n")

    # Final summary
    wandb.run.summary['best_val_loss'] = best_val_loss
    wandb.run.summary['total_epochs'] = args.epochs
    wandb.run.summary['total_params'] = num_params

    wandb.finish()

    print(f"WandB run completed: {wandb.run.url}")
    print("Results saved to WandB!")


if __name__ == '__main__':
    main()
