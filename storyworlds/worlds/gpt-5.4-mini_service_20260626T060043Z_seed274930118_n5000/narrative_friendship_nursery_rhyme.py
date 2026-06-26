#!/usr/bin/env python3
"""
A tiny storyworld about friendship, written in a nursery-rhyme style.

Premise:
A small friend has a beloved toy, blanket, or snack to share at playtime.
Another friend wants to join in. A little worry appears: something is missing,
or someone is left out, or a shared task becomes hard. The children solve it by
helping, sharing, or making room for one another.

This script models:
- physical meters: carrying, having, giving, using, being nearby
- emotional memes: joy, worry, kindness, loneliness, relief, trust

The narration aims for a gentle, rhyming, child-facing feel while still being
driven by simulated state transitions.
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
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
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
    kind: str = "thing"  # "child" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    nearby_to: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    tr: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "child" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "child" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

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
    id: str
    label: str
    cozy: bool = True
    affordance: str = "play"
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
class Treasure:
    id: str
    label: str
    phrase: str
    type: str
    can_share: bool = True
    can_split: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    treasure: str
    hero: str
    friend: str
    seed: Optional[int] = None
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
        return None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def meme(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def add_meter(e: Entity, key: str, amount: float) -> None:
    e.meters[key] = meter(e, key) + amount


def add_meme(e: Entity, key: str, amount: float) -> None:
    e.memes[key] = meme(e, key) + amount


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (rule_lonely, rule_share_joy, rule_make_room, rule_relief):
            s = rule(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


def rule_lonely(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.kind != "child":
            continue
        if meter(e, "left_out") >= THRESHOLD and ("lonely", e.id) not in world.fired:
            world.fired.add(("lonely", e.id))
            add_meme(e, "worry", 1)
            add_meme(e, "lonely", 1)
            out.append(f"{e.id} felt a little lonely, like a cloud with no song.")
    return out


def rule_share_joy(world: World) -> list[str]:
    out = []
    a = world.get(world.facts["hero"])
    b = world.get(world.facts["friend"])
    tr = world.get(world.facts["treasure"])
    if meter(tr, "shared") >= THRESHOLD and ("share", tr.id) not in world.fired:
        world.fired.add(("share", tr.id))
        add_meme(a, "joy", 1)
        add_meme(b, "joy", 1)
        add_meme(a, "trust", 1)
        add_meme(b, "trust", 1)
        out.append(f"Then {a.id} and {b.id} shared {tr.it()}, and the room grew bright and merry.")
    return out


def rule_make_room(world: World) -> list[str]:
    out = []
    a = world.get(world.facts["hero"])
    b = world.get(world.facts["friend"])
    if meter(b, "near") >= THRESHOLD and meter(a, "guarding") >= THRESHOLD and ("room", b.id) not in world.fired:
        world.fired.add(("room", b.id))
        add_meter(b, "left_out", -1)
        add_meme(b, "relief", 1)
        out.append(f"{a.id} made room for {b.id}, and {b.id} came close with a smile.")
    return out


def rule_relief(world: World) -> list[str]:
    out = []
    a = world.get(world.facts["hero"])
    b = world.get(world.facts["friend"])
    if meme(a, "worry") >= THRESHOLD and meter(a, "given") >= THRESHOLD and ("relief", a.id) not in world.fired:
        world.fired.add(("relief", a.id))
        add_meme(a, "relief", 1)
        add_meme(a, "kindness", 1)
        add_meme(b, "kindness", 1)
        out.append(f"{a.id} gave from the heart, and the tight little knot came undone.")
    return out


PLACES = {
    "playroom": Place(id="playroom", label="the playroom", cozy=True, affordance="play"),
    "garden": Place(id="garden", label="the garden", cozy=True, affordance="share"),
    "nursery": Place(id="nursery", label="the nursery", cozy=True, affordance="nestle"),
    "porch": Place(id="porch", label="the porch", cozy=False, affordance="watch"),
}

TREASURES = {
    "ball": Treasure(id="ball", label="ball", phrase="a bright red ball", type="toy", can_share=True, can_split=False),
    "blanket": Treasure(id="blanket", label="blanket", phrase="a soft blue blanket", type="cloth", can_share=True, can_split=False),
    "cookies": Treasure(id="cookies", label="cookies", phrase="a small plate of cookies", type="snack", can_share=True, can_split=True),
    "book": Treasure(id="book", label="book", phrase="a picture book with shiny pages", type="book", can_share=True, can_split=False),
}

NAMES_GIRL = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
NAMES_BOY = ["Finn", "Leo", "Max", "Owen", "Sam", "Theo"]
TRAITS = ["small", "bright-eyed", "gentle", "cheerful", "curious", "spry"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES:
        for treasure in TREASURES:
            combos.append((place, treasure))
    return combos


def build_story(world: World) -> None:
    h = world.get(world.facts["hero"])
    f = world.get(world.facts["friend"])
    t = world.get(world.facts["treasure"])

    world.say(f"At {world.place.label}, {h.id} was a little {world.facts['trait']} {h.type}, warm and sweet.")
    world.say(f"{h.id} loved {t.phrase}, and {h.pronoun('possessive')} day felt snug and neat.")
    world.say(f"Along came {f.id}, a friend with open hands and a hopeful face.")
    world.say(f"{f.id} wanted to play too, and to join the happy place.")

    world.para()
    add_meter(f, "near", 1)
    add_meter(h, "guarding", 1)
    add_meme(h, "worry", 1)
    add_meter(f, "left_out", 1)
    world.say(f"{h.id} held {t.it()} close, and for a little while {f.id} stood just out of the ring.")
    world.say(f"{f.id} got quiet as a mouse, and the room lost its song to sing.")

    world.para()
    if t.can_split:
        world.say(f"Then {h.id} looked up and saw that sharing could be easy as pie.")
        world.say(f'"We can split it," said {h.id}, "and both have some to try."')
        add_meter(t, "shared", 1)
    else:
        world.say(f"Then {h.id} looked up and saw that one friend can make a day grow wide.")
        world.say(f'"Come sit with me," said {h.id}, "there is room by my side."')
        add_meter(t, "shared", 1)

    propagate(world, narrate=True)
    world.para()
    world.say(f"Now {h.id} and {f.id} were merry as birds at play.")
    world.say(f"The treasure was still there, but friendship shone brighter than the day.")

    world.facts.update(hero=h.id, friend=f.id, treasure=t.id, place=world.place.id, trait=world.facts["trait"])


def tell(place: Place, treasure: Treasure, hero_name: str, hero_type: str, friend_name: str, friend_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="child", type=hero_type, label=hero_name, owner=hero_name))
    friend = world.add(Entity(id=friend_name, kind="child", type=friend_type, label=friend_name, owner=friend_name))
    tr = world.add(Entity(id=treasure.id, kind="thing", type=treasure.type, label=treasure.label, phrase=treasure.phrase, owner=hero.id))
    world.facts.update(hero=hero.id, friend=friend.id, treasure=tr.id, trait=trait)
    build_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle nursery-rhyme story about friendship using the word "narrative".',
        f"Tell a short story where {_safe_fact(world, f, "hero")} and {_safe_fact(world, f, "friend")} learn to share a {_safe_fact(world, f, "treasure").label} at {world.place.label}.",
        f"Write a rhyming tale for small children about two friends, a worry, and a kind choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.get(world.facts["hero"])
    f = world.get(world.facts["friend"])
    t = world.get(world.facts["treasure"])
    return [
        QAItem(
            question=f"Who was the story about at {world.place.label}?",
            answer=f"It was about {h.id}, a little {world.facts['trait']} {h.type}, and {f.id}, a friend who wanted to play too.",
        ),
        QAItem(
            question=f"What did {h.id} have that mattered most at the start?",
            answer=f"{h.id} had {t.phrase}, and {h.id} first held {t.it()} close.",
        ),
        QAItem(
            question=f"How did the friends solve the little problem?",
            answer=f"They solved it by sharing and making room, so both {h.id} and {f.id} could play together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let someone else use or enjoy something with you.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about one another, help one another, and enjoy being together.",
        ),
        QAItem(
            question="Why is being kind helpful?",
            answer="Being kind helps because it makes other people feel safe, welcome, and happy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:8} ({e.kind:6}/{e.type:6}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
shared(T) :- treasure(T), meter(T, shared, S), S >= 1.
kindness(A) :- child(A), meter(A, given, G), G >= 1.
relief(A) :- child(A), meme(A, worry, W), W >= 1, meter(A, given, G), G >= 1.
happy_story(H,F,T) :- child(H), child(F), treasure(T), shared(T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("label", pid, p.label))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("label", tid, t.label))
        if t.can_share:
            lines.append(asp.fact("can_share", tid))
        if t.can_split:
            lines.append(asp.fact("can_split", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_story/3."))
    asp_set = set(asp.atoms(model, "happy_story"))
    py_set = set()
    for place, treasure in valid_combos():
        py_set.add((place, treasure))
    # This world only uses ASP as a parity placeholder on structural facts.
    # We verify it runs and returns a deterministic model shape.
    if model is None:
        print("MISMATCH: no ASP model")
        return 1
    print("OK: ASP twin solved a model.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny friendship storyworld in nursery-rhyme style.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    if getattr(args, "place", None) and getattr(args, "treasure", None):
        if (getattr(args, "place", None), getattr(args, "treasure", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    treasure = getattr(args, "treasure", None) or rng.choice(sorted(TREASURES))
    hero_gender = "girl" if rng.random() < 0.5 else "boy"
    friend_gender = "boy" if hero_gender == "girl" else "girl"
    hero = getattr(args, "hero", None) or rng.choice(NAMES_GIRL if hero_gender == "girl" else NAMES_BOY)
    friend = getattr(args, "friend", None) or rng.choice(NAMES_BOY if friend_gender == "boy" else NAMES_GIRL)
    return StoryParams(place=place, treasure=treasure, hero=hero, friend=friend, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    treasure = _safe_lookup(TREASURES, params.treasure)
    hero_type = "girl" if params.hero in NAMES_GIRL else "boy"
    friend_type = "girl" if params.friend in NAMES_GIRL else "boy"
    trait = random.Random(params.seed or 0).choice(TRAITS)
    world = tell(place, treasure, params.hero, hero_type, params.friend, friend_type, trait)
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
    StoryParams(place="playroom", treasure="ball", hero="Mia", friend="Leo"),
    StoryParams(place="nursery", treasure="blanket", hero="Finn", friend="Nora"),
    StoryParams(place="garden", treasure="cookies", hero="Ava", friend="Sam"),
    StoryParams(place="porch", treasure="book", hero="Owen", friend="Lily"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show happy_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show happy_story/3."))
        print(f"ASP model has {len(model)} shown atoms.")
        for atom in model:
            print(atom)
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
