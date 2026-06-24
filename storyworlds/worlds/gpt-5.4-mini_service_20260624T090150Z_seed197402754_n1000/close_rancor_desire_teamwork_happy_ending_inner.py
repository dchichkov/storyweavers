#!/usr/bin/env python3
"""
A tiny comedy storyworld about close feelings, a little rancor, a strong desire,
and a teamwork ending that turns into a happy ending.

Seed premise:
- Two close friends want the same prize.
- A small squabble grows into rancor.
- Their inner monologues reveal what they really want.
- They solve the problem by teaming up, and the ending is happy.
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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    a: object | None = None
    b: object | None = None
    prize: object | None = None
    prop: object | None = None
    prop2: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type
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
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str]
    covers: set[str]
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
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "kitchen": Setting("the kitchen", {"baking", "snack"}),
    "playroom": Setting("the playroom", {"building", "baking", "snack"}),
}

TASKS = {
    "cookies": Task(
        id="cookies",
        verb="bake cookies",
        gerund="baking cookies",
        mess="flour",
        soil="covered in flour",
        keyword="cookie",
        tags={"baking", "sweet"},
    ),
    "fort": Task(
        id="fort",
        verb="build a pillow fort",
        gerund="building a pillow fort",
        mess="pillows",
        soil="all tumbled and messy",
        keyword="fort",
        tags={"building", "silly"},
    ),
}

PRIZES = {
    "sprinkles": Prize("sprinkles", "a small cup of rainbow sprinkles", "counter"),
    "blanket": Prize("blanket", "a soft blue blanket", "couch"),
}

FIXES = [
    Fix(
        id="share",
        label="share the job",
        prep="divide the job in half and work together",
        tail="worked side by side",
        helps={"flour", "pillows"},
        covers={"counter", "couch"},
    ),
    Fix(
        id="timer",
        label="use a timer",
        prep="set a timer and take turns",
        tail="took turns without bickering",
        helps={"flour"},
        covers={"counter"},
    ),
]

NAMES = ["Mina", "Leo", "June", "Nico", "Pia", "Owen"]
TRAITS = ["silly", "busy", "brave", "clever", "chatty"]


def reasonableness(task: Task, prize: Prize) -> bool:
    if task.id == "cookies" and prize.region == "counter":
        return True
    if task.id == "fort" and prize.region == "couch":
        return True
    return False


def select_fix(task: Task, prize: Prize) -> Optional[Fix]:
    for fix in FIXES:
        if task.mess in fix.helps and prize.region in fix.covers:
            return fix
    return None


def predict_soil(world: World, actor: Entity, task: Task, prize_id: str) -> bool:
    sim = world.copy()
    _do_task(sim, sim.get(actor.id), task, narrate=False)
    prize = sim.entities.get(prize_id)
    return bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD)


def _do_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    actor.meters[task.mess] = actor.meters.get(task.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    for e in list(world.entities.values()):
        if e.kind == "thing" and e.owner == actor.id and e.label == task.keyword:
            e.meters["dirty"] = e.meters.get("dirty", 0.0) + 1
    if narrate:
        world.say(f"They started {task.gerund}, and the room got a little louder.")


def run_propagation(world: World) -> None:
    for e in list(world.entities.values()):
        if e.kind == "thing" and e.meters.get("dirty", 0.0) >= THRESHOLD and e.caretaker:
            sig = ("cleanup", e.id)
            if sig not in world.fired:
                world.fired.add(sig)
                care = world.get(e.caretaker)
                care.meters["workload"] = care.meters.get("workload", 0.0) + 1


def tell_inner_monologue(person: Entity, desire_text: str, rancor_text: str) -> str:
    return f"Inside, {person.id} thought, \"{desire_text}\" Then another thought popped up: \"{rancor_text}\""


def tell_story(world: World, a: Entity, b: Entity, task: Task, prize: Entity, fix: Optional[Fix]) -> None:
    world.say(
        f"On a bright afternoon in {world.setting.place}, {a.id} and {b.id} were very close friends."
    )
    world.say(
        f"They both wanted to {task.verb}, and they both wanted {prize.phrase} for the finish."
    )
    world.say(
        f"{a.id} whispered, \"I had the idea first!\" and {b.id} snapped, \"No, I did!\""
    )
    a.memes["rancor"] = a.memes.get("rancor", 0.0) + 1
    b.memes["rancor"] = b.memes.get("rancor", 0.0) + 1
    world.say(
        tell_inner_monologue(a, f"I really want to win {prize.label}.", "Oh no, now I sound like a grumpy spoon.")
    )
    world.say(
        tell_inner_monologue(b, f"I want that prize too.", "This is getting as silly as a sock in a soup bowl.")
    )

    world.para()
    world.say(
        f"They tried to begin the job alone, but that only made more mess and more rancor."
    )
    _do_task(world, a, task)
    _do_task(world, b, task)
    run_propagation(world)

    if reasonableness(task, prize):
        if fix is None:
            pass
        world.say(
            f"Then {a.id} stopped and looked at {b.id}. {a.id} said, \"We can be silly and still team up.\""
        )
        world.say(
            f"{b.id} blinked, then nodded. \"Fine. Let's use {fix.label}.\""
        )
        world.say(
            f"They {fix.prep}, and that turned the whole mood around."
        )
        world.say(
            f"Soon they {fix.tail}, and the job finally felt easy."
        )
        world.para()
        world.say(
            f"At the end, {a.id} and {b.id} were laughing together, {prize.phrase} was safe, and the room had a happy ending."
        )
        a.memes["rancor"] = 0.0
        b.memes["rancor"] = 0.0
        a.memes["teamwork"] = a.memes.get("teamwork", 0.0) + 1
        b.memes["teamwork"] = b.memes.get("teamwork", 0.0) + 1
    else:
        pass


def choose_story(seed: int) -> tuple[str, str, str]:
    rng = random.Random(seed)
    task_id = rng.choice(list(TASKS))
    if task_id == "cookies":
        return "kitchen", "cookies", "sprinkles"
    return "playroom", "fort", "blanket"


@dataclass
class StoryParams:
    setting: str
    task: str
    prize: str
    name1: str
    name2: str
    trait1: str
    trait2: str
    seed: Optional[int] = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about close friends, rancor, desire, teamwork, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--trait1")
    ap.add_argument("--trait2")
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
        if not reasonableness(_safe_lookup(TASKS, getattr(args, "task", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, task, prize = getattr(args, "setting", None), getattr(args, "task", None), getattr(args, "prize", None)
    if setting is None or task is None or prize is None:
        setting, task, prize = choose_story(rng.randrange(10**9))
    return StoryParams(
        setting=setting,
        task=task,
        prize=prize,
        name1=getattr(args, "name1", None) or rng.choice(NAMES),
        name2=getattr(args, "name2", None) or rng.choice([n for n in NAMES if n != (getattr(args, "name1", None) or "")]),
        trait1=getattr(args, "trait1", None) or rng.choice(TRAITS),
        trait2=getattr(args, "trait2", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.setting))
    a = world.add(Entity(id=params.name1, kind="character", type="girl" if params.name1 in {"Mina", "June", "Pia"} else "boy"))
    b = world.add(Entity(id=params.name2, kind="character", type="girl" if params.name2 in {"Mina", "June", "Pia"} else "boy"))
    task = _safe_lookup(TASKS, params.task)
    prize = world.add(Entity(id="prize", type="thing", label=_safe_lookup(PRIZES, params.prize).label, phrase=_safe_lookup(PRIZES, params.prize).phrase, caretaker=a.id))
    prop = world.add(Entity(id="prop", type="thing", label=task.keyword, phrase=task.keyword, owner=a.id, caretaker=b.id))
    prop2 = world.add(Entity(id="prop2", type="thing", label=task.keyword, phrase=task.keyword, owner=b.id, caretaker=a.id))
    fix = select_fix(task, _safe_lookup(PRIZES, params.prize))

    tell_story(world, a, b, task, prize, fix)
    world.facts.update(params=params, task=task, prize=prize, a=a, b=b, fix=fix)
    prompts = [
        f"Write a funny short story about two close friends who both want to {task.verb}.",
        f"Tell a comedy story where desire turns into rancor, then teamwork saves the day.",
        f"Write a child-friendly story with an inner monologue, a squabble, and a happy ending.",
    ]
    story_qa = [
        QAItem(
            question=f"Why did {a.id} and {b.id} feel upset at first?",
            answer=f"They both desired the same thing, so their closeness turned into a small rancor when they started arguing about who got to go first.",
        ),
        QAItem(
            question=f"What changed the story from bickering to teamwork?",
            answer=f"They decided to work together and use {fix.label} so they could finish the job without making the problem worse.",
        ),
        QAItem(
            question=f"What was the happy ending?",
            answer=f"{a.id} and {b.id} laughed together at the end, and {prize.phrase} stayed safe while the room ended in a cheerful mood.",
        ),
    ]
    world_qa = [
        QAItem(question="What does teamwork mean?", answer="Teamwork means people help each other and share the job instead of fighting over it."),
        QAItem(question="What is rancor?", answer="Rancor is a sour, grumpy feeling that can happen when people stay angry for a while."),
        QAItem(question="What is desire?", answer="Desire is a strong want for something, like a prize, a treat, or a chance to do a fun job."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"PROMPT {i}: {p}")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(setting,task,prize) :- setting(setting), task(task), prize(prize), compatible(task,prize).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    for task_id, task in TASKS.items():
        for prize_id, prize in PRIZES.items():
            if reasonableness(task, prize):
                lines.append(asp.fact("compatible", task_id, prize_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set()
    for s in SETTINGS:
        for t in TASKS:
            for p in PRIZES:
                if reasonableness(_safe_lookup(TASKS, t), _safe_lookup(PRIZES, p)):
                    python_set.add((s, t, p))
    if clingo_set == python_set:
        print(f"OK: ASP matches Python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH")
    print("only ASP:", sorted(clingo_set - python_set))
    print("only Python:", sorted(python_set - clingo_set))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for t in TASKS:
            for p in PRIZES:
                if reasonableness(_safe_lookup(TASKS, t), _safe_lookup(PRIZES, p)):
                    out.append((s, t, p))
    return out


CURATED = [
    StoryParams("kitchen", "cookies", "sprinkles", "Mina", "Leo", "silly", "busy"),
    StoryParams("playroom", "fort", "blanket", "June", "Nico", "clever", "chatty"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
