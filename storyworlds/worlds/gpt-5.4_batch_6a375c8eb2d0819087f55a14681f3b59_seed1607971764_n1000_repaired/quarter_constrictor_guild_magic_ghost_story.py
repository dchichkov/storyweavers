#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/quarter_constrictor_guild_magic_ghost_story.py
=========================================================================

A standalone storyworld for a gentle ghost story with magic: in one old town
quarter, a child hears a lonely guild ghost trapped by a magical constrictor
binding. A lost silver quarter must be found and returned before the ghost can
rest. The world model tracks the haunting, the search, the easing of the bind,
and the warm ending image that proves the place changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/quarter_constrictor_guild_magic_ghost_story.py
    python storyworlds/worlds/gpt-5.4/quarter_constrictor_guild_magic_ghost_story.py --place bell_quarter --ghost bellkeeper --bind ribbon
    python storyworlds/worlds/gpt-5.4/quarter_constrictor_guild_magic_ghost_story.py --place river_quarter --ghost tailor
    python storyworlds/worlds/gpt-5.4/quarter_constrictor_guild_magic_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/quarter_constrictor_guild_magic_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/quarter_constrictor_guild_magic_ghost_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/quarter_constrictor_guild_magic_ghost_story.py --json
    python storyworlds/worlds/gpt-5.4/quarter_constrictor_guild_magic_ghost_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt", "grandmother"}
        male = {"boy", "father", "man", "uncle", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
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
    path: str
    guild_hall: str
    air: str
    sound: str
    hiding_spot: str
    reveal_line: str
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
class GhostCfg:
    id: str
    label: str
    role_name: str
    guild_name: str
    opening_sound: str
    request: str
    thanks: str
    rest_image: str
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
class Bind:
    id: str
    label: str
    opener: str
    squeeze_text: str
    loosen_text: str
    release_aid: str
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
class Aid:
    id: str
    label: str
    phrase: str
    action_text: str
    magic_text: str
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


def _r_haunt(world: World) -> list[str]:
    ghost = world.get("ghost")
    bind = world.get("bind")
    room = world.get("hall")
    child = world.get("child")
    if ghost.meters["present"] < THRESHOLD or bind.meters["tight"] < THRESHOLD:
        return []
    sig = ("haunt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["cold"] += 1
    room.meters["echo"] += 1
    child.memes["fear"] += 1
    ghost.memes["lonely"] += 1
    return []


def _r_found_hope(world: World) -> list[str]:
    quarter = world.get("quarter")
    child = world.get("child")
    ghost = world.get("ghost")
    if quarter.meters["found"] < THRESHOLD:
        return []
    sig = ("found_hope",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["brave"] += 1
    ghost.memes["hope"] += 1
    return []


def _r_return_loosens(world: World) -> list[str]:
    quarter = world.get("quarter")
    bind = world.get("bind")
    ghost = world.get("ghost")
    if quarter.meters["returned"] < THRESHOLD:
        return []
    sig = ("return_loosens",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bind.meters["tight"] = 0.0
    bind.meters["loose"] += 1
    ghost.memes["hope"] += 1
    ghost.memes["lonely"] = 0.0
    return []


def _r_release(world: World) -> list[str]:
    bind = world.get("bind")
    aid = world.get("aid")
    ghost = world.get("ghost")
    room = world.get("hall")
    child = world.get("child")
    if bind.meters["loose"] < THRESHOLD or aid.meters["active"] < THRESHOLD:
        return []
    sig = ("release",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.meters["free"] += 1
    room.meters["cold"] = 0.0
    room.meters["echo"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["wonder"] += 1
    ghost.memes["peace"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="haunt", tag="ghost", apply=_r_haunt),
    Rule(name="found_hope", tag="emotion", apply=_r_found_hope),
    Rule(name="return_loosens", tag="magic", apply=_r_return_loosens),
    Rule(name="release", tag="magic", apply=_r_release),
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
            world.say(line)
    return produced


PLACES = {
    "bell_quarter": Place(
        id="bell_quarter",
        label="the Bell Quarter",
        path="a steep lane of stone steps",
        guild_hall="the old Bell Guild hall",
        air="The mist smelled like rain and cold iron.",
        sound="somewhere above them, a cracked bell gave one thin note",
        hiding_spot="a loose floor tile beneath the bell rope chest",
        reveal_line="A pale line of light crept under the loose tile and drew a circle there.",
        ending_image="The smallest bell over the door rang once, clear and gentle.",
        tags={"quarter", "bell", "guild"},
    ),
    "river_quarter": Place(
        id="river_quarter",
        label="the River Quarter",
        path="a narrow walk beside the black water",
        guild_hall="the Ferry Guild house",
        air="Fog lay low over the river and made every lamp look sleepy.",
        sound="the old dock chains gave a slow clink in the dark",
        hiding_spot="a locked fare box by the last ferry post",
        reveal_line="Blue sparks slipped across the fare box and showed the keyhole like a tiny star.",
        ending_image="The river smoothed itself flat, and one empty boat rocked as if someone had stepped ashore.",
        tags={"quarter", "river", "guild"},
    ),
    "market_quarter": Place(
        id="market_quarter",
        label="the Market Quarter",
        path="a crooked street of shuttered shops",
        guild_hall="the Cloth Guild room",
        air="The night smelled of dust, wool, and lavender soap.",
        sound="from behind a dark curtain came the softest rustle, like cloth in a draft",
        hiding_spot="the hem of a velvet guild banner",
        reveal_line="Moony marks fluttered over the old banner and stopped at one stitched hem.",
        ending_image="The hanging cloths settled, and a strip of silver thread shone in the window.",
        tags={"quarter", "market", "guild"},
    ),
}

GHOSTS = {
    "bellkeeper": GhostCfg(
        id="bellkeeper",
        label="the bellkeeper's ghost",
        role_name="bellkeeper",
        guild_name="Bell Guild",
        opening_sound="a tapping like a spoon against brass",
        request="My lucky quarter paid the first bell fee I ever kept. Without it, I cannot finish my last round.",
        thanks="The bells remember me now.",
        rest_image="The ghost touched an invisible cap, then thinned into pearly light near the bell frame.",
        places={"bell_quarter"},
        tags={"ghost", "bell", "guild"},
    ),
    "ferryman": GhostCfg(
        id="ferryman",
        label="the ferryman's ghost",
        role_name="ferryman",
        guild_name="Ferry Guild",
        opening_sound="a hollow knock as if an oar tapped old wood",
        request="My silver quarter was the ferry token I kept for storms. Without it, I cannot cross to my quiet shore.",
        thanks="The river knows my hands again.",
        rest_image="The ghost lifted one transparent lantern and faded like mist over water.",
        places={"river_quarter"},
        tags={"ghost", "river", "guild"},
    ),
    "tailor": GhostCfg(
        id="tailor",
        label="the tailor's ghost",
        role_name="tailor",
        guild_name="Cloth Guild",
        opening_sound="a neat click like invisible scissors",
        request="My silver quarter sat in my measuring box for luck. Without it, every thread catches and I cannot rest.",
        thanks="The cloth lies smooth at last.",
        rest_image="The ghost bowed once, and the moonlight folded around the empty sewing chair.",
        places={"market_quarter"},
        tags={"ghost", "cloth", "guild"},
    ),
}

BINDS = {
    "ribbon": Bind(
        id="ribbon",
        label="a ribbon constrictor",
        opener="moon_chalk",
        squeeze_text="A long silver ribbon moved as if it were alive, winding tighter whenever the ghost tried to speak.",
        loosen_text="The ribbon constrictor slackened and slipped to the floor like ordinary silk.",
        release_aid="moon_chalk",
        tags={"constrictor", "magic", "ribbon"},
    ),
    "ivy": Bind(
        id="ivy",
        label="an ivy constrictor",
        opener="brass_key",
        squeeze_text="Dark ivy with glassy leaves crawled over the ghost's middle and squeezed with a slow green creak.",
        loosen_text="The ivy constrictor untwined leaf by leaf and crumbled into cool dew.",
        release_aid="brass_key",
        tags={"constrictor", "magic", "ivy"},
    ),
    "smoke": Bind(
        id="smoke",
        label="a smoke constrictor",
        opener="blue_lantern",
        squeeze_text="A rope of blue smoke coiled around the ghost like a constrictor snake made of fog.",
        loosen_text="The smoke constrictor came apart in rings and vanished into the lantern glow.",
        release_aid="blue_lantern",
        tags={"constrictor", "magic", "smoke"},
    ),
}

AIDS = {
    "moon_chalk": Aid(
        id="moon_chalk",
        label="moon chalk",
        phrase="a stub of moon chalk",
        action_text="drew a small circle of pale magic on the boards",
        magic_text="The chalk gave off a clean white shine, and hidden things answered it.",
        tags={"magic", "chalk"},
    ),
    "brass_key": Aid(
        id="brass_key",
        label="brass guild key",
        phrase="a brass guild key",
        action_text="turned the old brass key with both hands",
        magic_text="The key warmed at once, as if it remembered every lock in the guild.",
        tags={"magic", "key"},
    ),
    "blue_lantern": Aid(
        id="blue_lantern",
        label="blue lantern",
        phrase="a blue lantern",
        action_text="lifted the blue lantern high",
        magic_text="Blue firelight spread softly and showed what the dark had been hiding.",
        tags={"magic", "lantern"},
    ),
}

CHILD_NAMES = ["Mira", "Nell", "Tomas", "Ivy", "Bram", "Lina", "Owen", "Suri", "June", "Eli"]
CHILD_TYPES = {
    "Mira": "girl",
    "Nell": "girl",
    "Tomas": "boy",
    "Ivy": "girl",
    "Bram": "boy",
    "Lina": "girl",
    "Owen": "boy",
    "Suri": "girl",
    "June": "girl",
    "Eli": "boy",
}
CAREGIVERS = ["grandmother", "grandfather", "mother", "father"]
TRAITS = ["careful", "quiet", "curious", "gentle", "steady", "brave"]


def aid_for_bind(bind_id: str) -> str:
    if bind_id not in BINDS:
        raise StoryError(f"(Unknown bind: {bind_id})")
    return BINDS[bind_id].release_aid


def ghost_belongs(place_id: str, ghost_id: str) -> bool:
    return place_id in GHOSTS[ghost_id].places


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for ghost_id, ghost in GHOSTS.items():
            if not ghost_belongs(place_id, ghost_id):
                continue
            for bind_id in BINDS:
                combos.append((place_id, ghost_id, bind_id))
    return combos


def explain_place_ghost(place_id: str, ghost_id: str) -> str:
    place = PLACES[place_id]
    ghost = GHOSTS[ghost_id]
    allowed = ", ".join(sorted(ghost.places))
    return (
        f"(No story: {ghost.label} does not belong in {place.label}. "
        f"This ghost is tied to {ghost.guild_name} and only makes sense in: {allowed}.)"
    )


def explain_aid(bind_id: str, aid_id: str) -> str:
    bind = BINDS[bind_id]
    wanted = aid_for_bind(bind_id)
    return (
        f"(No story: {AIDS[aid_id].label} will not open {bind.label}. "
        f"This binding yields only to {AIDS[wanted].label}.)"
    )


def predict_release(world: World) -> dict:
    sim = world.copy()
    sim.get("quarter").meters["found"] += 1
    sim.get("quarter").meters["returned"] += 1
    sim.get("aid").meters["active"] += 1
    propagate(sim, narrate=False)
    return {
        "freed": sim.get("ghost").meters["free"] >= THRESHOLD,
        "cold": sim.get("hall").meters["cold"],
    }


def introduce(world: World, child: Entity, carer: Entity, place: Place) -> None:
    world.say(
        f"One misty evening, {child.id} walked with {child.pronoun('possessive')} "
        f"{carer.label_word} through {place.label}. They took {place.path} because "
        f"{carer.label_word} said the old stones there remembered stories."
    )
    world.say(place.air)
    world.say(
        f"At the end of the lane stood {place.guild_hall}, dark except for one pale window."
    )


def hear_haunting(world: World, child: Entity, place: Place, ghost: GhostCfg) -> None:
    world.say(
        f"As they passed, {place.sound}, and under it came {ghost.opening_sound}. "
        f"{child.id} stopped so fast that even the mist seemed to stop too."
    )
    world.say(
        f'"Did you hear that?" {child.id} whispered. The door of {place.guild_hall} '
        f"eased inward with a long sleepy creak."
    )


def appear(world: World, child: Entity, carer: Entity, ghost_cfg: GhostCfg, bind_cfg: Bind) -> None:
    ghost = world.get("ghost")
    bind = world.get("bind")
    ghost.meters["present"] += 1
    bind.meters["tight"] += 1
    propagate(world, narrate=False)
    fear_note = " The air turned so cold that their breath puffed white."
    if child.memes["fear"] < THRESHOLD:
        fear_note = ""
    world.say(
        f"Inside, a dim shape rose beside a worktable: {ghost_cfg.label}. "
        f"{bind_cfg.squeeze_text}{fear_note}"
    )
    world.say(
        f'{carer.label_word.capitalize()} squeezed {child.id}\'s hand, but did not pull away. '
        f'"A lonely ghost," {carer.pronoun()} said softly. "Let us listen before we run."'
    )


def plea(world: World, ghost_cfg: GhostCfg, bind_cfg: Bind) -> None:
    world.say(
        f'The ghost tried to lift one hand, but {bind_cfg.label} pulled tight. '
        f'"Please," it sighed. "{ghost_cfg.request}"'
    )


def choose_aid(world: World, child: Entity, carer: Entity, aid_cfg: Aid, bind_cfg: Bind) -> None:
    pred = predict_release(world)
    world.facts["predicted_freed"] = pred["freed"]
    world.say(
        f'{carer.label_word.capitalize()} opened a little guild cupboard by the wall and found '
        f"{aid_cfg.phrase}. \"Old halls keep old helps,\" {carer.pronoun()} murmured."
    )
    world.say(
        f"{child.id} {aid_cfg.action_text}. {aid_cfg.magic_text}"
    )


def find_quarter(world: World, child: Entity, place: Place, quarter: Entity, aid: Entity) -> None:
    quarter.meters["found"] += 1
    aid.meters["active"] += 1
    propagate(world, narrate=False)
    world.say(place.reveal_line)
    world.say(
        f"There, hidden in {place.hiding_spot}, lay the silver quarter. "
        f"{child.id} picked it up, and it felt cold for only a breath before growing warm."
    )


def return_quarter(world: World, child: Entity, ghost_cfg: GhostCfg, bind_cfg: Bind) -> None:
    quarter = world.get("quarter")
    quarter.meters["returned"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{child.id} stepped close enough to see starlight through the ghost and set the quarter '
        f"into the ghost's waiting palm."
    )
    world.say(bind_cfg.loosen_text)
    world.say(
        f'The ghost drew in a long, amazed breath. "{ghost_cfg.thanks}"'
    )


def farewell(world: World, child: Entity, place: Place, ghost_cfg: GhostCfg) -> None:
    ghost = world.get("ghost")
    if ghost.meters["free"] < THRESHOLD:
        raise StoryError("(Story bug: the ghost was not freed before the ending.)")
    world.say(ghost_cfg.rest_image)
    world.say(
        f"{place.ending_image} The room no longer felt hungry or cold."
    )
    world.say(
        f"When {child.id} and {child.pronoun('possessive')} family member stepped back into the lane, "
        f"{place.label} felt like an ordinary quarter again, only kinder."
    )


def tell(
    place: Place,
    ghost_cfg: GhostCfg,
    bind_cfg: Bind,
    aid_cfg: Aid,
    child_name: str,
    child_type: str,
    caregiver_type: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_type,
            label=child_name,
            role="child",
            traits=[trait],
        )
    )
    carer = world.add(
        Entity(
            id="Carer",
            kind="character",
            type=caregiver_type,
            label="the caregiver",
            role="caregiver",
            traits=["calm"],
        )
    )
    hall = world.add(
        Entity(
            id="hall",
            type="hall",
            label=place.guild_hall,
        )
    )
    ghost = world.add(
        Entity(
            id="ghost",
            type="ghost",
            label=ghost_cfg.label,
            role="ghost",
            attrs={"guild_name": ghost_cfg.guild_name, "role_name": ghost_cfg.role_name},
        )
    )
    bind = world.add(
        Entity(
            id="bind",
            type="binding",
            label=bind_cfg.label,
            role="bind",
            attrs={"bind_id": bind_cfg.id},
        )
    )
    quarter = world.add(
        Entity(
            id="quarter",
            type="coin",
            label="silver quarter",
            role="keepsake",
        )
    )
    aid = world.add(
        Entity(
            id="aid",
            type="magic_tool",
            label=aid_cfg.label,
            role="aid",
            attrs={"aid_id": aid_cfg.id},
        )
    )

    child.memes["curiosity"] = 1.0
    child.memes["kindness"] = 1.0
    hall.meters["cold"] = 0.0
    hall.meters["echo"] = 0.0
    ghost.meters["present"] = 0.0
    ghost.meters["free"] = 0.0
    bind.meters["tight"] = 0.0
    bind.meters["loose"] = 0.0
    quarter.meters["found"] = 0.0
    quarter.meters["returned"] = 0.0
    aid.meters["active"] = 0.0

    world.facts.update(
        place=place,
        ghost_cfg=ghost_cfg,
        bind_cfg=bind_cfg,
        aid_cfg=aid_cfg,
        child=child,
        caregiver=carer,
    )

    introduce(world, child, carer, place)
    world.para()
    hear_haunting(world, child, place, ghost_cfg)
    appear(world, child, carer, ghost_cfg, bind_cfg)
    plea(world, ghost_cfg, bind_cfg)
    world.para()
    choose_aid(world, child, carer, aid_cfg, bind_cfg)
    find_quarter(world, child, place, quarter, aid)
    return_quarter(world, child, ghost_cfg, bind_cfg)
    world.para()
    farewell(world, child, place, ghost_cfg)

    world.facts.update(
        hall=hall,
        ghost=ghost,
        bind=bind,
        quarter=quarter,
        aid=aid,
        freed=ghost.meters["free"] >= THRESHOLD,
        quarter_found=quarter.meters["found"] >= THRESHOLD,
        quarter_returned=quarter.meters["returned"] >= THRESHOLD,
        hall_warm=hall.meters["cold"] < THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost in a story?",
            "A ghost in a story is the spirit of someone who has died. In gentle stories, a ghost is often lonely or unfinished rather than mean."
        )
    ],
    "guild": [
        (
            "What is a guild?",
            "A guild is a group of workers who share the same craft, like bellkeepers, ferrymen, or tailors. Long ago, guilds often kept tools, records, and meeting halls together."
        )
    ],
    "quarter": [
        (
            "What can the word quarter mean?",
            "Quarter can mean one part out of four, and it can also mean a part of a town. In this story, it is both a silver coin and a neighborhood."
        )
    ],
    "constrictor": [
        (
            "What does constrictor mean?",
            "Constrictor means something that coils around and squeezes tight. The word is often used for a snake, but in a magic story it can describe a binding too."
        )
    ],
    "magic": [
        (
            "Why do magic tools glow in stories?",
            "A glowing magic tool shows that hidden things are being revealed or changed. The light helps readers feel the turn from danger toward help."
        )
    ],
    "bell": [
        (
            "Why do bells sound spooky at night?",
            "Bells carry far in cold air, so even one small note can feel lonely at night. That is why ghost stories often use bells to make a place feel old and waiting."
        )
    ],
    "river": [
        (
            "Why does fog make a river look mysterious?",
            "Fog hides the far side of the water and softens shapes. That makes the river seem deeper and quieter than it does in daylight."
        )
    ],
    "cloth": [
        (
            "Why can old cloth sound ghostly?",
            "Old cloth can rustle and sway even in a tiny draft. In a dark room, that soft sound can seem like someone moving when no one is there."
        )
    ],
    "chalk": [
        (
            "What is chalk used for?",
            "Chalk can make marks on stone or wood that are easy to see. In magic stories, it is often used to draw circles, signs, or guiding lines."
        )
    ],
    "key": [
        (
            "Why is a key a good magic object in stories?",
            "A key already opens closed things, so it also feels right as a magic tool. Story magic often grows out of what an ordinary object already does."
        )
    ],
    "lantern": [
        (
            "Why is a lantern good in a ghost story?",
            "A lantern makes a small safe circle of light in a big dark place. That makes it perfect for scenes where someone must be brave and kind."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "ghost",
    "guild",
    "quarter",
    "constrictor",
    "magic",
    "bell",
    "river",
    "cloth",
    "chalk",
    "key",
    "lantern",
]


@dataclass
class StoryParams:
    place: str
    ghost: str
    bind: str
    aid: str
    child_name: str
    child_type: str
    caregiver_type: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    ghost_cfg = f["ghost_cfg"]
    bind_cfg = f["bind_cfg"]
    aid_cfg = f["aid_cfg"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "quarter", "constrictor", and "guild".',
        f"Tell a magic ghost story where {child.id} enters {place.guild_hall}, meets {ghost_cfg.label}, and uses {aid_cfg.label} to return a lost silver quarter.",
        f"Write a child-facing ghost tale set in {place.label} where {bind_cfg.label} traps a lonely guild spirit until one brave child helps it rest.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    carer = f["caregiver"]
    place = f["place"]
    ghost_cfg = f["ghost_cfg"]
    bind_cfg = f["bind_cfg"]
    aid_cfg = f["aid_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {carer.label_word}, and {ghost_cfg.label} in {place.label}. The story begins with a walk through an old quarter and turns into a rescue."
        ),
        (
            f"What made the place feel spooky at first?",
            f"{place.sound.capitalize()}, and the ghost appeared inside the dark guild hall. The hall also turned cold because the magical binding was still tight around the ghost."
        ),
        (
            "Why was the ghost unhappy?",
            f"The ghost was unhappy because {bind_cfg.label} was squeezing it and its lucky silver quarter was lost. Without the quarter, the ghost could not finish its last small duty and rest."
        ),
        (
            f"How did {child.id} help the ghost?",
            f"{child.id} used {aid_cfg.label} to reveal the hidden quarter in {place.hiding_spot}. Then {child.pronoun()} returned the coin to the ghost, which loosened the binding and freed it."
        ),
        (
            "How did the story end?",
            f"The hall stopped feeling cold, and the ghost faded away peacefully. The ending image shows that the quarter had changed from a hungry, haunted place back into a calm old street."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"ghost", "guild", "quarter", "constrictor", "magic"}
    place = f["place"]
    ghost_cfg = f["ghost_cfg"]
    aid_cfg = f["aid_cfg"]
    bind_cfg = f["bind_cfg"]
    tags |= set(place.tags) | set(ghost_cfg.tags) | set(aid_cfg.tags) | set(bind_cfg.tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="bell_quarter",
        ghost="bellkeeper",
        bind="ribbon",
        aid="moon_chalk",
        child_name="Mira",
        child_type="girl",
        caregiver_type="grandmother",
        trait="curious",
    ),
    StoryParams(
        place="river_quarter",
        ghost="ferryman",
        bind="ivy",
        aid="brass_key",
        child_name="Owen",
        child_type="boy",
        caregiver_type="grandfather",
        trait="steady",
    ),
    StoryParams(
        place="market_quarter",
        ghost="tailor",
        bind="smoke",
        aid="blue_lantern",
        child_name="June",
        child_type="girl",
        caregiver_type="mother",
        trait="gentle",
    ),
    StoryParams(
        place="bell_quarter",
        ghost="bellkeeper",
        bind="smoke",
        aid="blue_lantern",
        child_name="Eli",
        child_type="boy",
        caregiver_type="father",
        trait="brave",
    ),
    StoryParams(
        place="market_quarter",
        ghost="tailor",
        bind="ribbon",
        aid="moon_chalk",
        child_name="Lina",
        child_type="girl",
        caregiver_type="grandmother",
        trait="quiet",
    ),
]


ASP_RULES = r"""
haunt_ok(P,G) :- ghost_belongs(G,P).
aid_for_bind(B,A) :- bind(B), opener(B,A).
valid(P,G,B,A) :- place(P), ghost(G), bind(B), aid(A),
                  haunt_ok(P,G), aid_for_bind(B,A).

#show valid/4.
#show haunt_ok/2.
#show aid_for_bind/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for ghost_id, ghost in GHOSTS.items():
        lines.append(asp.fact("ghost", ghost_id))
        for place_id in sorted(ghost.places):
            lines.append(asp.fact("ghost_belongs", ghost_id, place_id))
    for bind_id, bind in BINDS.items():
        lines.append(asp.fact("bind", bind_id))
        lines.append(asp.fact("opener", bind_id, bind.release_aid))
    for aid_id in AIDS:
        lines.append(asp.fact("aid", aid_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_aid_pairs() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "aid_for_bind")))


def asp_verify() -> int:
    rc = 0
    python_valid = set((p, g, b, aid_for_bind(b)) for (p, g, b) in valid_combos())
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: ASP valid combos match Python ({len(python_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    python_pairs = set((bind_id, aid_for_bind(bind_id)) for bind_id in BINDS)
    clingo_pairs = set(asp_aid_pairs())
    if python_pairs == clingo_pairs:
        print(f"OK: ASP aid mapping matches Python ({sorted(python_pairs)}).")
    else:
        rc = 1
        print("MISMATCH in aid mapping:")
        if clingo_pairs - python_pairs:
            print("  only in clingo:", sorted(clingo_pairs - python_pairs))
        if python_pairs - clingo_pairs:
            print("  only in python:", sorted(python_pairs - clingo_pairs))

    smoke_cases = [
        CURATED[0],
        StoryParams(
            place="river_quarter",
            ghost="ferryman",
            bind="smoke",
            aid="blue_lantern",
            child_name="Mira",
            child_type="girl",
            caregiver_type="grandfather",
            trait="careful",
        ),
    ]
    for params in smoke_cases:
        try:
            sample = generate(params)
        except Exception as err:  # pragma: no cover - verify path
            print(f"SMOKE TEST FAILED for {params}: {err}")
            return 1
        if not sample.story.strip():
            print("SMOKE TEST FAILED: empty story.")
            return 1
        if sample.world is None or not sample.world.facts.get("freed"):
            print("SMOKE TEST FAILED: generated world did not free the ghost.")
            return 1
    print("OK: smoke-tested ordinary generation on 2 scenarios.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child helps a guild ghost in an old quarter using magic."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--bind", choices=BINDS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--caregiver-type", choices=CAREGIVERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.ghost and not ghost_belongs(args.place, args.ghost):
        raise StoryError(explain_place_ghost(args.place, args.ghost))
    if args.bind and args.aid and aid_for_bind(args.bind) != args.aid:
        raise StoryError(explain_aid(args.bind, args.aid))
    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.ghost is None or combo[1] == args.ghost)
        and (args.bind is None or combo[2] == args.bind)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place_id, ghost_id, bind_id = rng.choice(sorted(combos))
    aid_id = aid_for_bind(bind_id)
    if args.aid and args.aid != aid_id:
        raise StoryError(explain_aid(bind_id, args.aid))
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    child_type = args.child_type or CHILD_TYPES[child_name]
    caregiver_type = args.caregiver_type or rng.choice(CAREGIVERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        ghost=ghost_id,
        bind=bind_id,
        aid=aid_id,
        child_name=child_name,
        child_type=child_type,
        caregiver_type=caregiver_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.ghost not in GHOSTS:
        raise StoryError(f"(Unknown ghost: {params.ghost})")
    if params.bind not in BINDS:
        raise StoryError(f"(Unknown bind: {params.bind})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if not ghost_belongs(params.place, params.ghost):
        raise StoryError(explain_place_ghost(params.place, params.ghost))
    if aid_for_bind(params.bind) != params.aid:
        raise StoryError(explain_aid(params.bind, params.aid))

    world = tell(
        place=PLACES[params.place],
        ghost_cfg=GHOSTS[params.ghost],
        bind_cfg=BINDS[params.bind],
        aid_cfg=AIDS[params.aid],
        child_name=params.child_name,
        child_type=params.child_type,
        caregiver_type=params.caregiver_type,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, ghost, bind, aid) combos:\n")
        for place_id, ghost_id, bind_id, aid_id in combos:
            print(f"  {place_id:14} {ghost_id:10} {bind_id:7} {aid_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.child_name}: {p.ghost} in {p.place} ({p.bind}, {p.aid})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
