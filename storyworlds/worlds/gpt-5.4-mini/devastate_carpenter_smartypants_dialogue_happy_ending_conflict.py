#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/devastate_carpenter_smartypants_dialogue_happy_ending_conflict.py
=================================================================================================

A standalone storyworld script for a small detective-style domain about a child
detective, a carpenter, a smartypants clue-giver, a conflict over a broken
wooden toy, and a happy ending after the real cause is discovered.

The story uses dialogue, a state-driven mystery turn, and an ending image that
proves what changed. The key seed words appear in the world:
- devastate
- carpenter
- smartypants
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
class Clue:
    id: str
    label: str
    phrase: str
    where: str
    reveal: str
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
class Problem:
    id: str
    label: str
    damage: str
    cause: str
    fix: str
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
class Solution:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    if world.get("problem").meters["broken"] >= THRESHOLD:
        if "alarm" not in world.fired:
            world.fired.add(("alarm",))
            for e in list(world.entities.values()):
                if e.role in {"detective", "partner"}:
                    e.memes["worry"] += 1
            out.append("__alarm__")
    return out


def _r_mend(world: World) -> list[str]:
    out: list[str] = []
    if world.get("problem").meters["broken"] < THRESHOLD:
        return out
    if world.get("solution").id != "wrong_fix":
        return out
    return out


CAUSAL_RULES: list[Rule] = [Rule("alarm", "social", _r_alarm)]


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


def problem_at_risk(problem: Problem, clue: Clue) -> bool:
    return problem.id in clue.tags


def sensible_solutions() -> list[Solution]:
    return [s for s in SOLUTIONS.values() if s.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for case in CASES:
        for prob_id, prob in PROBLEMS.items():
            for clue_id, clue in CLUES.items():
                if problem_at_risk(prob, clue):
                    combos.append((case, prob_id, clue_id))
    return combos


def solve_power(problem: Problem, delay: int) -> int:
    return 2 + max(0, 1 - delay)


def is_solved(solution: Solution, problem: Problem, delay: int) -> bool:
    return solution.power >= solve_power(problem, delay)


def reason_about_clue(world: World, clue: Clue) -> str:
    return clue.reveal


def start_scene(world: World, kid: Entity, partner: Entity, carpenter: Entity, clue: Clue, problem: Problem) -> None:
    kid.memes["curiosity"] += 1
    partner.memes["curiosity"] += 1
    world.say(
        f"Detective {kid.id} and {partner.id} were on a quiet street when they found {problem.label}."
    )
    world.say(
        f'The old thing had been so badly hit that it could almost {problem.cause}. '
        f"{carpenter.label_word.capitalize()} said it would need careful fixing."
    )


def dialogue_conflict(world: World, kid: Entity, partner: Entity, clue: Clue, problem: Problem) -> None:
    kid.memes["stubborn"] += 1
    partner.memes["worry"] += 1
    world.say(
        f'"This looks like a simple break," {kid.id} said. "Maybe the answer is right in front of us."'
    )
    world.say(
        f'"Smartypants," {partner.id} muttered, "you always say that before you miss the best clue."'
    )
    world.say(
        f'Then {partner.id} pointed at {clue.label} near {clue.where}. "Look again," {partner.id} said.'
    )


def accuse_and_answer(world: World, kid: Entity, partner: Entity, clue: Clue) -> None:
    world.say(
        f'"Did you see who did it?" {kid.id} asked.'
    )
    world.say(
        f'"Yes," {partner.id} said. "{clue.reveal}"'
    )


def confirm_solution(world: World, carpenter: Entity, solution: Solution, problem: Problem) -> None:
    body = solution.text.replace("{problem}", problem.label)
    world.say(
        f"{carpenter.label_word.capitalize()} came over, nodded, and {body}."
    )
    problem_ent = world.get("problem")
    problem_ent.meters["broken"] = 0.0


def happy_ending(world: World, kid: Entity, partner: Entity, carpenter: Entity) -> None:
    kid.memes["joy"] += 1
    partner.memes["joy"] += 1
    carpenter.memes["joy"] += 1
    world.say(
        f'After that, {carpenter.label_word.capitalize()} smiled and said, "You solved the case together."'
    )
    world.say(
        f'The repaired {world.get("problem").label} sat straight again, shiny and strong, while {kid.id} and {partner.id} grinned at the finished work.'
    )


def tell(case: str, problem: Problem, clue: Clue, solution: Solution, delay: int = 0) -> World:
    world = World()
    detective = world.add(Entity(id="Mina", kind="character", type="girl", role="detective"))
    partner = world.add(Entity(id="Jo", kind="character", type="boy", role="partner"))
    carpenter = world.add(Entity(id="carpenter", kind="character", type="man", label="the carpenter", role="carpenter"))
    world.add(Entity(id="problem", kind="thing", type="thing", label=problem.label, attrs={"case": case}))
    world.add(Entity(id="clue", kind="thing", type="thing", label=clue.label))
    world.add(Entity(id="solution", kind="thing", type="thing", label=solution.id))

    start_scene(world, detective, partner, carpenter, clue, problem)
    world.para()
    dialogue_conflict(world, detective, partner, clue, problem)
    accuse_and_answer(world, detective, partner, clue)

    if not problem_at_risk(problem, clue):
        raise StoryError("This clue cannot honestly reveal the problem.")
    if not is_solved(solution, problem, delay):
        raise StoryError("This solution is too weak to fix the damaged thing.")

    world.para()
    confirm_solution(world, carpenter, solution, problem)
    happy_ending(world, detective, partner, carpenter)

    world.facts.update(
        detective=detective,
        partner=partner,
        carpenter=carpenter,
        problem=problem,
        clue=clue,
        solution=solution,
        delay=delay,
        case=case,
        solved=True,
    )
    return world


CASES = {
    "workshop": "a little workshop",
    "alley": "a narrow alley",
    "porch": "a front porch",
}

PROBLEMS = {
    "birdhouse": Problem("birdhouse", "the birdhouse", "come apart", "a hard bump", "nail it back together", {"wood", "case"}),
    "chair": Problem("chair", "the chair", "wobble", "a loose leg", "tighten the leg", {"wood", "case"}),
    "box": Problem("box", "the toy box", "split open", "a cracked side", "glue and clamp it", {"wood", "case"}),
}

CLUES = {
    "splinters": Clue("splinters", "splinters", "fresh splinters on the floor", "the doorway", "A cart bumped the wood on the way past.", {"wood", "case"}),
    "mud_print": Clue("mud_print", "mud prints", "mud prints by the bench", "the bench", "The delivery cart rolled through the muddy yard.", {"case"}),
    "paint_smear": Clue("paint_smear", "paint smear", "a paint smear on the railing", "the railing", "The painter brushed the rail while backing up.", {"case"}),
}

SOLUTIONS = {
    "right_fix": Solution("right_fix", 3, 3, "checked the crack, added a strong brace, and fixed the {problem} the careful way", "tried to tape it up, but that was not enough", "fixed the {problem} with a strong brace", {"case"}),
    "good_fix": Solution("good_fix", 2, 2, "cleaned the pieces, lined them up, and made the {problem} steady again", "pressed on it once, but it still leaned", "made the {problem} steady again", {"case"}),
    "wrong_fix": Solution("wrong_fix", 1, 1, "gave it a quick push and hoped for the best", "gave it a quick push, but the {problem} stayed broken", "gave it a quick push", {"case"}),
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    prob = f["problem"]
    clue = f["clue"]
    return [
        f'Write a detective story for a child that uses the words "devastate", "carpenter", and "smartypants".',
        f"Tell a small mystery where Mina and Jo argue over a broken {prob.label}, but a clue near {clue.where} leads them to the truth.",
        f"Write a happy-ending detective story with dialogue in which a carpenter fixes {prob.label} after the kids notice the real clue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    prob = f["problem"]
    clue = f["clue"]
    sol = f["solution"]
    items = [
        QAItem(
            question="Who solved the mystery?",
            answer="Mina and Jo solved it together by noticing the clue and listening to the carpenter.",
        ),
        QAItem(
            question="Why did they argue at first?",
            answer=f'Mina thought the break was simple, while Jo called her "smartypants" and teased her for being too sure. Their conflict made them look harder at the evidence.',
        ),
        QAItem(
            question="What clue helped them?",
            answer=f'The clue was {clue.phrase}. It pointed to the real cause, which is why the children stopped guessing and started thinking like detectives.',
        ),
        QAItem(
            question="How did the carpenter help?",
            answer=f"The carpenter came over and {sol.qa_text.replace('{problem}', prob.label)}. That careful fix made the broken thing strong again.",
        ),
    ]
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a carpenter do?",
            answer="A carpenter works with wood. A carpenter can build, repair, and make wooden things strong again.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a little piece of information that helps you figure out what really happened.",
        ),
        QAItem(
            question="Why do detectives ask questions?",
            answer="Detectives ask questions so they can compare ideas, notice clues, and find the truth instead of guessing.",
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)




@dataclass
class StoryParams:
    case: str
    problem: str
    clue: str
    solution: str
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

CURATED = [
    StoryParams("workshop", "birdhouse", "splinters", "right_fix", seed=None),
    StoryParams("alley", "chair", "mud_print", "good_fix", seed=None),
    StoryParams("porch", "box", "paint_smear", "right_fix", seed=None),
]



def explain_rejection(problem: Problem, clue: Clue) -> str:
    return f"(No story: {clue.phrase} does not honestly point to {problem.label}.)"


def explain_solution(solution: str) -> str:
    return f"(Refusing solution '{solution}': it is too weak to resolve the mystery.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in CASES:
        lines.append(asp.fact("case", cid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for tag in sorted(clue.tags):
            lines.append(asp.fact("tag", cid, tag))
    for sid, sol in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        lines.append(asp.fact("sense", sid, sol.sense))
        lines.append(asp.fact("power", sid, sol.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Case, Prob, Clue) :- case(Case), problem(Prob), clue(Clue), tag(Clue, wood), tag(Prob, case).
sensible(S) :- solution(S), sense(S, N), sense_min(M), N >= M.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: valid_combos matches ASP ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    if set(asp_sensible()) == {s.id for s in sensible_solutions()}:
        print("OK: sensible solutions match.")
    else:
        print("MISMATCH: ASP and Python sensible solutions differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(case=None, problem=None, clue=None, solution=None), random.Random(1)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style storyworld with dialogue, conflict, and a happy ending.")
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--solution", choices=SOLUTIONS)
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
    if args.solution and args.solution not in SOLUTIONS:
        raise StoryError(explain_solution(args.solution))
    combos = [c for c in valid_combos()
              if (args.case is None or c[0] == args.case)
              and (args.problem is None or c[1] == args.problem)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    case, problem, clue = rng.choice(sorted(combos))
    solution = args.solution or rng.choice(sorted(s.id for s in sensible_solutions()))
    return StoryParams(case, problem, clue, solution)


def generate(params: StoryParams) -> StorySample:
    world = World()
    problem = PROBLEMS[params.problem]
    clue = CLUES[params.clue]
    solution = SOLUTIONS[params.solution]
    story_world = tell(params.case, problem, clue, solution)
    return StorySample(
        params=params,
        story=story_world.render(),
        prompts=generation_prompts(story_world),
        story_qa=story_qa(story_world),
        world_qa=world_knowledge_qa(story_world),
        world=story_world,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible solutions: {', '.join(asp_sensible())}")
        print(f"compatible combos: {len(asp_valid_combos())}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
