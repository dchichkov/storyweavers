#!/usr/bin/env python3
"""
A standalone story world for a tiny pirate tale about logic, a boat, surprise,
conflict, and a lesson learned.

Premise:
- A small pirate crew sails a boat toward a glittering island.
- The captain trusts logic: check the map, count the stars, and choose a safe route.
- A surprise appears on the water, causing conflict on deck.
- The crew learns a lesson: calm thinking beats hasty shouting.

The story model is state-driven:
- boat meters track damage, drift, and steadiness
- character memes track worry, pride, conflict, and trust
- surprise and conflict emerge from the world and are resolved by a careful plan
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
# Model
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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    boat: object | None = None
    captain: object | None = None
    hero: object | None = None
    map_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "pirate"}:
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
class Setting:
    place: str = "the bright blue sea"
    boat_name: str = "the Little Gull"
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
class Boat:
    id: str
    name: str
    safety: float = 0.0
    drift: float = 0.0
    repaired: bool = False
    boat: object | None = None
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
class Challenge:
    surprise: str
    conflict: str
    lesson: str
    hazard: str
    solution: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.boat = Boat(id="boat", name=setting.boat_name)
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
    "sea": Setting(place="the bright blue sea", boat_name="the Little Gull"),
    "harbor": Setting(place="the harbor road", boat_name="the Salt Sprite"),
}

CHALLENGES = {
    "reef": Challenge(
        surprise="a hidden reef",
        conflict="the crew argued about whether to turn left or right",
        lesson="they learned that looking carefully first keeps a boat safe",
        hazard="rocks under the water",
        solution="the captain counted the waves and steered around the reef",
    ),
    "fog": Challenge(
        surprise="a thick patch of fog",
        conflict="the crew shouted different directions at once",
        lesson="they learned that one calm voice can help everyone think",
        hazard="no clear path ahead",
        solution="the captain used the lantern and the map together",
    ),
    "sail": Challenge(
        surprise="a sudden snap in the sail rope",
        conflict="the crew rushed and bumped elbows on deck",
        lesson="they learned that simple jobs go better when everyone has a task",
        hazard="a drooping sail",
        solution="the captain tied the rope, then gave each pirate one job",
    ),
}

HERO_NAMES = ["Mira", "Nell", "Toby", "Finn", "Pip", "Ava"]
CREW_NAMES = ["Captain Reed", "Bosun Wren", "Mate Joss"]
TRAITS = ["brave", "curious", "lively", "stubborn", "clever"]

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when a setting and challenge are both present.
valid_story(S, C) :- setting(S), challenge(C).

% A challenge is a surprise if it introduces a hazard on the route.
surprise(C) :- challenge(C), hazard(C, _).

% Conflict follows if the crew disagrees during the surprise.
conflict(C) :- surprise(C), argument(C).

% A lesson is learned if a careful plan resolves the conflict.
lesson_learned(C) :- conflict(C), solution(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("surprise_text", cid, ch.surprise))
        lines.append(asp.fact("argument", cid))
        lines.append(asp.fact("solution", cid))
        lines.append(asp.fact("hazard", cid, ch.hazard))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def setup_world(setting: Setting, challenge: Challenge, hero_name: str, crew_name: str, trait: str) -> World:
    w = World(setting)
    hero = w.add(Entity(id=hero_name, kind="character", type="pirate", traits=["little", trait]))
    captain = w.add(Entity(id=crew_name, kind="character", type="pirate", label="the captain"))
    map_ent = w.add(Entity(id="map", type="map", label="a creased map", phrase="a creased map with a red X"))
    boat = w.add(Entity(id="boat", type="boat", label=setting.boat_name, phrase=f"the boat {setting.boat_name}"))

    hero.memes.update({"trust": 0.0, "worry": 0.0, "conflict": 0.0, "joy": 0.0})
    captain.memes.update({"calm": 1.0, "logic": 1.0})
    boat.meters.update({"drift": 0.0, "damage": 0.0, "steady": 1.0})
    map_ent.meters["clarity"] = 1.0

    w.facts.update(hero=hero, captain=captain, map=map_ent, boat=boat, challenge=challenge)
    return w


def tell_story(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    captain: Entity = _safe_fact(world, world.facts, "captain")
    boat: Entity = _safe_fact(world, world.facts, "boat")
    challenge: Challenge = _safe_fact(world, world.facts, "challenge")

    world.say(
        f"{hero.id} was a little pirate who loved the smell of salt and the creak of {boat.label}."
    )
    world.say(
        f"{hero.id} and {captain.label} kept a creased map on deck, because {captain.label} liked logic more than guessing."
    )
    world.para()
    world.say(
        f"One evening on {world.setting.place}, a surprise appeared: {challenge.surprise}."
    )
    world.boat.meters["drift"] += 1.0
    hero.memes["worry"] += 1.0
    hero.memes["conflict"] += 1.0
    world.say(
        f"The surprise made {boat.label} wobble, and {hero.id}'s chest went tight."
    )
    world.say(
        f"Then {challenge.conflict}, and soon the deck was full of mixed-up pointing and noisy words."
    )
    world.para()
    world.say(
        f"Instead of shouting back, {captain.label} held up the map and said, \"Let's use our eyes and think.\""
    )
    world.say(
        f"{captain.label} looked for {challenge.hazard}, counted the waves, and chose a careful line past the trouble."
    )
    world.boat.meters["steady"] += 1.0
    world.boat.meters["drift"] = max(0.0, world.boat.meters["drift"] - 1.0)
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    hero.memes["trust"] += 1.0
    hero.memes["conflict"] = 0.0
    world.boat.repaired = True
    world.say(
        f"At last, {challenge.solution}, and {boat.label} slipped safely along the dark water."
    )
    world.say(
        f"{hero.id} smiled, because {challenge.lesson}."
    )
    world.say(
        f"By the time the stars came out, the boat was steady again, and the little pirate had learned to choose thought before fuss."
    )


# ---------------------------------------------------------------------------
# Params and QA
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    challenge: str
    name: str
    captain: str
    trait: str
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


def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    challenge = _safe_fact(world, world.facts, "challenge")
    return [
        f"Write a short pirate tale about {hero.id}, a boat, and {challenge.surprise}.",
        f"Tell a child-friendly story where logic helps a pirate crew solve a surprise on {world.setting.place}.",
        f"Write a simple sea adventure with conflict on deck and a lesson learned at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    captain = _safe_fact(world, world.facts, "captain")
    challenge = _safe_fact(world, world.facts, "challenge")
    boat = _safe_fact(world, world.facts, "boat")
    return [
        QAItem(
            question=f"Who was the little pirate in the story?",
            answer=f"The little pirate was {hero.id}, who sailed on {boat.label} with {captain.label}.",
        ),
        QAItem(
            question=f"What surprise caused trouble on the water?",
            answer=f"The surprise was {challenge.surprise}, which made the boat wobble and started the conflict.",
        ),
        QAItem(
            question=f"How did the captain use logic to help?",
            answer=f"{captain.label} looked at the map, counted the waves, and steered carefully around the danger.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that {challenge.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a boat for?",
            answer="A boat is used to travel on water and carry people across seas, lakes, or rivers.",
        ),
        QAItem(
            question="What does it mean to use logic?",
            answer="Using logic means thinking carefully, noticing clues, and making a sensible choice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"setting={world.setting.place}")
    lines.append(f"boat={world.boat.name} drift={world.boat.drift} steady={world.boat.safety}")
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(parts)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {(sid, cid) for sid in SETTINGS for cid in CHALLENGES}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches python registry ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and python:")
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    if py - cl:
        print(" only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Parsing / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world about logic, a boat, surprise, conflict, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--captain", choices=CREW_NAMES)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    challenge = getattr(args, "challenge", None) or rng.choice(list(CHALLENGES))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    captain = getattr(args, "captain", None) or rng.choice(CREW_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, challenge=challenge, name=name, captain=captain, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(_safe_lookup(SETTINGS, params.setting), _safe_lookup(CHALLENGES, params.challenge), params.name, params.captain, params.trait)
    tell_story(world)
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="sea", challenge="reef", name="Mira", captain="Captain Reed", trait="clever"),
    StoryParams(setting="sea", challenge="fog", name="Toby", captain="Bosun Wren", trait="curious"),
    StoryParams(setting="harbor", challenge="sail", name="Nell", captain="Mate Joss", trait="brave"),
]


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
        stories = sorted(set(asp.atoms(model, "valid_story")))
        for s in stories:
            print(s)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
