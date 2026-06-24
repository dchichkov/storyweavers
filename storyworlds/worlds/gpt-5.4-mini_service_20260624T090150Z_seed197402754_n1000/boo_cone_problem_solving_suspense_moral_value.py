#!/usr/bin/env python3
"""
A small heartwarming storyworld about a boo and a cone problem.

Premise:
- A child hears a shy little boo from somewhere nearby.
- A bright cone is part of the problem, and it also becomes part of the fix.
- The story turns on careful observation, a gentle plan, suspense about what is hiding, and a moral choice to help.

This script is self-contained and uses a tiny stateful simulation to drive prose.
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
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    bearer: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = True
    details: str = ""


@dataclass
class Problem:
    id: str
    cause: str
    symptom: str
    suspense_hint: str
    clue: str
    fix_action: str
    solved_image: str
    risk_meter: str = "worry"
    reveal_meter: str = "known"


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    kind: str
    helps_with: set[str] = field(default_factory=set)
    requires: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paras: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paras[-1].append(text)
            self.lines.append(text)

    def para(self) -> None:
        if self.paras[-1]:
            self.paras.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paras if p)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "playroom": Place("the playroom", indoors=True, details="The rug was soft, and a toy shelf stood by the wall."),
    "hall": Place("the hall", indoors=True, details="The hall was quiet, with shoes lined up by the door."),
    "garden": Place("the garden", indoors=False, details="The garden had a little path and a bright patch of flowers."),
}

PROBLEMS = {
    "boo_in_box": Problem(
        id="boo_in_box",
        cause="a tiny creature hiding in a box",
        symptom="a soft boo from inside the box",
        suspense_hint="the box wiggled a little, as if something shy were inside",
        clue="a corner of a cone-shaped lid peeking up from the box",
        fix_action="open the box carefully and use the cone to guide the shy thing out",
        solved_image="the shy boo turned out to be a little bird with a stuck feather",
        risk_meter="worry",
        reveal_meter="known",
    ),
    "boo_under_cone": Problem(
        id="boo_under_cone",
        cause="a nervous puppy hiding under a cone",
        symptom="a little boo-boo sound under the cone",
        suspense_hint="the cone tipped once, then settled again",
        clue="soft paws printing dust around the cone",
        fix_action="lift the cone slowly and let the puppy see a safe hand first",
        solved_image="the puppy wagged its tail and licked the child's palm",
        risk_meter="worry",
        reveal_meter="known",
    ),
    "boo_by_gate": Problem(
        id="boo_by_gate",
        cause="a worried friend stuck behind a gate",
        symptom="a lonely boo carried through the bars",
        suspense_hint="something on the other side kept tugging the gate gently",
        clue="a cone left nearby like a marker for help",
        fix_action="use the cone as a pointer, then find the latch and open the gate",
        solved_image="the friend stepped out and smiled with watery eyes",
        risk_meter="worry",
        reveal_meter="known",
    ),
}

AIDS = {
    "cone": Aid(
        id="cone",
        label="cone",
        phrase="a bright orange cone",
        kind="thing",
        helps_with={"point", "shield", "guide"},
        requires={"care"},
    ),
    "blanket": Aid(
        id="blanket",
        label="blanket",
        phrase="a soft blanket",
        kind="thing",
        helps_with={"comfort", "shield"},
        requires={"gentle"},
    ),
    "flashlight": Aid(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        kind="thing",
        helps_with={"look", "find"},
        requires={"patience"},
    ),
}

NAMES = ["Mia", "Ava", "Noah", "Leo", "Ivy", "Zoe", "Milo", "Eli"]
GENDERS = ["girl", "boy"]
PARENTS = ["mother", "father"]
TRAITS = ["gentle", "careful", "kind", "brave", "patient"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------
def has_reasonable_fix(problem: Problem, aid: Aid) -> bool:
    if problem.id == "boo_in_box":
        return "guide" in aid.helps_with and "care" in aid.requires
    if problem.id == "boo_under_cone":
        return "shield" in aid.helps_with and "gentle" in aid.requires
    if problem.id == "boo_by_gate":
        return "find" in aid.helps_with and "patience" in aid.requires
    return False


def resolve_aid(problem: Problem) -> Aid:
    for aid in AIDS.values():
        if has_reasonable_fix(problem, aid):
            return aid
    raise StoryError("No reasonable aid exists for this problem.")


def setup_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    prob = PROBLEMS[params.problem]
    world = World(place)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="parent"))
    target = world.add(Entity(id="boo", kind="thing", type="boo", label="boo", phrase=prob.symptom))
    cone = world.add(Entity(id="cone", kind="thing", type="cone", label="cone", phrase=AIDS["cone"].phrase))
    aid = world.add(Entity(id="aid", kind="thing", type="cone", label="cone", phrase=AIDS["cone"].phrase))
    world.facts.update(child=child, parent=parent, target=target, cone=cone, aid=aid, problem=prob, place=place)
    return world


def predict_resolution(world: World, problem: Problem, aid: Aid) -> bool:
    return has_reasonable_fix(problem, aid)


def tell_story(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    prob: Problem = f["problem"]
    place: Place = f["place"]
    aid = resolve_aid(prob)
    child.memes["curious"] = 1
    child.memes["care"] = 1
    child.meters["worry"] = 0
    world.say(f"{child.id} was a {world.facts['child'].pronoun('subject') == 'she' and 'little girl' or 'little boy'} who liked quiet places and kind plans.")
    world.say(f"One day at {place.name}, {child.id} heard a soft boo.")
    world.say(place.details)
    world.para()

    child.meters["worry"] += 1
    child.memes["suspense"] = 1
    world.say(f"The boo came from somewhere hard to see. {prob.suspense_hint}.")
    world.say(f"{child.id} looked and listened, but the sound stayed hidden.")
    world.say(f"{prob.clue.capitalize()}.")
    world.para()

    world.say(f'"Let’s be careful," {parent.pronoun("subject")} said, and {child.id} nodded.')
    if not predict_resolution(world, prob, aid):
        raise StoryError("The selected aid does not actually solve the problem.")
    world.say(f"{child.id} found {aid.phrase} and used it with care.")
    world.say(f"That helped {prob.fix_action}.")
    world.say(f"At last, {prob.solved_image}.")
    child.meters["worry"] = 0
    child.memes["suspense"] = 0
    child.memes["joy"] = 1
    child.memes["moral_value"] = 1
    world.facts["aid_used"] = aid
    world.facts["solved"] = True


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts are emitted from the Python registries.
% The declarative twin models whether a problem has a reasonable fix.

reasonable_aid(P, A) :- problem(P), aid(A), fixable(P, A).
solvable(P) :- problem(P), reasonable_aid(P, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for aid in AIDS.values():
        lines.append(asp.fact("aid", aid.id))
        for h in sorted(aid.helps_with):
            lines.append(asp.fact("helps_with", aid.id, h))
        for r in sorted(aid.requires):
            lines.append(asp.fact("requires", aid.id, r))
    for pid, prob in PROBLEMS.items():
        for aid in AIDS.values():
            if has_reasonable_fix(prob, aid):
                lines.append(asp.fact("fixable", pid, aid.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_solvable() -> set[str]:
    import asp
    model = asp.one_model(asp_program("#show solvable/1."))
    return {pid for (pid,) in asp.atoms(model, "solvable")}


def asp_verify() -> int:
    python_set = {pid for pid, prob in PROBLEMS.items() if any(has_reasonable_fix(prob, a) for a in AIDS.values())}
    clingo_set = asp_solvable()
    if python_set == clingo_set:
        print(f"OK: ASP and Python agree on solvable problems ({len(python_set)}).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("python:", sorted(python_set))
    print("asp:", sorted(clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    prob: Problem = f["problem"]
    child: Entity = f["child"]
    return [
        f'Write a heartwarming story for a young child that includes the words "boo" and "cone".',
        f"Tell a gentle mystery about {child.id} hearing a boo at {world.place.name} and using a cone to help.",
        f"Write a short suspenseful story with a kind ending where a child solves a boo problem carefully.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    prob: Problem = f["problem"]
    aid: Aid = f["aid_used"]
    return [
        QAItem(
            question=f"What did {child.id} hear at the start of the story?",
            answer=f"{child.id} heard a soft boo at {world.place.name}.",
        ),
        QAItem(
            question=f"What made the story feel suspenseful before the problem was solved?",
            answer=f"The sound stayed hidden, and {prob.suspense_hint}.",
        ),
        QAItem(
            question=f"How did the cone help {child.id} solve the problem?",
            answer=f"{child.id} used the cone with care to {prob.fix_action}.",
        ),
        QAItem(
            question=f"What changed at the end after the kind solution?",
            answer=f"The hidden boo was understood and {prob.solved_image}. {child.id} felt calm and happy afterward.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "cone": (
        "What is a cone?",
        "A cone is a shape that points up to a small top and widens at the bottom. "
        "You can use cone-shaped objects to point, guide, or block a space.",
    ),
    "boo": (
        "What does a boo sound like?",
        "A boo can be a soft sound someone makes when they are shy, scared, or trying to get attention gently.",
    ),
}


def world_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE.values()]


# ---------------------------------------------------------------------------
# Generation / emit
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming boo-and-cone storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENTS)
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
    problem = args.problem or rng.choice(list(PROBLEMS))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    lines.append(f"place={world.place.name}")
    lines.append(f"facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== story qa ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world qa ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


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
        print(asp_program("#show solvable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solvable/1."))
        vals = sorted({pid for (pid,) in asp.atoms(model, "solvable")})
        print(f"{len(vals)} solvable problems:")
        for v in vals:
            print(f"  {v}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in PLACES:
            for problem in PROBLEMS:
                params = StoryParams(place=place, problem=problem, name="Mia", gender="girl", parent="mother", trait="kind")
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        if len(samples) > 1:
            header = f"### story {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
