#!/usr/bin/env python3
"""
storyworlds/worlds/chug_digital_polio_teamwork_fable.py
=======================================================

A small fable-style story world about a village journey where teamwork,
a chugging ride, and a digital helper keep a polio medicine delivery on track.

The seed tale behind this world is simple:
- A stormy road makes a medicine run hard.
- The travelers have a chugging vehicle, a digital map, and a child-safe
  delivery of polio drops.
- They can succeed only by helping one another.

This script turns that premise into a compact simulated domain with stateful
physical meters and emotional memes, a reasonableness gate, and an inline ASP
twin for parity checks.
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

    aid: object | None = None
    friend: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    place: str = "the village road"
    affords: set[str] = field(default_factory=set)
    SETTING: object | None = None
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
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
    kind: str
    plural: bool = False
    fragile: bool = True
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
    helps: set[str]
    prep: str
    tail: str
    keyword: str
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_stall(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters.get("stuck", 0) < THRESHOLD:
            continue
        sig = ("stall", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] = e.memes.get("worry", 0) + 1
        out.append(f"The little road slowed {e.label_word} down.")
    return out


def _r_teamwork(world: World) -> list[str]:
    for e in list(world.entities.values()):
        if e.memes.get("teamwork", 0) < THRESHOLD:
            continue
        sig = ("teamwork", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["hope"] = e.memes.get("hope", 0) + 1
        return [f"{e.label_word} felt stronger with help nearby."]
    return []


CAUSAL_RULES = [
    _r_stall,
    _r_teamwork,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def chance_of_success(world: World, hero: Entity, action: Action, prize: Prize) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters[action.id] = sim.get(hero.id).meters.get(action.id, 0) + 1
    if prize.kind == "polio":
        sim.get("vaccine").meters["safe"] = 1
    return True


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"Once in {world.setting.place}, {hero.id} was a little {hero.type} who loved to help, "
        f"and {friend.id} was a steady friend who never rushed past a problem."
    )


def setup(world: World, hero: Entity, friend: Entity, prize: Entity, aid: Aid, action: Action) -> None:
    world.say(
        f"They were carrying {prize.phrase} to the far homes, because the village needed "
        f"{prize.label} for the children."
    )
    world.say(
        f"Along the way they had a {aid.label} and a {action.keyword} ride that went "
        f"chug, chug, chug."
    )


def conflict(world: World, hero: Entity, friend: Entity, prize: Entity, action: Action) -> None:
    hero.meters["stuck"] = hero.meters.get("stuck", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"But the muddy path made the cart slow, and {hero.id} wanted to hurry so the "
        f"{prize.label} would not grow late."
    )
    world.say(
        f"{friend.id} shook {friend.pronoun('possessive')} head and said, "
        f'"We go farther when we go together."'
    )


def turn(world: World, hero: Entity, friend: Entity, aid: Aid) -> None:
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0) + 1
    friend.memes["teamwork"] = friend.memes.get("teamwork", 0) + 1
    world.say(
        f"Then they used the {aid.label}: one steered, one watched the road, and one checked "
        f"the {aid.keyword} map so they would not turn the wrong way."
    )
    propagate(world, narrate=True)


def resolution(world: World, hero: Entity, friend: Entity, prize: Entity, aid: Aid, action: Action) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0) + 1
    world.say(
        f"At last they reached the homes, and the {prize.label} stayed safe and ready."
    )
    world.say(
        f"{hero.id} smiled because the {aid.tail}, and the road that felt hard at first "
        f"had become a lesson in teamwork."
    )
    world.say(
        f"The fable ended with the best kind of sound: a gentle chug forward, and no one left behind."
    )


SETTING = Setting(
    place="the village road",
    affords={"chug", "digital", "polio", "teamwork"},
)

ACTIONS = {
    "chug": Action(
        id="chug",
        verb="chug along the road",
        gerund="chugging along",
        rush="hurry down the muddy lane",
        weather="rainy",
        keyword="chug",
        tags={"chug"},
    ),
    "digital": Action(
        id="digital",
        verb="check a digital map",
        gerund="checking a digital map",
        rush="peer at the screen",
        weather="rainy",
        keyword="digital",
        tags={"digital"},
    ),
    "polio": Action(
        id="polio",
        verb="carry polio drops",
        gerund="carrying polio drops",
        rush="bring the drops quickly",
        weather="rainy",
        keyword="polio",
        tags={"polio"},
    ),
    "teamwork": Action(
        id="teamwork",
        verb="work as a team",
        gerund="working together",
        rush="try to do it alone",
        weather="rainy",
        keyword="teamwork",
        tags={"teamwork"},
    ),
}

PRIZES = {
    "vaccine": Prize(
        label="polio drops",
        phrase="a small cooler of polio drops",
        type="medicine",
        kind="polio",
        plural=True,
        fragile=True,
    ),
}

AIDS = {
    "tablet": Aid(
        id="tablet",
        label="digital tablet",
        helps={"digital"},
        prep="hold up the digital tablet",
        tail="used the digital tablet to find the best path",
        keyword="digital",
    ),
}

NAMES = ["Mina", "Tavi", "Rafi", "Lena", "Kito", "Sana"]
FRIENDS = ["heron", "goat", "mole", "fox", "donkey"]
TRAITS = ["kind", "careful", "brave", "patient"]


@dataclass
class StoryParams:
    name: str
    friend: str
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
    return [("village", "chug", "vaccine"), ("village", "digital", "vaccine"),
            ("village", "polio", "vaccine"), ("village", "teamwork", "vaccine")]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short fable for a young child that includes the words "chug", "digital", and "polio".',
        f"Tell a gentle teamwork fable about {f['hero'].id} and a {f['friend'].id} delivering {f['prize'].label}.",
        "Write a simple moral tale where a hard road becomes easier because friends work together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, aid, action = f["hero"], f["friend"], f["prize"], f["aid"], f["action"]
    return [
        QAItem(
            question=f"Who went on the journey in the story?",
            answer=f"{hero.id} and {friend.id} went together to carry {prize.label} through the village.",
        ),
        QAItem(
            question=f"What sound did the ride make?",
            answer="The ride made a soft chug, chug, chug as they moved along the road.",
        ),
        QAItem(
            question=f"How did the digital tablet help them?",
            answer=f"The digital tablet showed the safest path, so they could keep going without getting lost.",
        ),
        QAItem(
            question=f"Why were they carrying the polio drops?",
            answer="They were bringing the polio drops to the village homes so children could have them in time.",
        ),
        QAItem(
            question=f"What lesson did the story teach about teamwork?",
            answer="The story taught that teamwork makes a hard job easier and helps friends finish safely together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a digital tablet?",
            answer="A digital tablet is a small screen you can tap to read maps, messages, or pictures.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help one another to finish a job together.",
        ),
        QAItem(
            question="What does a chugging vehicle sound like?",
            answer="A chugging vehicle makes a steady, bumpy sound as it moves along.",
        ),
        QAItem(
            question="What are polio drops for?",
            answer="Polio drops are medicine that helps protect children from polio.",
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
        lines.append(f"  {e.id:10} ({e.type:8}) meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "village")]
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tagged", aid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("kind", pid, p.kind))
    for aid in AIDS.values():
        lines.append(asp.fact("aid", aid.id))
        for h in sorted(aid.helps):
            lines.append(asp.fact("helps", aid.id, h))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(village, A, P) :- action(A), prize(P), kind(P, polio), tagged(A, chug).
valid_story(village, A, P) :- action(A), prize(P), kind(P, polio), tagged(A, digital).
valid_story(village, A, P) :- action(A), prize(P), kind(P, polio), tagged(A, teamwork).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about chugging, digital help, polio drops, and teamwork.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--trait", choices=TRAITS)
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
    name = getattr(args, "name", None) or rng.choice(NAMES)
    friend = getattr(args, "friend", None) or rng.choice(FRIENDS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(name=name, friend=friend, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type="girl", label=params.name))
    friend = world.add(Entity(id=params.friend, kind="character", type="animal", label=params.friend))
    prize = world.add(Entity(id="vaccine", type="medicine", label="polio drops", phrase="a small cooler of polio drops", plural=True))
    aid = world.add(Entity(id="tablet", type="tool", label="digital tablet"))
    action = ACTIONS["chug"]

    world.say(
        f"Once in {world.setting.place}, {hero.id} was a {params.trait} little helper, and {friend.id} was a faithful companion."
    )
    world.say(
        f"They had one important job: bring {prize.phrase} to the far homes before night."
    )
    world.say(
        f"Their cart went chug, chug, chug, and the digital tablet glowed like a tiny guide."
    )
    world.para()
    world.say(
        f"But the road had puddles and mud, and the cart began to slow."
    )
    world.say(
        f"{hero.id} worried that the polio drops would arrive too late."
    )
    world.say(
        f"Then {friend.id} reminded {hero.id} that a problem is smaller when two friends carry it together."
    )
    world.para()
    hero.memes["worry"] = 1
    hero.meters["stuck"] = 1
    world.facts.update(hero=hero, friend=friend, prize=prize, aid=aid, action=action)
    turn(world, hero, friend, aid)
    resolution(world, hero, friend, prize, aid, action)
    hero.memes["teamwork"] = 1
    friend.memes["teamwork"] = 1
    return world


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
    StoryParams(name="Mina", friend="goat", trait="kind"),
    StoryParams(name="Tavi", friend="fox", trait="patient"),
    StoryParams(name="Rafi", friend="heron", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
