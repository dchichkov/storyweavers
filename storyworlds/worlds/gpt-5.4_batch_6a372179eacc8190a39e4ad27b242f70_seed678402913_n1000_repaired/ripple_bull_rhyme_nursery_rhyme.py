#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ripple_bull_rhyme_nursery_rhyme.py
=============================================================

A small storyworld for nursery-rhyme-like tales about a little bull, a pond
ripple, and a floating thing that drifts just out of reach. The world model
tracks physical state (wetness, mud, drifting distance, recovery) and emotional
state (pride, worry, patience, relief). Story text is rendered from simulated
state, with a reasonableness gate and an inline ASP twin.

Run it
------
    python storyworlds/worlds/gpt-5.4/ripple_bull_rhyme_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/ripple_bull_rhyme_nursery_rhyme.py --item wreath --tool reed_hook
    python storyworlds/worlds/gpt-5.4/ripple_bull_rhyme_nursery_rhyme.py --tool spoon
    python storyworlds/worlds/gpt-5.4/ripple_bull_rhyme_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/ripple_bull_rhyme_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/ripple_bull_rhyme_nursery_rhyme.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "hen", "duck", "goose", "mother", "sister"}
        male = {"boy", "man", "bull", "calf", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    water: str
    bank: str
    opening: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FloatingItem:
    id: str
    label: str
    phrase: str
    owner_kind: str
    start: str
    rescued: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    reach: int
    sense: int
    rhyme: str
    rescue_text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FriendSpec:
    id: str
    type: str
    label: str
    cry: str
    calm: str
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


def _r_ripple(world: World) -> list[str]:
    out: list[str] = []
    pond = world.get("pond")
    item = world.get("item")
    bull = world.get("bull")
    friend = world.get("friend")
    if bull.meters["stomped"] >= THRESHOLD:
        sig = ("ripple",)
        if sig not in world.fired:
            world.fired.add(sig)
            pond.meters["ripple"] += 1
            item.meters["drift"] += 1
            friend.memes["worry"] += 1
            out.append("__ripple__")
    return out


def _r_mud(world: World) -> list[str]:
    out: list[str] = []
    bull = world.get("bull")
    if bull.meters["in_water"] >= THRESHOLD:
        sig = ("mud",)
        if sig not in world.fired:
            world.fired.add(sig)
            bull.meters["wet"] += 1
            bull.meters["muddy"] += 1
            bull.memes["embarrassed"] += 1
            out.append("__mud__")
    return out


CAUSAL_RULES = [
    Rule(name="ripple", tag="physical", apply=_r_ripple),
    Rule(name="mud", tag="physical", apply=_r_mud),
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


def drift_need(item: FloatingItem) -> int:
    return {
        "wreath": 2,
        "bonnet": 3,
        "drum": 2,
        "kite": 3,
    }[item.id]


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def rescue_possible(item: FloatingItem, tool: Tool) -> bool:
    return tool.reach >= drift_need(item)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for item_id, item in ITEMS.items():
            for tool_id, tool in TOOLS.items():
                if tool.sense >= SENSE_MIN and rescue_possible(item, tool):
                    for friend_id in FRIENDS:
                        combos.append((place_id, item_id, tool_id, friend_id))
    return combos


def predict_charge(world: World) -> dict:
    sim = world.copy()
    bull = sim.get("bull")
    bull.meters["stomped"] += 1
    bull.meters["in_water"] += 1
    propagate(sim, narrate=False)
    return {
        "ripple": sim.get("pond").meters["ripple"],
        "drift": sim.get("item").meters["drift"],
        "wet": sim.get("bull").meters["wet"],
    }


def nursery_line(a: str, b: str) -> str:
    return f"{a}; {b}."


def opening(world: World, place: Place, bull: Entity, friend: Entity, item: FloatingItem) -> None:
    bull.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        nursery_line(
            f"In {place.label}, where willows sway, little {bull.label} kicked at clover all the day",
            place.opening,
        )
    )
    world.say(
        nursery_line(
            f"By {place.water}, a bright {item.label} danced and did not stay",
            f"it bobbed on every ripple and drifted from the hay",
        )
    )
    world.say(
        nursery_line(
            f'{friend.label.capitalize()} cried, "{friend.cry}"',
            f"and little {bull.label} puffed with pride and stamped the bank nearby",
        )
    )


def warn(world: World, bull: Entity, friend: Entity, place: Place, item: FloatingItem) -> None:
    pred = predict_charge(world)
    world.facts["predicted_drift"] = int(pred["drift"])
    world.facts["predicted_wet"] = int(pred["wet"])
    bull.memes["pride"] += 1
    friend.memes["care"] += 1
    world.say(
        nursery_line(
            f'{friend.label.capitalize()} said, "{friend.calm}"',
            f"one splash will wake the water, and the {item.label} will slip away at {place.bank}",
        )
    )


def charge(world: World, bull: Entity, item: FloatingItem) -> None:
    bull.meters["stomped"] += 1
    bull.meters["in_water"] += 1
    bull.memes["defiance"] += 1
    propagate(world, narrate=False)
    world.say(
        nursery_line(
            f"But little {bull.label} snorted, " + '"I am bold, and I am full!"',
            f"he lunged to catch the floating thing, hoof first, the eager bull",
        )
    )
    if world.get("pond").meters["ripple"] >= THRESHOLD:
        world.say(
            nursery_line(
                f"The water ran in rings and rings, a silver jumping ripple",
                f"the {item.label} slid farther out beyond his muddy nipple",
            )
        )


def rescue(world: World, bull: Entity, friend: Entity, item: FloatingItem, tool: Tool) -> None:
    item.meters["rescued"] += 1
    bull.memes["relief"] += 1
    friend.memes["relief"] += 1
    bull.memes["patience"] += 1
    bull.meters["in_water"] = 0.0
    world.say(
        nursery_line(
            f"Then {friend.label} found {tool.phrase}",
            tool.rescue_text.format(item=item.label),
        )
    )
    world.say(
        nursery_line(
            f"The little bull stood still at last and watched the water settle",
            f"soon {item.rescued}, and sunshine winked on horn and reed and kettle",
        )
    )


def fail_rescue(world: World, bull: Entity, friend: Entity, item: FloatingItem, tool: Tool, place: Place) -> None:
    bull.memes["sad"] += 1
    friend.memes["sad"] += 1
    world.say(
        nursery_line(
            f"Then {friend.label} tried {tool.phrase}",
            tool.fail_text.format(item=item.label),
        )
    )
    world.say(
        nursery_line(
            f"The {item.label} twirled beyond them still and turned with every wave",
            f"so little {bull.label} left it there and let the quiet {place.water} save",
        )
    )


def lesson(world: World, bull: Entity, friend: Entity, item: FloatingItem) -> None:
    bull.memes["lesson"] += 1
    friend.memes["love"] += 1
    if world.get("item").meters["rescued"] >= THRESHOLD:
        world.say(
            nursery_line(
                f'{friend.label.capitalize()} smiled, "Soft steps help more than thunder; that is gentle rule"',
                f"and little {bull.label} learned still water serves a kinder bull",
            )
        )
    else:
        world.say(
            nursery_line(
                f'{friend.label.capitalize()} sighed, "Some things drift best when left to pond and pool"',
                f"and little {bull.label} learned loud hooves can never hush a ripple's rule",
            )
        )


def ending(world: World, place: Place, bull: Entity, friend: Entity, item: FloatingItem) -> None:
    if world.get("item").meters["rescued"] >= THRESHOLD:
        world.say(
            nursery_line(
                f"Home went the pair by dusk's soft light, no longer in a rush",
                f"the bank lay calm, the reeds lay straight, and even the ripple learned to hush",
            )
        )
    else:
        world.say(
            nursery_line(
                f"Home went the pair by dusk's soft light, with slower hoof and tread",
                f"the pond kept one small floating prize, but wiser thoughts filled little {bull.label}'s head",
            )
        )


def tell(
    place: Place,
    item_cfg: FloatingItem,
    tool_cfg: Tool,
    friend_cfg: FriendSpec,
    bull_name: str = "Brindle",
) -> World:
    world = World()
    bull = world.add(Entity(id=bull_name, kind="character", type="bull", label=bull_name.lower(), role="bull"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_cfg.type, label=friend_cfg.label, role="friend"))
    pond = world.add(Entity(id="pond", kind="thing", type="pond", label=place.water, role="pond"))
    item = world.add(Entity(id="item", kind="thing", type="item", label=item_cfg.label, phrase=item_cfg.phrase, role="item"))
    world.facts["bull_name"] = bull_name

    opening(world, place, bull, friend, item_cfg)
    world.para()
    warn(world, bull, friend, place, item_cfg)
    charge(world, bull, item_cfg)

    world.para()
    if rescue_possible(item_cfg, tool_cfg):
        rescue(world, bull, friend, item_cfg, tool_cfg)
        outcome = "rescued"
    else:
        fail_rescue(world, bull, friend, item_cfg, tool_cfg, place)
        outcome = "drifted"

    world.para()
    lesson(world, bull, friend, item_cfg)
    ending(world, place, bull, friend, item_cfg)

    world.facts.update(
        place=place,
        item_cfg=item_cfg,
        tool=tool_cfg,
        friend_cfg=friend_cfg,
        bull=bull,
        friend=friend,
        pond=pond,
        item=item,
        outcome=outcome,
        drift_need=drift_need(item_cfg),
        predicted_drift=world.facts.get("predicted_drift", 0),
        predicted_wet=world.facts.get("predicted_wet", 0),
    )
    return world


PLACES = {
    "meadow_pond": Place(
        id="meadow_pond",
        label="the meadow green",
        water="the meadow pond",
        bank="the grassy bank",
        opening="where bees hummed low and white clouds lay",
        ending="the reeds leaned low at end of day",
        tags={"pond", "farm"},
    ),
    "mill_pool": Place(
        id="mill_pool",
        label="the mill-yard lane",
        water="the mill pool",
        bank="the mossy edge",
        opening="where old wheels dreamed beside the spray",
        ending="the wheel grew still at close of day",
        tags={"pond", "mill"},
    ),
    "clover_brook": Place(
        id="clover_brook",
        label="the clover field",
        water="the brookside pool",
        bank="the daisy bank",
        opening="where clover bent in scented sway",
        ending="the swallows dipped at end of day",
        tags={"brook", "farm"},
    ),
}

ITEMS = {
    "wreath": FloatingItem(
        id="wreath",
        label="wreath",
        phrase="a daisy wreath",
        owner_kind="lamb",
        start="A daisy wreath had slipped away.",
        rescued="the daisy wreath was hooked and lifted from the gleam",
        tags={"wreath", "flowers"},
    ),
    "bonnet": FloatingItem(
        id="bonnet",
        label="bonnet",
        phrase="a blue bonnet",
        owner_kind="goat",
        start="A blue bonnet had blown away.",
        rescued="the blue bonnet was drawn to shore without a tear or seam",
        tags={"bonnet", "clothes"},
    ),
    "drum": FloatingItem(
        id="drum",
        label="drum",
        phrase="a tin drum",
        owner_kind="boy",
        start="A tin drum had bobbed away.",
        rescued="the little drum came clinking back with one bright watery gleam",
        tags={"drum", "music"},
    ),
    "kite": FloatingItem(
        id="kite",
        label="kite",
        phrase="a paper kite",
        owner_kind="girl",
        start="A paper kite had sailed away.",
        rescued="the paper kite was teased to land before it soaked its seam",
        tags={"kite", "paper"},
    ),
}

TOOLS = {
    "reed_hook": Tool(
        id="reed_hook",
        label="reed hook",
        phrase="a bent reed hook",
        reach=3,
        sense=3,
        rhyme="hook",
        rescue_text="with patient hands it drew the {item} near by crook",
        fail_text="but the bent reed hook was short, and never reached the {item}",
        qa_text="used a bent reed hook to pull it to shore",
        tags={"hook", "tool"},
    ),
    "rake": Tool(
        id="rake",
        label="garden rake",
        phrase="the little garden rake",
        reach=3,
        sense=3,
        rhyme="rake",
        rescue_text="and with the little garden rake it nudged the {item} home",
        fail_text="but the garden rake was caught in rushes before it touched the {item}",
        qa_text="used a little garden rake to nudge it home",
        tags={"rake", "tool"},
    ),
    "willow_branch": Tool(
        id="willow_branch",
        label="willow branch",
        phrase="a long willow branch",
        reach=2,
        sense=2,
        rhyme="branch",
        rescue_text="a long willow branch reached out and tapped the {item} close",
        fail_text="but the willow branch was too short, and only made the water rose",
        qa_text="used a long willow branch to tap it close",
        tags={"branch", "tool"},
    ),
    "spoon": Tool(
        id="spoon",
        label="wooden spoon",
        phrase="a wooden spoon",
        reach=1,
        sense=1,
        rhyme="spoon",
        rescue_text="the wooden spoon somehow scooped the {item} in",
        fail_text="but the wooden spoon was much too short for the {item}",
        qa_text="tried a wooden spoon",
        tags={"spoon", "tool"},
    ),
}

FRIENDS = {
    "duck": FriendSpec(
        id="duck",
        type="duck",
        label="the duck",
        cry="Mind the ring and mind the wave!",
        calm="Soft hooves, dear bull, will help us best.",
        tags={"duck"},
    ),
    "hen": FriendSpec(
        id="hen",
        type="hen",
        label="the hen",
        cry="Hush your hooves and save, oh save!",
        calm="Quick hearts need calm feet by the nest.",
        tags={"hen"},
    ),
    "frog": FriendSpec(
        id="frog",
        type="frog",
        label="the frog",
        cry="Plip and plop! Do not be rash!",
        calm="Still water listens better than a splash.",
        tags={"frog"},
    ),
}

BULL_NAMES = ["Brindle", "Bram", "Moss", "Tumble", "Cob", "Pip"]


@dataclass
class StoryParams:
    place: str
    item: str
    tool: str
    friend: str
    bull_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="meadow_pond",
        item="wreath",
        tool="reed_hook",
        friend="duck",
        bull_name="Brindle",
    ),
    StoryParams(
        place="mill_pool",
        item="drum",
        tool="rake",
        friend="frog",
        bull_name="Bram",
    ),
    StoryParams(
        place="clover_brook",
        item="bonnet",
        tool="willow_branch",
        friend="hen",
        bull_name="Moss",
    ),
    StoryParams(
        place="meadow_pond",
        item="kite",
        tool="reed_hook",
        friend="frog",
        bull_name="Tumble",
    ),
]


KNOWLEDGE = {
    "pond": [
        (
            "What is a ripple?",
            "A ripple is a small ring or wave that moves across water. One splash can send many tiny ripples away from the shore.",
        )
    ],
    "bull": [
        (
            "What is a bull?",
            "A bull is a male cow. A young bull can be strong and lively, but he still has to learn to move gently.",
        )
    ],
    "hook": [
        (
            "Why is a hook or crook useful for reaching something on water?",
            "A hooked stick can catch or pull a floating thing without making you step into the water. That keeps the bank calmer and safer.",
        )
    ],
    "rake": [
        (
            "What does a garden rake do?",
            "A garden rake has a long handle and a head that can pull light things closer. In a careful grown-up-style fix, its length matters more than pushing with your feet.",
        )
    ],
    "branch": [
        (
            "Why can a long branch help from the shore?",
            "A long branch lets you reach farther without wading in. Staying on the shore keeps the water from splashing more.",
        )
    ],
    "spoon": [
        (
            "Why is a spoon a poor tool for reaching into a pond?",
            "A spoon is short, so it cannot reach far across water. A poor tool makes the problem harder instead of easier.",
        )
    ],
    "wreath": [
        (
            "What is a wreath?",
            "A wreath is a ring made from flowers or leaves. A floating wreath is light, so water can carry it away.",
        )
    ],
    "bonnet": [
        (
            "What is a bonnet?",
            "A bonnet is a soft hat. If it falls on water, it may drift and get wet quickly.",
        )
    ],
    "drum": [
        (
            "What is a drum?",
            "A drum is a musical instrument you tap to make a beat. A little tin drum can bob on water for a moment before it sinks or fills.",
        )
    ],
    "kite": [
        (
            "Why can paper be ruined by water?",
            "Paper gets soggy and weak when it is wet. That is why a paper kite needs a quick, careful rescue.",
        )
    ],
}
KNOWLEDGE_ORDER = ["pond", "bull", "wreath", "bonnet", "drum", "kite", "hook", "rake", "branch", "spoon"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    bull = f["bull"]
    item = f["item_cfg"]
    place = f["place"]
    friend = f["friend_cfg"]
    outcome = f["outcome"]
    if outcome == "rescued":
        return [
            f'Write a nursery-rhyme story that includes the words "ripple" and "bull". Set it by {place.water} and let a little bull learn to use calm help instead of splashing.',
            f"Tell a rhyming tale where {bull.id} the little bull tries to grab a floating {item.label}, makes a ripple, and then listens to {friend.label} and rescues it the gentle way.",
            f"Write a short child-facing rhyme about a boastful bull, a drifting {item.label}, and a soft ending beside the pond.",
        ]
    return [
        f'Write a nursery-rhyme story that includes the words "ripple" and "bull". Set it by {place.water} and let the little bull learn that stomping can make things drift farther away.',
        f"Tell a rhyming tale where {bull.id} the little bull splashes after a floating {item.label}, but the water stays too lively to catch.",
        f"Write a short rhyme about a young bull who learns to move more gently near water.",
    ]


def pair_answer(world: World) -> str:
    bull = world.facts["bull"]
    friend = world.facts["friend_cfg"]
    return f"It is about {bull.id}, a little bull, and {friend.label} by the pond."


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    bull = f["bull"]
    item = f["item_cfg"]
    tool = f["tool"]
    place = f["place"]
    friend = f["friend_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            pair_answer(world),
        ),
        (
            f"What was floating on the water?",
            f"A {item.label} was floating on {place.water}. It bobbed on the water and tempted {bull.id} to rush after it.",
        ),
        (
            f"Why did the {item.label} drift farther away?",
            f"It drifted farther because {bull.id} stomped into the water and made a bigger ripple. The splash pushed the floating thing away instead of bringing it closer.",
        ),
    ]
    if f["predicted_wet"] >= 1:
        qa.append(
            (
                f"Why did {friend.label} warn {bull.id} before he charged?",
                f"{friend.label.capitalize()} warned him because one splash would make the water ripple more and leave the little bull wet and muddy. The warning came from seeing that rushing would worsen the problem, not solve it.",
            )
        )
    if f["outcome"] == "rescued":
        qa.append(
            (
                f"How did they get the {item.label} back?",
                f"They used {tool.phrase} and stayed on the shore. That worked because the tool could reach the drifting {item.label} without making the pond splash again.",
            )
        )
        qa.append(
            (
                f"What did {bull.id} learn at the end?",
                f"{bull.id} learned that soft steps can help more than loud hooves. When he stopped rushing, the water settled and the rescue became easier.",
            )
        )
    else:
        qa.append(
            (
                f"Did they bring the {item.label} back?",
                f"No. The {item.label} drifted too far for {tool.phrase}, so they left it on the quiet water. The sad turn taught {bull.id} that a poor tool and a noisy splash can make a small problem bigger.",
            )
        )
        qa.append(
            (
                f"What did {bull.id} learn at the end?",
                f"He learned that stomping at a ripple does not make water obey. Next time he will pause first and choose a better way to help.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"pond", "bull"} | set(f["item_cfg"].tags) | set(f["tool"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_tool(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    better = ", ".join(sorted(t.id for t in sensible_tools()))
    return (
        f"(No story: '{tool_id}' is known in this world, but it is too poor a rescue tool "
        f"(sense={tool.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def explain_combo(item: FloatingItem, tool: Tool) -> str:
    return (
        f"(No story: {tool.phrase} cannot honestly reach the drifting {item.label}. "
        f"The rescue tool must be long enough to solve the pond problem.)"
    )


ASP_RULES = r"""
sensible_tool(Tl) :- tool(Tl), sense(Tl, S), sense_min(M), S >= M.
rescue_possible(It, Tl) :- item(It), tool(Tl), need(It, N), reach(Tl, R), R >= N.
valid(Pl, It, Tl, Fr) :- place(Pl), item(It), friend(Fr), sensible_tool(Tl), rescue_possible(It, Tl).

outcome(rescued) :- chosen_item(It), chosen_tool(Tl), rescue_possible(It, Tl).
outcome(drifted) :- chosen_item(It), chosen_tool(Tl), not rescue_possible(It, Tl).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("need", item_id, drift_need(item)))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("reach", tool_id, tool.reach))
        lines.append(asp.fact("sense", tool_id, tool.sense))
    for friend_id in FRIENDS:
        lines.append(asp.fact("friend", friend_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
            asp.fact("chosen_item", params.item),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    item = ITEMS[params.item]
    tool = TOOLS[params.tool]
    return "rescued" if rescue_possible(item, tool) else "drifted"


def smoke_test_generate() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    if "bull" not in sample.story.lower():
        raise StoryError("Smoke test failed: story did not mention the bull.")
    if "ripple" not in sample.story.lower():
        raise StoryError("Smoke test failed: story did not mention a ripple.")


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
    for seed in range(40):
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
        smoke_test_generate()
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme storyworld: a little bull, a pond ripple, and a gentle rescue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--bull-name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(args.tool))
    if args.item and args.tool:
        item = ITEMS[args.item]
        tool = TOOLS[args.tool]
        if not rescue_possible(item, tool):
            raise StoryError(explain_combo(item, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.tool is None or combo[2] == args.tool)
        and (args.friend is None or combo[3] == args.friend)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, tool_id, friend_id = rng.choice(sorted(combos))
    bull_name = args.bull_name or rng.choice(BULL_NAMES)
    return StoryParams(
        place=place_id,
        item=item_id,
        tool=tool_id,
        friend=friend_id,
        bull_name=bull_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.friend not in FRIENDS:
        raise StoryError(f"(Unknown friend: {params.friend})")

    item = ITEMS[params.item]
    tool = TOOLS[params.tool]
    if tool.sense < SENSE_MIN:
        raise StoryError(explain_tool(params.tool))
    if not rescue_possible(item, tool):
        raise StoryError(explain_combo(item, tool))

    world = tell(
        place=PLACES[params.place],
        item_cfg=item,
        tool_cfg=tool,
        friend_cfg=FRIENDS[params.friend],
        bull_name=params.bull_name,
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
        print(f"{len(combos)} compatible (place, item, tool, friend) combos:\n")
        for place_id, item_id, tool_id, friend_id in combos:
            print(f"  {place_id:12} {item_id:8} {tool_id:13} {friend_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.bull_name}: {p.item} at {p.place} with {p.tool} and {p.friend}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
