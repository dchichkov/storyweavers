#!/usr/bin/env python3
"""
storyworlds/worlds/hone_platter_coarse_community_center_reconciliation_mystery.py
=================================================================================

A small storyworld set in a community center, built from a comedy-shaped
reconciliation mystery.

Premise:
- A child and a helper arrive at the community center for a shared activity.
- A polished platter is important to the event.
- A coarse cloth or surface threatens to scratch, dull, or contaminate it.

Tension:
- Something about the platter goes missing, gets swapped, or looks wrong.
- People suspect the wrong person, creating a funny little misunderstanding.

Turn:
- The group investigates clues in the community center.
- The real cause is simple and ordinary, not dramatic.

Resolution:
- The misunderstanding clears up.
- The characters reconcile, the platter is restored, and the event can continue.

The domain uses typed entities with physical meters and emotional memes, and it
includes an inline ASP twin for the reasonableness gate and registries.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"clean": 0.0, "scratched": 0.0, "missing": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "embarrassment": 0.0, "relief": 0.0, "reconciliation": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt", "lady"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle", "guy"}:
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
class Place:
    name: str = "the community center"
    affords: set[str] = field(default_factory=lambda: {"potluck", "crafts", "singalong"})
    PLACE: object | None = None
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
class Activity:
    id: str
    verb: str
    gerund: str
    clue: str
    mess: str
    risk: str
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
class Prize:
    label: str
    phrase: str
    type: str
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


@dataclass
class StoryParams:
    activity: str
    prize: str
    name: str
    helper: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
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
        other = World(self.place)
        other.entities = copy.deepcopy(self.entities)
        other.facts = copy.deepcopy(self.facts)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        return other


def resolve_mystery(world: World, actor: Entity, prize: Entity, clue: str) -> None:
    if "mystery_resolved" in world.fired:
        return
    world.fired.add("mystery_resolved")
    actor.memes["curiosity"] += 1
    prize.meters["missing"] = 0.0
    prize.meters["clean"] += 1.0
    world.say(
        f"{actor.id} followed the clue and found the answer: the {clue} had only been "
        f"moved to the supply table, not stolen."
    )


PLACE = Place()

ACTIVITIES = {
    "bake": Activity(
        id="bake",
        verb="help with the bake sale",
        gerund="helping with the bake sale",
        clue="honey jar",
        mess="sticky",
        risk="sticky fingers on the platter",
        keyword="hone",
        tags={"honey", "platter", "mystery"},
    ),
    "craft": Activity(
        id="craft",
        verb="set up the craft table",
        gerund="setting up the craft table",
        clue="paper scraps",
        mess="dusty",
        risk="dust on the platter",
        keyword="coarse",
        tags={"platter", "mystery"},
    ),
    "share": Activity(
        id="share",
        verb="serve snacks for the group",
        gerund="serving snacks for the group",
        clue="napkin pile",
        mess="crumbly",
        risk="crumbs on the platter",
        keyword="platter",
        tags={"platter", "mystery"},
    ),
}

PRIZES = {
    "platter": Prize(
        label="platter",
        phrase="a shiny platter for the community snack table",
        type="platter",
    ),
    "tray": Prize(
        label="tray",
        phrase="a silver tray with a bright rim",
        type="tray",
    ),
}

GIVEN_NAMES = ["Maya", "Noah", "Lina", "Eli", "Ivy", "Owen", "Zara", "Theo"]
HELPERS = ["Ms. Pru", "Mr. Lane", "Auntie June", "Coach Bea"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for act in ACTIVITIES:
        for prize in PRIZES:
            combos.append(("community_center", act, prize))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: the setup never becomes funny enough for {activity.id} with {prize.label}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Community center reconciliation mystery storyworld.")
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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
    act = getattr(args, "activity", None) or rng.choice(list(ACTIVITIES))
    pr = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    if (act, pr) not in {(a, p) for _, a, p in valid_combos()}:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(GIVEN_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(activity=act, prize=pr, name=name, helper=helper)


def tell(params: StoryParams) -> World:
    world = World(PLACE)
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Maya", "Lina", "Ivy", "Zara"} else "boy"))
    helper = world.add(Entity(id=params.helper, kind="character", type="woman" if "Ms." in params.helper or "Auntie" in params.helper else "man"))
    prize = world.add(Entity(id="platter", type=_safe_lookup(PRIZES, params.prize).type, label=_safe_lookup(PRIZES, params.prize).label, phrase=_safe_lookup(PRIZES, params.prize).phrase, caretaker=helper.id))
    activity = _safe_lookup(ACTIVITIES, params.activity)

    hero.memes["curiosity"] += 1
    hero.memes["worry"] += 1
    prize.meters["clean"] += 1
    world.say(f"{hero.id} came to {world.place.name} with {hero.pronoun('possessive')} {prize.label} plan.")
    world.say(f"{hero.id} wanted to {activity.verb}, because the day needed a little extra comedy.")

    world.para()
    world.say(
        f"Then the {prize.label} went missing for a minute, and everyone looked at the coarsest clue in the room: {activity.clue} on the supply shelf."
    )
    helper.memes["embarrassment"] += 1
    world.say(
        f"{helper.id} squinted at the shelf and said, \"Oh no, I only set the {prize.label} near the napkins.\""
    )
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} briefly thought {helper.pronoun('subject')} had taken it for good, which made the whole mystery feel very dramatic for a snack table problem."
    )

    world.para()
    world.say(
        f"Together they hunted for clues. The answer was tiny and silly: the {prize.label} had been moved behind a box while someone tried to {activity.verb} around the crowded room."
    )
    resolve_mystery(world, hero, prize, activity.clue)
    world.say(
        f"{helper.id} laughed, {hero.id} laughed too, and the two of them stopped being suspicious of each other."
    )
    hero.memes["reconciliation"] += 1
    helper.memes["reconciliation"] += 1
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1

    world.para()
    world.say(
        f"In the end, {hero.id} carried the {prize.label} back to the table, now looking clean and proud, and {helper.id} promised to label the shelf before the next snack-time mystery."
    )

    world.facts = {
        "hero": hero,
        "helper": helper,
        "prize": prize,
        "activity": activity,
        "params": params,
    }
    return world


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, activity, prize = f["hero"], f["helper"], f["activity"], f["prize"]
    return [
        f'Write a short comedy story for young children set in a community center that includes the word "{activity.keyword}".',
        f"Tell a gentle mystery where {hero.id} and {helper.id} search for a {prize.label} and then make up after a silly misunderstanding.",
        f"Write a story about a {prize.label}, a clue, and a small mix-up that gets solved with laughter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, activity, prize = f["hero"], f["helper"], f["activity"], f["prize"]
    return [
        QAItem(
            question=f"Where does {hero.id} look for the missing {prize.label}?",
            answer=f"{hero.id} looks for it at the community center with {helper.id}, because that is where the snack-table mix-up happened.",
        ),
        QAItem(
            question=f"What made the mystery funny instead of scary?",
            answer=f"It was funny because the {prize.label} was only moved, not stolen, and everyone had been worrying about a simple shelf mistake.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} feel at the end?",
            answer=f"They felt relieved and reconciled. They laughed, stopped blaming each other, and put the {prize.label} back where it belonged.",
        ),
        QAItem(
            question=f"What clue did they follow to solve the mystery?",
            answer=f"They followed the clue of the {activity.clue} and the messy little shelf area near the supply table.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a community center?",
            answer="A community center is a place where people gather for games, classes, snacks, and events.",
        ),
        QAItem(
            question="What does reconcile mean?",
            answer="To reconcile means to make up after a disagreement and feel friendly again.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle about something unknown that people try to figure out by looking for clues.",
        ),
        QAItem(
            question="What does coarse mean?",
            answer="Coarse means rough or not smooth, like a scratchy cloth or a bumpy surface.",
        ),
        QAItem(
            question="What does hone mean?",
            answer="To hone something means to sharpen it or improve it with careful practice.",
        ),
        QAItem(
            question="What is a platter?",
            answer="A platter is a large flat dish used for serving food.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(activity="bake", prize="platter", name="Maya", helper="Ms. Pru"),
    StoryParams(activity="craft", prize="tray", name="Noah", helper="Mr. Lane"),
    StoryParams(activity="share", prize="platter", name="Ivy", helper="Auntie June"),
]


ASP_RULES = r"""
place(community_center).
activity(bake). activity(craft). activity(share).
prize(platter). prize(tray).

affords(community_center,bake).
affords(community_center,craft).
affords(community_center,share).

valid(Place,A,P) :- place(Place), activity(A), prize(P), affords(Place,A).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "community_center")]
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    lines.append(asp.fact("affords", "community_center", "bake"))
    lines.append(asp.fact("affords", "community_center", "craft"))
    lines.append(asp.fact("affords", "community_center", "share"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_py() -> list[tuple[str, str, str]]:
    return [("community_center", a, p) for a in ACTIVITIES for p in PRIZES]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos_py())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    act = getattr(args, "activity", None) or rng.choice(list(ACTIVITIES))
    pr = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    if (PLACE.name, act, pr) not in valid_combos_py():
        pass
    return StoryParams(
        activity=act,
        prize=pr,
        name=getattr(args, "name", None) or rng.choice(GIVEN_NAMES),
        helper=getattr(args, "helper", None) or rng.choice(HELPERS),
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
            params = build_story_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.activity} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
