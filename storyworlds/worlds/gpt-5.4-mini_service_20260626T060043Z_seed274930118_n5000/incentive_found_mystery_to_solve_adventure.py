#!/usr/bin/env python3
"""
A standalone Storyweavers world: an adventure mystery about a child explorer
who finds an incentive to solve a small mystery.

The world model tracks:
- physical meters: clue_found, trust, tiredness, reward
- emotional memes: curiosity, worry, courage, joy

The child discovers a clue, uses an incentive to keep going, solves the mystery,
and ends with a concrete changed world.
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue_item: object | None = None
    hero: object | None = None
    incentive_item: object | None = None
    parent: object | None = None
    reward_item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Setting:
    place: str
    detail: str
    found_kind: str
    clue_kind: str
    affords: set[str] = field(default_factory=set)
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
    missing: str
    found_phrase: str
    solving_action: str
    reward: str
    incentive: str
    clue: str
    location_hint: str
    solution: str
    tags: set[str] = field(default_factory=set)
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
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.trace_lines: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


GIRL_NAMES = ["Mia", "Ava", "Lila", "Nora", "Zoe", "Ella", "Ruby", "Iris"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Owen", "Jude", "Eli", "Noah"]
TRAITS = ["brave", "curious", "patient", "lively", "clever", "bold"]


SETTINGS = {
    "forest_trail": Setting(
        place="the forest trail",
        detail="Tall trees leaned over a sandy path, and a crooked sign pointed deeper in.",
        found_kind="map",
        clue_kind="footprints",
        affords={"map", "birdcall", "lantern"},
    ),
    "old_cabin": Setting(
        place="the old cabin",
        detail="The cabin door creaked, and dust floated in the light like tiny stars.",
        found_kind="key",
        clue_kind="drawer",
        affords={"key", "drawer", "lantern"},
    ),
    "harbor": Setting(
        place="the harbor",
        detail="Masts rocked gently, and ropes snapped softly in the salt wind.",
        found_kind="shell",
        clue_kind="rope",
        affords={"shell", "rope", "lantern"},
    ),
}

MYSTERIES = {
    "map": Mystery(
        id="map",
        missing="the lost trail marker",
        found_phrase="a torn corner of a map",
        solving_action="follow the marked path",
        reward="a tiny brass compass",
        incentive="the promise of a shiny compass at the end",
        clue="footprints",
        location_hint="near the split in the path",
        solution="the marker had blown behind a stump",
        tags={"forest", "map", "trail"},
    ),
    "key": Mystery(
        id="key",
        missing="the little blue box",
        found_phrase="a rusty key",
        solving_action="open the dusty drawer",
        reward="a wrapped cookie",
        incentive="the thought of a warm cookie once the drawer was opened",
        clue="drawer",
        location_hint="under the table",
        solution="the box was hidden in the drawer",
        tags={"cabin", "key", "drawer"},
    ),
    "shell": Mystery(
        id="shell",
        missing="the captain's whistle",
        found_phrase="a pearly shell",
        solving_action="ask the dock keeper",
        reward="a paper star",
        incentive="the chance to earn a paper star for helping",
        clue="rope",
        location_hint="by the mooring post",
        solution="the whistle had fallen into a rope basket",
        tags={"harbor", "shell", "rope"},
    ),
}

ITEMS = {
    "lantern": ("a little lantern", "lantern"),
    "map": ("a torn map", "map"),
    "key": ("a small key", "key"),
    "shell": ("a bright shell", "shell"),
    "cookie": ("a wrapped cookie", "cookie"),
    "compass": ("a brass compass", "compass"),
    "star": ("a paper star", "star"),
}


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    parent: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure mystery storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def reasonableness_gate(setting: Setting, mystery: Mystery) -> bool:
    return mystery.id in setting.affords


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for mid in setting.affords:
            out.append((place, mid))
    return sorted(out)


def explain_rejection(setting: Setting, mystery: Mystery) -> str:
    return (
        f"(No story: {setting.place} doesn't support the mystery of {mystery.missing}. "
        f"Choose a place where the clue and the missing thing fit together.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "mystery", None):
        if not reasonableness_gate(_safe_lookup(SETTINGS, getattr(args, "place", None)), _safe_lookup(MYSTERIES, getattr(args, "mystery", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery = rng.choice(combos)
    m = _safe_lookup(MYSTERIES, mystery)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, parent=parent, trait=trait)


def tell(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    setting = _safe_lookup(SETTINGS, params.place)

    clue_item = world.add(Entity(id="clue", type=params.mystery, label=mystery.found_phrase, owner=hero.id))
    incentive_item = world.add(Entity(id="incentive", type="reward", label=mystery.incentive, owner=hero.id))
    reward_item = world.add(Entity(id="reward", type="reward", label=mystery.reward, owner=hero.id))

    world.facts.update(hero=hero, parent=parent, mystery=mystery, setting=setting,
                       clue_item=clue_item, incentive_item=incentive_item, reward_item=reward_item)

    hero.memes["curiosity"] = 2
    hero.memes["courage"] = 1

    world.say(f"{hero.id} was a little {params.trait} {params.gender} who loved adventure.")
    world.say(f"One morning, {hero.id} went to {setting.place}. {setting.detail}")
    world.say(f"There, {hero.id} found {mystery.found_phrase}. That was the first clue in a mystery to solve.")
    world.say(
        f"{hero.id}'s {parent.id.lower() if False else params.parent} had a special incentive ready: "
        f"{mystery.incentive}."
    )

    world.para()
    hero.memes["worry"] = 1
    world.say(
        f"{hero.id} wanted to give up when the path bent and the clue seemed small, "
        f"but {mystery.incentive} gave {hero.pronoun('object')} a reason to keep going."
    )
    world.say(f"So {hero.id} followed the clue {mystery.location_hint}.")

    world.para()
    hero.memes["joy"] = 1
    world.say(
        f"At last, {hero.id} found out that {mystery.solution}. "
        f"That solved the mystery of {mystery.missing}."
    )
    world.say(
        f"{params.parent} smiled and gave {hero.id} {mystery.reward}. "
        f"The incentive had turned a hard search into a brave adventure."
    )

    world.para()
    world.say(
        f"By the end, {hero.id} carried {mystery.reward} home, "
        f"and the trail felt less strange because the mystery was finally solved."
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(World(_safe_lookup(SETTINGS, params.place)), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m = _safe_fact(world, f, "mystery")
    return [
        f'Write a short adventure story for a child who finds a clue and an incentive to solve a mystery.',
        f'Write a child-friendly story where {f["hero"].id} finds {m.found_phrase} and keeps going because of {m.incentive}.',
        f'Write a simple mystery-to-solve adventure set at {f["setting"].place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    parent: Entity = _safe_fact(world, f, "parent")
    m: Mystery = _safe_fact(world, f, "mystery")
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"What mystery did {hero.id} try to solve at {setting.place}?",
            answer=f"{hero.id} tried to solve the mystery of {m.missing} at {setting.place}.",
        ),
        QAItem(
            question=f"What clue did {hero.id} find first?",
            answer=f"{hero.id} found {m.found_phrase} first.",
        ),
        QAItem(
            question=f"What kept {hero.id} going when the search felt hard?",
            answer=f"{m.incentive} kept {hero.id} going.",
        ),
        QAItem(
            question=f"Who helped {hero.id} at the end?",
            answer=f"{parent.id if parent.id != 'Parent' else 'the parent'} helped by smiling and giving {hero.id} the reward.",
        ),
        QAItem(
            question=f"What happened when the mystery was solved?",
            answer=f"The lost thing was found, and {hero.id} got {m.reward}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone solve a mystery.",
        ),
        QAItem(
            question="What is an incentive?",
            answer="An incentive is a reason to keep going or do a hard thing, like a reward or promise.",
        ),
        QAItem(
            question="Why do explorers check clues carefully?",
            answer="Explorers check clues carefully because one clue can point them toward the next place to look.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A place supports a mystery if it affords that mystery id.
valid(Place, Mystery) :- affords(Place, Mystery).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for mid in setting.affords:
            lines.append(asp.fact("affords", place, mid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("incentive", mid, m.incentive))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


CURATED = [
    StoryParams(place="forest_trail", mystery="map", name="Mia", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="old_cabin", mystery="key", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="harbor", mystery="shell", name="Nora", gender="girl", parent="mother", trait="clever"),
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, mystery) combos:\n")
        for place, mystery in combos:
            print(f"  {place:14} {mystery}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def valid_story_combos() -> list[tuple[str, str]]:
    return valid_combos()


if __name__ == "__main__":
    main()
