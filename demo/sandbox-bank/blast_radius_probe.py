"""Measure the blast radius of an agent-run command on this machine.

Run this the same way Copilot CLI would run any shell command - once *outside*
the sandbox and once *inside* it - and compare the two reports. The difference
is the control story.

Runs natively on Windows (PowerShell), macOS and Linux/WSL.

Safety properties (deliberate, so this can be run on a corporate laptop):
  * Secrets are never printed. Only a SHA-256 prefix and byte count are shown.
  * No data is transmitted anywhere. The egress probe opens a TCP connection
    and closes it without sending a payload.
  * Nothing is deleted. The destructive probe writes one clearly named canary
    file and removes only that file.

Usage:
    python blast_radius_probe.py
    python blast_radius_probe.py --json before.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEMO_ROOT: Path = Path.home() / "wbc-sandbox-demo"
INTERNAL_SERVICE: tuple[str, int] = ("127.0.0.1", 9443)
EGRESS_TARGET: tuple[str, int] = ("example.com", 443)
CANARY_NAME: str = "SANDBOX-DEMO-CANARY.txt"
IS_WINDOWS: bool = sys.platform.startswith("win")


@dataclass
class ProbeResult:
    """Outcome of a single blast-radius probe."""

    number: int
    name: str
    reached: bool
    detail: str
    control: str
    evidence: list[str] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        return "REACHED" if self.reached else "BLOCKED"


def _fingerprint(path: Path) -> str:
    """Return a non-reversible marker proving the file was readable."""
    data: bytes = path.read_bytes()
    digest: str = hashlib.sha256(data).hexdigest()[:8]
    return f"{path.name}: {len(data)} bytes, sha256:{digest}"


def _sensitive_paths() -> list[Path]:
    """Credential and data locations a developer workstation typically holds."""
    home: Path = Path.home()
    paths: list[Path] = [
        DEMO_ROOT / "secrets" / "prod-db.conf",
        DEMO_ROOT / "secrets" / "hsm-signing.key",
        DEMO_ROOT / "secrets" / "swift-gateway.env",
        DEMO_ROOT / "secrets" / "customer-extract.csv",
        home / ".aws" / "credentials",
        home / ".ssh" / "id_rsa",
        home / ".gitconfig",
        home / ".npmrc",
        home / ".copilot" / "settings.json",
    ]

    if IS_WINDOWS:
        appdata: Path = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
        local_appdata: Path = Path(
            os.environ.get("LOCALAPPDATA", home / "AppData" / "Local")
        )
        paths += [
            appdata / "GitHub CLI" / "hosts.yml",
            appdata / "npm" / ".npmrc",
            appdata / "NuGet" / "NuGet.Config",
            home / ".azure" / "msal_token_cache.json",
            home / ".docker" / "config.json",
            local_appdata / "Microsoft" / "IdentityCache",
        ]
    else:
        paths += [
            home / ".config" / "gh" / "hosts.yml",
            home / ".azure" / "msal_token_cache.json",
            home / ".docker" / "config.json",
            home / ".kube" / "config",
        ]

    return paths


def probe_credentials() -> ProbeResult:
    """Can a sandboxed command read credentials living outside the repo?"""
    candidates: list[Path] = _sensitive_paths()

    evidence: list[str] = []
    for path in candidates:
        try:
            if path.is_file():
                evidence.append(_fingerprint(path))
        except (PermissionError, OSError) as exc:
            evidence.append(f"{path.name}: blocked ({type(exc).__name__})")

    readable: list[str] = [e for e in evidence if "blocked" not in e]
    return ProbeResult(
        number=1,
        name="Read credentials outside the working directory",
        reached=bool(readable),
        detail=f"{len(readable)} of {len(candidates)} sensitive paths readable",
        control="sandbox.userPolicy.filesystem.deniedPaths",
        evidence=evidence,
    )


def probe_internal_network() -> ProbeResult:
    """Can a sandboxed command reach an internal-only service?"""
    host, port = INTERNAL_SERVICE
    url: str = f"http://{host}:{port}/accounts"
    try:
        with urllib.request.urlopen(url, timeout=3) as response:  # noqa: S310
            payload: dict[str, Any] = json.loads(response.read().decode("utf-8"))
        count: int = int(payload.get("count", 0))
        return ProbeResult(
            number=2,
            name="Reach internal service on the local network",
            reached=True,
            detail=f"pulled {count} customer records from {url}",
            control="sandbox.userPolicy.network.allowLocalNetwork = false",
            evidence=[f"HTTP 200 from {url}", f"records exposed: {count}"],
        )
    except (urllib.error.URLError, OSError, TimeoutError, ValueError) as exc:
        return ProbeResult(
            number=2,
            name="Reach internal service on the local network",
            reached=False,
            detail=f"unreachable ({type(exc).__name__})",
            control="sandbox.userPolicy.network.allowLocalNetwork = false",
            evidence=[f"no response from {url}"],
        )


def probe_egress() -> ProbeResult:
    """Is there an uncontrolled path off the machine? No payload is sent."""
    host, port = EGRESS_TARGET
    try:
        with socket.create_connection((host, port), timeout=4):
            pass
        return ProbeResult(
            number=3,
            name="Open an outbound path to the public internet",
            reached=True,
            detail=f"TCP handshake to {host}:{port} succeeded (no data sent)",
            control="sandbox.userPolicy.network.allowOutbound = false, or a pinned proxy",
            evidence=[f"connect() to {host}:{port} succeeded"],
        )
    except (OSError, TimeoutError) as exc:
        return ProbeResult(
            number=3,
            name="Open an outbound path to the public internet",
            reached=False,
            detail=f"egress blocked ({type(exc).__name__})",
            control="sandbox.userPolicy.network.allowOutbound = false, or a pinned proxy",
            evidence=[f"connect() to {host}:{port} failed"],
        )


def probe_destructive_write() -> ProbeResult:
    """Can a sandboxed command modify a *different* repo on the same disk?"""
    target_dir: Path = DEMO_ROOT / "payments-mainframe-adapter" / "src"
    canary: Path = target_dir / CANARY_NAME
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        canary.write_text(
            "Written by the sandbox demo probe to prove write access. Safe to delete.\n",
            encoding="utf-8",
        )
        canary.unlink()
        return ProbeResult(
            number=4,
            name="Write into a different repository on disk",
            reached=True,
            detail=f"created and removed a canary in {target_dir}",
            control="working-directory scoping plus deniedPaths",
            evidence=[f"write succeeded at {canary}"],
        )
    except (PermissionError, OSError) as exc:
        return ProbeResult(
            number=4,
            name="Write into a different repository on disk",
            reached=False,
            detail=f"write blocked ({type(exc).__name__})",
            control="working-directory scoping plus deniedPaths",
            evidence=[f"write refused at {canary}"],
        )


def probe_inherited_tokens() -> ProbeResult:
    """Which of the developer's tokens does a sandboxed command inherit?"""
    home: Path = Path.home()
    evidence: list[str] = []

    for var in ("GH_TOKEN", "GITHUB_TOKEN", "AZURE_CLIENT_SECRET", "NPM_TOKEN"):
        if os.environ.get(var):
            evidence.append(f"env {var} is present in the command environment")

    stores: list[Path] = [home / ".git-credentials"]
    if IS_WINDOWS:
        appdata: Path = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
        stores += [
            appdata / "GitHub CLI" / "hosts.yml",
            appdata / "Microsoft" / "Credentials",
        ]
    else:
        stores += [home / ".config" / "gh" / "hosts.yml"]

    for path in stores:
        try:
            if path.exists():
                evidence.append(f"credential store reachable: {path.name}")
        except (PermissionError, OSError):
            continue

    if IS_WINDOWS:
        try:
            result = subprocess.run(
                ["cmdkey", "/list"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode == 0 and "Target:" in result.stdout:
                count: int = result.stdout.count("Target:")
                evidence.append(
                    f"Windows Credential Manager enumerable: {count} stored credential(s)"
                )
        except (OSError, subprocess.SubprocessError):
            pass

    return ProbeResult(
        number=5,
        name="Inherit the developer's tokens and credential stores",
        reached=bool(evidence),
        detail=f"{len(evidence)} credential source(s) available to the command",
        control="sandbox.ghAuth / sandbox.gitAuth = false, seatbelt.keychainAccess = false (macOS)",
        evidence=evidence or ["no token sources detected"],
    )


def render(results: list[ProbeResult]) -> None:
    reached: int = sum(1 for r in results if r.reached)

    print()
    print("=" * 78)
    print(" AGENT BLAST-RADIUS REPORT".center(78))
    print("=" * 78)
    print(f" host           : {socket.gethostname()}")
    print(f" platform       : {sys.platform} ({'Windows' if IS_WINDOWS else 'POSIX'})")
    print(f" working dir    : {Path.cwd()}")
    print(f" generated (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    print("-" * 78)

    for result in results:
        marker: str = "!!" if result.reached else "ok"
        print(f"\n [{marker}] {result.number}. {result.name}")
        print(f"      verdict : {result.verdict}")
        print(f"      detail  : {result.detail}")
        print(f"      control : {result.control}")
        for line in result.evidence:
            print(f"                - {line}")

    print("\n" + "-" * 78)
    print(f" {reached} of {len(results)} probes REACHED their target.")
    if reached:
        print(" An unsandboxed agent command inherits all of the access above.")
    else:
        print(" The sandbox policy contained every probe.")
    print("=" * 78 + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", metavar="PATH", help="also write the report as JSON evidence")
    args = parser.parse_args()

    results: list[ProbeResult] = [
        probe_credentials(),
        probe_internal_network(),
        probe_egress(),
        probe_destructive_write(),
        probe_inherited_tokens(),
    ]

    render(results)

    if args.json:
        report: dict[str, Any] = {
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "host": socket.gethostname(),
            "platform": sys.platform,
            "working_directory": str(Path.cwd()),
            "probes": [asdict(r) | {"verdict": r.verdict} for r in results],
            "reached_count": sum(1 for r in results if r.reached),
        }
        Path(args.json).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"JSON evidence written to {args.json}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
