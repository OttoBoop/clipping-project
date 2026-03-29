# Workspace Configuration â€” Claude Code

This file is the **general workspace hub** for all projects in this repository. Rules here apply to every project unless a per-project `CLAUDE.md` explicitly overrides them.

---

## Projects

| Project | Description | CLAUDE.md |
|---------|-------------|-----------|
| `IA_Educacao_V2` | AI-powered educational grading platform (Prova AI) | `IA_Educacao_V2/CLAUDE.md` |
| `general_scraper` | Modular profile-driven web scraper (Playwright) | `general_scraper/CLAUDE.md` |
| `fgv_scraper` | FGV eClass scraper (mostly deprecated) | `fgv_scraper/CLAUDE.md` |
| `Updating-FlavioValle` | FlavioValle.com website project | â€” |
| `general-ai-workflows` | Workspace orchestration, docs, `.claude/` | This file |

For project-specific commands, deployment URLs, test runners, and environment variables, see the per-project `CLAUDE.md` listed above.

---

## Precedence Rule

**Root `CLAUDE.md` rules apply to ALL projects.** Per-project `CLAUDE.md` files add project-specific content (commands, URLs, test runners, env vars).

If a project needs to override a root rule, it must explicitly state:

> `Override: [root rule being overridden]`
> Justification: [why this project differs]

When no override is declared, the root rule wins.

---

## Important Files (Workspace Level)

| File | Purpose |
|------|---------|
| `docs/PLAN_[feature].md` | Implementation plans (ALWAYS reference the active plan) |
| `docs/FUTURE_GOALS.md` | Queued improvements (check after tasks) |
| `docs/guides/GENERAL_DEPRECATION_AND_UNIFICATION_GUIDE.md` | Canonical deprecation guide |
| `docs/DOCUMENTATION_STRUCTURE.md` | Doc organization reference |
| `docs/logs/` | Bug fix logs (date-prefixed) |
| `docs/postmortems/` | Incident postmortems |
| `docs/legacy/` | Archived/outdated docs |
| `.claude/commands/` | User-facing slash commands |
| `.claude/agents/` | Specialized subagents |

---

## Development Workflow

### MANDATORY: Auto-Trigger Workflow Commands

Claude MUST proactively invoke workflow commands using the Skill tool based on conversation context. Do NOT wait for the user to type slash commands.

| When the user... | Auto-invoke | How |
|-------------------|-------------|-----|
| Requests a new feature or significant change | `/discover [topic]` | Use the Skill tool with skill="discover" |
| Completes discovery (all 9 categories answered + 5/5 gates pass) | `