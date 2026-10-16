"""Yerel Python HTTP sunucusu: statik arayüz + ölçüm ve rota API'si.

Yalnızca 127.0.0.1 üzerinde dinler. Kimlik doğrulama veya gerçek cihaz
verisi içermez; internet üzerinde yayımlanacak üretim sunucusu değildir.
"""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import unquote, urlparse
from .service import PROJECT_ROOT, Planner


def reject_nonfinite(value: str) -> None:
    raise ValueError(f"JSON içinde {value} desteklenmiyor.")


class DemoServer(ThreadingHTTPServer):
    daemon_threads = True


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".js": "text/javascript; charset=utf-8",
        ".md": "text/plain; charset=utf-8",
        ".ino": "text/plain; charset=utf-8",
    }

    def __init__(self, *args, planner: Planner, **kwargs):
        self.planner = planner
        super().__init__(*args, directory=str(PROJECT_ROOT), **kwargs)

    def json_response(self, status: int, payload: dict) -> None:
        content = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode(
            "utf-8"
        )
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.json_response(
                200,
                {
                    "app": "temiz-rota",
                    "status": "ok",
                    "engine": "python",
                    "simulation": True,
                },
            )
            return
        if self.static_path_allowed(parsed.path):
            super().do_GET()

    def static_path_allowed(self, path: str) -> bool:
        parts = Path(unquote(path).lstrip("/")).parts
        target = (PROJECT_ROOT / Path(*parts)).resolve()
        if any(part.startswith(".") for part in parts) or not target.is_relative_to(
            PROJECT_ROOT
        ):
            self.send_error(403, "Bu dosya sunulmuyor.")
            return False
        return True

    def do_HEAD(self) -> None:
        if self.static_path_allowed(urlparse(self.path).path):
            super().do_HEAD()

    def list_directory(self, path):
        self.send_error(404, "Directory listing disabled")
        return None

    def do_POST(self) -> None:
        endpoint = urlparse(self.path).path
        if endpoint not in {"/api/plan", "/api/measurement"}:
            self.json_response(404, {"error": "API yolu bulunamadı."})
            return
        origin = self.headers.get("Origin")
        if origin:
            parsed = urlparse(origin)
            try:
                valid_origin = (
                    parsed.scheme == "http"
                    and parsed.hostname in {"127.0.0.1", "localhost"}
                    and parsed.port == self.server.server_port
                )
            except ValueError:
                valid_origin = False
            if not valid_origin:
                self.json_response(403, {"error": "Bu origin kabul edilmiyor."})
                return
        if self.headers.get_content_type() != "application/json":
            self.json_response(415, {"error": "Content-Type application/json olmalı."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 65536:
                self.json_response(
                    413, {"error": "İstek boyutu 1–65536 bayt arasında olmalı."}
                )
                return
            payload = json.loads(
                self.rfile.read(length), parse_constant=reject_nonfinite
            )
            if not isinstance(payload, dict):
                raise ValueError("JSON gövdesi bir nesne olmalı.")
            if endpoint == "/api/measurement":
                result = self.planner.measurement(payload.get("measurement"))
            else:
                if "bins" not in payload or payload["bins"] is None:
                    raise ValueError("bins alanı zorunlu.")
                result = self.planner.plan(
                    payload["bins"], payload.get("threshold", 50)
                )
            self.json_response(200, result)
        except (ValueError, TypeError, UnicodeDecodeError) as error:
            self.json_response(400, {"error": str(error)})


def make_server(port: int = 4173, planner: Planner | None = None) -> DemoServer:
    return DemoServer(
        ("127.0.0.1", port), partial(Handler, planner=planner or Planner())
    )
