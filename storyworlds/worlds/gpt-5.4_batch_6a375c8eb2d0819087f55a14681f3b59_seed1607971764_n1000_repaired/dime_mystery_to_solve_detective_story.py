#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dime_mystery_to_solve_detective_story.py
===================================================================

A standalone story world for a tiny child-facing detective story: a missing
dime, a small physical mystery, and a careful child who solves it by following
real clues instead of wild guesses.

The world rebuilds a simple premise in simulation form:

- a child brings a dime for a treat or machine,
- the dime vanishes from sight,
- a clue appears because of how the dime physically moved,
- the child investigates with a helper,
- the dime is found in a satisfying place,
- the ending image proves the child learned to look closely before blaming anyone.

Run it
------
    python storyworlds/worlds/gpt-5.4/dime_mystery_to_solve_detective_story.py
    python storyworlds/worlds/gpt-5.4/dime_mystery_to_solve_detective_story.py --scene picnic --cause sticky
    python storyworlds/worlds/gpt-5.4/dime_mystery_to_solve_detective_story.py --scene porch --cause rolled
    python storyworlds/worlds/gpt-5.4/dime_mystery_to_solve_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/dime_mystery_to_solve_detective_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/dime_mystery_to_solve_detective_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/dime_mystery_to_solve_detective_story.py --verify
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
NOTICE_MIN = 1.0


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
class Scene:
    id: str
    place: str
    opening: str
    surface: str
    missing_from: str
    affordances: set[str] = field(default_factory=set)
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
    verb: str
    effect: str
    location: str
    needs: set[str] = field(default_factory=set)
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
    notice_text: str
    reason_text: str
    supports: set[str] = field(default_factory=set)
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
class Method:
    id: str
    action_text: str
    recovery_text: str
    fits: set[str] = field(default_factory=set)
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
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
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
        clone = World(self.scene)
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


def _r_generate_clue(world: World) -> list[str]:
    dime = world.get("dime")
    clue = world.get("clue")
    detective = world.get("detective")
    if dime.meters["missing"] < THRESHOLD:
        return []
    sig = ("clue", world.facts["cause"].id, world.facts["clue"].id)
    if sig in world.fired:
        return []
    if world.facts["clue"].id not in world.facts["cause"].tags and world.facts["clue"].id not in world.facts["cause"].needs and world.facts["cause"].id not in world.facts["clue"].supports:
        return []
    world.fired.add(sig)
    clue.meters["visible"] += 1
    detective.memes["curiosity"] += 1
    return ["__clue__"]


def _r_follow_clue(world: World) -> list[str]:
    clue = world.get("clue")
    detective = world.get("detective")
    if clue.meters["visible"] < THRESHOLD or detective.memes["focus"] < THRESHOLD:
        return []
    sig = ("deduce", world.facts["cause"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["certainty"] += 1
    return ["__deduction__"]


def _r_find_dime(world: World) -> list[str]:
    dime = world.get("dime")
    detective = world.get("detective")
    if detective.memes["certainty"] < THRESHOLD or world.facts.get("searched_right_place", 0.0) < THRESHOLD:
        return []
    sig = ("found", world.facts["cause"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    dime.meters["missing"] = 0.0
    dime.meters["found"] += 1
    detective.memes["relief"] += 1
    detective.memes["pride"] += 1
    detective.memes["worry"] = 0.0
    helper = world.get("helper")
    helper.memes["relief"] += 1
    return ["__found__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="generate_clue", tag="physical", apply=_r_generate_clue),
    Rule(name="follow_clue", tag="mental", apply=_r_follow_clue),
    Rule(name="find_dime", tag="physical", apply=_r_find_dime),
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


def cause_fits_scene(scene: Scene, cause: Cause) -> bool:
    return cause.id in scene.affordances and cause.needs.issubset(scene.tags | scene.affordances)


def combo_is_valid(scene: Scene, cause: Cause, clue: Clue, method: Method) -> bool:
    if not cause_fits_scene(scene, cause):
        return False
    if cause.id not in clue.supports:
        return False
    if cause.id not in method.fits:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for scene_id, scene in SCENES.items():
        for cause_id, cause in CAUSES.items():
            for clue_id, clue in CLUES.items():
                for method_id, method in METHODS.items():
                    if combo_is_valid(scene, cause, clue, method):
                        out.append((scene_id, cause_id, clue_id, method_id))
    return out


def explain_rejection(scene: Scene, cause: Cause, clue: Clue, method: Method) -> str:
    if not cause_fits_scene(scene, cause):
        return (
            f"(No story: in {scene.place}, a dime would not reasonably {cause.effect}. "
            f"Pick a scene that supports {cause.verb}.)"
        )
    if cause.id not in clue.supports:
        return (
            f"(No story: the clue '{clue.label}' does not honestly point to a dime that {cause.effect}. "
            f"Choose a clue that matches the physical cause.)"
        )
    if cause.id not in method.fits:
        return (
            f"(No story: the method '{method.id}' would not find a dime that {cause.effect}. "
            f"The detective must solve the mystery with a fitting search.)"
        )
    return "(No story: this combination does not form a reasonable mystery.)"


def predict_clue(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    clue = sim.get("clue")
    detective = sim.get("detective")
    return {
        "clue_visible": clue.meters["visible"] >= THRESHOLD,
        "curiosity": detective.memes["curiosity"],
    }


def introduce(world: World, detective: Entity, helper: Entity, parent: Entity, scene: Scene) -> None:
    detective.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{scene.opening} {detective.id} liked pretending to be a detective, and "
        f"{helper.id} was the best helper {detective.pronoun()} could ask for."
    )
    world.say(
        f"{detective.id} carried one bright dime in {detective.pronoun('possessive')} pocket "
        f"and planned to use it later."
    )
    world.say(
        f'{parent.label_word.capitalize()} smiled and said, "Keep an eye on that little coin."'
    )


def place_dime(world: World, detective: Entity, scene: Scene) -> None:
    dime = world.get("dime")
    dime.meters["safe"] += 1
    world.say(
        f"When it was time to wash sticky hands and straighten the game, "
        f"{detective.id} set the dime on {scene.missing_from} for just a moment."
    )


def discover_missing(world: World, detective: Entity, helper: Entity) -> None:
    dime = world.get("dime")
    dime.meters["missing"] += 1
    dime.meters["safe"] = 0.0
    detective.memes["worry"] += 1
    helper.memes["surprise"] += 1
    world.say(
        f"But when {detective.id} turned back, the dime was gone."
    )
    world.say(
        f'"A mystery," {detective.id} whispered. "{helper.id}, do not touch anything yet."'
    )


def notice_clue(world: World, detective: Entity, clue: Clue) -> None:
    pred = predict_clue(world)
    detective.memes["focus"] += 1
    world.facts["predicted_clue_visible"] = pred["clue_visible"]
    world.say(
        f"{detective.id} bent low and looked carefully. {clue.notice_text}"
    )
    world.say(
        f'"That is a clue," {detective.pronoun()} said. "{clue.reason_text}"'
    )
    propagate(world, narrate=False)


def calm_no_blame(world: World, detective: Entity, helper: Entity, parent: Entity) -> None:
    helper.memes["worry"] += 1
    world.say(
        f'{helper.id} looked worried, but {detective.id} shook {detective.pronoun("possessive")} head. '
        f'"We are not blaming anybody," {detective.pronoun()} said. '
        f'"A real detective follows signs first."'
    )
    world.say(
        f'{parent.label_word.capitalize()} nodded. "That is the wise way to solve a mystery."'
    )


def deduce(world: World, detective: Entity, cause: Cause) -> None:
    detective.memes["focus"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the pieces fit together in {detective.id}'s mind. "
        f"The dime had not been stolen at all; it had {cause.effect}."
    )


def search(world: World, detective: Entity, helper: Entity, method: Method, cause: Cause) -> None:
    world.facts["searched_right_place"] = 1.0
    helper.memes["helpfulness"] += 1
    world.say(
        f"{detective.id} and {helper.id} {method.action_text}"
    )
    propagate(world, narrate=False)
    if world.get("dime").meters["found"] >= THRESHOLD:
        world.say(method.recovery_text)
        world.say(
            f'"Case closed," {detective.id} said, and {helper.id} laughed with relief.'
        )
    else:
        raise StoryError("The detective searched the right place, but the dime was not found.")


def ending(world: World, detective: Entity, helper: Entity, parent: Entity, scene: Scene) -> None:
    detective.memes["trust_in_clues"] += 1
    world.say(
        f'{parent.label_word.capitalize()} tapped the recovered dime into {detective.id}\'s palm. '
        f'"What solved the mystery?"'
    )
    world.say(
        f'"Looking closely," {detective.id} answered. "The clue told the truth."'
    )
    world.say(
        f"After that, the dime rode safely in a buttoned pocket, and "
        f"{detective.id} and {helper.id} marched across {scene.place} as if the whole world "
        f"were full of tiny cases waiting to be solved."
    )


def tell(
    scene: Scene,
    cause: Cause,
    clue: Clue,
    method: Method,
    detective_name: str = "Nora",
    detective_gender: str = "girl",
    helper_name: str = "Ben",
    helper_gender: str = "boy",
    parent_type: str = "mother",
    detective_trait: str = "careful",
) -> World:
    world = World(scene)

    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        label=detective_name,
        role="detective",
        traits=[detective_trait, "observant"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        label=helper_name,
        role="helper",
        traits=["kind"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    dime = world.add(Entity(
        id="dime",
        kind="thing",
        type="coin",
        label="dime",
        role="lost_item",
    ))
    clue_ent = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=clue.label,
        role="clue",
    ))
    place_ent = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=scene.place,
        role="place",
    ))

    world.facts.update(
        detective=detective,
        helper=helper,
        parent=parent,
        dime=dime,
        clue=clue_ent,
        scene=scene,
        cause=cause,
        clue_cfg=clue,
        method=method,
        searched_right_place=0.0,
    )

    introduce(world, detective, helper, parent, scene)
    place_dime(world, detective, scene)

    world.para()
    discover_missing(world, detective, helper)
    propagate(world, narrate=False)
    notice_clue(world, detective, clue)
    calm_no_blame(world, detective, helper, parent)

    world.para()
    deduce(world, detective, cause)
    search(world, detective, helper, method, cause)

    world.para()
    ending(world, detective, helper, parent, scene)
    world.facts["solved"] = dime.meters["found"] >= THRESHOLD
    return world


SCENES = {
    "porch": Scene(
        id="porch",
        place="the front porch",
        opening="Late in the afternoon, the front porch smelled of warm wood and summer dust.",
        surface="slanted boards",
        missing_from="the porch rail",
        affordances={"rolled"},
        tags={"slanted", "boards", "under_bench", "detective"},
    ),
    "picnic": Scene(
        id="picnic",
        place="the picnic table by the garden",
        opening="Near supper time, the picnic table by the garden was crowded with paper cups and a jar of red jam.",
        surface="sticky tabletop",
        missing_from="the edge of the table beside the jam jar",
        affordances={"sticky"},
        tags={"sticky", "jar", "sweet", "detective"},
    ),
    "playroom": Scene(
        id="playroom",
        place="the playroom",
        opening="On a rainy afternoon, the playroom was full of dress-up clothes, cardboard crowns, and one tall rubber boot by the rug.",
        surface="soft rug",
        missing_from="the rug beside the dress-up basket",
        affordances={"slipped"},
        tags={"boot", "dressup", "clink", "detective"},
    ),
}

CAUSES = {
    "rolled": Cause(
        id="rolled",
        verb="roll away",
        effect="rolled through a crack and hidden itself under the bench",
        location="under the porch bench",
        needs={"slanted"},
        tags={"rolled", "scrape"},
    ),
    "sticky": Cause(
        id="sticky",
        verb="stick to something sweet",
        effect="stuck to the jammy lid of the jar",
        location="on the underside of the jam jar lid",
        needs={"sticky"},
        tags={"sticky", "sweet"},
    ),
    "slipped": Cause(
        id="slipped",
        verb="slip into soft dress-up things",
        effect="slipped into the toe of the tall rubber boot",
        location="inside the tall rubber boot",
        needs={"boot"},
        tags={"slipped", "clink"},
    ),
}

CLUES = {
    "scrape": Clue(
        id="scrape",
        label="a tiny silver scrape",
        notice_text="On the wood was a tiny silver scrape that caught the light like a thread.",
        reason_text="A mark like that means something small and hard rolled away in a hurry.",
        supports={"rolled"},
        tags={"detective", "trace"},
    ),
    "sweet_smudge": Clue(
        id="sweet_smudge",
        label="a sweet red smudge",
        notice_text="Beside the empty spot was a sweet red smudge, and even the air smelled like berries.",
        reason_text="Sticky jam can grab a coin and carry it somewhere strange.",
        supports={"sticky"},
        tags={"detective", "jam"},
    ),
    "little_clink": Clue(
        id="little_clink",
        label="a little clink",
        notice_text="When the tall boot leaned against the basket, it gave a tiny clink from deep inside.",
        reason_text="Metal makes that sound when it bumps against rubber or the floor.",
        supports={"slipped"},
        tags={"detective", "sound"},
    ),
}

METHODS = {
    "flashlight_peek": Method(
        id="flashlight_peek",
        action_text="knelt by the bench and used a small flashlight to look into the dark strip under it.",
        recovery_text="There, under the bench, the dime winked back like a tiny moon.",
        fits={"rolled"},
        tags={"flashlight", "search"},
    ),
    "twist_lid": Method(
        id="twist_lid",
        action_text="carefully twisted open the jam jar and turned the lid over in the light.",
        recovery_text="The dime was stuck to the underside of the lid with a shiny red dot of jam.",
        fits={"sticky"},
        tags={"jar", "search"},
    ),
    "tip_boot": Method(
        id="tip_boot",
        action_text="picked up the tall boot and tipped it upside down over the rug.",
        recovery_text="Out dropped the dime with one cheerful clink and a soft little bounce.",
        fits={"slipped"},
        tags={"boot", "search"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lily", "Ava", "Zoe", "Ruby", "Ella", "Anna"]
BOY_NAMES = ["Ben", "Max", "Leo", "Finn", "Theo", "Sam", "Noah", "Jack"]
TRAITS = ["careful", "steady", "curious", "patient", "sharp-eyed"]


@dataclass
class StoryParams:
    scene: str
    cause: str
    clue: str
    method: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
    parent: str
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
    "dime": [
        (
            "What is a dime?",
            "A dime is a small coin worth ten cents. It is thin, round, and easy to drop or roll away."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective solves mysteries by noticing clues and thinking carefully about what happened. A good detective looks for facts before guessing."
        )
    ],
    "flashlight": [
        (
            "Why does a flashlight help in a mystery?",
            "A flashlight helps you see into dark places where your eyes miss small things. It is useful when something tiny rolls under furniture."
        )
    ],
    "jam": [
        (
            "Why can a coin stick to jam?",
            "Jam is sticky because it is thick and sugary. A light coin can cling to it instead of dropping straight down."
        )
    ],
    "sound": [
        (
            "Why would a coin make a clink in a boot?",
            "A coin is made of metal, so it makes a sharp little sound when it hits something hard or rubbery. That sound can be a clue."
        )
    ],
    "rolled": [
        (
            "Why do coins roll away so easily?",
            "Coins are round and smooth, so even a small tilt can make them move. On a slanted surface, they may roll farther than you expect."
        )
    ],
}
KNOWLEDGE_ORDER = ["dime", "detective", "rolled", "jam", "sound", "flashlight"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    scene = f["scene"]
    clue = f["clue_cfg"]
    return [
        f'Write a child-friendly detective story about a missing dime in {scene.place}. Include the word "dime".',
        f"Tell a mystery where {detective.id} and {helper.id} solve a small case by noticing {clue.label} and following it calmly.",
        "Write a gentle Mystery to Solve story in a detective style where nobody steals anything, and the truth is found by careful looking."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    parent = f["parent"]
    scene = f["scene"]
    cause = f["cause"]
    clue = f["clue_cfg"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a small detective, and {helper.id}, the helper who searched beside {detective.pronoun('object')}. {parent.label_word.capitalize()} also listened and praised their careful thinking."
        ),
        (
            "What was the mystery?",
            f"The mystery was that {detective.id}'s dime disappeared from {scene.missing_from}. The children had to figure out where it went and why it vanished."
        ),
        (
            "What clue did they find?",
            f"They found {clue.label}. That clue mattered because it matched the way the dime had really moved."
        ),
        (
            f"Why did {detective.id} say they should not blame anyone right away?",
            f"{detective.id} wanted to solve the case like a real detective. The clue showed that something physical had happened, so careful looking was smarter than making a wild guess."
        ),
        (
            "How was the mystery solved?",
            f"They used the clue to decide that the dime had {cause.effect}. Then they {method.action_text} and found it exactly where the clue pointed."
        ),
        (
            "How did the story end?",
            f"The dime was back in {detective.id}'s hand, and everyone felt relieved. After that, {detective.id} kept the dime in a buttoned pocket and trusted clues more than quick blame."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"dime", "detective"}
    cause = world.facts["cause"]
    method = world.facts["method"]
    if cause.id == "rolled":
        tags.add("rolled")
    if cause.id == "sticky":
        tags.add("jam")
    if cause.id == "slipped":
        tags.add("sound")
    if method.id == "flashlight_peek":
        tags.add("flashlight")
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        scene="porch",
        cause="rolled",
        clue="scrape",
        method="flashlight_peek",
        detective="Nora",
        detective_gender="girl",
        helper="Ben",
        helper_gender="boy",
        parent="mother",
        trait="careful",
        seed=101,
    ),
    StoryParams(
        scene="picnic",
        cause="sticky",
        clue="sweet_smudge",
        method="twist_lid",
        detective="Leo",
        detective_gender="boy",
        helper="Mia",
        helper_gender="girl",
        parent="father",
        trait="patient",
        seed=102,
    ),
    StoryParams(
        scene="playroom",
        cause="slipped",
        clue="little_clink",
        method="tip_boot",
        detective="Ava",
        detective_gender="girl",
        helper="Max",
        helper_gender="boy",
        parent="mother",
        trait="sharp-eyed",
        seed=103,
    ),
]


ASP_RULES = r"""
scene_supports(S,C) :- affords(S,C).
clue_matches(C,Cl) :- supports(Cl,C).
method_matches(C,M) :- fits(M,C).

valid(S,C,Cl,M) :- scene(S), cause(C), clue(Cl), method(M),
                   scene_supports(S,C), clue_matches(C,Cl), method_matches(C,M).

solved(S,C,Cl,M) :- valid(S,C,Cl,M).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for scene_id, scene in SCENES.items():
        lines.append(asp.fact("scene", scene_id))
        for cause_id in sorted(scene.affordances):
            lines.append(asp.fact("affords", scene_id, cause_id))
    for cause_id in CAUSES:
        lines.append(asp.fact("cause", cause_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        for cause_id in sorted(clue.supports):
            lines.append(asp.fact("supports", clue_id, cause_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        for cause_id in sorted(method.fits):
            lines.append(asp.fact("fits", method_id, cause_id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/4.") -> str:
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
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty during verify.")
        if sample.world is None or not sample.world.facts.get("solved"):
            raise StoryError("Generated story did not solve the mystery during verify.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"VERIFY generation failure: {err}")

    parser = build_parser()
    for seed in range(5):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if "dime" not in sample.story.lower():
                raise StoryError("Smoke test story did not mention dime.")
        except Exception as err:
            rc = 1
            print(f"VERIFY random generation failure at seed {seed}: {err}")
            break

    if rc == 0:
        print("OK: random generation smoke tests succeeded.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tiny detective story world: a missing dime, a clue, and a careful solution."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--detective")
    ap.add_argument("--helper")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid mystery combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene is not None and args.scene not in SCENES:
        raise StoryError(f"(Unknown scene: {args.scene})")
    if args.cause is not None and args.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {args.cause})")
    if args.clue is not None and args.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {args.clue})")
    if args.method is not None and args.method not in METHODS:
        raise StoryError(f"(Unknown method: {args.method})")

    if args.scene and args.cause and args.clue and args.method:
        scene = SCENES[args.scene]
        cause = CAUSES[args.cause]
        clue = CLUES[args.clue]
        method = METHODS[args.method]
        if not combo_is_valid(scene, cause, clue, method):
            raise StoryError(explain_rejection(scene, cause, clue, method))

    combos = [
        combo for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.cause is None or combo[1] == args.cause)
        and (args.clue is None or combo[2] == args.clue)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, cause_id, clue_id, method_id = rng.choice(sorted(combos))
    detective_name, detective_gender = _pick_name(rng)
    helper_name, helper_gender = _pick_name(rng, avoid=detective_name)
    if args.detective:
        detective_name = args.detective
    if args.helper:
        helper_name = args.helper
        if helper_name == detective_name:
            alt, helper_gender = _pick_name(rng, avoid=detective_name)
            helper_name = alt
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        scene=scene_id,
        cause=cause_id,
        clue=clue_id,
        method=method_id,
        detective=detective_name,
        detective_gender=detective_gender,
        helper=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"(Unknown scene: {params.scene})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    scene = SCENES[params.scene]
    cause = CAUSES[params.cause]
    clue = CLUES[params.clue]
    method = METHODS[params.method]
    if not combo_is_valid(scene, cause, clue, method):
        raise StoryError(explain_rejection(scene, cause, clue, method))

    world = tell(
        scene=scene,
        cause=cause,
        clue=clue,
        method=method,
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        detective_trait=params.trait,
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
        print(f"{len(combos)} valid (scene, cause, clue, method) combinations:\n")
        for scene_id, cause_id, clue_id, method_id in combos:
            print(f"  {scene_id:8} {cause_id:8} {clue_id:12} {method_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective}: {p.scene} / {p.cause} / {p.clue} / {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
