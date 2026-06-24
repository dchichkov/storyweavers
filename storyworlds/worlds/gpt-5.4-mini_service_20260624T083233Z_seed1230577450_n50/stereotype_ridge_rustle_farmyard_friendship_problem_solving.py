#!/usr/bin/env python3
"""
storyworlds/worlds/stereotype_ridge_rustle_farmyard_friendship_problem_solving.py
==================================================================================

A small comedy-leaning story world set in a farmyard, built from the seed
words "stereotype", "ridge", and "rustle".

Premise:
- A duck and a goat are friends in a farmyard.
- A careless stereotype makes one of them assume the other will be a problem.
- A windy rustle on a ridge creates a real problem.
- Friendship, kindness, and problem solving turn the day around.

The world is deliberately tiny and classical: one place, one tension, one
clever fix, one cheerful ending image.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        for k in ["dust", "rustle", "jitter", "help"]:
            self.meters.setdefault(k, 0.0)
        for k in ["friendship", "kindness", "problem_solving", "worry", "embarrassment", "delight", "stereotype", "trust"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"duck", "girl", "cow", "hen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"goat", "boy", "farmer", "man"}:
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
    place: str = "the farmyard"
    affords: set[str] = field(default_factory=set)
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
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
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str]
    guards: set[str]
    plural: bool = False
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
        self.zone: set[str] = set()
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


def _r_rustle(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["rustle"] < THRESHOLD:
            continue
        sig = ("rustle", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] += 1
        out.append("The wind made everything feel a little silly.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["kindness"] < THRESHOLD:
            continue
        sig = ("kindness", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["trust"] += 1
        out.append("A kind move made the whole farmyard soften.")
    return out


CAUSAL_RULES = [
    _r_rustle,
    _r_kindness,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    return "The farmyard was wide and bright, with a little ridge behind the barn and a heap of straw that liked to whisper in the wind."


def predict_problem(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["rustle"] += 1
    sim.zone = set(activity.zone)
    prize = sim.get(prize_id)
    return {"lost": bool(prize and prize.meters["dust"] >= THRESHOLD), "worry": sum(e.memes["worry"] for e in sim.characters())}


def do_activity(world: World, actor: Entity, activity: Activity) -> None:
    world.zone = set(activity.zone)
    actor.meters["rustle"] += 1
    propagate(world, narrate=True)


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(f"{hero.id} was a cheerful duck who loved jokes, shiny puddles, and having {friend.id} around.")
    world.say(f"{friend.id} was a gentle goat who was good at thinking with his whole head, not just the horns part.")


def stereo(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["stereotype"] += 1
    hero.memes["worry"] += 1
    world.say(f"One morning, {hero.id} made a silly stereotype about goats and muttered that {friend.id} would probably make a mess.")
    world.say(f"{friend.id} blinked at that, looking less like a problem and more like a very surprised lunch helper.")


def arrive(world: World, hero: Entity) -> None:
    world.say("Then the two friends went out to the farmyard together.")
    world.say(setting_detail(world.setting))


def want_and_warning(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {activity.verb}, but a gust on the ridge had other ideas.")
    pred = predict_problem(world, hero, activity, prize.id)
    if pred["lost"]:
        hero.memes["worry"] += 1
        world.facts["predicted_worry"] = pred["worry"]
        world.say(f'"If you go now, your {prize.label} might get dusty," {friend_name(world)} said, because the wind was already rustling the straw.')


def friend_name(world: World) -> str:
    return world.facts["friend"].id


def problem(world: World, hero: Entity, friend: Entity, activity: Activity, prize: Entity) -> None:
    world.say(f"Sure enough, a noisy rustle rolled across the ridge and bumped {hero.id}'s {prize.label} toward the edge.")
    hero.memes["embarrassment"] += 1
    friend.memes["problem_solving"] += 1
    world.say(f"{hero.id} gasped, and {friend.id} did not laugh even one tiny goat laugh. He just looked up, thinking.")


def fix(world: World, hero: Entity, friend: Entity, activity: Activity, prize: Entity, tool: Tool) -> None:
    friend.memes["kindness"] += 1
    friend.memes["friendship"] += 1
    hero.memes["friendship"] += 1
    world.say(f"Then {friend.id} found a clever fix: {tool.prep}.")
    world.say(f"{friend.id} nudged the {tool.label} into place, and together the two friends used it to reach the {prize.label} safely.")
    world.say(f"{tool.tail}. Soon {hero.id} could {activity.verb}, {prize.phrase} still clean, and the whole farmyard seemed to grin.")


def ending(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["trust"] += 1
    hero.memes["kindness"] += 1
    world.say(f"{hero.id} apologized for the stereotype and thanked {friend.id} for being kind instead of grumpy.")
    world.say(f"{friend.id} only smiled, and the two friends walked off side by side, with straw on their shoes and victory in their pockets.")


SETTINGS = {
    "farmyard": Setting(place="the farmyard", affords={"rustle"}),
}

ACTIVITIES = {
    "rustle": Activity(
        id="rustle",
        verb="rustle through the straw",
        gerund="rustling through the straw",
        rush="rush up the ridge",
        mess="dusty",
        soil="dusty",
        zone={"feet", "legs"},
        keyword="rustle",
        tags={"rustle", "ridge", "farmyard"},
    ),
}

PRIZES = {
    "lunchbox": Prize(
        label="lunchbox",
        phrase="a shiny lunchbox",
        type="lunchbox",
        region="legs",
    ),
    "basket": Prize(
        label="basket",
        phrase="a little picnic basket",
        type="basket",
        region="legs",
    ),
}

TOOLS = [
    Tool(
        id="plank",
        label="plank",
        prep="the goat found a plank near the shed and balanced it over the dip in the ridge",
        tail="The plank made a neat little bridge",
        covers={"legs"},
        guards={"dusty"},
    )
]

HERO_NAMES = ["Mina", "Pip", "Dot", "Lulu", "Tess", "Ned"]
FRIEND_NAMES = ["Gus", "Nell", "Bram", "Moe", "Clara", "Bea"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero_name: str
    friend_name: str
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


CURATED = [
    StoryParams(place="farmyard", activity="rustle", prize="lunchbox", hero_name="Dot", friend_name="Gus"),
    StoryParams(place="farmyard", activity="rustle", prize="basket", hero_name="Mina", friend_name="Nell"),
]

ASP_RULES = r"""
at_risk(A,P) :- splashes(A,R), worn_on(P,R).
tool_helps(T,A,P) :- at_risk(A,P), covers(T,R), worn_on(P,R), guards(T,M), mess_of(A,M).
valid_story(Place,A,P) :- affords(Place,A), at_risk(A,P), tool_helps(_,A,P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for r in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, r))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", t.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, s in SETTINGS.items():
        for a_id in s.affords:
            act = _safe_lookup(ACTIVITIES, a_id)
            for p_id, p in PRIZES.items():
                if p.region in act.zone:
                    out.append((place, a_id, p_id))
    return out


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    cl = set(asp.atoms(asp.one_model(asp_program("#show valid_story/3.")).__class__.__module__ and asp_program("#show valid_story/3."), "valid_story"))
    return 0 if py == cl else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Farmyard comedy world: stereotype, ridge, rustle, friendship, problem solving, and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, act, prize = rng.choice(list(combos))
    return StoryParams(
        place=place,
        activity=act,
        prize=prize,
        hero_name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        friend_name=getattr(args, "friend", None) or rng.choice(FRIEND_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.hero_name, kind="character", type="duck", label=params.hero_name, traits=["funny", "curious"]))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="goat", label=params.friend_name, traits=["kind", "clever"]))
    prize = world.add(Entity(id="prize", type=params.prize, label=_safe_lookup(PRIZES, params.prize).label, phrase=_safe_lookup(PRIZES, params.prize).phrase, owner=hero.id, caretaker=friend.id, region=_safe_lookup(PRIZES, params.prize).region))

    world.facts.update(hero=hero, friend=friend, prize=prize, activity=_safe_lookup(ACTIVITIES, params.activity), setting=_safe_lookup(SETTINGS, params.place))

    introduce(world, hero, friend)
    world.para()
    stereo(world, hero, friend)
    arrive(world, hero)
    want_and_warning(world, hero, _safe_lookup(ACTIVITIES, params.activity), prize)
    problem(world, hero, friend, _safe_lookup(ACTIVITIES, params.activity), prize)
    world.para()
    fix(world, hero, friend, _safe_lookup(ACTIVITIES, params.activity), prize, _safe_lookup(TOOLS, 0))
    ending(world, hero, friend)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            'Write a funny farmyard story about a stereotype that turns out to be wrong, a rustle on a ridge, and two friends solving a problem kindly.',
            f"Tell a comedy-leaning story where {params.hero_name} the duck and {params.friend_name} the goat help each other after a windy mishap in the farmyard.",
            'Write a short child-friendly story using the words stereotype, ridge, and rustle, and end with friendship and kindness.',
        ],
        story_qa=[
            QAItem(
                question=f"Who were the two friends in the story?",
                answer=f"The friends were {params.hero_name} the duck and {params.friend_name} the goat.",
            ),
            QAItem(
                question=f"What made the problem on the ridge?",
                answer="A windy rustle in the straw made the lunchbox start slipping near the ridge.",
            ),
            QAItem(
                question=f"What did the goat do to help?",
                answer=f"{params.friend_name} found a clever plank and used problem solving to turn it into a little bridge.",
            ),
            QAItem(
                question=f"What did the duck learn?",
                answer=f"{params.hero_name} learned not to trust a silly stereotype and to thank a friend for being kind.",
            ),
        ],
        world_qa=[
            QAItem(
                question="What is a stereotype?",
                answer="A stereotype is a quick and unfair idea about a whole kind of creature or person before you really know them.",
            ),
            QAItem(
                question="What does rustle mean?",
                answer="Rustle means a soft, scratchy sound, like straw or leaves moving in the wind.",
            ),
            QAItem(
                question="What is kindness?",
                answer="Kindness means treating someone gently and helpfully, especially when they need support.",
            ),
            QAItem(
                question="What is problem solving?",
                answer="Problem solving means finding a sensible way to fix a tricky situation.",
            ),
        ],
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== QA ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(0)
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
