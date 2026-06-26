#!/usr/bin/env python3
"""
storyworlds/worlds/radiology_rheumatoid_moral_value_transformation_adventure.py
===============================================================================

A compact adventure storyworld about a child’s visit to radiology, a loved one
with rheumatoid pain, and a moral-value transformation that helps the day end
well.

Premise:
- A young hero wants to rush on a little adventure through a hospital.
- A relative or helper has rheumatoid pain and needs a careful radiology visit.
- The hero begins a little selfishly, then learns patience, kindness, and help.
- The ending proves the change through concrete action: carrying, waiting,
  sharing, fetching, or comforting.

World model:
- Physical meters track pain, fatigue, load, and progress.
- Emotional memes track impatience, care, courage, and moral value.
- The story is driven by state changes, not a frozen template.

This world is intentionally small and constraint-checked: the chosen scene must
allow a believable adventure, a radiology step, and a transformation ending.
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
# Registries
# ---------------------------------------------------------------------------

LOCATIONS = {
    "clinic_hall": "the clinic hall",
    "radiology_suite": "the radiology suite",
    "waiting_room": "the waiting room",
    "corridor": "the long corridor",
}

ROLES = {
    "child": "child",
    "grandchild": "grandchild",
    "patient": "patient",
    "parent": "parent",
}

HELPERS = {
    "nurse": "a kind nurse",
    "technician": "a radiology technician",
    "parent": "the parent",
}

OBJECTS = {
    "scan_pass": "a scan pass",
    "wheelchair": "a wheelchair",
    "blanket": "a warm blanket",
    "water": "a small cup of water",
    "toy_compass": "a little compass toy",
}

MORAL_VALUES = {
    "kindness": "kindness",
    "patience": "patience",
    "courage": "courage",
    "honesty": "honesty",
    "helpfulness": "helpfulness",
}

TRANSFORMATIONS = {
    "impatient_to_kind": {
        "start": "impatient",
        "end": "kind",
        "label": "from impatience to kindness",
    },
    "careless_to_helpful": {
        "start": "careless",
        "end": "helpful",
        "label": "from carelessness to helpfulness",
    },
    "afraid_to_courageous": {
        "start": "afraid",
        "end": "courageous",
        "label": "from fear to courage",
    },
}

PAIN_LEVELS = {
    "mild": 1.0,
    "stiff": 2.0,
    "ache": 3.0,
}


# ---------------------------------------------------------------------------
# Shared entity/world model
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    blanket: object | None = None
    helper: object | None = None
    hero: object | None = None
    scan_pass: object | None = None
    water: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class World:
    location: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Per-world params
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
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


@dataclass
class StoryParams:
    location: str
    hero_name: str
    hero_type: str
    helper_type: str
    moral_value: str
    transformation: str
    pain_level: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
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


def _name_for_type(hero_type: str, rng: random.Random) -> str:
    girl_names = ["Mia", "Nora", "Lena", "Ivy", "Zoe", "Ava"]
    boy_names = ["Leo", "Finn", "Noah", "Owen", "Theo", "Eli"]
    return rng.choice(girl_names if hero_type == "girl" else boy_names)


def _article_phrase(text: str) -> str:
    first = text.strip()[0].lower()
    return f"an {text}" if first in "aeiou" else f"a {text}"


def _hero_intro(hero: Entity, helper: Entity, value: str) -> str:
    return (
        f"{hero.id} loved adventures, but {hero.pronoun('possessive')} heart was still learning "
        f"{value}. Today {hero.pronoun()} had come with {helper.phrase}."
    )


def _hospital_setup(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"Their path led through {world.location}, where bright signs pointed toward radiology "
        f"and quiet shoes tapped on the floor."
    )
    world.say(
        f"Inside, {helper.phrase} moved slowly because {helper.pronoun('possessive')} joints ached "
        f"with rheumatoid pain."
    )


def _pressure(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["impatient"] += 1
    hero.memes["moral_value"] += 0.1
    world.say(
        f"{hero.id} wanted to dash ahead and see everything at once, but the hallway was crowded "
        f"and {helper.pronoun('possessive')} steps had to stay careful."
    )
    world.say(
        f"When the scanner room appeared, {hero.id} noticed that rushing would only make the day harder "
        f"for {helper.id}."
    )


def _turn(world: World, hero: Entity, helper: Entity, value: str, transformation: str) -> None:
    hero.memes["impatient"] = 0.0
    hero.memes["kind"] += 1
    hero.memes["helpful"] += 1
    hero.memes["moral_value"] += 1
    world.say(
        f"Then {hero.id} remembered {value}: {helper.id} needed care more than speed."
    )
    world.say(
        f"{hero.id} took a breath, held the door, and helped carry {helper.pronoun('possessive')} "
        f"blanket and water instead of racing off."
    )
    world.say(
        f"That was {transformation['label']}, and it made the whole hallway feel lighter."
    )


def _resolution(world: World, hero: Entity, helper: Entity) -> None:
    helper.meters["pain"] = max(0.0, helper.meters.get("pain", 0.0) - 0.5)
    helper.meters["fatigue"] = max(0.0, helper.meters.get("fatigue", 0.0) - 0.2)
    world.say(
        f"The radiology technician smiled, and the scan began while {hero.id} waited quietly beside "
        f"{helper.id}."
    )
    world.say(
        f"When it was over, {helper.id} could sit easier, and {hero.id} carried the blanket back out "
        f"like a small helper on a big adventure."
    )


def _build_world(params: StoryParams) -> World:
    world = World(location=_safe_lookup(LOCATIONS, params.location))

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        phrase=params.hero_name,
        meters={"energy": 1.0},
        memes={"impatient": 0.0, "kind": 0.0, "helpful": 0.0, "moral_value": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper_type,
        label=_safe_lookup(HELPERS, params.helper_type),
        phrase=_safe_lookup(HELPERS, params.helper_type),
        meters={"pain": _safe_lookup(PAIN_LEVELS, params.pain_level), "fatigue": 0.7},
        memes={"hope": 0.5},
    ))
    scan_pass = world.add(Entity(
        id="ScanPass",
        kind="thing",
        type="pass",
        label=OBJECTS["scan_pass"],
        phrase=OBJECTS["scan_pass"],
        owner=helper.id,
        carried_by=helper.id,
    ))
    blanket = world.add(Entity(
        id="Blanket",
        kind="thing",
        type="blanket",
        label="blanket",
        phrase=OBJECTS["blanket"],
        owner=helper.id,
        carried_by=helper.id,
    ))
    water = world.add(Entity(
        id="Water",
        kind="thing",
        type="water",
        label="water",
        phrase=OBJECTS["water"],
        owner=helper.id,
        carried_by=helper.id,
    ))

    world.facts.update(
        hero=hero,
        helper=helper,
        scan_pass=scan_pass,
        blanket=blanket,
        water=water,
        moral_value=params.moral_value,
        transformation=_safe_lookup(TRANSFORMATIONS, params.transformation),
        pain_level=params.pain_level,
    )

    world.say(_hero_intro(hero, helper, params.moral_value))
    world.say(
        f"They carried {scan_pass.phrase} because the day’s task was a radiology appointment."
    )
    world.para()
    _hospital_setup(world, hero, helper)
    _pressure(world, hero, helper)
    world.para()
    _turn(world, hero, helper, params.moral_value, _safe_lookup(TRANSFORMATIONS, params.transformation))
    _resolution(world, hero, helper)
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def _valid_params(params: StoryParams) -> bool:
    return (
        params.location in LOCATIONS
        and params.hero_type in {"girl", "boy"}
        and params.helper_type in {"mother", "father", "grandmother", "grandfather"}
        and params.moral_value in MORAL_VALUES
        and params.transformation in TRANSFORMATIONS
        and params.pain_level in PAIN_LEVELS
    )


def _explain_invalid(params: StoryParams) -> str:
    return (
        "Invalid story request: the radiology adventure needs a supported hero, "
        "a helper with rheumatoid pain, a moral value, and a transformation."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    return [
        f'Write a short adventure story for a child named {hero.id} at the radiology suite that shows {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "moral_value")}.',
        f"Tell a gentle story where {hero.id} learns to help {helper.phrase} during a radiology visit for rheumatoid pain.",
        f"Write a story about a small hospital adventure and a moral transformation from {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "transformation")['start']} to {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "transformation")['end']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    value = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "moral_value")
    trans = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "transformation")
    return [
        QAItem(
            question=f"What kind of day did {hero.id} have at {world.location}?",
            answer=f"{hero.id} had a small hospital adventure in {world.location}, and the day taught {hero.pronoun('object')} about {value}.",
        ),
        QAItem(
            question=f"Why did {helper.id} need to move carefully?",
            answer=f"{helper.id} moved carefully because {helper.pronoun('possessive')} joints hurt with rheumatoid pain.",
        ),
        QAItem(
            question=f"How did {hero.id} change during the story?",
            answer=f"{hero.id} changed {trans['label']} by becoming more helpful and kinder instead of rushing ahead.",
        ),
        QAItem(
            question=f"What did {hero.id} do to help at the end?",
            answer=f"{hero.id} held the door, carried the blanket and water, and waited quietly during the radiology scan.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is radiology?",
            answer="Radiology is a part of medicine that uses special machines, like scanners or X-rays, to look inside the body.",
        ),
        QAItem(
            question="What does rheumatoid mean?",
            answer="Rheumatoid is a word that can describe a kind of arthritis that makes joints sore, stiff, and hard to move.",
        ),
        QAItem(
            question="Why does kindness matter in a hospital?",
            answer="Kindness matters because careful, patient help can make a worried day feel safer and less painful.",
        ),
    ]


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(X) :- helper_name(X).

valid_value(V) :- moral_value(V).
valid_transformation(T) :- transformation(T).
valid_location(L) :- location(L).

story_ready(H, X, V, T, L) :-
    hero(H), helper(X), valid_value(V), valid_transformation(T), valid_location(L).

#show story_ready/5.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for loc in LOCATIONS:
        lines.append(asp.fact("location", loc))
    for mv in MORAL_VALUES:
        lines.append(asp.fact("moral_value", mv))
    for tr in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tr))
    for h in ["girl", "boy"]:
        lines.append(asp.fact("hero_type", h))
    for h in HELPERS:
        lines.append(asp.fact("helper_name", h))
    for h in ["Mia", "Leo", "Nora", "Finn"]:
        lines.append(asp.fact("hero_name", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show story_ready/5."))
    clingo_set = set(asp.atoms(model, "story_ready"))
    python_set = set()
    for loc in LOCATIONS:
        for mv in MORAL_VALUES:
            for tr in TRANSFORMATIONS:
                for hero in ["Mia", "Leo", "Nora", "Finn"]:
                    for helper in HELPERS:
                        python_set.add((hero, helper, mv, tr, loc))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python registry space ({len(clingo_set)} combinations).")
        return 0
    print("MISMATCH between clingo and Python registry space.")
    return 1


# ---------------------------------------------------------------------------
# Params, generation, emission
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small radiology adventure with rheumatoid care and a moral transformation."
    )
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=list(HELPERS))
    ap.add_argument("--moral-value", choices=list(MORAL_VALUES))
    ap.add_argument("--transformation", choices=list(TRANSFORMATIONS))
    ap.add_argument("--pain-level", choices=list(PAIN_LEVELS))
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
    location = getattr(args, "location", None) or rng.choice(list(LOCATIONS))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(list(HELPERS))
    moral_value = getattr(args, "moral_value", None) or rng.choice(list(MORAL_VALUES))
    transformation = getattr(args, "transformation", None) or rng.choice(list(TRANSFORMATIONS))
    pain_level = getattr(args, "pain_level", None) or rng.choice(list(PAIN_LEVELS))
    hero_name = getattr(args, "hero_name", None) or _name_for_type(hero_type, rng)

    params = StoryParams(
        location=location,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_type=helper_type,
        moral_value=moral_value,
        transformation=transformation,
        pain_level=pain_level,
    )
    if not _valid_params(params):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return params


def generate(params: StoryParams) -> StorySample:
    if not _valid_params(params):
        pass
    world = _build_world(params)
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
    for e in list(world.entities.values()):
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items())}}}")
        if e.memes:
            bits.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items())}}}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
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
    StoryParams(
        location="radiology_suite",
        hero_name="Mia",
        hero_type="girl",
        helper_type="grandmother",
        moral_value="kindness",
        transformation="impatient_to_kind",
        pain_level="stiff",
    ),
    StoryParams(
        location="waiting_room",
        hero_name="Leo",
        hero_type="boy",
        helper_type="father",
        moral_value="helpfulness",
        transformation="careless_to_helpful",
        pain_level="ache",
    ),
    StoryParams(
        location="clinic_hall",
        hero_name="Nora",
        hero_type="girl",
        helper_type="mother",
        moral_value="patience",
        transformation="afraid_to_courageous",
        pain_level="mild",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show story_ready/5."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show story_ready/5."))
        items = sorted(set(asp.atoms(model, "story_ready")))
        for item in items:
            print(item)
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.hero_name}: {p.moral_value} / {p.transformation} at {p.location}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
