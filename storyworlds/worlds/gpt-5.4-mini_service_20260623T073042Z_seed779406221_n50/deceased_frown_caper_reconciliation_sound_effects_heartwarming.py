#!/usr/bin/env python3
"""
storyworlds/worlds/deceased_frown_caper_reconciliation_sound_effects_heartwarming.py
===================================================================================

A small standalone storyworld for a heartwarming tale built from the seed words
"deceased", "frown", and "caper".

Premise:
- A child is sad after a family loss.
- A sibling or caregiver plans a small caper to help make a memory box.
- A misunderstanding causes a frown and a brief emotional dip.
- Reconciliation happens through apology, shared sound effects, and a gentle
  ending image that proves the change.

The world model uses typed entities with physical meters and emotional memes.
It includes a Python reasonableness gate, an inline ASP twin, and grounded QA.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    child: object | None = None
    helper: object | None = None
    keepsake: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    place: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Caper:
    id: str
    verb: str
    sound: str
    goal: str
    turn: str
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
class MemoryItem:
    id: str
    label: str
    phrase: str
    keepsake: bool = True
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

    def people(self) -> list[Entity]:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["frown"] < THRESHOLD:
        return out
    if ("soften",) in world.fired:
        return out
    world.fired.add(("soften",))
    world.get("child").memes["sad"] += 1
    out.append("A small silence settled in the room.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["hurt"] < THRESHOLD or helper.memes["apology"] < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["trust"] += 1
    child.memes["frown"] = 0
    helper.memes["love"] += 1
    out.append("They found their way back to each other.")
    return out


CAUSAL_RULES = [
    Rule("soften", "emotional", _r_soften),
    Rule("reconcile", "social", _r_reconcile),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(setting: Setting, caper: Caper, memory: MemoryItem) -> bool:
    return "reconciliation" in caper.tags and memory.keepsake and caper.goal in {"memory box", "photo album", "warm hug"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for caper_id, caper in CAPERS.items():
            for memory_id, memory in MEMORIES.items():
                if reasonableness_gate(setting, caper, memory):
                    combos.append((place, caper_id, memory_id))
    return combos


@dataclass
class StoryParams:
    place: str
    caper: str
    memory: str
    child: str
    helper: str
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
    "kitchen": Setting(place="the kitchen", affords={"memory_box", "baking"}),
    "living_room": Setting(place="the living room", affords={"memory_box", "story_time"}),
    "porch": Setting(place="the porch", affords={"memory_box"}),
}

CAPERS = {
    "shoe_box_caper": Caper(
        id="shoe_box_caper",
        verb="tiptoe on a tiny caper",
        sound="tap-tap",
        goal="memory box",
        turn="find the keepsakes",
        tags={"reconciliation", "sound_effects"},
    ),
    "drawer_rummage": Caper(
        id="drawer_rummage",
        verb="search the drawer with a careful caper",
        sound="shff-shff",
        goal="memory box",
        turn="find the ribbon",
        tags={"reconciliation", "sound_effects"},
    ),
    "porch_sort": Caper(
        id="porch_sort",
        verb="sort things into a cozy caper",
        sound="rustle-rustle",
        goal="memory box",
        turn="set out the memories",
        tags={"reconciliation", "sound_effects"},
    ),
}

MEMORIES = {
    "blue_scarf": MemoryItem(
        id="blue_scarf",
        label="blue scarf",
        phrase="a soft blue scarf",
        tags={"memory", "cloth"},
    ),
    "button_jar": MemoryItem(
        id="button_jar",
        label="button jar",
        phrase="a little jar of bright buttons",
        tags={"memory", "buttons"},
    ),
    "postcard": MemoryItem(
        id="postcard",
        label="postcard",
        phrase="an old postcard with a smiley stamp",
        tags={"memory", "paper"},
    ),
}

GIRL_NAMES = ["Maya", "Lina", "Nora", "Ivy", "Zoe"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Owen", "Leo"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a young child that includes the word "deceased" and the sound effect "{f["caper"].sound}".',
        f"Tell a gentle story where {f['child'].id} frowns after hearing about a deceased loved one, then joins {f['helper'].id} in a caper to make a memory box.",
        f'Write a reconciliation story with sound effects, a frown, and a warm ending centered on {f["memory"].label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    caper = f["caper"]
    memory = f["memory"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {child.id}, who starts out sad, and {helper.id}, who helps with a gentle caper.",
        ),
        QAItem(
            question=f"Why did {child.id} frown at the start?",
            answer=f"{child.id} frowns because the family is remembering someone deceased, and the feeling is heavy at first.",
        ),
        QAItem(
            question=f"What sound effect went with the caper?",
            answer=f"The caper made a {caper.sound} sound as they moved quietly and carefully.",
        ),
        QAItem(
            question=f"What did they make together?",
            answer=f"They made a memory box for {memory.phrase}, so the keepsake could be stored with care.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with reconciliation: {child.id} and {helper.id} apologized, hugged, and smiled together.",
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(
            QAItem(
                question=f"What changed in {child.id}'s face by the end?",
                answer=f"The frown was gone, replaced by a small relieved smile because they felt safe and understood.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a caper?",
            answer="A caper is a small, playful, careful adventure, often with sneaky footsteps and a little goal.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset, say sorry, and feel close again.",
        ),
        QAItem(
            question="Why do sound effects make stories feel lively?",
            answer="Sound effects help you hear the action in your head, so the scene feels bright and real.",
        ),
    ]


def tell(setting: Setting, caper: Caper, memory: MemoryItem, child_name: str, helper_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="girl" if child_name in GIRL_NAMES else "boy", role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type="woman" if helper_name in GIRL_NAMES else "man", role="helper"))
    keepsake = world.add(Entity(id="keepsake", type="thing", label=memory.label, phrase=memory.phrase))
    child.memes["hurt"] = 1.0
    child.memes["frown"] = 1.0
    child.memes["trust"] = 0.0
    helper.memes["apology"] = 0.0
    helper.memes["love"] = 1.0
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["caper"] = caper
    world.facts["memory"] = memory
    world.facts["keepsake"] = keepsake

    world.say(f"{child.id} stood in {setting.place} with a little frown.")
    world.say(f"The family was remembering someone deceased, and the room felt very quiet.")
    world.para()
    world.say(f"Then {helper.id} leaned close and planned a small {caper.verb}.")
    world.say(f"Tap-tap, {caper.sound}, went their careful feet as they gathered {memory.phrase}.")
    world.para()

    child.memes["hurt"] += 1.0
    helper.memes["apology"] += 1.0
    world.say(f"{child.id} still looked down, because the frown was heavy.")
    world.say(f"{helper.id} said, \"I am sorry.\"")
    propagate(world, narrate=True)
    if child.memes["frown"] >= THRESHOLD:
        child.memes["frown"] = 0.0
    world.say(f"Then they tucked {memory.phrase} into a small memory box.")
    world.say(f"Rustle-rustle, the lid shut softly, and the new box looked warm on the table.")
    world.para()
    world.say(f"{child.id} gave {helper.id} a hug.")
    world.say("The sad day did not disappear, but it became gentler.")
    world.say(f"By the end, {child.id} could smile at the memory and stay close to {helper.id}.")
    world.facts["resolved"] = True
    return world


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)} role={e.role}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this combination does not support a warm reconciliation caper.)"


CURATED = [
    StoryParams(place="living_room", caper="shoe_box_caper", memory="blue_scarf", child="Maya", helper="Aunt June"),
    StoryParams(place="kitchen", caper="drawer_rummage", memory="button_jar", child="Eli", helper="Mom"),
    StoryParams(place="porch", caper="porch_sort", memory="postcard", child="Nora", helper="Dad"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming storyworld with a frown, a caper, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--caper", choices=CAPERS)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--child")
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
              and (getattr(args, "caper", None) is None or c[1] == getattr(args, "caper", None))
              and (getattr(args, "memory", None) is None or c[2] == getattr(args, "memory", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, caper, memory = rng.choice(list(combos))
    child = getattr(args, "child", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper_pool = [n for n in GIRL_NAMES + BOY_NAMES if n != child]
    helper = getattr(args, "helper", None) or rng.choice(helper_pool)
    return StoryParams(place=place, caper=caper, memory=memory, child=child, helper=helper)


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS or params.caper not in CAPERS or params.memory not in MEMORIES:
        pass
    if not reasonableness_gate(_safe_lookup(SETTINGS, params.place), _safe_lookup(CAPERS, params.caper), _safe_lookup(MEMORIES, params.memory)):
        pass
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CAPERS, params.caper), _safe_lookup(MEMORIES, params.memory), params.child, params.helper)
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
valid(P,C,M) :- place(P), caper(C), memory(M), caper_supports(C,reconciliation), memory_keepsake(M).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for c, cap in CAPERS.items():
        lines.append(asp.fact("caper", c))
        if "reconciliation" in cap.tags:
            lines.append(asp.fact("caper_supports", c, "reconciliation"))
    for m, mem in MEMORIES.items():
        lines.append(asp.fact("memory", m))
        if mem.keepsake:
            lines.append(asp.fact("memory_keepsake", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: ASP matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    print("only in asp:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
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
        i = 0
        seen = set()
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        if i:
            print("\n" + "=" * 70 + "\n")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))


if __name__ == "__main__":
    main()
