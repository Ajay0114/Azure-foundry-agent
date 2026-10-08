"""Tiny terminal chat client for the local Responses server (stdlib only).

Usage:  python3 chat.py            (server must be running on :8088)
Chains turns with previous_response_id, so the bot's saved dialog state follows the conversation.
Type /new to start a fresh conversation, /quit to exit.
"""

import json
import urllib.request

URL = "http://localhost:8088/responses"


def ask(text: str, previous: str | None, session: str | None) -> tuple[str, str, str | None, str | None]:
    body = {"input": text, "stream": False}
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
    print("Marina bot (local). /new = new conversation, /quit = exit\n")
    while True:
        try:
            text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text == "/quit":
            break
        if text == "/new":
            previous = session = None
            print("-- new conversation --")
            continue
        if not text:
            continue
        reply, rid, err, sid = ask(text, previous, session)
        if err:
            print(f"[error] {err}")
            continue
        previous, session = rid, sid or session
        print(f"bot> {reply}\n")


if __name__ == "__main__":
    main()
