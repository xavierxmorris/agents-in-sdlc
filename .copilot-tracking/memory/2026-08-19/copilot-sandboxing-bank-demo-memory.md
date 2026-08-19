<!-- markdownlint-disable-file -->
# Memory: copilot-sandboxing-bank-demo

**Created:** 2026-08-19 11:43 (+10:00) | **Last Updated:** 2026-08-19 11:43 (+10:00)

## Task Overview

Repository: `C:\Users\xaviermorris\repos\agents-in-sdlc` (git repo `se-copilot-workshops/agents-in-sdlc`, branch `main`). Tailspin Toys crowdfunding workshop app — Flask/SQLAlchemy backend in `server/`, Astro/Svelte/Tailwind frontend in `client/`.

User is a GitHub/Microsoft solutions engineer working with **Westpac** (Australian regulated bank). Four requests across the session, **all completed**:

1. Can a regulated bank like Westpac use GitHub Copilot sandboxing, and how/why?
2. Build a runnable demo with bank-flavoured use cases plus demo steps.
3. Make the demo Windows-friendly and open the README.
4. List the exact steps and prompts needed to run the demo.

**Constraints honoured:** synthetic data only; nothing destructive; Windows-first; no git commit was made — all work is untracked in the working tree (`git status` shows `?? demo/`).

## Current State

Complete, tested demo created at `demo/sandbox-bank/` — **untracked, nothing committed**.

Files (14 on disk; `before.json` is generated probe evidence, not authored):

| File | Purpose |
|---|---|
| `README.md` | Windows-first runbook, 5 acts, ~35 min, APRA mapping + objection handling |
| `RUNSHEET.md` | Flat list of every command and the **4 exact prompts**, plus a 15-minute cut |
| `Invoke-SandboxDemo.ps1` | Driver. Actions: `Check`, `Setup`, `StartService`, `Probe`, `StopService`, `Teardown`. Background service tracked by PID file at `$env:TEMP\wbc-sandbox-demo-service.pid`; health-checks on start |
| `Install-ManagedSettings.ps1` | Templates `REPLACE_USERNAME`, validates JSON, writes `%ProgramFiles%\GitHubCopilot\managed-settings.json`. Supports `-WhatIf` (no elevation) and `-Remove`; elevation asserted only at write time |
| `blast_radius_probe.py` | **Centrepiece.** 5 probes: (1) read credentials outside cwd, (2) reach internal service on localhost, (3) outbound egress, (4) write into a different repo, (5) inherit tokens/credential stores. Platform-aware candidate path lists (Windows vs POSIX). `--json` writes evidence. Type-hinted per repo convention |
| `internal_payments_api.py` | Stand-in unauthenticated internal bank service on `127.0.0.1:9443`, serves fictional accounts |
| `setup_demo.py` / `teardown_demo.py` | Create/remove synthetic artefacts under `~/wbc-sandbox-demo`, plus generated injection payload at `vendor-docs/UPGRADE_NOTES.md` |
| `managed-settings/` | `baseline-windows.json`, `tier1-regulated-windows.json`, `baseline-posix.json`, `tier1-regulated-posix.json`, plus `README.md` (deployment, Intune registry mapping, trade-offs) |
| `before.json` | Generated unsandboxed probe evidence from verification run |

**Verification performed and passing:**

* Setup ran clean.
* Probe reported **5/5 REACHED** unsandboxed on Windows — 10 of 15 sensitive paths readable, including real `gh` `hosts.yml`, `NuGet.Config`, Docker `config.json`, and **53 credentials enumerable via `cmdkey /list`**.
* BLOCKED rendering path confirmed by stopping the service.
* `--json` evidence output validated.
* All 4 policy JSON files parse after templating.
* `Invoke-SandboxDemo.ps1 -Action Check/Setup/Probe/Teardown` all tested.
* `Install-ManagedSettings.ps1 -WhatIf` tested.
* Teardown leaves no residue (`~/wbc-sandbox-demo` removed, background service stopped).

## Important Discoveries

### Product/technical facts (verified against live GitHub Docs, not recall)

1. **Default sandbox policy grants the user profile (home) directory READ-ONLY, and allows both local network and outbound internet.** So `/sandbox enable` alone does **NOT** protect secrets — `~/.aws/credentials`, gh token stores etc. remain readable. Deny rules must be added explicitly. **Highest-value teaching point** (Act 2b: "sandbox enabled ≠ secrets protected").
2. Local sandboxing is powered by **MXC**; backends are Seatbelt (macOS), bubblewrap (Linux, needs `bwrap` on PATH), ProcessContainer (**Windows Insiders builds only**).
3. GitHub documents local sandboxing as the *lightweight* end of the isolation spectrum — **not** a VM or container. Must not be oversold as a hostile-code boundary.
4. CLI built-in file read/edit tools run in-process and check policy **in software only, no OS backstop**. Shell commands, grep/glob, and sandboxed MCP/LSP servers get real OS enforcement.
5. Managed `sandbox` keys are an **exception to normal precedence**: they act as a **FLOOR** and combine across MDM/server/file-based sources in the **most restrictive** direction. Users can tighten, never loosen.
6. Verified managed-settings schema keys: `sandbox.enabled`, `allowBypass`, `addCurrentWorkingDirectory`, `sandboxMcpServers`, `sandboxLspServers`, `gitAuth`, `ghAuth`, `allowDevToolAccess`, `sandbox.userPolicy.filesystem.{readwritePaths,readonlyPaths,deniedPaths}`, `sandbox.userPolicy.network.{allowOutbound,allowLocalNetwork}`, `sandbox.userPolicy.seatbelt.keychainAccess`, plus `permissions.disableBypassPermissionsMode` (value `"disable"`), `allowedMcpServers`/`deniedMcpServers`, `strictKnownMarketplaces`.
7. Denied paths must be **absolute**; **wildcards are NOT supported** (cannot express `C:\Users\*\.ssh`) → Windows fleets need per-user templating via MDM.
8. Deployment locations: Windows `%ProgramFiles%\GitHubCopilot\managed-settings.json`; macOS `/Library/Application Support/GitHubCopilot/managed-settings.json`; Linux `/etc/github-copilot/managed-settings.json`. On macOS/Linux the CLI rejects the file unless root-owned, not group/world-writable, not a symlink. Intune uses `REG_SZ` values under `HKLM\SOFTWARE\Policies\GitHubCopilot` with dot-separated keys.
9. Cloud sandboxing runs on **Azure Container Apps Sandboxes**; requires an org/enterprise owner to enable the **Cloud Sandbox access** policy (off by default); usage-billed on compute/memory/snapshot storage; lifecycle Active → Stopped (snapshotted) → Deleted; shares policy config with Copilot cloud agent.
10. **Open compliance question:** GitHub Enterprise Cloud data residency for Australia has been GA since Feb 2025, but cloud sandbox **execution and snapshot residency is NOT documented as in-region**. Must be confirmed in writing with the GitHub account team before bank code touches a cloud sandbox.
11. Both features are **public preview**; local sandboxing is experimental (`--experimental` / `/experimental on`).

### Environment facts (this machine)

* Windows 11 Pro 25H2, **build 26200 = retail, NOT Insiders** → local sandbox enforcement unavailable natively. Acts 1, 3, 4, 5 still run; **Act 2 needs WSL2 or Insiders**.
* WSL2 Ubuntu present but `bwrap` **not installed**, and **sudo requires a password**, so the agent could not install bubblewrap. User must run it themselves.
* Windows Python 3.14.2 on PATH; WSL has python3 3.12.3 but no node and no copilot CLI.
* `copilot` and `code` are on PATH on Windows.

### Failed approaches

* **Installing bubblewrap in WSL from the agent** — blocked by password-protected sudo. Left as a user action.
* **Relying on native Windows for live sandbox enforcement** — retail build 26200 lacks ProcessContainer support; enforcement demo must run in WSL2 or an Insiders build.

## Next Steps

1. User to run `wsl -e sudo apt-get install -y bubblewrap` if live Act 2 enforcement is wanted (native Windows build cannot enforce).
2. Optionally commit `demo/sandbox-bank/` — currently untracked, no commit made.
3. Optionally dry-run the full demo end to end once, **including a real Copilot CLI session for Acts 2–4** — not yet exercised. Only the PowerShell/Python harness was tested; the `/sandbox` slash-command flow was never executed because the platform cannot enforce.
4. Confirm cloud sandbox **data residency** with the GitHub account team before recommending cloud sandboxes to Westpac.
5. Consider whether the workshop `docs/` Jekyll site should gain a numbered lesson page for this content (existing pattern: `docs/0-prereqs.md` … `docs/5-reviewing-coding-agent.md`).

## Context to Preserve

### Narrative framing that worked

* **Threat model** is NOT a malicious developer — it is **untrusted content instructing a trusted agent** (prompt injection, Act 3). Model refusal is probabilistic and unauditable; sandbox policy is deterministic and evidenced.
* **Act 1 framing:** "none of this is a Copilot finding — it is the ambient authority every shell command already has; the agent just exercises it faster."
* The `before.json` / `after.json` probe pair is positioned as **CPS 234 control-effectiveness evidence**.
* **APRA mapping used:** CPS 234 (access control, segmentation, DLP, control testing), CPS 230 (operational blast radius / resilience), CPS 231 (third-party risk, via MCP allowlisting).

### Safety design of the demo (important if extending)

* Secrets are **never printed** — only SHA-256 prefix + byte count.
* **No data is ever transmitted** — egress probe does a TCP handshake with no payload.
* **Nothing is deleted** — destructive probe writes and removes a single clearly-named canary.
* All demo data is synthetic and labelled: fake prod DB config, HSM key, SWIFT token, fictional customers, clearly-marked **SIMULATED** prompt-injection payload.

### Conventions

* Repo convention followed: Python type hints on all parameters and return values.
* The 4 demo prompts live in `RUNSHEET.md`; Act 2 prompts deliberately include **"without summarising it"** so the probe table renders in full.

### Open questions

* Cloud sandbox execution/snapshot data residency for Australia — unconfirmed, blocking for Westpac cloud-sandbox recommendation.
* Whether Westpac's Windows fleet can get Insiders builds, or whether WSL2 is the sanctioned path for local sandbox enforcement.
* Whether this content should become a numbered workshop lesson in `docs/`.
