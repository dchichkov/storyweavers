#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/conjunction_curt_sycamore_inner_monologue_nursery_rhyme.py
======================================================================================

A standalone storyworld for a tiny nursery-rhyme-like domain:

A child and a playmate try to sing a two-part rhyme under a sycamore tree.
When the lead child answers in a curt way, the duet falls apart. A gentle grown-up
shows that a conjunction can join not only two lines of verse, but also two
children who want to sing together. The protagonist's inner monologue appears
throughout in short child-facing thoughts.

The world model tracks both physical meters (cards joined, rhythm broken, hands
shared) and emotional memes (pride, hurt, shame, relief, joy). State drives the
turn and ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/conjunction_curt_sycamore_inner_monologue_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/conjunction_curt_sycamore_inner_monologue_nursery_rhyme.py --link and --prop bell
    python storyworlds/worlds/gpt-5.4/conjunction_curt_sycamore_inner_monologue_nursery_rhyme.py --prop stone
    python storyworlds/worlds/gpt-5.4/conjunction_curt_sycamore_inner_monologue_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/conjunction_curt_sycamore_inner_monologue_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/conjunction_curt_sycamore_inner_monologue_nursery_rhyme.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    steady: bool = False
    joins_lines: bool = False
    keeps_beat: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )
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
class Setting:
    id: str
    place: str
    breeze: str
    ground: str
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
class LinkWord:
    id: str
    word: str
    meaning: str
    turn_text: str
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
class Prop:
    id: str
    label: str
    phrase: str
    rhythm_text: str
    sense: int
    steady: bool
    keeps_beat: bool
    joins_lines: bool
    success_text: str
    qa_text: str
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
class Mood:
    id: str
    adjective: str
    reply: str
    soft_fix: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"lead", "friend"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
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


def _r_hurt_breaks_duet(world: World) -> list[str]:
    out: list[str] = []
    lead = world.get("lead")
    friend = world.get("friend")
    cards = world.get("cards")
    if lead.memes["curtness"] >= THRESHOLD and friend.memes["hurt"] >= THRESHOLD:
        sig = ("duet_break",)
        if sig not in world.fired:
            world.fired.add(sig)
            cards.meters["unjoined"] += 1
            cards.meters["rhythm_lost"] += 1
            world.get("song").meters["broken"] += 1
            out.append("__break__")
    return out


def _r_shared_singing_restores(world: World) -> list[str]:
    out: list[str] = []
    lead = world.get("lead")
    friend = world.get("friend")
    cards = world.get("cards")
    prop = world.get("prop")
    song = world.get("song")
    if (
        cards.meters["joined"] >= THRESHOLD
        and prop.meters["ready"] >= THRESHOLD
        and lead.memes["kindness"] >= THRESHOLD
        and friend.memes["trust"] >= THRESHOLD
    ):
        sig = ("restored",)
        if sig not in world.fired:
            world.fired.add(sig)
            song.meters["steady"] += 1
            song.meters["broken"] = 0.0
            lead.memes["relief"] += 1
            friend.memes["relief"] += 1
            out.append("__restored__")
    return out


CAUSAL_RULES = [
    Rule(name="hurt_breaks_duet", tag="social", apply=_r_hurt_breaks_duet),
    Rule(name="shared_singing_restores", tag="social", apply=_r_shared_singing_restores),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prop_is_sensible(prop: Prop) -> bool:
    return prop.sense >= SENSE_MIN and prop.joins_lines and prop.keeps_beat and prop.steady


def valid_story(setting: Setting, prop: Prop) -> bool:
    return "sycamore" in setting.tags and prop_is_sensible(prop)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for lid in LINKS:
            for mid in MOODS:
                for pid, prop in PROPS.items():
                    if valid_story(setting, prop):
                        combos.append((sid, lid, mid, pid))
    return combos


def predict_break(world: World) -> dict:
    sim = world.copy()
    lead = sim.get("lead")
    friend = sim.get("friend")
    lead.memes["curtness"] += 1
    friend.memes["hurt"] += 1
    propagate(sim, narrate=False)
    return {
        "broken": sim.get("song").meters["broken"] >= THRESHOLD,
        "cards_unjoined": sim.get("cards").meters["unjoined"],
    }


def inner(world: World, lead: Entity, text: str) -> None:
    world.say(f'{lead.id} thought, "{text}"')


def opening(world: World, lead: Entity, friend: Entity, setting: Setting, prop: Prop) -> None:
    lead.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Under the sycamore at {setting.place}, {lead.id} and {friend.id} came to play. "
        f"{setting.breeze} {setting.ground}"
    )
    world.say(
        f"{lead.id} held two rhyme cards and {prop.phrase}. "
        f'The morning seemed to sing, "{prop.rhythm_text}"'
    )
    inner(world, lead, "If our two little lines can dance as one, our song will skip along just right.")


def invite(world: World, lead: Entity, friend: Entity) -> None:
    friend.memes["hope"] += 1
    world.say(
        f'"Shall I sing the second line?" asked {friend.id}, with a hand already half raised.'
    )
    inner(world, lead, "I want the prettiest part for myself.")


def curt_reply(world: World, lead: Entity, friend: Entity, mood: Mood) -> None:
    lead.memes["pride"] += 1
    lead.memes["curtness"] += 1
    friend.memes["hurt"] += 1
    world.say(
        f"But {lead.id} gave a {mood.adjective} answer. {mood.reply}"
    )
    inner(world, lead, "That was quick and sharp. It sounded big in my mouth, but small in my heart.")
    propagate(world, narrate=False)
    if world.get("song").meters["broken"] >= THRESHOLD:
        world.say(
            f"{friend.id}'s smile folded up, and the two rhyme cards no longer felt like a pair."
        )


def falter(world: World, lead: Entity, friend: Entity) -> None:
    world.say(
        f"{lead.id} tried the first line alone, and {friend.id} looked down at the grass. "
        f"The tune did not hop; it only sat."
    )
    inner(world, lead, "Oh dear. One line is lonely. The song has room for two.")
    world.facts["noticed_lonely_song"] = True


def helper_arrives(world: World, helper: Entity, link: LinkWord) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"{helper.label_word.capitalize()} came by with a soft step and listened. "
        f'"A rhyme can share a branch," {helper.pronoun()} said. '
        f'"A {link.word} is a conjunction. It helps one part hold hands with another."'
    )


def lesson(world: World, helper: Entity, lead: Entity, friend: Entity, link: LinkWord, prop: Prop) -> None:
    cards = world.get("cards")
    cards.meters["joined"] += 1
    prop_ent = world.get("prop")
    prop_ent.meters["ready"] += 1
    lead.memes["shame"] += 1
    lead.memes["kindness"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"{helper.label_word.capitalize()} tapped the two cards together and {prop.success_text}. "
        f'"Try again," {helper.pronoun()} said, "{friend.id} on one side, {link.word} on the other."'
    )
    inner(world, lead, f"I do not need to be first all by myself. I can be first {link.word} friendly.")
    world.say(
        f'{lead.id} took a breath. "I was {world.facts["mood_word"]}. Will you sing with me?"'
    )
    world.say(f'{friend.id} nodded. "{link.turn_text}"')
    propagate(world, narrate=False)


def sing_together(world: World, lead: Entity, friend: Entity, link: LinkWord, prop: Prop, setting: Setting) -> None:
    lead.memes["joy"] += 1
    friend.memes["joy"] += 1
    song = world.get("song")
    if song.meters["steady"] >= THRESHOLD:
        world.say(
            f'''So they sang beneath the sycamore: "{lead.id} hums {link.word} {friend.id} rings, "'''
            f"two small hearts on silver strings."
        )
        world.say(
            f"The tune kept time with {prop.label}, and even {setting.breeze.lower()} seemed to sway along."
        )
        world.say(
            f"By the end, the cards were together, the children were together, and the little rhyme knew how to skip."
        )
@dataclass
class StoryParams:
    setting: str
    link: str
    mood: str
    prop: str
    lead_name: str
    lead_type: str
    friend_name: str
    friend_type: str
    helper_type: str
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


KNOWLEDGE = {
    "conjunction": [
        (
            "What is a conjunction?",
            "A conjunction is a joining word such as and, but, or so. It helps two ideas belong together in one sentence or one song.",
        )
    ],
    "curt": [
        (
            "What does curt mean?",
            "Curt means very short in a sharp or unfriendly way. A curt answer can make another person feel small or shut out.",
        )
    ],
    "sycamore": [
        (
            "What is a sycamore?",
            "A sycamore is a big tree with wide leaves and strong branches. Its shade can make a cool, cozy place to sit or sing.",
        )
    ],
    "music": [
        (
            "Why does keeping a beat help a song?",
            "A beat gives a song a steady pattern to follow. When everyone keeps the same beat, singing together feels easier.",
        )
    ],
    "bell": [
        (
            "What does a bell do in a song game?",
            "A bell can ring in a clear, bright way that helps children hear the rhythm. That makes it easier to sing at the same time.",
        )
    ],
    "ribbon": [
        (
            "What can a ribbon do besides decorate?",
            "A ribbon can tie or join light things together. In a game, that can help small cards stay neat and side by side.",
        )
    ],
    "clappers": [
        (
            "What are wooden clappers for?",
            "Wooden clappers make a click-clack sound when you tap them. Children can use them to keep a simple beat.",
        )
    ],
}
KNOWLEDGE_ORDER = ["conjunction", "curt", "sycamore", "music", "bell", "ribbon", "clappers"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    friend = f["friend"]
    link = f["link"]
    prop = f["prop_cfg"]
    return [
        'Write a short nursery-rhyme-style story for a 3-to-5-year-old that includes the words "conjunction", "curt", and "sycamore".',
        f"Tell a gentle story with inner monologue where {lead.id} speaks too sharply to {friend.id}, then learns to use the conjunction '{link.word}' to join a rhyme and mend the moment.",
        f"Write a child-facing story under a sycamore tree where a small musical prop like {prop.label} helps two children sing together after one curt reply breaks the game.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    friend = f["friend"]
    helper = f["helper"]
    link = f["link"]
    prop = f["prop_cfg"]
    mood = f["mood"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {lead.id} and {friend.id}, who wanted to sing a rhyme under a sycamore tree, and {helper.label_word} who helped them. The story follows how their little game wobbled and then was mended.",
        ),
        (
            f"Why did the song stop feeling happy after {lead.id} answered?",
            f"{lead.id} gave a {mood.adjective} reply and shut {friend.id} out of the duet. That hurt {friend.id}'s feelings, so the two rhyme cards no longer felt joined and the tune lost its hop.",
        ),
        (
            "What did the inner monologue show?",
            f"It showed {lead.id}'s private thoughts changing inside. First {lead.pronoun()} wanted the prettiest part alone, and then {lead.pronoun()} realized one line was lonely and that being sharp had felt wrong.",
        ),
        (
            f"How did the grown-up help fix the problem?",
            f"{helper.label_word.capitalize()} explained that '{link.word}' is a conjunction, a joining word, and then {prop.qa_text}. That gave the children both a kinder plan and a steadier way to sing together.",
        ),
        (
            "How did the story end?",
            f"It ended with the rhyme moving again beneath the sycamore and both children singing side by side. The ending image proves what changed, because the cards were together, the beat was steady, and the children were together too.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"conjunction", "curt", "sycamore", "music"}
    tags |= set(f["link"].tags)
    tags |= set(f["mood"].tags)
    tags |= set(f["prop_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        flags = [name for name, on in (("steady", e.steady), ("joins_lines", e.joins_lines), ("keeps_beat", e.keeps_beat)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="yard",
        link="and",
        mood="curt",
        prop="bell",
        lead_name="Lila",
        lead_type="girl",
        friend_name="Ben",
        friend_type="boy",
        helper_type="mother",
        seed=101,
    ),
    StoryParams(
        setting="lane",
        link="so",
        mood="snappy",
        prop="ribbon",
        lead_name="Ollie",
        lead_type="boy",
        friend_name="May",
        friend_type="girl",
        helper_type="aunt",
        seed=102,
    ),
    StoryParams(
        setting="green",
        link="but",
        mood="huffy",
        prop="clappers",
        lead_name="Tess",
        lead_type="girl",
        friend_name="Max",
        friend_type="boy",
        helper_type="father",
        seed=103,
    ),
]


def explain_rejection(setting: Setting, prop: Prop) -> str:
    if "sycamore" not in setting.tags:
        return "(No story: the setting must truly be under a sycamore, because that tree is part of the tale's image and ending.)"
    if prop.sense < SENSE_MIN:
        return (
            f"(No story: {prop.label} is too weak for this rhyme game. The fix should both join the cards and help keep the beat.)"
        )
    if not prop.joins_lines:
        return (
            f"(No story: {prop.label} does not join the two rhyme cards, so it cannot honestly solve the problem.)"
        )
    if not prop.keeps_beat:
        return (
            f"(No story: {prop.label} does not help the children keep a beat, so the duet would still wobble.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
valid_setting(S) :- setting(S), has_sycamore(S).
sensible_prop(P) :- prop(P), sense(P, N), sense_min(M), N >= M, joins_lines(P), keeps_beat(P), steady(P).
valid(S, L, M, P) :- valid_setting(S), link(L), mood(M), sensible_prop(P).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "sycamore" in setting.tags:
            lines.append(asp.fact("has_sycamore", sid))
    for lid in LINKS:
        lines.append(asp.fact("link", lid))
    for mid in MOODS:
        lines.append(asp.fact("mood", mid))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("sense", pid, prop.sense))
        if prop.joins_lines:
            lines.append(asp.fact("joins_lines", pid))
        if prop.keeps_beat:
            lines.append(asp.fact("keeps_beat", pid))
        if prop.steady:
            lines.append(asp.fact("steady", pid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gate:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a curt reply under a sycamore tree, mended by a conjunction and a shared rhyme."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--link", choices=LINKS)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--lead-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--lead-type", choices=["girl", "boy"])
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.prop:
        setting = SETTINGS[args.setting]
        prop = PROPS[args.prop]
        if not valid_story(setting, prop):
            raise StoryError(explain_rejection(setting, prop))
    if args.prop and not prop_is_sensible(PROPS[args.prop]):
        raise StoryError(explain_rejection(SETTINGS[args.setting] if args.setting else SETTINGS["yard"], PROPS[args.prop]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.link is None or combo[1] == args.link)
        and (args.mood is None or combo[2] == args.mood)
        and (args.prop is None or combo[3] == args.prop)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, link, mood, prop = rng.choice(sorted(combos))
    lead_type = args.lead_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or rng.choice(["girl", "boy"])
    lead_name = args.lead_name or _pick_name(rng, lead_type)
    friend_name = args.friend_name or _pick_name(rng, friend_type, avoid=lead_name)
    helper_type = args.helper_type or rng.choice(["mother", "father", "aunt", "uncle"])

    return StoryParams(
        setting=setting,
        link=link,
        mood=mood,
        prop=prop,
        lead_name=lead_name,
        lead_type=lead_type,
        friend_name=friend_name,
        friend_type=friend_type,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        link = LINKS[params.link]
        mood = MOODS[params.mood]
        prop = PROPS[params.prop]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if not valid_story(setting, prop):
        raise StoryError(explain_rejection(setting, prop))

    reply = mood.reply.format(lead=params.lead_name)
    mood = Mood(
        id=mood.id,
        adjective=mood.adjective,
        reply=reply,
        soft_fix=mood.soft_fix,
        tags=set(mood.tags),
    )

    world = tell(
        setting=setting,
        link=link,
        mood=mood,
        prop=prop,
        lead_name=params.lead_name,
        lead_type=params.lead_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        helper_type=params.helper_type,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, link, mood, prop) combos:\n")
        for setting, link, mood, prop in combos:
            print(f"  {setting:6} {link:4} {mood:7} {prop}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
            header = f"### {p.lead_name} and {p.friend_name}: {p.link} under {p.setting} ({p.mood}, {p.prop})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    setting: Setting,
    link: LinkWord,
    mood: Mood,
    prop: Prop,
    lead_name: str,
    lead_type: str,
    friend_name: str,
    friend_type: str,
    helper_type: str,
) -> World:
    world = World()
    lead = world.add(
        Entity(
            id=lead_name,
            kind="character",
            type=lead_type,
            role="lead",
            label=lead_name,
            attrs={},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_type,
            role="friend",
            label=friend_name,
            attrs={},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the grown-up",
            attrs={},
        )
    )
    world.add(
        Entity(
            id="tree",
            type="tree",
            label="sycamore",
            attrs={},
        )
    )
    world.add(
        Entity(
            id="cards",
            type="cards",
            label="rhyme cards",
            attrs={},
        )
    )
    world.add(
        Entity(
            id="song",
            type="song",
            label="little song",
            attrs={},
        )
    )
    world.add(
        Entity(
            id="prop",
            type="prop",
            label=prop.label,
            steady=prop.steady,
            joins_lines=prop.joins_lines,
            keeps_beat=prop.keeps_beat,
            attrs={},
        )
    )

    world.facts["mood_word"] = mood.adjective
    world.facts["link_word"] = link.word
    world.facts["setting"] = setting
    world.facts["link"] = link
    world.facts["mood"] = mood
    world.facts["prop_cfg"] = prop
    world.facts["predicted_break"] = False
    world.facts["noticed_lonely_song"] = False

    opening(world, lead, friend, setting, prop)
    invite(world, lead, friend)

    world.para()
    pred = predict_break(world)
    world.facts["predicted_break"] = pred["broken"]
    world.facts["predicted_unjoined"] = pred["cards_unjoined"]
    curt_reply(world, lead, friend, mood)
    falter(world, lead, friend)

    world.para()
    helper_arrives(world, helper, link)
    lesson(world, helper, lead, friend, link, prop)
    sing_together(world, lead, friend, link, prop, setting)

    world.facts.update(
        lead=lead,
        friend=friend,
        helper=helper,
        outcome="mended" if world.get("song").meters["steady"] >= THRESHOLD else "stuck",
        shared=world.get("cards").meters["joined"] >= THRESHOLD,
        song_steady=world.get("song").meters["steady"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "yard": Setting(
        id="yard",
        place="the little yard",
        breeze="A green breeze brushed the leaves.",
        ground="The roots made round bumps for dancing shoes.",
        tags={"sycamore", "outdoor"},
    ),
    "lane": Setting(
        id="lane",
        place="the shady lane",
        breeze="A soft breeze rocked the branches.",
        ground="The path was striped with leaf-shadow.",
        tags={"sycamore", "outdoor"},
    ),
    "green": Setting(
        id="green",
        place="the village green",
        breeze="A mild breeze turned the leaves like tiny hands.",
        ground="The grass looked combed and bright.",
        tags={"sycamore", "outdoor"},
    ),
}

LINKS = {
    "and": LinkWord(
        id="and",
        word="and",
        meaning="joining two happy parts",
        turn_text="Yes, let us sing side by side.",
        tags={"conjunction", "joining"},
    ),
    "but": LinkWord(
        id="but",
        word="but",
        meaning="showing a turn",
        turn_text="Yes, and let the turn sound gentle this time.",
        tags={"conjunction", "turning"},
    ),
    "so": LinkWord(
        id="so",
        word="so",
        meaning="showing what happens next",
        turn_text="Yes, so the song can go on.",
        tags={"conjunction", "result"},
    ),
}

MOODS = {
    "curt": Mood(
        id="curt",
        adjective="curt",
        reply='"No, I will do it myself," said {lead}.',
        soft_fix="speak softly instead",
        tags={"curt", "feelings"},
    ),
    "snappy": Mood(
        id="snappy",
        adjective="snappy",
        reply='"No, not that way," said {lead}, too fast.',
        soft_fix="slow down and speak softly instead",
        tags={"curt", "feelings"},
    ),
    "huffy": Mood(
        id="huffy",
        adjective="huffy",
        reply='"No, this is my song," said {lead}, with a little puff.',
        soft_fix="make room and speak softly instead",
        tags={"curt", "feelings"},
    ),
}

PROPS = {
    "bell": Prop(
        id="bell",
        label="a silver bell",
        phrase="a silver bell",
        rhythm_text="ting-a-ling, sing-a-sing",
        sense=3,
        steady=True,
        keeps_beat=True,
        joins_lines=True,
        success_text="tied the cards to the bell-string so they could swing together",
        qa_text="used the bell-string to hold the two cards together and keep the beat",
        tags={"music", "bell"},
    ),
    "ribbon": Prop(
        id="ribbon",
        label="a blue ribbon",
        phrase="a blue ribbon",
        rhythm_text="flutter and patter, chatter and clatter",
        sense=3,
        steady=True,
        keeps_beat=True,
        joins_lines=True,
        success_text="looped the ribbon through the cards so the lines stayed side by side",
        qa_text="looped the ribbon through the cards to join the lines neatly",
        tags={"music", "ribbon"},
    ),
    "clappers": Prop(
        id="clappers",
        label="wooden clappers",
        phrase="two wooden clappers",
        rhythm_text="clap-a-click, pick-a-trick",
        sense=2,
        steady=True,
        keeps_beat=True,
        joins_lines=True,
        success_text="set the clappers in the children's hands and tucked the cards together between turns",
        qa_text="used the clappers to keep time while the joined cards stayed in order",
        tags={"music", "clappers"},
    ),
    "stone": Prop(
        id="stone",
        label="a smooth stone",
        phrase="a smooth stone",
        rhythm_text="thump and bump",
        sense=1,
        steady=True,
        keeps_beat=False,
        joins_lines=False,
        success_text="set the stone on the cards",
        qa_text="put a stone on the cards",
        tags={"stone"},
    ),
}

GIRL_NAMES = ["Lila", "May", "Nell", "Tess", "Mina", "Rose", "Ivy", "Pip"]
BOY_NAMES = ["Ollie", "Ben", "Toby", "Max", "Finn", "Ned", "Jem", "Kit"]

if __name__ == "__main__":
    main()
