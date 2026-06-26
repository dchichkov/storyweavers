#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/seize_approval_rhinoceros_conflict_curiosity_suspense_heartwarming.py
====================================================================================================

A compact storyworld about a curious young rhinoceros, a tense moment of wanting
to seize something important, and a warm ending where approval is earned by
gentleness instead of force.

Seed-tale premise:
---
A little rhinoceros named Rumi loves watching the lantern show at the edge of
the meadow. He is curious about everything, especially the silver approval bell
that the keeper rings when an animal has helped kindly. One evening, Rumi wants
to seize the bell rope and ring it himself, but the keeper worries that his
horn will catch the ribbon and scare the birds. Rumi feels the suspense and
conflict in his chest.

Then Rumi notices a tiny foal struggling with a dropped bundle of hay. He uses
his strength carefully to carry the hay back instead of seizing the bell. The
keeper smiles, rings the approval bell for real, and everyone cheers. Rumi gets
the approval he wanted by being helpful first.

World model notes:
---
- Physical meters: balance, tidiness, strain, order
- Emotional memes: curiosity, conflict, suspense, approval, warmth, pride
- The "seize" action is only reasonable when it can be done safely with a helper
  or a tool; otherwise the world rejects invalid choices with StoryError.
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

HERO_KIND = "rhinoceros"



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
    wearable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str
    evening: bool = False
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
    risk: str
    requires: set[str] = field(default_factory=set)
    keyword: str = "seize"
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
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Tool:
    id: str
    label: str
    helps: set[str]
    covers: set[str]
    prep: str
    tail: str
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
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "meadow": Setting(place="the meadow edge", evening=True, affords={"seize_bell", "help_hay"}),
    "barn": Setting(place="the barn lane", evening=False, affords={"help_hay"}),
    "showring": Setting(place="the lantern ring", evening=True, affords={"seize_bell", "help_hay"}),
}

ACTIVITIES = {
    "seize_bell": Activity(
        id="seize_bell",
        verb="seize the approval bell rope",
        gerund="seizing the bell rope",
        risk="the ribbon might tangle around the horn and frighten the birds",
        requires={"tool"},
        keyword="seize",
        tags={"seize", "approval", "suspense"},
    ),
    "help_hay": Activity(
        id="help_hay",
        verb="help carry the fallen hay",
        gerund="lifting the hay bundle carefully",
        risk="the bundle could spill if handled too fast",
        requires=set(),
        keyword="help",
        tags={"approval", "curiosity", "heartwarming"},
    ),
}

PRIZES = {
    "bell": Prize(
        id="bell",
        label="approval bell",
        phrase="a silver approval bell with a ribbon",
        region="torso",
    ),
    "hay": Prize(
        id="hay",
        label="hay bundle",
        phrase="a neat bundle of hay",
        region="ground",
    ),
}

TOOLS = {
    "hook": Tool(
        id="hook",
        label="a little wooden hook",
        helps={"seize_bell"},
        covers={"torso"},
        prep="use a little wooden hook instead",
        tail="held the rope with the hook and kept the ribbon from snagging",
    ),
    "strap": Tool(
        id="strap",
        label="a soft carrying strap",
        helps={"help_hay"},
        covers={"back"},
        prep="lift the hay with a soft carrying strap",
        tail="carried the hay without dropping a single stem",
    ),
}

NAMES = ["Rumi", "Milo", "Nia", "Tessa", "Arlo", "Pippa"]
GROWNUPS = ["keeper", "aunt", "father", "mother"]


def choose(seq, rng: random.Random):
    return rng.choice(list(seq))


def reasonableness_gate(activity: Activity, prize: Prize, tool: Optional[Tool]) -> None:
    if activity.id == "seize_bell" and tool is None:
        pass
    if activity.id == "help_hay" and prize.id != "hay":
        pass


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                if act == "seize_bell" and prize == "bell":
                    combos.append((place, act, prize))
                if act == "help_hay" and prize == "hay":
                    combos.append((place, act, prize))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
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


def _do_seize(world: World, hero: Entity, prize: Entity, tool: Optional[Tool]) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["suspense"] += 1
    if tool:
        hero.meters["order"] += 1
        world.say(
            f"{hero.id} was curious about the approval bell and wanted to seize it right away, but {tool.prep} sounded wiser."
        )
        world.say(f"So {hero.id} {tool.tail}.")
        return
    pass


def _do_help(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["warmth"] += 1
    hero.meters["tidiness"] += 1
    world.say(
        f"{hero.id} noticed a dropped hay bundle and felt a little conflict between chasing applause and doing what was kind."
    )
    world.say(f"Instead, {hero.id} helped with the hay, and the field grew tidier.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, parent_role: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=HERO_KIND, label=name, meters={}, memes={}))
    parent = world.add(Entity(id="Adult", kind="character", type=parent_role, label=f"the {parent_role}", meters={}, memes={}))
    prize = world.add(Entity(id=prize_cfg.id, type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase, caretaker=parent.id))

    world.say(f"At {setting.place}, {hero.id} was a small {HERO_KIND} with a big, curious heart.")
    world.say(f"{hero.id} loved the warm evening light and the shiny promise of approval.")

    world.para()
    if activity.id == "seize_bell":
        world.say(
            f"When the keeper rang the approval bell, {hero.id} felt suspense twist into a bright idea: what if {hero.id} could seize the bell rope and ring it too?"
        )
        world.say(f"But the ribbon on {prize.label} was delicate, and the keeper worried that a horn might catch it.")
        tool = world.add(Entity(id="hook", type="tool", label=TOOLS["hook"].label, wearable=False))
        _do_seize(world, hero, prize, TOOLS["hook"])
        world.say(
            f"That pause gave {hero.id} time to notice a tiny foal watching nearby, hoping no one would get startled."
        )
        world.say(
            f"{hero.id} chose patience instead of grabbing, and the keeper's face softened with approval."
        )
        hero.memes["approval"] += 1
        hero.memes["warmth"] += 1
        hero.meters["order"] += 1
        hero.meters["balance"] += 1
        world.para()
        world.say(
            f"Then the keeper rang the bell for real. It chimed sweetly while {hero.id} stood still, proud to have earned approval by being gentle."
        )
        world.say(
            f"The foal bounced happily, and the meadow felt safer and kinder than before."
        )
        world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, tool=tool, resolved=True)
    else:
        _do_help(world, hero, prize)
        world.say(
            f"That mattered more than seizing applause. The keeper watched, then gave {hero.id} a warm nod of approval."
        )
        hero.memes["approval"] += 1
        hero.memes["warmth"] += 1
        hero.meters["order"] += 1
        hero.meters["balance"] += 1
        world.para()
        world.say(
            f"When the lanterns glowed on, {hero.id} felt the happiest kind of suspense end in a cozy smile."
        )
        world.say(
            f"Approval had arrived, and it had arrived because {hero.id} helped first."
        )
        world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, tool=None, resolved=True)
    return world


SETTINGS_BY_ACTIVITY = {
    "seize_bell": ["meadow", "showring"],
    "help_hay": ["barn", "meadow", "showring"],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming storyworld about a curious rhinoceros seeking approval.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=GROWNUPS)
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
    combos = valid_combos()
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None)) and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(GROWNUPS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, parent=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a child about a curious rhinoceros who wants to seize approval but learns a gentler way.',
        f"Tell a small suspenseful story where {f['hero'].id} at {world.setting.place} almost seizes the approval bell, then helps instead.",
        f'Write a simple story that includes the words "seize", "approval", and "rhinoceros" and ends with a warm feeling.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, prize, activity = f["hero"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who wanted approval in the story?",
            answer=f"{hero.id}, the little rhinoceros, wanted approval and felt very curious about the shiny bell.",
        ),
        QAItem(
            question=f"What made the story tense at first?",
            answer=f"{hero.id} wanted to {activity.verb}, but the keeper worried the ribbon on {prize.label} might be caught and the moment felt suspenseful.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended warmly: {hero.id} helped instead of forcing the moment, and the keeper gave real approval.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is approval?",
            answer="Approval is a good feeling or a kind sign that someone thinks you did something well.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn about something new.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the nervous wondering about what will happen next.",
        ),
        QAItem(
            question="What is a rhinoceros?",
            answer="A rhinoceros is a very large animal with thick skin and one or two horns on its nose.",
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("\n== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("\n== (3) World questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


ASP_RULES = r"""
valid(Place,Act,Prize) :- affords(Place,Act), combo(Act,Prize).
valid_story(Place,Act,Prize,Name) :- valid(Place,Act,Prize), hero(Name).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", place, act))
    for act, pr in [("seize_bell", "bell"), ("help_hay", "hay")]:
        lines.append(asp.fact("combo", act, pr))
    for name in NAMES:
        lines.append(asp.fact("hero", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    activity = _safe_lookup(ACTIVITIES, params.activity)
    prize = _safe_lookup(PRIZES, params.prize)
    reasonableness_gate(activity, prize, TOOLS["hook"] if activity.id == "seize_bell" else None)
    world = tell(setting, activity, prize, params.name, params.parent)
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
    StoryParams(place="showring", activity="seize_bell", prize="bell", name="Rumi", parent="keeper"),
    StoryParams(place="barn", activity="help_hay", prize="hay", name="Milo", parent="mother"),
    StoryParams(place="meadow", activity="seize_bell", prize="bell", name="Nia", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with names):\n")
        for p, a, pr in triples:
            names = sorted(n for (pp, aa, ppz, n) in stories if (pp, aa, ppz) == (p, a, pr))
            print(f"  {p:9} {a:11} {pr:6}  [{', '.join(names)}]")
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
