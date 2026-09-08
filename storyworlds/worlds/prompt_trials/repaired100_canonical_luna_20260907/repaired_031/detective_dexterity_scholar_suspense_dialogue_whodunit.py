#!/usr/bin/env python3
"""
Standalone story world: a child detective solves a tiny library whodunit.

A scholar's silver bookmark vanishes during a dexterity demonstration. The
detective gathers clues, questions suspects, and uses a careful physical test
to reveal the harmless culprit.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    place: str
    affords: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
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


@dataclass
class StoryParams:
    place: str
    detective_name: str
    detective_gender: str
    scholar_name: str
    scholar_role: str
    missing_item: str
    suspect: str
    dexterity_challenge: str
    case_variant: int = 0
    opening_variant: int = 0
    ending_variant: int = 0
    seed: Optional[int] = None


SETTINGS = {
    "library": Setting(
        id="library",
        place="the old town library",
        affords={"quiet", "research", "dexterity_demo"},
    ),
}

ITEMS = {
    "silver_bookmark": {
        "label": "a silver bookmark",
        "material": "silver",
        "shape": "a narrow leaf",
    },
    "brass_key": {
        "label": "a brass key",
        "material": "brass",
        "shape": "a tiny sun",
    },
    "blue_lens": {
        "label": "a blue reading lens",
        "material": "glass",
        "shape": "a round moon",
    },
}

CHALLENGES = {
    "thread_the_needle": {
        "label": "thread a needle without touching the table",
        "tool": "a loop of red thread",
        "clue": "a red fiber caught on the drawer pull",
    },
    "stack_the_coins": {
        "label": "stack five coins on the edge of a card",
        "tool": "five copper coins",
        "clue": "a copper coin lay beside the atlas",
    },
    "balance_the_quill": {
        "label": "balance a quill on one fingertip",
        "tool": "a black feather",
        "clue": "a black feather rested beneath the reading stand",
    },
}

SUSPECTS = {
    "Mara": {
        "role": "the careful archivist",
        "trait": "keeps every shelf in perfect order",
        "secret": "she had moved a cart away from the window",
        "truth": "the missing object slipped into the cart's folded cloth",
    },
    "Jon": {
        "role": "the young map helper",
        "trait": "draws islands in the margins of his notebook",
        "secret": "he had been searching for a lost compass",
        "truth": "he saw the cart roll but did not notice the bookmark",
    },
    "Pia": {
        "role": "the visiting puzzle maker",
        "trait": "can solve knots with one hand",
        "secret": "she had borrowed the demonstration thread",
        "truth": "she moved the thread but never touched the missing object",
    },
}

GIRL_NAMES = ["Luna", "Mina", "Ivy", "Nora"]
BOY_NAMES = ["Dex", "Theo", "Milo", "Owen"]
SCHOLAR_NAMES = ["Dr. Vale", "Professor Reed", "Ms. Noor", "Mr. Rowan"]

OPENINGS = [
    "Rain tapped the tall windows when {detective} entered {place}.",
    "At three o'clock, the library clock gave one soft chime as {detective} arrived at {place}.",
    "The reading room was so quiet that {detective} could hear a page turn from the far desk.",
]

CASE_OPENERS = [
    "{scholar} had placed {item} beside an old atlas before beginning a dexterity lesson.",
    "{scholar} was showing visitors {item} when the lights blinked and the object disappeared.",
    "{scholar} had promised to explain why {item} belonged in the library's history case.",
]

ENDINGS = [
    "The room relaxed, and {detective} wrote the final line in the case notebook: careful hands can solve a quiet mystery.",
    "Everyone applauded softly. {detective} smiled, because the best clue had been the one that explained what happened next.",
    "The library clock chimed again, and {item} gleamed safely on the desk while the mystery became a story to remember.",
]


def valid_combo(place: str, missing_item: str, challenge: str, suspect: str) -> bool:
    return (
        place in SETTINGS
        and missing_item in ITEMS
        and challenge in CHALLENGES
        and suspect in SUSPECTS
    )


def explain_rejection(place: str, missing_item: str, challenge: str, suspect: str) -> str:
    return (
        f"No story: {place}, {missing_item}, {challenge}, and {suspect} "
        "do not form a solvable library mystery."
    )


def _pronoun(gender: str, case: str = "subject") -> str:
    if gender == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    return {"subject": "he", "object": "him", "possessive": "his"}[case]


def tell(params: StoryParams) -> World:
    if not valid_combo(params.place, params.missing_item, params.dexterity_challenge, params.suspect):
        raise StoryError(
            explain_rejection(
                params.place,
                params.missing_item,
                params.dexterity_challenge,
                params.suspect,
            )
        )

    setting = SETTINGS[params.place]
    item = ITEMS[params.missing_item]
    challenge = CHALLENGES[params.dexterity_challenge]
    suspect_data = SUSPECTS[params.suspect]

    world = World(setting)
    detective = world.add(
        Entity(
            params.detective_name,
            "detective",
            params.detective_name,
            meters={"attention": 1.0, "dexterity": 0.0},
            memes={"curiosity": 1.0},
        )
    )
    scholar = world.add(
        Entity(
            params.scholar_name,
            "scholar",
            params.scholar_name,
            meters={"knowledge": 1.0},
            memes={"worry": 1.0},
        )
    )
    suspect = world.add(
        Entity(
            params.suspect,
            "suspect",
            params.suspect,
            meters={"opportunity": 1.0},
            memes={"nervousness": 1.0},
        )
    )

    world.facts.update(
        detective=detective,
        scholar=scholar,
        suspect=suspect,
        item=item,
        challenge=challenge,
        suspect_data=suspect_data,
        missing_item=params.missing_item,
        clue=challenge["clue"],
        resolved=False,
    )

    opening = OPENINGS[params.opening_variant % len(OPENINGS)].format(
        detective=params.detective_name,
        place=setting.place,
    )
    world.say(opening)
    world.say(
        f"{params.scholar_name}, a visiting scholar, had gathered everyone around a reading table. "
        + CASE_OPENERS[params.case_variant % len(CASE_OPENERS)].format(
            scholar=params.scholar_name,
            item=item["label"],
        )
    )
    world.say(
        f"Then the bell above the door rang. When {params.scholar_name} looked back, "
        f"{item['label']} was gone."
    )

    world.para()
    world.say(
        f'"Nobody leave yet," said {params.detective_name}. '
        f'"A mystery is easier when the clues stay where they are."'
    )
    world.say(
        f'"I did not take it," said {params.suspect}, touching the edge of the table. '
        f'"I was only {suspect_data["secret"].rstrip(".")}."'
    )
    world.say(
        f'"That may be true," replied {params.detective_name}, '
        f'"but a good detective listens to what hands do as well as what mouths say."'
    )
    world.say(
        f"{params.detective_name} noticed {challenge['clue']}. "
        f"The clue did not prove guilt, but it pointed toward the rolling display cart."
    )
    detective.meters["dexterity"] += 1.0
    detective.memes["suspense"] = 1.0

    world.para()
    world.say(
        f"To test the clue, {params.detective_name} tried to {challenge['label']}. "
        f"The first attempt wobbled, but the second was steady."
    )
    world.say(
        f"The small movement made the cart's folded cloth slide. Something bright flashed beneath it."
    )
    world.say(
        f'"There!" cried {params.scholar_name}. "The {item["shape"]} was hidden in the cart."'
    )
    world.say(
        f'"So {params.suspect} took it?" asked {params.scholar_name}."
    )
    world.say(
        f'"Not exactly," said {params.detective_name}. '
        f'"The cart moved when {params.suspect} pushed it away from the window, but the object slipped into the cloth. '
        f"No one meant to steal it.""
    )
    world.say(
        f"{params.suspect} blinked. \"I remember the cart rolling,\" {params.suspect} said, "
        f"\"but I never saw the {item['label']} fall.\""
    )
    suspect.memes["nervousness"] = 0.0
    scholar.memes["worry"] = 0.0
    detective.memes["suspense"] = 0.0
    world.facts["resolved"] = True
    world.facts["method"] = (
        f"{params.detective_name} used {challenge['label']} to make the cart cloth shift and reveal the missing object."
    )

    world.para()
    world.say(
        f"{params.scholar_name} thanked {params.detective_name} and placed {item['label']} back beside the atlas."
    )
    world.say(
        f"{params.detective_name} explained that the clue showed where the object had traveled, not who had stolen it."
    )
    world.say(
        ENDINGS[params.ending_variant % len(ENDINGS)].format(
            detective=params.detective_name,
            item=item["label"],
        )
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a child-friendly whodunit with a detective, a scholar, suspense, and a fair physical clue.",
        f"Tell how the missing {f['item']['label']} is found without falsely blaming the suspect.",
        f"Use dialogue to show how {f['detective'].label} changes from suspicion to understanding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"].label
    scholar = f["scholar"].label
    suspect = f["suspect"].label
    item = f["item"]["label"]
    return [
        QAItem(
            question=f"What disappeared from {scholar}'s table?",
            answer=f"{item} disappeared from {scholar}'s reading table during the dexterity lesson.",
        ),
        QAItem(
            question=f"What clue did {detective} notice?",
            answer=f"{detective} noticed {f['clue']}, which pointed toward the rolling display cart and its folded cloth.",
        ),
        QAItem(
            question=f"How did {detective} solve the mystery?",
            answer=f"{detective} used {f['challenge']['label']} to make the cart cloth shift, revealing {item} underneath.",
        ),
        QAItem(
            question=f"Did {suspect} steal the missing object?",
            answer=f"No. {suspect} moved the cart, but the object slipped into the cloth without being noticed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective studies clues, asks questions, and uses careful reasoning to understand what happened.",
        ),
        QAItem(
            question="What is a scholar?",
            answer="A scholar is a person who learns deeply about a subject and shares that knowledge with others.",
        ),
        QAItem(
            question="Why should a detective avoid blaming someone too quickly?",
            answer="A detective should avoid quick blame because a clue may show where something went without proving who caused it.",
        ),
        QAItem(
            question="What is dexterity?",
            answer="Dexterity is the ability to use the hands and fingers carefully and skillfully.",
        ),
        QAItem(
            question="What makes a whodunit fair?",
            answer="A fair whodunit gives readers clues that can make sense before the solution is revealed.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
missing(Item) :- chosen_item(Item).
clue_points_to_cart(Item) :- missing(Item), cart_clue.
revealed(Item) :- clue_points_to_cart(Item), dexterity_test.
reasonable_case(Item, Suspect) :-
    missing(Item),
    suspect(Suspect),
    clue_points_to_cart(Item),
    dexterity_test,
    not intentional_theft.
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("place", "library"),
        asp.fact("chosen_item", "silver_bookmark"),
        asp.fact("missing", "silver_bookmark"),
        asp.fact("suspect", "Mara"),
        asp.fact("cart_clue"),
        asp.fact("dexterity_test"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show reasonable_case/2."))
    return sorted(set(asp.atoms(model, "reasonable_case")))


def asp_verify() -> int:
    expected = [("silver_bookmark", "Mara")]
    actual = asp_valid_combos()
    if actual == expected:
        print("OK: clingo gate matches Python gate (1 combo).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("python:", expected)
    print("clingo:", actual)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A suspenseful library whodunit about detective work and dexterity."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--name")
    parser.add_argument("--scholar")
    parser.add_argument("--suspect", choices=SUSPECTS)
    parser.add_argument("--item", choices=ITEMS)
    parser.add_argument("--challenge", choices=CHALLENGES)
    parser.add_argument("--gender", choices=["girl", "boy"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    detective_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    scholar_name = args.scholar or rng.choice(SCHOLAR_NAMES)
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    item = args.item or rng.choice(list(ITEMS))
    challenge = args.challenge or rng.choice(list(CHALLENGES))
    place = args.place or "library"
    if not valid_combo(place, item, challenge, suspect):
        raise StoryError(explain_rejection(place, item, challenge, suspect))
    return StoryParams(
        place=place,
        detective_name=detective_name,
        detective_gender=gender,
        scholar_name=scholar_name,
        scholar_role="visiting scholar",
        missing_item=item,
        suspect=suspect,
        dexterity_challenge=challenge,
        case_variant=rng.randrange(3),
        opening_variant=rng.randrange(len(OPENINGS)),
        ending_variant=rng.randrange(len(ENDINGS)),
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label:12} ({entity.kind:9}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  resolved: {world.facts.get('resolved')}")
    lines.append(f"  fired: {sorted(world.fired)}")
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


def curated_params() -> list[StoryParams]:
    return [
        StoryParams(
            place="library",
            detective_name="Luna",
            detective_gender="girl",
            scholar_name="Dr. Vale",
            scholar_role="visiting scholar",
            missing_item="silver_bookmark",
            suspect="Mara",
            dexterity_challenge="thread_the_needle",
        ),
        StoryParams(
            place="library",
            detective_name="Dex",
            detective_gender="boy",
            scholar_name="Professor Reed",
            scholar_role="visiting scholar",
            missing_item="brass_key",
            suspect="Jon",
            dexterity_challenge="stack_the_coins",
            case_variant=1,
            opening_variant=1,
            ending_variant=1,
        ),
        StoryParams(
            place="library",
            detective_name="Ivy",
            detective_gender="girl",
            scholar_name="Ms. Noor",
            scholar_role="visiting scholar",
            missing_item="blue_lens",
            suspect="Pia",
            dexterity_challenge="balance_the_quill",
            case_variant=2,
            opening_variant=2,
            ending_variant=2,
        ),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable_case/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in curated_params()]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError:
                continue
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
        header = ""
        if args.all:
            params = sample.params
            header = (
                f"### {params.detective_name}: {params.missing_item} "
                f"at {params.place} with {params.suspect}"
            )
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
