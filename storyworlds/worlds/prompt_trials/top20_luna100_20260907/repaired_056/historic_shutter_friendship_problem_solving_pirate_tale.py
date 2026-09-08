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
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402

PLACES = {
    "old harbor": {
        "setting": "the old harbor",
        "landmark": "a historic lighthouse",
        "safe": True,
        "shutter": True,
    },
    "coral cove": {
        "setting": "Coral Cove",
        "landmark": "a historic lookout tower",
        "safe": True,
        "shutter": True,
    },
    "maple island": {
        "setting": "Maple Island",
        "landmark": "a historic signal house",
        "safe": True,
        "shutter": True,
    },
    "whispering quay": {
        "setting": "the Whispering Quay",
        "landmark": "a historic sea gate",
        "safe": True,
        "shutter": True,
    },
}

NAMES = ("Luna", "Mara", "Pip", "Nico", "Tessa", "Jory", "Bea", "Finn")
MOODS = ("brave", "patient", "curious", "careful", "cheerful")
ROLES = ("captain", "deck helper", "map keeper", "lookout")

CASES = (
    {
        "title": "the salt-wind shutter",
        "opening": "A hard wind rattled the old harbor's historic lighthouse just before the evening bell.",
        "problem": "One wooden shutter had swung loose, and the lighthouse lamp could not shine through its narrow window.",
        "clue": "a rope had slipped from a brass ring above the window, while the spare hook lay beneath a coil of sailcloth",
        "wrong": "tried to push the shutter closed from the ground with a long oar, but the wind shoved it open again",
        "discovery": "the shutter was not broken; its rope had been threaded around the wrong ring",
        "action": "asked the harbor keeper to lower the safe line, then used the spare hook to guide the rope through the correct ring",
        "result": "the shutter folded neatly against the stone wall and the lamp cast a bright path across the water",
        "friendship": "Luna thanked the harbor keeper and shared the credit with her friend instead of claiming the fix alone",
        "lesson": "friends solve hard problems by sharing clues and giving one another room to think",
        "ending": "That night, the historic lighthouse blinked over the waves, and two friends sailed home beneath its steady golden beam.",
        "sound": ("clack", "whump", "click"),
    },
    {
        "title": "the painted pirate shutter",
        "opening": "At Coral Cove, a historic lookout tower wore a painted shutter shaped like a blue whale.",
        "problem": "The shutter would not open, so the lookout could not send the crew's welcome signal.",
        "clue": "a tiny shell was wedged in the lower hinge, and the hinge pin had slipped sideways",
        "wrong": "pulled the shutter with all her might, but the whale tail only squeaked",
        "discovery": "the shutter needed a careful lift before it could swing",
        "action": "held the lantern while her friend lifted the hinge pin with a wooden spoon",
        "result": "the shutter opened, and the lookout sent three cheerful flashes across the cove",
        "friendship": "Luna admitted she needed help, and her friend proudly supplied the missing idea",
        "lesson": "asking a friend for help can make a clever solution possible",
        "ending": "The blue whale shutter waved in the sea breeze while the friends celebrated with warm cocoa on deck.",
        "sound": ("squeak", "tink", "flash"),
    },
    {
        "title": "the moonlit signal",
        "opening": "On Maple Island, a historic signal house stood above the moonlit dock.",
        "problem": "Its shutter was stuck halfway open, making every lantern signal look like a different message.",
        "clue": "the lower latch was tied with a knot meant for a boat, not a window",
        "wrong": "copied the confusing flashes into her notebook without first checking the stuck latch",
        "discovery": "the signal was unclear because the shutter could not make its full shapes",
        "action": "worked with her friend to loosen the knot and replace it with a simple loop",
        "result": "the shutter swung freely, and the dock crew understood that the boat was safe to enter",
        "friendship": "Luna listened when her friend noticed the knot, then praised the careful observation",
        "lesson": "problem solving improves when friends compare what each one notices",
        "ending": "The signal house sent one clear moon-shaped flash, and the waiting boat glided into the quiet dock.",
        "sound": ("tap", "scrape", "blink"),
    },
    {
        "title": "the sea gate puzzle",
        "opening": "At the Whispering Quay, sailors gathered beside a historic sea gate before a small storm.",
        "problem": "A heavy shutter over the gate's warning bell had closed, hiding the bell from view.",
        "clue": "three shells marked the safe lifting points, but one shell was covered by a wet rope",
        "wrong": "pulled the largest rope because it looked strongest, and a bucket swung down with a splash",
        "discovery": "the shells showed the order for lifting the shutter, not the strength of the ropes",
        "action": "moved the bucket aside, followed the shell marks, and lifted with her friend on the count of three",
        "result": "the bell became visible and rang before the storm reached the quay",
        "friendship": "Luna and her friend took turns calling the count so neither had to work alone",
        "lesson": "good friends make a plan together before they pull, push, or hurry",
        "ending": "The warning bell boomed over the quay, and the friends tied their ship safely before the rain arrived.",
        "sound": ("splash", "heave-ho", "boom"),
    },
    {
        "title": "the shuttered treasure map",
        "opening": "A historic chart room aboard the little ship Starling had one round shutter over its map window.",
        "problem": "Sunlight could not reach the map, and the crew kept mistaking a reef for a safe channel.",
        "clue": "the shutter's inside peg had been placed through a painted star instead of the real hole beside it",
        "wrong": "searched the sea for a reef marker while the important clue stayed hidden on the window",
        "discovery": "the painted star was decoration, while the plain hole held the shutter open",
        "action": "moved the peg, opened the shutter, and traced the safe channel with a blue crayon",
        "result": "the crew steered around the reef and reached the island without a bump",
        "friendship": "Luna let her friend hold the map steady and thanked them for spotting the plain hole",
        "lesson": "friends can solve a puzzle by looking past the most eye-catching clue",
        "ending": "The Starling sailed into calm water, its map glowing beneath the open historic shutter.",
        "sound": ("knock", "rustle", "splash"),
    },
)

DIALOGUE = (
    ("I know what to do", "Maybe, but let us check the clues together"),
    ("The shutter is ruined", "Let us look closely before we decide that"),
    ("Pull harder", "A plan is safer than a stronger pull"),
    ("I found something small", "Small clues can explain big problems"),
    ("We should hurry", "We can work quickly after we make a safe plan"),
    ("I cannot fix this alone", "You do not have to; I am here with you"),
)

OPENINGS = (
    "The sea was calm until one stubborn shutter made the whole crew pause.",
    "A pirate adventure began with an ordinary wooden shutter and an unusual problem.",
    "Before breakfast, the harbor's oldest building gave a loud wooden rattle.",
    "The ship was ready to sail, but a historic shutter had one last puzzle to share.",
)

ASP_RULES = r"""
kind(historic).
kind(shutter).
kind(friendship).
kind(problem_solving).
feature(historic) :- kind(historic).
feature(shutter) :- kind(shutter).
feature(friendship) :- kind(friendship).
feature(problem_solving) :- kind(problem_solving).

place(old_harbor).
place(coral_cove).
place(maple_island).
place(whispering_quay).

has_landmark(old_harbor, historic_lighthouse).
has_landmark(coral_cove, historic_lookout_tower).
has_landmark(maple_island, historic_signal_house).
has_landmark(whispering_quay, historic_sea_gate).

has_feature(P, historic) :- place(P), has_landmark(P, _).
has_feature(P, shutter) :- place(P), has_landmark(P, _).
has_feature(P, friendship) :- place(P), has_landmark(P, _).
has_feature(P, problem_solving) :- place(P), has_landmark(P, _).

compatible(P) :- has_feature(P, historic), has_feature(P, shutter),
                  has_feature(P, friendship), has_feature(P, problem_solving).

#show compatible/1.
#show has_feature/2.
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: Optional[str] = None
    carried_by: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    mood: str
    role: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle pirate tale about a historic shutter, friendship, and problem solving."
    )
    parser.add_argument("--place", choices=tuple(PLACES))
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


def asp_facts() -> str:
    import asp

    lines = []
    for place, data in PLACES.items():
        atom = place.replace(" ", "_")
        landmark = data["landmark"].replace(" ", "_")
        lines.append(asp.fact("place", atom))
        lines.append(asp.fact("has_landmark", atom, landmark))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    python_places = {
        place.replace(" ", "_")
        for place, data in PLACES.items()
        if data["safe"] and data["shutter"]
    }
    model = asp.one_model(asp_program("#show compatible/1."))
    clingo_places = {row[0] for row in asp.atoms(model, "compatible")}
    if python_places == clingo_places:
        print(f"OK: clingo gate matches Python reasoning ({len(clingo_places)} places).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(clingo_places - python_places))
    print("only in python:", sorted(python_places - clingo_places))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(tuple(PLACES))
    if place not in PLACES:
        raise StoryError(f"Unknown place: {place!r}.")
    if not PLACES[place]["safe"] or not PLACES[place]["shutter"]:
        raise StoryError("This tale needs a safe historic place with a working shutter.")
    hero = rng.choice(NAMES)
    friend = rng.choice([name for name in NAMES if name != hero])
    return StoryParams(
        place=place,
        hero=hero,
        friend=friend,
        mood=rng.choice(MOODS),
        role=rng.choice(ROLES),
        seed=args.seed,
    )


def _story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.place, params.hero, params.friend, params.mood, params.role))
    return int.from_bytes(hashlib.blake2b(text.encode(), digest_size=8).digest(), "big")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place!r}.")
    if params.hero == params.friend:
        raise StoryError("The hero and friend must be different people.")

    seed = _story_seed(params)
    rng = random.Random(seed)
    case = CASES[seed % len(CASES)]
    opening = OPENINGS[(seed // len(CASES)) % len(OPENINGS)]
    dialogue = DIALOGUE[(seed // (len(CASES) * len(OPENINGS))) % len(DIALOGUE)]
    meta = PLACES[params.place]

    world = World(place=meta["setting"])
    hero = Entity(
        id=params.hero,
        kind="character",
        label=params.role,
        type="pirate",
        location=params.place,
        meters={"strength": 0.8, "care": 0.8},
        memes={"bravery": 1.0, "friendship": 0.6},
    )
    friend = Entity(
        id=params.friend,
        kind="character",
        label="friend",
        type="pirate_helper",
        location=params.place,
        meters={"strength": 0.7, "care": 0.9},
        memes={"friendship": 1.0, "observation": 0.8},
    )
    shutter = Entity(
        id="historic_shutter",
        kind="object",
        label="the historic shutter",
        type="shutter",
        location=params.place,
        meters={"stability": 0.3, "openness": 0.2},
        memes={"clue": 1.0},
    )
    world.entities = {entity.id: entity for entity in (hero, friend, shutter)}

    world.say(opening)
    world.say(
        f"{params.hero}, a {params.mood} young pirate and {params.role}, "
        f"was exploring {meta['setting']} with {params.friend}."
    )
    world.say(f"Their destination was {meta['landmark']}, a place sailors had cared for across many years.")
    world.say(case["opening"])

    world.para()
    sound_one, sound_two, sound_three = case["sound"]
    world.say(
        f"The historic shutter went '{sound_one} ... {sound_two}!' "
        f"{case['problem']}"
    )
    world.say(f"{params.hero} frowned. {params.friend} watched the hinges and noticed that {case['clue']}.")
    world.say(f"'{dialogue[0]},' said {params.hero}. '{dialogue[1]},' answered {params.friend}.")
    world.say(f"Their first attempt was not enough: {params.hero} {case['wrong']}.")

    world.para()
    world.say(
        f"They stopped rushing and shared a plan. The useful clue was that {case['discovery']}."
    )
    world.say(
        f"'{sound_three}!' went the old wood when they tested the safer idea."
    )
    world.say(
        f"Together, they decided to {case['action']}."
    )

    world.para()
    world.say(
        f"The plan worked: {case['result']}."
    )
    world.say(case["friendship"] + ".")
    world.say(
        f"They learned that {case['lesson'].capitalize()}."
    )
    world.say(case["ending"])

    hero.meters["care"] = 1.4
    friend.meters["observation"] = 1.3
    shutter.meters["stability"] = 1.0
    shutter.meters["openness"] = 1.0
    hero.memes["problem_solved"] = 1.0
    friend.memes["problem_solved"] = 1.0
    world.trace = [
        f"noticed: {case['problem']}",
        f"clue: {case['clue']}",
        f"first_attempt: {case['wrong']}",
        f"discovery: {case['discovery']}",
        f"resolution: {case['result']}",
        "friendship: the pair shared credit and solved the problem together",
    ]
    world.facts = {
        "place": params.place,
        "setting": meta["setting"],
        "hero": params.hero,
        "friend": params.friend,
        "landmark": meta["landmark"],
        "case": case["title"],
        "problem": case["problem"],
        "clue": case["clue"],
        "discovery": case["discovery"],
        "resolution": case["result"],
        "lesson": case["lesson"],
    }

    prompts = [
        f"Write a child-friendly pirate tale about {params.hero} and {params.friend} solving a historic shutter problem in {meta['setting']}.",
        f"Tell how friendship and problem solving help repair the shutter at {meta['landmark']}.",
        f"Include the pirate sounds '{sound_one}', '{sound_two}', and '{sound_three}', plus a clear ending image.",
    ]

    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} and {params.friend} find?",
            answer=f"They found that {case['problem']}. The shutter stopped an important light, signal, or warning from doing its job.",
        ),
        QAItem(
            question="What clue helped them understand the problem?",
            answer=f"They noticed that {case['clue']}. That small observation pointed them toward a safer solution.",
        ),
        QAItem(
            question=f"How did {params.hero} and {params.friend} solve the problem?",
            answer=f"They worked together to {case['action']}. Their shared plan made the shutter work again.",
        ),
        QAItem(
            question="How did friendship help in the tale?",
            answer=f"{case['friendship']}. The friends listened to each other and shared the work.",
        ),
        QAItem(
            question="What lesson did the pirates learn?",
            answer=f"They learned that {case['lesson'].capitalize()}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a movable cover for a window or opening. It can protect the opening or control how much light passes through.",
        ),
        QAItem(
            question="What does historic mean?",
            answer="Historic describes something important from the past, such as an old lighthouse, tower, or sea gate cared for by many people.",
        ),
        QAItem(
            question="Why is friendship useful when solving a problem?",
            answer="Friendship is useful because friends can share clues, listen to different ideas, and help one another make a safe plan.",
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
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            details = []
            if entity.label:
                details.append(f"label={entity.label}")
            if entity.location:
                details.append(f"location={entity.location}")
            if entity.meters:
                details.append(f"meters={entity.meters}")
            if entity.memes:
                details.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.kind} {' '.join(details)}")
        for item in sample.world.trace:
            print(f"  event: {item}")
    if qa:
        print()
        print("== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
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


CURATED = [
    StoryParams(place="old harbor", hero="Luna", friend="Mara", mood="brave", role="captain"),
    StoryParams(place="coral cove", hero="Pip", friend="Tessa", mood="curious", role="lookout"),
    StoryParams(place="maple island", hero="Nico", friend="Bea", mood="patient", role="map keeper"),
    StoryParams(place="whispering quay", hero="Jory", friend="Finn", mood="careful", role="deck helper"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/1.\n#show has_feature/2."))
        return

    if args.verify:
        status = asp_verify()
        if status:
            sys.exit(status)
        for params in CURATED:
            sample = generate(params)
            if not sample.story or not sample.story_qa or not sample.world_qa:
                print("Generated story validation failed.")
                sys.exit(1)
        print(f"OK: generated {len(CURATED)} story samples.")
        return

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show compatible/1.\n#show has_feature/2."))
        print(asp.atoms(model, "compatible"))
        print(asp.atoms(model, "has_feature"))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen = set()
        attempts = 0
        while len(samples) < max(1, args.n) and attempts < max(20, args.n * 30):
            attempts += 1
            local_seed = (args.seed if args.seed is not None else rng.randrange(2**31)) + attempts
            local_rng = random.Random(local_seed)
            params = resolve_params(args, local_rng)
            params.seed = local_seed
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
