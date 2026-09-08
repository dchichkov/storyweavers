#!/usr/bin/env python3
"""
A small superhero quest world about losing something important, discovering a
surprising twist, and learning that a careful rescue can turn loss into hope.
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
STORYWORLDS_ROOT = next(parent for parent in HERE.parents if (parent / "results.py").is_file())
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
    hero_name: str
    friend_name: str
    keeper_name: str
    quest: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Character] = {}
        self.location = Location("the skybridge park")
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.dialogue_turns: list[tuple[str, str]] = []

    def add(self, character: Character) -> Character:
        self.entities[character.id] = character
        return character

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def paragraph(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass(frozen=True)
class QuestCase:
    object_name: str
    object_description: str
    loss: str
    danger: str
    clue: str
    hero_action: str
    friend_action: str
    keeper_action: str
    twist: str
    result: str
    ending: str
    lesson: str


HERO_NAMES = ["Luna", "Nova", "Comet", "Spark", "Orbit"]
FRIEND_NAMES = ["Milo", "Ruby", "Theo", "Iris", "Zane"]
KEEPER_NAMES = ["Mara", "Nina", "June", "Tess", "Ada"]
QUESTS = [
    "return the moon badge before the evening parade",
    "find the tiny beacon that guides the rooftop birds home",
    "recover the star map before the clouds cover the stars",
    "bring the town's lantern key back to the night garden",
]

CASES = [
    QuestCase(
        object_name="moon badge",
        object_description="a silver badge that glowed whenever someone helped another person",
        loss="the moon badge slipped from Luna's cape and vanished beneath the bridge",
        danger="the rising river could carry it away",
        clue="a faint silver blink appeared beside a nest of reeds",
        hero_action="made a gentle ribbon of light across the water",
        friend_action="followed the silver blinks without stepping into the current",
        keeper_action="lowered a long rescue net from the bridge rail",
        twist="the badge was not in the river at all; a young heron had tucked it beside its nest because the glow warmed its frightened chick",
        result="the team recovered the badge without disturbing the nest",
        ending="the badge shone on Luna's cape while the heron chick settled under its mother's wing",
        lesson="a lost thing may be close to someone who needs it",
    ),
    QuestCase(
        object_name="rooftop beacon",
        object_description="a blue beacon that sent a safe path of light across the rooftops",
        loss="the rooftop beacon rolled from its stand and disappeared into a laundry basket",
        danger="without it, the returning birds might circle into the smoky chimney wind",
        clue="a row of clean feathers pointed toward the old bell tower",
        hero_action="spread a quiet shield between the birds and the chimney gusts",
        friend_action="checked each basket only after asking its owner",
        keeper_action="opened the bell tower door and called softly into the dark",
        twist="the beacon had been carried away by a puppy that thought its blue light was a toy",
        result="the puppy returned the beacon when Ruby traded it for a bright rubber ball",
        ending="blue light marked the safe roof while the puppy slept beside its new toy",
        lesson="a quest becomes kinder when we ask who may have moved the missing thing",
    ),
    QuestCase(
        object_name="star map",
        object_description="a folded map showing the safest places to watch the night sky",
        loss="the star map flew from Luna's hand and vanished in the festival breeze",
        danger="the paper could tear on the thorny hill below",
        clue="a paper corner was caught on a red kite string",
        hero_action="slowed the wind around the kite without snapping its tail",
        friend_action="climbed the marked path and kept the loose paper from scraping the thorns",
        keeper_action="untangled the string with a wooden hook",
        twist="the map had landed inside the kite, where its folds made a picture of a new constellation",
        result="the map was freed and the kite was repaired instead of thrown away",
        ending="children held the kite high as its map-shaped shadow crossed the first stars",
        lesson="a surprising change can reveal a new way to see an old plan",
    ),
    QuestCase(
        object_name="lantern key",
        object_description="a brass key that opened the night garden's warm lanterns",
        loss="the lantern key dropped through a crack in the garden path",
        danger="the garden's young plants would freeze if the lanterns stayed dark",
        clue="a line of glowing beetles gathered beside one loose stone",
        hero_action="lit the crack with a soft golden beam",
        friend_action="counted the stones so the path would be rebuilt correctly",
        keeper_action="lifted the loose stone with a small garden lever",
        twist="the key had fallen into a hollow root, where a mouse had used it to hold open a tiny doorway",
        result="the mouse moved safely aside and the key came free",
        ending="the lanterns glowed above the garden while the mouse peeked from its warm doorway",
        lesson="careful observation can protect both the goal and a smaller neighbor",
    ),
    QuestCase(
        object_name="rainbow compass",
        object_description="a compass that pointed toward anyone who needed help",
        loss="the rainbow compass disappeared during a cloudburst",
        danger="its wet paper dial could dissolve before the rescue team found it",
        clue="colored drops led from the fountain to a covered bus stop",
        hero_action="held an umbrella of light over the trail",
        friend_action="read the colored drops as a path instead of wiping them away",
        keeper_action="moved the bench cushions and checked underneath them",
        twist="a tired traveler had found the compass and used its needle to locate the warm bus stop",
        result="the traveler returned it after Luna promised to guide the last passengers home",
        ending="the compass pointed at the waiting bus, then rested safely in Luna's palm",
        lesson="helping someone else may be the truest part of finding what was lost",
    ),
]

OPENINGS = [
    "The city was bright with banners for the nighttime hero parade.",
    "Clouds curled over the rooftops as the young heroes began their evening patrol.",
    "A warm bell rang across the neighborhood just as the quest began.",
    "The park was full of children, lanterns, and superhero questions.",
]

DIALOGUE = [
    (
        "I lost the important thing, and the parade cannot wait.",
        "Then we will not guess. We will look for clues.",
        "A clue can tell us what happened, not just where to search.",
    ),
    (
        "Everyone stay calm. Losing something is not the end of the quest.",
        "What should we protect first?",
        "The missing object, the people nearby, and anyone who may have found it.",
    ),
    (
        "My cape is empty. The treasure is gone!",
        "Your eyes are still full of good ideas, Luna.",
        "Let us follow the smallest change we can see.",
    ),
    (
        "Stop rushing. A lost thing may have a story of its own.",
        "I will watch the path while you watch the air.",
        "And I will ask before I take anything from a hiding place.",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Superhero lost-object quest story world.")
    parser.add_argument("--hero-name", choices=HERO_NAMES)
    parser.add_argument("--friend-name", choices=FRIEND_NAMES)
    parser.add_argument("--keeper-name", choices=KEEPER_NAMES)
    parser.add_argument("--quest", choices=QUESTS)
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
    hero = args.hero_name or rng.choice(HERO_NAMES)
    friend = args.friend_name or rng.choice([name for name in FRIEND_NAMES if name != hero])
    keeper = args.keeper_name or rng.choice(KEEPER_NAMES)
    quest = args.quest or rng.choice(QUESTS)
    if hero == friend:
        raise StoryError("The hero and friend must have different names.")
    return StoryParams(hero_name=hero, friend_name=friend, keeper_name=keeper, quest=quest)


def _case_for(params: StoryParams) -> QuestCase:
    key = params.seed if params.seed is not None else sum(ord(c) for c in params.hero_name + params.quest)
    return CASES[key % len(CASES)]


def _setup(params: StoryParams) -> World:
    world = World()
    world.add(Character("hero", params.hero_name, "hero", memes={"courage": 1.0, "worry": 0.4}))
    world.add(Character("friend", params.friend_name, "friend", memes={"curiosity": 1.0}))
    world.add(Character("keeper", params.keeper_name, "keeper", memes={"patience": 1.0}))
    world.facts["params"] = params
    return world


def _speak(world: World, speaker: Character, line: str) -> None:
    world.dialogue_turns.append((speaker.name, line))
    world.say(f'{speaker.name} said, "{line}"')


def generate_story(world: World, params: StoryParams) -> None:
    hero = world.entities["hero"]
    friend = world.entities["friend"]
    keeper = world.entities["keeper"]
    case = _case_for(params)
    key = params.seed if params.seed is not None else sum(ord(c) for c in params.hero_name + params.friend_name)
    opening = OPENINGS[key % len(OPENINGS)]
    first, second, third = DIALOGUE[key % len(DIALOGUE)]

    world.facts.update(
        case=case,
        opening=opening,
        first=first,
        second=second,
        third=third,
        lost=True,
        resolved=False,
    )
    world.location.meters["danger"] = 1.0
    world.location.memes["hope"] = 0.3

    world.say(opening)
    world.say(
        f"{hero.name}, a young superhero, had promised to {params.quest}. "
        f"The quest mattered because the {case.object_name} was {case.object_description}."
    )
    world.say(f"Then {case.loss}. {case.danger.capitalize()}.")

    world.paragraph()
    _speak(world, hero, first)
    _speak(world, friend, second)
    _speak(world, keeper, third)
    world.say(f"{friend.name} looked closely and found the clue: {case.clue}.")
    world.say(
        f"The heroes did not snatch at the first hiding place. They made a plan to protect the path, "
        f"the missing {case.object_name}, and anyone who might be nearby."
    )

    world.paragraph()
    world.say(f"First, {hero.name} {case.hero_action}.")
    world.say(f"Next, {friend.name} {case.friend_action}.")
    world.say(f"Finally, Keeper {keeper.name} {case.keeper_action}.")
    _speak(world, keeper, "A careful rescue leaves room for every living thing.")
    world.say(f"Then came the twist: {case.twist}.")
    _speak(world, hero, "We found it, but finding it is not enough. We must leave this place safer.")
    world.say(f"Because of their patience, {case.result}.")
    world.say(f"{case.ending}.")
    world.say(f"The heroes learned that {case.lesson}.")
    world.location.meters["danger"] = 0.0
    world.location.memes["hope"] = 1.0
    world.facts["resolved"] = True


def story_qa(world: World) -> list[QAItem]:
    case: QuestCase = world.facts["case"]
    hero = world.entities["hero"]
    friend = world.entities["friend"]
    return [
        QAItem(
            question=f"What did {hero.name} lose at the beginning of the quest?",
            answer=f"{hero.name} lost the {case.object_name}: {case.loss}.",
        ),
        QAItem(
            question=f"What clue did {friend.name} notice?",
            answer=f"{friend.name} noticed that {case.clue}.",
        ),
        QAItem(
            question="What was the twist in the search?",
            answer=f"The twist was that {case.twist}.",
        ),
        QAItem(
            question="How did the heroes solve the problem, and what showed that the ending had changed?",
            answer=(
                f"{hero.name} {case.hero_action}; {friend.name} {case.friend_action}; and the keeper "
                f"{case.keeper_action}. In the ending, {case.ending}."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a purposeful journey in which someone searches, solves a problem, or helps others.",
        ),
        QAItem(
            question="Why should people look for clues before acting?",
            answer="Clues can reveal what happened and help people choose a safer and kinder action.",
        ),
        QAItem(
            question="What does it mean to lose something?",
            answer="To lose something means it is no longer where you expected it to be, so you must search carefully or ask for help.",
        ),
        QAItem(
            question="Why can a twist change a story?",
            answer="A twist reveals surprising information that changes what the characters understand about the problem.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    case: QuestCase = world.facts["case"]
    hero = world.entities["hero"]
    friend = world.entities["friend"]
    return [
        f"Write a child-friendly superhero quest about {hero.name} losing a {case.object_name}.",
        f"Include dialogue between {hero.name} and {friend.name}, the clue that {case.clue}, and the twist that {case.twist}.",
        f"End with this concrete image: {case.ending}.",
    ]


ASP_RULES = r"""
#show risk/1.
#show quest/1.
#show twist/1.
#show resolved/1.
risk(lost_object) :- lost(lost_object).
quest(hero_quest) :- lost(lost_object), clue(found_clue).
twist(surprising_cause) :- quest(hero_quest), helper(present).
resolved(hero_quest) :- twist(surprising_cause), safe(path).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("lost", "lost_object"),
            asp.fact("clue", "found_clue"),
            asp.fact("helper", "present"),
            asp.fact("safe", "path"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: name={entity.name} role={entity.role} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  location: {world.location.name} meters={world.location.meters} memes={world.location.memes}")
    lines.append(f"  dialogue turns: {len(world.dialogue_turns)}")
    lines.append(f"  resolved: {world.facts.get('resolved')}")
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
    world = _setup(params)
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
    StoryParams("Luna", "Milo", "Mara", QUESTS[0]),
    StoryParams("Nova", "Ruby", "Nina", QUESTS[1]),
    StoryParams("Comet", "Theo", "June", QUESTS[2]),
    StoryParams("Spark", "Iris", "Tess", QUESTS[3]),
]


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show risk/1.\n#show quest/1.\n#show twist/1.\n#show resolved/1."))
    required = {
        ("lost_object",) in asp.atoms(model, "risk"),
        ("hero_quest",) in asp.atoms(model, "quest"),
        ("surprising_cause",) in asp.atoms(model, "twist"),
        ("hero_quest",) in asp.atoms(model, "resolved"),
    }
    if not all(required):
        print("MISMATCH: ASP did not produce the expected quest state.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("resolved"):
            print("MISMATCH: generated story did not resolve.")
            return 1
        if len(sample.world.dialogue_turns) < 5:
            print("MISMATCH: generated story lacks dialogue.")
            return 1
    print("OK: Python and ASP agree on the lost-object quest.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show risk/1.\n#show quest/1.\n#show twist/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show risk/1.\n#show quest/1.\n#show twist/1.\n#show resolved/1."))
        print("risk:", asp.atoms(model, "risk"))
        print("quest:", asp.atoms(model, "quest"))
        print("twist:", asp.atoms(model, "twist"))
        print("resolved:", asp.atoms(model, "resolved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            index += 1
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
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
