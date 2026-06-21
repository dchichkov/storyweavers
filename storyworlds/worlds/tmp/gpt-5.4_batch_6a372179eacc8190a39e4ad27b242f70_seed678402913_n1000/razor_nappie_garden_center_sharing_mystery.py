#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/razor_nappie_garden_center_sharing_mystery.py
========================================================================

A standalone storyworld about a small mystery at a garden center.

Two children notice that something has gone missing. There is only one useful
search tool nearby, and at first one child wants to keep it. The mystery is
solved only when they share the tool and work together.

The seed words "razor" and "nappie" appear naturally in the setting details:
a grown-up-only razor is kept in a marked cabinet for opening twine and boxes,
and a baby sibling's nappie bag hangs from the stroller by the aisle.

Run it
------
    python storyworlds/worlds/gpt-5.4/razor_nappie_garden_center_sharing_mystery.py
    python storyworlds/worlds/gpt-5.4/razor_nappie_garden_center_sharing_mystery.py --case labels --tool magnifier
    python storyworlds/worlds/gpt-5.4/razor_nappie_garden_center_sharing_mystery.py --case hanging_star --tool wagon
    python storyworlds/worlds/gpt-5.4/razor_nappie_garden_center_sharing_mystery.py --all
    python storyworlds/worlds/gpt-5.4/razor_nappie_garden_center_sharing_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4/razor_nappie_garden_center_sharing_mystery.py --verify
"""

from __future__ import annotations

import argparse
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
class MysteryCase:
    id: str
    missing_item: str
    opening: str
    question: str
    need: str
    clue_text: str
    reveal_text: str
    ending_text: str
    culprit: str
    hiding_place: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ToolDef:
    id: str
    label: str
    phrase: str
    solves: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
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
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def tool_fits(case_cfg: MysteryCase, tool_cfg: ToolDef) -> bool:
    return case_cfg.need in tool_cfg.solves


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for case_id, case_cfg in CASES.items():
        for tool_id, tool_cfg in TOOLS.items():
            if tool_fits(case_cfg, tool_cfg):
                out.append((case_id, tool_id))
    return out


def explain_rejection(case_cfg: MysteryCase, tool_cfg: ToolDef) -> str:
    need_map = {
        "tiny": "The clue in this mystery is too small to inspect without a close-looking tool.",
        "high": "The missing thing is up high, so the children need a way to reach it safely.",
        "carry": "The solution requires carrying several things back together.",
    }
    return (
        f"(No story: {tool_cfg.label} does not fit the {case_cfg.id} mystery. "
        f"{need_map.get(case_cfg.need, 'The tool does not solve this kind of clue.')}"
    )


def _r_hoard(world: World) -> list[str]:
    tool = world.get("tool")
    if tool.meters["shared"] >= THRESHOLD:
        return []
    holder = world.facts.get("holder")
    other = world.facts.get("other")
    if not holder or not other or holder.memes["hoard"] < THRESHOLD:
        return []
    sig = ("left_out", other.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    other.memes["left_out"] += 1
    other.memes["frustration"] += 1
    world.get("team").meters["stuck"] += 1
    return ["__left_out__"]


def _r_find_clue(world: World) -> list[str]:
    tool = world.get("tool")
    case = world.get("case")
    if tool.meters["shared"] < THRESHOLD or case.meters["searching"] < THRESHOLD:
        return []
    if not world.facts.get("tool_works", False):
        return []
    sig = ("clue_found", case.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    case.meters["clue_found"] += 1
    for kid in (world.facts["child1"], world.facts["child2"]):
        kid.memes["focus"] += 1
    return ["__clue_found__"]


def _r_solve(world: World) -> list[str]:
    case = world.get("case")
    if case.meters["clue_found"] < THRESHOLD:
        return []
    sig = ("solved", case.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    case.meters["solved"] += 1
    team = world.get("team")
    team.meters["stuck"] = 0.0
    team.meters["solved"] += 1
    for kid in (world.facts["child1"], world.facts["child2"]):
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
        kid.memes["generosity"] += 1
    return ["__solved__"]


CAUSAL_RULES = [
    Rule(name="hoard", apply=_r_hoard),
    Rule(name="find_clue", apply=_r_find_clue),
    Rule(name="solve", apply=_r_solve),
]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                produced.extend(bits)
                changed = True
    return produced


@dataclass
class StoryParams:
    case: str
    tool: str
    child1_name: str
    child1_gender: str
    child2_name: str
    child2_gender: str
    parent: str
    holder: str
    seed: Optional[int] = None


CASES = {
    "labels": MysteryCase(
        id="labels",
        missing_item="the strawberry labels",
        opening="The strawberry seedlings stood in neat rows, but their little name labels were gone.",
        question="Who had made the strawberry names disappear?",
        need="tiny",
        clue_text="When they shared the tool, they spotted tiny muddy paw marks and one bent paper tab tucked under the bench.",
        reveal_text="The trail led to a sleepy garden-center kitten batting the labels under the slats one by one.",
        ending_text="Together they slid the labels back into the pots and left one jingly bell-ball nearby so the kitten had something better to chase.",
        culprit="a garden-center kitten",
        hiding_place="under the slatted strawberry bench",
        tags={"magnifier", "kitten", "labels"},
    ),
    "hanging_star": MysteryCase(
        id="hanging_star",
        missing_item="the silver star wind-spinner",
        opening="Above the vine arch, an empty hook swung slowly where the silver star wind-spinner should have been.",
        question="Where had the shining star gone?",
        need="high",
        clue_text="When they took turns safely, they saw a thin ribbon snagged on the top beam and a flash of silver above the leaves.",
        reveal_text="The missing spinner had been tossed up onto the beam by a gust of wind and left there, twinkling out of sight.",
        ending_text="Together they brought the star down and tied it back on with help from the grown-up, where it could spin again in the soft air.",
        culprit="a gust of wind",
        hiding_place="on the top beam over the vine arch",
        tags={"stool", "wind", "star"},
    ),
    "herb_pots": MysteryCase(
        id="herb_pots",
        missing_item="three tiny herb pots",
        opening="By the mint table, three tiny herb pots were missing from the front row, leaving three round dusty circles behind.",
        question="Who had moved the little pots?",
        need="carry",
        clue_text="Once they shared the tool, they followed a line of soil crumbs behind the fern stand and found the pots grouped together there.",
        reveal_text="A helper had nudged the pots out of the busy path during a delivery and forgotten to bring them back.",
        ending_text="Together the children loaded the little pots in the wagon and rolled them back, side by side, until the table looked complete again.",
        culprit="a rushed helper",
        hiding_place="behind the fern stand",
        tags={"wagon", "herbs", "pots"},
    ),
}

TOOLS = {
    "magnifier": ToolDef(
        id="magnifier",
        label="magnifying glass",
        phrase="the big round magnifying glass from the discovery table",
        solves={"tiny"},
        tags={"magnifier"},
    ),
    "stool": ToolDef(
        id="stool",
        label="step stool",
        phrase="the little green step stool by the trellis display",
        solves={"high"},
        tags={"stool"},
    ),
    "wagon": ToolDef(
        id="wagon",
        label="red wagon",
        phrase="the red wagon used for small pots",
        solves={"carry"},
        tags={"wagon"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah"]


CURATED = [
    StoryParams(
        case="labels",
        tool="magnifier",
        child1_name="Lily",
        child1_gender="girl",
        child2_name="Tom",
        child2_gender="boy",
        parent="mother",
        holder="child1",
    ),
    StoryParams(
        case="hanging_star",
        tool="stool",
        child1_name="Ben",
        child1_gender="boy",
        child2_name="Mia",
        child2_gender="girl",
        parent="father",
        holder="child2",
    ),
    StoryParams(
        case="herb_pots",
        tool="wagon",
        child1_name="Zoe",
        child1_gender="girl",
        child2_name="Max",
        child2_gender="boy",
        parent="mother",
        holder="child1",
    ),
]


def introduce(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    for kid in (a, b):
        kid.memes["curiosity"] += 1
    world.say(
        f"On a bright morning, {a.id} and {b.id} walked through the garden center with their {parent.label_word}."
    )
    world.say(
        "Near the potting bench stood a tall cabinet with a note that said only grown-ups may use the razor for cutting twine and boxes."
    )
    world.say(
        "Beside the stroller hung the baby's nappie bag, gently bumping the wheel whenever anyone stopped to look at the plants."
    )


def notice_mystery(world: World, a: Entity, b: Entity, case_cfg: MysteryCase) -> None:
    world.say(case_cfg.opening)
    world.say(
        f'"That is odd," {a.id} whispered. "{case_cfg.question}"'
    )
    b.memes["curiosity"] += 1
    world.get("case").meters["noticed"] += 1


def choose_tool(world: World, holder: Entity, other: Entity, tool_cfg: ToolDef) -> None:
    holder.memes["hoard"] += 1
    holder.memes["eagerness"] += 1
    world.facts["holder"] = holder
    world.facts["other"] = other
    world.say(
        f"{holder.id} hurried to grab {tool_cfg.phrase}. "
        f'"I can do it fastest," {holder.pronoun()} said.'
    )
    propagate(world)
    if other.memes["left_out"] >= THRESHOLD:
        world.say(
            f"{other.id} took a step back. {other.pronoun().capitalize()} wanted to help too, but being left out made the mystery feel harder instead of easier."
        )


def nudge_to_share(world: World, parent: Entity, holder: Entity, other: Entity, tool_cfg: ToolDef) -> None:
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them. "A mystery is easier with two careful eyes," {parent.pronoun()} said. '
        f'"If {holder.id} shares the {tool_cfg.label}, both of you can notice more."'
    )
    holder.memes["hoard"] = 0.0
    holder.memes["generosity"] += 1
    other.memes["trust"] += 1
    world.get("tool").meters["shared"] += 1
    world.say(
        f"{holder.id} looked at {other.id}, then moved over and held the {tool_cfg.label} between them so they could both use it."
    )


def search_together(world: World, a: Entity, b: Entity, case_cfg: MysteryCase, tool_cfg: ToolDef) -> None:
    world.get("case").meters["searching"] += 1
    propagate(world)
    if world.get("case").meters["clue_found"] >= THRESHOLD:
        world.say(case_cfg.clue_text)
    if world.get("case").meters["solved"] >= THRESHOLD:
        world.say(case_cfg.reveal_text)
    world.facts["shared"] = True
    world.facts["solver_pair"] = (a, b)
    world.facts["tool_cfg"] = tool_cfg


def restore(world: World, a: Entity, b: Entity, parent: Entity, case_cfg: MysteryCase) -> None:
    world.say(case_cfg.ending_text)
    world.say(
        f'{a.id} and {b.id} grinned at each other. The garden center did not feel spooky anymore; it felt bright, leafy, and full of small solved secrets.'
    )
    world.say(
        f'"Next time, we share first," {b.id} said, and even {parent.label_word} smiled at that.'
    )


def tell(
    case_cfg: MysteryCase,
    tool_cfg: ToolDef,
    child1_name: str,
    child1_gender: str,
    child2_name: str,
    child2_gender: str,
    parent_type: str,
    holder_id: str,
) -> World:
    world = World()
    a = world.add(Entity(id=child1_name, kind="character", type=child1_gender, role="child1"))
    b = world.add(Entity(id=child2_name, kind="character", type=child2_gender, role="child2"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    case_ent = world.add(Entity(id="case", kind="thing", type="mystery", label=case_cfg.missing_item))
    tool_ent = world.add(Entity(id="tool", kind="thing", type="tool", label=tool_cfg.label))
    world.add(Entity(id="team", kind="thing", type="team", label="the team"))

    world.facts.update(
        child1=a,
        child2=b,
        parent=parent,
        case_cfg=case_cfg,
        tool_cfg=tool_cfg,
        tool_works=tool_fits(case_cfg, tool_cfg),
        shared=False,
    )

    introduce(world, a, b, parent)
    notice_mystery(world, a, b, case_cfg)

    world.para()
    holder = a if holder_id == "child1" else b
    other = b if holder is a else a
    choose_tool(world, holder, other, tool_cfg)
    nudge_to_share(world, parent, holder, other, tool_cfg)

    world.para()
    search_together(world, a, b, case_cfg, tool_cfg)
    restore(world, a, b, parent, case_cfg)

    world.facts.update(
        holder=holder,
        other=other,
        solved=case_ent.meters["solved"] >= THRESHOLD,
        clue_found=case_ent.meters["clue_found"] >= THRESHOLD,
        culprit=case_cfg.culprit,
        hiding_place=case_cfg.hiding_place,
    )
    return world


KNOWLEDGE = {
    "magnifier": [
        (
            "What does a magnifying glass do?",
            "A magnifying glass makes tiny things look bigger, so small marks and little clues are easier to see.",
        )
    ],
    "stool": [
        (
            "Why do people use a step stool?",
            "A step stool helps you reach something a little higher in a safer way. A grown-up should make sure it is steady.",
        )
    ],
    "wagon": [
        (
            "What is a wagon useful for in a garden center?",
            "A wagon can carry pots and tools from one place to another. It helps when there are several things to move together.",
        )
    ],
    "sharing": [
        (
            "Why does sharing help with a mystery?",
            "Sharing lets two people look, think, and help at the same time. Working together often solves a problem faster than one person trying alone.",
        )
    ],
    "kitten": [
        (
            "Why might a kitten bat at little paper labels?",
            "Kittens love small moving things. A light paper tag can look like a toy to them.",
        )
    ],
    "wind": [
        (
            "How can wind move light things in a garden center?",
            "A gust of wind can lift or toss something light, especially if it hangs loose. That is why ribbons and spinners can end up in surprising places.",
        )
    ],
    "pots": [
        (
            "Why are little plant pots easy to move by mistake?",
            "Small pots are light and easy to pick up or nudge aside. In a busy place, someone can move them and forget to put them back.",
        )
    ],
}

KNOWLEDGE_ORDER = ["sharing", "magnifier", "stool", "wagon", "kitten", "wind", "pots"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    case_cfg = f["case_cfg"]
    tool_cfg = f["tool_cfg"]
    return [
        (
            f'Write a short mystery story for a 3-to-5-year-old set in a garden center. '
            f'Include the words "razor" and "nappie", and make sharing the key to solving what happened to {case_cfg.missing_item}.'
        ),
        (
            f"Tell a gentle mystery where {a.id} and {b.id} first struggle over {tool_cfg.label}, "
            f"then share it and discover that {case_cfg.culprit} hid {case_cfg.missing_item}."
        ),
        (
            f"Write a child-facing story with a leafy, curious feeling: something is missing at a garden center, "
            f"two children work together, and the ending shows the mystery solved at {case_cfg.hiding_place}."
        ),
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    return "a girl and a boy"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    parent = f["parent"]
    case_cfg = f["case_cfg"]
    tool_cfg = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.id} and {b.id}, visiting a garden center with their {parent.label_word}. They notice that {case_cfg.missing_item} is missing and decide to investigate.",
        ),
        (
            "What was the mystery?",
            f"The mystery was that {case_cfg.missing_item} had disappeared. That odd empty place made the children stop and start asking careful questions.",
        ),
        (
            f"Why did the mystery feel harder at first?",
            f"It felt harder because only one useful tool was nearby, and one child grabbed it first instead of sharing. That left the other child out and slowed the search down.",
        ),
        (
            f"How did sharing help {a.id} and {b.id} solve the mystery?",
            f"They shared the {tool_cfg.label}, so both children could search together instead of one child trying alone. Once they worked as a team, they found the clue and understood that {case_cfg.culprit} had put the missing thing at {case_cfg.hiding_place}.",
        ),
        (
            "How did the story end?",
            f"The children put things right together and the garden center felt calm again. The ending shows that sharing changed the whole mood from stuck and puzzled to proud and relieved.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    case_cfg = f["case_cfg"]
    tool_cfg = f["tool_cfg"]
    tags = {"sharing"} | set(tool_cfg.tags)
    if "kitten" in case_cfg.tags:
        tags.add("kitten")
    if "wind" in case_cfg.tags:
        tags.add("wind")
    if "pots" in case_cfg.tags or "herbs" in case_cfg.tags:
        tags.add("pots")
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
    for ent in world.entities.values():
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for (n, *_) in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(C, T) :- mystery_case(C), tool(T), need(C, N), solves(T, N).

solvable :- chosen_case(C), chosen_tool(T), valid(C, T).
outcome(solved) :- solvable.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for case_id, case_cfg in CASES.items():
        lines.append(asp.fact("mystery_case", case_id))
        lines.append(asp.fact("need", case_id, case_cfg.need))
    for tool_id, tool_cfg in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for need in sorted(tool_cfg.solves):
            lines.append(asp.fact("solves", tool_id, need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_case", params.case),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    items = asp.atoms(model, "outcome")
    return items[0][0] if items else "?"


def outcome_of(params: StoryParams) -> str:
    case_cfg = CASES.get(params.case)
    tool_cfg = TOOLS.get(params.tool)
    if not case_cfg or not tool_cfg:
        return "?"
    return "solved" if tool_fits(case_cfg, tool_cfg) else "?"


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

    for params in CURATED:
        py_out = outcome_of(params)
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            rc = 1
            print(f"MISMATCH outcome for {params.case}/{params.tool}: python={py_out} clingo={asp_out}")

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story or "{" in sample.story or "}" in sample.story:
            raise StoryError("smoke test produced broken story text")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Garden-center mystery storyworld. Two children solve a small mystery by sharing one useful tool."
    )
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible case/tool pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.case and args.tool:
        case_cfg = CASES[args.case]
        tool_cfg = TOOLS[args.tool]
        if not tool_fits(case_cfg, tool_cfg):
            raise StoryError(explain_rejection(case_cfg, tool_cfg))

    combos = [
        combo
        for combo in valid_combos()
        if (args.case is None or combo[0] == args.case)
        and (args.tool is None or combo[1] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    case_id, tool_id = rng.choice(sorted(combos))
    child1_name, child1_gender = _pick_child(rng)
    child2_name, child2_gender = _pick_child(rng, avoid=child1_name)
    parent = args.parent or rng.choice(["mother", "father"])
    holder = rng.choice(["child1", "child2"])
    return StoryParams(
        case=case_id,
        tool=tool_id,
        child1_name=child1_name,
        child1_gender=child1_gender,
        child2_name=child2_name,
        child2_gender=child2_gender,
        parent=parent,
        holder=holder,
    )


def generate(params: StoryParams) -> StorySample:
    case_cfg = CASES.get(params.case)
    tool_cfg = TOOLS.get(params.tool)
    if case_cfg is None:
        raise StoryError(f"(Unknown case: {params.case})")
    if tool_cfg is None:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if not tool_fits(case_cfg, tool_cfg):
        raise StoryError(explain_rejection(case_cfg, tool_cfg))

    world = tell(
        case_cfg=case_cfg,
        tool_cfg=tool_cfg,
        child1_name=params.child1_name,
        child1_gender=params.child1_gender,
        child2_name=params.child2_name,
        child2_gender=params.child2_gender,
        parent_type=params.parent,
        holder_id=params.holder,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (case, tool) pairs:\n")
        for case_id, tool_id in combos:
            print(f"  {case_id:12} {tool_id}")
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
            header = f"### {p.case} with {p.tool} ({p.child1_name} and {p.child2_name})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
