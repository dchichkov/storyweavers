#!/usr/bin/env python3
"""
Standalone storyworld: Galley Transformation Detective Story.

A small detective domain set in and around a ship's galley, where clues, hidden
motives, and a surprising transformation drive the plot. The story stays child-
facing and classical: setup, suspicion, investigation, reveal, and resolution.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
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
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Location:
    id: str
    label: str
    indoors: bool = False


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    motive: str
    clue: str
    transforms_to: str
    transformed_clue: str
    location: str


@dataclass
class StoryParams:
    location: str
    suspect: str
    name: str
    gender: str
    detective: str
    seed: Optional[int] = None


class World:
    def __init__(self, location: Location):
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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

    def copy(self) -> "World":
        w = World(self.location)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


LOCATIONS = {
    "galley": Location(id="galley", label="the galley", indoors=True),
    "dock": Location(id="dock", label="the dock", indoors=False),
    "harbor": Location(id="harbor", label="the harbor", indoors=False),
}

SUSPECTS = {
    "cat": Suspect(
        id="cat",
        label="the ship's cat",
        type="cat",
        motive="wanted the fish tart",
        clue="a tiny paw print on the flour sack",
        transforms_to="mouse",
        transformed_clue="a much smaller paw print by the sugar bowl",
        location="galley",
    ),
    "cook": Suspect(
        id="cook",
        label="the cook",
        type="person",
        motive="wanted to hide the missing spoon",
        clue="a floury sleeve near the sink",
        transforms_to="helper",
        transformed_clue="a neat apron ribbon tied in a different knot",
        location="galley",
    ),
    "seagull": Suspect(
        id="seagull",
        label="a seagull",
        type="bird",
        motive="wanted shiny crumbs",
        clue="a feather stuck to the window latch",
        transforms_to="sparrow",
        transformed_clue="a smaller feather near the open hatch",
        location="dock",
    ),
}

DETECTIVE_NAMES = ["Mina", "Jules", "Toby", "Nora", "Pip", "Ada", "Rae", "Theo"]


def valid_combos() -> list[tuple[str, str]]:
    return [(loc_id, sid) for loc_id, loc in LOCATIONS.items() for sid, s in SUSPECTS.items() if s.location == loc_id]


def explain_rejection(location: Location, suspect: Suspect) -> str:
    return (
        f"(No story: {suspect.label} does not belong at {location.label} in this little case. "
        f"Try a suspect that fits the chosen place.)"
    )


def reasonableness_gate(location: Location, suspect: Suspect) -> None:
    if suspect.location != location.id:
        raise StoryError(explain_rejection(location, suspect))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with a galley and a transformation mystery.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--detective", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.location:
        combos = [c for c in combos if c[0] == args.location]
    if args.suspect:
        combos = [c for c in combos if c[1] == args.suspect]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    location_id, suspect_id = rng.choice(sorted(combos))
    suspect = SUSPECTS[suspect_id]
    name = args.name or rng.choice(DETECTIVE_NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    detective = args.detective or gender
    return StoryParams(location=location_id, suspect=suspect_id, name=name, gender=gender, detective=detective)


def _setup(world: World, hero: Entity, suspect: Suspect) -> None:
    world.say(f"{hero.id} was a little detective who loved quiet puzzles and careful clues.")
    world.say(f"One day, {hero.pronoun('possessive')} case led {hero.id} into {world.location.label}, where something had gone missing.")
    world.say(f"The clue was strange: {suspect.clue}.")


def _suspicion(world: World, hero: Entity, suspect: Suspect) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(f"{hero.id} looked around and whispered, 'This is a curious one.'")
    world.say(f"Someone had hidden the truth behind a small, busy mess in the galley.")


def _investigate(world: World, hero: Entity, suspect: Suspect) -> None:
    hero.meters["observations"] = hero.meters.get("observations", 0) + 1
    if suspect.id == "cat":
        world.say(f"{hero.id} noticed that the paw print was too tiny for a person.")
        world.say(f"Then {hero.id} saw a bowl tipped just enough to point at the sugar bowl.")
    elif suspect.id == "cook":
        world.say(f"{hero.id} noticed the floury sleeve and the careful way the sink had been wiped.")
        world.say(f"That meant the cook was hiding something, but not to be mean.")
    else:
        world.say(f"{hero.id} followed the feather and found crumbs near the hatch.")
        world.say(f"The trail led from the galley to the dock and back again.")


def _transformation(world: World, hero: Entity, suspect: Suspect) -> None:
    world.say(f"At the end of the trail, the clue changed.")
    world.say(f"What looked like {suspect.clue} turned into {suspect.transformed_clue}.")
    world.say(f"That was the transformation: the same mystery, but now seen in a new shape.")
    world.facts["transformed"] = True


def _reveal(world: World, hero: Entity, suspect: Suspect) -> None:
    world.say(f"{hero.id} put the clues together and smiled.")
    world.say(f"The answer was {suspect.label}, because {suspect.motive}.")
    world.say(f"It was not a scary trick after all, just a puzzle that changed when looked at closely.")


def _resolution(world: World, hero: Entity, suspect: Suspect) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    world.say(f"{hero.id} returned the missing thing, and the galley felt peaceful again.")
    world.say(f"At the end, {hero.id} carried the solved case home in {hero.pronoun('possessive')} notebook.")


def generate_story_world(params: StoryParams) -> World:
    location = LOCATIONS[params.location]
    suspect = SUSPECTS[params.suspect]
    reasonableness_gate(location, suspect)
    world = World(location)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    world.facts.update(hero=hero, suspect=suspect, location=location, params=params)
    _setup(world, hero, suspect)
    world.para()
    _suspicion(world, hero, suspect)
    _investigate(world, hero, suspect)
    world.para()
    _transformation(world, hero, suspect)
    _reveal(world, hero, suspect)
    _resolution(world, hero, suspect)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    suspect = f["suspect"]
    loc = f["location"]
    return [
        f"Write a short detective story for a child set in {loc.label} with a clear clue and a gentle twist.",
        f"Tell a mystery about {hero.id} in {loc.label} where {suspect.label} seems suspicious, but the clue transforms into a new answer.",
        f"Write a child-friendly detective story that includes a galley, a clue, and a surprising transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    suspect = f["suspect"]
    loc = f["location"]
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {hero.id}, who carefully looked for clues in {loc.label}.",
        ),
        QAItem(
            question=f"Where did the mystery happen?",
            answer=f"It happened in {loc.label}, a place where the clue was hiding in a busy little scene.",
        ),
        QAItem(
            question=f"What was the main clue before it changed?",
            answer=f"The main clue was {suspect.clue}. That clue helped {hero.id} start solving the case.",
        ),
        QAItem(
            question=f"What happened at the transformation moment?",
            answer=f"The clue changed into {suspect.transformed_clue}, which showed the mystery in a new way.",
        ),
        QAItem(
            question=f"Who or what turned out to be the answer?",
            answer=f"The answer was {suspect.label}, because {suspect.motive}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a galley?",
            answer="A galley is a kitchen area on a ship, where food is cooked and tools are kept tidy.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is when something changes into a new form or looks different than before.",
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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
location(galley).
location(dock).
location(harbor).

suspect(cat).
suspect(cook).
suspect(seagull).

at(cat, galley).
at(cook, galley).
at(seagull, dock).

valid(L, S) :- location(L), suspect(S), at(S, L).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for loc_id in LOCATIONS:
        lines.append(asp.fact("location", loc_id))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("at", sid, s.location))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
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


CURATED = [
    StoryParams(location="galley", suspect="cat", name="Mina", gender="girl", detective="girl"),
    StoryParams(location="galley", suspect="cook", name="Jules", gender="boy", detective="boy"),
    StoryParams(location="dock", suspect="seagull", name="Nora", gender="girl", detective="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (location, suspect) combos:\n")
        for loc, sus in triples:
            print(f"  {loc:8} {sus}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.suspect} in {p.location}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
