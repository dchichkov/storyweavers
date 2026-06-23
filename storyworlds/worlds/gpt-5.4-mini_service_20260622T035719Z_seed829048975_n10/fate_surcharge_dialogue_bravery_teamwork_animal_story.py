#!/usr/bin/env python3
"""
storyworlds/worlds/fate_surcharge_dialogue_bravery_teamwork_animal_story.py
===========================================================================

A small animal storyworld: a brave animal crew faces a tiny unfair surcharge,
talks it through, and solves it with teamwork.

Seed tale:
---
Milo the mouse and Pip the pigeon wanted to cross the river to bring berries to
Grandma Tula the turtle. But the ferry keeper said there was a surprise
surcharge for anyone carrying a basket. Milo worried the berries would never
arrive. Pip puffed up and said, "Then we will find another way!" The friends
worked together, built a little raft from reeds, and carried the berries across
the river. Grandma Tula smiled, and Milo said the day's fate had turned kindly
after all.

Contract focus:
- typed entities with meters and memes
- dialogue, bravery, teamwork
- state-driven conflict and resolution
- inline ASP twin plus Python reasonableness gate
- child-facing QA grounded in world state
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str | None = None
    caretaker: str | None = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id


@dataclass
class StoryParams:
    animal1: str
    animal2: str
    helper: str
    name1: str
    name2: str
    place: str
    prize: str
    fee_word: str
    seed: Optional[int] = None


@dataclass
class AnimalSpec:
    kind: str
    label: str
    phrase: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class PlaceSpec:
    place: str
    needs_crossing: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class ProblemSpec:
    id: str
    label: str
    surcharge: str
    fear: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SolutionSpec:
    id: str
    label: str
    prep: str
    payoff: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: PlaceSpec) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, ...]] = set()

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

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = {k: v for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.history = list(self.history)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def _add_sentence(world: World, sentence: str) -> None:
    world.say(sentence)
    world.event("say", sentence=sentence)


def _r_boat_ready(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("raft_ready") and not world.facts.get("crossed"):
        key = ("team_cross",)
        if key in world.fired:
            return out
        world.fired.add(key)
        for eid in ("hero1", "hero2"):
            world.get(eid).memes["teamwork"] += 1
        out.append("teamwork_strengthened")
    return out


CAUSAL_RULES = [ _r_boat_ready ]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            if s == "teamwork_strengthened":
                _add_sentence(world, "Working together made their paws and wings steadier.")
    return out


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in PLACES:
        for problem in PROBLEMS:
            for sol in SOLUTIONS:
                if problem in PLACE_PROBLEMS[place].affords and problem in PROBLEM_SOLUTIONS and sol in PROBLEM_SOLUTIONS[problem]:
                    combos.append((place, problem, sol))
    return combos


def reason_ok(place: str, problem: str, solution: str) -> bool:
    return (place, problem, solution) in valid_combos()


def explain_rejection(place: str, problem: str, solution: str) -> str:
    return f"(No story: {place} does not support a reasonable {problem} and {solution} pairing.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        for pr in PLACE_PROBLEMS[p].affords:
            lines.append(asp.fact("affords", p, pr))
    for pr in PROBLEMS:
        lines.append(asp.fact("problem", pr))
        lines.append(asp.fact("fee", pr, PROBLEMS[pr].surcharge))
    for s in SOLUTIONS:
        lines.append(asp.fact("solution", s))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Pr, S) :- place(P), problem(Pr), solution(S), affords(P, Pr), allowed(Pr, S).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class StoryWorldFacts:
    hero1: Entity
    hero2: Entity
    helper: Entity
    place: PlaceSpec
    problem: ProblemSpec
    solution: SolutionSpec
    prize: Entity


def tell(world: World, hero1: Entity, hero2: Entity, helper: Entity, problem: ProblemSpec, solution: SolutionSpec, prize: Entity) -> World:
    hero1.memes["bravery"] += 1
    hero2.memes["bravery"] += 1
    _add_sentence(world, f"At {world.place.place}, {hero1.ref()} and {hero2.ref()} met by the ferry dock with a little basket of {prize.label}.")
    _add_sentence(world, f'The ferry keeper pointed to a sign and said, "There is a {problem.surcharge} for baskets today."')
    _add_sentence(world, f'{hero1.ref()} frowned. "That is not fair," {hero1.pronoun()} said, and {hero2.ref()} puffed up bravely. "Maybe fate wants us to try harder," {hero2.pronoun()} said.')
    _add_sentence(world, f'{helper.ref()} nodded. "{solution.prep}," {helper.pronoun()} said. "We can still get the berries across."')
    world.para()
    hero1.memes["fear"] += 1
    hero2.memes["hope"] += 1
    _add_sentence(world, f"They gathered reeds, tied them with grass, and made a tiny raft that could carry the basket without paying the extra surcharge.")
    world.facts["raft_ready"] = True
    propagate(world, narrate=True)
    _add_sentence(world, f'{hero1.ref()} and {hero2.ref()} took turns pushing the raft, and {helper.ref()} balanced the basket while the water rippled beside them.')
    _add_sentence(world, f"By the far bank, {problem.label} had lost its sting, and the berries arrived safe for Grandma Tula.")
    world.para()
    _add_sentence(world, f'{hero1.ref()} smiled. "Maybe that was our fate after all," {hero1.pronoun()} said. "{solution.payoff}."')
    hero1.memes["joy"] += 1
    hero2.memes["joy"] += 1
    helper.memes["pride"] += 1
    world.facts.update(hero1=hero1, hero2=hero2, helper=helper, place=world.place, problem=problem, solution=solution, prize=prize, crossed=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story for a young child that includes the words "{f["problem"].id}" and "fate", with a gentle surprise and a teamwork ending.',
        f"Tell a brave little story about {f['hero1'].id} and {f['hero2'].id} helping a friend cross {f['place'].place} after a {f['problem'].surcharge}.",
        f'Write an animal story where a keeper mentions a "{f["problem"].surcharge}" and the animals answer with dialogue, bravery, and teamwork.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h1, h2, helper, problem, solution, prize = f["hero1"], f["hero2"], f["helper"], f["problem"], f["solution"], f["prize"]
    return [
        QAItem(
            question=f"Why did {h1.ref()} worry at {f['place'].place}?",
            answer=f"{h1.ref()} worried because the ferry keeper asked for a {problem.surcharge} on the basket. That made the trip feel hard at first, but the animals did not give up.",
        ),
        QAItem(
            question=f"How did {h2.ref()} show bravery when the surcharge was announced?",
            answer=f"{h2.ref()} answered with a brave voice and helped look for a new plan. The courage was not loud for its own sake; it helped the friends keep going together.",
        ),
        QAItem(
            question=f"What did the three friends do to solve the problem?",
            answer=f"They built a little raft from reeds and tied it with grass so the basket could cross without the extra fee. Teamwork turned the mistake into a working plan.",
        ),
        QAItem(
            question=f"What happened to the berries by the end?",
            answer=f"The berries reached Grandma Tula safe and dry. That ending shows the fate of the day changed because the animals worked together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["problem"].id, world.facts["solution"].id}
    out: list[QAItem] = []
    if "surcharge" in tags:
        out.append(QAItem("What is a surcharge?", "A surcharge is an extra fee added on top of the usual price. People pay it when there is a special reason or rule." ))
    out.append(QAItem("What does teamwork mean?", "Teamwork means people or animals help each other to finish something together. Each one does a small part so the whole job gets done."))
    out.append(QAItem("What does bravery mean?", "Bravery means doing the right thing even when you feel worried. It does not mean you never feel scared."))
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  history events: {len(world.history)}")
    return "\n".join(lines)


PLACES = ["river_dock", "market_bridge", "reed_crossing"]
PROBLEMS: dict[str, ProblemSpec] = {
    "surcharge": ProblemSpec(id="surcharge", label="surcharge", surcharge="basket surcharge", fear="extra fee", tags={"money", "fee"}),
    "mud": ProblemSpec(id="mud", label="mud", surcharge="mud fee", fear="sticky boots", tags={"mess"}),
}
SOLUTIONS: dict[str, SolutionSpec] = {
    "raft": SolutionSpec(id="raft", label="raft", prep="Let's build a little raft from reeds", payoff="they crossed on the raft", tags={"teamwork"}),
    "bridge": SolutionSpec(id="bridge", label="bridge", prep="Let's make a small bridge with boards", payoff="the bridge carried the basket", tags={"teamwork"}),
}
PLACE_PROBLEMS: dict[str, PlaceSpec] = {
    "river_dock": PlaceSpec(place="the river dock", affords={"surcharge"}),
    "market_bridge": PlaceSpec(place="the market bridge", affords={"surcharge", "mud"}),
    "reed_crossing": PlaceSpec(place="the reed crossing", affords={"surcharge"}),
}
PROBLEM_SOLUTIONS = {"surcharge": {"raft", "bridge"}, "mud": {"bridge"}}

ANIMALS = {
    "mouse": AnimalSpec(kind="mouse", label="mouse", phrase="a tiny mouse"),
    "pigeon": AnimalSpec(kind="pigeon", label="pigeon", phrase="a plump pigeon"),
    "rabbit": AnimalSpec(kind="rabbit", label="rabbit", phrase="a quick rabbit"),
    "turtle": AnimalSpec(kind="turtle", label="turtle", phrase="a slow turtle"),
}
NAMES = ["Milo", "Pip", "Nora", "Tia", "Ollie", "Wren", "Bea", "Coco"]


def valid_story_params() -> list[tuple[str, str, str]]:
    return valid_combos()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (not getattr(args, "place", None) or c[0] == args.place)
              and (not getattr(args, "problem", None) or c[1] == args.problem)
              and (not getattr(args, "solution", None) or c[2] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, solution = rng.choice(sorted(combos))
    a1, a2 = rng.sample(sorted(ANIMALS), 2)
    h1, h2 = rng.sample(NAMES, 2)
    helper = "Grandma Tula"
    return StoryParams(animal1=a1, animal2=a2, helper=helper, name1=h1, name2=h2, place=place, prize="berries", fee_word=problem, seed=None)


def generate(params: StoryParams) -> StorySample:
    if params.fee_word not in PROBLEMS:
        raise StoryError("Unknown fee word.")
    problem = PROBLEMS[params.fee_word]
    if params.place not in PLACE_PROBLEMS:
        raise StoryError("Unknown place.")
    place = PLACE_PROBLEMS[params.place]
    if params.prize != "berries":
        raise StoryError("This storyworld only tells berry-carrying tales.")
    solution = SOLUTIONS["raft" if params.place != "market_bridge" else "bridge"]
    if not reason_ok(params.place, problem.id, solution.id):
        raise StoryError(explain_rejection(params.place, problem.id, solution.id))
    world = World(place)
    hero1 = world.add(Entity(id=params.name1, kind="character", type=params.animal1, label=params.name1, phrase=ANIMALS[params.animal1].phrase, traits=["brave"], role="leader"))
    hero2 = world.add(Entity(id=params.name2, kind="character", type=params.animal2, label=params.name2, phrase=ANIMALS[params.animal2].phrase, traits=["helpful"], role="helper"))
    helper = world.add(Entity(id=params.helper, kind="character", type="turtle", label=params.helper, phrase="Grandma Tula", traits=["kind"], role="helper"))
    prize = world.add(Entity(id="berries", kind="thing", type="berries", label="berries", phrase="a basket of berries", owner=hero1.id))
    world.facts["raft_ready"] = False
    tell(world, hero1, hero2, helper, problem, solution, prize)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld with fate, surcharge, bravery, and teamwork.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("-n", "--n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


CURATED = [
    StoryParams(animal1="mouse", animal2="pigeon", helper="Grandma Tula", name1="Milo", name2="Pip", place="river_dock", prize="berries", fee_word="surcharge"),
    StoryParams(animal1="rabbit", animal2="turtle", helper="Grandma Tula", name1="Nora", name2="Wren", place="reed_crossing", prize="berries", fee_word="surcharge"),
]


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = py == cl
    sample_ok = True
    try:
        _ = generate(CURATED[0])
    except Exception:
        sample_ok = False
    if ok and sample_ok:
        print(f"OK: ASP matches Python ({len(py)} combos) and generate() smoke test passed.")
        return 0
    if not ok:
        print("MISMATCH between ASP and Python valid combos.")
        print("python only:", sorted(py - cl))
        print("asp only:", sorted(cl - py))
    if not sample_ok:
        print("Smoke test failed: generate() crashed.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
