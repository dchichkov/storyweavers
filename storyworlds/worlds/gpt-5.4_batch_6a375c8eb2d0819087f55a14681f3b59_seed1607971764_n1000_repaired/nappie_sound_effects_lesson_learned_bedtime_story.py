#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/nappie_sound_effects_lesson_learned_bedtime_story.py
================================================================================

A standalone story world for a gentle bedtime tale: a child is getting ready
for sleep, tucks in a favorite baby doll wearing a nappie, and thinks a noisy
bedtime helper will make the room feel fun. Instead, the sound wakes someone
who was already drifting off. A calm grown-up helps the child notice the
difference between lively play sounds and soft bedtime sounds, then offers a
quiet way to finish the night.

The world model is small on purpose. It tracks:

- typed entities (child, parent, doll, sleeper, room, objects)
- physical meters like noise, wakefulness, and bedtime calm
- emotional memes like pride, worry, relief, and learning
- a reasonableness gate: only some objects are noisy enough to wake some
  sleepers, and only some quiet fixes are sensible bedtime responses

This script follows the Storyworld Contract used by the Storyweavers repo.
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"              # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs
# ---------------------------------------------------------------------------
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
class Mood:
    id: str
    room_open: str
    window_line: str
    bed_line: str
    ending_image: str
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
class Companion:
    id: str
    label: str
    phrase: str
    bedtime_line: str
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
class NoisyThing:
    id: str
    label: str
    phrase: str
    sound: str
    burst: str
    noise: int
    bedtime_fit: int
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
class Sleeper:
    id: str
    label: str
    phrase: str
    place: str
    wake_threshold: int
    waking_sound: str
    comfort_need: str
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
class QuietFix:
    id: str
    label: str
    phrase: str
    sense: int
    calming: int
    action: str
    after: str
    qa_text: str
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


def _r_wake(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    sleeper = world.get("sleeper")
    if room.meters["noise"] >= sleeper.attrs["wake_threshold"]:
        sig = ("wake", sleeper.id)
        if sig not in world.fired:
            world.fired.add(sig)
            sleeper.meters["awake"] += 1
            sleeper.meters["sleep"] = 0.0
            sleeper.memes["startled"] += 1
            world.get("child").memes["worry"] += 1
            world.get("parent").memes["concern"] += 1
            out.append("__wake__")
    return out


def _r_room_unsettled(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    if room.meters["noise"] >= THRESHOLD:
        sig = ("unsettled", "room")
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["calm"] = 0.0
            out.append("__room__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wake", tag="physical", apply=_r_wake),
    Rule(name="room_unsettled", tag="physical", apply=_r_room_unsettled),
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
        for sent in produced:
            world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def wakes_sleeper(thing: NoisyThing, sleeper: Sleeper) -> bool:
    return thing.noise >= sleeper.wake_threshold


def sensible_fixes() -> list[QuietFix]:
    return [fix for fix in QUIET_FIXES.values() if fix.sense >= SENSE_MIN]


def settles_enough(fix: QuietFix, sleeper: Sleeper, extra_noise: int) -> bool:
    needed = 1 + extra_noise
    if sleeper.wake_threshold >= 3:
        needed += 1
    return fix.calming >= needed


def bedtime_safe(thing: NoisyThing) -> bool:
    return thing.bedtime_fit >= 2


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_wake(world: World, thing_id: str) -> dict:
    sim = world.copy()
    do_noise(sim, sim.get(thing_id), narrate=False)
    sleeper = sim.get("sleeper")
    return {
        "awake": sleeper.meters["awake"] >= THRESHOLD,
        "room_noise": sim.get("room").meters["noise"],
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def open_story(world: World, child: Entity, mood: Mood) -> None:
    child.memes["sleepy"] += 1
    world.say(f"{mood.room_open} {mood.window_line} {mood.bed_line}")


def tuck_companion(world: World, child: Entity, companion: Companion) -> None:
    child.memes["care"] += 1
    world.say(
        f"{child.id} tucked {companion.phrase} close and whispered, "
        f'"{companion.bedtime_line}"'
    )


def introduce_sleeper(world: World, sleeper_cfg: Sleeper) -> None:
    world.say(
        f"Across the room, {sleeper_cfg.phrase} was already resting {sleeper_cfg.place}."
    )


def tempt(world: World, child: Entity, thing: NoisyThing) -> None:
    child.memes["pride"] += 1
    world.say(
        f"Then {child.id} spotted {thing.phrase} and had a bright little idea. "
        f'"I can help everyone fall asleep with a bedtime song," {child.pronoun()} said.'
    )


def warn(world: World, parent: Entity, child: Entity, thing: NoisyThing, sleeper_cfg: Sleeper) -> None:
    pred = predict_wake(world, "thing")
    world.facts["predicted_noise"] = pred["room_noise"]
    child.memes["hesitation"] += 1
    world.say(
        f'{child.id}\'s {parent.label_word} smiled gently and said, '
        f'"That {thing.label} makes a {thing.sound} sound, and {sleeper_cfg.label} '
        f'is almost asleep. Bedtime sounds need to be soft."'
    )


def choose_quietly(world: World, child: Entity, thing: NoisyThing) -> None:
    child.memes["care"] += 1
    child.memes["learning"] += 1
    world.say(
        f"{child.id} looked at {thing.phrase}, then at the sleepy room, and nodded. "
        f'{child.pronoun().capitalize()} set it down without a peep.'
    )


def insist(world: World, child: Entity, thing: NoisyThing) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'"Just one tiny sound," {child.id} promised. But the idea still felt fun, '
        f"and {child.pronoun()} gave {thing.phrase} a try."
    )


def do_noise(world: World, thing: Entity, narrate: bool = True) -> None:
    thing.meters["used"] += 1
    room = world.get("room")
    room.meters["noise"] += thing.attrs["noise"]
    propagate(world, narrate=narrate)


def sound_burst(world: World, thing_cfg: NoisyThing) -> None:
    do_noise(world, world.get("thing"))
    world.say(
        f'{thing_cfg.burst} went the {thing_cfg.label} -- {thing_cfg.sound}, '
        f'{thing_cfg.sound}, {thing_cfg.sound}! The lively sound bounced around the dark room.'
    )


def wake_scene(world: World, sleeper_cfg: Sleeper) -> None:
    if world.get("sleeper").meters["awake"] >= THRESHOLD:
        world.say(
            f"At once, {sleeper_cfg.waking_sound}. {sleeper_cfg.phrase.capitalize()} opened sleepy eyes "
            f"and began to {sleeper_cfg.comfort_need}."
        )


def regret(world: World, child: Entity, companion: Companion) -> None:
    child.memes["worry"] += 1
    world.say(
        f"{child.id} hugged {companion.phrase} and felt very small. "
        f'"Oh," {child.pronoun()} whispered. "That was not a bedtime sound."'
    )


def soothe(world: World, parent: Entity, child: Entity, sleeper_cfg: Sleeper, fix: QuietFix) -> None:
    world.get("room").meters["noise"] = 0.0
    world.get("room").meters["calm"] += 1
    world.get("sleeper").meters["awake"] = 0.0
    world.get("sleeper").meters["sleep"] += 1
    world.get("sleeper").memes["startled"] = 0.0
    child.memes["relief"] += 1
    child.memes["learning"] += 1
    parent.memes["care"] += 1
    world.say(
        f"{child.id}'s {parent.label_word} did not scold. {parent.pronoun().capitalize()} {fix.action}."
    )
    world.say(fix.after)


def lesson(world: World, parent: Entity, child: Entity, thing: NoisyThing) -> None:
    child.memes["learning"] += 1
    world.say(
        f'Then {child.id}\'s {parent.label_word} kissed the top of '
        f'{child.pronoun("possessive")} head. '
        f'"Fun sounds are for playtime," {parent.pronoun()} said softly. '
        f'"At bedtime, we choose quiet helpers so everyone can rest."'
    )
    world.say(
        f"{child.id} nodded and looked at the {thing.label} with new understanding. "
        f"{child.pronoun().capitalize()} had learned that a lively sound can feel much bigger at night."
    )


def quiet_ending(world: World, child: Entity, companion: Companion, mood: Mood, fix: QuietFix) -> None:
    child.memes["sleepy"] += 1
    child.memes["calm"] += 1
    world.say(
        f"Soon the room was soft again. {child.id} tucked {companion.phrase} in once more and kept "
        f"{fix.phrase} close."
    )
    world.say(mood.ending_image)


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    mood: Mood,
    companion: Companion,
    thing: NoisyThing,
    sleeper_cfg: Sleeper,
    fix: QuietFix,
    *,
    child_name: str = "Mila",
    child_gender: str = "girl",
    parent_type: str = "mother",
    heed_warning: bool = False,
    extra_noise: int = 0,
) -> World:
    world = World()

    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label="bedroom",
    ))
    world.add(Entity(
        id="companion",
        kind="thing",
        type="companion",
        label=companion.label,
        attrs={"tags": set(companion.tags)},
    ))
    world.add(Entity(
        id="thing",
        kind="thing",
        type="bedtime_object",
        label=thing.label,
        attrs={"noise": int(thing.noise + extra_noise), "tags": set(thing.tags)},
    ))
    world.add(Entity(
        id="sleeper",
        kind="character",
        type="baby",
        role="sleeper",
        label=sleeper_cfg.label,
        attrs={"wake_threshold": sleeper_cfg.wake_threshold},
    ))

    world.get("room").meters["calm"] = 1.0
    world.get("sleeper").meters["sleep"] = 1.0
    world.get("child").memes["care"] = 0.0
    world.get("child").memes["learning"] = 0.0
    world.get("child").memes["worry"] = 0.0
    world.get("parent").memes["care"] = 0.0
    world.get("parent").memes["concern"] = 0.0

    open_story(world, child, mood)
    tuck_companion(world, child, companion)
    introduce_sleeper(world, sleeper_cfg)

    world.para()
    tempt(world, child, thing)
    warn(world, parent, child, thing, sleeper_cfg)

    if heed_warning:
        choose_quietly(world, child, thing)
        world.para()
        soothe(world, parent, child, sleeper_cfg, fix)
        lesson(world, parent, child, thing)
        world.para()
        quiet_ending(world, child, companion, mood, fix)
        outcome = "averted"
    else:
        insist(world, child, thing)
        world.para()
        sound_burst(world, thing)
        wake_scene(world, sleeper_cfg)
        regret(world, child, companion)

        contained = settles_enough(fix, sleeper_cfg, extra_noise)
        world.para()
        if contained:
            soothe(world, parent, child, sleeper_cfg, fix)
            lesson(world, parent, child, thing)
            world.para()
            quiet_ending(world, child, companion, mood, fix)
            outcome = "settled"
        else:
            soothe(world, parent, child, sleeper_cfg, fix)
            world.say(
                "It took a long while for the room to grow still again, and everyone felt heavy with tiredness."
            )
            lesson(world, parent, child, thing)
            world.para()
            world.say(
                f"At last, the house quieted. {child.id} kept the noisy toy on the shelf, held {companion.phrase}, "
                f"and listened to the plain, gentle hush of nighttime instead."
            )
            outcome = "frazzled"

    world.facts.update(
        mood=mood,
        companion=companion,
        noisy_thing=thing,
        sleeper_cfg=sleeper_cfg,
        fix=fix,
        child=child,
        parent=parent,
        heed_warning=heed_warning,
        extra_noise=extra_noise,
        outcome=outcome,
        sleeper_woke=(not heed_warning and wakes_sleeper(NoisyThing(
            id=thing.id,
            label=thing.label,
            phrase=thing.phrase,
            sound=thing.sound,
            burst=thing.burst,
            noise=thing.noise + extra_noise,
            bedtime_fit=thing.bedtime_fit,
            tags=set(thing.tags),
        ), sleeper_cfg)),
        settled=(outcome == "settled"),
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
MOODS = {
    "moon": Mood(
        id="moon",
        room_open="The moon poured a silver square onto the bedroom floor.",
        window_line="Outside, the night garden stood very still.",
        bed_line="Inside, blankets made a warm little cave for sleep.",
        ending_image="Before long, only the moon was awake, laying quiet light over the room.",
        tags={"moon", "bedtime"},
    ),
    "rain": Mood(
        id="rain",
        room_open="Rain tapped softly at the window while the bedroom lamps were already dim.",
        window_line="The clouds outside looked like folded gray blankets.",
        bed_line="Inside, the bed was warm and the pillows smelled clean and sleepy.",
        ending_image="Soon the rain was the only sound left, a soft shhh-shhh outside the window.",
        tags={"rain", "bedtime"},
    ),
    "stars": Mood(
        id="stars",
        room_open="Tiny star stickers glimmered on the ceiling in the half-dark room.",
        window_line="Beyond the curtains, the sky looked deep and velvety.",
        bed_line="Inside, every blanket corner seemed ready for a dream.",
        ending_image="In the end, the stars above and the room below both felt hushed and kind.",
        tags={"stars", "bedtime"},
    ),
}

COMPANIONS = {
    "doll": Companion(
        id="doll",
        label="baby doll",
        phrase="her baby doll in a tiny nappie",
        bedtime_line="You sleep here beside me, little one.",
        tags={"doll", "nappie"},
    ),
    "rabbit": Companion(
        id="rabbit",
        label="cloth rabbit",
        phrase="a cloth rabbit wearing a little doll's nappie like a funny night skirt",
        bedtime_line="You can sleep first, and I will be quiet too.",
        tags={"rabbit", "nappie"},
    ),
    "bear": Companion(
        id="bear",
        label="sleepy bear",
        phrase="a sleepy plush bear with a soft nappie tucked around its middle",
        bedtime_line="Tonight is for resting paws and resting eyes.",
        tags={"bear", "nappie"},
    ),
}

NOISY_THINGS = {
    "tambourine": NoisyThing(
        id="tambourine",
        label="tambourine",
        phrase="the little tambourine",
        sound="jingle-jingle",
        burst="JINGLE-JINGLE",
        noise=3,
        bedtime_fit=0,
        tags={"music", "noise"},
    ),
    "duck": NoisyThing(
        id="duck",
        label="squeaky duck",
        phrase="the squeaky duck",
        sound="squeak",
        burst="SQUEAK",
        noise=2,
        bedtime_fit=1,
        tags={"squeak", "noise"},
    ),
    "drum": NoisyThing(
        id="drum",
        label="toy drum",
        phrase="the toy drum",
        sound="boom-boom",
        burst="BOOM-BOOM",
        noise=4,
        bedtime_fit=0,
        tags={"drum", "noise"},
    ),
    "music_box": NoisyThing(
        id="music_box",
        label="music box",
        phrase="the music box",
        sound="plink-plink",
        burst="PLINK-PLINK",
        noise=1,
        bedtime_fit=2,
        tags={"music_box", "quiet"},
    ),
}

SLEEPERS = {
    "baby": Sleeper(
        id="baby",
        label="the baby",
        phrase="the baby in the crib",
        place="in a crib near the wall",
        wake_threshold=2,
        waking_sound="the baby blinked and wobbled a little lip",
        comfort_need="fuss",
        tags={"baby", "sleep"},
    ),
    "brother": Sleeper(
        id="brother",
        label="big brother",
        phrase="big brother in the top bunk",
        place="in the top bunk above the toy shelf",
        wake_threshold=3,
        waking_sound="big brother sat up with a groggy little grunt",
        comfort_need="rub his eyes and mumble",
        tags={"sibling", "sleep"},
    ),
    "sister": Sleeper(
        id="sister",
        label="big sister",
        phrase="big sister in the trundle bed",
        place="in the trundle bed by the book basket",
        wake_threshold=3,
        waking_sound="big sister pushed her blanket down with a sleepy sigh",
        comfort_need="blink and whisper for quiet",
        tags={"sibling", "sleep"},
    ),
}

QUIET_FIXES = {
    "hum": QuietFix(
        id="hum",
        label="humming",
        phrase="a little humming",
        sense=3,
        calming=2,
        action="gathered the child close and hummed a slow mmm-mmm song until the sharp moment melted away",
        after="The worried faces softened. The crib and the corners of the room seemed to breathe more slowly.",
        qa_text="hummed softly until the room felt calm again",
        tags={"hum", "quiet"},
    ),
    "pat": QuietFix(
        id="pat",
        label="gentle patting",
        phrase="gentle patting",
        sense=3,
        calming=3,
        action="rocked the sleepy one, gave a few gentle pats, and let the quiet return in tiny waves",
        after="Little by little, the fussing faded. The whole room loosened back into bedtime.",
        qa_text="rocked and gently patted until everyone settled",
        tags={"pat", "quiet"},
    ),
    "nightlight": QuietFix(
        id="nightlight",
        label="night-light",
        phrase="the soft night-light",
        sense=2,
        calming=2,
        action="clicked on the soft night-light and whispered a calm good-night",
        after="The warm glow made the dark feel friendly instead of exciting, and the room remembered how to be still.",
        qa_text="turned on the night-light and spoke in a calm whisper",
        tags={"nightlight", "quiet", "light"},
    ),
    "tickle": QuietFix(
        id="tickle",
        label="tickle game",
        phrase="a tickle game",
        sense=1,
        calming=0,
        action="started a silly tickle game",
        after="It only made the room busier.",
        qa_text="started a tickle game",
        tags={"bad_fix"},
    ),
}

GIRL_NAMES = ["Mila", "Lily", "Ava", "Nora", "Zoe", "Maya", "Ella", "Lucy"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Finn", "Theo", "Eli", "Noah"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mood_id in MOODS:
        for thing_id, thing in NOISY_THINGS.items():
            for sleeper_id, sleeper in SLEEPERS.items():
                if wakes_sleeper(thing, sleeper):
                    combos.append((mood_id, thing_id, sleeper_id))
    return combos


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    mood: str
    companion: str
    noisy_thing: str
    sleeper: str
    quiet_fix: str
    child_name: str
    child_gender: str
    parent: str
    heed_warning: bool = False
    extra_noise: int = 0
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
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
    "nappie": [
        (
            "What is a nappie?",
            "A nappie is a soft diaper for a baby or a doll. It helps keep a little one clean and dry."
        )
    ],
    "sleep": [
        (
            "Why do people use quiet voices at bedtime?",
            "Quiet voices help brains and bodies slow down for sleep. Loud sounds can wake someone who was almost resting."
        )
    ],
    "noise": [
        (
            "Why can a loud toy feel louder at night?",
            "At night the room is already still, so a jingle or boom stands out more. That is why bedtime usually needs softer sounds."
        )
    ],
    "hum": [
        (
            "Why can humming help at bedtime?",
            "A soft hum is steady and gentle, so it can make a room feel calm. It does not jump out the way a sharp toy sound does."
        )
    ],
    "nightlight": [
        (
            "What does a night-light do?",
            "A night-light gives a small, gentle glow so the dark feels less scary. It helps without making a noisy fuss."
        )
    ],
    "music_box": [
        (
            "Why is a quiet music box better for bedtime than a drum?",
            "A quiet music box makes a soft sound instead of a big one. That makes it kinder to sleepy ears."
        )
    ],
    "baby": [
        (
            "Why do babies wake up easily?",
            "Babies are still learning sleep routines, so sudden sounds can wake them fast. Gentle quiet helps them rest."
        )
    ],
    "sibling": [
        (
            "Why should we think about other people when getting ready for bed?",
            "Other people may already be tired or asleep. A kind bedtime choice helps everyone in the room rest."
        )
    ],
}
KNOWLEDGE_ORDER = ["nappie", "sleep", "noise", "baby", "sibling", "hum", "nightlight", "music_box"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    thing = f["noisy_thing"]
    companion = f["companion"]
    sleeper = f["sleeper_cfg"]
    if f["outcome"] == "averted":
        return [
            f'Write a gentle bedtime story for a 3-to-5-year-old that includes the word "nappie" and a child who decides not to make a noisy sound.',
            f"Tell a calm story where {child.id} tucks in {companion.phrase} and almost uses a {thing.label}, but listens when a parent explains that {sleeper.label} is sleeping.",
            'Write a bedtime story with soft sound effects and a lesson learned about choosing quiet helpers at night.',
        ]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the word "nappie", uses sound effects, and ends with a lesson learned.',
        f"Tell a sleepy nighttime story where {child.id} tucks in {companion.phrase}, makes a noisy sound with a {thing.label}, and then learns why bedtime needs gentler sounds.",
        f"Write a child-facing story in which a sound wakes {sleeper.label}, a calm grown-up helps, and the ending proves the room became peaceful again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    companion = f["companion"]
    thing = f["noisy_thing"]
    sleeper = f["sleeper_cfg"]
    fix = f["fix"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child getting ready for bed, {child.pronoun('possessive')} favorite companion, and {child.pronoun('possessive')} {parent.label_word} who helps keep the room calm."
        ),
        (
            f"What was special about {companion.label}?",
            f"{companion.label.capitalize()} was tucked in for bed and had a nappie in the story. That bedtime detail made {child.id} want to care for it very gently."
        ),
        (
            f"Why did {child.id} want to use the {thing.label}?",
            f"{child.id} thought the sound would make bedtime feel fun and helpful. The idea seemed clever until it met a room that was already trying to sleep."
        ),
        (
            f"Why was the {thing.label} a problem at bedtime?",
            f"It made a {thing.sound} sound that was too lively for the sleepy room. {sleeper.label.capitalize()} was already resting, so the noise could wake {sleeper.label}."
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"What did {child.id} do after the warning?",
            f"{child.id} set the noisy toy down and chose quiet instead. That kind choice protected the sleepy room before anyone woke up."
        ))
    else:
        qa.append((
            f"What happened when {child.id} used the {thing.label}?",
            f"The room filled with {thing.sound} sounds, and {sleeper.label} woke up. The turn in the story came from one playful noise landing in a bedtime place."
        ))
        qa.append((
            f"How did {child.id}'s {parent.label_word} help?",
            f"{parent.label_word.capitalize()} {fix.qa_text}. The grown-up answered the problem with a quieter method instead of more excitement."
        ))
    qa.append((
        "What lesson did the child learn?",
        f"{child.id} learned that fun sounds belong to playtime, but bedtime needs soft helpers. Quiet choices care for other sleepy people as well as for the child."
    ))
    if outcome == "frazzled":
        qa.append((
            "How did the ending show that something had changed?",
            f"The room did grow quiet again, but only after a long tired stretch. In the end, the noisy toy stayed on the shelf and the child listened to the hush of nighttime instead."
        ))
    else:
        qa.append((
            "How did the ending show that the room was peaceful again?",
            f"The story ends with a calm room, a tucked-in companion, and only soft bedtime sounds left. That ending image proves the child chose a gentler way to finish the night."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"sleep", "noise"}
    tags |= set(f["companion"].tags)
    tags |= set(f["sleeper_cfg"].tags)
    tags |= set(f["fix"].tags)
    if f["noisy_thing"].id == "music_box":
        tags.add("music_box")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        attrs = {k: v for k, v in e.attrs.items() if v or isinstance(v, int)}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        mood="moon",
        companion="doll",
        noisy_thing="duck",
        sleeper="baby",
        quiet_fix="hum",
        child_name="Mila",
        child_gender="girl",
        parent="mother",
        heed_warning=False,
        extra_noise=0,
    ),
    StoryParams(
        mood="rain",
        companion="bear",
        noisy_thing="tambourine",
        sleeper="brother",
        quiet_fix="pat",
        child_name="Leo",
        child_gender="boy",
        parent="father",
        heed_warning=False,
        extra_noise=0,
    ),
    StoryParams(
        mood="stars",
        companion="rabbit",
        noisy_thing="drum",
        sleeper="sister",
        quiet_fix="nightlight",
        child_name="Ava",
        child_gender="girl",
        parent="mother",
        heed_warning=False,
        extra_noise=1,
    ),
    StoryParams(
        mood="moon",
        companion="doll",
        noisy_thing="tambourine",
        sleeper="baby",
        quiet_fix="hum",
        child_name="Noah",
        child_gender="boy",
        parent="father",
        heed_warning=True,
        extra_noise=0,
    ),
]


def explain_rejection(thing: NoisyThing, sleeper: Sleeper) -> str:
    return (
        f"(No story: the {thing.label} is not noisy enough to wake {sleeper.label} here, "
        f"so the bedtime mistake would not create a real problem to fix.)"
    )


def explain_fix(rid: str) -> str:
    fix = QUIET_FIXES[rid]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing quiet fix '{rid}': it scores too low on bedtime common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.heed_warning:
        return "averted"
    sleeper = SLEEPERS[params.sleeper]
    fix = QUIET_FIXES[params.quiet_fix]
    if settles_enough(fix, sleeper, params.extra_noise):
        return "settled"
    return "frazzled"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hazard(Tg, Sl) :- noisy_thing(Tg), sleeper(Sl), noise(Tg, N), wake_threshold(Sl, W), N >= W.
sensible_fix(F) :- quiet_fix(F), sense(F, S), sense_min(M), S >= M.
valid(M, Tg, Sl) :- mood(M), hazard(Tg, Sl).

needed(Sl, 1) :- sleeper(Sl), wake_threshold(Sl, W), W < 3.
needed(Sl, 2) :- sleeper(Sl), wake_threshold(Sl, W), W >= 3.

extra(0) :- not extra(1), not extra(2).
settle_need(Sl, K + E) :- needed(Sl, K), extra(E).
contained :- chosen_fix(F), calming(F, C), chosen_sleeper(Sl), settle_need(Sl, N), C >= N.
averted :- heed_warning.
outcome(averted) :- averted.
outcome(settled) :- not averted, contained.
outcome(frazzled) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mood_id in MOODS:
        lines.append(asp.fact("mood", mood_id))
    for tid, thing in NOISY_THINGS.items():
        lines.append(asp.fact("noisy_thing", tid))
        lines.append(asp.fact("noise", tid, thing.noise))
        lines.append(asp.fact("bedtime_fit", tid, thing.bedtime_fit))
    for sid, sleeper in SLEEPERS.items():
        lines.append(asp.fact("sleeper", sid))
        lines.append(asp.fact("wake_threshold", sid, sleeper.wake_threshold))
    for fid, fix in QUIET_FIXES.items():
        lines.append(asp.fact("quiet_fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("calming", fid, fix.calming))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_fixes() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_fix/1."))
    return sorted(f for (f,) in asp.atoms(model, "sensible_fix"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_sleeper", params.sleeper),
        asp.fact("chosen_fix", params.quiet_fix),
        asp.fact("extra", params.extra_noise),
        *([asp.fact("heed_warning")] if params.heed_warning else []),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    c_valid, p_valid = set(asp_valid_combos()), set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_fixes = set(asp_sensible_fixes())
    p_fixes = {fix.id for fix in sensible_fixes()}
    if c_fixes == p_fixes:
        print(f"OK: sensible fixes match ({sorted(c_fixes)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(c_fixes)} python={sorted(p_fixes)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    mismatches = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bedtime noise, a sleepy room, and a gentle lesson learned."
    )
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--noisy-thing", dest="noisy_thing", choices=NOISY_THINGS)
    ap.add_argument("--sleeper", choices=SLEEPERS)
    ap.add_argument("--quiet-fix", dest="quiet_fix", choices=QUIET_FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--heed-warning", action="store_true",
                    help="the child listens before making the noise")
    ap.add_argument("--extra-noise", type=int, choices=[0, 1, 2],
                    help="how much bigger the sound feels in the room")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.noisy_thing and args.sleeper:
        thing = NOISY_THINGS[args.noisy_thing]
        sleeper = SLEEPERS[args.sleeper]
        if not wakes_sleeper(thing, sleeper):
            raise StoryError(explain_rejection(thing, sleeper))
    if args.quiet_fix and QUIET_FIXES[args.quiet_fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.quiet_fix))

    combos = [
        combo for combo in valid_combos()
        if (args.mood is None or combo[0] == args.mood)
        and (args.noisy_thing is None or combo[1] == args.noisy_thing)
        and (args.sleeper is None or combo[2] == args.sleeper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mood, noisy_thing, sleeper = rng.choice(sorted(combos))
    companion = args.companion or rng.choice(sorted(COMPANIONS))
    quiet_fix = args.quiet_fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    extra_noise = args.extra_noise if args.extra_noise is not None else rng.choice([0, 0, 1])
    heed_warning = bool(args.heed_warning) or rng.choice([False, False, True])

    return StoryParams(
        mood=mood,
        companion=companion,
        noisy_thing=noisy_thing,
        sleeper=sleeper,
        quiet_fix=quiet_fix,
        child_name=child_name,
        child_gender=gender,
        parent=parent,
        heed_warning=heed_warning,
        extra_noise=extra_noise,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mood not in MOODS:
        raise StoryError(f"(Unknown mood: {params.mood})")
    if params.companion not in COMPANIONS:
        raise StoryError(f"(Unknown companion: {params.companion})")
    if params.noisy_thing not in NOISY_THINGS:
        raise StoryError(f"(Unknown noisy thing: {params.noisy_thing})")
    if params.sleeper not in SLEEPERS:
        raise StoryError(f"(Unknown sleeper: {params.sleeper})")
    if params.quiet_fix not in QUIET_FIXES:
        raise StoryError(f"(Unknown quiet fix: {params.quiet_fix})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown child gender: {params.child_gender})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")
    if QUIET_FIXES[params.quiet_fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(params.quiet_fix))
    if not wakes_sleeper(NOISY_THINGS[params.noisy_thing], SLEEPERS[params.sleeper]):
        raise StoryError(explain_rejection(NOISY_THINGS[params.noisy_thing], SLEEPERS[params.sleeper]))

    world = tell(
        MOODS[params.mood],
        COMPANIONS[params.companion],
        NOISY_THINGS[params.noisy_thing],
        SLEEPERS[params.sleeper],
        QUIET_FIXES[params.quiet_fix],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        heed_warning=params.heed_warning,
        extra_noise=params.extra_noise,
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
        print(asp_program("", "#show valid/3.\n#show sensible_fix/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible_fixes())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mood, noisy_thing, sleeper) combos:\n")
        for mood, thing, sleeper in combos:
            print(f"  {mood:8} {thing:12} {sleeper}")
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
            header = (
                f"### {p.child_name}: {p.noisy_thing} at bedtime "
                f"({p.mood}, {p.sleeper}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
