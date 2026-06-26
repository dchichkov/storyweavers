#!/usr/bin/env python3
"""
Story world: a small Animal Story with a fisher, a problem, and a twist.

Seed tale imagined from the prompt:
A fisher named Fern lives near a quiet creek. Fern is proud of her clever paws and loves helping her friends. One morning, the beavers' dam springs a leak after a storm, and the creek starts to spill into their den. Fern tries one fix, but it fails in a surprising way. Then she notices a better idea: use the loose sticks to make a new path for the water. The animals work together, the water settles, and the beavers get their home back.

This world turns that tale into a tiny simulation:
- typed animal entities with physical meters and emotional memes,
- a problem that changes state when water rises,
- a twist that changes which solution is possible,
- a resolution that proves the state changed.

The script intentionally keeps the domain small and constraint-checked:
fewer valid story variants are better than a weak one.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fisher", "fox", "beaver", "otter", "mouse", "rabbit", "squirrel"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    name: str
    places: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    source: str
    effect: str
    twist: str
    risk_region: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    moves: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.events: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.events = list(self.events)
        return clone


SETTINGS = {
    "creek": Setting(name="the creek", places={"bank", "water", "den"}),
    "woods": Setting(name="the woods", places={"bank", "water", "den"}),
}

PROBLEMS = {
    "leak": Problem(
        id="leak",
        label="a leak in the beaver dam",
        source="the dam crack",
        effect="water rushed into the beavers' den",
        twist="the loose sticks could guide the water away",
        risk_region="den",
        keyword="leak",
        tags={"water", "stick"},
    ),
    "mudslide": Problem(
        id="mudslide",
        label="a muddy slide on the bank",
        source="the rain-soaked hill",
        effect="mud slid toward the little nest",
        twist="the roots could hold the mud in place",
        risk_region="bank",
        keyword="mud",
        tags={"mud", "root"},
    ),
}

TOOLS = {
    "sticks": Tool(
        id="sticks",
        label="loose sticks",
        phrase="a pile of loose sticks",
        helps={"leak"},
        moves="build a little channel",
    ),
    "roots": Tool(
        id="roots",
        label="tree roots",
        phrase="thick tree roots",
        helps={"mudslide"},
        moves="brace the hillside",
    ),
}

CURIOUS_ANIMALS = ["fisher", "otter", "fox", "rabbit", "beaver", "squirrel"]
NAMES = ["Fern", "Milo", "Pip", "Hazel", "Nina", "Jasper", "Tilly", "Rory"]
TRAITS = ["clever", "gentle", "brave", "quick", "curious"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    name: str
    friend: str
    trait: str
    seed: Optional[int] = None


@dataclass
class State:
    actor: Entity
    friend: Entity
    problem: Entity
    tool: Entity
    solved: bool = False
    twisted: bool = False


def viable(problem: Problem, tool: Tool) -> bool:
    return problem.id in tool.helps


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for p in sorted(s.places):
            lines.append(asp.fact("place", sid, p))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("risk_region", pid, p.risk_region))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for g in sorted(t.helps):
            lines.append(asp.fact("helps", tid, g))
    return "\n".join(lines)


ASP_RULES = r"""
can_solve(P,T) :- problem(P), tool(T), helps(T,P).
good_story(S,P,T) :- setting(S), problem(P), tool(T), can_solve(P,T).
#show good_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show good_story/3."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = {(sid, pid, tid) for sid in SETTINGS for pid, p in PROBLEMS.items() for tid, t in TOOLS.items() if viable(p, t)}
    cl = set(asp_valid_combos())
    if cl == py:
        print(f"OK: clingo gate matches viable() ({len(cl)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal-story world with a fisher, a problem, and a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = []
    for sid, setting in SETTINGS.items():
        if args.setting and sid != args.setting:
            continue
        for pid, prob in PROBLEMS.items():
            if args.problem and pid != args.problem:
                continue
            for tid, tool in TOOLS.items():
                if args.tool and tid != args.tool:
                    continue
                if viable(prob, tool):
                    combos.append((sid, pid, tid))
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    sid, pid, tid = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=sid, problem=pid, tool=tid, name=name, friend=friend, trait=trait)


def predict(world: World, actor: Entity, problem: Problem, tool: Tool) -> dict:
    sim = world.copy()
    a = sim.get(actor.id)
    if problem.id == "leak":
        a.meters["water"] += 1
    else:
        a.meters["mud"] += 1
    return {"twist": True, "needs_tool": True}


def tell(setting: Setting, problem: Problem, tool: Tool, name: str, friend: str, trait: str) -> World:
    world = World(setting)
    fisher = world.add(Entity(id=name, kind="character", type="fisher"))
    pal = world.add(Entity(id=friend, kind="character", type="beaver" if problem.id == "leak" else "otter"))
    prob = world.add(Entity(id="problem", type="problem", label=problem.label, location="bank"))
    item = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, plural=tool.plural))
    item.location = "bank"

    fisher.memes["care"] = 1
    pal.memes["worry"] = 1

    world.say(f"{fisher.id} was a {trait} fisher who lived near {setting.name}.")
    world.say(f"{fisher.id} liked helping {pal.id} when trouble came to the water.")

    world.para()
    world.say(f"One morning, {problem.label} made a hard problem.")
    if problem.id == "leak":
        world.say("Water slipped through the dam and crept toward the beavers' den.")
    else:
        world.say("Mud slid down the bank and began to crowd the little nesting place.")
    fisher.memes["alert"] = 1
    pal.memes["worry"] = 2

    world.para()
    world.say(f"{fisher.id} first tried to fix it by pushing at the edge alone, but that did not work.")
    world.say(f"Then {problem.twist}.")

    world.para()
    fisher.memes["hope"] = 1
    world.say(f"{fisher.id} had a better idea: use {tool.label} to {tool.moves}.")
    world.say(f"{pal.id} gathered the pieces, and together they worked carefully.")

    world.para()
    if problem.id == "leak":
        world.say("The sticks nudged the water into a little side stream, and the den stayed dry.")
        pal.meters["safe"] = 1
    else:
        world.say("The roots held the mud back, and the tiny nest stayed clear.")
        pal.meters["safe"] = 1
    world.say(f"{fisher.id} smiled when the problem finally settled down.")
    world.say(f"{pal.id} chirped happily, and the creek was calm again.")

    world.facts.update(actor=fisher, friend=pal, problem=problem, tool=item, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story for a child about a {f["actor"].type} named {f["actor"].id} helping a friend near {f["setting"].name}.',
        f"Tell a gentle story where a fisher solves {f['problem'].label} with {f['tool'].label} and a twist changes the plan.",
        f'Write a simple story that includes the word "{f["problem"].keyword}" and ends with the animals safe and happy.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    actor, friend, problem, tool = f["actor"], f["friend"], f["problem"], f["tool"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {actor.id}, a clever fisher who helps {friend.id} near {f['setting'].name}.",
        ),
        QAItem(
            question=f"What problem did the animals have?",
            answer=f"They had {problem.label}. It made trouble until {actor.id} found a better way to fix it.",
        ),
        QAItem(
            question=f"What tool helped solve the problem?",
            answer=f"{tool.label} helped solve the problem because it let the animals guide the water or hold the mess in place.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {problem.twist}. That changed the problem into something {actor.id} could solve.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the problem settled, {friend.id} safe, and {actor.id} smiling because the fix worked.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fisher?",
            answer="A fisher is a furry animal that lives in the woods and can climb and hunt well.",
        ),
        QAItem(
            question="Why do animals work together when something is wrong?",
            answer="Animals work together because many small helpers can solve a problem faster than one animal alone.",
        ),
        QAItem(
            question="What does it mean to make a better plan?",
            answer="It means stopping for a moment, thinking again, and choosing a fix that works more safely.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], TOOLS[params.tool], params.name, params.friend, params.trait)
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
    StoryParams(setting="creek", problem="leak", tool="sticks", name="Fern", friend="Bram", trait="clever"),
    StoryParams(setting="woods", problem="mudslide", tool="roots", name="Fern", friend="Otis", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for sid, pid, tid in combos:
            print(f"  {sid:6} {pid:10} {tid:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
