#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dissension_dome_flashback_folk_tale.py
=======================================================================

A small folk-tale storyworld about a village dome, a quarrel of voices, and a
flashback that explains how the people learned to mend a split before it grew.

Premise
-------
A child or young helper enters a village dome where music, chores, or a shared
meal is meant to happen. A small dissension begins over how to use the dome, and
an older helper remembers, in a flashback, an earlier time when a similar quarrel
nearly spoiled the day. The remembered lesson leads to a wise compromise, and the
village ends in peace with the dome used well.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- forward causal rules
- explicit reasonableness gate
- inline ASP twin
- generation prompts, story QA, world QA
- --verify smoke test, ASP parity, JSON, trace, and all the standard flags
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
SENSE_MIN = 2

SETTINGS = {
    "village": "the village square",
    "hill": "the hill path",
    "orchard": "the orchard lane",
}

DOME_TYPES = {
    "song_dome": {
        "label": "the dome",
        "phrase": "a round dome with painted beams",
        "use": "hold the village singing",
        "inside": "under the dome",
        "outside": "outside the dome",
    },
    "bell_dome": {
        "label": "the bell dome",
        "phrase": "a tall bell dome with a bright lantern inside",
        "use": "gather everyone for supper",
        "inside": "inside the dome",
        "outside": "beside the dome",
    },
    "grain_dome": {
        "label": "the grain dome",
        "phrase": "a warm grain dome with straw mats and a round roof",
        "use": "share the harvest bread",
        "inside": "in the dome",
        "outside": "at the door of the dome",
    },
}

DISSENSION_TYPES = {
    "drums": {
        "label": "the drumbeat",
        "phrase": "the drums should start first",
        "line": "the drums first",
        "effect": "the rhythm would drown out the singers",
        "topic": "drums",
    },
    "bread": {
        "label": "the bread",
        "phrase": "the bread should be cut before the song",
        "line": "the bread first",
        "effect": "the loaves would cool before sharing",
        "topic": "bread",
    },
    "lantern": {
        "label": "the lantern",
        "phrase": "the lantern should hang higher",
        "line": "the lantern higher",
        "effect": "the light would spread across the whole dome",
        "topic": "lantern",
    },
}

FOLK_COMPACTS = {
    "listen": {
        "sense": 3,
        "power": 3,
        "text": "listened to both sides, lifted a calm hand, and asked the two to speak one at a time",
        "fail": "tried to calm them, but the voices had already tangled too tightly",
        "qa": "listened to both sides and asked the two to speak one at a time",
    },
    "share": {
        "sense": 3,
        "power": 4,
        "text": "made a shared plan so each side got a turn, and tied the plan with a ribbon of promise",
        "fail": "made a shared plan, but the quarrel was too hot to settle",
        "qa": "made a shared plan so each side got a turn",
    },
    "song_leader": {
        "sense": 2,
        "power": 2,
        "text": "named a song leader and set a gentle beat for everyone to follow",
        "fail": "named a song leader, but the voices still rose over one another",
        "qa": "named a song leader and set a gentle beat",
    },
    "water_offering": {
        "sense": 1,
        "power": 1,
        "text": "offered water to cool the argument",
        "fail": "offered water to cool the argument, but that did not mend the quarrel",
        "qa": "offered water to cool the argument",
    },
}

GIRL_NAMES = ["Mara", "Anya", "Lina", "Tara", "Nina", "Sela", "Rosa"]
BOY_NAMES = ["Bram", "Oren", "Lio", "Pek", "Evan", "Milo", "Toma"]
ELDER_NAMES = ["Grandmother Iri", "Uncle Joss", "Aunt Bel", "Old Nera"]
TRAITS = ["thoughtful", "careful", "quiet", "bright", "patient", "brave"]

REASONABLE_COMPACTS = {"listen", "share", "song_leader"}

KNOWLEDGE = {
    "dome": [("What is a dome?",
              "A dome is a round roof or room shaped like the top half of a ball. "
              "It can make voices carry and sound rich.")],
    "dissension": [("What does dissension mean?",
                   "Dissension means a disagreement or split in opinion. "
                   "It is when people do not want the same thing.")],
    "flashback": [("What is a flashback in a story?",
                    "A flashback is when the story remembers something that happened before. "
                    "It helps explain why a character knows what to do.")],
    "voice": [("Why do voices sound different in a dome?",
                "A dome can bounce sound around, so voices may echo and carry farther.")],
    "listen": [("Why is listening helpful in a quarrel?",
                 "Listening helps people understand each other. "
                 "When each side feels heard, it is easier to find a fair plan.")],
    "share": [("Why do people take turns sharing?",
                "Taking turns keeps one person from taking everything. "
                "It helps a group stay peaceful and fair.")],
}

KNOWLEDGE_ORDER = ["dome", "dissension", "flashback", "voice", "listen", "share"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "uncle": "uncle",
            "aunt": "aunt",
        }.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    gathers: str
    echo: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Dome:
    id: str
    label: str
    phrase: str
    use: str
    inside: str
    outside: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Dissension:
    id: str
    label: str
    phrase: str
    line: str
    effect: str
    topic: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Compact:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_echo(world: World) -> list[str]:
    out = []
    dome = world.get("dome")
    if dome.meters["quarrel"] >= THRESHOLD and ("echo",) not in world.fired:
        world.fired.add(("echo",))
        for e in list(world.entities.values()):
            if e.role in {"child", "elder"}:
                e.memes["stress"] += 1
        dome.meters["echo"] += 1
        out.append("__echo__")
    return out


def _r_smooth(world: World) -> list[str]:
    out = []
    dome = world.get("dome")
    if dome.meters["peace"] >= THRESHOLD and ("smooth",) not in world.fired:
        world.fired.add(("smooth",))
        for e in list(world.entities.values()):
            if e.role in {"child", "elder"}:
                e.memes["relief"] += 1
        out.append("__smooth__")
    return out


CAUSAL_RULES = [Rule("echo", "sound", _r_echo), Rule("smooth", "social", _r_smooth)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_broadcast(dome: Dome, diss: Dissension) -> bool:
    return bool(dome.label and diss.topic)


def sensible_compacts() -> list[Compact]:
    return [Compact(k, v["sense"], v["power"], v["text"], v["fail"], v["qa"])
            for k, v in FOLK_COMPACTS.items() if v["sense"] >= SENSE_MIN]


def best_compact() -> Compact:
    return max((Compact(k, v["sense"], v["power"], v["text"], v["fail"], v["qa"])
                for k, v in FOLK_COMPACTS.items()), key=lambda c: c.sense)


def calm_needed(level: int) -> int:
    return level


def story_flashback(world: World, elder: Entity, child: Entity, dome: Dome, diss: Dissension) -> None:
    world.say(
        f"{elder.id} frowned at the rising dissension in the dome. "
        f'"This reminds me of an old day," {elder.id} said, and the words became a flashback.'
    )
    world.say(
        f"In that memory, the same {diss.label} had split the room, and nobody could hear {diss.line} "
        f"over the echoing roof."
    )
    elder.memes["memory"] += 1
    child.memes["curiosity"] += 1


def begin(world: World, child: Entity, elder: Entity, dome: Dome) -> None:
    child.memes["joy"] += 1
    elder.memes["duty"] += 1
    world.say(
        f"At {world.setting.place}, {child.id} and {elder.id} came to {dome.use} "
        f"inside {dome.label}. {dome.phrase}."
    )
    world.say(
        f"The round roof made every voice carry soft and long, like a song in a bowl of air."
    )


def dissension_rises(world: World, child: Entity, elder: Entity, diss: Dissension) -> None:
    child.memes["desire"] += 1
    world.say(
        f"{child.id} wanted {diss.phrase}, but another voice called for a different way. "
        f"Soon there was dissension, and the dome rang with two wishes at once."
    )
    world.get("dome").meters["quarrel"] += 1
    propagate(world, narrate=False)


def warn(world: World, elder: Entity, child: Entity, diss: Dissension) -> None:
    world.say(
        f"{elder.id} lifted a hand. \"If we let the dissension grow, {diss.effect},\" "
        f"{elder.pronoun()} said. \"We must listen before the roof turns every word into a louder word.\""
    )
    elder.memes["care"] += 1


def resolve(world: World, elder: Entity, child: Entity, compact: Compact, dome: Dome) -> None:
    world.get("dome").meters["peace"] += 1
    world.say(
        f"Then {elder.id} chose wisely: {compact.text}."
    )
    propagate(world, narrate=False)
    child.memes["joy"] += 1
    elder.memes["relief"] += 1
    world.say(
        f"The two sides nodded, and the dome grew quiet again. At last, the people could {dome.use} "
        f"without stepping on each other's hopes."
    )


def ending(world: World, child: Entity, elder: Entity, dome: Dome) -> None:
    world.say(
        f"By evening, the roof held only peaceful echoes. {child.id} smiled at {elder.id}, "
        f"and the dome shone like a friendly moon above the village."
    )


def tell(setting: Setting, dome: Dome, diss: Dissension, compact: Compact,
         child_name: str = "Mara", child_gender: str = "girl",
         elder_name: str = "Grandmother Iri", elder_type: str = "grandmother",
         child_role: str = "child") -> World:
    world = World(setting)
    child = world.add(Entity(child_name, kind="character", type=child_gender, role=child_role))
    elder = world.add(Entity(elder_name, kind="character", type=elder_type, role="elder"))
    dome_ent = world.add(Entity("dome", kind="thing", type="dome", label=dome.label))
    dome_ent.meters["peace"] = 0.0

    begin(world, child, elder, dome)
    world.para()
    dissension_rises(world, child, elder, diss)
    warn(world, elder, child, diss)
    world.para()
    story_flashback(world, elder, child, dome, diss)
    resolve(world, elder, child, compact, dome)
    world.para()
    ending(world, child, elder, dome)

    world.facts.update(
        child=child, elder=elder, dome=dome, diss=diss, compact=compact,
        setting=setting, peaceful=world.get("dome").meters["peace"] >= THRESHOLD,
        quarrel=world.get("dome").meters["quarrel"] >= THRESHOLD,
        flashed=True,
    )
    return world


SETTINGS_REG = {
    "village": Setting("village", SETTINGS["village"], "gather", "echoes"),
    "hill": Setting("hill", SETTINGS["hill"], "gather", "echoes"),
    "orchard": Setting("orchard", SETTINGS["orchard"], "gather", "echoes"),
}

DOMES = {
    k: Dome(k, v["label"], v["phrase"], v["use"], v["inside"], v["outside"])
    for k, v in DOME_TYPES.items()
}

DISSENSIONS = {
    k: Dissension(k, v["label"], v["phrase"], v["line"], v["effect"], v["topic"])
    for k, v in DISSENSION_TYPES.items()
}

COMPacts = {
    k: Compact(k, v["sense"], v["power"], v["text"], v["fail"], v["qa"])
    for k, v in FOLK_COMPACTS.items()
}

SAFE_COMPACTS = [k for k, v in FOLK_COMPACTS.items() if v["sense"] >= SENSE_MIN]

KNOWLEDGE_ORDER = KNOWLEDGE_ORDER


@dataclass
@dataclass
class StoryParams:
    setting: str
    dome: str
    dissension: str
    compact: str
    child: str
    child_gender: str
    elder: str
    elder_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS_REG:
        for d in DOMES:
            for x in DISSENSIONS:
                if can_broadcast(DOMES[d], DISSENSIONS[x]):
                    combos.append((s, d, x))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world about a dome, dissension, and a flashback.")
    ap.add_argument("--setting", choices=SETTINGS_REG)
    ap.add_argument("--dome", choices=DOMES)
    ap.add_argument("--dissension", choices=DISSENSIONS)
    ap.add_argument("--compact", choices=COMPacts)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather", "aunt", "uncle"])
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
    if args.compact and FOLK_COMPACTS[args.compact]["sense"] < SENSE_MIN:
        raise StoryError("That compromise is too weak for a folk-tale ending.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.dome is None or c[1] == args.dome)
              and (args.dissension is None or c[2] == args.dissension)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, dome, diss = rng.choice(sorted(combos))
    compact = args.compact or rng.choice(sorted(SAFE_COMPACTS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather", "aunt", "uncle"])
    elder = args.elder or rng.choice(ELDER_NAMES)
    return StoryParams(setting, dome, diss, compact, child, child_gender, elder, elder_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a small child that includes the word "dissension" and a dome.',
        f"Tell a gentle story about {f['child'].id} and {f['elder'].id} where a flashback helps settle a quarrel in the dome.",
        f"Write a short folk tale where dissension grows in the dome, then a wise elder remembers an older lesson and brings peace.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, elder, dome, diss, compact = f["child"], f["elder"], f["dome"], f["diss"], f["compact"]
    qa = [
        QAItem(
            question="What was the story about?",
            answer=f"It was about {child.id} and {elder.id} coming to {dome.label} and facing a little dissension. The elder used a flashback to remember an older lesson and help the room grow calm again."
        ),
        QAItem(
            question="Why did the dissension matter?",
            answer=f"It mattered because the dome carried sound, so every voice grew louder and harder to share. The quarrel could have drowned out the good work unless someone listened first."
        ),
        QAItem(
            question="What did the flashback do in the story?",
            answer=f"The flashback showed that this was not the first time the same kind of problem had happened. That memory helped {elder.id} choose {compact.qa}, which gave both sides a fair turn."
        ),
    ]
    if f.get("peaceful"):
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended peacefully. The dissension settled, the dome became quiet, and the people could {dome.use} with smiles instead of sharp words."
        ))
    return qa


def world_qa(world: World) -> list[QAItem]:
    tags = {"dome", "dissension", "flashback", "listen", "share"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(q, a))
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("village", "song_dome", "drums", "listen", "Mara", "girl", "Grandmother Iri", "grandmother"),
    StoryParams("hill", "bell_dome", "bread", "share", "Bram", "boy", "Uncle Joss", "uncle"),
    StoryParams("orchard", "grain_dome", "lantern", "song_leader", "Lina", "girl", "Aunt Bel", "aunt"),
]


def explain_rejection(compact: Compact) -> str:
    return f"(Refusing compact '{compact.id}': it is too weak/common-sense-poor for a folk-tale resolution.)"


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS_REG:
        lines.append(asp.fact("setting", s))
    for d in DOMES:
        lines.append(asp.fact("dome", d))
    for x, v in DISSENSIONS.items():
        lines.append(asp.fact("dissension", x))
        lines.append(asp.fact("topic", x, v.topic))
    for c, v in FOLK_COMPACTS.items():
        lines.append(asp.fact("compact", c))
        lines.append(asp.fact("sense", c, v["sense"]))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, D, X) :- setting(S), dome(D), dissension(X).
sensible(C) :- compact(C), sense(C, S), sense_min(M), S >= M.
outcome(peaceful) :- sensible(C).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos.")
    if set(asp_sensible()) == {k for k, v in FOLK_COMPACTS.items() if v["sense"] >= SENSE_MIN}:
        print("OK: sensible compacts match.")
    else:
        rc = 1
        print("MISMATCH in sensible compacts.")
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: sample story empty.")
    else:
        print("OK: smoke story generated.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS_REG[params.setting],
        DOMES[params.dome],
        DISSENSIONS[params.dissension],
        COMPacts[params.compact],
        params.child,
        params.child_gender,
        params.elder,
        params.elder_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible compacts: {', '.join(asp_sensible())}\n")
        for s, d, x in asp_valid_combos():
            print(f"  {s:8} {d:10} {x}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} at {p.dome} ({p.dissension}, {p.compact})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
