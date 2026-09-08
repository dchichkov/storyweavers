#!/usr/bin/env python3
"""
A small standalone Pirate Tale storyworld about a historic shutter, friendship,
and problem solving aboard a lively little ship.
"""

from __future__ import annotations

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
    traits: list[str] = field(default_factory=list)


@dataclass
class Ship:
    name: str
    place: str
    weather: str
    flag: str


@dataclass(frozen=True)
class Scenario:
    key: str
    treasure: str
    obstacle: str
    mistake: str
    consequence: str
    clue: str
    plan: str
    reveal: str
    repair: str
    outcome: str
    lesson: str
    ending: str


@dataclass
class StoryParams:
    captain: str
    friend: str
    ship_name: str
    place: str
    seed: Optional[int] = None
    scenario: Optional[str] = None
    telling_mode: Optional[str] = None


CAPTAIN_NAMES = ["Mara", "Nell", "Pip", "Rosa", "Toby", "Finn"]
FRIEND_NAMES = ["Bram", "Lulu", "Kit", "Ollie", "Sable", "Jo"]
SHIP_NAMES = ["The Bright Gull", "The Tin Kettle", "The Moonlit Crab", "The Merry Acorn"]
PLACES = [
    "the old harbor of Bellwater",
    "the misty island of Lantern Key",
    "the crooked cove of Driftwood Bay",
    "the reef beneath the Red Moon",
]
WEATHERS = ["a warm breeze", "a silver rain", "a playful wind", "a calm blue morning"]
TELLING_MODES = ["arrival", "warning", "dialogue", "mystery", "promise", "countdown"]

SCENARIOS = [
    Scenario(
        key="lighthouse_shutter",
        treasure="a brass friendship bell",
        obstacle="a historic wooden shutter had fallen across the lighthouse window",
        mistake="tried to pry the shutter loose with a boat hook",
        consequence="the old hinge cracked and the lighthouse lamp swung toward the sea",
        clue="three carved gulls on the shutter pointed toward the bell tower",
        plan="studied the hinge and asked the lighthouse keeper what the carvings meant",
        reveal="the shutter was a safety panel designed to open only when the bell rope was pulled",
        repair="roped the panel gently while the keeper steadied the lamp",
        outcome="the shutter opened, and the lighthouse sent a bright path across the waves",
        lesson="friends solve more when they share what they know before they pull or push",
        ending="the friendship bell rang over the harbor as the repaired shutter gleamed in the dawn",
    ),
    Scenario(
        key="map_room",
        treasure="a map to a shared island garden",
        obstacle="a historic shutter sealed the captain's map room",
        mistake="ordered everyone to force the door at once",
        consequence="the map room shook and its loose charts fluttered into the tide",
        clue="the shutter's brass nails formed a tiny picture of two hands",
        plan="matched the picture with a second latch hidden beneath the floor mat",
        reveal="the shutter had been made to protect a map meant for two trusted friends",
        repair="retrieved the charts and invited the whole crew to hold the map corners together",
        outcome="the route to the island garden became clear to everyone",
        lesson="a shared problem deserves shared hands and shared credit",
        ending="the crew planted bright beans together while the old shutter rested open",
    ),
    Scenario(
        key="storm_storehouse",
        treasure="a chest of dry blankets for island children",
        obstacle="a historic shutter slammed shut on the storm storehouse",
        mistake="blamed the smallest sailor for blocking it",
        consequence="the crew argued while rainwater poured beneath the door",
        clue="the shutter moved whenever two ropes were pulled at the same time",
        plan="paired each sailor with a friend and counted the pulls together",
        reveal="the shutter was not stuck; its old counterweight needed two equal teams",
        repair="worked in pairs to lift the counterweight and dry the blankets",
        outcome="the children received warm blankets before the storm grew strong",
        lesson="friendship means looking for a fair part for everyone to play",
        ending="wet sailors laughed beneath dry blankets while the historic shutter stood firm",
    ),
    Scenario(
        key="parrot_signal",
        treasure="a message from a missing harbor friend",
        obstacle="a historic shutter hid the signal lantern in the crow's-nest cabin",
        mistake="sent the ship's parrot to tug every latch",
        consequence="the parrot dropped the message into a bucket of seawater",
        clue="the shutter had small holes shaped like stars and waves",
        plan="held lanterns behind the holes and copied the pattern onto a sail",
        reveal="the shutter itself was an old signal code for the safe harbor",
        repair="dried the message, decoded the pattern, and raised the correct flag",
        outcome="the missing friend saw the signal and sailed home by sunset",
        lesson="careful observation can turn an old obstacle into a useful guide",
        ending="the parrot squawked hello as two ships met beneath the historic signal shutter",
    ),
    Scenario(
        key="quiet_cabin",
        treasure="a songbook shared by two rival crews",
        obstacle="a historic shutter made the musicians' cabin dark and silent",
        mistake="declared that one crew should own the songbook",
        consequence="both crews stopped singing and the harbor lost its festival tune",
        clue="the shutter opened a little whenever voices sang together",
        plan="asked each crew to sing one line and listen for the next",
        reveal="the shutter's spring was tuned to harmony, not to a single loud voice",
        repair="joined the crews in one song and polished the spring with lamp oil",
        outcome="the cabin filled with music that belonged to everyone",
        lesson="friendship grows when people make room for another voice",
        ending="the historic shutter danced in its hinges while every sailor sang the same chorus",
    ),
    Scenario(
        key="hidden_garden",
        treasure="a basket of moon pears for the ship's sick cook",
        obstacle="a historic shutter covered the garden's only gate",
        mistake="cut the vines wrapped around its wooden bars",
        consequence="the garden's watering channel broke and the pears began to dry",
        clue="the vines curled around a painted picture of a watering can",
        plan="followed the picture to a small stone lever beside the gate",
        reveal="the shutter was part of an old water-saving lock",
        repair="reset the lever, guided the water back, and tied the vines to a trellis",
        outcome="the moon pears ripened in time for the cook",
        lesson="problem solving begins with learning what a strange thing is for",
        ending="the cook shared moon pears beneath the historic shutter and thanked every helper",
    ),
]

ASP_RULES = r"""
#show feature/1.
#show word/1.
#show valid/1.
feature(friendship).
feature(problem_solving).
word(historic).
word(shutter).
valid :- feature(friendship), feature(problem_solving), word(historic), word(shutter).
"""


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Historic shutter Pirate Tale storyworld.")
    parser.add_argument("--captain", choices=CAPTAIN_NAMES)
    parser.add_argument("--friend", choices=FRIEND_NAMES)
    parser.add_argument("--ship-name", choices=SHIP_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--scenario", choices=[s.key for s in SCENARIOS])
    parser.add_argument("--telling-mode", choices=TELLING_MODES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    friend = args.friend or rng.choice([name for name in FRIEND_NAMES if name != captain])
    return StoryParams(
        captain=captain,
        friend=friend,
        ship_name=args.ship_name or rng.choice(SHIP_NAMES),
        place=args.place or rng.choice(PLACES),
        scenario=args.scenario or rng.choice(SCENARIOS).key,
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
    )


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("feature", "friendship"),
            asp.fact("feature", "problem_solving"),
            asp.fact("word", "historic"),
            asp.fact("word", "shutter"),
        ]
    )


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/0.\n#show feature/1.\n#show word/1."))
    features = sorted(asp.atoms(model, "feature"))
    words = sorted(asp.atoms(model, "word"))
    valid = bool(asp.atoms(model, "valid"))
    if features == [("friendship",), ("problem_solving",)] and words == [("historic",), ("shutter",)] and valid:
        print("OK: ASP and Python story features agree.")
        return 0
    print("MISMATCH: ASP story features are incomplete.")
    return 1


def _scenario(key: Optional[str]) -> Scenario:
    for item in SCENARIOS:
        if item.key == key:
            return item
    return SCENARIOS[0]


def generate(params: StoryParams) -> StorySample:
    if not params.captain or not params.friend:
        raise StoryError("A captain and a friend are required.")
    if params.captain == params.friend:
        raise StoryError("The captain and friend must have different names.")
    if not params.ship_name or not params.place:
        raise StoryError("A ship name and place are required.")

    rng = random.Random(params.seed)
    scenario = _scenario(params.scenario)
    ship = Ship(params.ship_name, params.place, rng.choice(WEATHERS), "a blue-and-gold friendship flag"))
    world = World(ship)

    captain = world.add(
        Entity(
            id=params.captain,
            type="captain",
            label=f"Captain {params.captain}",
            location="quarterdeck",
            meters={"courage": 0.8, "patience": 0.5},
            memes={"friendship": 0.6},
            traits=["brave", "curious"],
        )
    )
    friend = world.add(
        Entity(
            id=params.friend,
            type="sailor",
            label=params.friend,
            location="main deck",
            meters={"cleverness": 0.8, "patience": 0.7},
            memes={"trust": 0.7},
            traits=["observant", "loyal"],
        )
    )
    shutter = world.add(
        Entity(
            id="historic_shutter",
            type="artifact",
            label="historic shutter",
            location=params.place,
            meters={"stuckness": 1.0, "age": 1.0},
            memes={"mystery": 1.0},
            traits=["old", "useful"],
        )
    )
    world.facts.update(
        scenario=scenario.key,
        treasure=scenario.treasure,
        obstacle=scenario.obstacle,
        consequence=scenario.consequence,
        clue=scenario.clue,
        repair=scenario.repair,
        outcome=scenario.outcome,
        lesson=scenario.lesson,
    )

    mode = params.telling_mode or "arrival"
    if mode == "warning":
        world.say(f'"Mind the old wood!" {params.friend} warned as {ship.name} sailed into {params.place}.')
        world.say(f"{params.captain} slowed the ship. They had come to find {scenario.treasure}.")
    elif mode == "dialogue":
        world.say(f'"A pirate adventure?" {params.captain} asked. "Only if we help each other," {params.friend} replied.')
        world.say(f"Together they sailed {ship.name} toward {params.place} to find {scenario.treasure}.")
    elif mode == "mystery":
        world.say(f"A strange tapping followed {ship.name} into {params.place}.")
        world.say(f"{params.captain} and {params.friend} were searching for {scenario.treasure} when the tapping stopped.")
    elif mode == "promise":
        world.say(f"{params.captain} had promised to bring {scenario.treasure} home safely.")
        world.say(f"With {params.friend} beside them, the captain steered {ship.name} into {params.place}.")
    elif mode == "countdown":
        world.say(f"The tide would turn in one hour as {ship.name} reached {params.place}.")
        world.say(f"{params.captain} and {params.friend} hurried to find {scenario.treasure}.")
    else:
        world.say(f"{ship.name} sailed into {params.place} beneath {ship.weather}.")
        world.say(f"Captain {params.captain} and {params.friend} had come to find {scenario.treasure}.")

    world.say(f"Then they discovered that {scenario.obstacle}.")
    world.para()
    world.say(f'"I can open it!" {params.captain} cried, and {params.captain} {scenario.mistake}.')
    world.say(f"{scenario.consequence.capitalize()}.")
    world.say(f'"Wait," {params.friend} said. "Let us look before we make the trouble larger."')
    world.para()
    world.say(f"Together, they noticed that {scenario.clue}.")
    world.say(f"{params.friend} suggested that they {scenario.plan}.")
    world.say(f"{params.captain} listened and agreed. Their friendship gave them time to think.")
    world.say(f"At last, they understood that {scenario.reveal}.")
    world.para()
    world.say(f'"I was too quick," {params.captain} admitted. "I am glad you stopped me."')
    world.say(f'"And I am glad you listened," {params.friend} answered. "Now let us fix it together."')
    world.say(f"The friends {scenario.repair}.")
    world.say(f"Because they shared the work, {scenario.outcome}.")
    world.para()
    world.say(f"They remembered that {scenario.lesson}.")
    world.say(f"As {ship.name} sailed home, {scenario.ending}.")

    shutter.location = "repaired and open"
    shutter.meters["stuckness"] = 0.0
    shutter.memes["purpose_understood"] = 1.0
    captain.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0
    world.facts["resolved"] = True

    prompts = [
        f"Write a Pirate Tale about {params.captain} and {params.friend} solving a problem with a historic shutter.",
        f"Tell a child-friendly story in which friendship helps repair this obstacle: {scenario.obstacle}.",
        f"Write an ending that proves the friends learned that {scenario.lesson}.",
    ]
    story_qa = [
        QAItem(
            question="What problem did the friends face?",
            answer=f"They faced a problem because {scenario.obstacle}. The historic shutter blocked their search for {scenario.treasure}.",
        ),
        QAItem(
            question="What clue helped them solve the problem?",
            answer=f"They noticed that {scenario.clue}. That clue helped them understand how the shutter worked.",
        ),
        QAItem(
            question=f"How did {params.captain} and {params.friend} use friendship?",
            answer=f"They listened to each other, shared the work, and then they {scenario.repair}.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The shutter was repaired and open, so {scenario.outcome}.",
        ),
        QAItem(
            question="What lesson did the friends learn?",
            answer=f"They learned that {scenario.lesson}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a historic object?",
            answer="A historic object is something old that carries information or meaning from the past.",
        ),
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a hinged cover that can close or open a window, doorway, or opening.",
        ),
        QAItem(
            question="Why is friendship useful during problem solving?",
            answer="Friendship helps people listen, share ideas, encourage one another, and work together.",
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
        print(asp_program("#show feature/1.\n#show word/1.\n#show valid/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Mara", "Bram", "The Bright Gull", "the old harbor of Bellwater", 101, "lighthouse_shutter", "arrival"),
            StoryParams("Nell", "Lulu", "The Tin Kettle", "the misty island of Lantern Key", 202, "map_room", "dialogue"),
            StoryParams("Finn", "Sable", "The Moonlit Crab", "the crooked cove of Driftwood Bay", 303, "storm_storehouse", "warning"),
        ]
        samples = [generate(item) for item in curated]
    else:
        seen: set[str] = set()
        attempt = 0
        target = max(1, args.n)
        while len(samples) < target and attempt < max(50, target * 20):
            attempt += 1
            seed = base_seed + attempt
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show feature/1.\n#show word/1.\n#show valid/0."))
        print("ASP model:", " ".join(str(atom) for atom in model))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.captain} and {sample.params.friend}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
