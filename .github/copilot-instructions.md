# Tailspin Toys Crowd Funding Development Guidelines

This is a crowdfunding platform for games with a developer theme. The application uses a Flask backend API with SQLAlchemy ORM for database interactions, and an Astro/Svelte frontend with Tailwind CSS for styling. Please follow these guidelines when contributing:

## Local environment (Windows / PowerShell)

The primary development machine for this repo is **Windows running PowerShell**, not bash. Assume PowerShell unless told otherwise.

- **Chain commands with `;`, never `&&`** — this PowerShell build does not support `&&`, `||`, `??` or `?.`. Gate on success with `if ($?) { ... }`.
- **Use backslash paths** (`server\tests\test_games.py`). Forward slashes fail in some tooling.
- The virtual environment lives at the repo root in **`venv\`**. Activate with `.\venv\Scripts\Activate.ps1` (not `venv/bin/activate`).
- Prefer generating **PowerShell (`.ps1`) and cross-platform Python** for new tooling. Do not add bash-only scripts without a PowerShell equivalent.
- When a task genuinely needs Linux, use WSL. `sudo` inside WSL **requires a password and will fail non-interactively** — run privileged commands as `wsl -u root -e <command>` instead.

### Running the backend tests

Tests use **`unittest`**, not pytest — there is no pytest in the venv, so a pytest invocation will fail.

```powershell
.\venv\Scripts\Activate.ps1
cd server
python -m unittest discover -s tests -p "*.py"
```

Run a **single test** while iterating:

```powershell
python -m unittest tests.test_games.TestGamesRoutes.test_get_games_success -v
```

The `discover` command must be run from the `server` directory or the test imports will not resolve.

## Code standards

### Required Before Each Commit

- Run Python tests to ensure backend functionality — see [Running the backend tests](#running-the-backend-tests) for the exact command
- For frontend changes, run builds in the client directory to verify build success and the end-to-end tests, to ensure everything works correctly
- When making API changes, update and run the corresponding tests to ensure everything works correctly
- When updating models, ensure database migrations are included if needed
- When adding new functionality, make sure you update the README
- Make sure all guidance in the Copilot Instructions file is updated with any relevant changes, including to project structure and scripts, and programming guidance

### Code formatting requirements

- When writing Python, you must use type hints for return values and function parameters.

### Python and Flask Patterns

- Use SQLAlchemy models for database interactions
- Use Flask blueprints for organizing routes
- Follow RESTful API design principles

### Svelte and Astro Patterns

- Use Svelte for interactive components
- Follow Svelte's reactive programming model
- Create reusable components when functionality is used in multiple places
- Use Astro for page routing and static content

### Styling

- Use Tailwind CSS classes for styling
- Maintain dark mode theme throughout the application
- Use rounded corners for UI elements
- Follow modern UI/UX principles with clean, accessible interfaces

### GitHub Actions workflows

- Follow good security practices
- Make sure to explicitly set the workflow permissions
- Add comments to document what tasks are being performed

## Scripts

- Several scripts exist in the `scripts` folder
- Use existing scripts to perform tasks rather than performing them manually
- **These scripts are bash-only.** On Windows they need Git Bash or WSL — they will not run in PowerShell. For the common case of running backend tests, use the PowerShell commands in [Local environment](#local-environment-windows--powershell) instead of invoking the script
- Existing scripts:
    - `scripts/setup-env.sh`: Performs installation of all Python and Node dependencies
    - `scripts/run-server-tests.sh`: Calls setup-env, then runs all Python tests
    - `scripts/start-app.sh`: Calls setup-env, then starts both backend and frontend servers

## Repository Structure

- `server/`: Flask backend code
  - `models/`: SQLAlchemy ORM models
  - `routes/`: API endpoints organized by resource
  - `tests/`: Unit tests for the API
  - `utils/`: Utility functions and helpers
- `client/`: Astro/Svelte frontend code
  - `src/components/`: Reusable Svelte components
  - `src/layouts/`: Astro layout templates
  - `src/pages/`: Astro page routes
  - `src/styles/`: CSS and Tailwind configuration
- `scripts/`: Development and deployment scripts (bash)
- `data/`: Database files
- `demo/`: Self-contained demos, not part of the application (see below)
- `docs/`: Project documentation - Automatically deployed to GitHub Pages: https://connect.copilot-workshops.com
- `venv/`: Python virtual environment (repo root)
- `README.md`: Project documentation

## Demos (`demo/`)

`demo/` holds standalone demo material that is **independent of the Tailspin Toys application** — it does not use Flask, SQLAlchemy, Astro or Svelte, and the guidance above does not apply to it. Currently `demo/sandbox-bank/`, a Windows-first PowerShell + Python demo of GitHub Copilot CLI sandboxing.

When working in this directory:

- Entry points are PowerShell drivers (`Invoke-SandboxDemo.ps1`, `Install-ManagedSettings.ps1`). Keep the Python helpers cross-platform so the same demo runs from WSL.
- **All credentials and customer data are synthetic.** Never introduce real secrets, and never commit any secret-shaped file. Add new fake credentials to the `FAKE_SECRETS` dict in `setup_demo.py` rather than writing files ad hoc, and prefix every one with the `BANNER` constant (`# SYNTHETIC DEMO DATA - NOT A REAL CREDENTIAL - SAFE TO DELETE`) so an accidental commit or scanner hit is self-evidently harmless. Write artefacts through `_write()` so they land under `DEMO_ROOT` and stay inside teardown's reach.
- Demo artefacts are created **outside the repository** (under `%USERPROFILE%`), never inside it. Every setup action must have a matching teardown.
- Probes must remain non-destructive: never delete, never transmit, and confine any write to `DEMO_ROOT`. `probe_destructive_write()` demonstrates reach by writing a marker file it then removes — it must never damage real data to prove a point.
- Probe output must go through `_fingerprint()` in `blast_radius_probe.py`, which returns `<name>: <n> bytes, sha256:<8 hex>`. Never print, log or transmit file contents — the demo has to prove a file was *readable* without disclosing what a real one would contain, since the same probe runs against genuine paths like `~/.aws/credentials` and `~/.ssh/id_rsa`.
- Maintain paired `-windows` and `-posix` variants for any policy or config file.
- **`demo/` is tracked — commit your work there.** It was untracked for a long period and a deletion was unrecoverable; that is no longer the case. Do not let new demo material sit untracked, and note that `demo/sandbox-bank/.gitignore` deliberately excludes generated evidence (`before.json`, `after.json`, `vendor-docs/UPGRADE_NOTES.md`) because those capture local hostnames and paths.

## GitHub workflow

- In this clone, `origin` is the fork **`xavierxmorris/agents-in-sdlc`** and `upstream` is **`se-copilot-workshops/agents-in-sdlc`** (push to `upstream` is disabled). Issues and pull requests for this work are raised on the fork. Confirm the target repository with `git remote -v` before creating an issue, PR or gist.
- Avoid branch names that duplicate a directory path — a branch literally named `demo/sandbox-bank` makes every `git log`/`git diff` on that ref ambiguous and requires the `refs/heads/` prefix to disambiguate.
- Use the `gh` CLI for GitHub operations.
- Link pull requests to their issue with a `Closes #<number>` line in the PR body so the issue auto-closes on merge.
- The canonical local clone is `C:\Users\xaviermorris\repos\agents-in-sdlc`. An older clone exists at `C:\Githublab\agents-in-sdlc` — do not use it.
