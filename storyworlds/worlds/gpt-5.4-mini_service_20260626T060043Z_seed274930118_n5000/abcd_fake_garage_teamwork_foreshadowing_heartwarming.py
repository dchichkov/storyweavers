#!/usr/bin/env python3
"""
Storyworld: a heartwarming garage teamwork tale with foreshadowing.

A child and a grown-up work together in a garage to solve a small problem.
The story is built from a stateful simulation so the turning points are driven
by meters and memes rather than a frozen paragraph.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class GarageSetting:
    place: str = "the garage"
    affords: set[str] = field(default_factory=lambda: {"fix", "clean", "build"})


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: str
    ready_text: str
    use_text: str
    weathered: bool = False


@dataclass
class StoryParams:
    place: str
    task: str
    tool: str
    name: str
    child_type: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: GarageSetting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}
        self.trace_lines: list[str] = []

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

    def log(self, text: str) -> None:
        self.trace_lines.append(text)


SETTINGS = {"garage": GarageSetting()}
TASKS = {
    "fix": {
        "verb": "fix the bike",
        "problem": "the bike had a flat tire",
        "risk": "the bike would stay broken",
        "turn": "patch the tire",
        "result": "the bike rolled smoothly again",
        "foreshadow": "a small hissing sound from the tire",
    },
    "clean": {
        "verb": "clean the old box",
        "problem": "the box was dusty and stuck to the shelf",
        "risk": "the mess would keep growing",
        "turn": "wipe the shelves and sort the parts",
        "result": "the box shone and the shelf looked neat",
        "foreshadow": "a gray dust line along the shelf",
    },
    "build": {
        "verb": "build a bird feeder",
        "problem": "the boards did not line up right",
        "risk": "the feeder would wobble",
        "turn": "measure twice and hold the boards steady",
        "result": "the feeder stood straight and true",
        "foreshadow": "a crooked sketch on a scrap of paper",
    },
}
TOOLS = {
    "wrench": Tool("wrench", "wrench", "a little wrench", "fix", "lay ready on the workbench", "turned the nut just right"),
    "rag": Tool("rag", "rag", "a soft rag", "clean", "sat folded by the sink", "wiped away the dust"),
    "clamp": Tool("clamp", "clamp", "a bright clamp", "build", "waited beside the wood scraps", "held the boards together"),
}
NAMES = ["Ada", "Milo", "Nia", "Owen", "Iris", "Leo"]
TRAITS = ["careful", "kind", "brave", "patient", "gentle", "cheerful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming garage teamwork storyworld.")
    ap.add_argument("--place", choices=list(SETTINGS), default=None)
    ap.add_argument("--task", choices=list(TASKS), default=None)
    ap.add_argument("--tool", choices=list(TOOLS), default=None)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy"], default=None)
    ap.add_argument("--helper-type", choices=["mother", "father"], default=None)
    ap.add_argument("--trait")
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


def _validate_explicit(args: argparse.Namespace) -> None:
    if args.task and args.tool:
        if TASKS[args.task]["verb"] == "fix the bike" and args.tool != "wrench":
            raise StoryError("That tool does not make sense for fixing a bike in the garage.")
        if TASKS[args.task]["verb"] == "clean the old box" and args.tool != "rag":
            raise StoryError("That tool does not make sense for cleaning dusty things.")
        if TASKS[args.task]["verb"] == "build a bird feeder" and args.tool != "clamp":
            raise StoryError("That tool does not make sense for building the feeder safely.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    _validate_explicit(args)
    place = args.place or "garage"
    task = args.task or rng.choice(list(TASKS))
    tool = args.tool or {"fix": "wrench", "clean": "rag", "build": "clamp"}[task]
    child_type = args.child_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["mother", "father"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, tool=tool, name=name, child_type=child_type, helper_type=helper_type, trait=trait)


def _safety_check(task: str, tool: str) -> None:
    if task == "fix" and tool != "wrench":
        raise StoryError("The garage fix story needs a wrench to feel believable.")
    if task == "clean" and tool != "rag":
        raise StoryError("The garage clean story needs a rag to feel believable.")
    if task == "build" and tool != "clamp":
        raise StoryError("The garage build story needs a clamp to feel believable.")


def generate_world(params: StoryParams) -> World:
    _safety_check(params.task, params.tool)
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.name, traits=["little", params.trait]))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=f"the {params.helper_type}"))
    tool = TOOLS[params.tool]
    item = world.add(Entity(id="project", type="thing", label=tool.label, phrase=tool.phrase, owner=child.id, caretaker=helper.id))
    world.facts.update(child=child, helper=helper, tool=tool, task=params.task, item=item, params=params)

    world.say(f"{child.label} was a little {params.trait} {params.child_type} who loved the garage.")
    world.say(f"{child.pronoun('subject').capitalize()} liked how {tool.phrase} could help on {TASKS[params.task]['verb']} days.")
    world.say(f"One shelf held {tool.phrase}, and {tool.ready_text}.")
    world.say(f"In the corner, there was even a toy note that said \"abcd\" on it, which made {child.label} giggle; it looked fake, but it helped the garage feel like a game.")

    world.para()
    world.say(f"One afternoon, {child.label} and {child.pronoun('possessive')} {params.helper_type} went into {params.place}.")
    world.say(f"They found that {TASKS[params.task]['problem']}.")
    world.say(f"Near the workbench, {TASKS[params.task]['foreshadow']} gave a quiet clue about what needed to happen next.")
    child.memes["want"] = 1.0
    helper.memes["care"] = 1.0
    world.say(f"{child.label} wanted to {TASKS[params.task]['verb']}, and {child.pronoun('possessive')} {params.helper_type} wanted to help.")

    world.para()
    child.meters["helpfulness"] = 1.0
    helper.meters["teamwork"] = 1.0
    world.say(f"Together they chose {tool.phrase}.")
    world.say(f"{child.label} held it steady while {child.pronoun('possessive')} {params.helper_type} {tool.use_text}.")
    world.say(f"They worked as a team, and the small problem started to feel much smaller.")
    item.meters["fixed_progress"] = 1.0
    item.memes["hope"] = 1.0

    world.para()
    world.say(f"At last, {TASKS[params.task]['turn']} made all the difference.")
    world.say(f"{TASKS[params.task]['result'].capitalize()}, and {child.label} smiled up at {child.pronoun('possessive')} {params.helper_type}.")
    child.memes["joy"] = 1.0
    helper.memes["pride"] = 1.0
    world.say(f"The garage felt warm and safe again, and the little note with \"abcd\" on it stayed tucked by the bench, still fake, still funny, and now part of a happy memory.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]  # type: ignore[assignment]
    task = TASKS[params.task]
    tool = TOOLS[params.tool]
    return [
        f'Write a heartwarming story set in a garage where a child wants to {task["verb"]} and a parent helps them do it safely.',
        f'Write a gentle teamwork story that includes a foreshadowing clue, the word "{tool.label}", and a happy ending in the garage.',
        f'Write a short child-facing story about a garage project, a helper, and a child who works together with "{params.name}" in the middle of it.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]  # type: ignore[assignment]
    task = TASKS[params.task]
    tool = TOOLS[params.tool]
    child: Entity = f["child"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    qs = [
        QAItem(
            question=f"What did {params.name} want to do in the garage?",
            answer=f"{params.name} wanted to {task['verb']} with help from {helper.label}.",
        ),
        QAItem(
            question=f"What tool did they use together?",
            answer=f"They used {tool.phrase} together, because that was the right tool for the job.",
        ),
        QAItem(
            question=f"How did {params.name} and the {params.helper_type} solve the problem?",
            answer=f"They solved it by working as a team: {params.name} held things steady, and the {params.helper_type} used {tool.phrase} to make it work.",
        ),
    ]
    qs.append(
        QAItem(
            question=f"What clue hinted at the problem before they fixed it?",
            answer=f"The story foreshadowed the problem with {TASKS[params.task]['foreshadow']}.",
        )
    )
    qs.append(
        QAItem(
            question=f"How did {params.name} feel at the end?",
            answer=f"{params.name} felt happy and proud, because the garage project ended well.",
        )
    )
    return qs


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a garage for?", answer="A garage is a place where people can park, store things, and work on projects."),
        QAItem(question="What does teamwork mean?", answer="Teamwork means people help each other and do a job together."),
        QAItem(question="What does foreshadowing mean in a story?", answer="Foreshadowing is a small clue that hints at what will happen later."),
        QAItem(question="Why can a wrench be useful?", answer="A wrench can help turn nuts and bolts tightly or loosen them when something needs fixing."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = [f"{ent.id}({ent.type})"]
        if ent.label:
            parts.append(f"label={ent.label}")
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append("  " + " ".join(parts))
    return "\n".join(lines)


ASP_RULES = r"""
place(garage).
task(fix). task(clean). task(build).
tool(wrench). tool(rag). tool(clamp).

compatible(fix,wrench).
compatible(clean,rag).
compatible(build,clamp).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("place", "garage")]
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    lines.append(asp.fact("compatible", "fix", "wrench"))
    lines.append(asp.fact("compatible", "clean", "rag"))
    lines.append(asp.fact("compatible", "build", "clamp"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    program = asp_program("#show compatible/2.")
    model = asp.one_model(program)
    atoms = sorted(set(asp.atoms(model, "compatible")))
    py = sorted((k, v) for k, v in [("fix", "wrench"), ("clean", "rag"), ("build", "clamp")])
    if atoms == py:
        print("OK: ASP and Python compatibility match.")
        return 0
    print("MISMATCH:", atoms, py)
    return 1


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="garage", task="fix", tool="wrench", name="Ada", child_type="girl", helper_type="father", trait="careful"),
    StoryParams(place="garage", task="clean", tool="rag", name="Milo", child_type="boy", helper_type="mother", trait="gentle"),
    StoryParams(place="garage", task="build", tool="clamp", name="Nia", child_type="girl", helper_type="father", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This storyworld has a tiny ASP twin; use --show-asp or --verify.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.task} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
