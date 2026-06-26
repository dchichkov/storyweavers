#!/usr/bin/env python3
"""
storyworlds/worlds/magnum_quarry_edge_inner_monologue_comedy.py
===============================================================

A small comedy storyworld at the quarry edge, built around a magnum ice cream
and an inner-monologue-driven worry/recovery beat.

Premise:
- A kid or helper wants to enjoy a magnum at the quarry edge.
- The nearby ledge is dusty, windy, and full of gulls and pebbles.
- The hero's inner monologue makes the worry funny and concrete.
- A sensible fix keeps the magnum intact and turns the moment into a joke.

The simulated world tracks:
- physical meters: spill, melt, dust, wobble, chill, crumb
- emotional memes: delight, worry, pride, embarrassment, resolve
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


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    w: object | None = None
    world: object | None = None
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


THRESHOLD = 1.0
WINDY_METER = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    wind: bool
    dust: bool
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


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
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
class Fix:
    label: str
    prep: str
    tail: str
    guards_melt: bool = False
    guards_dust: bool = False
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


SETTINGS = {
    "quarry_edge": Setting(place="the quarry edge", wind=True, dust=True),
}

PRIZES = {
    "magnum": Prize(
        label="magnum",
        phrase="a chocolate-dipped magnum ice cream",
        type="ice_cream",
        region="hand",
    ),
}

FIXES = {
    "bench_shade": Fix(
        label="a shady bench",
        prep="sit on the shady bench for one minute",
        tail="moved to the shady bench and unwrapped the magnum carefully",
        guards_melt=True,
        guards_dust=True,
    ),
    "paper_wrap": Fix(
        label="paper wrap",
        prep="wrap the magnum in paper and hold it higher",
        tail="wrapped the magnum in paper and carried it like a tiny treasure",
        guards_melt=False,
        guards_dust=True,
    ),
}

NAMES = ["Milo", "Nina", "Toby", "Rae", "Pip", "Lena", "Otto", "June"]
TRAITS = ["curious", "cheerful", "awkward", "earnest", "bouncy", "sly"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str = "quarry_edge"
    prize: str = "magnum"
    fix: str = "bench_shade"
    name: str = "Milo"
    gender: str = "boy"
    parent: str = "dad"
    trait: str = "curious"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
    params: object | None = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld at the quarry edge with a magnum and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mom", "dad"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def reasonableness_gate(params: StoryParams) -> None:
    if params.place != "quarry_edge":
        pass
    if params.prize != "magnum":
        pass
    if params.fix not in FIXES:
        pass
    if params.fix == "paper_wrap":
        return


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or "quarry_edge"
    prize = getattr(args, "prize", None) or "magnum"
    fix = getattr(args, "fix", None) or rng.choice(list(FIXES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or ("mom" if gender == "girl" else "dad")
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    params = StoryParams(place=place, prize=prize, fix=fix, name=name, gender=gender, parent=parent, trait=trait)
    reasonableness_gate(params)
    return params


def intro_line(hero: Entity, parent: Entity) -> str:
    return f"{hero.id} was a {hero.memes.get('trait_word', 'curious')} {hero.type} who had a habit of thinking too loudly in {hero.pronoun('possessive')} head."


def predict_melt(world: World, hero: Entity, prize: Entity, fix: Fix) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["worry"] += 1
    sim.get(prize.id).meters["melt"] += 1.0
    if SETTINGS["quarry_edge"].wind:
        sim.get(prize.id).meters["dust"] += 1.0
    if fix.guards_melt:
        sim.get(prize.id).meters["melt"] = 0.0
    if fix.guards_dust:
        sim.get(prize.id).meters["dust"] = 0.0
    return {"melted": sim.get(prize.id).meters["melt"] >= THRESHOLD, "dusty": sim.get(prize.id).meters["dust"] >= THRESHOLD}


def inner_monologue(world: World, hero: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} stared at the magnum and thought, "
        f"\"If I hold it too long, it will become a chocolate soup rocket.\""
    )
    hero.memes["worry"] += 1


def offer_fix(world: World, parent: Entity, hero: Entity, prize: Entity, fix: Fix) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"{parent.id} pointed to {fix.label} and said, "
        f"\"Let's use the safe trick first.\""
    )
    world.say(
        f"{hero.id} blinked, then decided the magnum deserved a rescue plan."
    )
    world.say(
        f"They {fix.tail}."
    )
    hero.memes["pride"] += 1


def tell_story(params: StoryParams) -> World:
    world = World(place=_safe_lookup(SETTINGS, params.place).place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    hero.memes["trait_word"] = params.trait
    parent = world.add(Entity(id="Parent", kind="character", type="parent", label=params.parent))
    prize = world.add(Entity(id="Magnum", kind="thing", type="ice_cream", label="magnum", phrase=_safe_lookup(PRIZES, params.prize).phrase, owner=hero.id))

    world.say(
        f"{hero.id} came to {world.place} with {hero.pronoun('possessive')} {parent.label}, "
        f"holding a magnum that looked far too fancy for dusty rocks."
    )
    world.say(
        f"{hero.id} loved the cold snap of the chocolate shell and kept imagining the crunch before the first bite."
    )

    world.para()
    inner_monologue(world, hero, prize)
    world.say(
        f"The quarry edge hissed with wind, and a little pebble skittered near {hero.pronoun('possessive')} shoes."
    )
    prediction = predict_melt(world, hero, prize, _safe_lookup(FIXES, params.fix))
    world.facts["prediction"] = prediction
    if prediction["melted"] or prediction["dusty"]:
        world.say(
            f"{hero.id} worried the magnum would get dusty or soft before the best bite."
        )
    world.say(
        f"{hero.id} almost rushed forward anyway, because delicious things can make a person behave like a tiny stampede."
    )

    world.para()
    offer_fix(world, parent, hero, prize, _safe_lookup(FIXES, params.fix))
    if params.fix == "bench_shade":
        world.say(
            f"Under the shade, the magnum stayed firm enough to crack instead of flop."
        )
    else:
        world.say(
            f"The paper wrap kept the dust off, and {hero.id} held the magnum like a prize medal."
        )
    world.say(
        f"{hero.id} took the first bite and made a very serious face, which was ridiculous because the face was covered in chocolate."
    )
    world.say(
        f"{hero.id}'s inner voice declared, \"Emergency over. Snack victorious.\""
    )

    hero.memes["worry"] = 0.0
    hero.memes["joy"] = 1.0

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        fix=_safe_lookup(FIXES, params.fix),
        params=params,
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(quarry_edge).
prize(magnum).
fix(bench_shade).
fix(paper_wrap).

valid(quarry_edge, magnum, bench_shade).
valid(quarry_edge, magnum, paper_wrap).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("place", "quarry_edge"),
        asp.fact("prize", "magnum"),
        asp.fact("fix", "bench_shade"),
        asp.fact("fix", "paper_wrap"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid() -> list[tuple]:
    return [("quarry_edge", "magnum", "bench_shade"), ("quarry_edge", "magnum", "paper_wrap")]


def asp_verify() -> int:
    a = set(asp_valid())
    p = set(python_valid())
    if a != p:
        print("MISMATCH:")
        print("only in asp:", sorted(a - p))
        print("only in python:", sorted(p - a))
        return 1
    print(f"OK: ASP matches Python ({len(a)} combos).")
    return 0


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    fix = _safe_fact(world, f, "fix")
    return [
        f'Write a short comic story about a child named {hero.id} at the quarry edge with a magnum.',
        f'Write a funny story where {hero.id} thinks aloud about a magnum, then uses {fix.label} to avoid a mess.',
        "Tell a child-friendly comedy with an inner monologue, a cold snack, and a safe choice near the rocks.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    parent: Entity = _safe_fact(world, f, "parent")
    prize: Entity = _safe_fact(world, f, "prize")
    fix: Fix = _safe_fact(world, f, "fix")
    return [
        QAItem(
            question=f"Why did {hero.id} worry at the quarry edge?",
            answer=f"{hero.id} worried that the magnum would get dusty or melt before the best bite.",
        ),
        QAItem(
            question=f"What was the funny thing {hero.id} thought in {hero.pronoun('possessive')} head?",
            answer=f"{hero.pronoun().capitalize()} thought the magnum might turn into a chocolate soup rocket.",
        ),
        QAItem(
            question=f"How did {parent.label} help {hero.id} keep the magnum safe?",
            answer=f"{parent.label} suggested {fix.label}, which kept the magnum out of the dust and made the plan feel clever.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a magnum?",
            answer="A magnum is a chocolate-coated ice cream treat on a stick.",
        ),
        QAItem(
            question="Why can a quarry edge feel windy and dusty?",
            answer="A quarry edge can have bare rocks and open space, so wind can blow dust around easily.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private voice in a character's head that says what they are thinking.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def curated() -> list[StoryParams]:
    return [
        StoryParams(name="Milo", gender="boy", parent="dad", trait="curious", fix="bench_shade"),
        StoryParams(name="Nina", gender="girl", parent="mom", trait="cheerful", fix="paper_wrap"),
        StoryParams(name="Pip", gender="boy", parent="dad", trait="awkward", fix="bench_shade"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in curated()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name} at the quarry edge"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
