#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/endow_straw_rhyme_problem_solving_quest_bedtime.py
==============================================================================================================

A tiny bedtime storyworld about a moonlit quest, a straw problem, and a gentle
solution told with a little rhyme.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


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

    region: object | None = None
    aid: object | None = None
    child: object | None = None
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
    indoor: bool = False
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
    seek: str
    gerund: str
    trouble: str
    mess: str
    zone: set[str]
    keyword: str
    rhyme: tuple[str, str]
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
class Aid:
    id: str
    label: str
    covers: set[str]
    solves: set[str]
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        return c

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    aid: str
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


SETTINGS = {
    "nursery": Setting(place="the nursery", indoor=True, affords={"straw"}),
    "moon_garden": Setting(place="the moon garden", indoor=False, affords={"straw"}),
    "hay_room": Setting(place="the hay room", indoor=True, affords={"straw"}),
}

TASKS = {
    "straw": Task(
        id="straw",
        seek="gather the loose straw",
        gerund="gathering straw",
        trouble="blowing apart",
        mess="scratchy",
        zone={"hands", "arms"},
        keyword="straw",
        rhyme=("straw", "glow"),
        tags={"straw", "bedtime"},
    ),
}

PRIZES = {
    "bunny": Prize(id="bunny", label="bunny blanket", phrase="a soft bunny blanket", region="torso"),
    "pillow": Prize(id="pillow", label="pillow", phrase="a cloud-soft pillow", region="head"),
    "pajamas": Prize(id="pajamas", label="pajamas", phrase="striped pajamas", region="torso", plural=True),
}

AIDS = {
    "basket": Aid(
        id="basket",
        label="a little basket",
        covers={"hands"},
        solves={"scratchy"},
        prep="place the straw in a little basket first",
        tail="tucked the straw into the basket",
    ),
    "blanket": Aid(
        id="blanket",
        label="a blanket wrap",
        covers={"arms", "hands"},
        solves={"scratchy"},
        prep="wrap the straw bundle in a blanket first",
        tail="wrapped the straw bundle in the blanket",
    ),
    "ribbon": Aid(
        id="ribbon",
        label="a ribbon tie",
        covers={"hands"},
        solves={"scratchy"},
        prep="tie the straw with a soft ribbon first",
        tail="tied the straw with the ribbon",
    ),
}

NAMES_GIRL = ["Mina", "Lena", "Tia", "Nora", "Mila"]
NAMES_BOY = ["Owen", "Theo", "Eli", "Finn", "Jonah"]
TRAITS = ["gentle", "curious", "sleepy", "careful", "brave"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task in setting.affords:
            for prize in PRIZES:
                for aid in AIDS:
                    combos.append((place, task, prize, aid))
    return combos


def prize_at_risk(task: Task, prize: Prize) -> bool:
    return prize.region in task.zone


def select_aid(task: Task, prize: Prize) -> Optional[Aid]:
    for aid in AIDS.values():
        if task.mess in aid.solves and prize.region in aid.covers:
            return aid
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime storyworld about a moonlit quest and a straw problem.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--aid", choices=AIDS)
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


def explain_rejection(task: Task, prize: Prize) -> str:
    return f"(No story: {task.seek} would not endanger the {prize.label} in a way this storyworld can honestly solve.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "task", None) and getattr(args, "prize", None):
        t, p = _safe_lookup(TASKS, getattr(args, "task", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not prize_at_risk(t, p):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
              and (getattr(args, "aid", None) is None or c[3] == getattr(args, "aid", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, prize, aid = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, task=task, prize=prize, aid=aid, name=name, gender=gender, parent=parent)


def _do_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    world.zone = set(task.zone)
    actor.meters[task.mess] = actor.meters.get(task.mess, 0) + 1
    if narrate:
        world.say(f"{actor.id} worked carefully, and the straw began to feel lively in {actor.pronoun('possessive')} hands.")


def _soak_or_scrape(world: World) -> list[str]:
    out: list[str] = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters.get("scratchy", 0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.region not in world.zone:
                continue
            if item.meters.get("protected", 0) >= THRESHOLD:
                continue
            sig = ("scratch", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["scratched"] = item.meters.get("scratched", 0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got a little scratchy.")
    return out


def predict(world: World, actor: Entity, task: Task, prize_id: str) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get(actor.id), task, narrate=False)
    prize = sim.entities[prize_id]
    return {"scratched": prize.meters.get("scratched", 0) > 0}


def setting_detail(setting: Setting) -> str:
    if setting.indoor:
        return f"{setting.place.capitalize()} was hushed and cozy, with one lamp making a little puddle of gold."
    return f"{setting.place.capitalize()} lay under a silver sky, quiet as a lullaby."


def tell(setting: Setting, task: Task, prize_cfg: Prize, aid_def: Aid,
         hero_name: str, hero_gender: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=child.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))
    aid = world.add(Entity(id=aid_def.id, type="aid", label=aid_def.label, owner=child.id))
    aid.worn_by = child.id

    child.memes["wonder"] = 1
    world.say(f"At bedtime, {child.id} was a {random.choice(TRAITS)} little {child.type} who loved quiet quests.")
    world.say(f"{child.id} had one small task: to {task.seek}, because the moon seemed to endow the straw with a soft shine.")
    world.say(f"{setting_detail(setting)}")

    world.para()
    world.say(f"{child.id} and {child.pronoun('possessive')} {parent.label} tiptoed to the straw corner.")
    world.say(f"{child.id} wanted to keep {prize.label} safe, but the loose straw kept {task.trouble}.")
    if predict(world, child, task, prize.id)["scratched"]:
        world.say(f'"Be careful," {child.pronoun("possessive")} {parent.label} whispered, "or your {prize.label} may get scratchy."')
    world.say(f"{child.id} took a breath and began to think. The rhyme helped: “Straw can glow, but it should not go.”")

    world.para()
    world.say(f"{child.id} found a simple answer: {aid_def.prep}.")
    world.say(f"That way, the straw could travel safely, and {child.id} could finish the little quest without any fuss.")
    world.say(f"Together they {aid_def.tail}, and the room grew tidy and calm.")
    world.say(f"At last, {child.id} tucked {prize.label} close and smiled sleepily, because the problem was solved.")

    world.facts.update(child=child, parent=parent, prize=prize, aid=aid, task=task, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    task = _safe_fact(world, f, "task")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a bedtime story about {child.id} and a {task.keyword} quest that includes the word "straw".',
        f"Tell a gentle rhyme-filled story where {child.id} must solve a small problem before sleep and keep the {prize.label} safe.",
        f"Write a cozy story about a moonlit quest, a little bit of straw, and a kind solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, prize, task = f["child"], f["parent"], f["prize"], f["task"]
    return [
        QAItem(
            question=f"What did {child.id} try to do at bedtime?",
            answer=f"{child.id} tried to {task.seek}. It was a quiet quest in the {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the {prize.label}?",
            answer=f"{parent.label} worried because the loose straw could make the {prize.label} scratchy if {child.id} handled it the wrong way.",
        ),
        QAItem(
            question=f"What was the simple problem-solving idea?",
            answer=f"{child.id} and {parent.label} used {f['aid'].label} so the straw could be gathered safely and the {prize.label} could stay snug.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the straw put away, the {prize.label} kept safe, and {child.id} ready for sleep.",
        ),
    ]


KNOWLEDGE = {
    "straw": [
        ("What is straw?", "Straw is the dry, hollow stems of grain plants, and it can be light and scratchy."),
    ],
    "bedtime": [
        ("Why do children get sleepy at bedtime?", "Children get sleepy at bedtime because their bodies and minds need rest after a busy day."),
    ],
    "rhyme": [
        ("What is a rhyme?", "A rhyme is when two words sound alike at the end, like glow and snow."),
    ],
    "quest": [
        ("What is a quest?", "A quest is a little journey to find something or solve a problem."),
    ],
    "problem": [
        ("What is problem solving?", "Problem solving is when you think carefully and pick a good way to fix something."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags) | {"bedtime", "rhyme", "quest", "problem", "straw"}
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


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
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.region:
            parts.append(f"region={e.region}")
        if e.worn_by:
            parts.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(T,P) :- zone(T,R), worn_on(P,R).
fix(T,P) :- prize_at_risk(T,P), aid(A), solves(A,M), mess_of(T,M), covers(A,R), worn_on(P,R).
valid_story(Place,T,P,A) :- affords(Place,T), prize_at_risk(T,P), fix(T,P), aid(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("mess_of", tid, t.mess))
        for r in sorted(t.zone):
            lines.append(asp.fact("zone", tid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for aid in AIDS.values():
        lines.append(asp.fact("aid", aid.id))
        for c in sorted(aid.covers):
            lines.append(asp.fact("covers", aid.id, c))
        for s in sorted(aid.solves):
            lines.append(asp.fact("solves", aid.id, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="nursery", task="straw", prize="bunny", aid="basket", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="moon_garden", task="straw", prize="pillow", aid="ribbon", name="Theo", gender="boy", parent="father"),
    StoryParams(place="hay_room", task="straw", prize="pajamas", aid="blanket", name="Lena", gender="girl", parent="mother"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(PRIZES, params.prize), _safe_lookup(AIDS, params.aid), params.name, params.gender, params.parent)
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
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/4."))
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.task} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
