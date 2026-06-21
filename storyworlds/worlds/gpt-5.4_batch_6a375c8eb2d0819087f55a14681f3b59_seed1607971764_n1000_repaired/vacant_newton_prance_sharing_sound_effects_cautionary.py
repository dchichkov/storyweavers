#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/vacant_newton_prance_sharing_sound_effects_cautionary.py
====================================================================================

A small ghost-story-flavored story world about two children in a vacant old
building, one sound-making toy, and the difference between rushing ahead alone
and sharing.

The domain rebuilds a gentle cautionary tale:

- a child named Newton and a friend explore a vacant place
- they use playful sound effects in a pretend ghost parade
- one child is asked to share the sound-maker
- if the child refuses and prances ahead alone, a harmless draft-driven object
  sounds spooky in the dark and frightens them
- a calm grown-up explains what made the noise
- the children learn to share and stay together

Run it
------
    python storyworlds/worlds/gpt-5.4/vacant_newton_prance_sharing_sound_effects_cautionary.py
    python storyworlds/worlds/gpt-5.4/vacant_newton_prance_sharing_sound_effects_cautionary.py --place ballroom --tool bell --source curtain
    python storyworlds/worlds/gpt-5.4/vacant_newton_prance_sharing_sound_effects_cautionary.py --source wall
    python storyworlds/worlds/gpt-5.4/vacant_newton_prance_sharing_sound_effects_cautionary.py --all
    python storyworlds/worlds/gpt-5.4/vacant_newton_prance_sharing_sound_effects_cautionary.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/vacant_newton_prance_sharing_sound_effects_cautionary.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    movable: bool = False
    noisy: bool = False
    shareable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "aunt", "mother"}
        male = {"boy", "man", "uncle", "father", "caretaker"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        mapping = {
            "aunt": "aunt",
            "uncle": "uncle",
            "caretaker": "caretaker",
            "mother": "mom",
            "father": "dad",
        }
        return mapping.get(self.type, self.type)
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    opening: str
    dark_corner: str
    tags: set[str] = field(default_factory=set)
    affords: set[str] = field(default_factory=set)
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
class SoundTool:
    id: str
    label: str
    phrase: str
    effect: str
    together_effect: str
    tags: set[str] = field(default_factory=set)
    shareable: bool = True
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
class Source:
    id: str
    label: str
    the: str
    motion: str
    sound: str
    reveal: str
    scary_shape: str
    movable: bool = True
    noisy: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "heard_noise": False,
            "looked_like_ghost": False,
            "shared_before": False,
            "adult_helped": False,
            "lesson_learned": False,
        }

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"holder", "friend"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.place)
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


def _r_draft_noise(world: World) -> list[str]:
    source = world.get("source")
    room = world.get("room")
    if source.meters["draft"] < THRESHOLD or not source.movable or not source.noisy:
        return []
    sig = ("draft_noise", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["spooky_noise"] += 1
    world.facts["heard_noise"] = True
    return ["__noise__"]


def _r_alone_fear(world: World) -> list[str]:
    source = world.get("source")
    room = world.get("room")
    out: list[str] = []
    for kid in world.kids():
        if kid.memes["alone"] < THRESHOLD or room.meters["spooky_noise"] < THRESHOLD:
            continue
        sig = ("alone_fear", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["fear"] += 2
        kid.meters["startled"] += 1
        world.facts["looked_like_ghost"] = True
        out.append("__fear__")
        if source.scary_shape:
            kid.attrs["shape_guess"] = source.scary_shape
    return out


def _r_together_courage(world: World) -> list[str]:
    kids = world.kids()
    if not kids:
        return []
    if any(k.memes["together"] < THRESHOLD for k in kids):
        return []
    sig = ("together_courage", "kids")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in kids:
        kid.memes["courage"] += 1
        if kid.memes["fear"] > 0:
            kid.memes["fear"] = max(0.0, kid.memes["fear"] - 1.0)
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="draft_noise", tag="physical", apply=_r_draft_noise),
    Rule(name="alone_fear", tag="emotional", apply=_r_alone_fear),
    Rule(name="together_courage", tag="social", apply=_r_together_courage),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def source_works(place: Place, source: Source) -> bool:
    return source.id in place.affords and source.movable and source.noisy


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for tool_id in TOOLS:
            for source_id, source in SOURCES.items():
                if source_works(place, source):
                    combos.append((place_id, tool_id, source_id))
    return combos


def predict_spook(world: World) -> dict:
    sim = world.copy()
    sim.get("source").meters["draft"] += 1
    propagate(sim, narrate=False)
    alone = sim.get("holder").memes["alone"] >= THRESHOLD
    scared = sim.get("holder").memes["fear"] >= THRESHOLD
    return {
        "noise": sim.get("room").meters["spooky_noise"] >= THRESHOLD,
        "alone": alone,
        "scared": scared,
    }


def introduce(world: World, holder: Entity, friend: Entity, tool: SoundTool) -> None:
    for kid in (holder, friend):
        kid.memes["joy"] += 1
    world.say(
        f"One windy evening, {holder.id} and {friend.id} slipped into {world.place.opening}. "
        f"The place looked vacant, but to them it felt perfect for a make-believe ghost parade."
    )
    world.say(
        f"{holder.id} loved to prance across the dusty floor with {tool.phrase}, making "
        f"{tool.effect} in the dim air."
    )


def set_game(world: World, holder: Entity, friend: Entity, tool: SoundTool) -> None:
    world.say(
        f'"Listen to this," {holder.id} whispered. {tool.together_effect.capitalize()} answered the empty room, '
        f"and both children giggled instead of feeling afraid."
    )
    world.say(
        f'Soon {friend.id} wanted a turn too. "Let me hold it next," {friend.pronoun()} asked.'
    )


def share_now(world: World, holder: Entity, friend: Entity, tool: SoundTool) -> None:
    holder.memes["generosity"] += 1
    friend.memes["gratitude"] += 1
    for kid in (holder, friend):
        kid.memes["together"] += 1
    world.facts["shared_before"] = True
    world.say(
        f"{holder.id} remembered that games feel better when everyone gets a turn, so "
        f"{holder.pronoun()} passed {tool.phrase} to {friend.id}."
    )
    world.say(
        f"They walked shoulder to shoulder toward {world.place.dark_corner}, taking turns with the sound "
        f"and counting each brave little step."
    )
    propagate(world, narrate=False)


def refuse_and_prance(world: World, holder: Entity, friend: Entity, tool: SoundTool) -> None:
    holder.memes["selfishness"] += 1
    holder.memes["alone"] += 1
    friend.memes["left_out"] += 1
    world.say(
        f'But {holder.id} hugged {tool.phrase} close. "Just one more turn for me," '
        f"{holder.pronoun()} said, and then {holder.pronoun()} began to prance ahead alone."
    )
    world.say(
        f"{friend.id} stayed behind by the doorway, feeling cross and a little worried as the cheerful "
        f"{tool.effect} faded into the dark."
    )


def spooky_turn(world: World, holder: Entity, source: Source) -> None:
    world.get("source").meters["draft"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When {holder.id} reached {world.place.dark_corner}, a draft slipped through a crack somewhere above. "
        f"{source.The} {source.motion} and made a sudden {source.sound}."
    )
    world.say(
        f"In the half-light it looked like {source.scary_shape}, and {holder.id}'s brave parade stopped all at once."
    )


def cry_for_help(world: World, holder: Entity, friend: Entity) -> None:
    holder.memes["fear"] += 1
    friend.memes["concern"] += 1
    world.say(f'"Oh!" cried {holder.id}. "I thought I saw a ghost!"')
    world.say(f'{friend.id} hurried closer and called, "Help! We heard something in here!"')


def calm_inspection(world: World, holder: Entity, friend: Entity, source: Source, tool: SoundTool) -> None:
    world.get("source").meters["draft"] += 1
    for kid in (holder, friend):
        kid.memes["together"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a draft brushed past them. {source.The} {source.motion} and made {source.sound} again, "
        f"but this time the children stayed together and listened carefully."
    )
    world.say(
        f'"That is not a ghost," {friend.id} said softly. "{source.reveal}." With {tool.phrase} shared between them, '
        f"the room felt more playful than spooky."
    )


def adult_arrives(world: World, adult: Entity, source: Source) -> None:
    world.facts["adult_helped"] = True
    adult.meters["lamplight"] += 1
    world.say(
        f"Soon {adult.title_word.capitalize()} {adult.id} came in with a small lamp. Warm light reached "
        f"{source.the} and showed exactly what had made the sound."
    )
    world.say(f"{source.The} was only {source.reveal}.")


def lesson(world: World, adult: Entity, holder: Entity, friend: Entity, tool: SoundTool) -> None:
    for kid in (holder, friend):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
        kid.memes["together"] += 1
    world.facts["lesson_learned"] = True
    world.say(
        f'{adult.title_word.capitalize()} {adult.id} knelt beside them. "Old places can sound spooky when drafts push '
        f"things around,\" {adult.pronoun()} said. \"That is why we stay together, use our eyes, and do not race ahead alone.\""
    )
    world.say(
        f'"And when there is only one {tool.label}," {adult.pronoun()} added, "sharing keeps the game kind as well as safe."'
    )


def shared_ending(world: World, holder: Entity, friend: Entity, tool: SoundTool) -> None:
    holder.memes["generosity"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"After that, {holder.id} and {friend.id} took turns with {tool.phrase}. "
        f"Each child made a little {tool.effect}, and each child waited for the other."
    )
    world.say(
        f"By the time they pranced back out of the old room, the vacant place no longer felt full of ghosts. "
        f"It felt full of careful footsteps, fair turns, and brave laughter."
    )
@dataclass
class StoryParams:
    place: str
    tool: str
    source: str
    holder_name: str = "Newton"
    holder_gender: str = "boy"
    friend_name: str = "Mira"
    friend_gender: str = "girl"
    adult_type: str = "caretaker"
    share_first: bool = False
    trait: str = "eager"
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
    "sharing": [
        (
            "Why is sharing important in a game?",
            "Sharing lets everyone join in and feel included. It also helps children stay close enough to help one another."
        )
    ],
    "sound_effects": [
        (
            "What are sound effects?",
            "Sound effects are noises people make or use to help a story or game feel real. A little jingle or clack can make pretend play feel exciting."
        )
    ],
    "draft": [
        (
            "What is a draft in an old room?",
            "A draft is a little stream of moving air that slips through cracks or open spaces. It can make curtains, shutters, or other loose things move and sound spooky."
        )
    ],
    "ghost_story": [
        (
            "Why do things look scary in the dark?",
            "In the dark, shapes are hard to see clearly, so your brain guesses before your eyes have enough information. That can make an ordinary thing look like something spooky."
        )
    ],
    "bell": [
        (
            "What sound does a little bell make?",
            "A little bell often makes a light ringing sound like jingle-jingle. The sound is bright and easy to hear."
        )
    ],
    "clapper": [
        (
            "What does a wooden clapper do?",
            "A wooden clapper makes a sharp clack-clack sound when the pieces knock together. It is a simple way to make rhythm in a game."
        )
    ],
    "whistle": [
        (
            "How does a whistle make a sound?",
            "When air moves through a whistle in the right way, it makes a clear high note. That is why whistles can be heard from far away."
        )
    ],
    "curtain": [
        (
            "Why can a curtain sound spooky in a draft?",
            "A curtain can rub, flap, and swish when moving air pushes it. In a quiet room, that soft sound can seem much bigger than it really is."
        )
    ],
    "coatstand": [
        (
            "Why might a coat stand look like a ghost?",
            "A coat stand can have long arms and a tall shape, especially if something is hanging on it. In dim light, that shape can fool you for a moment."
        )
    ],
    "shutter": [
        (
            "Why does a loose shutter make noise?",
            "A loose shutter can bump and creak when the wind pushes it. The wood knocks against the frame and makes a repeating sound."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "sharing",
    "sound_effects",
    "draft",
    "ghost_story",
    "bell",
    "clapper",
    "whistle",
    "curtain",
    "coatstand",
    "shutter",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    holder = f["holder"]
    friend = f["friend"]
    tool = f["tool_cfg"]
    source = f["source_cfg"]
    place = f["place_cfg"]
    if f["outcome"] == "shared_early":
        return [
            f'Write a gentle ghost-story-flavored story for a 3-to-5-year-old about a vacant {place.label}, a child named {holder.id}, and a sound-maker that must be shared.',
            f"Tell a story where {holder.id} and {friend.id} hear {source.sound} in the dark, but because they share {tool.phrase} and stay together, they discover the sound is harmless.",
            f'Write a story that includes the words "vacant" and "prance", uses playful sound effects, and ends with children sharing kindly instead of scaring one another.',
        ]
    return [
        f'Write a gentle cautionary ghost story for a 3-to-5-year-old about a vacant {place.label}, a child named {holder.id}, and one small {tool.label} that should be shared.',
        f"Tell a story where {holder.id} refuses to share {tool.phrase}, prances ahead alone, hears {source.sound}, and learns that spooky noises in old places can have ordinary causes.",
        f'Write a child-safe spooky story using sound effects and a sharing lesson, ending with the children calmer, kinder, and together.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    holder = f["holder"]
    friend = f["friend"]
    adult = f["adult"]
    tool = f["tool_cfg"]
    source = f["source_cfg"]
    place = f["place_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {holder.id} and {friend.id} exploring a vacant {place.label} with {tool.phrase}. The grown-up {adult.title_word} {adult.id} comes to help when the room feels spooky."
        ),
        (
            f"What were {holder.id} and {friend.id} pretending to do?",
            f"They were making a ghost parade in the old room and using {tool.phrase} for playful sound effects. The game is what led them deeper into the shadowy part of the building."
        ),
        (
            f"Why did {friend.id} ask for a turn with the {tool.label}?",
            f"{friend.id} wanted to join the game fairly instead of only listening from the side. Sharing mattered because one small sound-maker was part of the fun for both children."
        ),
    ]
    if f["outcome"] == "scared_then_shared":
        qa.extend([
            (
                f"Why did {holder.id} get scared?",
                f"{holder.id} ran ahead alone after refusing to share, so {holder.pronoun()} reached the darkest part of the room without a friend beside {holder.pronoun('object')}. Then {source.the} moved in a draft and made {source.sound}, which looked like {source.scary_shape} for a moment."
            ),
            (
                f"What did {adult.title_word} {adult.id} show the children?",
                f"{adult.title_word.capitalize()} {adult.id} showed them that the noise came from {source.reveal}. The lamp made the ordinary cause easy to see, which turned the ghost fear back into a simple room sound."
            ),
            (
                "What lesson did the children learn?",
                f"They learned to stay together in spooky places and to share {tool.phrase} instead of grabbing all the turns. Those two choices made the game kinder and kept anyone from rushing into fear alone."
            ),
        ])
    else:
        qa.extend([
            (
                f"Why did the children stay calm when they heard {source.sound}?",
                f"They were together and had already shared the game fairly, so neither child felt lonely or left out. Because they listened side by side, the sound felt easier to inspect instead of turning into panic."
            ),
            (
                f"What did {adult.title_word} {adult.id} explain?",
                f"{adult.title_word.capitalize()} {adult.id} explained that {source.reveal} and that drafts can make old rooms sound strange. The explanation gave the children a real cause for the spooky noise."
            ),
            (
                "How did the story end?",
                f"It ended with both children taking turns with {tool.phrase} and prancing out together. The ending shows they changed the game from grabby and spooky into fair and brave."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tool = f["tool_cfg"]
    source = f["source_cfg"]
    tags = {"sharing", "sound_effects", "draft", "ghost_story", tool.id, source.id}
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [n for n, on in (("movable", e.movable), ("noisy", e.noisy), ("shareable", e.shareable)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="ballroom",
        tool="bell",
        source="curtain",
        holder_name="Newton",
        holder_gender="boy",
        friend_name="Mira",
        friend_gender="girl",
        adult_type="caretaker",
        share_first=False,
        trait="eager",
    ),
    StoryParams(
        place="theater",
        tool="clapper",
        source="coatstand",
        holder_name="Newton",
        holder_gender="boy",
        friend_name="Lila",
        friend_gender="girl",
        adult_type="caretaker",
        share_first=True,
        trait="bouncy",
    ),
    StoryParams(
        place="schoolroom",
        tool="whistle",
        source="shutter",
        holder_name="Nora",
        holder_gender="girl",
        friend_name="Newton",
        friend_gender="boy",
        adult_type="uncle",
        share_first=False,
        trait="curious",
    ),
    StoryParams(
        place="theater",
        tool="bell",
        source="curtain",
        holder_name="Newton",
        holder_gender="boy",
        friend_name="Theo",
        friend_gender="boy",
        adult_type="caretaker",
        share_first=True,
        trait="thoughtful",
    ),
]


def explain_rejection(place: Place, source: Source) -> str:
    if source.id not in place.affords:
        allowed = ", ".join(sorted(place.affords))
        return (
            f"(No story: {source.the} does not fit the spooky sounds in this {place.label}. "
            f"Try a source that belongs here, like: {allowed}.)"
        )
    if not source.movable or not source.noisy:
        return (
            f"(No story: {source.the} would not move and make a spooky noise, so there is no honest ghost-story turn. "
            f"Pick a curtain, coat stand, or loose shutter instead.)"
        )
    return "(No story: this place/source pair does not make a plausible spooky sound.)"


ASP_RULES = r"""
shareable_tool(T) :- tool(T), shareable(T).
spooky_source(S) :- source(S), movable(S), noisy(S).
valid(P, T, S) :- place(P), tool(T), source(S), affords(P, S), shareable_tool(T), spooky_source(S).

outcome(shared_early) :- chosen_share(1).
outcome(scared_then_shared) :- chosen_share(0).

#show valid/3.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for sid in sorted(place.affords):
            lines.append(asp.fact("affords", pid, sid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if tool.shareable:
            lines.append(asp.fact("shareable", tid))
    for sid, source in SOURCES.items():
        lines.append(asp.fact("source", sid))
        if source.movable:
            lines.append(asp.fact("movable", sid))
        if source.noisy:
            lines.append(asp.fact("noisy", sid))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_share", 1 if params.share_first else 0)
    model = asp.one_model(asp_program(extra))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "shared_early" if params.share_first else "scared_then_shared"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost-story-flavored story world: a vacant place, spooky sound effects, sharing, and caution."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--adult-type", choices=["caretaker", "aunt", "uncle", "mother", "father"])
    ap.add_argument("--share-first", action="store_true", help="the holder shares before anything spooky happens")
    ap.add_argument("--no-share-first", action="store_true", help="the holder refuses first, causing the cautionary scare")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, tool, source) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Mira", "Lila", "Nora", "Ava", "Ella", "Ruby", "June", "Ivy"]
BOY_NAMES = ["Newton", "Theo", "Max", "Ben", "Leo", "Finn", "Owen", "Sam"]
TRAITS = ["eager", "bouncy", "careful", "curious", "thoughtful", "bright"]


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.share_first and args.no_share_first:
        raise StoryError("(Choose only one of --share-first or --no-share-first.)")

    if args.place and args.source:
        place = PLACES[args.place]
        source = SOURCES[args.source]
        if not source_works(place, source):
            raise StoryError(explain_rejection(place, source))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.tool is None or combo[1] == args.tool)
        and (args.source is None or combo[2] == args.source)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, tool_id, source_id = rng.choice(sorted(combos))
    holder_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    holder_name = _pick_name(rng, holder_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=holder_name)
    adult_type = args.adult_type or rng.choice(["caretaker", "aunt", "uncle", "mother", "father"])
    if args.share_first:
        share_first = True
    elif args.no_share_first:
        share_first = False
    else:
        share_first = bool(rng.randint(0, 1))
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        tool=tool_id,
        source=source_id,
        holder_name=holder_name,
        holder_gender=holder_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        adult_type=adult_type,
        share_first=share_first,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")

    place = PLACES[params.place]
    tool = TOOLS[params.tool]
    source = SOURCES[params.source]
    if not source_works(place, source):
        raise StoryError(explain_rejection(place, source))

    world = tell(
        place=place,
        tool=tool,
        source=source,
        holder_name=params.holder_name,
        holder_gender=params.holder_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        adult_type=params.adult_type,
        share_first=params.share_first,
        trait=params.trait,
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


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid_combos matches ASP ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    rng = random.Random(123)
    parser = build_parser()
    for _ in range(12):
        params = resolve_params(parser.parse_args([]), rng)
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke test generation and emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, tool, source) combos:\n")
        for place, tool, source in combos:
            print(f"  {place:10} {tool:8} {source}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
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
            header = (
                f"### {p.holder_name} & {p.friend_name}: {p.tool} in {p.place} near "
                f"{p.source} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    place: Place,
    tool: SoundTool,
    source: Source,
    holder_name: str = "Newton",
    holder_gender: str = "boy",
    friend_name: str = "Mira",
    friend_gender: str = "girl",
    adult_type: str = "caretaker",
    share_first: bool = False,
    trait: str = "eager",
) -> World:
    world = World(place)
    holder = world.add(Entity(
        id=holder_name,
        kind="character",
        type=holder_gender,
        role="holder",
        traits=[trait],
        attrs={"asked_to_share": False, "share_first": share_first},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=["careful"],
        attrs={"asked_to_share": True},
    ))
    adult = world.add(Entity(
        id="Ada",
        kind="character",
        type=adult_type,
        role="adult",
        label="the grown-up",
    ))
    world.add(Entity(id="room", type="room", label=place.label))
    world.add(Entity(
        id="tool",
        type="tool",
        label=tool.label,
        shareable=tool.shareable,
    ))
    world.add(Entity(
        id="source",
        type="source",
        label=source.label,
        movable=source.movable,
        noisy=source.noisy,
    ))

    introduce(world, holder, friend, tool)
    set_game(world, holder, friend, tool)

    world.para()
    if share_first:
        share_now(world, holder, friend, tool)
        calm_inspection(world, holder, friend, source, tool)
        world.para()
        adult_arrives(world, adult, source)
        lesson(world, adult, holder, friend, tool)
        world.para()
        shared_ending(world, holder, friend, tool)
        outcome = "shared_early"
    else:
        refuse_and_prance(world, holder, friend, tool)
        world.para()
        spooky_turn(world, holder, source)
        cry_for_help(world, holder, friend)
        world.para()
        adult_arrives(world, adult, source)
        lesson(world, adult, holder, friend, tool)
        world.para()
        shared_ending(world, holder, friend, tool)
        outcome = "scared_then_shared"

    world.facts.update(
        holder=holder,
        friend=friend,
        adult=adult,
        place_cfg=place,
        tool_cfg=tool,
        source_cfg=source,
        outcome=outcome,
    )
    return world


PLACES = {
    "ballroom": Place(
        id="ballroom",
        label="ballroom",
        opening="a vacant old ballroom at the edge of town",
        dark_corner="the shadowy end of the dance floor near the tall curtains",
        tags={"vacant", "ghost_place"},
        affords={"curtain", "shutter"},
    ),
    "theater": Place(
        id="theater",
        label="theater",
        opening="a vacant little theater behind the library",
        dark_corner="the wings beside the stage",
        tags={"vacant", "ghost_place"},
        affords={"curtain", "coatstand"},
    ),
    "schoolroom": Place(
        id="schoolroom",
        label="schoolroom",
        opening="a vacant schoolroom with a cracked piano",
        dark_corner="the far corner by the cloak hooks",
        tags={"vacant", "ghost_place"},
        affords={"coatstand", "shutter"},
    ),
}

TOOLS = {
    "bell": SoundTool(
        id="bell",
        label="jingle bell",
        phrase="a little jingle bell",
        effect="jingle-jingle",
        together_effect="jingle-jingle",
        tags={"sound_effects", "sharing", "bell"},
    ),
    "clapper": SoundTool(
        id="clapper",
        label="wooden clapper",
        phrase="a wooden clapper",
        effect="clack-clack",
        together_effect="clack-clack",
        tags={"sound_effects", "sharing", "clapper"},
    ),
    "whistle": SoundTool(
        id="whistle",
        label="tin whistle",
        phrase="a tin whistle",
        effect="peep-peep",
        together_effect="peep-peep",
        tags={"sound_effects", "sharing", "whistle"},
    ),
}

SOURCES = {
    "curtain": Source(
        id="curtain",
        label="curtain",
        the="the curtain",
        motion="lifted and whispered against the wall",
        sound="swish-swish",
        reveal="a long curtain puffing in the draft",
        scary_shape="a tall gray ghost with waving sleeves",
        movable=True,
        noisy=True,
        tags={"curtain", "draft", "ghost_shape"},
    ),
    "coatstand": Source(
        id="coatstand",
        label="coat stand",
        the="the coat stand",
        motion="rocked and tapped one wooden foot on the floor",
        sound="tap-tap",
        reveal="a lonely coat stand wobbling under an old scarf",
        scary_shape="a bent ghost bowing its head",
        movable=True,
        noisy=True,
        tags={"coatstand", "draft", "ghost_shape"},
    ),
    "shutter": Source(
        id="shutter",
        label="loose shutter",
        the="the loose shutter",
        motion="banged and shivered in the wind",
        sound="creak-creak",
        reveal="a loose shutter knocking against the frame",
        scary_shape="a giant ghost hand at the window",
        movable=True,
        noisy=True,
        tags={"shutter", "draft", "ghost_shape"},
    ),
    "wall": Source(
        id="wall",
        label="brick wall",
        the="the brick wall",
        motion="stood perfectly still",
        sound="",
        reveal="just a brick wall",
        scary_shape="nothing at all",
        movable=False,
        noisy=False,
        tags={"wall"},
    ),
}

if __name__ == "__main__":
    main()
