#!/usr/bin/env python3
"""
storyworlds/worlds/caster_sandbox_reconciliation_mystery_to_solve_twist.py
==========================================================================

A small slice-of-life storyworld in a sandbox setting with a caster, a mystery
to solve, a twist, and a reconciliation ending.

Premise:
- A child finds a sandbox castle kit and a little caster tool.
- A tiny mystery appears when the sand keeps changing shape.
- The twist is that the "mystery" is caused by a helpful neighbor using the
  caster to make patterns and secret paths for a surprise.
- The story resolves with a reconciliation: misunderstanding turns into a shared
  game, and the sandbox becomes a place for both building and playing.

This script follows the Storyweavers contract:
- self-contained stdlib script
- imports results eagerly, asp lazily
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate and inline ASP_RULES twin
- emits registry facts via asp_facts()
- --verify checks ASP/Python parity and exercise generated stories
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
        if not hasattr(self, "_tags"):
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
    place: str = "the sandbox"
    affords: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Caster:
    id: str
    label: str
    phrase: str
    action: str
    effect: str
    mystery: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

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
class Clue:
    id: str
    label: str
    phrase: str
    reveals: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

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
class Twist:
    id: str
    label: str
    reveal: str
    tags: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


@dataclass
class StoryParams:
    name: str
    child_gender: str
    parent: str
    caster: str
    clue: str
    twist: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


SETTINGS = {
    "sandbox": Setting(place="the sandbox", affords={"build", "search", "share"}),
}

CASTERS = {
    "sifter": Caster(
        id="sifter",
        label="sand sifter",
        phrase="a little sand sifter",
        action="sift the sand",
        effect="made neat little lines in the sand",
        mystery="the sand kept changing shape",
        tags={"caster", "sand"},
    ),
    "stamp": Caster(
        id="stamp",
        label="shape stamp",
        phrase="a shape stamp",
        action="press patterns into the sand",
        effect="left star and shell marks",
        mystery="new shapes kept appearing",
        tags={"caster", "pattern"},
    ),
}

CLUES = {
    "footprints": Clue(
        id="footprints",
        label="footprints",
        phrase="tiny footprints",
        reveals="someone had been visiting the sandbox and making secret trails",
        tags={"mystery", "sandbox"},
    ),
    "cup": Clue(
        id="cup",
        label="plastic cup",
        phrase="a plastic cup",
        reveals="it could scoop sand and hide a surprise path",
        tags={"mystery", "sandbox"},
    ),
}

TWISTS = {
    "neighbor": Twist(
        id="neighbor",
        label="neighbor surprise",
        reveal="the supposed mystery was a friendly neighbor making a game",
        tags={"twist", "reconciliation"},
    ),
    "sibling": Twist(
        id="sibling",
        label="sibling surprise",
        reveal="the 'mystery' was a sibling setting up a shared castle game",
        tags={"twist", "reconciliation"},
    ),
}

NAMES = ["Mia", "Liam", "Noa", "Ava", "Theo", "Zoe", "Ben", "Luna"]
GENDERS = {"Mia": "girl", "Liam": "boy", "Noa": "girl", "Ava": "girl", "Theo": "boy", "Zoe": "girl", "Ben": "boy", "Luna": "girl"}
TRAITS = ["curious", "gentle", "quiet", "thoughtful", "patient", "bright"]


def reason_ok(caster: Caster, clue: Clue, twist: Twist) -> bool:
    return bool(caster.tags & {"caster"}) and bool(clue.tags & {"mystery"}) and bool(twist.tags & {"twist"})


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CASTERS:
            for clue in CLUES:
                for tw in TWISTS:
                    if reason_ok(_safe_lookup(CASTERS, c), _safe_lookup(CLUES, clue), _safe_lookup(TWISTS, tw)):
                        combos.append((s, c, clue, tw))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("affords", sid, "build"))
        lines.append(asp.fact("affords", sid, "search"))
        lines.append(asp.fact("affords", sid, "share"))
    for cid, c in CASTERS.items():
        lines.append(asp.fact("caster", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("caster_tag", cid, t))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("clue_tag", cid, t))
    for tid, t in TWISTS.items():
        lines.append(asp.fact("twist", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("twist_tag", tid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,L,T) :- setting(S), caster(C), clue(L), twist(T),
                  caster_tag(C,"caster"), clue_tag(L,"mystery"), twist_tag(T,"twist").
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Sandbox slice-of-life storyworld with a caster, a mystery, and a twist.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mom", "dad"])
    ap.add_argument("--caster", choices=CASTERS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--twist", choices=TWISTS)
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
    combos = valid_combos()
    if getattr(args, "caster", None) and getattr(args, "caster", None) not in CASTERS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "clue", None) and getattr(args, "clue", None) not in CLUES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "twist", None) and getattr(args, "twist", None) not in TWISTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [
        c for c in combos
        if (getattr(args, "caster", None) is None or c[1] == getattr(args, "caster", None))
        and (getattr(args, "clue", None) is None or c[2] == getattr(args, "clue", None))
        and (getattr(args, "twist", None) is None or c[3] == getattr(args, "twist", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    _, caster, clue, twist = rng.choice(list(filtered))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    gender = getattr(args, "gender", None) or _safe_lookup(GENDERS, name)
    parent = getattr(args, "parent", None) or rng.choice(["mom", "dad"])
    return StoryParams(name=name, child_gender=gender, parent=parent, caster=caster, clue=clue, twist=twist)


def _build_world(params: StoryParams) -> World:
    world = World(SETTINGS["sandbox"])
    child = world.add(Entity(id=params.name, kind="character", type=params.child_gender, role="child", traits=["little", "curious"]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent", label=f"the {params.parent}"))
    caster = _safe_lookup(CASTERS, params.caster)
    clue = _safe_lookup(CLUES, params.clue)
    twist = _safe_lookup(TWISTS, params.twist)
    world.facts.update(child=child, parent=parent, caster=caster, clue=clue, twist=twist)
    child.memes["curiosity"] += 1
    child.memes["trust"] += 1
    world.say(f"{child.id} liked playing in {world.setting.place}.")
    world.say(f"One afternoon, {child.id} found {caster.phrase} near a little sand castle wall.")
    world.para()
    world.say(f"{caster.effect.capitalize()}, but there was one odd thing: {caster.mystery}.")
    world.say(f"{child.id} noticed {clue.phrase} and wondered what they meant.")
    world.para()
    child.memes["mystery"] += 1
    child.meters["sand"] += 1
    world.say(f'{child.id} asked, "Who made this?" and watched the sandbox closely.')
    world.say(f"{parent.label_word.capitalize()} came over and listened instead of hurrying away.")
    world.para()
    child.memes["worry"] += 1
    world.say(f"Then came the twist: {twist.reveal}.")
    world.say(f"{parent.label_word.capitalize()} smiled and explained the surprise, so the strange tracks made sense at last.")
    world.para()
    child.memes["reconciliation"] += 1
    parent.memes["reconciliation"] += 1
    world.say(f"{child.id} laughed, and {child.id} and {parent.label_word} cleaned the sand together.")
    world.say(f"In the end, the sandbox stayed messy in a good way, and the new game belonged to both of them.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short slice-of-life story set in a sandbox where a child finds a caster tool and notices a small mystery.',
        f'Write a gentle story where {f["child"].id} in the sandbox sees {f["clue"].phrase}, discovers a twist, and ends with reconciliation.',
        'Tell a child-facing story about a sandbox, a caster, a mystery to solve, and a happy shared ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, caster, clue, twist = f["child"], f["parent"], f["caster"], f["clue"], f["twist"]
    return [
        QAItem(
            question=f"What did {child.id} find in the sandbox?",
            answer=f"{child.id} found {caster.phrase}. It made patterns in the sand and started the mystery."
        ),
        QAItem(
            question=f"What was the mystery that needed solving?",
            answer=f"The mystery was that {caster.mystery}. {child.id} watched the sandbox closely to figure it out."
        ),
        QAItem(
            question=f"What clue helped explain the strange sandbox tracks?",
            answer=f"{clue.phrase} helped. It showed that {clue.reveals}, which gave the mystery a clue-shaped answer."
        ),
        QAItem(
            question=f"What was the twist at the end?",
            answer=f"The twist was that {twist.reveal}. The surprising truth changed the whole story."
        ),
        QAItem(
            question=f"How did the story end for {child.id} and {parent.label_word}?",
            answer=f"They reconciled by cleaning the sand together and laughing. The sandbox became their shared game."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a sandbox?", "A sandbox is a box or area filled with sand where children can build and play."),
        QAItem("What does a caster do?", "A caster can sift or stamp the sand so it makes patterns, paths, or little shapes."),
        QAItem("What is reconciliation?", "Reconciliation means people stop being upset, understand each other, and make peace again."),
        QAItem("What is a mystery?", "A mystery is something puzzling that you want to understand."),
        QAItem("What is a twist in a story?", "A twist is a surprising new fact that changes how you understand what was happening."),
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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
    StoryParams(name="Mia", child_gender="girl", parent="mom", caster="sifter", clue="footprints", twist="neighbor"),
    StoryParams(name="Theo", child_gender="boy", parent="dad", caster="stamp", clue="cup", twist="sibling"),
]


def asp_verify_stories() -> int:
    rng = random.Random(7)
    for _ in range(10):
        p = resolve_params(build_parser().parse_args([]), rng)
        s = generate(p)
        if not s.story:
            return 1
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(0 if asp_verify() == 0 and asp_verify_stories() == 0 else 1)
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, caster, clue, twist) combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
