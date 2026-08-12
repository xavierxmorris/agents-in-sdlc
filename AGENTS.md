# Tailspin Toys — Agent Guide

Crowdfunding platform for developer-themed board games. This file is the **portable root context** for any coding agent (Copilot, Claude, Codex, Cursor, Gemini).

Copilot-specific additions live in `.github/copilot-instructions.md`. Path-scoped rules live in `.github/instructions/*.instructions.md`.

## Stack

- **Backend** — Flask + SQLAlchemy ORM, blueprint-per-resource, RESTful
- **Frontend** — Astro 5 (routing, static) + Svelte 5 (interactive) + Tailwind CSS 4
- **Tests** — `unittest` for the API, Playwright for e2e

## Layout

```
server/     Flask backend — models/ routes/ tests/ utils/
client/     Astro + Svelte frontend — src/{components,layouts,pages,styles}/
scripts/    Dev scripts — always prefer these over manual commands
data/       SQLite database files
docs/       Workshop content → https://connect.copilot-workshops.com
```

## Build and test

Always use the provided scripts rather than running commands manually:

```bash
scripts/setup-env.sh         # install all Python + Node dependencies
scripts/run-server-tests.sh  # setup-env, then all Python tests
scripts/start-app.sh         # setup-env, then backend + frontend
```

Frontend checks run from `client/`: `npm run build` and `npm run test:e2e`.

The Python virtual environment is `venv/` in the repository root.

## Conventions

**Python** — type hints on every parameter and return value. Docstrings on every function. SQLAlchemy models for all database access. Register new blueprints in `server/app.py`.

**Frontend** — Svelte for interactive components, Astro for routing and static content. Extract a reusable component as soon as behaviour is needed twice.

**Styling** — Tailwind utility classes only. Dark mode throughout. Rounded corners. Accessible by default.

**Workflows** — explicit `permissions:` on every job. Never interpolate untrusted input (issue titles, comment bodies, branch names) directly into a `run:` step — pass it through `env:` instead.

## Definition of done

1. API change → update and run its tests
2. Frontend change → `npm run build` **and** `npm run test:e2e` both pass
3. Model change → include a migration if the schema moved
4. New functionality → update `README.md`
5. Structural change → update this file and `.github/copilot-instructions.md`

## Agent guidance

Prefer the smallest complete change that satisfies the request. Do not opportunistically refactor unrelated code.

When a task spans backend, frontend, and tests, decompose it and delegate rather than attempting one large edit — see `.github/agents/` for the specialist agents available in this repository.
