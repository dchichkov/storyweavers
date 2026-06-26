#!/usr/bin/env python3
"""
storyworlds/worlds/coconut_neighborhood_mystery_to_solve_whodunit.py
=====================================================================

A small whodunit-style storyworld about a neighborhood mystery involving a
missing coconut. The simulated state tracks clues, suspicion, and the final
reveal so the story reads like a true little detective tale rather than a
swapped-noun template.

Seed premise:
- A coconut goes missing in a neighborhood.
- A child detective investigates.
- The clues point to one plausible culprit.
- The reveal clears the confusion and restores calm.

The story aims for a cozy mystery tone with concrete, child-facing details.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    coconut: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "lady"}
        male = {"boy", "father", "dad", "man", "neighbor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Neighborhood:
    name: str = "the neighborhood"
    place: str = "the street"
    weather: str = "quiet"
    rumor: str = "missing coconut"
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
class Suspect:
    id: str
    label: str
    type: str
    motive: str
    clue: str
    harmless_reason: str
    reveal: str
    guilty: bool = False
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
    setting: str
    coconut_form: str
    hero_name: str
    hero_type: str
    helper_type: str
    suspect: str
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
    def __init__(self, neighborhood: Neighborhood) -> None:
        self.neighborhood = neighborhood
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "quiet_block": Neighborhood(name="the neighborhood", place="the quiet block", weather="quiet"),
    "corner_lane": Neighborhood(name="the neighborhood", place="the corner lane", weather="breezy"),
    "porch_row": Neighborhood(name="the neighborhood", place="the front porches", weather="sunny"),
}

COCONUT_FORMS = {
    "whole": "a whole coconut",
    "shaved": "a bowl of shaved coconut",
    "snack": "a little coconut snack",
}

HERO_TYPES = ["girl", "boy"]
HELPER_TYPES = ["cat", "dog", "grandma", "neighbor"]

SUSPECTS = {
    "cat": Suspect(
        id="cat",
        label="the tabby cat",
        type="cat",
        motive="It liked to bat at round things.",
        clue="tiny paw prints",
        harmless_reason="It was playing beside the fence and never carried the coconut away.",
        reveal="The cat only nudged a husk near the steps.",
        guilty=False,
    ),
    "mail_carrier": Suspect(
        id="mail_carrier",
        label="the mail carrier",
        type="neighbor",
        motive="He was carrying a bag and walking fast.",
        clue="a blue bag strap mark",
        harmless_reason="He only dropped letters by the gate.",
        reveal="The mail carrier had seen the coconut first and pointed the detective to the right house.",
        guilty=False,
    ),
    "gardener": Suspect(
        id="gardener",
        label="the gardener",
        type="neighbor",
        motive="She was working with tools and leaves.",
        clue="green leaf bits",
        harmless_reason="She was trimming vines near the hedge.",
        reveal="The gardener found a white trail leading under the hedges.",
        guilty=False,
    ),
    "brother": Suspect(
        id="brother",
        label="the older brother",
        type="boy",
        motive="He loved snacks and had quick hands.",
        clue="coconut shreds on his sleeve",
        harmless_reason="He was only making a bird feeder from an empty shell.",
        reveal="He had carried the coconut to the porch table to make a bird toy.",
        guilty=True,
    ),
    "neighbor": Suspect(
        id="neighbor",
        label="Mr. Pine, the next-door neighbor",
        type="neighbor",
        motive="He borrowed things and returned them later.",
        clue="a wheelbarrow track",
        harmless_reason="He was moving flower pots, not stealing fruit.",
        reveal="He had borrowed the coconut to fill a game basket for the block party.",
        guilty=True,
    ),
}

SETTINGS_ORDER = list(SETTINGS)
SUSPECT_ORDER = list(SUSPECTS)


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------
class DetectiveWorld:
    def __init__(self, world: World) -> None:
        self.world = world

    def intro(self, hero: Entity, helper: Entity, coconut: Entity) -> None:
        self.world.say(
            f"{hero.id} was a little {hero.type} who loved a good neighborhood mystery."
        )
        self.world.say(
            f"One morning, {hero.pronoun('possessive')} eyes found {coconut.phrase} missing from the porch table."
        )
        helper_word = helper.type
        self.world.say(
            f"{helper.id} padded along beside {hero.pronoun('object')}, and together they looked at the quiet block."
        )
        self.world.facts["setup"] = True

    def gather_clue(self, clue: str, suspect: Suspect) -> None:
        self.world.say(
            f"Near the sidewalk, they found {clue}."
        )
        self.world.facts.setdefault("clues", []).append(clue)
        self.world.facts.setdefault("suspicions", []).append(suspect.id)

    def question_suspect(self, suspect: Suspect) -> None:
        self.world.say(
            f"{suspect.label} seemed like a likely suspect at first, but {suspect.harmless_reason}"
        )

    def reveal(self, hero: Entity, suspect: Suspect, coconut: Entity) -> None:
        self.world.say(
            f"At last, the clues led to the answer: {suspect.label} had the coconut all along."
            if suspect.guilty else
            f"At last, the clues led to the answer: {suspect.label} was not the thief."
        )
        self.world.say(
            f"{suspect.reveal}"
        )
        if suspect.guilty:
            self.world.say(
                f"The coconut was brought back, and {coconut.phrase} sat safely on the porch again."
            )
            hero.memes["relief"] += 1
            hero.memes["joy"] += 1
        else:
            self.world.say(
                f"The neighborhood stayed peaceful, and the missing coconut was found without any blame."
            )
            hero.memes["relief"] += 1

    def ending(self, hero: Entity, coconut: Entity) -> None:
        self.world.say(
            f"By sunset, {hero.id} was smiling at the porch table, and {coconut.phrase} was right where it belonged."
        )


# ---------------------------------------------------------------------------
# Reasonableness and simulation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting in SETTINGS:
        for suspect in SUSPECTS:
            combos.append((setting, suspect))
    return combos


def explain_rejection(setting: str, suspect: str) -> str:
    return f"(No story: the neighborhood setting '{setting}' does not fit the suspect '{suspect}' in this mystery.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "setting", None) and getattr(args, "setting", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "suspect", None) and getattr(args, "suspect", None) not in SUSPECTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None)
              if getattr(args, "suspect", None) is None or c[1] == getattr(args, "suspect", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting, suspect = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    helper_type = getattr(args, "helper_type", None) or rng.choice(HELPER_TYPES)
    hero_name = getattr(args, "hero_name", None) or rng.choice(["Mia", "Leo", "Nora", "Sam", "Zoe", "Ben"])
    coconut_form = getattr(args, "coconut_form", None) or rng.choice(list(COCONUT_FORMS))
    return StoryParams(
        setting=setting,
        coconut_form=coconut_form,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_type=helper_type,
        suspect=suspect,
    )


def generate(params: StoryParams) -> StorySample:
    neighborhood = _safe_lookup(SETTINGS, params.setting)
    world = World(neighborhood)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, memes={"curiosity": 1.0}))
    helper = world.add(Entity(id=params.helper_type.capitalize(), kind="character", type=params.helper_type))
    coconut = world.add(Entity(id="coconut", type="thing", label="coconut", phrase=_safe_lookup(COCONUT_FORMS, params.coconut_form)))
    suspect = _safe_lookup(SUSPECTS, params.suspect)

    dw = DetectiveWorld(world)
    dw.intro(hero, helper, coconut)
    world.para()

    world.say(f"They checked {neighborhood.place} and followed the first little clue.")
    dw.gather_clue(suspect.clue, suspect)
    dw.question_suspect(suspect)
    world.para()

    if suspect.guilty:
        world.say(f"{hero.id} noticed the clue matched the real answer, not just a guess.")
    else:
        world.say(f"{hero.id} noticed the clue did not point to a thief after all.")

    dw.reveal(hero, suspect, coconut)
    dw.ending(hero, coconut)

    world.facts.update(
        hero=hero,
        helper=helper,
        coconut=coconut,
        suspect=suspect,
        setting=neighborhood,
        params=params,
        solved=True,
    )

    story = world.render()
    prompts = generation_prompts(world)
    story_qa = make_story_qa(world)
    world_qa = make_world_qa(world)
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a cozy whodunit for a young child about a missing coconut in the neighborhood.",
        f"Tell a mystery story where {f['hero'].id} follows clues and learns who moved the coconut.",
        f"Write a short neighborhood detective tale with a clear clue, a guess, and a reveal.",
    ]


def make_story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    coconut: Entity = _safe_fact(world, f, "coconut")
    suspect: Suspect = _safe_fact(world, f, "suspect")
    setting: Neighborhood = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"What mystery did {hero.id} try to solve?",
            answer=f"{hero.id} tried to solve the mystery of the missing coconut in {setting.place}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} look for the coconut?",
            answer=f"{helper.id} helped {hero.id} search the neighborhood and follow the clues.",
        ),
        QAItem(
            question=f"What clue pointed toward {suspect.label}?",
            answer=f"The clue was {suspect.clue}, which made {suspect.label} look important at first.",
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"The coconut was found, the mystery was solved, and {coconut.phrase} went back where it belonged.",
        ),
    ]


def make_world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a neighborhood?",
            answer="A neighborhood is a group of nearby homes and streets where people live, walk, and know one another.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks questions, and tries to figure out what really happened.",
        ),
        QAItem(
            question="What is a coconut?",
            answer="A coconut is a round fruit with a hard shell and a white inside.",
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
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(S) :- setting_fact(S).
suspect(X) :- suspect_fact(X).

valid_story(S, X) :- setting(S), suspect(X).

#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for x in SUSPECTS:
        lines.append(asp.fact("suspect_fact", x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy neighborhood whodunit about a missing coconut.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--coconut-form", choices=COCONUT_FORMS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--suspect", choices=SUSPECTS)
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="quiet_block", coconut_form="whole", hero_name="Mia", hero_type="girl", helper_type="cat", suspect="brother"),
    StoryParams(setting="corner_lane", coconut_form="snack", hero_name="Leo", hero_type="boy", helper_type="neighbor", suspect="gardener"),
    StoryParams(setting="porch_row", coconut_form="shaved", hero_name="Nora", hero_type="girl", helper_type="dog", suspect="mail_carrier"),
]


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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible (setting, suspect) combos:")
        for setting, suspect in combos:
            print(f"  {setting:12} {suspect}")
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
                params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.hero_name}: {p.suspect} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
