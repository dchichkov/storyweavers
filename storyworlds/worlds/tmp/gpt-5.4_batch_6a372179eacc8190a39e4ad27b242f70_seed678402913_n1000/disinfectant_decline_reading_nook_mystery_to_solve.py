#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/disinfectant_decline_reading_nook_mystery_to_solve.py
=================================================================================

A small bedtime-style story world set in a reading nook.

Premise
-------
Two children settle into a cozy reading nook and discover that something needed
for their bedtime story game has gone missing. A fresh clue in the nook points
toward one hiding place. Solving the mystery requires a shared tool, but one
child may briefly decline to share it before choosing teamwork instead.

This world models:
- a clue grounded in the physical nook
- a short mystery with one sensible solution path
- emotional state: curiosity, frustration, generosity, relief
- sharing as the turn that lets the mystery resolve

The seed words "disinfectant" and "decline" appear naturally in the stories.

Run it
------
python storyworlds/worlds/gpt-5.4/disinfectant_decline_reading_nook_mystery_to_solve.py
python storyworlds/worlds/gpt-5.4/disinfectant_decline_reading_nook_mystery_to_solve.py --all
python storyworlds/worlds/gpt-5.4/disinfectant_decline_reading_nook_mystery_to_solve.py --qa
python storyworlds/worlds/gpt-5.4/disinfectant_decline_reading_nook_mystery_to_solve.py --trace
python storyworlds/worlds/gpt-5.4/disinfectant_decline_reading_nook_mystery_to_solve.py --verify
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

# Make shared result containers importable when run directly from the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
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
class LostThing:
    id: str
    label: str
    phrase: str
    use_text: str
    ending_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    notice_text: str
    points_to: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingSpot:
    id: str
    label: str
    phrase: str
    requires_tool: str = ""
    search_text: str = ""
    reveal_text: str = ""
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareTool:
    id: str
    label: str
    phrase: str
    holder_action: str
    shared_action: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_need_sharing(world: World) -> list[str]:
    holder = world.entities.get("holder")
    seeker = world.entities.get("seeker")
    spot = world.facts.get("spot_cfg")
    tool = world.facts.get("tool_cfg")
    if not holder or not seeker or not spot or not tool:
        return []
    if world.facts.get("searched_wrong"):
        sig = ("stuck", spot.id)
        if sig not in world.fired:
            world.fired.add(sig)
            holder.memes["frustration"] += 1
            seeker.memes["frustration"] += 1
            return [f"They still could not look properly {spot.phrase} without the {tool.label}."]
    return []


def _r_shared_search_succeeds(world: World) -> list[str]:
    item = world.entities.get("lost")
    holder = world.entities.get("holder")
    seeker = world.entities.get("seeker")
    spot = world.facts.get("spot_cfg")
    if not item or not holder or not seeker or not spot:
        return []
    if world.facts.get("tool_shared") and world.facts.get("searched_right"):
        sig = ("found", item.id)
        if sig not in world.fired:
            world.fired.add(sig)
            item.meters["found"] += 1
            holder.memes["relief"] += 1
            seeker.memes["relief"] += 1
            holder.memes["generosity"] += 1
            seeker.memes["gratitude"] += 1
            return ["__found__"]
    return []


CAUSAL_RULES = [
    Rule(name="need_sharing", tag="social", apply=_r_need_sharing),
    Rule(name="shared_search_succeeds", tag="physical", apply=_r_shared_search_succeeds),
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
        for s in produced:
            world.say(s)
    return produced


LOST_THINGS = {
    "bookmark": LostThing(
        id="bookmark",
        label="bookmark",
        phrase="a silver moon bookmark",
        use_text="mark the next chapter in their bedtime book",
        ending_text="the silver moon peeked from the page again",
        tags={"bookmark", "book"},
    ),
    "riddle_card": LostThing(
        id="riddle_card",
        label="riddle card",
        phrase="a little riddle card with stars around the edge",
        use_text="finish the mystery game tucked into their bedtime story",
        ending_text="the little stars on the card winked in the lamplight",
        tags={"riddle", "card"},
    ),
    "story_stone": LostThing(
        id="story_stone",
        label="story stone",
        phrase="a smooth story stone painted with a tiny owl",
        use_text="choose who would begin the bedtime tale",
        ending_text="the tiny owl on the stone looked wise and sleepy",
        tags={"stone", "owl"},
    ),
}

CLUES = {
    "lemon_smell": Clue(
        id="lemon_smell",
        label="lemony smell",
        notice_text="A lemony smell floated through the reading nook, the sharp-clean smell of disinfectant.",
        points_to={"book_bin"},
        tags={"disinfectant", "smell", "cleaning"},
    ),
    "glitter_thread": Clue(
        id="glitter_thread",
        label="glitter thread",
        notice_text="A tiny silver thread glimmered near the cushion seam, as if something had brushed past it.",
        points_to={"cushion_gap"},
        tags={"sparkle", "clue"},
    ),
    "paper_corner": Clue(
        id="paper_corner",
        label="paper corner",
        notice_text="Just beside the blanket chest, a small paper corner stuck out and then slipped back when the blanket settled.",
        points_to={"blanket_chest"},
        tags={"paper", "clue"},
    ),
}

SPOTS = {
    "book_bin": HidingSpot(
        id="book_bin",
        label="book bin",
        phrase="inside the deep book bin",
        requires_tool="grabber",
        search_text="The bin was so full of books that small things could slide to the very bottom.",
        reveal_text="At last the grabber hooked something flat between two books.",
        ending_image="They slid the book back into place and the reading nook smelled only softly clean now.",
        tags={"books", "bin"},
    ),
    "cushion_gap": HidingSpot(
        id="cushion_gap",
        label="cushion gap",
        phrase="in the dark gap behind the big floor cushion",
        requires_tool="flashlight",
        search_text="The gap was narrow and shadowy, too dark for guessing eyes.",
        reveal_text="The beam found a small shine tucked in the cloth fold.",
        ending_image="The cushion puffed back into place, and the nook looked warm and secret again.",
        tags={"cushion", "dark"},
    ),
    "blanket_chest": HidingSpot(
        id="blanket_chest",
        label="blanket chest",
        phrase="under the folded blankets in the little chest",
        requires_tool="both_hands",
        search_text="The blankets were piled high, and one child had to lift while the other looked underneath.",
        reveal_text="Under the last folded blanket waited the missing thing, quiet and patient.",
        ending_image="They folded the blankets neatly again, and the nook looked ready for sleep.",
        tags={"blanket", "chest"},
    ),
}

TOOLS = {
    "grabber": ShareTool(
        id="grabber",
        label="grabber",
        phrase="a little reaching grabber",
        holder_action="kept the little reaching grabber close by",
        shared_action="passed over the grabber so both children could take turns fishing carefully between the books",
        tags={"tool", "sharing"},
    ),
    "flashlight": ShareTool(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight shaped like a star",
        holder_action="hugged the small star-shaped flashlight to his chest",
        shared_action="clicked on the flashlight and held it steady so both children could search the shadows together",
        tags={"flashlight", "sharing"},
    ),
    "both_hands": ShareTool(
        id="both_hands",
        label="helping hands",
        phrase="two helping hands",
        holder_action="folded her hands and said she wanted the discovery all to herself",
        shared_action="used both hands to lift the blankets while the other child peeked underneath",
        tags={"help", "sharing"},
    ),
}


def valid_combo(clue_id: str, spot_id: str, tool_id: str) -> bool:
    clue = CLUES[clue_id]
    spot = SPOTS[spot_id]
    return spot_id in clue.points_to and spot.requires_tool == tool_id


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for clue_id in CLUES:
        for spot_id in SPOTS:
            for tool_id in TOOLS:
                if valid_combo(clue_id, spot_id, tool_id):
                    out.append((clue_id, spot_id, tool_id))
    return out


def predict_solution(world: World, share: bool) -> dict:
    sim = world.copy()
    sim.facts["tool_shared"] = share
    sim.facts["searched_right"] = True
    sim.facts["searched_wrong"] = not share
    propagate(sim, narrate=False)
    return {
        "found": sim.get("lost").meters["found"] >= THRESHOLD,
        "frustration": sim.get("holder").memes["frustration"] + sim.get("seeker").memes["frustration"],
    }


def opening(world: World, holder: Entity, seeker: Entity, item: Entity, parent: Entity) -> None:
    holder.memes["cozy"] += 1
    seeker.memes["cozy"] += 1
    world.say(
        f"At bedtime, {holder.id} and {seeker.id} tucked themselves into the reading nook with their knees under a soft quilt and a lamp glowing like a butter-yellow moon."
    )
    world.say(
        f"{parent.label_word.capitalize()} had stacked the pillows, straightened the baskets, and wiped the little shelf earlier that evening."
    )
    world.say(
        f"They were ready to use {item.phrase} to {world.facts['item_cfg'].use_text}, but when {seeker.id} reached for it, it was gone."
    )


def discover_clue(world: World, holder: Entity, seeker: Entity, clue: Clue) -> None:
    holder.memes["curiosity"] += 1
    seeker.memes["curiosity"] += 1
    world.say(
        f'"Where did it go?" whispered {seeker.id}. {clue.notice_text}'
    )
    world.say(
        f"That was enough to turn a missing thing into a tiny mystery to solve."
    )


def first_guess(world: World, seeker: Entity, wrong_spot: str) -> None:
    guess = {
        "book_bin": "under the lamp cushion",
        "cushion_gap": "inside the book basket",
        "blanket_chest": "behind the tallest stack of books",
    }[wrong_spot]
    world.say(
        f'{seeker.id} made a first guess and looked {guess}, but the missing thing was not there.'
    )


def hesitate_to_share(world: World, holder: Entity, seeker: Entity, tool: ShareTool) -> None:
    holder.memes["possessive"] += 1
    seeker.memes["hope"] += 1
    world.say(
        f"{holder.id} {tool.holder_action}. For one small moment, {holder.pronoun()} wanted to decline sharing it."
    )
    world.say(
        f'"I wanted to be the one who solves it," {holder.id} admitted.'
    )


def explain_need(world: World, seeker: Entity, holder: Entity, spot: HidingSpot, tool: ShareTool) -> None:
    pred = predict_solution(world, share=False)
    world.facts["predicted_frustration"] = pred["frustration"]
    seeker.memes["gentleness"] += 1
    world.say(
        f'{seeker.id} did not grab. "{spot.search_text} If we do not share the {tool.label}, we may stay stuck," {seeker.pronoun()} said softly.'
    )


def choose_sharing(world: World, holder: Entity, seeker: Entity, tool: ShareTool) -> None:
    holder.memes["generosity"] += 1
    world.facts["tool_shared"] = True
    world.facts["searched_right"] = True
    world.facts["searched_wrong"] = False
    world.say(
        f"{holder.id} looked at {seeker.id}, then at the sleepy little nook around them, and gave a shy nod."
    )
    world.say(
        f"{holder.pronoun().capitalize()} {tool.shared_action}."
    )
    propagate(world, narrate=False)


def solve_mystery(world: World, holder: Entity, seeker: Entity, spot: HidingSpot, item: Entity) -> None:
    world.say(
        f"Together they searched {spot.phrase}. {spot.reveal_text}"
    )
    world.say(
        f'"There you are," breathed {holder.id} as {item.phrase} came back into the light.'
    )


def bedtime_end(world: World, holder: Entity, seeker: Entity, item: Entity, spot: HidingSpot, parent: Entity) -> None:
    holder.memes["joy"] += 1
    seeker.memes["joy"] += 1
    world.say(
        f"They thanked each other, and even {parent.label_word} smiled from the doorway when the whispering mystery was finally done."
    )
    world.say(
        f"Soon the story began, {world.facts['item_cfg'].ending_text}, and {spot.ending_image}"
    )
    world.say(
        "By the time the last page turned, the whole nook felt calm, shared, and ready for sleep."
    )


def tell(
    *,
    lost_thing: LostThing,
    clue: Clue,
    spot: HidingSpot,
    tool: ShareTool,
    holder_name: str,
    holder_gender: str,
    seeker_name: str,
    seeker_gender: str,
    parent_type: str,
) -> World:
    world = World()
    holder = world.add(Entity(id=holder_name, kind="character", type=holder_gender, role="holder"))
    seeker = world.add(Entity(id=seeker_name, kind="character", type=seeker_gender, role="seeker"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    item = world.add(Entity(id="lost", kind="thing", type="lost_thing", label=lost_thing.label, phrase=lost_thing.phrase))
    tool_ent = world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label, phrase=tool.phrase, owner=holder.id))
    nook = world.add(Entity(id="nook", kind="thing", type="place", label="reading nook"))

    world.facts.update(
        item_cfg=lost_thing,
        clue_cfg=clue,
        spot_cfg=spot,
        tool_cfg=tool,
        holder=holder,
        seeker=seeker,
        parent=parent,
        item=item,
        tool=tool_ent,
        nook=nook,
        tool_shared=False,
        searched_right=False,
        searched_wrong=False,
    )

    opening(world, holder, seeker, item, parent)
    world.para()
    discover_clue(world, holder, seeker, clue)
    first_guess(world, seeker, spot.id)

    world.para()
    hesitate_to_share(world, holder, seeker, tool)
    explain_need(world, seeker, holder, spot, tool)
    world.facts["searched_wrong"] = True
    propagate(world, narrate=True)

    world.para()
    choose_sharing(world, holder, seeker, tool)
    solve_mystery(world, holder, seeker, spot, item)

    world.para()
    bedtime_end(world, holder, seeker, item, spot, parent)

    world.facts.update(
        found=item.meters["found"] >= THRESHOLD,
        shared=world.facts["tool_shared"],
        predicted_found_if_shared=predict_solution(world, share=True)["found"],
        predicted_found_without_sharing=predict_solution(world, share=False)["found"],
    )
    return world


KNOWLEDGE = {
    "disinfectant": [
        (
            "What is disinfectant?",
            "Disinfectant is a cleaning liquid or spray that helps kill germs on surfaces. Grown-ups use it to clean places like shelves or tables."
        )
    ],
    "sharing": [
        (
            "Why does sharing help in a problem?",
            "Sharing lets people use what each person has, so they can solve a problem together. It also helps everyone feel included and cared for."
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight useful in a dark place?",
            "A flashlight makes a beam of light that helps you see into shadows. That makes it easier to look safely and carefully."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. It can be a smell, a sound, or something tiny you notice."
        )
    ],
    "bookmark": [
        (
            "What does a bookmark do?",
            "A bookmark keeps your place in a book so you can come back later. It helps you find the next page without hunting for it again."
        )
    ],
    "reading_nook": [
        (
            "What is a reading nook?",
            "A reading nook is a small cozy place set up for reading and resting. It often has pillows, blankets, and soft light."
        )
    ],
    "blanket": [
        (
            "Why do blankets make a nook feel cozy?",
            "Blankets feel warm and soft, so they make a small space feel safe and comfortable. That is why many bedtime corners have them."
        )
    ],
}
KNOWLEDGE_ORDER = ["reading_nook", "clue", "disinfectant", "sharing", "flashlight", "bookmark", "blanket"]


@dataclass
class StoryParams:
    lost_thing: str
    clue: str
    spot: str
    tool: str
    holder_name: str
    holder_gender: str
    seeker_name: str
    seeker_gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        lost_thing="bookmark",
        clue="lemon_smell",
        spot="book_bin",
        tool="grabber",
        holder_name="Milo",
        holder_gender="boy",
        seeker_name="Nora",
        seeker_gender="girl",
        parent="mother",
    ),
    StoryParams(
        lost_thing="riddle_card",
        clue="glitter_thread",
        spot="cushion_gap",
        tool="flashlight",
        holder_name="Lily",
        holder_gender="girl",
        seeker_name="Ben",
        seeker_gender="boy",
        parent="father",
    ),
    StoryParams(
        lost_thing="story_stone",
        clue="paper_corner",
        spot="blanket_chest",
        tool="both_hands",
        holder_name="Ava",
        holder_gender="girl",
        seeker_name="Theo",
        seeker_gender="boy",
        parent="mother",
    ),
]


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo", "Milo"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    holder = f["holder"]
    seeker = f["seeker"]
    item = f["item_cfg"]
    clue = f["clue_cfg"]
    tool = f["tool_cfg"]
    return [
        'Write a bedtime story for a 3-to-5-year-old set in a reading nook, with a tiny mystery to solve and a gentle lesson about sharing. Include the words "disinfectant" and "decline".',
        f"Tell a soft, cozy story where {item.phrase} goes missing in a reading nook, {clue.label} becomes the clue, and {holder.id} must stop trying to keep {tool.label} to {holder.pronoun('object')}self.",
        f"Write a simple mystery story for bedtime where {holder.id} and {seeker.id} solve the problem together by sharing, then settle down to read."
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "a girl and a boy"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    holder = f["holder"]
    seeker = f["seeker"]
    parent = f["parent"]
    item = f["item_cfg"]
    clue = f["clue_cfg"]
    spot = f["spot_cfg"]
    tool = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(holder, seeker)}, {holder.id} and {seeker.id}, in a cozy reading nook. They were getting ready for a bedtime story when {item.label} went missing."
        ),
        (
            f"What was the mystery to solve?",
            f"The children had to figure out where {item.phrase} had gone. They needed it to {item.use_text}, so the little loss mattered right away."
        ),
        (
            "What clue did they notice?",
            f"They noticed {clue.label}. That small sign helped them guess the missing thing was near {spot.label}."
        ),
        (
            f"Why did {holder.id} not share right away?",
            f"{holder.id} wanted to be the one who solved the mystery alone, so {holder.pronoun()} almost kept the {tool.label} to {holder.pronoun('object')}self. For one moment, {holder.pronoun()} wanted to decline sharing because the discovery felt exciting."
        ),
        (
            "How did sharing help them solve the mystery?",
            f"Once they shared the {tool.label}, they could search {spot.phrase} the right way. Working together changed the search from guessing into finding."
        ),
        (
            "How did the story end?",
            f"They found {item.phrase}, thanked each other, and began their bedtime story at last. The ending feels peaceful because the mystery is solved and the children are sharing again."
        ),
    ]
    if f.get("predicted_frustration", 0) >= THRESHOLD:
        qa.append(
            (
                "What might have happened if they had not shared?",
                f"They might have stayed frustrated and the mystery could have lasted longer. In this world, the right search depended on sharing the {tool.label}."
            )
        )
    if parent:
        qa.append(
            (
                f"What was {holder.id}'s {parent.label_word} doing in the story?",
                f"{parent.label_word.capitalize()} had cleaned and straightened the reading nook earlier, which is why the smell of disinfectant made sense as a clue. At the end, {parent.pronoun()} smiled from the doorway when the children solved the problem kindly."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"reading_nook", "clue", "sharing"}
    item = world.facts["item_cfg"]
    clue = world.facts["clue_cfg"]
    spot = world.facts["spot_cfg"]
    tool = world.facts["tool_cfg"]
    tags |= set(item.tags) | set(clue.tags) | set(spot.tags) | set(tool.tags)
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: shared={world.facts.get('tool_shared')} found={world.facts.get('found')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(clue_id: str, spot_id: str, tool_id: str) -> str:
    clue = CLUES[clue_id]
    spot = SPOTS[spot_id]
    tool = TOOLS[tool_id]
    if spot_id not in clue.points_to:
        return (
            f"(No story: the clue '{clue.label}' does not honestly point to {spot.phrase}. "
            f"A mystery should be solvable from the clue, not by random guessing.)"
        )
    if spot.requires_tool != tool_id:
        needed = TOOLS[spot.requires_tool].label
        return (
            f"(No story: searching {spot.phrase} reasonably needs {needed}, not {tool.label}. "
            f"The shared tool must actually help solve the mystery.)"
        )
    return "(No story: that combination is not reasonable.)"


ASP_RULES = r"""
points(C, S) :- clue_points(C, S).
needs(S, T)  :- spot_requires(S, T).
valid(C, S, T) :- clue(C), spot(S), tool(T), points(C, S), needs(S, T).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for spot_id in SPOTS:
        lines.append(asp.fact("spot", spot_id))
    for tool_id in TOOLS:
        lines.append(asp.fact("tool", tool_id))
    for clue_id, clue in CLUES.items():
        for spot_id in sorted(clue.points_to):
            lines.append(asp.fact("clue_points", clue_id, spot_id))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot_requires", spot_id, spot.requires_tool))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: ASP gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if cset - pset:
            print("  only in ASP:", sorted(cset - pset))
        if pset - cset:
            print("  only in Python:", sorted(pset - cset))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "reading nook" not in sample.story:
            raise StoryError("Smoke test produced an empty or malformed story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime mystery in a reading nook. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--lost-thing", dest="lost_thing", choices=sorted(LOST_THINGS))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--spot", choices=sorted(SPOTS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid clue/spot/tool combos derived by ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.spot and args.tool and not valid_combo(args.clue, args.spot, args.tool):
        raise StoryError(explain_rejection(args.clue, args.spot, args.tool))

    combos = [
        combo for combo in valid_combos()
        if (args.clue is None or combo[0] == args.clue)
        and (args.spot is None or combo[1] == args.spot)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    clue_id, spot_id, tool_id = rng.choice(sorted(combos))
    lost_id = args.lost_thing or rng.choice(sorted(LOST_THINGS))
    holder_gender = rng.choice(["girl", "boy"])
    seeker_gender = rng.choice(["girl", "boy"])
    holder_name = _pick_name(rng, holder_gender)
    seeker_name = _pick_name(rng, seeker_gender, avoid=holder_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        lost_thing=lost_id,
        clue=clue_id,
        spot=spot_id,
        tool=tool_id,
        holder_name=holder_name,
        holder_gender=holder_gender,
        seeker_name=seeker_name,
        seeker_gender=seeker_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.lost_thing not in LOST_THINGS:
        raise StoryError(f"(Unknown lost thing: {params.lost_thing})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if not valid_combo(params.clue, params.spot, params.tool):
        raise StoryError(explain_rejection(params.clue, params.spot, params.tool))

    world = tell(
        lost_thing=LOST_THINGS[params.lost_thing],
        clue=CLUES[params.clue],
        spot=SPOTS[params.spot],
        tool=TOOLS[params.tool],
        holder_name=params.holder_name,
        holder_gender=params.holder_gender,
        seeker_name=params.seeker_name,
        seeker_gender=params.seeker_gender,
        parent_type=params.parent,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (clue, spot, tool) combos:\n")
        for clue_id, spot_id, tool_id in combos:
            print(f"  {clue_id:14} {spot_id:14} {tool_id}")
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
            header = f"### {p.holder_name} and {p.seeker_name}: {p.clue} -> {p.spot} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
