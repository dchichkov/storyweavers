#!/usr/bin/env python3
"""
A small mystery storyworld about Kool-Aid in a storage closet, where kindness
and problem solving help friends uncover a missing red pitcher.
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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


OPENERS = [
    "On a rainy afternoon,",
    "One quiet morning,",
    "Just before the neighborhood party,",
    "When the hallway clock chimed three,",
]

SCENES = [
    "The storage closet smelled of cardboard, soap, and the sweet powder of Kool-Aid.",
    "Dusty shelves filled the storage closet, and a little red Kool-Aid stain marked the floor.",
    "Brooms leaned beside boxes in the storage closet while sunlight made bright squares on the door.",
    "The storage closet was crowded with paper cups, folded tables, and jars of Kool-Aid mix.",
]

CLUES = {
    "stain": {
        "name": "red stain",
        "text": "a thin red Kool-Aid stain beside the lowest shelf",
        "meaning": "the pitcher had leaked while someone moved it",
    },
    "scoop": {
        "name": "blue scoop",
        "text": "a blue measuring scoop resting inside an open box",
        "meaning": "someone had prepared drink mix near the party supplies",
    },
    "cloth": {
        "name": "damp cloth",
        "text": "a damp cloth tucked behind a stack of napkins",
        "meaning": "someone had tried to clean a spill",
    },
}

SOLUTIONS = {
    "label": {
        "name": "reading the labels",
        "action": "read the shelf labels from left to right",
        "result": "found the pitcher behind a box marked PARTY CUPS",
    },
    "map": {
        "name": "following the shelf map",
        "action": "follow the small map taped to the closet door",
        "result": "found the pitcher on the shelf shown by a red star",
    },
    "teamwork": {
        "name": "working together",
        "action": "ask one friend to check high shelves while the other checked low shelves",
        "result": "found the pitcher safely tucked behind a folded table",
    },
}

ENDINGS = {
    "table": "Soon the red Kool-Aid filled the pitcher, and every guest found a cool cup beside the sunny table.",
    "smiles": "At the party, the sweet red drink passed from hand to hand, and the friends smiled because nobody had been blamed.",
    "sparkle": "The cleaned pitcher shone on the table like a small red lantern while the storage closet stood neat behind them.",
}


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
class Setting:
    id: str
    label: str
    affords: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace_events: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)
        self.trace_events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "closet": Setting(
        id="closet",
        label="the storage closet",
        affords={"search"},
    )
}

ACTIVITIES = {
    "search": {
        "verb": "search for the missing Kool-Aid pitcher",
        "gerund": "searching for the missing Kool-Aid pitcher",
    }
}

NAMES = ["Luna", "Milo", "Nia", "Toby", "Ravi"]
HELPERS = ["Ari", "June", "Sam", "Pip"]


@dataclass
class StoryParams:
    place: str = "closet"
    activity: str = "search"
    clue: str = "stain"
    solution: str = "label"
    ending: str = "table"
    name: str = "Luna"
    helper: str = "Ari"
    seed: Optional[int] = None


KNOWLEDGE = {
    "koolaid": [
        QAItem(
            question="What is Kool-Aid?",
            answer="Kool-Aid is a flavored drink mix that can be stirred into water, often with sugar.",
        )
    ],
    "kindness": [
        QAItem(
            question="Why is kindness useful when solving a problem?",
            answer="Kindness helps people listen, share ideas, and fix a problem without blaming someone who may need help.",
        )
    ],
    "problem_solving": [
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing clues, thinking of possible answers, and trying a careful plan.",
        )
    ],
    "mystery": [
        QAItem(
            question="What makes a story a mystery?",
            answer="A mystery gives characters a question, clues, and a discovery that explains what happened.",
        )
    ],
}


def build_world(params: StoryParams, rng: random.Random) -> World:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.activity not in ACTIVITIES:
        raise StoryError(f"Unknown activity: {params.activity}")
    if params.clue not in CLUES:
        raise StoryError(f"Unknown clue: {params.clue}")
    if params.solution not in SOLUTIONS:
        raise StoryError(f"Unknown solution: {params.solution}")
    if params.ending not in ENDINGS:
        raise StoryError(f"Unknown ending: {params.ending}")
    if params.name == params.helper:
        raise StoryError("The child and helper must have different names.")

    world = World(SETTINGS[params.place])
    child = world.add(Entity(
        id=params.name,
        kind="character",
        label=f"a curious child named {params.name}",
        location="hallway",
        memes={"curiosity": 1.0, "kindness": 0.0, "confidence": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        label=f"{params.helper}, a careful friend",
        location="hallway",
        memes={"kindness": 1.0, "confidence": 0.0},
    ))
    pitcher = world.add(Entity(
        id="pitcher",
        kind="object",
        label="the red Kool-Aid pitcher",
        owner="party",
        location="unknown",
        meters={"missing": 1.0},
    ))

    clue = CLUES[params.clue]
    solution = SOLUTIONS[params.solution]
    world.facts.update(
        child=child,
        helper=helper,
        pitcher=pitcher,
        clue=clue,
        solution=solution,
        ending=ENDINGS[params.ending],
        scene=rng.choice(SCENES),
        opener=rng.choice(OPENERS),
    )

    world.say(
        f"{world.facts['opener']} {params.name} was asked to bring {pitcher.label} from {world.setting.label}."
    )
    world.say(world.facts["scene"])
    world.say(
        f"At the doorway, {params.name} frowned. The pitcher was not beside the cups where it belonged."
    )
    world.para()

    child.memes["worry"] = 1.0
    world.say(
        f'"I cannot find it," {params.name} said. "What if everyone waits for a drink?"'
    )
    world.say(
        f'"We can solve it together," {params.helper} replied. "Let us look for clues instead of blaming anyone."'
    )
    world.say(
        f"They stepped into {world.setting.label} and noticed {clue['text']}."
    )

    pitcher.location = "storage closet"
    pitcher.meters["missing"] = 0.0
    pitcher.meters["found_clue"] = 1.0
    world.facts["clue_found"] = True
    world.say(
        f"The clue suggested that {clue['meaning']}."
    )
    world.say(
        f"{params.name} wanted to pull every box down, but {params.helper} shook their head. "
        f'"Kindness means we leave the closet safe for the next person," {params.helper} said.'
    )
    world.say(
        f"Together, they decided to {solution['action']}."
    )

    child.memes["confidence"] += 1.0
    helper.memes["confidence"] += 1.0
    world.facts["method_used"] = solution["name"]
    world.say(
        f"The careful plan worked: they {solution['result']}."
    )
    world.say(
        f"{params.name} lifted the pitcher while {params.helper} steadied the boxes. "
        f"The red Kool-Aid pitcher was dusty, but it was not broken."
    )
    world.say(
        f'"We found it without making a mess," {params.name} said. '
        f'"And nobody had to feel bad," {params.helper} answered.'
    )
    child.memes["kindness"] = 1.0
    helper.memes["kindness"] += 1.0
    world.para()
    world.say(world.facts["ending"])
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short mystery for young readers about {f['child'].id} and {f['helper'].id} searching {world.setting.label} for a missing Kool-Aid pitcher.",
        f"Use the clue {f['clue']['text']} and show kindness guiding a careful problem-solving plan.",
        f"End with this image: {f['ending']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"].id
    helper = f["helper"].id
    clue = f["clue"]
    solution = f["solution"]
    return [
        QAItem(
            question=f"Why did {child} enter the storage closet?",
            answer=f"{child} entered the storage closet to search for the missing red Kool-Aid pitcher before the party.",
        ),
        QAItem(
            question=f"What clue helped {child} and {helper}?",
            answer=f"They noticed {clue['text']}, which suggested that {clue['meaning']}.",
        ),
        QAItem(
            question=f"How did kindness help solve the mystery?",
            answer=f"{helper} asked {child} not to blame anyone and encouraged a safe search, so they could solve the problem together.",
        ),
        QAItem(
            question="What problem-solving method did they use?",
            answer=f"They used {solution['name']}: they {solution['action']}, and then {solution['result']}.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"The missing pitcher was found safely, the closet stayed orderly, and Kool-Aid was ready for the party. {f['ending']}",
        ),
    ]


def world_knowledge_qa(_: World) -> list[QAItem]:
    return [
        item
        for topic in ("koolaid", "kindness", "problem_solving", "mystery")
        for item in KNOWLEDGE[topic]
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: location={entity.location!r} meters={meters} memes={memes}"
        )
    lines.append("  events:")
    lines.extend(f"    - {event}" for event in world.trace_events)
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place="closet",
        activity="search",
        clue=args.clue or rng.choice(list(CLUES)),
        solution=args.solution or rng.choice(list(SOLUTIONS)),
        ending=args.ending or rng.choice(list(ENDINGS)),
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
    )


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else 0)
    world = build_world(params, rng)
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


ASP_RULES = r"""
setting(closet).
activity(search).
item(pitcher).
contains(koolaid, pitcher).
clue(stain).
clue(scoop).
clue(cloth).
method(label).
method(map).
method(teamwork).
kindness.
problem_solving.
mystery.

searches(search, pitcher).
safe_method(label).
safe_method(map).
safe_method(teamwork).
uses_clue(stain, search).
uses_clue(scoop, search).
uses_clue(cloth, search).
solves(search, pitcher) :- searches(search, pitcher), problem_solving, kindness, safe_method(label).
solves(search, pitcher) :- searches(search, pitcher), problem_solving, kindness, safe_method(map).
solves(search, pitcher) :- searches(search, pitcher), problem_solving, kindness, safe_method(teamwork).
valid_story(Place, Activity, Item) :-
    setting(Place),
    activity(Activity),
    item(Item),
    searches(Activity, Item),
    kindness,
    problem_solving,
    mystery,
    solves(Activity, Item).
"""


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("setting", "closet"),
        asp.fact("activity", "search"),
        asp.fact("item", "pitcher"),
        asp.fact("contains", "koolaid", "pitcher"),
        asp.fact("kindness"),
        asp.fact("problem_solving"),
        asp.fact("mystery"),
        asp.fact("searches", "search", "pitcher"),
        asp.fact("safe_method", "label"),
        asp.fact("safe_method", "map"),
        asp.fact("safe_method", "teamwork"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid_combos() -> list[tuple[str, str, str]]:
    return [("closet", "search", "pitcher")]


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    try:
        asp_result = set(asp_valid_combos())
    except ImportError as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    python_result = set(python_valid_combos())
    if asp_result != python_result:
        print("MISMATCH between ASP and Python reasonableness gates.")
        print("  only in ASP:", sorted(asp_result - python_result))
        print("  only in Python:", sorted(python_result - asp_result))
        return 1

    for seed in range(5):
        params = StoryParams(seed=seed)
        sample = generate(params)
        if not sample.story.strip() or "Kool-Aid" not in sample.story:
            print("Generated story verification failed.")
            return 1

    print("OK: ASP/Python parity and generated story checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A mystery storyworld about Kool-Aid in a storage closet."
    )
    parser.add_argument("--place", choices=SETTINGS, default="closet")
    parser.add_argument("--activity", choices=ACTIVITIES, default="search")
    parser.add_argument("--clue", choices=CLUES)
    parser.add_argument("--solution", choices=SOLUTIONS)
    parser.add_argument("--ending", choices=ENDINGS)
    parser.add_argument("--name")
    parser.add_argument("--helper")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        try:
            import asp

            model = asp.one_model(asp_program())
            atoms = asp.atoms(model, "valid_story")
            print("ASP valid stories:")
            for atom in sorted(atoms):
                print(f"  {atom}")
        except ImportError as exc:
            raise StoryError(f"ASP mode requires clingo: {exc}") from exc
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    count = max(1, args.n)
    if args.all:
        count = len(CLUES) * len(SOLUTIONS)
        combinations = [
            (clue, solution)
            for clue in CLUES
            for solution in SOLUTIONS
        ]
        for i, (clue, solution) in enumerate(combinations):
            params = StoryParams(
                clue=clue,
                solution=solution,
                ending=list(ENDINGS)[i % len(ENDINGS)],
                name=NAMES[i % len(NAMES)],
                helper=HELPERS[i % len(HELPERS)],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        for i in range(count):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
