#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/badminton_promise_moral_value_ghost_story.py
=======================================================================

A standalone story world about a child, a game of badminton, and a promise that
matters once evening turns a familiar place into a ghost story.

The tiny domain:
- A child plays badminton near dusk.
- The child has made a promise to a caring elder.
- The shuttlecock lands in a haunted-looking spot.
- If the promise is pushed aside, a gentle ghostly guardian appears.
- The child must choose honesty and responsibility, then keep or repair the promise.

The moral value is explicit in the state model: promises create obligations,
breaking them raises worry and guilt, and truthful repair restores calm.
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
    portable: bool = False
    hidden: bool = False
    eerie: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
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
    opening: str
    evening: str
    path_home: str
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
class PromiseKind:
    id: str
    line: str
    reminder: str
    repair: str
    duty: str
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
class HauntedSpot:
    id: str
    label: str
    phrase: str
    whisper: str
    hides_items: bool = True
    eerie: bool = True
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
class Spirit:
    id: str
    label: str
    opening: str
    lesson: str
    gift_line: str
    gentle: bool = True
    guardian: bool = True
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


def _r_broken_promise_stirs_fear(world: World) -> list[str]:
    child = world.get("child")
    elder = world.get("elder")
    if child.meters["promise_broken"] < THRESHOLD:
        return []
    sig = ("broken_promise", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["guilt"] += 1
    child.memes["fear"] += 1
    elder.memes["worry"] += 1
    world.get("evening").meters["hush"] += 1
    return ["__broken__"]


def _r_lost_in_eerie_place_summons_spirit(world: World) -> list[str]:
    shuttle = world.get("shuttle")
    spot = world.get("spot")
    child = world.get("child")
    spirit = world.get("spirit")
    if shuttle.meters["lost"] < THRESHOLD or not spot.eerie:
        return []
    if child.meters["promise_broken"] < THRESHOLD:
        return []
    sig = ("spirit_appears", spot.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    spirit.meters["present"] += 1
    child.memes["fear"] += 1
    return ["__spirit__"]


def _r_truth_brings_relief(world: World) -> list[str]:
    child = world.get("child")
    elder = world.get("elder")
    spirit = world.get("spirit")
    if child.meters["truth_told"] < THRESHOLD:
        return []
    sig = ("truth_relief", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["courage"] += 1
    child.memes["fear"] = 0.0
    child.memes["guilt"] = 0.0
    elder.memes["worry"] = 0.0
    spirit.memes["peace"] += 1
    return ["__truth__"]


CAUSAL_RULES = [
    Rule(name="broken_promise_stirs_fear", tag="moral", apply=_r_broken_promise_stirs_fear),
    Rule(name="lost_in_eerie_place_summons_spirit", tag="ghost", apply=_r_lost_in_eerie_place_summons_spirit),
    Rule(name="truth_brings_relief", tag="moral", apply=_r_truth_brings_relief),
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


def promise_relevant(promise: PromiseKind, place: Place) -> bool:
    return True


def valid_pair(spot: HauntedSpot, spirit: Spirit) -> bool:
    return spot.hides_items and spot.eerie and spirit.gentle and spirit.guardian


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for promise_id, promise in PROMISES.items():
            if not promise_relevant(promise, place):
                continue
            for spot_id, spot in SPOTS.items():
                for spirit_id, spirit in SPIRITS.items():
                    if valid_pair(spot, spirit):
                        combos.append((place_id, promise_id, spot_id, spirit_id))
    return combos


def predict_ghost(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["promise_broken"] += 1
    sim.get("shuttle").meters["lost"] += 1
    propagate(sim, narrate=False)
    return {
        "spirit": sim.get("spirit").meters["present"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"],
        "worry": sim.get("elder").memes["worry"],
    }


def opening_scene(world: World, child: Entity, elder: Entity, place: Place, promise: PromiseKind) -> None:
    child.memes["joy"] += 1
    world.say(
        f"That evening, {child.id} took a badminton racket to {place.label}. {place.opening}"
    )
    world.say(
        f'Before {child.pronoun()} skipped out the gate, {child.pronoun("possessive")} '
        f'{elder.label_word} said, "{promise.line}"'
    )
    world.say(
        f'"I promise," {child.id} said, and meant it.'
    )


def play_badminton(world: World, child: Entity, friend: Entity) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    shuttle = world.get("shuttle")
    shuttle.meters["in_play"] += 1
    world.say(
        f"Soon {child.id} and {friend.id} were laughing and batting the shuttlecock back and forth. "
        f"Each light tap of the badminton game sounded neat and bright in the warm air."
    )


def dusk_turns(world: World, child: Entity, elder: Entity, place: Place, promise: PromiseKind) -> None:
    world.say(place.evening)
    pred = predict_ghost(world)
    world.facts["predicted_fear"] = pred["fear"]
    world.facts["predicted_worry"] = pred["worry"]
    child.memes["doubt"] += 1
    world.say(
        f'{child.id} remembered the promise then. {promise.reminder} '
        f'But one more game felt easy to excuse.'
    )
    elder.memes["care"] += 1


def lose_shuttle(world: World, child: Entity, spot: HauntedSpot) -> None:
    shuttle = world.get("shuttle")
    shuttle.meters["lost"] += 1
    shuttle.hidden = True
    world.say(
        f"On the last swing, the shuttlecock flew crooked and vanished into {spot.phrase}. "
        f"For a moment, even the crickets seemed to stop and listen."
    )


def break_promise(world: World, child: Entity) -> None:
    child.meters["promise_broken"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} took a step toward the shadows anyway. The little promise {child.pronoun()} had made now felt heavy in {child.pronoun('possessive')} chest."
    )


def spirit_arrives(world: World, spirit_cfg: Spirit, spot: HauntedSpot) -> None:
    spirit = world.get("spirit")
    propagate(world, narrate=False)
    if spirit.meters["present"] < THRESHOLD:
        raise StoryError("The ghost story requires the spirit to appear, but the world state did not summon it.")
    world.say(
        f"From {spot.label} came a silver shimmer, and out of it drifted {spirit_cfg.opening}. "
        f"{spot.whisper}"
    )


def spirit_speaks(world: World, child: Entity, spirit_cfg: Spirit, promise: PromiseKind) -> None:
    child.memes["awe"] += 1
    world.say(
        f'"Little player," the spirit said, not unkindly, "{spirit_cfg.lesson} '
        f'A promise should not be treated like a feather in the wind."'
    )
    world.say(
        f"{child.id} swallowed hard and thought of home, of waiting footsteps, and of the words {child.pronoun()} had given away so easily."
    )


def confess(world: World, child: Entity, elder: Entity, promise: PromiseKind) -> None:
    child.meters["truth_told"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I did make a promise," {child.id} whispered. "I wanted one more turn, and I chose badly."'
    )
    world.say(
        f'The spirit nodded. "{promise.repair}"'
    )
    elder.memes["hope"] += 1


def return_shuttle(world: World, child: Entity, spirit_cfg: Spirit, spot: HauntedSpot) -> None:
    shuttle = world.get("shuttle")
    shuttle.meters["lost"] = 0.0
    shuttle.hidden = False
    shuttle.meters["found"] += 1
    world.say(
        f"The spirit lifted one pale hand. The shuttlecock rose from {spot.phrase} as if a soft wind carried it, and settled into {child.id}'s palm."
    )
    world.say(
        spirit_cfg.gift_line
    )


def go_home_and_repair(world: World, child: Entity, elder: Entity, place: Place, promise: PromiseKind) -> None:
    child.meters["promise_kept_in_the_end"] += 1
    child.memes["responsibility"] += 1
    elder.memes["relief"] += 1
    world.say(
        f"{child.id} ran {place.path_home} with the racket tucked under one arm and the shuttlecock safe in the other hand."
    )
    world.say(
        f"{elder.label_word.capitalize()} was waiting by the door lamp. Before any question came, {child.id} told the truth and said sorry for the broken promise."
    )
    world.say(
        f'{elder.label_word.capitalize()} hugged {child.pronoun("object")} close. "Thank you for telling the truth," {elder.pronoun()} said. "{promise.duty}"'
    )


def ending_image(world: World, child: Entity, friend: Entity) -> None:
    child.memes["joy"] += 1
    child.memes["peace"] += 1
    world.say(
        f"The next afternoon, {child.id} came back early, finished the game of badminton before dusk, and went home when {child.pronoun("possessive")} time was up."
    )
    world.say(
        f"When the shuttlecock floated over the net, {child.id} never forgot how light it looked and how heavy a promise could be. From then on, {child.pronoun()} tried to keep both hands and words steady."
    )


def tell(
    place: Place,
    promise: PromiseKind,
    spot: HauntedSpot,
    spirit_cfg: Spirit,
    *,
    child_name: str = "Mina",
    child_gender: str = "girl",
    friend_name: str = "Arun",
    friend_gender: str = "boy",
    elder_type: str = "grandmother",
) -> World:
    world = World()

    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, role="elder", label="the elder"))
    world.add(Entity(id="shuttle", type="shuttlecock", label="shuttlecock", portable=True))
    world.add(Entity(id="racket", type="racket", label="badminton racket", portable=True))
    world.add(Entity(id="spot", type="place", label=spot.label, eerie=spot.eerie, hidden=False))
    world.add(Entity(id="spirit", kind="character", type="ghost", role="spirit", label=spirit_cfg.label))
    world.add(Entity(id="evening", type="time", label="evening"))

    world.facts.update(
        place=place,
        promise_cfg=promise,
        spot_cfg=spot,
        spirit_cfg=spirit_cfg,
        child=child,
        friend=friend,
        elder=elder,
    )

    opening_scene(world, child, elder, place, promise)
    play_badminton(world, child, friend)

    world.para()
    dusk_turns(world, child, elder, place, promise)
    lose_shuttle(world, child, spot)
    break_promise(world, child)

    world.para()
    spirit_arrives(world, spirit_cfg, spot)
    spirit_speaks(world, child, spirit_cfg, promise)
    confess(world, child, elder, promise)
    return_shuttle(world, child, spirit_cfg, spot)

    world.para()
    go_home_and_repair(world, child, elder, place, promise)
    ending_image(world, child, friend)

    world.facts.update(
        promise_broken=child.meters["promise_broken"] >= THRESHOLD,
        spirit_seen=world.get("spirit").meters["present"] >= THRESHOLD,
        truth_told=child.meters["truth_told"] >= THRESHOLD,
        shuttle_found=world.get("shuttle").meters["found"] >= THRESHOLD,
        repaired=child.meters["promise_kept_in_the_end"] >= THRESHOLD,
    )
    return world


PLACES = {
    "lane": Place(
        id="lane",
        label="the narrow lane behind the houses",
        opening="A faded chalk line still marked where children liked to play.",
        evening="The sky dimmed from gold to smoky purple, and the lane began to look older than it had a moment before.",
        path_home="down the lane and past the hibiscus fence",
        tags={"dusk", "home"},
    ),
    "schoolyard": Place(
        id="schoolyard",
        label="the old schoolyard",
        opening="The cracked court lines made a crooked little badminton square on the ground.",
        evening="As the light thinned, the empty windows of the old classroom watched the yard in silence.",
        path_home="through the side gate and along the quiet road",
        tags={"dusk", "school"},
    ),
    "courtyard": Place(
        id="courtyard",
        label="the temple courtyard",
        opening="Stone flags held the last warmth of the day, and the air smelled faintly of jasmine.",
        evening="When the bells stopped ringing, the courtyard corners filled with long, listening shadows.",
        path_home="across the courtyard and under the lantern arch",
        tags={"dusk", "lantern"},
    ),
}

PROMISES = {
    "before_dark": PromiseKind(
        id="before_dark",
        line="Come home before it gets dark.",
        reminder="The first shadows had already reached the net.",
        repair="Then go home with honest feet, not hiding feet.",
        duty="A promise is small when we speak it and big when we carry it.",
        tags={"promise", "obedience"},
    ),
    "return_racket": PromiseKind(
        id="return_racket",
        line="Bring the racket back before the lamp is lit.",
        reminder="The lamp in the front room would be glowing soon.",
        repair="Return what was trusted to you, and let your truth arrive first.",
        duty="When someone trusts you with something, your promise must travel with it.",
        tags={"promise", "trust"},
    ),
    "three_hits": PromiseKind(
        id="three_hits",
        line="Only three more hits, and then come straight home.",
        reminder="They had already played far more than three careful hits.",
        repair="Count your heart more carefully than your game.",
        duty="A good child does not stretch a promise until it snaps.",
        tags={"promise", "self_control"},
    ),
}

SPOTS = {
    "banyan_roots": HauntedSpot(
        id="banyan_roots",
        label="the banyan roots",
        phrase="the twisted banyan roots by the wall",
        whisper="The hanging roots trembled though there was almost no wind.",
        hides_items=True,
        eerie=True,
        tags={"tree", "ghost"},
    ),
    "well_edge": HauntedSpot(
        id="well_edge",
        label="the old well",
        phrase="the mossy stones around the old well",
        whisper="A cool breath seemed to rise from the dark circle below.",
        hides_items=True,
        eerie=True,
        tags={"well", "ghost"},
    ),
    "shrine_steps": HauntedSpot(
        id="shrine_steps",
        label="the shrine steps",
        phrase="the shadowy shrine steps",
        whisper="The little brass bells gave one tiny sound all by themselves.",
        hides_items=True,
        eerie=True,
        tags={"shrine", "ghost"},
    ),
    "open_bench": HauntedSpot(
        id="open_bench",
        label="the open bench",
        phrase="the plain wooden bench",
        whisper="Nothing there looked especially strange at all.",
        hides_items=False,
        eerie=False,
        tags={"plain"},
    ),
}

SPIRITS = {
    "caretaker": Spirit(
        id="caretaker",
        label="the caretaker spirit",
        opening="the pale shape of an old court keeper in a coat that shimmered like moonlit dust",
        lesson="Games are joyful, but true hearts go home when they said they would",
        gift_line="Its smile was sad and kind, as if it had once waited for someone else's late footsteps long ago.",
        gentle=True,
        guardian=True,
        tags={"ghost", "kindness"},
    ),
    "feather_girl": Spirit(
        id="feather_girl",
        label="the shuttle ghost",
        opening="a girl made of misty light, with a white feather tucked behind one ear",
        lesson="A shuttlecock may drift, but your word should not",
        gift_line="For a blink, she looked almost like any child who had once loved this court and never forgotten it.",
        gentle=True,
        guardian=True,
        tags={"ghost", "memory"},
    ),
    "lantern_grandpa": Spirit(
        id="lantern_grandpa",
        label="the lantern grandpa",
        opening="a bent old man carrying a dim lantern that glowed without any flame",
        lesson="The night listens closely when children forget their promises",
        gift_line="His lantern dimmed and brightened softly, as if approving the brave choice at last.",
        gentle=True,
        guardian=True,
        tags={"ghost", "lantern"},
    ),
    "dust_shadow": Spirit(
        id="dust_shadow",
        label="the dust shadow",
        opening="a blot of gray dust that swayed without shape",
        lesson="Shadows have no lesson worth keeping",
        gift_line="It offered nothing but a cold shiver.",
        gentle=False,
        guardian=False,
        tags={"dark"},
    ),
}

GIRL_NAMES = ["Mina", "Tara", "Lila", "Anya", "Nila", "Ria", "Kavya", "Sumi"]
BOY_NAMES = ["Arun", "Dev", "Rohan", "Kiran", "Amit", "Neel", "Ravi", "Manu"]
TRAITS = ["careful", "eager", "bright", "gentle", "spirited"]


@dataclass
class StoryParams:
    place: str
    promise: str
    spot: str
    spirit: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    elder: str
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
    "badminton": [
        (
            "What is badminton?",
            "Badminton is a game where players use rackets to hit a shuttlecock back and forth over a net. The shuttlecock is light, so it floats and dips instead of bouncing like a ball.",
        )
    ],
    "promise": [
        (
            "What is a promise?",
            "A promise is when you give your word that you will do something. People trust promises, so it is important to keep them or honestly fix things if you fail.",
        )
    ],
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a tale with spooky feelings, shadows, and spirits. Some ghost stories are scary, but others use the ghost to teach something important.",
        )
    ],
    "truth": [
        (
            "Why is telling the truth brave?",
            "Telling the truth is brave because you speak honestly even when you are afraid of trouble. Truth helps people solve problems instead of hiding them.",
        )
    ],
    "trust": [
        (
            "Why do promises matter?",
            "Promises matter because they help people trust each other. When you keep a promise, you show that your words can be believed.",
        )
    ],
    "dusk": [
        (
            "What is dusk?",
            "Dusk is the time when day is ending and night is beginning. The light grows dim, which can make ordinary places look mysterious.",
        )
    ],
}
KNOWLEDGE_ORDER = ["badminton", "promise", "ghost", "truth", "trust", "dusk"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    promise = f["promise_cfg"]
    place = f["place"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "badminton" and "promise".',
        f"Tell a spooky but kind story where {child.id} plays badminton at {place.label}, forgets a promise, and meets a ghost who teaches a moral lesson.",
        f'Write a child-facing moral-value story in ghost-story style where breaking a promise feels scary, telling the truth repairs the mistake, and the ending proves the child changed.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    elder = f["elder"]
    promise = f["promise_cfg"]
    place = f["place"]
    spot = f["spot_cfg"]
    spirit = f["spirit_cfg"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who went to play badminton with {friend.id}, and {child.id}'s {elder.label_word}, who trusted {child.pronoun('object')} to keep a promise.",
        ),
        (
            "What promise did the child make?",
            f"{child.id} promised: {promise.line} That promise mattered because someone at home was depending on {child.pronoun('object')} to do the right thing.",
        ),
        (
            "What changed the happy game into a ghost story?",
            f"The game changed when the shuttlecock flew into {spot.phrase} and evening made the place feel strange. {child.id} stepped toward the shadows after already pushing aside the promise, so fear and guilt rose together.",
        ),
    ]
    if f.get("spirit_seen"):
        qa.append(
            (
                "Why did the ghost appear?",
                f"The spirit appeared because the shuttlecock was lost in an eerie place after {child.id} had broken the promise. In this story world, the broken promise makes the moment feel morally wrong as well as spooky, so the ghost arrives to stop the mistake from growing bigger.",
            )
        )
    if f.get("truth_told"):
        qa.append(
            (
                "How did the child solve the problem?",
                f"{child.id} admitted the truth instead of pretending nothing was wrong. After the confession, the spirit returned the shuttlecock, and {child.id} hurried home to say sorry and repair the broken promise.",
            )
        )
    if f.get("repaired"):
        qa.append(
            (
                "What is the moral of the story?",
                f"The moral is that a promise should be kept, and if you fail, you should tell the truth quickly. {child.id} learned that words can feel as important as actions, especially when someone trusts you.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"badminton", "promise", "ghost", "truth", "trust", "dusk"}
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
        flags = []
        if e.portable:
            flags.append("portable")
        if e.hidden:
            flags.append("hidden")
        if e.eerie:
            flags.append("eerie")
        if flags:
            bits.append(f"flags={flags}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="courtyard",
        promise="before_dark",
        spot="shrine_steps",
        spirit="lantern_grandpa",
        child_name="Mina",
        child_gender="girl",
        friend_name="Arun",
        friend_gender="boy",
        elder="grandmother",
        trait="careful",
        seed=101,
    ),
    StoryParams(
        place="schoolyard",
        promise="return_racket",
        spot="banyan_roots",
        spirit="caretaker",
        child_name="Dev",
        child_gender="boy",
        friend_name="Lila",
        friend_gender="girl",
        elder="grandfather",
        trait="bright",
        seed=102,
    ),
    StoryParams(
        place="lane",
        promise="three_hits",
        spot="well_edge",
        spirit="feather_girl",
        child_name="Tara",
        child_gender="girl",
        friend_name="Neel",
        friend_gender="boy",
        elder="grandmother",
        trait="spirited",
        seed=103,
    ),
]


def explain_rejection(spot: HauntedSpot, spirit: Spirit) -> str:
    if not spot.hides_items:
        return (
            f"(No story: {spot.label} is too open to hide a lost shuttlecock, so the ghostly search has no real tension.)"
        )
    if not spot.eerie:
        return (
            f"(No story: {spot.label} does not feel eerie enough for a ghost-story turn.)"
        )
    if not spirit.gentle or not spirit.guardian:
        return (
            f"(No story: {spirit.label} is not a gentle guardian spirit, so it does not fit this child-facing moral ghost story.)"
        )
    return "(No story: this spot and spirit do not make a reasonable ghost-story pair.)"


ASP_RULES = r"""
relevant_promise(P, L) :- promise(P), place(L).

valid_pair(S, G) :- spot(S), spirit(G), hides_items(S), eerie(S), gentle(G), guardian(G).
valid(L, P, S, G) :- place(L), promise(P), relevant_promise(P, L), valid_pair(S, G).

broken_promise :- choose_break(yes).
lost_shuttle   :- choose_lost(yes).

spirit_appears :- broken_promise, lost_shuttle, chosen_spot(S), eerie(S), hides_items(S),
                  chosen_spirit(G), gentle(G), guardian(G).

truth_told :- spirit_appears.
repaired   :- truth_told.

#show valid/4.
#show spirit_appears/0.
#show repaired/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for promise_id in PROMISES:
        lines.append(asp.fact("promise", promise_id))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        if spot.hides_items:
            lines.append(asp.fact("hides_items", spot_id))
        if spot.eerie:
            lines.append(asp.fact("eerie", spot_id))
    for spirit_id, spirit in SPIRITS.items():
        lines.append(asp.fact("spirit", spirit_id))
        if spirit.gentle:
            lines.append(asp.fact("gentle", spirit_id))
        if spirit.guardian:
            lines.append(asp.fact("guardian", spirit_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_story_outcome(params: StoryParams) -> dict:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_spot", params.spot),
            asp.fact("chosen_spirit", params.spirit),
            asp.fact("choose_break", "yes"),
            asp.fact("choose_lost", "yes"),
        ]
    )
    model = asp.one_model(asp_program(extra))
    return {
        "spirit_appears": bool(asp.atoms(model, "spirit_appears")),
        "repaired": bool(asp.atoms(model, "repaired")),
    }


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

    smoke_params = CURATED[0]
    try:
        smoke = generate(smoke_params)
        if not smoke.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        emit(smoke, trace=False, qa=False, header="### smoke")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    mismatch = 0
    for params in CURATED:
        py_world = tell(
            PLACES[params.place],
            PROMISES[params.promise],
            SPOTS[params.spot],
            SPIRITS[params.spirit],
            child_name=params.child_name,
            child_gender=params.child_gender,
            friend_name=params.friend_name,
            friend_gender=params.friend_gender,
            elder_type=params.elder,
        )
        asp_out = asp_story_outcome(params)
        py_out = {
            "spirit_appears": py_world.facts["spirit_seen"],
            "repaired": py_world.facts["repaired"],
        }
        if asp_out != py_out:
            mismatch += 1
            print(f"MISMATCH for seed {params.seed}: asp={asp_out} python={py_out}")
    if mismatch == 0:
        print(f"OK: story outcome parity matches on {len(CURATED)} curated scenarios.")
    else:
        rc = 1

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: badminton, a promise, and a gentle ghost-story lesson."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--promise", choices=PROMISES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--spirit", choices=SPIRITS)
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spot and args.spirit:
        spot = SPOTS[args.spot]
        spirit = SPIRITS[args.spirit]
        if not valid_pair(spot, spirit):
            raise StoryError(explain_rejection(spot, spirit))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.promise is None or c[1] == args.promise)
        and (args.spot is None or c[2] == args.spot)
        and (args.spirit is None or c[3] == args.spirit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, promise, spot, spirit = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or _pick_name(rng, child_gender)
    friend_gender = "boy" if child_gender == "girl" else "girl"
    friend_name = _pick_name(rng, friend_gender, avoid=child_name)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place,
        promise=promise,
        spot=spot,
        spirit=spirit,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        elder=elder,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        promise = PROMISES[params.promise]
        spot = SPOTS[params.spot]
        spirit = SPIRITS[params.spirit]
    except KeyError as err:
        raise StoryError(f"Unknown parameter value: {err}") from None

    if not valid_pair(spot, spirit):
        raise StoryError(explain_rejection(spot, spirit))

    world = tell(
        place,
        promise,
        spot,
        spirit,
        child_name=params.child_name,
        child_gender=params.child_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        elder_type=params.elder,
    )

    world.get("child").traits.append(params.trait)

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
        print(f"{len(combos)} compatible (place, promise, spot, spirit) combos:\n")
        for place, promise, spot, spirit in combos:
            print(f"  {place:10} {promise:14} {spot:13} {spirit}")
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
            header = f"### {p.child_name}: {p.promise} at {p.place} ({p.spot}, {p.spirit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
