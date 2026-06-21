#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gent_draft_whoosh_reconciliation_adventure.py
========================================================================

A small storyworld about two children on a make-believe adventure. A loose clue
gets swept away by a cool draft with a sudden whoosh, the children quarrel, and
they must reconcile to finish the quest together.

The generated stories are not frozen templates with swapped nouns. They model a
tiny world with typed entities, physical meters, emotional memes, a small causal
engine, a reasonableness gate, and an inline ASP twin.

Run it
------
    python storyworlds/worlds/gpt-5.4/gent_draft_whoosh_reconciliation_adventure.py
    python storyworlds/worlds/gpt-5.4/gent_draft_whoosh_reconciliation_adventure.py --place attic --clue map
    python storyworlds/worlds/gpt-5.4/gent_draft_whoosh_reconciliation_adventure.py --clue stone_tablet
    python storyworlds/worlds/gpt-5.4/gent_draft_whoosh_reconciliation_adventure.py --all
    python storyworlds/worlds/gpt-5.4/gent_draft_whoosh_reconciliation_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4/gent_draft_whoosh_reconciliation_adventure.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
REPAIR_MIN = 2


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
    scene: str
    hideout: str
    draft_from: str
    whoosh_line: str
    treasure: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    line: str
    light: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    line: str
    hurt: int
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Bridge:
    id: str
    line: str
    power: int
    offers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    clue: str
    cause: str
    bridge: str
    name1: str
    gender1: str
    name2: str
    gender2: str
    parent: str
    trait1: str
    trait2: str
    seed: Optional[int] = None


PLACES = {
    "attic": Place(
        id="attic",
        scene="a secret attic fort under the roof",
        hideout="the little door behind the old trunks",
        draft_from="a crack near the roof beams",
        whoosh_line="The cool air slipped under the eaves and made the paper flutter with a soft whoosh.",
        treasure="a tin star badge",
        ending_image="They came back down the ladder with the badge shining between them.",
        tags={"attic", "draft", "adventure"},
    ),
    "treehouse": Place(
        id="treehouse",
        scene="a treehouse lookout high in the leaves",
        hideout="the narrow cubby behind the flag box",
        draft_from="a loose board by the window frame",
        whoosh_line="A lively puff curled through the boards and sent the clue dancing away with a whoosh.",
        treasure="a painted explorer button",
        ending_image="They climbed down the ladder with the button safe in both hands.",
        tags={"treehouse", "draft", "adventure"},
    ),
    "lighthouse": Place(
        id="lighthouse",
        scene="a pretend lighthouse at the top of the stairs",
        hideout="the round panel beside the lamp shelf",
        draft_from="a thin gap around the window latch",
        whoosh_line="A salty draft slid through the gap and the clue skipped away with a bright whoosh.",
        treasure="a brass compass token",
        ending_image="They stood by the window with the token warm in their joined palms.",
        tags={"lighthouse", "draft", "adventure"},
    ),
}

CLUES = {
    "map": Clue(
        id="map",
        label="map",
        phrase="a folded paper map",
        line='In one corner, a funny little stamp said "gent," which made them giggle.',
        light=True,
        tags={"map", "paper", "gent"},
    ),
    "feather": Clue(
        id="feather",
        label="feather clue",
        phrase="a feather tied to a ribbon clue",
        line='On the ribbon was the odd word "gent" in tiny blue letters.',
        light=True,
        tags={"feather", "gent"},
    ),
    "sail": Clue(
        id="sail",
        label="paper sail",
        phrase="a paper sail marked with arrow stars",
        line='Across the bottom, someone had penciled the silly word "gent."',
        light=True,
        tags={"sail", "paper", "gent"},
    ),
    "stone_tablet": Clue(
        id="stone_tablet",
        label="stone tablet",
        phrase="a heavy stone tablet",
        line='It had the word "gent" scratched on it, but it was far too heavy to flutter.',
        light=False,
        tags={"stone", "gent"},
    ),
}

CAUSES = {
    "grab": Cause(
        id="grab",
        line="{a} snatched the clue first and said, \"I should lead because I found the fort.\" {b} pulled back, and both of them frowned.",
        hurt=2,
        needs={"share", "apology"},
        tags={"sharing", "hurt"},
    ),
    "blame": Cause(
        id="blame",
        line="{a} pointed at {b} and said, \"You let it go.\" {b}'s brave face crumpled a little.",
        hurt=3,
        needs={"apology", "help"},
        tags={"blame", "hurt"},
    ),
    "boast": Cause(
        id="boast",
        line="{a} puffed up and said, \"I can finish this adventure alone.\" That made {b} step back and fold {pb} arms.",
        hurt=2,
        needs={"help", "apology"},
        tags={"pride", "hurt"},
    ),
}

BRIDGES = {
    "apology": Bridge(
        id="apology",
        line='{a} took a breath and said, "I was unkind. I am sorry."',
        power=2,
        offers={"apology"},
        tags={"apology", "reconciliation"},
    ),
    "share": Bridge(
        id="share",
        line='{a} held the clue between them and said, "Let us lead together and take turns."',
        power=2,
        offers={"share"},
        tags={"sharing", "reconciliation"},
    ),
    "help_search": Bridge(
        id="help_search",
        line='{a} said, "I should not have pushed ahead. Will you help me search by {place_draft}?"',
        power=3,
        offers={"help", "apology"},
        tags={"help", "reconciliation"},
    ),
    "wave_off": Bridge(
        id="wave_off",
        line='{a} shrugged and said, "It is not a big deal."',
        power=1,
        offers={"none"},
        tags={"weak"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Theo"]
TRAITS = ["bold", "careful", "curious", "steady", "bright", "kind"]


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


def _r_draft_moves_clue(world: World) -> list[str]:
    clue = world.get("clue")
    place = world.get("place")
    if clue.meters["loose"] < THRESHOLD:
        return []
    if place.meters["drafty"] < THRESHOLD:
        return []
    sig = ("draft_moves", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clue.meters["lost"] += 1
    clue.meters["near_hatch"] += 1
    return ["__whoosh__"]


def _r_hurt_blocks_team(world: World) -> list[str]:
    a = world.get("kid1")
    b = world.get("kid2")
    if a.memes["hurt"] < THRESHOLD and b.memes["hurt"] < THRESHOLD:
        return []
    sig = ("team_block",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["apart"] += 1
    b.memes["apart"] += 1
    return []


def _r_reconcile_restores_team(world: World) -> list[str]:
    a = world.get("kid1")
    b = world.get("kid2")
    if a.memes["repair"] < THRESHOLD:
        return []
    sig = ("repair",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["hurt"] = 0.0
    b.memes["hurt"] = 0.0
    a.memes["apart"] = 0.0
    b.memes["apart"] = 0.0
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    a.memes["together"] += 1
    b.memes["together"] += 1
    return []


def _r_find_treasure(world: World) -> list[str]:
    a = world.get("kid1")
    b = world.get("kid2")
    clue = world.get("clue")
    treasure = world.get("treasure")
    if clue.meters["near_hatch"] < THRESHOLD:
        return []
    if a.memes["together"] < THRESHOLD or b.memes["together"] < THRESHOLD:
        return []
    sig = ("find_treasure",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    treasure.meters["found"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="draft_moves_clue", tag="physical", apply=_r_draft_moves_clue),
    Rule(name="hurt_blocks_team", tag="social", apply=_r_hurt_blocks_team),
    Rule(name="reconcile_restores_team", tag="social", apply=_r_reconcile_restores_team),
    Rule(name="find_treasure", tag="physical", apply=_r_find_treasure),
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
        for item in produced:
            if item == "__whoosh__":
                place = world.facts["place_cfg"]
                world.say(place.whoosh_line)
    return produced


def clue_at_risk(place: Place, clue: Clue) -> bool:
    return clue.light


def bridge_works(cause: Cause, bridge: Bridge) -> bool:
    return bool(cause.needs & bridge.offers)


def sensible_bridges() -> list[Bridge]:
    return [b for b in BRIDGES.values() if b.power >= REPAIR_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for clue_id, clue in CLUES.items():
            for cause_id, cause in CAUSES.items():
                for bridge_id, bridge in BRIDGES.items():
                    if clue_at_risk(place, clue) and bridge_works(cause, bridge) and bridge.power >= REPAIR_MIN:
                        out.append((place_id, clue_id, cause_id, bridge_id))
    return out


def outcome_of(params: StoryParams) -> str:
    cause = CAUSES[params.cause]
    bridge = BRIDGES[params.bridge]
    return "quick" if bridge.power >= cause.hurt else "stumble"


def explain_clue(place: Place, clue: Clue) -> str:
    return (
        f"(No story: {clue.phrase} would not be swept by a draft in {place.hideout}. "
        f"This adventure needs a light clue that can skitter away on the wind.)"
    )


def explain_bridge(cause: Cause, bridge: Bridge) -> str:
    if bridge.power < REPAIR_MIN:
        return (
            f"(Refusing bridge '{bridge.id}': it is too weak for this world "
            f"(power={bridge.power} < {REPAIR_MIN}). A reconciliation story should use a real repair move.)"
        )
    need = " / ".join(sorted(cause.needs))
    return (
        f"(No story: bridge '{bridge.id}' does not fit the quarrel '{cause.id}'. "
        f"This hurt needs {need} to feel honestly repaired.)"
    )


def predict_loss(world: World) -> dict:
    sim = world.copy()
    sim.get("clue").meters["loose"] += 1
    propagate(sim, narrate=False)
    return {
        "lost": sim.get("clue").meters["lost"] >= THRESHOLD,
        "near_hatch": sim.get("clue").meters["near_hatch"] >= THRESHOLD,
    }


def introduce(world: World, a: Entity, b: Entity, place: Place, clue: Clue) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"After lunch, {a.id} and {b.id} turned the house into {place.scene}. "
        f"They whispered that {place.hideout} might hide a prize."
    )
    world.say(
        f"They carried {clue.phrase} as their treasure clue. {clue.line}"
    )


def notice_wind(world: World, a: Entity, b: Entity, place: Place) -> None:
    world.get("place").meters["drafty"] += 1
    world.say(
        f"As they crept closer, a cool draft brushed their cheeks from {place.draft_from}. "
        f'"Did you feel that?" {b.id} whispered.'
    )


def loose_clue(world: World, a: Entity, clue: Clue) -> None:
    world.get("clue").meters["loose"] += 1
    world.say(
        f"{a.id} lifted {clue.phrase} a little higher so the arrows could catch the light."
    )
    pred = predict_loss(world)
    world.facts["predicted_loss"] = pred["lost"]


def quarrel(world: World, a: Entity, b: Entity, cause: Cause) -> None:
    b.memes["hurt"] += cause.hurt
    a.memes["pride"] += 1
    pa = a.pronoun("possessive")
    pb = b.pronoun("possessive")
    world.say(cause.line.format(a=a.id, b=b.id, pa=pa, pb=pb))
    world.say("For a moment, the adventure felt smaller than their feelings.")
    propagate(world, narrate=False)


def wind_snatch(world: World) -> None:
    propagate(world, narrate=True)
    clue = world.facts["clue_cfg"]
    place = world.facts["place_cfg"]
    world.say(
        f"The {clue.label} slid across the floor and vanished by {place.hideout}."
    )


def lonely_try(world: World, a: Entity, b: Entity, place: Place) -> None:
    a.memes["worry"] += 1
    world.say(
        f"{a.id} tried to squeeze toward {place.hideout} alone, but the gap was awkward and the room felt too quiet."
    )
    world.say(
        f"When {a.pronoun()} looked back and saw {b.id} standing apart, the lonely part of the adventure finally felt wrong."
    )


def repair(world: World, a: Entity, b: Entity, bridge: Bridge, place: Place) -> None:
    line = bridge.line.format(a=a.id, b=b.id, place_draft=place.draft_from)
    world.say(line)
    world.get("kid1").memes["repair"] += bridge.power
    propagate(world, narrate=False)
    world.say(
        f"{b.id} looked at {a.id} for a heartbeat, then stepped close again. The tight feeling between them began to loosen."
    )


def search_together(world: World, a: Entity, b: Entity, place: Place) -> None:
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    a.memes["together"] += 1
    b.memes["together"] += 1
    propagate(world, narrate=False)
    treasure = world.facts["place_cfg"].treasure
    world.say(
        f"Together they followed the chilly air to {place.hideout}. "
        f"{b.id} held the panel steady while {a.id} reached in."
    )
    world.say(
        f"Inside was {treasure}, tucked behind the wood as if it had been waiting for both of them."
    )


def ending(world: World, a: Entity, b: Entity, place: Place) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["trust"] += 1
    world.say(
        f'"Next time," {a.id} said, "we stay on the same team."'
    )
    world.say(
        f'"Even when there is a whoosh and a surprise," {b.id} said, smiling.'
    )
    world.say(place.ending_image)


def tell(
    place: Place,
    clue_cfg: Clue,
    cause: Cause,
    bridge: Bridge,
    name1: str = "Lily",
    gender1: str = "girl",
    name2: str = "Tom",
    gender2: str = "boy",
    parent_type: str = "mother",
    trait1: str = "bold",
    trait2: str = "careful",
) -> World:
    world = World()
    a = world.add(Entity(id="kid1", kind="character", type=gender1, label=name1, phrase=name1, role="leader", attrs={"trait": trait1}))
    b = world.add(Entity(id="kid2", kind="character", type=gender2, label=name2, phrase=name2, role="partner", attrs={"trait": trait2}))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", phrase="the parent", role="parent"))
    place_ent = world.add(Entity(id="place", type="place", label=place.id, phrase=place.hideout, tags=set(place.tags)))
    clue = world.add(Entity(id="clue", type="clue", label=clue_cfg.label, phrase=clue_cfg.phrase, tags=set(clue_cfg.tags)))
    treasure = world.add(Entity(id="treasure", type="treasure", label=place.treasure, phrase=place.treasure))

    world.facts.update(
        kid1=a,
        kid2=b,
        parent=parent,
        place_cfg=place,
        clue_cfg=clue_cfg,
        cause_cfg=cause,
        bridge_cfg=bridge,
        clue_ent=clue,
        treasure_ent=treasure,
        names=(name1, name2),
    )

    introduce(world, a, b, place, clue_cfg)
    notice_wind(world, a, b, place)

    world.para()
    loose_clue(world, a, clue_cfg)
    quarrel(world, a, b, cause)
    wind_snatch(world)

    world.para()
    outcome = "quick" if bridge.power >= cause.hurt else "stumble"
    world.facts["outcome"] = outcome
    if outcome == "stumble":
        lonely_try(world, a, b, place)
    repair(world, a, b, bridge, place)
    search_together(world, a, b, place)

    world.para()
    ending(world, a, b, place)

    world.facts.update(
        reconciled=a.memes["together"] >= THRESHOLD and b.memes["together"] >= THRESHOLD,
        found=treasure.meters["found"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "draft": [
        (
            "What is a draft?",
            "A draft is a little stream of moving air that slips through a crack or an open space. It can feel cool on your skin and make light things flutter.",
        )
    ],
    "whoosh": [
        (
            "What does whoosh mean?",
            "Whoosh is a word people use for a fast rushing sound. Wind, paper, or something moving quickly can make a whoosh.",
        )
    ],
    "map": [
        (
            "What does a map help you do?",
            "A map helps you find your way from one place to another. It can show where to look next on an adventure.",
        )
    ],
    "sharing": [
        (
            "Why does taking turns help friends?",
            "Taking turns helps both people feel included and respected. Sharing can make a game fair and keep hurt feelings from growing.",
        )
    ],
    "apology": [
        (
            "What makes an apology feel real?",
            "A real apology says what was unkind and shows you want to make things better. Kind actions after the words help the other person believe you.",
        )
    ],
    "help": [
        (
            "Why can helping fix a quarrel?",
            "Helping shows that you care about the other person and the problem you made together. Working side by side can rebuild trust.",
        )
    ],
    "reconciliation": [
        (
            "What is reconciliation?",
            "Reconciliation is when people who were upset make peace again. They listen, repair the hurt, and come back together.",
        )
    ],
}
KNOWLEDGE_ORDER = ["draft", "whoosh", "map", "sharing", "apology", "help", "reconciliation"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["kid1"].label
    b = f["kid2"].label
    place = f["place_cfg"]
    clue = f["clue_cfg"]
    return [
        f'Write an adventure story for a 3-to-5-year-old that includes the words "gent," "draft," and "whoosh," and ends in reconciliation.',
        f"Tell a gentle adventure where {a} and {b} lose {clue.phrase} in {place.scene}, quarrel, and then make peace so they can finish the quest together.",
        f"Write a child-facing story about a small adventure, a hurt feeling, and a repaired friendship after a clue is swept away by moving air.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["kid1"]
    b = f["kid2"]
    place = f["place_cfg"]
    clue = f["clue_cfg"]
    cause = f["cause_cfg"]
    bridge = f["bridge_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.label} and {b.label}, who turned the house into {place.scene}. They were hunting for a hidden prize together.",
        ),
        (
            "What did the children use as their clue?",
            f"They used {clue.phrase} as their clue. It was light enough for the wind to catch and send skittering away.",
        ),
        (
            "Why did the clue blow away?",
            f"A cool draft came from {place.draft_from}, and the clue was loose in the air. That moving air made it flutter away with a whoosh.",
        ),
        (
            "Why did the children get upset with each other?",
            f"They had a quarrel because of {cause.id}. The unkind moment hurt {b.label}'s feelings, so the adventure stopped feeling fun.",
        ),
    ]
    if f.get("outcome") == "stumble":
        qa.append(
            (
                f"Did {a.label} fix the problem right away?",
                f"No. {a.label} first tried to keep going alone, and that lonely try felt wrong. Then {a.pronoun('subject')} slowed down, repaired the hurt, and came back to {b.label}.",
            )
        )
    qa.append(
        (
            "How did they reconcile?",
            f"They reconciled when {bridge.line.format(a=a.label, b=b.label, place_draft=place.draft_from)} {b.label} came close again because the repair matched what the quarrel needed.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"They worked together, found {place.treasure}, and felt like one team again. The ending image shows the adventure changed because the prize mattered less than making peace.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"draft", "whoosh", "reconciliation"} | set(f["bridge_cfg"].tags)
    if "map" in f["clue_cfg"].tags:
        tags.add("map")
    if "sharing" in f["cause_cfg"].tags or "sharing" in f["bridge_cfg"].tags:
        tags.add("sharing")
    if "apology" in f["bridge_cfg"].tags:
        tags.add("apology")
    if "help" in f["bridge_cfg"].tags:
        tags.add("help")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.label and ent.id not in ent.label:
            bits.append(f"label={ent.label!r}")
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
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="attic",
        clue="map",
        cause="blame",
        bridge="help_search",
        name1="Lily",
        gender1="girl",
        name2="Tom",
        gender2="boy",
        parent="mother",
        trait1="bold",
        trait2="steady",
    ),
    StoryParams(
        place="treehouse",
        clue="feather",
        cause="grab",
        bridge="share",
        name1="Mia",
        gender1="girl",
        name2="Ben",
        gender2="boy",
        parent="father",
        trait1="curious",
        trait2="kind",
    ),
    StoryParams(
        place="lighthouse",
        clue="sail",
        cause="boast",
        bridge="apology",
        name1="Sam",
        gender1="boy",
        name2="Leo",
        gender2="boy",
        parent="mother",
        trait1="bright",
        trait2="careful",
    ),
    StoryParams(
        place="attic",
        clue="map",
        cause="blame",
        bridge="apology",
        name1="Ava",
        gender1="girl",
        name2="Ella",
        gender2="girl",
        parent="father",
        trait1="bold",
        trait2="kind",
    ),
]


ASP_RULES = r"""
% A clue is at risk when it is light enough for the draft to move.
at_risk(P, C) :- place(P), clue(C), light(C).

% A bridge fits a cause when it offers at least one needed repair move.
bridge_works(Ca, Br) :- cause(Ca), bridge(Br), needs(Ca, X), offers(Br, X).

% Reasonable story combinations.
valid(P, C, Ca, Br) :- at_risk(P, C), bridge_works(Ca, Br), power(Br, Pw), repair_min(M), Pw >= M.

% Outcome: quick repair when the bridge is strong enough for the hurt.
quick :- chosen_cause(Ca), chosen_bridge(Br), hurt(Ca, H), power(Br, P), P >= H.
outcome(quick) :- quick.
outcome(stumble) :- not quick.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        if clue.light:
            lines.append(asp.fact("light", clue_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("hurt", cause_id, cause.hurt))
        for need in sorted(cause.needs):
            lines.append(asp.fact("needs", cause_id, need))
    for bridge_id, bridge in BRIDGES.items():
        lines.append(asp.fact("bridge", bridge_id))
        lines.append(asp.fact("power", bridge_id, bridge.power))
        for offer in sorted(bridge.offers):
            lines.append(asp.fact("offers", bridge_id, offer))
    lines.append(asp.fact("repair_min", REPAIR_MIN))
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
            asp.fact("chosen_cause", params.cause),
            asp.fact("chosen_bridge", params.bridge),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
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
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="smoke")
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke generation and emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a windy adventure, a quarrel, and reconciliation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--bridge", choices=BRIDGES)
    ap.add_argument("--parent", choices=["mother", "father"])
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


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.clue:
        place = PLACES[args.place]
        clue = CLUES[args.clue]
        if not clue_at_risk(place, clue):
            raise StoryError(explain_clue(place, clue))
    if args.cause and args.bridge:
        cause = CAUSES[args.cause]
        bridge = BRIDGES[args.bridge]
        if not bridge_works(cause, bridge) or bridge.power < REPAIR_MIN:
            raise StoryError(explain_bridge(cause, bridge))
    if args.bridge and BRIDGES[args.bridge].power < REPAIR_MIN:
        cause = CAUSES[args.cause] if args.cause else CAUSES[next(iter(CAUSES))]
        raise StoryError(explain_bridge(cause, BRIDGES[args.bridge]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.clue is None or combo[1] == args.clue)
        and (args.cause is None or combo[2] == args.cause)
        and (args.bridge is None or combo[3] == args.bridge)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, clue, cause, bridge = rng.choice(sorted(combos))
    name1, gender1 = _pick_child(rng)
    name2, gender2 = _pick_child(rng, avoid=name1)
    parent = args.parent or rng.choice(["mother", "father"])
    trait1 = rng.choice(TRAITS)
    trait2 = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        clue=clue,
        cause=cause,
        bridge=bridge,
        name1=name1,
        gender1=gender1,
        name2=name2,
        gender2=gender2,
        parent=parent,
        trait1=trait1,
        trait2=trait2,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.clue not in CLUES:
        raise StoryError(f"(Invalid clue: {params.clue})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Invalid cause: {params.cause})")
    if params.bridge not in BRIDGES:
        raise StoryError(f"(Invalid bridge: {params.bridge})")

    place = PLACES[params.place]
    clue = CLUES[params.clue]
    cause = CAUSES[params.cause]
    bridge = BRIDGES[params.bridge]

    if not clue_at_risk(place, clue):
        raise StoryError(explain_clue(place, clue))
    if not bridge_works(cause, bridge) or bridge.power < REPAIR_MIN:
        raise StoryError(explain_bridge(cause, bridge))

    world = tell(
        place=place,
        clue_cfg=clue,
        cause=cause,
        bridge=bridge,
        name1=params.name1,
        gender1=params.gender1,
        name2=params.name2,
        gender2=params.gender2,
        parent_type=params.parent,
        trait1=params.trait1,
        trait2=params.trait2,
    )

    story = world.render().replace("kid1", params.name1).replace("kid2", params.name2)
    story = story.replace("parent", world.get("parent").label_word)

    for ent_id, real_name in (("kid1", params.name1), ("kid2", params.name2)):
        ent = world.get(ent_id)
        ent.id = real_name
        ent.label = real_name
    world.entities[params.name1] = world.entities.pop("kid1")
    world.entities[params.name2] = world.entities.pop("kid2")

    sample = StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )
    return sample


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
        print(f"{len(combos)} compatible (place, clue, cause, bridge) combos:\n")
        for place, clue, cause, bridge in combos:
            print(f"  {place:10} {clue:12} {cause:8} {bridge}")
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
            header = f"### {p.name1} & {p.name2}: {p.place}, {p.clue}, {p.cause}->{p.bridge} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
