#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bronchitis_lever_transformation_detective_story.py
==============================================================================

A standalone storyworld for a gentle detective-story mystery built around
transformation. A child detective thinks a small creature has been stolen after
it vanishes from a display, but the "crime" is solved when a lever reveals the
creature in a new form. A caretaker's rough cough from bronchitis creates a
misleading clue, so the story also teaches that one clue is not enough to blame
someone.

Run it
------
    python storyworlds/worlds/gpt-5.4/bronchitis_lever_transformation_detective_story.py
    python storyworlds/worlds/gpt-5.4/bronchitis_lever_transformation_detective_story.py --place greenhouse --creature monarch --lever shade_lever
    python storyworlds/worlds/gpt-5.4/bronchitis_lever_transformation_detective_story.py --place classroom --creature treefrog
    python storyworlds/worlds/gpt-5.4/bronchitis_lever_transformation_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/bronchitis_lever_transformation_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/bronchitis_lever_transformation_detective_story.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    intro: str
    clue_spot: str
    reveal_spot: str
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
class CreatureCfg:
    id: str
    family: str
    start_label: str
    hidden_label: str
    final_label: str
    sign_text: str
    reveal_line: str
    ending_image: str
    food_or_home: str
    knowledge_tag: str
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
class LeverCfg:
    id: str
    label: str
    action: str
    reveal_text: str
    families: set[str] = field(default_factory=set)
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_transform(world: World) -> list[str]:
    creature = world.get("creature")
    place = world.get("place")
    sig = ("transform", creature.id)
    if sig in world.fired:
        return []
    if creature.meters["ready"] < THRESHOLD:
        return []
    if creature.attrs.get("family") not in place.attrs.get("affords", set()):
        return []
    world.fired.add(sig)
    creature.meters["transformed"] += 1
    creature.meters["hidden"] += 1
    creature.attrs["stage"] = creature.attrs["hidden_label"]
    creature.attrs["visible_label"] = creature.attrs["hidden_label"]
    return ["__transform__"]


def _r_suspicion(world: World) -> list[str]:
    detective = world.get("detective")
    caretaker = world.get("caretaker")
    sig = ("suspicion", detective.id)
    if sig in world.fired:
        return []
    if caretaker.meters["coughing"] < THRESHOLD:
        return []
    if world.facts.get("case_opened") is not True:
        return []
    world.fired.add(sig)
    detective.memes["suspicion"] += 1
    detective.memes["worry"] += 1
    return ["__suspicion__"]


def _r_reveal(world: World) -> list[str]:
    creature = world.get("creature")
    lever = world.get("lever")
    detective = world.get("detective")
    sig = ("reveal", creature.id)
    if sig in world.fired:
        return []
    if lever.meters["pulled"] < THRESHOLD:
        return []
    if creature.meters["hidden"] < THRESHOLD:
        return []
    if creature.attrs.get("family") not in lever.attrs.get("families", set()):
        return []
    world.fired.add(sig)
    creature.meters["hidden"] = 0.0
    creature.meters["visible"] += 1
    detective.memes["relief"] += 1
    detective.memes["insight"] += 1
    return ["__reveal__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="transform", tag="physical", apply=_r_transform),
    Rule(name="suspicion", tag="social", apply=_r_suspicion),
    Rule(name="reveal", tag="physical", apply=_r_reveal),
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
            if not line.startswith("__"):
                world.say(line)
    return produced


PLACES = {
    "greenhouse": Place(
        id="greenhouse",
        label="the town greenhouse",
        intro="Glass panes glittered over rows of leaves, and every bench looked as if it might be hiding a clue.",
        clue_spot="a milkweed stand by the warm window",
        reveal_spot="the sun shelf above the milkweed stand",
        affords={"butterfly", "frog"},
        tags={"greenhouse"},
    ),
    "classroom": Place(
        id="classroom",
        label="the school science room",
        intro="Jars, charts, and magnifying glasses made the room feel like a tiny detective office.",
        clue_spot="the science table under the bulletin board",
        reveal_spot="the tall display shelf by the lamp",
        affords={"butterfly"},
        tags={"classroom"},
    ),
    "pondhouse": Place(
        id="pondhouse",
        label="the little pond house",
        intro="The wooden room smelled of pond water and reeds, and the shadows under the beams seemed full of secrets.",
        clue_spot="a shallow tank beside the reeds",
        reveal_spot="the damp ledge above the tank",
        affords={"frog"},
        tags={"pond"},
    ),
}

CREATURES = {
    "monarch": CreatureCfg(
        id="monarch",
        family="butterfly",
        start_label="striped caterpillar",
        hidden_label="jade chrysalis",
        final_label="orange butterfly",
        sign_text="a tiny shed caterpillar skin and a silk button no bigger than a pinhead",
        reveal_line="hanging perfectly still, as neat as a secret wrapped in green silk",
        ending_image="By the end of the afternoon, the new orange butterfly opened and closed its wings like a tiny, solved flag.",
        food_or_home="milkweed leaves",
        knowledge_tag="chrysalis",
        tags={"butterfly", "chrysalis"},
    ),
    "swallowtail": CreatureCfg(
        id="swallowtail",
        family="butterfly",
        start_label="plump green caterpillar",
        hidden_label="speckled chrysalis",
        final_label="yellow butterfly",
        sign_text="a curled bit of old caterpillar skin and a small silk thread on the stem",
        reveal_line="hooked to the stem, quiet and sure, already becoming something new",
        ending_image="Soon the yellow butterfly rested in the light, opening its wings as if the case itself had learned to smile.",
        food_or_home="fennel sprigs",
        knowledge_tag="chrysalis",
        tags={"butterfly", "chrysalis"},
    ),
    "treefrog": CreatureCfg(
        id="treefrog",
        family="frog",
        start_label="round tadpole",
        hidden_label="tiny froglet",
        final_label="little tree frog",
        sign_text="a split tadpole skin near the waterline and two prints no bigger than raindrops",
        reveal_line="crouched on the damp ledge, with new little legs and bright watchful eyes",
        ending_image="At sunset, the little tree frog gave one brave hop onto a reed, and everyone could see the mystery had changed into a beginning.",
        food_or_home="the shallow tank",
        knowledge_tag="froglet",
        tags={"frog", "froglet"},
    ),
}

LEVERS = {
    "shade_lever": LeverCfg(
        id="shade_lever",
        label="the brass shade lever",
        action="pulled the brass shade lever",
        reveal_text="The cloth shade rolled up with a soft whisk, and warm light spilled over the upper shelf.",
        families={"butterfly"},
        tags={"lever", "shade"},
    ),
    "panel_lever": LeverCfg(
        id="panel_lever",
        label="the oak panel lever",
        action="pressed down the oak panel lever",
        reveal_text="A hidden panel swung open with a click, showing the space behind the display.",
        families={"butterfly", "frog"},
        tags={"lever", "panel"},
    ),
    "mist_lever": LeverCfg(
        id="mist_lever",
        label="the iron mist lever",
        action="pushed the iron mist lever",
        reveal_text="The mist pipes sighed awake, and the damp ledge above the tank gleamed softly.",
        families={"frog"},
        tags={"lever", "mist"},
    ),
}

GIRL_NAMES = ["Lila", "Mira", "Tess", "Nora", "Ivy", "June", "Clara", "Eva"]
BOY_NAMES = ["Theo", "Milo", "Ben", "Owen", "Finn", "Eli", "Jude", "Max"]
HELPER_TRAITS = ["careful", "sharp-eyed", "patient", "curious", "calm"]


def valid_combo(place_id: str, creature_id: str, lever_id: str) -> bool:
    place = PLACES[place_id]
    creature = CREATURES[creature_id]
    lever = LEVERS[lever_id]
    return creature.family in place.affords and creature.family in lever.families


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id in sorted(PLACES):
        for creature_id in sorted(CREATURES):
            for lever_id in sorted(LEVERS):
                if valid_combo(place_id, creature_id, lever_id):
                    out.append((place_id, creature_id, lever_id))
    return out


def hidden_form(creature_id: str) -> str:
    family = CREATURES[creature_id].family
    return "chrysalis" if family == "butterfly" else "froglet"


@dataclass
class StoryParams:
    place: str
    creature: str
    lever: str
    detective: str
    detective_gender: str
    friend: str
    friend_gender: str
    caretaker_name: str
    caretaker_gender: str
    helper_trait: str
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


def explain_rejection(place_id: str, creature_id: str, lever_id: Optional[str] = None) -> str:
    place = PLACES[place_id]
    creature = CREATURES[creature_id]
    if creature.family not in place.affords:
        return (
            f"(No story: {place.label} is not a good home for a {creature.family} case, "
            f"so {creature.start_label} cannot reasonably transform there.)"
        )
    if lever_id is not None and creature.family not in LEVERS[lever_id].families:
        return (
            f"(No story: {LEVERS[lever_id].label} would not reveal a {creature.family} clue. "
            f"Pick a lever that can uncover where the transformed creature is hiding.)"
        )
    return "(No story: that combination does not fit this mystery.)"


def introduce(world: World, detective: Entity, friend: Entity, place: Place, creature: CreatureCfg) -> None:
    world.say(
        f"{detective.id} liked mysteries so much that even a quiet visit to {place.label} felt like the start of a detective story."
    )
    world.say(
        f"That morning, {detective.pronoun()} and {friend.id} came to see a {creature.start_label} that had been eating {creature.food_or_home} at {place.clue_spot}."
    )
    world.say(place.intro)


def meet_caretaker(world: World, caretaker: Entity) -> None:
    world.say(
        f"{caretaker.id}, the caretaker, greeted them with a scarf around {caretaker.pronoun('possessive')} neck."
    )
    world.say(
        f'"I have bronchitis," {caretaker.pronoun()} explained after a rough cough. "So if I sound like a rusty trumpet, that is the reason."'
    )


def open_case(world: World, detective: Entity, friend: Entity, creature: CreatureCfg, place: Place) -> None:
    world.facts["case_opened"] = True
    propagate(world, narrate=False)
    detective.memes["focus"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"When they reached {place.clue_spot}, the {creature.start_label} was gone."
    )
    world.say(
        f'Only an empty stem remained. "{detective.id}," whispered {friend.id}, "this looks like a real case."'
    )


def wrong_suspicion(world: World, detective: Entity, caretaker: Entity) -> None:
    propagate(world, narrate=False)
    if detective.memes["suspicion"] >= THRESHOLD:
        world.say(
            f"Just then {caretaker.id} coughed again in the next aisle, and for one quick second {detective.id} wondered if the caretaker had moved the little creature."
        )
        world.say(
            f"The cough sounded important, but {detective.id} knew a detective had to test a clue before trusting it."
        )


def inspect_clues(world: World, detective: Entity, friend: Entity, creature: CreatureCfg, place: Place) -> None:
    detective.memes["insight"] += 1
    friend.memes["hope"] += 1
    world.say(
        f"{detective.id} knelt by the stem and found {creature.sign_text}."
    )
    if creature.family == "butterfly":
        world.say(
            f'"Not stolen," {detective.pronoun()} murmured. "A caterpillar can change. If it transformed, it would leave a clue and hang somewhere safe and still."'
        )
    else:
        world.say(
            f'"Not stolen," {detective.pronoun()} murmured. "A tadpole can change too. If it transformed, it would climb toward a damp place where little new legs could rest."'
        )
    world.say(
        f"{friend.id}'s eyes grew round. The case was turning from a theft into a puzzle about transformation."
    )


def test_lever(world: World, detective: Entity, lever: LeverCfg, place: Place) -> None:
    lever_ent = world.get("lever")
    lever_ent.meters["pulled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{detective.id} looked from the clue spot to {lever.label} and then {lever.action}."
    )
    world.say(lever.reveal_text)
    world.say(
        f"There, at {place.reveal_spot}, was the missing creature in its new form."
    )


def reveal_solution(world: World, detective: Entity, friend: Entity, caretaker: Entity, creature: CreatureCfg) -> None:
    world.say(
        f"It was {creature.reveal_line}."
    )
    world.say(
        f'"Case solved," said {detective.id}. "Nobody took it. It changed."'
    )
    world.say(
        f"{caretaker.id} smiled between coughs. {caretaker.pronoun().capitalize()} had not hidden anything at all; the bronchitis cough had only been a noisy, confusing clue."
    )
    world.say(
        f"{friend.id} laughed with relief, and even {detective.id} had to grin. The best answer was stranger and kinder than the first guess."
    )


def ending(world: World, detective: Entity, friend: Entity, creature: CreatureCfg) -> None:
    detective.memes["relief"] += 1
    friend.memes["joy"] += 1
    detective.memes["lesson"] += 1
    world.say(
        f"Before they left, {detective.id} wrote one neat line in a little notebook: Do not blame a person for one loud clue."
    )
    world.say(
        creature.ending_image
    )
    world.say(
        f"{detective.id} and {friend.id} walked home feeling as if they had solved a mystery and watched a tiny miracle at the same time."
    )


def tell(
    place: Place,
    creature_cfg: CreatureCfg,
    lever_cfg: LeverCfg,
    detective_name: str = "Lila",
    detective_gender: str = "girl",
    friend_name: str = "Theo",
    friend_gender: str = "boy",
    caretaker_name: str = "Mr. Vale",
    caretaker_gender: str = "man",
    helper_trait: str = "careful",
) -> World:
    world = World(place=place)

    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        role="detective",
        label=detective_name,
        attrs={"trait": helper_trait},
        tags={"detective"},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        label=friend_name,
        attrs={},
        tags={"friend"},
    ))
    caretaker = world.add(Entity(
        id=caretaker_name,
        kind="character",
        type=caretaker_gender,
        role="caretaker",
        label="the caretaker",
        attrs={"condition": "bronchitis"},
        tags={"bronchitis"},
    ))
    place_ent = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=place.label,
        attrs={"affords": set(place.affords)},
        tags=set(place.tags),
    ))
    lever = world.add(Entity(
        id="lever",
        kind="thing",
        type="lever",
        label=lever_cfg.label,
        attrs={"families": set(lever_cfg.families), "id": lever_cfg.id},
        tags=set(lever_cfg.tags),
    ))
    creature = world.add(Entity(
        id="creature",
        kind="thing",
        type=creature_cfg.family,
        label=creature_cfg.start_label,
        attrs={
            "family": creature_cfg.family,
            "stage": creature_cfg.start_label,
            "start_label": creature_cfg.start_label,
            "hidden_label": creature_cfg.hidden_label,
            "final_label": creature_cfg.final_label,
            "visible_label": creature_cfg.start_label,
        },
        tags=set(creature_cfg.tags),
    ))

    detective.memes["curiosity"] = 1.0
    friend.memes["trust"] = 1.0
    caretaker.meters["coughing"] = 1.0
    creature.meters["ready"] = 1.0

    introduce(world, detective, friend, place, creature_cfg)
    meet_caretaker(world, caretaker)

    world.para()
    open_case(world, detective, friend, creature_cfg, place)
    wrong_suspicion(world, detective, caretaker)
    inspect_clues(world, detective, friend, creature_cfg, place)

    world.para()
    test_lever(world, detective, lever_cfg, place)
    reveal_solution(world, detective, friend, caretaker, creature_cfg)

    world.para()
    ending(world, detective, friend, creature_cfg)

    world.facts.update(
        detective=detective,
        friend=friend,
        caretaker=caretaker,
        place_cfg=place,
        creature_cfg=creature_cfg,
        lever_cfg=lever_cfg,
        transformed=creature.meters["transformed"] >= THRESHOLD,
        revealed=creature.meters["visible"] >= THRESHOLD,
        hidden_form=creature_cfg.hidden_label,
        final_form=creature_cfg.final_label,
        case_kind="transformation",
        wrong_suspect=detective.memes["suspicion"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "bronchitis": [
        (
            "What is bronchitis?",
            "Bronchitis is an illness that makes the tubes in your chest sore and swollen, so a person may cough a lot. A cough from bronchitis can sound loud, but it does not mean the person did something wrong."
        )
    ],
    "lever": [
        (
            "What is a lever?",
            "A lever is a handle or bar that helps you move something with a push or pull. People use levers to lift, open, or turn parts of a machine."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and asks careful questions to solve a mystery. A good detective does not decide too fast from only one clue."
        )
    ],
    "chrysalis": [
        (
            "What is a chrysalis?",
            "A chrysalis is the quiet case around a caterpillar while it changes into a butterfly. From the outside it looks still, but inside a big transformation is happening."
        )
    ],
    "froglet": [
        (
            "What is a froglet?",
            "A froglet is a young frog that has just changed from a tadpole. It is partway through its transformation and often still very small."
        )
    ],
    "butterfly": [
        (
            "How does a caterpillar become a butterfly?",
            "First the caterpillar grows, and then it makes a chrysalis. After the transformation inside is finished, a butterfly comes out."
        )
    ],
    "frog": [
        (
            "How does a tadpole become a frog?",
            "A tadpole slowly grows legs and lungs and changes shape over time. When the transformation is far enough along, it becomes a little frog."
        )
    ],
    "clue": [
        (
            "Why can one clue be misleading?",
            "One clue may point in the wrong direction if you do not check it with other facts. That is why careful thinkers look for more than one sign before blaming someone."
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "clue", "bronchitis", "lever", "chrysalis", "butterfly", "froglet", "frog"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    creature = f["creature_cfg"]
    place = f["place_cfg"]
    lever = f["lever_cfg"]
    return [
        f'Write a gentle detective story for a 3-to-5-year-old that includes the words "bronchitis" and "lever" and ends with a transformation instead of a theft.',
        f"Tell a child-friendly mystery where {detective.id} visits {place.label}, thinks a {creature.start_label} has vanished, and solves the case by using {lever.label}.",
        f"Write a tiny detective story where a rough cough creates the wrong suspicion, but the real answer is that the missing creature changed into {creature.hidden_label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    friend = f["friend"]
    caretaker = f["caretaker"]
    creature = f["creature_cfg"]
    place = f["place_cfg"]
    lever = f["lever_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child who loves mysteries, {friend.id}, and the caretaker at {place.label}. Together they try to solve why a {creature.start_label} disappeared."
        ),
        (
            f"What was the mystery at {place.label}?",
            f"The mystery was that the {creature.start_label} was gone from {place.clue_spot}. At first it looked like a theft, because the creature had vanished and the case opened suddenly."
        ),
        (
            f"Why did {detective.id} briefly suspect the caretaker?",
            f"{caretaker.id} coughed nearby, and the cough from bronchitis sounded like an important clue. But that was only one clue, so it was not enough to prove the caretaker had done anything."
        ),
        (
            f"How did {detective.id} solve the case?",
            f"{detective.id} studied the little signs left behind and realized they matched a transformation, not a kidnapping. Then {detective.pronoun()} used {lever.label}, which revealed the missing creature in its new form."
        ),
        (
            "What was the real answer to the mystery?",
            f"The creature had changed into {creature.hidden_label} and was hiding in plain sight. The case was solved when everyone understood that the disappearance was really part of a transformation."
        ),
        (
            "What lesson did the detective learn?",
            f"{detective.id} learned not to blame a person for one loud clue. The story shows that careful thinking means checking signs and being fair before making a guess."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    creature = f["creature_cfg"]
    tags = {"detective", "clue", "bronchitis", "lever", creature.knowledge_tag}
    if creature.family == "butterfly":
        tags.add("butterfly")
    if creature.family == "frog":
        tags.add("frog")
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
            shown = {
                k: (sorted(v) if isinstance(v, set) else v)
                for k, v in ent.attrs.items()
                if v not in ("", None, [], {})
            }
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,L) :- place(P), creature(C), lever(L), affords(P,F), family(C,F), reveals(L,F).

hidden_form(C,chrysalis) :- family(C,butterfly).
hidden_form(C,froglet)   :- family(C,frog).

#show valid/3.
#show hidden_form/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for family in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, family))
    for creature_id, creature in CREATURES.items():
        lines.append(asp.fact("creature", creature_id))
        lines.append(asp.fact("family", creature_id, creature.family))
    for lever_id, lever in LEVERS.items():
        lines.append(asp.fact("lever", lever_id))
        for family in sorted(lever.families):
            lines.append(asp.fact("reveals", lever_id, family))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_hidden_forms() -> dict[str, str]:
    import asp

    model = asp.one_model(asp_program())
    return {creature: form for creature, form in asp.atoms(model, "hidden_form")}


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos() matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in asp:", sorted(asp_valid - py_valid))

    py_forms = {cid: hidden_form(cid) for cid in CREATURES}
    asp_forms = asp_hidden_forms()
    if py_forms == asp_forms:
        print(f"OK: hidden-form mapping matches ASP ({len(py_forms)} creatures).")
    else:
        rc = 1
        print("MISMATCH in hidden forms:")
        print("  python:", py_forms)
        print("  asp:   ", asp_forms)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("default-resolve smoke test generated an empty story")
        print("OK: default resolve/generate smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


CURATED = [
    StoryParams(
        place="greenhouse",
        creature="monarch",
        lever="shade_lever",
        detective="Lila",
        detective_gender="girl",
        friend="Theo",
        friend_gender="boy",
        caretaker_name="Mr. Vale",
        caretaker_gender="man",
        helper_trait="careful",
    ),
    StoryParams(
        place="classroom",
        creature="swallowtail",
        lever="panel_lever",
        detective="Mira",
        detective_gender="girl",
        friend="Ben",
        friend_gender="boy",
        caretaker_name="Ms. Rowan",
        caretaker_gender="woman",
        helper_trait="sharp-eyed",
    ),
    StoryParams(
        place="pondhouse",
        creature="treefrog",
        lever="mist_lever",
        detective="Owen",
        detective_gender="boy",
        friend="Ivy",
        friend_gender="girl",
        caretaker_name="Mr. Fen",
        caretaker_gender="man",
        helper_trait="patient",
    ),
    StoryParams(
        place="greenhouse",
        creature="treefrog",
        lever="panel_lever",
        detective="June",
        detective_gender="girl",
        friend="Max",
        friend_gender="boy",
        caretaker_name="Ms. Vale",
        caretaker_gender="woman",
        helper_trait="curious",
    ),
    StoryParams(
        place="greenhouse",
        creature="swallowtail",
        lever="shade_lever",
        detective="Finn",
        detective_gender="boy",
        friend="Clara",
        friend_gender="girl",
        caretaker_name="Mr. Reed",
        caretaker_gender="man",
        helper_trait="calm",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle detective-story world: a missing creature, a misleading cough, a lever, and a transformation."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--creature", choices=sorted(CREATURES))
    ap.add_argument("--lever", choices=sorted(LEVERS))
    ap.add_argument("--detective")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker-name")
    ap.add_argument("--caretaker-gender", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and question sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, creature, lever) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.creature and not valid_combo(args.place, args.creature, args.lever or next(iter(LEVERS))):
        if args.lever:
            raise StoryError(explain_rejection(args.place, args.creature, args.lever))
        place = PLACES[args.place]
        creature = CREATURES[args.creature]
        if creature.family not in place.affords:
            raise StoryError(explain_rejection(args.place, args.creature))
    if args.place and args.creature and args.lever and not valid_combo(args.place, args.creature, args.lever):
        raise StoryError(explain_rejection(args.place, args.creature, args.lever))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.creature is None or combo[1] == args.creature)
        and (args.lever is None or combo[2] == args.lever)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, creature_id, lever_id = rng.choice(sorted(combos))
    detective_gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    detective_name = args.detective or _pick_name(rng, detective_gender)
    friend_name = args.friend or _pick_name(rng, friend_gender, avoid=detective_name)
    caretaker_gender = args.caretaker_gender or rng.choice(["woman", "man"])
    if args.caretaker_name:
        caretaker_name = args.caretaker_name
    else:
        caretaker_name = rng.choice(["Ms. Vale", "Mr. Vale", "Ms. Rowan", "Mr. Fen", "Ms. Reed", "Mr. Reed"])
        if caretaker_gender == "woman" and caretaker_name.startswith("Mr. "):
            caretaker_name = caretaker_name.replace("Mr. ", "Ms. ", 1)
        if caretaker_gender == "man" and caretaker_name.startswith("Ms. "):
            caretaker_name = caretaker_name.replace("Ms. ", "Mr. ", 1)
    helper_trait = rng.choice(HELPER_TRAITS)
    return StoryParams(
        place=place_id,
        creature=creature_id,
        lever=lever_id,
        detective=detective_name,
        detective_gender=detective_gender,
        friend=friend_name,
        friend_gender=friend_gender,
        caretaker_name=caretaker_name,
        caretaker_gender=caretaker_gender,
        helper_trait=helper_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.lever not in LEVERS:
        raise StoryError(f"(Unknown lever: {params.lever})")
    if not valid_combo(params.place, params.creature, params.lever):
        raise StoryError(explain_rejection(params.place, params.creature, params.lever))

    world = tell(
        place=PLACES[params.place],
        creature_cfg=CREATURES[params.creature],
        lever_cfg=LEVERS[params.lever],
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        caretaker_name=params.caretaker_name,
        caretaker_gender=params.caretaker_gender,
        helper_trait=params.helper_trait,
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
        print(f"{len(combos)} compatible (place, creature, lever) combos:\n")
        for place_id, creature_id, lever_id in combos:
            print(f"  {place_id:10} {creature_id:11} {lever_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective}: {p.creature} at {p.place} with {p.lever}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
