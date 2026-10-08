"""A small web chat page for the local bot (stdlib only, like chat.py).

Usage:   python3 ui.py             then open http://localhost:8000   (the bot must be running on :8088)

The page is served from here and its messages are forwarded to the bot's /responses endpoint, so the browser never
talks to the bot directly (no cross-origin problems). It keeps the conversation the same way chat.py does: the id of the
last response and the session id the bot hands back. "Attach a file link" adds an https link that is sent with your
next message (the attachment service downloads it, so it must be a link, not a file from your disk).

Settings (optional environment variables):  BOT_URL (default http://localhost:8088/responses), UI_PORT (default 8000).
Local use only: it listens on 127.0.0.1 and has no login.
"""

import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BOT_URL = os.environ.get("BOT_URL", "http://localhost:8088/responses")
PORT = int(os.environ.get("UI_PORT", "8000"))
MAX_BODY = 64 * 1024

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Marina</title>
<style>
  :root {
    --bg: #f4f6f8; --panel: #ffffff; --text: #1d2733; --muted: #6b7785; --line: #e2e7ec;
    --bot: #eef2f6; --user: #0b6b7a; --user-text: #ffffff; --accent: #0b6b7a; --danger: #b3261e;
  }
  @media (prefers-color-scheme: dark) {
    :root { --bg: #11161b; --panel: #1a2128; --text: #e6ebf0; --muted: #93a0ad; --line: #2a343d;
            --bot: #242d36; --user: #1f8a9b; --user-text: #ffffff; --accent: #4fb3c2; --danger: #f2b8b5; }
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--text); font: 15px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif;
         height: 100vh; display: flex; justify-content: center; }
  .app { width: 100%; max-width: 760px; display: flex; flex-direction: column; background: var(--panel);
         border-left: 1px solid var(--line); border-right: 1px solid var(--line); }
  header { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 18px;
           border-bottom: 1px solid var(--line); }
  header h1 { font-size: 16px; margin: 0; }
  header small { color: var(--muted); display: block; font-weight: normal; }
  button { font: inherit; cursor: pointer; border-radius: 8px; border: 1px solid var(--line); background: var(--panel);
           color: var(--text); padding: 7px 12px; }
  button:hover { border-color: var(--accent); }
  button.primary { background: var(--accent); border-color: var(--accent); color: var(--user-text); }
  button:disabled { opacity: .5; cursor: default; }
  #log { flex: 1; overflow-y: auto; padding: 18px; display: flex; flex-direction: column; gap: 10px; }
  .msg { max-width: 82%; padding: 10px 14px; border-radius: 14px; white-space: normal; overflow-wrap: anywhere; }
  .bot { background: var(--bot); align-self: flex-start; border-bottom-left-radius: 4px; }
  .user { background: var(--user); color: var(--user-text); align-self: flex-end; border-bottom-right-radius: 4px; }
  .err { background: transparent; border: 1px solid var(--danger); color: var(--danger); align-self: center; font-size: 13px; }
  .note { align-self: center; color: var(--muted); font-size: 12px; }
  .dots span { display: inline-block; width: 6px; height: 6px; margin: 0 2px; border-radius: 50%; background: var(--muted);
               animation: blink 1.2s infinite; }
  .dots span:nth-child(2) { animation-delay: .2s; } .dots span:nth-child(3) { animation-delay: .4s; }
  @keyframes blink { 0%, 80%, 100% { opacity: .2; } 40% { opacity: 1; } }
  footer { border-top: 1px solid var(--line); padding: 12px 18px; display: flex; flex-direction: column; gap: 8px; }
  #chips { display: flex; flex-wrap: wrap; gap: 6px; }
  .chip { font-size: 12px; background: var(--bot); border-radius: 999px; padding: 3px 10px; display: flex; gap: 6px; align-items: center; }
  .chip button { border: 0; padding: 0 2px; background: none; color: var(--muted); }
  .row { display: flex; gap: 8px; }
  #attachRow { display: none; }
  input[type=text], input[type=url] { flex: 1; font: inherit; padding: 9px 12px; border-radius: 8px; border: 1px solid var(--line);
                                      background: var(--bg); color: var(--text); }
  input:focus { outline: 2px solid var(--accent); outline-offset: -1px; }
</style>
</head>
<body>
<div class="app">
  <header>
    <h1>Marina <small>OneSpaWorld product returns (local test)</small></h1>
    <button id="newBtn" title="Start a new conversation">New conversation</button>
  </header>
  <div id="log" aria-live="polite"></div>
  <footer>
    <div id="chips"></div>
    <div class="row" id="attachRow">
      <input type="url" id="fileUrl" placeholder="https://… link to the file">
      <button id="addBtn">Add</button>
    </div>
    <div class="row">
      <button id="attachBtn" title="Attach a file link">📎</button>
      <input type="text" id="box" placeholder="Type a message" autocomplete="off" autofocus>
      <button class="primary" id="sendBtn">Send</button>
    </div>
  </footer>
</div>
<script>
  const log = document.getElementById("log"), box = document.getElementById("box"), sendBtn = document.getElementById("sendBtn");
  const chips = document.getElementById("chips"), attachRow = document.getElementById("attachRow"), fileUrl = document.getElementById("fileUrl");
  let previous = null, session = null, files = [], busy = false;

  function escapeHtml(s) { return s.replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c])); }
  // The bot writes *bold* and plain line breaks; everything else is shown as typed.
  function render(text) { return escapeHtml(text).replace(/\*([^*\n]+)\*/g, "<strong>$1</strong>").replace(/\n/g, "<br>"); }

  function add(kind, text) {
    const div = document.createElement("div");
    div.className = "msg " + kind;
    if (kind === "user") div.textContent = text; else div.innerHTML = render(text);
    log.appendChild(div); log.scrollTop = log.scrollHeight;
    return div;
  }
  function note(text) { const d = document.createElement("div"); d.className = "note"; d.textContent = text; log.appendChild(d); }

  function drawChips() {
    chips.innerHTML = "";
    files.forEach((u, i) => {
      const c = document.createElement("span"); c.className = "chip";
      c.append("📎 " + (u.split("/").pop() || u).slice(0, 40));
      const x = document.createElement("button"); x.textContent = "×"; x.title = "Remove";
      x.onclick = () => { files.splice(i, 1); drawChips(); };
      c.appendChild(x); chips.appendChild(c);
    });
  }

  async function send() {
    const text = box.value.trim();
    if (busy || (!text && !files.length)) return;
    busy = true; sendBtn.disabled = true;
    add("user", text + (files.length ? "\n" + files.map(u => "📎 " + u).join("\n") : ""));
    const sentFiles = files; files = []; drawChips(); box.value = "";
    const typing = add("bot", ""); typing.innerHTML = '<span class="dots"><span></span><span></span><span></span></span>';
    try {
      const res = await fetch("/chat", {method: "POST", headers: {"Content-Type": "application/json"},
                                        body: JSON.stringify({text: text || "(file)", files: sentFiles, previous, session})});
      const data = await res.json();
      typing.remove();
      if (data.error) { add("err", data.error); }
      else { previous = data.id; session = data.session || session; add("bot", data.reply || "(no reply)"); }
    } catch (e) {
      typing.remove(); add("err", "Could not reach the chat page server: " + e.message);
    } finally { busy = false; sendBtn.disabled = false; box.focus(); }
  }

  function reset() {
    previous = session = null; files = []; drawChips(); log.innerHTML = "";
    note("New conversation. Say what you would like to return.");
  }

  document.getElementById("newBtn").onclick = reset;
  sendBtn.onclick = send;
  box.addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } });
  document.getElementById("attachBtn").onclick = () => { attachRow.style.display = attachRow.style.display === "flex" ? "none" : "flex"; fileUrl.focus(); };
  function addFile() {
    const u = fileUrl.value.trim();
    if (!/^https:\/\/\S+$/i.test(u)) { fileUrl.setCustomValidity("Use an https:// link"); fileUrl.reportValidity(); return; }
    fileUrl.setCustomValidity(""); files.push(u); fileUrl.value = ""; drawChips(); box.focus();
  }
  document.getElementById("addBtn").onclick = addFile;
  fileUrl.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); addFile(); } });
  reset();
</script>
</body>
</html>
"""


def ask_bot(body: dict) -> dict:
    """Forward one chat turn to the bot's Responses endpoint and flatten the answer for the page."""
    text, files = str(body.get("text") or ""), [u for u in body.get("files") or [] if isinstance(u, str)]
    content = [{"type": "input_text", "text": text}] + [{"type": "input_file", "file_url": u} for u in files]
    request = {"input": [{"role": "user", "content": content}] if files else text, "stream": False}
    if body.get("previous"):
        request["previous_response_id"] = body["previous"]
    if body.get("session"):
        request["agent_session_id"] = body["session"]        # the host scopes saved workflow state by session
    req = urllib.request.Request(BOT_URL, data=json.dumps(request).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as exc:
        return {"error": f"The bot answered with HTTP {exc.code}."}
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return {"error": f"The bot is not reachable at {BOT_URL}. Start it with: uv run --no-sync python main.py"}
    parts = [c.get("text", "") for item in data.get("output") or [] for c in item.get("content") or []
             if c.get("type") == "output_text"]
    err = (data.get("error") or {}).get("message")
    if err:
        return {"error": err}
    return {"reply": "\n".join(parts), "id": data.get("id"), "session": data.get("agent_session_id")}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path.split("?")[0] == "/":
            self._send(200, PAGE.encode(), "text/html; charset=utf-8")
        else:
            self._send(404, b"Not found", "text/plain")

    def do_POST(self) -> None:
        if self.path != "/chat":
            self._send(404, b"Not found", "text/plain")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(min(length, MAX_BODY)) or b"{}")
            if not isinstance(body, dict):
                raise ValueError
        except (ValueError, json.JSONDecodeError):
            self._send(400, json.dumps({"error": "Bad request."}).encode(), "application/json")
            return
        self._send(200, json.dumps(ask_bot(body)).encode(), "application/json")

    def log_message(self, fmt: str, *args) -> None:        # keep the terminal quiet (messages can hold customer details)
        pass


def main() -> None:
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError as exc:
        raise SystemExit(f"Cannot listen on port {PORT} ({exc.strerror}). Something else is using it, or an earlier "
                         f"ui.py is still running. Pick another port:  UI_PORT=8010 python3 ui.py")
    print(f"Marina chat page: http://localhost:{PORT}   (bot: {BOT_URL})   Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
