#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/classic_wrench_loo_misunderstanding_happy_ending_sharing.py
======================================================================================

A standalone story world for a small slice-of-life misunderstanding tale:
two children are playing repair shop with a classic toy toolbox when a grown-up
needs a wrench for a loose loo fixture. One child hears "the wrench" and thinks
the favorite toy wrench is being taken away. The mix-up is clarified, the loo is
fixed with the proper tool, and the children end by sharing their play tools.

This world models:
- a home place with a loo problem that may or may not be present there
- a real wrench that may or may not fit the job
- a play kit that may or may not contain a toy wrench, which is required for
  the misunderstanding to make sense

The story shape is stable:
premise -> ambiguous request -> misunderstanding -> clarification -> repair ->
shared, happy ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/classic_wrench_loo_misunderstanding_happy_ending_sharing.py
    python storyworlds/worlds/gpt-5.4/classic_wrench_loo_misunderstanding_happy_ending_sharing.py --problem loo_seat --tool basin_wrench
    python storyworlds/worlds/gpt-5.4/classic_wrench_loo_misunderstanding_happy_ending_sharing.py --kit doctor_bag
    python storyworlds/worlds/gpt-5.4/classic_wrench_loo_misunderstanding_happy_ending_sharing.py --all
    python storyworlds/worlds/gpt-5.4/classic_wrench_loo_misunderstanding_happy_ending_sharing.py --verify
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
    traits: tuple = field(default_factory=tuple)
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    safe_for_child: bool = False
    plastic: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    bathroom_phrase: str
    allows: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    fixture: str
    need: str
    loose_part: str
    repair_line: str
    after_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    works_on: set[str] = field(default_factory=set)
    child_safe_help: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class PlayKit:
    id: str
    label: str
    phrase: str
    classic: bool = False
    has_toy_wrench: bool = False
    toy_color: str = ""
    ending_play: str = ""
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
        return [e for e in self.entities.values() if e.role in {"owner", "friend"}]

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


def _r_worry_blocks_sharing(world: World) -> list[str]:
    out: list[str] = []
    owner = world.entities.get("owner")
    if owner is None:
        return out
    if owner.memes["worry"] >= THRESHOLD and owner.memes["trust"] < THRESHOLD:
        sig = ("guarding", owner.id)
        if sig not in world.fired:
            world.fired.add(sig)
            owner.memes["guarding"] += 1
            out.append("__guarding__")
    return out


def _r_clarity_brings_relief(world: World) -> list[str]:
    out: list[str] = []
    owner = world.entities.get("owner")
    if owner is None:
        return out
    if owner.memes["clarity"] >= THRESHOLD:
        sig = ("relief", owner.id)
        if sig not in world.fired:
            world.fired.add(sig)
            owner.memes["worry"] = 0.0
            owner.memes["trust"] += 1
            owner.memes["relief"] += 1
            out.append("__relief__")
    return out


def _r_fixed_room_calms_everyone(world: World) -> list[str]:
    out: list[str] = []
    loo = world.entities.get("loo")
    if loo is None:
        return out
    if loo.meters["fixed"] >= THRESHOLD:
        sig = ("calm", loo.id)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in world.kids():
                kid.memes["calm"] += 1
                kid.memes["joy"] += 1
            out.append("__calm__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="worry_blocks_sharing", tag="social", apply=_r_worry_blocks_sharing),
    Rule(name="clarity_brings_relief", tag="social", apply=_r_clarity_brings_relief),
    Rule(name="fixed_room_calms_everyone", tag="physical", apply=_r_fixed_room_calms_everyone),
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
        for sent in produced:
            world.say(sent)
    return produced


def problem_possible(place: Place, problem: Problem) -> bool:
    return problem.id in place.allows


def tool_fits(problem: Problem, tool: Tool) -> bool:
    return problem.id in tool.works_on


def misunderstanding_possible(kit: PlayKit) -> bool:
    return kit.has_toy_wrench


def valid_story(place: Place, problem: Problem, tool: Tool, kit: PlayKit) -> bool:
    return problem_possible(place, problem) and tool_fits(problem, tool) and misunderstanding_possible(kit)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for problem_id, problem in PROBLEMS.items():
            for tool_id, tool in TOOLS.items():
                for kit_id, kit in PLAY_KITS.items():
                    if valid_story(place, problem, tool, kit):
                        combos.append((place_id, problem_id, tool_id, kit_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if not valid_story(PLACES[params.place], PROBLEMS[params.problem], TOOLS[params.tool], PLAY_KITS[params.kit]):
        return "invalid"
    return "shared_fix"


def predict_need(world: World, problem_id: str, tool_id: str) -> dict:
    sim = world.copy()
    problem = PROBLEMS[problem_id]
    tool = TOOLS[tool_id]
    loo = sim.get("loo")
    if tool_fits(problem, tool):
        loo.meters["fixed"] += 1
        loo.meters["loose"] = 0.0
    return {
        "can_fix": loo.meters["fixed"] >= THRESHOLD,
        "still_loose": loo.meters["loose"] >= THRESHOLD,
    }


def introduce(world: World, owner: Entity, friend: Entity, kit: PlayKit) -> None:
    classic = "classic " if kit.classic else ""
    world.say(
        f"{world.place.opening} {owner.id} and {friend.id} sat on the rug outside {world.place.bathroom_phrase} "
        f"with {kit.phrase}. Inside it was a {classic}{kit.toy_color} toy wrench that {owner.id} liked very much."
    )
    owner.memes["pride"] += 1
    friend.memes["joy"] += 1
    owner.memes["joy"] += 1
    world.say(
        f"They were pretending to fix all the squeaks in the house, and every chair leg and door hinge got a turn."
    )


def note_problem(world: World, parent: Entity, problem: Problem) -> None:
    loo = world.get("loo")
    loo.meters["loose"] += 1
    world.say(
        f"Then {parent.label_word} paused in the loo. {problem.repair_line}"
    )


def ambiguous_request(world: World, parent: Entity, owner: Entity, friend: Entity, tool: Tool) -> None:
    parent.memes["need_help"] += 1
    world.say(
        f'"Could someone bring me the wrench?" {parent.label_word.capitalize()} called. '
        f'"The loo needs a quick tighten."'
    )
    world.facts["heard_word"] = "wrench"
    owner.memes["worry"] += 1
    owner.memes["trust"] = 0.0
    friend.memes["confusion"] += 1
    propagate(world, narrate=False)
    if owner.memes["guarding"] >= THRESHOLD:
        world.say(
            f"{owner.id} quickly put a hand over the toy wrench in the play kit. "
            f"{owner.pronoun().capitalize()} thought the grown-up meant that one."
        )


def mistaken_hurt(world: World, owner: Entity, friend: Entity, kit: PlayKit) -> None:
    owner.memes["sadness"] += 1
    friend.memes["concern"] += 1
    world.say(
        f'"But that is my wrench," {owner.id} said in a small voice. '
        f'"If it goes away, our game will stop."'
    )
    world.say(
        f'{friend.id} blinked. "{owner.id}, maybe {friend.pronoun("subject")} just wants to borrow it," '
        f'{friend.pronoun()} said, but that only made {owner.id} hug the {kit.label} closer.'
    )


def clarify(world: World, parent: Entity, owner: Entity, tool: Tool, kit: PlayKit) -> None:
    owner.memes["clarity"] += 1
    parent.memes["care"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} stepped out and saw the worried face at once."
    )
    world.say(
        f'"Oh, not your toy wrench," {parent.pronoun()} said gently. '
        f'"I meant {tool.phrase} from the hall toolbox. Your {kit.toy_color} one is for play, and it stays with you."'
    )


def supervised_help(world: World, parent: Entity, owner: Entity, friend: Entity, problem: Problem, tool: Tool) -> None:
    loo = world.get("loo")
    real_tool = world.get("real_tool")
    real_tool.meters["borrowed"] += 1
    friend.memes["helpfulness"] += 1
    owner.memes["helpfulness"] += 1
    world.say(
        f"{friend.id} fetched {tool.phrase}, and {owner.id} carried the little tray of screws just to help."
    )
    pred = predict_need(world, problem.id, tool.id)
    if not pred["can_fix"]:
        raise StoryError("(Story error: selected tool cannot actually fix the loo problem.)")
    loo.meters["fixed"] += 1
    loo.meters["loose"] = 0.0
    real_tool.meters["used"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} knelt by the loo and used the wrench while both children watched from the doorway. "
        f"{problem.after_line}"
    )


def sharing_ending(world: World, owner: Entity, friend: Entity, kit: PlayKit) -> None:
    owner.memes["generosity"] += 1
    friend.memes["gratitude"] += 1
    owner.memes["joy"] += 1
    friend.memes["joy"] += 1
    toy = world.get("toy_wrench")
    toy.meters["shared"] += 1
    world.say(
        f'{owner.id} let out a long breath and smiled. "{friend.id}, you can use my toy wrench first," '
        f'{owner.pronoun()} said.'
    )
    world.say(
        f"Soon they were both back on the rug, {kit.ending_play}. This time the wrench went happily from one small hand to the other."
    )


def tell(
    place: Place,
    problem: Problem,
    tool: Tool,
    kit: PlayKit,
    owner_name: str = "Mia",
    owner_gender: str = "girl",
    friend_name: str = "Ben",
    friend_gender: str = "boy",
    parent_type: str = "mother",
    owner_trait: str = "careful",
    friend_trait: str = "kind",
) -> World:
    world = World(place)
    owner = world.add(Entity(
        id=owner_name,
        kind="character",
        type=owner_gender,
        label=owner_name,
        role="owner",
        attrs={"trait": owner_trait},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        attrs={"trait": friend_trait},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    world.add(Entity(
        id="loo",
        kind="thing",
        type="fixture",
        label=problem.fixture,
        phrase=problem.fixture,
        tags=set(problem.tags),
    ))
    world.add(Entity(
        id="real_tool",
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        safe_for_child=tool.child_safe_help,
        tags=set(tool.tags),
    ))
    world.add(Entity(
        id="toy_wrench",
        kind="thing",
        type="toy",
        label="toy wrench",
        phrase=f"{kit.toy_color} toy wrench",
        owner=owner.id,
        safe_for_child=True,
        plastic=True,
        tags=set(kit.tags),
    ))

    introduce(world, owner, friend, kit)
    note_problem(world, parent, problem)

    world.para()
    ambiguous_request(world, parent, owner, friend, tool)
    mistaken_hurt(world, owner, friend, kit)

    world.para()
    clarify(world, parent, owner, tool, kit)
    supervised_help(world, parent, owner, friend, problem, tool)

    world.para()
    sharing_ending(world, owner, friend, kit)

    world.facts.update(
        place=place,
        problem=problem,
        tool=tool,
        kit=kit,
        owner=owner,
        friend=friend,
        parent=parent,
        misunderstanding=True,
        repaired=world.get("loo").meters["fixed"] >= THRESHOLD,
        shared=world.get("toy_wrench").meters["shared"] >= THRESHOLD,
        outcome="shared_fix",
    )
    return world


PLACES = {
    "flat_hall": Place(
        id="flat_hall",
        label="the flat hallway",
        opening="On a quiet afternoon in the flat hallway,",
        bathroom_phrase="the loo",
        allows={"loo_seat", "flush_handle"},
    ),
    "small_house": Place(
        id="small_house",
        label="the little house landing",
        opening="On a bright afternoon in the little house landing,",
        bathroom_phrase="the upstairs loo",
        allows={"loo_seat", "flush_handle", "paper_holder"},
    ),
    "grandma_house": Place(
        id="grandma_house",
        label="Grandma's long hall",
        opening="At Grandma's house after lunch,",
        bathroom_phrase="the guest loo",
        allows={"loo_seat", "paper_holder"},
    ),
}

PROBLEMS = {
    "loo_seat": Problem(
        id="loo_seat",
        label="loose loo seat",
        fixture="loo seat",
        need="nut",
        loose_part="the side bolt",
        repair_line="The loo seat gave a soft wobble when it was touched.",
        after_line="A few careful turns later, the seat sat still and straight again.",
        tags={"loo", "repair"},
    ),
    "flush_handle": Problem(
        id="flush_handle",
        label="loose flush handle",
        fixture="flush handle",
        need="small_nut",
        loose_part="the nut behind the handle",
        repair_line="The handle felt floppy, as if it might wiggle right off.",
        after_line="After a snug turn, the handle sat firm and gave a neat little click.",
        tags={"loo", "repair"},
    ),
    "paper_holder": Problem(
        id="paper_holder",
        label="wobbly loo paper holder",
        fixture="loo paper holder",
        need="mount",
        loose_part="the little side fastener",
        repair_line="The loo paper holder kept dipping to one side whenever someone touched it.",
        after_line="Soon the holder stood straight again, with the roll sitting nicely in place.",
        tags={"loo", "repair"},
    ),
}

TOOLS = {
    "adjustable_wrench": Tool(
        id="adjustable_wrench",
        label="adjustable wrench",
        phrase="the silver adjustable wrench",
        works_on={"loo_seat", "flush_handle", "paper_holder"},
        child_safe_help=True,
        tags={"wrench", "repair"},
    ),
    "basin_wrench": Tool(
        id="basin_wrench",
        label="basin wrench",
        phrase="the long basin wrench",
        works_on={"loo_seat"},
        child_safe_help=False,
        tags={"wrench", "repair"},
    ),
    "small_spanner": Tool(
        id="small_spanner",
        label="small spanner",
        phrase="the little spanner wrench",
        works_on={"flush_handle", "paper_holder"},
        child_safe_help=True,
        tags={"wrench", "repair"},
    ),
    "pipe_wrench": Tool(
        id="pipe_wrench",
        label="pipe wrench",
        phrase="the heavy pipe wrench",
        works_on=set(),
        child_safe_help=False,
        tags={"wrench", "repair"},
    ),
}

PLAY_KITS = {
    "classic_red_box": PlayKit(
        id="classic_red_box",
        label="toolbox",
        phrase="a classic red toy toolbox",
        classic=True,
        has_toy_wrench=True,
        toy_color="red",
        ending_play="pretending to mend a squeaky stool and a sleepy doll bed",
        tags={"sharing", "toy_wrench"},
    ),
    "blue_repair_tin": PlayKit(
        id="blue_repair_tin",
        label="tin",
        phrase="a classic blue repair tin",
        classic=True,
        has_toy_wrench=True,
        toy_color="blue",
        ending_play="taking turns fixing an imaginary train station made of blocks",
        tags={"sharing", "toy_wrench"},
    ),
    "cardboard_garage": PlayKit(
        id="cardboard_garage",
        label="garage box",
        phrase="a cardboard garage box of play tools",
        classic=False,
        has_toy_wrench=True,
        toy_color="yellow",
        ending_play="repairing a line of toy cars parked by the skirting board",
        tags={"sharing", "toy_wrench"},
    ),
    "doctor_bag": PlayKit(
        id="doctor_bag",
        label="doctor bag",
        phrase="a little doctor bag with a toy stethoscope",
        classic=False,
        has_toy_wrench=False,
        toy_color="green",
        ending_play="checking every teddy for a pretend heartbeat",
        tags={"doctor"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Ella", "Zoe"]
BOY_NAMES = ["Ben", "Sam", "Leo", "Finn", "Jack", "Theo"]
OWNER_TRAITS = ["careful", "thoughtful", "quiet", "earnest"]
FRIEND_TRAITS = ["kind", "gentle", "patient", "cheerful"]


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    kit: str
    owner_name: str
    owner_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    owner_trait: str
    friend_trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "loo": [(
        "What is a loo?",
        "A loo is another word for a toilet or bathroom. Families use it every day, so small loose parts get noticed quickly."
    )],
    "wrench": [(
        "What does a wrench do?",
        "A wrench helps turn nuts or bolts so something can be tightened or loosened. Grown-ups use the right size so the tool can grip properly."
    )],
    "sharing": [(
        "What does sharing mean?",
        "Sharing means letting someone else use something kindly and fairly. It works best when everyone knows the item will be cared for and returned."
    )],
    "repair": [(
        "Why do loose things need fixing?",
        "Loose things can wobble, slip, or stop working the right way. Tightening them early keeps everyday jobs simple and safe."
    )],
    "misunderstanding": [(
        "What is a misunderstanding?",
        "A misunderstanding happens when two people hear or mean different things. Talking clearly and asking one more question can fix it."
    )],
    "toy_wrench": [(
        "Why is a toy wrench different from a real wrench?",
        "A toy wrench is for pretend play, so it is light and safe for children. A real wrench is a tool for actual repairs and should be used with a grown-up."
    )],
}
KNOWLEDGE_ORDER = ["loo", "wrench", "repair", "misunderstanding", "sharing", "toy_wrench"]


def generation_prompts(world: World) -> list[str]:
    owner = world.facts["owner"]
    friend = world.facts["friend"]
    parent = world.facts["parent"]
    problem = world.facts["problem"]
    kit = world.facts["kit"]
    return [
        'Write a short slice-of-life story for a 3-to-5-year-old that includes the words "classic", "wrench", and "loo".',
        f"Tell a gentle misunderstanding story where {owner.id} and {friend.id} are playing with {kit.phrase}, {parent.label_word} asks for a wrench to fix a {problem.label}, and everyone ends with a happy sharing moment.",
        "Write a simple home story with a mix-up over which wrench someone means, a calm clarification, and an ending that shows both repair and kindness.",
    ]


def pair_noun(owner: Entity, friend: Entity) -> str:
    if owner.type == "girl" and friend.type == "girl":
        return "two girls"
    if owner.type == "boy" and friend.type == "boy":
        return "two boys"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    owner = world.facts["owner"]
    friend = world.facts["friend"]
    parent = world.facts["parent"]
    problem = world.facts["problem"]
    tool = world.facts["tool"]
    kit = world.facts["kit"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(owner, friend)}, {owner.id} and {friend.id}, and their {pw}. They were playing outside the loo when a small household job interrupted the game."
        ),
        (
            "What was the misunderstanding?",
            f"When {pw} called for a wrench, {owner.id} thought the grown-up meant the toy wrench from {kit.phrase}. {owner.pronoun().capitalize()} worried the favorite play tool would be taken away, but the grown-up really meant {tool.phrase}."
        ),
        (
            f"Why did {pw} need a wrench?",
            f"{pw.capitalize()} needed it to fix the {problem.label}. The loo fixture was loose, so it needed a careful tighten to sit straight again."
        ),
        (
            f"How was the misunderstanding fixed?",
            f"{pw.capitalize()} came out, saw {owner.id}'s worried face, and explained exactly which wrench was needed. That clear explanation turned the hurt feeling into relief because the toy wrench was never being taken away."
        ),
    ]
    if world.facts.get("repaired"):
        qa.append((
            "What happened after the grown-up got the right tool?",
            f"{pw.capitalize()} used {tool.phrase} and fixed the loo problem while the children watched from the doorway. The quiet repair showed that the real wrench had a different job from the toy one."
        ))
    if world.facts.get("shared"):
        qa.append((
            f"How did {owner.id} show sharing at the end?",
            f"{owner.id} offered the toy wrench to {friend.id} first. That mattered because once the misunderstanding was gone, sharing felt safe and kind instead of scary."
        ))
        qa.append((
            "How did the story end?",
            f"It ended happily with the loo fixed and the children back on the rug together. The same wrench word that caused the mix-up became part of a calm, shared game."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"loo", "wrench", "sharing", "misunderstanding", "repair"}
    kit = world.facts["kit"]
    if kit.has_toy_wrench:
        tags.add("toy_wrench")
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
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.safe_for_child:
            bits.append("safe_for_child=True")
        if e.plastic:
            bits.append("plastic=True")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="flat_hall",
        problem="loo_seat",
        tool="adjustable_wrench",
        kit="classic_red_box",
        owner_name="Mia",
        owner_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        parent="mother",
        owner_trait="careful",
        friend_trait="kind",
    ),
    StoryParams(
        place="small_house",
        problem="flush_handle",
        tool="small_spanner",
        kit="blue_repair_tin",
        owner_name="Leo",
        owner_gender="boy",
        friend_name="Ava",
        friend_gender="girl",
        parent="father",
        owner_trait="thoughtful",
        friend_trait="patient",
    ),
    StoryParams(
        place="grandma_house",
        problem="paper_holder",
        tool="small_spanner",
        kit="cardboard_garage",
        owner_name="Nora",
        owner_gender="girl",
        friend_name="Sam",
        friend_gender="boy",
        parent="mother",
        owner_trait="earnest",
        friend_trait="cheerful",
    ),
]


def explain_rejection(place: Place, problem: Problem, tool: Tool, kit: PlayKit) -> str:
    if not problem_possible(place, problem):
        return (
            f"(No story: {problem.label} is not a sensible problem for {place.label}. "
            f"Pick a loo problem that this place actually affords.)"
        )
    if not misunderstanding_possible(kit):
        return (
            f"(No story: {kit.phrase} has no toy wrench, so there is no honest misunderstanding over the word "
            f'"wrench". Pick a play kit with a toy wrench.)'
        )
    if not tool_fits(problem, tool):
        return (
            f"(No story: {tool.label} is the wrong tool for the {problem.label}. "
            f"The repair must be physically plausible, so choose a fitting wrench.)"
        )
    return "(No story: this combination is unreasonable.)"


ASP_RULES = r"""
problem_possible(Place, Problem) :- place(Place), problem(Problem), allows(Place, Problem).
tool_fits(Problem, Tool) :- problem(Problem), tool(Tool), works_on(Tool, Problem).
misunderstanding_possible(Kit) :- playkit(Kit), has_toy_wrench(Kit).

valid(Place, Problem, Tool, Kit) :-
    problem_possible(Place, Problem),
    tool_fits(Problem, Tool),
    misunderstanding_possible(Kit).

outcome(shared_fix) :- chosen_place(P), chosen_problem(Pr), chosen_tool(T), chosen_kit(K),
                       valid(P, Pr, T, K).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for problem_id in sorted(place.allows):
            lines.append(asp.fact("allows", place_id, problem_id))
    for problem_id in PROBLEMS:
        lines.append(asp.fact("problem", problem_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for problem_id in sorted(tool.works_on):
            lines.append(asp.fact("works_on", tool_id, problem_id))
    for kit_id, kit in PLAY_KITS.items():
        lines.append(asp.fact("playkit", kit_id))
        if kit.has_toy_wrench:
            lines.append(asp.fact("has_toy_wrench", kit_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_kit", params.kit),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "invalid"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if mismatches:
        rc = 1
        print(f"MISMATCH in outcome model on {len(mismatches)} scenarios.")
    else:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Verify failed: generated story was empty.)")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a wrench misunderstanding by the loo, ending in repair and sharing."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--kit", choices=PLAY_KITS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_id = args.place
    problem_id = args.problem
    tool_id = args.tool
    kit_id = args.kit

    if place_id and problem_id and not problem_possible(PLACES[place_id], PROBLEMS[problem_id]):
        raise StoryError(explain_rejection(PLACES[place_id], PROBLEMS[problem_id], TOOLS.get(tool_id or "adjustable_wrench", TOOLS["adjustable_wrench"]), PLAY_KITS.get(kit_id or "classic_red_box", PLAY_KITS["classic_red_box"])))
    if kit_id and not misunderstanding_possible(PLAY_KITS[kit_id]):
        place = PLACES[place_id] if place_id else next(iter(PLACES.values()))
        problem = PROBLEMS[problem_id] if problem_id else next(iter(PROBLEMS.values()))
        tool = TOOLS[tool_id] if tool_id else next(iter(TOOLS.values()))
        raise StoryError(explain_rejection(place, problem, tool, PLAY_KITS[kit_id]))
    if problem_id and tool_id and not tool_fits(PROBLEMS[problem_id], TOOLS[tool_id]):
        place = PLACES[place_id] if place_id else next(iter(PLACES.values()))
        kit = PLAY_KITS[kit_id] if kit_id else PLAY_KITS["classic_red_box"]
        raise StoryError(explain_rejection(place, PROBLEMS[problem_id], TOOLS[tool_id], kit))

    combos = [
        combo for combo in valid_combos()
        if (place_id is None or combo[0] == place_id)
        and (problem_id is None or combo[1] == problem_id)
        and (tool_id is None or combo[2] == tool_id)
        and (kit_id is None or combo[3] == kit_id)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    chosen_place, chosen_problem, chosen_tool, chosen_kit = rng.choice(sorted(combos))
    owner_name, owner_gender = pick_kid(rng)
    friend_name, friend_gender = pick_kid(rng, avoid=owner_name)
    parent = args.parent or rng.choice(["mother", "father"])
    owner_trait = rng.choice(OWNER_TRAITS)
    friend_trait = rng.choice(FRIEND_TRAITS)
    return StoryParams(
        place=chosen_place,
        problem=chosen_problem,
        tool=chosen_tool,
        kit=chosen_kit,
        owner_name=owner_name,
        owner_gender=owner_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        owner_trait=owner_trait,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Invalid problem: {params.problem})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Invalid tool: {params.tool})")
    if params.kit not in PLAY_KITS:
        raise StoryError(f"(Invalid kit: {params.kit})")

    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    kit = PLAY_KITS[params.kit]
    if not valid_story(place, problem, tool, kit):
        raise StoryError(explain_rejection(place, problem, tool, kit))

    world = tell(
        place=place,
        problem=problem,
        tool=tool,
        kit=kit,
        owner_name=params.owner_name,
        owner_gender=params.owner_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        owner_trait=params.owner_trait,
        friend_trait=params.friend_trait,
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
        print(f"{len(combos)} compatible (place, problem, tool, kit) combos:\n")
        for place, problem, tool, kit in combos:
            print(f"  {place:12} {problem:12} {tool:18} {kit}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.owner_name} & {p.friend_name}: {p.problem} with {p.tool} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
