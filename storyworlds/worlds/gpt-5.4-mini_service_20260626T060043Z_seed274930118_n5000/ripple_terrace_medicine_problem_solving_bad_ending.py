#!/usr/bin/env python3
"""
Story world: Ripple Terrace Medicine Problem Solving Bad Ending Rhyme.

A small adventure domain about a child on a terrace, a needed medicine bottle,
a ripple of spilled water, and a problem-solving attempt that goes wrong.
The story is intentionally capable of a bad ending: the medicine is lost, and
the last image proves the problem was not solved.

The world is built around a few stateful entities:
- a child with courage, worry, and determination
- a sick elder waiting for medicine
- a terrace with a bowl of water that can ripple and spill
- a medicine bottle that can be dropped, soaked, and ruined

The script supports the shared storyworld CLI contract, including ASP parity
checks for the validity gate.
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
# Small domain registries
# ---------------------------------------------------------------------------

NAMES = ["Mina", "Toby", "Lina", "Owen", "Iris", "Noah", "Pia", "Ezra"]
ELDER_NAMES = ["Grandma", "Grandpa", "Aunt June", "Uncle Hal"]
TRAITS = ["brave", "careful", "curious", "steady", "eager"]

PLACES = {
    "terrace": {
        "label": "the terrace",
        "indoors": False,
        "edges": True,
        "bowl": True,
    }
}

MEDICINES = {
    "syrup": {
        "label": "medicine syrup",
        "phrase": "a small bottle of medicine syrup",
        "taste": "bitter",
        "container": "bottle",
    },
    "drops": {
        "label": "eye drops",
        "phrase": "a tiny bottle of eye drops",
        "taste": "sharp",
        "container": "dropper bottle",
    },
}

PROBLEMS = {
    "spill": {
        "label": "spill",
        "verb": "spill",
        "gerund": "spilling",
        "mess": "wet",
        "risk": "the medicine bottle could slip and tip over",
    },
    "ripple": {
        "label": "ripple",
        "verb": "make a ripple",
        "gerund": "rippling",
        "mess": "wet",
        "risk": "a ripple could splash water onto the medicine and the floor",
    },
}

SOLUTIONS = {
    "tray": {
        "label": "a tray",
        "verb": "carry the bottle on a tray",
        "helps": {"spill"},
    },
    "cloth": {
        "label": "a dry cloth",
        "verb": "wrap the bottle in a dry cloth",
        "helps": {"spill"},
    },
    "ladder": {
        "label": "a short ladder",
        "verb": "climb up for a better look",
        "helps": set(),
    },
}

# ---------------------------------------------------------------------------
# Shared dataclasses and world model
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = "terrace"
    problem: str = "ripple"
    medicine: str = "syrup"
    name: str = "Mina"
    elder: str = "Grandma"
    trait: str = "careful"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.water_level: float = 0.0
        self.ripple_active: bool = False
        self.medicine_wet: bool = False
        self.resolved: bool = False
        self.bad_ending: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        w = World(self.params)
        w.entities = copy.deepcopy(self.entities)
        w.lines = []
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.water_level = self.water_level
        w.ripple_active = self.ripple_active
        w.medicine_wet = self.medicine_wet
        w.resolved = self.resolved
        w.bad_ending = self.bad_ending
        return w


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------

def problem_at_risk(problem: str, medicine: str) -> bool:
    return problem in PROBLEMS and medicine in MEDICINES


def valid_combo(problem: str, medicine: str) -> bool:
    return problem_at_risk(problem, medicine)


def choose_solution(problem: str) -> Optional[str]:
    for sid, sol in SOLUTIONS.items():
        if problem in sol["helps"]:
            return sid
    return None


def _cause_ripple(world: World, child: Entity, medicine: Entity) -> None:
    sig = ("ripple",)
    if sig in world.fired:
        return
    world.fired.add(sig)
    world.ripple_active = True
    world.water_level += 1.0
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    world.say(
        f"On the terrace, a shallow bowl of water caught {child.id}'s eye, "
        f"and one little ripple danced across it like a silver ring."
    )
    world.say(
        f"{child.id} was carrying {medicine.phrase} for {world.facts['elder_name']}, "
        f"but the ripple made the floor slick."
    )


def _problem_solve(world: World, child: Entity, medicine: Entity) -> None:
    sig = ("solve",)
    if sig in world.fired:
        return
    world.fired.add(sig)

    solution_id = choose_solution(world.params.problem)
    if solution_id is None:
        raise StoryError("No safe solution exists for this problem.")

    sol = SOLUTIONS[solution_id]
    world.say(
        f"{child.id} tried to solve the problem by choosing {sol['label']} and "
        f"thinking hard."
    )

    # The intended solution fails for the ripple problem, which creates the bad ending.
    if world.params.problem == "ripple":
        world.say(
            f"But the terrace still shivered with water, and the little wave slipped "
            f"around the tray before {child.id} could hold it steady."
        )
        world.medicine_wet = True
        medicine.meters["wet"] = medicine.meters.get("wet", 0.0) + 1.0
        child.memes["worry"] += 1.0
        world.bad_ending = True
        world.say(
            f"The bottle tilted, the medicine splashed, and the bottle rolled into a corner "
            f"where nobody could save it."
        )
    else:
        world.resolved = True


def _ending(world: World, child: Entity, elder: Entity, medicine: Entity) -> None:
    if world.bad_ending:
        child.memes["sad"] = child.memes.get("sad", 0.0) + 1.0
        elder.memes["hope"] = elder.memes.get("hope", 0.0) - 1.0
        world.say(
            f"So {child.id} stood still beside the wet stone floor, and the medicine was gone. "
            f"{elder.id} would have to wait, which felt heavy and wrong."
        )
        world.say(
            f"On that terrace, the ripple won the day; the needed medicine slipped away."
        )
    else:
        world.say(
            f"At last, {child.id} carried {medicine.label} to {elder.id}, and the day ended safely."
        )


def tell(params: StoryParams) -> World:
    world = World(params)
    child_type = "girl" if params.name in {"Mina", "Lina", "Iris", "Pia"} else "boy"
    child = world.add(Entity(id=params.name, kind="character", type=child_type))
    elder = world.add(Entity(id=params.elder, kind="character", type="elder"))
    medicine = world.add(
        Entity(
            id="medicine",
            kind="thing",
            type=params.medicine,
            label=MEDICINES[params.medicine]["label"],
            phrase=MEDICINES[params.medicine]["phrase"],
            owner=elder.id,
            caretaker=elder.id,
        )
    )

    world.facts["child_name"] = child.id
    world.facts["elder_name"] = elder.id
    world.facts["medicine_label"] = medicine.label
    world.facts["problem"] = params.problem
    world.facts["place"] = params.place

    world.say(
        f"{child.id} was a {params.trait} child on {PLACES[params.place]['label']}, "
        f"and {elder.id} needed {medicine.label} right away."
    )
    world.say(
        f"{child.id} held {medicine.phrase} carefully, hoping the trip would be quick."
    )

    if params.problem == "ripple":
        _cause_ripple(world, child, medicine)
    else:
        world.say("The terrace was calm, but the plan still needed a careful fix.")

    _problem_solve(world, child, medicine)
    _ending(world, child, elder, medicine)

    world.facts["bad_ending"] = world.bad_ending
    world.facts["resolved"] = world.resolved
    return world


# ---------------------------------------------------------------------------
# Registries and prompts
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a short adventure story for young children about {p.name}, a terrace, and a ripple.",
        f"Tell a child-facing story where someone tries problem solving with medicine on a terrace but the ending is bad.",
        f"Write a rhyming little tale about {p.name} and {p.elder} when a ripple makes the medicine hard to save.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    elder = world.facts["elder_name"]
    child = world.facts["child_name"]
    medicine = world.facts["medicine_label"]
    return [
        QAItem(
            question=f"Who was trying to bring the {medicine} on the terrace?",
            answer=f"{child} was trying to bring the {medicine} to {elder} on the terrace."
        ),
        QAItem(
            question="What caused the problem on the terrace?",
            answer="A little ripple in the water made the floor slick and caused trouble for the medicine."
        ),
        QAItem(
            question="Did the problem get solved in the end?",
            answer="No. The attempt at problem solving failed, and the story ended badly when the medicine was spilled."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ripple?",
            answer="A ripple is a small wave that moves across water."
        ),
        QAItem(
            question="What is a terrace?",
            answer="A terrace is a flat outdoor place beside a building where people can sit or walk."
        ),
        QAItem(
            question="Why must medicine be handled carefully?",
            answer="Medicine must be handled carefully so it does not spill, break, or get ruined before someone can use it."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid(P, Prob, Med) :- place(P), problem(Prob), medicine(Med), valid_combo(Prob, Med).
bad_end(Prob) :- problem(Prob), Prob = ripple.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for prob in PROBLEMS:
        lines.append(asp.fact("problem", prob))
    for med in MEDICINES:
        lines.append(asp.fact("medicine", med))
    for prob in PROBLEMS:
        for med in MEDICINES:
            if valid_combo(prob, med):
                lines.append(asp.fact("valid_combo", prob, med))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, prob, med) for p in PLACES for prob in PROBLEMS for med in MEDICINES if valid_combo(prob, med)}
    try:
        asp_set = set(asp_valid_combos())
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    if asp_set == py:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  only in ASP:", sorted(asp_set - py))
    print("  only in Python:", sorted(py - asp_set))
    return 1


# ---------------------------------------------------------------------------
# CLI and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ripple terrace medicine adventure with a bad ending.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--medicine", choices=sorted(MEDICINES))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--elder", choices=ELDER_NAMES)
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
    place = args.place or "terrace"
    problem = args.problem or rng.choice(list(PROBLEMS))
    medicine = args.medicine or rng.choice(list(MEDICINES))
    if not valid_combo(problem, medicine):
        raise StoryError("That problem and medicine do not make a reasonable story.")
    name = args.name or rng.choice(NAMES)
    elder = args.elder or rng.choice(ELDER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, medicine=medicine, name=name, elder=elder, trait=trait)


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"bad_ending={world.bad_ending} resolved={world.resolved} ripple_active={world.ripple_active}")
    lines.append(f"water_level={world.water_level} medicine_wet={world.medicine_wet}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
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
    StoryParams(place="terrace", problem="ripple", medicine="syrup", name="Mina", elder="Grandma", trait="careful"),
    StoryParams(place="terrace", problem="ripple", medicine="drops", name="Owen", elder="Grandpa", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program("#show valid/3."))
            vals = sorted(set(asp.atoms(model, "valid")))
            for v in vals:
                print(v)
        except Exception as e:
            print(f"ASP unavailable: {e}")
            sys.exit(1)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
