#!/usr/bin/env python3
"""
A standalone story world for a tiny mythic petting-zoo tale.

Premise:
A young keeper at a petting zoo must choose between a grand opera rehearsal
and urgent maintenance after a gate latch breaks. The child goes on a brave
quest, mends the trouble, and learns how courage can sound like music.

The world is simulated with physical meters and emotional memes, and the
story is authored from that changing state.
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
# Typed world entities
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "sister"}
        male = {"boy", "father", "dad", "man", "king", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the petting zoo"
    affords: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    name: str
    verb: str
    gerund: str
    risk: str
    weather: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    region: str
    mess: str
    remedy: str
    fix_label: str
    fix_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    covers: set[str]
    helps: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


THRESHOLD = 1.0
MUTATE_KEYS = {"broken", "dirty", "noisy", "tired"}


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "petting_zoo": Setting(place="the petting zoo", affords={"opera", "maintenance"}),
}

GOALS = {
    "opera": Goal(
        id="opera",
        name="opera",
        verb="sing the opera",
        gerund="singing the opera",
        risk="the music would be stopped by the broken gate",
        weather="clear",
        tags={"opera", "music", "bravery"},
    ),
    "maintenance": Goal(
        id="maintenance",
        name="maintenance",
        verb="repair the broken latch",
        gerund="repairing the broken latch",
        risk="the gate might swing open",
        weather="clear",
        tags={"maintenance", "quest", "bravery"},
    ),
}

PROBLEMS = {
    "gate": Problem(
        id="gate",
        label="gate",
        phrase="the wooden gate with the bent latch",
        region="gate",
        mess="broken",
        remedy="fixed",
        fix_label="latch",
        fix_phrase="a brass latch pin and a small hammer",
        tags={"maintenance", "quest"},
    ),
    "chorus_bell": Problem(
        id="chorus_bell",
        label="bell",
        phrase="the bell that marked the start of the chorus",
        region="sound",
        mess="noisy",
        remedy="quieted",
        fix_label="cloth",
        fix_phrase="a soft cloth and a tie of twine",
        tags={"opera", "music"},
    ),
}

AIDS = [
    Aid(
        id="toolkit",
        label="a little toolkit",
        covers={"gate"},
        helps={"broken"},
        prep="carry the little toolkit to the gate",
        tail="walked home beneath the lantern-light with the fixed latch",
    ),
    Aid(
        id="cloak",
        label="a bright cloak",
        covers={"sound"},
        helps={"noisy"},
        prep="wear the bright cloak of stage-calm",
        tail="stood in the lantern glow with the cloak fluttering like a banner",
    ),
]

HERO_NAMES = ["Mira", "Tala", "Ivo", "Sera", "Noa", "Orin", "Lina", "Ari"]
GUARDIAN_NAMES = ["keeper", "caretaker", "warden", "guide"]


# ---------------------------------------------------------------------------
# World model helpers
# ---------------------------------------------------------------------------
def prize_at_risk(goal: Goal, problem: Problem) -> bool:
    return (goal.id in problem.tags) or (goal.id == "maintenance" and problem.id == "gate")


def select_aid(goal: Goal, problem: Problem) -> Optional[Aid]:
    for aid in AIDS:
        if problem.mess in aid.helps and problem.region in aid.covers:
            return aid
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for goal_id in setting.affords:
            goal = GOALS[goal_id]
            for prob_id, problem in PROBLEMS.items():
                if prize_at_risk(goal, problem) and select_aid(goal, problem):
                    combos.append((place, goal_id, prob_id))
    return combos


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    goal: str
    problem: str
    name: str
    role: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="child"))
    guardian = world.add(Entity(id="Guardian", kind="character", type=params.role, label=params.role))
    goal = GOALS[params.goal]
    problem = PROBLEMS[params.problem]
    problem_ent = world.add(Entity(
        id=problem.id,
        kind="thing",
        type="thing",
        label=problem.label,
        phrase=problem.phrase,
        caretaker=guardian.id,
    ))

    hero.memes["wonder"] = 1.0
    hero.memes["bravery"] = 0.0
    guardian.memes["worry"] = 1.0

    world.say(f"{hero.id} lived by {world.setting.place} and listened for marvels in the dust and hay.")
    world.say(f"{hero.id} loved {goal.gerund}, because it sounded like a royal song under the open sky.")
    world.say(f"The old {problem_ent.label} waited by the pen, and its {problem.phrase} made the day uneasy.")

    world.para()
    world.say(f"One noon, the keeper called for the start of the opera, but the broken {problem_ent.label} kept the gate from closing.")
    world.say(f"{hero.id} wanted to {goal.verb}, yet {guardian.label} feared the gate might swing wide and start a trouble bigger than song.")

    hero.memes["desire"] = 1.0
    guardian.memes["conflict"] = 1.0

    world.para()
    world.say(f"So {hero.id} chose a quest instead of waiting.")
    hero.memes["bravery"] = 1.0
    world.say(f"{hero.id} carried the little toolkit to the gate, even though the hinges creaked like an old giant waking.")
    world.say(f"With steady hands, {hero.id} set the latch right, and the gate became calm again.")
    problem_ent.meters["broken"] = 0.0
    problem_ent.meters["fixed"] = 1.0

    aid = select_aid(goal, problem)
    if aid:
        world.say(f"Then {hero.id} returned wearing {aid.label}, and the zoo became a stage.")
        world.say(f"The animals listened while {hero.id} sang the opera, and the notes rose over the pens like bright birds.")
        world.say(f"{guardian.label} smiled, because bravery had become part of the music.")

    world.facts.update(
        hero=hero,
        guardian=guardian,
        goal=goal,
        problem=problem_ent,
        aid=aid,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    goal = f["goal"]
    return [
        f"Write a myth-like story about a child named {hero.id} at a petting zoo who must choose between {goal.name} and a maintenance quest.",
        f"Tell a gentle tale where bravery helps a keeper solve a broken-gate problem before the opera begins.",
        f"Write a short story set in a petting zoo where music and maintenance come together through courage.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guardian = f["guardian"]
    goal = f["goal"]
    problem = f["problem"]
    aid = f["aid"]
    return [
        QAItem(
            question=f"Why did {hero.id} go on a quest instead of only waiting for the opera?",
            answer=f"{hero.id} saw that the broken {problem.label} needed maintenance, and the gate had to be fixed before the opera could begin safely.",
        ),
        QAItem(
            question=f"What made the story brave?",
            answer=f"It was brave because {hero.id} carried the toolkit to the gate and fixed the latch even though it felt like stepping toward an old giant.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the {problem.label} was fixed, the gate was calm, and {hero.id} could join the opera while {guardian.label} smiled in relief.",
        ),
    ] + (
        [QAItem(
            question=f"How did the aid help {hero.id} finish the maintenance quest?",
            answer=f"The {aid.label} helped because it was the right tool to handle the broken gate, so {hero.id} could repair it and return to the music.",
        )] if aid else []
    )


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is maintenance?",
            answer="Maintenance means taking care of something and fixing it so it keeps working well.",
        ),
        QAItem(
            question="What is an opera?",
            answer="An opera is a story told with singing, music, and dramatic voices.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is the courage to do something hard or scary because it is the right thing to do.",
        ),
        QAItem(
            question="What is a petting zoo?",
            answer="A petting zoo is a place where children can visit small animals and often touch or feed them gently.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
at_risk(G,P) :- goal(G), problem(P), goal_tags(G,T), problem_tags(P,T).
compatible(G,P) :- at_risk(G,P), aid(A), aid_helps(A,M), problem_mess(P,M), aid_covers(A,R), problem_region(P,R).
valid_story(Place,G,P) :- setting(Place), affords(Place,G), at_risk(G,P), compatible(G,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for g in sorted(s.affords):
            lines.append(asp.fact("affords", place, g))
    for gid, g in GOALS.items():
        lines.append(asp.fact("goal", gid))
        for t in sorted(g.tags):
            lines.append(asp.fact("goal_tags", gid, t))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("problem_region", pid, p.region))
        lines.append(asp.fact("problem_mess", pid, p.mess))
        for t in sorted(p.tags):
            lines.append(asp.fact("problem_tags", pid, t))
    for a in AIDS:
        lines.append(asp.fact("aid", a.id))
        for c in sorted(a.covers):
            lines.append(asp.fact("aid_covers", a.id, c))
        for h in sorted(a.helps):
            lines.append(asp.fact("aid_helps", a.id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# QA / trace / params
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"{e.id}: {', '.join(bits) if bits else 'empty'}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic petting-zoo story world with maintenance, opera, quest, and bravery.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--goal", choices=GOALS.keys())
    ap.add_argument("--problem", choices=PROBLEMS.keys())
    ap.add_argument("--name")
    ap.add_argument("--role", choices=GUARDIAN_NAMES)
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
    if args.place or args.goal or args.problem:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.goal is None or c[1] == args.goal)
            and (args.problem is None or c[2] == args.problem)
        ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, goal, problem = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    role = args.role or rng.choice(GUARDIAN_NAMES)
    return StoryParams(place=place, goal=goal, problem=problem, name=name, role=role)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


CURATED = [
    StoryParams(place="petting_zoo", goal="opera", problem="gate", name="Mira", role="keeper"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        for item in combos:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
