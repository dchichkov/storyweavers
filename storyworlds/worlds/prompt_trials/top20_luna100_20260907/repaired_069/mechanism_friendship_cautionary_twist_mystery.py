#!/usr/bin/env python3
"""Child-friendly mystery stories about a hidden mechanism, friendship, and caution."""

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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child: str = "Luna"
    friend: str = "Milo"
    keeper: str = "Nora"
    place: str = "the old clock tower"
    mystery: int = 0
    opening: int = 0
    warning: int = 0
    exchange: int = 0
    twist: int = 0
    ending: int = 0


NAMES = ["Luna", "Iris", "Pip", "Tessa", "Mina", "Jun"]
FRIENDS = ["Milo", "Bea", "Ollie", "Ravi", "Nell"]
KEEPERS = ["Nora", "Aunt Ada", "Mr. Finch", "Sage"]
PLACES = [
    "the old clock tower",
    "the moonlit museum",
    "the harbor warehouse",
    "the village greenhouse",
    "the library attic",
]

MYSTERIES = [
    {
        "title": "the bell that rang by itself",
        "object": "brass bell",
        "premise": "Every midnight, a brass bell rang three times even though the tower keeper had locked its rope away.",
        "clue": "A thin line of flour led from the bell to a loose floorboard.",
        "mechanism": "A hidden wooden lever under the floorboard tipped a marble into a tin cup; the cup pulled a cord to the bell.",
        "danger": "The lever was balanced over a cracked stair, so one careless step could send someone tumbling.",
        "action": "They wedged the lever safely, lifted the floorboard with a ruler, and traced the cord before touching anything else.",
        "twist": "The ringing was not a ghostly warning. The keeper had built the mechanism years ago to remind himself to check the tower's storm shutters.",
        "result": "The bell stopped ringing, and the storm shutters were secured before the night wind arrived.",
        "lesson": "A mystery is safer when friends pause to understand its mechanism instead of rushing toward a frightening guess.",
        "ending": "At dawn, the quiet bell held one silver drop of rain.",
    },
    {
        "title": "the vanishing map",
        "object": "blue map",
        "premise": "A blue map disappeared from a locked display each afternoon and returned before sunset.",
        "clue": "A thread from the map's corner was caught in a brass vent.",
        "mechanism": "Warm air from the bakery below lifted a hidden flap, which drew the map through the vent and dropped it into a laundry basket.",
        "danger": "The vent cover was loose above a hot oven, so reaching inside could burn a hand.",
        "action": "They asked the baker to cool the oven, tied a ribbon to the flap, and watched the safe route from the floor.",
        "twist": "The map was not being stolen. A former cartographer had designed the mechanism to protect it from afternoon sunlight.",
        "result": "The map stayed in a shaded frame, and the baker found a lost recipe beneath it.",
        "lesson": "A careful question can reveal a kind reason behind a suspicious-looking trick.",
        "ending": "The blue map rested under glass while a ribbon marked its hidden path.",
    },
    {
        "title": "the whispering cabinet",
        "object": "oak cabinet",
        "premise": "The locked oak cabinet whispered a name whenever someone passed its keyhole.",
        "clue": "Dust trembled beside a narrow pipe leading to the garden wall.",
        "mechanism": "A wind vane outside turned a tiny wheel, which puffed air through the pipe and made a reed vibrate.",
        "danger": "The cabinet's back panel was held by a spring that could snap shut on curious fingers.",
        "action": "They used a spoon handle to hold the spring open and placed a leaf beside the pipe to test each puff.",
        "twist": "The cabinet was not speaking. It was announcing the gardener's name because the reed had been carved from an old flute.",
        "result": "They repaired the reed, and the cabinet became a gentle weather signal.",
        "lesson": "When a sound seems mysterious, find what moves the air before inventing a scary story.",
        "ending": "The cabinet gave one soft note as leaves turned in the evening breeze.",
    },
    {
        "title": "the moving chess piece",
        "object": "ivory knight",
        "premise": "An ivory knight moved across the reading room chessboard whenever the lights flickered.",
        "clue": "A copper wire ran beneath the board toward the fireplace.",
        "mechanism": "Heat from the fireplace bent a metal strip, which pulled a magnet under the board and slid the knight.",
        "danger": "The wire crossed a damp rug, where a hurried tug could make someone slip.",
        "action": "They dried the rug, marked the wire's path, and cooled the fireplace before lifting one board square.",
        "twist": "The knight's movement was a safety signal designed to show that the room was too warm for the old books.",
        "result": "The books were moved to a cooler shelf, and the knight stayed beside the chess king.",
        "lesson": "A strange movement may be a warning worth understanding, not a challenge to chase.",
        "ending": "The ivory knight watched over the books in a room kept cool and bright.",
    },
    {
        "title": "the locked garden gate",
        "object": "iron gate",
        "premise": "The garden gate clicked open at noon even when its key was hanging inside the shed.",
        "clue": "A row of sunflowers leaned toward a small mirror tied to the fence.",
        "mechanism": "Sunlight bounced from the mirror onto a dark metal plate, warming a wax cord until it released the latch.",
        "danger": "The mirror's sharp corner faced the path, and a sudden tug could cut someone.",
        "action": "They covered the corner, stood behind the fence, and watched the reflected sunlight move across the plate.",
        "twist": "The gate had been built to open for bees and gardeners when the sun reached the flower beds.",
        "result": "They replaced the mirror with a safe round reflector and kept the gate from opening into the road.",
        "lesson": "Safety comes before solving a puzzle, especially when a clever mechanism can surprise people.",
        "ending": "Bees hummed through the safe open gate while the round reflector shone softly.",
    },
]

OPENINGS = [
    "{child} loved small mysteries, but {friend} was the friend who always remembered to look underfoot.",
    "Rain tapped {place} while {child} and {friend} searched for a sensible explanation.",
    "{child} and {friend} had promised to solve one mystery without touching anything dangerous.",
    "At {place}, a strange sound made everyone whisper, but {child} and {friend} stayed together.",
    "The mystery began with one impossible movement and two friends who trusted caution.",
]

WARNINGS = [
    "The keeper raised a hand. 'Stop there. A hidden mechanism can move even when it looks still.'",
    "{friend} said, 'We can be brave without being careless. First we make the place safe.'",
    "They drew a chalk line around the danger. No one crossed it until they knew what could spring, roll, or fall.",
    "{child} remembered the rule: observe, ask, and only then test.",
]

EXCHANGES = [
    ("'Do you think it is a ghost?' asked {child}.", "'I think it is a clue,' said {friend}. 'Let us follow the evidence, not the fear.'"),
    ("'{friend}, should we pull this?' asked {child}.", "'Not yet,' said {friend}. 'We do not know what it connects to.'"),
    ("'The sound changed when the wind blew,' said {child}.", "'Then the wind may be part of the mechanism,' replied {friend}."),
    ("'I want to solve it first,' whispered {child}.", "'We will solve it together and come home with all our fingers,' said {friend}."),
]

TWIST_LINES = [
    "The truth made the mystery smaller and the old machine more interesting.",
    "Their frightening guess folded into a useful explanation.",
    "The secret was not a villain at all, but a forgotten purpose.",
    "The final clue changed what both friends thought they knew.",
]

ENDINGS = [
    "The two friends wrote the mechanism in their notebook, along with a bold warning: never test a machine alone.",
    "They left a bright safety card beside the device so the next curious visitor would know where to stand.",
    "Before they went home, they thanked the keeper and promised that friendship would never mean daring each other into danger.",
    "The mystery became a story they could tell because they had solved it carefully, not because they had taken a foolish risk.",
]


ASP_RULES = r"""
#show cautious/2.
#show friendship/2.
#show mechanism/1.

cautious(A, M) :- observes(A), danger(M).
friendship(A, B) :- trusts(A, B), helps(A, B).
mechanism(M) :- hidden(M), moves(M).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("observes", "child"),
            asp.fact("danger", "hidden_machine"),
            asp.fact("trusts", "child", "friend"),
            asp.fact("helps", "child", "friend"),
            asp.fact("hidden", "clock_mechanism"),
            asp.fact("moves", "clock_mechanism"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery stories about a mechanism, friendship, and caution.")
    ap.add_argument("--child", choices=NAMES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--keeper", choices=KEEPERS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", type=int, choices=range(len(MYSTERIES)))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        child=args.child or rng.choice(NAMES),
        friend=args.friend or rng.choice(FRIENDS),
        keeper=args.keeper or rng.choice(KEEPERS),
        place=args.place or rng.choice(PLACES),
        mystery=args.mystery if args.mystery is not None else rng.randrange(len(MYSTERIES)),
        opening=rng.randrange(len(OPENINGS)),
        warning=rng.randrange(len(WARNINGS)),
        exchange=rng.randrange(len(EXCHANGES)),
        twist=rng.randrange(len(TWIST_LINES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.child == params.friend:
        raise StoryError("The child and friend must have different names.")
    if not params.place:
        raise StoryError("A mystery needs a named place.")

    mystery = MYSTERIES[params.mystery % len(MYSTERIES)]
    world = World()

    child = world.add(Entity(params.child, "child", params.child))
    friend = world.add(Entity(params.friend, "friend", params.friend))
    keeper = world.add(Entity(params.keeper, "keeper", params.keeper))
    device = world.add(Entity("device", "mechanism", mystery["object"], owner=params.keeper))

    child.meters.update(curiosity=1.0, safety=0.0)
    friend.meters.update(observation=1.0, safety=1.0)
    child.memes["trust"] = 1.0
    friend.memes["trust"] = 1.0
    device.meters["hidden_parts"] = 1.0
    device.memes["purpose_unknown"] = 1.0

    values = {
        "child": child.id,
        "friend": friend.id,
        "keeper": keeper.id,
        "place": params.place,
    }

    def fmt(text: str) -> str:
        return text.format(**values)

    world.say(fmt(OPENINGS[params.opening % len(OPENINGS)]))
    world.say(f"At {params.place}, {mystery['premise']}")
    world.say(fmt(EXCHANGES[params.exchange % len(EXCHANGES)][0]))
    world.say(fmt(EXCHANGES[params.exchange % len(EXCHANGES)][1]))
    world.say(f"They found the first clue: {mystery['clue']}")
    world.say(mystery["danger"])
    world.say(fmt(WARNINGS[params.warning % len(WARNINGS)]))
    world.say(f"{child.id} and {friend.id} worked side by side. {mystery['action']}")
    child.meters["safety"] = 1.0
    friend.meters["safety"] = 1.0
    world.say(f"Then the hidden mechanism became clear: {mystery['mechanism']}")
    world.say(f"{mystery['twist']} {TWIST_LINES[params.twist % len(TWIST_LINES)]}")
    device.memes["purpose_unknown"] = 0.0
    device.memes["understood"] = 1.0
    world.say(mystery["result"])
    world.say(f"'{mystery['lesson']}' said {friend.id}, and {child.id} nodded.")
    world.say(mystery["ending"])
    world.say(ENDINGS[params.ending % len(ENDINGS)])

    world.facts.update(
        child=child,
        friend=friend,
        keeper=keeper,
        device=device,
        mystery=mystery,
        place=params.place,
        mechanism=mystery["mechanism"],
        friendship=True,
        cautious=True,
        twist=mystery["twist"],
        solved=True,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery = f["mystery"]
    child = f["child"].id
    friend = f["friend"].id
    return [
        f"Write a child-friendly mystery about {child} and {friend} discovering the mechanism behind {mystery['title']}.",
        f"Tell a cautionary friendship story where two friends inspect {mystery['object']} without touching a dangerous hidden part.",
        f"Write a mystery with a surprising twist: the strange mechanism has a helpful purpose, and the friends solve it safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery = f["mystery"]
    child = f["child"].id
    friend = f["friend"].id
    return [
        QAItem(
            question=f"What mystery did {child} and {friend} investigate?",
            answer=f"They investigated {mystery['title']}: {mystery['premise']}",
        ),
        QAItem(
            question="What clue helped the friends?",
            answer=mystery["clue"],
        ),
        QAItem(
            question="What was the hidden mechanism?",
            answer=mystery["mechanism"],
        ),
        QAItem(
            question="Why did the friends act cautiously?",
            answer=f"They acted cautiously because {mystery['danger']} They wanted to understand the machine without getting hurt.",
        ),
        QAItem(
            question="What was the twist?",
            answer=mystery["twist"],
        ),
        QAItem(
            question="What lesson did the friends learn?",
            answer=mystery["lesson"],
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of moving parts that work together to make something happen.",
        ),
        QAItem(
            question="Why is caution important around an unknown machine?",
            answer="Caution is important because hidden springs, sharp edges, heat, or moving parts can cause harm before we understand how the machine works.",
        ),
        QAItem(
            question="How can friendship help during a mystery?",
            answer="Good friends can share clues, ask careful questions, and stop one another from taking unsafe risks.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label}: type={entity.type}, "
            f"meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_valid() -> dict[str, set[tuple]]:
    import asp
    model = asp.one_model(
        asp_program("#show cautious/2.\n#show friendship/2.\n#show mechanism/1.")
    )
    return {
        "cautious": set(asp.atoms(model, "cautious")),
        "friendship": set(asp.atoms(model, "friendship")),
        "mechanism": set(asp.atoms(model, "mechanism")),
    }


def asp_verify() -> int:
    expected = {
        "cautious": {("child", "hidden_machine")},
        "friendship": {("child", "friend")},
        "mechanism": {("clock_mechanism",)},
    }
    actual = asp_valid()
    if actual == expected:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("  clingo:", actual)
    print("  python:", expected)
    return 1


def verify_stories() -> int:
    for params in CURATED:
        sample = generate(params)
        if not sample.story.strip():
            print("Generated an empty story.")
            return 1
        if params.child not in sample.story or params.friend not in sample.story:
            print("Generated story omitted a main character.")
            return 1
        if "mechanism" not in sample.story:
            print("Generated story omitted the mechanism.")
            return 1
        if len(sample.story_qa) < 4:
            print("Generated story omitted grounded questions.")
            return 1
    return 0


CURATED = [
    StoryParams(
        seed=1,
        child="Luna",
        friend="Milo",
        keeper="Nora",
        place="the old clock tower",
        mystery=0,
        opening=0,
        warning=1,
        exchange=0,
        twist=2,
        ending=0,
    ),
    StoryParams(
        seed=2,
        child="Iris",
        friend="Bea",
        keeper="Aunt Ada",
        place="the moonlit museum",
        mystery=1,
        opening=2,
        warning=0,
        exchange=1,
        twist=0,
        ending=1,
    ),
    StoryParams(
        seed=3,
        child="Pip",
        friend="Ravi",
        keeper="Mr. Finch",
        place="the library attic",
        mystery=3,
        opening=4,
        warning=2,
        exchange=3,
        twist=3,
        ending=2,
    ),
]


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show cautious/2.\n#show friendship/2.\n#show mechanism/1."))
        return

    if args.verify:
        code = asp_verify()
        if code == 0:
            code = verify_stories()
            if code == 0:
                print("OK: generated stories pass the world gate.")
        sys.exit(code)

    if args.asp:
        results = asp_valid()
        for name in ("cautious", "friendship", "mechanism"):
            print(f"{name}: {sorted(results[name])}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n:
            if attempt > max(100, args.n * 50):
                raise StoryError("Could not produce enough distinct story variants.")
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.all:
            header = f"### {sample.params.child}: {sample.world.facts['mystery']['title']}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
