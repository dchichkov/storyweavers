#!/usr/bin/env python3
"""A child-facing whodunit about anxiety, a witch, a sketch, and a happy ending."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Person:
    name: str
    kind: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Case:
    clue: str
    worry: str
    first_test: str
    failed_reason: str
    decisive_clue: str
    cause: str
    safe_action: str
    repair: str
    lesson: str
    ending: str


@dataclass
class Mystery:
    title: str
    clue: str
    solved: bool = False


@dataclass
class World:
    cottage: Place
    witch: Person
    helper: Person
    mystery: Mystery
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    cottage_name: str = "the Moonbeam Cottage"
    witch_name: str = "Luna"
    witch_kind: str = "young witch"
    helper_name: str = "Pip"
    helper_kind: str = "talking fox"
    case: str = "missing_sketch"
    route: str = "clue_first"


PLACES = {
    "Moonbeam Cottage": Place("the Moonbeam Cottage", "cottage"),
    "Bluebell Cottage": Place("the Bluebell Cottage", "cottage"),
    "Mossy Tower": Place("the Mossy Tower", "tower"),
}

WITCHES = [
    ("Luna", "young witch"),
    ("Mira", "apprentice witch"),
    ("Tess", "garden witch"),
]

HELPERS = [
    ("Pip", "talking fox"),
    ("Nori", "little owl"),
    ("Bram", "kind badger"),
]

CASES = {
    "missing_sketch": Case(
        clue="the moon-moth sketch had vanished",
        worry="the witch might miss the pattern needed to guide the moths home",
        first_test="looked beneath the drawing table and inside the empty paint box",
        failed_reason="the sketch was not in either place, and the clean table showed no torn scraps",
        decisive_clue="a silver-blue smudge curved from the window toward the laundry basket",
        cause="a breeze had lifted the damp sketch onto a clothespin, where it folded into the basket",
        safe_action="asked Pip to hold the basket still while she followed the smudge from the floor",
        repair="pressed the sketch flat, dried it between clean books, and clipped it to a corkboard",
        lesson="an anxious guess becomes smaller when kind friends and careful clues work together",
        ending="the moon-moths followed Luna's restored sketch home, glowing like tiny stars above the garden",
    ),
    "vanished_broom": Case(
        clue="the red broom had disappeared",
        worry="the cottage floor might stay too dusty for the evening spell",
        first_test="searched the broom closet and counted every bundle of straw",
        failed_reason="all the bundles were there, but the red handle was missing",
        decisive_clue="three red bristles poked from behind the curtain beside a trail of flour",
        cause="a flour sack had tipped over and rolled the broom behind the curtain",
        safe_action="waited for Pip to sweep the flour away from the doorway before reaching behind it",
        repair="stood the broom in a marked corner and tied the flour sack closed",
        lesson="a calm search is safer and more useful than a frightened dash",
        ending="the clean floor shone beneath the happy broom, and everyone danced without slipping",
    ),
    "silent_bell": Case(
        clue="the welcome bell no longer rang",
        worry="lost travelers might pass the cottage without finding shelter",
        first_test="pulled the bell cord once and checked the hook above the door",
        failed_reason="the cord was attached, but the bell stayed quiet",
        decisive_clue="a soft yellow feather was caught between the bell and its clapper",
        cause="a sleepy robin had tucked the feather there while building a nest nearby",
        safe_action="spoke softly and asked Pip to move the nest only after finding a safe branch",
        repair="freed the clapper, hung the nest in the branch, and tested the bell gently",
        lesson="solving a problem can protect both a home and the small creature nearby",
        ending="the bell gave a warm clear ring, and the robin chirped from its new safe nest",
    ),
}

ROUTES = ("clue_first", "dialogue_first", "anxiety_first", "sketch_first")

ASP_RULES = r"""
calm(W) :- witch(W), names_worry(W), chooses_safe_action(W).
solved(C) :- mystery(C), has_cause(C).
valid_story(C) :- witch(witch), calm(witch), solved(C).
"""


def case_id(name: str) -> str:
    return "case_" + "".join(ch if ch.isalnum() else "_" for ch in name).strip("_")


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("witch", "witch"),
        asp.fact("names_worry", "witch"),
        asp.fact("chooses_safe_action", "witch"),
    ]
    for name, case in CASES.items():
        cid = case_id(name)
        lines.append(asp.fact("mystery", cid))
        lines.append(asp.fact("has_cause", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/1."))
    actual = set(asp.atoms(model, "solved"))
    expected = {(case_id(name),) for name in CASES}
    if actual == expected:
        print(f"OK: clingo gate matches Python reasoning ({len(expected)} cases).")
        return 0
    print("MISMATCH between clingo and Python reasoning.")
    print("clingo:", sorted(actual))
    print("python:", sorted(expected))
    return 1


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(str(value) for value in (
        params.seed, params.cottage_name, params.witch_name, params.witch_kind,
        params.helper_name, params.helper_kind, params.case, params.route,
    ))
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def build_world(params: StoryParams) -> World:
    if params.cottage_name not in {p.name.removeprefix("the ") for p in PLACES.values()}:
        raise StoryError(f"Unknown cottage: {params.cottage_name}")
    if params.case not in CASES:
        raise StoryError(f"Unknown mystery case: {params.case}")
    place = PLACES[params.cottage_name]
    return World(
        cottage=Place(place.name, place.kind),
        witch=Person(params.witch_name, params.witch_kind, "witch"),
        helper=Person(params.helper_name, params.helper_kind, "helper"),
        mystery=Mystery(params.case, CASES[params.case].clue),
    )


def tell_story(world: World, params: StoryParams) -> None:
    rng = story_rng(params)
    witch, helper, cottage = world.witch, world.helper, world.cottage
    case = CASES[params.case]
    witch.memes.update(anxiety=1.0, courage=0.0)
    helper.memes.update(kindness=1.0, patience=1.0)

    openings = {
        "clue_first": f"At {cottage.name}, {witch.name}, a {witch.kind}, found that {case.clue}.",
        "dialogue_first": f'"Something is wrong," {witch.name} whispered at {cottage.name}. {case.clue.capitalize()} had disappeared.',
        "anxiety_first": f"Anxiety fluttered in {witch.name}'s chest before breakfast at {cottage.name}. Then she noticed that {case.clue}.",
        "sketch_first": f"{witch.name} had drawn a careful sketch at {cottage.name}, but now {case.clue}.",
    }
    world.say(openings[params.route])
    world.say(f"The clue mattered because {case.worry}.")
    world.say(f'"We can feel worried and still investigate safely," {helper.name} said. "{witch.name}, tell me what you know first."')
    world.say(f'"I know the last place I saw it," {witch.name} replied. "I will not rush."')

    world.para()
    world.say(f"First, {witch.name} {case.first_test}.")
    world.say(f"The first idea failed: {case.failed_reason}.")
    world.say(f'"The missing thing may have traveled," {helper.name} said. "Let us follow evidence, not fear."')
    world.say(f"Then {witch.name} noticed that {case.decisive_clue}.")
    world.say(f"At last, the mystery made sense: {case.cause}.")

    world.para()
    world.say(f"{witch.name} took a slow breath and {case.safe_action}.")
    witch.memes["anxiety"] = 0.3
    witch.memes["courage"] = 1.0
    witch.meters["safe_steps"] = 2.0
    world.say(f"Together, they {case.repair}.")
    world.mystery.solved = True
    cottage.meters["safety"] = 1.0

    world.para()
    world.say(f'"What helped most?" {helper.name} asked.')
    world.say(f'{witch.name} smiled. "I remembered that {case.lesson}."')
    world.say(f"With the worry solved, {case.ending}.")
    world.facts.update(
        case=case,
        cause=case.cause,
        repair=case.repair,
        lesson=case.lesson,
        ending=case.ending,
        solved=True,
    )


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    return [
        f"Write a child-friendly whodunit about {world.witch.name}, a witch with anxiety, and {world.mystery.clue}.",
        f"Show how a sketch clue reveals that {case.cause}.",
        f"End with this happy image: {case.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case = world.facts["case"]
    return [
        QAItem(
            f"What mystery did {world.witch.name} investigate?",
            f"{world.witch.name} investigated why {case.clue}. It mattered because {case.worry}.",
        ),
        QAItem(
            "Why did the first search fail?",
            f"The first search failed because {case.failed_reason}.",
        ),
        QAItem(
            "What clue solved the whodunit?",
            f"The decisive clue was that {case.decisive_clue}. It showed that {case.cause}.",
        ),
        QAItem(
            f"How did {world.witch.name} handle anxiety?",
            f"{world.witch.name} took a slow breath and {case.safe_action}. She chose a safe step instead of rushing.",
        ),
        QAItem(
            "How did the story end happily?",
            f"After they {case.repair}, {case.ending}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a witch in this story world?",
            "A witch is a person who studies gentle magic and uses care, practice, and good judgment.",
        ),
        QAItem(
            "What is anxiety?",
            "Anxiety is a worried feeling that can make a problem seem larger, but slow breathing and safe help can make it easier to handle.",
        ),
        QAItem(
            "Why can a sketch help solve a mystery?",
            "A sketch can preserve details about a shape, place, or pattern so careful observers can compare it with new clues.",
        ),
        QAItem(
            "What makes a whodunit satisfying?",
            "A whodunit presents a puzzling problem, follows clues, and reveals a believable cause that explains what happened.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle whodunit about anxiety, a witch, and a sketch."
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--cottage", choices=sorted(PLACES))
    parser.add_argument("--witch-name")
    parser.add_argument("--helper-name")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.cottage or rng.choice(sorted(PLACES))
    witch_name, witch_kind = rng.choice(WITCHES)
    helper_name, helper_kind = rng.choice(HELPERS)
    return StoryParams(
        seed=args.seed,
        cottage_name=place,
        witch_name=args.witch_name or witch_name,
        witch_kind=witch_kind,
        helper_name=args.helper_name or helper_name,
        helper_kind=helper_kind,
        case=rng.choice(sorted(CASES)),
        route=rng.choice(ROUTES),
    )


def dump_trace(world: World) -> str:
    return "\n".join([
        "--- world trace ---",
        f"{world.cottage.name}: meters={world.cottage.meters}",
        f"{world.witch.name}: meters={world.witch.meters} memes={world.witch.memes}",
        f"{world.helper.name}: meters={world.helper.meters} memes={world.helper.memes}",
        f"mystery={world.mystery.title!r} clue={world.mystery.clue!r} solved={world.mystery.solved}",
        f"cause={world.facts['cause']!r}",
    ])


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/1."))
        print(sorted(set(asp.atoms(model, "solved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 3 if args.all else args.n
    samples = []
    for index in range(count):
        params = resolve_params(args, random.Random(base_seed + index))
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
