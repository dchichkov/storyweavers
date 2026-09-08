#!/usr/bin/env python3
"""
A child-facing whodunit about a formula, a sham clue, and a careful twist.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    object_word: str


@dataclass
class StoryParams:
    place: str
    detective: str
    helper: str
    formula_name: str
    object_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    object: str
    owner: str
    sham: str
    clue: str
    test: str
    cause: str
    twist: str
    repair: str
    lesson: str
    ending: str


CASES = [
    Case(
        "a blue bottle",
        "the baker",
        "a paper saying SECRET FORMULA",
        "a sticky ring beside the empty measuring cup",
        "mixed plain water with a spoonful of flour and compared the smell",
        "the baker had moved the real syrup to a cool cupboard and left the empty bottle near the recipe shelf",
        "the frightening secret was only a sham label made to keep a curious puppy away",
        "returned the syrup and wrote the true ingredients in large letters",
        "A mysterious label is not proof; kind testing can uncover the truth.",
        "warm buns rose while the real recipe rested safely on the shelf",
    ),
    Case(
        "a silver tin",
        "the gardener",
        "a black wax seal stamped with a crooked star",
        "green dust beneath the tin's loose lid",
        "brushed the dust onto a white card and followed its trail",
        "the tin held ordinary seeds, while the star seal had come from a costume box",
        "the supposed secret formula was a sham planted by a playful actor",
        "put the seeds in labeled packets and returned the seal to the costume box",
        "A strange mark may tell where an object came from, not who did wrong.",
        "tiny sprouts appeared in neat rows beneath honest labels",
    ),
    Case(
        "a glass jar",
        "the museum keeper",
        "a red note warning DO NOT OPEN",
        "two dry crumbs under the jar and a clean circle in the dust",
        "placed the jar inside its circle and checked which shelf shadow matched",
        "the keeper had moved the jar during cleaning and forgotten to replace the note",
        "the scary warning was a sham left from yesterday's pretend dragon exhibit",
        "washed the jar, removed the old note, and added a real cleaning card",
        "A good detective separates pretend danger from real danger.",
        "the dragon exhibit gleamed while the jar stood safely behind its label",
    ),
    Case(
        "a copper bowl",
        "the soup maker",
        "a chalk formula filled with impossible numbers",
        "one chalk line continued onto the floor beneath the bowl",
        "copied the line onto a clean board and checked its path",
        "the bowl had rolled over the old chalk writing and made the formula look changed",
        "the impossible formula was a sham drawing from a game",
        "erased the game marks and placed the bowl on a rubber mat",
        "A neat test can untangle a confusing picture.",
        "the soup maker stirred a steady pot while the bowl stayed still",
    ),
    Case(
        "a green packet",
        "the librarian",
        "a gold ribbon tied like a warning",
        "a matching ribbon fiber caught on the lowest book cart wheel",
        "rolled the cart along the floor and watched the ribbon tug",
        "the cart had brushed the packet and pulled its ribbon loose",
        "the secret formula was a sham cover for a bookmark-making kit",
        "moved the packet to a drawer and repaired the cart wheel",
        "Following a physical clue is fairer than guessing at a culprit.",
        "bright bookmarks waved from the drawer beside the quiet cart",
    ),
    Case(
        "a wooden box",
        "the clockmaker",
        "a silver card claiming the box held a vanished jewel",
        "fine sawdust formed a trail from the workbench to the box",
        "matched the sawdust to the clockmaker's fresh wooden gears",
        "the clockmaker had stored harmless gear pieces inside the box",
        "the jewel story was a sham written for a treasure hunt",
        "labeled the gears and placed the treasure-hunt card in its game basket",
        "A playful story can look like a mystery until evidence gives it its size.",
        "a little clock ticked beside the box and nobody needed to whisper",
    ),
]

OPENINGS = [
    "The mystery began when a familiar shelf looked strangely secret.",
    "Rain tapped the window as the young detective noticed one object out of place.",
    "The room was peaceful until a formula appeared where no formula belonged.",
    "At first, the case seemed to involve a missing treasure.",
    "A hush fell over the workroom when someone cried, 'Look at this!'",
]

DIALOGUE = [
    ('"That warning proves someone is hiding something," the helper said.',
     '"It proves only that someone wrote a warning," the detective replied.'),
    ('"Should we tell everyone who did it?" asked the helper.',
     '"Not until one test agrees with the clue," said the detective.'),
    ('"The formula looks frightening," whispered the helper.',
     '"Numbers can be dressed up like a sham," the detective answered.'),
    ('"I saw the object first," said the helper. "That makes me sure."',
     '"Seeing first is not the same as knowing first," said the detective.'),
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, ...]] = set()
        self.facts: dict[str, object] = {}

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def investigate(world: World, case: Case) -> None:
    detective = world.entities["detective"]
    helper = world.entities["helper"]
    detective.memes["curiosity"] = 1
    helper.memes["suspense"] = 1
    world.fired.add(("clue_found",))
    world.facts["clue"] = case.clue


def resolve(world: World) -> None:
    detective = world.entities["detective"]
    helper = world.entities["helper"]
    detective.memes["relief"] = 1
    detective.memes["pride"] = 1
    helper.memes["suspense"] = 0
    world.fired.add(("case_solved",))


def tell(world: World, params: StoryParams) -> World:
    seed = params.seed
    if seed is None:
        seed = sum((i + 1) * ord(c) for i, c in enumerate(
            f"{params.place}|{params.detective}|{params.helper}|{params.formula_name}|{params.object_name}"
        ))
    rng = random.Random(seed ^ 0xB048)
    case = rng.choice(CASES)
    opening = rng.choice(OPENINGS)
    dialogue = rng.choice(DIALOGUE)

    detective = world.add(Entity("detective", "character", "child", params.detective))
    helper = world.add(Entity("helper", "character", "child", params.helper))
    formula = world.add(Entity("formula", "thing", "formula", params.formula_name))
    object_ent = world.add(Entity("object", "thing", "object", params.object_name, owner=case.owner))
    formula.meters["truth"] = 0
    object_ent.meters["present"] = 1
    helper.memes["suspense"] = 1

    world.say(opening)
    world.say(f"{params.detective} was the young detective of {params.place}, and {params.helper} helped keep the clue cards in order.")
    world.say(f"On the center table sat {params.object_name}, beside a formula called {params.formula_name}.")
    world.para()
    world.say(f"The trouble began when they saw {case.sham}.")
    world.say(f"The label made the harmless object seem dangerous, and suspense tightened around the room.")
    world.say(dialogue[0])
    world.say(dialogue[1])

    investigate(world, case)
    world.para()
    world.say(f"Then {params.detective} noticed the real clue: {case.clue}.")
    world.say(f"To test it, they {case.test}.")
    world.say(f"The result brought a twist. {case.cause.capitalize()}.")
    world.say(f"The frightening formula was a sham after all: {case.twist}.")
    formula.meters["truth"] = 1

    resolve(world)
    world.para()
    world.say(f"Together they {case.repair}.")
    world.say(f"{params.detective} smiled and said, \"{case.lesson}\"")
    world.say(f"At last, {case.ending}.")
    world.facts.update(
        case=case,
        detective=detective,
        helper=helper,
        formula=formula,
        object=object_ent,
        place=params.place,
        owner=case.owner,
    )
    return world


PLACES = {
    "bakehouse": Setting("the bakehouse", "shelf"),
    "garden shed": Setting("the garden shed", "shelf"),
    "museum room": Setting("the museum room", "case"),
    "workroom": Setting("the workroom", "table"),
    "library corner": Setting("the library corner", "cart"),
}

DETECTIVES = ["Luna", "Mara", "Nico", "Ivy", "Theo", "Pia"]
HELPERS = ["Pip", "Sol", "Milo", "June", "Tess", "Ari"]
FORMULAS = ["the bright formula", "the garden formula", "the supper formula", "the clock formula"]
OBJECTS = ["blue bottle", "silver tin", "glass jar", "copper bowl", "green packet", "wooden box"]


ASP_RULES = r"""
truthful_formula(F) :- formula(F), marked_truth(F).
safe_object(O) :- object(O), present(O), tested(O).
solved(C) :- truthful_formula(F), safe_object(O), clue(C), tested(C).

#show truthful_formula/1.
#show safe_object/1.
#show solved/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("formula", "formula"),
        asp.fact("marked_truth", "formula"),
        asp.fact("object", "object"),
        asp.fact("present", "object"),
        asp.fact("tested", "formula"),
        asp.fact("tested", "object"),
        asp.fact("clue", "case"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A formula-and-sham whodunit storyworld.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--detective")
    parser.add_argument("--helper")
    parser.add_argument("--formula-name")
    parser.add_argument("--object-name")
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
    return StoryParams(
        place=args.place or rng.choice(sorted(PLACES)),
        detective=args.detective or rng.choice(DETECTIVES),
        helper=args.helper or rng.choice(HELPERS),
        formula_name=args.formula_name or rng.choice(FORMULAS),
        object_name=args.object_name or rng.choice(OBJECTS),
    )


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    return [
        'Write a child-friendly whodunit containing the words "formula" and "sham".',
        f"Tell how {world.facts['detective'].label} tests a suspicious formula in {world.facts['place']}.",
        f"Build suspense around {case.sham}, then reveal the twist using {case.clue}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]
    detective: Entity = world.facts["detective"]
    helper: Entity = world.facts["helper"]
    return [
        QAItem(
            "Who investigated the suspicious formula?",
            f"{detective.label} investigated it with help from {helper.label}.",
        ),
        QAItem(
            "What made the case seem frightening at first?",
            f"The case seemed frightening because {case.sham}.",
        ),
        QAItem(
            "What clue changed the investigation?",
            f"They noticed that {case.clue}.",
        ),
        QAItem(
            "What was the twist?",
            f"The twist was that {case.twist}.",
        ),
        QAItem(
            "How was the mystery resolved?",
            f"They tested the clue, learned that {case.cause}, and then {case.repair}.",
        ),
        QAItem(
            "What lesson did the detective learn?",
            case.lesson,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a formula?", "A formula is a set of signs or instructions used to describe how something works or is made."),
        QAItem("What is a sham?", "A sham is something that looks real or important but is actually false or pretend."),
        QAItem("What does a detective do?", "A detective studies clues, asks careful questions, and tests ideas before deciding what happened."),
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
        lines.append(
            f"{entity.id}: kind={entity.kind} type={entity.type} "
            f"meters={dict(entity.meters)} memes={dict(entity.memes)}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if not params.detective.strip() or not params.helper.strip():
        raise StoryError("Detective and helper names must not be empty.")
    world = World(PLACES[params.place])
    tell(world, params)
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


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show truthful_formula/1.\n#show safe_object/1.\n#show solved/1."))
    truthful = set(asp.atoms(model, "truthful_formula"))
    safe = set(asp.atoms(model, "safe_object"))
    solved = set(asp.atoms(model, "solved"))
    if truthful == {("formula",)} and safe == {("object",)} and solved == {("case",)}:
        sample = generate(StoryParams("workroom", "Luna", "Pip", "the bright formula", "wooden box", 7))
        if "sham" in sample.story and "formula" in sample.story and sample.world.fired:
            print("OK: ASP/Python parity and generated-story checks passed.")
            return 0
    print("MISMATCH: ASP/Python parity or story checks failed.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show truthful_formula/1.\n#show safe_object/1.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show truthful_formula/1.\n#show safe_object/1.\n#show solved/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("bakehouse", "Luna", "Pip", "the bright formula", "blue bottle", base_seed),
            StoryParams("museum room", "Mara", "Sol", "the garden formula", "glass jar", base_seed + 1),
            StoryParams("workroom", "Theo", "June", "the clock formula", "wooden box", base_seed + 2),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 0)):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)

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
