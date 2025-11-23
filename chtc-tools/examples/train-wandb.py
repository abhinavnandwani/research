#!/usr/bin/env python3
"""
Example training script with WandB integration for CHTC.

This script demonstrates:
- WandB initialization and logging
- HTCondor environment detection
- Checkpoint saving and artifact tracking
"""

import os
import sys
import argparse
import wandb
import time


def get_htcondor_metadata():
    """Extract metadata from HTCondor environment."""
    metadata = {}

    # HTCondor sets various environment variables
    condor_vars = {
        '_CONDOR_JOB_AD': 'job_ad',
        '_CONDOR_MACHINE_AD': 'machine_ad',
        '_CONDOR_SLOT': 'slot',
        'CLUSTER': 'cluster_id',
        'PROCESS': 'process_id',
    }

    for env_var, key in condor_vars.items():
        value = os.environ.get(env_var)
        if value:
            metadata[key] = value

    return metadata


def train(config):
    """Dummy training function."""
    print(f"Starting training with config: {config}")

    # Simulate training
    for epoch in range(config['epochs']):
        # Simulate some computation
        time.sleep(0.5)

        # Log fake metrics
        train_loss = 1.0 / (epoch + 1) + (config['learning_rate'] * 0.1)
        val_loss = train_loss * 1.1

        wandb.log({
            'epoch': epoch,
            'train_loss': train_loss,
            'val_loss': val_loss,
            'learning_rate': config['learning_rate'],
        })

        print(f"Epoch {epoch}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}")

        # Save checkpoint every 5 epochs
        if (epoch + 1) % 5 == 0:
            checkpoint_path = f"checkpoint_epoch_{epoch+1}.pt"
            with open(checkpoint_path, 'w') as f:
                f.write(f"Checkpoint at epoch {epoch+1}\n")

            # Log checkpoint as artifact
            artifact = wandb.Artifact(
                name=f"model-checkpoint",
                type="model",
                description=f"Checkpoint at epoch {epoch+1}"
            )
            artifact.add_file(checkpoint_path)
            wandb.log_artifact(artifact)

            print(f"Saved checkpoint: {checkpoint_path}")

    print("Training complete!")


def main():
    parser = argparse.ArgumentParser(description="Example WandB training script")
    parser.add_argument('--learning-rate', type=float, default=0.001)
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--epochs', type=int, default=10)
    parser.add_argument('--wandb-project', default='chtc-example')
    parser.add_argument('--wandb-run-name', default=None)

    args = parser.parse_args()

    # Get HTCondor metadata
    htcondor_metadata = get_htcondor_metadata()

    # Initialize WandB
    config = {
        'learning_rate': args.learning_rate,
        'batch_size': args.batch_size,
        'epochs': args.epochs,
        **htcondor_metadata,
    }

    wandb.init(
        project=args.wandb_project,
        name=args.wandb_run_name,
        config=config,
        tags=['chtc', 'example'],
    )

    print(f"WandB run initialized: {wandb.run.name}")
    print(f"WandB URL: {wandb.run.url}")

    # Run training
    try:
        train(config)

        # Mark as successful
        wandb.run.summary['status'] = 'success'

    except Exception as e:
        print(f"Error during training: {e}", file=sys.stderr)
        wandb.run.summary['status'] = 'failed'
        wandb.run.summary['error'] = str(e)
        raise

    finally:
        wandb.finish()


if __name__ == '__main__':
    main()
