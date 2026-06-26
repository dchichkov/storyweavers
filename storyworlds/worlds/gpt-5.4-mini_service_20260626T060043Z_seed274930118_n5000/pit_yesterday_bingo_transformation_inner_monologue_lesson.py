#!/usr/bin/env python3
"""
A heartwarming tiny storyworld about a child, a pit, yesterday's mishap, and
a bingo game that changes how they feel and act.

The world premise:
- Yesterday, something precious slipped into a shallow pit.
- Today, the child goes to bingo with a worried heart.
- A kind helper and a small transformation turn embarrassment into empathy.
- The child learns a gentle lesson and ends feeling proud, not ashamed.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "hall": Place(id="hall", label="the community hall", indoors=True, affords={"bingo"}),
    "center": Place(id="center", label="the neighborhood center", indoors=True, affords={"bingo"}),
    "church": Place(id="church", label="the church basement", indoors=True, affords={"bingo"}),
}

GIRL_NAMES = ["Maya", "Lena", "Nora", "Ivy", "Ava", "Zoe"]
BOY_NAMES = ["Eli", "Noah", "Owen", "Finn", "Milo", "Leo"]
PARENTS = {"girl": "mother", "boy": "father"}

# One tiny activity: bingo.
BINGO = {
    "id": "bingo",
    "verb": "play bingo",
    "gerund": "playing bingo",
    "hall_tell": "The room smelled like crayons and warm cocoa, and the bingo cards waited in neat stacks.",
    "sound": "the cheerful call of numbers",
}

# Transformation: shame -> calm confidence, and stained hands -> clean hands.
TRANSFORMATION = {
    "before": "embarrassed and tight inside",
    "after": "calm and proud",
    "action": "wash the dusty hands, breathe slowly, and choose to help instead of hide",
}

# Lesson learned phrasing.
LESSON = "When something goes wrong, kindness can turn a hard day into a better one."


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_place/1.
#show valid_story/3.

valid_place(P) :- place(P), affords(P,bingo).
valid_story(P,N,G) :- valid_place(P), name(N), gender(G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for n in GIRL_NAMES:
        lines.append(asp.fact("name", n))
        lines.append(asp.fact("gender", n, "girl"))
    for n in BOY_NAMES:
        lines.append(asp.fact("name", n))
        lines.append(asp.fact("gender", n, "boy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_place/1."))
    return sorted(set(asp.atoms(model, "valid_place")))


def asp_verify() -> int:
    py = {(k,) for k, p in PLACES.items() if "bingo" in p.affords}
    cl = set(asp_valid_places())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} places).")
        return 0
    print("MISMATCH")
    print(" python:", sorted(py))
    print(" clingo:", sorted(cl))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    place = args.place or rng.choice(list(PLACES))
    if "bingo" not in PLACES[place].affords:
        raise StoryError("That place cannot host a bingo story.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or PARENTS[gender]
    return StoryParams(place=place, name=name, gender=gender, parent=parent)


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    card = world.add(Entity(
        id="card",
        kind="thing",
        type="card",
        label="bingo card",
        phrase="a bright bingo card with blue stars",
        owner=child.id,
    ))
    pit = world.add(Entity(
        id="pit",
        kind="thing",
        type="pit",
        label="pit",
        phrase="a shallow pit behind the fence",
    ))

    # Yesterday: the card fell into the pit.
    child.memes["worry"] = 1.0
    child.memes["memory"] = 1.0
    world.facts["yesterday_lost"] = True
    world.facts["lesson"] = LESSON

    world.say(
        f"Yesterday, {child.id} carried {card.phrase} too close to a shallow pit, "
        f"and down it slipped."
    )
    world.say(
        f"{child.id} stood there with a sinking feeling, because {card.label} was the card "
        f"for today's bingo game."
    )

    # Inner monologue before the turn.
    world.para()
    world.say(
        f'Inside, {child.id} thought, "I should have been more careful. '
        f'Now everyone will notice."'
    )
    world.say(
        f'But {child.id} also thought, "Maybe I can still help make today kind."'
    )

    # Today: bingo, and a transformation.
    world.para()
    world.say(
        f"At the community hall, the tables were set for bingo, and {BINGO['hall_tell']}"
    )
    world.say(
        f"When the caller began the first round, {child.id} noticed a little kid searching for a lost marker."
    )
    world.say(
        f"Instead of hiding in worry, {child.id} chose to {TRANSFORMATION['action']}."
    )
    world.say(
        f"That small choice changed {child.id} from {TRANSFORMATION['before']} to {TRANSFORMATION['after']}."
    )
    child.memes["worry"] = 0.0
    child.memes["pride"] = 1.0
    child.memes["kindness"] = 1.0
    world.facts["transformed"] = True

    # Resolution.
    world.para()
    world.say(
        f"The {params.parent} smiled when {child.id} explained what happened yesterday and how {child.pronoun()} helped today."
    )
    world.say(
        f"By the end of bingo, {child.id} still remembered the pit, but it no longer felt like a bad ending."
    )
    world.say(
        f"{child.id} went home calm and proud, carrying the lesson in a warm chest and a softer smile."
    )
    world.say(f"Lesson learned: {LESSON}")

    world.facts.update(
        child=child,
        parent=parent,
        card=card,
        pit=pit,
        place=place,
        activity=BINGO,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    return [
        f"Write a heartwarming story about {child.id}, a pit, yesterday, and a bingo day that ends with a lesson learned.",
        f"Tell a gentle tale where {child.id} remembers something from yesterday and transforms worry into kindness at bingo.",
        f"Create a short story for children about losing a bingo card in a pit and finding a better feeling on game day.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What happened yesterday to {child.id}'s bingo card?",
            answer=f"Yesterday, {child.id}'s bingo card slipped into a pit behind the fence.",
        ),
        QAItem(
            question=f"How did {child.id} feel before the bingo game started?",
            answer=f"{child.id} felt worried and embarrassed at first, but also hoped to be helpful.",
        ),
        QAItem(
            question=f"What changed {child.id} during bingo at {place.label}?",
            answer=f"{child.id} noticed someone else needed help, chose kindness, and felt proud and calm instead of stuck in worry.",
        ),
        QAItem(
            question=f"What lesson was learned by the end?",
            answer=LESSON,
        ),
        QAItem(
            question=f"Who smiled when {child.id} explained what happened?",
            answer=f"The {parent.type} smiled because {child.id} told the truth and helped make the day better.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pit?",
            answer="A pit is a hole in the ground. It can be shallow or deep, and things can fall into it.",
        ),
        QAItem(
            question="What is bingo?",
            answer="Bingo is a game where people listen for numbers and mark them on a card.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a new state. In stories, a feeling can transform from worry into confidence.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice inside a character's mind, where they think about what to do or how they feel.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming storyworld about pit, yesterday, and bingo.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if args.all:
        for place in PLACES:
            for gender in ["girl", "boy"]:
                params = StoryParams(
                    place=place,
                    name=GIRL_NAMES[0] if gender == "girl" else BOY_NAMES[0],
                    gender=gender,
                    parent=PARENTS[gender],
                )
                samples.append(generate(params))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            params.seed = args.seed if args.seed is not None else None
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
