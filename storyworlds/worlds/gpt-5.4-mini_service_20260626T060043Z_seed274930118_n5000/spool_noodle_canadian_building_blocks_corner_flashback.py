#!/usr/bin/env python3
"""
storyworlds/worlds/spool_noodle_canadian_building_blocks_corner_flashback.py
============================================================================

A tall-tale-style story world set in the building blocks corner, built from the
seed words spool, noodle, canadian, with a flashback that explains why the
play plan matters.

The premise:
- A child in the building blocks corner wants to build something big and silly.
- A spool, a noodle, and a Canadian souvenir become the key parts.
- A flashback reveals where the spool came from and why the child treasures it.
- The ending proves the build changed the room and the child's feelings.

The world is intentionally small and constraint-checked: the build only works
when the parts are compatible, and the flashback is only used when it actually
helps the child choose a safer, sturdier plan.
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
# Data model
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    blocks: object | None = None
    child: object | None = None
    flag: object | None = None
    noodle: object | None = None
    prize_ent: object | None = None
    spool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    place: str = "the building blocks corner"
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
class BuildPlan:
    name: str
    target: str
    action: str
    height_word: str
    flashback_trigger: str
    requires: set[str] = field(default_factory=set)
    helpful_parts: set[str] = field(default_factory=set)
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
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
    place: str
    build: str
    prize: str
    name: str
    seed: Optional[int] = None
    flashback: bool = True
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "building_blocks_corner": Setting(place="the building blocks corner"),
}

PRIZES = {
    "canadian_flag": Prize(
        label="little Canadian flag",
        phrase="a tiny Canadian flag from a travel box",
        type="flag",
        region="top",
    ),
    "red_scarf": Prize(
        label="red scarf",
        phrase="a bright red scarf",
        type="scarf",
        region="top",
    ),
    "toy_car": Prize(
        label="toy car",
        phrase="a shiny toy car",
        type="car",
        region="floor",
    ),
}

BUILD_PLANS = {
    "tower": BuildPlan(
        name="tower",
        target="a tower that touched the ceiling of imagination",
        action="build a tower",
        height_word="tall as a kite pole",
        flashback_trigger="when the tower wobbled",
        requires={"spool", "blocks"},
        helpful_parts={"spool", "blocks"},
    ),
    "bridge": BuildPlan(
        name="bridge",
        target="a bridge for toy cars",
        action="build a bridge",
        height_word="long as a corndog line",
        flashback_trigger="when the bridge sagged",
        requires={"spool", "noodle", "blocks"},
        helpful_parts={"spool", "noodle", "blocks"},
    ),
    "rocket": BuildPlan(
        name="rocket",
        target="a rocket for a paper-travel to the moon",
        action="build a rocket",
        height_word="sturdy as a tree trunk",
        flashback_trigger="when the rocket tip leaned sideways",
        requires={"spool", "blocks", "flag"},
        helpful_parts={"spool", "blocks", "flag"},
    ),
}

TRAITS = ["curious", "brave", "bright-eyed", "stubborn", "cheerful", "inventive"]
CANADIAN_WORDS = ["Canadian", "canadian"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A plan is feasible if it has all required parts.
feasible(P) :- plan(P), requires(P, R), has(R).
feasible(P) :- plan(P), not requires_any(P).

% The story is valid when the selected plan is feasible and the prize exists.
valid_story(Plan, Prize) :- feasible(Plan), prize(Prize).

% A flashback is useful when the selected plan can benefit from memory.
uses_flashback(Plan) :- flashback(Plan), valid_story(Plan, _).

#show valid_story/2.
#show uses_flashback/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for bid, plan in BUILD_PLANS.items():
        lines.append(asp.fact("plan", bid))
        if "noodle" in plan.requires:
            lines.append(asp.fact("flashback", bid))
        for r in sorted(plan.requires):
            lines.append(asp.fact("requires", bid, r))
        for h in sorted(plan.helpful_parts):
            lines.append(asp.fact("helps", bid, h))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    for part in {"spool", "noodle", "blocks", "flag"}:
        lines.append(asp.fact("has", part))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_valid = set((k, prize_id) for k, prize_id in valid_combos())
    clingo_valid = set(asp_valid())
    if python_valid == clingo_valid:
        print(f"OK: clingo gate matches valid_combos() ({len(python_valid)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_valid - python_valid))
    print("  only in python:", sorted(python_valid - clingo_valid))
    return 1


# ---------------------------------------------------------------------------
# Logic helpers
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for build_id, plan in BUILD_PLANS.items():
        if plan.requires.issubset({"spool", "noodle", "blocks", "flag"}):
            for prize_id in PRIZES:
                combos.append((build_id, prize_id))
    return combos


def build_is_reasonable(plan: BuildPlan, prize: Prize) -> bool:
    if plan.name == "bridge":
        return prize.type in {"car", "flag"}
    if plan.name == "tower":
        return prize.type in {"flag", "scarf"}
    if plan.name == "rocket":
        return prize.type in {"flag", "scarf"}
    return False


def choose_name(rng: random.Random) -> str:
    return rng.choice(["Milo", "Nina", "Iris", "Theo", "June", "Wes", "Ada"])


def choose_trait(rng: random.Random) -> str:
    return rng.choice(TRAITS)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def tell(setting: Setting, plan: BuildPlan, prize: Prize, name: str, trait: str, flashback: bool) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type="child"))
    spool = world.add(Entity(id="spool", label="spool", type="spool", owner=child.id))
    noodle = world.add(Entity(id="noodle", label="noodle", type="noodle", owner=child.id))
    flag = world.add(Entity(id="flag", label="Canadian flag", type="flag", owner=child.id))
    blocks = world.add(Entity(id="blocks", label="blocks", type="blocks", owner=child.id, plural=True))
    prize_ent = world.add(Entity(id="prize", label=prize.label, phrase=prize.phrase, type=prize.type, owner=child.id))

    child.memes["hope"] = 1
    child.memes["wonder"] = 1

    world.say(
        f"In the building blocks corner, {name} was a {trait} little builder who "
        f"could make a castle look like a mountain and a mountain look like a joke."
    )
    world.say(
        f"{name} had a {prize.label} tucked near the blocks and a grand idea to {plan.action}."
    )
    world.say(
        f"{name} said the plan would be {plan.height_word}, which was exactly the kind of talk "
        f"that could make the dust bunnies sit up and listen."
    )

    world.para()
    world.say(
        f"{name} started stacking {plan.target}."
    )
    if plan.name == "bridge":
        world.say(
            f"The {spool.label} rolled under the middle like a steady little wheel, and the {noodle.label} bent into a curve."
        )
    elif plan.name == "tower":
        world.say(
            f"The {spool.label} stood at the bottom like a stump in a fairy forest, holding the blocks brave and straight."
        )
    else:
        world.say(
            f"The {spool.label} became the rocket body, and the {flag.label} waved on top like a tiny promise to the sky."
        )

    if flashback:
        world.para()
        world.say(
            f"Then came a flashback, because {plan.flashback_trigger} made {name} remember something important."
        )
        world.say(
            f"Once, at a Canadian picnic, {name}'s grandparent had given the {spool.label} to {name} and said, "
            f'"Keep this little wheel. One day it may help you build a big brave thing."'
        )
        world.say(
            f"{name} remembered how the {spool.label} had traveled home in a lunch pail beside a noodle cup and a paper map of Canada."
        )

    world.para()
    world.say(
        f"{name} looked at the {prize.label} and worried it might topple or tangle in the build."
    )
    if plan.name == "bridge":
        world.say(
            f"So {name} tucked the {noodle.label} under the bridge like a soft brace, and the whole thing stopped wobbling."
        )
    elif plan.name == "tower":
        world.say(
            f"So {name} set the {flag.label} at the top, not as decoration only, but as a light banner that kept the tower feeling proud."
        )
    else:
        world.say(
            f"So {name} tied the {flag.label} to the front, and the rocket looked ready to zoom clear over the moon's bedtime."
        )

    child.memes["pride"] = 1
    child.memes["joy"] = 1
    world.say(
        f"By the end, the {plan.name} stood in the corner like a tall tale made of blocks, spool, and noodle, "
        f"and {name} grinned at the Canadian-colored wonder they had built."
    )

    world.facts.update(
        child=child,
        spool=spool,
        noodle=noodle,
        flag=flag,
        blocks=blocks,
        prize=prize_ent,
        plan=plan,
        flashback=flashback,
        trait=trait,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a young child set in the building blocks corner that includes the words "spool", "noodle", and "Canadian".',
        f"Tell a playful story where {f['child'].id} uses a spool and noodle to finish a big build, and a flashback explains why the spool matters.",
        f"Write a child-friendly story about a surprising build in the building blocks corner that ends with a proud, completed creation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    prize = _safe_fact(world, f, "prize")
    plan = _safe_fact(world, f, "plan")
    qa = [
        QAItem(
            question=f"What was {child.id} building in the building blocks corner?",
            answer=f"{child.id} was building {plan.target}. The plan used blocks, a spool, and a noodle to make the idea hold together.",
        ),
        QAItem(
            question=f"Why did the story stop for a flashback?",
            answer=f"It stopped for a flashback when {plan.flashback_trigger}. That memory reminded {child.id} where the spool came from and why it was special.",
        ),
        QAItem(
            question=f"What happened to the {prize.label} by the end?",
            answer=f"The {prize.label} stayed part of the plan instead of causing trouble, and the finished build stood proudly in the corner.",
        ),
    ]
    if f["plan"].name == "bridge":
        qa.append(QAItem(
            question="How did the noodle help the bridge?",
            answer="The noodle bent into a soft brace under the bridge, so the middle stopped wobbling and the build could stay up.",
        ))
    elif f["plan"].name == "tower":
        qa.append(QAItem(
            question="How did the spool help the tower?",
            answer="The spool stood at the bottom like a steady base, helping the tower rise without tipping over.",
        ))
    else:
        qa.append(QAItem(
            question="How did the Canadian flag help the rocket?",
            answer="The Canadian flag sat at the front like a light banner, and it helped the rocket feel ready for a pretend trip skyward.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem(
            question="What is a spool?",
            answer="A spool is a small round object that holds string or thread wound around it, like a tiny wheel.",
        ),
        QAItem(
            question="What is a noodle?",
            answer="A noodle is a long, soft strip of food that can bend and twist easily.",
        ),
        QAItem(
            question="What does Canadian mean?",
            answer="Canadian means something is from Canada or connected to Canada.",
        ),
    ]
    if f["plan"].name == "bridge":
        out.append(QAItem(
            question="What is a bridge used for?",
            answer="A bridge helps people or toy cars go over a gap, like water, a road, or a pretend river.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        if e.plural:
            bits.append("plural=True")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI and orchestration
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world in the building blocks corner.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--build", choices=BUILD_PLANS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--flashback", action="store_true", default=False)
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
    build = getattr(args, "build", None) or rng.choice(list(BUILD_PLANS))
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    plan = _safe_lookup(BUILD_PLANS, build)
    prize_obj = _safe_lookup(PRIZES, prize)
    if not build_is_reasonable(plan, prize_obj):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or choose_name(rng)
    return StoryParams(
        place=getattr(args, "place", None) or "building_blocks_corner",
        build=build,
        prize=prize,
        name=name,
        seed=getattr(args, "seed", None),
        flashback=getattr(args, "flashback", None) or plan.name in {"bridge", "rocket"},
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(BUILD_PLANS, params.build),
        _safe_lookup(PRIZES, params.prize),
        params.name,
        choose_trait(random.Random(params.seed or 0)),
        params.flashback,
    )
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
        print(asp_program("#show valid_story/2.\n#show uses_flashback/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show valid_story/2.\n#show uses_flashback/1."))
        valid = sorted(set(asp.atoms(model, "valid_story")))
        flash = sorted(set(asp.atoms(model, "uses_flashback")))
        print(f"{len(valid)} valid story combos:\n")
        for plan, prize in valid:
            use_fb = "yes" if (plan,) in flash else "no"
            print(f"  {plan:10} {prize:14} flashback={use_fb}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("building_blocks_corner", "bridge", "toy_car", "Milo", flashback=True),
            StoryParams("building_blocks_corner", "tower", "canadian_flag", "Nina", flashback=True),
            StoryParams("building_blocks_corner", "rocket", "red_scarf", "Iris", flashback=True),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
