#!/usr/bin/env python3
"""
storyworlds/worlds/expose_bull_s_couple_suspense_repetition_detective.py
======================================================================

A small detective-story world about a careful investigator, a suspicious
couple, and a bull's missing clue. The premise is built from a tiny story:
the detective notices repeated strange signs, follows them through a tense
afternoon, and finally exposes the truth about the couple.

The world supports a few tightly constrained variants:
- a bull's bell or ribbon is missing
- a couple is secretly involved
- repeated clues create suspense
- the final reveal exposes the hidden truth

The generated story is driven by world state, not by a frozen template.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"damage": 0.0, "hidden": 0.0}
        if not self.memes:
            self.memes = {"suspense": 0.0, "worry": 0.0, "certainty": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "girl", "mother"}
        male = {"man", "boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Location:
    id: str
    label: str
    clues: list[str] = field(default_factory=list)
    tense: str = "quiet"


@dataclass
class Clue:
    id: str
    kind: str
    phrase: str
    repeat_phrase: str
    location: str
    reveals: str


@dataclass
class SuspectPair:
    id: str
    label: str
    members: tuple[str, str]
    motive: str
    secret: str


@dataclass
class StoryParams:
    place: str
    clue: str
    pair: str
    hero_name: str
    hero_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Location) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


LOCATIONS = {
    "barn": Location(id="barn", label="the barn", clues=["hay", "hoofprints", "gate"], tense="quiet"),
    "lane": Location(id="lane", label="the lane", clues=["wheeltracks", "mud", "gate"], tense="windy"),
    "yard": Location(id="yard", label="the yard", clues=["mud", "rope", "hay"], tense="still"),
}

CLAUSES = {
    "bell": Clue(
        id="bell",
        kind="bell",
        phrase="a small brass bell",
        repeat_phrase="that little brass bell",
        location="gate",
        reveals="the bell had been tied to a hidden bundle",
    ),
    "ribbon": Clue(
        id="ribbon",
        kind="ribbon",
        phrase="a red ribbon",
        repeat_phrase="that red ribbon",
        location="hay",
        reveals="the ribbon had been used to mark a secret door",
    ),
    "hoofprint": Clue(
        id="hoofprint",
        kind="hoofprint",
        phrase="a row of deep hoofprints",
        repeat_phrase="those same hoofprints",
        location="mud",
        reveals="the prints pointed to the couple's cart",
    ),
}

PAIRS = {
    "couple": SuspectPair(
        id="couple",
        label="the couple",
        members=("Mara", "Joss"),
        motive="they wanted to hide the surprise until evening",
        secret="they were trying to move the bull without scaring the town",
    ),
    "farmers": SuspectPair(
        id="farmers",
        label="the farmers",
        members=("Iris", "Tom"),
        motive="they were keeping the barn quiet for a calf",
        secret="they had borrowed the bull's bell by mistake",
    ),
}


GIRL_NAMES = ["Mina", "Lena", "Nora", "Clara", "Tess"]
BOY_NAMES = ["Noel", "Evan", "Milo", "Finn", "Jude"]
TRAITS = ["careful", "sharp-eyed", "patient", "quiet", "brave"]


class Detective:
    def __init__(self, name: str, kind: str) -> None:
        self.id = name
        self.kind = kind
        self.type = kind
        self.label = name
        self.meters = {"steps": 0.0}
        self.memes = {"suspense": 0.0, "certainty": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "she", "object": "her", "possessive": "her"}[case] if self.kind == "girl" else {"subject": "he", "object": "him", "possessive": "his"}[case]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective story world with suspense, repetition, and a reveal.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--clue", choices=CLAUSES)
    ap.add_argument("--pair", choices=PAIRS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in LOCATIONS.items():
        for clue_id, clue in CLAUSES.items():
            if clue.location in place.clues:
                for pair_id in PAIRS:
                    combos.append((place_id, clue_id, pair_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.pair is None or c[2] == args.pair)]
    if not combos:
        raise StoryError("No valid detective story matches those choices.")
    place, clue, pair = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, clue=clue, pair=pair, hero_name=name, hero_type=gender)


def _report_clue(world: World, detective: Detective, clue: Clue, pair: SuspectPair, repeated: bool = False) -> None:
    detective.memes["suspense"] += 1
    if repeated:
        world.say(f"Again, {clue.repeat_phrase} turned up in the same place.")
    else:
        world.say(f"{clue.phrase} appeared where it should not have been.")
    world.say(f"{detective.id} stayed quiet and looked harder, because the same sign kept coming back.")


def _narrate_setting(world: World, detective: Detective) -> None:
    world.say(f"{detective.id} walked into {world.place.label}, where the air felt still and watchful.")
    world.say("Something there felt off, as if the place itself was waiting to be examined.")


def _investigate(world: World, detective: Detective, clue: Clue, pair: SuspectPair) -> None:
    detective.memes["certainty"] += 1
    world.say(f"{detective.id} checked the {clue.location}, then checked it again.")
    world.say(f"The same little sign showed up a second time, and that repetition made the case feel stranger.")
    world.say(f"At last, {detective.id} saw how {clue.reveals}.")


def _expose(world: World, detective: Detective, clue: Clue, pair: SuspectPair) -> None:
    world.say(f"{detective.id} followed the clues to {pair.label}.")
    world.say(f"Then {detective.id} exposed the truth: {pair.secret}.")
    world.say(f"{pair.label.capitalize()} admitted it was only a secret plan, not a cruel trick.")
    detective.memes["relief"] += 1
    world.say(f"By evening, the town was calm again, and {detective.id} could finally breathe easily.")


def tell(params: StoryParams) -> World:
    place = LOCATIONS[params.place]
    clue = CLAUSES[params.clue]
    pair = PAIRS[params.pair]
    world = World(place)
    detective = Detective(params.hero_name, params.hero_type)

    bull = world.add(Entity(id="bull", kind="character", type="bull", label="the bull", role="owner"))
    bell = world.add(Entity(id="bull_bell", type="thing", label="bell", phrase=clue.phrase, owner="bull", hidden_by=pair.id))
    suspect_a = world.add(Entity(id=pair.members[0], kind="character", type="woman", label=pair.members[0], role="member"))
    suspect_b = world.add(Entity(id=pair.members[1], kind="character", type="man", label=pair.members[1], role="member"))
    world.add(Entity(id="clue", type="thing", label=clue.kind, phrase=clue.phrase))
    world.facts.update(detective=detective, bull=bull, bell=bell, pair=pair, clue=clue, place=place)

    _narrate_setting(world, detective)
    world.para()
    world.say(f"{detective.id} had heard about {pair.label}, and the story felt wrong from the start.")
    world.say(f"People kept whispering the same worry, and that repeated whisper made the day even tenser.")
    _report_clue(world, detective, clue, pair, repeated=False)
    world.say(f"Later, {clue.repeat_phrase} showed up again.")
    _report_clue(world, detective, clue, pair, repeated=True)

    world.para()
    world.say(f"{detective.id} knew the answer was near, because the clues were no longer hiding their path.")
    _investigate(world, detective, clue, pair)
    _expose(world, detective, clue, pair)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    clue = f["clue"]
    pair = f["pair"]
    return [
        f"Write a suspenseful detective story for a child about {detective.id}, {pair.label}, and {clue.phrase}.",
        f"Tell a short mystery where the same clue appears twice before the detective exposes the truth.",
        f"Write a gentle detective tale that uses repetition to build suspense around {pair.label} and a bull's missing clue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    clue = f["clue"]
    pair = f["pair"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who solved the mystery in {place.label}?",
            answer=f"{detective.id} solved it by following the clues carefully and not giving up when the same sign returned."
        ),
        QAItem(
            question=f"What repeated clue made the case feel more suspicious?",
            answer=f"{clue.phrase.capitalize()} showed up more than once, and that repetition made the mystery tense."
        ),
        QAItem(
            question=f"What truth did the detective expose about {pair.label}?",
            answer=f"{detective.id} exposed that {pair.secret}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to discover the truth."
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the nervous feeling of waiting to learn what will happen next."
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means something happens or appears again, and writers often use it to help a story feel stronger or more memorable."
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone solve a mystery."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.hidden_by:
            bits.append(f"hidden_by={e.hidden_by}")
        if any(v for v in e.meters.values()):
            bits.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="barn", clue="bell", pair="couple", hero_name="Mina", hero_type="girl"),
    StoryParams(place="lane", clue="hoofprint", pair="farmers", hero_name="Noel", hero_type="boy"),
    StoryParams(place="yard", clue="ribbon", pair="couple", hero_name="Clara", hero_type="girl"),
]


ASP_RULES = r"""
% A clue is relevant if it matches the place.
relevant(P, C) :- place(P), clue(C), clue_at(C, X), has(P, X).

% Repetition increases suspense.
suspense(P, C) :- relevant(P, C).
suspense_more(P, C) :- suspense(P, C), repeated(C).

% The expose moment happens when the detective has enough clues.
expose(D, P, C) :- detective(D), place(P), clue(C), suspense(P, C), suspense_more(P, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in LOCATIONS.items():
        lines.append(asp.fact("place", pid))
        for c in place.clues:
            lines.append(asp.fact("has", pid, c))
    for cid, clue in CLAUSES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_at", cid, clue.location))
        lines.append(asp.fact("repeated", cid))
    for pid in PAIRS:
        lines.append(asp.fact("pair", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show relevant/2.\n#show suspense/2.\n#show suspense_more/2.\n#show expose/3."))
    return sorted(set(asp.atoms(model, "relevant")))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show relevant/2."))
    asp_set = set(asp.atoms(model, "relevant"))
    py_set = set((p, c) for p, c, _ in valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in LOCATIONS.items():
        for clue_id, clue in CLAUSES.items():
            if clue.location in place.clues:
                for pair_id in PAIRS:
                    combos.append((place_id, clue_id, pair_id))
    return combos


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
        print(asp_program("#show expose/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show relevant/2.\n#show expose/3."))
        print(f"{len(set(asp.atoms(model, 'relevant')))} relevant place/clue pairs")
        print(f"{len(set(asp.atoms(model, 'expose')))} expose facts")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.hero_name}: {p.clue} at {p.place} ({p.pair})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
