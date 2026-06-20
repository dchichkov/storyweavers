#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cell_compactor_deep_puddle_lesson_learned_surprise.py
=================================================================================

A tiny storyworld about a child, a dropped cell phone, a deep puddle, and a
garbage truck whose compactor becomes part of the funny rescue.

The domain is deliberately small and constraint-checked:

* A cherished "cell" item falls into a deep puddle.
* The child wants to wade in, but the puddle is too deep and slippery.
* A rescue only counts if the chosen tool can honestly reach and grab the item.
* Floating items may drift closer when the garbage truck's compactor thumps.
* The ending always includes a lesson learned and a small surprise.

Run it
------
    python storyworlds/worlds/gpt-5.4/cell_compactor_deep_puddle_lesson_learned_surprise.py
    python storyworlds/worlds/gpt-5.4/cell_compactor_deep_puddle_lesson_learned_surprise.py --item old_cell_phone --tool litter_claw
    python storyworlds/worlds/gpt-5.4/cell_compactor_deep_puddle_lesson_learned_surprise.py --tool umbrella_hook
    python storyworlds/worlds/gpt-5.4/cell_compactor_deep_puddle_lesson_learned_surprise.py --all --qa
    python storyworlds/worlds/gpt-5.4/cell_compactor_deep_puddle_lesson_learned_surprise.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man", "driver"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class LostItem:
    id: str
    label: str
    phrase: str
    floats: bool
    rigid: bool
    metal: bool
    sentimental: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    reach: str
    needs_near: bool
    works_on_float: bool
    works_on_sink: bool
    needs_rigid: bool = False
    needs_metal: bool = False
    helper: str = "parent"
    action: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    label: str
    source: str
    text: str
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


def _r_wade(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["wading"] < THRESHOLD:
        return []
    sig = ("wade", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["soaked"] += 1
    child.meters["wobble"] += 1
    child.memes["alarm"] += 1
    world.get("parent").memes["fear"] += 1
    return ["__wade__"]


def _r_compactor_ripple(world: World) -> list[str]:
    item = world.get("item")
    truck = world.get("truck")
    if truck.meters["compacting"] < THRESHOLD:
        return []
    if not item.attrs.get("in_puddle"):
        return []
    if not item.attrs.get("floats"):
        return []
    if item.attrs.get("position") != "far":
        return []
    sig = ("ripple", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.attrs["position"] = "near"
    item.meters["bob"] += 1
    return ["The puddle gave a round wobble, and the little cell phone bobbed closer to the curb."]


def _r_retrieve(world: World) -> list[str]:
    item = world.get("item")
    tool = world.facts.get("tool_cfg")
    if tool is None:
        return []
    helper = world.get(world.facts["helper_id"])
    if helper.meters["reaching"] < THRESHOLD:
        return []
    if not item.attrs.get("in_puddle"):
        return []
    if not can_retrieve(world.facts["item_cfg"], tool, item.attrs.get("position", "far")):
        return []
    sig = ("retrieve", item.id, tool.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.attrs["in_puddle"] = False
    item.attrs["recovered"] = True
    item.meters["wet"] += 1
    child = world.get("child")
    child.memes["relief"] += 1
    helper.memes["pride"] += 1
    return [f"{helper.id} {tool.action} and lifted the wet {item.label} out of the puddle."]


CAUSAL_RULES = [
    Rule("wade", "physical", _r_wade),
    Rule("compactor_ripple", "physical", _r_compactor_ripple),
    Rule("retrieve", "physical", _r_retrieve),
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
        for s in produced:
            world.say(s)
    return produced


ITEMS = {
    "toy_cell_phone": LostItem(
        "toy_cell_phone",
        "toy cell phone",
        "a cherry-red toy cell phone with three giant buttons",
        True,
        True,
        False,
        "because it made the silliest pretend ring in the world",
        tags={"cell_phone", "floating"},
    ),
    "old_cell_phone": LostItem(
        "old_cell_phone",
        "old cell phone",
        "an old cell phone in a bumpy blue case",
        False,
        True,
        False,
        "because it still held a picture of the child wearing pudding like a hat",
        tags={"cell_phone", "phone"},
    ),
    "banana_cell_case": LostItem(
        "banana_cell_case",
        "banana cell phone case",
        "a squishy banana-shaped cell phone case",
        True,
        False,
        False,
        "because it made every pocket look like it had packed lunch by mistake",
        tags={"cell_phone", "floating"},
    ),
}

TOOLS = {
    "umbrella_hook": Tool(
        "umbrella_hook",
        "umbrella hook",
        "the hooked handle of the umbrella",
        "short",
        True,
        True,
        False,
        needs_rigid=False,
        helper="parent",
        action="leaned far over with the umbrella hook",
        tags={"umbrella"},
    ),
    "butterfly_net": Tool(
        "butterfly_net",
        "butterfly net",
        "a butterfly net from the truck's side bin",
        "long",
        False,
        True,
        False,
        helper="driver",
        action="stretched the butterfly net right over the shiny water",
        tags={"net"},
    ),
    "litter_claw": Tool(
        "litter_claw",
        "litter claw",
        "a long litter claw from the garbage truck",
        "long",
        False,
        True,
        True,
        needs_rigid=True,
        helper="driver",
        action="clicked the litter claw open like a metal crab",
        tags={"claw"},
    ),
    "magnet_wand": Tool(
        "magnet_wand",
        "magnet wand",
        "a magnet wand from the truck's tool box",
        "medium",
        True,
        False,
        True,
        needs_metal=True,
        helper="driver",
        action="lowered the magnet wand with a careful grin",
        tags={"magnet"},
    ),
}

SURPRISES = {
    "sticker": Surprise(
        "sticker",
        "garbage truck sticker",
        "driver",
        'Then the driver reached into his pocket and handed over a bright garbage truck sticker shaped like a star. "For the best puddle patience I saw all morning," he said.',
        tags={"sticker"},
    ),
    "honk": Surprise(
        "honk",
        "tiny horn honk",
        "driver",
        'Then the driver gave the gentlest little honk on the truck horn. It was not a scary BLAAAT at all. It was a polite beep-beep, and it made the child laugh so hard the puddle almost got a second splash just from giggles.',
        tags={"honk"},
    ),
    "clean_towel": Surprise(
        "clean_towel",
        "checkered towel",
        "parent",
        'Then the parent opened the stroller basket and pulled out a tiny checkered towel no one had remembered packing. "Surprise," the parent said. "My bag is basically a magician."',
        tags={"towel"},
    ),
}


def can_retrieve(item: LostItem, tool: Tool, position: str) -> bool:
    if tool.needs_near and position != "near":
        return False
    if item.floats and not tool.works_on_float:
        return False
    if (not item.floats) and not tool.works_on_sink:
        return False
    if tool.needs_rigid and not item.rigid:
        return False
    if tool.needs_metal and not item.metal:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for item_id, item in ITEMS.items():
        for tool_id, tool in TOOLS.items():
            start_pos = "far"
            if item.floats:
                final_pos = "near"
            else:
                final_pos = start_pos
            if can_retrieve(item, tool, final_pos):
                for surprise_id, surprise in SURPRISES.items():
                    if surprise.source == tool.helper:
                        combos.append((item_id, tool_id, surprise_id))
    return combos


@dataclass
class StoryParams:
    item: str
    tool: str
    surprise: str
    child: str
    gender: str
    parent: str
    mood: str
    seed: Optional[int] = None


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Finn", "Theo", "Eli", "Noah"]
MOODS = ["bouncy", "chatty", "curious", "goofy", "sunny", "wiggly"]


def setup_story(world: World, child: Entity, parent: Entity, item: LostItem) -> None:
    truck = world.get("truck")
    child.memes["joy"] += 1
    world.say(
        f"After a rainy morning, {child.id} and {child.pronoun('possessive')} {parent.label_word} stopped beside a deep puddle at the curb to watch the garbage truck rumble by."
    )
    world.say(
        f"In {child.pronoun('possessive')} hand was {item.phrase}. {child.id} was using it like a tiny reporter's microphone and whispering, "
        f'"Hello from Splash Street. A very important truck is arriving."'
    )
    world.say(
        f"The truck rolled closer, shiny and huge, and the driver gave a friendly wave from the cab."
    )
    truck.meters["arrived"] += 1


def drop_it(world: World, child: Entity, item: LostItem) -> None:
    ent = world.get("item")
    ent.attrs["in_puddle"] = True
    ent.attrs["position"] = "far"
    ent.attrs["floats"] = item.floats
    child.memes["shock"] += 1
    world.say(
        f"Then {child.id} made one extra-silly drumroll on the curb, bumped {child.pronoun('possessive')} own elbow, and ploink -- the {item.label} flew straight into the deep puddle."
    )
    if item.floats:
        world.say("It spun once like a pancake on parade and floated just out of reach.")
    else:
        world.say("It sank with one rude gulp and hid under the brown water.")


def warn(world: World, child: Entity, parent: Entity) -> None:
    child.memes["desire"] += 1
    world.say(
        f'"I can get it!" cried {child.id}, already leaning toward the puddle.'
    )
    world.say(
        f'But {parent.label_word.capitalize()} caught the back of {child.pronoun("possessive")} raincoat and said, '
        f'"No wading into a deep puddle. Deep puddles can hide slippery holes, and the water is too yucky to trust."'
    )
    world.facts["lesson_core"] = "ask for help instead of climbing into deep puddles"


def compactor_turn(world: World, item: LostItem) -> None:
    truck = world.get("truck")
    driver = world.get("driver")
    world.para()
    world.say(
        f'Just then the driver hopped down and called, "Everyone stand back. I have to use the compactor."'
    )
    truck.meters["compacting"] += 1
    driver.memes["helpfulness"] += 1
    world.say(
        'The compactor gave a chunky WHUMPH-squish-clunk that sounded like a giant chewing a cardboard sandwich.'
    )
    propagate(world, narrate=True)
    if not item.floats:
        world.say(
            "The puddle only made grumpy circles, but at least now everyone knew the lost thing was not going to swim back by itself."
        )


def rescue(world: World, tool: Tool) -> None:
    helper = world.get(world.facts["helper_id"])
    helper.meters["reaching"] += 1
    if helper.id == "Driver":
        world.say(
            f'"Let me try with {tool.phrase}," the driver said.'
        )
    else:
        world.say(
            f'"Let me try with {tool.phrase}," {helper.label_word} said.'
        )
    propagate(world, narrate=True)


def lesson(world: World, child: Entity, parent: Entity, item: LostItem) -> None:
    child.memes["lesson"] += 1
    child.memes["relief"] += 1
    world.para()
    world.say(
        f"{child.id} hugged the damp {item.label} to {child.pronoun('possessive')} chest and made a face. It smelled like rainwater and old leaves."
    )
    world.say(
        f'"Okay," {child.pronoun()} said. "Next time I will {world.facts["lesson_core"]}."'
    )
    world.say(
        f'{parent.label_word.capitalize()} smiled. "That is the lesson. Puddles can be funny, but deep puddles are not for climbing in."'
    )


def surprise_end(world: World, child: Entity, surprise: Surprise, item: LostItem) -> None:
    world.say(surprise.text)
    if surprise.id == "clean_towel":
        world.say(
            f"They patted the {item.label} dry as much as they could, and soon it looked less like puddle soup and more like itself again."
        )
    else:
        world.say(
            f"{child.id} stood a little taller, grinning so wide that even the wet {item.label} seemed less tragic."
        )
    world.say(
        f"When the truck rolled away, {child.id} waved with one hand, held the rescued {item.label} with the other, and stayed safely on the curb beside the deep puddle."
    )


def tell(params: StoryParams) -> World:
    item_cfg = ITEMS[params.item]
    tool_cfg = TOOLS[params.tool]
    surprise_cfg = SURPRISES[params.surprise]

    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.gender, role="child", traits=[params.mood]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    driver = world.add(Entity(id="Driver", kind="character", type="driver", role="driver", label="the driver"))
    truck = world.add(Entity(id="truck", type="garbage_truck", label="garbage truck"))
    item = world.add(Entity(id="item", type="lost_item", label=item_cfg.label, phrase=item_cfg.phrase))
    world.facts["item_cfg"] = item_cfg
    world.facts["tool_cfg"] = tool_cfg
    world.facts["surprise_cfg"] = surprise_cfg
    world.facts["helper_id"] = "Driver" if tool_cfg.helper == "driver" else "Parent"

    setup_story(world, child, parent, item_cfg)
    world.para()
    drop_it(world, child, item_cfg)
    warn(world, child, parent)
    compactor_turn(world, item_cfg)
    world.para()
    rescue(world, tool_cfg)

    if not item.attrs.get("recovered"):
        raise StoryError("Internal error: chosen rescue did not recover the item.")

    lesson(world, child, parent, item_cfg)
    surprise_end(world, child, surprise_cfg, item_cfg)

    world.facts.update(
        child=child,
        parent=parent,
        driver=driver,
        truck=truck,
        item=item,
        recovered=item.attrs.get("recovered", False),
        floated=item_cfg.floats,
        drifted=(item_cfg.floats and item.meters["bob"] >= THRESHOLD),
    )
    return world


KNOWLEDGE = {
    "cell_phone": [
        (
            "What is a cell phone?",
            "A cell phone is a small device people use to talk, send messages, or take pictures. Some are real phones, and some are toy phones made for pretend play."
        )
    ],
    "phone": [
        (
            "Why should a wet phone be dried carefully?",
            "Water can get inside a phone and stop it from working. Drying it gently gives it a better chance to be okay."
        )
    ],
    "floating": [
        (
            "Why do some things float in puddles?",
            "Some things float because they are light or shaped in a way that lets the water hold them up. Other things sink if they are heavier or let water pull them down."
        )
    ],
    "umbrella": [
        (
            "What is an umbrella hook good for?",
            "A curved umbrella handle can catch or pull something light that is already close. It is not good for reaching far into dangerous water."
        )
    ],
    "net": [
        (
            "What does a net do?",
            "A net scoops something up without you needing to grab it with your hands. That can be useful when an object is floating in water."
        )
    ],
    "claw": [
        (
            "What is a litter claw?",
            "A litter claw is a grabber tool with long handles and pinching ends. It lets a grown-up pick something up from far away."
        )
    ],
    "magnet": [
        (
            "What does a magnet pick up?",
            "A magnet pulls on some kinds of metal. It does not pick up plastic or cloth just because they look shiny."
        )
    ],
    "sticker": [
        (
            "Why do stickers feel like a surprise?",
            "A sticker is a tiny gift that says someone noticed you. Small surprises can make a hard moment feel brighter."
        )
    ],
    "honk": [
        (
            "Why can a funny honk make people laugh?",
            "A sudden silly sound can surprise your brain in a playful way. That often turns worry into giggles."
        )
    ],
    "towel": [
        (
            "What is a towel for?",
            "A towel soaks up water and helps dry wet things. Even a small towel can be handy after rain."
        )
    ],
    "deep_puddle": [
        (
            "Why should children stay out of a deep puddle?",
            "A deep puddle can hide holes, slippery ground, or dirty water. It is safer to stay on the edge and ask a grown-up for help."
        )
    ],
    "compactor": [
        (
            "What is a compactor on a garbage truck?",
            "A compactor is the part of a garbage truck that presses trash down so it takes up less space. It is a powerful machine part, so children should stay back from it."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "cell_phone",
    "phone",
    "floating",
    "deep_puddle",
    "compactor",
    "umbrella",
    "net",
    "claw",
    "magnet",
    "sticker",
    "honk",
    "towel",
]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    item = world.facts["item_cfg"]
    tool = world.facts["tool_cfg"]
    surprise = world.facts["surprise_cfg"]
    return [
        'Write a funny story for a 3-to-5-year-old that includes the words "cell" and "compactor," takes place by a deep puddle, and ends with a lesson learned and a surprise.',
        f"Tell a comedy-tinged story where a {child.type} named {child.id} drops {item.phrase} into a deep puddle, wants to rush in after it, and is helped safely with {tool.phrase}.",
        f"Write a gentle story in which the garbage truck's compactor becomes part of the scene, the child learns not to climb into deep puddles, and the ending includes a small surprise: {surprise.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    item_cfg = world.facts["item_cfg"]
    tool = world.facts["tool_cfg"]
    surprise = world.facts["surprise_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {parent.label_word}, and a friendly garbage truck driver by a deep puddle."
        ),
        (
            f"What fell into the deep puddle?",
            f"The {item_cfg.label} fell into the puddle. It mattered to {child.id} {item_cfg.sentimental}."
        ),
        (
            f"Why did {parent.label_word} stop {child.id} from climbing into the puddle?",
            f"{parent.label_word.capitalize()} knew the puddle was deep, slippery, and dirty. The danger was not just getting wet; the child could wobble or step into something hidden under the water."
        ),
        (
            "What did the compactor do in the story?",
            "The garbage truck's compactor made a big funny thump while everyone stood back. In this story, that noisy moment became part of the rescue scene instead of just background noise."
        ),
    ]
    if world.facts.get("drifted"):
        qa.append(
            (
                "How did the floating item change during the story?",
                f"When the compactor thumped, the puddle wobbled and the {item_cfg.label} bobbed closer to the curb. That made it easier for the grown-up to reach it with {tool.phrase}."
            )
        )
    else:
        qa.append(
            (
                "How was the item rescued?",
                f"It did not float back on its own, so the grown-up used {tool.phrase} to reach in safely and lift it out. The rescue worked because the tool could reach the item without anyone stepping into the deep puddle."
            )
        )
    qa.append(
        (
            "What lesson did the child learn?",
            f"{child.id} learned to ask for help instead of climbing into deep puddles. The ending shows the lesson because {child.pronoun()} stays on the curb even after getting the {item_cfg.label} back."
        )
    )
    qa.append(
        (
            "What was the surprise at the end?",
            f"The surprise was {surprise.label}. It came after the rescue, so the scary moment finished with laughter instead of tears."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"deep_puddle", "compactor"} | set(world.facts["item_cfg"].tags) | set(world.facts["tool_cfg"].tags) | set(world.facts["surprise_cfg"].tags)
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
        attrs = {k: v for k, v in e.attrs.items() if v or v is False}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("toy_cell_phone", "umbrella_hook", "clean_towel", "Lily", "girl", "mother", "chatty"),
    StoryParams("toy_cell_phone", "butterfly_net", "sticker", "Ben", "boy", "father", "goofy"),
    StoryParams("old_cell_phone", "litter_claw", "honk", "Mia", "girl", "mother", "curious"),
    StoryParams("banana_cell_case", "butterfly_net", "sticker", "Theo", "boy", "father", "bouncy"),
]


def explain_rejection(item: LostItem, tool: Tool, surprise: Optional[Surprise] = None) -> str:
    if surprise is not None and surprise.source != tool.helper:
        return (
            f"(No story: the surprise '{surprise.id}' comes from a {surprise.source}, but the chosen tool '{tool.id}' is used by a {tool.helper}. Pick a matching surprise.)"
        )
    if item.floats and tool.needs_near:
        return (
            f"(No story: {tool.label} only works when something is close. It can rescue {item.label} only after the floating item drifts near the curb.)"
        )
    reason = []
    if not item.floats and not tool.works_on_sink:
        reason.append("the item sinks")
    if item.floats and not tool.works_on_float:
        reason.append("the item floats")
    if tool.needs_rigid and not item.rigid:
        reason.append("the item is too floppy to grab cleanly")
    if tool.needs_metal and not item.metal:
        reason.append("the item is not magnetic metal")
    joined = "; ".join(reason) if reason else "the tool does not honestly fit the rescue"
    return f"(No story: {tool.label} is unreasonable here because {joined}.)"


ASP_RULES = r"""
floating(I) :- item(I), floats(I).
sinking(I)  :- item(I), not floats(I).

drifts_near(I) :- floating(I).
final_near(I)  :- drifts_near(I).
final_far(I)   :- sinking(I).

tool_works_on(I, T) :-
    item(I), tool(T),
    floating(I), works_on_float(T),
    not needs_rigid(T).
tool_works_on(I, T) :-
    item(I), tool(T),
    floating(I), works_on_float(T),
    needs_rigid(T), rigid(I).
tool_works_on(I, T) :-
    item(I), tool(T),
    sinking(I), works_on_sink(T),
    not needs_rigid(T), not needs_metal(T).
tool_works_on(I, T) :-
    item(I), tool(T),
    sinking(I), works_on_sink(T),
    needs_rigid(T), rigid(I), not needs_metal(T).
tool_works_on(I, T) :-
    item(I), tool(T),
    sinking(I), works_on_sink(T),
    needs_metal(T), metal(I).

position_ok(I, T) :- item(I), tool(T), not needs_near(T).
position_ok(I, T) :- item(I), tool(T), needs_near(T), final_near(I).

rescuable(I, T) :- tool_works_on(I, T), position_ok(I, T).

valid(I, T, S) :- item(I), tool(T), surprise(S), rescuable(I, T), helper(T, H), source(S, H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.floats:
            lines.append(asp.fact("floats", iid))
        if item.rigid:
            lines.append(asp.fact("rigid", iid))
        if item.metal:
            lines.append(asp.fact("metal", iid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("helper", tid, tool.helper))
        if tool.needs_near:
            lines.append(asp.fact("needs_near", tid))
        if tool.works_on_float:
            lines.append(asp.fact("works_on_float", tid))
        if tool.works_on_sink:
            lines.append(asp.fact("works_on_sink", tid))
        if tool.needs_rigid:
            lines.append(asp.fact("needs_rigid", tid))
        if tool.needs_metal:
            lines.append(asp.fact("needs_metal", tid))
    for sid, surprise in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        lines.append(asp.fact("source", sid, surprise.source))
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
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))
    try:
        sample = generate(CURATED[0])
        if not sample.story or "compactor" not in sample.story.lower() or "cell" not in sample.story.lower():
            raise StoryError("Smoke test story missing required seed words or prose.")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a deep puddle, a dropped cell phone, a compactor, a lesson, and a surprise."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.tool:
        item = ITEMS[args.item]
        tool = TOOLS[args.tool]
        final_pos = "near" if item.floats else "far"
        if not can_retrieve(item, tool, final_pos):
            raise StoryError(explain_rejection(item, tool))
    if args.tool and args.surprise:
        tool = TOOLS[args.tool]
        surprise = SURPRISES[args.surprise]
        if surprise.source != tool.helper:
            raise StoryError(explain_rejection(ITEMS[args.item] if args.item else next(iter(ITEMS.values())), tool, surprise))

    combos = [
        c for c in valid_combos()
        if (args.item is None or c[0] == args.item)
        and (args.tool is None or c[1] == args.tool)
        and (args.surprise is None or c[2] == args.surprise)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, tool_id, surprise_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    mood = rng.choice(MOODS)
    return StoryParams(item_id, tool_id, surprise_id, name, gender, parent, mood)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(f"{len(combos)} compatible (item, tool, surprise) combos:\n")
        for item_id, tool_id, surprise_id in combos:
            print(f"  {item_id:18} {tool_id:14} {surprise_id}")
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
            header = f"### {p.child}: {p.item} with {p.tool} ({p.surprise})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
