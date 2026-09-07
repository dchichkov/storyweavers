#!/usr/bin/env python3
"""
Heartwarming dining-room quest: a darling decides what to do.

A child notices that a little note has vanished from the dining-room table.
Through an inner monologue and a gentle suspenseful quest, the child follows
small clues, decides to ask for help, and discovers a loving surprise.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Setting:
    place: str = "the dining room"
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[tuple[str, ...]] = field(default_factory=set)
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


NAMES = (
    ("Lila", "girl"),
    ("Noah", "boy"),
    ("Mara", "girl"),
    ("Theo", "boy"),
    ("Pip", "child"),
    ("June", "girl"),
)

DARLINGS = (
    ("Grandma", "grandmother"),
    ("Dad", "father"),
    ("Mama", "mother"),
    ("Auntie Rose", "aunt"),
    ("Grandpa", "grandfather"),
)

TABLES = (
    "the round oak table",
    "the table beneath the sunny window",
    "the long table with blue chairs",
    "the little table beside the china cabinet",
    "the polished table under the paper stars",
)

QUEST_OBJECTS = (
    "a folded darling note",
    "a tiny envelope sealed with a gold heart",
    "a blue card with a smiling moon",
    "a little paper crown",
    "a recipe card covered in red hearts",
)

CLUES = (
    (
        "one silver button beside the salt bowl",
        "a soft trail of flour leading toward the sideboard",
        "the button belonged to the darling's old cardigan",
        "the flour marked the path to the hidden envelope",
    ),
    (
        "a green ribbon curled beneath a chair",
        "three crumbs beside the flower vase",
        "the ribbon had fallen from the darling's apron",
        "the crumbs pointed toward the bread basket",
    ),
    (
        "a warm candle scent near the window",
        "a tiny paper star under the serving plate",
        "the candle had been lit while the surprise was prepared",
        "the paper star had slipped from the secret card",
    ),
    (
        "a pencil mark on the tablecloth",
        "a quiet rustle inside the china cabinet",
        "the mark was shaped like the first letter of the darling's name",
        "the cabinet held the place chosen for the surprise",
    ),
)

MOTIVES = (
    "the darling wanted to leave a loving surprise before supper",
    "the darling hoped to remind the child that they were deeply loved",
    "the darling had prepared a small celebration for finishing a brave quest",
    "the darling wanted the dining room to hold one more happy memory",
)

ENDING_IMAGES = (
    "The dining-room lamp glowed over the table, and the little heart on the note seemed to smile.",
    "Soon the plates were warm with supper, while the darling note rested safely beside the child's spoon.",
    "The blue chairs gathered close, and the family laughed beneath the paper stars.",
    "The candle made a golden pool on the table as the child tucked the note into a special pocket.",
    "The envelope stayed on the mantel after supper, shining like a tiny promise.",
)

REACTIONS = (
    "took a careful breath and listened before moving",
    "wondered whether a good quest began with noticing small things",
    "felt a flutter of suspense but chose to look closely",
    "remembered that asking for help could be part of being brave",
)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child_name: str = "Lila"
    child_type: str = "girl"
    darling_name: str = "Grandma"
    darling_type: str = "grandmother"
    table: str = TABLES[0]
    quest_object: str = QUEST_OBJECTS[0]
    first_clue: str = CLUES[0][0]
    second_clue: str = CLUES[0][1]
    first_meaning: str = CLUES[0][2]
    second_meaning: str = CLUES[0][3]
    motive: str = MOTIVES[0]
    reaction: str = REACTIONS[0]
    ending: str = ENDING_IMAGES[0]


def _pronoun(entity_type: str, case: str = "subject") -> str:
    if entity_type in {"girl", "mother", "grandmother", "aunt"}:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    if entity_type in {"boy", "father", "grandfather"}:
        return {"subject": "he", "object": "him", "possessive": "his"}[case]
    return {"subject": "they", "object": "them", "possessive": "their"}[case]


def tell(params: StoryParams) -> World:
    setting = Setting()
    world = World(setting)
    child = world.add(Entity("child", "character", params.child_name))
    darling = world.add(Entity("darling", "character", params.darling_name))
    quest = world.add(Entity("quest_object", "object", params.quest_object))

    child.meters["curiosity"] = 1.0
    child.meters["courage"] = 0.5
    child.memes["wonder"] = 1.0
    darling.memes["care"] = 1.0
    quest.meters["importance"] = 1.0

    world.facts.update(
        child=child,
        darling=darling,
        quest=quest,
        setting=setting,
        first_clue=params.first_clue,
        second_clue=params.second_clue,
        first_meaning=params.first_meaning,
        second_meaning=params.second_meaning,
        motive=params.motive,
    )

    world.say(
        f"After washing their hands, {child.label} came into the dining room for supper. "
        f"{params.table} was set with shining spoons, but {params.quest_object} was missing."
    )
    world.say(
        f'"Where could it be?" {child.label} whispered. '
        f"{_pronoun(params.child_type).capitalize()} felt the suspense gather quietly around the chairs."
    )

    world.para()
    child.memes["quest_started"] = 1.0
    child.meters["courage"] += 0.25
    world.say(
        f"{child.label} began a careful quest. In an inner monologue, "
        f"{_pronoun(params.child_type)} thought, "
        f'"I can decide what to do. First I will notice, then I will ask."'
    )
    world.say(
        f"The first thing {child.label} noticed was {params.first_clue}. "
        f"It made the missing {params.quest_object} feel less like a loss and more like a secret."
    )
    child.memes["first_clue"] = 1.0

    world.para()
    child.meters["courage"] += 0.25
    child.memes["second_clue"] = 1.0
    world.say(
        f"Under the edge of {params.table}, {child.label} found {params.second_clue}. "
        f"The room was very still, and even the clock seemed to wait."
    )
    world.say(
        f'"I could keep guessing," {child.label} thought, "but a brave darling does not have to solve every mystery alone."'
    )
    world.say(
        f"So {child.label} decided to call for {darling.label}. "
        f"{darling.label} came from the kitchen with a warm smile and flour on {_pronoun(params.darling_type, "possessive")} sleeve."
    )

    world.para()
    child.memes["asked_for_help"] = 1.0
    child.memes["relief"] = 1.0
    quest.meters["found"] = 1.0
    darling.memes["care"] += 1.0
    world.say(
        f"{darling.label} followed the clues to a small basket beside the sideboard. "
        f"Inside lay {params.quest_object}, safe beneath a linen napkin."
    )
    world.say(
        f'"The {params.first_clue} and {params.second_clue} were little hints," '
        f"{darling.label} explained. {params.first_meaning.capitalize()}, and {params.second_meaning}."
    )
    world.say(
        f'"I moved it because {params.motive}." '
        f"{child.label} held the note close, and the suspense softened into a happy glow."
    )
    child.memes["understanding"] = 1.0

    world.para()
    child.meters["courage"] = 1.0
    child.memes["joy"] = 1.0
    world.say(
        f"{child.label} thanked {darling.label}, then placed the precious surprise beside "
        f"{_pronoun(params.child_type, "possessive")} plate. The quest had ended, not with a frightening answer, "
        f"but with a loving one."
    )
    world.say(params.ending)
    return world


ASP_RULES = r"""
missing(quest_note).
has_clue(first).
has_clue(second).
has_darling(darling).
asked_for_help(child).
kind_reason(darling).

quest(note) :- missing(quest_note), has_clue(first), has_clue(second).
resolved(note) :- quest(note), has_darling(darling), asked_for_help(child), kind_reason(darling).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("missing", "quest_note"),
            asp.fact("has_clue", "first"),
            asp.fact("has_clue", "second"),
            asp.fact("has_darling", "darling"),
            asp.fact("asked_for_help", "child"),
            asp.fact("kind_reason", "darling"),
        ]
    )


def asp_program(show: str = "#show quest/1.\n#show resolved/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    quests = set(asp.atoms(model, "quest"))
    resolved = set(asp.atoms(model, "resolved"))
    if quests == {("note",)} and resolved == {("note",)}:
        sample = generate(resolve_params(argparse.Namespace(seed=17), random.Random(17)))
        if sample.story and "decided" in sample.story:
            print("OK: ASP and Python agree on the dining-room quest.")
            return 0
    print("MISMATCH between ASP and Python.")
    print("ASP quest:", sorted(quests))
    print("ASP resolved:", sorted(resolved))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a heartwarming dining-room quest with inner monologue and suspense."
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
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    seed = int(args.seed if args.seed is not None else 0)
    local = random.Random(seed)
    child_name, child_type = local.choice(NAMES)
    darling_name, darling_type = local.choice(DARLINGS)
    clues = local.choice(CLUES)
    return StoryParams(
        seed=seed,
        child_name=child_name,
        child_type=child_type,
        darling_name=darling_name,
        darling_type=darling_type,
        table=local.choice(TABLES),
        quest_object=local.choice(QUEST_OBJECTS),
        first_clue=clues[0],
        second_clue=clues[1],
        first_meaning=clues[2],
        second_meaning=clues[3],
        motive=local.choice(MOTIVES),
        reaction=local.choice(REACTIONS),
        ending=local.choice(ENDING_IMAGES),
    )


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    darling = world.facts["darling"]
    return [
        f"Write a heartwarming dining-room quest in which {child.label} must decide what to do.",
        f"Use an inner monologue as {child.label} follows clues and asks {darling.label} for help.",
        "Build gentle suspense around a missing loving surprise, then resolve it with warmth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    darling: Entity = world.facts["darling"]
    quest: Entity = world.facts["quest"]
    return [
        QAItem(
            question=f"What was missing from the dining room when {child.label} arrived?",
            answer=f"{quest.label.capitalize()} was missing from the dining-room table when {child.label} arrived for supper.",
        ),
        QAItem(
            question=f"Which clues helped {child.label} on the quest?",
            answer=f"{child.label} noticed {world.facts['first_clue']} and later found {world.facts['second_clue']}.",
        ),
        QAItem(
            question=f"What did {child.label} decide to do when the mystery felt difficult?",
            answer=f"{child.label} decided to call for {darling.label} instead of continuing to guess alone.",
        ),
        QAItem(
            question=f"Why had {darling.label} moved the surprise?",
            answer=f"{darling.label} had moved it because {world.facts['motive']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet stream of thoughts a character has inside their mind.",
        ),
        QAItem(
            question="Why can asking for help be brave?",
            answer="Asking for help can be brave because it admits that a problem is difficult while still choosing to solve it safely.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next while a character faces an unanswered question.",
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
            f"{entity.id}: meters={dict(entity.meters)} memes={dict(entity.memes)}"
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
        print(asp_program())
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(sorted(set(asp.atoms(model, "quest"))))
        print(sorted(set(asp.atoms(model, "resolved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 1 if args.all else max(1, args.n)
    samples = []
    for index in range(count):
        seed = base_seed + index
        params = resolve_params(argparse.Namespace(seed=seed), random.Random(seed))
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
