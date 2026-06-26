#!/usr/bin/env python3
"""
A standalone story world for a small Animal Story about curiosity, bravery,
and a surprising feather.

Premise:
- A little animal wants to explore something new.
- A shiny marvel catches attention.
- A cheapo object seems useless at first.
- A feather becomes the key to a gentle brave choice.

This world is intentionally small and constraint-checked. It models a tiny
outdoor animal scene with physical meters and emotional memes.
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
# Core data model
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
    kind: str = "thing"  # "animal" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    location: str = ""

    animal: object | None = None
    helper: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "animal" and self.type in {"fox", "rabbit", "cat", "dog", "mouse", "bear", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    indoors: bool = False
    affords: set[str] = field(default_factory=set)
    outdoors: bool = False
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
class ObjectDef:
    label: str
    phrase: str
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
class StoryParams:
    place: str
    animal: str
    prize: str
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


@dataclass
class World:
    place: Place
    animals: dict[str, Entity] = field(default_factory=dict)
    things: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    world: object | None = None
    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add_animal(self, ent: Entity) -> Entity:
        self.animals[ent.id] = ent
        return ent

    def add_thing(self, ent: Entity) -> Entity:
        self.things[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.animals.get(eid) or self.things[eid]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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


PLACES = {
    "meadow": Place(name="the meadow", outdoors=True, affords={"search", "gather", "watch"}),
    "woods": Place(name="the woods", outdoors=True, affords={"search", "gather", "watch"}),
    "pond": Place(name="the pond", outdoors=True, affords={"search", "watch", "float"}),
    "barnyard": Place(name="the barnyard", outdoors=True, affords={"search", "watch"}),
}

ANIMALS = {
    "fox": {"type": "fox", "label": "fox"},
    "rabbit": {"type": "rabbit", "label": "rabbit"},
    "bird": {"type": "bird", "label": "bird"},
    "mouse": {"type": "mouse", "label": "mouse"},
}

PRIZES = {
    "feather": ObjectDef(label="feather", phrase="a pale feather", region="mouth"),
    "marvel": ObjectDef(label="marvel", phrase="a shiny marvel", region="paw"),
    "cheapo": ObjectDef(label="cheapo", phrase="a cheapo little trinket", region="paw"),
}

# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------
def is_plausibly_risky(animal: Entity, prize: Entity) -> bool:
    # In this little world, the "feather" and "marvel" are both attention-grabbers.
    # A story is reasonable when the animal's curiosity pushes it toward the object.
    return prize.id in {"feather", "marvel", "cheapo"} and animal.memes.get("curiosity", 0) >= 1


def valid_combo(place: str, animal: str, prize: str) -> bool:
    return place in PLACES and animal in ANIMALS and prize in PRIZES


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
animal(A) :- animal_fact(A).
place(P) :- place_fact(P).
prize(P) :- prize_fact(P).

valid(Place, Animal, Prize) :- place(Place), animal(Animal), prize(Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place_fact", pid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal_fact", aid))
    for prid in PRIZES:
        lines.append(asp.fact("prize_fact", prid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted((p, a, r) for p in PLACES for a in ANIMALS for r in PRIZES if valid_combo(p, a, r))
    cl = asp_valid_combos()
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if set(py) - set(cl):
        print("  only in python:", sorted(set(py) - set(cl)))
    if set(cl) - set(py):
        print("  only in clingo:", sorted(set(cl) - set(py)))
    return 1


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    world = World(place=_safe_lookup(PLACES, params.place))

    animal_def = _safe_lookup(ANIMALS, params.animal)
    animal = world.add_animal(Entity(
        id="hero",
        kind="animal",
        type=animal_def["type"],
        label=animal_def["label"],
        traits=["little", "curious", "brave"],
        meters={"energy": 2.0},
        memes={"curiosity": 0.0, "bravery": 0.0, "worry": 0.0, "joy": 0.0},
        location=world.place.name,
    ))
    prize_def = _safe_lookup(PRIZES, params.prize)
    prize = world.add_thing(Entity(
        id=params.prize,
        kind="thing",
        type=params.prize,
        label=prize_def.label,
        phrase=prize_def.phrase,
        plural=prize_def.plural,
        meters={"sparkle": 1.0 if params.prize == "marvel" else 0.0},
        memes={"mystery": 1.0 if params.prize in {"marvel", "feather"} else 0.5},
        location=world.place.name,
    ))
    helper = world.add_thing(Entity(
        id="cheapo",
        kind="thing",
        type="cheapo",
        label="cheapo",
        phrase="a cheapo little trinket",
        meters={"sparkle": 0.0},
        memes={"oddness": 1.0},
        location=world.place.name,
    ))

    # Act 1: setup.
    world.say(
        f"One day, a little {animal.label} was in {world.place.name} and noticed "
        f"{prize.phrase} near a soft patch of grass."
    )
    if params.prize == "feather":
        world.say(
            f"It looked light as a breeze, and the {animal.label} wanted to know where it had come from."
        )
    elif params.prize == "marvel":
        world.say(
            f"It shimmered in a way that felt like a tiny marvel, and the {animal.label} blinked at it twice."
        )
    else:
        world.say(
            f"It was a cheapo little trinket, and at first the {animal.label} almost ignored it."
        )

    world.para()

    # Act 2: curiosity turns into a small quest.
    animal.memes["curiosity"] += 1.0
    world.say(
        f"The {animal.label} took a careful step closer, because curiosity can make even a quiet animal feel bold."
    )
    world.say(
        f"Then the {animal.label} sniffed the air, looked under a leaf, and followed the tiny signs around the prize."
    )

    # If the prize is feather, its path can be found by a bird. If marvel, it is seen as treasure.
    if params.prize == "feather":
        world.say(
            f"A bird overhead fluttered its wings, and one pale feather drifted down like a secret answer."
        )
        animal.memes["bravery"] += 1.0
    elif params.prize == "marvel":
        world.say(
            f"The shiny marvel caught the sun, and the little {animal.label} felt brave enough to reach for it."
        )
        animal.memes["bravery"] += 0.5
    else:
        world.say(
            f"The cheapo trinket was plain, but the little {animal.label} decided that plain things can still matter."
        )
        animal.memes["bravery"] += 0.5

    # Act 3: resolution.
    world.para()
    if params.prize == "feather":
        animal.meters["care"] = animal.meters.get("care", 0.0) + 1.0
        world.say(
            f"The {animal.label} picked up the feather gently and held it as if it were a tiny promise."
        )
        world.say(
            f"That made the little animal feel proud, because it had been curious and brave without being rough."
        )
    elif params.prize == "marvel":
        animal.meters["care"] = animal.meters.get("care", 0.0) + 1.0
        world.say(
            f"The {animal.label} carried the marvel back to a safe nook, where it could shine without getting lost."
        )
        world.say(
            f"The animal's brave choice turned the sparkling thing from a mystery into a treasure for later."
        )
    else:
        helper.meters["usefulness"] = 1.0
        world.say(
            f"The little {animal.label} tucked the cheapo trinket beside the feather, and together they made a neat little find."
        )
        world.say(
            f"In the end, the animal learned that a small thing can be special when someone looks at it with curiosity."
        )

    animal.memes["joy"] += 1.0
    world.facts.update(
        hero=animal,
        prize=prize,
        helper=helper,
        place=params.place,
        animal=params.animal,
        prize_name=params.prize,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short Animal Story about a curious {hero.type} who finds {prize.label} in {world.place.name}.',
        f"Tell a gentle story where a little {hero.label} becomes brave after noticing {prize.phrase}.",
        'Write a child-friendly story using the words "marvel", "cheapo", and "feather".',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    prize = _safe_fact(world, world.facts, "prize")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about a little {hero.label} who was curious and brave in {world.place.name}.",
        ),
        QAItem(
            question=f"What did the animal notice first?",
            answer=f"The animal noticed {prize.phrase} near the grass.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The little animal handled the object gently and felt proud for choosing a careful, brave way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a feather?",
            answer="A feather is a light covering from a bird that can float on the breeze.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn about something new.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something scary or new while trying to stay calm and careful.",
        ),
        QAItem(
            question="What can a marvel be?",
            answer="A marvel is something surprising or wonderful that makes you stop and look.",
        ),
        QAItem(
            question="What is something cheapo?",
            answer="A cheapo thing is very plain or not fancy, but it can still be worth keeping if it matters to you.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sampling / parsing
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world about curiosity, bravery, marvel, cheapo, and feather.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--prize", choices=sorted(PRIZES))
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
    choices = [(p, a, r) for p in PLACES for a in ANIMALS for r in PRIZES if valid_combo(p, a, r)]
    if getattr(args, "place", None):
        choices = [c for c in choices if c[0] == getattr(args, "place", None)]
    if getattr(args, "animal", None):
        choices = [c for c in choices if c[1] == getattr(args, "animal", None)]
    if getattr(args, "prize", None):
        choices = [c for c in choices if c[2] == getattr(args, "prize", None)]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, animal, prize = rng.choice(sorted(choices))
    return StoryParams(place=place, animal=animal, prize=prize)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.animals.values()) + list(world.things.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.kind:6}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} valid combos.")
        for t in asp_valid_combos():
            print(t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="meadow", animal="rabbit", prize="feather"),
            StoryParams(place="woods", animal="fox", prize="marvel"),
            StoryParams(place="pond", animal="bird", prize="cheapo"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
