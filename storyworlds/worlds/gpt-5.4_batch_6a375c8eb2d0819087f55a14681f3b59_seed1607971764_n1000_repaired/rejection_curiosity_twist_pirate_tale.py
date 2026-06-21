#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rejection_curiosity_twist_pirate_tale.py
===================================================================

A standalone story world for a tiny pirate-play tale built around **rejection,
curiosity, and a twist**.

Premise
-------
Two children are playing pirates when they find something odd that looks like
junk. The captain quickly rejects the first mate's curious idea about it. But
the first mate keeps looking, and a twist reveals that the strange object really
is a clue. The crew follows it, finds a treasure, and the captain repairs the
hurt caused by the rejection.

Design notes
------------
This world models:
- typed entities with physical meters and emotional memes
- a short causal chain: rejection -> hurt, careful inspection -> clue decoded,
  decoded clue + following it -> treasure found, apology + shared treasure ->
  belonging restored
- a reasonableness gate: only clues that fit the chosen place and reveal method,
  and only treasures that plausibly fit the destination hiding spot, are allowed

Run it
------
    python storyworlds/worlds/gpt-5.4/rejection_curiosity_twist_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/rejection_curiosity_twist_pirate_tale.py --place beach
    python storyworlds/worlds/gpt-5.4/rejection_curiosity_twist_pirate_tale.py --clue rope_knots
    python storyworlds/worlds/gpt-5.4/rejection_curiosity_twist_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/rejection_curiosity_twist_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/rejection_curiosity_twist_pirate_tale.py --trace
    python storyworlds/worlds/gpt-5.4/rejection_curiosity_twist_pirate_tale.py --asp
    python storyworlds/worlds/gpt-5.4/rejection_curiosity_twist_pirate_tale.py --verify
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
OPEN_CAPTAINS = {"gentle", "thoughtful"}
STEADY_MATES = {"bold", "patient", "curious"}


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
class Setting:
    id: str
    scene: str
    rig: str
    dark_goal: str
    place_line: str
    afford_reveals: set[str] = field(default_factory=set)
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
class Spot:
    id: str
    label: str
    the: str
    place: str
    kind: str
    image: str
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
class RevealMethod:
    id: str
    label: str
    action_text: str
    twist_text: str
    supported_in: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    label: str
    phrase: str
    odd_look: str
    guess: str
    reveal: str
    destination: str
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
class Treasure:
    id: str
    label: str
    phrase: str
    fits: set[str] = field(default_factory=set)
    ending_image: str = ""
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_rejection_hurt(world: World) -> list[str]:
    mate = world.entities.get("mate")
    crew = world.entities.get("crew")
    if mate is None or crew is None:
        return []
    if mate.memes["rejected"] < THRESHOLD:
        return []
    sig = ("hurt", "mate")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mate.memes["hurt"] += 1
    crew.memes["together"] -= 1
    return []


def _r_decode(world: World) -> list[str]:
    clue = world.entities.get("clue")
    if clue is None:
        return []
    if clue.meters["inspected"] < THRESHOLD:
        return []
    if clue.meters["decoded"] >= THRESHOLD:
        return []
    sig = ("decode", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clue.meters["decoded"] += 1
    return ["__decoded__"]


def _r_find_treasure(world: World) -> list[str]:
    clue = world.entities.get("clue")
    treasure = world.entities.get("treasure")
    if clue is None or treasure is None:
        return []
    if clue.meters["decoded"] < THRESHOLD or treasure.meters["followed"] < THRESHOLD:
        return []
    sig = ("found", treasure.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    treasure.meters["found"] += 1
    return ["__found__"]


def _r_repair(world: World) -> list[str]:
    mate = world.entities.get("mate")
    captain = world.entities.get("captain")
    crew = world.entities.get("crew")
    treasure = world.entities.get("treasure")
    if not all((mate, captain, crew, treasure)):
        return []
    if captain.memes["apology"] < THRESHOLD or treasure.meters["found"] < THRESHOLD:
        return []
    sig = ("repair", "crew")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mate.memes["hurt"] = 0.0
    mate.memes["belonging"] += 1
    captain.memes["warmth"] += 1
    crew.memes["together"] += 2
    return []


CAUSAL_RULES = [
    Rule(name="rejection_hurt", tag="social", apply=_r_rejection_hurt),
    Rule(name="decode", tag="physical", apply=_r_decode),
    Rule(name="find_treasure", tag="physical", apply=_r_find_treasure),
    Rule(name="repair", tag="social", apply=_r_repair),
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
        for s in produced:
            world.say(s)
    return produced


def clue_fits_place(setting: Setting, clue: Clue) -> bool:
    spot = SPOTS[clue.destination]
    reveal = REVEALS[clue.reveal]
    return spot.place == setting.id and clue.reveal in setting.afford_reveals and setting.id in reveal.supported_in


def treasure_fits_clue(clue: Clue, treasure: Treasure) -> bool:
    spot = SPOTS[clue.destination]
    return spot.kind in treasure.fits


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for clue_id, clue in CLUES.items():
            if not clue_fits_place(setting, clue):
                continue
            for treasure_id, treasure in TREASURES.items():
                if treasure_fits_clue(clue, treasure):
                    out.append((place_id, clue_id, treasure_id))
    return sorted(out)


def outcome_of(params: "StoryParams") -> str:
    return "quick_listen" if params.captain_trait in OPEN_CAPTAINS else "proved_right"


def predict_decode(world: World) -> dict:
    sim = world.copy()
    sim.get("clue").meters["inspected"] += 1
    propagate(sim, narrate=False)
    return {
        "decoded": sim.get("clue").meters["decoded"] >= THRESHOLD,
    }


def play_setup(world: World, captain: Entity, mate: Entity, setting: Setting) -> None:
    captain.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {captain.id} and {mate.id} turned the day into "
        f"{setting.scene}. {setting.rig}"
    )
    world.say(
        f'"Captain {captain.id} and First Mate {mate.id}!" {captain.id} cheered. '
        f'"Let\'s find {setting.dark_goal}!"'
    )
    world.say(setting.place_line)


def discover_clue(world: World, mate: Entity, clue_cfg: Clue) -> None:
    clue = world.get("clue")
    clue.meters["noticed"] += 1
    mate.memes["curiosity"] += 1
    world.say(
        f"Near their path, {mate.id} spotted {clue_cfg.phrase}. It looked like "
        f"{clue_cfg.odd_look}."
    )
    world.say(
        f'{mate.id} crouched close. "Wait," {mate.pronoun()} whispered. '
        f'"What if it is {clue_cfg.guess}?"'
    )


def reject_guess(world: World, captain: Entity, mate: Entity, clue_cfg: Clue) -> None:
    mate.memes["rejected"] += 1
    captain.memes["pride"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{captain.id} gave a quick snort. "That? No, that is only {clue_cfg.odd_look}," '
        f'{captain.pronoun()} said. "A real pirate clue would look grander than that."'
    )
    world.say(
        f"The rejection made {mate.id} go quiet for a moment, but "
        f"{mate.pronoun("possessive")} eyes stayed fixed on the strange thing."
    )


def soft_turn(world: World, captain: Entity, mate: Entity, clue_cfg: Clue) -> None:
    pred = predict_decode(world)
    world.facts["predicted_decode"] = pred["decoded"]
    captain.memes["doubt"] += 1
    world.say(
        f"Then {captain.id} noticed how carefully {mate.id} was looking and slowed down. "
        f'"All right," {captain.pronoun()} said. "Show me what you see."'
    )


def hard_turn(world: World, captain: Entity, mate: Entity, clue_cfg: Clue, spot: Spot) -> None:
    captain.memes["stubborn"] += 1
    world.say(
        f"But {captain.id} marched off toward a very noisy-looking corner instead, sure that "
        f"the treasure had to be hiding somewhere flashy."
    )
    world.say(
        f"{mate.id} did not follow at once. Curiosity tugged harder than the sting of the rejection."
    )


def inspect_clue(world: World, mate: Entity, clue_cfg: Clue, reveal: RevealMethod) -> None:
    clue = world.get("clue")
    mate.memes["curiosity"] += 1
    clue.meters["inspected"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{mate.id} {reveal.action_text}."
    )
    world.say(reveal.twist_text)


def call_back(world: World, captain: Entity, mate: Entity) -> None:
    world.say(
        f'"Captain {captain.id}!" {mate.id} called. "Come see! It was a clue after all!"'
    )


def captain_returns(world: World, captain: Entity) -> None:
    captain.memes["surprise"] += 1
    world.say(
        f"{captain.id} spun around, blinked, and hurried back with boots thumping as fast as drums."
    )


def follow_clue(world: World, captain: Entity, mate: Entity, spot: Spot) -> None:
    treasure = world.get("treasure")
    treasure.meters["followed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they followed the clue to {spot.the}, where the boards and shadows suddenly looked full of secrets."
    )


def reveal_treasure(world: World, captain: Entity, mate: Entity, treasure_cfg: Treasure, spot: Spot) -> None:
    world.say(
        f"Tucked inside {spot.the} was {treasure_cfg.phrase}. For one breath both pirates only stared."
    )
    world.say(
        f"Then {captain.id} laughed first, and {mate.id} laughed right after, because the day had turned upside down in the best way."
    )


def apologize(world: World, captain: Entity, mate: Entity) -> None:
    captain.memes["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{captain.id} looked at {mate.id} and spoke more softly. "I was wrong to brush your idea away," '
        f'{captain.pronoun()} said. "I made you feel small, and I am sorry."'
    )
    world.say(
        f'{mate.id} nodded. "{mate.pronoun().capitalize()} was hurt," {mate.id} said, "but I am glad you came back."'
    )


def celebrate(world: World, captain: Entity, mate: Entity, treasure_cfg: Treasure, spot: Spot) -> None:
    captain.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f'Then {captain.id} lifted one hand in a grand pirate sweep. "From now on, First Mate {mate.id} is our best clue-finder."'
    )
    world.say(
        f"They shared the treasure at {spot.the}, and {treasure_cfg.ending_image}"
    )
def tell(
    clue_cfg: Clue,
    treasure_cfg: Treasure,
    captain_name: str,
    captain_gender: str,
    mate_name: str,
    mate_gender: str,
    captain_trait: CaptainTrait,
    mate_trait: MateTrait,
    parent_type: ParentType,
    pet: Pet,
    setting=None,
) -> World:
    spot = SPOTS[clue_cfg.destination]
    reveal = REVEALS[clue_cfg.reveal]

    world = World(setting)
    captain = world.add(Entity(
        id=captain_name,
        kind="character",
        type=captain_gender,
        role="captain",
        traits=[captain_trait],
        attrs={"pet": pet},
    ))
    mate = world.add(Entity(
        id=mate_name,
        kind="character",
        type=mate_gender,
        role="mate",
        traits=[mate_trait],
        attrs={"pet": pet},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    crew = world.add(Entity(
        id="crew",
        type="crew",
        label="the pirate crew",
    ))
    clue = world.add(Entity(
        id="clue",
        type="clue",
        label=clue_cfg.label,
        attrs={"reveal": reveal.id, "destination": spot.id},
    ))
    treasure = world.add(Entity(
        id="treasure",
        type="treasure",
        label=treasure_cfg.label,
        attrs={"spot": spot.id},
    ))

    crew.memes["together"] = 2.0
    captain.memes["joy"] = 0.0
    captain.memes["pride"] = 0.0
    captain.memes["apology"] = 0.0
    mate.memes["curiosity"] = 0.0
    mate.memes["rejected"] = 0.0
    mate.memes["hurt"] = 0.0
    mate.memes["belonging"] = 1.0
    clue.meters["noticed"] = 0.0
    clue.meters["inspected"] = 0.0
    clue.meters["decoded"] = 0.0
    treasure.meters["followed"] = 0.0
    treasure.meters["found"] = 0.0

    play_setup(world, captain, mate, setting)
    world.para()
    discover_clue(world, mate, clue_cfg)
    reject_guess(world, captain, mate, clue_cfg)

    world.para()
    branch = outcome_of(StoryParams(
        place=setting.id,
        clue=clue_cfg.id,
        treasure=treasure_cfg.id,
        captain=captain_name,
        captain_gender=captain_gender,
        mate=mate_name,
        mate_gender=mate_gender,
        parent=parent_type,
        captain_trait=captain_trait,
        mate_trait=mate_trait,
        pet=pet,
        seed=None,
    ))
    if branch == "quick_listen":
        soft_turn(world, captain, mate, clue_cfg)
        inspect_clue(world, mate, clue_cfg, reveal)
    else:
        hard_turn(world, captain, mate, clue_cfg, spot)
        inspect_clue(world, mate, clue_cfg, reveal)
        call_back(world, captain, mate)
        captain_returns(world, captain)

    world.para()
    follow_clue(world, captain, mate, spot)
    reveal_treasure(world, captain, mate, treasure_cfg, spot)
    apologize(world, captain, mate)

    world.para()
    celebrate(world, captain, mate, treasure_cfg, spot)

    world.facts.update(
        captain=captain,
        mate=mate,
        parent=parent,
        crew=crew,
        clue_cfg=clue_cfg,
        clue=clue,
        reveal_cfg=reveal,
        spot=spot,
        treasure_cfg=treasure_cfg,
        treasure=treasure,
        setting=setting,
        branch=branch,
        pet=pet,
        rejection_happened=mate.memes["rejected"] >= THRESHOLD,
        clue_decoded=clue.meters["decoded"] >= THRESHOLD,
        treasure_found=treasure.meters["found"] >= THRESHOLD,
    )
    return world
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


SETTINGS = {
    "beach": Setting(
        id="beach",
        scene="a windy pirate shore",
        rig="A striped towel became their sail, a stick was a mast, and a bucket sat upside down like a tiny captain's drum.",
        dark_goal="the hidden pirate prize",
        place_line="The beach was full of shells, driftwood, and little places where a secret might crouch and wait.",
        afford_reveals={"sun_glow", "wave_rinse"},
        tags={"beach", "pirates"},
    ),
    "backyard": Setting(
        id="backyard",
        scene="a backyard island with a fence for a fort wall",
        rig="A wheelbarrow became their ship, a broom was a mast, and a rope looped over a chair like a hanging anchor line.",
        dark_goal="the captain's buried reward",
        place_line="The backyard had flowerbeds, fence posts, and one old barrel that looked as if it could remember a hundred storms.",
        afford_reveals={"knot_count"},
        tags={"yard", "pirates"},
    ),
    "playroom": Setting(
        id="playroom",
        scene="a cozy pirate cabin",
        rig="The sofa was their ship, a blanket made a sail, and a cardboard box sat by the wall like a treasure chest waiting for orders.",
        dark_goal="the secret captain's hoard",
        place_line="The playroom felt full of corners and shadows, as if tiny maps might be hiding inside ordinary things.",
        afford_reveals={"lantern_shadow"},
        tags={"indoor", "pirates"},
    ),
}

SPOTS = {
    "drift_log": Spot(
        id="drift_log",
        label="drift log",
        the="the drift log",
        place="beach",
        kind="small_nook",
        image="the smooth drift log near the dune grass",
        tags={"log", "beach"},
    ),
    "old_barrel": Spot(
        id="old_barrel",
        label="old barrel",
        the="the old barrel",
        place="backyard",
        kind="small_nook",
        image="the old barrel by the fence",
        tags={"barrel", "yard"},
    ),
    "toy_chest": Spot(
        id="toy_chest",
        label="toy chest",
        the="the toy chest",
        place="playroom",
        kind="box_space",
        image="the toy chest by the wall",
        tags={"chest", "indoor"},
    ),
}

REVEALS = {
    "sun_glow": RevealMethod(
        id="sun_glow",
        label="sunlight",
        action_text="tilted it into a stripe of sun and rubbed off the sand with one thumb",
        twist_text="At once, pale lines shone through the glass: not scratches at all, but a tiny map with an X hidden in the shine.",
        supported_in={"beach"},
        tags={"sun", "map"},
    ),
    "wave_rinse": RevealMethod(
        id="wave_rinse",
        label="a wash of seawater",
        action_text="dipped it in the edge of a foamy wave and lifted it carefully",
        twist_text="The salt water cleared away the dull film, and underneath was a neat arrow worked into the shell all along.",
        supported_in={"beach"},
        tags={"waves", "shell"},
    ),
    "knot_count": RevealMethod(
        id="knot_count",
        label="counting the knots",
        action_text="held the rope still and counted each knot from one end to the other",
        twist_text="The knots were spaced too neatly to be messy. They counted out a set of steps, just like a secret pirate code.",
        supported_in={"backyard"},
        tags={"rope", "counting"},
    ),
    "lantern_shadow": RevealMethod(
        id="lantern_shadow",
        label="lamplight",
        action_text="held it under the lamp and turned it very slowly",
        twist_text="A dark anchor-shaped shadow stretched across the floor and pointed straight at the toy chest, as if the room itself had whispered the answer.",
        supported_in={"playroom"},
        tags={"shadow", "anchor"},
    ),
}

CLUES = {
    "bottle_map": Clue(
        id="bottle_map",
        label="bottle",
        phrase="a cloudy little bottle half-buried in the sand",
        odd_look="only a bit of beach glass and old cork",
        guess="a pirate message hiding inside",
        reveal="sun_glow",
        destination="drift_log",
        tags={"bottle", "map"},
    ),
    "shell_arrow": Clue(
        id="shell_arrow",
        label="shell",
        phrase="a large shell with chalky streaks on one side",
        odd_look="only a scratched shell",
        guess="an arrow somebody had hidden in plain sight",
        reveal="wave_rinse",
        destination="drift_log",
        tags={"shell", "arrow"},
    ),
    "rope_knots": Clue(
        id="rope_knots",
        label="rope",
        phrase="a short rope hanging from the fence rail",
        odd_look="only a floppy piece of old rope",
        guess="counting knots for a pirate code",
        reveal="knot_count",
        destination="old_barrel",
        tags={"rope", "code"},
    ),
    "anchor_token": Clue(
        id="anchor_token",
        label="anchor token",
        phrase="a paper anchor with one corner folded under",
        odd_look="only a crumpled bit of craft paper",
        guess="a clue that would point somewhere when the light hit it",
        reveal="lantern_shadow",
        destination="toy_chest",
        tags={"anchor", "shadow"},
    ),
}

TREASURES = {
    "gold_coins": Treasure(
        id="gold_coins",
        label="gold coins",
        phrase="a little bag of chocolate gold coins wrapped in red foil",
        fits={"small_nook", "box_space"},
        ending_image="the foil coins flashed between their fingers like sunset on little waves.",
        tags={"coins", "chocolate"},
    ),
    "bead_necklace": Treasure(
        id="bead_necklace",
        label="bead necklace",
        phrase="a shiny bead necklace with blue and green beads",
        fits={"small_nook", "box_space"},
        ending_image="the beads clicked softly while the two pirates took turns wearing them as captain's treasure.",
        tags={"beads", "necklace"},
    ),
    "star_compass": Treasure(
        id="star_compass",
        label="toy compass",
        phrase="a toy compass with a silver star on the lid",
        fits={"small_nook", "box_space"},
        ending_image="the little star on the lid caught the light, and both children leaned close as if the whole world might still hold one more clue.",
        tags={"compass", "star"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
CAPTAIN_TRAITS = ["gentle", "thoughtful", "proud", "bossy"]
MATE_TRAITS = ["curious", "patient", "bold", "careful"]
PETS = ["the cat", "the puppy", "their little dog", "the kitten", ""]


KNOWLEDGE = {
    "map": [(
        "What is a map?",
        "A map is a picture that helps you find where something is. It uses marks or shapes to point the way."
    )],
    "rope": [(
        "What is a knot?",
        "A knot is a twist or loop tied into rope or string. People can count knots or use them to hold things together."
    )],
    "shadow": [(
        "What is a shadow?",
        "A shadow is a dark shape made when light is blocked. Sometimes a shadow shows the shape of something in a new way."
    )],
    "shell": [(
        "What is a shell?",
        "A shell is the hard outside home of some sea animals. You can often find empty shells at the beach."
    )],
    "waves": [(
        "What do waves do at the beach?",
        "Waves roll water onto the shore and back again. They can wash sand away and make hidden things easier to see."
    )],
    "compass": [(
        "What does a compass do?",
        "A compass helps people know direction. It can show which way to go when they are exploring."
    )],
    "coins": [(
        "What are coins?",
        "Coins are small round pieces of money. In pretend pirate games, shiny coins often stand for treasure."
    )],
    "apology": [(
        "What is an apology?",
        "An apology is when you say you were wrong and try to make things better. A real apology helps another person feel seen and cared for."
    )],
    "rejection": [(
        "What is rejection?",
        "Rejection is when someone pushes away your idea, offer, or wish. It can make your heart feel sore, especially if you were trying to help."
    )],
}
KNOWLEDGE_ORDER = ["rejection", "map", "rope", "shell", "waves", "shadow", "coins", "compass", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    setting = f["setting"]
    clue_cfg = f["clue_cfg"]
    treasure_cfg = f["treasure_cfg"]
    branch = f["branch"]
    prompts = [
        'Write a pirate-play story for a 3-to-5-year-old that includes the word "rejection" and uses curiosity plus a twist.',
        f"Tell a gentle pirate tale where {captain.id} rejects {mate.id}'s strange clue idea, but the clue turns out to be real and leads to {treasure_cfg.label}.",
        f"Write a short story set in {setting.scene} where something that looks like {clue_cfg.odd_look} becomes an important clue."
    ]
    if branch == "proved_right":
        prompts.append(
            f"Make the captain too quick to dismiss the first mate at first, then use a twist to prove {mate.id} right and end with an apology."
        )
    else:
        prompts.append(
            f"Make the captain pause after a hasty rejection and listen before the clue's twist is revealed."
        )
    return prompts


def pair_noun(captain: Entity, mate: Entity) -> str:
    if captain.type == "boy" and mate.type == "boy":
        return "two boys"
    if captain.type == "girl" and mate.type == "girl":
        return "two girls"
    return "a boy and a girl"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    clue_cfg = f["clue_cfg"]
    reveal_cfg = f["reveal_cfg"]
    treasure_cfg = f["treasure_cfg"]
    spot = f["spot"]
    branch = f["branch"]
    pair = pair_noun(captain, mate)
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {captain.id} and {mate.id}, who were pretending to be pirates. One was the captain, and one was the first mate."
        ),
        (
            "What started the problem in the story?",
            f"The problem started when {mate.id} noticed {clue_cfg.phrase} and guessed it might be a real clue. {captain.id} rejected the idea too quickly because the clue looked plain and ordinary."
        ),
        (
            f"How did the rejection affect {mate.id}?",
            f"The rejection hurt {mate.id}'s feelings and made {mate.pronoun('object')} go quiet for a moment. But curiosity stayed stronger than the hurt, so {mate.pronoun()} kept looking carefully."
        ),
        (
            "What was the twist?",
            f"The twist was that the strange object really was a clue. When {mate.id} used {reveal_cfg.label}, it changed from seeming like {clue_cfg.odd_look} into a real sign that pointed the way."
        ),
        (
            "How did they find the treasure?",
            f"They followed the newly understood clue to {spot.the}. That led them to {treasure_cfg.phrase}, which proved {mate.id} had been right to look closer."
        ),
    ]
    if branch == "proved_right":
        out.append((
            f"Why did {captain.id} apologize?",
            f"{captain.id} apologized because {captain.pronoun()} had brushed aside {mate.id}'s good idea and made {mate.pronoun('object')} feel small. The treasure showed that the curious idea was wise after all."
        ))
    else:
        out.append((
            f"Why did {captain.id} stop and listen?",
            f"{captain.id} saw how carefully {mate.id} was studying the clue and realized there might be more to it. That small change let the crew discover the truth together."
        ))
    out.append((
        "How did the story end?",
        f"It ended with the two pirates sharing the treasure and feeling like a team again. The ending image shows that the crew changed because {captain.id} repaired the hurt and honored {mate.id}'s curiosity."
    ))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"rejection", "apology"}
    tags |= set(f["clue_cfg"].tags)
    tags |= set(f["reveal_cfg"].tags)
    tags |= set(f["treasure_cfg"].tags)
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:9} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    place: str
    clue: str
    treasure: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    parent: str
    captain_trait: str
    mate_trait: str
    pet: str = ""
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        place="beach",
        clue="bottle_map",
        treasure="gold_coins",
        captain="Tom",
        captain_gender="boy",
        mate="Lily",
        mate_gender="girl",
        parent="mother",
        captain_trait="proud",
        mate_trait="curious",
        pet="the puppy",
    ),
    StoryParams(
        place="beach",
        clue="shell_arrow",
        treasure="star_compass",
        captain="Mia",
        captain_gender="girl",
        mate="Ben",
        mate_gender="boy",
        parent="father",
        captain_trait="gentle",
        mate_trait="patient",
        pet="the cat",
    ),
    StoryParams(
        place="backyard",
        clue="rope_knots",
        treasure="bead_necklace",
        captain="Max",
        captain_gender="boy",
        mate="Nora",
        mate_gender="girl",
        parent="mother",
        captain_trait="bossy",
        mate_trait="bold",
        pet="",
    ),
    StoryParams(
        place="playroom",
        clue="anchor_token",
        treasure="gold_coins",
        captain="Ava",
        captain_gender="girl",
        mate="Theo",
        mate_gender="boy",
        parent="father",
        captain_trait="thoughtful",
        mate_trait="curious",
        pet="their little dog",
    ),
]


def explain_rejection(place: str, clue: str, treasure: str) -> str:
    if place not in SETTINGS:
        return f"(No story: unknown place '{place}'.)"
    if clue not in CLUES:
        return f"(No story: unknown clue '{clue}'.)"
    if treasure not in TREASURES:
        return f"(No story: unknown treasure '{treasure}'.)"
    setting = SETTINGS[place]
    clue_cfg = CLUES[clue]
    treasure_cfg = TREASURES[treasure]
    spot = SPOTS[clue_cfg.destination]
    reveal = REVEALS[clue_cfg.reveal]
    if spot.place != setting.id:
        return (
            f"(No story: {clue_cfg.label} points to {spot.the}, but that hiding place belongs in the {spot.place}, not {setting.id}. "
            f"The clue and place must match.)"
        )
    if clue_cfg.reveal not in setting.afford_reveals or setting.id not in reveal.supported_in:
        return (
            f"(No story: {setting.id} does not support the reveal method for {clue_cfg.label}. "
            f"The twist only works where {reveal.label} can plausibly reveal the clue.)"
        )
    if spot.kind not in treasure_cfg.fits:
        return (
            f"(No story: {treasure_cfg.label} does not plausibly fit in {spot.the}. "
            f"Pick a treasure that can be hidden in a {spot.kind.replace('_', ' ')}.)"
        )
    return "(No story: this combination is not reasonable in this world.)"


ASP_RULES = r"""
valid(Place, Clue, Treasure) :-
    setting(Place), clue(Clue), treasure(Treasure),
    clue_spot(Clue, Spot), spot_place(Spot, Place),
    clue_reveal(Clue, Reveal), setting_affords(Place, Reveal), reveal_supported(Place, Reveal),
    spot_kind(Spot, Kind), treasure_fits(Treasure, Kind).

open_captain(T) :- captain_trait(T), captain_open(T).
outcome(quick_listen) :- chosen_trait(T), captain_open(T).
outcome(proved_right) :- chosen_trait(T), not captain_open(T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place_id))
        for reveal_id in sorted(setting.afford_reveals):
            lines.append(asp.fact("setting_affords", place_id, reveal_id))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        lines.append(asp.fact("spot_place", spot_id, spot.place))
        lines.append(asp.fact("spot_kind", spot_id, spot.kind))
    for reveal_id, reveal in REVEALS.items():
        lines.append(asp.fact("reveal", reveal_id))
        for place_id in sorted(reveal.supported_in):
            lines.append(asp.fact("reveal_supported", place_id, reveal_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_reveal", clue_id, clue.reveal))
        lines.append(asp.fact("clue_spot", clue_id, clue.destination))
    for treasure_id, treasure in TREASURES.items():
        lines.append(asp.fact("treasure", treasure_id))
        for kind in sorted(treasure.fits):
            lines.append(asp.fact("treasure_fits", treasure_id, kind))
    for trait in CAPTAIN_TRAITS:
        lines.append(asp.fact("captain_trait", trait))
    for trait in sorted(OPEN_CAPTAINS):
        lines.append(asp.fact("captain_open", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    program = asp_program(
        asp.fact("chosen_trait", params.captain_trait),
        "#show outcome/1.",
    )
    model = asp.one_model(program)
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"MISMATCH: resolve_params failed on seed {s}.")
            break

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
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_params.seed = 123
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        _ = smoke_sample.to_json()
        print("OK: generate()/to_json() smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirate play, rejection, curiosity, and a twist. "
                    "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--captain-trait", choices=CAPTAIN_TRAITS)
    ap.add_argument("--mate-trait", choices=MATE_TRAITS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.clue and args.treasure:
        triple = (args.place, args.clue, args.treasure)
        if triple not in set(valid_combos()):
            raise StoryError(explain_rejection(args.place, args.clue, args.treasure))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.clue is None or combo[1] == args.clue)
        and (args.treasure is None or combo[2] == args.treasure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, clue, treasure = rng.choice(combos)
    captain, captain_gender = _pick_name(rng)
    mate, mate_gender = _pick_name(rng, avoid=captain)
    parent = args.parent or rng.choice(["mother", "father"])
    captain_trait = args.captain_trait or rng.choice(CAPTAIN_TRAITS)
    mate_trait = args.mate_trait or rng.choice(MATE_TRAITS)
    pet = rng.choice(PETS)
    return StoryParams(
        place=place,
        clue=clue,
        treasure=treasure,
        captain=captain,
        captain_gender=captain_gender,
        mate=mate,
        mate_gender=mate_gender,
        parent=parent,
        captain_trait=captain_trait,
        mate_trait=mate_trait,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(explain_rejection(params.place, params.clue, params.treasure))
    if params.clue not in CLUES:
        raise StoryError(explain_rejection(params.place, params.clue, params.treasure))
    if params.treasure not in TREASURES:
        raise StoryError(explain_rejection(params.place, params.clue, params.treasure))
    if (params.place, params.clue, params.treasure) not in set(valid_combos()):
        raise StoryError(explain_rejection(params.place, params.clue, params.treasure))
    if params.captain_trait not in CAPTAIN_TRAITS:
        raise StoryError(f"(No story: unknown captain trait '{params.captain_trait}'.)")
    if params.mate_trait not in MATE_TRAITS:
        raise StoryError(f"(No story: unknown mate trait '{params.mate_trait}'.)")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(No story: unknown parent type '{params.parent}').")

    world = tell(
        setting=SETTINGS[params.place],
        clue_cfg=CLUES[params.clue],
        treasure_cfg=TREASURES[params.treasure],
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        mate_name=params.mate,
        mate_gender=params.mate_gender,
        captain_trait=params.captain_trait,
        mate_trait=params.mate_trait,
        parent_type=params.parent,
        pet=params.pet,
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
        print(f"{len(combos)} compatible (place, clue, treasure) combos:\n")
        for place, clue, treasure in combos:
            print(f"  {place:10} {clue:13} {treasure}")
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
            header = f"### {p.captain} & {p.mate}: {p.place}, {p.clue}, {p.treasure} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
