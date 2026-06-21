#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/clutch_ball_dim_annual_problem_solving_bravery.py
=============================================================================

A small fable-style storyworld about a young forest animal carrying a round
festival lantern to an annual hilltop lighting. On the way, one concrete problem
makes the lantern go dim or the path feel dangerous. The child must be brave,
solve the problem with the right tool, and arrive with a changed ending image.

Seed words intentionally included in this world:
- clutch
- ball-dim
- annual

Run it
------
python storyworlds/worlds/gpt-5.4/clutch_ball_dim_annual_problem_solving_bravery.py
python storyworlds/worlds/gpt-5.4/clutch_ball_dim_annual_problem_solving_bravery.py --problem wind_gust
python storyworlds/worlds/gpt-5.4/clutch_ball_dim_annual_problem_solving_bravery.py --tool counting_song
python storyworlds/worlds/gpt-5.4/clutch_ball_dim_annual_problem_solving_bravery.py --all
python storyworlds/worlds/gpt-5.4/clutch_ball_dim_annual_problem_solving_bravery.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/clutch_ball_dim_annual_problem_solving_bravery.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "doe"}
        male = {"boy", "father", "buck"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Festival:
    id: str
    name: str
    place: str
    closing: str
    signal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LanternKind:
    id: str
    label: str
    phrase: str
    glow: str
    dims_to: str
    repair: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    place: str
    hazard: str
    needs: set[str]
    damage: str
    fear: int
    line: str
    fix_result: str
    failure: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    solves: set[str]
    sense: int
    action: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_dim_fear(world: World) -> list[str]:
    out: list[str] = []
    lantern = world.entities.get("lantern")
    hero = world.entities.get("hero")
    if lantern is None or hero is None:
        return out
    if lantern.meters["light"] < THRESHOLD:
        sig = ("fear_from_dim",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["fear"] += 1
            out.append("__dim__")
    return out


CAUSAL_RULES = [
    Rule(name="dim_fear", tag="emotion", apply=_r_dim_fear),
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


def compatible(problem: Problem, tool: Tool) -> bool:
    return bool(problem.needs & tool.solves)


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for fest_id in FESTIVALS:
        for problem_id, problem in PROBLEMS.items():
            for tool_id, tool in TOOLS.items():
                if compatible(problem, tool) and tool.sense >= SENSE_MIN:
                    combos.append((fest_id, problem_id, tool_id))
    return combos


def reason_about_rejection(problem: Problem, tool: Tool) -> str:
    if tool.sense < SENSE_MIN:
        better = ", ".join(sorted(t.id for t in sensible_tools()))
        return (
            f"(No story: '{tool.id}' is too weak or silly for this world "
            f"(sense={tool.sense} < {SENSE_MIN}). Try one of: {better}.)"
        )
    return (
        f"(No story: {tool.label} does not solve {problem.label}. "
        f"This problem needs one of {sorted(problem.needs)}, but the tool only covers "
        f"{sorted(tool.solves)}.)"
    )


def outcome_of(params: "StoryParams") -> str:
    return "solved" if compatible(PROBLEMS[params.problem], TOOLS[params.tool]) and TOOLS[params.tool].sense >= SENSE_MIN else "stuck"


def predict_with_tool(world: World, problem: Problem, tool: Tool) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    lantern = sim.get("lantern")
    hero.memes["fear"] += float(problem.fear)
    if problem.damage in {"light", "both"}:
        lantern.meters["light"] -= 1
    if problem.damage in {"balance", "both"}:
        hero.meters["balance"] -= 1
    propagate(sim, narrate=False)
    if compatible(problem, tool):
        lantern.meters["light"] = max(lantern.meters["light"], 1.0)
        hero.meters["balance"] = max(hero.meters["balance"], 1.0)
        hero.memes["courage"] += 1
        hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
    return {
        "dark": lantern.meters["light"] < THRESHOLD,
        "unsteady": hero.meters["balance"] < THRESHOLD,
        "fear": hero.memes["fear"],
    }


def introduce(world: World, hero: Entity, elder: Entity, festival: Festival, lantern_kind: LanternKind) -> None:
    hero.memes["hope"] += 1
    lantern = world.get("lantern")
    world.say(
        f"In a quiet wood, {hero.id} had waited all year for the {festival.annual_word} {festival.name}."
    )
    world.say(
        f"{elder.id}, the old {elder.type}, placed {lantern_kind.phrase} in {hero.id}'s paws and said, "
        f'"Carry it to {festival.place}, and our little valley will know it is time for {festival.signal}."'
    )
    world.say(
        f"The lantern was round as an apple and warm as a pocketed star. {hero.id} began to climb, careful not to clutch it too hard."
    )
    lantern.meters["light"] = 1.0


def face_problem(world: World, hero: Entity, lantern_kind: LanternKind, problem: Problem) -> None:
    lantern = world.get("lantern")
    hero.memes["fear"] += float(problem.fear)
    if problem.damage in {"light", "both"}:
        lantern.meters["light"] -= 1
    if problem.damage in {"balance", "both"}:
        hero.meters["balance"] -= 1
    propagate(world, narrate=False)
    dim_line = ""
    if lantern.meters["light"] < THRESHOLD:
        dim_line = f" At once the glow turned {lantern_kind.dims_to}, a tiny ball-dim bead in the dark."
    wobble_line = ""
    if hero.meters["balance"] < THRESHOLD:
        wobble_line = " The path felt too narrow, and every pawstep asked for courage."
    world.say(f"{problem.line}{dim_line}{wobble_line}")


def choose_tool(world: World, hero: Entity, tool: Tool, problem: Problem) -> None:
    pred = predict_with_tool(world, problem, tool)
    world.facts["predicted_dark"] = pred["dark"]
    world.facts["predicted_unsteady"] = pred["unsteady"]
    world.say(
        f"{hero.id} stopped instead of rushing. {hero.pronoun().capitalize()} remembered {tool.phrase} and thought hard."
    )


def solve(world: World, hero: Entity, lantern_kind: LanternKind, problem: Problem, tool: Tool) -> None:
    lantern = world.get("lantern")
    hero.memes["courage"] += 1
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
    if problem.damage in {"light", "both"}:
        lantern.meters["light"] = 1.0
    if problem.damage in {"balance", "both"}:
        hero.meters["balance"] = 1.0
    world.say(
        f"{hero.id} took a breath, {tool.action}, and kept going. {problem.fix_result}"
    )
    world.say(
        f"Soon the lantern shone {lantern_kind.glow} again, and the dark no longer seemed bigger than {hero.pronoun('object')}."
    )


def fail_forward(world: World, hero: Entity, lantern_kind: LanternKind, problem: Problem, tool: Tool) -> None:
    lantern = world.get("lantern")
    hero.memes["fear"] += 1
    world.say(
        f"{hero.id} tried {tool.label}, but {problem.failure}"
    )
    if lantern.meters["light"] < THRESHOLD:
        world.say(
            f"The lantern stayed {lantern_kind.dims_to}, and the path ahead looked too uncertain for one small traveler."
        )


def finish_story(world: World, hero: Entity, elder: Entity, festival: Festival, lantern_kind: LanternKind, solved: bool) -> None:
    if solved:
        hero.memes["pride"] += 1
        world.say(
            f"At the top of {festival.place}, {hero.id} set the lantern on the stone niche. Its round light opened over the branches, and one by one the windows below answered with their own warm sparks."
        )
        world.say(
            f'{elder.id} smiled when {hero.id} came back down. "A brave heart is not the one that feels no fear," {elder.pronoun()} said. "It is the one that thinks kindly in the middle of fear."'
        )
        world.say(
            f"From then on, whenever the {festival.annual_word} night returned, the younger animals remembered how small paws, steady thought, and a little bravery had carried the light."
        )
    else:
        world.say(
            f"{hero.id} turned back and told {elder.id} the truth. The old {elder.type} did not scold."
        )
        world.say(
            f'"You were wise to stop before the dark grew mean," {elder.pronoun()} said. Then {elder.pronoun()} walked back with {hero.pronoun("object")}, and together they used a better tool.'
        )
        world.say(
            f"By moonrise the lantern was glowing on the hill after all, and {hero.id} learned that bravery may mean asking for the right help as much as stepping forward alone."
        )


def tell(
    festival: Festival,
    lantern_kind: LanternKind,
    problem: Problem,
    tool: Tool,
    hero_name: str,
    hero_type: str,
    elder_type: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", traits=[trait], label=hero_name))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, role="elder", label="the elder"))
    lantern = world.add(Entity(id="lantern", kind="thing", type="lantern", label=lantern_kind.label, phrase=lantern_kind.phrase))
    path = world.add(Entity(id="path", kind="thing", type="place", label=problem.place))
    hero.meters["balance"] = 1.0
    hero.memes["courage"] = 0.0
    introduce(world, hero, elder, festival, lantern_kind)

    world.para()
    face_problem(world, hero, lantern_kind, problem)
    choose_tool(world, hero, tool, problem)

    solved = compatible(problem, tool) and tool.sense >= SENSE_MIN
    world.para()
    if solved:
        solve(world, hero, lantern_kind, problem, tool)
    else:
        fail_forward(world, hero, lantern_kind, problem, tool)

    world.para()
    finish_story(world, hero, elder, festival, lantern_kind, solved)

    world.facts.update(
        hero=hero,
        elder=elder,
        lantern=lantern,
        festival=festival,
        lantern_kind=lantern_kind,
        problem=problem,
        tool=tool,
        solved=solved,
    )
    return world


@dataclass
class StoryParams:
    festival: str
    lantern: str
    problem: str
    tool: str
    hero_name: str
    hero_type: str
    elder_type: str
    trait: str
    seed: Optional[int] = None


FESTIVALS = {
    "lantern_night": Festival(
        id="lantern_night",
        name="Lantern Night",
        place="the hill of roots",
        closing="the whole wood gleamed below",
        signal="the dancing and soup",
        tags={"annual", "festival"},
    ),
    "acorn_evening": Festival(
        id="acorn_evening",
        name="Acorn Evening",
        place="the old stump tower",
        closing="the orchard lanes softened into gold",
        signal="the songs and sharing",
        tags={"annual", "festival"},
    ),
}
for _festival in FESTIVALS.values():
    _festival.annual_word = "annual"

LANTERNS = {
    "glowball": LanternKind(
        id="glowball",
        label="glowball lantern",
        phrase="a round glowball lantern",
        glow="bright as honey in glass",
        dims_to="ball-dim",
        repair="brightened",
        tags={"lantern", "light"},
    ),
    "moss_orb": LanternKind(
        id="moss_orb",
        label="moss-orb lamp",
        phrase="a moss-orb lamp with a clear shell",
        glow="soft and steady as a window at dusk",
        dims_to="ball-dim",
        repair="steadied",
        tags={"lantern", "light"},
    ),
}

PROBLEMS = {
    "wind_gust": Problem(
        id="wind_gust",
        label="a sharp wind gust",
        place="the bend above the thorns",
        hazard="wind",
        needs={"shield"},
        damage="light",
        fear=1,
        line="Halfway up, a sharp wind gust rushed through the trees and bit at the lantern flame.",
        fix_result="The wind slid around the shelter instead of through it.",
        failure="the wind kept licking the light smaller and smaller",
        tags={"wind", "light"},
    ),
    "stream_stones": Problem(
        id="stream_stones",
        label="slick stream stones",
        place="the stepping stones by the brook",
        hazard="balance",
        needs={"steady"},
        damage="both",
        fear=1,
        line="Near the brook, the stepping stones shone slick as fish backs.",
        fix_result="The careful rhythm gave each foot a true place to land.",
        failure="the stones stayed slippery, and the child dared not leap with the lantern",
        tags={"stream", "balance"},
    ),
    "owl_shadow": Problem(
        id="owl_shadow",
        label="a giant owl shadow",
        place="the tunnel of hazels",
        hazard="fear",
        needs={"calm"},
        damage="light",
        fear=2,
        line="In the hazel tunnel, an owl's long shadow swept over the path and made the lantern flutter.",
        fix_result="A calm pattern returned to the child's breath, and the light stopped trembling.",
        failure="the big shadow kept every little sound feeling twice as large",
        tags={"shadow", "courage"},
    ),
}

TOOLS = {
    "leaf_shield": Tool(
        id="leaf_shield",
        label="leaf shield",
        phrase="a broad dock leaf tucked in a sash",
        solves={"shield"},
        sense=3,
        action="held the broad leaf around the lantern like a tiny green wall",
        qa_text="used a broad leaf to shield the lantern from the wind",
        tags={"leaf", "shield"},
    ),
    "counting_song": Tool(
        id="counting_song",
        label="counting song",
        phrase="the counting song Elder had taught for nervous moments",
        solves={"calm", "steady"},
        sense=3,
        action="sang the counting song under a steady breath and matched each step to each number",
        qa_text="used a counting song to calm down and place each step carefully",
        tags={"song", "calm"},
    ),
    "vine_loop": Tool(
        id="vine_loop",
        label="vine loop",
        phrase="a little vine loop for the wrist",
        solves={"steady"},
        sense=2,
        action="slipped the vine loop around a wrist and kept the lantern close while testing each stone",
        qa_text="used a vine loop to keep the lantern close and cross carefully",
        tags={"vine", "steady"},
    ),
    "quick_dash": Tool(
        id="quick_dash",
        label="quick dash",
        phrase="the idea of running fast and hoping for luck",
        solves={"none"},
        sense=1,
        action="ran at the problem all at once",
        qa_text="tried to run fast",
        tags={"risky"},
    ),
}

GIRL_NAMES = ["Mina", "Pip", "Lark", "Daisy", "Fern", "Nell"]
BOY_NAMES = ["Bram", "Tobin", "Milo", "Ash", "Rowan", "Pip"]
HERO_TYPES = ["hedgehog", "mouse", "rabbit", "squirrel"]
ELDER_TYPES = ["owl", "tortoise", "badger"]
TRAITS = ["careful", "bright", "patient", "small", "thoughtful"]

CURATED = [
    StoryParams(
        festival="lantern_night",
        lantern="glowball",
        problem="wind_gust",
        tool="leaf_shield",
        hero_name="Mina",
        hero_type="hedgehog",
        elder_type="owl",
        trait="careful",
    ),
    StoryParams(
        festival="acorn_evening",
        lantern="moss_orb",
        problem="stream_stones",
        tool="vine_loop",
        hero_name="Bram",
        hero_type="mouse",
        elder_type="tortoise",
        trait="patient",
    ),
    StoryParams(
        festival="lantern_night",
        lantern="glowball",
        problem="owl_shadow",
        tool="counting_song",
        hero_name="Fern",
        hero_type="rabbit",
        elder_type="badger",
        trait="thoughtful",
    ),
]


KNOWLEDGE = {
    "annual": [
        (
            "What does annual mean?",
            "Annual means something happens once every year. A birthday party every year is an annual event."
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a light you can carry from place to place. It helps you see when the world is dark."
        )
    ],
    "wind": [
        (
            "Why can wind make a small light go dim?",
            "Wind pushes the warm air around a flame or little glow and can make it weaker. If the light is small, a strong gust can almost snuff it out."
        )
    ],
    "stream": [
        (
            "Why are wet stones slippery?",
            "Water makes stone slick, so feet do not grip it as well. That is why people and animals step slowly on wet rocks."
        )
    ],
    "shadow": [
        (
            "Why can shadows feel scary?",
            "Shadows hide shapes and make them hard to read. When you cannot tell what something is, your mind may imagine it is bigger or worse than it really is."
        )
    ],
    "shield": [
        (
            "What does a shield do for a small light?",
            "A shield blocks wind or rain from hitting the light directly. That gives the light a better chance to stay steady."
        )
    ],
    "song": [
        (
            "How can singing help when you feel afraid?",
            "A simple song can slow your breathing and give your mind a pattern to follow. That can help your body feel steadier too."
        )
    ],
    "vine": [
        (
            "Why would a loop around the wrist help while carrying something?",
            "A loop helps keep the thing close to your body so it does not swing away. That can make careful walking easier."
        )
    ],
}
KNOWLEDGE_ORDER = ["annual", "lantern", "wind", "stream", "shadow", "shield", "song", "vine"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    festival = f["festival"]
    lantern_kind = f["lantern_kind"]
    tool = f["tool"]
    return [
        f'Write a short fable for a 3-to-5-year-old that includes the words "clutch", "ball-dim", and "annual".',
        f"Tell a gentle animal fable where {hero.id}, a young {hero.type}, carries {lantern_kind.phrase} to an annual festival, meets {problem.label}, and solves it with {tool.label}.",
        f"Write a story about bravery and problem solving in which a small traveler pauses to think before acting, then saves a lantern on the way to {festival.name}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    problem = f["problem"]
    tool = f["tool"]
    festival = f["festival"]
    lantern_kind = f["lantern_kind"]
    solved = f["solved"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young {hero.type}, and {elder.id}, the old {elder.type}. {hero.id} is trusted to carry the lantern for the {festival.annual_word} {festival.name}."
        ),
        (
            f"Why was {hero.id} carrying the lantern?",
            f"{hero.id} was carrying it to {festival.place} so the forest could begin {festival.signal}. The journey mattered because the round lantern was the signal for the whole celebration."
        ),
        (
            f"What problem did {hero.id} meet on the path?",
            f"{hero.id} met {problem.label} at {problem.place}. It made the trip feel dangerous because it hurt the lantern light, the footing, or both."
        ),
    ]
    if solved:
        qa.append(
            (
                f"How did {hero.id} solve the problem?",
                f"{hero.id} {tool.qa_text}. That worked because it matched the real trouble instead of hoping the trouble would go away by itself."
            )
        )
        qa.append(
            (
                f"How was {hero.id} brave?",
                f"{hero.id} was brave by stopping to think even while feeling afraid. Bravery here meant taking the next wise step instead of dropping the lantern or running away."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The lantern reached {festival.place} and shone {lantern_kind.glow}. The ending image proves that thought and courage together can carry a small light a long way."
            )
        )
    else:
        qa.append(
            (
                f"Did {tool.label} solve the problem?",
                f"No. {tool.label.capitalize()} did not fit {problem.label}, so the trouble stayed in the way. {hero.id} had to turn back and get wiser help."
            )
        )
        qa.append(
            (
                "What lesson did the story teach?",
                "The lesson is that bravery is not just rushing forward. Real bravery also includes noticing what kind of problem you have and choosing the right answer."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"annual"} | set(f["lantern_kind"].tags) | set(f["problem"].tags) | set(f["tool"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible_tool(T) :- tool(T), sense(T, S), sense_min(M), S >= M.
compatible(P, T) :- problem(P), tool(T), needs(P, N), solves(T, N).
valid(F, P, T) :- festival(F), problem(P), tool(T), compatible(P, T), sensible_tool(T).

outcome(solved) :- chosen_problem(P), chosen_tool(T), compatible(P, T), sensible_tool(T).
outcome(stuck) :- chosen_problem(P), chosen_tool(T), not compatible(P, T).
outcome(stuck) :- chosen_tool(T), tool(T), not sensible_tool(T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for fid in FESTIVALS:
        lines.append(asp.fact("festival", fid))
    for lid in LANTERNS:
        lines.append(asp.fact("lantern", lid))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for need in sorted(problem.needs):
            lines.append(asp.fact("needs", pid, need))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, tool.sense))
        for solve in sorted(tool.solves):
            lines.append(asp.fact("solves", tid, solve))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_tool", params.tool),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            pass
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} scenario outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        assert sample.story.strip()
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable storyworld: a small forest traveler solves one annual lantern-path problem."
    )
    ap.add_argument("--festival", choices=FESTIVALS)
    ap.add_argument("--lantern", choices=LANTERNS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--elder-type", choices=ELDER_TYPES)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.tool:
        problem = PROBLEMS[args.problem]
        tool = TOOLS[args.tool]
        if not compatible(problem, tool) or tool.sense < SENSE_MIN:
            raise StoryError(reason_about_rejection(problem, tool))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        tool = TOOLS[args.tool]
        problem = PROBLEMS[args.problem] if args.problem else next(iter(PROBLEMS.values()))
        raise StoryError(reason_about_rejection(problem, tool))

    combos = [
        c for c in valid_combos()
        if (args.festival is None or c[0] == args.festival)
        and (args.problem is None or c[1] == args.problem)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    festival, problem, tool = rng.choice(sorted(combos))
    lantern = args.lantern or rng.choice(sorted(LANTERNS))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    elder_type = args.elder_type or rng.choice(ELDER_TYPES)
    if args.name:
        hero_name = args.name
    else:
        if hero_type in {"rabbit", "squirrel"}:
            hero_name = rng.choice(sorted(set(GIRL_NAMES + BOY_NAMES)))
        else:
            hero_name = rng.choice(sorted(set(GIRL_NAMES + BOY_NAMES)))
    trait = rng.choice(TRAITS)
    return StoryParams(
        festival=festival,
        lantern=lantern,
        problem=problem,
        tool=tool,
        hero_name=hero_name,
        hero_type=hero_type,
        elder_type=elder_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        festival = FESTIVALS[params.festival]
        lantern = LANTERNS[params.lantern]
        problem = PROBLEMS[params.problem]
        tool = TOOLS[params.tool]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from err

    if not compatible(problem, tool) or tool.sense < SENSE_MIN:
        raise StoryError(reason_about_rejection(problem, tool))

    world = tell(
        festival=festival,
        lantern_kind=lantern,
        problem=problem,
        tool=tool,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        elder_type=params.elder_type,
        trait=params.trait,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (festival, problem, tool) combos:\n")
        for festival, problem, tool in combos:
            print(f"  {festival:14} {problem:14} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            try:
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.hero_name}: {p.problem} with {p.tool} at {p.festival}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
