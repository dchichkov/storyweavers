#!/usr/bin/env python3
"""
storyworlds/worlds/cozy_garden_misty_flower_forest_trail_sharing_2.py
========================================================================

Seed prompt
-----------
Write a story that includes the following words and narrative instruments.
Words: cozy garden, misty flower
Setting: forest trail
Features: Sharing, Happy Ending
Style: Whodunit

Internal source tale
--------------------
Iris keeps a cozy garden beside a forest trail, and the garden's favorite
misty flower vanishes one damp morning. The empty ring on the stone stand makes
the case feel like a tiny whodunit, but Iris refuses to accuse the wrong child.
Instead she follows a clue through the mist.

The trail leads to a resting place where another child has borrowed the flower
to comfort someone tired, cold, or sad. Iris still insists that sharing needs
asking first. By the end, the flower is not hidden anymore: the children make
an open sharing plan, carry the flower home together, and the garden becomes
warmer because the truth was kindness instead of theft.
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
    label: str
    opening: str
    mist_line: str
    paths: set[str]
    ending_touch: str


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


@dataclass(frozen=True)
class Borrower:
    id: str
    label: str
    role: str
    routes: set[str]
    carries: set[int]
    shares_for: set[str]
    motive: str
    confession: str


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
    use_line: str
    ending_image: str


@dataclass(frozen=True)
class Clue:
    id: str
    label: str
    trace: str
    observation: str
    hunch: str


@dataclass
class Entity:
    id: str
    label: str
    kind: str
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
    "fern_turn": Trail(
        id="fern_turn",
        label="Fern Turn",
        opening="At Fern Turn, Iris kept a cozy garden beside the forest trail, with flat stones around each bed and a low gate that never quite shut.",
        mist_line="The morning mist drifted low enough to kiss the leaves and soften every footprint.",
        paths={"stone_steps", "moss_curve"},
        ending_touch="Even the ferns seemed to lean closer once the mystery ended kindly.",
    ),
    "lantern_bend": Trail(
        id="lantern_bend",
        label="Lantern Bend",
        opening="At Lantern Bend, a forest trail curled past Iris's cozy garden and a post where a rain lantern swung without hurry.",
        mist_line="Misty air hung under the branches like a pale curtain that turned every clue into a secret.",
        paths={"moss_curve", "lantern_stile"},
        ending_touch="The little lantern looked less lonely after the children chose honesty.",
    ),
    "brook_meander": Trail(
        id="brook_meander",
        label="Brook Meander",
        opening="Near Brook Meander, Iris tended a cozy garden beside the forest trail where stepping stones pointed toward the water.",
        mist_line="Mist from the brook made the trail shine as if someone had brushed it with silver milk.",
        paths={"stone_steps", "brook_turn", "lantern_stile"},
        ending_touch="The brook kept talking softly, but now it sounded like a happy secret instead of a worried one.",
    ),
}


FLOWERS = {
    "mooncup": Flower(
        id="mooncup",
        label="Mooncup",
        phrase="the misty flower called Mooncup",
        pot="a blue clay pot",
        size=1,
        gifts={"calm", "cheer"},
        scent="a cool pear scent",
        ending_color="pearl-white",
    ),
    "silverbell": Flower(
        id="silverbell",
        label="Silverbell",
        phrase="the misty flower called Silverbell",
        pot="a green basket pot",
        size=2,
        gifts={"calm", "warmth"},
        scent="a mint-and-rain scent",
        ending_color="silver-blue",
    ),
    "glowpetal": Flower(
        id="glowpetal",
        label="Glowpetal",
        phrase="the misty flower called Glowpetal",
        pot="a yellow tin pot",
        size=1,
        gifts={"cheer", "warmth"},
        scent="a lemon-honey scent",
        ending_color="gold-pink",
    ),
}


BORROWERS = {
    "tavi": Borrower(
        id="tavi",
        label="Tavi",
        role="a berry-picker with quick feet",
        routes={"stone_steps", "moss_curve"},
        carries={1},
        shares_for={"calm", "cheer"},
        motive="Tavi had seen someone droop and decided to help first and explain later.",
        confession='"I wanted to share comfort, but I should have asked before I borrowed it," Tavi admitted.',
    ),
    "nella": Borrower(
        id="nella",
        label="Nella",
        role="the trail helper who notices cold hands and tired faces",
        routes={"moss_curve", "lantern_stile"},
        carries={1, 2},
        shares_for={"warmth", "calm"},
        motive="Nella believed a gentle flower could do more good on the path than hidden safely at home.",
        confession='"I was trying to be useful, not sneaky, but useful things still need permission," Nella said.',
    ),
    "bram": Borrower(
        id="bram",
        label="Bram",
        role="a map-carrying cousin who hates seeing anyone left out",
        routes={"stone_steps", "brook_turn"},
        carries={1},
        shares_for={"cheer", "warmth", "calm"},
        motive="Bram could not bear a lonely face and rushed away with the flower before stopping to think.",
        confession='"I solved the wrong problem first," Bram said. "I helped, but I skipped the asking part."',
    ),
}


SHARE_SPOTS = {
    "story_stump": ShareSpot(
        id="story_stump",
        label="story stump",
        where="the story stump just past the stone steps",
        path="stone_steps",
        capacity=1,
        need="cheer",
        trace="dew_arc",
        recipient="Little Oona",
        recipient_state="Little Oona had gone quiet after her paper bird tore in the damp air",
        use_line="The flower sat by her knees while its bright petals gave her something lovely to look at.",
        ending_image="Oona tucked a new paper bird beside the pot before everyone walked home.",
    ),
    "moss_bench": ShareSpot(
        id="moss_bench",
        label="moss bench",
        where="the moss bench by the trail map",
        path="moss_curve",
        capacity=2,
        need="calm",
        trace="pollen_dust",
        recipient="Grandma Bex",
        recipient_state="Grandma Bex was breathing too fast after the uphill part of the trail",
        use_line="The flower rested near her hands, and its cool mist made the whole bench feel slower and easier to breathe around.",
        ending_image="By the time they left, Grandma Bex was smiling at the map again instead of staring at the ground.",
    ),
    "lantern_stile": ShareSpot(
        id="lantern_stile",
        label="lantern stile",
        where="the little stile below the rain lantern",
        path="lantern_stile",
        capacity=2,
        need="warmth",
        trace="ribbon_thread",
        recipient="Ranger Sol",
        recipient_state="Ranger Sol had cold fingers from wiping rain off the lantern glass",
        use_line="The flower stood near the lantern post so scent and lamplight could warm the same patch of air together.",
        ending_image="The lantern and the petals glowed side by side like two friendly suns.",
    ),
    "brook_rock": ShareSpot(
        id="brook_rock",
        label="brook rock",
        where="the flat rock beside the brook",
        path="brook_turn",
        capacity=1,
        need="calm",
        trace="silver_sand",
        recipient="Cousin Rue",
        recipient_state="Cousin Rue was holding a sore ankle very still and trying not to wince",
        use_line="The flower's soft mist quieted the air enough that Rue finally stopped pretending everything was fine.",
        ending_image="The brook sounded gentler once nobody had to hide their worry anymore.",
    ),
}


CLUES = {
    "dew": Clue(
        id="dew",
        label="dew crescents",
        trace="dew_arc",
        observation="On the stand and the first stone, Iris found tiny wet crescents where a pot had bumped the path.",
        hunch="Those marks curved toward the stone steps, as if the missing flower had hurried to comfort someone small.",
    ),
    "pollen": Clue(
        id="pollen",
        label="blue pollen dust",
        trace="pollen_dust",
        observation="A light blue dusting glittered on the garden gate even though the vegetables there had no blue bloom at all.",
        hunch="That kind of pollen drifted from the moss curve, where people often stopped to catch their breath.",
    ),
    "ribbon": Clue(
        id="ribbon",
        label="ribbon thread",
        trace="ribbon_thread",
        observation="One pale ribbon fiber clung to the gate latch like a quiet finger pointing away from the beds.",
        hunch="The thread matched the ribbon tied under the rain lantern down the trail.",
    ),
    "sand": Clue(
        id="sand",
        label="silver sand",
        trace="silver_sand",
        observation="Silvery sand sparkled on the dark soil, and no one in the cozy garden used sand like that.",
        hunch="Only the brook turn wore that color, which meant the mystery had walked toward the water.",
    ),
}


PROMPT_TEMPLATES = [
    'Write a child-friendly whodunit set on a forest trail that uses the exact words "cozy garden" and "misty flower".',
    "Tell a gentle mystery where the missing thing was borrowed for sharing, not taken for greed.",
    "End with a concrete happy image that proves the world changed after the truth came out.",
]


WORLD_KNOWLEDGE = {
    "sharing": (
        "Why does asking matter when people want to share something helpful?",
        "Asking shows respect for the person who cares for the item. A kind idea becomes true sharing when everyone knows what is happening and agrees."
    ),
    "trail": (
        "Why do clues work well on a misty forest trail?",
        "Mist and damp ground hold marks that would disappear on a dry road. Little traces like sand, pollen, or wet arcs can stay in place long enough to be noticed."
    ),
    "whodunit": (
        "What makes a whodunit feel gentle instead of scary for children?",
        "A gentle whodunit uses curiosity more than danger. The puzzle matters, but the answer leads to understanding instead of punishment."
    ),
}


@dataclass
class StoryParams:
    trail: str
    flower: str
    borrower: str
    share_spot: str
    clue: str
    seed: Optional[int] = None


ASP_RULES = """
valid(Trail, Flower, Borrower, Spot, Clue) :-
    trail(Trail),
    flower(Flower),
    borrower(Borrower),
    share_spot(Spot),
    clue(Clue),
    trail_path(Trail, Path),
    share_spot_path(Spot, Path),
    borrower_path(Borrower, Path),
    flower_size(Flower, Size),
    borrower_carries(Borrower, Size),
    share_spot_capacity(Spot, Capacity),
    Size <= Capacity,
    share_spot_need(Spot, Need),
    flower_gift(Flower, Need),
    borrower_shares_for(Borrower, Need),
    share_spot_trace(Spot, Trace),
    clue_trace(Clue, Trace).
"""


def combo_is_valid(
    trail: Trail,
    flower: Flower,
    borrower: Borrower,
    spot: ShareSpot,
    clue: Clue,
) -> bool:
    return (
        spot.path in trail.paths
        and spot.path in borrower.routes
        and flower.size in borrower.carries
        and flower.size <= spot.capacity
        and spot.need in flower.gifts
        and spot.need in borrower.shares_for
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
        return f"(No story: {trail.label} does not reach {spot.where}.)"
    if spot.path not in borrower.routes:
        return f"(No story: {borrower.label} does not use the path to {spot.where}.)"
    if flower.size not in borrower.carries:
        return f"(No story: {borrower.label} cannot plausibly carry {flower.phrase} in {flower.pot}.)"
    if flower.size > spot.capacity:
        return f"(No story: {flower.phrase} is too large for {spot.where}.)"
    if spot.need not in flower.gifts:
        return f"(No story: {flower.label} does not fit the need at {spot.where}.)"
    if spot.need not in borrower.shares_for:
        return f"(No story: {borrower.label} would not choose that kind of sharing stop.)"
    if spot.trace != clue.trace:
        return f"(No story: the clue points to {clue.trace.replace('_', ' ')}, but {spot.where} leaves {spot.trace.replace('_', ' ')}.)"
    return "(No story: the clue, path, and sharing turn do not line up.)"


def all_params() -> list[StoryParams]:
    out: list[StoryParams] = []
    for trail_id, trail in TRAILS.items():
        for flower_id, flower in FLOWERS.items():
            for borrower_id, borrower in BORROWERS.items():
                for spot_id, spot in SHARE_SPOTS.items():
                    for clue_id, clue in CLUES.items():
                        if combo_is_valid(trail, flower, borrower, spot, clue):
                            out.append(StoryParams(trail_id, flower_id, borrower_id, spot_id, clue_id))
    return out


def matching_params(args: argparse.Namespace) -> list[StoryParams]:
    return [
        params for params in all_params()
        if (args.trail is None or params.trail == args.trail)
        and (args.flower is None or params.flower == args.flower)
        and (args.borrower is None or params.borrower == args.borrower)
        and (args.share_spot is None or params.share_spot == args.share_spot)
        and (args.clue is None or params.clue == args.clue)
    ]


def need_sentence(need: str) -> str:
    return {
        "calm": "The air around the flower seemed to remember how to slow down.",
        "cheer": "Its bright petals gave a drooping face one good reason to lift again.",
        "warmth": "Its color and scent made the wet little resting place feel warmer than it had a minute before.",
    }[need]


def make_world(params: StoryParams) -> StoryWorld:
    trail = TRAILS[params.trail]
    flower = FLOWERS[params.flower]
    borrower = BORROWERS[params.borrower]
    spot = SHARE_SPOTS[params.share_spot]
    clue = CLUES[params.clue]

    world = StoryWorld(params=params)
    world.add(Entity("hero", "Iris", "child", memes={"care": 2, "curiosity": 2}))
    world.add(Entity("helper", "Jun", "child", memes={"trust": 2, "fairness": 1}))
    world.add(Entity("borrower", borrower.label, "child", memes={"kindness": 2, "guilt": 0}, attrs={"role": borrower.role}))
    world.add(Entity("recipient", spot.recipient, "person", meters={"comfort": 0}, attrs={"state": spot.recipient_state}))
    world.add(Entity("trail", trail.label, "place", attrs={"paths": set(trail.paths)}))
    world.add(Entity("garden", "the cozy garden", "place", meters={"flowers": 1}))
    world.add(Entity("flower", flower.phrase, "flower", meters={"home": 1, "borrowed": 0, "shared_openly": 0}, memes={"comfort": 2}, attrs={"pot": flower.pot, "scent": flower.scent}))
    world.add(Entity("spot", spot.where, "place", attrs={"need": spot.need, "trace": spot.trace}))
    world.add(Entity("clue", clue.label, "clue", attrs={"trace": clue.trace}))
    world.facts.update(
        {
            "trail_id": trail.id,
            "flower_id": flower.id,
            "borrower_id": borrower.id,
            "spot_id": spot.id,
            "clue_id": clue.id,
            "solved": False,
            "happy_ending": False,
            "shared_plan": False,
        }
    )
    return world


def tell(params: StoryParams) -> StoryWorld:
    trail = TRAILS[params.trail]
    flower = FLOWERS[params.flower]
    borrower = BORROWERS[params.borrower]
    spot = SHARE_SPOTS[params.share_spot]
    clue = CLUES[params.clue]
    world = make_world(params)

    hero = world.get("hero")
    helper = world.get("helper")
    borrower_ent = world.get("borrower")
    recipient = world.get("recipient")
    flower_ent = world.get("flower")

    world.record(
        "opening",
        hero.id,
        trail.id,
        f"{trail.opening} On the nicest stand in the middle bed grew {flower.phrase} in {flower.pot}.",
    )
    world.record(
        "mist",
        hero.id,
        trail.id,
        f"{trail.mist_line} Iris loved that flower most because it gave off {flower.scent} whenever the path felt tired.",
    )
    world.para()

    flower_ent.meters["home"] = 0
    flower_ent.meters["borrowed"] = 1
    hero.memes["alarm"] = hero.memes.get("alarm", 0) + 1
    world.record(
        "missing",
        hero.id,
        "garden",
        f"But after breakfast the stand was empty. The missing misty flower made Iris feel as if her cozy garden had turned into a very small whodunit.",
        target="flower",
    )
    world.record(
        "clue_found",
        hero.id,
        "garden",
        f"{clue.observation} Iris knelt beside it instead of shouting a name.",
        target="clue",
    )
    world.record(
        "helper_joins",
        helper.id,
        "garden",
        f'Jun whispered, "Then let the clue speak first." {clue.hunch}',
        target="clue",
    )
    world.para()

    hero.memes["certainty"] = hero.memes.get("certainty", 0) + 1
    world.record(
        "investigate",
        hero.id,
        spot.id,
        f"They followed the clue along the forest trail until they reached {spot.where}. Iris kept wondering who had taken the flower, but she also wondered who needed it badly enough to borrow it in secret.",
        target="spot",
    )
    borrower_ent.memes["guilt"] = borrower_ent.memes.get("guilt", 0) + 1
    recipient.meters["comfort"] = 1
    world.record(
        "discovery",
        hero.id,
        spot.id,
        f"There they found {borrower.label} with {spot.recipient}. {spot.recipient_state}. {spot.use_line}",
        target="borrower",
    )
    world.record(
        "turn",
        borrower_ent.id,
        spot.id,
        f"{borrower.motive} {need_sentence(spot.need)}",
        target="recipient",
    )
    world.para()

    hero.memes["alarm"] = max(0, hero.memes.get("alarm", 0) - 1)
    hero.memes["relief"] = hero.memes.get("relief", 0) + 2
    borrower_ent.memes["honesty"] = borrower_ent.memes.get("honesty", 0) + 1
    world.record(
        "confession",
        borrower_ent.id,
        spot.id,
        borrower.confession,
        target="hero",
    )
    world.record(
        "boundary",
        hero.id,
        spot.id,
        f'Iris nodded because the truth was kind, but she still said, "Sharing means asking first, so nobody has to solve a mystery before lunch."',
        target="borrower",
    )
    flower_ent.meters["borrowed"] = 0
    flower_ent.meters["shared_openly"] = 1
    flower_ent.meters["home"] = 1
    world.facts["solved"] = True
    world.facts["shared_plan"] = True
    world.record(
        "resolution",
        helper.id,
        "garden",
        f"Together they carried the pot back to the garden and set out a small wooden card: Ask, carry, comfort, return. After that, anyone on the trail could borrow the flower openly when help was truly needed.",
        target="flower",
    )
    world.record(
        "ending",
        hero.id,
        "garden",
        f"{spot.ending_image} Back in the cozy garden, {flower.ending_color} petals held the last mist of the day. {trail.ending_touch}",
        target="flower",
    )
    world.facts["happy_ending"] = True
    return world


def generation_prompts(world: StoryWorld) -> list[str]:
    borrower = BORROWERS[world.params.borrower]
    spot = SHARE_SPOTS[world.params.share_spot]
    clue = CLUES[world.params.clue]
    return [
        PROMPT_TEMPLATES[0],
        f"Center the mystery on {clue.label} and lead the children to {spot.where}.",
        f"Reveal that {borrower.label} borrowed the flower for sharing because {spot.recipient} needed {spot.need}.",
    ]


def story_qa(world: StoryWorld) -> list[tuple[str, str]]:
    borrower = BORROWERS[world.params.borrower]
    spot = SHARE_SPOTS[world.params.share_spot]
    clue = CLUES[world.params.clue]
    flower = FLOWERS[world.params.flower]
    return [
        (
            "Who borrowed the misty flower, and why did that child take it?",
            f"{borrower.label} borrowed the flower. {borrower.motive} That choice made the case look sneaky at first, even though the reason was to help."
        ),
        (
            "What clue told Iris where to look on the forest trail?",
            f"The clue was {clue.label}. {clue.observation} Because Iris read that trace carefully, she knew which part of the trail to follow."
        ),
        (
            f"Where did Iris find {flower.label}, and who was being helped there?",
            f"Iris found the flower at {spot.where}. {spot.recipient_state}, so the flower had been carried there to give comfort instead of being hidden away."
        ),
        (
            "Why did the mystery stop feeling like a theft by the end?",
            f"The children discovered that the flower had been borrowed for sharing, not taken for greed. Once the truth came out, Iris could solve the problem with a new rule instead of with blame."
        ),
        (
            "How did the ending prove that the world had changed?",
            "The children made an open sharing plan and carried the flower home together. That turned a secret borrowing into a happy system that everyone could trust."
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[tuple[str, str]]:
    clue = world.params.clue
    spot = world.params.share_spot
    items = [
        WORLD_KNOWLEDGE["sharing"],
        WORLD_KNOWLEDGE["trail"],
        WORLD_KNOWLEDGE["whodunit"],
    ]
    if clue == "pollen":
        items.append(
            (
                "Why can pollen become useful evidence in a garden mystery?",
                "Pollen sticks to hands, pots, and cloth very easily. When it appears where it does not belong, it can point a detective toward the right path."
            )
        )
    if clue == "sand":
        items.append(
            (
                "Why does sand make a good trail clue?",
                "Sand moves with feet and pots but does not stay everywhere. If it appears in dark garden soil, something probably traveled from a sandy place."
            )
        )
    if spot == "lantern_stile":
        items.append(
            (
                "Why does a lantern make a strong happy ending image?",
                "A lantern gives visible light, so readers can picture the scene clearly. It also suggests that worry has turned into safety."
            )
        )
    return items[:3]


def format_qa(sample: StorySample) -> str:
    parts: list[str] = ["PROMPTS"]
    for prompt in sample.prompts:
        parts.append(f"- {prompt}")
    parts.append("")
    parts.append("STORY QA")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("WORLD KNOWLEDGE QA")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: StoryWorld) -> str:
    lines = ["TRACE"]
    lines.append(f"params: {world.params}")
    lines.append(f"facts: {world.facts}")
    lines.append("entities:")
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  - {entity.id}: {entity.kind} | {entity.label}")
        if meters:
            lines.append(f"    meters={meters}")
        if memes:
            lines.append(f"    memes={memes}")
        if entity.attrs:
            lines.append(f"    attrs={entity.attrs}")
    lines.append("history:")
    for event in world.history:
        lines.append(f"  - {event.id} @ {event.place}: {event.text}")
    return "\n".join(lines)


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
        for path in sorted(borrower.routes):
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


def asp_program(show: str = "#show valid/5.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str, str]]:
    import asp

    model = asp.one_model(asp_program())
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
    if "whodunit" not in story_lower:
        raise AssertionError("story should carry the whodunit frame")
    if sample.story.count("\n\n") < 3:
        raise AssertionError("story should have at least four paragraphs")
    if not world.facts.get("solved"):
        raise AssertionError("story did not solve the case")
    if not world.facts.get("happy_ending"):
        raise AssertionError("story did not reach a happy ending")
    if world.get("flower").meters.get("shared_openly", 0) < 1:
        raise AssertionError("flower never reached open sharing")
    if world.get("recipient").meters.get("comfort", 0) < 1:
        raise AssertionError("recipient never received comfort")
    if len(sample.prompts) != 3:
        raise AssertionError("expected exactly three prompts")
    if len(sample.story_qa) < 5 or len(sample.world_qa) < 3:
        raise AssertionError("QA sets are too thin")
    if "{" in sample.story or "}" in sample.story:
        raise AssertionError("story leaked unresolved formatting")
    for item in list(sample.story_qa) + list(sample.world_qa):
        if len(item.answer.split()) < 10:
            raise AssertionError(f"answer is too short for: {item.question}")


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
        description="Generate a cozy-garden forest-trail sharing whodunit."
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
        raise StoryError("(No valid cozy-garden whodunit matches the given options.)")
    chosen = StoryParams(**vars(rng.choice(combos)))
    return chosen


def generate(params: StoryParams) -> StorySample:
    trail = TRAILS[params.trail]
    flower = FLOWERS[params.flower]
    borrower = BORROWERS[params.borrower]
    spot = SHARE_SPOTS[params.share_spot]
    clue = CLUES[params.clue]
    if not combo_is_valid(trail, flower, borrower, spot, clue):
        raise StoryError(explain_rejection(trail, flower, borrower, spot, clue))
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
        print()
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
        raise SystemExit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid cozy-garden whodunits:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:14}" for part in combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        selected = matching_params(args)
        if not selected:
            print("(No valid cozy-garden whodunit matches the given options.)")
            return
        samples = [generate(params) for params in selected]
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
        if len(samples) < args.n:
            print(f"(Only found {len(samples)} distinct stories after {attempts} attempts.)")
            return

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples, 1):
        header = ""
        if len(samples) > 1:
            header = f"=== cozy_garden_misty_flower_forest_trail_sharing_2 #{i} seed={sample.params.seed} ==="
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i != len(samples):
            print()


if __name__ == "__main__":
    main()
