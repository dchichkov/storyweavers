#!/usr/bin/env python3
"""
storyworlds/worlds/mouth_scratch_dim_toast_repetition_sound_effects.py
======================================================================

A small fable-like storyworld about a hushy mouth, a scratch-dim itch, and a
piece of toast that changes hands through repetition and sound effects.

Seed tale sketch:
---
In a quiet little barnyard, Pip the mouse loved to nibble toast at sunrise.
But every time Pip rushed to speak with a crusty mouth, a scratch-dim tickle
kept making the words come out crooked. Pip tried again and again: "Squeak,
squeak," and the sound of the scratchy stuck bit made the others laugh kindly.
At last, Pip listened, cooled the toast, and learned that a small pause can
make a small meal sweeter.

World idea:
- Physical meters track toast warmth, crumbiness, and mouth scratch-dim.
- Emotional memes track patience, pride, and relief.
- Repetition matters: repeated attempts can increase the scratch-dim itch,
  but repeated careful pauses reduce it.
- Sound effects matter: the world narrates the tiny sounds of nibbling,
  scraping, and sighing to make the turn feel lived-in.
- The ending proves change by showing the mouth soothed, the toast shared, and
  the lesson learned.

This file follows the Storyweavers storyworld contract.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Lazy ASP import only inside helpers.

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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    friend: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "child", "boy", "girl"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    place: str = "the little barn"
    indoor: bool = False
    repeats: set[str] = field(default_factory=set)
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
class Action:
    id: str
    verb: str
    repeated_verb: str
    sound: str
    risk_meter: str
    risk_gain: float
    soothing_gain: float
    keyword: str
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
class Prize:
    label: str
    phrase: str
    type: str
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
class Companion:
    id: str
    label: str
    kind: str = "character"
    type: str = "friend"
    trait: str = "kind"
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        return w


def sound_for(action: Action, repeated: bool) -> str:
    if action.id == "toast":
        return "crunch-crunch" if repeated else "munch"
    return "scritch-scritch" if repeated else "scratch"


def narration_repeat(count: int) -> str:
    if count == 1:
        return "again"
    if count == 2:
        return "again and again"
    return "over and over"


def setup_story(world: World, hero: Entity, prize: Entity, action: Action, friend: Entity) -> None:
    world.say(
        f"{hero.id} was a small {hero.type} who loved the morning hush."
    )
    world.say(
        f"{hero.pronoun().capitalize()} liked {action.verb} beside {friend.label}, "
        f"and {friend.label} always listened with a patient smile."
    )
    world.say(
        f"One dawn, {hero.id} found {prize.phrase} waiting near the warm stone."
    )


def do_action(world: World, hero: Entity, action: Action, repeated: bool = False) -> None:
    s = sound_for(action, repeated)
    world.say(f"{s}! {hero.id} kept to {action.repeated_verb if repeated else action.verb}.")
    hero.meters[action.risk_meter] = hero.meters.get(action.risk_meter, 0.0) + action.risk_gain
    hero.memes["restless"] = hero.memes.get("restless", 0.0) + 0.5
    if repeated:
        hero.meters["scratch_dim"] = hero.meters.get("scratch_dim", 0.0) + 1.0
    if hero.meters.get("scratch_dim", 0.0) >= THRESHOLD:
        world.say(
            f"The scratch-dim itch made {hero.pronoun('possessive')} mouth feel noisy."
        )


def warn_and_repeat(world: World, hero: Entity, action: Action, prize: Entity) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0
    world.say(
        f"{hero.id} tried once, then {narration_repeat(2)} tried to speak with a full mouth."
    )
    world.say(
        f'"Wait," said the friend. "A small pause can help your {prize.label} stay sweet."'
    )
    world.say(
        f"But {hero.id} went on with the same little rush: {sound_for(action, True)}."
    )
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1.0


def turn_to_pause(world: World, hero: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} stopped at last, took a breath, and held the toast up to the light."
    )
    world.say(
        f"The toast cooled. The mouth quieted. The room felt softer."
    )
    hero.meters["scratch_dim"] = max(0.0, hero.meters.get("scratch_dim", 0.0) - 1.0)
    hero.memes["patience"] = hero.memes.get("patience", 0.0) + 1.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
    prize.meters["warmth"] = max(0.0, prize.meters.get("warmth", 0.0) - 1.0)


def resolution(world: World, hero: Entity, prize: Entity, friend: Entity, action: Action) -> None:
    world.say(
        f"At the end, {hero.id} took the toast in small bites: {sound_for(action, False)}, {sound_for(action, True)}."
    )
    world.say(
        f"{friend.label} shared the last crumb, and {hero.id}'s mouth stayed calm."
    )
    world.say(
        f"So the little {hero.type} learned that a pause can be kinder than haste."
    )


def tell(setting: Setting, action: Action, prize_cfg: Prize, hero_name: str,
         friend_label: str = "the sparrow") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="mouse",
        label=hero_name,
        meters={"scratch_dim": 0.0, "toast": 0.0},
        memes={"curious": 1.0},
    ))
    prize = world.add(Entity(
        id="toast",
        kind="thing",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
        meters={"warmth": 1.0, "crumbs": 0.0},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type="bird",
        label=friend_label,
        meters={},
        memes={"kind": 1.0},
    ))

    setup_story(world, hero, prize, action, friend)
    world.para()
    do_action(world, hero, action, repeated=False)
    warn_and_repeat(world, hero, action, prize)
    do_action(world, hero, action, repeated=True)
    world.para()
    turn_to_pause(world, hero, prize)
    resolution(world, hero, prize, friend, action)

    world.facts.update(hero=hero, prize=prize, friend=friend, action=action, setting=setting)
    return world


SETTINGS = {
    "barn": Setting(place="the little barn", indoor=True, repeats={"toast", "scratch"}),
    "kitchen": Setting(place="the warm kitchen", indoor=True, repeats={"toast"}),
    "porch": Setting(place="the sunlit porch", indoor=False, repeats={"toast", "scratch"}),
}

ACTIONS = {
    "toast": Action(
        id="toast",
        verb="nibble toast",
        repeated_verb="nibble toast again and again",
        sound="crunch-crunch",
        risk_meter="scratch_dim",
        risk_gain=1.0,
        soothing_gain=1.0,
        keyword="toast",
        tags={"toast", "sound_effect", "repetition"},
    ),
    "scratch": Action(
        id="scratch",
        verb="scratch the itchy whiskers",
        repeated_verb="scratch the itchy whiskers again and again",
        sound="scritch-scritch",
        risk_meter="scratch_dim",
        risk_gain=1.0,
        soothing_gain=0.5,
        keyword="scratch-dim",
        tags={"scratch-dim", "sound_effect", "repetition"},
    ),
}

PRIZES = {
    "toast": Prize(
        label="toast",
        phrase="a little piece of toast",
        type="toast",
        region="mouth",
    ),
    "buttered_toast": Prize(
        label="toast",
        phrase="buttered toast on a blue plate",
        type="toast",
        region="mouth",
    ),
}

NAMES = ["Pip", "Tia", "Milo", "Nell", "Bea", "Ollie"]
FRIEND_LABELS = ["the sparrow", "the robin", "the lamb"]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    friend: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, s in SETTINGS.items():
        for action in s.repeats:
            for prize in PRIZES:
                out.append((place, action, prize))
    return out


def explain_invalid(place: str, action: str, prize: str) -> str:
    return f"(No story: {place}, {action}, and {prize} do not make a gentle fable here.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like storyworld of mouth, scratch-dim, and toast.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend", choices=FRIEND_LABELS)
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
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, prize = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    friend = getattr(args, "friend", None) or rng.choice(FRIEND_LABELS)
    return StoryParams(place=place, action=action, prize=prize, name=name, friend=friend)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short fable for children about a mouse, a scratch-dim mouth, and toast.',
        f"Tell a gentle story where {f['hero'].id} keeps trying with {f['action'].verb} until a pause helps.",
        "Use repetition and sound effects, and end with a small lesson about patience.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, prize, friend, action = f["hero"], f["prize"], f["friend"], f["action"]
    return [
        QAItem(
            question=f"What did {hero.id} keep trying to do?",
            answer=f"{hero.id} kept trying to {action.verb}, and the repeated sounds showed the attempt.",
        ),
        QAItem(
            question=f"What helped {hero.id}'s mouth feel better?",
            answer="Taking a pause and letting the toast cool helped the mouth feel calm again.",
        ),
        QAItem(
            question=f"Who listened kindly to {hero.id}?",
            answer=f"{friend.label} listened kindly and reminded {hero.id} that a small pause could help the toast stay sweet.",
        ),
        QAItem(
            question=f"What was special about the toast in the story?",
            answer=f"It was a little piece of toast that stayed at the center of the lesson and changed from hot to calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is toast?", answer="Toast is bread that has been browned by heat so it becomes crisp and warm."),
        QAItem(question="What does repetition mean?", answer="Repetition means doing or saying something again and again."),
        QAItem(question="What are sound effects in a story?", answer="Sound effects are written sounds like crunch or scritch that help a reader hear the scene."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,A,T) :- place(P), action(A), prize(T), allowed(P,A,T).
allowed(P,A,T) :- repeats(P,A), toastish(T).
toastish(toast).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.repeats):
            lines.append(asp.fact("repeats", pid, a))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for tid in PRIZES:
        lines.append(asp.fact("prize", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(PRIZES, params.prize), params.name, params.friend)
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(e.id, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="barn", action="toast", prize="toast", name="Pip", friend="the sparrow"),
    StoryParams(place="kitchen", action="toast", prize="buttered_toast", name="Tia", friend="the robin"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
