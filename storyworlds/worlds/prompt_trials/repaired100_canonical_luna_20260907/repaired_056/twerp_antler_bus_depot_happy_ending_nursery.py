#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = {
    "bus depot": {
        "setting": "the busy bus depot",
        "features": ("covered bays", "a lost-and-found shelf", "a bright departure board"),
    },
}

CHARACTERS = ("Luna", "Milo", "Pip", "Nell", "Toby", "Mara")
MOODS = ("cheerful", "careful", "sleepy", "brave", "curious")
NURSERY_RHYME_OPENINGS = (
    "At the depot by the gate, the buses hummed and did not wait.",
    "Down by the depot, bright and neat, little wheels went tap-tap-tweet.",
    "At dawn in the depot, beneath the blue sky, a small puzzle rolled by.",
    "Hush-a-bus and toot-a-tune, a curious riddle came at noon.",
)
CASES = (
    {
        "name": "the antler sign mix-up",
        "opening": "A cardboard antler sign had slipped from a bus window and blocked the number board.",
        "twerp": "a tiny, bouncy twerp of a helper",
        "mistake": "thought the antler was part of a runaway animal hiding among the buses",
        "clue": "the antler had painted letters on its flat cardboard side",
        "turn": "it was a costume sign for the bus depot's woodland play",
        "action": "lifted the light sign and carried it to the lost-and-found shelf",
        "result": "the driver could read the departure number again and the play's little deer costume was complete",
        "ending": "The bus went toot-toot down the lane, while the cardboard antler winked beside the happy play.",
        "lesson": "look closely before turning a funny shape into a frightening story",
    },
    {
        "name": "the antler parcel",
        "opening": "A wrapped parcel marked with an antler sat beneath a bench, and nobody knew which bus should carry it.",
        "twerp": "a friendly little twerp with quick feet",
        "mistake": "tried to follow the antler mark as though it were a trail through the depot",
        "clue": "the mark matched the antler logo on the northbound bus",
        "turn": "the antler was a delivery symbol, not a creature's footprint",
        "action": "asked the driver, checked the label, and placed the parcel in the northbound luggage rack",
        "result": "the parcel reached the children's winter show safely",
        "ending": "The northbound bus rolled away with a merry beep, and the depot bell chimed, 'All is well!'",
        "lesson": "a picture can be a label as well as a clue",
    },
    {
        "name": "the missing costume",
        "opening": "The nursery show was nearly ready, but its wooden antler had vanished from the prop basket.",
        "twerp": "a soft-hearted twerp who loved helping",
        "mistake": "imagined that a real antler had wandered onto a bus",
        "clue": "a trail of sawdust led from the basket to the depot's repair table",
        "turn": "the antler had been taken for a quick smoothing, not stolen at all",
        "action": "found the carpenter, polished the prop, and returned it before the performers arrived",
        "result": "the little deer could bow proudly in the final song",
        "ending": "Clap-clap went the children, and the deer bowed low as the buses sang along.",
        "lesson": "a calm search can turn a worry into a welcome surprise",
    },
)

DIALOGUES = (
    ("'That antler looks alive!'", "'Let us ask what it is made for before we guess.'"),
    ("'I am a twerp, but I can still inspect a label!'", "'Good helpers use eyes, ears, and kind questions.'"),
    ("'Should we chase it?'", "'No need to chase a thing that is safely standing still.'"),
    ("'The bus must know where it belongs.'", "'Then the driver and the label can tell us.'"),
)

MOVES = (
    "They counted the bus bays, listened to the drivers, and checked the nearest labels.",
    "They paused beside the timetable and separated what they knew from what they guessed.",
    "They looked at the shape, the material, and the place where the clue had been found.",
    "They asked a gentle question instead of making a noisy guess.",
)

ASP_RULES = r"""
kind(twerp).
kind(antler).
feature(happy_ending).
style(nursery_rhyme).
setting(bus_depot).
has_seed_word(twerp).
has_seed_word(antler).
supports(bus_depot, twerp).
supports(bus_depot, antler).
story_ok(bus_depot) :- supports(bus_depot, twerp), supports(bus_depot, antler), feature(happy_ending), style(nursery_rhyme).
#show supports/2.
#show story_ok/1.
"""


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    mood: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A nursery-rhyme storyworld at a bus depot.")
    parser.add_argument("--place", choices=tuple(PLACES), default=None)
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
        (
            asp.fact("supports", "bus_depot", "twerp"),
            asp.fact("supports", "bus_depot", "antler"),
        )
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/1."))
    found = set(asp.atoms(model, "story_ok"))
    expected = {("bus_depot",)}
    if found == expected:
        print("OK: ASP story gate matches Python reasoning.")
        return 0
    print("MISMATCH:")
    print("ASP:", sorted(found))
    print("Python:", sorted(expected))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "bus depot"
    if place not in PLACES:
        raise StoryError(f"Unknown place: {place}")
    hero = rng.choice(CHARACTERS)
    helper = rng.choice([name for name in CHARACTERS if name != hero])
    mood = rng.choice(MOODS)
    return StoryParams(place=place, hero=hero, helper=helper, mood=mood, seed=args.seed)


def story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    raw = "|".join((params.place, params.hero, params.helper, params.mood))
    return int.from_bytes(hashlib.blake2b(raw.encode(), digest_size=8).digest(), "big")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("This story must take place in the bus depot.")
    rng = random.Random(story_seed(params))
    case = CASES[story_seed(params) % len(CASES)]
    opening = NURSERY_RHYME_OPENINGS[rng.randrange(len(NURSERY_RHYME_OPENINGS))]
    dialogue = DIALOGUES[rng.randrange(len(DIALOGUES))]
    move = MOVES[rng.randrange(len(MOVES))]
    place = PLACES[params.place]

    hero = Entity(
        id=params.hero,
        kind="character",
        label="young helper",
        location=params.place,
        meters={"energy": 1.0, "distance_walked": 0.0},
        memes={"curiosity": 1.0, "kindness": 0.8},
    )
    helper = Entity(
        id=params.helper,
        kind="character",
        label=case["twerp"],
        location=params.place,
        meters={"energy": 0.9, "distance_walked": 0.0},
        memes={"cheer": 1.0, "helpfulness": 1.0},
    )
    antler = Entity(
        id="antler",
        kind="prop",
        label="antler",
        location=params.place,
        meters={"weight": 0.2},
        memes={"mystery": 1.0, "safe": 1.0},
    )
    bus = Entity(
        id="bus",
        kind="vehicle",
        label="northbound bus",
        location=params.place,
        meters={"wheels": 4.0},
        memes={"ready": 0.0},
    )
    world = World(place=place["setting"], entities={e.id: e for e in (hero, helper, antler, bus)})

    world.say(opening)
    world.say(
        f"{params.hero}, feeling {params.mood}, was helping at {world.place} with {params.helper}, "
        f"{case['twerp']}. Around them were {place['features'][0]}, {place['features'][1]}, and {place['features'][2]}."
    )
    world.say(case["opening"])
    world.say(f"{params.helper} whispered, {dialogue[0]} {params.hero} answered, {dialogue[1]}")
    world.say(f"They made a first guess: {params.helper} {case['mistake']}.")
    world.para()

    world.say(move)
    world.say(f"Then they noticed that {case['clue']}.")
    world.say(f"The antler was not a wild danger; {case['turn']}.")
    world.say(f"{params.hero} said, 'Now we know what to do.' {params.helper} replied, 'Twerp or not, I can help!'")
    world.para()

    world.say(f"Together, they {case['action']}.")
    world.say(f"Because they checked before rushing, {case['result']}.")
    world.say(f"The happy ending came with a rhyme: {case['ending']}")
    world.say("They learned that a small question can make a large worry grow small.")

    hero.meters["distance_walked"] = 12.0
    hero.memes["confidence"] = 1.0
    helper.meters["distance_walked"] = 9.0
    helper.memes["confidence"] = 1.0
    antler.memes["mystery"] = 0.0
    antler.memes["understood"] = 1.0
    bus.memes["ready"] = 1.0

    world.trace = [
        "found:twerp",
        "found:antler",
        f"misunderstood:{case['mistake']}",
        f"observed:{case['clue']}",
        f"understood:{case['turn']}",
        f"resolved:{case['result']}",
    ]
    world.facts = {
        "setting": params.place,
        "hero": params.hero,
        "helper": params.helper,
        "seed_words": "twerp, antler",
        "case": case["name"],
        "clue": case["clue"],
        "turn": case["turn"],
        "resolution": case["result"],
        "feature": "Happy Ending",
        "style": "Nursery Rhyme",
    }

    prompts = [
        f"Write a Nursery Rhyme style story at a bus depot using the words twerp and antler.",
        f"Tell how {params.hero} and {params.helper} solve {case['name']} without rushing.",
        "Include a spoken back-and-forth, a misunderstanding, a safe discovery, and a happy ending.",
    ]
    story_qa = [
        QAItem(
            question="Where did the story happen?",
            answer="It happened at the busy bus depot, among the bus bays, timetable, and departure board.",
        ),
        QAItem(
            question="What were the two special seed words?",
            answer="The two seed words were twerp and antler.",
        ),
        QAItem(
            question="What did the characters first misunderstand?",
            answer=f"They first misunderstood the antler because {case['mistake']}.",
        ),
        QAItem(
            question="What clue changed their minds?",
            answer=f"They noticed that {case['clue']}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"They {case['action']}, and {case['result']}. The ending was happy because everyone and everything was safe.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a bus depot?",
            answer="A bus depot is a place where buses park, receive care, and begin or end their routes.",
        ),
        QAItem(
            question="What is an antler?",
            answer="An antler is a branching growth found on animals such as deer, though a story may also use an antler-shaped prop or sign.",
        ),
        QAItem(
            question="What does twerp mean in this story?",
            answer="Here, twerp is a playful word for a small, lively helper; it is not a reason to treat anyone unkindly.",
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
            print(
                f"  {entity.id}: {entity.kind}; location={entity.location}; "
                f"meters={entity.meters}; memes={entity.memes}"
            )
        for item in sample.world.trace:
            print(f"  event: {item}")
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


CURATED = [
    StoryParams(place="bus depot", hero="Luna", helper="Milo", mood="cheerful"),
    StoryParams(place="bus depot", hero="Pip", helper="Nell", mood="careful"),
    StoryParams(place="bus depot", hero="Toby", helper="Mara", mood="curious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show supports/2.\n#show story_ok/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show supports/2.\n#show story_ok/1."))
        print(asp.atoms(model, "supports"))
        print(asp.atoms(model, "story_ok"))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")
    seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        for index in range(args.n):
            local_rng = random.Random(seed + index)
            params = resolve_params(args, local_rng)
            params.seed = seed + index
            sample = generate(params)
            if sample.story in seen:
                params.seed += 1000003
                sample = generate(params)
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
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
