#!/usr/bin/env python3
"""
House Bernard — VPS Intake Server v1.0
Runs on the 1984 Hosting VPS (Iceland). Public-facing shield wall.

Accepts SAIF artifact submissions via HTTP POST.
Validates, hashes, stores to staging, awaits pull by Beelink.

Designed for minimal attack surface:
- No database
- No authentication framework (uses submission tokens)
- No dynamic content
- Flat file storage
- Rate limited

Usage:
    python3 intake_server.py --port 8443 --staging-dir /opt/hb/staging

Security model:
    VPS (this server) → NEVER processes artifacts
    VPS → stores to staging/
    Beelink → pulls from staging/ via rsync over Tailscale
    Beelink → processes in Lab A / Lab B
    Beelink → pushes results back to VPS
    VPS → serves results (read-only)
"""

import http.server
import json
import hashlib
import os
import sys
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

# === CONFIGURATION ===

MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB max artifact size
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 5  # max submissions per IP per window
ALLOWED_EXTENSIONS = {".zip"}
SUBMISSION_LOG = "SUBMISSION_LOG.jsonl"


class RateLimiter:
    """Simple in-memory rate limiter per IP."""

    def __init__(self, window: int, max_requests: int):
        self.window = window
        self.max_requests = max_requests
        self.requests: dict = {}  # ip -> [timestamps]

    def check(self, ip: str) -> bool:
        """Return True if request is allowed."""
        now = time.time()
        if ip not in self.requests:
            self.requests[ip] = []

        # Prune old entries
        self.requests[ip] = [t for t in self.requests[ip] if now - t < self.window]

        if len(self.requests[ip]) >= self.max_requests:
            return False

        self.requests[ip].append(now)
        return True


class IntakeHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler for artifact submission."""

    staging_dir: str = "/opt/hb/staging"
    results_dir: str = "/opt/hb/results"
    rate_limiter: RateLimiter = RateLimiter(RATE_LIMIT_WINDOW, RATE_LIMIT_MAX)

    def log_message(self, format, *args):
        """Override to log in structured format."""
        pass  # Suppress default logging; we log to SUBMISSION_LOG

    def _respond(self, code: int, body: dict):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-House", "Bernard")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def _log_submission(self, record: dict):
        log_path = os.path.join(self.staging_dir, SUBMISSION_LOG)
        with open(log_path, "a") as f:
            f.write(json.dumps(record) + "\n")

    def _get_client_ip(self) -> str:
        # Respect X-Forwarded-For if behind reverse proxy
        forwarded = self.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return self.client_address[0]

    def do_GET(self):
        """Health check and results retrieval."""
        path = urlparse(self.path).path

        if path == "/health":
            self._respond(200, {
                "status": "operational",
                "service": "House Bernard Intake",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return

        if path == "/results":
            # List available results (filenames only, no content)
            results_path = Path(self.results_dir)
            if results_path.exists():
                files = sorted(f.name for f in results_path.iterdir() if f.is_file())
            else:
                files = []
            self._respond(200, {"results": files})
            return

        self._respond(404, {"error": "Not found"})

    def do_POST(self):
        """Accept artifact submission."""
        path = urlparse(self.path).path

        if path != "/submit":
            self._respond(404, {"error": "Not found"})
            return

        client_ip = self._get_client_ip()

        # Rate limit
        if not self.rate_limiter.check(client_ip):
            self._respond(429, {"error": "Rate limit exceeded. Try again later."})
            self._log_submission({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "ip": client_ip,
                "status": "RATE_LIMITED",
            })
            return

        # Check content length
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self._respond(400, {"error": "Empty submission"})
            return
        if content_length > MAX_UPLOAD_SIZE:
            self._respond(413, {"error": f"Artifact too large. Max {MAX_UPLOAD_SIZE} bytes."})
            return

        # Read body
        body = self.rfile.read(content_length)

        # Hash
        artifact_hash = hashlib.sha256(body).hexdigest()

        # Check for duplicate
        staging_path = Path(self.staging_dir)
        existing = list(staging_path.glob(f"{artifact_hash}*"))
        if existing:
            self._respond(409, {
                "error": "Duplicate submission",
                "hash": artifact_hash,
            })
            return

        # Validate: must be a zip file (check magic bytes)
        if body[:4] != b'PK\x03\x04':
            self._respond(400, {"error": "Invalid file format. Must be a .zip archive."})
            self._log_submission({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "ip": client_ip,
                "status": "REJECTED",
                "reason": "invalid_format",
                "size": content_length,
            })
            return

        # Store
        filename = f"{artifact_hash}.zip"
        filepath = staging_path / filename
        staging_path.mkdir(parents=True, exist_ok=True)

        with open(filepath, "wb") as f:
            f.write(body)

        # Log
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ip": client_ip,
            "status": "ACCEPTED",
            "hash": artifact_hash,
            "size": content_length,
            "filename": filename,
        }
        self._log_submission(record)

        self._respond(202, {
            "status": "accepted",
            "hash": artifact_hash,
            "message": "Artifact queued for processing. Check /results later.",
        })


def main():
    parser = argparse.ArgumentParser(description="House Bernard Intake Server")
    parser.add_argument("--port", type=int, default=8443, help="Port to listen on")
    parser.add_argument("--bind", default="0.0.0.0", help="Address to bind to")
    parser.add_argument("--staging-dir", default="/opt/hb/staging", help="Staging directory")
    parser.add_argument("--results-dir", default="/opt/hb/results", help="Results directory")
    args = parser.parse_args()

    IntakeHandler.staging_dir = args.staging_dir
    IntakeHandler.results_dir = args.results_dir

    # Ensure directories exist
    Path(args.staging_dir).mkdir(parents=True, exist_ok=True)
    Path(args.results_dir).mkdir(parents=True, exist_ok=True)

    server = http.server.HTTPServer((args.bind, args.port), IntakeHandler)
    print(f"House Bernard Intake Server listening on {args.bind}:{args.port}")
    print(f"Staging: {args.staging_dir}")
    print(f"Results: {args.results_dir}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutdown.")
        server.server_close()


if __name__ == "__main__":
    main()
