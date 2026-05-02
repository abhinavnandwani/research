# research

Personal monorepo for HPC tooling, small ML experiments, and one-off data/reading projects.

## Layout

| Path | Purpose |
|------|---------|
| `chtc-tools/` | Scripts and templates for [CHTC](https://chtc.cs.wisc.edu/) (HTCondor, SSH, WandB hooks). |
| `TiDAR/` | TiDAR model + CHTC submit/train scripts (see `TiDAR/README.md`). |
| `rl/` | Reinforcement-learning demos (`uv`-managed; run `uv sync` locally). |
| `law/dhs_reports/` | PDFs + Python to extract structured stats (see `law/dhs_reports/pyproject.toml`). |
| `tpu/` | TPU-related reading notes and draft post. |
| `notes/` | Long-form surveys (e.g. TurboQuant paper list). |

## Local setup

- **Python envs**: Use per-project `uv` environments (`rl/`, `law/dhs_reports/`). Virtualenv directories are gitignored.
- **CHTC / WandB**: Copy `chtc-tools/.chtcrc.example` to `~/.chtcrc` and set real values. For HTCondor, export `WANDB_API_KEY` in your shell before `condor_submit` so `$(WANDB_API_KEY)` expands in `.sub` files.
- **Security**: An API key was previously committed in git history on `main`; rotate that WandB key in your account settings if it was ever pushed or shared.

## Remote branches (historical)

These changes are now folded into this tree: WandB placeholders in examples (was `origin/claude/document-repo-overview-K1EGD`), TurboQuant notes in `notes/turboquant-papers.md` (was `origin/claude/research-turboquant-papers-QxEdk`). Those remote branches can be deleted after you verify this `main`.
