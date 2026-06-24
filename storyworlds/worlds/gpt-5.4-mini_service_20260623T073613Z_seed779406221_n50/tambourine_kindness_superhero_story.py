#!/usr/bin/env python3
"""
storyworlds/worlds/tambourine_kindness_superhero_story.py
========================================================

A standalone story world for a tiny superhero tale about a tambourine, kindness,
and a small rescue that turns a noisy problem into a bright ending.

Seed premise:
A child superhero wants to help at a block party. A lost tambourine makes a
jumpy dog and a worried little crowd. The hero uses kindness, rhythm, and a
gentle plan to calm everyone down and find the owner.

World model:
- typed entities with physical meters and emotional memes
- state-driven narration with a premise, turn, and resolution
- a reasonableness gate: only plausible hero/problem/fix combinations are
  generated
- an inline ASP twin with facts from the registries and a verification mode
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    noise: str
    worry: str
    risky: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    method: str
    effect: str
    calm: float
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    problem: str
    fix: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "plaza": Setting("the sunny plaza", False, {"loud", "ring"}),
    "schoolyard": Setting("the schoolyard", False, {"loud", "ring"}),
    "community_room": Setting("the community room", True, {"loud", "ring"}),
}

PROBLEMS = {
    "lost_tambourine": Problem(
        id="lost_tambourine",
        label="tambourine",
        phrase="a shiny tambourine",
        noise="jingle-jingle",
        worry="the loud jingling made the little dog bark and the crowd flinch",
        risky=True,
        tags={"tambourine", "noise", "lost"},
    ),
    "snatched_tambourine": Problem(
        id="snatched_tambourine",
        label="tambourine",
        phrase="a bright tambourine",
        noise="clang-clang",
        worry="the sudden racket upset the marching band kids",
        risky=True,
        tags={"tambourine", "noise"},
    ),
}

FIXES = {
    "kind_words": Fix(
        id="kind_words",
        label="kind words",
        phrase="kind words and a gentle smile",
        method="speak softly and ask everyone to take a breath",
        effect="the noise felt smaller right away",
        calm=2.0,
        tags={"kindness", "soft"},
    ),
    "slow_rhythm": Fix(
        id="slow_rhythm",
        label="slow rhythm",
        phrase="a slow superhero rhythm",
        method="tap a slow beat on the tambourine to guide the room",
        effect="the crowd matched the beat and settled down",
        calm=3.0,
        tags={"kindness", "rhythm"},
    ),
    "return_it": Fix(
        id="return_it",
        label="return it kindly",
        phrase="a careful handoff",
        method="find the owner and return the tambourine politely",
        effect="the missing owner smiled and the room relaxed",
        calm=4.0,
        tags={"kindness", "help"},
    ),
}

HERO_NAMES = ["Maya", "Nova", "Zane", "Pip", "Aria", "Jude", "Luna", "Kai"]
HELPER_NAMES = ["Milo", "Rae", "Finn", "Bea", "Noah", "Ivy", "Nia", "Theo"]
TRAITS = ["kind", "brave", "gentle", "careful", "cheerful"]

GIRL_NAMES = ["Maya", "Nova", "Aria", "Luna", "Rae", "Bea", "Ivy", "Nia"]
BOY_NAMES = ["Zane", "Pip", "Jude", "Kai", "Milo", "Finn", "Noah", "Theo"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for p in PROBLEMS:
            for f in FIXES:
                if PROBLEMS[p].risky and "kindness" in FIXES[f].tags:
                    out.append((s, p, f))
    return out


def reason_ok(problem: Problem, fix: Fix) -> bool:
    return problem.risky and "kindness" in fix.tags


def explain_rejection(problem: Problem, fix: Fix) -> str:
    return (
        f"(No story: {problem.label} needs a gentle, kindness-based fix, but "
        f"{fix.label} does not fit that shape.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: tambourine, kindness, and a calm rescue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


@dataclass
class Rule:
    name: str
    apply: callable


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _r_calm(world: World) -> list[str]:
    out = []
    if world.facts.get("shared_beat") and not world.fired.__contains__(("calm",)):
        world.fired.add(("calm",))
        crowd = world.get("crowd")
        crowd.meters["calm"] = crowd.meters.get("calm", 0.0) + 1
        out.append("The room began to settle.")
    return out


RULES = [Rule("calm", _r_calm)]


def tell(setting: Setting, problem: Problem, fix: Fix, hero_name: str, hero_gender: str,
         helper_name: str, helper_gender: str, parent: str, trait: str) -> World:
    w = World(setting)
    hero = w.add(Entity(hero_name, kind="character", type=hero_gender, label=hero_name))
    helper = w.add(Entity(helper_name, kind="character", type=helper_gender, label=helper_name))
    adult = w.add(Entity("parent", kind="character", type=parent, label=f"the {parent}"))
    tamb = w.add(Entity("tambourine", kind="thing", type="tambourine", label="tambourine", phrase=problem.phrase, owner=hero.id, tags={"tambourine"}))
    crowd = w.add(Entity("crowd", kind="thing", type="crowd", label="the little crowd"))
    dog = w.add(Entity("dog", kind="thing", type="dog", label="the small dog"))
    hero.memes["kindness"] = 1.0
    helper.memes["hope"] = 1.0
    w.say(f"{hero.id} was a {trait} little superhero who liked helping at {setting.place}.")
    w.say(f"On that day, {problem.phrase} made a noisy {problem.noise} and {problem.worry}.")
    w.para()
    hero.memes["worry"] = 1.0
    helper.memes["worry"] = 1.0
    w.say(f"{helper.id} looked at the noisy scene and pointed to {hero.id}.")
    w.say(f'"We can fix this with kindness," {helper.id} said.')
    w.say(f'{hero.id} nodded and held up {hero.pronoun("possessive")} little superhero badge.')
    w.facts["shared_beat"] = True
    propagate(w, narrate=True)
    w.para()
    if fix.id == "kind_words":
        w.say(f"{hero.id} spoke softly to the dog and the crowd, and the noise felt smaller right away.")
        w.say(f"Then {helper.id} found the owner, and the tambourine went back to the right hands.")
    elif fix.id == "slow_rhythm":
        w.say(f"{hero.id} tapped a slow rhythm on the tambourine, and the crowd started breathing with the beat.")
        w.say(f"{helper.id} smiled as the jingle turned into a calm song instead of a sharp racket.")
    else:
        w.say(f"{helper.id} helped {hero.id} find the owner, and {hero.id} returned the tambourine kindly.")
        w.say(f"The missing owner thanked them, and the little crowd relaxed at once.")
    w.say(f"By the end, {hero.id} was smiling beside {helper.id}, and the tambourine sounded like a happy song.")
    w.facts.update(hero=hero, helper=helper, adult=adult, tambourine=tamb, crowd=crowd, dog=dog,
                   setting=setting, problem=problem, fix=fix)
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["problem"]
    f = world.facts["fix"]
    h = world.facts["hero"]
    return [
        f'Write a superhero story for a 3-to-5-year-old about {h.id}, a tambourine, and kindness.',
        f"Tell a short story where {h.id} uses {f.label} to calm a noisy {p.label} problem.",
        f'Write a gentle superhero story that includes the word "tambourine" and ends with a kind rescue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    problem = f["problem"]
    fix = f["fix"]
    adult = f["adult"]
    return [
        QAItem(question=f"Who is the superhero in the story?", answer=f"It is {hero.id}, who helped with kindness and a calm plan."),
        QAItem(question=f"What was noisy about the {problem.label}?", answer=f"The tambourine made a loud {problem.noise}, and that noise worried the crowd and the dog."),
        QAItem(question=f"How did {helper.id} help {hero.id}?", answer=f"{helper.id} reminded {hero.id} to use {fix.label}, so the problem could be solved gently."),
        QAItem(question=f"Did the {adult.label_word if hasattr(adult, 'label_word') else adult.type} stay upset?", answer=f"No. The grown-up saw the kind help, and the room settled down by the end."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tambourine?",
            answer="A tambourine is a hand instrument with little jingles that make a bright shaking sound when you tap or shake it.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means using gentle words and helpful actions so other people feel safe, calm, and cared for.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,F) :- setting(S), problem(P), fix(F), risky(P), kindness_fix(F).
kindness_fix(F) :- fix(F), fix_kindness(F).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p, obj in PROBLEMS.items():
        lines.append(asp.fact("problem", p))
        if obj.risky:
            lines.append(asp.fact("risky", p))
    for f, obj in FIXES.items():
        lines.append(asp.fact("fix", f))
        if "kindness" in obj.tags:
            lines.append(asp.fact("fix_kindness", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.fix and not reason_ok(PROBLEMS[args.problem], FIXES[args.fix]):
        raise StoryError(explain_rejection(PROBLEMS[args.problem], FIXES[args.fix]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, fix = rng.choice(sorted(combos))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    helper_name = args.helper or rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != hero_name])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, problem, fix, hero_name, hero_gender, helper_name, helper_gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], FIXES[params.fix],
                 params.hero_name, params.hero_gender, params.helper_name, params.helper_gender,
                 params.parent, params.trait)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world),
                       story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
    StoryParams("plaza", "lost_tambourine", "slow_rhythm", "Maya", "girl", "Kai", "boy", "mother", "kind"),
    StoryParams("community_room", "snatched_tambourine", "kind_words", "Zane", "boy", "Luna", "girl", "father", "gentle"),
    StoryParams("schoolyard", "lost_tambourine", "return_it", "Aria", "girl", "Jude", "boy", "mother", "brave"),
]


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
        for row in combos:
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
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
