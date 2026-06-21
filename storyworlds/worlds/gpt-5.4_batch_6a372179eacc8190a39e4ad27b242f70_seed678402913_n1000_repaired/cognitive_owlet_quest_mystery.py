#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cognitive_owlet_quest_mystery.py
===========================================================

A standalone story world about a child and a worried owlet on a small mystery
quest. The child helps the owlet search for a missing keepsake by following one
grounded clue, facing one practical obstacle, and using one sensible tool.

The world model prefers tight, reasonable stories:
- a setting must actually contain the chosen hiding place
- the chosen tool must solve the hiding place's obstacle

Run it
------
    python storyworlds/worlds/gpt-5.4/cognitive_owlet_quest_mystery.py
    python storyworlds/worlds/gpt-5.4/cognitive_owlet_quest_mystery.py --place garden --hideout bramble_hollow --tool lantern
    python storyworlds/worlds/gpt-5.4/cognitive_owlet_quest_mystery.py --hideout loft_beam
    python storyworlds/worlds/gpt-5.4/cognitive_owlet_quest_mystery.py --all
    python storyworlds/worlds/gpt-5.4/cognitive_owlet_quest_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/cognitive_owlet_quest_mystery.py --trace
    python storyworlds/worlds/gpt-5.4/cognitive_owlet_quest_mystery.py --verify
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

HERE = os.path.abspath(__file__)
WORLD_DIR = os.path.dirname(HERE)
STORYWORLDS_DIR = os.path.dirname(os.path.dirname(WORLD_DIR))
sys.path.insert(0, STORYWORLDS_DIR)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        bird = {"owlet"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in bird:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    trail: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Hideout:
    id: str
    label: str
    phrase: str
    challenge: str
    clue_text: str
    retrieval: str
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    handles: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    sound: str
    value_text: str
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


def _r_clue_brings_hope(world: World) -> list[str]:
    child = world.get("child")
    owlet = world.get("owlet")
    if child.meters["clue_found"] < THRESHOLD:
        return []
    sig = ("hope",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["hope"] += 1
    owlet.memes["hope"] += 1
    return []


def _r_obstacle_brings_worry(world: World) -> list[str]:
    child = world.get("child")
    owlet = world.get("owlet")
    if child.meters["obstacle_seen"] < THRESHOLD:
        return []
    sig = ("worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    owlet.memes["worry"] += 1
    return []


def _r_tool_solves_obstacle(world: World) -> list[str]:
    child = world.get("child")
    tool = world.get("tool")
    hideout = world.get("hideout")
    if child.meters["used_tool"] < THRESHOLD:
        return []
    sig = ("solved",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if hideout.attrs.get("challenge") in tool.attrs.get("handles", set()):
        child.meters["path_open"] += 1
        child.memes["confidence"] += 1
        return []
    return []


def _r_retrieval_relief(world: World) -> list[str]:
    child = world.get("child")
    owlet = world.get("owlet")
    keepsake = world.get("keepsake")
    if child.meters["found_keepsake"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owlet.memes["relief"] += 1
    child.memes["joy"] += 1
    keepsake.meters["safe"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="clue_brings_hope", tag="emotion", apply=_r_clue_brings_hope),
    Rule(name="obstacle_brings_worry", tag="emotion", apply=_r_obstacle_brings_worry),
    Rule(name="tool_solves_obstacle", tag="physical", apply=_r_tool_solves_obstacle),
    Rule(name="retrieval_relief", tag="emotion", apply=_r_retrieval_relief),
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
            elif any(sig[0] == rule.name.split("_")[0] for sig in world.fired):
                pass
        if not changed:
            # rules above mostly mutate state silently; detect any silent changes by rerunning
            silent_before = len(world.fired)
            for rule in CAUSAL_RULES:
                rule.apply(world)
            changed = len(world.fired) > silent_before
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "garden": Place(
        id="garden",
        label="garden",
        phrase="the moonlit garden behind the house",
        trail="A silver path lay across the grass, and every leaf seemed to be hiding a whisper.",
        affords={"bramble_hollow", "pond_edge"},
        tags={"garden"},
    ),
    "library": Place(
        id="library",
        label="library",
        phrase="the little library room with the tall shelves",
        trail="The room smelled like paper and dust, and the shadows sat between the books.",
        affords={"book_nook", "window_box"},
        tags={"library"},
    ),
    "barn": Place(
        id="barn",
        label="barn",
        phrase="the quiet barn with sleepy beams overhead",
        trail="The boards creaked softly, as if the place remembered old secrets.",
        affords={"loft_beam", "grain_crate"},
        tags={"barn"},
    ),
}

HIDEOUTS = {
    "bramble_hollow": Hideout(
        id="bramble_hollow",
        label="bramble hollow",
        phrase="a hollow under a curl of bramble roots",
        challenge="dark",
        clue_text="a tiny gray feather caught on a thorn and one soft blink of silver deep inside",
        retrieval="held the lantern low until the silver glint woke up in the dark",
        image="The little hollow shone like a pocket of night with one bright secret in it.",
        tags={"dark", "bramble"},
    ),
    "pond_edge": Hideout(
        id="pond_edge",
        label="pond edge",
        phrase="the reeds beside the pond",
        challenge="narrow",
        clue_text="a line of little claw prints ending where the reeds grew tight together",
        retrieval="used the string hook to lift the reeds apart without tearing them",
        image="The pond made one round moon on the water, and the reeds finally gave up their secret.",
        tags={"narrow", "pond"},
    ),
    "book_nook": Hideout(
        id="book_nook",
        label="book nook",
        phrase="a narrow gap behind the biggest storybook",
        challenge="narrow",
        clue_text="one drifting down feather tucked between the books and a faint chime when the shelf was nudged",
        retrieval="used the string hook to tug the keepsake gently from the gap",
        image="Dust floated like tiny stars while the shelf gave back what it had hidden.",
        tags={"narrow", "books"},
    ),
    "window_box": Hideout(
        id="window_box",
        label="window box",
        phrase="the flower box under the library window",
        challenge="high",
        clue_text="a smudge of owl down on the sill and a sleepy sparkle above eye level",
        retrieval="climbed the step stool and reached carefully into the window box",
        image="At the window, the flowers nodded as if they had been guarding the answer all along.",
        tags={"high", "flowers"},
    ),
    "loft_beam": Hideout(
        id="loft_beam",
        label="loft beam",
        phrase="the highest beam under the roof",
        challenge="high",
        clue_text="a loose feather spiraling from above and one tiny clink in the rafters",
        retrieval="climbed the step stool and stretched just high enough to touch the beam",
        image="Above the hay, the rafters stopped being shadows and became the end of the quest.",
        tags={"high", "rafters"},
    ),
    "grain_crate": Hideout(
        id="grain_crate",
        label="grain crate",
        phrase="a crate pushed behind two sacks of grain",
        challenge="dark",
        clue_text="a round mark in the dust and a muffled little ring from behind the sacks",
        retrieval="held the lantern near the crate until the lost thing blinked back from the shadows",
        image="Behind the grain sacks, the dark corner looked ordinary no longer.",
        tags={"dark", "crate"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a warm little lantern",
        action="lifted the lantern so the dark place could not keep its secret",
        handles={"dark"},
        tags={"lantern", "light"},
    ),
    "step_stool": Tool(
        id="step_stool",
        label="step stool",
        phrase="a steady wooden step stool",
        action="set the step stool in place so the high hiding spot became reachable",
        handles={"high"},
        tags={"stool", "reach"},
    ),
    "string_hook": Tool(
        id="string_hook",
        label="string hook",
        phrase="a bent string hook made from cord and a smooth twig",
        action="slid the string hook into the tight space and drew the hidden thing out carefully",
        handles={"narrow"},
        tags={"hook", "reach"},
    ),
}

KEEPSAKES = {
    "moonbell": Keepsake(
        id="moonbell",
        label="moon bell",
        phrase="a tiny moon bell",
        sound="made the softest silver ring",
        value_text="It helped the owlet feel brave when the dark felt wide.",
        tags={"bell", "moon"},
    ),
    "star_key": Keepsake(
        id="star_key",
        label="star key",
        phrase="a little star key",
        sound="tapped with a bright, careful clink",
        value_text="It fit the owlet's keepsake box back in the nest.",
        tags={"key", "star"},
    ),
    "map_tube": Keepsake(
        id="map_tube",
        label="map tube",
        phrase="a tiny rolled map tube",
        sound="rustled like a paper secret",
        value_text="Inside was the owlet's quest map to favorite resting places.",
        tags={"map", "paper"},
    ),
}


def tool_fits(tool: Tool, hideout: Hideout) -> bool:
    return hideout.challenge in tool.handles


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for hideout_id in sorted(place.affords):
            hideout = HIDEOUTS[hideout_id]
            for tool_id, tool in TOOLS.items():
                if not tool_fits(tool, hideout):
                    continue
                for keepsake_id in KEEPSAKES:
                    out.append((place_id, hideout_id, tool_id, keepsake_id))
    return out


@dataclass
class StoryParams:
    place: str
    hideout: str
    tool: str
    keepsake: str
    child_name: str
    child_gender: str
    parent: str
    mood: str
    seed: Optional[int] = None


def predict_success(world: World, hideout: Hideout, tool: Tool) -> dict:
    sim = world.copy()
    sim.get("child").meters["obstacle_seen"] += 1
    sim.get("child").meters["used_tool"] += 1
    propagate(sim, narrate=False)
    return {
        "opened": sim.get("child").meters["path_open"] >= THRESHOLD,
        "worry": sim.get("child").memes["worry"],
    }


def introduce(world: World, child: Entity, owlet: Entity, place: Place, keepsake: Keepsake) -> None:
    world.say(
        f"One hushy evening, {child.id} was walking near {place.phrase} when a tiny owlet fluttered down to the fence."
    )
    world.say(
        f'"Please help me," the owlet whispered. "My {keepsake.label} is gone."'
    )
    world.say(place.trail)


def child_notices(world: World, child: Entity, owlet: Entity) -> None:
    child.memes["care"] += 1
    child.memes["curiosity"] += 1
    owlet.memes["worry"] += 1
    world.say(
        f"{child.id} liked puzzles, even the sort a teacher might call a cognitive game, so {child.pronoun()} knelt at once to listen."
    )
    world.say(
        f"The owlet's round eyes looked shiny with worry, and that made the mystery feel important."
    )


def start_quest(world: World, child: Entity, owlet: Entity, keepsake: Keepsake) -> None:
    child.memes["quest"] += 1
    world.say(
        f'"Then we will go on a quest," said {child.id}. "We will follow the smallest clue until your {keepsake.label} comes home."'
    )


def find_clue(world: World, hideout: Hideout) -> None:
    child = world.get("child")
    child.meters["clue_found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They searched slowly and found {hideout.clue_text}. That was enough to turn a fear into a real trail."
    )


def approach_hideout(world: World, hideout: Hideout) -> None:
    child = world.get("child")
    child.meters["obstacle_seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The trail led them to {hideout.phrase}. It was {hideout.challenge}, and for one second the mystery felt bigger than the two of them."
    )


def choose_tool(world: World, tool: Tool, hideout: Hideout) -> None:
    child = world.get("child")
    pred = predict_success(world, hideout, tool)
    world.facts["predicted_opened"] = pred["opened"]
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'{child.id} did not rush. {child.pronoun().capitalize()} looked, thought, and chose {tool.phrase}.'
    )


def use_tool(world: World, tool: Tool, hideout: Hideout) -> None:
    child = world.get("child")
    child.meters["used_tool"] += 1
    propagate(world, narrate=False)
    world.say(f"{child.id} {tool.action}.")
    world.say(f"Then {child.pronoun()} {hideout.retrieval}.")


def recover(world: World, child: Entity, owlet: Entity, keepsake: Keepsake, hideout: Hideout) -> None:
    child.meters["found_keepsake"] += 1
    propagate(world, narrate=False)
    world.say(
        f"There it was: {keepsake.phrase}. It {keepsake.sound}, and the owlet gave one soft hop of relief."
    )
    world.say(keepsake.value_text)
    world.say(hideout.image)


def ending(world: World, child: Entity, owlet: Entity, parent: Entity, keepsake: Keepsake) -> None:
    owlet.memes["trust"] += 1
    child.memes["joy"] += 1
    world.say(
        f'The owlet tucked the {keepsake.label} under its wing. "You solved the mystery," it said.'
    )
    world.say(
        f"When {child.id} went back to {child.pronoun('possessive')} {parent.label_word}, {child.pronoun()} still had a moon-bright smile."
    )
    world.say(
        f"High in the dark, the owlet circled once above the path, no longer worried at all."
    )


def tell(
    place: Place,
    hideout: Hideout,
    tool: Tool,
    keepsake: Keepsake,
    child_name: str = "Nia",
    child_gender: str = "girl",
    parent_type: str = "mother",
    mood: str = "careful",
) -> World:
    world = World(place)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            attrs={"mood": mood},
        )
    )
    owlet = world.add(
        Entity(
            id="Owlet",
            kind="character",
            type="owlet",
            label="the owlet",
            role="guide",
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    world.add(
        Entity(
            id="hideout",
            type="hideout",
            label=hideout.label,
            attrs={"challenge": hideout.challenge},
            tags=set(hideout.tags),
        )
    )
    world.add(
        Entity(
            id="tool",
            type="tool",
            label=tool.label,
            attrs={"handles": set(tool.handles)},
            tags=set(tool.tags),
        )
    )
    world.add(
        Entity(
            id="keepsake",
            type="keepsake",
            label=keepsake.label,
            tags=set(keepsake.tags),
        )
    )

    introduce(world, child, owlet, place, keepsake)
    child_notices(world, child, owlet)

    world.para()
    start_quest(world, child, owlet, keepsake)
    find_clue(world, hideout)
    approach_hideout(world, hideout)

    world.para()
    choose_tool(world, tool, hideout)
    use_tool(world, tool, hideout)
    if child.meters["path_open"] < THRESHOLD:
        raise StoryError("The chosen tool did not open the hiding place in the simulated world.")
    recover(world, child, owlet, keepsake, hideout)

    world.para()
    ending(world, child, owlet, parent, keepsake)

    world.facts.update(
        child=child,
        owlet=owlet,
        parent=parent,
        place=place,
        hideout_cfg=hideout,
        tool_cfg=tool,
        keepsake_cfg=keepsake,
        success=child.meters["found_keepsake"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "owlet": [
        (
            "What is an owlet?",
            "An owlet is a baby owl. It is smaller than a grown owl and still learning about the world.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something you do not know yet and want to figure out. You solve it by noticing clues and thinking carefully.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a special journey to find something or do something important. It usually has a goal and a few hard steps along the way.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you find an answer. A feather, a print, or a sound can all be clues.",
        )
    ],
    "lantern": [
        (
            "Why does a lantern help in the dark?",
            "A lantern makes light, so you can see what the dark was hiding. Good light can turn a scary place into an ordinary place.",
        )
    ],
    "stool": [
        (
            "What is a step stool for?",
            "A step stool helps you safely reach something that is too high. It gives you one extra step without climbing somewhere shaky.",
        )
    ],
    "hook": [
        (
            "What can a hook help you do?",
            "A hook can pull or lift something that is tucked in a tight place. It helps when hands cannot fit easily.",
        )
    ],
}

KNOWLEDGE_ORDER = ["owlet", "mystery", "quest", "clue", "lantern", "stool", "hook"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    keepsake = f["keepsake_cfg"]
    return [
        'Write a short Mystery story for a 3-to-5-year-old that includes the words "cognitive" and "owlet" and centers on a small Quest.',
        f"Tell a gentle mystery where {child.id} helps a worried owlet search for a missing {keepsake.label} in {place.phrase}.",
        f"Write a child-facing quest story with one clue, one obstacle, and a happy ending where careful thinking solves the problem.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    owlet = f["owlet"]
    parent = f["parent"]
    place = f["place"]
    hideout = f["hideout_cfg"]
    tool = f["tool_cfg"]
    keepsake = f["keepsake_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and a tiny owlet. The owlet needed help, and {child.id} chose to help solve the mystery.",
        ),
        (
            f"What was missing?",
            f"The missing thing was the owlet's {keepsake.label}. It mattered because {keepsake.value_text.lower()}",
        ),
        (
            "Where did the quest happen?",
            f"The quest happened in {place.phrase}. That place felt mysterious because {place.trail.lower()}",
        ),
        (
            "What clue did they find?",
            f"They found {hideout.clue_text}. The clue mattered because it pointed them toward {hideout.phrase}.",
        ),
        (
            f"Why did {child.id} choose the {tool.label}?",
            f"{child.id} chose the {tool.label} because the hiding place was {hideout.challenge}. The tool matched the problem and helped open the way safely.",
        ),
        (
            "How was the mystery solved?",
            f"The mystery was solved when {child.id} used the {tool.label} and found the {keepsake.label} in {hideout.phrase}. After that, the owlet stopped worrying and felt relieved.",
        ),
        (
            f"How did the story end?",
            f"It ended happily with the owlet carrying the {keepsake.label} home again. {child.id} went back to {child.pronoun('possessive')} {parent.label_word} smiling, which shows the quest changed fear into joy.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"owlet", "mystery", "quest", "clue"}
    tool = f["tool_cfg"]
    if tool.id == "lantern":
        tags.add("lantern")
    elif tool.id == "step_stool":
        tags.add("stool")
    elif tool.id == "string_hook":
        tags.add("hook")
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
    for ent in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {}
            for key, value in ent.attrs.items():
                if isinstance(value, set):
                    shown[key] = sorted(value)
                else:
                    shown[key] = value
            bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="garden",
        hideout="bramble_hollow",
        tool="lantern",
        keepsake="moonbell",
        child_name="Nia",
        child_gender="girl",
        parent="mother",
        mood="careful",
    ),
    StoryParams(
        place="library",
        hideout="window_box",
        tool="step_stool",
        keepsake="star_key",
        child_name="Ben",
        child_gender="boy",
        parent="father",
        mood="patient",
    ),
    StoryParams(
        place="barn",
        hideout="grain_crate",
        tool="lantern",
        keepsake="map_tube",
        child_name="Mila",
        child_gender="girl",
        parent="mother",
        mood="gentle",
    ),
    StoryParams(
        place="library",
        hideout="book_nook",
        tool="string_hook",
        keepsake="moonbell",
        child_name="Leo",
        child_gender="boy",
        parent="father",
        mood="thoughtful",
    ),
]


def explain_rejection(place: Optional[Place], hideout: Optional[Hideout], tool: Optional[Tool]) -> str:
    if place is not None and hideout is not None and hideout.id not in place.affords:
        return (
            f"(No story: {hideout.label} does not belong in {place.label}. Pick a hiding place that the setting can honestly contain.)"
        )
    if hideout is not None and tool is not None and not tool_fits(tool, hideout):
        return (
            f"(No story: a {tool.label} does not solve a {hideout.challenge} hiding place. Choose a tool that matches the obstacle.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


ASP_RULES = r"""
fits(Tool, Hideout) :- handles(Tool, Need), challenge(Hideout, Need).
valid(Place, Hideout, Tool, Keepsake) :-
    place(Place), hideout(Hideout), tool(Tool), keepsake(Keepsake),
    affords(Place, Hideout), fits(Tool, Hideout).

outcome(found) :- chosen_place(P), chosen_hideout(H), chosen_tool(T), chosen_keepsake(K),
                  valid(P, H, T, K).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for hideout_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, hideout_id))
    for hideout_id, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hideout_id))
        lines.append(asp.fact("challenge", hideout_id, hideout.challenge))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for handle in sorted(tool.handles):
            lines.append(asp.fact("handles", tool_id, handle))
    for keepsake_id in KEEPSAKES:
        lines.append(asp.fact("keepsake", keepsake_id))
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
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_hideout", params.hideout),
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_keepsake", params.keepsake),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "none"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a child and an owlet solve a small mystery quest."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Nia", "Mila", "Tess", "Ava", "Lina", "Ruby", "Mae", "Zoe"]
BOY_NAMES = ["Ben", "Leo", "Noah", "Finn", "Eli", "Owen", "Sam", "Max"]
MOODS = ["careful", "patient", "gentle", "thoughtful", "brave", "curious"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_obj = PLACES.get(args.place) if args.place else None
    hideout_obj = HIDEOUTS.get(args.hideout) if args.hideout else None
    tool_obj = TOOLS.get(args.tool) if args.tool else None

    if place_obj is not None and hideout_obj is not None and args.hideout not in place_obj.affords:
        raise StoryError(explain_rejection(place_obj, hideout_obj, tool_obj))
    if hideout_obj is not None and tool_obj is not None and not tool_fits(tool_obj, hideout_obj):
        raise StoryError(explain_rejection(place_obj, hideout_obj, tool_obj))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.hideout is None or combo[1] == args.hideout)
        and (args.tool is None or combo[2] == args.tool)
        and (args.keepsake is None or combo[3] == args.keepsake)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, hideout_id, tool_id, keepsake_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    mood = rng.choice(MOODS)
    return StoryParams(
        place=place_id,
        hideout=hideout_id,
        tool=tool_id,
        keepsake=keepsake_id,
        child_name=name,
        child_gender=gender,
        parent=parent,
        mood=mood,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"Unknown hideout: {params.hideout}")
    if params.tool not in TOOLS:
        raise StoryError(f"Unknown tool: {params.tool}")
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"Unknown keepsake: {params.keepsake}")

    place = PLACES[params.place]
    hideout = HIDEOUTS[params.hideout]
    tool = TOOLS[params.tool]
    if params.hideout not in place.affords or not tool_fits(tool, hideout):
        raise StoryError(explain_rejection(place, hideout, tool))

    world = tell(
        place=place,
        hideout=hideout,
        tool=tool,
        keepsake=KEEPSAKES[params.keepsake],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        mood=params.mood,
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


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    for params in CURATED:
        out = asp_outcome(params)
        if out != "found":
            rc = 1
            print(f"MISMATCH in outcome for curated params: {params} -> {out}")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(0))
        smoke_params.seed = 0
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        emit(smoke_sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, hideout, tool, keepsake) combos:\n")
        for place_id, hideout_id, tool_id, keepsake_id in combos:
            print(f"  {place_id:8} {hideout_id:15} {tool_id:11} {keepsake_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.keepsake} in {p.hideout} at {p.place}"
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
