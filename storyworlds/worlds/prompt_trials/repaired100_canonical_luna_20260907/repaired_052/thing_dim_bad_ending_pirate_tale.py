#!/usr/bin/env python3
"""
A small standalone Pirate Tale storyworld about a dim thing and a bad ending.
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
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    location: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    name: str
    setting: str
    condition: str = "afloat"


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass
class StoryParams:
    captain: str
    deckhand: str
    ship_name: str
    place: str
    seed: Optional[int] = None
    scenario: Optional[str] = None
    telling_mode: Optional[str] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    premise: str
    dim_thing: str
    temptation: str
    warning: str
    bad_choice: str
    bad_result: str
    last_chance: str
    ending: str
    lesson: str


CAPTAIN_NAMES = ["Mara", "Rook", "Nell", "Tessa", "Ivo", "Pia"]
DECKHAND_NAMES = ["Finn", "Kit", "Bo", "Lio", "Suri", "Pip"]
PLACES = [
    "the foggy Coral Sea",
    "Black Lantern Bay",
    "the crooked islands",
    "the moonlit Shiver Strait",
]
SHIP_NAMES = ["The Merry Minnow", "The Blue Gull", "The Salt Finch", "The Little Kraken"]
TELLING_MODES = ["warning", "arrival", "question", "countdown", "rumor", "promise"]

SCENARIOS = [
    Scenario(
        key="dim_lantern",
        premise="was carrying a chest of apples to a hungry harbor",
        dim_thing="a dim brass lantern",
        temptation="use it as a bright guide through a reef",
        warning="its weak flame pointed toward a nest of sleeping sea dragons",
        bad_choice="raised the lantern high and steered straight toward the glow",
        bad_result="the dragons woke, blew steam across the deck, and sent the ship spinning into a sandbar",
        last_chance="lowered the lantern and followed the quiet stars instead",
        ending="the apples reached the harbor late, bruised but still sweet, while the dim lantern rested safely below deck",
        lesson="a small warning can matter more than a bright promise",
    ),
    Scenario(
        key="dim_compass",
        premise="was searching for a lost sailor's family island",
        dim_thing="a dim compass with a trembling needle",
        temptation="trust it because its lid was painted with a golden crown",
        warning="the needle shook whenever the ship faced the hungry tide",
        bad_choice="ignored the shaking and ordered the crew toward the painted crown",
        bad_result="the tide dragged the ship into a whirlpool and washed the treasure map overboard",
        last_chance="listened to the compass and rowed toward the calmer water",
        ending="the crew escaped without the map, but the island remained hidden beyond the gray horizon",
        lesson="a fancy outside cannot make a doubtful tool safe",
    ),
    Scenario(
        key="dim_key",
        premise="was delivering a letter from a grandmother to her faraway grandson",
        dim_thing="a dim iron key",
        temptation="open a sealed sea chest found on a lonely rock",
        warning="the key grew cold whenever the chest's black lock clicked",
        bad_choice="forced the key into the lock and twisted with all her strength",
        bad_result="the chest snapped shut on the letter, and the tide carried both chest and message away",
        last_chance="used the key only on the small boat locker and found a dry scrap of paper with the route",
        ending="the crew sailed on, but the grandson never received the letter that day",
        lesson="curiosity can cost more when it forgets the promise already in hand",
    ),
    Scenario(
        key="dim-bell",
        premise="was guiding a rescue boat toward a lighthouse hidden by rain",
        dim_thing="a dim silver bell",
        temptation="ring it loudly to make the lighthouse answer",
        warning="one soft ring echoed from the rocks, while loud rings vanished in the storm",
        bad_choice="rang the bell again and again above the roar of the waves",
        bad_result="the rescue boat missed the safe channel and lost its oars against the rocks",
        last_chance="held the bell still and watched the faint echo between thunderclaps",
        ending="the lighthouse keeper found them at dawn, but the rescue had failed through the long night",
        lesson="more noise does not always make a true signal clearer",
    ),
    Scenario(
        key="dim-bottle",
        premise="was bringing medicine to an island village before sunset",
        dim_thing="a dim green bottle that glowed under the moon",
        temptation="trade it for a jeweled bottle offered by a smiling stranger",
        warning="the green glass stayed cool, while the jeweled bottle hissed when shaken",
        bad_choice="traded the medicine and packed the glittering bottle instead",
        bad_result="the strange bottle held only salty water, and the village healer had nothing to use",
        last_chance="opened the sea chest and found one last pouch of herbs beneath the dim bottle",
        ending="the herbs helped one child, but the rest of the village waited through the night",
        lesson="a useful little thing is worth more than a splendid empty one",
    ),
    Scenario(
        key="dim-flag",
        premise="was carrying a peace flag between two quarrelling pirate crews",
        dim_thing="a dim white flag patched with old sails",
        temptation="replace it with a bright red banner from the captain's chest",
        warning="the patched flag showed both crews' colors in its tiny stitches",
        bad_choice="hid the old flag and raised the red banner above the mast",
        bad_result="both crews mistook the red cloth for a challenge and fired their warning cannons",
        last_chance="lowered the red banner and waved the patched flag from the little boat",
        ending="the crews stopped firing, but their friendship was badly torn by the mistake",
        lesson="peace may look plain, yet its history can be precious",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pirate Tale storyworld about a dim thing and a bad ending.")
    parser.add_argument("--captain", choices=CAPTAIN_NAMES)
    parser.add_argument("--deckhand", choices=DECKHAND_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--ship-name", choices=SHIP_NAMES)
    parser.add_argument("--scenario", choices=[item.key for item in SCENARIOS])
    parser.add_argument("--telling-mode", choices=TELLING_MODES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    deckhand = args.deckhand or rng.choice([name for name in DECKHAND_NAMES if name != captain])
    return StoryParams(
        captain=captain,
        deckhand=deckhand,
        ship_name=args.ship_name or rng.choice(SHIP_NAMES),
        place=args.place or rng.choice(PLACES),
        scenario=args.scenario or rng.choice(SCENARIOS).key,
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
    )


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("domain", "pirate_tale"),
            asp.fact("seed_word", "thing_dim"),
            asp.fact("feature", "bad_ending"),
            asp.fact("has", "warning"),
            asp.fact("has", "temptation"),
            asp.fact("has", "consequence"),
        ]
    )


ASP_RULES = r"""
story_domain(pirate_tale).
story_seed(thing_dim).
story_feature(bad_ending).
valid_story :- story_domain(pirate_tale), story_seed(thing_dim), story_feature(bad_ending).
#show story_domain/1.
#show story_seed/1.
#show story_feature/1.
#show valid_story/0.
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    domains = asp.atoms(model, "story_domain")
    seeds = asp.atoms(model, "story_seed")
    features = asp.atoms(model, "story_feature")
    valid = any(symbol.name == "valid_story" for symbol in model)
    if domains == [("pirate_tale",)] and seeds == [("thing_dim",)] and features == [("bad_ending",)] and valid:
        params = StoryParams("Mara", "Finn", "The Blue Gull", "Black Lantern Bay", seed=9, scenario="dim_lantern", telling_mode="warning")
        sample = generate(params)
        if "bad" not in sample.story.lower() or "dim" not in sample.story.lower():
            print("MISMATCH: generated prose does not preserve the requested domain.")
            return 1
        print("OK: ASP and Python preserve pirate tale, thing-dim, and bad ending.")
        return 0
    print("MISMATCH: ASP parity failed.")
    return 1


def _opening(params: StoryParams, scenario: Scenario) -> list[str]:
    captain = f"Captain {params.captain}"
    mode = params.telling_mode or "arrival"
    if mode == "warning":
        return [
            f'"Keep low!" {params.deckhand} cried as {params.ship_name} entered {params.place}.',
            f"{captain} gripped the wheel. The crew {scenario.premise}.",
        ]
    if mode == "question":
        return [
            f'"Why is that thing so dim?" {params.deckhand} asked on the deck of {params.ship_name}.',
            f"{captain} looked toward {params.place}. The crew {scenario.premise}.",
        ]
    if mode == "countdown":
        return [
            f"The sun hung low as {params.ship_name} crossed {params.place}.",
            f"The crew had only a little daylight left. They {scenario.premise}.",
        ]
    if mode == "rumor":
        return [
            f"Sailors whispered that {params.place} hid a thing no pirate could understand.",
            f"That morning, {captain} and {params.deckhand} found it while the crew {scenario.premise}.",
        ]
    if mode == "promise":
        return [
            f"{captain} had promised to finish one good deed before sunset.",
            f"So {params.ship_name} sailed into {params.place} while the crew {scenario.premise}.",
        ]
    return [
        f"{params.ship_name} creaked into {params.place} beneath a pale sky.",
        f"{captain} steered while {params.deckhand} watched the waves. The crew {scenario.premise}.",
    ]


def generate(params: StoryParams) -> StorySample:
    if params.captain == params.deckhand:
        raise StoryError("captain and deckhand must have different names")
    if params.scenario not in {item.key for item in SCENARIOS}:
        raise StoryError(f"unknown pirate scenario: {params.scenario}")
    if params.telling_mode not in TELLING_MODES:
        raise StoryError(f"unknown telling mode: {params.telling_mode}")

    rng = random.Random(params.seed)
    scenario = next(item for item in SCENARIOS if item.key == params.scenario)
    ship = Ship(params.ship_name, params.place)
    world = World(ship)

    captain = world.add(
        Entity(
            id=params.captain,
            type="captain",
            label="captain",
            location="quarterdeck",
            meters={"alertness": 0.7, "hope": 0.8},
            memes={"duty": 1.0, "pride": 0.5},
        )
    )
    deckhand = world.add(
        Entity(
            id=params.deckhand,
            type="boy",
            label="deckhand",
            location="main deck",
            meters={"alertness": 0.8, "trust": 0.7},
            memes={"curiosity": 1.0},
        )
    )
    thing = world.add(
        Entity(
            id="thing_dim",
            type="artifact",
            label=scenario.dim_thing,
            location="main deck",
            meters={"brightness": 0.25, "usefulness": 0.8},
            memes={"mystery": 1.0, "warning": 1.0},
        )
    )

    world.facts.update(
        scenario=scenario.key,
        seed_word="thing-dim",
        feature="Bad Ending",
        premise=scenario.premise,
        warning=scenario.warning,
        bad_choice=scenario.bad_choice,
        bad_result=scenario.bad_result,
        lesson=scenario.lesson,
    )

    for sentence in _opening(params, scenario):
        world.say(sentence)
    world.say(f"Near the mast they found {scenario.dim_thing}.")
    world.say(f'"It looks too weak to help us," {params.deckhand} said.')
    world.say(f'"Weak light can still carry a warning," Captain {params.captain} replied.')

    world.para()
    world.say(f"The crew wanted to {scenario.temptation}.")
    world.say(f"At first, {scenario.warning}.")
    world.say(f"But the captain grew eager for a quick victory and {scenario.bad_choice}.")
    world.say(f'"Captain, wait!" {params.deckhand} shouted. "The dim thing is telling us something."')
    world.say(f'"A pirate cannot fear a little shadow," Captain {params.captain} answered.')

    world.para()
    world.say(f"Then the bad choice brought its price: {scenario.bad_result}.")
    world.say(f"{params.deckhand} tried to help and {scenario.last_chance}.")
    world.say(f"The deckhand called, 'We can still turn back!'")
    world.say(f"Captain {params.captain} answered, 'I should have listened sooner.'")
    world.say(f"But the tide, wind, or lost chance was already stronger than the crew.")
    world.say(f"{scenario.ending}.")
    world.say(f"The voyage ended with a bad ending, not because the sea was cruel, but because a clear warning was ignored.")
    world.say(f"Still, the crew remembered this lesson: {scenario.lesson}.")

    thing.location = "below deck"
    thing.meters["brightness"] = 0.15
    thing.meters["usefulness"] = 0.9
    thing.memes["lesson"] = 1.0
    captain.memes["regret"] = 1.0
    captain.meters["hope"] = 0.25
    ship.condition = "safe but regretful"
    world.facts.update(outcome="bad_ending", warning_ignored=True, lesson_learned=True)

    prompts = [
        f"Write a Pirate Tale about {params.captain} and {params.deckhand} finding {scenario.dim_thing}. Give the tale a Bad Ending.",
        f"Tell a child-friendly pirate story using the seed word thing-dim and this warning: {scenario.warning}.",
        f"Write a short sea adventure where ignoring a small warning causes this consequence: {scenario.bad_result}.",
    ]
    story_qa = [
        QAItem(
            question=f"What dim thing did Captain {params.captain} and {params.deckhand} find?",
            answer=f"They found {scenario.dim_thing} on the deck of {params.ship_name} while sailing through {params.place}.",
        ),
        QAItem(
            question="What warning did the dim thing give?",
            answer=f"The warning was that {scenario.warning}. It showed the crew that the tempting path was unsafe.",
        ),
        QAItem(
            question=f"What bad choice did Captain {params.captain} make?",
            answer=f"Captain {params.captain} {scenario.bad_choice}. The captain chose speed and pride instead of listening to the dim thing.",
        ),
        QAItem(
            question="Why did the tale have a bad ending?",
            answer=f"The tale had a bad ending because {scenario.bad_result}. The crew tried to recover, but the lost chance could not be completely repaired.",
        ),
        QAItem(
            question="What lesson did the crew learn?",
            answer=f"They learned that {scenario.lesson}. The dim thing was small, but its warning was important.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a Bad Ending in a story?",
            answer="A Bad Ending is an ending in which a harmful choice has a lasting consequence, even if the characters understand their mistake.",
        ),
        QAItem(
            question="What does thing-dim suggest in this storyworld?",
            answer="Thing-dim suggests an ordinary object with weak light, weak power, or a quiet warning that characters might wrongly overlook.",
        ),
        QAItem(
            question="What makes a Pirate Tale?",
            answer="A Pirate Tale usually has a ship, a sea journey, a crew, danger, bold choices, and a lesson learned from the voyage.",
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
        print("--- world model state ---")
        print(f"  ship: {sample.world.ship.name} condition={sample.world.ship.condition}")
        for entity in sample.world.entities.values():
            print(
                f"  {entity.id}: {entity.type} location={entity.location} "
                f"meters={entity.meters} memes={entity.memes}"
            )
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        print(json.dumps([str(atom) for atom in asp.one_model(asp_program())], indent=2))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Mara", "Finn", "The Blue Gull", "Black Lantern Bay", 101, "dim_lantern", "warning"),
            StoryParams("Rook", "Kit", "The Salt Finch", "the crooked islands", 202, "dim_compass", "question"),
            StoryParams("Nell", "Bo", "The Little Kraken", "the moonlit Shiver Strait", 303, "dim-flag", "rumor"),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(1, args.n):
            attempt += 1
            seed = base_seed + attempt
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
        header = ""
        if args.all:
            header = f"### {sample.params.captain} sails on {sample.params.ship_name}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
