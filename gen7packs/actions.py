"""Core direct-call aliases for gen7.

This pack owns the broad kernel-name ontology: uppercase TinyStories kernel
calls lower to frame kinds here before Parser.direct_call applies shared role
and world-model logic.
"""

from gen7 import REGISTRY


ALIASES = {
    "find": "find", "discover": "discover", "discovery": "discover",
    "want": "want", "desire": "want", "longing": "want",
    "lost": "lost", "loss": "lost", "lose": "lost",
    "search": "search", "ask": "ask", "request": "ask",
    "help": "help", "assist": "help", "comfort": "help",
    "give": "give", "gift": "give", "receive": "receive",
    "break": "break", "broken": "broken", "fix": "fix", "repair": "fix",
    "play": "play", "fear": "fear", "rescue": "rescue", "save": "rescue",
    "friendship": "friendship", "moral": "lesson", "lesson": "lesson",
    "refuse": "refuse", "refusal": "refuse", "apology": "apology",
    "forgiveness": "forgiveness", "return": "return", "transform": "transform",
    "problem": "problem", "reaction": "reaction", "emotion": "emotion",
    "encounter": "encounter", "meet": "encounter", "hug": "hug",
    "listen": "listen", "share": "share", "promise": "promise",
    "rest": "rest", "feed": "give", "warm": "warm", "capture": "capture",
    "catch": "capture", "take": "take", "shrink": "shrink", "grow": "grow",
    "dig": "dig", "plead": "ask", "smile": "emotion",
    "dialogue": "ask", "parting": "parting", "disturbance": "problem",
    "attemptsleep": "rest", "captureattempt": "capture",
    "kindness": "help", "magic": "annotation", "trade": "trade",
    "deal": "deal", "idea": "idea", "collaboration": "collaboration",
    "sharing": "share", "satisfaction": "satisfaction",
    "hunger": "hunger", "state": "state", "guide": "guide",
    "reunion": "reunion", "race": "race", "competition": "competition",
    "run": "run", "recall": "recall", "learn": "lesson",
    "completion": "complete", "bake": "bake", "party": "party",
    "dance": "dance", "sing": "sing", "ride": "ride",
    "surprise": "surprise", "reveal": "reveal", "walk": "walk",
    "open": "open", "attack": "attack", "protect": "protect",
    "bite": "bite", "hospital": "hospital", "avoidance": "avoidance",
    "memory": "memory", "scold": "scold", "make": "make",
    "wear": "wear", "accept": "accept", "resist": "resist",
    "compromise": "compromise", "insight": "lesson",
    "catalyst": "activity", "process": "activity",
    "cooperation": "collaboration", "caretaker": "caretaker",
    "outcome": "outcome", "requirement": "need", "advice": "advice",
    "try": "attempt", "perform": "perform", "approve": "approve",
    "reward": "reward", "pickup": "take", "enjoy": "emotion",
    "visit": "visit", "hide": "hide", "warning": "warning",
    "intervention": "intervention", "praise": "praise",
    "awareness": "state", "offer": "offer", "polishing": "work",
    "heal": "heal", "safe": "safe", "harmony": "harmony",
    "report": "report", "investigation": "search",
    "escape": "escape", "continuation": "play",
    "command": "command", "obedience": "perform", "message": "message",
    "affection": "hug", "sick": "problem",
    "hold": "hold", "drop": "drop", "permission": "permission",
    "pick": "take", "suggest": "advice", "remove": "remove",
    "teach": "teach", "transport": "transport", "drive": "drive",
    "clean": "clean", "chew": "chew",
}

for _name, _kind in ALIASES.items():
    REGISTRY.direct_alias(_name, kind=_kind)

