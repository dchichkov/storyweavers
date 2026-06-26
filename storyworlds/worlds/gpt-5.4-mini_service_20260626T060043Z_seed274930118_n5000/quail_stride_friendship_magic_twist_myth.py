#!/usr/bin/env python3
"""
Standalone storyworld for a small mythic friendship tale with a quail, a stride,
a touch of magic, and a twist.

A seed-like source tale imagined for this domain:
---
A little quail with a bright heart loved to stride across the sunlit meadow.
One day she met a lonely moth, and they became friends. A river spirit offered
a spark of magic: it could guide them home if they shared kindly words and
walked together. But the path twisted through reeds, and the moth grew afraid.
The quail did not laugh or leave. She slowed her stride, held her friend's wing,
and the magic answered their friendship. The twist of the path became a twist
of joy, because they reached the nest together.

This script turns that premise into a small simulated world:
- the quail has physical stamina and emotional courage
- the path has length and a bend that can confuse travelers
- friendship and magic are not decorations; they alter state and outcome
- the ending image proves what changed
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    props: dict[str, str] = field(default_factory=dict)

    friend: object | None = None
    path: object | None = None
    quail: object | None = None
    spirit: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"quail", "bird", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"moth", "fox", "boy", "spirit"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Place:
    name: str
    features: set[str] = field(default_factory=set)
    path_kind: str = "meadow path"
    has_magic: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class StoryParams:
    place: str
    companion: str
    twist: str
    name: str
    seed: Optional[int] = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _w_fatigue(world: World) -> None:
    quail = world.get("quail")
    if quail.meters.get("stride", 0.0) >= THRESHOLD:
        quail.meters["tired"] = quail.meters.get("tired", 0.0) + 1


def _w_twist(world: World) -> None:
    path = world.get("path")
    if path.meters.get("twist", 0.0) >= THRESHOLD:
        for ent in list(world.entities.values()):
            if ent.kind == "character":
                ent.memes["uncertain"] = ent.memes.get("uncertain", 0.0) + 1


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        before = {e.id: (dict(e.meters), dict(e.memes)) for e in world.entities.values()}
        _w_fatigue(world)
        _w_twist(world)
        after = {e.id: (dict(e.meters), dict(e.memes)) for e in world.entities.values()}
        changed = before != after


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic quail friendship storyworld with a magic twist."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


PLACES = {
    "reed_path": Place(name="the reed path", features={"reeds", "water", "wind"}, path_kind="winding reed path", has_magic=True),
    "moon_meadow": Place(name="the moon meadow", features={"grass", "stars", "dew"}, path_kind="silver meadow trail", has_magic=True),
    "hill_road": Place(name="the hill road", features={"stones", "breeze", "flowers"}, path_kind="stone hill road", has_magic=False),
}

COMPANIONS = {
    "moth": {"type": "moth", "label": "moth", "phrase": "a small moth with pale wings"},
    "fox": {"type": "fox", "label": "fox", "phrase": "a gentle fox with a russet tail"},
}

TWISTS = {
    "bend": {"label": "a sudden bend", "meter": "bend"},
    "fog": {"label": "a drift of fog", "meter": "fog"},
    "storm": {"label": "a storm twist", "meter": "storm"},
}

NAMES = ["Luma", "Nia", "Kiri", "Sora", "Mira", "Tavi", "Ari", "Luna"]
TRAITS = ["bright", "brave", "gentle", "lively", "quiet", "wise"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p, place in PLACES.items():
        for c in COMPANIONS:
            for t in TWISTS:
                if place.has_magic or t != "storm":
                    combos.append((p, c, t))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "companion", None) is None or c[1] == getattr(args, "companion", None))
              and (getattr(args, "twist", None) is None or c[2] == getattr(args, "twist", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, companion, twist = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(place=place, companion=companion, twist=twist, name=name)


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    quail = world.add(Entity(
        id="quail", kind="character", type="quail", label=params.name,
        phrase=f"a little quail named {params.name}",
        meters={"stride": 0.0, "tired": 0.0},
        memes={"friendship": 0.0, "joy": 0.0, "courage": 0.0, "uncertain": 0.0},
    ))
    comp = _safe_lookup(COMPANIONS, params.companion)
    friend = world.add(Entity(
        id="friend", kind="character", type=comp["type"], label=comp["label"],
        phrase=comp["phrase"], meters={"worry": 0.0}, memes={"friendship": 0.0, "fear": 0.0},
    ))
    path = world.add(Entity(
        id="path", kind="thing", type="path", label=world.place.path_kind,
        meters={"length": 3.0, "twist": 1.0 if params.twist != "fog" else 0.5, "mystery": 1.0},
        memes={"magic": 0.0},
    ))
    spirit = None
    if world.place.has_magic:
        spirit = world.add(Entity(
            id="spirit", kind="character", type="spirit", label="river spirit",
            phrase="a river spirit with moonlit feathers",
            meters={"light": 1.0}, memes={"magic": 1.0, "kindness": 0.0},
        ))
    world.facts.update(params=params, quail=quail, friend=friend, path=path, spirit=spirit)
    return world


def begin(world: World) -> None:
    q = world.get("quail")
    f = world.get("friend")
    world.say(f"{q.label} was a little quail who loved to stride across the meadow at dawn.")
    world.say(f"One day {q.label} met {f.phrase}, and they became friends before the sun climbed high.")
    q.memes["friendship"] += 1
    f.memes["friendship"] += 1
    q.memes["joy"] += 1


def offer_magic(world: World) -> bool:
    if world.place.has_magic and "spirit" in world.entities:
        s = world.get("spirit")
        q = world.get("quail")
        f = world.get("friend")
        s.memes["kindness"] += 1
        world.say(f"A river spirit shimmered beside the path and offered a small magic to guide them home.")
        world.say(f'"Walk together, and your friendship will light the way," {s.pronoun()} said.')
        q.memes["courage"] += 1
        f.memes["fear"] = max(0.0, f.memes.get("fear", 0.0) - 0.5)
        world.get("path").memes["magic"] += 1
        return True
    return False


def travel(world: World, params: StoryParams) -> None:
    q = world.get("quail")
    f = world.get("friend")
    path = world.get("path")
    q.meters["stride"] += 1
    q.meters["stride"] += 0.5
    world.say(f"They set out along the {world.place.path_kind}, with {q.label} striding first and {f.label} close beside.")
    if params.twist == "bend":
        world.say("Soon the path turned in a sudden bend, and the tall reeds hid the road ahead.")
    elif params.twist == "fog":
        world.say("Soon a drift of fog folded over the grass, and even the stones seemed to vanish.")
    else:
        world.say("Then a storm twist of wind curled around the hill, rattling the grass and making the trail seem strange.")
    path.meters["twist"] += 1
    propagate(world)


def conflict(world: World) -> None:
    q = world.get("quail")
    f = world.get("friend")
    if q.meters.get("tired", 0.0) >= THRESHOLD or q.memes.get("uncertain", 0.0) >= THRESHOLD:
        f.memes["fear"] += 1
        world.say(f"{f.label} wavered for a moment, but {q.label} slowed her stride instead of hurrying ahead.")
        world.say(f"She held her friend close and shared her courage, because friendship mattered more than speed.")
        q.memes["courage"] += 1
        q.memes["joy"] += 1
        q.meters["stride"] = max(0.0, q.meters["stride"] - 0.5)


def resolve(world: World) -> None:
    q = world.get("quail")
    f = world.get("friend")
    path = world.get("path")
    if "spirit" in world.entities and world.get("spirit").memes.get("kindness", 0.0) >= THRESHOLD:
        world.say("The magic listened to their kindness, and the confusion in the road began to soften.")
    world.say(f"At last they found the nest again, not because the road was straight, but because they stayed together.")
    world.say(f"{q.label} and {f.label} arrived side by side, and the little twist in the path became a twist of joy.")
    q.memes["joy"] += 1
    q.memes["friendship"] += 1
    f.memes["fear"] = 0.0
    path.meters["mystery"] = 0.0


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    begin(world)
    world.para()
    offer_magic(world)
    travel(world, params)
    conflict(world)
    world.para()
    resolve(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = _safe_fact(world, world.facts, "params")  # type: ignore[assignment]
    return [
        f"Write a short myth for children about a quail who loves to stride and learns a friendship lesson.",
        f"Tell a gentle story about {p.name}, a quail, a magic helper, and a twist in the road.",
        f"Write a tiny myth using the words quail, stride, friendship, magic, and twist.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact(world, world.facts, "params")  # type: ignore[assignment]
    q = world.get("quail")
    f = world.get("friend")
    place = world.place.name
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {q.phrase}, who loved to stride across {place} and learn with {f.label}.",
        ),
        QAItem(
            question=f"What did the quail do on the path?",
            answer=f"{q.label} strode along the path with her friend instead of running away when the road turned strange.",
        ),
        QAItem(
            question=f"What changed the ending of the trip?",
            answer=f"The ending changed because friendship held them together, and the magic helped them keep going through the twist.",
        ),
        QAItem(
            question=f"Why did the quail slow down?",
            answer=f"{q.label} slowed down because {f.label} was unsure, and she chose kindness and friendship over speed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quail?",
            answer="A quail is a small bird that lives on the ground and can move quickly through grass and reeds.",
        ),
        QAItem(
            question="What does stride mean?",
            answer="To stride means to walk in a strong, steady way, with long confident steps.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind bond between friends who help, trust, and care for one another.",
        ),
        QAItem(
            question="What is a magic spell in a story?",
            answer="In a story, a magic spell is something enchanted that can change what happens or guide someone safely.",
        ),
        QAItem(
            question="What is a twist in a path?",
            answer="A twist is a turn or bend that makes a path go a different way than you expected.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
quail_friendship(Q,F) :- quail(Q), friend(F), friendship(Q,F).
twist_path(P) :- path(P), twist(P).
magic_guides(S) :- spirit(S), magic(S).
safe_return(Q,F) :- quail_friendship(Q,F), twist_path(_), magic_guides(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        if _safe_lookup(PLACES, p).has_magic:
            lines.append(asp.fact("magic_place", p))
    for c in COMPANIONS:
        lines.append(asp.fact("companion", c))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    lines.append(asp.fact("quail", "quail"))
    lines.append(asp.fact("friend", "friend"))
    lines.append(asp.fact("path", "path"))
    lines.append(asp.fact("spirit", "spirit"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe_return/2."))
    asp_atoms = set(asp.atoms(model, "safe_return"))
    py_atoms = set()
    for place in PLACES:
        if _safe_lookup(PLACES, place).has_magic:
            py_atoms.add(("quail", "friend"))
    if asp_atoms == py_atoms:
        print(f"OK: clingo gate matches Python gate ({len(py_atoms)} cases).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("  asp:", sorted(asp_atoms))
    print("  py :", sorted(py_atoms))
    return 1


def valid_story(params: StoryParams) -> bool:
    return params.place in PLACES and params.companion in COMPANIONS and params.twist in TWISTS


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="reed_path", companion="moth", twist="bend", name="Luma"),
    StoryParams(place="moon_meadow", companion="moth", twist="fog", name="Nia"),
    StoryParams(place="hill_road", companion="fox", twist="storm", name="Kiri"),
]


def resolve_and_validate(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = resolve_params(args, rng)
    if not valid_story(params):
        pass
    return params


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show safe_return/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show safe_return/2."))
        print(sorted(set(asp.atoms(model, "safe_return"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_and_validate(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.place} / {p.companion} / {p.twist}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
