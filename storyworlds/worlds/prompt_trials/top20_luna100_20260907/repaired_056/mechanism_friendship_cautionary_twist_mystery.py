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
    "clockwork garden": {
        "setting": "the clockwork garden",
        "mechanism": "a brass watering mechanism",
        "safe": True,
    },
    "old ferry shed": {
        "setting": "the old ferry shed",
        "mechanism": "a rope-and-pulley mechanism",
        "safe": True,
    },
    "hilltop observatory": {
        "setting": "the hilltop observatory",
        "mechanism": "a rotating star mechanism",
        "safe": True,
    },
    "glasshouse": {
        "setting": "the glasshouse",
        "mechanism": "a vent-opening mechanism",
        "safe": True,
    },
}

CHAR_NAMES = ("Luna", "Milo", "Nia", "Toby", "Iris", "Pip", "Mara", "Jasper")
MOODS = ("curious", "careful", "brave", "patient")

CASES = (
    {
        "name": "the silent bell",
        "opening": "At sunset, the garden bell stopped ringing even though the wind still moved the vines.",
        "clue": "a tiny silver seed was wedged between two brass teeth",
        "twist": "the mechanism had not broken at all; a frightened mouse had carried the seed into its gears while hiding",
        "danger": "Luna nearly pulled the jammed wheel with all her strength",
        "action": "they turned the handle backward, loosened the seed with a wooden spoon, and left a safe crumb trail away from the gears",
        "result": "the bell rang again, and the mouse hurried into a warm nest beneath the shed",
        "ending": "The evening bell chimed softly while two friends watched the little mouse disappear among the lavender.",
        "lesson": "a stuck machine needs patience and a safe plan, not a stronger tug",
    },
    {
        "name": "the false footprints",
        "opening": "Fresh muddy footprints crossed the ferry shed, then vanished beside the pulley rope.",
        "clue": "the marks had a neat double line made by a dripping wheel, not by shoes",
        "twist": "someone had not sneaked into the shed; the old mechanism had rolled through puddled mud during the night",
        "danger": "Milo wanted to chase the footprints toward the dark riverbank",
        "action": "they tied the rope safely, examined the wheel, and marked the wet boards for the ferryman",
        "result": "the ferryman repaired the loose guide before anyone stepped beneath the swinging load",
        "ending": "By morning, the rope rested still, and the only tracks left were their careful footprints home.",
        "lesson": "a clue can look like a person until you study how it was made",
    },
    {
        "name": "the missing star",
        "opening": "One bright star vanished from the observatory's paper map just before the night lesson.",
        "clue": "a round patch of fresh glue shone under the rotating star mechanism",
        "twist": "the star had not been stolen; it was stuck to the mechanism's turning arm after a careless repair",
        "danger": "Nia reached for the moving arm before Luna called her back",
        "action": "they stopped the rotation, asked the astronomer for help, and lifted the paper star with a soft brush",
        "result": "the map was restored and the mechanism turned without tearing another constellation",
        "ending": "The real stars glittered overhead while the rescued paper star gleamed in its proper place.",
        "lesson": "even a small mystery deserves a pause before anyone reaches into moving parts",
    },
    {
        "name": "the breathing house",
        "opening": "The glasshouse seemed to breathe: its roof vents opened at noon and slammed shut at dusk.",
        "clue": "a bright ribbon was tangled around the vent-opening mechanism",
        "twist": "the mysterious flap was not a ghostly warning; a parade ribbon had caught the wind and pulled the lever",
        "danger": "Toby planned to climb the wet ladder to grab it",
        "action": "they closed the nearby door, called the gardener, and waited while an adult freed the ribbon",
        "result": "the vents opened gently, keeping the seedlings warm without risking a fall",
        "ending": "The glasshouse sighed in the evening light, and the seedlings stood safe beneath the clear roof.",
        "lesson": "when a mechanism is high or moving, friendship means stopping a risky rescue",
    },
    {
        "name": "the ticking parcel",
        "opening": "A parcel on the workshop floor ticked whenever someone walked past it.",
        "clue": "the ticking matched the rhythm of a loose spring inside a toy-making mechanism",
        "twist": "the parcel was not a secret timer; it held a friendly wooden bird whose clockwork wing had slipped",
        "danger": "Pip almost opened the parcel with a pocketknife",
        "action": "they read the label, asked the maker to inspect it, and carried it carefully to the workbench",
        "result": "the spring was replaced, and the wooden bird began flapping for the children's show",
        "ending": "The parcel opened into a bright wooden bird, and its cheerful tick became a song.",
        "lesson": "mysterious sounds should lead to questions, not dangerous guesses",
    },
)

DIALOGUES = (
    ("We should solve the mystery quickly", "We should solve it safely first"),
    ("I think the mechanism is broken", "Let us find out what changed before we decide"),
    ("That clue looks like a warning", "It may be a clue, but we still need evidence"),
    ("I can fix it myself", "A good friend stops you before a risky repair"),
    ("Someone must have done this", "Perhaps, but the mechanism may tell another story"),
    ("The mystery is getting bigger", "Then we will make our next step smaller and safer"),
)

OPENINGS = (
    "The mystery began with one sound that did not belong.",
    "Luna and a friend found the first clue before breakfast.",
    "A quiet place became puzzling when its mechanism changed rhythm.",
    "The first sign was small, but it made everyone stop and listen.",
    "No one expected a friendship test to hide inside an ordinary machine.",
)

ASP_RULES = r"""
kind(mechanism).
kind(friendship).
kind(cautionary).
kind(twist).
kind(mystery).

feature(mechanism) :- kind(mechanism).
feature(friendship) :- kind(friendship).
feature(cautionary) :- kind(cautionary).
feature(twist) :- kind(twist).
feature(mystery) :- kind(mystery).

setting(clockwork_garden).
setting(old_ferry_shed).
setting(hilltop_observatory).
setting(glasshouse).

safe_setting(P) :- setting(P).

story_ready(P) :-
    safe_setting(P),
    feature(mechanism),
    feature(friendship),
    feature(cautionary),
    feature(twist),
    feature(mystery).

#show story_ready/1.
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
        description="A mystery storyworld about mechanisms, friendship, and careful choices."
    )
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


def asp_facts() -> str:
    import asp

    return "\n".join(
        asp.fact("setting", place.replace(" ", "_")) for place in PLACES
    )


def asp_program(show: str = "#show story_ready/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_ready() -> set[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "story_ready"))


def asp_verify() -> int:
    expected = {(place.replace(" ", "_"),) for place in PLACES}
    actual = asp_ready()
    if expected == actual:
        print(f"OK: clingo gate matches Python reasoning ({len(actual)} settings).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(actual - expected))
    print("only in python:", sorted(expected - actual))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(tuple(PLACES))
    if place not in PLACES:
        raise StoryError(f"Unknown place: {place}")
    hero = rng.choice(CHAR_NAMES)
    friend = rng.choice([name for name in CHAR_NAMES if name != hero])
    mood = rng.choice(MOODS)
    return StoryParams(place=place, hero=hero, friend=friend, mood=mood)


def story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    key = "|".join((params.place, params.hero, params.friend, params.mood))
    return int.from_bytes(hashlib.blake2b(key.encode(), digest_size=8).digest(), "big")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"The place {params.place!r} is not in the story registry.")
    if params.hero == params.friend:
        raise StoryError("The hero and friend must be different people.")

    seed = story_seed(params)
    rng = random.Random(seed)
    case = CASES[seed % len(CASES)]
    opening = OPENINGS[(seed // len(CASES)) % len(OPENINGS)]
    dialogue = DIALOGUES[
        (seed // (len(CASES) * len(OPENINGS))) % len(DIALOGUES)
    ]
    meta = PLACES[params.place]

    world = World(place=meta["setting"])
    hero = Entity(
        id=params.hero,
        kind="character",
        label="mystery solver",
        type="hero",
        location=params.place,
        meters={"alertness": 1.0},
        memes={"curiosity": 1.0},
    )
    friend = Entity(
        id=params.friend,
        kind="character",
        label="friend",
        type="friend",
        location=params.place,
        meters={"alertness": 0.8},
        memes={"loyalty": 1.0},
    )
    machine = Entity(
        id="mechanism",
        kind="object",
        label=meta["mechanism"],
        type="mechanism",
        location=params.place,
        meters={"motion": 0.5},
        memes={"mystery": 1.0},
    )
    world.entities = {item.id: item for item in (hero, friend, machine)}

    world.say(opening)
    world.say(
        f"{params.hero}, a {params.mood} young detective, visited {world.place} "
        f"with {params.friend}, their best friend."
    )
    world.say(
        f"They came to inspect {meta['mechanism']}, which had begun behaving strangely."
    )
    world.say(case["opening"])

    world.para()
    world.say(
        f"The mechanism made a small, uneven sound. {params.hero} and {params.friend} "
        f"examined it without putting their fingers near the moving parts."
    )
    world.say(f"They found that {case['clue']}.")
    world.say(
        f"'{dialogue[0]},' said {params.hero}. "
        f"'{dialogue[1]},' answered {params.friend}."
    )
    world.say(
        f"{params.friend} noticed that {case['danger']}. "
        "That was the moment their friendship mattered more than being first to solve the puzzle."
    )

    world.para()
    world.say(
        "Together, they listed what they knew, what they guessed, and what still needed checking."
    )
    world.say(f"Then came the twist: {case['twist']}.")
    world.say(
        f"The mystery changed when they understood that the safest clue was also the clearest one."
    )

    world.para()
    world.say(f"{params.hero} and {params.friend} {case['action']}.")
    world.say(f"Because they stayed calm and helped each other, {case['result']}.")
    world.say(
        "They learned that a careful friend does not merely offer help; "
        "a careful friend also knows when to pause."
    )
    world.say(f"The lesson was simple: {case['lesson'].capitalize()}.")
    world.say(case["ending"])

    hero.meters["alertness"] = 1.5
    friend.meters["alertness"] = 1.3
    hero.memes["careful_reasoning"] = 1.0
    friend.memes["protective_friendship"] = 1.0
    machine.meters["motion"] = 1.0
    machine.memes["mystery_solved"] = 1.0

    world.trace = [
        f"noticed:{case['opening']}",
        f"clue:{case['clue']}",
        f"caution:{case['danger']}",
        f"twist:{case['twist']}",
        f"resolved:{case['result']}",
    ]
    world.facts = {
        "hero": params.hero,
        "friend": params.friend,
        "place": params.place,
        "setting": meta["setting"],
        "mechanism": meta["mechanism"],
        "case": case["name"],
        "clue": case["clue"],
        "danger": case["danger"],
        "twist": case["twist"],
        "resolution": case["result"],
        "lesson": case["lesson"],
    }

    prompts = [
        f"Write a child-friendly mystery about {meta['mechanism']} in {meta['setting']}.",
        f"Show how {params.hero} and {params.friend} use friendship and caution to solve {case['name']}.",
        "Include a mechanism, a surprising twist, a safe choice, and a clear lesson.",
    ]

    story_qa = [
        QAItem(
            question=f"What mystery did {params.hero} and {params.friend} investigate?",
            answer=f"They investigated {case['name']} involving {meta['mechanism']} in {meta['setting']}.",
        ),
        QAItem(
            question="What clue helped them understand the problem?",
            answer=f"They discovered that {case['clue']}. This physical clue helped them test their guesses.",
        ),
        QAItem(
            question="Why did they stop before taking a risky action?",
            answer=f"They stopped because {case['danger']}. Their friendship helped them choose a safer plan.",
        ),
        QAItem(
            question="What was the surprising twist?",
            answer=f"The twist was that {case['twist']}. The strange event had a different cause than they first imagined.",
        ),
        QAItem(
            question="How was the mystery resolved?",
            answer=f"They {case['action']}. As a result, {case['result']}.",
        ),
        QAItem(
            question="What lesson did the friends learn?",
            answer=f"They learned that {case['lesson']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of parts that work together to make something move, open, turn, or perform another job.",
        ),
        QAItem(
            question="How can a friend help during a mystery?",
            answer="A friend can notice clues, question a risky guess, and help choose a safe next step.",
        ),
        QAItem(
            question="Why should people be cautious around moving mechanisms?",
            answer="Moving mechanisms can pinch, pull, or swing unexpectedly, so people should keep clear and ask a trained adult for help when needed.",
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
        for event in sample.world.trace:
            print(f"  event: {event}")

    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(place="clockwork garden", hero="Luna", friend="Milo", mood="curious"),
    StoryParams(place="old ferry shed", hero="Nia", friend="Toby", mood="careful"),
    StoryParams(place="hilltop observatory", hero="Mara", friend="Pip", mood="patient"),
    StoryParams(place="glasshouse", hero="Iris", friend="Jasper", mood="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show story_ready/1."))
        print(asp.atoms(model, "story_ready"))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < args.n * 30:
            attempt += 1
            local_rng = random.Random(base_seed + attempt)
            params = resolve_params(args, local_rng)
            params.seed = base_seed + attempt
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
