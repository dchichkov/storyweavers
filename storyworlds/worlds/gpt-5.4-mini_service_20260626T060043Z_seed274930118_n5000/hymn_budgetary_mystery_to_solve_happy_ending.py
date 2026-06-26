#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/hymn_budgetary_mystery_to_solve_happy_ending.py
==============================================================================================================

A small heartwarming storyworld about a child, a community hymn, and a
budgetary mystery that gets solved with care.

Premise:
- A small choir is preparing for a Sunday hymn.
- The town needs to stay inside a tight budget.
- Something important goes missing, and the child helps solve the mystery.

The storyworld generates a complete little tale with:
- clear setup
- a concrete mystery
- state-driven investigation and turn
- a happy ending image proving what changed

The world model tracks both physical state (meters) and emotional state (memes).
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
# World data
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
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
class Venue:
    place: str = "the little community hall"
    afford_hymn: bool = True
    afford_budget: bool = True


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    mystery: str
    budget: int
    seed: Optional[int] = None


class World:
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace_notes: list[str] = []
        self.fired: set[str] = set()

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
        clone = World(self.venue)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.trace_notes = list(self.trace_notes)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "hall": Venue(place="the little community hall"),
    "church": Venue(place="the bright church room"),
    "school": Venue(place="the school music room"),
}

MYSTERIES = {
    "missing_hymnbook": {
        "thing": "the hymnbook",
        "clue": "a page with pencil marks",
        "hide_spot": "under the piano bench",
        "cause": "someone had moved it after practice",
        "budget_item": "a replacement hymnbook",
        "budget_cost": 3,
        "resolution": "the choir could sing from the found book instead of buying a new one",
    },
    "missing_tin": {
        "thing": "the donation tin",
        "clue": "a coin trail by the window",
        "hide_spot": "behind the snack table",
        "cause": "a gust had nudged it while the windows were open",
        "budget_item": "new poster tape",
        "budget_cost": 2,
        "resolution": "the tin was found and the budget stayed safe",
    },
    "missing_sheet_music": {
        "thing": "the song sheet",
        "clue": "a folded corner near the chairs",
        "hide_spot": "inside the hymn binder",
        "cause": "it had been tucked away by mistake",
        "budget_item": "fresh copies",
        "budget_cost": 4,
        "resolution": "the lost pages were found, so nobody had to print extras",
    },
}

CHILDREN = [
    ("Maya", "girl"),
    ("Noah", "boy"),
    ("Lena", "girl"),
    ("Theo", "boy"),
    ("Iris", "girl"),
    ("Eli", "boy"),
]

HELPERS = [
    ("Grandma June", "woman"),
    ("Mr. Patel", "man"),
    ("Aunt Rose", "woman"),
    ("Father Ben", "man"),
]

TRAITS = ["gentle", "curious", "helpful", "thoughtful", "careful"]


# ---------------------------------------------------------------------------
# Story building
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming hymn mystery with a budget to protect.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["woman", "man"])
    ap.add_argument("--budget", type=int)
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


def _make_entity(name: str, typ: str, kind: str = "character") -> Entity:
    return Entity(id=name, kind=kind, type=typ, label=name, meters={}, memes={})


def reasonableness_gate(place: str, mystery: str, budget: int) -> None:
    if place not in PLACES:
        raise StoryError("Unknown place for this storyworld.")
    if mystery not in MYSTERIES:
        raise StoryError("Unknown mystery for this storyworld.")
    if budget < MYSTERIES[mystery]["budget_cost"]:
        raise StoryError(
            f"(No story: the budget is too small to matter here. "
            f"Try at least {MYSTERIES[mystery]['budget_cost']}.)"
        )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    place = args.place or rng.choice(sorted(PLACES))
    budget = args.budget if args.budget is not None else rng.randint(
        MYSTERIES[mystery]["budget_cost"], MYSTERIES[mystery]["budget_cost"] + 5
    )
    reasonableness_gate(place, mystery, budget)

    child_name, child_type = (args.child_name, args.child_type)
    if child_name is None or child_type is None:
        child_name, child_type = rng.choice(CHILDREN)

    helper_name, helper_type = (args.helper_name, args.helper_type)
    if helper_name is None or helper_type is None:
        helper_name, helper_type = rng.choice(HELPERS)

    if child_name == helper_name:
        raise StoryError("The child and helper must be different people.")

    return StoryParams(
        place=place,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
        mystery=mystery,
        budget=budget,
    )


def _setup(world: World, params: StoryParams) -> tuple[Entity, Entity, Entity]:
    child = world.add(_make_entity(params.child_name, params.child_type))
    helper = world.add(_make_entity(params.helper_name, params.helper_type))
    mystery = MYSTERIES[params.mystery]
    thing = world.add(Entity(
        id="missing_thing",
        kind="thing",
        type="item",
        label=mystery["thing"],
        phrase=mystery["thing"],
        owner="choir",
        caretaker=helper.id,
        meters={"missing": 1.0},
        memes={"worry": 1.0},
    ))
    world.facts.update(child=child, helper=helper, thing=thing, mystery=mystery, params=params)
    return child, helper, thing


def _narrate_setup(world: World, child: Entity, helper: Entity, thing: Entity, params: StoryParams) -> None:
    world.say(
        f"{child.id} was a gentle child who loved music, especially a warm old hymn "
        f"that filled {PLACES[params.place].place} with quiet smiles."
    )
    world.say(
        f"That evening, {child.id} and {helper.id} were getting ready for practice, "
        f"because the choir wanted a happy song and had only a small budget."
    )
    world.say(
        f"But then someone noticed {thing.label} was missing."
    )


def _investigate(world: World, child: Entity, helper: Entity, thing: Entity, mystery: dict, params: StoryParams) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1.0
    helper.memes["worry"] = helper.memes.get("worry", 0.0) + 1.0
    world.para()
    world.say(
        f"{child.id} looked carefully under the chairs and spotted {mystery['clue']}."
    )
    world.say(
        f"{helper.id} checked the budget notebook and sighed, because buying {mystery['budget_item']} "
        f"would cost {mystery['budget_cost']} coins."
    )
    world.say(
        f"They followed the clue through {params.place}, hoping the missing thing had only been misplaced."
    )
    thing.meters["missing"] = 0.0
    thing.meters["found"] = 1.0
    world.facts["clue"] = mystery["clue"]
    world.facts["cause"] = mystery["cause"]


def _reveal(world: World, child: Entity, helper: Entity, thing: Entity, mystery: dict, params: StoryParams) -> None:
    world.para()
    world.say(
        f"At last, {child.id} peeked {mystery['hide_spot']} and found {thing.label} at once."
    )
    world.say(
        f"It turned out that {mystery['cause']}, so the missing {thing.label} had never really been lost."
    )
    if params.budget >= mystery["budget_cost"]:
        world.say(
            f"Because the real book was found, the choir did not need to spend the budget on {mystery['budget_item']}."
        )
    helper.memes["relief"] = helper.memes.get("relief", 0.0) + 1.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
    world.facts["resolved"] = True


def _ending(world: World, child: Entity, helper: Entity, thing: Entity, params: StoryParams) -> None:
    world.para()
    world.say(
        f"Soon everyone sat together, singing the hymn from the found {thing.label} while the budget stayed safe."
    )
    world.say(
        f"{child.id} smiled when the final note floated through {PLACES[params.place].place}, "
        f"and {helper.id} set the money aside for another day."
    )
    world.say(
        f"It was a small mystery, but the happy ending made the whole room feel warmer."
    )


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    child, helper, thing = _setup(world, params)
    mystery = MYSTERIES[params.mystery]

    _narrate_setup(world, child, helper, thing, params)
    _investigate(world, child, helper, thing, mystery, params)
    _reveal(world, child, helper, thing, mystery, params)
    _ending(world, child, helper, thing, params)

    prompts = [
        f"Write a heartwarming story about a child, a hymn, and a budgetary mystery in {PLACES[params.place].place}.",
        f"Tell a gentle tale where {child.id} helps {helper.id} solve a mystery without spending too much money.",
        f"Write a short mystery story with a happy ending, a choir hymn, and a careful budget.",
    ]

    story_qa = [
        QAItem(
            question=f"Who helped {child.id} solve the mystery?",
            answer=f"{helper.id} helped {child.id} solve it by checking the clues and the budget notebook.",
        ),
        QAItem(
            question=f"What was missing in the story?",
            answer=f"{thing.label} was missing at first, but {child.id} found it by following the clue.",
        ),
        QAItem(
            question="Why did the budget matter?",
            answer=f"The choir did not want to waste coins on {mystery['budget_item']} if the real {thing.label} could be found.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a hymn?",
            answer="A hymn is a song sung in a church or community gathering, often to share hope, thanks, or comfort.",
        ),
        QAItem(
            question="What does budgetary mean?",
            answer="Budgetary means connected to a budget, which is a plan for how much money you can spend.",
        ),
        QAItem(
            question="Why do people look for clues in a mystery?",
            answer="People look for clues because clues can show what happened and help solve the mystery.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    for k, v in world.facts.items():
        if k in {"child", "helper", "thing", "mystery", "params"}:
            continue
        lines.append(f"  fact {k}={v}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
mystery(M) :- mystery_def(M).

needs_budget(M,C) :- mystery_cost(M,C).
budget_safe(B,M) :- needs_budget(M,C), B >= C.

missing_thing(M) :- mystery_def(M).
found_thing(M) :- found(M).

solved(M) :- missing_thing(M), found_thing(M), clue_seen(M), budget_safe(B,M).
happy_ending(M) :- solved(M).

#show solved/1.
#show happy_ending/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("setting", p))
    for m, d in MYSTERIES.items():
        lines.append(asp.fact("mystery_def", m))
        lines.append(asp.fact("mystery_cost", m, d["budget_cost"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _python_reasonable(params: StoryParams) -> bool:
    return params.place in PLACES and params.mystery in MYSTERIES and params.budget >= MYSTERIES[params.mystery]["budget_cost"]


def asp_verify() -> int:
    import asp
    program = asp_program("#show happy_ending/1.")
    model = asp.one_model(program)
    asp_ok = bool(asp.atoms(model, "happy_ending"))
    py_ok = _python_reasonable(StoryParams(place="hall", child_name="Maya", child_type="girl", helper_name="Grandma June", helper_type="woman", mystery="missing_hymnbook", budget=3))
    if asp_ok and py_ok:
        print("OK: ASP twin and Python gate both admit a happy ending.")
        return 0
    print("MISMATCH: ASP/Python parity failed.")
    return 1


def asp_facts_for_verify() -> str:
    return asp_facts()


# ---------------------------------------------------------------------------
# Selection / CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="hall", child_name="Maya", child_type="girl", helper_name="Grandma June", helper_type="woman", mystery="missing_hymnbook", budget=3),
    StoryParams(place="church", child_name="Noah", child_type="boy", helper_name="Father Ben", helper_type="man", mystery="missing_tin", budget=4),
    StoryParams(place="school", child_name="Lena", child_type="girl", helper_name="Mr. Patel", helper_type="man", mystery="missing_sheet_music", budget=5),
]


def build_sample_list(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        return [generate(p) for p in CURATED]
    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(50, args.n * 50):
        rng = random.Random(base + i)
        i += 1
        try:
            params = resolve_params(args, rng)
        except StoryError as e:
            raise e
        params.seed = base + i
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_ending/1."))
        print(facts_to_text(model, asp))
        return

    try:
        samples = build_sample_list(args)
    except StoryError as e:
        print(str(e))
        return

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


def facts_to_text(model, asp_mod) -> str:
    import asp
    atoms = asp.atoms(model, "happy_ending")
    if not atoms:
        return "No happy ending found."
    return f"{len(atoms)} happy ending(s) possible."


if __name__ == "__main__":
    main()
