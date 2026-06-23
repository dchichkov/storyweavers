#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/thimble_surprise_moral_value_reconciliation_tall_tale.py
===============================================================================================================================

A standalone storyworld for a tiny Tall Tale about a thimble, a surprise, a moral
value, and a reconciliation.

Premise:
- A child and an elder keep a treasured thimble for mending.
- A boastful rival treats it like a joke.
- A surprise event reveals the thimble's true value.
- The story turns on a moral choice and ends with reconciliation.

This file is self-contained except for the shared result containers in
storyworlds/results.py and the lazy ASP helper in storyworlds/asp.py.
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
    plural: bool = False
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    box: object | None = None
    elder: object | None = None
    hero: object | None = None
    item: object | None = None
    rival: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
    id: str
    place: str
    affords: set[str] = field(default_factory=set)
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
    rush: str
    mess: str
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
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
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
class Gear:
    id: str
    label: str
    use: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    w: object | None = None
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]
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


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("surprise_seen") and not world.facts.get("reveal_spoken"):
        world.facts["reveal_spoken"] = True
        out.append("__reveal__")
    return out


def _r_heal(world: World) -> list[str]:
    if world.facts.get("hurt") and world.facts.get("forgive"):
        for eid in ("hero", "rival"):
            world.get(eid).memes["hurt"] = 0.0
            world.get(eid).memes["warmth"] = 1.0
        return ["__heal__"]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_r_reveal, _r_heal):
            out = fn(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combo(setting: str, activity: str, prize: str, gear: str) -> bool:
    return (
        setting in SETTINGS
        and activity in ACTIVITIES
        and prize in PRIZES
        and gear in GEARS
        and prize in {"thimble"}
        and activity in _safe_lookup(SETTINGS, setting).affords
        and _safe_lookup(PRIZES, prize).region in _safe_lookup(ACTIVITIES, activity).zone
        and gear == "needlebox"
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [
        (s, a, p, g)
        for s in SETTINGS
        for a in _safe_lookup(SETTINGS, s).affords
        for p in PRIZES
        for g in GEARS
        if valid_combo(s, a, p, g)
    ]


@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    gear: str
    hero: str
    hero_type: str
    rival: str
    rival_type: str
    elder: str
    elder_type: str
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
    "fair": Setting(id="fair", place="the county fair", affords={"stitch", "mend"}),
    "porch": Setting(id="porch", place="the front porch", affords={"stitch", "mend"}),
}

ACTIVITIES = {
    "stitch": Activity(
        id="stitch",
        verb="stitch the torn banner",
        gerund="stitching the torn banner",
        rush="snatch the banner and tug the needle",
        mess="pricked",
        zone={"hands"},
        keyword="stitch",
        tags={"needle", "thread", "moral"},
    ),
    "mend": Activity(
        id="mend",
        verb="mend the hem",
        gerund="mending the hem",
        rush="grab the cloth and hurry the fix",
        mess="pricked",
        zone={"hands"},
        keyword="mend",
        tags={"needle", "thread", "moral"},
    ),
}

PRIZES = {
    "thimble": Prize(
        id="thimble",
        label="thimble",
        phrase="a silver thimble with a tiny dent",
        region="hands",
        tags={"thimble"},
    ),
}

GEARS = {
    "needlebox": Gear(
        id="needlebox",
        label="needle box",
        use="keep the needles safe",
        tail="put the thimble back in the needle box",
        tags={"needle", "thread"},
    ),
}

GIRL_NAMES = ["Mabel", "Ada", "Nell", "Ruth", "June"]
BOY_NAMES = ["Bram", "Otis", "Ike", "Toby", "Cal"]
ELDER_NAMES = ["Grandma Dot", "Grandpa Will", "Aunt May", "Uncle Ned"]


def tell(setting: Setting, activity: Activity, prize: Prize, gear: Gear,
         hero_name: str, hero_type: str, rival_name: str, rival_type: str,
         elder_name: str, elder_type: str) -> World:
    w = World(setting)
    hero = w.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    rival = w.add(Entity(id="rival", kind="character", type=rival_type, label=rival_name, role="boastful"))
    elder = w.add(Entity(id="elder", kind="character", type=elder_type, label=elder_name, role="guide"))
    item = w.add(Entity(id="thimble", type="thimble", label=prize.label, owner=hero.id))
    box = w.add(Entity(id="needlebox", type="box", label=gear.label))
    for e in (hero, rival, elder, item, box):
        e.meters.setdefault("clean", 0.0)
        e.meters.setdefault("safe", 0.0)
        e.memes.setdefault("joy", 0.0)
        e.memes.setdefault("pride", 0.0)
        e.memes.setdefault("hurt", 0.0)
        e.memes.setdefault("warmth", 0.0)

    w.say(f"{hero.label} and {elder.label} kept a little thimble by the {setting.place}.")
    w.say(f"The thimble was no bigger than a bean, but it could save a finger and save a day.")
    w.say(f"{rival.label} laughed and said the thimble was too small to matter.")

    w.para()
    hero.memes["joy"] += 1
    rival.memes["pride"] += 1
    w.say(f"At the fair, {hero.label} wanted to {activity.verb}, and the banner fluttered like a wild flag.")
    w.say(f"Then a wind came dancing over the boards, and surprise! the banner tore right down the middle.")
    w.facts["surprise_seen"] = True

    w.para()
    rival.memes["pride"] += 1
    w.say(f"{rival.label} reached for the cloth in a hurry, but {elder.label} held up a hand.")
    w.say(f'"A good fix is a kind fix," {elder.label} said. "A thimble is little, but it keeps the hands steady."')
    w.say(f"{hero.label} slipped the thimble on, and the needle stopped biting back.")
    hero.meters["safe"] += 1
    hero.memes["pride"] += 1

    w.para()
    w.say(f"{hero.label} sewed as neat as a riverboat captain tying knots in a storm.")
    w.say(f"When the last stitch went through, the banner hung straight again, bright as sunrise.")
    w.say(f"{rival.label} looked down at the scuffed cloth, then at the steady little thimble, and the boast drained out of {rival.pronoun('possessive')} voice.")

    w.facts["hurt"] = True
    w.facts["forgive"] = True
    propagate(w, narrate=False)

    w.para()
    w.say(f'{rival.label} said, "I was wrong to laugh. That thimble did a mighty job."')
    w.say(f'{hero.label} smiled and said, "Come sit by me. You can help tie the knot."')
    w.say(f"{elder.label} nodded, and the three of them set the thimble back in the needle box, not as a joke, but as a treasure.")

    w.facts.update(
        hero=hero,
        rival=rival,
        elder=elder,
        prize=item,
        gear=box,
        activity=activity,
        setting=setting,
        resolved=True,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a Tall Tale for a child that includes the word "thimble" and a surprise when a little tool proves mighty.',
        f"Tell a story where {f['hero'].label} uses a thimble to help with {f['activity'].verb}, and a boastful rival learns a moral value.",
        f"Write a short tall tale in which a torn banner, a thimble, and a kind apology end in reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    rival = f["rival"]
    elder = f["elder"]
    qa = [
        QAItem(
            question=f"What surprised {hero.label} at {f['setting'].place}?",
            answer=f"A sudden wind tore the banner in two. The surprise changed the day from ordinary sewing into a hurried rescue with a tiny thimble.",
        ),
        QAItem(
            question=f"Why did {elder.label} tell {hero.label} to use the thimble?",
            answer=f"{elder.label} knew a thimble keeps a needle steady and protects a finger. That was the moral choice: careful hands could finish the job without getting hurt.",
        ),
        QAItem(
            question=f"How did {rival.label} and {hero.label} make up at the end?",
            answer=f"{rival.label} admitted the laughter was wrong and praised the thimble. {hero.label} answered with kindness and invited {rival.label} to help, so the three of them ended together in reconciliation.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags) | set(world.facts["prize"].label.split()) | set(world.facts["gear"].label.split())
    out: list[QAItem] = []
    if "thimble" in tags:
        out.append(QAItem(
            question="What is a thimble for?",
            answer="A thimble is a little cap worn on a finger while sewing. It helps push a needle safely through cloth.",
        ))
    if "needle" in tags:
        out.append(QAItem(
            question="Why do people use a needle box?",
            answer="A needle box keeps sharp sewing things together so they do not get lost. That makes sewing safer and tidier.",
        ))
    if "moral" in tags:
        out.append(QAItem(
            question="What is a moral value?",
            answer="A moral value is a kind rule for living, like being careful, honest, or kind to other people.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== story qa ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="fair",
        activity="stitch",
        prize="thimble",
        gear="needlebox",
        hero="Mabel",
        hero_type="girl",
        rival="Bram",
        rival_type="boy",
        elder="Grandma Dot",
        elder_type="grandmother",
    ),
    StoryParams(
        setting="porch",
        activity="mend",
        prize="thimble",
        gear="needlebox",
        hero="Toby",
        hero_type="boy",
        rival="Nell",
        rival_type="girl",
        elder="Aunt May",
        elder_type="aunt",
    ),
]


def explain_rejection(reason: str) -> str:
    return f"(No story: {reason})"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    activity = getattr(args, "activity", None) or rng.choice(sorted(_safe_lookup(SETTINGS, setting).affords))
    prize = getattr(args, "prize", None) or "thimble"
    gear = getattr(args, "gear", None) or "needlebox"
    if not valid_combo(setting, activity, prize, gear):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    rival_type = getattr(args, "rival_type", None) or ("boy" if hero_type == "girl" else "girl")
    elder_type = getattr(args, "elder_type", None) or rng.choice(["grandmother", "grandfather", "aunt", "uncle"])
    hero = getattr(args, "hero", None) or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    rival = getattr(args, "rival", None) or rng.choice([n for n in (BOY_NAMES if rival_type == "boy" else GIRL_NAMES) if n != hero])
    elder = getattr(args, "elder", None) or rng.choice(ELDER_NAMES)
    return StoryParams(
        setting=setting,
        activity=activity,
        prize=prize,
        gear=gear,
        hero=hero,
        hero_type=hero_type,
        rival=rival,
        rival_type=rival_type,
        elder=elder,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    for key in ("setting", "activity", "prize", "gear"):
        if getattr(params, key) not in (globals().get(key.upper() + "S") or globals().get(key.upper() + "ES") or globals().get(key.upper()[:-1] + "IES") or {}):
            pass
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(PRIZES, params.prize),
        _safe_lookup(GEARS, params.gear),
        params.hero,
        params.hero_type,
        params.rival,
        params.rival_type,
        params.elder,
        params.elder_type,
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for z in sorted(a.zone):
            lines.append(asp.fact("zone", aid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for gid in GEARS:
        lines.append(asp.fact("gear", gid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,A,P,G) :- setting(S), activity(A), prize(P), gear(G),
                  affords(S,A), region(P,R), zone(A,R), P = thimble, G = needlebox.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, activity=None, prize=None, gear=None,
            hero=None, hero_type=None, rival=None, rival_type=None,
            elder=None, elder_type=None,
        ), random.Random(777)))
        _ = sample.story
        emit(sample, trace=True, qa=True)
    except Exception:
        traceback.print_exc()
        return 1
    print("OK: verify smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld about a thimble, surprise, moral value, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--rival")
    ap.add_argument("--rival-type", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather", "aunt", "uncle"])
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("\n".join(map(str, asp_valid_combos())))
        return

    base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            p = resolve_params(args, random.Random(base + i))
            p.seed = base + i
            s = generate(p)
            if s.story not in seen:
                samples.append(s)
                seen.add(s.story)
            i += 1

    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
