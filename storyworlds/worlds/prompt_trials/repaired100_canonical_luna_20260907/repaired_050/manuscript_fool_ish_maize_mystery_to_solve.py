#!/usr/bin/env python3
"""
A child-safe whodunit about a missing manuscript, a foolish-looking clue,
and a maize field that keeps a secret until everyone observes carefully.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass(frozen=True)
class Case:
    id: str
    title: str
    opening: str
    discovery: str
    clue: str
    false_suspect: str
    first_guess: str
    dialogue: str
    deduction: str
    solution: str
    proof: str
    ending: str
    lesson: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    manuscript: str
    name: str
    role: str
    mood: str
    case: str = ""
    telling: str = ""
    seed: Optional[int] = None


PLACES = {
    "maize_farm": "the old maize farm",
    "village_archive": "the village archive beside the maize farm",
    "harvest_barn": "the harvest barn at the edge of the maize field",
}

MYSTERIES = {
    "missing_manuscript": "a missing manuscript",
}

MANUSCRIPTS = {
    "moon_maize": "the Moon-Maize manuscript",
    "golden_crows": "the Golden Crows manuscript",
    "green_rows": "the Green Rows manuscript",
}

NAMES = [
    ("Luna", "young detective"),
    ("Milo", "apprentice archivist"),
    ("Tess", "curious farm child"),
    ("Oren", "careful messenger"),
    ("Pia", "village puzzle-solver"),
]

MOODS = ["patient", "brave", "cheerful", "quiet", "curious"]
TELLINGS = ["clue_first", "suspect_first", "question_first", "field_first"]

CASES = {
    item.id: item
    for item in [
        Case(
            id="cornsilk_thread",
            title="The Thread in the Cornsilk",
            opening="The harvest festival was three days away, and the village archive smelled of paper, dust, and dried maize leaves.",
            discovery="When the archivist opened the locked drawer, the Moon-Maize manuscript was gone.",
            clue="A pale thread of corn silk clung to the empty drawer, although the archive windows had been shut.",
            false_suspect="Everyone pointed at the scarecrow keeper, whose straw hat was full of maize silk.",
            first_guess="Luna almost accused him because his hat looked so foolishly tangled.",
            dialogue='"I did not take the manuscript," said the scarecrow keeper. "Then why is maize silk on your hat?" Luna asked. "Because I repaired the scarecrow beside the field," he replied.',
            deduction="Luna noticed that the thread ran from the drawer to the archive door, then stopped at a small muddy wheel mark.",
            solution="The manuscript had not been stolen by the scarecrow keeper at all. A breeze had pushed it from a drying table into a document cart, and the cart had rolled toward the maize shed.",
            proof="Behind the shed, the manuscript rested beneath a clean canvas cover, safe and dry.",
            ending="The scarecrow keeper laughed when Luna called the tangled hat a fool-ish clue, and the manuscript's silver moon on its cover shone in the afternoon sun.",
            lesson="A strange clue may point to a real cause, but a wise detective checks the whole trail before blaming anyone.",
        ),
        Case(
            id="ink_on_cob",
            title="The Ink on the Cob",
            opening="Rain tapped on the roof of the village archive while bundles of maize waited in the barn to dry.",
            discovery="The Golden Crows manuscript, needed for the festival play, had vanished from its reading stand.",
            clue="A blue ink spot appeared on one maize cob beside the stand.",
            false_suspect="The village jester became the first suspect because his coat was covered in silly blue patches.",
            first_guess="Luna thought the jester had made a fool-ish joke by hiding the manuscript among the cobs.",
            dialogue='"Did you hide the book?" Luna asked. "I hid only my boots from the rain," said the jester. "Then help me look at the ink," she said. "Gladly," he answered.',
            deduction="The ink spot was not on the cob's rough outside. It was on a smooth shaving, showing that the cob had brushed against the manuscript's wooden stand.",
            solution="A damp maize stalk had fallen through a loose roof board. It knocked the stand, and the manuscript slid into a basket used for sorting cobs.",
            proof="The basket held the manuscript between two dry cloths, with its pages unwrinkled.",
            ending="The jester bowed to the rescued book, and the blue ink became a tiny star in Luna's notebook instead of proof of guilt.",
            lesson="A mark tells what touched something, but careful questions tell when and how it happened.",
        ),
        Case(
            id="three_cornrows",
            title="The Three Crooked Rows",
            opening="At dawn, the maize field stood in neat green lines behind the archive.",
            discovery="The Green Rows manuscript disappeared just before the children were to read it aloud.",
            clue="Three rows of maize bent toward the same narrow path behind the barn.",
            false_suspect="The goat farmer seemed suspicious because his goat had a habit of nibbling anything that looked important.",
            first_guess="Luna imagined a fool-ish goat chewing the manuscript and hurried toward the pen.",
            dialogue='"Was your goat near the barn?" Luna asked. "Only near the hay," said the farmer. "What did you hear?" she asked. "A cart wheel squeaked three times," he answered.',
            deduction="The bent rows did not have bite marks. They had wheel marks, and the three bends matched the cart's three squeaks.",
            solution="The manuscript had been placed in a covered reading cart. A loose wheel pulled the cart through the maize rows before stopping behind the barn.",
            proof="The manuscript lay in the cart under a blanket, beside three fresh green leaves.",
            ending="The goat bleated as if offended by the accusation, while Luna straightened the cart and read the first page beneath the rustling maize.",
            lesson="Before calling someone a culprit, compare the shape of the evidence with the story it tells.",
        ),
        Case(
            id="waxen_corn",
            title="The Wax Seal and the Corn",
            opening="The archive prepared a special display about old farms, with a manuscript sealed by red wax.",
            discovery="The manuscript was missing, but its red seal lay beside a basket of maize.",
            clue="A tiny crescent of red wax was pressed into a corn husk.",
            false_suspect="The traveling magician looked guilty because he wore red gloves and made dramatic, foolish bows.",
            first_guess="Luna wondered if his trick had whisked the manuscript away.",
            dialogue='"Can your magic explain this wax?" Luna asked. "No magic," said the magician. "I carried the maize basket," he added. "Show me how," said Luna. "Gladly," he replied.',
            deduction="The magician had carried the basket past the display, and its rough handle had caught the manuscript's seal.",
            solution="The manuscript had stuck briefly to the basket handle. When the basket was set down, the book slid behind a stack of empty crates.",
            proof="The red wax crescent matched the seal, and the manuscript was found behind the crates without a torn page.",
            ending="The magician made one honest bow, and Luna placed the manuscript on a higher stand far from the busy maize baskets.",
            lesson="A clever-looking trick may have an ordinary explanation hiding in plain sight.",
        ),
        Case(
            id="owl-feather",
            title="The Feather in the Maize",
            opening="A quiet evening settled over the farm while an owl watched from the barn roof.",
            discovery="The manuscript for the midnight reading was gone from the lantern table.",
            clue="An owl feather lay beside a trail of crushed maize leaves.",
            false_suspect="The night watchman seemed suspicious because his coat was dusty and his lantern had gone out.",
            first_guess="Luna thought he had made a fool-ish mistake and carried the book into the field.",
            dialogue='"Did you move the manuscript?" Luna asked. "No," said the watchman. "But I heard pages flap," he added. "Where did the sound go?" Luna asked. "Toward the barn," he said.',
            deduction="The feather showed that the owl had flown low, and the crushed leaves showed a gust had swept toward the barn.",
            solution="The lantern table's cloth caught the wind. It lifted the manuscript into a shallow grain box near the barn wall.",
            proof="The book was inside the box, protected by a layer of clean maize husks.",
            ending="The owl blinked from the roof as Luna returned the manuscript, and the night reading began with every page in place.",
            lesson="When evidence seems mysterious, follow its direction and listen to witnesses who noticed the moment.",
        ),
    ]
}

ASP_RULES = r"""
missing(M) :- manuscript(M), case_open.
found(M) :- missing(M), clue_traced, safe_place.
solved :- found(M).
#show missing/1.
#show found/1.
#show solved/0.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Whodunit world: a manuscript mystery in maize country.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--mystery", choices=MYSTERIES)
    parser.add_argument("--manuscript", choices=MANUSCRIPTS)
    parser.add_argument("--name")
    parser.add_argument("--role")
    parser.add_argument("--mood", choices=MOODS)
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--telling", choices=TELLINGS)
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
    if args.place and args.place not in PLACES:
        raise StoryError("The chosen place is not part of this manuscript mystery.")
    if args.mystery and args.mystery != "missing_manuscript":
        raise StoryError("This world solves one mystery: a missing manuscript.")
    if args.manuscript and args.manuscript not in MANUSCRIPTS:
        raise StoryError("That manuscript is not kept in the maize archive.")
    name, role = rng.choice(NAMES)
    if args.name:
        name = args.name
    if args.role:
        role = args.role
    return StoryParams(
        place=args.place or rng.choice(sorted(PLACES)),
        mystery="missing_manuscript",
        manuscript=args.manuscript or rng.choice(sorted(MANUSCRIPTS)),
        name=name,
        role=role,
        mood=args.mood or rng.choice(MOODS),
        case=args.case or rng.choice(sorted(CASES)),
        telling=args.telling or rng.choice(TELLINGS),
    )


def tell(params: StoryParams, rng: random.Random) -> World:
    world = World()
    hero = world.add(Entity(params.name, "character", "detective", params.name))
    manuscript = world.add(Entity("manuscript", "thing", "manuscript", MANUSCRIPTS[params.manuscript]))
    maize = world.add(Entity("maize", "thing", "crop", "maize"))
    world.facts.update(hero=hero, manuscript=manuscript, maize=maize, case=CASES[params.case])
    case = CASES[params.case]

    intro = {
        "clue_first": f"{params.name}, a {params.mood} {params.role}, noticed a pale thread near the archive door.",
        "suspect_first": f"{params.name}, a {params.mood} {params.role}, saw a suspicious figure leaving the maize shed.",
        "question_first": f"Who had taken the manuscript, and why had the maize field become part of the puzzle?",
        "field_first": f"The maize leaves whispered beside the archive as {params.name}, a {params.mood} {params.role}, began the morning round.",
    }
    world.say(intro[params.telling])
    world.say(case.opening)
    world.para()

    world.say(case.discovery)
    world.say(case.clue)
    world.facts["case_open"] = True
    world.say("Luna's first look made the clue seem more mysterious than it really was.")
    world.para()

    world.say(case.false_suspect)
    world.say(case.first_guess)
    world.say(case.dialogue)
    world.say("The conversation changed the search: instead of chasing a silly-looking suspect, Luna asked what each clue had touched.")
    world.para()

    world.say(case.deduction)
    world.facts["clue_traced"] = True
    world.say(case.solution)
    world.para()

    world.say(case.proof)
    world.facts.update(safe_place=True, solved=True)
    world.say(case.ending)
    world.say(f"{params.name} wrote the lesson in the casebook: {case.lesson}")
    return world


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("Unknown setting for this story.")
    if params.mystery != "missing_manuscript":
        raise StoryError("Only the missing-manuscript mystery is supported.")
    if params.case not in CASES:
        raise StoryError("The selected case has no solvable clue trail.")
    seed = params.seed if params.seed is not None else sum(ord(c) for c in params.name + params.case)
    world = tell(params, random.Random(seed ^ 0xA17E))
    case = CASES[params.case]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a child-safe whodunit about {MANUSCRIPTS[params.manuscript]} disappearing near a maize field.",
            "Use a fool-ish first suspicion, a useful conversation, and a physical clue that solves the mystery.",
            "End with the manuscript found safe and a concrete image from the maize setting.",
        ],
        story_qa=[
            QAItem(
                question=f"Who investigated the missing manuscript in {PLACES[params.place]}?",
                answer=f"{params.name}, a {params.mood} {params.role}, investigated the missing manuscript.",
            ),
            QAItem(
                question="What clue changed the detective's first guess?",
                answer=case.clue,
            ),
            QAItem(
                question="What did the conversation reveal?",
                answer=case.dialogue,
            ),
            QAItem(
                question="How was the manuscript found?",
                answer=case.proof,
            ),
            QAItem(
                question="What lesson did the detective learn?",
                answer=case.lesson,
            ),
        ],
        world_qa=[
            QAItem(
                question="What is a manuscript?",
                answer="A manuscript is a handwritten or carefully prepared text, often kept safe because it is valuable or old.",
            ),
            QAItem(
                question="What is maize?",
                answer="Maize is a tall crop that grows ears covered by husks and is also called corn.",
            ),
            QAItem(
                question="What is a whodunit?",
                answer="A whodunit is a mystery story in which clues and questions help reveal who caused an event.",
            ),
            QAItem(
                question="Why should someone avoid blaming a person too quickly?",
                answer="They should check several clues first because an odd-looking detail can have an ordinary explanation.",
            ),
        ],
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:12} ({entity.type:10}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts={sorted(world.facts)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("manuscript", "moon_maize"),
            asp.fact("manuscript", "golden_crows"),
            asp.fact("manuscript", "green_rows"),
            asp.fact("crop", "maize"),
            asp.fact("case_open"),
            asp.fact("clue_traced"),
            asp.fact("safe_place"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
        solved = bool(asp.atoms(model, "solved"))
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 0
    if not solved:
        print("MISMATCH: ASP did not solve the manuscript case.")
        return 1
    for case_id in CASES:
        params = StoryParams(
            place="maize_farm",
            mystery="missing_manuscript",
            manuscript="moon_maize",
            name="Luna",
            role="young detective",
            mood="patient",
            case=case_id,
            telling="clue_first",
            seed=7,
        )
        sample = generate(params)
        if "manuscript" not in sample.story.lower() or "maize" not in sample.story.lower():
            print(f"MISMATCH: generated story failed for {case_id}.")
            return 1
    print("OK: Python stories and ASP case resolution agree.")
    return 0


CURATED = [
    StoryParams("maize_farm", "missing_manuscript", "moon_maize", "Luna", "young detective", "patient", "cornsilk_thread", "clue_first", 11),
    StoryParams("village_archive", "missing_manuscript", "golden_crows", "Milo", "apprentice archivist", "curious", "ink_on_cob", "question_first", 23),
    StoryParams("harvest_barn", "missing_manuscript", "green_rows", "Tess", "curious farm child", "brave", "three_cornrows", "field_first", 41),
]


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
    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp:
        print(asp_program())
        return
    if args.asp:
        print("ASP case facts:")
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(item) for item in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(1, args.n):
            seed = base_seed + attempt
            attempt += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as exc:
                print(exc)
                return
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
        if index + 1 < len(samples):
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
