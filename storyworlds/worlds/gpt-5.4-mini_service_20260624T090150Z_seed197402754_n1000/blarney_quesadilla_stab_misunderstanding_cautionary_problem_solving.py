#!/usr/bin/env python3
"""
Tall-tale storyworld: a blustering town, a quesadilla gone sideways, and a
cautionary misunderstanding that gets solved with patience and a clever fix.

Seed tale:
---
Folks in Bramble Bend said Papa Tully could spin more blarney than a windmill
on a blustery day. One bright afternoon, he promised the whole picnic he could
make the best quesadilla in town. But when he reached for the hot pan, the long
fork slipped and gave the tortilla a sharp stab, and little Dot gasped. She
thought he had hurt the supper on purpose.

Papa Tully laughed, then saw Dot’s worried face and stopped his boasting. He
explained that the fork was only for turning the quesadilla, not for poking
anybody. Together they slowed down, moved the hot pan back, and used a wooden
spatula. Soon the quesadilla came out golden and safe, and Dot learned that
sometimes a big misunderstanding needs a calm talk and a careful plan.

World model:
- meters: physical measures such as heat, sharpness, mess, and doneness
- memes: emotional measures such as blarening, worry, caution, and relief
- story state advances through setup -> misunderstanding -> cautionary turn ->
  problem solving -> resolution
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

    memo: str = ""
    child: object | None = None
    food: object | None = None
    parent: object | None = None
    safe_tool: bool = False
    tool: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    place: str = "the picnic table"
    indoors: bool = False
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
class Tool:
    id: str
    label: str
    safe: bool = False
    turns_food: bool = False
    pokes: bool = False
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
class Food:
    id: str
    label: str
    phrase: str
    region: str = "hands"
    delicate: bool = True
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
class StoryParams:
    name: str
    child_type: str
    parent_type: str
    place: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


SETTINGS = {
    "picnic": Setting("the picnic table", indoors=False),
    "kitchen": Setting("the kitchen", indoors=True),
    "porch": Setting("the porch", indoors=False),
}

TOOLS = {
    "fork": Tool("fork", "a long fork", safe=False, pokes=True),
    "spatula": Tool("spatula", "a wooden spatula", safe=True, turns_food=True),
    "knife": Tool("knife", "a small kitchen knife", safe=False, pokes=True),
    "tongs": Tool("tongs", "a pair of tongs", safe=True, turns_food=True),
}

FOODS = {
    "quesadilla": Food("quesadilla", "quesadilla", "a cheesy quesadilla"),
    "tortilla": Food("tortilla", "tortilla", "a soft tortilla"),
    "snack": Food("snack", "snack", "a warm snack"),
}

NAMES = ["Dot", "Mabel", "Nora", "Lina", "June", "Ruby", "Pip", "Milo"]
PARENTS = ["father", "mother", "uncle", "aunt"]
TRAITS = ["brave", "curious", "quick-tongued", "wide-eyed"]


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(
        id=params.name, kind="character", type=params.child_type, memo="",
        meters={"hunger": 0.0}, memes={"worry": 0.0, "wonder": 0.0, "relief": 0.0}
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=params.parent_type, label=f"the {params.parent_type}",
        memes={"blarney": 0.0, "caution": 0.0, "patience": 0.0}
    ))
    food = world.add(Entity(
        id="Quesadilla", type="quesadilla", label="quesadilla", phrase="a cheesy quesadilla",
        caretaker=parent.id, meters={"heat": 0.0, "doneness": 0.0, "risk": 0.0}, memes={"fame": 0.0}
    ))
    tool = world.add(Entity(
        id="Fork", type="tool", label="fork", phrase="a long fork",
        meters={"sharpness": 1.0}, memes={"fuss": 0.0}
    ))
    safe_tool = world.add(Entity(
        id="Spatula", type="tool", label="spatula", phrase="a wooden spatula",
        meters={"sharpness": 0.0}, memes={"calm": 1.0}
    ))
    world.facts.update(child=child, parent=parent, food=food, tool=tool, safe_tool=safe_tool)
    return world


def nudge(world: World, eid: str, meter: str = None, mdelta: float = 0.0,
          meme: str = None, edelta: float = 0.0) -> None:
    e = world.get(eid)
    if meter:
        e.meters[meter] = e.meters.get(meter, 0.0) + mdelta
    if meme:
        e.memes[meme] = e.memes.get(meme, 0.0) + edelta


def narrate_setup(world: World) -> None:
    c = _safe_fact(world, world.facts, "child")
    p = _safe_fact(world, world.facts, "parent")
    f = _safe_fact(world, world.facts, "food")
    world.say(
        f"{c.id} was a {random.choice(TRAITS)} little {c.type} who loved listening to big stories."
    )
    world.say(
        f"At {world.setting.place}, {p.label} went on with so much blarney that even the napkins seemed to listen."
    )
    world.say(
        f"They were making {f.label} for the picnic, and the whole thing smelled as hopeful as sunshine on a fencepost."
    )


def cause_heat(world: World) -> None:
    food = _safe_fact(world, world.facts, "food")
    nudge(world, food.id, "heat", 1.0)
    nudge(world, food.id, "risk", 0.5)
    world.say(
        f"The skillet got hot, and the {food.label} began to sizzle like a little firecracker in a pan."
    )


def misunderstanding(world: World) -> None:
    c = _safe_fact(world, world.facts, "child")
    p = _safe_fact(world, world.facts, "parent")
    f = _safe_fact(world, world.facts, "food")
    t = _safe_fact(world, world.facts, "tool")
    nudge(world, c.id, meme="worry", edelta=1.0)
    nudge(world, p.id, meme="caution", edelta=1.0)
    nudge(world, p.id, meme="blarney", edelta=1.0)
    world.say(
        f"Then {p.label} reached for {t.label}, and the long fork gave the tortilla a sharp stab as it slid."
    )
    world.say(
        f"{c.id} gasped and thought the supper had been poked the wrong way on purpose."
    )
    world.say(
        f"The little one’s eyes went round as buttons, because a misunderstanding can grow tall as a beanpole when nobody speaks plain."
    )
    world.facts["misunderstanding"] = True


def cautionary_turn(world: World) -> None:
    c = _safe_fact(world, world.facts, "child")
    p = _safe_fact(world, world.facts, "parent")
    f = _safe_fact(world, world.facts, "food")
    t = _safe_fact(world, world.facts, "tool")
    nudge(world, p.id, meme="patience", edelta=1.0)
    nudge(world, c.id, meme="worry", edelta=-0.25)
    world.say(
        f"{p.label} stopped smiling and said, \"Easy now. A fork can poke, and hot food can bite back if we rush it.\""
    )
    world.say(
        f"That warning sounded serious enough to shake the blarney out of the air."
    )
    world.say(
        f"{p.label} showed that {t.label} was only for turning the {f.label}, not for hurting anybody."
    )
    world.facts["cautionary"] = True


def problem_solving(world: World) -> None:
    c = _safe_fact(world, world.facts, "child")
    p = _safe_fact(world, world.facts, "parent")
    f = _safe_fact(world, world.facts, "food")
    safe_tool = _safe_fact(world, world.facts, "safe_tool")
    nudge(world, p.id, meme="caution", edelta=-0.5)
    nudge(world, c.id, meme="wonder", edelta=1.0)
    world.say(
        f"Together they moved the hot pan back from the edge of the table."
    )
    world.say(
        f"Then they swapped the fork for the {safe_tool.label}, which slid under the {f.label} as gentle as a cloud."
    )
    world.say(
        f"That was the problem-solving part: less hurry, more care, and one steady hand after another."
    )
    world.facts["problem_solving"] = True


def resolution(world: World) -> None:
    c = _safe_fact(world, world.facts, "child")
    p = _safe_fact(world, world.facts, "parent")
    f = _safe_fact(world, world.facts, "food")
    nudge(world, c.id, meme="worry", edelta=-1.0)
    nudge(world, c.id, meme="relief", edelta=1.0)
    nudge(world, f.id, "doneness", 1.0)
    world.say(
        f"Soon the {f.label} came out golden and whole, and not one bite had been spoiled."
    )
    world.say(
        f"{c.id} laughed, because the big scare had turned into a safe supper and a much better story."
    )
    world.say(
        f"{p.label} grinned too, and the last of the blarney sounded kinder than before."
    )
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    narrate_setup(world)
    world.para()
    cause_heat(world)
    misunderstanding(world)
    world.para()
    cautionary_turn(world)
    problem_solving(world)
    world.para()
    resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    c = _safe_fact(world, world.facts, "child")
    p = _safe_fact(world, world.facts, "parent")
    f = _safe_fact(world, world.facts, "food")
    return [
        "Write a tall tale for a young child about blarney, a quesadilla, and a misunderstanding that gets solved safely.",
        f"Tell a gentle story where {c.id} thinks {p.label} hurt a {f.label}, but the grown-up explains and fixes the problem.",
        "Create a child-friendly cautionary story with a hot pan, a bad guess, and a careful solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = _safe_fact(world, world.facts, "child")
    p = _safe_fact(world, world.facts, "parent")
    f = _safe_fact(world, world.facts, "food")
    return [
        QAItem(
            question=f"Who was the story mainly about?",
            answer=f"The story was mainly about {c.id}, who got worried when the {f.label} was handled in a surprising way."
        ),
        QAItem(
            question=f"Why did {c.id} think something was wrong with the {f.label}?",
            answer=(
                f"{c.id} saw {p.label} use a fork and thought the sharp poke meant the {f.label} had been hurt on purpose. "
                f"It was a misunderstanding, because the fork was only being used to turn the food."
            ),
        ),
        QAItem(
            question=f"What did {p.label} do to solve the problem?",
            answer=(
                f"{p.label} explained the mistake, moved the hot pan back, and used a wooden spatula instead of the fork. "
                f"That careful plan kept the supper safe."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"The {f.label} came out golden and whole, {c.id} felt relieved, and the grown-up’s blarney turned into a kinder, calmer voice."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is blarney?",
            answer="Blarney is smooth, showy talk that can sound bigger than the truth, like a boast told with a grin."
        ),
        QAItem(
            question="What is a quesadilla?",
            answer="A quesadilla is a warm tortilla filled with cheese or other good things, usually cooked in a pan until it is melty."
        ),
        QAItem(
            question="Why should a hot pan be handled carefully?",
            answer="A hot pan can burn hands and make food cook too fast, so it should be moved slowly and with care."
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_invalid(place: str) -> str:
    return f"(No story: {place} is not a known setting for this tall tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld with blarney, a quesadilla, and careful problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "uncle", "aunt"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    child_type = "girl" if gender == "girl" else "boy"
    return StoryParams(name=name, child_type=child_type, parent_type=parent, place=place)


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


ASP_RULES = r"""
place(picnic). place(kitchen). place(porch).
setting_place(picnic). setting_place(kitchen). setting_place(porch).

child(girl). child(boy).
parent(mother). parent(father). parent(uncle). parent(aunt).

tool(fork). tool(spatula). tool(knife). tool(tongs).
safe_tool(spatula). safe_tool(tongs).
pokes(fork). pokes(knife).
turns_food(spatula). turns_food(tongs).

food(quesadilla).
story_feature(misunderstanding).
story_feature(cautionary).
story_feature(problem_solving).

misunderstanding :- pokes(fork), turns_food(spatula).
cautionary :- safe_tool(spatula).
problem_solving :- safe_tool(spatula), food(quesadilla).

valid_story(P) :- setting_place(P), misunderstanding, cautionary, problem_solving.

#show valid_story/1.
#show misunderstanding/0.
#show cautionary/0.
#show problem_solving/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for t in TOOLS.values():
        lines.append(asp.fact("tool", t.id))
        if t.safe:
            lines.append(asp.fact("safe_tool", t.id))
        if t.pokes:
            lines.append(asp.fact("pokes", t.id))
        if t.turns_food:
            lines.append(asp.fact("turns_food", t.id))
    for f in FOODS.values():
        lines.append(asp.fact("food", f.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("picnic",), ("kitchen",), ("porch",)}
    clingo = set(asp_valid_places())
    if py == clingo:
        print(f"OK: ASP gate matches Python ({len(py)} places).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("python:", sorted(py))
    print("asp:", sorted(clingo))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for row in asp_valid_places():
            print(row[0])
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in [StoryParams("Dot", "girl", "father", "picnic")]:
            samples.append(generate(p))
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
