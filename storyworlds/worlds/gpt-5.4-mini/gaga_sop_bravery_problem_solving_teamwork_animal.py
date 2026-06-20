#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gaga_sop_bravery_problem_solving_teamwork_animal.py
===================================================================================

A standalone story world for a tiny animal adventure about bravery, problem
solving, and teamwork.

Seed inspiration:
- Words: gaga, sop
- Style: Animal Story
- Features: Bravery, Problem Solving, Teamwork

Premise:
A small animal group hears a strange sound in a low marshy place and must work
together to cross it safely, help a stuck friend, and end with a cozy, earned
reward.

This file is self-contained and follows the Storyweavers contract:
- typed entities with meters and memes
- a Python reasonableness gate
- inline ASP twin
- default / -n / --all / --seed / --trace / --qa / --json / --asp / --verify / --show-asp
- generated stories, prompts, story QA, and world QA all grounded in simulated state
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "she"}
        male = {"boy", "father", "dad", "man", "he"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    wet: bool = False
    muddy: bool = False
    deep: bool = False


@dataclass
class Animal:
    id: str
    species: str
    label: str
    role: str
    brave: int
    clever: int
    kind: str = "character"
    type: str = "animal"
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Challenge:
    id: str
    label: str
    problem: str
    risk: str
    fix_kind: str
    reward: str
    depth: int
    wet: bool = False
    muddy: bool = False


@dataclass
class Tool:
    id: str
    label: str
    helpful_for: str
    effect: str


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


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for animal in world.characters():
        if animal.meters["soggy"] < THRESHOLD:
            continue
        sig = ("soak", animal.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        animal.memes["unease"] += 1
        out.append("__soak__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if sum(a.memes["helping"] for a in world.characters()) >= 2:
        sig = ("teamwork",)
        if sig not in world.fired:
            world.fired.add(sig)
            for a in world.characters():
                a.memes["pride"] += 1
            out.append("__team__")
    return out


CAUSAL_RULES = [Rule("soak", "physical", _r_soak), Rule("teamwork", "social", _r_teamwork)]


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


def hazard_at_risk(challenge: Challenge, place: Place) -> bool:
    return (challenge.wet and place.wet) or (challenge.muddy and place.muddy) or challenge.depth <= 2


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.id in {"reed_pole", "rope", "boat"}]


def best_tool() -> Tool:
    return max(TOOLS.values(), key=lambda t: 3 if t.id in {"reed_pole", "rope", "boat"} else 1)


def rescue_needed(challenge: Challenge, delay: int) -> bool:
    return challenge.depth + delay >= 3


def can_solve(tool: Tool, challenge: Challenge, delay: int) -> bool:
    return tool.helpful_for == challenge.fix_kind and not (challenge.depth + delay > 4 and tool.id == "reed_pole")


def _do_problem(world: World, target: Entity) -> None:
    target.meters["stuck"] += 1
    target.meters["soggy"] += 1
    propagate(world, narrate=False)


def setup(world: World, a: Entity, b: Entity, c: Entity, place: Place, challenge: Challenge) -> None:
    a.memes["bravery"] += a.attrs.get("bravery", 1)
    b.memes["cleverness"] += b.attrs.get("cleverness", 1)
    c.memes["kindness"] += 1
    world.say(
        f"On a bright morning, {a.id}, {b.id}, and {c.id} met by {place.label}. "
        f"The little animals liked to explore there, even when the ground felt {('sop-soggy' if place.wet else 'soft')}."
    )
    world.say(
        f"They had come to look for {challenge.reward}, but the path led toward a {challenge.label}."
    )


def prompt_problem(world: World, a: Entity, challenge: Challenge) -> None:
    world.say(
        f"Then they heard a funny sound: gaga, gaga, from the reeds. "
        f"{a.id} peeked forward and saw that the way was {challenge.problem}."
    )


def brave_choice(world: World, a: Entity, b: Entity, c: Entity, tool: Tool) -> None:
    a.memes["bravery"] += 1
    b.memes["cleverness"] += 1
    c.memes["helping"] += 1
    world.say(
        f'"We can do this," said {a.id}. {b.id} nodded, and {c.id} hurried to bring {tool.label}. '
        f"Together, they made a plan instead of panicking."
    )


def use_tool(world: World, tool: Tool, challenge: Challenge, target: Entity) -> None:
    target.memes["helping"] += 1
    if tool.id == "rope":
        world.say(
            f"{tool.label.capitalize()} went around the branch first, then under {target.id}, "
            f"and the others pulled gently and steadily."
        )
    elif tool.id == "boat":
        world.say(
            f"{tool.label.capitalize()} slid into the water like a leaf, and the animals climbed in one by one."
        )
    else:
        world.say(
            f"{tool.label.capitalize()} made a strong path where the mud had been too deep to cross."
        )
    world.say(f"They used the {tool.label} to solve the problem without making the {challenge.label} worse.")


def free_friend(world: World, target: Entity) -> None:
    target.meters["stuck"] = 0.0
    target.memes["relief"] += 1
    target.memes["joy"] += 1
    world.say(
        f"At last, {target.id} popped free with a wet little laugh. The friend shook off the muck and stood tall again."
    )


def ending(world: World, a: Entity, b: Entity, c: Entity, challenge: Challenge) -> None:
    for animal in (a, b, c):
        animal.memes["joy"] += 1
        animal.memes["pride"] += 1
    world.say(
        f"They crossed safely and found {challenge.reward} waiting beyond the reeds. "
        f"{a.id} felt brave, {b.id} felt clever, and {c.id} smiled at the teamwork that made the day turn good."
    )
    world.say(
        f"That evening, the three friends sat dry on a warm stone and listened as the marsh said gaga again, "
        f"but now it sounded friendly."
    )


def tell(place: Place, challenge: Challenge, tool: Tool,
         hero: str = "Momo", helper: str = "Pip", friend: str = "Gigi") -> World:
    world = World()
    a = world.add(Entity(id=hero, kind="character", type="animal", label=hero, role="brave", attrs={"bravery": 2}))
    b = world.add(Entity(id=helper, kind="character", type="animal", label=helper, role="solver", attrs={"cleverness": 2}))
    c = world.add(Entity(id=friend, kind="character", type="animal", label=friend, role="helper"))
    stuck = world.add(Entity(id="stuck_friend", kind="character", type="animal", label=friend))
    _ = world.add(Entity(id="tool", type="tool", label=tool.label))
    world.facts["place"] = place
    world.facts["challenge"] = challenge
    world.facts["tool"] = tool
    world.facts["animals"] = (a, b, c)

    setup(world, a, b, c, place, challenge)
    world.para()
    prompt_problem(world, a, challenge)
    brave_choice(world, a, b, c, tool)
    if can_solve(tool, challenge, 0):
        world.para()
        use_tool(world, tool, challenge, stuck)
        free_friend(world, stuck)
        ending(world, a, b, c, challenge)
        outcome = "solved"
    else:
        world.say("The plan was brave, but the tool was not strong enough.")
        outcome = "failed"
    world.facts["outcome"] = outcome
    world.facts["friend"] = stuck
    return world


PLACES = {
    "marsh": Place("marsh", "the marsh", wet=True, muddy=True, deep=True),
    "pond": Place("pond", "the pond", wet=True, muddy=False, deep=True),
    "riverbank": Place("riverbank", "the riverbank", wet=True, muddy=True, deep=True),
}

CHALLENGES = {
    "reed_crossing": Challenge("reed_crossing", "reed crossing", "blocked by slippery mud", "sinking in the muck", "rope", "a basket of berries", 3, wet=True, muddy=True),
    "log_bridge": Challenge("log_bridge", "log bridge", "wobbly and wet", "falling into the water", "boat", "a patch of lilies", 3, wet=True),
    "deep_mud": Challenge("deep_mud", "mud hole", "too deep to stomp through", "getting stuck", "reed_pole", "a hidden trail", 2, muddy=True),
}

TOOLS = {
    "rope": Tool("rope", "a rope", "rope", "ties the group together"),
    "boat": Tool("boat", "a tiny boat", "boat", "carries them over"),
    "reed_pole": Tool("reed_pole", "a reed pole", "reed_pole", "pries a friend free"),
    "net": Tool("net", "a fishing net", "net", "looks useful but is too weak"),
}

CURATED = [
    ("marsh", "reed_crossing", "rope"),
    ("pond", "log_bridge", "boat"),
    ("riverbank", "deep_mud", "reed_pole"),
]


@dataclass
class StoryParams:
    place: str
    challenge: str
    tool: str
    hero: str = "Momo"
    helper: str = "Pip"
    friend: str = "Gigi"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for c in CHALLENGES:
            for t in TOOLS:
                if hazard_at_risk(CHALLENGES[c], PLACES[p]) and can_solve(TOOLS[t], CHALLENGES[c], 0):
                    out.append((p, c, t))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, c = f["animals"]
    ch = f["challenge"]
    return [
        f'Write an animal story that includes the words "gaga" and "sop" and shows {a.id}, {b.id}, and {c.id} working together.',
        f"Tell a brave little animal adventure where a friend gets stuck in a {ch.label}, and the group solves it with teamwork.",
        f'Write a child-friendly story about bravery and problem solving that ends with a cozy success image in a marshy place.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, c = f["animals"]
    ch = f["challenge"]
    tool = f["tool"]
    friend = f["friend"]
    out = [
        ("Who are the story about?",
         f"The story is about {a.id}, {b.id}, and {c.id}, three little animals who stay together and help each other."),
        ("What problem did they face?",
         f"They found a {ch.label} that was {ch.problem}. One friend got stuck, so they had to think carefully and act bravely."),
        ("How did they fix the problem?",
         f"They used {tool.label} and made a plan together. {a.id} led with bravery, {b.id} solved the tricky part, and {c.id} helped pull until {friend.id} was free."),
    ]
    if f["outcome"] == "solved":
        out.append((
            "How did the friends feel at the end?",
            f"They felt proud, happy, and safe. The hard part was solved, and their teamwork made the day turn into a good memory."
        ))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does teamwork mean?",
         "Teamwork means people or animals help each other and do different jobs together so a hard job becomes easier."),
        ("What is bravery?",
         "Bravery means doing something even when you feel a little scared, because it is the right thing to do."),
        ("What is problem solving?",
         "Problem solving means thinking about a trouble and finding a smart way to fix it."),
        ("What is a marsh like?",
         "A marsh is wet ground with reeds, mud, and shallow water, so it can be slippery and tricky to cross."),
    ]


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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(P, C) :- place(P), challenge(C), wet_place(P), wet_challenge(C).
hazard(P, C) :- place(P), challenge(C), muddy_place(P), muddy_challenge(C).
valid(P, C, T) :- hazard(P, C), tool(T), fixes(T, C).
solved(C) :- chosen_tool(T), chosen_challenge(C), fixes(T, C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.wet:
            lines.append(asp.fact("wet_place", pid))
        if p.muddy:
            lines.append(asp.fact("muddy_place", pid))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        if c.wet:
            lines.append(asp.fact("wet_challenge", cid))
        if c.muddy:
            lines.append(asp.fact("muddy_challenge", cid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("fixes", tid, t.helpful_for))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_tool", params.tool), asp.fact("chosen_challenge", params.challenge)])
    model = asp.one_model(asp_program(extra, "#show solved/1."))
    return "solved" if asp.atoms(model, "solved") else "failed"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos")
    smoke = generate(resolve_params(argparse.Namespace(place=None, challenge=None, tool=None, seed=None), random.Random(7)))
    if not smoke.story:
        rc = 1
        print("SMOKE TEST FAILED")
    print("OK" if rc == 0 else "FAIL")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about bravery, problem solving, and teamwork.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--tool", choices=TOOLS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, challenge, tool = rng.choice(sorted(combos))
    return StoryParams(place, challenge, tool)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], CHALLENGES[params.challenge], TOOLS[params.tool], params.hero, params.helper, params.friend)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(*c)) for c in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
