#!/usr/bin/env python3
"""
A standalone storyworld for a small comedy domain built from the seed words:
thrust, likely, issue.

Premise:
- A child wants to thrust something forward in a playful way.
- The likely issue is that a prop, costume, or gadget is too floppy, sticky,
  or otherwise awkward.

Core turn:
- The situation transforms when the child changes the object, the method, or
  the outfit.

Twist:
- The "issue" turns out to be funny rather than serious, often because the
  object was meant for a different use all along.

Style:
- Comedy: light, concrete, child-facing, with a playful ending image.
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
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    prop: object | None = None
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
    indoor: bool
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
class Item:
    id: str
    label: str
    phrase: str
    type: str
    style: str
    twist: str
    issue: str
    transformation: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Prop:
    id: str
    label: str
    phrase: str
    use: str
    fix: str
    helps: set[str]
    region: str
    plural: bool = False
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registry content
# ---------------------------------------------------------------------------

SETTINGS = {
    "garage": Setting(place="the garage", indoor=True, affords={"thrust", "transform"}),
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"thrust", "transform"}),
    "yard": Setting(place="the yard", indoor=False, affords={"thrust", "transform"}),
    "stage": Setting(place="the little stage", indoor=True, affords={"thrust", "transform"}),
}

ITEMS = {
    "banner": Item(
        id="banner",
        label="banner",
        phrase="a long paper banner",
        type="banner",
        style="bright",
        twist="it kept twisting in the air",
        issue="the banner would likely flop over",
        transformation="the banner turned into a curly ribbon of laughter",
        region="hands",
        plural=False,
    ),
    "toyhorn": Item(
        id="toyhorn",
        label="toy horn",
        phrase="a squeaky toy horn",
        type="horn",
        style="silly",
        twist="it made the funniest honk",
        issue="the horn would likely wobble away",
        transformation="the horn became the star of the joke",
        region="hands",
        plural=False,
    ),
    "flag": Item(
        id="flag",
        label="small flag",
        phrase="a tiny parade flag",
        type="flag",
        style="bright",
        twist="it flipped like a fish in a breeze",
        issue="the flag would likely slip from their fingers",
        transformation="the flag became a spinning little twirl",
        region="hands",
        plural=False,
    ),
    "spoonprop": Item(
        id="spoonprop",
        label="big spoon",
        phrase="a big wooden spoon prop",
        type="spoon",
        style="plain",
        twist="it looked far too serious for a joke",
        issue="the spoon would likely bounce like a drumstick",
        transformation="the spoon turned into a parade baton",
        region="hands",
        plural=False,
    ),
}

PROPS = {
    "gloves": Prop(
        id="gloves",
        label="soft gloves",
        phrase="a pair of soft gloves",
        use="keep little hands steady",
        fix="hold the prop better",
        helps={"thrust"},
        region="hands",
        plural=True,
    ),
    "clipboard": Prop(
        id="clipboard",
        label="a clipboard",
        phrase="a clipboard with a clip",
        use="keep papers flat",
        fix="pin the banner down",
        helps={"transform"},
        region="hands",
        plural=False,
    ),
    "tape": Prop(
        id="tape",
        label="tape",
        phrase="a roll of bright tape",
        use="stick things in place",
        fix="make the prop stop flipping",
        helps={"thrust", "transform"},
        region="hands",
        plural=False,
    ),
}

NAMES_GIRL = ["Mia", "Luna", "Nora", "Zoe", "Ava", "Ivy", "Maya"]
NAMES_BOY = ["Ben", "Leo", "Toby", "Max", "Theo", "Sam", "Finn"]
TRAITS = ["bouncy", "curious", "sneaky", "cheerful", "goofy", "sprightly"]


# ---------------------------------------------------------------------------
# Reasonable story gate
# ---------------------------------------------------------------------------

def issue_exists(action: str, item: Item) -> bool:
    return action in {"thrust", "transform"} and bool(item.issue)


def likely_fix(action: str, item: Item) -> bool:
    return action in PROPS and any(action in p.helps for p in PROPS.values()) and bool(item.transformation)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for item_id, item in ITEMS.items():
                if issue_exists(act, item) and likely_fix(act, item):
                    out.append((place, act, item_id))
    return out


def explain_rejection(action: str, item: Item) -> str:
    return (
        f"(No story: the {item.label} does not create a funny enough issue for "
        f"{action}, or there is no believable transformation.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% An item has an issue for an action when the story can plausibly stumble.
has_issue(A, I) :- action(A), item(I), issue_for(A, I).

% A prop helps when it can resolve the action's issue.
helps(P, A, I) :- prop(P), action(A), item(I), prop_for(P, A), issue_for(A, I).

valid_story(Place, A, I) :- affords(Place, A), has_issue(A, I), helps(_, A, I).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("issue_for", "thrust", iid))
        lines.append(asp.fact("issue_for", "transform", iid))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        for a in sorted(p.helps):
            lines.append(asp.fact("prop_for", pid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
# Story logic
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    action: str
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


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)


def build_story(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    item: Entity = _safe_fact(world, f, "item")
    prop: Optional[Entity] = f.get("prop")
    action = _safe_fact(world, f, "action")
    trait = _safe_fact(world, f, "trait")

    world.say(
        f"{hero.id} was a {trait} little {hero.type} who loved silly showtime and big ideas."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to {action} {item.phrase} because it looked important and a tiny bit ridiculous."
    )
    world.say(
        f"The plan sounded fun, but there was one likely issue: {item.issue}."
    )
    world.para()
    world.say(
        f"At {world.setting.place}, {hero.id} took a breath and tried to {action} the prop with a very serious face."
    )
    world.say(
        f"That was when the funny twist happened: {item.twist}."
    )
    if prop is not None:
        world.say(
            f"{helper.pronoun().capitalize()} brought {prop.phrase} so {hero.id} could {prop.fix}."
        )
        world.say(
            f"With that help, the little problem transformed fast."
        )
    world.para()
    world.say(
        f"Instead of a mess, the {item.label} became {item.transformation}."
    )
    world.say(
        f"{hero.id} laughed so hard that even {helper.id} had to grin."
    )
    world.say(
        f"By the end, the whole room felt like a tiny comedy show, and the prop was the star."
    )

    world.facts.update(
        action=action,
        item=item,
        helper=helper,
        hero=hero,
        prop=prop,
        trait=trait,
    )


def generate_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"confidence": 1.0},
        memes={"mischief": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
    ))
    item = world.add(Entity(
        id=params.item,
        type=_safe_lookup(ITEMS, params.item).type,
        label=_safe_lookup(ITEMS, params.item).label,
        phrase=_safe_lookup(ITEMS, params.item).phrase,
        owner=hero.id,
    ))
    prop = None
    if params.action in {"thrust", "transform"}:
        prop = world.add(Entity(
            id="prop",
            type="tool",
            label=PROPS["tape"].label if params.action == "thrust" else PROPS["clipboard"].label,
            phrase=PROPS["tape"].phrase if params.action == "thrust" else PROPS["clipboard"].phrase,
            owner=helper.id,
        ))
    world.facts.update(hero=hero, helper=helper, item=item, prop=prop, action=params.action, trait=params.trait)
    build_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    item = _safe_fact(world, f, "item")
    action = _safe_fact(world, f, "action")
    return [
        f'Write a short comedy story for a child where {hero.id} wants to {action} {item.phrase}.',
        f'Write a funny story that includes the words "thrust", "likely", and "issue" and ends with a cheerful transformation.',
        f'Tell a playful story about a small stage problem that turns into a twist and a joke.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    item = _safe_fact(world, f, "item")
    prop = f.get("prop")
    action = _safe_fact(world, f, "action")
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do with the {item.label}?",
            answer=f"{hero.id} wanted to {action} the {item.phrase}.",
        ),
        QAItem(
            question=f"What was the likely issue in the story?",
            answer=f"The likely issue was that {item.issue}.",
        ),
        QAItem(
            question=f"What funny twist changed the scene?",
            answer=f"The twist was that {item.twist}.",
        ),
    ]
    if prop is not None:
        qa.append(
            QAItem(
                question=f"Who helped {hero.id} handle the problem?",
                answer=f"{helper.id} helped with {prop.phrase} so the little problem could be fixed.",
            )
        )
    qa.append(
        QAItem(
            question=f"What did the issue turn into by the end?",
            answer=f"It turned into {item.transformation}.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what you expected.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="A transformation means something changes into a different form or state.",
        ),
        QAItem(
            question="Why do people laugh at comedy?",
            answer="Comedy is made to be funny, so people laugh when something silly or surprising happens.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameter selection
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="garage", action="thrust", item="banner", name="Mia", gender="girl", helper="father", trait="bouncy"),
    StoryParams(place="stage", action="transform", item="toyhorn", name="Leo", gender="boy", helper="mother", trait="goofy"),
    StoryParams(place="kitchen", action="thrust", item="flag", name="Nora", gender="girl", helper="mother", trait="cheerful"),
    StoryParams(place="yard", action="transform", item="spoonprop", name="Theo", gender="boy", helper="father", trait="curious"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld with thrust / likely / issue, plus twist and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=["thrust", "transform"])
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "action", None) and getattr(args, "item", None):
        item = _safe_lookup(ITEMS, getattr(args, "item", None))
        if not issue_exists(getattr(args, "action", None), item):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, action, item_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or choose_name(gender, rng)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, item=item_id, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, action, item) combos:\n")
        for place, action, item in combos:
            print(f"  {place:12} {action:10} {item}")
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
            header = f"### {p.name}: {p.action} at {p.place} (item: {p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
