#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bbd_mystery_to_solve_fairy_tale.py
=============================================================

A standalone story world for a tiny fairy-tale mystery. A child hero notices
that something lovely has gone missing, follows a clue, meets the true taker,
learns the gentle reason behind the trouble, and helps set things right.

Seed requirement
----------------
This world always includes the word "bbd" as part of the central clue: a tiny
golden tag stamped with the letters BBD. The letters are visible in the story
text, but their meaning is only explained once the mystery is solved.

Run it
------
    python storyworlds/worlds/gpt-5.4/bbd_mystery_to_solve_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/bbd_mystery_to_solve_fairy_tale.py --place glade --lost bell --suspect bird
    python storyworlds/worlds/gpt-5.4/bbd_mystery_to_solve_fairy_tale.py --lost crown --suspect mole
    python storyworlds/worlds/gpt-5.4/bbd_mystery_to_solve_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/bbd_mystery_to_solve_fairy_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/bbd_mystery_to_solve_fairy_tale.py --qa --json
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "fairy_girl", "witch"}
        male = {"boy", "king", "prince", "fairy_boy", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    title: str
    opening: str
    hiding_spots: list[str] = field(default_factory=list)
    travelers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class LostThing:
    id: str
    label: str
    phrase: str
    home: str
    gleam: str
    use: str
    desired_by: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    phrase: str
    type: str
    movement: str
    clue: str
    reason_templates: dict[str, str] = field(default_factory=dict)
    bbd_meaning: str = ""
    can_visit: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    type: str
    advice: str
    method: str
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


def _r_missing_worry(world: World) -> list[str]:
    hero = world.entities.get("hero")
    lost = world.entities.get("lost")
    if not hero or not lost:
        return []
    if lost.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    hero.memes["resolve"] += 1
    return []


def _r_clue_suspicion(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if not hero:
        return []
    if world.facts.get("clue_found") != "bbd_tag":
        return []
    sig = ("clue_suspicion", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["curiosity"] += 1
    hero.memes["hope"] += 1
    return []


def _r_reason_softens(world: World) -> list[str]:
    hero = world.entities.get("hero")
    suspect = world.entities.get("suspect")
    if not hero or not suspect:
        return []
    if suspect.memes["ashamed"] < THRESHOLD:
        return []
    sig = ("reason_softens", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["kindness"] += 1
    hero.memes["anger"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="clue_suspicion", tag="emotional", apply=_r_clue_suspicion),
    Rule(name="reason_softens", tag="emotional", apply=_r_reason_softens),
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
        for sent in produced:
            world.say(sent)
    return produced


def suspect_can_take(place: Place, lost: LostThing, suspect: Suspect) -> bool:
    return place.id in suspect.can_visit and lost.id in suspect.reason_templates


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for lost_id, lost in LOST_THINGS.items():
            for suspect_id, suspect in SUSPECTS.items():
                if suspect_can_take(place, lost, suspect):
                    combos.append((place_id, lost_id, suspect_id))
    return combos


def reason_text(lost: LostThing, suspect: Suspect) -> str:
    return suspect.reason_templates[lost.id]


def resolve_spot(place: Place, rng: random.Random) -> str:
    return rng.choice(place.hiding_spots)


def predict_solution(place: Place, lost: LostThing, suspect: Suspect) -> dict:
    if not suspect_can_take(place, lost, suspect):
        return {"solvable": False, "reason": ""}
    return {"solvable": True, "reason": reason_text(lost, suspect)}


def open_tale(world: World, hero: Entity, place: Place, lost: LostThing) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"In {place.title}, where dew shone like tiny stars, there lived {hero.phrase}. "
        f"{place.opening}"
    )
    world.say(
        f"Each morning, {hero.id} loved to visit {lost.home}, where {lost.phrase} "
        f"{lost.gleam}."
    )


def discover_missing(world: World, hero: Entity, lost_ent: Entity, lost: LostThing) -> None:
    lost_ent.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But one pale-gold morning, the place was empty. {lost.phrase.capitalize()} "
        f"was gone."
    )
    world.say(
        f"{hero.id} pressed a hand to {hero.pronoun('possessive')} heart. "
        f'"Oh dear," {hero.pronoun()} whispered. "Who would take {lost.label}, '
        f'and why?"'
    )


def inspect_scene(world: World, hero: Entity, helper: Entity, helper_cfg: Helper, suspect: Suspect) -> None:
    world.say(
        f"Just then {helper.phrase} came by. {helper.id} listened, blinked slowly, "
        f"and said, {helper_cfg.advice}"
    )
    hero.memes["trust"] += 1
    helper.memes["care"] += 1
    world.say(
        f"So {hero.id} and {helper.id} looked carefully instead of rushing. "
        f"They found {suspect.clue} and, beside it, a tiny golden tag stamped with "
        f"the letters bbd."
    )
    world.facts["clue_found"] = "bbd_tag"
    propagate(world, narrate=False)


def follow_clue(world: World, hero: Entity, helper: Entity, place: Place, spot: str) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f'"A clue is a whisper that points somewhere," said {helper.id}. '
        f"Together they followed the trail past ferns and stepping-stones until it led to {spot}."
    )


def confront_gently(world: World, hero: Entity, suspect_ent: Entity, suspect: Suspect, lost: LostThing) -> None:
    suspect_ent.memes["startled"] += 1
    world.say(
        f"There, tucked in the shade, was {suspect.phrase} with {lost.phrase} beside "
        f"{suspect_ent.pronoun('object')}."
    )
    world.say(
        f'{hero.id} took a steady breath. "Did you take {lost.label}?" '
        f"{hero.pronoun()} asked."
    )


def reveal_reason(world: World, suspect_ent: Entity, suspect: Suspect, lost: LostThing) -> None:
    suspect_ent.memes["ashamed"] += 1
    suspect_ent.memes["need"] += 1
    propagate(world, narrate=False)
    reason = reason_text(lost, suspect)
    world.say(
        f'{suspect_ent.id} lowered {suspect_ent.pronoun("possessive")} head. '
        f'"I did," {suspect_ent.pronoun()} said softly. "{reason}"'
    )
    world.say(
        f"Then {suspect_ent.pronoun().capitalize()} touched the small tag. "
        f'"The letters bbd stand for {suspect.bbd_meaning}," {suspect_ent.pronoun()} added.'
    )
    world.facts["reason"] = reason


def mend(world: World, hero: Entity, helper: Entity, suspect_ent: Entity, lost_ent: Entity, lost: LostThing) -> None:
    hero.memes["kindness"] += 1
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    helper.memes["joy"] += 1
    suspect_ent.memes["relief"] += 1
    suspect_ent.memes["trust"] += 1
    lost_ent.meters["missing"] = 0.0
    lost_ent.meters["returned"] += 1
    world.say(
        f"{hero.id} saw that this was not a wicked theft at all, but a frightened mistake. "
        f"So {hero.pronoun()} and {helper.id} helped {suspect_ent.id} carry {lost.label} back."
    )
    world.say(
        f"Together they made a fair new plan for its {lost.use}, so no one would need to sneak again."
    )


def ending_image(world: World, hero: Entity, lost: LostThing, suspect_ent: Entity) -> None:
    world.say(
        f"By evening, {lost.phrase} was home once more, shining softly in the dusk. "
        f"{hero.id} smiled to hear its gentle sound again."
    )
    world.say(
        f"And whenever {hero.id} later saw {suspect_ent.id}, neither of them thought first of the missing thing. "
        f"They thought of the day a mystery became mercy."
    )


def tell(
    place: Place,
    lost: LostThing,
    suspect: Suspect,
    helper_cfg: Helper,
    hero_name: str = "Elin",
    hero_type: str = "girl",
    helper_name: str = "Moss",
    spot: str = "",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        phrase=f"a little {hero_type} with a silver cloak",
        role="hero",
        traits=["gentle", "brave"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        phrase=helper_cfg.phrase,
        role="helper",
        traits=["wise"],
    ))
    suspect_ent = world.add(Entity(
        id=suspect.label.capitalize(),
        kind="character",
        type=suspect.type,
        label=suspect.label,
        phrase=suspect.phrase,
        role="suspect",
        traits=["troubled"],
    ))
    lost_ent = world.add(Entity(
        id="lost",
        kind="thing",
        type="treasure",
        label=lost.label,
        phrase=lost.phrase,
        role="lost",
        tags=set(lost.tags),
    ))

    open_tale(world, hero, place, lost)
    world.para()
    discover_missing(world, hero, lost_ent, lost)
    inspect_scene(world, hero, helper, helper_cfg, suspect)
    follow_clue(world, hero, helper, place, spot)
    world.para()
    confront_gently(world, hero, suspect_ent, suspect, lost)
    reveal_reason(world, suspect_ent, suspect, lost)
    world.para()
    mend(world, hero, helper, suspect_ent, lost_ent, lost)
    ending_image(world, hero, lost, suspect_ent)

    world.facts.update(
        hero=hero,
        helper=helper,
        suspect=suspect_ent,
        suspect_cfg=suspect,
        place=place,
        lost=lost_ent,
        lost_cfg=lost,
        clue=suspect.clue,
        clue_word="bbd",
        spot=spot,
        solved=lost_ent.meters["returned"] >= THRESHOLD,
        bbd_meaning=suspect.bbd_meaning,
    )
    return world


PLACES = {
    "glade": Place(
        id="glade",
        title="the Moonpetal Glade",
        opening="A ring of mushrooms circled the grass, and a brook hummed under a willow bridge.",
        hiding_spots=["the willow roots", "a ferny hollow", "the mossy bridge"],
        travelers={"bird", "fox", "hedgehog"},
        tags={"forest"},
    ),
    "tower": Place(
        id="tower",
        title="the Briarbell Tower",
        opening="A winding stair curled around the stone, and lantern flowers burned with sleepy light.",
        hiding_spots=["the stair alcove", "the lantern room", "the ivy arch"],
        travelers={"bird", "mole", "cat"},
        tags={"tower"},
    ),
    "garden": Place(
        id="garden",
        title="the Roseglass Garden",
        opening="Crystal drops hung on the roses, and small paths twined between pear trees.",
        hiding_spots=["the rose arbor", "the pear-tree roots", "the little tool shed"],
        travelers={"mole", "fox", "hedgehog"},
        tags={"garden"},
    ),
}

LOST_THINGS = {
    "bell": LostThing(
        id="bell",
        label="the silver bell",
        phrase="the silver bell",
        home="a velvet cushion by the willow gate",
        gleam="caught the morning light like a drop of moon",
        use="ringing at dusk so everyone could find the safe path home",
        desired_by={"bird"},
        tags={"bell", "sound"},
    ),
    "crown": LostThing(
        id="crown",
        label="the dewdrop crown",
        phrase="the dewdrop crown",
        home="a carved oak stand near the rose path",
        gleam="sparkled with blue dew-beads",
        use="being worn at the moon feast",
        desired_by={"fox", "cat"},
        tags={"crown", "dew"},
    ),
    "seeds": LostThing(
        id="seeds",
        label="the star-seed pouch",
        phrase="the star-seed pouch",
        home="a hook beside the garden gate",
        gleam="glittered with stitched silver thread",
        use="planting glow-flowers before nightfall",
        desired_by={"hedgehog", "mole"},
        tags={"seeds", "garden"},
    ),
}

SUSPECTS = {
    "bird": Suspect(
        id="bird",
        label="Pip",
        phrase="a blue bird with rain-bright feathers",
        type="bird",
        movement="fluttered",
        clue="a scatter of blue feathers",
        reason_templates={
            "bell": "My little nestlings were afraid of the dark cave wind, and I thought its ringing might comfort them.",
        },
        bbd_meaning="Blue Bird Delivery",
        can_visit={"glade", "tower"},
        tags={"bird", "nest"},
    ),
    "fox": Suspect(
        id="fox",
        label="Rill",
        phrase="a young fox with a burr on one ear",
        type="fox",
        movement="padded",
        clue="soft pawprints and one red hair caught on a thorn",
        reason_templates={
            "crown": "I wanted to look splendid at the moon feast too, because no one ever asks a fox to dance first.",
        },
        bbd_meaning="Borrowed Before Dancing",
        can_visit={"glade", "garden"},
        tags={"fox", "feast"},
    ),
    "mole": Suspect(
        id="mole",
        label="Tumble",
        phrase="a small mole in a patched velvet coat",
        type="mole",
        movement="tunneled",
        clue="crumbled earth and a neat little digging mark",
        reason_templates={
            "seeds": "The tunnel roof by my door was sinking, and I hoped to grow quick roots there before it fell.",
            "crown": "I wanted to study the dew-beads up close, because I have never seen the moon feast clearly from underground.",
        },
        bbd_meaning="Burrow Builder's Bundle",
        can_visit={"tower", "garden"},
        tags={"mole", "burrow"},
    ),
    "hedgehog": Suspect(
        id="hedgehog",
        label="Bram",
        phrase="a hedgehog with a basket tied behind one shoulder",
        type="hedgehog",
        movement="trundled",
        clue="tiny leaf scraps and careful little footprints",
        reason_templates={
            "seeds": "The winter corner of the wood looked bare, and I wanted to plant something kind before the frost came.",
        },
        bbd_meaning="Brave Briar Delivery",
        can_visit={"glade", "garden"},
        tags={"hedgehog", "winter"},
    ),
}

HELPERS = {
    "owl": Helper(
        id="owl",
        label="owl",
        phrase="an old owl in a shawl of feathers",
        type="owl",
        advice='"Mysteries do not like stomping feet. They open best to quiet eyes."',
        method="observe",
        tags={"owl", "clue"},
    ),
    "frog": Helper(
        id="frog",
        label="frog",
        phrase="a green frog with a reed walking-stick",
        type="frog",
        advice='"A worried heart sees only loss. A patient heart sees tracks."',
        method="track",
        tags={"frog", "clue"},
    ),
}


@dataclass
class StoryParams:
    place: str
    lost: str
    suspect: str
    helper: str
    hero_name: str
    hero_type: str
    helper_name: str
    spot: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "bell": [
        (
            "What is a bell used for?",
            "A bell makes a clear ringing sound that can call people together or help them know it is time for something."
        )
    ],
    "crown": [
        (
            "What is a crown?",
            "A crown is a special headpiece that shows honor or celebration. In fairy tales, it often means someone has an important part in a feast or ceremony."
        )
    ],
    "seeds": [
        (
            "What do seeds do?",
            "Seeds can grow into plants when they are put into soil and given water and light. Tiny seeds can become flowers, herbs, or trees."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. It might be a footprint, a feather, or a scrap that points to what happened."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something you do not understand at first and need to solve. You solve it by noticing facts and thinking carefully."
        )
    ],
    "kindness": [
        (
            "Why can kindness help solve a problem?",
            "Kindness helps people tell the truth when they are scared or ashamed. A gentle question can open a stuck heart better than shouting can."
        )
    ],
    "bird": [
        (
            "Why do birds build nests?",
            "Birds build nests to keep their eggs or babies safe. A nest needs to feel sheltered and comfortable."
        )
    ],
    "fox": [
        (
            "Why might someone want to feel included at a feast?",
            "Everyone wants to feel welcome sometimes. When someone feels left out, they may make poor choices because they are lonely."
        )
    ],
    "mole": [
        (
            "Why do moles dig tunnels?",
            "Moles live underground and dig tunnels to move around and make homes. Soft earth is easy for them to shape."
        )
    ],
    "hedgehog": [
        (
            "Why do animals prepare for winter?",
            "Cold seasons can be hard, so animals often gather food or make cozy places ahead of time. Getting ready early helps them stay safe."
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "clue", "kindness", "bell", "crown", "seeds", "bird", "fox", "mole", "hedgehog"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    lost = f["lost_cfg"]
    place = f["place"]
    suspect = f["suspect_cfg"]
    return [
        f'Write a short fairy tale for a 3-to-5-year-old that includes the word "bbd" and begins with a missing treasure in {place.title}.',
        f"Tell a gentle mystery-to-solve story where {hero.id} notices that {lost.label} is gone, follows clues, and discovers that {suspect.label} had a sad reason for taking it.",
        f'Write a child-facing fairy tale mystery where the hero solves the problem by noticing clues and asking kindly instead of accusing anyone at once.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    suspect = f["suspect"]
    lost = f["lost_cfg"]
    place = f["place"]
    clue = f["clue"]
    spot = f["spot"]
    meaning = f["bbd_meaning"]
    reason = f["reason"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who lives in {place.title}, and about the mystery of {lost.label}. {helper.id} helps with the clues, and {suspect.id} turns out to be the one who took it."
        ),
        (
            f"What was missing?",
            f"{lost.phrase.capitalize()} was missing from {lost.home}. That loss started the whole mystery because something important had vanished from its proper place."
        ),
        (
            "What clue did they find?",
            f"They found {clue} and a tiny golden tag stamped with the letters bbd. Those signs told them that someone had carried the missing thing away instead of it simply being lost by accident."
        ),
        (
            "How did they solve the mystery?",
            f"They looked closely, followed the clue trail, and went all the way to {spot}. Then {hero.id} asked a calm question instead of shouting, which helped the truth come out."
        ),
        (
            "What did bbd mean in this story?",
            f'In this story, bbd meant "{meaning}." The letters on the tag connected the clue to the one who had taken the missing thing.'
        ),
        (
            f"Why did {suspect.id} take {lost.label}?",
            f"{suspect.id} took it because {reason} {hero.id} learned that the taking came from worry or longing, not from meanness alone."
        ),
    ]
    if f.get("solved"):
        qa.append(
            (
                "How did the story end?",
                f"The missing thing was carried home and a fair plan was made for its {lost.use}. The ending shows that the mystery was solved and the hearts in the story grew softer too."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mystery", "clue", "kindness"}
    tags |= set(f["lost_cfg"].tags)
    tags |= set(f["suspect_cfg"].tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="glade",
        lost="bell",
        suspect="bird",
        helper="owl",
        hero_name="Elin",
        hero_type="girl",
        helper_name="Moss",
        spot="the willow roots",
    ),
    StoryParams(
        place="garden",
        lost="crown",
        suspect="fox",
        helper="frog",
        hero_name="Rowan",
        hero_type="boy",
        helper_name="Pebble",
        spot="the rose arbor",
    ),
    StoryParams(
        place="garden",
        lost="seeds",
        suspect="hedgehog",
        helper="owl",
        hero_name="Mira",
        hero_type="girl",
        helper_name="Thimble",
        spot="the pear-tree roots",
    ),
    StoryParams(
        place="tower",
        lost="seeds",
        suspect="mole",
        helper="frog",
        hero_name="Ash",
        hero_type="boy",
        helper_name="Ripple",
        spot="the stair alcove",
    ),
    StoryParams(
        place="tower",
        lost="crown",
        suspect="mole",
        helper="owl",
        hero_name="Nella",
        hero_type="girl",
        helper_name="Moss",
        spot="the lantern room",
    ),
]


def explain_rejection(place: Place, lost: LostThing, suspect: Suspect) -> str:
    if place.id not in suspect.can_visit:
        return (
            f"(No story: {suspect.label} does not plausibly travel through {place.title}, "
            f"so the clue trail would feel unfair. Pick a suspect who can visit that place.)"
        )
    if lost.id not in suspect.reason_templates:
        return (
            f"(No story: {suspect.label} has no believable fairy-tale reason to take {lost.label}. "
            f"Choose a different suspect or a different missing thing.)"
        )
    return "(No story: this mystery setup is not reasonable.)"


ASP_RULES = r"""
valid(Place, Lost, Suspect) :- place(Place), lost(Lost), suspect(Suspect),
                               visits(Suspect, Place), motive(Suspect, Lost).

solvable(Place, Lost, Suspect) :- valid(Place, Lost, Suspect).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for lost_id in LOST_THINGS:
        lines.append(asp.fact("lost", lost_id))
    for suspect_id, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", suspect_id))
        for place_id in sorted(suspect.can_visit):
            lines.append(asp.fact("visits", suspect_id, place_id))
        for lost_id in sorted(suspect.reason_templates):
            lines.append(asp.fact("motive", suspect_id, lost_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
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
        if not sample.story or "bbd" not in sample.story.lower():
            raise StoryError("Smoke test failed: generated story was empty or missed the seed word.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale mystery storyworld with a gentle clue trail and a bbd tag."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--lost", choices=LOST_THINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible mystery setups derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Elin", "Mira", "Nella", "Luma", "Tansy", "Wren", "Ivy", "Pearl"]
BOY_NAMES = ["Ash", "Rowan", "Bram", "Pip", "Theo", "Alder", "Finn", "Milo"]
HELPER_NAMES = ["Moss", "Pebble", "Ripple", "Thimble", "Sage", "Dewdrop"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.lost and args.suspect:
        place = PLACES[args.place]
        lost = LOST_THINGS[args.lost]
        suspect = SUSPECTS[args.suspect]
        if not suspect_can_take(place, lost, suspect):
            raise StoryError(explain_rejection(place, lost, suspect))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.lost is None or combo[1] == args.lost)
        and (args.suspect is None or combo[2] == args.suspect)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, lost_id, suspect_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper_name = rng.choice(HELPER_NAMES)
    spot = resolve_spot(PLACES[place_id], rng)

    return StoryParams(
        place=place_id,
        lost=lost_id,
        suspect=suspect_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
    spot=spot,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        lost = LOST_THINGS[params.lost]
        suspect = SUSPECTS[params.suspect]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]!r} is not a known option.)") from err

    if not suspect_can_take(place, lost, suspect):
        raise StoryError(explain_rejection(place, lost, suspect))

    pred = predict_solution(place, lost, suspect)
    if not pred["solvable"]:
        raise StoryError("(This mystery is not solvable in the current world model.)")

    world = tell(
        place=place,
        lost=lost,
        suspect=suspect,
        helper_cfg=helper,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        helper_name=params.helper_name,
        spot=params.spot,
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
        print(f"{len(combos)} compatible (place, lost, suspect) mystery setups:\n")
        for place_id, lost_id, suspect_id in combos:
            print(f"  {place_id:8} {lost_id:7} {suspect_id}")
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
            header = f"### {p.hero_name}: {p.lost} in {p.place} (suspect: {p.suspect})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
