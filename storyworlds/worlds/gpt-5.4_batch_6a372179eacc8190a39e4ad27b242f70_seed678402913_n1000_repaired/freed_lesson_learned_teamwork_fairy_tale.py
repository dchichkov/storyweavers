#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/freed_lesson_learned_teamwork_fairy_tale.py
======================================================================

A standalone story world for gentle fairy-tale stories about two small helpers
working together to free a trapped magical friend. The core lesson is simple:
one brave try is not always enough, but shared effort can do what lonely effort
cannot.

The world models:
- typed entities with physical meters and emotional memes
- a tiny causal rule system
- a reasonableness gate over valid helper/obstacle/tool combinations
- an inline ASP twin for parity checks

Run it
------
    python storyworlds/worlds/gpt-5.4/freed_lesson_learned_teamwork_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/freed_lesson_learned_teamwork_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/freed_lesson_learned_teamwork_fairy_tale.py --qa
    python storyworlds/worlds/gpt-5.4/freed_lesson_learned_teamwork_fairy_tale.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives one level deeper than most worlds, so we add storyworlds/ itself.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # character | creature | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "fairy", "pixie", "witch", "queen"}
        male = {"boy", "prince", "elf", "gnome", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    closing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FriendKind:
    id: str
    label: str
    phrase: str
    cry: str
    thanks: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    requires: tuple[str, str] = ("", "")
    danger_text: str = ""
    release_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperKind:
    id: str
    type: str
    title: str
    talent: str
    action: str
    solo_fail: str
    join_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    aids: str
    use_text: str
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


def _r_distress(world: World) -> list[str]:
    out: list[str] = []
    friend = world.get("friend")
    obstacle = world.get("obstacle")
    if friend.meters["trapped"] >= THRESHOLD and obstacle.meters["closed"] >= THRESHOLD:
        sig = ("distress",)
        if sig not in world.fired:
            world.fired.add(sig)
            friend.memes["fear"] += 1
            out.append("__distress__")
    return out


def _r_free(world: World) -> list[str]:
    out: list[str] = []
    friend = world.get("friend")
    obstacle = world.get("obstacle")
    helper1 = world.get("helper1")
    helper2 = world.get("helper2")
    need_a, need_b = obstacle.attrs["requires"]
    skills = {helper1.attrs["talent"], helper2.attrs["talent"]}
    tool = world.get("tool")
    aided = tool.attrs["aids"]
    if obstacle.meters["closed"] < THRESHOLD:
        return out
    if need_a in skills and need_b in skills and aided in skills:
        sig = ("freed",)
        if sig not in world.fired:
            world.fired.add(sig)
            obstacle.meters["closed"] = 0.0
            friend.meters["trapped"] = 0.0
            friend.memes["fear"] = 0.0
            friend.memes["relief"] += 1
            helper1.memes["pride"] += 1
            helper2.memes["pride"] += 1
            helper1.memes["care"] += 1
            helper2.memes["care"] += 1
            helper1.memes["teamwork"] += 1
            helper2.memes["teamwork"] += 1
            out.append("__freed__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="distress", tag="emotional", apply=_r_distress),
    Rule(name="freed", tag="physical", apply=_r_free),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for bit in produced:
            if bit == "__distress__":
                friend = world.get("friend")
                world.say(
                    f"The sound of {friend.label} trembling made the little clearing feel smaller."
                )
            elif bit == "__freed__":
                friend = world.get("friend")
                obstacle = world.get("obstacle")
                world.say(obstacle.attrs["release_text"])
                world.say(f"At last, {friend.label} was freed.")
    return produced


SETTINGS = {
    "glade": Setting(
        id="glade",
        place="the silver glade",
        opening="In the silver glade, moonflowers nodded beside a brook that talked to the stones.",
        closing="The moonflowers shone softly, as if they too were pleased."
    ),
    "hill": Setting(
        id="hill",
        place="the lantern hill",
        opening="On lantern hill, fireflies drifted above the grass like tiny floating stars.",
        closing="The lanterns in the windows seemed to wink across the valley."
    ),
    "orchard": Setting(
        id="orchard",
        place="the pearled orchard",
        opening="In the pearled orchard, dew hung on every leaf like little glass beads.",
        closing="Even the old trees looked gentler in the evening glow."
    ),
}

FRIENDS = {
    "bird": FriendKind(
        id="bird",
        label="a golden bird",
        phrase="a golden bird with a frightened heartbeat",
        cry='"Please help me," chirped the little bird.',
        thanks='"You listened to one another, and that is why I am safe," sang the golden bird.'
    ),
    "fawn": FriendKind(
        id="fawn",
        label="a silver fawn",
        phrase="a silver fawn with bright wet eyes",
        cry='"Please, please," whispered the small fawn.',
        thanks='"Two kind hearts are stronger than one rushing heart," said the silver fawn.'
    ),
    "moth": FriendKind(
        id="moth",
        label="a moon-moth",
        phrase="a moon-moth with soft shining wings",
        cry='"I cannot get loose," sighed the moon-moth.',
        thanks='"Your hands worked together like a song," hummed the moon-moth.'
    ),
}

OBSTACLES = {
    "thorn_gate": Obstacle(
        id="thorn_gate",
        label="thorn gate",
        phrase="a round gate of woven thorns",
        requires=("lift", "untie"),
        danger_text="The thorns were tight and twisty, too strong to simply pull apart.",
        release_text="The thorn gate loosened, then opened with a soft leafy sigh."
    ),
    "vine_knot": Obstacle(
        id="vine_knot",
        label="vine knot",
        phrase="a thick knot of sleepy vines",
        requires=("comb", "untie"),
        danger_text="The vines were looped in so many sleepy curls that one tug only made them cling harder.",
        release_text="The vine knot slipped apart and fell into a harmless green heap."
    ),
    "crystal_latch": Obstacle(
        id="crystal_latch",
        label="crystal latch",
        phrase="a crystal latch caught under a fallen branch",
        requires=("lift", "reach"),
        danger_text="The latch could not move while the branch pressed on it, and it sat too deep for one pair of hands.",
        release_text="The branch rose, the latch clicked, and the little prison came gently open."
    ),
}

HELPERS = {
    "elf": HelperKind(
        id="elf",
        type="elf",
        title="a quick little elf",
        talent="untie",
        action="nimble fingers for knots",
        solo_fail="His nimble fingers found the knot, but without room to move, he could not free it alone.",
        join_text="worked carefully at the tricky loops"
    ),
    "troll": HelperKind(
        id="troll",
        type="troll",
        title="a sturdy moss-troll",
        talent="lift",
        action="steady strength for lifting",
        solo_fail="His strong arms could lift the heavy part a little, but he could not finish the job alone.",
        join_text="braced both feet and lifted with patient strength"
    ),
    "fairy": HelperKind(
        id="fairy",
        type="fairy",
        title="a bright-winged fairy",
        talent="reach",
        action="small careful hands that could reach tiny places",
        solo_fail="Her small hands could reach the hidden place, but she could not hold the weight back alone.",
        join_text="slipped into the narrow gap with careful hands"
    ),
    "mouse": HelperKind(
        id="mouse",
        type="mouse",
        title="a brave field mouse",
        talent="comb",
        action="whiskers and paws for teasing tangles apart",
        solo_fail="His tiny paws teased at the tangle, but each loosened curl only sprang back again.",
        join_text="combed through the tangled strands a little at a time"
    ),
}

TOOLS = {
    "ribbon": Tool(
        id="ribbon",
        label="silk ribbon",
        phrase="a silk ribbon from the wishing tree",
        aids="untie",
        use_text="The ribbon held the loosest loops apart so the knot would not tighten again."
    ),
    "branch": Tool(
        id="branch",
        label="forked branch",
        phrase="a forked branch smooth with old bark",
        aids="lift",
        use_text="The forked branch gave the heavy part something firm to rest on."
    ),
    "needle": Tool(
        id="needle",
        label="dew needle",
        phrase="a dew needle as thin as a raindrop",
        aids="reach",
        use_text="The dew needle slipped where fingers could barely fit."
    ),
    "comb": Tool(
        id="comb",
        label="petal comb",
        phrase="a petal comb with soft little teeth",
        aids="comb",
        use_text="The petal comb teased the snarled parts apart without tearing them."
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Nella", "Poppy", "Ivy"]
BOY_NAMES = ["Oren", "Finn", "Bram", "Nico", "Rowan", "Tobin"]


def needs_match(obstacle: Obstacle, helper1: HelperKind, helper2: HelperKind, tool: Tool) -> bool:
    skills = {helper1.talent, helper2.talent}
    reqs = set(obstacle.requires)
    if helper1.id == helper2.id:
        return False
    if skills != reqs:
        return False
    if tool.aids not in reqs:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id in SETTINGS:
        for friend_id in FRIENDS:
            for obstacle_id, obstacle in OBSTACLES.items():
                for helper1_id, helper1 in HELPERS.items():
                    for helper2_id, helper2 in HELPERS.items():
                        for tool_id, tool in TOOLS.items():
                            if needs_match(obstacle, helper1, helper2, tool):
                                combos.append(
                                    (setting_id, friend_id, obstacle_id, helper1_id, helper2_id, tool_id)
                                )
    return sorted(set(combos))


@dataclass
class StoryParams:
    setting: str
    friend: str
    obstacle: str
    helper1_kind: str
    helper2_kind: str
    tool: str
    helper1_name: str
    helper2_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="glade",
        friend="bird",
        obstacle="thorn_gate",
        helper1_kind="troll",
        helper2_kind="elf",
        tool="ribbon",
        helper1_name="Bram",
        helper2_name="Lina",
    ),
    StoryParams(
        setting="hill",
        friend="moth",
        obstacle="crystal_latch",
        helper1_kind="fairy",
        helper2_kind="troll",
        tool="branch",
        helper1_name="Mira",
        helper2_name="Rowan",
    ),
    StoryParams(
        setting="orchard",
        friend="fawn",
        obstacle="vine_knot",
        helper1_kind="mouse",
        helper2_kind="elf",
        tool="comb",
        helper1_name="Tobin",
        helper2_name="Nella",
    ),
]


def helper_name_pool(kind: HelperKind) -> list[str]:
    if kind.type == "fairy":
        return GIRL_NAMES
    if kind.type in {"elf", "troll", "mouse"}:
        return BOY_NAMES + GIRL_NAMES
    return GIRL_NAMES + BOY_NAMES


def explain_rejection(obstacle: Obstacle, helper1: HelperKind, helper2: HelperKind, tool: Tool) -> str:
    if helper1.id == helper2.id:
        return "(No story: the two helpers must bring different talents, not be the very same kind.)"
    reqs = sorted(set(obstacle.requires))
    skills = sorted({helper1.talent, helper2.talent})
    if set(skills) != set(reqs):
        return (
            f"(No story: {obstacle.label} needs {reqs}, but these helpers only bring {skills}. "
            f"The rescue must honestly require teamwork.)"
        )
    if tool.aids not in set(obstacle.requires):
        return (
            f"(No story: the {tool.label} helps with {tool.aids}, but {obstacle.label} needs "
            f"{sorted(set(obstacle.requires))}. Pick a tool that truly helps the rescue.)"
        )
    return "(No story: this combination does not form a sensible rescue.)"


def introduce(world: World, helper1: Entity, helper2: Entity, friend: Entity) -> None:
    world.say("Once, under a kindly sky, two small friends walked together through the fairy wood.")
    world.say(
        f"One was {helper1.id}, {helper1.attrs['title']}, and the other was {helper2.id}, {helper2.attrs['title']}."
    )
    world.say(world.setting.opening)
    world.say(
        f"Then they heard a worried sound and found {friend.phrase} in trouble."
    )


def reveal_trouble(world: World, friend_cfg: FriendKind, obstacle_cfg: Obstacle, friend: Entity) -> None:
    world.say(
        f"{friend_cfg.cry} {friend.label.capitalize()} was caught behind {obstacle_cfg.phrase}."
    )
    world.say(obstacle_cfg.danger_text)
    friend.meters["trapped"] += 1
    world.get("obstacle").meters["closed"] += 1
    propagate(world, narrate=True)


def solo_attempts(world: World, helper1: Entity, helper2: Entity, obstacle_cfg: Obstacle) -> None:
    world.say(
        f'"I will try first," said {helper1.id}, because {helper1.pronoun()} was eager to help.'
    )
    helper1.memes["effort"] += 1
    world.say(helper1.attrs["solo_fail"])
    world.say(
        f'Then {helper2.id} took a turn, hoping {helper2.pronoun("possessive")} own gift would be enough.'
    )
    helper2.memes["effort"] += 1
    world.say(helper2.attrs["solo_fail"])
    world.say(
        f"They stepped back from the {obstacle_cfg.label} and looked at one another with wiser eyes."
    )


def learn_and_plan(world: World, helper1: Entity, helper2: Entity, tool: Entity) -> None:
    helper1.memes["humility"] += 1
    helper2.memes["humility"] += 1
    world.say(
        f'"Your gift is not my gift," said {helper1.id}. "Maybe that is exactly what we need."'
    )
    world.say(
        f'{helper2.id} nodded. Together they picked up {tool.phrase}. {tool.attrs["use_text"]}'
    )


def join_effort(world: World, helper1: Entity, helper2: Entity, obstacle_cfg: Obstacle) -> None:
    helper1.memes["effort"] += 1
    helper2.memes["effort"] += 1
    world.say(
        f"{helper1.id} {helper1.attrs['join_text']}, while {helper2.id} {helper2.attrs['join_text']}."
    )
    world.say(
        f"Neither hurried. They listened to the problem, and they listened to each other."
    )
    world.get("tool").meters["used"] += 1
    propagate(world, narrate=True)
    if world.get("friend").meters["trapped"] >= THRESHOLD:
        raise StoryError("(Story logic failed: the helpers worked together but the friend was not freed.)")


def ending(world: World, friend_cfg: FriendKind, helper1: Entity, helper2: Entity) -> None:
    friend = world.get("friend")
    world.say(
        f"{friend.label.capitalize()} fluttered and stretched, then came close to thank them."
    )
    world.say(friend_cfg.thanks)
    world.say(
        f"{helper1.id} and {helper2.id} walked home more slowly than before, carrying a new thought between them: "
        f"small gifts grow strong when kind hearts use them together."
    )
    world.say(world.setting.closing)


def tell(
    setting: Setting,
    friend_cfg: FriendKind,
    obstacle_cfg: Obstacle,
    helper1_cfg: HelperKind,
    helper2_cfg: HelperKind,
    tool_cfg: Tool,
    helper1_name: str,
    helper2_name: str,
) -> World:
    world = World(setting=setting)
    helper1 = world.add(
        Entity(
            id=helper1_name,
            kind="character",
            type=helper1_cfg.type,
            label=helper1_name,
            role="helper",
            attrs={
                "talent": helper1_cfg.talent,
                "title": helper1_cfg.title,
                "solo_fail": helper1_cfg.solo_fail,
                "join_text": helper1_cfg.join_text,
            },
            tags=set(helper1_cfg.tags),
        )
    )
    helper2 = world.add(
        Entity(
            id=helper2_name,
            kind="character",
            type=helper2_cfg.type,
            label=helper2_name,
            role="helper",
            attrs={
                "talent": helper2_cfg.talent,
                "title": helper2_cfg.title,
                "solo_fail": helper2_cfg.solo_fail,
                "join_text": helper2_cfg.join_text,
            },
            tags=set(helper2_cfg.tags),
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            kind="creature",
            type="creature",
            label=friend_cfg.label,
            phrase=friend_cfg.phrase,
            role="friend",
            tags=set(friend_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="obstacle",
            kind="thing",
            type="obstacle",
            label=obstacle_cfg.label,
            phrase=obstacle_cfg.phrase,
            role="obstacle",
            attrs={
                "requires": obstacle_cfg.requires,
                "release_text": obstacle_cfg.release_text,
            },
            tags=set(obstacle_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="tool",
            kind="thing",
            type="tool",
            label=tool_cfg.label,
            phrase=tool_cfg.phrase,
            role="tool",
            attrs={
                "aids": tool_cfg.aids,
                "use_text": tool_cfg.use_text,
            },
            tags=set(tool_cfg.tags),
        )
    )

    introduce(world, helper1, helper2, friend)
    reveal_trouble(world, friend_cfg, obstacle_cfg, friend)

    world.para()
    solo_attempts(world, helper1, helper2, obstacle_cfg)

    world.para()
    learn_and_plan(world, helper1, helper2, world.get("tool"))
    join_effort(world, helper1, helper2, obstacle_cfg)

    world.para()
    ending(world, friend_cfg, helper1, helper2)

    world.facts.update(
        setting=setting,
        friend_cfg=friend_cfg,
        obstacle_cfg=obstacle_cfg,
        helper1_cfg=helper1_cfg,
        helper2_cfg=helper2_cfg,
        tool_cfg=tool_cfg,
        helper1=helper1,
        helper2=helper2,
        friend=friend,
        obstacle=world.get("obstacle"),
        tool=world.get("tool"),
        outcome="freed" if friend.meters["trapped"] < THRESHOLD else "stuck",
        lesson="teamwork",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    helper1 = f["helper1"]
    helper2 = f["helper2"]
    friend_cfg = f["friend_cfg"]
    obstacle_cfg = f["obstacle_cfg"]
    return [
        'Write a fairy tale for a 3-to-5-year-old that includes the word "freed" and teaches a lesson about teamwork.',
        f"Tell a gentle fairy tale where {helper1.id} and {helper2.id} find {friend_cfg.label} trapped by a {obstacle_cfg.label} and learn that helping together works better than helping alone.",
        f"Write a small magical rescue story with a clear lesson learned: two different gifts must be joined to set {friend_cfg.label} free.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    helper1 = f["helper1"]
    helper2 = f["helper2"]
    friend_cfg = f["friend_cfg"]
    obstacle_cfg = f["obstacle_cfg"]
    tool_cfg = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {helper1.id} and {helper2.id}, two small friends in a fairy wood, and {friend_cfg.label} whom they found in trouble."
        ),
        (
            f"Why did {friend_cfg.label} need help?",
            f"{friend_cfg.label.capitalize()} was trapped behind {obstacle_cfg.phrase}. The problem was too tricky for one quick tug, so help had to be careful and wise."
        ),
        (
            "Did one helper solve the problem alone?",
            f"No. Each helper tried alone first, but one gift by itself was not enough. Their failure taught them to stop rushing and make a plan together."
        ),
        (
            f"How was {friend_cfg.label} freed?",
            f"{helper1.id} and {helper2.id} worked together and used {tool_cfg.phrase}. One helper did the part they were best at, and the other finished the part that needed a different talent."
        ),
        (
            "What lesson did they learn?",
            "They learned that teamwork can solve a problem that one person cannot solve alone. Listening to each other mattered just as much as being brave."
        ),
    ]
    return qa


KNOWLEDGE = {
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help each other on the same job. They share their different strengths so the job becomes easier and better."
        )
    ],
    "fairy": [
        (
            "What is a fairy in a fairy tale?",
            "A fairy is a tiny magical person who often has wings and helps or guides others in stories."
        )
    ],
    "elf": [
        (
            "What is an elf in a fairy tale?",
            "An elf is a small magical woodland person. Elves are often shown as quick, careful, and clever."
        )
    ],
    "troll": [
        (
            "What is a troll in a gentle fairy tale?",
            "A troll is a magical creature that can be large or strong. In a gentle tale, a troll can be kind and helpful."
        )
    ],
    "mouse": [
        (
            "Why can a small mouse help in a story?",
            "A small mouse can fit into tiny places and work carefully. Sometimes little helpers can do things bigger helpers cannot."
        )
    ],
    "freed": [
        (
            "What does freed mean?",
            "Freed means someone was stuck or trapped before, and then they were let out. It means they became safe to move again."
        )
    ],
}
KNOWLEDGE_ORDER = ["teamwork", "freed", "fairy", "elf", "troll", "mouse"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"teamwork", "freed", world.facts["helper1_cfg"].id, world.facts["helper2_cfg"].id}
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
different(H1, H2) :- helper(H1), helper(H2), H1 != H2.
has_skill(H, S) :- helper_skill(H, S).
needs(O, S) :- obstacle_req(O, S).

covers(O, H1, H2) :- obstacle(O), different(H1, H2),
                     needs(O, S1), needs(O, S2),
                     has_skill(H1, S1), has_skill(H2, S2), S1 != S2.

covers(O, H1, H2) :- obstacle(O), different(H1, H2),
                     needs(O, S1), needs(O, S2),
                     has_skill(H1, S2), has_skill(H2, S1), S1 != S2.

tool_helps(O, T) :- obstacle(O), tool(T), obstacle_req(O, S), tool_aids(T, S).

valid(Se, Fr, O, H1, H2, T) :- setting(Se), friend(Fr), obstacle(O),
                               helper(H1), helper(H2), tool(T),
                               different(H1, H2), covers(O, H1, H2), tool_helps(O, T).

outcome(freed) :- chosen_obstacle(O), chosen_helper1(H1), chosen_helper2(H2), chosen_tool(T),
                  different(H1, H2), covers(O, H1, H2), tool_helps(O, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for friend_id in FRIENDS:
        lines.append(asp.fact("friend", friend_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        for req in obstacle.requires:
            lines.append(asp.fact("obstacle_req", obstacle_id, req))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("helper_skill", helper_id, helper.talent))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("tool_aids", tool_id, tool.aids))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/6."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_helper1", params.helper1_kind),
            asp.fact("chosen_helper2", params.helper2_kind),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "invalid"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: two helpers free a trapped magical friend by working together."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--helper1-kind", choices=HELPERS)
    ap.add_argument("--helper2-kind", choices=HELPERS)
    ap.add_argument("--tool", choices=TOOLS)
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
    if args.helper1_kind and args.helper2_kind and args.helper1_kind == args.helper2_kind:
        raise StoryError("(No story: the two helpers must be different kinds so teamwork matters.)")
    if args.obstacle and args.helper1_kind and args.helper2_kind and args.tool:
        obstacle = OBSTACLES[args.obstacle]
        helper1 = HELPERS[args.helper1_kind]
        helper2 = HELPERS[args.helper2_kind]
        tool = TOOLS[args.tool]
        if not needs_match(obstacle, helper1, helper2, tool):
            raise StoryError(explain_rejection(obstacle, helper1, helper2, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.friend is None or combo[1] == args.friend)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.helper1_kind is None or combo[3] == args.helper1_kind)
        and (args.helper2_kind is None or combo[4] == args.helper2_kind)
        and (args.tool is None or combo[5] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, friend_id, obstacle_id, helper1_id, helper2_id, tool_id = rng.choice(sorted(combos))
    helper1_cfg = HELPERS[helper1_id]
    helper2_cfg = HELPERS[helper2_id]
    helper1_name = rng.choice(helper_name_pool(helper1_cfg))
    helper2_name = rng.choice([n for n in helper_name_pool(helper2_cfg) if n != helper1_name])
    return StoryParams(
        setting=setting_id,
        friend=friend_id,
        obstacle=obstacle_id,
        helper1_kind=helper1_id,
        helper2_kind=helper2_id,
        tool=tool_id,
        helper1_name=helper1_name,
        helper2_name=helper2_name,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        friend_cfg = FRIENDS[params.friend]
        obstacle_cfg = OBSTACLES[params.obstacle]
        helper1_cfg = HELPERS[params.helper1_kind]
        helper2_cfg = HELPERS[params.helper2_kind]
        tool_cfg = TOOLS[params.tool]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from err

    if not needs_match(obstacle_cfg, helper1_cfg, helper2_cfg, tool_cfg):
        raise StoryError(explain_rejection(obstacle_cfg, helper1_cfg, helper2_cfg, tool_cfg))

    world = tell(
        setting=setting,
        friend_cfg=friend_cfg,
        obstacle_cfg=obstacle_cfg,
        helper1_cfg=helper1_cfg,
        helper2_cfg=helper2_cfg,
        tool_cfg=tool_cfg,
        helper1_name=params.helper1_name,
        helper2_name=params.helper2_name,
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
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    mismatches = 0
    for params in cases:
        py_outcome = "freed" if needs_match(
            OBSTACLES[params.obstacle],
            HELPERS[params.helper1_kind],
            HELPERS[params.helper2_kind],
            TOOLS[params.tool],
        ) else "invalid"
        asp_result = asp_outcome(params)
        if py_outcome != asp_result:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/6.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, friend, obstacle, helper1, helper2, tool) combos:\n")
        for combo in combos:
            print("  " + "  ".join(combo))
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
            header = (
                f"### {p.helper1_name} and {p.helper2_name}: {p.friend} in {p.obstacle} "
                f"({p.setting}, {p.tool})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
