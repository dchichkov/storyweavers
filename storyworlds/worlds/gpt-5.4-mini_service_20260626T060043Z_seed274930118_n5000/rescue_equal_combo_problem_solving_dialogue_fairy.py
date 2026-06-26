#!/usr/bin/env python3
"""
A fairy-tale storyworld about a small rescue, a fair equal share, and a combo
solution reached through dialogue and problem solving.

Seed tale:
---
A little fairy named Pippa found two young hedgehogs stuck on opposite sides of a
shallow stream. One wanted the shiny acorn boat, and the other wanted the soft
moss raft. Pippa knew only one safe rescue would work: an equal combo of both
boats tied together with a reed rope, so both hedgehogs could cross at once
without either feeling left out. She asked them to talk it through, and together
they chose the combo plan. The stream was crossed, both were rescued, and each
hedgehog smiled because the rescue was equal.
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
# World model
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    helper_a: object | None = None
    helper_b: object | None = None
    hero: object | None = None
    item_a: object | None = None
    item_b: object | None = None
    rope: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fairy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"hedgehog"}:
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
    water: bool = False
    safe_bank: bool = True
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
class RescueTarget:
    label: str
    phrase: str
    kind: str
    side: str
    needs: str
    gender_ok: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Combo:
    id: str
    label: str
    pieces: list[str]
    effect: str
    dialogue_offer: str
    ending: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace_log: list[str] = []

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
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "brook": Place(name="the silver brook", water=True, safe_bank=True),
    "glade": Place(name="the moonlit glade", water=False, safe_bank=True),
    "garden": Place(name="the old rose garden", water=True, safe_bank=True),
}

TARGETS = {
    "hedgehog_pair": RescueTarget(
        label="hedgehogs",
        phrase="two tiny hedgehogs",
        kind="hedgehog",
        side="both banks",
        needs="a safe crossing",
        gender_ok={"girl", "boy"},
    ),
}

COMBOS = {
    "boat_raft": Combo(
        id="boat_raft",
        label="acorn-boat and moss-raft combo",
        pieces=["acorn boat", "moss raft"],
        effect="two little rides tied into one steady rescue",
        dialogue_offer="one boat for each side, joined by a reed rope",
        ending="both boats bobbed together like a single happy cradle",
    ),
    "lantern_bridge": Combo(
        id="lantern_bridge",
        label="lantern-and-bridge combo",
        pieces=["glow lantern", "pale twig bridge"],
        effect="light and a steady path working together",
        dialogue_offer="a lantern to light the way and a bridge to steady the feet",
        ending="the bridge shone softly under the lantern light",
    ),
}

GIRL_NAMES = ["Pippa", "Mira", "Luna", "Faye", "Nora"]
BOY_NAMES = ["Tobin", "Elio", "Robin", "Bram", "Otis"]
TRAITS = ["kind", "brave", "gentle", "curious", "wise"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    target: str
    combo: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
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


def story_seed_words() -> list[str]:
    return ["rescue", "equal", "combo"]


def valid_combo(place: Place, target: RescueTarget, combo: Combo) -> bool:
    if place.name not in {"the silver brook", "the old rose garden", "the moonlit glade"}:
        return False
    if target.kind != "hedgehog":
        return False
    return combo.id in COMBOS


def explain_invalid(combo: Combo) -> str:
    return (
        f"(No story: the {combo.label} does not fit this rescue. "
        f"The tale needs a real equal combo that can carry both hedgehogs safely.)"
    )


def human_join(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    target = _safe_lookup(TARGETS, params.target)
    combo = _safe_lookup(COMBOS, params.combo)
    world = World(place)

    hero = world.add(Entity(id=params.name, kind="character", type="fairy", label=params.name))
    helper_a = world.add(Entity(id="helper_a", kind="character", type="hedgehog", label="Milo"))
    helper_b = world.add(Entity(id="helper_b", kind="character", type="hedgehog", label="Nia"))
    rope = world.add(Entity(id="rope", kind="thing", type="rope", label="reed rope"))
    item_a = world.add(Entity(id="item_a", kind="thing", type="boat", label=combo.pieces[0], carried_by=helper_a.id))
    item_b = world.add(Entity(id="item_b", kind="thing", type="boat", label=combo.pieces[1], carried_by=helper_b.id))

    helper_a.memes["worried"] = 1
    helper_b.memes["worried"] = 1
    world.facts.update(hero=hero, helper_a=helper_a, helper_b=helper_b, combo=combo, target=target)

    # Setup
    world.say(
        f"Once upon a time, {hero.id} was a {params.trait} fairy who wandered to {place.name}."
    )
    world.say(
        f"There {target.phrase} stood on opposite banks, each needing {target.needs}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved a fair rescue, and {target.label} were already asking for help."
    )

    # Problem
    world.para()
    world.say(
        f'"We each want a safe way across," said Milo. "But we do not want the other left behind."'
    )
    world.say(
        f'"Then we need an equal answer," said Nia, looking at {hero.id}.'
    )
    world.say(
        f"{hero.id} looked at the brook, then at the two little boats, and thought carefully."
    )

    # Solution
    world.para()
    world.say(
        f'"What if we make a {combo.label}?" {hero.id} asked. "{combo.dialogue_offer}."'
    )
    world.say(
        f'"Would that be fair?" asked Milo.'
        f'"Yes," said {hero.id}. "It would rescue you both at once, and the rescue would be equal."'
    )
    world.say(
        f'The hedgehogs nodded, because the plan was a kind combo of both ideas, not just one.'
    )

    # Resolution
    world.para()
    helper_a.carried_by = hero.id
    helper_b.carried_by = hero.id
    rope.carried_by = hero.id
    helper_a.memes["safe"] = 1
    helper_b.memes["safe"] = 1
    world.facts["resolved"] = True
    world.say(
        f"{hero.id} tied {item_a.label} and {item_b.label} with {rope.label}, then set them together on the water."
    )
    world.say(
        f"The {combo.ending}, and the hedgehogs crossed side by side, rescued at last."
    )
    world.say(
        f"When they reached the far bank, each hedgehog smiled because the help had been equal, and nobody was left out."
    )

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    combo = _safe_fact(world, f, "combo")
    return [
        f'Write a fairy-tale story for a young child that includes the words "rescue", "equal", and "combo".',
        f"Tell a gentle story where {hero.id} solves a rescue problem with a clever equal combo and a bit of dialogue.",
        f"Write a short fairy tale about helping two creatures cross safely by choosing a combo plan that feels fair.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    combo = _safe_fact(world, f, "combo")
    return [
        QAItem(
            question=f"Who came up with the rescue plan in the story?",
            answer=f"{hero.id} came up with the rescue plan after thinking about what would be fair for both hedgehogs.",
        ),
        QAItem(
            question=f"What made the plan equal?",
            answer=f"The plan was equal because it used both parts of the {combo.label} so each hedgehog was helped at the same time.",
        ),
        QAItem(
            question=f"Why did the hedgehogs agree to the combo?",
            answer=f"They agreed because the combo solved their crossing problem without leaving either one behind.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rescue?",
            answer="A rescue is when someone helps another creature get out of danger or trouble.",
        ),
        QAItem(
            question="What does equal mean?",
            answer="Equal means the same amount or the same kind of fair treatment for everyone involved.",
        ),
        QAItem(
            question="What is a combo?",
            answer="A combo is a mix of two or more things that work together as one helpful plan.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place_ok(P) :- place(P).
target_ok(T) :- target(T).
combo_ok(C) :- combo(C).

valid_story(P, T, C) :- place_ok(P), target_ok(T), combo_ok(C), rescue_fit(P, T, C).

rescue_fit(P, T, C) :- place(P), target(T), combo(C), combo_piece(C, _), target_kind(T, hedgehog).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.water:
            lines.append(asp.fact("water_place", pid))
        if place.safe_bank:
            lines.append(asp.fact("safe_bank", pid))
    for tid, target in TARGETS.items():
        lines.append(asp.fact("target", tid))
        lines.append(asp.fact("target_kind", tid, target.kind))
    for cid, combo in COMBOS.items():
        lines.append(asp.fact("combo", cid))
        for piece in combo.pieces:
            lines.append(asp.fact("combo_piece", cid, piece))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid_combos() -> list[tuple]:
    out = []
    for pid, place in PLACES.items():
        for tid, target in TARGETS.items():
            for cid, combo in COMBOS.items():
                if valid_combo(place, target, combo):
                    out.append((pid, tid, cid))
    return sorted(out)


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(python_valid_combos())
    if a == b:
        print(f"OK: clingo gate matches python gate ({len(a)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if a - b:
        print("  only in ASP:", sorted(a - b))
    if b - a:
        print("  only in Python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale rescue world with equal combo problem solving and dialogue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--combo", choices=COMBOS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "combo", None) and getattr(args, "combo", None) not in COMBOS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place_id = getattr(args, "place", None) or rng.choice(list(PLACES))
    target_id = getattr(args, "target", None) or "hedgehog_pair"
    combo_id = getattr(args, "combo", None) or rng.choice(list(COMBOS))
    place = _safe_lookup(PLACES, place_id)
    target = _safe_lookup(TARGETS, target_id)
    combo = _safe_lookup(COMBOS, combo_id)
    if not valid_combo(place, target, combo):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if gender not in target.gender_ok:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place_id, target=target_id, combo=combo_id, name=name, gender=gender, trait=trait)


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="brook", target="hedgehog_pair", combo="boat_raft", name="Pippa", gender="girl", trait="kind"),
    StoryParams(place="garden", target="hedgehog_pair", combo="lantern_bridge", name="Tobin", gender="boy", trait="wise"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} valid stories:")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            i += 1
            seed = base_seed + i
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
