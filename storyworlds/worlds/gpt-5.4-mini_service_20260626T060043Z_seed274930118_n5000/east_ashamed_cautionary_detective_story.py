#!/usr/bin/env python3
"""
A standalone storyworld: a cautionary detective story set in the east side of town.

Premise:
- A young detective hears about a missing jar of moon jam from the east market.
- The clue trail is physical and emotional: muddy paw prints, a dropped ticket, and
  a child who feels ashamed after making a bad choice.
- The detective must solve the case without blaming too quickly.

The world is small on purpose: a few typed entities, two state dimensions
(meters and memes), a causal turn, and a gentle resolution that proves what
changed.
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
# Core domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class District:
    name: str
    east: bool = False
    places: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    location: str
    kind: str


@dataclass
class Case:
    id: str
    title: str
    suspect_action: str
    warning: str
    consequence: str
    clue_kind: str
    solved_by: str


class World:
    def __init__(self, district: District) -> None:
        self.district = district
        self.entities: dict[str, Entity] = {}
        self.clues: list[Clue] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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

        clone = World(self.district)
        clone.entities = copy.deepcopy(self.entities)
        clone.clues = copy.deepcopy(self.clues)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
DISTRICTS = {
    "east": District(name="the east side", east=True, places={"east market", "east lane", "east pier"}),
    "center": District(name="the center square", east=False, places={"square", "station", "library"}),
}

CASES = {
    "jam": Case(
        id="jam",
        title="The Missing Moon Jam",
        suspect_action="take the moon jam from the stall",
        warning="That jar was not meant to be taken without asking",
        consequence="the stall owner would lose trust",
        clue_kind="sticky",
        solved_by="find the truth before the wrong person got blamed",
    ),
    "lantern": Case(
        id="lantern",
        title="The Broken Lantern",
        suspect_action="carry the lantern too fast",
        warning="That lantern could crack if it was rushed",
        consequence="the path would turn dark",
        clue_kind="glass",
        solved_by="slow down and follow the careful clue trail",
    ),
    "ticket": Case(
        id="ticket",
        title="The Lost Train Ticket",
        suspect_action="hide the train ticket after a mistake",
        warning="A hidden ticket can make a small mistake look worse",
        consequence="someone might miss the train",
        clue_kind="paper",
        solved_by="admit the mistake and return the ticket",
    ),
}

# A cautionary detective tale should have a concrete risk and a truthful fix.
CLUES = {
    "sticky": Clue(id="jam_clue", label="a sticky smear", location="stall counter", kind="sticky"),
    "glass": Clue(id="glass_clue", label="a tiny shard", location="alley stones", kind="glass"),
    "paper": Clue(id="paper_clue", label="a torn ticket stub", location="bench seat", kind="paper"),
}

NAMES = ["Mina", "Jules", "Tara", "Eli", "Noor", "Finn"]
ADJECTIVES = ["careful", "curious", "quiet", "smart", "patient", "brave"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    district: str
    case: str
    detective: str
    suspect: str
    suspect_type: str
    bystander: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------
def is_east(district: District) -> bool:
    return district.east


def clue_matches(case: Case, clue: Clue) -> bool:
    return case.clue_kind == clue.kind


def plausible_case(case: Case, district: District) -> bool:
    return is_east(district) and len(district.places) > 0


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for did, d in DISTRICTS.items():
        lines.append(asp.fact("district", did))
        if d.east:
            lines.append(asp.fact("east", did))
        for p in sorted(d.places):
            lines.append(asp.fact("place", did, p))
    for cid, c in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("warning", cid, c.warning))
        lines.append(asp.fact("consequence", cid, c.consequence))
        lines.append(asp.fact("clue_kind", cid, c.clue_kind))
    for kid, clue in CLUES.items():
        lines.append(asp.fact("clue", kid))
        lines.append(asp.fact("kind", kid, clue.kind))
    return "\n".join(lines)


ASP_RULES = r"""
east_story(D, C) :- east(D), case(C).
good_case(C) :- clue_kind(C, K), kind(_, K).
valid(D, C) :- east_story(D, C), good_case(C).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid() -> list[tuple]:
    out = []
    for did, d in DISTRICTS.items():
        for cid, c in CASES.items():
            if plausible_case(c, d) and any(clue_matches(c, clue) for clue in CLUES.values()):
                out.append((did, cid))
    return sorted(set(out))


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def predict_consequence(world: World, params: StoryParams) -> bool:
    case = CASES[params.case]
    clue = next(c for c in CLUES.values() if c.kind == case.clue_kind)
    return clue_matches(case, clue) and world.get("suspect").memes.get("ashamed", 0) >= 1


def build_world(params: StoryParams) -> World:
    district = DISTRICTS[params.district]
    case = CASES[params.case]
    world = World(district)

    detective = world.add(Entity(
        id="detective", kind="character", type="girl", label=params.detective
    ))
    suspect = world.add(Entity(
        id="suspect", kind="character", type=params.suspect_type, label=params.suspect
    ))
    bystander = world.add(Entity(
        id="bystander", kind="character", type="boy", label=params.bystander
    ))
    clue = next(c for c in CLUES.values() if c.kind == case.clue_kind)
    world.clues.append(clue)

    world.say(f"{detective.label} was a young detective who loved quiet clues and honest answers.")
    world.say(f"One evening, {detective.label} took a case in {district.name}.")
    world.say(f"People said something was missing, but nobody knew why.")

    world.para()
    world.say(
        f"{detective.label} found {clue.label} at the {clue.location}, "
        f"so {detective.label} followed it step by step."
    )
    suspect.memes["ashamed"] = 1
    suspect.meters["restless"] = 1
    world.say(
        f"Near the end of the trail, {suspect.label} looked down in shame. "
        f"{suspect.label.capitalize()} had tried to {case.suspect_action}, and now "
        f"{suspect.pronoun()} felt ashamed."
    )

    world.para()
    if predict_consequence(world, params):
        world.say(
            f"{detective.label} did not rush to accuse anyone. "
            f"Instead, {detective.label} asked one gentle question at a time."
        )
        world.say(
            f"{suspect.label} finally admitted the mistake, and the missing thing was returned."
        )
        world.say(
            f"Because {suspect.label} told the truth, the east side stayed calm, "
            f"and the warning came true in a useful way: {case.warning.lower()}."
        )
    else:
        raise StoryError("The case does not form a believable cautionary detective story.")

    world.facts.update(
        detective=detective,
        suspect=suspect,
        bystander=bystander,
        case=case,
        clue=clue,
        district=district,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case: Case = f["case"]
    return [
        f'Write a short cautionary detective story set in the east side about {case.title}.',
        f"Tell a child-friendly detective story where someone feels ashamed after a mistake and then tells the truth.",
        f"Write a story about a detective in the east who follows a clue and solves a small problem without blaming too quickly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    suspect: Entity = f["suspect"]
    case: Case = f["case"]
    clue: Clue = f["clue"]
    district: District = f["district"]

    return [
        QAItem(
            question=f"Where did {detective.label} work on the case?",
            answer=f"{detective.label} worked in {district.name}, where the clue trail was easy to follow.",
        ),
        QAItem(
            question=f"What clue helped {detective.label} solve the case?",
            answer=f"{clue.label.capitalize()} helped {detective.label} find the truth.",
        ),
        QAItem(
            question=f"Why did {suspect.label} feel ashamed?",
            answer=(
                f"{suspect.label} felt ashamed because {suspect.pronoun('subject')} "
                f"tried to {case.suspect_action} and knew it was wrong."
            ),
        ),
        QAItem(
            question=f"What did the detective do instead of accusing everyone right away?",
            answer=(
                f"{detective.label} asked gentle questions and followed the clue trail "
                f"before saying who was responsible."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"The missing thing was returned, the mistake was admitted, and the east side "
                f"stayed calm because the truth came out."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "east": [
        QAItem(
            question="What does east mean?",
            answer="East is the direction where the sun rises in the morning.",
        )
    ],
    "ashamed": [
        QAItem(
            question="What does ashamed mean?",
            answer="Ashamed means feeling bad because you know you did something wrong.",
        )
    ],
    "detective": [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and uses careful thinking to solve a problem.",
        )
    ],
    "clue": [
        QAItem(
            question="What is a clue?",
            answer="A clue is a piece of information that helps someone solve a mystery.",
        )
    ],
    "truth": [
        QAItem(
            question="Why is telling the truth important?",
            answer="Telling the truth helps people fix mistakes and trust each other again.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["east"])
    out.extend(WORLD_KNOWLEDGE["ashamed"])
    out.extend(WORLD_KNOWLEDGE["detective"])
    out.extend(WORLD_KNOWLEDGE["clue"])
    out.extend(WORLD_KNOWLEDGE["truth"])
    return out


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


# ---------------------------------------------------------------------------
# Serialization / tracing
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:9} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  clues: {[c.label for c in world.clues]}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A cautionary detective storyworld set on the east side."
    )
    ap.add_argument("--district", choices=DISTRICTS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--detective")
    ap.add_argument("--suspect")
    ap.add_argument("--suspect-type", choices=["boy", "girl"])
    ap.add_argument("--bystander")
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
    if args.district and not DISTRICTS[args.district].east:
        raise StoryError("This storyworld only supports the east side.")
    district = args.district or "east"
    case = args.case or "jam"
    detective = args.detective or rng.choice(NAMES)
    suspect = args.suspect or rng.choice([n for n in NAMES if n != detective])
    suspect_type = args.suspect_type or rng.choice(["boy", "girl"])
    bystander = args.bystander or rng.choice([n for n in NAMES if n not in {detective, suspect}])

    if not plausible_case(CASES[case], DISTRICTS[district]):
        raise StoryError("The requested case does not fit this district.")
    return StoryParams(
        district=district,
        case=case,
        detective=detective,
        suspect=suspect,
        suspect_type=suspect_type,
        bystander=bystander,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def asp_valid_cases() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(python_valid())
    cl = set(asp_valid_cases())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} cases).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        cases = asp_valid_cases()
        print(f"{len(cases)} valid east-side cases:\n")
        for d, c in cases:
            print(f"  {d:5} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    curated = [
        StoryParams(district="east", case="jam", detective="Mina", suspect="Jules", suspect_type="boy", bystander="Noor"),
        StoryParams(district="east", case="lantern", detective="Eli", suspect="Tara", suspect_type="girl", bystander="Finn"),
        StoryParams(district="east", case="ticket", detective="Noor", suspect="Mina", suspect_type="girl", bystander="Jules"),
    ]

    if args.all:
        samples = [generate(p) for p in curated]
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
            header = f"### {p.detective}: {p.case} in {p.district}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
