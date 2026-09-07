#!/usr/bin/env python3
"""
A gentle fable about a small team that buries a seed together.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child_name: str = "Mara"
    animal_one: str = "Rabbit"
    animal_two: str = "Mole"
    animal_three: str = "Wren"
    place: str = "the meadow beside the old oak"
    seed_kind: str = "an acorn"
    obstacle: str = "the hard, stony ground"
    ending_image: str = "By spring, a bright green shoot lifted its leaves toward the sun."
    samples: list = field(default_factory=list)


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


PLACES = (
    "the meadow beside the old oak",
    "the sunny garden behind the cottage",
    "the quiet field near the brook",
    "the hill where the warm grass waved",
)

SEEDS = (
    "an acorn",
    "a sunflower seed",
    "a bean seed",
    "a little apple seed",
)

OBSTACLES = (
    "the hard, stony ground",
    "a mat of tangled roots",
    "a patch of dry earth",
    "a shallow trench left by the rain",
)

ENDINGS = (
    "By spring, a bright green shoot lifted its leaves toward the sun.",
    "When warm days returned, a young tree opened its first tiny leaves.",
    "Soon the buried seed woke beneath the soil and pushed up a brave green stem.",
    "At last, a little plant appeared, and every helper claimed one leaf as a friend.",
)


def tell(params: StoryParams) -> World:
    if not params.child_name.strip():
        raise StoryError("The child name cannot be empty.")
    if not params.seed_kind.strip():
        raise StoryError("The seed must have a name.")
    if not params.place.strip():
        raise StoryError("The story needs a place.")

    world = World(params)
    child = world.add(Entity("child", "character", params.child_name))
    rabbit = world.add(Entity("rabbit", "character", params.animal_one))
    mole = world.add(Entity("mole", "character", params.animal_two))
    wren = world.add(Entity("wren", "character", params.animal_three))
    seed = world.add(Entity("seed", "thing", params.seed_kind))

    world.facts.update(
        child=child,
        rabbit=rabbit,
        mole=mole,
        wren=wren,
        seed=seed,
        place=params.place,
        obstacle=params.obstacle,
    )

    child.memes["curiosity"] = 1.0
    rabbit.memes["helpfulness"] = 1.0
    mole.memes["helpfulness"] = 1.0
    wren.memes["helpfulness"] = 1.0
    seed.meters["depth"] = 0.0

    world.say(
        f"One bright morning, {params.child_name} found {params.seed_kind} shining in the grass at {params.place}."
    )
    world.say(
        f'"I will bury it here," said {params.child_name}, "and perhaps it will grow into something wonderful."'
    )

    world.para()
    world.say(
        f"But {params.obstacle} made the little task too difficult for one pair of hands."
    )
    world.say(
        f"{params.animal_one} tugged at the roots, {params.animal_two} loosened the earth, and {params.animal_three} carried soft leaves for a blanket."
    )

    world.para()
    world.fired.add("teamwork")
    rabbit.memes["teamwork"] = 1.0
    mole.memes["teamwork"] = 1.0
    wren.memes["teamwork"] = 1.0
    child.memes["teamwork"] = 1.0
    seed.meters["depth"] = 1.0
    world.say(
        f"Together, the team made a small hollow. {params.child_name} placed {params.seed_kind} inside, and the friends covered it with gentle soil."
    )
    world.say(
        f"They pressed the earth firm, sprinkled it with water, and marked the spot with three smooth stones."
    )

    world.para()
    world.fired.add("resolution")
    seed.memes["hope"] = 1.0
    child.memes["joy"] = 1.0
    world.say(
        f"Each friend had done a small part, but only their teamwork had made the hiding place ready."
    )
    world.say(
        f"{params.child_name} smiled at the quiet patch of earth. {params.ending_image}"
    )
    world.say(
        "The friends learned that a task may look too large for one, yet become light when many caring hearts share it."
    )

    return world


ASP_RULES = r"""
seed(seed).
team_member(child).
team_member(rabbit).
team_member(mole).
team_member(wren).
obstacle(ground).
buried(seed) :- seed(seed), teamwork(team).
teamwork(team) :- team_member(child), team_member(rabbit), team_member(mole), team_member(wren).
resolved(seed) :- buried(seed), teamwork(team).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("seed", "seed"),
            asp.fact("team_member", "child"),
            asp.fact("team_member", "rabbit"),
            asp.fact("team_member", "mole"),
            asp.fact("team_member", "wren"),
            asp.fact("obstacle", "ground"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> tuple[set[tuple], set[tuple]]:
    import asp

    model = asp.one_model(
        asp_program("#show teamwork/1.\n#show buried/1.\n#show resolved/1.")
    )
    return (
        set(asp.atoms(model, "teamwork")),
        set(asp.atoms(model, "buried")),
        set(asp.atoms(model, "resolved")),
    )


def asp_verify() -> int:
    teamwork, buried, resolved = asp_valid()
    if teamwork == {("team",)} and buried == {("seed",)} and resolved == {("seed",)}:
        sample = generate(StoryParams())
        if "teamwork" not in sample.story.lower() or "buried" not in sample.story.lower():
            print("MISMATCH: generated story does not exercise the verified outcome.")
            return 1
        print("OK: ASP and Python agree on the teamwork burial fable.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP teamwork:", sorted(teamwork))
    print("ASP buried:", sorted(buried))
    print("ASP resolved:", sorted(resolved))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a teamwork fable about burying a seed.")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        child_name=rng.choice(("Mara", "Timo", "Nia", "Pip")),
        animal_one=rng.choice(("Rabbit", "Squirrel", "Hedgehog")),
        animal_two=rng.choice(("Mole", "Badger", "Mouse")),
        animal_three=rng.choice(("Wren", "Robin", "Sparrow")),
        place=rng.choice(PLACES),
        seed_kind=rng.choice(SEEDS),
        obstacle=rng.choice(OBSTACLES),
        ending_image=rng.choice(ENDINGS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a fable about {f['child'].label} and friends who bury {f['seed'].label}.",
        f"Tell a teamwork story set in {f['place']}, where friends overcome {f['obstacle']}.",
        "Write a child-friendly fable showing that shared work can make a difficult task possible.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = world.params
    return [
        QAItem(
            question=f"What did {p.child_name} find in the grass?",
            answer=f"{p.child_name} found {p.seed_kind} shining in the grass at {p.place}.",
        ),
        QAItem(
            question=f"Why did {p.child_name} need help to bury {p.seed_kind}?",
            answer=f"{p.child_name} needed help because {p.obstacle} made the task too difficult for one pair of hands.",
        ),
        QAItem(
            question="How did the friends work as a team?",
            answer=f"{p.animal_one} tugged at the roots, {p.animal_two} loosened the earth, {p.animal_three} carried soft leaves, and {p.child_name} placed the seed in the hollow.",
        ),
        QAItem(
            question="What happened after the seed was buried?",
            answer=f"The friends covered it with soil, watered it, and waited. {p.ending_image}",
        ),
        QAItem(
            question="What lesson did the fable teach?",
            answer="The fable taught that a task that seems too large for one person can become light when caring friends share the work.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why are seeds buried in soil?",
            answer="Seeds are buried in soil so they can stay protected and receive water while their roots and shoots begin to grow.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means that people or animals cooperate and share their efforts to reach a common goal.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


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

    if args.show_asp:
        print(asp_program("#show teamwork/1.\n#show buried/1.\n#show resolved/1."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program("#show teamwork/1.\n#show buried/1.\n#show resolved/1.")
        )
        print("teamwork:", sorted(set(asp.atoms(model, "teamwork"))))
        print("buried:", sorted(set(asp.atoms(model, "buried"))))
        print("resolved:", sorted(set(asp.atoms(model, "resolved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 1 if args.all else max(1, args.n)
    samples: list[StorySample] = []

    for index in range(count):
        sample_seed = base_seed + index
        params = resolve_params(args, random.Random(sample_seed))
        params.seed = sample_seed
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
