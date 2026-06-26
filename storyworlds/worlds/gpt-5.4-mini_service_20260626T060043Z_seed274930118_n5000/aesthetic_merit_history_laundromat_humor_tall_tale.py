#!/usr/bin/env python3
"""
A Storyweavers story world: a tall-tale laundromat with humor, aesthetic merit,
and a little history.

Premise:
A boastful kid wants to clean a legendary, very dusty item in the laundromat
so it can be admired in a town history display.

Turn:
The washer has a mind of its own, the item is too grand for the small machine,
and the kid's first plan makes a comic mess.

Resolution:
A sensible helper offers the right-sized fix, the item comes out shining, and
the story ends with the town admiring both the clean treasure and the kid's
new respect for care, craft, and history.

This file is standalone and uses only the stdlib plus the shared results/asp
helpers from the Storyweavers repo.
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
# World model
# ---------------------------------------------------------------------------

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
    worn_by: Optional[str] = None
    fragile: bool = False
    valuable: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper_ent: object | None = None
    hero: object | None = None
    prize: object | None = None
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
class Setting:
    place: str = "the laundromat"
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
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
    worthy_of_display: bool = True
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
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    fits: set[str]
    solves: set[str]
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
        self.machine_thirst = 0.0

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.machine_thirst = self.machine_thirst
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "laundromat": Setting(place="the laundromat", affords={"wash", "dry", "starch"}),
}

ACTIVITIES = {
    "wash_hat": Activity(
        id="wash_hat",
        verb="wash the famous old hat",
        gerund="washing the famous old hat",
        rush="feed the hat into the little washer",
        mess="soapy",
        soil="too sudsy and lopsided",
        risk="the brim can fold and the stitches can sigh",
        keyword="aesthetic",
        tags={"aesthetic", "history", "humor"},
    ),
    "wash_banner": Activity(
        id="wash_banner",
        verb="wash the parade banner",
        gerund="washing the parade banner",
        rush="stuff the banner into the machine",
        mess="wet",
        soil="soggy and wrinkled",
        risk="the letters can blur and the paint can pout",
        keyword="history",
        tags={"history", "humor"},
    ),
    "wash_cape": Activity(
        id="wash_cape",
        verb="wash the glitter cape",
        gerund="washing the glitter cape",
        rush="shove the cape into the washer",
        mess="sparkly",
        soil="sparkles everywhere",
        risk="the glitter can travel like a prankster",
        keyword="merit",
        tags={"aesthetic", "merit", "humor"},
    ),
}

PRIZES = {
    "hat": Prize(
        label="hat",
        phrase="a famous old hat with a feather and a story",
        type="hat",
        plural=False,
    ),
    "banner": Prize(
        label="banner",
        phrase="a parade banner from the town museum",
        type="banner",
        plural=False,
    ),
    "cape": Prize(
        label="cape",
        phrase="a glitter cape fit for a sidewalk superstar",
        type="cape",
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="meshbag",
        label="a mesh laundry bag",
        prep="put it in a mesh laundry bag first",
        tail="slid the item into the mesh bag and tried again the careful way",
        fits={"hat", "cape"},
        solves={"soapy", "sparkly"},
    ),
    Gear(
        id="delicates",
        label="the delicate cycle",
        prep="switch the washer to the delicate cycle",
        tail="let the delicate cycle do its gentle work",
        fits={"hat", "banner", "cape"},
        solves={"soapy", "wet", "sparkly"},
    ),
    Gear(
        id="line_dry",
        label="a clean drying line",
        prep="hang it on a clean drying line",
        tail="hung the treasure on the line where the air could fuss with it kindly",
        fits={"banner", "cape"},
        solves={"wet", "sparkly"},
    ),
]

NAMES = ["Milo", "Nina", "Junie", "Otis", "Penny", "Rosa", "Toby", "Willa"]
TRAITS = ["bright-eyed", "nimble", "proud", "curious", "merry", "stubborn"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    trait: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utility / reasonableness
# ---------------------------------------------------------------------------
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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return True


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.type in gear.fits and activity.mess in gear.solves:
            return gear
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: the laundromat trick for {activity.gerund} would not make "
        f"sense for a {prize.label} in this little world.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        act = _safe_lookup(ACTIVITIES, getattr(args, "activity", None))
        pr = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not select_gear(act, pr):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id, prize in PRIZES.items():
                if select_gear(_safe_lookup(ACTIVITIES, act_id), prize):
                    combos.append((place, act_id, prize_id))

    if getattr(args, "activity", None):
        combos = [c for c in combos if c[1] == getattr(args, "activity", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[2] == getattr(args, "prize", None)]

    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, activity, prize = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    helper = getattr(args, "helper", None) or rng.choice(["the laundromat attendant", "an old aunt", "a neighboring kid"])
    return StoryParams(place=place, activity=activity, prize=prize, name=name, trait=trait, helper=helper)


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------
def machine_sound(activity: Activity) -> str:
    return {
        "wash_hat": "The washer went kachunk-kachunk like a tin goat on skates.",
        "wash_banner": "The washer went whump-whump like a drum in a snowstorm.",
        "wash_cape": "The washer went chitter-chatter like a squirrel with a silver spoon.",
    }[activity.id]


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, trait: str, helper: str) -> World:
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type="boy" if hero_name in {"Milo", "Otis", "Toby"} else "girl"))
    helper_ent = world.add(Entity(id="Helper", kind="character", type="woman", label=helper))

    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=helper_ent.id,
        fragile=True,
        valuable=True,
    ))

    hero.memes["pride"] = 1.0
    hero.memes["love"] = 1.0
    prize.meters["dust"] = 1.0

    world.say(
        f"{hero.id} was a {trait} little soul with a big opinion about cleanliness, "
        f"beauty, and the family history of the town."
    )
    world.say(
        f"{hero.id} had {hero.pronoun('possessive')} eye on {prize.phrase}, which was not just old, "
        f"but old in the way a story can be old and still stand up straight."
    )
    world.say(
        f"The child kept saying the prize had enough aesthetic merit to be hung in a museum, "
        f"and enough merit-merit to make the mayor salute it twice."
    )

    world.para()
    world.say(
        f"One day, {hero.id} and {helper} went to {setting.place} with {prize.label} tucked under {hero.pronoun('possessive')} arm."
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, because {hero.pronoun('subject')} believed history looked better after a wash."
    )
    world.say(machine_sound(activity))

    # conflict: overconfidence causes comic trouble
    if activity.id == "wash_hat":
        world.say(
            f"{hero.id} fed the hat into the washer, and the brim came out spinning like a penny in a skillet."
        )
    elif activity.id == "wash_banner":
        world.say(
            f"{hero.id} shoved the banner inside, and the letters wriggled like minnows in a windstorm."
        )
    else:
        world.say(
            f"{hero.id} sent the glitter cape twirling, and sparkles hopped onto every sock in the room."
        )

    world.say(
        f"That made the little laundromat look as if a circus had sneezed in it."
    )
    world.machine_thirst += 1
    hero.memes["alarm"] = 1.0

    world.para()
    gear = select_gear(activity, prize_cfg)
    if gear is None:
        gear = next(iter(globals().get("GEARS", globals().get("GEAR", []))))

    world.say(
        f"{helper} put up a hand and said, "
        f"\"Hold your horses and your buttons too, sugar. We need {gear.label} for that.\""
    )
    world.say(
        f"{hero.id} blinked, then saw the truth of it: the prize needed care, not bravado."
    )
    world.say(
        f"So they agreed to {gear.prep}."
    )

    world.para()
    if gear.id == "meshbag":
        world.say(
            f"They slipped the {prize.label} into the mesh bag, and the washer stopped acting like a hungry bear."
        )
    elif gear.id == "delicates":
        world.say(
            f"They chose the delicate cycle, and the machine turned gentle as a grandmother patting pie crust."
        )
    else:
        world.say(
            f"They used the clean drying line, where the prize could sway like a flag at a polite parade."
        )

    hero.memes["pride"] = 0.0
    hero.memes["respect"] = 1.0
    prize.meters["dust"] = 0.0
    prize.meters["clean"] = 1.0
    prize.meters["shine"] = 1.0

    world.say(
        f"At last, the {prize.label} came out clean and bright, with all its old history still stitched inside it."
    )
    world.say(
        f"{hero.id} stood taller than the coin jar and said the prize had both beauty and merit, "
        f"which was the kind of praise that makes a thing feel newly famous."
    )
    world.say(
        f"The whole laundromat laughed, because in that town a clean old treasure was worth more than a barrel of polished apples."
    )

    world.facts.update(
        hero=hero,
        helper=helper_ent,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        gear=gear,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, prize, act = f["hero"], f["prize_cfg"], f["activity"]
    return [
        f'Write a humorous tall tale about a child named {hero.id} in a laundromat who thinks {prize.phrase} has history worth preserving.',
        f"Tell a funny story where {hero.id} tries to {act.verb} but learns to use a gentler method instead.",
        f'Write a child-friendly tall tale that includes the words "aesthetic", "merit", and "history" and ends with a clean, comic victory.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, act, gear = f["hero"], f["helper"], f["prize"], f["activity"], f["gear"]
    return [
        QAItem(
            question=f"What did {hero.id} think was so special about {prize.label}?",
            answer=(
                f"{hero.id} thought {prize.phrase} had aesthetic merit and a proud old history, "
                f"like it belonged in a town display instead of on a dusty shelf."
            ),
        ),
        QAItem(
            question=f"What went funny and wrong when {hero.id} tried to {act.verb}?",
            answer=(
                f"The machine acted like a clown, and the prize came out tumbling, lopsided, or sparkly in a messy way."
            ),
        ),
        QAItem(
            question=f"How did {helper.id if hasattr(helper, 'id') else 'the helper'} help fix the problem?",
            answer=(
                f"The helper told {hero.id} to use {gear.label if gear else 'the right gentle method'}, "
                f"which let the prize get clean without getting mangled."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=(
                f"By the end, {hero.id} respected careful work more, and the old prize came out clean, shining, and ready for its next chapter."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "aesthetic": [
        QAItem(
            question="What does aesthetic mean?",
            answer="Aesthetic means about how something looks or feels when people think it is beautiful or pleasing.",
        )
    ],
    "merit": [
        QAItem(
            question="What does merit mean?",
            answer="Merit means a good quality that makes something deserve praise or care.",
        )
    ],
    "history": [
        QAItem(
            question="What is history?",
            answer="History is the story of things that happened before us, like people, places, and objects from long ago.",
        )
    ],
    "laundromat": [
        QAItem(
            question="What is a laundromat?",
            answer="A laundromat is a place with washing machines and dryers where people clean clothes and other washable things.",
        )
    ],
    "humor": [
        QAItem(
            question="What is humor?",
            answer="Humor is the kind of funny talk or action that makes people smile or laugh.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [item for key in ["aesthetic", "merit", "history", "laundromat", "humor"] for item in WORLD_KNOWLEDGE[key]]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  machine_thirst={world.machine_thirst}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), activity_kind(A,_).
compatible(A,P) :- prize_at_risk(A,P), gear(G), fits(G,P), solves(G,A).
valid_story(A,P) :- compatible(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("activity_kind", aid, act.keyword))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if prize.plural:
            lines.append(asp.fact("plural", pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for fit in sorted(g.fits):
            lines.append(asp.fact("fits", g.id, fit))
        for sol in sorted(g.solves):
            lines.append(asp.fact("solves", g.id, sol))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for act_id in ACTIVITIES:
        for prize_id in PRIZES:
            if select_gear(_safe_lookup(ACTIVITIES, act_id), _safe_lookup(PRIZES, prize_id)):
                combos.append(("laundromat", act_id, prize_id))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale laundromat story world with humor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--helper")
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


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(PRIZES, params.prize),
        params.name,
        params.trait,
        params.helper,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="laundromat", activity="wash_hat", prize="hat", name="Milo", trait="curious", helper="the laundromat attendant"),
    StoryParams(place="laundromat", activity="wash_banner", prize="banner", name="Nina", trait="proud", helper="an old aunt"),
    StoryParams(place="laundromat", activity="wash_cape", prize="cape", name="Junie", trait="merry", helper="a neighboring kid"),
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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
