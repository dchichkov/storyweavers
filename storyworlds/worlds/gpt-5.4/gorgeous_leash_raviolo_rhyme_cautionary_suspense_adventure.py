#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gorgeous_leash_raviolo_rhyme_cautionary_suspense_adventure.py
=========================================================================================

A standalone storyworld for a tiny cautionary adventure: a child and a dog set
off for a festive place, a tempting food smell pulls the dog toward danger, and
a sensible grown-up turns a near-accident into a safer habit.

Seed obligations:
- includes the words "gorgeous", "leash", and "raviolo"
- uses rhyme, cautionary tension, and an adventure shape
- renders state-driven prose from a simulated world rather than noun-swaps

Core common-sense constraint
----------------------------
The dog's temptation must happen somewhere with a real edge risk and a real
food lure. A leash only matters when the dog is excitable and the place has a
drop, water edge, crowd edge, or road edge. The world rejects combinations where
nothing risky would happen, because then there is no honest warning and no real
turn.

Run it
------
    python storyworlds/worlds/gpt-5.4/gorgeous_leash_raviolo_rhyme_cautionary_suspense_adventure.py
    python storyworlds/worlds/gpt-5.4/gorgeous_leash_raviolo_rhyme_cautionary_suspense_adventure.py --place harbor --lure food_cart --gear leash
    python storyworlds/worlds/gpt-5.4/gorgeous_leash_raviolo_rhyme_cautionary_suspense_adventure.py --place meadow
    python storyworlds/worlds/gpt-5.4/gorgeous_leash_raviolo_rhyme_cautionary_suspense_adventure.py --all
    python storyworlds/worlds/gpt-5.4/gorgeous_leash_raviolo_rhyme_cautionary_suspense_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/gorgeous_leash_raviolo_rhyme_cautionary_suspense_adventure.py --verify
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

# Make the shared result containers importable when this script is run directly
# from a nested directory under storyworlds/worlds/.
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
STORYWORLDS_DIR = os.path.dirname(os.path.dirname(THIS_DIR))
sys.path.insert(0, STORYWORLDS_DIR)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SAFE_SENSE_MIN = 2


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "animal" | "thing"
    type: str = "thing"            # girl, boy, mother, father, dog, bridge ...
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""                 # child | adult | dog
    owner: str = ""
    tethered_to: str = ""
    # state axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        doggy = {"dog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in doggy:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs
# ---------------------------------------------------------------------------
@dataclass
class Place:
    id: str
    label: str
    scene: str
    path: str
    edge: str
    hazard: str
    rescue_spot: str
    danger: int
    risk_tags: set[str] = field(default_factory=set)


@dataclass
class Lure:
    id: str
    label: str
    source: str
    motion: str
    smell: str
    object_word: str
    danger_reason: str
    intensity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    keeps_close: bool
    pretty: bool
    adjective: str
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    label: str
    method: str
    success_text: str
    qa_text: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_tug_becomes_risk(world: World) -> list[str]:
    out: list[str] = []
    dog = world.entities.get("dog")
    child = world.entities.get("child")
    place = world.facts.get("place")
    gear = world.facts.get("gear")
    if not dog or not child or place is None or gear is None:
        return out
    if dog.meters["lunging"] < THRESHOLD:
        return out
    sig = ("tug_risk", bool(gear.keeps_close))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if gear.keeps_close:
        child.meters["pulled"] += 1
        child.memes["alarm"] += 1
        dog.memes["frustration"] += 1
        out.append("__held__")
    else:
        dog.meters["distance"] += 1
        dog.meters["near_edge"] += 1
        child.memes["alarm"] += 1
        out.append("__loose__")
    return out


def _r_edge_danger(world: World) -> list[str]:
    out: list[str] = []
    dog = world.entities.get("dog")
    place = world.facts.get("place")
    if not dog or place is None:
        return out
    if dog.meters["near_edge"] < THRESHOLD:
        return out
    sig = ("edge_danger", place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("place").meters["danger"] += place.danger
    dog.memes["fear"] += 1
    out.append("__danger__")
    return out


CAUSAL_RULES = [
    Rule("tug_becomes_risk", "physical", _r_tug_becomes_risk),
    Rule("edge_danger", "physical", _r_edge_danger),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(got)
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def hazard_at_risk(place: Place, lure: Lure) -> bool:
    return place.danger > 0 and lure.intensity > 0


def sensible_gears() -> list[Gear]:
    return [g for g in GEARS.values() if g.sense >= SAFE_SENSE_MIN]


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SAFE_SENSE_MIN]


def chase_severity(place: Place, lure: Lure, patience: int) -> int:
    return place.danger + lure.intensity + patience


def is_contained(gear: Gear, response: Response, place: Place, lure: Lure, patience: int) -> bool:
    base = response.power + (1 if gear.keeps_close else 0)
    return base >= chase_severity(place, lure, patience)


def explain_rejection(place: Place, lure: Lure) -> str:
    if place.danger <= 0:
        return (f"(No story: {place.label} has no real edge danger here, so a leash "
                f"would not matter and there is no honest cautionary turn.)")
    if lure.intensity <= 0:
        return (f"(No story: {lure.label} would not tempt the dog strongly enough "
                f"to create suspense or risk.)")
    return "(No story: this place and lure do not make a real hazard together.)"


def explain_gear(gid: str) -> str:
    g = GEARS[gid]
    better = ", ".join(sorted(x.id for x in sensible_gears()))
    return (f"(Refusing gear '{gid}': it scores too low on common sense "
            f"(sense={g.sense} < {SAFE_SENSE_MIN}). Try: {better}.)")


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_chase(world: World) -> dict:
    sim = world.copy()
    trigger_lunge(sim, narrate=False)
    place = sim.get("place")
    return {
        "danger": place.meters["danger"],
        "dog_near_edge": sim.get("dog").meters["near_edge"] >= THRESHOLD,
        "child_alarm": sim.get("child").memes["alarm"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs / screenplay beats
# ---------------------------------------------------------------------------
def rhyme_pair(a: str, b: str) -> str:
    return f'"{a}," said the grown-up. "{b}."'


def introduce(world: World, child: Entity, dog: Entity, place: Place, gear: Gear) -> None:
    dog.memes["joy"] += 1
    child.memes["wonder"] += 1
    gorgeous = "gorgeous " if gear.pretty else ""
    world.say(
        f"{child.id} and {dog.id} set out for {place.label}, where {place.scene}. "
        f"{dog.id} wore a {gorgeous}{gear.label} that bounced against {dog.pronoun('possessive')} chest."
    )
    world.say(
        f"To {child.id}, it felt like the start of a true adventure along {place.path}."
    )
    world.say(
        rhyme_pair("Steady paws, steady nose", "that's how a brave explorer goes")
    )


def goal(world: World, child: Entity, adult: Entity, dog: Entity, place: Place) -> None:
    child.memes["joy"] += 1
    world.say(
        f"They were hunting for the prettiest view near {place.edge}, and {adult.label_word} promised a snack at {place.rescue_spot} after."
    )
    world.say(
        f"{dog.id} trotted ahead, tail high, as if every stone and breeze might hide a secret."
    )


def scent_arrives(world: World, dog: Entity, lure: Lure) -> None:
    dog.memes["tempted"] += 1
    world.say(
        f"Then a rich smell slipped through the air: {lure.smell}. It came from {lure.source}, where {lure.motion}."
    )
    world.say(
        f"Right on top sat one enormous raviolo, round and golden and almost too good to be real."
    )
    world.say(
        rhyme_pair("Raviolo, raviolo, slow and low", "sniff first, think first, then you may go")
    )


def warn(world: World, adult: Entity, child: Entity, dog: Entity, place: Place, lure: Lure, gear: Gear) -> None:
    pred = predict_chase(world)
    world.facts["predicted_danger"] = pred["danger"]
    extra = "keep the leash snug" if gear.keeps_close else "hold close and do not let go"
    world.say(
        f'{adult.label_word.capitalize()} saw {dog.id} freeze, nose twitching toward {lure.object_word}. '
        f'"Careful," {adult.pronoun()} said. "{lure.danger_reason} by {place.edge}. {extra}."'
    )


def choice_beat(world: World, child: Entity, dog: Entity, gear: Gear) -> None:
    child.memes["responsibility"] += 1
    if gear.keeps_close:
        world.say(
            f"{child.id} wrapped a hand around the leash and felt the dog’s excitement humming through it."
        )
    else:
        world.say(
            f"{child.id} meant to stay careful, but the pretty collar loop felt easy and loose in {child.pronoun('possessive')} fingers."
        )
    world.say(
        "For one breath, everything held still."
    )


def trigger_lunge(world: World, narrate: bool = True) -> None:
    dog = world.get("dog")
    gear = world.facts["gear"]
    place = world.facts["place"]
    lure = world.facts["lure"]
    dog.meters["lunging"] += 1
    dog.meters["speed"] += lure.intensity
    marks = propagate(world, narrate=False)
    if not narrate:
        return
    world.say(
        f"Then {dog.id} sprang toward {lure.object_word} so suddenly that the world seemed to jump with him."
    )
    if "__held__" in marks:
        world.say(
            f"The {gear.label} snapped tight. {child.id} slid one shoe across the ground, heart thumping, but {dog.id} did not reach {place.edge}."
        )
    if "__loose__" in marks:
        world.say(
            f"The loose strap slipped free. In a blink, {dog.id} skittered toward {place.edge}, claws ticking fast."
        )


def rescue(world: World, adult: Entity, child: Entity, dog: Entity, response: Response, place: Place) -> None:
    dog.meters["near_edge"] = 0.0
    dog.meters["distance"] = 0.0
    dog.meters["lunging"] = 0.0
    world.get("place").meters["danger"] = 0.0
    dog.memes["fear"] = 0.0
    child.memes["alarm"] = 0.0
    child.memes["relief"] += 1
    dog.memes["relief"] += 1
    adult.memes["care"] += 1
    world.say(
        f"{adult.label_word.capitalize()} {response.success_text}."
    )
    world.say(
        f"A moment later, {dog.id} was safe again, trembling beside {child.id} and staring at {place.edge} as if it had grown teeth."
    )


def lesson(world: World, adult: Entity, child: Entity, dog: Entity, gear: Gear) -> None:
    child.memes["lesson"] += 1
    dog.memes["trust"] += 1
    world.say(
        f'{adult.label_word.capitalize()} knelt beside them both. "A {gear.label} is not just pretty," {adult.pronoun()} said softly. "It keeps a fast friend close when a fast idea races by."'
    )
    world.say(
        rhyme_pair("Near an edge, do not dash", "pause, hold tight, and miss the splash")
    )
    world.say(
        f"{child.id} nodded and stroked {dog.id}'s ears until the shaking stopped."
    )


def safe_end(world: World, child: Entity, adult: Entity, dog: Entity, gear: Gear, place: Place) -> None:
    child.memes["joy"] += 1
    dog.memes["joy"] += 1
    world.say(
        f"After that, {child.id} clipped the {gear.label} on properly and kept the leash short while they finished their walk."
    )
    world.say(
        f"At {place.rescue_spot}, they shared a picnic treat, and {dog.id} got a biscuit instead of chasing the giant raviolo."
    )
    world.say(
        f"The adventure still felt gorgeous at the end, only now it was brave and careful too."
    )


def loss_scare(world: World, adult: Entity, child: Entity, dog: Entity, place: Place, lure: Lure) -> None:
    child.memes["alarm"] += 1
    dog.memes["fear"] += 1
    world.say(
        f"For a terrible second, {dog.id} scrambled at the very edge near {place.edge}, with {lure.object_word} skidding away and the drop just beyond."
    )
    world.say(
        f"{child.id} could only gasp as {adult.label_word} lunged after him."
    )


def grim_resolution(world: World, adult: Entity, child: Entity, dog: Entity, gear: Gear, place: Place) -> None:
    dog.meters["near_edge"] = 0.0
    world.get("place").meters["danger"] = 0.0
    child.memes["lesson"] += 1
    child.memes["relief"] += 1
    dog.memes["relief"] += 1
    world.say(
        f"{adult.label_word.capitalize()} caught {dog.id} just in time and held him tight against {adult.pronoun('possessive')} coat."
    )
    world.say(
        f'No one was hurt, but nobody called it a game anymore. "{gear.label.capitalize()} first, every single time," {adult.pronoun()} said.'
    )
    world.say(
        f"They went straight home, and the quiet walk back felt longer than the whole adventure out."
    )


def tell(place: Place, lure: Lure, gear: Gear, response: Response,
         child_name: str = "Lina", child_gender: str = "girl",
         dog_name: str = "Ravi", adult_type: str = "mother",
         patience: int = 0, child_trait: str = "careful") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="child", traits=[child_trait]))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type,
                             role="adult", label="the grown-up"))
    dog = world.add(Entity(id=dog_name, kind="animal", type="dog", role="dog",
                           traits=["quick", "hungry"]))
    leash_ent = world.add(Entity(id="gear", kind="thing", type="gear", label=gear.label))
    place_ent = world.add(Entity(id="place", kind="thing", type="place", label=place.label))
    leash_ent.owner = child.id
    dog.owner = child.id
    if gear.keeps_close:
        dog.tethered_to = "gear"

    world.facts.update(
        place=place,
        lure=lure,
        gear=gear,
        response=response,
        patience=patience,
    )

    introduce(world, child, dog, place, gear)
    goal(world, child, adult, dog, place)

    world.para()
    scent_arrives(world, dog, lure)
    warn(world, adult, child, dog, place, lure, gear)
    choice_beat(world, child, dog, gear)

    world.para()
    trigger_lunge(world, narrate=True)
    severity = chase_severity(place, lure, patience)
    contained = is_contained(gear, response, place, lure, patience)
    world.facts["severity"] = severity
    world.facts["contained"] = contained

    world.para()
    if contained:
        rescue(world, adult, child, dog, response, place)
        lesson(world, adult, child, dog, gear)
        world.para()
        safe_end(world, child, adult, dog, gear, place)
        outcome = "contained"
    else:
        loss_scare(world, adult, child, dog, place, lure)
        grim_resolution(world, adult, child, dog, gear, place)
        outcome = "scared"
    world.facts.update(
        child=child,
        adult=adult,
        dog=dog,
        outcome=outcome,
        promised=child.memes["lesson"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "harbor": Place(
        "harbor",
        "the moonlit harbor walk",
        "string lights swung over black water and fishing boats knocked softly together",
        "the slick stone path",
        "the harbor rail",
        "deep water just below",
        "a bench under a lamp",
        danger=3,
        risk_tags={"water", "edge"},
    ),
    "bridge": Place(
        "bridge",
        "the old bridge path",
        "wind hummed through the ropes and the river flashed below",
        "the wooden boards",
        "the bridge side",
        "a hard drop to the riverbank",
        "the wide middle platform",
        danger=2,
        risk_tags={"river", "edge"},
    ),
    "market": Place(
        "market",
        "the evening market lane",
        "lanterns glowed over busy feet and wagons rattled by",
        "the crowded lane",
        "the cart lane",
        "rolling wheels and rushing people",
        "the baker's doorway",
        danger=2,
        risk_tags={"crowd", "road"},
    ),
    "meadow": Place(
        "meadow",
        "the bright meadow path",
        "buttercups nodded in a warm breeze and bees bumbled lazily",
        "the soft grass trail",
        "the flower patch",
        "nothing sharper than tall grass",
        "the big oak stump",
        danger=0,
        risk_tags={"soft"},
    ),
}

LURES = {
    "food_cart": Lure(
        "food_cart",
        "the food cart",
        "a little cart at the bend",
        "steam curling from a silver pan",
        "butter, cheese, and sage",
        "the giant raviolo",
        "A dog who leaps for food can forget where his paws are",
        intensity=2,
        tags={"food", "raviolo"},
    ),
    "picnic_plate": Lure(
        "picnic_plate",
        "the picnic plate",
        "a blanket near the path",
        "a paper plate wobbling in the breeze",
        "warm tomato sauce and baked pasta",
        "the picnic raviolo",
        "A dog who lunges for dropped food can run straight into trouble",
        intensity=1,
        tags={"food", "raviolo"},
    ),
    "vendor_bag": Lure(
        "vendor_bag",
        "the paper bag",
        "a laughing vendor's hand",
        "a striped bag swinging back and forth",
        "fried herbs and soft pasta",
        "the dangling raviolo",
        "A swinging treat can pull a dog faster than a child can think",
        intensity=2,
        tags={"food", "raviolo"},
    ),
}

GEARS = {
    "leash": Gear(
        "leash", "leash", keeps_close=True, pretty=False, adjective="plain", sense=3,
        tags={"leash", "safe"}
    ),
    "gorgeous_leash": Gear(
        "gorgeous_leash", "gorgeous leash", keeps_close=True, pretty=True, adjective="gorgeous", sense=3,
        tags={"leash", "safe", "gorgeous"}
    ),
    "collar_loop": Gear(
        "collar_loop", "collar loop", keeps_close=False, pretty=False, adjective="loose", sense=1,
        tags={"collar"}
    ),
}

RESPONSES = {
    "brace_and_pull": Response(
        "brace_and_pull",
        "brace and pull",
        "the grown-up braces and gathers the leash",
        "planted both feet, caught the leash with both hands, and pulled the dog back from danger",
        "braced, seized the leash, and pulled the dog back from danger",
        power=3,
        sense=3,
        tags={"rescue", "leash"},
    ),
    "scoop_dog": Response(
        "scoop_dog",
        "scoop dog",
        "the grown-up grabs the dog under the belly",
        "darted forward and scooped the dog up before he could reach the edge",
        "darted forward and scooped the dog up before he reached the edge",
        power=2,
        sense=3,
        tags={"rescue", "dog"},
    ),
    "shout_only": Response(
        "shout_only",
        "shout only",
        "the grown-up only shouts",
        "shouted for the dog to stop",
        "only shouted for the dog to stop",
        power=1,
        sense=1,
        tags={"weak"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Nora", "Ava", "Lucy", "Maya", "Zoe"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Ben", "Leo", "Finn", "Eli", "Sam"]
DOG_NAMES = ["Ravi", "Pip", "Comet", "Biscuit", "Moss", "Pepper"]
TRAITS = ["careful", "curious", "bold", "thoughtful", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for lid, lure in LURES.items():
            if not hazard_at_risk(place, lure):
                continue
            for gid, gear in GEARS.items():
                if gear.sense >= SAFE_SENSE_MIN:
                    combos.append((pid, lid, gid))
    return combos


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    lure: str
    gear: str
    response: str
    child_name: str
    child_gender: str
    dog_name: str
    adult: str
    trait: str
    patience: int = 0
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "leash": [("What does a leash do?",
               "A leash keeps a dog close to the person holding it. That helps the dog stay safe near roads, crowds, and edges.")],
    "gorgeous": [("What does gorgeous mean?",
                  "Gorgeous means very beautiful or lovely to look at. People use it for something bright, pretty, or special.")],
    "raviolo": [("What is a raviolo?",
                 "A raviolo is one big piece of stuffed pasta. It can smell delicious, which is why it might tempt a hungry dog.")],
    "water": [("Why is a harbor edge dangerous for a dog?",
               "A harbor edge is dangerous because the water is deep and the ground can be slippery. A fast jump can turn into a fall.")],
    "river": [("Why should you hold tight on a bridge?",
               "A bridge can be windy and narrow, and there may be a drop beside it. Holding tight helps you keep control.")],
    "crowd": [("Why can a busy market be risky for a dog?",
               "A busy market has rolling carts, many feet, and lots of smells. A dog that darts suddenly can get lost or hurt.")],
    "rescue": [("What should a grown-up do if a dog lunges toward danger?",
                "The grown-up should act quickly and calmly to get the dog back to safety. Fast help matters because danger moves faster than talking.")],
}
KNOWLEDGE_ORDER = ["gorgeous", "leash", "raviolo", "water", "river", "crowd", "rescue"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place, lure, gear = f["place"], f["lure"], f["gear"]
    outcome = f["outcome"]
    core = (f'Write a short adventure story for a 3-to-5-year-old that includes the words '
            f'"gorgeous", "leash", and "raviolo".')
    if outcome == "contained":
        return [
            core,
            f"Tell a suspenseful cautionary story where a child walking a dog at {place.label} must hold a {gear.label} tight when a tempting raviolo appears.",
            f"Write a gentle rhyming adventure where danger flashes for one moment, a grown-up helps, and the ending shows a safer habit.",
        ]
    return [
        core,
        f"Tell a cautionary adventure where a loose hold near {place.edge} lets a dog dash toward a raviolo and scares everyone badly.",
        f"Write a rhyming suspense story that teaches why a leash matters when something delicious appears near danger.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, adult, dog = f["child"], f["adult"], f["dog"]
    place, lure, gear, response = f["place"], f["lure"], f["gear"], f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        ("Who is the story about?",
         f"It is about {child.id}, a child on an adventure walk, {dog.id} the dog, and {child.pronoun('possessive')} {adult.label_word} who keeps them safe."),
        ("What made the walk feel exciting at the start?",
         f"They went to {place.label}, where {place.scene}. That beautiful place made the walk feel like an adventure before the danger appeared."),
        (f"What tempted {dog.id}?",
         f"{dog.id} smelled food from {lure.source} and saw a huge raviolo. The smell was so strong that it made him lunge before he thought."),
        (f"Why did {adult.label_word} warn {child.id}?",
         f"{adult.label_word.capitalize()} knew that {lure.danger_reason.lower()} near {place.edge}. The warning came before the lunge because the grown-up could see the risk coming."),
    ]
    if outcome == "contained":
        qa.append((
            f"How did the {gear.label} help?",
            f"The {gear.label} kept {dog.id} close enough for the grown-up to stop the dash. It turned a dangerous leap into a scary moment that could still be fixed."
        ))
        qa.append((
            f"How did {adult.label_word} save {dog.id}?",
            f"{adult.label_word.capitalize()} {response.qa_text}. Acting fast mattered because the dog had already jumped toward the edge."
        ))
        qa.append((
            "What did the child learn at the end?",
            f"{child.id} learned that a leash is not just for decoration. It is for safety, especially when a quick dog sees something delicious near danger."
        ))
    else:
        qa.append((
            "Did anyone get hurt?",
            f"No, but everyone was badly frightened. The scare felt serious because {dog.id} got right to the edge before the grown-up grabbed him."
        ))
        qa.append((
            "Why did the walk home feel different?",
            f"It felt quiet and heavy instead of adventurous. The near accident showed them how fast a fun outing can turn scary when the hold is loose."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["gear"].tags) | set(f["lure"].tags) | {"rescue"}
    for tag in f["place"].risk_tags:
        if tag == "edge":
            continue
        tags.add(tag)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.tethered_to:
            bits.append(f"tethered_to={e.tethered_to}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams("harbor", "food_cart", "gorgeous_leash", "brace_and_pull",
                "Lina", "girl", "Ravi", "mother", "careful", 0),
    StoryParams("bridge", "vendor_bag", "leash", "scoop_dog",
                "Owen", "boy", "Pip", "father", "thoughtful", 0),
    StoryParams("market", "picnic_plate", "gorgeous_leash", "brace_and_pull",
                "Mira", "girl", "Comet", "mother", "curious", 1),
    StoryParams("harbor", "food_cart", "gorgeous_leash", "scoop_dog",
                "Theo", "boy", "Biscuit", "father", "bold", 1),
    StoryParams("bridge", "food_cart", "gorgeous_leash", "scoop_dog",
                "Lucy", "girl", "Pepper", "mother", "steady", 2),
]


def outcome_of(params: StoryParams) -> str:
    return "contained" if is_contained(
        GEARS[params.gear],
        RESPONSES[params.response],
        PLACES[params.place],
        LURES[params.lure],
        params.patience,
    ) else "scared"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% reasonableness
hazard(P,L) :- place(P), lure(L), danger(P,D), D > 0, intensity(L,I), I > 0.
sensible_gear(G) :- gear(G), gear_sense(G,S), safe_sense_min(M), S >= M.
sensible_response(R) :- response(R), response_sense(R,S), safe_sense_min(M), S >= M.
valid(P,L,G) :- hazard(P,L), sensible_gear(G).

% outcome
severity(V) :- chosen_place(P), chosen_lure(L), patience(T),
               danger(P,D), intensity(L,I), V = D + I + T.
control_bonus(1) :- chosen_gear(G), keeps_close(G).
control_bonus(0) :- chosen_gear(G), not keeps_close(G).
capacity(C) :- chosen_response(R), response_power(R,P), control_bonus(B), C = P + B.
outcome(contained) :- severity(V), capacity(C), C >= V.
outcome(scared) :- severity(V), capacity(C), C < V.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("danger", pid, p.danger))
    for lid, l in LURES.items():
        lines.append(asp.fact("lure", lid))
        lines.append(asp.fact("intensity", lid, l.intensity))
    for gid, g in GEARS.items():
        lines.append(asp.fact("gear", gid))
        lines.append(asp.fact("gear_sense", gid, g.sense))
        if g.keeps_close:
            lines.append(asp.fact("keeps_close", gid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("response_power", rid, r.power))
        lines.append(asp.fact("response_sense", rid, r.sense))
    lines.append(asp.fact("safe_sense_min", SAFE_SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_gears() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_gear/1."))
    return sorted(g for (g,) in asp.atoms(model, "sensible_gear"))


def asp_sensible_responses() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_response/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_response"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_lure", params.lure),
        asp.fact("chosen_gear", params.gear),
        asp.fact("chosen_response", params.response),
        asp.fact("patience", params.patience),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    g1, g2 = set(asp_sensible_gears()), {g.id for g in sensible_gears()}
    if g1 == g2:
        print(f"OK: sensible gears match ({sorted(g1)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible gears: clingo={sorted(g1)} python={sorted(g2)}")

    r1, r2 = set(asp_sensible_responses()), {r.id for r in sensible_responses()}
    if r1 == r2:
        print(f"OK: sensible responses match ({sorted(r1)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(r1)} python={sorted(r2)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
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

    # smoke test normal generation / rendering
    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("\nOK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a dog, a tempting raviolo, and the safety of a leash."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--patience", type=int, choices=[0, 1, 2],
                    help="how long the adults lose before the rescue; higher is riskier")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_child(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and PLACES[args.place].danger <= 0:
        lure = LURES[args.lure] if args.lure else next(iter(LURES.values()))
        raise StoryError(explain_rejection(PLACES[args.place], lure))
    if args.place and args.lure:
        if not hazard_at_risk(PLACES[args.place], LURES[args.lure]):
            raise StoryError(explain_rejection(PLACES[args.place], LURES[args.lure]))
    if args.gear and GEARS[args.gear].sense < SAFE_SENSE_MIN:
        raise StoryError(explain_gear(args.gear))
    if args.response and RESPONSES[args.response].sense < SAFE_SENSE_MIN:
        r = RESPONSES[args.response]
        better = ", ".join(sorted(x.id for x in sensible_responses()))
        raise StoryError(
            f"(Refusing response '{r.id}': it scores too low on common sense "
            f"(sense={r.sense} < {SAFE_SENSE_MIN}). Try: {better}.)"
        )

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.lure is None or c[1] == args.lure)
              and (args.gear is None or c[2] == args.gear)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, lure, gear = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_name, child_gender = _pick_child(rng)
    dog_name = rng.choice([d for d in DOG_NAMES if d.lower() != child_name.lower()])
    adult = args.adult or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    patience = args.patience if args.patience is not None else rng.randint(0, 2)

    return StoryParams(
        place=place,
        lure=lure,
        gear=gear,
        response=response,
        child_name=child_name,
        child_gender=child_gender,
        dog_name=dog_name,
        adult=adult,
        trait=trait,
        patience=patience,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        LURES[params.lure],
        GEARS[params.gear],
        RESPONSES[params.response],
        params.child_name,
        params.child_gender,
        params.dog_name,
        params.adult,
        params.patience,
        params.trait,
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
        print(asp_program("", "#show valid/3.\n#show sensible_gear/1.\n#show sensible_response/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible gears: {', '.join(asp_sensible_gears())}")
        print(f"sensible responses: {', '.join(asp_sensible_responses())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, lure, gear) combos:\n")
        for place, lure, gear in combos:
            print(f"  {place:8} {lure:12} {gear}")
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
            header = f"### {p.child_name} & {p.dog_name}: {p.place}, {p.lure}, {p.gear} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
