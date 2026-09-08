#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_here))))
if os.path.exists(os.path.join(_root, "results.py")):
    sys.path.insert(0, _root)
from results import QAItem, StoryError, StorySample


ASP_RULES = r"""
solvable :- clue(spoon), clue(moonbeam), clue(crumb), helper(smartypants).
answer(pantry) :- solvable, hiding_place(pantry).
"""


@dataclass
class StoryParams:
    child: str
    companion: str
    mood: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


NAMES = ["Luna", "Mira", "Nora", "Sami", "Ivy"]
COMPANIONS = ["the sleepy cat", "the small owl", "the gentle fox", "the old teddy bear"]
MOODS = ["curious", "patient", "brave", "thoughtful"]

JOURNEYS = [
    {
        "clue": "a tiny green smear on the windowsill",
        "answer": "the pantry",
        "method": "They followed the green smear past the quiet table and toward the pantry.",
        "image": "moonlight rested on the clean spoon while the pesto waited safely for breakfast",
    },
    {
        "clue": "three bright crumbs beside the blue rug",
        "answer": "the pantry",
        "method": "They counted the crumbs, which made a little trail toward the pantry door.",
        "image": "the house grew still again, with the pesto jar tucked safely on its shelf",
    },
    {
        "clue": "a warm basil scent beneath the kitchen chair",
        "answer": "the pantry",
        "method": "They bent low and followed the basil smell until it curled around the pantry door.",
        "image": "a soft green gleam shone from the shelf as everyone settled back to sleep",
    },
]

OPENINGS = [
    "When the bedtime stars blinked above the little house, {child} was getting ready for sleep.",
    "The lamps were low and the blankets were warm when {child} heard a tiny sound in the kitchen.",
    "Just before bedtime, {child} peeked from the bedroom and noticed that the moon made a silver path across the floor.",
]

MORALS = [
    "A quiet question and careful eyes can solve a mystery without making the night noisy.",
    "Even a small helper can find a big answer when friends listen together.",
    "Smart thinking is gentlest when it helps everyone feel safe.",
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(n, c, m) for n in NAMES for c in COMPANIONS for m in MOODS]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A gentle bedtime mystery about smartypants thinking and pesto.")
    parser.add_argument("--child", choices=NAMES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--mood", choices=MOODS)
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
        child=args.child or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        mood=args.mood or rng.choice(MOODS),
    )


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a gentle bedtime story containing the words "smartypants" and "pesto".',
        f"Tell a bedtime mystery in which {world.facts['child']} solves a small kitchen mystery with {world.facts['companion']}.",
        "Write a cozy Mystery to Solve where careful clues lead to a peaceful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem("Who noticed the mystery?", f"{f['child']} noticed the mystery before bedtime."),
        QAItem("What had gone missing?", "A little jar of pesto had vanished from the kitchen table."),
        QAItem("What clues helped solve the mystery?", f"The clues were {f['journey']['clue']}, a spoon, and the smell of basil."),
        QAItem("Who helped with the investigation?", f"{f['companion'].capitalize()} helped {f['child']} look carefully and listen."),
        QAItem("Where was the pesto found?", "The pesto was found safely in the pantry."),
        QAItem("What lesson did the story teach?", f"{f['moral']}"),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is pesto?", "Pesto is a savory green sauce often made with basil, nuts, cheese, oil, and garlic."),
        QAItem("What does smartypants mean?", "Smartypants is a playful word for someone who is clever."),
        QAItem("Why are clues useful?", "Clues are useful because they give hints that help us understand what happened."),
        QAItem("What makes a bedtime story cozy?", "A bedtime story is cozy when it feels gentle, safe, and peaceful at the end."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---", f"  setting: {world.setting}"]
    for entity in world.entities.values():
        lines.append(f"  {entity.id}: meters={entity.meters} memes={entity.memes}")
    lines.append(f"  mystery answer: {world.facts.get('answer')}")
    return "\n".join(lines)


def tell(params: StoryParams) -> World:
    if params.child not in NAMES:
        raise StoryError(f"Unknown child: {params.child}")
    if params.companion not in COMPANIONS:
        raise StoryError(f"Unknown companion: {params.companion}")
    if params.mood not in MOODS:
        raise StoryError(f"Unknown mood: {params.mood}")

    seed = params.seed if params.seed is not None else sum(map(ord, params.child + params.companion + params.mood))
    rng = random.Random(seed)
    journey = rng.choice(JOURNEYS)
    moral = rng.choice(MORALS)
    world = World("the little house at bedtime")
    child = world.add(Entity(params.child, "child", params.child, memes={"calm": 1.0}))
    companion = world.add(Entity("companion", "companion", params.companion, memes={"help": 1.0}))
    pesto = world.add(Entity("pesto", "food", "a little jar of pesto", meters={"safe": 0.0}))
    spoon = world.add(Entity("spoon", "clue", "a silver spoon", meters={"shiny": 1.0}))
    world.facts.update(
        child=params.child,
        companion=params.companion,
        journey=journey,
        moral=moral,
        answer=journey["answer"],
    )

    world.say(OPENINGS[rng.randrange(len(OPENINGS))].format(child=params.child))
    world.say(
        f"{params.child} had been called a little smartypants because {params.mood} questions "
        f"often helped {params.child} notice what others missed."
    )
    world.say(f"Tonight, {params.child} looked at the kitchen table and gasped. The little jar of pesto was gone.")
    world.say(f'"Did you move it?" asked {params.child}.')
    world.say(f'"Not me," whispered {params.companion}. "Let us look for clues, softly."')
    world.para()

    child.meters["mystery"] = 1.0
    child.memes["curiosity"] = 1.0
    world.say(f"They found {journey['clue']}. Beside it lay the silver spoon, still shining in the moonlight.")
    world.say(f'"A clue is not a guess," said {params.child}. "It tells us where to look next."')
    world.say(f'"And I smell basil," said {params.companion}. "The pesto cannot be far away."')
    world.para()

    world.say(journey["method"])
    world.say(
        f"The pantry door was open just a little. Inside, the pesto jar rested behind a bowl, "
        f"where someone had placed it safely after supper."
    )
    pesto.meters["safe"] = 1.0
    child.memes["relief"] = 1.0
    companion.memes["joy"] = 1.0
    world.para()

    world.say(
        f"{params.child} carried the pesto back to the table, and {params.companion} placed the spoon beside it."
    )
    world.say(
        f'"Mystery solved," said {params.child}. "Careful looking helped us find the answer." '
        f'{params.companion.capitalize()} gave a sleepy nod.'
    )
    world.say(f"They tucked the kitchen into the quiet night. {journey['image']}.")
    world.say(f"And the bedtime lesson was simple: {moral}")
    return world


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


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("clue", "spoon"),
            asp.fact("clue", "moonbeam"),
            asp.fact("clue", "crumb"),
            asp.fact("helper", "smartypants"),
            asp.fact("hiding_place", "pantry"),
        ]
    )


def asp_program(show: str = "#show solvable/0.\n#show answer/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    solvable = bool(asp.atoms(model, "solvable"))
    answer = asp.atoms(model, "answer")
    if solvable and answer == [("pantry",)]:
        print("OK: ASP mystery gate matches the Python mystery.")
        return 0
    print("ASP/Python parity failure.")
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "the sleepy cat", "curious"),
    StoryParams("Mira", "the small owl", "patient"),
    StoryParams("Nora", "the gentle fox", "thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(sorted(asp.atoms(model, "solvable") + asp.atoms(model, "answer")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
