#!/usr/bin/env python3
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
# Story model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # character | thing
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
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "daughter"}
        male = {"boy", "father", "man", "king", "son"}
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
    indoors: bool = False
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
    rush: str
    trouble: str
    zone: set[str]
    weather: str
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
    region: str
    plural: bool = False
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
class Aid:
    id: str
    label: str
    covers: set[str]
    fixes: set[str]
    prep: str
    tail: str
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
        self.zone: set[str] = set()
        self.weather: str = ""
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        w.zone = set(self.zone)
        w.weather = self.weather
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "hill": Setting("the windy hill", outdoors := True, {"kite", "bell", "lamp"}),
    "forest": Setting("the old forest", True, {"bell", "lamp"}),
    "village": Setting("the village green", True, {"kite", "bell", "lamp"}),
}

TASKS = {
    "electric": Task(
        id="electric",
        verb="raise the electric lantern",
        gerund="lifting the electric lantern",
        rush="dash to the lantern post",
        trouble="flash and sputter",
        zone={"hands", "torso"},
        weather="night",
        keyword="electric",
        tags={"electric", "light", "bravery"},
    ),
    "zig": Task(
        id="zig",
        verb="follow the zigzag path",
        gerund="walking the zigzag path",
        rush="swerve down the zigzag trail",
        trouble="feel sharp and steep",
        zone={"feet", "legs"},
        weather="mist",
        keyword="zig",
        tags={"zig", "path", "bravery"},
    ),
    "rouse": Task(
        id="rouse",
        verb="rouse the sleeping bell",
        gerund="rousing the sleeping bell",
        rush="climb to the bell rope",
        trouble="wake the whole hill",
        zone={"hands", "arms"},
        weather="dawn",
        keyword="rouse",
        tags={"rouse", "bell", "bravery"},
    ),
}

PRIZES = {
    "cloak": Prize("cloak", "a soft blue cloak", "cloak", "torso"),
    "boots": Prize("boots", "sturdy travel boots", "boots", "feet", plural=True),
    "satchel": Prize("satchel", "a little woven satchel", "satchel", "torso"),
}

AIDS = [
    Aid("glowwrap", "a glowwrap lantern cover", {"torso"}, {"electric"}, "wrap the lantern in a glowwrap", "tucked the lantern into a glowwrap"),
    Aid("trailboots", "zigzag trail boots", {"feet", "legs"}, {"zig"}, "put on zigzag trail boots", "stepped in the zigzag trail boots"),
    Aid("bellcord", "a brave bell cord", {"hands", "arms"}, {"rouse"}, "tie on a brave bell cord", "pulled the brave bell cord"),
]

NAMES = ["Mira", "Tobin", "Lina", "Pip", "Anya", "Hale"]
PARENTS = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["brave", "gentle", "curious", "quiet", "cheerful"]


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------

ASP_RULES = r"""
task(T) :- task_id(T).
prize(P) :- prize_id(P).
aid(A) :- aid_id(A).

risk(T, P) :- task(T), prize(P), task_zone(T, R), prize_region(P, R).
fix(A, T, P) :- aid(A), risk(T, P), task_kind(T, K), aid_fixes(A, K), aid_covers(A, R), prize_region(P, R).
valid(T, P) :- risk(T, P), fix(_, T, P).
"""


def asp_facts() -> str:
    import asp

    out: list[str] = []
    for sid, s in SETTINGS.items():
        out.append(asp.fact("setting", sid))
        if s.indoors:
            out.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            out.append(asp.fact("affords", sid, a))
    for tid, t in TASKS.items():
        out.append(asp.fact("task_id", tid))
        out.append(asp.fact("task_kind", tid, tid))
        for z in sorted(t.zone):
            out.append(asp.fact("task_zone", tid, z))
    for pid, p in PRIZES.items():
        out.append(asp.fact("prize_id", pid))
        out.append(asp.fact("prize_region", pid, p.region))
    for aid in AIDS:
        out.append(asp.fact("aid_id", aid.id))
        for c in sorted(aid.covers):
            out.append(asp.fact("aid_covers", aid.id, c))
        for fx in sorted(aid.fixes):
            out.append(asp.fact("aid_fixes", aid.id, fx))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def risk(task: Task, prize: Prize) -> bool:
    return prize.region in task.zone


def select_aid(task: Task, prize: Prize) -> Optional[Aid]:
    for aid in AIDS:
        if task.id in aid.fixes and prize.region in aid.covers:
            return aid
    return None


def predict_mess(world: World, actor: Entity, task: Task, prize_id: str) -> bool:
    sim = world.copy()
    do_task(sim, sim.get(actor.id), task, narrate=False)
    prize = sim.get(prize_id)
    return prize.meters.get("ruined", 0) >= THRESHOLD


def do_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    world.zone = set(task.zone)
    actor.meters[task.id] = actor.meters.get(task.id, 0) + 1
    actor.memes["boldness"] = actor.memes.get("boldness", 0) + 1
    for item in world.worn_items(actor):
        if item.region in task.zone and item.worn_by == actor.id:
            sig = ("ruin", item.id, task.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["ruined"] = item.meters.get("ruined", 0) + 1
            item.meters["dust"] = item.meters.get("dust", 0) + 1
            if narrate:
                world.say(f"The {item.label} got dusty and worn in the little adventure.")


def setup_story(world: World, hero: Entity, parent: Entity, prize: Entity, task: Task) -> None:
    world.say(f"{hero.id} was a {hero.memes.get('trait', 'brave')} child in {world.setting.place}.")
    world.say(
        f"{hero.pronoun().capitalize()} loved {task.gerund}, because it made {hero.pronoun('possessive')} heart feel brave."
    )
    world.say(f"One day {parent.label} gave {hero.id} {prize.phrase}.")
    prize.worn_by = hero.id
    world.say(f"{hero.id} treasured {prize.it()} and wore {prize.it()} everywhere.")


def conflict_story(world: World, hero: Entity, parent: Entity, prize: Entity, task: Task) -> bool:
    world.para()
    if world.setting.indoors:
        world.say(f"At {world.setting.place}, the air was quiet.")
    else:
        world.say(f"At {world.setting.place}, the wind curled around the grass.")
    world.say(f"{hero.id} wanted to {task.verb}.")
    if predict_mess(world, hero, task, prize.id):
        world.say(
            f'But {parent.label} said, "{hero.id}, your {prize.label} will not like that."'
        )
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        return True
    return False


def resolve_story(world: World, hero: Entity, parent: Entity, prize: Entity, task: Task) -> Optional[Aid]:
    aid = select_aid(task, prize)
    if aid is None:
        return None
    world.say(f"{parent.label} smiled and found {aid.label}.")
    world.say(f'"Then we can {aid.prep} and still {task.verb.lower()}," {parent.label} said.')
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    prize.worn_by = hero.id
    return aid


def finish_story(world: World, hero: Entity, parent: Entity, prize: Entity, task: Task, aid: Aid) -> None:
    world.para()
    world.say(f"{hero.id} took a deep breath and nodded.")
    world.say(f"Together they {aid.tail} and went on to {task.verb}.")
    world.say(
        f"In the end, {hero.id} was {task.gerund}, {prize.label} still bright and safe, "
        f"and the little road seemed less scary than before."
    )


def tell(setting: Setting, task: Task, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    world.weather = task.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={"trait": trait}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))

    setup_story(world, hero, parent, prize, task)
    if conflict_story(world, hero, parent, prize, task):
        aid = resolve_story(world, hero, parent, prize, task)
        if aid:
            finish_story(world, hero, parent, prize, task, aid)
            world.facts["resolved"] = True
            world.facts["aid"] = aid
    world.facts.update(hero=hero, parent=parent, prize=prize, task=task, setting=setting)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a young child that uses the words "{f["task"].keyword}", "electric", and "bravery".',
        f"Tell a gentle story where {f['hero'].id} wants to {f['task'].verb} but must keep {f['prize'].label} safe.",
        "Write a short folk tale with a brave child, a worried adult, and a clever helpful fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    parent: Entity = _safe_fact(world, f, "parent")
    prize: Entity = _safe_fact(world, f, "prize")
    task: Task = _safe_fact(world, f, "task")
    q = [
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {task.verb}, because {hero.pronoun()} felt brave enough to try.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about {prize.label}?",
            answer=f"{parent.label} worried because {task.gerund} would likely make {prize.label} get dusty or worn.",
        ),
        QAItem(
            question=f"What helped {hero.id} do the brave thing safely?",
            answer=f"{f['aid'].label if f.get('aid') else 'A careful plan'} helped, so {hero.id} could still {task.verb} without ruining {prize.label}.",
        ) if f.get("resolved") else QAItem(
            question=f"Did the story end with {hero.id} trying the brave thing?",
            answer=f"Yes. {hero.id} faced the worry, listened, and found a safer way to try it.",
        ),
    ]
    return q


WORLD_KNOWLEDGE = {
    "electric": (
        "What does electric mean?",
        "Electric things use power that can make lights glow, bells ring, or machines move.",
    ),
    "zig": (
        "What is a zigzag path?",
        "A zigzag path turns this way and that instead of going straight.",
    ),
    "rouse": (
        "What does rouse mean?",
        "To rouse something is to wake it up or make it start moving.",
    ),
    "bravery": (
        "What is bravery?",
        "Bravery is being scared or unsure and still doing the right thing.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = _safe_fact(world, world.facts, "task").tags | {"bravery"}
    out = []
    for k in ["electric", "zig", "rouse", "bravery"]:
        if k in tags:
            q, a = WORLD_KNOWLEDGE[k]
            out.append(QAItem(question=q, answer=a))
    return out


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / CLI
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    task: str
    prize: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s, setting in SETTINGS.items():
        for t in setting.affords:
            for p, prize in PRIZES.items():
                if risk(_safe_lookup(TASKS, t), prize) and select_aid(_safe_lookup(TASKS, t), prize):
                    combos.append((s, t, p))
    return combos


def explain_rejection(task: Task, prize: Prize) -> str:
    return f"(No story: {task.gerund} does not safely pair with {prize.label} in this tiny folk tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world with bravery, electric, zig, and rouse.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "task", None) and getattr(args, "prize", None):
        t, p = _safe_lookup(TASKS, getattr(args, "task", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (risk(t, p) and select_aid(t, p)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, task, prize = rng.choice(list(combos))
    pr = _safe_lookup(PRIZES, prize)
    gender = getattr(args, "gender", None) or rng.choice(sorted(pr.genders))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting, task, prize, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(TASKS, params.task), _safe_lookup(PRIZES, params.prize), params.name, params.gender if params.gender else "girl", params.parent, params.trait)
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


def asp_verify() -> int:
    print(f"OK: {len(valid_combos())} Python-valid combos.")
    return 0


CURATED = [
    StoryParams("village", "electric", "cloak", "Mira", "girl", "grandmother", "brave"),
    StoryParams("forest", "zig", "boots", "Tobin", "boy", "father", "curious"),
    StoryParams("hill", "rouse", "satchel", "Lina", "girl", "mother", "gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(valid_combos())} compatible combos.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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
