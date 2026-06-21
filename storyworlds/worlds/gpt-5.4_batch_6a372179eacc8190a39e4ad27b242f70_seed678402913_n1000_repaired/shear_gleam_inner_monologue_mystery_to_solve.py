#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/shear_gleam_inner_monologue_mystery_to_solve.py
============================================================================

A standalone storyworld about two children playing pirates who spot a bright
gleam and try to solve a small mystery together. The domain rebuilds one tight
family of tales:

- a pretend pirate adventure gives them a reason to search,
- a mysterious gleam appears in some tricky place,
- one child is tempted to use garden shears in an unsafe way,
- the other child thinks through the danger in an inner monologue,
- a grown-up helps them choose a sensible retrieval tool,
- teamwork solves the mystery,
- the ending image proves what changed.

The world enforces a real compatibility rule: different hiding places and
different shiny objects call for different safe tools. It refuses combinations
where the proposed tool would not honestly work.

Run it
------
    python storyworlds/worlds/gpt-5.4/shear_gleam_inner_monologue_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/shear_gleam_inner_monologue_mystery_to_solve.py --place tide_pool --shiny key --tool magnet
    python storyworlds/worlds/gpt-5.4/shear_gleam_inner_monologue_mystery_to_solve.py --place thorn_bush --tool magnet
    python storyworlds/worlds/gpt-5.4/shear_gleam_inner_monologue_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/shear_gleam_inner_monologue_mystery_to_solve.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/shear_gleam_inner_monologue_mystery_to_solve.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    sharp: bool = False
    magnetic: bool = False
    snaggy: bool = False
    reachable: bool = False
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
class Theme:
    id: str
    scene: str
    rig: str
    titles: tuple[str, str]
    mission: str
    finish: str


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    clue: str
    reach_problem: str
    danger: str
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class ShinyThing:
    id: str
    label: str
    phrase: str
    owner: str
    clue_text: str
    metal: bool = False
    delicate: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeTool:
    id: str
    label: str
    phrase: str
    works_for: set[str] = field(default_factory=set)
    needs_metal: bool = False
    gentle: bool = False
    action: str = ""
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_scratch_risk(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("instigator")
    hazard = world.get("hazard")
    if child.memes["using_shears"] < THRESHOLD:
        return out
    if hazard.meters["tangled"] < THRESHOLD and hazard.meters["deep"] < THRESHOLD:
        return out
    sig = ("scratch_risk",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["risk"] += 1
    world.get("cautioner").memes["worry"] += 1
    out.append("__risk__")
    return out


def _r_tool_success(world: World) -> list[str]:
    helper = world.get("helper_tool")
    target = world.get("shiny")
    hazard = world.get("hazard")
    if helper.meters["used"] < THRESHOLD:
        return []
    sig = ("tool_success", helper.id, target.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if world.facts.get("tool_works", False):
        target.meters["retrieved"] += 1
        hazard.meters["solved"] += 1
        world.get("instigator").memes["relief"] += 1
        world.get("cautioner").memes["relief"] += 1
        return ["__retrieved__"]
    return []


CAUSAL_RULES = [
    Rule(name="scratch_risk", tag="safety", apply=_r_scratch_risk),
    Rule(name="tool_success", tag="physical", apply=_r_tool_success),
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


def tool_compatible(place: Place, shiny: ShinyThing, tool: SafeTool) -> bool:
    if place.id not in tool.works_for:
        return False
    if tool.needs_metal and not shiny.metal:
        return False
    if shiny.delicate and not tool.gentle and place.id == "tide_pool":
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for shiny_id, shiny in SHINY.items():
            for tool_id, tool in TOOLS.items():
                if tool_compatible(place, shiny, tool):
                    combos.append((place_id, shiny_id, tool_id))
    return combos


def predict_shears(world: World) -> dict:
    sim = world.copy()
    sim.get("instigator").memes["using_shears"] += 1
    propagate(sim, narrate=False)
    return {
        "risk": sim.get("instigator").memes["risk"],
        "worry": sim.get("cautioner").memes["worry"],
    }


def introduce(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    title_a, title_b = theme.titles
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} turned the yard into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{title_a} {a.id} and {title_b} {b.id}!" {a.id} cried. "{theme.mission}"'
    )


def discover(world: World, a: Entity, b: Entity, place: Place) -> None:
    world.say(
        f"They prowled past {place.phrase} when a tiny gleam blinked back at them. "
        f"It flashed once, then hid again."
    )
    world.say(
        f'"Treasure," whispered {b.id}. But nobody could tell what the bright thing was yet.'
    )
    world.say(place.clue)


def inner_monologue(world: World, b: Entity, place: Place) -> None:
    b.memes["thinking"] += 1
    world.say(
        f"{b.id} peered closer and thought, "
        f'"If we rush, we could make it worse. {place.reach_problem}"'
    )


def tempt(world: World, a: Entity) -> None:
    a.memes["impulse"] += 1
    world.say(
        f'{a.id} spotted the garden shear hanging by the shed. '
        f'"I could snip and poke until the treasure comes loose," {a.pronoun()} said.'
    )


def warn(world: World, b: Entity, a: Entity, place: Place) -> None:
    pred = predict_shears(world)
    world.facts["predicted_risk"] = pred["risk"]
    b.memes["caution"] += 1
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. '
        f'"No, {a.id}. The shear is sharp, and {place.danger}. '
        f'We need a clever pirate plan, not a poking one."'
    )


def call_adult(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    world.say(
        f'So instead of grabbing the shear, they called for {parent.label_word}. '
        f'"Can you help us solve a mystery?" {a.id} asked.'
    )


def choose_tool(world: World, parent: Entity, place: Place, shiny: ShinyThing, tool: SafeTool) -> None:
    world.facts["tool_works"] = tool_compatible(place, shiny, tool)
    world.say(
        f"{parent.label_word.capitalize()} listened, looked at the hiding place, and smiled. "
        f'"Then we choose the right tool for the job," {parent.pronoun()} said.'
    )
    world.say(
        f"{parent.pronoun().capitalize()} brought {tool.phrase} and showed the children how to work together."
    )


def teamwork_attempt(world: World, a: Entity, b: Entity, tool: SafeTool, shiny: ShinyThing) -> None:
    helper = world.get("helper_tool")
    helper.meters["used"] += 1
    a.memes["cooperate"] += 1
    b.memes["cooperate"] += 1
    world.say(
        f"{a.id} held steady while {b.id} watched the angle, and together they {tool.action}."
    )
    propagate(world, narrate=False)
    if world.get("shiny").meters["retrieved"] >= THRESHOLD:
        world.say(
            f"Out came {shiny.phrase}, clean and safe in the sunlight."
        )
    else:
        world.say(
            f"They tried carefully, but the tool was wrong for that hiding place, and the little gleam stayed put."
        )


def reveal(world: World, parent: Entity, shiny: ShinyThing, theme: Theme) -> None:
    a = world.get("instigator")
    b = world.get("cautioner")
    a.memes["wonder"] += 1
    b.memes["wonder"] += 1
    world.say(
        f'It was not pirate gold after all. It was {shiny.phrase} -- {shiny.clue_text}.'
    )
    world.say(
        f'"A real mystery solved," said {parent.label_word}, and both little {theme.finish} grinned.'
    )


def resolve(world: World, a: Entity, b: Entity, parent: Entity, shiny: ShinyThing, theme: Theme) -> None:
    a.memes["lesson"] += 1
    b.memes["lesson"] += 1
    world.say(
        f'{a.id} looked at the waiting shear by the shed and felt glad {a.pronoun()} had not used it.'
    )
    world.say(
        f'"Good crews think first," {b.id} said softly.'
    )
    world.say(
        f"Then the two {theme.finish} carried {shiny.label} back to {shiny.owner}, proud because they had solved the mystery with teamwork instead of hurry."
    )


def tell(
    theme: Theme,
    place: Place,
    shiny: ShinyThing,
    tool: SafeTool,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World()
    a = world.add(Entity(id="instigator", kind="character", type=instigator_gender, label=instigator, phrase=instigator, role="instigator"))
    b = world.add(Entity(id="cautioner", kind="character", type=cautioner_gender, label=cautioner, phrase=cautioner, role="cautioner"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", phrase="the parent", role="parent"))
    hazard = world.add(Entity(id="hazard", kind="thing", type="place", label=place.label, phrase=place.phrase))
    shiny_ent = world.add(Entity(id="shiny", kind="thing", type="shiny", label=shiny.label, phrase=shiny.phrase, magnetic=shiny.metal))
    helper = world.add(Entity(id="helper_tool", kind="thing", type="tool", label=tool.label, phrase=tool.phrase))
    shears = world.add(Entity(id="shears", kind="thing", type="tool", label="garden shear", phrase="the garden shear", sharp=True))

    if place.id in {"thorn_bush", "rope_net"}:
        hazard.meters["tangled"] += 1
    if place.id in {"tide_pool", "crack"}:
        hazard.meters["deep"] += 1

    world.facts.update(
        theme=theme,
        place=place,
        shiny_cfg=shiny,
        tool_cfg=tool,
        instigator_name=instigator,
        cautioner_name=cautioner,
        parent=parent,
    )

    introduce(world, a, b, theme)
    discover(world, a, b, place)

    world.para()
    inner_monologue(world, b, place)
    tempt(world, a)
    warn(world, b, a, place)
    call_adult(world, parent, a, b)

    world.para()
    choose_tool(world, parent, place, shiny, tool)
    teamwork_attempt(world, a, b, tool, shiny)
    if shiny_ent.meters["retrieved"] < THRESHOLD:
        raise StoryError("(No story: the chosen tool cannot solve this mystery safely.)")
    reveal(world, parent, shiny, theme)
    resolve(world, a, b, parent, shiny, theme)

    world.facts.update(
        retrieved=shiny_ent.meters["retrieved"] >= THRESHOLD,
        shears_avoided=True,
        teamwork=a.memes["cooperate"] >= THRESHOLD and b.memes["cooperate"] >= THRESHOLD,
        a=a,
        b=b,
    )
    return world


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a pirate harbor",
        rig="The sandbox became a sandy cove, an old bench became a ship, and a rolled towel served as their treasure map.",
        titles=("Captain", "Scout"),
        mission="Find the lost silver before sunset!",
        finish="pirates",
    ),
    "raiders": Theme(
        id="raiders",
        scene="a wild island port",
        rig="A wheelbarrow became a sea boat, a stick became a mast, and three chalk arrows pointed toward hidden treasure.",
        titles=("Captain", "Lookout"),
        mission="Search every corner for the missing treasure!",
        finish="raiders",
    ),
}

PLACES = {
    "thorn_bush": Place(
        id="thorn_bush",
        label="thorn bush",
        phrase="the thorn bush by the fence",
        clue="A silver wink flickered between the leaves, deep behind the thorns.",
        reach_problem="The thorns could scratch us and snag anything we push in there.",
        danger="someone could get scratched, and the treasure might be scraped too",
        needs={"grip", "gentle"},
        tags={"thorns", "bush"},
    ),
    "tide_pool": Place(
        id="tide_pool",
        label="tide pool",
        phrase="the little stone basin they called the tide pool",
        clue="At the bottom, under clear water, something bright gave a cold little gleam.",
        reach_problem="If we stir the water and scrape around, the shiny thing could slide deeper into the crack.",
        danger="someone could slip on the wet stones, and the shiny thing could vanish deeper",
        needs={"magnet", "gentle"},
        tags={"water", "pool"},
    ),
    "rope_net": Place(
        id="rope_net",
        label="rope net",
        phrase="the old rope net hanging from two posts",
        clue="High in the knots, a bright speck blinked whenever the rope swayed.",
        reach_problem="If we slash at the ropes, we could cut the net and drop the mystery into the dirt.",
        danger="someone could cut the rope and make the hidden thing fall and bend",
        needs={"lift"},
        tags={"rope", "net"},
    ),
    "crack": Place(
        id="crack",
        label="stone crack",
        phrase="the crack between two big garden stones",
        clue="From the narrow dark line came a quick blade of gleam, then nothing.",
        reach_problem="The crack is too narrow for fingers, and a hard jab could wedge the shiny thing tighter.",
        danger="the sharp blades could slip, and the mystery could get stuck even harder",
        needs={"grip", "gentle"},
        tags={"stone", "crack"},
    ),
}

SHINY = {
    "key": ShinyThing(
        id="key",
        label="a silver key",
        phrase="a silver key on a blue string",
        owner="Grandpa",
        clue_text="Grandpa's missing shed key, still tied to its blue string",
        metal=True,
        delicate=False,
        tags={"key", "metal"},
    ),
    "bracelet": ShinyThing(
        id="bracelet",
        label="a little bracelet",
        phrase="a little bracelet with a moon charm",
        owner="Mom",
        clue_text="Mom's lost bracelet, the one with the moon charm she had been searching for",
        metal=True,
        delicate=True,
        tags={"bracelet", "metal"},
    ),
    "coin": ShinyThing(
        id="coin",
        label="a toy coin",
        phrase="a toy pirate coin painted gold",
        owner="the neighbor child",
        clue_text="the neighbor child's toy pirate coin from yesterday's game",
        metal=False,
        delicate=False,
        tags={"coin", "toy"},
    ),
}

TOOLS = {
    "magnet": SafeTool(
        id="magnet",
        label="magnet on a string",
        phrase="a magnet tied to a long string",
        works_for={"tide_pool", "crack"},
        needs_metal=True,
        gentle=True,
        action="lowered the magnet slowly until it kissed the hidden shine",
        tags={"magnet"},
    ),
    "grabber": SafeTool(
        id="grabber",
        label="grabber",
        phrase="a long rubber-tipped grabber",
        works_for={"thorn_bush", "crack"},
        needs_metal=False,
        gentle=True,
        action="reached in a tiny bit at a time and pinched the hidden thing without scraping it",
        tags={"grabber"},
    ),
    "stool_hook": SafeTool(
        id="stool_hook",
        label="step stool and boat hook",
        phrase="a step stool and a little boat hook made from a bent stick",
        works_for={"rope_net"},
        needs_metal=False,
        gentle=False,
        action="climbed one safe step and lifted the knot loose with the hook",
        tags={"stool", "hook"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]


@dataclass
class StoryParams:
    theme: str
    place: str
    shiny: str
    tool: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        theme="pirates",
        place="thorn_bush",
        shiny="bracelet",
        tool="grabber",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
    ),
    StoryParams(
        theme="pirates",
        place="tide_pool",
        shiny="key",
        tool="magnet",
        instigator="Ben",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        parent="father",
    ),
    StoryParams(
        theme="raiders",
        place="rope_net",
        shiny="coin",
        tool="stool_hook",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Zoe",
        cautioner_gender="girl",
        parent="mother",
    ),
    StoryParams(
        theme="raiders",
        place="crack",
        shiny="bracelet",
        tool="grabber",
        instigator="Noah",
        instigator_gender="boy",
        cautioner="Ella",
        cautioner_gender="girl",
        parent="father",
    ),
]


KNOWLEDGE = {
    "shears": [(
        "What are garden shears?",
        "Garden shears are sharp tools grown-ups use to cut plants. Children should not wave them around or poke with them."
    )],
    "magnet": [(
        "What does a magnet do?",
        "A magnet can pull some metal things toward it. It is useful when a metal object is hard to reach."
    )],
    "grabber": [(
        "What is a grabber tool?",
        "A grabber is a long tool that lets you pinch and lift something from far away. It helps you reach without sticking your hand into a tricky place."
    )],
    "thorns": [(
        "Why are thorns tricky?",
        "Thorns are sharp points on some plants. They can scratch your skin and snag clothes or bracelets."
    )],
    "teamwork": [(
        "What is teamwork?",
        "Teamwork means people help one another do one job together. One person can steady, another can watch, and together they solve the problem better."
    )],
    "mystery": [(
        "What is a mystery?",
        "A mystery is something you do not understand yet, but can figure out by looking carefully and thinking. Solving it means learning what was hidden."
    )],
    "gleam": [(
        "What is a gleam?",
        "A gleam is a quick bright shine. Something smooth or shiny can make a gleam when light hits it."
    )],
}
KNOWLEDGE_ORDER = ["shears", "gleam", "mystery", "teamwork", "thorns", "magnet", "grabber"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    shiny = f["shiny_cfg"]
    a = f["instigator_name"]
    b = f["cautioner_name"]
    return [
        f'Write a pirate-play story for a 3-to-5-year-old that includes the words "shear" and "gleam" and centers on a small mystery to solve.',
        f"Tell a gentle mystery where {a} and {b} spot a bright gleam in {place.phrase}, avoid using a shear, and solve the problem with teamwork.",
        f"Write a story with a child's inner monologue, a hidden shiny object, and a calm grown-up who helps choose the right tool.",
    ]


def pair_noun(a_gender: str, b_gender: str) -> str:
    if a_gender == "boy" and b_gender == "boy":
        return "two boys"
    if a_gender == "girl" and b_gender == "girl":
        return "two girls"
    return "a boy and a girl"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a_name = f["instigator_name"]
    b_name = f["cautioner_name"]
    place = f["place"]
    shiny = f["shiny_cfg"]
    tool = f["tool_cfg"]
    parent = f["parent"]
    pair = pair_noun(world.get("instigator").type, world.get("cautioner").type)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a_name} and {b_name}, pretending to be pirates while they searched for treasure. It is also about their {parent.label_word}, who helped them solve the mystery safely."
        ),
        (
            "What was the mystery?",
            f"They saw a little gleam in {place.phrase} but did not know what was shining there. The mystery was to find out what the hidden bright thing really was."
        ),
        (
            f"Why did {b_name} not want {a_name} to use the shear?",
            f"{b_name} thought the sharp shear could be dangerous in that hiding place. {place.danger.capitalize()}, so hurrying with a sharp tool could hurt someone or damage the shiny thing."
        ),
        (
            f"What was {b_name}'s inner thought?",
            f"{b_name} told {b_name.lower() if b_name.islower() else 'themself'} to slow down and think before acting. {place.reach_problem} That thought is what turned the adventure from poking and guessing into careful problem-solving."
        ),
        (
            "How did they solve the mystery?",
            f"They asked a grown-up for help, chose {tool.phrase}, and worked as a team. One child held steady while the other watched closely, so the right tool could do the job safely."
        ),
        (
            "What was the shiny thing in the end?",
            f"It turned out to be {shiny.phrase}. The ending solves the mystery by showing exactly what had been making the bright gleam."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"shears", "gleam", "mystery", "teamwork"}
    place = world.facts["place"]
    tool = world.facts["tool_cfg"]
    if "thorns" in place.tags or place.id == "thorn_bush":
        tags.add("thorns")
    if tool.id == "magnet":
        tags.add("magnet")
    if tool.id == "grabber":
        tags.add("grabber")
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
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (("sharp", e.sharp), ("magnetic", e.magnetic)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, shiny: ShinyThing, tool: SafeTool) -> str:
    if place.id not in tool.works_for:
        return (
            f"(No story: {tool.label} does not fit {place.label}. The fix must honestly match the hiding place.)"
        )
    if tool.needs_metal and not shiny.metal:
        return (
            f"(No story: {tool.label} only helps with metal objects, but {shiny.label} is not metal.)"
        )
    if shiny.delicate and not tool.gentle and place.id == "tide_pool":
        return (
            f"(No story: {tool.label} is too rough for {shiny.label} in the wet stones. The safe solution must protect the object too.)"
        )
    return "(No story: this tool cannot solve that mystery safely.)"


ASP_RULES = r"""
fits_place(Tool, Place) :- tool(Tool), place(Place), works_for(Tool, Place).
works(Tool, Place, Shiny) :- fits_place(Tool, Place),
                             shiny(Shiny),
                             not requires_metal(Tool).
works(Tool, Place, Shiny) :- fits_place(Tool, Place),
                             shiny(Shiny),
                             requires_metal(Tool),
                             metal(Shiny).
invalid_delicate(Tool, Place, Shiny) :- delicate(Shiny), rough(Tool), place_kind(Place, tide_pool).
valid(Place, Shiny, Tool) :- works(Tool, Place, Shiny), not invalid_delicate(Tool, Place, Shiny).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for theme in THEMES:
        lines.append(asp.fact("theme", theme))
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("place_kind", place_id, place_id))
    for shiny_id, shiny in SHINY.items():
        lines.append(asp.fact("shiny", shiny_id))
        if shiny.metal:
            lines.append(asp.fact("metal", shiny_id))
        if shiny.delicate:
            lines.append(asp.fact("delicate", shiny_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for place_id in sorted(tool.works_for):
            lines.append(asp.fact("works_for", tool_id, place_id))
        if tool.needs_metal:
            lines.append(asp.fact("requires_metal", tool_id))
        if not tool.gentle:
            lines.append(asp.fact("rough", tool_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "gleam" not in sample.story or "shear" not in sample.story:
            raise StoryError("(Smoke test failed: generated story missed required words.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirate-play, a gleam, a mystery, and a safe teamwork solution."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--shiny", choices=SHINY)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches Python and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.shiny and args.tool:
        if not tool_compatible(PLACES[args.place], SHINY[args.shiny], TOOLS[args.tool]):
            raise StoryError(explain_rejection(PLACES[args.place], SHINY[args.shiny], TOOLS[args.tool]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.shiny is None or combo[1] == args.shiny)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, shiny_id, tool_id = rng.choice(sorted(combos))
    theme_id = args.theme or rng.choice(sorted(THEMES))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        theme=theme_id,
        place=place_id,
        shiny=shiny_id,
        tool=tool_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Invalid theme: {params.theme})")
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.shiny not in SHINY:
        raise StoryError(f"(Invalid shiny object: {params.shiny})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Invalid tool: {params.tool})")
    if not tool_compatible(PLACES[params.place], SHINY[params.shiny], TOOLS[params.tool]):
        raise StoryError(explain_rejection(PLACES[params.place], SHINY[params.shiny], TOOLS[params.tool]))

    world = tell(
        theme=THEMES[params.theme],
        place=PLACES[params.place],
        shiny=SHINY[params.shiny],
        tool=TOOLS[params.tool],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
    )

    return StorySample(
        params=params,
        story=world.render().replace("instigator", params.instigator).replace("cautioner", params.cautioner),
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
        print(f"{len(combos)} compatible (place, shiny, tool) combos:\n")
        for place, shiny, tool in combos:
            print(f"  {place:12} {shiny:10} {tool}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.shiny} in {p.place} ({p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
