#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/macho_dank_mystery_to_solve_moral_value.py
=====================================================================

A standalone story world about two children playing pirates when an important
treasure-item goes missing. One child starts off macho and boastful, wanting to
solve the mystery alone. The clues lead them into a high or dank hiding place,
where the boaster has to tell the truth, ask for help, and change. The mystery
gets solved, the game is saved, and the ending proves the transformation.

Run it
------
python storyworlds/worlds/gpt-5.4/macho_dank_mystery_to_solve_moral_value.py
python storyworlds/worlds/gpt-5.4/macho_dank_mystery_to_solve_moral_value.py --scene cove --culprit gull --item map_tube --hiding gull_nest
python storyworlds/worlds/gpt-5.4/macho_dank_mystery_to_solve_moral_value.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/macho_dank_mystery_to_solve_moral_value.py --all
python storyworlds/worlds/gpt-5.4/macho_dank_mystery_to_solve_moral_value.py --verify
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
class Scene:
    id: str
    title: str
    opening: str
    game_line: str
    missing_place: str
    ambience: str
    affords: set[str] = field(default_factory=set)
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
class MissingItem:
    id: str
    label: str
    phrase: str
    texture: str
    purpose: str
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
class Culprit:
    id: str
    label: str
    likes: set[str] = field(default_factory=set)
    reaches: set[str] = field(default_factory=set)
    clue_text: str = ""
    move_text: str = ""
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
class HidingPlace:
    id: str
    label: str
    phrase: str
    challenge: str
    recover_text: str
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
class Moral:
    id: str
    lesson: str
    promise: str
    ending: str
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


def _r_missing_worry(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("leader").memes["worry"] += 1
    world.get("mate").memes["worry"] += 1
    world.get("game").meters["stalled"] += 1
    return []


def _r_clue_points(world: World) -> list[str]:
    if not world.facts.get("clue_seen"):
        return []
    sig = ("clue_points",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("mate").memes["insight"] += 1
    culprit = world.facts["culprit"]
    world.facts["suspect"] = culprit.id
    return []


def _r_challenge_fear(world: World) -> list[str]:
    leader = world.get("leader")
    place = world.facts["hiding_cfg"]
    if not world.facts.get("entered_search"):
        return []
    sig = ("challenge_fear", place.id)
    if sig in world.fired:
        return []
    if place.challenge not in {"dank", "high"}:
        return []
    world.fired.add(sig)
    if place.challenge == "dank":
        leader.memes["fear"] += 1
    else:
        leader.memes["doubt"] += 1
    return []


def _r_truth_turn(world: World) -> list[str]:
    leader = world.get("leader")
    if not world.facts.get("entered_search"):
        return []
    challenge = world.facts["hiding_cfg"].challenge
    needed = leader.memes["fear"] >= THRESHOLD if challenge == "dank" else leader.memes["doubt"] >= THRESHOLD
    if not needed or leader.memes["bravado"] < THRESHOLD:
        return []
    sig = ("truth_turn", challenge)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    leader.memes["honesty"] += 1
    leader.memes["bravado"] = 0.0
    world.get("mate").memes["trust"] += 1
    world.facts["asked_help"] = True
    return []


def _r_teamwork_restore(world: World) -> list[str]:
    if not world.facts.get("asked_help"):
        return []
    sig = ("teamwork_restore",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item = world.get("item")
    item.meters["missing"] = 0.0
    item.meters["found"] += 1
    world.get("game").meters["stalled"] = 0.0
    world.get("leader").memes["joy"] += 1
    world.get("mate").memes["joy"] += 1
    world.get("leader").memes["growth"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_worry", tag="social", apply=_r_missing_worry),
    Rule(name="clue_points", tag="mystery", apply=_r_clue_points),
    Rule(name="challenge_fear", tag="emotion", apply=_r_challenge_fear),
    Rule(name="truth_turn", tag="emotion", apply=_r_truth_turn),
    Rule(name="teamwork_restore", tag="social", apply=_r_teamwork_restore),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                changed = changed or False
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def culprit_can_take(culprit: Culprit, item: MissingItem) -> bool:
    return bool(culprit.likes & item.tags)


def hiding_fits(culprit: Culprit, hiding: HidingPlace) -> bool:
    return hiding.id in culprit.reaches


def scene_supports(scene: Scene, hiding: HidingPlace) -> bool:
    return hiding.id in scene.affords


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for scene_id, scene in SCENES.items():
        for culprit_id, culprit in CULPRITS.items():
            for item_id, item in ITEMS.items():
                for hiding_id, hiding in HIDING_PLACES.items():
                    if culprit_can_take(culprit, item) and hiding_fits(culprit, hiding) and scene_supports(scene, hiding):
                        combos.append((scene_id, culprit_id, item_id, hiding_id))
    return sorted(combos)


def explain_rejection(scene: Scene, culprit: Culprit, item: MissingItem, hiding: HidingPlace) -> str:
    if not culprit_can_take(culprit, item):
        return (
            f"(No story: {culprit.label} would not bother taking {item.phrase}. "
            f"This culprit goes after things with tags {sorted(culprit.likes)}, "
            f"but that item has tags {sorted(item.tags)}.)"
        )
    if not hiding_fits(culprit, hiding):
        return (
            f"(No story: {culprit.label} cannot plausibly hide anything in {hiding.phrase}. "
            f"That place does not fit how this culprit moves.)"
        )
    if not scene_supports(scene, hiding):
        return (
            f"(No story: {scene.title} does not contain {hiding.phrase}, so the clue trail "
            f"has nowhere honest to lead.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


def challenge_of(params: "StoryParams") -> str:
    if params.hiding not in HIDING_PLACES:
        raise StoryError(f"(Unknown hiding place: {params.hiding})")
    return HIDING_PLACES[params.hiding].challenge


def outcome_of(params: "StoryParams") -> str:
    challenge = challenge_of(params)
    return "admit_scared" if challenge == "dank" else "admit_need"


def predict_turn(world: World) -> dict:
    sim = world.copy()
    sim.facts["entered_search"] = True
    propagate(sim, narrate=False)
    challenge = sim.facts["hiding_cfg"].challenge
    return {
        "challenge": challenge,
        "asked_help": bool(sim.facts.get("asked_help")),
    }


def setup_play(world: World, leader: Entity, mate: Entity, scene: Scene, item: MissingItem) -> None:
    leader.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(scene.opening)
    world.say(scene.game_line)
    world.say(
        f"They needed {item.phrase} for the grand ending of the game, because {item.purpose}."
    )
    world.say(
        f"But when {leader.id} reached for it at {scene.missing_place}, it was gone."
    )
    world.get("item").meters["missing"] += 1
    propagate(world, narrate=False)


def boast(world: World, leader: Entity, mate: Entity, item: MissingItem) -> None:
    leader.memes["bravado"] += 1
    world.say(
        f'"Nobody panic," {leader.id} said in a macho voice. "{leader.pronoun("subject").capitalize()} can solve '
        f"this mystery alone and bring back the {item.label} before the tide even blinks."
    )
    world.say(
        f"{mate.id} looked around the floorboards and sacks instead of arguing."
    )


def notice_clue(world: World, mate: Entity, culprit: Culprit) -> None:
    world.facts["clue_seen"] = True
    propagate(world, narrate=False)
    world.say(
        f"Then {mate.id} pointed. {culprit.clue_text}"
    )
    world.say(
        f'"That is a clue," {mate.id} said. "A real pirate uses {mate.pronoun("possessive")} eyes before {mate.pronoun("possessive")} mouth."'
    )


def follow_clue(world: World, leader: Entity, mate: Entity, hiding: HidingPlace, scene: Scene) -> None:
    turn = predict_turn(world)
    hint = "dark and a little dank" if turn["challenge"] == "dank" else "so high it swayed above their heads"
    world.say(
        f"The clue trail led them through {scene.ambience} to {hiding.phrase}, {hint}."
    )
    world.facts["entered_search"] = True
    propagate(world, narrate=False)


def confession(world: World, leader: Entity, mate: Entity, hiding: HidingPlace) -> None:
    challenge = hiding.challenge
    if challenge == "dank":
        world.say(
            f"{leader.id} took two brave steps toward {hiding.phrase}, then stopped. "
            f'The macho voice fell right out of {leader.pronoun("possessive")} mouth. '
            f'"I do not like how dark and dank it is in there," {leader.pronoun()} admitted.'
        )
        world.say(
            f'"Will you come with me?"'
        )
    else:
        world.say(
            f"{leader.id} stretched up toward {hiding.phrase}, but it was too high for one child alone. "
            f'The macho grin crumpled into an honest one. "I cannot reach it by myself," {leader.pronoun()} said.'
        )
        world.say(
            f'"Will you help me instead of letting me bluster?"'
        )
    world.say(
        f'{mate.id} nodded at once. "Of course," {mate.pronoun()} said. "Pirates who tell the truth solve more mysteries."'
    )


def recover(world: World, leader: Entity, mate: Entity, item: MissingItem, culprit: Culprit, hiding: HidingPlace) -> None:
    world.say(
        f"Together they {hiding.recover_text}, and there was {item.phrase}."
    )
    world.say(
        f"{culprit.move_text}"
    )
    if hiding.challenge == "dank":
        world.say(
            f"{leader.id} held the item tight, and the dark place did not seem so large with {mate.id} beside {leader.pronoun('object')}."
        )
    else:
        world.say(
            f"{mate.id} steadied the crate below while {leader.id} reached, and the wobbling place felt simple once they worked as a pair."
        )


def lesson(world: World, leader: Entity, mate: Entity, parent: Entity, moral: Moral, item: MissingItem) -> None:
    world.say(
        f"When they came back out, {parent.label_word.capitalize()} was waiting by the dock rope with a soft smile."
    )
    world.say(
        f'"Did you find the {item.label}?" {parent.pronoun()} asked.'
    )
    world.say(
        f'"Yes," said {leader.id}, "and I learned {moral.lesson}."'
    )
    world.say(
        f'{mate.id} squeezed {leader.pronoun("possessive")} hand. "{moral.promise}"'
    )
    world.say(
        moral.ending
    )
def tell(
    culprit: Culprit,
    item: Item,
    hiding: Hiding,
    moral: Moral,
    leader_name: str,
    leader_gender: str,
    mate_name: str,
    mate_gender: str,
    parent_type: ParentType,
    scene=None,
) -> World:
    world = World()
    leader = world.add(Entity(id=leader_name, kind="character", type=leader_gender, role="leader", traits=["bold"], attrs={}))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_gender, role="mate", traits=["careful"], attrs={}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent", attrs={}))
    world.add(Entity(id="game", kind="thing", type="game", label="the pirate game", attrs={}))
    world.add(Entity(id="item", kind="thing", type="treasure", label=item.label, attrs={}))

    world.facts.update(
        scene=scene,
        culprit=culprit,
        item_cfg=item,
        hiding_cfg=hiding,
        moral=moral,
        clue_seen=False,
        entered_search=False,
        asked_help=False,
        suspect="",
    )

    setup_play(world, leader, mate, scene, item)
    world.para()
    boast(world, leader, mate, item)
    notice_clue(world, mate, culprit)
    follow_clue(world, leader, mate, hiding, scene)
    confession(world, leader, mate, hiding)
    world.para()
    recover(world, leader, mate, item, culprit, hiding)
    propagate(world, narrate=False)
    lesson(world, leader, mate, parent, moral, item)

    world.facts.update(
        leader=leader,
        mate=mate,
        parent=parent,
        found=world.get("item").meters["found"] >= THRESHOLD,
        outcome=outcome_of(
            StoryParams(
                scene=scene.id,
                culprit=culprit.id,
                item=item.id,
                hiding=hiding.id,
                moral=moral.id,
                leader=leader_name,
                leader_gender=leader_gender,
                mate=mate_name,
                mate_gender=mate_gender,
                parent=parent_type,
                seed=None,
            )
        ),
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


SCENES = {
    "harbor": Scene(
        id="harbor",
        title="the little harbor",
        opening="On a windy afternoon, two children turned the little harbor into a pirate kingdom. A wooden bench became a ship, a coil of rope became a sea serpent, and the dock posts stood like old masts over the water.",
        game_line='"Captain Rex and Scout Lina!" Rex cried. "Today we find the stolen treasure before sunset."',
        missing_place="the old bait box beside the pier",
        ambience="salt wind, creaking planks, and shadowy stacks of nets",
        affords={"barrel_nook", "net_loft"},
        tags={"harbor"},
    ),
    "cove": Scene(
        id="cove",
        title="the cove",
        opening="On a silver morning, two children turned the cove into a pirate island. Driftwood made a brave little ship, a bucket became a drum, and a torn blue towel flapped like a captain's flag.",
        game_line='"Captain Rex and Scout Lina!" Rex cried. "Today we solve the mystery of the missing treasure."',
        missing_place="the flat rock they used as a treasure table",
        ambience="seaweed smell, dripping stone, and the hush of waves in the cove",
        affords={"tide_crevice", "barrel_nook"},
        tags={"cove"},
    ),
    "boathouse": Scene(
        id="boathouse",
        title="the boathouse",
        opening="On a gray afternoon, two children turned the old boathouse into a pirate fort. An upside-down tub became a captain's drum, hanging ropes looked like rigging, and each puddle on the floor shivered with thin strips of light.",
        game_line='"Captain Rex and Scout Lina!" Rex cried. "No thief can outsmart us today."',
        missing_place="the shelf under the lantern hook",
        ambience="the smell of wet wood, rope, and a gently dank corner under the eaves",
        affords={"barrel_nook", "net_loft"},
        tags={"boathouse", "dank"},
    ),
}

ITEMS = {
    "compass": MissingItem(
        id="compass",
        label="compass",
        phrase="the brass compass",
        texture="shiny",
        purpose="without it, their ship could not pretend to steer toward the secret island",
        tags={"shiny", "round"},
    ),
    "shell_key": MissingItem(
        id="shell_key",
        label="shell key",
        phrase="the shell key on a blue string",
        texture="shiny",
        purpose="without it, their treasure chest could never be opened",
        tags={"shiny", "string"},
    ),
    "map_tube": MissingItem(
        id="map_tube",
        label="map tube",
        phrase="the rolled map tube",
        texture="crinkly",
        purpose="without it, nobody could point the way to the hidden cave",
        tags={"crinkly", "paper"},
    ),
    "velvet_flag": MissingItem(
        id="velvet_flag",
        label="velvet flag",
        phrase="the little velvet flag",
        texture="soft",
        purpose="without it, the ship had no proud sign to raise at the end",
        tags={"soft", "cloth"},
    ),
}

CULPRITS = {
    "gull": Culprit(
        id="gull",
        label="a gull",
        likes={"shiny", "crinkly"},
        reaches={"net_loft", "gull_nest"},
        clue_text='A white feather lay on the plank, and beside it was a tiny scrape, as if something light had been tugged and dragged away.',
        move_text="A gull on the roof gave one offended squawk, as if it had only borrowed something bright for nest business.",
        tags={"gull", "bird"},
    ),
    "crab": Culprit(
        id="crab",
        label="a crab",
        likes={"shiny", "round"},
        reaches={"tide_crevice"},
        clue_text='Near the waterline, little side-stepping marks stitched the sand, and something glimmered once from a crack in the stone.',
        move_text="From deeper in the crack, a crab clicked its claws, proud of its shiny prize.",
        tags={"crab", "shore"},
    ),
    "puppy": Culprit(
        id="puppy",
        label="the harbor puppy",
        likes={"soft", "cloth", "string"},
        reaches={"barrel_nook"},
        clue_text='A damp pawprint curved around a barrel, and a short bit of blue string poked out from the straw behind it.',
        move_text="The harbor puppy thumped its tail against the barrel, pleased that its hiding game had finally been understood.",
        tags={"dog", "puppy"},
    ),
}

HIDING_PLACES = {
    "tide_crevice": HidingPlace(
        id="tide_crevice",
        label="tide crevice",
        phrase="a narrow crevice in the tide rock",
        challenge="dank",
        recover_text="crouched together, reached into the chilly stone crack, and felt around carefully",
        tags={"dank", "wet", "low"},
    ),
    "barrel_nook": HidingPlace(
        id="barrel_nook",
        label="barrel nook",
        phrase="the shadowy nook behind a barrel",
        challenge="dank",
        recover_text="moved the barrel together and peered into the small, dank space behind it",
        tags={"dank", "low"},
    ),
    "net_loft": HidingPlace(
        id="net_loft",
        label="net loft",
        phrase="the high loft where old nets hung from beams",
        challenge="high",
        recover_text="dragged over a safe crate, held it steady together, and reached up through the hanging nets",
        tags={"high", "dry"},
    ),
    "gull_nest": HidingPlace(
        id="gull_nest",
        label="gull nest",
        phrase="the gull nest tucked high under the roof edge",
        challenge="high",
        recover_text="balanced the ladder with four careful hands and reached into the nest with great respect",
        tags={"high", "roof"},
    ),
}

MORALS = {
    "help": Moral(
        id="help",
        lesson="that asking for help is braver than pretending not to need it",
        promise='"Next time, we will solve things together from the start."',
        ending="Then they raised the treasure high, and the pirate game sailed on again, not louder than before, but wiser.",
        tags={"help", "honesty"},
    ),
    "truth": Moral(
        id="truth",
        lesson="that telling the truth about being scared makes room for courage to grow",
        promise='"Next time, we tell the truth first and the bragging can stay on shore."',
        ending="Then they raised the treasure high, and even the wind seemed gentler, as if it liked honest captains better.",
        tags={"truth", "courage"},
    ),
}


GIRL_NAMES = ["Lina", "Mara", "Nora", "Tess", "Ruby", "Ivy", "Zoe", "Anna"]
BOY_NAMES = ["Rex", "Ben", "Max", "Leo", "Finn", "Theo", "Jack", "Eli"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    mate = f["mate"]
    item = f["item_cfg"]
    culprit = f["culprit"]
    hiding = f["hiding_cfg"]
    moral = f["moral"]
    return [
        f'Write a pirate-style story for a 3-to-5-year-old that includes the words "macho" and "dank". Make the missing object be a {item.label} and let the mystery end with kindness.',
        f"Tell a gentle mystery where {leader.id} starts out macho and boastful, {mate.id} notices the real clue, and together they find {item.phrase} after following signs left by {culprit.label}.",
        f"Write a complete story with a beginning, a mystery to solve, and a transformation: the clue trail leads to {hiding.phrase}, and the ending teaches {moral.lesson}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    mate = f["mate"]
    parent = f["parent"]
    scene = f["scene"]
    item = f["item_cfg"]
    culprit = f["culprit"]
    hiding = f["hiding_cfg"]
    moral = f["moral"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {leader.id} and {mate.id}, two children playing pirates near {scene.title}, and {leader.id}'s {parent.label_word}. Their game turns into a mystery when the treasure-item goes missing."
        ),
        (
            f"What was missing?",
            f"The missing thing was {item.phrase}. It mattered because {item.purpose}."
        ),
        (
            f"Who found the important clue?",
            f"{mate.id} found the clue. {mate.pronoun('subject').capitalize()} noticed the small sign that pointed toward {culprit.label}, so the search became a real mystery instead of wild guessing."
        ),
        (
            f"Why did {leader.id} change during the story?",
            f"{leader.id} began by acting macho and saying {leader.pronoun('subject')} could solve everything alone. But when the clue led to {hiding.phrase}, {leader.pronoun('subject')} had to tell the truth and ask for help, and that honest moment changed how {leader.pronoun('subject')} acted."
        ),
    ]
    if outcome == "admit_scared":
        qa.append(
            (
                f"What truth did {leader.id} tell in the dark place?",
                f"{leader.id} admitted that the hiding place felt dark and dank and that {leader.pronoun('subject')} did not want to go in alone. Saying that truth made teamwork possible, because {mate.id} could help once {leader.pronoun('subject')} stopped pretending."
            )
        )
    else:
        qa.append(
            (
                f"What truth did {leader.id} tell at the high place?",
                f"{leader.id} admitted that {leader.pronoun('subject')} could not reach the hiding place alone. That mattered because the mystery was solved only after {mate.id} steadied things and helped with the search."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"They found {item.phrase}, understood that {culprit.label} had carried it off, and went back to the game together. The ending shows the change because {leader.id} is not bragging anymore and instead wants to work side by side."
        )
    )
    qa.append(
        (
            "What lesson did they learn?",
            f"They learned {moral.lesson}. The clue, the hard hiding place, and the shared rescue all proved that honesty and help make people stronger, not smaller."
        )
    )
    return qa


KNOWLEDGE = {
    "gull": [
        (
            "Why do gulls sometimes take shiny or crinkly things?",
            "Gulls are curious birds, and shiny or rustly things can catch their eyes. They may grab them because the objects look interesting, not because they understand who owns them."
        )
    ],
    "crab": [
        (
            "Where do crabs like to hide?",
            "Crabs like narrow rocky places near the water where they can tuck themselves in. Those cracks stay cool and wet, which helps them feel safe."
        )
    ],
    "dog": [
        (
            "Why do puppies hide things?",
            "Puppies often carry and hide things because they are playful and curious. They are not being mean; they are exploring with their mouths and paws."
        )
    ],
    "dank": [
        (
            "What does dank mean?",
            "Dank means a place feels wet, cool, and a little dark. A dank place might smell like stone, wood, or water that has stayed there awhile."
        )
    ],
    "help": [
        (
            "Why is asking for help brave?",
            "Asking for help is brave because you tell the truth about what you need. That honesty lets other people work with you and keeps a problem from growing bigger."
        )
    ],
    "truth": [
        (
            "Why does telling the truth help solve problems?",
            "Telling the truth helps because everyone can see the real problem clearly. When people stop pretending, they can choose the right next step together."
        )
    ],
    "pirate": [
        (
            "What is a compass for?",
            "A compass helps sailors know which direction they are going. In pirate games, it feels special because it helps pretend ships find their way."
        )
    ],
}
KNOWLEDGE_ORDER = ["dank", "gull", "crab", "dog", "help", "truth", "pirate"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["culprit"].tags) | set(f["moral"].tags)
    if f["item_cfg"].id == "compass":
        tags.add("pirate")
    if f["hiding_cfg"].challenge == "dank":
        tags.add("dank")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: suspect={world.facts.get('suspect')} asked_help={world.facts.get('asked_help')} outcome={world.facts.get('outcome')}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    scene: str
    culprit: str
    item: str
    hiding: str
    moral: str
    leader: str
    leader_gender: str
    mate: str
    mate_gender: str
    parent: str
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        scene="cove",
        culprit="crab",
        item="compass",
        hiding="tide_crevice",
        moral="truth",
        leader="Rex",
        leader_gender="boy",
        mate="Lina",
        mate_gender="girl",
        parent="mother",
        seed=None,
    ),
    StoryParams(
        scene="harbor",
        culprit="puppy",
        item="velvet_flag",
        hiding="barrel_nook",
        moral="help",
        leader="Max",
        leader_gender="boy",
        mate="Nora",
        mate_gender="girl",
        parent="father",
        seed=None,
    ),
    StoryParams(
        scene="boathouse",
        culprit="gull",
        item="map_tube",
        hiding="net_loft",
        moral="help",
        leader="Finn",
        leader_gender="boy",
        mate="Ruby",
        mate_gender="girl",
        parent="mother",
        seed=None,
    ),
    StoryParams(
        scene="harbor",
        culprit="gull",
        item="shell_key",
        hiding="net_loft",
        moral="truth",
        leader="Leo",
        leader_gender="boy",
        mate="Ivy",
        mate_gender="girl",
        parent="father",
        seed=None,
    ),
]


ASP_RULES = r"""
takes(C, I) :- culprit(C), item(I), likes(C, T), item_tag(I, T).
fits(C, H)  :- culprit(C), hiding(H), reaches(C, H).
present(S, H) :- scene(S), affords(S, H).

valid(S, C, I, H) :- takes(C, I), fits(C, H), present(S, H).

outcome(admit_scared) :- chosen_hiding(H), challenge(H, dank).
outcome(admit_need)   :- chosen_hiding(H), challenge(H, high).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
        for hid in sorted(SCENES[sid].affords):
            lines.append(asp.fact("affords", sid, hid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for tag in sorted(item.tags):
            lines.append(asp.fact("item_tag", iid, tag))
    for cid, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        for tag in sorted(culprit.likes):
            lines.append(asp.fact("likes", cid, tag))
        for hid in sorted(culprit.reaches):
            lines.append(asp.fact("reaches", cid, hid))
    for hid, place in HIDING_PLACES.items():
        lines.append(asp.fact("hiding", hid))
        lines.append(asp.fact("challenge", hid, place.challenge))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    model = asp.one_model(
        asp_program(
            asp.fact("chosen_hiding", params.hiding),
            "#show outcome/1.",
        )
    )
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: pirate-style mystery, moral value, and transformation."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hiding", choices=HIDING_PLACES)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.culprit and args.item and args.hiding:
        scene = SCENES[args.scene]
        culprit = CULPRITS[args.culprit]
        item = ITEMS[args.item]
        hiding = HIDING_PLACES[args.hiding]
        if not (culprit_can_take(culprit, item) and hiding_fits(culprit, hiding) and scene_supports(scene, hiding)):
            raise StoryError(explain_rejection(scene, culprit, item, hiding))

    combos = [
        combo
        for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.item is None or combo[2] == args.item)
        and (args.hiding is None or combo[3] == args.hiding)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, culprit_id, item_id, hiding_id = rng.choice(sorted(combos))
    moral_id = args.moral or ("truth" if HIDING_PLACES[hiding_id].challenge == "dank" else "help")
    leader_gender = "boy"
    mate_gender = rng.choice(["girl", "boy"])
    leader_name = _pick_name(rng, leader_gender)
    mate_name = _pick_name(rng, mate_gender, avoid=leader_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        scene=scene_id,
        culprit=culprit_id,
        item=item_id,
        hiding=hiding_id,
        moral=moral_id,
        leader=leader_name,
        leader_gender=leader_gender,
        mate=mate_name,
        mate_gender=mate_gender,
        parent=parent,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"(Unknown scene: {params.scene})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.hiding not in HIDING_PLACES:
        raise StoryError(f"(Unknown hiding place: {params.hiding})")
    if params.moral not in MORALS:
        raise StoryError(f"(Unknown moral: {params.moral})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")

    scene = SCENES[params.scene]
    culprit = CULPRITS[params.culprit]
    item = ITEMS[params.item]
    hiding = HIDING_PLACES[params.hiding]
    moral = MORALS[params.moral]

    if not (culprit_can_take(culprit, item) and hiding_fits(culprit, hiding) and scene_supports(scene, hiding)):
        raise StoryError(explain_rejection(scene, culprit, item, hiding))

    world = tell(
        scene=scene,
        culprit=culprit,
        item=item,
        hiding=hiding,
        moral=moral,
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        mate_name=params.mate,
        mate_gender=params.mate_gender,
        parent_type=params.parent,
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

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0] if cases else CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (scene, culprit, item, hiding) combos:\n")
        for scene, culprit, item, hiding in combos:
            print(f"  {scene:10} {culprit:8} {item:12} {hiding}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.leader} & {p.mate}: {p.item} mystery at {p.scene} ({p.culprit} -> {p.hiding})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
