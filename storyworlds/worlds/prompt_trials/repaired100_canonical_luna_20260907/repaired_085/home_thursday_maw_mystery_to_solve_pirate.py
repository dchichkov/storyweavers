#!/usr/bin/env python3
"""A child-safe pirate tale about solving a mystery at home on Thursday."""

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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("distance", "risk", "dust", "sound"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "curiosity", "trust", "joy", "calm"):
            self.memes.setdefault(key, 0.0)


@dataclass
class Home:
    place: str = "home"
    room: str = "attic"
    locked_chest: bool = True
    safe_lantern: bool = True


@dataclass
class StoryParams:
    place: str
    day: str
    hero: str
    helper: str
    object_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Mystery:
    title: str
    task: str
    first_clue: str
    guess: str
    second_clue: str
    test: str
    truth: str
    action: str
    repair: str
    result: str
    lesson: str
    ending: str


MYSTERIES = [
    Mystery(
        "the missing brass compass",
        "dusting an old sea chest",
        "a round clean mark beneath the chest lid",
        "a tiny sea ghost had carried it away",
        "three blue threads caught on a splinter beside the window",
        "followed the threads without opening the locked chest",
        "a toy parrot had dragged the compass toward its bright ribbon nest",
        "asked an adult to lift the chest lid and moved the parrot's perch",
        "returned the compass to its padded box",
        "the family found the north star on the next clear night",
        "A strange clue deserves a calm test before a spooky guess",
        "the compass winked beside a mug of cocoa while the toy parrot guarded its ribbons",
    ),
    Mystery(
        "the vanishing captain's bell",
        "sorting maps on a Thursday afternoon",
        "a bell-shaped dust print beside the hearth",
        "the captain's bell had rolled through a secret tunnel",
        "a line of flour led from the kitchen to a basket of clean towels",
        "asked the cook and checked the basket with a wooden spoon",
        "a puppy had nudged the bell into the towel basket",
        "called the puppy gently and kept hands away from the hearth",
        "washed the bell and hung it by the map shelf",
        "everyone heard dinner called without a single shout",
        "A trail can explain a mystery better than an exciting rumor",
        "the bell chimed over supper as rain tapped the home windows",
    ),
    Mystery(
        "the whispering map",
        "preparing a pretend voyage at home",
        "a map corner moved though every window was shut",
        "the map was whispering a warning from the deep",
        "a loose thread connected the corner to a spinning desk fan",
        "turned off the fan and watched the paper from a safe distance",
        "the thread had caught the fan's breeze and made the whispering sound",
        "asked an adult to unplug the fan before freeing the thread",
        "taped the map flat and placed it under a wooden ruler",
        "the pretend crew sailed around the sofa without losing its route",
        "Test the ordinary cause before naming a magical one",
        "the map lay smooth while paper ships crossed a blanket sea",
    ),
    Mystery(
        "the silver tooth in the maw",
        "examining a friendly wooden sea monster",
        "one shiny tooth was missing from the monster's maw",
        "a pirate had hidden treasure inside its mouth",
        "silver paint glittered beside a loose floorboard",
        "used a flashlight and asked an adult to inspect the board",
        "the tooth had slipped into a crack when the toy was moved",
        "kept fingers away from the crack and lifted the toy with help",
        "retrieved the tooth with a safe magnet",
        "the monster grinned again without needing a treasure hunt",
        "Look closely at a small object before making a large story",
        "the wooden maw smiled beside a bowl of sliced apples",
    ),
    Mystery(
        "the cold treasure key",
        "checking a treasure box before bedtime",
        "a key felt cold even in a warm room",
        "the key had been chilled by a moonlit curse",
        "a damp ring marked the shelf under an open pitcher",
        "closed the pitcher and compared the key with another metal button",
        "water from the pitcher had cooled the key by evaporation",
        "wiped the shelf and asked an adult to move the pitcher",
        "dried the key and placed it in its labeled envelope",
        "the treasure box opened with a wooden thump",
        "A nearby ordinary cause may solve an unusual feeling",
        "the key turned in the lock as Thursday stars appeared",
    ),
    Mystery(
        "the rattling maw",
        "reading a pirate book beside the toy monster",
        "the monster's maw rattled whenever someone spoke",
        "a tiny pirate was trapped inside",
        "the rattle stopped when the book moved from the rug",
        "lifted the book with both hands and listened from the side",
        "a wooden bead in the book's loose cover was tapping the toy",
        "asked an adult to repair the book instead of shaking it",
        "removed the bead and mended the cover",
        "the monster became quiet enough for the story to finish",
        "Listening carefully can turn a frightening sound into a simple answer",
        "the quiet maw opened toward a warm lamp and a finished book",
    ),
]

ROUTES = [
    (
        "On Thursday, the little home felt like a ship waiting for a tide.",
        "The mystery grew, but the crew chose evidence over a dramatic guess.",
        "By evening, their home felt safer because everyone had helped solve one small puzzle.",
    ),
    (
        "Thursday brought gray clouds, a warm lamp, and a very curious crew.",
        "They treated the strange clue like a treasure map: one mark at a time.",
        "Their best prize was not gold but the clear answer they found together.",
    ),
    (
        "At home, ordinary rooms can seem grand when a pirate story begins.",
        "The crew paused before touching anything and let each clue change the plan.",
        "The solved mystery made the rest of the evening bright and peaceful.",
    ),
    (
        "The attic at home held maps, toys, and more questions than treasure.",
        "A careful conversation helped the crew separate what they knew from what they imagined.",
        "The house settled into a happy hush after the last clue made sense.",
    ),
    (
        "A Thursday adventure started with a tiny detail near an old toy.",
        "The crew followed a safe trail instead of chasing the most exciting explanation.",
        "Even the toy maw seemed pleased when the room returned to order.",
    ),
]


HEROES = ["Luna", "Mara", "Pip", "Cora", "Finn", "Jo"]
HELPERS = ["Aunt Bea", "Uncle Tom", "Nell", "Rafi", "Milo", "Tess"]
OBJECTS = ["wooden compass", "toy treasure chest", "painted sea monster", "folded map"]


class World:
    def __init__(self, home: Home):
        self.home = home
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)


def _choose(params: StoryParams) -> tuple[Mystery, tuple[str, str, str]]:
    value = params.seed if params.seed is not None else 0
    return MYSTERIES[value % len(MYSTERIES)], ROUTES[(value // len(MYSTERIES)) % len(ROUTES)]


def tell_story(params: StoryParams) -> World:
    if params.day.lower() != "thursday":
        raise StoryError("This pirate mystery requires Thursday.")
    if not params.place.strip():
        raise StoryError("The story needs a home setting.")
    if params.hero == params.helper:
        raise StoryError("The hero and helper must be different characters.")

    mystery, route = _choose(params)
    world = World(Home(place=params.place))
    hero = world.add(Entity(params.hero, "character", "young pirate"))
    helper = world.add(Entity(params.helper, "character", "trusted helper"))
    object_entity = world.add(
        Entity("mystery_object", "prop", "pirate object", label=params.object_name, owner=params.hero)
    )
    maw = world.add(Entity("maw", "prop", "friendly wooden sea monster", label="maw"))
    clue = world.add(Entity("clue", "prop", "physical clue", label=mystery.first_clue))

    hero.memes.update(worry=0.8, curiosity=1.0)
    helper.memes["trust"] = 0.8
    maw.meters["risk"] = 0.1
    clue.meters["sound"] = 0.2

    world.say(route[0])
    world.say(
        f"At {params.place}, {params.hero} was {mystery.task} when {params.helper} arrived "
        f"with the {params.object_name}."
    )
    world.say(
        f'"Ahoy, {params.helper}," {params.hero} said. "Can you help me solve a mystery before our home becomes a pirate port?"'
    )
    world.say(
        f'"Aye," {params.helper} replied. "Tell me what you noticed, and we will check it safely."'
    )
    world.say(f"Near the friendly wooden maw, they noticed {mystery.first_clue}.")
    world.say(
        f'"My first guess is that {mystery.guess}," {params.hero} said. '
        f'"But a guess is not proof."'
    )
    world.say(route[1])
    world.say(f"Then they found another clue: {mystery.second_clue}.")
    world.say(
        f'"That clue changes our plan," {params.helper} said. "Let us {mystery.test}."'
    )
    world.say(f"The careful check showed that {mystery.truth}.")
    world.say(f"They {mystery.action}.")
    world.say(f"Afterward, they {mystery.repair}. As a result, {mystery.result}.")
    world.say(
        f'"{mystery.lesson}," {params.hero} said, while the maw watched with its harmless wooden grin.'
    )
    world.say(route[2])
    world.say(f"That night, {mystery.ending}.")

    hero.memes.update(worry=0.0, calm=1.0, joy=1.0)
    helper.memes.update(trust=1.0, calm=1.0)
    maw.meters["risk"] = 0.0
    world.facts.update(
        hero=hero,
        helper=helper,
        object_entity=object_entity,
        maw=maw,
        clue=clue,
        mystery=mystery,
        resolved=True,
        child_safe=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    mystery = world.facts["mystery"]
    return [
        'Write a child-safe Pirate Tale set at home on Thursday using the words "home," "thursday," and "maw."',
        f'Tell a dialogue-rich Mystery to Solve about "{mystery.title}" without using danger or magic as the answer.',
        f"Write a pirate mystery where the key clue is that {mystery.second_clue}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"]
    helper = facts["helper"]
    mystery = facts["mystery"]
    return [
        QAItem(
            f"What were {hero.id} and {helper.id} doing at home on Thursday?",
            f"{hero.id} was {mystery.task}, and {helper.id} joined the search with a pirate object. They decided to investigate the mystery together.",
        ),
        QAItem(
            "What was the first clue?",
            f"The first clue was that {mystery.first_clue}. It made the mystery interesting, but it did not prove the first guess.",
        ),
        QAItem(
            "What clue changed their plan?",
            f"They discovered that {mystery.second_clue}. That physical detail led them to perform a safer, more useful check.",
        ),
        QAItem(
            f"What really caused {mystery.title}?",
            f"They learned that {mystery.truth}. The answer came from checking the clues rather than believing a spooky pirate rumor.",
        ),
        QAItem(
            "How did the crew solve the mystery?",
            f"They {mystery.action} Then they {mystery.repair}, and {mystery.result}.",
        ),
        QAItem(
            "What lesson did the pirate crew learn?",
            f"They learned that {mystery.lesson}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a maw?",
            "A maw is the mouth of a large creature. In this story, the maw belongs to a friendly wooden sea monster and is not dangerous.",
        ),
        QAItem(
            "What does it mean to solve a mystery?",
            "To solve a mystery means to gather clues, test sensible explanations, and use the evidence to find what happened.",
        ),
        QAItem(
            "Why is it useful to talk with a helper?",
            "A helper can notice a different clue, ask a careful question, and help someone choose a safe next step.",
        ),
        QAItem(
            "What is a Pirate Tale?",
            "A Pirate Tale is an adventure story with a crew, sea-going imagination, treasure-like objects, and brave problem solving.",
        ),
        QAItem(
            "What does Thursday mean in the story?",
            "Thursday is the day when the home mystery begins. It gives the adventure a clear time and keeps the setting connected to ordinary life.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *sample.prompts, "", "== story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(
            f"{entity.id}: kind={entity.kind} type={entity.type} "
            f"meters={meters} memes={memes}"
        )
    mystery = world.facts["mystery"]
    lines.append(f"mystery: {mystery.title}")
    lines.append(f"resolved: {world.facts['resolved']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Home Thursday pirate mystery storyworld.")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = rng.choice(HEROES)
    helper = rng.choice([name for name in HELPERS if name != hero])
    return StoryParams(
        place="home",
        day="Thursday",
        hero=hero,
        helper=helper,
        object_name=rng.choice(OBJECTS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


ASP_RULES = r"""
place(home).
day(thursday).
feature(mystery_to_solve).
style(pirate_tale).
object(maw).
safe_clue :- place(home), day(thursday), feature(mystery_to_solve), object(maw).
resolved :- safe_clue.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("place", "home"),
            asp.fact("day", "thursday"),
            asp.fact("feature", "mystery_to_solve"),
            asp.fact("style", "pirate_tale"),
            asp.fact("object", "maw"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp

        symbols = asp.one_model(asp_program("#show safe_clue/0.\n#show resolved/0."))
        names = {str(symbol) for symbol in symbols}
        if "safe_clue" not in names or "resolved" not in names:
            return 1
    except Exception:
        return 1

    for seed in range(min(len(MYSTERIES), 6)):
        params = StoryParams(
            place="home",
            day="Thursday",
            hero="Luna",
            helper="Aunt Bea",
            object_name="wooden compass",
            seed=seed,
        )
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("resolved"):
            return 1
        if not sample.story_qa or not all(item.answer.strip() for item in sample.story_qa):
            return 1
        if any(token in sample.story for token in ("{", "}", "None")):
            return 1
    return 0


def main() -> None:
    args = build_parser().parse_args()
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.show_asp or args.asp:
        print(asp_program("#show safe_clue/0.\n#show resolved/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.all:
        samples = [
            generate(
                StoryParams(
                    place="home",
                    day="Thursday",
                    hero="Luna",
                    helper="Aunt Bea",
                    object_name="wooden compass",
                    seed=index,
                )
            )
            for index in range(len(MYSTERIES))
        ]
    else:
        samples = []
        for offset in range(max(1, args.n)):
            seed = base_seed + offset
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
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
