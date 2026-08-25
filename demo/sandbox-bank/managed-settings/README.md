# Managed settings artefacts

Two enforcement tiers. Managed `sandbox` keys are a **floor**, not a default:
developers can tighten them, never loosen them, and they combine across
server-managed, MDM and file-based sources in the most restrictive direction.

| File | Scope | Intent |
| --- | --- | --- |
| `baseline-windows.json` | Whole Windows fleet | Sandbox always on, credential stores denied, no allow-all mode |
| `tier1-regulated-windows.json` | Payments / customer-data teams | Adds no-bypass, no token injection, no network, no dev-tool access |
| `baseline-posix.json` | macOS / Linux / WSL fleet | Same floor, POSIX paths |
| `tier1-regulated-posix.json` | macOS / Linux / WSL regulated teams | Same regulated tier, plus `seatbelt.keychainAccess: false` |

The Windows files contain a `REPLACE_USERNAME` placeholder. `Install-ManagedSettings.ps1`
substitutes it, validates the result as JSON, and writes it to Program Files.

## Deployment

**Server-managed (recommended default).** Commit to the enterprise
`.github-private` repository as `copilot/managed-settings.json`. For the
regulated tier, place it at `copilot/teams/tier1-regulated.json` and map it in
`copilot/team-mappings.json`:

```json
{ "tier1-regulated.json": ["payments-engineering", "customer-data-platform"] }
```

Only keys marked `{ "overridable": <value> }` in the enterprise default can be
varied by a team file. Everything else stays governed centrally.

**MDM (Intune).** Values are deployed as individual `REG_SZ` strings under
`HKEY_LOCAL_MACHINE\SOFTWARE\Policies\GitHubCopilot`, using dot-separated keys.
Booleans, arrays and objects are stored as JSON text inside a string value:

| Registry value name | String data |
| --- | --- |
| `sandbox.enabled` | `true` |
| `sandbox.allowBypass` | `false` |
| `sandbox.ghAuth` | `false` |
| `sandbox.userPolicy.network.allowLocalNetwork` | `false` |
| `sandbox.userPolicy.filesystem.deniedPaths` | `["C:\\Users\\jsmith\\.ssh","C:\\Users\\jsmith\\.aws"]` |
| `permissions.disableBypassPermissionsMode` | `disable` |

**File-based fallback** (containers, Codespaces, dev boxes):

| OS | Location |
| --- | --- |
| Windows | `%ProgramFiles%\GitHubCopilot\managed-settings.json` |
| macOS | `/Library/Application Support/GitHubCopilot/managed-settings.json` |
| Linux | `/etc/github-copilot/managed-settings.json` |

On macOS and Linux the CLI **rejects** the file unless it is a regular file
owned by `root`, not group- or world-writable, and not a symlink.

## Path notes

Denied paths must be absolute and **wildcards are not supported**. The POSIX
files use `~` for readability; the Windows files carry an explicit
`C:\Users\REPLACE_USERNAME\...` path, because you cannot express
`C:\Users\*\.ssh`. Template the real per-user path through your MDM, or use
`Install-ManagedSettings.ps1` for a single machine.

Managed `readwritePaths` and `readonlyPaths` are matched against user-configured
lists by **exact path string**, not by parent/child coverage. `deniedPaths` is
additive across every source.

## Trade-offs to socialise before you ship

- `allowDevToolAccess: false` blocks package-registry credentials and shared
  build caches. Restores and builds that rely on an authenticated internal feed
  will fail until you explicitly grant those paths.
- `gitAuth: false` and `ghAuth: false` mean `git push` and `gh pr create` stop
  working inside the sandbox. That is the point for a regulated repo, but it
  changes the developer workflow, so pilot it.
- `allowOutbound: false` breaks dependency installation. Most teams will want a
  pinned proxy instead so egress is inspected rather than severed.
- A proxy is not a complete egress boundary. Some tools ignore proxy settings,
  and on macOS and Linux the proxy is cooperative rather than enforced.
