#!/usr/bin/env python3
"""
storyworlds/worlds/junior_wolverine_foreshadowing_curiosity_conflict_ghost_story.py
===================================================================================

A small ghost-story world with a junior wolverine, a whispering place, and a
single curiosity-led conflict that resolves by uncovering a harmless truth.

The world is built to support:
- Foreshadowing: odd signs hint that something is wrong.
- Curiosity: the junior wolverine wants to inspect the signs.
- Conflict: fear rises when the signs seem spooky.
- Resolution: the mystery turns out to be small, physical, and explainable.

The prose is child-facing and concrete, with a gentle ghost-story mood.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    sig: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"wolverine"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    mood: str
    hidden: str
    clues: list[str] = field(default_factory=list)
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
class Sign:
    label: str
    type: str
    meter: str
    clue: str
    hint: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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
    sign: str
    name: str = "Junior"
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
        self.facts: dict = {}

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
        import copy
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


RULES_ORDER = ("foreshadow", "curiosity", "conflict", "reveal")


def _fired(world: World, key: tuple) -> bool:
    if key in world.fired:
        return True
    world.fired.add(key)
    return False


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for step in globals().get("RULES_ORDER", sorted(globals().get("RULES", []))):
            if step == "foreshadow":
                s = _r_foreshadow(world)
            elif step == "curiosity":
                s = _r_curiosity(world)
            elif step == "conflict":
                s = _r_conflict(world)
            else:
                s = _r_reveal(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_foreshadow(world: World) -> list[str]:
    hero = world.get("junior")
    sign = world.get("sign")
    if hero.memes.get("noticed", 0) < THRESHOLD:
        return []
    if _fired(world, ("foreshadow",)):
        return []
    return [
        f"At {world.place.name}, a small sign kept showing up: {sign.clue}.",
        f"It felt like the place was trying to whisper a warning.",
    ]


def _r_curiosity(world: World) -> list[str]:
    hero = world.get("junior")
    if hero.memes.get("noticed", 0) < THRESHOLD:
        return []
    if hero.memes.get("curiosity", 0) < THRESHOLD:
        return []
    if _fired(world, ("curiosity",)):
        return []
    hero.memes["curiosity"] += 1
    return [f"{hero.id} leaned closer, because he wanted to know what was making the strange sign."]


def _r_conflict(world: World) -> list[str]:
    hero = world.get("junior")
    sign = world.get("sign")
    if hero.memes.get("curiosity", 0) < THRESHOLD:
        return []
    if _fired(world, ("conflict",)):
        return []
    hero.memes["conflict"] += 1
    world.facts["clue"] = sign.clue
    return [
        f"Then the little wolverine heard a creak and froze.",
        f"The quiet sounded spooky, and his heart thumped fast.",
    ]


def _r_reveal(world: World) -> list[str]:
    hero = world.get("junior")
    if hero.memes.get("conflict", 0) < THRESHOLD:
        return []
    if _fired(world, ("reveal",)):
        return []
    hero.memes["conflict"] = 0
    hero.memes["relief"] = 1
    return [
        f"But the mystery was only {world.place.hidden}.",
        f"Nothing ghostly was hiding there at all.",
    ]


PLACES = {
    "attic": Place(
        name="the attic",
        mood="dusty",
        hidden="a loose window that tapped in the wind",
        clues=["a thin tapping sound", "a pale shape on the wall", "dust spinning in a beam of light"],
    ),
    "hall": Place(
        name="the old hall",
        mood="echoing",
        hidden="a swinging coat on a hook",
        clues=["a long shadow near the door", "a coat that moved when the air shifted", "a floorboard that groaned"],
    ),
    "garden": Place(
        name="the moonlit garden",
        mood="quiet",
        hidden="a branch brushing a fence",
        clues=["a shape between the hedges", "a soft rustle in the leaves", "a white blur under the moon"],
    ),
}

SIGNS = {
    "tapping": Sign(
        label="tapping sound",
        type="sound",
        meter="sound",
        clue="a thin tapping sound on the glass",
        hint="a wind-made tap",
    ),
    "shadow": Sign(
        label="shadow",
        type="shape",
        meter="shape",
        clue="a pale shape that slid across the wall",
        hint="a moving shadow from a swaying coat or branch",
    ),
    "rustle": Sign(
        label="rustle",
        type="sound",
        meter="sound",
        clue="a soft rustle in the dark leaves",
        hint="a branch brushing nearby",
    ),
}


def valid_combos() -> list[tuple[str, str]]:
    return [
        ("attic", "tapping"),
        ("hall", "shadow"),
        ("garden", "rustle"),
    ]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("mood", pid, place.mood))
        lines.append(asp.fact("hidden", pid, place.hidden))
    for sid, sign in SIGNS.items():
        lines.append(asp.fact("sign", sid))
        lines.append(asp.fact("kind", sid, sign.type))
    for p, s in valid_combos():
        lines.append(asp.fact("compatible", p, s))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(P,S) :- place(P), sign(S), base_compatible(P,S).
#show compatible/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\nbase_compatible(P,S) :- compatible(P,S).\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with foreshadowing, curiosity, and conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--name", default="Junior")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None) and getattr(args, "sign", None) and (getattr(args, "place", None), getattr(args, "sign", None)) not in combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    opts = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "sign", None) is None or c[1] == getattr(args, "sign", None))]
    if not opts:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, sign = rng.choice(sorted(opts))
    return StoryParams(place=place, sign=sign, name=getattr(args, "name", None))


def tell(place: Place, sign: Sign, name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id="junior", kind="character", type="wolverine", label=name))
    sig = world.add(Entity(id="sign", kind="thing", type=sign.type, label=sign.label, phrase=sign.clue))
    hero.memes["noticed"] = 1
    hero.memes["curiosity"] = 1

    world.say(f"Junior was a little wolverine who liked to explore quiet places after dusk.")
    world.say(f"At {place.name}, {sign.clue} kept appearing, and it made the air feel strange.")
    world.para()
    propagate(world)
    world.para()
    world.say(f"Junior took a careful breath and looked again.")
    world.say(f"He found that the scary sign had an ordinary cause: {place.hidden}.")
    world.say(f"He laughed softly, because the place was only playing tricks with sound and shadow.")
    world.facts.update(hero=hero, sign=sig, place=place, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short ghost-story for a child about a junior wolverine who notices a spooky sign and then solves it.',
        f"Tell a gentle mystery where Junior visits {f['place'].name} and hears {f['sign'].clue}.",
        "Write a story with foreshadowing, curiosity, conflict, and a calm reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    place = _safe_fact(world, f, "place")
    sign = _safe_fact(world, f, "sign")
    return [
        QAItem(
            question="Who is the story about?",
            answer="It is about Junior, a little wolverine who walks into a quiet place and looks for the source of a spooky clue.",
        ),
        QAItem(
            question=f"What strange thing did Junior notice at {place.name}?",
            answer=f"Junior noticed {sign.clue}, which made the place feel eerie before he understood it.",
        ),
        QAItem(
            question="How did the scary feeling change at the end?",
            answer=f"The scary feeling went away when Junior learned that the mystery was only {place.hidden}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story leaves small hints that something important or surprising may happen later.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to look, listen, and learn more about something that seems interesting or strange.",
        ),
        QAItem(
            question="What does a ghost story do for a child reader?",
            answer="A ghost story gives a little shiver of suspense, but it can still end safely when the mystery is explained.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for (n, *_) in world.fired})}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(SIGNS, params.sign), params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="attic", sign="tapping", name="Junior"),
    StoryParams(place="hall", sign="shadow", name="Junior"),
    StoryParams(place="garden", sign="rustle", name="Junior"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, sign) combos:\n")
        for p, s in combos:
            print(f"  {p:8} {s}")
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
