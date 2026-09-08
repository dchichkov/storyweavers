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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = {
    "harbor fort": {
        "setting": "the old harbor fort",
        "shutter": "the historic west shutter",
        "safe": True,
    },
    "lighthouse quay": {
        "setting": "the lighthouse quay",
        "shutter": "the historic lantern-room shutter",
        "safe": True,
    },
    "seaglass museum": {
        "setting": "the seaglass museum",
        "shutter": "the historic gallery shutter",
        "safe": True,
    },
    "captain's cove": {
        "setting": "the captain's cove",
        "shutter": "the historic chart-room shutter",
        "safe": True,
    },
}

CHAR_NAMES = ("Luna", "Mara", "Finn", "Pip", "Nico", "Tessa", "Jory", "Bram")
MOODS = ("brave", "careful", "curious", "patient")
SHIPS = ("the Sea Star", "the Blue Gull", "the Kindred Crab", "the Dawn Skiff")

CASES = (
    {
        "name": "the stuck shutter",
        "opening": "A hard sea wind slammed the historic shutter shut before the harbor festival began.",
        "problem": "The festival lanterns and the old signal flag were trapped inside.",
        "clue": "salt had swollen the lower wooden hinge, while a loose rope had wrapped around the outside latch",
        "mistake": "wanted to force the whole shutter open with a heavy oar",
        "turn": "Luna noticed that the rope, not the iron bolt, was holding the shutter tight",
        "action": "they freed the rope with a boat hook, brushed sand from the hinge, and lifted together",
        "result": "the shutter opened without cracking its historic boards",
        "ending": "At sunset, the shutter rested open, and the festival lanterns winked across the water.",
        "lesson": "good friends solve a problem by sharing clues before choosing a strong action",
    },
    {
        "name": "the missing map",
        "opening": "The harbor crew needed the historic shutter opened because an old tide map hung behind it.",
        "problem": "Without the map, sailors might steer toward a shallow sandbar.",
        "clue": "a blue thread caught on the latch matched the ribbon used to tie the map case",
        "mistake": "searched every barrel for a thief before checking the shutter itself",
        "turn": "Luna realized the map case had been pulled against the shutter when the wind changed",
        "action": "they eased the shutter inward, rescued the map case, and tied it safely to a post",
        "result": "the crew could read the tide marks and guide the boats around the sandbar",
        "ending": "The map dried in the warm galley while friends watched the boats pass safely beyond the shoal.",
        "lesson": "friendship grows when people investigate together instead of blaming someone too soon",
    },
    {
        "name": "the gull's alarm",
        "opening": "A gull cried again and again above the historic shutter at the edge of the fort.",
        "problem": "The crew feared that a small bird was trapped behind the thick boards.",
        "clue": "feathers showed that the gull was perched outside, tugging at a bright ribbon caught in the shutter",
        "mistake": "planned to pull the shutter wide without first checking what was caught",
        "turn": "Luna asked everyone to hold still so they could see the ribbon's knot",
        "action": "they loosened the knot, lifted the ribbon free, and opened the shutter a finger at a time",
        "result": "the gull flew away and the historic wood remained unharmed",
        "ending": "The gull circled once over the fort, as if cheering for the careful crew below.",
        "lesson": "patient friends protect both people and precious things",
    },
    {
        "name": "the tide bell",
        "opening": "The tide bell should have rung, but its sound was muffled behind the historic shutter.",
        "problem": "Boats waiting outside could not hear the warning that shallow water was coming.",
        "clue": "the bell rope had slipped through a crack and caught around the shutter's inside peg",
        "mistake": "thought the bell itself had broken and reached for a hammer",
        "turn": "Luna traced the rope from the bell instead of guessing from the silence",
        "action": "they opened the shutter just enough to free the rope and tested the bell with a gentle pull",
        "result": "three clear rings warned the boats before the tide fell",
        "ending": "Three bright notes crossed the bay, and the friends grinned beside the open shutter.",
        "lesson": "following a problem back to its cause is better than striking at the nearest object",
    ),
    {
        "name": "the storm lantern",
        "opening": "A storm lantern flickered behind the historic shutter as dark clouds rolled over the bay.",
        "problem": "The harbor keeper needed the lantern before the fishing boats returned.",
        "clue": "the shutter's top pin had slipped sideways and blocked the only safe opening",
        "mistake": "wanted to climb the wet wall to reach the lantern from above",
        "turn": "Luna spotted the pin's bright brass end shining under the ledge",
        "action": "they used a dry wooden mallet, worked from the ground, and slid the pin back into its groove",
        "result": "the shutter opened safely and the lantern guided the boats home",
        "ending": "Warm light swept over the waves while friendship stood stronger than the storm.",
        "lesson": "friends can find a safer plan when they pause and use the clues around them",
    ),
)

OPENINGS = (
    "The sea was restless, and the old fort creaked in the wind.",
    "On a bright morning, the harbor seemed ready for an easy adventure.",
    "Before the first ship bell, a small problem appeared by the shore.",
    "The tide was turning when Luna heard a worried call from the dock.",
    "A pirate-style errand became a puzzle beside the oldest wall in town.",
)

DIALOGUES = (
    ("We should push harder", "Let us first find what is holding it"),
    ("I think the shutter is broken", "Maybe a smaller part is causing the trouble"),
    ("Friends, what did we actually see", "We saw a rope, a hinge, and a board that stayed still"),
    ("Can we fix this before the boats return", "Yes, if we share the work and stay careful"),
    ("I have a plan", "Tell us the clue that supports it"),
)

ASP_RULES = r"""
kind(historic).
kind(shutter).
kind(friendship).
kind(problem_solving).
kind(pirate_tale).

feature(friendship) :- kind(friendship).
feature(problem_solving) :- kind(problem_solving).
compatible(P) :- setting(P), historic_shutter(P), friendship, problem_solving.
safe_place(P) :- compatible(P).

setting("harbor_fort").
setting("lighthouse_quay").
setting("seaglass_museum").
setting("captains_cove").

historic_shutter("harbor_fort").
historic_shutter("lighthouse_quay").
historic_shutter("seaglass_museum").
historic_shutter("captains_cove").

#show compatible/1.
#show safe_place/1.
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
    ship: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        description="A small pirate-style storyworld about friendship and a historic shutter."
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

    lines = []
    for place in PLACES:
        key = place.replace(" ", "_").replace("'", "")
        lines.append(asp.fact("setting", key))
        lines.append(asp.fact("historic_shutter", key))
    return "\n".join(lines)


def asp_program(show: str = "#show compatible/1.\n#show safe_place/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    expected = {
        (place.replace(" ", "_").replace("'", ""),)
        for place in PLACES
    }
    model = asp.one_model(asp_program("#show compatible/1."))
    actual = set(asp.atoms(model, "compatible"))
    if actual != expected:
        print("MISMATCH:")
        print("only in clingo:", sorted(actual - expected))
        print("only in Python:", sorted(expected - actual))
        return 1
    print(f"OK: clingo gate matches Python reasoning ({len(actual)} places).")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(tuple(PLACES))
    if place not in PLACES:
        raise StoryError(f"Unknown harbor setting: {place}")
    hero = rng.choice(CHAR_NAMES)
    friend = rng.choice(tuple(name for name in CHAR_NAMES if name != hero))
    return StoryParams(
        place=place,
        hero=hero,
        friend=friend,
        mood=rng.choice(MOODS),
        ship=rng.choice(SHIPS),
        seed=args.seed,
    )


def _seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join(
        (params.place, params.hero, params.friend, params.mood, params.ship)
    )
    return int.from_bytes(hashlib.blake2b(text.encode(), digest_size=8).digest(), "big")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Cannot sail to an unregistered place: {params.place}")
    if params.hero == params.friend:
        raise StoryError("A friendship story needs two different friends.")

    seed = _seed(params)
    rng = random.Random(seed)
    place = PLACES[params.place]
    case = CASES[seed % len(CASES)]
    opening = OPENINGS[(seed // len(CASES)) % len(OPENINGS)]
    dialogue = DIALOGUES[
        (seed // (len(CASES) * len(OPENINGS))) % len(DIALOGUES)
    ]
    extra = rng.choice(
        (
            "They had sailed together long enough to know that a shared clue was worth more than a proud guess.",
            "Their friendship was their best compass, especially when the harbor offered more than one answer.",
            "They promised to leave every old board and brass fitting as safe as they had found it.",
            "Neither friend wanted to be captain of the solution alone.",
        )
    )

    world = World(place=place["setting"])
    hero = Entity(
        id=params.hero,
        kind="character",
        label="young sailor",
        type="sailor",
        meters={"balance": 1.0, "strength": 0.8},
        memes={"friendship": 1.0, "curiosity": 0.8},
        location=params.place,
    )
    friend = Entity(
        id=params.friend,
        kind="character",
        label="trusted friend",
        type="sailor",
        meters={"balance": 0.9, "strength": 0.8},
        memes={"friendship": 1.0, "patience": 0.8},
        location=params.place,
    )
    shutter = Entity(
        id="historic_shutter",
        kind="object",
        label=place["shutter"],
        type="shutter",
        meters={"stability": 0.7, "openness": 0.0},
        memes={"history": 1.0, "needs_care": 1.0},
        location=params.place,
    )
    ship = Entity(
        id="ship",
        kind="vehicle",
        label=params.ship,
        type="sailing_ship",
        meters={"distance": 30.0, "safety": 0.7},
        memes={"trust": 1.0},
        location="harbor",
    )
    world.entities = {
        hero.id: hero,
        friend.id: friend,
        shutter.id: shutter,
        ship.id: ship,
    }

    world.say(opening)
    world.say(
        f"{params.hero}, a {params.mood} deckhand, walked along {world.place} "
        f"with {params.friend}, the friend who always noticed small details."
    )
    world.say(extra)
    world.say(case["opening"])

    world.para()
    world.say(case["problem"])
    world.say(
        f"The {case['name']} looked simple until {params.friend} noticed that "
        f"{case['clue']}."
    )
    world.say(f"'{dialogue[0]},' said {params.hero}. '{dialogue[1]},' answered {params.friend}.")
    world.say(
        f"At first, {params.hero} {case['mistake']}. "
        "The plan would have damaged the historic wood."
    )

    world.para()
    world.say(
        f"Then {params.hero} and {params.friend} shared what each one had seen. "
        f"{case['turn']}."
    )
    world.say(
        f"That was the turning point: they stopped fighting the whole shutter "
        "and searched for the small cause of the trouble."
    )
    world.say(
        f"Together, they {case['action']}. Their teamwork kept the old boards safe."
    )

    world.para()
    world.say(
        f"Because the friends solved the puzzle carefully, {case['result']}. "
        f"The waiting crew aboard {params.ship} gave a grateful cheer."
    )
    world.say(
        f"{params.hero} laughed. 'We made a fine crew.' "
        f"{params.friend} replied, 'Friends make the best problem-solving team.'"
    )
    world.say(f"The lesson of the voyage was this: {case['lesson'].capitalize()}.")
    world.say(case["ending"])

    hero.meters["balance"] = 1.0
    friend.meters["balance"] = 1.0
    shutter.meters["openness"] = 1.0
    shutter.meters["stability"] = 0.85
    hero.memes["confidence"] = 1.0
    friend.memes["confidence"] = 1.0
    hero.memes["friendship"] = 1.5
    friend.memes["friendship"] = 1.5
    ship.meters["safety"] = 1.0

    world.trace = [
        f"problem:{case['problem']}",
        f"clue:{case['clue']}",
        f"first_plan:{case['mistake']}",
        f"turn:{case['turn']}",
        f"repair:{case['action']}",
        f"outcome:{case['result']}",
    ]
    world.facts = {
        "place": params.place,
        "setting": place["setting"],
        "historic_object": place["shutter"],
        "hero": params.hero,
        "friend": params.friend,
        "ship": params.ship,
        "case": case["name"],
        "problem": case["problem"],
        "clue": case["clue"],
        "turn": case["turn"],
        "resolution": case["result"],
        "lesson": case["lesson"],
    }

    prompts = [
        f"Write a child-friendly pirate tale in {place['setting']} about friendship and problem solving.",
        f"Tell how {params.hero} and {params.friend} safely opened {place['shutter']}.",
        f"Create a historic harbor mystery involving {params.ship}, a shutter, and two friends who share clues.",
    ]

    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} and {params.friend} face?",
            answer=f"They had to deal with {case['problem']} at {place['shutter']}.",
        ),
        QAItem(
            question="What clue helped them understand the problem?",
            answer=f"They noticed that {case['clue']}. This showed them where the trouble really was.",
        ),
        QAItem(
            question=f"What did {params.hero} first want to do?",
            answer=f"{params.hero} {case['mistake']}, but that could have harmed the historic shutter.",
        ),
        QAItem(
            question=f"How did the friends solve the problem?",
            answer=f"They {case['action']}. Their shared plan protected the old wood.",
        ),
        QAItem(
            question="What did the story teach about friendship?",
            answer=f"It taught that {case['lesson']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a panel that can cover a window or opening, protecting it from wind, light, or danger.",
        ),
        QAItem(
            question="What does historic mean?",
            answer="Historic means important because it belongs to the past and helps people remember earlier times.",
        ),
        QAItem(
            question="Why is problem solving useful on a ship?",
            answer="Problem solving helps a crew understand a difficulty, choose a safe plan, and work together before the ship or its passengers are put at risk.",
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
    StoryParams("harbor fort", "Luna", "Mara", "brave", "the Sea Star"),
    StoryParams("lighthouse quay", "Finn", "Tessa", "careful", "the Blue Gull"),
    StoryParams("seaglass museum", "Nico", "Pip", "curious", "the Dawn Skiff"),
    StoryParams("captain's cove", "Jory", "Bram", "patient", "the Kindred Crab"),
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

        model = asp.one_model(asp_program())
        print(asp.atoms(model, "compatible"))
        print(asp.atoms(model, "safe_place"))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        for index in range(args.n):
            local = random.Random(base_seed + index)
            params = resolve_params(args, local)
            params.seed = base_seed + index
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
