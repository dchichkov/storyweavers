#!/usr/bin/env python3
"""
A small mystery storyworld about a hidden mechanism, loyal friends, and the
caution that a strange clue should be tested before it is trusted.
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Item
    friend: Item
    keeper: Item
    mechanism: Item
    place: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    friend_name: str
    keeper_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Luna", "Mara", "Nico", "Tess", "Owen", "Pia", "Juno", "Cal"]
FRIENDS = ["Finn", "Mina", "Theo", "Rae", "Sol", "Bea", "Kit", "Noor"]
KEEPERS = ["Mrs. Vale", "Uncle Ivo", "Aunt Sela", "Mr. Moss", "Grandma June"]
PLACES = [
    "the old clock house",
    "the foggy ferry shed",
    "the hilltop museum",
    "the moonlit greenhouse",
    "the locked library porch",
]


ASP_RULES = r"""
#show clues/1.
#show cautious/1.
#show trusted/1.
#show solved/1.

clues(H) :- finds_mechanism(H).
cautious(H) :- checks_clue(H), warns_friend(H).
trusted(H) :- stands_by_friend(H).
solved(H) :- checks_clue(H), finds_mechanism(H), stands_by_friend(H).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("finds_mechanism", "hero"),
            asp.fact("checks_clue", "hero"),
            asp.fact("warns_friend", "hero"),
            asp.fact("stands_by_friend", "hero"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program(
            "#show clues/1.\n"
            "#show cautious/1.\n"
            "#show trusted/1.\n"
            "#show solved/1."
        )
    )
    actual = {
        (symbol.name, tuple(
            arg.number if arg.type == arg.type.Number
            else arg.string if arg.type == arg.type.String
            else arg.name
            for arg in symbol.arguments
        ))
        for symbol in model
    }
    expected = {
        ("clues", ("hero",)),
        ("cautious", ("hero",)),
        ("trusted", ("hero",)),
        ("solved", ("hero",)),
    }
    if actual == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mystery storyworld about a hidden mechanism and friendship."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend-name", choices=FRIENDS)
    parser.add_argument("--keeper-name", choices=KEEPERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        friend_name=args.friend_name or rng.choice(FRIENDS),
        keeper_name=args.keeper_name or rng.choice(KEEPERS),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    if params.name == params.friend_name:
        raise StoryError("The hero and friend must have different names.")
    hero = Item(
        id="hero",
        label=params.name,
        phrase=f"young {params.name}",
        kind="character",
        meters={"attention": 0.8, "distance": 0.0},
        memes={"curiosity": 0.9, "trust": 0.7},
    )
    friend = Item(
        id="friend",
        label=params.friend_name,
        phrase=params.friend_name,
        kind="character",
        meters={"attention": 0.7, "distance": 0.0},
        memes={"courage": 0.8, "trust": 0.9},
    )
    keeper = Item(
        id="keeper",
        label=params.keeper_name,
        phrase=params.keeper_name,
        kind="character",
        meters={"attention": 0.5},
        memes={"care": 0.9},
    )
    mechanism = Item(
        id="mechanism",
        label="brass mechanism",
        phrase="a little brass mechanism with three teeth and a blue glass eye",
        kind="device",
        meters={"spring_tension": 0.0, "danger": 0.0, "distance": 1.0},
        memes={"mystery": 1.0, "trust": 0.0},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.friend_name}|{params.place}")
    return World(
        hero=hero,
        friend=friend,
        keeper=keeper,
        mechanism=mechanism,
        place=params.place,
        seed=seed,
    )


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record(
    world: World,
    *,
    clue: str,
    danger: str,
    cause: str,
    twist: str,
    resolution: str,
    ending: str,
    lesson: str,
    lines: list[str],
) -> str:
    world.facts.update(
        clue=clue,
        danger=danger,
        cause=cause,
        twist=twist,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        friendship=True,
        cautious=True,
        solved=True,
    )
    return " ".join(lines)


def _clock_arc(world: World, rng: random.Random) -> str:
    h, f, k, p = (
        world.hero.label,
        world.friend.label,
        world.keeper.label,
        world.place,
    )
    hour = _choice(rng, ["midnight", "one o'clock", "the first bell", "moonrise"])
    clue = "a brass mechanism hidden behind the clock face, turning whenever someone whispered"
    danger = "the tower clock began pulling its heavy bell rope toward the open stair"
    cause = "a loose spring had been wound too tightly by the last person who tested the device"
    twist = "the frightening footsteps were not a stranger at all, but the mechanism dragging a little brass shoe around its track"
    resolution = f"{h} stopped touching the spring, while {f} held the lantern and {k} safely released the bell rope"
    ending = "the clock gave one gentle chime, and the blue eye of the mechanism rested darkly in its velvet slot"
    lesson = "a mysterious device deserves careful testing, not a brave shove"
    lines = [
        f"At {p}, {h} and {f} found a cold draft behind the old clock face.",
        f"Inside the wall sat {world.mechanism.phrase}. When {h} whispered, its three teeth clicked and the clock began counting toward {hour}.",
        f'"We found the secret," said {h}. "Then let us not poke it," said {f}.',
        f"Before they could study the next tooth, a heavy step sounded above them. Then another. The bell rope jerked toward the open stair.",
        f"{h} reached for the shining spring, but {f} caught the child's sleeve. \"Mysteries can wait one breath,\" {f} said. \"First, let us see what is moving.\"",
        f"Together they watched from the doorway. A tiny brass shoe circled the mechanism and tugged the rope each time the spring snapped.",
        f'The footsteps were not a prowler. They were the mechanism\'s shoe tapping around its track. "{twist.capitalize()}!" whispered {h}.',
        f"{h} stopped touching the spring, {f} held the lantern, and {k} safely released the rope. The dangerous pull faded.",
        f"By morning, {ending}. {h} learned that {lesson}, and {f} felt glad that friendship had slowed the story down.",
    ]
    return _record(
        world,
        clue=clue,
        danger=danger,
        cause=cause,
        twist=twist,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        lines=lines,
    )


def _ferry_arc(world: World, rng: random.Random) -> str:
    h, f, k, p = (
        world.hero.label,
        world.friend.label,
        world.keeper.label,
        world.place,
    )
    object_name = _choice(rng, ["a silver key", "a red button", "a folded ticket", "a tiny bell"])
    clue = f"a brass mechanism beneath the ferry desk that clicked whenever {object_name} moved"
    danger = "the empty ferry began gliding from the dock into the fog"
    cause = "the mechanism was an old automatic release, and the object had slipped into its trigger slot"
    twist = f"the supposed ghostly signal was only {object_name} bouncing inside the release mechanism"
    resolution = f"{h} kept everyone on the dock while {f} fetched {k}, and they used a pole to guide the ferry back before touching the trigger"
    ending = "the ferry rope was tied twice, while the mechanism rested in a labeled tin instead of a pocket"
    lesson = "a clue can explain a danger without making the danger harmless"
    lines = [
        f"One misty evening at {p}, {h} noticed three clicks beneath the ferry desk.",
        f"{f} lifted a loose board and found {world.mechanism.phrase}. A blue glass eye blinked whenever {object_name} rolled nearby.",
        f'"It is calling a ghost boat!" said {h}. "Or it is calling someone to check it," said {f}.',
        f"Then the empty ferry slipped free and began gliding into the fog. Its lantern made a pale circle on the black water.",
        f"{h} took one step toward the edge, but {f} held the child's hand. \"We can be brave without being foolish,\" said {f}.",
        f"They called for {k}, kept their feet on the dock, and watched the clicks repeat. Each click came when {object_name} bounced into a narrow brass slot.",
        f"The ghostly signal was not a ghost. It was {twist}.",
        f"With a long pole, {k} guided the ferry back. Only after the rope was secure did the friends lift the object free.",
        f"At dawn, {ending}. The mystery had ended, but {h} remembered that {lesson}.",
    ]
    return _record(
        world,
        clue=clue,
        danger=danger,
        cause=cause,
        twist=twist,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        lines=lines,
    )


def _greenhouse_arc(world: World, rng: random.Random) -> str:
    h, f, k, p = (
        world.hero.label,
        world.friend.label,
        world.keeper.label,
        world.place,
    )
    plant = _choice(rng, ["the night-blooming vine", "the tallest fern", "the lemon tree", "the sleepy orchid"])
    clue = f"a hidden mechanism that opened vents above {plant} whenever the moon rose"
    danger = "the glass roof began sliding open during a hard, cold wind"
    cause = "a damp leaf had wedged the mechanism's sensor, making it mistake the wind for warm moonlight"
    twist = "the moving shadow at the roof was a dangling plant label, not a person climbing outside"
    resolution = f"{h} and {f} first shut the inner door, then asked {k} to disconnect the mechanism while they brushed away the leaf"
    ending = "the roof settled above the plants, and the brass teeth turned only when the morning air was truly warm"
    lesson = "a quiet observation can be safer than a quick answer"
    lines = [
        f"At {p}, {h} and {f} followed a trail of wet footprints between the pots.",
        f"The trail ended beside {world.mechanism.phrase}, tucked under {plant}. Its tiny teeth clicked, and a roof panel slid open.",
        f'"Someone is up there," said {h}. "Or something is pulling the roof," said {f}.',
        f"A cold gust rushed through the glasshouse. The panel opened wider, and a dark shape swung across the moon.",
        f"{h} wanted to climb the ladder, but {f} shook their head. \"Mysteries do not become safer when we chase them upward.\"",
        f"They watched from the floor. The dark shape swung whenever the wind moved a dangling plant label. Below it, a wet leaf trembled inside the sensor.",
        f"The climber was not a person. The shadow was only the plant label, and the mechanism was reacting to the leaf.",
        f"Together they shut the inner door. {k} disconnected the device, and the friends brushed the leaf away before testing it with warm air.",
        f"By sunrise, {ending}. {h} decided that {lesson}, especially when a friend was close enough to say, \"Wait.\"",
    ]
    return _record(
        world,
        clue=clue,
        danger=danger,
        cause=cause,
        twist=twist,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        lines=lines,
    )


def _library_arc(world: World, rng: random.Random) -> str:
    h, f, k, p = (
        world.hero.label,
        world.friend.label,
        world.keeper.label,
        world.place,
    )
    book = _choice(rng, ["a blue atlas", "a red notebook", "a book of sea maps", "a book of riddles"])
    clue = f"a hidden brass mechanism that opened a secret shelf whenever {book} was placed on a certain tile"
    danger = "the shelf swung open toward the narrow porch and nearly pulled a stack of books down"
    cause = "the tile was loose, so the book's weight pressed the mechanism twice instead of once"
    twist = "the mysterious tapping behind the wall was a book's metal clasp striking the shelf as it moved"
    resolution = f"{h} and {f} cleared the porch, marked the loose tile, and asked {k} to lock the mechanism before opening the shelf again"
    ending = "the secret shelf held old friendship letters, and the mechanism wore a small warning ribbon"
    lesson = "finding a secret is only the beginning; caring for what it can affect matters too"
    lines = [
        f"At {p}, {h} found a line of dusty footprints ending at {book}.",
        f"When {h} placed the book on a loose tile, {world.mechanism.phrase} clicked inside the wall.",
        f'"A hidden door!" cried {h}. "A hidden door with a very narrow porch," warned {f}.',
        f"The shelf swung outward. Books slid, the porch boards groaned, and a tapping began behind the wall.",
        f"{h} reached for the shelf handle, but {f} pulled the child back. \"Let us move the books first,\" said {f}.",
        f"They cleared the porch and watched the mechanism through the gap. The tapping happened whenever the book's metal clasp struck the moving shelf.",
        f"The sound was not a secret visitor. The mysterious tapping was {twist}.",
        f"After {k} locked the mechanism, the friends tested the tile with a wooden block. The shelf opened slowly and revealed letters written by old friends.",
        f"That evening, {ending}. The best clue was not the hidden door but the reminder that {lesson}.",
    ]
    return _record(
        world,
        clue=clue,
        danger=danger,
        cause=cause,
        twist=twist,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        lines=lines,
    )


def _museum_arc(world: World, rng: random.Random) -> str:
    h, f, k, p = (
        world.hero.label,
        world.friend.label,
        world.keeper.label,
        world.place,
    )
    statue = _choice(rng, ["a wooden fox", "a stone sailor", "a paper dragon", "a bronze bird"])
    clue = f"a brass mechanism hidden inside {statue}, whose blue eye shone whenever someone told the truth"
    danger = "the display case began lowering its glass lid while the friends stood inside the marked circle"
    cause = "a pressure plate had been placed under the wrong exhibit label during a rearrangement"
    twist = "the shining eye did not detect lies; it reflected the museum lamp through a turning gear"
    resolution = f"{h} warned {f} to step back, and {k} switched off the display before moving the pressure plate"
    ending = "the exhibit reopened with a clear sign, and the little mechanism turned harmlessly behind its glass"
    lesson = "a strange sign can invite questions, but evidence must answer them"
    lines = [
        f"At {p}, {h} and {f} found a blue flash inside {statue}.",
        f"Behind its panel sat {world.mechanism.phrase}. The eye shone whenever anyone spoke near the display.",
        f'"It knows who is telling the truth," said {h}. "Then we should not let it decide for us," said {f}.',
        f"The floor clicked. A glass lid began lowering over the marked circle where the friends stood.",
        f"{h} wanted to grab the glowing eye, but {f} pointed to the warning line. \"Back first. Questions second.\"",
        f"They stepped away and called {k}. The keeper switched off the display and examined the gears.",
        f"The eye did not detect lies. It only reflected the museum lamp through a turning gear, while a misplaced label covered the pressure plate.",
        f"Once the plate was moved, the friends tested the mechanism with a wooden ruler and watched it safely open and close.",
        f"By closing time, {ending}. {h} and {f} left together, proud that their friendship had outlasted the trick.",
    ]
    return _record(
        world,
        clue=clue,
        danger=danger,
        cause=cause,
        twist=twist,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        lines=lines,
    )


ARC_BUILDERS = [_clock_arc, _ferry_arc, _greenhouse_arc, _library_arc, _museum_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x4D454348)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    f = world.friend.label
    facts = world.facts
    return [
        QAItem(
            question=f"What clue did {h} and {f} discover?",
            answer=f"They discovered {facts['clue']}.",
        ),
        QAItem(
            question="What made the mystery dangerous?",
            answer=f"The danger came from {facts['danger']} because {facts['cause']}.",
        ),
        QAItem(
            question="What was the surprising twist?",
            answer=f"The twist was that {facts['twist']}.",
        ),
        QAItem(
            question=f"How did {h} and {f} solve the problem?",
            answer=f"They solved it when {facts['resolution']}.",
        ),
        QAItem(
            question="How did friendship help?",
            answer=f"The friends listened to each other and acted together instead of rushing into danger.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a group of parts that move together to perform a task, such as opening, locking, ringing, or lifting something.",
        ),
        QAItem(
            question="Why is caution useful during a mystery?",
            answer="Caution gives people time to observe evidence and avoid making a dangerous situation worse.",
        ),
        QAItem(
            question="What makes a friendship strong?",
            answer="A strong friendship includes listening, honesty, care, and helping one another make safe choices.",
        ),
        QAItem(
            question="What is a twist in a mystery story?",
            answer="A twist is a surprising change in understanding that reveals the clue or danger was not what it first seemed.",
        ),
        QAItem(
            question="Why should a moving machine be tested carefully?",
            answer="A moving machine can pinch, pull, or drop things, so people should keep a safe distance and ask a knowledgeable helper to inspect it.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly mystery about a hidden mechanism and two loyal friends.",
        f"Tell a cautionary mystery set at {world.place}, where careful observation reveals a surprising twist.",
        "Create a friendship story in which a strange device seems frightening but its real purpose is discovered safely.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.hero, world.friend, world.keeper, world.mechanism]:
        lines.append(
            f"  {entity.id:10} {entity.kind:10} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  place={world.place!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        out.append(f"{index}. {prompt}")
    out.extend(["", "== Story QA =="])
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.extend(["", "== World QA =="])
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    world.facts["story"] = story
    return StorySample(
        params=params,
        story=story,
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
        print()
        print(format_qa(sample))


def asp_facts_text() -> str:
    return asp_facts()


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                "#show clues/1.\n"
                "#show cautious/1.\n"
                "#show trusted/1.\n"
                "#show solved/1."
            )
        )
        return

    if args.verify:
        status = asp_verify()
        if status == 0:
            try:
                verify_params = StoryParams(
                    name="Luna",
                    friend_name="Finn",
                    keeper_name="Mrs. Vale",
                    place="the old clock house",
                    seed=7,
                )
                sample = generate(verify_params)
                required = ["mechanism", "friend", "safe", "friendship"]
                text = sample.story.lower()
                if not all(word in text for word in required):
                    print("MISMATCH: generated story failed story-quality checks.")
                    return_code = 1
                elif not sample.story_qa or not sample.world_qa:
                    print("MISMATCH: generated story lacks QA.")
                    return_code = 1
                else:
                    print("OK: generated story exercised.")
                    return_code = 0
            except Exception as exc:
                print(f"MISMATCH: generated story failed: {exc}")
                return_code = 1
            sys.exit(return_code)
        sys.exit(status)

    if args.asp:
        print(
            "4 compatible logical atoms: "
            "clues(hero), cautious(hero), trusted(hero), solved(hero)"
        )
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                name="Luna",
                friend_name="Finn",
                keeper_name="Mrs. Vale",
                place="the old clock house",
                seed=base_seed,
            ),
            StoryParams(
                name="Mara",
                friend_name="Mina",
                keeper_name="Uncle Ivo",
                place="the foggy ferry shed",
                seed=base_seed + 1,
            ),
            StoryParams(
                name="Nico",
                friend_name="Theo",
                keeper_name="Aunt Sela",
                place="the moonlit greenhouse",
                seed=base_seed + 2,
            ),
            StoryParams(
                name="Tess",
                friend_name="Rae",
                keeper_name="Mr. Moss",
                place="the locked library porch",
                seed=base_seed + 3,
            ),
            StoryParams(
                name="Owen",
                friend_name="Pia",
                keeper_name="Grandma June",
                place="the hilltop museum",
                seed=base_seed + 4,
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if len(samples) < args.n and not args.all:
        raise StoryError("Could not create the requested number of distinct stories.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps(
                [sample.to_dict() for sample in samples],
                indent=2,
                ensure_ascii=False,
            ))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.name} at {params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
