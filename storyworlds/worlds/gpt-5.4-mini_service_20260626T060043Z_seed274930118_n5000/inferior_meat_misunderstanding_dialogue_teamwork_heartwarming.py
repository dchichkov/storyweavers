#!/usr/bin/env python3
"""
storyworlds/worlds/inferior_meat_misunderstanding_dialogue_teamwork_heartwarming.py
==================================================================================

A standalone story world about a small heartwarming misunderstanding:
a child thinks something "inferior" about the meat they brought, a gentle
dialogue clears it up, and teamwork turns the meal into something lovely.

The premise is built as a tiny simulated world:
- a cook has prepared a humble piece of meat for a shared meal,
- a child misunderstands the word "inferior" and worries the food is bad,
- helpers explain, improve the meal together, and the ending proves the change.

The world tracks physical meters and emotional memes so the story is driven by
state instead of a frozen paraphrase.
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
# World model
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    cooked: bool = False
    improved: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    membranes: object | None = None
    child: object | None = None
    cut: object | None = None
    parent: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {
                "freshness": 0.0,
                "warmth": 0.0,
                "goodness": 0.0,
                "helpfulness": 0.0,
            }
        if not self.memes:
            self.memes = {
                "worry": 0.0,
                "hope": 0.0,
                "confusion": 0.0,
                "joy": 0.0,
                "bond": 0.0,
                "pride": 0.0,
            }

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
    place: str = "the small kitchen"
    table: str = "the wooden table"
    kind: str = "home"
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
class Cut:
    id: str
    label: str
    phrase: str
    quality: str
    needs_help: bool = True
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
class MealPlan:
    id: str
    dish: str
    serving: str
    smell: str
    warmth: str
    keyword: str = "meat"
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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the small kitchen", table="the wooden table", kind="home"),
    "picnic": Setting(place="the sunny picnic blanket", table="the red-checkered blanket", kind="outdoors"),
    "school": Setting(place="the cozy school lunchroom", table="the long lunch table", kind="school"),
}

CUTS = {
    "humble": Cut(
        id="humble",
        label="humble meat",
        phrase="a humble cut of meat",
        quality="simple",
    ),
    "thin": Cut(
        id="thin",
        label="thin meat slices",
        phrase="thin slices of meat",
        quality="light",
    ),
    "leftover": Cut(
        id="leftover",
        label="leftover meat",
        phrase="leftover meat from yesterday",
        quality="saved",
    ),
}

PLANS = {
    "stew": MealPlan(
        id="stew",
        dish="stew",
        serving="a warm bowl of stew",
        smell="rich",
        warmth="steaming",
        keyword="meat",
    ),
    "sandwich": MealPlan(
        id="sandwich",
        dish="sandwiches",
        serving="soft sandwiches",
        smell="toasty",
        warmth="fresh",
        keyword="meat",
    ),
    "skewers": MealPlan(
        id="skewers",
        dish="skewers",
        serving="tiny skewers",
        smell="savory",
        warmth="warm",
        keyword="meat",
    ),
}

NAMES = {
    "girl": ["Mina", "Lena", "Sage", "Ivy", "Nora"],
    "boy": ["Eli", "Milo", "Theo", "Jasper", "Finn"],
}

PARENTS = ["mother", "father"]

TRAITS = ["kind", "curious", "careful", "gentle", "thoughtful"]


# ---------------------------------------------------------------------------
# Core reasoning
# ---------------------------------------------------------------------------
def meat_is_small_and_humble(cut: Cut, plan: MealPlan) -> bool:
    return cut.id in {"humble", "thin", "leftover"} and plan.id in {"stew", "sandwich", "skewers"}


def will_misunderstand(child: Entity, cut: Cut) -> bool:
    return child.memes["confusion"] >= 1.0 and cut.quality in {"simple", "light", "saved"}


def can_fix_with_teamwork(cut: Cut, plan: MealPlan) -> bool:
    return meat_is_small_and_humble(cut, plan)


def warn_reason(cut: Cut) -> str:
    return f"The meat looked plain, and someone might think it was inferior because it was so simple."


def explain_word_in_story() -> str:
    return (
        "The word inferior can mean lower in quality, but it can also mean less special "
        "or less grand. In this story, the grown-up helps the child understand that simple "
        "food can still be good and made with love."
    )


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def tell_intro(world: World, child: Entity, parent: Entity, cut: Entity, plan: MealPlan) -> None:
    world.say(
        f"{child.id} was a {child.memes.get('trait', 'kind')} little {child.type} who loved helping in the kitchen."
    )
    world.say(
        f"One day, {parent.pronoun('possessive')} {parent.label} brought home {cut.phrase} for {plan.serving}."
    )
    world.say(
        f"{child.id} peeked at the pan and wondered if the meat was too plain to be any good."
    )


def generate_misunderstanding(world: World, child: Entity, parent: Entity, cut: Entity, plan: MealPlan) -> None:
    child.memes["confusion"] += 1
    child.memes["worry"] += 1
    world.say(
        f'"Is this meat inferior?" {child.id} asked softly, looking up at {parent.id}.'
    )
    world.say(
        f'{parent.id} paused, then smiled kindly. "It looks simple, but simple does not mean bad," '
        f'{parent.pronoun("subject")} said.'
    )


def dialogue(world: World, child: Entity, parent: Entity, cut: Entity, plan: MealPlan) -> None:
    child.memes["confusion"] = max(0.0, child.memes["confusion"] - 1.0)
    child.memes["hope"] += 1
    parent.memes["bond"] += 1
    world.say(
        f'"Inferior means less grand," {parent.id} explained, "but this meat can still become something warm and tasty."'
    )
    world.say(
        f'{child.id} listened closely. "{parent.id}, can I help make it better?" {child.id} asked.'
    )


def teamwork(world: World, child: Entity, parent: Entity, cut: Entity, plan: MealPlan) -> None:
    if not can_fix_with_teamwork(cut, plan):
        pass

    cut.held_by = child.id
    cut.cooked = True
    cut.improved = True
    cut.meters["goodness"] += 2.0
    cut.meters["warmth"] += 1.0

    child.memes["joy"] += 1
    child.memes["pride"] += 1
    parent.memes["joy"] += 1
    parent.memes["bond"] += 1

    world.say(
        f'Together they stirred, tasted, and set the table. {child.id} sprinkled herbs while {parent.id} turned the meat gently.'
    )
    world.say(
        f'Soon the kitchen smelled {plan.smell}, and the meal became {plan.serving} instead of just a plain piece of meat.'
    )


def ending(world: World, child: Entity, parent: Entity, cut: Entity, plan: MealPlan) -> None:
    child.memes["worry"] = 0.0
    child.memes["confusion"] = 0.0
    world.say(
        f'{child.id} took a bite and grinned. "It is not inferior at all," {child.id} said. "It is delicious because we made it together."'
    )
    world.say(
        f'{parent.id} laughed and nudged {child.id} toward {plan.serving}. At {world.setting.table}, the humble meat had become a happy meal.'
    )


def build_world(params) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.trait,
        membranes=None if False else None,
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label="parent",
    ))
    cut = world.add(Entity(
        id="Meat",
        kind="thing",
        type="food",
        label=_safe_lookup(CUTS, params.cut).label,
        phrase=_safe_lookup(CUTS, params.cut).phrase,
        owner=parent.id,
    ))
    plan = _safe_lookup(PLANS, params.plan)

    child.memes["trait"] = 0.0  # type: ignore[index]
    # Inject readable trait in a side channel for narration only.
    world.facts["trait"] = params.trait

    tell_intro(world, child, parent, cut, plan)
    world.para()
    generate_misunderstanding(world, child, parent, cut, plan)
    dialogue(world, child, parent, cut, plan)
    world.para()
    teamwork(world, child, parent, cut, plan)
    ending(world, child, parent, cut, plan)

    world.facts.update(
        child=child,
        parent=parent,
        cut=cut,
        plan=plan,
        setting=world.setting,
        resolved=True,
        misunderstanding=True,
    )
    return world


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    cut: str
    plan: str
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
    ap = argparse.ArgumentParser(
        description="A heartwarming story world about misunderstanding, dialogue, and teamwork."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cut", choices=CUTS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--name")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for cut in CUTS:
            for plan in PLANS:
                if meat_is_small_and_humble(_safe_lookup(CUTS, cut), _safe_lookup(PLANS, plan)):
                    combos.append((setting, cut, plan))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "cut", None):
        combos = [c for c in combos if c[1] == getattr(args, "cut", None)]
    if getattr(args, "plan", None):
        combos = [c for c in combos if c[2] == getattr(args, "plan", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting, cut, plan = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, cut=cut, plan=plan, name=name, gender=gender, parent=parent, trait=trait)


# ---------------------------------------------------------------------------
# Story generation and QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    cut = _safe_fact(world, f, "cut")
    plan = _safe_fact(world, f, "plan")
    trait = _safe_fact(world, f, "trait")
    return [
        f'Write a heartwarming story about a {trait} child who misunderstands the word "inferior" while helping cook meat.',
        f"Tell a gentle story where {child.id} worries that {cut.label} is inferior, but {plan.serving} is made through dialogue and teamwork.",
        f"Write a short child-friendly story that begins with a misunderstanding about meat and ends with everyone feeling proud.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    cut = _safe_fact(world, f, "cut")
    plan = _safe_fact(world, f, "plan")
    trait = _safe_fact(world, f, "trait")

    return [
        QAItem(
            question=f"Why did {child.id} worry when {parent.id} brought home {cut.phrase}?",
            answer=(
                f"{child.id} thought the meat might be inferior because it looked simple and plain. "
                f"{parent.id} gently explained that simple food can still be good."
            ),
        ),
        QAItem(
            question=f"What helped {child.id} understand the meal better?",
            answer=(
                f"Their dialogue helped. {parent.id} explained the word inferior, and {child.id} listened and asked to help."
            ),
        ),
        QAItem(
            question=f"What did teamwork change about the meat and the meal?",
            answer=(
                f"Teamwork turned {cut.phrase} into {plan.serving}. {child.id} and {parent.id} cooked together, "
                f"so the meal became warm, tasty, and something they both felt proud of."
            ),
        ),
        QAItem(
            question=f"How did {child.id} feel at the end of the story?",
            answer=(
                f"{child.id} felt happy, proud, and close to {parent.id}. The misunderstanding was gone, and the meal felt special because they made it together."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does inferior usually mean?",
            answer=(
                "Inferior usually means lower in quality or not as good as something else. "
                "Sometimes people also use it to mean less grand or less special."
            ),
        ),
        QAItem(
            question="Why can simple food still be nice?",
            answer=(
                "Simple food can still be nice because it can be fresh, warm, and cooked with care. "
                "Good company and teamwork can make it feel special too."
            ),
        ),
        QAItem(
            question="What is teamwork?",
            answer=(
                "Teamwork is when people help each other to do something together. "
                "Each person can do a small part, and those small parts make one bigger result."
            ),
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer=(
                "A misunderstanding happens when someone thinks something means one thing, but it really means something else. "
                "A kind explanation can clear it up."
            ),
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
    for e in list(world.entities.values()):
        m = {k: v for k, v in e.meters.items() if v}
        s = {k: v for k, v in e.memes.items() if v and k != "trait"}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if s:
            bits.append(f"memes={s}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A meal is compatible when the humble meat can be improved by teamwork.
meat_kind(humble).
meat_kind(thin).
meat_kind(leftover).

supports_teamwork(stew).
supports_teamwork(sandwich).
supports_teamwork(skewers).

valid(setting, cut, plan) :- meat_kind(cut), supports_teamwork(plan).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CUTS:
        lines.append(asp.fact("cut", cid))
    for pid in PLANS:
        lines.append(asp.fact("plan", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Sample selection
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="kitchen", cut="humble", plan="stew", name="Mina", gender="girl", parent="mother", trait="gentle"),
    StoryParams(setting="picnic", cut="thin", plan="sandwich", name="Eli", gender="boy", parent="father", trait="curious"),
    StoryParams(setting="school", cut="leftover", plan="skewers", name="Nora", gender="girl", parent="mother", trait="thoughtful"),
]


def explain_rejection() -> str:
    return "(No story: this world only tells heartwarming stories where simple meat can be improved through teamwork.)"


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print("  ", row)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.cut} meat in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
