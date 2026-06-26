#!/usr/bin/env python3
"""
Standalone story world: a tiny detective story with teamwork and sympathy.

Premise:
- A small detective team notices a puzzling missing-object case.
- The main tension is between suspicion and sympathy.
- The turn is that the team follows clues together instead of blaming.
- The ending proves the change: the missing thing is found, and the team
  "sympathy-izes" the suspect, realizing they needed help.

The world is built around:
- typed entities with physical meters and emotional memes,
- a simple clue trail,
- a cooperative investigation,
- a reasonableness gate that only allows cases with a genuine clue path and a
  plausible helpful resolution.

This script follows the storyworld contract:
- self-contained stdlib script,
- eager import of storyworlds/results.py for QAItem, StoryError, StorySample,
- lazy import of storyworlds/asp.py in ASP helpers,
- StoryParams, registries, build_parser, resolve_params, generate, emit, main,
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp.
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


# ---------------------------------------------------------------------------
# Entities
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
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"lost": 0.0, "found": 0.0, "dusty": 0.0}
        if not self.memes:
            self.memes = {
                "curiosity": 0.0,
                "suspicion": 0.0,
                "sympathy": 0.0,
                "teamwork": 0.0,
                "relief": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "detective-girl"}
        male = {"boy", "man", "father", "uncle", "detective-boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    can_hide: set[str] = field(default_factory=set)
    clue_kind: str = ""


@dataclass
class Clue:
    id: str
    label: str
    place: str
    points_to: Optional[str] = None
    reveals: Optional[str] = None
    helps_teamwork: bool = False


@dataclass
class Case:
    id: str
    missing: str
    missing_label: str
    missing_phrase: str
    owner: str
    suspect: str
    suspect_label: str
    suspect_reason: str
    first_place: str
    solution_place: str
    ending_image: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.clues: dict[str, Clue] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_clue(self, clue: Clue) -> Clue:
        self.clues[clue.id] = clue
        return clue

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
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.clues = _copy.deepcopy(self.clues)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "office": Place(id="office", label="the little office", can_hide={"drawer", "desk"}, clue_kind="dust"),
    "library": Place(id="library", label="the quiet library nook", can_hide={"shelf", "cart"}, clue_kind="paper"),
    "kitchen": Place(id="kitchen", label="the warm kitchen", can_hide={"cupboard", "table"}, clue_kind="crumb"),
    "garden": Place(id="garden", label="the backyard garden path", can_hide={"bush", "bench"}, clue_kind="mud"),
}

CASES = {
    "cookie": Case(
        id="cookie",
        missing="cookie",
        missing_label="cookie jar",
        missing_phrase="a plate of chocolate cookies",
        owner="Benny",
        suspect="Milo",
        suspect_label="the little cat",
        suspect_reason="there were crumb prints by the door",
        first_place="kitchen",
        solution_place="table",
        ending_image="the cookie jar was back on the table, and the crumbs made a tiny trail of proof",
    ),
    "bookmark": Case(
        id="bookmark",
        missing="bookmark",
        missing_label="book",
        missing_phrase="a shiny red bookmark",
        owner="Nina",
        suspect="Pip",
        suspect_label="the page-sorting parrot",
        suspect_reason="there was a feather stuck near the shelf",
        first_place="library",
        solution_place="shelf",
        ending_image="the red bookmark lay safely inside the book, and the shelf looked peaceful again",
    ),
    "key": Case(
        id="key",
        missing="key",
        missing_label="key ring",
        missing_phrase="the garden shed key",
        owner="Tara",
        suspect="Ollie",
        suspect_label="the muddy dog",
        suspect_reason="mud spots led from the path to the bench",
        first_place="garden",
        solution_place="bench",
        ending_image="the key ring was under the bench, shining through a soft patch of mud",
    ),
}

DETECTIVES = {
    "girl": ["Maya", "Lina", "Zoe", "Iris"],
    "boy": ["Noah", "Eli", "Finn", "Theo"],
}

HELPERS = ["sidekick", "partner", "friend"]

TRAITS = ["brave", "careful", "curious", "kind", "sharp-eyed"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    case: str
    detective: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def _make_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    case = CASES[params.case]
    world = World(place)

    hero = world.add(Entity(
        id=params.detective,
        kind="character",
        type="girl" if params.gender == "girl" else "boy",
        label="detective",
        phrase=f"a {params.trait} detective",
    ))
    helper = world.add(Entity(
        id=f"{params.detective}_helper",
        kind="character",
        type="girl" if params.gender == "girl" else "boy",
        label=params.helper,
        phrase=f"a loyal {params.helper}",
    ))
    owner = world.add(Entity(
        id=case.owner,
        kind="character",
        type="girl",
        label="owner",
        phrase="the worried owner",
    ))
    suspect = world.add(Entity(
        id=case.suspect,
        kind="character",
        type="thing",
        label=case.suspect_label,
        phrase=case.suspect_label,
    ))
    missing = world.add(Entity(
        id=case.missing,
        kind="thing",
        type=case.missing,
        label=case.missing_label,
        phrase=case.missing_phrase,
        owner=owner.id,
        caretaker=owner.id,
    ))

    world.add_clue(Clue(
        id=f"{case.id}_first",
        label=f"the {place.clue_kind} clue",
        place=case.first_place,
        points_to=case.solution_place,
        helps_teamwork=False,
    ))
    world.add_clue(Clue(
        id=f"{case.id}_bridge",
        label="the teamwork clue",
        place=case.solution_place,
        reveals=case.missing,
        helps_teamwork=True,
    ))

    world.facts.update(
        hero=hero,
        helper=helper,
        owner=owner,
        suspect=suspect,
        missing=missing,
        case=case,
        place=place,
    )
    return world


def _suspicion_rises(world: World) -> None:
    hero = world.facts["hero"]
    owner = world.facts["owner"]
    suspect = world.facts["suspect"]
    hero.memes["curiosity"] += 1
    hero.memes["suspicion"] += 1
    world.say(
        f"{hero.id} was a {hero.phrase} who liked solving small puzzles."
    )
    world.say(
        f"One day, {owner.id} looked worried because {owner.pronoun('possessive')} "
        f"{world.facts['case'].missing_label} was gone."
    )
    world.say(
        f"{hero.id} noticed {world.facts['case'].suspect_reason}, so {hero.pronoun()} "
        f"looked at {suspect.id} and started to wonder."
    )


def _follow_clue(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    case = world.facts["case"]
    first = next(c for c in world.clues.values() if c.id.endswith("_first"))
    bridge = next(c for c in world.clues.values() if c.id.endswith("_bridge"))
    hero.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    world.say(
        f"{hero.id} and {helper.id} decided to work as a team."
    )
    world.say(
        f"They followed the {first.label} from {case.first_place} to {case.solution_place}."
    )
    world.say(
        f"At last, they found {bridge.label} and realized the problem was not theft at all."
    )


def _sympathy_ize(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    owner = world.facts["owner"]
    suspect = world.facts["suspect"]
    case = world.facts["case"]
    hero.memes["sympathy"] += 2
    helper.memes["sympathy"] += 2
    owner.memes["relief"] += 2
    suspect.memes["relief"] += 1
    world.say(
        f"{hero.id} sympathy-ized {suspect.id}, because the clues showed {suspect.id} "
        f"had only been helping, not hiding anything bad."
    )
    world.say(
        f"Together, they found {case.missing_phrase} {case.ending_image}."
    )
    world.say(
        f"{owner.id} smiled, and the whole little team felt proud of their teamwork."
    )


def _resolve_case(world: World) -> None:
    case = world.facts["case"]
    missing = world.facts["missing"]
    missing.meters["found"] += 1
    missing.meters["lost"] = 0
    _follow_clue(world)
    _sympathy_ize(world)
    world.para()
    world.say(f"By the end, {case.ending_image}.")


def tell(params: StoryParams) -> World:
    world = _make_world(params)
    _suspicion_rises(world)
    world.para()
    _resolve_case(world)
    return world


# ---------------------------------------------------------------------------
# Reasonableness helpers
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for case_id, case in CASES.items():
            if case.first_place == place_id:
                combos.append((place_id, case_id, case.owner))
    return combos


def explain_rejection(place: str, case: str) -> str:
    return (
        f"(No story: this case does not begin in {PLACES[place].label if place in PLACES else place} "
        f"with the selected mystery. Try a case whose first clue belongs there.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A case is valid when the selected place is where the first clue begins.
valid(Place, Case) :- starts_at(Case, Place).

% Teamwork is part of the story when a helper works with the detective.
teamwork_story(Case) :- has_helper(Case), valid(_, Case).

% Sympathy is part of the story when the detective does not blame the suspect
% after following clues to the answer.
sympathy_story(Case) :- valid(_, Case), clue_path(Case), not blame_only(Case).

#show valid/2.
#show teamwork_story/1.
#show sympathy_story/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("starts_at", place_id, place_id))
    for case_id, case in CASES.items():
        lines.append(asp.fact("case", case_id))
        lines.append(asp.fact("starts_at", case_id, case.first_place))
        lines.append(asp.fact("clue_path", case_id))
        lines.append(asp.fact("has_helper", case_id))
        if case.solution_place == case.first_place:
            lines.append(asp.fact("blame_only", case_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, c) for p, c, _ in valid_combos()}
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    hero = world.facts["hero"]
    return [
        f'Write a short detective story for a young child that includes the word "sympathy-ize" and shows teamwork.',
        f"Tell a small mystery story where {hero.id} and a helper follow clues, then sympathy-ize the suspect.",
        f"Write a gentle detective story about a missing {case.missing}, a clue trail, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case = world.facts["case"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    owner = world.facts["owner"]
    suspect = world.facts["suspect"]
    place = world.facts["place"]

    return [
        QAItem(
            question=f"Who solved the mystery in {place.label}?",
            answer=f"{hero.id} solved it with help from {helper.id}. They worked as a team and followed the clues together.",
        ),
        QAItem(
            question=f"What was missing in the story?",
            answer=f"{owner.id}'s {case.missing_label} was missing, and that started the little detective case.",
        ),
        QAItem(
            question=f"Why did {hero.id} first look at {suspect.id}?",
            answer=f"{hero.id} noticed a clue that made {suspect.id} look suspicious at first, but the team kept investigating instead of blaming.",
        ),
        QAItem(
            question=f"What did it mean when {hero.id} sympathy-ized {suspect.id}?",
            answer=f"It meant {hero.id} chose to understand {suspect.id} kindly after the clues showed there was a harmless reason for what happened.",
        ),
        QAItem(
            question=f"How did teamwork help the case?",
            answer=f"{hero.id} and {helper.id} shared clues, stayed calm, and found the missing thing faster together than one detective could alone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully for clues, asks smart questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people work together, help each other, and share the job instead of doing it alone.",
        ),
        QAItem(
            question="What is sympathy?",
            answer="Sympathy means caring about how someone else feels and trying to understand them kindly.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace / rendering
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny detective story world with teamwork and sympathy-ize.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--detective")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = valid_combos()
    if args.place or args.case:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.case is None or c[1] == args.case)
        ]
    if not combos:
        raise StoryError("(No valid detective case matches the given options.)")
    place, case_id, _ = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    detective = args.detective or rng.choice(DETECTIVES[gender])
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, case=case_id, detective=detective, gender=gender, helper=helper, trait=trait)


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="kitchen", case="cookie", detective="Maya", gender="girl", helper="partner", trait="curious"),
    StoryParams(place="library", case="bookmark", detective="Noah", gender="boy", helper="friend", trait="sharp-eyed"),
    StoryParams(place="garden", case="key", detective="Lina", gender="girl", helper="sidekick", trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2.\n#show teamwork_story/1.\n#show sympathy_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2.\n#show teamwork_story/1.\n#show sympathy_story/1."))
        valid = sorted(set(asp.atoms(model, "valid")))
        teamwork = sorted(set(asp.atoms(model, "teamwork_story")))
        sympathy = sorted(set(asp.atoms(model, "sympathy_story")))
        print(f"valid: {valid}")
        print(f"teamwork_story: {teamwork}")
        print(f"sympathy_story: {sympathy}")
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
            header = f"### {p.detective} in {p.place} (case: {p.case})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
