#!/usr/bin/env python3
"""
A small storyworld about a detective, a puzzling wiggle-dim clue, sharing,
problem solving, and dialogue in a child-friendly detective-story style.
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


@dataclass
class Place:
    id: str
    label: str
    indoor: bool = False
    traits: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    what: str
    color: str
    size: str
    wiggle_dim: bool = False
    traits: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str] = field(default_factory=set)
    shared: bool = True


@dataclass
class Character:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("curious", "kind", "hope", "confused", "teamwork", "relief"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)


@dataclass
class World:
    place: Place
    entities: dict[str, object] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, obj):
        self.entities[obj.id] = obj
        return obj

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str):
        if text:
            self.paragraphs[-1].append(text)

    def para(self):
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "museum": Place("museum", "the little museum", indoor=True, traits={"quiet", "careful"}),
    "library": Place("library", "the old library", indoor=True, traits={"quiet", "neat"}),
    "alley": Place("alley", "the narrow alley", indoor=False, traits={"shadowy", "busy"}),
}

CLUES = {
    "blue_thread": Clue("blue_thread", "a blue thread", "thread", "blue", "tiny", traits={"soft"}),
    "crumbs": Clue("crumbs", "crumbs", "crumbs", "golden", "small", traits={"crumbly"}),
    "button": Clue("button", "a button", "button", "red", "small", wiggle_dim=True, traits={"round"}),
    "feather": Clue("feather", "a feather", "feather", "white", "light", traits={"light"}),
    "keycard": Clue("keycard", "a keycard", "keycard", "gray", "flat", wiggle_dim=True, traits={"slippery"}),
}

TOOLS = {
    "magnifier": Tool("magnifier", "a magnifying glass", helps={"see_small"}),
    "map": Tool("map", "a folded map", helps={"find_path"}),
    "notes": Tool("notes", "a notebook", helps={"share_clues", "solve"}),
}

NAMES = ["Mira", "Toby", "Nina", "Leo", "Rosa", "Eli", "Ava", "Noah"]
TRAITS = ["careful", "curious", "brave", "patient", "bright"]


@dataclass
class StoryParams:
    place: str
    clue: str
    name: str
    sidekick: str
    trait: str
    seed: Optional[int] = None


ASP_RULES = r"""
place(P) :- place_fact(P).
clue(C) :- clue_fact(C).
wiggle_dim(C) :- wiggle_dim_fact(C).

problem(C) :- clue(C), wiggle_dim(C).
share_help(T) :- tool(T), helps(T, share_clue).
solve_way(T) :- tool(T), helps(T, solve_problem).

good_story(P, C) :- place(P), problem(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place_fact", pid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue_fact", cid))
        if clue.wiggle_dim:
            lines.append(asp.fact("wiggle_dim_fact", cid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if "share_clues" in tool.helps:
            lines.append(asp.fact("helps", tid, "share_clue"))
        if "solve" in tool.helps:
            lines.append(asp.fact("helps", tid, "solve_problem"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld with a wiggle-dim clue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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
    place = args.place or rng.choice(list(PLACES))
    clue = args.clue or rng.choice([c for c in CLUES if CLUES[c].wiggle_dim])
    name = args.name or rng.choice(NAMES)
    sidekick = args.sidekick or rng.choice([n for n in NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    if not CLUES[clue].wiggle_dim:
        raise StoryError("The detective story needs a wiggle-dim clue, but that clue is not wiggle-dim.")
    return StoryParams(place=place, clue=clue, name=name, sidekick=sidekick, trait=trait)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    clue = CLUES[params.clue]
    world = World(place=place)
    detective = world.add(Character(params.name, type="detective", label=params.name, traits=[params.trait, "detective"]))
    helper = world.add(Character(params.sidekick, type="friend", label=params.sidekick, traits=["helpful", "sharing"]))
    tool = world.add(TOOLS["notes"])
    world.facts.update(place=place, clue=clue, detective=detective, helper=helper, tool=tool)

    world.say(f"{detective.id} was a {params.trait} little detective who loved a good mystery.")
    world.say(f"At {place.label}, {detective.id} found {clue.label}. It looked small, but something about it felt wiggle-dim.")
    world.say(f"{helper.id} leaned close and said, \"Let's share what we see.\" {detective.id} nodded and opened {tool.label}.")

    world.para()
    world.say(f"The two friends talked in soft voices. \"It wiggled when I touched it,\" said {detective.id}.")
    world.say(f"\"And I saw it near the door,\" said {helper.id}. \"Maybe it rolled there.\"")
    world.say(f"They wrote down every clue together, because sharing made the puzzle clearer.")

    world.para()
    world.say(f"Then {detective.id} noticed a tiny mark on the floor. \"That is the answer!\" {detective.id} said.")
    world.say(f"They followed the mark, solved the problem, and found where the missing thing had gone.")
    world.say(f"In the end, {detective.id} and {helper.id} smiled with relief, and {clue.label} was safely placed back where it belonged.")

    prompts = [
        f"Write a short detective story for a child that includes the word \"wiggle-dim\" and a shared clue.",
        f"Tell a gentle mystery where {detective.id} and {helper.id} solve a problem by talking and sharing ideas.",
        f"Write a tiny detective tale set at {place.label} with a clue that seems odd at first but makes sense at the end.",
    ]
    story_qa = [
        QAItem(
            question=f"What kind of clue did {detective.id} find at {place.label}?",
            answer=f"{detective.id} found {clue.label}, and it seemed wiggle-dim and puzzling at first."
        ),
        QAItem(
            question=f"How did {detective.id} and {helper.id} solve the problem?",
            answer="They shared what they saw, talked kindly, wrote the clues down, and followed the tiny mark to the answer."
        ),
        QAItem(
            question=f"Why did the story feel like a detective story?",
            answer="Because the characters noticed clues, asked questions, shared ideas, and worked together to solve a mystery."
        ),
    ]
    world_qa = [
        QAItem(
            question="What does it mean to share?",
            answer="To share means to use, show, or give something together so other people can help or enjoy it too."
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully, trying ideas, and choosing a good way to fix a problem."
        ),
        QAItem(
            question="Why is dialogue useful in a mystery?",
            answer="Dialogue helps characters explain what they know, ask questions, and work together to find the answer."
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        if isinstance(e, Character):
            lines.append(f"  {e.id:10} character meters={e.meters} memes={e.memes}")
        else:
            lines.append(f"  {e.id:10} tool")
    lines.append(f"  place: {world.place.id}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
    StoryParams(place="museum", clue="button", name="Mira", sidekick="Toby", trait="curious"),
    StoryParams(place="library", clue="keycard", name="Nina", sidekick="Leo", trait="careful"),
    StoryParams(place="alley", clue="feather", name="Ava", sidekick="Eli", trait="brave"),
]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in PLACES:
        for clue, c in CLUES.items():
            if c.wiggle_dim:
                out.append((place, clue))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/2."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, clue) combos:\n")
        for place, clue in combos:
            print(f"  {place:8} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.name}: clue={p.clue} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
