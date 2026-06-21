#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bizarre_zipper_misunderstanding_curiosity_bad_ending_superhero.py
================================================================================================

A standalone storyworld about a superhero game, a bizarre zipper, and a sad
mistake. A curious child misunderstands a zippered gear pack as a superhero
power switch, opens it in a windy place, and loses a treasured costume piece.

The world model is small and classical:

- places have wind and a landing place
- zip-packs release loose fabric or gear when opened
- a treasured wearable has a "hold" strength
- loose gear + wind can snatch the wearable away
- losing the wearable makes the children sad and ends the game badly

The story is deliberately built around misunderstanding, curiosity, and a bad
ending, while staying child-facing and concrete.

Run it
------
    python storyworlds/worlds/gpt-5.4/bizarre_zipper_misunderstanding_curiosity_bad_ending_superhero.py
    python storyworlds/worlds/gpt-5.4/bizarre_zipper_misunderstanding_curiosity_bad_ending_superhero.py --place hill --pack glider_pack --prize cape
    python storyworlds/worlds/gpt-5.4/bizarre_zipper_misunderstanding_curiosity_bad_ending_superhero.py --all
    python storyworlds/worlds/gpt-5.4/bizarre_zipper_misunderstanding_curiosity_bad_ending_superhero.py --qa --json
    python storyworlds/worlds/gpt-5.4/bizarre_zipper_misunderstanding_curiosity_bad_ending_superhero.py --verify
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
# from this nested directory:
# storyworlds/worlds/gpt-5.4/<file>.py -> add storyworlds/ to sys.path.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    worn_by: str = ""
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    high_spot: str
    landing: str
    landing_kind: str
    wind: int
    tags: set[str] = field(default_factory=set)


@dataclass
class ZipPack:
    id: str
    label: str
    phrase: str
    contains: str
    zipper_desc: str
    misread: str
    warning: str
    burst: str
    release_force: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    wear_line: str
    hold: int
    plural: bool = False
    tags: set[str] = field(default_factory=set)

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    place: str
    pack: str
    prize: str
    hero: str
    hero_gender: str
    sidekick: str
    sidekick_gender: str
    parent: str
    hero_trait: str
    sidekick_trait: str
    seed: Optional[int] = None


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


def snag_power(place: Place, pack: ZipPack) -> int:
    return place.wind + pack.release_force


def pack_can_snatch(place: Place, pack: ZipPack, prize: Prize) -> bool:
    return snag_power(place, pack) > prize.hold


def outcome_of_combo(place: Place, pack: ZipPack, prize: Prize) -> str:
    if not pack_can_snatch(place, pack, prize):
        return "safe"
    return "soaked" if place.landing_kind == "water" else "snagged"


def _r_snatch(world: World) -> list[str]:
    hero = world.get("hero")
    prize = world.get("prize")
    released = world.get("released")
    if released.meters["loose"] < THRESHOLD:
        return []
    if prize.meters["lost"] >= THRESHOLD:
        return []
    sig = ("snatch", world.place.id, world.facts["pack_cfg"].id, world.facts["prize_cfg"].id)
    if sig in world.fired:
        return []
    if not pack_can_snatch(world.place, world.facts["pack_cfg"], world.facts["prize_cfg"]):
        return []
    world.fired.add(sig)
    prize.meters["lost"] += 1
    if world.place.landing_kind == "water":
        prize.meters["wet"] += 1
        prize.meters["ruined"] += 1
    else:
        prize.meters["torn"] += 1
        prize.meters["snagged"] += 1
    hero.memes["shock"] += 1
    return ["__lost__"]


def _r_sadness(world: World) -> list[str]:
    prize = world.get("prize")
    if prize.meters["lost"] < THRESHOLD:
        return []
    sig = ("sadness", prize.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("hero").memes["sadness"] += 1
    world.get("sidekick").memes["sadness"] += 1
    if "parent" in world.entities:
        world.get("parent").memes["concern"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="snatch", tag="physical", apply=_r_snatch),
    Rule(name="sadness", tag="emotional", apply=_r_sadness),
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
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "hill": Place(
        id="hill",
        label="the grassy hill behind the school",
        high_spot="the very top of the hill",
        landing="the thorny hedge at the bottom",
        landing_kind="thorn",
        wind=2,
        tags={"wind", "hill"},
    ),
    "roof": Place(
        id="roof",
        label="the flat garage roof",
        high_spot="the roof edge by the drainpipe",
        landing="the wet puddle in the alley below",
        landing_kind="water",
        wind=3,
        tags={"wind", "roof", "puddle"},
    ),
    "tower": Place(
        id="tower",
        label="the tall playground tower",
        high_spot="the highest little platform",
        landing="the chain-link fence by the sandbox",
        landing_kind="fence",
        wind=2,
        tags={"wind", "playground"},
    ),
}

PACKS = {
    "glider_pack": ZipPack(
        id="glider_pack",
        label="glider pack",
        phrase="a silver glider pack",
        contains="folded silk wings",
        zipper_desc="a bizarre zipper that looped in a crooked lightning shape",
        misread="the hidden switch for real flying power",
        warning="it was only holding folded silk wings for later",
        burst="the silk wings burst out all at once",
        release_force=2,
        tags={"zipper", "wind", "flying"},
    ),
    "banner_roll": ZipPack(
        id="banner_roll",
        label="banner roll",
        phrase="a bright hero-banner roll",
        contains="long shiny streamers",
        zipper_desc="a bizarre zipper sewn around it in a circle",
        misread="the ring that would spin up superhero wind",
        warning="it was just keeping the long streamers tucked inside",
        burst="the streamers whipped out in a bright noisy swirl",
        release_force=1,
        tags={"zipper", "wind", "banner"},
    ),
    "parachute_satchel": ZipPack(
        id="parachute_satchel",
        label="parachute satchel",
        phrase="a red parachute satchel",
        contains="a practice chute of thin orange cloth",
        zipper_desc="a bizarre zipper with two metal teeth missing",
        misread="the rip-cord for a daring sky rescue",
        warning="it was only meant to stay shut until a grown-up opened it",
        burst="the orange cloth leapt out and filled with air",
        release_force=3,
        tags={"zipper", "wind", "parachute"},
    ),
}

PRIZES = {
    "cape": Prize(
        id="cape",
        label="cape",
        phrase="a new blue cape with a gold star",
        wear_line="tied the blue cape around the shoulders",
        hold=2,
        plural=False,
        tags={"cape", "clothes"},
    ),
    "mask": Prize(
        id="mask",
        label="mask",
        phrase="a shiny hero mask with soft ties",
        wear_line="pulled the shiny mask snug over the eyes",
        hold=1,
        plural=False,
        tags={"mask", "clothes"},
    ),
    "wrist_streamers": Prize(
        id="wrist_streamers",
        label="wrist streamers",
        phrase="two silver wrist streamers",
        wear_line="tied the silver wrist streamers on tight",
        hold=1,
        plural=True,
        tags={"streamers", "clothes"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Max", "Ben", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]
TRAITS = ["brave", "curious", "eager", "lively", "careful", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for pack_id, pack in PACKS.items():
            for prize_id, prize in PRIZES.items():
                if pack_can_snatch(place, pack, prize):
                    combos.append((place_id, pack_id, prize_id))
    return combos


def explain_rejection(place: Place, pack: ZipPack, prize: Prize) -> str:
    return (
        f"(No story: at {place.label}, opening the {pack.label} is not strong enough "
        f"to carry off the {prize.label}. This world only tells the sad versions "
        f"where the loose gear really can snatch the costume piece away.)"
    )


def introduce(world: World, hero: Entity, sidekick: Entity, prize: Prize) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"On a breezy afternoon, {hero.id} and {sidekick.id} raced to {world.place.label} "
        f"to play superheroes."
    )
    world.say(
        f"{hero.id} {prize.wear_line}, and for one glowing moment it felt as if a real hero "
        f"might leap straight out of a comic book."
    )


def superhero_game(world: World, hero: Entity, sidekick: Entity, place: Place) -> None:
    hero.memes["imagination"] += 1
    sidekick.memes["imagination"] += 1
    world.say(
        f"They called {place.high_spot} their watchtower and pointed across the neighborhood "
        f"as if villains might appear at any second."
    )
    world.say(
        f'"Captain Comet!" {sidekick.id} cried. "{hero.id}, the city needs you!"'
    )


def spot_pack(world: World, hero: Entity, sidekick: Entity, pack: ZipPack) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"Near an old bench sat {pack.phrase}. Across the front ran {pack.zipper_desc}."
    )
    world.say(
        f'{hero.id} crouched beside it. "That must be {pack.misread}," {hero.pronoun()} whispered.'
    )
    world.say(
        f"The idea was wrong, but it sparkled so brightly in {hero.pronoun('possessive')} mind "
        f"that it felt almost true."
    )


def warn(world: World, hero: Entity, sidekick: Entity, parent: Entity, pack: ZipPack, prize: Prize) -> None:
    pred = predict_loss(world, prize.id)
    sidekick.memes["caution"] += 1
    world.facts["predicted_outcome"] = pred["outcome"]
    sidekick_extra = ""
    if sidekick.attrs.get("trait") in {"careful", "thoughtful"}:
        sidekick_extra = f" {sidekick.id} kept both hands behind {sidekick.pronoun('possessive')} back and did not go any closer."
    world.say(
        f'{sidekick.id} shook {sidekick.pronoun("possessive")} head. "No, it is just a zipper," '
        f'{sidekick.pronoun()} said. "{pack.warning} If you pull it here, the wind could grab your '
        f'{prize.label}."{sidekick_extra}'
    )
    world.say(
        f"{parent.label_word.capitalize()} was only a little way off, setting out juice and apples, "
        f"too far away to hear the warning in time."
    )


def defy(world: World, hero: Entity, pack: ZipPack) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"Just one tiny peek," {hero.id} said. Curiosity tugged harder than good sense, '
        f"and {hero.pronoun()} pinched the zipper pull."
    )


def _do_open(world: World, pack: ZipPack, narrate: bool = True) -> None:
    opened = world.get("pack")
    released = world.get("released")
    opened.meters["open"] += 1
    released.meters["loose"] += 1
    released.meters["airborne"] += 1
    propagate(world, narrate=narrate)


def open_pack(world: World, hero: Entity, pack: ZipPack) -> None:
    _do_open(world, pack, narrate=False)
    world.say(
        f"Zzzzip! The zipper ran wide, and {pack.burst}. The wind caught them before "
        f"{hero.id} could even blink."
    )


def loss_scene(world: World, hero: Entity, sidekick: Entity, prize: Prize, place: Place) -> None:
    if place.landing_kind == "water":
        world.say(
            f"The loose cloth slapped across {hero.id}'s {prize.label}, yanked it free, and sent it spinning "
            f"down into {place.landing}."
        )
        world.say(
            f"The bright costume piece darkened at once, sank crookedly, and was ruined before anyone could reach it."
        )
    elif place.landing_kind == "thorn":
        world.say(
            f"The loose cloth tangled with {hero.id}'s {prize.label}, tore it free, and dragged it straight into "
            f"{place.landing}."
        )
        world.say(
            f"When it stopped fluttering, the cloth hung there in ragged strips."
        )
    else:
        world.say(
            f"The loose cloth hooked {hero.id}'s {prize.label}, tore it free, and flung it against "
            f"{place.landing}."
        )
        world.say(
            f"It caught on the wire and ripped with a sharp, mean sound."
        )
    world.say(
        f'{sidekick.id} gasped. "{hero.id}, your {prize.label}!"'
    )


def bad_ending(world: World, hero: Entity, sidekick: Entity, parent: Entity, prize: Prize) -> None:
    hero.memes["lesson"] += 1
    sidekick.memes["lesson"] += 1
    parent.memes["care"] += 1
    condition = "ruined" if prize.meters["ruined"] >= THRESHOLD else "torn"
    world.say(
        f"{parent.label_word.capitalize()} hurried over, but the {prize.label} was already {condition}."
    )
    world.say(
        f'{parent.pronoun().capitalize()} put an arm around both children. "I know you wanted a superhero secret," '
        f'{parent.pronoun()} said softly, "but a zipper is just a zipper until you know what it does."'
    )
    world.say(
        f"{hero.id} did not feel like a hero anymore. The game was over, the afternoon had gone quiet, "
        f"and {hero.pronoun('possessive')} brave costume was gone."
    )
    world.say(
        f"They walked home slowly, with no flying, no cheering, and no parade at the end."
    )


def predict_loss(world: World, prize_id: str) -> dict:
    sim = world.copy()
    _do_open(sim, sim.facts["pack_cfg"], narrate=False)
    prize = sim.get(prize_id)
    outcome = "safe"
    if prize.meters["ruined"] >= THRESHOLD:
        outcome = "soaked"
    elif prize.meters["lost"] >= THRESHOLD:
        outcome = "snagged"
    return {"outcome": outcome, "lost": prize.meters["lost"] >= THRESHOLD}


def tell(
    place: Place,
    pack: ZipPack,
    prize_cfg: Prize,
    hero_name: str = "Max",
    hero_gender: str = "boy",
    sidekick_name: str = "Lily",
    sidekick_gender: str = "girl",
    parent_type: str = "mother",
    hero_trait: str = "curious",
    sidekick_trait: str = "careful",
) -> World:
    world = World(place)
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_gender,
            label=hero_name,
            phrase=hero_name,
            role="hero",
            traits=[hero_trait],
            attrs={"trait": hero_trait},
        )
    )
    sidekick = world.add(
        Entity(
            id="sidekick",
            kind="character",
            type=sidekick_gender,
            label=sidekick_name,
            phrase=sidekick_name,
            role="sidekick",
            traits=[sidekick_trait],
            attrs={"trait": sidekick_trait},
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            phrase="the parent",
            role="parent",
        )
    )
    prize = world.add(
        Entity(
            id="prize",
            type=prize_cfg.id,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner="hero",
            worn_by="hero",
            tags=set(prize_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="pack",
            type="pack",
            label=pack.label,
            phrase=pack.phrase,
            tags=set(pack.tags),
        )
    )
    world.add(
        Entity(
            id="released",
            type="cloth",
            label=pack.contains,
            phrase=pack.contains,
            tags=set(pack.tags),
        )
    )

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        parent=parent,
        prize=prize,
        place_cfg=place,
        pack_cfg=pack,
        prize_cfg=prize_cfg,
    )

    introduce(world, hero, sidekick, prize_cfg)
    superhero_game(world, hero, sidekick, place)

    world.para()
    spot_pack(world, hero, sidekick, pack)
    warn(world, hero, sidekick, parent, pack, prize_cfg)
    defy(world, hero, pack)

    world.para()
    open_pack(world, hero, pack)
    loss_scene(world, hero, sidekick, prize_cfg, place)

    world.para()
    bad_ending(world, hero, sidekick, parent, prize)

    world.facts.update(
        outcome=outcome_of_combo(place, pack, prize_cfg),
        lost=prize.meters["lost"] >= THRESHOLD,
        ruined=prize.meters["ruined"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "zipper": [
        (
            "What does a zipper do?",
            "A zipper is a row of little teeth that open and close cloth or a bag. It is not a magic switch, so you should ask before pulling one on something unfamiliar.",
        )
    ],
    "wind": [
        (
            "Why can wind carry light things away?",
            "Wind pushes on light cloth and paper very easily. If something is loose, the air can lift it and drag it before your hands can catch it.",
        )
    ],
    "cape": [
        (
            "Why can a cape get caught by the wind?",
            "A cape is broad and light, so moving air can grab it like a flag. That is why capes flap and can tug hard when it is windy.",
        )
    ],
    "mask": [
        (
            "Why can a mask be easy to lose outside?",
            "A soft mask is light, and its ties can slip or flutter. In a windy place, it can be blown away quickly.",
        )
    ],
    "streamers": [
        (
            "Why do streamers flap so much?",
            "Streamers are long thin strips, so air can catch every little piece of them. That makes them whip and flutter fast.",
        )
    ],
    "ask_first": [
        (
            "What should you do before opening something strange?",
            "Ask a grown-up what it is for first. That is the safe way to learn instead of guessing and making a mess or losing something.",
        )
    ],
    "puddle": [
        (
            "What happens to cloth if it falls into a puddle?",
            "It gets wet and dirty very fast. Some soft things can also be ruined if they soak up muddy water.",
        )
    ],
    "fence": [
        (
            "Why can a fence tear cloth?",
            "Wire and rough edges can catch cloth and pull holes in it. Thin costume fabric can rip very easily on a fence.",
        )
    ],
    "thorn": [
        (
            "Why do thorns snag clothes?",
            "Thorns are sharp little points on a plant. They can hook cloth and tear it when the wind pulls.",
        )
    ],
}
KNOWLEDGE_ORDER = ["zipper", "wind", "cape", "mask", "streamers", "ask_first", "puddle", "fence", "thorn"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    pack = world.facts["pack_cfg"]
    prize = world.facts["prize_cfg"]
    place = world.facts["place_cfg"]
    return [
        'Write a short superhero story for a 3-to-5-year-old that includes the words "bizarre" and "zipper" and ends sadly.',
        f"Tell a superhero story where {hero.label} misunderstands a {pack.label} at {place.label}, opens it out of curiosity, and loses a treasured {prize.label}.",
        f"Write a cautionary story where {sidekick.label} gives a sensible warning, but curiosity wins and the ending is bad because the costume piece is lost.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    parent = world.facts["parent"]
    pack = world.facts["pack_cfg"]
    prize = world.facts["prize_cfg"]
    place = world.facts["place_cfg"]
    out = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child pretending to be a superhero, and {sidekick.label}, the sidekick who tried to give a warning. {parent.label_word.capitalize()} was nearby, but not close enough to stop the mistake.",
        ),
        (
            "What was the misunderstanding?",
            f"{hero.label} thought the bizarre zipper on the {pack.label} was {pack.misread}. Really, it was only there to keep {pack.contains} tucked inside.",
        ),
        (
            f"Why did {hero.label} open the zipper?",
            f"{hero.label} was curious and wanted the game to feel more real. The wrong idea sounded exciting, so curiosity pushed harder than caution.",
        ),
        (
            f"What did {sidekick.label} warn would happen?",
            f"{sidekick.label} warned that the zipper was ordinary and that the wind could grab the {prize.label}. That warning fit the place, because {place.label} was breezy and high.",
        ),
    ]
    if out == "soaked":
        qa.append(
            (
                f"What happened to the {prize.label} after the zipper opened?",
                f"The loose cloth yanked the {prize.label} free and sent it into {place.landing}. It was ruined there before anyone could save it.",
            )
        )
    else:
        qa.append(
            (
                f"What happened to the {prize.label} after the zipper opened?",
                f"The loose cloth tore the {prize.label} free and flung it into {place.landing}. It ended up snagged and ripped, so the game could not go on.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended sadly. The costume piece was gone, the superhero game stopped, and the children walked home quietly instead of celebrating.",
        )
    )
    qa.append(
        (
            "What lesson did the children learn?",
            f"They learned not to guess what a strange zipper does. Asking first would have protected the costume and kept the afternoon from ending badly.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"zipper", "wind", "ask_first"}
    prize = world.facts["prize_cfg"]
    place = world.facts["place_cfg"]
    tags |= set(prize.tags)
    if place.landing_kind == "water":
        tags.add("puddle")
    elif place.landing_kind == "fence":
        tags.add("fence")
    elif place.landing_kind == "thorn":
        tags.add("thorn")
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
        if ent.worn_by:
            bits.append(f"worn_by={ent.worn_by}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="hill",
        pack="glider_pack",
        prize="cape",
        hero="Max",
        hero_gender="boy",
        sidekick="Lily",
        sidekick_gender="girl",
        parent="mother",
        hero_trait="curious",
        sidekick_trait="careful",
    ),
    StoryParams(
        place="roof",
        pack="banner_roll",
        prize="mask",
        hero="Mia",
        hero_gender="girl",
        sidekick="Ben",
        sidekick_gender="boy",
        parent="father",
        hero_trait="eager",
        sidekick_trait="thoughtful",
    ),
    StoryParams(
        place="tower",
        pack="parachute_satchel",
        prize="wrist_streamers",
        hero="Noah",
        hero_gender="boy",
        sidekick="Zoe",
        sidekick_gender="girl",
        parent="mother",
        hero_trait="brave",
        sidekick_trait="careful",
    ),
    StoryParams(
        place="roof",
        pack="parachute_satchel",
        prize="cape",
        hero="Ella",
        hero_gender="girl",
        sidekick="Sam",
        sidekick_gender="boy",
        parent="father",
        hero_trait="curious",
        sidekick_trait="thoughtful",
    ),
]


ASP_RULES = r"""
snag_power(P, K, V) :- wind(P, W), release_force(K, R), V = W + R.
valid(P, K, Z) :- place(P), pack(K), prize(Z), snag_power(P, K, V), hold(Z, H), V > H.

outcome(P, soaked) :- valid(P, _, _), landing_kind(P, water).
outcome(P, snagged) :- valid(P, _, _), landing_kind(P, thorn).
outcome(P, snagged) :- valid(P, _, _), landing_kind(P, fence).

chosen_valid :- chosen_place(P), chosen_pack(K), chosen_prize(Z), valid(P, K, Z).
chosen_outcome(soaked) :- chosen_valid, chosen_place(P), landing_kind(P, water).
chosen_outcome(snagged) :- chosen_valid, chosen_place(P), landing_kind(P, thorn).
chosen_outcome(snagged) :- chosen_valid, chosen_place(P), landing_kind(P, fence).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("wind", place_id, place.wind))
        lines.append(asp.fact("landing_kind", place_id, place.landing_kind))
    for pack_id, pack in PACKS.items():
        lines.append(asp.fact("pack", pack_id))
        lines.append(asp.fact("release_force", pack_id, pack.release_force))
    for prize_id, prize in PRIZES.items():
        lines.append(asp.fact("prize", prize_id))
        lines.append(asp.fact("hold", prize_id, prize.hold))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_pack", params.pack),
            asp.fact("chosen_prize", params.prize),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show chosen_outcome/1."))
    atoms = asp.atoms(model, "chosen_outcome")
    return atoms[0][0] if atoms else "safe"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero game, a bizarre zipper, curiosity, misunderstanding, and a sad ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--pack", choices=PACKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick")
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "", gender: Optional[str] = None) -> tuple[str, str]:
    chosen_gender = gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if chosen_gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), chosen_gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.pack and args.prize:
        place = PLACES[args.place]
        pack = PACKS[args.pack]
        prize = PRIZES[args.prize]
        if not pack_can_snatch(place, pack, prize):
            raise StoryError(explain_rejection(place, pack, prize))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.pack is None or combo[1] == args.pack)
        and (args.prize is None or combo[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, pack_id, prize_id = rng.choice(sorted(combos))
    hero_name, hero_gender = _pick_child(rng, gender=args.hero_gender)
    if args.hero:
        hero_name = args.hero
    sidekick_name, sidekick_gender = _pick_child(rng, avoid=hero_name, gender=args.sidekick_gender)
    if args.sidekick:
        sidekick_name = args.sidekick
    parent = args.parent or rng.choice(["mother", "father"])
    hero_trait = rng.choice(TRAITS)
    sidekick_trait = rng.choice(["careful", "thoughtful", "brave", "curious"])
    return StoryParams(
        place=place_id,
        pack=pack_id,
        prize=prize_id,
        hero=hero_name,
        hero_gender=hero_gender,
        sidekick=sidekick_name,
        sidekick_gender=sidekick_gender,
        parent=parent,
        hero_trait=hero_trait,
        sidekick_trait=sidekick_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.pack not in PACKS:
        raise StoryError(f"(Unknown pack: {params.pack})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")

    place = PLACES[params.place]
    pack = PACKS[params.pack]
    prize = PRIZES[params.prize]
    if not pack_can_snatch(place, pack, prize):
        raise StoryError(explain_rejection(place, pack, prize))

    world = tell(
        place=place,
        pack=pack,
        prize_cfg=prize,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        sidekick_name=params.sidekick,
        sidekick_gender=params.sidekick_gender,
        parent_type=params.parent,
        hero_trait=params.hero_trait,
        sidekick_trait=params.sidekick_trait,
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for params in cases:
        py = outcome_of_combo(PLACES[params.place], PACKS[params.pack], PRIZES[params.prize])
        asp = asp_outcome(params)
        if py != asp:
            rc = 1
            print(
                f"MISMATCH outcome for {params.place}/{params.pack}/{params.prize}: "
                f"python={py} asp={asp}"
            )

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show chosen_outcome/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, pack, prize) combos:\n")
        for place, pack, prize in combos:
            print(f"  {place:8} {pack:18} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.hero} and {p.sidekick}: {p.pack} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
