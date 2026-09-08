#!/usr/bin/env python3
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(
        default_factory=lambda: {
            "distance": 0.0,
            "battery": 0.0,
            "clarity": 0.0,
            "warmth": 0.0,
        }
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {
            "worry": 0.0,
            "curiosity": 0.0,
            "trust": 0.0,
            "courage": 0.0,
            "relief": 0.0,
            "joy": 0.0,
        }
    )
    location: str = ""
    carried_by: Optional[str] = None


@dataclass
class Setting:
    name: str = "the little hill-town terminal"


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    terminal_name: str
    mystery_index: int = 0
    detail_variant: int = 0
    seed: Optional[int] = None


MYSTERIES = [
    {
        "place": "the old bus terminal",
        "object": "a small brass bell",
        "clue": "a line of muddy paw prints beside the lost-and-found bench",
        "wrong": "They searched the ticket windows first, but the bell was not there.",
        "method": "They followed the paw prints to a quiet waiting room and looked beneath the lowest bench.",
        "answer": "a tired little dog had carried the bell there because its tag was caught on the handle",
        "resolution": "The child freed the tag gently, and the dog wagged while the bell rang again.",
        "lesson": "careful listening and kindness can solve a mystery better than rushing",
        "image": "the bell chimed softly as the dog curled beside its grateful owner",
        "question": "Where did the brass bell go?",
    },
    {
        "place": "the rain-bright terminal platform",
        "object": "a blue knitted scarf",
        "clue": "one blue thread caught on a warm radiator",
        "wrong": "They checked every empty seat, but the scarf had slipped beyond the main hall.",
        "method": "They followed the thread toward the service corridor and asked the keeper before opening the door.",
        "answer": "a grandmother had placed the scarf near the radiator so it could dry for her grandson",
        "resolution": "The scarf was returned before the next bus arrived, warm and ready for its small owner.",
        "lesson": "asking before acting helps protect what belongs to someone else",
        "image": "the blue scarf rested around a boy's shoulders while rain glittered on the windows",
        "question": "Why was the blue scarf near the radiator?",
    },
    {
        "place": "the terminal's quiet information room",
        "object": "a paper star",
        "clue": "a silver fleck on the message board",
        "wrong": "They looked under the chairs, although the star had never fallen to the floor.",
        "method": "They compared the silver fleck with the empty space on a child's card and checked the board one careful row at a time.",
        "answer": "the star had been moved onto the message board to brighten a lonely traveler's note",
        "resolution": "The child added a new star beside it, and the traveler smiled at the small kindness.",
        "lesson": "a mystery may be solved by noticing why something was moved, not only where it went",
        "image": "two paper stars shone above a note that said, 'You are not alone.'",
        "question": "Why had the paper star been moved?",
    },
    {
        "place": "the terminal's covered bicycle stand",
        "object": "a red key",
        "clue": "a faint bell sound behind a stack of delivery crates",
        "wrong": "They pulled at the crates too quickly and made the hidden bicycle wobble.",
        "method": "They steadied the crates, called for the station keeper, and slid the key out with a ruler.",
        "answer": "the key had fallen from a rider's pocket and landed beside a bicycle bell",
        "resolution": "The rider found the key and thanked the friends for taking their time.",
        "lesson": "patience can keep a small problem from becoming a bigger one",
        "image": "the red key gleamed in its owner's palm as bicycles hummed past",
        "question": "How did the friends recover the red key safely?",
    },
]


OPENINGS = [
    "One gentle morning",
    "Just before the first bus arrived",
    "While rain tapped the terminal roof",
    "As the town lights faded into dawn",
    "On a cool afternoon",
]


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace_log: list[str] = []

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

    def log(self, text: str) -> None:
        self.trace_log.append(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming terminal mystery with a lesson learned."
    )
    parser.add_argument("--name")
    parser.add_argument("--type")
    parser.add_argument("--helper")
    parser.add_argument("--helper-type")
    parser.add_argument("--terminal")
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
        child_name=args.name or rng.choice(["Luna", "Mira", "Theo", "Nell", "Pip"]),
        child_type=args.type or rng.choice(["rabbit", "fox", "mouse", "otter", "bear"]),
        helper_name=args.helper or rng.choice(["Ari", "Milo", "Sana", "Jo", "Bea"]),
        helper_type=args.helper_type or rng.choice(["sparrow", "cat", "badger", "duck", "squirrel"]),
        terminal_name=args.terminal or rng.choice(
            ["the town terminal", "the river terminal", "the old terminal"]
        ),
        mystery_index=rng.randrange(len(MYSTERIES)),
        detail_variant=rng.randrange(10000),
    )


def tell(params: StoryParams) -> World:
    scenario = MYSTERIES[params.mystery_index % len(MYSTERIES)]
    world = World(Setting())
    child = world.add(
        Entity(
            id="child",
            kind="animal",
            type=params.child_type,
            label=params.child_name,
            location="entrance",
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="animal",
            type=params.helper_type,
            label=params.helper_name,
            location="entrance",
        )
    )
    terminal = world.add(
        Entity(
            id="terminal",
            kind="place",
            type="terminal",
            label=params.terminal_name,
            location="town",
        )
    )
    mystery_object = world.add(
        Entity(
            id="mystery_object",
            kind="thing",
            type="lost_object",
            label=scenario["object"],
            location="unknown",
        )
    )
    world.facts.update(
        child=child,
        helper=helper,
        terminal=terminal,
        mystery_object=mystery_object,
        scenario=scenario,
    )

    child.memes["curiosity"] = 1.0
    helper.memes["trust"] = 1.0
    terminal.meters["clarity"] = 0.2

    opening = OPENINGS[params.detail_variant % len(OPENINGS)]
    world.say(
        f"{opening}, {params.child_name} the {params.child_type} arrived at "
        f"{params.terminal_name} with {params.helper_name} the {params.helper_type}."
    )
    world.say(
        f"Near {scenario['place']}, they noticed that {scenario['object']} was missing "
        "from the terminal's lost-and-found basket."
    )
    world.say(
        f"The keeper looked worried. \"Someone is waiting for that,\" the keeper said. "
        f"\"Will you help me find it?\""
    )
    world.say(
        f"\"We will look carefully,\" {params.child_name} promised. "
        f"{params.helper_name} nodded and held the little notebook for clues."
    )
    world.para()

    child.memes["worry"] = 0.8
    mystery_object.meters["distance"] = 1.0
    world.say(
        f"They began near the ticket windows, but {scenario['wrong']}"
    )
    world.say(
        f"Then {params.helper_name} whispered, \"What did we miss?\" "
        f"{params.child_name} listened instead of hurrying."
    )
    world.say(
        f"They found {scenario['clue']}. It was a small clue, but it pointed "
        "toward a reason rather than merely a place."
    )
    child.memes["courage"] = 0.8
    helper.memes["courage"] = 0.7
    world.para()

    world.say(
        f"\"Let us ask before we touch anything,\" said {params.child_name}. "
        f"\"Good idea,\" said {params.helper_name}. \"That way we can help, not harm.\""
    )
    world.say(scenario["method"])
    world.say(
        f"At last, they learned that {scenario['answer']}."
    )
    terminal.meters["clarity"] = 1.0
    mystery_object.meters["clarity"] = 1.0
    mystery_object.location = "found"
    world.para()

    world.say(scenario["resolution"])
    mystery_object.meters["warmth"] = 1.0
    mystery_object.carried_by = "child"
    child.memes["relief"] = 1.0
    helper.memes["relief"] = 1.0
    terminal.meters["battery"] = 1.0
    world.say(
        f"The keeper smiled. \"You solved the mystery,\" the keeper said. "
        f"\"More than that,\" replied {params.child_name}, \"we listened to what the clue was telling us.\""
    )
    world.say(
        f"{params.helper_name} added, \"And we asked first. That made the helping safe.\""
    )
    world.para()

    world.say(
        f"{params.child_name} learned that {scenario['lesson']}."
    )
    world.say(scenario["image"])
    child.memes["joy"] = 1.0
    helper.memes["joy"] = 1.0
    world.log(f"mystery={params.mystery_index % len(MYSTERIES)}")
    world.log("object_found=true")
    world.log("lesson_learned=true")
    return world


def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    scenario: dict[str, str] = world.facts["scenario"]  # type: ignore[assignment]
    return [
        f"Write a heartwarming story about {child.label} and {helper.label} solving a mystery at a terminal.",
        f"Tell how the missing {scenario['object']} was found and what lesson {child.label} learned.",
        "Include a gentle dialogue exchange in which careful listening changes the characters' plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    scenario: dict[str, str] = world.facts["scenario"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What mystery did {child.label} and {helper.label} solve?",
            answer=f"They solved the mystery of the missing {scenario['object']} at the terminal.",
        ),
        QAItem(
            question="What clue helped them?",
            answer=f"They noticed {scenario['clue']}, which led them toward the true reason the object had moved.",
        ),
        QAItem(
            question="What did the friends do differently after their first search?",
            answer="They slowed down, listened to the clue, and asked before touching anything.",
        ),
        QAItem(
            question=f"What lesson did {child.label} learn?",
            answer=f"{child.label} learned that {scenario['lesson']}.",
        ),
        QAItem(
            question="How did the ending show that the problem was solved?",
            answer=scenario["image"].capitalize() + ".",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a terminal?",
            answer="A terminal is a place where travelers begin or end trips, often by bus, train, or another vehicle.",
        ),
        QAItem(
            question="Why should someone ask before moving a lost object?",
            answer="Asking first helps protect the object and makes sure it is returned to the right person.",
        ),
        QAItem(
            question="What makes a mystery easier to solve?",
            answer="Careful observation, patient questions, and connecting clues to possible reasons make a mystery easier to solve.",
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
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        parts = [f"type={entity.type}"]
        if entity.location:
            parts.append(f"location={entity.location}")
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"{entity.id}: " + ", ".join(parts))
    lines.extend(f"event: {event}" for event in world.trace_log)
    return "\n".join(lines)


ASP_RULES = r"""
entity(child).
entity(helper).
entity(terminal).
entity(mystery_object).

clue_noticed.
asked_before_touching.
object_found.
lesson_learned.

solved_mystery :-
    clue_noticed,
    asked_before_touching,
    object_found.

heartwarming_end :-
    solved_mystery,
    lesson_learned.

#show solved_mystery/0.
#show heartwarming_end/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("clue_noticed"),
            asp.fact("asked_before_touching"),
            asp.fact("object_found"),
            asp.fact("lesson_learned"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program("#show solved_mystery/0. #show heartwarming_end/0.")
    )
    atoms = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {"solved_mystery/0", "heartwarming_end/0"}
    if atoms != expected:
        print(f"MISMATCH: {sorted(atoms)} != {sorted(expected)}")
        return 1

    params = StoryParams(
        child_name="Luna",
        child_type="rabbit",
        helper_name="Milo",
        helper_type="cat",
        terminal_name="the old terminal",
    )
    sample = generate(params)
    if not sample.story or "terminal" not in sample.story.lower():
        print("MISMATCH: generated story exercise failed")
        return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        child_name="Luna",
        child_type="rabbit",
        helper_name="Milo",
        helper_type="cat",
        terminal_name="the old terminal",
        mystery_index=0,
        detail_variant=3,
    ),
    StoryParams(
        child_name="Mira",
        child_type="otter",
        helper_name="Bea",
        helper_type="sparrow",
        terminal_name="the river terminal",
        mystery_index=1,
        detail_variant=7,
    ),
    StoryParams(
        child_name="Theo",
        child_type="fox",
        helper_name="Sana",
        helper_type="badger",
        terminal_name="the town terminal",
        mystery_index=2,
        detail_variant=11,
    ),
    StoryParams(
        child_name="Nell",
        child_type="mouse",
        helper_name="Jo",
        helper_type="duck",
        terminal_name="the covered terminal",
        mystery_index=3,
        detail_variant=15,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved_mystery/0. #show heartwarming_end/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program("#show solved_mystery/0. #show heartwarming_end/0.")
        )
        print("ASP model:", " ".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        limit = max(args.n * 20, 20)
        while len(samples) < args.n and index < limit:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            index += 1
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
