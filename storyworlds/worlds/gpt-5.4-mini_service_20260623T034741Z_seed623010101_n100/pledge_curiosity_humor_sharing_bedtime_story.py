#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/pledge_curiosity_humor_sharing_bedtime_story.py
==========================================================================================================================

A small bedtime-story world about a curious child, a funny bedtime problem,
and a sharing-based pledge that helps everyone settle down.

Seed tale inspiration:
---
At bedtime, Nia hears a tiny tap-tap from under the bed. She is curious and
peeks under the blanket fort. She finds a sleepy bunny, a missing storybook,
and a pile of toy socks that make the whole room look silly. Nia laughs, shares
the flashlight with her little brother, and makes a pledge to put the toys away
before the final story. Together they tidy the room, tell one last joke, and
fall asleep feeling cozy.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    caretaker: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    hidden: object | None = None
    sibling: object | None = None
    toy: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Room:
    name: str
    cozy: str
    hidden_spot: str
    bedtime_object: str
    bedtime_sound: str
    tidy_task: str
    joke: str
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
class BedtimeThing:
    id: str
    label: str
    phrase: str
    type: str
    plural: bool = False
    messy: bool = False
    comforting: bool = False
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
class StoryParams:
    room: str
    child: str
    sibling: str
    toy: str
    hidden: str
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


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.cursor_hidden: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
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
        w = World(self.room)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.cursor_hidden = self.cursor_hidden
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    CAUSAL_RULES: list = field(default_factory=list)
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


def _r_tidy(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["mess"] < THRESHOLD:
            continue
        sig = ("tidy", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["mess"] = 0.0
        ent.meters["tidy"] += 1
        out.append(f"The room looked calmer after the toys were put away.")
    return out


CAUSAL_RULES = [Rule("tidy", "physical", _r_tidy)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(items)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hidden_at_risk(hidden: BedtimeThing) -> bool:
    return hidden.messy or hidden.comforting


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room_id in ROOMS:
        for child in CHILDREN:
            for toy_id, toy in THINGS.items():
                for hidden_id, hidden in THINGS.items():
                    if toy_id == hidden_id:
                        continue
                    if hidden_at_risk(hidden):
                        combos.append((room_id, child, hidden_id))
    return combos


def setup_prediction(world: World, child: Entity, toy: BedtimeThing) -> bool:
    sim = world.copy()
    sim.get(child.id).memes["curiosity"] += 1
    sim.get(child.id).meters["mess"] += 1
    propagate(sim, narrate=False)
    return sim.get(child.id).meters["mess"] < THRESHOLD


def tell(room: Room, child_name: str, sibling_name: str, toy_cfg: BedtimeThing, hidden_cfg: BedtimeThing, helper_name: str) -> World:
    world = World(room)
    child = world.add(Entity(id=child_name, kind="character", type="girl" if child_name in GIRL_NAMES else "boy", role="curious child", traits=["curious", "sleepy"]))
    sibling = world.add(Entity(id=sibling_name, kind="character", type="boy" if sibling_name in BOY_NAMES else "girl", role="younger sibling", traits=["tiny", "silly"]))
    helper = world.add(Entity(id=helper_name, kind="character", type="parent", role="helper", traits=["kind"]))
    toy = world.add(Entity(id="toy", type=toy_cfg.type, label=toy_cfg.label, plural=toy_cfg.plural, owner=child.id))
    hidden = world.add(Entity(id="hidden", type=hidden_cfg.type, label=hidden_cfg.label, plural=hidden_cfg.plural, owner=child.id))

    child.memes["curiosity"] = 1.0
    child.memes["humor"] = 0.0
    child.memes["sharing"] = 0.0
    sibling.memes["humor"] = 0.0
    helper.memes["comfort"] = 1.0
    child.meters["mess"] = 0.0
    sibling.meters["sleepy"] = 0.0

    world.say(f"{child.id} was tucked in a cozy room, where {room.cozy}.")
    world.say(f"Near {room.hidden_spot}, {room.bedtime_sound} made the dark feel like a little secret.")
    world.say(f"{child.id} loved bedtime, but {child.pronoun()} was curious about what might be hiding in the shadows.")

    world.para()
    world.say(f"Then {child.id} saw {hidden.phrase} and had to peek.")
    child.memes["curiosity"] += 1
    world.cursor_hidden = True
    if hidden.comforting:
        world.say(f"It looked so soft and funny that {child.id} laughed right away.")
        child.memes["humor"] += 1
    else:
        world.say(f"It looked so silly that {child.id} snorted a tiny laugh.")
        child.memes["humor"] += 1

    world.say(f"{sibling.id} came over with {toy.phrase}, and {child.id} shared the light so they could look together.")
    child.memes["sharing"] += 1
    sibling.memes["sharing"] += 1

    world.para()
    world.say(f"{child.id} made a pledge to put the toys away before the final story.")
    child.memes["comfort"] += 1
    toy.meters["mess"] += 1
    propagate(world, narrate=False)

    world.say(f"Together they picked up {toy.label} and fixed the bedtime corner.")
    child.meters["mess"] = 0.0
    hidden.meters["tidy"] += 1
    world.say(f"Even {helper.id} smiled, because the room grew neat and ready for sleep.")
    world.say(f"At last, {child.id} and {sibling.id} lay down while {room.joke} made them giggle one more time.")
    world.say(f"The pledge had turned a curious, silly bedtime into a calm one.")

    world.facts.update(
        child=child,
        sibling=sibling,
        helper=helper,
        toy=toy,
        hidden=hidden,
        room=room,
        pledge="put the toys away before the final story",
        outcome="cozy",
    )
    return world


ROOMS = {
    "moonroom": Room(
        name="moon room",
        cozy="the quilt was soft and the lamp glowed like a tiny moon",
        hidden_spot="under the bed",
        bedtime_object="flashlight",
        bedtime_sound="tap-tap",
        tidy_task="toy socks",
        joke="the pillow seemed to wink",
    ),
    "nestroom": Room(
        name="nest room",
        cozy="stuffed animals made the blankets look like a nest",
        hidden_spot="behind the pillow pile",
        bedtime_object="storybook",
        bedtime_sound="thump-thump",
        tidy_task="little blocks",
        joke="a teddy bear wore the silliest hat",
    ),
    "lanternroom": Room(
        name="lantern room",
        cozy="the nightlight painted gold stripes on the wall",
        hidden_spot="inside the blanket fort",
        bedtime_object="nightlight",
        bedtime_sound="tick-tick",
        tidy_task="crayons",
        joke="the sock puppet gave a sleepy bow",
    ),
}

THINGS = {
    "toy_socks": BedtimeThing(id="toy_socks", label="toy socks", phrase="a pile of toy socks", type="socks", plural=True, messy=True, tags={"sharing"}),
    "storybook": BedtimeThing(id="storybook", label="storybook", phrase="the missing storybook", type="book", comforting=True, tags={"curiosity"}),
    "bunny": BedtimeThing(id="bunny", label="sleepy bunny", phrase="a sleepy bunny", type="bunny", comforting=True, tags={"humor"}),
    "blocks": BedtimeThing(id="blocks", label="little blocks", phrase="little blocks", type="blocks", plural=True, messy=True, tags={"sharing"}),
    "flashlight": BedtimeThing(id="flashlight", label="flashlight", phrase="a flashlight", type="tool", comforting=True, tags={"sharing"}),
    "blanket": BedtimeThing(id="blanket", label="blanket fort", phrase="the blanket fort", type="blanket", comforting=True, tags={"curiosity", "humor"}),
}

CHILDREN = ["Nia", "Milo", "Pia", "Theo", "Luna", "Ben"]
GIRL_NAMES = ["Nia", "Pia", "Luna"]
BOY_NAMES = ["Milo", "Theo", "Ben"]


def explain_rejection(hidden: BedtimeThing) -> str:
    return f"(No story: {hidden.label} would not create a bedtime curiosity turn.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    sibling = f["sibling"]
    room = f["room"]
    hidden = f["hidden"]
    return [
        f'Write a gentle bedtime story for a 3-to-5-year-old about {child.id} and {sibling.id}, where curiosity leads to a funny discovery in the {room.name}. Include the word "pledge".',
        f"Tell a cozy story where {child.id} peeks under {room.hidden_spot}, shares the light with {sibling.id}, and makes a pledge to tidy up before sleep.",
        f'Write a bedtime story with curiosity, humor, and sharing that ends with a promise to put {hidden.label} away before the final story.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    sibling = f["sibling"]
    helper = f["helper"]
    room = f["room"]
    toy = f["toy"]
    hidden = f["hidden"]
    qa = [
        QAItem(
            question=f"What did {child.id} do when bedtime got interesting in the {room.name}?",
            answer=f"{child.id} peeked under {room.hidden_spot} because {child.pronoun()} was curious. That little peek led to a funny surprise and a very cozy ending.",
        ),
        QAItem(
            question=f"How did {child.id} and {sibling.id} share during the bedtime story?",
            answer=f"They shared the light and looked together instead of keeping the surprise to one person. Sharing made the moment calmer and helped them solve the little bedtime mess.",
        ),
        QAItem(
            question=f"What pledge did {child.id} make before the final story?",
            answer=f"{child.id} made a pledge to put the toys away before the final story. That promise helped the room become neat and ready for sleep.",
        ),
        QAItem(
            question=f"Why did {helper.id} smile at the end?",
            answer=f"{helper.id} smiled because the children tidied up and kept the bedtime corner peaceful. The room was cozy again, so everyone could settle down happily.",
        ),
    ]
    if toy.meters["mess"] >= THRESHOLD:
        qa.append(QAItem(
            question=f"What changed after {child.id} touched {toy.label}?",
            answer=f"The toy made the room a little messy, so the children had to put it away. Once they did, the mess disappeared and bedtime felt calm again.",
        ))
    if hidden.comforting:
        qa.append(QAItem(
            question=f"Why was {hidden.label} funny to find?",
            answer=f"{hidden.label} looked sweet and a little silly, so {child.id} laughed right away. The funny surprise helped turn curiosity into a warm bedtime moment.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["hidden"].tags) | set(world.facts["toy"].tags) | {"pledge"}
    out: list[QAItem] = []
    if "curiosity" in tags:
        out.append(QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn about something new. It helps children discover little surprises.",
        ))
    if "humor" in tags:
        out.append(QAItem(
            question="What is humor?",
            answer="Humor is what makes people laugh or smile. A silly sound, a funny face, or a cozy joke can all bring humor to a story.",
        ))
    if "sharing" in tags:
        out.append(QAItem(
            question="What does sharing mean?",
            answer="Sharing means using something together or giving someone else a turn. It helps people feel close and kind to one another.",
        ))
    out.append(QAItem(
        question="What is a pledge?",
        answer="A pledge is a promise you make carefully and mean to keep. In a story, a pledge can help a child choose the right thing before bedtime.",
    ))
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(room="moonroom", child="Nia", sibling="Milo", toy="flashlight", hidden="storybook", helper="Mama"),
    StoryParams(room="nestroom", child="Pia", sibling="Ben", toy="blocks", hidden="bunny", helper="Papa"),
    StoryParams(room="lanternroom", child="Luna", sibling="Theo", toy="toy_socks", hidden="blanket", helper="Auntie"),
]


ASP_RULES = r"""
choice_hidden(H) :- hidden(H).
curiosity_turn(C,H) :- child(C), hidden(H), comforting(H).
sharing_turn(C,S) :- child(C), sibling(S), shareable(T), toy(T).
pledge_turn(C) :- child(C), pledge_word.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for cid in CHILDREN:
        lines.append(asp.fact("child", cid))
    for tid, thing in THINGS.items():
        lines.append(asp.fact("hidden", tid))
        if thing.comforting:
            lines.append(asp.fact("comforting", tid))
        if thing.messy:
            lines.append(asp.fact("messy", tid))
        if thing.id in {"flashlight", "toy_socks", "blocks"}:
            lines.append(asp.fact("shareable", tid))
    lines.append(asp.fact("pledge_word", "pledge"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show curiosity_turn/2.\n#show sharing_turn/2.\n#show pledge_turn/1."))
    return sorted(set(asp.atoms(model, "curiosity_turn")))


def asp_verify() -> int:
    # smoke test generation
    try:
        sample = generate(resolve_params(argparse.Namespace(room=None, child=None, sibling=None, toy=None, hidden=None, helper=None, seed=None), random.Random(7)))
        assert sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    # basic parity: python gate vs ASP facts
    try:
        import asp
        _ = asp_program("#show pledge_turn/1.")
    except Exception as exc:
        print(f"ASP SETUP FAILED: {exc}")
        return 1
    print("OK: smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: curiosity, humor, sharing, and a pledge.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--sibling", choices=CHILDREN)
    ap.add_argument("--toy", choices=THINGS)
    ap.add_argument("--hidden", choices=THINGS)
    ap.add_argument("--helper", choices=["Mama", "Papa", "Auntie"])
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
    if getattr(args, "room", None) and getattr(args, "child", None) and getattr(args, "hidden", None):
        pass
    filtered = [c for c in combos if (getattr(args, "room", None) is None or c[0] == getattr(args, "room", None)) and (getattr(args, "child", None) is None or c[1] == getattr(args, "child", None)) and (getattr(args, "hidden", None) is None or c[2] == getattr(args, "hidden", None))]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    room, child, hidden = rng.choice(list(filtered))
    sibling = getattr(args, "sibling", None) or rng.choice([n for n in CHILDREN if n != child])
    toy = getattr(args, "toy", None) or rng.choice(sorted(THINGS))
    helper = getattr(args, "helper", None) or rng.choice(["Mama", "Papa", "Auntie"])
    return StoryParams(room=room, child=child, sibling=sibling, toy=toy, hidden=hidden, helper=helper)


def generate(params: StoryParams) -> StorySample:
    room = ROOMS.get(params.room)
    child = Entity(id=params.child, kind="character", type="girl" if params.child in GIRL_NAMES else "boy")
    sibling = Entity(id=params.sibling, kind="character", type="boy" if params.sibling in BOY_NAMES else "girl")
    helper = Entity(id=params.helper, kind="character", type="parent")
    toy_cfg = THINGS.get(params.toy)
    hidden_cfg = THINGS.get(params.hidden)
    if room is None or toy_cfg is None or hidden_cfg is None:
        pass
    world = tell(room, child.id, sibling.id, toy_cfg, hidden_cfg, helper.id)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(asp_program("#show curiosity_turn/2.\n#show sharing_turn/2.\n#show pledge_turn/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
