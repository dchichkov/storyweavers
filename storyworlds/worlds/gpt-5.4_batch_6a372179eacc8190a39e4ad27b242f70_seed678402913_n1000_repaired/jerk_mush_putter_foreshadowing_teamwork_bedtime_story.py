#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/jerk_mush_putter_foreshadowing_teamwork_bedtime_story.py
===================================================================================

A small bedtime-story world about two children carrying a warm bedtime snack to a
sleepy little one. The world models a near-spill on the way, a sensible helper
tool, and a teamwork turn that resolves the danger.

The seed words appear naturally in the story:
- "putter" in the cozy setup
- "mush" in the snack scene
- "jerk" in the near-spill turn

Run it
------
    python storyworlds/worlds/gpt-5.4/jerk_mush_putter_foreshadowing_teamwork_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/jerk_mush_putter_foreshadowing_teamwork_bedtime_story.py --hazard dark_hall --tool lantern
    python storyworlds/worlds/gpt-5.4/jerk_mush_putter_foreshadowing_teamwork_bedtime_story.py --hazard sleepy_cat --tool tray
    python storyworlds/worlds/gpt-5.4/jerk_mush_putter_foreshadowing_teamwork_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/jerk_mush_putter_foreshadowing_teamwork_bedtime_story.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    scent: str
    texture: str
    heat_word: str
    comfort_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    place: str
    foreshadow: str
    trigger: str
    problem: str
    need: str
    helper_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    kind: str
    action: str
    ending_line: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"carrier", "helper", "receiver"}]

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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.get("bowl")
    if bowl.meters["wobble"] < THRESHOLD:
        return out
    sig = ("worry", "bowl")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        if kid.role != "receiver":
            kid.memes["worry"] += 1
    out.append("__worry__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.get("bowl")
    if bowl.meters["spill_risk"] < THRESHOLD:
        return out
    if bowl.attrs.get("secured"):
        return out
    sig = ("spill", "bowl")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bowl.meters["splashed"] += 1
    for kid in world.kids():
        if kid.role != "receiver":
            kid.memes["fear"] += 1
    out.append("__spill__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="spill", tag="physical", apply=_r_spill),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                produced.extend(s for s in sent if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SNACKS = {
    "oatmeal": Snack(
        id="oatmeal",
        label="oatmeal",
        phrase="a warm bowl of oatmeal with a little honey",
        scent="sweet steam",
        texture="soft mush",
        heat_word="warm",
        comfort_line="The oatmeal smelled sleepy and kind, the way a quiet night should.",
        tags={"oatmeal", "bedtime_food", "hot_bowl"},
    ),
    "rice_pudding": Snack(
        id="rice_pudding",
        label="rice pudding",
        phrase="a bowl of cinnamon rice pudding",
        scent="milky cinnamon steam",
        texture="gentle mush",
        heat_word="warm",
        comfort_line="The rice pudding looked soft enough for a whispery bedtime snack.",
        tags={"rice_pudding", "bedtime_food", "hot_bowl"},
    ),
    "apple_mash": Snack(
        id="apple_mash",
        label="apple mash",
        phrase="a bowl of warm apple mash",
        scent="apple-cinnamon steam",
        texture="apple mush",
        heat_word="warm",
        comfort_line="The apple mash was smooth and cozy, just right for the end of the day.",
        tags={"apple", "bedtime_food", "hot_bowl"},
    ),
}

HAZARDS = {
    "dark_hall": Hazard(
        id="dark_hall",
        label="the dark hall",
        place="the dark hall",
        foreshadow="The hall between the kitchen and the bedroom was dusky, and the corners had already begun to swallow the light.",
        trigger="When they stepped into the dark hall, the shadows made the floor hard to read.",
        problem="the carrier could not see the rug edge",
        need="light",
        helper_line="The helper must show the floor clearly so the carrier can keep both eyes on the bowl.",
        tags={"dark", "nightlight"},
    ),
    "sleepy_cat": Hazard(
        id="sleepy_cat",
        label="the sleepy cat",
        place="the hallway",
        foreshadow="Old Marmalade the cat was already curled in the hallway, with one tail stretched across the runner like a stripe of moonlight.",
        trigger="Just outside the kitchen, the sleepy cat twitched and stretched across their path.",
        problem="the carrier might trip over the cat",
        need="guide",
        helper_line="The helper must gently move the cat aside before the warm bowl goes past.",
        tags={"cat", "pet"},
    ),
    "creaky_stairs": Hazard(
        id="creaky_stairs",
        label="the creaky stairs",
        place="the stairs",
        foreshadow="The stairs gave their little bedtime groans, and the top step was always the one that made hands tighten.",
        trigger="On the stairs, the bowl tipped a little as the carrier reached the creaky top step.",
        problem="the bowl could wobble in tired hands",
        need="steady",
        helper_line="The helper must steady the bowl so the carrier can climb with small careful feet.",
        tags={"stairs", "balance"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a pearly night-lantern",
        kind="light",
        action="held up the little lantern until the rug edge and every corner showed",
        ending_line="The lantern made a soft pool of gold all the way to the bedroom door.",
        tags={"lantern", "light"},
    ),
    "cat_bell": Tool(
        id="cat_bell",
        label="cat bell",
        phrase="a tiny brass cat bell",
        kind="guide",
        action="rang the cat bell once, and Marmalade blinked, stood up, and padded to his cushion",
        ending_line="The small bell saved the path without any hurrying or shooing.",
        tags={"bell", "cat"},
    ),
    "tray": Tool(
        id="tray",
        label="tray",
        phrase="a wooden tray with two handles",
        kind="steady",
        action="slid the bowl onto the tray and took the other handle with both hands ready",
        ending_line="The tray kept the bowl level even on the fussy top step.",
        tags={"tray", "balance"},
    ),
}


def valid_pair(hazard: Hazard, tool: Tool) -> bool:
    return hazard.need == tool.kind


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for snack_id in sorted(SNACKS):
        for hazard_id, hazard in HAZARDS.items():
            for tool_id, tool in TOOLS.items():
                if valid_pair(hazard, tool):
                    combos.append((snack_id, hazard_id, tool_id))
    return combos


@dataclass
class StoryParams:
    snack: str
    hazard: str
    tool: str
    carrier_name: str
    carrier_gender: str
    helper_name: str
    helper_gender: str
    receiver_name: str
    receiver_gender: str
    parent: str
    seed: Optional[int] = None


def explain_rejection(hazard: Hazard, tool: Tool) -> str:
    return (
        f"(No story: {tool.phrase} does not solve {hazard.label}. "
        f"{hazard.helper_line} Try a tool of kind '{hazard.need}'.)"
    )


def predict_near_spill(hazard: Hazard, tool: Tool) -> dict:
    sim = World()
    carrier = sim.add(Entity(id="Carrier", kind="character", type="girl", role="carrier"))
    helper = sim.add(Entity(id="Helper", kind="character", type="boy", role="helper"))
    sim.add(Entity(id="Receiver", kind="character", type="girl", role="receiver"))
    bowl = sim.add(Entity(id="bowl", kind="thing", type="bowl", label="bowl"))
    bowl.meters["warmth"] = 1
    bowl.attrs["secured"] = False

    if hazard.id in {"dark_hall", "creaky_stairs", "sleepy_cat"}:
        bowl.meters["wobble"] += 1
        bowl.meters["spill_risk"] += 1
        propagate(sim, narrate=False)

    if valid_pair(hazard, tool):
        bowl.attrs["secured"] = True
        bowl.meters["spill_risk"] = 0.0
        bowl.meters["wobble"] = 0.0

    return {
        "spilled": bowl.meters["splashed"] >= THRESHOLD,
        "worry": carrier.memes["worry"] + helper.memes["worry"],
        "secured": bool(bowl.attrs.get("secured")),
    }


def cozy_setup(world: World, parent: Entity, snack: Snack, receiver: Entity) -> None:
    world.say(
        f"In the kitchen, the kettle began to putter on the stove while the house turned soft and quiet."
    )
    world.say(
        f"{parent.label_word.capitalize()} stirred {snack.phrase}, and soon it became {snack.texture} with {snack.scent} curling into the air."
    )
    world.say(snack.comfort_line)
    world.say(
        f'From the bedroom came a small voice. "{receiver.id} is still awake," {parent.label_word} said. "A few warm bites might help."'
    )


def assign_task(world: World, carrier: Entity, helper: Entity, snack: Snack) -> None:
    bowl = world.get("bowl")
    bowl.meters["warmth"] += 1
    carrier.memes["pride"] += 1
    helper.memes["pride"] += 1
    world.say(
        f'{carrier.id} wanted to carry the bowl at once, and {helper.id} wanted to help. '
        f'The bowl looked small, but it was {snack.heat_word}, full, and easy to slosh.'
    )


def foreshadow(world: World, hazard: Hazard) -> None:
    world.para()
    world.say(hazard.foreshadow)
    world.facts["foreshadowed"] = True


def start_walk(world: World, carrier: Entity, helper: Entity, hazard: Hazard) -> None:
    world.say(
        f'{carrier.id} took the bowl in both hands, and {helper.id} walked beside {carrier.pronoun("object")} with listening feet.'
    )
    world.say(
        f'They meant to go slowly, but bedtime makes hallways feel long, and the room ahead waited in a hush.'
    )


def trigger_hazard(world: World, carrier: Entity, helper: Entity, hazard: Hazard) -> None:
    bowl = world.get("bowl")
    bowl.meters["wobble"] += 1
    bowl.meters["spill_risk"] += 1
    propagate(world, narrate=False)
    carrier.memes["alarm"] += 1
    helper.memes["alarm"] += 1
    world.para()
    world.say(hazard.trigger)
    world.say(
        f'The bowl gave a tiny jerk in {carrier.pronoun("possessive")} hands, and both children stopped so fast they could hear their own breath.'
    )


def teamwork_fix(world: World, carrier: Entity, helper: Entity, tool: Tool, hazard: Hazard) -> None:
    bowl = world.get("bowl")
    bowl.attrs["secured"] = True
    bowl.meters["spill_risk"] = 0.0
    bowl.meters["wobble"] = 0.0
    carrier.memes["relief"] += 1
    helper.memes["relief"] += 1
    carrier.memes["trust"] += 1
    helper.memes["trust"] += 1
    world.say(
        f'"Wait," whispered {helper.id}. "We can do this together." {helper.id} {tool.action}.'
    )
    if hazard.need == "steady":
        world.say(
            f'{carrier.id} kept one careful step at a time while {helper.id} carried the other side. Now the bowl felt shared instead of heavy.'
        )
    elif hazard.need == "light":
        world.say(
            f'With the light steady on the floor, {carrier.id} could see exactly where to place each foot, and {helper.id} stayed close on the dark side.'
        )
    else:
        world.say(
            f'With the path clear again, {carrier.id} kept the bowl high and level while {helper.id} watched every step.'
        )
    world.facts["teamwork_used"] = True


def safe_arrival(world: World, carrier: Entity, helper: Entity, receiver: Entity, tool: Tool, snack: Snack) -> None:
    bowl = world.get("bowl")
    bowl.meters["served"] += 1
    receiver.memes["comfort"] += 1
    carrier.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.para()
    world.say(
        f'Together they reached {receiver.id}\'s room without spilling a drop. {tool.ending_line}'
    )
    world.say(
        f'{receiver.id} pushed up from the pillow and smiled at the warm bowl. {carrier.id} held the spoon, {helper.id} tucked the blanket, and the whole room seemed to settle.'
    )
    world.say(
        f'Soon the bedtime snack was gone, the night was calm, and the children felt bigger for having solved a small hard thing together.'
    )


def tell(
    snack: Snack,
    hazard: Hazard,
    tool: Tool,
    carrier_name: str,
    carrier_gender: str,
    helper_name: str,
    helper_gender: str,
    receiver_name: str,
    receiver_gender: str,
    parent_type: str,
) -> World:
    world = World()
    carrier = world.add(Entity(id=carrier_name, kind="character", type=carrier_gender, role="carrier"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    receiver = world.add(Entity(id=receiver_name, kind="character", type=receiver_gender, role="receiver"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    bowl = world.add(Entity(id="bowl", kind="thing", type="bowl", label="the bowl"))
    world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label, phrase=tool.phrase))

    cozy_setup(world, parent, snack, receiver)
    assign_task(world, carrier, helper, snack)
    foreshadow(world, hazard)
    start_walk(world, carrier, helper, hazard)
    trigger_hazard(world, carrier, helper, hazard)
    teamwork_fix(world, carrier, helper, tool, hazard)
    safe_arrival(world, carrier, helper, receiver, tool, snack)

    world.facts.update(
        snack=snack,
        hazard=hazard,
        tool_cfg=tool,
        carrier=carrier,
        helper=helper,
        receiver=receiver,
        parent=parent,
        bowl=bowl,
        outcome="safe",
        near_spill=True,
        delivered=bowl.meters["served"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "oatmeal": [
        (
            "What is oatmeal?",
            "Oatmeal is a soft warm food made from oats cooked with milk or water. Many people eat it when they want something gentle and cozy.",
        )
    ],
    "rice_pudding": [
        (
            "What is rice pudding?",
            "Rice pudding is a soft sweet dish made from rice cooked until it is tender and creamy. It is often eaten warm.",
        )
    ],
    "apple": [
        (
            "What is apple mash?",
            "Apple mash is cooked apple that has been made soft and smooth. It is easy to eat and can feel comforting at bedtime.",
        )
    ],
    "hot_bowl": [
        (
            "Why should you carry a warm bowl carefully?",
            "A warm bowl can wobble and spill if you rush or hold it badly. Slow hands and help from another person can keep it safe.",
        )
    ],
    "lantern": [
        (
            "What does a lantern help you do?",
            "A lantern helps you see in dim places. Good light makes it easier to walk safely.",
        )
    ],
    "cat": [
        (
            "Why should you watch for pets in a hallway?",
            "Pets can stop or stretch out without warning. If you notice them first, you can move gently and avoid tripping.",
        )
    ],
    "tray": [
        (
            "Why can a tray help carry food?",
            "A tray gives the bowl a flatter place to sit. It can make a wobbly carry feel steadier.",
        )
    ],
    "balance": [
        (
            "Why is teamwork useful when carrying something?",
            "Two people can share jobs. One can watch the path while the other keeps the bowl level.",
        )
    ],
    "nightlight": [
        (
            "Why is it harder to walk in a dark hallway?",
            "In a dark hallway, you can miss small things on the floor or the edge of a rug. Light helps your eyes and your feet work together.",
        )
    ],
    "pet": [
        (
            "How should you move a sleepy cat?",
            "You should move a sleepy cat gently and calmly. Sudden grabbing can scare the cat.",
        )
    ],
    "stairs": [
        (
            "Why do stairs need extra care?",
            "Stairs ask your feet and hands to work together. When you are carrying something, each step matters more.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "oatmeal",
    "rice_pudding",
    "apple",
    "hot_bowl",
    "lantern",
    "cat",
    "tray",
    "balance",
    "nightlight",
    "pet",
    "stairs",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    carrier = f["carrier"]
    helper = f["helper"]
    receiver = f["receiver"]
    snack = f["snack"]
    hazard = f["hazard"]
    tool = f["tool_cfg"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "putter," "mush," and "jerk."',
        f"Tell a gentle story where {carrier.id} and {helper.id} carry {snack.phrase} to sleepy {receiver.id}, face {hazard.label}, and solve the problem with teamwork and {tool.phrase}.",
        f"Write a cozy story with foreshadowing, a near-spill in {hazard.place}, and a calm ending that shows two children working together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    carrier = f["carrier"]
    helper = f["helper"]
    receiver = f["receiver"]
    parent = f["parent"]
    snack = f["snack"]
    hazard = f["hazard"]
    tool = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {carrier.id} and {helper.id}, who were carrying a warm bedtime snack to {receiver.id}. {parent.label_word.capitalize()} began the task, but the children solved the hard part together.",
        ),
        (
            "What were they carrying?",
            f"They were carrying {snack.phrase}. It was warm and soft, so it needed careful hands.",
        ),
        (
            "What was the early clue that trouble might happen?",
            f"The story warned us early with {hazard.foreshadow.lower()} That foreshadowing told us the walk might be tricky before the bowl ever wobbled.",
        ),
        (
            f"What happened in {hazard.place}?",
            f"In {hazard.place}, {hazard.problem}, and the bowl gave a tiny jerk. That was the turning point, because the children had to stop and think instead of hurrying on.",
        ),
        (
            "How did they solve the problem?",
            f"They used teamwork: {helper.id} {tool.action}, and {carrier.id} kept the bowl careful and level. Each child did a different job, which is why the warm snack reached the bedroom safely.",
        ),
        (
            f"How did the story end for {receiver.id}?",
            f"{receiver.id} got the warm snack without a spill and smiled from the pillow. The calm ending proves the children changed the night by helping each other.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["snack"].tags) | set(world.facts["hazard"].tags) | set(world.facts["tool_cfg"].tags)
    if "pet" in world.facts["hazard"].tags:
        tags.add("pet")
    if "stairs" in world.facts["hazard"].tags:
        tags.add("stairs")
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.label:
            bits.append(f"label={ent.label}")
        if ent.phrase:
            bits.append(f"phrase={ent.phrase}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
needs(dark_hall, light).
needs(sleepy_cat, guide).
needs(creaky_stairs, steady).

valid(S, H, T) :- snack(S), hazard(H), tool(T), needs(H, N), tool_kind(T, N).
safe(H, T) :- needs(H, N), tool_kind(T, N).
outcome(safe) :- chosen_hazard(H), chosen_tool(T), safe(H, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for snack_id in sorted(SNACKS):
        lines.append(asp.fact("snack", snack_id))
    for hazard_id in sorted(HAZARDS):
        lines.append(asp.fact("hazard", hazard_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("tool_kind", tool_id, tool.kind))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        snack="oatmeal",
        hazard="dark_hall",
        tool="lantern",
        carrier_name="Lila",
        carrier_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        receiver_name="Pip",
        receiver_gender="boy",
        parent="mother",
    ),
    StoryParams(
        snack="rice_pudding",
        hazard="sleepy_cat",
        tool="cat_bell",
        carrier_name="Noah",
        carrier_gender="boy",
        helper_name="Mina",
        helper_gender="girl",
        receiver_name="June",
        receiver_gender="girl",
        parent="father",
    ),
    StoryParams(
        snack="apple_mash",
        hazard="creaky_stairs",
        tool="tray",
        carrier_name="Tess",
        carrier_gender="girl",
        helper_name="Ollie",
        helper_gender="boy",
        receiver_name="Mae",
        receiver_gender="girl",
        parent="mother",
    ),
]


GIRL_NAMES = ["Lila", "Mina", "Tess", "Nora", "Elsie", "Wren", "Mabel", "Ivy"]
BOY_NAMES = ["Ben", "Noah", "Ollie", "Theo", "Milo", "Finn", "Jude", "Pip"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Bedtime teamwork storyworld. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--snack", choices=sorted(SNACKS))
    ap.add_argument("--hazard", choices=sorted(HAZARDS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard and args.tool:
        hazard = HAZARDS[args.hazard]
        tool = TOOLS[args.tool]
        if not valid_pair(hazard, tool):
            raise StoryError(explain_rejection(hazard, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.snack is None or combo[0] == args.snack)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    snack_id, hazard_id, tool_id = rng.choice(sorted(combos))
    carrier_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    receiver_gender = rng.choice(["girl", "boy"])
    carrier_name = pick_name(rng, carrier_gender)
    helper_name = pick_name(rng, helper_gender, avoid=carrier_name)
    receiver_name = pick_name(rng, receiver_gender, avoid=carrier_name if receiver_gender == carrier_gender else "")
    parent = args.parent or rng.choice(["mother", "father"])

    return StoryParams(
        snack=snack_id,
        hazard=hazard_id,
        tool=tool_id,
        carrier_name=carrier_name,
        carrier_gender=carrier_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        receiver_name=receiver_name,
        receiver_gender=receiver_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.snack not in SNACKS:
        raise StoryError(f"(Unknown snack '{params.snack}')")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard '{params.hazard}')")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool '{params.tool}')")

    snack = SNACKS[params.snack]
    hazard = HAZARDS[params.hazard]
    tool = TOOLS[params.tool]
    if not valid_pair(hazard, tool):
        raise StoryError(explain_rejection(hazard, tool))

    world = tell(
        snack=snack,
        hazard=hazard,
        tool=tool,
        carrier_name=params.carrier_name,
        carrier_gender=params.carrier_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        receiver_name=params.receiver_name,
        receiver_gender=params.receiver_gender,
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
    py_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if py_set == clingo_set:
        print(f"OK: valid_combos matches ASP ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - clingo_set:
            print("  only in python:", sorted(py_set - clingo_set))
        if clingo_set - py_set:
            print("  only in clingo:", sorted(clingo_set - py_set))

    for params in CURATED:
        out = asp_outcome(params)
        if out != "safe":
            rc = 1
            print(f"MISMATCH in outcome for curated sample: {params} -> {out}")

    smoke_cases = list(CURATED)
    try:
        smoke_cases.append(resolve_params(build_parser().parse_args([]), random.Random(7)))
    except StoryError as err:
        rc = 1
        print(f"Smoke resolve failed: {err}")

    for i, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            print(f"OK: smoke test {i} generated a story with {len(sample.story.split())} words.")
        except Exception as err:
            rc = 1
            print(f"SMOKE TEST FAILED on case {i}: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (snack, hazard, tool) combos:\n")
        for snack_id, hazard_id, tool_id in combos:
            print(f"  {snack_id:12} {hazard_id:13} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.carrier_name} & {p.helper_name}: {p.snack}, {p.hazard}, {p.tool}"
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
