#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ottoman_quest_conflict_space_adventure.py
====================================================================

A standalone story world for a tiny "space adventure" domain: two children turn
the living room into a spaceship, an important mission item slips under a piece
of furniture, one child wants to solve it with an unsafe shortcut, and a calm
grown-up helps them finish the quest the safe way.

The seed asked for:
- the word "ottoman"
- Quest
- Conflict
- Space Adventure style

This world builds a small simulation around that premise. The children have a
clear quest (recover the mission item to complete the pretend mission), a real
conflict (trying to move heavy furniture alone vs. asking for help), and a
resolution driven by world state rather than slot-filling prose.

Run it
------
    python storyworlds/worlds/gpt-5.4/ottoman_quest_conflict_space_adventure.py
    python storyworlds/worlds/gpt-5.4/ottoman_quest_conflict_space_adventure.py --spot ottoman
    python storyworlds/worlds/gpt-5.4/ottoman_quest_conflict_space_adventure.py --response broom_poke
    python storyworlds/worlds/gpt-5.4/ottoman_quest_conflict_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/ottoman_quest_conflict_space_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/ottoman_quest_conflict_space_adventure.py --verify
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


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "thoughtful", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    heavy: bool = False
    dark: bool = False
    metallic: bool = False
    soft: bool = False
    fragile: bool = False
    # physical
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    # emotional / social
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Theme:
    id: str
    scene: str
    rig: str
    captain: str
    scout: str
    goal: str
    send_off: str
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
    mission_use: str
    metallic: bool = False
    soft: bool = False
    fragile: bool = False
    flat: bool = False
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
class Spot:
    id: str
    label: str
    the: str
    depth: int
    heavy: bool
    dark: bool
    slide_text: str
    warning_text: str
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
class Response:
    id: str
    sense: int
    mode: str
    reach: int
    gentle: bool
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_hidden_worry(world: World) -> list[str]:
    out: list[str] = []
    item = world.entities.get("item")
    spot = world.entities.get("spot")
    if item is None or spot is None:
        return out
    if item.meters["hidden"] < THRESHOLD or not spot.dark:
        return out
    sig = ("hidden_worry", item.id, spot.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
    out.append("__worry__")
    return out


def _r_wobble_risk(world: World) -> list[str]:
    out: list[str] = []
    spot = world.entities.get("spot")
    if spot is None:
        return out
    if spot.meters["pulled"] < THRESHOLD or not spot.heavy:
        return out
    sig = ("wobble_risk", spot.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["risk"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__risk__")
    return out


def _r_item_slides(world: World) -> list[str]:
    out: list[str] = []
    item = world.entities.get("item")
    spot = world.entities.get("spot")
    if item is None or spot is None:
        return out
    if spot.meters["pulled"] < THRESHOLD or item.meters["hidden"] < THRESHOLD:
        return out
    sig = ("item_slides", item.id, spot.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["deeper"] += 1
    out.append("__slide__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="hidden_worry", tag="emotional", apply=_r_hidden_worry),
    Rule(name="wobble_risk", tag="physical", apply=_r_wobble_risk),
    Rule(name="item_slides", tag="physical", apply=_r_item_slides),
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


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def response_works(response: Response, item: LostItem, spot: Spot) -> bool:
    if response.reach < spot.depth:
        return False
    if response.mode == "magnet":
        return item.metallic
    if response.mode == "grab":
        if item.flat and not item.soft:
            return False
        if item.fragile and not response.gentle:
            return False
        return True
    if response.mode == "lift":
        return True
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme_id in THEMES:
        for item_id, item in ITEMS.items():
            for spot_id, spot in SPOTS.items():
                for response_id, response in RESPONSES.items():
                    if response.sense >= SENSE_MIN and response_works(response, item, spot):
                        combos.append((theme_id, item_id, spot_id, response_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_risk(world: World) -> dict:
    sim = world.copy()
    spot = sim.get("spot")
    spot.meters["pulled"] += 1
    propagate(sim, narrate=False)
    return {
        "room_risk": sim.get("room").meters["risk"],
        "item_deeper": sim.get("item").meters["deeper"],
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} turned the living room into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{theme.captain} {a.id} and {theme.scout} {b.id}!" {a.id} said. '
        f'"Today we finish {theme.goal}."'
    )


def quest_object(world: World, a: Entity, b: Entity, item: LostItem) -> None:
    world.say(
        f"The mission needed {item.phrase}. Without it, the crew could not {item.mission_use}."
    )
    world.say(
        f"{b.id} carried the little treasure carefully while {a.id} counted down the launch."
    )


def accident(world: World, item_ent: Entity, item: LostItem, spot: Spot) -> None:
    item_ent.meters["hidden"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But just as the ship was about to blast off, {item.phrase} slipped from small fingers, "
        f"skittered across the rug, and vanished under {spot.the}."
    )
    if spot.dark:
        world.say(
            f"A dark gap waited there like space between stars, and suddenly the room felt quieter."
        )
    else:
        world.say(
            f"It stopped in a tricky little place where no one could quite reach it."
        )


def tempt(world: World, a: Entity, spot: Spot) -> None:
    a.memes["bravado"] += 1
    if spot.heavy:
        world.say(
            f'{a.id} dropped to {a.pronoun("possessive")} knees. "I can pull {spot.the} myself," '
            f'{a.pronoun()} said. "Then our quest can keep going."'
        )
    else:
        world.say(
            f'{a.id} leaned close. "I can reach under {spot.the} by myself," {a.pronoun()} said. '
            f'"We do not have time to wait."'
        )


def warn(world: World, b: Entity, a: Entity, spot: Spot, parent: Entity) -> None:
    pred = predict_risk(world)
    world.facts["predicted_risk"] = pred["room_risk"]
    world.facts["predicted_deeper"] = pred["item_deeper"]
    b.memes["caution"] += 1
    world.say(
        f'{b.id} caught {a.id}\'s sleeve. "{spot.warning_text} {parent.label_word.capitalize()} '
        f'can help us do this the safe way."'
    )


def defy(world: World, a: Entity, b: Entity, spot_ent: Entity, spot: Spot) -> None:
    a.memes["defiance"] += 1
    if spot.heavy:
        world.say(
            f'"We are space heroes," {a.id} said, and tugged at the edge of {spot.the} anyway.'
        )
    else:
        world.say(
            f'"We are almost there," {a.id} said, and shoved {a.pronoun("possessive")} arm toward '
            f'the gap anyway.'
        )
    spot_ent.meters["pulled"] += 1
    propagate(world, narrate=False)
    if world.get("room").meters["risk"] >= THRESHOLD:
        world.say(
            f"{spot.The} gave a small wobble that made both children freeze."
        )
    if world.get("item").meters["deeper"] >= THRESHOLD:
        world.say(spot.slide_text)


def back_down(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked at the dark gap again, then slowly nodded. "Okay," {a.pronoun()} said. '
        f'"Real captains ask for help before they make a bigger problem."'
    )
    world.say(
        f"So the crew left the trapped treasure where it was and called for {parent.label_word}."
    )


def rescue(world: World, parent: Entity, item_ent: Entity, item: LostItem,
           spot: Spot, response: Response) -> None:
    item_ent.meters["hidden"] = 0.0
    item_ent.meters["retrieved"] += 1
    world.get("room").meters["risk"] = 0.0
    for kid in world.kids():
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["hope"] += 1
    body = response.text.format(spot=spot.label, item=item.label)
    world.say(
        f"{parent.label_word.capitalize()} came in, listened fast, and {body}."
    )
    world.say(
        f"In one careful moment, {item.phrase} slid back into the light."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, spot: Spot) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f"Then {parent.label_word.capitalize()} knelt beside them. "
        f'"Quests can wait for one safe minute," {parent.pronoun()} said softly. '
        f'"Heavy things like {spot.the} are for grown-up hands to move."'
    )
    world.say(
        f'{a.id} and {b.id} nodded. The mission suddenly felt calmer than before.'
    )


def finish_quest(world: World, a: Entity, b: Entity, theme: Theme, item: LostItem) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"With {item.phrase} back on board, the crew could finally {item.mission_use}."
    )
    world.say(
        f"{a.id} tucked it into the pretend control panel, {b.id} made a long whooshing sound, "
        f"and together they {theme.send_off}."
    )
    world.say(
        "This time, the spaceship felt brave not because it rushed, but because it was careful."
    )


def tell(theme: Theme, item: LostItem, spot: Spot, response: Response,
         instigator: str = "Nova", instigator_gender: str = "girl",
         cautioner: str = "Leo", cautioner_gender: str = "boy",
         trait: str = "careful", parent_type: str = "mother",
         instigator_age: int = 5, cautioner_age: int = 7,
         relation: str = "siblings", trust: int = 6) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        traits=["bold"],
        age=instigator_age,
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        traits=[trait],
        age=cautioner_age,
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    world.add(Entity(id="room", type="room", label="the room"))
    spot_ent = world.add(Entity(
        id="spot",
        type="furniture",
        label=spot.label,
        heavy=spot.heavy,
        dark=spot.dark,
    ))
    item_ent = world.add(Entity(
        id="item",
        type="mission_item",
        label=item.label,
        metallic=item.metallic,
        soft=item.soft,
        fragile=item.fragile,
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)

    world.facts.update(
        theme=theme,
        item_cfg=item,
        spot_cfg=spot,
        response=response,
        instigator=a,
        cautioner=b,
        parent=parent,
        relation=relation,
    )

    play_setup(world, a, b, theme)
    quest_object(world, a, b, item)

    world.para()
    accident(world, item_ent, item, spot)
    tempt(world, a, spot)
    warn(world, b, a, spot, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    world.para()
    if averted:
        back_down(world, a, b, parent)
    else:
        defy(world, a, b, spot_ent, spot)

    world.para()
    rescue(world, parent, item_ent, item, spot, response)
    lesson(world, parent, a, b, spot)

    world.para()
    finish_quest(world, a, b, theme, item)

    world.facts.update(
        outcome="averted" if averted else "rescued",
        hidden=item_ent.meters["retrieved"] < THRESHOLD,
        rescued=item_ent.meters["retrieved"] >= THRESHOLD,
        risk=world.get("room").meters["risk"],
        promised=a.memes["lesson"] >= THRESHOLD,
    )
    return world


THEMES = {
    "star_patrol": Theme(
        id="star_patrol",
        scene="a silver starship crossing a sleepy galaxy",
        rig="The couch was the command deck, a blanket became the night sky, and the ottoman was the moon pod docked beside the ship.",
        captain="Captain",
        scout="Scout",
        goal="the Star Patrol mission",
        send_off="sailed past the couch-arm nebula toward a make-believe moon",
        tags={"space"},
    ),
    "comet_run": Theme(
        id="comet_run",
        scene="a quick rocket racing after a bright comet",
        rig="The couch was the rocket bridge, paper stars were taped to the wall, and the ottoman was a bumpy little landing moon.",
        captain="Commander",
        scout="Navigator",
        goal="the comet chase",
        send_off="zoomed through the living room sky after the silver comet",
        tags={"space"},
    ),
    "nebula_rescue": Theme(
        id="nebula_rescue",
        scene="a rescue ship gliding through a purple nebula",
        rig="The couch was the rescue ship, cushions became meteor clouds, and the ottoman waited nearby like a rocky station.",
        captain="Captain",
        scout="Pilot",
        goal="the rescue launch",
        send_off="glided out through the blanket stars to finish the rescue",
        tags={"space"},
    ),
}

ITEMS = {
    "star_key": LostItem(
        id="star_key",
        label="star key",
        phrase="the tiny star key",
        mission_use="open the moon gate",
        metallic=True,
        flat=True,
        tags={"metal", "key"},
    ),
    "captain_badge": LostItem(
        id="captain_badge",
        label="captain badge",
        phrase="the shiny captain badge",
        mission_use="wake the blinking beacon",
        metallic=True,
        flat=True,
        tags={"metal", "badge"},
    ),
    "plush_alien": LostItem(
        id="plush_alien",
        label="plush alien",
        phrase="the little plush alien",
        mission_use="guide the ship home",
        soft=True,
        tags={"plush"},
    ),
    "glow_cube": LostItem(
        id="glow_cube",
        label="glow cube",
        phrase="the glowing cube",
        mission_use="light the map screen",
        fragile=True,
        tags={"glow", "fragile"},
    ),
}

SPOTS = {
    "ottoman": Spot(
        id="ottoman",
        label="ottoman",
        the="the ottoman",
        depth=2,
        heavy=True,
        dark=True,
        slide_text="Instead of coming out, the mission piece scooted farther back under the ottoman where the shadows were thicker.",
        warning_text="Do not pull the ottoman alone. It is heavy, and little fingers can get pinched.",
        tags={"ottoman", "heavy_furniture", "dark_space"},
    ),
    "sofa": Spot(
        id="sofa",
        label="sofa",
        the="the sofa",
        depth=2,
        heavy=True,
        dark=True,
        slide_text="Instead of popping free, the mission piece slid deeper under the sofa where nobody could reach it by hand.",
        warning_text="Do not tug the sofa alone. Heavy furniture can wobble and trap fingers.",
        tags={"heavy_furniture", "dark_space"},
    ),
    "bookshelf": Spot(
        id="bookshelf",
        label="bookshelf",
        the="the low bookshelf",
        depth=1,
        heavy=True,
        dark=False,
        slide_text="The mission piece scraped along the floor and hid itself even farther under the low bookshelf.",
        warning_text="Do not shove the bookshelf around by yourself. Heavy furniture needs grown-up help.",
        tags={"heavy_furniture"},
    ),
}

RESPONSES = {
    "magnet_wand": Response(
        id="magnet_wand",
        sense=3,
        mode="magnet",
        reach=3,
        gentle=True,
        text="switched on a flashlight, slid a magnet wand under the {spot}, and drew the {item} back slowly",
        qa_text="used a flashlight and a magnet wand to pull the item out",
        tags={"flashlight", "magnet", "ask_adult"},
    ),
    "grabber": Response(
        id="grabber",
        sense=3,
        mode="grab",
        reach=3,
        gentle=True,
        text="lay flat on the rug, reached a long grabber under the {spot}, and pinched the {item} gently",
        qa_text="used a long grabber to reach under the furniture and lift the item out",
        tags={"grabber", "ask_adult"},
    ),
    "lift_together": Response(
        id="lift_together",
        sense=3,
        mode="lift",
        reach=2,
        gentle=True,
        text="held the {spot} steady with grown-up hands, lifted just enough space, and picked up the {item}",
        qa_text="lifted the furniture safely and picked the item up",
        tags={"heavy_furniture", "ask_adult"},
    ),
    "broom_poke": Response(
        id="broom_poke",
        sense=1,
        mode="grab",
        reach=2,
        gentle=False,
        text="poked around with a broom until the {item} came out",
        qa_text="poked around with a broom",
        tags={"broom"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mia", "Zoe", "Ava", "Iris", "Nora", "Skye"]
BOY_NAMES = ["Leo", "Max", "Finn", "Theo", "Eli", "Kai", "Milo", "Noah"]
TRAITS = ["careful", "cautious", "steady", "thoughtful", "curious", "brave", "sensible"]


@dataclass
class StoryParams:
    theme: str
    item: str
    spot: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    instigator_age: int = 5
    cautioner_age: int = 7
    relation: str = "siblings"
    trust: int = 6
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
    "ottoman": [
        (
            "What is an ottoman?",
            "An ottoman is a low, padded piece of furniture people use to rest their feet or sit on. Because it is still furniture, children should not try to shove or lift it alone.",
        )
    ],
    "heavy_furniture": [
        (
            "Why should a child ask a grown-up before moving heavy furniture?",
            "Heavy furniture can wobble, pinch fingers, or fall the wrong way. A grown-up can hold it steady and move it safely.",
        )
    ],
    "dark_space": [
        (
            "Why is it hard to find something in a dark space under furniture?",
            "It is hard because the shadows hide the object and you cannot see where your hand is going. A light helps you aim instead of guessing.",
        )
    ],
    "magnet": [
        (
            "What does a magnet do?",
            "A magnet can pull some metal things toward it without grabbing them with fingers. That makes it useful for small metal objects in tricky places.",
        )
    ],
    "grabber": [
        (
            "What is a grabber tool?",
            "A grabber is a long tool with little jaws at the end. It helps a grown-up reach something without crawling under furniture.",
        )
    ],
    "flashlight": [
        (
            "Why does a flashlight help when something is lost?",
            "A flashlight shines into dark places so you can see exactly where the object is. Seeing first helps people solve the problem more safely.",
        )
    ],
    "ask_adult": [
        (
            "What should you do if something important gets stuck under furniture?",
            "Stop and ask a grown-up for help. Asking for help early keeps the problem small and keeps fingers safe.",
        )
    ],
    "metal": [
        (
            "What kinds of things can a magnet pull?",
            "A magnet can pull some metal things, like certain badges or keys. It does not pull soft toys or most plastic things.",
        )
    ],
    "plush": [
        (
            "What is a plush toy?",
            "A plush toy is a soft stuffed toy made for cuddling and pretend play. Because it is soft, people usually pick it up by holding it gently.",
        )
    ],
    "fragile": [
        (
            "What does fragile mean?",
            "Fragile means something can crack or break if it is squeezed or dropped. Fragile things need gentle hands and careful tools.",
        )
    ],
}

KNOWLEDGE_ORDER = [
    "ottoman",
    "heavy_furniture",
    "dark_space",
    "magnet",
    "grabber",
    "flashlight",
    "ask_adult",
    "metal",
    "plush",
    "fragile",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    theme = f["theme"]
    item = f["item_cfg"]
    spot = f["spot_cfg"]
    outcome = f["outcome"]
    a = f["instigator"]
    b = f["cautioner"]
    if outcome == "averted":
        return [
            f'Write a short space-adventure story for a 3-to-5-year-old where a mission item slips under {spot.the}, but an older child stops the unsafe shortcut before anyone moves it alone. Include the word "ottoman".',
            f"Tell a quest story where {a.id} wants to rush, {b.id} warns about heavy furniture, and a grown-up helps the crew finish the mission safely.",
            f'Write a gentle story about a pretend spaceship mission, a trapped {item.label}, and children learning that brave can mean careful.',
        ]
    return [
        f'Write a short space-adventure story for a 3-to-5-year-old where a mission item slips under {spot.the} and the children need safe help to get it back. Include the word "ottoman".',
        f"Tell a quest-and-conflict story where {a.id} tries an unsafe shortcut, the mission item slides deeper, and a grown-up solves the problem calmly.",
        f'Write a simple story about two children on a pretend spaceship who learn to pause and ask for help before moving heavy furniture.',
    ]


def relation_phrase(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    theme = f["theme"]
    item = f["item_cfg"]
    spot = f["spot_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    pair = relation_phrase(a, b, f["relation"])
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, pretending to be a spaceship crew. Their quest mattered because they needed {item.phrase} to {item.mission_use}.",
        ),
        (
            "What was the children's quest?",
            f"They wanted to finish {theme.goal} in their pretend spaceship game. They could not do that until they got {item.phrase} back.",
        ),
        (
            f"Where did the {item.label} go?",
            f"It slipped away and vanished under {spot.the}. That turned the pretend mission into a real little problem because the gap was hard to reach.",
        ),
        (
            f"Why did {b.id} tell {a.id} to stop?",
            f"{b.id} warned that {spot.the} was not safe to move alone. Heavy furniture can wobble or pinch fingers, so asking {pw} was the safer plan.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What did {a.id} do after the warning?",
                f"{a.id} backed down and agreed to ask for help instead of rushing. That choice kept the problem from getting bigger before {pw} came.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {a.id} tried to do it alone?",
                f"{spot.The} wobbled, and the children froze because it suddenly felt risky. The trapped item also slid farther back, which made the quest harder instead of easier.",
            )
        )
    qa.append(
        (
            f"How did {pw} solve the problem?",
            f"{pw.capitalize()} {response.qa_text}. That worked because the helper used the right tool and kept the heavy furniture under control.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"The crew got the mission item back and finished their pretend launch. The ending shows what changed: they were still brave, but now they knew to pause and ask for help first.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["spot_cfg"].tags) | set(f["response"].tags) | set(f["item_cfg"].tags)
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
        flags = [n for n, on in (
            ("heavy", e.heavy),
            ("dark", e.dark),
            ("metallic", e.metallic),
            ("soft", e.soft),
            ("fragile", e.fragile),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="star_patrol",
        item="star_key",
        spot="ottoman",
        response="magnet_wand",
        instigator="Nova",
        instigator_gender="girl",
        cautioner="Leo",
        cautioner_gender="boy",
        parent="mother",
        trait="careful",
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        theme="comet_run",
        item="plush_alien",
        spot="sofa",
        response="grabber",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Iris",
        cautioner_gender="girl",
        parent="father",
        trait="thoughtful",
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        theme="nebula_rescue",
        item="glow_cube",
        spot="bookshelf",
        response="lift_together",
        instigator="Luna",
        instigator_gender="girl",
        cautioner="Milo",
        cautioner_gender="boy",
        parent="mother",
        trait="steady",
        instigator_age=6,
        cautioner_age=8,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        theme="star_patrol",
        item="captain_badge",
        spot="ottoman",
        response="lift_together",
        instigator="Theo",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="father",
        trait="cautious",
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=3,
    ),
]


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of these safer choices: {better}.)"
    )


def explain_combo(item: LostItem, spot: Spot, response: Response) -> str:
    return (
        f"(No story: {response.id} is not a good way to get {item.phrase} from under "
        f"{spot.the}. The tool must be sensible, long enough, and suitable for the kind of item.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "rescued"


ASP_RULES = r"""
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

works(R, I, S) :- response_mode(R, magnet), item_metallic(I), reach(R, RR), depth(S, D), RR >= D.
works(R, I, S) :- response_mode(R, grab), not item_flat(I), reach(R, RR), depth(S, D), RR >= D, gentle_ok(R, I).
works(R, I, S) :- response_mode(R, lift), reach(R, RR), depth(S, D), RR >= D.

gentle_ok(R, I) :- not item_fragile(I).
gentle_ok(R, I) :- item_fragile(I), gentle(R).

valid(T, I, S, R) :- theme(T), item(I), spot(S), sensible(R), works(R, I, S).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

outcome(averted) :- averted.
outcome(rescued) :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.metallic:
            lines.append(asp.fact("item_metallic", iid))
        if item.fragile:
            lines.append(asp.fact("item_fragile", iid))
        if item.flat:
            lines.append(asp.fact("item_flat", iid))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        lines.append(asp.fact("depth", sid, spot.depth))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("reach", rid, response.reach))
        lines.append(asp.fact("response_mode", rid, response.mode))
        if response.gentle:
            lines.append(asp.fact("gentle", rid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pretend space quest, a trapped mission item, and a safer way to finish the adventure."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.item and args.spot and args.response:
        item = ITEMS[args.item]
        spot = SPOTS[args.spot]
        response = RESPONSES[args.response]
        if not response_works(response, item, spot):
            raise StoryError(explain_combo(item, spot, response))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.item is None or c[1] == args.item)
        and (args.spot is None or c[2] == args.spot)
        and (args.response is None or c[3] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, item, spot, response = rng.choice(sorted(combos))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7, 8], 2)
    trust = rng.randint(0, 10)

    return StoryParams(
        theme=theme,
        item=item,
        spot=spot,
        response=response,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        item = ITEMS[params.item]
        spot = SPOTS[params.spot]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter choice: {err.args[0]}.)") from None

    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not response_works(response, item, spot):
        raise StoryError(explain_combo(item, spot, response))

    world = tell(
        theme=theme,
        item=item,
        spot=spot,
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        parent_type=params.parent,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
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
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for s in range(100):
        try:
            case_args = build_parser().parse_args([])
            params = resolve_params(case_args, random.Random(s))
            cases.append(params)
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    # Smoke-test ordinary generation and rendering.
    smoke_cases = [
        CURATED[0],
        CURATED[-1],
        resolve_params(build_parser().parse_args([]), random.Random(777)),
    ]
    for i, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            _ = sample.to_dict()
            print(f"OK: smoke test {i} generated and serialized.")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"SMOKE TEST FAILED on case {i}: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, item, spot, response) combos:\n")
        for theme, item, spot, response in combos:
            print(f"  {theme:13} {item:14} {spot:10} {response}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.item} under {p.spot} ({p.theme}, {p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
