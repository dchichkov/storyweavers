#!/usr/bin/env python3
"""
storyworlds/worlds/seep_repetition_slice_of_life.py
====================================================

A small slice-of-life story world about a household routine, a repeated tiny
problem, and a gentle fix.

Premise:
- A careful child tends a windowsill plant every morning.
- Water slowly seeps from the pot, then again and again on different days.
- The parent notices the repeated damp ring, and they solve it with a tray and
  a smaller pour.

The world models:
- physical meters: wet, soggy, tired, full
- emotional memes: worry, patience, relief, pride, fondness

The story is intentionally modest and grounded: a small household scene with a
clear repeated turn and a satisfying ending image.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    label: str
    morning_light: str
    routine: str


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    repeat_phrase: str
    mess: str
    sign: str
    cause: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    phrase: str
    applies: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    problem: str
    solution: str
    name: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.events: list[str] = []

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.events = list(self.events)
        w.paragraphs = [[]]
        return w


def _narrate_repeat(world: World, problem: Problem, actor: Entity, thing: Entity) -> None:
    world.say(
        f"Each morning, {actor.id} checked the {thing.label}, and each morning "
        f"the same small drip came back."
    )
    world.say(
        f"The water would {problem.verb} from the pot and leave the {problem.sign} "
        f"again on the sill."
    )


def _apply_seep(world: World) -> list[str]:
    out = []
    plant = world.entities.get("plant")
    sill = world.entities.get("sill")
    tray = world.entities.get("tray")
    if not plant or not sill:
        return out
    if world.facts.get("solved"):
        return out
    if tray and tray.meters.get("full", 0) >= THRESHOLD:
        return out
    plant.meters["wet"] = plant.meters.get("wet", 0) + 1
    sill.meters["wet"] = sill.meters.get("wet", 0) + 1
    out.append("A little water seeped out again and darkened the sill.")
    return out


ASP_RULES = r"""
problem_occurs(seep) :- seep.
repeats(seep) :- problem_occurs(seep).
solved_by(tray) :- tray.
"""


@dataclass
class Rule:
    name: str
    apply: callable


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                if narrate:
                    for s in items:
                        world.say(s)


CAUSAL_RULES = [Rule("seep", _apply_seep)]


SETTINGS = {
    "kitchen": Place(
        label="the kitchen windowsill",
        morning_light="soft morning light",
        routine="breakfast and watering time",
    ),
    "hall": Place(
        label="the hallway table",
        morning_light="thin morning light",
        routine="tidying and starting the day",
    ),
    "sunroom": Place(
        label="the sunroom shelf",
        morning_light="warm morning light",
        routine="quiet tea and checking the plants",
    ),
}

PROBLEMS = {
    "seep": Problem(
        id="seep",
        verb="seep",
        gerund="seeping",
        repeat_phrase="again and again",
        mess="wet",
        sign="damp ring",
        cause="the pot held too much water after each watering",
        fix="put a tray under the pot and pour a little less",
        tags={"water", "repeat", "plant"},
    )
}

SOLUTIONS = {
    "tray": Solution(
        id="tray",
        label="a shallow tray",
        phrase="a shallow tray for the plant",
        applies="under the pot",
        effect="caught the drips before they reached the wood",
        tags={"water", "plant", "repeat"},
    ),
    "mat": Solution(
        id="mat",
        label="a cloth mat",
        phrase="a cloth mat for under the pot",
        applies="under the pot",
        effect="soaked up the drips before they spread",
        tags={"water", "plant"},
    ),
}

NAMES_GIRL = ["Mina", "Ivy", "Nora", "Lina", "Sana", "Maya"]
NAMES_BOY = ["Eli", "Noah", "Owen", "Toby", "Finn", "Leo"]
TRAITS = ["careful", "quiet", "patient", "gentle", "thoughtful", "tidy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for prob in PROBLEMS:
            for sol in SOLUTIONS:
                combos.append((place, prob, sol))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.problem:
        combos = [c for c in combos if c[1] == args.problem]
    if args.solution:
        combos = [c for c in combos if c[2] == args.solution]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, solution = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    adult = args.adult or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, solution=solution, name=name, gender=gender, adult=adult, trait=trait)


def build_world(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    prob = PROBLEMS[params.problem]
    sol = SOLUTIONS[params.solution]
    w = World(place)
    child = w.add(Entity(id=params.name, kind="character", type=params.gender, meters={"wet": 0}, memes={"worry": 0, "patience": 1}))
    adult = w.add(Entity(id="Adult", kind="character", type=params.adult, label=f"the {params.adult}", meters={"tired": 0}, memes={"patience": 1, "relief": 0}))
    plant = w.add(Entity(id="plant", type="plant", label="small plant", phrase="a small green plant", owner=child.id, caretaker=adult.id, meters={"wet": 0}))
    sill = w.add(Entity(id="sill", type="surface", label="windowsill", phrase="the painted sill", meters={"wet": 0}))
    tray = w.add(Entity(id="tray", type="tray", label=sol.label, phrase=sol.phrase, owner=adult.id, meters={"full": 0}))
    w.facts.update(child=child, adult=adult, plant=plant, sill=sill, tray=tray, problem=prob, solution=sol)
    return w


def tell(w: World) -> None:
    f = w.facts
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    plant: Entity = f["plant"]
    sill: Entity = f["sill"]
    tray: Entity = f["tray"]
    prob: Problem = f["problem"]
    sol: Solution = f["solution"]

    w.say(f"{child.id} liked the little plant on {w.place.label}.")
    w.say(f"The plant sat there in {w.place.morning_light}, part of the family's {w.place.routine}.")
    w.say(f"{child.id} watered it carefully, because {child.pronoun('subject')} wanted to help.")
    w.say(f"But the pot would {prob.verb} at the edge, {prob.repeat_phrase}, and leave a {prob.sign}.")

    w.para()
    _narrate_repeat(w, prob, child, plant)
    w.say(f"One day, {adult.label} noticed the {prob.sign} and wiped the sill with a cloth.")
    w.say(f'"It keeps happening," {adult.pronoun("subject")} said, and {child.id} nodded.')

    child.memes["worry"] += 1
    adult.memes["patience"] += 1

    w.para()
    w.say(f"{adult.label} looked at the pot and said, \"The water is {prob.cause}.\"")
    w.say(f'"We can {prob.fix}," {adult.pronoun("subject")} said, and {child.id} liked that idea.')
    tray.meters["full"] = 1
    child.memes["worry"] = 0
    adult.memes["relief"] += 1
    w.facts["solved"] = True
    w.say(f"They put {sol.label} {sol.applies}, and after that the drips landed there instead of on the wood.")
    w.say(f"Now the sill stayed dry, and the plant still got its drink.")
    w.say(f"At the end of the morning, {child.id} smiled at the neat tray and the clean sill.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    prob: Problem = f["problem"]
    child: Entity = f["child"]
    return [
        f'Write a small slice-of-life story about a child named {child.id}, a plant, and a tiny problem that keeps {prob.gerund}.',
        f"Tell a gentle family story where the same damp ring appears {prob.repeat_phrase} and someone finds a practical fix.",
        f'Write a story for young children that includes the word "{prob.id}" and ends with a calm household routine.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    prob: Problem = f["problem"]
    sol: Solution = f["solution"]
    return [
        QAItem(
            question=f"What did {child.id} notice happening to the sill?",
            answer=f"{child.id} noticed a damp ring and little wet marks because the water kept {prob.gerund} from the pot.",
        ),
        QAItem(
            question=f"Why did {adult.label} think the problem kept coming back?",
            answer=f"{adult.label} saw that the pot held too much water after watering, so the extra water kept {prob.verb} out again.",
        ),
        QAItem(
            question=f"What did they do to help keep the wood dry?",
            answer=f"They put {sol.label} under the pot and poured a little less water, so the drips stayed in the tray.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt happy and calm, because the plant was cared for and the sill stayed clean and dry.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a tray do when something leaks a little?",
            answer="A tray catches drips and keeps them from spreading across the table or sill.",
        ),
        QAItem(
            question="Why is a repeated small problem important to notice?",
            answer="If the same little problem keeps happening, people can fix the cause instead of cleaning the mess over and over.",
        ),
        QAItem(
            question="What is seep?",
            answer="To seep means to slowly move through a tiny opening or crack, like water slipping out little by little.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", problem="seep", solution="tray", name="Mina", gender="girl", adult="mother", trait="careful"),
    StoryParams(place="sunroom", problem="seep", solution="mat", name="Eli", gender="boy", adult="grandmother", trait="patient"),
]


def explain_rejection() -> str:
    return "(No story: this world only models a small recurring seep that can be sensibly fixed with a tray or mat.)"


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("repeat", pid))
    for sid in SOLUTIONS:
        lines.append(asp.fact("solution", sid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Prob, Sol) :- place(P), problem(Prob), solution(Sol), repeat(Prob), Sol = tray.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about a repeated seep and a gentle fix.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=["careful", "quiet", "patient", "gentle", "thoughtful", "tidy"])
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.problem:
        combos = [c for c in combos if c[1] == args.problem]
    if args.solution:
        combos = [c for c in combos if c[2] == args.solution]
    if not combos:
        raise StoryError(explain_rejection())
    place, problem, solution = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    adult = args.adult or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, solution=solution, name=name, gender=gender, adult=adult, trait=trait)


def valid_combos() -> list[tuple[str, str, str]]:
    return [("kitchen", "seep", "tray"), ("kitchen", "seep", "mat"), ("hall", "seep", "tray"), ("hall", "seep", "mat"), ("sunroom", "seep", "tray"), ("sunroom", "seep", "mat")]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for item in combos:
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
