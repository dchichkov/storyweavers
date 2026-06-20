#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/centaur_lesson_learned_problem_solving_animal_story.py
======================================================================================

A standalone storyworld script for a small animal-story domain centered on a
centaur, a problem, a practical fix, and a learned lesson.

The world is intentionally tiny:
- one animal-like caretaker
- one centaur child
- one helpful animal friend
- one small problem involving a blocked path or missing item
- one grounded solution
- one lesson learned ending

The story is built from simulation state, not from a frozen paragraph template.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "father", "man", "centaur"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    obstacle: str
    item: str
    animal_friend: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Problem:
    id: str
    kind: str
    cause: str
    blocked_by: str
    needs: str
    clue: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Fix:
    id: str
    kind: str
    action: str
    result: str
    lesson: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    c = world.get("centaur")
    p = world.get("problem")
    if c.memes["concern"] >= THRESHOLD and p.id not in world.fired:
        world.fired.add(( "worry", p.id))
        out.append("__worry__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    p = world.get("problem")
    if p.meters["fixed"] >= THRESHOLD and p.id not in world.fired:
        world.fired.add(("relief", p.id))
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("relief", "social", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_problem(world: World, narrate: bool = True) -> None:
    p = world.get("problem")
    p.meters["blocked"] += 1
    world.get("centaur").memes["concern"] += 1
    propagate(world, narrate=narrate)


def problem_at_risk(problem: Problem) -> bool:
    return problem.kind in {"blocked_path", "missing_item"}


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= 2]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def fix_works(fix: Fix, problem: Problem) -> bool:
    return fix.power >= (2 if problem.kind == "blocked_path" else 1)


def tell(setting: Setting, problem: Problem, fix: Fix, *, centaur_name: str = "Centa",
         friend_name: str = "Milo", caretaker_name: str = "Mara") -> World:
    world = World()
    centaur = world.add(Entity("centaur", kind="character", type="centaur", label=centaur_name,
                               role="hero", traits=["kind", "curious"]))
    friend = world.add(Entity("friend", kind="character", type="fox", label=friend_name,
                              role="helper", traits=["quick", "helpful"]))
    caretaker = world.add(Entity("caretaker", kind="character", type="mother", label=caretaker_name,
                                 role="guide", traits=["calm", "wise"]))
    path = world.add(Entity("path", label=setting.place))
    obstacle = world.add(Entity("obstacle", label=setting.obstacle))
    item = world.add(Entity("item", label=setting.item))
    world.facts["setting"] = setting

    centaur.memes["hope"] = 1
    friend.memes["helpfulness"] = 1

    world.say(
        f"In {setting.place}, {centaur_name} the centaur was playing with {friend_name} the fox. "
        f"They wanted to reach {setting.item}, but {setting.obstacle} blocked the way."
    )
    world.say(
        f'{centaur_name} frowned. "{problem.clue}"'
    )

    world.para()
    centaur.memes["concern"] += 1
    world.say(
        f"{friend_name} peered at the problem and nudged a plan closer. "
        f"They looked for a way around, because the first idea would not work."
    )

    if fix_works(fix, problem):
        world.para()
        p = world.get("problem")
        p.meters["fixed"] += 1
        world.get("centaur").memes["joy"] += 1
        world.get("centaur").memes["lesson"] += 1
        world.say(
            f"{caretaker_name} smiled and showed them {fix.action}. "
            f"Together they used it, and soon {fix.result}."
        )
        world.say(
            f"{centaur_name} learned {fix.lesson}."
        )
        world.say(
            f"By the end, the centaur and the fox were back on the path, proud that they had solved it the safe way."
        )
    else:
        world.para()
        world.say(
            f"{caretaker_name} tried a fix, but it was too small for the trouble. "
            f"They had to stop, back up, and choose a better plan."
        )
        world.say(
            f"At last, they used {best_fix().action} and got {best_fix().result}."
        )
        world.say(f"{centaur_name} learned {best_fix().lesson}.")

    world.facts.update(
        centaur=centaur,
        friend=friend,
        caretaker=caretaker,
        path=path,
        obstacle=obstacle,
        item=item,
        problem_cfg=problem,
        fix=fix,
        resolved=True,
    )
    return world


SETTINGS = {
    "meadow": Setting("meadow", "a sunny meadow trail", "a fallen branch", "a berry basket", "the fox"),
    "forest": Setting("forest", "a mossy forest path", "a tangle of vines", "a little stream", "the rabbit"),
    "farm": Setting("farm", "a quiet farm lane", "a mud patch", "a crate of apples", "the duck"),
}

PROBLEMS = {
    "blocked_path": Problem("blocked_path", "blocked_path", "a branch fell across the trail",
                            "a branch", "they needed a way through", "We need a way past it!",
                            tags={"path", "obstacle"}),
    "missing_item": Problem("missing_item", "missing_item", "the basket rolled behind the stones",
                            "the stones", "they needed to reach it safely", "We need to get it back!",
                            tags={"item", "search"}),
}

FIXES = {
    "lift": Fix("lift", "lift_and_slide", "lift the branch together and slide it aside",
                "the path opened wide again", "working together can solve a problem", 2, 3,
                tags={"teamwork", "path"}),
    "bridge": Fix("bridge", "find a sturdy plank and make a small bridge",
                  "they crossed without getting stuck", "a problem can need a different tool", 2, 3,
                  tags={"planning", "path"}),
    "ask": Fix("ask", "ask a grown-up for help",
               "the grown-up fixed it quickly", "it is smart to ask for help", 3, 4,
               tags={"help", "lesson"}),
    "roll": Fix("roll", "roll the stones away one by one",
                "the basket came free", "slow careful work can be enough", 1, 2,
                tags={"careful", "item"}),
}

NAMES = ["Centa", "Aris", "Pip", "Nova", "Bran", "Mira", "Sunny", "Tavi"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            if not problem_at_risk(problem):
                continue
            for fid, fix in FIXES.items():
                if fix_works(fix, problem):
                    out.append((sid, pid, fid))
    return out


@dataclass
@dataclass
class StoryParams:
    setting: str
    problem: str
    fix: str
    centaur_name: str
    friend_name: str
    caretaker_name: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


KNOWLEDGE = {
    "centaur": [("What is a centaur?", "A centaur is a story creature with a human upper body and a horse body. In animal stories, centaurs can be kind helpers or brave problem solvers.")],
    "branch": [("Why can a fallen branch block a path?", "A fallen branch can be too big to walk over safely. It may need to be moved before anyone can pass.")],
    "teamwork": [("What is teamwork?", "Teamwork is when friends work together to solve a problem. Each helper does a part, and the job gets easier.")],
    "help": [("When should you ask for help?", "Ask for help when a problem is too hard or too risky to solve alone. A grown-up can keep everyone safe.")],
    "lesson": [("What is a lesson learned?", "A lesson learned is something you understand better after something happens. It helps you make a wiser choice next time.")],
    "bridge": [("What is a bridge used for?", "A bridge lets you cross over something safely, like water or a muddy gap.")],
    "roll": [("What does it mean to roll something away?", "It means to move it little by little so it does not hurt anyone or break anything.")],
}
KNOWLEDGE_ORDER = ["centaur", "branch", "teamwork", "help", "lesson", "bridge", "roll"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s = f["setting"]
    p = f["problem_cfg"]
    fx = f["fix"]
    return [
        f'Write an animal story for a young child that includes the word "centaur" and a problem on {s.place}.',
        f"Tell a gentle story where the centaur and a fox notice a problem, think of a plan, and learn a lesson.",
        f'Write a story about {p.clue.lower()} ending with {fx.lesson}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    centaur = f["centaur"]
    friend = f["friend"]
    caretaker = f["caretaker"]
    problem = f["problem_cfg"]
    fix = f["fix"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {centaur.id} the centaur, {friend.id} the fox, and {caretaker.id} who helped them. They worked through one small problem together."
        ),
        QAItem(
            question="What was the problem?",
            answer=f"The problem was that {problem.cause}. That blocked what they wanted to do next, so they had to stop and think."
        ),
        QAItem(
            question="How did they solve it?",
            answer=f"They solved it by {fix.action}. That worked because it was strong enough for the problem and kept everyone safe."
        ),
        QAItem(
            question="What lesson did {0} learn?".format(centaur.id),
            answer=f"{centaur.id} learned {fix.lesson}. The ending shows the centaur using a calmer, smarter idea instead of rushing ahead."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["problem_cfg"].tags) | set(world.facts["fix"].tags)
    out: list[QAItem] = []
    for k in KNOWLEDGE_ORDER:
        if k in tags and k in KNOWLEDGE:
            q, a = KNOWLEDGE[k][0]
            out.append(QAItem(q, a))
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        out.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(out)


CURATED = [
    StoryParams("meadow", "blocked_path", "lift", "Centa", "Milo", "Mara"),
    StoryParams("forest", "blocked_path", "ask", "Aris", "Pip", "Mira"),
    StoryParams("farm", "missing_item", "roll", "Nova", "Tavi", "Sunny"),
]


def explain_rejection(problem: Problem, fix: Fix) -> str:
    return f"(No story: {fix.id} is not a sensible enough fix for this problem.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
works(F, P) :- fix(F), problem(P), power(F, Pow), P == blocked_path, Pow >= 2.
works(F, P) :- fix(F), problem(P), power(F, Pow), P == missing_item, Pow >= 1.
valid(S, P, F) :- setting(S), problem(P), fix(F), sensible(F), works(F, P).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid combos differ.")
        rc = 1
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    if set(asp_sensible()) != {f.id for f in sensible_fixes()}:
        print("MISMATCH: sensible fixes differ.")
        rc = 1
    else:
        print("OK: sensible fixes match.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke-generated story succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal-story world with a centaur, a problem, a fix, and a lesson.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--centaur-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--caretaker-name")
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
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, fix = rng.choice(sorted(combos))
    centaur_name = args.centaur_name or rng.choice(NAMES)
    friend_name = args.friend_name or rng.choice([n for n in NAMES if n != centaur_name])
    caretaker_name = args.caretaker_name or rng.choice([n for n in NAMES if n not in {centaur_name, friend_name}])
    return StoryParams(setting, problem, fix, centaur_name, friend_name, caretaker_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], FIXES[params.fix],
                 centaur_name=params.centaur_name, friend_name=params.friend_name,
                 caretaker_name=params.caretaker_name)
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
        print(asp_program(show="#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
