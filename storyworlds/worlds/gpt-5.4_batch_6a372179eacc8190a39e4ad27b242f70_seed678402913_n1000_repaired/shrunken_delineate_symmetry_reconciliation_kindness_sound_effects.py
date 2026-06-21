#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/shrunken_delineate_symmetry_reconciliation_kindness_sound_effects.py
================================================================================================

A standalone story world about two young explorers following a faded treasure
note through a small adventure path. The note has gone shrunken after damp
weather, so the children must delineate their route with sensible markers and
use a clue about symmetry to find the right place.

The tension is social as well as practical: one child rushes, hurts the other
child's feelings, and spoils the neat marker pattern. A kind repair method can
rebuild trust and restore the route; a weak method may come too late for the
treasure hunt, though the children can still reconcile.

Run it
------
    python storyworlds/worlds/gpt-5.4/shrunken_delineate_symmetry_reconciliation_kindness_sound_effects.py
    python storyworlds/worlds/gpt-5.4/shrunken_delineate_symmetry_reconciliation_kindness_sound_effects.py --place stone_garden --marker chalk
    python storyworlds/worlds/gpt-5.4/shrunken_delineate_symmetry_reconciliation_kindness_sound_effects.py --place hedge_path --marker shells
    python storyworlds/worlds/gpt-5.4/shrunken_delineate_symmetry_reconciliation_kindness_sound_effects.py --all
    python storyworlds/worlds/gpt-5.4/shrunken_delineate_symmetry_reconciliation_kindness_sound_effects.py --qa --json
    python storyworlds/worlds/gpt-5.4/shrunken_delineate_symmetry_reconciliation_kindness_sound_effects.py --verify
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
SENSE_MIN = 2


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
    phrase: str
    surface: str
    landmark: str
    symmetry_line: str
    treasure: str
    complexity: int
    opening: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Marker:
    id: str
    label: str
    phrase: str
    works_on: set[str]
    make_line: str
    repair_line: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class RepairMethod:
    id: str
    label: str
    sense: int
    power: int
    kind: bool
    text: str
    later_text: str
    qa_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "partner"}]

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


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    note = world.get("note")
    path = world.get("path")
    if note.meters["shrunk"] >= THRESHOLD and path.meters["clear"] < THRESHOLD:
        sig = ("confusion",)
        if sig not in world.fired:
            world.fired.add(sig)
            path.meters["confusion"] += 1
            for kid in world.kids():
                kid.memes["worry"] += 1
            out.append("__confusion__")
    return out


def _r_hurt(world: World) -> list[str]:
    out: list[str] = []
    leader = world.get("leader")
    partner = world.get("partner")
    if leader.memes["snapped"] >= THRESHOLD and partner.memes["hurt"] < THRESHOLD:
        sig = ("hurt",)
        if sig not in world.fired:
            world.fired.add(sig)
            partner.memes["hurt"] += 1
            partner.memes["trust"] -= 1
            out.append("__hurt__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    leader = world.get("leader")
    partner = world.get("partner")
    if leader.memes["kindness"] >= THRESHOLD and leader.memes["apology"] >= THRESHOLD:
        sig = ("reconcile",)
        if sig not in world.fired:
            world.fired.add(sig)
            leader.memes["peace"] += 1
            partner.memes["peace"] += 1
            partner.memes["hurt"] = 0.0
            partner.memes["trust"] += 2
            out.append("__reconcile__")
    return out


def _r_progress(world: World) -> list[str]:
    out: list[str] = []
    path = world.get("path")
    if path.meters["clear"] >= THRESHOLD and path.meters["symmetry"] >= THRESHOLD:
        sig = ("progress",)
        if sig not in world.fired:
            world.fired.add(sig)
            path.meters["progress"] += 1
            out.append("__progress__")
    return out


CAUSAL_RULES = [
    Rule(name="confusion", tag="social", apply=_r_confusion),
    Rule(name="hurt", tag="social", apply=_r_hurt),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
    Rule(name="progress", tag="physical", apply=_r_progress),
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


def marker_fits(place: Place, marker: Marker) -> bool:
    return place.surface in marker.works_on


def sensible_repairs() -> list[RepairMethod]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN and r.kind]


def confusion_severity(place: Place, delay: int) -> int:
    return place.complexity + delay


def can_finish(place: Place, repair: RepairMethod, delay: int) -> bool:
    return repair.power >= confusion_severity(place, delay)


def explain_rejection(place: Place, marker: Marker) -> str:
    return (
        f"(No story: {marker.label} cannot neatly delineate a trail in {place.label}. "
        f"That place needs a marker that works on {place.surface}.)"
    )


def explain_repair(rid: str) -> str:
    repair = REPAIRS[rid]
    return (
        f"(Refusing repair '{rid}': it is not kind enough for a reconciliation story "
        f"(sense={repair.sense}, kind={repair.kind}). Try one of: "
        f"{', '.join(sorted(r.id for r in sensible_repairs()))}.)"
    )


def predict_route(world: World) -> dict:
    sim = world.copy()
    path = sim.get("path")
    path.meters["clear"] = 0.0
    path.meters["symmetry"] = 0.0
    propagate(sim, narrate=False)
    return {
        "confused": path.meters["confusion"] >= THRESHOLD,
        "worry": sum(k.memes["worry"] for k in sim.kids()),
    }


def introduce(world: World, leader: Entity, partner: Entity, place: Place) -> None:
    for kid in (leader, partner):
        kid.memes["wonder"] += 1
    world.say(
        f"On a bright afternoon, {leader.id} and {partner.id} slipped into {place.phrase} "
        f"for an adventure. {place.opening}"
    )
    world.say(
        f"In {leader.id}'s pocket was a tiny treasure note that had gone shrunken in the damp grass, "
        f"so some of its turns looked crinkly and small."
    )
    world.say(
        f'"Then we will have to delineate our trail as we go," said {partner.id}, '
        f'tapping the note with one careful finger.'
    )


def clue(world: World, partner: Entity, place: Place) -> None:
    world.say(
        f'The note still showed one useful clue: "{place.symmetry_line}" '
        f'It pointed toward {place.landmark}.'
    )
    world.say(
        f'{partner.id} liked that idea because symmetry made left and right easier to remember.'
    )


def choose_marker(world: World, leader: Entity, marker: Marker) -> None:
    path = world.get("path")
    path.meters["clear"] += 1
    world.say(
        f'{leader.id} lifted {marker.phrase}. "Perfect," {leader.pronoun()} said. '
        f'"We can mark the way."'
    )
    world.say(marker.make_line)


def rush_and_spoil(world: World, leader: Entity, partner: Entity, marker: Marker) -> None:
    path = world.get("path")
    leader.memes["snapped"] += 1
    path.meters["clear"] = 0.0
    path.meters["symmetry"] = 0.0
    path.meters["spoiled"] += 1
    propagate(world, narrate=False)
    bang = leader.attrs.get("sound", "clack")
    rustle = partner.attrs.get("sound", "swish")
    world.say(
        f'But when the trail bent around a corner, {partner.id} asked for two neat marks to match. '
        f'"If the signs keep their symmetry, we will know which turn belongs with which," '
        f'{partner.pronoun()} said.'
    )
    world.say(
        f'{leader.id} was too excited to listen. "{leader.id} can do it faster," '
        f'{leader.pronoun()} blurted, and then came {bang}! {rustle}! One marker skidded aside, '
        f'and the tidy pattern broke.'
    )
    world.say(
        f'{partner.id} stopped and stared at the crooked trail. The shrunken note was no help at all now.'
    )


def worry(world: World, leader: Entity, partner: Entity, place: Place) -> None:
    pred = predict_route(world)
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'For a moment the whole adventure felt smaller. Without clear marks, '
        f'{place.label} seemed twisty and strange, and both children went quiet.'
    )
    world.say(
        f'{partner.id} hugged the note to {partner.pronoun("possessive")} chest, and '
        f'{leader.id} finally heard how lonely the silence sounded.'
    )


def repair_trail(world: World, leader: Entity, partner: Entity, marker: Marker,
                 repair: RepairMethod) -> None:
    path = world.get("path")
    leader.memes["apology"] += 1
    leader.memes["kindness"] += 1 if repair.kind else 0.0
    path.meters["clear"] += 1
    path.meters["symmetry"] += 1
    propagate(world, narrate=False)
    world.say(repair.text.format(leader=leader.id, partner=partner.id, marker=marker.label))
    world.say(marker.repair_line)
    world.say(
        f'Soon the trail looked balanced again, and {partner.id} gave a small nod. '
        f'The adventure sounded different too: soft tap-tap, careful swish, happy pat-pat.'
    )


def treasure_found(world: World, leader: Entity, partner: Entity, place: Place,
                   repair: RepairMethod) -> None:
    for kid in (leader, partner):
        kid.memes["joy"] += 1
    world.say(
        f'Together they followed the paired marks to {place.landmark}. There, right where the pattern '
        f'came together, they found {place.treasure}.'
    )
    world.say(
        f'{repair.later_text} The little prize mattered, but not as much as the way they reached it: '
        f'side by side at last.'
    )


def too_late(world: World, leader: Entity, partner: Entity, place: Place,
             repair: RepairMethod) -> None:
    for kid in (leader, partner):
        kid.memes["calm"] += 1
    world.say(
        f'They repaired the trail, but the sun had already slipped low. Shadows stretched across '
        f'{place.label}, and the treasure place would have to wait for another day.'
    )
    world.say(
        f'{repair.later_text} {leader.id} and {partner.id} walked home with the fixed note between them, '
        f'no longer cross, already planning a kinder adventure for tomorrow.'
    )


def tell(place: Place, marker: Marker, repair: RepairMethod,
         leader_name: str = "Nora", leader_gender: str = "girl",
         partner_name: str = "Eli", partner_gender: str = "boy",
         relation: str = "friends", delay: int = 0) -> World:
    world = World(place)
    leader = world.add(Entity(
        id="leader",
        kind="character",
        type=leader_gender,
        label=leader_name,
        phrase=leader_name,
        role="leader",
        attrs={"name": leader_name, "relation": relation, "sound": random.choice(["thump", "clack", "skitter"])},
    ))
    partner = world.add(Entity(
        id="partner",
        kind="character",
        type=partner_gender,
        label=partner_name,
        phrase=partner_name,
        role="partner",
        attrs={"name": partner_name, "relation": relation, "sound": random.choice(["rustle", "swish", "patter"])},
    ))
    note = world.add(Entity(id="note", type="note", label="treasure note"))
    path = world.add(Entity(id="path", type="trail", label="trail"))
    note.meters["shrunk"] += 1
    path.meters["clear"] = 0.0
    path.meters["symmetry"] = 0.0
    partner.memes["trust"] += 1

    world.facts["leader_name"] = leader_name
    world.facts["partner_name"] = partner_name

    introduce(world, leader, partner, place)
    clue(world, partner, place)

    world.para()
    choose_marker(world, leader, marker)
    rush_and_spoil(world, leader, partner, marker)
    worry(world, leader, partner, place)

    world.para()
    repair_trail(world, leader, partner, marker, repair)

    path.meters["severity"] = float(confusion_severity(place, delay))
    success = can_finish(place, repair, delay)
    world.para()
    if success:
        treasure_found(world, leader, partner, place, repair)
        outcome = "found"
    else:
        too_late(world, leader, partner, place, repair)
        outcome = "late"

    world.facts.update(
        place=place,
        marker=marker,
        repair=repair,
        leader=leader,
        partner=partner,
        note=note,
        path=path,
        outcome=outcome,
        delay=delay,
        reconciled=partner.memes["peace"] >= THRESHOLD,
        success=success,
        relation=relation,
    )
    return world


KNOWLEDGE = {
    "symmetry": [
        (
            "What is symmetry?",
            "Symmetry means two sides match in shape or pattern, like wings or two halves of a heart. "
            "It can help people notice order and remember where things belong.",
        )
    ],
    "chalk": [
        (
            "What is chalk good for?",
            "Chalk is good for making marks on stone or pavement. It leaves a line you can see, but rain can wash it away.",
        )
    ],
    "ribbon": [
        (
            "What can ribbon be used for on a trail?",
            "Ribbon can be tied to branches or posts to show the way. Bright ribbon is easy to spot when you look back.",
        )
    ],
    "shells": [
        (
            "How can shells mark a path?",
            "You can place shells in a little row or pattern on sand. They help show direction as long as the wind does not scatter them.",
        )
    ],
    "apology": [
        (
            "Why does an apology help after an argument?",
            "An apology shows that someone understands the hurt they caused. It can open the door for trust and friendship to come back.",
        )
    ],
    "kindness": [
        (
            "What does kindness sound like?",
            "Kindness sounds like gentle words, patient listening, and a voice that makes room for someone else. It can calm a problem before it grows bigger.",
        )
    ],
    "map": [
        (
            "What does a map do?",
            "A map helps people remember where to go. It turns places and turns into a pattern you can follow.",
        )
    ],
}
KNOWLEDGE_ORDER = ["map", "symmetry", "chalk", "ribbon", "shells", "apology", "kindness"]


PLACES = {
    "stone_garden": Place(
        id="stone_garden",
        label="the stone garden",
        phrase="the stone garden behind the old greenhouse",
        surface="stone",
        landmark="a round gate carved with leaves",
        symmetry_line="Find the place where both sides match.",
        treasure="a tin box with polished marbles inside",
        complexity=1,
        opening="Smooth paths curled between mossy stepping stones, and every turn felt like part of a secret map.",
        tags={"map", "symmetry", "adventure"},
    ),
    "hedge_path": Place(
        id="hedge_path",
        label="the hedge path",
        phrase="the hedge path by the apple trees",
        surface="hedge",
        landmark="an arch where two climbing roses met in the middle",
        symmetry_line="Look for the arch with the same shape on both sides.",
        treasure="a tiny bell tucked under a flowerpot",
        complexity=2,
        opening="Green walls rose shoulder-high around them, and each bend whispered of hidden things.",
        tags={"map", "symmetry", "adventure"},
    ),
    "sandy_courtyard": Place(
        id="sandy_courtyard",
        label="the sandy courtyard",
        phrase="the sandy courtyard near the old shed",
        surface="sand",
        landmark="a pair of brick circles with a shell at the center",
        symmetry_line="Follow the matching rings until the middle lines up.",
        treasure="a cloth pouch with bright glass beads",
        complexity=2,
        opening="Warm sand lay in loops and ridges, as if a lost fort had sunk there long ago.",
        tags={"map", "symmetry", "adventure"},
    ),
}

MARKERS = {
    "chalk": Marker(
        id="chalk",
        label="chalk",
        phrase="a stub of blue chalk",
        works_on={"stone"},
        make_line="With a quick scrape-scrape, a bright line bloomed across the edge of a stepping stone.",
        repair_line="This time they drew twin marks together, one on each side, neat enough to smile at.",
        tags={"chalk", "map"},
    ),
    "ribbon": Marker(
        id="ribbon",
        label="ribbon",
        phrase="a roll of red ribbon",
        works_on={"hedge"},
        make_line='Snip, flutter, knot-knot: the ribbon made little flags that winked between the leaves.',
        repair_line="This time they tied matching bows at eye level, so each turn answered the one before it.",
        tags={"ribbon", "map"},
    ),
    "shells": Marker(
        id="shells",
        label="shells",
        phrase="a pocketful of striped shells",
        works_on={"sand"},
        make_line="Plink-plink, they set the shells in a pale row that curved through the sand.",
        repair_line="This time they set the shells in mirrored pairs, each little curve balancing the next.",
        plural=True,
        tags={"shells", "map"},
    ),
}

REPAIRS = {
    "apology_redraw": RepairMethod(
        id="apology_redraw",
        label="apology and redraw",
        sense=3,
        power=4,
        kind=True,
        text='"I was rushing, and I hurt your feelings," said {leader}. "Will you help me fix the marks?" '
             '{partner} looked up, heard the apology, and stepped closer.',
        later_text="When they looked at each other again, the sharp part of the quarrel was already gone.",
        qa_text="apologized, listened, and redrew the path together",
        tags={"apology", "kindness"},
    ),
    "kind_counting": RepairMethod(
        id="kind_counting",
        label="kind counting game",
        sense=3,
        power=3,
        kind=True,
        text='{leader} took a slow breath. "Let us count the marks in pairs," {leader} said gently. '
             '"I want to hear your idea this time." {partner} smiled a little and joined in.',
        later_text="They did not race anymore; they counted and listened and moved as one team.",
        qa_text="slowed down, counted the paired marks, and listened kindly",
        tags={"kindness", "symmetry"},
    ),
    "hold_hands": RepairMethod(
        id="hold_hands",
        label="hold hands and try again",
        sense=2,
        power=2,
        kind=True,
        text='{leader} reached for {partner}\'s hand. "I do not want to stomp ahead alone," {leader} admitted. '
             '"Let us stay together and make one good line."',
        later_text="Their steps matched better than their first plan had.",
        qa_text="stayed together and remade the trail side by side",
        tags={"kindness"},
    ),
    "bossy_pointing": RepairMethod(
        id="bossy_pointing",
        label="bossy pointing",
        sense=1,
        power=1,
        kind=False,
        text='{leader} pointed sharply and told {partner} where to stand.',
        later_text="The words landed hard instead of helping.",
        qa_text="pointed and ordered instead of making peace",
        tags=set(),
    ),
}


GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Anna", "Ella", "Rose"]
BOY_NAMES = ["Eli", "Ben", "Max", "Sam", "Leo", "Finn", "Theo", "Jack"]


@dataclass
class StoryParams:
    place: str
    marker: str
    repair: str
    leader_name: str
    leader_gender: str
    partner_name: str
    partner_gender: str
    relation: str
    delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for marker_id, marker in MARKERS.items():
            if marker_fits(place, marker):
                combos.append((place_id, marker_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    if not marker_fits(PLACES[params.place], MARKERS[params.marker]):
        raise StoryError(explain_rejection(PLACES[params.place], MARKERS[params.marker]))
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    repair = REPAIRS[params.repair]
    if repair.sense < SENSE_MIN or not repair.kind:
        raise StoryError(explain_repair(params.repair))
    return "found" if can_finish(PLACES[params.place], repair, params.delay) else "late"


def pair_noun(leader: Entity, partner: Entity, relation: str) -> str:
    if relation == "siblings":
        if leader.type == "girl" and partner.type == "girl":
            return "two sisters"
        if leader.type == "boy" and partner.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def display_name(ent: Entity) -> str:
    return ent.label or ent.attrs.get("name", ent.id)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place, marker, repair = f["place"], f["marker"], f["repair"]
    leader = f["leader"]
    partner = f["partner"]
    if f["outcome"] == "found":
        return [
            'Write a short adventure story for a 3-to-5-year-old that includes the words "shrunken", '
            '"delineate", and "symmetry".',
            f"Tell an adventure where {display_name(leader)} and {display_name(partner)} follow a shrunken treasure note, "
            f"spoil their marker pattern, then reconcile through kindness and find the treasure.",
            f"Write a gentle reconciliation story with sound effects where children use {marker.label} to delineate a trail "
            f"and a clue about symmetry helps them succeed.",
        ]
    return [
        'Write a short adventure story for a 3-to-5-year-old that includes the words "shrunken", '
        '"delineate", and "symmetry".',
        f"Tell an adventure where {display_name(leader)} and {display_name(partner)} repair a quarrel with kindness after "
        f"spoiling their trail marks in {place.label}.",
        f"Write a reconciliation story with sound effects where children use {marker.label} to delineate a path, "
        f"but dusk comes before the treasure is found.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    place = f["place"]
    marker = f["marker"]
    repair = f["repair"]
    relation = f["relation"]
    leader_name = display_name(leader)
    partner_name = display_name(partner)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(leader, partner, relation)}, {leader_name} and {partner_name}, on a small adventure in {place.label}. "
            f"They are trying to follow a treasure note together.",
        ),
        (
            "Why was the note hard to use?",
            "The treasure note had gone shrunken in the damp grass, so the turns were hard to read. "
            "That is why the children needed another way to keep track of the route.",
        ),
        (
            f"Why did {partner_name} care about symmetry?",
            f"{partner_name} thought matching marks would help the children remember left and right. "
            f"The clue on the note also pointed them toward a place where both sides matched.",
        ),
        (
            f"What went wrong on the trail?",
            f"{leader_name} rushed and snapped instead of listening, and the marker pattern got spoiled. "
            f"Once the neat trail broke, the shrunken note could not guide them well enough by itself.",
        ),
        (
            f"How did the children make peace?",
            f"{leader_name} {repair.qa_text}. "
            f"That kindness helped {partner_name} feel heard again, so the two children could work as a team.",
        ),
    ]
    if f["outcome"] == "found":
        qa.append(
            (
                "How did the story end?",
                f"They followed the repaired, balanced trail to {place.landmark} and found {place.treasure}. "
                f"The ending shows both success in the adventure and reconciliation between the children.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"They fixed the quarrel and the trail, but sunset came before they reached {place.landmark}. "
                f"Even without the treasure that day, they ended the story kinder and closer than before.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["place"].tags) | set(f["marker"].tags) | set(f["repair"].tags)
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="stone_garden",
        marker="chalk",
        repair="apology_redraw",
        leader_name="Nora",
        leader_gender="girl",
        partner_name="Eli",
        partner_gender="boy",
        relation="friends",
        delay=0,
    ),
    StoryParams(
        place="hedge_path",
        marker="ribbon",
        repair="kind_counting",
        leader_name="Max",
        leader_gender="boy",
        partner_name="Lily",
        partner_gender="girl",
        relation="siblings",
        delay=1,
    ),
    StoryParams(
        place="sandy_courtyard",
        marker="shells",
        repair="hold_hands",
        leader_name="Anna",
        leader_gender="girl",
        partner_name="Ben",
        partner_gender="boy",
        relation="friends",
        delay=1,
    ),
    StoryParams(
        place="hedge_path",
        marker="ribbon",
        repair="hold_hands",
        leader_name="Theo",
        leader_gender="boy",
        partner_name="Rose",
        partner_gender="girl",
        relation="friends",
        delay=2,
    ),
]


ASP_RULES = r"""
fits(P, M) :- place(P), marker(M), surface(P, S), works_on(M, S).
sensible(R) :- repair(R), sense(R, S), sense_min(Min), S >= Min, kind(R).

severity(P, D, V) :- complexity(P, C), delay(D), V = C + D.
outcome(found) :- chosen_place(P), chosen_repair(R), sensible(R), chosen_delay(D),
                  power(R, Pw), severity(P, D, V), Pw >= V.
outcome(late) :- chosen_place(P), chosen_repair(R), sensible(R), chosen_delay(D),
                 power(R, Pw), severity(P, D, V), Pw < V.
valid(P, M) :- fits(P, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("surface", pid, place.surface))
        lines.append(asp.fact("complexity", pid, place.complexity))
    for mid, marker in MARKERS.items():
        lines.append(asp.fact("marker", mid))
        for surface in sorted(marker.works_on):
            lines.append(asp.fact("works_on", mid, surface))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense", rid, repair.sense))
        lines.append(asp.fact("power", rid, repair.power))
        if repair.kind:
            lines.append(asp.fact("kind", rid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_repairs() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_repair", params.repair),
            asp.fact("chosen_delay", params.delay),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_repairs = set(asp_sensible_repairs())
    p_repairs = {r.id for r in sensible_repairs()}
    if c_repairs == p_repairs:
        print(f"OK: sensible repairs match ({sorted(c_repairs)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: clingo={sorted(c_repairs)} python={sorted(p_repairs)}")

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            continue

    bad = 0
    for params in cases:
        try:
            py = outcome_of(params)
        except StoryError:
            continue
        asp_value = asp_outcome(params)
        if py != asp_value:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a small adventure about a shrunken note, a broken trail, and kindness."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--marker", choices=MARKERS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--leader-name")
    ap.add_argument("--partner-name")
    ap.add_argument("--leader-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("--relation", choices=["friends", "siblings"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the children lose time before repairing the trail")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.marker:
        place = PLACES[args.place]
        marker = MARKERS[args.marker]
        if not marker_fits(place, marker):
            raise StoryError(explain_rejection(place, marker))

    if args.repair:
        repair = REPAIRS[args.repair]
        if repair.sense < SENSE_MIN or not repair.kind:
            raise StoryError(explain_repair(args.repair))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.marker is None or combo[1] == args.marker)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, marker_id = rng.choice(sorted(combos))
    repair_id = args.repair or rng.choice(sorted(r.id for r in sensible_repairs()))
    leader_gender = args.leader_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    leader_name = args.leader_name or pick_name(rng, leader_gender)
    partner_name = args.partner_name or pick_name(rng, partner_gender, avoid=leader_name)
    relation = args.relation or rng.choice(["friends", "siblings"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        place=place_id,
        marker=marker_id,
        repair=repair_id,
        leader_name=leader_name,
        leader_gender=leader_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        relation=relation,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.marker not in MARKERS:
        raise StoryError(f"(Unknown marker: {params.marker})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")

    place = PLACES[params.place]
    marker = MARKERS[params.marker]
    repair = REPAIRS[params.repair]

    if not marker_fits(place, marker):
        raise StoryError(explain_rejection(place, marker))
    if repair.sense < SENSE_MIN or not repair.kind:
        raise StoryError(explain_repair(params.repair))

    world = tell(
        place=place,
        marker=marker,
        repair=repair,
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        relation=params.relation,
        delay=params.delay,
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
    print(sample.story.replace(" leader ", " ").replace(" partner ", " "))
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible repairs: {', '.join(asp_sensible_repairs())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, marker) combos:\n")
        for place, marker in combos:
            print(f"  {place:16} {marker}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for i, params in enumerate(CURATED):
            seeded = StoryParams(
                place=params.place,
                marker=params.marker,
                repair=params.repair,
                leader_name=params.leader_name,
                leader_gender=params.leader_gender,
                partner_name=params.partner_name,
                partner_gender=params.partner_gender,
                relation=params.relation,
                delay=params.delay,
                seed=base_seed + i,
            )
            random.seed(seeded.seed)
            samples.append(generate(seeded))
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
            random.seed(seed)
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
            header = f"### {p.leader_name} and {p.partner_name}: {p.marker} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
