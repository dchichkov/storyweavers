#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ijklmnop_opus_foreshadowing_dialogue_kindness_bedtime_story.py
===========================================================================================

A standalone story world for a gentle bedtime tale with foreshadowing, dialogue,
and kindness. A child sees a strange night shadow in the room, grows frightened,
and a kind helper reveals the ordinary cause in a calm, child-facing way.

This world is built around one small common-sense constraint:
a night shadow only makes sense when a room, a light, and a lumpy object can
really combine to cast it; and a bedtime response is only preferred when it is
both kind enough and revealing enough to calm the fear honestly.

Run it
------
    python storyworlds/worlds/gpt-5.4/ijklmnop_opus_foreshadowing_dialogue_kindness_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/ijklmnop_opus_foreshadowing_dialogue_kindness_bedtime_story.py --room bedroom --light moonbeam --source coat_chair
    python storyworlds/worlds/gpt-5.4/ijklmnop_opus_foreshadowing_dialogue_kindness_bedtime_story.py --source toy_basket
    python storyworlds/worlds/gpt-5.4/ijklmnop_opus_foreshadowing_dialogue_kindness_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/ijklmnop_opus_foreshadowing_dialogue_kindness_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/ijklmnop_opus_foreshadowing_dialogue_kindness_bedtime_story.py --verify
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
KINDNESS_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    casts_shadow: bool = False
    light_maker: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "sister", "woman"}
        male = {"boy", "father", "grandfather", "brother", "man"}
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
            "sister": "sister",
            "brother": "brother",
        }.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Room:
    id: str
    label: str
    bedtime_line: str
    window_side: bool
    hall_side: bool
    nook: str
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
class Light:
    id: str
    label: str
    phrase: str
    source_line: str
    needs: str
    spooky: str
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
class ShadowSource:
    id: str
    label: str
    phrase: str
    hint: str
    reveal: str
    scare: int
    needs_shape: str
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
class Response:
    id: str
    label: str
    kindness: int
    power: int
    text: str
    fail: str
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
    def __init__(self, room: Room) -> None:
        self.room_cfg = room
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
        clone = World(self.room_cfg)
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
    room = world.get("room")
    source = world.get("source")
    light = world.get("light")
    child = world.get("child")
    if room.meters["night_light"] < THRESHOLD:
        return []
    if source.meters["in_place"] < THRESHOLD or light.meters["shining"] < THRESHOLD:
        return []
    if source.attrs.get("shape") != world.facts.get("source_shape"):
        return []
    if light.attrs.get("side") != world.facts.get("light_side"):
        return []
    sig = ("shadow", source.id, light.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["shadow_big"] += 1
    child.memes["fear"] += float(world.facts["scare"])
    return ["__shadow__"]


def _r_reveal(world: World) -> list[str]:
    room = world.get("room")
    child = world.get("child")
    helper = world.get("helper")
    if helper.meters["reassuring"] < THRESHOLD:
        return []
    sig = ("reveal", helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if world.facts["response_power"] >= world.facts["scare"]:
        room.meters["shadow_big"] = 0.0
        child.memes["fear"] = 0.0
        child.memes["relief"] += 2
        child.memes["trust"] += 1
        helper.memes["love"] += 1
        return ["__calm__"]
    child.memes["fear"] = max(1.0, child.memes["fear"] - 1.0)
    child.memes["uncertain"] += 1
    helper.memes["care"] += 1
    return ["__soothe__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="shadow", tag="physical", apply=_r_shadow),
    Rule(name="reveal", tag="social", apply=_r_reveal),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def shadow_possible(room: Room, light: Light, source: ShadowSource) -> bool:
    if light.needs == "window" and not room.window_side:
        return False
    if light.needs == "hall" and not room.hall_side:
        return False
    return source.needs_shape == light.needs


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.kindness >= KINDNESS_MIN]


def shadow_severity(source: ShadowSource) -> int:
    return source.scare


def fully_comforted(response: Response, source: ShadowSource) -> bool:
    return response.power >= shadow_severity(source)


def predict_shadow(world: World) -> dict:
    sim = world.copy()
    sim.get("room").meters["night_light"] = 1.0
    sim.get("source").meters["in_place"] = 1.0
    sim.get("light").meters["shining"] = 1.0
    propagate(sim, narrate=False)
    return {
        "shadow": sim.get("room").meters["shadow_big"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"],
    }


def open_story(world: World, child: Entity, helper: Entity, room: Room) -> None:
    child.memes["sleepy"] += 1
    helper.memes["care"] += 1
    world.say(
        f"It was bedtime in {room.label}. {room.bedtime_line}"
    )
    world.say(
        f"{child.id} had tucked a small alphabet card beside the pillow. On it, the letters "
        f'"ijklmnop" curved in sleepy crayon, and beneath them {child.pronoun("possessive")} '
        f"helper had written the word opus because it sounded grand for such a tiny song."
    )
    world.say(
        f'{helper.label_word.capitalize()} sat on the edge of the bed and said, '
        f'"When the room grows quiet, we will hum our little bedtime opus together."'
    )


def foreshadow(world: World, room: Room, light: Light, source: ShadowSource) -> None:
    world.say(
        f"Near {room.nook}, {source.hint}. At the same time, {light.source_line}"
    )


def lights_lower(world: World, light: Light) -> None:
    room = world.get("room")
    source = world.get("source")
    lamp = world.get("light")
    room.meters["night_light"] = 1.0
    source.meters["in_place"] = 1.0
    lamp.meters["shining"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Soon the room was darker, and {light.spooky} stretched across the wall."
    )


def notice_shadow(world: World, child: Entity) -> None:
    world.say(
        f'{child.id} sat up and whispered, "Who is that by the wall?"'
    )


def ask_for_help(world: World, child: Entity, helper: Entity) -> None:
    pred = predict_shadow(world)
    world.facts["predicted_shadow"] = pred["shadow"]
    world.facts["predicted_fear"] = pred["fear"]
    child.memes["fear"] = pred["fear"]
    world.say(
        f'"{helper.label_word.capitalize()}," {child.id} said, "it looks too tall and wiggly for this room."'
    )


def kind_response(world: World, child: Entity, helper: Entity, response: Response) -> None:
    helper.meters["reassuring"] = 1.0
    child.memes["heard"] += 1
    if response.kindness >= 3:
        world.say(
            f'{helper.label_word.capitalize()} answered at once, "{response.text} I will stay right here while we look together."'
        )
    else:
        world.say(
            f'{helper.label_word.capitalize()} answered softly, "{response.text}"'
        )
    propagate(world, narrate=False)


def reveal_success(world: World, child: Entity, helper: Entity, source: ShadowSource, response: Response) -> None:
    world.say(
        f"{helper.label_word.capitalize()} showed the wall, then the corner, then {source.reveal}. "
        f'The shadow melted back into an ordinary {source.label}.'
    )
    world.say(
        f'"See?" {helper.pronoun()} said. "Nothing spooky came in. The room was only making a giant picture."'
    )
    world.say(
        f'{child.id} let out a long breath. "So it was our room all along," {child.pronoun()} said.'
    )
    child.memes["joy"] += 1
    helper.memes["love"] += 1


def reveal_partial(world: World, child: Entity, helper: Entity, source: ShadowSource, response: Response) -> None:
    world.say(
        f"{helper.label_word.capitalize()} tried to help, but the shape still looked bigger than {source.label} from the bed."
    )
    world.say(
        f'"It is only {source.label}," {helper.pronoun()} said, "but big shadows can still feel surprising."'
    )
    world.say(
        f"So {helper.pronoun()} left a warm light low, held {child.id}'s hand, and stayed until the breathing in the room grew slower."
    )
    child.memes["sleepy"] += 1


def bedtime_close(world: World, child: Entity, helper: Entity) -> None:
    card = world.get("card")
    card.meters["kept"] = 1.0
    child.memes["sleepy"] += 1
    world.say(
        f"Then they hummed the tiny alphabet opus together, all the way through ijklmnop and on into the soft last letters."
    )
    world.say(
        f'{child.id} smiled into the pillow. "{helper.label_word.capitalize()}, the room feels little again," {child.pronoun()} murmured.'
    )
    world.say(
        f"Before long, the wall held only quiet shadows, the card rested by the pillow, and {child.id} drifted to sleep."
    )


def bedtime_close_gentle(world: World, child: Entity, helper: Entity) -> None:
    child.memes["sleepy"] += 1
    world.say(
        f"They did not sing the whole opus that night. Instead, {helper.label_word} hummed only ijklmnop very slowly, like stepping-stones into sleep."
    )
    world.say(
        f"With a hand to hold and a small light glowing, {child.id} finally settled under the blanket."
    )


def tell(
    room: Room,
    light: Light,
    source: ShadowSource,
    response: Response,
    *,
    child_name: str = "Mina",
    child_type: str = "girl",
    helper_type: str = "mother",
    trait: str = "gentle",
) -> World:
    world = World(room=room)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
        role="child",
        traits=[trait],
        attrs={"trait": trait},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
        attrs={"relation": helper_type},
    ))
    room_ent = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label=room.label,
    ))
    light_ent = world.add(Entity(
        id="light",
        kind="thing",
        type="light",
        label=light.label,
        light_maker=True,
        attrs={"side": light.needs},
    ))
    source_ent = world.add(Entity(
        id="source",
        kind="thing",
        type="source",
        label=source.label,
        casts_shadow=True,
        attrs={"shape": source.needs_shape},
    ))
    card = world.add(Entity(
        id="card",
        kind="thing",
        type="paper",
        label="alphabet card",
    ))

    world.facts.update(
        room=room,
        light=light,
        source_cfg=source,
        response=response,
        child=child,
        helper=helper,
        source_shape=source.needs_shape,
        light_side=light.needs,
        scare=source.scare,
        response_power=response.power,
        response_kindness=response.kindness,
        outcome="?",
    )

    open_story(world, child, helper, room)
    foreshadow(world, room, light, source)

    world.para()
    lights_lower(world, light)
    notice_shadow(world, child)
    ask_for_help(world, child, helper)

    world.para()
    kind_response(world, child, helper, response)
    if fully_comforted(response, source):
        reveal_success(world, child, helper, source, response)
        world.para()
        bedtime_close(world, child, helper)
        outcome = "revealed"
    else:
        reveal_partial(world, child, helper, source, response)
        world.para()
        bedtime_close_gentle(world, child, helper)
        outcome = "dimmed"

    world.facts["outcome"] = outcome
    world.facts["shadow_seen"] = world.get("room").meters["shadow_big"] < THRESHOLD or True
    world.facts["fully_comforted"] = outcome == "revealed"
    world.facts["card_kept"] = world.get("card").meters["kept"] >= THRESHOLD
    return world


ROOMS = {
    "bedroom": Room(
        id="bedroom",
        label="the little bedroom",
        bedtime_line="A blue quilt made a hill over the bed, and a cup of water shone on the nightstand.",
        window_side=True,
        hall_side=True,
        nook="the reading chair",
        tags={"bedroom"},
    ),
    "attic_room": Room(
        id="attic_room",
        label="the attic room",
        bedtime_line="The slanted ceiling tucked down low, and the blankets smelled faintly of cedar.",
        window_side=True,
        hall_side=False,
        nook="the old trunk",
        tags={"attic"},
    ),
    "cabin_nook": Room(
        id="cabin_nook",
        label="the cabin sleeping nook",
        bedtime_line="Pine boards glowed honey-brown, and the blanket had little stars stitched along the edge.",
        window_side=True,
        hall_side=True,
        nook="the peg by the door",
        tags={"cabin"},
    ),
}

LIGHTS = {
    "moonbeam": Light(
        id="moonbeam",
        label="moonbeam",
        phrase="a pale moonbeam",
        source_line="a moonbeam slipped through the window and laid a silver stripe across the floor.",
        needs="window",
        spooky="a long silver shape",
        tags={"moon", "shadow"},
    ),
    "hallglow": Light(
        id="hallglow",
        label="hall light",
        phrase="a stripe of hall light",
        source_line="a stripe of golden light slipped in from the hall.",
        needs="hall",
        spooky="a tall amber shape",
        tags={"light", "shadow"},
    ),
}

SOURCES = {
    "coat_chair": ShadowSource(
        id="coat_chair",
        label="chair with a coat",
        phrase="a chair with a coat draped over it",
        hint="a coat had slipped across the back of a chair and one sleeve hung lower than the other",
        reveal="the sagging sleeve on the chair",
        scare=2,
        needs_shape="window",
        tags={"coat", "shadow"},
    ),
    "laundry_pile": ShadowSource(
        id="laundry_pile",
        label="pile of folded laundry",
        phrase="a pile of folded laundry",
        hint="a stack of folded laundry leaned a little crooked on the trunk",
        reveal="the leaning stack of pajamas and towels",
        scare=3,
        needs_shape="window",
        tags={"laundry", "shadow"},
    ),
    "peg_robe": ShadowSource(
        id="peg_robe",
        label="robe on a peg",
        phrase="a robe hanging on a peg",
        hint="a robe hung from the peg by the door, full and still",
        reveal="the robe's belt and sleeves hanging from the peg",
        scare=1,
        needs_shape="hall",
        tags={"robe", "shadow"},
    ),
    "toy_basket": ShadowSource(
        id="toy_basket",
        label="toy basket",
        phrase="a low toy basket",
        hint="a toy basket sat under a shelf, round and small",
        reveal="the toy basket under the shelf",
        scare=0,
        needs_shape="window",
        tags={"toys"},
    ),
}

RESPONSES = {
    "lamp_and_show": Response(
        id="lamp_and_show",
        label="turn on the lamp and show the corner",
        kindness=3,
        power=3,
        text="Let us turn on the little lamp and see what the room is trying to say.",
        fail="The lamp came on, but the shape still looked puzzling from the bed.",
        qa_text="turned on the lamp and showed the corner",
        tags={"lamp", "kindness"},
    ),
    "walk_and_explain": Response(
        id="walk_and_explain",
        label="walk over together and explain",
        kindness=3,
        power=2,
        text="Come close to me, and we will walk there together with slow feet.",
        fail="They walked closer, but the shape still felt very large at first.",
        qa_text="walked over with the child and explained the shadow",
        tags={"explain", "kindness"},
    ),
    "hug_and_hum": Response(
        id="hug_and_hum",
        label="hug and hum",
        kindness=2,
        power=1,
        text="I will hug you first, and then we will listen carefully together.",
        fail="The humming was kind, but it did not fully explain the shape.",
        qa_text="hugged the child and hummed softly",
        tags={"hug", "kindness", "song"},
    ),
    "call_from_door": Response(
        id="call_from_door",
        label="call from the doorway",
        kindness=1,
        power=1,
        text="It is probably nothing. Try to lie down again.",
        fail="The words came from the doorway and did not help much.",
        qa_text="called from the doorway",
        tags={"weak"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Ella", "Lucy", "Sana", "Ivy"]
BOY_NAMES = ["Owen", "Theo", "Ben", "Max", "Eli", "Noah", "Finn", "Milo"]
TRAITS = ["gentle", "sleepy", "thoughtful", "tender-hearted", "quiet", "curious"]


@dataclass
class StoryParams:
    room: str
    light: str
    source: str
    response: str
    child_name: str
    child_type: str
    helper_type: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for room_id, room in ROOMS.items():
        for light_id, light in LIGHTS.items():
            for source_id, source in SOURCES.items():
                if source.scare <= 0:
                    continue
                if shadow_possible(room, light, source):
                    combos.append((room_id, light_id, source_id))
    return sorted(combos)


KNOWLEDGE = {
    "shadow": [(
        "What makes a shadow look big at night?",
        "A shadow can look big when a light shines from the side and stretches the shape across a wall. At night, a familiar object can seem strange because the room is darker."
    )],
    "moon": [(
        "Why does moonlight change how a room looks?",
        "Moonlight is dim and silvery, so it hides some details and shows others. That can make ordinary things look different from across the room."
    )],
    "light": [(
        "Why can turning on a lamp help when something looks scary?",
        "A lamp adds more light, so you can see the real shape more clearly. When you understand what you are seeing, it often feels less frightening."
    )],
    "kindness": [(
        "What is a kind way to help someone at bedtime?",
        "A kind helper stays close, speaks softly, and listens before trying to fix the problem. That helps the worried person feel safe enough to look again."
    )],
    "song": [(
        "How can a soft song help at bedtime?",
        "A soft song gives your mind something gentle to follow. The steady sound can help your breathing slow down and your body feel calmer."
    )],
    "coat": [(
        "Why might a coat on a chair look strange in the dark?",
        "A draped coat can make bumpy shapes with sleeves sticking out. In dim light, your eyes may turn that shape into something much bigger."
    )],
    "laundry": [(
        "Why can a pile of laundry make funny shadows?",
        "Folded clothes can lean and make uneven corners. When light hits them from the side, those corners can turn into a tall shadow."
    )],
    "robe": [(
        "Why can a hanging robe look spooky at night?",
        "A hanging robe has long sleeves and a belt, so it can look like arms or a body in dim light. When the room gets brighter, it usually looks ordinary again."
    )],
}
KNOWLEDGE_ORDER = ["shadow", "moon", "light", "kindness", "song", "coat", "laundry", "robe"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    source = world.facts["source_cfg"]
    light = world.facts["light"]
    response = world.facts["response"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "ijklmnop" and "opus". Use foreshadowing so a {source.label} seems ordinary at first and spooky later.',
        f"Tell a gentle night story where {child.id} sees a shadow made by {light.label}, speaks in dialogue to {helper.label_word}, and is helped with kindness.",
        f"Write a calm story in which a child grows worried at bedtime, a grown-up or older helper answers kindly, and the ending proves the room is safe again with {response.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    room = world.facts["room"]
    light = world.facts["light"]
    source = world.facts["source_cfg"]
    response = world.facts["response"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} at bedtime and {helper.label_word}, who came to help in {room.label}. The story stays small and quiet because the problem happens right there in the room."
        ),
        (
            "What made the room feel scary?",
            f"The strange shape came from {light.phrase} and {source.phrase}. The room looked scary because the light stretched that ordinary object into a much bigger shadow."
        ),
        (
            'Why were the words "ijklmnop" and "opus" in the story?',
            f'{child.id} had a little alphabet bedtime card, and the helper called their tiny song an opus. That made the bedtime ritual feel special and gentle instead of frightening.'
        ),
        (
            f"How did {helper.label_word} answer when {child.id} got scared?",
            f"{helper.label_word.capitalize()} answered with calm words and stayed close instead of brushing the fear away. That kindness mattered because {child.id} felt safe enough to look again."
        ),
    ]
    if outcome == "revealed":
        qa.append((
            "How was the problem solved?",
            f"{helper.label_word.capitalize()} {response.qa_text} and showed the real cause of the shadow. Once {child.id} could see the ordinary object, the fear disappeared and bedtime could begin again."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with a soft alphabet song and a peaceful room. The ending image proves what changed because the wall held only quiet shadows and {child.id} fell asleep."
        ))
    else:
        qa.append((
            "Was the shadow fully explained right away?",
            f"Not quite. The helper made the room gentler and stayed nearby, so the fear became smaller even before everything felt fully ordinary."
        ))
        qa.append((
            "How did the helper still show kindness at the end?",
            f"{helper.label_word.capitalize()} kept a light on low, held a hand, and hummed slowly. Even without a perfect fix at once, the kindness helped {child.id} settle enough to sleep."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"shadow", "kindness"} | set(world.facts["light"].tags) | set(world.facts["response"].tags) | set(world.facts["source_cfg"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        room="bedroom",
        light="moonbeam",
        source="coat_chair",
        response="lamp_and_show",
        child_name="Mina",
        child_type="girl",
        helper_type="mother",
        trait="gentle",
    ),
    StoryParams(
        room="attic_room",
        light="moonbeam",
        source="laundry_pile",
        response="walk_and_explain",
        child_name="Theo",
        child_type="boy",
        helper_type="grandmother",
        trait="thoughtful",
    ),
    StoryParams(
        room="cabin_nook",
        light="hallglow",
        source="peg_robe",
        response="hug_and_hum",
        child_name="Lucy",
        child_type="girl",
        helper_type="father",
        trait="quiet",
    ),
]


def explain_rejection(room: Room, light: Light, source: ShadowSource) -> str:
    if source.scare <= 0:
        return (
            f"(No story: {source.phrase} is too low and ordinary to make a bedtime fright here. "
            f"Pick a source with a larger, stranger shape, like a coat on a chair or a laundry pile.)"
        )
    need = "window light" if light.needs == "window" else "hall light"
    return (
        f"(No story: {source.phrase} does not line up with {light.label} in {room.label}. "
        f"This shadow needs {need} from the right side to stretch into a scary shape.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it is too unkind for this world "
        f"(kindness={r.kindness} < {KINDNESS_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    source = SOURCES[params.source]
    response = RESPONSES[params.response]
    return "revealed" if fully_comforted(response, source) else "dimmed"


ASP_RULES = r"""
shadow_possible(R, L, S) :- room(R), light(L), source(S), scare(S, C), C > 0,
                            light_needs(L, window), room_window(R), source_shape(S, window).
shadow_possible(R, L, S) :- room(R), light(L), source(S), scare(S, C), C > 0,
                            light_needs(L, hall), room_hall(R), source_shape(S, hall).

sensible_response(X) :- response(X), kindness(X, K), kindness_min(M), K >= M.

outcome(revealed) :- chosen_source(S), chosen_response(R), scare(S, C), power(R, P), P >= C.
outcome(dimmed)   :- chosen_source(S), chosen_response(R), scare(S, C), power(R, P), P < C.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for room_id, room in ROOMS.items():
        lines.append(asp.fact("room", room_id))
        if room.window_side:
            lines.append(asp.fact("room_window", room_id))
        if room.hall_side:
            lines.append(asp.fact("room_hall", room_id))
    for light_id, light in LIGHTS.items():
        lines.append(asp.fact("light", light_id))
        lines.append(asp.fact("light_needs", light_id, light.needs))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("scare", source_id, source.scare))
        lines.append(asp.fact("source_shape", source_id, source.needs_shape))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("kindness", rid, response.kindness))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("kindness_min", KINDNESS_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show shadow_possible/3."))
    return sorted(set(asp.atoms(model, "shadow_possible")))


def asp_sensible_responses() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_response/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_response"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_source", params.source),
        asp.fact("chosen_response", params.response),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {r.id for r in sensible_responses()}
    asp_sensible = set(asp_sensible_responses())
    if py_sensible == asp_sensible:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(asp_sensible)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            rc = 1
            print(f"Unexpected resolve_params failure at seed {s}.")
            continue
        p.seed = s
        cases.append(p)

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime storyworld: a child sees a night shadow, and a kind helper reveals what changed the room."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather", "sister", "brother"])
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
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
    if args.source and args.source not in SOURCES:
        raise StoryError(f"(Unknown source: {args.source})")
    if args.room and args.room not in ROOMS:
        raise StoryError(f"(Unknown room: {args.room})")
    if args.light and args.light not in LIGHTS:
        raise StoryError(f"(Unknown light: {args.light})")
    if args.response and args.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {args.response})")

    if args.response and RESPONSES[args.response].kindness < KINDNESS_MIN:
        raise StoryError(explain_response(args.response))

    if args.room and args.light and args.source:
        room = ROOMS[args.room]
        light = LIGHTS[args.light]
        source = SOURCES[args.source]
        if not shadow_possible(room, light, source) or source.scare <= 0:
            raise StoryError(explain_rejection(room, light, source))

    combos = [
        c for c in valid_combos()
        if (args.room is None or c[0] == args.room)
        and (args.light is None or c[1] == args.light)
        and (args.source is None or c[2] == args.source)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room_id, light_id, source_id = rng.choice(combos)
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_type = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather", "sister", "brother"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        room=room_id,
        light=light_id,
        source=source_id,
        response=response_id,
        child_name=child_name,
        child_type=child_type,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"(Unknown room: {params.room})")
    if params.light not in LIGHTS:
        raise StoryError(f"(Unknown light: {params.light})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    room = ROOMS[params.room]
    light = LIGHTS[params.light]
    source = SOURCES[params.source]
    response = RESPONSES[params.response]

    if not shadow_possible(room, light, source) or source.scare <= 0:
        raise StoryError(explain_rejection(room, light, source))
    if response.kindness < KINDNESS_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        room=room,
        light=light,
        source=source,
        response=response,
        child_name=params.child_name,
        child_type=params.child_type,
        helper_type=params.helper_type,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show shadow_possible/3.\n#show sensible_response/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible_responses())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (room, light, source) combos:\n")
        for room, light, source in combos:
            print(f"  {room:11} {light:9} {source}")
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
            header = f"### {p.child_name}: {p.source} in {p.room} ({p.light}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
