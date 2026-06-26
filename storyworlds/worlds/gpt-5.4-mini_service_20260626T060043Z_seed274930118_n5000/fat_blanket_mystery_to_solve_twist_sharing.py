#!/usr/bin/env python3
"""
storyworlds/worlds/fat_blanket_mystery_to_solve_twist_sharing.py
=================================================================

A small adventure-style story world about a thick blanket, a mystery to solve,
a twist, and a sharing ending.

Premise:
- A young adventurer at camp loses a fat blanket on a cold evening.
- The trail looks puzzling at first: a paw print, a snag, and a missing corner.
- The mystery resolves when the explorer discovers the blanket was not stolen;
  it was borrowed to keep a smaller creature warm.
- The twist is that the "missing" blanket leads to sharing, not blame.

The story remains state-driven:
- physical meters track cold, carried items, and warmth
- emotional memes track worry, curiosity, relief, and care
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    blanket: object | None = None
    helper: object | None = None
    hero: object | None = None
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
    place: str
    afford: set[str] = field(default_factory=set)
    cold: float = 0.0
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
class Mystery:
    id: str
    clue: str
    reason: str
    reveal: str
    solved_by: str
    twist: str
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
class StoryParams:
    place: str
    hero: str
    helper: str
    blanket: str
    mystery: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "camp": Setting(place="the camp", afford={"night", "search", "share"}, cold=2.0),
    "cabin": Setting(place="the cabin", afford={"night", "search", "share"}, cold=1.5),
    "ridge": Setting(place="the ridge", afford={"night", "search", "share"}, cold=3.0),
}

HEROES = {
    "Ari": {"type": "boy", "traits": ["brave", "curious"]},
    "Mina": {"type": "girl", "traits": ["brave", "curious"]},
    "Nico": {"type": "boy", "traits": ["lively", "curious"]},
    "Luna": {"type": "girl", "traits": ["gentle", "curious"]},
}

HELPERS = {
    "fox": {"type": "fox", "label": "little fox", "cold_need": 2.0},
    "runt": {"type": "runt", "label": "tiny wolf pup", "cold_need": 2.5},
    "owl": {"type": "owl", "label": "small owl", "cold_need": 1.5},
}

BLANKETS = {
    "fat_blanket": {
        "label": "fat blanket",
        "phrase": "a fat, fluffy blanket",
        "warmth": 3.0,
        "bulk": 2.0,
    },
    "wool_blanket": {
        "label": "wool blanket",
        "phrase": "a thick wool blanket",
        "warmth": 2.5,
        "bulk": 1.5,
    },
}

MYSTERIES = {
    "borrowed": Mystery(
        id="borrowed",
        clue="a tiny paw print",
        reason="the blanket was pulled toward a cold nest",
        reveal="the blanket was being shared",
        solved_by="following the paw print",
        twist="the missing blanket was not stolen at all",
    ),
    "snagged": Mystery(
        id="snagged",
        clue="a torn pine branch",
        reason="the blanket caught on a branch near the trail",
        reveal="the blanket had snagged on brush",
        solved_by="looking at the torn branch",
        twist="the mystery was a simple snag",
    ),
}

GIRL_NAMES = [n for n, p in HEROES.items() if p["type"] == "girl"]
BOY_NAMES = [n for n, p in HEROES.items() if p["type"] == "boy"]


def make_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    hero_info = _safe_lookup(HEROES, params.hero)
    helper_info = _safe_lookup(HELPERS, params.helper)
    blanket_info = _safe_lookup(BLANKETS, params.blanket)
    mystery = _safe_lookup(MYSTERIES, params.mystery)

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type=hero_info["type"],
        traits=list(hero_info["traits"]),
        meters={"warmth": 1.0, "worry": 0.0, "curiosity": 1.0, "relief": 0.0},
        memes={"care": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type=helper_info["type"],
        label=helper_info["label"],
        traits=["small", "cold"],
        meters={"cold": helper_info["cold_need"], "warmth": 0.0},
        memes={"need": 1.0},
    ))
    blanket = world.add(Entity(
        id=params.blanket,
        type="blanket",
        label=blanket_info["label"],
        phrase=blanket_info["phrase"],
        owner=hero.id,
        carried_by=hero.id,
        meters={"warmth": blanket_info["warmth"], "bulk": blanket_info["bulk"]},
        memes={"value": 1.0},
    ))

    world.facts.update(hero=hero, helper=helper, blanket=blanket, mystery=mystery, setting=setting)
    return world


def _cold_night(world: World, hero: Entity, helper: Entity, blanket: Entity) -> None:
    hero.meters["cold"] = world.setting.cold
    hero.memes["worry"] += 1.0
    world.say(
        f"At {world.setting.place}, {hero.id} noticed the night air biting at {hero.pronoun('possessive')} cheeks."
    )
    world.say(
        f"{hero.id} had brought {hero.pronoun('possessive')} {blanket.label}, and it felt like a soft hill of warmth."
    )


def _mystery_turn(world: World, hero: Entity, helper: Entity, blanket: Entity, mystery: Mystery) -> None:
    world.para()
    hero.memes["curiosity"] += 1.0
    hero.memes["worry"] += 1.0
    world.say(
        f"Then {hero.id} looked around and froze. The {blanket.label} was gone."
    )
    world.say(
        f"Only one clue waited nearby: {mystery.clue}."
    )
    world.say(
        f"{hero.id} whispered that the clue might explain why {mystery.reveal if mystery.id == 'borrowed' else 'it was missing'}."
    )


def _solve(world: World, hero: Entity, helper: Entity, blanket: Entity, mystery: Mystery) -> None:
    world.para()
    world.say(
        f"{hero.id} {mystery.solved_by}, and the trail led to {helper.pronoun('possessive')} nest."
    )
    if mystery.id == "borrowed":
        helper.meters["warmth"] += blanket.meters["warmth"]
        helper.memes["safe"] = 1.0
        hero.memes["relief"] += 1.0
        hero.memes["surprise"] = 1.0
        world.say(
            f"The twist was kind, not sneaky: the little fox had borrowed the {blanket.label} to keep warm."
        )
        world.say(
            f"It was not a theft. It was sharing."
        )
    else:
        hero.memes["relief"] += 1.0
        world.say(
            f"{hero.id} found the {blanket.label} caught on brush, and the puzzle became clear at once."
        )


def _share(world: World, hero: Entity, helper: Entity, blanket: Entity, mystery: Mystery) -> None:
    world.para()
    hero.meters["warmth"] += 1.0
    helper.meters["warmth"] += 1.0
    hero.memes["care"] += 1.0
    helper.memes["safe"] = 1.0
    world.say(
        f"{hero.id} smiled, wrapped the {blanket.label} around both of them, and shared its warmth with {helper.id}."
    )
    world.say(
        f"Together they sat by the fire, and the big blanket felt less like a lost thing and more like a promise."
    )


def tell(world: World) -> World:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    blanket: Entity = _safe_fact(world, world.facts, "blanket")
    mystery: Mystery = _safe_fact(world, world.facts, "mystery")

    _cold_night(world, hero, helper, blanket)
    _mystery_turn(world, hero, helper, blanket, mystery)
    _solve(world, hero, helper, blanket, mystery)
    _share(world, hero, helper, blanket, mystery)
    return world


def valid_story_combo(place: str, hero: str, helper: str, blanket: str, mystery: str) -> bool:
    if place not in SETTINGS or hero not in HEROES or helper not in HELPERS or blanket not in BLANKETS or mystery not in MYSTERIES:
        return False
    if blanket != "fat_blanket":
        return False
    if mystery == "borrowed" and helper not in {"fox", "runt"}:
        return False
    if mystery == "snagged":
        return True
    return True


def explain_rejection(params: StoryParams) -> str:
    if params.blanket != "fat_blanket":
        return "The story needs the fat blanket, because the thick blanket is the thing that goes missing and gets shared."
    if params.mystery == "borrowed" and params.helper not in {"fox", "runt"}:
        return "That twist needs a small cold creature, so the sharing feels believable."
    return "No valid story matches the chosen options."


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world about a fat blanket mystery and a sharing twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--blanket", choices=BLANKETS)
    ap.add_argument("--mystery", choices=MYSTERIES)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    hero = getattr(args, "hero", None) or rng.choice(list(HEROES))
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    blanket = getattr(args, "blanket", None) or "fat_blanket"
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    params = StoryParams(place=place, hero=hero, helper=helper, blanket=blanket, mystery=mystery)

    if not valid_story_combo(params.place, params.hero, params.helper, params.blanket, params.mystery):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(make_world(params))
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
    return [
        'Write a short adventure story for a child about a fat blanket that seems to go missing at night.',
        f"Tell a mystery story where {f['hero'].id} follows a clue and discovers that the blanket was being shared.",
        f"Write a gentle twist story set at {f['setting'].place} that ends with warm sharing by the fire.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    blanket: Entity = _safe_fact(world, f, "blanket")
    mystery: Mystery = _safe_fact(world, f, "mystery")

    return [
        QAItem(
            question=f"What did {hero.id} lose at {world.setting.place}?",
            answer=f"{hero.id} lost the {blanket.label}, which was {blanket.phrase}.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} solve the mystery?",
            answer=f"The clue was {mystery.clue}, and {mystery.solved_by} led {hero.id} to the answer.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {mystery.twist}, because {helper.id} only needed warmth and was being kind.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} sharing the {blanket.label} with {helper.id} so they could both stay warm.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a blanket for?",
            answer="A blanket is used to keep people warm and cozy, especially on cold nights.",
        ),
        QAItem(
            question="Why can a mystery be fun to solve?",
            answer="A mystery is fun to solve because you look for clues, think carefully, and discover the answer.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use something with you or giving them part of it kindly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,H,K,B,M) :- place(P), hero(H), helper(K), blanket(B), mystery(M),
                          blanket_is_fat(B), compatible(H,K,B,M).
compatible(H,K,B,borrowed) :- helper_is_small(K), hero(H), blanket(B).
compatible(_,_,B,snagged) :- blanket_is_fat(B).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for k in HELPERS:
        lines.append(asp.fact("helper", k))
        if k in {"fox", "runt", "owl"}:
            lines.append(asp.fact("helper_is_small", k))
    for b in BLANKETS:
        lines.append(asp.fact("blanket", b))
        if b == "fat_blanket":
            lines.append(asp.fact("blanket_is_fat", b))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(
        (p, h, k, b, m)
        for p in SETTINGS
        for h in HEROES
        for k in HELPERS
        for b in BLANKETS
        for m in MYSTERIES
        if valid_story_combo(p, h, k, b, m)
    )
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="camp", hero="Ari", helper="fox", blanket="fat_blanket", mystery="borrowed"),
    StoryParams(place="cabin", hero="Mina", helper="owl", blanket="fat_blanket", mystery="snagged"),
    StoryParams(place="ridge", hero="Nico", helper="runt", blanket="fat_blanket", mystery="borrowed"),
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


def build_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/5."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for row in stories:
            print("  " + " ".join(map(str, row)))
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
                params = build_params_from_args(args, random.Random(seed))
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
