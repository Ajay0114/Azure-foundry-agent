"""Small helper for building Zendesk HTML."""

import html
from typing import Any


def esc(value: Any) -> str:
    """HTML-escape anything the customer typed (or the API said) before it goes into a ticket."""
    return html.escape(str(value), quote=False)
