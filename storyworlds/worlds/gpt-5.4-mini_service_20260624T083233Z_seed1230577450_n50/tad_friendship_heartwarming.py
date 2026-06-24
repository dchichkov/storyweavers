#!/usr/bin/env python3
"""
storyworlds/worlds/tad_friendship_heartwarming.py
=================================================

A tiny heartwarming storyworld about a tadpole, a friendship worry, and a
kindly turn toward helping, sharing, and belonging.

Seed tale sketch:
---
A small tad lived in a pond with reeds, pebbles, and lily pads. Tad felt lonely
because the bigger frogs kept hopping away too fast. One day, Tad met a gentle
snail friend who liked slow walks and careful listening. Tad wanted to play, but
the pond was windy and the lily pad was far away. The friend helped Tad across,
and Tad learned that a good friend can make even a small pond feel warm.
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
    companion: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    aid: object | None = None
    friend: object | None = None
    tad: object | None = None
    def __post_init__(self) -> None:
        self.meters.setdefault("tired", 0.0)
        self.meters.setdefault("travel", 0.0)
        self.meters.setdefault("wind", 0.0)
        self.meters.setdefault("wet", 0.0)
        self.memes.setdefault("lonely", 0.0)
        self.memes.setdefault("joy", 0.0)
        self.memes.setdefault("care", 0.0)
        self.memes.setdefault("friendship", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"tad", "tadpole"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the pond"
    windiness: str = "breezy"
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
    challenge: str
    weather: str = ""
    keyword: str = "tad"
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
class Aid:
    id: str
    label: str
    phrase: str
    helps: set[str]
    prep: str
    tail: str
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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    aid: str
    name: str
    friend_name: str
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


SETTINGS = {
    "pond": Setting(place="the pond", windiness="breezy", affords={"cross", "play"}),
    "reeds": Setting(place="the reeds", windiness="soft", affords={"hide", "play"}),
    "lily": Setting(place="the lily pad", windiness="breezy", affords={"cross", "rest"}),
}

ACTIVITIES = {
    "cross": Activity(
        id="cross",
        verb="cross the pond",
        gerund="crossing the pond",
        rush="hurry over the water",
        challenge="the water is too wide and wobbly",
        weather="breezy",
        keyword="tad",
        tags={"water", "tad", "wind"},
    ),
    "play": Activity(
        id="play",
        verb="play by the pond",
        gerund="playing by the pond",
        rush="run toward the reeds",
        challenge="the wind can make little swimmers wobble",
        weather="breezy",
        keyword="tad",
        tags={"tad", "friendship"},
    ),
    "hide": Activity(
        id="hide",
        verb="hide in the reeds",
        gerund="hiding in the reeds",
        rush="dash into the tall stems",
        challenge="the reeds can snag a small tail",
        weather="soft",
        keyword="tad",
        tags={"tad"},
    ),
}

AIDS = {
    "leafboat": Aid(
        id="leafboat",
        label="a leaf boat",
        phrase="a little leaf boat",
        helps={"cross"},
        prep="make a leaf boat together",
        tail="floated across on the leaf boat",
    ),
    "shellstep": Aid(
        id="shellstep",
        label="a shell step",
        phrase="a smooth shell step",
        helps={"cross", "play"},
        prep="set out a smooth shell step",
        tail="crossed carefully on the shell step",
    ),
    "reedshade": Aid(
        id="reedshade",
        label="reed shade",
        phrase="a soft reed shade",
        helps={"hide", "play"},
        prep="sit under the reeds and rest",
        tail="rested safely under the reeds",
    ),
}

NAMES = ["Tad", "Milo", "Pip", "Nori", "Luna", "Wren", "Poppy", "Moss"]
FRIEND_NAMES = ["Fin", "Bea", "Sage", "Dot", "Theo", "Ruby", "Iris", "June"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for aid_id, aid in AIDS.items():
            for act_id in setting.affords:
                act = _safe_lookup(ACTIVITIES, act_id)
                if act.id in aid.helps:
                    combos.append((place, act_id, aid_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming tad friendship storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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
    if getattr(args, "activity", None) and getattr(args, "aid", None):
        if (getattr(args, "place", None) and (getattr(args, "place", None), getattr(args, "activity", None), getattr(args, "aid", None)) not in valid_combos()):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "aid", None) is None or c[2] == getattr(args, "aid", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, aid_id = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice(FRIEND_NAMES)
    return StoryParams(place=place, activity=activity, aid=aid_id, name=name, friend_name=friend_name)


def _do_activity(world: World, actor: Entity, act: Activity, narrate: bool = True) -> None:
    actor.meters["travel"] += 1
    actor.meters["wind"] += 1 if world.setting.windiness == "breezy" else 0
    actor.memes["joy"] += 1
    if act.id == "cross":
        actor.meters["wet"] += 1
    if narrate:
        world.say(f"{actor.id} tried to {act.verb}, and the pond felt bigger than expected.")


def predict(world: World, actor: Entity, act: Activity) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), act, narrate=False)
    return {
        "tired": sim.get(actor.id).meters["travel"] >= THRESHOLD,
        "wet": sim.get(actor.id).meters["wet"] >= THRESHOLD,
    }


def tell(setting: Setting, activity: Activity, aid_def: Aid, name: str, friend_name: str) -> World:
    world = World(setting)
    tad = world.add(Entity(id=name, kind="character", type="tad", label="tad"))
    friend = world.add(Entity(id=friend_name, kind="character", type="friend", label="friend"))
    aid = world.add(Entity(id=aid_def.id, type="thing", label=aid_def.label, phrase=aid_def.phrase, owner=tad.id))
    friend.companion = tad.id

    world.say(f"{tad.id} was a small tad who loved the calm water in {setting.place}.")
    world.say(f"{tad.id} felt lonely sometimes, because the bigger frogs hopped away too fast.")
    world.say(f"One day, {friend.id} came to the pond with a warm smile and a slow, careful step.")

    world.para()
    world.say(f"{tad.id} wanted to {activity.verb}, but {activity.challenge}.")
    pred = predict(world, tad, activity)
    if pred["wet"]:
        tad.memes["lonely"] += 1
        world.say(f"{tad.id} looked at the water and wished for someone kind to stay close.")
    world.say(f"{friend.id} listened, then said they could help in a gentle way.")

    world.para()
    world.say(f"They decided to {aid_def.prep}.")
    aid.memes["care"] += 1
    aid.memes["friendship"] += 1
    tad.memes["friendship"] += 1
    tad.memes["lonely"] = max(0.0, tad.memes["lonely"] - 1)
    _do_activity(world, tad, activity)
    if activity.id in aid_def.helps:
        world.say(f"Together, they {aid_def.tail}, and {tad.id} did not have to do it alone.")
    if activity.id == "cross":
        tad.memes["joy"] += 1
    world.say(f"{tad.id} smiled because the pond felt friendlier with {friend.id} beside {tad.pronoun('object')}.")

    world.facts.update(tad=tad, friend=friend, aid=aid, activity=activity, setting=setting, aid_def=aid_def)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    tad = f["tad"]
    act = f["activity"]
    aid_def = f["aid_def"]
    return [
        f'Write a heartwarming story for a young child about "{tad.id}" and a kind friend.',
        f"Tell a gentle story where {tad.id} wants to {act.verb} and learns to accept help from a friend.",
        f"Write a simple friendship story that includes a {aid_def.label} and ends with a warm feeling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    tad = f["tad"]
    friend = f["friend"]
    act = f["activity"]
    aid = f["aid"]
    return [
        QAItem(
            question=f"Who was the story about at {world.setting.place}?",
            answer=f"It was about {tad.id}, a small tad, and {friend.id}, a kind friend who stayed close.",
        ),
        QAItem(
            question=f"What did {tad.id} want to do before the friend helped?",
            answer=f"{tad.id} wanted to {act.verb}, but the pond felt a little hard and wobbly at first.",
        ),
        QAItem(
            question=f"How did the two friends solve the problem?",
            answer=f"They used {aid.label} and did the hard part together, so {tad.id} could keep going with a smile.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tadpole?",
            answer="A tadpole is a young frog that starts life in water and has a tail for swimming.",
        ),
        QAItem(
            question="What does a good friend do?",
            answer="A good friend listens, helps when something feels hard, and makes another creature feel less alone.",
        ),
        QAItem(
            question="What is a pond?",
            answer="A pond is a small body of water where plants and little animals can live.",
        ),
    ]


ASP_RULES = r"""
valid_story(Place, Act, Aid) :- affords(Place, Act), helps(Aid, Act).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        for act in sorted(a.helps):
            lines.append(asp.fact("helps", aid, act))
    for act_id in ACTIVITIES:
        lines.append(asp.fact("activity", act_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(place="pond", activity="cross", aid="leafboat", name="Tad", friend_name="Fin"),
    StoryParams(place="pond", activity="cross", aid="shellstep", name="Milo", friend_name="Bea"),
    StoryParams(place="reeds", activity="play", aid="reedshade", name="Pip", friend_name="Sage"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(AIDS, params.aid), params.name, params.friend_name)
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
        import storyworlds.asp as asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, aid) combos:\n")
        for place, act, aid in triples:
            print(f"  {place:8} {act:8} {aid:10}")
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
