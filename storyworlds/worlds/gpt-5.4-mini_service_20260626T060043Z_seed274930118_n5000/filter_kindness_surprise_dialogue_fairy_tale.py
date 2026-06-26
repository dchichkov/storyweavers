#!/usr/bin/env python3
"""
storyworlds/worlds/filter_kindness_surprise_dialogue_fairy_tale.py
===================================================================

A tiny fairy-tale storyworld about a magical filter that only lets kind
offerings, kind words, and gentle surprises through the castle gate.

Premise:
A child and a fairy-tale keeper discover that the old silver filter at the
bridge can sort through tangled wishes. When a rude plan is blocked, a kinder
choice slips through, and a surprise gift appears with a little dialogue.

The world model tracks:
- physical meters: things like blocked, open, carried, sparkling, hidden
- emotional memes: things like kindness, surprise, worry, delight, trust

The simulated turn:
- a wish is tried
- the filter rejects unkindness
- a kinder dialogue opens the way
- a surprise gift arrives

This file follows the Storyweavers world contract and includes a Python
reasonableness gate plus an inline ASP twin.
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
# Domain registries
# ---------------------------------------------------------------------------

FAIRY_TALE_OPENERS = [
    "Once upon a time",
    "Long ago",
    "In a small kingdom of mist and roses",
    "On a moonlit morning",
]

CHARACTER_NAMES = ["Elsa", "Mira", "Tobin", "Iris", "Pip", "Anya", "Rowan", "Lina"]
ROLE_TYPES = ["girl", "boy", "princess", "prince", "page", "keeper", "woodcutter's child"]
HELPER_TYPES = ["fairy", "queen", "knight", "owl", "mouse", "baker"]
TRAITS = ["brave", "gentle", "curious", "kind-hearted", "bright-eyed", "hopeful"]

PLACES = {
    "bridge": "the old stone bridge",
    "gate": "the castle gate",
    "garden": "the rose garden",
    "well": "the wishing well",
}

GIFTS = {
    "apple": ("a red apple tied with ribbon", "apple"),
    "cloak": ("a soft blue cloak", "cloak"),
    "bread": ("a warm loaf of bread", "bread"),
    "lantern": ("a little brass lantern", "lantern"),
}

WISHES = {
    "take": ("take the gift without asking", "grab"),
    "share": ("share the gift with the helper", "offer"),
    "thank": ("thank the helper before leaving", "thank"),
    "help": ("help the helper carry a bundle", "carry"),
}

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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    open: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    gate: object | None = None
    helper: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "fairy"}
        male = {"boy", "prince", "king", "father", "woodcutter", "knight"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str
    name: str
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
class Wish:
    id: str
    phrase: str
    verb: str
    kind: str
    surprise: str
    requires_dialogue: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Gift:
    id: str
    label: str
    phrase: str
    surprise: str
    kind: str
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


THRESHOLD = 1.0


def _have(entity: Entity, meter: str) -> bool:
    return entity.meters.get(meter, 0.0) >= THRESHOLD


def _feel(entity: Entity, meme: str, value: float = 1.0) -> None:
    entity.memes[meme] = entity.memes.get(meme, 0.0) + value


# ---------------------------------------------------------------------------
# Reasonable story gate
# ---------------------------------------------------------------------------

def wish_needs_dialogue(wish: Wish) -> bool:
    return wish.requires_dialogue


def dialogue_is_kind(dialogue: str) -> bool:
    lowered = dialogue.lower()
    return any(word in lowered for word in ("please", "thank", "help", "kind", "sorry", "may"))


def surprise_fits_gift(gift: Gift, wish: Wish) -> bool:
    return gift.surprise in wish.surprise


def valid_combo(place: str, wish_id: str, gift_id: str) -> bool:
    wish = WISH_REGISTRY[wish_id]
    gift = GIFT_REGISTRY[gift_id]
    return wish_needs_dialogue(wish) and surprise_fits_gift(gift, wish) and place in PLACES


def explain_rejection(wish_id: str, gift_id: str) -> str:
    wish = WISH_REGISTRY[wish_id]
    gift = GIFT_REGISTRY[gift_id]
    return (
        f"(No story: {wish.phrase} needs a dialogue turn, and {gift.label} does not fit "
        f"that surprise well. Choose a wish that can be softened by kind words.)"
    )


# ---------------------------------------------------------------------------
# Story acts
# ---------------------------------------------------------------------------

def introduce(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    trait = next((t for t in child.traits if t != "little"), "kind")
    world.say(
        f"{_safe_lookup(FAIRY_TALE_OPENERS, 0)}, there was a little {trait} {child.type} named {child.id} "
        f"who loved the hush of {setting.name}."
    )
    world.say(
        f"At the gate lived {helper.id}, who kept an old silver filter that could sort "
        f"kind wishes from sharp ones."
    )


def desire(world: World, child: Entity, wish: Wish, gift: Gift) -> None:
    _feel(child, "hope", 1)
    world.say(
        f"{child.id} saw {gift.phrase} and wanted to {wish.phrase}."
    )


def test_filter(world: World, child: Entity, helper: Entity, wish: Wish, gift: Gift) -> bool:
    # The magical filter prefers kindness and dialogue.
    if wish.kind != "kind":
        _feel(child, "worry", 1)
        world.say(
            f'The silver filter hummed, "No, no, not yet," and its rim stayed closed.'
        )
        return False
    if not dialogue_is_kind(wish.phrase):
        _feel(child, "worry", 1)
        world.say(
            f'The filter twinkled, but it would not open for a wish without kind words.'
        )
        return False
    _feel(child, "trust", 1)
    world.say(
        f'{helper.id} smiled and said, "Try again with a gentler voice."'
    )
    world.say(
        f'{child.id} took a breath and answered, "Please may I {wish.phrase}?"'
    )
    return True


def surprise(world: World, child: Entity, helper: Entity, wish: Wish, gift: Gift) -> None:
    child.meters["open"] = 1
    helper.meters["open"] = 1
    child.memes["surprise"] = child.memes.get("surprise", 0.0) + 1
    child.memes["delight"] = child.memes.get("delight", 0.0) + 1
    world.say(
        f"At once, the filter parted like a flower, and a hidden latch clicked open."
    )
    world.say(
        f"Inside was {gift.phrase}, waiting as a surprise for {child.id}."
    )
    world.say(
        f'{child.id} gasped, then laughed. "{gift.surprise}!" {child.pronoun()} said.'
    )


def resolve(world: World, child: Entity, helper: Entity, wish: Wish, gift: Gift) -> None:
    _feel(child, "kindness", 1)
    _feel(helper, "kindness", 1)
    world.say(
        f'{helper.id} said, "Kindness opened the gate, and kindness kept the gift bright."'
    )
    world.say(
        f"{child.id} thanked {helper.pronoun('object')} and shared the first sweet piece."
    )


# ---------------------------------------------------------------------------
# Inline screenplay
# ---------------------------------------------------------------------------

def tell_story(
    setting: Setting,
    wish: Wish,
    gift: Gift,
    child_name: str = "Elsa",
    child_type: str = "girl",
    helper_name: str = "Mira",
    helper_type: str = "fairy",
    trait: str = "gentle",
) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        traits=["little", trait],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        traits=["kind", "patient"],
    ))
    gate = world.add(Entity(
        id="filter_gate",
        kind="thing",
        type="filter",
        label="silver filter",
        open=False,
        meters={"closed": 1},
        memes={"silence": 1},
    ))
    prize = world.add(Entity(
        id=gift.id,
        kind="thing",
        type=gift.id,
        label=gift.label,
        phrase=gift.phrase,
        owner=helper.id,
    ))

    introduce(world, child, helper, setting)
    world.para()
    desire(world, child, wish, gift)
    if not test_filter(world, child, helper, wish, gift):
        world.say(f"{child.id} frowned, then tried again with softer hands.")
        world.say(
            f'This time {child.id} said, "Please may I {wish.phrase}?"'
        )
        world.say(
            f"The silver filter listened."
        )
    world.para()
    surprise(world, child, helper, wish, prize)
    world.para()
    resolve(world, child, helper, wish, prize)

    world.facts.update(
        child=child,
        helper=helper,
        gate=gate,
        gift=prize,
        wish=wish,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "bridge": Setting(place="bridge", name="the old stone bridge"),
    "gate": Setting(place="gate", name="the castle gate"),
    "garden": Setting(place="garden", name="the rose garden"),
    "well": Setting(place="well", name="the wishing well"),
}

WISH_REGISTRY = {
    "share": Wish(
        id="share",
        phrase="share the gift with the helper",
        verb="share",
        kind="kind",
        surprise="gift",
    ),
    "thank": Wish(
        id="thank",
        phrase="thank the helper before leaving",
        verb="thank",
        kind="kind",
        surprise="gift",
    ),
    "help": Wish(
        id="help",
        phrase="help the helper carry a bundle",
        verb="help",
        kind="kind",
        surprise="bundle",
    ),
    "take": Wish(
        id="take",
        phrase="take the gift without asking",
        verb="take",
        kind="unkind",
        surprise="gift",
    ),
}

GIFT_REGISTRY = {
    "apple": Gift(
        id="apple",
        label="a red apple tied with ribbon",
        phrase="a red apple tied with ribbon",
        surprise="gift",
        kind="kind",
    ),
    "cloak": Gift(
        id="cloak",
        label="a soft blue cloak",
        phrase="a soft blue cloak",
        surprise="gift",
        kind="kind",
    ),
    "bread": Gift(
        id="bread",
        label="a warm loaf of bread",
        phrase="a warm loaf of bread",
        surprise="bundle",
        kind="kind",
    ),
    "lantern": Gift(
        id="lantern",
        label="a little brass lantern",
        phrase="a little brass lantern",
        surprise="gift",
        kind="kind",
    ),
}

CURATED = [
    ("bridge", "share", "apple"),
    ("gate", "thank", "cloak"),
    ("garden", "help", "bread"),
    ("well", "share", "lantern"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A wish is acceptable when it is kind and it calls for dialogue.
acceptable_wish(W) :- wish(W), kind_wish(W), needs_dialogue(W).

% A gift is a surprise fit if the gift's surprise type matches the wish.
fit(W, G) :- acceptable_wish(W), gift(G), surprise_of(G, S), surprise_of_wish(W, S).

% A story combo is valid when a place exists and both the wish and gift fit.
valid(Place, W, G) :- place(Place), acceptable_wish(W), fit(W, G).

#show valid/3.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for wid, w in WISH_REGISTRY.items():
        lines.append(asp.fact("wish", wid))
        if w.kind == "kind":
            lines.append(asp.fact("kind_wish", wid))
        if w.requires_dialogue:
            lines.append(asp.fact("needs_dialogue", wid))
        lines.append(asp.fact("surprise_of_wish", wid, w.surprise))
    for gid, g in GIFT_REGISTRY.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("surprise_of", gid, g.surprise))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted((place, w, g) for place in SETTINGS for w, g in [(wid, gid) for wid in WISH_REGISTRY for gid in GIFT_REGISTRY] if valid_combo(place, w, g))
    cl = asp_valid_combos()
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("python:", py)
    print("asp:", cl)
    return 1


# ---------------------------------------------------------------------------
# Params / generation / QA
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    wish: str
    gift: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None
    params: object | None = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about a magical filter of kindness and surprise.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--wish", choices=WISH_REGISTRY.keys())
    ap.add_argument("--gift", choices=GIFT_REGISTRY.keys())
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=ROLE_TYPES)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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
    combos = [
        (p, w, g)
        for p in SETTINGS
        for w in WISH_REGISTRY
        for g in GIFT_REGISTRY
        if valid_combo(p, w, g)
    ]
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "wish", None):
        combos = [c for c in combos if c[1] == getattr(args, "wish", None)]
    if getattr(args, "gift", None):
        combos = [c for c in combos if c[2] == getattr(args, "gift", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, wish, gift = rng.choice(list(combos))
    child_name = getattr(args, "name", None) or rng.choice(CHARACTER_NAMES)
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy", "princess", "prince"])
    helper_name = getattr(args, "helper_name", None) or rng.choice(CHARACTER_NAMES)
    helper_type = getattr(args, "helper_type", None) or rng.choice(HELPER_TYPES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        wish=wish,
        gift=gift,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
        trait=trait,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    wish = _safe_fact(world, f, "wish")
    gift = _safe_fact(world, f, "gift")
    return [
        f'Write a short fairy-tale story about a child named {child.id} who meets a filter at {world.setting.name}.',
        f"Tell a gentle story in which {child.id} learns that kindness opens the way to {gift.label}.",
        f'Write a fairy tale that includes dialogue, a surprise, and the word "filter".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    helper: Entity = _safe_fact(world, f, "helper")
    wish: Wish = _safe_fact(world, f, "wish")
    gift: Entity = _safe_fact(world, f, "gift")
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {child.id}, a little {child.type}, and {helper.id}, who keeps the silver filter at {setting.name}.",
        ),
        QAItem(
            question=f"What did {child.id} want to do?",
            answer=f"{child.id} wanted to {wish.phrase}, but needed to say it with kind words.",
        ),
        QAItem(
            question=f"What surprise appeared after the filter opened?",
            answer=f"A surprise gift appeared: {gift.phrase}.",
        ),
        QAItem(
            question=f"Why did the filter open at the end?",
            answer=f"It opened because {child.id} chose a kind, polite way to speak in dialogue.",
        ),
        QAItem(
            question=f"How did {child.id} feel when the gift appeared?",
            answer=f"{child.id} felt surprised, delighted, and thankful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a filter?",
            answer="A filter is something that lets some things pass through and holds other things back.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means treating others gently, helping them, and using caring words and actions.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that appears or happens when you are not ready for it.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is a conversation, with people speaking back and forth to each other.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.open:
            bits.append("open=True")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(
        _safe_lookup(SETTINGS, params.place),
        WISH_REGISTRY[params.wish],
        GIFT_REGISTRY[params.gift],
        child_name=params.child_name,
        child_type=params.child_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        trait=params.trait,
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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program())
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible combos:")
        for place, wish, gift in triples:
            print(f"  {place:8} {wish:8} {gift:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place, wish, gift in CURATED:
            params = StoryParams(
                place=place,
                wish=wish,
                gift=gift,
                child_name="Elsa",
                child_type="girl",
                helper_name="Mira",
                helper_type="fairy",
                trait="gentle",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
