import json
import threading
import webbrowser
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote

from settings import CONFIG, ROOT
from cutter import BACKUP, duration, keep, export

HOST: str = CONFIG["server"]["host"]
PORT: int = CONFIG["server"]["port"]
PRINT_HOST: str = CONFIG["server"]["print_host"]
OPEN_BROWSER: bool = CONFIG["server"]["open_browser"]
CHUNK: int = CONFIG["io"]["chunk_bytes"]
DEFAULT_NAME: str = CONFIG["io"]["default_filename"]
INDEX: Path = ROOT / CONFIG["paths"]["web_dir"] / CONFIG["paths"]["index_file"]
SUFFIX: str = CONFIG["paths"]["output_suffix"]

SRC: Path = ROOT
OUT: Path = ROOT


def set_source(name: str) -> None:
    global SRC, OUT
    BACKUP.mkdir(parents=True, exist_ok=True)
    SRC = BACKUP / Path(name).name
    OUT = ROOT / (SRC.stem + SUFFIX + SRC.suffix)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args) -> None:
        pass

    def respond(self, code: int, mime: str, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def sse(self, event: str, data: dict) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.wfile.write(f"event: {event}\ndata: ".encode() + payload + b"\n\n")
        self.wfile.flush()

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self.respond(200, "text/html; charset=utf-8", INDEX.read_bytes())

    def do_POST(self) -> None:
        if self.path == "/api/load":
            n: int = int(self.headers.get("Content-Length", "0"))
            set_source(unquote(self.headers.get("X-Filename", DEFAULT_NAME)))
            with SRC.open("wb") as f:
                left: int = n
                while left > 0:
                    chunk: bytes = self.rfile.read(min(CHUNK, left))
                    f.write(chunk)
                    left -= len(chunk)
            self.respond(200, "application/json", json.dumps({"name": SRC.name}).encode())
        elif self.path == "/api/cut":
            n: int = int(self.headers.get("Content-Length", "0"))
            cuts: list[list[float]] = json.loads(self.rfile.read(n))["cuts"]
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            emit = lambda line: self.sse("log", {"line": line})
            audio_ok = export(str(SRC), OUT, keep(duration(str(SRC)), [tuple(c) for c in cuts]), emit)
            result = {"file": OUT.name, "size": OUT.stat().st_size, "audio_ok": audio_ok}
            self.sse("done", result)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"服务已启动，请在浏览器打开：http://{PRINT_HOST}:{PORT}")
    if OPEN_BROWSER:
        threading.Thread(target=webbrowser.open, args=(f"http://{PRINT_HOST}:{PORT}",)).start()
    server.serve_forever()


if __name__ == "__main__":
    main()
