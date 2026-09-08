#!/usr/bin/env python3
"""A curious nursery-rhyme story about grammatic words and a curry pot."""

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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Nursery:
    place: str = "the moonlit nursery"
    shelf: str = "the rhyme shelf"
    pot: str = "the little curry pot"


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child: str = "Luna"
    helper: str = "Pip"
    cat: str = "Marmalade"
    place: str = "nursery"
    rhyme: int = 0
    curiosity: int = 0
    ending: int = 0
    cadence: int = 0


CHILDREN = ["Luna", "Nora", "Milo", "Tess", "Rafi", "Poppy"]
HELPERS = ["Pip", "Bun", "Wren", "Dot", "Kit"]
CATS = ["Marmalade", "Pepper", "Clover", "Saffron"]

RHYMES = [
    {
        "title": "the grammar spoon",
        "clue": "Luna noticed that the word 'curry' needed a little spoon between two lines of the rhyme.",
        "action": "She moved the spoon beside the pot and read the couplet aloud: 'Stir the curry, do not hurry.'",
        "result": "The sleepy pot stopped wobbling, and its warm scent curled through the room.",
        "lesson": "Curiosity can mend a mixed-up rhyme.",
        "object": "the grammar spoon",
    },
    {
        "title": "the backwards recipe",
        "clue": "Luna saw that the grammatic recipe began with the last step instead of the first.",
        "action": "She put the words in order: 'Wash, chop, stir curry, then sit by the fire.'",
        "result": "The recipe made sense, and the kitchen bell gave one bright ding.",
        "lesson": "Small words can guide a big task.",
        "object": "the recipe card",
    },
    {
        "title": "the missing rhyme",
        "clue": "Luna heard that 'curry' did not rhyme with 'hurry' because one word had fallen beneath the bed.",
        "action": "She found the missing word, 'hurry,' and tucked it back beside 'curry.'",
        "result": "The verse bounced neatly from line to line, and everyone could chant it.",
        "lesson": "Asking why helps us find what is missing.",
        "object": "the missing word",
    },
    {
        "title": "the quiet question",
        "clue": "Luna wondered why the curry pot was cold when the rhyme promised a warm supper.",
        "action": "She followed a trail of crumbs and found the firewood hidden behind a toy drum.",
        "result": "Pip built a tiny safe fire with an adult, and the pot began to bubble.",
        "lesson": "A careful question can uncover a simple cause.",
        "object": "the firewood",
    },
    {
        "title": "the hopping commas",
        "clue": "Luna saw three commas hopping from line to line and changing where the rhyme paused.",
        "action": "She placed each comma after the right word and read slowly: 'Stir, curry, stir!'",
        "result": "The rhythm settled, and the baby dolls rocked without a bump.",
        "lesson": "Punctuation helps words keep their rhythm.",
        "object": "the three commas",
    },
]

BAD_ENDINGS = [
    "But the pot tipped, the curry splashed, and the rhyme ended with a soggy frown.",
    "Then the candle went out, the last word vanished, and the nursery grew quiet and gray.",
    "At first the rhyme broke apart, and the curry cooled before anyone knew what to do.",
    "The shelf shook hard, the cards fell down, and the cheerful verse lost its crown.",
]

OPENINGS = [
    "In {place}, where moonbeams slept in a row, {child} found a rhyme card below.",
    "At bedtime, {child} heard a tiny tap from the nursery shelf and followed its map.",
    "By the window at {place}, {child} found a golden spoon beside a curry pot.",
    "The dolls were tucked in, the blankets were tight, but {child} still wondered what stirred in the night.",
]

DIALOGUES = [
    "'Why does this word wobble?' asked {child}. 'Let us read it slowly,' said {helper}.",
    "'Is the curry meant to rhyme?' asked {child}. '{child}, let us look for the missing clue,' said {helper}.",
    "'Something is not grammatic here,' said {child}. 'Then your curious eyes may help,' replied {helper}.",
    "'Should we hurry?' asked {child}. 'No, careful readers do not hurry,' said {helper}.",
]

CADENCES = [
    "Tick-tock, read and check; a patient thought can mend a wreck.",
    "Look high, look low, then let the small clue show.",
    "Word by word and line by line, the little rhyme began to shine.",
    "A question first, a careful glance, then every word found its dance.",
]

GOOD_ENDINGS = [
    "The curry steamed, the rhyme rang clear, and every sleepy ear could hear.",
    "The cards lay straight, the spoon shone bright, and curiosity tucked the room good-night.",
    "The final couplet glowed by the bed: 'Curry with care, and questions with flair.'",
    "The pot sang softly, the dolls all smiled, and the repaired rhyme watched over the child.",
]


ASP_RULES = r"""
#show curious/1.
#show ingredient/1.
#show solved/1.

curious(C) :- asks(C).
ingredient(curry).
solved(P) :- curious(P), ingredient(curry), checks(P).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("asks", "child"),
            asp.fact("checks", "child"),
            asp.fact("ingredient", "curry"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nursery-rhyme storyworld about grammatic words, curry, and curiosity."
    )
    parser.add_argument("--child", choices=CHILDREN)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--cat", choices=CATS)
    parser.add_argument("--place", default="nursery")
    parser.add_argument("--rhyme", type=int, choices=range(len(RHYMES)))
    parser.add_argument("--curiosity", type=int, choices=range(len(DIALOGUES)))
    parser.add_argument("--ending", type=int, choices=range(len(BAD_ENDINGS)))
    parser.add_argument("--cadence", type=int, choices=range(len(CADENCES)))
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
        seed=args.seed,
        child=args.child or rng.choice(CHILDREN),
        helper=args.helper or rng.choice(HELPERS),
        cat=args.cat or rng.choice(CATS),
        place=args.place or "nursery",
        rhyme=args.rhyme if args.rhyme is not None else rng.randrange(len(RHYMES)),
        curiosity=(
            args.curiosity
            if args.curiosity is not None
            else rng.randrange(len(DIALOGUES))
        ),
        ending=args.ending if args.ending is not None else rng.randrange(len(BAD_ENDINGS)),
        cadence=args.cadence if args.cadence is not None else rng.randrange(len(CADENCES)),
    )


def generate(params: StoryParams) -> StorySample:
    if not params.child or not params.helper or not params.cat:
        raise StoryError("The child, helper, and cat must all have names.")
    if not 0 <= params.rhyme < len(RHYMES):
        raise StoryError("Rhyme choice is outside the available nursery rhymes.")

    world = World()
    nursery = Nursery(place=f"the {params.place}")
    child = world.add(
        Entity(
            id=params.child,
            type="child",
            label=params.child,
            meters={"reach": 0.8},
            memes={"curiosity": 1.0},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper,
            type="helper",
            label=params.helper,
            meters={"reach": 0.6},
            memes={"patience": 1.0},
        )
    )
    cat = world.add(
        Entity(
            id=params.cat,
            type="cat",
            label=params.cat,
            meters={"softness": 1.0},
            memes={"watchfulness": 1.0},
        )
    )
    pot = world.add(
        Entity(
            id="curry_pot",
            type="object",
            label="curry pot",
            owner=params.child,
            meters={"warmth": 0.2, "stability": 0.4},
            memes={"importance": 1.0},
        )
    )
    world.facts["nursery"] = nursery
    rhyme = RHYMES[params.rhyme]
    common = {
        "place": nursery.place,
        "child": child.label,
        "helper": helper.label,
    }

    world.say(OPENINGS[params.rhyme % len(OPENINGS)].format(**common))
    world.say(
        f"The card said, 'Be grammatic, and do not let the curry turn dramatic,' "
        f"but its words were scrambled and its ending was bad."
    )
    world.say(BAD_ENDINGS[params.ending % len(BAD_ENDINGS)])
    world.say(DIALOGUES[params.curiosity % len(DIALOGUES)].format(**common))
    world.say(f"{cat.label} blinked at the pot and gave a tiny, worried mew.")
    world.say(f"In the middle of the card was {rhyme['title']}, waiting for a curious reader.")
    world.say(rhyme["clue"])
    world.say(CADENCES[params.cadence % len(CADENCES)])
    world.say(rhyme["action"])
    world.say(f"{helper.label} held the card while {child.label} checked each word and each pause.")
    world.say(rhyme["result"])

    child.memes["curiosity"] = 2.0
    helper.memes["trust"] = 1.0
    pot.meters["warmth"] = 1.0
    pot.meters["stability"] = 1.0
    world.facts.update(
        child=child,
        helper=helper,
        cat=cat,
        pot=pot,
        nursery=nursery,
        rhyme=rhyme,
        bad_ending=BAD_ENDINGS[params.ending % len(BAD_ENDINGS)],
        grammatic=True,
        curry=True,
        curiosity=True,
        solved=True,
    )
    world.say(f"Lesson learned: {rhyme['lesson']}")
    world.say(GOOD_ENDINGS[params.rhyme % len(GOOD_ENDINGS)])

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    rhyme = f["rhyme"]
    child = f["child"]
    return [
        f"Write a nursery rhyme about {child.label}'s curiosity during {rhyme['title']}.",
        "Include the words grammatic and curry, a bad ending that creates a problem, and a repaired rhyme.",
        "Use a child-friendly spoken exchange and end with a clear image showing the problem is solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    rhyme = f["rhyme"]
    return [
        QAItem(
            question=f"What made {child.label} curious?",
            answer=(
                f"{child.label} became curious because the grammatic rhyme was scrambled, "
                f"the curry pot was in trouble, and the card had a bad ending."
            ),
        ),
        QAItem(
            question="What was the clue in the rhyme?",
            answer=rhyme["clue"],
        ),
        QAItem(
            question=f"How did {child.label} and {helper.label} repair the rhyme?",
            answer=rhyme["action"],
        ),
        QAItem(
            question="What changed at the end?",
            answer=(
                f"The words and pauses were checked, the curry became warm and steady, "
                f"and the repaired rhyme ended happily."
            ),
        ),
        QAItem(
            question="What lesson did the story teach?",
            answer=f"The lesson was that {rhyme['lesson'].lower()}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does grammatic mean?",
            answer=(
                "Grammatic means related to grammar, the rules that help words and sentences "
                "fit together clearly."
            ),
        ),
        QAItem(
            question="What is curry?",
            answer=(
                "Curry is a dish or sauce made with seasonings and other ingredients. "
                "Different cultures make many kinds of curry."
            ),
        ),
        QAItem(
            question="Why is curiosity useful?",
            answer=(
                "Curiosity encourages us to ask careful questions, look for clues, and learn "
                "how something works."
            ),
        ),
        QAItem(
            question="What is a rhyme?",
            answer=(
                "A rhyme is a pattern in which words have matching or similar ending sounds."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for number, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{number}. {prompt}")
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
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:12} ({entity.type:8}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_valid() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program("#show curious/1.\n#show solved/1."))
    return set(asp.atoms(model, "solved"))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show curious/1.\n#show ingredient/1.\n#show solved/1."))
    curious = set(asp.atoms(model, "curious"))
    ingredients = set(asp.atoms(model, "ingredient"))
    solved = set(asp.atoms(model, "solved"))
    expected_curious = {("child",)}
    expected_ingredients = {("curry",)}
    expected_solved = {("child",)}
    if (
        curious == expected_curious
        and ingredients == expected_ingredients
        and solved == expected_solved
    ):
        sample = generate(
            StoryParams(
                seed=7,
                child="Luna",
                helper="Pip",
                cat="Marmalade",
                rhyme=0,
                curiosity=0,
                ending=0,
                cadence=0,
            )
        )
        required = ["grammatic", "curry", "curious", "rhyme"]
        if all(word in sample.story.lower() for word in required):
            print("OK: ASP parity and generated story checks passed.")
            return 0
    print("MISMATCH in ASP parity or generated story checks.")
    print("  curious:", sorted(curious))
    print("  ingredients:", sorted(ingredients))
    print("  solved:", sorted(solved))
    return 1


CURATED = [
    StoryParams(
        seed=1,
        child="Luna",
        helper="Pip",
        cat="Marmalade",
        place="nursery",
        rhyme=0,
        curiosity=0,
        ending=0,
        cadence=0,
    ),
    StoryParams(
        seed=2,
        child="Nora",
        helper="Wren",
        cat="Pepper",
        place="nursery",
        rhyme=2,
        curiosity=2,
        ending=1,
        cadence=3,
    ),
    StoryParams(
        seed=3,
        child="Milo",
        helper="Dot",
        cat="Saffron",
        place="playroom",
        rhyme=4,
        curiosity=3,
        ending=3,
        cadence=2,
    ),
]


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
        print(asp_program("#show curious/1.\n#show ingredient/1.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} ASP-suggested solved facts")
        for item in sorted(asp_valid()):
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        limit = max(50, args.n * 30)
        while len(samples) < args.n and attempt < limit:
            params = resolve_params(args, random.Random(base_seed + attempt))
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            attempt += 1

    if not samples:
        raise StoryError("No stories could be generated.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.all:
            header = f"### {sample.params.child}: curious curry rhyme"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
