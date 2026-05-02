#!/usr/bin/env python3
"""
Monitor WandB runs in real-time for CHTC jobs
"""

import argparse
import time
import sys
from datetime import datetime

try:
    import wandb
except ImportError:
    print("Error: wandb not installed. Install with: pip install wandb")
    sys.exit(1)


def monitor_run(project, entity=None, run_id=None, run_name=None, watch_interval=5):
    """
    Monitor a WandB run in real-time.

    Args:
        project: WandB project name
        entity: WandB entity (username/team)
        run_id: Specific run ID to monitor
        run_name: Run name pattern to match
        watch_interval: How often to check for updates (seconds)
    """
    api = wandb.Api()

    # Construct project path
    if entity:
        project_path = f"{entity}/{project}"
    else:
        # Get default entity
        try:
            default_entity = api.viewer.username
            project_path = f"{default_entity}/{project}"
        except:
            project_path = project

    print(f"Monitoring WandB project: {project_path}")
    print(f"Refresh interval: {watch_interval}s")
    print("=" * 60)

    last_logged_step = {}

    try:
        while True:
            try:
                # Get all runs in project
                runs = api.runs(project_path)

                if not runs:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] No runs found in project '{project_path}'")
                    print("Waiting for runs to appear...")
                    time.sleep(watch_interval)
                    continue

                # Filter runs if specified
                if run_id:
                    runs = [r for r in runs if r.id == run_id]
                elif run_name:
                    runs = [r for r in runs if run_name in r.name]

                # Monitor each run
                for run in runs:
                    run_key = f"{run.id}"

                    # Print run header if new
                    if run_key not in last_logged_step:
                        print(f"\n{'='*60}")
                        print(f"Run: {run.name} ({run.id})")
                        print(f"State: {run.state}")
                        print(f"URL: {run.url}")
                        print(f"Started: {run.created_at}")
                        print(f"{'='*60}\n")
                        last_logged_step[run_key] = -1

                    # Get history
                    history = run.history()

                    if not history.empty:
                        # Get latest metrics
                        latest = history.iloc[-1]
                        current_step = int(latest.get('_step', -1))

                        # Only print if new data
                        if current_step > last_logged_step[run_key]:
                            timestamp = datetime.now().strftime('%H:%M:%S')

                            # Print relevant metrics
                            metrics_str = f"[{timestamp}] {run.name} - Step {current_step}"

                            # Add common metrics
                            if 'epoch' in latest:
                                metrics_str += f" | Epoch: {latest['epoch']:.0f}"
                            if 'train_loss' in latest:
                                metrics_str += f" | Train Loss: {latest['train_loss']:.4f}"
                            if 'train_acc' in latest:
                                metrics_str += f" | Train Acc: {latest['train_acc']:.2f}%"
                            if 'test_acc' in latest:
                                metrics_str += f" | Test Acc: {latest['test_acc']:.2f}%"
                            if 'train_batch_loss' in latest:
                                metrics_str += f" | Batch Loss: {latest['train_batch_loss']:.4f}"
                            if 'train_batch_acc' in latest:
                                metrics_str += f" | Batch Acc: {latest['train_batch_acc']:.2f}%"

                            print(metrics_str)
                            last_logged_step[run_key] = current_step

                        # Check if run completed
                        if run.state == "finished":
                            print(f"\n{'='*60}")
                            print(f"Run {run.name} COMPLETED!")
                            print(f"Summary:")
                            for key, value in run.summary.items():
                                if not key.startswith('_'):
                                    print(f"  {key}: {value}")
                            print(f"{'='*60}\n")
                        elif run.state == "failed":
                            print(f"\n{'='*60}")
                            print(f"Run {run.name} FAILED!")
                            print(f"{'='*60}\n")
                        elif run.state == "crashed":
                            print(f"\n{'='*60}")
                            print(f"Run {run.name} CRASHED!")
                            print(f"{'='*60}\n")

                    else:
                        # No history yet
                        if last_logged_step[run_key] == -1:
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for {run.name} to start logging...")
                            last_logged_step[run_key] = -2  # Mark as waiting

            except Exception as e:
                print(f"Error fetching runs: {e}")

            time.sleep(watch_interval)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
        sys.exit(0)


def list_runs(project, entity=None):
    """List all runs in a project."""
    api = wandb.Api()

    if entity:
        project_path = f"{entity}/{project}"
    else:
        try:
            default_entity = api.viewer.username
            project_path = f"{default_entity}/{project}"
        except:
            project_path = project

    print(f"Runs in project: {project_path}")
    print("=" * 60)

    runs = api.runs(project_path)

    if not runs:
        print("No runs found")
        return

    for run in runs:
        print(f"\nName: {run.name}")
        print(f"ID: {run.id}")
        print(f"State: {run.state}")
        print(f"Created: {run.created_at}")
        print(f"URL: {run.url}")

        if run.summary:
            print("Summary:")
            for key, value in run.summary.items():
                if not key.startswith('_'):
                    print(f"  {key}: {value}")


def main():
    parser = argparse.ArgumentParser(
        description='Monitor WandB runs in real-time',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor all runs in a project
  %(prog)s --project chtc-mnist

  # Monitor specific run by name
  %(prog)s --project chtc-mnist --run-name mnist-job-4628778

  # Monitor with custom entity
  %(prog)s --project chtc-mnist --entity myteam

  # List all runs
  %(prog)s --project chtc-mnist --list

  # Monitor with faster updates
  %(prog)s --project chtc-mnist --interval 2
"""
    )

    parser.add_argument('--project', '-p', required=True,
                        help='WandB project name')
    parser.add_argument('--entity', '-e',
                        help='WandB entity (username/team)')
    parser.add_argument('--run-id',
                        help='Specific run ID to monitor')
    parser.add_argument('--run-name', '-n',
                        help='Run name pattern to match')
    parser.add_argument('--interval', '-i', type=int, default=5,
                        help='Update interval in seconds (default: 5)')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List all runs and exit')

    args = parser.parse_args()

    if args.list:
        list_runs(args.project, args.entity)
    else:
        monitor_run(
            args.project,
            entity=args.entity,
            run_id=args.run_id,
            run_name=args.run_name,
            watch_interval=args.interval
        )


if __name__ == '__main__':
    main()
