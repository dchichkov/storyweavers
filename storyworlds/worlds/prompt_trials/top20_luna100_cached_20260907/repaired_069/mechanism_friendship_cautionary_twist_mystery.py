#!/usr/bin/env python3
"""Child-friendly mystery stories about a hidden mechanism, friendship, and a cautionary twist."""

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
    place: str = "clocktower"
    mystery: int = 0
    opening: int = 0
    clue: int = 0
    twist: int = 0
    ending: int = 0


NAMES = ["Luna", "Nia", "Pip", "Ravi", "Tess", "Uma"]
FRIENDS = ["Milo", "Bea", "Finn", "Zuri", "Ollie"]
PLACES = ["clocktower", "old greenhouse", "harbor shed", "museum attic", "railway hut"]

MYSTERIES = [
    {
        "title": "the midnight bell",
        "object": "brass bell",
        "premise": "Every night, the brass bell rang once even though nobody pulled its rope.",
        "clue": "Luna noticed a thin thread running from the bell toward a dusty gear box.",
        "mechanism": "Inside the box, a bent spring pressed a wheel whenever the tower cooled.",
        "danger": "If they forced the wheel, the bell could drop from its cracked wooden bracket.",
        "result": "They loosened the spring, braced the bracket, and stopped the lonely ringing.",
        "lesson": "A strange noise deserves careful checking before anyone blames a friend.",
        "image": "The bell rested quietly above two fresh support beams.",
    },
    {
        "title": "the vanishing lantern",
        "object": "blue lantern",
        "premise": "A blue lantern disappeared from the dock each evening and returned before sunrise.",
        "clue": "Milo found wet marks that ended beside a loose plank, not beside the locked door.",
        "mechanism": "A hidden pulley under the plank lowered the lantern into a storage hollow below.",
        "danger": "A hard tug could snap the pulley and drop the lantern into the tide channel.",
        "result": "They secured the pulley and lifted the lantern gently back to its hook.",
        "lesson": "A hidden mechanism can make an honest mystery look like mischief.",
        "image": "The blue lantern shone safely above the dry dock.",
    },
    {
        "title": "the whispering cabinet",
        "object": "wooden cabinet",
        "premise": "A cabinet in the museum whispered whenever someone opened the front door.",
        "clue": "Luna saw dust jump from a pinhole near the cabinet's bottom hinge.",
        "mechanism": "A narrow tube carried the door's movement to a reed hidden inside the cabinet.",
        "danger": "Prying the cabinet apart could ruin the old exhibit and release sharp splinters.",
        "result": "They repaired the tube and placed a soft guard around the reed.",
        "lesson": "Understanding how a thing works is kinder than smashing what seems strange.",
        "image": "The cabinet stood silent while its little reed made music on purpose.",
    },
    {
        "title": "the moving garden gate",
        "object": "iron gate",
        "premise": "The greenhouse gate opened by itself whenever clouds covered the sun.",
        "clue": "Bea spotted a silver strip stretching from the gate to a warm glass roof.",
        "mechanism": "Heat had tightened the strip, and cooling made it shrink and pull a latch.",
        "danger": "The gate might swing into the flower cart if they blocked it too quickly.",
        "result": "They adjusted the latch and placed a soft stopper beneath the hinges.",
        "lesson": "A patient test can reveal a cause that a quick guess would miss.",
        "image": "The iron gate now opened only for gardeners carrying flowers.",
    },
]

OPENINGS = [
    "At dawn, {child} and {friend} met beside the {place}, where a puzzling sound had woken the neighborhood.",
    "The mystery began when {child} found {friend} staring at the {place} with a worried face.",
    "Rain tapped the roofs as {child} and {friend} arrived at the {place} to investigate a secret.",
    "Everyone had a guess about the {place}, but {child} and {friend} decided to look for evidence.",
    "By the time the sun rose, {child} and {friend} were already following a trail toward the {place}.",
]

CLUE_LINES = [
    "They did not touch the machine at first. They watched, listened, and drew its parts in the dust.",
    "The friends compared the marks twice because one clue can point in two directions.",
    "Luna held the lamp while Milo checked each hinge, pin, and wheel without forcing anything.",
    "Their friendship helped them disagree safely: one suggested a guess, and the other asked for a test.",
    "A small click answered their question, but they waited before celebrating.",
]

TWISTS = [
    "Then came the twist: the owner had not hidden the object at all. The mechanism had been designed years earlier to protect it from storms.",
    "The final surprise was that the frightening sound was a safety warning, not a secret message from a thief.",
    "At last they learned that the missing object had been moving to its safe place by itself.",
    "The mystery had one more turn: the loose part was not broken until someone had tried to force it.",
]

ENDINGS = [
    "Milo smiled. 'Next time, we investigate together.' Luna nodded, and the two friends left the repaired mechanism ready for morning.",
    "Luna said, 'We were safer because we listened to each other.' Milo tied a bright caution ribbon beside the mechanism.",
    "They wrote a clear note explaining the cause, then promised never to turn a mystery into a dare.",
    "The neighbors thanked both friends. Their careful friendship had solved the puzzle without harming the old machine.",
]

ASP_RULES = r"""
#show mystery/1.
#show safe/1.

mystery(X) :- mechanism(X), unexplained(X).
safe(X) :- mechanism(X), checked(X), protected(X).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("mechanism", "hidden_device"),
            asp.fact("unexplained", "hidden_device"),
            asp.fact("checked", "hidden_device"),
            asp.fact("protected", "hidden_device"),
        ]
    )


def asp_program(show: str = "#show mystery/1.\n#show safe/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mystery storyworld about a mechanism, friendship, caution, and a twist."
    )
    parser.add_argument("--child", choices=NAMES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--place", choices=PLACES, default=None)
    parser.add_argument("--mystery", type=int, choices=range(len(MYSTERIES)))
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
        seed=args.seed,
        child=args.child or rng.choice(NAMES),
        friend=args.friend or rng.choice(FRIENDS),
        place=args.place or rng.choice(PLACES),
        mystery=args.mystery if args.mystery is not None else rng.randrange(len(MYSTERIES)),
        opening=rng.randrange(len(OPENINGS)),
        clue=rng.randrange(len(CLUE_LINES)),
        twist=rng.randrange(len(TWISTS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.child == params.friend:
        raise StoryError("The child and friend must have different names.")
    if not 0 <= params.mystery < len(MYSTERIES):
        raise StoryError("The mystery choice is outside the available registry.")

    mystery = MYSTERIES[params.mystery]
    world = World()

    child = world.add(
        Entity(
            id="child",
            type="investigator",
            label=params.child,
            meters={"reach": 0.7, "care": 0.9},
            memes={"curiosity": 1.0, "trust": 0.8},
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            type="helper",
            label=params.friend,
            meters={"reach": 0.8, "care": 0.9},
            memes={"courage": 0.8, "trust": 0.9},
        )
    )
    machine = world.add(
        Entity(
            id="mechanism",
            type="device",
            label=mystery["object"],
            meters={"stability": 0.4, "risk": 0.7},
            memes={"mystery": 1.0},
        )
    )

    values = {
        "child": child.label,
        "friend": friend.label,
        "place": params.place,
    }

    world.say(OPENINGS[params.opening].format(**values))
    world.say(mystery["premise"])
    world.say(f"{friend.label} whispered, 'Should we pull the handle and see?'")
    world.say(f"{child.label} shook their head. 'Not yet. If there is a mechanism, forcing it could make the danger worse.'")
    world.say(CLUE_LINES[params.clue])
    world.say(mystery["clue"])
    world.say(f"{friend.label} asked, 'What do you think is moving?'")
    world.say(f"{child.label} answered, 'The {mystery['object']} is only the visible part. Let us find the cause before we touch it.'")
    world.say(mystery["mechanism"])
    world.say(mystery["danger"])
    world.say(TWISTS[params.twist])
    world.say(f"{friend.label} held the lamp steady while {child.label} made a careful adjustment.")
    world.say(mystery["result"])
    world.say(f"{child.label} said, 'The mystery is solved because we tested our idea instead of guessing.'")
    world.say(f"{friend.label} replied, 'And because we watched out for each other.'")
    world.say(mystery["lesson"])
    world.say(ENDINGS[params.ending])
    world.say(mystery["image"])

    child.memes["confidence"] = 1.0
    friend.memes["confidence"] = 1.0
    machine.meters["stability"] = 1.0
    machine.meters["risk"] = 0.0
    machine.memes["mystery"] = 0.0

    world.facts.update(
        child=child,
        friend=friend,
        mechanism=machine,
        mystery=mystery,
        place=params.place,
        solved=True,
        cautious=True,
        friendship=True,
        twist=True,
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
    mystery = world.facts["mystery"]
    child = world.facts["child"].label
    friend = world.facts["friend"].label
    return [
        f"Write a child-friendly mystery about {child} and {friend} investigating {mystery['title']}.",
        f"Tell a cautionary friendship story where a hidden mechanism explains {mystery['object']}.",
        f"Write a mystery with dialogue, careful testing, a surprising twist, and a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    mystery = world.facts["mystery"]
    child = world.facts["child"].label
    friend = world.facts["friend"].label
    return [
        QAItem(
            question=f"What mystery did {child} and {friend} investigate?",
            answer=f"They investigated {mystery['title']}, involving a {mystery['object']}.",
        ),
        QAItem(
            question="What clue helped explain the mystery?",
            answer=mystery["clue"],
        ),
        QAItem(
            question="What was the hidden mechanism?",
            answer=mystery["mechanism"],
        ),
        QAItem(
            question="Why did the friends avoid forcing the object?",
            answer=f"They avoided forcing it because {mystery['danger'].lower()}",
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
            answer="A mechanism is a set of parts that work together to make something move, open, ring, or perform another action.",
        ),
        QAItem(
            question="Why is caution useful during a mystery?",
            answer="Caution helps people gather evidence and avoid damaging an object or hurting someone while they investigate.",
        ),
        QAItem(
            question="How can friendship help solve a problem?",
            answer="Friends can share observations, ask careful questions, and protect one another from unsafe choices.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    mysteries = set(asp.atoms(model, "mystery"))
    safe = set(asp.atoms(model, "safe"))
    if mysteries == {("hidden_device",)} and safe == {("hidden_device",)}:
        sample = generate(StoryParams())
        if all(word not in sample.story for word in ("{", "}", "None")):
            print("OK: ASP parity and generated story checks passed.")
            return 0
    print("MISMATCH: ASP parity or story validation failed.")
    return 1


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


CURATED = [
    StoryParams(child="Luna", friend="Milo", place="clocktower", mystery=0),
    StoryParams(child="Nia", friend="Bea", place="harbor shed", mystery=1, opening=1, clue=2, twist=1, ending=2),
    StoryParams(child="Pip", friend="Finn", place="museum attic", mystery=2, opening=3, clue=3, twist=2, ending=3),
    StoryParams(child="Tess", friend="Zuri", place="old greenhouse", mystery=3, opening=4, clue=1, twist=0, ending=1),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("mystery:", sorted(asp.atoms(model, "mystery")))
        print("safe:", sorted(asp.atoms(model, "safe")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        limit = max(50, args.n * 30)
        while len(samples) < args.n and attempt < limit:
            params = resolve_params(args, random.Random(base_seed + attempt))
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
            header = f"### {sample.params.child}: mystery at the {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
