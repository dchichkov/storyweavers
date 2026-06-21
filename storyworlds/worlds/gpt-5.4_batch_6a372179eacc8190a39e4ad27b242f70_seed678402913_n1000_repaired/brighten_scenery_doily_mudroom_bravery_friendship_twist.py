#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/brighten_scenery_doily_mudroom_bravery_friendship_twist.py
=====================================================================================

A standalone storyworld for a tiny child-facing whodunit set in a mudroom.

Premise
-------
Two friends are making cheerful paper scenery in the mudroom when a lace doily
that usually helps brighten the little table goes missing. They notice clues,
suspect the wrong cause for a moment, then follow the world state to the real
answer. The story aims for a gentle mystery: bravery means looking in an
awkward or shadowy spot and telling the truth when blame feels close, friendship
means choosing trust over accusation, and the twist is that the real culprit is
not the first one the children guessed.

Run it
------
    python storyworlds/worlds/gpt-5.4/brighten_scenery_doily_mudroom_bravery_friendship_twist.py
    python storyworlds/worlds/gpt-5.4/brighten_scenery_doily_mudroom_bravery_friendship_twist.py --cause wind
    python storyworlds/worlds/gpt-5.4/brighten_scenery_doily_mudroom_bravery_friendship_twist.py --all
    python storyworlds/worlds/gpt-5.4/brighten_scenery_doily_mudroom_bravery_friendship_twist.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/brighten_scenery_doily_mudroom_bravery_friendship_twist.py --trace
    python storyworlds/worlds/gpt-5.4/brighten_scenery_doily_mudroom_bravery_friendship_twist.py --json
    python storyworlds/worlds/gpt-5.4/brighten_scenery_doily_mudroom_bravery_friendship_twist.py --verify
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


# ---------------------------------------------------------------------------
# Shared entity model.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"              # "character" | "thing"
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


# ---------------------------------------------------------------------------
# Domain knobs.
# ---------------------------------------------------------------------------
@dataclass
class Cause:
    id: str
    apparent: str
    true_culprit: str
    clue: str
    trace_mark: str
    hiding_place: str
    recovery_action: str
    brave_spot: str
    twist_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SearchStyle:
    id: str
    prop: str
    line: str
    check_action: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    detail: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World model and narration.
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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"sleuth", "friend"}]

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


# ---------------------------------------------------------------------------
# Causal rules.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_missing_worry(world: World) -> list[str]:
    doily = world.get("doily")
    if doily.attrs.get("where") != "missing":
        return []
    sig = ("missing_worry", "doily")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.children():
        kid.memes["worry"] += 1
    return ["__missing__"]


def _r_false_blame(world: World) -> list[str]:
    lead = world.facts.get("false_lead")
    if not lead:
        return []
    sig = ("false_blame", lead)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.children():
        kid.memes["suspicion"] += 1
    return ["__suspicion__"]


def _r_share_truth(world: World) -> list[str]:
    if not world.facts.get("friendship_repaired"):
        return []
    sig = ("share_truth", "repair")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.children():
        kid.memes["trust"] += 1
        kid.memes["worry"] = 0.0
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_worry", tag="emotion", apply=_r_missing_worry),
    Rule(name="false_blame", tag="emotion", apply=_r_false_blame),
    Rule(name="share_truth", tag="emotion", apply=_r_share_truth),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Registry content.
# ---------------------------------------------------------------------------
CAUSES = {
    "wind": Cause(
        id="wind",
        apparent="the puppy",
        true_culprit="a gust from the open door",
        clue="the paper hill on the scenery board was bent in the same direction as the wet umbrella straps",
        trace_mark="door_breeze",
        hiding_place="under the boot bench, caught against one red rain boot",
        recovery_action="knelt to look under the boot bench and reached past the lined-up boots",
        brave_spot="the dim space under the bench",
        twist_line="It had not been chewed or stolen at all. A gust had lifted it and tucked it beneath the bench like a pale little sail.",
        tags={"wind", "boots", "mystery"},
    ),
    "kitten": Cause(
        id="kitten",
        apparent="the wind",
        true_culprit="the kitten",
        clue="a thin white thread snagged on the edge of the shoe tray and two tiny paw prints beside it",
        trace_mark="paw_prints",
        hiding_place="inside the mitten basket, under one striped mitten",
        recovery_action="tipped the mitten basket gently and peered between the woolly gloves",
        brave_spot="the shadowy basket corner",
        twist_line="The breeze had looked guilty, but the real thief was softer and sneakier. The kitten had dragged the doily into the basket to make a nest.",
        tags={"kitten", "basket", "mystery"},
    ),
    "sibling": Cause(
        id="sibling",
        apparent="the wind",
        true_culprit="the little brother",
        clue="a crumb of blue paper scenery clung to the doorknob, matching the scraps by the craft box",
        trace_mark="blue_scrap",
        hiding_place="behind the coat curtain, where a pretend cave had been started",
        recovery_action="parted the hanging coats and stepped behind them",
        brave_spot="the coat-shadow cave",
        twist_line="The door had banged, but that was not the whole story. The little brother had borrowed the doily to make a moon for his own tiny cave.",
        tags={"sibling", "coats", "mystery"},
    ),
}

SEARCH_STYLES = {
    "magnifier": SearchStyle(
        id="magnifier",
        prop="a toy magnifying glass",
        line='"{0}, Chief Finder," {1} whispered, lifting {2}. "Every clue matters in a mudroom mystery."',
        check_action="They bent low and followed the smallest signs instead of arguing.",
        tags={"clue", "magnifier"},
    ),
    "notebook": SearchStyle(
        id="notebook",
        prop="a little detective notebook",
        line='"{0}, Chief Note-Taker," {1} whispered, opening {2}. "A true clue should fit the facts."',
        check_action="They paused to compare each clue with what the room really showed.",
        tags={"clue", "notebook"},
    ),
    "flashlight": SearchStyle(
        id="flashlight",
        prop="a small flashlight",
        line='"{0}, Chief Light-Finder," {1} whispered, clicking on {2}. "Let us brighten the corners before we guess."',
        check_action="The beam helped them brighten the darker edges of the mudroom and notice what had been missed.",
        tags={"light", "flashlight"},
    ),
}

COMFORTS = {
    "lamp": Comfort(
        id="lamp",
        detail="the little table lamp in the mudroom window",
        ending_image="The lamp shone on the lace, and the whole muddy little room looked kinder.",
        tags={"lamp"},
    ),
    "window": Comfort(
        id="window",
        detail="the bright mudroom window ledge",
        ending_image="Sun from the window touched the lace and made the paper scenery look almost magical.",
        tags={"window"},
    ),
    "bench": Comfort(
        id="bench",
        detail="the freshly wiped mudroom bench",
        ending_image="The doily sat safe again, and even the boot bench looked tidy enough for a solved case.",
        tags={"bench"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "bold", "curious", "steady", "thoughtful", "cheerful"]


# ---------------------------------------------------------------------------
# Constraints and helpers.
# ---------------------------------------------------------------------------
def valid_combo(cause_id: str, search_id: str, comfort_id: str) -> bool:
    cause = CAUSES[cause_id]
    search = SEARCH_STYLES[search_id]
    comfort = COMFORTS[comfort_id]
    if cause.id == "wind" and comfort.id == "window":
        return False
    if cause.id == "kitten" and search.id == "flashlight":
        return False
    if cause.id == "sibling" and comfort.id == "bench":
        return False
    return bool(cause and search and comfort)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for cause_id in sorted(CAUSES):
        for search_id in sorted(SEARCH_STYLES):
            for comfort_id in sorted(COMFORTS):
                if valid_combo(cause_id, search_id, comfort_id):
                    combos.append((cause_id, search_id, comfort_id))
    return combos


def explain_rejection(cause_id: str, search_id: str, comfort_id: str) -> str:
    if cause_id == "wind" and comfort_id == "window":
        return ("(No story: if a gust from the door caused the mystery, ending with the doily set on the open window ledge is too drafty to feel sensible. Pick a steadier resting place.)")
    if cause_id == "kitten" and search_id == "flashlight":
        return ("(No story: a flashlight-heavy search weakens the kitten clues, which are soft and close-up. A magnifying glass or notebook fits this mystery better.)")
    if cause_id == "sibling" and comfort_id == "bench":
        return ("(No story: when the twist involves the little brother's coat-curtain cave, ending at the boot bench misses the emotional resolution. A warmer resting place fits better.)")
    return "(No valid combination matches the given options.)"


def false_lead_for(cause: Cause) -> str:
    return cause.apparent


def brave_success(world: World) -> bool:
    sleuth = world.get("sleuth")
    friend = world.get("friend")
    return sleuth.memes["bravery"] >= THRESHOLD and friend.memes["support"] >= THRESHOLD


# ---------------------------------------------------------------------------
# Simulation verbs.
# ---------------------------------------------------------------------------
def setup_scene(world: World, sleuth: Entity, friend: Entity, search: SearchStyle, comfort: Comfort) -> None:
    for kid in (sleuth, friend):
        kid.memes["joy"] += 1
        kid.memes["friendship"] += 1
    doily = world.get("doily")
    world.say(
        f"On a rainy afternoon, {sleuth.id} and {friend.id} played in the mudroom while puddles tapped outside. "
        f"They were making paper scenery for a pretend detective show, and the little table looked extra cheerful because a lace doily rested beside {comfort.detail}."
    )
    world.say(
        f"{friend.id} set out paper trees and a paper moon. {sleuth.id} picked up {search.prop}, already speaking in a whisper as if the case had begun."
    )
    world.say(
        f'Together they promised to keep the scenery neat, because the doily made the whole small room brighten.'
    )
    world.facts["doily_start"] = doily.attrs.get("where", "table")


def missing_beat(world: World, sleuth: Entity, friend: Entity, search: SearchStyle) -> None:
    doily = world.get("doily")
    doily.attrs["where"] = "missing"
    propagate(world, narrate=False)
    world.say(
        f"But when {friend.id} reached for the lace to slide the paper moon a little closer, the doily was gone."
    )
    world.say(
        f'{search.line.format(sleuth.id, friend.id, search.prop)}'
    )
    world.say("They looked at the empty tabletop and fell very quiet.")


def guess_wrong(world: World, sleuth: Entity, friend: Entity, cause: Cause, search: SearchStyle) -> None:
    world.facts["false_lead"] = false_lead_for(cause)
    propagate(world, narrate=False)
    world.say(
        f'At first the clues seemed to point at {cause.apparent}. "{cause.apparent.capitalize()} did it," {sleuth.id} said.'
    )
    world.say(
        f'{friend.id} frowned. "Maybe. But a good whodunit should fit all the clues." {search.check_action}'
    )
    friend.memes["support"] += 1
    sleuth.memes["doubt"] += 1


def inspect_clues(world: World, sleuth: Entity, friend: Entity, cause: Cause) -> None:
    world.say(
        f"Then {friend.id} noticed something new: {cause.clue}."
    )
    world.say(
        f"That did not match the first guess at all, so the room changed from simple to puzzling in one blink."
    )
    world.facts["true_clue"] = cause.clue
    sleuth.memes["reason"] += 1
    friend.memes["reason"] += 1


def choose_bravery(world: World, sleuth: Entity, friend: Entity, cause: Cause) -> None:
    sleuth.memes["bravery"] += 1
    friend.memes["support"] += 1
    world.say(
        f'"The last clue leads to {cause.brave_spot}," {friend.id} said softly.'
    )
    world.say(
        f"{sleuth.id} did not love that idea. The mudroom was not truly scary, but {cause.brave_spot} still looked close and shadowy."
    )
    world.say(
        f'Friendship felt stronger than the shiver in {sleuth.id}\'s belly. "{friend.id}, stay with me," {sleuth.id} whispered. "{friend.id}," {friend.id} answered, taking {sleuth.pronoun("possessive")} hand.'
    )


def reveal(world: World, sleuth: Entity, friend: Entity, cause: Cause) -> None:
    if not brave_success(world):
        raise StoryError("(No story: the children never became brave enough to follow the final clue.)")
    doily = world.get("doily")
    world.say(
        f"Together they {cause.recovery_action}."
    )
    doily.attrs["where"] = cause.hiding_place
    doily.meters["found"] += 1
    world.say(cause.twist_line)
    world.say(
        f"There, safe at last, lay the doily."
    )
    world.facts["reveal_place"] = cause.hiding_place
    world.facts["true_culprit"] = cause.true_culprit


def repair_friendship(world: World, sleuth: Entity, friend: Entity, cause: Cause) -> None:
    world.facts["friendship_repaired"] = True
    propagate(world, narrate=False)
    sleuth.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    world.say(
        f'{sleuth.id} looked at {friend.id} and felt a warm, embarrassed little squeeze inside. "I am glad you told me not to blame {cause.apparent} too fast," {sleuth.pronoun()} said.'
    )
    world.say(
        f'"That is what partners do," {friend.id} answered. "We stay kind until the truth catches up."'
    )


def restore_order(world: World, sleuth: Entity, friend: Entity, comfort: Comfort) -> None:
    doily = world.get("doily")
    doily.attrs["where"] = comfort.id
    doily.meters["safe"] += 1
    sleuth.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"They shook the lace gently, set it back beside the scenery, and made the paper trees stand straight again."
    )
    world.say(
        f"Now the mudroom did not feel like a place of loss at all. It felt like a place where brave friends could solve gentle mysteries together."
    )
    world.say(comfort.ending_image)


def tell(
    cause: Cause,
    search: SearchStyle,
    comfort: Comfort,
    sleuth_name: str = "Lily",
    sleuth_gender: str = "girl",
    friend_name: str = "Tom",
    friend_gender: str = "boy",
    parent_type: str = "mother",
    sleuth_trait: str = "curious",
    friend_trait: str = "steady",
    pet_name: str = "the kitten",
    sibling_name: str = "Ned",
) -> World:
    world = World()
    sleuth = world.add(Entity(
        id=sleuth_name,
        kind="character",
        type=sleuth_gender,
        role="sleuth",
        traits=[sleuth_trait],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=[friend_trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    doily = world.add(Entity(
        id="doily",
        type="doily",
        label="doily",
        phrase="a small lace doily",
        attrs={"where": "table"},
        tags={"doily", "lace"},
    ))
    world.add(Entity(id="mudroom", type="room", label="mudroom", tags={"mudroom"}))
    if cause.id == "kitten":
        world.add(Entity(id="pet", type="thing", label=pet_name, tags={"kitten"}))
    if cause.id == "sibling":
        world.add(Entity(id="sibling", kind="character", type="boy", label=sibling_name, tags={"sibling"}))

    setup_scene(world, sleuth, friend, search, comfort)
    world.para()
    missing_beat(world, sleuth, friend, search)
    guess_wrong(world, sleuth, friend, cause, search)
    inspect_clues(world, sleuth, friend, cause)
    world.para()
    choose_bravery(world, sleuth, friend, cause)
    reveal(world, sleuth, friend, cause)
    repair_friendship(world, sleuth, friend, cause)
    world.para()
    restore_order(world, sleuth, friend, comfort)

    world.facts.update(
        cause=cause,
        search=search,
        comfort=comfort,
        sleuth=sleuth,
        friend=friend,
        parent=parent,
        doily=doily,
        pet_name=pet_name,
        sibling_name=sibling_name,
        brave=brave_success(world),
        recovered=doily.meters["found"] >= THRESHOLD,
        ending_place=comfort.id,
    )
    return world


# ---------------------------------------------------------------------------
# Per-world parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    cause: str
    search: str
    comfort: str
    sleuth_name: str
    sleuth_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    sleuth_trait: str
    friend_trait: str
    pet_name: str = "the kitten"
    sibling_name: str = "Ned"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "mudroom": [
        (
            "What is a mudroom?",
            "A mudroom is a small room near a door where people leave boots, coats, and wet things before going into the rest of the house."
        )
    ],
    "doily": [
        (
            "What is a doily?",
            "A doily is a small cloth, often made of lace, that people place under or beside things to make a table look pretty and neat."
        )
    ],
    "whodunit": [
        (
            "What is a whodunit story?",
            "A whodunit is a mystery story where characters look for clues and try to figure out who caused the problem."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you understand what happened. Good clues match the truth instead of only matching a quick guess."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right thing even when you feel nervous. It does not mean you never feel scared."
        )
    ],
    "friendship": [
        (
            "How can friendship help in a problem?",
            "A good friend helps you stay calm, kind, and honest. Working together often helps people notice the truth."
        )
    ],
    "wind": [
        (
            "How can wind move light things?",
            "A strong little gust can lift or slide light paper and cloth. That is why people keep light things away from open doors and breezes."
        )
    ],
    "kitten": [
        (
            "Why might a kitten carry cloth into a basket?",
            "Kittens like soft places. A small cloth can feel cozy to curl up on, so a kitten may drag it to a snug spot."
        )
    ],
    "sibling": [
        (
            "Why might a younger child borrow something without asking?",
            "Little children sometimes see a pretty object and use it in play before thinking to ask first. They still need help learning to return things."
        )
    ],
}
KNOWLEDGE_ORDER = ["mudroom", "doily", "whodunit", "clue", "bravery", "friendship", "wind", "kitten", "sibling"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cause = f["cause"]
    search = f["search"]
    return [
        'Write a gentle whodunit for a 3-to-5-year-old set in a mudroom. Include the words "brighten", "scenery", and "doily".',
        f"Tell a small mystery where two friends making scenery in the mudroom discover that a doily is missing, follow clues with {search.prop}, and solve the case with bravery and friendship.",
        f"Write a child-facing mystery with a twist where everyone first suspects {cause.apparent}, but the real answer is {cause.true_culprit}."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sleuth = f["sleuth"]
    friend = f["friend"]
    cause = f["cause"]
    search = f["search"]
    comfort = f["comfort"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {sleuth.id} and {friend.id}, two friends playing detective in the mudroom. They were making paper scenery when the doily disappeared."
        ),
        (
            "What was missing?",
            "A small lace doily was missing from the little table. It had helped the mudroom look cheerful and neat."
        ),
        (
            f"Why did they think {cause.apparent} had done it at first?",
            f"They made a quick guess before they had all the facts. In a mystery, the first idea can feel right even when a later clue shows it is wrong."
        ),
        (
            "What clue changed the case?",
            f"The clue was that {cause.clue}. That did not fit the first guess, so it pushed them toward the true answer."
        ),
        (
            "How did bravery help solve the mystery?",
            f"{sleuth.id} felt nervous about checking {cause.brave_spot}, but went anyway because {friend.id} stayed beside {sleuth.pronoun('object')}. Their bravery mattered because the doily was hidden in that last, awkward place."
        ),
        (
            "How did friendship help?",
            f"They stopped blaming and started listening to each other. Because they worked together kindly, they followed the real clue instead of the wrong guess."
        ),
        (
            "What was the twist?",
            f"The twist was that the doily had not been taken by {cause.apparent} after all. The true cause was {cause.true_culprit}, and the doily was hidden {f['reveal_place']}."
        ),
        (
            "How did the story end?",
            f"They put the doily back beside the scenery and made the mudroom feel cozy again. {comfort.ending_image}"
        ),
    ]
    if cause.id == "kitten":
        qa.append((
            "Did the kitten mean to be naughty?",
            "No. The kitten only wanted a soft place to curl up, so the problem came from animal behavior, not meanness."
        ))
    if cause.id == "sibling":
        qa.append((
            "Was the little brother trying to be bad?",
            "No. He had borrowed the doily for pretend play without thinking it through. The twist shows that confusion is not the same as cruelty."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mudroom", "doily", "whodunit", "clue", "bravery", "friendship", f["cause"].id}
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
# Trace helpers.
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(Cause, Search, Comfort) :- cause(Cause), search(Search), comfort(Comfort),
                                 not bad_combo(Cause, Search, Comfort).

bad_combo(wind, _, window).
bad_combo(kitten, flashlight, _).
bad_combo(sibling, _, bench).

wrong_lead(Cause, Apparent) :- apparent(Cause, Apparent).
reveal(Cause, Truth) :- truth(Cause, Truth).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("apparent", cause_id, cause.apparent))
        lines.append(asp.fact("truth", cause_id, cause.true_culprit))
    for search_id in SEARCH_STYLES:
        lines.append(asp.fact("search", search_id))
    for comfort_id in COMFORTS:
        lines.append(asp.fact("comfort", comfort_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Verify failed: generated story was empty.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"VERIFY ERROR: smoke test failed: {err}")

    for params in CURATED[:3]:
        try:
            sample = generate(params)
            if "doily" not in sample.story.lower() or "mudroom" not in sample.story.lower():
                raise StoryError("(Verify failed: required seed words or setting missing from story text.)")
        except Exception as err:
            rc = 1
            print(f"VERIFY ERROR: curated generation failed for {params.cause}: {err}")
    if rc == 0:
        print("OK: curated generation checks passed.")
    return rc


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        cause="wind",
        search="flashlight",
        comfort="lamp",
        sleuth_name="Lily",
        sleuth_gender="girl",
        friend_name="Tom",
        friend_gender="boy",
        parent="mother",
        sleuth_trait="curious",
        friend_trait="steady",
        pet_name="the kitten",
        sibling_name="Ned",
    ),
    StoryParams(
        cause="kitten",
        search="magnifier",
        comfort="bench",
        sleuth_name="Mia",
        sleuth_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        parent="father",
        sleuth_trait="bold",
        friend_trait="careful",
        pet_name="the kitten",
        sibling_name="Oli",
    ),
    StoryParams(
        cause="sibling",
        search="notebook",
        comfort="window",
        sleuth_name="Sam",
        sleuth_gender="boy",
        friend_name="Zoe",
        friend_gender="girl",
        parent="mother",
        sleuth_trait="thoughtful",
        friend_trait="cheerful",
        pet_name="the kitten",
        sibling_name="Pip",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle mudroom whodunit about a missing doily, bravery, friendship, and a twist."
    )
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--search", choices=SEARCH_STYLES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--sleuth-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.search and args.comfort and not valid_combo(args.cause, args.search, args.comfort):
        raise StoryError(explain_rejection(args.cause, args.search, args.comfort))

    combos = [
        combo for combo in valid_combos()
        if (args.cause is None or combo[0] == args.cause)
        and (args.search is None or combo[1] == args.search)
        and (args.comfort is None or combo[2] == args.comfort)
    ]
    if not combos:
        if args.cause and args.search and args.comfort:
            raise StoryError(explain_rejection(args.cause, args.search, args.comfort))
        raise StoryError("(No valid combination matches the given options.)")

    cause_id, search_id, comfort_id = rng.choice(sorted(combos))
    sleuth_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    sleuth_name = args.sleuth_name or _pick_name(rng, sleuth_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=sleuth_name)
    parent = args.parent or rng.choice(["mother", "father"])
    sleuth_trait = rng.choice(TRAITS)
    friend_trait = rng.choice([t for t in TRAITS if t != sleuth_trait] or TRAITS)
    pet_name = rng.choice(["the kitten", "the gray kitten", "the small cat"])
    sibling_name = rng.choice(["Pip", "Ned", "Milo", "Toby"])
    return StoryParams(
        cause=cause_id,
        search=search_id,
        comfort=comfort_id,
        sleuth_name=sleuth_name,
        sleuth_gender=sleuth_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        sleuth_trait=sleuth_trait,
        friend_trait=friend_trait,
        pet_name=pet_name,
        sibling_name=sibling_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.cause not in CAUSES:
        raise StoryError(f"(Invalid cause: {params.cause})")
    if params.search not in SEARCH_STYLES:
        raise StoryError(f"(Invalid search style: {params.search})")
    if params.comfort not in COMFORTS:
        raise StoryError(f"(Invalid comfort ending: {params.comfort})")
    if not valid_combo(params.cause, params.search, params.comfort):
        raise StoryError(explain_rejection(params.cause, params.search, params.comfort))

    world = tell(
        cause=CAUSES[params.cause],
        search=SEARCH_STYLES[params.search],
        comfort=COMFORTS[params.comfort],
        sleuth_name=params.sleuth_name,
        sleuth_gender=params.sleuth_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        sleuth_trait=params.sleuth_trait,
        friend_trait=params.friend_trait,
        pet_name=params.pet_name,
        sibling_name=params.sibling_name,
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
        print(f"{len(combos)} compatible (cause, search, comfort) combos:\n")
        for cause_id, search_id, comfort_id in combos:
            print(f"  {cause_id:8} {search_id:10} {comfort_id}")
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
            header = f"### {p.sleuth_name} & {p.friend_name}: {p.cause} / {p.search} / {p.comfort}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
