#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/skin_lollipop_sharing_curiosity_space_adventure.py
=============================================================================

A standalone story world about two children playing astronauts, finding a
"mystery space sample," and learning that curiosity should be guided by safe
choices. The story always includes the words "skin" and "lollipop" and centers
Sharing + Curiosity in a child-facing Space Adventure style.

The core common-sense constraint is simple:

* a sample must actually be risky to bare skin for the warning to be honest
* a chosen tool must really keep skin away from the sample
* some stories are a near-miss (the warning works), and some include a small
  "ouch" moment before a grown-up helps

Run it
------
    python storyworlds/worlds/gpt-5.4/skin_lollipop_sharing_curiosity_space_adventure.py
    python storyworlds/worlds/gpt-5.4/skin_lollipop_sharing_curiosity_space_adventure.py --sample cactus
    python storyworlds/worlds/gpt-5.4/skin_lollipop_sharing_curiosity_space_adventure.py --tool magnifier
    python storyworlds/worlds/gpt-5.4/skin_lollipop_sharing_curiosity_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/skin_lollipop_sharing_curiosity_space_adventure.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/skin_lollipop_sharing_curiosity_space_adventure.py --qa --json
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
CAUTIOUS_TRAITS = {"careful", "cautious", "gentle", "patient"}
CURIOSITY_INIT = 6.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    risky_to_skin: bool = False
    protects_skin: bool = False
    shared: bool = False
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
    launch_line: str
    target: str
    dark_corner: str
    crew_word: str
    ending_line: str


@dataclass
class SampleKind:
    id: str
    label: str
    phrase: str
    where: str
    danger: str
    touch_line: str
    hurt_line: str
    care_line: str
    severity: int = 1
    risky_to_skin: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    protects: set[str]
    intro: str
    use_line: str
    share_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    color: str
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
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_skin_reacts(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.kids():
        if kid.meters["bare_touch"] < THRESHOLD:
            continue
        sample = world.get("sample")
        if not sample.risky_to_skin:
            continue
        sig = ("skin_reacts", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        effect = sample.attrs.get("effect", "hurt")
        kid.meters[effect] += sample.attrs.get("severity", 1)
        kid.meters["needs_help"] += 1
        kid.memes["fear"] += 1
        out.append("__skin__")
    return out


def _r_need_adult(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.kids():
        if kid.meters["needs_help"] < THRESHOLD:
            continue
        sig = ("need_adult", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        parent = world.get("parent")
        parent.meters["care_work"] += 1
        out.append("__adult__")
    return out


def _r_shared_turn(world: World) -> list[str]:
    tool = world.get("tool")
    if not tool.shared or tool.meters["shared_turns"] < THRESHOLD:
        return []
    sig = ("shared_turn", tool.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["sharing"] += 1
    return ["__share__"]


CAUSAL_RULES = [
    Rule("skin_reacts", "physical", _r_skin_reacts),
    Rule("need_adult", "social", _r_need_adult),
    Rule("shared_turn", "social", _r_shared_turn),
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


def sample_at_risk(sample: SampleKind) -> bool:
    return sample.risky_to_skin


def tool_works(sample: SampleKind, tool: Tool) -> bool:
    return sample.id in tool.protects


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for sample_id, sample in SAMPLES.items():
            for tool_id, tool in TOOLS.items():
                if sample_at_risk(sample) and tool_works(sample, tool):
                    combos.append((theme_id, sample_id, tool_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (3.0 if older else 0.0)
    return older and authority > CURIOSITY_INIT


def predict_skin(world: World) -> dict:
    sim = world.copy()
    kid = sim.get("instigator")
    kid.meters["bare_touch"] += 1
    propagate(sim, narrate=False)
    sample = sim.get("sample")
    effect = sample.attrs.get("effect", "hurt")
    return {
        "harm": kid.meters[effect] >= THRESHOLD,
        "effect": effect,
        "care_work": sim.get("parent").meters["care_work"],
    }


def introduce(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"After lunch, {a.id} and {b.id} turned the room into {theme.scene}. {theme.rig}"
    )
    world.say(f'"{theme.launch_line}" {a.id} said.')


def discover(world: World, b: Entity, theme: Theme, sample: SampleKind) -> None:
    b.memes["curiosity"] += 1
    world.say(
        f"They crawled toward {theme.dark_corner}, where a strange little thing waited: "
        f"{sample.phrase} {sample.where}."
    )
    world.say(
        f'"Maybe it is {theme.target}," {b.id} whispered, leaning close with wide, curious eyes.'
    )


def tempt(world: World, a: Entity, sample: SampleKind) -> None:
    a.memes["curiosity"] += 1
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} reached forward. "I want to touch it," {a.pronoun()} said. '
        f'The tiny mystery pulled at {a.pronoun("possessive")} curiosity.'
    )
    world.say(f"For one bright second, touching it with bare skin felt like the fastest way to know more.")


def warn(world: World, b: Entity, a: Entity, sample: SampleKind, parent: Entity) -> None:
    pred = predict_skin(world)
    b.memes["caution"] += 1
    world.facts["predicted_effect"] = pred["effect"]
    world.facts["predicted_care_work"] = pred["care_work"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.id} shook {b.pronoun('possessive')} head right away."
    world.say(
        f'"Wait," {b.id} said. "{parent.label_word.capitalize()} says we do not touch unknown things '
        f'with our skin first. {sample.danger}."{extra}'
    )


def back_down(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"{a.id} stopped with one finger in the air, then tucked the hand back against "
        f"{a.pronoun('possessive')} shirt."
    )
    world.say(
        f'"You are right," {a.pronoun()} said. "Let\'s ask {parent.label_word} before our mission gets ouchy."'
    )


def touch_sample(world: World, a: Entity, sample: SampleKind) -> None:
    a.meters["bare_touch"] += 1
    propagate(world, narrate=False)
    effect = world.facts.get("predicted_effect", sample.id)
    a.memes["regret"] += 1
    world.say(sample.touch_line.replace("{name}", a.id))
    world.say(sample.hurt_line.replace("{name}", a.id))


def call_parent(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    world.say(f'"{parent.label_word.upper()}!" {b.id} called.')
    world.say(f"{parent.label_word.capitalize()} came quickly and knelt beside them.")


def soothe(world: World, parent: Entity, a: Entity, sample: SampleKind) -> None:
    a.memes["fear"] = 0.0
    a.memes["relief"] += 1
    a.memes["lesson"] += 1
    parent.memes["care"] += 1
    world.say(
        f'{parent.label_word.capitalize()} looked at {a.id}\'s skin and {sample.care_line}.'
    )
    world.say(
        f'"Curious is good," {parent.pronoun()} said softly, "but first we keep your skin safe, and then we investigate."'
    )


def bring_tool(world: World, parent: Entity, tool: Tool) -> None:
    world.say(
        f"Then {parent.label_word} brought {tool.phrase}. {tool.intro}"
    )


def investigate(world: World, a: Entity, b: Entity, tool: Tool, sample: SampleKind) -> None:
    tool_ent = world.get("tool")
    tool_ent.meters["shared_turns"] += 1
    propagate(world, narrate=False)
    world.say(tool.use_line.replace("{sample}", sample.label))
    world.say(tool.share_line.replace("{a}", a.id).replace("{b}", b.id))


def shared_treat(world: World, a: Entity, b: Entity, treat: Treat, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["sharing"] += 1
        kid.memes["joy"] += 1
    world.say(
        f"When the mission was over, they sat by their cardboard controls and shared {treat.phrase}, "
        f"a {treat.color} lollipop that clicked gently against their teeth."
    )
    world.say(
        f"They took turns with the sweet treat just as they had taken turns with the tool, "
        f"and the crew of two felt wiser than before."
    )
    world.say(theme.ending_line)


def tell(
    theme: Theme,
    sample_cfg: SampleKind,
    tool_cfg: Tool,
    treat_cfg: Treat,
    instigator: str = "Nova",
    instigator_gender: str = "girl",
    cautioner: str = "Leo",
    cautioner_gender: str = "boy",
    trait: str = "careful",
    parent_type: str = "mother",
    instigator_age: int = 5,
    cautioner_age: int = 7,
    relation: str = "siblings",
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=instigator,
            kind="character",
            type=instigator_gender,
            role="instigator",
            traits=["curious"],
            age=instigator_age,
            attrs={"relation": relation},
        )
    )
    b = world.add(
        Entity(
            id=cautioner,
            kind="character",
            type=cautioner_gender,
            role="cautioner",
            traits=[trait],
            age=cautioner_age,
            attrs={"relation": relation},
        )
    )
    parent = world.add(
        Entity(id="parent", kind="character", type=parent_type, role="parent", label="the parent")
    )
    sample = world.add(
        Entity(
            id="sample",
            type="sample",
            label=sample_cfg.label,
            risky_to_skin=sample_cfg.risky_to_skin,
            attrs={"effect": sample_cfg.id, "severity": sample_cfg.severity},
        )
    )
    world.add(
        Entity(
            id="tool",
            type="tool",
            label=tool_cfg.label,
            protects_skin=True,
            shared=True,
        )
    )

    a.memes["curiosity"] = CURIOSITY_INIT
    b.memes["caution"] = initial_caution(trait)

    introduce(world, a, b, theme)
    discover(world, b, theme, sample_cfg)

    world.para()
    tempt(world, a, sample_cfg)
    warn(world, b, a, sample_cfg, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, parent)
    else:
        world.say(f'{a.id} could not wait. Before anyone else could stop {a.pronoun("object")}, one finger poked the mystery.')
        world.para()
        touch_sample(world, a, sample_cfg)
        call_parent(world, parent, a, b)
        soothe(world, parent, a, sample_cfg)

    world.para()
    bring_tool(world, parent, tool_cfg)
    investigate(world, a, b, tool_cfg, sample_cfg)
    shared_treat(world, a, b, treat_cfg, theme)

    outcome = "averted" if averted else "ouch"
    world.facts.update(
        theme=theme,
        sample_cfg=sample_cfg,
        tool_cfg=tool_cfg,
        treat_cfg=treat_cfg,
        instigator=a,
        cautioner=b,
        parent=parent,
        relation=relation,
        outcome=outcome,
        averted=averted,
        hurt=not averted,
        shared=True,
    )
    return world


THEMES = {
    "rocket": Theme(
        "rocket",
        "a silver rocket ship",
        "A big blanket became the launch roof, couch cushions became moon rocks, and a laundry basket became the captain's seat.",
        "Crew, prepare for star lift-off!",
        "a tiny moon sample from an unknown world",
        "the dim corner beside the window",
        "crew",
        "Soon the rocket was off again, but now curiosity wore a seat belt.",
    ),
    "moonbase": Theme(
        "moonbase",
        "a humming moon base",
        "A sheet over the table became the base dome, pillows became craters, and a flashlight became the beacon lamp.",
        "Moon base ready!",
        "a tiny sample from a silent crater",
        "the shadow under the table",
        "crew",
        "Their moon base felt brighter because they had learned how explorers think first.",
    ),
    "starship": Theme(
        "starship",
        "a long starship corridor",
        "Chairs became control panels, a scarf became a comet tail, and the rug became a star map under their boots.",
        "Star crew, this way!",
        "a strange thing from the edge of the galaxy",
        "the nook behind the chair",
        "crew",
        "The starship sailed on, carrying two kinder and more careful explorers.",
    ),
}

SAMPLES = {
    "cactus": SampleKind(
        "cactus",
        "little cactus",
        "a little green cactus in a blue pot",
        "on the sill like a spiky alien planet",
        "Its sharp points can poke skin.",
        "{name} brushed one fingertip against the little cactus.",
        "At once {name} pulled the hand back. The skin stung, and tiny eyes filled with tears.",
        "washed the fingertip, checked for little pokes, and kissed the sore spot",
        severity=1,
        risky_to_skin=True,
        tags={"skin", "plant", "safe_touch"},
    ),
    "nettle": SampleKind(
        "nettle",
        "nettle leaf",
        "a jagged nettle leaf",
        "in a jar by the back door like a curled green meteor",
        "Some leaves can make skin itchy.",
        "{name} tapped the leaf before thinking.",
        "In a blink {name}'s skin began to itch, and {name} rubbed the finger against a shirt.",
        "rinsed the hand with cool water and helped the itchy feeling settle down",
        severity=1,
        risky_to_skin=True,
        tags={"skin", "plant", "itchy"},
    ),
    "glue": SampleKind(
        "glue",
        "glitter glue blob",
        "a blob of glitter glue",
        "on a tray like silver space slime",
        "Sticky things can cling to skin and make a mess.",
        "{name} pressed a finger into the shiny blob.",
        "The blob stuck fast. {name} stared at the glitter on the skin and made a worried little gasp.",
        "used warm water and a washcloth until the sticky glitter slid away",
        severity=1,
        risky_to_skin=True,
        tags={"skin", "sticky", "clean_up"},
    ),
    "stone": SampleKind(
        "stone",
        "smooth stone",
        "a smooth gray stone",
        "by the flowerpot like a quiet moon pebble",
        "It would not hurt skin at all.",
        "{name} touched the smooth stone.",
        "Nothing happened.",
        "smiled because there was nothing to fix",
        severity=0,
        risky_to_skin=False,
        tags={"stone"},
    ),
}

TOOLS = {
    "gloves": Tool(
        "gloves",
        "gloves",
        "one pair of soft garden gloves",
        {"cactus", "nettle", "glue"},
        "They looked like proper explorer gloves.",
        "With the gloves on, they gently moved the {sample} and looked at it from every side.",
        "{a} wore the gloves first, then passed them to {b} for the next turn.",
        tags={"gloves", "sharing"},
    ),
    "tongs": Tool(
        "tongs",
        "tongs",
        "a pair of kitchen tongs",
        {"cactus", "nettle", "glue"},
        "The shiny ends kept fingers away from trouble.",
        "Using the tongs, they lifted the {sample} just enough to peer underneath without touching it.",
        "{a} held the tongs, then {b} took a careful turn with the same tool.",
        tags={"tongs", "sharing"},
    ),
    "jar": Tool(
        "jar",
        "clear jar",
        "a clear jar with a lid",
        {"nettle", "glue"},
        "The clear sides let them look closely while keeping skin outside.",
        "They settled the {sample} into the jar and bent close to study its shapes and colors.",
        "{a} looked through one side, and {b} looked through the other, sharing the discovery together.",
        tags={"jar", "sharing"},
    ),
    "magnifier": Tool(
        "magnifier",
        "magnifying glass",
        "a magnifying glass",
        set(),
        "It made little things look bigger, but it did not protect skin.",
        "They looked at the {sample}.",
        "{a} and {b} passed it back and forth.",
        tags={"magnifier"},
    ),
}

TREATS = {
    "cherry": Treat("cherry", "cherry lollipop", "one cherry lollipop", "red", tags={"lollipop"}),
    "lemon": Treat("lemon", "lemon lollipop", "one lemon lollipop", "yellow", tags={"lollipop"}),
    "grape": Treat("grape", "grape lollipop", "one grape lollipop", "purple", tags={"lollipop"}),
}

GIRL_NAMES = ["Nova", "Lily", "Mia", "Zoe", "Ava", "Ella", "Nora"]
BOY_NAMES = ["Leo", "Max", "Sam", "Finn", "Theo", "Eli", "Jack"]
TRAITS = ["careful", "cautious", "gentle", "patient", "thoughtful", "calm"]


@dataclass
class StoryParams:
    theme: str
    sample: str
    tool: str
    treat: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 5
    cautioner_age: int = 7
    seed: Optional[int] = None


KNOWLEDGE = {
    "skin": [
        (
            "What is skin?",
            "Skin is the soft covering on the outside of your body. It helps protect you, so it is important to keep it safe.",
        )
    ],
    "plant": [
        (
            "Why should you be careful with unknown plants?",
            "Some plants can poke, sting, or make your skin itchy. It is smart to ask a grown-up before touching one.",
        )
    ],
    "itchy": [
        (
            "What does itchy skin feel like?",
            "Itchy skin feels tickly and uncomfortable, and it makes you want to scratch. Washing and getting help can make it feel better.",
        )
    ],
    "sticky": [
        (
            "Why can sticky glue be messy?",
            "Sticky glue clings to skin and other things, so it can be hard to get off. That is why it helps to use tools and clean up carefully.",
        )
    ],
    "safe_touch": [
        (
            "What should you do before touching something strange?",
            "Stop and look first, then ask a grown-up if you are not sure. Safe explorers use their eyes and tools before their hands.",
        )
    ],
    "gloves": [
        (
            "What do gloves do?",
            "Gloves cover your hands so your skin does not touch the thing directly. They can help protect you from pokes, itchiness, and messes.",
        )
    ],
    "tongs": [
        (
            "What are tongs for?",
            "Tongs are tools that help you pick things up without using your fingers. They are useful when you want to keep your skin away from something.",
        )
    ],
    "jar": [
        (
            "Why use a clear jar to look at something?",
            "A clear jar lets you see the thing while keeping it away from your skin. That means you can stay curious and still be safe.",
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means taking turns or letting someone else use something too. It helps everyone feel included and cared for.",
        )
    ],
    "lollipop": [
        (
            "What is a lollipop?",
            "A lollipop is a sweet candy on a stick. It is something people can enjoy as a treat.",
        )
    ],
}
KNOWLEDGE_ORDER = ["skin", "plant", "itchy", "sticky", "safe_touch", "gloves", "tongs", "jar", "sharing", "lollipop"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    theme = f["theme"]
    sample = f["sample_cfg"]
    tool = f["tool_cfg"]
    treat = f["treat_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short space-adventure story for a 3-to-5-year-old that includes the words "skin" '
        f'and "{treat.label}". Use curiosity and sharing in the plot.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle story where {a.id} and {b.id} are pretending to be space explorers, "
            f"{a.id} wants to touch {sample.phrase}, but a wiser older child stops the bare-skin touch and they investigate safely with {tool.phrase}.",
            f"Write a story where curiosity leads to caution instead of an accident, and the children end by sharing a {treat.label}.",
        ]
    return [
        base,
        f"Tell a space-adventure story where {a.id} touches {sample.phrase} too quickly, a grown-up helps, and then the children use {tool.phrase} to explore the mystery the safe way.",
        f"Write a child-facing story about curiosity, safe skin, and sharing, ending with the children taking turns and sharing a {treat.label}.",
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    theme = f["theme"]
    sample = f["sample_cfg"]
    tool = f["tool_cfg"]
    treat = f["treat_cfg"]
    pair = pair_noun(a, b, f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who were pretending to be a space crew. Their {parent.label_word} helped them when the mission became uncertain.",
        ),
        (
            "What were the children pretending to do?",
            f"They had turned the room into {theme.scene} and were exploring for a mystery sample. The game made the ordinary corner feel like a faraway place.",
        ),
        (
            f"Why did {a.id} want to touch the {sample.label}?",
            f"{a.id} was curious and wanted to learn about it quickly. In the story, touching it with bare skin seemed like the fastest way to know more.",
        ),
        (
            f"What warning did {b.id} give?",
            f"{b.id} warned that they should not touch unknown things with their skin first. The warning was about staying curious in a safe way instead of rushing in.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What did {a.id} do after the warning?",
                f"{a.id} stopped and asked for help instead of touching the sample. That changed the whole mission, because they moved from risky curiosity to careful curiosity.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {a.id} touched the {sample.label}?",
                f"{a.id}'s skin was bothered right away, so the pretend mission turned into a real problem. {parent.label_word.capitalize()} had to help before the children could keep exploring.",
            )
        )
        qa.append(
            (
                f"How did {parent.label_word} help?",
                f"{parent.label_word.capitalize()} helped {a.id} feel better and reminded the children to protect skin before investigating. The grown-up turned the scary moment into a calmer, safer plan.",
            )
        )
    qa.append(
        (
            "How did they solve the problem?",
            f"They used {tool.phrase} so they could study the sample without bare skin touching it. Then they shared turns, which let curiosity and safety work together.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the children sharing {treat.phrase} and feeling wiser. The last image shows that they learned to share both tools and treats after the mission.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"skin", "sharing", "lollipop"} | set(f["sample_cfg"].tags) | set(f["tool_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [n for n, on in (("risky_to_skin", e.risky_to_skin), ("protects_skin", e.protects_skin), ("shared", e.shared)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("rocket", "cactus", "gloves", "cherry", "Nova", "girl", "Leo", "boy", "mother", "careful", relation="siblings", instigator_age=5, cautioner_age=7),
    StoryParams("moonbase", "nettle", "jar", "lemon", "Max", "boy", "Ava", "girl", "father", "gentle", relation="friends", instigator_age=6, cautioner_age=6),
    StoryParams("starship", "glue", "tongs", "grape", "Ella", "girl", "Finn", "boy", "mother", "patient", relation="siblings", instigator_age=6, cautioner_age=8),
]


def explain_rejection(sample: SampleKind, tool: Tool) -> str:
    if not sample.risky_to_skin:
        return (
            f"(No story: {sample.phrase} is not risky to skin, so there is no honest warning and no need for a careful rescue. "
            f"Pick a sample like cactus, nettle, or glue.)"
        )
    return (
        f"(No story: {tool.phrase} does not really protect skin from {sample.label}. "
        f"The fix must keep hands safely away from the sample.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "ouch"


ASP_RULES = r"""
risky(S) :- sample(S), risky_to_skin(S).
works(S, T) :- tool(T), protects(T, S).
valid(Th, S, T) :- theme(Th), risky(S), works(S, T).

cautious_now(Trait) :- trait(Trait), is_cautious(Trait).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_sibling :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(3) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sibling, authority(A), curiosity_init(CI), A > CI.

outcome(averted) :- averted.
outcome(ouch) :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for sid, s in SAMPLES.items():
        lines.append(asp.fact("sample", sid))
        if s.risky_to_skin:
            lines.append(asp.fact("risky_to_skin", sid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for sid in sorted(t.protects):
            lines.append(asp.fact("protects", tid, sid))
    for tr in sorted(TRAITS):
        lines.append(asp.fact("trait", tr))
    for tr in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", tr))
    lines.append(asp.fact("curiosity_init", int(CURIOSITY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny space adventure about curiosity, skin safety, sharing, and a lollipop."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--sample", choices=SAMPLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.sample and not SAMPLES[args.sample].risky_to_skin:
        tool = TOOLS[args.tool] if args.tool else next(iter(TOOLS.values()))
        raise StoryError(explain_rejection(SAMPLES[args.sample], tool))
    if args.sample and args.tool:
        sample = SAMPLES[args.sample]
        tool = TOOLS[args.tool]
        if not (sample_at_risk(sample) and tool_works(sample, tool)):
            raise StoryError(explain_rejection(sample, tool))

    combos = [
        c
        for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.sample is None or c[1] == args.sample)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, sample, tool = rng.choice(sorted(combos))
    treat = args.treat or rng.choice(sorted(TREATS))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7, 8], 2)
    return StoryParams(
        theme,
        sample,
        tool,
        treat,
        instigator,
        ig,
        cautioner,
        cg,
        parent,
        trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        THEMES[params.theme],
        SAMPLES[params.sample],
        TOOLS[params.tool],
        TREATS[params.treat],
        params.instigator,
        params.instigator_gender,
        params.cautioner,
        params.cautioner_gender,
        params.trait,
        params.parent,
        params.instigator_age,
        params.cautioner_age,
        params.relation,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
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
        print(f"{len(combos)} compatible (theme, sample, tool) combos:\n")
        for theme, sample, tool in combos:
            print(f"  {theme:9} {sample:8} {tool}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.sample} with {p.tool} ({p.theme}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
