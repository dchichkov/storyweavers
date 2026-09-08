#!/usr/bin/env python3
"""
A small whodunit storyworld about significance, a wagging clue, and Soo.

A missing silver bell creates suspense in the village garden. Luna and Soo
misunderstand a wagging tail, then follow physical clues to discover that the
"culprit" is a puppy who carried the bell to a safe place.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve()
ROOT = next(parent for parent in HERE.parents if (parent / "results.py").is_file())
sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


NAME_POOL = ["Luna", "Milo", "Nina", "Toby", "Ivy", "Soo"]
HELPER_POOL = ["Soo", "Grandma", "Uncle Jo", "Mina"]
PLACES = ["the village garden", "the old clock courtyard", "the lantern square"]
OBJECTS = ["silver bell", "brass key", "blue ribbon", "tiny music box"]
ANIMALS = ["Pip the puppy", "a brown dog", "the baker's puppy", "a spotted pup"]


CASES = [
    {
        "object": "silver bell",
        "significance": "It was the bell rung every evening to tell the village that supper was ready.",
        "opening": "Luna was polishing the silver bell before the evening supper signal.",
        "problem": "When she looked up, the bell had vanished from the red table.",
        "clue": "a line of damp paw prints crossed the dust beneath the table",
        "misunderstanding": "Soo saw a dog wagging beside the hedge and thought the dog was wagging at the missing bell.",
        "false": "the dog had stolen the bell",
        "turn": "the paw prints led not toward the hedge but toward the rain barrel",
        "solution": "Pip the puppy had carried the bell away because it was rattling near a deep puddle",
        "ending": "The bell hung from its hook again, and its clear note sent every supper bowl toward the garden.",
    },
    {
        "object": "brass key",
        "significance": "It opened the little library cabinet where the village kept its oldest maps.",
        "opening": "Luna was placing the brass key beside the library cabinet before the map club began.",
        "problem": "The key was gone when the cabinet lock needed opening.",
        "clue": "a curl of yellow thread clung to the key's empty hook",
        "misunderstanding": "Soo noticed a wagging scarf near the reading rug and thought its owner was hiding the key.",
        "false": "someone had tucked the key inside the scarf",
        "turn": "the yellow thread matched a bookmark caught beneath the rolling book cart",
        "solution": "the key had slipped into the cart's wheel and been carried across the room",
        "ending": "The cabinet opened, and the oldest map unfolded like a quiet road to the past.",
    },
    {
        "object": "blue ribbon",
        "significance": "It marked the garden's champion sunflower and was awarded only once each summer.",
        "opening": "Luna was tying the blue ribbon to the tallest sunflower for the village fair.",
        "problem": "A gust came through, and the ribbon disappeared from the stalk.",
        "clue": "one blue thread glittered on the edge of the birdbath",
        "misunderstanding": "Soo saw a pigeon wagging its tail feathers and suspected it had carried the prize away.",
        "false": "the pigeon had stolen the ribbon for its nest",
        "turn": "the thread continued in a bright little trail toward the tool shed",
        "solution": "the ribbon had snagged on a rake and been pulled beneath the shed door",
        "ending": "The ribbon returned to the sunflower, whose golden face nodded above the fair.",
    },
    {
        "object": "tiny music box",
        "significance": "Its tune had belonged to Luna's great-grandmother and comforted the family on stormy nights.",
        "opening": "Luna placed the tiny music box on the mantel before the first thundercloud arrived.",
        "problem": "A clap of thunder shook the room, and the music box was nowhere to be seen.",
        "clue": "a faint silver tune came from beneath the window seat",
        "misunderstanding": "Soo saw a wagging curtain and thought someone behind it was secretly playing the box.",
        "false": "a hidden visitor had taken the music box",
        "turn": "the tune grew louder beside a blanket folded under the seat",
        "solution": "the box had slid there when the floor trembled, and the blanket had pressed its music key",
        "ending": "The storm rumbled outside while the old tune made the room feel warm again.",
    },
]


@dataclass
class StoryParams:
    name: str = "Luna"
    helper: str = "Soo"
    place: str = "the village garden"
    animal: str = "Pip the puppy"
    object_name: str = "silver bell"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("distance", "noise", "visibility", "trail"):
            self.meters.setdefault(key, 0.0)
        for key in ("suspense", "confusion", "relief", "curiosity", "trust"):
            self.memes.setdefault(key, 0.0)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


def _seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum(ord(ch) for ch in "|".join(
        [params.name, params.helper, params.place, params.animal, params.object_name]
    ))


def _cap(value: str) -> str:
    return value[:1].upper() + value[1:]


def validate(params: StoryParams) -> None:
    if params.name not in NAME_POOL:
        raise StoryError(f"unknown detective name: {params.name}")
    if params.helper not in HELPER_POOL:
        raise StoryError(f"unknown helper: {params.helper}")
    if params.place not in PLACES:
        raise StoryError(f"unknown place: {params.place}")
    if params.animal not in ANIMALS:
        raise StoryError(f"unknown animal: {params.animal}")
    if params.object_name not in OBJECTS:
        raise StoryError(f"unknown object: {params.object_name}")


def tell_world(params: StoryParams) -> World:
    validate(params)
    rng = random.Random(_seed(params))
    case = next((item for item in CASES if item["object"] == params.object_name), None)
    if case is None:
        raise StoryError(f"no whodunit case is registered for {params.object_name}")

    w = World(params.place)
    detective = w.add(Entity(params.name, "character", params.name))
    helper = w.add(Entity("helper", "character", params.helper))
    suspect = w.add(Entity("suspect", "animal", params.animal))
    focus = w.add(Entity("focus", "object", params.object_name))
    w.facts.update(case=case, params=params, detective=detective, helper=helper,
                   suspect=suspect, focus=focus, case_index=CASES.index(case))

    detective.memes["curiosity"] = 1
    focus.meters["visibility"] = 0
    w.say(f"In {w.place}, {case['opening']}")
    w.say(case["significance"])
    w.say(f"{params.name} was writing down every detail because the object's significance made the disappearance important.")
    w.para()

    detective.memes["suspense"] = 2
    detective.memes["confusion"] = 1
    focus.meters["distance"] = 4
    w.say(f"{case['problem']} The empty place made the whole square feel unusually quiet.")
    w.say(f'"Do you see anything strange?" {params.helper} asked.')
    w.say(f'"Only a wagging clue," {params.name} whispered. "But a wag is not proof."')
    w.say(case["misunderstanding"])
    w.say(f"For one breath, they believed that {case['false']}.")
    w.para()

    detective.memes["curiosity"] += 2
    suspect.meters["trail"] = 1
    w.say(f"{params.name} crouched down and found {case['clue']}.")
    w.say(f'"The tail made us look at the wrong place," {params.name} said. "The ground is telling a different story."')
    w.say(f'"Then let us follow the ground," {params.helper} replied.')
    w.say(f"The suspense tightened until {case['turn']}.")
    w.say(f"They followed the trail together, and discovered that {case['solution']}.")
    w.para()

    detective.memes["confusion"] = 0
    detective.memes["suspense"] = 0
    detective.memes["relief"] = 2
    detective.memes["trust"] = 2
    focus.meters["visibility"] = 1
    focus.meters["distance"] = 0
    w.say(f'"So the wagging was innocent," {params.helper} said.')
    w.say(f'"And the misunderstanding was ours," {params.name} answered, giving {params.animal} a gentle pat.')
    w.say(case["ending"])
    w.facts["resolved"] = True
    w.facts["culprit"] = params.animal
    w.facts["clue"] = case["clue"]
    w.facts["solution"] = case["solution"]
    return w


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    p: StoryParams = world.facts["params"]
    return [
        f"Write a child-friendly whodunit in {p.place} where {p.name} investigates a missing {p.object_name}.",
        f"Build suspense around a misunderstanding involving a wagging {p.animal}, then reveal the significance of the object.",
        f"Tell a Soo-and-{p.name} mystery using the clue '{case['clue']}' and a concrete ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    case = world.facts["case"]
    return [
        QAItem(
            question=f"What important object disappears from {p.place}?",
            answer=f"The {p.object_name} disappears from {p.place}. {case['significance']}",
        ),
        QAItem(
            question="What misunderstanding increases the suspense?",
            answer=f"Soo and the detective think that {case['false']}, but the wagging clue is misleading.",
        ),
        QAItem(
            question="What clue solves the mystery?",
            answer=f"They follow {case['clue']} and discover that {case['solution']}.",
        ),
        QAItem(
            question=f"Who was responsible for moving the {p.object_name}?",
            answer=f"{p.animal} moved it, but not to cause trouble; the object was carried for a safe reason.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why can a wagging tail be misunderstood?",
            answer="A wagging tail can show excitement, but it does not prove that an animal took something.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of waiting and wondering what will happen next.",
        ),
        QAItem(
            question="Why are physical clues useful in a mystery?",
            answer="Physical clues such as footprints, threads, or sounds can connect a missing object to its real hiding place.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 3) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 3) for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id} ({entity.kind}) meters={meters} memes={memes}")
    lines.append(f"  facts={{resolved: {world.facts.get('resolved')}, clue: {world.facts.get('clue')!r}, culprit: {world.facts.get('culprit')!r}}}")
    return "\n".join(lines)


ASP_RULES = r"""
% A valid whodunit has an important object, a misleading wag, a physical clue,
% and a resolution that distinguishes misunderstanding from responsibility.
valid_case(Object) :-
    significant(Object),
    wag_clue(Object),
    physical_clue(Object),
    resolved(Object).

suspense(Object) :-
    missing(Object),
    misunderstanding(Object).

resolved(Object) :-
    carried_safely(Object).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for case in CASES:
        obj = case["object"].replace(" ", "_")
        lines.extend([
            asp.fact("significant", obj),
            asp.fact("wag_clue", obj),
            asp.fact("physical_clue", obj),
            asp.fact("missing", obj),
            asp.fact("misunderstanding", obj),
            asp.fact("carried_safely", obj),
        ])
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show valid_case/1. #show suspense/1."))
    valid = {row[0] for row in asp.atoms(model, "valid_case")}
    suspense = {row[0] for row in asp.atoms(model, "suspense")}
    expected = {case["object"].replace(" ", "_") for case in CASES}
    if valid != expected or suspense != expected:
        print("MISMATCH between ASP and Python registry parity")
        print("  valid:", sorted(valid))
        print("  suspense:", sorted(suspense))
        print("  expected:", sorted(expected))
        return 1
    for index, case in enumerate(CASES):
        sample = generate(StoryParams(
            name=NAME_POOL[index % len(NAME_POOL)],
            helper="Soo",
            place=PLACES[index % len(PLACES)],
            animal=ANIMALS[index % len(ANIMALS)],
            object_name=case["object"],
            seed=100 + index,
        ))
        if not sample.world or not sample.world.facts.get("resolved"):
            print("Generated story failed resolution check")
            return 1
    print(f"OK: ASP/Python parity matches ({len(expected)} whodunits); generated stories resolve.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A suspenseful whodunit storyworld.")
    parser.add_argument("--name", choices=NAME_POOL)
    parser.add_argument("--helper", choices=HELPER_POOL)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
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
        name=args.name or rng.choice(NAME_POOL),
        helper=args.helper or rng.choice(HELPER_POOL),
        place=args.place or rng.choice(PLACES),
        animal=args.animal or rng.choice(ANIMALS),
        object_name=args.object_name or rng.choice(OBJECTS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program("#show valid_case/1. #show suspense/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as err:
            raise SystemExit(f"ASP unavailable: {err}")
        model = asp.one_model(asp_program("#show valid_case/1. #show suspense/1."))
        print(json.dumps({
            "valid_case": sorted(asp.atoms(model, "valid_case")),
            "suspense": sorted(asp.atoms(model, "suspense")),
        }, indent=2))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, case in enumerate(CASES):
            params = StoryParams(
                name=NAME_POOL[index % len(NAME_POOL)],
                helper="Soo",
                place=PLACES[index % len(PLACES)],
                animal=ANIMALS[index % len(ANIMALS)],
                object_name=case["object"],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < max(0, args.n) and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
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
