#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/appearance_briar_automatic_rhyme_bedtime_story.py
=============================================================================

A standalone story world for a bedtime tale about a child who sees a strange
appearance on the wall, grows frightened, and then learns that the shape came
from a briar outside the window. A calm grown-up checks the room, fixes the real
cause, turns on an automatic bedtime light, and speaks a tiny rhyme that lets
the room feel gentle again.

This world keeps the shape classical and state-driven:
- typed entities with physical meters and emotional memes
- a small causal rule engine
- a Python reasonableness gate plus an inline ASP twin
- prose rendered from the simulated state, not from a frozen template

Run it
------
    python storyworlds/worlds/gpt-5.4/appearance_briar_automatic_rhyme_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/appearance_briar_automatic_rhyme_bedtime_story.py --room eaves_room --briar rose_briar --aid automatic_nightlight
    python storyworlds/worlds/gpt-5.4/appearance_briar_automatic_rhyme_bedtime_story.py --room high_window_nursery --briar low_berry_briar
    python storyworlds/worlds/gpt-5.4/appearance_briar_automatic_rhyme_bedtime_story.py --aid automatic_music_box
    python storyworlds/worlds/gpt-5.4/appearance_briar_automatic_rhyme_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/appearance_briar_automatic_rhyme_bedtime_story.py --asp
    python storyworlds/worlds/gpt-5.4/appearance_briar_automatic_rhyme_bedtime_story.py --verify
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
class Room:
    id: str
    label: str
    bed: str
    nook: str
    sill_height: int
    moon_line: str
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
class Briar:
    id: str
    label: str
    the: str
    appearance: str
    sound: str
    height: int
    thorny: bool = True
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


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    action: str
    glow: str
    sense: int
    power: int
    rhyme_a: str
    rhyme_b: str
    automatic: bool = True
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


def _r_shadow(world: World) -> list[str]:
    child = world.get("child")
    room = world.get("room")
    briar = world.get("briar")
    wall = world.get("wall")
    if room.meters["moonlight"] < THRESHOLD:
        return []
    if briar.meters["at_window"] < THRESHOLD:
        return []
    sig = ("shadow",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    wall.meters["shadow_shape"] += 1
    child.memes["fear"] += 1
    return ["__appearance__"]


def _r_tap(world: World) -> list[str]:
    child = world.get("child")
    briar = world.get("briar")
    window = world.get("window")
    if briar.meters["at_window"] < THRESHOLD and briar.meters["scratching"] < THRESHOLD:
        return []
    if not briar.attrs.get("thorny", False):
        return []
    sig = ("tap",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    window.meters["tapping"] += 1
    child.memes["fear"] += 1
    return []


def _r_relief(world: World) -> list[str]:
    child = world.get("child")
    aid = world.get("aid")
    wall = world.get("wall")
    window = world.get("window")
    if aid.meters["on"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    wall.meters["shadow_shape"] = 0.0
    window.meters["tapping"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["sleepy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="shadow", tag="physical", apply=_r_shadow),
    Rule(name="tap", tag="physical", apply=_r_tap),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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


def briar_reaches(room: Room, briar: Briar) -> bool:
    return briar.height >= room.sill_height


def fear_severity(briar: Briar) -> int:
    return 2 if briar.thorny else 1


def sensible_aids() -> list[Aid]:
    return [aid for aid in AIDS.values() if aid.sense >= SENSE_MIN]


def aid_can_settle(aid: Aid, briar: Briar) -> bool:
    return aid.power >= fear_severity(briar)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for room_id, room in ROOMS.items():
        for briar_id, briar in BRIARS.items():
            if not briar_reaches(room, briar):
                continue
            for aid_id, aid in AIDS.items():
                if aid.sense >= SENSE_MIN and aid_can_settle(aid, briar):
                    combos.append((room_id, briar_id, aid_id))
    return combos


def predict_fright(world: World) -> dict:
    sim = world.copy()
    sim.get("briar").meters["at_window"] = 1
    if sim.get("briar").attrs.get("thorny", False):
        sim.get("briar").meters["scratching"] = 1
    propagate(sim, narrate=False)
    return {
        "appearance": sim.get("wall").meters["shadow_shape"] >= THRESHOLD,
        "tapping": sim.get("window").meters["tapping"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"],
    }


def introduce(world: World, child: Entity, parent: Entity, room: Room) -> None:
    child.memes["calm"] += 1
    world.say(
        f"In {room.nook}, {child.id} snuggled into {room.bed} while "
        f"{child.pronoun('possessive')} {parent.label_word} tucked the blanket smooth."
    )
    world.say(room.moon_line)


def rising_wind(world: World, briar_cfg: Briar) -> None:
    room = world.get("room")
    briar = world.get("briar")
    room.meters["moonlight"] = 1
    briar.meters["at_window"] = 1
    if briar_cfg.thorny:
        briar.meters["scratching"] = 1
    propagate(world, narrate=False)
    world.say(
        f"Outside the window, {briar_cfg.the} leaned close in the wind."
    )


def notice_appearance(world: World, child: Entity, briar_cfg: Briar) -> None:
    wall = world.get("wall")
    window = world.get("window")
    if wall.meters["shadow_shape"] >= THRESHOLD:
        world.say(
            f"Moonlight and moving stems made an odd appearance on the wall, "
            f"{briar_cfg.appearance}."
        )
    if window.meters["tapping"] >= THRESHOLD:
        world.say(
            f"Then came {briar_cfg.sound}, and the quiet room no longer felt sleepy at all."
        )
    world.say(
        f'{child.id} pulled the blanket to {child.pronoun("possessive")} chin. '
        f'"Something is there," {child.pronoun()} whispered.'
    )


def call_parent(world: World, child: Entity, parent: Entity) -> None:
    child.memes["trust"] += 1
    parent.memes["care"] += 1
    world.say(
        f'{child.id} did not hide under the pillow or guess again. '
        f'{child.pronoun().capitalize()} called softly for {child.pronoun("possessive")} {parent.label_word}.'
    )


def inspect(world: World, child: Entity, parent: Entity, briar_cfg: Briar) -> None:
    pred = predict_fright(world)
    world.facts["predicted_fear"] = pred["fear"]
    world.facts["predicted_tapping"] = pred["tapping"]
    child.memes["seen_help"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came in, listened once, and went straight to the window."
    )
    world.say(
        f'There was no monster at all. It was only {briar_cfg.the}, '
        f'its thorns and leaves making a queer wall-shape in the moon.'
    )


def fix_room(world: World, child: Entity, parent: Entity, aid_cfg: Aid, briar_cfg: Briar) -> None:
    aid = world.get("aid")
    world.get("briar").meters["at_window"] = 0.0
    world.get("briar").meters["scratching"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} {aid_cfg.action} and set {aid_cfg.phrase} by the bed."
    )
    aid.meters["on"] = 1
    propagate(world, narrate=False)
    child.memes["love"] += 1
    world.say(
        f"Soon the {aid_cfg.label} {aid_cfg.glow}, and the room showed its true shapes again."
    )


def bedtime_rhyme(world: World, child: Entity, parent: Entity, aid_cfg: Aid, briar_cfg: Briar) -> None:
    world.say(
        f'{parent.label_word.capitalize()} kissed {child.id}\'s forehead and said, '
        f'"{aid_cfg.rhyme_a} {aid_cfg.rhyme_b}"'
    )
    world.say(
        f"{child.id} listened once more. The window was still, the briar was only a briar, "
        f"and the strange appearance was gone."
    )


def sleep_end(world: World, child: Entity, aid_cfg: Aid) -> None:
    child.memes["sleep"] += 1
    world.say(
        f"With the automatic glow beside {child.pronoun('object')}, {child.id}'s eyes grew heavy."
    )
    world.say(
        f"Before long, {child.pronoun()} was asleep, and the small room looked kind again."
    )


def tell(
    room: Room,
    briar_cfg: Briar,
    aid_cfg: Aid,
    *,
    child_name: str = "Mina",
    child_type: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent"))
    room_ent = world.add(Entity(id="room", type="room", label=room.label))
    room_ent.attrs["room_id"] = room.id
    window = world.add(Entity(id="window", type="window", label="window"))
    wall = world.add(Entity(id="wall", type="wall", label="wall"))
    briar = world.add(Entity(id="briar", type="plant", label=briar_cfg.label))
    briar.attrs["thorny"] = briar_cfg.thorny
    aid = world.add(Entity(id="aid", type="light", label=aid_cfg.label))
    child.attrs["name"] = child_name
    parent.attrs["type"] = parent_type
    world.facts.update(
        room=room,
        briar_cfg=briar_cfg,
        aid_cfg=aid_cfg,
        child=child,
        parent=parent,
    )

    introduce(world, child, parent, room)
    world.para()
    rising_wind(world, briar_cfg)
    notice_appearance(world, child, briar_cfg)
    call_parent(world, child, parent)
    world.para()
    inspect(world, child, parent, briar_cfg)
    fix_room(world, child, parent, aid_cfg, briar_cfg)
    bedtime_rhyme(world, child, parent, aid_cfg, briar_cfg)
    world.para()
    sleep_end(world, child, aid_cfg)

    world.facts.update(
        appearance_seen=wall.meters["shadow_shape"] < THRESHOLD,
        tapping_happened=window.meters["tapping"] < THRESHOLD,
        fear_cleared=child.memes["fear"] < THRESHOLD,
        asleep=child.memes["sleep"] >= THRESHOLD,
        rhyme=(aid_cfg.rhyme_a, aid_cfg.rhyme_b),
    )
    return world


ROOMS = {
    "eaves_room": Room(
        id="eaves_room",
        label="the eaves room",
        bed="a little patchwork bed",
        nook="the eaves room under the sloping roof",
        sill_height=2,
        moon_line="A silver moon put a pale square of light across the floorboards.",
        tags={"bedroom", "moon"},
    ),
    "small_bedroom": Room(
        id="small_bedroom",
        label="the small bedroom",
        bed="a soft bed with a blue quilt",
        nook="the small bedroom at the end of the hall",
        sill_height=1,
        moon_line="The curtains were half open, and the moon shone softly by the pillow.",
        tags={"bedroom", "moon"},
    ),
    "high_window_nursery": Room(
        id="high_window_nursery",
        label="the high-window nursery",
        bed="a crib-sized bed with star sheets",
        nook="the quiet nursery with the high window",
        sill_height=3,
        moon_line="A sleepy stripe of moonlight stretched along the rug and touched the rocking chair.",
        tags={"nursery", "moon"},
    ),
}

BRIARS = {
    "rose_briar": Briar(
        id="rose_briar",
        label="rose briar",
        the="the rose briar",
        appearance="like a crooked crown with fingers",
        sound="a tiny tik-tik at the glass",
        height=3,
        thorny=True,
        tags={"briar", "shadow"},
    ),
    "berry_briar": Briar(
        id="berry_briar",
        label="berry briar",
        the="the berry briar",
        appearance="like a nest of long little claws",
        sound="a soft rasp against the pane",
        height=2,
        thorny=True,
        tags={"briar", "shadow"},
    ),
    "low_berry_briar": Briar(
        id="low_berry_briar",
        label="low berry briar",
        the="the low berry briar",
        appearance="like a wobbling scribble",
        sound="the faintest brush at the frame",
        height=1,
        thorny=True,
        tags={"briar", "shadow"},
    ),
}

AIDS = {
    "automatic_nightlight": Aid(
        id="automatic_nightlight",
        label="automatic night-light",
        phrase="the automatic night-light",
        action="drew the briar branch back from the pane",
        glow="clicked on by itself with a warm pearly shine",
        sense=3,
        power=2,
        rhyme_a="Little light, soft and bright,",
        rhyme_b="keep kind watch through the night.",
        automatic=True,
        tags={"automatic", "nightlight", "rhyme"},
    ),
    "automatic_star_lamp": Aid(
        id="automatic_star_lamp",
        label="automatic star lamp",
        phrase="the automatic star lamp",
        action="tied the briar gently away with garden twine",
        glow="woke with tiny golden stars across the ceiling",
        sense=3,
        power=2,
        rhyme_a="Star by star, near and far,",
        rhyme_b="night is gentle as you are.",
        automatic=True,
        tags={"automatic", "lamp", "rhyme"},
    ),
    "automatic_hall_glow": Aid(
        id="automatic_hall_glow",
        label="automatic hall glow",
        phrase="the automatic hall glow",
        action="latched the window snug and moved the briar clear",
        glow="spilled a honey stripe from the doorway without any loud switch",
        sense=2,
        power=2,
        rhyme_a="Doorway gleam, steady beam,",
        rhyme_b="carry calm into a dream.",
        automatic=True,
        tags={"automatic", "light", "rhyme"},
    ),
    "automatic_music_box": Aid(
        id="automatic_music_box",
        label="automatic music box",
        phrase="the automatic music box",
        action="wound the music box and left the briar where it was",
        glow="did not brighten the room at all",
        sense=1,
        power=1,
        rhyme_a="Hush and sway till break of day,",
        rhyme_b="let the shadows dance away.",
        automatic=True,
        tags={"automatic", "music", "rhyme"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Tess", "Nora", "Ivy", "Poppy", "Wren", "Ella"]
BOY_NAMES = ["Owen", "Milo", "Finn", "Theo", "Arlo", "Jules", "Noah", "Ben"]


@dataclass
class StoryParams:
    room: str
    briar: str
    aid: str
    child_name: str
    child_gender: str
    parent: str
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
    "briar": [
        (
            "What is a briar?",
            "A briar is a thorny plant with long stems that can catch on things. When the wind moves it near a window, it can scrape and make funny shapes."
        )
    ],
    "shadow": [
        (
            "Why can shadows look strange at night?",
            "At night, a small light and a moving branch can stretch a shadow into a bigger shape than it really is. That can make an ordinary thing look mysterious."
        )
    ],
    "automatic": [
        (
            "What does automatic mean?",
            "Automatic means something can start or work by itself when it needs to. An automatic night-light can glow without a big person flipping it on each time."
        )
    ],
    "nightlight": [
        (
            "What is a night-light for?",
            "A night-light gives a small gentle glow in the dark. It helps a room stay easy to see without making it bright like morning."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words sound alike at the end, like bright and night. Rhymes can make a bedtime sentence feel calm and easy to remember."
        )
    ],
}
KNOWLEDGE_ORDER = ["briar", "shadow", "automatic", "nightlight", "rhyme"]


def generation_prompts(world: World) -> list[str]:
    room: Room = world.facts["room"]
    briar_cfg: Briar = world.facts["briar_cfg"]
    aid_cfg: Aid = world.facts["aid_cfg"]
    child: Entity = world.facts["child"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "appearance," "briar," and "automatic," and uses a gentle rhyme.',
        f"Tell a soft nighttime story where {child.attrs['name']} sees a frightening appearance on the wall, but it turns out to be {briar_cfg.the} outside {room.label}.",
        f"Write a sleepy story in which a grown-up fixes a window fright with {aid_cfg.phrase} and ends with a short rhyming comfort line.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    room: Room = world.facts["room"]
    briar_cfg: Briar = world.facts["briar_cfg"]
    aid_cfg: Aid = world.facts["aid_cfg"]
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    name = child.attrs["name"]
    pw = parent.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, who was getting ready to sleep, and {name}'s {pw}, who came to help. The story stays close to their room and follows how fear turns back into calm."
        ),
        (
            "What scared the child at first?",
            f"{name} saw a strange appearance on the wall and heard the window being brushed. The shape and sound came from {briar_cfg.the} moving in the moonlight."
        ),
        (
            f"Why did {name} call for {name}'s {pw}?",
            f"{name} called for {pw} because the room no longer felt ordinary or safe. Instead of hiding alone, {name} asked for help as soon as the fear grew big."
        ),
        (
            f"How did {name}'s {pw} solve the problem?",
            f"{pw.capitalize()} checked the window, showed that the fright was only {briar_cfg.the}, and moved it away from the pane. Then {pw} set {aid_cfg.phrase} by the bed so the room could keep its true shape."
        ),
        (
            "How did the story end?",
            f"It ended with a rhyme, a soft automatic glow, and a room that felt kind again. Once the real cause was known, {name} relaxed and fell asleep."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"briar", "shadow", "automatic", "rhyme"}
    aid_cfg: Aid = world.facts["aid_cfg"]
    if "nightlight" in aid_cfg.tags or "light" in aid_cfg.tags or "lamp" in aid_cfg.tags:
        tags.add("nightlight")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_room_briar(room: Room, briar: Briar) -> str:
    return (
        f"(No story: {briar.the} is too low to reach {room.label}'s window. "
        f"If it cannot brush the pane or throw a high shadow, there is no honest bedtime fright to explain.)"
    )


def explain_aid(aid: Aid, briar: Briar) -> str:
    if aid.sense < SENSE_MIN:
        return (
            f"(Refusing aid '{aid.id}': it is too weak on common sense for this world "
            f"(sense={aid.sense} < {SENSE_MIN}). A bedtime fix should reveal the cause and calm the room.)"
        )
    return (
        f"(No story: {aid.phrase} is not strong enough to settle fear caused by {briar.the}. "
        f"The chosen comfort must actually make the room feel safe again.)"
    )


ASP_RULES = r"""
hazard(Room, Briar) :- room(Room), briar(Briar), sill(Room, S), height(Briar, H), H >= S.
severity(Briar, 2)  :- thorny(Briar).
sensible(Aid)       :- aid(Aid), sense(Aid, S), sense_min(M), S >= M.
works(Aid, Briar)   :- aid(Aid), briar(Briar), power(Aid, P), severity(Briar, V), P >= V.
valid(Room, Briar, Aid) :- hazard(Room, Briar), sensible(Aid), works(Aid, Briar).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for room_id, room in ROOMS.items():
        lines.append(asp.fact("room", room_id))
        lines.append(asp.fact("sill", room_id, room.sill_height))
    for briar_id, briar in BRIARS.items():
        lines.append(asp.fact("briar", briar_id))
        lines.append(asp.fact("height", briar_id, briar.height))
        if briar.thorny:
            lines.append(asp.fact("thorny", briar_id))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("sense", aid_id, aid.sense))
        lines.append(asp.fact("power", aid_id, aid.power))
        if aid.automatic:
            lines.append(asp.fact("automatic", aid_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="### verify smoke")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(7))
        params.seed = 7
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("empty default story")
        print("OK: default seeded generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


CURATED = [
    StoryParams(
        room="small_bedroom",
        briar="rose_briar",
        aid="automatic_nightlight",
        child_name="Mina",
        child_gender="girl",
        parent="mother",
    ),
    StoryParams(
        room="eaves_room",
        briar="berry_briar",
        aid="automatic_star_lamp",
        child_name="Owen",
        child_gender="boy",
        parent="father",
    ),
    StoryParams(
        room="high_window_nursery",
        briar="rose_briar",
        aid="automatic_hall_glow",
        child_name="Nora",
        child_gender="girl",
        parent="mother",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bedtime appearance, a briar, and an automatic light."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--briar", choices=BRIARS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.room and args.briar:
        room = ROOMS[args.room]
        briar = BRIARS[args.briar]
        if not briar_reaches(room, briar):
            raise StoryError(explain_room_briar(room, briar))

    if args.aid and args.briar:
        aid = AIDS[args.aid]
        briar = BRIARS[args.briar]
        if aid.sense < SENSE_MIN or not aid_can_settle(aid, briar):
            raise StoryError(explain_aid(aid, briar))

    if args.aid and not args.briar:
        aid = AIDS[args.aid]
        if aid.sense < SENSE_MIN:
            raise StoryError(
                f"(Refusing aid '{aid.id}': it is too weak on common sense for this world "
                f"(sense={aid.sense} < {SENSE_MIN}).)"
            )

    combos = [
        combo
        for combo in valid_combos()
        if (args.room is None or combo[0] == args.room)
        and (args.briar is None or combo[1] == args.briar)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room_id, briar_id, aid_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        room=room_id,
        briar=briar_id,
        aid=aid_id,
        child_name=name,
        child_gender=gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"(Unknown room: {params.room})")
    if params.briar not in BRIARS:
        raise StoryError(f"(Unknown briar: {params.briar})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")

    room = ROOMS[params.room]
    briar = BRIARS[params.briar]
    aid = AIDS[params.aid]
    if not briar_reaches(room, briar):
        raise StoryError(explain_room_briar(room, briar))
    if aid.sense < SENSE_MIN or not aid_can_settle(aid, briar):
        raise StoryError(explain_aid(aid, briar))

    world = tell(
        room,
        briar,
        aid,
        child_name=params.child_name,
        child_type=params.child_gender,
        parent_type=params.parent,
    )
    story = world.render().replace("child", params.child_name)
    story = story.replace("parent", params.parent.capitalize())
    story = story.replace("the parent", params.parent)
    story = story.replace("child's", f"{params.child_name}'s")

    child = world.facts["child"]
    child.label = params.child_name
    child.attrs["name"] = params.child_name

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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (room, briar, aid) combos:\n")
        for room_id, briar_id, aid_id in combos:
            print(f"  {room_id:20} {briar_id:16} {aid_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.briar} at {p.room} with {p.aid}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
