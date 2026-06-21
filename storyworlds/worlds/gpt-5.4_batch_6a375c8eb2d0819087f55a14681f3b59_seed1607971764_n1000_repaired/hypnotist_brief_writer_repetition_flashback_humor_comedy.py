#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hypnotist_brief_writer_repetition_flashback_humor_comedy.py
======================================================================================

A tiny storyworld about a writer who promises to give a brief speech, then gets
caught in the silly rhythm of a stage hypnotist's warm-up routine. The story is
built as a small stateful simulation: distraction spreads, the writer starts
repeating a funny word, a flashback supplies useful advice, and a grounding
anchor helps the writer finish in a warm, comic way.

Run it
------
    python storyworlds/worlds/gpt-5.4/hypnotist_brief_writer_repetition_flashback_humor_comedy.py
    python storyworlds/worlds/gpt-5.4/hypnotist_brief_writer_repetition_flashback_humor_comedy.py --venue library --prop watch --anchor card
    python storyworlds/worlds/gpt-5.4/hypnotist_brief_writer_repetition_flashback_humor_comedy.py --venue cafe --anchor bookmark
    python storyworlds/worlds/gpt-5.4/hypnotist_brief_writer_repetition_flashback_humor_comedy.py --all
    python storyworlds/worlds/gpt-5.4/hypnotist_brief_writer_repetition_flashback_humor_comedy.py --qa --json
    python storyworlds/worlds/gpt-5.4/hypnotist_brief_writer_repetition_flashback_humor_comedy.py --verify
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


# ---------------------------------------------------------------------------
# Core entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "librarian", "teacher", "mother"}
        male = {"boy", "man", "host", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
class Venue:
    id: str
    label: str
    room_phrase: str
    helper_name: str
    helper_type: str
    helper_label: str
    available_anchors: set[str] = field(default_factory=set)
    calm_bonus: int = 0
    crowd_size: int = 0
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
    swing_text: str
    joke_word: str
    sparkle: int
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
class BriefKind:
    id: str
    label: str
    promise_text: str
    opener: str
    thanks_text: str
    closer: str
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
class Anchor:
    id: str
    label: str
    phrase: str
    flashback: str
    calm_power: int
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
class Temperament:
    id: str
    label: str
    steadiness: int
    extra_line: str
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


VENUES = {
    "library": Venue(
        id="library",
        label="the library hall",
        room_phrase="Rows of folding chairs faced a tiny stage between two tall bookcases.",
        helper_name="Ms. Wren",
        helper_type="librarian",
        helper_label="the librarian",
        available_anchors={"card", "bookmark"},
        calm_bonus=1,
        crowd_size=1,
        tags={"library", "books"},
    ),
    "school": Venue(
        id="school",
        label="the school stage",
        room_phrase="The curtain had one glittery rip, and the microphone stand leaned like a sleepy flamingo.",
        helper_name="Mr. Bell",
        helper_type="teacher",
        helper_label="the teacher",
        available_anchors={"card", "pencil", "bookmark"},
        calm_bonus=0,
        crowd_size=2,
        tags={"school", "stage"},
    ),
    "cafe": Venue(
        id="cafe",
        label="the little café corner",
        room_phrase="A chalkboard menu squeaked above the stools, and every spoon on every saucer made a tiny bright wink.",
        helper_name="Nina",
        helper_type="woman",
        helper_label="the host",
        available_anchors={"card", "pencil"},
        calm_bonus=0,
        crowd_size=1,
        tags={"cafe", "cups"},
    ),
}

PROPS = {
    "watch": Prop(
        id="watch",
        label="silver watch",
        swing_text="swung a silver watch in a slow shiny arc",
        joke_word="pickle",
        sparkle=1,
        tags={"watch", "hypnotist"},
    ),
    "spiral": Prop(
        id="spiral",
        label="spiral card",
        swing_text="held up a black-and-white spiral card and twirled it in little circles",
        joke_word="marshmallow",
        sparkle=2,
        tags={"spiral", "hypnotist"},
    ),
    "coin": Prop(
        id="coin",
        label="glitter coin",
        swing_text="flipped a glitter coin so it flashed every time it turned",
        joke_word="bananas",
        sparkle=2,
        tags={"coin", "hypnotist"},
    ),
}

BRIEFS = {
    "welcome": BriefKind(
        id="welcome",
        label="welcome note",
        promise_text="a brief welcome before the show",
        opener="Good evening, everyone.",
        thanks_text="Thank you for coming to our funny little night of words and wonders.",
        closer="That was my whole brief speech.",
        tags={"welcome"},
    ),
    "thanks": BriefKind(
        id="thanks",
        label="thank-you note",
        promise_text="a brief thank-you after the raffle",
        opener="Hello, kind friends.",
        thanks_text="Thank you for filling the room with claps, laughter, and patient ears.",
        closer="That was brief, just as promised.",
        tags={"thanks"},
    ),
    "reading": BriefKind(
        id="reading",
        label="book-introduction",
        promise_text="a brief introduction to a new story",
        opener="Hello, readers.",
        thanks_text="Thank you for giving a writer a quiet room and such bright eyes.",
        closer="Now the story can begin.",
        tags={"reading"},
    ),
}

ANCHORS = {
    "card": Anchor(
        id="card",
        label="index card",
        phrase="a small index card with five neat words",
        flashback='Earlier that afternoon, the writer had written a reminder: "One line. One smile. Then stop."',
        calm_power=2,
        tags={"card", "note"},
    ),
    "bookmark": Anchor(
        id="bookmark",
        label="bookmarked page",
        phrase="a stiff paper bookmark tucked inside the notes",
        flashback='The writer remembered an old reading where a bookseller had whispered, "When your words wobble, find the first sentence and trust it."',
        calm_power=1,
        tags={"bookmark", "books"},
    ),
    "pencil": Anchor(
        id="pencil",
        label="short yellow pencil",
        phrase="a short yellow pencil with bite marks near the eraser",
        flashback='A week before, the writer had practiced with a chewed pencil in hand and learned to tap once, breathe once, and speak once.',
        calm_power=2,
        tags={"pencil", "practice"},
    ),
}

TEMPERAMENTS = {
    "steady": Temperament(
        id="steady",
        label="steady",
        steadiness=1,
        extra_line="Even when nervous, the writer usually had a quiet place inside to stand.",
    ),
    "fluttery": Temperament(
        id="fluttery",
        label="fluttery",
        steadiness=0,
        extra_line="Nerves liked to flap around this writer like pigeons near dropped crumbs.",
    ),
}


# ---------------------------------------------------------------------------
# World container
# ---------------------------------------------------------------------------
class World:
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
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
        clone = World(self.venue)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
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


def _r_echo(world: World) -> list[str]:
    writer = world.get("writer")
    stage = world.get("stage")
    if writer.attrs.get("heard_trigger") != 1:
        return []
    if writer.memes["echo"] >= THRESHOLD:
        return []
    sig = ("echo",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    writer.memes["echo"] += float(writer.attrs["prop_sparkle"])
    writer.memes["dizzy"] += 1.0
    stage.meters["awkward"] += 1.0
    world.get("audience").memes["amused"] += 1.0
    return ["__echo__"]


def _r_flashback(world: World) -> list[str]:
    writer = world.get("writer")
    if writer.memes["echo"] < THRESHOLD:
        return []
    if writer.attrs.get("holding_anchor") != 1:
        return []
    sig = ("flashback",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    writer.memes["memory"] += 1.0
    return ["__flashback__"]


def _r_focus(world: World) -> list[str]:
    writer = world.get("writer")
    if writer.memes["memory"] < THRESHOLD:
        return []
    sig = ("focus",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    writer.memes["focus"] += float(writer.attrs["anchor_power"] + writer.attrs["steadiness"])
    return ["__focus__"]


def _r_settle(world: World) -> list[str]:
    writer = world.get("writer")
    if writer.memes["echo"] < THRESHOLD:
        return []
    if writer.memes["focus"] < writer.memes["echo"]:
        return []
    sig = ("settle",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    writer.memes["steady"] += 1.0
    writer.memes["echo"] = 0.0
    writer.memes["dizzy"] = 0.0
    stage = world.get("stage")
    stage.meters["awkward"] = max(0.0, stage.meters["awkward"] - 1.0)
    return ["__settled__"]


CAUSAL_RULES = [
    Rule(name="echo", tag="social", apply=_r_echo),
    Rule(name="flashback", tag="memory", apply=_r_flashback),
    Rule(name="focus", tag="emotional", apply=_r_focus),
    Rule(name="settle", tag="emotional", apply=_r_settle),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                out.extend(s for s in res if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


# ---------------------------------------------------------------------------
# Reasonableness and outcomes
# ---------------------------------------------------------------------------
def available_anchor(venue: Venue, anchor: Anchor) -> bool:
    return anchor.id in venue.available_anchors


def can_recover(prop: Prop, anchor: Anchor) -> bool:
    return anchor.calm_power >= prop.sparkle


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for venue_id, venue in VENUES.items():
        for prop_id, prop in PROPS.items():
            for anchor_id, anchor in ANCHORS.items():
                if available_anchor(venue, anchor) and can_recover(prop, anchor):
                    combos.append((venue_id, prop_id, anchor_id))
    return sorted(combos)


def outcome_of(params: "StoryParams") -> str:
    venue = VENUES[params.venue]
    prop = PROPS[params.prop]
    anchor = ANCHORS[params.anchor]
    temperament = TEMPERAMENTS[params.temperament]
    if not available_anchor(venue, anchor) or not can_recover(prop, anchor):
        return "invalid"
    score = anchor.calm_power + temperament.steadiness + venue.calm_bonus
    if score >= prop.sparkle + 2:
        return "smooth"
    return "giggly"


def explain_combo(venue: Venue, prop: Prop, anchor: Anchor) -> str:
    if not available_anchor(venue, anchor):
        options = ", ".join(sorted(venue.available_anchors))
        return (
            f"(No story: {anchor.label} is not available at {venue.label}. "
            f"That place honestly supports only these grounding tools: {options}.)"
        )
    if not can_recover(prop, anchor):
        return (
            f"(No story: {anchor.label} is too weak to break the rhythm of the "
            f"{prop.label}. The writer would keep echoing {prop.joke_word!r} "
            f"instead of finishing the brief speech.)"
        )
    return "(No story: this combination is not reasonable.)"


# ---------------------------------------------------------------------------
# Story beats
# ---------------------------------------------------------------------------
def introduce(world: World, writer: Entity, helper: Entity, brief: BriefKind, temperament: Temperament) -> None:
    world.say(
        f"{writer.id} was a writer who had promised to give {brief.promise_text} at {world.venue.label}. "
        f"{world.venue.room_phrase}"
    )
    world.say(
        f"{helper.id}, {helper.label}, kept saying the nicest scary sentence in the world: "
        f'"Just keep it brief."'
    )
    world.say(temperament.extra_line)


def bring_in_hypnotist(world: World, hypnotist: Entity, prop: Prop) -> None:
    world.say(
        f"Then the guest hypnotist arrived in a velvet jacket and {prop.swing_text}. "
        f'For a warm-up, the hypnotist told the crowd, "When I say {prop.joke_word}, nobody panic. '
        f'It is only a very silly word."'
    )


def start_repetition(world: World, writer: Entity, prop: Prop) -> None:
    writer.attrs["heard_trigger"] = 1
    propagate(world, narrate=False)
    world.say(
        f"The word bounced once around the room, and somehow it bounced twice inside {writer.id}'s head: "
        f'{prop.joke_word}, {prop.joke_word}, {prop.joke_word}.'
    )
    world.say(
        f"{writer.id} smiled in the wrong place, which is to say everywhere."
    )


def call_writer_up(world: World, writer: Entity, brief: BriefKind, prop: Prop) -> None:
    world.say(
        f"When it was time for the brief speech, {writer.id} walked to the microphone and tried to begin. "
        f'"{brief.opener}"'
    )
    world.say(
        f'But out popped, "{prop.joke_word}," and then, because one silly mistake likes company, '
        f'"{prop.joke_word}" again.'
    )


def flashback_and_anchor(world: World, writer: Entity, anchor: Anchor) -> None:
    writer.attrs["holding_anchor"] = 1
    propagate(world, narrate=False)
    world.say(
        f"{writer.id}'s fingers found {anchor.phrase}. In a tiny flashback that felt bright and useful, "
        f"{anchor.flashback}"
    )
    world.say(
        f"So {writer.id} touched the anchor, took one careful breath, and let the room stop spinning around the joke."
    )


def finish_smooth(world: World, writer: Entity, helper: Entity, brief: BriefKind, prop: Prop) -> None:
    world.say(
        f'This time the words came out in the right order. "{brief.thanks_text}" '
        f'{writer.id} said, and even managed a grin before adding, "{brief.closer}"'
    )
    world.say(
        f"The room laughed kindly, not at the writer but with the whole delicious muddle of it, and {helper.id} clapped first."
    )
    world.say(
        f"Even the hypnotist bowed and said that the shortest speech had somehow gotten the biggest cheer."
    )


def finish_giggly(world: World, writer: Entity, helper: Entity, brief: BriefKind, prop: Prop) -> None:
    world.say(
        f'{writer.id} still had one bubble of laughter left, so the speech came out like this: '
        f'"{brief.thanks_text} And no more {prop.joke_word} from me."'
    )
    world.say(
        f"That made the audience laugh even harder, which helped. Then {writer.id} finished with, "
        f'"{brief.closer}"'
    )
    world.say(
        f"{helper.id} fanned the air with the program as if a perfect comic ending had been planned all along."
    )


def closing_image(world: World, writer: Entity, hypnotist: Entity, anchor: Anchor, outcome: str) -> None:
    if outcome == "smooth":
        world.say(
            f"Afterward, the hypnotist asked for the secret, and {writer.id} held up the {anchor.label}. "
            f'"Not magic," {writer.pronoun()} said. "Just a better first line."'
        )
    else:
        world.say(
            f"Afterward, the hypnotist promised never to battle a writer carrying a {anchor.label}. "
            f"The crowd kept chuckling all the way to the biscuit table."
        )
def tell(
    prop: Prop,
    brief: Brief,
    anchor: Anchor,
    temperament: Temperament,
    writer_name: str,
    writer_type: WriterType,
    venue=None,
) -> World:
    world = World(venue)

    writer = world.add(Entity(id=writer_name, kind="character", type=writer_type, role="writer", label="the writer"))
    hypnotist = world.add(Entity(id="Rufus", kind="character", type="man", role="hypnotist", label="the hypnotist"))
    helper = world.add(
        Entity(
            id=venue.helper_name,
            kind="character",
            type=venue.helper_type,
            role="helper",
            label=venue.helper_label,
        )
    )
    stage = world.add(Entity(id="stage", type="place", label=venue.label))
    audience = world.add(Entity(id="audience", type="group", label="the audience"))
    anchor_ent = world.add(Entity(id="anchor", type="thing", label=anchor.label))

    # Initialize values read by rules before propagate()
    writer.attrs["heard_trigger"] = 0
    writer.attrs["holding_anchor"] = 0
    writer.attrs["prop_sparkle"] = prop.sparkle
    writer.attrs["anchor_power"] = anchor.calm_power
    writer.attrs["steadiness"] = temperament.steadiness
    writer.memes["echo"] = 0.0
    writer.memes["dizzy"] = 0.0
    writer.memes["memory"] = 0.0
    writer.memes["focus"] = 0.0
    writer.memes["steady"] = 0.0
    stage.meters["awkward"] = 0.0
    audience.memes["amused"] = 0.0

    introduce(world, writer, helper, brief, temperament)
    world.para()
    bring_in_hypnotist(world, hypnotist, prop)
    start_repetition(world, writer, prop)
    call_writer_up(world, writer, brief, prop)
    world.para()
    flashback_and_anchor(world, writer, anchor)

    outcome = outcome_of(
        StoryParams(
            venue=venue.id,
            prop=prop.id,
            brief=brief.id,
            anchor=anchor.id,
            writer=writer_name,
            gender=writer_type,
            temperament=temperament.id,
            seed=None,
        )
    )
    world.para()
    if outcome == "smooth":
        finish_smooth(world, writer, helper, brief, prop)
    else:
        finish_giggly(world, writer, helper, brief, prop)
    closing_image(world, writer, hypnotist, anchor, outcome)

    world.facts.update(
        venue=venue,
        prop=prop,
        brief=brief,
        anchor=anchor,
        temperament=temperament,
        writer=writer,
        helper=helper,
        hypnotist=hypnotist,
        audience=audience,
        stage=stage,
        outcome=outcome,
        repeated_word=prop.joke_word,
        flashback_used=writer.memes["memory"] >= THRESHOLD,
        brief_kept=True,
        echo_started=True,
    )
    return world


# ---------------------------------------------------------------------------
# Params
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


GIRL_NAMES = ["Mina", "Tessa", "Lulu", "Nora", "Pia", "Vera"]
BOY_NAMES = ["Milo", "Owen", "Jasper", "Theo", "Ned", "Arlo"]
@dataclass
class StoryParams:
    venue: str = "library"
    prop: str = "watch"
    brief: str = "welcome"
    anchor: str = "card"
    writer: str = "Milo"
    gender: str = "boy"
    temperament: str = "steady"
    seed: Optional[int] = None



CURATED = [
    StoryParams(
        venue="library",
        prop="watch",
        brief="welcome",
        anchor="card",
        writer="Milo",
        gender="boy",
        temperament="steady",
    ),
    StoryParams(
        venue="school",
        prop="spiral",
        brief="thanks",
        anchor="pencil",
        writer="Tessa",
        gender="girl",
        temperament="fluttery",
    ),
    StoryParams(
        venue="cafe",
        prop="coin",
        brief="reading",
        anchor="card",
        writer="Arlo",
        gender="boy",
        temperament="steady",
    ),
    StoryParams(
        venue="library",
        prop="watch",
        brief="reading",
        anchor="bookmark",
        writer="Nora",
        gender="girl",
        temperament="fluttery",
    ),
]


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "hypnotist": [
        (
            "What does a hypnotist do in stories and stage shows?",
            "A hypnotist is a performer who uses voice, rhythm, and attention tricks to guide what people notice. In a comedy story, that can make people act silly or extra suggestible for a moment."
        )
    ],
    "brief": [
        (
            "What does brief mean when someone gives a speech?",
            "Brief means short and not too long. A brief speech says the important part and then stops."
        )
    ],
    "writer": [
        (
            "What does a writer do?",
            "A writer makes stories, notes, poems, or speeches out of words. Writers often plan their first line carefully so the rest can follow."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a quick look back at something that happened earlier. It helps explain why a character knows what to do now."
        )
    ],
    "repetition": [
        (
            "What is repetition in a funny story?",
            "Repetition is when a word or action happens again and again. It can be funny because each repeat makes the pattern clearer and sillier."
        )
    ],
    "card": [
        (
            "Why can a small note card help someone speak?",
            "A note card can hold just the key words, so a speaker does not have to remember every sentence. Touching it can also help them slow down and focus."
        )
    ],
    "bookmark": [
        (
            "How can a bookmark help a reader or speaker?",
            "A bookmark helps you find the exact place you want to start. That can calm you because you know where your first line lives."
        )
    ],
    "pencil": [
        (
            "Why do some people hold a pencil when they practice speaking?",
            "A pencil gives restless fingers something simple to do. That small habit can help the body feel steady."
        )
    ],
}
KNOWLEDGE_ORDER = ["hypnotist", "brief", "writer", "flashback", "repetition", "card", "bookmark", "pencil"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    writer = f["writer"]
    venue = f["venue"]
    brief = f["brief"]
    prop = f["prop"]
    outcome = f["outcome"]
    tone = "finishes smoothly after a flashback helps" if outcome == "smooth" else "turns the mistake into a laugh and finishes anyway"
    return [
        f'Write a comedy story for a young child that includes the words "hypnotist," "brief," and "writer."',
        f"Tell a funny story set at {venue.label} where a writer has promised {brief.promise_text}, but a hypnotist with a {prop.label} makes one silly word repeat until the writer remembers what to do.",
        f"Write a child-friendly story using repetition and a flashback, where the writer {tone}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    writer = f["writer"]
    helper = f["helper"]
    venue = f["venue"]
    prop = f["prop"]
    brief = f["brief"]
    anchor = f["anchor"]
    repeated = f["repeated_word"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {writer.id}, a writer who had promised a brief speech, and a stage hypnotist who accidentally scrambled that plan. The helper at {venue.label} also matters because that grown-up keeps the moment kind instead of scary."
        ),
        (
            "What problem happened before the speech?",
            f"The hypnotist used a funny warm-up word, and it got stuck in {writer.id}'s head. That is why the writer started repeating {repeated!r} instead of smoothly beginning the speech."
        ),
        (
            "Where does the flashback happen, and why does it help?",
            f"The flashback happens when {writer.id} touches the {anchor.label}. It helps because the earlier advice gives the writer one clear starting move: breathe, trust the first line, and speak again."
        ),
        (
            "Why is the speech called brief in the story?",
            f"It is called brief because the writer promised to keep it short. That promise matters later, because once the writer recovers, the speech works best by saying only the warm important part and then stopping."
        ),
    ]
    if outcome == "smooth":
        qa.append(
            (
                "How did the writer solve the problem?",
                f"{writer.id} used the {anchor.label} as a grounding anchor and remembered earlier advice in a flashback. That broke the repeating rhythm, so the writer could say the real thank-you lines clearly."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a clean, funny success: the audience cheered and even the hypnotist laughed. The ending proves the writer changed from wobbly and distracted to calm enough to finish the brief speech."
            )
        )
    else:
        qa.append(
            (
                "Did the writer stop being funny after the flashback?",
                f"Not completely, and that is part of the comedy. The flashback helped enough for {writer.id} to steer the joke instead of being trapped by it, so the speech finished with laughter and control."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended in a giggly success. The writer still made the audience laugh, but now on purpose, and then finished the brief speech instead of getting lost in repetition."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"hypnotist", "brief", "writer", "flashback", "repetition", world.facts["anchor"].id}
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
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(V, P, A) :- venue(V), prop(P), anchor(A), available(V, A), calm(A, C), sparkle(P, S), C >= S.

% --- ending quality --------------------------------------------------------
score(Total) :- chosen_venue(V), chosen_prop(P), chosen_anchor(A), chosen_temperament(T),
                calm(A, C), steadiness(T, St), calm_bonus(V, B), Total = C + St + B.
outcome(smooth) :- chosen_prop(P), sparkle(P, S), score(T), T >= S + 2.
outcome(giggly) :- valid_choice, not outcome(smooth).

valid_choice :- chosen_venue(V), chosen_prop(P), chosen_anchor(A), valid(V, P, A).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id, venue in VENUES.items():
        lines.append(asp.fact("venue", venue_id))
        lines.append(asp.fact("calm_bonus", venue_id, venue.calm_bonus))
        for anchor_id in sorted(venue.available_anchors):
            lines.append(asp.fact("available", venue_id, anchor_id))
    for prop_id, prop in PROPS.items():
        lines.append(asp.fact("prop", prop_id))
        lines.append(asp.fact("sparkle", prop_id, prop.sparkle))
    for anchor_id, anchor in ANCHORS.items():
        lines.append(asp.fact("anchor", anchor_id))
        lines.append(asp.fact("calm", anchor_id, anchor.calm_power))
    for temperament_id, temperament in TEMPERAMENTS.items():
        lines.append(asp.fact("temperament", temperament_id))
        lines.append(asp.fact("steadiness", temperament_id, temperament.steadiness))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_venue", params.venue),
            asp.fact("chosen_prop", params.prop),
            asp.fact("chosen_anchor", params.anchor),
            asp.fact("chosen_temperament", params.temperament),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "invalid"


def asp_verify() -> int:
    rc = 0

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {seed}.")
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
            print(f"Outcome mismatch for {params}: py={outcome_of(params)} asp={asp_outcome(params)}")
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"Smoke generation failed: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A comedy storyworld: a writer, a hypnotist, a brief speech, repetition, and a useful flashback."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--brief", choices=BRIEFS)
    ap.add_argument("--anchor", choices=ANCHORS)
    ap.add_argument("--writer")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--temperament", choices=TEMPERAMENTS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP facts and rules")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.venue and args.anchor:
        venue = VENUES[args.venue]
        anchor = ANCHORS[args.anchor]
        prop = PROPS[args.prop] if args.prop else next(iter(PROPS.values()))
        if not available_anchor(venue, anchor):
            raise StoryError(explain_combo(venue, prop, anchor))
    if args.prop and args.anchor:
        venue = VENUES[args.venue] if args.venue else next(iter(VENUES.values()))
        prop = PROPS[args.prop]
        anchor = ANCHORS[args.anchor]
        if not can_recover(prop, anchor):
            raise StoryError(explain_combo(venue, prop, anchor))

    combos = [
        combo
        for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.prop is None or combo[1] == args.prop)
        and (args.anchor is None or combo[2] == args.anchor)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue_id, prop_id, anchor_id = rng.choice(combos)
    brief_id = args.brief or rng.choice(sorted(BRIEFS))
    gender = args.gender or rng.choice(["girl", "boy"])
    writer = args.writer or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    temperament = args.temperament or rng.choice(sorted(TEMPERAMENTS))
    return StoryParams(
        venue=venue_id,
        prop=prop_id,
        brief=brief_id,
        anchor=anchor_id,
        writer=writer,
        gender=gender,
        temperament=temperament,
    )


def generate(params: StoryParams) -> StorySample:
    if params.venue not in VENUES:
        raise StoryError(f"(No story: unknown venue {params.venue!r}.)")
    if params.prop not in PROPS:
        raise StoryError(f"(No story: unknown prop {params.prop!r}.)")
    if params.brief not in BRIEFS:
        raise StoryError(f"(No story: unknown brief kind {params.brief!r}.)")
    if params.anchor not in ANCHORS:
        raise StoryError(f"(No story: unknown anchor {params.anchor!r}.)")
    if params.temperament not in TEMPERAMENTS:
        raise StoryError(f"(No story: unknown temperament {params.temperament!r}.)")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(No story: unsupported gender {params.gender!r}.)")

    venue = VENUES[params.venue]
    prop = PROPS[params.prop]
    brief = BRIEFS[params.brief]
    anchor = ANCHORS[params.anchor]
    temperament = TEMPERAMENTS[params.temperament]
    if not available_anchor(venue, anchor) or not can_recover(prop, anchor):
        raise StoryError(explain_combo(venue, prop, anchor))

    world = tell(
        venue=venue,
        prop=prop,
        brief=brief,
        anchor=anchor,
        temperament=temperament,
        writer_name=params.writer,
        writer_type=params.gender,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (venue, prop, anchor) combos:\n")
        for venue_id, prop_id, anchor_id in combos:
            print(f"  {venue_id:8} {prop_id:7} {anchor_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.writer}: {p.brief} at {p.venue} ({p.prop}, {p.anchor}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
