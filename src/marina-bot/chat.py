"""Tiny terminal chat client for the local Responses server (stdlib only).

Usage:  python3 chat.py            (server must be running on :8088)
Chains turns with previous_response_id, so the bot's saved dialog state follows the conversation.
Type /new to start a fresh conversation, /quit to exit.
Type /attach <https-url> to send a file link with your next message (the attachment service downloads it).
"""

import json
import urllib.request

URL = "http://localhost:8088/responses"


def ask(text: str, previous: str | None, session: str | None,
        files: list[str] | None = None) -> tuple[str, str, str | None, str | None]:
    content = [{"type": "input_text", "text": text}] + [{"type": "input_file", "file_url": u} for u in files or []]
    body = {"input": [{"role": "user", "content": content}] if files else text, "stream": False}
    if previous:
        body["previous_response_id"] = previous
    if session:
        # The host scopes saved workflow state by session; locally we must echo the id it gave us.
        body["agent_session_id"] = session
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.load(resp)
    parts = [c.get("text", "") for item in data.get("output", []) or [] for c in item.get("content", []) or []
             if c.get("type") == "output_text"]
    err = (data.get("error") or {}).get("message")
    return "\n".join(parts), data.get("id"), err, data.get("agent_session_id")


def main() -> None:
    previous = session = None
    files: list[str] = []
    print("Marina bot (local). /new = new conversation, /attach <url> = attach a file, /quit = exit\n")
    while True:
        try:
            text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text == "/quit":
            break
        if text.startswith("/attach "):
            files.append(text.split(None, 1)[1].strip())
            print(f"-- {len(files)} file(s) will be sent with your next message --")
            continue
        if text == "/new":
            previous = session = None
            files = []
            print("-- new conversation --")
            continue
        if not text and not files:
            continue
        reply, rid, err, sid = ask(text or "(file)", previous, session, files)
        files = []
        if err:
            print(f"[error] {err}")
            continue
        previous, session = rid, sid or session
        print(f"bot> {reply}\n")


if __name__ == "__main__":
    main()
