#!/usr/bin/env python3
"""
A small detective-story world about a lush place, a worried head, a germ,
and a reconciliation at the end.

A seed tale idea:
---
The garden was lush and green, but every morning the same mystery returned:
one child woke with a scratchy head and a bad mood. A detective noticed the
pattern, followed clues through the wet leaves, and found that a tiny germ
was hiding in a comb. After a careful wash and a kind apology, the child and
the parent made up, and the garden felt bright again.
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


@dataclass
class Person:
    id: str
    role: str
    name: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.role in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.role in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str
    lush: bool = True
    wet: bool = False
    clues: list[str] = field(default_factory=list)


@dataclass
class Suspect:
    id: str
    label: str
    clue: str
    germy: bool = False
    cleaned: bool = False


@dataclass
class StoryParams:
    place: str
    detective: str
    detective_role: str
    child_name: str
    child_role: str
    parent_name: str
    parent_role: str
    suspect: str
    seed: Optional[int] = None


PLACES = {
    "garden": Place(name="the lush garden", lush=True, wet=True),
    "schoolyard": Place(name="the schoolyard", lush=False, wet=False),
    "porch": Place(name="the porch", lush=False, wet=True),
    "park": Place(name="the park", lush=True, wet=True),
}

DETECTIVES = [
    ("Mina", "girl"),
    ("Theo", "boy"),
    ("June", "girl"),
    ("Finn", "boy"),
]

CHILDREN = [
    ("Lila", "girl"),
    ("Noah", "boy"),
    ("Ivy", "girl"),
    ("Eli", "boy"),
]

PARENTS = [
    ("Mara", "mother"),
    ("Ben", "father"),
    ("Ada", "mother"),
    ("Owen", "father"),
]

SUSPECTS = {
    "comb": Suspect(id="comb", label="a comb", clue="tiny teeth"),
    "hat": Suspect(id="hat", label="a hat", clue="a warm seam"),
    "pillow": Suspect(id="pillow", label="a pillow", clue="soft cloth"),
    "brush": Suspect(id="brush", label="a brush", clue="stiff bristles"),
}


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.people: dict[str, Person] = {}
        self.suspects: dict[str, Suspect] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add_person(self, p: Person) -> Person:
        self.people[p.id] = p
        return p

    def add_suspect(self, s: Suspect) -> Suspect:
        self.suspects[s.id] = s
        return s

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _detective_intro(world: World, detective: Person) -> None:
    world.say(
        f"{detective.name} was a little detective with a sharp eye and a careful head."
    )
    world.say(
        f"{detective.pronoun().capitalize()} liked quiet clues, muddy footprints, and solving puzzles in neat order."
    )


def _case_setup(world: World, detective: Person, child: Person, parent: Person, suspect: Suspect) -> None:
    world.say(
        f"One morning in {world.place.name}, the leaves were lush and the air smelled clean."
    )
    world.say(
        f"But {child.name} kept rubbing {child.pronoun('possessive')} head and frowning, and {parent.name} looked worried."
    )
    world.say(
        f"{parent.name} asked {detective.name} to solve the mystery before the day turned into tears."
    )
    world.facts["case_started"] = True
    world.facts["suspect_label"] = suspect.label


def _collect_clues(world: World, suspect: Suspect) -> None:
    world.place.clues.extend(["a fallen hair ribbon", "a damp spot", suspect.clue])
    world.say(
        f"{detective_name(world)} followed the trail of clues: a fallen ribbon, a damp spot, and {suspect.clue} near the shelf."
    )


def detective_name(world: World) -> str:
    return world.facts["detective"].name  # type: ignore[index]


def child_name(world: World) -> str:
    return world.facts["child"].name  # type: ignore[index]


def parent_name(world: World) -> str:
    return world.facts["parent"].name  # type: ignore[index]


def _discover_germ(world: World, suspect: Suspect, child: Person, parent: Person) -> None:
    suspect.germy = True
    child.meters["itch"] = child.meters.get("itch", 0.0) + 1.0
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    world.say(
        f"At last, {detective_name(world)} found the answer: a tiny germ had hidden in {suspect.label}."
    )
    world.say(
        f"That was why {child.name}'s head felt scratchy and why {child.pronoun('subject')} had been so cross."
    )
    world.facts["germ_found"] = True


def _clean_and_reconcile(world: World, suspect: Suspect, child: Person, parent: Person) -> None:
    suspect.cleaned = True
    child.memes["worry"] = 0.0
    child.meters["itch"] = 0.0
    parent.memes["relief"] = parent.memes.get("relief", 0.0) + 1.0
    child.memes["reconciliation"] = 1.0
    parent.memes["reconciliation"] = 1.0
    world.say(
        f"{parent.name} washed {suspect.label} carefully, and the germ was gone."
    )
    world.say(
        f"{child.name} took a deep breath, then said sorry for the cranky words."
    )
    world.say(
        f"{parent.name} hugged {child.name}, and the two made up at once."
    )
    world.say(
        f"By evening, the lush garden was calm again, and {child.name}'s head felt light and clear."
    )
    world.facts["reconciled"] = True


def tell_story(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place=place)

    detective = world.add_person(Person(id="detective", role=params.detective_role, name=params.detective))
    child = world.add_person(Person(id="child", role=params.child_role, name=params.child_name))
    parent = world.add_person(Person(id="parent", role=params.parent_role, name=params.parent_name))
    suspect = world.add_suspect(SUSPECTS[params.suspect])

    world.facts["detective"] = detective
    world.facts["child"] = child
    world.facts["parent"] = parent
    world.facts["suspect"] = suspect
    world.facts["place"] = place

    _detective_intro(world, detective)
    world.para()
    _case_setup(world, detective, child, parent, suspect)
    world.para()
    _collect_clues(world, suspect)
    _discover_germ(world, suspect, child, parent)
    world.para()
    _clean_and_reconcile(world, suspect, child, parent)
    return world


def story_qa(world: World) -> list[QAItem]:
    detective: Person = world.facts["detective"]  # type: ignore[assignment]
    child: Person = world.facts["child"]  # type: ignore[assignment]
    parent: Person = world.facts["parent"]  # type: ignore[assignment]
    suspect: Suspect = world.facts["suspect"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who solved the mystery in {place.name}?",
            answer=f"{detective.name} solved it by following the clues and finding the germ.",
        ),
        QAItem(
            question=f"What was wrong with {child.name}'s head?",
            answer=f"{child.name}'s head felt scratchy because a tiny germ was hiding in {suspect.label}.",
        ),
        QAItem(
            question=f"How did {child.name} and {parent.name} end the story?",
            answer=f"They made up, because {parent.name} washed {suspect.label} and {child.name} said sorry.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does lush mean?",
            answer="Lush means full of healthy, rich, green growth, like a garden after good rain.",
        ),
        QAItem(
            question="What is a germ?",
            answer="A germ is a tiny living thing that can make people feel sick or itchy if it gets where it should not be.",
        ),
        QAItem(
            question="What is a detective for?",
            answer="A detective looks for clues and uses them to solve a mystery.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means two people stop being upset and make peace again.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    detective: Person = world.facts["detective"]  # type: ignore[assignment]
    child: Person = world.facts["child"]  # type: ignore[assignment]
    parent: Person = world.facts["parent"]  # type: ignore[assignment]
    suspect: Suspect = world.facts["suspect"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    return [
        f"Write a short detective story for a young child set in {place.name} with a lush scene, a head mystery, and a germ clue.",
        f"Tell a gentle mystery where {detective.name} helps {child.name} and {parent.name} find out why {child.name}'s head feels bad.",
        f"Write a simple story that begins with clues in {place.name}, names {suspect.label}, and ends with reconciliation.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for p in world.people.values():
        lines.append(f"  {p.id}: role={p.role} meters={p.meters} memes={p.memes}")
    for s in world.suspects.values():
        lines.append(f"  {s.id}: germy={s.germy} cleaned={s.cleaned}")
    lines.append(f"  place: {world.place.name} lush={world.place.lush} wet={world.place.wet}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective-story world about a lush place, a head mystery, and reconciliation.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--detective")
    ap.add_argument("--detective-role", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--child-role", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-role", choices=["mother", "father"])
    ap.add_argument("--suspect", choices=SUSPECTS.keys())
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
    place = args.place or rng.choice(list(PLACES.keys()))
    detective, detective_role = (args.detective, args.detective_role) if args.detective and args.detective_role else rng.choice(DETECTIVES)
    child_name, child_role = (args.child_name, args.child_role) if args.child_name and args.child_role else rng.choice(CHILDREN)
    parent_name, parent_role = (args.parent_name, args.parent_role) if args.parent_name and args.parent_role else rng.choice(PARENTS)
    suspect = args.suspect or rng.choice(list(SUSPECTS.keys()))
    return StoryParams(place=place, detective=detective, detective_role=detective_role, child_name=child_name, child_role=child_role, parent_name=parent_name, parent_role=parent_role, suspect=suspect)


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


ASP_RULES = r"""
place(garden). place(schoolyard). place(porch). place(park).
lush(garden). lush(park).
wet(garden). wet(porch). wet(park).

person(detective). person(child). person(parent).
suspect(comb). suspect(hat). suspect(pillow). suspect(brush).

clue(garden, ribbon). clue(garden, spot). clue(garden, teeth).

germy(comb) :- suspect(comb).
germy(brush) :- suspect(brush).

mystery(place(P)) :- lush(P), wet(P).
resolved :- germy(S), suspect(S).
reconciliation :- resolved.

#show lush/1.
#show germy/1.
#show resolved/0.
#show reconciliation/0.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        if PLACES[p].lush:
            lines.append(asp.fact("lush", p))
        if PLACES[p].wet:
            lines.append(asp.fact("wet", p))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show lush/1.\n#show germy/1.\n#show resolved/0.\n#show reconciliation/0."))
    atoms = set((sym.name, tuple(str(a) for a in sym.arguments)) for sym in model)
    needed = {("lush", ("garden",)), ("lush", ("park",))}
    if not needed.issubset(atoms):
        print("MISMATCH: ASP gate did not produce expected lush facts.")
        return 1
    print("OK: ASP twin parses and emits the expected core facts.")
    return 0


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
    StoryParams(place="garden", detective="Mina", detective_role="girl", child_name="Lila", child_role="girl", parent_name="Mara", parent_role="mother", suspect="comb"),
    StoryParams(place="park", detective="Theo", detective_role="boy", child_name="Noah", child_role="boy", parent_name="Ben", parent_role="father", suspect="brush"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolved/0.\n#show reconciliation/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
