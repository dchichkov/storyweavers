#!/usr/bin/env python3
"""
A small whodunit storyworld about a cumbersome hypoallergenic blanket.

The mystery is solved through kindness, reconciliation, and repetition:
characters listen to one another, revisit clues, and repair a friendship as
well as a practical problem.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE)))))
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    name: str
    kind: str
    trait: str
    place: str
    blanket_color: str
    seed: Optional[int] = None


@dataclass
class Character:
    name: str
    kind: str
    trait: str
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Blanket:
    color: str
    hypoallergenic: bool = True
    cumbersome: bool = True
    location: str = "the reading nook"
    folded: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Character
    friend: Character
    blanket: Blanket
    place: str
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "library": "in the little library",
    "greenhouse": "beside the warm greenhouse",
    "clubhouse": "in the pinewood clubhouse",
    "attic": "in the bright attic",
}

KINDS = ["rabbit", "fox", "mouse", "badger", "otter"]
TRAITS = ["curious", "patient", "gentle", "brave", "thoughtful"]
COLORS = ["blue", "golden", "red", "green", "violet"]

NAMES = {
    "rabbit": ["Luna", "Pip", "Clover"],
    "fox": ["Mara", "Sol", "Fenn"],
    "mouse": ["Nell", "Milo", "Tess"],
    "badger": ["Bran", "Mabel", "Rook"],
    "otter": ["Ollie", "Rue", "Wren"],
}

MYSTERIES = [
    {
        "object": "a brass bookmark",
        "clue": "a trail of soft blue threads beside the window",
        "suspect": "the sleepy magpie",
        "truth": "the bookmark had caught in the blanket's loose fringe and slid beneath the window seat",
        "method": "repeated the search from the window inward, lifting each fold gently",
        "ending": "the bookmark gleamed in the blanket fringe",
    },
    {
        "object": "a jar of honey biscuits",
        "clue": "three round crumbs under the reading stool",
        "suspect": "the hungry young badger",
        "truth": "the cumbersome blanket had dragged the biscuit jar from the stool when someone carried it across the room",
        "method": "walked the same path again, stopping wherever the blanket had bumped a leg",
        "ending": "the biscuit jar rested safely on a wide shelf",
    },
    {
        "object": "a silver thimble",
        "clue": "a tiny shine between two folded corners",
        "suspect": "the proud magpie",
        "truth": "the thimble had been tucked into a pocket of the blanket during sewing time",
        "method": "folded and unfolded the blanket in the same careful order",
        "ending": "the thimble shone beside the needle basket",
    },
    {
        "object": "a green story card",
        "clue": "a square mark in the dust near the door",
        "suspect": "the rushing fox",
        "truth": "the card had traveled under the cumbersome blanket when it was carried to the reading nook",
        "method": "repeated the carrying route with a cord tied to the blanket's corner",
        "ending": "the green card returned to the story box",
    },
]

LESSONS = [
    "kind questions can uncover clues that sharp accusations hide",
    "repeating a careful search can reveal what a hurried search misses",
    "reconciliation begins when everyone is allowed to tell the whole story",
    "kindness makes room for mistakes without turning them into blame",
]

DIALOGUE = [
    ('"I did not take it," {friend} said. "But I will help you look."',
     '"Then I am sorry I suspected you," {hero} replied. "Let us search together."'),
    ('"My paws moved the blanket," {friend} admitted. "I never saw the missing thing."',
     '"Thank you for telling me," {hero} said. "We can follow what really happened."'),
    ('"Ask me again, slowly," {friend} said. "I remember one more detail."',
     '"I will listen again," {hero} promised. "Every detail matters."'),
]

OPENINGS = [
    "On a quiet afternoon, everyone gathered for a story.",
    "Rain tapped the windows while the friends prepared a warm reading hour.",
    "The room smelled of paper, pine, and cocoa.",
    "A golden patch of sunlight crossed the floor as the friends settled down.",
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (place, kind, color)
        for place in PLACES
        for kind in KINDS
        for color in COLORS
    ]


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.kind not in KINDS:
        raise StoryError(f"Unknown character kind: {params.kind}")
    if params.blanket_color not in COLORS:
        raise StoryError(f"Unknown blanket color: {params.blanket_color}")

    number = params.seed if params.seed is not None else sum(
        (i + 1) * ord(c) for i, c in enumerate(params.name + params.place)
    )
    friend_kind = KINDS[(number + 1) % len(KINDS)]
    friend_name = NAMES[friend_kind][number % len(NAMES[friend_kind])]
    mystery = MYSTERIES[number % len(MYSTERIES)]
    opening = OPENINGS[number % len(OPENINGS)]
    dialogue = DIALOGUE[number % len(DIALOGUE)]
    lesson = LESSONS[number % len(LESSONS)]

    hero = Character(params.name, params.kind, params.trait, {"curiosity": 1.0})
    friend = Character(friend_name, friend_kind, "honest", {"trust": 0.5})
    blanket = Blanket(params.blanket_color, meters={"weight": 2.0, "warmth": 1.0},
                      memes={"comfort": 1.0, "embarrassment": 0.0})
    world = World(hero, friend, blanket, params.place)
    world.facts.update(
        mystery=mystery,
        opening=opening,
        dialogue=dialogue,
        lesson=lesson,
        object=mystery["object"],
        clue=mystery["clue"],
        suspect=mystery["suspect"],
        truth=mystery["truth"],
        method=mystery["method"],
        ending=mystery["ending"],
    )
    return world


def speak_and_reconcile(world: World) -> None:
    if "reconcile" in world.fired:
        return
    world.fired.add("reconcile")
    first, second = world.facts["dialogue"]
    world.say(first.format(hero=world.hero.name, friend=world.friend.name))
    world.say(second.format(hero=world.hero.name, friend=world.friend.name))
    world.friend.memes["trust"] = 1.0
    world.blanket.memes["embarrassment"] = 0.0
    world.facts["reconciled"] = True


def repeat_search(world: World) -> None:
    if not world.facts.get("reconciled"):
        raise StoryError("The repeated search requires reconciliation first.")
    if "search" in world.fired:
        return
    world.fired.add("search")
    world.say(
        f"They searched once, then repeated the search more slowly. "
        f"{world.hero.name} {world.facts['method']}."
    )
    world.blanket.meters["careful_searches"] = 2.0
    world.blanket.found = True
    world.blanket.location = "the reading nook"


def solve_mystery(world: World) -> None:
    if not world.blanket.found:
        raise StoryError("The mystery cannot be solved before the object is found.")
    if "solve" in world.fired:
        return
    world.fired.add("solve")
    world.say(
        f"The clue made sense at last: {world.facts['truth']}. "
        f"The missing {world.facts['object']} had never been stolen."
    )
    world.hero.memes["kindness"] = 1.0


def tell_story(world: World) -> None:
    h = world.hero
    f = world.friend
    b = world.blanket
    mystery = world.facts

    world.say(
        f"{mystery['opening']} {PLACES[world.place]}, {h.name}, a {h.trait} "
        f"{h.kind}, brought out a {b.color} hypoallergenic blanket."
    )
    world.say(
        f"It was warm and clean, but cumbersome, so {h.name} carried it with both paws. "
        f"Then the {mystery['object']} vanished."
    )

    world.para()
    world.say(
        f"Everyone noticed {mystery['clue']}. {h.name} wondered whether "
        f"{mystery['suspect']} had taken the missing object."
    )
    speak_and_reconcile(world)
    world.say(
        f"Instead of blaming {f.name}, {h.name} asked what had happened before the mystery began."
    )

    world.para()
    repeat_search(world)
    solve_mystery(world)

    world.para()
    world.say(
        f"{f.name} helped return the {mystery['object']}, and {h.name} folded the "
        f"hypoallergenic blanket into a neat square. The friends shared the blanket "
        f"without a quarrel; {mystery['ending']}."
    )
    world.say(
        f"They remembered that {mystery['lesson']}. "
        f"The next reading hour began with kindness, and the same careful questions."
    )
    world.facts.update(
        resolved=True,
        hero=h,
        friend=f,
        blanket=b,
        place=world.place,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly whodunit about {f['object']} disappearing near a {world.blanket.color} hypoallergenic blanket.",
        f"Tell a mystery in which a cumbersome blanket creates a clue and kindness leads to reconciliation.",
        f"Write a repeated-search mystery where {f['clue']} helps solve the case.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What disappeared in the mystery?",
            answer=f"The missing object was {f['object']}.",
        ),
        QAItem(
            question=f"Why did {world.hero.name} first suspect {f['suspect']}?",
            answer=f"{world.hero.name} noticed {f['clue']}, so that clue made {f['suspect']} seem suspicious at first.",
        ),
        QAItem(
            question="How did the friends repair their disagreement?",
            answer=(
                f"They spoke honestly and kindly. {world.hero.name} apologized for suspecting "
                f"{world.friend.name}, and then they searched together."
            ),
        ),
        QAItem(
            question="What solved the mystery?",
            answer=(
                f"They repeated the search slowly and discovered that {f['truth']}. "
                f"The object had not been stolen."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does hypoallergenic mean?",
            answer="Hypoallergenic describes something made to be less likely to cause an allergic reaction.",
        ),
        QAItem(
            question="What does cumbersome mean?",
            answer="Cumbersome means difficult to carry, move, or use because it is awkward or heavy.",
        ),
        QAItem(
            question="Why can repeating a search help?",
            answer="Repeating a search slowly can reveal a clue that was overlooked when people were hurried.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is making peace after a disagreement by listening, apologizing, and rebuilding trust.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return "\n".join([
        "--- world model state ---",
        f"place={world.place}",
        f"hero={world.hero.name} ({world.hero.kind}, {world.hero.trait})",
        f"friend={world.friend.name} ({world.friend.kind})",
        f"blanket.color={world.blanket.color}",
        f"blanket.hypoallergenic={world.blanket.hypoallergenic}",
        f"blanket.cumbersome={world.blanket.cumbersome}",
        f"blanket.found={world.blanket.found}",
        f"blanket.meters={world.blanket.meters}",
        f"blanket.memes={world.blanket.memes}",
        f"reconciled={world.facts.get('reconciled')}",
        f"fired={sorted(world.fired)}",
    ])


ASP_RULES = r"""
place(P) :- place_name(P).
kind(K) :- kind_name(K).
color(C) :- color_name(C).
valid(P,K,C) :- place(P), kind(K), color(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.extend(asp.fact("place_name", x) for x in PLACES)
    lines.extend(asp.fact("kind_name", x) for x in KINDS)
    lines.extend(asp.fact("color_name", x) for x in COLORS)
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and ASP.")
    return 1


@dataclass
class _Args:
    place: Optional[str] = None
    kind: Optional[str] = None
    trait: Optional[str] = None
    color: Optional[str] = None
    name: Optional[str] = None
    n: int = 1
    seed: Optional[int] = None
    all: bool = False
    trace: bool = False
    qa: bool = False
    json: bool = False
    asp: bool = False
    verify: bool = False
    show_asp: bool = False


CURATED = [
    StoryParams("Luna", "rabbit", "curious", "library", "blue"),
    StoryParams("Mara", "fox", "patient", "greenhouse", "golden"),
    StoryParams("Nell", "mouse", "gentle", "clubhouse", "red"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A kindness-centered whodunit with a cumbersome hypoallergenic blanket.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--kind", choices=KINDS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--color", choices=COLORS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    kind = args.kind or rng.choice(KINDS)
    return StoryParams(
        name=args.name or rng.choice(NAMES[kind]),
        kind=kind,
        trait=args.trait or rng.choice(TRAITS),
        place=args.place or rng.choice(list(PLACES)),
        blanket_color=args.color or rng.choice(COLORS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
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
        raise SystemExit(asp_verify())
    if args.asp:
        for place, kind, color in asp_valid_combos():
            print(f"{place:12} {kind:10} {color}")
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, args.n)):
            rng = random.Random(base + i)
            params = resolve_params(args, rng)
            params.seed = base + i
            samples.append(generate(params))

    if args.json:
        print(
            samples[0].to_json()
            if len(samples) == 1
            else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False)
        )
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name}: {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
