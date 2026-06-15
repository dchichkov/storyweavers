"""Core direct-call aliases for gen7.

This pack owns the broad kernel-name ontology: uppercase TinyStories kernel
calls lower to frame kinds here before Parser.direct_call applies shared role
and world-model logic.
"""

from gen7 import EvalResult, Frame, LowerExpr, Memeplex, REGISTRY, flatten, is_character, objects_from


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
    "pick": "take", "suggest": "advice", "remove": "remove", "pull": "rescue",
    "teach": "teach", "transport": "transport", "drive": "drive",
    "clean": "clean", "cut": "cut", "chew": "chew", "build": "make", "use": "use",
    "show": "show", "calendaradd": "calendar_add", "anticipation": "anticipation",
    "celebration": "celebration", "playinside": "play",
}

for _name, _kind in ALIASES.items():
    REGISTRY.direct_alias(_name, kind=_kind)


@REGISTRY.direct_handler
def calendar_add(parser, name, lname, values, kw_values, child_frames, context, role):
    if lname != "calendaradd":
        return None
    agents = [v for v in flatten(kw_values.get("agents", [])) if is_character(v)]
    actor = agents[0] if agents else parser.current_actor
    event_objects = objects_from(flatten(kw_values.get("event", [])), parser.world)
    calendar = parser.world.physical("calendar")
    objects = [calendar] + event_objects
    if actor is not None:
        parser.current_actor = actor
    frame = Frame(
        "calendar_add",
        actor=actor,
        patient=agents[1] if len(agents) > 1 else None,
        objects=objects,
        source=name,
        meta={"participants": agents},
    )
    return EvalResult(frames=child_frames + [frame], values=[Memeplex(name)])


@REGISTRY.direct_handler
def incident(parser, name, lname, values, kw_values, child_frames, context, role):
    if lname != "incident":
        return None
    chars = [v for v in values if is_character(v)]
    actor = chars[0] if chars else parser.current_actor
    frames = list(child_frames)
    for value in values + flatten(kw_values.values()):
        if isinstance(value, LowerExpr) and value.name.lower() == "chew":
            frames.append(Frame(
                "chew",
                actor=actor,
                objects=objects_from(value.args, parser.world),
                source=name,
                meta={"participants": chars},
            ))
    if actor is not None:
        parser.current_actor = actor
    if frames:
        return EvalResult(frames=frames, values=[Memeplex(name)])
    return None
