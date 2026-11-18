"""Prompt text shared with run.py (copied verbatim)."""
import pathlib

HERE = pathlib.Path(__file__).parent
NAMES = [l.strip() for l in (HERE / "names.txt").read_text().splitlines() if l.strip()]
PROMPTS = {
    "P1": "Create a puzzle spy game. Choose any setting you want. Reply with only the setting's name on line 1, then one sentence.",
    "P2": "Write the premise of a classic murder mystery. Reply with only the detective's full name on line 1, then one sentence.",
    "P3": "Invent a space station for a sci-fi story. Reply with only its name on line 1, then one sentence.",
    "P4": "Name a new AI note-taking startup. Reply with only the name on line 1, then one sentence.",
    "C": "Pick one name at random from this list and reply with only that name: " + ", ".join(NAMES),
}
