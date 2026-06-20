#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/repulse_prove_sausage_problem_solving_friendship_fairy.py
====================================================================================

A standalone story world for a small fairy-tale domain built from the seed words
"repulse", "prove", and "sausage", with the features Problem Solving and
Friendship.

Premise
-------
Two friends are on their way to a fairy feast with a sausage in their basket.
At a magical crossing, they meet a lonely guardian and a blocked passage. The
trouble has two parts at once: the guardian is too hungry and worried to help,
and the crossing mechanism is jammed in a specific way. The friends solve the
problem by sharing their food, using the right tool, and working together to
prove they are true friends.

Run it
------
    python storyworlds/worlds/gpt-5.4/repulse_prove_sausage_problem_solving_friendship_fairy.py
    python storyworlds/worlds/gpt-5.4/repulse_prove_sausage_problem_solving_friendship_fairy.py --setting moon_bridge --problem jammed_crank --tool oil_flask
    python storyworlds/worlds/gpt-5.4/repulse_prove_sausage_problem_solving_friendship_fairy.py --problem thorn_rope --tool moonwater
    python storyworlds/worlds/gpt-5.4/repulse_prove_sausage_problem_solving_friendship_fairy.py --all
    python storyworlds/worlds/gpt-5.4/repulse_prove_sausage_problem_solving_friendship_fairy.py --qa --json
    python storyworlds/worlds/gpt-5.4/repulse_prove_sausage_problem_solving_friendship_fairy.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we need the package dir
# storyworlds/ on sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"     # "character" | "thing"
    type: str = "thing"     # child, troll, bridge, gate, tool, food ...
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "fairy_girl", "princess", "woman"}
        male = {"boy", "father", "fairy_boy", "prince", "man", "troll"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str
    place: str
    destination: str
    crossing: str
    crossing_the: str
    guardian_kind: str
    guardian_name: str
    opening_line: str
    ending_line: str
    moonlight: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    jam_text: str
    smell_text: str
    repulse_line: str
    requires: str
    fix_text: str
    qa_fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    handles: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class SausageKind:
    id: str
    label: str
    phrase: str
    aroma: str
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
        return clone


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_grumpy(world: World) -> list[str]:
    guardian = world.get("guardian")
    if guardian.meters["hunger"] < THRESHOLD:
        return []
    sig = ("grumpy", "guardian")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    guardian.memes["worry"] += 1
    guardian.memes["lonely"] += 1
    return []


def _r_friendship(world: World) -> list[str]:
    f1 = world.get("friend1")
    f2 = world.get("friend2")
    if f1.memes["helped"] < THRESHOLD or f2.memes["helped"] < THRESHOLD:
        return []
    sig = ("friendship", "pair")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    f1.memes["trust"] += 1
    f2.memes["trust"] += 1
    f1.memes["pride"] += 1
    f2.memes["pride"] += 1
    world.get("crossing").memes["teamwork_seen"] += 1
    return []


def _r_open(world: World) -> list[str]:
    crossing = world.get("crossing")
    guardian = world.get("guardian")
    if crossing.meters["unstuck"] < THRESHOLD:
        return []
    if guardian.meters["hunger"] >= THRESHOLD:
        return []
    if crossing.memes["teamwork_seen"] < THRESHOLD:
        return []
    sig = ("open", "crossing")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crossing.meters["open"] += 1
    guardian.memes["trust"] += 1
    guardian.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule("grumpy", "social", _r_grumpy),
    Rule("friendship", "social", _r_friendship),
    Rule("open", "physical", _r_open),
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
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def tool_matches(problem: Problem, tool: Tool) -> bool:
    return problem.id in tool.handles and problem.requires == tool.id


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid in SETTINGS:
        for pid, prob in PROBLEMS.items():
            for tid, tool in TOOLS.items():
                if tool_matches(prob, tool):
                    combos.append((sid, pid, tid))
    return combos


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return (
        f"(No story: {tool.phrase} does not solve {problem.label}. "
        f"In this world, {problem.label} needs {TOOLS[problem.requires].phrase}, "
        f"so the friends would have no honest solution.)"
    )


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, f1: Entity, f2: Entity, setting: Setting, sausage: SausageKind) -> None:
    for child in (f1, f2):
        child.memes["joy"] += 1
    world.say(
        f"In a little kingdom where dew shone like silver coins, {f1.id} and {f2.id} "
        f"were the best of friends. {setting.opening_line}"
    )
    world.say(
        f"They were walking to {setting.destination} with a basket that held "
        f"{sausage.phrase}. {sausage.aroma}"
    )


def approach(world: World, setting: Setting, problem: Problem) -> None:
    crossing = world.get("crossing")
    crossing.meters["stuck"] += 1
    guardian = world.get("guardian")
    guardian.meters["hunger"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when they reached {setting.crossing_the}, they stopped. {problem.jam_text}"
    )
    world.say(problem.smell_text)
    world.say(problem.repulse_line)


def guardian_challenge(world: World, setting: Setting, f1: Entity, f2: Entity) -> None:
    guardian = world.get("guardian")
    world.say(
        f'By the post sat {setting.guardian_name} the {setting.guardian_kind}, rubbing '
        f'his round belly. "I have not lowered {setting.crossing_the} for anyone today," '
        f'he sighed. "If you wish to pass, you must prove that you are true friends, '
        f'not just two hurried feet on the same road."'
    )
    guardian.memes["hope"] += 1
    f1.memes["worry"] += 1
    f2.memes["worry"] += 1


def think_together(world: World, f1: Entity, f2: Entity, tool: Tool, sausage: SausageKind) -> None:
    world.say(
        f'{f1.id} looked at the basket. "{sausage.label.capitalize()} can cheer a hungry heart," '
        f'{f1.pronoun()} whispered.'
    )
    world.say(
        f'{f2.id} touched {tool.phrase}. "And this can help with the stuck part," '
        f'{f2.pronoun()} said. "If we do one kind thing and one clever thing together, '
        f'we can solve it."'
    )


def share_sausage(world: World, f1: Entity, f2: Entity, sausage: SausageKind) -> None:
    guardian = world.get("guardian")
    guardian.meters["hunger"] = 0.0
    guardian.memes["gratitude"] += 1
    f1.memes["kindness"] += 1
    f2.memes["kindness"] += 1
    world.say(
        f'Together they took out the {sausage.label} and offered half to the guardian. '
        f'He blinked in surprise before taking the warm bite.'
    )
    world.say(
        f'"You shared your feast before your own bellies were full," he said. '
        f'"That is the first proof."'
    )


def fix_crossing(world: World, f1: Entity, f2: Entity, problem: Problem, tool: Tool, setting: Setting) -> None:
    crossing = world.get("crossing")
    f1.memes["helped"] += 1
    f2.memes["helped"] += 1
    crossing.meters["unstuck"] += 1
    crossing.meters["stuck"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"Then {f1.id} steadied {setting.crossing_the} while {f2.id} {tool.action}. "
        f"{problem.fix_text}"
    )
    world.say(
        f"They did not tug against each other or argue over turns. They moved like two hands "
        f"on the same ribbon."
    )


def resolution(world: World, f1: Entity, f2: Entity, setting: Setting) -> None:
    propagate(world, narrate=False)
    guardian = world.get("guardian")
    crossing = world.get("crossing")
    if crossing.meters["open"] < THRESHOLD:
        raise StoryError("The passage never opened, so the story has no fairy-tale resolution.")
    f1.memes["worry"] = 0.0
    f2.memes["worry"] = 0.0
    f1.memes["joy"] += 1
    f2.memes["joy"] += 1
    world.say(
        f'With a soft creak and a bright little shiver, {setting.crossing_the} opened. '
        f'{setting.guardian_name} smiled until his eyes looked kind and sleepy.'
    )
    world.say(
        f'"You did not only feed me," he said. "You listened, planned, and helped one another. '
        f'You have proved your friendship."'
    )
    if guardian.memes["lonely"] >= THRESHOLD:
        world.say(
            f'He promised that from then on he would speak more gently to travelers, because the '
            f'two friends had reminded him how warm company could be.'
        )
    world.say(
        f'{setting.ending_line} Above them, {setting.moonlight}'
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, problem: Problem, tool: Tool, sausage: SausageKind,
         friend1: str = "Nella", friend1_type: str = "girl",
         friend2: str = "Tobin", friend2_type: str = "boy") -> World:
    world = World()
    f1 = world.add(Entity(id=friend1, kind="character", type=friend1_type, role="friend"))
    f2 = world.add(Entity(id=friend2, kind="character", type=friend2_type, role="friend"))
    guardian = world.add(Entity(
        id="guardian", kind="character", type="troll", role="guardian",
        label=setting.guardian_name, attrs={"kind": setting.guardian_kind},
    ))
    crossing = world.add(Entity(
        id="crossing", kind="thing", type="crossing", role="crossing", label=setting.crossing
    ))
    basket = world.add(Entity(id="basket", kind="thing", type="basket", label="basket"))
    food = world.add(Entity(id="sausage", kind="thing", type="food", label=sausage.label))
    tool_ent = world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label))
    basket.attrs["holds"] = sausage.id
    tool_ent.attrs["tool_id"] = tool.id

    introduce(world, f1, f2, setting, sausage)
    world.para()
    approach(world, setting, problem)
    guardian_challenge(world, setting, f1, f2)
    think_together(world, f1, f2, tool, sausage)
    world.para()
    share_sausage(world, f1, f2, sausage)
    fix_crossing(world, f1, f2, problem, tool, setting)
    world.para()
    resolution(world, f1, f2, setting)

    world.facts.update(
        friend1=f1,
        friend2=f2,
        guardian=guardian,
        crossing=crossing,
        basket=basket,
        sausage_cfg=sausage,
        tool_cfg=tool,
        problem=problem,
        setting=setting,
        proved=crossing.meters["open"] >= THRESHOLD,
        guardian_fed=guardian.meters["hunger"] < THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
SETTINGS = {
    "moon_bridge": Setting(
        "moon_bridge",
        "the moon bridge path",
        "the Moonberry Feast",
        "the moon bridge",
        "the moon bridge",
        "bridge troll",
        "Mossbeard",
        "They loved to follow the path of blue mushrooms to the Moonberry Feast.",
        "Hand in hand, they crossed the moon bridge and went on to the Moonberry Feast, where even the lanterns seemed to bow to them.",
        "moonlight lay on the water like folded silk",
        tags={"bridge", "feast", "fairy"},
    ),
    "willow_gate": Setting(
        "willow_gate",
        "the willow lane",
        "the Dewdrop Dance",
        "the willow gate",
        "the willow gate",
        "gate troll",
        "Mossbeard",
        "They had set out before sunset to reach the Dewdrop Dance beyond the willow lane.",
        "Laughing softly, they stepped through the willow gate and on toward the Dewdrop Dance, where the fiddles were already singing.",
        "the willow leaves flashed silver like fish scales in a stream",
        tags={"gate", "dance", "fairy"},
    ),
    "crystal_ferry": Setting(
        "crystal_ferry",
        "the crystal ford road",
        "the Starlight Supper",
        "the crystal ferry",
        "the crystal ferry",
        "ferry troll",
        "Mossbeard",
        "They were hurrying along the crystal ford road to reach the Starlight Supper before the first bell.",
        "Soon they floated over the water on the crystal ferry and on to the Starlight Supper, where stars shivered in the soup bowls.",
        "small stars peeped out early and trembled in the darkening sky",
        tags={"ferry", "supper", "fairy"},
    ),
}

PROBLEMS = {
    "jammed_crank": Problem(
        "jammed_crank",
        "a jammed crank",
        "The turning crank would not budge, no matter how the wind pushed at it.",
        "Black stinkweed had worked its way into the iron teeth and made the whole thing smell sour.",
        "The sharp smell was enough to repulse even the midges dancing over the water.",
        "oil_flask",
        "The sticky teeth loosened, and the crank began to turn with a patient click-click-click.",
        "used the oil flask to loosen the jammed crank",
        tags={"crank", "smell", "repulse"},
    ),
    "thorn_rope": Problem(
        "thorn_rope",
        "a thorn-snared rope",
        "A rope that should have lifted the crossing had caught fast in a nest of hooked thorns.",
        "Each tug made dry briar dust puff into the air and prickle at their noses.",
        "The dusty briar smell would repulse anyone who tried to stand too near for long.",
        "silver_comb",
        "Little by little, the thorns let go, and the rope slid free with a bright whisper.",
        "used the silver comb to tease the thorns out of the rope",
        tags={"rope", "thorns", "repulse"},
    ),
    "sticky_latch": Problem(
        "sticky_latch",
        "a sap-sticky latch",
        "The latch had been glued shut by amber pine sap and would not lift.",
        "The old sap had turned bitter in the cold evening, and the smell hung under the archway.",
        "It was a smell strong enough to repulse even a beetle looking for supper.",
        "moonwater",
        "The moonwater thinned the sap, and the latch sprang free with a silver pop.",
        "poured moonwater over the latch to wash the sap away",
        tags={"latch", "sap", "repulse"},
    ),
}

TOOLS = {
    "oil_flask": Tool(
        "oil_flask",
        "oil flask",
        "an oil flask",
        "tilted the oil flask over the stubborn metal",
        handles={"jammed_crank"},
        tags={"oil", "tool"},
    ),
    "silver_comb": Tool(
        "silver_comb",
        "silver comb",
        "a silver comb",
        "worked the silver comb between the knot of thorns",
        handles={"thorn_rope"},
        tags={"comb", "tool"},
    ),
    "moonwater": Tool(
        "moonwater",
        "moonwater vial",
        "a vial of moonwater",
        "poured the moonwater in a shining thread across the sticky latch",
        handles={"sticky_latch"},
        tags={"water", "tool"},
    ),
}

SAUSAGES = {
    "festival_sausage": SausageKind(
        "festival_sausage",
        "sausage",
        "a warm picnic sausage wrapped in paper",
        "The smell of pepper and rosemary floated out whenever the basket lid bounced.",
        tags={"sausage", "food"},
    ),
}

GIRL_NAMES = ["Nella", "Poppy", "Iris", "Mina", "Elsie", "Fern", "Lila", "Wren"]
BOY_NAMES = ["Tobin", "Rowan", "Milo", "Ash", "Bram", "Perrin", "Hugo", "Finn"]

CURATED = [
    # Seed-faithful default trio.
    None,
]

# Fill after StoryParams is defined.


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    sausage: str
    friend1: str
    friend1_type: str
    friend2: str
    friend2_type: str
    seed: Optional[int] = None


# Curated samples, now that StoryParams exists.
CURATED = [
    StoryParams("moon_bridge", "jammed_crank", "oil_flask", "festival_sausage", "Nella", "girl", "Tobin", "boy"),
    StoryParams("willow_gate", "thorn_rope", "silver_comb", "festival_sausage", "Poppy", "girl", "Bram", "boy"),
    StoryParams("crystal_ferry", "sticky_latch", "moonwater", "festival_sausage", "Fern", "girl", "Milo", "boy"),
]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "sausage": [(
        "What is a sausage?",
        "A sausage is a food made for eating, often shaped like a little tube. In stories, sharing food can show kindness and care."
    )],
    "bridge": [(
        "What does a bridge do?",
        "A bridge helps people cross over water or a gap without falling in. If a bridge is stuck, travelers may need help to pass safely."
    )],
    "gate": [(
        "What does a gate do?",
        "A gate opens and closes a path. It can keep a place safe, but someone has to unlatch it before people can go through."
    )],
    "ferry": [(
        "What is a ferry?",
        "A ferry is a boat or floating platform that carries people across water. It helps travelers reach the other side."
    )],
    "tool": [(
        "What is a tool?",
        "A tool is something you use to help fix or make something. The right tool makes a hard job easier."
    )],
    "problem_solving": [(
        "What does problem solving mean?",
        "Problem solving means stopping to think about what is wrong and then choosing a smart way to fix it. It often works best when people share ideas."
    )],
    "friendship": [(
        "How can friends prove their friendship?",
        "Friends prove their friendship by helping each other, sharing, and staying kind when something is hard. Real friendship shows in actions, not just words."
    )],
    "repulse": [(
        "What does the word 'repulse' mean?",
        "Repulse means to push away by making someone feel strong dislike or disgust. A bad smell can repulse someone and make them step back."
    )],
}
KNOWLEDGE_ORDER = ["sausage", "bridge", "gate", "ferry", "tool", "problem_solving", "friendship", "repulse"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s = f["setting"]
    p = f["problem"]
    t = f["tool_cfg"]
    return [
        'Write a fairy-tale story for a 3-to-5-year-old that includes the words "repulse", "prove", and "sausage".',
        f"Tell a gentle problem-solving story where two friends must get past {s.crossing_the}, solve {p.label}, and prove their friendship.",
        f"Write a child-facing fairy tale where kindness and the right tool matter: the friends share a sausage, use {t.phrase}, and help a lonely guardian.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    f1 = f["friend1"]
    f2 = f["friend2"]
    setting = f["setting"]
    problem = f["problem"]
    tool = f["tool_cfg"]
    sausage = f["sausage_cfg"]
    guardian = f["guardian"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {f1.id} and {f2.id}, and {setting.guardian_name} the {setting.guardian_kind}. "
            f"They meet at {setting.crossing_the} on the way to {setting.destination}."
        ),
        (
            "What problem stopped the friends?",
            f"They found {setting.crossing_the} blocked by {problem.label}. "
            f"The crossing could not open until somebody solved the jammed part."
        ),
        (
            "Why does the story use the word 'repulse'?",
            f"The bad smell around the crossing was so strong it could repulse anyone nearby. "
            f"That helped show why the place felt unpleasant and why the problem needed fixing."
        ),
        (
            f"How did {f1.id} and {f2.id} solve the problem?",
            f"They shared their {sausage.label} with the hungry guardian and then {problem.qa_fix}. "
            f"Feeding him softened his heart, and using the right tool fixed the crossing."
        ),
        (
            "How did they prove their friendship?",
            f"They proved it by thinking together and helping at the same time instead of arguing or rushing. "
            f"One held steady while the other worked, and their kindness showed the guardian they trusted each other."
        ),
        (
            "How did the story end?",
            f"In the end, {setting.crossing_the} opened and the friends went on to {setting.destination}. "
            f"The final image shows that their kindness changed the road from a stuck, sour place into a bright one."
        ),
    ]
    if guardian.memes["lonely"] >= THRESHOLD:
        qa.append((
            f"Why was {setting.guardian_name} kinder at the end?",
            f"He had been lonely and hungry, which made him worried and sharp with travelers. "
            f"After the friends shared food and listened to him, he felt relieved and trusted them."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"sausage", "tool", "problem_solving", "friendship", "repulse"}
    setting = f["setting"]
    if "bridge" in setting.tags:
        tags.add("bridge")
    if "gate" in setting.tags:
        tags.add("gate")
    if "ferry" in setting.tags:
        tags.add("ferry")
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:9} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Correct tool for each problem.
tool_matches(P, T) :- requires(P, T), handles(T, P).

% Reasonable story combinations.
valid(S, P, T) :- setting(S), problem(P), tool(T), tool_matches(P, T).

% Outcome model: in this domain, the passage opens when the right tool is used,
% the guardian is fed, and both friends help. Those three action-facts are part
% of every generated story, but we keep them explicit for parity checking.
solved          :- chosen_problem(P), chosen_tool(T), tool_matches(P, T).
friendship_seen :- both_help.
kindness_seen   :- fed_guardian.
opened          :- solved, friendship_seen, kindness_seen.
outcome(opened) :- opened.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("requires", pid, prob.requires))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for handled in sorted(tool.handles):
            lines.append(asp.fact("handles", tid, handled))
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
        asp.fact("fed_guardian"),
        asp.fact("both_help"),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "opened" if tool_matches(PROBLEMS[params.problem], TOOLS[params.tool]) else "?"


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
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print(f"MISMATCH in outcome for {params}: asp={asp_outcome(params)} python={outcome_of(params)}")

    if rc == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} curated scenarios.")

    # Smoke test: ordinary generation and emit must not crash.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty during verify.")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke test")
        if not buf.getvalue().strip():
            raise StoryError("Emit produced no output during verify.")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: two friends solve a blocked magical crossing with kindness, a sausage, and the right tool."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--friend1")
    ap.add_argument("--friend2")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.tool:
        prob = PROBLEMS[args.problem]
        tool = TOOLS[args.tool]
        if not tool_matches(prob, tool):
            raise StoryError(explain_rejection(prob, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.problem is None or combo[1] == args.problem)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, problem, tool = rng.choice(sorted(combos))
    friend1, t1 = _pick_name(rng)
    if args.friend1:
        friend1 = args.friend1
    friend2, t2 = _pick_name(rng, avoid=friend1)
    if args.friend2:
        if args.friend2 == friend1:
            raise StoryError("(No story: the two friends must have different names.)")
        friend2 = args.friend2

    return StoryParams(
        setting=setting,
        problem=problem,
        tool=tool,
        sausage="festival_sausage",
        friend1=friend1,
        friend1_type=t1,
        friend2=friend2,
        friend2_type=t2,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        PROBLEMS[params.problem],
        TOOLS[params.tool],
        SAUSAGES[params.sausage],
        params.friend1,
        params.friend1_type,
        params.friend2,
        params.friend2_type,
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
        print(f"{len(combos)} compatible (setting, problem, tool) combos:\n")
        for setting, problem, tool in combos:
            print(f"  {setting:14} {problem:14} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
            header = f"### {p.friend1} & {p.friend2}: {p.setting} / {p.problem} / {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
