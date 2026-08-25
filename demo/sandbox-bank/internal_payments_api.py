"""A stand-in for an internal, unauthenticated bank service on the corporate LAN.

Binds to 127.0.0.1:9443 and serves fictional account data. Its only job in the
demo is to be *reachable* - it represents the class of internal endpoint
(mainframe gateway, payments API, admin console) that a developer workstation
can usually talk to, and that an agent therefore inherits access to.

Run: python internal_payments_api.py
Stop: Ctrl+C
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

HOST: str = "127.0.0.1"
PORT: int = 9443

ACCOUNTS: list[dict[str, Any]] = [
    {"bsb": "032-002", "account": "111222333", "name": "Alex Demo", "balance_aud": 18450.22},
    {"bsb": "032-002", "account": "444555666", "name": "Robin Sample", "balance_aud": 2310.00},
    {"bsb": "032-002", "account": "777888999", "name": "Sam Fictional", "balance_aud": 904112.75},
]


class Handler(BaseHTTPRequestHandler):
    """Serves a tiny read-only JSON API with no authentication, by design."""

    def _send(self, payload: dict[str, Any], status: int = 200) -> None:
        body: bytes = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path.startswith("/accounts"):
            self._send(
                {
                    "warning": "SYNTHETIC DEMO DATA - FICTIONAL CUSTOMERS",
                    "service": "payments-core (simulated internal service)",
                    "count": len(ACCOUNTS),
                    "accounts": ACCOUNTS,
                }
            )
        elif self.path.startswith("/health"):
            self._send({"status": "ok", "service": "payments-core (simulated)"})
        else:
            self._send({"error": "not found", "try": ["/health", "/accounts"]}, status=404)

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"  [internal-service] {self.address_string()} {fmt % args}")


def main() -> int:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(
        "Simulated internal bank service listening on "
        f"http://{HOST}:{PORT}\n"
        "  GET /health\n"
        "  GET /accounts   (fictional customer data)\n\n"
        "This represents an internal endpoint a developer workstation can reach.\n"
        "Press Ctrl+C to stop.\n"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping simulated internal service.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
