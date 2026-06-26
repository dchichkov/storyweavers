#!/usr/bin/env python3
"""
storyworlds/worlds/loud_flashback_mystery.py
===========================================

A small mystery storyworld with a loud clue and a flashback turn.

Premise:
- A child notices something missing or out of place.
- A loud sound or shout reveals a clue.
- A flashback explains how an earlier event caused the mystery.
- The ending proves what changed and what was found or fixed.

The world keeps a lightweight simulation of:
- physical state: location, object positions, sounds, hidden evidence
- emotional state: worry, curiosity, relief, trust

The prose is generated from the simulated state, not from a frozen template.
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
# Registry data
# ---------------------------------------------------------------------------

PLACES = {
    "attic": "the attic",
    "kitchen": "the kitchen",
    "garden": "the garden",
    "library": "the library",
    "garage": "the garage",
    "hallway": "the hallway",
}

HERO_NAMES = ["Mia", "Noah", "Lena", "Owen", "Rosa", "Finn", "Ava", "Theo"]
ADULT_NAMES = ["Mom", "Dad", "Grandma", "Grandpa", "Aunt June", "Uncle Ben"]

MYSTERY_OBJECTS = {
    "key": {
        "label": "key",
        "phrase": "a tiny brass key",
        "hide_spot": "under the rug",
        "find_spot": "on the shelf",
    },
    "cookie": {
        "label": "cookie",
        "phrase": "the last chocolate cookie",
        "hide_spot": "inside the blue jar",
        "find_spot": "in the toy box",
    },
    "note": {
        "label": "note",
        "phrase": "a folded note",
        "hide_spot": "behind the lamp",
        "find_spot": "inside the storybook",
    },
    "shell": {
        "label": "shell",
        "phrase": "a smooth white shell",
        "hide_spot": "in the flower pot",
        "find_spot": "beneath the cushion",
    },
    "button": {
        "label": "button",
        "phrase": "a shiny red button",
        "hide_spot": "behind the toolbox",
        "find_spot": "in the coat pocket",
    },
}

SOUNDS = [
    "a loud bang",
    "a loud clatter",
    "a loud thump",
    "a loud squeak",
    "a loud shout",
    "a loud crash",
]

FLASHBACK_TRIGGERS = [
    "the open window",
    "the tipped chair",
    "the dusty footprint",
    "the crumb trail",
    "the crooked drawer",
    "the half-closed door",
]

HUNCHES = [
    "Something had been moved in a hurry.",
    "Someone had been there before the others came in.",
    "The room was telling a secret.",
    "That noise did not belong to an ordinary afternoon.",
]

RESOLUTIONS = [
    "It was tucked away safely all along.",
    "It had only fallen behind something heavy.",
    "It was hidden by accident during a quick cleanup.",
    "It had been waiting in the wrong room.",
]


# ---------------------------------------------------------------------------
# Core model
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
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden_in: Optional[str] = None
    found_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    hero: object | None = None
    obj: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.id in {"Mom", "Grandma", "Aunt June"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.id in {"Dad", "Grandpa", "Uncle Ben"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class StoryParams:
    place: str
    object_id: str
    hero_name: str
    adult_name: str
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
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    flashback: bool = False
    loud_sound: str = ""
    clue: str = ""

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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.flashback = self.flashback
        clone.loud_sound = self.loud_sound
        clone.clue = self.clue
        return clone


# ---------------------------------------------------------------------------
# Reasoning / simulation
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


def _step_search(world: World) -> None:
    hero = world.get("hero")
    obj = world.get("object")
    adult = world.get("adult")

    if "search_started" in world.fired:
        return
    world.fired.add("search_started")

    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0

    world.say(
        f"{hero.id} looked around {world.place} and felt a small knot of worry. "
        f"{hero.pronoun().capitalize()} could not find {obj.phrase}."
    )
    world.say(
        f'"Where did it go?" {hero.id} asked {adult.id}, but nobody knew yet.'
    )


def _step_loud_clue(world: World) -> None:
    if "loud_clue" in world.fired:
        return
    world.fired.add("loud_clue")

    hero = world.get("hero")
    obj = world.get("object")

    world.loud_sound = random.choice(SOUNDS)
    world.clue = random.choice(FLASHBACK_TRIGGERS)

    hero.memes["alert"] = hero.memes.get("alert", 0.0) + 1.0

    world.say(
        f"Then there was {world.loud_sound} from the other side of the room, "
        f"and everyone turned at once."
    )
    world.say(
        f"{hero.id} noticed {world.clue}, and that made the missing {obj.label} feel less mysterious."
    )


def _step_flashback(world: World) -> None:
    if "flashback" in world.fired:
        return
    world.fired.add("flashback")

    hero = world.get("hero")
    obj = world.get("object")
    adult = world.get("adult")

    world.flashback = True
    obj.hidden_in = obj.hidden_in or obj.phrase

    world.say(
        f"For a moment, {hero.id} remembered something from earlier: "
        f"{adult.id} had carried {obj.phrase} into {world.place} and set it down in a hurry."
    )
    world.say(
        f"The memory came back like a little movie in {hero.pronoun('possessive')} head, "
        f"and the loud clue finally made sense."
    )


def _step_find(world: World) -> None:
    if "found" in world.fired:
        return
    world.fired.add("found")

    hero = world.get("hero")
    obj = world.get("object")
    adult = world.get("adult")

    obj.hidden_in = None
    obj.found_by = hero.id
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
    adult.memes["relief"] = adult.memes.get("relief", 0.0) + 1.0

    resolution = random.choice(RESOLUTIONS)
    world.say(
        f"{hero.id} followed the clue to {obj.find_spot} and found {obj.phrase}. "
        f"{resolution}"
    )
    world.say(
        f"{adult.id} smiled, and the room felt calm again."
    )


def propagate(world: World) -> None:
    _step_search(world)
    _step_loud_clue(world)
    _step_flashback(world)
    _step_find(world)


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def intro_line(hero: Entity, adult: Entity, obj: Entity, place: str) -> str:
    return (
        f"One afternoon, {hero.id} and {adult.id} were in {place} when {obj.phrase} went missing."
    )


def mystery_line(hero: Entity, obj: Entity) -> str:
    return (
        f"{hero.id} searched every corner, because {hero.pronoun('possessive')} {obj.label} had vanished."
    )


def ending_line(hero: Entity, adult: Entity, obj: Entity) -> str:
    return (
        f"By the end, {hero.id} was holding {obj.phrase}, and {adult.id} was laughing softly beside {hero.pronoun('object')}."
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- room(P).
object(O) :- mystery_object(O).
loud_clue(O) :- loud(O).
flashback(O) :- clue(O), remembered(O).
found(O) :- flashback(O), hidden(O).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("room", pid))
    for oid in MYSTERY_OBJECTS:
        lines.append(asp.fact("mystery_object", oid))
    for s in SOUNDS:
        if "loud" in s:
            lines.append(asp.fact("loud", s))
    for trig in FLASHBACK_TRIGGERS:
        lines.append(asp.fact("clue", trig))
        lines.append(asp.fact("remembered", trig))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show place/1. #show object/1. #show loud_clue/1. #show flashback/1. #show found/1."))
    if model is None:
        print("ASP verification failed: no model.")
        return 1
    print("OK: ASP program grounded successfully.")
    return 0


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(place=_safe_lookup(PLACES, params.place))

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        label=params.hero_name,
        meters={"meters": 1.0},
        memes={"curiosity": 1.0},
    ))
    adult = world.add(Entity(
        id=params.adult_name,
        kind="character",
        label=params.adult_name,
        meters={"meters": 1.0},
        memes={"calm": 1.0},
    ))
    obj_cfg = _safe_lookup(MYSTERY_OBJECTS, params.object_id)
    obj = world.add(Entity(
        id="object",
        kind="thing",
        label=obj_cfg["label"],
        phrase=obj_cfg["phrase"],
        hidden_in=obj_cfg["hide_spot"],
    ))

    world.facts.update(hero=hero, adult=adult, object=obj, params=params)
    propagate(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    adult = _safe_fact(world, f, "adult")
    obj = _safe_fact(world, f, "object")
    return [
        f"Write a short mystery for a small child where {hero.id} cannot find {obj.phrase} in {world.place}.",
        f"Tell a gentle story with a loud clue and a flashback that helps {hero.id} understand what happened.",
        f"Make a child-friendly mystery where {adult.id} and {hero.id} solve the problem together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    adult = _safe_fact(world, f, "adult")
    obj = _safe_fact(world, f, "object")

    return [
        QAItem(
            question=f"What was missing in {world.place}?",
            answer=f"{obj.phrase} was missing, and that made {hero.id} worried.",
        ),
        QAItem(
            question=f"What noisy clue helped {hero.id} notice something important?",
            answer=f"The story used {world.loud_sound}, a loud sound that made everyone turn and look around.",
        ),
        QAItem(
            question=f"What did the flashback help {hero.id} remember?",
            answer=(
                f"It helped {hero.id} remember that {adult.id} had set {obj.phrase} down earlier, "
                f"which explained why it ended up hidden."
            ),
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"{hero.id} found {obj.phrase}, and the room felt calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer=(
                "A flashback is a part of a story that shows something from earlier, so the reader can understand "
                "why things are happening now."
            ),
        ),
        QAItem(
            question="Why can a loud sound matter in a mystery?",
            answer=(
                "A loud sound can make people look up, stop, and notice a clue they would have missed before."
            ),
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer=(
                "To solve a mystery means to figure out what happened by noticing clues and putting them together."
            ),
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        bits = []
        if ent.phrase:
            bits.append(f"phrase={ent.phrase!r}")
        if ent.hidden_in:
            bits.append(f"hidden_in={ent.hidden_in!r}")
        if ent.found_by:
            bits.append(f"found_by={ent.found_by!r}")
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"  {ent.id:10} ({ent.kind}) {' '.join(bits)}")
    lines.append(f"  loud_sound={world.loud_sound!r}")
    lines.append(f"  clue={world.clue!r}")
    lines.append(f"  flashback={world.flashback}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameter selection
# ---------------------------------------------------------------------------

@dataclass
class ParamRegistry:
    places: dict[str, str] = field(default_factory=lambda: dict(PLACES))
    objects: dict[str, dict] = field(default_factory=lambda: dict(MYSTERY_OBJECTS))
    REGISTRY: object | None = None
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


REGISTRY = ParamRegistry()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small loud flashback mystery storyworld.")
    ap.add_argument("--place", choices=REGISTRY.places)
    ap.add_argument("--object", dest="object_id", choices=REGISTRY.objects)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--adult", choices=ADULT_NAMES)
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
    place = getattr(args, "place", None) or rng.choice(list(REGISTRY.places))
    object_id = getattr(args, "object_id", None) or rng.choice(list(REGISTRY.objects))
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    adult = getattr(args, "adult", None) or rng.choice(ADULT_NAMES)

    if place == "library" and object_id == "cookie":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if place == "garden" and object_id == "key":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, object_id=object_id, hero_name=hero, adult_name=adult)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== (3) World-knowledge questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show place/1. #show object/1. #show loud_clue/1. #show flashback/1. #show found/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show place/1. #show object/1. #show loud_clue/1. #show flashback/1. #show found/1."))
        print("ASP atoms:")
        for atom in model:
            print(atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="attic", object_id="key", hero_name="Mia", adult_name="Mom"),
            StoryParams(place="kitchen", object_id="cookie", hero_name="Noah", adult_name="Dad"),
            StoryParams(place="library", object_id="note", hero_name="Lena", adult_name="Grandma"),
            StoryParams(place="garden", object_id="shell", hero_name="Rosa", adult_name="Aunt June"),
            StoryParams(place="garage", object_id="button", hero_name="Theo", adult_name="Uncle Ben"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 30):
            i += 1
            rng = random.Random(base_seed + i)
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
            header = f"### {p.hero_name} in {p.place} looking for {p.object_id}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
