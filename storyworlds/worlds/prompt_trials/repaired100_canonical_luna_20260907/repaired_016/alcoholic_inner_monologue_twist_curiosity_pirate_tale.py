#!/usr/bin/env python3
"""
A child-friendly pirate tale about an alcoholic sailor who chooses curiosity,
faces an inner monologue, and discovers a surprising twist.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve()
try:
    STORYWORLDS_ROOT = next(parent for parent in HERE.parents if (parent / "results.py").is_file())
except StopIteration:
    STORYWORLDS_ROOT = HERE.parent
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    id: str
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Location:
    name: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    captain_name: str
    cabin_boy_name: str
    parrot_name: str
    island_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Adventure:
    clue: str
    danger: str
    question: str
    action: str
    discovery: str
    twist: str
    ending: str
    lesson: str


CAPTAIN_NAMES = ["Mara", "Tobin", "Nell", "Rafe", "Sable"]
CABIN_BOY_NAMES = ["Pip", "Kit", "Jo", "Finn", "Wren"]
PARROT_NAMES = ["Biscuit", "Sprig", "Peaches", "Blue", "Buttons"]
ISLAND_NAMES = ["Whisper Reef", "Moonhook Isle", "Crescent Cay", "Lantern Island", "Starfish Key"]

ADVENTURES = [
    Adventure(
        clue="a blue bottle bobbed beside the ship with a silver feather tied to its neck",
        danger="the current was pulling the bottle toward sharp rocks",
        question="Why would a bottle carry a feather instead of a flag?",
        action="used the long boat hook to draw the bottle safely aboard",
        discovery="inside was a map showing a tiny door beneath the old lighthouse",
        twist="the map was not treasure directions at all; it was a picture made by a lonely lighthouse keeper asking for company",
        ending="the keeper opened the lighthouse door, and the pirates shared warm bread beneath the turning beam",
        lesson="curiosity can uncover a need that treasure hunters might miss",
    ),
    Adventure(
        clue="a bell rang from the fog even though no ship appeared on the horizon",
        danger="the hidden bell marked a reef that could tear the ship's hull",
        question="Who rings a bell where nobody can see them?",
        action="followed the sound slowly while watching the water depth",
        discovery="a little brass bell hung from a buoy tangled in seaweed",
        twist="the mysterious ringing was caused by a family of crabs climbing over the buoy",
        ending="the crew freed the buoy, and the crabs waved their claws from a safe tide pool",
        lesson="a strange sound deserves careful investigation before a frightening guess",
    ),
    Adventure(
        clue="a trail of warm cinnamon smell drifted from a cave on the island",
        danger="the cave mouth was narrow and the tide was rising",
        question="Can a cave bake something, or is someone waiting inside?",
        action="marked the tide line and entered only as far as the dry sand",
        discovery="a basket held fresh cakes and a note asking sailors to leave one for the cave's guardian",
        twist="the guardian was a shy young baker who had hidden there after losing her village oven",
        ending="the crew carried her basket to the village, where a new oven soon filled the harbor with cinnamon air",
        lesson="curiosity grows kinder when it makes room for another person's story",
    ),
    Adventure(
        clue="a green light blinked beneath the waves beside a quiet island",
        danger="the reef was too shallow for the ship to pass over",
        question="Is the light a jewel, a fish, or a warning?",
        action="anchored in deep water and lowered a glass-bottomed bucket",
        discovery="the light came from tiny sea creatures glowing around a sunken bell",
        twist="the bell belonged to the captain's grandmother and had been lost before the captain was born",
        ending="the captain left the bell beneath the glowing water, where it chimed softly for every passing sailor",
        lesson="not every treasure must be taken home to be treasured",
    ),
    Adventure(
        clue="a row of footprints crossed the beach and stopped at a blank wall of rock",
        danger="the tide would soon cover the footprints and the beach path",
        question="How could footprints end at solid stone?",
        action="examined the sand, the rock, and the tide before touching anything",
        discovery="a hidden door opened when the crew pressed a seashell into a round hollow",
        twist="the secret room contained no gold, only old journals written by children who had explored the island",
        ending="the pirates added their own careful page and closed the door for the next curious crew",
        lesson="knowledge shared across time can be a richer treasure than coins",
    ),
]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Character] = {}
        self.location = Location("the pirate ship and its nearby island")
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.dialogue_turns: list[tuple[str, str]] = []

    def add(self, entity: Character) -> Character:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def speak(self, speaker: Character, line: str) -> None:
        self.dialogue_turns.append((speaker.name, line))
        self.say(f'{speaker.name} said, "{line}"')

    def render(self) -> str:
        return "\n\n".join(" ".join(group) for group in self.paragraphs if group)


ASP_RULES = r"""
#show risk/1.
#show safe_choice/1.
#show discovery/1.
risk(reef) :- current(strong), rocks(nearby).
safe_choice(boat_hook) :- bottle(floating), rocks(nearby).
discovery(map) :- bottle(floating), feather(mark).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("current", "strong"),
            asp.fact("rocks", "nearby"),
            asp.fact("bottle", "floating"),
            asp.fact("feather", "mark"),
        ]
    )


def asp_program(show: str = "#show risk/1.\n#show safe_choice/1.\n#show discovery/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Curious pirate tale storyworld.")
    parser.add_argument("--captain-name", choices=CAPTAIN_NAMES)
    parser.add_argument("--cabin-boy-name", choices=CABIN_BOY_NAMES)
    parser.add_argument("--parrot-name", choices=PARROT_NAMES)
    parser.add_argument("--island-name", choices=ISLAND_NAMES)
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
    captain = args.captain_name or rng.choice(CAPTAIN_NAMES)
    cabin = args.cabin_boy_name or rng.choice([name for name in CABIN_BOY_NAMES if name != captain])
    parrot = args.parrot_name or rng.choice(PARROT_NAMES)
    island = args.island_name or rng.choice(ISLAND_NAMES)
    return StoryParams(captain, cabin, parrot, island)


def validate(params: StoryParams) -> None:
    if params.captain_name == params.cabin_boy_name:
        raise StoryError("The captain and cabin boy must have different names.")
    if not all(
        isinstance(value, str) and value.strip()
        for value in (
            params.captain_name,
            params.cabin_boy_name,
            params.parrot_name,
            params.island_name,
        )
    ):
        raise StoryError("Every named character and place must have a non-empty name.")


def setup_world(params: StoryParams) -> World:
    validate(params)
    world = World()
    captain = world.add(Character("captain", params.captain_name, "captain"))
    cabin = world.add(Character("cabin", params.cabin_boy_name, "cabin boy"))
    parrot = world.add(Character("parrot", params.parrot_name, "parrot"))
    world.facts.update(captain=captain, cabin=cabin, parrot=parrot, island=params.island_name)
    return world


def generate_story(world: World, params: StoryParams) -> None:
    captain: Character = world.facts["captain"]
    cabin: Character = world.facts["cabin"]
    parrot: Character = world.facts["parrot"]
    index = (params.seed if params.seed is not None else sum(map(ord, params.captain_name))) % len(ADVENTURES)
    adventure = ADVENTURES[index]

    world.facts.update(adventure=adventure, index=index, resolved=False)
    captain.memes.update(courage=0.4, curiosity=0.7, sobriety=0.2)
    cabin.memes.update(curiosity=0.8, trust=0.6)
    parrot.memes.update(alertness=0.9)
    world.location.meters.update(tide=0.4, visibility=0.8)

    world.say(
        f"Captain {captain.name} was an alcoholic pirate who had once let rum steer more "
        f"of his choices than wisdom. On the morning the crew sailed near {params.island_name}, "
        f"he poured the last bottle into the sea and kept both hands on the wheel."
    )
    world.say(
        f"{cabin.name}, the cabin boy, and {parrot.name} the parrot were watching the waves when "
        f"{adventure.clue}. Nobody knew who had sent it."
    )
    world.para()
    world.speak(cabin, adventure.question)
    world.speak(captain, "A captain should not chase every odd thing that shines.")
    world.speak(cabin, "Then let us ask one careful question and look before we leap.")
    world.say(
        f"Captain {captain.name} felt an inner monologue stir inside his mind: "
        f'"I am an alcoholic, but I do not have to obey an old habit. Curiosity can be a compass '
        f'if I use it with care."'
    )
    world.say(f"{adventure.danger.capitalize()}. {parrot.name} flapped toward the safer side of the deck.")

    world.para()
    world.say(
        f"The captain checked the wind, the water, and the crew before he {adventure.action}. "
        f"That choice mattered because {adventure.danger}."
    )
    world.speak(cabin, "We found something, Captain. Shall we open it?")
    world.speak(captain, "Only after we understand what it might change.")
    world.say(f"At last, {adventure.discovery}.")

    world.para()
    world.say(f"Then came the twist: {adventure.twist.capitalize()}.")
    world.speak(cabin, "So the mystery was asking for help, not for gold.")
    world.speak(captain, "Aye. The best treasure is sometimes the truth we nearly sailed past.")
    world.say(
        f"The crew acted gently, and {adventure.ending}. They remembered that {adventure.lesson}."
    )
    captain.memes.update(curiosity=1.0, sobriety=0.8, trust=0.9)
    world.location.meters["tide"] = 0.2
    world.facts["resolved"] = True


def story_qa(world: World) -> list[QAItem]:
    captain: Character = world.facts["captain"]
    cabin: Character = world.facts["cabin"]
    adventure: Adventure = world.facts["adventure"]
    return [
        QAItem(
            question=f"Who was Captain {captain.name}, and what choice did he make with the last bottle?",
            answer=(
                f"Captain {captain.name} was an alcoholic pirate who poured the last bottle into the sea "
                "so he could keep his hands on the wheel and make a wiser choice."
            ),
        ),
        QAItem(
            question=f"What made {cabin.name} curious?",
            answer=f"{cabin.name} became curious because {adventure.clue}.",
        ),
        QAItem(
            question="What did the captain's inner monologue help him decide?",
            answer=(
                "It helped him decide that being alcoholic did not mean he had to obey an old habit; "
                "he could investigate carefully and choose sobriety and caution."
            ),
        ),
        QAItem(
            question="What was the twist, and how did the story end?",
            answer=f"The twist was that {adventure.twist}. In the end, {adventure.ending}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does alcoholic mean?",
            answer="Alcoholic describes a person who has a harmful dependence on alcohol and may need support to stop drinking.",
        ),
        QAItem(
            question="Why is curiosity useful?",
            answer="Curiosity can help someone ask questions, notice clues, and learn instead of making a quick guess.",
        ),
        QAItem(
            question="Why should a pirate check the water before sailing near rocks?",
            answer="Checking the water helps the pirate notice shallow places and avoid damaging the ship or hurting the crew.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private stream of thoughts a character has inside their mind.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    captain: Character = world.facts["captain"]
    cabin: Character = world.facts["cabin"]
    adventure: Adventure = world.facts["adventure"]
    return [
        f"Write a child-friendly pirate tale about alcoholic Captain {captain.name} choosing a safer path.",
        f"Include dialogue between {captain.name} and {cabin.name}, an inner monologue, curiosity about {adventure.clue}, and a clear twist.",
        f"End the pirate story with this concrete image: {adventure.ending}.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: name={entity.name} role={entity.role} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  location: {world.location.name} meters={world.location.meters}")
    lines.append(f"  dialogue turns: {len(world.dialogue_turns)}")
    lines.append(f"  resolved: {world.facts.get('resolved', False)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Mara", "Pip", "Biscuit", "Whisper Reef"),
    StoryParams("Tobin", "Kit", "Sprig", "Moonhook Isle"),
    StoryParams("Nell", "Jo", "Peaches", "Crescent Cay"),
    StoryParams("Rafe", "Finn", "Blue", "Lantern Island"),
    StoryParams("Sable", "Wren", "Buttons", "Starfish Key"),
]


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    risks = asp.atoms(model, "risk")
    choices = asp.atoms(model, "safe_choice")
    discoveries = asp.atoms(model, "discovery")
    if ("reef",) not in risks:
        print("MISMATCH: ASP did not detect the reef risk.")
        return 1
    if ("boat_hook",) not in choices or ("map",) not in discoveries:
        print("MISMATCH: ASP did not find the safe choice and discovery.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("resolved"):
            print("MISMATCH: generated story did not resolve.")
            return 1
        if "alcoholic" not in sample.story.lower() or "twist" not in sample.story.lower():
            print("MISMATCH: required narrative elements are missing.")
            return 1
    print("OK: ASP and Python agree; generated stories resolve.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("risk:", asp.atoms(model, "risk"))
        print("safe_choice:", asp.atoms(model, "safe_choice"))
        print("discovery:", asp.atoms(model, "discovery"))
        return

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(args.n, 0)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)

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
