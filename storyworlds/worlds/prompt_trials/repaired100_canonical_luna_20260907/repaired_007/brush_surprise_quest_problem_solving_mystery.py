#!/usr/bin/env python3
"""
A small mystery storyworld about a missing brush, a surprising clue, and a
careful quest solved by patient problem solving.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass(frozen=True)
class MysteryCase:
    key: str
    object_name: str
    hiding_place: str
    clue: str
    discovery: str
    solution: str
    opening: tuple[str, str]
    trouble: tuple[str, str]
    quest: tuple[str, str]
    ending: tuple[str, str]


CASES = (
    MysteryCase(
        "blue_swirl",
        "blue paintbrush",
        "behind a folded map",
        "a blue swirl on the edge of the map",
        "a tiny blue bristle caught in its fold",
        "followed the paint marks to the window box",
        (
            "In the little art room, {hero} set out paper, jars, and a {object}.",
            "{helper} promised to paint a moon, but the brush vanished before the first star.",
        ),
        (
            "A surprise waited on the table: one bright blue swirl, but no brush.",
            '"A mystery!" whispered {hero}. "Let us look closely," said {helper}.',
        ),
        (
            "{hero} followed blue specks from the table to a folded map near the shelf.",
            "{helper} opened the map and found {clue}; together they traced the marks toward the window box.",
        ),
        (
            "There, beneath a fallen leaf, rested the {object}, safe beside the flower pots.",
            "The friends smiled. Their careful quest had turned a puzzling surprise into a picture of the moon.",
        ),
    ),
    MysteryCase(
        "green_handle",
        "green-handled brush",
        "inside a clean watering can",
        "three green dots beside the sink",
        "green drops leading toward the watering can",
        "checked the can before blaming the wind",
        (
            "At {place}, {hero} planned a secret garden painting with a {object}.",
            "{helper} mixed yellow and white, then noticed that the brush was gone.",
        ),
        (
            "A surprise sparkled beside the sink: three green dots in a row.",
            '"Could the dots be a message?" asked {helper}. "Only if we inspect them," said {hero}.',
        ),
        (
            "{hero} measured the dots with a finger and found matching drops near the watering can.",
            "{helper} lifted the empty can and discovered {clue}; they searched inside instead of guessing.",
        ),
        (
            "The {object} was tucked inside the clean can, its handle peeking above the rim.",
            "They solved the mystery by checking each clue, then painted leaves that curled like tiny green trails.",
        ),
    ),
    MysteryCase(
        "red_ribbon",
        "red-tipped brush",
        "under a ribbon basket",
        "a red thread on the floor",
        "a red mark beneath the basket",
        "lifted the basket together",
        (
            "In {place}, {hero} prepared a treasure map and placed a {object} beside it.",
            "{helper} turned for one moment, and the brush disappeared.",
        ),
        (
            "A surprise clue shone near the chair: one loose red thread.",
            '"The thread must have come from somewhere," said {hero}. "Then let us follow it," replied {helper}.',
        ),
        (
            "The red thread crossed the floor and ended at the ribbon basket.",
            "{hero} steadied the basket while {helper} looked beneath it and noticed {clue}.",
        ),
        (
            "Under the basket lay the {object}, hidden by a loop of ribbon.",
            "The friends laughed softly. Their question had an answer because they followed evidence one small step at a time.",
        ),
    ),
    MysteryCase(
        "silver_rinse",
        "silver paintbrush",
        "beside the rinse bowl",
        "a shining line across the floor",
        "silver flecks near the rinse bowl",
        "followed the glimmer instead of searching randomly",
        (
            "At {place}, {hero} drew a castle while {helper} brought a {object}.",
            "Then the light flashed, the brush was missing, and the castle had no shining gate.",
        ),
        (
            "A surprise line glittered from the paper table toward the doorway.",
            '"Something shiny moved," said {helper}. "Let us test that idea," said {hero}.',
        ),
        (
            "{hero} checked the line against the paint on the paper and found matching silver flecks.",
            "{helper} followed them to the rinse bowl, where {clue}; they searched carefully around it.",
        ),
        (
            "The {object} rested beside the bowl, safe and ready to finish the castle gate.",
            "The mystery ended with a bright discovery: good questions helped them see the path.",
        ),
    ),
)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


PLACES = {
    "old_studio": "the old studio",
    "garden_shed": "the garden shed",
    "attic_workroom": "the attic workroom",
}

NAMES = ["Luna", "Milo", "Nia", "Owen", "Pip", "Tara"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, case.key) for place in PLACES for case in CASES]


def choose_case(params: StoryParams) -> MysteryCase:
    seed = params.seed if params.seed is not None else sum(ord(c) for c in params.place + params.hero_name)
    return CASES[random.Random(seed).randrange(len(CASES))]


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown setting: {params.place}.")
    if not params.hero_name.strip() or not params.helper_name.strip():
        raise StoryError("Both mystery solvers need names.")
    if params.hero_name == params.helper_name:
        raise StoryError("The two mystery solvers must have different names.")

    case = choose_case(params)
    world = World(place=PLACES[params.place])
    hero = world.add(Entity("hero", "character", params.hero_name))
    helper = world.add(Entity("helper", "character", params.helper_name))
    brush = world.add(Entity("brush", "object", case.object_name))
    hero.memes["curiosity"] = 1.0
    helper.memes["care"] = 1.0
    brush.meters["missing"] = 1.0

    values = {
        "place": world.place,
        "hero": hero.label,
        "helper": helper.label,
        "object": case.object_name,
        "clue": case.clue,
    }
    for line in case.opening:
        world.say(line.format(**values))
    world.para()

    for line in case.trouble:
        world.say(line.format(**values))
    world.para()

    hero.memes["surprise"] = 1.0
    helper.memes["questioning"] = 1.0
    for line in case.quest:
        world.say(line.format(**values))
    world.para()

    brush.meters["missing"] = 0.0
    brush.meters["found"] = 1.0
    hero.memes["pride"] = 1.0
    helper.memes["joy"] = 1.0
    for line in case.ending:
        world.say(line.format(**values))

    world.facts.update(
        hero=hero.label,
        helper=helper.label,
        brush=case.object_name,
        place=world.place,
        case=case.key,
        clue=case.clue,
        discovery=case.discovery,
        solution=case.solution,
        hiding_place=case.hiding_place,
        ending=case.ending[-1].format(**values),
        found=True,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    facts = world.facts
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            'Write a child-friendly mystery story that includes a brush, a surprise clue, and a careful quest.',
            f"Tell a mystery in {facts['place']} where {facts['hero']} and {facts['helper']} solve a missing-brush problem.",
            "Show problem solving through observation, conversation, and a satisfying discovery.",
        ],
        story_qa=[
            QAItem(
                "What went missing?",
                f"The missing object was the {facts['brush']}, which the friends needed for their art.",
            ),
            QAItem(
                "What clue helped solve the mystery?",
                f"They noticed {facts['clue']}, then used it to {facts['discovery']}.",
            ),
            QAItem(
                "How did the friends solve the problem?",
                f"They solved it by {facts['solution']}. Their careful search led them to the {facts['hiding_place']}.",
            ),
            QAItem(
                "What showed that the mystery was over?",
                f"The ending showed the change clearly: {facts['ending']}",
            ),
        ],
        world_qa=[
            QAItem(
                "Why are clues useful in a mystery?",
                "Clues give information about what happened. When people compare clues carefully, they can make a sensible explanation.",
            ),
            QAItem(
                "What is problem solving?",
                "Problem solving means noticing a difficulty, thinking of possible answers, testing useful ideas, and changing the plan when needed.",
            ),
        ],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:7} ({entity.kind:9}) "
            f"meters={meters or {}} memes={memes or {}}"
        )
    lines.append(f"  found_brush={world.facts.get('found')}")
    lines.append(f"  clue={world.facts.get('clue')}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
brush_missing(B) :- brush(B), missing(B).
clue_seen :- brush_missing(B), clue(B).
brush_found(B) :- brush(B), clue_seen, searched(B).
solved :- brush_found(B).
#show solved/0.
"""


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("brush", "brush"),
        asp.fact("missing", "brush"),
        asp.fact("clue", "brush"),
        asp.fact("searched", "brush"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show solved/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return asp.atoms(model, "solved")


def asp_verify() -> int:
    try:
        import asp

        model = asp.one_model(asp_program())
        if not asp.atoms(model, "solved"):
            print("ASP parity failed: the mystery was not solved.")
            return 1
    except Exception as exc:
        print(f"ASP smoke test failed: {exc}")
        return 1

    try:
        for params in (
            StoryParams("old_studio", "Luna", "Milo", seed=1),
            StoryParams("garden_shed", "Nia", "Owen", seed=2),
            StoryParams("attic_workroom", "Pip", "Tara", seed=3),
        ):
            sample = generate(params)
            if not sample.story.strip() or not sample.world.facts["found"]:
                print("Generation smoke test failed.")
                return 1
    except Exception as exc:
        print(f"Generation smoke test failed: {exc}")
        return 1

    print("OK: Python and ASP mystery checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A brush mystery about surprise, quest, and problem solving."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--hero")
    parser.add_argument("--helper")
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
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(NAMES)
    choices = [name for name in NAMES if name != hero]
    helper = args.helper or rng.choice(choices)
    return StoryParams(place=place, hero_name=hero, helper_name=helper, seed=args.seed)


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
        try:
            print(asp_valid_combos())
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            raise SystemExit(1)
        return
    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams("old_studio", "Luna", "Milo", seed=base_seed + i)
            for i in range(len(CASES))
        ]
        params_list = [
            StoryParams(
                place=PLACES.keys().__iter__().__next__(),
                hero_name="Luna",
                helper_name="Milo",
                seed=base_seed,
            )
        ]
        for index, case in enumerate(CASES):
            place = list(PLACES)[index % len(PLACES)]
            params_list[index] = StoryParams(
                place=place,
                hero_name=NAMES[index % len(NAMES)],
                helper_name=NAMES[(index + 1) % len(NAMES)],
                seed=index,
            )
    else:
        params_list = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            if args.seed is None:
                params.seed = base_seed + index
            params_list.append(params)

    samples = [generate(params) for params in params_list]

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
            header=f"### mystery {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
