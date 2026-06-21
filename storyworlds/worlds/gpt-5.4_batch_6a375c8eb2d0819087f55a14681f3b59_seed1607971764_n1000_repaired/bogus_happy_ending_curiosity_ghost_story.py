#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bogus_happy_ending_curiosity_ghost_story.py
======================================================================

A standalone story world about a child who becomes curious about a "ghost" in a
creaky place, feels scared, investigates safely with a grown-up, and discovers
that the haunting was bogus all along.

The world model tracks physical meters (light, wobble, draft, noise) and
emotional memes (fear, curiosity, relief, bravery). The prose is rendered from
simulated state, not from a frozen template. Every valid story has a beginning,
a spooky middle turn, and a happy ending image proving what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/bogus_happy_ending_curiosity_ghost_story.py
    python storyworlds/worlds/gpt-5.4/bogus_happy_ending_curiosity_ghost_story.py --place attic --sign whisper
    python storyworlds/worlds/gpt-5.4/bogus_happy_ending_curiosity_ghost_story.py --cause kitten
    python storyworlds/worlds/gpt-5.4/bogus_happy_ending_curiosity_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/bogus_happy_ending_curiosity_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/bogus_happy_ending_curiosity_ghost_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/bogus_happy_ending_curiosity_ghost_story.py --verify
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
        female = {"girl", "mother", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "grandfather", "man", "uncle"}
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
            "aunt": "aunt",
            "uncle": "uncle",
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
class Place:
    id: str
    label: str
    phrase: str
    spooky_detail: str
    hiding_spot: str
    sound_path: str
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
class Sign:
    id: str
    label: str
    line: str
    kind: str
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
class Cause:
    id: str
    label: str
    article: str
    reveal_line: str
    fix_line: str
    explain_line: str
    kinds: set[str] = field(default_factory=set)
    places: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    phrase: str
    use_line: str
    comfort_line: str
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


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    sign = world.get("sign")
    child = world.get("child")
    if sign.meters["active"] < THRESHOLD:
        return out
    if ("spook",) not in world.fired:
        world.fired.add(("spook",))
        room.meters["spooky"] += 1
        child.memes["fear"] += 1
        child.memes["curiosity"] += 1
        out.append("__spook__")
    return out


def _r_light_relief(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    child = world.get("child")
    helper = world.get("helper")
    if room.meters["lit"] < THRESHOLD:
        return out
    if room.meters["spooky"] < THRESHOLD:
        return out
    if ("light_relief",) in world.fired:
        return out
    world.fired.add(("light_relief",))
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
    child.memes["bravery"] += 1
    helper.memes["calm"] += 1
    return out


def _r_fix_relief(world: World) -> list[str]:
    out: list[str] = []
    cause = world.get("cause")
    child = world.get("child")
    helper = world.get("helper")
    if cause.meters["fixed"] < THRESHOLD:
        return out
    if ("fixed",) in world.fired:
        return out
    world.fired.add(("fixed",))
    child.memes["relief"] += 2
    child.memes["fear"] = 0.0
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.get("room").meters["spooky"] = 0.0
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="spook", tag="emotional", apply=_r_spook),
    Rule(name="light_relief", tag="emotional", apply=_r_light_relief),
    Rule(name="fix_relief", tag="resolution", apply=_r_fix_relief),
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


def sign_matches(place: Place, sign: Sign, cause: Cause) -> bool:
    return sign.kind in cause.kinds and place.id in cause.places


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for sign_id, sign in SIGNS.items():
            for cause_id, cause in CAUSES.items():
                if sign_matches(place, sign, cause):
                    combos.append((place_id, sign_id, cause_id))
    return combos


def predict_bogus(world: World, tool_id: str) -> dict:
    sim = world.copy()
    room = sim.get("room")
    tool = sim.get(tool_id)
    if tool.attrs.get("makes_light"):
        room.meters["lit"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": sim.get("child").memes["fear"],
        "lit": room.meters["lit"] >= THRESHOLD,
        "can_see": room.meters["lit"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, place: Place) -> None:
    child.memes["calm"] += 1
    world.say(
        f"One evening, {child.id} stood near {place.phrase}. {place.spooky_detail}"
    )
    world.say(
        f"{child.pronoun().capitalize()} had heard older kids whisper that a ghost lived there, "
        f"which made the shadows seem taller than they were."
    )


def spark_curiosity(world: World, child: Entity, sign: Sign) -> None:
    world.say(sign.line)
    world.say(
        f"{child.id}'s heart gave a jump, but curiosity tugged just as hard as fear."
    )
    sign_ent = world.get("sign")
    sign_ent.meters["active"] += 1
    propagate(world, narrate=False)


def tell_helper(world: World, child: Entity, helper: Entity) -> None:
    child.memes["trust"] += 1
    helper.memes["care"] += 1
    world.say(
        f'"Did you hear that?" {child.id} whispered. "What if it is a ghost?"'
    )
    world.say(
        f"{child.id}'s {helper.label_word} came over instead of laughing."
    )


def helper_reframes(world: World, child: Entity, helper: Entity, tool: Tool) -> None:
    pred = predict_bogus(world, "tool")
    world.facts["predicted_can_see"] = pred["can_see"]
    world.say(
        f'"Maybe it sounds spooky," {helper.label_word} said softly, '
        f'"but we do not have to guess. We can bring {tool.phrase} and look carefully together."'
    )
    world.say(tool.comfort_line)


def approach(world: World, child: Entity, helper: Entity, place: Place, tool: Tool) -> None:
    child.memes["bravery"] += 1
    helper.memes["calm"] += 1
    tool_ent = world.get("tool")
    room = world.get("room")
    if tool_ent.attrs.get("makes_light"):
        room.meters["lit"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Step by step, they went to {place.phrase}. {tool.use_line}"
    )
    world.say(
        f"The light reached into {place.hiding_spot}, and the terrible ghost shape began to shrink into ordinary things."
    )


def reveal(world: World, child: Entity, helper: Entity, cause: Cause) -> None:
    world.say(cause.reveal_line)
    world.say(
        f'{helper.label_word.capitalize()} let out a small laugh. "So the ghost story was bogus," '
        f"{helper.pronoun()} said."
    )
    child.memes["wonder"] += 1


def fix_cause(world: World, child: Entity, helper: Entity, cause: Cause) -> None:
    cause_ent = world.get("cause")
    cause_ent.meters["fixed"] += 1
    propagate(world, narrate=False)
    world.say(cause.fix_line)
    world.say(cause.explain_line)


def ending(world: World, child: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"{child.id} breathed out so hard that {child.pronoun('possessive')} shoulders dropped."
    )
    world.say(
        f'Soon {place.phrase} felt different: not haunted at all, just quiet and old.'
    )
    world.say(
        f"Before bed, {child.id} peeked back once more and smiled. The dark corner that had seemed full of ghosts now looked small, still, and friendly."
    )


def tell(
    place: Place,
    sign: Sign,
    cause: Cause,
    tool: Tool,
    child_name: str = "Nora",
    child_type: str = "girl",
    helper_type: str = "grandmother",
    child_trait: str = "curious",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
        role="child",
        traits=[child_trait],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the grown-up",
        role="helper",
        attrs={},
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label=place.label,
        attrs={"place": place.id},
    ))
    sign_ent = world.add(Entity(
        id="sign",
        type="sign",
        label=sign.label,
        attrs={"kind": sign.kind},
    ))
    cause_ent = world.add(Entity(
        id="cause",
        type="cause",
        label=cause.label,
        attrs={"cause": cause.id},
    ))
    tool_ent = world.add(Entity(
        id="tool",
        type="tool",
        label=tool.label,
        attrs={"makes_light": True},
    ))

    room.meters["lit"] = 0.0
    room.meters["spooky"] = 0.0
    sign_ent.meters["active"] = 0.0
    cause_ent.meters["fixed"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["curiosity"] = 1.0 if child_trait == "curious" else 0.5
    child.memes["relief"] = 0.0
    child.memes["bravery"] = 0.0
    helper.memes["calm"] = 1.0
    helper.memes["care"] = 0.0
    helper.memes["joy"] = 0.0
    child.memes["joy"] = 0.0
    child.memes["wonder"] = 0.0
    child.memes["trust"] = 0.0

    introduce(world, child, place)
    spark_curiosity(world, child, sign)

    world.para()
    tell_helper(world, child, helper)
    helper_reframes(world, child, helper, tool)

    world.para()
    approach(world, child, helper, place, tool)
    reveal(world, child, helper, cause)
    fix_cause(world, child, helper, cause)

    world.para()
    ending(world, child, helper, place)

    world.facts.update(
        place=place,
        sign=sign,
        cause_cfg=cause,
        tool=tool,
        child=child,
        helper=helper,
        room=room,
        sign_ent=sign_ent,
        cause_ent=cause_ent,
        bogus=True,
        happy=child.memes["relief"] >= THRESHOLD,
    )
    return world


PLACES = {
    "attic": Place(
        id="attic",
        label="attic",
        phrase="the attic door at the end of the hall",
        spooky_detail="The wood around it was old and silver-gray, and the crack under the door looked like a thin dark smile.",
        hiding_spot="a stack of trunks and winter coats",
        sound_path="along the rafters",
        tags={"attic", "old_house"},
    ),
    "porch": Place(
        id="porch",
        label="porch",
        phrase="the back porch with its screen door",
        spooky_detail="The porch boards held the day's heat, but the far corner was already full of blue evening shadows.",
        hiding_spot="the rocking chair and a heap of folded quilts",
        sound_path="through the screen",
        tags={"porch", "old_house"},
    ),
    "shed": Place(
        id="shed",
        label="shed",
        phrase="the garden shed behind the lilac bush",
        spooky_detail="The little shed leaned a bit to one side, and one window had a cloudy pane that turned every shadow soft and strange.",
        hiding_spot="a shelf of jars and hanging tools",
        sound_path="between the boards",
        tags={"shed", "old_house"},
    ),
}

SIGNS = {
    "whisper": Sign(
        id="whisper",
        label="whisper",
        line='From inside came a hushy little sound, almost like someone whispering from far away.',
        kind="soft_noise",
        tags={"whisper", "sound"},
    ),
    "tap": Sign(
        id="tap",
        label="tapping",
        line="A quick tap-tap-tap came from the dark, then stopped so suddenly that the silence felt louder than before.",
        kind="hard_noise",
        tags={"tap", "sound"},
    ),
    "glow": Sign(
        id="glow",
        label="glow",
        line="For one moment, a pale wobbling glow shone and vanished again.",
        kind="light_flicker",
        tags={"glow", "light"},
    ),
}

CAUSES = {
    "curtain_draft": Cause(
        id="curtain_draft",
        label="a curtain puffing in a draft",
        article="a",
        reveal_line="It was only an old lace curtain lifting and falling as night air slipped in through a cracked window.",
        fix_line="Together they latched the window, and the curtain stopped floating like a white ghost.",
        explain_line="The whispery sound had been cloth rubbing the wall whenever the draft pushed it.",
        kinds={"soft_noise", "light_flicker"},
        places={"attic", "porch"},
        tags={"draft", "curtain", "window"},
    ),
    "kitten_box": Cause(
        id="kitten_box",
        label="a kitten in a box",
        article="a",
        reveal_line="Inside a hat box sat a tiny gray kitten, blinking with wide moon-round eyes.",
        fix_line="The grown-up lifted the kitten out, set down a saucer of water, and left the box lid open so it would not rattle anymore.",
        explain_line="Its small paws and soft mews had made the whispery, spooky sounds.",
        kinds={"soft_noise", "hard_noise"},
        places={"attic", "shed"},
        tags={"kitten", "animal"},
    ),
    "loose_lantern": Cause(
        id="loose_lantern",
        label="a loose lantern chain",
        article="a",
        reveal_line="The 'ghost light' turned out to be an old porch lantern swinging on a loose chain and tossing weak flashes across the wall.",
        fix_line="The grown-up tightened the chain, and the lantern stopped wobbling and blinking.",
        explain_line="That shaky lantern had made both the tapping and the odd glow.",
        kinds={"hard_noise", "light_flicker"},
        places={"porch", "shed"},
        tags={"lantern", "metal", "light"},
    ),
}

TOOLS = {
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a bright flashlight",
        use_line="Grandma clicked on the flashlight, and a clean yellow beam slid over every board and box.",
        comfort_line="The button made a cheerful little click, which felt much better than listening to shadows.",
        tags={"flashlight", "light"},
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a camping lantern",
        use_line="Dad lifted the camping lantern, and its warm round glow pushed the darkness back from the corners.",
        comfort_line="The steady glow made the strange place feel smaller and easier to understand.",
        tags={"lantern", "light"},
    ),
    "headlamp": Tool(
        id="headlamp",
        label="headlamp",
        phrase="a head-lamp",
        use_line="Aunt snapped on the head-lamp, and the narrow beam showed exactly where every shadow began and ended.",
        comfort_line="Seeing the beam point right at things made guessing feel less scary.",
        tags={"headlamp", "light"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Ella", "Ruby", "Ivy"]
BOY_NAMES = ["Ben", "Sam", "Max", "Leo", "Finn", "Theo", "Jack", "Eli"]
CHILD_TRAITS = ["curious", "careful", "thoughtful", "brave"]
HELPERS = ["grandmother", "grandfather", "mother", "father", "aunt", "uncle"]


@dataclass
class StoryParams:
    place: str
    sign: str
    cause: str
    tool: str
    child_name: str
    child_type: str
    helper_type: str
    child_trait: str
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
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a spooky tale about something that seems haunted or mysterious. Sometimes the scary thing turns out to have an ordinary reason."
        )
    ],
    "bogus": [
        (
            "What does bogus mean?",
            "Bogus means not real or not true. If a ghost warning is bogus, it only seemed true at first."
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight helpful in the dark?",
            "A flashlight makes a bright beam so you can see what is really there. Seeing clearly helps your brain stop guessing scary things."
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern gives light all around it. That makes dark corners easier to see."
        )
    ],
    "headlamp": [
        (
            "What is a head-lamp for?",
            "A head-lamp is a light you wear on your head. It shines where you look."
        )
    ],
    "draft": [
        (
            "What is a draft from a window?",
            "A draft is moving air that slips in through a gap. It can make curtains move and soft sounds happen."
        )
    ],
    "kitten": [
        (
            "Why might a kitten sound spooky in the dark?",
            "A kitten can scratch, rustle, and mew in tiny sounds that are hard to understand in the dark. When you cannot see the kitten, your imagination may guess something scarier."
        )
    ],
    "lantern_obj": [
        (
            "Why can a loose chain make tapping sounds?",
            "When metal wobbles and bumps, it can tap again and again. In a quiet place, that sound can seem mysterious."
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling of wanting to find out more. It can help you learn when you use it in a safe way."
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "bogus", "curiosity", "flashlight", "lantern", "headlamp", "draft", "kitten", "lantern_obj"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    sign = f["sign"]
    tool = f["tool"]
    cause = f["cause_cfg"]
    return [
        'Write a short ghost-story-style story for a 3-to-5-year-old that includes the word "bogus" and ends happily.',
        f"Tell a gentle spooky story where {child.id} hears {sign.label} near the {place.label}, grows curious, and investigates safely with {child.pronoun('possessive')} {helper.label_word}.",
        f"Write a story where a child thinks a ghost might be hiding nearby, but {tool.label} light reveals {cause.label} and proves the haunting was bogus.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    sign = f["sign"]
    cause = f["cause_cfg"]
    tool = f["tool"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who heard something spooky near the {place.label}, and {child.pronoun('possessive')} {helper.label_word} who helped investigate. They solved the mystery together instead of just guessing."
        ),
        (
            f"Why did {child.id} think there might be a ghost?",
            f"{child.id} heard {sign.label} in the dark, and that made the place feel haunted. The strange sound or glow came before the real cause was visible, so fear filled in the rest."
        ),
        (
            f"Why did {child.id} go closer instead of running away?",
            f"{child.id} was scared, but curiosity kept tugging too. {child.pronoun('possessive').capitalize()} {helper.label_word} stayed calm and offered to look carefully together, which made the investigation feel safe."
        ),
        (
            f"What did they use to solve the mystery?",
            f"They used {tool.phrase} to light the dark place. Once they could see clearly, the pretend ghost started to turn back into ordinary things."
        ),
        (
            "What was the 'ghost' really?",
            f"It was really {cause.label}. The spooky sign had an everyday cause, which is why the ghost story turned out to be bogus."
        ),
        (
            "How did the story end?",
            f"It ended happily because the mystery was explained and fixed. By the end, the same place that had felt haunted looked quiet and friendly again."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"ghost", "bogus", "curiosity"}
    tool = world.facts["tool"]
    cause = world.facts["cause_cfg"]
    if tool.id == "flashlight":
        tags.add("flashlight")
    elif tool.id == "lantern":
        tags.add("lantern")
    elif tool.id == "headlamp":
        tags.add("headlamp")
    if cause.id == "curtain_draft":
        tags.add("draft")
    elif cause.id == "kitten_box":
        tags.add("kitten")
    elif cause.id == "loose_lantern":
        tags.add("lantern_obj")
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="attic",
        sign="whisper",
        cause="curtain_draft",
        tool="flashlight",
        child_name="Nora",
        child_type="girl",
        helper_type="grandmother",
        child_trait="curious",
    ),
    StoryParams(
        place="shed",
        sign="tap",
        cause="kitten_box",
        tool="lantern",
        child_name="Ben",
        child_type="boy",
        helper_type="father",
        child_trait="thoughtful",
    ),
    StoryParams(
        place="porch",
        sign="glow",
        cause="loose_lantern",
        tool="headlamp",
        child_name="Mia",
        child_type="girl",
        helper_type="aunt",
        child_trait="careful",
    ),
    StoryParams(
        place="porch",
        sign="whisper",
        cause="curtain_draft",
        tool="lantern",
        child_name="Eli",
        child_type="boy",
        helper_type="grandfather",
        child_trait="curious",
    ),
    StoryParams(
        place="shed",
        sign="glow",
        cause="loose_lantern",
        tool="flashlight",
        child_name="Ruby",
        child_type="girl",
        helper_type="mother",
        child_trait="brave",
    ),
]


def explain_rejection(place: Place, sign: Sign, cause: Cause) -> str:
    return (
        f"(No story: {sign.label} at the {place.label} does not fit {cause.label}. "
        f"This world only tells mysteries where the spooky sign can honestly come from the hidden cause.)"
    )


ASP_RULES = r"""
fits(P,S,C) :- place(P), sign(S), cause(C), sign_kind(S,K), cause_kind(C,K), cause_place(C,P).
happy(P,S,C,T) :- fits(P,S,C), tool(T).
bogus(P,S,C) :- fits(P,S,C).

#show fits/3.
#show happy/4.
#show bogus/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for sign_id, sign in SIGNS.items():
        lines.append(asp.fact("sign", sign_id))
        lines.append(asp.fact("sign_kind", sign_id, sign.kind))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        for kind in sorted(cause.kinds):
            lines.append(asp.fact("cause_kind", cause_id, kind))
        for place_id in sorted(cause.places):
            lines.append(asp.fact("cause_place", cause_id, place_id))
    for tool_id in TOOLS:
        lines.append(asp.fact("tool", tool_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show fits/3."))
    return sorted(set(asp.atoms(model, "fits")))


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

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="### smoke")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a spooky mystery that turns out bogus and ends happily."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story triples derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.sign and args.cause:
        place = PLACES[args.place]
        sign = SIGNS[args.sign]
        cause = CAUSES[args.cause]
        if not sign_matches(place, sign, cause):
            raise StoryError(explain_rejection(place, sign, cause))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.sign is None or combo[1] == args.sign)
        and (args.cause is None or combo[2] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, sign_id, cause_id = rng.choice(sorted(combos))
    tool_id = args.tool or rng.choice(sorted(TOOLS.keys()))
    child_type = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_type = args.helper or rng.choice(HELPERS)
    child_trait = rng.choice(CHILD_TRAITS)

    return StoryParams(
        place=place_id,
        sign=sign_id,
        cause=cause_id,
        tool=tool_id,
        child_name=child_name,
        child_type=child_type,
        helper_type=helper_type,
        child_trait=child_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.sign not in SIGNS:
        raise StoryError(f"(Unknown sign: {params.sign})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.child_type not in {"girl", "boy"}:
        raise StoryError(f"(Unknown child type: {params.child_type})")
    if params.helper_type not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper_type})")

    place = PLACES[params.place]
    sign = SIGNS[params.sign]
    cause = CAUSES[params.cause]
    tool = TOOLS[params.tool]
    if not sign_matches(place, sign, cause):
        raise StoryError(explain_rejection(place, sign, cause))

    world = tell(
        place=place,
        sign=sign,
        cause=cause,
        tool=tool,
        child_name=params.child_name,
        child_type=params.child_type,
        helper_type=params.helper_type,
        child_trait=params.child_trait,
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
        print(asp_program("", "#show fits/3.\n#show happy/4.\n#show bogus/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, sign, cause) combos:\n")
        for place, sign, cause in combos:
            print(f"  {place:8} {sign:8} {cause}")
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
            header = f"### {p.child_name}: {p.sign} at {p.place} ({p.cause}, {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
