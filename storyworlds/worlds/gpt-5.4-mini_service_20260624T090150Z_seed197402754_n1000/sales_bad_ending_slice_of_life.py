#!/usr/bin/env python3
"""
Storyworld: a small slice-of-life sales day with a gentle bad ending.

Seed tale sketch:
---
A child helps at a little neighborhood sale stand. They set out neat items,
wait for customers, and hope the day will go well. The child wants to make a
few sales, but the street stays quiet and the useful little plan doesn't work.
By the end, the stand is packed away with the same unsold things, and the child
goes home a little disappointed but still thoughtful.

World model:
---
- A child, a helper adult, a small sales stand, and one featured item.
- The item is meant to be sold during a small neighborhood sale.
- Customers may browse, but the world can end in a bad ending: no sale.
- Emotional meters track hope, patience, disappointment, and pride.
- Physical meters track stock, coins, and whether the stand is packed.

Narrative shape:
---
Beginning: setup the stand and the item for sale.
Middle: the child waits and tries to attract a buyer.
Turn: the sale fails or nearly fails.
Ending: the stand is packed up; the unsold item proves what changed.
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

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    stand: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
    place: str = "the front sidewalk"
    weather: str = "mild"
    afford_sales: bool = True
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
class SaleItem:
    id: str
    label: str
    phrase: str
    price: int
    category: str
    value: str
    tags: set[str] = field(default_factory=set)
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
class SalesPlan:
    name: str
    type: str
    trait: str
    helper: str
    goal: str
    world: object | None = None
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


def tock(world: World, key: str, amount: float = 1.0) -> None:
    world.facts[key] = world.facts.get(key, 0.0) + amount


def maybe_pack_up(world: World) -> None:
    stand = world.get("stand")
    stand.meters["packed"] = 1.0
    world.say("At last, it was time to fold the table, stack the signs, and carry the box back inside.")


def attempt_sale(world: World, hero: Entity, helper: Entity, item: Entity) -> bool:
    # A quiet, realistic sale day: people may pass, but the final sale can fail.
    chance = world.facts.get("sale_chance", 0.2)
    roll = world.facts.get("roll", 1.0)
    if roll < chance:
        hero.meters["sales"] += 1
        hero.memes["joy"] += 1
        item.meters["sold"] = 1
        world.say(f"A neighbor stopped, smiled, and bought {hero.pronoun('possessive')} {item.label}.")
        return True
    hero.memes["hope"] -= 1
    hero.memes["disappointment"] += 1
    world.say(f"No one stopped for {hero.pronoun('possessive')} {item.label}, even after {hero.pronoun()} stood up straight and waved.")
    return False


def predict_bad_ending(world: World, hero: Entity, item: Entity) -> bool:
    sim = world.copy()
    sim.facts["roll"] = 0.95
    sold = attempt_sale(sim, sim.get(hero.id), sim.get("helper"), sim.get(item.id))
    return not sold


def setup_story(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    world.say(f"{hero.id} helped {helper.label} set up a tiny sales stand on {world.setting.place}.")
    world.say(f"They lined up {hero.pronoun('possessive')} {item.label} so it would look neat and easy to buy.")
    hero.memes["hope"] += 1
    hero.memes["pride"] += 1
    tock(world, "set_up", 1)


def waiting_beat(world: World, hero: Entity, item: Entity) -> None:
    world.para()
    world.say(f"{hero.id} waited by the stand and listened for footsteps on the sidewalk.")
    world.say(f"{hero.pronoun().capitalize()} kept {hero.pronoun('possessive')} hands folded so the {item.label} would not get dusty.")
    hero.memes["patience"] += 1
    tock(world, "waited", 1)


def bad_turn(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    world.para()
    world.say(f"An hour passed, then another, but the little sales day stayed slow.")
    if predict_bad_ending(world, hero, item):
        world.say(f"{helper.label} looked at the quiet street and said the kindest thing: 'Sometimes a sale just doesn't happen.'")
    sold = attempt_sale(world, hero, helper, item)
    if not sold:
        hero.memes["defeat"] += 1
        helper.memes["sympathy"] += 1


def ending_image(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    world.para()
    maybe_pack_up(world)
    hero.memes["hope"] = max(0.0, hero.memes.get("hope", 0.0) - 1)
    world.say(f"{hero.id} carried the unsold {item.label} inside while {helper.label} folded the table with slow, careful hands.")
    world.say(f"The {item.label} was still there at the end, bright and tidy, only waiting for a better day.")


def tell(setting: Setting, plan: SalesPlan, item_cfg: SaleItem) -> World:
    world = World(setting)

    hero = world.add(Entity(id=plan.name, kind="character", type=plan.type))
    helper = world.add(Entity(id="helper", kind="character", type=plan.helper, label=plan.helper))
    item = world.add(Entity(id="item", type=item_cfg.category, label=item_cfg.label, phrase=item_cfg.phrase, owner=hero.id))
    stand = world.add(Entity(id="stand", type="stand", label="the sales stand"))

    hero.memes["hope"] = 1.0
    hero.memes["patience"] = 0.0
    hero.memes["disappointment"] = 0.0
    hero.memes["pride"] = 0.0
    helper.memes["patience"] = 1.0
    stand.meters["stock"] = 1.0

    world.facts.update(
        hero=hero,
        helper=helper,
        item=item,
        stand=stand,
        plan=plan,
        item_cfg=item_cfg,
        sale_chance=0.15,
        roll=0.95,  # bias toward the bad ending
        bad_ending=True,
    )

    setup_story(world, hero, helper, item)
    waiting_beat(world, hero, item)
    bad_turn(world, hero, helper, item)
    ending_image(world, hero, helper, item)

    return world


SETTINGS = {
    "sidewalk": Setting(place="the front sidewalk", weather="mild", afford_sales=True),
    "porch": Setting(place="the porch", weather="mild", afford_sales=True),
    "garage": Setting(place="the garage door", weather="warm", afford_sales=True),
}

ITEMS = {
    "book": SaleItem(
        id="book",
        label="picture book",
        phrase="a picture book with bright pages",
        price=2,
        category="book",
        value="bright",
        tags={"paper", "book", "quiet"},
    ),
    "toy": SaleItem(
        id="toy",
        label="toy car",
        phrase="a little red toy car",
        price=3,
        category="toy",
        value="small",
        tags={"toy", "play"},
    ),
    "lamp": SaleItem(
        id="lamp",
        label="table lamp",
        phrase="a small table lamp with a yellow shade",
        price=5,
        category="lamp",
        value="useful",
        tags={"home", "light"},
    ),
    "mug": SaleItem(
        id="mug",
        label="mug",
        phrase="a blue mug with a chip on the handle",
        price=1,
        category="mug",
        value="kitchen",
        tags={"cup", "home"},
    ),
}

NAMES = ["Mina", "Eli", "Noah", "Sara", "Pia", "Owen", "Lina", "Tess"]
HELPERS = ["mother", "father", "grandma", "grandpa"]
TRAITS = ["careful", "hopeful", "quiet", "patient", "earnest"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for item in ITEMS:
            combos.append((place, "sale", item))
    return combos


@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    gender: str
    helper: str
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
    ap = argparse.ArgumentParser(description="Slice-of-life sales storyworld with a gentle bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    choices = valid_combos()
    if getattr(args, "place", None):
        choices = [c for c in choices if c[0] == getattr(args, "place", None)]
    if getattr(args, "item", None):
        choices = [c for c in choices if c[2] == getattr(args, "item", None)]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, _, item = rng.choice(choices)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, item=item, name=name, gender=gender, helper=helper, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    item = _safe_fact(world, f, "item_cfg")
    return [
        f'Write a short slice-of-life story about {hero.id} helping at a small sales stand with "{item.label}".',
        f"Tell a gentle everyday story where a child tries to make a sale but the stand stays quiet.",
        f'Write a simple story about a child, a sales table, and "{item.phrase}", ending in a bad ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    item = _safe_fact(world, f, "item_cfg")
    return [
        QAItem(
            question=f"What did {hero.id} help put out at the sales stand?",
            answer=f"{hero.id} helped put out {item.phrase} so it could be sold.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with the sales stand?",
            answer=f"{helper.label.capitalize()} helped {hero.id} with the small sales stand.",
        ),
        QAItem(
            question=f"Did {hero.id} make a sale at the end?",
            answer="No. The day ended badly, and the item stayed unsold.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a sale?", answer="A sale is when someone buys something for money."),
        QAItem(question="Why do people set up a stand?", answer="People set up a stand to show things they want to sell."),
        QAItem(question="What does it mean if something is unsold?", answer="Unsold means nobody bought it yet."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), SalesPlan(name=params.name, type=params.gender, trait=params.trait, helper=params.helper, goal="sell the item"), _safe_lookup(ITEMS, params.item))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"facts={world.facts}")
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


ASP_RULES = r"""
place(P) :- setting(P).
item(I) :- sale_item(I).
valid_story(P,I) :- place(P), item(I).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for i in ITEMS:
        lines.append(asp.fact("sale_item", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, i) for p, _, i in valid_combos()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("Mismatch:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="sidewalk", item="book", name="Mina", gender="girl", helper="mother", trait="quiet"),
            StoryParams(place="porch", item="toy", name="Eli", gender="boy", helper="father", trait="patient"),
            StoryParams(place="garage", item="mug", name="Sara", gender="girl", helper="grandma", trait="hopeful"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], ensure_ascii=False, indent=2))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
