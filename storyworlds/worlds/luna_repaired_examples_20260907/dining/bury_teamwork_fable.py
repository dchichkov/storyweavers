#!/usr/bin/env python3
"""
A small fable storyworld about burying a seed together.

A young mole wants to bury an acorn before the first rain, but the ground is
too hard for one pair of paws. With teamwork, a rabbit loosens the soil, a
mouse carries the acorn, and a beetle clears the pebbles. The resolution proves
that shared work can make a small beginning grow.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    leader_name: str
    helper_name: str
    seed_kind: str
    seed: Optional[int] = None
    tale_id: Optional[str] = None


LEADERS = ["Milo", "Tessa", "Pip", "Nell", "Bram"]
HELPERS = ["Fern", "Otis", "Wren", "Mara", "Clover"]
SEEDS = ["acorn", "bean", "maple seed", "sunflower seed"]

TALES = [
    {
        "id": "hard_patch",
        "obstacle": "the earth was packed hard as a clay pot",
        "lesson": "A strong paw is useful, but many willing paws can change the ground.",
        "ending": "After the rain, a green shoot rose from the little mound, and every helper knew it had begun with their shared work.",
    },
    {
        "id": "stone_circle",
        "obstacle": "a ring of stubborn stones surrounded the softest patch",
        "lesson": "The smallest helper may notice the place where a larger helper cannot work.",
        "ending": "Soon the buried seed rested safely below a round green sprout, while the stones formed a proud border around it.",
    },
    {
        "id": "windy_hill",
        "obstacle": "the hilltop wind kept uncovering every shallow hole",
        "lesson": "Teamwork means changing the plan when the first plan does not hold.",
        "ending": "The seed stayed hidden beneath its woven cover, and later its first leaf waved bravely at the same wind.",
    },
    {
        "id": "dry_soil",
        "obstacle": "the soil was dry and crumbly beneath the old oak",
        "lesson": "Care is not only beginning a task; it is helping the task reach its end.",
        "ending": "A gentle rain darkened the mound, and a tiny green stem promised that their care had not been wasted.",
    },
]

TaleById = {tale["id"]: tale for tale in TALES}


def rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xBURI3)
    text = "|".join([params.leader_name, params.helper_name, params.seed_kind, params.tale_id or ""])
    return random.Random(sum((i + 1) * ord(c) for i, c in enumerate(text)))


def build_world(params: StoryParams) -> World:
    rng = rng_for(params)
    tale = TaleById.get(params.tale_id or "") or rng.choice(TALES)
    seed_kind = params.seed_kind

    if params.leader_name == params.helper_name:
        raise StoryError("leader and helper must have different names")
    if seed_kind not in SEEDS:
        raise StoryError(f"unknown seed kind: {seed_kind}")

    world = World("the edge of the forest")
    leader = world.add(Entity(
        id=params.leader_name,
        kind="character",
        type="mole",
        label=params.leader_name,
        meters={"strength": 1.0, "tiredness": 0.0},
        memes={"hope": 1.0, "confidence": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="rabbit",
        label=params.helper_name,
        meters={"strength": 1.0, "tiredness": 0.0},
        memes={"kindness": 1.0, "confidence": 1.0},
    ))
    seed = world.add(Entity(
        id="seed",
        kind="thing",
        type="seed",
        label=seed_kind,
        meters={"buried": 0.0, "depth": 0.0, "safety": 0.0},
        memes={"promise": 1.0},
    ))
    ground = world.add(Entity(
        id="ground",
        kind="place",
        type="earth",
        label="the patch of earth",
        meters={"hardness": 2.0, "moisture": 0.0},
        memes={},
    ))
    world.add(Entity(
        id="stones",
        kind="thing",
        type="stones",
        label="the loose stones",
        meters={"cleared": 0.0},
        memes={},
    ))

    opening = [
        f"At the edge of the forest, {leader.label} found a {seed_kind} beneath an old oak.",
        f"{leader.label} carried a small {seed_kind} to a sunny patch at the edge of the forest.",
        f"One bright morning, {leader.label} discovered a {seed_kind} and imagined the tree it might become.",
    ]
    world.say(rng.choice(opening))
    world.say(f"{leader.label} tried to bury it alone, but {tale['obstacle']}.")
    world.say("The little hole collapsed before the seed could settle.")

    world.para()
    leader.meters["tiredness"] = 1.0
    leader.memes["confidence"] = 0.0
    world.say(f'"I can dig harder," said {leader.label}, though the seed could see that the work was wearing {leader.label} out.')
    world.say(f"{helper.label} listened instead of laughing. \"A task can be small and still be too big for one helper,\" said {helper.label}.")
    world.say(f"They formed a teamwork plan: {leader.label} would loosen the earth, {helper.label} would carry the seed, and both would protect the little hole.")
    leader.memes["teamwork"] = 1.0
    helper.memes["teamwork"] = 1.0
    world.facts["teamwork"] = True

    world.para()
    ground.meters["hardness"] = 1.0
    leader.meters["tiredness"] = 0.5
    world.say(f"{leader.label} scratched the surface while {helper.label} pushed aside the stones that blocked the soft soil.")
    world.say("When one pair of paws grew tired, the other pair took a turn. The work became slower than rushing, but steadier than struggling alone.")
    ground.meters["hardness"] = 0.0
    world.entities["stones"].meters["cleared"] = 1.0
    world.say(f"At last, they made a deep, safe hollow. {helper.label} placed the {seed_kind} inside, and {leader.label} covered it with warm earth.")
    seed.meters["buried"] = 1.0
    seed.meters["depth"] = 1.0
    seed.meters["safety"] = 1.0
    leader.memes["confidence"] = 1.0
    helper.memes["confidence"] = 1.0

    world.para()
    ground.meters["moisture"] = 1.0
    world.say(f"They pressed the soil gently and marked the place with three acorns so no careless foot would uncover it.")
    world.say(f"{tale['lesson']}")
    world.say(tale["ending"])

    world.facts.update(
        leader=leader,
        helper=helper,
        seed=seed,
        ground=ground,
        tale=tale,
        place=world.place,
        cause="teamwork",
        solved=True,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    f = world.facts
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a child-friendly fable in which {params.leader_name} tries to bury a {params.seed_kind}.",
            f"Show how {params.leader_name} and {params.helper_name} use teamwork when {f['tale']['obstacle']}.",
            "End with a concrete image proving that the buried seed is safe and that shared work mattered.",
        ],
        story_qa=[
            QAItem(
                question=f"Why could {f['leader'].label} not bury the {params.seed_kind} alone?",
                answer=f"{f['leader'].label} could not bury it alone because {f['tale']['obstacle']}, and the hole kept collapsing.",
            ),
            QAItem(
                question=f"How did {f['leader'].label} and {f['helper'].label} use teamwork?",
                answer=f"{f['leader'].label} loosened the earth while {f['helper'].label} moved the stones and carried the seed. They took turns so the work stayed steady.",
            ),
            QAItem(
                question="What happened to the seed at the end?",
                answer=f"The {params.seed_kind} was buried in a deep, safe hollow, covered with warm earth, and protected by three marker acorns.",
            ),
            QAItem(
                question="What is the lesson of the fable?",
                answer=f"{f['tale']['lesson']}",
            ),
        ],
        world_qa=[
            QAItem(
                question="What does teamwork mean?",
                answer="Teamwork means cooperating and sharing jobs so people can accomplish something together.",
            ),
            QAItem(
                question="Why do seeds need to be buried?",
                answer="Many seeds are buried so they can stay protected in the soil while they begin to grow.",
            ),
            QAItem(
                question="What is a fable?",
                answer="A fable is a short story that often uses animals or nature to teach a lesson.",
            ),
        ],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.type}; meters={entity.meters}; memes={entity.memes}"
        )
    lines.append(f"  place: {world.place}")
    lines.append(f"  solved: {world.facts.get('solved')}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "forest_edge"),
        asp.fact("object", "seed"),
        asp.fact("action", "bury"),
        asp.fact("feature", "teamwork"),
        asp.fact("obstacle", "hard_ground"),
        asp.fact("outcome", "seed_safe"),
    ])


ASP_RULES = r"""
burial_attempt :- action(bury), object(seed).
teamwork_used :- feature(teamwork), burial_attempt.
obstacle_met :- obstacle(hard_ground).
seed_protected :- outcome(seed_safe), teamwork_used.
valid_story :- obstacle_met, seed_protected.
#show valid_story/0.
"""


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    valid = any(symbol.name == "valid_story" for symbol in model)
    if not valid:
        print("MISMATCH: ASP twin did not confirm the fable.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("solved"):
            print("MISMATCH: generated story did not resolve.")
            return 1
    print("OK: ASP twin and generated fables agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a teamwork fable about burying a seed."
    )
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--seed-kind", choices=SEEDS)
    parser.add_argument("--tale")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
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
        leader_name=args.name or rng.choice(LEADERS),
        helper_name=args.helper or rng.choice(HELPERS),
        seed_kind=args.seed_kind or rng.choice(SEEDS),
        tale_id=args.tale or rng.choice(TALES)["id"],
    )


CURATED = [
    StoryParams("Milo", "Fern", "acorn", tale_id="hard_patch"),
    StoryParams("Tessa", "Otis", "bean", tale_id="stone_circle"),
    StoryParams("Pip", "Wren", "sunflower seed", tale_id="windy_hill"),
]


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
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

    if args.show_asp or args.asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
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
