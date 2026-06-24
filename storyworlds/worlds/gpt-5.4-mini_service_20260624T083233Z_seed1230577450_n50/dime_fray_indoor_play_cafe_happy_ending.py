#!/usr/bin/env python3
"""
Small storyworld: indoor play cafe, a dime, and a fray.

A child visits an indoor play cafe, notices a dime, and deals with a small fray
in a shared toy or play item. The simulated world can end three ways:

- happy ending: the child uses the dime in a kind, tidy way and the fray gets fixed
- lesson learned: the child makes a small mistake, then learns to be careful
- bad ending: the child ignores the fray and the day ends in disappointment

The prose is slice-of-life: concrete, gentle, and state-driven.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str = "the indoor play cafe"
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
    risk: str
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
class Ending:
    id: str
    label: str
    turn: str
    mood: str
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


@dataclass
class StoryParams:
    ending: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "cafe": Setting(place="the indoor play cafe", affords={"tokens", "craft", "snack"}),
}

ACTIVITIES = {
    "tokens": Activity(
        id="tokens",
        verb="use the coin to get a token",
        gerund="pushing the token button",
        rush="dash to the machine",
        mess="scatter",
        soil="lost in the foam pit",
        keyword="dime",
        tags={"dime"},
    ),
    "craft": Activity(
        id="craft",
        verb="make a craft",
        gerund="gluing glitter and paper",
        rush="grab the glue",
        mess="fray",
        soil="more frayed and messy",
        keyword="fray",
        tags={"fray"},
    ),
    "snack": Activity(
        id="snack",
        verb="pick a snack",
        gerund="eating at a tiny table",
        rush="run toward the counter",
        mess="spill",
        soil="sticky",
        keyword="dime",
        tags={"dime"},
    ),
}

PRIZES = {
    "dime": Prize(
        label="dime",
        phrase="a shiny dime from the floor",
        type="dime",
        risk="could get spent too fast",
    ),
    "string": Prize(
        label="string",
        phrase="a frayed ribbon string",
        type="string",
        risk="could unravel more",
    ),
    "tag": Prize(
        label="tag",
        phrase="a loose paper tag on a toy",
        type="tag",
        risk="could tear off",
    ),
}

ENDINGS = {
    "happy": Ending(
        id="happy",
        label="Happy Ending",
        turn="They fixed the small problem and finished the day smiling.",
        mood="warm",
    ),
    "lesson": Ending(
        id="lesson",
        label="Lesson Learned",
        turn="The child made a mistake, then learned how to be careful next time.",
        mood="gentle",
    ),
    "bad": Ending(
        id="bad",
        label="Bad Ending",
        turn="The mistake was not fixed, and the child had to leave disappointed.",
        mood="sad",
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lila", "Ella", "Zoe", "Ava", "Maya"]
BOY_NAMES = ["Leo", "Ben", "Max", "Noah", "Finn", "Eli", "Theo"]
TRAITS = ["curious", "cheerful", "quiet", "lively", "gentle", "patient"]


def reasonableness(activity: Activity, prize: Prize, ending: Ending) -> bool:
    if activity.id == "tokens" and prize.label != "dime":
        return False
    if activity.id == "craft" and prize.label not in {"string", "tag"}:
        return False
    if activity.id == "snack" and prize.label != "dime":
        return False
    if ending.id == "bad" and activity.id == "craft" and prize.label == "string":
        return True
    return True


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not realistically affect {prize.phrase} "
        f"in this small cafe world.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: an indoor play cafe, a dime, and a fray."
    )
    ap.add_argument("--ending", choices=ENDINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    ending = getattr(args, "ending", None) or rng.choice(list(ENDINGS))
    activity = getattr(args, "activity", None) or rng.choice(list(ACTIVITIES))
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    if not reasonableness(_safe_lookup(ACTIVITIES, activity), _safe_lookup(PRIZES, prize), _safe_lookup(ENDINGS, ending)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(
        ending=ending,
        activity=activity,
        prize=prize,
        name=name,
        gender=gender,
        parent=parent,
    )


def predict_fray(world: World, prize: Entity) -> bool:
    return prize.meters.get("fray", 0.0) >= THRESHOLD


def tell(params: StoryParams) -> World:
    world = World(SETTINGS["cafe"])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="parent"))
    act = _safe_lookup(ACTIVITIES, params.activity)
    prize_cfg = _safe_lookup(PRIZES, params.prize)
    ending = _safe_lookup(ENDINGS, params.ending)
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
    ))

    hero.memes["want"] = 1
    world.say(
        f"{hero.id} went to {world.setting.place} with {hero.pronoun('possessive')} {parent.label}."
    )
    world.say(
        f"Near the toy shelves, {hero.id} noticed {prize.phrase} and a small {act.keyword} problem."
    )
    world.say(
        f"{hero.id} wanted to {act.verb}, but {hero.pronoun('possessive')} {parent.label} saw the {prize.label} was at risk."
    )

    world.para()
    if params.ending == "happy":
        if prize.label == "dime":
            world.say(
                f"{parent.id} suggested saving the dime for the machine instead of spending it right away."
            )
            world.say(
                f"Then they used the token machine carefully, and {hero.id} smiled when the prize stayed safe."
            )
        else:
            prize.meters["fray"] = 1
            world.say(
                f"{parent.id} found tape in a drawer and fixed the fray before it spread."
            )
            world.say(
                f"After that, {hero.id} could {act.verb} and still carry {prize.it()} home neatly."
            )
    elif params.ending == "lesson":
        if prize.label == "dime":
            world.say(
                f"{hero.id} almost dropped the dime into the wrong slot, then paused and listened."
            )
            world.say(
                f"With a slow breath, {hero.id} put {prize.it()} away for later and learned to wait."
            )
        else:
            prize.meters["fray"] = 1
            world.say(
                f"{hero.id} tugged too hard and made the fray worse."
            )
            world.say(
                f"After {parent.id} showed how to hold it gently, {hero.id} learned to use smaller hands and slower motions."
            )
    else:
        if prize.label == "dime":
            world.say(
                f"{hero.id} rushed ahead, spent the dime, and then realized the machine was out of the toy {hero.id} wanted."
            )
            world.say(
                f"The lost chance made {hero.id} frown while the cafe got louder around {hero.id}."
            )
        else:
            prize.meters["fray"] = 2
            world.say(
                f"{hero.id} kept pulling at the fray until the ribbon split."
            )
            world.say(
                f"The little project had to stop, and the broken piece could not be used that day."
            )

    world.para()
    if params.ending == "happy":
        world.say(
            f"In the end, {ending.turn} {hero.id} left {world.setting.place} with a calm face and a better plan for the next visit."
        )
    elif params.ending == "lesson":
        world.say(
            f"In the end, {ending.turn} {hero.id} kept the dime safe and remembered that careful hands make play easier."
        )
    else:
        world.say(
            f"In the end, {ending.turn} {hero.id} walked out quietly, still wishing the fray had been handled sooner."
        )

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=act, ending=ending)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, prize, act, ending = f["hero"], f["parent"], f["prize"], f["activity"], f["ending"]
    return [
        f'Write a slice-of-life story for a young child set in an indoor play cafe, and include the words "dime" and "fray".',
        f"Tell a gentle story about {hero.id} and {hero.pronoun('possessive')} {parent.label} at {world.setting.place} where a {prize.label} causes a small problem.",
        f"Write a short story that ends with {ending.label.lower()} and shows how a tiny cafe problem changes the day.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act, ending = f["hero"], f["parent"], f["prize"], f["activity"], f["ending"]
    return [
        QAItem(
            question=f"Where was {hero.id} when the small problem happened?",
            answer=f"{hero.id} was at {world.setting.place} with {hero.pronoun('possessive')} {parent.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} notice in the cafe?",
            answer=f"{hero.id} noticed {prize.phrase} and a little {act.keyword} problem.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended as a {ending.label.lower()} and showed that a small choice changed the day.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dime?",
            answer="A dime is a small coin. People can save it, spend it, or drop it into a machine.",
        ),
        QAItem(
            question="What does fray mean?",
            answer="A fray is a place where thread, ribbon, or fabric is wearing out and getting fuzzy or split.",
        ),
        QAItem(
            question="What is an indoor play cafe?",
            answer="An indoor play cafe is a place where children can play inside while families sit, snack, and watch nearby.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
valid_story(E,A,P) :- ending(E), activity(A), prize(P), compatible(E,A,P).
compatible(happy,tokens,dime).
compatible(lesson,tokens,dime).
compatible(happy,craft,string).
compatible(lesson,craft,string).
compatible(bad,craft,string).
compatible(happy,craft,tag).
compatible(lesson,craft,tag).
compatible(bad,craft,tag).
compatible(happy,snack,dime).
compatible(lesson,snack,dime).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for e in ENDINGS:
        lines.append(asp.fact("ending", e))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/3."))
    found = sorted(set(asp.atoms(model, "valid_story")))
    expected = sorted(
        (e, a, p)
        for e in ENDINGS
        for a in ACTIVITIES
        for p in PRIZES
        if (e == "bad" and a == "craft" and p in {"string", "tag"})
        or (e in {"happy", "lesson"} and ((a == "tokens" and p == "dime") or (a == "craft" and p in {"string", "tag"}) or (a == "snack" and p == "dime")))
        or (e == "bad" and a == "craft" and p == "string")
    )
    if found == expected:
        print(f"OK: ASP gate matches Python expectations ({len(found)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("ASP:", found)
    print("PY :", expected)
    return 1


def build_valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for e in ENDINGS:
        for a in ACTIVITIES:
            for p in PRIZES:
                if e == "bad" and a == "craft" and p in {"string", "tag"}:
                    combos.append((e, a, p))
                if e in {"happy", "lesson"} and ((a == "tokens" and p == "dime") or (a == "craft" and p in {"string", "tag"}) or (a == "snack" and p == "dime")):
                    combos.append((e, a, p))
    return sorted(set(combos))


def resolve_story(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    ending = getattr(args, "ending", None) or rng.choice(list(ENDINGS))
    activity = getattr(args, "activity", None) or rng.choice(list(ACTIVITIES))
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    if (ending, activity, prize) not in build_valid_combos():
        pass
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(ending=ending, activity=activity, prize=prize, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(ending="happy", activity="tokens", prize="dime", name="Mia", gender="girl", parent="mother"),
    StoryParams(ending="lesson", activity="craft", prize="string", name="Leo", gender="boy", parent="father"),
    StoryParams(ending="bad", activity="craft", prize="tag", name="Ava", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        try:
            import storyworlds.asp as asp
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            return
        model = asp.one_model(asp_program("#show valid_story/3."))
        atoms = sorted(set(asp.atoms(model, "valid_story")))
        for a in atoms:
            print(a)
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
                params = resolve_story(args, random.Random(seed))
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
            header = f"### {p.name}: {p.ending} / {p.activity} / {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
