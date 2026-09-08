#!/usr/bin/env python3
"""
A small child-facing ghost story world about learning to differentiate two
mysterious sounds, with a gentle Twist.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


METERS = {"darkness", "noise", "warmth", "courage", "clarity"}
MEMES = {"worry", "curiosity", "trust", "relief", "kindness"}


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in METERS:
            self.meters.setdefault(key, 0.0)
        for key in MEMES:
            self.memes.setdefault(key, 0.0)


@dataclass
class House:
    name: str
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in METERS:
            self.meters.setdefault(key, 0.0)
        for key in MEMES:
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    aunt_name: str
    house_name: str
    place: str
    seed: Optional[int] = None


CHILD_NAMES = ["Luna", "Milo", "Nora", "Theo", "Ivy", "Sam"]
AUNT_NAMES = ["Aunt June", "Aunt Bea", "Aunt Rosa", "Aunt Mae"]
HOUSE_NAMES = ["Whisper House", "The Blue Cottage", "Moonbell House", "The Crooked Manor"]
PLACES = ["the edge of town", "a hill above the village", "the old lane", "the misty moor"]


@dataclass(frozen=True)
class Haunting:
    id: str
    omen: str
    ghost_claim: str
    false_clue: str
    task: str
    obstacle: str
    turn: str
    resolution: str
    ending: str
    sound_a: str
    sound_b: str


HAUNTINGS = [
    Haunting(
        "bell_and_wing",
        "At midnight, a bell chimed once, and a soft flutter answered from the attic.",
        "the ghost of a lonely bell maker was calling for company",
        "the attic window trembled though the night air was still",
        "climb to the attic and differentiate the bell's clear chime from the softer sound",
        "the stairs groaned so loudly that every sound seemed to become one long moan",
        "held a candle near the bell and listened between each creak",
        "the clear chime came from a loose brass bell, while the flutter came from a trapped moth",
        "The moth flew into the moonlight, and the bell gave one friendly ring.",
        "ting",
        "fuff",
    ),
    Haunting(
        "footsteps_and_drips",
        "Wet footsteps crossed the kitchen floor, followed by three careful taps.",
        "a ghostly visitor had come looking for its lost umbrella",
        "the marks ended beside a locked cupboard",
        "follow the prints and differentiate footsteps from the tapping water",
        "a dripping pipe echoed inside the cupboard like a tiny marching band",
        "placed a bowl under the pipe and counted the steps again",
        "the wet prints belonged to rainwater on Aunt Bea's boots, while the taps came from the pipe",
        "The floor dried, and the cupboard stopped knocking as if it had heard the truth.",
        "tap",
        "squelch",
    ),
    Haunting(
        "music_and_wind",
        "A lonely tune floated from the parlor after the piano had been closed.",
        "a ghost musician was practicing for a concert no one remembered",
        "a pale shape appeared beside the piano bench",
        "enter the parlor and differentiate the tune from the whispering curtains",
        "the curtains swelled and hid the piano keys",
        "tied the curtains back and asked the unseen player for one more note",
        "the tune came from a music box beneath the bench, while the pale shape was moonlight on dust",
        "The music box played its last note, and the moonlit dust settled like silver snow.",
        "plink",
        "whoosh",
    ),
    Haunting(
        "scratching_and_purring",
        "Scratching sounded behind the wall, then a deep purr rolled under the floor.",
        "a house ghost was trying to scratch a secret message",
        "the wallpaper curled into a shape like a pale hand",
        "find the hidden space and differentiate scratching from the animal's purr",
        "the wall released a puff of dust that made the room look full of spirits",
        "opened the window, waited for the dust to clear, and followed the gentler sound",
        "the scratching came from a branch outside, while a stray cat had curled beneath the floorboards",
        "The cat blinked up at the child, and the branch tapped a harmless pattern on the glass.",
        "scratch",
        "purr",
    ),
]


ASP_RULES = r"""
needs_listening(P) :- child(P), haunting(H), omen(H).
can_differentiate(P) :- needs_listening(P), has_sound(P, first), has_sound(P, second).
valid_story(P) :- can_differentiate(P), has_courage(P).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("child", "child"),
            asp.fact("haunting", "haunting"),
            asp.fact("omen", "haunting"),
            asp.fact("has_sound", "child", "first"),
            asp.fact("has_sound", "child", "second"),
            asp.fact("has_courage", "child"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    return bool(asp.atoms(model, "valid_story"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle ghost story about learning to differentiate mysterious sounds."
    )
    parser.add_argument("--name", choices=CHILD_NAMES)
    parser.add_argument("--aunt", choices=AUNT_NAMES)
    parser.add_argument("--house", choices=HOUSE_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(CHILD_NAMES)
    return StoryParams(
        child_name=name,
        child_type="girl" if name in {"Luna", "Nora", "Ivy"} else "boy",
        aunt_name=args.aunt or rng.choice(AUNT_NAMES),
        house_name=args.house or rng.choice(HOUSE_NAMES),
        place=args.place or rng.choice(PLACES),
        seed=rng.randrange(2**31),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.child_name not in CHILD_NAMES:
        raise StoryError("The child must have a name from the story registry.")
    if params.aunt_name not in AUNT_NAMES:
        raise StoryError("The grown-up helper must be a known aunt.")
    if params.house_name not in HOUSE_NAMES:
        raise StoryError("The haunted house must have a known name.")
    if params.place not in PLACES:
        raise StoryError("The house needs a known setting.")


def make_world(params: StoryParams) -> House:
    house = House(params.house_name, params.place)
    house.entities["child"] = Entity("child", params.child_type, params.child_name)
    house.entities["aunt"] = Entity("aunt", "woman", params.aunt_name)
    house.entities["ghost"] = Entity("ghost", "spirit", "the pale visitor")
    house.meters["darkness"] = 1
    house.meters["noise"] = 1
    house.memes["worry"] = 1
    house.facts.update(
        {
            "child": params.child_name,
            "aunt": params.aunt_name,
            "house": params.house_name,
            "place": params.place,
            "resolved": False,
        }
    )
    return house


def tell_story(params: StoryParams) -> House:
    house = make_world(params)
    rng = random.Random(params.seed if params.seed is not None else params.child_name)
    haunting = rng.choice(HAUNTINGS)
    house.facts["haunting"] = haunting
    house.facts["haunting_id"] = haunting.id
    house.facts["resolved"] = False

    child = params.child_name
    aunt = params.aunt_name
    house_name = params.house_name
    place = params.place

    intro_forms = [
        f"{child} stayed one rainy night in {house_name}, a tall house at {place}. "
        f"Everyone said a ghost lived there, but {child} wanted to know what the ghost really wanted.",
        f"When {child} arrived at {house_name} on {place}, the windows shone like sleepy eyes. "
        f"The house had a ghost story, and the story had never been checked carefully.",
        f"{child} was brave enough to sleep in {house_name}, even though it stood alone at {place}. "
        f"Still, bravery felt smaller when the first strange sound crossed the dark hallway.",
    ]
    intro = rng.choice(intro_forms)

    house.memes["curiosity"] = 1
    omen = haunting.omen
    dialogue_forms = [
        f'"Did you hear that?" whispered {child}. "{omen}"',
        f'{aunt} gripped the candle. "The house is speaking again, {child}."',
        f'"Maybe it is a ghost," said {child}. {aunt} answered, "Maybe. First, let us listen closely."',
    ]
    dialogue = rng.choice(dialogue_forms)
    if "let us listen" not in dialogue and "First" not in dialogue:
        dialogue += f' "{aunt} said, "We can differentiate the sounds before we decide what they mean.""'

    house.memes["trust"] = 1
    listening = (
        f"{aunt} did not run. Instead, {aunt} handed {child} a candle. "
        f'"We need to differentiate the sounds," {aunt} said. '
        f"{child} remembered the plan: {haunting.task}."
    )
    house.meters["courage"] = 1

    middle = (
        f"The first try was confusing. {haunting.obstacle.capitalize()}. "
        f"{child} nearly called the sound a ghost, but stopped and listened again. "
        f"{haunting.turn.capitalize()}."
    )
    house.meters["noise"] = 2
    house.meters["clarity"] = 1
    house.memes["worry"] = 0
    house.memes["curiosity"] = 2

    twist = (
        f"Then came the Twist: {haunting.resolution.capitalize()} "
        f"The pale visitor had never meant to frighten anyone; the house had simply "
        f"hidden two ordinary sounds inside one spooky story."
    )
    house.facts["resolved"] = True
    house.meters["darkness"] = 0
    house.meters["noise"] = 0
    house.meters["warmth"] = 1
    house.meters["clarity"] = 2
    house.memes["relief"] = 1
    house.memes["kindness"] = 1

    ending = (
        f"{haunting.ending} {child} smiled at {aunt}. "
        f'"A ghost story can be mysterious without being cruel," {child} said. '
        f"By morning, {house_name} felt less like a trap and more like a home with secrets."
    )

    paragraphs = [intro, omen, dialogue, listening, middle, twist, ending]
    house.facts["story"] = "\n\n".join(paragraphs)
    return house


def prompts(house: House) -> list[str]:
    haunting: Haunting = house.facts["haunting"]
    return [
        'Write a gentle ghost story that uses the word "differentiate".',
        f"Tell a ghost story in {house.name} where {house.facts['child']} must differentiate two sounds.",
        f"Use a Twist to reveal what really made the sounds: {haunting.sound_a} and {haunting.sound_b}.",
    ]


def story_qa(house: House) -> list[QAItem]:
    haunting: Haunting = house.facts["haunting"]
    child = house.facts["child"]
    aunt = house.facts["aunt"]
    return [
        QAItem(
            question=f"What did {child} hear first in {house.name}?",
            answer=f"{child} heard this warning: {haunting.omen}",
        ),
        QAItem(
            question=f"How did {aunt} help {child} in {house.name}?",
            answer=f"{aunt} stayed calm, gave {child} a candle, and helped {child} differentiate the two mysterious sounds instead of guessing that everything was a ghost.",
        ),
        QAItem(
            question=f"What obstacle made it hard for {child} to differentiate the sounds?",
            answer=f"{haunting.obstacle.capitalize()} {child} had to listen again rather than trust the first frightening impression.",
        ),
        QAItem(
            question=f"What was the Twist at the end of the ghost story?",
            answer=f"{haunting.resolution.capitalize()} The strange event had an ordinary cause, so the ghostly rumor no longer seemed frightening.",
        ),
    ]


def world_qa(house: House) -> list[QAItem]:
    return [
        QAItem(
            question="What does differentiate mean?",
            answer="To differentiate means to notice how two things are different from each other.",
        ),
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale about a spirit or mysterious event, often told to create wonder or a little safe fright.",
        ),
        QAItem(
            question="Why is careful listening useful?",
            answer="Careful listening helps us separate similar sounds and discover what may really be causing them.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(house: House) -> str:
    haunting: Haunting = house.facts["haunting"]
    return "\n".join(
        [
            "--- trace ---",
            f"house={house.name}",
            f"place={house.place}",
            f"haunting={haunting.id}",
            f"resolved={house.facts['resolved']}",
            f"meters={house.meters}",
            f"memes={house.memes}",
        ]
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    house = tell_story(params)
    return StorySample(
        params=params,
        story=house.facts["story"],
        prompts=prompts(house),
        story_qa=story_qa(house),
        world_qa=world_qa(house),
        world=house,
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


def asp_verify() -> int:
    import asp

    if asp_valid() is not True:
        print("MISMATCH: ASP rejected a reasonable story.")
        return 1
    params = StoryParams(
        child_name="Luna",
        child_type="girl",
        aunt_name="Aunt June",
        house_name="Whisper House",
        place="the old lane",
    )
    sample = generate(params)
    required = ["differentiate", "Twist", "ghost"]
    if any(word not in sample.story for word in required):
        print("MISMATCH: generated story lost a required feature.")
        return 1
    if len(sample.story_qa) < 3:
        print("MISMATCH: story QA is incomplete.")
        return 1
    print("OK: ASP and Python gates agree; generated story checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("ASP gate: valid_story/1 is", "true" if asp_valid() else "false")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [
            StoryParams("Luna", "girl", "Aunt June", "Whisper House", "the old lane"),
            StoryParams("Milo", "boy", "Aunt Bea", "The Blue Cottage", "the edge of town"),
            StoryParams("Nora", "girl", "Aunt Rosa", "Moonbell House", "a hill above the village"),
            StoryParams("Theo", "boy", "Aunt Mae", "The Crooked Manor", "the misty moor"),
        ]
        samples = [generate(params) for params in params_list]
    else:
        samples = []
        seen: set[str] = set()
        index = 0
        target = max(1, args.n)
        while len(samples) < target and index < max(50, target * 50):
            rng = random.Random(base_seed + index)
            index += 1
            params = resolve_params(args, rng)
            try:
                sample = generate(params)
            except StoryError as error:
                print(error)
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
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
