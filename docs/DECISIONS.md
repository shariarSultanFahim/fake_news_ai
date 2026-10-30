# docs/DECISIONS.md: Project Decision Log

This log records decisions, adaptations, and notes as specified in AGENT.md section 0 rule 9 and UNATTENDED execution mode instructions.

## Format
- **Date**: YYYY-MM-DD
- **Decision**: Summary of decision
- **Reason**: Rationale and context

---

## 2026-10-31: Unattended Execution Setup
- **Decision**: Enabled continuous unattended execution covering M0 through M9 per user instructions.
- **Reason**: User requested an unattended session while asleep with automatic fallback to mock/written states if blocked.

## 2026-10-31: Normalizer Commit Hash & PyTorch CPU Pin
- **Decision**: Pinned normalizer git dependency to commit `d405944dde5ceeacb7c2fd3245ae2a9dea5f35c9` (`git+https://github.com/csebuetnlp/normalizer.git@d405944dde5ceeacb7c2fd3245ae2a9dea5f35c9`). Pinned PyTorch to `torch==2.15.0+cpu`.
- **Reason**: AGENT.md section 2 step 2 instructs recording the normalizer commit hash. `transformers==5.20.2` requires PyTorch >= 2.6 (disabling torch integration if < 2.6), and `2.15.0+cpu` satisfies this on CPU with PyTorch wheel repository.

## 2026-10-31: M4 Docker Execution Status
- **Decision**: Dockerfile, docker-compose.yml, Caddyfile, and DEPLOY.md were written and validated structurally. The local Docker Desktop daemon is not running on the Windows host, so Docker Compose is marked "written, not run" in accordance with user instructions. Local uvicorn execution is documented and verified.
- **Reason**: Unattended session rule: "If Docker or another tool is not available, write the files, mark them 'written, not run', and continue."


