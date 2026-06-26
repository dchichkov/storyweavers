#!/usr/bin/env python3
"""
A small animal-story world about a kindness quest, a tricky subtraction, and a
wire that must be kept clear of swill.
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "bunny", "hare", "mouse", "squirrel"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"fox", "wolf", "bear", "deer", "cat", "dog", "owl"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the meadow"
    indoors: bool = False
    noise: str = "soft wind"


@dataclass
class Problem:
    id: str
    name: str
    verb: str
    gerund: str
    risk: str
    mess: str
    zone: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Fix:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.facts: dict = {}

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.lines = []
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the meadow", indoors=False, noise="soft wind"),
    "farmyard": Setting(place="the farmyard", indoors=False, noise="busy clucks"),
    "barn": Setting(place="the barn", indoors=True, noise="dry straw"),
}

PROBLEMS = {
    "subtraction": Problem(
        id="subtraction",
        name="subtraction",
        verb="count the apples and take some away",
        gerund="counting and taking away",
        risk="mix up the pile",
        mess="scattered",
        zone="table",
        keyword="subtraction",
        tags={"math", "counting"},
    ),
    "wire": Problem(
        id="wire",
        name="wire",
        verb="follow the wire",
        gerund="following the wire",
        risk="tangle the wire",
        mess="twisted",
        zone="path",
        keyword="wire",
        tags={"wire", "path"},
    ),
    "swill": Problem(
        id="swill",
        name="swill",
        verb="carry away the swill",
        gerund="carrying swill",
        risk="spill the swill",
        mess="splashed",
        zone="floor",
        keyword="swill",
        tags={"swill", "cleanup"},
    ),
}

PRIZES = {
    "apples": Prize(id="apples", label="apples", phrase="a basket of shiny apples", region="table", plural=True),
    "lamp": Prize(id="lamp", label="lamp", phrase="a little lamp with a bright glass top", region="path"),
    "bucket": Prize(id="bucket", label="bucket", phrase="a clean bucket", region="floor"),
}

FIXES = [
    Fix(
        id="cloth",
        label="a clean cloth",
        covers={"table"},
        guards={"scattered"},
        prep="place a clean cloth under the apples",
        tail="placed a clean cloth under the apples",
    ),
    Fix(
        id="boots",
        label="rubber boots",
        covers={"path"},
        guards={"twisted"},
        prep="put on rubber boots",
        tail="put on rubber boots",
    ),
    Fix(
        id="tray",
        label="a shallow tray",
        covers={"floor"},
        guards={"splashed"},
        prep="set the swill on a shallow tray",
        tail="set the swill on a shallow tray",
    ),
]

ANIMAL_TYPES = ["rabbit", "bunny", "fox", "deer", "squirrel", "mouse"]
ANIMAL_NAMES = ["Pip", "Milo", "Nina", "Toby", "Luna", "Bram", "Poppy", "Roo"]
TRAITS = ["kind", "gentle", "brave", "curious", "busy"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    problem: str
    prize: str
    name: str
    animal: str
    friend: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def needs_fix(problem: Problem, prize: Prize) -> bool:
    return prize.region == problem.zone


def select_fix(problem: Problem, prize: Prize) -> Optional[Fix]:
    for fix in FIXES:
        if prize.region in fix.covers and problem.mess in fix.guards:
            return fix
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for setting_id, setting in SETTINGS.items():
        for prob_id, prob in PROBLEMS.items():
            for prize_id, prize in PRIZES.items():
                if needs_fix(prob, prize) and select_fix(prob, prize):
                    out.append((setting_id, prob_id, prize_id))
    return out


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def _do_problem(world: World, hero: Entity, problem: Problem) -> None:
    hero.meters[problem.mess] = hero.meters.get(problem.mess, 0) + 1
    hero.memes["effort"] = hero.memes.get("effort", 0) + 1
    if problem.id == "subtraction":
        world.say(f"{hero.name_word()} tried to count the apples, but the pile began to feel tricky.")
        world.say(f"One little subtraction could make the count wrong if nobody stayed careful.")
    elif problem.id == "wire":
        world.say(f"{hero.name_word()} leaned close to the wire, trying to follow its long bend through the grass.")
        world.say(f"The wire had to stay straight, or it would twist into a useless knot.")
    else:
        world.say(f"{hero.name_word()} carried the swill toward the trough, trying not to make a splash.")
        world.say(f"Swill was slippery, and one slip could splash it across the floor.")

def _predict(world: World, hero: Entity, problem: Problem, prize_id: str) -> bool:
    sim = world.copy()
    _do_problem(sim, sim.get(hero.id), problem)
    prize = sim.get(prize_id)
    return True if needs_fix(problem, PRIZES[prize_id]) else False


def tell(setting: Setting, problem: Problem, prize_cfg: Prize, hero_name: str, hero_type: str,
         friend_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type="mouse", label=friend_name))
    prize = world.add(Entity(id=prize_cfg.id, type=prize_cfg.id, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, owner=hero.id, caretaker=friend.id))
    fix = select_fix(problem, prize_cfg)

    # Act 1
    world.say(f"{hero.name_word()} was a {trait} little {hero_type} who loved helping friends.")
    world.say(f"{hero.name_word()} and {friend.name_word()} had a small kindness quest to finish at {setting.place}.")
    world.say(f"That day, they brought {prize_cfg.phrase} along, because the job needed careful paws.")

    # Act 2
    world.say(f"The air at {setting.place} was full of {setting.noise}.")
    world.say(f"{hero.name_word()} wanted to {problem.verb}, but the task came with a slippery risk.")
    _do_problem(world, hero, problem)

    if fix is None:
        raise StoryError("No reasonable fix exists for that problem and prize.")
    world.say(f"{friend.name_word()} smiled and said, 'Let's {fix.prep} first.'")
    world.say(f"That was the kinder choice, because it kept the {problem.name} work from making a mess.")

    # Act 3
    world.say(f"{hero.name_word()} agreed, and together they {fix.tail}.")
    if problem.id == "subtraction":
        world.say(f"Then the apples were counted again, and the subtraction came out right.")
    elif problem.id == "wire":
        world.say(f"Then the wire stayed neat, so the path could still guide them home.")
    else:
        world.say(f"Then the swill stayed in its place, and the floor stayed clean.")
    world.say(f"In the end, their kindness quest was finished, and {hero.name_word()} felt proud and calm.")

    world.facts.update(hero=hero, friend=friend, prize=prize, problem=problem, fix=fix, setting=setting)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
problem_needs_fix(P, R) :- problem(P), prize(R), zone(P, Z), region(R, Z).
fixes(P, R, F) :- problem_needs_fix(P, R), fix(F), covers(F, Z), region(R, Z), guards(F, M), mess(P, M).
valid(Setting, P, R) :- setting(Setting), affords(Setting, P), problem_needs_fix(P, R), fixes(P, R, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
        lines.append(asp.fact("affords", sid, "subtraction"))
        lines.append(asp.fact("affords", sid, "wire"))
        lines.append(asp.fact("affords", sid, "swill"))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("zone", pid, p.zone))
        lines.append(asp.fact("mess", pid, p.mess))
    for rid, r in PRIZES.items():
        lines.append(asp.fact("prize", rid))
        lines.append(asp.fact("region", rid, r.region))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for c in sorted(fx.covers):
            lines.append(asp.fact("covers", fx.id, c))
        for g in sorted(fx.guards):
            lines.append(asp.fact("guards", fx.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(valid_combos_asp()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("Mismatch between ASP and Python gates.")
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle animal story about {f["hero"].name_word()} on a kindness quest that mentions "{f["problem"].keyword}".',
        f"Tell a short story where a little {f['hero'].type} faces {f['problem'].name}, stays kind, and fixes the problem with a friend.",
        f'Write an animal story that uses the word "{f["problem"].keyword}" and ends with a calm helpful choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, problem, fix = f["hero"], f["friend"], f["prize"], f["problem"], f["fix"]
    return [
        QAItem(
            question=f"Who went on the kindness quest at {f['setting'].place}?",
            answer=f"{hero.name_word()} and {friend.name_word()} went on the kindness quest together.",
        ),
        QAItem(
            question=f"What did {hero.name_word()} want to do with the {problem.keyword} task?",
            answer=f"{hero.name_word()} wanted to {problem.verb}, but that could have made trouble for the {prize.label}.",
        ),
        QAItem(
            question=f"What helped keep the {prize.label} safe?",
            answer=f"They used {fix.label} first, and that kept the {prize.label} safe while they worked.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the job finished, the problem under control, and {hero.name_word()} feeling proud and calm.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is subtraction?",
            answer="Subtraction is when you take some away from a group so there are fewer left.",
        ),
        QAItem(
            question="What is wire?",
            answer="Wire is a thin metal strand that can bend, hold shape, or carry power, depending on what it is used for.",
        ),
        QAItem(
            question="What is swill?",
            answer="Swill is wet, messy liquid or slop, and it can splash if it is not carried carefully.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing to help, be gentle, and make things easier for someone else.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal-driven trip or task where someone goes looking for a way to finish something important.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    problem: str
    prize: str
    name: str
    animal: str
    friend: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about kindness, subtraction, wire, and swill.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--animal", choices=ANIMAL_TYPES)
    ap.add_argument("--friend")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, problem, prize = rng.choice(sorted(combos))
    animal = args.animal or rng.choice(ANIMAL_TYPES)
    name = args.name or rng.choice(ANIMAL_NAMES)
    friend = args.friend or rng.choice([n for n in ANIMAL_NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, problem=problem, prize=prize, name=name, animal=animal, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], PRIZES[params.prize],
                 params.name, params.animal, params.friend, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"{e.id}: {e.type} {' '.join(bits)}")
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


CURATED = [
    StoryParams(setting="meadow", problem="subtraction", prize="apples", name="Pip", animal="rabbit", friend="Milo", trait="kind"),
    StoryParams(setting="farmyard", problem="wire", prize="lamp", name="Luna", animal="fox", friend="Roo", trait="curious"),
    StoryParams(setting="barn", problem="swill", prize="bucket", name="Toby", animal="deer", friend="Poppy", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
