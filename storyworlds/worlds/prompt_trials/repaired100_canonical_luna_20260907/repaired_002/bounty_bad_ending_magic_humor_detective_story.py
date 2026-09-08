#!/usr/bin/env python3
"""
A tiny detective storyworld about a mysterious bounty, a magical clue, and a
case that ends badly in a funny way.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


CASES = {
    "moon_coin": {
        "bounty": "a silver moon coin",
        "clue": "a trail of purple dust",
        "magic": "the coin whispers whenever a lie is told",
        "culprit": "the mayor's enchanted goose",
        "bad": "the goose flew away with the bounty and the detective's hat",
        "ending": "At midnight, the goose wore the hat on the town fountain.",
    },
    "vanishing_pie": {
        "bounty": "a golden pie medal",
        "clue": "three buttery footprints",
        "magic": "the medal points toward whoever is thinking about pie",
        "culprit": "the invisible baker",
        "bad": "the medal led everyone into a pantry and locked the door",
        "ending": "By breakfast, the detective was still inside, sharing crumbs with a broom.",
    },
    "singing_key": {
        "bounty": "a brass key that sings",
        "clue": "a blue feather humming softly",
        "magic": "the key unlocks only doors that tell jokes",
        "culprit": "the courthouse raven",
        "bad": "the raven snatched the key and flew into the evidence tower",
        "ending": "The tower door opened, and every old case file began laughing.",
    },
}

DETECTIVE_NAMES = ["Luna", "Pip", "Mara", "Nico"]
HELPERS = ["Inspector Bean", "Aunt Dot", "Clerk Peep"]
OPENERS = [
    "On a rainy Tuesday, Detective {detective} found a bounty notice under the bakery door.",
    "The town bell rang thirteen times when Detective {detective} accepted a strange bounty.",
    "At dawn, Detective {detective} discovered a glittering bounty pinned to a pigeon.",
]
SCENES = [
    "The station smelled of wet umbrellas, pepper, and one suspicious biscuit.",
    "Rain tapped the windows while the evidence shelf sneezed dust.",
    "The town square was quiet except for a statue that kept changing hats.",
]


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    case_id: str
    detective: Entity
    helper: Entity
    suspect: Entity
    bounty: Entity
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def mark(self, text: str) -> None:
        self.trace.append(text)


@dataclass
class StoryParams:
    case: str = "moon_coin"
    detective: str = "Luna"
    helper: str = "Inspector Bean"
    seed: Optional[int] = None


def build_world(params: StoryParams) -> World:
    if params.case not in CASES:
        raise StoryError(f"Unknown case: {params.case}")
    if not params.detective.strip():
        raise StoryError("Detective name must not be empty.")
    if not params.helper.strip():
        raise StoryError("Helper name must not be empty.")

    data = CASES[params.case]
    detective = Entity(params.detective, "detective", params.detective, location="station")
    helper = Entity(params.helper, "helper", params.helper, location="station")
    suspect = Entity("suspect", "suspect", data["culprit"], location="square")
    bounty = Entity("bounty", "object", data["bounty"], owner="town", location="station")
    world = World(params.case, detective, helper, suspect, bounty)
    for entity in (detective, helper, suspect, bounty):
        world.add(entity)
    world.facts.update(data)
    return world


def investigate(world: World) -> None:
    d, h, s, b = world.detective, world.helper, world.suspect, world.bounty
    d.memes["curiosity"] = 1
    h.memes["doubt"] = 1
    world.mark(f"{d.id} accepted the bounty to find {b.label}.")
    world.mark(f"The clue appeared: {world.facts['clue']}.")
    s.meters["suspicion"] = 1
    world.mark(f"The trail pointed toward {s.label}.")
    d.memes["confidence"] = 1


def solve_badly(world: World) -> None:
    d, h, s, b = world.detective, world.helper, world.suspect, world.bounty
    d.memes["confidence"] += 1
    world.mark(f"{d.id} confronted {s.label}.")
    world.mark(f'The magic revealed: {world.facts["magic"]}.')
    h.memes["alarm"] = 1
    s.meters["mischief"] = 1
    b.location = "tower"
    d.location = "fountain"
    world.mark(world.facts["bad"])


def render_story(world: World, opener: str, scene: str) -> str:
    d, h, s, b = world.detective, world.helper, world.suspect, world.bounty
    return "\n\n".join(
        [
            opener.format(detective=d.id),
            f"{scene} {d.id} studied the notice. It promised {b.label} to anyone who solved the town's strangest mystery.",
            f'"I will take the case," {d.id} said. "{h.id}, bring the magnifying glass."',
            f'"Should I bring a snack too?" {h.id} asked. "Detectives think better when they are not chewing their own sleeves."',
            f"{d.id} followed {world.facts['clue']} from the station to the square. The trail ended beside {s.label}, who was hiding behind a sign that said NO HIDING.",
            f'"Aha!" said {d.id}. "You took the bounty."',
            f'"I did not," said {s.label}.',
            f'"Then the magic will tell us," said {d.id}. The magic revealed that {world.facts['magic']}.',
            f"The clue was clear at last: {s.label} had taken the bounty, but not for a sensible reason. {world.facts['bad']}",
            f'"This is a bad ending," {h.id} whispered.',
            f'"A very bad ending," said {d.id}, watching the getaway. {world.facts["ending"]}',
        ]
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a humorous detective story in which {world.detective.id} investigates a bounty for {world.bounty.label}.",
        f"Use the clue {world.facts['clue']} and the magic that {world.facts['magic']}.",
        f"End badly but amusingly when {world.facts['culprit']} escapes with the bounty.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What bounty was Detective Luna investigating?",
            f"{world.detective.id} was investigating a bounty for {world.bounty.label}.",
        ),
        QAItem(
            "What clue helped solve the mystery?",
            f"The clue was {world.facts['clue']}, which led the detective toward {world.suspect.label}.",
        ),
        QAItem(
            "How did magic help?",
            f"The magic said that {world.facts['magic']}, helping reveal the truth.",
        ),
        QAItem(
            "Why was the ending bad?",
            f"The ending was bad because {world.facts['bad']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a bounty?", "A bounty is a reward offered for completing a task or finding someone or something."),
        QAItem("What does a detective do?", "A detective gathers clues and reasons about a mystery."),
        QAItem("What is magic in a story?", "Magic is an imaginary power that can make unusual things happen."),
        QAItem("What makes humor?", "Humor often comes from a surprising, silly, or unexpected situation."),
    ]


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else 0)
    world = build_world(params)
    investigate(world)
    solve_badly(world)
    story = render_story(world, rng.choice(OPENERS), rng.choice(SCENES))
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story Q&A ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind} location={entity.location} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.extend(f"  event: {event}" for event in world.trace)
    return "\n".join(lines)


ASP_RULES = r"""
kind(detective).
kind(helper).
kind(suspect).
kind(bounty).
magic(clue).
has_clue(detective, clue).
bounty_case(detective, bounty).
suspect_found(detective, suspect).
bad_ending(detective) :- bounty_case(detective, bounty), suspect_found(detective, suspect), magic(clue).
valid_story(detective) :- bad_ending(detective).
#show valid_story/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("kind", "detective"),
            asp.fact("kind", "helper"),
            asp.fact("kind", "suspect"),
            asp.fact("kind", "bounty"),
            asp.fact("magic", "clue"),
            asp.fact("has_clue", "detective", "clue"),
            asp.fact("bounty_case", "detective", "bounty"),
            asp.fact("suspect_found", "detective", "suspect"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}"


def verify() -> int:
    try:
        import asp
        atoms = asp.one_model(asp_program())
        valid = bool(asp.atoms(atoms, "valid_story"))
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    if not valid:
        print("ASP verification failed.")
        return 1
    sample = generate(StoryParams(seed=7))
    if not sample.story or "bounty" not in sample.story.lower():
        print("Story verification failed.")
        return 1
    print("OK: ASP parity and generated story checks passed.")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        case=args.case or rng.choice(list(CASES)),
        detective=args.detective or rng.choice(DETECTIVE_NAMES),
        helper=args.helper or rng.choice(HELPERS),
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A humorous magical detective storyworld about a bounty.")
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--detective")
    parser.add_argument("--helper")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(verify())
    if args.asp:
        try:
            import asp
            print(json.dumps([str(atom) for atom in asp.one_model(asp_program())], indent=2))
        except Exception as exc:
            raise StoryError(f"ASP mode failed: {exc}") from exc
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = len(CASES) if args.all else max(1, args.n)
    samples = []
    for i in range(count):
        rng = random.Random(base_seed + i)
        params = resolve_params(args, rng)
        params.seed = base_seed + i
        samples.append(generate(params))

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [sample.to_dict() for sample in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
