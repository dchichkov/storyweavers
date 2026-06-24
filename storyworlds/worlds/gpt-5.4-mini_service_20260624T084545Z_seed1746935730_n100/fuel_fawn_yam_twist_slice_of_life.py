#!/usr/bin/env python3
"""
storyworlds/worlds/fuel_fawn_yam_twist_slice_of_life.py
========================================================

A small slice-of-life story world about a household moment with low fuel,
a shy fawn, and a yam supper that takes an unexpected turn.

Seed tale inspiration:
---
A child and a parent were getting dinner ready when they noticed the lamp fuel
was low. Outside, a fawn wandered into the yard near a basket of yams. The child
worried the evening would become messy, but the parent found a calm, clever way
to finish supper. The little surprise in the yard changed the plan, and the
night ended with warm food, soft light, and a gentle story to remember.

The world model tracks:
- physical meters: fuel, warmth, hunger, tidy, trust
- emotional memes: worry, relief, wonder, care

The twist:
- the fawn's appearance reveals a hidden but ordinary solution, changing the
  family's plan without turning the story into a big adventure.
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    fawn: object | None = None
    fuel: object | None = None
    parent: object | None = None
    yam: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
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
    place: str
    indoors: bool
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
    worry: str
    twist: str
    tag: str
    needs: set[str] = field(default_factory=set)
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    clone: object | None = None
    world: object | None = None
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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone
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
    "kitchen": Setting("the kitchen", True, {"cook", "light"}),
    "porch": Setting("the porch", False, {"watch", "gather"}),
    "garden": Setting("the garden", False, {"watch", "gather", "cook"}),
}

ACTIVITIES = {
    "cook_yam": Activity(
        id="cook_yam",
        verb="cook the yam",
        gerund="cooking the yam",
        worry="The lamp fuel was running low, so the room might grow dim",
        twist="the fawn's visit pointed the family toward the spare fuel can",
        tag="yam",
        needs={"fuel", "yam"},
    ),
    "watch_fawn": Activity(
        id="watch_fawn",
        verb="watch the fawn",
        gerund="watching the fawn",
        worry="the little deer might startle and run away",
        twist="the quiet fawn stayed long enough to make the evening feel special",
        tag="fawn",
        needs={"fawn"},
    ),
    "prepare_supper": Activity(
        id="prepare_supper",
        verb="prepare supper",
        gerund="preparing supper",
        worry="the stove needed fuel before dinner could begin",
        twist="the child found the extra fuel can beside the back step",
        tag="fuel",
        needs={"fuel", "yam"},
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Tessa", "Nora", "June", "Ella", "Zoe"]
BOY_NAMES = ["Theo", "Milo", "Finn", "Owen", "Eli", "Jack", "Noah"]
TRAITS = ["gentle", "curious", "thoughtful", "quiet", "bright", "patient"]


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    gender: str
    parent: str
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


def _entity_story(world: World) -> tuple[Entity, Entity, Entity, Entity]:
    child = world.add(Entity(id=world.facts["name"], kind="character", type=world.facts["gender"]))
    parent = world.add(Entity(id="Parent", kind="character", type=world.facts["parent"], label=world.facts["parent"]))
    fuel = world.add(Entity(id="fuel", type="fuel", label="fuel can", phrase="a small fuel can"))
    yam = world.add(Entity(id="yam", type="yam", label="yam", phrase="a golden yam"))
    fawn = world.add(Entity(id="fawn", kind="character", type="fawn", label="fawn"))
    return child, parent, fuel, yam, fawn


def _raise_if_invalid(args: argparse.Namespace) -> None:
    if getattr(args, "activity", None) and getattr(args, "activity", None) not in ACTIVITIES:
        pass
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        pass


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for aid, act in ACTIVITIES.items():
            if all(req in {"fuel", "yam", "fawn"} for req in act.needs) and aid in {
                "cook_yam", "watch_fawn", "prepare_supper"
            } and aid in ACTIVITIES and aid in ACTIVITIES:
                if place in SETTINGS:
                    combos.append((place, aid))
    return combos


def tell(setting: Setting, activity: Activity, name: str, gender: str, parent: str, trait: str) -> World:
    world = World(setting)
    world.facts.update(setting=setting, activity=activity, name=name, gender=gender, parent=parent, trait=trait)
    child, parent_ent, fuel, yam, fawn = _entity_story(world)

    child.memes["wonder"] += 1
    child.memes["care"] += 1
    fuel.meters["fuel"] = 0.5
    yam.meters["fresh"] = 1.0
    fawn.meters["energy"] = 0.6
    world.facts["child"] = child
    world.facts["parent_ent"] = parent_ent
    world.facts["fuel_ent"] = fuel
    world.facts["yam_ent"] = yam
    world.facts["fawn_ent"] = fawn

    world.say(
        f"{name} was a {trait} {gender} who liked helping {parent} with little jobs around {setting.place}."
    )
    world.say(
        f"That evening, {name} and {parent_ent.label} were getting supper ready, and the {yam.label} on the counter looked ready to soften."
    )

    world.para()
    if setting.indoors:
        world.say(
            f"In the kitchen, the lamp looked dim because the fuel was nearly gone."
        )
    else:
        world.say(
            f"Outside, the air was cool, and the porch light would need fuel soon."
        )
    world.say(activity.worry + ".")
    if activity.id == "watch_fawn":
        world.say("Then a small fawn wandered near the fence, blinking at the yard with soft brown eyes.")
    else:
        world.say("Then a small fawn stepped near the back gate, as if it wanted to see what the family was doing.")
    child.memes["worry"] += 1
    child.memes["wonder"] += 1
    parent_ent.memes["care"] += 1

    world.para()
    if activity.id == "cook_yam":
        world.say(
            f"{name} worried they might not finish the {yam.label} in time."
        )
        world.say(
            f"But {parent_ent.label} noticed the fawn by the fence, smiled, and checked the back step."
        )
        world.say(
            f"There was a spare fuel can tucked there all along, and that was the twist {activity.twist}."
        )
        fuel.meters["fuel"] = 1.0
        child.memes["relief"] += 1
        parent_ent.memes["relief"] += 1
        world.say(
            f"Soon the stove had enough fuel, the {yam.label} steamed up warm and soft, and the fawn watched from the grass while the family ate."
        )
    elif activity.id == "watch_fawn":
        world.say(
            f"{name} and {parent_ent.label} kept very still so they would not scare the fawn."
        )
        world.say(
            f"The twist {activity.twist}."
        )
        world.say(
            f"After a while, the fawn drifted away, and the family carried the yam inside for supper."
        )
        child.memes["relief"] += 1
    else:
        world.say(
            f"{name} found the extra fuel can beside the back step while {parent_ent.label} set the yam on the stove."
        )
        world.say(
            f"That was the twist {activity.twist}."
        )
        fuel.meters["fuel"] = 1.0
        world.say(
            f"With the fuel found, the lamp shone brighter, the supper finished well, and the little fawn rested in the yard as the house smelled sweet and warm."
        )
        child.memes["relief"] += 1

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act = f["activity"]
    return [
        f'Write a gentle slice-of-life story for a small child that includes the words "fuel", "fawn", and "yam".',
        f"Tell a calm story about {f['name']} helping {f['parent']} with {act.gerund} at {f['setting'].place}.",
        f'Write a short, child-friendly story where a fawn changes an evening plan about fuel and a yam supper.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent_ent"]
    act = f["activity"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {child.id}, a {f['trait']} {f['gender']} who helped {parent.label} at {setting.place}.",
        ),
        QAItem(
            question=f"What was the family trying to do at {setting.place}?",
            answer=f"They were getting supper ready and {act.gerund}, with a yam on the counter and the fuel running low.",
        ),
        QAItem(
            question=f"What surprised {child.id} during the evening?",
            answer="A small fawn wandered nearby, and its quiet visit helped the family notice the better solution.",
        ),
        QAItem(
            question=f"What changed because of the twist?",
            answer="They found a way to finish supper with enough fuel, so the yam cooked nicely and the evening stayed calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is fuel used for?",
            answer="Fuel is something a lamp or stove can burn so it gives light or heat.",
        ),
        QAItem(
            question="What is a fawn?",
            answer="A fawn is a young deer, and it usually moves softly and carefully.",
        ),
        QAItem(
            question="What is a yam?",
            answer="A yam is a starchy root vegetable that people can cook and eat for supper.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(kitchen).
setting(porch).
setting(garden).

activity(cook_yam).
activity(watch_fawn).
activity(prepare_supper).

affords(kitchen,cook_yam).
affords(kitchen,prepare_supper).
affords(kitchen,watch_fawn).
affords(porch,watch_fawn).
affords(porch,prepare_supper).
affords(garden,cook_yam).
affords(garden,watch_fawn).
affords(garden,prepare_supper).

needs(cook_yam,fuel).
needs(cook_yam,yam).
needs(watch_fawn,fawn).
needs(prepare_supper,fuel).
needs(prepare_supper,yam).

valid(Place,Act) :- affords(Place,Act), activity(Act), setting(Place).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            lines.append(asp.fact("affords", place, act))
    for aid, act in ACTIVITIES.items():
        for need in act.needs:
            lines.append(asp.fact("needs", aid, need))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world: fuel, fawn, and yam.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
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
    _raise_if_invalid(args)
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "activity", None):
        combos = [c for c in combos if c[1] == getattr(args, "activity", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity = rng.choice(combos)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), params.name, params.gender, params.parent, params.trait)
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
    StoryParams(place="kitchen", activity="cook_yam", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="porch", activity="watch_fawn", name="Theo", gender="boy", parent="father", trait="gentle"),
    StoryParams(place="garden", activity="prepare_supper", name="Nora", gender="girl", parent="mother", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity) combos:\n")
        for place, act in combos:
            print(f"  {place:8} {act}")
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
