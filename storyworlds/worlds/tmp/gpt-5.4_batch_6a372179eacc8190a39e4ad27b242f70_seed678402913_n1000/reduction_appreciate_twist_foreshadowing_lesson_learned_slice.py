#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/reduction_appreciate_twist_foreshadowing_lesson_learned_slice.py
=============================================================================================

A standalone storyworld about a child cleaning a crowded room to make space for
something new. The story turns on a small "reduction" of clutter that reveals a
forgotten keepsake, and the child learns to appreciate both the room and the
memory hidden inside it.

The domain is intentionally small and constraint-checked:

- a goal needs a particular room zone to be cleared
- only clutter in that zone can honestly block the goal
- only a matching storage tool can tidy that clutter
- only keepsakes plausibly hidden in that clutter can be rediscovered
- only a fitting restore method can sensibly fix the keepsake

The resulting stories stay close to slice-of-life: a room, a parent, a chore,
a small twist, and a warm ending image.

Run it
------
    python storyworlds/worlds/gpt-5.4/reduction_appreciate_twist_foreshadowing_lesson_learned_slice.py
    python storyworlds/worlds/gpt-5.4/reduction_appreciate_twist_foreshadowing_lesson_learned_slice.py --goal reading_nook
    python storyworlds/worlds/gpt-5.4/reduction_appreciate_twist_foreshadowing_lesson_learned_slice.py --goal art_desk --clutter stuffed_animals
    python storyworlds/worlds/gpt-5.4/reduction_appreciate_twist_foreshadowing_lesson_learned_slice.py --all
    python storyworlds/worlds/gpt-5.4/reduction_appreciate_twist_foreshadowing_lesson_learned_slice.py --qa
    python storyworlds/worlds/gpt-5.4/reduction_appreciate_twist_foreshadowing_lesson_learned_slice.py --verify
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
ZONES = {"floor", "shelf", "desk", "bed"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    zone: str = ""
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
class Goal:
    id: str
    label: str
    zone: str
    setup: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clutter:
    id: str
    label: str
    phrase: str
    zone: str
    reduction_word: str
    storage: str
    peek: str
    hideable: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    zone: str
    handles: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    maker: str
    issue: str
    clue: str
    appreciate_line: str
    use_for: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class RestoreMethod:
    id: str
    label: str
    action: str
    fixes: set[str] = field(default_factory=set)
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


def _r_space(world: World) -> list[str]:
    room = world.get("room")
    pile = world.get("pile")
    if pile.meters["clutter"] >= THRESHOLD:
        return []
    sig = ("space", pile.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["free_space"] += 1
    child = world.get("child")
    child.memes["relief"] += 1
    return ["__space__"]


def _r_appreciation(world: World) -> list[str]:
    keepsake = world.get("keepsake")
    child = world.get("child")
    if keepsake.meters["restored"] < THRESHOLD:
        return []
    sig = ("appreciation", keepsake.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["appreciation"] += 1
    child.memes["gratitude"] += 1
    return ["__appreciation__"]


CAUSAL_RULES = [
    Rule(name="space", tag="physical", apply=_r_space),
    Rule(name="appreciation", tag="emotional", apply=_r_appreciation),
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


def goal_blocked(goal: Goal, clutter: Clutter) -> bool:
    return goal.zone == clutter.zone


def tool_fits(clutter: Clutter, tool: Tool) -> bool:
    return clutter.id in tool.handles and clutter.zone == tool.zone


def keepsake_hidden_in(clutter: Clutter, keepsake: Keepsake) -> bool:
    return keepsake.id in clutter.hideable


def method_fits(keepsake: Keepsake, method: RestoreMethod) -> bool:
    return keepsake.issue in method.fixes


def valid_combo(goal: Goal, clutter: Clutter, tool: Tool, keepsake: Keepsake, method: RestoreMethod) -> bool:
    return (
        goal_blocked(goal, clutter)
        and tool_fits(clutter, tool)
        and keepsake_hidden_in(clutter, keepsake)
        and method_fits(keepsake, method)
        and goal.id in keepsake.use_for
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for goal_id, goal in GOALS.items():
        for clutter_id, clutter in CLUTTER.items():
            for tool_id, tool in TOOLS.items():
                for keepsake_id, keepsake in KEEPSAKES.items():
                    for method_id, method in METHODS.items():
                        if valid_combo(goal, clutter, tool, keepsake, method):
                            combos.append((goal_id, clutter_id, tool_id, keepsake_id, method_id))
    return combos


@dataclass
class StoryParams:
    goal: str
    clutter: str
    tool: str
    keepsake: str
    method: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


GOALS = {
    "reading_nook": Goal(
        id="reading_nook",
        label="a reading nook by the window",
        zone="floor",
        setup="wanted to spread a quilt by the window and make a reading nook there",
        ending="curled up in the new reading nook with a book and the keepsake close by",
        tags={"reading", "room"},
    ),
    "art_desk": Goal(
        id="art_desk",
        label="a clear art desk",
        zone="desk",
        setup="wanted a clear desk for drawing after school",
        ending="sat at the clear desk, drawing carefully under the keepsake",
        tags={"art", "room"},
    ),
    "sleepover_spot": Goal(
        id="sleepover_spot",
        label="a tidy spot for a cousin to sleep",
        zone="bed",
        setup="wanted to make room on the bed for a cousin who would visit that evening",
        ending="smoothed the bed for the visit and set the keepsake where everyone could see it",
        tags={"sleepover", "room"},
    ),
}

CLUTTER = {
    "blocks": Clutter(
        id="blocks",
        label="blocks",
        phrase="a wide scatter of blocks",
        zone="floor",
        reduction_word="a reduction in the block pile",
        storage="into a rolling crate",
        peek="something bright peeking between two wooden towers",
        hideable={"paper_star_mobile"},
        tags={"tidy", "blocks"},
    ),
    "papers": Clutter(
        id="papers",
        label="papers",
        phrase="a leaning stack of papers and drawings",
        zone="desk",
        reduction_word="a reduction in the paper mountain",
        storage="into a blue folder",
        peek="a loop of ribbon showing under a bent corner",
        hideable={"ribbon_bookmark"},
        tags={"tidy", "paper"},
    ),
    "stuffed_animals": Clutter(
        id="stuffed_animals",
        label="stuffed animals",
        phrase="a soft hill of stuffed animals",
        zone="bed",
        reduction_word="a reduction in the stuffed-animal crowd",
        storage="into a cloth basket",
        peek="a tiny wheel glinting under a plush bear",
        hideable={"wooden_music_box"},
        tags={"tidy", "toys"},
    ),
}

TOOLS = {
    "crate": Tool(
        id="crate",
        label="rolling crate",
        phrase="a rolling crate with squeaky wheels",
        zone="floor",
        handles={"blocks"},
        tags={"storage", "crate"},
    ),
    "folder": Tool(
        id="folder",
        label="blue folder",
        phrase="a blue folder that could hold the loose pages flat",
        zone="desk",
        handles={"papers"},
        tags={"storage", "folder"},
    ),
    "basket": Tool(
        id="basket",
        label="cloth basket",
        phrase="a cloth basket with rope handles",
        zone="bed",
        handles={"stuffed_animals"},
        tags={"storage", "basket"},
    ),
}

KEEPSAKES = {
    "paper_star_mobile": Keepsake(
        id="paper_star_mobile",
        label="paper star mobile",
        phrase="a little paper star mobile",
        maker="Grandpa",
        issue="untangled",
        clue="One yellow star was stuck fast in a knot of string.",
        appreciate_line="The stars had been made by Grandpa on a rainy afternoon, and suddenly they felt bright all over again.",
        use_for={"reading_nook"},
        tags={"memory", "stars"},
    ),
    "ribbon_bookmark": Keepsake(
        id="ribbon_bookmark",
        label="ribbon bookmark",
        phrase="a ribbon bookmark with a pressed daisy",
        maker="Aunt May",
        issue="flattened",
        clue="The daisy inside was safe, but the ribbon had been folded hard in the stack.",
        appreciate_line="Aunt May had sewn the ribbon by hand, and the child could almost remember her careful fingers.",
        use_for={"art_desk"},
        tags={"memory", "bookmark"},
    ),
    "wooden_music_box": Keepsake(
        id="wooden_music_box",
        label="wooden music box",
        phrase="a tiny wooden music box",
        maker="Grandma",
        issue="dusted",
        clue="Its little brass wheel looked dull under a sleeve of lint.",
        appreciate_line="Grandma had once turned the wheel and laughed at the thin sweet tune, and the sound came back in the child's mind.",
        use_for={"sleepover_spot"},
        tags={"memory", "music_box"},
    ),
}

METHODS = {
    "untangle": RestoreMethod(
        id="untangle",
        label="untangle the string",
        action="carefully loosened the knot and shook the stars free",
        fixes={"untangled"},
        tags={"fix", "gentle"},
    ),
    "press_flat": RestoreMethod(
        id="press_flat",
        label="smooth the ribbon",
        action="smoothed the ribbon with warm hands and tucked it under a heavy book for a minute",
        fixes={"flattened"},
        tags={"fix", "paper"},
    ),
    "dust_cloth": RestoreMethod(
        id="dust_cloth",
        label="wipe away the dust",
        action="rubbed it clean with a soft cloth until the wood shone again",
        fixes={"dusted"},
        tags={"fix", "clean"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Theo", "Finn", "Eli", "Jack"]
TRAITS = ["careful", "busy", "thoughtful", "restless", "cheerful", "curious"]


def _predict_after_tidy(goal: Goal, clutter: Clutter, keepsake: Keepsake) -> dict:
    return {
        "space": goal_blocked(goal, clutter),
        "surprise": keepsake_hidden_in(clutter, keepsake),
    }


def introduce(world: World, child: Entity, parent: Entity, goal: Goal, clutter: Clutter) -> None:
    world.say(
        f"On a quiet afternoon, {child.id} stood in the bedroom doorway and wished for {goal.label}. "
        f"{child.pronoun().capitalize()} {goal.setup}, but {clutter.phrase} was in the way."
    )
    world.say(
        f"{child.id}'s {parent.label_word} noticed the crowded {clutter.zone} and said the room looked as if it needed one small, patient change."
    )


def foreshadow(world: World, child: Entity, clutter: Clutter, keepsake: Keepsake) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"As {child.pronoun()} bent down, {child.pronoun()} saw {clutter.peek}. "
        f"{keepsake.clue}"
    )


def resist(world: World, child: Entity, parent: Entity, clutter: Clutter) -> None:
    child.memes["grumble"] += 1
    world.say(
        f'"Do I have to?" {child.id} asked. "{clutter.reduction_word.capitalize()} sounds like making my room smaller."'
    )
    world.say(
        f'{child.id} was not angry exactly, but the chore felt larger than the room.'
    )


def reframe(world: World, child: Entity, parent: Entity, goal: Goal) -> None:
    parent.memes["patience"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt beside {child.id}. '
        f'"A reduction is not the same as losing everything," {parent.pronoun()} said softly. '
        f'"Sometimes it just means making space for what you really want."'
    )
    pred = world.facts.get("prediction", {})
    if pred.get("space"):
        world.say(
            f'{parent.pronoun().capitalize()} tapped the blocked {goal.zone}. '
            f'"If we clear this spot, your room can do something new."'
        )


def tidy(world: World, child: Entity, clutter: Clutter, tool: Tool) -> None:
    pile = world.get("pile")
    room = world.get("room")
    pile.meters["clutter"] = 0.0
    room.meters["order"] += 1
    child.memes["effort"] += 1
    world.say(
        f"So {child.id} began sorting. Piece by piece, the {clutter.label} went {clutter.storage}, "
        f"and the {tool.label} slowly did its quiet work."
    )
    propagate(world, narrate=False)
    if room.meters["free_space"] >= THRESHOLD:
        world.say(
            f"Little by little, the {clutter.zone} opened up. The room seemed to take one long, easy breath."
        )


def discover(world: World, child: Entity, keepsake: Keepsake) -> None:
    keepsake_ent = world.get("keepsake")
    keepsake_ent.meters["found"] += 1
    child.memes["surprise"] += 1
    world.say(
        f"Then came the twist {child.id} had not expected at all: under the last bit of clutter lay {keepsake.phrase}."
    )
    world.say(
        f'{child.pronoun().capitalize()} picked it up carefully and went very still.'
    )


def restore(world: World, child: Entity, parent: Entity, keepsake: Keepsake, method: RestoreMethod) -> None:
    keepsake_ent = world.get("keepsake")
    keepsake_ent.meters["restored"] += 1
    world.say(
        f'"{keepsake.maker} made this for me," {child.id} whispered.'
    )
    world.say(
        f"{child.id} and {child.pronoun('possessive')} {parent.label_word} {method.action}."
    )
    propagate(world, narrate=False)
    if child.memes["appreciation"] >= THRESHOLD:
        world.say(
            keepsake.appreciate_line
        )


def ending(world: World, child: Entity, parent: Entity, goal: Goal, keepsake: Keepsake) -> None:
    child.memes["lesson"] += 1
    child.memes["joy"] += 1
    world.say(
        f"When the room was ready, {child.id} did exactly what {child.pronoun()} had hoped for at the start. "
        f"{child.pronoun().capitalize()} {goal.ending}."
    )
    world.say(
        f'"I think I understand now," {child.id} said. "The reduction made room for something better, and it helped me appreciate what I already had."'
    )
    world.say(
        f'{parent.label_word.capitalize()} smiled. The room was not emptier after all. It felt clearer, warmer, and more loved.'
    )


def tell(
    goal: Goal,
    clutter: Clutter,
    tool: Tool,
    keepsake: Keepsake,
    method: RestoreMethod,
    child_name: str = "Lily",
    child_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
) -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        phrase=child_name,
        role="child",
        attrs={"name": child_name, "trait": trait},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label=f"the {parent_type}",
        phrase=f"the {parent_type}",
        role="parent",
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label="room",
        phrase="the bedroom",
    ))
    pile = world.add(Entity(
        id="pile",
        type="clutter",
        label=clutter.label,
        phrase=clutter.phrase,
        zone=clutter.zone,
    ))
    tool_ent = world.add(Entity(
        id="tool",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        zone=tool.zone,
    ))
    keepsake_ent = world.add(Entity(
        id="keepsake",
        type="keepsake",
        label=keepsake.label,
        phrase=keepsake.phrase,
        zone=clutter.zone,
    ))
    pile.meters["clutter"] = 1
    room.meters["crowded"] = 1
    child.memes["wish"] = 1
    world.facts["prediction"] = _predict_after_tidy(goal, clutter, keepsake)

    introduce(world, child, parent, goal, clutter)
    foreshadow(world, child, clutter, keepsake)

    world.para()
    resist(world, child, parent, clutter)
    reframe(world, child, parent, goal)
    tidy(world, child, clutter, tool)

    world.para()
    discover(world, child, keepsake)
    restore(world, child, parent, keepsake, method)

    world.para()
    ending(world, child, parent, goal, keepsake)

    world.facts.update(
        child=child,
        parent=parent,
        room=room,
        pile=pile,
        tool=tool_ent,
        keepsake=keepsake_ent,
        goal_cfg=goal,
        clutter_cfg=clutter,
        tool_cfg=tool,
        keepsake_cfg=keepsake,
        method_cfg=method,
        found=keepsake_ent.meters["found"] >= THRESHOLD,
        restored=keepsake_ent.meters["restored"] >= THRESHOLD,
        space_opened=room.meters["free_space"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    goal = f["goal_cfg"]
    clutter = f["clutter_cfg"]
    keepsake = f["keepsake_cfg"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the words "reduction" and "appreciate".',
        f"Tell a gentle room-cleaning story where a {child.type} wants {goal.label}, resists tidying {clutter.label}, and then finds {keepsake.phrase} in a small twist.",
        f"Write a child-facing story with foreshadowing, a warm family moment, and a lesson learned: clearing clutter can help someone appreciate what matters.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    goal = f["goal_cfg"]
    clutter = f["clutter_cfg"]
    keepsake = f["keepsake_cfg"]
    method = f["method_cfg"]
    name = child.attrs.get("name", child.label)
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name} and {name}'s {pw}. They are working together in a crowded bedroom."
        ),
        (
            f"What did {name} want at the start?",
            f"{name} wanted {goal.label}. The problem was that {clutter.phrase} was blocking the very place needed for it."
        ),
        (
            f"Why did the story mention a reduction?",
            f"The reduction meant making the pile of {clutter.label} smaller by sorting it away. It was not about taking all the child's things away, but about opening space for something useful."
        ),
        (
            "What was the foreshadowing clue?",
            f"Before the keepsake was found, there was a small clue in the clutter: {clutter.peek.lower()} {keepsake.clue} That hint quietly showed that something special was hiding there."
        ),
    ]
    if f.get("found"):
        qa.append((
            "What was the twist?",
            f"The twist was that the boring clean-up turned into a discovery. Under the last of the {clutter.label}, {name} found {keepsake.phrase}."
        ))
    if f.get("restored"):
        qa.append((
            f"How did {name} come to appreciate the keepsake?",
            f"{name} remembered that {keepsake.maker} had made it, and then {name} and {pw} {method.action}. Fixing it brought the memory back and made the keepsake feel important again."
        ))
    qa.append((
        "What lesson did the child learn?",
        f"{name} learned that clearing a room can make space for what matters most. The small chore also helped {child.pronoun('object')} appreciate a forgotten gift instead of only thinking about what had to be put away."
    ))
    return qa


KNOWLEDGE = {
    "tidy": [
        ("Why does tidying a room help?",
         "Tidying helps because it puts things where they belong and opens space to use the room more easily. A clear space can feel calmer too.")
    ],
    "storage": [
        ("What is a storage basket or crate for?",
         "A basket or crate holds loose things in one place so they do not stay scattered all over the room.")
    ],
    "memory": [
        ("Why can old keepsakes feel special?",
         "A keepsake can remind you of a person, a day, or a feeling you love. Even a small object can carry a big memory.")
    ],
    "reading": [
        ("What is a reading nook?",
         "A reading nook is a small cozy spot set up for sitting with books. It is meant to feel quiet and comfortable.")
    ],
    "art": [
        ("Why is a clear desk useful for drawing?",
         "A clear desk gives your paper and crayons room to spread out. It helps you work without bumping into piles.")
    ],
    "sleepover": [
        ("What do you need for a sleepover spot?",
         "You need a clean place to lie down, with enough room for blankets and a pillow. A tidy spot helps a guest feel welcome.")
    ],
    "stars": [
        ("What is a mobile?",
         "A mobile is a light hanging decoration that moves gently in the air.")
    ],
    "bookmark": [
        ("What is a bookmark for?",
         "A bookmark keeps your place in a book so you can stop reading and find the same page later.")
    ],
    "music_box": [
        ("What does a music box do?",
         "A music box is a little box that plays a tune when you wind or turn it.")
    ],
}
KNOWLEDGE_ORDER = ["tidy", "storage", "memory", "reading", "art", "sleepover", "stars", "bookmark", "music_box"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["goal_cfg"].tags) | set(f["clutter_cfg"].tags) | set(f["tool_cfg"].tags) | set(f["keepsake_cfg"].tags)
    out: list[tuple[str, str]] = []
    tag_map = {
        "tidy": "tidy",
        "blocks": "storage",
        "paper": "storage",
        "toys": "storage",
        "memory": "memory",
        "reading": "reading",
        "art": "art",
        "sleepover": "sleepover",
        "stars": "stars",
        "bookmark": "bookmark",
        "music_box": "music_box",
    }
    normalized = {tag_map[t] for t in tags if t in tag_map}
    for key in KNOWLEDGE_ORDER:
        if key in normalized:
            out.extend(KNOWLEDGE[key])
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
        if ent.zone:
            bits.append(f"zone={ent.zone}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        goal="reading_nook",
        clutter="blocks",
        tool="crate",
        keepsake="paper_star_mobile",
        method="untangle",
        child_name="Lily",
        child_gender="girl",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        goal="art_desk",
        clutter="papers",
        tool="folder",
        keepsake="ribbon_bookmark",
        method="press_flat",
        child_name="Ben",
        child_gender="boy",
        parent="father",
        trait="curious",
    ),
    StoryParams(
        goal="sleepover_spot",
        clutter="stuffed_animals",
        tool="basket",
        keepsake="wooden_music_box",
        method="dust_cloth",
        child_name="Maya",
        child_gender="girl",
        parent="mother",
        trait="thoughtful",
    ),
]


def explain_rejection(goal: Goal, clutter: Clutter, tool: Tool, keepsake: Keepsake, method: RestoreMethod) -> str:
    if not goal_blocked(goal, clutter):
        return (
            f"(No story: {goal.label} needs the {goal.zone}, but {clutter.label} are on the {clutter.zone}. "
            f"The clutter must honestly block the child's plan.)"
        )
    if not tool_fits(clutter, tool):
        return (
            f"(No story: {tool.label} is not the right tool for tidying {clutter.label} on the {clutter.zone}.)"
        )
    if not keepsake_hidden_in(clutter, keepsake):
        return (
            f"(No story: {keepsake.label} would not plausibly be hidden in {clutter.label}.)"
        )
    if not method_fits(keepsake, method):
        return (
            f"(No story: {method.label} does not sensibly fix a keepsake that is {keepsake.issue}.)"
        )
    if goal.id not in keepsake.use_for:
        return (
            f"(No story: {keepsake.label} does not naturally fit the ending image for {goal.label}.)"
        )
    return "(No story: this combination is not reasonable in this world.)"


ASP_RULES = r"""
blocked(G, C) :- goal_zone(G, Z), clutter_zone(C, Z).
tool_fits(C, T) :- tool(T), handles(T, C), clutter_zone(C, Z), tool_zone(T, Z).
hidden(C, K) :- hides(C, K).
method_fits(K, M) :- keepsake_issue(K, I), fixes(M, I).
fits_ending(G, K) :- useful_for(K, G).

valid(G, C, T, K, M) :- goal(G), clutter(C), tool(T), keepsake(K), method(M),
                        blocked(G, C), tool_fits(C, T), hidden(C, K),
                        method_fits(K, M), fits_ending(G, K).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for goal_id, goal in GOALS.items():
        lines.append(asp.fact("goal", goal_id))
        lines.append(asp.fact("goal_zone", goal_id, goal.zone))
    for clutter_id, clutter in CLUTTER.items():
        lines.append(asp.fact("clutter", clutter_id))
        lines.append(asp.fact("clutter_zone", clutter_id, clutter.zone))
        for keepsake_id in sorted(clutter.hideable):
            lines.append(asp.fact("hides", clutter_id, keepsake_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("tool_zone", tool_id, tool.zone))
        for handle in sorted(tool.handles):
            lines.append(asp.fact("handles", tool_id, handle))
    for keepsake_id, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", keepsake_id))
        lines.append(asp.fact("keepsake_issue", keepsake_id, keepsake.issue))
        for goal_id in sorted(keepsake.use_for):
            lines.append(asp.fact("useful_for", keepsake_id, goal_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        for issue in sorted(method.fixes):
            lines.append(asp.fact("fixes", method_id, issue))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between Python and ASP:")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child makes a reduction in room clutter, finds a keepsake, and learns to appreciate it."
    )
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--clutter", choices=CLUTTER)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    chosen_goal = GOALS[args.goal] if args.goal else None
    chosen_clutter = CLUTTER[args.clutter] if args.clutter else None
    chosen_tool = TOOLS[args.tool] if args.tool else None
    chosen_keepsake = KEEPSAKES[args.keepsake] if args.keepsake else None
    chosen_method = METHODS[args.method] if args.method else None

    if all(x is not None for x in (chosen_goal, chosen_clutter, chosen_tool, chosen_keepsake, chosen_method)):
        if not valid_combo(chosen_goal, chosen_clutter, chosen_tool, chosen_keepsake, chosen_method):
            raise StoryError(explain_rejection(chosen_goal, chosen_clutter, chosen_tool, chosen_keepsake, chosen_method))

    combos = [
        combo for combo in valid_combos()
        if (args.goal is None or combo[0] == args.goal)
        and (args.clutter is None or combo[1] == args.clutter)
        and (args.tool is None or combo[2] == args.tool)
        and (args.keepsake is None or combo[3] == args.keepsake)
        and (args.method is None or combo[4] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    goal_id, clutter_id, tool_id, keepsake_id, method_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        goal=goal_id,
        clutter=clutter_id,
        tool=tool_id,
        keepsake=keepsake_id,
        method=method_id,
        child_name=name,
        child_gender=gender,
        parent=parent,
        trait=trait,
    )


def _require_key(table: dict, key: str, field_name: str):
    if key not in table:
        raise StoryError(f"(Invalid {field_name}: {key})")
    return table[key]


def generate(params: StoryParams) -> StorySample:
    goal = _require_key(GOALS, params.goal, "goal")
    clutter = _require_key(CLUTTER, params.clutter, "clutter")
    tool = _require_key(TOOLS, params.tool, "tool")
    keepsake = _require_key(KEEPSAKES, params.keepsake, "keepsake")
    method = _require_key(METHODS, params.method, "method")
    if not valid_combo(goal, clutter, tool, keepsake, method):
        raise StoryError(explain_rejection(goal, clutter, tool, keepsake, method))

    world = tell(
        goal=goal,
        clutter=clutter,
        tool=tool,
        keepsake=keepsake,
        method=method,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        trait=params.trait,
    )
    child = world.get("child")
    child.attrs["name"] = params.child_name
    child.label = params.child_name
    child.phrase = params.child_name
    return StorySample(
        params=params,
        story=world.render().replace("child", params.child_name),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    story = sample.story.replace("child", sample.params.child_name).replace("parent", sample.params.parent)
    print(story)
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
        print(f"{len(combos)} valid (goal, clutter, tool, keepsake, method) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:16}" for part in combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = []
        for idx, params in enumerate(CURATED):
            params = StoryParams(
                goal=params.goal,
                clutter=params.clutter,
                tool=params.tool,
                keepsake=params.keepsake,
                method=params.method,
                child_name=params.child_name,
                child_gender=params.child_gender,
                parent=params.parent,
                trait=params.trait,
                seed=(base_seed + idx),
            )
            samples.append(generate(params))
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
            header = f"### {p.child_name}: {p.goal} with {p.clutter} ({p.keepsake})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
