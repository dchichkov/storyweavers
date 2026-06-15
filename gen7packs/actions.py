"""Core direct-call aliases for gen7.

This pack owns the broad kernel-name ontology: uppercase TinyStories kernel
calls lower to frame kinds here before Parser.direct_call applies shared role
and world-model logic.
"""

from gen7 import (
    EvalResult,
    Frame,
    LowerExpr,
    Memeplex,
    REGISTRY,
    display_type,
    flatten,
    is_character,
    objects_from,
)


ALIASES = {
    "find": "find", "discover": "discover", "discovery": "discover",
    "want": "want", "desire": "want", "longing": "want",
    "lost": "lost", "loss": "lost", "lose": "lost",
    "search": "search", "ask": "ask", "request": "ask",
    "help": "help", "assist": "help", "comfort": "comfort",
    "give": "give", "gift": "give", "receive": "receive", "obtain": "receive",
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
    "eat": "eat", "nap": "rest", "dream": "dream", "print": "print",
    "wipe": "wipe", "habit": "habit", "reject": "refuse",
    "skillacquired": "complete",
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
    "create": "make", "paint": "paint", "meal": "eat",
    "show": "show", "calendaradd": "calendar_add", "anticipation": "anticipation",
    "celebration": "celebration", "playinside": "play",
    "pinch": "injury", "threat": "threat",
    "alarm": "alarm", "screamtogether": "alarm", "scare": "scare",
    "blowaway": "blow_away", "unlock": "unlock", "makelaugh": "cheer",
    "cheer": "cheer", "reassure": "reassure",
}

for _name, _kind in ALIASES.items():
    REGISTRY.direct_alias(_name, kind=_kind)


@REGISTRY.direct_handler
def accident(parser, name, lname, values, kw_values, child_frames, context, role):
    if lname != "accident":
        return None
    if child_frames:
        return EvalResult(frames=child_frames, values=[Memeplex(name)])
    chars = [v for v in values if is_character(v)]
    actor = chars[0] if chars else parser.current_actor
    objects = objects_from([v for v in values if not is_character(v)], parser.world)
    object_names = {display_type(o) for o in objects}
    labels = {
        label.lower()
        for value in flatten(kw_values.values())
        if isinstance(value, Memeplex)
        for label in value.labels()
    }
    if chars and object_names & {"arm", "leg", "hand", "foot", "head"}:
        return EvalResult(
            frames=[Frame("injury", actor=actor, objects=objects, source=name)],
            values=[Memeplex(name)],
        )
    if objects and (labels & {"break", "broken"} or "scale" in object_names):
        return EvalResult(
            frames=[Frame("broken", actor=actor, objects=objects, source=name)],
            values=[Memeplex(name)],
        )
    jump = next((v for v in values if isinstance(v, LowerExpr) and v.name.lower() == "jump"), None)
    if jump is not None:
        trouble = objects_from(jump.args, parser.world)
        return EvalResult(
            frames=[Frame("problem", actor=actor, objects=trouble, concepts=[Memeplex("stuck")], source=name)],
            values=[Memeplex(name)],
        )
    if objects:
        return EvalResult(
            frames=[Frame("problem", actor=actor, objects=objects, concepts=[Memeplex(name)], source=name)],
            values=[Memeplex(name)],
        )
    return EvalResult(values=[Memeplex(name)])


@REGISTRY.direct_handler
def growth(parser, name, lname, values, kw_values, child_frames, context, role):
    if lname != "growth":
        return None
    chars = [v for v in values if is_character(v)]
    actor = chars[0] if chars else parser.current_actor
    if actor is not None and display_type(actor) == "seed":
        return EvalResult(
            frames=child_frames + [Frame("grow", actor=actor, source=name)],
            values=[Memeplex(name)],
        )
    return EvalResult(frames=child_frames, values=[Memeplex(name)])


@REGISTRY.direct_handler
def learning(parser, name, lname, values, kw_values, child_frames, context, role):
    if lname != "learning":
        return None
    chars = [v for v in values if is_character(v)]
    actor = chars[0] if chars else parser.current_actor
    labels = {
        label.lower()
        for value in values + flatten(kw_values.values())
        if isinstance(value, Memeplex)
        for label in value.labels()
    }
    if actor is not None and "grow" in labels:
        return EvalResult(
            frames=child_frames + [Frame(
                "lesson",
                actor=actor,
                concepts=[Memeplex("Grow")],
                source=name,
                meta={"actor_locked": True, "participants": [actor]},
            )],
            values=[Memeplex(name)],
        )
    return EvalResult(frames=child_frames, values=[Memeplex(name)])


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
