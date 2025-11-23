# CHTC Tools - Complete Documentation

Comprehensive documentation for managing CHTC (Center for High Throughput Computing) operations.

## Documentation Structure

### 📚 Guides
Step-by-step instructional documents:
- **[Getting Started](guides/getting-started.md)** - First-time setup and basics
- **[File Transfer Guide](guides/file-transfer.md)** - Managing data movement
- **[Container Guide](guides/containers.md)** - Building and using containers
- **[GPU Jobs Guide](guides/gpu-jobs.md)** - Running GPU workloads
- **[DAG Workflows](guides/dag-workflows.md)** - Multi-step job workflows
- **[WandB Integration](guides/wandb-integration.md)** - Experiment tracking

### 📖 Reference
Technical specifications and syntax:
- **[Submit File Reference](reference/submit-file-reference.md)** - Complete submit file syntax
- **[HTCondor Commands](reference/htcondor-commands.md)** - Command reference
- **[Resource Requests](reference/resource-requests.md)** - CPU, memory, disk, GPU
- **[File Transfer Protocols](reference/file-transfer-protocols.md)** - OSDF, staging, etc.
- **[Environment Variables](reference/environment-variables.md)** - HTCondor variables

### 🎓 Tutorials
Practical examples and walkthroughs:
- **[First HTCondor Job](tutorials/first-job.md)** - Submit your first job
- **[Parameter Sweeps](tutorials/parameter-sweeps.md)** - Multiple job variations
- **[GPU Machine Learning](tutorials/gpu-ml.md)** - ML training on GPUs
- **[Building Containers](tutorials/building-containers.md)** - Create custom containers
- **[Data Pipelines](tutorials/data-pipelines.md)** - Multi-stage workflows

### 🔧 Troubleshooting
Problem-solving and debugging:
- **[Common Errors](troubleshooting/common-errors.md)** - Frequent issues and solutions
- **[Job Holds](troubleshooting/job-holds.md)** - Understanding and fixing holds
- **[Resource Issues](troubleshooting/resource-issues.md)** - Memory, disk problems
- **[File Transfer Failures](troubleshooting/file-transfer.md)** - Transfer debugging
- **[Container Issues](troubleshooting/container-issues.md)** - Container problems

## Quick Links

### Essential Reading
1. [Getting Started Guide](guides/getting-started.md)
2. [Submit File Reference](reference/submit-file-reference.md)
3. [Common Errors](troubleshooting/common-errors.md)

### By Task
- **Running your first job**: [First HTCondor Job Tutorial](tutorials/first-job.md)
- **Using GPUs**: [GPU Jobs Guide](guides/gpu-jobs.md)
- **Large datasets**: [File Transfer Guide](guides/file-transfer.md)
- **Custom software**: [Container Guide](guides/containers.md)
- **Complex workflows**: [DAG Workflows](guides/dag-workflows.md)
- **Experiment tracking**: [WandB Integration](guides/wandb-integration.md)

### By Problem
- **Job won't start**: [Job Holds](troubleshooting/job-holds.md)
- **Out of memory**: [Resource Issues](troubleshooting/resource-issues.md)
- **Can't find files**: [File Transfer Failures](troubleshooting/file-transfer.md)
- **Container won't run**: [Container Issues](troubleshooting/container-issues.md)

## Official Resources

### CHTC Documentation
- [CHTC Home](https://chtc.cs.wisc.edu/)
- [UW Research Computing](https://chtc.cs.wisc.edu/uw-research-computing/)
- [HTCondor Job Submission](https://chtc.cs.wisc.edu/uw-research-computing/htcondor-job-submission)
- [File Transfer Documentation](https://chtc.cs.wisc.edu/uw-research-computing/htc-job-file-transfer)
- [GPU Jobs](https://chtc.cs.wisc.edu/uw-research-computing/gpu-jobs)
- [Container Documentation](https://chtc.cs.wisc.edu/uw-research-computing/apptainer-htc)

### HTCondor Official Docs
- [HTCondor Manual](https://htcondor.readthedocs.io/)
- [Submitting a Job](https://htcondor.readthedocs.io/en/latest/users-manual/submitting-a-job.html)
- [DAGMan Introduction](https://htcondor.readthedocs.io/en/latest/automated-workflows/dagman-introduction.html)
- [Troubleshooting](https://htcondor.readthedocs.io/en/main/users-manual/troubleshooting.html)

### Community Resources
- CHTC Support: chtc@cs.wisc.edu
- Office Hours: Tuesdays 10:30am-12pm, Thursdays 3-4:30pm

## Contributing

Found an error or want to add something? The documentation is located in `chtc-tools/docs/`.

## Version

Documentation last updated: November 2025
HTCondor Version: 25.5.0
