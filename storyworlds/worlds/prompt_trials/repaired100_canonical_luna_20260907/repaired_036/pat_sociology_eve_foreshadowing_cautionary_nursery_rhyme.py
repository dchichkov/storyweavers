#!/usr/bin/env python3
"""
A standalone nursery-rhyme storyworld about Pat, sociology, and Eve.

The seed premise:
Pat studies how people live together, but on the eve of a village fair,
a tempting shortcut threatens the shared bell. A small warning is noticed,
a careful choice is made, and the whole neighborhood learns that good
society is built by listening before acting.
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


PEOPLE = ["Pat", "Eve", "Mina", "Toby", "Nell", "Sam"]
PLACES = ["the village green", "the market lane", "the school yard", "the orchard gate"]
OBJECTS = ["the fair bell", "the ribbon arch", "the soup cart", "the lantern bridge"]
TOOLS = ["a blue ribbon", "a wooden brace", "a listening list", "a little handbell"]
ROLES = ["sociology student", "young neighbor", "village helper", "careful bell keeper"]

SCENES = [
    {
        "id": "loose_rope",
        "premise": "the fair bell hung from a rope that had begun to fray",
        "warning": "A single white thread curled loose and dropped beside Pat's shoe.",
        "temptation": "tie one quick knot and ring the bell before anyone noticed",
        "clue": "the top loop sagged whenever the wind turned west",
        "safe_action": "closed the path, asked the grown bell keeper to inspect the rope, and braced the post",
        "result": "the bell stayed still until its rope was safely replaced",
        "ending": "then the bell rang bright, with no one beneath its swinging weight",
    },
    {
        "id": "crowded_lane",
        "premise": "a narrow lane filled with baskets as families hurried toward the fair",
        "warning": "A basket handle snapped, and apples rolled toward the open well.",
        "temptation": "push through the crowd and clear the lane alone",
        "clue": "everyone was moving toward the same tiny gap",
        "safe_action": "asked the neighbors to step back, made two walking lines, and covered the well",
        "result": "the baskets were gathered without a child or apple falling",
        "ending": "the lane hummed like a happy rhyme, with room for every pair of feet",
    },
    {
        "id": "wet_bridge",
        "premise": "rain made the little lantern bridge shine above the brook",
        "warning": "One plank squeaked twice beneath a passing cart.",
        "temptation": "run across first and wave the fair crowd after",
        "clue": "the wet plank dipped only when the cart's left wheel crossed it",
        "safe_action": "stopped the cart, marked the weak board, and led everyone around by the dry stepping stones",
        "result": "the bridge was repaired before the lanterns were carried over it",
        "ending": "golden lights twinkled safely on both banks at dusk",
    },
]

WARNINGS = [
    "A tiny warning is a friend, not a foe.",
    "The smallest clue may tell the biggest truth.",
    "When many share a path, each voice can help.",
    "A pause can keep a whole village safe.",
]

LESSONS = [
    "Pat learned that sociology was not only a word in a book; it was the care people gave one another.",
    "Pat learned that a community is a promise made by many careful hands.",
    "Pat learned that listening to a group can be braver than rushing ahead alone.",
]


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    pat: Person
    eve: Person
    place: str
    object_name: str
    tool: str
    scene: dict
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    person: str
    companion: str
    place: str
    object_name: str
    tool: str
    role: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A cautionary nursery-rhyme world about Pat, sociology, and Eve."
    )
    parser.add_argument("--person", choices=PEOPLE)
    parser.add_argument("--companion", choices=PEOPLE)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--object-name", dest="object_name", choices=OBJECTS)
    parser.add_argument("--tool", choices=TOOLS)
    parser.add_argument("--role", choices=ROLES)
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


def valid_combo(params: StoryParams) -> bool:
    return (
        params.person != params.companion
        and params.person == "Pat"
        and params.companion == "Eve"
        and params.tool in TOOLS
    )


def asp_facts() -> str:
    import asp

    facts = []
    for person in PEOPLE:
        facts.append(asp.fact("person", person))
    for place in PLACES:
        facts.append(asp.fact("place", place))
    for item in OBJECTS:
        facts.append(asp.fact("object_name", item))
    for tool in TOOLS:
        facts.append(asp.fact("tool", tool))
    return "\n".join(facts)


ASP_RULES = r"""
chosen(P,E,L,O,T) :- person(P), person(E), place(L), object_name(O), tool(T), P != E.
pat_eve(P,E) :- chosen(P,E,_,_,_), P = "Pat", E = "Eve".
valid(P,E,L,O,T) :- chosen(P,E,L,O,T), pat_eve(P,E).
#show valid/5.
"""


def asp_program(show: str = "#show valid/5.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> set[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid"))


def asp_verify() -> int:
    python_values = set()
    for place in PLACES:
        for item in OBJECTS:
            for tool in TOOLS:
                params = StoryParams("Pat", "Eve", place, item, tool, ROLES[0])
                if valid_combo(params):
                    python_values.add(("Pat", "Eve", place, item, tool))
    clingo_values = asp_valid()
    if python_values == clingo_values:
        print(f"OK: clingo gate matches Python ({len(python_values)} combinations).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(clingo_values - python_values))
    print("only in python:", sorted(python_values - clingo_values))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    person = args.person or "Pat"
    companion = args.companion or "Eve"
    place = args.place or rng.choice(PLACES)
    object_name = args.object_name or rng.choice(OBJECTS)
    tool = args.tool or rng.choice(TOOLS)
    role = args.role or rng.choice(ROLES)
    params = StoryParams(person, companion, place, object_name, tool, role, args.seed)
    if not valid_combo(params):
        raise StoryError("The story requires Pat and Eve as different people.")
    return params


def make_world(params: StoryParams) -> World:
    stable_seed = params.seed
    if stable_seed is None:
        stable_seed = sum(
            (index + 1) * ord(char)
            for index, char in enumerate("|".join(map(str, vars(params).values())))
        )
    rng = random.Random(stable_seed)
    scene = rng.choice(SCENES)
    pat = Person(
        name="Pat",
        role=params.role,
        meters={"attention": 1.0, "distance": 0.0},
        memes={"curiosity": 1.0, "caution": 0.0, "trust": 0.0},
    )
    eve = Person(
        name="Eve",
        role="neighbor and listener",
        meters={"attention": 1.0, "distance": 0.0},
        memes={"caution": 1.0, "trust": 1.0},
    )
    return World(
        pat=pat,
        eve=eve,
        place=params.place,
        object_name=params.object_name,
        tool=params.tool,
        scene=scene,
        facts={
            "warning_line": rng.choice(WARNINGS),
            "lesson": rng.choice(LESSONS),
            "title": rng.choice(
                [
                    "Pat and Eve at the Fair",
                    "The Bell That Waited",
                    "The Careful Village Rhyme",
                ]
            ),
        },
    )


def generate_story(world: World) -> None:
    p = world.pat
    e = world.eve
    s = world.scene

    world.say(
        f"On the eve of the fair, Pat walked to {world.place}, "
        f"where {world.object_name} waited beneath a pear-tree sky."
    )
    world.say(
        f"Pat was a {p.role}, and studied sociology, the way people share, "
        "help, listen, and live together."
    )
    world.say(f"There Pat saw that {s['premise']}.")
    world.say(f"{s['warning']} {world.facts['warning_line']}")
    world.say(
        f'"I can {s["temptation"]}," said Pat. '
        f'"Not so fast," said Eve. "What does the little warning say?"'
    )
    world.say(
        f"Pat looked again and saw that {s['clue']}. "
        "The tempting shortcut grew smaller, while the careful plan grew clear."
    )
    p.memes["caution"] += 1
    p.memes["trust"] += 1
    e.memes["trust"] += 1
    world.say(
        f'"Let us tell the neighbors and make room for every voice," said Eve. '
        f'"Yes," said Pat, "a village works best when nobody is pushed aside."'
    )
    world.say(
        f"Pat used {world.tool} to mark the safe place, and the neighbors "
        f"{s['safe_action']}."
    )
    p.meters["distance"] = 1.0
    p.memes["curiosity"] += 1
    world.say(
        f"Because the warning was heard, {s['result']}. "
        f"{world.facts['lesson']}"
    )
    world.say(
        f"Then the fair began: {s['ending']} "
        "Pat and Eve smiled, for a careful community makes a cheerful rhyme."
    )


def story_qa(world: World) -> list[QAItem]:
    scene = world.scene
    return [
        QAItem(
            question="Who studied sociology in the story?",
            answer="Pat studied sociology, learning how people share, listen, help, and live together.",
        ),
        QAItem(
            question="Who helped Pat notice the warning?",
            answer="Eve helped Pat notice the small warning and choose a safer plan.",
        ),
        QAItem(
            question="What was the warning?",
            answer=f"{scene['warning']} It showed that the tempting shortcut could cause trouble.",
        ),
        QAItem(
            question="What did Pat do instead of rushing?",
            answer=f"Pat used {world.tool} to mark the safe place and helped the neighbors {scene['safe_action']}.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"Because the warning was heard, {scene['result']} The fair could begin safely.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sociology?",
            answer="Sociology is the study of how people live together in groups and communities.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue that hints at something important that may happen later.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means slowing down, noticing risks, and choosing a safer action.",
        ),
        QAItem(
            question="Why can listening help a community?",
            answer="Listening helps a community notice different needs and make room for better choices.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a cautionary nursery rhyme in which Pat studies sociology and learns from a small warning.",
        f"Tell how Pat and Eve keep {world.object_name} safe on the eve of a village fair.",
        f"Use foreshadowing through this clue: {world.scene['clue']}.",
    ]


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"pat={world.pat.name} role={world.pat.role} meters={world.pat.meters} memes={world.pat.memes}",
            f"eve={world.eve.name} role={world.eve.role} meters={world.eve.meters} memes={world.eve.memes}",
            f"place={world.place} object={world.object_name} tool={world.tool}",
            f"scene={world.scene['id']}",
            f"warning={world.scene['warning']}",
            f"result={world.scene['result']}",
        ]
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Pat", "Eve", "the village green", "the fair bell", "a blue ribbon", ROLES[0]),
    StoryParams("Pat", "Eve", "the market lane", "the ribbon arch", "a listening list", ROLES[1]),
    StoryParams("Pat", "Eve", "the orchard gate", "the lantern bridge", "a wooden brace", ROLES[2]),
]


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params):
        raise StoryError("Invalid story parameters: use Pat and Eve as distinct people.")
    world = make_world(params)
    generate_story(world)
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
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
