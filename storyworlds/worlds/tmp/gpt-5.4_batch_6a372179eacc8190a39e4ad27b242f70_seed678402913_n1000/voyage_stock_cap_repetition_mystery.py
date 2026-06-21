#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/voyage_stock_cap_repetition_mystery.py
=================================================================

A standalone story world for a small child-facing mystery built from the seed
words "voyage", "stock", and "cap". The domain is a short supply voyage where a
child notices that a captain's cap has gone missing just before departure. The
story uses repetition as a clue pattern and resolves the mystery through a small
physical simulation of tracks, wind, and where the cap could reasonably end up.

Run it
------
    python storyworlds/worlds/gpt-5.4/voyage_stock_cap_repetition_mystery.py
    python storyworlds/worlds/gpt-5.4/voyage_stock_cap_repetition_mystery.py --dock harbor --cargo soup
    python storyworlds/worlds/gpt-5.4/voyage_stock_cap_repetition_mystery.py --cause wind --hide crate
    python storyworlds/worlds/gpt-5.4/voyage_stock_cap_repetition_mystery.py --hide water
    python storyworlds/worlds/gpt-5.4/voyage_stock_cap_repetition_mystery.py --all
    python storyworlds/worlds/gpt-5.4/voyage_stock_cap_repetition_mystery.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/voyage_stock_cap_repetition_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4/voyage_stock_cap_repetition_mystery.py --verify

Reasonableness constraint
-------------------------
Not every hiding place makes a good mystery. The world only allows combinations
where the chosen cause could really move the cap to the chosen place and where a
child detective could find a visible clue. For example, a tied cap cannot blow
into the water, and a calm dock gives no wind trail to follow.
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

# Make the shared result containers importable when this script is run directly:
# add storyworlds/ to sys.path from this nested directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Shared entity model.
# ---------------------------------------------------------------------------
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
        female = {"girl", "mother", "woman", "aunt", "grandmother"}
        male = {"boy", "father", "man", "uncle", "grandfather", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"grandfather": "grandpa", "grandmother": "grandma"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain knobs.
# ---------------------------------------------------------------------------
@dataclass
class Dock:
    id: str
    label: str
    water: str
    trail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    stock_word: str
    smell: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CapStyle:
    id: str
    label: str
    phrase: str
    color: str
    brim: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    clue: str
    verb: str
    moves_to: set[str] = field(default_factory=set)
    needs_breeze: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class HidePlace:
    id: str
    label: str
    phrase: str
    discover: str
    dry: bool = True
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World and rules.
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


def _r_missing_worry(world: World) -> list[str]:
    cap = world.get("cap")
    if cap.attrs.get("place") != "missing":
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("hero").memes["curiosity"] += 1
    world.get("captain").memes["worry"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    cap = world.get("cap")
    if cap.attrs.get("place") == "missing":
        return []
    sig = ("found_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("hero").memes["pride"] += 1
    world.get("captain").memes["relief"] += 1
    world.get("boat").meters["ready"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="social", apply=_r_missing_worry),
    Rule(name="found_relief", tag="social", apply=_r_found_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                produced.extend(sents)
                changed = True
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Constraints and prediction.
# ---------------------------------------------------------------------------
def hide_is_valid(cause: Cause, hide: HidePlace) -> bool:
    return hide.id in cause.moves_to


def best_clue_kind(cause: Cause, hide: HidePlace) -> str:
    if cause.id == "wind":
        return "ribbon"
    if cause.id == "cat":
        return "pawprints"
    if cause.id == "splash":
        return "drops"
    return "trace"


def predict_case(cause: Cause, hide: HidePlace) -> dict:
    return {
        "possible": hide_is_valid(cause, hide),
        "clue_kind": best_clue_kind(cause, hide) if hide_is_valid(cause, hide) else "",
        "dry_end": hide.dry,
    }


# ---------------------------------------------------------------------------
# Story actions.
# ---------------------------------------------------------------------------
def open_scene(world: World, hero: Entity, captain: Entity, dock: Dock, cargo: Cargo,
               cap_style: CapStyle) -> None:
    hero.memes["eager"] += 1
    captain.memes["care"] += 1
    world.say(
        f"Early one gray morning, {hero.id} hurried down to {dock.label} with "
        f"{hero.pronoun('possessive')} {captain.label_word}. Their little boat was "
        f"waiting for a short voyage across {dock.water}."
    )
    world.say(
        f"On the dock sat a neat stock of {cargo.label}: {cargo.stock_word}, "
        f"ropes, and a lantern packed for the trip. {cargo.smell}"
    )
    world.say(
        f"{captain.label_word.capitalize()} hung {cap_style.phrase} on a peg by "
        f"the gangplank while {hero.id} counted the parcels."
    )


def notice_missing(world: World, hero: Entity, captain: Entity, cap_style: CapStyle) -> None:
    cap = world.get("cap")
    cap.attrs["place"] = "missing"
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"When the counting was done, the peg was empty. The {cap_style.label} was gone."
    )
    world.say(
        f'"The cap is gone," whispered {hero.id}. "{cap_style.label.capitalize()}, '
        f'{cap_style.label.lower()}, where did you go?"'
    )
    world.say(
        f"{captain.label_word.capitalize()} looked at the deck, then the dock, then the peg again. "
        f'Without the cap, the trip felt oddly unfinished.'
    )


def repeat_search(world: World, hero: Entity, dock: Dock) -> None:
    world.say(
        f'{hero.id} searched the same three places out loud, because saying them helped '
        f'{hero.pronoun("object")} think. "Not on the peg. Not on the plank. Not by the stock."'
    )
    world.say(
        f"The words came again, soft and steady: not on the peg, not on the plank, "
        f"not by the stock."
    )
    world.facts["refrain"] = "not on the peg, not on the plank, not by the stock"
    world.facts["dock_trail"] = dock.trail


def inspect_clue(world: World, hero: Entity, cause: Cause, hide: HidePlace, dock: Dock) -> None:
    world.get("hero").meters["clues_found"] += 1
    clue_kind = best_clue_kind(cause, hide)
    if cause.id == "wind":
        world.say(
            f"Then {hero.id} noticed {cause.clue} {dock.trail}. A thin ribbon from a flour sack "
            f"quivered under the crate lid, as if the breeze had whispered, this way, this way."
        )
    elif cause.id == "cat":
        world.say(
            f"Then {hero.id} noticed {cause.clue} near the flour dust. Small pawprints crossed "
            f"the dock and stopped beside the crates."
        )
    else:
        world.say(
            f"Then {hero.id} noticed {cause.clue} near the edge of the dock. Bright drops glimmered "
            f"and led toward the mooring post."
        )
    world.facts["clue_kind"] = clue_kind


def solve_case(world: World, hero: Entity, captain: Entity, cause: Cause, hide: HidePlace,
               cap_style: CapStyle, cargo: Cargo) -> None:
    cap = world.get("cap")
    world.para()
    if hide.id == "crate":
        world.say(
            f'"Not on the peg, not on the plank, not by the stock," {hero.id} murmured one last time. '
            f'"Then it must be under the stock."'
        )
        world.say(
            f"{hero.pronoun().capitalize()} lifted the corner of a crate, and there was the "
            f"{cap_style.label}, tucked beneath the boxes of {cargo.label}."
        )
    elif hide.id == "post":
        world.say(
            f'"Not on the peg, not on the plank, not by the stock," {hero.id} said, listening to the '
            f"little slap of water. \"Then I should look where things drift and catch.\""
        )
        world.say(
            f"There, snagged on the rough mooring post, hung the {cap_style.label}."
        )
    else:
        world.say(
            f'"Not on the peg, not on the plank, not by the stock," {hero.id} said. '
            f'"Then I should look low and still."'
        )
        world.say(
            f"In the shallow water beside the dock floated the {cap_style.label}, bobbing gently "
            f"like a sleepy leaf."
        )
    cap.attrs["place"] = hide.id
    cap.attrs["wet"] = 0 if hide.dry else 1
    cap.meters["found"] += 1
    if not hide.dry:
        cap.meters["wet"] += 1
    world.facts["solution_line"] = f"{cause.label} moved the cap to {hide.label}"
    propagate(world, narrate=False)
    if cause.id == "wind":
        world.say(
            f'"The breeze {cause.verb} it," said {hero.id}. "It slid from the peg and sailed away."'
        )
    elif cause.id == "cat":
        world.say(
            f'"The dock cat {cause.verb} it," said {hero.id}. "It must have batted it along the boards."'
        )
    else:
        world.say(
            f'"A fish made a sudden splash and {cause.verb} it," said {hero.id}. '
            f'"The cap hopped, then drifted."'
        )
    if cap.attrs.get("wet"):
        world.say(
            f"{captain.label_word.capitalize()} wrung a little water from the brim and laughed with relief."
        )
    else:
        world.say(
            f"{captain.label_word.capitalize()} brushed the brim smooth and smiled with relief."
        )


def close_scene(world: World, hero: Entity, captain: Entity, dock: Dock, cargo: Cargo,
                cap_style: CapStyle) -> None:
    world.para()
    hero.memes["wonder"] += 1
    world.say(
        f'Soon the parcels were loaded, the {cap_style.label} was back where it belonged, '
        f"and the boat pushed away from {dock.label}."
    )
    world.say(
        f"{hero.id} sat beside the neat stock of {cargo.label} and watched the shore grow small."
    )
    world.say(
        f'The mystery was over, but the words stayed with {hero.pronoun("object")} all across the voyage: '
        f'"Not on the peg, not on the plank, not by the stock" -- until at last they became '
        f'"Safe on the head, safe on the head."'
    )


def tell(dock: Dock, cargo: Cargo, cap_style: CapStyle, cause: Cause, hide: HidePlace,
         hero_name: str = "Mina", hero_type: str = "girl",
         captain_type: str = "grandfather") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    captain = world.add(
        Entity(id="Captain", kind="character", type=captain_type, role="captain", label="the captain")
    )
    boat = world.add(Entity(id="boat", type="boat", label="the little boat"))
    cap = world.add(
        Entity(
            id="cap",
            type="cap",
            label=cap_style.label,
            phrase=cap_style.phrase,
            attrs={"place": "peg", "wet": 0},
            tags=set(cap_style.tags),
        )
    )

    open_scene(world, hero, captain, dock, cargo, cap_style)
    notice_missing(world, hero, captain, cap_style)
    repeat_search(world, hero, dock)
    inspect_clue(world, hero, cause, hide, dock)
    solve_case(world, hero, captain, cause, hide, cap_style, cargo)
    close_scene(world, hero, captain, dock, cargo, cap_style)

    world.facts.update(
        hero=hero,
        captain=captain,
        boat=boat,
        cap=cap,
        dock=dock,
        cargo=cargo,
        cap_style=cap_style,
        cause=cause,
        hide=hide,
        solved=cap.meters["found"] >= THRESHOLD,
        wet=cap.attrs.get("wet", 0) == 1,
    )
    return world


# ---------------------------------------------------------------------------
# Registries.
# ---------------------------------------------------------------------------
DOCKS = {
    "harbor": Dock(
        id="harbor",
        label="the harbor dock",
        water="the bay",
        trail="along the salt-gray boards",
        tags={"boat", "harbor"},
    ),
    "river": Dock(
        id="river",
        label="the river pier",
        water="the slow river",
        trail="over the damp wooden pier",
        tags={"boat", "river"},
    ),
    "canal": Dock(
        id="canal",
        label="the canal wharf",
        water="the narrow canal",
        trail="past the painted bollards",
        tags={"boat", "canal"},
    ),
}

CARGOES = {
    "soup": Cargo(
        id="soup",
        label="vegetable soup stock",
        phrase="jars of vegetable soup stock",
        stock_word="a tidy stock of jars",
        smell="The air held the warm smell of carrots and onions.",
        tags={"stock", "soup"},
    ),
    "seed": Cargo(
        id="seed",
        label="garden seed stock",
        phrase="packets of garden seed stock",
        stock_word="a careful stock of packets",
        smell="Paper packets rustled like dry leaves.",
        tags={"stock", "seed"},
    ),
    "blanket": Cargo(
        id="blanket",
        label="winter blanket stock",
        phrase="bundles from the winter blanket stock",
        stock_word="a snug stock of folded blankets",
        smell="The wool smell was soft and sleepy.",
        tags={"stock", "blanket"},
    ),
}

CAP_STYLES = {
    "blue": CapStyle(
        id="blue",
        label="blue cap",
        phrase="a blue captain's cap",
        color="blue",
        brim="dark brim",
        tags={"cap", "blue"},
    ),
    "red": CapStyle(
        id="red",
        label="red cap",
        phrase="a red wool cap with a small brass button",
        color="red",
        brim="round brim",
        tags={"cap", "red"},
    ),
    "striped": CapStyle(
        id="striped",
        label="striped cap",
        phrase="a striped skipper cap",
        color="striped",
        brim="short brim",
        tags={"cap", "striped"},
    ),
}

CAUSES = {
    "wind": Cause(
        id="wind",
        label="the breeze",
        clue="a flapping sack ribbon",
        verb="blew",
        moves_to={"crate", "post", "water"},
        needs_breeze=True,
        tags={"wind", "clue"},
    ),
    "cat": Cause(
        id="cat",
        label="the dock cat",
        clue="tiny pawprints",
        verb="batted",
        moves_to={"crate", "post"},
        tags={"cat", "clue"},
    ),
    "splash": Cause(
        id="splash",
        label="a silver fish splash",
        clue="bright water drops",
        verb="nudged",
        moves_to={"post", "water"},
        tags={"water", "clue"},
    ),
}

HIDES = {
    "crate": HidePlace(
        id="crate",
        label="the crate stack",
        phrase="under the cargo crates",
        discover="by lifting a crate corner",
        dry=True,
        tags={"crate"},
    ),
    "post": HidePlace(
        id="post",
        label="the mooring post",
        phrase="caught on the mooring post",
        discover="by peering over the side",
        dry=True,
        tags={"post"},
    ),
    "water": HidePlace(
        id="water",
        label="the water beside the dock",
        phrase="floating in the water",
        discover="by looking low beside the boards",
        dry=False,
        tags={"water"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tess", "Ruby", "Ava", "Ella", "June"]
BOY_NAMES = ["Owen", "Finn", "Leo", "Sam", "Max", "Theo", "Eli", "Ben"]


# ---------------------------------------------------------------------------
# Story parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    dock: str
    cargo: str
    cap_style: str
    cause: str
    hide: str
    hero_name: str
    hero_type: str
    captain_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Curated set.
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        dock="harbor",
        cargo="soup",
        cap_style="blue",
        cause="wind",
        hide="crate",
        hero_name="Mina",
        hero_type="girl",
        captain_type="grandfather",
    ),
    StoryParams(
        dock="river",
        cargo="seed",
        cap_style="red",
        cause="cat",
        hide="post",
        hero_name="Owen",
        hero_type="boy",
        captain_type="grandmother",
    ),
    StoryParams(
        dock="canal",
        cargo="blanket",
        cap_style="striped",
        cause="splash",
        hide="water",
        hero_name="Lila",
        hero_type="girl",
        captain_type="grandfather",
    ),
    StoryParams(
        dock="harbor",
        cargo="seed",
        cap_style="red",
        cause="wind",
        hide="post",
        hero_name="Finn",
        hero_type="boy",
        captain_type="grandfather",
    ),
]


# ---------------------------------------------------------------------------
# QA.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "voyage": [
        (
            "What is a voyage?",
            "A voyage is a trip from one place to another, often by boat or ship. It can be short or long, but it means traveling with a purpose."
        )
    ],
    "stock": [
        (
            "What does stock mean in this story?",
            "Here, stock means a supply of things kept ready to use or carry. It is a neat group of goods packed for the trip."
        )
    ],
    "cap": [
        (
            "What is a cap?",
            "A cap is a soft hat that fits close on your head. Some caps also have a brim to shade your face."
        )
    ],
    "wind": [
        (
            "How can wind move light things?",
            "Wind pushes on light things like paper, ribbons, and hats. If they are loose, they can slide, tumble, or blow away."
        )
    ],
    "cat": [
        (
            "Why do cats bat things with their paws?",
            "Cats often tap and bat small things because they are curious and playful. A round or soft thing can start moving when a cat pats it."
        )
    ],
    "water": [
        (
            "Why do things drift on water?",
            "Some things float and drift because the water holds them up and gentle movement carries them along. They may catch on posts or edges as they move."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you solve a problem or mystery. It points your mind in the right direction."
        )
    ],
    "repetition": [
        (
            "Why do people repeat words while they think?",
            "Repeating words can help your mind stay focused. It also helps you notice patterns and remember what you have already checked."
        )
    ],
}
KNOWLEDGE_ORDER = ["voyage", "stock", "cap", "wind", "cat", "water", "clue", "repetition"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    cargo = f["cargo"]
    cap_style = f["cap_style"]
    cause = f["cause"]
    hide = f["hide"]
    return [
        f'Write a gentle mystery story for a 3-to-5-year-old that includes the words "voyage", "stock", and "cap".',
        f"Tell a child-friendly dockside mystery where {hero.id} helps solve the disappearance of a {cap_style.label} before a boat voyage with a stock of {cargo.label}.",
        f"Write a repetitive mystery where a missing cap is found by following a clue left by {cause.label} to {hide.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    cargo = f["cargo"]
    cap_style = f["cap_style"]
    cause = f["cause"]
    hide = f["hide"]
    refrain = f.get("refrain", "")
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {hero.pronoun('possessive')} {captain.label_word}, who were getting a little boat ready for a voyage. They were loading a stock of {cargo.label} when the mystery began."
        ),
        (
            "What was the mystery?",
            f"The mystery was that the {cap_style.label} vanished from its peg before the boat left. That made the dock feel strange, because the voyage could not begin in the usual happy way."
        ),
        (
            "What words did the child keep repeating?",
            f'{hero.id} kept repeating, "{refrain}." The repeated line helped {hero.pronoun("object")} remember where {hero.pronoun("subject")} had already looked and pushed the search toward a new place.'
        ),
        (
            f"What clue helped {hero.id} solve the mystery?",
            f"{hero.id} noticed {cause.clue}. That clue matched what {cause.label} could have done, so it pointed the search toward {hide.label}."
        ),
        (
            "Where was the cap found?",
            f"The cap was found at {hide.label}. {hero.id} checked there because the clue made that place seem more likely than the peg, the plank, or the stock."
        ),
        (
            "How was the mystery solved?",
            f"{hero.id} used careful looking and repeated the same searching words until the pattern changed. Then {hero.pronoun('subject').capitalize()} followed the clue and worked out that {cause.label} had moved the cap."
        ),
    ]
    if f.get("wet"):
        qa.append(
            (
                "Was the cap dry when they found it?",
                f"No. The cap had gotten wet because it ended up in the water beside the dock. {captain.label_word.capitalize()} had to wring the brim before the voyage could begin."
            )
        )
    else:
        qa.append(
            (
                "What changed at the end?",
                f"At the end, the cap was back, the captain felt relieved, and the little boat was finally ready. The mystery ending is shown by the boat pushing away from the dock with everything in its proper place."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"voyage", "stock", "cap", "clue", "repetition"}
    tags |= set(f["cause"].tags)
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
# Trace.
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or k == "place"}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reasonableness helpers.
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for dock_id in DOCKS:
        for cargo_id in CARGOES:
            for cap_id in CAP_STYLES:
                for cause_id, cause in CAUSES.items():
                    for hide_id, hide in HIDES.items():
                        if hide_is_valid(cause, hide):
                            combos.append((dock_id, cargo_id, cap_id, cause_id, hide_id))
    return combos


def explain_rejection(cause: Cause, hide: HidePlace) -> str:
    return (
        f"(No story: {cause.label} cannot reasonably move the cap to {hide.label}. "
        f"Choose a hiding place that fits the cause's path and leaves a clue.)"
    )


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
can_move(Cause, Hide) :- moves_to(Cause, Hide).
valid(Dock, Cargo, Cap, Cause, Hide) :-
    dock(Dock), cargo(Cargo), cap_style(Cap), cause(Cause), hide(Hide),
    can_move(Cause, Hide).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for dock_id in DOCKS:
        lines.append(asp.fact("dock", dock_id))
    for cargo_id in CARGOES:
        lines.append(asp.fact("cargo", cargo_id))
    for cap_id in CAP_STYLES:
        lines.append(asp.fact("cap_style", cap_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        for hide_id in sorted(cause.moves_to):
            lines.append(asp.fact("moves_to", cause_id, hide_id))
    for hide_id in HIDES:
        lines.append(asp.fact("hide", hide_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child solves a dockside cap mystery before a voyage."
    )
    ap.add_argument("--dock", choices=DOCKS)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--cap-style", dest="cap_style", choices=CAP_STYLES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--hide", choices=HIDES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--captain", dest="captain_type", choices=["grandfather", "grandmother"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.hide:
        cause = CAUSES[args.cause]
        hide = HIDES[args.hide]
        if not hide_is_valid(cause, hide):
            raise StoryError(explain_rejection(cause, hide))

    combos = [
        combo for combo in valid_combos()
        if (args.dock is None or combo[0] == args.dock)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.cap_style is None or combo[2] == args.cap_style)
        and (args.cause is None or combo[3] == args.cause)
        and (args.hide is None or combo[4] == args.hide)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    dock_id, cargo_id, cap_id, cause_id, hide_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    captain_type = args.captain_type or rng.choice(["grandfather", "grandmother"])
    return StoryParams(
        dock=dock_id,
        cargo=cargo_id,
        cap_style=cap_id,
        cause=cause_id,
        hide=hide_id,
        hero_name=hero_name,
        hero_type=hero_type,
        captain_type=captain_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.dock not in DOCKS:
        raise StoryError(f"(Unknown dock: {params.dock})")
    if params.cargo not in CARGOES:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.cap_style not in CAP_STYLES:
        raise StoryError(f"(Unknown cap style: {params.cap_style})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.hide not in HIDES:
        raise StoryError(f"(Unknown hiding place: {params.hide})")

    cause = CAUSES[params.cause]
    hide = HIDES[params.hide]
    if not hide_is_valid(cause, hide):
        raise StoryError(explain_rejection(cause, hide))

    world = tell(
        dock=DOCKS[params.dock],
        cargo=CARGOES[params.cargo],
        cap_style=CAP_STYLES[params.cap_style],
        cause=cause,
        hide=hide,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        captain_type=params.captain_type,
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
        print(asp_program("", "#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (dock, cargo, cap_style, cause, hide) combos:\n")
        for dock_id, cargo_id, cap_id, cause_id, hide_id in combos:
            print(f"  {dock_id:7} {cargo_id:8} {cap_id:8} {cause_id:6} {hide_id}")
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
                f"### {p.hero_name}: {p.cap_style} cap at {p.dock} "
                f"({p.cause} -> {p.hide}, cargo: {p.cargo})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
