#!/usr/bin/env python3
"""
storyworlds/worlds/back_dim_cursive_loom_problem_solving_heartwarming.py
========================================================================

A small heartwarming problem-solving storyworld about a child, a dim back room,
a curious loom, and a cursive note that helps everyone fix what is tangled.

Premise:
- A child finds a loom in the back-dim corner of a little workshop.
- The loom's threads are crossed and the pattern cannot grow.
- A grown-up leaves a cursive note with a gentle clue.
- The child and helper solve the problem together, and the loom makes something lovely.

This world is deliberately small and constraint-driven:
- The loom can only be repaired with the right tool for the thread tangle.
- The story must end with a clear, concrete change in state.
- Emotional state is tracked as memes; physical state is tracked as meters.

Story shape:
- Setup: who is in the workshop, what they love, and what is wrong.
- Turn: the child notices the problem and tries a simple fix.
- Resolution: a helper reads the cursive clue, uses the right tool, and the loom works again.
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
TANGLES = {"knot", "snag", "snarl"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    usable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["dust", "tangle", "clean", "care", "work", "glow", "pattern"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "hope", "joy", "calm", "pride", "confusion"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Place:
    name: str
    dim: bool = False
    holds: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    trouble: str
    clue: str
    fix_verb: str
    fix_tool: str
    fix_tool_label: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    type: str
    label: str
    phrase: str
    tool: str
    tool_label: str
    clue_read: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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


def _r_untangle(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "thing":
            continue
        if ent.meters["tangle"] < THRESHOLD:
            continue
        if ("untangle", ent.id) in world.fired:
            continue
        world.fired.add(("untangle", ent.id))
        ent.meters["tangle"] = max(0.0, ent.meters["tangle"] - 1.0)
        ent.meters["clean"] += 1.0
        out.append(f"The threads loosened a little.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.memes["worry"] < THRESHOLD:
            continue
        if ent.memes["hope"] >= THRESHOLD and ("calm", ent.id) not in world.fired:
            world.fired.add(("calm", ent.id))
            ent.memes["calm"] += 1.0
            ent.memes["worry"] = max(0.0, ent.memes["worry"] - 1.0)
            out.append(f"{ent.id} took a slow breath and felt a little calmer.")
    return out


def _r_pattern(world: World) -> list[str]:
    out: list[str] = []
    loom = world.entities.get("loom")
    if not loom:
        return out
    if loom.meters["tangle"] < THRESHOLD and loom.meters["pattern"] < THRESHOLD:
        if ("pattern", "loom") not in world.fired:
            world.fired.add(("pattern", "loom"))
            loom.meters["pattern"] += 1.0
            loom.meters["glow"] += 1.0
            out.append("The loom began to make a neat little pattern again.")
    return out


CAUSAL_RULES = [_r_untangle, _r_calm, _r_pattern]


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


def problem_at_risk(problem: Problem) -> bool:
    return True


def select_fix(problem: Problem) -> Optional[Helper]:
    for helper in HELPERS:
        if helper.tool == problem.fix_tool:
            return helper
    return None


def build_world(params: "StoryParams") -> World:
    place = PLACES[params.place]
    world = World(place)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.trait],
    ))
    grown = world.add(Entity(
        id="grownup",
        kind="character",
        type=params.adult,
        label=f"the {params.adult}",
    ))
    loom = world.add(Entity(
        id="loom",
        type="loom",
        label="the loom",
        phrase="a sturdy old loom",
        caretaker=grown.id,
    ))
    note = world.add(Entity(
        id="note",
        type="note",
        label="the note",
        phrase="a cursive note tucked beside the loom",
    ))
    thread = world.add(Entity(
        id="thread",
        type="thread",
        label="the thread",
        phrase="a bundle of bright thread",
        caretaker=grown.id,
    ))
    loom.meters["tangle"] = 1.0
    note.meters["clean"] = 1.0

    world.facts.update(
        child=child,
        grown=grown,
        loom=loom,
        note=note,
        thread=thread,
        problem=PROBLEMS[params.problem],
        helper=None,
        fixed=False,
    )

    # Setup
    world.say(
        f"In the back-dim room, {params.name} found {loom.phrase} waiting by the wall."
    )
    world.say(
        f"{params.name} liked how the loom turned thread into something warm and useful."
    )
    world.say(
        f"But today the threads were crossed tight, and the loom could not make its pattern."
    )

    # Turn
    world.para()
    child.memes["worry"] += 1.0
    child.memes["hope"] += 1.0
    world.say(
        f"{params.name} touched the loom gently and tried to smooth the threads with small hands."
    )
    world.say(
        f"That helped a tiny bit, but the knot stayed stuck."
    )
    world.say(
        f"Near the loom, there was a cursive note with a clue: \"{PROBLEMS[params.problem].clue}\""
    )

    # Resolution
    world.para()
    helper = HELPER_BY_TOOL[PROBLEMS[params.problem].fix_tool]
    world.facts["helper"] = helper
    world.say(
        f"{helper.phrase} came over, read the cursive note, and smiled."
    )
    world.say(
        f"\"We need the {helper.tool_label} for this kind of tangle,\" {params.name} said."
    )
    child.memes["joy"] += 1.0
    child.memes["hope"] += 1.0
    grown.memes["pride"] += 1.0
    thread.meters["tangle"] += 1.0
    world.say(
        f"Together they used the {helper.tool_label} to {PROBLEMS[params.problem].fix_verb} the threads."
    )
    propagate(world, narrate=True)
    world.say(
        f"At last the loom was {PROBLEMS[params.problem].result}, and a small bright piece hung there like a thank-you."
    )
    child.memes["worry"] = 0.0
    grown.memes["calm"] += 1.0
    world.facts["fixed"] = True
    return world


@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "workshop": Place(name="the workshop", dim=True, holds={"loom", "note", "thread"}),
    "back_room": Place(name="the back room", dim=True, holds={"loom", "note", "thread"}),
    "attic": Place(name="the attic", dim=True, holds={"loom", "note", "thread"}),
}

PROBLEMS = {
    "knot": Problem(
        id="knot",
        label="a stubborn knot",
        trouble="the threads were knotted together",
        clue="Use the wide comb first, then lift the loop gently.",
        fix_verb="comb",
        fix_tool="wide_comb",
        fix_tool_label="wide comb",
        result="smooth and ready",
        tags={"loom", "cursive", "problem_solving"},
    ),
    "snag": Problem(
        id="snag",
        label="a snag on a spoke",
        trouble="one thread had snagged on a wooden spoke",
        clue="Slide the little hook under the snag before you pull.",
        fix_verb="hook",
        fix_tool="little_hook",
        fix_tool_label="little hook",
        result="steady and bright",
        tags={"loom", "cursive", "problem_solving"},
    ),
    "snarl": Problem(
        id="snarl",
        label="a twisted snarl",
        trouble="the wool had snarled into a tight twist",
        clue="Wind the loose end onto the smooth spool and let it breathe.",
        fix_verb="spool",
        fix_tool="smooth_spool",
        fix_tool_label="smooth spool",
        result="soft and even",
        tags={"loom", "cursive", "problem_solving"},
    ),
}

HELPERS = [
    Helper("wide_comb", "tool", "the wide comb", "A gentle grown-up came in", "wide_comb", "wide comb", "read"),
    Helper("little_hook", "tool", "the little hook", "The helpful neighbor leaned in", "little_hook", "little hook", "read"),
    Helper("smooth_spool", "tool", "the smooth spool", "The patient aunt came by", "smooth_spool", "smooth spool", "read"),
]

HELPER_BY_TOOL = {h.tool: h for h in HELPERS}

NAMES = ["Mina", "Iris", "Nora", "Toby", "Eli", "June"]
TRAITS = ["curious", "gentle", "careful", "hopeful", "patient"]
ADULTS = ["mother", "father", "aunt", "uncle"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES:
        for problem in PROBLEMS:
            combos.append((place, problem))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming problem-solving story world about a back-dim loom and a cursive clue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=ADULTS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.problem:
        combos = [c for c in combos if c[1] == args.problem]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    adult = args.adult or rng.choice(ADULTS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, name=name, gender=gender, adult=adult, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    problem = f["problem"]
    return [
        f"Write a heartwarming story about {child.id} finding a loom in a {world.place.name} and solving {problem.label}.",
        f"Tell a simple story with a cursive note, a dim back room, and a child who learns how to fix a loom.",
        f"Write a gentle problem-solving story where a family works together to make a loom's pattern start again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    grown = f["grown"]
    loom = f["loom"]
    problem = f["problem"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"What did {child.id} find in {world.place.name}?",
            answer=f"{child.id} found {loom.phrase} in {world.place.name}. It was waiting in the back-dim room.",
        ),
        QAItem(
            question=f"What was wrong with the loom?",
            answer=f"The loom had {problem.trouble}, so it could not make its pattern yet.",
        ),
        QAItem(
            question=f"What clue was written in the note?",
            answer=f"The note said, \"{problem.clue}\"",
        ),
        QAItem(
            question=f"Who helped fix the loom?",
            answer=f"{helper.phrase} helped by reading the cursive note and using the {helper.tool_label}.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt happy because the loom was working again and the room felt warm and peaceful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a loom?",
            answer="A loom is a tool that holds threads in place so people can weave cloth or cloth-like pieces.",
        ),
        QAItem(
            question="What does cursive mean?",
            answer="Cursive is a style of handwriting where the letters are joined together in a flowing way.",
        ),
        QAItem(
            question="Why is it harder to work in a dim room?",
            answer="A dim room has less light, so people may need to look more carefully at small details.",
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
place(P) :- setting(P).
problem(K) :- issue(K).
valid_story(P,K) :- place(P), problem(K).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("setting", p))
    for k in PROBLEMS:
        lines.append(asp.fact("issue", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    cl2 = {(a, b) for (a, b) in cl}
    if py == cl2:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python only:", sorted(py - cl2))
    print("clingo only:", sorted(cl2 - py))
    return 1


CURATED = [
    StoryParams(place="workshop", problem="knot", name="Mina", gender="girl", adult="mother", trait="gentle"),
    StoryParams(place="back_room", problem="snag", name="Toby", gender="boy", adult="father", trait="careful"),
    StoryParams(place="attic", problem="snarl", name="June", gender="girl", adult="aunt", trait="hopeful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for p, k in asp_valid_combos():
            print(p, k)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
