#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/ant_mystery_to_solve_bad_ending_fable.py
===============================================================================================================

A small fable-like story world about an ant who tries to solve a mystery,
but the ending turns bad.

Premise:
- An ant finds a trail of missing crumbs and wants to discover who took them.
- The ant investigates with tiny tools and questions of neighbors.
- The clues point the wrong way; the ant grows stubborn and wastes time.
- In the end, the real culprit is never stopped, and the ant loses the chance
  to save the nest's supper.

The world is built to feel like a fable:
- short, concrete cast
- a moral pressure around pride, patience, and listening
- a clear lesson implied by the bad ending

The story model uses physical meters and emotional memes, and the prose is driven
by simulated state rather than by a frozen paragraph with swapped nouns.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"ant", "queen"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"beetle", "spider", "mouse", "cricket"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    kind: str
    hiding: bool = False
    crumbs: int = 0
    trails: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    nest: str
    clue: str
    culprit: str
    ant_name: str
    helper: str
    seed: Optional[int] = None


@dataclass
class World:
    nest: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    places: dict[str, Place] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        import copy
        clone = World(nest=copy.deepcopy(self.nest))
        clone.entities = copy.deepcopy(self.entities)
        clone.places = copy.deepcopy(self.places)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "nest": Place(id="nest", label="the nest", kind="home", crumbs=0),
    "path": Place(id="path", label="the mossy path", kind="trail", hiding=False, crumbs=1, trails={"footprint"}),
    "stump": Place(id="stump", label="the hollow stump", kind="hiding", hiding=True, crumbs=2, trails={"broken_leaf"}),
    "kitchen": Place(id="kitchen", label="the picnic kitchen", kind="food", hiding=False, crumbs=3, trails={"sugar"}),
}

CLUES = {
    "footprint": "a small footprint",
    "broken_leaf": "a broken leaf",
    "sugar": "a trail of sugar dust",
}

CULPRITS = {
    "beetle": "a beetle",
    "mouse": "a mouse",
    "cricket": "a cricket",
}

HELPERS = {
    "snail": "a slow snail",
    "mole": "a blind mole",
    "bee": "a busy bee",
}

ANT_NAMES = ["Ari", "Mina", "Tio", "Luz", "Pip", "Nia"]


# ---------------------------------------------------------------------------
# Fable world model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def clean_state() -> World:
    world = World(nest=PLACES["nest"])
    world.places = {k: v for k, v in PLACES.items()}
    return world


def _accuse(world: World, ant: Entity, target: Entity) -> None:
    target.memes["worry"] = target.memes.get("worry", 0.0) + 1
    ant.memes["certainty"] = ant.memes.get("certainty", 0.0) + 0.5


def _investigate(world: World, ant: Entity, clue: str) -> None:
    ant.meters["steps"] = ant.meters.get("steps", 0.0) + 1
    ant.meters["time"] = ant.meters.get("time", 0.0) + 1
    ant.memes["curiosity"] = ant.memes.get("curiosity", 0.0) + 1
    ant.memes["stubbornness"] = ant.memes.get("stubbornness", 0.0) + 1
    world.facts["last_clue"] = clue


def _bad_turn(world: World, ant: Entity) -> None:
    ant.memes["regret"] = ant.memes.get("regret", 0.0) + 1
    ant.meters["missed_chance"] = ant.meters.get("missed_chance", 0.0) + 1


def tell(params: StoryParams) -> World:
    world = clean_state()
    ant = world.add(Entity(id=params.ant_name, kind="character", type="ant", label=params.ant_name))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper, label=params.helper))
    culprit = world.add(Entity(id=params.culprit, kind="character", type=params.culprit, label=params.culprit))
    world.facts.update(ant=ant, helper=helper, culprit=culprit, params=params)

    # Act 1: the mystery is born.
    world.say(f"Once there was a little ant named {ant.id} who found the nest's supper nearly gone.")
    world.say(f"Only crumbs remained, and one small clue waited in {world.places[params.nest].label}.")

    # Act 2: investigation.
    world.para()
    world.say(f"{ant.id} followed {params.clue} to {world.places['path'].label}.")
    _investigate(world, ant, params.clue)
    world.say(f"{ant.id} asked {helper.id} for help, but {helper.id} could only point toward the {world.places['stump'].label}.")
    world.say(f"{ant.id} then blamed {culprit.id} at once, without waiting to see the whole trail.")
    _accuse(world, ant, culprit)

    # Act 3: bad ending.
    world.para()
    world.say(f"While {ant.id} argued, the true crumbs were carried off from the {world.places['kitchen'].label}.")
    _bad_turn(world, ant)
    world.say(f"When {ant.id} finally reached the right place, the food was gone, and the nest went hungry.")
    world.say(f"So the ant learned too late that pride can hide a truth more deeply than a shadow.")

    world.facts.update(
        lost_food=True,
        bad_ending=True,
        clue=params.clue,
        place=params.nest,
        helper_id=params.helper,
        culprit_id=params.culprit,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short fable for children about an ant named {p.ant_name} who tries to solve a mystery about missing crumbs.',
        f'Tell a gentle but sad story where {p.ant_name} follows the clue "{p.clue}" and learns a lesson too late.',
        f'Write a simple animal fable with an ant, a helper, and a bad ending about food that disappears.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    ant = world.facts["ant"]
    helper = world.facts["helper"]
    culprit = world.facts["culprit"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about a little ant named {ant.id} who tried to solve a mystery about missing crumbs.",
        ),
        QAItem(
            question=f"What clue did {ant.id} follow?",
            answer=f"{ant.id} followed {p.clue} first, but that clue did not lead to the truth right away.",
        ),
        QAItem(
            question=f"Why did the story end badly?",
            answer=f"It ended badly because {ant.id} spent too long arguing and blaming others, so the nest's food was gone by the time the truth was found.",
        ),
        QAItem(
            question=f"Who tried to help {ant.id}?",
            answer=f"{helper.id} tried to help, but the help came too late to stop the lost supper.",
        ),
        QAItem(
            question=f"Who was the culprit?",
            answer=f"The real culprit was {culprit.id}, but {ant.id} did not catch {culprit.pronoun('object')} in time.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something confusing or hidden that needs clues and careful thinking to understand.",
        ),
        QAItem(
            question="What does a careful helper do in a mystery?",
            answer="A careful helper looks at clues, listens well, and helps solve the problem without guessing too fast.",
        ),
        QAItem(
            question="What lesson does this fable suggest?",
            answer="It suggests that pride and rushing to blame others can make a problem worse.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reasonableness gate and ASP twin
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for nest_id, nest in PLACES.items():
        for clue in CLUES:
            for culprit in CULPRITS:
                if nest.hiding or nest.crumbs > 0:
                    out.append((nest_id, clue, culprit))
    return out


ASP_RULES = r"""
place(nest;path;stump;kitchen).
clue(footprint;broken_leaf;sugar).
culprit(beetle;mouse;cricket).

good_place(P) :- place(P), P != nest.
valid(P,C,U) :- good_place(P), clue(C), culprit(U).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.hiding:
            lines.append(asp.fact("hiding", pid))
        if place.crumbs:
            lines.append(asp.fact("crumbs", pid, place.crumbs))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for u in CULPRITS:
        lines.append(asp.fact("culprit", u))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    nest: str
    clue: str
    culprit: str
    ant_name: str
    helper: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like ant mystery with a bad ending.")
    ap.add_argument("--nest", choices=PLACES.keys())
    ap.add_argument("--clue", choices=CLUES.keys())
    ap.add_argument("--culprit", choices=CULPRITS.keys())
    ap.add_argument("--ant-name")
    ap.add_argument("--helper", choices=HELPERS.keys())
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
    if args.nest:
        combos = [c for c in combos if c[0] == args.nest]
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if args.culprit:
        combos = [c for c in combos if c[2] == args.culprit]
    if not combos:
        raise StoryError("No valid story combination matches those options.")
    nest, clue, culprit = rng.choice(sorted(combos))
    ant_name = args.ant_name or rng.choice(ANT_NAMES)
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(nest=nest, clue=clue, culprit=culprit, ant_name=ant_name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
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


def valid_story_params() -> list[StoryParams]:
    return [
        StoryParams(nest="stump", clue="footprint", culprit="beetle", ant_name="Ari", helper="snail"),
        StoryParams(nest="path", clue="broken_leaf", culprit="mouse", ant_name="Mina", helper="mole"),
        StoryParams(nest="kitchen", clue="sugar", culprit="cricket", ant_name="Tio", helper="bee"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} valid combinations:")
        for row in vals:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in valid_story_params()]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
