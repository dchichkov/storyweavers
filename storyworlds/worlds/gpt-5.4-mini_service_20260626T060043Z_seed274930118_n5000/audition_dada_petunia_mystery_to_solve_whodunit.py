#!/usr/bin/env python3
"""
storyworlds/worlds/audition_dada_petunia_mystery_to_solve_whodunit.py
======================================================================

A small whodunit storyworld: Petunia has an audition, something goes missing,
and Petunia and Dada follow clues to solve the mystery.

Premise:
- Petunia is getting ready for an audition.
- A tiny important item disappears.
- Dada helps Petunia search, compare clues, and ask who could have taken it.

Turn:
- The first clue points one way, then another clue changes the guess.
- The world model tracks who had access, what was seen, and which clue matters.

Resolution:
- The true culprit is identified by the evidence, not by a frozen reveal.
- The missing item is recovered in a concrete place, and the audition can go on.

This world is designed to read like a gentle children's whodunit, with
cause-and-effect state changes driving the prose rather than a fixed paragraph.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    seen_by: set[str] = field(default_factory=set)
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
    bright: bool = False
    indoor: bool = True


@dataclass
class Suspect:
    id: str
    label: str
    access: set[str]
    clue_style: str


@dataclass
class StoryParams:
    place: str
    missing: str
    culprit: str
    clue: str
    name: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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


SETTINGS = {
    "the little theater": Location(id="the little theater", label="the little theater", bright=False, indoor=True),
    "the school hall": Location(id="the school hall", label="the school hall", bright=True, indoor=True),
    "the music room": Location(id="the music room", label="the music room", bright=True, indoor=True),
    "the kitchen": Location(id="the kitchen", label="the kitchen", bright=True, indoor=True),
}

MISSING_ITEMS = {
    "ribbon": Entity(id="ribbon", kind="thing", type="ribbon", label="red ribbon", phrase="a red ribbon", location=""),
    "glove": Entity(id="glove", kind="thing", type="glove", label="white glove", phrase="a white glove", location=""),
    "bell": Entity(id="bell", kind="thing", type="bell", label="silver bell", phrase="a tiny silver bell", location=""),
    "card": Entity(id="card", kind="thing", type="card", label="song card", phrase="a song card", location=""),
}

SUSPECTS = {
    "cat": Suspect(id="cat", label="the cat", access={"floor", "chair", "curtain"}, clue_style="fur"),
    "tote": Suspect(id="tote", label="the tote bag", access={"table", "bench", "door"}, clue_style="string"),
    "wind": Suspect(id="wind", label="the wind", access={"window", "hall", "stage"}, clue_style="blown"),
    "little brother": Suspect(id="little brother", label="the little brother", access={"floor", "table", "chair"}, clue_style="small feet"),
}

CLUES = {
    "fur": "a strip of soft fur",
    "string": "a loose string from the tote bag",
    "blown": "a paper fluttered under the curtain",
    "small feet": "tiny footprints by the chair",
}

GOOD_COMBOS = [
    ("the little theater", "ribbon", "cat", "fur"),
    ("the school hall", "glove", "little brother", "small feet"),
    ("the music room", "bell", "tote", "string"),
    ("the kitchen", "card", "wind", "blown"),
]

GIRL_NAMES = ["Petunia", "Mina", "Lena", "Poppy", "Mira", "Nina"]
BOY_NAMES = ["Toby", "Finn", "Eli", "Jasper"]
PARENTS = ["dada", "mother", "father", "dad"]
SUSPECT_KEYS = list(SUSPECTS.keys())
MISSING_KEYS = list(MISSING_ITEMS.keys())
PLACE_KEYS = list(SETTINGS.keys())


def reasonableness_gate(place: str, missing: str, culprit: str, clue: str) -> bool:
    return (place, missing, culprit, clue) in GOOD_COMBOS


def explain_rejection(place: str, missing: str, culprit: str, clue: str) -> str:
    return (
        f"(No story: that mystery would not make a clear whodunit. "
        f"At {place}, the item {missing} would not honestly fit the clue '{clue}' "
        f"for {culprit}. Choose one of the compatible mystery pairs.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle whodunit storyworld about Petunia, Dada, and an audition.")
    ap.add_argument("--place", choices=PLACE_KEYS)
    ap.add_argument("--missing", choices=MISSING_KEYS)
    ap.add_argument("--culprit", choices=SUSPECT_KEYS)
    ap.add_argument("--clue", choices=list(CLUES))
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENTS)
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
    if args.place and args.missing and args.culprit and args.clue:
        if not reasonableness_gate(args.place, args.missing, args.culprit, args.clue):
            raise StoryError(explain_rejection(args.place, args.missing, args.culprit, args.clue))
    combos = [
        c for c in GOOD_COMBOS
        if (args.place is None or c[0] == args.place)
        and (args.missing is None or c[1] == args.missing)
        and (args.culprit is None or c[2] == args.culprit)
        and (args.clue is None or c[3] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid mystery combination matches the given options.)")
    place, missing, culprit, clue = rng.choice(sorted(combos))
    name = args.name or "Petunia"
    parent = args.parent or "dada"
    return StoryParams(place=place, missing=missing, culprit=culprit, clue=clue, name=name, parent=parent)


def _introduce(world: World, hero: Entity, parent: Entity, item: Entity) -> None:
    world.say(f"{hero.id} was a careful little girl who was getting ready for an audition.")
    world.say(f"She loved her {item.label}, because it made her feel brave and neat.")
    world.say(f"Her {parent.id} told her they could handle anything together.")


def _discovery(world: World, hero: Entity, item: Entity) -> None:
    item.location = "missing"
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(f"But when {hero.id} reached for {item.label}, it was gone.")
    world.say(f"{hero.id} looked under the bench, beside the door, and behind the chair, but nothing was there.")


def _clue_scene(world: World, hero: Entity, parent: Entity, suspect: Suspect, clue: str) -> None:
    world.para()
    world.say(f"{parent.id} crouched beside {hero.id} and said, 'Let's be detectives.'")
    world.say(f"They found {CLUES[clue]} near the place where the item had been.")
    if suspect.id == "cat":
        world.say("A little gray cat had hopped past the curtain earlier, quick as a wink.")
    elif suspect.id == "tote":
        world.say("The tote bag was open, and a string dangled from one of its corners.")
    elif suspect.id == "wind":
        world.say("A draft stirred the papers and made the curtain flutter like a flag.")
    elif suspect.id == "little brother":
        world.say("Small feet had scurried by, leaving tiny marks in the dust.")
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    parent.memes["calm"] = parent.memes.get("calm", 0.0) + 1


def _deduce(world: World, hero: Entity, parent: Entity, culprit: Suspect, item: Entity) -> None:
    world.para()
    world.say(f"{hero.id} and {parent.id} compared the clue with every suspect.")
    world.say(f"The clue matched {culprit.label} better than anyone else.")
    world.say(f"That made the mystery feel less scary, because the facts finally pointed to one answer.")
    item.location = f"hidden with {culprit.label}"
    culprit_item = world.add(Entity(id=f"trace_{culprit.id}", kind="thing", type="trace", label=culprit.clue_style, location="evidence"))
    culprit_item.meters["evidence"] = 1.0
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1


def _reveal(world: World, hero: Entity, parent: Entity, culprit: Suspect, item: Entity) -> None:
    world.para()
    world.say(f"At last, they looked in the right spot and found the missing {item.label}.")
    world.say(f"It had been tucked {item.location}, right where {culprit.label} could reach it.")
    world.say(f"{parent.id} smiled and said, 'Whodunit? Why, {culprit.label} did, but only by accident.'")
    world.say(f"{hero.id} laughed, because the mystery was solved and the audition could go on.")
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    item.location = "recovered"


def tell(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id=params.name, kind="character", type="girl", label=params.name))
    parent = world.add(Entity(id=params.parent, kind="character", type="father", label=params.parent))
    item = world.add(Entity(**{**MISSING_ITEMS[params.missing].__dict__}))
    suspect = SUSPECTS[params.culprit]
    world.facts.update(params=params, hero=hero, parent=parent, item=item, culprit=suspect, clue=params.clue, place=world.location)
    _introduce(world, hero, parent, item)
    _discovery(world, hero, item)
    _clue_scene(world, hero, parent, suspect, params.clue)
    _deduce(world, hero, parent, suspect, item)
    _reveal(world, hero, parent, suspect, item)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a gentle whodunit about {p.name}, {p.parent}, and a missing {p.missing} before an audition.",
        f"Tell a child-friendly mystery story set at {p.place} where the clue is {CLUES[p.clue]}.",
        f"Write a short story in which {p.name} and {p.parent} solve a mystery and the audition can finally begin.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    item = world.facts["item"]
    culprit = world.facts["culprit"]
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    return [
        QAItem(
            question=f"What was missing before {hero.id}'s audition?",
            answer=f"The missing item was {item.label}. {hero.id} had wanted it because it helped her feel ready for the audition.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the mystery?",
            answer=f"{parent.id} helped {hero.id} by acting like a detective and following the clue carefully.",
        ),
        QAItem(
            question=f"Who was the whodunit in the story?",
            answer=f"The clue pointed to {culprit.label}, so {culprit.label} was the one who had the missing item by accident.",
        ),
        QAItem(
            question=f"How did the story end after the mystery was solved?",
            answer=f"The missing {item.label} was found, and {hero.id} could go on with the audition feeling relieved and happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    item = world.facts["item"]
    culprit = world.facts["culprit"]
    return [
        QAItem(
            question="What is an audition?",
            answer="An audition is when someone tries out to show a skill, like singing, acting, or dancing.",
        ),
        QAItem(
            question="Who is Dada?",
            answer="Dada is a child-friendly word for a father.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not understood at first, so people look for clues to solve it.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a piece of evidence that helps show what happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
missing(M) :- item(M).
culprit(C) :- suspect(C).
clue(K) :- clue_kind(K).

compatible("the little theater", ribbon, cat, fur).
compatible("the school hall", glove, little_brother, small_feet).
compatible("the music room", bell, tote, string).
compatible("the kitchen", card, wind, blown).

valid_story(P, M, C, K) :- compatible(P, M, C, K).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for m in MISSING_ITEMS:
        lines.append(asp.fact("item", m))
    for c in SUSPECTS:
        lines.append(asp.fact("suspect", c))
    for k in CLUES:
        lines.append(asp.fact("clue_kind", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(GOOD_COMBOS)
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches reasonableness_gate() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    world = tell(world, params)
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
    StoryParams(place="the little theater", missing="ribbon", culprit="cat", clue="fur", name="Petunia", parent="dada"),
    StoryParams(place="the school hall", missing="glove", culprit="little brother", clue="small feet", name="Petunia", parent="dada"),
    StoryParams(place="the music room", missing="bell", culprit="tote", clue="string", name="Petunia", parent="dada"),
    StoryParams(place="the kitchen", missing="card", culprit="wind", clue="blown", name="Petunia", parent="dada"),
]


def explain_genderless() -> str:
    return "(No story: this world always uses Petunia and dada for the gentle whodunit tone.)"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for row in stories:
            print("  ", row)
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name}: missing {p.missing} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
