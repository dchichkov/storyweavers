#!/usr/bin/env python3
"""A child-safe magical space adventure about an American dribble and a misunderstood innuendo."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import copy
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
sys.path.insert(0, os.path.dirname(_storyworlds_dir))

from results import QAItem, StoryError, StorySample  # noqa: E402


CAPTAINS = ["Luna", "Maya", "Theo", "Jalen", "Nova", "Amir"]
PLANETS = ["the Moon Garden", "the Comet Harbor", "the Blue Ring Station"]
CREATURES = ["star mice", "cloud foxes", "glow beetles"]
MISSIONS = ["a moonball tournament", "a comet festival", "a zero-gravity practice"]
OPENINGS = [
    "At sunrise above the silver planets",
    "When the first stars blinked awake",
    "On a quiet orbit beyond Earth",
    "As the rocket engines hummed softly",
    "Beneath a curtain of purple starlight",
]
REPAIRS = [
    "a bright practice lane marked with friendly moonstones",
    "a floating hoop tied safely to the station rail",
    "a clear signal lamp beside the launch deck",
    "a shared rulebook written in glittering space chalk",
]
CLOSINGS = [
    "the moonball sailed through the hoop and lit the whole station blue",
    "the creatures dribbled together while comets curled like ribbons overhead",
    "Luna and the new friends passed the glowing ball beneath a sky full of stars",
    "the repaired lane shone softly as everyone took turns and cheered",
]


@dataclass
class Entity:
    id: str
    type: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    captain: str
    planet: str
    creatures: str
    mission: str
    repair: str
    closing: str
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
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

    def copy(self) -> "World":
        return copy.deepcopy(self)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Magical Space Adventure about an American dribble and a repaired innuendo."
    )
    parser.add_argument("--captain", choices=CAPTAINS)
    parser.add_argument("--planet", choices=PLANETS)
    parser.add_argument("--creatures", choices=CREATURES)
    parser.add_argument("--mission", choices=MISSIONS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument(f"--{flag}", action="store_true", dest=flag.replace("-", "_"))
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        captain=args.captain or rng.choice(CAPTAINS),
        planet=args.planet or rng.choice(PLANETS),
        creatures=args.creatures or rng.choice(CREATURES),
        mission=args.mission or rng.choice(MISSIONS),
        repair=rng.choice(REPAIRS),
        closing=rng.choice(CLOSINGS),
    )


def tell(params: StoryParams) -> World:
    if not params.captain or not params.planet:
        raise StoryError("A captain and a planet are required for a safe mission.")

    world = World()
    captain = world.add(
        Entity(
            "captain",
            "human",
            params.captain,
            "American space captain",
            meters={"balance": 0.6, "courage": 0.8},
            memes={"curiosity": 1.0, "patience": 0.4},
        )
    )
    friends = world.add(
        Entity(
            "friends",
            "space_creatures",
            params.creatures,
            "helpers",
            meters={"floatiness": 0.9},
            memes={"friendliness": 0.8},
        )
    )
    ball = world.add(
        Entity(
            "moonball",
            "magical_ball",
            "the moonball",
            "shared game ball",
            meters={"bounce": 0.7, "glow": 0.5},
            memes={"kindness": 0.5},
        )
    )
    world.facts.update(
        captain=captain,
        friends=friends,
        ball=ball,
        mission=params.mission,
        misunderstanding=True,
        lane_open=False,
        repaired=False,
        trust=0.3,
    )

    world.say(f"{OPENINGS[hash(params.captain) % len(OPENINGS)]}, {captain.label} piloted a little American rocket to {params.planet}.")
    world.say(f"The mission was {params.mission}, and the crew carried one enchanted moonball that could dribble across empty air.")
    world.say(f"{friends.label} waited by the practice deck, their silver paws ready for a turn.")
    world.para()

    world.say(f"{captain.label} bounced the moonball once, twice, and then made a proud American dribble around a floating cone.")
    world.say(f"The ball sprang toward a cracked hoop, where an old sign read, 'Mind the rim and watch your bounce.'")
    world.say(f"The sign was a harmless space-station innuendo about the hoop's rim, but nobody had explained the playful phrase.")
    world.say(f"One glow beetle whispered, 'Does that mean we should hide the hoop?'")
    world.say(f"{captain.label} answered, 'I am not sure. What do you think it means?'")
    world.say(f"The star crew replied, 'We thought the sign meant the game was forbidden.'")
    world.say(f"{captain.label} listened and said, 'Then let us check the real rule together.'")
    world.facts["misunderstanding"] = True
    world.para()

    world.say(f"They discovered that a loose moonstone had dimmed the safety lane, so the sign's joke had covered a real problem.")
    world.say(f"The moonball bounced toward the dark edge, and {captain.label} caught it before it drifted into space.")
    world.say(f"The crew pointed to the loose stone. 'The innuendo confused us,' they said, 'but the dim lane is what needs fixing.'")
    world.say(f"{captain.label} replied, 'Words can be playful, but safety must be plain.'")
    world.say(f"Together they placed {params.repair}.")
    world.facts["lane_open"] = True
    world.facts["repaired"] = True
    world.facts["trust"] = 1.0
    world.para()

    world.say(f"The captain explained that innuendo is a playful hint, not a hidden command, and the friends asked questions whenever a phrase seemed puzzling.")
    world.say(f"Then {captain.label} invited {friends.label} to dribble the moonball through the repaired lane.")
    world.say(f"The friends took careful turns, calling, 'Clear lane!' before each bounce.")
    world.say(f"The magical ball glowed brighter because everyone understood both the words and the safety rule.")
    world.say(f"At last, {params.closing}.")
    world.say("The crew learned that clear questions, shared repairs, and kind play can guide a spacecraft farther than guessing.")

    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    captain = world.facts["captain"].label
    friends = world.facts["friends"].label
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a child-safe Space Adventure about {captain}, an American captain, who uses a magical dribble to help {friends}.",
            "Include the word innuendo as a harmless misunderstanding that is clarified through dialogue.",
            f"End with a repaired practice lane at {params.planet} and a shared lesson about asking questions.",
        ],
        story_qa=[
            QAItem(
                f"Why did {captain} stop the moonball game?",
                f"{captain} stopped because a loose moonstone had dimmed the safety lane, even though the playful innuendo on the sign had caused confusion.",
            ),
            QAItem(
                "What did the innuendo mean?",
                "It was a playful hint about the hoop's rim, not a command to hide the hoop or stop the game.",
            ),
            QAItem(
                "How did the crew repair the problem?",
                f"They placed {params.repair}, which made the lane clear and safe again.",
            ),
            QAItem(
                "How did the dialogue change the mission?",
                f"{captain} asked what the friends thought, listened to their worry, and then explained the phrase while everyone fixed the lane together.",
            ),
            QAItem(
                "What proved that trust returned?",
                f"{friends} took careful turns dribbling the glowing moonball through the repaired lane.",
            ),
        ],
        world_qa=[
            QAItem(
                "What is a dribble?",
                "A dribble is the repeated bouncing or tapping of a ball while guiding it along.",
            ),
            QAItem(
                "What is innuendo?",
                "Innuendo is an indirect or playful hint. Clear questions help people understand what a hint really means.",
            ),
            QAItem(
                "Why should space games use a safety lane?",
                "A marked safety lane keeps players and equipment away from dangerous edges, loose objects, and open space.",
            ),
            QAItem(
                "What makes magic helpful in this story?",
                "The magic makes the moonball glow and bounce through empty air, but careful choices and teamwork still keep the game safe.",
            ),
        ],
        world=world,
    )


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "space"),
            asp.fact("style", "space_adventure"),
            asp.fact("feature", "magic"),
            asp.fact("theme", "american"),
            asp.fact("activity", "dribble"),
            asp.fact("device", "innuendo"),
            asp.fact("value", "clarity"),
            asp.fact("value", "repair"),
        ]
    )


ASP_RULES = """
valid_story :-
    setting(space),
    style(space_adventure),
    feature(magic),
    theme(american),
    activity(dribble),
    device(innuendo),
    value(clarity),
    value(repair).
#show valid_story/0.
"""


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(asp_program())
    accepted = any(symbol.name == "valid_story" for symbol in symbols)
    if not accepted:
        print("Mismatch: ASP rejected the magical space story.")
        return 1
    sample = generate(
        StoryParams(
            captain="Luna",
            planet=PLANETS[0],
            creatures=CREATURES[0],
            mission=MISSIONS[0],
            repair=REPAIRS[0],
            closing=CLOSINGS[0],
        )
    )
    required = ("American", "dribble", "innuendo", "magic", "space")
    if not all(word.lower() in sample.story.lower() for word in required):
        print("Mismatch: generated prose lacks a required story feature.")
        return 1
    print("OK: ASP and Python accepted the magical space adventure.")
    return 0


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.type} {entity.label} role={entity.role} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    for key, value in world.facts.items():
        if key not in {"captain", "friends", "ball"}:
            lines.append(f"  fact.{key}={value}")
    return "\n".join(lines)


CURATED = [
    StoryParams(CAPTAINS[0], PLANETS[0], CREATURES[0], MISSIONS[0], REPAIRS[0], CLOSINGS[0]),
    StoryParams(CAPTAINS[1], PLANETS[1], CREATURES[1], MISSIONS[1], REPAIRS[1], CLOSINGS[1]),
    StoryParams(CAPTAINS[2], PLANETS[2], CREATURES[2], MISSIONS[2], REPAIRS[2], CLOSINGS[2]),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        print("compatible story:")
        for symbol in asp.one_model(asp_program()):
            print(symbol)
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(item) for item in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(100, args.n * 30):
            seed = base + attempt
            attempt += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
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
