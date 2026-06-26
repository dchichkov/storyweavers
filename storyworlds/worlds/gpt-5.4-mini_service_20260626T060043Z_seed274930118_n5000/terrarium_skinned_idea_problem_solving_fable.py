#!/usr/bin/env python3
"""
storyworlds/worlds/terrarium_skinned_idea_problem_solving_fable.py
===================================================================

A small fable-like story world about a tiny problem, a bright idea, and a
terrarium that changes hands.

Seed image:
- A little animal sees a terrarium
- Something goes wrong and a paw/knee gets skinned
- A helpful idea solves the problem

The world keeps the prose concrete and causal: a character wants something,
meets a problem, thinks of an idea, and makes a kind fix.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "rabbit", "fox", "bird", "hedgehog"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero: str
    companion: str
    problem: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        import copy
        return World(self.place, copy.deepcopy(self.entities), [[]], dict(self.facts), set(self.fired))


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "garden_room": Place(name="the garden room", indoors=True, affords={"care", "observe", "move"}),
    "sunroom": Place(name="the sunroom", indoors=True, affords={"care", "observe", "move"}),
    "porch": Place(name="the porch", indoors=True, affords={"care", "observe", "move"}),
}

HEROES = {
    "mouse": {"type": "mouse", "label": "mouse"},
    "rabbit": {"type": "rabbit", "label": "rabbit"},
    "fox": {"type": "fox", "label": "fox"},
    "bird": {"type": "bird", "label": "bird"},
    "hedgehog": {"type": "hedgehog", "label": "hedgehog"},
}

COMPANIONS = {
    "snail": {"type": "snail", "label": "snail"},
    "frog": {"type": "frog", "label": "frog"},
    "turtle": {"type": "turtle", "label": "turtle"},
    "lizard": {"type": "lizard", "label": "lizard"},
}

PROBLEMS = {
    "stuck_lid": {
        "label": "stuck lid",
        "risk": "the lid would not lift",
        "moral": "a strong pull is not always the best plan",
    },
    "dry_soil": {
        "label": "dry soil",
        "risk": "the soil was too dry and crumbly",
        "moral": "water helps when dry things need softening",
    },
    "tiny_rock": {
        "label": "tiny rock",
        "risk": "the pebble blocked the little path",
        "moral": "small problems can have small fixes",
    },
    "bent_wire": {
        "label": "bent wire",
        "risk": "the wire kept the door from closing",
        "moral": "a careful bend can be better than a forceful push",
    },
}

TOOLS = {
    "cloth": {"label": "a soft cloth", "use": "wipe", "guards": {"dry_soil"}},
    "water": {"label": "a little water", "use": "soften", "guards": {"dry_soil"}},
    "twig": {"label": "a thin twig", "use": "nudge", "guards": {"tiny_rock", "bent_wire"}},
    "spoon": {"label": "a small spoon", "use": "pry", "guards": {"stuck_lid"}},
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- place_fact(P).
hero(H) :- hero_fact(H).
problem(X) :- problem_fact(X).
tool(T) :- tool_fact(T).

fits(T, P) :- tool(T), problem(P), guards(T, P).
valid(P, T) :- problem(P), tool(T), fits(T, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place_fact", pid))
    for hid in HEROES:
        lines.append(asp.fact("hero_fact", hid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem_fact", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool_fact", tid))
        for p in TOOLS[tid]["guards"]:
            lines.append(asp.fact("guards", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid_pairs() -> list[tuple[str, str]]:
    out = []
    for p in PROBLEMS:
        for t in TOOLS:
            if p in TOOLS[t]["guards"]:
                out.append((p, t))
    return sorted(out)


def asp_verify() -> int:
    a = set(asp_valid_pairs())
    b = set(python_valid_pairs())
    if a == b:
        print(f"OK: clingo gate matches python gate ({len(a)} pairs).")
        return 0
    print("MISMATCH between clingo and python gate")
    print("only in asp:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

@dataclass
class Rule:
    name: str
    apply: callable


def _r_problem(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    problem = world.facts["problem"]
    if hero.memes.get("frustration", 0) >= 1 and problem == "stuck_lid":
        if ("problem", "stuck_lid") not in world.fired:
            world.fired.add(("problem", "stuck_lid"))
            out.append("The lid still would not move.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for rule in [Rule("problem", _r_problem)]:
        out.extend(rule.apply(world))
    if narrate:
        for s in out:
            world.say(s)
    return out


def choose_tool(problem: str) -> Optional[str]:
    for tid, tool in TOOLS.items():
        if problem in tool["guards"]:
            return tid
    return None


def resolve_problem(world: World, problem: str) -> Optional[str]:
    return choose_tool(problem)


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    hero = world.add(Entity(id="hero", kind="character", type=params.hero, label=params.hero))
    companion = world.add(Entity(id="companion", kind="character", type=params.companion, label=params.companion))
    terrarium = world.add(Entity(
        id="terrarium", type="terrarium", label="terrarium",
        phrase="a clear terrarium with a tiny green world inside",
        owner=hero.id,
    ))
    problem = PROBLEMS[params.problem]
    tool_id = resolve_problem(world, params.problem)

    world.facts.update(problem=params.problem, tool=tool_id, place=params.place,
                       hero=params.hero, companion=params.companion)

    world.say(
        f"Once, a little {params.hero} found {terrarium.phrase} on a low table."
    )
    world.say(
        f"Inside it was a small problem: {problem['risk']}."
    )
    world.say(
        f"The {params.hero} wanted to help, because a kind heart does not like to leave a thing in trouble."
    )

    world.para()
    world.say(
        f"{params.hero.capitalize()} tried the first idea at once, but the first idea was too rough."
    )
    if params.problem == "stuck_lid":
        hero.memes["frustration"] = hero.memes.get("frustration", 0) + 1
        propagate(world)
        world.say(
            f"The lid stayed firm, and the {params.hero} felt a little skinned in spirit from trying so hard."
        )
    elif params.problem == "dry_soil":
        world.say(
            f"The dry soil only puffed into dust, and that was no help at all."
        )
    elif params.problem == "tiny_rock":
        world.say(
            f"The big push only slid the rock farther across the path."
        )
    else:
        world.say(
            f"The hard shove bent the wire the wrong way."
        )

    world.para()
    if tool_id is None:
        raise StoryError("No gentle fix exists for this problem.")
    tool = TOOLS[tool_id]
    world.say(
        f"Then {params.companion} had an idea: use {tool['label']} and solve it by being careful instead of loud."
    )
    if params.problem == "dry_soil":
        world.say(
            "A little water softened the soil, and then the roots could breathe again."
        )
    elif params.problem == "stuck_lid":
        world.say(
            "The small spoon slipped under the edge, and the lid rose without a fight."
        )
    elif params.problem == "tiny_rock":
        world.say(
            "The thin twig nudged the pebble aside, and the path opened."
        )
    else:
        world.say(
            "The twig guided the wire back into a neat curve, and the door shut properly."
        )

    world.para()
    world.say(
        f"At the end, the terrarium was safe, the {params.hero} was proud, and the {params.companion} was pleased."
    )
    world.say(
        "The lesson was simple: when a problem looks stubborn, a gentle idea can be stronger than force."
    )
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for children that includes a terrarium and the word "idea".',
        f"Tell a small problem-solving story about a {f['hero']} and a {f['companion']} fixing {f['problem']}.",
        "Write a gentle fable where careful thinking solves a tiny trouble better than force.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    problem = PROBLEMS[f["problem"]]["label"]
    tool = TOOLS[f["tool"]]["label"]
    return [
        QAItem(
            question="What object was on the low table?",
            answer="A clear terrarium with a tiny green world inside was on the low table.",
        ),
        QAItem(
            question=f"What problem did the story face?",
            answer=f"The story faced {problem}, which made the first attempt fail.",
        ),
        QAItem(
            question="What idea solved the trouble?",
            answer=f"The helpful idea was to use {tool} and work carefully instead of forcing the problem.",
        ),
        QAItem(
            question="What lesson did the story end with?",
            answer="The story ended with the lesson that a gentle idea can be stronger than force.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a terrarium?",
            answer="A terrarium is a clear container where small plants, moss, or tiny creatures can live and be watched safely.",
        ),
        QAItem(
            question="What does it mean when something is skinned?",
            answer="When something is skinned, its outer surface has been rubbed or scraped off a little, like a skinned knee.",
        ),
        QAItem(
            question="What is an idea?",
            answer="An idea is a thought that helps someone understand, create, or solve a problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like problem-solving terrarium story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--problem", choices=PROBLEMS)
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
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(list(HEROES))
    companion = args.companion or rng.choice(list(COMPANIONS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    if hero == companion:
        raise StoryError("Hero and companion must be different characters.")
    if choose_tool(problem) is None:
        raise StoryError("No valid tool exists for the chosen problem.")
    return StoryParams(place=place, hero=hero, companion=companion, problem=problem)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid problem/tool pairs:")
        for p, t in pairs:
            print(f"  {p:12} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        combos = [
            StoryParams(place=pl, hero=h, companion=c, problem=p)
            for pl in PLACES for h in HEROES for c in COMPANIONS for p in PROBLEMS
            if h != c and choose_tool(p) is not None
        ]
        samples = [generate(sp) for sp in combos[:5]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < args.n * 50:
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
