#!/usr/bin/env python3
"""
storyworlds/worlds/gin_dime_friendship_comedy.py
=================================================

A tiny comedy story world about two friends, a dime, and a silly misunderstanding.

Premise:
- Two friends are having an ordinary day together.
- They find a dime and treat it like a treasure.
- One friend makes a goofy plan that nearly goes wrong.
- Their friendship fixes the problem, and the ending lands on a funny, warm image.

The world keeps track of:
- physical meters: coin ownership, dirt, wetness, distance, and prop placement
- emotional memes: joy, worry, embarrassment, and friendship
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    a: object | None = None
    b: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def obj_pronoun(self) -> str:
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
    place: str = "the playground"
    indoor: bool = False
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
class FriendshipProp:
    id: str
    label: str
    phrase: str
    use: str
    funny_result: str
    risk: str
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
class StoryParams:
    place: str
    prop: str
    name_a: str
    name_b: str
    type_a: str
    type_b: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def friend_name_pool(gender: str) -> list[str]:
    if gender == "girl":
        return ["Gin", "Mia", "Nora", "Lia", "Mona", "Bea", "Tess"]
    return ["Max", "Ben", "Noah", "Finn", "Theo", "Sam", "Kai"]


SETTINGS = {
    "park": Setting(place="the park", indoor=False, affords={"dime", "river"}),
    "bench": Setting(place="the old bench by the path", indoor=False, affords={"dime"}),
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"dime"}),
    "library": Setting(place="the library steps", indoor=False, affords={"dime"}),
}

PROPS = {
    "dime": FriendshipProp(
        id="dime",
        label="dime",
        phrase="a shiny dime",
        use="buy one tiny snack together",
        funny_result="a paper cup of lemonade and one very dramatic cookie",
        risk="roll away like a sneaky marble",
        tags={"coin", "money", "shiny", "friendship"},
    ),
    "gin": FriendshipProp(
        id="gin",
        label="gin bottle",
        phrase="a bottle labeled gin",
        use="return it to the grown-up shelf",
        funny_result="a very confused cough and a stern label",
        risk="look like a forbidden soup ingredient",
        tags={"label", "bottle", "friendship"},
    ),
}

GENDERS = {"girl", "boy"}
GIRL_NAMES = friend_name_pool("girl")
BOY_NAMES = friend_name_pool("boy")


def valid_combos() -> list[tuple[str, str]]:
    return [(place, prop) for place, s in SETTINGS.items() for prop in s.affords if prop in PROPS]


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_roll_away(world: World) -> list[str]:
    out: list[str] = []
    dime = world.entities.get("dime")
    if not dime or dime.meters.get("rolling", 0) < THRESHOLD:
        return out
    if ("roll", dime.id) in world.fired:
        return out
    world.fired.add(("roll", dime.id))
    dime.meters["distance"] = dime.meters.get("distance", 0) + 1
    out.append("The dime rolled farther away, as if it had its own little joke.")
    return out


def _r_friendship_fix(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("A")
    b = world.get("B")
    dime = world.get("dime")
    if dime.meters.get("lost", 0) < THRESHOLD:
        return out
    if a.memes.get("friendship", 0) < THRESHOLD or b.memes.get("friendship", 0) < THRESHOLD:
        return out
    sig = ("fix",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    dime.meters["lost"] = 0
    dime.owner = a.id
    out.append("Their friendship turned the chase into a laugh, and the dime was found again.")
    return out


CAUSAL_RULES = [
    Rule("roll", _r_roll_away),
    Rule("fix", _r_friendship_fix),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def setup_world(setting: Setting, prop: FriendshipProp, name_a: str, name_b: str,
                type_a: str, type_b: str) -> World:
    world = World(setting)
    a = world.add(Entity(id="A", kind="character", type=type_a, label=name_a))
    b = world.add(Entity(id="B", kind="character", type=type_b, label=name_b))
    item = world.add(Entity(id=prop.id, type=prop.id, label=prop.label, phrase=prop.phrase, owner="A"))
    world.facts.update(a=a, b=b, item=item, prop=prop)
    return world


def introduce(world: World) -> None:
    a, b = world.get("A"), world.get("B")
    world.say(f"{a.label} and {b.label} were best friends who could turn almost anything into a game.")


def find_prop(world: World, prop: FriendshipProp) -> None:
    a, b, item = world.get("A"), world.get("B"), world.get(prop.id)
    item.owner = a.id
    item.meters["found"] = 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"One day, they found {prop.phrase} near {world.setting.place}. "
        f"{a.label} said it looked important, and {b.label} said it looked silly enough to be important."
    )


def make_plan(world: World, prop: FriendshipProp) -> None:
    a, b, item = world.get("A"), world.get("B"), world.get(prop.id)
    a.memes["curiosity"] = a.memes.get("curiosity", 0) + 1
    b.memes["curiosity"] = b.memes.get("curiosity", 0) + 1
    world.say(
        f"They decided to {prop.use}. {a.label} held {item.obj_pronoun()} up like a treasure, "
        f"and {b.label} bowed to it like it was royalty."
    )


def complication(world: World, prop: FriendshipProp) -> None:
    a, b, item = world.get("A"), world.get("B"), world.get(prop.id)
    item.meters["rolling"] = 1
    item.meters["lost"] = 1
    a.memes["worry"] = a.memes.get("worry", 0) + 1
    b.memes["worry"] = b.memes.get("worry", 0) + 1
    world.say(
        f"Then the plan went wobbly. {a.label} tapped the {item.label}, and it {prop.risk}. "
        f"{b.label} made a face so serious it was almost funny."
    )
    propagate(world, narrate=True)


def recover(world: World, prop: FriendshipProp) -> None:
    a, b, item = world.get("A"), world.get("B"), world.get(prop.id)
    if item.meters.get("lost", 0) >= THRESHOLD:
        world.say(
            f"{b.label} reached under a bench, {a.label} pointed, and together they scooped it up before it could disappear."
        )
        item.meters["lost"] = 0
        item.owner = a.id
    a.memes["friendship"] = a.memes.get("friendship", 0) + 1
    b.memes["friendship"] = b.memes.get("friendship", 0) + 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"They laughed at the whole mess. In the end, {a.label} kept the {prop.label}, {b.label} kept the joke, "
        f"and their friendship kept both of them smiling."
    )


def tell(setting: Setting, prop: FriendshipProp, name_a: str, name_b: str,
         type_a: str, type_b: str) -> World:
    world = setup_world(setting, prop, name_a, name_b, type_a, type_b)
    introduce(world)
    world.para()
    find_prop(world, prop)
    make_plan(world, prop)
    world.para()
    complication(world, prop)
    recover(world, prop)
    return world


def valid_story_for(setting_key: str, prop_key: str) -> bool:
    return prop_key in _safe_lookup(SETTINGS, setting_key).affords and prop_key in PROPS


def explain_rejection(setting_key: str, prop_key: str) -> str:
    return f"(No story: {prop_key} is not a reasonable prop for {setting_key} in this tiny world.)"


def pick_name(rng: random.Random, gender: str) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small comedic friendship storyworld about a dime and a silly prop.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--type-a", choices=["girl", "boy"])
    ap.add_argument("--type-b", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "prop", None) is None or c[1] == getattr(args, "prop", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, prop = rng.choice(list(combos))
    type_a = getattr(args, "type_a", None) or rng.choice(["girl", "boy"])
    type_b = getattr(args, "type_b", None) or rng.choice(["girl", "boy"])
    name_a = getattr(args, "name_a", None) or pick_name(rng, type_a)
    name_b = getattr(args, "name_b", None) or pick_name(rng, type_b)
    if name_a == name_b:
        name_b = pick_name(rng, type_b)
    return StoryParams(place=place, prop=prop, name_a=name_a, name_b=name_b, type_a=type_a, type_b=type_b)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(PROPS, params.prop), params.name_a, params.name_b, params.type_a, params.type_b)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    prop = _safe_fact(world, world.facts, "prop")
    a, b = world.facts["a"], world.facts["b"]
    return [
        f"Write a funny friendship story for young children that includes the words '{prop.id}' and 'dime'.",
        f"Tell a short comedy about two friends, {a.label} and {b.label}, who find {prop.phrase} and try to handle it together.",
        f"Write a gentle, silly story where friendship helps after a small problem with {prop.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a, b, prop = world.facts["a"], world.facts["b"], world.facts["prop"]
    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The two friends were {a.label} and {b.label}. They stayed together the whole time.",
        ),
        QAItem(
            question=f"What did they find?",
            answer=f"They found {prop.phrase}, and it turned into a silly little adventure.",
        ),
        QAItem(
            question=f"Why did the story become funny?",
            answer=f"It became funny because the plan wobbled, the {prop.label} tried to get away, and the friends kept laughing instead of giving up.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {a.label} and {b.label} smiling together while the {prop.label} stayed safely with them.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dime?",
            answer="A dime is a small coin. People can use coins to buy tiny things, save money, or make a wish in a playful story.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the warm feeling and trust between people who like to help, share, and spend time together.",
        ),
        QAItem(
            question="Why can a small coin roll away?",
            answer="A small coin can roll away because it is light and round, so a little push can send it skittering across a surface.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
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
        lines.append(f"  {e.id:6} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
friend(A). friend(B) :- char(A), char(B), A != B.
found_dime(D) :- item(D), dime(D).
risk_roll(D) :- found_dime(D), round(D).
friendship_fix(A,B,D) :- friend(A), friend(B), found_dime(D), friendship(A,B).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
        for prop in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, prop))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("item", pid))
        lines.append(asp.fact("label", pid, prop.label))
        for tag in sorted(prop.tags):
            lines.append(asp.fact("tag", pid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show setting/1."))
    if not model:
        print("ASP produced no model.")
        return 1
    print(f"OK: ASP loaded {len(model)} shown atoms.")
    return 0


CURATED = [
    StoryParams(place="park", prop="dime", name_a="Gin", name_b="Max", type_a="girl", type_b="boy"),
    StoryParams(place="bench", prop="dime", name_a="Mia", name_b="Theo", type_a="girl", type_b="boy"),
    StoryParams(place="kitchen", prop="dime", name_a="Lia", name_b="Sam", type_a="girl", type_b="boy"),
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
        print(asp_program("#show setting/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show setting/1."))
        print(f"ASP model has {len(model)} shown atoms.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name_a} and {p.name_b} at {p.place} with {p.prop}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
