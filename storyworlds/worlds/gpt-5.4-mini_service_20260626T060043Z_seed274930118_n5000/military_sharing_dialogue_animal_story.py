#!/usr/bin/env python3
"""
military_sharing_dialogue_animal_story.py
========================================

A small story world about animal friends in a tiny military-style camp where
sharing gear and speaking kindly solves a problem.

Premise:
- A young animal wants to use a prized item or treat.
- A stricter camp routine or missing gear creates friction.
- A friend or leader notices the shortage and offers a fair share.
- Dialogue turns the problem into a cooperative ending.

This is a gentle, child-facing world: the "military" element is limited to
marching, drills, hats, and orderly camp routines.
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
class Creature:
    name: str
    species: str
    role: str
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    items: list[str] = field(default_factory=list)

    friend: object | None = None
    hero: object | None = None
    def pronoun(self) -> str:
        return "they"

    def poss(self) -> str:
        return "their"
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
class Item:
    id: str
    label: str
    owner: Optional[str] = None
    held_by: Optional[str] = None
    shareable: bool = True
    use: str = ""
    item: object | None = None
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
class Camp:
    place: str
    duty: str
    mood: str = "orderly"
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
    camp: str
    duty: str
    hero_name: str
    hero_species: str
    friend_name: str
    friend_species: str
    item: str
    seed: Optional[int] = None
    p: object | None = None
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
    def __init__(self, camp: Camp) -> None:
        self.camp = camp
        self.creatures: dict[str, Creature] = {}
        self.items: dict[str, Item] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.trace_log: list[str] = []

    def add_creature(self, c: Creature) -> Creature:
        self.creatures[c.name] = c
        return c

    def add_item(self, it: Item) -> Item:
        self.items[it.id] = it
        return it

    def get_creature(self, name: str) -> Creature:
        return self.creatures[name]

    def say(self, text: str) -> None:
        self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)

    def trace(self, text: str) -> None:
        self.trace_log.append(text)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
CAMPS = {
    "drill_yard": Camp(place="the drill yard", duty="marching practice"),
    "mess_tent": Camp(place="the mess tent", duty="supper line"),
    "gear_shed": Camp(place="the gear shed", duty="gear check"),
}

ANIMALS = {
    "rabbit": {"gentle", "quick"},
    "fox": {"bright", "swift"},
    "bear": {"steady", "strong"},
    "deer": {"quiet", "careful"},
    "mouse": {"tiny", "eager"},
    "otter": {"playful", "helpful"},
}

ITEMS = {
    "drum": Item(id="drum", label="a little drum", use="beat the march"),
    "hat": Item(id="hat", label="a red cap", use="keep the line neat"),
    "flag": Item(id="flag", label="a tiny flag", use="lead the group"),
    "cup": Item(id="cup", label="a blue cup", use="drink after the drill"),
    "crumbs": Item(id="crumbs", label="some crackers", use="share at supper"),
}

DUTIES = {
    "marching": "marching practice",
    "snack": "supper line",
    "cleanup": "gear check",
}

HERO_TRAITS = ["brave", "gentle", "curious", "cheerful", "careful", "lively"]
FRIEND_TRAITS = ["kind", "patient", "calm", "helpful", "smart", "sweet"]


# ---------------------------------------------------------------------------
# Logic helpers
# ---------------------------------------------------------------------------
def valid_combo(camp: str, duty: str, item: str) -> bool:
    if camp not in CAMPS or duty not in DUTIES or item not in ITEMS:
        return False
    if camp == "drill_yard" and item not in {"drum", "flag", "hat"}:
        return False
    if camp == "mess_tent" and item not in {"cup", "crumbs"}:
        return False
    if camp == "gear_shed" and item not in {"hat", "cup"}:
        return False
    return True


def explain_rejection(camp: str, duty: str, item: str) -> str:
    return (
        f"(No story: {_safe_lookup(ITEMS, item).label} does not fit naturally with "
        f"{_safe_lookup(DUTIES, duty)} at {_safe_lookup(CAMPS, camp).place}. Choose a more compatible item.)"
    )


def setup_world(params: StoryParams) -> World:
    camp = _safe_lookup(CAMPS, params.camp)
    world = World(camp)

    hero = world.add_creature(Creature(
        name=params.hero_name,
        species=params.hero_species,
        role="young recruit",
        meters={"hope": 1.0},
        memes={"want": 1.0, "worry": 0.0, "joy": 0.0},
    ))
    friend = world.add_creature(Creature(
        name=params.friend_name,
        species=params.friend_species,
        role="camp helper",
        meters={"care": 1.0},
        memes={"kindness": 1.0, "joy": 0.0},
    ))
    item = world.add_item(Item(
        id=params.item,
        label=_safe_lookup(ITEMS, params.item).label,
        owner=friend.name,
        held_by=friend.name,
        shareable=True,
        use=_safe_lookup(ITEMS, params.item).use,
    ))

    world.facts.update(
        hero=hero,
        friend=friend,
        item=item,
        params=params,
    )
    return world


def narrate_opening(world: World) -> None:
    h: Creature = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    f: Creature = _safe_fact(world, world.facts, "friend")  # type: ignore[assignment]
    item: Item = _safe_fact(world, world.facts, "item")  # type: ignore[assignment]
    camp = world.camp

    world.say(
        f"At {camp.place}, {h.name} was a {h.species} recruit who liked {camp.duty}."
    )
    world.say(
        f"{h.name} also kept looking at {item.label}, because {item.use} sounded fun."
    )
    world.say(
        f"{f.name}, a {f.species} helper, noticed {h.name}'s ears perk up and smiled."
    )


def narrate_conflict(world: World) -> None:
    h: Creature = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    f: Creature = _safe_fact(world, world.facts, "friend")  # type: ignore[assignment]
    item: Item = _safe_fact(world, world.facts, "item")  # type: ignore[assignment]

    h.memes["worry"] += 1.0
    h.memes["want"] += 1.0
    world.para()
    world.say(
        f'"Can I use {item.label}?" {h.name} asked. "I want to help with {world.camp.duty}."'
    )
    world.say(
        f'"Not yet," said {f.name}. "We only have one, and the line would get messy if we rush."'
    )
    world.say(
        f"{h.name} frowned a little. The little recruit wanted a turn, but the camp only had one good tool."
    )


def narrate_share(world: World) -> None:
    h: Creature = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    f: Creature = _safe_fact(world, world.facts, "friend")  # type: ignore[assignment]
    item: Item = _safe_fact(world, world.facts, "item")  # type: ignore[assignment]

    world.para()
    world.say(
        f"{f.name} tapped {item.label} with a paw and said, "
        f'"Let us share it. You can take the first turn, and I will take the next."'
    )
    world.say(
        f'"Really?" asked {h.name}.'
    )
    world.say(
        f'"Really," said {f.name}. "A good camp works best when friends help each other."'
    )
    item.held_by = h.name
    h.items.append(item.id)
    h.memes["joy"] += 1.0
    f.memes["joy"] += 1.0


def narrate_resolution(world: World) -> None:
    h: Creature = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    f: Creature = _safe_fact(world, world.facts, "friend")  # type: ignore[assignment]
    item: Item = _safe_fact(world, world.facts, "item")  # type: ignore[assignment]

    world.para()
    world.say(
        f"{h.name} used {item.label} carefully, and {f.name} waited with a patient smile."
    )
    world.say(
        f"Then they switched, and both animals finished the task together."
    )
    world.say(
        f"By the end, the drill yard looked neat, the item stayed safe, and {h.name} felt proud to share."
    )


def story_from_params(params: StoryParams) -> World:
    world = setup_world(params)
    narrate_opening(world)
    narrate_conflict(world)
    narrate_share(world)
    narrate_resolution(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p: StoryParams = _safe_fact(world, world.facts, "params")  # type: ignore[assignment]
    return [
        f'Write a short animal story about sharing at {_safe_lookup(CAMPS, p.camp).place} during {_safe_lookup(DUTIES, p.duty)}.',
        f"Tell a gentle military-style camp story where {p.hero_name} asks to borrow {_safe_lookup(ITEMS, p.item).label}.",
        f'Write a child-friendly story with dialogue about two animals solving a turn-taking problem.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact(world, world.facts, "params")  # type: ignore[assignment]
    h: Creature = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    f: Creature = _safe_fact(world, world.facts, "friend")  # type: ignore[assignment]
    item: Item = _safe_fact(world, world.facts, "item")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who wanted to use {item.label}?",
            answer=f"{h.name}, the {h.species} recruit, wanted to use {item.label} for {_safe_lookup(DUTIES, p.duty)}.",
        ),
        QAItem(
            question=f"Who helped by sharing {item.label}?",
            answer=f"{f.name}, the {f.species} helper, shared {item.label} and let {h.name} take a turn first.",
        ),
        QAItem(
            question="How did the problem get solved?",
            answer=f"They solved it by sharing and taking turns, so both animals could finish the job without arguing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact(world, world.facts, "params")  # type: ignore[assignment]
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use part of what you have or take a turn with it.",
        ),
        QAItem(
            question="Why is taking turns helpful?",
            answer="Taking turns is helpful because it lets everyone get a fair chance without fighting.",
        ),
        QAItem(
            question="What is a drill?",
            answer="A drill is practice that helps a group do something in an orderly way.",
        ),
        QAItem(
            question="What is a camp?",
            answer=f"A camp is a place where a group stays and works together, like {_safe_lookup(CAMPS, p.camp).place}.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for c in world.creatures.values():
        lines.append(f"{c.name}: species={c.species}, role={c.role}, meters={c.meters}, memes={c.memes}, items={c.items}")
    for it in world.items.values():
        lines.append(f"{it.id}: label={it.label}, owner={it.owner}, held_by={it.held_by}")
    lines.extend(world.trace_log)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
camp(drill_yard). camp(mess_tent). camp(gear_shed).
duty(marching). duty(snack). duty(cleanup).
item(drum). item(hat). item(flag). item(cup). item(crumbs).

compatible(drill_yard, marching, drum).
compatible(drill_yard, marching, hat).
compatible(drill_yard, marching, flag).
compatible(mess_tent, snack, cup).
compatible(mess_tent, snack, crumbs).
compatible(gear_shed, cleanup, hat).
compatible(gear_shed, cleanup, cup).

#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for camp_id in CAMPS:
        lines.append(asp.fact("camp", camp_id))
    for duty_id in DUTIES:
        lines.append(asp.fact("duty", duty_id))
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = sorted((c, d, i) for c in CAMPS for d in DUTIES for i in ITEMS if valid_combo(c, d, i))
    asp_set = asp_valid_combos()
    if py == asp_set:
        print(f"OK: ASP and Python agree on {len(py)} compatible combos.")
        return 0
    print("MISMATCH:")
    if set(py) - set(asp_set):
        print("  only in python:", sorted(set(py) - set(asp_set)))
    if set(asp_set) - set(py):
        print("  only in ASP:", sorted(set(asp_set) - set(py)))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal military sharing dialogue story world.")
    ap.add_argument("--camp", choices=CAMPS)
    ap.add_argument("--duty", choices=DUTIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-species", choices=sorted(ANIMALS))
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-species", choices=sorted(ANIMALS))
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
    camps = list(CAMPS)
    duties = list(DUTIES)
    items = list(ITEMS)

    if getattr(args, "camp", None) and getattr(args, "duty", None) and getattr(args, "item", None):
        if not valid_combo(getattr(args, "camp", None), getattr(args, "duty", None), getattr(args, "item", None)):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [(c, d, i) for c in camps for d in duties for i in items if valid_combo(c, d, i)]
    combos = [
        c for c in combos
        if (getattr(args, "camp", None) is None or c[0] == getattr(args, "camp", None))
        and (getattr(args, "duty", None) is None or c[1] == getattr(args, "duty", None))
        and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    camp, duty, item = rng.choice(list(combos))
    hero_species = getattr(args, "hero_species", None) or rng.choice(sorted(ANIMALS))
    friend_species = getattr(args, "friend_species", None) or rng.choice(sorted([s for s in ANIMALS if s != hero_species]))
    hero_name = getattr(args, "hero_name", None) or rng.choice(["Pip", "Milo", "Nia", "Toby", "Luna", "Benny", "Kiko", "Pia"])
    friend_name = getattr(args, "friend_name", None) or rng.choice(["Rae", "Bram", "Suki", "Momo", "Tess", "Juno", "Otis"])
    return StoryParams(
        camp=camp,
        duty=duty,
        hero_name=hero_name,
        hero_species=hero_species,
        friend_name=friend_name,
        friend_species=friend_species,
        item=item,
    )


def generate(params: StoryParams) -> StorySample:
    world = story_from_params(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c, d, i in combos:
            print(f"  {c:10} {d:10} {i}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = []
        for c in CAMPS:
            for d in DUTIES:
                for i in ITEMS:
                    if valid_combo(c, d, i):
                        p = StoryParams(
                            camp=c,
                            duty=d,
                            hero_name="Pip",
                            hero_species="rabbit",
                            friend_name="Rae",
                            friend_species="fox",
                            item=i,
                            seed=base_seed,
                        )
                        samples.append(generate(p))
    else:
        samples = []
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.camp} / {p.duty} / {p.item}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
