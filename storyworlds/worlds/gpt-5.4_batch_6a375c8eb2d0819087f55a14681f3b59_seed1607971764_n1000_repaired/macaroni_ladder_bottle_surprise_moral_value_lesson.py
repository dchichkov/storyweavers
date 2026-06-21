#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/macaroni_ladder_bottle_surprise_moral_value_lesson.py
================================================================================

A standalone story world for a rhyming, child-facing tale about macaroni, a
ladder, and a bottle.

Tiny domain:
    A child wants to make a little music craft by pouring macaroni into a bottle
    that sits high on a shelf. A ladder is nearby, but climbing before asking
    for help can make it wobble. A grown-up either hands the bottle down or
    steadies the ladder. Then the child makes the craft, finds a small surprise
    sound inside the bottle, and learns the lesson: asking for help is brave.

This world keeps the prose state-driven:
    premise  -> a child spots a bottle and dreams up a macaroni shaker
    tension  -> the bottle is high up, and the ladder can wobble
    turn     -> the grown-up warns, predicts risk, and helps in a sensible way
    surprise -> the finished bottle sings with a hidden little jingle
    lesson   -> patience and asking for help make play safer and sweeter

Run it
------
    python storyworlds/worlds/gpt-5.4/macaroni_ladder_bottle_surprise_moral_value_lesson.py
    python storyworlds/worlds/gpt-5.4/macaroni_ladder_bottle_surprise_moral_value_lesson.py --qa
    python storyworlds/worlds/gpt-5.4/macaroni_ladder_bottle_surprise_moral_value_lesson.py --all
    python storyworlds/worlds/gpt-5.4/macaroni_ladder_bottle_surprise_moral_value_lesson.py --bottle spice_bottle
    python storyworlds/worlds/gpt-5.4/macaroni_ladder_bottle_surprise_moral_value_lesson.py --verify
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
IMPULSIVE_TRAITS = {"eager", "bouncy", "hasty"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    mouth_wide: bool = False
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Craft:
    id: str
    goal: str
    first_line: str
    closing: str
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
class BottleKind:
    id: str
    label: str
    phrase: str
    material: str
    mouth_wide: bool
    fragile: bool
    bonus: str
    bonus_sound: str
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
class Shelf:
    id: str
    label: str
    place: str
    height: int
    needs_ladder: bool
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
class Response:
    id: str
    sense: int
    supports: bool
    text: str
    qa_text: str
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


def _r_wobble(world: World) -> list[str]:
    child = world.get("child")
    ladder = world.get("ladder")
    if child.meters["climbing"] < THRESHOLD:
        return []
    if ladder.meters["steady"] >= THRESHOLD:
        return []
    sig = ("wobble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ladder.meters["wobble"] += 1
    child.memes["fear"] += 1
    world.get("room").meters["risk"] += 1
    return ["__wobble__"]


def _r_music(world: World) -> list[str]:
    bottle = world.get("bottle")
    if bottle.meters["opened"] < THRESHOLD:
        return []
    if bottle.meters["macaroni_in"] < THRESHOLD:
        return []
    if bottle.meters["sealed"] < THRESHOLD:
        return []
    sig = ("music",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bottle.meters["music"] += 1
    return ["__music__"]


def _r_surprise(world: World) -> list[str]:
    bottle = world.get("bottle")
    child = world.get("child")
    if bottle.meters["music"] < THRESHOLD:
        return []
    if not bottle.attrs.get("bonus"):
        return []
    sig = ("surprise",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["surprise"] += 1
    bottle.attrs["bonus_found"] = True
    return ["__surprise__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="music", tag="physical", apply=_r_music),
    Rule(name="surprise", tag="emotional", apply=_r_surprise),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


def usable_bottle(bottle: BottleKind) -> bool:
    return bottle.mouth_wide and not bottle.fragile


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for craft_id in CRAFTS:
        for bottle_id, bottle in BOTTLES.items():
            for shelf_id, shelf in SHELVES.items():
                if usable_bottle(bottle) and shelf.needs_ladder:
                    combos.append((craft_id, bottle_id, shelf_id))
    return combos


def explain_bottle_rejection(bottle: BottleKind) -> str:
    if bottle.fragile:
        return (
            f"(No story: {bottle.phrase} is glass and too breakable for a small child to "
            f"shake with macaroni. Pick a sturdy plastic bottle instead.)"
        )
    if not bottle.mouth_wide:
        return (
            f"(No story: dry macaroni will not fit neatly into {bottle.phrase}. "
            f"Pick a bottle with a wider mouth.)"
        )
    return "(No story: this bottle does not suit the craft.)"


def explain_shelf_rejection(shelf: Shelf) -> str:
    return (
        f"(No story: the bottle on {shelf.label} does not honestly need a ladder, "
        f"so there is no real safety choice or lesson to tell.)"
    )


def explain_response_rejection(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_wobble(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["climbing"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("ladder").meters["wobble"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"],
        "risk": sim.get("room").meters["risk"],
    }


def introduce(world: World, child: Entity, craft: Craft) -> None:
    world.say(
        f"{child.id} had a bright little plan for the day: {craft.first_line}. "
        f"The words in {child.pronoun('possessive')} head came almost like a tune, "
        f"light as a spoon and round as the moon."
    )


def spot_bottle(world: World, child: Entity, shelf: Shelf, bottle: BottleKind) -> None:
    child.memes["want"] += 1
    world.say(
        f"On {shelf.label} in the {shelf.place} sat {bottle.phrase}, tidy and tall. "
        f'"If I pour in macaroni, it might sing for us all," {child.pronoun()} said, '
        f"for the bottle looked perfect and the ladder stood by the wall."
    )


def warn(world: World, parent: Entity, child: Entity, shelf: Shelf, bottle: BottleKind) -> None:
    pred = predict_wobble(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f"{parent.label_word.capitalize()} saw {child.pronoun('object')} eyeing the ladder and "
        f"the bottle above. "
        f'"Slow and steady," {parent.pronoun()} said. "If you climb before I am near, '
        f"the ladder may wobble and fill you with fear."
    )


def first_step(world: World, child: Entity) -> None:
    child.meters["climbing"] += 1
    events = propagate(world, narrate=False)
    if "__wobble__" in events:
        world.say(
            f"But {child.id} was eager, quick as a breeze, and put one foot on the ladder "
            f"with too much ease. It gave a small shiver, a wobble, a sway, and {child.pronoun()} "
            f"froze on the rung right away."
        )


def ask_parent(world: World, parent: Entity, child: Entity, bottle: BottleKind) -> None:
    child.memes["trust"] += 1
    child.memes["relief"] += 1
    world.say(
        f"{child.id} took a breath and stepped back from the ladder. "
        f'"Please help me with the bottle," {child.pronoun()} said, calmer and gladder.'
    )
    world.say(
        f"{parent.label_word.capitalize()} reached up, brought {bottle.phrase} safely down, "
        f"and set it in {child.pronoun('possessive')} hands with a smile instead of a frown."
    )


def steady_ladder(world: World, parent: Entity, child: Entity, bottle: BottleKind) -> None:
    ladder = world.get("ladder")
    ladder.meters["steady"] += 1
    child.meters["climbing"] = 1.0
    child.memes["trust"] += 1
    child.memes["relief"] += 1
    world.say(
        f'{parent.label_word.capitalize()} wrapped steady hands around the ladder and said, '
        f'"Now climb one step at a time, with calm in your head."'
    )
    world.say(
        f"With the ladder held still, {child.id} climbed slowly and bright, "
        f"lifted down {bottle.phrase}, and beamed at the safe little sight."
    )


def make_craft(world: World, child: Entity, craft: Craft, bottle: BottleKind) -> None:
    bottle_ent = world.get("bottle")
    bottle_ent.meters["opened"] += 1
    bottle_ent.meters["macaroni_in"] += 1
    bottle_ent.meters["sealed"] += 1
    child.memes["joy"] += 1
    events = propagate(world, narrate=False)
    world.say(
        f"At the table they tapped dry macaroni into the bottle, one clink after another, "
        f"soft, bright, and dottle. Then on went the cap with a neat little twist, "
        f"and {child.id} gave the bottle a careful shake from {child.pronoun('possessive')} wrist."
    )
    if "__music__" in events:
        world.say(
            f"The macaroni went skitter-skat, patter and pring, turning the plain little bottle "
            f"into a thing that could sing."
        )


def surprise(world: World, child: Entity, bottle: BottleKind, craft: Craft) -> None:
    if not world.get("bottle").attrs.get("bonus_found"):
        return
    child.memes["wonder"] += 1
    world.say(
        f"Then came the surprise with a bright silver zing: {bottle.bonus} made "
        f"{bottle.bonus_sound}, a secret small ring. "
        f"{child.id}'s eyes grew round as the moon in the night, and the room felt warmer, "
        f"safer, and light."
    )
    world.say(
        f'"A kind slow start made a sweeter sound," {child.pronoun()} said. '
        f"That was the moral {child.pronoun()} carried in {child.pronoun('possessive')} head."
    )
    world.say(
        f"From then on, when something stood high and a ladder stood near, "
        f"{child.pronoun()} asked first for help, and climbed without fear. {craft.closing}"
    )
@dataclass
class StoryParams:
    craft: str
    bottle: str
    shelf: str
    response: str
    child_name: str
    child_type: str
    parent_type: str
    trait: str
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
    "macaroni": [
        (
            "What is macaroni?",
            "Macaroni is a small kind of pasta. Dry macaroni is hard and can rattle inside a container."
        )
    ],
    "ladder": [
        (
            "Why should a child ask for help before climbing a ladder?",
            "A ladder can wobble if it is not held steady or used carefully. Asking for help keeps climbing slower and safer."
        )
    ],
    "bottle": [
        (
            "Why can a bottle make a shaker sound?",
            "When dry pieces like macaroni bounce inside a bottle, they tap the sides and make a rattling sound. That is why bottles can become simple music toys."
        )
    ],
    "ask_help": [
        (
            "Why is asking for help a brave choice?",
            "Asking for help shows good thinking, not weakness. It helps people stay safe and solve problems together."
        )
    ],
    "plastic": [
        (
            "Why is a plastic bottle better than a glass bottle for a child craft?",
            "Plastic is lighter and less likely to break. That makes it a safer choice for shaking and playing."
        )
    ],
    "music": [
        (
            "How can a homemade shaker make music?",
            "A homemade shaker makes music when the things inside bounce and tap. Different little objects can make bright or soft sounds."
        )
    ],
}
KNOWLEDGE_ORDER = ["macaroni", "ladder", "bottle", "ask_help", "plastic", "music"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    craft = f["craft"]
    bottle = f["bottle_cfg"]
    if f["outcome"] == "wobble_then_safe":
        return [
            'Write a rhyming story for a 3-to-5-year-old that includes the words "macaroni", "ladder", and "bottle".',
            f"Tell a gentle rhyming story where {f['child_name']} wants to make {craft.goal}, starts up a ladder too fast, and then learns to ask for help.",
            f'Write a child-facing poem-story with a surprise ending, a clear moral value, and the lesson "{f["lesson"]}".',
        ]
    return [
        'Write a rhyming story for a 3-to-5-year-old that includes the words "macaroni", "ladder", and "bottle".',
        f"Tell a warm rhyming story where a {child.type} asks for help getting {bottle.phrase} from a high shelf and turns it into {craft.goal}.",
        f'Write a simple rhyming story with a surprise sound at the end and the lesson "{f["lesson"]}".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    craft = f["craft"]
    bottle = f["bottle_cfg"]
    shelf = f["shelf_cfg"]
    response = f["response"]
    child_name = f["child_name"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name} and {child_name}'s {pw}. {child_name} wanted to make {craft.goal} from macaroni and a bottle."
        ),
        (
            "Why did the ladder matter in the story?",
            f"The bottle was sitting on {shelf.label}, so the child noticed the ladder beside the wall. The ladder made the moment into a safety choice instead of a simple grab."
        ),
        (
            f"What problem did {child_name} have?",
            f"{child_name} wanted the bottle for the macaroni craft, but it was up high. That meant climbing too quickly could make the ladder wobble."
        ),
    ]
    if f.get("wobble"):
        qa.append(
            (
                f"What happened before the grown-up helped {child_name}?",
                f"{child_name} stepped onto the ladder too fast, and it gave a small wobble. That scare is what showed why the warning mattered."
            )
        )
    qa.append(
        (
            f"How was the problem solved?",
            f"{pw.capitalize()} helped by using the safe plan: {response.qa_text}. Because of that help, the bottle came down without a fall."
        )
    )
    if f.get("surprise"):
        qa.append(
            (
                "What was the surprise in the bottle craft?",
                f"The finished bottle did more than rattle with macaroni: {bottle.bonus} also made {bottle.bonus_sound}. The extra little sound turned the craft into a happy surprise."
            )
        )
    qa.append(
        (
            "What lesson did the child learn?",
            f"{child_name} learned to ask for help before climbing for something high. The calm choice made the craft safer and the ending sweeter."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"macaroni", "ladder", "bottle", "music", "ask_help"}
    if "plastic" in f["bottle_cfg"].tags:
        tags.add("plastic")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        flags = []
        if e.mouth_wide:
            flags.append("mouth_wide")
        if e.fragile:
            flags.append("fragile")
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        craft="rain_song",
        bottle="juice_bottle",
        shelf="pantry_top",
        response="ask_parent",
        child_name="Mia",
        child_type="girl",
        parent_type="mother",
        trait="careful",
    ),
    StoryParams(
        craft="parade_rhyme",
        bottle="milk_bottle",
        shelf="studio_high",
        response="hold_ladder",
        child_name="Leo",
        child_type="boy",
        parent_type="father",
        trait="thoughtful",
    ),
    StoryParams(
        craft="moon_chime",
        bottle="juice_bottle",
        shelf="bookcase_top",
        response="hold_ladder",
        child_name="Zoe",
        child_type="girl",
        parent_type="mother",
        trait="eager",
    ),
]


def outcome_of(params: StoryParams) -> str:
    if params.response == "hold_ladder" and params.trait in IMPULSIVE_TRAITS:
        return "wobble_then_safe"
    return "asked_first" if params.response == "ask_parent" else "steady_climb"


ASP_RULES = r"""
usable_bottle(B) :- bottle(B), mouth_wide(B), not fragile(B).
valid(C, B, S) :- craft(C), bottle(B), shelf(S), usable_bottle(B), needs_ladder(S).

sensible(R) :- response(R), sense(R, N), sense_min(M), N >= M.

wobble_then_safe :- chosen_response(hold_ladder), chosen_trait(T), impulsive(T).
asked_first :- chosen_response(ask_parent).
steady_climb :- chosen_response(hold_ladder), not wobble_then_safe.

outcome(wobble_then_safe) :- wobble_then_safe.
outcome(asked_first) :- asked_first.
outcome(steady_climb) :- steady_climb.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid in CRAFTS:
        lines.append(asp.fact("craft", cid))
    for bid, bottle in BOTTLES.items():
        lines.append(asp.fact("bottle", bid))
        if bottle.mouth_wide:
            lines.append(asp.fact("mouth_wide", bid))
        if bottle.fragile:
            lines.append(asp.fact("fragile", bid))
    for sid, shelf in SHELVES.items():
        lines.append(asp.fact("shelf", sid))
        if shelf.needs_ladder:
            lines.append(asp.fact("needs_ladder", sid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
    for trait in sorted(IMPULSIVE_TRAITS):
        lines.append(asp.fact("impulsive", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


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


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_response", params.response),
            asp.fact("chosen_trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: macaroni, ladder, bottle, surprise, and a lesson."
    )
    ap.add_argument("--craft", choices=CRAFTS)
    ap.add_argument("--bottle", choices=BOTTLES)
    ap.add_argument("--shelf", choices=SHELVES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.bottle is not None and not usable_bottle(BOTTLES[args.bottle]):
        raise StoryError(explain_bottle_rejection(BOTTLES[args.bottle]))
    if args.shelf is not None and not SHELVES[args.shelf].needs_ladder:
        raise StoryError(explain_shelf_rejection(SHELVES[args.shelf]))
    if args.response is not None and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response_rejection(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.craft is None or combo[0] == args.craft)
        and (args.bottle is None or combo[1] == args.bottle)
        and (args.shelf is None or combo[2] == args.shelf)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    craft_id, bottle_id, shelf_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        craft=craft_id,
        bottle=bottle_id,
        shelf=shelf_id,
        response=response_id,
        child_name=child_name,
        child_type=child_type,
        parent_type=parent_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.craft not in CRAFTS:
        raise StoryError(f"(Unknown craft: {params.craft})")
    if params.bottle not in BOTTLES:
        raise StoryError(f"(Unknown bottle: {params.bottle})")
    if params.shelf not in SHELVES:
        raise StoryError(f"(Unknown shelf: {params.shelf})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    bottle = BOTTLES[params.bottle]
    shelf = SHELVES[params.shelf]
    response = RESPONSES[params.response]

    if not usable_bottle(bottle):
        raise StoryError(explain_bottle_rejection(bottle))
    if not shelf.needs_ladder:
        raise StoryError(explain_shelf_rejection(shelf))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response_rejection(params.response))

    world = tell(
        craft=CRAFTS[params.craft],
        bottle_cfg=bottle,
        shelf_cfg=shelf,
        response=response,
        child_name=params.child_name,
        child_type=params.child_type,
        parent_type=params.parent_type,
        trait=params.trait,
    )
    child = world.facts["child"]
    story_text = world.render().replace("child", world.facts["child_name"]).replace("parent", child.id)
    story_text = story_text.replace("child", world.facts["child_name"])
    story_text = story_text.replace("parent", world.facts["parent"].label_word.capitalize())

    # Restore proper names carefully in the rendered story.
    story_text = story_text.replace("child's", f"{world.facts['child_name']}'s")
    story_text = story_text.replace("child", world.facts["child_name"])
    story_text = story_text.replace("Parent", world.facts["parent"].label_word.capitalize())

    # The prose functions mostly used labels/pronouns; ensure opening references use the child's name.
    story_text = story_text.replace("child.id", world.facts["child_name"])

    return StorySample(
        params=params,
        story=story_text,
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

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos parity holds ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sensible = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(py_sensible)} clingo={sorted(asp_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(p)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} scenario outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (craft, bottle, shelf) combos:\n")
        for craft, bottle, shelf in combos:
            print(f"  {craft:13} {bottle:12} {shelf}")
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
            header = f"### {p.child_name}: {p.craft} with {p.bottle} from {p.shelf} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    craft: Craft,
    bottle_cfg: BottleKind,
    shelf_cfg: Shelf,
    response: Response,
    child_name: str = "Mia",
    child_type: str = "girl",
    parent_type: str = "mother",
    trait: str = "eager",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id="child",
            kind="character",
            type=child_type,
            label=child_name,
            role="child",
            traits=[trait],
            attrs={},
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
            traits=["calm"],
            attrs={},
        )
    )
    world.add(
        Entity(
            id="room",
            type="room",
            label=shelf_cfg.place,
            attrs={},
        )
    )
    world.add(
        Entity(
            id="ladder",
            type="ladder",
            label="ladder",
            attrs={},
        )
    )
    world.add(
        Entity(
            id="bottle",
            type="bottle",
            label=bottle_cfg.label,
            mouth_wide=bottle_cfg.mouth_wide,
            fragile=bottle_cfg.fragile,
            attrs={
                "bonus": bottle_cfg.bonus,
                "bonus_found": False,
                "material": bottle_cfg.material,
            },
        )
    )
    world.facts.update(
        child_name=child_name,
        parent_type=parent_type,
        trait=trait,
        craft=craft,
        bottle_cfg=bottle_cfg,
        shelf_cfg=shelf_cfg,
        response=response,
        child=child,
        parent=parent,
        surprise=False,
    )

    introduce(world, child, craft)
    spot_bottle(world, child, shelf_cfg, bottle_cfg)

    world.para()
    warn(world, parent, child, shelf_cfg, bottle_cfg)

    if response.id == "hold_ladder" and trait in IMPULSIVE_TRAITS:
        first_step(world, child)

    world.para()
    if response.id == "ask_parent":
        ask_parent(world, parent, child, bottle_cfg)
        outcome = "asked_first"
    else:
        steady_ladder(world, parent, child, bottle_cfg)
        outcome = "steady_climb" if world.get("ladder").meters["wobble"] < THRESHOLD else "wobble_then_safe"

    world.para()
    make_craft(world, child, craft, bottle_cfg)
    surprise(world, child, bottle_cfg, craft)

    world.facts.update(
        outcome=outcome,
        wobble=world.get("ladder").meters["wobble"] >= THRESHOLD,
        surprise=world.get("bottle").attrs.get("bonus_found", False),
        lesson="ask for help before climbing",
    )
    return world


CRAFTS = {
    "rain_song": Craft(
        id="rain_song",
        goal="a rain-song shaker",
        first_line="to make a rain-song shaker from a bottle and macaroni",
        closing="So the lesson stayed simple and true: ask for help, and safe hands help you.",
        tags={"music", "macaroni"},
    ),
    "parade_rhyme": Craft(
        id="parade_rhyme",
        goal="a parade-rhyme shaker",
        first_line="to make a parade-rhyme shaker from a bottle and macaroni",
        closing="So the lesson marched on in gentle delight: kind help first, then play just right.",
        tags={"music", "macaroni"},
    ),
    "moon_chime": Craft(
        id="moon_chime",
        goal="a moon-chime shaker",
        first_line="to make a moon-chime shaker from a bottle and macaroni",
        closing="So the lesson glowed soft as a lantern above: ask with care, and play with love.",
        tags={"music", "macaroni"},
    ),
}

BOTTLES = {
    "juice_bottle": BottleKind(
        id="juice_bottle",
        label="juice bottle",
        phrase="a clean plastic juice bottle",
        material="plastic",
        mouth_wide=True,
        fragile=False,
        bonus="a tiny bell left inside from an old craft kit",
        bonus_sound="a sweet bell-bright tingle",
        tags={"bottle", "plastic", "bell"},
    ),
    "milk_bottle": BottleKind(
        id="milk_bottle",
        label="milk bottle",
        phrase="a sturdy little milk bottle",
        material="plastic",
        mouth_wide=True,
        fragile=False,
        bonus="a shiny bead tucked in the bottom",
        bonus_sound="a bright bead-click jingle",
        tags={"bottle", "plastic", "bead"},
    ),
    "glass_bottle": BottleKind(
        id="glass_bottle",
        label="glass bottle",
        phrase="a slim glass bottle",
        material="glass",
        mouth_wide=True,
        fragile=True,
        bonus="a tiny shell caught inside",
        bonus_sound="a soft shell-tap ring",
        tags={"bottle", "glass"},
    ),
    "spice_bottle": BottleKind(
        id="spice_bottle",
        label="spice bottle",
        phrase="a narrow spice bottle",
        material="plastic",
        mouth_wide=False,
        fragile=False,
        bonus="a paper star at the bottom",
        bonus_sound="a papery flutter",
        tags={"bottle", "narrow"},
    ),
}

SHELVES = {
    "pantry_top": Shelf(
        id="pantry_top",
        label="the top pantry shelf",
        place="kitchen",
        height=3,
        needs_ladder=True,
        tags={"high_shelf", "kitchen"},
    ),
    "studio_high": Shelf(
        id="studio_high",
        label="the high craft shelf",
        place="hall cupboard",
        height=3,
        needs_ladder=True,
        tags={"high_shelf", "crafts"},
    ),
    "bookcase_top": Shelf(
        id="bookcase_top",
        label="the top bookcase ledge",
        place="playroom",
        height=2,
        needs_ladder=True,
        tags={"high_shelf", "playroom"},
    ),
    "bench_corner": Shelf(
        id="bench_corner",
        label="the low bench corner",
        place="kitchen",
        height=0,
        needs_ladder=False,
        tags={"low_spot"},
    ),
}

RESPONSES = {
    "ask_parent": Response(
        id="ask_parent",
        sense=3,
        supports=False,
        text="the child asks first and the grown-up brings the bottle down",
        qa_text="asked for help, and the grown-up handed the bottle down safely",
        tags={"ask_help"},
    ),
    "hold_ladder": Response(
        id="hold_ladder",
        sense=3,
        supports=True,
        text="the grown-up holds the ladder while the child climbs slowly",
        qa_text="the grown-up held the ladder while the child climbed carefully",
        tags={"ladder", "ask_help"},
    ),
    "pull_with_spoon": Response(
        id="pull_with_spoon",
        sense=1,
        supports=False,
        text="the child tries to hook the bottle with a long spoon",
        qa_text="tried to pull the bottle down with a spoon",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Ella", "Nora"]
BOY_NAMES = ["Leo", "Max", "Ben", "Sam", "Eli", "Theo"]
TRAITS = ["eager", "careful", "bouncy", "thoughtful", "hasty", "gentle"]

if __name__ == "__main__":
    main()
