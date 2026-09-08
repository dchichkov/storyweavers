#!/usr/bin/env python3
"""A child-facing pirate tale about a historic shutter, friendship, and clever repairs."""

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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Scene:
    place: str
    weather: str
    landmark: str


@dataclass
class StoryParams:
    place: str
    shutter: str
    captain: str
    friend: str
    helper: str
    problem: str = ""
    route: str = ""
    seed: Optional[int] = None


@dataclass(frozen=True)
class PirateProblem:
    lost: str
    worry: str
    first_plan: str
    failed: str
    clue: str
    truth: str
    repair: str
    lesson: str
    ending: str


@dataclass
class World:
    scene: Scene
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


PLACES = {
    "cove": Scene("Moonwake Cove", "a salty morning wind", "an old stone watchtower"),
    "harbor": Scene("Lantern Harbor", "a bright breeze", "a bell tower above the docks"),
    "island": Scene("Parrot-Key Island", "warm gusts from the sea", "a weathered lighthouse"),
}

SHUTTERS = {
    "blue": "the historic blue shutter",
    "red": "the historic red shutter",
    "green": "the historic green shutter",
    "gold": "the historic gold shutter",
}

CAPTAINS = {"Luna": "girl", "Mara": "girl", "Pip": "boy", "Tavi": "boy"}
FRIENDS = {"Niko": "boy", "Suri": "girl", "Beau": "boy", "Mina": "girl"}
HELPERS = {"parrot": "parrot", "dolphin": "dolphin", "turtle": "turtle", "monkey": "monkey"}

PROBLEMS = {
    "storm_rope": PirateProblem(
        "the signal rope that lifted the harbor flag",
        "without the flag, friendly ships might miss the safe channel",
        "pulled the rope together from the deck",
        "the rope only tightened around a pulley and would not move",
        "a salt-stiff knot was wedged behind the shutter hinge",
        "the wind had pushed the rope through the open shutter before a gust slammed it closed",
        "softened the knot with warm water, opened the shutter with a boat hook, and replaced the rope",
        "a calm team can untangle what one sailor cannot",
        "the repaired flag rose above the historic shutter as ships cheered below",
    ),
    "map_damp": PirateProblem(
        "the captain's map of the reef passage",
        "the crew could not safely steer home without its marks",
        "spread the map in the sun",
        "the damp paper curled tighter instead of flattening",
        "a dry corner was tucked beneath the shutter's iron latch",
        "a sea splash had blown the map behind the shutter during the night",
        "lifted the latch, dried the map between clean cloths, and copied its marks",
        "good friends share careful jobs when a treasure map is fragile",
        "the reef route shone on a dry map beneath the open historic shutter",
    ),
    "bell_silent": PirateProblem(
        "the little brass bell used for the noon watch",
        "the crew needed its sound to warn boats away from rocks",
        "rang it harder and harder",
        "the bell stayed silent, though the clapper swung",
        "a strip of old sailcloth was caught between the bell and its frame",
        "the wind had blown the cloth through the shutter and into the bell housing",
        "freed the cloth, polished the bell, and tied a small guard below the shutter",
        "loud effort is not always better than patient looking",
        "one clear bell rang across the harbor beside the repaired shutter",
    ),
    "lantern_dark": PirateProblem(
        "the lantern that guided the evening watch",
        "darkness could hide the reef from every passing boat",
        "trimmed the wick and added more oil",
        "the flame still flickered because the lantern glass was blocked",
        "a fallen shutter slat covered the lantern's glass",
        "a loose hinge had let the historic shutter sag into the lantern frame",
        "braced the hinge, lifted the slat, and cleaned the glass",
        "problem solving begins by checking what is actually blocking the light",
        "the lantern glowed warmly through the open shutter at sunset",
    ),
    "parrot_feather": PirateProblem(
        "the bright feather pennant for the crew's welcome",
        "the crew's shy new sailor thought nobody would know where to meet",
        "searched the whole beach in separate directions",
        "the friends became scattered and found only driftwood",
        "a feather was caught on the shutter's inner peg",
        "the pennant had blown through the shutter and folded into the window recess",
        "searched in pairs, freed the pennant, and tied it to the mast",
        "friendship keeps a search together",
        "the feather pennant waved above the historic shutter while the crew shared mangoes",
    ),
    "chest_key": PirateProblem(
        "the tiny key to the ship's story chest",
        "the crew could not read the historic log inside",
        "shook every barrel near the dock",
        "the key was not in any barrel, and the noise upset the gulls",
        "a bright scratch led from the shutter sill to a coil of rope",
        "the key had slid along the sill when the shutter swung in the wind",
        "followed the scratch, retrieved the key with a magnet, and secured the shutter",
        "small clues can guide a large search",
        "the story chest opened beside the steady historic shutter, and everyone read together",
    ),
}

ROUTES = (
    "map_first",
    "friend_first",
    "clue_first",
    "storm_first",
    "quiet_first",
    "question_first",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A pirate tale about Luna, friendship, and a historic shutter."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--shutter", choices=sorted(SHUTTERS))
    parser.add_argument("--captain")
    parser.add_argument("--friend", choices=sorted(FRIENDS))
    parser.add_argument("--helper", choices=sorted(HELPERS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument(f"--{flag}", action="store_true")
    return parser


def valid_combos() -> list[tuple[str, str]]:
    return [(place, shutter) for place in sorted(PLACES) for shutter in sorted(SHUTTERS)]


ASP_RULES = """
valid(Place, Shutter) :- place(Place), shutter(Shutter).
friendship_required(Place, Shutter) :- valid(Place, Shutter).
problem_solving_required(Place, Shutter) :- valid(Place, Shutter).
#show valid/2.
#show friendship_required/2.
#show problem_solving_required/2.
"""


def asp_facts() -> str:
    import asp

    facts = [asp.fact("place", place) for place in PLACES]
    facts.extend(asp.fact("shutter", shutter) for shutter in SHUTTERS)
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    symbols = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(symbols, "valid")))


def asp_verify() -> int:
    python_combos = set(valid_combos())
    asp_combos = set(asp_valid_combos())
    if python_combos == asp_combos:
        print(f"OK: clingo gate matches valid_combos() ({len(python_combos)} combinations).")
        return 0
    print("MISMATCH:", sorted(python_combos - asp_combos), sorted(asp_combos - python_combos))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo
        for combo in valid_combos()
        if not args.place or combo[0] == args.place
        if not args.shutter or combo[1] == args.shutter
    ]
    if not combos:
        raise StoryError("No valid pirate tale fits those place and shutter choices.")

    place, shutter = rng.choice(combos)
    captain = args.captain or "Luna"
    if captain not in CAPTAINS:
        raise StoryError(f"Unknown captain {captain!r}; choose a friendly pirate name.")
    possible_friends = [name for name in sorted(FRIENDS) if name != captain]
    friend = args.friend or rng.choice(possible_friends or sorted(FRIENDS))
    return StoryParams(
        place=place,
        shutter=shutter,
        captain=captain,
        friend=friend,
        helper=args.helper or rng.choice(sorted(HELPERS)),
        problem=rng.choice(sorted(PROBLEMS)),
        route=rng.choice(ROUTES),
    )


def story_rng(params: StoryParams) -> random.Random:
    values = (
        params.seed,
        params.place,
        params.shutter,
        params.captain,
        params.friend,
        params.helper,
        params.problem,
        params.route,
    )
    text = "|".join(str(value) for value in values)
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> World:
    scene = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    rng = story_rng(params)
    world = World(scene)

    captain = world.add(
        Entity(
            id=params.captain,
            kind="character",
            type=CAPTAINS[params.captain],
            meters={"courage": 2.0},
            memes={"friendship": 1.0},
        )
    )
    friend = world.add(
        Entity(
            id=params.friend,
            kind="character",
            type=FRIENDS[params.friend],
            meters={"helpfulness": 2.0},
            memes={"trust": 1.0},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper,
            kind="character",
            type=HELPERS[params.helper],
            meters={"reach": 1.0},
            memes={"curiosity": 1.0},
        )
    )
    shutter = world.add(
        Entity(
            id=params.shutter,
            kind="object",
            type="historic_shutter",
            label=SHUTTERS[params.shutter],
            meters={"hinge_strength": 1.0},
            memes={"memory": 1.0},
        )
    )

    opening = {
        "map_first": (
            f"Captain {captain.id} spread a salt-stained map across the deck at {scene.place}. "
            f"Beside {scene.landmark} stood {shutter.label}, a historic shutter that had watched many ships sail home."
        ),
        "friend_first": (
            f"At {scene.place}, Captain {captain.id} and {friend.id} checked on one another before checking the ship. "
            f"Their first stop was {shutter.label}, the historic shutter beside {scene.landmark}."
        ),
        "clue_first": (
            f"{captain.id} noticed a strange mark on {shutter.label} at {scene.place}. "
            f"That historic shutter stood near {scene.landmark}, where the crew had just discovered that {problem.lost} was missing."
        ),
        "storm_first": (
            f"A gust swept across {scene.place} while Captain {captain.id} guarded the deck. "
            f"The crew needed {problem.lost}, and {shutter.label} banged beside {scene.landmark}."
        ),
        "quiet_first": (
            f"The sea grew quiet at {scene.place}, but the crew heard an uneasy creak from {shutter.label}. "
            f"The historic shutter rested beside {scene.landmark}, while {problem.lost} had disappeared."
        ),
        "question_first": (
            f'"What changed?" {captain.id} asked at {scene.place}. '
            f"Nobody answered at first. Then {friend.id} pointed toward {shutter.label}, the historic shutter beside {scene.landmark}, and remembered {problem.lost}."
        ),
    }
    world.say(opening[params.route])
    world.say(
        rng.choice(
            [
                f"{friend.id} tied a blue ribbon between the two friends so they would not lose one another in the busy search.",
                f"The {helper.id} watched from nearby while {captain.id} and {friend.id} made a list of facts.",
                f"{captain.id} gave {friend.id} the ship's pencil, because every good crew member deserved a voice.",
                f"Though the sea wind tugged at their hats, {captain.id} and {friend.id} stayed shoulder to shoulder.",
            ]
        )
    )
    world.para()

    world.say(f"The missing thing mattered because {problem.worry}.")
    world.say(
        rng.choice(
            [
                f'"I have a plan," said {captain.id}. "We will {problem.first_plan}."',
                f'{captain.id} pointed toward the deck. "Let us {problem.first_plan}," the captain said.',
                f'"A crew solves trouble together," {friend.id} answered. "First, we can {problem.first_plan}."',
            ]
        )
    )
    world.say(f"They tried, but {problem.failed}. The first plan had not solved the problem.")
    captain.meters["courage"] += 1.0
    friend.memes["trust"] += 1.0
    world.say(
        rng.choice(
            [
                f'"That did not work," {captain.id} admitted. "{friend.id}, what did you notice?"',
                f'{friend.id} shook their head. "We need a better question, not a louder effort."',
                f'"No blaming," {captain.id} said. "We can change the plan and keep helping one another."',
            ]
        )
    )
    world.para()

    world.say(f"Together, the friends inspected the deck, the ropes, and {shutter.label}.")
    world.say(f"At last, {friend.id} found the important clue: {problem.clue}.")
    world.say(
        rng.choice(
            [
                f"The {helper.id} gave a small call, and {captain.id} realized the clue pointed behind the shutter.",
                f"{captain.id} held the lantern while {friend.id} followed the clue without disturbing it.",
                f"The friends compared the clue with their list. This time, every detail pointed in the same direction.",
            ]
        )
    )
    world.para()

    world.say(f"The truth was that {problem.truth}.")
    world.say(
        rng.choice(
            [
                f"{captain.id} and {friend.id} worked as one crew: they {problem.repair}.",
                f'"Together," said {captain.id}. Then the friends {problem.repair}.',
                f"The {helper.id} helped keep watch while the friends {problem.repair}.",
            ]
        )
    )
    shutter.meters["hinge_strength"] = 3.0
    captain.memes["friendship"] = 2.0
    friend.memes["trust"] = 2.0
    world.say(f"Captain {captain.id} wrote in the ship's log: {problem.lesson}.")
    world.say(
        rng.choice(
            [
                f"At sunset, {problem.ending}.",
                f"When the tide turned, {problem.ending}.",
                f"Before the crew sailed on, {problem.ending}.",
            ]
        )
    )

    world.facts.update(
        captain=captain,
        friend=friend,
        helper=helper,
        shutter=shutter,
        scene=scene,
        problem=problem,
        truth=problem.truth,
        repair=problem.repair,
        lesson=problem.lesson,
        ending=problem.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    problem = facts["problem"]
    return [
        (
            f"Write a short pirate tale for a young child about Captain {facts['captain'].id}, "
            f"{facts['friend'].id}, and {facts['shutter'].label}."
        ),
        (
            f"Tell a friendship story in which the crew solves a problem after learning that "
            f"{problem.truth}."
        ),
        (
            f"Write an adventure at {facts['scene'].place} that includes the clue "
            f"'{problem.clue}' and ends with {problem.ending}."
        ),
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    problem = facts["problem"]
    return [
        QAItem(
            question=f"What was missing when Captain {facts['captain'].id} and {facts['friend'].id} worked near {facts['shutter'].label}?",
            answer=f"{problem.lost.capitalize()} was missing at {facts['scene'].place}.",
        ),
        QAItem(
            question=f"Why did the missing item matter to the pirate crew?",
            answer=f"It mattered because {problem.worry.capitalize()}.",
        ),
        QAItem(
            question=f"How did the first plan change the friends' problem solving?",
            answer=f"They tried to {problem.first_plan}, but {problem.failed}. They learned to change the plan instead of giving up or blaming one another.",
        ),
        QAItem(
            question=f"What clue helped reveal the truth behind {facts['shutter'].label}?",
            answer=f"{facts['friend'].id} found that {problem.clue}. This showed that {problem.truth}.",
        ),
        QAItem(
            question=f"How did the friends repair the problem?",
            answer=f"They worked together and {problem.repair}. Their teamwork made the historic shutter safe again.",
        ),
        QAItem(
            question=f"What lesson did Captain {facts['captain'].id} write in the ship's log?",
            answer=f"The lesson was that {problem.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a hinged cover that can close over a window or opening. It can protect a room from wind, rain, or bright sunlight.",
        ),
        QAItem(
            question="Why can historic objects need careful repairs?",
            answer="Historic objects carry memories from the past, so people should inspect them gently and preserve useful old materials while making them safe.",
        ),
        QAItem(
            question="How does friendship help with problem solving?",
            answer="Friends can share observations, listen to different ideas, divide the work, and encourage one another when the first plan fails.",
        ),
        QAItem(
            question="What should a crew do when a plan does not work?",
            answer="The crew should stay calm, describe what happened, look for new clues, and try a safer plan together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
    lines.extend(["", "== story qa =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== world qa =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id} ({entity.kind}/{entity.type}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  truth={world.facts['truth']}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams(
        place="cove",
        shutter="blue",
        captain="Luna",
        friend="Niko",
        helper="parrot",
        problem="storm_rope",
        route="clue_first",
        seed=101,
    ),
    StoryParams(
        place="harbor",
        shutter="red",
        captain="Luna",
        friend="Suri",
        helper="dolphin",
        problem="bell_silent",
        route="friend_first",
        seed=202,
    ),
    StoryParams(
        place="island",
        shutter="gold",
        captain="Luna",
        friend="Beau",
        helper="turtle",
        problem="chest_key",
        route="question_first",
        seed=303,
    ),
]


def verify_generated_stories() -> int:
    for params in CURATED:
        sample = generate(params)
        if not sample.story.strip():
            print("VERIFY FAILED: generated story was empty.")
            return 1
        if "historic" not in sample.story.lower():
            print("VERIFY FAILED: story omitted the historic shutter.")
            return 1
        if len(sample.story_qa) < 4 or len(sample.world_qa) < 3:
            print("VERIFY FAILED: incomplete question sets.")
            return 1
    print("OK: generated stories passed prose and QA checks.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify() or verify_generated_stories())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:\n")
        for place, shutter in combos:
            print(f"  {place:8} {shutter}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
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
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
        return

    for index, sample in enumerate(samples):
        header = (
            "### curated story"
            if args.all
            else f"### variant {index + 1}" if len(samples) > 1 else ""
        )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
