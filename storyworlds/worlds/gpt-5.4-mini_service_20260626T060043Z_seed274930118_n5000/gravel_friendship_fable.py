#!/usr/bin/env python3
"""
A small fable world about friendship, a gravel pile, and a kind repair.

A short source tale behind the model:
---
Near a garden gate, a little rabbit and a small sparrow were friends. One day,
the rain left the path loose and rough with gravel. The rabbit wanted the path
smooth so an old tortoise could visit, but the sparrow thought the stones were
only clutter. Together they carried the gravel, packed the path, and made a
safe road. The tortoise arrived happily, and the friends learned that even
small hands can help in a big way.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    a: object | None = None
    b: object | None = None
    c: object | None = None
    path: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "rabbit": {"subject": "it", "object": "it", "possessive": "its"},
            "hare": {"subject": "it", "object": "it", "possessive": "its"},
            "sparrow": {"subject": "it", "object": "it", "possessive": "its"},
            "tortoise": {"subject": "it", "object": "it", "possessive": "its"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]

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
    weather: str = "after rain"
    helps: set[str] = field(default_factory=set)
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
    mess: str
    soil: str
    keyword: str = "gravel"
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
    region: str = "path"
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
class Plan:
    label: str
    verb: str
    result: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
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
        self.trace: list[str] = []

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


def _count_meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _add_meter(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amt


def _add_meme(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amt


def _do_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    if task.id not in world.setting.helps:
        pass
    _add_meter(actor, task.mess)
    _add_meme(actor, "purpose")
    if narrate:
        world.say(f"{actor.id} began to {task.verb}.")


def _spread_gravel(world: World, task: Task) -> None:
    for e in list(world.entities.values()):
        if e.kind == "character" and _count_meter(e, task.mess) >= THRESHOLD:
            if ("gravel_shift", e.id) not in world.fired:
                world.fired.add(("gravel_shift", e.id))
                _add_meme(e, "effort")
                world.trace.append(f"{e.id} moved gravel.")


def _fix_path(world: World, path: Entity, plan: Plan) -> None:
    if _count_meter(path, "loose") >= THRESHOLD and _count_meter(path, "packed") < THRESHOLD:
        _add_meter(path, "packed")
        world.say(f"The path grew firmer under their small, careful work.")


def _help_arrive(world: World, friend: Entity) -> None:
    if _count_meter(friend, "welcomed") < THRESHOLD:
        _add_meter(friend, "welcomed")
        _add_meme(friend, "joy")
        world.say(f"{friend.id} arrived smiling, because the road was safe to cross.")


@dataclass
class StoryParams:
    place: str
    task: str
    hero1: str
    hero2: str
    friend: str
    trait: str
    seed: Optional[int] = None
    p: object | None = None
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


SETTINGS = {
    "garden_gate": Setting(place="the garden gate", helps={"move_gravel"}),
    "old_lane": Setting(place="the old lane", helps={"move_gravel"}),
}

TASKS = {
    "move_gravel": Task(
        id="move_gravel",
        verb="carry away the loose gravel",
        gerund="carrying away loose gravel",
        rush="hurry to brush the stones aside",
        mess="effort",
        soil="stiff with effort",
        tags={"gravel", "path", "friendship"},
    )
}

PRIZES = {
    "path": Prize(
        label="path",
        phrase="the little path to the gate",
        type="path",
        region="path",
    )
}

PLANS = {
    "pack_path": Plan(
        label="pack the path",
        verb="pack the path",
        result="firm",
        prep="walk together and press the stones down",
        tail="walked side by side until the road felt smooth",
        guards={"effort"},
    )
}

NAMES = ["Pip", "Moss", "Lark", "Nim", "Bram", "Wren"]
FRIENDS = ["Toto", "Sage", "June", "Ollie", "Mira"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for task_id in setting.helps:
            for prize_id in PRIZES:
                out.append((place, task_id, prize_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world about friendship and gravel.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--trait", choices=["kind", "patient", "bright", "steady"])
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
    if getattr(args, "task", None) and getattr(args, "task", None) not in TASKS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, prize = (list(rng.choice(combos)) + [None, None, None])[:3]
    return StoryParams(
        place=place,
        task=task,
        hero1=getattr(args, "name", None) or rng.choice(NAMES),
        hero2=getattr(args, "friend_name", None) or rng.choice(FRIENDS),
        friend=getattr(args, "friend_name", None) or rng.choice(FRIENDS),
        trait=getattr(args, "trait", None) or rng.choice(["kind", "patient", "bright", "steady"]),
    )


def tell(setting: Setting, task: Task, prize: Prize, p: StoryParams) -> World:
    world = World(setting)
    a = world.add(Entity(id=p.hero1, kind="character", type="rabbit"))
    b = world.add(Entity(id=p.hero2, kind="character", type="sparrow"))
    c = world.add(Entity(id="visitor", kind="character", type="tortoise"))
    path = world.add(Entity(id="path", kind="thing", type="path", label="path"))
    _add_meter(path, "loose", 1.0)

    world.say(f"Near {setting.place}, {a.id} and {b.id} were friends.")
    world.say(f"{a.id} was {p.trait}, and {b.id} was quick with a song.")
    world.say(f"After the rain, the gravel on the path lay loose and rough.")
    world.para()

    world.say(f"{a.id} wanted to {task.verb} so an old friend could visit.")
    world.say(f"{b.id} said the stones were only clutter and should be left alone.")
    _add_meme(a, "care")
    _add_meme(b, "doubt")
    _do_task(world, a, task, narrate=False)
    _do_task(world, b, task, narrate=False)
    _spread_gravel(world, task)
    world.say(f"Then {a.id} asked {b.id} to help, because friendship was more useful than pride.")
    world.para()

    plan = PLANS["pack_path"]
    world.say(f"{b.id} looked again and saw the need. Together they chose to {plan.verb}.")
    world.say(f"They {plan.prep}, and the path became {plan.result}.")
    _fix_path(world, path, plan)
    _add_meter(c, "welcomed", 1.0)
    _help_arrive(world, c)
    world.say(f"{c.id} came at last, and the three friends shared the quiet joy of a good deed.")
    world.say("So they learned that even small stones can become a help when friends carry them together.")

    world.facts.update(hero=a, helper=b, visitor=c, path=path, task=task, prize=prize, plan=plan, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for children about friendship and the word "{f["task"].keyword}".',
        f"Tell a gentle story where {f['hero'].id} and {f['helper'].id} work together to fix a rough path.",
        f"Write a simple moral tale in which loose gravel becomes useful because friends choose kindness over grumbling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    visitor = _safe_fact(world, f, "visitor")
    task = _safe_fact(world, f, "task")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"Who were the friends near {place}?",
            answer=f"The friends were {hero.id} and {helper.id}. They stayed close and solved the problem together.",
        ),
        QAItem(
            question=f"What problem did the loose gravel cause on the path?",
            answer="The path was rough and unsafe, so it needed careful work before an old friend could visit.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the gravel?",
            answer=f"{hero.id} wanted to {task.verb}, because the path needed to be made smooth again.",
        ),
        QAItem(
            question=f"Why did {helper.id} change from doubt to help?",
            answer=f"{helper.id} saw that the work was kind and useful, and friendship was worth more than leaving the stones alone.",
        ),
        QAItem(
            question=f"Who arrived after the friends fixed the path?",
            answer=f"{visitor.id} arrived happily after the path was packed and made safe to cross.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gravel?",
            answer="Gravel is a mix of small stones. People use it on paths and roads because it can make the ground firm.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind bond between creatures who care about one another, share help, and stay loyal.",
        ),
        QAItem(
            question="Why do people pack a loose path?",
            answer="People pack a loose path so it becomes firm and safe to walk on.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for t in sorted(setting.helps):
            lines.append(asp.fact("helps", place, t))
    for task_id, task in TASKS.items():
        lines.append(asp.fact("task", task_id))
        lines.append(asp.fact("keyword", task_id, task.keyword))
    for prize_id in PRIZES:
        lines.append(asp.fact("prize", prize_id))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,R) :- setting(P), helps(P,T), task(T), prize(R).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(PRIZES, params.prize), params)
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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for i, (place, task, prize) in enumerate(valid_combos()):
            p = StoryParams(
                place=place,
                task=task,
                hero1=_safe_lookup(NAMES, i % len(NAMES)),
                hero2=_safe_lookup(FRIENDS, i % len(FRIENDS)),
                friend=_safe_lookup(FRIENDS, i % len(FRIENDS)),
                trait=["kind", "patient", "bright", "steady"][i % 4],
                seed=base_seed + i,
            )
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                p = resolve_params(args, rng)
            except StoryError:
                continue
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
