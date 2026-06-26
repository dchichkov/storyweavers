#!/usr/bin/env python3
"""
A compact detective-story world about a detective under duress who must choose
between a quick lie and a morally right answer.

The seed premise:
- A small town detective is pressured under duress during a case.
- A moral value matters: honesty.
- The story resolves when the detective protects the truth, reveals the culprit,
  and the pressure lifts.

This script follows the storyworld contract:
- standalone stdlib script
- results imported eagerly
- ASP imported lazily
- supports story generation, QA, JSON, trace, ASP, verify, show-asp
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # detective | suspect | witness | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "girl", "mother", "sister", "detective"}
        male = {"man", "boy", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str
    clues: set[str] = field(default_factory=set)
    pressure_sources: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    value: str
    clue: str
    culprit: str
    setting: str
    duress: str
    resolution: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "alley": Place(name="the narrow alley", clues={"mud", "receipt"}, pressure_sources={"threat"}),
    "station": Place(name="the police station", clues={"file", "lamp"}, pressure_sources={"supervisor"}),
    "library": Place(name="the old library", clues={"book", "key"}, pressure_sources={"deadline"}),
    "dock": Place(name="the quiet dock", clues={"rope", "coin"}, pressure_sources={"fog"}),
}

CASES = {
    "stolen_key": Case(
        id="stolen_key",
        value="honesty",
        clue="key",
        culprit="the greedy clerk",
        setting="library",
        duress="a stern supervisor kept pressing for a fast answer",
        resolution="the detective told the truth and pointed to the hidden key",
    ),
    "missing_coin": Case(
        id="missing_coin",
        value="honesty",
        clue="coin",
        culprit="the nervous porter",
        setting="dock",
        duress="the fog and the ticking clock made everyone push for a shortcut",
        resolution="the detective refused to blame the wrong person and followed the coin trail",
    ),
    "broken_lamp": Case(
        id="broken_lamp",
        value="fairness",
        clue="lamp",
        culprit="the jealous cousin",
        setting="station",
        duress="the chief wanted an easy answer before sunset",
        resolution="the detective named the true culprit and cleared an innocent witness",
    ),
}

DETECTIVES = [
    ("Mara", "woman"),
    ("Evan", "man"),
    ("June", "woman"),
    ("Theo", "man"),
]

WITNESSES = [
    ("Mr. Pike", "man"),
    ("Nina", "woman"),
    ("Ollie", "boy"),
    ("Ruth", "woman"),
]

TRAITS = ["careful", "sharp-eyed", "quiet", "patient", "steady"]


# ---------------------------------------------------------------------------
# Reasonable-world gate
# ---------------------------------------------------------------------------

def case_is_reasonable(place: Place, case: Case) -> bool:
    return case.setting == next(k for k, v in PLACES.items() if v.name == place.name) or case.clue in place.clues


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for case_id, case in CASES.items():
            if case.setting == place_id and case.clue in place.clues:
                combos.append((place_id, case_id))
    return combos


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    case: str
    detective_name: str
    detective_type: str
    witness_name: str
    witness_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def _case_scene(world: World, detective: Entity, witness: Entity, case: Case) -> None:
    world.say(
        f"{detective.id} was a {next(t for t in detective.meters.get('trait_words', []), '')}".strip()
    )


def opening_line(detective: Entity, place: Place, case: Case) -> str:
    return (
        f"{detective.id} was a careful detective who liked solving small mysteries at {place.name}. "
        f"That morning, a case about {case.value} had landed on {detective.pronoun('possessive')} desk."
    )


def clue_line(place: Place, case: Case) -> str:
    return (
        f"The best clue was a {case.clue}, and {place.name} was one of the few places where that clue could appear."
    )


def duress_line(case: Case) -> str:
    return f"Then the pressure grew: {case.duress}."


def lie_choice_line(detective: Entity) -> str:
    detective.memes["duress"] += 1
    detective.memes["temptation"] += 1
    return (
        f"For a moment, {detective.id} thought about giving the easy answer just to make the pressure stop."
    )


def truth_turn_line(detective: Entity, case: Case, witness: Entity) -> str:
    detective.memes["honesty"] += 1
    detective.memes["resolve"] += 1
    detective.memes["duress"] = max(0.0, detective.memes.get("duress", 0.0) - 1.0)
    return (
        f"But {detective.id} took a breath, looked at the clue again, and said the honest thing: "
        f"{case.resolution}. {witness.id} blinked, then nodded because the truth finally fit."
    )


def ending_line(detective: Entity, case: Case) -> str:
    return (
        f"By the end, {detective.id} had protected {case.value}, and the real culprit could no longer hide in the dark."
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def tell(place: Place, case: Case, detective_name: str, detective_type: str,
         witness_name: str, witness_type: str, trait: str) -> World:
    world = World(place)
    detective = world.add(Entity(
        id=detective_name,
        kind="detective",
        type=detective_type,
        label="detective",
        memes={"duress": 0.0, "honesty": 0.0, "resolve": 0.0, "temptation": 0.0},
    ))
    witness = world.add(Entity(
        id=witness_name,
        kind="witness",
        type=witness_type,
        label="witness",
        memes={"fear": 0.0},
    ))
    culprit = world.add(Entity(
        id="culprit",
        kind="suspect",
        type="person",
        label=case.culprit,
    ))

    world.facts.update(
        detective=detective,
        witness=witness,
        culprit=culprit,
        case=case,
        place=place,
        trait=trait,
    )

    world.say(
        f"{detective.id} was a {trait} detective who worked at {place.name}."
    )
    world.say(
        f"{detective.id} was looking into a small mystery about {case.value}, and the case depended on one honest clue."
    )
    world.say(clue_line(place, case))
    world.para()
    world.say(
        f"At {place.name}, {witness.id} brought a worried face and whispered that someone had been asking for a quick answer."
    )
    world.say(duress_line(case))
    world.say(lie_choice_line(detective))
    world.say(
        f"{witness.id} waited with a tight throat while {detective.id} studied the clue and the footprints around it."
    )
    world.para()
    world.say(
        f"That was when {detective.id} chose the right thing instead of the easy thing."
    )
    world.say(truth_turn_line(detective, case, witness))
    world.say(
        f"The real culprit, {case.culprit}, had tried to slip away, but the honest clue pointed straight back."
    )
    world.say(ending_line(detective, case))
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case: Case = f["case"]
    place: Place = f["place"]
    return [
        f'Write a short detective story for a young child about {case.value} at {place.name}, with a clue that matters.',
        f"Tell a simple mystery where a detective is under duress but still chooses honesty.",
        f'Write a kid-friendly detective story that includes the word "duress" and ends with the truth winning.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    witness: Entity = f["witness"]
    case: Case = f["case"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {detective.id}, a careful sleuth working at {place.name}.",
        ),
        QAItem(
            question=f"What clue mattered in the case?",
            answer=f"The important clue was a {case.clue}, and it helped point toward the truth.",
        ),
        QAItem(
            question=f"What was making the detective feel pressure?",
            answer=f"{case.duress.capitalize()}. That meant the detective had to work through duress instead of taking a shortcut.",
        ),
        QAItem(
            question=f"Who helped show that the truth was right?",
            answer=f"{witness.id} was there when the detective chose honesty, and the witness nodded when the story fit.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {detective.id} telling the truth and exposing {case.culprit}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]
    return [
        QAItem(
            question="What is a detective for?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What does honesty mean?",
            answer="Honesty means telling the truth, even when it is hard or uncomfortable.",
        ),
        QAItem(
            question="What is duress?",
            answer="Duress means strong pressure or force that can make it hard to choose calmly.",
        ),
        QAItem(
            question=f"Why was the clue important in this case?",
            answer=f"The clue mattered because it matched the case about {case.value} and led the detective to the real answer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
case(C) :- mystery(C).
valid(P,C) :- place(P), case(C), setting_of(C,P), clue_in(P,C).

honesty_needed(C) :- duress_case(C).
truthful(C) :- honesty_needed(C).
#show valid/2.
#show honesty_needed/1.
#show truthful/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for cid, case in CASES.items():
        lines.append(asp.fact("mystery", cid))
        lines.append(asp.fact("setting_of", cid, case.setting))
        lines.append(asp.fact("clue_in", case.setting, cid))
        if case.value == "honesty":
            lines.append(asp.fact("duress_case", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_reasoning() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show honesty_needed/1.\n#show truthful/1."))
    return sorted(set(asp.atoms(model, "honesty_needed"))), sorted(set(asp.atoms(model, "truthful")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Parameters and CLI
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    case: str
    detective_name: str
    detective_type: str
    witness_name: str
    witness_type: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective story world about duress and honesty.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--case", choices=CASES.keys())
    ap.add_argument("--name")
    ap.add_argument("--witness")
    ap.add_argument("--det-type", choices=["woman", "man"], dest="det_type")
    ap.add_argument("--wit-type", choices=["woman", "man", "boy", "girl"], dest="wit_type")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place and args.case:
        if (args.place, args.case) not in combos:
            raise StoryError("That place and case do not fit together in this world.")
    combos = [
        (p, c) for (p, c) in combos
        if (args.place is None or p == args.place)
        and (args.case is None or c == args.case)
    ]
    if not combos:
        raise StoryError("No valid case matches the given options.")
    place, case = rng.choice(sorted(combos))
    det_name, det_type = random.choice(DETECTIVES) if args.name is None or args.det_type is None else (args.name, args.det_type)
    wit_name, wit_type = random.choice(WITNESSES) if args.witness is None or args.wit_type is None else (args.witness, args.wit_type)
    trait = args.trait or rng.choice(TRAITS)
    if args.name is not None and args.det_type is not None:
        det_name, det_type = args.name, args.det_type
    if args.witness is not None and args.wit_type is not None:
        wit_name, wit_type = args.witness, args.wit_type
    return StoryParams(place, case, det_name, det_type, wit_name, wit_type, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        CASES[params.case],
        params.detective_name,
        params.detective_type,
        params.witness_name,
        params.witness_type,
        params.trait,
    )
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
    StoryParams("library", "stolen_key", "Mara", "woman", "Nina", "woman", "careful"),
    StoryParams("dock", "missing_coin", "Theo", "man", "Mr. Pike", "man", "patient"),
    StoryParams("station", "broken_lamp", "June", "woman", "Ruth", "woman", "steady"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2.\n#show honesty_needed/1.\n#show truthful/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for p, c in combos:
            print(f"  {p:10} {c}")
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
            header = f"### {p.detective_name}: {p.case} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
