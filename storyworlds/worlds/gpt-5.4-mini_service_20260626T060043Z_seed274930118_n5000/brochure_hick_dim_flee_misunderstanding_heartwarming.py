#!/usr/bin/env python3
"""
storyworlds/worlds/brochure_hick_dim_flee_misunderstanding_heartwarming.py
===========================================================================

A small, self-contained story world about a misunderstood brochure, a sudden
fleeing moment, and a warm ending that clears the confusion.

Seed premise:
- A child finds a brochure that looks dim and strange.
- The child misunderstands it and flees.
- A kind adult explains the brochure and the child returns.
- The story ends with relief, belonging, and a gentle shared plan.

The world is intentionally tiny: one setting, one central object, one emotional
turn, and one heartwarming resolution.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str


@dataclass
class Brochure:
    label: str
    phrase: str
    place_name: str
    dimness: str
    keyword: str = "brochure"


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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

    def copy(self) -> "World":
        import copy

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _ensure_world_state(world: World) -> None:
    child = world.get("child")
    adult = world.get("adult")
    brochure = world.get("brochure")
    if child.memes.get("fear", 0.0) >= THRESHOLD and brochure.held_by == adult.id:
        child.memes["misunderstanding"] = 0.0


def _turn_flee(world: World) -> None:
    child = world.get("child")
    if child.memes.get("fear", 0.0) >= THRESHOLD and child.location == "outside":
        return


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child_name: str = "Mina"
    child_type: str = "girl"
    adult_name: str = "Aunt Jo"
    adult_type: str = "aunt"
    place: str = "the station bench"


PLACES = {
    "station": Place("the station bench"),
    "porch": Place("the porch"),
    "library": Place("the library steps"),
}

BROCHURES = {
    "hick_dim": Brochure(
        label="brochure",
        phrase="a little brochure with hick-dim letters and a faded cover",
        place_name="the station bench",
        dimness="dim",
    ),
}


ASP_RULES = r"""
% The child flees when the brochure looks dim and scary.
flee(C) :- child(C), sees(C,B), brochure(B), dim_brochure(B), misunderstand(C).

% The misunderstanding clears when the adult explains the brochure.
resolved(C) :- child(C), adult(A), explains(A,B), brochure(B), sees(C,B).
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("child", "child"),
        asp.fact("adult", "adult"),
        asp.fact("brochure", "brochure"),
        asp.fact("dim_brochure", "brochure"),
        asp.fact("sees", "child", "brochure"),
        asp.fact("misunderstand", "child"),
        asp.fact("explains", "adult", "brochure"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show flee/1. #show resolved/1."))
    atoms = set((s.name, tuple(a.number if a.type == 1 else a.string if a.type == 3 else a.name for a in s.arguments)) for s in model)
    expected = {("flee", ("child",)), ("resolved", ("child",))}
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH:", atoms, expected)
    return 1


def tell(params: StoryParams) -> World:
    place = PLACES.get(params.place, PLACES["station"])
    world = World(place)

    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.child_type,
        label=params.child_name,
        meters={"motion": 0.0},
        memes={"curiosity": 1.0, "fear": 0.0, "relief": 0.0, "belonging": 0.0, "misunderstanding": 0.0},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=params.adult_type,
        label=params.adult_name,
        meters={"motion": 0.0},
        memes={"care": 1.0, "worry": 0.0, "relief": 0.0},
    ))
    brochure = world.add(Entity(
        id="brochure",
        type="brochure",
        label="brochure",
        phrase=BROCHURES["hick_dim"].phrase,
        owner=adult.id,
        held_by=adult.id,
        location=place.name,
    ))

    # Act 1: setup
    world.say(
        f"{child.label} sat on {place.name} while {adult.label} waved a small brochure."
    )
    world.say(
        f"It was {brochure.phrase}, and the hick-dim printing made the page look gloomy at first glance."
    )
    child.memes["curiosity"] += 1.0
    child.memes["misunderstanding"] += 1.0

    # Act 2: misunderstanding
    world.para()
    world.say(
        f"{child.label} thought the brochure was telling {child.pronoun('object')} to leave quickly."
    )
    child.meters["motion"] += 1.0
    child.memes["fear"] += 1.0
    child.location = "outside"
    world.say(
        f"So {child.label} started to flee from the bench, with a tight little feeling in {child.pronoun('possessive')} chest."
    )

    # Act 3: warm turn
    world.para()
    adult.held_by = None
    world.say(
        f"{adult.label} hurried after {child.pronoun('object')}, not angry, only gentle."
    )
    world.say(
        f'"Wait," {adult.label} said. "This brochure is an invitation. The hick-dim letters are just old ink."'
    )
    child.memes["fear"] = 0.0
    child.memes["misunderstanding"] = 0.0
    child.memes["relief"] += 1.0
    child.memes["belonging"] += 1.0
    child.location = place.name
    brochure.held_by = adult.id
    world.say(
        f"{child.label} came back, read the brochure again, and saw the warm little plan hidden inside it."
    )
    world.say(
        f"Together they smiled, because what looked strange was really kind."
    )

    world.facts.update(
        child=child,
        adult=adult,
        brochure=brochure,
        place=place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    adult = world.facts["adult"]
    return [
        f"Write a heartwarming story where {child.label} misunderstands a brochure and flees, then comes back after {adult.label} explains it.",
        "Tell a gentle story about a dim-looking brochure, a quick misunderstanding, and a comforting apology.",
        "Write a short child-friendly story using the words brochure, hick-dim, and flee.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    adult = world.facts["adult"]
    brochure = world.facts["brochure"]
    return [
        QAItem(
            question=f"Why did {child.label} flee at first?",
            answer=f"{child.label} thought the brochure was telling {child.pronoun('object')} to leave, because the hick-dim lettering made it look gloomy and serious.",
        ),
        QAItem(
            question=f"What did {adult.label} explain about the brochure?",
            answer=f"{adult.label} explained that the brochure was really an invitation, and the hick-dim look came from old faded ink rather than a bad message.",
        ),
        QAItem(
            question=f"What changed when {child.label} came back?",
            answer=f"{child.label} felt relieved instead of scared, and the misunderstanding faded as {child.label} saw the warm plan hidden in the brochure.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a brochure?",
            answer="A brochure is a small folded paper that gives information or invites someone to something.",
        ),
        QAItem(
            question="What does it mean to flee?",
            answer="To flee means to run away quickly because you feel frightened or unsafe.",
        ),
        QAItem(
            question="What does misunderstanding mean?",
            answer="A misunderstanding is when someone gets the wrong idea about what is happening.",
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming misunderstanding story world about a brochure.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--name")
    ap.add_argument("--adult")
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
        child_name=args.name or rng.choice(["Mina", "Lia", "Nora", "Ivy"]),
        child_type="girl",
        adult_name=args.adult or rng.choice(["Aunt Jo", "Aunt May", "Aunt Belle"]),
        adult_type="aunt",
        place=args.place or rng.choice(list(PLACES.keys())),
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program("#show flee/1. #show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show flee/1. #show resolved/1."))
        print(sorted((s.name, [a.string if a.type == 3 else a.name for a in s.arguments]) for s in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples.append(generate(resolve_params(args, random.Random(base_seed))))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
