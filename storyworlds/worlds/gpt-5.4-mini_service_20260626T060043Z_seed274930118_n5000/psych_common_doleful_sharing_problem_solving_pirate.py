#!/usr/bin/env python3
"""
storyworlds/worlds/psych_common_doleful_sharing_problem_solving_pirate.py
=========================================================================

A small pirate-tale storyworld about sharing, doleful feelings, and problem
solving on a shared ship.

Premise:
- A young pirate loves a common treasure or snack.
- Another pirate needs it too.
- The first pirate feels doleful at the thought of giving it up.
- A problem-solving helper suggests sharing in a fair way.
- The ship ends with a gentle, child-facing resolution.

Seed words: psych, common, doleful
Style: Pirate Tale
Features: Sharing, Problem Solving
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
# Shared world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    shared_with: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "pirate_girl"}
        male = {"boy", "father", "man", "pirate_boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class CrewMate:
    id: str
    type: str
    label: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"hunger": 0.0, "tired": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"joy": 0.0, "doleful": 0.0, "care": 0.0, "problem_solving": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "pirate_girl"}
        male = {"boy", "father", "man", "pirate_boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, Entity | CrewMate] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    shore: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    need: str
    divisible: bool = True


@dataclass
class Problem:
    id: str
    want: str
    issue: str
    fix_hint: str
    keywords: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    method: str
    fair_share: str
    needs: set[str]


SETTINGS = {
    "deck": Setting(place="the deck", shore="the sea", affords={"share", "solve"}),
    "galley": Setting(place="the galley", shore="the ship's kitchen", affords={"share", "solve"}),
    "cove": Setting(place="the cove", shore="the quiet shore", affords={"share", "solve"}),
}

ITEMS = {
    "biscuits": Item(id="biscuits", label="biscuits", phrase="a tin of common biscuits", need="hunger"),
    "map": Item(id="map", label="map", phrase="a common map of the island", need="direction"),
    "lantern": Item(id="lantern", label="lantern", phrase="one lantern that kept the dark away", need="light"),
}

PROBLEMS = {
    "snack": Problem(
        id="snack",
        want="eat",
        issue="there was only one small tin for two hungry pirates",
        fix_hint="split it fairly",
        keywords={"common", "sharing"},
    ),
    "dark": Problem(
        id="dark",
        want="see the way",
        issue="the lantern was too dim for the whole crew to use at once",
        fix_hint="take turns and share the light",
        keywords={"problem", "solving"},
    ),
    "map": Problem(
        id="map",
        want="find the cove",
        issue="the old map was folded tight and everyone wanted a look",
        fix_hint="hold it open together",
        keywords={"common", "psych"},
    ),
}

SOLUTIONS = {
    "split": Solution(
        id="split",
        label="a fair split",
        method="cut the biscuits into even pieces",
        fair_share="each pirate got the same amount",
        needs={"biscuits"},
    ),
    "turns": Solution(
        id="turns",
        label="taking turns",
        method="pass the lantern from hand to hand",
        fair_share="no one had to stay in the dark for long",
        needs={"lantern"},
    ),
    "together": Solution(
        id="together",
        label="holding it together",
        method="spread the map flat between two hands",
        fair_share="both pirates could study the same map at once",
        needs={"map"},
    ),
}

NAMES = ["Pip", "Mara", "Jory", "Nell", "Rory", "Tess", "Finn", "Sail", "Bo", "Wren"]
TYPES = ["pirate_boy", "pirate_girl"]
TRAITS = ["brave", "small", "quick", "curious", "cheerful", "doleful"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    problem: str
    item: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for p in PROBLEMS:
            for i in ITEMS:
                if _matches(p, i):
                    out.append((s, p, i))
    return out


def _matches(problem_id: str, item_id: str) -> bool:
    p = PROBLEMS[problem_id]
    i = ITEMS[item_id]
    if problem_id == "snack":
        return i.need == "hunger"
    if problem_id == "dark":
        return i.need == "light"
    if problem_id == "map":
        return i.need == "direction"
    return False


def _choose_solution(problem_id: str) -> Solution:
    return {"snack": SOLUTIONS["split"], "dark": SOLUTIONS["turns"], "map": SOLUTIONS["together"]}[problem_id]


def _choose_helpful_line(problem_id: str) -> str:
    return {
        "snack": "Let's share it evenly, so nobody goes hungry.",
        "dark": "Let's take turns with the lantern, so the whole crew can see.",
        "map": "Let's hold the map open together, so we can all read it.",
    }[problem_id]


# ---------------------------------------------------------------------------
# Narration
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    world = World(params.setting)
    hero = world.add(CrewMate(id=params.hero, type=params.hero_type, label=params.hero, traits=["young", params.trait]))
    helper = world.add(CrewMate(id=params.helper, type=params.helper_type, label=params.helper, traits=["steady", "kind"]))
    item_cfg = ITEMS[params.item]
    item = world.add(Entity(id=params.item, kind="thing", type="thing", label=item_cfg.label, phrase=item_cfg.phrase, owner=hero.id))
    item.memes["precious"] = 1.0

    problem = PROBLEMS[params.problem]
    solution = _choose_solution(params.problem)

    # Act 1
    world.say(f"On {SETTINGS[params.setting].place}, {hero.id} found {item.phrase}.")
    world.say(f"{hero.pronoun().capitalize()} liked {item.label} because it was a common thing the crew could use on a long sail.")
    world.say(f"But then {helper.id} came close, and {problem.issue}.")

    # Act 2
    world.para()
    hero.memes["doleful"] += 1.0
    hero.memes["care"] += 1.0
    helper.memes["problem_solving"] += 1.0
    world.say(f"{hero.id} felt doleful and looked down at the boards.")
    world.say(f"{helper.id} did not grab the {item.label}; instead, {helper.pronoun()} spoke softly: \"{_choose_helpful_line(params.problem)}\"")
    world.say(f"That was a fine problem-solving idea, because it helped the crew keep peace on the ship.")

    # Act 3
    world.para()
    if params.problem == "snack":
        item.shared_with = [helper.id]
        world.say(f"{hero.id} used a small knife to {solution.method}. {solution.fair_share}.")
        world.say(f"{hero.id} gave one piece to {helper.id}, and kept one piece too.")
    elif params.problem == "dark":
        item.shared_with = [helper.id]
        world.say(f"{hero.id} and {helper.id} chose {solution.label}. They {solution.method}, and {solution.fair_share}.")
    else:
        item.shared_with = [helper.id]
        world.say(f"{hero.id} and {helper.id} chose {solution.label}. They {solution.method}, and {solution.fair_share}.")
    hero.memes["joy"] += 1.0
    hero.memes["doleful"] = 0.0
    world.say(f"By the end, the {item.label} was still useful, and both pirates smiled at the calm sea.")

    world.facts.update(
        hero=hero,
        helper=helper,
        item=item,
        problem=problem,
        solution=solution,
        setting=SETTINGS[params.setting],
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: CrewMate = f["hero"]
    helper: CrewMate = f["helper"]
    item: Entity = f["item"]
    problem: Problem = f["problem"]
    return [
        f'Write a short pirate tale for a child about "{item.label}" and the word "common".',
        f"Tell a doleful pirate story where {hero.id} and {helper.id} solve a sharing problem on the ship.",
        f"Write a simple story in which two pirates use problem solving to share {item.phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: CrewMate = f["hero"]
    helper: CrewMate = f["helper"]
    item: Entity = f["item"]
    problem: Problem = f["problem"]
    solution: Solution = f["solution"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who felt doleful when the {item.label} turned into a sharing problem?",
            answer=f"{hero.id} felt doleful at first, because {item.label} was important and there was only one for the crew.",
        ),
        QAItem(
            question=f"What did {helper.id} do to solve the problem about the {item.label}?",
            answer=f"{helper.id} used problem solving and suggested {solution.label}, which was a fair way to handle the {problem.issue}.",
        ),
        QAItem(
            question=f"How did the pirates share the {item.label} in the end?",
            answer=f"They chose {solution.label}. That meant {solution.fair_share}.",
        ),
        QAItem(
            question=f"Where did the story happen?",
            answer=f"It happened on {setting.place}, a pirate place where the crew could meet and solve problems together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to share something?",
            answer="To share something means to let more than one person use it, have it, or enjoy it in a fair way.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking about a trouble and finding a good plan to fix it.",
        ),
        QAItem(
            question="What does doleful mean?",
            answer="Doleful means feeling sad or gloomy.",
        ),
        QAItem(
            question="Why do pirates use common things together?",
            answer="Pirates use common things together because ships are small and the crew often has to share what they have.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in world.entities.values():
        bits = []
        if isinstance(e, CrewMate):
            if e.memes:
                bits.append(f"memes={e.memes}")
        else:
            bits.append(f"owner={e.owner}")
            if e.shared_with:
                bits.append(f"shared_with={e.shared_with}")
            if e.memes:
                bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {e.label} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
problem(P) :- problem_id(P).
item(I) :- item_id(I).
setting(S) :- setting_id(S).

valid(S,P,I) :- setting(S), problem(P), item(I), matches(P,I).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_id", s))
    for p in PROBLEMS:
        lines.append(asp.fact("problem_id", p))
    for i in ITEMS:
        lines.append(asp.fact("item_id", i))
    for p in PROBLEMS:
        for i in ITEMS:
            if _matches(p, i):
                lines.append(asp.fact("matches", p, i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: ASP matches Python valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    print("only ASP:", sorted(a - b))
    print("only Python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Story API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld about sharing and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, item = rng.choice(sorted(combos))
    hero_type = rng.choice(TYPES)
    helper_type = rng.choice(TYPES)
    hero = args.name if hasattr(args, "name") and args.name else rng.choice(NAMES)
    helper = rng.choice([n for n in NAMES if n != hero])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, problem=problem, item=item, hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="deck", problem="snack", item="biscuits", hero="Pip", hero_type="pirate_boy", helper="Mara", helper_type="pirate_girl", trait="doleful"),
    StoryParams(setting="galley", problem="dark", item="lantern", hero="Nell", hero_type="pirate_girl", helper="Jory", helper_type="pirate_boy", trait="curious"),
    StoryParams(setting="cove", problem="map", item="map", hero="Rory", hero_type="pirate_boy", helper="Tess", helper_type="pirate_girl", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            except StoryError as e:
                print(e)
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
            header = f"### {p.hero}: {p.problem} with {p.item} on {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
