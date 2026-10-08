"""Detecting "I want to stop" in a customer's reply (Kore: the Cancel_Mid_Workflow exit rules).

Two tiers, as in Kore:
  * phrases that are always a cancel ("I don't want to continue", "cancel this request", ...)
  * single exit words ("cancel", "exit", "quit", "discard", "terminate") as whole words, unless the sentence is about
    something else ("cancel my subscription", "at the end of", "exit the ship")
"""

import re

EXIT_PHRASES = (
    "i do not want to continue this anymore", "i don't want to continue this anymore",
    "i dont want to continue this anymore", "i don't want to continue", "i dont want to continue",
    "i don't need this anymore", "i dont need this anymore", "stop the process",
    "end the conversation", "end this conversation", "end this request", "end this",
    "cancel this request", "cancel this", "stop this", "i want to cancel", "i want to exit",
    "i want to discard", "i want to stop",
)
EXIT_WORDS = ("discard", "cancel", "exit", "quit", "terminate")
NOT_A_CANCEL = (
    "cancel that", "cancel that thought", "cancel the", "cancel my", "cancel your", "cancel their", "cancel it",
    "cancel a ", "cancel my subscription", "cancelled", "cancellation", "canceling", "cancelling", "stop me if",
    "stop the", "stop my", "stop charging", "end of", "end the", "end my", "by the end", "toward the end",
    "at the end", "close to", "quite", "exiting", "exit the", "exit a ", "discarded", "discarding",
)

MSG_CANCELLED = "Okay, cancelling this request."


def is_cancel_request(text: str) -> bool:
    message = (text or "").lower().strip()
    if not message:
        return False
    if any(phrase in message for phrase in EXIT_PHRASES):
        return True
    if any(phrase in message for phrase in NOT_A_CANCEL):
        return False
    return any(re.search(rf"(^|[^a-zA-Z]){word}([^a-zA-Z]|$)", message) for word in EXIT_WORDS)
