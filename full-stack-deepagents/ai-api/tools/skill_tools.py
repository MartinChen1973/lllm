"""
Optional tools that back imported Agent Skills when the filesystem layout is present.

Deep Agents load SKILL.md metadata via `create_deep_agent(skills=[...])`; some third-party
skills assume CLI helpers. We expose minimal Python tools for those hooks where the default
StateBackend does not offer `execute`.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Any

## ⬇️ Parallels SKILLS_DIR in main.py (sibling of `tools/`)
_SKILLS_ROOT = Path(__file__).resolve().parent.parent / "skills"
_ACTION_FINDER_LOG = _SKILLS_ROOT / "action-finder" / "scripts" / "log.py"
_ACTION_FINDER_TEMPLATES = frozenset({"CIDED", "CIDRA", "CID"})
## ⬇️ Generic “CRUD verbs” that are NOT the CIDED/CID slot names (Index=list, Details=get, Edit=edit)
_BAD_ACTION_VERBS = re.compile(r"^(read|update|fetch|patch)([A-Z]|$)")


def _camel_verb_prefix(name: str, verb: str) -> bool:
    ## ⬇️ True if camelCase action starts with verb + uppercase continuation (e.g. listUsers)
    if not name.startswith(verb):
        return False
    if len(name) == len(verb):
        return True
    return name[len(verb)].isupper()


def _validate_cided_actions(actions: list[str]) -> str | None:
    ## ⬇️ CIDED must map five slots; forbid read*/update*/fetch*/patch* as stand-ins for list/get/edit
    if len(actions) < 5:
        return (
            "action_finder_log: CIDED requires at least five actions (Create, Index, Details, Edit, Delete) "
            f"before any inferred extras; got {len(actions)}. Add list*, get*, edit* — do not use read* or update*."
        )
    for a in actions:
        if _BAD_ACTION_VERBS.match(a):
            return (
                "action_finder_log: CIDED forbids generic verbs read/update/fetch/patch "
                f"({a!r}). Use list* for Index, get* for Details, edit* for Edit — see action-finder SKILL.md."
            )
    required = ("create", "list", "get", "edit", "delete")
    for verb in required:
        if not any(_camel_verb_prefix(x, verb) for x in actions):
            return (
                "action_finder_log: CIDED actions must include one camelCase name per slot: "
                f"create*, list*, get*, edit*, delete*. Missing verb prefix {verb!r}."
            )
    return None


def action_finder_log(entity_name: str, template_selected: str, actions: list[str]) -> str:
    ## ⬇️ Writes to skills/action-finder/scripts/history.yaml via bundled log.py
    """Log one action-finder run (entity, template code, camelCase action names) to history.yaml.

    template_selected MUST be exactly one of: CIDED, CIDRA, CID (see skill references).
    Do NOT use the word CRUD as the template code. Pass the same camelCase names you show
    the user—not template labels like Create or Index.
    """
    if not _ACTION_FINDER_LOG.is_file():
        return "action_finder_log: bundled log.py not found (skill not installed under ai-api/skills/)."
    t = (template_selected or "").strip().upper()
    if t not in _ACTION_FINDER_TEMPLATES:
        return (
            "action_finder_log: template_selected must be exactly CIDED, CIDRA, or CID "
            f"(not {template_selected!r}). Tell the user which template you used before logging."
        )
    if not actions:
        return "action_finder_log: pass at least one generated action name."
    if t == "CIDED":
        bad = _validate_cided_actions(actions)
        if bad:
            return bad
    try:
        proc = subprocess.run(
            [sys.executable, str(_ACTION_FINDER_LOG), entity_name, t, *actions],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as e:
        return f"action_finder_log: failed to run log.py: {e}"
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    if proc.returncode != 0:
        msg = err or out or f"exit {proc.returncode}"
        return f"action_finder_log: {msg}"
    return out or "action_finder_log: OK."


def get_skill_tools() -> list[Any]:
    ## ⬇️ Register only when the action-finder skill layout exists on disk
    if _ACTION_FINDER_LOG.is_file():
        return [action_finder_log]
    return []
