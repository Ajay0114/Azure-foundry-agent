"""Local server for the Marina chat widget (web/) and its developer debug panel.

Run it from src/marina-bot with the project's Python (it reads the same conversation state as the bot):

    uv run --no-sync python ui.py                      the widget on a demo page:      http://localhost:8000
    UI_DEBUG=true uv run --no-sync python ui.py        also the developer page:        http://localhost:8000/dev

What it does
  * serves web/ (the embeddable widget, the demo page, and, only with UI_DEBUG, the developer page);
  * POST /api/chat    forwards the customer's message to the bot and returns the reply plus the buttons to offer;
  * GET  /api/debug   (UI_DEBUG only) the execution trace and the conversation variables, for the debug panel.

This server is the "backend for the front end": the browser never talks to the bot or to Azure. Embedding the widget in a real
site means running something like this on your side (with its own login to the bot) and pointing the widget at it. The widget
itself (web/widget.js, web/widget.css) contains no debug code.

Settings (environment variables, all optional)
  BOT_URL      where the bot answers. Default http://localhost:8088/responses. For the deployed agent use its endpoint:
               https://<account>.services.ai.azure.com/api/projects/<project>/agents/<agent>/endpoint/protocols/openai/responses?api-version=v1
  BOT_AUTH     "none" (default for localhost) or "azure": send an Azure token (your az login) to the bot. Default: azure when BOT_URL is not local.
  UI_PORT      default 8000
  UI_DEBUG     "true" to enable /dev and /api/debug. The debug data holds what customers typed: use it in dev and test only.
  UI_HOST      default 127.0.0.1. Local use only: there is no login on this server.
The conversation state (for the buttons and the debug panel) is read with the same settings as the bot (STATE_BLOB_* / MARINA_STATE_DIR).
"""

import json
import mimetypes
import os
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

WEB = Path(__file__).parent / "web"
BOT_URL = os.environ.get("BOT_URL", "http://localhost:8088/responses")
PORT = int(os.environ.get("UI_PORT", "8000"))
HOST = os.environ.get("UI_HOST", "127.0.0.1")
DEBUG = os.environ.get("UI_DEBUG", "").strip().lower() in ("1", "true", "yes", "on")
IS_LOCAL = urlparse(BOT_URL).hostname in ("localhost", "127.0.0.1", "::1")
AUTH = (os.environ.get("BOT_AUTH") or ("none" if IS_LOCAL else "azure")).strip().lower()
MAX_BODY = 64 * 1024
TOKEN_SCOPE = "https://ai.azure.com/.default"
NOISY = {"messages", "transcript", "transcript_rows", "conversationHistoryString", "nodeOutputs", "debug_turns", "suggestions"}

_store = None
_store_error = ""
_token: tuple[str, float] | None = None
_lock = threading.Lock()


def state_store():
    """The conversation state, read with the bot's own settings. None (with a reason) when it cannot be reached."""
    global _store, _store_error
    if _store is None and not _store_error:
        try:
            from dotenv import load_dotenv
            load_dotenv(Path(__file__).parent / ".env")
            from shared.state_store import make_state_store
            _store = make_state_store()
        except Exception as exc:                                # noqa: BLE001  (no store: the chat still works, without buttons)
            _store_error = f"{type(exc).__name__}: {exc}"
    return _store


def bearer() -> str:
    """An Azure access token for the deployed agent, cached until shortly before it expires."""
    global _token
    with _lock:
        if _token is None or time.time() > _token[1] - 120:
            from azure.identity import DefaultAzureCredential
            access = DefaultAzureCredential().get_token(TOKEN_SCOPE)
            _token = (access.token, float(access.expires_on))
        return _token[0]


def ask_bot(body: dict) -> dict:
    """Forward one chat turn to the bot's Responses endpoint and flatten the answer for the widget."""
    text, files = str(body.get("text") or ""), [u for u in body.get("files") or [] if isinstance(u, str)]
    content = [{"type": "input_text", "text": text}] + [{"type": "input_file", "file_url": u} for u in files]
    request = {"input": [{"role": "user", "content": content}] if files else text, "stream": False}
    if body.get("previous"):
        request["previous_response_id"] = body["previous"]
    if body.get("session"):
        request["agent_session_id"] = body["session"]        # the host scopes saved workflow state by session
    headers = {"Content-Type": "application/json"}
    try:
        if AUTH == "azure":
            headers["Authorization"] = f"Bearer {bearer()}"
        req = urllib.request.Request(BOT_URL, data=json.dumps(request).encode(), headers=headers)
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.load(resp)
            header_session = resp.headers.get("x-agent-session-id") or resp.headers.get("x-ms-agent-session-id")
    except urllib.error.HTTPError as exc:
        return {"error": f"The bot answered with HTTP {exc.code}."}
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return {"error": f"The bot is not reachable at {urlparse(BOT_URL)._replace(query='').geturl()}."}
    except Exception as exc:                                     # noqa: BLE001  (a token problem, for example)
        return {"error": f"Could not call the bot: {type(exc).__name__}."}
    parts = [c.get("text", "") for item in data.get("output") or [] for c in item.get("content") or [] if c.get("type") == "output_text"]
    if (data.get("error") or {}).get("message"):
        return {"error": data["error"]["message"]}
    session = data.get("agent_session_id") or header_session or body.get("session")
    return {"reply": "\n".join(parts), "previous": data.get("id"), "session": session, "suggestions": suggestions_for(session, data.get("id"))}


def load_state(*keys: str | None) -> dict | None:
    keys = [k for k in keys if k]
    store = state_store() if keys else None
    if store is None:
        return None
    try:
        return store.load(keys) or None
    except Exception:                                            # noqa: BLE001
        return None


def suggestions_for(*keys: str | None) -> list[str]:
    state = load_state(*keys)
    labels = ((state or {}).get("session") or {}).get("suggestions") or []
    return [str(label) for label in labels][:8]


def debug_for(*keys: str | None) -> dict:
    state = load_state(*keys)
    if state is None:
        return {"available": False, "reason": _store_error or "No saved state for this conversation yet.", "turns": [], "variables": {}}
    s = state.get("session") or {}
    return {"available": True, "turns": s.get("debug_turns") or [],
            "variables": {"session": {k: v for k, v in s.items() if k not in NOISY}, "entities": state.get("entities") or {}},
            "tracing": bool(s.get("debug_turns"))}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, data: dict) -> None:
        self._send(status, json.dumps(data).encode(), "application/json")

    def _file(self, name: str) -> None:
        path = (WEB / name).resolve()
        if WEB.resolve() not in path.parents or not path.is_file() or (name == "dev.html" and not DEBUG):
            self._send(404, b"Not found", "text/plain")
            return
        kind = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self._send(200, path.read_bytes(), f"{kind}; charset=utf-8" if kind.startswith(("text/", "application/javascript")) else kind)

    def do_GET(self) -> None:
        url = urlparse(self.path)
        if url.path == "/":
            self._file("demo.html")
        elif url.path == "/dev":
            self._file("dev.html")
        elif url.path == "/api/config":
            self._json(200, {"debug": DEBUG, "botUrl": urlparse(BOT_URL)._replace(query="").geturl(), "auth": AUTH})
        elif url.path == "/api/debug":
            if not DEBUG:
                self._send(404, b"Not found", "text/plain")
            else:
                query = parse_qs(url.query)
                self._json(200, debug_for(*(query.get(k, [None])[0] for k in ("session", "previous"))))
        elif url.path.lstrip("/") in {"widget.js", "widget.css"} or url.path.lstrip("/").startswith("assets/"):
            self._file(url.path.lstrip("/"))
        else:
            self._send(404, b"Not found", "text/plain")

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/chat":
            self._send(404, b"Not found", "text/plain")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(min(length, MAX_BODY)) or b"{}")
            if not isinstance(body, dict):
                raise ValueError
        except (ValueError, json.JSONDecodeError):
            self._json(400, {"error": "Bad request."})
            return
        self._json(200, ask_bot(body))

    def log_message(self, fmt: str, *args) -> None:        # keep the terminal quiet (messages can hold customer details)
        pass


def main() -> None:
    try:
        server = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError as exc:
        raise SystemExit(f"Cannot listen on port {PORT} ({exc.strerror}). Something else is using it, or an earlier ui.py is still "
                         f"running. Pick another port:  UI_PORT=8010 uv run --no-sync python ui.py")
    print(f"Marina chat widget:  http://localhost:{PORT}" + (f"   developer page: http://localhost:{PORT}/dev" if DEBUG else ""))
    print(f"bot: {urlparse(BOT_URL)._replace(query='').geturl()}  (auth: {AUTH})   Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
