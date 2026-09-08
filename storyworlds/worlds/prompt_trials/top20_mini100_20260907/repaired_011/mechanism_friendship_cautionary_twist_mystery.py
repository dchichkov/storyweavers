#!/usr/bin/env python3
"""
A small mystery storyworld about a mechanism, friendship, a cautionary twist,
and a harmless but puzzling reveal.

Seed premise:
A child and a friend find a strange mechanism in a quiet place. Their curiosity
leads them through a small mystery, a cautionary warning, and a twist that
changes what they think is happening.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    child: str
    friend: str
    adult: str
    place: str
    mechanism_name: str
    mechanism_part: str
    object_name: str
    warning: str
    twist: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


NAMES = ["Mina", "Theo", "Lila", "Jun", "Nora", "Eli", "Zoe", "Ari"]
FRIENDS = ["Pip", "Bea", "Max", "Rae", "Toby", "Momo"]
ADULTS = ["mom", "dad", "aunt", "uncle", "grandma", "grandpa"]
PLACES = ["library basement", "garden shed", "old boathouse", "school attic", "museum hallway", "quiet garage"]
MECHANISMS = ["clockwork box", "secret latch", "humming dial", "tiny pulley gate", "brass lever panel", "spinning keywheel"]
PARTS = ["a hidden lever", "a glass window", "a loose gear", "a narrow slot", "a spring latch", "a painted arrow"]
OBJECTS = ["blue marble", "paper map", "silver button", "red ribbon", "cookie tin", "small key"]
WARNINGS = [
    "Don't pull the lever twice.",
    "If it clicks, step back first.",
    "Never put your fingers near the moving gear.",
    "Wait until the sound stops before touching it.",
    "Only one turn, or the box may jam.",
]
TWISTS = [
    "the mysterious sound came from a wind-up toy hiding inside",
    "the strange rattle was only a postcard bouncing in a tin drawer",
    "the machine was not guarding treasure; it was opening a snack tray",
    "the scary clunk was a loose marble dropping into a cup",
    "the puzzle mechanism was making a map rise out of a secret sleeve",
    "the whispering noise was the friender's own flashlight rattling on the floor",
]


ASP_RULES = r"""
#show valid/5.
#show valid_story/6.

valid(C,F,A,P,M) :- child_name(C), friend_name(F), adult_name(A), place_name(P), mechanism_name(M).
valid_story(C,F,A,P,M,O) :- valid(C,F,A,P,M), object_name(O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for n in NAMES:
        lines.append(asp.fact("child_name", n))
    for f in FRIENDS:
        lines.append(asp.fact("friend_name", f))
    for a in ADULTS:
        lines.append(asp.fact("adult_name", a))
    for p in PLACES:
        lines.append(asp.fact("place_name", p))
    for m in MECHANISMS:
        lines.append(asp.fact("mechanism_name", m))
    for part in PARTS:
        lines.append(asp.fact("mechanism_part_name", part))
    for o in OBJECTS:
        lines.append(asp.fact("object_name", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


PREMISES = [
    "{child} and {friend} found a strange {mechanism_name} in the {place}. It looked important, and it looked a little spooky too.",
    "On a quiet afternoon, {child} and {friend} slipped into the {place} and noticed a {mechanism_name} beside a dusty shelf.",
    "{adult} sent {child} and {friend} to fetch a forgotten {object_name} from the {place}, but they discovered a {mechanism_name} instead.",
    "The {place} was so still that even a small tick sounded loud. Then {child} saw a {mechanism_name} with one bright {mechanism_part}.",
]

OPENERS = [
    "{child} leaned closer and whispered, 'What do you think it does?'",
    "{friend} pointed at the mechanism and said, 'It has to mean something.'",
    "{child} asked, 'Should we touch it?' and {friend} answered, 'Only if we do it carefully.'",
    "The two friends exchanged a worried look, and {friend} said, 'Let's not guess too fast.'",
]

TURNS = [
    "They found the warning taped to the side: '{warning}'",
    "A second note fluttered from beneath the mechanism: '{warning}'",
    "Then {child} read a faded label: '{warning}'",
    "Inside the dust, they spotted a neat little sign: '{warning}'",
]

ACTIONS = [
    "{child} and {friend} decided to try one careful turn together. When the mechanism clicked, they both jumped back exactly as the warning said.",
    "Instead of yanking it, {child} turned the part slowly while {friend} counted the seconds. The mechanism answered with one soft clack.",
    "{friend} held the flashlight while {child} moved the {mechanism_part} only a little. The machine shivered, but it did not break.",
    "They took a breath, then worked together: one held the side, the other nudged the lever. The mechanism gave a tiny sigh and stopped.",
]

TWIST_LINES = [
    "Then came the twist: {twist}.",
    "But the real answer was even kinder: {twist}.",
    "After that, they learned the surprise was simple: {twist}.",
    "The mystery changed shape in a blink, because {twist}.",
]

ENDINGS = [
    "The friends laughed at their own spooky guesses. {adult} smiled, and the little mechanism sat quietly, safe and understood.",
    "{child} and {friend} carried the {object_name} home, relieved that the mystery was harmless and happy in the end.",
    "By the time they left the {place}, the scary feeling was gone. The mechanism had become just another careful secret they had solved together.",
    "{adult} praised their caution, and the friends walked out proud of how they listened, waited, and solved the puzzle without rushing.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mystery storyworld about a mechanism, friendship, caution, and a twist.")
    ap.add_argument("--child", choices=NAMES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--adult", choices=ADULTS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mechanism-name", dest="mechanism_name", choices=MECHANISMS)
    ap.add_argument("--mechanism-part", dest="mechanism_part", choices=PARTS)
    ap.add_argument("--object-name", dest="object_name", choices=OBJECTS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        child=args.child or rng.choice(NAMES),
        friend=args.friend or rng.choice(FRIENDS),
        adult=args.adult or rng.choice(ADULTS),
        place=args.place or rng.choice(PLACES),
        mechanism_name=args.mechanism_name or rng.choice(MECHANISMS),
        mechanism_part=args.mechanism_part or rng.choice(PARTS),
        object_name=args.object_name or rng.choice(OBJECTS),
        warning=rng.choice(WARNINGS),
        twist=rng.choice(TWISTS),
    )


def generate(params: StoryParams) -> StorySample:
    values = {
        "child": params.child,
        "friend": params.friend,
        "adult": params.adult,
        "place": params.place,
        "mechanism_name": params.mechanism_name,
        "mechanism_part": params.mechanism_part,
        "object_name": params.object_name,
        "warning": params.warning,
        "twist": params.twist,
    }

    w = World()
    w.add(Entity(id=params.child, kind="character", label=params.child, meters={"courage": 0.4}, memes={"curiosity": 0.8}))
    w.add(Entity(id=params.friend, kind="character", label=params.friend, meters={"courage": 0.5}, memes={"worry": 0.3}))
    w.add(Entity(id=params.adult, kind="character", label=params.adult, meters={"distance": 1.0}, memes={"calm": 0.7}))
    w.add(Entity(id="mechanism", kind="object", label=params.mechanism_name, meters={"tension": 0.2}, memes={"mystery": 1.0}))
    w.add(Entity(id="object", kind="object", label=params.object_name, meters={"hidden": 0.9}, memes={"importance": 0.5}))

    w.say(PREMISES[0].format(**values))
    w.say(OPENERS[0].format(**values))
    w.say(TURNS[0].format(**values))
    w.para()
    w.say(ACTIONS[0].format(**values))
    w.say("The sound was small, but it made the room feel much bigger and much more serious.")
    w.say(TWIST_LINES[0].format(**values))
    w.para()
    w.say(f"{params.child} said, 'So it was never dangerous?'")
    w.say(f"{params.friend} grinned and answered, 'Just mysterious.'")
    w.say(ENDINGS[0].format(**values))

    w.facts.update(
        child=params.child,
        friend=params.friend,
        adult=params.adult,
        place=params.place,
        mechanism=params.mechanism_name,
        object=params.object_name,
        warning=params.warning,
        twist=params.twist,
        solved=True,
        cautious=True,
    )

    prompts = [
        "Write a child-friendly mystery about friends finding a strange mechanism and solving it carefully.",
        f"Tell a cautionary story where {params.child} and {params.friend} discover a mechanism in the {params.place}.",
        "Write a short mystery with friendship, a warning, and a twist ending that changes what the characters think is happening.",
    ]

    story_qa = [
        QAItem(
            question="Who found the mechanism?",
            answer=f"{params.child} and {params.friend} found it together in the {params.place}.",
        ),
        QAItem(
            question="What warning did they hear?",
            answer=params.warning,
        ),
        QAItem(
            question="How did they solve the mystery safely?",
            answer=f"They listened to the warning, moved the {params.mechanism_part} carefully, and waited to see what happened next.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {params.twist}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of parts that work together to make something move, open, or change.",
        ),
        QAItem(
            question="Why is caution useful in a mystery story?",
            answer="Caution helps the characters avoid trouble while they investigate and solve the puzzle safely.",
        ),
        QAItem(
            question="What does friendship do in this kind of story?",
            answer="Friendship helps the characters work together, share ideas, and stay brave.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the story turn in a new direction.",
        ),
    ]

    return StorySample(params=params, story=w.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=w)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str, str, str, str, str]]:
    return [
        (c, f, a, p, m, mp, o)
        for c in NAMES
        for f in FRIENDS
        for a in ADULTS
        for p in PLACES
        for m in MECHANISMS
        for mp in PARTS
        for o in OBJECTS
    ]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted({tuple(x for x in tup) for tup in asp.atoms(model, "valid")})


def asp_verify() -> int:
    py = {(c, f, a, p, m) for (c, f, a, p, m, _, _) in valid_combos()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl)[:10])
    if cl - py:
        print("  only in clingo:", sorted(cl - py)[:10])
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(child="Mina", friend="Pip", adult="mom", place="library basement", mechanism_name="clockwork box", mechanism_part="a hidden lever", object_name="blue marble", warning="Don't pull the lever twice.", twist="the mysterious sound came from a wind-up toy hiding inside"),
        StoryParams(child="Theo", friend="Bea", adult="dad", place="garden shed", mechanism_name="brass lever panel", mechanism_part="a loose gear", object_name="paper map", warning="If it clicks, step back first.", twist="the strange rattle was only a postcard bouncing in a tin drawer"),
        StoryParams(child="Lila", friend="Max", adult="aunt", place="old boathouse", mechanism_name="tiny pulley gate", mechanism_part="a narrow slot", object_name="small key", warning="Never put your fingers near the moving gear.", twist="the machine was not guarding treasure; it was opening a snack tray"),
        StoryParams(child="Jun", friend="Rae", adult="grandma", place="museum hallway", mechanism_name="humming dial", mechanism_part="a spring latch", object_name="silver button", warning="Wait until the sound stops before touching it.", twist="the scary clunk was a loose marble dropping into a cup"),
    ]


CURATED = build_curated()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/6."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/5."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} and {p.friend} at the {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
