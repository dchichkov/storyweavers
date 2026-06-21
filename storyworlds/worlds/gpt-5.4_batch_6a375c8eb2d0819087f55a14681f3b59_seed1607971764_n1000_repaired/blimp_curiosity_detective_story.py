#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/blimp_curiosity_detective_story.py
=============================================================

A standalone story world about a curious child detective who solves a small
mystery with the help of a blimp. The stories are gentle detective tales for
young children: something important goes missing at a cheerful gathering, the
hero resists blaming anyone too quickly, follows physical clues, and uses a
small blimp's view from above to spot where the lost object drifted.

The world is state-driven rather than slot-filled. Typed entities accumulate
physical meters and emotional memes; simple causal rules turn those states into
story beats. A reasonableness gate keeps only plausible combinations: the lost
object must be light enough for wind to carry, the hiding place must be able to
catch it, the chosen blimp must be able to see that place, and the retrieval
method must be able to reach it.

Run it
------
    python storyworlds/worlds/gpt-5.4/blimp_curiosity_detective_story.py
    python storyworlds/worlds/gpt-5.4/blimp_curiosity_detective_story.py --setting park_fair --lost banner --spot tree_branch
    python storyworlds/worlds/gpt-5.4/blimp_curiosity_detective_story.py --spot fountain_edge
    python storyworlds/worlds/gpt-5.4/blimp_curiosity_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/blimp_curiosity_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/blimp_curiosity_detective_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/blimp_curiosity_detective_story.py --json
    python storyworlds/worlds/gpt-5.4/blimp_curiosity_detective_story.py --asp
    python storyworlds/worlds/gpt-5.4/blimp_curiosity_detective_story.py --verify
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
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Setting:
    id: str
    place: str
    event: str
    opening: str
    breeze: str
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
class LostThing:
    id: str
    label: str
    phrase: str
    material: str
    importance: str
    clue_text: str
    clue_kind: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)

    def it(self) -> str:
        return "them" if self.plural else "it"
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
    phrase: str
    catch_materials: set[str]
    visible_by: set[str]
    reachable_by: set[str]
    ground_clue: str
    ending_image: str
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
class BlimpConfig:
    id: str
    label: str
    phrase: str
    vision: str
    drift_text: str
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
class Retrieval:
    id: str
    label: str
    action_text: str
    past_text: str
    reaches: set[str]
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
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


def _r_missing_stirs_curiosity(world: World) -> list[str]:
    item = world.get("lost")
    hero = world.get("hero")
    friend = world.get("friend")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_stirs_curiosity", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["curiosity"] += 1
    hero.memes["focus"] += 1
    friend.memes["worry"] += 1
    return ["__missing__"]


def _r_clue_builds_theory(world: World) -> list[str]:
    clue = world.get("clue")
    hero = world.get("hero")
    if clue.meters["noticed"] < THRESHOLD:
        return []
    sig = ("clue_builds_theory", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["confidence"] += 1
    hero.memes["curiosity"] += 1
    world.get("case").meters["mystery"] -= 1
    return []


def _r_blimp_reveal(world: World) -> list[str]:
    blimp = world.get("blimp")
    hero = world.get("hero")
    spot = world.get("spot")
    if blimp.meters["scouting"] < THRESHOLD:
        return []
    sig = ("blimp_reveal", blimp.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    spot.meters["revealed"] += 1
    hero.memes["hope"] += 1
    world.get("case").meters["mystery"] -= 1
    return []


def _r_retrieved_resolves(world: World) -> list[str]:
    item = world.get("lost")
    hero = world.get("hero")
    friend = world.get("friend")
    if item.meters["recovered"] < THRESHOLD:
        return []
    sig = ("retrieved_resolves", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["missing"] = 0.0
    world.get("case").meters["mystery"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    friend.memes["relief"] += 1
    friend.memes["joy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_stirs_curiosity", tag="emotion", apply=_r_missing_stirs_curiosity),
    Rule(name="clue_builds_theory", tag="reasoning", apply=_r_clue_builds_theory),
    Rule(name="blimp_reveal", tag="reasoning", apply=_r_blimp_reveal),
    Rule(name="retrieved_resolves", tag="emotion", apply=_r_retrieved_resolves),
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


def can_drift_to(lost: LostThing, spot: Spot) -> bool:
    return lost.material in spot.catch_materials


def blimp_can_spot(blimp: BlimpConfig, spot: Spot) -> bool:
    return blimp.vision in spot.visible_by


def retrieval_works(retrieval: Retrieval, spot: Spot) -> bool:
    return bool(retrieval.reaches & spot.reachable_by)


def valid_combo(lost: LostThing, spot: Spot, blimp: BlimpConfig, retrieval: Retrieval) -> bool:
    return can_drift_to(lost, spot) and blimp_can_spot(blimp, spot) and retrieval_works(retrieval, spot)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for lost_id, lost in LOST_THINGS.items():
        for spot_id, spot in SPOTS.items():
            for blimp_id, blimp in BLIMPS.items():
                for retrieval_id, retrieval in RETRIEVALS.items():
                    if valid_combo(lost, spot, blimp, retrieval):
                        combos.append((lost_id, spot_id, blimp_id, retrieval_id))
    return combos


def predict_reveal(world: World) -> dict:
    sim = world.copy()
    sim.get("blimp").meters["scouting"] += 1
    propagate(sim, narrate=False)
    return {
        "revealed": sim.get("spot").meters["revealed"] >= THRESHOLD,
        "mystery": sim.get("case").meters["mystery"],
    }


def introduce(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    world.say(
        f"On the morning of {setting.event}, {hero.id} and {friend.id} reached {setting.place} early. "
        f"{setting.opening}"
    )
    world.say(
        f"{hero.id} liked mysteries, but not the kind that made people cry. "
        f"{hero.pronoun().capitalize()} liked the quiet kind, where a tiny clue could make a whole puzzle sit up straight."
    )


def show_importance(world: World, lost: LostThing) -> None:
    world.say(
        f"Near the front table rested {lost.phrase}. It mattered because {lost.importance}."
    )


def gust_and_loss(world: World, setting: Setting, lost_ent: Entity, lost: LostThing) -> None:
    lost_ent.meters["missing"] += 1
    world.get("case").meters["mystery"] += 2
    propagate(world, narrate=False)
    world.say(
        f"Then {setting.breeze}. By the time everyone looked back, {lost.label} was gone."
    )


def first_reaction(world: World, friend: Entity, hero: Entity, lost: LostThing) -> None:
    world.say(
        f'"Oh no," {friend.id} whispered. "Did somebody take {lost.it()}?"'
    )
    world.say(
        f'{hero.id} shook {hero.pronoun("possessive")} head. "Maybe," {hero.pronoun()} said, '
        f'"but a detective looks first and blames later."'
    )


def inspect_ground(world: World, hero: Entity, lost: LostThing, spot: Spot) -> None:
    clue = world.get("clue")
    clue.meters["noticed"] += 1
    world.facts["ground_clue"] = spot.ground_clue
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} crouched beside the table and looked slowly instead of rushing. "
        f"There, at the edge of the path, was {lost.clue_text}. {spot.ground_clue}"
    )


def form_theory(world: World, hero: Entity, spot: Spot) -> None:
    pred = predict_reveal(world)
    world.facts["predicted_mystery_after_scout"] = pred["mystery"]
    world.say(
        f'"That is not a stealing clue," {hero.id} murmured. "That is a drifting clue." '
        f'{hero.pronoun().capitalize()} traced the little trail with one finger and looked toward {spot.phrase}.'
    )


def scout_with_blimp(world: World, hero: Entity, blimp: BlimpConfig, spot: Spot) -> None:
    blimp_ent = world.get("blimp")
    blimp_ent.meters["scouting"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Above the booths floated {blimp.phrase}, a small blimp that {blimp.drift_text}. "
        f'{hero.id} borrowed its view for one careful sweep. On the second pass, {hero.pronoun()} saw a flutter at {spot.phrase}.'
    )


def reveal_spot(world: World, friend: Entity, lost: LostThing, spot: Spot) -> None:
    world.say(
        f'"There!" cried {friend.id}. "{lost.label.capitalize()} is caught by {spot.label}!"'
    )


def recover(world: World, grownup: Entity, retrieval: Retrieval, lost_ent: Entity, lost: LostThing) -> None:
    lost_ent.meters["recovered"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{grownup.label_word.capitalize()} came over, {retrieval.action_text}, and soon {retrieval.past_text}."
    )
    world.say(
        f"{lost.label.capitalize()} came back without a single person being blamed."
    )


def closing(world: World, hero: Entity, friend: Entity, setting: Setting, spot: Spot) -> None:
    world.say(
        f'The case was small, but {hero.id} stood a little taller. "{hero.pronoun("possessive").capitalize()} curiosity solved it," '
        f"{friend.id} said."
    )
    world.say(
        f"After that, whenever a puzzle popped up at {setting.event}, people did not start with guesses. "
        f"They started with eyes wide open. And high above them, the blimp drifted on while {spot.ending_image}."
    )


def tell(
    setting: Setting,
    lost: LostThing,
    spot: Spot,
    blimp: BlimpConfig,
    retrieval: Retrieval,
    hero_name: str = "Nora",
    hero_gender: str = "girl",
    friend_name: str = "Ben",
    friend_gender: str = "boy",
    grownup_type: str = "mother",
    trait: str = "curious",
) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait, "patient"],
        attrs={"detective_style": "gentle"},
        tags={"curiosity"},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        traits=["helpful"],
        attrs={},
    ))
    grownup = world.add(Entity(
        id="Grownup",
        kind="character",
        type=grownup_type,
        label="the grown-up",
        role="grownup",
        attrs={},
    ))
    lost_ent = world.add(Entity(
        id="lost",
        kind="thing",
        type="lost",
        label=lost.label,
        attrs={"material": lost.material},
        tags=set(lost.tags),
    ))
    spot_ent = world.add(Entity(
        id="spot",
        kind="thing",
        type="spot",
        label=spot.label,
        attrs={"place": spot.phrase},
        tags=set(spot.tags),
    ))
    clue_ent = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label="clue",
        attrs={"clue_kind": lost.clue_kind, "clue_text": lost.clue_text},
    ))
    blimp_ent = world.add(Entity(
        id="blimp",
        kind="thing",
        type="blimp",
        label=blimp.label,
        attrs={"vision": blimp.vision},
        tags=set(blimp.tags),
    ))
    world.add(Entity(
        id="case",
        kind="thing",
        type="case",
        label="the case",
        attrs={},
    ))

    world.facts.update(
        setting=setting,
        lost_cfg=lost,
        spot_cfg=spot,
        blimp_cfg=blimp,
        retrieval_cfg=retrieval,
        hero=hero,
        friend=friend,
        grownup=grownup,
        recovered=False,
        ground_clue="",
        predicted_mystery_after_scout=None,
    )

    introduce(world, hero, friend, setting)
    show_importance(world, lost)

    world.para()
    gust_and_loss(world, setting, lost_ent, lost)
    first_reaction(world, friend, hero, lost)

    world.para()
    inspect_ground(world, hero, lost, spot)
    form_theory(world, hero, spot)
    scout_with_blimp(world, hero, blimp, spot)
    reveal_spot(world, friend, lost, spot)

    world.para()
    recover(world, grownup, retrieval, lost_ent, lost)
    closing(world, hero, friend, setting, spot)

    world.facts.update(
        recovered=lost_ent.meters["recovered"] >= THRESHOLD,
        curiosity=hero.memes["curiosity"],
        mystery=world.get("case").meters["mystery"],
    )
    return world


SETTINGS = {
    "park_fair": Setting(
        id="park_fair",
        place="the park fair",
        event="the park fair",
        opening="Strings of paper stars bobbed over the booths, and the grass smelled like morning.",
        breeze="a playful wind skipped through the tents and tugged at every loose corner",
        tags={"fair", "outdoor"},
    ),
    "school_field_day": Setting(
        id="school_field_day",
        place="the school field day",
        event="field day",
        opening="Little flags lined the running lane, and the teachers were still setting out juice cups.",
        breeze="a quick breeze raced across the field and whisked the light papers into a dance",
        tags={"school", "outdoor"},
    ),
    "library_garden": Setting(
        id="library_garden",
        place="the library garden party",
        event="the library garden party",
        opening="Flower boxes sat under the windows, and a reading blanket waited near the lemonade table.",
        breeze="a gentle breeze curled around the benches and lifted the loosest things with it",
        tags={"library", "garden"},
    ),
}

LOST_THINGS = {
    "banner": LostThing(
        id="banner",
        label="the welcome banner",
        phrase="a bright welcome banner painted with stars",
        material="cloth",
        importance="it was supposed to hang over the main table before the guests arrived",
        clue_text="a small blue ribbon thread",
        clue_kind="ribbon",
        plural=False,
        tags={"banner", "cloth"},
    ),
    "map": LostThing(
        id="map",
        label="the treasure map",
        phrase="a treasure map with crayon arrows and a red X",
        material="paper",
        importance="the game could not begin until the children knew where to hunt",
        clue_text="a paper corner with a red crayon mark",
        clue_kind="paper",
        plural=False,
        tags={"map", "paper"},
    ),
    "tickets": LostThing(
        id="tickets",
        label="the game tickets",
        phrase="a roll of game tickets tied with a little string",
        material="paper",
        importance="the ring-toss booth needed them so children could take turns fairly",
        clue_text="a tiny curl of ticket paper caught beside the path",
        clue_kind="paper",
        plural=True,
        tags={"tickets", "paper"},
    ),
}

SPOTS = {
    "tree_branch": Spot(
        id="tree_branch",
        label="a low tree branch",
        phrase="the low tree branch beside the path",
        catch_materials={"cloth", "paper"},
        visible_by={"high", "low"},
        reachable_by={"ladder", "rake"},
        ground_clue="The breeze had dragged the clue in a neat little line toward the trees.",
        ending_image="the branch nodded in the breeze as if it had given the secret back",
        tags={"tree"},
    ),
    "gazebo_roof": Spot(
        id="gazebo_roof",
        label="the gazebo roof",
        phrase="the edge of the gazebo roof",
        catch_materials={"cloth", "paper"},
        visible_by={"high"},
        reachable_by={"ladder", "hook"},
        ground_clue="A faint scrape on the wooden step pointed up instead of away.",
        ending_image="sunlight slid over the roof where the mystery had been hiding",
        tags={"roof"},
    ),
    "hedge_top": Spot(
        id="hedge_top",
        label="the top of the tall hedge",
        phrase="the top of the tall hedge near the lemonade table",
        catch_materials={"paper", "cloth"},
        visible_by={"high", "low"},
        reachable_by={"rake", "hook"},
        ground_clue="A soft rustle in the leaves answered the wind like a whisper.",
        ending_image="the hedge stood fluffy and innocent again",
        tags={"hedge"},
    ),
    "fountain_edge": Spot(
        id="fountain_edge",
        label="the dry stone lip of the fountain",
        phrase="the dry stone lip of the fountain",
        catch_materials={"paper"},
        visible_by={"low"},
        reachable_by={"hook"},
        ground_clue="A damp-looking smudge on the path curved toward the fountain stones.",
        ending_image="the fountain rim gleamed quietly, no longer keeping the secret",
        tags={"fountain"},
    ),
}

BLIMPS = {
    "camera_blimp": BlimpConfig(
        id="camera_blimp",
        label="camera blimp",
        phrase="the little camera blimp",
        vision="high",
        drift_text="hummed above the crowd with a tiny lens blinking like a watchful eye",
        tags={"blimp", "camera"},
    ),
    "parade_blimp": BlimpConfig(
        id="parade_blimp",
        label="parade blimp",
        phrase="the parade blimp",
        vision="high",
        drift_text="glided slow and proud above the bunting, steady enough to notice what the ground forgot",
        tags={"blimp", "parade"},
    ),
    "toy_blimp": BlimpConfig(
        id="toy_blimp",
        label="toy blimp",
        phrase="a tethered toy blimp",
        vision="low",
        drift_text="bobbed just over the booths, close enough to peek into hedges and over fountain stone",
        tags={"blimp", "toy"},
    ),
}

RETRIEVALS = {
    "ladder": Retrieval(
        id="ladder",
        label="step ladder",
        action_text="brought a step ladder, climbed carefully",
        past_text="the missing thing was lifted down",
        reaches={"ladder"},
        tags={"ladder"},
    ),
    "rake": Retrieval(
        id="rake",
        label="garden rake",
        action_text="used a garden rake with very gentle hands",
        past_text="the missing thing was nudged loose and caught before it fell",
        reaches={"rake"},
        tags={"rake"},
    ),
    "hook": Retrieval(
        id="hook",
        label="umbrella hook",
        action_text="turned an umbrella by the handle and reached with the curved hook",
        past_text="the missing thing was hooked safely and brought back",
        reaches={"hook"},
        tags={"hook"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Ben", "Theo", "Sam", "Leo", "Finn", "Jack", "Noah", "Max"]
TRAITS = ["curious", "careful", "observant", "patient"]


@dataclass
class StoryParams:
    setting: str
    lost: str
    spot: str
    blimp: str
    retrieval: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    grownup: str
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


CURATED = [
    StoryParams(
        setting="park_fair",
        lost="banner",
        spot="tree_branch",
        blimp="parade_blimp",
        retrieval="ladder",
        hero="Nora",
        hero_gender="girl",
        friend="Ben",
        friend_gender="boy",
        grownup="mother",
        trait="curious",
    ),
    StoryParams(
        setting="school_field_day",
        lost="map",
        spot="gazebo_roof",
        blimp="camera_blimp",
        retrieval="hook",
        hero="Theo",
        hero_gender="boy",
        friend="Mia",
        friend_gender="girl",
        grownup="father",
        trait="observant",
    ),
    StoryParams(
        setting="library_garden",
        lost="tickets",
        spot="hedge_top",
        blimp="toy_blimp",
        retrieval="rake",
        hero="Lucy",
        hero_gender="girl",
        friend="Sam",
        friend_gender="boy",
        grownup="mother",
        trait="patient",
    ),
    StoryParams(
        setting="park_fair",
        lost="map",
        spot="fountain_edge",
        blimp="toy_blimp",
        retrieval="hook",
        hero="Leo",
        hero_gender="boy",
        friend="Ava",
        friend_gender="girl",
        grownup="father",
        trait="careful",
    ),
]


KNOWLEDGE = {
    "blimp": [
        (
            "What is a blimp?",
            "A blimp is a big balloon-shaped airship that floats in the sky. It can move slowly and look down on things from above.",
        )
    ],
    "curiosity": [
        (
            "What does curiosity mean?",
            "Curiosity means wanting to know more and looking closely to learn the truth. It helps people ask good questions instead of making wild guesses.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective notices clues, asks careful questions, and tries to find out what really happened. A good detective does not blame someone before checking the facts.",
        )
    ],
    "paper": [
        (
            "Why can paper blow away?",
            "Paper is light, so wind can lift it and push it along. That is why papers need to be held down on breezy days.",
        )
    ],
    "cloth": [
        (
            "Why can a cloth banner get caught in a branch?",
            "A cloth banner is light and floppy, so wind can carry it and a branch can snag it. The cloth may hang there until someone reaches it carefully.",
        )
    ],
    "ladder": [
        (
            "What is a ladder for?",
            "A ladder helps a person reach something higher than their hands can go. Grown-ups use it carefully to climb up and bring things down.",
        )
    ],
    "rake": [
        (
            "How can a rake help get something out of a hedge?",
            "A rake has long reach, so a grown-up can gently pull a light object loose from leaves or branches. It should be used carefully so the object does not tear.",
        )
    ],
    "hook": [
        (
            "Why does a hook help reach something?",
            "A hook can catch a string, corner, or edge that hands cannot reach. That makes it useful for pulling a light thing back safely.",
        )
    ],
    "tree": [
        (
            "Why do things get stuck in tree branches?",
            "Branches have little forks and twigs that can catch light things carried by the wind. Once something snags there, it may stay put until someone gets it down.",
        )
    ],
    "roof": [
        (
            "Why is a roof easier to see from above?",
            "A roof is high and flat, so it can be hard to see from the ground but easier from above. Looking from a new angle can reveal what was hidden before.",
        )
    ],
    "hedge": [
        (
            "Why can a hedge hide things?",
            "A hedge is thick with leaves, so a light object can sit on top or slip between branches. From the ground it may look like ordinary green leaves.",
        )
    ],
    "fountain": [
        (
            "Why might something light stop at the edge of a fountain?",
            "A stone edge can block a drifting paper and keep it from moving farther. The object may rest there until someone notices it.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "blimp",
    "curiosity",
    "detective",
    "paper",
    "cloth",
    "ladder",
    "rake",
    "hook",
    "tree",
    "roof",
    "hedge",
    "fountain",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    lost = f["lost_cfg"]
    setting = f["setting"]
    blimp = f["blimp_cfg"]
    return [
        f'Write a gentle detective story for a 3-to-5-year-old that includes the word "blimp" and follows a curious child solving a missing-object mystery at {setting.place}.',
        f"Tell a small detective story where {hero.id} notices clues, uses {blimp.phrase} to look from above, and finds {lost.label} without blaming anyone too quickly.",
        f"Write a child-facing mystery about curiosity, wind, and careful clue-following, ending with a happy recovery and a detective-like lesson.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    grownup = f["grownup"]
    setting = f["setting"]
    lost = f["lost_cfg"]
    spot = f["spot_cfg"]
    blimp = f["blimp_cfg"]
    retrieval = f["retrieval_cfg"]
    clue = f.get("ground_clue", "")
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a curious child who likes gentle detective work, and {friend.id}, who helps with the case. They are at {setting.place} when {lost.label} goes missing.",
        ),
        (
            f"What went missing, and why did it matter?",
            f"{lost.label.capitalize()} went missing. It mattered because {lost.importance}.",
        ),
        (
            "Why did the hero not blame anyone right away?",
            f"{hero.id} wanted the truth, not a quick guess. {hero.pronoun().capitalize()} knew a detective should look for clues first so nobody gets blamed unfairly.",
        ),
        (
            "What clue helped the detective?",
            f"{hero.id} found {lost.clue_text}. {clue}",
        ),
        (
            "How did the blimp help solve the mystery?",
            f"{blimp.phrase.capitalize()} gave {hero.id} a better view from above. From that new angle, {hero.pronoun()} could see that the missing thing had drifted to {spot.phrase}.",
        ),
        (
            f"How did the grown-up get {lost.label} back?",
            f"{grownup.label_word.capitalize()} {retrieval.action_text}, and {retrieval.past_text}. That worked because {retrieval.label} could reach {spot.label}.",
        ),
        (
            "How did the story end?",
            f"It ended happily, with {lost.label} returned and nobody blamed. The ending shows that curiosity and careful looking solved the little case.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lost = f["lost_cfg"]
    spot = f["spot_cfg"]
    retrieval = f["retrieval_cfg"]
    tags = {"blimp", "curiosity", "detective"} | set(lost.tags) | set(spot.tags) | set(retrieval.tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(lost: LostThing, spot: Spot, blimp: BlimpConfig, retrieval: Retrieval) -> str:
    if not can_drift_to(lost, spot):
        return (
            f"(No story: {lost.label} is {lost.material}, but {spot.label} is not a plausible place for wind to catch that material. "
            f"A detective story needs a believable trail, not a random hiding place.)"
        )
    if not blimp_can_spot(blimp, spot):
        return (
            f"(No story: {blimp.label} cannot honestly see {spot.label} from its usual angle. "
            f"The blimp must reveal a clue the ground view would miss.)"
        )
    if not retrieval_works(retrieval, spot):
        return (
            f"(No story: {retrieval.label} would not reach {spot.label}. "
            f"The recovery method must be able to get the missing thing back.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
drift_ok(L, S) :- lost(L), spot(S), material(L, M), catches(S, M).
spot_ok(B, S)  :- blimp(B), spot(S), vision(B, V), visible_by(S, V).
reach_ok(R, S) :- retrieval(R), spot(S), needs_reach(S, Need), reaches(R, Need).
valid(L, S, B, R) :- drift_ok(L, S), spot_ok(B, S), reach_ok(R, S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for lid, lost in LOST_THINGS.items():
        lines.append(asp.fact("lost", lid))
        lines.append(asp.fact("material", lid, lost.material))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        for mat in sorted(spot.catch_materials):
            lines.append(asp.fact("catches", sid, mat))
        for vis in sorted(spot.visible_by):
            lines.append(asp.fact("visible_by", sid, vis))
        for need in sorted(spot.reachable_by):
            lines.append(asp.fact("needs_reach", sid, need))
    for bid, blimp in BLIMPS.items():
        lines.append(asp.fact("blimp", bid))
        lines.append(asp.fact("vision", bid, blimp.vision))
    for rid, retrieval in RETRIEVALS.items():
        lines.append(asp.fact("retrieval", rid))
        for reach in sorted(retrieval.reaches):
            lines.append(asp.fact("reaches", rid, reach))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
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
            raise StoryError("(verify) smoke test produced an empty story")
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("(verify) smoke test produced incomplete QA/prompts")
        print("OK: smoke test generate() succeeded on a curated scenario.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a curious child detective solves a tiny mystery with a blimp."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--lost", choices=LOST_THINGS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--blimp", choices=BLIMPS)
    ap.add_argument("--retrieval", choices=RETRIEVALS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.lost and args.spot and args.blimp and args.retrieval:
        lost = LOST_THINGS[args.lost]
        spot = SPOTS[args.spot]
        blimp = BLIMPS[args.blimp]
        retrieval = RETRIEVALS[args.retrieval]
        if not valid_combo(lost, spot, blimp, retrieval):
            raise StoryError(explain_rejection(lost, spot, blimp, retrieval))

    combos = [
        combo for combo in valid_combos()
        if (args.lost is None or combo[0] == args.lost)
        and (args.spot is None or combo[1] == args.spot)
        and (args.blimp is None or combo[2] == args.blimp)
        and (args.retrieval is None or combo[3] == args.retrieval)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    lost_id, spot_id, blimp_id, retrieval_id = rng.choice(sorted(combos))
    setting = args.setting or rng.choice(sorted(SETTINGS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=hero)
    grownup = args.grownup or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        setting=setting,
        lost=lost_id,
        spot=spot_id,
        blimp=blimp_id,
        retrieval=retrieval_id,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        grownup=grownup,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.lost not in LOST_THINGS:
        raise StoryError(f"(Invalid lost item: {params.lost})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Invalid spot: {params.spot})")
    if params.blimp not in BLIMPS:
        raise StoryError(f"(Invalid blimp: {params.blimp})")
    if params.retrieval not in RETRIEVALS:
        raise StoryError(f"(Invalid retrieval: {params.retrieval})")

    lost = LOST_THINGS[params.lost]
    spot = SPOTS[params.spot]
    blimp = BLIMPS[params.blimp]
    retrieval = RETRIEVALS[params.retrieval]
    if not valid_combo(lost, spot, blimp, retrieval):
        raise StoryError(explain_rejection(lost, spot, blimp, retrieval))

    world = tell(
        setting=SETTINGS[params.setting],
        lost=lost,
        spot=spot,
        blimp=blimp,
        retrieval=retrieval,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        grownup_type=params.grownup,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (lost, spot, blimp, retrieval) combos:\n")
        for lost, spot, blimp, retrieval in combos:
            print(f"  {lost:8} {spot:13} {blimp:12} {retrieval}")
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
            header = f"### {p.hero}: {p.lost} at {p.setting} ({p.spot}, {p.blimp}, {p.retrieval})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
