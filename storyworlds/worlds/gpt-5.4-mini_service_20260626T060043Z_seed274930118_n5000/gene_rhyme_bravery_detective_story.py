#!/usr/bin/env python3
"""
A small storyworld: a detective tale about a gene, with rhyme and bravery.

Premise:
- A young detective follows clues around a quiet neighborhood.
- The clue trail is shaped by rhyme: notes, scraps, and repeated sounds.
- Bravery matters because the final clue leads to a place that feels a little scary.
- The resolution reveals that the gene was not a person but a label on a sample,
  and the detective's brave, rhyming method solves the case.

This world is deliberately tiny and constraint-checked: the story only forms
when the clue trail, the setting, and the brave action fit together.
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
# Entities / World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # detective, thing, clue, place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    found_by: Optional[str] = None
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
class Place:
    id: str
    label: str
    mood: str
    shadowy: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    rhyme_word: str
    points_to: str
    risk: str = ""
    found_at: str = ""


@dataclass
class Case:
    id: str
    label: str
    suspect_hint: str
    prize: str
    final_place: str
    requires_bravery: bool = True


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []
        self.mystery_solved = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.mystery_solved = self.mystery_solved
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "alley": Place(id="alley", label="the alley", mood="narrow and quiet", shadowy=True, affords={"search", "listen"}),
    "library": Place(id="library", label="the library", mood="still and bright", affords={"search", "listen"}),
    "lab": Place(id="lab", label="the small lab", mood="clean and careful", affords={"search", "analyze"}),
    "garden": Place(id="garden", label="the garden", mood="soft and leafy", affords={"search", "listen"}),
}

CASE_FILES = {
    "gene": Case(
        id="gene",
        label="the gene case",
        suspect_hint="a coded label",
        prize="the missing sample tag",
        final_place="lab",
    )
}

CLUES = {
    "note": Clue(
        id="note",
        label="a torn note",
        phrase="a torn note that said, 'Brave and bright, find the right rhyme tonight.'",
        rhyme_word="bright",
        points_to="library",
        risk="mysterious",
        found_at="alley",
    ),
    "chalk": Clue(
        id="chalk",
        label="a bit of chalk",
        phrase="a chalk mark shaped like a looping line",
        rhyme_word="line",
        points_to="garden",
        risk="faint",
        found_at="library",
    ),
    "tag": Clue(
        id="tag",
        label="a sample tag",
        phrase="a small sample tag with the word 'gene' on it",
        rhyme_word="gene",
        points_to="lab",
        risk="important",
        found_at="garden",
    ),
}

GIRL_NAMES = ["Mina", "Tess", "Luna", "Ivy", "Nora"]
BOY_NAMES = ["Finn", "Miles", "Theo", "Owen", "Eli"]
TRAITS = ["curious", "careful", "brave", "quick", "steady"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    case: str
    detective_name: str
    detective_gender: str
    parent_or_partner: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def rhyme_step(phrase: str, rhyme_word: str) -> str:
    return f"{phrase} The clue seemed to rhyme with {rhyme_word}."


def can_start(place: Place, case: Case) -> bool:
    return place.id in {"alley", "library"} and case.id == "gene"


def reasonableness_gate(place: Place, case: Case) -> bool:
    return can_start(place, case)


def _narrate_found(world: World, detective: Entity, clue: Clue) -> None:
    if clue.id in world.fired:
        return
    world.fired.add((clue.id, "found"))
    world.say(
        f"{detective.id} found {clue.label} in {world.get(clue.found_at).label}. "
        f"{rhyme_step(clue.phrase, clue.rhyme_word)}"
    )


def _narrate_follow(world: World, detective: Entity, clue: Clue) -> None:
    world.say(
        f"{detective.id} followed the hint toward {world.get(clue.points_to).label}, "
        f"because the rhyme kept the clues in a straight line."
    )


def _narrate_brave_turn(world: World, detective: Entity, case: Case) -> None:
    detective.memes["bravery"] = detective.memes.get("bravery", 0) + 1
    world.say(
        f"The last stop was {world.get(case.final_place).label}, which felt shadowy and a little strange. "
        f"But {detective.id} stood tall and kept going anyway."
    )


def _narrate_solve(world: World, detective: Entity, case: Case) -> None:
    world.mystery_solved = True
    world.say(
        f"Inside, {detective.id} found {case.prize}. It was not a person at all, but a tiny label on a sample. "
        f"The word gene was the real clue, and the brave rhyme had led {detective.pronoun('object')} right there."
    )
    world.say(
        f"{detective.id} smiled, tucked the case away, and knew that brave feet and careful rhyme had solved the mystery."
    )


def tell_world(world: World, detective_name: str, gender: str, trait: str, partner: str, case_id: str) -> World:
    case = CASE_FILES[case_id]
    detective = world.add(Entity(
        id=detective_name,
        kind="detective",
        type=gender,
        label=detective_name,
        owner=partner,
        meters={"courage": 0.0},
        memes={"bravery": 0.0, "curiosity": 1.0},
    ))
    world.add(Entity(id="partner", kind="thing", type=partner, label=f"the {partner}"))
    for p in PLACES.values():
        world.add(Entity(id=p.id, kind="place", type="place", label=p.label, phrase=p.mood, location=p.id))

    # Act 1
    world.say(
        f"{detective.id} was a {trait} young detective who liked to solve small mysteries."
    )
    world.say(
        f"{detective.id} also loved a good rhyme, because rhyming words made clues easier to remember."
    )
    world.say(
        f"One day, a case came in about {case.prize} and a strange word: gene."
    )
    world.para()

    # Act 2
    if not reasonableness_gate(world.place, case):
        raise StoryError("This setting does not support a believable gene mystery.")
    clue1 = CLUES["note"]
    clue2 = CLUES["chalk"]
    clue3 = CLUES["tag"]

    _narrate_found(world, detective, clue1)
    _narrate_follow(world, detective, clue1)
    world.para()
    _narrate_found(world, detective, clue2)
    _narrate_follow(world, detective, clue2)
    world.para()

    # turn: bravery in the shadowy final place
    world.place = PLACES[case.final_place]
    _narrate_brave_turn(world, detective, case)
    _narrate_found(world, detective, clue3)
    world.say(
        f"The tag had one tiny word on it: gene. That was the answer, and it matched the earlier rhyme."
    )
    _narrate_solve(world, detective, case)
    return world


# ---------------------------------------------------------------------------
# Story QA / prompts
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short detective story for a young child about a gene clue, using rhyme and bravery.',
        f"Tell a simple mystery about {f['detective_name']} following a rhyming trail to {f['case_prize']}.",
        "Write a child-friendly detective tale where the final clue is a gene label and the hero is brave enough to solve it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective_name"]
    case_prize = f["case_prize"]
    final_place = f["final_place"]
    return [
        QAItem(
            question=f"Who solved the mystery in the story?",
            answer=f"{detective} solved the mystery by following the clues with careful rhyme and bravery."
        ),
        QAItem(
            question="What was the final clue?",
            answer="The final clue was a tiny sample tag with the word gene on it."
        ),
        QAItem(
            question=f"Why did {detective} keep going into the shadowy place?",
            answer=f"{detective} was brave, so the scary feeling of the final place did not stop the search."
        ),
        QAItem(
            question=f"What was found in the end at {world.get(final_place).label}?",
            answer=f"{case_prize} was found, and it turned out to be a label on a sample rather than a person."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like bright and night."
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when it feels a little scary."
        ),
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues to solve a mystery."
        ),
        QAItem(
            question="What is a gene?",
            answer="A gene is a tiny part of living things that carries instructions for how bodies grow and work."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(alley). place(library). place(lab). place(garden).
shadowy(alley).

case(gene).
needs_bravery(gene).
final_place(gene, lab).

affords(alley, search). affords(alley, listen).
affords(library, search). affords(library, listen).
affords(lab, search). affords(lab, analyze).
affords(garden, search). affords(garden, listen).

clue(note). clue(chalk). clue(tag).

rhyme_clue(note).
rhyme_clue(chalk).
gene_clue(tag).

safe_start(P, C) :- case(C), place(P), (P = alley; P = library).
good_story(P, C) :- safe_start(P, C), final_place(C, lab), needs_bravery(C).

#show good_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.shadowy:
            lines.append(asp.fact("shadowy", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in CASE_FILES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("final_place", cid, c.final_place))
        if c.requires_bravery:
            lines.append(asp.fact("needs_bravery", cid))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        if clue_id in {"note", "chalk"}:
            lines.append(asp.fact("rhyme_clue", clue_id))
        if clue_id == "tag":
            lines.append(asp.fact("gene_clue", clue_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/2."))
    asp_set = set(asp.atoms(model, "good_story"))
    py_set = {(p, c) for p in PLACES for c in CASE_FILES if reasonableness_gate(PLACES[p], CASE_FILES[c])}
    if asp_set == py_set:
        print(f"OK: ASP matches Python reasonableness gate ({len(py_set)} pairs).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    if asp_set - py_set:
        print("  only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in Python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Generation / params / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld with gene, rhyme, and bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--case", choices=CASE_FILES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--partner", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    case = args.case or "gene"
    if case not in CASE_FILES:
        raise StoryError("Unknown case.")
    if place not in {"alley", "library"}:
        raise StoryError("This detective story needs a start in the alley or the library.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    partner = args.partner or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, case=case, detective_name=name, detective_gender=gender, parent_or_partner=partner, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    world = tell_world(world, params.detective_name, params.detective_gender, params.trait, params.parent_or_partner, params.case)
    world.facts = {
        "detective_name": params.detective_name,
        "case_prize": CASE_FILES[params.case].prize,
        "final_place": CASE_FILES[params.case].final_place,
        "case": CASE_FILES[params.case],
        "params": params,
    }
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for eid, ent in world.entities.items():
        bits = []
        if ent.label:
            bits.append(f"label={ent.label}")
        if ent.location:
            bits.append(f"location={ent.location}")
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"  {eid}: {ent.kind}/{ent.type} {' '.join(bits)}")
    lines.append(f"  solved={world.mystery_solved}")
    return "\n".join(lines)


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
    StoryParams(place="alley", case="gene", detective_name="Mina", detective_gender="girl", parent_or_partner="mother", trait="curious"),
    StoryParams(place="library", case="gene", detective_name="Theo", detective_gender="boy", parent_or_partner="father", trait="careful"),
]


def asp_check() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show good_story/2."))
    return sorted(set(asp.atoms(model, "good_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_check()
        print(f"{len(pairs)} compatible story starts:")
        for p, c in pairs:
            print(f"  {p} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = f"### variant {i+1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
