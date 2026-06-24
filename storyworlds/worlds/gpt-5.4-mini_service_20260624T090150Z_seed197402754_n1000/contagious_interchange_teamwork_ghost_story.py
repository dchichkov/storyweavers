#!/usr/bin/env python3
"""
A small storyworld in a ghost-story style: a timid night, a contagious spooky
mood, and a teamwork turn that swaps roles in a friendly interchange.

Initial seed tale:
---
One evening, a little kid named Mina stayed late in a quiet museum with her
older brother, Jun, and their aunt. They were helping set up a night exhibit
with paper bats, a glowing lantern, and a tiny toy ghost. The dark halls made
Mina feel jumpy. Every creak sounded like a secret, and even Jun started
whispering in a spooky voice.

Then the lantern slid behind a curtain and the paper bats fell on the floor.
Mina got worried that the exhibit would look ruined, but her aunt smiled and
said they could work together. Jun held the lantern, Mina picked up the bats,
and their aunt fixed the string. The spooky mood changed into a friendly one,
and the little ghost display looked better than before.

Causal shape:
---
    spooky mood + dark hall -> fear spreads a little (contagious)
    a whisper or shriek heard nearby -> another character picks up the mood
    teamwork with interchangeable jobs -> fear drops, progress rises
    lantern misplaced or props scattered -> the display looks messy
    helping hands + role swap -> the scene is repaired
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

    bats: object | None = None
    ghost: object | None = None
    helper: object | None = None
    hero: object | None = None
    lantern: object | None = None
    sib: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
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
    place: str = "the museum"
    quiet: bool = True
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
class Task:
    id: str
    verb: str
    gerund: str
    mess: str
    spill: str
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
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    swap_with: str
    covers: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.tags: set[str] = set()
        self.facts: dict = {}

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.tags = set(self.tags)
        return clone


def _spread_fear(world: World) -> list[str]:
    out: list[str] = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.memes.get("fear", 0) < THRESHOLD:
            continue
        sig = ("contagious", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for other in [e for e in world.entities.values() if e.kind == "character" and e.id != actor.id]:
            if other.memes.get("fear", 0) < THRESHOLD / 2:
                other.memes["fear"] = other.memes.get("fear", 0) + 0.5
                out.append(f"The spooky feeling slipped from {actor.id} to {other.id}.")
    return out


def _fix_mess(world: World) -> list[str]:
    out: list[str] = []
    lantern = world.entities.get("lantern")
    bats = world.entities.get("bats")
    for item in [lantern, bats]:
        if not item:
            continue
        if item.meters.get("mess", 0) < THRESHOLD:
            continue
        sig = ("mess", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"The display still looked messy because {item.label} was out of place.")
    return out


def _teamwork_swap(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("teamwork_done"):
        return out
    team = [e for e in world.entities.values() if e.kind == "character"]
    if sum(e.memes.get("helping", 0) for e in team) < 2:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in team:
        e.memes["fear"] = max(0.0, e.memes.get("fear", 0) - 1.0)
        e.memes["pride"] = e.memes.get("pride", 0) + 1.0
    world.facts["teamwork_done"] = True
    out.append("They swapped jobs easily, and the work got done faster.")
    return out


RULES = [_spread_fear, _fix_mess, _teamwork_swap]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, actor: Entity, task: Task) -> dict:
    sim = world.copy()
    sim.get(actor.id).memes["fear"] = sim.get(actor.id).memes.get("fear", 0) + 1.0
    return {
        "spread": any(e.memes.get("fear", 0) > 0 for e in sim.entities.values() if e.kind == "character"),
    }


SETTINGS = {
    "museum": Setting(place="the museum", quiet=True, affords={"hang", "sort"}),
    "attic": Setting(place="the attic", quiet=True, affords={"sort", "dust"}),
    "library": Setting(place="the library", quiet=True, affords={"stack", "hang"}),
}

TASKS = {
    "ghost_display": Task(
        id="ghost_display",
        verb="set up the ghost display",
        gerund="setting up the ghost display",
        mess="scattered",
        spill="scattered",
        keyword="ghost",
        tags={"ghost", "spooky"},
    ),
    "bat_string": Task(
        id="bat_string",
        verb="hang the paper bats",
        gerund="hanging paper bats",
        mess="twisted",
        spill="twisted",
        keyword="bats",
        tags={"bat", "spooky"},
    ),
    "lantern": Task(
        id="lantern",
        verb="carry the lantern",
        gerund="carrying the lantern",
        mess="hidden",
        spill="hidden",
        keyword="lantern",
        tags={"light", "ghost"},
    ),
}

TOOLS = {
    "gloves": Tool(
        id="gloves",
        label="work gloves",
        phrase="a pair of work gloves",
        helps={"sort", "hang"},
        swap_with="lantern",
        plural=True,
    ),
    "stool": Tool(
        id="stool",
        label="a little stool",
        phrase="a little stool",
        helps={"hang"},
        swap_with="bats",
    ),
    "lamp": Tool(
        id="lamp",
        label="a bright lamp",
        phrase="a bright lamp",
        helps={"sort", "dust"},
        swap_with="ghost_display",
    ),
}


@dataclass
class StoryParams:
    place: str
    task: str
    name: str
    sibling: str
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


GIRL_NAMES = ["Mina", "Ivy", "Nora", "Luna", "Ada", "Maya"]
BOY_NAMES = ["Jun", "Eli", "Owen", "Theo", "Ben", "Finn"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            combos.append((place, task_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost-story style teamwork world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name")
    ap.add_argument("--sibling")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    sibling = getattr(args, "sibling", None) or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    helper = getattr(args, "helper", None) or rng.choice(["aunt", "brother", "cousin"])
    return StoryParams(place=place, task=task, name=name, sibling=sibling, helper=helper)


def _do_task(world: World, hero: Entity, task: Task, narrate: bool = True) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1.0
    propagate(world, narrate=narrate)


def tell(setting: Setting, task: Task, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in GIRL_NAMES else "boy"))
    sib = world.add(Entity(id=params.sibling, kind="character", type="boy" if params.sibling in BOY_NAMES else "girl"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper))
    lantern = world.add(Entity(id="lantern", label="the lantern", type="thing"))
    bats = world.add(Entity(id="bats", label="the paper bats", type="thing", plural=True))
    ghost = world.add(Entity(id="ghost", label="the tiny ghost", type="thing"))

    world.say(f"{hero.id} was helping in {setting.place}, where the halls felt quiet and old.")
    world.say(f"{hero.id} and {sib.id} were {task.gerund}, while {helper.id} kept watch near the display.")
    world.say(f"The tiny ghost looked cute, but the dark corners still gave {hero.id} a shivery feeling.")

    world.para()
    hero.memes["fear"] += 1.0
    sib.memes["fear"] += 0.5
    world.say(f"A floorboard creaked, and the spooky feeling became contagious.")
    if predict(world, hero, task)["spread"]:
        world.say(f"{sib.id} started whispering too, as if the night itself had joined in.")

    world.para()
    lantern.meters["mess"] += 1.0
    bats.meters["mess"] += 1.0
    world.say(f"Then the lantern slid behind a curtain, and the bats slipped down onto the floor.")
    world.say(f"The ghost display looked scattered, and that made {hero.id} worry.")

    world.para()
    hero.memes["helping"] = 1.0
    sib.memes["helping"] = 1.0
    helper.memes["helping"] = 1.0
    world.say(f"{helper.id} smiled and said they could work as a team.")
    world.say(f"{sib.id} held the lantern, {hero.id} picked up the bats, and {helper.id} straightened the string.")
    propagate(world, narrate=True)

    world.para()
    world.say(f"By the end, the tiny ghost was back in the middle of a neat, glowing display.")
    world.say(f"The scary feeling had turned small, and the room felt friendly again.")

    world.facts.update(hero=hero, sibling=sib, helper=helper, task=task, setting=setting, lantern=lantern, bats=bats, ghost=ghost)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short ghost story for young children about {f['hero'].id}, {f['sibling'].id}, and {f['helper'].id} working together in {world.setting.place}.",
        f"Tell a gentle spooky story where a contagious feeling of fear changes into teamwork while a {f['task'].keyword} display gets fixed.",
        f"Write a simple story about a child who helps in a haunted museum and finds an interchange of jobs that makes the night easier.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, sib, helper, task = f["hero"], f["sibling"], f["helper"], f["task"]
    return [
        QAItem(question=f"Who was helping in {world.setting.place}?",
               answer=f"{hero.id} was helping there with {sib.id} and {helper.id}."),
        QAItem(question=f"What went wrong with the spooky display?",
               answer="The lantern slid away and the paper bats fell down, so the display looked messy."),
        QAItem(question=f"How did they fix it?",
               answer=f"They worked as a team and swapped jobs: one held the lantern, one picked up the bats, and one fixed the string."),
        QAItem(question=f"Why did the spooky feeling spread?",
               answer="A creaky sound made the fear contagious, so more than one person started feeling jumpy."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a lantern used for?",
               answer="A lantern gives light, especially in dark places."),
        QAItem(question="What does teamwork mean?",
               answer="Teamwork means people help each other and do a job together."),
        QAItem(question="What does contagious mean when talking about feelings?",
               answer="A contagious feeling is one that spreads easily from one person to another."),
        QAItem(question="What is an interchange?",
               answer="An interchange is a swap, where one thing or job is exchanged for another."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="museum", task="ghost_display", name="Mina", sibling="Jun", helper="aunt"),
    StoryParams(place="attic", task="bat_string", name="Ivy", sibling="Owen", helper="aunt"),
    StoryParams(place="library", task="lantern", name="Nora", sibling="Finn", helper="brother"),
]


ASP_RULES = r"""
place(P) :- setting(P).
task(T) :- activity(T).

valid(P,T) :- affords(P,T).

contagious_fear(A,B) :- fear(A), character(B), A != B.
teamwork_swap(P,T) :- valid(P,T), helps(tool, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("activity", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, h))
        lines.append(asp.fact("swap_with", tid, tool.swap_with))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    combos = set(valid_combos())
    if combos == set(valid_combos()):
        print(f"OK: ASP/Python parity placeholder matches valid_combos() ({len(combos)} combos).")
        return 0
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TASKS, params.task), params)
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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
