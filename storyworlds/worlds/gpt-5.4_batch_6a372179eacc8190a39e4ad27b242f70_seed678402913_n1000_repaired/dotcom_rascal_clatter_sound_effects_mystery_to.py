#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dotcom_rascal_clatter_sound_effects_mystery_to.py
=============================================================================

A small folk-tale storyworld about a night noise, a mystery to solve, and the
moment a child learns that not every clatter in the dark comes from a spirit.

The fixed ingredients of the domain are:
- a moonlit village place,
- a child and an elder,
- Dotcom the village cat,
- a culprit that makes a noisy mess,
- a clue that can truly point to that culprit,
- and a gentle remedy that fits the culprit's nature.

The world model prefers a real mystery with a fair solution:
a clue must honestly match the culprit, and the chosen fix must really stop the
rascal from returning. The result should read like a complete tale, not a bag
of swapped nouns.

Run it
------
    python storyworlds/worlds/gpt-5.4/dotcom_rascal_clatter_sound_effects_mystery_to.py
    python storyworlds/worlds/gpt-5.4/dotcom_rascal_clatter_sound_effects_mystery_to.py --culprit monkey --clue banana_peels
    python storyworlds/worlds/gpt-5.4/dotcom_rascal_clatter_sound_effects_mystery_to.py --culprit goat --fix fruit_basket
    python storyworlds/worlds/gpt-5.4/dotcom_rascal_clatter_sound_effects_mystery_to.py --all
    python storyworlds/worlds/gpt-5.4/dotcom_rascal_clatter_sound_effects_mystery_to.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/dotcom_rascal_clatter_sound_effects_mystery_to.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so go up three levels to
# reach storyworlds/ and let "results" resolve from there.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "mother", "aunt"}
        male = {"boy", "man", "grandfather", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "cat":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    stores: str
    noisy_object: str
    object_phrase: str
    sound: str
    mood: str
    invites: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    phrase: str
    move_sound: str
    taste: str
    clue_ids: set[str] = field(default_factory=set)
    fix_ids: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    reading: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    action: str
    proof: str
    tags: set[str] = field(default_factory=set)


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


def _r_noise_spreads(world: World) -> list[str]:
    out: list[str] = []
    culprit = world.entities.get("culprit")
    place = world.entities.get("place")
    child = world.entities.get("child")
    elder = world.entities.get("elder")
    if not culprit or not place or culprit.meters["rummaging"] < THRESHOLD:
        return out
    sig = ("noise", culprit.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    place.meters["noise"] += 1
    child.memes["fear"] += 1
    elder.memes["concern"] += 1
    out.append("__noise__")
    return out


def _r_clue_teaches(world: World) -> list[str]:
    out: list[str] = []
    clue = world.entities.get("clue")
    child = world.entities.get("child")
    if not clue or clue.meters["noticed"] < THRESHOLD:
        return out
    sig = ("noticed", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    out.append("__clue__")
    return out


def _r_solution_calms(world: World) -> list[str]:
    out: list[str] = []
    fix = world.entities.get("fix")
    culprit = world.entities.get("culprit")
    child = world.entities.get("child")
    elder = world.entities.get("elder")
    place = world.entities.get("place")
    if not fix or fix.meters["used"] < THRESHOLD:
        return out
    sig = ("calm", fix.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    culprit.meters["kept_out"] += 1
    place.meters["noise"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    elder.memes["relief"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="noise_spreads", tag="physical", apply=_r_noise_spreads),
    Rule(name="clue_teaches", tag="epistemic", apply=_r_clue_teaches),
    Rule(name="solution_calms", tag="social", apply=_r_solution_calms),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


PLACES = {
    "granary": Place(
        id="granary",
        label="granary",
        phrase="the old granary beside the millet field",
        stores="sacks of millet and jars of beans",
        noisy_object="pot_lids",
        object_phrase="a string of tin pot lids hanging by the door",
        sound="Clatter-clatter! Ting-ting-ting!",
        mood="The moon laid a pale stripe across the yard.",
        invites={"goat", "monkey"},
        tags={"granary", "grain"},
    ),
    "tea_shed": Place(
        id="tea_shed",
        label="tea shed",
        phrase="the tea shed behind the steaming kitchen",
        stores="bundles of dried tea leaves and sweet fruit peels",
        noisy_object="tea_trays",
        object_phrase="three round tea trays stacked on a stool",
        sound="Clack-clack! Clatter!",
        mood="The night air smelled of mint and woodsmoke.",
        invites={"monkey", "magpie"},
        tags={"shed", "tea"},
    ),
    "lantern_house": Place(
        id="lantern_house",
        label="lantern house",
        phrase="the little lantern house near the well",
        stores="oil jars, broom handles, and polished brass cups",
        noisy_object="brass_cups",
        object_phrase="a row of bright brass cups on a narrow shelf",
        sound="Ting! Ting-ting! Clatter!",
        mood="Fireflies winked near the well like tiny green beads.",
        invites={"goat", "magpie"},
        tags={"lantern", "well"},
    ),
}

CULPRITS = {
    "goat": Culprit(
        id="goat",
        label="goat",
        phrase="a hungry white goat",
        move_sound="clip-clop",
        taste="bean leaves",
        clue_ids={"hoofprints", "chewed_rope"},
        fix_ids={"latch_gate"},
        tags={"goat", "hoof"},
    ),
    "monkey": Culprit(
        id="monkey",
        label="monkey",
        phrase="a nimble monkey",
        move_sound="skitter-skip",
        taste="sweet fruit",
        clue_ids={"banana_peels", "tail_swish_marks"},
        fix_ids={"fruit_basket"},
        tags={"monkey", "fruit"},
    ),
    "magpie": Culprit(
        id="magpie",
        label="magpie",
        phrase="a glossy black-and-white magpie",
        move_sound="flutter-flap",
        taste="bright shiny things",
        clue_ids={"black_feather", "silver_thread"},
        fix_ids={"ribbon_perch"},
        tags={"magpie", "bird"},
    ),
}

CLUES = {
    "hoofprints": Clue(
        id="hoofprints",
        label="hoofprints",
        phrase="two neat hoofprints in the dust",
        reading="Only a creature with hard little hooves could have left those marks.",
        tags={"hoofprint"},
    ),
    "chewed_rope": Clue(
        id="chewed_rope",
        label="chewed rope",
        phrase="a rope end frayed with fresh tooth marks",
        reading="The teeth marks were low to the ground, as if some greedy mouth had nibbled there.",
        tags={"rope"},
    ),
    "banana_peels": Clue(
        id="banana_peels",
        label="banana peels",
        phrase="two curled banana peels under the stool",
        reading="Someone that loved sweet fruit had finished a secret supper there.",
        tags={"banana"},
    ),
    "tail_swish_marks": Clue(
        id="tail_swish_marks",
        label="tail swish marks",
        phrase="thin swish marks drawn through the dust",
        reading="Something quick had balanced on the stool and whisked its tail as it turned.",
        tags={"tail"},
    ),
    "black_feather": Clue(
        id="black_feather",
        label="black feather",
        phrase="a black feather caught in the door crack",
        reading="A feather does not belong to goat or monkey, so the night visitor must have flown.",
        tags={"feather"},
    ),
    "silver_thread": Clue(
        id="silver_thread",
        label="silver thread",
        phrase="a silver thread missing from an old festival tassel",
        reading="Only a bird that loved shiny bits would trouble itself over such a thing.",
        tags={"silver"},
    ),
}

FIXES = {
    "latch_gate": Fix(
        id="latch_gate",
        label="latch the gate",
        phrase="a wooden bar across the low gate",
        action="set a wooden bar across the low gate and tied the feed basket farther away",
        proof="In the morning the bar still held firm, and the pots were quiet.",
        tags={"gate", "bar"},
    ),
    "fruit_basket": Fix(
        id="fruit_basket",
        label="set a fruit basket outside",
        phrase="a basket of overripe fruit beneath the fig tree",
        action="set a basket of overripe fruit beneath the fig tree, away from the trays",
        proof="At dawn the basket was empty, but the shed stood neat and still.",
        tags={"fruit", "basket"},
    ),
    "ribbon_perch": Fix(
        id="ribbon_perch",
        label="hang a ribbon perch",
        phrase="a willow perch hung with bright ribbons by the well",
        action="hung a willow perch with bright ribbons by the well, away from the cups",
        proof="By sunrise a magpie sang from the perch, and every brass cup shone untouched.",
        tags={"ribbon", "perch"},
    ),
}


def culprit_matches_clue(culprit_id: str, clue_id: str) -> bool:
    culprit = CULPRITS[culprit_id]
    return clue_id in culprit.clue_ids


def place_allows_culprit(place_id: str, culprit_id: str) -> bool:
    return culprit_id in PLACES[place_id].invites


def fix_matches_culprit(culprit_id: str, fix_id: str) -> bool:
    culprit = CULPRITS[culprit_id]
    return fix_id in culprit.fix_ids


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for culprit_id in CULPRITS:
            if not place_allows_culprit(place_id, culprit_id):
                continue
            for clue_id in CLUES:
                if not culprit_matches_clue(culprit_id, clue_id):
                    continue
                for fix_id in FIXES:
                    if fix_matches_culprit(culprit_id, fix_id):
                        combos.append((place_id, culprit_id, clue_id, fix_id))
    return combos


@dataclass
class StoryParams:
    place: str
    culprit: str
    clue: str
    fix: str
    child_name: str
    child_gender: str
    elder_type: str
    child_trait: str
    seed: Optional[int] = None


CHILD_NAMES = {
    "girl": ["Lina", "Mei", "Anya", "Suri", "Tala", "Nila", "Asha", "Rina"],
    "boy": ["Taro", "Kiran", "Beni", "Ivo", "Milo", "Hari", "Ren", "Pavel"],
}
CHILD_TRAITS = ["patient", "bright-eyed", "quiet", "curious", "careful", "steadfast"]


def _do_rummage(world: World) -> None:
    culprit = world.get("culprit")
    clue = world.get("clue")
    culprit.meters["rummaging"] += 1
    clue.meters["left_behind"] += 1
    propagate(world, narrate=False)


def predict_mystery(world: World, clue_id: str) -> dict:
    sim = world.copy()
    _do_rummage(sim)
    clue = sim.get("clue")
    place = sim.get("place")
    child = sim.get("child")
    return {
        "noise": place.meters["noise"] >= THRESHOLD,
        "fear": child.memes["fear"] >= THRESHOLD,
        "clue_present": clue.meters["left_behind"] >= THRESHOLD,
        "clue_id": clue_id,
    }


def introduce(world: World, child: Entity, elder: Entity, place: Place) -> None:
    world.say(
        f"In a village where people still told stories beside the cooking fire, "
        f"there lived a {child.attrs.get('trait', 'curious')} child named {child.id}."
    )
    world.say(
        f"{child.id} slept in a small house with {child.pronoun('possessive')} "
        f"{elder.label_word}, and near their door stood {place.phrase} full of {place.stores}."
    )
    world.say(place.mood)


def first_noise(world: World, child: Entity, elder: Entity, place: Place) -> None:
    world.say(
        f"One night, when the village dogs had curled their tails around their noses, "
        f"a sudden sound leapt from the dark: \"{place.sound}\""
    )
    world.say(
        f"{child.id} sat up at once. Even Dotcom, the striped village cat, lifted his head."
    )
    world.say(
        f'"Did you hear that?" whispered {child.id}. "{place.label.capitalize()} ghosts do not use '
        f'{place.noisy_object.replace("_", " ")}, do they?"'
    )
    elder_word = elder.label_word
    world.say(
        f'{elder_word.capitalize()} took the lamp and listened. "Every clatter has a cause," '
        f'{elder.pronoun()} said. "Let us find the truth before fear grows tall."'
    )


def dotcom_joins(world: World, child: Entity) -> None:
    dotcom = world.get("dotcom")
    dotcom.memes["alert"] += 1
    child.memes["trust"] += 1
    world.say(
        f"Dotcom gave a small \"mrrp\" and slipped ahead with his tail straight up, as if he, too, meant to solve the mystery."
    )


def search_place(world: World, child: Entity, elder: Entity, place: Place, clue: Clue) -> None:
    pred = predict_mystery(world, clue.id)
    world.facts["predicted_noise"] = pred["noise"]
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f"They walked into the yard softly. The lamp showed {place.object_phrase}, all trembling from the last knock."
    )
    world.say(
        f"Near the door, {child.id} found {clue.phrase}."
    )
    ent = world.get("clue")
    ent.meters["noticed"] += 1
    propagate(world, narrate=False)


def reason_out(world: World, child: Entity, elder: Entity, clue: Clue, culprit: Culprit) -> None:
    child.memes["wonder"] += 1
    child.memes["certainty"] += 1
    elder.memes["pride"] += 1
    world.say(
        f"{child.id} bent close and thought hard. {clue.reading}"
    )
    world.say(
        f'"Then it was no ghost," said {child.id}. "It was {culprit.phrase}, the rascal!"'
    )
    world.say(
        f'{elder.label_word.capitalize()} smiled. "A mystery grows small when the right eyes look at it."'
    )


def reveal(world: World, culprit: Culprit, place: Place) -> None:
    culprit_ent = world.get("culprit")
    culprit_ent.meters["seen"] += 1
    world.say(
        f"Just then came a little {culprit.move_sound} from the shadow, and out peeped {culprit.phrase}."
    )
    world.say(
        f"It gave the hanging things one more nudge -- \"{place.sound}\" -- and then froze, caught in the lamp glow."
    )


def fix_problem(world: World, child: Entity, elder: Entity, fix: Fix) -> None:
    fix_ent = world.get("fix")
    fix_ent.meters["used"] += 1
    propagate(world, narrate=False)
    child.memes["care"] += 1
    world.say(
        f"They did not shout, and they did not throw stones. Instead, they {fix.action}."
    )
    world.say(
        f'"Let us be wiser than the rascal," said {elder.label_word}.'
    )


def ending(world: World, child: Entity, elder: Entity, fix: Fix, culprit: Culprit) -> None:
    child.memes["lesson"] += 1
    child.memes["relief"] += 1
    world.say(fix.proof)
    world.say(
        f"After that night, whenever a strange sound hopped through the dark, {child.id} listened before guessing."
    )
    world.say(
        f"And if Dotcom heard so much as a spoon whisper, he twitched his ears as if to say that even a rascal leaves a trail for patient people."
    )
    world.say(
        f"So the village remembered this: a loud clatter may start a tale, but calm eyes and a kind plan finish it."
    )


def tell(
    place: Place,
    culprit_cfg: Culprit,
    clue_cfg: Clue,
    fix_cfg: Fix,
    child_name: str = "Lina",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
    child_trait: str = "curious",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        attrs={"trait": child_trait},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label="the elder",
        role="elder",
    ))
    dotcom = world.add(Entity(
        id="dotcom",
        kind="character",
        type="cat",
        label="Dotcom",
        role="helper",
        tags={"cat", "dotcom"},
    ))
    place_ent = world.add(Entity(
        id="place",
        type="place",
        label=place.label,
        phrase=place.phrase,
        tags=set(place.tags),
    ))
    culprit = world.add(Entity(
        id="culprit",
        type=culprit_cfg.id,
        label=culprit_cfg.label,
        phrase=culprit_cfg.phrase,
        tags=set(culprit_cfg.tags),
    ))
    clue = world.add(Entity(
        id="clue",
        type="clue",
        label=clue_cfg.label,
        phrase=clue_cfg.phrase,
        tags=set(clue_cfg.tags),
    ))
    fix = world.add(Entity(
        id="fix",
        type="fix",
        label=fix_cfg.label,
        phrase=fix_cfg.phrase,
        tags=set(fix_cfg.tags),
    ))

    introduce(world, child, elder, place)
    world.para()
    _do_rummage(world)
    first_noise(world, child, elder, place)
    dotcom_joins(world)
    world.para()
    search_place(world, child, elder, place, clue_cfg)
    reason_out(world, child, elder, clue_cfg, culprit_cfg)
    reveal(world, culprit_cfg, place)
    world.para()
    fix_problem(world, child, elder, fix_cfg)
    ending(world, child, elder, fix_cfg, culprit_cfg)

    world.facts.update(
        child=child,
        elder=elder,
        dotcom=dotcom,
        place_cfg=place,
        culprit_cfg=culprit_cfg,
        clue_cfg=clue_cfg,
        fix_cfg=fix_cfg,
        solved=child.memes["certainty"] >= THRESHOLD,
        culprit_seen=culprit.meters["seen"] >= THRESHOLD,
        calmed=culprit.meters["kept_out"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "goat": [
        (
            "Why do goats get into places they should not?",
            "Goats are curious and hungry, so they often push into yards or sheds looking for leaves or scraps. If a gate is loose, a goat may treat it like an invitation."
        )
    ],
    "monkey": [
        (
            "Why might a monkey make a mess in a shed?",
            "A monkey has quick hands and likes to pry, grab, and taste things. When it hunts for fruit or treats, it can knock objects together and make a loud noise."
        )
    ],
    "magpie": [
        (
            "Why do some birds pick up shiny things?",
            "Some birds are drawn to bright, glittering objects that catch the light. A shiny cup or ribbon can seem as interesting to them as a toy does to a child."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you understand what happened. Good clues point toward the truth even before anyone says the answer out loud."
        )
    ],
    "mystery": [
        (
            "What is a mystery to solve?",
            "A mystery is a question whose answer is hidden at first. You solve it by noticing signs, thinking carefully, and checking whether your idea fits the facts."
        )
    ],
    "sound": [
        (
            "Why can sounds in the dark feel scary?",
            "When you cannot see what made a noise, your mind may imagine something bigger or stranger than the truth. Light and careful looking often make the fear smaller."
        )
    ],
    "gate": [
        (
            "Why does a latch help keep animals out?",
            "A latch keeps a gate from swinging open when an animal nudges it. It turns a weak barrier into a firm one."
        )
    ],
    "fruit": [
        (
            "Why would fruit draw an animal away from a shed?",
            "If an animal comes looking for sweet food, putting food in a better place gives it an easier choice. That can solve the trouble without hurting the animal."
        )
    ],
    "ribbon": [
        (
            "Why would a bird like a ribbon perch?",
            "A ribbon perch gives a bird a bright, safe place to land and peck. If it likes shiny things, it may choose the perch instead of upsetting cups or tools."
        )
    ],
    "cat": [
        (
            "Why are cats good at noticing little movements?",
            "Cats watch closely and hear tiny sounds that people miss. Their sharp ears and patient eyes make them seem like small nighttime detectives."
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "clue", "sound", "goat", "monkey", "magpie", "gate", "fruit", "ribbon", "cat"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    culprit = f["culprit_cfg"]
    clue = f["clue_cfg"]
    place = f["place_cfg"]
    fix = f["fix_cfg"]
    return [
        'Write a short folk-tale for a 3-to-5-year-old that includes the words "dotcom", "rascal", and "clatter".',
        f"Tell a gentle mystery where a child hears a noise in {place.phrase}, follows {clue.phrase}, and discovers that the culprit is {culprit.phrase}.",
        f"Write a village-night story with sound effects, a fair clue, Dotcom the cat, and an ending where {child.id} solves the mystery by using {fix.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    place = f["place_cfg"]
    culprit = f["culprit_cfg"]
    clue = f["clue_cfg"]
    fix = f["fix_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {elder.label_word}, and Dotcom the cat. Together they listened to a night noise and solved where it came from."
        ),
        (
            "What was the mystery?",
            f"The mystery was the sudden noise in {place.phrase}. At first it sounded strange and spooky because nobody could yet see what was making the clatter."
        ),
        (
            "What clue helped solve the mystery?",
            f"The clue was {clue.phrase}. {clue.reading} That is why {child.id} could move from guessing to knowing."
        ),
        (
            f"Who was the rascal in the story?",
            f"The rascal was {culprit.phrase}. It had been upsetting things in the dark and making the sound that frightened everyone."
        ),
        (
            "How did they solve the problem?",
            f"They solved it by staying calm and using {fix.phrase}. The plan fit the culprit instead of punishing it, so the place grew quiet again."
        ),
        (
            "What did the child learn?",
            f"{child.id} learned not to call every dark sound a ghost. Careful looking, a true clue, and a thoughtful fix can turn fear into understanding."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mystery", "clue", "sound", "cat"}
    culprit = f["culprit_cfg"]
    fix = f["fix_cfg"]
    if culprit.id == "goat":
        tags.add("goat")
    elif culprit.id == "monkey":
        tags.add("monkey")
    elif culprit.id == "magpie":
        tags.add("magpie")
    if fix.id == "latch_gate":
        tags.add("gate")
    elif fix.id == "fruit_basket":
        tags.add("fruit")
    elif fix.id == "ribbon_perch":
        tags.add("ribbon")
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
    for ent in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place_id: str, culprit_id: str, clue_id: str, fix_id: str) -> str:
    parts: list[str] = []
    if not place_allows_culprit(place_id, culprit_id):
        parts.append(
            f"{CULPRITS[culprit_id].label.capitalize()} does not fit {PLACES[place_id].phrase} in this world"
        )
    if not culprit_matches_clue(culprit_id, clue_id):
        parts.append(
            f"{CLUES[clue_id].phrase} does not honestly point to {CULPRITS[culprit_id].label}"
        )
    if not fix_matches_culprit(culprit_id, fix_id):
        parts.append(
            f"{FIXES[fix_id].label} is not a fitting remedy for {CULPRITS[culprit_id].label}"
        )
    if not parts:
        return "(No story: the requested combination is not valid.)"
    return "(No story: " + "; ".join(parts) + ".)"


ASP_RULES = r"""
% A place can host a culprit only when the world says that animal is drawn there.
valid_place(P, C) :- invites(P, C).

% A clue is fair only when it belongs to that culprit.
fair_clue(C, Cl) :- clue_of(C, Cl).

% A remedy is good only when it matches that culprit's habits.
good_fix(C, F) :- remedy(C, F).

valid(P, C, Cl, F) :- place(P), culprit(C), clue(Cl), fix(F),
                      valid_place(P, C), fair_clue(C, Cl), good_fix(C, F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for culprit_id in sorted(place.invites):
            lines.append(asp.fact("invites", place_id, culprit_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        for clue_id in sorted(culprit.clue_ids):
            lines.append(asp.fact("clue_of", culprit_id, clue_id))
        for fix_id in sorted(culprit.fix_ids):
            lines.append(asp.fact("remedy", culprit_id, fix_id))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for fix_id in FIXES:
        lines.append(asp.fact("fix", fix_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(
        place="granary",
        culprit="goat",
        clue="hoofprints",
        fix="latch_gate",
        child_name="Lina",
        child_gender="girl",
        elder_type="grandmother",
        child_trait="curious",
    ),
    StoryParams(
        place="tea_shed",
        culprit="monkey",
        clue="banana_peels",
        fix="fruit_basket",
        child_name="Milo",
        child_gender="boy",
        elder_type="grandfather",
        child_trait="patient",
    ),
    StoryParams(
        place="lantern_house",
        culprit="magpie",
        clue="black_feather",
        fix="ribbon_perch",
        child_name="Asha",
        child_gender="girl",
        elder_type="grandmother",
        child_trait="bright-eyed",
    ),
    StoryParams(
        place="tea_shed",
        culprit="magpie",
        clue="silver_thread",
        fix="ribbon_perch",
        child_name="Ren",
        child_gender="boy",
        elder_type="grandfather",
        child_trait="careful",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale mystery storyworld: Dotcom the cat, a night clatter, and a rascal to identify."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--culprit", choices=sorted(CULPRITS))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--fix", choices=sorted(FIXES))
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_id = args.place
    culprit_id = args.culprit
    clue_id = args.clue
    fix_id = args.fix

    if place_id and culprit_id and not place_allows_culprit(place_id, culprit_id):
        raise StoryError(explain_rejection(place_id, culprit_id, clue_id or next(iter(CLUES)), fix_id or next(iter(FIXES))))
    if culprit_id and clue_id and not culprit_matches_clue(culprit_id, clue_id):
        raise StoryError(explain_rejection(place_id or next(iter(PLACES)), culprit_id, clue_id, fix_id or next(iter(FIXES))))
    if culprit_id and fix_id and not fix_matches_culprit(culprit_id, fix_id):
        raise StoryError(explain_rejection(place_id or next(iter(PLACES)), culprit_id, clue_id or next(iter(CLUES)), fix_id))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.clue is None or combo[2] == args.clue)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, culprit_id, clue_id, fix_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES[child_gender])
    elder_type = args.elder or rng.choice(["grandmother", "grandfather"])
    child_trait = rng.choice(CHILD_TRAITS)

    return StoryParams(
        place=place_id,
        culprit=culprit_id,
        clue=clue_id,
        fix=fix_id,
        child_name=child_name,
        child_gender=child_gender,
        elder_type=elder_type,
        child_trait=child_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(No story: unknown culprit '{params.culprit}'.)")
    if params.clue not in CLUES:
        raise StoryError(f"(No story: unknown clue '{params.clue}'.)")
    if params.fix not in FIXES:
        raise StoryError(f"(No story: unknown fix '{params.fix}'.)")
    if not place_allows_culprit(params.place, params.culprit):
        raise StoryError(explain_rejection(params.place, params.culprit, params.clue, params.fix))
    if not culprit_matches_clue(params.culprit, params.clue):
        raise StoryError(explain_rejection(params.place, params.culprit, params.clue, params.fix))
    if not fix_matches_culprit(params.culprit, params.fix):
        raise StoryError(explain_rejection(params.place, params.culprit, params.clue, params.fix))

    world = tell(
        place=PLACES[params.place],
        culprit_cfg=CULPRITS[params.culprit],
        clue_cfg=CLUES[params.clue],
        fix_cfg=FIXES[params.fix],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        child_trait=params.child_trait,
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
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(123))
        params.seed = 123
        smoke_cases.append(params)
    except StoryError as err:
        rc = 1
        print(f"Smoke-test setup failed: {err}")

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            emit(sample, trace=False, qa=False, header=f"### smoke {idx}")
        except Exception as err:
            rc = 1
            print(f"Smoke test {idx} failed: {err}")

    if rc == 0:
        print("OK: smoke tests generated and emitted stories successfully.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, culprit, clue, fix) combos:\n")
        for place_id, culprit_id, clue_id, fix_id in combos:
            print(f"  {place_id:13} {culprit_id:7} {clue_id:16} {fix_id}")
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
            header = f"### {p.child_name}: {p.culprit} in {p.place} (clue: {p.clue}, fix: {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
