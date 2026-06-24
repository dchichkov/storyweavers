#!/usr/bin/env python3
"""
storyworlds/worlds/wicked_quarry_edge_teamwork_mystery_to_solve.py
==================================================================

A small folk-tale storyworld set at the quarry edge.

Premise:
- A wicked old miller has hidden a strange token near the quarry edge.
- A small group of friends must work together to solve a mystery.
- The story turns on sharing clues, asking for help, and trusting one another.

The world is deliberately narrow: fewer, stronger story variants are preferred
over broad but weak ones.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Shared result containers, imported eagerly per contract.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the quarry edge"
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    title: str
    clue: str
    hidden: str
    solved_by: str
    at_risk: str
    ask: str
    reveal: str


@dataclass
class Team:
    id: str
    name: str
    members: list[str]
    bond: str
    method: str
    ending: str


@dataclass
class StoryParams:
    mystery: str
    team: str
    hero1: str
    hero2: str
    hero3: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

    def copy(self) -> "World":
        clone = World(self.setting)
        import copy as _copy
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTING = Setting(place="the quarry edge", tags={"quarry", "edge", "folk tale", "mystery"})


MYSTERIES = {
    "lantern": Mystery(
        id="lantern",
        title="the missing lantern",
        clue="a pale glow on the stone",
        hidden="under a loose slate by the edge",
        solved_by="looking together and following the glow",
        at_risk="the path might be too dark at dusk",
        ask="Where did the lantern go?",
        reveal="the lantern had been tucked under a loose slate by the quarry edge",
    ),
    "bell": Mystery(
        id="bell",
        title="the little bell",
        clue="a tiny silver ring in the dust",
        hidden="inside a cracked bucket",
        solved_by="sharing the dust and tracing the sound",
        at_risk="the bell might be lost before the market day",
        ask="Who hid the little bell?",
        reveal="the bell was hidden inside a cracked bucket near the stones",
    ),
    "key": Mystery(
        id="key",
        title="the iron key",
        clue="a cold mark on a rope coil",
        hidden="beneath a mossy brick",
        solved_by="lifting together and checking every corner",
        at_risk="the old gate might stay locked",
        ask="Where is the iron key?",
        reveal="the iron key was tucked beneath a mossy brick at the quarry edge",
    ),
}

TEAMS = {
    "friends": Team(
        id="friends",
        name="three friends",
        members=["hero1", "hero2", "hero3"],
        bond="friendship",
        method="they shared clues and listened to one another",
        ending="they walked home as friends, glad that none had kept the secret alone",
    ),
}

NAMES = ["Mara", "Ned", "Pip", "Tess", "Ivo", "Una", "Finn", "Rose", "Jory", "Lina"]
TRAITS = ["brave", "curious", "kind", "quick", "steady", "gentle"]


def valid_combos() -> list[tuple[str, str]]:
    return [(m, t) for m in MYSTERIES for t in TEAMS]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("hidden", mid, m.hidden))
        lines.append(asp.fact("risk", mid, m.at_risk))
    for tid, t in TEAMS.items():
        lines.append(asp.fact("team", tid))
        lines.append(asp.fact("bond", tid, t.bond))
    lines.append(asp.fact("setting", "quarry_edge"))
    return "\n".join(lines)


ASP_RULES = r"""
solve(M, T) :- mystery(M), team(T), bond(T, friendship).
#show solve/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show solve/2."))
    return sorted(set(asp.atoms(model, "solve")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld at the quarry edge.")
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--team", choices=sorted(TEAMS))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.mystery:
        combos = [c for c in combos if c[0] == args.mystery]
    if args.team:
        combos = [c for c in combos if c[1] == args.team]
    if not combos:
        raise StoryError("No valid story matches those options.")
    mystery, team = rng.choice(sorted(combos))
    names = rng.sample(NAMES, 3)
    return StoryParams(
        mystery=mystery,
        team=team,
        hero1=names[0],
        hero2=names[1],
        hero3=names[2],
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    m: Mystery = f["mystery_obj"]
    names = f["names"]
    return [
        QAItem(
            question=f"Who came to the quarry edge to solve {m.title}?",
            answer=f"{names[0]}, {names[1]}, and {names[2]} came together as friends to solve {m.title}.",
        ),
        QAItem(
            question=f"What clue helped the friends solve the mystery?",
            answer=f"They noticed {m.clue}, and that clue led them to the hidden answer.",
        ),
        QAItem(
            question=f"Where was the answer hidden?",
            answer=f"The answer was hidden {m.hidden}.",
        ),
        QAItem(
            question=f"Why did they need teamwork?",
            answer=f"They needed teamwork because {m.at_risk}, so each friend had to listen and help with the search.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help one another and use their different strengths to do something together.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not understood at first and must be solved by looking for clues.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind bond between people who care about one another and enjoy being together.",
        ),
        QAItem(
            question="What is a quarry edge?",
            answer="A quarry edge is the side of a quarry, where stone has been dug out and the ground can be steep or rocky.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    m: Mystery = world.facts["mystery_obj"]
    return [
        "Write a short folk tale about friends who solve a mystery at the quarry edge.",
        f"Tell a child-friendly story about {m.ask.lower()} with teamwork and friendship.",
        "Write a gentle tale where a wicked secret is uncovered by friends working together.",
    ]


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    mystery = MYSTERIES[params.mystery]
    team = TEAMS[params.team]
    h1 = world.add(Entity(id="hero1", kind="character", type="child", label=params.hero1, traits=["curious"]))
    h2 = world.add(Entity(id="hero2", kind="character", type="child", label=params.hero2, traits=["kind"]))
    h3 = world.add(Entity(id="hero3", kind="character", type="child", label=params.hero3, traits=["steady"]))
    wicked = world.add(Entity(id="wicked", kind="character", type="old_woman", label="the wicked old miller", traits=["wicked"]))
    world.facts.update(mystery_obj=mystery, team_obj=team, names=[params.hero1, params.hero2, params.hero3], heroes=[h1, h2, h3], wicked=wicked)

    world.say(f"Long ago, at the quarry edge, there lived a wicked old miller who loved to hide things and scare travelers.")
    world.say(f"One dusk, {params.hero1}, {params.hero2}, and {params.hero3} found a sign of {mystery.title}: {mystery.clue}.")
    world.para()
    world.say(f"They looked at one another and knew this was a mystery to solve.")
    world.say(f"{params.hero1} asked, '{mystery.ask}'")
    world.say(f"{params.hero2} said they should look together, and {params.hero3} said to search the stones by hand.")
    world.say(f"The wicked miller had made the path uneasy, and the children could not solve it alone.")
    world.para()
    world.say(f"So the three friends used teamwork: {team.method}.")
    world.say(f"{params.hero1} lifted loose slate, {params.hero2} peered into a cracked bucket, and {params.hero3} brushed away the dust.")
    world.say(f"At last they found that {mystery.reveal}.")
    world.para()
    world.say(f"When the truth came out, the wicked miller had no more secret to keep.")
    world.say(f"The friends carried the treasure back together, and their friendship grew warmer than the quarry wind.")
    world.say(f"In the end, {team.ending}.")
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.kind:
            bits.append(f"kind={e.kind}")
        lines.append(f"  {e.id}: {e.label or e.type} {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(mystery="lantern", team="friends", hero1="Mara", hero2="Pip", hero3="Tess"),
    StoryParams(mystery="bell", team="friends", hero1="Ned", hero2="Lina", hero3="Ivo"),
    StoryParams(mystery="key", team="friends", hero1="Rose", hero2="Jory", hero3="Una"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solve/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
