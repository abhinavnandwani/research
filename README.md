# research

Personal repo: reading notes and CHTC helper tooling.

## Layout

| Path | Purpose |
|------|---------|
| `papers/ai-for-silicon-design/` | Notes and reading queue for AI-for-silicon-design topics. |
| `papers/llm-architecture/` | Long-form paper surveys (e.g. TurboQuant). |
| `papers/tpu/` | TPU-related PDF and notes. |
| `utils/chtc-tools/` | Scripts and templates for [CHTC](https://chtc.cs.wisc.edu/) (HTCondor, SSH, WandB hooks). |

## Local setup

- **CHTC / WandB**: Copy `utils/chtc-tools/.chtcrc.example` to `~/.chtcrc` and set real values. For HTCondor, export `WANDB_API_KEY` before `condor_submit` so `$(WANDB_API_KEY)` expands in `.sub` files.
- **Python**: If you use local venvs under this tree, keep them gitignored (see root `.gitignore`).

Older topics (`TiDAR`, `rl`, `law/dhs_reports`, top-level `tpu/`, `notes/`) have been removed from this checkout.

## Git / security

`main` may still contain historical commits with a leaked WandB key; rotate keys if that history was ever public.
