#!/usr/bin/env python3
"""A gentle whodunit about a copper strip, a davenport, and a brave sharing clue."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


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
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    cause: str
    result: str


@dataclass
class World:
    hero: str
    friend: str
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    clues: list[str] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def record(self, kind: str, text: str, cause: str, result: str) -> None:
        self.history.append(Event(kind, text, cause, result))
        self.paragraphs.append(text)

    def render(self) -> str:
        return "\n\n".join(self.paragraphs)


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    copper_owner: str
    suspect: str
    seed: Optional[int] = None


PLACES = {
    "parlor": "the sunny parlor",
    "library": "the quiet library",
    "clubhouse": "the little clubhouse",
}

HEROES = ["Luna", "Milo", "Nora", "Theo"]
FRIENDS = ["Ari", "Pip", "June", "Sam"]
OWNERS = ["Grandma", "Mr. Fox", "Aunt Bea"]
SUSPECTS = ["Pip", "June", "Sam", "Mr. Fox"]


def build_world(params: StoryParams) -> World:
    if params.hero == params.friend:
        raise StoryError("The detective and friend must have different names.")
    if params.suspect == params.hero:
        raise StoryError("The detective cannot be the suspected person.")

    world = World(params.hero, params.friend, params.place)
    hero = world.add(Entity(params.hero, "character", params.hero))
    friend = world.add(Entity(params.friend, "character", params.friend))
    davenport = world.add(Entity("davenport", "furniture", "davenport"))
    strip = world.add(Entity("strip", "object", "copper strip"))
    box = world.add(Entity("sharing_box", "object", "sharing box"))

    hero.memes["bravery"] = 0
    hero.memes["curiosity"] = 1
    friend.memes["worry"] = 1
    davenport.meters["hiding_places"] = 1
    strip.meters["found"] = 0
    box.meters["shared"] = 0

    world.facts.update(
        hero=hero,
        friend=friend,
        davenport=davenport,
        strip=strip,
        box=box,
        owner=params.copper_owner,
        suspect=params.suspect,
        solved=False,
    )
    return world


def investigate(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    owner = str(world.facts["owner"])
    suspect = str(world.facts["suspect"])

    world.record(
        "arrival",
        f"{hero.label} and {friend.label} were playing detectives in {world.place}. "
        f"{owner}'s shiny copper strip had vanished from a small sharing box. "
        f'"The last person near it was {suspect}," {friend.label} whispered. '
        f'"Then we must ask questions, not point fingers," {hero.label} said.',
        "The copper strip was missing, and a misunderstanding made the children suspect someone.",
        f"{hero.label} chose to investigate carefully instead of blaming {suspect}.",
    )
    world.clues.append("the davenport had a soft gap beneath one cushion")
    world.record(
        "clue",
        f"They searched the table, the rug, and the davenport. "
        f"Under one cushion, {hero.label} noticed a thin line of copper color. "
        f'"I see a clue," {hero.label} said. "But a clue is not the same as a culprit."',
        "The davenport had a hiding place, and a copper-colored glint appeared beneath its cushion.",
        f"They had a place to search without deciding who was guilty.",
    )


def solve(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    strip: Entity = world.facts["strip"]  # type: ignore[assignment]
    suspect = str(world.facts["suspect"])
    owner = str(world.facts["owner"])

    hero.memes["bravery"] = 1
    strip.meters["found"] = 1

    world.record(
        "discovery",
        f"{hero.label} took a brave breath and lifted the cushion. "
        f"The missing copper strip was there, tucked beside a lost button. "
        f'"{suspect} did not take it," {hero.label} said. '
        f'"It must have slipped when we shared the davenport." '
        f'{friend.label} nodded. "I was mistaken. I am glad you checked."',
        "The copper strip was beneath the davenport cushion, so the suspicion was a misunderstanding.",
        f"{hero.label} and {friend.label} learned that {suspect} had not stolen anything.",
    )

    box: Entity = world.facts["box"]  # type: ignore[assignment]
    box.meters["shared"] = 1
    world.facts["solved"] = True
    world.record(
        "sharing",
        f"{hero.label} returned the copper strip to {owner}. "
        f"{owner} smiled and placed it in the sharing box with room for everyone. "
        f'"Next time, we can search together," {friend.label} said. '
        f'"Together is better," {hero.label} replied.',
        "The children shared the truth and included everyone instead of keeping the discovery to themselves.",
        "The copper strip rested safely in the sharing box, while the friends made peace.",
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    investigate(world)
    solve(world)
    prompts = [
        "Write a gentle whodunit about a missing copper strip beneath a davenport.",
        f"Tell a child-facing mystery in {world.place} where bravery corrects a misunderstanding.",
    ]
    story_qa = [
        QAItem("Why did the children begin investigating?", world.history[0].cause + " " + world.history[0].result),
        QAItem("Where was the copper strip found?", world.history[1].cause + " " + world.history[1].result),
        QAItem("What misunderstanding was corrected?", world.history[2].cause + " " + world.history[2].result),
        QAItem("How did the friends resolve the mystery?", world.history[3].cause + " " + world.history[3].result),
    ]
    world_qa = [
        QAItem(
            "What is a davenport?",
            "A davenport is a comfortable sofa or couch where people can sit together.",
        ),
        QAItem(
            "What is copper?",
            "Copper is a reddish-brown metal that can be shaped into useful objects.",
        ),
        QAItem(
            "Why is sharing helpful?",
            "Sharing lets people use good things together and helps everyone feel included.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


ASP_RULES = r"""
found(strip) :- beneath(strip, davenport).
solved :- found(strip), brave(detective), corrected(misunderstanding).
shared(strip) :- solved, sharing(box).
#show solved/0.
#show shared/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("beneath", "strip", "davenport"),
            asp.fact("brave", "detective"),
            asp.fact("corrected", "misunderstanding"),
            asp.fact("sharing", "box"),
        ]
    )


def asp_program(show: str = "#show solved/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A gentle copper-strip whodunit.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--copper-owner")
    parser.add_argument("--suspect")
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
    hero = args.hero or rng.choice(HEROES)
    friend_choices = [name for name in FRIENDS if name != hero]
    friend = args.friend or rng.choice(friend_choices)
    suspect = args.suspect or rng.choice([name for name in SUSPECTS if name != hero])
    return StoryParams(
        place=args.place or rng.choice(sorted(PLACES)),
        hero=hero,
        friend=friend,
        copper_owner=args.copper_owner or rng.choice(OWNERS),
        suspect=suspect,
    )


CURATED = [
    StoryParams("parlor", "Luna", "Pip", "Grandma", "Pip"),
    StoryParams("library", "Milo", "June", "Mr. Fox", "June"),
    StoryParams("clubhouse", "Nora", "Sam", "Aunt Bea", "Sam"),
]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.text}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)


def verify() -> int:
    sample = generate(CURATED[0])
    world = sample.world
    assert world is not None
    assert world.facts["solved"] is True
    assert world.get("strip").meters["found"] == 1
    assert world.get("sharing_box").meters["shared"] == 1
    assert "davenport" in sample.story
    assert "copper" in sample.story
    assert "misunderstanding" in sample.story
    assert "brave" in sample.story
    assert "sharing" in sample.story
    assert all(event.text in sample.story for event in world.history)
    assert all(q.answer.endswith(".") for q in sample.story_qa)
    try:
        import asp
        atoms = asp.one_model(asp_program("#show solved/0."))
        assert asp.atoms(atoms, "solved") == [()]
    except ImportError:
        pass
    print("OK: whodunit state, prose, QA, and ASP checks passed.")
    return 0


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
    if args.n < 1:
        raise SystemExit("-n must be at least 1")
    if args.show_asp:
        print(asp_program("#show solved/0.\n#show shared/1."))
        return
    if args.verify:
        raise SystemExit(verify())
    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program("#show solved/0.\n#show shared/1."))
            print("Solved atoms:")
            for atom in model:
                print(f"  {atom}")
        except ImportError as exc:
            raise SystemExit("ASP mode requires clingo.") from exc
        return

    rng = random.Random(args.seed)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        for index in range(args.n):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            params.seed = args.seed
            samples.append(generate(params))

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [sample.to_dict() for sample in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### {sample.params.hero}'s copper-strip mystery" if args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
