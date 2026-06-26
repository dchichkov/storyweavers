#!/usr/bin/env python3
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
    label: str = ""
    phrase: str = ""
    type: str = ""
    owner: Optional[str] = None
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
    setting: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    mystery: str
    lead: str
    reveal: str
    clue: str
    theme: str
    tag: str


@dataclass
class Moral:
    id: str
    label: str
    explanation: str


@dataclass
class StoryParams:
    place: str
    case: str
    moral: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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


PLACES = {
    "garden": Place("garden", "the garden", "outside", affords={"search", "sow"}),
    "schoolyard": Place("schoolyard", "the schoolyard", "outside", affords={"search"}),
    "library": Place("library", "the library", "inside", affords={"search"}),
    "market": Place("market", "the market", "inside", affords={"search"}),
}

CASES = {
    "missing_seed_packet": Case(
        id="missing_seed_packet",
        mystery="a missing packet of flower seeds",
        lead="a trail of tiny dirt crumbs",
        reveal="the seeds had been moved to the watering shelf",
        clue="soil on the bench",
        theme="sow",
        tag="sow",
    ),
    "lost_badge": Case(
        id="lost_badge",
        mystery="a lost helper badge",
        lead="a shiny flash near the library table",
        reveal="the badge had slipped into a book",
        clue="a bent ribbon",
        theme="attention",
        tag="attention",
    ),
    "missing_crayon_box": Case(
        id="missing_crayon_box",
        mystery="a missing box of crayons",
        lead="a rainbow smudge on a chair",
        reveal="the box had been shared with the art corner",
        clue="a colored fingerprint",
        theme="sharing",
        tag="sharing",
    ),
}

MORALS = {
    "kindness": Moral("kindness", "Kindness", "kindness means helping carefully, even before the answer is clear"),
    "sharing": Moral("sharing", "Sharing", "sharing means letting others use something and taking turns fairly"),
    "attention": Moral("attention", "Attention", "attention means looking closely at small details"),
}

HELPERS = {
    "mother": "mother",
    "father": "father",
    "friend": "friend",
    "teacher": "teacher",
}

NAMES = {
    "girl": ["Mia", "Lily", "Nora", "Ava", "Zoe"],
    "boy": ["Leo", "Finn", "Noah", "Eli", "Max"],
}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for case_id, case in CASES.items():
            if case.theme in place.affords:
                for moral_id in MORALS:
                    out.append((place_id, case_id, moral_id))
    return out


def explain_invalid(place: Place, case: Case) -> str:
    return (
        f"(No story: {case.mystery} does not fit well at {place.label}. "
        f"Try a place where that kind of search feels natural.)"
    )


@dataclass
class StoryState:
    world: World
    detective: Entity
    helper: Entity
    object_of_interest: Entity
    case: Case
    moral: Moral


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style moral value story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.place and args.case:
        place = PLACES[args.place]
        case = CASES[args.case]
        if (args.place, args.case) not in {(p, c) for p, c, _ in valid_combos()}:
            raise StoryError(explain_invalid(place, case))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.case is None or c[1] == args.case)
        and (args.moral is None or c[2] == args.moral)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, case, moral = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place=place, case=case, moral=moral, name=name, gender=gender, helper=helper)


def _detective_pronoun(gender: str, case: str) -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def generate_world(params: StoryParams) -> StoryState:
    place = PLACES[params.place]
    case = CASES[params.case]
    moral = MORALS[params.moral]
    world = World(place)
    detective = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=params.helper))
    item = world.add(Entity(id="item", label=case.mystery, phrase=case.mystery, owner=helper.id))
    detective.memes["curiosity"] = 1.0
    helper.memes["kindness"] = 1.0
    return StoryState(world=world, detective=detective, helper=helper, object_of_interest=item, case=case, moral=moral)


def tell(state: StoryState) -> None:
    w = state.world
    d = state.detective
    h = state.helper
    item = state.object_of_interest
    case = state.case
    moral = state.moral

    w.say(f"{d.id} was a small detective who loved clues, careful footsteps, and solving little puzzles.")
    w.say(f"One day at {w.place.label}, {d.id} noticed {case.lead} and started paying close attention.")
    w.say(f"{_detective_pronoun(d.type, 'subject').capitalize()} wanted to find {item.phrase}, but the place was busy and noisy.")

    w.para()
    w.say(f"{h.label.capitalize()} came over and showed kindness by standing still and sharing the quiet work.")
    w.say(f"{d.id} asked gentle questions, and {h.label} pointed to {case.clue}.")
    w.say(f"That clue mattered, because it was the kind of tiny detail only a careful detective would notice.")

    w.para()
    w.say(
        f"{d.id} looked again, found the answer, and solved the case: {case.reveal}."
    )
    if case.tag == "sow":
        w.say(f"Near the garden bed, someone had been ready to sow new flowers, so the seeds were safe after all.")
    elif case.tag == "sharing":
        w.say(f"The crayons had been shared instead of hidden, so everyone could color together.")
    else:
        w.say(f"The missing thing was there all along, tucked where no one had thought to look.")

    w.para()
    w.say(
        f"In the end, {d.id} smiled and remembered the lesson: {moral.label.lower()} meant "
        f"{moral.explanation}, and that made the whole day feel bright."
    )

    w.facts.update(
        detective=d,
        helper=h,
        item=item,
        case=case,
        moral=moral,
        place=w.place,
    )


def story_qa(world: World) -> list[QAItem]:
    d = world.facts["detective"]
    h = world.facts["helper"]
    case = world.facts["case"]
    moral = world.facts["moral"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"Who solved the mystery at {place.label}?",
            answer=f"{d.id} solved the mystery by paying close attention to the clues.",
        ),
        QAItem(
            question=f"How did {h.label} help {d.id}?",
            answer=f"{h.label.capitalize()} showed kindness and shared what {d.id} needed to notice the clue.",
        ),
        QAItem(
            question=f"What was the important lesson in the story?",
            answer=f"The story taught {moral.label.lower()}, which means {moral.explanation}.",
        ),
        QAItem(
            question=f"What was the mystery about?",
            answer=f"It was about {case.mystery}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is treating others gently and helping them when you can.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use something or take a turn.",
        ),
        QAItem(
            question="What does it mean to pay attention?",
            answer="It means looking and listening carefully so you do not miss small details.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    moral = world.facts["moral"]
    return [
        f"Write a short detective story for a child about {case.mystery} and {moral.label.lower()}.",
        f"Tell a gentle mystery where a small detective uses attention, kindness, and sharing to solve a case.",
        f"Write a story with the words variant, attention, and sow, ending with a clear clue and a warm lesson.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  place={world.place.id}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(Place, Case, Moral) :- place(Place), case(Case), moral(Moral), affords(Place, Theme), case_theme(Case, Theme).
#show valid_combo/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, case in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("case_theme", cid, case.theme))
    for mid in MORALS:
        lines.append(asp.fact("moral", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def valid_combo_list() -> list[tuple[str, str, str]]:
    return valid_combos()


def generate(params: StoryParams) -> StorySample:
    state = generate_world(params)
    tell(state)
    return StorySample(
        params=params,
        story=state.world.render(),
        prompts=generation_prompts(state.world),
        story_qa=story_qa(state.world),
        world_qa=world_qa(state.world),
        world=state.world,
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
    StoryParams(place="garden", case="missing_seed_packet", moral="kindness", name="Mia", gender="girl", helper="mother"),
    StoryParams(place="library", case="lost_badge", moral="attention", name="Leo", gender="boy", helper="teacher"),
    StoryParams(place="market", case="missing_crayon_box", moral="sharing", name="Ava", gender="girl", helper="friend"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.name}: {p.case} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
