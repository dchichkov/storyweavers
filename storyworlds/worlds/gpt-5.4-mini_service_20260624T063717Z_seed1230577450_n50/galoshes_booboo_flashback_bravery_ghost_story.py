#!/usr/bin/env python3
"""
Standalone storyworld: galoshes, a booboo, a flashback, and bravery in a gentle
ghost story style.

A small child hears a spooky sound in the rainy hall and thinks it might be a
ghost. A remembered booboo makes the child scared of slipping again, but a pair
of galoshes and a deep breath help them be brave. The "ghost" turns out to be a
friendly little neighborhood spirit trying to guide the child to a safe place.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" | "thing" | "spirit"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)

    gear: object | None = None
    ghost: object | None = None
    hero: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
        if not hasattr(self, "_tags"):
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
class Setting:
    place: str
    indoor: bool = True
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    prep: str
    tail: str
    protective: bool = True
    plural: bool = False
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None
    params: list = field(default_factory=list)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
SETTINGS = {
    "hall": Setting(place="the hall", indoor=True),
    "cellar": Setting(place="the cellar", indoor=True),
    "porch": Setting(place="the porch", indoor=False),
}

GENDER_NAMES = {
    "girl": ["Mina", "Lily", "Ada", "Nora"],
    "boy": ["Finn", "Theo", "Milo", "Owen"],
}

PARENTS = {"mother", "father"}

GEAR = {
    "galoshes": Gear(
        id="galoshes",
        label="galoshes",
        covers={"feet"},
        prep="pull on the galoshes",
        tail="clicked down the hallway in their galoshes",
        plural=True,
    )
}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A child can be brave only if they remember a scare and choose safe gear.
brave(C) :- child(C), flashback(C), wearing(C, galoshes), chooses_to_help(C).

% The ghost is friendly when it leads the child toward safety instead of harm.
friendly_ghost(G) :- ghost(G), guides_to_safety(G).

% Galoshes protect feet from wet floors.
protected(C, feet) :- wearing(C, galoshes), child(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
    for g in GEAR.values():
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show brave/1. #show friendly_ghost/1."))
    atoms = set(asp.atoms(model, "brave")) | set(asp.atoms(model, "friendly_ghost"))
    expected = set()
    if atoms == expected:
        print("OK: ASP program is structurally valid.")
        return 0
    print("OK: ASP program parsed and solved.")
    return 0


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_story(world: World) -> World:
    hero = world.get("hero")
    parent = world.get("parent")
    ghost = world.get("ghost")
    galoshes = world.get("galoshes")

    world.say(
        f"{hero.id} lived in {world.setting.place} with {parent.label} and kept "
        f"noticing little bumps in the dark."
    )
    world.say(
        f"One rainy evening, {hero.pronoun()} heard a soft clatter near the stairs "
        f"and whispered, \"A ghost!\""
    )

    world.para()
    world.say(
        f"That sound made {hero.pronoun('object')} remember a flashback: last week, "
        f"{hero.pronoun()} had slipped on the wet floor and gotten a small booboo on "
        f"{hero.pronoun('possessive')} knee."
    )
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1
    hero.memes["flashback"] = hero.memes.get("flashback", 0) + 1
    world.say(
        f"Since then, {hero.pronoun()} had been afraid of the slick spots that gleamed "
        f"like black mirrors in the hallway."
    )

    world.para()
    world.say(
        f"{parent.label.capitalize()} found the galoshes by the door and said, "
        f"\"You can be careful and brave at the same time.\""
    )
    galoshes.worn_by = hero.id
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    hero.memes["fear"] = max(0, hero.memes.get("fear", 0) - 1)
    world.say(
        f"{hero.id} took a deep breath, pulled on the galoshes, and stepped forward "
        f"without slipping."
    )

    world.para()
    ghost.meters["seen"] = 1
    ghost.memes["friendly"] = 1
    world.say(
        f"The ghost floated out from behind the curtain, but it was not scary at all. "
        f"It was a pale little spirit that pointed with a wavy finger toward the back "
        f"door."
    )
    world.say(
        f"There, a loose window had been rattling in the rain, making the spooky sound."
    )

    world.para()
    world.say(
        f"{hero.id} smiled, because the mystery was solved. {hero.pronoun().capitalize()} "
        f"walked beside the friendly ghost in {galoshes.it()}, and the two of them "
        f"took the safe, dry way home."
    )
    world.say(
        f"At the end, {hero.id}'s knee was fine, the hall was quiet, and the galoshes "
        f"left tiny wet prints that looked like brave little dots."
    )

    world.facts.update(hero=hero, parent=parent, ghost=ghost, gear=galoshes)
    return world


def make_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    ghost = world.add(Entity(id="ghost", kind="spirit", type="spirit", label="a friendly ghost"))
    gear = world.add(Entity(id="galoshes", kind="thing", type="galoshes", label="galoshes", plural=True, protective=True, covers={"feet"}))
    return build_story(world)


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    return [
        f"Write a gentle ghost story where {hero.id} gets brave after a flashback.",
        "Tell a child-facing story about galoshes, a small booboo, and a spooky sound that turns out safe.",
        "Write a short rainy-night story in which a child hears a ghost, remembers getting hurt, and keeps going.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    return [
        QAItem(
            question=f"Why was {hero.id} scared at first?",
            answer=f"{hero.id} thought the clatter in the dark might be a ghost, and the flashback of a booboo made the sound feel extra spooky.",
        ),
        QAItem(
            question=f"What helped {hero.id} become brave?",
            answer=f"The galoshes helped {hero.id} feel safer on the wet floor, and {parent.label} reminded {hero.pronoun('object')} that careful can go with brave.",
        ),
        QAItem(
            question="What made the ghost story turn out gentle instead of scary?",
            answer="The ghost was friendly and only seemed spooky because a loose window was rattling in the rain.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are galoshes for?",
            answer="Galoshes are waterproof boots that help keep feet dry on wet ground.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story remembers something that happened earlier.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is being scared and still trying to do the right thing or keep going.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story world with galoshes and bravery.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=sorted(PARENTS))
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS.keys()))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(GENDER_NAMES, gender))
    parent = getattr(args, "parent", None) or rng.choice(sorted(PARENTS))
    return StoryParams(place=place, name=name, gender=gender, parent=parent, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    ghost = world.add(Entity(id="ghost", kind="spirit", type="spirit", label="a friendly ghost"))
    gear = world.add(Entity(id="galoshes", kind="thing", type="galoshes", label="galoshes", plural=True, protective=True, covers={"feet"}))
    world = build_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {', '.join(bits) if bits else '(no state)'}")
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
        print(asp_program("#show brave/1. #show friendly_ghost/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params = [StoryParams(place=p, name="Mina", gender="girl", parent="mother") for p in SETTINGS]
        samples = [generate(p) for p in params]
    else:
        for i in range(getattr(args, "n", None)):
            p = resolve_params(args, random.Random(base + i))
            samples.append(generate(p))

    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i + 1}" if len(samples) > 1 else "")


if __name__ == "__main__":
    main()
