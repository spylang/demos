#!/usr/bin/env python3
"""
Local AWS Lambda dev server.

Runs a Lambda binary locally by bridging two servers:
  - Lambda Runtime API (port 9001): the binary polls this for invocations
  - HTTP frontend (port 8080): accepts real HTTP requests from a browser/curl

Usage:
    python aws_devserver.py ./build/demo [--port 8080] [--runtime-port 9001]
"""

import http.server
import json
import os
import queue
import subprocess
import sys
import threading
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Invocation:
    request_id: str
    event: dict
    done: threading.Event = field(default_factory=threading.Event)
    response: Optional[dict] = None


# Shared state between the two servers
_pending: queue.Queue[Invocation] = queue.Queue()
_active: dict[str, Invocation] = {}
_active_lock = threading.Lock()


# ── Lambda Runtime API server ──────────────────────────────────────────────────

class RuntimeHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[runtime] {fmt % args}", flush=True)

    def do_GET(self):
        if not self.path.endswith("/invocation/next"):
            print(f"[runtime] unknown GET {self.path}", flush=True)
            self.send_response(200)
            self.end_headers()
            return

        # Block until an invocation arrives
        inv = _pending.get()
        with _active_lock:
            _active[inv.request_id] = inv

        body = json.dumps(inv.event).encode()
        self.send_response(200)
        self.send_header("Lambda-Runtime-Aws-Request-Id", inv.request_id)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        # Path: /2018-06-01/runtime/invocation/{requestId}/response
        #       /2018-06-01/runtime/invocation/{requestId}/error
        parts = self.path.split("/")
        try:
            idx = parts.index("invocation")
            request_id = parts[idx + 1]
        except (ValueError, IndexError):
            print(f"[runtime] unknown POST {self.path}", flush=True)
            self.send_response(200)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)

        with _active_lock:
            inv = _active.pop(request_id, None)

        if inv is not None:
            try:
                inv.response = json.loads(raw)
            except json.JSONDecodeError:
                inv.response = {"statusCode": 500, "body": raw.decode(errors="replace")}
            inv.done.set()

        self.send_response(202)
        self.end_headers()


# ── HTTP frontend server ───────────────────────────────────────────────────────

class FrontendHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[http]    {fmt % args}", flush=True)

    def handle_any(self):
        path = self.path
        query = ""
        if "?" in path:
            path, query = path.split("?", 1)

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode(errors="replace") if length else ""

        event = {
            "body": body,
            "rawPath": path,
            "rawQueryString": query,
            "requestContext": {"http": {"method": self.command, "path": path}},
            "headers": dict(self.headers),
        }

        inv = Invocation(request_id=str(uuid.uuid4()), event=event)
        _pending.put(inv)

        if not inv.done.wait(timeout=30):
            self.send_response(504)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Lambda timeout\n")
            return

        resp = inv.response
        status = resp.get("statusCode", 200)
        resp_body = resp.get("body", "")
        if isinstance(resp_body, str):
            resp_body = resp_body.encode()

        self.send_response(status)
        for k, v in resp.get("headers", {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(resp_body)))
        self.end_headers()
        self.wfile.write(resp_body)

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = handle_any


# ── Entry point ────────────────────────────────────────────────────────────────

def start(handler_class, host, port, label):
    srv = http.server.ThreadingHTTPServer((host, port), handler_class)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    print(f"{label} on {host}:{port}")
    return srv


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <binary> [--port PORT] [--runtime-port PORT]")
        sys.exit(1)

    binary = sys.argv[1]
    port = 8080
    runtime_port = 9001

    args = sys.argv[2:]
    while args:
        arg = args.pop(0)
        if arg == "--port" and args:
            port = int(args.pop(0))
        elif arg == "--runtime-port" and args:
            runtime_port = int(args.pop(0))

    start(RuntimeHandler, "127.0.0.1", runtime_port, "Lambda Runtime API")
    start(FrontendHandler, "0.0.0.0", port, "HTTP frontend")

    env = {**os.environ, "AWS_LAMBDA_RUNTIME_API": f"127.0.0.1:{runtime_port}"}
    print(f"Open http://localhost:{port}/")

    while True:
        print(f"Starting: {binary}", flush=True)
        proc = subprocess.Popen([binary], env=env)
        try:
            rc = proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            proc.wait()
            break
        print(f"Binary exited (code {rc}), restarting...", flush=True)


if __name__ == "__main__":
    main()
