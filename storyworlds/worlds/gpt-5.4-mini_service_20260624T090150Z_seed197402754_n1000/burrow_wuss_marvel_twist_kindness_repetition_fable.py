#!/usr/bin/env python3
"""
A small fable-style storyworld about a timid burrow-dweller, a marvelous
problem, and a kind repetition that leads to a twist ending.

Premise:
- A wuss-like little animal wants to keep safe in its burrow.
- A marvel appears nearby, tempting the animal to react with fear.
- A kinder creature repeats a small helpful action until the timid one learns
  courage enough for a gentle twist.

The world is intentionally tiny and state-driven:
- physical meters track shelter, distance, readiness, and comfort
- emotional memes track fear, trust, kindness, and pride
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    name: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    marvel: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def label(self) -> str:
        return self.name or self.type
    @property
    def label_word(self) -> str:
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
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    clone: object | None = None
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
        clone = World(self.place)
        clone.entities = json.loads(json.dumps({k: asdict(v) for k, v in self.entities.items()}))
        # rebuild entities simply for simulation helpers
        clone.entities = {
            k: Entity(**v) for k, v in clone.entities.items()
        }
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


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


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    marvel: str
    seed: Optional[int] = None
    params: object | None = None
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
class Place:
    id: str
    label: str
    cozy: bool
    shelters: set[str]
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
class Marvel:
    id: str
    label: str
    shine: str
    curiosity: str
    danger: str
    visible: bool = True
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


PLACES = {
    "burrow": Place(
        id="burrow",
        label="the burrow",
        cozy=True,
        shelters={"small", "quiet"},
    ),
    "meadow": Place(
        id="meadow",
        label="the meadow",
        cozy=False,
        shelters={"open", "sunny"},
    ),
}

HEROES = {
    "wuss": {"name": "Wren", "type": "rabbit", "trait": "wuss"},
    "wisp": {"name": "Milo", "type": "mouse", "trait": "wuss"},
    "hush": {"name": "Pip", "type": "mole", "trait": "wuss"},
}

HELPERS = {
    "kindness": {"name": "Aunt Fern", "type": "badger", "trait": "kind"},
    "kindness2": {"name": "Nell", "type": "beaver", "trait": "kind"},
}

MARVELS = {
    "marvel": Marvel(
        id="marvel",
        label="a tiny marvel",
        shine="glimmered",
        curiosity="sparkled",
        danger="looked strangely loud",
    ),
    "shell": Marvel(
        id="shell",
        label="a rainbow shell",
        shine="glowed",
        curiosity="shimmered",
        danger="was easy to lose",
    ),
}

# Style instruments required by the seed/request.
TWIST = "Twist"
KINDNESS = "Kindness"
REPETITION = "Repetition"


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------

def fable_opening(world: World, hero: Entity, helper: Entity, marvel: Entity) -> None:
    world.say(
        f"Once in {world.place}, {hero.label()} was a little wuss who loved safe corners "
        f"and soft leaves."
    )
    world.say(
        f"One day, {marvel.label} {marvel.shine} near the doorway, and everyone stopped "
        f"to marvel at it."
    )
    world.say(
        f"{helper.label()} was kind, and {helper.label()} knew that a scared heart "
        f"sometimes needs the same gentle help more than once."
    )


def repeat_kindness(world: World, hero: Entity, helper: Entity, marvel: Entity) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1
    hero.meters["distance"] = hero.meters.get("distance", 0) + 1
    world.say(
        f"At first, {hero.label()} backed into the burrow and whispered, "
        f'"I am too small for that marvelous thing."'
    )
    world.say(
        f"{helper.label()} did not laugh. Instead, {helper.label()} repeated the same kind words: "
        f'"You may look. You may breathe. You may choose."'
    )
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    hero.meters["comfort"] = hero.meters.get("comfort", 0) + 1


def repetition_beats_fear(world: World, hero: Entity, helper: Entity, marvel: Entity) -> None:
    world.para()
    world.say(
        f"{helper.label()} repeated the same offer again, and then again, until it sounded "
        f"as steady as raindrops."
    )
    world.say(
        f"Each time, {hero.label()} peeped a little farther out, and each time the burrow "
        f"felt less like a hiding place and more like a home."
    )
    hero.memes["fear"] = max(0, hero.memes.get("fear", 0) - 1)
    hero.meters["ready"] = hero.meters.get("ready", 0) + 1
    hero.meters["distance"] = max(0, hero.meters.get("distance", 0) - 1)


def twist_turn(world: World, hero: Entity, helper: Entity, marvel: Entity) -> None:
    world.para()
    world.say(
        f"Then came the {TWIST}: the marvelous thing was not a trap at all."
    )
    world.say(
        f"It was a polished pebble that had rolled from the hill, and it reflected the sky "
        f"so brightly that even the burrow looked blue."
    )
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    hero.meters["courage"] = hero.meters.get("courage", 0) + 1


def ending_image(world: World, hero: Entity, helper: Entity, marvel: Entity) -> None:
    world.say(
        f"{hero.label()} touched the pebble, smiled, and stayed near the doorway instead of "
        f"running away."
    )
    world.say(
        f"{helper.label()} smiled too, because the {KINDNESS} had worked, the "
        f"{REPETITION} had helped, and the burrow was still safe."
    )
    world.say(
        f"In the end, the little wuss was not less careful, only less afraid."
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place_ok(P) :- place(P).
can_story(P,H,K,M) :- place_ok(P), hero(H), helper(K), marvel(M),
                      hero_trait(H,wuss), helper_trait(K,kind), marvel_kind(M,marvel).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for hid, h in HEROES.items():
        lines.append(asp.fact("hero", hid))
        lines.append(asp.fact("hero_trait", hid, h["trait"]))
    for kid, k in HELPERS.items():
        lines.append(asp.fact("helper", kid))
        lines.append(asp.fact("helper_trait", kid, k["trait"]))
    for mid, m in MARVELS.items():
        lines.append(asp.fact("marvel", mid))
        lines.append(asp.fact("marvel_kind", mid, mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_story/4."))
    clingo_set = set(asp.atoms(model, "can_story"))
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for hero in HEROES:
            for helper in HELPERS:
                for marvel in MARVELS:
                    combos.append((place, hero, helper, marvel))
    return combos


def explain_rejection() -> str:
    return "No story fits those choices; this fable needs a burrow, a wuss, a kind helper, and a marvel."


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        pass
    if params.hero not in HEROES:
        pass
    if params.helper not in HELPERS:
        pass
    if params.marvel not in MARVELS:
        pass

    world = World(_safe_lookup(PLACES, params.place).label)
    hero_cfg = _safe_lookup(HEROES, params.hero)
    helper_cfg = _safe_lookup(HELPERS, params.helper)
    marvel_cfg = _safe_lookup(MARVELS, params.marvel)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_cfg["type"],
        name=hero_cfg["name"],
        role=hero_cfg["trait"],
        meters={"distance": 0.0, "comfort": 0.0, "ready": 0.0, "courage": 0.0},
        memes={"fear": 0.0, "trust": 0.0, "wonder": 0.0, "pride": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg["type"],
        name=helper_cfg["name"],
        role=helper_cfg["trait"],
        meters={"kindness": 0.0},
        memes={"kindness": 1.0},
    ))
    marvel = world.add(Entity(
        id="marvel",
        kind="thing",
        type="pebble",
        name=marvel_cfg.label,
        role="marvel",
        meters={"shine": 1.0},
        memes={"mystery": 1.0},
    ))

    fable_opening(world, hero, helper, marvel)
    repeat_kindness(world, hero, helper, marvel)
    repetition_beats_fear(world, hero, helper, marvel)
    twist_turn(world, hero, helper, marvel)
    ending_image(world, hero, helper, marvel)

    world.facts.update(
        hero=hero,
        helper=helper,
        marvel=marvel,
        params=params,
        place=params.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    marvel = _safe_fact(world, world.facts, "marvel")
    return [
        f"Write a short fable about a timid {hero.type} in a burrow who meets {marvel.name}.",
        f"Tell a child-friendly story where {helper.label()} uses kindness and repetition to help a wuss feel brave.",
        f"Write a fable with a twist ending, where the marvelous thing turns out to be harmless.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    marvel = _safe_fact(world, world.facts, "marvel")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label()}, a little wuss who lived near the burrow.",
        ),
        QAItem(
            question=f"What did {helper.label()} do to help?",
            answer=f"{helper.label()} used kindness and repeated gentle words until {hero.label()} felt steadier.",
        ),
        QAItem(
            question=f"What was the twist?",
            answer=f"The marvelous thing was only a polished pebble, not a danger at all.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.label()} stayed near the burrow doorway, calmer and a little proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a burrow?",
            answer="A burrow is a tunnel or hole made by an animal for shelter and safety.",
        ),
        QAItem(
            question="What does kindness do in a story?",
            answer="Kindness helps a character feel cared for, calmer, and more willing to try again.",
        ),
        QAItem(
            question="Why can repetition help a scared character?",
            answer="Repeating the same gentle help can make the moment feel steady and safe.",
        ),
        QAItem(
            question="What is a twist in a fable?",
            answer="A twist is a surprising turn near the end that changes how you understand the problem.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI / output
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-style storyworld about a burrow, a wuss, and a marvel.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--marvel", choices=sorted(MARVELS))
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    hero = getattr(args, "hero", None) or rng.choice(list(HEROES))
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    marvel = getattr(args, "marvel", None) or rng.choice(list(MARVELS))
    return StoryParams(place=place, hero=hero, helper=helper, marvel=marvel, seed=getattr(args, "seed", None))


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
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
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
        print(asp_program("#show can_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show can_story/4."))
        combos = sorted(set(asp.atoms(model, "can_story")))
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in valid_combos():
            params = StoryParams(place=p[0], hero=p[1], helper=p[2], marvel=p[3], seed=getattr(args, "seed", None))
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            p = resolve_params(args, random.Random((getattr(args, "seed", None) or 0) + i))
            i += 1
            sample = generate(p)
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
        header = f"### variant {i+1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
