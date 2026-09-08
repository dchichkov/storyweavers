#!/usr/bin/env python3
"""
A small mystery world about a mechanism, friendship, caution, and a twist.
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
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

STORYWORLDS_DIR = __import__("pathlib").Path(__file__).resolve().parents[3]
sys.path.insert(0, str(STORYWORLDS_DIR))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    kind: str
    meme: dict[str, float] = field(default_factory=dict)
    meter: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: Optional[str] = None
    friend_name: Optional[str] = None
    place: Optional[str] = None
    seed: Optional[int] = None


@dataclass
class World:
    detective: Character
    friend: Character
    place: str
    mechanism_found: bool = False
    caution_used: bool = False
    twist_revealed: bool = False
    clue_chain: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


NAMES = ["Mina", "Pip", "Nori", "Luna", "Tavi", "Roo", "Milo", "Suri"]
PLACES = [
    "the attic library",
    "the garden shed",
    "the moonlit toy shop",
    "the quiet station platform",
    "the old clock room",
]

MECHANISMS = [
    {
        "title": "the missing key mechanism",
        "setting": "a brass key mechanism inside a music box",
        "problem": "the music box would not open, so a little ribbon had vanished with the key",
        "clue": "the wind-up spring clicked only when the lid was lifted halfway",
        "mistake": "someone assumed the key had been stolen",
        "caution": "the mechanism had tiny teeth that could pinch a careless finger",
        "dialogue": ("'I think it is stuck,' said {friend}.", "'Then we should look, not grab,' said {name}."),
        "twist": "the ribbon had not been stolen at all; it was tucked under the box's felt lining",
        "repair": "they used a thin wooden pointer, freed the key, and set the ribbon back beside the music box",
        "ending": "the music box chimed once, and the ribbon lay safe on the table like a soft red trail",
    },
    {
        "title": "the lantern latch mechanism",
        "setting": "a springy latch inside an old lantern door",
        "problem": "the lantern would not stay shut, so the candle kept going out in the breeze",
        "clue": "a line of dust showed the latch had slipped only when the lantern tilted left",
        "mistake": "someone blamed the lantern for being broken beyond repair",
        "caution": "the glass was warm, and the latch could snap shut on a busy hand",
        "dialogue": ("'That door keeps whispering open,' said {friend}.", "'Let's ask why before we force it,' said {name}."),
        "twist": "the latch was fine; a loose pebble was wedged in the hinge and acting like a secret blocker",
        "repair": "they cooled the lantern, tipped out the pebble, and closed the door gently with a cloth",
        "ending": "the lantern held its glow, and the pebble rested outside like the answer to a riddle",
    },
    {
        "title": "the toy train mechanism",
        "setting": "a tiny gear mechanism beneath a tin toy train",
        "problem": "the train rolled backward every time it reached the bridge",
        "clue": "the bridge plank had a small bump that made the front wheel wobble",
        "mistake": "someone thought the train's engine had lost its will to move forward",
        "caution": "the gears were exposed, so a finger could stop the whole machine and get pinched",
        "dialogue": ("'It looks shy,' said {friend}.", "'Or something is nudging it,' said {name}."),
        "twist": "the train was not shy at all; a magnet under the bridge was pulling one wheel off course",
        "repair": "they moved the magnet away and guided the train with a pencil-sized stick",
        "ending": "the little train crossed straight ahead, leaving the bridge behind with a proud silver rattle",
    },
    {
        "title": "the pantry door mechanism",
        "setting": "a latch mechanism on a pantry door",
        "problem": "the pantry kept clicking open after everyone left the room",
        "clue": "crumbs lined up from the floor to the latch as if carried by a busy little path",
        "mistake": "someone thought the door was haunted by a sneaky draft",
        "caution": "the door was heavy, and a hasty pull could slam a thumb",
        "dialogue": ("'Did the door move on its own?' asked {friend}.", "'Let's find the real mover,' said {name}."),
        "twist": "a cat had pushed the door with its shoulder while chasing the crumbs",
        "repair": "they cleaned the crumbs, latched the door, and gave the cat a toy instead",
        "ending": "the pantry stayed shut, and the cat settled beside the toy with a pleased blink",
    },
    {
        "title": "the garden gate mechanism",
        "setting": "a squeaky hinge mechanism on a garden gate",
        "problem": "the gate opened only a little, then stopped as if it remembered a secret",
        "clue": "fresh mud on the hinge matched a trail from the flower beds",
        "mistake": "someone blamed rust before checking the track",
        "caution": "the gate had a sharp edge hidden in the frame",
        "dialogue": ("'It feels stuck,' said {friend}.", "'It may only be crowded,' said {name}."),
        "twist": "a lost scarf had wrapped around the hinge and was holding the gate like a stubborn hand",
        "repair": "they loosened the scarf carefully and rubbed the hinge with a drop of oil",
        "ending": "the gate swung open, and the scarf fluttered free like a bright clue finally solved",
    },
    {
        "title": "the drawer lock mechanism",
        "setting": "a tiny lock mechanism on a wooden drawer",
        "problem": "the drawer would not open, even though everyone knew the note was inside",
        "clue": "the keyhole glittered with a speck of blue paint from a craft project",
        "mistake": "someone assumed the note had been lost forever",
        "caution": "the lock was delicate, so forcing it could bend the latch",
        "dialogue": ("'The drawer is hiding something,' said {friend}.", "'Then we should persuade it politely,' said {name}."),
        "twist": "the note was not inside the drawer at all; it had slipped behind the drawer's back board",
        "repair": "they lifted the drawer, found the note, and opened the lock with the proper key",
        "ending": "the note returned to view, and the drawer rested calmly in its frame",
    },
]

OPENERS = [
    "The mystery began when",
    "On an otherwise ordinary afternoon,",
    "Just before the room went quiet,",
    "At the edge of a very small and puzzling problem,",
    "When the light fell across the floorboards,",
    "Near the start of a careful search,",
]

DEDUCTIONS = [
    "looked for what repeated instead of what seemed dramatic",
    "checked the edges, hinges, and shadows before making a guess",
    "asked one careful question after another",
    "followed the clue trail from the floor to the mechanism",
    "moved slowly so they would not disturb the evidence",
    "noticed that the same sound happened every time the object tilted",
]

LESSONS = [
    "The best detective work was patient and gentle.",
    "A cautious friend can save a mystery from becoming a mess.",
    "A good twist is only fair when the clues were there all along.",
    "Friendship helped more than shouting ever could.",
    "The answer was hidden in plain sight, waiting for a careful look.",
    "Sometimes the thing that seems dangerous only needs respect and a slower hand.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world about a mechanism and friendship.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend-name", choices=NAMES)
    ap.add_argument("--place", choices=PLACES)
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
    name = args.name or rng.choice(NAMES)
    friend_choices = [n for n in NAMES if n != name]
    friend_name = args.friend_name or rng.choice(friend_choices)
    place = args.place or rng.choice(PLACES)
    return StoryParams(name=name, friend_name=friend_name, place=place)


def _reasonableness_gate(params: StoryParams) -> None:
    if params.name == params.friend_name:
        raise StoryError("The detective and friend must be different people.")
    if params.place not in PLACES:
        raise StoryError("That place is not part of this mystery world.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)

    rng = random.Random(params.seed if params.seed is not None else 0)
    case = rng.choice(MECHANISMS)
    opener = rng.choice(OPENERS)
    deduction = rng.choice(DEDUCTIONS)
    lesson = rng.choice(LESSONS)

    detective = Character(name=params.name, kind="detective", meme={"curious": 1.0, "careful": 1.0}, meter={"worry": 1.0})
    friend = Character(name=params.friend_name, kind="friend", meme={"loyal": 1.0, "brave": 1.0}, meter={"worry": 0.5})
    world = World(detective=detective, friend=friend, place=params.place)

    line1 = f"{params.name} and {params.friend_name} were exploring {params.place} when they found {case['setting']}."
    line2 = f"{opener} {case['problem']}."
    line3 = f"At first, {params.friend_name} made the wrong guess: {case['mistake']}."
    line4 = f"{params.name} did not rush. Instead, they {deduction}."

    world.clue_chain.append(case["clue"])
    world.facts["case"] = case["title"]
    world.facts["problem"] = case["problem"]
    world.facts["mistake"] = case["mistake"]
    world.facts["clue"] = case["clue"]

    dialogue1, dialogue2 = [s.format(name=params.name, friend=params.friend_name) for s in case["dialogue"]]
    line5 = f"{dialogue1} {dialogue2}"

    world.caution_used = True
    line6 = f"They remembered to be careful because {case['caution']}."
    line7 = f"The clue that changed everything was simple: {case['clue']}."
    line8 = f"Then came the twist: {case['twist']}."
    world.twist_revealed = True

    line9 = f"Together, they fixed it by {case['repair']}."
    world.mechanism_found = True
    world.facts["repair"] = case["repair"]
    world.facts["twist"] = case["twist"]
    world.facts["lesson"] = lesson

    line10 = f"{lesson} By the end, {case['ending']}."

    world.facts["story"] = " ".join([line1, line2, line3, line4, line5, line6, line7, line8, line9, line10])

    prompts = [
        f"Write a child-friendly mystery about {case['title']} in {params.place}.",
        f"Show how {params.name} and {params.friend_name} solve a problem with a mechanism and a cautious clue.",
        f"Include a twist, a short dialogue, and a happy ending image for {case['title']}.",
    ]

    story_qa = [
        QAItem(
            question=f"What problem did the characters discover in {case['title']}?",
            answer=f"They discovered that {case['problem']}.",
        ),
        QAItem(
            question=f"What wrong guess did {params.friend_name} make at first?",
            answer=f"{params.friend_name} first guessed that {case['mistake']}.",
        ),
        QAItem(
            question=f"What clue helped solve the mystery?",
            answer=f"The clue was that {case['clue']}.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {case['twist']}.",
        ),
        QAItem(
            question="How did they fix the problem?",
            answer=f"They fixed it by {case['repair']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of parts that work together to make something move, lock, click, open, or turn.",
        ),
        QAItem(
            question="Why should you be cautious around a mechanism?",
            answer="You should be cautious because small moving parts, springs, hinges, or edges can pinch, snap, or surprise you.",
        ),
        QAItem(
            question="What makes a good mystery story?",
            answer="A good mystery story gives clues, includes a wrong first guess, and ends with a fair explanation.",
        ),
        QAItem(
            question="Why is friendship important in this kind of story?",
            answer="Friendship helps the characters share ideas, stay calm, and solve the problem together.",
        ),
        QAItem(
            question="What should a character do before forcing something stuck?",
            answer="A character should stop, look carefully, and ask for help or check for a clue before forcing it.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        w = sample.world
        print(f"detective={w.detective.name}, kind={w.detective.kind}, meme={w.detective.meme}, meter={w.detective.meter}")
        print(f"friend={w.friend.name}, kind={w.friend.kind}, meme={w.friend.meme}, meter={w.friend.meter}")
        print(f"place={w.place}, mechanism_found={w.mechanism_found}, caution_used={w.caution_used}, twist_revealed={w.twist_revealed}")
        print(f"clues={w.clue_chain}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
valid_place(P) :- place(P).
valid_case(C) :- case(C).

show_twist(C) :- valid_case(C).
#show valid_place/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(asp.fact("place", place) for place in PLACES) + "\n" + "\n".join(
        asp.fact("case", case["title"]) for case in MECHANISMS
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_place/1."))
    return sorted(set(asp.atoms(model, "valid_place")))


def asp_verify() -> int:
    py = set((p,) for p in PLACES)
    cl = set(asp_valid_places())
    if py == cl:
        print(f"OK: clingo gate matches PLACES ({len(py)} places).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generation_samples(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        out: list[StoryParams] = []
        for i, place in enumerate(PLACES):
            name = NAMES[i % len(NAMES)]
            friend = NAMES[(i + 1) % len(NAMES)]
            if friend == name:
                friend = NAMES[(i + 2) % len(NAMES)]
            out.append(StoryParams(name=name, friend_name=friend, place=place))
        return out
    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [resolve_params(args, random.Random(base + i)) for i in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        print("\n".join(f"{p[0]}" for p in asp_valid_places()))
        return

    samples: list[StorySample] = []
    for i, params in enumerate(generation_samples(args)):
        params.seed = (args.seed if args.seed is not None else 0) + i
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
