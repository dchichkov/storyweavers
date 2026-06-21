#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/harmony_biology_paste_magic_quest_bedtime_story.py
===================================================================================

A tiny bedtime storyworld about a child who wants to make a magical quest
smoother, but learns that true harmony comes from careful, ordinary help.

Seed words: harmony, biology, paste
Features: Magic, Quest
Style: Bedtime Story

The domain is built around:
- a child preparing a bedtime quest with a glowing map
- a small biology project using paste
- a magical mismatch that can become a mess
- a calm grown-up or helper who guides the child to a safer, gentler solution
- a peaceful ending image that proves what changed

This script follows the Storyweavers contract:
- standalone stdlib Python
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily in ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Room:
    id: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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


@dataclass
class Quest:
    id: str
    scene: str
    goal: str
    trail: str
    ending_image: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class BiologyItem:
    id: str
    label: str
    phrase: str
    place: str
    messy: bool = False
    can_paste: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    glow: str
    safe: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.rooms: dict[str, Room] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_room(self, room: Room) -> Room:
        self.rooms[room.id] = room
        return room

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.rooms = copy.deepcopy(self.rooms)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


def _r_spill(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.meters["paste"] < THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.rooms["bedroom"].meters["mess"] += 1
        ent.memes["worry"] += 1
        out.append("__spill__")
    return out


def _r_harmony(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if not child or not helper:
        return out
    if child.memes["calm"] >= THRESHOLD and helper.memes["calm"] >= THRESHOLD:
        sig = ("harmony",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.rooms["bedroom"].meters["harmony"] += 1
            out.append("__harmony__")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill), Rule("harmony", _r_harmony)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def is_valid_combo(quest: Quest, item: BiologyItem, tool: MagicTool) -> bool:
    return item.can_paste and item.messy and tool.safe


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for quest_id, q in QUESTS.items():
        for bid, item in BIOLOGY.items():
            for mid, tool in MAGIC.items():
                if is_valid_combo(q, item, tool):
                    out.append((quest_id, bid, mid))
    return out


def _do_paste(world: World, item: Entity, narrate: bool = True) -> None:
    item.meters["paste"] += 1
    item.memes["pride"] += 1
    propagate(world, narrate=narrate)


def tell(quest: Quest, biology: BiologyItem, magic: MagicTool, fix: Fix,
         child_name: str = "Mila", child_gender: str = "girl",
         helper_name: str = "Nana", helper_gender: str = "woman",
         delay: int = 0, seed_note: str = "") -> World:
    world = World()
    child = world.add_entity(Entity(id="child", kind="character", type=child_gender, label=child_name, role="hero"))
    helper = world.add_entity(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="guide"))
    world.add_room(Room(id="bedroom", label="the bedroom"))
    specimen = world.add_entity(Entity(id="specimen", type="thing", label=biology.label, attrs={"place": biology.place}))
    wand = world.add_entity(Entity(id="wand", type="thing", label=magic.label))
    child.memes["wonder"] = 1.0
    helper.memes["calm"] = 1.0
    world.facts["seed_note"] = seed_note

    world.say(f"At bedtime, {child.label} tucked a tiny lantern beside the pillow and smiled at a small quest. {quest.scene}")
    world.say(f"{child.label} loved the soft magic of the room, and {helper.label} promised that the night could stay gentle.")

    world.para()
    world.say(f"There was a little biology project on the desk. {biology.phrase} waited beside a card with careful labels, and {child.label} wanted to use paste to hold everything neat.")
    child.memes["desire"] += 1
    world.say(f'"It will help the quest map stay in harmony," {child.label} whispered.')

    if biology.messy:
        child.meters["paste"] += 1

    world.para()
    world.say(f"But when the paste came out, it gleamed on the paper and began to slide toward the edge. That was the part that could make a sleepy mess.")
    if delay:
        world.rooms["bedroom"].meters["mess"] += float(delay)

    world.para()
    helper.memes["calm"] += 1
    if fix.power >= 1:
        world.say(f'{helper.label} knelt beside the desk. "{biology.label} can be part of the quest, but paste is for a little bit only," {helper.pronoun()} said softly.')
        world.say(f'Then {helper.label} showed a smaller, safer way: {fix.text}.')

    if fix.power >= 1:
        child.memes["calm"] += 1
        child.memes["joy"] += 1
        world.rooms["bedroom"].meters["mess"] = 0.0
        world.rooms["bedroom"].meters["harmony"] += 1
        world.say(f'{child.label} nodded, and together they made the page tidy again. The magic stayed warm instead of wild.')
        world.para()
        world.say(f"Before sleep, {child.label} set down the finished paper and listened to the quiet breathing in the room. {quest.ending_image}")
        world.say(f"The bedtime quest ended with harmony, biology, and paste all in their proper places.")
    else:
        world.say(f"The gentle fix was not enough, so the page stayed sticky and the bedroom felt less peaceful.")
        world.para()
        world.say(f"{child.label} and {helper.label} put the project aside and decided to finish it in the morning, when the room could be calm again.")

    world.facts.update(
        child=child,
        helper=helper,
        quest=quest,
        biology=biology,
        magic=magic,
        fix=fix,
        outcome="peaceful" if world.rooms["bedroom"].meters["mess"] == 0 else "sticky",
        noisemade=world.rooms["bedroom"].meters["mess"] > 0,
    )
    return world


QUESTS = {
    "lantern": Quest(
        id="lantern",
        scene="A tiny quest began with a paper moon, a folded map, and a promise to find the quietest path.",
        goal="the moon stone",
        trail="a ribbon of silver stars",
        ending_image="On the nightstand, the map lay flat, and the moon sticker shone like a little promise kept.",
    ),
    "garden": Quest(
        id="garden",
        scene="A garden quest waited in the dim room, where leaves on the blanket looked like secret trees.",
        goal="the sleeping seed",
        trail="a path of gold dust",
        ending_image="The seed picture rested beside the lamp, and the whole room felt soft and green.",
    ),
    "harbor": Quest(
        id="harbor",
        scene="A harbor quest drifted under the quilt, where the pillows became boats and the shadows became waves.",
        goal="the pearl shell",
        trail="a line of silver water",
        ending_image="The pearl shell card leaned safely against the books, bright enough to guide a dream.",
    ),
}

BIOLOGY = {
    "seed_card": BiologyItem("seed_card", "seed card", "a card with seeds drawn on it", "desk", messy=True, can_paste=True, tags={"biology"}),
    "leaf_sheet": BiologyItem("leaf_sheet", "leaf sheet", "a page with leaf shapes on it", "desk", messy=True, can_paste=True, tags={"biology"}),
    "bug_chart": BiologyItem("bug_chart", "bug chart", "a chart of little insects", "desk", messy=True, can_paste=True, tags={"biology"}),
}

MAGIC = {
    "moon_chalk": MagicTool("moon_chalk", "moon chalk", "a stick of moon chalk", "glowed like a firefly", safe=True, tags={"magic"}),
    "star_glass": MagicTool("star_glass", "star glass", "a star glass charm", "shone softly", safe=True, tags={"magic"}),
    "spark_ribbon": MagicTool("spark_ribbon", "spark ribbon", "a spark ribbon", "twinkled without heat", safe=True, tags={"magic"}),
}

FIXES = {
    "blot": Fix("blot", 3, 2, "blotted the extra paste with a soft cloth", "tried to tidy it, but the paste kept spreading"),
    "dry_sheet": Fix("dry_sheet", 2, 1, "slid a dry sheet under the page and waited for the paste to settle", "waited too long and the page was still sticky"),
    "tiny_dabs": Fix("tiny_dabs", 3, 2, "used just tiny dabs of paste, one careful dot at a time", "used too much paste again"),
}

CHILD_NAMES = ["Mila", "Nora", "Luna", "Iris", "Tessa", "Owen", "Arlo", "Theo"]
HELPER_NAMES = ["Nana", "Mama", "Papa", "Baba", "Auntie"]
TRAITS = ["curious", "gentle", "sleepy", "thoughtful", "careful"]


@dataclass
class StoryParams:
    quest: str
    biology: str
    magic: str
    fix: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    trait: str
    delay: int = 0
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


CURATED = [
    StoryParams(quest="lantern", biology="seed_card", magic="moon_chalk", fix="blot", child_name="Mila", child_gender="girl", helper_name="Nana", helper_gender="woman", trait="curious", delay=0),
    StoryParams(quest="garden", biology="leaf_sheet", magic="star_glass", fix="tiny_dabs", child_name="Owen", child_gender="boy", helper_name="Papa", helper_gender="man", trait="careful", delay=0),
    StoryParams(quest="harbor", biology="bug_chart", magic="spark_ribbon", fix="dry_sheet", child_name="Luna", child_gender="girl", helper_name="Mama", helper_gender="woman", trait="gentle", delay=1),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a young child that includes the words "harmony", "biology", and "paste", and features a small quest with magic.',
        f"Tell a gentle story where {f['child'].label} works on {f['biology'].label} beside a magical quest scene, and a grown-up helps keep the room peaceful.",
        f'Write a soothing bedtime story with a magical quest, a biology project, and paste used carefully so the room ends in harmony.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, quest, biology, fix = f["child"], f["helper"], f["quest"], f["biology"], f["fix"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.label} and {helper.label}, who share a quiet bedtime quest. The story stays small and gentle, like a lullaby."),
        ("What was the child doing with paste?",
         f"{child.label} was using paste on {biology.label} for a little biology project. The paste was meant to help, but too much would have made the page sticky."),
        ("How did the grown-up help?",
         f"{helper.label} showed a safer way by {fix.text}. That kept the project neat and helped the room stay peaceful."),
    ]
    if f["outcome"] == "peaceful":
        qa.append((
            "How did the story end?",
            f"It ended in harmony. {child.label} finished the page, the magic stayed soft, and the bedtime room felt calm again."
        ))
        qa.append((
            "Why did the child feel better at the end?",
            f"{child.label} felt better because the mess was fixed and the quest could continue quietly. The child learned that careful help makes even magic feel safe."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It ended with the project put aside for the morning. The page stayed sticky, so everyone chose rest and quiet instead of pushing ahead."
        ))
    return qa


WORLD_KNOWLEDGE = {
    "harmony": [("What is harmony?",
                 "Harmony is when different things fit together peacefully, like soft music that sounds nice instead of noisy.")],
    "biology": [("What is biology?",
                 "Biology is the study of living things, like plants, animals, and tiny creatures.")],
    "paste": [("What is paste used for?",
               "Paste helps paper pieces stick together. It can be messy if you use too much.")],
    "magic": [("What is magic in a story?",
              "Magic in a story is pretend wonder, like a glow or a spell that makes an adventure feel special.")],
    "quest": [("What is a quest?",
              "A quest is a journey or mission to find something, solve a problem, or reach a goal.")],
}
WORLD_ORDER = ["harmony", "biology", "paste", "magic", "quest"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set()
    f = world.facts
    tags |= set(f["biology"].tags)
    tags |= set(f["magic"].tags)
    tags.add("quest")
    tags.add("harmony")
    if "paste" in f["biology"].label:
        tags.add("paste")
    out = []
    for k in WORLD_ORDER:
        if k in tags and k in WORLD_KNOWLEDGE:
            out.extend(WORLD_KNOWLEDGE[k])
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
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    for r in world.rooms.values():
        meters = {k: v for k, v in r.meters.items() if v}
        lines.append(f"  {r.id:8} (room   ) meters={meters}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(bio: BiologyItem, magic: MagicTool) -> str:
    if not bio.can_paste:
        return f"(No story: {bio.label} does not naturally call for paste, so the clue is too weak.)"
    if not magic.safe:
        return f"(No story: {magic.label} is not a safe bedtime magic tool.)"
    return "(No story: this combination does not make a small, reasonable bedtime quest.)"


def valid_fix_ids() -> list[str]:
    return [f.id for f in sensible_fixes()]


def asp_facts() -> str:
    import asp
    lines = []
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for b in BIOLOGY:
        lines.append(asp.fact("biology", b))
    for m in MAGIC:
        lines.append(asp.fact("magic", m))
    for f in FIXES.values():
        lines.append(asp.fact("fix", f.id))
        lines.append(asp.fact("sense", f.id, f.sense))
        lines.append(asp.fact("power", f.id, f.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for b in BIOLOGY.values():
        if b.messy:
            lines.append(asp.fact("messy", b.id))
        if b.can_paste:
            lines.append(asp.fact("can_paste", b.id))
    for m in MAGIC.values():
        if m.safe:
            lines.append(asp.fact("safe_magic", m.id))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Q,B,M) :- quest(Q), biology(B), magic(M), can_paste(B), messy(B), safe_magic(M).
sensible(F) :- fix(F), sense(F,S), sense_min(M), S >= M.
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
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print("  only in asp:", sorted(a - p))
        print("  only in python:", sorted(p - a))
    if set(asp_sensible()) == set(valid_fix_ids()):
        print("OK: sensible fixes match.")
    else:
        rc = 1
        print("MISMATCH in fix ranking.")
    # smoke test ordinary generation
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story.strip()
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: harmony, biology, paste, magic, quest.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--biology", choices=BIOLOGY)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["woman", "man"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
              if (args.quest is None or c[0] == args.quest)
              and (args.biology is None or c[1] == args.biology)
              and (args.magic is None or c[2] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    if args.biology and args.biology not in BIOLOGY:
        raise StoryError("Unknown biology item.")
    if args.magic and args.magic not in MAGIC:
        raise StoryError("Unknown magic tool.")
    if args.fix and args.fix not in FIXES:
        raise StoryError("Unknown fix.")
    quest, biology, magic = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(valid_fix_ids())
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    trait = rng.choice(TRAITS)
    return StoryParams(quest=quest, biology=biology, magic=magic, fix=fix,
                       child_name=child_name, child_gender=child_gender,
                       helper_name=helper_name, helper_gender=helper_gender,
                       trait=trait, delay=delay)


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS or params.biology not in BIOLOGY or params.magic not in MAGIC or params.fix not in FIXES:
        raise StoryError("Invalid params.")
    world = tell(QUESTS[params.quest], BIOLOGY[params.biology], MAGIC[params.magic], FIXES[params.fix],
                 child_name=params.child_name, child_gender=params.child_gender,
                 helper_name=params.helper_name, helper_gender=params.helper_gender,
                 delay=params.delay, seed_note=str(params.seed or ""))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (quest, biology, magic) combos:\n")
        for q, b, m in combos:
            print(f"  {q:8} {b:12} {m}")
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
            header = f"### {p.child_name}: {p.quest} / {p.biology} / {p.magic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
