#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T072428Z_seed779406221_n50/hip_addition_inner_monologue_kindness_superhero_story.py
==============================================================================================================================

A standalone story world for a small superhero-style tale with the seed words
"hip" and "addition". The domain centers on a young hero with a sore hip who
faces a tiny classroom challenge about addition, uses an inner monologue to
think through the problem, and resolves the scene with kindness.

The world is intentionally small and state-driven:
- physical meters: hip pain, fatigue, wobble, notebook neatness, etc.
- emotional memes: courage, worry, kindness, pride, relief
- story events mutate the world and drive the prose
- a reasonableness gate prevents weak or impossible combinations
- inline ASP rules mirror the Python gate and are parity-checked by --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"pain": 0.0, "fatigue": 0.0, "mess": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "courage": 0.0, "kindness": 0.0, "pride": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str]


@dataclass
class Problem:
    id: str
    prompt: str
    answer: int
    steps: int
    noise: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    offer: str
    effect: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_pain(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero or hero.meters["pain"] < THRESHOLD:
        return out
    sig = ("pain",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["fatigue"] += 1
    hero.memes["worry"] += 1
    out.append("__pain__")
    return out


CAUSAL_RULES = [Rule("pain", "physical", _r_pain)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def problem_at_risk(problem: Problem, setting: Setting) -> bool:
    return problem.id in setting.affords


def select_helper(problem: Problem) -> Optional[Helper]:
    for helper in HELPERS:
        if problem.id in helper.tags:
            return helper
    return None


def predict_problem(world: World, hero: Entity, problem: Problem) -> dict:
    sim = world.copy()
    _do_problem(sim, sim.get(hero.id), problem, narrate=False)
    return {
        "pain": sim.get(hero.id).meters["pain"],
        "fatigue": sim.get(hero.id).meters["fatigue"],
    }


def _do_problem(world: World, hero: Entity, problem: Problem, narrate: bool = True) -> None:
    if not problem_at_risk(problem, world.setting):
        return
    hero.meters["mess"] += 1
    hero.meters["pain"] += 1
    hero.memes["worry"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, friend: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(
        f"{hero.id} was a little {trait} superhero who kept a careful eye on {hero.pronoun('possessive')} hip."
    )
    world.say(
        f"{friend.id} was there too, and together they made a tiny team that liked helping at school."
    )


def setup(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["courage"] += 1
    world.say(
        f"At the bright classroom table, the page showed {problem.prompt}. "
        f"{hero.id} loved the feeling of solving addition, but {problem.noise} made {hero.pronoun('possessive')} hip ache."
    )


def inner_monologue(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["worry"] += 1
    world.say(
        f'{hero.id} thought, "If I rush, my hip will hurt more. If I go slow, I can still finish this addition."'
    )


def worry(world: World, friend: Entity, hero: Entity, problem: Problem) -> None:
    pred = predict_problem(world, hero, problem)
    world.facts["predicted_pain"] = pred["pain"]
    world.say(
        f"{friend.id} noticed the pause and asked if {hero.pronoun()} was okay."
    )
    world.say(
        f"{hero.id} nodded, holding {hero.pronoun('possessive')} hip a little more carefully."
    )


def kindness(world: World, friend: Entity, hero: Entity, problem: Problem) -> None:
    helper = select_helper(problem)
    if helper is None:
        return
    world.say(
        f"{friend.id} smiled and offered kindness first: {helper.offer}."
    )
    world.say(
        f"That gentle help made {hero.id} breathe easier and try the addition one step at a time."
    )
    hero.memes["kindness"] += 1
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    hero.meters["fatigue"] = max(0.0, hero.meters["fatigue"] - 1.0)
    world.facts["helper"] = helper


def solve(world: World, hero: Entity, problem: Problem) -> None:
    world.say(
        f"{hero.id} counted slowly: {problem.answer - 2}, then {problem.answer - 1}, then {problem.answer}."
    )
    hero.meters["mess"] = 0.0
    hero.memes["pride"] += 1
    world.say(
        f"The answer came out right, and the page stayed neat even with the sore hip."
    )


def ending(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["relief"] += 1
    world.say(
        f"By the end, {hero.id} stood taller, {hero.pronoun()} still careful with {hero.pronoun('possessive')} hip but proud of the finished work."
    )
    world.say(
        f"{friend.id} gave a thumbs-up, and the two heroes left the room like a team that had won by being kind."
    )


def tell(setting: Setting, problem: Problem, hero_name: str = "Mila", friend_name: str = "Kai") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", traits=["little", "brave", "gentle"]))
    friend = world.add(Entity(id=friend_name, kind="character", type="boy", traits=["helpful"]))
    page = world.add(Entity(id="page", type="thing", label="worksheet"))
    world.facts["page"] = page
    intro(world, hero, friend)
    world.para()
    setup(world, hero, problem)
    inner_monologue(world, hero, problem)
    worry(world, friend, hero, problem)
    world.para()
    kindness(world, friend, hero, problem)
    solve(world, hero, problem)
    ending(world, hero, friend)
    world.facts.update(hero=hero, friend=friend, problem=problem, setting=setting)
    return world


SETTINGS = {
    "classroom": Setting(place="the classroom", affords={"single_digit", "tens"}),
    "hall": Setting(place="the hallway", affords={"single_digit"}),
    "library": Setting(place="the library corner", affords={"single_digit", "tens"}),
}

PROBLEMS = {
    "single_digit": Problem(
        id="single_digit",
        prompt="3 + 2",
        answer=5,
        steps=2,
        noise="the chair legs wobbled",
        risk="a little wobble",
        tags={"addition", "hip"},
    ),
    "tens": Problem(
        id="tens",
        prompt="10 + 4",
        answer=14,
        steps=3,
        noise="the long bench sat low and hard",
        risk="a longer sit",
        tags={"addition", "hip"},
    ),
}

HELPERS = [
    Helper(
        id="slow_count",
        label="slow counting",
        offer="We can count one number at a time and take a tiny pause for your hip.",
        effect="slow and steady",
        tags={"single_digit", "tens"},
    ),
    Helper(
        id="chair_shift",
        label="chair shift",
        offer="You can move to the softer chair and keep going.",
        effect="comfortable",
        tags={"single_digit"},
    ),
]

TRAITS = ["brave", "gentle", "curious", "careful"]
GIRL_NAMES = ["Mila", "Nora", "Ava", "Zoe", "Lena"]
BOY_NAMES = ["Kai", "Theo", "Eli", "Noah", "Ben"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PROBLEMS.values():
            if problem_at_risk(p, SETTINGS[s]):
                combos.append((s, p.id))
    return combos


@dataclass
class StoryParams:
    setting: str
    problem: str
    name: str
    friend: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, problem = f["hero"], f["friend"], f["problem"]
    return [
        f'Write a short superhero story for a young child about {hero.id} solving {problem.prompt} with a sore hip and a kind friend.',
        f"Tell a gentle story where {hero.id} uses inner monologue to keep going, and {friend.id} helps with kindness.",
        f'Write a classroom superhero story that includes the words "hip" and "addition" and ends with a brave, kind solution.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, problem = f["hero"], f["friend"], f["problem"]
    return [
        QAItem(
            question=f"Who is the superhero story about?",
            answer=f"It is about {hero.id}, a little superhero who had a sore hip and still worked on {problem.prompt}.",
        ),
        QAItem(
            question=f"What did {hero.id} think to {hero.pronoun('object')}self before solving the problem?",
            answer=f"{hero.id} thought that going slowly would help {hero.pronoun('possessive')} hip and still let {hero.pronoun()} finish the addition.",
        ),
        QAItem(
            question=f"How did {friend.id} help {hero.id}?",
            answer=f"{friend.id} helped with kindness by offering quiet support and making the addition feel easier.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"{hero.id} solved the addition, felt proud, and left with {friend.id} feeling like a team.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is addition?",
            answer="Addition is a math skill where you put numbers together to find how many there are in all.",
        ),
        QAItem(
            question="What is a hip?",
            answer="A hip is a part of the body near the side of your waist that helps you sit, stand, and walk.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping, caring, and using gentle words or actions so someone feels better.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="classroom", problem="single_digit", name="Mila", friend="Kai", trait="brave"),
    StoryParams(setting="library", problem="tens", name="Nora", friend="Theo", trait="careful"),
]


def explain_rejection(problem: Problem, setting: Setting) -> str:
    return f"(No story: {problem.id} does not fit {setting.place} in this tiny world.)"


ASP_RULES = r"""
risk(P,S) :- problem(P), setting(S), affords(S,P).
valid(S,P) :- risk(P,S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for p in sorted(s.affords):
            lines.append(asp.fact("affords", sid, p))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print(" only python:", sorted(py - cl))
    print(" only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with hip, addition, inner monologue, and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES)
    friend = args.friend or rng.choice(BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, problem=problem, name=name, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], params.name, params.friend)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, problem) combos:\n")
        for s, p in combos:
            print(f"  {s:10} {p}")
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
            header = f"### {p.name}: {p.problem} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
