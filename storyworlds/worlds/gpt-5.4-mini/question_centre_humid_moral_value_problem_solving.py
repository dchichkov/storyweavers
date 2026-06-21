#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/question_centre_humid_moral_value_problem_solving.py
====================================================================================

A small heartwarming storyworld about a child at a community centre on a humid
day, facing a problem, listening to an inner monologue, asking a question, and
choosing a moral value while solving the problem kindly.

The world model keeps a few typed entities with physical meters and emotional
memes, then drives the story from that state rather than swapping nouns in a
fixed paragraph.

Seed words: question, centre, humid
Features: Moral Value, Problem Solving, Inner Monologue
Style: Heartwarming
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
MORAL_MIN = 2
HELPFUL_TRAITS = {"kind", "helpful", "gentle", "thoughtful", "patient"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    label: str
    humid: bool
    centre_name: str
    room: str
    helps: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    label: str
    need: str
    obstacle: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Solution:
    id: str
    label: str
    action: str
    effect: str
    moral: str
    comfort: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_humid(world: World) -> list[str]:
    out: list[str] = []
    if not world.setting.humid:
        return out
    for ent in world.characters():
        if ent.meters["sticky"] >= THRESHOLD:
            sig = ("humid_sticky", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["irritation"] += 1
            out.append("__humid__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["helped"] >= THRESHOLD:
            sig = ("kindness", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["warmth"] += 1
            out.append("__kind__")
    return out


CAUSAL_RULES = [Rule("humid", "physical", _r_humid), Rule("kindness", "social", _r_kindness)]


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


def helpful_solution(sid: str) -> Solution:
    return SOLUTIONS[sid]


def problem_at_risk(problem: Problem) -> bool:
    return True


def solveable(problem: Problem, solution: Solution) -> bool:
    return problem.id in solution.tags or problem.keyword in solution.tags


def best_solution() -> Solution:
    return max(SOLUTIONS.values(), key=lambda s: len(s.moral))


def predict(world: World, problem_id: str, solution_id: str) -> dict:
    sim = world.copy()
    _do_problem(sim, sim.get("child"), PROBLEMS[problem_id], narrate=False)
    _do_solution(sim, sim.get("child"), sim.get("helper"), PROBLEMS[problem_id], SOLUTIONS[solution_id])
    return {"solved": sim.get("child").memes["relief"] >= THRESHOLD}


def _do_problem(world: World, child: Entity, problem: Problem, narrate: bool = True) -> None:
    child.meters["sticky"] += 1
    child.memes["worry"] += 1
    propagate(world, narrate=narrate)


def _do_solution(world: World, child: Entity, helper: Entity, problem: Problem, solution: Solution, narrate: bool = True) -> None:
    child.meters["sticky"] = 0
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    helper.memes["pride"] += 1
    helper.memes["helped"] += 1
    world.say(
        f"{helper.label_word.capitalize()} {solution.action} and {solution.effect}."
    )
    if narrate:
        propagate(world, narrate=narrate)


def intro(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"On a humid afternoon at the {setting.centre_name}, {child.id} and {helper.id} "
        f"walked through the bright {setting.room}."
    )
    world.say(
        f"{child.id} liked the cheerful noise there, but {setting.label.lower()} felt a little heavy in the warm air."
    )


def notice_problem(world: World, child: Entity, problem: Problem) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} noticed {problem.obstacle} and wanted to fix {problem.need} before it became worse."
    )
    world.say(
        f'Inside, {child.id} asked a small question: "{problem.keyword.capitalize()}? What should I do now?"'
    )


def inner_monologue(world: World, child: Entity, problem: Problem) -> None:
    world.say(
        f"'{problem.risk},' {child.id} thought. 'But I can be kind and keep trying until this is better.'"
    )


def ask_help(world: World, child: Entity, helper: Entity, problem: Problem) -> None:
    helper.memes["listening"] += 1
    world.say(
        f"{child.id} looked up and asked {helper.id} for help. {helper.id} smiled and listened carefully."
    )


def resolve(world: World, child: Entity, helper: Entity, problem: Problem, solution: Solution) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"Together they chose {solution.label}. That {solution.comfort} the problem and made the room feel lighter."
    )
    world.say(
        f"Before long, {child.id} could breathe easier, and the day at the centre felt warm again."
    )


def tell(setting: Setting, problem: Problem, solution: Solution,
         child_name: str = "Maya", child_gender: str = "girl",
         helper_name: str = "Nadia", helper_gender: str = "girl",
         helper_role: str = "volunteer") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role=helper_role))
    world.add(Entity(id="centre", kind="thing", type="place", label=setting.centre_name))
    world.facts["setting"] = setting
    world.facts["problem"] = problem
    world.facts["solution"] = solution

    intro(world, child, helper, setting)
    world.para()
    notice_problem(world, child, problem)
    inner_monologue(world, child, problem)
    ask_help(world, child, helper, problem)

    world.para()
    _do_problem(world, child, problem)
    resolve(world, child, helper, problem, solution)
    _do_solution(world, child, helper, problem, solution)

    world.say(
        f"In the end, {child.id} had a calm heart, {helper.id} had a happy smile, and the {setting.centre_name} stayed welcoming."
    )
    world.facts.update(child=child, helper=helper, solved=True)
    return world


SETTINGS = {
    "community_centre": Setting(
        id="community_centre",
        label="the community centre",
        humid=True,
        centre_name="community centre",
        room="art room",
        helps={"problem", "sharing"},
    ),
    "neighbourhood_centre": Setting(
        id="neighbourhood_centre",
        label="the neighbourhood centre",
        humid=True,
        centre_name="neighbourhood centre",
        room="music room",
        helps={"problem", "listening"},
    ),
    "after_school_centre": Setting(
        id="after_school_centre",
        label="the after-school centre",
        humid=True,
        centre_name="after-school centre",
        room="reading corner",
        helps={"problem", "helping"},
    ),
}

PROBLEMS = {
    "lost_crayons": Problem("lost_crayons", "the missing crayons", "the art table needs color", "the crayon box was empty", "the drawings might stay unfinished", "question", {"question", "centre"}),
    "stuck_puzzle": Problem("stuck_puzzle", "the stuck puzzle", "the puzzle needs matching pieces", "one corner would not fit", "the game might end sadly", "centre", {"centre", "problem"}),
    "humid_stickers": Problem("humid_stickers", "the sticky stickers", "the stickers need sorting", "the sheets curled in the humid air", "the crafts might get messy", "humid", {"humid", "question"}),
}

SOLUTIONS = {
    "sort_drawer": Solution("sort_drawer", "sorting the drawer together", "opened the supply drawer", "found the missing pieces and put them in order", "good helpers make trouble smaller", "soothing", {"lost_crayons", "question"}),
    "match_pieces": Solution("match_pieces", "matching the pieces one by one", "sat beside the puzzle", "slid the right pieces into place", "patience helps when a problem is slow", "comforting", {"stuck_puzzle", "centre"}),
    "fan_and_towel": Solution("fan_and_towel", "a fan and a towel", "set a small fan nearby and patted the sheets dry", "made the stickers easier to peel", "small careful fixes can still be loving", "gentle", {"humid_stickers", "humid"}),
}

NAMES_GIRL = ["Maya", "Lila", "Nina", "Zara", "Ivy", "Sana"]
NAMES_BOY = ["Noah", "Eli", "Tariq", "Finn", "Owen", "Sam"]
TRAITS = ["kind", "helpful", "gentle", "thoughtful", "patient", "careful"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    problem: str
    solution: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    helper_role: str
    trait: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, prob in PROBLEMS.items():
            for sol_id, sol in SOLUTIONS.items():
                if sid == "community_centre" and solveable(prob, sol):
                    combos.append((sid, pid, sol_id))
                elif sid == "neighbourhood_centre" and solveable(prob, sol):
                    combos.append((sid, pid, sol_id))
                elif sid == "after_school_centre" and solveable(prob, sol):
                    combos.append((sid, pid, sol_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming centre storyworld with humid-day problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-role", default="volunteer")
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
              and (args.solution is None or c[2] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, solution = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(NAMES_GIRL if child_gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice([n for n in (NAMES_GIRL if helper_gender == "girl" else NAMES_BOY) if n != child])
    helper_role = args.helper_role
    trait = rng.choice(TRAITS)
    return StoryParams(setting, problem, solution, child, child_gender, helper, helper_gender, helper_role, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting, problem, solution = f["setting"], f["problem"], f["solution"]
    return [
        f"Write a heartwarming story about a humid day at a {setting.centre_name} where a child asks a question and solves a problem kindly.",
        f"Tell a short story set in the {setting.centre_name} where {problem.label} is fixed with {solution.label}.",
        f"Write a gentle story that includes the words question, centre, and humid, and ends with a warm solution.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, problem, solution = f["child"], f["helper"], f["problem"], f["solution"]
    qa = [
        ("Who is the story about?", f"It is about {child.id} and {helper.id} at the {world.setting.centre_name}."),
        ("What problem came up?", f"{problem.label.capitalize()} came up, and it made the day feel harder until they worked on it together."),
        ("What did {0} ask?".format(child.id), f"{child.id} asked a question because {problem.obstacle}, and {child.id} wanted to make things better."),
        ("How did they solve it?", f"They solved it with {solution.label}. That choice fit the problem and helped everyone relax."),
    ]
    qa.append(("What did the child think?", f"{child.id} thought that a kind answer could make the whole room feel kinder too."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["problem"].tags) | set(world.facts["solution"].tags) | {"question", "centre", "humid"}
    knowledge = {
        "question": [("What is a question?", "A question is something you ask when you want to learn, solve a problem, or understand more.")],
        "centre": [("What is a centre?", "A centre is a place where people gather to do activities, learn, or get help together.")],
        "humid": [("What does humid mean?", "Humid means the air feels wet or sticky because there is a lot of moisture in it.")],
        "problem": [("What is problem solving?", "Problem solving means thinking carefully about what is wrong and choosing a good way to fix it.")],
        "kind": [("Why is kindness important?", "Kindness matters because it helps people feel safe, heard, and cared for.")],
    }
    order = ["question", "centre", "humid", "problem", "kind"]
    out = []
    for tag in order:
        if tag in tags and tag in knowledge:
            out.extend(knowledge[tag])
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
solvable(P, S) :- problem(P), solution(S), tag(S, P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for sid, sol in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        for t in sorted(sol.tags):
            lines.append(asp.fact("tag", sid, t))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show solvable/2."))
    return sorted(set(asp.atoms(model, "solvable")))


def asp_verify() -> int:
    import asp
    py = set((p, s) for p, _, s in valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, solution=None, child=None, child_gender=None, helper=None, helper_gender=None, helper_role="volunteer"), random.Random(777)))
        assert sample.story
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], SOLUTIONS[params.solution],
                 params.child, params.child_gender, params.helper, params.helper_gender, params.helper_role)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    StoryParams("community_centre", "lost_crayons", "sort_drawer", "Maya", "girl", "Nadia", "girl", "volunteer", "kind"),
    StoryParams("neighbourhood_centre", "stuck_puzzle", "match_pieces", "Noah", "boy", "Amina", "girl", "helper", "patient"),
    StoryParams("after_school_centre", "humid_stickers", "fan_and_towel", "Lila", "girl", "Eli", "boy", "coach", "gentle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show solvable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} solvable combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        print(json.dumps(samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
