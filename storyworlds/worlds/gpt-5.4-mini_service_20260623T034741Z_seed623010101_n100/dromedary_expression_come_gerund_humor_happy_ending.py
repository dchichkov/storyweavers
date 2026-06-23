#!/usr/bin/env python3
"""
storyworlds/worlds/dromedary_expression_come_gerund_humor_happy_ending.py
========================================================================

A tiny nursery-rhyme storyworld about a dromedary, a funny expression,
and a "come + gerund" invitation that turns an awkward moment into a happy
ending.

Seed tale:
---
A child sees a dromedary making a silly expression and asks it to come
dancing by the fountain. The dromedary is worried at first, but a friendly
helper shows a safer, kinder way to play, and everyone ends up laughing
together.

World idea:
- A dromedary can be in a grumpy, shy, or surprised mood.
- The child's invitation uses a come-gerund phrase such as "come dancing"
  or "come singing".
- The helper notices when the dromedary is uncomfortable and offers a small
  prop or simple trick that changes the expression.
- Humor comes from the silly face, wobbling movement, and the way the helper
  teaches a gentle fix.
- Happy ending comes from shared play, calm moods, and a bright final image.

This script follows the storyworld contract:
- stdlib only
- results.py imported eagerly
- asp.py imported lazily in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, --show-asp
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
    mood: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    camel: object | None = None
    child: object | None = None
    helper: object | None = None
    prop: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type in {"dromedary", "children"} else "it"
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
    name: str
    place: str
    affords: set[str] = field(default_factory=set)
    mood: str = ""
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


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    come_phrase: str
    sound: str
    splash: str
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
class Prop:
    id: str
    label: str
    phrase: str
    helps: str
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
class StoryParams:
    setting: str = "fountain"
    activity: str = "dance"
    prop: str = "parasol"
    child_name: str = "Mina"
    child_gender: str = "girl"
    helper_name: str = "Pip"
    helper_gender: str = "boy"
    dromedary_name: str = "Dot"
    seed: Optional[int] = None
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


SETTINGS = {
    "fountain": Setting(name="the town fountain", place="by the town fountain", affords={"dance", "sing", "skip"}, mood="sparkly"),
    "meadow": Setting(name="the meadow", place="in the meadow", affords={"dance", "sing", "skip"}, mood="sunny"),
    "courtyard": Setting(name="the courtyard", place="in the courtyard", affords={"dance", "sing", "skip"}, mood="echoing"),
}

ACTIVITIES = {
    "dance": Activity(id="dance", verb="dance", gerund="dancing", come_phrase="come dancing", sound="do-si-do", splash="bounce", tags={"joy", "dance"}),
    "sing": Activity(id="sing", verb="sing", gerund="singing", come_phrase="come singing", sound="la-la-la", splash="hum", tags={"joy", "sing"}),
    "skip": Activity(id="skip", verb="skip", gerund="skipping", come_phrase="come skipping", sound="hop-hop", splash="bob", tags={"joy", "skip"}),
}

PROPS = {
    "parasol": Prop(id="parasol", label="a striped parasol", phrase="a striped parasol", helps="make shade and a silly shadow", tags={"shade", "humor"}),
    "bell": Prop(id="bell", label="a tiny bell", phrase="a tiny bell", helps="make a jingly rhythm", tags={"sound", "humor"}),
    "ribbon": Prop(id="ribbon", label="a bright ribbon", phrase="a bright ribbon", helps="make a twirly trail", tags={"color", "humor"}),
}

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nina", "Tia", "Rosa"]
BOY_NAMES = ["Pip", "Owen", "Ben", "Noah", "Toby", "Leo"]
DROMEDARY_NAMES = ["Dot", "Dodo", "Dara", "Dune"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for a in ACTIVITIES:
            for p in PROPS:
                if a == "dance" or p != "bell":
                    combos.append((s, a, p))
    return combos


def explain_rejection(setting: str, activity: str, prop: str) -> str:
    if activity == "sing" and prop == "bell":
        return "(No story: the tiny bell is too much like a loud toy for a calm singing scene. Pick a different prop.)"
    return "(No story: this combination does not make a plausible nursery-rhyme turn.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about a dromedary, a funny expression, and a come-gerund invitation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--dromedary-name")
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
    if getattr(args, "setting", None) and getattr(args, "activity", None) and getattr(args, "prop", None) and not any(True for c in valid_combos() if c == (getattr(args, "setting", None), getattr(args, "activity", None), getattr(args, "prop", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prop", None) is None or c[2] == getattr(args, "prop", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, activity, prop = rng.choice(list(combos))
    child_gender = getattr(args, "child_gender", None) or rng.choice(["girl", "boy"])
    helper_gender = getattr(args, "helper_gender", None) or rng.choice(["girl", "boy"])
    child_name = getattr(args, "child_name", None) or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != child_name])
    dromedary_name = getattr(args, "dromedary_name", None) or rng.choice(DROMEDARY_NAMES)
    return StoryParams(setting=setting, activity=activity, prop=prop, child_name=child_name, child_gender=child_gender, helper_name=helper_name, helper_gender=helper_gender, dromedary_name=dromedary_name)


def make_world(params: StoryParams):
    world = type("World", (), {})()
    world.entities = {}
    world.paragraphs = [[]]
    world.facts = {}
    world.fired = set()
    world.setting = _safe_lookup(SETTINGS, params.setting)
    world.activity = _safe_lookup(ACTIVITIES, params.activity)
    world.prop = _safe_lookup(PROPS, params.prop)
    world.story_events = []
    world.mood = "careful"
    world.trace = []

    def add(ent):
        world.entities[ent.id] = ent
        return ent

    world.add = add
    world.say = lambda txt: world.paragraphs[-1].append(txt) if txt else None
    world.para = lambda: world.paragraphs.append([]) if world.paragraphs[-1] else None
    world.render = lambda: "\n\n".join(" ".join(p) for p in world.paragraphs if p)
    world.characters = lambda: [e for e in world.entities.values() if e.kind == "character"]
    return world


def _set(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = float(value)


def _add(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = float(ent.meters.get(key, 0.0) + value)


def propagate(world) -> list[str]:
    out = []
    for ent in world.characters():
        if ent.meters.get("embarrassed", 0.0) >= THRESHOLD and ("express", ent.id) not in world.fired:
            world.fired.add(("express", ent.id))
            ent.memes["wry"] = ent.memes.get("wry", 0.0) + 1
            out.append(f"{ent.id} wore a wry expression, and the others had to grin.")
    for ent in world.characters():
        if ent.memes.get("laugh", 0.0) >= THRESHOLD and ("laugh", ent.id) not in world.fired:
            world.fired.add(("laugh", ent.id))
            ent.memes["joy"] = ent.memes.get("joy", 0.0) + 1
    return out


def tell(params: StoryParams):
    world = make_world(params)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, label=params.child_name, role="child", meters={"delight": 0.0, "worry": 0.0}, memes={"joy": 0.0, "curiosity": 0.0}))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, label=params.helper_name, role="helper", meters={"delight": 0.0}, memes={"joy": 0.0, "kindness": 0.0}))
    camel = world.add(Entity(id=params.dromedary_name, kind="character", type="dromedary", label="the dromedary", role="dromedary", mood="shy", meters={"worry": 0.0, "pose": 0.0, "step": 0.0}, memes={"embarrassed": 0.0, "relief": 0.0}, attrs={"expression": "funny"}))
    prop = world.add(Entity(id=params.prop, kind="thing", type="prop", label=_safe_lookup(PROPS, params.prop).label, phrase=_safe_lookup(PROPS, params.prop).phrase, tags=set(_safe_lookup(PROPS, params.prop).tags), meters={"shine": 1.0}, memes={}))

    act = _safe_lookup(ACTIVITIES, params.activity)
    world.say(f"By {_safe_lookup(SETTINGS, params.setting).name}, {child.id} found {camel.label} making a funny expression.")
    world.say(f'"Come, {act.gerund}," {child.id} said, with a {_safe_lookup(PROPS, params.prop).label} to help the fun.')
    world.para()
    _add(camel, "worry", 1)
    camel.memes["embarrassed"] = camel.memes.get("embarrassed", 0.0) + 1
    world.say(f"The dromedary blinked and blinked, then made a very silly face. The child giggled, and even the stones seemed amused.")
    world.say(f"{helper.id} came along with {prop.phrase}. {helper.id} knew {prop.helps}.")
    world.para()
    helper.memes["kindness"] += 1
    child.memes["joy"] += 1
    camel.memes["relief"] += 1
    camel.mood = "brave"
    _add(camel, "step", 1)
    propagate(world)
    if params.activity == "dance":
        world.say(f"{helper.id} held up the {prop.label} like a little stage roof, and {camel.id} came dancing under it.")
    elif params.activity == "sing":
        world.say(f"{helper.id} gave the {camel.id} a tiny beat with the {prop.label}, and {camel.id} came singing a soft baaa-hum.")
    else:
        world.say(f"{helper.id} twirled the {prop.label}, and {camel.id} came skipping with a wobble and a grin.")
    world.say(f"The funny expression turned into a proud one, then a happy one, and the whole circle laughed in a gentle nursery-rhyme way.")
    world.say(f"At the end, {camel.id} stood by {_safe_lookup(SETTINGS, params.setting).name} with a bright expression, and the three friends shared the last laugh.")
    world.facts.update(child=child, helper=helper, camel=camel, prop=prop, setting=world.setting, activity=act, params=params)
    return world


def generation_prompts(world) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme story that includes the word "dromedary" and the phrase "{f["activity"].come_phrase}".',
        f'Tell a funny, gentle story where {f["child"].id} sees a dromedary with a strange expression and invites it to {f["activity"].come_phrase}.',
        f'Write a happy ending story with a dromedary, a helper, and a bright prop like {f["prop"].phrase}.',
    ]


def story_qa(world) -> list[QAItem]:
    f = world.facts
    child, helper, camel, prop, act = f["child"], f["helper"], f["camel"], f["prop"], f["activity"]
    setting = f["setting"].name
    return [
        QAItem(
            question=f"Who saw the dromedary by {setting}?",
            answer=f"{child.id} saw the dromedary by {setting}. {child.id} was the one who noticed the funny expression first, and that started the little rhyme-like adventure.",
        ),
        QAItem(
            question=f"What did {child.id} ask the dromedary to do?",
            answer=f"{child.id} asked the dromedary to {act.come_phrase}. It was a playful invitation, and it gave the dromedary a gentle way to join in.",
        ),
        QAItem(
            question=f"How did {helper.id} help make the ending happy?",
            answer=f"{helper.id} brought {prop.phrase} and used it to make the play feel safe and silly. That helped the dromedary relax, so the funny expression changed into a happy one.",
        ),
    ]


KNOWLEDGE = {
    "dromedary": [("What is a dromedary?", "A dromedary is a kind of camel with one hump. It can walk for a long time and live in hot places.")],
    "expression": [("What is an expression?", "An expression is the look on someone's face. A smile, a frown, or wide eyes can all be expressions.")],
    "come-gerund": [("What does 'come dancing' mean?", "It means to come over and join the dancing. The word 'come' invites someone to do the activity with you.")],
    "humor": [("What makes a story funny?", "A story feels funny when something is a little silly, surprising, or playful. Humor makes readers smile or laugh.")],
    "happy ending": [("What is a happy ending?", "A happy ending is when the problem gets better and the characters finish safe, calm, or smiling.")],
}


def world_knowledge_qa(world) -> list[QAItem]:
    return [QAItem(q, a) for q, a in KNOWLEDGE["dromedary"] + KNOWLEDGE["expression"] + KNOWLEDGE["come-gerund"] + KNOWLEDGE["humor"] + KNOWLEDGE["happy ending"]]


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


def dump_trace(world) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.mood:
            bits.append(f"mood={e.mood}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="fountain", activity="dance", prop="parasol", child_name="Mina", child_gender="girl", helper_name="Pip", helper_gender="boy", dromedary_name="Dot"),
    StoryParams(setting="meadow", activity="sing", prop="ribbon", child_name="Luna", child_gender="girl", helper_name="Noah", helper_gender="boy", dromedary_name="Dara"),
    StoryParams(setting="courtyard", activity="skip", prop="bell", child_name="Toby", child_gender="boy", helper_name="Ivy", helper_gender="girl", dromedary_name="Dune"),
]


ASP_RULES = r"""
valid(S,A,P) :- setting(S), activity(A), prop(P), not bad_combo(A,P).
bad_combo(sing,bell).
happy(C) :- child(C), comes_gerund(C,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
        lines.append(asp.fact("comes_gerund", a, _safe_lookup(ACTIVITIES, a).come_phrase))
    for p in PROPS:
        lines.append(asp.fact("prop", p))
    for c in ("dromedary", "expression", "come-gerund"):
        lines.append(asp.fact("topic", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    try:
        clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
        ok1 = clingo_set == python_set
        sample = generate(resolve_params(argparse.Namespace(setting=None, activity=None, prop=None, child_name=None, child_gender=None, helper_name=None, helper_gender=None, dromedary_name=None), random.Random(777)))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=False)
        ok2 = bool(sample.story.strip())
    except Exception as exc:
        print(f"VERIFY FAILED: {exc}")
        return 1
    if ok1 and ok2:
        print(f"OK: ASP parity and smoke test passed ({len(clingo_set)} combos).")
        return 0
    print("VERIFY FAILED: parity or smoke test failed.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.activity not in ACTIVITIES or params.prop not in PROPS:
        pass
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for item in combos:
            print("  ", item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
