#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/hoofer_problem_solving_whodunit.py
==============================================================================================================

A small standalone storyworld for a child-facing whodunit: a little detective,
a helpful hoofer, a set of clues, and a gentle problem-solving reveal.

The world is built around a simple mystery premise:
- something goes missing,
- the detective and hoofer gather clues,
- the clues point to one reasonable culprit,
- the missing thing is returned, and the ending proves what changed.

This script follows the Storyweavers contract:
- self-contained stdlib world script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- supports generate / emit / main plus CLI flags for trace, qa, json, asp, verify, show-asp
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    memo: str = ""
    helper: object | None = None
    hero: object | None = None
    suspect: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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


@dataclass(frozen=True)
class Setting:
    place: str
    indoor: bool
    afford: str
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


@dataclass(frozen=True)
class Mystery:
    id: str
    thing: str
    phrase: str
    location: str
    clue_kind: str
    clue_text: str
    suspect: str
    reason: str
    resolution: str
    tags: tuple[str, ...]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass(frozen=True)
class Helper:
    id: str
    label: str
    type: str = "horse"
    traits: tuple[str, ...] = ("patient", "smart")
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.trace_steps: list[str] = []

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
            self.trace_steps.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "barn": Setting(place="the barn", indoor=True, afford="investigation"),
    "garden": Setting(place="the garden", indoor=False, afford="investigation"),
    "kitchen": Setting(place="the kitchen", indoor=True, afford="investigation"),
}

MYSTERIES = {
    "pie": Mystery(
        id="pie",
        thing="pie",
        phrase="a strawberry pie",
        location="the windowsill",
        clue_kind="crumb",
        clue_text="There were strawberry crumbs on the floor.",
        suspect="goat",
        reason="a goat had frosting on its nose and liked sweet things",
        resolution="the pie was brought back to the windowsill, whole again",
        tags=("crumb", "sweet", "goat"),
    ),
    "bell": Mystery(
        id="bell",
        thing="bell",
        phrase="a shiny brass bell",
        location="the tack room hook",
        clue_kind="scratch",
        clue_text="There were tiny scratches on the hook and a trail of straw.",
        suspect="foal",
        reason="the small hoofprints were the right size for a foal",
        resolution="the bell was hung back on its hook, where it could chime softly",
        tags=("scratch", "straw", "foal"),
    ),
    "ribbon": Mystery(
        id="ribbon",
        thing="ribbon",
        phrase="a red ribbon",
        location="the porch chair",
        clue_kind="mud",
        clue_text="A muddy ribbon trail led toward the flower patch.",
        suspect="rabbit",
        reason="the ribbon had been used to tie up a flower bunch",
        resolution="the ribbon was tied neatly back around the chair",
        tags=("mud", "flower", "rabbit"),
    ),
    "cookie_tin": Mystery(
        id="cookie_tin",
        thing="cookie tin",
        phrase="a tin of oat cookies",
        location="the pantry shelf",
        clue_kind="hoofprint",
        clue_text="Little hoofprints stopped at the pantry step and turned around.",
        suspect="kid_goat",
        reason="the crumbs led straight to the goat pen",
        resolution="the cookies were counted and shared, and the tin went back on the shelf",
        tags=("hoofprint", "crumb", "goat"),
    ),
}

HELPERS = {
    "hoofer": Helper(id="hoofer", label="Hoofer", type="horse"),
}

GUESTS = {
    "goat": "a white goat",
    "foal": "a small foal",
    "rabbit": "a round rabbit",
    "kid_goat": "a bouncy kid goat",
}

HERO_NAMES = ["Mina", "Toby", "Lena", "Finn", "Ruby", "Owen"]
HERO_TYPES = ["girl", "boy"]
TRAITS = ["curious", "careful", "brave", "quiet", "bright"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    hero_type: str
    trait: str
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


def _hero_ref(hero: Entity) -> str:
    return hero.id


def _hero_desc(hero: Entity) -> str:
    trait = next((t for t in hero.memes.get("traits", [])), "curious")
    return f"little {trait} {hero.type}"


def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def introduce(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} was a little detective who loved solving small puzzles, and {helper.label} the hoofer liked to help."
    )
    world.say(
        f"One morning, something important went missing: {mystery.phrase} from {mystery.location}."
    )


def search(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    _add_meme(hero, "curiosity", 1)
    _add_meme(helper, "attention", 1)
    world.say(
        f"{hero.id} looked at the empty spot, then at the floor. {helper.label} lowered {helper.pronoun('possessive')} head and snuffled near the ground."
    )
    _add_meme(hero, "confidence", 1)


def clue(world: World, mystery: Mystery) -> None:
    world.say(mystery.clue_text)
    _add_meme(world.facts["hero"], "logic", 1)
    _add_meme(world.facts["hero"], "certainty", 1)


def deduce(world: World, hero: Entity, helper: Entity, mystery: Mystery, suspect_ent: Entity) -> None:
    _add_meme(hero, "joy", 1)
    hero.memes["mystery_solved"] = 1.0
    world.say(
        f"{helper.label} pointed with {helper.pronoun('possessive')} nose, and {hero.id} understood the clue."
    )
    world.say(
        f"It had to be {suspect_ent.label}: {mystery.reason}."
    )


def resolve(world: World, hero: Entity, helper: Entity, mystery: Mystery, suspect_ent: Entity) -> None:
    _add_meme(suspect_ent, "relief", 1)
    world.say(
        f"{suspect_ent.label} came back looking sorry, and {hero.id} did not scold. {hero.id} simply asked for {mystery.thing} back."
    )
    world.say(
        f"Then {hero.id} put it where it belonged again. {mystery.resolution.capitalize()}."
    )
    _add_meme(hero, "pride", 1)
    _add_meme(helper, "pride", 1)


def tell(setting: Setting, mystery: Mystery, hero_name: str, hero_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memo=""))
    helper = world.add(Entity(id="Hoofer", kind="character", type="horse", label="Hoofer"))
    suspect = world.add(Entity(id="Suspect", kind="character", type=mystery.suspect, label=_safe_lookup(GUESTS, mystery.suspect)))

    hero.memes["traits"] = [trait]
    helper.memes["traits"] = ["patient", "smart"]

    world.facts.update(hero=hero, helper=helper, mystery=mystery, suspect=suspect, setting=setting)

    introduce(world, hero, helper, mystery)
    world.para()
    search(world, hero, helper, mystery)
    clue(world, mystery)
    world.para()
    deduce(world, hero, helper, mystery, suspect)
    resolve(world, hero, helper, mystery, suspect)
    return world


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for mystery in MYSTERIES:
            combos.append((place, mystery))
    return combos


def story_for(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(MYSTERIES, params.mystery), params.hero_name, params.hero_type, params.trait)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = _safe_fact(world, f, "mystery")
    return [
        f'Write a short whodunit for a young child about a missing {mystery.thing} and a helpful hoofer named Hoofer.',
        f"Tell a gentle detective story where {f['hero'].id} follows clues to find who took {mystery.phrase}.",
        f'Write a child-friendly mystery story that uses the word "hoofer" and ends with the missing thing back in place.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    suspect: Entity = _safe_fact(world, f, "suspect")
    helper: Entity = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"What was missing in the story?",
            answer=f"{mystery.phrase} was missing from {mystery.location}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the mystery?",
            answer=f"Hoofer the hoofer helped by noticing clues and pointing the way.",
        ),
        QAItem(
            question=f"Who turned out to be the one connected to the clue?",
            answer=f"It was {suspect.label}, because {mystery.reason}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The missing {mystery.thing} was returned to its place, and the mystery was solved.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = _safe_fact(world, f, "mystery")
    out = [
        QAItem(
            question="What is a clue in a mystery story?",
            answer="A clue is a small bit of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully, asks questions, and uses clues to solve a problem.",
        ),
    ]
    if "hoof" in mystery.tags or "hoofprint" in mystery.tags:
        out.append(
            QAItem(
                question="What are hoofprints?",
                answer="Hoofprints are marks left on the ground by animals with hooves, like horses or goats.",
            )
        )
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.extend(f"  step: {s}" for s in world.trace_steps)
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is valid when the place and mystery are both grounded facts.
valid(Place, Mystery) :- setting(Place), mystery(Mystery).

% A clue belongs to the mystery, and a clue supports the deduction.
supports(Mystery) :- mystery(Mystery), clue_kind(Mystery, _), suspect(Mystery, _).

% We only show valid mysteries that have a supported clue and a clear suspect.
eligible(Place, Mystery) :- valid(Place, Mystery), supports(Mystery).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("thing", mid, m.thing))
        lines.append(asp.fact("phrase", mid, m.phrase))
        lines.append(asp.fact("location", mid, m.location))
        lines.append(asp.fact("clue_kind", mid, m.clue_kind))
        lines.append(asp.fact("suspect", mid, m.suspect))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show eligible/2."))
    return sorted(set(asp.atoms(model, "eligible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP parity matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle whodunit story world with Hoofer the hoofer.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "mystery", None):
        combos = [c for c in combos if c[1] == getattr(args, "mystery", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery = rng.choice(combos)
    gender = getattr(args, "gender", None) or rng.choice(HERO_TYPES)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, hero_name=name, hero_type=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    return story_for(params)


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
    StoryParams(place="barn", mystery="pie", hero_name="Mina", hero_type="girl", trait="curious"),
    StoryParams(place="garden", mystery="bell", hero_name="Toby", hero_type="boy", trait="careful"),
    StoryParams(place="kitchen", mystery="cookie_tin", hero_name="Lena", hero_type="girl", trait="bright"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show eligible/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} eligible combos:")
        for place, mystery in combos:
            print(f"  {place}  {mystery}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
