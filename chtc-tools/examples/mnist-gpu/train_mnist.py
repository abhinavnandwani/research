#!/usr/bin/env python3
"""
MNIST Neural Network Training with WandB and CHTC GPU Support
"""

import argparse
import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import wandb


class SimpleNet(nn.Module):
    """Simple CNN for MNIST classification."""

    def __init__(self):
        super(SimpleNet, self).__init__()
        # Convolutional layers
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)

        # Fully connected layers
        self.fc1 = nn.Linear(64 * 7 * 7, 128)
        self.fc2 = nn.Linear(128, 10)

        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.5)

    def forward(self, x):
        # Conv block 1
        x = self.pool(self.relu(self.conv1(x)))  # 28x28 -> 14x14

        # Conv block 2
        x = self.pool(self.relu(self.conv2(x)))  # 14x14 -> 7x7

        # Flatten
        x = x.view(-1, 64 * 7 * 7)

        # FC layers
        x = self.dropout(self.relu(self.fc1(x)))
        x = self.fc2(x)

        return x


def get_dataloaders(batch_size=64, data_dir='./data'):
    """Create MNIST train and test dataloaders."""

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])

    train_dataset = datasets.MNIST(
        data_dir,
        train=True,
        download=True,
        transform=transform
    )

    test_dataset = datasets.MNIST(
        data_dir,
        train=False,
        download=True,
        transform=transform
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=2
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=2
    )

    return train_loader, test_loader


def train_epoch(model, train_loader, criterion, optimizer, device, epoch):
    """Train for one epoch."""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(device), target.to(device)

        # Forward pass
        optimizer.zero_grad()
        output = model(data)
        loss = criterion(output, target)

        # Backward pass
        loss.backward()
        optimizer.step()

        # Statistics
        running_loss += loss.item()
        _, predicted = output.max(1)
        total += target.size(0)
        correct += predicted.eq(target).sum().item()

        # Log every 100 batches
        if batch_idx % 100 == 0:
            batch_acc = 100. * correct / total
            batch_loss = running_loss / (batch_idx + 1)

            print(f'Epoch {epoch} [{batch_idx}/{len(train_loader)}] '
                  f'Loss: {batch_loss:.4f} Acc: {batch_acc:.2f}%')

            wandb.log({
                'batch': epoch * len(train_loader) + batch_idx,
                'train_batch_loss': loss.item(),
                'train_batch_acc': batch_acc,
            })

    epoch_loss = running_loss / len(train_loader)
    epoch_acc = 100. * correct / total

    return epoch_loss, epoch_acc


def evaluate(model, test_loader, criterion, device):
    """Evaluate on test set."""
    model.eval()
    test_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)

            output = model(data)
            test_loss += criterion(output, target).item()

            _, predicted = output.max(1)
            total += target.size(0)
            correct += predicted.eq(target).sum().item()

    test_loss /= len(test_loader)
    test_acc = 100. * correct / total

    return test_loss, test_acc


def main():
    parser = argparse.ArgumentParser(description='Train MNIST on CHTC GPU')
    parser.add_argument('--batch-size', type=int, default=64, help='Batch size')
    parser.add_argument('--epochs', type=int, default=10, help='Number of epochs')
    parser.add_argument('--lr', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--wandb-project', type=str, default='chtc-mnist',
                        help='WandB project name')
    parser.add_argument('--wandb-run-name', type=str, default=None,
                        help='WandB run name')
    parser.add_argument('--no-cuda', action='store_true', default=False,
                        help='Disable CUDA')

    args = parser.parse_args()

    # Device setup
    use_cuda = not args.no_cuda and torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")

    print("=" * 60)
    print("MNIST Training on CHTC")
    print("=" * 60)
    print(f"Device: {device}")

    if use_cuda:
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"CUDA Version: {torch.version.cuda}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

    print(f"Batch Size: {args.batch_size}")
    print(f"Epochs: {args.epochs}")
    print(f"Learning Rate: {args.lr}")
    print("=" * 60)

    # Get HTCondor job info if available
    htcondor_job_id = os.environ.get('CLUSTER', 'local')
    htcondor_process = os.environ.get('PROCESS', '0')

    # Initialize WandB
    config = {
        'batch_size': args.batch_size,
        'epochs': args.epochs,
        'learning_rate': args.lr,
        'device': str(device),
        'htcondor_job_id': htcondor_job_id,
        'htcondor_process': htcondor_process,
    }

    if use_cuda:
        config['gpu_name'] = torch.cuda.get_device_name(0)
        config['cuda_version'] = torch.version.cuda

    run_name = args.wandb_run_name or f"mnist-job-{htcondor_job_id}"

    wandb.init(
        project=args.wandb_project,
        name=run_name,
        config=config,
        tags=['chtc', 'mnist', 'gpu' if use_cuda else 'cpu']
    )

    print(f"\nWandB Run: {wandb.run.name}")
    print(f"WandB URL: {wandb.run.url}\n")

    # Load data
    print("Loading MNIST dataset...")
    train_loader, test_loader = get_dataloaders(args.batch_size)
    print(f"Training samples: {len(train_loader.dataset)}")
    print(f"Test samples: {len(test_loader.dataset)}\n")

    # Create model
    model = SimpleNet().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    # Log model architecture
    wandb.watch(model, log='all', log_freq=100)

    print("Model architecture:")
    print(model)
    print(f"\nTotal parameters: {sum(p.numel() for p in model.parameters()):,}\n")

    # Training loop
    best_acc = 0.0

    for epoch in range(1, args.epochs + 1):
        print(f"\n{'='*60}")
        print(f"Epoch {epoch}/{args.epochs}")
        print(f"{'='*60}")

        # Train
        train_loss, train_acc = train_epoch(
            model, train_loader, criterion, optimizer, device, epoch
        )

        # Evaluate
        test_loss, test_acc = evaluate(model, test_loader, criterion, device)

        print(f"\nEpoch {epoch} Summary:")
        print(f"  Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%")
        print(f"  Test Loss:  {test_loss:.4f}, Test Acc:  {test_acc:.2f}%")

        # Log to WandB
        wandb.log({
            'epoch': epoch,
            'train_loss': train_loss,
            'train_acc': train_acc,
            'test_loss': test_loss,
            'test_acc': test_acc,
            'learning_rate': args.lr,
        })

        # Save best model
        if test_acc > best_acc:
            best_acc = test_acc
            print(f"  New best accuracy! Saving model...")

            model_path = 'best_model.pth'
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'test_acc': test_acc,
                'test_loss': test_loss,
            }, model_path)

            # Log model as artifact
            artifact = wandb.Artifact(
                name=f'mnist-model-{wandb.run.id}',
                type='model',
                description=f'Best MNIST model (acc: {test_acc:.2f}%)'
            )
            artifact.add_file(model_path)
            wandb.log_artifact(artifact)

    print(f"\n{'='*60}")
    print("Training Complete!")
    print(f"Best Test Accuracy: {best_acc:.2f}%")
    print(f"{'='*60}\n")

    # Final summary
    wandb.run.summary['best_test_acc'] = best_acc
    wandb.run.summary['final_test_acc'] = test_acc
    wandb.run.summary['total_epochs'] = args.epochs

    # Finish WandB
    wandb.finish()

    print(f"WandB run completed: {wandb.run.url}")
    print("Results saved to WandB!")


if __name__ == '__main__':
    main()
