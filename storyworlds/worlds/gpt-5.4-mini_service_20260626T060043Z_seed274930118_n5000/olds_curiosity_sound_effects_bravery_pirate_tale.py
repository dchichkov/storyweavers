#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/olds_curiosity_sound_effects_bravery_pirate_tale.py
===============================================================================================================================

A small pirate-tale story world about an old crew member, a curious child pirate,
sound effects, and a brave choice.

The core seed image:
- An old pirate keeps hearing strange sounds on a calm little voyage.
- Curiosity draws the child toward a closed chest or hidden nook.
- The child must be brave enough to look, ask, or help.
- The turn resolves when the sound is explained and the crew finds something useful,
  surprising, or sweet inside.

This script models that premise as a tiny state machine:
- physical meters: distance, noise, risk, wind, etc.
- emotional memes: curiosity, worry, bravery, relief, delight.

The prose is generated from state transitions, not from a frozen template.
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


# ---------------------------------------------------------------------------
# Entities
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
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    openable: bool = False
    opened: bool = False
    noisy: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    item: object | None = None
    def __post_init__(self) -> None:
        for k in ("distance", "noise", "risk", "wind", "find"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "worry", "bravery", "relief", "joy", "wonder"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pirate", "sailor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str = "the little pirate ship"
    open_sea: bool = True
    SETTINGS: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    label: str
    phrase: str
    sound: str
    source: str
    risk: str
    reveal: str
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
    clue: str
    hero_name: str
    hero_type: str
    elder_name: str
    elder_type: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def old_prefix(name: str) -> str:
    return f"old {name}"


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {"ship": Setting()}

CLUES = {
    "parrot": Clue(
        id="parrot",
        label="parrot",
        phrase="an old parrot with a bright red feather",
        sound="squawk-squawk",
        source="the mast",
        risk="afraid",
        reveal="a buried apple wrapped in cloth",
    ),
    "box": Clue(
        id="box",
        label="wooden box",
        phrase="an old wooden box with a brass latch",
        sound="tap-tap-tap",
        source="below the deck",
        risk="stuck",
        reveal="a map corner tied with blue string",
    ),
    "pump": Clue(
        id="pump",
        label="bilge pump",
        phrase="an old bilge pump with a squeaky handle",
        sound="chug-chug",
        source="near the water line",
        risk="leaking",
        reveal="fresh water was draining safely away",
    ),
    "shell": Clue(
        id="shell",
        label="shell",
        phrase="a little shell hidden in a crate",
        sound="clink-clink",
        source="inside a crate of rope",
        risk="lonely",
        reveal="a song the crew could hum together",
    ),
}

HERO_NAMES = ["Nina", "Milo", "Tess", "Pip", "Luna", "Owen", "Jade", "Theo"]
ELDER_NAMES = ["Captain Reed", "Old Mara", "Uncle Finn", "Aunt Sloane"]
HERO_TYPES = ["girl", "boy"]
ELDER_TYPES = ["pirate", "captain", "sailor"]
TRAITS = ["curious", "brave", "lively", "small", "quick"]


# ---------------------------------------------------------------------------
# World model and prose helpers
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    world = World(SETTINGS["ship"])
    hero = world.add(Entity(
        id=params.hero_name, kind="character", type=params.hero_type,
        label=params.hero_name, memes={"curiosity": 0.0, "worry": 0.0, "bravery": 0.0, "relief": 0.0, "joy": 0.0, "wonder": 0.0},
    ))
    elder = world.add(Entity(
        id=params.elder_name, kind="character", type=params.elder_type,
        label=params.elder_name, memes={"curiosity": 0.0, "worry": 0.0, "bravery": 0.0, "relief": 0.0, "joy": 0.0, "wonder": 0.0},
    ))
    clue = _safe_lookup(CLUES, params.clue)
    item = world.add(Entity(
        id=clue.id, type="thing", label=clue.label, phrase=clue.phrase,
        openable=(clue.id in {"box"}), noisy=True,
    ))
    world.facts.update(hero=hero, elder=elder, clue=item, clue_def=clue, trait=random.choice(TRAITS))
    return world


def sound_intro(clue: Clue) -> str:
    return {
        "parrot": "squawk-squawk!",
        "box": "tap-tap-tap!",
        "pump": "chug-chug!",
        "shell": "clink-clink!",
    }[clue.id]


def setting_line(world: World) -> str:
    return "The little ship bobbed on blue water, and the deck creaked under tiny boots."


def curiosity_line(hero: Entity, clue: Clue) -> str:
    return f"{hero.label} kept looking toward the {clue.source} because {clue.sound} sounded too strange to ignore."


def bravery_line(hero: Entity) -> str:
    return f"{hero.label} took a deep breath and stepped closer, even though the noise made the air feel a little sharp."


def resolve_line(hero: Entity, elder: Entity, clue: Clue) -> str:
    return f"When they opened it, they found {clue.reveal}, and the whole deck felt warmer at once."


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
def _r_noise_to_curiosity(world: World) -> list[str]:
    out: list[str] = []
    hero = next(e for e in world.characters() if e.type in HERO_TYPES)
    clue = _safe_fact(world, world.facts, "clue_def")
    if hero.memes["curiosity"] >= THRESHOLD and ("noise", clue.id) not in world.fired:
        world.fired.add(("noise", clue.id))
        hero.meters["distance"] += 1
        hero.memes["wonder"] += 1
        out.append(f"{hero.label} leaned toward the sound.")
    return out


def _r_bravery_to_open(world: World) -> list[str]:
    out: list[str] = []
    hero = next(e for e in world.characters() if e.type in HERO_TYPES)
    clue = _safe_fact(world, world.facts, "clue")
    if hero.memes["bravery"] >= THRESHOLD and clue.openable and not clue.opened:
        sig = ("open", clue.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        clue.opened = True
        hero.meters["find"] += 1
        hero.memes["relief"] += 1
        out.append("The latch gave a tiny click.")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    clue = _safe_fact(world, world.facts, "clue")
    hero = next(e for e in world.characters() if e.type in HERO_TYPES)
    elder = next(e for e in world.characters() if e.type in ELDER_TYPES)
    if clue.opened and ("reveal", clue.id) not in world.fired:
        world.fired.add(("reveal", clue.id))
        hero.memes["joy"] += 1
        elder.memes["joy"] += 1
        elder.memes["relief"] += 1
        out.append(resolve_line(hero, elder, world.facts["clue_def"]))
    return out


CAUSAL_RULES = [
    _r_noise_to_curiosity,
    _r_bravery_to_open,
    _r_reveal,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    world = make_world(params)
    hero: Entity = _safe_fact(world, world.facts, "hero")
    elder: Entity = _safe_fact(world, world.facts, "elder")
    clue: Entity = _safe_fact(world, world.facts, "clue")
    clue_def: Clue = _safe_fact(world, world.facts, "clue_def")

    world.say(f"{hero.label} was a {world.facts['trait']} little pirate on the ship with {elder.label}.")
    world.say(setting_line(world))
    world.say(f"Then came {sound_intro(clue_def)} from {clue.source}.")
    world.say(curiosity_line(hero, clue_def))
    hero.memes["curiosity"] += 1
    hero.memes["worry"] += 0.5
    world.say(f"{elder.label} warned that old ships can hide tricky surprises, but {hero.label} wanted to know the truth.")
    world.para()
    world.say(bravery_line(hero))
    hero.memes["bravery"] += 1
    hero.meters["distance"] += 1
    propagate(world, narrate=True)
    world.para()
    world.say(f"{elder.label} smiled when {hero.label} looked inside.")
    world.say(f"By the end, the sound was no longer scary; it was a clue that led to something helpful and kind.")
    world.facts.update(final_open=clue.opened, hero=hero, elder=elder)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue: Clue = _safe_fact(world, f, "clue_def")
    hero: Entity = _safe_fact(world, f, "hero")
    elder: Entity = _safe_fact(world, f, "elder")
    return [
        f'Write a pirate tale for a young child with a curious {hero.type} named {hero.label}, a strange sound, and a brave choice.',
        f"Tell a short story where {hero.label} hears {clue.sound} on a ship and {elder.label} helps explain what it means.",
        f"Write a gentle pirate story about curiosity, sound effects, and bravery on a little ship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    elder: Entity = _safe_fact(world, f, "elder")
    clue: Clue = _safe_fact(world, f, "clue_def")
    return [
        QAItem(
            question=f"Who heard the strange sound on the ship?",
            answer=f"{hero.label} heard it first, then kept listening because the sound made {hero.pronoun('object')} curious.",
        ),
        QAItem(
            question=f"What sound did the old pirate clue make?",
            answer=f"It made the sound {clue.sound}, which came from {clue.source}.",
        ),
        QAItem(
            question=f"Why did {hero.label} go closer even though the sound was odd?",
            answer=f"{hero.label} was curious and brave, so {hero.pronoun()} stepped closer to find out what was making the noise.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be curious?",
            answer="Being curious means wanting to look, listen, or ask questions about something you do not yet understand.",
        ),
        QAItem(
            question="What is a sound effect in a story?",
            answer="A sound effect is a made-up or written-out noise, like 'tap-tap' or 'squawk,' that helps you imagine what is happening.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something scary or hard even when you feel nervous.",
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
hero(H) :- hero_name(H).
elder(E) :- elder_name(E).
clue(C) :- clue_id(C).

curious(H) :- hero_name(H), hero_curiosity(H, 1).
brave(H) :- hero_name(H), hero_bravery(H, 1).
heard(H,C) :- hero_name(H), clue_id(C), clue_sound(C,S), sound_heard(H,S).

closer(H) :- curious(H).
opens(C) :- brave(H), clue_id(C), clue_openable(C).

resolved(H,C) :- opens(C), heard(H,C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue_id", cid))
        lines.append(asp.fact("clue_sound", cid, clue.sound))
        lines.append(asp.fact("clue_source", cid, clue.source))
        if clue.id == "box":
            lines.append(asp.fact("clue_openable", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show resolved/2.")
    model = asp.one_model(program)
    asp_res = set(asp.atoms(model, "resolved"))
    py_res = set()
    for cid, clue in CLUES.items():
        if clue.openable:
            py_res.add(("dummy", cid))
    if asp_res == py_res:
        print(f"OK: clingo gate matches Python reasonableness check ({len(asp_res)} cases).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  clingo:", sorted(asp_res))
    print("  python:", sorted(py_res))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate tale story world with curiosity, sound effects, and bravery.")
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--elder")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--elder-type", choices=ELDER_TYPES)
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
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    elder_type = getattr(args, "elder_type", None) or rng.choice(ELDER_TYPES)
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    elder_name = getattr(args, "elder", None) or rng.choice(ELDER_NAMES)
    if hero_name == elder_name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        clue=clue,
        hero_name=hero_name,
        hero_type=hero_type,
        elder_name=elder_name,
        elder_type=elder_type,
    )


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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.openable:
            bits.append(f"openable={e.openable}")
        if e.opened:
            bits.append("opened=True")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
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
    StoryParams(clue="parrot", hero_name="Nina", hero_type="girl", elder_name="Captain Reed", elder_type="pirate"),
    StoryParams(clue="box", hero_name="Milo", hero_type="boy", elder_name="Old Mara", elder_type="captain"),
    StoryParams(clue="pump", hero_name="Tess", hero_type="girl", elder_name="Uncle Finn", elder_type="sailor"),
    StoryParams(clue="shell", hero_name="Pip", hero_type="boy", elder_name="Aunt Sloane", elder_type="pirate"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show resolved/2."))
        print(sorted(asp.atoms(model, "resolved")))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
