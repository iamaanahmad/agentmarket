# AgentMarket Specification Workspace (.kiro)

This folder captures the spec-driven workflow we followed using Kiro IDE and AWS Q Developer. Judges can verify that every feature shipped against a written requirement and trace decisions from concept to code.

## Folder Overview

| Path | Purpose |
|------|---------|
| `requirements.md` | User stories in EARS format with acceptance criteria.
| `design.md` | System architecture, data models, AWS + Solana diagrams.
| `tasks.md` | Granular implementation checklist mapped to requirements.
| `steering/` | Strategic guides (project context, AWS integration, coding standards, security policies).
| `specs/` | Deep dives for subsystems (e.g., SecurityGuard AI pipeline).
| `aws-q-developer-evidence/` | Proof of AI-assisted development via AWS Q Developer.

## How We Use This Workspace
1. **Discover** – Capture feature requirements in `requirements.md`.
2. **Design** – Detail architecture and data flows in `design.md` before writing code.
3. **Plan** – Break requirements into trackable tasks in `tasks.md` with estimates.
4. **Implement** – Reference specs during development; link commits to task IDs.
5. **Validate** – Ensure acceptance criteria and test plans are satisfied before marking tasks complete.
6. **Document** – Record AWS Q Developer interactions to show AI-assisted productivity.

## Workflow Example
- Requirement `R-AGENT-001` (Register Agent) → Detailed in `requirements.md`.
- Design Section `D-3.1` outlines smart contract + API responsibilities.
- Tasks `T-12`..`T-20` implement frontend form, API route, contract instruction.
- AWS Q Developer generated the initial `/api/agents/register` handler (documented in `aws-q-developer-evidence/api-generation/agents-register.md`).
- Final implementation references the requirement ID in commit messages and pull requests.

## How Judges Can Verify
- Open `requirements.md` to see fully fleshed user stories.
- Cross-reference `tasks.md` to confirm each requirement became actionable work.
- Inspect `aws-q-developer-evidence/` to see prompts, outputs, and impact metrics for Amazon Q Developer involvement.
- Review `steering/` files to understand strategic decisions (AWS architecture, coding standards, security plan).

## Maintenance Checklist
- Update `tasks.md` after sprint planning or scope changes.
- Log notable AWS Q Developer sessions the same day they occur.
- Keep `design.md` in sync with architectural changes (e.g., new AWS service adoption).
- Refresh summary metrics in `aws-q-developer-evidence/README.md` before submission.

By presenting this organized specification workspace, we cover the 20-point "Kiro IDE Implementation" judging criterion and demonstrate enterprise-grade discipline.