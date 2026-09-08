#!/usr/bin/env python3
"""
A gentle grocery-store ghost story about an insult, a triangle clue, and tuna.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


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
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    ghost_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    title: str
    occasion: str
    insult: str
    problem: str
    first_guess: str
    clue: str
    action: str
    truth: str
    repair: str
    lesson: str
    ending: str


NAMES = {
    "girl": ["Luna", "Maya", "Nina", "Ivy", "Zuri"],
    "boy": ["Owen", "Theo", "Eli", "Noah", "Jace"],
}
HELPERS = ["mother", "father", "grandmother", "grandfather", "aunt", "uncle"]
GHOST_NAMES = ["Moss", "Pip", "Bells", "Milo", "Rue"]

INCIDENTS = [
    Incident(
        "triangle shelf",
        "the grocery store was preparing a tasting table for families",
        "a rude voice had called the tuna cans 'stupid little fish boxes'",
        "a triangle-shaped sign had vanished from the tuna display",
        "that someone had thrown it away after hearing the insult",
        "three silver tuna cans stood in a neat triangle beside a cart with blue tape on its wheel",
        "followed the triangle pattern without touching the food and asked the store clerk for help",
        "the sign had slipped behind the cart when the wheel bumped the display",
        "retrieved the sign, apologized for the unkind words, and rebuilt the display safely",
        "curiosity can uncover the truth, but kind words help repair hurt feelings",
        "the tuna cans gleamed beneath the restored triangle sign while the ghost gave a shy wave",
    ),
    Incident(
        "cold aisle triangle",
        "shoppers were collecting groceries before a storm",
        "a customer had insulted the freezer by calling it a useless noisy box",
        "the tuna salad samples were warming because the small cooler had stopped humming",
        "that the ghost had made the cooler quiet as a prank",
        "a paper triangle on the floor pointed from the cooler to an unplugged cord",
        "asked the manager to check the cord and kept everyone from tasting the warm samples",
        "a stocking cart had tugged the plug loose from the wall",
        "moved the cart, plugged in the cooler with the manager, and replaced the samples",
        "curiosity should lead to safe questions, not risky guesses",
        "cold sample cups waited under a bright triangle card as the storm tapped the windows",
    ),
    Incident(
        "tuna label",
        "the grocery store was making a clear display for shoppers with allergies",
        "someone had insulted a careful label as 'silly scribbling'",
        "the tuna cans and their ingredient card no longer matched",
        "that the ghost had mixed them up to confuse the shoppers",
        "noticed a triangle mark on the card and compared it with the store's shelf map",
        "the card belonged to a different tuna recipe and had been placed on the wrong shelf",
        "returned the card, printed a large new label, and asked the clerk to check every can",
        "curiosity is strongest when it protects people and checks details",
        "fresh labels stood in a triangle above the tuna shelf, easy for every shopper to read",
    ),
    Incident(
        "the missing basket",
        "the store was gathering canned food for a neighborhood pantry",
        "a voice had insulted the donation basket by calling it an empty little joke",
        "the basket for tuna donations had disappeared",
        "that a shopper had taken it because the insult made the basket seem unwanted",
        "looked for a triangle of floor stickers and asked the pantry volunteer what had moved",
        "the basket had been carried to the loading door with the first pantry boxes",
        "brought it back, filled it with tuna, and thanked the volunteer for organizing the food",
        "curiosity can reveal a simple reason before blame begins",
        "the full basket rested beneath a triangle of paper stars by the pantry table",
    ),
    Incident(
        "ghostly checkout",
        "Luna and her helper were paying for groceries at the end of a busy afternoon",
        "a tired shopper had insulted the slow checkout line",
        "the tuna can on the counter kept rolling into a triangle-shaped candy display",
        "that the friendly ghost was nudging it for fun",
        "watched the floor, found a tiny raised tile, and told the cashier instead of grabbing the can",
        "the tile was loose and made the counter slope toward the display",
        "the cashier moved the can, marked the tile, and called the repair worker",
        "curiosity means noticing small causes while treating people gently",
        "the repaired counter held a tuna can still while the ghost smiled at the patient line",
    ),
    Incident(
        "three-cornered clue",
        "the store was decorating for a quiet evening sale",
        "a passerby had insulted the ghost's soft voice as a silly squeak",
        "the ghost would only point at three corners near the tuna aisle",
        "that the ghost was upset and wanted everyone to leave",
        "checked each corner with the helper and listened for a change in the store's hum",
        "a fallen sign had covered the emergency call button at the third corner",
        "asked the manager to move the sign and made sure the button was visible again",
        "curiosity can turn a strange signal into useful care",
        "the three corners shone cleanly while the tuna aisle became calm and bright",
    ),
]


@dataclass(frozen=True)
class StoryChoice:
    opening: str
    thought: str
    question: str


OPENINGS = [
    "A gentle grocery-store mystery began when",
    "The evening shoppers were choosing groceries when",
    "A soft blue glow appeared beside the shelves just as",
    "The store was nearly quiet when",
    "Luna was comparing labels with her helper when",
]

CHOICES = [
    StoryChoice(
        "Luna did not want to repeat the insult, because unkind words could hurt someone",
        "Curiosity made her look closely instead of rushing to a conclusion",
        '"What changed near the triangle?" Luna asked.',
    ),
    StoryChoice(
        "Luna felt worried, but she knew a question could be kinder than an accusation",
        "Her curiosity helped her notice a pattern that other shoppers had missed",
        '"Can we check the clue safely?" Luna asked.',
    ),
    StoryChoice(
        "Luna remembered that a strange event could have an ordinary cause",
        "Curiosity gave her patience enough to compare what she saw",
        '"Which detail should we test first?" Luna asked.',
    ),
]


def tell_story(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    incident = rng.choice(INCIDENTS)
    opening = rng.choice(OPENINGS)
    choice = rng.choice(CHOICES)

    world = World(place="the neighborhood grocery store")
    child = world.add(Entity(params.name, "character", params.gender))
    helper = world.add(Entity(params.helper.capitalize(), "character", params.helper))
    ghost = world.add(Entity(params.ghost_name, "character", "ghost"))
    tuna = world.add(Entity("tuna", type="food", label="cans of tuna"))
    triangle = world.add(Entity("triangle", type="clue", label="triangle clue"))
    curiosity = world.add(Entity("curiosity", type="feeling"))

    world.say(
        f"{opening} {incident.occasion}. {child.id} and {helper.id} were walking through "
        f"{world.place} when {ghost.id}, a small friendly ghost, floated beside the tuna shelf."
    )
    world.say(
        f"Someone had spoken an insult: {incident.insult}. The words were unkind, but "
        f"{child.id} chose not to repeat them loudly."
    )
    world.say(f"Then they discovered that {incident.problem}.")
    world.say(
        f"{ghost.id} pointed to a triangle and whispered, \"Tuna, triangle, look again.\""
    )

    world.para()
    world.say(
        f"At first, {child.id} guessed {incident.first_guess}. {helper.id} reminded "
        f"{child.id} that it was only a guess, so nobody should be blamed."
    )
    child.memes["curiosity"] = 1.0
    world.say(f"{choice.opening}. {choice.thought}.")
    world.say(f'{choice.question} "{incident.insult.capitalize()} does not tell us what really happened."')
    world.say(
        f"{helper.id} answered, \"Good thinking. We can look carefully and ask for help.\" "
        f"{ghost.id} pointed to the triangle again."
    )

    world.para()
    world.say(
        f"With {helper.id} beside {child.id}, they {incident.action}. The pattern led to "
        f"the truth: {incident.truth}."
    )
    world.say(
        f'"Now I understand the clue," {child.id} said. "{incident.insult.capitalize()} was not evidence."'
    )
    world.say(f"Together, they {incident.repair}.")

    world.para()
    child.memes["curiosity"] = 0.0
    child.memes["understanding"] = 1.0
    ghost.memes["relieved"] = 1.0
    tuna.meters["safe"] = 1.0
    triangle.meters["explained"] = 1.0
    world.say(
        f"{incident.lesson.capitalize()}. {ghost.id} thanked {child.id} and {helper.id} "
        f"with a little bow."
    )
    world.say(
        f"At the end of the shopping trip, {incident.ending}. "
        f"The store felt peaceful again."
    )

    world.facts.update(
        child=child,
        helper=helper,
        ghost=ghost,
        tuna=tuna,
        triangle=triangle,
        curiosity=curiosity,
        incident=incident,
        place=world.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    incident: Incident = world.facts["incident"]
    child: Entity = world.facts["child"]
    return [
        f"Write a gentle grocery-store ghost story in which {child.id} uses curiosity to solve a tuna and triangle mystery.",
        f"Tell a child-safe story about an insult, a triangle clue, tuna, and a kind repair in a grocery store.",
        f"Write a cozy ghost story where curiosity proves that {incident.insult} was not evidence.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    ghost: Entity = f["ghost"]
    incident: Incident = f["incident"]
    return [
        QAItem(
            question=f"What problem did {child.id} and {helper.id} find in the grocery store?",
            answer=f"They found that {incident.problem}.",
        ),
        QAItem(
            question=f"What clue did {ghost.id} show them?",
            answer=f"{ghost.id} showed them a triangle clue near the tuna display and asked them to look again.",
        ),
        QAItem(
            question=f"Why did {child.id} avoid blaming someone?",
            answer=f"{child.id} knew that {incident.insult} was unkind but was not evidence of what had happened.",
        ),
        QAItem(
            question="How did curiosity help solve the mystery?",
            answer=f"Curiosity led them to {incident.clue}, and then they {incident.action}.",
        ),
        QAItem(
            question="What was the real cause of the problem?",
            answer=f"The real cause was that {incident.truth}.",
        ),
        QAItem(
            question="How was the problem repaired?",
            answer=f"They {incident.repair}.",
        ),
        QAItem(
            question=f"What did {child.id} learn?",
            answer=f"{child.id} learned that {incident.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a triangle?",
            answer="A triangle is a shape with three sides and three corners.",
        ),
        QAItem(
            question="What is tuna?",
            answer="Tuna is a fish that people may buy fresh or in sealed cans.",
        ),
        QAItem(
            question="What is an insult?",
            answer="An insult is an unkind remark meant to hurt or belittle someone or something.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes someone want to learn more by noticing details and asking questions.",
        ),
        QAItem(
            question="Why should shoppers ask a store worker for help?",
            answer="A store worker can check a display, a label, or a safety concern without shoppers taking unnecessary risks.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
% The ghost's repeated clue is useful when curiosity is active.
has_triangle_clue :- triangle(triangle_clue), near(tuna, triangle_clue).
useful_question :- curiosity(child), has_triangle_clue.
% The ending is safe when the food is checked and the problem is repaired.
happy_ending :- useful_question, tuna_checked, problem_repaired.

#show has_triangle_clue/0.
#show useful_question/0.
#show happy_ending/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("triangle", "triangle_clue"),
            asp.fact("near", "tuna", "triangle_clue"),
            asp.fact("curiosity", "child"),
            asp.fact("tuna_checked"),
            asp.fact("problem_repaired"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/0."))
    if asp.atoms(model, "happy_ending"):
        print("OK: ASP reasoning confirms the curious, safe ending.")
        return 0
    print("MISMATCH: ASP reasoning did not confirm the ending.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle grocery-store ghost story about curiosity, tuna, and a triangle clue."
    )
    ap.add_argument("--name", choices=sorted({n for values in NAMES.values() for n in values}))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--ghost-name", choices=GHOST_NAMES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    inferred = next(
        (gender for gender, names in NAMES.items() if args.name in names),
        None,
    )
    gender = args.gender or inferred or rng.choice(["girl", "boy"])
    return StoryParams(
        name=args.name or rng.choice(NAMES[gender]),
        gender=gender,
        helper=args.helper or rng.choice(HELPERS),
        ghost_name=args.ghost_name or rng.choice(GHOST_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(
            f"  {entity.id:10} ({entity.type:10}) {' '.join(details)}"
        )
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
    StoryParams("Luna", "girl", "mother", "Moss", 7201),
    StoryParams("Owen", "boy", "father", "Pip", 7202),
    StoryParams("Nina", "girl", "grandmother", "Rue", 7203),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show has_triangle_clue/0. #show useful_question/0. #show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(
            asp_program(
                "#show has_triangle_clue/0. "
                "#show useful_question/0. "
                "#show happy_ending/0."
            )
        )
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
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
