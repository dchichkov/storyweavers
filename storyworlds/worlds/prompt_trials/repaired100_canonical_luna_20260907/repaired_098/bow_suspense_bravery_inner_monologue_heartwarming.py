#!/usr/bin/env python3
"""A heartwarming bow story about suspense, bravery, and a quiet inner voice."""

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


@dataclass
class Bow:
    color: str
    material: str
    owner: str
    location: str
    tied: bool = False
    found: bool = False


@dataclass
class World:
    meadow: Place
    child: Person
    helper: Person
    bow: Bow
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


@dataclass(frozen=True)
class BowCase:
    danger: str
    first_clue: str
    failed_guess: str
    true_cause: str
    safe_action: str
    repair: str
    lesson: str
    ending: str


PLACES = {
    "willow meadow": Place("Willow Meadow", "meadow"),
    "lantern garden": Place("Lantern Garden", "garden"),
    "bluebell hill": Place("Bluebell Hill", "hill"),
}

CHILDREN = [
    ("Luna", "child"),
    ("Mara", "child"),
    ("Theo", "child"),
]

HELPERS = [
    ("Auntie Bea", "rabbit"),
    ("Pip", "small dog"),
    ("Nell", "goat"),
]

BOWS = [
    ("red", "ribbon", "the willow bench"),
    ("gold", "satin", "the garden gate"),
    ("blue", "cloth", "the picnic basket"),
    ("green", "wool", "the old oak"),
]

CASES = {
    "wind": BowCase(
        danger="the ribbon might blow into the creek",
        first_clue="a bright red tail fluttered beyond the safe path",
        failed_guess="the bow was not caught on the fence where it first seemed to be",
        true_cause="a gust had carried the bow into a low willow branch above the creek bank",
        safe_action="stood on the dry path and asked the helper to bring a long shepherd's crook",
        repair="lifted the bow down without stepping near the slippery bank and tied it to a firm basket handle",
        lesson="being brave can mean stopping at the safe edge and asking for the right tool",
        ending="the bow rested safely on the basket while the willow leaves whispered overhead",
    ),
    "thorn": BowCase(
        danger="the ribbon might tear on a thorn",
        first_clue="one loose loop shone beside the rose arbor",
        failed_guess="pulling the ribbon only made the hidden knot tighter",
        true_cause="a small thorn had curled through the bow's center knot",
        safe_action="kept their fingers away from the thorn and held the ribbon still while the helper brought gloves",
        repair="snipped the thorn free with garden clippers and retied the bow with a soft new loop",
        lesson="courage is not rushing toward a problem; it is making a careful plan",
        ending="the fresh bow bobbed on the garden gate, bright as a little sunrise",
    ),
    "duck": BowCase(
        danger="the bow might drift away with a duckling",
        first_clue="a blue ribbon tip waved from the pond reeds",
        failed_guess="calling from the bank did not bring the bow closer",
        true_cause="a breeze had wrapped the bow around a reed beside the quiet pond",
        safe_action="stayed on the bank and asked the helper to guide a floating branch toward the reeds",
        repair="pulled the bow back with the branch and dried it on a warm picnic cloth",
        lesson="a brave heart can stay calm while someone works beside it",
        ending="the ducklings paddled past the dry bow as sunlight shimmered on the pond",
    ),
    "tree": BowCase(
        danger="the green bow might fall from the old oak",
        first_clue="a green flash trembled high above the picnic blanket",
        failed_guess="tugging the low string did not loosen the bow",
        true_cause="the bow was caught on a twig far above the ground",
        safe_action="moved everyone away from the falling leaves and waited for the helper with a padded pole",
        repair="caught the bow gently with the pole and tied it lower on a sturdy branch",
        lesson="bravery can be patient when height makes a quick choice unsafe",
        ending="the green bow hung low enough for every child to see and smile",
    ),
}


ROUTES = (
    "quiet_start",
    "clue_start",
    "dialogue_start",
    "memory_start",
    "rain_start",
)


ASP_RULES = r"""
brave(child) :- child(child), names_worry(child), chooses_safe_action(child).
solved(bow_case) :- bow_case, safe_action_taken.
heartwarming :- solved(bow_case), helper_present, child(child).
valid_story :- brave(child), solved(bow_case), heartwarming.
"""


def safe_atom(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("child", "child"),
        asp.fact("names_worry", "child"),
        asp.fact("chooses_safe_action", "child"),
        asp.fact("bow_case"),
        asp.fact("safe_action_taken"),
        asp.fact("helper_present"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/0."))
    found = bool(asp.atoms(model, "valid_story"))
    if found:
        print("OK: ASP and Python both recognize a solved, brave bow story.")
        return 0
    print("MISMATCH: ASP did not recognize the valid bow story.")
    return 1


def story_rng(params: "StoryParams") -> random.Random:
    raw = "|".join(
        str(value)
        for value in (
            params.seed,
            params.place,
            params.child_name,
            params.helper_name,
            params.case,
            params.route,
            params.bow_color,
        )
    )
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


@dataclass
class StoryParams:
    seed: Optional[int] = None
    place: str = "willow meadow"
    child_name: str = "Luna"
    child_kind: str = "child"
    helper_name: str = "Auntie Bea"
    helper_kind: str = "rabbit"
    bow_color: str = "red"
    case: str = "wind"
    route: str = "quiet_start"


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.case not in CASES:
        raise StoryError(f"Unknown bow case: {params.case}")
    if not params.child_name.strip():
        raise StoryError("The child needs a name.")
    if not params.helper_name.strip():
        raise StoryError("The helper needs a name.")

    place = PLACES[params.place]
    bow_template = next((item for item in BOWS if item[0] == params.bow_color), None)
    if bow_template is None:
        raise StoryError(f"Unknown bow color: {params.bow_color}")

    return World(
        meadow=Place(place.name, place.kind),
        child=Person(params.child_name, params.child_kind, "young bow keeper"),
        helper=Person(params.helper_name, params.helper_kind, "kind helper"),
        bow=Bow(
            color=bow_template[0],
            material=bow_template[1],
            owner=params.child_name,
            location=bow_template[2],
        ),
    )


def tell_story(world: World, params: StoryParams) -> None:
    rng = story_rng(params)
    child = world.child
    helper = world.helper
    bow = world.bow
    place = world.meadow
    case = CASES[params.case]

    child.memes.update(hope=1.0, worry=0.5, bravery=0.0)
    helper.memes.update(kindness=1.0, patience=1.0)

    openings = {
        "quiet_start": (
            f"In {place.name}, {child.name} carried a {bow.color} {bow.material} bow "
            f"for the afternoon picnic. It was tied to {bow.location}, where the breeze "
            f"made its two loops dance."
        ),
        "clue_start": (
            f"A {bow.color} bow belonged to {child.name}, but it vanished near "
            f"{place.name}. Then {child.name} noticed {case.first_clue}."
        ),
        "dialogue_start": (
            f'"Where is my bow?" {child.name} asked softly in {place.name}. '
            f"The question mattered because {case.danger}."
        ),
        "memory_start": (
            f"That morning, {child.name} had tied the {bow.color} bow with extra care. "
            f"By picnic time at {place.name}, only a loose ribbon trail remained, and {case.danger}."
        ),
        "rain_start": (
            f"Clouds gathered over {place.name} while {child.name} searched for a "
            f"{bow.color} bow. The suspense grew because {case.danger}."
        ),
    }
    world.say(openings[params.route])
    world.say(
        rng.choice(
            [
                f"{child.name}'s chest felt tight, but they told themselves, "
                '"I can feel afraid and still take one careful step."',
                f'Inside, {child.name} thought, "A bow is small, but it matters to me. '
                'I will not let worry hurry me."',
                f"{child.name} wanted to run after the fluttering color, yet their inner voice "
                'whispered, "Stop first. Look. Choose safely."',
            ]
        )
    )
    world.say(
        f'"I will help you look," {helper.name} said. "{case.danger.capitalize()}, '
        'so we will stay together."'
    )

    world.para()
    world.say(f"First, {child.name} checked the nearest place, but {case.failed_guess}.")
    world.say(
        rng.choice(
            [
                f'"My first guess was wrong," {child.name} admitted. {helper.name} nodded.',
                f"The suspense deepened, but {child.name} did not pretend to know more than they did.",
                f"{child.name} took a slow breath and listened instead of pulling harder.",
            ]
        )
    )
    world.say(f"Then they saw the fuller clue: {case.true_cause}.")
    world.say(
        f'"There it is," {helper.name} said. "What should we do?" '
        f'{child.name} answered, "We will {case.safe_action}."'
    )

    world.para()
    world.say(
        f"{child.name} {case.safe_action}. Their hands still trembled, but the trembling "
        "did not decide what happened next."
    )
    child.memes["bravery"] = 1.0
    child.meters["safe_choices"] = 1.0
    world.say(f"Together, they {case.repair}.")
    bow.found = True
    bow.tied = True
    bow.location = "a safe place near the picnic"
    world.meadow.meters["safety"] = 1.0
    helper.memes["pride"] = 1.0

    world.para()
    world.say(
        rng.choice(
            [
                f"{child.name} smiled. Their inner voice now sounded warm: "
                f'"{case.lesson.capitalize()}."',
                f'"I thought bravery would feel loud," {child.name} said. '
                f'"But it felt like listening." {helper.name} gave a gentle smile.',
                f"{helper.name} said, \"You did not have to be fearless.\" "
                f'{child.name} replied, "I only had to choose the safe next step."',
            ]
        )
    )
    world.say(f"At last, {case.ending}.")
    world.facts.update(
        case=case,
        cause=case.true_cause,
        safe_action=case.safe_action,
        repair=case.repair,
        lesson=case.lesson,
        ending=case.ending,
        solved=True,
    )


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    return [
        f"Write a heartwarming suspense story about {world.child.name} finding a {world.bow.color} bow in {world.meadow.name}.",
        f"Show {world.child.name} using an inner monologue to turn worry into bravery while {world.helper.name} helps.",
        f"End with this changed image: {case.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case = world.facts["case"]
    return [
        QAItem(
            question=f"Why was {world.child.name} worried about the bow?",
            answer=f"{world.child.name} worried because {case.danger}.",
        ),
        QAItem(
            question="What did the first guess fail to explain?",
            answer=f"The first guess failed because {case.failed_guess}.",
        ),
        QAItem(
            question=f"What was really happening to the bow?",
            answer=f"The real cause was that {case.true_cause}.",
        ),
        QAItem(
            question=f"How did {world.child.name} show bravery?",
            answer=f"{world.child.name} showed bravery when they {case.safe_action}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The bow was safe after they {case.repair}. In the final image, {case.ending}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bow?",
            answer="A bow is a looped decoration made by tying ribbon, cloth, or another flexible material.",
        ),
        QAItem(
            question="What does bravery mean in this story?",
            answer="Bravery means noticing fear, slowing down, and choosing a safe helpful action.",
        ),
        QAItem(
            question="Why can inner thoughts help someone?",
            answer="Inner thoughts can help someone name a worry and remember to make a careful choice.",
        ),
        QAItem(
            question="Why is asking for help useful?",
            answer="A helper may bring experience, tools, or calm attention when a problem is difficult to handle alone.",
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


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world trace ---",
            f"place: {world.meadow.name} meters={world.meadow.meters}",
            f"child: {world.child.name} meters={world.child.meters} memes={world.child.memes}",
            f"helper: {world.helper.name} meters={world.helper.meters} memes={world.helper.memes}",
            f"bow: color={world.bow.color!r} material={world.bow.material!r} "
            f"location={world.bow.location!r} tied={world.bow.tied} found={world.bow.found}",
            f"facts: solved={world.facts.get('solved')} cause={world.facts.get('cause')!r}",
        ]
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
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming bow story with suspense and bravery."
    )
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--child-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--case", choices=sorted(CASES))
    parser.add_argument("--bow-color", choices=sorted(item[0] for item in BOWS))
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child_name, _ = rng.choice(CHILDREN)
    helper_name, helper_kind = rng.choice(HELPERS)
    bow_color = args.bow_color or rng.choice([item[0] for item in BOWS])
    return StoryParams(
        seed=args.seed,
        place=args.place or rng.choice(sorted(PLACES)),
        child_name=args.child_name or child_name,
        child_kind="child",
        helper_name=args.helper_name or helper_name,
        helper_kind=helper_kind,
        bow_color=bow_color,
        case=args.case or rng.choice(sorted(CASES)),
        route=rng.choice(ROUTES),
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/0."))
        print(bool(asp.atoms(model, "valid_story")))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 3 if args.all else args.n
    samples: list[StorySample] = []

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
