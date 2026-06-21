#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bip_advance_scour_moral_value_surprise_rhyming.py
=============================================================================

A standalone storyworld for a tiny rhyming tale about **Bip**, a small beeping
helper who wants to advance to the front of a moon parade, but pauses to scour
for a lost parade item instead. The moral value is simple and state-driven:
kindness matters more than hurrying for a prize. The surprise is earned from the
world state: the grateful owner invites Bip and a friend to lead the parade and
shares a gift linked to the recovered item.

Run it
------
    python storyworlds/worlds/gpt-5.4/bip_advance_scour_moral_value_surprise_rhyming.py
    python storyworlds/worlds/gpt-5.4/bip_advance_scour_moral_value_surprise_rhyming.py --item bell --hideout drain_grate --aid magnet_wand
    python storyworlds/worlds/gpt_5.4/bip_advance_scour_moral_value_surprise_rhyming.py --item ribbon --aid magnet_wand
    python storyworlds/worlds/gpt-5.4/bip_advance_scour_moral_value_surprise_rhyming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/bip_advance_scour_moral_value_surprise_rhyming.py --all
    python storyworlds/worlds/gpt-5.4/bip_advance_scour_moral_value_surprise_rhyming.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "hen", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain configs
# ---------------------------------------------------------------------------
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    path_text: str
    hideouts: set[str] = field(default_factory=set)
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


@dataclass
class LostItem:
    id: str
    label: str
    phrase: str
    owner_name: str
    owner_type: str
    owner_role: str
    need_text: str
    surprise_text: str
    rhyme_image: str
    jingles: bool = False
    shiny: bool = False
    soft: bool = False
    metal: bool = False
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
class Hideout:
    id: str
    label: str
    phrase: str
    search_verb: str
    dark: bool = False
    narrow: bool = False
    soft: bool = False
    open: bool = False
    allows: set[str] = field(default_factory=set)
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
class Aid:
    id: str
    label: str
    phrase: str
    action_text: str
    finds_metal: bool = False
    finds_sound: bool = False
    finds_shine: bool = False
    finds_soft: bool = False
    reaches_narrow: bool = False
    works_in_dark: bool = False
    works_open: bool = False
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


class World:
    def __init__(self) -> None:
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


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def item_fits_hideout(item: LostItem, hideout: Hideout) -> bool:
    return item.id in hideout.allows


def aid_matches(aid: Aid, item: LostItem, hideout: Hideout) -> bool:
    possible = False
    if item.metal and aid.finds_metal:
        possible = True
    if item.jingles and aid.finds_sound:
        possible = True
    if item.shiny and aid.finds_shine:
        possible = True
    if item.soft and aid.finds_soft:
        possible = True
    if hideout.narrow and not aid.reaches_narrow:
        return False
    if hideout.dark and not aid.works_in_dark:
        return False
    if hideout.open and not (aid.works_open or aid.finds_sound or aid.finds_shine or aid.finds_soft):
        return False
    return possible


def valid_combo(place_id: str, item_id: str, hideout_id: str, aid_id: str) -> bool:
    place = PLACES[place_id]
    item = ITEMS[item_id]
    hideout = HIDEOUTS[hideout_id]
    aid = AIDS[aid_id]
    if hideout.id not in place.hideouts:
        return False
    if not item_fits_hideout(item, hideout):
        return False
    if not aid_matches(aid, item, hideout):
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in sorted(PLACES):
        for item_id in sorted(ITEMS):
            for hideout_id in sorted(HIDEOUTS):
                for aid_id in sorted(AIDS):
                    if valid_combo(place_id, item_id, hideout_id, aid_id):
                        combos.append((place_id, item_id, hideout_id, aid_id))
    return combos


def surprise_kind(item_id: str) -> str:
    return {
        "bell": "bell_gift",
        "ribbon": "ribbon_gift",
        "star_charm": "star_gift",
    }[item_id]


def explain_rejection(place_id: str, item_id: str, hideout_id: str, aid_id: str) -> str:
    place = PLACES[place_id]
    item = ITEMS[item_id]
    hideout = HIDEOUTS[hideout_id]
    aid = AIDS[aid_id]
    if hideout.id not in place.hideouts:
        return (
            f"(No story: {hideout.phrase} is not part of {place.label}, "
            f"so there is nowhere honest to scour there.)"
        )
    if not item_fits_hideout(item, hideout):
        return (
            f"(No story: {item.phrase} does not reasonably belong in {hideout.phrase}. "
            f"Pick a hideout that could truly hide that item.)"
        )
    if hideout.narrow and not aid.reaches_narrow:
        return (
            f"(No story: {aid.label} cannot reach into {hideout.phrase}. "
            f"A narrow hiding place needs a tool that can reach in.)"
        )
    if hideout.dark and not aid.works_in_dark:
        return (
            f"(No story: {hideout.phrase} is too dark for {aid.label}. "
            f"Choose a search aid that can work in the dark.)"
        )
    return (
        f"(No story: {aid.label} is not a sensible way to find {item.phrase} in "
        f"{hideout.phrase}. Choose an aid that matches the item's sound, shine, "
        f"softness, or metal.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def introduce(world: World, bip: Entity, friend: Entity, place: Place) -> None:
    bip.memes["joy"] += 1
    friend.memes["joy"] += 1
    bip.memes["hurry"] += 1
    friend.memes["hurry"] += 1
    world.say(
        f"On moon-bright stones by {place.label}, went little {bip.id} with a cheerful sway. "
        f'"bip, bip," went {bip.id}, so trim and bright, as {friend.id} skipped beside in silver light.'
    )
    world.say(
        f"They hoped to advance to the front that night, where lanterns bobbed in a pearly line of light."
    )


def trouble(world: World, owner: Entity, item: LostItem, hideout: Hideout, place: Place) -> None:
    owner.memes["worry"] += 1
    world.say(
        f"But near {place.path_text}, they heard a sigh. {owner.id} blinked and looked nearby. "
        f'"Oh dear," said {owner.id}, "I cannot start till {item.need_text}.'
    )
    world.say(
        f"My {item.label} slipped away from sight and hid itself in {hideout.phrase} tonight."
    )


def choice(world: World, bip: Entity, friend: Entity) -> None:
    world.say(
        f"{friend.id} looked up at the marching band. {bip.id} could almost take the leading stand. "
        f"For one quick beat they thought, \"Advance! advance!\" while moonbeams made the tin wheels dance."
    )
    world.say(
        f"Then kindness nudged more strong than pride, and {bip.id} rolled softly to {friend.id}'s side."
    )
    bip.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    bip.memes["hurry"] = 0.0
    friend.memes["hurry"] = 0.0


def scour(world: World, bip: Entity, friend: Entity, item_ent: Entity,
          hideout: Hideout, aid: Aid) -> None:
    world.say(
        f'"We will scour {hideout.phrase}," said {friend.id} with care. '
        f'{bip.id} gave a happy "bip" and zipped right there.'
    )
    world.say(
        f"With {aid.phrase}, they {aid.action_text} by and by, while stars hung still in the velvet sky."
    )
    item_ent.meters["found"] += 1
    item_ent.meters["hidden"] = 0.0
    bip.memes["hope"] += 1
    friend.memes["hope"] += 1


def recover(world: World, bip: Entity, friend: Entity, owner: Entity,
            item_ent: Entity, item: LostItem, hideout: Hideout) -> None:
    owner.memes["worry"] = 0.0
    owner.memes["relief"] += 1
    owner.memes["joy"] += 1
    bip.memes["joy"] += 1
    friend.memes["joy"] += 1
    bip.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    world.say(
        f"At last from {hideout.phrase} came proof and spark: they found the {item.label}, snug but dark. "
        f"{item.rhyme_image}"
    )
    world.say(
        f"{owner.id} clasped it close with shining eyes. "
        f'"You helped before your own big prize. That is the finest way to be; kind hearts make room for all," said {owner.id} with glee.'
    )


def surprise(world: World, bip: Entity, friend: Entity, owner: Entity,
             item: LostItem) -> None:
    bip.memes["surprise"] += 1
    friend.memes["surprise"] += 1
    bip.meters["front_spot"] += 1
    friend.meters["front_spot"] += 1
    world.say(
        f"Then came the surprise beneath the moonlit skies: "
        f'{owner.id} laughed and said, "{item.surprise_text}"'
    )
    world.say(
        f"So {bip.id} and {friend.id} did not just watch the light. "
        f"They led the line through gentle night, and every step rang warm and right."
    )


def ending(world: World, bip: Entity, friend: Entity, item: LostItem) -> None:
    gift = {
        "bell": f"A tiny bell rode on {bip.id}'s blue bow, and every brave step made music glow.",
        "ribbon": f"A moon-pale ribbon streamed behind, with tails that twirled like threads of wind.",
        "star_charm": f"A little star charm shone on {bip.id}'s chest, and its mild gold light looked kindest, best.",
    }[item.id]
    world.say(
        f"{gift} {friend.id} grinned wide, and {bip.id} sang one last bright "  # noqa: ISC003
        f'"bip"—for helping first had made the night more bright.'
    )
@dataclass
class StoryParams:
    place: str
    item: str
    hideout: str
    aid: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
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


KNOWLEDGE = {
    "bell": [
        ("What is a bell?",
         "A bell is a hollow metal object that rings when it shakes or gets tapped. Small bells make a bright jingling sound."),
    ],
    "music": [
        ("Why would a parade use a bell?",
         "A bell can help start the music and keep people together. Its clear sound is easy to hear over happy marching feet."),
    ],
    "ribbon": [
        ("What is a ribbon?",
         "A ribbon is a long strip of soft cloth. People use ribbons to tie things, decorate, or mark a special place."),
    ],
    "cloth": [
        ("Why can cloth hide in leaves or flowers?",
         "Soft cloth can slip between stems and leaves without making much noise. That makes it easy to miss until someone looks carefully."),
    ],
    "star": [
        ("What is a star charm?",
         "A star charm is a tiny star-shaped decoration, often made of metal. People clip it onto something to make it look bright and special."),
    ],
    "lantern": [
        ("What does a lantern do?",
         "A lantern gives light when it is dark. It helps people see and can make a parade glow warmly at night."),
    ],
    "magnet": [
        ("What does a magnet do?",
         "A magnet can pull some kinds of metal toward it without fingers touching them. That can help with small metal things in hard places."),
    ],
    "listening": [
        ("Why can listening help you find something?",
         "Some lost things make a sound when they move, like a bell giving a tiny tinkle. Quiet listening can tell you where to look next."),
    ],
    "hands": [
        ("Why should you use gentle hands when searching?",
         "Gentle hands help you move leaves or cloth without tearing or crushing them. Careful searching keeps the place tidy and the lost thing safe."),
    ],
    "parade": [
        ("What is a parade?",
         "A parade is a group of people who move together in a happy line, often with music, lights, or costumes. People watch and celebrate as it passes by."),
    ],
    "kindness": [
        ("Why is helping someone kind?",
         "Helping means you stop thinking only about yourself and make room for another person's problem. Kindness can turn someone else's worry into relief and joy."),
    ],
}
KNOWLEDGE_ORDER = [
    "bell", "music", "ribbon", "cloth", "star", "lantern",
    "magnet", "listening", "hands", "parade", "kindness",
]


def generation_prompts(world: World) -> list[str]:
    item = world.facts["item_cfg"]
    place = world.facts["place"]
    friend = world.facts["friend"]
    aid = world.facts["aid"]
    return [
        f'Write a rhyming story for a 3-to-5-year-old about Bip, who wants to advance to the front of a parade but stops to scour for {item.phrase} at {place.label}. Include the word "bip".',
        f"Tell a gentle moral tale in rhyme where Bip and {friend.id} choose kindness over hurrying, use {aid.label}, and discover a happy surprise at the end.",
        f'Write a moonlit rhyming story that includes the words "bip", "advance", and "scour", and ends by showing that helping first can bring an unexpected reward.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    bip = world.facts["bip"]
    friend = world.facts["friend"]
    owner = world.facts["owner"]
    item = world.facts["item_cfg"]
    hideout = world.facts["hideout"]
    aid = world.facts["aid"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {bip.id}, a little beeping helper, and {friend.id}, who were hurrying to a moon parade. They met {owner.id}, who had lost {item.phrase}.",
        ),
        (
            f"Why did Bip and {friend.id} stop instead of trying to advance to the front right away?",
            f"They stopped because {owner.id} could not begin the parade without the lost {item.label}. Bip and {friend.id} chose kindness over rushing ahead for their own place.",
        ),
        (
            f"Where did they scour, and how did they search?",
            f"They scoured {hideout.phrase}. They used {aid.phrase}, because that was a sensible way to find the missing {item.label} there.",
        ),
        (
            f"What happened when they found the {item.label}?",
            f"{owner.id}'s worry changed into relief and joy as soon as the {item.label} was found. Because Bip and {friend.id} helped first, {owner.id} rewarded them with the front place in the parade.",
        ),
        (
            "What is the surprise at the end?",
            f"The surprise is that helping did not make them miss the best part. It is exactly what earned them the chance to lead the parade together.",
        ),
        (
            "What lesson does the story teach?",
            "The story teaches that helping someone else matters more than hurrying for your own turn. Kind choices can come back as bright surprises later.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["item_cfg"].tags) | set(world.facts["place"].tags) | {"kindness", "parade"}
    aid = world.facts["aid"]
    if "magnet" in aid.tags:
        tags.add("magnet")
    if "listening" in aid.tags:
        tags.add("listening")
    if "hands" in aid.tags:
        tags.add("hands")
    if "lantern" in aid.tags:
        tags.add("lantern")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  facts: surprise_kind={world.facts.get('surprise_kind')} moral={world.facts.get('moral')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(P,I,H,A) :- place(P), item(I), hideout(H), aid(A),
                  has_hideout(P,H), allows(H,I), aid_fits(A,I,H).

aid_fits(A,I,H) :- finds_metal(A), metal(I), hideout(H), not blocked_narrow(A,H), not blocked_dark(A,H), open_ok(A,H).
aid_fits(A,I,H) :- finds_sound(A), jingles(I), hideout(H), not blocked_narrow(A,H), not blocked_dark(A,H), open_ok(A,H).
aid_fits(A,I,H) :- finds_shine(A), shiny(I), hideout(H), not blocked_narrow(A,H), not blocked_dark(A,H), open_ok(A,H).
aid_fits(A,I,H) :- finds_soft(A), soft(I), hideout(H), not blocked_narrow(A,H), not blocked_dark(A,H), open_ok(A,H).

blocked_narrow(A,H) :- narrow(H), not reaches_narrow(A).
blocked_dark(A,H)   :- dark(H), not works_in_dark(A).

open_ok(A,H) :- not open(H).
open_ok(A,H) :- open(H), works_open(A).
open_ok(A,H) :- open(H), finds_sound(A).
open_ok(A,H) :- open(H), finds_shine(A).
open_ok(A,H) :- open(H), finds_soft(A).

surprise(I,bell_gift) :- item(I), I = bell.
surprise(I,ribbon_gift) :- item(I), I = ribbon.
surprise(I,star_gift) :- item(I), I = star_charm.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for hideout_id in sorted(place.hideouts):
            lines.append(asp.fact("has_hideout", place_id, hideout_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.jingles:
            lines.append(asp.fact("jingles", item_id))
        if item.shiny:
            lines.append(asp.fact("shiny", item_id))
        if item.soft:
            lines.append(asp.fact("soft", item_id))
        if item.metal:
            lines.append(asp.fact("metal", item_id))
    for hideout_id, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hideout_id))
        if hideout.dark:
            lines.append(asp.fact("dark", hideout_id))
        if hideout.narrow:
            lines.append(asp.fact("narrow", hideout_id))
        if hideout.open:
            lines.append(asp.fact("open", hideout_id))
        for item_id in sorted(hideout.allows):
            lines.append(asp.fact("allows", hideout_id, item_id))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        if aid.finds_metal:
            lines.append(asp.fact("finds_metal", aid_id))
        if aid.finds_sound:
            lines.append(asp.fact("finds_sound", aid_id))
        if aid.finds_shine:
            lines.append(asp.fact("finds_shine", aid_id))
        if aid.finds_soft:
            lines.append(asp.fact("finds_soft", aid_id))
        if aid.reaches_narrow:
            lines.append(asp.fact("reaches_narrow", aid_id))
        if aid.works_in_dark:
            lines.append(asp.fact("works_in_dark", aid_id))
        if aid.works_open:
            lines.append(asp.fact("works_open", aid_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_surprise(item_id: str) -> str:
    import asp

    extra = f"chosen_item({item_id}).\nwhich(S) :- chosen_item(I), surprise(I,S)."
    model = asp.one_model(asp_program(extra, "#show which/1."))
    found = asp.atoms(model, "which")
    return found[0][0] if found else "?"


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming storyworld: Bip pauses before a parade to help find a lost item."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--friend")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_friend(rng: random.Random, friend_type: Optional[str], explicit: Optional[str]) -> tuple[str, str]:
    ftype = friend_type or rng.choice(["girl", "boy"])
    if explicit:
        return explicit, ftype
    if ftype == "girl":
        return rng.choice(GIRL_NAMES), "girl"
    return rng.choice(BOY_NAMES), "boy"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.hideout and args.aid:
        if not valid_combo(args.place, args.item, args.hideout, args.aid):
            raise StoryError(explain_rejection(args.place, args.item, args.hideout, args.aid))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.hideout is None or combo[2] == args.hideout)
        and (args.aid is None or combo[3] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, hideout_id, aid_id = rng.choice(sorted(combos))
    friend_name, friend_type = pick_friend(rng, args.friend_type, args.friend)
    return StoryParams(
        place=place_id,
        item=item_id,
        hideout=hideout_id,
        aid=aid_id,
        friend_name=friend_name,
        friend_type=friend_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.item not in ITEMS or params.hideout not in HIDEOUTS or params.aid not in AIDS:
        raise StoryError("(Invalid params: unknown registry key.)")
    if not valid_combo(params.place, params.item, params.hideout, params.aid):
        raise StoryError(explain_rejection(params.place, params.item, params.hideout, params.aid))
    world = tell(
        place=PLACES[params.place],
        item=ITEMS[params.item],
        hideout=HIDEOUTS[params.hideout],
        aid=AIDS[params.aid],
        friend_name=params.friend_name,
        friend_type=params.friend_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
    StoryParams(
        place="lantern_lane",
        item="bell",
        hideout="drain_grate",
        aid="magnet_wand",
        friend_name="Nia",
        friend_type="girl",
    ),
    StoryParams(
        place="garden_green",
        item="ribbon",
        hideout="flower_patch",
        aid="gentle_fingers",
        friend_name="Milo",
        friend_type="boy",
    ),
    StoryParams(
        place="harbor_walk",
        item="star_charm",
        hideout="crate_corner",
        aid="lantern_glow",
        friend_name="Ivy",
        friend_type="girl",
    ),
    StoryParams(
        place="garden_green",
        item="bell",
        hideout="flower_patch",
        aid="listening_pause",
        friend_name="Leo",
        friend_type="boy",
    ),
]


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    apy = set(asp_valid_combos())
    if py == apy:
        print(f"OK: valid combos match ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - apy:
            print("  only in python:", sorted(py - apy))
        if apy - py:
            print("  only in clingo:", sorted(apy - py))

    for item_id in sorted(ITEMS):
        py_surprise = surprise_kind(item_id)
        asp_s = asp_surprise(item_id)
        if py_surprise != asp_s:
            rc = 1
            print(f"MISMATCH in surprise for {item_id}: python={py_surprise} clingo={asp_s}")
    if rc == 0:
        print("OK: surprise mapping matches.")

    smoke_cases = list(CURATED)
    try:
        smoke_cases.append(resolve_params(build_parser().parse_args([]), random.Random(0)))
    except StoryError as err:
        rc = 1
        print(f"FAILED: default resolve_params crashed: {err}")
    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if idx == 1:
                emit(sample, trace=False, qa=False)
        except Exception as err:  # pragma: no cover - verify path
            rc = 1
            print(f"FAILED: smoke generation crashed for case {idx}: {err}")
            break
    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} story generations.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show surprise/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, hideout, aid) combos:\n")
        for place_id, item_id, hideout_id, aid_id in combos:
            print(f"  {place_id:12} {item_id:10} {hideout_id:12} {aid_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.item} at {p.place} via {p.hideout} with {p.aid}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(place: Place, item: LostItem, hideout: Hideout, aid: Aid,
         friend_name: str = "Nia", friend_type: str = "girl") -> World:
    world = World()
    bip = world.add(Entity(id="Bip", kind="character", type="robot", role="helper",
                           label="little Bip", attrs={"sound": "bip"}))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type,
                              role="friend", label=friend_name))
    owner = world.add(Entity(id=item.owner_name, kind="character", type=item.owner_type,
                             role="owner", label=item.owner_name,
                             attrs={"job": item.owner_role}))
    item_ent = world.add(Entity(id="item", kind="thing", type="parade_item",
                                label=item.label, attrs={"item_id": item.id}))
    item_ent.meters["hidden"] = 1.0
    item_ent.meters["found"] = 0.0
    bip.memes["kindness"] = 0.0
    friend.memes["kindness"] = 0.0
    owner.memes["worry"] = 0.0
    owner.memes["joy"] = 0.0
    world.facts.update(
        place=place,
        item_cfg=item,
        hideout=hideout,
        aid=aid,
        bip=bip,
        friend=friend,
        owner=owner,
        item=item_ent,
        surprise_kind=surprise_kind(item.id),
    )

    introduce(world, bip, friend, place)
    world.para()
    trouble(world, owner, item, hideout, place)
    choice(world, bip, friend)
    world.para()
    scour(world, bip, friend, item_ent, hideout, aid)
    recover(world, bip, friend, owner, item_ent, item, hideout)
    world.para()
    surprise(world, bip, friend, owner, item)
    ending(world, bip, friend, item)

    world.facts.update(
        found=item_ent.meters["found"] >= THRESHOLD,
        led_parade=bip.meters["front_spot"] >= THRESHOLD,
        moral="help_before_hurry",
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "lantern_lane": Place(
        id="lantern_lane",
        label="Lantern Lane",
        path_text="the string of paper moons",
        hideouts={"bench_shadow", "drain_grate"},
        tags={"parade", "street"},
    ),
    "garden_green": Place(
        id="garden_green",
        label="Garden Green",
        path_text="the hedge of sleepy roses",
        hideouts={"flower_patch", "bench_shadow"},
        tags={"garden"},
    ),
    "harbor_walk": Place(
        id="harbor_walk",
        label="Harbor Walk",
        path_text="the rope posts by the water",
        hideouts={"drain_grate", "crate_corner"},
        tags={"harbor"},
    ),
}

ITEMS = {
    "bell": LostItem(
        id="bell",
        label="bell",
        phrase="a silver bell",
        owner_name="Mara",
        owner_type="woman",
        owner_role="band leader",
        need_text="I find my bell, for the parade song waits",
        surprise_text="Take the first place in the parade, and let this little bell on Bip's blue bow be laid!",
        rhyme_image="It gave a tiny ting from under a leaf, like a shy small laugh after a moment of grief.",
        jingles=True,
        metal=True,
        tags={"bell", "music"},
    ),
    "ribbon": LostItem(
        id="ribbon",
        label="ribbon",
        phrase="a satin ribbon",
        owner_name="Tavi",
        owner_type="boy",
        owner_role="banner bearer",
        need_text="I find my ribbon, for the moon banner droops and waits",
        surprise_text="Come lead with me at the very front, and wear this moon-pale ribbon while the lanterns hunt!",
        rhyme_image="It slid from the dim place soft and slow, like a strip of dawn in a hidden glow.",
        soft=True,
        tags={"ribbon", "cloth"},
    ),
    "star_charm": LostItem(
        id="star_charm",
        label="star charm",
        phrase="a brass star charm",
        owner_name="Aunt Suri",
        owner_type="aunt",
        owner_role="lantern keeper",
        need_text="I find my star charm, for the tallest lantern still waits",
        surprise_text="Lead the parade tonight, my dears, and let this star shine close instead of hiding in fears!",
        rhyme_image="A gold point winked where the shadows were warm, a pocket of night had been hiding a star charm.",
        shiny=True,
        metal=True,
        tags={"star", "lantern"},
    ),
}

HIDEOUTS = {
    "bench_shadow": Hideout(
        id="bench_shadow",
        label="bench shadow",
        phrase="the bench shadow",
        search_verb="peer beneath",
        dark=True,
        open=True,
        allows={"bell", "ribbon", "star_charm"},
        tags={"shadow"},
    ),
    "drain_grate": Hideout(
        id="drain_grate",
        label="drain grate",
        phrase="the narrow drain grate",
        search_verb="reach into",
        dark=True,
        narrow=True,
        allows={"bell", "star_charm"},
        tags={"drain"},
    ),
    "flower_patch": Hideout(
        id="flower_patch",
        label="flower patch",
        phrase="the flower patch",
        search_verb="part through",
        soft=True,
        open=True,
        allows={"bell", "ribbon"},
        tags={"flowers"},
    ),
    "crate_corner": Hideout(
        id="crate_corner",
        label="crate corner",
        phrase="the crate corner",
        search_verb="look behind",
        dark=False,
        open=True,
        allows={"ribbon", "star_charm"},
        tags={"crate"},
    ),
}

AIDS = {
    "magnet_wand": Aid(
        id="magnet_wand",
        label="magnet wand",
        phrase="a magnet wand",
        action_text="swept low and slow",
        finds_metal=True,
        reaches_narrow=True,
        works_in_dark=True,
        works_open=True,
        tags={"magnet"},
    ),
    "lantern_glow": Aid(
        id="lantern_glow",
        label="lantern glow",
        phrase="a little lantern glow",
        action_text="cast a warm ring of light",
        finds_shine=True,
        works_in_dark=True,
        works_open=True,
        tags={"lantern"},
    ),
    "listening_pause": Aid(
        id="listening_pause",
        label="listening pause",
        phrase="a listening pause and very still ears",
        action_text="waited for the tiniest tinkle",
        finds_sound=True,
        works_in_dark=True,
        works_open=True,
        tags={"listening"},
    ),
    "gentle_fingers": Aid(
        id="gentle_fingers",
        label="gentle fingers",
        phrase="gentle fingers and patient hands",
        action_text="lifted leaves and cloth with care",
        finds_soft=True,
        works_open=True,
        tags={"hands"},
    ),
}

GIRL_NAMES = ["Nia", "Lila", "June", "Mina", "Tess", "Ivy"]
BOY_NAMES = ["Oren", "Pip", "Milo", "Finn", "Tavi", "Leo"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
