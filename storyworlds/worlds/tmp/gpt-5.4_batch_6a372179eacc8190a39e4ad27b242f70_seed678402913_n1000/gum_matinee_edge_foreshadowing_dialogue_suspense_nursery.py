#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gum_matinee_edge_foreshadowing_dialogue_suspense_nursery.py
======================================================================================

A standalone storyworld about a child at a matinee who hides gum on an edge,
then learns that a tiny sticky thing can become a big problem in the dark.

The stories are written in a gentle nursery-rhyme style, but the world model is
classical and state-driven: characters and objects are typed entities with
physical meters and emotional memes, a small forward-chaining rule engine moves
the world ahead, and prose is rendered from the simulated state.

Premise
-------
Two children go to a matinee. One child wants to save a piece of gum for later,
so the gum gets pressed onto some nearby edge. In the dark, something important
snags there -- a ticket stub, a sleeve, or a shoe ribbon -- and the child leans
or stumbles toward danger. A calm grown-up helps, and the ending proves what
changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/gum_matinee_edge_foreshadowing_dialogue_suspense_nursery.py
    python storyworlds/worlds/gpt-5.4/gum_matinee_edge_foreshadowing_dialogue_suspense_nursery.py --edge balcony_rail
    python storyworlds/worlds/gpt-5.4/gum_matinee_edge_foreshadowing_dialogue_suspense_nursery.py --edge curtain_hem
    python storyworlds/worlds/gpt-5.4/gum_matinee_edge_foreshadowing_dialogue_suspense_nursery.py --all --qa
    python storyworlds/worlds/gpt-5.4/gum_matinee_edge_foreshadowing_dialogue_suspense_nursery.py --verify
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
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "steady", "watchful", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    sticky: bool = False
    edge: bool = False
    movable: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "usheress"}
        male = {"boy", "father", "man", "usher"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "usher": "usher",
            "usheress": "usher",
        }.get(self.type, self.label or self.type)


@dataclass
class Matinee:
    id: str
    title: str
    opening: str
    stage_image: str
    cheer: str
    tags: set[str] = field(default_factory=set)


@dataclass
class EdgeConfig:
    id: str
    label: str
    phrase: str
    danger: int
    zones: set[str]
    rhyme: str
    flippable: bool = False
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class SnagItem:
    id: str
    label: str
    phrase: str
    zone: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_snag(world: World) -> list[str]:
    gum = world.entities.get("gum")
    edge = world.entities.get("edge")
    snag = world.entities.get("snag")
    child = world.entities.get("instigator")
    if not gum or not edge or not snag or not child:
        return []
    if gum.meters["placed"] < THRESHOLD or snag.meters["moving"] < THRESHOLD:
        return []
    if snag.attrs.get("zone") not in edge.attrs.get("zones", set()):
        return []
    sig = ("snag", edge.id, snag.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    snag.meters["stuck"] += 1
    child.memes["alarm"] += 1
    world.get("room").meters["danger"] += edge.attrs.get("danger", 1)
    return ["__snag__"]


def _r_lean(world: World) -> list[str]:
    child = world.entities.get("instigator")
    snag = world.entities.get("snag")
    if not child or not snag:
        return []
    if snag.meters["stuck"] < THRESHOLD:
        return []
    sig = ("lean", child.id, snag.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["off_balance"] += 1
    child.memes["fear"] += 1
    return ["__lean__"]


CAUSAL_RULES = [
    Rule(name="snag", tag="physical", apply=_r_snag),
    Rule(name="lean", tag="physical", apply=_r_lean),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def hazard_at_risk(edge: EdgeConfig, snag: SnagItem) -> bool:
    return edge.safe and snag.zone in edge.zones


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def snag_severity(edge: EdgeConfig, delay: int) -> int:
    return edge.danger + delay


def is_contained(response: Response, edge: EdgeConfig, delay: int) -> bool:
    return response.power >= snag_severity(edge, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (3.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_snag(world: World) -> dict:
    sim = world.copy()
    _place_gum(sim, narrate=False)
    _show_begins(sim, narrate=False)
    return {
        "snagged": sim.get("snag").meters["stuck"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def _place_gum(world: World, narrate: bool = True) -> None:
    gum = world.get("gum")
    gum.meters["placed"] += 1
    world.get("edge").meters["sticky"] += 1
    if narrate:
        world.say("The little wad of gum sat still, but still things can wait like traps.")


def _show_begins(world: World, narrate: bool = True) -> None:
    snag = world.get("snag")
    snag.meters["moving"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, a: Entity, b: Entity, parent: Entity, matinee: Matinee) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"At the matinee, when the noon bells hummed and the posters shone, "
        f"{a.id} and {b.id} skipped in with {a.pronoun('possessive')} {parent.label_word}. "
        f"{matinee.opening}"
    )
    world.say(
        f'On the stage, {matinee.stage_image}. "{matinee.cheer}!" whispered {b.id}.'
    )


def gum_gift(world: World, a: Entity) -> None:
    world.say(
        f"In {a.id}'s pocket lay a piece of gum, soft and sweet and pink as dawn."
    )
    world.say(
        "It looked like a tiny thing, but tiny things can cling in the dark."
    )


def warning(world: World, b: Entity, a: Entity, parent: Entity, edge: EdgeConfig) -> None:
    pred = predict_snag(world)
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.id} gave the smallest shiver, as if the dark itself had nodded."
    world.say(
        f'{b.id} tugged {a.id}\'s sleeve. "Please do not press your gum on {edge.phrase}," '
        f'{b.pronoun()} said. "Things catch there at the edge when the room goes dim."{extra}'
    )
    world.say(
        f'"And gum belongs in paper, not on seats or rails," said {parent.label_word}.'
    )


def defy(world: World, a: Entity, b: Entity, edge: EdgeConfig) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"Just for later," said {a.id}. Because {a.id} was older, {b.id} could not quite stop '
            f"{a.pronoun('object')}. With one quick press, {a.id} tucked the gum on {edge.phrase}."
        )
    else:
        world.say(
            f'"Just for later," said {a.id}, and with one quick press, {a.pronoun()} tucked the gum on {edge.phrase}.'
        )
    _place_gum(world, narrate=False)
    world.say(edge.rhyme)


def back_down(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["lesson"] += 1
    world.say(
        f'{a.id} looked at the darkening rows, then at {b.id}, and sighed. '
        f'"You are right," {a.pronoun()} said. {a.pronoun().capitalize()} folded the gum into its paper and gave it to '
        f"{a.pronoun('possessive')} {parent.label_word} to keep."
    )
    world.say(
        "The edge stayed clean, and the trouble stayed only a shiver in a thought."
    )


def show_turn(world: World, matinee: Matinee, snag_cfg: SnagItem) -> None:
    world.say(
        f"Then the hall went hush-hush-hush. The {matinee.title} began, the lamps grew low, "
        f"and {world.get('snag').label} brushed by the edge."
    )
    _show_begins(world, narrate=False)
    if world.get("snag").meters["stuck"] >= THRESHOLD:
        world.say(
            f"All at once, {snag_cfg.phrase} stuck fast in the gum with a tiny snick."
        )
    if world.get("instigator").meters["off_balance"] >= THRESHOLD:
        world.say(
            "Pull came a tug, tug came a lean, and for one breath nobody knew what would happen next."
        )


def alarm(world: World, b: Entity, a: Entity, snag_cfg: SnagItem, helper: Entity) -> None:
    b.memes["fear"] += 1
    world.say(
        f'"{a.id}!" cried {b.id}. "{snag_cfg.label.capitalize()} is stuck!"'
    )
    world.say(f'"Stay still," said the {helper.label_word}. "Not one more inch toward the edge."')


def rescue(world: World, helper: Entity, response: Response, a: Entity, snag_cfg: SnagItem, edge: EdgeConfig) -> None:
    world.get("snag").meters["stuck"] = 0.0
    world.get("instigator").meters["off_balance"] = 0.0
    world.get("room").meters["danger"] = 0.0
    world.say(
        f"The {helper.label_word} {response.text}."
    )
    world.say(
        f"Soon {snag_cfg.phrase} was free, the gum was gone from {edge.phrase}, and {a.id} was standing safe again."
    )


def lesson(world: World, helper: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'Then the {helper.label_word} bent low and spoke in a voice soft as velvet. '
        f'"A little gum can make a big stop in the dark. When you have gum, keep it in paper or throw it away the proper way."'
    )
    world.say(
        f'"We will," said {a.id} and {b.id}, small and sure together.'
    )


def safe_end(world: World, matinee: Matinee, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"The show went on. {matinee.stage_image.capitalize()}, and this time the children watched with hands in laps and feet far from the edge."
    )
    world.say(
        f"When the matinee ended, {a.id} dropped the old wrapper into the bin, and {b.id} sang, "
        f'"Sticky sweet belongs in paper neat!"'
    )


def rescue_fail(world: World, helper: Entity, response: Response, a: Entity, edge: EdgeConfig) -> None:
    world.get("instigator").meters["off_balance"] += 1
    a.memes["fear"] += 1
    world.say(
        f"The {helper.label_word} {response.fail}, but the tug had already pulled {a.id} down onto the step with a bump."
    )
    if edge.flippable:
        world.say(
            "Programs fluttered like pale moths, and the whole row gasped."
        )
    else:
        world.say(
            "The row gave a startled rustle, and the music paused."
        )


def sore_but_safe(world: World, helper: Entity, a: Entity, b: Entity, matinee: Matinee) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    a.meters["bumped"] += 1
    world.say(
        f"{a.id} was safe, only shaken with a sore knee and wet eyes. {b.id} held {a.pronoun('possessive')} hand while the {helper.label_word} checked the scrape."
    )
    world.say(
        f"They missed the rest of the matinee, but on the way home {a.id} never stopped thinking about how a tiny sticky lump had made such a sudden trouble."
    )
    world.say(
        'After that, gum always stayed wrapped, and edges stayed bare.'
    )


def tell(
    matinee: Matinee,
    edge_cfg: EdgeConfig,
    snag_cfg: SnagItem,
    response: Response,
    instigator: str = "Mina",
    instigator_gender: str = "girl",
    cautioner: str = "Pip",
    cautioner_gender: str = "boy",
    trait: str = "careful",
    parent_type: str = "mother",
    helper_type: str = "usher",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 5,
    relation: str = "siblings",
) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
    ))
    world.add(Entity(
        id="room",
        type="theater",
        label="the matinee hall",
        movable=False,
    ))
    world.add(Entity(
        id="gum",
        type="gum",
        label="gum",
        phrase="a pink piece of gum",
        sticky=True,
        tags={"gum"},
    ))
    world.add(Entity(
        id="edge",
        type="edge",
        label=edge_cfg.label,
        phrase=edge_cfg.phrase,
        edge=True,
        movable=False,
        attrs={"zones": set(edge_cfg.zones), "danger": edge_cfg.danger},
        tags=set(edge_cfg.tags),
    ))
    world.add(Entity(
        id="snag",
        type="snag_item",
        label=snag_cfg.label,
        phrase=snag_cfg.phrase,
        attrs={"zone": snag_cfg.zone},
        tags=set(snag_cfg.tags),
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)

    opening(world, a, b, parent, matinee)
    gum_gift(world, a)

    world.para()
    warning(world, b, a, parent, edge_cfg)
    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, parent)
        world.para()
        safe_end(world, matinee, a, b)
        severity = 0
        contained = True
    else:
        defy(world, a, b, edge_cfg)
        world.para()
        show_turn(world, matinee, snag_cfg)
        alarm(world, b, a, snag_cfg, helper)
        severity = snag_severity(edge_cfg, delay)
        world.get("edge").meters["severity"] = float(severity)
        contained = is_contained(response, edge_cfg, delay)
        world.para()
        if contained:
            rescue(world, helper, response, a, snag_cfg, edge_cfg)
            lesson(world, helper, a, b)
            world.para()
            safe_end(world, matinee, a, b)
        else:
            rescue_fail(world, helper, response, a, edge_cfg)
            sore_but_safe(world, helper, a, b, matinee)

    outcome = "averted" if averted else ("contained" if contained else "bumped")
    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        helper=helper,
        matinee=matinee,
        edge_cfg=edge_cfg,
        snag_cfg=snag_cfg,
        response=response,
        delay=delay,
        severity=severity,
        outcome=outcome,
        relation=relation,
        ignited=False,
        promised=a.memes["lesson"] >= THRESHOLD,
    )
    return world


MATINEES = {
    "moon_mice": Matinee(
        id="moon_mice",
        title="Moon Mice Matinee",
        opening="Their shoes made little tap-tap tunes on the red carpet.",
        stage_image="three paper mice rode a silver spoon across a painted moon",
        cheer="oh, look",
        tags={"matinee", "moon"},
    ),
    "duck_band": Matinee(
        id="duck_band",
        title="Duck Band Matinee",
        opening="A gold horn painted on the curtain seemed almost ready to sing.",
        stage_image="four yellow ducks in tiny coats bobbed beside a blue drum",
        cheer="hark, the ducks",
        tags={"matinee", "music"},
    ),
    "button_prince": Matinee(
        id="button_prince",
        title="Button Prince Matinee",
        opening="The velvet seats looked deep as plum jam and twice as grand.",
        stage_image="a button prince bowed to a cardboard star on a string",
        cheer="see him bow",
        tags={"matinee", "stage"},
    ),
}

EDGES = {
    "seat_rim": EdgeConfig(
        id="seat_rim",
        label="seat rim",
        phrase="the seat's front edge",
        danger=1,
        zones={"sleeve", "ticket"},
        rhyme="There it sat on the edge so trim, a naughty pink moon on the velvet rim.",
        tags={"seat", "edge"},
    ),
    "stair_lip": EdgeConfig(
        id="stair_lip",
        label="stair lip",
        phrase="the stair edge",
        danger=2,
        zones={"shoe", "ticket"},
        rhyme="There it sat by the edge of the stair, a sticky little snare in the theater air.",
        tags={"stairs", "edge"},
    ),
    "balcony_rail": EdgeConfig(
        id="balcony_rail",
        label="balcony rail",
        phrase="the balcony edge",
        danger=3,
        zones={"sleeve", "ticket"},
        rhyme="There it sat on the balcony edge, small as a berry and sly as a hedge.",
        tags={"balcony", "edge"},
    ),
    "curtain_hem": EdgeConfig(
        id="curtain_hem",
        label="curtain hem",
        phrase="the curtain hem",
        danger=1,
        zones=set(),
        safe=False,
        rhyme="No one ought to gum the curtain hem, but nothing there would snag the child back.",
        tags={"curtain"},
    ),
}

SNAG_ITEMS = {
    "ticket_stub": SnagItem(
        id="ticket_stub",
        label="ticket stub",
        phrase="the ticket stub",
        zone="ticket",
        tags={"ticket"},
    ),
    "cardigan_cuff": SnagItem(
        id="cardigan_cuff",
        label="cardigan cuff",
        phrase="the soft cardigan cuff",
        zone="sleeve",
        tags={"sleeve"},
    ),
    "shoe_ribbon": SnagItem(
        id="shoe_ribbon",
        label="shoe ribbon",
        phrase="the loose shoe ribbon",
        zone="shoe",
        tags={"shoe"},
    ),
}

RESPONSES = {
    "steady_peel": Response(
        id="steady_peel",
        sense=3,
        power=3,
        text="reached with a paper napkin, steadied one small shoulder, and peeled the gum away without a jerk",
        fail="reached with a napkin and tried to peel the gum away gently",
        qa_text="steadied the child and peeled the gum away with a paper napkin",
        tags={"napkin", "help"},
    ),
    "guide_back": Response(
        id="guide_back",
        sense=2,
        power=2,
        text="took both small hands, guided the child one step back, and lifted the sticky bit off with the ticket paper",
        fail="took both small hands and tried to guide the child back",
        qa_text="guided the child back from the edge and lifted the gum off with paper",
        tags={"help", "back"},
    ),
    "yank_hard": Response(
        id="yank_hard",
        sense=1,
        power=1,
        text="gave a hard pull and tore the gum loose",
        fail="gave a hard pull at the stuck thing",
        qa_text="yanked hard at the stuck thing",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Mina", "Lulu", "Nell", "Dora", "Ivy", "Poppy", "Tessa", "Ruth"]
BOY_NAMES = ["Pip", "Ollie", "Ned", "Toby", "Kit", "Milo", "Benji", "Jem"]
TRAITS = ["careful", "steady", "watchful", "sensible", "bright", "curious"]


@dataclass
class StoryParams:
    matinee: str
    edge: str
    snag: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    helper: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 5
    relation: str = "siblings"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mid in MATINEES:
        for eid, edge in EDGES.items():
            for sid, snag in SNAG_ITEMS.items():
                if hazard_at_risk(edge, snag):
                    combos.append((mid, eid, sid))
    return combos


KNOWLEDGE = {
    "gum": [
        (
            "Why should gum stay in paper or go in the bin?",
            "Chewed gum is sticky, so it can cling to seats, rails, shoes, and sleeves. Keeping it wrapped or throwing it away stops messy snags."
        )
    ],
    "matinee": [
        (
            "What is a matinee?",
            "A matinee is a show in the daytime, often in the afternoon. Families go to watch it while the sun is still up."
        )
    ],
    "edge": [
        (
            "Why should children stay back from an edge in the dark?",
            "An edge is where something ends, like a stair lip or balcony rail. In dim light it is easier to trip or lean too far, so staying back is safer."
        )
    ],
    "ticket": [
        (
            "What is a ticket stub?",
            "A ticket stub is the small piece of a ticket you keep after going into a show. It proves you came in and often becomes a little keepsake."
        )
    ],
    "shoe": [
        (
            "Why can a loose shoe ribbon be a problem?",
            "A loose ribbon can catch on things or tangle around your foot. That can make you stumble when you walk."
        )
    ],
    "sleeve": [
        (
            "Why can a sleeve catch by accident?",
            "A sleeve brushes along the side of your body when you move. If something sticky is on an edge, the cloth can cling before you notice."
        )
    ],
    "help": [
        (
            "What should you do if something gets stuck near an edge?",
            "Stop moving and call a grown-up right away. Staying still gives the helper time to free it safely."
        )
    ],
}
KNOWLEDGE_ORDER = ["gum", "matinee", "edge", "ticket", "shoe", "sleeve", "help"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    matinee = f["matinee"]
    edge = f["edge_cfg"]
    snag = f["snag_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the words '
        f'"gum", "matinee", and "edge", and uses foreshadowing, dialogue, and suspense.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle matinee story where {a.label} is tempted to hide gum on {edge.phrase}, "
            f"but {b.label}, an older sibling, warns what might catch there and stops the trouble before it starts.",
            f"Write a rhyming story with dialogue where a child listens in time, keeps the gum in paper, "
            f"and enjoys the matinee safely.",
        ]
    if outcome == "bumped":
        return [
            base,
            f"Tell a suspenseful but child-safe story where {snag.label} gets stuck in gum at {edge.phrase}, "
            f"a child lurches toward the edge, and a helper is almost too late.",
            f"Write a nursery-rhyme cautionary tale where a sticky mistake at a matinee leads to a scrape and a strong lesson.",
        ]
    return [
        base,
        f"Tell a rhyming matinee story where {a.label} hides gum on {edge.phrase}, {snag.label} gets stuck there in the dark, "
        f"and a calm helper rescues the child safely.",
        f"Write a gentle suspense story with foreshadowing and dialogue, ending with the gum wrapped up properly and the matinee finishing well.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    helper = f["helper"]
    matinee = f["matinee"]
    edge = f["edge_cfg"]
    snag = f["snag_cfg"]
    response = f["response"]
    relation = f["relation"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b, relation)}, {a.label} and {b.label}, at a daytime matinee. "
            f"A calm {helper.label_word} helps when the sticky trouble begins."
        ),
        (
            "What made the trouble start?",
            f"The trouble started when {a.label} pressed gum onto {edge.phrase} to save it for later. "
            f"That left a sticky trap waiting in the dark."
        ),
        (
            f"What warning did {b.label} give?",
            f"{b.label} said not to put gum on {edge.phrase} because things can catch there at the edge when the room goes dim. "
            f"The warning foreshadowed the exact danger that came later."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"How was the problem solved before it happened?",
                f"{a.label} listened to {b.label} and folded the gum back into paper instead of hiding it. "
                f"Because the edge stayed clean, nothing snagged there during the matinee."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended peacefully, with the children watching {matinee.title} and keeping hands and feet away from the edge. "
                f"The ending proves they changed by choosing care before trouble."
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                f"What got stuck, and why was that scary?",
                f"{snag.phrase.capitalize()} got stuck in the gum, which made {a.label} pull and lean. "
                f"That was scary because the snag happened right by the edge in a dim theater."
            )
        )
        qa.append(
            (
                f"How did the {helper.label_word} help?",
                f"The {helper.label_word} {response.qa_text}. "
                f"The quick, steady help freed the stuck thing and stopped the danger before {a.label} fell."
            )
        )
        qa.append(
            (
                "What did the children learn?",
                "They learned that a little gum can make a big problem in the dark, so gum should stay wrapped or be thrown away properly. "
                "After that, they kept the edges clean and watched the show safely."
            )
        )
    else:
        qa.append(
            (
                f"What happened when the stuck thing tugged back?",
                f"When {snag.phrase} tugged back, {a.label} lurched and bumped down with a scrape. "
                f"The danger came from pulling against the sticky gum too close to the edge."
            )
        )
        qa.append(
            (
                "Did everyone stay safe?",
                f"Yes. {a.label} was sore and frightened, but safe, and the grown-up checked the scrape right away. "
                f"They missed the rest of the matinee, which made the lesson feel very real."
            )
        )
        qa.append(
            (
                "What changed at the end?",
                "After the scare, gum always stayed wrapped and edges stayed bare. "
                "The final image shows the new rule living in their everyday choices."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"gum", "matinee", "edge", "help"}
    tags |= set(world.get("snag").tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        matinee="moon_mice",
        edge="seat_rim",
        snag="ticket_stub",
        response="steady_peel",
        instigator="Mina",
        instigator_gender="girl",
        cautioner="Pip",
        cautioner_gender="boy",
        parent="mother",
        helper="usher",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=5,
        relation="siblings",
    ),
    StoryParams(
        matinee="duck_band",
        edge="stair_lip",
        snag="shoe_ribbon",
        response="guide_back",
        instigator="Ollie",
        instigator_gender="boy",
        cautioner="Nell",
        cautioner_gender="girl",
        parent="father",
        helper="usher",
        trait="watchful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="friends",
    ),
    StoryParams(
        matinee="button_prince",
        edge="balcony_rail",
        snag="cardigan_cuff",
        response="guide_back",
        instigator="Lulu",
        instigator_gender="girl",
        cautioner="Milo",
        cautioner_gender="boy",
        parent="mother",
        helper="usher",
        trait="bright",
        delay=2,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
    ),
    StoryParams(
        matinee="moon_mice",
        edge="balcony_rail",
        snag="ticket_stub",
        response="steady_peel",
        instigator="Kit",
        instigator_gender="boy",
        cautioner="Dora",
        cautioner_gender="girl",
        parent="father",
        helper="usher",
        trait="steady",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
    ),
]


def explain_rejection(edge: EdgeConfig, snag: SnagItem) -> str:
    if not edge.safe:
        return (
            f"(No story: {edge.phrase} is part of the theater, but this world's problem is a child snagging something at an edge. "
            f"Nothing in this model catches there, so there is no honest suspense beat.)"
        )
    return (
        f"(No story: {snag.phrase} would not brush {edge.phrase} in this world model, so the gum would not cause a believable snag. "
        f"Pick a matching pair like ticket stub + balcony edge or shoe ribbon + stair edge.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). "
        f"Try a steadier helper action instead, such as: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    response = RESPONSES[params.response]
    edge = EDGES[params.edge]
    return "contained" if is_contained(response, edge, params.delay) else "bumped"


ASP_RULES = r"""
hazard(E, S) :- safe_edge(E), touches(E, Z), snag_zone(S, Z).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(M, E, S) :- matinee(M), edge(E), snag(S), hazard(E, S).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_sibling :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(3) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sibling, authority(A), bravery_init(BR), A > BR.

severity(Dg + Dl) :- chosen_edge(E), danger(E, Dg), delay(Dl).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(bumped) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mid in MATINEES:
        lines.append(asp.fact("matinee", mid))
    for eid, edge in EDGES.items():
        lines.append(asp.fact("edge", eid))
        if edge.safe:
            lines.append(asp.fact("safe_edge", eid))
        lines.append(asp.fact("danger", eid, edge.danger))
        for zone in sorted(edge.zones):
            lines.append(asp.fact("touches", eid, zone))
    for sid, snag in SNAG_ITEMS.items():
        lines.append(asp.fact("snag", sid))
        lines.append(asp.fact("snag_zone", sid, snag.zone))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_edge", params.edge),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: gum, matinee, edge. Nursery-rhyme suspense with a sticky lesson."
    )
    ap.add_argument("--matinee", choices=MATINEES)
    ap.add_argument("--edge", choices=EDGES)
    ap.add_argument("--snag", choices=SNAG_ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--helper", choices=["usher", "usheress"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the child tugs before help arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.edge and args.snag:
        edge = EDGES[args.edge]
        snag = SNAG_ITEMS[args.snag]
        if not hazard_at_risk(edge, snag):
            raise StoryError(explain_rejection(edge, snag))
    if args.edge and not EDGES[args.edge].safe:
        snag = SNAG_ITEMS[args.snag] if args.snag else next(iter(SNAG_ITEMS.values()))
        raise StoryError(explain_rejection(EDGES[args.edge], snag))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.matinee is None or combo[0] == args.matinee)
        and (args.edge is None or combo[1] == args.edge)
        and (args.snag is None or combo[2] == args.snag)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    matinee, edge, snag = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    helper = args.helper or rng.choice(["usher", "usheress"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)

    return StoryParams(
        matinee=matinee,
        edge=edge,
        snag=snag,
        response=response,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        helper=helper,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.matinee not in MATINEES:
        raise StoryError(f"(Unknown matinee: {params.matinee})")
    if params.edge not in EDGES:
        raise StoryError(f"(Unknown edge: {params.edge})")
    if params.snag not in SNAG_ITEMS:
        raise StoryError(f"(Unknown snag item: {params.snag})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not hazard_at_risk(EDGES[params.edge], SNAG_ITEMS[params.snag]):
        raise StoryError(explain_rejection(EDGES[params.edge], SNAG_ITEMS[params.snag]))

    world = tell(
        matinee=MATINEES[params.matinee],
        edge_cfg=EDGES[params.edge],
        snag_cfg=SNAG_ITEMS[params.snag],
        response=RESPONSES[params.response],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        parent_type=params.parent,
        helper_type=params.helper,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
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

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(80):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke-tested normal story generation.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (matinee, edge, snag) combos:\n")
        for matinee, edge, snag in combos:
            print(f"  {matinee:14} {edge:13} {snag}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.edge} + {p.snag} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
