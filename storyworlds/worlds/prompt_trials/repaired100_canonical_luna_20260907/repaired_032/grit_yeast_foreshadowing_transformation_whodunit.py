#!/usr/bin/env python3
"""
A child-facing whodunit about grit, yeast, and a surprising transformation.

Luna wants to bake a moon-shaped loaf for the village supper, but the dough
refuses to rise. A trail of flour, a warm fingerprint on the mixing bowl, and
a tiny yeast packet point toward a mystery. The answer is not a thief: the
yeast is quietly transforming the dough, and Luna's grit helps her wait, knead,
and solve the case.
"""

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

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    label: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    culprit: str
    clue: str
    transformation: str
    image: str


@dataclass
class StoryParams:
    place: str
    case: str
    name: str
    helper: str
    seed: Optional[int] = None
    telling: str = "lantern"


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity


PLACES = {
    "bakery": Place("bakery", "the little bakery", {"bread"}),
    "school_kitchen": Place("school_kitchen", "the school kitchen", {"bread"}),
    "harbor_cafe": Place("harbor_cafe", "the harbor café", {"bread"}),
}

CASES = {
    "moon_loaf": Case(
        "moon_loaf",
        "the yeast",
        "three warm fingerprints circled the bowl, and a tiny trail of flour led back to the covered jar",
        "the flat dough became a springy moon-shaped loaf",
        "the loaf rose so high that its golden crust seemed to grin at the moon",
    ),
    "star_rolls": Case(
        "star_rolls",
        "the yeast",
        "a star of flour appeared beneath the cloth beside one missing yeast packet",
        "the small lumps became six soft star rolls",
        "the rolls shone like little suns in a basket",
    ),
    "giant_bun": Case(
        "giant_bun",
        "the yeast",
        "the bowl had crept toward the warm stove, leaving a floury crescent behind it",
        "the tight dough became one enormous, airy bun",
        "the bun was so round that a sparrow tried to orbit it",
    ),
}

NAMES = ["Luna", "Mara", "Nell", "Pip", "Theo", "Iris"]
HELPERS = ["Pip", "Theo", "Iris", "Mara", "Nell", "Jo"]

TELLINGS = {
    "lantern": {
        "opening": "At dusk, {hero} found a covered bowl on the bakery table.",
        "invite": "\"This is a baking mystery,\" said {hero}. \"Will you help me solve it?\"",
        "reply": "\"I will inspect the clues,\" said {helper}. \"But you must not give up.\"",
    },
    "rainy": {
        "opening": "Rain tapped the windows when {hero} discovered a silent bowl beneath a striped cloth.",
        "invite": "{hero} called {helper}, who hurried in with a lantern and a notebook.",
        "reply": "\"A good detective watches and waits,\" {helper} said. \"Let us do both.\"",
    },
    "market": {
        "opening": "Before the market opened, {hero} noticed a bowl that had changed places on the counter.",
        "invite": "\"Something happened here,\" {hero} whispered, and {helper} leaned close.",
        "reply": "\"Then we will follow every crumb,\" {helper} promised.",
    },
}


def valid_combos() -> list[tuple[str, str]]:
    return [
        (place_id, case_id)
        for place_id, place in PLACES.items()
        for case_id in CASES
        if "bread" in place.affords
    ]


ASP_RULES = r"""
place(P) :- place_name(P).
case(C) :- case_name(C).
valid_story(P,C) :- place(P), case(C), affords(P,bread), has_ingredient(C,yeast),
                     has_trait(C,grit), transforms(C,dough,bread).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place_name", pid))
        for affordance in sorted(place.affords):
            lines.append(asp.fact("affords", pid, affordance))
    for cid in CASES:
        lines.extend(
            [
                asp.fact("case_name", cid),
                asp.fact("has_ingredient", cid, "yeast"),
                asp.fact("has_trait", cid, "grit"),
                asp.fact("transforms", cid, "dough", "bread"),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_pairs = set(valid_combos())
    asp_pairs = set(asp_valid_stories())
    if python_pairs == asp_pairs:
        print(f"OK: ASP matches Python ({len(python_pairs)} valid stories).")
        return 0
    print("Mismatch between ASP and Python.")
    print("Only in ASP:", sorted(asp_pairs - python_pairs))
    print("Only in Python:", sorted(python_pairs - asp_pairs))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A whodunit storyworld about grit, yeast, foreshadowing, and transformation."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--case", choices=sorted(CASES))
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--telling", choices=sorted(TELLINGS))
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
    choices = [
        pair
        for pair in valid_combos()
        if (args.place is None or pair[0] == args.place)
        and (args.case is None or pair[1] == args.case)
    ]
    if not choices:
        raise StoryError("No valid place and case combination matches those choices.")
    place, case = rng.choice(sorted(choices))
    name = args.name or rng.choice(NAMES)
    helper_choices = [person for person in HELPERS if person != name]
    helper = args.helper or rng.choice(helper_choices)
    if helper == name:
        raise StoryError("The helper must have a different name from the detective.")
    return StoryParams(
        place=place,
        case=case,
        name=name,
        helper=helper,
        telling=args.telling or rng.choice(sorted(TELLINGS)),
    )


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    case = CASES[params.case]
    telling = TELLINGS[params.telling]
    world = World(place)

    hero = world.add(
        Entity(
            params.name,
            "character",
            params.name,
            memes={"grit": 0.0, "curiosity": 1.0},
        )
    )
    helper = world.add(
        Entity(
            params.helper,
            "character",
            params.helper,
            memes={"careful": 1.0, "helping": 0.0},
        )
    )
    dough = world.add(
        Entity(
            "dough",
            "food",
            "dough",
            meters={"rise": 0.0, "warmth": 0.0},
            memes={"patience_needed": 1.0},
        )
    )
    yeast = world.add(
        Entity(
            "yeast",
            "ingredient",
            "yeast",
            meters={"active": 0.0},
            memes={"hidden": 1.0},
        )
    )
    bowl = world.add(Entity("bowl", "tool", "mixing bowl"))
    world.add(Entity("flour_trail", "clue", "flour trail"))
    world.add(Entity("warm_fingerprint", "clue", "warm fingerprint"))

    world.facts.update(
        hero=hero,
        helper=helper,
        dough=dough,
        yeast=yeast,
        bowl=bowl,
        case=case,
        opening=telling["opening"].format(hero=params.name),
        invitation=telling["invite"].format(hero=params.name, helper=params.helper),
        reply=telling["reply"].format(hero=params.name, helper=params.helper),
        clue=case.clue,
        transformation=case.transformation,
        image=case.image,
        culprit=case.culprit,
        solved=False,
    )

    return world


def solve_case(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    dough: Entity = world.facts["dough"]  # type: ignore[assignment]
    yeast: Entity = world.facts["yeast"]  # type: ignore[assignment]

    hero.memes["grit"] = 1.0
    helper.memes["helping"] = 1.0
    yeast.meters["active"] = 1.0
    dough.meters["warmth"] = 1.0
    dough.meters["rise"] = 1.0
    dough.memes["patience_needed"] = 0.0
    world.fired.update({"clues_examined", "yeast_identified", "transformation_complete"})
    world.facts["solved"] = True


def render_story(world: World) -> str:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    case: Case = world.facts["case"]  # type: ignore[assignment]
    dough: Entity = world.facts["dough"]  # type: ignore[assignment]
    yeast: Entity = world.facts["yeast"]  # type: ignore[assignment]

    paragraphs = [
        (
            f"{world.facts['opening']} {hero.label} lifted the cloth and found dough "
            f"sleeping in the bowl. It was supposed to become {case.transformation.split(' became ')[-1]}, "
            "but it looked flat and cold."
        ),
        (
            f"{hero.label} noticed that {world.facts['clue']}. "
            f"\"The baker's prize is missing,\" {hero.label} said. "
            f"\"Or perhaps the dough is hiding the answer,\" replied {helper.label}. "
            f"{helper.label} pointed to the flour trail, while {hero.label} studied the warm fingerprint."
        ),
        (
            f"{world.facts['invitation']} {world.facts['reply']} "
            f"{hero.label} kneaded the dough slowly instead of tossing it away. "
            f"{helper.label} warmed the bowl and placed the tiny yeast packet beside it. "
            "They waited, listened, and checked the clues again."
        ),
        (
            f"Then the mystery cracked open. The yeast was not a thief at all. "
            f"It was the quiet worker changing the dough from within. "
            f"{hero.label}'s grit gave the yeast time to work, and the dough transformed: "
            f"{world.facts['transformation']}."
        ),
        (
            f"\"So the yeast did it!\" cried {hero.label}. "
            f"\"Yes,\" said {helper.label}, \"but your grit solved the case.\" "
            f"The baker returned with a smile, and everyone shared the bread. "
            f"At the end, {world.facts['image']}."
        ),
    ]
    return "\n\n".join(paragraphs)


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    case: Case = world.facts["case"]  # type: ignore[assignment]
    return [
        "Write a short child-facing whodunit about grit and yeast.",
        f"Make {hero.label} follow this foreshadowing clue: {case.clue}.",
        f"Show the transformation clearly: {case.transformation}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    case: Case = world.facts["case"]  # type: ignore[assignment]
    return [
        QAItem(
            f"What mystery did {hero.label} investigate?",
            f"{hero.label} investigated why the dough stayed flat instead of becoming {case.transformation.split(' became ')[-1]}.",
        ),
        QAItem(
            "What clues foreshadowed the answer?",
            f"The clues were that {case.clue}. They pointed toward the covered yeast and the warm bowl.",
        ),
        QAItem(
            "Who helped solve the mystery?",
            f"{helper.label} helped by examining the flour trail, warming the bowl, and encouraging patience.",
        ),
        QAItem(
            "How did grit help?",
            f"Grit helped because the detective kept kneading and waiting instead of giving up when the dough did not rise.",
        ),
        QAItem(
            "What transformation happened?",
            f"The yeast transformed the dough: {case.transformation}.",
        ),
        QAItem(
            "Who was responsible for the change?",
            "The yeast was responsible for the change, but it needed warmth, time, and the children's careful work.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is yeast?",
            "Yeast is a living ingredient that helps dough rise by making tiny bubbles inside it.",
        ),
        QAItem(
            "What is grit?",
            "Grit is the courage to keep working carefully when a task is difficult.",
        ),
        QAItem(
            "What is foreshadowing?",
            "Foreshadowing is an early clue that hints at something important later in a story.",
        ),
        QAItem(
            "What is transformation?",
            "Transformation is a meaningful change from one form or condition into another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---", f"place: {world.place.label}"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: meters={entity.meters or {}} memes={entity.memes or {}}"
        )
    lines.append(f"fired rules: {sorted(world.fired)}")
    lines.append(f"case solved: {world.facts.get('solved', False)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    solve_case(world)
    return StorySample(
        params=params,
        story=render_story(world),
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


CURATED = [
    StoryParams(
        place="bakery",
        case="moon_loaf",
        name="Luna",
        helper="Pip",
        telling="lantern",
    ),
    StoryParams(
        place="school_kitchen",
        case="star_rolls",
        name="Mara",
        helper="Theo",
        telling="rainy",
    ),
    StoryParams(
        place="harbor_cafe",
        case="giant_bun",
        name="Iris",
        helper="Nell",
        telling="market",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:")
        for story in stories:
            print(" ", story)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            attempts += 1
            rng = random.Random(base_seed + attempts)
            try:
                params = resolve_params(args, rng)
            except StoryError as error:
                print(error)
                return
            params.seed = base_seed + attempts
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
