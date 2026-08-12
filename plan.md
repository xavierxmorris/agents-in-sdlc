# Modernization plan — Agents in the SDLC workshop

**Fork:** `xavierxmorris/agents-in-sdlc` (upstream `se-copilot-workshops/agents-in-sdlc`, synced at `aef8522`)
**Date:** 2026-08-12
**Grounded in:** [gh-aw subagents.md](https://github.com/github/gh-aw/blob/main/.github/aw/subagents.md), [gh-aw multi-agent-research.md](https://github.com/github/gh-aw/blob/main/.github/aw/multi-agent-research.md), [github/gh-aw](https://github.com/github/gh-aw)

---

## 1. Where the workshop stands today

Six exercises, ~1,100 lines of docs, over a Flask + SQLAlchemy API and an Astro 5 / Svelte 5 / Tailwind 4 frontend with Playwright e2e.

| # | Exercise | Capability taught |
|---|---|---|
| 0 | Prereqs | Template repo → Codespace |
| 1 | Coding agent | Issue → PR, async delegation |
| 2 | MCP | GitHub MCP server, create backlog |
| 3 | Custom instructions | `copilot-instructions.md`, `*.instructions.md` |
| 4 | Agent mode | Site-wide change in VS Code |
| 5 | Review | Reviewing the coding agent's PR |

It is a solid **single-agent** workshop. Every exercise is one human driving one agent.

## 2. The gap

The product has moved from "an assistant that helps you code" to **an agent platform you operate**. The workshop does not yet teach the platform.

| Capability | Status (Aug 2026) | Workshop |
|---|---|---|
| `AGENTS.md` open standard | GA | ❌ absent |
| Custom agents (`.github/agents/*.agent.md`) | GA — VS Code + JetBrains | ❌ absent |
| Subagents / planner–worker orchestration | GA | ❌ absent |
| Plan agent (plan-then-execute) | GA | ❌ absent |
| Agentic Workflows (`gh-aw`) — Continuous AI | Public preview | ❌ absent |
| Safe outputs, sandboxing, threat detection | via gh-aw | ❌ absent |
| Agent hooks (`.github/hooks/hooks.json`) | Public preview | ❌ absent |
| Model selection & cost control | GA | ❌ absent |
| MCP `gh-proxy`, scoped toolsets | GA | ⚠️ one HTTP server, no scoping |
| Copilot code review | GA | ⚠️ implicit in Ex 5 |

**Stale details also worth fixing**

- `docs/README.md` advertises "prompt files, and chat participants" for Ex 3 — chat participants are legacy terminology, and prompt files are never actually taught.
- `server/requirements.txt` is fully unpinned (`flask`, `sqlalchemy`, `flask_sqlalchemy`, `flask-cors`). This contradicts the repo's own instruction to "follow good security practices" and makes the lab non-reproducible as upstream releases land.
- `.github/workflows/run-tests.yml` uses `actions/setup-python@v4` and `actions/setup-node@v4` — both behind current majors.
- Ex 0 requires the learner to create the repo **inside the `se-copilot-workshops` org** to get coding-agent access. That hard org dependency is the most common cause of a blocked start; a fork-based flow is more portable.
- `.vscode/mcp.json` registers only the GitHub MCP server, despite Playwright already being a project dependency — a free, relevant second server.

## 3. The reframe

> From *"Copilot helps you write this feature"* → *"you design, delegate to, and govern a fleet of agents across the SDLC."*

Three layers, each building on the last:

**Layer 1 — Context engineering.** What the agent knows before it starts.
**Layer 2 — Delegation & orchestration.** Who does the work, and how it is decomposed.
**Layer 3 — Continuous AI.** Work that happens with no human in the loop at all — and the guardrails that make that safe.

## 4. Proposed exercise structure

| # | Exercise | Change | Layer |
|---|---|---|---|
| 0 | Setup | **Revise** — fork-based, drop the org dependency | — |
| 1 | Coding agent | Keep, add model selection + cost framing | 2 |
| 2 | MCP | **Extend** — add Playwright MCP, `gh-proxy`, toolset scoping | 1 |
| 3 | Context engineering | **Rewrite** — `AGENTS.md` first, precedence, prompt files | 1 |
| 4 | Agent mode + plan mode | **Extend** — plan before execute | 2 |
| 5 | **Custom agents & subagents** | **NEW** — planner–worker on the filter feature | 2 |
| 6 | **Continuous AI with `gh-aw`** | **NEW** — agentic workflow with inline subagents | 3 |
| 7 | **Guardrails** | **NEW** — safe outputs, least privilege, hooks | 3 |
| 8 | Review | Keep, add Copilot code review + agentic PR review | 3 |

### 4.1 Ex 3 rewrite — context engineering

Teach the **hierarchy**, not just one file:

```
AGENTS.md                        ← portable root; Copilot, Claude, Codex, Cursor, Gemini
.github/copilot-instructions.md  ← Copilot-specific additions
.github/instructions/*.md        ← path-scoped via applyTo frontmatter
.github/prompts/*.prompt.md      ← invocable, parameterised tasks
```

The teachable moment: the repo already has three `.instructions.md` files but **no `AGENTS.md`**. Learners add it, then observe that the same context now steers a *different vendor's* agent — portability made concrete.

### 4.2 Ex 5 (new) — custom agents & subagent orchestration

Apply the **planner–worker pattern** from gh-aw's `subagents.md` to the existing filter feature:

- Orchestrator (frontier model) — decomposes, synthesises, decides.
- `api-worker` (`model: small`) — Flask blueprint + endpoint.
- `ui-worker` (`model: small`) — Svelte component.
- `test-worker` (`model: small`) — unittest + Playwright specs.
- `reviewer` (`model: large`) — adversarial audit with a **domain-specific hunt list**, not "check carefully".

Key lessons, straight from the source guidance:

- Match model to task — `small` for bounded extraction, `large` for synthesis. This is the cost lever.
- Workers return **compact structured output**, never raw logs or file dumps.
- **One level of delegation only.** No recursive fan-out.
- Bounded, evidence-first worker prompts ("return exact error messages and line references").

### 4.3 Ex 6 (new) — Continuous AI

`gh-aw` compiles Markdown + YAML frontmatter into a real GitHub Actions workflow. Learners ship an **issue-triage workflow with inline subagents** — the repo starts maintaining itself.

This is where the two reference docs the plan is built on pay off directly: `subagents.md` for the inline `## agent:` syntax and model aliases, `multi-agent-research.md` for orchestration policy.

### 4.4 Ex 7 (new) — guardrails

The security exercise the workshop currently lacks:

- Agent jobs are **read-only and sandboxed by default**; writes go through validated `safe-outputs` jobs with scoped permissions.
- Least-privilege `permissions:` blocks.
- Prompt-injection surface: why untrusted issue/PR text never gets interpolated into a shell step.
- `max-ai-credits` and per-run fan-out caps as runaway-cost circuit breakers.
- Agent hooks for policy enforcement at lifecycle points.

### 4.5 Advanced/optional — deep research pattern

For an extended track, `multi-agent-research.md` supplies a genuinely advanced module: anti-convergence orchestration (information hiding, idea-keyed registry, delayed cross-pollination), blocked-route bookkeeping in `cache-memory`, adversarial verification, and an artifact-only return contract. Applied to a real repo question such as *"what is our highest-risk untested code path?"*

## 5. Repo hygiene (do first — small, independent)

| Fix | Why |
|---|---|
| Pin `server/requirements.txt` | Reproducibility + supply chain; repo's own guidance demands it |
| `setup-python@v4` → v5, `setup-node@v4` → v5 | Behind current majors |
| Add `.gitattributes` with `.github/workflows/*.lock.yml linguist-generated=true` | Required before any gh-aw workflow lands |
| Add Playwright MCP to `.vscode/mcp.json` | Already a dependency; free second server for Ex 2 |
| Fix "chat participants" in `docs/README.md` | Legacy terminology |

## 6. Sequencing

1. **Repo hygiene** — independent, no doc churn, lands immediately.
2. **`AGENTS.md` + custom agents + prompt files** — the seed artifacts; enables Ex 3 and Ex 5.
3. **First `gh-aw` workflow** — requires `gh aw compile`; enables Ex 6 and Ex 7.
4. **Doc rewrites** — last, once the artifacts they describe actually exist and have been run.

## 7. Known blocker

`gh extension install github/gh-aw` currently fails from this machine — the `github` org enforces SAML SSO and the active token is not authorized:

```
HTTP 403: Resource protected by organization SAML enforcement
```

Authorize at `https://github.com/orgs/github/sso`, or install via the token-free script. Until then, `gh-aw` workflow `.md` sources can be authored but **not compiled** to `.lock.yml`, and an uncompiled agentic workflow will not run. No hand-written `.lock.yml` should be committed — it is generated output.
