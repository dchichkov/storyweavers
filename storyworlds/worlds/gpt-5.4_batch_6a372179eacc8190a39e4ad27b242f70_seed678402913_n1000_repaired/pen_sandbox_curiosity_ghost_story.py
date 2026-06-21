#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pen_sandbox_curiosity_ghost_story.py
===============================================================

A standalone story world for a gentle "ghost story" in a sandbox.

Seed:
- word: pen
- setting: sandbox
- feature: curiosity
- style: ghost story

The source-tale premise rebuilt here is:

    A child smooths a sandbox and leaves feeling proud. Later, strange marks
    appear in the sand. In the dim light, the child imagines a ghost. Curiosity
    grows stronger than fear, so the child and a grown-up investigate carefully.
    They use a pen to make a little note or plan, watch for clues, and discover a
    real, small cause such as a snail, a cat, or a low branch dragging in the
    sand. The ending keeps the delicious spooky mood while proving what changed:
    the child now knows how to wonder first and panic later.

The world model keeps a simple physical state:
- the sandbox can be smoothed, marked, and observed
- a source can make marks with a distinctive shape
- a tool can or cannot reveal the source reasonably

It also keeps emotional "memes":
- fear, curiosity, relief, pride, wonder, trust

The story is state-driven, not frozen text with noun swaps.
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

# Make the shared result containers importable when this script is run directly
# from this nested directory (storyworlds/worlds/gpt-5.4/).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"           # "character" | "thing"
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
# Config dataclasses
# ---------------------------------------------------------------------------
@dataclass
class Mystery:
    id: str
    setup: str
    oddity: str
    rumor: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    phrase: str
    track_shape: str
    sound: str
    method: str
    reveal_line: str
    makes_loops: bool = False
    makes_paw: bool = False
    makes_sweep: bool = False
    night_active: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    finds_loops: bool = False
    finds_paw: bool = False
    finds_sweep: bool = False
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
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
# Rule engine
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_marks_raise_wonder(world: World) -> list[str]:
    box = world.get("sandbox")
    if box.meters["marked"] < THRESHOLD:
        return []
    sig = ("wonder",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child = world.get("child")
    child.memes["wonder"] += 1
    child.memes["fear"] += 1
    child.memes["curiosity"] += 1
    return []


def _r_curiosity_enables_search(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["curiosity"] < THRESHOLD:
        return []
    sig = ("search",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["looking"] += 1
    return []


def _r_reveal_brings_relief(world: World) -> list[str]:
    if not world.facts.get("revealed"):
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child = world.get("child")
    helper = world.get("helper")
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    child.memes["fear"] = 0.0
    child.memes["trust"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="marks_raise_wonder", tag="emotional", apply=_r_marks_raise_wonder),
    Rule(name="curiosity_enables_search", tag="action", apply=_r_curiosity_enables_search),
    Rule(name="reveal_brings_relief", tag="emotional", apply=_r_reveal_brings_relief),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                # no narration payload, but state may have changed
                pass
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def tool_matches_source(tool: Tool, source: Source) -> bool:
    return (
        (source.makes_loops and tool.finds_loops)
        or (source.makes_paw and tool.finds_paw)
        or (source.makes_sweep and tool.finds_sweep)
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mystery_id in MYSTERIES:
        for source_id, source in SOURCES.items():
            if not source.night_active:
                continue
            for tool_id, tool in TOOLS.items():
                if tool_matches_source(tool, source):
                    combos.append((mystery_id, source_id, tool_id))
    return combos


def explain_rejection(source: Source, tool: Tool) -> str:
    return (
        f"(No story: {tool.phrase} would not honestly reveal {source.phrase}. "
        f"The investigation tool has to match the kind of mark in the sandbox.)"
    )


# ---------------------------------------------------------------------------
# Prediction helpers
# ---------------------------------------------------------------------------
def predict_marks(world: World, source_id: str) -> dict:
    sim = world.copy()
    make_marks(sim, SOURCES[source_id], narrate=False)
    return {
        "marked": sim.get("sandbox").meters["marked"] >= THRESHOLD,
        "track_shape": sim.facts.get("track_shape", ""),
    }


def predict_reveal(world: World, source_id: str, tool_id: str) -> bool:
    return tool_matches_source(TOOLS[tool_id], SOURCES[source_id])


# ---------------------------------------------------------------------------
# Verbs / screenplay beats
# ---------------------------------------------------------------------------
def setup_evening(world: World, child: Entity, helper: Entity, mystery: Mystery, pen: Entity) -> None:
    child.memes["pride"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"At the edge of the yard stood a sandbox that looked deep and golden in the late light. "
        f"{child.id} knelt beside it with {pen.phrase} and a little scrap of paper, "
        f"making a tiny map of castles and treasure paths."
    )
    world.say(
        f"{mystery.setup} {helper.label_word.capitalize()} sat nearby on the steps, "
        f"close enough to hear every small sigh and every delighted idea."
    )


def smooth_sand(world: World, child: Entity) -> None:
    box = world.get("sandbox")
    box.meters["smooth"] += 1
    world.say(
        f"Before going inside, {child.id} patted the sand flat with careful hands until it looked "
        f"like a quiet yellow blanket."
    )


def night_strangeness(world: World, mystery: Mystery) -> None:
    world.say(
        f"By the time the sky turned purple, the sandbox did not seem like an ordinary sandbox anymore. "
        f"{mystery.oddity}"
    )
    world.say(mystery.rumor)


def make_marks(world: World, source: Source, narrate: bool = True) -> None:
    box = world.get("sandbox")
    box.meters["marked"] += 1
    world.facts["track_shape"] = source.track_shape
    world.facts["mark_source"] = source.id
    if narrate:
        world.say(
            f"Across the smooth sand lay {source.track_shape}. In the hush of evening, they looked almost written there by a ghost."
        )
    propagate(world, narrate=False)


def notice_and_wonder(world: World, child: Entity, pen: Entity, mystery: Mystery) -> None:
    pred = predict_marks(world, world.facts["source_cfg"].id)
    world.facts["predicted_marks"] = pred["marked"]
    child.memes["fear"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"The next time {child.id} looked, the smooth sand was changed. {child.pronoun().capitalize()} "
        f"stared so hard that {child.pronoun('possessive')} fingers squeezed around the {pen.label}."
    )
    world.say(
        f'"Did a ghost come to visit the sandbox?" {child.pronoun()} whispered. '
        f"The question felt chilly, but it also made {child.pronoun('object')} want to know more."
    )
    world.say(
        f"{child.id} bent close and used the {pen.label} to draw the strange shapes on the paper, "
        f"as if copying them might help the mystery behave."
    )


def invite_investigation(world: World, helper: Entity, child: Entity, tool: Tool) -> None:
    helper.memes["calm"] += 1
    child.memes["trust"] += 1
    world.say(
        f"{helper.label_word.capitalize()} came over and crouched beside {child.id}. "
        f'"It does look spooky," {helper.pronoun()} said, "but spooky is not the same as magic. '
        f'Let us be curious and look carefully."'
    )
    world.say(
        f"Together they made a small plan. {child.id} tapped the paper with the pen, "
        f"and {helper.label_word} chose {tool.phrase} to help them search."
    )


def investigate(world: World, child: Entity, helper: Entity, tool: Tool, source: Source) -> None:
    child.meters["looking"] += 1
    helper.meters["looking"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They waited very still beside the sandbox. The air was soft, the shadows were long, "
        f"and every rustle sounded bigger than it really was."
    )
    world.say(
        f"Then {helper.label_word} {tool.action}. {source.sound}"
    )


def reveal(world: World, child: Entity, source: Source) -> None:
    world.facts["revealed"] = True
    world.facts["ghost_real"] = False
    propagate(world, narrate=False)
    world.say(
        source.reveal_line
    )
    world.say(
        f"{child.id} let out a breath that had been hiding in {child.pronoun('possessive')} chest. "
        f"It was not a ghost at all. It was {source.phrase}, making the very same marks they had copied with the pen."
    )


def ending(world: World, child: Entity, helper: Entity, mystery: Mystery, pen: Entity) -> None:
    child.memes["lesson"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{helper.label_word.capitalize()} smiled and smoothed one corner of the paper. "
        f'"Your pen made a good detective note," {helper.pronoun()} said. '
        f'"When something feels strange, curiosity helps us see what is really there."'
    )
    world.say(
        f"{child.id} nodded and drew one more neat line on the page: Not a ghost. "
        f"Just a nighttime visitor."
    )
    world.say(mystery.ending_image)


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
MYSTERIES = {
    "whispers": Mystery(
        id="whispers",
        setup="The sandbox held two crumbly towers and a crooked road for toy wagons",
        oddity="A pale wind slid over it, and the shadows around the wooden rim looked full of little secrets.",
        rumor="Old stories from bigger children floated back into mind: sometimes, they said, the yard had sandbox ghosts that wrote messages after bedtime.",
        ending_image="Soon the sandbox looked mysterious in a friendly way, and the night no longer felt full of hiding things. It felt full of small lives and clues.",
        tags={"ghost", "sandbox"},
    ),
    "moonlight": Mystery(
        id="moonlight",
        setup="A thin moon was climbing, and every grain of sand seemed to shine on its own",
        oddity="Moonlight gathered in the hollow places and made the sandbox look like a silver bowl.",
        rumor="It was easy to imagine that moonlit ghosts might step softly through such a place and leave secret writing behind.",
        ending_image="The moon still made the sandbox gleam, but now it looked less like a haunted bowl and more like a notebook for the night.",
        tags={"ghost", "moon"},
    ),
    "hush": Mystery(
        id="hush",
        setup="Even the yard seemed to be listening, as if the sandbox were waiting for one last story before dark",
        oddity="The quiet around it was so deep that every tiny scrape felt important.",
        rumor="In that hush, a curious mind could almost believe that invisible hands had come to draw in the sand.",
        ending_image="When the stars came out, the sandbox still felt deliciously spooky, only now the spooky part had an answer. That made it better, not smaller.",
        tags={"ghost", "night"},
    ),
}

SOURCES = {
    "snail": Source(
        id="snail",
        label="snail",
        phrase="a small garden snail",
        track_shape="thin silver loops and a sleepy winding trail",
        sound="For a long moment nothing happened. Then something small glimmered near the rim.",
        method="watching quietly for a slow trail-maker",
        reveal_line="A snail was inching along the edge, drawing wet loops across the sand with its soft body.",
        makes_loops=True,
        night_active=True,
        tags={"snail", "tracks", "night"},
    ),
    "cat": Source(
        id="cat",
        label="cat",
        phrase="the neighbor's cat",
        track_shape="round paw prints with a tail-dragged line between them",
        sound="A soft thump came from the fence, and two bright eyes blinked in the dark.",
        method="using light to catch a quick visitor",
        reveal_line="The neighbor's cat hopped down, padded through the sandbox, and flicked its tail in a line behind it.",
        makes_paw=True,
        night_active=True,
        tags={"cat", "tracks", "night"},
    ),
    "branch": Source(
        id="branch",
        label="branch",
        phrase="the low willow branch above the yard",
        track_shape="long sweeping marks and little leaf taps",
        sound="The leaves shivered, though the wind had seemed asleep a moment before.",
        method="watching the shadow and movement overhead",
        reveal_line="A low willow branch swayed over the sandbox, and its leaves brushed the sand in soft dragging strokes.",
        makes_sweep=True,
        night_active=True,
        tags={"tree", "wind", "night"},
    ),
}

TOOLS = {
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        action="clicked on the flashlight and swept a gentle beam over the sand",
        finds_paw=True,
        tags={"flashlight", "light"},
    ),
    "waiting": Tool(
        id="waiting",
        label="stillness",
        phrase="their patient stillness",
        action="held very still and watched without talking at all",
        finds_loops=True,
        tags={"waiting", "observe"},
    ),
    "listening": Tool(
        id="listening",
        label="careful listening",
        phrase="careful listening under the tree",
        action="tilted both their heads and listened while watching the shadow above the sandbox",
        finds_sweep=True,
        tags={"listening", "tree"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["curious", "careful", "quiet", "thoughtful", "brave", "observant"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    mystery: str
    source: str
    tool: str
    child_name: str
    child_gender: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a story that feels spooky and mysterious. In gentle ghost stories for young children, the scary feeling usually turns out to have a safe explanation."
        )
    ],
    "sandbox": [
        (
            "What is a sandbox?",
            "A sandbox is a box or small area filled with sand for children to dig in and build with. Sand also shows tracks and marks very easily."
        )
    ],
    "snail": [
        (
            "How can a snail leave a trail?",
            "A snail moves very slowly on a wet, slippery foot. As it slides along, it can leave a shiny trail behind it."
        )
    ],
    "cat": [
        (
            "Why do cats leave paw prints?",
            "Cats leave paw prints because their soft feet press into loose dirt or sand. If the ground is smooth first, the prints are easy to see."
        )
    ],
    "tree": [
        (
            "How can a branch make marks in sand?",
            "A low branch can brush or drag across soft sand when the wind moves it. The leaves and twigs can make long lines and little taps."
        )
    ],
    "flashlight": [
        (
            "What does a flashlight help you do?",
            "A flashlight helps you see in the dark by shining a beam of light. It can make hidden details easier to notice."
        )
    ],
    "waiting": [
        (
            "Why can waiting quietly help you solve a mystery?",
            "Waiting quietly gives you time to notice small movements and sounds. If you rush, you may miss the clue that explains everything."
        )
    ],
    "observe": [
        (
            "What does it mean to observe carefully?",
            "Observing carefully means looking and listening closely instead of guessing too fast. It helps you learn what is really happening."
        )
    ],
    "light": [
        (
            "Why do shadows look stranger at night?",
            "Shadows can look stranger at night because the light is dim and uneven. When you cannot see clearly, ordinary things can seem mysterious."
        )
    ],
    "pen": [
        (
            "What can a pen help you do during an investigation?",
            "A pen can help you draw what you see or write a note about it. That way, you can remember clues and compare them later."
        )
    ],
}

KNOWLEDGE_ORDER = ["ghost", "sandbox", "snail", "cat", "tree", "flashlight", "waiting", "observe", "light", "pen"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    source = f["source_cfg"]
    tool = f["tool_cfg"]
    mystery = f["mystery_cfg"]
    return [
        'Write a gentle ghost story for a 3-to-5-year-old set in a sandbox that includes the word "pen" and centers curiosity instead of panic.',
        f"Tell a spooky-but-safe story where {child.id} sees strange marks in a sandbox, uses a pen to copy the clues, and solves the mystery with {helper.label_word}'s help.",
        f"Write a child-facing mystery in moonlit, hush-filled language where the supposed ghost turns out to be {source.phrase}, discovered through {tool.phrase}.",
        f"Create a tiny ghost-story world where a sandbox feels haunted for a moment, then becomes understandable again because {mystery.id} curiosity leads the child to look carefully.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    source = f["source_cfg"]
    tool = f["tool_cfg"]
    mystery = f["mystery_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a {child.type} who notices strange marks in the sandbox, and {helper.label_word} who helps investigate. The story follows fear turning into curiosity."
        ),
        (
            "Why did the sandbox seem spooky?",
            f"The sand had been smoothed flat, and later it showed {source.track_shape}. In the dim evening light, those fresh marks looked like secret ghost writing."
        ),
        (
            "How did the pen matter in the story?",
            f"{child.id} held a pen and copied the odd shapes onto paper. That turned the pen into a detective tool, because writing the clue down helped {child.pronoun('object')} focus on what was really there."
        ),
        (
            f"Why did {child.id} keep looking instead of running away?",
            f"{child.id} did feel scared, but curiosity grew at the same time. {helper.label_word.capitalize()} also stayed calm and suggested looking carefully, which made the mystery feel solvable."
        ),
    ]
    if f.get("revealed"):
        qa.append(
            (
                "What was really making the marks?",
                f"It was {source.phrase}. The ghost idea disappeared once they watched carefully enough to see the real source making the same pattern."
            )
        )
        qa.append(
            (
                f"How did they solve the mystery?",
                f"They used {tool.phrase} and paid close attention to the sandbox. That method matched the kind of clue they had, so it revealed the truth instead of leaving them guessing."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with relief and wonder instead of fear. The sandbox still felt mysterious in a fun ghost-story way, but now {child.id} knew what had changed and why."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ghost", "sandbox", "pen", "light"}
    tags |= set(f["source_cfg"].tags)
    tags |= set(f["tool_cfg"].tags)
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
# Telling
# ---------------------------------------------------------------------------
def tell(
    mystery: Mystery,
    source: Source,
    tool: Tool,
    child_name: str = "Lily",
    child_gender: str = "girl",
    helper_type: str = "mother",
    trait: str = "curious",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            label=child_name,
            traits=[trait],
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the parent",
        )
    )
    sandbox = world.add(
        Entity(
            id="sandbox",
            kind="thing",
            type="sandbox",
            label="sandbox",
            phrase="the sandbox",
            tags={"sandbox"},
        )
    )
    pen = world.add(
        Entity(
            id="pen",
            kind="thing",
            type="pen",
            label="pen",
            phrase="a blue pen",
            tags={"pen"},
        )
    )
    world.facts.update(
        child=child,
        helper=helper,
        sandbox=sandbox,
        pen=pen,
        mystery_cfg=mystery,
        source_cfg=source,
        tool_cfg=tool,
        revealed=False,
        ghost_real=None,
    )

    setup_evening(world, child, helper, mystery, pen)
    smooth_sand(world, child)

    world.para()
    night_strangeness(world, mystery)
    make_marks(world, source)
    notice_and_wonder(world, child, pen, mystery)

    world.para()
    invite_investigation(world, helper, child, tool)
    investigate(world, child, helper, tool, source)
    reveal(world, child, source)

    world.para()
    ending(world, child, helper, mystery, pen)

    world.facts.update(
        outcome="revealed",
        source_seen=True,
        tool_worked=True,
        sandbox_marked=sandbox.meters["marked"] >= THRESHOLD,
        curiosity_won=child.memes["curiosity"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} source={world.facts.get('source_cfg').id} tool={world.facts.get('tool_cfg').id}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        mystery="whispers",
        source="snail",
        tool="waiting",
        child_name="Lily",
        child_gender="girl",
        helper_type="mother",
        trait="curious",
    ),
    StoryParams(
        mystery="moonlight",
        source="cat",
        tool="flashlight",
        child_name="Ben",
        child_gender="boy",
        helper_type="father",
        trait="observant",
    ),
    StoryParams(
        mystery="hush",
        source="branch",
        tool="listening",
        child_name="Maya",
        child_gender="girl",
        helper_type="mother",
        trait="thoughtful",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Valid investigation pairs: the tool must match the mark-making source.
valid(M, S, T) :- mystery(M), source(S), tool(T), night_active(S), matches(S, T).

% One outcome in this world: the mystery is revealed when the chosen pair matches.
revealed :- chosen_source(S), chosen_tool(T), matches(S, T).
outcome(revealed) :- revealed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for sid, source in SOURCES.items():
        lines.append(asp.fact("source", sid))
        if source.night_active:
            lines.append(asp.fact("night_active", sid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for sid, source in SOURCES.items():
        for tid, tool in TOOLS.items():
            if tool_matches_source(tool, source):
                lines.append(asp.fact("matches", sid, tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_source", params.source),
        asp.fact("chosen_tool", params.tool),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


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
    for p in cases:
        if asp_outcome(p) != "revealed":
            rc = 1
            print(f"MISMATCH in outcome for curated case: {p}")
            break
    else:
        print(f"OK: outcome model matches on {len(cases)} curated scenarios.")

    # Smoke test normal generation and rendering.
    try:
        sample = generate(
            StoryParams(
                mystery="whispers",
                source="snail",
                tool="waiting",
                child_name="Lily",
                child_gender="girl",
                helper_type="mother",
                trait="curious",
                seed=123,
            )
        )
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: generation smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story sandbox world: a child sees spooky marks, uses curiosity and a pen, and finds a real answer."
    )
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--source", choices=sorted(SOURCES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.tool:
        source = SOURCES[args.source]
        tool = TOOLS[args.tool]
        if not tool_matches_source(tool, source):
            raise StoryError(explain_rejection(source, tool))

    combos = [
        c for c in valid_combos()
        if (args.mystery is None or c[0] == args.mystery)
        and (args.source is None or c[1] == args.source)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mystery_id, source_id, tool_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        mystery=mystery_id,
        source=source_id,
        tool=tool_id,
        child_name=name,
        child_gender=gender,
        helper_type=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mystery not in MYSTERIES:
        raise StoryError(f"(Unknown mystery: {params.mystery})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if not tool_matches_source(TOOLS[params.tool], SOURCES[params.source]):
        raise StoryError(explain_rejection(SOURCES[params.source], TOOLS[params.tool]))

    world = tell(
        mystery=MYSTERIES[params.mystery],
        source=SOURCES[params.source],
        tool=TOOLS[params.tool],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
        trait=params.trait,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mystery, source, tool) combos:\n")
        for mystery, source, tool in combos:
            print(f"  {mystery:10} {source:8} {tool}")
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
            header = f"### {p.child_name}: {p.source} in the sandbox ({p.mystery}, {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
