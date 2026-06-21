#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/species_marshal_binkie_curiosity_quest_nursery_rhyme.py
==================================================================================

A tiny storyworld about a child who loses a binkie, follows curiosity into a
small detour, and completes a gentle quest with help from a park marshal and a
local animal species. The prose aims for a nursery-rhyme lilt while still being
state-driven and constraint-checked.

Run it
------
    python storyworlds/worlds/gpt-5.4/species_marshal_binkie_curiosity_quest_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/species_marshal_binkie_curiosity_quest_nursery_rhyme.py --place pond --species duck
    python storyworlds/worlds/gpt-5.4/species_marshal_binkie_curiosity_quest_nursery_rhyme.py --spot burrow
    python storyworlds/worlds/gpt-5.4/species_marshal_binkie_curiosity_quest_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/species_marshal_binkie_curiosity_quest_nursery_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4/species_marshal_binkie_curiosity_quest_nursery_rhyme.py --verify
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

_THIS = os.path.abspath(__file__)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(_THIS))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    location: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "lady"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "park_marshal":
            return "marshal"
        if self.type == "mother":
            return "mom"
        if self.type == "father":
            return "dad"
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    path: str
    rhyme: str
    where_found: str
    species_ids: set[str] = field(default_factory=set)
    spot_ids: set[str] = field(default_factory=set)
    distraction_ids: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class SpeciesCfg:
    id: str
    label: str
    phrase: str
    call: str
    step: str
    habitat: set[str] = field(default_factory=set)
    spots: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    cue: str
    found_line: str
    places: set[str] = field(default_factory=set)
    species_ids: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Distraction:
    id: str
    label: str
    phrase: str
    lure: str
    wrong_reason: str
    places: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


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


def _r_loss_sadness(world: World) -> list[str]:
    child = world.get("child")
    binkie = world.get("binkie")
    if binkie.location != "with_child" and ("loss", child.id) not in world.fired:
        world.fired.add(("loss", child.id))
        child.memes["sad"] += 1
        child.memes["need"] += 1
    return []


def _r_curiosity_detour(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["curious"] >= THRESHOLD and child.location == "distracted":
        sig = ("detour", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["steps"] += 1
            child.memes["frustration"] += 1
    return []


def _r_species_help(world: World) -> list[str]:
    child = world.get("child")
    guide = world.get("guide")
    if child.location == "following_guide" and guide.memes["noticed"] >= THRESHOLD:
        sig = ("help", guide.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["hope"] += 1
            child.memes["trust"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="loss_sadness", tag="emotional", apply=_r_loss_sadness),
    Rule(name="curiosity_detour", tag="movement", apply=_r_curiosity_detour),
    Rule(name="species_help", tag="social", apply=_r_species_help),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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
    "meadow": Place(
        id="meadow",
        label="the clover meadow",
        path="along the clover lane",
        rhyme="where bees hummed low and daisies swayed",
        where_found="beside a tuft of clover",
        species_ids={"lamb", "mouse"},
        spot_ids={"clover", "burrow"},
        distraction_ids={"feather", "pebble"},
        tags={"meadow"},
    ),
    "pond": Place(
        id="pond",
        label="the duck pond",
        path="round the silver pond",
        rhyme="where reeds bowed down and ripples played",
        where_found="by the reeds at the water's edge",
        species_ids={"duck", "frog"},
        spot_ids={"reeds", "lily"},
        distraction_ids={"ribbon", "pebble"},
        tags={"pond"},
    ),
    "orchard": Place(
        id="orchard",
        label="the apple orchard",
        path="under the apple boughs",
        rhyme="where shadows hopped and apples swayed",
        where_found="under a basket near the tree roots",
        species_ids={"sparrow", "mouse"},
        spot_ids={"basket", "roots"},
        distraction_ids={"feather", "ribbon"},
        tags={"orchard"},
    ),
}

SPECIES = {
    "duck": SpeciesCfg(
        id="duck",
        label="duck",
        phrase="a waddling duck",
        call="quack-quack",
        step="waddled in a bobbing track",
        habitat={"pond"},
        spots={"reeds", "lily"},
        tags={"duck", "species"},
    ),
    "frog": SpeciesCfg(
        id="frog",
        label="frog",
        phrase="a springy frog",
        call="ribbit-ribbit",
        step="sprang with little velvet hops",
        habitat={"pond"},
        spots={"reeds", "lily"},
        tags={"frog", "species"},
    ),
    "lamb": SpeciesCfg(
        id="lamb",
        label="lamb",
        phrase="a woolly lamb",
        call="baa-baa",
        step="trotted soft on cloudy feet",
        habitat={"meadow"},
        spots={"clover"},
        tags={"lamb", "species"},
    ),
    "mouse": SpeciesCfg(
        id="mouse",
        label="mouse",
        phrase="a whiskered mouse",
        call="squeak-squeak",
        step="scurried in a tiny streak",
        habitat={"meadow", "orchard"},
        spots={"burrow", "roots", "basket"},
        tags={"mouse", "species"},
    ),
    "sparrow": SpeciesCfg(
        id="sparrow",
        label="sparrow",
        phrase="a chirping sparrow",
        call="chirp-chirp",
        step="fluttered in a skipping arc",
        habitat={"orchard"},
        spots={"basket", "roots"},
        tags={"sparrow", "species"},
    ),
}

SPOTS = {
    "clover": Spot(
        id="clover",
        label="clover patch",
        phrase="the clover patch",
        cue="a soft green patch where clover curled",
        found_line="There, in the clover, lay the binkie snug and still.",
        places={"meadow"},
        species_ids={"lamb"},
        tags={"clover"},
    ),
    "burrow": Spot(
        id="burrow",
        label="burrow mouth",
        phrase="the little burrow mouth",
        cue="a round brown door in the earth",
        found_line="There, by the burrow mouth, the binkie peeked like a moon.",
        places={"meadow"},
        species_ids={"mouse"},
        tags={"burrow"},
    ),
    "reeds": Spot(
        id="reeds",
        label="reed bed",
        phrase="the bendy reeds",
        cue="a hush of reeds whispering by the shore",
        found_line="There, by the reeds, the binkie rested above the mud.",
        places={"pond"},
        species_ids={"duck", "frog"},
        tags={"reeds"},
    ),
    "lily": Spot(
        id="lily",
        label="lily pad",
        phrase="the lily pads",
        cue="a ring of lily pads with shiny drops",
        found_line="There, near the lily pads, the binkie waited on a dry stone.",
        places={"pond"},
        species_ids={"duck", "frog"},
        tags={"lily"},
    ),
    "basket": Spot(
        id="basket",
        label="apple basket",
        phrase="the tilted apple basket",
        cue="a wicker basket smelling faintly sweet",
        found_line="There, under the basket rim, the binkie glowed pale and safe.",
        places={"orchard"},
        species_ids={"sparrow", "mouse"},
        tags={"basket"},
    ),
    "roots": Spot(
        id="roots",
        label="tree roots",
        phrase="the twisty tree roots",
        cue="old roots curling like sleepy fingers",
        found_line="There, among the roots, the binkie lay where shadows kept it cool.",
        places={"orchard"},
        species_ids={"sparrow", "mouse"},
        tags={"roots"},
    ),
}

DISTRACTIONS = {
    "feather": Distraction(
        id="feather",
        label="feather",
        phrase="a silver feather",
        lure="It twirled so prettily that curiosity tugged the child that way first.",
        wrong_reason="The feather was light and lovely, but it was not the missing binkie.",
        places={"meadow", "orchard"},
        tags={"feather"},
    ),
    "pebble": Distraction(
        id="pebble",
        label="pebble",
        phrase="a shiny pebble",
        lure="It winked like a tiny star, and curiosity sent little feet skipping after it.",
        wrong_reason="The pebble could sparkle, but it could not soothe sleepy lips.",
        places={"meadow", "pond"},
        tags={"pebble"},
    ),
    "ribbon": Distraction(
        id="ribbon",
        label="ribbon",
        phrase="a red ribbon",
        lure="It fluttered and flapped, so curiosity chased its dancing tail.",
        wrong_reason="The ribbon was bright, but it was only ribbon, not a binkie at all.",
        places={"pond", "orchard"},
        tags={"ribbon"},
    ),
}

MARSHALS = {
    "maple": {
        "name": "Marshal Maple",
        "line": "with a sash of leaves and a patient smile",
        "tags": {"marshal"},
    },
    "moss": {
        "name": "Marshal Moss",
        "line": "with kind boots and a whistle tucked away",
        "tags": {"marshal"},
    },
}

GIRL_NAMES = ["Mina", "Lulu", "Tess", "Poppy", "Nell", "Daisy"]
BOY_NAMES = ["Pip", "Ollie", "Bram", "Toby", "Ned", "Milo"]
TRAITS = ["curious", "gentle", "bouncy", "bright-eyed", "sleepy", "cheerful"]


def valid_combo(place_id: str, species_id: str, spot_id: str, distraction_id: str) -> bool:
    place = PLACES[place_id]
    species = SPECIES[species_id]
    spot = SPOTS[spot_id]
    distraction = DISTRACTIONS[distraction_id]
    if species_id not in place.species_ids:
        return False
    if spot_id not in place.spot_ids:
        return False
    if distraction_id not in place.distraction_ids:
        return False
    if place_id not in species.habitat:
        return False
    if spot_id not in species.spots:
        return False
    if place_id not in spot.places:
        return False
    if species_id not in spot.species_ids:
        return False
    if place_id not in distraction.places:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place_id in sorted(PLACES):
        for species_id in sorted(SPECIES):
            for spot_id in sorted(SPOTS):
                for distraction_id in sorted(DISTRACTIONS):
                    if valid_combo(place_id, species_id, spot_id, distraction_id):
                        out.append((place_id, species_id, spot_id, distraction_id))
    return out


def explain_rejection(place_id: str, species_id: str, spot_id: str, distraction_id: str) -> str:
    place = PLACES.get(place_id)
    species = SPECIES.get(species_id)
    spot = SPOTS.get(spot_id)
    distraction = DISTRACTIONS.get(distraction_id)
    if place and species and species_id not in place.species_ids:
        return (f"(No story: {species.label} does not belong in {place.label}, so that species "
                f"cannot guide the quest there.)")
    if place and spot and spot_id not in place.spot_ids:
        return (f"(No story: {spot.phrase} is not a hiding place in {place.label}, so the binkie "
                f"would not plausibly be found there.)")
    if place and distraction and distraction_id not in place.distraction_ids:
        return (f"(No story: {distraction.phrase} is not part of the little scene in {place.label}, "
                f"so the curiosity detour would feel ungrounded.)")
    if species and spot and spot_id not in species.spots:
        return (f"(No story: a {species.label} would not honestly lead to {spot.phrase}. Pick a spot "
                f"that this species can notice.)")
    return "(No story: those choices do not make one coherent quest.)"


def predict_found(place_id: str, species_id: str, spot_id: str, distraction_id: str) -> dict:
    ok = valid_combo(place_id, species_id, spot_id, distraction_id)
    return {
        "coherent": ok,
        "detour": ok,
        "resolved": ok,
    }


def introduce(world: World, child: Entity, marshal: Entity) -> None:
    place = world.place
    world.say(
        f"In {place.label}, {place.rhyme}, little {child.id} skipped with {child.pronoun('possessive')} "
        f"binkie till the breeze felt light and mild."
    )
    world.say(
        f"Near the gate stood {marshal.id}, the park marshal, {marshal.attrs['line']}."
    )


def lose_binkie(world: World, child: Entity, binkie: Entity) -> None:
    binkie.location = "lost"
    child.memes["curious"] += 1
    child.meters["quest_steps"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But hop and hum and heel-toe swing made the binkie slip away. "
        f"When {child.id} touched {child.pronoun('possessive')} cheek, the binkie was gone, and the game turned gray."
    )


def marshal_starts_quest(world: World, child: Entity, marshal: Entity, species: SpeciesCfg) -> None:
    child.memes["hope"] += 1
    marshal.memes["care"] += 1
    world.say(
        f'"Do not droop, dear duckling," said {marshal.id}. "Let curiosity be kind. '
        f'We will make a quest, step by step, and ask which species saw where it went."'
    )
    world.say(
        f'{marshal.id} pointed softly. "Hark -- {species.phrase} may help."'
    )


def detour(world: World, child: Entity, distraction: Distraction) -> None:
    child.location = "distracted"
    child.memes["curious"] += 1
    propagate(world, narrate=False)
    world.say(
        f"First {child.id} spotted {distraction.phrase}. {distraction.lure}"
    )
    world.say(
        f"{child.id} stooped, blinked, and shook {child.pronoun('possessive')} head. {distraction.wrong_reason}"
    )


def meet_species(world: World, child: Entity, guide: Entity, species: SpeciesCfg, spot: Spot) -> None:
    guide.memes["noticed"] += 1
    child.location = "following_guide"
    propagate(world, narrate=False)
    world.say(
        f"Then came {species.phrase}: {species.call}! {species.call}! It {species.step}."
    )
    world.say(
        f"{child.id} watched with wide eyes. The little helper seemed to know {spot.cue}."
    )
    world.say(
        f'"What a fine species friend," whispered {child.id}, and followed close behind.'
    )


def find_binkie(world: World, child: Entity, marshal: Entity, binkie: Entity, spot: Spot) -> None:
    binkie.location = "found"
    child.memes["sad"] = 0.0
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    child.location = "found"
    world.say(spot.found_line)
    world.say(
        f"{marshal.id} lifted it high, dusted it clean, and laid the binkie back into {child.id}'s hands."
    )


def resolve(world: World, child: Entity, marshal: Entity, species: SpeciesCfg) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"{child.id} kissed the binkie once and smiled. \"My quest is done,\" {child.pronoun()} said."
    )
    world.say(
        f"{marshal.id} laughed a little laugh. \"Curiosity can wander,\" {marshal.pronoun()} said, "
        f"\"but with calm steps and a helpful species, it can wander home as well.\""
    )
    world.say(
        f"So round they went {world.place.path}, child and marshal side by side, while {species.label} sounds "
        f"trailed after them, and the meadow of the heart felt wide."
    )


def tell(
    place: Place,
    species_cfg: SpeciesCfg,
    spot: Spot,
    distraction: Distraction,
    *,
    child_name: str = "Mina",
    child_gender: str = "girl",
    marshal_key: str = "maple",
    parent_type: str = "mother",
    trait: str = "curious",
) -> World:
    world = World(place)
    marshal_data = MARSHALS[marshal_key]

    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
        location="with_binkie",
    ))
    marshal = world.add(Entity(
        id=marshal_data["name"],
        kind="character",
        type="park_marshal",
        role="marshal",
        attrs={"line": marshal_data["line"]},
        tags=set(marshal_data["tags"]),
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    guide = world.add(Entity(
        id="guide",
        kind="character",
        type="animal",
        role="guide",
        label=species_cfg.label,
        phrase=species_cfg.phrase,
        tags=set(species_cfg.tags),
    ))
    binkie = world.add(Entity(
        id="binkie",
        kind="thing",
        type="binkie",
        label="binkie",
        phrase="the soft moon-round binkie",
        owner=child.id,
        location="with_child",
        tags={"binkie"},
    ))

    introduce(world, child, marshal)
    world.para()
    lose_binkie(world, child, binkie)
    marshal_starts_quest(world, child, marshal, species_cfg)
    detour(world, child, distraction)
    world.para()
    meet_species(world, child, guide, species_cfg, spot)
    find_binkie(world, child, marshal, binkie, spot)
    resolve(world, child, marshal, species_cfg)

    world.facts.update(
        child=child,
        marshal=marshal,
        parent=parent,
        guide=guide,
        binkie=binkie,
        place=place,
        species_cfg=species_cfg,
        spot=spot,
        distraction=distraction,
        quest_done=binkie.location == "found",
        detour_taken=child.meters["steps"] >= THRESHOLD,
        learned_species=True,
    )
    return world


@dataclass
class StoryParams:
    place: str
    species: str
    spot: str
    distraction: str
    child_name: str
    child_gender: str
    marshal: str
    parent: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    species_cfg = f["species_cfg"]
    return [
        'Write a nursery-rhyme style story for a 3-to-5-year-old that includes the words '
        '"species", "marshal", and "binkie".',
        f"Tell a gentle quest where {child.id} loses a binkie in {place.label}, follows curiosity into a "
        f"small wrong turn, and is helped by a {species_cfg.label}.",
        f"Write a sing-song story in which a park marshal helps a child ask what species noticed the "
        f"missing binkie and bring it safely home.",
    ]


KNOWLEDGE = {
    "species": [
        ("What does species mean?",
         "Species is a word for a kind of living thing, like ducks, frogs, or mice. "
         "Animals in one species are the same kind of creature.")
    ],
    "marshal": [
        ("What is a marshal?",
         "A marshal is a person who helps keep a place orderly and safe. In a park, a marshal can guide people and help when something is lost.")
    ],
    "binkie": [
        ("What is a binkie?",
         "A binkie is a soft comfort object or pacifier some little children like to keep close. It helps them feel calm and cozy.")
    ],
    "quest": [
        ("What is a quest?",
         "A quest is a little journey with a purpose. You go looking for something important and keep trying until you find it.")
    ],
    "curiosity": [
        ("What is curiosity?",
         "Curiosity is the feeling that makes you want to look, ask, and learn. It can help you discover things when you use it carefully.")
    ],
    "duck": [
        ("Why do ducks like ponds?",
         "Ducks like ponds because they can swim there and look for food by the water. Their webbed feet help them move through the water easily.")
    ],
    "frog": [
        ("Where do frogs like to hide?",
         "Frogs often hide near water, reeds, and leaves. Those wet places help keep their skin comfortable.")
    ],
    "lamb": [
        ("What does a lamb sound like?",
         "A lamb says baa-baa. Lambs are young sheep with soft wool.")
    ],
    "mouse": [
        ("Why do mice notice little places?",
         "Mice are small and quick, so they can slip near roots, baskets, and burrows. They often notice tiny hiding spots.")
    ],
    "sparrow": [
        ("What is a sparrow?",
         "A sparrow is a small bird that chirps and hops. It often lives near trees and gardens.")
    ],
}

KNOWLEDGE_ORDER = [
    "species", "marshal", "binkie", "quest", "curiosity",
    "duck", "frog", "lamb", "mouse", "sparrow",
]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    marshal = f["marshal"]
    species_cfg = f["species_cfg"]
    place = f["place"]
    spot = f["spot"]
    distraction = f["distraction"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about little {child.id}, {marshal.id} the park marshal, and a helpful {species_cfg.label}. "
            f"Together they go on a small quest to find the missing binkie."
        ),
        (
            f"Why did {child.id} need help?",
            f"{child.id} was skipping and playing when the binkie slipped away in {place.label}. "
            f"That loss made the child sad, so the marshal started a calm search."
        ),
        (
            "How did curiosity change the middle of the story?",
            f"Curiosity first pulled {child.id} toward {distraction.phrase}, which caused a small detour. "
            f"But after that wrong guess, curiosity turned into careful looking, and the quest could continue."
        ),
        (
            f"How did the {species_cfg.label} help?",
            f"The {species_cfg.label} led {child.id} toward {spot.phrase}. "
            f"That mattered because this species belongs in that place and could honestly notice the hiding spot."
        ),
        (
            "How did the story end?",
            f"The binkie was found, cleaned, and placed back into {child.id}'s hands. "
            f"The ending image shows the change: the child walks home beside the marshal feeling calm again."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"species", "marshal", "binkie", "quest", "curiosity", f["species_cfg"].id}
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.location:
            bits.append(f"location={e.location}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:14} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="pond",
        species="duck",
        spot="reeds",
        distraction="pebble",
        child_name="Mina",
        child_gender="girl",
        marshal="maple",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        place="pond",
        species="frog",
        spot="lily",
        distraction="ribbon",
        child_name="Pip",
        child_gender="boy",
        marshal="moss",
        parent="father",
        trait="bright-eyed",
    ),
    StoryParams(
        place="meadow",
        species="lamb",
        spot="clover",
        distraction="feather",
        child_name="Lulu",
        child_gender="girl",
        marshal="maple",
        parent="mother",
        trait="gentle",
    ),
    StoryParams(
        place="meadow",
        species="mouse",
        spot="burrow",
        distraction="pebble",
        child_name="Ned",
        child_gender="boy",
        marshal="moss",
        parent="father",
        trait="bouncy",
    ),
    StoryParams(
        place="orchard",
        species="sparrow",
        spot="basket",
        distraction="ribbon",
        child_name="Tess",
        child_gender="girl",
        marshal="maple",
        parent="mother",
        trait="cheerful",
    ),
]


ASP_RULES = r"""
species_ok(P, S) :- place_has_species(P, S), habitat(S, P).
spot_ok(P, T) :- place_has_spot(P, T), spot_place(T, P).
distraction_ok(P, D) :- place_has_distraction(P, D), distraction_place(D, P).
guide_to(S, T) :- species_spot(S, T), spot_species(T, S).

valid(P, S, T, D) :- species_ok(P, S), spot_ok(P, T), distraction_ok(P, D), guide_to(S, T).

quest_resolves(P, S, T, D) :- valid(P, S, T, D).
#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for s in sorted(place.species_ids):
            lines.append(asp.fact("place_has_species", place_id, s))
        for t in sorted(place.spot_ids):
            lines.append(asp.fact("place_has_spot", place_id, t))
        for d in sorted(place.distraction_ids):
            lines.append(asp.fact("place_has_distraction", place_id, d))
    for species_id, species in SPECIES.items():
        lines.append(asp.fact("species", species_id))
        for p in sorted(species.habitat):
            lines.append(asp.fact("habitat", species_id, p))
        for t in sorted(species.spots):
            lines.append(asp.fact("species_spot", species_id, t))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        for p in sorted(spot.places):
            lines.append(asp.fact("spot_place", spot_id, p))
        for s in sorted(spot.species_ids):
            lines.append(asp.fact("spot_species", spot_id, s))
    for dis_id, dis in DISTRACTIONS.items():
        lines.append(asp.fact("distraction", dis_id))
        for p in sorted(dis.places):
            lines.append(asp.fact("distraction_place", dis_id, p))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    smoke_cases = list(CURATED[:2])
    try:
        for params in smoke_cases:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("Generated story was empty.")
            if "binkie" not in sample.story.lower():
                raise StoryError("Generated story did not contain 'binkie'.")
        print(f"OK: smoke-tested normal generation on {len(smoke_cases)} curated samples.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme storyworld: a lost binkie, a park marshal, and a species-led quest."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--species", choices=sorted(SPECIES))
    ap.add_argument("--spot", choices=sorted(SPOTS))
    ap.add_argument("--distraction", choices=sorted(DISTRACTIONS))
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--marshal", choices=sorted(MARSHALS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.species and args.spot and args.distraction:
        if not valid_combo(args.place, args.species, args.spot, args.distraction):
            raise StoryError(explain_rejection(args.place, args.species, args.spot, args.distraction))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.species is None or combo[1] == args.species)
        and (args.spot is None or combo[2] == args.spot)
        and (args.distraction is None or combo[3] == args.distraction)
    ]
    if not combos:
        p = args.place or next(iter(PLACES))
        s = args.species or next(iter(SPECIES))
        t = args.spot or next(iter(SPOTS))
        d = args.distraction or next(iter(DISTRACTIONS))
        raise StoryError(explain_rejection(p, s, t, d))

    place_id, species_id, spot_id, distraction_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    marshal = args.marshal or rng.choice(sorted(MARSHALS))
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        species=species_id,
        spot=spot_id,
        distraction=distraction_id,
        child_name=child_name,
        child_gender=child_gender,
        marshal=marshal,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.species not in SPECIES:
        raise StoryError(f"(Invalid species: {params.species})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Invalid spot: {params.spot})")
    if params.distraction not in DISTRACTIONS:
        raise StoryError(f"(Invalid distraction: {params.distraction})")
    if params.marshal not in MARSHALS:
        raise StoryError(f"(Invalid marshal: {params.marshal})")
    if not valid_combo(params.place, params.species, params.spot, params.distraction):
        raise StoryError(explain_rejection(params.place, params.species, params.spot, params.distraction))

    world = tell(
        PLACES[params.place],
        SPECIES[params.species],
        SPOTS[params.spot],
        DISTRACTIONS[params.distraction],
        child_name=params.child_name,
        child_gender=params.child_gender,
        marshal_key=params.marshal,
        parent_type=params.parent,
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
        print(f"{len(combos)} valid (place, species, spot, distraction) combos:\n")
        for place_id, species_id, spot_id, distraction_id in combos:
            print(f"  {place_id:8} {species_id:8} {spot_id:8} {distraction_id}")
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
            header = f"### {p.child_name}: {p.place}, {p.species}, {p.spot}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
