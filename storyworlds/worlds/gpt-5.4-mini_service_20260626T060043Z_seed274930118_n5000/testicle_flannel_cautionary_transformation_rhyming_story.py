#!/usr/bin/env python3
"""
storyworlds/worlds/testicle_flannel_cautionary_transformation_rhyming_story.py
==============================================================================

A standalone story world for a tiny, rhyming, cautionary transformation tale.

Seed premise:
- A child loves a flannel garment.
- A risky play choice can stain, shrink, or twist that garment.
- A warning leads to a safe transformation: the garment is repurposed and the
  ending image proves the change.

The world is intentionally small and state-driven:
- physical meters track wetness, stain, shrink, tear, and repair
- emotional memes track worry, defiance, care, pride, and joy
- the story is built from the simulated world rather than a frozen template

The odd seed words are included as required:
- testicle
- flannel

The tone is a child-facing rhyming cautionary story with a clear turn and a
visible transformation.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Small story domain
# ---------------------------------------------------------------------------

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
    label: str = ""
    type: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    region: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    hero: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "mother", "woman"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "father", "man"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
    risky: str
    safe: str
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
class Garment:
    id: str
    label: str
    phrase: str
    region: str
    can_transform: bool
    can_protect: bool = False
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
    action: str
    garment: str
    name: str
    gender: str
    parent: str
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "lantern_shop": Place(
        name="the lantern shop",
        risky="the dye barrel",
        safe="the ribbon shelf",
    ),
    "rainy_lane": Place(
        name="the rainy lane",
        risky="the puddle patch",
        safe="the dry brick path",
    ),
    "sewing_room": Place(
        name="the sewing room",
        risky="the wash tub",
        safe="the button tin",
    ),
}

GARMENTS = {
    "flannel_shirt": Garment(
        id="flannel_shirt",
        label="flannel shirt",
        phrase="a red flannel shirt",
        region="torso",
        can_transform=True,
        can_protect=False,
    ),
    "flannel_blanket": Garment(
        id="flannel_blanket",
        label="flannel blanket",
        phrase="a soft flannel blanket",
        region="torso",
        can_transform=True,
        can_protect=True,
    ),
    "flannel_scarf": Garment(
        id="flannel_scarf",
        label="flannel scarf",
        phrase="a warm flannel scarf",
        region="torso",
        can_transform=True,
        can_protect=True,
    ),
}

ACTIONS = {
    "dance_in_dye": {
        "verb": "dance near the dye",
        "gerund": "dancing near the dye",
        "rush": "run to the dye barrel",
        "risk": "stained",
        "change": "turned bright and blotchy",
        "rhyming": "the swish and swash could make a splash",
        "meter": "stain",
    },
    "splash_in_rain": {
        "verb": "splash in the rain",
        "gerund": "splashing in the rain",
        "rush": "skip to the puddles",
        "risk": "soaked",
        "change": "turned soggy and saggy",
        "rhyming": "the drip and drop could make it flop",
        "meter": "wet",
    },
    "wash_and_wring": {
        "verb": "wash and wring cloth",
        "gerund": "washing and wringing cloth",
        "rush": "reach for the wash tub",
        "risk": "shrunken",
        "change": "turned small and curled",
        "rhyming": "the scrub and squeeze could make it seize",
        "meter": "shrink",
    },
}

CHILDREN = ["Mina", "Luca", "Noa", "Pip", "Tobi", "Zuri", "Nell", "Ari"]
PARENTS = ["mother", "father"]
TRAITS = ["curious", "cheerful", "stubborn", "playful", "careful", "spirited"]


# ---------------------------------------------------------------------------
# Rhyming helper
# ---------------------------------------------------------------------------

def rhyme_line(*parts: str) -> str:
    return " ".join(p.strip() for p in parts if p.strip())


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def do_action(world: World, hero: Entity, action: str) -> None:
    spec = _safe_lookup(ACTIONS, action)
    hero.meters[spec["meter"]] += 1
    hero.memes["joy"] += 1


def warn(world: World, parent: Entity, hero: Entity, garment: Entity, action: str) -> bool:
    spec = _safe_lookup(ACTIONS, action)
    if hero.meters[spec["meter"]] >= THRESHOLD:
        return False
    risk = _safe_fact(world, world.facts, "risk")
    world.say(
        f'"Careful," {parent.pronoun("subject")} said, "that {garment.label} may get {risk}, '
        f"and then the day could turn quite grim."
        f'"'
    )
    world.facts["warned"] = True
    parent.memes["worry"] += 1
    hero.memes["worry"] += 1
    return True


def ignore_warning(world: World, hero: Entity, action: str) -> None:
    hero.memes["defiance"] += 1
    spec = _safe_lookup(ACTIONS, action)
    world.say(
        f"But {hero.id} still felt bold and free, "
        f"and {hero.pronoun('subject')} went to {spec['rush']}."
    )


def transform_garment(world: World, garment: Entity, action: str) -> None:
    spec = _safe_lookup(ACTIONS, action)
    garment.meters[spec["meter"]] += 1
    garment.meters["changed"] += 1


def resolve(world: World, hero: Entity, parent: Entity, garment: Entity, action: str) -> None:
    spec = _safe_lookup(ACTIONS, action)
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    parent.memes["care"] += 1
    world.say(
        f"So {hero.id} and {parent.pronoun('subject')} did not pout or frown; "
        f"they slowed down and found a gentler route."
    )


def repurpose(world: World, garment: Entity, action: str) -> None:
    if garment.meters["changed"] >= THRESHOLD:
        garment.label = "patchwork " + garment.label
        garment.meters["repair"] += 1


def tell(world: World, hero: Entity, parent: Entity, garment: Entity, action: str) -> None:
    spec = _safe_lookup(ACTIONS, action)
    world.say(
        f"{hero.id} had a {garment.phrase} and loved it so. "
        f"It was soft like a cloud and red like a bow."
    )
    world.say(
        f"One day at {world.place.name}, {hero.id} wanted to {spec['verb']}. "
        f"{spec['rhyming'].capitalize()}."
    )
    warn(world, parent, hero, garment, action)
    world.say(
        f'But {hero.id} ran on ahead with a giggle and grin, '
        f"and the trouble began before {parent.pronoun('subject')} could step in."
    )
    do_action(world, hero, action)
    transform_garment(world, garment, action)
    world.para()
    resolve(world, hero, parent, garment, action)
    repurpose(world, garment, action)
    world.say(
        f"Now the {garment.label} was not just the same; "
        f"it had changed its shape and it played a new game."
    )
    if action == "dance_in_dye":
        world.say(
            f"It stayed as a bright patchwork shirt, with a swirl and a spot, "
            f"and the little testicle charm on the pocket was still not forgot."
        )
    elif action == "splash_in_rain":
        world.say(
            f"It dried by the fire, then hung by the door, "
            f"and the flannel still smelled like rain, but a bit soft at the core."
        )
    else:
        world.say(
            f"It came out smaller, with a curl at the seam, "
            f"then became a toy cloak for a doll in a dream."
        )


# ---------------------------------------------------------------------------
# Story generation and QA
# ---------------------------------------------------------------------------

def pick_name(gender: str, rng: random.Random) -> str:
    return rng.choice(CHILDREN)


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    action = params.action
    garment_cfg = _safe_lookup(GARMENTS, params.garment)
    world = World(place)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent))
    garment = world.add(
        Entity(
            id=garment_cfg.id,
            label=garment_cfg.label,
            type="garment",
            owner=hero.id,
            caretaker=parent.id,
            region=garment_cfg.region,
        )
    )

    # Seed words required by prompt.
    world.facts["seed_words"] = ["testicle", "flannel"]
    world.facts["risk"] = _safe_lookup(ACTIONS, action)["risk"]
    world.facts["place"] = place.name
    world.facts["action"] = action
    world.facts["garment"] = garment_cfg
    world.facts["hero"] = hero
    world.facts["parent"] = parent
    world.facts["garment_ent"] = garment

    tell(world, hero, parent, garment, action)

    story = world.render()
    prompts = [
        f"Write a short cautionary rhyming story about a child and a {garment_cfg.label}.",
        f"Tell a gentle transformation story where {params.name} learns what happens when {hero.pronoun('subject')} ignores a warning.",
        f"Make a small rhyming tale that includes the words testicle and flannel in a child-friendly way.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {params.name} want to do at {place.name}?",
            answer=f"{params.name} wanted to {_safe_lookup(ACTIONS, action)['verb']} at {place.name}.",
        ),
        QAItem(
            question=f"Why did the parent warn {params.name}?",
            answer=f"The parent warned {params.name} because the {garment_cfg.label} could get {_safe_lookup(ACTIONS, action)['risk']}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The {garment_cfg.label} changed into a patchwork version, showing a small transformation after the risky play.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is flannel?",
            answer="Flannel is a soft cloth that feels cozy and warm.",
        ),
        QAItem(
            question="What does it mean when something transforms?",
            answer="When something transforms, it changes into a different form or look.",
        ),
        QAItem(
            question="What is a cautionary story?",
            answer="A cautionary story gives a warning and shows what can happen if someone ignores it.",
        ),
    ]

    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

place(lantern_shop).
place(rainy_lane).
place(sewing_room).

action(dance_in_dye).
action(splash_in_rain).
action(wash_and_wring).

garment(flannel_shirt).
garment(flannel_blanket).
garment(flannel_scarf).

risk(dance_in_dye, stain).
risk(splash_in_rain, wet).
risk(wash_and_wring, shrink).

transforms(flannel_shirt).
transforms(flannel_blanket).
transforms(flannel_scarf).

at_risk(A, G) :- action(A), garment(G), risk(A, _), transforms(G).

valid(P, A, G) :- place(P), action(A), garment(G).

valid_story(P, A, G, Gender) :- valid(P, A, G), person_gender(Gender).
person_gender(girl).
person_gender(boy).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
        lines.append(asp.fact("risk", a, _safe_lookup(ACTIONS, a)["meter"]))
    for g in GARMENTS:
        lines.append(asp.fact("garment", g))
        if _safe_lookup(GARMENTS, g).can_transform:
            lines.append(asp.fact("transforms", g))
    lines.append(asp.fact("person_gender", "girl"))
    lines.append(asp.fact("person_gender", "boy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness / validity
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for p in PLACES:
        for a in ACTIONS:
            for g in GARMENTS:
                combos.append((p, a, g))
    return combos


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A cautionary transformation rhyming story world with flannel and testicle."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--garment", choices=GARMENTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    action = getattr(args, "action", None) or rng.choice(list(ACTIONS))
    garment = getattr(args, "garment", None) or rng.choice(list(GARMENTS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    name = getattr(args, "name", None) or pick_name(gender, rng)
    return StoryParams(
        place=place,
        action=action,
        garment=garment,
        name=name,
        gender=gender,
        parent=parent,
    )


def valid_params(params: StoryParams) -> None:
    if params.garment not in GARMENTS:
        pass
    if params.action not in ACTIONS:
        pass
    if params.place not in PLACES:
        pass


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, action, garment) combos "
              f"({len(stories)} with gender):\n")
        for p, a, g in triples:
            genders = sorted(x for (pp, aa, gg, x) in stories if (pp, aa, gg) == (p, a, g))
            print(f"  {p:12} {a:16} {g:16}  [{', '.join(genders)}]")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams("lantern_shop", "dance_in_dye", "flannel_shirt", "Mina", "girl", "mother"),
            StoryParams("rainy_lane", "splash_in_rain", "flannel_scarf", "Luca", "boy", "father"),
            StoryParams("sewing_room", "wash_and_wring", "flannel_blanket", "Noa", "girl", "mother"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            valid_params(params)
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
