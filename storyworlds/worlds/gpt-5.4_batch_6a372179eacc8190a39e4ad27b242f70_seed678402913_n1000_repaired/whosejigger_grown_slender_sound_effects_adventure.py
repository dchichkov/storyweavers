#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/whosejigger_grown_slender_sound_effects_adventure.py
==============================================================================

A standalone story world for a tiny adventure domain: two children discover that
something important is out of reach in a place that has grown wild, and they
must choose a sensible tool instead of trusting a slender, risky shortcut.

The special seed words are built into the domain:
- "whosejigger" names the grabber-like rescue tools
- "grown" appears in the setting descriptions
- "slender" appears in the risky shortcut descriptions

The world model tracks both physical meters and emotional memes. The prose comes
from the simulated state: spotting the lost object, predicting the danger of the
slender shortcut, using the right whosejigger, and ending with a changed scene.

Run it
------
    python storyworlds/worlds/gpt-5.4/whosejigger_grown_slender_sound_effects_adventure.py
    python storyworlds/worlds/gpt-5.4/whosejigger_grown_slender_sound_effects_adventure.py --mission brook_map --tool net_whosejigger
    python storyworlds/worlds/gpt-5.4/whosejigger_grown_slender_sound_effects_adventure.py --mission arch_key --tool magnet_whosejigger
    python storyworlds/worlds/gpt-5.4/whosejigger_grown_slender_sound_effects_adventure.py --tool flimsy_stick
    python storyworlds/worlds/gpt-5.4/whosejigger_grown_slender_sound_effects_adventure.py --all
    python storyworlds/worlds/gpt-5.4/whosejigger_grown_slender_sound_effects_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/whosejigger_grown_slender_sound_effects_adventure.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    path_sound: str
    grown_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    goal_label: str
    goal_phrase: str
    place_spot: str
    hook_line: str
    risk_plan: str
    slender_thing: str
    obstacle: str
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    capabilities: set[str] = field(default_factory=set)
    sense: int = 2
    use_sound: str = ""
    reach_text: str = ""
    success_text: str = ""
    qa_text: str = ""
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    leader = world.entities.get("leader")
    if leader is None:
        return out
    if leader.meters["on_slender"] < THRESHOLD:
        return out
    sig = ("wobble", leader.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    leader.meters["wobble"] += 1
    leader.memes["fear"] += 1
    room = world.entities.get("scene")
    if room is not None:
        room.meters["danger"] += 1
    helper = world.entities.get("helper")
    if helper is not None:
        helper.memes["worry"] += 1
    out.append("__wobble__")
    return out


def _r_retrieve(world: World) -> list[str]:
    out: list[str] = []
    tool = world.entities.get("tool")
    goal = world.entities.get("goal")
    if tool is None or goal is None:
        return out
    if tool.meters["used"] < THRESHOLD:
        return out
    mission_needs = set(world.facts.get("mission_needs", set()))
    tool_caps = set(tool.attrs.get("capabilities", set()))
    if not (mission_needs & tool_caps):
        return out
    sig = ("retrieve", tool.id, goal.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    goal.meters["retrieved"] += 1
    goal.meters["distance"] = 0.0
    leader = world.entities.get("leader")
    helper = world.entities.get("helper")
    if leader is not None:
        leader.memes["relief"] += 1
        leader.memes["pride"] += 1
    if helper is not None:
        helper.memes["relief"] += 1
        helper.memes["joy"] += 1
    out.append("__retrieved__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="retrieve", tag="physical", apply=_r_retrieve),
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


def tool_works(mission: Mission, tool: Tool) -> bool:
    return bool(mission.needs & tool.capabilities)


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for mission_id, mission in MISSIONS.items():
        for tool_id, tool in TOOLS.items():
            if tool.sense >= SENSE_MIN and tool_works(mission, tool):
                combos.append((mission_id, tool_id))
    return combos


def explain_rejection(mission: Mission, tool: Tool) -> str:
    if tool.sense < SENSE_MIN:
        return (
            f"(No story: {tool.label} is known in the world, but it is too flimsy to be "
            f"a sensible fix. Use a sturdier whosejigger instead.)"
        )
    return (
        f"(No story: {tool.label} does not fit the problem of {mission.goal_phrase}. "
        f"Pick a whosejigger that can really reach or catch it.)"
    )


def predict_wobble(world: World) -> dict:
    sim = world.copy()
    leader = sim.get("leader")
    leader.meters["on_slender"] += 1
    propagate(sim, narrate=False)
    scene = sim.get("scene")
    return {
        "wobble": leader.meters["wobble"] >= THRESHOLD,
        "danger": scene.meters["danger"],
    }


def introduce(world: World, leader: Entity, helper: Entity, place: Place) -> None:
    leader.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{leader.id} and {helper.id} set off on an afternoon adventure in {place.label}. "
        f"{place.opening}"
    )
    world.say(f"{place.grown_line} {place.path_sound}")


def discover(world: World, leader: Entity, helper: Entity, mission: Mission) -> None:
    goal = world.get("goal")
    goal.meters["distance"] = 1.0
    world.say(
        f"Then {leader.id} spotted {mission.goal_phrase} {mission.place_spot}. "
        f"{mission.hook_line}"
    )
    helper.memes["curiosity"] += 1
    leader.memes["desire"] += 1


def risky_idea(world: World, leader: Entity, helper: Entity, mission: Mission) -> None:
    pred = predict_wobble(world)
    world.facts["predicted_danger"] = pred["danger"]
    leader.memes["boldness"] += 1
    helper.memes["worry"] += 1
    world.say(
        f'"I can get it," said {leader.id}. {leader.pronoun().capitalize()} pointed at '
        f"{mission.slender_thing}. {mission.risk_plan}"
    )
    world.say(
        f'{helper.id} shook {helper.pronoun("possessive")} head. '
        f'"That thing is slender. It could wobble under you."'
    )


def test_slender(world: World, leader: Entity, mission: Mission) -> None:
    leader.meters["on_slender"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{leader.id} put one foot on {mission.slender_thing}. "
        f"Cre-eeak! {mission.obstacle} suddenly felt bigger."
    )


def choose_tool(world: World, helper: Entity, tool: Tool, parent: Entity) -> None:
    helper.memes["idea"] += 1
    world.say(
        f'"Wait," said {helper.id}. "{parent.label_word.capitalize()} keeps a {tool.label} '
        f'in the shed. That whosejigger is for tricky reaches."'
    )


def fetch_tool(world: World, leader: Entity, helper: Entity, tool: Tool) -> None:
    world.say(
        f"They ran to the shed and came back with {tool.phrase}. "
        f"{tool.use_sound} The adventure suddenly felt possible again."
    )
    world.get("tool").attrs["capabilities"] = set(tool.capabilities)


def use_tool(world: World, leader: Entity, helper: Entity, tool: Tool, mission: Mission) -> None:
    tool_ent = world.get("tool")
    tool_ent.meters["used"] += 1
    propagate(world, narrate=False)
    world.say(tool.reach_text.format(leader=leader.id, helper=helper.id, goal=mission.goal_label))
    if world.get("goal").meters["retrieved"] >= THRESHOLD:
        world.say(tool.success_text.format(goal=mission.goal_label))
    else:
        raise StoryError("(Internal story failure: a chosen valid tool did not retrieve the goal.)")


def celebrate(world: World, leader: Entity, helper: Entity, place: Place, mission: Mission) -> None:
    goal = world.get("goal")
    leader.meters["on_slender"] = 0.0
    leader.meters["wobble"] = 0.0
    world.get("scene").meters["danger"] = 0.0
    world.say(
        f'{helper.id} clapped. "{mission.goal_label.capitalize()} rescued!"'
    )
    if goal.meters["retrieved"] >= THRESHOLD:
        world.say(
            f"They turned back along the path with {mission.goal_phrase} safe at last. "
            f"{place.ending_image}"
        )


def tell(
    place: Place,
    mission: Mission,
    tool: Tool,
    leader_name: str = "Mira",
    leader_type: str = "girl",
    helper_name: str = "Tao",
    helper_type: str = "boy",
    parent_type: str = "grandfather",
    trait: str = "brave",
) -> World:
    world = World()
    leader = world.add(Entity(id="leader", kind="character", type=leader_type, label=leader_name, role="leader"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, role="helper"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the grown-up", role="parent"))
    scene = world.add(Entity(id="scene", kind="thing", type="place", label=place.label))
    goal = world.add(Entity(id="goal", kind="thing", type="goal", label=mission.goal_label, phrase=mission.goal_phrase))
    tool_ent = world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label, phrase=tool.phrase))
    leader.attrs["name"] = leader_name
    helper.attrs["name"] = helper_name
    leader.attrs["trait"] = trait
    world.facts["mission_needs"] = set(mission.needs)

    introduce(world, leader, helper, place)
    discover(world, leader, helper, mission)

    world.para()
    risky_idea(world, leader, helper, mission)
    test_slender(world, leader, mission)
    choose_tool(world, helper, tool, parent)

    world.para()
    fetch_tool(world, leader, helper, tool)
    use_tool(world, leader, helper, tool, mission)
    celebrate(world, leader, helper, place, mission)

    world.facts.update(
        place=place,
        mission=mission,
        tool_cfg=tool,
        leader=leader,
        helper=helper,
        parent=parent,
        goal=goal,
        retrieved=goal.meters["retrieved"] >= THRESHOLD,
        avoided_fall=scene.meters["danger"] == 0.0 and leader.meters["on_slender"] == 0.0,
    )
    return world


KNOWLEDGE = {
    "brook": [(
        "Why can a brook be hard to reach into?",
        "A brook keeps moving, and wet banks can be slippery. That makes it safer to reach with a tool instead of leaning too far."
    )],
    "ivy": [(
        "What is ivy?",
        "Ivy is a climbing plant that wraps around walls, arches, and fences. When it grows thick, it can hide things inside the leaves."
    )],
    "bramble": [(
        "Why are brambles tricky?",
        "Brambles have thorny stems that can scratch your skin and snag cloth. A long tool helps you reach without putting your hands into the thorns."
    )],
    "magnet": [(
        "What does a magnet do?",
        "A magnet pulls on some kinds of metal. That can help lift a small metal object without touching it."
    )],
    "hook": [(
        "What is a hook tool good for?",
        "A hook can catch a loop, ribbon, or edge and pull it closer. It helps when something is dangling or tied."
    )],
    "net": [(
        "What is a net good for?",
        "A net can scoop or hold a light object so it does not slip away. It is useful when something is floating or hard to pinch."
    )],
    "safety": [(
        "Why should you not trust a slender board or branch?",
        "A slender thing can bend, wobble, or crack more easily than a sturdy one. If you are reaching over water or thorns, a safe tool is wiser than balancing there."
    )],
    "shed": [(
        "What might a garden shed hold?",
        "A garden shed often holds tools, string, pots, and other useful things for outdoor jobs. In a story, it can also hold a handy whosejigger."
    )],
}
KNOWLEDGE_ORDER = ["brook", "ivy", "bramble", "magnet", "hook", "net", "safety", "shed"]


PLACES = {
    "garden": Place(
        id="garden",
        label="the old garden behind the shed",
        opening="Mint brushed their knees, and little stones winked in the sun.",
        path_sound="Crunch-crunch went their boots on the path.",
        grown_line="The place had grown wild in the nicest way, with tall beans, ivy, and bright marigolds leaning over the fence.",
        ending_image="The wind whispered through the leaves, and the garden no longer felt like a trap. It felt like a map they now knew how to read.",
        tags={"shed", "ivy"},
    ),
    "orchard": Place(
        id="orchard",
        label="the small orchard beyond the gate",
        opening="Apple shadows rocked on the grass, and every row looked like a secret lane.",
        path_sound="Swish-swish went the long grass around their ankles.",
        grown_line="The orchard had grown soft and leafy after summer rain, with vines curling around the old posts.",
        ending_image="Above them, the branches clicked gently together, as if the orchard were saying yes to one more brave and careful trip.",
        tags={"ivy"},
    ),
}

MISSIONS = {
    "arch_key": Mission(
        id="arch_key",
        goal_label="key",
        goal_phrase="the brass key",
        place_spot="high in the ivy on the garden arch",
        hook_line="It was the tiny key for the painted treasure box they had hoped to open.",
        risk_plan="A narrow root-box stood below it, and beside that lay a slender board that looked just tall enough to stand on.",
        slender_thing="the slender board",
        obstacle="The ivy rustled over their heads.",
        needs={"metal", "hook"},
        tags={"ivy", "magnet", "hook", "safety"},
    ),
    "brook_map": Mission(
        id="brook_map",
        goal_label="map",
        goal_phrase="the rolled-up map tube",
        place_spot="turning in a slow circle beside the brook bank",
        hook_line="Without it, their adventure trail would end before the secret hill.",
        risk_plan="A mossy rock jutted out near the water, and a slender branch reached over the current like a shaky handrail.",
        slender_thing="the slender branch",
        obstacle="Splish-splosh went the brook below.",
        needs={"scoop", "hook"},
        tags={"brook", "net", "hook", "safety"},
    ),
    "bramble_flag": Mission(
        id="bramble_flag",
        goal_label="flag",
        goal_phrase="the red flag",
        place_spot="caught in a bramble patch beside the path",
        hook_line="It was their explorer flag, and the game would feel wrong without it.",
        risk_plan="Near the thorns stood a flower pot turned upside down, with a slender cane laid across it like a tiny bridge.",
        slender_thing="the slender cane",
        obstacle="The brambles gave a scratchy little hiss in the breeze.",
        needs={"hook", "pinch"},
        tags={"bramble", "hook", "safety"},
    ),
}

TOOLS = {
    "magnet_whosejigger": Tool(
        id="magnet_whosejigger",
        label="magnet whosejigger",
        phrase="the magnet whosejigger with the blue handle",
        capabilities={"metal"},
        sense=3,
        use_sound="Click-click!",
        reach_text="{leader} held the pole steady while {helper} guided the tip upward, inch by inch.",
        success_text="Clink! The {goal} leapt to the magnet, and down it came through the leaves.",
        qa_text="used the magnet whosejigger to pull the metal object down",
        tags={"magnet", "shed"},
    ),
    "hook_whosejigger": Tool(
        id="hook_whosejigger",
        label="hook whosejigger",
        phrase="the hook whosejigger with the curling end",
        capabilities={"hook"},
        sense=3,
        use_sound="Skritch-skritch!",
        reach_text="{helper} pointed the hook while {leader} stretched the pole toward the prize with careful hands.",
        success_text="Snag! The hook caught just right, and the {goal} slid free.",
        qa_text="used the hook whosejigger to catch and pull the object free",
        tags={"hook", "shed"},
    ),
    "net_whosejigger": Tool(
        id="net_whosejigger",
        label="net whosejigger",
        phrase="the net whosejigger with a round green ring",
        capabilities={"scoop"},
        sense=3,
        use_sound="Fwip-fwip!",
        reach_text="{leader} lowered the net gently while {helper} watched the drift and whispered when to move left or right.",
        success_text="Plop! The {goal} settled into the net instead of slipping away.",
        qa_text="used the net whosejigger to scoop the object safely",
        tags={"net", "shed"},
    ),
    "claw_whosejigger": Tool(
        id="claw_whosejigger",
        label="claw whosejigger",
        phrase="the claw whosejigger with two rubber fingers",
        capabilities={"pinch"},
        sense=2,
        use_sound="Clack-clack!",
        reach_text="{leader} squeezed the handle while {helper} called out tiny directions from below.",
        success_text="Clack! The claw pinched the {goal} gently and lifted it free.",
        qa_text="used the claw whosejigger to pinch and lift the object free",
        tags={"shed"},
    ),
    "flimsy_stick": Tool(
        id="flimsy_stick",
        label="flimsy stick",
        phrase="a little flimsy stick",
        capabilities={"poke"},
        sense=1,
        use_sound="Tap-tap.",
        reach_text="{leader} poked toward the prize.",
        success_text="Nothing useful happened.",
        qa_text="tried a flimsy stick",
        tags=set(),
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Ava", "Nora", "Zoe", "Lucy", "Tessa", "Maya"]
BOY_NAMES = ["Tao", "Ben", "Leo", "Finn", "Owen", "Sam", "Eli", "Noah"]
TRAITS = ["brave", "careful", "eager", "curious", "steady"]


@dataclass
class StoryParams:
    place: str
    mission: str
    tool: str
    leader_name: str
    leader_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="garden",
        mission="arch_key",
        tool="magnet_whosejigger",
        leader_name="Mira",
        leader_gender="girl",
        helper_name="Tao",
        helper_gender="boy",
        parent="grandfather",
        trait="brave",
    ),
    StoryParams(
        place="garden",
        mission="brook_map",
        tool="net_whosejigger",
        leader_name="Leo",
        leader_gender="boy",
        helper_name="Ava",
        helper_gender="girl",
        parent="grandmother",
        trait="curious",
    ),
    StoryParams(
        place="orchard",
        mission="bramble_flag",
        tool="hook_whosejigger",
        leader_name="Nora",
        leader_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        parent="father",
        trait="careful",
    ),
    StoryParams(
        place="orchard",
        mission="arch_key",
        tool="hook_whosejigger",
        leader_name="Eli",
        leader_gender="boy",
        helper_name="Maya",
        helper_gender="girl",
        parent="grandfather",
        trait="steady",
    ),
]


def generation_prompts(world: World) -> list[str]:
    mission = world.facts["mission"]
    leader = world.facts["leader"]
    helper = world.facts["helper"]
    tool = world.facts["tool_cfg"]
    place = world.facts["place"]
    return [
        'Write a short adventure story for a 3-to-5-year-old that includes the words "whosejigger", "grown", and "slender", and uses sound effects.',
        f"Tell an adventure where {leader.label} and {helper.label} explore {place.label}, spot {mission.goal_phrase}, and avoid a risky slender shortcut by choosing a sensible whosejigger.",
        f"Write a child-facing story with sounds, a tricky reach, and a happy ending where a {tool.label} solves the problem more safely than climbing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    place = world.facts["place"]
    mission = world.facts["mission"]
    tool = world.facts["tool_cfg"]
    leader = world.facts["leader"]
    helper = world.facts["helper"]
    parent = world.facts["parent"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {leader.label} and {helper.label}, two children on an adventure in {place.label}. They also remember a helpful grown-up, {parent.label_word}, who keeps tools in the shed."
        ),
        (
            f"What problem did the children find?",
            f"They found {mission.goal_phrase} {mission.place_spot}. That mattered because {mission.hook_line.lower()}"
        ),
        (
            f"Why was the slender shortcut a bad idea?",
            f"{leader.label} first thought about using {mission.slender_thing}, but it could wobble and make the reach unsafe. {helper.label} warned about the risk before anyone fell."
        ),
        (
            f"How did they rescue the {mission.goal_label}?",
            f"They used the {tool.label} instead of trusting the slender shortcut. {tool.qa_text.capitalize()}, which let them solve the problem carefully."
        ),
        (
            "How did the story end?",
            f"It ended with the lost thing safe again and the adventure still going. The place felt friendlier at the end because the children had been brave and careful together."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["mission"].tags) | set(world.facts["tool_cfg"].tags) | set(world.facts["place"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.label:
            bits.append(f"label={ent.label!r}")
        if ent.phrase:
            bits.append(f"phrase={ent.phrase!r}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible(Tool) :- tool(Tool), sense(Tool, S), sense_min(M), S >= M.
works(M, T)    :- mission(M), tool(T), needs(M, Need), can(T, Need).
valid(M, T)    :- sensible(T), works(M, T).

outcome(success) :- chosen_mission(M), chosen_tool(T), valid(M, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        for need in sorted(mission.needs):
            lines.append(asp.fact("needs", mid, need))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, tool.sense))
        for cap in sorted(tool.capabilities):
            lines.append(asp.fact("can", tid, cap))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_mission", params.mission),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    mission = MISSIONS[params.mission]
    tool = TOOLS[params.tool]
    return "success" if tool.sense >= SENSE_MIN and tool_works(mission, tool) else "invalid"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child adventure with a risky slender shortcut and the right whosejigger."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible mission/tool set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mission and args.tool:
        mission = MISSIONS[args.mission]
        tool = TOOLS[args.tool]
        if not (tool.sense >= SENSE_MIN and tool_works(mission, tool)):
            raise StoryError(explain_rejection(mission, tool))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        mission = MISSIONS[args.mission] if args.mission else next(iter(MISSIONS.values()))
        raise StoryError(explain_rejection(mission, TOOLS[args.tool]))

    combos = [
        combo for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.tool is None or combo[1] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid mission/tool combination matches the given options.)")

    mission_id, tool_id = rng.choice(sorted(combos))
    place_id = args.place or rng.choice(sorted(PLACES))
    leader_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if leader_gender == "girl" else "girl"
    leader_name = _pick_name(rng, leader_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=leader_name)
    parent = args.parent or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        mission=mission_id,
        tool=tool_id,
        leader_name=leader_name,
        leader_gender=leader_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    mission = MISSIONS[params.mission]
    tool = TOOLS[params.tool]
    if tool.sense < SENSE_MIN or not tool_works(mission, tool):
        raise StoryError(explain_rejection(mission, tool))

    world = tell(
        place=PLACES[params.place],
        mission=mission,
        tool=tool,
        leader_name=params.leader_name,
        leader_type=params.leader_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_gender,
        parent_type=params.parent,
        trait=params.trait,
    )

    leader = world.get("leader")
    helper = world.get("helper")
    world_story = world.render().replace("leader", leader.label).replace("helper", helper.label)
    world_story = world_story.replace("parent", world.facts["parent"].label_word)

    # Restore names in the final prose where entity ids were used internally.
    for src, dst in [("leader", leader.label), ("helper", helper.label), ("parent", world.facts["parent"].label_word)]:
        world_story = world_story.replace(f"{src}.", f"{dst}.")
    world_story = (
        world_story.replace("leader", leader.label)
        .replace("helper", helper.label)
        .replace("the grown-up", world.facts["parent"].label_word)
    )

    return StorySample(
        params=params,
        story=world_story,
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
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=False, qa=False)
        finally:
            sys.stdout = old_stdout
        if not sample.story.strip():
            raise StoryError("(Smoke test generated empty story.)")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, tool) combos:\n")
        for mission_id, tool_id in combos:
            print(f"  {mission_id:12} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for params in CURATED:
            sample = generate(params)
            samples.append(sample)
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
            header = f"### {p.leader_name} & {p.helper_name}: {p.mission} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
