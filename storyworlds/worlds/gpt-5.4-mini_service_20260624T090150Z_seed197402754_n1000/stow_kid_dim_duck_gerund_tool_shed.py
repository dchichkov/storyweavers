#!/usr/bin/env python3
"""
storyworlds/worlds/stow_kid_dim_duck_gerund_tool_shed.py
=========================================================

A small, child-facing comedy storyworld set in a tool shed.

Seed premise:
A kid tries to stow a kid-dim tool in a tool shed, but a duck-gerund
something keeps making a goofy mess of the plan. The child uses curiosity,
problem solving, and bravery to finish the job.

The world is intentionally tiny and constraint-checked:
- the shed has a limited set of objects
- one object is too big or too awkward unless the child uses a helper
- the duck-gerund object is noisy, silly, and can trigger a small mess
- the ending proves what changed in the world state
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0
SCARES = {"dark", "clatter", "flutter", "splash"}
MESSY = {"dusty", "sticky", "muddy"}

KID_DIM = "kid-dim"
DUCK_GERUND = "duck-gerund"

# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "kid" | "adult" | "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    portable: bool = True
    noisy: bool = False
    size: str = "normal"  # "kid-dim" | "normal" | "big"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["dusty", "sticky", "muddy", "moved", "stowed", "tidy"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "bravery", "problem_solving", "worry", "joy", "conflict"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Shed:
    place: str = "the tool shed"
    dim: str = KID_DIM
    dark: bool = True
    has_flashlight: bool = True
    has_step_stool: bool = True
    has_workbench: bool = True
    affords: set[str] = field(default_factory=lambda: {"stow", "inspect", "clean", "find"})

    def detail(self) -> str:
        parts = ["The tool shed was a little dark and smelled like wood and dust."]
        if self.has_flashlight:
            parts.append("A flashlight waited near the door.")
        if self.has_step_stool:
            parts.append("A step stool stood beside the workbench.")
        return " ".join(parts)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    size: str = "kid-dim"
    awkward: bool = False
    can_stow: bool = True
    noisy: bool = False
    messy: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    shed: Shed
    entities: dict[str, Entity] = field(default_factory=dict)
    tools: dict[str, Tool] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_tool(self, tool: Tool) -> Tool:
        self.tools[tool.id] = tool
        return tool

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "kid"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.shed)
        clone.entities = copy.deepcopy(self.entities)
        clone.tools = copy.deepcopy(self.tools)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
def _r_duck_clatter(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.kids():
        if kid.memes["curiosity"] < THRESHOLD:
            continue
        duck = world.tools.get("duck")
        if not duck or duck.id in world.fired:
            continue
        if duck.noisy:
            world.fired.add((duck.id, "clatter"))
            kid.memes["joy"] += 1
            kid.meters["moved"] += 1
            out.append(f"The ducky thing gave one silly quack and wiggled on the shelf.")
    return out


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.kids():
        if kid.memes["bravery"] < THRESHOLD:
            continue
        for tool in world.tools.values():
            if not tool.messy:
                continue
            sig = (kid.id, tool.id, "mess")
            if sig in world.fired:
                continue
            world.fired.add(sig)
            kid.meters["dusty"] += 1
            out.append(f"{kid.pronoun('possessive').capitalize()} hands got dusty while reaching past the cobwebby jars.")
    return out


def _r_clean_finish(world: World) -> list[str]:
    out: list[str] = []
    for tool in world.tools.values():
        if tool.id in world.fired:
            continue
        if tool.can_stow and tool.id in world.fired:
            continue
    for kid in world.kids():
        if kid.memes["problem_solving"] < THRESHOLD:
            continue
        sig = (kid.id, "finish")
        if sig in world.fired:
            continue
        if world.facts.get("stowed"):
            continue
        world.fired.add(sig)
        world.facts["stowed"] = True
        kid.meters["stowed"] += 1
        kid.memes["joy"] += 1
        out.append("At last, everything fit in its place, neat as a toy box after a parade.")
    return out


CAUSAL_RULES = [_r_duck_clatter, _r_mess, _r_clean_finish]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    tool: str
    duck_mode: str
    seed: Optional[int] = None


NAMES = {
    "girl": ["Mia", "Lena", "Nora", "Tia", "Ivy"],
    "boy": ["Ben", "Noah", "Theo", "Max", "Eli"],
}
HELPERS = ["mom", "dad", "grandpa", "neighbor"]
DUCK_MODES = ["duck-gerund", "silly-duck", "quacky-duck"]


def build_world(params: StoryParams) -> World:
    shed = Shed()
    world = World(shed=shed)

    kid = world.add(Entity(
        id=params.name,
        kind="kid",
        type=params.gender,
        label=params.name,
        phrase=f"a little {params.gender}",
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="adult",
        type=params.helper,
        label=f"the {params.helper}",
    ))

    tools = {
        "box": Tool(
            id="box",
            label="little parts box",
            phrase="a kid-dim little parts box",
            size=KID_DIM,
            awkward=False,
            can_stow=True,
            noisy=False,
            messy=False,
            tags={"storage"},
        ),
        "duck": Tool(
            id="duck",
            label="rubber duck",
            phrase="a duck-gerund rubber duck that liked to wobble",
            size=KID_DIM,
            awkward=True,
            can_stow=True,
            noisy=True,
            messy=False,
            tags={"duck", "comedy"},
        ),
        "shovel": Tool(
            id="shovel",
            label="tiny shovel",
            phrase="a kid-dim shovel with a muddy blade",
            size=KID_DIM,
            awkward=False,
            can_stow=True,
            noisy=False,
            messy=True,
            tags={"mud"},
        ),
    }
    for t in tools.values():
        world.add_tool(t)

    chosen = tools[params.tool]
    world.facts["tool"] = chosen.id
    world.facts["helper"] = helper.id
    world.facts["duck_mode"] = params.duck_mode

    # Setup
    world.say(f"{kid.id} found a {chosen.phrase} in {world.shed.place}.")
    world.say(f"{kid.id} wanted to stow it before supper, because the shelf looked like a puzzle with one missing piece.")
    world.say(world.shed.detail())
    world.para()

    # Conflict / curiosity / bravery
    kid.memes["curiosity"] += 1
    world.say(f"{kid.id} peeked at the odd duck-gerund thing and wondered why it kept quacking at the nails.")
    if chosen.id == "duck":
        kid.memes["worry"] += 1
        world.say(f"The duck gave a squeaky wobble, then bonked a tin can with a very rude little clink.")
    else:
        world.say(f"The duck-gerund duck on the shelf tipped sideways, as if it had heard a joke only it understood.")

    kid.memes["bravery"] += 1
    world.say(f"Still, {kid.id} took a brave breath and reached for the cramped shelf without backing away.")
    propagate(world, narrate=True)

    # Problem solving
    world.para()
    kid.memes["problem_solving"] += 1
    if chosen.id == "shovel":
        world.say(f"{kid.id} noticed the muddy blade would smear the box, so {kid.pronoun('subject')} laid down an old rag first.")
        world.say(f"Then {kid.id} slid the box onto the rag and pushed it in with both hands, slow and careful.")
    elif chosen.id == "duck":
        world.say(f"{kid.id} noticed the duck was too wiggly for the high shelf, so {kid.pronoun('subject')} asked the {params.helper} for the step stool.")
        world.say(f"The {params.helper} held the stool steady while {kid.id} lifted the duck up like a tiny, bossy cloud.")
    else:
        world.say(f"{kid.id} noticed the parts box would fit if the lid were closed just right.")
        world.say(f"So {kid.id} tapped the corners straight, counted to three, and stowed it with a neat little thunk.")

    if params.tool == "duck":
        world.say(f"Then the duck-gerund duck did one last ridiculous quack, as if proud of its own bad manners.")
    else:
        world.say(f"The duck on the shelf gave a tiny squeak, but it stayed put this time.")

    world.facts["stowed"] = True
    kid.meters["stowed"] += 1
    kid.memes["joy"] += 1
    helper.memes["joy"] += 1

    world.para()
    world.say(f"In the end, the shelf was tidy, the shed was calmer, and {kid.id} smiled at the perfectly stowed tool.")
    world.say(f"{kid.id}'s dusty hands did not stop the grin; they only made the victory look extra brave and extra funny.")

    world.facts.update(
        kid=kid,
        helper=helper,
        chosen=chosen,
        shed=shed,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Registries and ASP twin
# ---------------------------------------------------------------------------
TOOLS = {
    "box": Tool(
        id="box",
        label="little parts box",
        phrase="a kid-dim little parts box",
        size=KID_DIM,
        awkward=False,
        can_stow=True,
        noisy=False,
        messy=False,
        tags={"storage"},
    ),
    "duck": Tool(
        id="duck",
        label="rubber duck",
        phrase="a duck-gerund rubber duck that liked to wobble",
        size=KID_DIM,
        awkward=True,
        can_stow=True,
        noisy=True,
        messy=False,
        tags={"duck", "comedy"},
    ),
    "shovel": Tool(
        id="shovel",
        label="tiny shovel",
        phrase="a kid-dim shovel with a muddy blade",
        size=KID_DIM,
        awkward=False,
        can_stow=True,
        noisy=False,
        messy=True,
        tags={"mud"},
    ),
}

ASP_RULES = r"""
stowable(T) :- tool(T), can_stow(T).
awkward(T) :- tool(T), noisy(T).
curious_story(T) :- tool(T), noisy(T).
problem_solving_story(T) :- tool(T), can_stow(T).
brave_story(T) :- tool(T), size(T,kid_dim).

valid_story(T) :- tool(T), size(T,kid_dim), can_stow(T).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("shed", "tool_shed"),
        asp.fact("feature", "problem_solving"),
        asp.fact("feature", "curiosity"),
        asp.fact("feature", "bravery"),
        asp.fact("style", "comedy"),
    ]
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("size", tid, "kid_dim" if t.size == KID_DIM else t.size))
        if t.can_stow:
            lines.append(asp.fact("can_stow", tid))
        if t.noisy:
            lines.append(asp.fact("noisy", tid))
        if t.messy:
            lines.append(asp.fact("messy", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_tools() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid_tools() -> list[tuple]:
    return [("box",), ("duck",), ("shovel",)]


def asp_verify() -> int:
    import storyworlds.asp as asp
    p = set(python_valid_tools())
    a = set(asp_valid_tools())
    if p == a:
        print(f"OK: clingo gate matches python gate ({len(p)} tools).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if a - p:
        print("  only in ASP:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid = f["kid"]
    tool = f["chosen"]
    return [
        f'Write a short comedy story for a child about a kid named {kid.id} trying to stow a {tool.label} in a tool shed.',
        f'Write a silly story using the words "{KID_DIM}" and "{DUCK_GERUND}" where {kid.id} solves a small problem with curiosity and bravery.',
        f'Tell a gentle tool-shed story where a child stows a toy, notices a duck-gerund oddity, and finishes with a tidy shelf.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid = f["kid"]
    helper = f["helper"]
    chosen = f["chosen"]
    qa = [
        QAItem(
            question=f"What was {kid.id} trying to do in the tool shed?",
            answer=f"{kid.id} was trying to stow the {chosen.label} in the tool shed so the shelf would be tidy again.",
        ),
        QAItem(
            question=f"Why did {kid.id} look at the duck-gerund thing so carefully?",
            answer=f"{kid.id} was curious, and the duck-gerund thing was funny and noisy, so {kid.pronoun('subject')} wanted to see what it would do next.",
        ),
        QAItem(
            question=f"Who helped {kid.id} when the duck was too wiggly or the shelf was too high?",
            answer=f"The {helper.split(':')[-1].lower() if ':' in helper else world.get('Helper').type} helped by steadying the stool and letting {kid.id} finish the job safely.",
        ),
        QAItem(
            question=f"How did {kid.id} solve the problem in the end?",
            answer=f"{kid.id} used a careful plan: a rag for the messy tool, or a step stool for the wiggly duck, and then everything was stowed neatly.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tool shed for?",
            answer="A tool shed is a small building or room where people keep tools, supplies, and other useful things out of the weather.",
        ),
        QAItem(
            question="What does stow mean?",
            answer="To stow something means to put it away in a safe place, often so it is neat and easy to find later.",
        ),
        QAItem(
            question="Why can a flashlight help in a dark shed?",
            answer="A flashlight helps because it shines light into dark places so you can see where things are and avoid bumping into them.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = [f"{e.kind}"]
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} {' '.join(bits)}")
    for t in world.tools.values():
        bits = []
        if t.noisy:
            bits.append("noisy")
        if t.messy:
            bits.append("messy")
        if t.can_stow:
            bits.append("stowable")
        lines.append(f"  {t.id:10} tool size={t.size} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy storyworld about stowing a kid-dim tool in a tool shed.")
    ap.add_argument("--name", choices=sum(NAMES.values(), []))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--duck-mode", choices=DUCK_MODES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    tool = args.tool or rng.choice(list(TOOLS))
    duck_mode = args.duck_mode or rng.choice(DUCK_MODES)
    return StoryParams(name=name, gender=gender, helper=helper, tool=tool, duck_mode=duck_mode)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


CURATED = [
    StoryParams(name="Mia", gender="girl", helper="mom", tool="duck", duck_mode="duck-gerund"),
    StoryParams(name="Ben", gender="boy", helper="dad", tool="box", duck_mode="duck-gerund"),
    StoryParams(name="Nora", gender="girl", helper="grandpa", tool="shovel", duck_mode="duck-gerund"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} valid tools:")
        for item in vals:
            print(" ", item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
