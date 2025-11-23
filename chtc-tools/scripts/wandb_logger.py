#!/usr/bin/env python3
"""WandB logger for CHTC jobs."""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import wandb
    import yaml
except ImportError:
    print("Error: Required packages not installed", file=sys.stderr)
    print("Install with: pip install wandb pyyaml", file=sys.stderr)
    sys.exit(1)


class CHTCWandBLogger:
    """Manages WandB logging for CHTC jobs."""

    def __init__(self, api_key: Optional[str] = None, entity: Optional[str] = None):
        """Initialize WandB logger.

        Args:
            api_key: WandB API key (defaults to env var)
            entity: WandB entity/username
        """
        self.api_key = api_key or os.environ.get('WANDB_API_KEY')
        self.entity = entity or os.environ.get('WANDB_ENTITY')

        if self.api_key:
            os.environ['WANDB_API_KEY'] = self.api_key

    def init_run(
        self,
        project: str,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[list] = None,
        job_id: Optional[str] = None,
    ) -> wandb.sdk.wandb_run.Run:
        """Initialize a WandB run for a CHTC job.

        Args:
            project: WandB project name
            name: Run name (defaults to job_id)
            config: Configuration dictionary
            tags: List of tags
            job_id: HTCondor job ID

        Returns:
            WandB run object
        """
        run_name = name or f"chtc-job-{job_id}" if job_id else None
        run_tags = tags or []
        run_tags.append("chtc")

        config = config or {}
        if job_id:
            config['htcondor_job_id'] = job_id
        config['cluster'] = 'chtc'

        run = wandb.init(
            project=project,
            name=run_name,
            config=config,
            tags=run_tags,
            entity=self.entity,
        )

        return run

    def log_job_submission(
        self,
        project: str,
        submit_file: str,
        job_id: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Log job submission to WandB.

        Args:
            project: WandB project
            submit_file: Path to submit file
            job_id: HTCondor job ID
            config: Additional config

        Returns:
            WandB run ID
        """
        # Parse submit file for metadata
        submit_config = self._parse_submit_file(submit_file)

        # Merge configs
        full_config = {**submit_config, **(config or {})}

        run = self.init_run(
            project=project,
            job_id=job_id,
            config=full_config,
        )

        # Log submit file as artifact
        artifact = wandb.Artifact(f"submit-{job_id}", type="submit_file")
        artifact.add_file(submit_file)
        run.log_artifact(artifact)

        run_id = run.id
        run.finish()

        return run_id

    def log_job_completion(
        self,
        run_id: str,
        log_file: Optional[str] = None,
        output_files: Optional[list] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ):
        """Log job completion with results.

        Args:
            run_id: WandB run ID to resume
            log_file: Path to HTCondor log file
            output_files: List of output file paths
            metrics: Dictionary of metrics to log
        """
        # Resume run
        run = wandb.init(id=run_id, resume="must")

        # Parse log file for resource usage
        if log_file and os.path.exists(log_file):
            resource_usage = self._parse_log_file(log_file)
            if resource_usage:
                run.log(resource_usage)

            # Add log as artifact
            artifact = wandb.Artifact(f"logs-{run_id}", type="logs")
            artifact.add_file(log_file)
            run.log_artifact(artifact)

        # Log additional metrics
        if metrics:
            run.log(metrics)

        # Log output files as artifacts
        if output_files:
            artifact = wandb.Artifact(f"outputs-{run_id}", type="results")
            for output_file in output_files:
                if os.path.exists(output_file):
                    artifact.add_file(output_file)
            run.log_artifact(artifact)

        run.finish()

    def _parse_submit_file(self, submit_file: str) -> Dict[str, Any]:
        """Parse HTCondor submit file for configuration.

        Args:
            submit_file: Path to submit file

        Returns:
            Dictionary of configuration
        """
        config = {}

        try:
            with open(submit_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip().lower()
                        value = value.strip()

                        # Extract key resources
                        if key in ['request_cpus', 'request_memory', 'request_disk']:
                            config[key] = value
                        elif key == 'executable':
                            config['executable'] = value
                        elif key == 'universe':
                            config['universe'] = value
        except Exception as e:
            print(f"Warning: Could not parse submit file: {e}", file=sys.stderr)

        return config

    def _parse_log_file(self, log_file: str) -> Optional[Dict[str, Any]]:
        """Parse HTCondor log file for resource usage.

        Args:
            log_file: Path to log file

        Returns:
            Dictionary of resource metrics
        """
        metrics = {}

        try:
            with open(log_file, 'r') as f:
                content = f.read()

                # Look for resource usage lines
                # Example: "Disk (KB)            : 512"
                import re

                # Extract runtime
                runtime_match = re.search(r'Job terminated.*?run time.*?(\d+:\d+:\d+)', content, re.DOTALL)
                if runtime_match:
                    time_str = runtime_match.group(1)
                    h, m, s = map(int, time_str.split(':'))
                    metrics['runtime_seconds'] = h * 3600 + m * 60 + s

                # Extract memory usage
                memory_match = re.search(r'Memory \(MB\)\s*:\s*(\d+)', content)
                if memory_match:
                    metrics['memory_mb'] = int(memory_match.group(1))

                # Extract disk usage
                disk_match = re.search(r'Disk \(KB\)\s*:\s*(\d+)', content)
                if disk_match:
                    metrics['disk_kb'] = int(disk_match.group(1))

        except Exception as e:
            print(f"Warning: Could not parse log file: {e}", file=sys.stderr)
            return None

        return metrics if metrics else None


def main():
    """CLI for WandB logger."""
    parser = argparse.ArgumentParser(description="CHTC WandB Logger")
    parser.add_argument('--api-key', help='WandB API key')
    parser.add_argument('--entity', help='WandB entity/username')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Submit command
    submit_parser = subparsers.add_parser('submit', help='Log job submission')
    submit_parser.add_argument('--project', required=True, help='WandB project')
    submit_parser.add_argument('--submit-file', required=True, help='Submit file path')
    submit_parser.add_argument('--job-id', required=True, help='HTCondor job ID')
    submit_parser.add_argument('--config', help='Additional config (YAML file)')

    # Complete command
    complete_parser = subparsers.add_parser('complete', help='Log job completion')
    complete_parser.add_argument('--run-id', required=True, help='WandB run ID')
    complete_parser.add_argument('--log-file', help='HTCondor log file')
    complete_parser.add_argument('--output-files', nargs='+', help='Output files')
    complete_parser.add_argument('--metrics', help='Metrics (YAML file)')

    args = parser.parse_args()

    logger = CHTCWandBLogger(api_key=args.api_key, entity=args.entity)

    if args.command == 'submit':
        config = {}
        if args.config and os.path.exists(args.config):
            with open(args.config) as f:
                config = yaml.safe_load(f)

        run_id = logger.log_job_submission(
            project=args.project,
            submit_file=args.submit_file,
            job_id=args.job_id,
            config=config,
        )
        print(run_id)

    elif args.command == 'complete':
        metrics = {}
        if args.metrics and os.path.exists(args.metrics):
            with open(args.metrics) as f:
                metrics = yaml.safe_load(f)

        logger.log_job_completion(
            run_id=args.run_id,
            log_file=args.log_file,
            output_files=args.output_files,
            metrics=metrics,
        )
        print(f"Logged completion for run {args.run_id}")


if __name__ == '__main__':
    main()
