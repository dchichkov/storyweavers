#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/therapy_ist_dream_octagon_mystery_to_solve.py
========================================================================

A standalone storyworld about a child who wakes from a scary dream, hears a
night sound, and has to solve a small bedtime mystery. The world models fear,
clues, comfort, and a physical source of noise. The story always includes the
words "therapy-ist", "dream", and "octagon", and centers a gentle conflict:
the child thinks the dream may have crept into the room, while a calm grown-up
urges looking for clues first.

Run it
------
    python storyworlds/worlds/gpt-5.4/therapy_ist_dream_octagon_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/therapy_ist_dream_octagon_mystery_to_solve.py --source branch_window --action peek_curtain
    python storyworlds/worlds/gpt-5.4/therapy_ist_dream_octagon_mystery_to_solve.py --source ceiling_mobile --action tighten_mobile
    python storyworlds/worlds/gpt-5.4/therapy_ist_dream_octagon_mystery_to_solve.py --source floor_drum --action peek_curtain
    python storyworlds/worlds/gpt-5.4/therapy_ist_dream_octagon_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/therapy_ist_dream_octagon_mystery_to_solve.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/therapy_ist_dream_octagon_mystery_to_solve.py --qa --json
    python storyworlds/worlds/gpt-5.4/therapy_ist_dream_octagon_mystery_to_solve.py --verify
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
LOUD_STARTLE = 2


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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)
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
class Dream:
    id: str
    image: str
    fear_line: str
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
class Source:
    id: str
    label: str
    place: str
    sound: str
    reveal_line: str
    fix_line: str
    clue_actions: set[str] = field(default_factory=set)
    loudness: int = 1
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
class Action:
    id: str
    text: str
    tool_line: str
    reveal_phrase: str
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
class Comfort:
    id: str
    phrase: str
    animal: str
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


def _r_noise_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    room = world.get("room")
    if room.meters["noise"] >= THRESHOLD and child.memes["fear"] >= THRESHOLD:
        sig = ("worry", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_reveal_calm(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    source = world.get("source")
    if source.meters["revealed"] >= THRESHOLD:
        sig = ("calm_after_reveal", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] = 0.0
            child.memes["worry"] = 0.0
            child.memes["curiosity"] += 1
            child.memes["calm"] += 1
            out.append("__calm__")
    return out


def _r_hug_steadies(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["hugged"] >= THRESHOLD:
        sig = ("hug_steadies", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["calm"] += 1
            child.memes["bravery"] += 1
            helper.memes["care"] += 1
            out.append("__hug__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="noise_worry", tag="emotional", apply=_r_noise_worry),
    Rule(name="reveal_calm", tag="emotional", apply=_r_reveal_calm),
    Rule(name="hug_steadies", tag="social", apply=_r_hug_steadies),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                produced.extend(s for s in sent if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def action_reveals(source: Source, action: Action) -> bool:
    return action.id in source.clue_actions


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for dream_id in DREAMS:
        for source_id, source in SOURCES.items():
            for action_id, action in ACTIONS.items():
                if action_reveals(source, action):
                    combos.append((dream_id, source_id, action_id))
    return combos


def explain_rejection(source: Source, action: Action) -> str:
    valid = ", ".join(sorted(source.clue_actions))
    return (
        f"(No story: {action.id} does not honestly reveal what is making the sound at "
        f"{source.place}. To solve this mystery, choose an action that matches the source, "
        f"such as: {valid}.)"
    )


def outcome_of(params: "StoryParams") -> str:
    source = SOURCES[params.source]
    if params.approach == "alone_first" and source.loudness >= LOUD_STARTLE:
        return "startled"
    return "steady"


def predict_reveal(world: World, source_id: str, action_id: str) -> dict:
    sim = world.copy()
    if action_id in sim.facts["source_cfg"].clue_actions:
        sim.get("source").meters["revealed"] += 1
        propagate(sim, narrate=False)
    return {
        "revealed": sim.get("source").meters["revealed"] >= THRESHOLD,
        "calm": sim.get("child").memes["calm"],
    }


def bedtime_setup(world: World, child: Entity, helper: Entity, comfort: Comfort, dream: Dream) -> None:
    child.memes["sleepy"] += 1
    child.memes["love"] += 1
    world.say(
        f"At bedtime, {child.id} curled beneath a soft blanket and tucked {comfort.phrase} under one arm. "
        f"{child.pronoun('possessive').capitalize()} helper at home was a grown-up, but {child.pronoun()} liked to joke "
        f"that the little {comfort.animal} was a tiny therapy-ist because it listened without interrupting."
    )
    world.say(
        f"Soon {child.pronoun()} drifted into a dream about {dream.image}."
    )


def wake_to_noise(world: World, child: Entity, source: Source, dream: Dream) -> None:
    room = world.get("room")
    room.meters["noise"] += 1
    child.memes["fear"] += 1
    child.meters["heartbeats"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But in the middle of the night, {source.sound} came from {source.place}, and {child.id}'s eyes flew open."
    )
    world.say(
        f'{dream.fear_line} "{child.pronoun().capitalize()} think it followed me out of my dream," '
        f'{child.pronoun()} whispered.'
    )


def call_helper(world: World, child: Entity, helper: Entity) -> None:
    helper.memes["care"] += 1
    world.say(
        f"{child.id} called softly, and {child.pronoun('possessive')} {helper.label_word} came in with quiet steps."
    )


def conflict(world: World, child: Entity, helper: Entity, outcome: str) -> None:
    child.memes["insists"] += 1
    helper.memes["patience"] += 1
    if outcome == "startled":
        child.memes["fear"] += 1
        world.say(
            f'"It is the dream thing," {child.id} insisted. "{child.pronoun().capitalize()} do not want to look." '
            f'But {helper.label_word} shook {helper.pronoun("possessive")} head gently.'
        )
    else:
        world.say(
            f'"It is the dream thing," {child.id} said, clutching the blanket. '
            f'But {helper.label_word} sat on the edge of the bed and spoke in a slow, warm voice.'
        )
    world.say(
        f'"Scary feelings can be real feelings," {helper.pronoun()} said, '
        f'"but that does not mean every sound is a monster. Let us look for a clue together."'
    )


def hug_first(world: World, child: Entity, helper: Entity, comfort: Comfort) -> None:
    child.memes["hugged"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.label_word.capitalize()} wrapped one arm around {child.id}, and {child.id} squeezed {comfort.phrase} tighter."
    )


def alone_peek(world: World, child: Entity, action: Action, source: Source) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"Before moving closer, {child.id} took one tiny breath and tried to {action.text}."
    )
    if source.loudness >= LOUD_STARTLE:
        child.memes["fear"] += 1
        child.meters["startle"] += 1
        world.say(
            f"But the sound came again, a little louder this time, and {child.pronoun()} scooted back across the pillow."
        )


def investigate(world: World, child: Entity, helper: Entity, source: Source, action: Action) -> None:
    pred = predict_reveal(world, source.id, action.id)
    world.facts["predicted_revealed"] = pred["revealed"]
    child.memes["curiosity"] += 1
    world.say(action.tool_line)
    world.say(
        f"Together they moved closer to {source.place} so they could {action.reveal_phrase}."
    )
    world.get("source").meters["revealed"] += 1
    propagate(world, narrate=False)
    world.say(source.reveal_line)


def fix_source(world: World, helper: Entity, source: Source) -> None:
    world.get("room").meters["noise"] = 0.0
    world.get("source").meters["settled"] += 1
    helper.meters["helped"] += 1
    world.say(
        f"{helper.label_word.capitalize()} {source.fix_line}. After that, the room grew quiet again."
    )


def lesson(world: World, child: Entity, helper: Entity, source: Source) -> None:
    child.memes["lesson"] += 1
    child.memes["trust"] += 1
    world.say(
        f'"See?" {helper.label_word.capitalize()} whispered. "The sound came from {source.label}, not from the dream."'
    )
    world.say(
        f'"Next time I feel scared, I can ask for help and look for clues first," {child.id} said. '
        f'That made {helper.label_word} smile.'
    )


def sleep_end(world: World, child: Entity, comfort: Comfort) -> None:
    child.memes["sleepy"] += 1
    world.say(
        f"Back in bed, {child.id} watched the moon paint a pale octagon of light on the wall."
    )
    world.say(
        f"Soon {child.pronoun()} was hugging {comfort.phrase} and drifting toward a softer dream, "
        f"with the mystery solved and the room at peace."
    )


def tell(
    dream: Dream,
    source_cfg: Source,
    action_cfg: Action,
    comfort_cfg: Comfort,
    child_name: str = "Nora",
    child_gender: str = "girl",
    helper_type: str = "mother",
    approach: str = "together",
    trait: str = "thoughtful",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child", traits=[trait]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label="the helper", role="helper"))
    room = world.add(Entity(id="room", type="room", label="bedroom"))
    source = world.add(Entity(id="source", type="source", label=source_cfg.label, role="source"))
    comfort = world.add(Entity(id="comfort", type="comfort", label=comfort_cfg.animal, role="comfort"))
    child.attrs["display_name"] = child_name
    helper.attrs["display_name"] = helper.label_word
    world.facts.update(
        child=child,
        helper=helper,
        room=room,
        source=source,
        comfort=comfort,
        dream_cfg=dream,
        source_cfg=source_cfg,
        action_cfg=action_cfg,
        comfort_cfg=comfort_cfg,
        approach=approach,
    )

    bedtime_setup(world, child, helper, comfort_cfg, dream)
    world.para()
    wake_to_noise(world, child, source_cfg, dream)
    call_helper(world, child, helper)
    outcome = "startled" if approach == "alone_first" and source_cfg.loudness >= LOUD_STARTLE else "steady"
    conflict(world, child, helper, outcome)
    if approach == "alone_first":
        alone_peek(world, child, action_cfg, source_cfg)
    world.para()
    hug_first(world, child, helper, comfort_cfg)
    investigate(world, child, helper, source_cfg, action_cfg)
    fix_source(world, helper, source_cfg)
    world.para()
    lesson(world, child, helper, source_cfg)
    sleep_end(world, child, comfort_cfg)

    world.facts.update(
        outcome=outcome,
        solved=world.get("source").meters["revealed"] >= THRESHOLD,
        settled=world.get("room").meters["noise"] < THRESHOLD,
        lesson_learned=child.memes["lesson"] >= THRESHOLD,
    )
    return world


DREAMS = {
    "moon_boat": Dream(
        id="moon_boat",
        image="a silver boat sailing over sleepy roofs",
        fear_line="For one shivery moment, the silver boat from the dream still felt close.",
        tags={"dream"},
    ),
    "whisper_forest": Dream(
        id="whisper_forest",
        image="a forest of pillows where the leaves whispered secrets",
        fear_line="The whispering leaves from the dream seemed to rustle in the dark room too.",
        tags={"dream"},
    ),
    "shadow_kite": Dream(
        id="shadow_kite",
        image="a kite made of shadow gliding across the stars",
        fear_line="The shadow kite from the dream felt as if it might be brushing the ceiling.",
        tags={"dream"},
    ),
}

SOURCES = {
    "branch_window": Source(
        id="branch_window",
        label="a branch tapping the window",
        place="the octagon window",
        sound="tap-tap-tap",
        reveal_line="When the curtain moved aside, they saw a thin branch bobbing outside and tapping the glass whenever the wind nudged it.",
        fix_line="reached outside, eased the branch away from the window, and tucked it behind the shutters",
        clue_actions={"peek_curtain"},
        loudness=2,
        tags={"window", "wind"},
    ),
    "ceiling_mobile": Source(
        id="ceiling_mobile",
        label="the loose star mobile",
        place="the corner above the bed",
        sound="clink-clink",
        reveal_line="In the dim light, a paper star on the mobile was wobbling and bumping the wooden ring each time the air stirred.",
        fix_line="stood on tiptoe, steadied the mobile, and tightened the little knot that had come loose",
        clue_actions={"tighten_mobile", "flashlight_look"},
        loudness=1,
        tags={"mobile", "bedroom"},
    ),
    "floor_drum": Source(
        id="floor_drum",
        label="a toy drum rolling on the rug",
        place="the octagon rug by the shelf",
        sound="rrr-roll ... bump",
        reveal_line="A round toy drum had slipped from the shelf and was rocking gently on the thick rug whenever the floorboard settled.",
        fix_line="picked up the drum and set it safely back on the shelf so it could not wobble anymore",
        clue_actions={"flashlight_look"},
        loudness=2,
        tags={"toy", "rug"},
    ),
}

ACTIONS = {
    "peek_curtain": Action(
        id="peek_curtain",
        text="peek past the curtain",
        tool_line="Grandma did not switch on the bright lamp. Instead, she opened the curtain just a finger-width so the moon could help.",
        reveal_phrase="see what was moving by the glass",
        tags={"clue", "window"},
    ),
    "flashlight_look": Action(
        id="flashlight_look",
        text="shine a small flashlight toward the sound",
        tool_line="Dad clicked on the little bedside flashlight and made a soft yellow circle on the floor and walls.",
        reveal_phrase="follow the sound to its true hiding place",
        tags={"clue", "flashlight"},
    ),
    "tighten_mobile": Action(
        id="tighten_mobile",
        text="reach up toward the hanging mobile",
        tool_line="Mom lifted the small chair near the bed and rose carefully enough to touch the dangling stars.",
        reveal_phrase="check whether anything overhead had come loose",
        tags={"clue", "mobile"},
    ),
}

COMFORTS = {
    "rabbit": Comfort(
        id="rabbit",
        phrase="a floppy rabbit named Mip",
        animal="rabbit",
        tags={"comfort"},
    ),
    "bear": Comfort(
        id="bear",
        phrase="a small bear named Button",
        animal="bear",
        tags={"comfort"},
    ),
    "fox": Comfort(
        id="fox",
        phrase="a velvety fox named Pip",
        animal="fox",
        tags={"comfort"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Ella", "Zoe"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Finn", "Theo", "Max"]
TRAITS = ["thoughtful", "gentle", "curious", "careful", "dreamy"]


@dataclass
class StoryParams:
    dream: str
    source: str
    action: str
    comfort: str
    child_name: str
    child_gender: str
    helper: str
    approach: str = "together"
    trait: str = "thoughtful"
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
    "dream": [
        (
            "What is a dream?",
            "A dream is a story your mind can make while you are asleep. Dreams can feel real, even though the room around you may still be safe.",
        )
    ],
    "window": [
        (
            "Why can a branch tap a window at night?",
            "Wind can push a branch back and forth until it taps the glass. In a quiet room, that little sound can seem much bigger than it is.",
        )
    ],
    "wind": [
        (
            "Can wind make night sounds?",
            "Yes. Wind can wiggle branches, curtains, and hanging things, and those movements can make soft tapping or clinking noises.",
        )
    ],
    "mobile": [
        (
            "What is a mobile above a bed?",
            "A mobile is a hanging decoration that can sway in the air. If one part comes loose, it may bump and make a clicking sound.",
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight useful in the dark?",
            "A flashlight helps you see what is really there without filling the whole room with bright light. It can turn a mystery into a clear clue.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a little piece of information that helps you solve a mystery. Looking and listening carefully can help you find one.",
        )
    ],
    "comfort": [
        (
            "Why do children hug comfort toys at bedtime?",
            "A comfort toy can help a child feel safe and steady. Holding something familiar can make a scary moment feel smaller.",
        )
    ],
}

KNOWLEDGE_ORDER = ["dream", "window", "wind", "mobile", "flashlight", "clue", "comfort"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    dream = f["dream_cfg"]
    source = f["source_cfg"]
    action = f["action_cfg"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "therapy-ist", "dream", and "octagon", and centers a small mystery to solve.',
        f"Tell a gentle story where {child.attrs['display_name']} wakes after a scary dream, hears {source.sound} from {source.place}, and learns with {helper.label_word} to look for clues instead of guessing.",
        f"Write a calm nighttime story where a child first worries about a dream creature, then uses {action.id} to discover the real cause of the sound and ends peacefully back in bed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    dream = f["dream_cfg"]
    source = f["source_cfg"]
    action = f["action_cfg"]
    comfort = f["comfort_cfg"]
    child_name = child.attrs["display_name"]
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name}, who woke from {dream.image} and heard a strange sound in the night. {helper_word.capitalize()} came to help solve the mystery.",
        ),
        (
            "What was the mystery?",
            f"The mystery was what was making {source.sound} from {source.place}. At first, {child_name} worried the scary feeling from the dream had followed into the room.",
        ),
        (
            f"Why did {child_name} feel scared?",
            f"{child_name} had just woken from a dream, so the sound felt mixed up with the dream's fear. That made an ordinary noise seem like something much bigger and stranger.",
        ),
        (
            f"How did {helper_word} help solve the mystery?",
            f"{helper_word.capitalize()} stayed calm, gave {child_name} a hug, and helped {child.pronoun('object')} look for a clue instead of guessing. Then they used {action.text} and found the real source of the sound.",
        ),
        (
            "What was really making the noise?",
            f"It was {source.label}. Once they saw the real cause, the fear shrank because the mystery had an ordinary answer.",
        ),
        (
            "What lesson did the child learn?",
            f"{child_name} learned to ask for help and look for clues first when something feels scary at night. That lesson mattered because the room was safer and calmer once the true cause was understood.",
        ),
        (
            "How did the story end?",
            f"The sound was fixed, the room grew quiet, and {child_name} went back to bed hugging {comfort.phrase}. The ending image shows the change: fear gave way to calm, and even the octagon patch of moonlight felt gentle.",
        ),
    ]
    if f.get("outcome") == "startled":
        qa.append(
            (
                f"Did {child_name} feel brave right away?",
                f"Not quite. {child_name} tried a tiny look first, but the louder sound made the fear jump again. After a hug and some help, bravery returned in a steadier way.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    source = f["source_cfg"]
    action = f["action_cfg"]
    comfort = f["comfort_cfg"]
    tags: set[str] = {"dream", "clue", "comfort"}
    tags |= set(source.tags)
    tags |= set(action.tags)
    tags |= set(comfort.tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        dream="moon_boat",
        source="branch_window",
        action="peek_curtain",
        comfort="rabbit",
        child_name="Nora",
        child_gender="girl",
        helper="grandmother",
        approach="alone_first",
        trait="dreamy",
    ),
    StoryParams(
        dream="whisper_forest",
        source="ceiling_mobile",
        action="tighten_mobile",
        comfort="bear",
        child_name="Ben",
        child_gender="boy",
        helper="mother",
        approach="together",
        trait="careful",
    ),
    StoryParams(
        dream="shadow_kite",
        source="floor_drum",
        action="flashlight_look",
        comfort="fox",
        child_name="Mia",
        child_gender="girl",
        helper="father",
        approach="alone_first",
        trait="curious",
    ),
    StoryParams(
        dream="moon_boat",
        source="ceiling_mobile",
        action="flashlight_look",
        comfort="rabbit",
        child_name="Theo",
        child_gender="boy",
        helper="grandfather",
        approach="together",
        trait="gentle",
    ),
]


ASP_RULES = r"""
valid(D, S, A) :- dream(D), source(S), action(A), reveals(S, A).

startled :- chosen_approach(alone_first), chosen_source(S), loudness(S, L), loud_startle(M), L >= M.
steady   :- not startled.

outcome(startled) :- startled.
outcome(steady)   :- steady.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for did in DREAMS:
        lines.append(asp.fact("dream", did))
    for sid, source in SOURCES.items():
        lines.append(asp.fact("source", sid))
        lines.append(asp.fact("loudness", sid, source.loudness))
        for aid in sorted(source.clue_actions):
            lines.append(asp.fact("reveals", sid, aid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    lines.append(asp.fact("loud_startle", LOUD_STARTLE))
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
            asp.fact("chosen_source", params.source),
            asp.fact("chosen_approach", params.approach),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_test_generation() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "dream" not in sample.story or "octagon" not in sample.story:
        raise StoryError("(Smoke test failed: generated story was empty or missing required seed words.)")
    buf = io.StringIO()
    with redirect_stdout(buf):
        emit(sample, trace=False, qa=True, header="### smoke")
    if not buf.getvalue().strip():
        raise StoryError("(Smoke test failed: emit() produced no output.)")


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_test_generation()
        print("OK: generation/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime storyworld: a child wakes from a scary dream, solves a gentle mystery, and learns to look for clues."
    )
    ap.add_argument("--dream", choices=sorted(DREAMS))
    ap.add_argument("--source", choices=sorted(SOURCES))
    ap.add_argument("--action", choices=sorted(ACTIONS))
    ap.add_argument("--comfort", choices=sorted(COMFORTS))
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--approach", choices=["together", "alone_first"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.action:
        source = SOURCES[args.source]
        action = ACTIONS[args.action]
        if not action_reveals(source, action):
            raise StoryError(explain_rejection(source, action))

    combos = [
        c
        for c in valid_combos()
        if (args.dream is None or c[0] == args.dream)
        and (args.source is None or c[1] == args.source)
        and (args.action is None or c[2] == args.action)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    dream_id, source_id, action_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    comfort_id = args.comfort or rng.choice(sorted(COMFORTS))
    helper = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    approach = args.approach or rng.choice(["together", "alone_first"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        dream=dream_id,
        source=source_id,
        action=action_id,
        comfort=comfort_id,
        child_name=name,
        child_gender=gender,
        helper=helper,
        approach=approach,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.dream not in DREAMS:
        raise StoryError(f"(Unknown dream: {params.dream})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.action not in ACTIONS:
        raise StoryError(f"(Unknown action: {params.action})")
    if params.comfort not in COMFORTS:
        raise StoryError(f"(Unknown comfort item: {params.comfort})")
    if params.helper not in {"mother", "father", "grandmother", "grandfather"}:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.approach not in {"together", "alone_first"}:
        raise StoryError(f"(Unknown approach: {params.approach})")

    source = SOURCES[params.source]
    action = ACTIONS[params.action]
    if not action_reveals(source, action):
        raise StoryError(explain_rejection(source, action))

    world = tell(
        dream=DREAMS[params.dream],
        source_cfg=source,
        action_cfg=action,
        comfort_cfg=COMFORTS[params.comfort],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper,
        approach=params.approach,
        trait=params.trait,
    )
    story = world.render().replace("child", params.child_name).replace("helper", world.get("helper").label_word)
    story = story.replace("  ", " ")
    return StorySample(
        params=params,
        story=story,
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
        print(f"{len(combos)} compatible (dream, source, action) combos:\n")
        for dream_id, source_id, action_id in combos:
            print(f"  {dream_id:14} {source_id:16} {action_id}")
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
            header = f"### {p.child_name}: {p.source} via {p.action} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
