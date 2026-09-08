#!/usr/bin/env python3
"""
A small standalone Pirate Tale storyworld about a historic shutter, friendship,
and problem solving.
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    name: str
    harbor: str
    course: str
    weather: str


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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    captain: str
    friend: str
    ship_name: str
    harbor: str
    seed: Optional[int] = None
    scenario: Optional[str] = None
    telling_mode: Optional[str] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    premise: str
    shutter: str
    mistake: str
    consequence: str
    clue: str
    solution: str
    reveal: str
    apology: str
    repair: str
    outcome: str
    lesson: str
    ending: str


CAPTAIN_NAMES = ["Mara", "Nell", "Rosa", "Tess", "Wren", "Ada"]
FRIEND_NAMES = ["Finn", "Jo", "Pip", "Sam", "Kit", "Bo"]
HARBORS = [
    "the old bell harbor",
    "the red-coral cove",
    "the moonlit trading quay",
    "the windy lighthouse port",
]
SHIP_NAMES = ["The Kind Compass", "The Blue Gull", "The Lantern Fox", "The Bright Kettle"]
TELLING_MODES = ["arrival", "warning", "dialogue", "countdown", "mystery", "promise"]

SCENARIOS = [
    Scenario(
        key="lighthouse_map",
        premise="were carrying a historic sea map to the lighthouse keeper",
        shutter="the lighthouse's historic wooden shutter had jammed across its signal window",
        mistake="pushed the shutter with a boathook",
        consequence="the old hinges groaned and the warning lamp went dark",
        clue="three brass nails clicked whenever the tide struck the lower rocks",
        solution="counted the clicks and matched them with the tide",
        reveal="the shutter was built to open only when the safe channel was clear",
        apology="admitted that rushing had nearly damaged a piece of harbor history",
        repair="used rope, oil, and the tide's rhythm to ease the shutter open",
        outcome="the lamp shone across the water and guided a fishing boat home",
        lesson="a careful friend listens before trying to force a difficult thing",
        ending="the historic shutter rested open while the lamp painted a golden road on the sea",
    ),
    Scenario(
        key="captains_house",
        premise="were delivering a friendship flag to an old captain's house on the cliff",
        shutter="a historic iron shutter blocked the house's only window",
        mistake="pulled hard on its rusted ring",
        consequence="the ring broke and the friendship flag slid into a puddle",
        clue="a tiny painted gull pointed toward a loose stone beside the frame",
        solution="removed the loose stone and found the shutter's hidden release",
        reveal="the shutter was a storm lock designed to protect the house during squalls",
        apology="told the housekeeper exactly how the broken ring had happened",
        repair="forged a new ring from a spare anchor link and dried the flag in the sun",
        outcome="the flag flew safely and the old captain welcomed both friends inside",
        lesson="honesty gives friendship a stronger rope to hold",
        ending="the new ring gleamed beneath the friendship flag as two cups of cocoa steamed indoors",
    ),
    Scenario(
        key="treasure_archive",
        premise="were searching the harbor archive for a record of a missing treasure chest",
        shutter="a historic cedar shutter had fallen over the archive's narrow doorway",
        mistake="tried to chop through it with a small axe",
        consequence="dust covered the shelves and a box of records tipped toward the floor",
        clue="a carved compass on the shutter pointed toward the archive's side latch",
        solution="followed the compass carving and lifted the latch from inside the wall",
        reveal="the shutter was a secret door meant to protect records from pirate raids",
        apology="said that impatience had put the harbor's memories at risk",
        repair="restacked the records and repaired the shutter with wooden pegs",
        outcome="they found the treasure record and returned it to the families who owned it",
        lesson="problem solving works best when friends protect what matters to others",
        ending="the repaired shutter closed softly over the archive while the true owners shared the treasure fairly",
    ),
    Scenario(
        key="storm_signal",
        premise="were bringing medicine to an island clinic before a storm reached the bay",
        shutter="the clinic's historic blue shutter had blown sideways and covered the signal bell",
        mistake="tugged it loose without checking the roof ropes",
        consequence="the shutter swung back and trapped the medicine basket on the porch",
        clue="the rope knots formed the same pattern as the island's old sailing flag",
        solution="copied the flag pattern and loosened the knots in the right order",
        reveal="the shutter was tied as part of a storm signal, not left there by accident",
        apology="accepted blame for making the rescue slower",
        repair="retied the storm signal and lowered the medicine basket with a pulley",
        outcome="the clinic received the medicine before the rain arrived",
        lesson="friends solve trouble faster when they share what they notice",
        ending="rain drummed on the historic shutter while the clinic's lantern glowed warmly inside",
    ),
    Scenario(
        key="harbor_clock",
        premise="were sailing to reset the harbor clock before the evening tide",
        shutter="a historic copper shutter covered the clockmaker's workshop",
        mistake="lifted it with a boat hook while the clock gears were still turning",
        consequence="the hook caught a gear and stopped every clock on the quay",
        clue="the clock's soft ticking paused whenever the shutter's lower hinge moved",
        solution="held the shutter steady and turned the hinge one careful notch at a time",
        reveal="the shutter's hinge was connected to a safety brake for the old clock",
        apology="promised the clockmaker that the mistake would be repaired openly",
        repair="cleaned the gear, replaced the hinge pin, and reset the clocks together",
        outcome="the harbor bells rang the correct hour for every waiting sailor",
        lesson="good friends make room for patience when a small machine has a big job",
        ending="copper light flashed from the historic shutter as the harbor clocks chimed in friendly unison",
    ),
    Scenario(
        key="whispering_dock",
        premise="were looking for a friend who had missed the last boat home",
        shutter="a historic green shutter at the empty dock office rattled in the wind",
        mistake="declared that the missing friend must have sailed away",
        consequence="the crew nearly left without checking the quiet office",
        clue="the shutter tapped twice, then once, like their friend's secret knock",
        solution="answered the rhythm and searched behind the office's storage bench",
        reveal="the friend had been sheltering there while repairing a torn sail",
        apology="said they should have trusted the clues before making a guess",
        repair="stitched the sail together and carried the friend safely to the boat",
        outcome="everyone reached home before the harbor bell rang midnight",
        lesson="friendship grows when people keep looking instead of giving up",
        ending="the historic shutter tapped a cheerful goodbye as the repaired sail filled with moonlight",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pirate Tale storyworld about a historic shutter, friendship, and problem solving."
    )
    parser.add_argument("--captain", choices=CAPTAIN_NAMES)
    parser.add_argument("--friend", choices=FRIEND_NAMES)
    parser.add_argument("--ship-name", choices=SHIP_NAMES)
    parser.add_argument("--harbor", choices=HARBORS)
    parser.add_argument("--scenario", choices=[s.key for s in SCENARIOS])
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
    friend = args.friend or rng.choice([name for name in FRIEND_NAMES if name != captain])
    return StoryParams(
        captain=captain,
        friend=friend,
        ship_name=args.ship_name or rng.choice(SHIP_NAMES),
        harbor=args.harbor or rng.choice(HARBORS),
        scenario=args.scenario or rng.choice(SCENARIOS).key,
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
    )


def _opening(params: StoryParams, scenario: Scenario) -> list[str]:
    captain = f"Captain {params.captain}"
    friend = params.friend
    ship = params.ship_name
    if params.telling_mode == "warning":
        return [
            f'"Mind the old harbor!" {friend} warned as {ship} slipped toward {params.harbor}.',
            f"{captain} lowered the sail. The two friends {scenario.premise}.",
        ]
    if params.telling_mode == "dialogue":
        return [
            f'"Ready for a proper pirate puzzle?" {captain} asked. "As long as we solve it together," {friend} replied.',
            f"On {ship}, the friends reached {params.harbor.}",
            f"They {scenario.premise}.",
        ]
    if params.telling_mode == "countdown":
        return [
            f"The harbor bell would ring in ten minutes as {ship} entered {params.harbor}.",
            f"{captain} and {friend} had only that long because they {scenario.premise}.",
        ]
    if params.telling_mode == "mystery":
        return [
            f"A strange tapping followed {ship} into {params.harbor}.",
            f"{captain} and {friend} searched for its source while they {scenario.premise}.",
        ]
    if params.telling_mode == "promise":
        return [
            f"{captain} had promised not to leave {friend} behind.",
            f"So {ship} sailed into {params.harbor}, where the friends {scenario.premise}.",
        ]
    return [
        f"{ship} sailed into {params.harbor} beneath a bright pirate flag.",
        f"Captain {params.captain} and {params.friend} were friends, and they {scenario.premise}.",
    ]


def asp_facts() -> str:
    from asp import fact

    return "\n".join(
        [
            fact("style", "pirate_tale"),
            fact("feature", "friendship"),
            fact("feature", "problem_solving"),
            fact("seed_word", "historic"),
            fact("seed_word", "shutter"),
            fact("object", "historic_shutter"),
            fact("requires", "historic_shutter", "careful_friendship"),
        ]
    )


ASP_RULES = r"""
solvable :- feature(friendship), feature(problem_solving), object(historic_shutter).
#show style/1.
#show feature/1.
#show seed_word/1.
#show object/1.
#show requires/2.
#show solvable/0.
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    features = sorted(set(asp.atoms(model, "feature")))
    words = sorted(set(asp.atoms(model, "seed_word")))
    solvable = bool(asp.atoms(model, "solvable"))
    if features == [("friendship",), ("problem_solving",)] and words == [
        ("historic",),
        ("shutter",),
    ] and solvable:
        print("OK: ASP twin contains the required story features and solvability.")
        return 0
    print("MISMATCH: ASP twin failed the required parity check.")
    print(model)
    return 1


def _validate(params: StoryParams) -> None:
    if not params.captain or not params.friend:
        raise StoryError("A pirate tale needs both a captain and a friend.")
    if params.captain == params.friend:
        raise StoryError("The captain and friend must have different names.")
    if params.nonsense if hasattr(params, "nonsense") else False:
        raise StoryError("Unsupported story choice.")


def generate(params: StoryParams) -> StorySample:
    _validate(params)
    rng = random.Random(params.seed)
    scenario = next((s for s in SCENARIOS if s.key == params.scenario), None)
    if scenario is None:
        raise StoryError(f"Unknown scenario: {params.scenario}")

    ship = Ship(
        name=params.ship_name,
        harbor=params.harbor,
        course="safe harbor",
        weather=rng.choice(["clear", "breezy", "cloudy"]),
    )
    world = World(ship)

    captain = world.add(
        Entity(
            id=params.captain,
            type="captain",
            label=f"Captain {params.captain}",
            location="quarterdeck",
            meters={"courage": 0.8, "patience": 0.4},
            memes={"friendship": 0.7},
        )
    )
    friend = world.add(
        Entity(
            id=params.friend,
            type="boy",
            label=params.friend,
            location="deck",
            meters={"notice": 0.8, "balance": 0.7},
            memes={"trust": 0.8},
        )
    )
    shutter = world.add(
        Entity(
            id="shutter",
            type="artifact",
            label="historic shutter",
            location="harbor building",
            meters={"hinge_health": 0.7, "openness": 0.0, "age": 1.0},
            memes={"history": 1.0, "mystery": 0.8},
        )
    )
    world.facts.update(
        scenario=scenario.key,
        historic=True,
        friendship=True,
        problem_solving=True,
        clue=scenario.clue,
        mistake=scenario.mistake,
        outcome=scenario.outcome,
    )

    for sentence in _opening(params, scenario):
        world.say(sentence)

    world.say(
        rng.choice(
            [
                f"At the harbor they discovered that {scenario.shutter}.",
                f"Then came the trouble: {scenario.shutter}.",
                f"The tapping stopped when they saw that {scenario.shutter}.",
            ]
        )
    )

    world.para()
    world.say(
        f'"I know what to do," {captain.id} said, and {captain.pronoun()} {scenario.mistake}.'
    )
    world.say(f"The quick choice caused trouble: {scenario.consequence}.")
    world.say(
        f'"Wait, Captain," {friend.id} replied. "What did the old marks tell us?"'
    )
    world.say(
        f'"I was trying to help," {captain.id} admitted. "{friend.id}, what do you see?"'
    )

    world.para()
    world.say(f"{friend.id} studied the wood, metal, and ropes. {scenario.clue}.")
    world.say(f'"Then we can solve it together," {friend.id} said.')
    world.say(f"Following the clue, they {scenario.solution}.")
    world.say(f"Their careful work revealed that {scenario.reveal}.")

    world.para()
    world.say(f"{captain.id} lowered {captain.pronoun('possessive')} head and {scenario.apology}.")
    world.say(
        f'"Thank you for telling me to look twice," {captain.id} said. "{friend.id}, you were right to notice the pattern."'
    )
    world.say(f"Together they {scenario.repair}.")
    world.say(f"At last, {scenario.outcome}.")

    world.para()
    world.say(f"The friends remembered that {scenario.lesson}.")
    world.say(f"As the tide turned, {scenario.ending}.")

    shutter.location = "repaired harbor building"
    shutter.meters["hinge_health"] = 1.0
    shutter.meters["openness"] = 1.0
    shutter.memes["mystery"] = 0.0
    captain.meters["patience"] = 0.9
    captain.memes["friendship"] = 1.0
    friend.memes["trust"] = 1.0
    world.facts["resolved"] = True

    prompts = [
        f"Write a Pirate Tale about Captain {params.captain} and {params.friend} solving a problem with a historic shutter.",
        f"Tell a child-friendly friendship story in {params.harbor} where careful observation repairs a mistake.",
        f"Write a pirate adventure ending with this lesson: {scenario.lesson}.",
    ]
    story_qa = [
        QAItem(
            question="What historic object caused the trouble?",
            answer=f"The trouble came from {scenario.shutter}. It was an old harbor object whose purpose had to be understood before it could be moved.",
        ),
        QAItem(
            question=f"What mistake did Captain {params.captain} make?",
            answer=f"Captain {params.captain} {scenario.mistake}, and that caused a problem: {scenario.consequence}.",
        ),
        QAItem(
            question=f"How did {params.friend} help solve the problem?",
            answer=f"{params.friend} noticed that {scenario.clue}. That clue helped the friends {scenario.solution}.",
        ),
        QAItem(
            question="How did the friends repair their friendship?",
            answer=f"The captain admitted the mistake, listened to the friend's clue, and they worked together to {scenario.repair}.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The shutter was repaired, and {scenario.outcome} The friends also learned that {scenario.lesson}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a covering that can close over a window, doorway, or opening.",
        ),
        QAItem(
            question="Why can a historic object need careful handling?",
            answer="A historic object carries memories from the past, so careless force may damage something that cannot easily be replaced.",
        ),
        QAItem(
            question="How does friendship help with problem solving?",
            answer="Friends can notice different clues, speak honestly, and combine their ideas to find a safer solution.",
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
            parts = [f"location={entity.location}"]
            if entity.meters:
                parts.append(f"meters={entity.meters}")
            if entity.memes:
                parts.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.type} " + " ".join(parts))
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        import asp

        status = asp_verify()
        if status:
            sys.exit(status)
        sample = generate(
            StoryParams(
                captain="Mara",
                friend="Finn",
                ship_name="The Kind Compass",
                harbor="the old bell harbor",
                seed=17,
                scenario="lighthouse_map",
                telling_mode="dialogue",
            )
        )
        if "historic shutter" not in sample.story or "friend" not in sample.story.lower():
            print("MISMATCH: generated story omitted required narrative elements.")
            sys.exit(1)
        print("OK: generated story exercises the friendship and problem-solving path.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                captain="Mara",
                friend="Finn",
                ship_name="The Kind Compass",
                harbor="the old bell harbor",
                seed=101,
                scenario="lighthouse_map",
                telling_mode="arrival",
            ),
            StoryParams(
                captain="Nell",
                friend="Jo",
                ship_name="The Blue Gull",
                harbor="the red-coral cove",
                seed=202,
                scenario="captains_house",
                telling_mode="dialogue",
            ),
            StoryParams(
                captain="Rosa",
                friend="Pip",
                ship_name="The Lantern Fox",
                harbor="the moonlit trading quay",
                seed=303,
                scenario="treasure_archive",
                telling_mode="mystery",
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 20):
            attempt += 1
            attempt_seed = base_seed + attempt
            params = resolve_params(args, random.Random(attempt_seed))
            params.seed = attempt_seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("ASP model:")
        for atom in sorted(str(atom) for atom in model):
            print(f"  {atom}")
        print()

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.captain} and {sample.params.friend} in {sample.params.harbor}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
