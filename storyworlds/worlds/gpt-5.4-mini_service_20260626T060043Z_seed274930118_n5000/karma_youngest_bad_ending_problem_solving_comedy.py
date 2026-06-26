#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/karma_youngest_bad_ending_problem_solving_comedy.py
===============================================================================================================================

A small, standalone story world about a youngest child, comic karma, and a
problem that gets solved before it can turn into a bad ending.

Premise:
- The youngest child wants something small and shiny or tasty.
- They try a shortcut, because they are impatient and a little dramatic.
- Comic karma makes the shortcut backfire in a harmless way.
- A nearby helper or the child themself solves the problem with a simple plan.
- The ending proves what changed: the mess is fixed, the risk is gone, and the
  youngest child is smiling again.

The world is intentionally tiny and constraint-checked.  It is meant to produce
short, authored stories with a clear beginning, middle turn, and ending image.
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
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "brother", "father", "dad", "man"}
        female = {"girl", "sister", "mother", "mom", "woman"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    affords: set[str] = field(default_factory=set)
    indoors: bool = False


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    mishap: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    result: str
    solves: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    problem: str
    prize: str
    fix: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "kitchen": Place("kitchen", "the kitchen", {"snack", "reach", "share"}, indoors=True),
    "playroom": Place("playroom", "the playroom", {"toy", "reach", "share"}, indoors=True),
    "backyard": Place("backyard", "the backyard", {"kite", "cleanup", "reach"}, indoors=False),
    "laundry_room": Place("laundry_room", "the laundry room", {"reach", "cleanup"}, indoors=True),
}

PROBLEMS = {
    "snack": Problem(
        id="snack",
        verb="grab the snack jar",
        gerund="grabbing the snack jar",
        mishap="the lid slips and the crackers pop everywhere",
        risk="the snack might spill and make a silly mess",
        zone={"counter"},
        keyword="snack",
        tags={"food", "mess"},
    ),
    "toy": Problem(
        id="toy",
        verb="reach the toy shelf",
        gerund="reaching the toy shelf",
        mishap="the basket tips and the toys rattle down like rain",
        risk="the pile could tumble into a wobbly heap",
        zone={"shelf"},
        keyword="toy",
        tags={"toy", "mess"},
    ),
    "kite": Problem(
        id="kite",
        verb="catch the kite string",
        gerund="chasing the kite string",
        mishap="the string wraps around a chair leg in one very dramatic loop",
        risk="the kite could get stuck before the fun even starts",
        zone={"yard"},
        keyword="kite",
        tags={"kite", "outdoor"},
    ),
    "reach": Problem(
        id="reach",
        verb="reach the top shelf",
        gerund="stretching for the top shelf",
        mishap="the broom bonks the basket and sends one sock spinning",
        risk="the item could stay out of reach",
        zone={"shelf"},
        keyword="reach",
        tags={"reach", "mess"},
    ),
}

PRIZES = {
    "cookie_jar": Entity(id="cookie_jar", type="thing", label="cookie jar", phrase="a glass cookie jar"),
    "toy_robot": Entity(id="toy_robot", type="thing", label="toy robot", phrase="a red toy robot"),
    "kite_reel": Entity(id="kite_reel", type="thing", label="kite reel", phrase="a bright blue kite reel"),
    "sock_basket": Entity(id="sock_basket", type="thing", label="sock basket", phrase="a basket full of socks"),
}

FIXES = {
    "stool": Fix(
        id="stool",
        label="a sturdy stool",
        prep="move a sturdy stool over",
        result="the youngest climbed up safely",
        solves={"snack", "reach", "toy"},
        covers={"counter", "shelf"},
    ),
    "ask": Fix(
        id="ask",
        label="a quick ask",
        prep="ask for help",
        result="the helper lifted the prize down",
        solves={"snack", "toy", "kite", "reach"},
        covers={"counter", "shelf", "yard"},
    ),
    "towel": Fix(
        id="towel",
        label="a clean towel",
        prep="spread out a clean towel",
        result="the mess landed neatly on the towel",
        solves={"snack"},
        covers={"counter"},
    ),
    "hook": Fix(
        id="hook",
        label="a hook on a pole",
        prep="use a hook on a pole",
        result="the prize came down without a wobble",
        solves={"reach", "toy"},
        covers={"shelf"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Ava", "Lily", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Theo", "Finn", "Max", "Noah"]
TRAITS = ["tiny", "bright", "impulsive", "cheerful", "bouncy", "sly"]


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------
def valid_combo(place: Place, problem: Problem, prize: Entity, fix: Fix) -> bool:
    if problem.id not in place.affords:
        return False
    if problem.id not in fix.solves:
        return False
    if not (problem.zone & fix.covers):
        return False
    return True


def all_valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for p_id, place in PLACES.items():
        for pr_id, problem in PROBLEMS.items():
            for z_id, prize in PRIZES.items():
                for f_id, fix in FIXES.items():
                    if valid_combo(place, problem, prize, fix):
                        out.append((p_id, pr_id, z_id, f_id))
    return out


def explain_rejection(place: Place, problem: Problem, prize: Entity, fix: Fix) -> str:
    return (
        f"(No story: {fix.label} does not actually solve the {problem.id} problem at {place.label}, "
        f"or it does not help with the right spot. The comedy needs a real fix, not a random prop.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def maybe_karma(world: World, youngest: Entity, problem: Problem) -> None:
    youngest.memes["impatience"] = youngest.memes.get("impatience", 0) + 1
    youngest.memes["want"] = youngest.memes.get("want", 0) + 1
    world.say(
        f"{youngest.id} was the youngest in the house, and that made {youngest.pronoun('object')} "
        f"both quick and dramatic. {youngest.pronoun('subject').capitalize()} wanted to {problem.verb} right away."
    )
    world.say(
        f"Then karma arrived in a goofy little way: {problem.mishap}."
    )
    youngest.meters["mishap"] = youngest.meters.get("mishap", 0) + 1


def solve_problem(world: World, youngest: Entity, helper: Entity, problem: Problem, prize: Entity, fix: Fix) -> None:
    youngest.memes["worry"] = youngest.memes.get("worry", 0) + 1
    world.say(
        f"{youngest.id} froze for a moment because {problem.risk}."
    )
    world.say(
        f"Then {helper.id} pointed at {fix.label} and said, \"Let's {fix.prep}.\""
    )
    if fix.id == "ask":
        world.say(f"{helper.id} lifted {prize.label} down with a grin, and nobody had to chase anything.")
    elif fix.id == "stool":
        world.say(f"{youngest.id} climbed up carefully, and {fix.result}.")
    elif fix.id == "towel":
        world.say(f"{helper.id} spread the towel under the jar, so the crumbs stayed in one tidy spot.")
    else:
        world.say(f"{fix.result}.")
    youngest.memes["relief"] = youngest.memes.get("relief", 0) + 1
    youngest.memes["joy"] = youngest.memes.get("joy", 0) + 1
    world.say(
        f"In the end, {youngest.id} laughed at the silly chaos, and {helper.id} laughed too."
    )


def build_story(world: World, params: StoryParams) -> None:
    youngest = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper_type = "mother" if params.helper == "mother" else "father"
    helper_name = "Mom" if params.helper == "mother" else "Dad"
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label=helper_name))

    problem = PROBLEMS[params.problem]
    prize = world.add(Entity(
        id=params.prize,
        type=PRIZES[params.prize].type,
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        owner=youngest.id,
        caretaker=helper.id,
    ))
    fix = FIXES[params.fix]

    youngest.memes["youngest"] = 1
    youngest.memes["karma"] = 1

    world.say(
        f"{youngest.id} was the youngest child in the family, and {youngest.pronoun('subject')} thought that made {youngest.pronoun('object')} extra clever."
    )
    world.say(
        f"At {world.place.label}, {youngest.id} wanted to {problem.verb} because {prize.label} looked too tempting to ignore."
    )
    maybe_karma(world, youngest, problem)

    world.para()
    world.say(
        f"{helper.id} saw the tiny disaster and did not make it worse. {helper.id} just said, \"We can solve this.\""
    )
    solve_problem(world, youngest, helper, problem, prize, fix)

    world.facts.update(
        youngest=youngest,
        helper=helper,
        problem=problem,
        prize=prize,
        fix=fix,
        place=world.place,
        resolved=True,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedy story about a youngest child named {f["youngest"].id} and a small problem at {f["place"].label}.',
        f"Tell a story where karma makes {f['youngest'].id}'s quick idea backfire, then a helper solves the mess.",
        f'Write a child-friendly funny story that includes the words "karma" and "youngest" and ends with a problem being solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    youngest: Entity = f["youngest"]
    helper: Entity = f["helper"]
    problem: Problem = f["problem"]
    prize: Entity = f["prize"]
    fix: Fix = f["fix"]
    return [
        QAItem(
            question=f"Who was the youngest child in the story?",
            answer=f"{youngest.id} was the youngest child, and {youngest.pronoun('subject')} was the one who tried to move fast.",
        ),
        QAItem(
            question=f"What silly karma happened when {youngest.id} tried to {problem.verb}?",
            answer=f"Karma showed up as a goofy mishap: {problem.mishap}.",
        ),
        QAItem(
            question=f"How did {helper.id} help with the problem?",
            answer=f"{helper.id} used {fix.label} and helped solve the problem so {prize.label} could be handled safely.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The mess was under control, the prize was safe, and {youngest.id} was laughing instead of worrying.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "karma": [
        QAItem(
            question="What does karma mean in a kid-friendly story?",
            answer="Karma means a choice can lead to a matching result, like a silly shortcut causing a silly problem.",
        )
    ],
    "youngest": [
        QAItem(
            question="What is the youngest child in a family?",
            answer="The youngest child is the child who was born last, so everyone else is older.",
        )
    ],
    "stool": [
        QAItem(
            question="What is a stool for?",
            answer="A stool is a small seat that can also help a child reach something a little higher, if a grown-up says it is safe.",
        )
    ],
    "towel": [
        QAItem(
            question="Why use a towel for a mess?",
            answer="A towel can catch crumbs or spills so the mess stays in one place and is easier to clean.",
        )
    ],
    "ask": [
        QAItem(
            question="Why is it smart to ask for help sometimes?",
            answer="Asking for help can keep a small problem from becoming a bigger one, and it often saves time.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = {"karma", "youngest"}
    fix: Fix = world.facts["fix"]
    if fix.id in WORLD_KNOWLEDGE:
        tags.add(fix.id)
    for tag in ["karma", "youngest", fix.id]:
        out.extend(WORLD_KNOWLEDGE.get(tag, []))
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(parts)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place_affords(P, A) :- affords(P, A).
problem_can_be_solved(A, F) :- solves(F, A).
fix_covers(F, Z) :- covers(F, Z).
compatible(P, A, F) :- place_affords(P, A), problem_can_be_solved(A, F), fix_covers(F, Z), problem_zone(A, Z).
valid_story(P, A, Prize, F) :- compatible(P, A, F), prize(Prize).
#show valid_story/4.
#show compatible/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", aid))
        for z in sorted(prob.zone):
            lines.append(asp.fact("problem_zone", aid, z))
    for pr in PRIZES:
        lines.append(asp.fact("prize", pr))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for s in sorted(fix.solves):
            lines.append(asp.fact("solves", fid, s))
        for c in sorted(fix.covers):
            lines.append(asp.fact("covers", fid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    python_set = set(all_valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP matches Python ({len(python_set)} combos).")
        return 0
    print("MISMATCH between Python and ASP:")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in ASP:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy story world about the youngest child, karma, and problem solving.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--problem", choices=PROBLEMS.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--fix", choices=FIXES.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = []
    for p_id, pr_id, prize_id, f_id in all_valid_combos():
        if args.place and p_id != args.place:
            continue
        if args.problem and pr_id != args.problem:
            continue
        if args.prize and prize_id != args.prize:
            continue
        if args.fix and f_id != args.fix:
            continue
        combos.append((p_id, pr_id, prize_id, f_id))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    p_id, pr_id, prize_id, f_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=p_id,
        problem=pr_id,
        prize=prize_id,
        fix=f_id,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    build_story(world, params)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} ASP-compatible story triples:")
        for s in stories:
            print(" ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = []
        for p_id, pr_id, prize_id, f_id in all_valid_combos():
            params = StoryParams(
                place=p_id,
                problem=pr_id,
                prize=prize_id,
                fix=f_id,
                name="Mia" if params_name_seed(p_id, pr_id, prize_id, f_id) % 2 == 0 else "Leo",
                gender="girl" if params_name_seed(p_id, pr_id, prize_id, f_id) % 2 == 0 else "boy",
                helper="mother",
                trait="cheerful",
            )
            curated.append(params)
        samples = [generate(p) for p in curated[: min(len(curated), max(args.n, 1))]]
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def params_name_seed(*parts: object) -> int:
    s = "|".join(str(p) for p in parts)
    return sum(ord(c) for c in s)


if __name__ == "__main__":
    main()
