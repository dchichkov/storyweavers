#!/usr/bin/env python3
"""
storyworlds/worlds/cozy_garden_misty_flower_forest_trail_sharing.py
===================================================================

Seed prompt
-----------
Write a story that includes the following words and narrative instruments.
Words: cozy garden, misty flower
Setting: forest trail
Features: Sharing, Happy Ending
Style: Whodunit

Source tale written from the seed
---------------------------------
Mira cared for a cozy garden beside a forest trail. One afternoon the prettiest
misty flower vanished from its round stone stand, leaving only a damp ring and
a clue on the path. Instead of blaming the first child she thought of, Mira
followed the clue like a gentle little detective.

The clue led her to a resting place farther down the trail, where she found that
another child had borrowed the flower to comfort someone tired or sad. The
flower had not been stolen for greed; it had been carried away for sharing.
Mira still said that borrowing needed asking first. Together they brought the
flower back, made a plan for sharing it properly, and ended the day with a
happier garden than the one they started with.

This script rebuilds that shape as a small state-driven whodunit. Valid stories
must line up physically and emotionally: the chosen trail must reach the sharing
spot, the borrower must be able to carry the flower there, the clue must match
that spot, and the flower's comfort must fit the person being helped. The happy
ending comes from changing the world state into open sharing instead of secret
borrowing.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Trail:
    id: str
    name: str
    opening: str
    mist_detail: str
    paths: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Flower:
    id: str
    label: str
    phrase: str
    pot: str
    size: int
    gifts: set[str]
    scent: str
    ending_color: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Borrower:
    id: str
    label: str
    role: str
    route: set[str]
    carries: set[int]
    shares_for: set[str]
    motive: str
    apology: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class ShareSpot:
    id: str
    label: str
    where: str
    path: str
    capacity: int
    need: str
    trace: str
    recipient: str
    recipient_state: str
    share_action: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Clue:
    id: str
    trace: str
    whisper: str
    sensory: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    type: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, int] = field(default_factory=dict)
    memes: dict[str, int] = field(default_factory=dict)
    attrs: dict[str, object] = field(default_factory=dict)


@dataclass
class Event:
    id: str
    actor: str
    place: str
    text: str
    target: Optional[str] = None


@dataclass
class StoryWorld:
    params: "StoryParams"
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, event_id: str, actor: str, place: str, text: str, target: str | None = None) -> None:
        self.history.append(Event(event_id, actor, place, text, target))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


TRAILS = {
    "fern_bend": Trail(
        "fern_bend",
        "Fern Bend",
        "Beside the forest trail at Fern Bend, Mira kept a cozy garden in three round beds edged with smooth stones.",
        "cool mist drifted low enough to brush the leaves",
        {"stone_step", "berry_curve", "brook_pebble"},
        tags={"forest", "garden", "mist"},
    ),
    "pine_arch": Trail(
        "pine_arch",
        "Pine Arch",
        "At Pine Arch, the forest trail curved past Mira's cozy garden and a wooden sign painted with small green ferns.",
        "the morning mist hung under the pine boughs like soft gray ribbon",
        {"stone_step", "moss_turn"},
        tags={"forest", "garden", "mist"},
    ),
    "brook_loop": Trail(
        "brook_loop",
        "Brook Loop",
        "Near Brook Loop, a forest trail hummed beside Mira's cozy garden where rain barrels and stepping stones sat in neat rows.",
        "mist from the brook made the path shine silver",
        {"berry_curve", "moss_turn", "brook_pebble"},
        tags={"forest", "garden", "mist", "brook"},
    ),
}

FLOWERS = {
    "moonbell": Flower(
        "moonbell",
        "Moonbell",
        "the misty flower called Moonbell",
        "a blue clay pot",
        1,
        {"calm", "cheer"},
        "a cool honey scent",
        "pearl-white",
        tags={"flower", "sharing", "calm"},
    ),
    "dewcup": Flower(
        "dewcup",
        "Dewcup",
        "the misty flower called Dewcup",
        "a deep green pot",
        2,
        {"calm", "warmth"},
        "a warm minty scent",
        "silver-blue",
        tags={"flower", "sharing", "warmth"},
    ),
    "starlantern": Flower(
        "starlantern",
        "Star Lantern",
        "the misty flower called Star Lantern",
        "a yellow tin pot",
        1,
        {"cheer", "warmth"},
        "a bright lemon scent",
        "gold-pink",
        tags={"flower", "sharing", "cheer"},
    ),
}

BORROWERS = {
    "elio": Borrower(
        "elio",
        "Elio",
        "neighbor child",
        {"stone_step", "berry_curve"},
        {1},
        {"calm", "cheer"},
        "He had seen someone struggling and believed the flower's gentle scent would help.",
        '"I should have asked before I carried it away," Elio said.',
        tags={"kind", "quick"},
    ),
    "nora": Borrower(
        "nora",
        "Nora",
        "trail helper",
        {"stone_step", "moss_turn"},
        {1, 2},
        {"warmth", "calm"},
        "She had wanted to help first and explain later, which made the mystery bigger than the problem.",
        '"I borrowed it to help, but I made everyone worry," Nora said.',
        tags={"kind", "steady"},
    ),
    "pip": Borrower(
        "pip",
        "Pip",
        "berry picker",
        {"berry_curve", "moss_turn", "brook_pebble"},
        {1},
        {"cheer", "calm"},
        "He knew the flower made the trail feel friendlier, so he hurried without stopping to ask.",
        '"I was trying to be kind too fast," Pip said.',
        tags={"kind", "hurried"},
    ),
}

SHARE_SPOTS = {
    "map_bench": ShareSpot(
        "map_bench",
        "map bench",
        "the moss bench by the trail map",
        "stone_step",
        2,
        "calm",
        "dew_scuff",
        "Grandma Suri",
        "Grandma Suri was breathing too fast after the hill",
        "set the flower beside her so its cool mist could slow the air around her",
        "the bench looked restful again",
        tags={"bench", "calm"},
    ),
    "berry_stump": ShareSpot(
        "berry_stump",
        "berry stump",
        "the berry stump at the curve in the trail",
        "berry_curve",
        1,
        "cheer",
        "blue_pollen",
        "little Jo",
        "little Jo had gone quiet after dropping a berry basket",
        "turned the flower so the bright petals faced his downcast eyes",
        "little Jo smiled so suddenly that even the berries seemed brighter",
        tags={"berries", "cheer"},
    ),
    "lantern_stool": ShareSpot(
        "lantern_stool",
        "lantern stool",
        "the ranger stool under the pine lantern",
        "moss_turn",
        2,
        "warmth",
        "ribbon_fiber",
        "Ranger May",
        "Ranger May had cold fingers from wiping rain off the lantern glass",
        "placed the flower near her hands until the scent and lantern glow felt warm together",
        "the lantern and the petals glowed side by side like two small suns",
        tags={"lantern", "warmth"},
    ),
    "brook_rock": ShareSpot(
        "brook_rock",
        "brook rock",
        "the flat brook rock beside the water",
        "brook_pebble",
        1,
        "calm",
        "silver_sand",
        "Auntie Fen",
        "Auntie Fen was resting her sore ankle and trying not to wince",
        "placed the flower close enough for its soft mist to make the whole spot feel quieter",
        "the brook sounded softer once everyone stopped hurrying",
        tags={"brook", "calm"},
    ),
}

CLUES = {
    "dew": Clue(
        "dew",
        "dew_scuff",
        "Dew beads on the stone step",
        "Tiny wet crescents shone where a pot had rubbed the path.",
        tags={"dew"},
    ),
    "pollen": Clue(
        "pollen",
        "blue_pollen",
        "Blue pollen near the berry curve",
        "A dusting of blue pollen sat where no blue berries grew.",
        tags={"pollen"},
    ),
    "ribbon": Clue(
        "ribbon",
        "ribbon_fiber",
        "A pale ribbon fiber under the pine lantern",
        "One thin ribbon thread clung to the damp wood like a quiet arrow.",
        tags={"ribbon"},
    ),
    "sand": Clue(
        "sand",
        "silver_sand",
        "Silver sand by the brook pebbles",
        "Silvery sand sparkled on the path though the garden used dark soil.",
        tags={"sand"},
    ),
}


GARDEN_PROMPTS = [
    'Write a child-friendly whodunit set on a forest trail with the exact words "cozy garden" and "misty flower".',
    "Tell a gentle mystery where the missing thing was borrowed for sharing, not stolen for greed.",
    "Write a happy ending story where a child follows one physical clue, finds the truth, and changes the world for the better.",
]


KNOWLEDGE = {
    "sharing": [
        (
            "Why is asking part of good sharing?",
            "Good sharing means caring about another person's feelings and things. Asking first turns a helpful idea into a respectful one."
        ),
    ],
    "dew": [
        (
            "Why can dew become a clue?",
            "Dew clings to cool shoes, pots, and stones. If something wet moves along a path, it can leave a shining trail behind."
        ),
    ],
    "pollen": [
        (
            "Why does pollen help a detective in a garden mystery?",
            "Pollen can stick to hands, shoes, or flower pots. When it shows up in the wrong place, it points to where a flower has been."
        ),
    ],
    "ribbon": [
        (
            "How can a ribbon fiber become evidence?",
            "A loose fiber can catch on wood or bark when someone passes by. Matching it to a spot helps show which path was used."
        ),
    ],
    "sand": [
        (
            "What can sand show on a trail?",
            "Sand moves easily and does not stay on every path. If it appears far from the brook, someone or something probably carried it there."
        ),
    ],
    "bench": [
        (
            "Why might a bench matter in a story?",
            "A bench gives a tired person a place to rest. In a small mystery, that can explain why someone carried comfort to that spot."
        ),
    ],
    "brook": [
        (
            "Why do stories put calm scenes near a brook?",
            "Running water has a soft repeating sound. Writers often use that sound to make a place feel quieter and gentler."
        ),
    ],
    "lantern": [
        (
            "Why does a lantern make a strong ending image?",
            "A lantern gives visible light, so readers can picture the scene clearly. It also suggests safety after worry."
        ),
    ],
}


@dataclass
class StoryParams:
    trail: str
    flower: str
    borrower: str
    share_spot: str
    clue: str
    seed: Optional[int] = None


def flower_helps_need(flower: Flower, need: str) -> bool:
    return need in flower.gifts


def borrower_supports_need(borrower: Borrower, need: str) -> bool:
    return need in borrower.shares_for


def combo_is_valid(
    trail: Trail,
    flower: Flower,
    borrower: Borrower,
    spot: ShareSpot,
    clue: Clue,
) -> bool:
    return (
        spot.path in trail.paths
        and spot.path in borrower.route
        and flower.size <= spot.capacity
        and flower.size in borrower.carries
        and flower_helps_need(flower, spot.need)
        and borrower_supports_need(borrower, spot.need)
        and spot.trace == clue.trace
    )


def explain_rejection(
    trail: Trail,
    flower: Flower,
    borrower: Borrower,
    spot: ShareSpot,
    clue: Clue,
) -> str:
    if spot.path not in trail.paths:
        return f"(No story: {trail.name} does not reach {spot.where}.)"
    if spot.path not in borrower.route:
        return f"(No story: {borrower.label} does not travel the path to {spot.where}.)"
    if flower.size > spot.capacity:
        return f"(No story: {flower.phrase} is too large for {spot.where}.)"
    if flower.size not in borrower.carries:
        return f"(No story: {borrower.label} cannot plausibly carry {flower.phrase} in {flower.pot}.)"
    if not flower_helps_need(flower, spot.need):
        return f"(No story: {flower.label} is not the right kind of misty flower to help at {spot.where}.)"
    if not borrower_supports_need(borrower, spot.need):
        return f"(No story: {borrower.label} would not choose that kind of sharing stop.)"
    if spot.trace != clue.trace:
        return f"(No story: the clue points to {clue.trace.replace('_', ' ')}, but {spot.where} leaves {spot.trace.replace('_', ' ')}.)"
    return "(No story: the clue, path, and sharing turn do not line up.)"


def all_params() -> list[StoryParams]:
    combos: list[StoryParams] = []
    for trail_id, trail in TRAILS.items():
        for flower_id, flower in FLOWERS.items():
            for borrower_id, borrower in BORROWERS.items():
                for spot_id, spot in SHARE_SPOTS.items():
                    for clue_id, clue in CLUES.items():
                        if combo_is_valid(trail, flower, borrower, spot, clue):
                            combos.append(StoryParams(trail_id, flower_id, borrower_id, spot_id, clue_id))
    return combos


def matching_params(args: argparse.Namespace) -> list[StoryParams]:
    return [
        p for p in all_params()
        if (args.trail is None or p.trail == args.trail)
        and (args.flower is None or p.flower == args.flower)
        and (args.borrower is None or p.borrower == args.borrower)
        and (args.share_spot is None or p.share_spot == args.share_spot)
        and (args.clue is None or p.clue == args.clue)
    ]


def need_sentence(need: str) -> str:
    return {
        "calm": "The misty flower made the place feel slower and easier to breathe in.",
        "cheer": "The misty flower did what bright things do best: it gave a sad face a reason to lift.",
        "warmth": "The misty flower and the lantern together made the damp air feel warmer.",
    }[need]


def sentence_case(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def make_world(params: StoryParams) -> StoryWorld:
    trail = TRAILS[params.trail]
    flower = FLOWERS[params.flower]
    borrower = BORROWERS[params.borrower]
    spot = SHARE_SPOTS[params.share_spot]
    clue = CLUES[params.clue]

    world = StoryWorld(params)
    world.add(Entity("hero", "Mira", "person", "child detective", ["careful"], memes={"curiosity": 2, "kindness": 2}))
    world.add(Entity("helper", "Rowan", "person", "friend", ["loyal"], memes={"trust": 1}))
    world.add(Entity("trail", trail.name, "place", "forest trail", attrs={"paths": set(trail.paths)}))
    world.add(Entity("garden", "the cozy garden", "place", "garden", meters={"flowers": 1}))
    world.add(Entity("flower", flower.phrase, "thing", "misty flower", meters={"home": 1}, attrs={"pot": flower.pot, "size": flower.size}))
    world.add(Entity("borrower", borrower.label, "person", borrower.role, memes={"generosity": 1}))
    world.add(Entity("spot", spot.where, "place", "sharing spot", attrs={"need": spot.need, "path": spot.path}))
    world.add(Entity("recipient", spot.recipient, "person", "trail walker", meters={"comfort": 0}))
    world.add(Entity("clue", clue.whisper, "thing", "clue", attrs={"trace": clue.trace}))

    world.facts.update(
        trail=trail,
        flower=flower,
        borrower=borrower,
        share_spot=spot,
        clue=clue,
        solved=False,
        shared_openly=False,
        happy_ending=False,
    )
    return world


def introduce(world: StoryWorld) -> None:
    trail: Trail = world.facts["trail"]
    flower: Flower = world.facts["flower"]
    hero = world.get("hero")
    world.record(
        "intro",
        "hero",
        "garden",
        f"{trail.opening} {trail.mist_detail.capitalize()}, and {hero.label} liked to check first on {flower.phrase} resting in {flower.pot}.",
    )
    world.record(
        "premise",
        "hero",
        "garden",
        f"People walking the forest trail often paused there because the cozy garden felt safe and the misty flower carried {flower.scent}.",
    )


def discover_missing_flower(world: StoryWorld) -> None:
    flower = world.get("flower")
    hero = world.get("hero")
    helper = world.get("helper")
    flower.meters["home"] = 0
    flower.meters["missing"] = 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 2
    world.get("garden").meters["worry"] = 1
    world.para()
    world.record(
        "missing",
        "hero",
        "garden",
        f"That afternoon the pot was gone, leaving only a round damp mark on the stone. \"Who took the misty flower?\" {helper.label} asked, and the cozy garden suddenly felt too still.",
        target="flower",
    )


def read_clue(world: StoryWorld) -> None:
    clue: Clue = world.facts["clue"]
    hero = world.get("hero")
    world.get("clue").meters["noticed"] = 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.record(
        "clue",
        "hero",
        "garden",
        f"{hero.label} knelt by the empty stand and found the first clue: {clue.whisper.lower()}. {clue.sensory}",
        target="clue",
    )
    world.record(
        "reason",
        "hero",
        "garden",
        f"This felt like a small whodunit, but {hero.label} did not want a mean answer. She wanted the true one.",
    )


def follow_trail(world: StoryWorld) -> None:
    trail: Trail = world.facts["trail"]
    flower: Flower = world.facts["flower"]
    borrower: Borrower = world.facts["borrower"]
    spot: ShareSpot = world.facts["share_spot"]
    hero = world.get("hero")
    world.para()
    hero.memes["patience"] = hero.memes.get("patience", 0) + 1
    world.get("trail").meters["searched"] = world.get("trail").meters.get("searched", 0) + 1
    world.record(
        "follow",
        "hero",
        "trail",
        f"{hero.label} and Rowan followed the clue along the forest trail toward {spot.where}. She thought about the facts: only someone who could carry {flower.pot} and wanted to help on purpose would choose that path.",
    )
    world.record(
        "suspect-frame",
        "hero",
        "trail",
        f"That is why she looked for {borrower.label} as a possible borrower, not as a villain. A kind mystery still needed careful checking.",
    )


def reveal_sharing(world: StoryWorld) -> None:
    borrower: Borrower = world.facts["borrower"]
    spot: ShareSpot = world.facts["share_spot"]
    hero = world.get("hero")
    recipient = world.get("recipient")
    flower = world.get("flower")
    borrower_ent = world.get("borrower")
    flower.meters["missing"] = 0
    flower.meters["shared"] = 1
    borrower_ent.memes["guilt"] = borrower_ent.memes.get("guilt", 0) + 1
    borrower_ent.memes["generosity"] = borrower_ent.memes.get("generosity", 0) + 1
    recipient.meters["comfort"] = 1
    world.record(
        "reveal",
        "hero",
        "spot",
        f"At {spot.where}, {borrower.label} was with {spot.recipient}. {sentence_case(spot.recipient_state)}, so {borrower.label} had {spot.share_action}. {need_sentence(spot.need)}",
        target="borrower",
    )
    world.record(
        "truth",
        "borrower",
        "spot",
        f"{borrower.apology} {borrower.motive}",
        target="hero",
    )
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1


def resolve_open_sharing(world: StoryWorld) -> None:
    flower: Flower = world.facts["flower"]
    spot: ShareSpot = world.facts["share_spot"]
    hero = world.get("hero")
    flower_ent = world.get("flower")
    borrower_ent = world.get("borrower")
    world.para()
    world.facts["solved"] = True
    world.facts["shared_openly"] = True
    world.facts["happy_ending"] = True
    flower_ent.meters["home"] = 1
    flower_ent.meters["shared_openly"] = 1
    borrower_ent.memes["trust"] = borrower_ent.memes.get("trust", 0) + 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    world.record(
        "resolution",
        "hero",
        "garden",
        f"{hero.label} said that helping was lovely, but borrowing still needed asking first. Together they carried the pot back to the cozy garden and tied on a little tag that said, \"Ask, then share.\"",
        target="flower",
    )
    world.record(
        "ending",
        "hero",
        "garden",
        f"By sunset, {flower.ending_color} petals shone beside the path, {spot.ending_image}, and nobody on the forest trail wondered where the misty flower belonged anymore.",
        target="trail",
    )


def tell(params: StoryParams) -> StoryWorld:
    world = make_world(params)
    introduce(world)
    discover_missing_flower(world)
    read_clue(world)
    follow_trail(world)
    reveal_sharing(world)
    resolve_open_sharing(world)
    return world


def generation_prompts(world: StoryWorld) -> list[str]:
    trail: Trail = world.facts["trail"]
    flower: Flower = world.facts["flower"]
    borrower: Borrower = world.facts["borrower"]
    spot: ShareSpot = world.facts["share_spot"]
    return [
        GARDEN_PROMPTS[0],
        f"Tell a whodunit for young readers where {flower.phrase} disappears from a cozy garden by {trail.name} and the answer turns out to be sharing.",
        f"Write a happy ending mystery in which {borrower.label} borrows a flower to help {spot.recipient} at {spot.where}, and the detective solves it without being cruel.",
    ]


def story_qa(world: StoryWorld) -> list[tuple[str, str]]:
    trail: Trail = world.facts["trail"]
    flower: Flower = world.facts["flower"]
    borrower: Borrower = world.facts["borrower"]
    spot: ShareSpot = world.facts["share_spot"]
    clue: Clue = world.facts["clue"]
    hero = world.get("hero")
    return [
        (
            "Who solved the mystery on the forest trail?",
            f"{hero.label} solved it. She followed the clue from the cozy garden and checked the path before blaming anyone."
        ),
        (
            "What was missing from the cozy garden?",
            f"The missing thing was {flower.phrase} in {flower.pot}. Its empty damp ring is what turned the afternoon into a little whodunit."
        ),
        (
            "What clue showed Mira where to look?",
            f"The key clue was \"{clue.whisper}.\" That trace matched the path to {spot.where}, so it gave her a grounded next step instead of a guess."
        ),
        (
            "Who had moved the flower, and why?",
            f"{borrower.label} had moved it. {borrower.motive} That is why the flower ended up beside {spot.recipient} instead of staying in the garden."
        ),
        (
            "How did sharing change the ending?",
            f"The mystery ended happily because everyone agreed the flower could be shared only in the open and only after asking first. The flower returned to the cozy garden, but it still remained part of the kindness on the forest trail."
        ),
        (
            "Why was the answer kinder than it first seemed?",
            f"It looked like someone had simply taken the flower. Once Mira reached {spot.where}, she learned the borrowing came from a wish to help, so the problem was secrecy rather than meanness."
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[tuple[str, str]]:
    trail: Trail = world.facts["trail"]
    flower: Flower = world.facts["flower"]
    spot: ShareSpot = world.facts["share_spot"]
    clue: Clue = world.facts["clue"]
    tags = set(trail.tags) | set(flower.tags) | set(spot.tags) | set(clue.tags) | {"sharing"}
    ordered = ["sharing", "dew", "pollen", "ribbon", "sand", "bench", "brook", "lantern"]
    out: list[tuple[str, str]] = []
    for tag in ordered:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{idx}. {prompt}" for idx, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story-grounded QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world trace ---"]
    for event in world.history:
        target = f" -> {event.target}" if event.target else ""
        lines.append(f"{event.id:10} {event.actor}{target} @ {event.place}: {event.text}")
    lines.append("--- entity state ---")
    for entity in world.entities.values():
        bits = []
        if entity.meters:
            bits.append(f"meters={entity.meters}")
        if entity.memes:
            bits.append(f"memes={entity.memes}")
        if entity.attrs:
            bits.append(f"attrs={entity.attrs}")
        lines.append(f"{entity.id:10} ({entity.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
reachable(T,S) :- trail_path(T,P), share_spot_path(S,P).
borrower_can_reach(B,S) :- borrower_path(B,P), share_spot_path(S,P).
fits(F,S) :- flower_size(F,FS), share_spot_capacity(S,SC), FS <= SC.
can_carry(B,F) :- borrower_carries(B,Size), flower_size(F,Size).
flower_helps(F,S) :- flower_gift(F,G), share_spot_need(S,G).
borrower_supports(B,S) :- borrower_shares_for(B,G), share_spot_need(S,G).
trace_matches(S,C) :- share_spot_trace(S,T), clue_trace(C,T).
valid(T,F,B,S,C) :- trail(T), flower(F), borrower(B), share_spot(S), clue(C),
                    reachable(T,S), borrower_can_reach(B,S), fits(F,S),
                    can_carry(B,F), flower_helps(F,S), borrower_supports(B,S),
                    trace_matches(S,C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for trail_id, trail in TRAILS.items():
        lines.append(asp.fact("trail", trail_id))
        for path in sorted(trail.paths):
            lines.append(asp.fact("trail_path", trail_id, path))
    for flower_id, flower in FLOWERS.items():
        lines.append(asp.fact("flower", flower_id))
        lines.append(asp.fact("flower_size", flower_id, flower.size))
        for gift in sorted(flower.gifts):
            lines.append(asp.fact("flower_gift", flower_id, gift))
    for borrower_id, borrower in BORROWERS.items():
        lines.append(asp.fact("borrower", borrower_id))
        for path in sorted(borrower.route):
            lines.append(asp.fact("borrower_path", borrower_id, path))
        for size in sorted(borrower.carries):
            lines.append(asp.fact("borrower_carries", borrower_id, size))
        for need in sorted(borrower.shares_for):
            lines.append(asp.fact("borrower_shares_for", borrower_id, need))
    for spot_id, spot in SHARE_SPOTS.items():
        lines.append(asp.fact("share_spot", spot_id))
        lines.append(asp.fact("share_spot_path", spot_id, spot.path))
        lines.append(asp.fact("share_spot_capacity", spot_id, spot.capacity))
        lines.append(asp.fact("share_spot_need", spot_id, spot.need))
        lines.append(asp.fact("share_spot_trace", spot_id, spot.trace))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_trace", clue_id, clue.trace))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def verify_sample(sample: StorySample) -> None:
    world = sample.world
    if world is None:
        raise AssertionError("sample world is missing")
    story_lower = sample.story.lower()
    if "cozy garden" not in story_lower:
        raise AssertionError("story is missing 'cozy garden'")
    if "misty flower" not in story_lower:
        raise AssertionError("story is missing 'misty flower'")
    if "forest trail" not in story_lower:
        raise AssertionError("story is missing 'forest trail'")
    if sample.story.count("\n\n") < 3:
        raise AssertionError("story should have at least four paragraphs")
    if not world.facts.get("solved") or not world.facts.get("happy_ending"):
        raise AssertionError("story world did not reach a solved happy ending")
    if world.get("flower").meters.get("shared_openly", 0) < 1:
        raise AssertionError("flower never reached open sharing state")
    if world.get("recipient").meters.get("comfort", 0) < 1:
        raise AssertionError("recipient was not helped")
    if len(sample.prompts) != 3:
        raise AssertionError("expected exactly three generation prompts")
    if len(sample.story_qa) < 5 or len(sample.world_qa) < 2:
        raise AssertionError("QA sets are too thin")
    if "{" in sample.story or "}" in sample.story:
        raise AssertionError("story leaked unresolved formatting")
    for item in list(sample.story_qa) + list(sample.world_qa):
        if len(item.answer.split()) < 8:
            raise AssertionError(f"answer is too short: {item.question}")


def asp_verify() -> int:
    py = sorted((p.trail, p.flower, p.borrower, p.share_spot, p.clue) for p in all_params())
    lp = sorted(asp_valid_combos())
    if py != lp:
        print("MISMATCH between Python and ASP gates:")
        only_py = sorted(set(py) - set(lp))
        only_lp = sorted(set(lp) - set(py))
        if only_py:
            print("  only in Python:", only_py)
        if only_lp:
            print("  only in ASP:", only_lp)
        return 1
    print(f"OK: ASP parity matches Python gate ({len(py)} valid combinations).")
    for params in all_params():
        verify_sample(generate(params))
    print(f"OK: generated stories and QA passed for all {len(py)} valid combinations.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A cozy-garden forest-trail whodunit where the answer becomes sharing."
    )
    parser.add_argument("--trail", choices=sorted(TRAILS))
    parser.add_argument("--flower", choices=sorted(FLOWERS))
    parser.add_argument("--borrower", choices=sorted(BORROWERS))
    parser.add_argument("--share-spot", choices=sorted(SHARE_SPOTS))
    parser.add_argument("--clue", choices=sorted(CLUES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if all(getattr(args, name) is not None for name in ("trail", "flower", "borrower", "share_spot", "clue")):
        trail = TRAILS[args.trail]
        flower = FLOWERS[args.flower]
        borrower = BORROWERS[args.borrower]
        spot = SHARE_SPOTS[args.share_spot]
        clue = CLUES[args.clue]
        if not combo_is_valid(trail, flower, borrower, spot, clue):
            raise StoryError(explain_rejection(trail, flower, borrower, spot, clue))

    combos = matching_params(args)
    if not combos:
        raise StoryError("(No valid cozy-garden mystery matches the given options.)")
    chosen = StoryParams(**vars(rng.choice(combos)))
    return chosen


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid cozy-garden mysteries:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:14}" for part in combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        selected = matching_params(args)
        if not selected:
            print("(No valid cozy-garden mystery matches the given options.)")
            return
        samples = [generate(p) for p in selected]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(100, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.trail} / {p.flower} / {p.borrower} / {p.share_spot} / {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
