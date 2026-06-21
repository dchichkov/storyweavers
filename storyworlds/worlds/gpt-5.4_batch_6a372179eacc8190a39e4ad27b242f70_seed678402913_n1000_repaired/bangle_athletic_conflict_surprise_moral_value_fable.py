#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bangle_athletic_conflict_surprise_moral_value_fable.py
==================================================================================

A standalone storyworld for a fable-shaped tale about an athletic young animal,
a shiny bangle, a conflict with a rival, a surprising turn, and a moral lesson.

The world model prefers a small number of plausible story shapes:

- an athletic animal finds a lost bangle and means to return it
- a rival thinks the shiny thing matters more than training or character
- the rival rushes toward a hidden danger
- the bangle unexpectedly becomes the warning sign
- the athlete's real strength is shown in a rescue or pull-back
- the ending states and proves a moral value in action

The reasonableness gate is explicit: a story is only valid when
(1) the terrain actually contains the obstacle,
(2) the bangle's cue can reveal that obstacle, and
(3) the athlete is agile enough to help sensibly.

Run it
------
python storyworlds/worlds/gpt-5.4/bangle_athletic_conflict_surprise_moral_value_fable.py
python storyworlds/worlds/gpt-5.4/bangle_athletic_conflict_surprise_moral_value_fable.py --all
python storyworlds/worlds/gpt-5.4/bangle_athletic_conflict_surprise_moral_value_fable.py --qa
python storyworlds/worlds/gpt-5.4/bangle_athletic_conflict_surprise_moral_value_fable.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "doe", "hen", "mother", "woman"}
        male = {"boy", "buck", "cock", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class AnimalKind:
    id: str
    name: str
    species: str
    gender: str
    phrase: str
    agility: int
    stride: str
    habitat_note: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Terrain:
    id: str
    label: str
    track: str
    detail: str
    obstacles: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    hidden_text: str
    edge_text: str
    cue_type: str
    difficulty: int
    rescue_need: int
    consequence: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BangleKind:
    id: str
    phrase: str
    cue_type: str
    surprise_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MoralValue:
    id: str
    noun: str
    closing: str
    repair_text: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    terrain: str
    athlete: str
    rival: str
    obstacle: str
    bangle: str
    moral: str
    seed: Optional[int] = None


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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_reveal(world: World) -> list[str]:
    athlete = world.get("athlete")
    rival = world.get("rival")
    obstacle = world.get("obstacle")
    bangle = world.get("bangle")
    if obstacle.meters["revealed"] >= THRESHOLD:
        return []
    if bangle.meters["cue"] < THRESHOLD:
        return []
    sig = ("reveal", bangle.id, obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obstacle.meters["revealed"] += 1
    athlete.memes["alert"] += 1
    rival.memes["alarm"] += 1
    return ["__revealed__"]


def _r_slip(world: World) -> list[str]:
    athlete = world.get("athlete")
    rival = world.get("rival")
    obstacle = world.get("obstacle")
    if rival.memes["rushing"] < THRESHOLD:
        return []
    if rival.meters["safe"] >= THRESHOLD:
        return []
    if obstacle.meters["revealed"] >= THRESHOLD and athlete.attrs.get("pull_mode") == "back":
        return []
    sig = ("slip", rival.id, obstacle.id)
    if sig in world.fired:
        return []
    if obstacle.meters["revealed"] >= THRESHOLD and athlete.attrs.get("pull_mode") == "back":
        return []
    world.fired.add(sig)
    rival.meters["stuck"] += 1
    rival.memes["fear"] += 1
    return ["__slip__"]


def _r_rescue(world: World) -> list[str]:
    athlete = world.get("athlete")
    rival = world.get("rival")
    obstacle = world.get("obstacle")
    if rival.meters["stuck"] < THRESHOLD:
        return []
    if athlete.attrs.get("agility", 0) < obstacle.attrs.get("rescue_need", 0):
        return []
    sig = ("rescue", athlete.id, rival.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rival.meters["stuck"] = 0.0
    rival.meters["safe"] += 1
    athlete.memes["helpfulness"] += 1
    rival.memes["gratitude"] += 1
    return ["__rescued__"]


CAUSAL_RULES = [
    Rule(name="reveal", tag="physical", apply=_r_reveal),
    Rule(name="slip", tag="physical", apply=_r_slip),
    Rule(name="rescue", tag="social", apply=_r_rescue),
]


def propagate(world: World, narrate: bool = False) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    return out


ANIMALS = {
    "gazelle": AnimalKind(
        id="gazelle",
        name="Gita",
        species="gazelle",
        gender="doe",
        phrase="a slim young gazelle",
        agility=5,
        stride="her hooves could skim the ground like skipping pebbles",
        habitat_note="She loved the morning wind on the open track.",
        tags={"gazelle", "athletic"},
    ),
    "hare": AnimalKind(
        id="hare",
        name="Lina",
        species="hare",
        gender="girl",
        phrase="a quick little hare",
        agility=4,
        stride="her long feet loved to spring over roots",
        habitat_note="She liked to race her own shadow at dawn.",
        tags={"hare", "athletic"},
    ),
    "goat": AnimalKind(
        id="goat",
        name="Tavi",
        species="goat",
        gender="boy",
        phrase="a bright-eyed young goat",
        agility=4,
        stride="his legs were sure even on sharp stones",
        habitat_note="He practiced where the hill paths bent and climbed.",
        tags={"goat", "athletic"},
    ),
    "squirrel": AnimalKind(
        id="squirrel",
        name="Pip",
        species="squirrel",
        gender="boy",
        phrase="a nimble red squirrel",
        agility=3,
        stride="his paws were fast and light on bark and branch",
        habitat_note="He never met a fallen log he did not want to cross.",
        tags={"squirrel", "athletic"},
    ),
}

RIVALS = {
    "fox": AnimalKind(
        id="fox",
        name="Fenn",
        species="fox",
        gender="boy",
        phrase="a sleek young fox",
        agility=3,
        stride="he liked to look swift even when he had not trained",
        habitat_note="He admired bright things almost as much as praise.",
        tags={"fox"},
    ),
    "magpie": AnimalKind(
        id="magpie",
        name="Mira",
        species="magpie",
        gender="girl",
        phrase="a sharp-eyed magpie",
        agility=2,
        stride="she could hop quickly, though not always wisely",
        habitat_note="She noticed every glint in the grass.",
        tags={"magpie"},
    ),
    "monkey": AnimalKind(
        id="monkey",
        name="Moku",
        species="monkey",
        gender="boy",
        phrase="a noisy young monkey",
        agility=3,
        stride="he leapt first and thought afterward",
        habitat_note="He loved applause more than practice.",
        tags={"monkey"},
    ),
}

TERRAINS = {
    "meadow": Terrain(
        id="meadow",
        label="the meadow path",
        track="a pale path through tall clover",
        detail="Bees hummed over the flowers, and the grass hid many small secrets.",
        obstacles={"burrow", "reed_ditch"},
        tags={"meadow"},
    ),
    "hill": Terrain(
        id="hill",
        label="the sunny hill",
        track="a winding track around warm rocks",
        detail="The stones held the morning light, and the wind smelled clean and dry.",
        obstacles={"stone_crack", "burrow"},
        tags={"hill"},
    ),
    "riverbank": Terrain(
        id="riverbank",
        label="the riverbank trail",
        track="a narrow trail beside whispering reeds",
        detail="Dragonflies flickered above the water, and the ground looked smooth until it suddenly did not.",
        obstacles={"reed_ditch"},
        tags={"river"},
    ),
}

OBSTACLES = {
    "burrow": Obstacle(
        id="burrow",
        label="a hidden burrow mouth",
        hidden_text="a hole tucked under the grass",
        edge_text="the dark lip of a burrow",
        cue_type="flash",
        difficulty=3,
        rescue_need=3,
        consequence="a careless runner could plunge a leg into it",
        tags={"burrow"},
    ),
    "stone_crack": Obstacle(
        id="stone_crack",
        label="a narrow crack between stones",
        hidden_text="a slit between two warm rocks",
        edge_text="the thin crack in the stone",
        cue_type="chime",
        difficulty=4,
        rescue_need=4,
        consequence="a careless runner could wedge a hoof or paw there",
        tags={"stone"},
    ),
    "reed_ditch": Obstacle(
        id="reed_ditch",
        label="a reed-covered ditch",
        hidden_text="a ditch hidden under bent reeds",
        edge_text="the reed-hidden ditch",
        cue_type="chime",
        difficulty=4,
        rescue_need=4,
        consequence="a careless runner could slide straight into it",
        tags={"ditch"},
    ),
}

BANGLES = {
    "silver": BangleKind(
        id="silver",
        phrase="a silver bangle",
        cue_type="flash",
        surprise_text="the bangle caught a spear of sunlight and sent it straight across the hidden ground",
        tags={"silver", "bangle"},
    ),
    "brass": BangleKind(
        id="brass",
        phrase="a brass bangle",
        cue_type="chime",
        surprise_text="the bangle struck a stone and rang out with a bright little chime",
        tags={"brass", "bangle"},
    ),
    "glass": BangleKind(
        id="glass",
        phrase="a glass bangle",
        cue_type="chime",
        surprise_text="the glass bangle tapped against itself and made a sharp warning music",
        tags={"glass", "bangle"},
    ),
}

MORALS = {
    "kindness": MoralValue(
        id="kindness",
        noun="kindness",
        closing="Kindness runs farther than pride.",
        repair_text="Instead of boasting, the athlete offered a steady shoulder and walked the rival back to the safe path.",
        lesson="A kind heart uses strength to help, even after a quarrel.",
        tags={"kindness"},
    ),
    "honesty": MoralValue(
        id="honesty",
        noun="honesty",
        closing="Honesty shines longer than silver.",
        repair_text="The athlete carried the bangle straight to its owner and told exactly what had happened on the trail.",
        lesson="A truthful heart returns what is not its own and speaks plainly.",
        tags={"honesty"},
    ),
    "humility": MoralValue(
        id="humility",
        noun="humility",
        closing="Humility keeps its feet surer than vanity.",
        repair_text="The athlete laid the bangle aside and said that strong legs and careful eyes were worth more than a shiny ring.",
        lesson="A humble heart knows that skill matters more than show.",
        tags={"humility"},
    ),
}


def terrain_has_obstacle(terrain: Terrain, obstacle: Obstacle) -> bool:
    return obstacle.id in terrain.obstacles


def cue_matches(bangle: BangleKind, obstacle: Obstacle) -> bool:
    return bangle.cue_type == obstacle.cue_type


def can_rescue(athlete: AnimalKind, obstacle: Obstacle) -> bool:
    return athlete.agility >= obstacle.rescue_need


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for terrain_id, terrain in TERRAINS.items():
        for athlete_id, athlete in ANIMALS.items():
            for obstacle_id, obstacle in OBSTACLES.items():
                for bangle_id, bangle in BANGLES.items():
                    if terrain_has_obstacle(terrain, obstacle) and cue_matches(bangle, obstacle) and can_rescue(athlete, obstacle):
                        combos.append((terrain_id, athlete_id, obstacle_id, bangle_id))
    return combos


def explain_rejection(terrain: Terrain, athlete: AnimalKind, obstacle: Obstacle, bangle: BangleKind) -> str:
    if not terrain_has_obstacle(terrain, obstacle):
        return (
            f"(No story: {terrain.label} does not sensibly contain {obstacle.label}. "
            f"Pick a terrain that actually has that danger.)"
        )
    if not cue_matches(bangle, obstacle):
        return (
            f"(No story: {bangle.phrase} gives a {bangle.cue_type} warning, but "
            f"{obstacle.label} is only revealed by a {obstacle.cue_type} cue in this world.)"
        )
    if not can_rescue(athlete, obstacle):
        return (
            f"(No story: {athlete.name} the {athlete.species} is not agile enough to rescue "
            f"someone from {obstacle.label}. Pick a stronger athlete or a milder obstacle.)"
        )
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    athlete = ANIMALS[params.athlete]
    obstacle = OBSTACLES[params.obstacle]
    if athlete.agility > obstacle.difficulty:
        return "pulled_back"
    return "lifted_out"


def predict_outcome(athlete: AnimalKind, obstacle: Obstacle) -> str:
    return "pulled_back" if athlete.agility > obstacle.difficulty else "lifted_out"


def introduce(world: World, athlete: Entity, terrain: Terrain) -> None:
    world.say(
        f"In the days when beasts still taught one another with examples, {athlete.id} was {athlete.phrase}."
    )
    world.say(
        f"Each dawn {athlete.pronoun()} trained along {terrain.track}, for {athlete.attrs['stride']}."
    )
    world.say(athlete.attrs["habitat_note"])


def find_bangle(world: World, athlete: Entity, bangle_cfg: BangleKind) -> None:
    athlete.memes["care"] += 1
    bangle = world.get("bangle")
    bangle.attrs["owner"] = "Judge Heron"
    bangle.attrs["holder"] = athlete.id
    world.say(
        f"One morning {athlete.pronoun()} found {bangle_cfg.phrase} lying in the dust. "
        f'"This must belong to Judge Heron," {athlete.pronoun()} said. "I will return it after practice."'
    )


def rival_appears(world: World, rival: Entity, athlete: Entity, bangle_cfg: BangleKind) -> None:
    rival.memes["envy"] += 1
    world.say(
        f"Then came {rival.id}, {rival.phrase}. {rival.pronoun().capitalize()} saw {bangle_cfg.phrase} and stopped short."
    )
    world.say(
        f'"Why run so hard?" {rival.pronoun()} said. "With a bangle like that, everyone will think the winner is splendid before the race even starts."'
    )


def quarrel(world: World, rival: Entity, athlete: Entity, moral: MoralValue) -> None:
    athlete.memes["resolve"] += 1
    rival.memes["pride"] += 1
    world.say(
        f'"A shiny ring is not the same as strong legs," {athlete.id} replied. '
        f'"I would rather keep {moral.noun} than borrow glory."'
    )
    world.say(
        f"But {rival.id} laughed, snatched the bangle, and dashed down the trail to prove that glitter was better than training."
    )
    rival.memes["rushing"] += 1
    world.get("bangle").attrs["holder"] = rival.id


def trigger_cue(world: World, terrain: Terrain, obstacle: Obstacle, bangle_cfg: BangleKind) -> None:
    bangle = world.get("bangle")
    bangle.meters["cue"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Yet the trail held {obstacle.hidden_text}. {bangle_cfg.surprise_text}, and all at once "
        f"{obstacle.edge_text} showed itself."
    )


def pull_back(world: World, athlete: Entity, rival: Entity, obstacle: Obstacle) -> None:
    rival.meters["safe"] += 1
    athlete.memes["helpfulness"] += 1
    rival.memes["gratitude"] += 1
    world.say(
        f'{athlete.id} sprang forward and caught {rival.id} by the foreleg just before {rival.pronoun()} reached {obstacle.edge_text}.'
    )
    world.say(
        f'{rival.id} skidded, stared, and saw that {obstacle.consequence}.'
    )


def slip_and_rescue(world: World, athlete: Entity, rival: Entity, obstacle: Obstacle) -> None:
    propagate(world, narrate=False)
    world.say(
        f'{rival.id} tried to stop, but haste had already carried {rival.pronoun("object")} too far. '
        f'{rival.pronoun().capitalize()} slipped at {obstacle.edge_text} and cried out.'
    )
    if rival.meters["safe"] >= THRESHOLD:
        world.say(
            f'{athlete.id} leapt after {rival.pronoun("object")}, braced firm feet on the edge, and hauled {rival.pronoun("object")} back to safety.'
        )


def moral_resolution(world: World, athlete: Entity, rival: Entity, moral: MoralValue) -> None:
    rival.memes["shame"] += 1
    athlete.memes["peace"] += 1
    world.say(
        f'{rival.id} hung {rival.pronoun("possessive")} head. "I thought the bangle would make me look great," {rival.pronoun()} murmured.'
    )
    world.say(
        f'"It only helped because it warned us," said {athlete.id}. "It was never mine, and it was never a substitute for care."'
    )
    world.say(moral.repair_text)
    world.say(
        f"Judge Heron received the bangle, heard the tale, and nodded at the one who had used strength with {moral.noun}."
    )
    world.say(moral.closing)


def tell(
    terrain_cfg: Terrain,
    athlete_cfg: AnimalKind,
    rival_cfg: AnimalKind,
    obstacle_cfg: Obstacle,
    bangle_cfg: BangleKind,
    moral_cfg: MoralValue,
) -> World:
    world = World()
    athlete = world.add(
        Entity(
            id=athlete_cfg.name,
            kind="character",
            type=athlete_cfg.gender,
            label=athlete_cfg.species,
            phrase=athlete_cfg.phrase,
            role="athlete",
            attrs={
                "agility": athlete_cfg.agility,
                "stride": athlete_cfg.stride,
                "habitat_note": athlete_cfg.habitat_note,
                "pull_mode": predict_outcome(athlete_cfg, obstacle_cfg).replace("pulled_back", "back").replace("lifted_out", "rescue"),
            },
            tags=set(athlete_cfg.tags),
        )
    )
    rival = world.add(
        Entity(
            id=rival_cfg.name,
            kind="character",
            type=rival_cfg.gender,
            label=rival_cfg.species,
            phrase=rival_cfg.phrase,
            role="rival",
            attrs={"agility": rival_cfg.agility},
            tags=set(rival_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="bangle",
            kind="thing",
            type="bangle",
            label="bangle",
            phrase=bangle_cfg.phrase,
            role="bangle",
            attrs={"cue_type": bangle_cfg.cue_type},
            tags=set(bangle_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="obstacle",
            kind="thing",
            type="obstacle",
            label=obstacle_cfg.label,
            phrase=obstacle_cfg.hidden_text,
            role="obstacle",
            attrs={"cue_type": obstacle_cfg.cue_type, "rescue_need": obstacle_cfg.rescue_need},
            tags=set(obstacle_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="judge",
            kind="character",
            type="heron",
            label="Judge Heron",
            phrase="an old white heron",
            role="owner",
            tags={"heron"},
        )
    )

    introduce(world, athlete, terrain_cfg)
    find_bangle(world, athlete, bangle_cfg)

    world.para()
    rival_appears(world, rival, athlete, bangle_cfg)
    quarrel(world, rival, athlete, moral_cfg)

    world.para()
    trigger_cue(world, terrain_cfg, obstacle_cfg, bangle_cfg)
    if predict_outcome(athlete_cfg, obstacle_cfg) == "pulled_back":
        pull_back(world, athlete, rival, obstacle_cfg)
    else:
        slip_and_rescue(world, athlete, rival, obstacle_cfg)

    world.para()
    moral_resolution(world, athlete, rival, moral_cfg)

    world.facts.update(
        terrain=terrain_cfg,
        athlete_cfg=athlete_cfg,
        rival_cfg=rival_cfg,
        obstacle_cfg=obstacle_cfg,
        bangle_cfg=bangle_cfg,
        moral_cfg=moral_cfg,
        athlete=athlete,
        rival=rival,
        owner=world.get("judge"),
        outcome=predict_outcome(athlete_cfg, obstacle_cfg),
        revealed=world.get("obstacle").meters["revealed"] >= THRESHOLD,
        rival_safe=rival.meters["safe"] >= THRESHOLD,
        holder=world.get("bangle").attrs.get("holder"),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    athlete = f["athlete_cfg"]
    rival = f["rival_cfg"]
    bangle = f["bangle_cfg"]
    moral = f["moral_cfg"]
    obstacle = f["obstacle_cfg"]
    return [
        f'Write a short fable for young children that includes the words "bangle" and "athletic".',
        f"Tell a fable about an athletic {athlete.species}, a jealous {rival.species}, and {bangle.phrase} that brings a surprising warning near {obstacle.label}.",
        f"Write a conflict-and-surprise animal fable that teaches {moral.noun} and ends with a clear moral sentence.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    athlete = f["athlete"]
    rival = f["rival"]
    obstacle = f["obstacle_cfg"]
    bangle = f["bangle_cfg"]
    moral = f["moral_cfg"]
    owner = f["owner"]
    outcome = f["outcome"]
    items: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {athlete.id}, an athletic {f['athlete_cfg'].species}, and {rival.id}, a rival who wanted a shiny bangle. Judge Heron matters too, because the bangle really belonged to {owner.label}.",
        ),
        (
            f"Why did {rival.id} grab the bangle?",
            f"{rival.id} thought the bangle's shine would make {rival.pronoun('object')} seem grand without any hard practice. The conflict began because {athlete.id} cared more about character and training than show.",
        ),
        (
            "What was the surprise in the story?",
            f"The surprise was that the bangle did not help anyone look important; it gave a warning instead. {bangle.phrase.capitalize()} revealed {obstacle.label}, which is what kept the danger from winning.",
        ),
    ]
    if outcome == "pulled_back":
        items.append(
            (
                f"How did {athlete.id} save {rival.id}?",
                f"{athlete.id} saw the danger in time and yanked {rival.id} back before {rival.pronoun()} stepped into it. That showed real athletic strength, because quick feet were used to protect someone, not to boast.",
            )
        )
    else:
        items.append(
            (
                f"How did {athlete.id} help after {rival.id} slipped?",
                f"{rival.id} slid at the edge of the hidden danger, and {athlete.id} leapt in to pull {rival.pronoun('object')} out. The rescue worked because {athlete.id} was strong, quick, and calm when the trail turned dangerous.",
            )
        )
    items.append(
        (
            "What lesson did the animals learn?",
            f"They learned that {moral.lesson} The ending proves it, because the one with the strongest character handled the bangle rightly after the quarrel.",
        )
    )
    return items


KNOWLEDGE = {
    "bangle": [
        (
            "What is a bangle?",
            "A bangle is a round bracelet that slips over a hand and rests on the wrist. It can be plain or shiny, but it is still just an object.",
        )
    ],
    "athletic": [
        (
            "What does athletic mean?",
            "Athletic means strong, quick, and good at moving your body. An athletic animal or person can often run, jump, or climb well because they practice.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means choosing to help or comfort someone instead of hurting them back. It is a way of using your strength gently.",
        )
    ],
    "honesty": [
        (
            "What is honesty?",
            "Honesty means telling the truth and returning what is not yours. People trust honest hearts because they do not hide or pretend.",
        )
    ],
    "humility": [
        (
            "What is humility?",
            "Humility means not bragging and not thinking shiny things make you better than others. A humble heart cares more about what is true than about showing off.",
        )
    ],
    "fable": [
        (
            "What is a fable?",
            "A fable is a short story, often about animals, that teaches a lesson. The lesson is called the moral.",
        )
    ],
    "ditch": [
        (
            "Why is a hidden ditch dangerous?",
            "A hidden ditch is dangerous because it looks like flat ground until someone steps too close. A runner can slide in before noticing it.",
        )
    ],
    "burrow": [
        (
            "Why can a hidden burrow be dangerous on a trail?",
            "A hidden burrow can catch a foot or hoof if it is covered by grass. That can make a fast runner stumble badly.",
        )
    ],
    "stone": [
        (
            "Why are cracks in stone dangerous?",
            "A narrow crack can trap a foot or paw between hard edges. That is why careful runners watch the ground as well as the finish line.",
        )
    ],
}
KNOWLEDGE_ORDER = ["fable", "bangle", "athletic", "kindness", "honesty", "humility", "ditch", "burrow", "stone"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"fable", "bangle", "athletic", world.facts["moral_cfg"].id}
    obstacle = world.facts["obstacle_cfg"]
    if obstacle.id == "reed_ditch":
        tags.add("ditch")
    elif obstacle.id == "burrow":
        tags.add("burrow")
    elif obstacle.id == "stone_crack":
        tags.add("stone")
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
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v not in ("", [], {}, set())}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        terrain="meadow",
        athlete="gazelle",
        rival="magpie",
        obstacle="burrow",
        bangle="silver",
        moral="kindness",
    ),
    StoryParams(
        terrain="hill",
        athlete="goat",
        rival="fox",
        obstacle="stone_crack",
        bangle="brass",
        moral="humility",
    ),
    StoryParams(
        terrain="riverbank",
        athlete="gazelle",
        rival="monkey",
        obstacle="reed_ditch",
        bangle="glass",
        moral="honesty",
    ),
    StoryParams(
        terrain="meadow",
        athlete="hare",
        rival="fox",
        obstacle="reed_ditch",
        bangle="brass",
        moral="kindness",
    ),
]


ASP_RULES = r"""
% reasonableness gate
valid(T,A,O,B) :- terrain(T), athlete(A), obstacle(O), bangle(B),
                  affords(T,O), cue(B,C), obstacle_cue(O,C),
                  agility(A,Ag), rescue_need(O,R), Ag >= R.

% outcome model
outcome(pulled_back) :- chosen_athlete(A), chosen_obstacle(O),
                        agility(A,Ag), difficulty(O,D), Ag > D.
outcome(lifted_out)  :- chosen_athlete(A), chosen_obstacle(O),
                        agility(A,Ag), difficulty(O,D), not Ag > D.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for terrain_id, terrain in TERRAINS.items():
        lines.append(asp.fact("terrain", terrain_id))
        for obstacle_id in sorted(terrain.obstacles):
            lines.append(asp.fact("affords", terrain_id, obstacle_id))
    for athlete_id, athlete in ANIMALS.items():
        lines.append(asp.fact("athlete", athlete_id))
        lines.append(asp.fact("agility", athlete_id, athlete.agility))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("obstacle_cue", obstacle_id, obstacle.cue_type))
        lines.append(asp.fact("difficulty", obstacle_id, obstacle.difficulty))
        lines.append(asp.fact("rescue_need", obstacle_id, obstacle.rescue_need))
    for bangle_id, bangle in BANGLES.items():
        lines.append(asp.fact("bangle", bangle_id))
        lines.append(asp.fact("cue", bangle_id, bangle.cue_type))
    for moral_id in MORALS:
        lines.append(asp.fact("moral", moral_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_athlete", params.athlete),
            asp.fact("chosen_obstacle", params.obstacle),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def generate_smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "bangle" not in sample.story.lower():
        raise StoryError("Smoke test failed: generated story was empty or missing 'bangle'.")
    if "athletic" not in " ".join(sample.prompts).lower() and "athletic" not in sample.story.lower():
        raise StoryError("Smoke test failed: storyworld lost the required seed word 'athletic'.")


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
    for seed in range(50):
        args = build_parser().parse_args([])
        try:
            params = resolve_params(args, random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome cases differ.")
        for p in mismatches[:5]:
            print(" ", p)

    try:
        generate_smoke_test()
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - explicit verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A fable storyworld about an athletic animal, a bangle, a quarrel, a surprise, and a moral value."
    )
    ap.add_argument("--terrain", choices=sorted(TERRAINS))
    ap.add_argument("--athlete", choices=sorted(ANIMALS))
    ap.add_argument("--rival", choices=sorted(RIVALS))
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
    ap.add_argument("--bangle", choices=sorted(BANGLES))
    ap.add_argument("--moral", choices=sorted(MORALS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    terrain_id = args.terrain
    athlete_id = args.athlete
    obstacle_id = args.obstacle
    bangle_id = args.bangle

    if terrain_id and athlete_id and obstacle_id and bangle_id:
        terrain = TERRAINS[terrain_id]
        athlete = ANIMALS[athlete_id]
        obstacle = OBSTACLES[obstacle_id]
        bangle = BANGLES[bangle_id]
        if not (terrain_has_obstacle(terrain, obstacle) and cue_matches(bangle, obstacle) and can_rescue(athlete, obstacle)):
            raise StoryError(explain_rejection(terrain, athlete, obstacle, bangle))

    combos = [
        combo
        for combo in valid_combos()
        if (args.terrain is None or combo[0] == args.terrain)
        and (args.athlete is None or combo[1] == args.athlete)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.bangle is None or combo[3] == args.bangle)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    terrain_id, athlete_id, obstacle_id, bangle_id = rng.choice(sorted(combos))
    rival_id = args.rival or rng.choice(sorted(RIVALS))
    moral_id = args.moral or rng.choice(sorted(MORALS))
    return StoryParams(
        terrain=terrain_id,
        athlete=athlete_id,
        rival=rival_id,
        obstacle=obstacle_id,
        bangle=bangle_id,
        moral=moral_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.terrain not in TERRAINS:
        raise StoryError(f"Unknown terrain: {params.terrain}")
    if params.athlete not in ANIMALS:
        raise StoryError(f"Unknown athlete: {params.athlete}")
    if params.rival not in RIVALS:
        raise StoryError(f"Unknown rival: {params.rival}")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"Unknown obstacle: {params.obstacle}")
    if params.bangle not in BANGLES:
        raise StoryError(f"Unknown bangle: {params.bangle}")
    if params.moral not in MORALS:
        raise StoryError(f"Unknown moral: {params.moral}")

    terrain = TERRAINS[params.terrain]
    athlete = ANIMALS[params.athlete]
    obstacle = OBSTACLES[params.obstacle]
    bangle = BANGLES[params.bangle]
    if not (terrain_has_obstacle(terrain, obstacle) and cue_matches(bangle, obstacle) and can_rescue(athlete, obstacle)):
        raise StoryError(explain_rejection(terrain, athlete, obstacle, bangle))

    world = tell(
        terrain_cfg=terrain,
        athlete_cfg=athlete,
        rival_cfg=RIVALS[params.rival],
        obstacle_cfg=obstacle,
        bangle_cfg=bangle,
        moral_cfg=MORALS[params.moral],
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (terrain, athlete, obstacle, bangle) combos:\n")
        for terrain, athlete, obstacle, bangle in combos:
            print(f"  {terrain:10} {athlete:9} {obstacle:11} {bangle}")
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
            header = (
                f"### {ANIMALS[p.athlete].name} vs {RIVALS[p.rival].name}: "
                f"{p.bangle} bangle at {p.terrain} ({outcome_of(p)}, {p.moral})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
