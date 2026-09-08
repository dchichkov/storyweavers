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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = {
    "clockwork greenhouse": {
        "setting": "the clockwork greenhouse",
        "mechanism": "a brass watering mechanism",
        "hazard": "a loose gear could pinch a finger",
        "safe_tool": "a wooden wedge",
        "landmark": "the moon-shaped vent",
    },
    "old ferry shed": {
        "setting": "the old ferry shed",
        "mechanism": "a rope-and-pulley lift",
        "hazard": "a sudden drop could spill the cargo",
        "safe_tool": "a locking peg",
        "landmark": "the red oar rack",
    },
    "hilltop observatory": {
        "setting": "the hilltop observatory",
        "mechanism": "a turning star map",
        "hazard": "the heavy panel could swing down",
        "safe_tool": "a canvas strap",
        "landmark": "the silver dome",
    },
    "toy repair room": {
        "setting": "the toy repair room",
        "mechanism": "a spring-powered music box",
        "hazard": "the spring could snap free",
        "safe_tool": "a padded clamp",
        "landmark": "the blue workbench",
    },
}

NAMES = ("Luna", "Milo", "Nia", "Owen", "Tess", "Pip", "Mara", "Jasper")
MOODS = ("curious", "careful", "brave", "patient")
CLUES = (
    "a faint click came from behind the painted panel",
    "dust rested on every gear except one bright tooth",
    "a blue thread was caught on the lower pulley",
    "the warning bell rang only when the handle was pulled twice",
    "a tiny footprint stopped beside the locked cabinet",
    "the same scratch appeared on the latch and on the missing sign",
)
DIALOGUE = (
    ("We should follow the noise", "We should first make sure the mechanism is safe"),
    ("I think someone broke it", "A clue is not the same as a conclusion"),
    ("You can trust me to help", "Then let us protect each other while we investigate"),
    ("The door was locked", "A locked door can still hide a moving part"),
    ("What if our guess is wrong", "Then our careful test will show us"),
    ("I found the answer", "You found an idea; now let us find proof"),
)
OPENINGS = (
    "The mystery began when an ordinary machine made an impossible sound.",
    "Before breakfast, a warning bell rang in a room that was supposed to be quiet.",
    "Luna and a friend were checking an old mechanism when a small secret slipped into view.",
    "A missing object, a locked cabinet, and one turning gear started the day's puzzle.",
)
LESSONS = (
    "good friends protect one another from danger instead of racing toward a mystery",
    "a mechanism should be observed before anyone touches its moving parts",
    "the first explanation is only a guess until the clues support it",
    "caution is part of courage, especially when a hidden machine is involved",
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

safe(place) :- setting(place), has_tool(place), has_guard(place).
usable_mechanism(place) :- setting(place), safe(place).
story_ready(place) :- usable_mechanism(place), supports_friendship(place), has_twist(place).

setting("clockwork_greenhouse").
setting("old_ferry_shed").
setting("hilltop_observatory").
setting("toy_repair_room").

has_tool("clockwork_greenhouse").
has_tool("old_ferry_shed").
has_tool("hilltop_observatory").
has_tool("toy_repair_room").

has_guard("clockwork_greenhouse").
has_guard("old_ferry_shed").
has_guard("hilltop_observatory").
has_guard("toy_repair_room").

supports_friendship("clockwork_greenhouse").
supports_friendship("old_ferry_shed").
supports_friendship("hilltop_observatory").
supports_friendship("toy_repair_room").

has_twist("clockwork_greenhouse").
has_twist("old_ferry_shed").
has_twist("hilltop_observatory").
has_twist("toy_repair_room").

#show usable_mechanism/1.
#show story_ready/1.
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
    friend: str
    mood: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
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
    parser = argparse.ArgumentParser(description="A cautious friendship mystery about a hidden mechanism.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--mood", choices=MOODS)
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
    facts = []
    for place in PLACES:
        key = place.replace(" ", "_")
        facts.extend(
            (
                asp.fact("setting", key),
                asp.fact("has_tool", key),
                asp.fact("has_guard", key),
                asp.fact("supports_friendship", key),
                asp.fact("has_twist", key),
            )
        )
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    expected = {(p.replace(" ", "_"),) for p in PLACES}
    model = asp.one_model(asp_program("#show story_ready/1."))
    actual = set(asp.atoms(model, "story_ready"))
    if actual == expected:
        print(f"OK: ASP/Python parity holds for {len(actual)} story settings.")
        return 0
    print("MISMATCH:")
    print("only in ASP:", sorted(actual - expected))
    print("only in Python:", sorted(expected - actual))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(tuple(PLACES))
    hero = args.hero or rng.choice(NAMES)
    choices = [name for name in NAMES if name != hero]
    friend = args.friend or rng.choice(choices)
    if friend == hero:
        raise StoryError("The hero and friend must have different names so their conversation is clear.")
    mood = args.mood or rng.choice(MOODS)
    if place not in PLACES:
        raise StoryError(f"Unknown place: {place}.")
    return StoryParams(place=place, hero=hero, friend=friend, mood=mood, seed=args.seed)


def story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.place, params.hero, params.friend, params.mood))
    return int.from_bytes(hashlib.blake2b(text.encode(), digest_size=8).digest(), "big")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}.")
    if params.hero == params.friend:
        raise StoryError("A friendship mystery needs two different friends.")

    meta = PLACES[params.place]
    seed = story_seed(params)
    rng = random.Random(seed)
    clue = CLUES[seed % len(CLUES)]
    opening = OPENINGS[(seed // len(CLUES)) % len(OPENINGS)]
    dialogue = DIALOGUE[(seed // (len(CLUES) * len(OPENINGS))) % len(DIALOGUE)]
    lesson = LESSONS[(seed // (len(CLUES) * len(OPENINGS) * len(DIALOGUE))) % len(LESSONS)]
    safe_action = (
        f"slid the {meta['safe_tool']} into the mechanism's guard slot",
        f"stood behind the safety line and used the {meta['safe_tool']} to hold the moving part",
        f"asked the caretaker for permission, then placed the {meta['safe_tool']} beside the control",
    )[seed % 3]

    world = World(place=meta["setting"])
    hero = Entity(
        id=params.hero,
        kind="character",
        label="careful investigator",
        type="hero",
        meters={"alertness": 1.0},
        memes={"curiosity": 1.0, "trust": 0.8},
        location=params.place,
    )
    friend = Entity(
        id=params.friend,
        kind="character",
        label="loyal friend",
        type="friend",
        meters={"alertness": 0.8},
        memes={"kindness": 1.0, "trust": 0.9},
        location=params.place,
    )
    machine = Entity(
        id="mechanism",
        kind="machine",
        label=meta["mechanism"],
        type="mechanism",
        meters={"tension": 0.7, "motion": 0.4},
        memes={"danger": 0.6},
        location=params.place,
    )
    tool = Entity(
        id="safety_tool",
        kind="object",
        label=meta["safe_tool"],
        type="guard",
        meters={"strength": 0.5},
        memes={"helpfulness": 1.0},
        location=params.place,
    )
    world.entities = {e.id: e for e in (hero, friend, machine, tool)}

    world.say(opening)
    world.say(
        f"{params.hero}, a {params.mood} puzzle-solver, visited {meta['setting']} with {params.friend}, "
        f"their closest friend."
    )
    world.say(f"They had come to inspect {meta['mechanism']}, which had stopped working before the day's visitors arrived.")
    world.say(f"A warning card said that {meta['hazard']}, so the friends promised not to grab any moving part.")

    world.para()
    world.say(f"Then {clue}. A brass handle twitched, and a tiny bell gave one nervous ring.")
    world.say(f"'{dialogue[0]},' said {params.hero}. '{dialogue[1]},' answered {params.friend}.")
    world.say(
        f"They searched the nearby shelves and found a missing instruction plate beneath {meta['landmark']}. "
        f"The plate claimed that the machine had been damaged by a careless visitor."
    )
    world.say(
        f"{params.hero} began to reach toward the handle, but {params.friend} gently caught their sleeve. "
        f"That small act of friendship stopped the most dangerous guess."

    world.para()
    world.say(
        f"Together they watched the gears without touching them. The bright tooth moved once, then stopped "
        f"whenever the warning bell rang."
    )
    world.say(
        f"They discovered a second clue: the instruction plate had been turned backward, and its scratch marks "
        f"matched the marks around the control box."
    )
    world.say(
        f"The twist was surprising. The mechanism was not broken by a visitor at all. A hidden timer had been "
        f"set to make the machine appear faulty so someone could enter the locked room after dark."
    )
    world.say(
        f"'{params.friend},' said {params.hero}, 'we should tell the caretaker instead of chasing whoever set it.' "
        f"'{params.hero},' replied {params.friend}, 'and we should keep the room safe until help arrives.'"
    )

    world.para()
    world.say(f"They {safe_action}. The handle stopped twitching, and the warning bell became quiet.")
    world.say(
        f"The caretaker arrived, checked the lock, and reset the timer. The hidden plan failed because the friends "
        f"noticed the danger before following the mystery too far."
    )
    world.say(
        f"{params.hero} thanked {params.friend} for speaking up. {params.friend} smiled and said that friendship "
        f"meant helping someone pause when excitement made a risky choice seem clever."
    )
    world.say(f"The lesson was clear: {lesson}.")
    world.say(
        f"By sunset, {meta['mechanism']} rested safely behind its guard, while the two friends walked home together, "
        f"still trading theories but no longer touching what they had not yet understood."
    )

    hero.meters["alertness"] = 1.5
    friend.meters["alertness"] = 1.4
    machine.meters["tension"] = 0.0
    machine.meters["motion"] = 0.0
    machine.memes["danger"] = 0.1
    hero.memes["trust"] = 1.0
    friend.memes["trust"] = 1.0

    world.trace = [
        "heard:warning bell and moving mechanism",
        f"observed:{clue}",
        "paused:friend prevented unsafe contact",
        "discovered:backward instruction plate and hidden timer",
        "twist:machine was made to look broken",
        "resolved:guarded mechanism and informed caretaker",
    ]
    world.facts = {
        "place": params.place,
        "setting": meta["setting"],
        "hero": params.hero,
        "friend": params.friend,
        "mechanism": meta["mechanism"],
        "hazard": meta["hazard"],
        "tool": meta["safe_tool"],
        "clue": clue,
        "twist": "A hidden timer made the mechanism appear broken so someone could enter after dark.",
        "lesson": lesson,
    }

    prompts = [
        f"Write a child-friendly mystery about {params.hero} and {params.friend} investigating {meta['mechanism']} in {meta['setting']}.",
        f"Include friendship, a caution about {meta['hazard']}, and a twist involving a hidden timer.",
        f"Show how the friends use {meta['safe_tool']} and careful observation instead of touching the mechanism.",
    ]
    story_qa = [
        QAItem(
            question=f"Why did {params.hero} and {params.friend} avoid grabbing the mechanism?",
            answer=f"They avoided grabbing it because {meta['hazard']}; the warning card told them to keep their hands away from moving parts.",
        ),
        QAItem(
            question="How did friendship help solve the mystery?",
            answer=f"{params.friend} stopped {params.hero} from reaching toward the handle, and together they chose to observe the mechanism and ask the caretaker for help.",
        ),
        QAItem(
            question="What was the twist?",
            answer="The mechanism was not truly broken. A hidden timer had been set to make it look faulty so someone could enter the locked room after dark.",
        ),
        QAItem(
            question="How did the friends make the mechanism safe?",
            answer=f"They {safe_action}, then told the caretaker what they had discovered so the timer could be reset safely.",
        ),
        QAItem(
            question="What lesson did the friends learn?",
            answer=f"They learned that {lesson}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a group of parts that work together to make something move, open, lift, turn, or perform another job.",
        ),
        QAItem(
            question="Why should children be cautious around machines?",
            answer="Children should keep away from moving parts, follow warning signs, and ask a trusted adult for help because machines can pinch, cut, or drop things.",
        ),
        QAItem(
            question="What makes a good mystery clue?",
            answer="A good mystery clue is a detail that can be observed and checked, such as a scratch, sound, footprint, or misplaced object.",
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
    if trace and sample.world:
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"  {entity.id}: {entity.kind}; location={entity.location}; "
                f"meters={entity.meters}; memes={entity.memes}"
            )
        for item in sample.world.trace:
            print(f"  - {item}")
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
    StoryParams("clockwork greenhouse", "Luna", "Milo", "curious"),
    StoryParams("old ferry shed", "Nia", "Owen", "careful"),
    StoryParams("hilltop observatory", "Tess", "Pip", "brave"),
    StoryParams("toy repair room", "Mara", "Jasper", "patient"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show usable_mechanism/1.\n#show story_ready/1."))
        return
    if args.verify:
        code = asp_verify()
        if code == 0:
            for params in CURATED:
                generate(params)
            print("OK: generated stories pass the world gate.")
        sys.exit(code)
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show usable_mechanism/1.\n#show story_ready/1."))
        print(asp.atoms(model, "usable_mechanism"))
        print(asp.atoms(model, "story_ready"))
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        base = args.seed if args.seed is not None else random.randrange(2**31)
        seen = set()
        for index in range(max(1, args.n) * 30):
            if len(samples) >= max(1, args.n):
                break
            rng = random.Random(base + index)
            local = argparse.Namespace(
                place=args.place,
                hero=args.hero,
                friend=args.friend,
                mood=args.mood,
            )
            params = resolve_params(local, rng)
            params.seed = base + index
            sample = generate(params)
            if sample.story not in seen:
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
