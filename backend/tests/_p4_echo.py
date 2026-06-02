"""Local echo server used by P4 real-HTTP verification tests."""

from __future__ import annotations

import json
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Deque


@dataclass
class EchoRequest:
    """One captured inbound request."""

    method: str
    path: str
    query: dict[str, str]
    headers: dict[str, str]
    body: str
    received_at: float


@dataclass
class ToolEchoServer:
    """Stdlib HTTP server that records inbound requests for assertions."""

    host: str
    port: int
    _server: ThreadingHTTPServer
    _thread: threading.Thread
    requests: Deque[EchoRequest] = field(default_factory=deque)

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def reset(self) -> None:
        self.requests.clear()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)


def _build_handler(
    state: dict[str, Any],
) -> type[BaseHTTPRequestHandler]:
    """Create a request handler bound to a shared mutable state dict."""

    class EchoHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            del format, args

        def do_GET(self) -> None:  # noqa: N802
            self._handle("GET")

        def do_POST(self) -> None:  # noqa: N802
            self._handle("POST")

        def do_PUT(self) -> None:  # noqa: N802
            self._handle("PUT")

        def do_DELETE(self) -> None:  # noqa: N802
            self._handle("DELETE")

        def _handle(self, method: str) -> None:
            length = int(self.headers.get("Content-Length", "0") or 0)
            raw_body = self.rfile.read(length) if length else b""
            from urllib.parse import parse_qs, urlsplit

            split = urlsplit(self.path)
            query_pairs = parse_qs(split.query, keep_blank_values=True)
            flat_query: dict[str, str] = {}
            for key, values in query_pairs.items():
                if values:
                    flat_query[key] = values[0]
            request = EchoRequest(
                method=method,
                path=split.path,
                query=flat_query,
                headers={key: value for key, value in self.headers.items()},
                body=raw_body.decode("utf-8", errors="replace"),
                received_at=time.time(),
            )
            state["requests"].append(request)
            payload: dict[str, Any] = {
                "echoed": {
                    "method": method,
                    "path": split.path,
                    "query": flat_query,
                    "headers": dict(self.headers.items()),
                    "body": request.body,
                }
            }
            if split.path == "/fail":
                body = json.dumps({"error": "boom"}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if split.path == "/slow":
                time.sleep(state.get("slow_delay", 2.0))
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return EchoHandler


def start_echo_server(
    *,
    host: str = "127.0.0.1",
    port: int = 0,
    slow_delay: float = 2.0,
) -> ToolEchoServer:
    """Start a daemon HTTP echo server and return its handle."""
    state: dict[str, Any] = {
        "requests": deque(),
        "slow_delay": slow_delay,
    }
    handler = _build_handler(state)
    httpd = ThreadingHTTPServer((host, port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return ToolEchoServer(
        host=host,
        port=httpd.server_address[1],
        _server=httpd,
        _thread=thread,
        requests=state["requests"],
    )
