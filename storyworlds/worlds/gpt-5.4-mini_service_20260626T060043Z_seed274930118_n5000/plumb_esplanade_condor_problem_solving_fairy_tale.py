#!/usr/bin/env python3
"""
A small fairy-tale story world about a plumb, an esplanade, and a condor
working through a practical problem with patient, child-friendly problem solving.

The premise:
- A royal or village walk on an esplanade is interrupted by a stuck plumbed
  fountain valve, a leaky pipe, or a blocked channel.
- A condor helper and a child or caretaker observe the trouble.
- They gather clues, test a few ideas, and choose the safest fix.
- The ending proves the world changed: water flows again, the path is dry, and
  everyone feels calmer and proud.

This script is standalone and uses only the standard library for the prose
engine. ASP support is imported lazily only when requested.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "mother", "lady"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "father", "lord"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the esplanade"
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    trouble: str
    clue: str
    test: str
    fix: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _r_leak(world: World) -> list[str]:
    out: list[str] = []
    problem = world.facts.get("problem")
    if not problem:
        return out
    leak = world.get(problem.id)
    if leak.meters.get("blocked", 0.0) < THRESHOLD:
        return out
    if ("leak", leak.id) in world.fired:
        return out
    world.fired.add(("leak", leak.id))
    leak.meters["messy"] = 1.0
    out.append("Water gathered in a small shining puddle.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes.get("concern", 0.0) < THRESHOLD:
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["resolve"] = ent.memes.get("resolve", 0.0) + 1.0
        out.append("The little trouble made everyone think more carefully.")
    return out


CAUSAL_RULES = [_r_leak, _r_worry]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    place: str
    problem: str
    aid: str
    name: str
    role: str
    seed: Optional[int] = None


SETTINGS = {
    "esplanade": Setting(place="the esplanade", outdoors=True, affords={"fountain", "drain"}),
    "garden_walk": Setting(place="the garden esplanade", outdoors=True, affords={"fountain", "drain"}),
    "castle_path": Setting(place="the castle esplanade", outdoors=True, affords={"fountain", "drain"}),
}

PROBLEMS = {
    "plumb": Problem(
        id="plumb",
        label="the plumb",
        trouble="stopped the water from flowing",
        clue="the pipe gave only a tiny drip",
        test="listened at the valve",
        fix="clear the little blockage and turn the handle just so",
        result="the water ran in a bright, steady stream",
        tags={"water", "pipe", "problem_solving"},
    ),
    "esplanade": Problem(
        id="esplanade",
        label="the esplanade crack",
        trouble="made the walking path uneven",
        clue="one stone stood higher than the others",
        test="placed a straight twig across the stones",
        fix="move the loose stone and smooth the sand beneath it",
        result="the path became safe for every small step",
        tags={"path", "stone", "problem_solving"},
    ),
    "condor": Problem(
        id="condor",
        label="the condor's broken string",
        trouble="left the kite basket dangling",
        clue="the basket swung from one knot",
        test="held the string up to the light",
        fix="tie a firmer knot and clip the end cleanly",
        result="the basket hung still and neat again",
        tags={"knot", "helper", "problem_solving"},
    ),
}

AIDS = {
    "bucket": Aid(
        id="bucket",
        label="a small bucket",
        phrase="a small bucket with a bright handle",
        helps={"plumb"},
        covers={"hands"},
        prep="fetch a small bucket",
        tail="brought back the small bucket",
    ),
    "towel": Aid(
        id="towel",
        label="a dry towel",
        phrase="a dry towel folded like a banner",
        helps={"plumb", "esplanade"},
        covers={"hands", "stone"},
        prep="bring a dry towel",
        tail="came back with the dry towel",
    ),
    "twine": Aid(
        id="twine",
        label="twine",
        phrase="a spool of twine from the gatehouse",
        helps={"condor"},
        covers={"string"},
        prep="get some twine",
        tail="returned with the twine",
    ),
}

NAMES = ["Mira", "Owen", "Lena", "Jasper", "Tia", "Nico", "Iris", "Bram"]
ROLES = ["girl", "boy", "queen", "king"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for prob_id, prob in PROBLEMS.items():
            if prob_id in setting.affords or True:
                for aid_id, aid in AIDS.items():
                    if prob_id in aid.helps:
                        combos.append((place, prob_id, aid_id))
    return combos


def reasonableness_gate(setting: Setting, problem: Problem, aid: Aid) -> None:
    if problem.id not in aid.helps:
        raise StoryError(f"(No story: {aid.label} does not help with {problem.label}.)")


def choose_aid(world: World, problem: Problem) -> Optional[Aid]:
    for aid in AIDS.values():
        if problem.id in aid.helps:
            return aid
    return None


def introduce(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    world.say(
        f"Once upon a time, {hero.id} wandered along {world.setting.place} "
        f"with {helper.label}, a calm condor who liked careful thinking."
    )
    world.say(
        f"They noticed {problem.label}, and soon {problem.trouble}."
    )


def observe(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["curious"] = hero.memes.get("curious", 0.0) + 1.0
    world.say(
        f"{hero.id} did not panic. Instead, {hero.pronoun()} looked closely, "
        f"because good problem solving begins with noticing what is true."
    )
    world.say(f"The clue was simple: {problem.clue}.")


def test_idea(world: World, hero: Entity, helper: Entity, problem: Problem, aid: Aid) -> None:
    world.say(
        f"{helper.label} suggested a test: they would {problem.test} and try "
        f"{aid.prep} if they needed to."
    )
    world.say(
        f"{hero.id} tried the test and saw that the first idea was not enough."
    )
    hero.memes["concern"] = hero.memes.get("concern", 0.0) + 1.0
    propagate(world)


def fix_problem(world: World, hero: Entity, helper: Entity, problem: Problem, aid: Aid) -> None:
    hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1.0
    world.say(
        f"Then {helper.label} helped {hero.id} choose a better plan: {problem.fix}."
    )
    world.say(
        f"They worked slowly and kindly, and soon {problem.result}."
    )


def ending(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    world.say(
        f"At the end, {hero.id} smiled at the tidy little change. "
        f"{helper.label} folded {helper.pronoun('possessive')} wings and looked proud."
    )
    world.say(
        f"Together they walked on, and {world.setting.place} felt brighter than before."
    )


def tell(setting: Setting, problem: Problem, aid: Aid, hero_name: str = "Mira", role: str = "girl") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=role, label=hero_name))
    helper = world.add(Entity(id="Condor", kind="character", type="condor", label="the condor"))
    issue = world.add(Entity(id=problem.id, type="thing", label=problem.label, phrase=problem.label))
    issue.meters["blocked"] = 1.0
    world.facts["problem"] = issue
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["aid"] = aid
    world.facts["problem_def"] = problem

    introduce(world, hero, helper, problem)
    world.para()
    observe(world, hero, problem)
    test_idea(world, hero, helper, problem, aid)
    world.para()
    fix_problem(world, hero, helper, problem, aid)
    issue.meters["blocked"] = 0.0
    world.facts["fixed"] = True
    ending(world, hero, helper, problem)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    problem: Problem = f["problem_def"]
    aid: Aid = f["aid"]
    hero: Entity = f["hero"]
    return [
        f'Write a short fairy tale about {hero.id} and a condor solving a problem on an esplanade.',
        f'Create a gentle story where a condor uses {aid.label} to help with {problem.label}.',
        f'Write a child-friendly fairy tale that includes the words "plumb", "esplanade", and "condor".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    aid: Aid = f["aid"]
    problem: Problem = f["problem_def"]
    return [
        QAItem(
            question=f"Who solved the trouble on {world.setting.place}?",
            answer=f"{hero.id} and {helper.label} solved it together by using careful problem solving.",
        ),
        QAItem(
            question=f"What was wrong with {problem.label}?",
            answer=f"It {problem.trouble}. The clue showed what needed attention, and then they found a better plan.",
        ),
        QAItem(
            question=f"How did they fix the problem?",
            answer=f"They used {aid.label} and then followed the plan to {problem.fix}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a condor?",
            answer="A condor is a very large bird with broad wings that can glide high in the sky.",
        ),
        QAItem(
            question="What is an esplanade?",
            answer="An esplanade is a wide path or open walkway made for strolling and looking around.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means noticing a trouble, thinking about clues, trying a plan, and choosing the best fix.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="esplanade", problem="plumb", aid="bucket", name="Mira", role="girl"),
    StoryParams(place="garden_walk", problem="esplanade", aid="towel", name="Owen", role="boy"),
    StoryParams(place="castle_path", problem="condor", aid="twine", name="Lena", role="girl"),
]


ASP_RULES = r"""
% A story is valid when the aid truly helps the selected problem.
valid(P, X, A) :- setting(P), problem(X), aid(A), helps(A, X).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for tag in sorted(prob.tags):
            lines.append(asp.fact("tag", pid, tag))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        for x in sorted(aid.helps):
            lines.append(asp.fact("helps", aid_id, x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    if py - asp_set:
        print("only python:", sorted(py - asp_set))
    if asp_set - py:
        print("only asp:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale problem solving story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["girl", "boy", "queen", "king"])
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
    combos = [c for c in combos if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.aid is None or c[2] == args.aid)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, aid = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        problem=problem,
        aid=aid,
        name=args.name or rng.choice(NAMES),
        role=args.role or rng.choice(ROLES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PROBLEMS[params.problem], AIDS[params.aid], params.name, params.role)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid_combos()
        for item in vals:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
