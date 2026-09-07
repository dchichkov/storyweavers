#!/usr/bin/env python3
"""A small dining-room quest about deciding what kindness can do.

A child notices a quiet problem at the dining table: a darling keepsake is
hidden beneath a pile of unwashed dishes. The child must decide whether to
wait, ask, or help. Inner thoughts create suspense, while a gentle exchange
turns uncertainty into shared work and a warm ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    location: str = "dining room"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def change_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meter(key) + amount

    def feel(self, key: str, amount: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class Event:
    kind: str
    actor: str
    target: str
    text: str
    cause: str
    result: str


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(
        self,
        kind: str,
        text: str,
        *,
        actor: str,
        target: str,
        cause: str,
        result: str,
    ) -> None:
        self.history.append(Event(kind, actor, target, text, cause, result))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    name: str
    companion: str
    object_kind: str
    problem: str
    decision: str
    trait: str
    seed: Optional[int] = None


OBJECTS = {
    "cup": {
        "phrase": "a darling blue cup",
        "label": "the blue cup",
        "ending": "the blue cup shone beside the warm teapot",
    },
    "napkin": {
        "phrase": "a darling cloth napkin embroidered with a sun",
        "label": "the sun napkin",
        "ending": "the sun on the napkin seemed to smile from the clean table",
    },
    "spoon": {
        "phrase": "a darling little silver spoon",
        "label": "the little silver spoon",
        "ending": "the little spoon rested in its own bright place",
    },
}

PROBLEMS = {
    "hidden": {
        "setup": "was hidden beneath a wobbling stack of breakfast dishes",
        "risk": "the stack might tumble if it was pulled too quickly",
    },
    "stained": {
        "setup": "had a berry stain beside the plates",
        "risk": "the stain might stay if no one washed it soon",
    },
    "missing": {
        "setup": "was missing from the table just before supper",
        "risk": "someone might feel sad if it was not found",
    },
}

DECISIONS = {
    "ask": "ask the grown-up before touching the table",
    "help": "help clear the safe dishes first",
    "wait": "wait quietly and watch for a safe moment",
}

TRAITS = ["careful", "curious", "patient", "hopeful"]
NAMES = ["Milo", "Nina", "Ivy", "Sam", "Tessa", "Owen"]
COMPANIONS = ["Mom", "Dad", "Aunt May", "Grandma"]

KNOWLEDGE = {
    "hidden": QAItem(
        "Why should a child be careful near a tall stack of dishes?",
        "A child should be careful because dishes can fall and break, so an adult can help make the table safe.",
    ),
    "stained": QAItem(
        "Why is it helpful to wash a cloth soon after a berry stain appears?",
        "Washing a cloth soon can loosen the berry stain before it dries and becomes harder to remove.",
    ),
    "missing": QAItem(
        "Why can looking together help when something is missing?",
        "Looking together helps because another person may remember a place or notice a small clue.",
    ),
}


def valid_params(params: StoryParams) -> None:
    if params.object_kind not in OBJECTS:
        raise StoryError("The darling object is not in the dining-room collection.")
    if params.problem not in PROBLEMS:
        raise StoryError("That dining-room problem is not supported.")
    if params.decision not in DECISIONS:
        raise StoryError("That decision is not part of this quest.")
    if params.trait not in TRAITS:
        raise StoryError("That character trait is not supported.")
    reserved = {"child", "companion", "darling", "table", "dishes", "answer"}
    if params.name.lower() in reserved:
        raise StoryError("The child's name must be distinct from story objects.")


def build_world(params: StoryParams) -> World:
    valid_params(params)
    world = World(setting="dining room")
    child = world.add(
        Entity(
            id="child",
            kind="character",
            label=params.name,
            location="dining room",
            memes={"care": 1.0, "curiosity": 1.0 if params.trait == "curious" else 0.0},
        )
    )
    companion = world.add(
        Entity(
            id="companion",
            kind="character",
            label=params.companion,
            location="dining room",
            memes={"warmth": 1.0},
        )
    )
    darling = world.add(
        Entity(
            id="darling",
            kind="keepsake",
            label=OBJECTS[params.object_kind]["label"],
            owner="child",
            location="dining room",
            meters={"safe": 0.0},
        )
    )
    table = world.add(
        Entity(
            id="table",
            kind="furniture",
            label="dining table",
            location="dining room",
            meters={"dishes": 1.0},
        )
    )
    world.add(
        Entity(
            id="dishes",
            kind="objects",
            label="breakfast dishes",
            location="dining room",
            meters={"stacked": 1.0},
        )
    )
    world.facts.update(
        child=child,
        companion=companion,
        darling=darling,
        table=table,
        problem=params.problem,
        decision=params.decision,
        object_kind=params.object_kind,
        resolved=False,
    )
    return world


def begin_quest(world: World, params: StoryParams) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    darling: Entity = world.facts["darling"]  # type: ignore[assignment]
    issue = PROBLEMS[params.problem]
    cause = f"{darling.label.capitalize()} {issue['setup']}."
    result = "The small dining-room quest had begun."
    world.record(
        "notice",
        f'{params.name} entered the dining room and noticed that {darling.label} '
        f'{issue["setup"]}. The chairs stood around the table like quiet horses. '
        f'{params.name} loved the darling keepsake and wanted to make things right. '
        f'“I need to decide carefully,” {params.name} whispered.',
        actor=child.id,
        target=darling.id,
        cause=cause,
        result=result,
    )


def inner_monologue(world: World, params: StoryParams) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    darling: Entity = world.facts["darling"]  # type: ignore[assignment]
    issue = PROBLEMS[params.problem]
    child.feel("suspense", 1.0)
    if params.decision == "ask":
        thought = (
            f'“If I ask first, {darling.label} may stay safe,” {params.name} thought. '
            f'“But what if I have to wait?”'
        )
    elif params.decision == "help":
        thought = (
            f'“I can make a safe path,” {params.name} thought. '
            f'“Then the darling keepsake will not be trapped.”'
        )
    else:
        thought = (
            f'“Perhaps the right moment is coming,” {params.name} thought. '
            f'“I must not hurry just because I am worried.”'
        )
    world.para()
    world.record(
        "think",
        f'{thought} The room was almost still, except for one tiny clink from the table. '
        f'{issue["risk"].capitalize()}.',
        actor=child.id,
        target=darling.id,
        cause=issue["risk"].capitalize() + ".",
        result="The child chose to think before acting.",
    )


def make_decision(world: World, params: StoryParams) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    darling: Entity = world.facts["darling"]  # type: ignore[assignment]
    table: Entity = world.facts["table"]  # type: ignore[assignment]
    world.para()

    if params.decision == "ask":
        text = (
            f'“{params.companion}, may I have help?” {params.name} asked. '
            f'“Of course, darling,” {params.companion} answered. '
            f'Together they steadied the dishes and lifted the top plate.'
        )
        result = "The adult helped make the table safe before the keepsake was touched."
        table.change_meter("safe", 1.0)
        child.feel("trust", 1.0)
    elif params.decision == "help":
        text = (
            f'“I will clear the safe dishes first,” {params.name} said. '
            f'“Good deciding,” {params.companion} replied. '
            f'{params.name} carried each light plate to the counter while '
            f'{params.companion} held the stack steady.'
        )
        result = "A clear space appeared beside the keepsake."
        table.change_meter("safe", 1.0)
        child.change_meter("helping", 1.0)
    else:
        text = (
            f'“I can wait,” {params.name} said. “Will you stay with me?” '
            f'“I will,” {params.companion} promised. '
            f'They watched until the dishes stopped wobbling, then moved together.'
        )
        result = "Patience gave them a safe moment to act."
        table.change_meter("safe", 1.0)
        child.feel("patience", 1.0)

    world.record(
        "decide",
        text,
        actor=child.id,
        target=companion.id,
        cause=f"{params.name} decided to {DECISIONS[params.decision]}.",
        result=result,
    )
    darling.meters["safe"] = 1.0


def resolve_quest(world: World, params: StoryParams) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    darling: Entity = world.facts["darling"]  # type: ignore[assignment]
    table: Entity = world.facts["table"]  # type: ignore[assignment]
    world.para()

    if params.problem == "stained":
        action = f"{params.name} and {params.companion} dabbed the berry mark with cool water."
        consequence = f"The mark faded, and {darling.label} was ready for another happy meal."
    elif params.problem == "missing":
        action = (
            f"{params.name} looked beneath the napkins while {params.companion} checked "
            f"the window seat. They found {darling.label} beside a basket."
        )
        consequence = f"The missing keepsake came back to the dining table."
    else:
        action = (
            f"{params.companion} moved the last dish, and {params.name} reached for "
            f"{darling.label} with two careful hands."
        )
        consequence = f"{darling.label.capitalize()} came free without a crash."

    child.feel("relief", 1.0)
    darling.meters["safe"] = 2.0
    table.meters["dishes"] = 0.0
    world.record(
        "resolve",
        f'{action} {consequence} “We did it together,” {params.name} said. '
        f'“Yes, darling,” {params.companion} replied, giving a gentle hug.',
        actor=child.id,
        target=darling.id,
        cause=f"The decision made the dining room safe enough to care for {darling.label}.",
        result=consequence,
    )


def finish(world: World, params: StoryParams) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    darling: Entity = world.facts["darling"]  # type: ignore[assignment]
    ending = OBJECTS[params.object_kind]["ending"]
    world.para()
    world.record(
        "ending",
        f'The dining room felt bright again. {ending.capitalize()}. '
        f'{params.name} set a small flower beside it, and {params.companion} poured '
        f'warm milk into a clean glass. The quest had ended, not with a grand prize, '
        f'but with a safe table, a darling keepsake, and two people smiling together.',
        actor=child.id,
        target=darling.id,
        cause="The child and companion shared the work instead of rushing alone.",
        result="The dining room became a welcoming place again.",
    )
    world.facts["resolved"] = True
    companion.feel("joy", 1.0)
    child.feel("joy", 1.0)


def tell(params: StoryParams) -> World:
    world = build_world(params)
    begin_quest(world, params)
    inner_monologue(world, params)
    make_decision(world, params)
    resolve_quest(world, params)
    finish(world, params)
    return world


def generation_prompts(world: World) -> list[str]:
    params_problem = world.facts["problem"]
    decision = world.facts["decision"]
    obj = world.facts["object_kind"]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    return [
        f"Write a heartwarming dining-room quest about {child.label}, a darling {obj}, "
        f"and the need to {DECISIONS[decision]}. Include suspense and inner monologue.",
        f"Tell a gentle story in which {child.label} notices that the darling keepsake is "
        f"{PROBLEMS[params_problem]['setup']}, speaks with {companion.label}, and makes a careful decision.",
    ]


def story_qa(world: World) -> list[QAItem]:
    questions = {
        "notice": "What problem did the child notice in the dining room?",
        "think": "Why did the child pause to think?",
        "decide": "What decision did the child make?",
        "resolve": "How did the child and companion solve the problem?",
        "ending": "What showed that the dining room was peaceful again?",
    }
    return [
        QAItem(question=questions[event.kind], answer=f"{event.cause} {event.result}")
        for event in world.history
        if event.kind in questions
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [KNOWLEDGE[world.facts["problem"]]]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: kind={entity.kind}, location={entity.location}, "
            f"meters={meters}, memes={memes}"
        )
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.text}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_choice(ask) :- decision(ask).
safe_choice(help) :- decision(help).
safe_choice(wait) :- decision(wait).
valid_problem(P) :- problem(P).
valid_story(P, D) :- valid_problem(P), decision(D), safe_choice(D).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for problem in PROBLEMS:
        lines.append(asp.fact("problem", problem))
    for decision in DECISIONS:
        lines.append(asp.fact("decision", decision))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "valid_story"))
    expected = {(problem, decision) for problem in PROBLEMS for decision in DECISIONS}
    if found != expected:
        print("MISMATCH: ASP and Python decision sets differ.")
        return 1
    checked = 0
    for problem, decision in sorted(expected):
        params = StoryParams(
            name="Robin",
            companion="Grandma",
            object_kind="cup",
            problem=problem,
            decision=decision,
            trait="careful",
        )
        sample = generate(params)
        check_sample(sample)
        checked += 1
    print(f"OK: {len(found)} ASP/Python plans and {checked} story checks.")
    return 0


def check_sample(sample: StorySample) -> None:
    world = sample.world
    assert world is not None
    assert world.facts["resolved"] is True
    assert world.entities["darling"].meter("safe") == 2.0
    assert world.entities["table"].meter("dishes") == 0.0
    assert len(sample.story_qa) == 5
    assert all(event.text in sample.story for event in world.history)
    # QA outcomes paraphrase events; validate against trace-derived answers.
    assert sample.story == world.render()
    assert sample.story_qa == story_qa(world)
    assert not any(mark in sample.story for mark in ("{", "}", "__", "meters=", "memes="))
    assert "darling" in sample.story.lower()
    assert "decide" in sample.story.lower()


CURATED = [
    StoryParams("Nina", "Mom", "cup", "hidden", "ask", "careful"),
    StoryParams("Milo", "Dad", "napkin", "stained", "help", "curious"),
    StoryParams("Ivy", "Grandma", "spoon", "missing", "wait", "patient"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming dining-room quest about deciding with care."
    )
    parser.add_argument("--name")
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--object", dest="object_kind", choices=sorted(OBJECTS))
    parser.add_argument("--problem", choices=sorted(PROBLEMS))
    parser.add_argument("--decision", choices=sorted(DECISIONS))
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        object_kind=args.object_kind or rng.choice(sorted(OBJECTS)),
        problem=args.problem or rng.choice(sorted(PROBLEMS)),
        decision=args.decision or rng.choice(sorted(DECISIONS)),
        trait=args.trait or rng.choice(TRAITS),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    valid_params(params)
    world = tell(params)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    return sample


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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
    if args.n < 1:
        raise SystemExit("-n must be at least 1")
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        pairs = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(pairs)} valid dining-room plans:")
        for problem, decision in pairs:
            print(f"  {problem:8} -> {decision}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name}: dining-room quest"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
