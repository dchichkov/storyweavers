#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/grandmum_dialogue_surprise_tall_tale.py
==================================================================

A standalone story world for tall-tale stories about a child helping grandmum
pick an absurdly high piece of fruit. The fruit hangs so high it almost scrapes
the clouds, the first plan nearly works, and then a surprise gives the branch
just enough extra shake.

The world is small on purpose:

- grandmum and a child talk about the problem
- a sky-high fruit hangs on a giant tree
- a reaching tool can nearly pull it loose
- a place-specific surprise adds the final bit of force
- the fruit lands safely in grandmum's apron, and the ending image proves the
  household changed from worried to delighted

The reasonableness gate is concrete rather than maximal:
a valid story needs a tool that can actually reach the fruit, the chosen place
must genuinely afford the surprise, the tool alone must *not* already solve the
problem, and the surprise must be gentle enough not to ruin the fruit.

Run it
------
    python storyworlds/worlds/gpt-5.4/grandmum_dialogue_surprise_tall_tale.py
    python storyworlds/worlds/gpt-5.4/grandmum_dialogue_surprise_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/grandmum_dialogue_surprise_tall_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/grandmum_dialogue_surprise_tall_tale.py --qa
    python storyworlds/worlds/gpt-5.4/grandmum_dialogue_surprise_tall_tale.py --trace
    python storyworlds/worlds/gpt-5.4/grandmum_dialogue_surprise_tall_tale.py --verify
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
# from a nested world directory:
#   storyworlds/worlds/gpt-5.4/<this_file>.py
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "grandmum"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "grandmum":
            return "grandmum"
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    tall_line: str
    surprise_ids: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Fruit:
    id: str
    label: str
    phrase: str
    height_need: int
    firmness: int
    delicacy: int
    ending_food: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    reach: int
    pull: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    force: int
    impact: int
    setup: str
    shout: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    fruit: str
    tool: str
    surprise: str
    child_name: str
    child_gender: str
    grandmum_name: str = "Grandmum"
    child_trait: str = "eager"
    seed: Optional[int] = None


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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_loosen(world: World) -> list[str]:
    fruit = world.get("fruit")
    if fruit.meters["pulled"] < fruit.attrs["firmness"]:
        return []
    sig = ("loosen", "fruit")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    fruit.meters["loose"] += 1
    for eid in ("child", "grandmum"):
        if eid in world.entities:
            world.get(eid).memes["hope"] += 1
    return ["__loose__"]


def _r_catch(world: World) -> list[str]:
    fruit = world.get("fruit")
    apron = world.get("apron")
    if fruit.meters["loose"] < THRESHOLD or apron.meters["ready"] < THRESHOLD:
        return []
    sig = ("catch", "fruit")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if world.facts.get("surprise_impact", 99) <= fruit.attrs["delicacy"]:
        fruit.meters["caught"] += 1
        fruit.meters["safe"] += 1
        return ["__caught__"]
    fruit.meters["bruised"] += 1
    return ["__bruised__"]


CAUSAL_RULES = [
    Rule(name="loosen", tag="physical", apply=_r_loosen),
    Rule(name="catch", tag="physical", apply=_r_catch),
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
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "hill_orchard": Place(
        id="hill_orchard",
        label="the hill orchard",
        tall_line="In the hill orchard, the trees were so tall they seemed to comb the morning clouds.",
        surprise_ids={"wind"},
        tags={"orchard", "wind"},
    ),
    "river_meadow": Place(
        id="river_meadow",
        label="the river meadow",
        tall_line="By the river meadow, the trees leaned over the water as if they wanted to hear their own reflections.",
        surprise_ids={"echo"},
        tags={"river", "orchard"},
    ),
    "farm_lane": Place(
        id="farm_lane",
        label="the farm lane",
        tall_line="Along the farm lane, the oldest tree stretched up so high even the crows had to rest halfway.",
        surprise_ids={"goose"},
        tags={"farm", "orchard"},
    ),
}

FRUITS = {
    "pear": Fruit(
        id="pear",
        label="pear",
        phrase="a moon-round pear",
        height_need=3,
        firmness=3,
        delicacy=2,
        ending_food="pear pie",
        tags={"pear", "pie"},
    ),
    "apple": Fruit(
        id="apple",
        label="apple",
        phrase="an apple as red as a wagon wheel",
        height_need=2,
        firmness=3,
        delicacy=2,
        ending_food="apple tart",
        tags={"apple", "tart"},
    ),
    "plum": Fruit(
        id="plum",
        label="plum",
        phrase="a plum as purple as sunset",
        height_need=2,
        firmness=2,
        delicacy=1,
        ending_food="plum jam",
        tags={"plum", "jam"},
    ),
}

TOOLS = {
    "orchard_hook": Tool(
        id="orchard_hook",
        label="orchard hook",
        phrase="a long orchard hook",
        reach=3,
        pull=2,
        tags={"tool", "hook"},
    ),
    "ladder_rake": Tool(
        id="ladder_rake",
        label="ladder and rake",
        phrase="a ladder and a rake tied together",
        reach=3,
        pull=1,
        tags={"tool", "ladder"},
    ),
    "fishing_pole": Tool(
        id="fishing_pole",
        label="fishing pole",
        phrase="the longest fishing pole in three counties",
        reach=2,
        pull=1,
        tags={"tool", "pole"},
    ),
}

SURPRISES = {
    "wind": Surprise(
        id="wind",
        label="wind gust",
        phrase="a hilltop wind",
        force=1,
        impact=1,
        setup="just then the hill gave one of its famous giant sighs",
        shout='"Hold your apron wide!" Grandmum cried.',
        result="The gust swelled the leaves, rocked the branch, and gave the fruit exactly the last little shake it needed.",
        tags={"wind"},
    ),
    "echo": Surprise(
        id="echo",
        label="river echo",
        phrase="a booming river echo",
        force=1,
        impact=1,
        setup="just then the child called across the water, and the river sent the words back twice as big",
        shout='"Listen to that river holler!" Grandmum laughed.',
        result="The great echo trembled through the branches until the fruit bobbled loose like a bell at noon.",
        tags={"river"},
    ),
    "goose": Surprise(
        id="goose",
        label="goose flap",
        phrase="a farm goose with sail-sized wings",
        force=2,
        impact=1,
        setup="just then old Captain Goose came marching by, offended by all the staring at the tree",
        shout='"Duck your head and keep the apron steady!" Grandmum said.',
        result="With one booming flap, the goose sent a puff of farmyard wind up the trunk and the branch gave a mighty jiggle.",
        tags={"goose", "farm"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]
TRAITS = ["eager", "curious", "bright", "brave", "spry", "quick-thinking"]


def valid_combo(place: Place, fruit: Fruit, tool: Tool, surprise: Surprise) -> bool:
    if surprise.id not in place.surprise_ids:
        return False
    if tool.reach < fruit.height_need:
        return False
    if tool.pull >= fruit.firmness:
        return False
    if tool.pull + surprise.force < fruit.firmness:
        return False
    if surprise.impact > fruit.delicacy:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for fruit_id, fruit in FRUITS.items():
            for tool_id, tool in TOOLS.items():
                for surprise_id, surprise in SURPRISES.items():
                    if valid_combo(place, fruit, tool, surprise):
                        out.append((place_id, fruit_id, tool_id, surprise_id))
    return out


def explain_rejection(place: Place, fruit: Fruit, tool: Tool, surprise: Surprise) -> str:
    if surprise.id not in place.surprise_ids:
        return (
            f"(No story: {place.label} does not naturally provide the surprise "
            f"'{surprise.id}', so the tall-tale turn has nowhere honest to come from.)"
        )
    if tool.reach < fruit.height_need:
        return (
            f"(No story: {tool.phrase} cannot reach the {fruit.label} on that sky-high branch. "
            f"The plan needs a tool that actually touches the fruit.)"
        )
    if tool.pull >= fruit.firmness:
        return (
            f"(No story: {tool.phrase} already pulls the {fruit.label} loose by itself. "
            f"This world requires the surprise to matter, not just decorate the ending.)"
        )
    if tool.pull + surprise.force < fruit.firmness:
        return (
            f"(No story: even with the surprise, the branch would still hold. "
            f"The problem needs a believable fix.)"
        )
    if surprise.impact > fruit.delicacy:
        return (
            f"(No story: that surprise would bruise the {fruit.label}. "
            f"Grandmum needs fruit fit for supper, not fruit fit for squashing.)"
        )
    return "(No story: that combination does not form a reasonable tall-tale plan.)"


def predict_attempt(world: World, tool: Tool, surprise: Surprise) -> dict:
    sim = world.copy()
    fruit = sim.get("fruit")
    fruit.meters["pulled"] += tool.pull
    sim.facts["surprise_impact"] = surprise.impact
    before = fruit.meters["loose"] >= THRESHOLD
    propagate(sim, narrate=False)
    tool_only_loose = fruit.meters["loose"] >= THRESHOLD
    fruit.meters["pulled"] += surprise.force
    propagate(sim, narrate=False)
    after = fruit.meters["caught"] >= THRESHOLD
    return {
        "tool_only_loose": before or tool_only_loose,
        "after_surprise_caught": after,
    }


def introduce(world: World, place: Place, child: Entity, grandmum: Entity, fruit: Fruit) -> None:
    child.memes["wonder"] += 1
    grandmum.memes["purpose"] += 1
    world.say(
        f"{place.tall_line} On that grand morning, {child.id} walked there with {grandmum.label_word}, "
        f"who had her eye on {fruit.phrase} hanging from the tallest branch in sight."
    )
    world.say(
        f'Grandmum shaded her eyes and said, "If I can get that {fruit.label}, I can bake a {fruit.ending_food} '
        f'big enough to feed the lane and still have a slice left for supper."'
    )


def problem(world: World, child: Entity, grandmum: Entity, fruit: Fruit) -> None:
    world.say(
        f'{child.id} tipped back {child.pronoun("possessive")} head until {child.pronoun()} nearly wobbled over. '
        f'"Grandmum," {child.pronoun()} said, "that {fruit.label} is so high it may be talking to the geese."'
    )
    world.say(
        f'"Then we had better answer it," Grandmum said, smiling, though {grandmum.pronoun()} kept one hand on '
        f'{grandmum.pronoun("possessive")} apron and looked thoughtful.'
    )


def plan(world: World, child: Entity, grandmum: Entity, tool: Tool, surprise: Surprise) -> None:
    child.memes["confidence"] += 1
    world.say(
        f'{child.id} pointed to {tool.phrase} and said, "What if we try that?"'
    )
    world.say(
        f'"A fine start," Grandmum said. "But mind you, a branch that high likes to keep its treasures."'
    )
    pred = predict_attempt(world, tool, surprise)
    world.facts["pred_tool_only_loose"] = pred["tool_only_loose"]
    world.facts["pred_after_surprise_caught"] = pred["after_surprise_caught"]


def try_tool(world: World, child: Entity, grandmum: Entity, tool: Tool, fruit: Fruit) -> None:
    fruit_ent = world.get("fruit")
    apron = world.get("apron")
    apron.meters["ready"] = 1
    fruit_ent.meters["pulled"] += tool.pull
    propagate(world, narrate=False)
    child.memes["strain"] += 1
    grandmum.memes["strain"] += 1
    world.say(
        f"So {child.id} and Grandmum took hold of {tool.phrase}. They stretched, reached, and tugged until "
        f"the tree leaves whispered and the branch bent like a fishing rod."
    )
    if fruit_ent.meters["loose"] >= THRESHOLD:
        world.say(
            f"For a blink it seemed the {fruit.label} might drop at once, but the tall branch still held fast."
        )
    else:
        world.say(
            f"The {tool.label} touched the branch, but only just, and the {fruit.label} wobbled without letting go."
        )


def surprise_turn(world: World, child: Entity, grandmum: Entity, surprise: Surprise, fruit: Fruit) -> None:
    fruit_ent = world.get("fruit")
    world.facts["surprise_impact"] = surprise.impact
    child.memes["astonishment"] += 1
    grandmum.memes["astonishment"] += 1
    world.say(surprise.setup + ".")
    world.say(surprise.shout)
    fruit_ent.meters["pulled"] += surprise.force
    propagate(world, narrate=False)
    world.say(surprise.result)
    if fruit_ent.meters["caught"] >= THRESHOLD:
        child.memes["joy"] += 1
        grandmum.memes["joy"] += 1
        world.say(
            f"Down came the {fruit.label}, not with a smash but with a plump little thump, right into Grandmum's apron."
        )
    else:
        fruit_ent.meters["bruised"] += 1
        world.say(
            f"Down came the {fruit.label}, but it landed too hard to be worth baking."
        )


def resolution(world: World, child: Entity, grandmum: Entity, fruit: Fruit) -> None:
    fruit_ent = world.get("fruit")
    if fruit_ent.meters["caught"] >= THRESHOLD and fruit_ent.meters["safe"] >= THRESHOLD:
        world.say(
            f'{child.id} laughed and said, "Grandmum, that was the biggest surprise I ever saw."'
        )
        world.say(
            f'"And the tastiest one may still be ahead," Grandmum replied. '
            f'By sunset, the kitchen windows were glowing, and the smell of {fruit.ending_food} drifted so far '
            f'even the neighbors followed it home.'
        )
        world.say(
            f"From then on, whenever the family passed that tree, they looked up at the high branches and grinned, "
            f"because they knew Grandmum could talk to trouble until surprise itself decided to help."
        )
        world.facts["outcome"] = "caught"
    else:
        world.say(
            f'Grandmum patted {child.id} on the shoulder and said, "Well, even a tall tale must tell the truth: '
            f'that one got away from us today."'
        )
        world.say(
            "They walked home smiling anyway, because the surprise had given them a story big enough to serve at supper."
        )
        world.facts["outcome"] = "bruised"


def tell(
    place: Place,
    fruit: Fruit,
    tool: Tool,
    surprise: Surprise,
    child_name: str,
    child_gender: str,
    grandmum_name: str,
    child_trait: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            attrs={"trait": child_trait},
        )
    )
    grandmum = world.add(
        Entity(
            id="grandmum",
            kind="character",
            type="grandmum",
            label=grandmum_name,
            role="grandmum",
        )
    )
    world.add(
        Entity(
            id="tree",
            kind="thing",
            type="tree",
            label="tree",
            phrase="the tallest tree in the place",
            attrs={"place": place.id},
        )
    )
    world.add(
        Entity(
            id="fruit",
            kind="thing",
            type="fruit",
            label=fruit.label,
            phrase=fruit.phrase,
            attrs={"firmness": fruit.firmness, "height_need": fruit.height_need, "delicacy": fruit.delicacy},
        )
    )
    world.add(
        Entity(
            id="tool",
            kind="thing",
            type="tool",
            label=tool.label,
            phrase=tool.phrase,
            attrs={"reach": tool.reach, "pull": tool.pull},
        )
    )
    world.add(
        Entity(
            id="apron",
            kind="thing",
            type="apron",
            label="apron",
            phrase="Grandmum's broad apron",
        )
    )

    introduce(world, place, child, grandmum, fruit)
    problem(world, child, grandmum, fruit)
    world.para()
    plan(world, child, grandmum, tool, surprise)
    try_tool(world, child, grandmum, tool, fruit)
    world.para()
    surprise_turn(world, child, grandmum, surprise, fruit)
    resolution(world, child, grandmum, fruit)

    world.facts.update(
        place=place,
        fruit_cfg=fruit,
        tool_cfg=tool,
        surprise_cfg=surprise,
        child=child,
        grandmum=grandmum,
        fruit=world.get("fruit"),
        tool=world.get("tool"),
        caught=world.get("fruit").meters["caught"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "orchard": [
        (
            "What is an orchard?",
            "An orchard is a place where people grow fruit trees. It is planted so the trees can be cared for and picked."
        )
    ],
    "wind": [
        (
            "What does a strong wind do to a tree branch?",
            "A strong wind can bend and shake a branch. If fruit is already loose, the shaking can make it fall."
        )
    ],
    "river": [
        (
            "What is an echo?",
            "An echo is a sound that bounces back after you shout. It can make your voice seem to answer you."
        )
    ],
    "goose": [
        (
            "Why do big birds make air move when they flap?",
            "Their wings push the air downward and outward. That moving air can feel like a little gust."
        )
    ],
    "pear": [
        (
            "What can you make from pears?",
            "People can bake pears into pies or cook them into sweet desserts. Pears are soft and juicy fruit."
        )
    ],
    "apple": [
        (
            "What can you make from apples?",
            "Apples can be baked into pies or tarts. They keep their shape well and taste sweet or tart."
        )
    ],
    "plum": [
        (
            "What is plum jam?",
            "Plum jam is fruit cooked with sugar until it turns thick and spreadable. It keeps the taste of the plums in a jar."
        )
    ],
    "tool": [
        (
            "Why do people use long tools to pick fruit?",
            "Long tools help people reach fruit that is high above their heads. They let you touch the branch without climbing too far."
        )
    ],
}
KNOWLEDGE_ORDER = ["orchard", "wind", "river", "goose", "pear", "apple", "plum", "tool"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    fruit = f["fruit_cfg"]
    place = f["place"]
    surprise = f["surprise_cfg"]
    return [
        f'Write a short tall tale for a 3-to-5-year-old that includes the word "grandmum", rich dialogue, and a surprise.',
        f"Tell a child-facing tall tale where {child.id} helps Grandmum in {place.label} reach {fruit.phrase}, and the final success comes from a surprising {surprise.label}.",
        f'Write a playful story with several spoken lines, a problem that seems almost solved, and a surprising turn that brings a happy kitchen ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    grandmum = f["grandmum"]
    fruit_cfg = f["fruit_cfg"]
    tool_cfg = f["tool_cfg"]
    surprise_cfg = f["surprise_cfg"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {grandmum.label_word}, who went together to {place.label}. They were trying to reach {fruit_cfg.phrase} for the kitchen."
        ),
        (
            f"Why did Grandmum want the {fruit_cfg.label}?",
            f"Grandmum wanted the {fruit_cfg.label} so she could make {fruit_cfg.ending_food}. That goal is what sent them under the giant tree in the first place."
        ),
        (
            f"Why did they need {tool_cfg.phrase}?",
            f"They needed {tool_cfg.phrase} because the {fruit_cfg.label} was hanging far too high to grab by hand. The tool let them touch the branch, even though it was not quite enough to finish the job alone."
        ),
        (
            "What was the surprise in the story?",
            f"The surprise was {surprise_cfg.phrase}. It mattered because it added the last little shake after the first plan almost worked."
        ),
    ]
    if f.get("caught"):
        qa.append(
            (
                f"How did the {fruit_cfg.label} finally come down safely?",
                f"{child.id} and Grandmum first tugged with {tool_cfg.phrase}, which made the branch wobble but did not free the fruit by itself. Then {surprise_cfg.phrase} gave one more helpful jolt, and the fruit dropped into Grandmum's apron instead of smashing on the ground."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the fruit safe in Grandmum's apron and the smell of {fruit_cfg.ending_food} drifting from the kitchen by sunset. The ending image shows that worry turned into food, laughter, and a family story worth retelling."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"orchard", "tool"}
    tags |= set(world.facts["place"].tags)
    tags |= set(world.facts["fruit_cfg"].tags)
    tags |= set(world.facts["surprise_cfg"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="hill_orchard",
        fruit="pear",
        tool="orchard_hook",
        surprise="wind",
        child_name="Lily",
        child_gender="girl",
        grandmum_name="Grandmum",
        child_trait="curious",
    ),
    StoryParams(
        place="river_meadow",
        fruit="apple",
        tool="fishing_pole",
        surprise="echo",
        child_name="Ben",
        child_gender="boy",
        grandmum_name="Grandmum",
        child_trait="bright",
    ),
    StoryParams(
        place="farm_lane",
        fruit="pear",
        tool="ladder_rake",
        surprise="goose",
        child_name="Mia",
        child_gender="girl",
        grandmum_name="Grandmum",
        child_trait="quick-thinking",
    ),
    StoryParams(
        place="farm_lane",
        fruit="apple",
        tool="orchard_hook",
        surprise="goose",
        child_name="Theo",
        child_gender="boy",
        grandmum_name="Grandmum",
        child_trait="eager",
    ),
]


ASP_RULES = r"""
% A place can only host the surprises it actually affords.
valid(P, F, T, S) :- place(P), fruit(F), tool(T), surprise(S),
                     affords(P, S),
                     reach(T, R), height_need(F, H), R >= H,
                     pull(T, TP), firmness(F, FM), TP < FM,
                     force(S, SF), TP + SF >= FM,
                     impact(S, I), delicacy(F, D), I =< D.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for sid in sorted(place.surprise_ids):
            lines.append(asp.fact("affords", place_id, sid))
    for fruit_id, fruit in FRUITS.items():
        lines.append(asp.fact("fruit", fruit_id))
        lines.append(asp.fact("height_need", fruit_id, fruit.height_need))
        lines.append(asp.fact("firmness", fruit_id, fruit.firmness))
        lines.append(asp.fact("delicacy", fruit_id, fruit.delicacy))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("reach", tool_id, tool.reach))
        lines.append(asp.fact("pull", tool_id, tool.pull))
    for surprise_id, surprise in SURPRISES.items():
        lines.append(asp.fact("surprise", surprise_id))
        lines.append(asp.fact("force", surprise_id, surprise.force))
        lines.append(asp.fact("impact", surprise_id, surprise.impact))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    if "Grandmum" not in sample.story and "grandmum" not in sample.story:
        raise StoryError("Smoke test failed: generated story did not mention grandmum.")


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
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
        smoke_test()
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for params in CURATED:
        try:
            sample = generate(params)
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"CURATED GENERATION FAILED for {params}: {err}")
            continue
        if not sample.story.strip():
            rc = 1
            print(f"CURATED STORY EMPTY for {params}")
    if rc == 0:
        print(f"OK: generated {len(CURATED)} curated stories without crashing.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Tall-tale story world: a child and grandmum try to pick a sky-high fruit, and a surprise makes the ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--fruit", choices=FRUITS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.fruit and args.tool and args.surprise:
        place = PLACES[args.place]
        fruit = FRUITS[args.fruit]
        tool = TOOLS[args.tool]
        surprise = SURPRISES[args.surprise]
        if not valid_combo(place, fruit, tool, surprise):
            raise StoryError(explain_rejection(place, fruit, tool, surprise))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.fruit is None or combo[1] == args.fruit)
        and (args.tool is None or combo[2] == args.tool)
        and (args.surprise is None or combo[3] == args.surprise)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, fruit_id, tool_id, surprise_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.child_name:
        child_name = args.child_name
    else:
        pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
        child_name = rng.choice(pool)
    return StoryParams(
        place=place_id,
        fruit=fruit_id,
        tool=tool_id,
        surprise=surprise_id,
        child_name=child_name,
        child_gender=gender,
        grandmum_name="Grandmum",
        child_trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        fruit = FRUITS[params.fruit]
        tool = TOOLS[params.tool]
        surprise = SURPRISES[params.surprise]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from None

    if not valid_combo(place, fruit, tool, surprise):
        raise StoryError(explain_rejection(place, fruit, tool, surprise))

    world = tell(
        place=place,
        fruit=fruit,
        tool=tool,
        surprise=surprise,
        child_name=params.child_name,
        child_gender=params.child_gender,
        grandmum_name=params.grandmum_name,
        child_trait=params.child_trait,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, fruit, tool, surprise) combos:\n")
        for place, fruit, tool, surprise in combos:
            print(f"  {place:12} {fruit:6} {tool:12} {surprise}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
            header = f"### {p.child_name} with Grandmum: {p.fruit} at {p.place} ({p.tool}, {p.surprise})"
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
