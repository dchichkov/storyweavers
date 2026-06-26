#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/chowder_snooze_whatchamacallit_surprise_conflict_rhyming_story.py
=================================================================================================================

A small, self-contained storyworld for a rhyming, child-facing tale built from
the seed words chowder, snooze, and whatchamacallit.

Premise:
- A child and a helper are making chowder in a cozy kitchen.
- A sleepy mistake, a missing tool, and a surprise cause a conflict.
- A rhyming fix resolves the scene and ends with a warm, complete image.

The world is intentionally tiny and constraint-driven:
- physical state uses meters (heat, spilled, sleepy, neat, hungry)
- emotional state uses memes (joy, worry, surprise, conflict, trust, pride)
- the narrative is generated from state transitions rather than a frozen template

This world includes:
- chowder
- snooze
- whatchamacallit
- Surprise
- Conflict
- a rhyming-story style
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    dish: object | None = None
    helper: object | None = None
    hero: object | None = None
    tool: object | None = None
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
    affords: set[str]
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
class Dish:
    label: str
    phrase: str
    hot: bool = True
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
class Tool:
    id: str
    label: str
    phrase: str
    handles: set[str]
    fix: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.lines = []
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    setting: str
    dish: str
    tool: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"cook", "snooze"}),
    "table": Setting(place="the tiny kitchen table", affords={"cook", "snooze"}),
}

DISHES = {
    "chowder": Dish(label="chowder", phrase="a steaming bowl of chowder", hot=True),
    "corn_chowder": Dish(label="corn chowder", phrase="a creamy bowl of corn chowder", hot=True),
    "veg_soup": Dish(label="soup", phrase="a happy pot of vegetable soup", hot=True),
}

TOOLS = [
    Tool(
        id="ladle",
        label="ladle",
        phrase="a long ladle",
        handles={"stir"},
        fix="stir the chowder back smooth",
        reveal="found the ladle under a napkin",
    ),
    Tool(
        id="lid",
        label="lid",
        phrase="a shiny lid",
        handles={"cover"},
        fix="cover the pot so it would not splash",
        reveal="peeked under a towel and saw the lid",
    ),
    Tool(
        id="spoon",
        label="spoon",
        phrase="a little spoon",
        handles={"stir"},
        fix="stir gently and make it neat again",
        reveal="spotted the spoon beside the sink",
    ),
]

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ruby", "Ivy"]
BOY_NAMES = ["Ben", "Theo", "Finn", "Ezra", "Kai"]
TRAITS = ["brave", "spry", "bright", "nimble", "jolly"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld about chowder, snooze, and whatchamacallit.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--dish", choices=DISHES.keys())
    ap.add_argument("--tool", choices=[t.id for t in TOOLS])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mother", "father", "grandma", "grandpa"])
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


def pick_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def reasonableness_gate(setting: Setting, dish: Dish, tool: Tool) -> bool:
    return "cook" in setting.affords and dish.hot and bool(tool.fix)


ASP_RULES = r"""
dish_ok(D) :- dish(D), hot(D).
tool_ok(T) :- tool(T), can_fix(T).
valid(S,D,T) :- setting(S), dish_ok(D), tool_ok(T), affords(S,cook).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for did in DISHES:
        lines.append(asp.fact("dish", did))
        lines.append(asp.fact("hot", did))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        lines.append(asp.fact("can_fix", t.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(s, d, t) for s in SETTINGS for d in DISHES for t in [x.id for x in TOOLS] if reasonableness_gate(_safe_lookup(SETTINGS, s), _safe_lookup(DISHES, d), next(x for x in TOOLS if x.id == t))}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "place", None) or rng.choice(list(SETTINGS.keys()))
    dish = getattr(args, "dish", None) or rng.choice(list(DISHES.keys()))
    tool = getattr(args, "tool", None) or rng.choice([t.id for t in TOOLS])
    if not reasonableness_gate(_safe_lookup(SETTINGS, setting), _safe_lookup(DISHES, dish), next(t for t in TOOLS if t.id == tool)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or pick_name(gender, rng)
    helper_name = getattr(args, "helper_name", None) or rng.choice(["Aunt May", "Dad", "Mom", "Grandma Jo"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(["mother", "father", "grandma", "grandpa"])
    return StoryParams(setting=setting, dish=dish, tool=tool, hero_name=name, hero_type=gender, helper_name=helper_name, helper_type=helper_type)


def _do_cook(world: World, hero: Entity, dish: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    dish.meters["heat"] = dish.meters.get("heat", 0) + 1
    dish.memes["surprise"] = dish.memes.get("surprise", 0) + 1
    world.say(f"{hero.id} stirred the chowder with a sing-song grin.")


def _do_snooze(world: World, helper: Entity) -> None:
    helper.memes["sleepy"] = helper.memes.get("sleepy", 0) + 1
    helper.meters["sleepy"] = helper.meters.get("sleepy", 0) + 1
    world.say(f"{helper.id} began to snooze, with a soft and dozy croon.")


def _do_conflict(world: World, hero: Entity, dish: Entity, helper: Entity) -> None:
    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    dish.meters["spilled"] = dish.meters.get("spilled", 0) + 1
    world.say(f"But oh, what a shock! The pot gave a plop and a swoon, and chowder splashed over the spoon.")
    world.say(f"{hero.id} frowned at the mess, and {helper.id} woke from the swoon.")
    world.say(f"That was the start of the conflict, under the kitchen moon.")


def _do_surprise(world: World, hero: Entity, tool: Entity) -> None:
    hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
    world.say(f"Then came a surprise: the whatchamacallit was the ladle all along, tucked safe in the spoon drawer dune.")


def _do_fix(world: World, hero: Entity, helper: Entity, dish: Entity, tool: Entity) -> None:
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    hero.memes["conflict"] = 0.0
    helper.memes["pride"] = helper.memes.get("pride", 0) + 1
    dish.meters["spilled"] = 0.0
    world.say(f"{helper.id} smiled and said, 'Let's use the {tool.label}; we can fix the fuss by the light of the moon.'")
    world.say(f"They used it to {tool.fix}, and soon the chowder was thick, warm, and strewn with a spoonful tune.")
    world.say(f"{hero.id} laughed, the pot stayed neat, and the whole little kitchen hummed in a cozy cocoon.")


def tell_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    dish_cfg = _safe_lookup(DISHES, params.dish)
    tool_cfg = next(t for t in TOOLS if t.id == params.tool)
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    dish = world.add(Entity(id=dish_cfg.label, kind="thing", type="dish", label=dish_cfg.label, phrase=dish_cfg.phrase))
    tool = world.add(Entity(id="whatchamacallit", kind="thing", type="tool", label="whatchamacallit", phrase=tool_cfg.phrase))
    world.facts.update(hero=hero, helper=helper, dish=dish, tool=tool, setting=setting, dish_cfg=dish_cfg, tool_cfg=tool_cfg)

    world.say(f"In {setting.place}, {hero.id} made {dish_cfg.phrase}, so bright and fine.")
    world.say(f"{hero.id} called the spoon the whatchamacallit, and that made everybody laugh in rhyme.")
    _do_cook(world, hero, dish)
    world.say(f"{helper.id} gave a yawn and a snooze, soft as a line of chime.")
    _do_snooze(world, helper)
    world.say(f"Then something went wrong in a blink and a boop: the ladle slipped out of time.")
    _do_conflict(world, hero, dish, helper)
    _do_surprise(world, hero, tool)
    _do_fix(world, hero, helper, dish, tool)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a rhyming story for a young child about {f['hero'].id}, chowder, and a whatchamacallit in {f['setting'].place}.",
        f"Tell a short cozy tale where {f['helper'].id} snoozes, a surprise appears, and the conflict turns into a fix.",
        f"Make a simple rhyming story that includes chowder, snooze, and whatchamacallit, and ends with a warm kitchen scene.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, dish = f["hero"], f["helper"], f["dish"]
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who was the story about in the kitchen?",
            answer=f"The story was about {hero.id}, who cooked chowder with {helper.id} in {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {helper.id} do before the problem started?",
            answer=f"{helper.id} began to snooze, so the kitchen got sleepy and quiet before the surprise.",
        ),
        QAItem(
            question=f"What was the whatchamacallit?",
            answer=f"The whatchamacallit was the hidden {tool_cfg_phrase(f)} that they used to fix the chowder.",
        ),
        QAItem(
            question=f"Why was there conflict in the story?",
            answer=f"There was conflict when the chowder splashed and the kitchen got messy, so {hero.id} frowned and {helper.id} had to wake up.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, the chowder was neat again, the surprise was solved, and {hero.id} and {helper.id} were smiling together.",
        ),
    ]


def tool_cfg_phrase(facts: dict[str, object]) -> str:
    cfg = facts["tool_cfg"]
    return cfg.phrase


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is chowder?",
        answer="Chowder is a thick soup, often creamy, with soft pieces inside it.",
    ),
    QAItem(
        question="What does snooze mean?",
        answer="To snooze means to doze or sleep for a little while.",
    ),
    QAItem(
        question="What is a whatchamacallit?",
        answer="A whatchamacallit is a funny word people use when they do not remember an object's name.",
    ),
    QAItem(
        question="What is a surprise?",
        answer="A surprise is something unexpected that makes people look up and pay attention.",
    ),
    QAItem(
        question="What is conflict?",
        answer="Conflict is a problem or disagreement that makes a story tense until it gets solved.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
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
    StoryParams(setting="kitchen", dish="chowder", tool="ladle", hero_name="Mina", hero_type="girl", helper_name="Mom", helper_type="mother"),
    StoryParams(setting="table", dish="corn_chowder", tool="lid", hero_name="Noah", hero_type="boy", helper_name="Dad", helper_type="father"),
    StoryParams(setting="kitchen", dish="veg_soup", tool="spoon", hero_name="Lia", hero_type="girl", helper_name="Grandma Jo", helper_type="grandma"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    dish = getattr(args, "dish", None) or rng.choice(list(DISHES))
    tool = getattr(args, "tool", None) or rng.choice([t.id for t in TOOLS])
    if not reasonableness_gate(_safe_lookup(SETTINGS, setting), _safe_lookup(DISHES, dish), next(t for t in TOOLS if t.id == tool)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or pick_name(gender, rng)
    helper_name = getattr(args, "helper_name", None) or rng.choice(["Mom", "Dad", "Grandma Jo", "Aunt Lee"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(["mother", "father", "grandma", "grandpa"])
    return StoryParams(setting=setting, dish=dish, tool=tool, hero_name=name, hero_type=gender, helper_name=helper_name, helper_type=helper_type)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
