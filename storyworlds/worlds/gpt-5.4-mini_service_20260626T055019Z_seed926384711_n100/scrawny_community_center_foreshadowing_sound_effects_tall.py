#!/usr/bin/env python3
"""
storyworlds/worlds/scrawny_community_center_foreshadowing_sound_effects_tall.py
===============================================================================

A small, self-contained story world about a scrawny kid at a community center,
with foreshadowing and sound effects in a tall-tale style.

Premise:
A scrawny child wants to join a big community-center event, but the stage door
and the old equipment make ominous sounds that hint at trouble. A helper notices
the danger, fixes the problem, and the child finishes the night in a grand,
crowd-pleasing way.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    helper: object | None = None
    hero: object | None = None
    prize_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
    id: str
    label: str
    echoes: bool = False
    affords: set[str] = field(default_factory=set)
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
    sound: str
    foreshadow: str
    risk: str
    result: str
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
    id: str
    label: str
    phrase: str
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


@dataclass
class Helper:
    id: str
    label: str
    fix: str
    tail: str
    tags: set[str] = field(default_factory=set)
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
    activity: str
    prize: str
    name: str
    gender: str
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
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
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


PLACES = {
    "community_center": Place(
        id="community_center",
        label="the community center",
        echoes=True,
        affords={"stage", "dance", "drums"},
    ),
}

ACTIVITIES = {
    "stage": Activity(
        id="stage",
        verb="climb onto the stage",
        gerund="climbing onto the stage",
        sound="creeeak",
        foreshadow="The floorboards gave a long, lonely creak, like a warning whisper.",
        risk="a wobble would make the spotlight swing and the curtain snarl",
        result="stood steady under the lights",
        tags={"sound_effects", "foreshadowing", "tall_tale"},
    ),
    "dance": Activity(
        id="dance",
        verb="dance in the hall",
        gerund="dancing in the hall",
        sound="tap-tap-tap",
        foreshadow="The old tiles tapped back, as if they knew a big step was coming.",
        risk="a slip would spill the music and tangle the rhythm",
        result="whirled like a weather vane in a storm",
        tags={"sound_effects", "foreshadowing", "tall_tale"},
    ),
    "drums": Activity(
        id="drums",
        verb="bang the big drum",
        gerund="banging the big drum",
        sound="boom-boom-BOOM",
        foreshadow="The drumskin hummed once, low and deep, like thunder saving up its voice.",
        risk="a loose strap would flop and flatten the whole parade of sound",
        result="made the windows grin with vibration",
        tags={"sound_effects", "foreshadowing", "tall_tale"},
    ),
}

PRIZES = {
    "badge": Prize(
        id="badge",
        label="community badge",
        phrase="a shiny community badge",
        region="chest",
    ),
    "banner": Prize(
        id="banner",
        label="banner ribbon",
        phrase="a bright banner ribbon",
        region="hands",
        plural=False,
    ),
    "shoes": Prize(
        id="shoes",
        label="tap shoes",
        phrase="a pair of tap shoes",
        region="feet",
        plural=True,
    ),
}

HELPERS = {
    "janitor": Helper(
        id="janitor",
        label="the janitor",
        fix="tighten the loose screw",
        tail="the janitor gave the wheel a firm twist, and the whole cart settled down like a tired colt",
        tags={"repair", "sound_effects"},
    ),
    "leader": Helper(
        id="leader",
        label="the center leader",
        fix="tie the curtain rope",
        tail="the center leader looped the rope, and the curtain held still as a church mouse",
        tags={"foreshadowing", "helper"},
    ),
    "coach": Helper(
        id="coach",
        label="the coach",
        fix="lace the shoes snugly",
        tail="the coach laced the shoes snug, and the little feet found their brave rhythm",
        tags={"sound_effects", "helper"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for act_id in place.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if act_id == "stage" and prize.region in {"chest", "hands"}:
                    combos.append((place_id, act_id, prize_id))
                if act_id == "dance" and prize.region in {"feet", "hands"}:
                    combos.append((place_id, act_id, prize_id))
                if act_id == "drums" and prize.region in {"hands", "chest"}:
                    combos.append((place_id, act_id, prize_id))
    return combos


def select_helper(activity: Activity, prize: Prize) -> Optional[Helper]:
    if activity.id == "stage":
        return HELPERS["leader"] if prize.region == "chest" else HELPERS["janitor"]
    if activity.id == "dance":
        return HELPERS["coach"] if prize.region == "feet" else HELPERS["leader"]
    if activity.id == "drums":
        return HELPERS["janitor"] if prize.region == "chest" else HELPERS["coach"]
    return None


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    if activity.id == "stage":
        return prize.region in {"chest", "hands"}
    if activity.id == "dance":
        return prize.region in {"feet", "hands"}
    if activity.id == "drums":
        return prize.region in {"hands", "chest"}
    return False


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.verb} does not reasonably threaten {prize.phrase} in this little world.)"
    )


ASP_RULES = r"""
prize_at_risk(A,P) :- risky_region(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), helper_fix(A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.echoes:
            lines.append(asp.fact("echoes", pid))
        for act in sorted(place.affords):
            lines.append(asp.fact("affords", pid, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for tag in sorted(act.tags):
            lines.append(asp.fact("tag", aid, tag))
        if act.id == "stage":
            lines.append(asp.fact("risky_region", aid, "chest"))
            lines.append(asp.fact("risky_region", aid, "hands"))
        elif act.id == "dance":
            lines.append(asp.fact("risky_region", aid, "feet"))
            lines.append(asp.fact("risky_region", aid, "hands"))
        elif act.id == "drums":
            lines.append(asp.fact("risky_region", aid, "hands"))
            lines.append(asp.fact("risky_region", aid, "chest"))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for tag in sorted(helper.tags):
            lines.append(asp.fact("helper_tag", hid, tag))
    # helper_fix facts by compatibility
    lines.append(asp.fact("helper_fix", "stage", "badge"))
    lines.append(asp.fact("helper_fix", "stage", "banner"))
    lines.append(asp.fact("helper_fix", "dance", "shoes"))
    lines.append(asp.fact("helper_fix", "drums", "badge"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(python_set - clingo_set))
    print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world at a community center.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(["Mabel", "Ezra", "Nina", "Otis", "June", "Wes"])
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, helper=helper)


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    act = _safe_lookup(ACTIVITIES, params.activity)
    prize = _safe_lookup(PRIZES, params.prize)
    helper_def = _safe_lookup(HELPERS, params.helper)

    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.gender == "girl" else "boy"))
    helper = world.add(Entity(id="Helper", kind="character", type="woman", label=helper_def.label))
    prize_ent = world.add(Entity(id="Prize", label=prize.label, phrase=prize.phrase, region=prize.region, plural=prize.plural, caretaker=helper.id))

    world.say(
        f"{hero.id} was a scrawny little {params.gender} with a big heart and shoes that seemed to carry a tune all by themselves."
    )
    world.say(
        f"{hero.id} came to {place.label} where even the doors had a habit of whispering and the benches had memory in their wood."
    )
    world.say(
        f"{hero.id} wore {prize_ent.phrase}, and the whole hall shone as if it had swallowed a pocketful of stars."
    )
    world.say(
        f"{hero.id} wanted to {act.verb}, and the first clue came before the second step: {act.foreshadow}"
    )

    if not prize_at_risk(act, prize):
        pass

    world.say(
        f"Then came the sound of trouble: {act.sound}! It bounced off the walls of {place.label} like a marble in a kettle."
    )
    world.say(
        f"{hero.id} climbed closer, but the old setup made {act.risk}."
    )
    world.say(
        f"The crowd sucked in one breath, and it sounded like the whole room said, \"Ooooh.\""
    )

    helper = world.get("Helper")
    world.say(
        f"{helper.label} squinted at the scene and said that a storm often leaves a shadow before the rain ever falls."
    )
    world.say(
        f"Sure enough, {helper_def.fix} would keep the trouble from growing teeth."
    )
    world.say(helper_def.tail + ".")
    world.say(
        f"After that, {hero.id} went on to {act.result}, and the hall rang with {act.sound} again, only this time it sounded like applause."
    )
    world.say(
        f"{hero.id} ended the night not as a scrawny kid in a giant room, but as the little spark that lit up the whole community center."
    )

    world.facts.update(hero=hero, helper=helper, prize=prize_ent, prize_def=prize, activity=act, place=place, helper_def=helper_def)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize_def"]
    return [
        f'Write a tall tale about a scrawny child at {world.place.label} where a sound warns of trouble before {hero.id} {act.verb}.',
        f"Tell a child-friendly community-center story with foreshadowing and a big sound effect, ending in a happy fix for {prize.phrase}.",
        f'Write a short story that includes "{act.sound}" and shows how a scrawny kid becomes brave at the community center.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, act, prize, helper = f["hero"], f["activity"], f["prize_def"], f["helper_def"]
    return [
        QAItem(
            question=f"Who was the scrawny child in the story?",
            answer=f"The scrawny child was {hero.id}, who came to {world.place.label} with a big wish and a small frame.",
        ),
        QAItem(
            question=f"What sound warned that trouble was coming?",
            answer=f"The sound was {act.sound}, and it hinted that {act.risk}.",
        ),
        QAItem(
            question=f"Who helped fix the problem?",
            answer=f"{helper.label} helped by using a careful fix so {hero.id} could safely keep going.",
        ),
        QAItem(
            question=f"What happened after the problem was fixed?",
            answer=f"{hero.id} went on to {act.result}, and the room turned the tense sound into cheerful applause.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a community center?",
            answer="A community center is a place where people gather for activities, classes, games, and events.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a small clue that something important or tricky may happen soon.",
        ),
        QAItem(
            question="Why do stories use sound effects?",
            answer="Stories use sound effects to make scenes feel lively, surprising, and easy to imagine.",
        ),
        QAItem(
            question="What makes a tall tale feel extra big?",
            answer="A tall tale makes ordinary things sound larger than life, with bold details, funny exaggeration, and a grand ending.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.region:
            bits.append(f"region={e.region}")
        if e.plural:
            bits.append("plural=True")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="community_center", activity="stage", prize="badge", name="Milo", gender="boy", helper="leader"),
    StoryParams(place="community_center", activity="dance", prize="shoes", name="Ruby", gender="girl", helper="coach"),
    StoryParams(place="community_center", activity="drums", prize="banner", name="Theo", gender="boy", helper="janitor"),
]


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify_full() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_full())
    if getattr(args, "asp", None):
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible (place, activity, prize) combos:")
        for item in combos:
            print(" ", item)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
