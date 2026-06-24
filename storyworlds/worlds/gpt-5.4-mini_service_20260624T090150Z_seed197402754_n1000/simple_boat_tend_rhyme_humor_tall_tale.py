#!/usr/bin/env python3
"""
Standalone storyworld: simple boat, tend, rhyme, humor, tall tale.

A small child loves a simple boat and wants to take it out on the water.
Something goes a little wrong, a grownup spots the trouble, and they tend
the boat with a clever fix. The prose keeps a tall-tale bounce, some rhyme,
and a bit of humor while staying state-driven.
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

BOAT_KINDS = {
    "skiff": "a simple skiff",
    "rowboat": "a simple rowboat",
    "punt": "a simple punt",
}

PLACES = {
    "pond": {"water", "dock"},
    "lake": {"water", "dock", "island"},
    "river": {"water", "bank"},
}

PROBLEMS = {
    "leak": {
        "meter": "leak",
        "hurt": "sinks lower",
        "fix": "patch",
        "rhyme": "drip",
        "humor": "The boat made a face like a soggy pancake.",
    },
    "stuck_oar": {
        "meter": "stuck",
        "hurt": "won't row right",
        "fix": "oil",
        "rhyme": "swoosh",
        "humor": "One oar seemed to be napping harder than a kitten.",
    },
    "tangled_rope": {
        "meter": "tangled",
        "hurt": "won't steer straight",
        "fix": "untie",
        "rhyme": "knot",
        "humor": "The rope looked like it had learned square dancing.",
    },
}

HELPERS = {
    "grandpa": "Grandpa",
    "grandma": "Grandma",
    "dad": "Dad",
    "mom": "Mom",
    "aunt": "Aunt Bea",
}

KIDS = ["Milo", "Nora", "Beck", "Luna", "Finn", "Ivy", "Otis", "Pia"]
TRAITS = ["cheery", "curious", "brave", "spry", "merry"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)


@dataclass
class StoryParams:
    boat: str
    place: str
    problem: str
    child: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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

    def copy(self) -> "World":
        import copy
        w = World(self.params)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _setup_world(params: StoryParams) -> World:
    world = World(params)
    child = world.add(Entity(id=params.child, kind="character", label=params.child))
    helper = world.add(Entity(id=HELPERS[params.helper], kind="character", label=HELPERS[params.helper]))
    boat = world.add(Entity(
        id="boat",
        kind="thing",
        label=BOAT_KINDS[params.boat],
        phrase=BOAT_KINDS[params.boat],
        owner=child.id,
        caretaker=helper.id,
        meters={"simple": 1.0},
    ))
    problem = world.add(Entity(
        id="problem",
        kind="thing",
        label=params.problem,
        phrase=params.problem,
        meters={PROBLEMS[params.problem]["meter"]: 1.0},
    ))
    world.facts.update(child=child, helper=helper, boat=boat, problem=problem)
    return world


def _prose_open(world: World) -> None:
    p = world.params
    world.say(
        f"Once upon a bright little day, {p.child} had {BOAT_KINDS[p.boat]}. "
        f"It was plain as a spoon and proud as a peacock in a patchwork crown."
    )
    world.say(
        f"{p.child} was a {p.trait} child who loved to watch the boat bob and go. "
        f"\"A boat so neat is a sweet little feat,\" {p.child} would boast with a grin."
    )


def _problem_begins(world: World) -> None:
    p = world.params
    problem = PROBLEMS[p.problem]
    world.para()
    world.say(
        f"One day at the {p.place}, {p.child} took the boat near the water."
    )
    world.say(
        f"Then came trouble with a tumble and a bubble: the boat got {p.problem}."
    )
    world.say(problem["humor"])
    if p.problem == "leak":
        world.say("A drip turned into a skip, and the little boat began to sip the pond.")
    elif p.problem == "stuck_oar":
        world.say("One oar flapped and slapped, but the boat still would not scoot.")
    else:
        world.say("The rope tied itself into a knot that looked fit for a cat's bedtime.")
    world.say(
        f"{p.child} frowned. \"Oh, no and oh, woe — my boat won't go!\""
    )


def _helper_tends(world: World) -> None:
    p = world.params
    helper = world.get(HELPERS[p.helper])
    boat = world.get("boat")
    problem = PROBLEMS[p.problem]
    world.para()
    world.say(
        f"{helper.label} came strolling over, as calm as a cat on a sill. "
        f"\"Let's tend this boat,\" {helper.label} said, \"and make it ready still.\""
    )
    if p.problem == "leak":
        boat.meters["leak"] = 0.0
        boat.meters["patched"] = 1.0
        world.say("They pressed on a patch, sharp as a catch, and the drip-drip stopped.")
        world.say("The boat went from soggy to sturdy in a blink and a wink.")
    elif p.problem == "stuck_oar":
        boat.meters["stuck"] = 0.0
        boat.meters["oiled"] = 1.0
        world.say("They rubbed a little oil on the oar, and the swoosh came back with a flourish.")
        world.say("The oar woke up with a squeak and a speak, then splashed like a star.")
    else:
        boat.meters["tangled"] = 0.0
        boat.meters["tidy"] = 1.0
        world.say("They untied the knot one loop at a time, and the rope quit its square dance.")
        world.say("The line went straight as a train track and stayed as neat as a napkin.")
    world.say(
        f"{helper.label} chuckled, \"A tender boat is a winner afloat.\""
    )
    world.facts["resolved"] = True
    world.facts["fix"] = problem["fix"]


def _ending(world: World) -> None:
    p = world.params
    world.para()
    world.say(
        f"Soon {p.child} climbed in again. The simple boat was all mended, and it slid along the {p.place} "
        f"like a spoon in soup."
    )
    world.say(
        f"{p.child} laughed, {HELPERS[p.helper].split()[0].lower()} laughed, and even the water seemed to clap. "
        f"It was a small boat story, but it sailed like a giant tale."
    )
    world.say(
        f"\"A boat in need is a boat to heed,\" {p.child} sang, and off they went, neat and fleet."
    )


def generate_world(params: StoryParams) -> World:
    world = _setup_world(params)
    _prose_open(world)
    _problem_begins(world)
    _helper_tends(world)
    _ending(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a short tall tale about {p.child} and a simple boat that needs tending.",
        f"Tell a rhyming, humorous story where {HELPERS[p.helper]} helps fix a {p.problem} boat at the {p.place}.",
        f"Write a child-friendly story with a simple boat, a problem, and a clever repair that ends happily.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    helper = HELPERS[p.helper]
    return [
        QAItem(
            question=f"Who had the simple boat in the story?",
            answer=f"{p.child} had the simple boat and loved it very much.",
        ),
        QAItem(
            question=f"What went wrong with the boat at the {p.place}?",
            answer=f"The boat got {p.problem}, so it could not go properly until it was tended.",
        ),
        QAItem(
            question=f"Who helped tend the boat?",
            answer=f"{helper} helped tend the boat and fix the trouble.",
        ),
        QAItem(
            question=f"How did the story end after the boat was fixed?",
            answer=f"{p.child} rode the simple boat again, and everything ended with laughter and a smooth ride.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.params
    qas = [
        QAItem(
            question="What does it mean to tend something?",
            answer="To tend something means to take care of it, help it, and keep it in good shape.",
        ),
        QAItem(
            question="What is a boat?",
            answer="A boat is a craft that floats on water and can carry people or things.",
        ),
        QAItem(
            question="Why do people fix leaks in boats?",
            answer="People fix leaks so the boat stays afloat and does not fill with water.",
        ),
    ]
    if p.problem == "tangled_rope":
        qas.append(QAItem(
            question="Why should a rope be untied carefully?",
            answer="A tangled rope can snatch and knot itself tighter, so gentle hands help it become neat again.",
        ))
    return qas


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        if meters:
            lines.append(f"{e.id}: {e.label} meters={meters}")
        else:
            lines.append(f"{e.id}: {e.label}")
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for boat in BOAT_KINDS:
        for place in PLACES:
            for problem in PROBLEMS:
                out.append((boat, place, problem))
    return out


def explain_rejection() -> str:
    return "(No story: the chosen boat tale would not be a simple, tidy problem-and-fix story.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about a simple boat that needs tending.")
    ap.add_argument("--boat", choices=BOAT_KINDS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--child")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.boat and args.place and args.problem:
        if (args.boat, args.place, args.problem) not in combos:
            raise StoryError(explain_rejection())
    boat = args.boat or rng.choice(list(BOAT_KINDS))
    place = args.place or rng.choice(list(PLACES))
    problem = args.problem or rng.choice(list(PROBLEMS))
    child = args.child or rng.choice(KIDS)
    helper = args.helper or rng.choice(list(HELPERS))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(boat=boat, place=place, problem=problem, child=child, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
boat(B) :- boat_kind(B).
place(P) :- place_kind(P).
problem(X) :- problem_kind(X).

tall_tale_story(B,P,X) :- boat(B), place(P), problem(X).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for b in BOAT_KINDS:
        lines.append(asp.fact("boat_kind", b))
    for p in PLACES:
        lines.append(asp.fact("place_kind", p))
    for x in PROBLEMS:
        lines.append(asp.fact("problem_kind", x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show tall_tale_story/3."))
    clingo_set = set(asp.atoms(model, "tall_tale_story"))
    python_set = set(valid_combos())
    if len(clingo_set) != len(python_set):
        print("MISMATCH between ASP and Python combo counts.")
        print(f"ASP: {len(clingo_set)} Python: {len(python_set)}")
        return 1
    print(f"OK: ASP and Python agree on {len(python_set)} story combos.")
    return 0


CURATED = [
    StoryParams(boat="skiff", place="pond", problem="leak", child="Milo", helper="grandpa", trait="merry"),
    StoryParams(boat="rowboat", place="lake", problem="stuck_oar", child="Nora", helper="dad", trait="curious"),
    StoryParams(boat="punt", place="river", problem="tangled_rope", child="Ivy", helper="aunt", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show tall_tale_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show tall_tale_story/3."))
        combos = sorted(set(asp.atoms(model, "tall_tale_story")))
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        while len(samples) < args.n and len(seen) < 1000:
            params = resolve_params(args, rng)
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
            header = f"### {p.child}: {p.boat} at {p.place} ({p.problem})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
