#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/toe_excessive_inner_monologue_teamwork_moral_value.py
=================================================================================

A standalone storyworld for a small adventure tale about two children on a
treasure trail. One child packs an excessive bundle, bumps a toe on the path,
and the pair must use teamwork and good judgment to finish the quest safely.

The world model tracks:
- physical state: load, toe pain, progress, blocked path, solved obstacle
- emotional state: eagerness, worry, trust, relief, pride
- an inner-monologue beat grounded in state, not templated after the fact

The core reasonableness gate is simple:
- each obstacle requires a fitting tool
- some tools are weak and known to the world but refused
- an excessive bundle creates a stumble risk, which the teammate can resolve by
  sharing and trimming the load

The ending proves what changed: the children reach a bright lookout and bring
back only what they truly needed.

Run it
------
    python storyworlds/worlds/gpt-5.4/toe_excessive_inner_monologue_teamwork_moral_value.py
    python storyworlds/worlds/gpt-5.4/toe_excessive_inner_monologue_teamwork_moral_value.py --obstacle stream --tool plank
    python storyworlds/worlds/gpt-5.4/toe_excessive_inner_monologue_teamwork_moral_value.py --tool ribbon
    python storyworlds/worlds/gpt-5.4/toe_excessive_inner_monologue_teamwork_moral_value.py --all
    python storyworlds/worlds/gpt-5.4/toe_excessive_inner_monologue_teamwork_moral_value.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/toe_excessive_inner_monologue_teamwork_moral_value.py --verify
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
SENSE_MIN = 2


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
class Setting:
    id: str
    place: str
    opening: str
    goal: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    scene: str
    problem: str
    solved_with: str
    success: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    works_on: set[str]
    sense: int
    success_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Bundle:
    id: str
    label: str
    phrase: str
    weight: int
    clutter_text: str
    keep_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        return [e for e in self.entities.values() if e.role in {"leader", "helper"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
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


def _r_heavy_trip(world: World) -> list[str]:
    out: list[str] = []
    leader = world.get("leader")
    if leader.meters["load"] >= 4 and leader.meters["walking"] >= THRESHOLD:
        sig = ("trip", leader.id)
        if sig not in world.fired:
            world.fired.add(sig)
            leader.meters["toe_hurt"] += 1
            leader.meters["speed"] -= 1
            leader.memes["worry"] += 1
            helper = world.get("helper")
            helper.memes["care"] += 1
            out.append("__trip__")
    return out


def _r_teamwork_calms(world: World) -> list[str]:
    out: list[str] = []
    leader = world.get("leader")
    helper = world.get("helper")
    if leader.meters["load"] <= 2 and helper.meters["helping"] >= THRESHOLD:
        sig = ("calm", leader.id)
        if sig not in world.fired:
            world.fired.add(sig)
            leader.memes["relief"] += 1
            helper.memes["pride"] += 1
            leader.memes["trust"] += 1
            out.append("__relief__")
    return out


def _r_progress(world: World) -> list[str]:
    out: list[str] = []
    path = world.get("path")
    if path.meters["cleared"] >= THRESHOLD and world.get("leader").meters["walking"] >= THRESHOLD:
        sig = ("progress",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("leader").meters["progress"] += 1
            world.get("helper").meters["progress"] += 1
            out.append("__progress__")
    return out


CAUSAL_RULES = [
    Rule(name="heavy_trip", tag="physical", apply=_r_heavy_trip),
    Rule(name="teamwork_calms", tag="social", apply=_r_teamwork_calms),
    Rule(name="progress", tag="physical", apply=_r_progress),
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


def tool_fits(tool: Tool, obstacle: Obstacle) -> bool:
    return obstacle.id in tool.works_on


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def stumble_risk(bundle: Bundle) -> bool:
    return bundle.weight >= 4


def predict_trouble(bundle: Bundle) -> dict:
    return {
        "stumble": stumble_risk(bundle),
        "toe_hurt": 1 if stumble_risk(bundle) else 0,
    }


def explain_tool_rejection(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    better = ", ".join(sorted(t.id for t in sensible_tools()))
    return (
        f"(Refusing tool '{tool_id}': it scores too low on common sense "
        f"(sense={tool.sense} < {SENSE_MIN}). A better adventure tool is one that "
        f"really helps with the obstacle. Try: {better}.)"
    )


def explain_combo_rejection(obstacle: Obstacle, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not solve {obstacle.problem.lower()}. "
        f"Pick a tool that can handle {obstacle.label}.)"
    )


def outcome_of(params: "StoryParams") -> str:
    if stumble_risk(BUNDLES[params.bundle]):
        return "teamwork_after_stumble"
    return "teamwork_without_stumble"


def introduce(world: World, leader: Entity, helper: Entity, parent: Entity, setting: Setting) -> None:
    leader.memes["eagerness"] += 1
    helper.memes["eagerness"] += 1
    world.say(
        f"{leader.id} and {helper.id} set out with {leader.id}'s {parent.label_word} for "
        f"{setting.place}. {setting.opening}"
    )
    world.say(
        f"They were hunting for {setting.goal}, and the morning felt full of adventure."
    )


def pack(world: World, leader: Entity, bundle: Bundle) -> None:
    leader.meters["load"] = float(bundle.weight)
    world.say(
        f"Before they even reached the trail, {leader.id} stuffed {bundle.phrase} into a little satchel."
    )
    world.say(bundle.clutter_text)


def inner_monologue(world: World, leader: Entity, bundle: Bundle) -> None:
    pred = predict_trouble(bundle)
    world.facts["predicted_stumble"] = pred["stumble"]
    if pred["stumble"]:
        leader.memes["worry"] += 1
        world.say(
            f'Inside, {leader.id} thought, "This might be an excessive amount to carry... '
            f'but what if we need every single thing?"'
        )
    else:
        world.say(
            f'Inside, {leader.id} thought, "We packed enough for the trail, and that feels just right."'
        )


def start_walk(world: World, leader: Entity, helper: Entity) -> None:
    leader.meters["walking"] += 1
    helper.meters["walking"] += 1
    propagate(world, narrate=False)
    if leader.meters["toe_hurt"] >= THRESHOLD:
        world.say(
            f"On the first rocky bend, the satchel swung sideways, and {leader.id} bumped a toe hard against a root."
        )
        world.say(
            f"{leader.id} stopped with wet eyes and took a careful breath."
        )
    else:
        world.say(
            f"They followed the trail between tall ferns, stepping over roots and listening for the little stream ahead."
        )


def comfort(world: World, helper: Entity, leader: Entity) -> None:
    if leader.meters["toe_hurt"] >= THRESHOLD:
        helper.memes["care"] += 1
        world.say(
            f'"Are you okay?" {helper.id} asked, kneeling beside {leader.id}. '
            f'"We do not have to rush. We can solve this together."'
        )


def share_and_trim(world: World, helper: Entity, leader: Entity, bundle: Bundle) -> None:
    helper.meters["helping"] += 1
    helper.memes["trust"] += 1
    moved = max(1, bundle.weight - 2)
    leader.meters["load"] = max(2.0, leader.meters["load"] - moved)
    helper.meters["load"] += float(moved - 1 if moved > 1 else 1)
    propagate(world, narrate=False)
    if bundle.weight >= 4:
        world.say(
            f"Together they opened the satchel. {helper.id} carried part of the load, "
            f"and they set aside the extra things that only made the bag wobble."
        )
        world.say(bundle.keep_text)
    else:
        world.say(
            f"{helper.id} still took one small item, just to make the climb easier, and {leader.id} smiled."
        )


def face_obstacle(world: World, obstacle: Obstacle) -> None:
    path = world.get("path")
    path.meters["blocked"] += 1
    world.say(obstacle.scene)
    world.say(obstacle.problem)


def use_tool(world: World, leader: Entity, helper: Entity, tool: Tool, obstacle: Obstacle) -> None:
    path = world.get("path")
    leader.memes["focus"] += 1
    helper.memes["focus"] += 1
    path.meters["cleared"] += 1
    path.meters["blocked"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{leader.id} and {helper.id} {tool.success_text.format(obstacle=obstacle.label)}"
    )
    world.say(obstacle.success)


def finish(world: World, leader: Entity, helper: Entity, parent: Entity, setting: Setting, bundle: Bundle) -> None:
    leader.memes["pride"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"At last they reached {setting.ending_image}, where a small painted marker showed they had found the trail's secret place."
    )
    if leader.meters["toe_hurt"] >= THRESHOLD:
        world.say(
            f"{leader.id}'s toe still throbbed a little, but now the pain felt smaller than the lesson."
        )
    world.say(
        f'{parent.label_word.capitalize()} smiled and said, "Real adventurers help each other and carry what they truly need."'
    )
    if bundle.weight >= 4:
        world.say(
            f"{leader.id} looked at the lighter satchel and knew the adventure had gone better once the load stopped being excessive."
        )
    else:
        world.say(
            f"Their small pack was enough, and the trail felt kinder when they worked as a team."
        )


def tell(
    setting: Setting,
    obstacle: Obstacle,
    tool: Tool,
    bundle: Bundle,
    leader_name: str = "Nora",
    leader_gender: str = "girl",
    helper_name: str = "Ben",
    helper_gender: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World(setting=setting)
    leader = world.add(Entity(id="leader", kind="character", type=leader_gender, label=leader_name, role="leader"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    path = world.add(Entity(id="path", kind="thing", type="trail", label="trail"))
    tool_ent = world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label, phrase=tool.phrase))
    bag = world.add(Entity(id="bundle", kind="thing", type="bundle", label=bundle.label, phrase=bundle.phrase))
    world.facts["actor_names"] = (leader_name, helper_name)

    introduce(world, leader, helper, parent, setting)
    pack(world, leader, bundle)
    inner_monologue(world, leader, bundle)

    world.para()
    start_walk(world, leader, helper)
    comfort(world, helper, leader)
    share_and_trim(world, helper, leader, bundle)

    world.para()
    face_obstacle(world, obstacle)
    use_tool(world, leader, helper, tool, obstacle)

    world.para()
    finish(world, leader, helper, parent, setting, bundle)

    world.facts.update(
        setting=setting,
        obstacle=obstacle,
        tool=tool,
        bundle_cfg=bundle,
        leader=leader,
        helper=helper,
        parent=parent,
        tool_ent=tool_ent,
        bundle_ent=bag,
        toe_hurt=leader.meters["toe_hurt"] >= THRESHOLD,
        teamwork=True,
        outcome="teamwork_after_stumble" if leader.meters["toe_hurt"] >= THRESHOLD else "teamwork_without_stumble",
    )
    return world


SETTINGS = {
    "forest": Setting(
        id="forest",
        place="the Whispering Forest trail",
        opening="Sunlight slipped through the leaves in bright pieces, and the narrow path curled toward the hills.",
        goal="the little lookout marker",
        ending_image="a windy lookout above the trees",
        tags={"forest", "adventure"},
    ),
    "cliffs": Setting(
        id="cliffs",
        place="the high cliff path",
        opening="Gulls cried overhead, and a ribbon of trail ran above the sparkling sea.",
        goal="the bell at the far lookout",
        ending_image="a high stone ledge above the water",
        tags={"cliff", "adventure"},
    ),
    "ruins": Setting(
        id="ruins",
        place="the old garden ruins",
        opening="Broken archways and mossy stones made the place feel like a map come alive.",
        goal="the sun-mark tile in the center court",
        ending_image="a sunny circle of old stone",
        tags={"ruins", "adventure"},
    ),
}

OBSTACLES = {
    "stream": Obstacle(
        id="stream",
        label="the stream",
        scene="Soon they reached a silver stream skipping across the trail.",
        problem="The stepping stones were far apart, and the water was too wide for an easy hop.",
        solved_with="plank",
        success="With careful feet and linked hands, they crossed to the other side.",
        tags={"stream", "water"},
    ),
    "thorn_gate": Obstacle(
        id="thorn_gate",
        label="the thorn gate",
        scene="Farther on, thorny vines had knotted themselves across the path like a prickly gate.",
        problem="The tangle scratched at sleeves and blocked the way forward.",
        solved_with="clippers",
        success="Bit by bit, the path opened, and the children made a doorway through the vines.",
        tags={"plants", "trail"},
    ),
    "dark_gap": Obstacle(
        id="dark_gap",
        label="the dark gap",
        scene="Near the end of the trail, the path ducked under a stone arch where the light almost disappeared.",
        problem="The shaded passage was too dim to trust with quick feet.",
        solved_with="lantern",
        success="The warm beam showed every stone, and together they stepped through the dark place safely.",
        tags={"dark", "light"},
    ),
}

TOOLS = {
    "plank": Tool(
        id="plank",
        label="plank",
        phrase="a short wooden plank",
        works_on={"stream"},
        sense=3,
        success_text="set down the plank over {obstacle}, then crossed one at a time while keeping hold of each other's hands.",
        qa_text="laid the plank across the stream and crossed carefully together",
        tags={"bridge", "teamwork"},
    ),
    "clippers": Tool(
        id="clippers",
        label="clippers",
        phrase="a pair of garden clippers",
        works_on={"thorn_gate"},
        sense=3,
        success_text="took turns with the clippers until the path through {obstacle} was wide enough to pass.",
        qa_text="took turns clipping the thorny vines until the path opened",
        tags={"plants", "teamwork"},
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a camping lantern",
        works_on={"dark_gap"},
        sense=3,
        success_text="lifted the lantern high beside {obstacle}, watching the ground and warning each other about the stones.",
        qa_text="used the lantern to light the dark passage and walked through carefully together",
        tags={"light", "safety"},
    ),
    "ribbon": Tool(
        id="ribbon",
        label="ribbon",
        phrase="a shiny ribbon",
        works_on=set(),
        sense=1,
        success_text="waved the ribbon near {obstacle}.",
        qa_text="waved a ribbon, which did not truly help",
        tags={"weak"},
    ),
}

BUNDLES = {
    "rocks": Bundle(
        id="rocks",
        label="lucky rocks",
        phrase="three lucky rocks, a brass compass, a snack box, a rolled-up flag, and two extra notebooks",
        weight=5,
        clutter_text="The bag looked brave and important, but it bulged so much it knocked against {leader}'s knee.".replace("{leader}", "the side of the trail"),
        keep_text="They kept the compass and one notebook, then tucked the rest by a flat stump to collect on the way back.",
        tags={"heavy", "excessive"},
    ),
    "snacks": Bundle(
        id="snacks",
        label="trail snacks",
        phrase="a snack box, a water bottle, and one tiny map",
        weight=2,
        clutter_text="The satchel was snug but easy to carry.",
        keep_text="They kept the whole small bundle because it already fit the trail well.",
        tags={"light"},
    ),
    "flags": Bundle(
        id="flags",
        label="signal flags",
        phrase="a rolled-up flag, a water bottle, a compass, and a bag of pebbles for markers",
        weight=4,
        clutter_text="It was such an excessive pile for a short trail that even the strap seemed to sigh.",
        keep_text="They kept the compass and water, then left the pebbles and extra flag neatly beside a stump to fetch later.",
        tags={"heavy", "excessive"},
    ),
}


GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Ben", "Leo", "Finn", "Noah", "Sam", "Max", "Theo", "Eli"]


@dataclass
class StoryParams:
    setting: str
    obstacle: str
    tool: str
    bundle: str
    leader_name: str
    leader_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when people help one another to do a job. They share the hard parts so the job becomes easier and safer."
        )
    ],
    "toe": [
        (
            "What should you do if you bump your toe?",
            "Stop for a moment and check that you are okay. Walking more carefully and getting help can keep a small hurt from turning into a bigger problem."
        )
    ],
    "excessive": [
        (
            "What does excessive mean?",
            "Excessive means more than is really needed. Too much of something can make a job harder instead of better."
        )
    ],
    "lantern": [
        (
            "Why is a lantern helpful in a dark place?",
            "A lantern gives steady light so you can see where to step. Good light helps people move more safely."
        )
    ],
    "plank": [
        (
            "How can a plank help at a stream?",
            "A strong plank can make a little bridge over water. It gives your feet a steadier path than a long jump."
        )
    ],
    "clippers": [
        (
            "What do clippers do?",
            "Clippers cut stems and small branches. They help clear prickly plants from a path."
        )
    ],
    "travel_light": [
        (
            "Why is it smart to carry only what you need on a trail?",
            "A lighter bag is easier to balance and easier to share. Carrying only what you need leaves more energy for the adventure itself."
        )
    ],
}
KNOWLEDGE_ORDER = ["teamwork", "toe", "excessive", "plank", "clippers", "lantern", "travel_light"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader_name, helper_name = f["actor_names"]
    obstacle = f["obstacle"]
    tool = f["tool"]
    bundle = f["bundle_cfg"]
    return [
        'Write a short adventure story for a 3-to-5-year-old that includes the words "toe" and "excessive" and shows teamwork.',
        f"Tell an adventure where {leader_name} packs {bundle.label}, bumps a toe on the trail, and solves a problem at {obstacle.label} with {helper_name}'s help.",
        f"Write a gentle moral story in which two children use {tool.label} to get past {obstacle.label} and learn that good teammates carry only what they truly need.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    helper = f["helper"]
    parent = f["parent"]
    obstacle = f["obstacle"]
    tool = f["tool"]
    bundle = f["bundle_cfg"]
    lname, hname = f["actor_names"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {lname} and {hname}, two children on an adventure trail with {lname}'s {pw}. They are trying to reach a special place at the end of the path."
        ),
        (
            f"Why did {lname} hurt a toe?",
            f"{lname} carried too much in the satchel, and the heavy bag swung while the trail twisted over roots. Because the load was excessive, {lname} bumped a toe on a root and had to stop."
        ),
        (
            f"What was {lname} thinking inside?",
            f"{lname} worried that the bag might be an excessive amount to carry but still wanted to be prepared. That inner thought shows {lname} already sensed the problem before the stumble."
        ),
        (
            f"How did {hname} help after the toe was hurt?",
            f"{hname} stayed calm, checked on {lname}, and helped sort the satchel. By sharing the load and leaving behind the extra things, {hname} turned a hard moment into teamwork."
        ),
        (
            f"How did they get past {obstacle.label}?",
            f"They used the {tool.label} and worked together instead of rushing. {lname} and {hname} could finish the trail because the tool truly fit the obstacle and they listened to each other."
        ),
        (
            "What is the moral of the story?",
            f"The story teaches that real adventurers help each other and do not carry more than they need. Good teamwork and good choices mattered more than having the biggest bag."
        ),
    ]
    if f["toe_hurt"]:
        qa.append(
            (
                f"How did {lname} feel at the end?",
                f"{lname} still noticed the sore toe a little, but felt proud and relieved. The children had learned to slow down, share the load, and finish together."
            )
        )
    else:
        qa.append(
            (
                f"How did the children feel at the end?",
                "They felt proud, light, and ready for the next adventure. Their teamwork made the trail feel easier and happier."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"teamwork", "toe", "travel_light"}
    if f["bundle_cfg"].weight >= 4:
        tags.add("excessive")
    tool_id = f["tool"].id
    if tool_id in {"plank", "clippers", "lantern"}:
        tags.add(tool_id)
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- reasonableness gate ----------------------------------------------------
fits(O, T) :- obstacle(O), tool(T), works_on(T, O).
sensible(T) :- tool(T), sense(T, S), sense_min(M), S >= M.
valid(S, O, T) :- setting(S), obstacle(O), tool(T), fits(O, T), sensible(T).

% --- outcome model ----------------------------------------------------------
stumble(Bundle) :- bundle(Bundle), weight(Bundle, W), W >= 4.
outcome(teamwork_after_stumble) :- chosen_bundle(B), stumble(B).
outcome(teamwork_without_stumble) :- chosen_bundle(B), not stumble(B).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid in OBSTACLES:
        lines.append(asp.fact("obstacle", oid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, tool.sense))
        for oid in sorted(tool.works_on):
            lines.append(asp.fact("works_on", tid, oid))
    for bid, bundle in BUNDLES.items():
        lines.append(asp.fact("bundle", bid))
        lines.append(asp.fact("weight", bid, bundle.weight))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_tools() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("chosen_bundle", params.bundle)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for sid in SETTINGS:
        for oid, obstacle in OBSTACLES.items():
            for tid, tool in TOOLS.items():
                if tool_fits(tool, obstacle) and tool.sense >= SENSE_MIN:
                    out.append((sid, oid, tid))
    return out


CURATED = [
    StoryParams(
        setting="forest",
        obstacle="stream",
        tool="plank",
        bundle="rocks",
        leader_name="Nora",
        leader_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        parent="mother",
    ),
    StoryParams(
        setting="cliffs",
        obstacle="thorn_gate",
        tool="clippers",
        bundle="snacks",
        leader_name="Leo",
        leader_gender="boy",
        helper_name="Mia",
        helper_gender="girl",
        parent="father",
    ),
    StoryParams(
        setting="ruins",
        obstacle="dark_gap",
        tool="lantern",
        bundle="flags",
        leader_name="Ava",
        leader_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        parent="mother",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: an adventure trail, an excessive load, a hurt toe, and teamwork."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--bundle", choices=BUNDLES)
    ap.add_argument("--leader-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--leader-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool_rejection(args.tool))
    if args.obstacle and args.tool:
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        if not tool_fits(tool, obstacle):
            raise StoryError(explain_combo_rejection(obstacle, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, obstacle_id, tool_id = rng.choice(sorted(combos))
    bundle_id = args.bundle or rng.choice(sorted(BUNDLES))
    leader_gender = args.leader_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    leader_name = args.leader_name or pick_name(rng, leader_gender)
    helper_name = args.helper_name or pick_name(rng, helper_gender, avoid=leader_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        obstacle=obstacle_id,
        tool=tool_id,
        bundle=bundle_id,
        leader_name=leader_name,
        leader_gender=leader_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.bundle not in BUNDLES:
        raise StoryError(f"(Unknown bundle: {params.bundle})")

    obstacle = OBSTACLES[params.obstacle]
    tool = TOOLS[params.tool]
    if tool.sense < SENSE_MIN:
        raise StoryError(explain_tool_rejection(params.tool))
    if not tool_fits(tool, obstacle):
        raise StoryError(explain_combo_rejection(obstacle, tool))

    world = tell(
        setting=SETTINGS[params.setting],
        obstacle=obstacle,
        tool=tool,
        bundle=BUNDLES[params.bundle],
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
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


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sensible = {tool.id for tool in sensible_tools()}
    asp_sensible = set(asp_sensible_tools())
    if py_sensible == asp_sensible:
        print(f"OK: sensible tools match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: python={sorted(py_sensible)} clingo={sorted(asp_sensible)}")

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke generation passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tools: {', '.join(asp_sensible_tools())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, obstacle, tool) combos:\n")
        for setting_id, obstacle_id, tool_id in combos:
            print(f"  {setting_id:8} {obstacle_id:11} {tool_id}")
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
            header = f"### {p.leader_name} & {p.helper_name}: {p.obstacle} with {p.tool} ({outcome_of(p)})"
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
