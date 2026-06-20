#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ammunition_quest_bravery_problem_solving_heartwarming.py
=======================================================================================

A standalone storyworld about a child-led quest, a brave choice, and a warm,
kind resolution.

Seed: ammunition
Style: heartwarming
Features: Quest, Bravery, Problem Solving

This world treats "ammunition" as a small box of practice darts for a toy archery
quest in a backyard game. The child wants to finish a pretend quest, discovers
that the toy darts are missing from the gear bag, and solves the problem with
care, courage, and help from a gentle adult. The ending proves that the quest
continues safely and the child feels proud, not triumphant in a loud way, but in
a warm, steady way.

The world model uses entities with physical meters and emotional memes, a small
forward-chaining engine, a reasonableness gate, an inline ASP twin, and three QA
sets grounded in the simulated state.
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    vital: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    missing_phrase: str
    risk_phrase: str
    fix_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    scout = world.facts.get("scout")
    if not scout:
        return out
    if scout.memes["worry"] >= THRESHOLD:
        sig = ("worry", scout.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("camp").meters["need"] += 1
            out.append("__need__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    helper = world.facts.get("helper")
    if not helper:
        return out
    if helper.memes["kindness"] >= THRESHOLD and world.get("camp").meters["need"] >= THRESHOLD:
        sig = ("calm", helper.id)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["hope"] += 1
            out.append("__hope__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("calm", _r_calm)]


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


def reasonableness_ok(item: QuestItem, problem: Problem) -> bool:
    return item.vital and "missing" in problem.tags


def sensible_solutions() -> list[Solution]:
    return [s for s in SOLUTIONS.values() if s.sense >= SENSE_MIN]


def solve_strength(problem: Problem, delay: int) -> int:
    return 1 + delay


def can_solve(solution: Solution, problem: Problem, delay: int) -> bool:
    return solution.power >= solve_strength(problem, delay)


def predict_loss(world: World, item: QuestItem) -> dict:
    sim = world.copy()
    sim.get("bag").meters["scattered"] += 1
    return {"missing": bool(item.vital), "need": sim.get("camp").meters["need"]}


def setup(world: World, scout: Entity, guide: Entity, quest_item: QuestItem) -> None:
    scout.memes["joy"] += 1
    guide.memes["care"] += 1
    world.say(
        f"On a bright afternoon, {scout.id} and {guide.id} set out on a little quest in the backyard. "
        f"{scout.id} carried a map, a string bracelet, and the hope of finding the lost gear."
    )
    world.say(
        f"The most important thing in the bag was the practice ammunition for the toy archery game: "
        f"{quest_item.phrase}."
    )


def problem_arrives(world: World, scout: Entity, problem: Problem, quest_item: QuestItem) -> None:
    scout.memes["worry"] += 1
    world.say(
        f"At the stone path, {scout.id} stopped and looked into the bag. The {problem.label} was gone."
    )
    world.say(
        f'"Oh no," {scout.id} whispered. "Without {quest_item.label}, I cannot finish the quest."'
    )


def brave_search(world: World, scout: Entity, guide: Entity, problem: Problem) -> None:
    scout.memes["bravery"] += 1
    world.say(
        f"{scout.id} took a deep breath. Even with a small knot in {scout.pronoun('possessive')} tummy, "
        f"{scout.pronoun()} kept searching instead of giving up."
    )
    world.say(
        f'"We can solve this," {guide.id} said kindly. "Brave does not mean loud. Brave means staying with the problem."'
    )


def search_and_find(world: World, scout: Entity, quest_item: QuestItem, problem: Problem) -> None:
    bag = world.get("bag")
    bag.meters["searched"] += 1
    world.say(
        f"They looked under the bench, behind the watering can, and inside the flower crate. "
        f"Then {scout.id} found the missing {quest_item.label} tucked under a folded towel."
    )
    world.say(
        f"{scout.id} held it up like a treasure. The quest piece had not been lost after all; it had only been misplaced."
    )


def warm_fix(world: World, scout: Entity, guide: Entity, solution: Solution, quest_item: QuestItem) -> None:
    scout.memes["joy"] += 1
    scout.memes["relief"] += 1
    guide.memes["relief"] += 1
    world.say(
        f"{guide.id} smiled and helped place the {quest_item.label} back into the pouch. "
        f"Then {guide.id} praised {scout.id} for using careful thinking."
    )
    world.say(
        f'"You kept going, asked for help, and solved the problem," {guide.id} said. '
        f'"That is the kind of bravery that keeps a quest kind."'
    )
    world.say(
        f"After that, the practice ammunition was ready again, and the little archery quest could continue safely."
    )


def tell(quest_item: QuestItem, problem: Problem, solution: Solution,
         scout_name: str = "Mina", scout_gender: str = "girl",
         guide_name: str = "Grandma", guide_gender: str = "woman") -> World:
    world = World()
    scout = world.add(Entity(id=scout_name, kind="character", type=scout_gender, role="scout"))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_gender, role="guide"))
    camp = world.add(Entity(id="camp", type="place", label="the camp table"))
    bag = world.add(Entity(id="bag", type="thing", label="the gear bag"))
    world.facts.update(scout=scout, guide=guide, camp=camp, bag=bag, quest_item=quest_item, problem=problem, solution=solution)

    setup(world, scout, guide, quest_item)
    world.para()
    problem_arrives(world, scout, problem, quest_item)
    brave_search(world, scout, guide, problem)
    world.para()
    search_and_find(world, scout, quest_item, problem)
    warm_fix(world, scout, guide, solution, quest_item)

    world.facts.update(
        outcome="solved",
        found=True,
        bravery=scout.memes["bravery"],
        relief=scout.memes["relief"],
    )
    return world


QUEST_ITEMS = {
    "ammunition": QuestItem(
        "ammunition",
        "ammunition",
        "the little practice ammunition",
        vital=True,
        tags={"ammunition", "quest"},
    ),
    "arrows": QuestItem("arrows", "arrows", "the practice arrows", vital=True, tags={"quest"}),
    "marbles": QuestItem("marbles", "marbles", "the shiny marbles", vital=False, tags={"toy"}),
}

PROBLEMS = {
    "missing_bag": Problem(
        "missing_bag",
        "missing gear",
        "the gear was missing",
        "the quest would stop",
        "look in calm places first",
        tags={"missing"},
    ),
    "tipped_box": Problem(
        "tipped_box",
        "tipped box",
        "the box had tipped over",
        "the pieces might scatter",
        "sort the pieces together",
        tags={"missing"},
    ),
}

SOLUTIONS = {
    "search": Solution(
        "search", 3, 3,
        "looked carefully around the yard and found the missing piece",
        "looked carefully, but the missing piece was still nowhere to be seen",
        "looked carefully and found the missing piece",
        tags={"problem_solving"},
    ),
    "ask_help": Solution(
        "ask_help", 3, 2,
        "asked a kind grown-up for help and found the missing piece together",
        "asked for help, but nobody could find it in time",
        "asked a kind grown-up for help and found the missing piece together",
        tags={"heartwarming"},
    ),
    "rush": Solution(
        "rush", 1, 1,
        "ran around too fast and made the search harder",
        "ran around too fast and made the search harder",
        "ran around too fast and made the search harder",
    ),
}

GIRL_NAMES = ["Mina", "Ivy", "Luna", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Owen", "Milo", "Finn"]
GUIDE_NAMES = ["Grandma", "Grandpa", "Aunt Jo", "Uncle Ben", "Mom", "Dad"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for qid, item in QUEST_ITEMS.items():
        for pid, problem in PROBLEMS.items():
            for sid, solution in SOLUTIONS.items():
                if reasonableness_ok(item, problem) and solution.sense >= SENSE_MIN:
                    combos.append((qid, pid, sid))
    return combos


@dataclass
class StoryParams:
    quest_item: str
    problem: str
    solution: str
    scout_name: str
    scout_gender: str
    guide_name: str
    guide_gender: str
    delay: int = 0
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    qi = f["quest_item"]
    prob = f["problem"]
    return [
        f'Write a heartwarming story for a young child that includes the word "{qi.label}" and follows a small quest.',
        f"Tell a brave story where {f['scout'].id} notices a problem, keeps going, and solves it with help.",
        f"Write a gentle adventure about {f['scout'].id} and {f['guide'].id} finding missing quest gear and feeling proud at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    scout, guide = f["scout"], f["guide"]
    qi, prob = f["quest_item"], f["problem"]
    return [
        ("Who is the story about?",
         f"It is about {scout.id} and {guide.id}, who go on a small quest together."),
        ("What went missing?",
         f"The {qi.label} went missing, and that made the quest feel stuck for a moment."),
        ("How did they solve the problem?",
         f"They searched calmly, found the missing {qi.label}, and put it back where it belonged. "
         f"That kept the quest safe and let them continue."),
        ("How did the scout show bravery?",
         f"{scout.id} stayed with the problem instead of giving up. {scout.pronoun().capitalize()} kept looking, asked for help, and kept trying until the problem was solved."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["quest_item"].tags) | set(f["problem"].tags) | set(f["solution"].tags)
    qa: list[tuple[str, str]] = []
    if "ammunition" in tags:
        qa.append(("What is ammunition?", "Ammunition is the small thing that is loaded into a toy or tool so it can be used for practice or play. In this story it means the little practice pieces for the quest game."))
    qa.append(("What is problem solving?", "Problem solving means noticing what is wrong, thinking carefully, and choosing a way to fix it. It often includes looking, asking, and trying again."))
    qa.append(("What is bravery?", "Bravery means doing the hard thing even when you feel nervous. It can look quiet and gentle, like staying calm and keeping on.")
    )
    return qa


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("ammunition", "missing_bag", "search", "Mina", "girl", "Grandma", "woman", 0),
    StoryParams("arrows", "tipped_box", "ask_help", "Eli", "boy", "Mom", "woman", 0),
]


def explain_rejection(item: QuestItem, problem: Problem) -> str:
    if not reasonableness_ok(item, problem):
        return "(No story: the quest item is not important enough, or the problem does not really make it matter. Choose the vital ammunition-like piece and a missing-type problem.)"
    return "(No story: this combination is not reasonable.)"


def explain_response(rid: str) -> str:
    sol = SOLUTIONS[rid]
    return f"(Refusing solution '{rid}': it scores too low on common sense (sense={sol.sense} < {SENSE_MIN}).)"


ASP_RULES = r"""
reasonable(Q, P) :- quest_item(Q), vital(Q), problem(P), missing_problem(P).
sensible(S) :- solution(S), sense(S, N), sense_min(M), N >= M.
valid(Q, P, S) :- reasonable(Q, P), sensible(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for qid, q in QUEST_ITEMS.items():
        lines.append(asp.fact("quest_item", qid))
        if q.vital:
            lines.append(asp.fact("vital", qid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if "missing" in p.tags:
            lines.append(asp.fact("missing_problem", pid))
    for sid, s in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        lines.append(asp.fact("sense", sid, s.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(v for (v,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    if set(asp_sensible()) == {s.id for s in sensible_solutions()}:
        print("OK: sensible solutions match.")
    else:
        rc = 1
        print("MISMATCH in sensible solutions.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming quest storyworld about missing ammunition and brave problem solving.")
    ap.add_argument("--quest-item", choices=QUEST_ITEMS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--scout-name")
    ap.add_argument("--scout-gender", choices=["girl", "boy"])
    ap.add_argument("--guide-name")
    ap.add_argument("--guide-gender", choices=["woman", "man"])
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
    qid = args.quest_item or rng.choice(list(QUEST_ITEMS))
    pid = args.problem or rng.choice(list(PROBLEMS))
    sid = args.solution or rng.choice(list(SOLUTIONS))
    if not reasonableness_ok(QUEST_ITEMS[qid], PROBLEMS[pid]):
        raise StoryError(explain_rejection(QUEST_ITEMS[qid], PROBLEMS[pid]))
    if SOLUTIONS[sid].sense < SENSE_MIN:
        raise StoryError(explain_response(sid))
    if args.scout_gender == "girl":
        scout_name = args.scout_name or rng.choice(GIRL_NAMES)
    elif args.scout_gender == "boy":
        scout_name = args.scout_name or rng.choice(BOY_NAMES)
    else:
        scout_gender = rng.choice(["girl", "boy"])
        scout_name = args.scout_name or rng.choice(GIRL_NAMES if scout_gender == "girl" else BOY_NAMES)
        args.scout_gender = scout_gender
    guide_gender = args.guide_gender or rng.choice(["woman", "man"])
    guide_name = args.guide_name or rng.choice(GUIDE_NAMES)
    return StoryParams(qid, pid, sid, scout_name, args.scout_gender or "girl", guide_name, guide_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(QUEST_ITEMS[params.quest_item], PROBLEMS[params.problem], SOLUTIONS[params.solution],
                 params.scout_name, params.scout_gender, params.guide_name, params.guide_gender)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible solutions: {', '.join(asp_sensible())}")
        print(f"{len(asp_valid_combos())} compatible combos:")
        for c in asp_valid_combos():
            print(c)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.scout_name}: {p.quest_item} / {p.problem} / {p.solution}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
