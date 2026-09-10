from __future__ import annotations

import json
from pathlib import Path
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from toolkit import (
    CircuitBreakerManager,
    CircuitPolicy,
    DeterministicRouter,
    ExecutionMetrics,
    QuotaManager,
    QuotaPolicy,
    Supervisor,
    ToolCache,
    list_index,
    ensure_index,
)
from toolkit.registry import load_registry, resolve_tool

if getattr(__import__("sys"), "frozen", False):
    ROOT = Path(sys._MEIPASS)
    WEB = ROOT / "desktop" / "index.html"
    STATE = Path.home() / ".content-skills-framework"
else:
    ROOT = Path(__file__).resolve().parents[1]
    WEB = Path(__file__).resolve().parent / "index.html"
    STATE = ROOT
STATE.mkdir(parents=True, exist_ok=True)
DB = STATE / ".content-skills-desktop.sqlite3"

metrics = ExecutionMetrics()
quotas = QuotaManager({
    "host": QuotaPolicy("desktop-host", max_concurrent=2, rate_per_second=2, burst=4),
    "desktop": QuotaPolicy("desktop", max_concurrent=1, rate_per_second=1, burst=2),
})
breakers = CircuitBreakerManager(CircuitPolicy(failure_threshold=3, cooldown_seconds=10))
supervisor = Supervisor(root=ROOT, quota_manager=quotas, circuit_breaker=breakers, metrics=metrics)


def router() -> DeterministicRouter:
    ensure_index(ROOT, DB)
    return DeterministicRouter(ROOT, ToolCache(ROOT, DB))


def json_response(handler: BaseHTTPRequestHandler, status: int, value: Any) -> None:
    body = json.dumps(value, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:
        if self.path == "/api/health":
            json_response(self, 200, {"status": "ready", "version": "0.3.0", "tools": len(load_registry(ROOT))})
            return
        if self.path == "/api/metrics":
            json_response(self, 200, metrics.snapshot().__dict__)
            return
        if self.path in {"/", "/index.html"}:
            body = WEB.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        json_response(self, 404, {"error": "not_found"})

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 2_000_000:
            json_response(self, 413, {"error": "input_too_large"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if self.path == "/api/route":
                decision = router().route(payload)
                json_response(self, 200, decision.to_dict())
                return
            if self.path == "/api/run":
                tool_id = str(payload.get("tool_id", ""))
                spec = resolve_tool(load_registry(ROOT), tool_id)
                if spec is None:
                    json_response(self, 404, {"error": "tool_not_found"})
                    return
                result = supervisor.run_script(
                    spec.runner,
                    payload.get("request", payload),
                    quota_scopes=("host", "desktop"),
                    circuit_key=tool_id,
                )
                json_response(self, 200, {
                    "result": result.result.to_dict(),
                    "duration_ms": result.duration_ms,
                    "isolation": result.isolation,
                    "stdout_bytes": result.stdout_bytes,
                    "stderr_bytes": result.stderr_bytes,
                })
                return
            json_response(self, 404, {"error": "not_found"})
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            json_response(self, 400, {"error": "invalid_request", "message": str(exc)})


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    url = "http://127.0.0.1:8765/"
    print(f"Content Skills Framework GUI: {url}", flush=True)
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
