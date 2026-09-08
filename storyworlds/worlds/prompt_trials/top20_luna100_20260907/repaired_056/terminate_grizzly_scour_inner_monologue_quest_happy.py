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
    "sunrise canyon": {
        "setting": "the bright canyon",
        "hazard": "a runaway storm machine",
        "landmark": "the Echo Bridge",
    },
    "pine valley": {
        "setting": "the green pine valley",
        "hazard": "a roaring rescue beacon",
        "landmark": "the old ranger tower",
    },
    "moonlit harbor": {
        "setting": "the silver harbor",
        "hazard": "a giant fog projector",
        "landmark": "the lighthouse hill",
    },
    "redwood park": {
        "setting": "the tall redwood park",
        "hazard": "a runaway drilling robot",
        "landmark": "the hidden grove",
    },
}

HEROES = ("Luna", "Nova", "Mira", "Sol", "Aria", "Juno")
PARTNERS = ("Pip", "Milo", "Tess", "Ravi", "Bee", "Kito")
MOODS = ("brave", "careful", "hopeful", "curious")
POWERS = {
    "star shield": "a shining star shield",
    "wind leap": "a powerful wind leap",
    "kindness beam": "a warm kindness beam",
    "moon rope": "a silver moon rope",
}

MISSIONS = (
    {
        "call": "A deep growl rolled through the trees, and the town alarm flashed three times.",
        "grizzly": "A frightened grizzly had become tangled beside the machine, and its growls shook the ground.",
        "scour": "Luna had to scour the canyon floor for the missing control crystal.",
        "clue": "silver paw marks led from the grizzly's den to a fallen supply cart",
        "turn": "the crystal was not lost at all; the grizzly had nudged it under the cart while trying to escape the noise",
        "action": "Luna used her moon rope to pull the cart away, then raised her star shield between the bear and the machine",
        "result": "the grizzly lumbered into a quiet cave while the control crystal clicked safely into Luna's glove",
        "ending": "At sunset, the bear found honey near the cave, and the valley glowed peacefully below.",
        "lesson": "a strong hero protects frightened creatures as well as people",
    },
    {
        "call": "A red warning light blinked above the village, and a metal voice shouted, 'Terminate the danger!'",
        "grizzly": "A huge grizzly stood between the heroes and the warning tower, guarding two cubs beneath a bush.",
        "scour": "Luna began to scour the hillside for a safe path around the family.",
        "clue": "the grizzly kept glancing toward a loose cable sparking beside the tower",
        "turn": "the bear was not attacking the village; it was warning everyone about the dangerous cable",
        "action": "Luna sent a kindness beam toward the cubs, guided the grizzly away, and used her wind leap to reach the tower switch",
        "result": "the warning system shut down without harming the bear or its cubs",
        "ending": "The grizzly family disappeared into the pines, and the village lights twinkled like friendly stars.",
        "lesson": "understanding a warning can turn an enemy-looking problem into a rescue",
    },
    {
        "call": "The harbor bells rang wildly when a wall of purple fog rolled toward the boats.",
        "grizzly": "A traveling grizzly mascot had been trapped on a floating stage and was roaring for help.",
        "scour": "Luna had to scour the docks for the fog projector's hidden power key.",
        "clue": "wet paw prints crossed the dock and stopped beside a crate marked with a moon",
        "turn": "the mascot had carried the key away from the projector while trying to protect the children nearby",
        "action": "Luna lifted the crate with her wind leap and used the moon rope to bring the key back",
        "result": "the projector stopped, the fog lifted, and the grizzly mascot waved to the cheering crowd",
        "ending": "Boats sailed beneath a clear moon, and the rescued mascot shared bright paper stars with everyone.",
        "lesson": "a quest succeeds when courage is guided by careful clues",
    },
    {
        "call": "A thunderous thump woke the redwoods, and a trail of glowing bolts led into the grove.",
        "grizzly": "A real grizzly had wandered near the bolts and was roaring because its fishing stream had gone dry.",
        "scour": "Luna promised to scour the grove for whatever had blocked the stream.",
        "clue": "fresh wood chips circled a fallen log wedged across the narrow waterway",
        "turn": "the drilling robot had pushed the log aside and accidentally dammed the stream",
        "action": "Luna raised her star shield, signaled the robot to stop, and guided it while it cleared the log",
        "result": "water rushed back to the grizzly's fishing pool and the robot's warning lights turned green",
        "ending": "The grizzly splashed happily in the restored stream while Luna accepted a berry-bright thank-you.",
        "lesson": "even a noisy machine can become a helper when someone teaches it what to do",
    },
)

DIALOGUE = (
    ("We can terminate the danger without hurting anyone", "Then let us look for the safest way"),
    ("That grizzly sounds angry", "It may be scared, so we should listen before we leap"),
    ("I will scour every path", "I will watch the clues and keep the path safe"),
    ("My power is strong", "Your careful choice makes it truly heroic"),
    ("The quest feels too big", "One brave step and one kind question can begin it"),
    ("Should we rush in", "No. A hero notices who might need protection first"),
)

ASP_RULES = r"""
kind(terminate).
kind(grizzly).
kind(scour).
feature(inner_monologue).
feature(quest).
feature(happy_ending).
style(superhero_story).

place("sunrise_canyon").
place("pine_valley").
place("moonlit_harbor").
place("redwood_park").

mission("sunrise_canyon", "grizzly").
mission("pine_valley", "grizzly").
mission("moonlit_harbor", "grizzly").
mission("redwood_park", "grizzly").

safe_quest(P) :- place(P), mission(P, "grizzly").
complete(P) :- safe_quest(P).

#show safe_quest/1.
#show complete/1.
"""


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: Optional[str] = None
    carried_by: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    hero: str
    partner: str
    mood: str
    power: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A gentle superhero quest with a grizzly.")
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
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place.replace(" ", "_")))
        lines.append(asp.fact("mission", place.replace(" ", "_"), "grizzly"))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    python = {(place.replace(" ", "_"),) for place in PLACES}
    model = asp.one_model(asp_program("#show safe_quest/1."))
    clingo = set(asp.atoms(model, "safe_quest"))
    if python == clingo:
        print(f"OK: clingo gate matches Python reasoning ({len(clingo)} quests).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(clingo - python))
    print("only in python:", sorted(python - clingo))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(tuple(PLACES))
    if place not in PLACES:
        raise StoryError(f"Unknown quest place: {place}.")
    hero = rng.choice(HEROES)
    partner = rng.choice([name for name in PARTNERS if name != hero])
    mood = rng.choice(MOODS)
    power = rng.choice(tuple(POWERS))
    return StoryParams(place=place, hero=hero, partner=partner, mood=mood, power=power)


def _story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    identity = "|".join((params.place, params.hero, params.partner, params.mood, params.power))
    return int.from_bytes(hashlib.blake2b(identity.encode(), digest_size=8).digest(), "big")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("The quest needs a known place.")
    if params.hero == params.partner:
        raise StoryError("The hero and partner must be different characters.")
    if params.power not in POWERS:
        raise StoryError("The hero must have a registered power.")

    seed = _story_seed(params)
    rng = random.Random(seed)
    mission = MISSIONS[seed % len(MISSIONS)]
    dialogue = DIALOGUE[(seed // len(MISSIONS)) % len(DIALOGUE)]
    meta = PLACES[params.place]
    world = World(place=meta["setting"])

    hero = Entity(
        id=params.hero,
        kind="character",
        label="superhero",
        type="hero",
        meters={"energy": 1.0, "distance": 0.0},
        memes={"courage": 1.0, "kindness": 0.8},
        location=params.place,
    )
    partner = Entity(
        id=params.partner,
        kind="character",
        label="trusted partner",
        type="helper",
        meters={"energy": 0.8, "distance": 0.0},
        memes={"care": 1.0, "curiosity": 0.8},
        location=params.place,
    )
    grizzly = Entity(
        id="grizzly",
        kind="animal",
        label="frightened grizzly",
        type="bear",
        meters={"distance": 12.0, "fear": 1.0},
        memes={"trust": 0.1, "relief": 0.0},
        location=params.place,
    )
    world.entities = {entity.id: entity for entity in (hero, partner, grizzly)}

    world.say(f"In {meta['setting']}, {params.hero} was a {params.mood} superhero with {POWERS[params.power]}.")
    world.say(f"{params.partner} helped from the ground while the town rested beneath {meta['landmark']}.")
    world.say(mission["call"])
    world.say(f"{params.hero} heard the alarm and thought, 'I must terminate the danger, but I must not make a frightened creature feel more afraid.'")
    world.say(f"That inner thought became a promise: the quest would protect everyone, including the grizzly.")
    world.say(f"{params.hero} said, '{dialogue[0]}.' {params.partner} answered, '{dialogue[1]}.'")

    world.para()
    world.say(mission["grizzly"])
    world.say(f"{params.hero} began to scour the area while {params.partner} watched the safe path. {mission['scour']}")
    world.say(f"They found that {mission['clue']}.")
    world.say(f"{params.hero} thought, 'The loudest thing is not always the real villain. I should understand the clue before using my power.'")
    world.say(f"Then the turning point became clear: {mission['turn']}.")
    world.say(f"'{params.partner}, stay close to the cubs and keep your voice gentle,' said {params.hero}. '{params.hero}, I will,' replied {params.partner}.")
    world.say(f"Together, they {mission['action']}.")

    world.para()
    world.say(f"The danger ended because {mission['result']}.")
    world.say(f"The grizzly's fear softened into trust, and the heroes' careful quest became a rescue instead of a battle.")
    world.say(f"{mission['lesson'].capitalize()}.")
    world.say(mission["ending"])
    world.say(f"{params.hero} smiled and thought, 'A happy ending is brightest when everyone gets to go home safely.'")

    hero.meters["energy"] = 0.7
    hero.meters["distance"] = 1.0
    hero.memes["wisdom"] = 1.0
    partner.meters["energy"] = 0.7
    partner.meters["distance"] = 1.0
    grizzly.meters["fear"] = 0.0
    grizzly.memes["trust"] = 1.0
    grizzly.memes["relief"] = 1.0

    world.trace = [
        "received:danger signal",
        "noticed:grizzly fear",
        "scoured:local paths",
        f"discovered:{mission['turn']}",
        f"resolved:{mission['result']}",
        "ending:happy and safe",
    ]
    world.facts = {
        "place": params.place,
        "setting": meta["setting"],
        "hero": params.hero,
        "partner": params.partner,
        "power": params.power,
        "mission": mission["lesson"],
        "grizzly": mission["grizzly"],
        "clue": mission["clue"],
        "turn": mission["turn"],
        "resolution": mission["result"],
    }

    prompts = [
        f"Write a child-friendly superhero quest in {meta['setting']} where {params.hero} must terminate a danger without hurting a grizzly.",
        f"Include an inner monologue, a careful scour for clues, a brief dialogue between {params.hero} and {params.partner}, and a happy ending.",
        f"Tell how {params.hero}'s {params.power} helps solve a grizzly rescue rather than start a battle.",
    ]
    story_qa = [
        QAItem(
            question=f"Why did {params.hero} begin the quest?",
            answer=f"{params.hero} began the quest because a danger threatened {meta['setting']}, and the hero wanted to protect both the people and the grizzly.",
        ),
        QAItem(
            question="What did the heroes discover while they scoured the area?",
            answer=f"They discovered that {mission['clue']}. This clue showed them what was really causing the trouble.",
        ),
        QAItem(
            question="What changed the heroes' plan?",
            answer=f"They learned that {mission['turn']}. The grizzly was frightened or helpful rather than the true enemy.",
        ),
        QAItem(
            question="How did the quest end?",
            answer=f"{mission['result']}. The danger ended and the grizzly was safe.",
        ),
        QAItem(
            question="What made the ending happy?",
            answer="The heroes solved the danger without harming the grizzly, so the people, the animals, and the heroes could all be safe.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does it mean to terminate a danger?",
            answer="To terminate a danger means to stop it or bring it to an end so people and animals are safe.",
        ),
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large brown bear. It should be treated with distance and respect.",
        ),
        QAItem(
            question="What does scour mean?",
            answer="To scour means to search an area carefully and thoroughly for something.",
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
            details = [f"type={entity.type}", f"location={entity.location}"]
            if entity.meters:
                details.append(f"meters={entity.meters}")
            if entity.memes:
                details.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {' '.join(details)}")
        for item in sample.world.trace:
            print(f"  event: {item}")
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


CURATED = [
    StoryParams("sunrise canyon", "Luna", "Pip", "brave", "star shield"),
    StoryParams("pine valley", "Nova", "Tess", "careful", "kindness beam"),
    StoryParams("moonlit harbor", "Mira", "Ravi", "hopeful", "moon rope"),
    StoryParams("redwood park", "Sol", "Bee", "curious", "wind leap"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_quest/1.\n#show complete/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show safe_quest/1.\n#show complete/1."))
        print(asp.atoms(model, "safe_quest"))
        print(asp.atoms(model, "complete"))
        return
    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen = set()
        for index in range(args.n):
            params = resolve_params(args, random.Random(rng.randrange(2**63)))
            params.seed = (args.seed if args.seed is not None else 0) + index
            sample = generate(params)
            while sample.story in seen:
                params.seed += 1
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
