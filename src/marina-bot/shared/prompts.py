"""Loads prompt templates stored as .md files next to each dialog.

Templates use {{name}} placeholders. We substitute with plain string replacement rather than
str.format because the prompts contain literal JSON braces.
"""

from pathlib import Path


def render(template: str, **variables: str) -> str:
    for key, value in variables.items():
        template = template.replace("{{" + key + "}}", value if value is not None else "")
    return template


def load_prompt(prompts_dir: Path, name: str, **variables: str) -> str:
    template = (prompts_dir / f"{name}.md").read_text(encoding="utf-8")
    return render(template, **variables)
