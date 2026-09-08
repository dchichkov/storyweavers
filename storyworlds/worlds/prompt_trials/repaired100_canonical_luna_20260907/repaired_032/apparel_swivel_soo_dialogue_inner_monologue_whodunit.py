#!/usr/bin/env python3
"""
A small child-facing whodunit about a missing piece of apparel, a swivel, and
Soo's careful use of dialogue and inner thoughts.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Clue:
    id: str
    description: str
    points_to: str


@dataclass
class StoryParams:
    apparel: str
    swivel: str
    detective: str
    helper: str
    setting: str = "the school costume room"
    seed: Optional[int] = None


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    clues: list[Clue] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


APPAREL = {
    "silver_cape": "a silver stage cape",
    "red_hat": "a red parade hat",
    "blue_sash": "a blue dancer's sash",
    "green_vest": "a green explorer's vest",
}

SWIVELS = {
    "brass_swivel": "a brass swivel hook",
    "wooden_swivel": "a wooden swivel stand",
    "silver_swivel": "a silver swivel clasp",
}

NAMES = ["Soo", "Mina", "Pip", "Lena", "Theo", "Nia"]
SETTINGS = [
    "the school costume room",
    "the little theater backstage",
    "the town parade shed",
]

ASP_RULES = r"""
apparel(A) :- apparel_name(A).
swivel(S) :- swivel_name(S).
suspect(X) :- suspect_name(X).
clue(C) :- clue_name(C).

solves(X) :- suspect(X), observant(X), asks_questions(X).
valid_case(A, S, X) :- apparel(A), swivel(S), solves(X), clue(C),
                        clue_links(C, A), clue_links(C, S).

#show valid_case/3.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Whodunit storyworld about apparel, a swivel, and Soo."
    )
    parser.add_argument("--apparel", choices=sorted(APPAREL))
    parser.add_argument("--swivel", choices=sorted(SWIVELS))
    parser.add_argument("--detective")
    parser.add_argument("--helper")
    parser.add_argument("--setting", choices=SETTINGS)
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


def valid_combos() -> list[tuple[str, str]]:
    return sorted((a, s) for a in APPAREL for s in SWIVELS)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    apparel = args.apparel or rng.choice(sorted(APPAREL))
    swivel = args.swivel or rng.choice(sorted(SWIVELS))
    detective = args.detective or "Soo"
    helper_choices = [n for n in NAMES if n != detective]
    helper = args.helper or rng.choice(helper_choices)
    if helper == detective:
        raise StoryError("The detective and helper must be different children.")
    if detective not in NAMES or helper not in NAMES:
        raise StoryError("Names must come from the story's child detective roster.")
    return StoryParams(
        apparel=apparel,
        swivel=swivel,
        detective=detective,
        helper=helper,
        setting=args.setting or rng.choice(SETTINGS),
    )


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for item in APPAREL:
        lines.append(asp.fact("apparel_name", item))
    for item in SWIVELS:
        lines.append(asp.fact("swivel_name", item))
    for name in NAMES:
        lines.append(asp.fact("suspect_name", name))
    lines.extend(
        [
            asp.fact("observant", "Soo"),
            asp.fact("asks_questions", "Soo"),
            asp.fact("clue_name", "thread"),
        ]
    )
    for apparel in APPAREL:
        for swivel in SWIVELS:
            lines.append(asp.fact("clue_links", "thread", apparel))
            lines.append(asp.fact("clue_links", "thread", swivel))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_case/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_cases() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_case")))


def asp_verify() -> int:
    expected = {(a, s, "Soo") for a, s in valid_combos()}
    actual = set(asp_valid_cases())
    if expected == actual:
        print(f"OK: clingo gate matches Python cases ({len(expected)} cases).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  only in clingo:", sorted(actual - expected))
    print("  only in python:", sorted(expected - actual))
    return 1


def build_world(params: StoryParams) -> World:
    world = World(params)
    detective = world.add(
        Entity(
            params.detective,
            "character",
            params.detective,
            memes={"curiosity": 2.0, "patience": 2.0},
        )
    )
    helper = world.add(
        Entity(
            params.helper,
            "character",
            params.helper,
            memes={"helpfulness": 2.0},
        )
    )
    apparel = world.add(
        Entity(
            "apparel",
            "apparel",
            APPAREL[params.apparel],
            meters={"present": 0.0},
        )
    )
    swivel = world.add(
        Entity(
            "swivel",
            "swivel",
            SWIVELS[params.swivel],
            meters={"present": 1.0},
        )
    )
    world.add(Entity("button", "clue", "a loose blue button"))
    world.add(Entity("thread", "clue", "a short silver thread"))

    world.clues = [
        Clue("thread", "a short silver thread caught on the swivel", "the missing apparel"),
        Clue("button", "a loose blue button beneath the costume rack", "the costume closet"),
    ]
    world.facts.update(
        detective=detective,
        helper=helper,
        apparel=apparel,
        swivel=swivel,
        culprit="the costume-room cat",
        solution=(
            f"The {apparel.label} was not stolen. It had snagged on the "
            f"{swivel.label} and been dragged behind the tall costume trunk."
        ),
    )
    return world


def tell(world: World) -> None:
    p = world.params
    f = world.facts
    detective: Entity = f["detective"]
    helper: Entity = f["helper"]
    apparel: Entity = f["apparel"]
    swivel: Entity = f["swivel"]

    world.say(
        f"At {p.setting}, {detective.label} was preparing costumes when "
        f"{apparel.label} vanished from its hook."
    )
    world.say(
        f"The cast needed it for the afternoon play, and the only thing left "
        f"on the hook was {swivel.label}."
    )
    world.say(
        f'"Nobody leaves until we know what happened," {detective.label} said. '
        f'"Let us look closely," replied {helper.label}.'
    )

    world.para()
    world.say(
        f"{detective.label} crouched beside the rack. "
        f"Inside {detective.label}'s thoughts, a small question flickered: "
        f'"If someone took the apparel, why leave the swivel behind?"'
    )
    world.say(
        f"{detective.label} noticed a short silver thread caught on the swivel "
        f"and a loose blue button beneath the rack."
    )
    world.say(
        f'"The thread matches the missing apparel," {detective.label} said. '
        f'"Then the swivel may have pulled it away," said {helper.label}.'
    )
    world.say(
        f"{helper.label} turned the swivel slowly. It made one complete turn, "
        f"and the thread pointed toward the tall costume trunk."
    )
    world.say(
        f"{detective.label} whispered, "
        f'"The clue is not just what we found. It shows a direction."'
    )

    world.para()
    world.say(
        f"Together, {detective.label} and {helper.label} moved the trunk carefully. "
        f"There was {apparel.label}, crumpled but safe, with the swivel hook still "
        f"caught in its hem."
    )
    world.say(
        f"The costume-room cat blinked from behind the trunk. It had brushed "
        f"against the rack and dragged the apparel while chasing a bright thread."
    )
    world.say(
        f'"So the cat caused the mystery without meaning to," said {helper.label}. '
        f'"And our clues told us where to look," answered {detective.label}.'
    )
    world.say(
        f"{detective.label} freed the hem from the swivel, smoothed the apparel, "
        f"and returned it to its hook. The play could begin."
    )
    world.say(
        f"At curtain time, the silver thread was gone from the swivel, and "
        f"{apparel.label} shone beneath the stage lights like a solved secret."
    )
    apparel.meters["present"] = 1.0
    apparel.memes["recovered"] = 1.0
    swivel.memes["revealing"] = 1.0
    world.fired.update({"question_asked", "clue_followed", "case_solved"})


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a child-friendly whodunit about missing apparel and a swivel.",
            f"Show how {params.detective} uses dialogue and inner monologue to follow physical clues.",
            "End with the missing item recovered and the mystery explained.",
        ],
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            f"What disappeared from the costume room?",
            f"{p.detective} was looking for {f['apparel'].label}, the missing piece of apparel.",
        ),
        QAItem(
            "What clue did the swivel provide?",
            f"The swivel held a short silver thread and turned toward the costume trunk, showing where the apparel had gone.",
        ),
        QAItem(
            f"How did {p.detective} solve the mystery?",
            f"{p.detective} asked questions, shared ideas with {p.helper}, and followed the thread and the swivel's direction.",
        ),
        QAItem(
            "Who caused the disappearance?",
            "The costume-room cat accidentally dragged the apparel behind the trunk while chasing a bright thread.",
        ),
        QAItem(
            "What happened at the end?",
            f"The children recovered {f['apparel'].label}, freed it from the swivel, and used it in the play.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is apparel?",
            "Apparel is clothing or something worn on the body.",
        ),
        QAItem(
            "What does a swivel do?",
            "A swivel lets an object turn around while staying attached.",
        ),
        QAItem(
            "What is a whodunit?",
            "A whodunit is a mystery story in which characters discover who caused an event.",
        ),
        QAItem(
            "What is dialogue?",
            "Dialogue is the spoken exchange between characters.",
        ),
        QAItem(
            "What is inner monologue?",
            "Inner monologue is a character's unspoken thought shown to the reader.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
            f"  {entity.id}: kind={entity.kind}, label={entity.label}, "
            f"meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  clues: {[clue.description for clue in world.clues]}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


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
        apparel="silver_cape",
        swivel="brass_swivel",
        detective="Soo",
        helper="Mina",
        setting="the school costume room",
    ),
    StoryParams(
        apparel="red_hat",
        swivel="silver_swivel",
        detective="Soo",
        helper="Pip",
        setting="the little theater backstage",
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
        cases = asp_valid_cases()
        print(f"{len(cases)} valid cases:")
        for case in cases:
            print(" ", case)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            try:
                params = resolve_params(args, rng)
            except StoryError as error:
                print(error)
                return
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
