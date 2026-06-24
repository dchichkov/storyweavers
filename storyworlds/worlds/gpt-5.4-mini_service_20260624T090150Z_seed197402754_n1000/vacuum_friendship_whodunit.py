#!/usr/bin/env python3
"""
storyworlds/worlds/vacuum_friendship_whodunit.py
=================================================

A small whodunit storyworld about a missing thing, a noisy vacuum, and a friend
who helps solve the mystery.

Seed premise:
---
Two friends notice something is wrong in a tidy house. A vacuum has been used,
but crumbs, dust, and a hidden clue make it look like somebody did not tell the
whole truth. The friends follow the trail, ask careful questions, and discover
that the "culprit" is not a thief at all, but a friend who was trying to help.

Story structure:
- Setup: friendship, ordinary room, and a small missing object.
- Tension: the vacuum has changed the room, and the clues do not add up.
- Turn: the friends reason through the trail and the vacuum bag.
- Resolution: truth is revealed, and the friendship grows stronger.

This script models both physical state (meters) and emotional state (memes)
and narrates from the evolving world model.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Room:
    name: str = "the living room"
    tidy: bool = True
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
    room: str
    hero_name: str
    friend_name: str
    hero_gender: str
    friend_gender: str
    missing_item: str
    clue: str
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


ROOMS = {
    "living_room": Room(name="the living room", tidy=True),
    "hallway": Room(name="the hallway", tidy=True),
    "den": Room(name="the den", tidy=True),
}

MISSING_ITEMS = {
    "button": ("a bright blue button", "button"),
    "coin": ("a shiny gold coin", "coin"),
    "note": ("a tiny folded note", "note"),
}

CLUES = {
    "dust": "a dusty circle under the couch",
    "lint": "a fluffy ball of lint near the rug",
    "crumbs": "a little trail of crumbs by the chair",
}

HERO_NAMES_G = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
HERO_NAMES_B = ["Ben", "Leo", "Max", "Finn", "Theo"]
FRIEND_NAMES_G = ["Eva", "June", "Iris", "Maya", "Ada"]
FRIEND_NAMES_B = ["Sam", "Noah", "Eli", "Jack", "Owen"]


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        w = World(self.room)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _setup_world(params: StoryParams) -> World:
    room = _safe_lookup(ROOMS, params.room)
    world = World(room)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_gender))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_gender))
    item_phrase, item_label = _safe_lookup(MISSING_ITEMS, params.missing_item)
    missing = world.add(
        Entity(
            id="missing",
            type="thing",
            label=item_label,
            phrase=item_phrase,
            owner=hero.id,
            meters={"missing": 0.0},
        )
    )
    vacuum = world.add(
        Entity(
            id="vacuum",
            type="thing",
            label="vacuum",
            phrase="a noisy vacuum cleaner",
            owner=friend.id,
            meters={"noise": 1.0, "power": 1.0},
        )
    )
    clue = world.add(
        Entity(
            id="clue",
            type="thing",
            label=params.clue,
            phrase=_safe_lookup(CLUES, params.clue),
            meters={"evidence": 1.0},
        )
    )
    world.facts.update(hero=hero, friend=friend, missing=missing, vacuum=vacuum, clue=clue)
    return world


def _vacuum_change(world: World) -> None:
    vacuum = world.get("vacuum")
    missing = world.get("missing")
    clue = world.get("clue")
    if "vacuumed" in world.fired:
        return
    world.fired.add("vacuumed")
    vacuum.meters["used"] = 1.0
    world.room.tidy = True
    clue.meters["seen"] = 1.0
    missing.meters["missing"] = 1.0
    world.get("friend").memes["nervous"] = 1.0


def _reason_about_clue(world: World) -> None:
    if "reasoned" in world.fired:
        return
    clue = world.get("clue")
    friend = world.get("friend")
    hero = world.get("hero")
    missing = world.get("missing")
    if clue.meters.get("seen", 0.0) >= THRESHOLD:
        world.fired.add("reasoned")
        hero.memes["curious"] = 1.0
        friend.memes["relief"] = 1.0
        if missing.label == "button":
            missing.meters["found"] = 1.0


def _reveal_truth(world: World) -> None:
    if "revealed" in world.fired:
        return
    world.fired.add("revealed")
    friend = world.get("friend")
    hero = world.get("hero")
    friend.memes["guilt"] = 0.0
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1.0
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1.0
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1.0


def tell(params: StoryParams) -> World:
    world = _setup_world(params)
    hero = world.get("hero")
    friend = world.get("friend")
    missing = world.get("missing")
    clue = world.get("clue")
    vacuum = world.get("vacuum")

    world.say(f"{hero.id} and {friend.id} were best friends, and they liked solving little mysteries together.")
    world.say(f"One morning, {hero.id} noticed that {missing.phrase} was gone from the table.")
    world.say(f"In the same room, there was {vacuum.phrase}, and the floor looked strangely neat.")

    world.para()
    _vacuum_change(world)
    world.say(f"{friend.id} had used the vacuum to help clean up, but {hero.id} frowned because something still did not make sense.")
    world.say(f"Near the rug, they found {clue.phrase}.")

    world.para()
    world.say(f"{hero.id} crouched down and looked at the clue like a tiny detective.")
    world.say(f"If the vacuum had swallowed the missing thing, why was {clue.phrase} still there?")
    _reason_about_clue(world)
    world.say(f"{friend.id} remembered that {missing.label} had been stuck inside the vacuum's brush, not lost forever.")

    world.para()
    _reveal_truth(world)
    world.say(f"{friend.id} apologized for keeping quiet, and {hero.id} helped open the vacuum bag.")
    if missing.meters.get("found", 0.0) >= THRESHOLD:
        world.say(f"There, under a soft puff of dust, was {missing.phrase}.")
    else:
        world.say(f"There, tucked safely away, was the missing {missing.label}.")
    world.say(f"{hero.id} smiled, because the mystery was solved and the two friends were laughing again.")
    world.say(f"That night, the room stayed tidy, the vacuum stayed quiet, and their friendship felt even stronger.")

    world.facts.update(room=params.room, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    missing = _safe_fact(world, f, "missing")
    clue = _safe_fact(world, f, "clue")
    return [
        f'Write a short whodunit for young children about {hero.id} and {friend.id}, a vacuum, and a missing {missing.label}.',
        f"Tell a gentle mystery where {friend.id} used a vacuum, {hero.id} found a clue, and the friends solved what happened.",
        f'Create a child-friendly detective story that includes {clue.label} and ends with friendship being restored.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    missing = _safe_fact(world, f, "missing")
    clue = _safe_fact(world, f, "clue")
    return [
        QAItem(
            question=f"What kind of story is this about {hero.id} and {friend.id}?",
            answer=f"It is a small whodunit about two friends who notice a mystery, follow clues, and solve it together.",
        ),
        QAItem(
            question=f"What was missing from the room?",
            answer=f"{missing.phrase.capitalize()} was missing, and that made {hero.id} wonder what had happened.",
        ),
        QAItem(
            question=f"What clue helped the friends think carefully?",
            answer=f"They found {clue.phrase}, and that clue helped them see that the vacuum had changed the room.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"The friends found the missing thing inside the vacuum area, apologized, and ended the story feeling closer than before.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a vacuum do?",
            answer="A vacuum sucks up dust, crumbs, and little bits of dirt so the floor can look cleaner.",
        ),
        QAItem(
            question="Why do detectives look at clues?",
            answer="Detectives look at clues because clues can help them figure out what happened when something is a mystery.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and try to make things better together.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for room in ROOMS:
        lines.append(asp.fact("room", room))
    for key, (_, label) in MISSING_ITEMS.items():
        lines.append(asp.fact("item", key))
        lines.append(asp.fact("label", key, label))
    for key in CLUES:
        lines.append(asp.fact("clue", key))
    lines.append(asp.fact("theme", "friendship"))
    lines.append(asp.fact("style", "whodunit"))
    lines.append(asp.fact("feature", "vacuum"))
    return "\n".join(lines)


ASP_RULES = r"""
compatible_story(Room, Item, Clue) :- room(Room), item(Item), clue(Clue), theme(friendship), style(whodunit), feature(vacuum).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatible() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/3."))
    return sorted(set(asp.atoms(model, "compatible_story")))


def asp_verify() -> int:
    py = {(r, i, c) for r in ROOMS for i in MISSING_ITEMS for c in CLUES}
    cl = set(asp_compatible())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} combos).")
        return 0
    print("Mismatch between clingo and python.")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny friendship whodunit with a vacuum and clues.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--missing-item", choices=MISSING_ITEMS)
    ap.add_argument("--clue", choices=CLUES)
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
    room = getattr(args, "room", None) or rng.choice(list(ROOMS))
    hero_gender = getattr(args, "hero_gender", None) or rng.choice(["girl", "boy"])
    friend_gender = getattr(args, "friend_gender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES_G if hero_gender == "girl" else HERO_NAMES_B)
    friend_name = getattr(args, "friend_name", None) or rng.choice(FRIEND_NAMES_G if friend_gender == "girl" else FRIEND_NAMES_B)
    if hero_name == friend_name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    missing_item = getattr(args, "missing_item", None) or rng.choice(list(MISSING_ITEMS))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    return StoryParams(
        room=room,
        hero_name=hero_name,
        friend_name=friend_name,
        hero_gender=hero_gender,
        friend_gender=friend_gender,
        missing_item=missing_item,
        clue=clue,
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
    StoryParams(room="living_room", hero_name="Mia", friend_name="Ben", hero_gender="girl", friend_gender="boy", missing_item="button", clue="dust"),
    StoryParams(room="hallway", hero_name="Leo", friend_name="Ava", hero_gender="boy", friend_gender="girl", missing_item="coin", clue="lint"),
    StoryParams(room="den", hero_name="Nora", friend_name="Sam", hero_gender="girl", friend_gender="boy", missing_item="note", clue="crumbs"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_compatible()
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
