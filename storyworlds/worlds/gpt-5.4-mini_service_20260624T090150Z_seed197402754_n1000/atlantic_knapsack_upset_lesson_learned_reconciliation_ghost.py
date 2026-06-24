#!/usr/bin/env python3
"""
A small storyworld for a child-friendly ghost story with:
- atlantic
- knapsack
- upset
- lesson learned
- reconciliation

The world models a shy ghost, a child, a misplaced knapsack, and a
stormy Atlantic night where feelings shift from upset to understood.
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    transparent: bool = False
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
    mood: str
    water: bool = False
    wind: bool = False


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    ghost_name: str
    seed: Optional[int] = None


PLACES = {
    "shore": Place(id="shore", label="the Atlantic shore", mood="salt-bright", water=True, wind=True),
    "pier": Place(id="pier", label="the old pier", mood="creaky", water=True, wind=True),
    "cove": Place(id="cove", label="the little cove", mood="quiet", water=True, wind=True),
}

HERO_NAMES = ["Mina", "Theo", "Luna", "Nico", "Iris", "Arlo"]
GHOST_NAMES = ["Murmur", "Pearl", "Cloud", "Tide", "Moss", "Wisp"]


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


def setup_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        location=world.place.id,
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label=params.ghost_name,
        transparent=True,
        location=world.place.id,
    ))
    knapsack = world.add(Entity(
        id="knapsack",
        kind="thing",
        type="knapsack",
        label="knapsack",
        phrase="a small knapsack with a blue strap",
        owner=hero.id,
        carried_by=hero.id,
        location=hero.id,
        meters={"weight": 1.0},
    ))
    shell = world.add(Entity(
        id="shell",
        kind="thing",
        type="shell",
        label="shell charm",
        phrase="a tiny shell charm",
        owner=ghost.id,
        location=world.place.id,
    ))
    world.facts.update(hero=hero, ghost=ghost, knapsack=knapsack, shell=shell)
    return world


def start_story(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    ghost: Entity = world.facts["ghost"]  # type: ignore[assignment]
    knapsack: Entity = world.facts["knapsack"]  # type: ignore[assignment]

    world.say(
        f"{hero.label} had come to {world.place.label} on a windy evening. "
        f"The Atlantic air tasted of salt and rain."
    )
    world.say(
        f"{hero.label} carried {hero.pronoun('possessive')} knapsack close, because it held "
        f"{knapsack.phrase} and a folded note."
    )
    world.say(
        f"Near the dark water, {ghost.label} drifted out like a puff of mist. "
        f"{ghost.label} looked quiet, but {ghost.label} was upset."
    )


def conflict(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    ghost: Entity = world.facts["ghost"]  # type: ignore[assignment]
    knapsack: Entity = world.facts["knapsack"]  # type: ignore[assignment]

    ghost.memes["upset"] = 1.0
    hero.memes["startled"] = 1.0
    world.say(
        f"{ghost.label} said the knapsack had been left too close to the tide line, "
        f"and now the shell charm inside felt lonely."
    )
    world.say(
        f"{hero.label} frowned. {hero.label} had not meant to be careless, "
        f"but the words made {hero.pronoun('object')} feel small."
    )
    if knapsack.location != hero.id:
        raise StoryError("The knapsack must begin with the child so the story can move it safely.")
    hero.memes["upset"] = 1.0


def lesson_learned(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    ghost: Entity = world.facts["ghost"]  # type: ignore[assignment]
    knapsack: Entity = world.facts["knapsack"]  # type: ignore[assignment]
    shell: Entity = world.facts["shell"]  # type: ignore[assignment]

    world.para()
    world.say(
        f"{hero.label} opened the knapsack and saw that the note was wet at one corner. "
        f"That was enough to teach a gentle lesson: things near the Atlantic need careful hands."
    )
    world.say(
        f"{hero.label} lifted the shell charm free, dried the note under {hero.pronoun('possessive')} sleeve, "
        f"and moved the knapsack back from the water."
    )
    knapsack.location = "safe_sand"
    shell.location = hero.id
    hero.memes["careful"] = 1.0
    hero.memes["upset"] = 0.0
    hero.memes["learned"] = 1.0
    ghost.memes["upset"] = 0.5
    world.say(
        f"{ghost.label} watched the careful work and softened. The little shell charm was safe again, "
        f"and the night felt less sharp."
    )


def reconciliation(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    ghost: Entity = world.facts["ghost"]  # type: ignore[assignment]
    shell: Entity = world.facts["shell"]  # type: ignore[assignment]

    world.para()
    ghost.memes["upset"] = 0.0
    ghost.memes["friendship"] = 1.0
    hero.memes["reconciled"] = 1.0
    world.say(
        f"{hero.label} held out the dry shell charm. {ghost.label} smiled, and the mist around "
        f"{ghost.label} turned bright and soft."
    )
    world.say(
        f"Together they tucked the charm into the knapsack's front pocket, where it would not slip toward "
        f"the tide again. The two of them stood side by side, listening to the Atlantic hush."
    )
    world.say(
        f"In the end, {hero.label} and {ghost.label} were no longer upset. They had learned to be careful, "
        f"and they had made peace under the windy sky."
    )
    world.facts["ending_shell"] = shell.location


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    start_story(world)
    conflict(world)
    lesson_learned(world)
    reconciliation(world)
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    ghost: Entity = world.facts["ghost"]  # type: ignore[assignment]
    return [
        "Write a short ghost story for a young child about a knapsack and the Atlantic shore.",
        f"Tell a gentle story where {hero.label} and {ghost.label} begin upset, learn a lesson, and make up.",
        "Write a simple seaside ghost story that ends with reconciliation and a cared-for knapsack.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    ghost: Entity = world.facts["ghost"]  # type: ignore[assignment]
    knapsack: Entity = world.facts["knapsack"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who carried the knapsack at the Atlantic shore?",
            answer=f"{hero.label} carried the knapsack at the Atlantic shore.",
        ),
        QAItem(
            question=f"Why was {ghost.label} upset at first?",
            answer=(
                f"{ghost.label} was upset because the knapsack had been left too close to the tide line, "
                f"and the shell charm inside seemed at risk."
            ),
        ),
        QAItem(
            question="What lesson did the child learn?",
            answer=(
                f"{hero.label} learned to keep careful track of the knapsack near the water and to move it "
                f"back from the Atlantic shore."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"The story ended with reconciliation: {hero.label} and {ghost.label} were calm, and the "
                f"shell charm was tucked safely into the knapsack."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is the Atlantic?",
            answer=(
                "The Atlantic is a very large ocean. It has salt water, waves, wind, and tides that move "
                "the water in and out."
            ),
        ),
        QAItem(
            question="What is a knapsack?",
            answer=(
                "A knapsack is a bag that people carry on their back or by a strap. It can hold small things "
                "like notes, snacks, or toys."
            ),
        ),
        QAItem(
            question="What does upset mean?",
            answer=(
                "Upset means feeling unhappy, worried, or bothered. A person who is upset may need kindness "
                "and a calm talk."
            ),
        ),
        QAItem(
            question="What is reconciliation?",
            answer=(
                "Reconciliation means making peace after a disagreement. It happens when people talk kindly "
                "and feel friendly again."
            ),
        ),
    ]


@dataclass
class ASPRegistry:
    places: dict[str, Place]
    moods: dict[str, str]


ASP_RULES = r"""
place(shore).
place(pier).
place(cove).

atlantic(shore) :- place(shore).
atlantic(pier) :- place(pier).
atlantic(cove) :- place(cove).

upset(hero) :- seeks(hero, knapsack), lost(hero, trust).
lesson_learned(hero) :- upset(hero), careful(hero).
reconciliation(hero, ghost) :- lesson_learned(hero), soften(ghost), shared_peace(hero, ghost).

safe(knapsack) :- moved_from_tide(knapsack), carried(hero, knapsack).
show_story :- atlantic(_), upset(hero), lesson_learned(hero), reconciliation(hero, ghost).
#show atlantic/1.
#show upset/1.
#show lesson_learned/1.
#show reconciliation/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("atlantic", pid))
    lines.append(asp.fact("seeks", "hero", "knapsack"))
    lines.append(asp.fact("lost", "hero", "trust"))
    lines.append(asp.fact("careful", "hero"))
    lines.append(asp.fact("soften", "ghost"))
    lines.append(asp.fact("shared_peace", "hero", "ghost"))
    lines.append(asp.fact("moved_from_tide", "knapsack"))
    lines.append(asp.fact("carried", "hero", "knapsack"))
    return "\n".join(lines)


def asp_program(show: str = "#show atlantic/1.\n#show upset/1.\n#show lesson_learned/1.\n#show reconciliation/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = set()
    for sym in model:
        if sym.name in {"atlantic", "upset", "lesson_learned", "reconciliation"}:
            atoms.add((sym.name, tuple(a.name if hasattr(a, "name") else getattr(a, "string", getattr(a, "number", None)) for a in sym.arguments)))
    expected = {
        ("atlantic", ("shore",)),
        ("atlantic", ("pier",)),
        ("atlantic", ("cove",)),
        ("upset", ("hero",)),
        ("lesson_learned", ("hero",)),
        ("reconciliation", ("hero", "ghost")),
    }
    if atoms == expected:
        print("OK: ASP twin matches the Python story logic.")
        return 0
    print("MISMATCH between ASP and Python story logic.")
    print("Expected:", sorted(expected))
    print("Got:", sorted(atoms))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.transparent:
            bits.append("transparent=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  place={world.place.id} mood={world.place.mood}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World knowledge Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world: Atlantic, knapsack, upset, lesson learned, reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--ghost-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    place = args.place or rng.choice(list(PLACES))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    return StoryParams(place=place, hero_name=hero_name, hero_type=gender, ghost_name=ghost_name, seed=args.seed)


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("\n".join(sorted(f"{sym.name}{tuple(a.name if hasattr(a, 'name') else getattr(a, 'string', getattr(a, 'number', None)) for a in sym.arguments)}" for sym in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place in PLACES:
            params = StoryParams(place=place, hero_name=HERO_NAMES[0], hero_type="girl", ghost_name=GHOST_NAMES[0], seed=base_seed)
            samples.append(generate(params))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
