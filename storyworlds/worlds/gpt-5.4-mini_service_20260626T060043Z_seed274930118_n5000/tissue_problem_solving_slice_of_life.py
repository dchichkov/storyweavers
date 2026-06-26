#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tissue_problem_solving_slice_of_life.py
==============================================================================================================

A small slice-of-life storyworld about noticing a problem, choosing a useful
tissue, and making the moment feel better.

Premise:
- A child is doing an ordinary activity at home.
- Something small goes wrong: a sneeze, a drip, a crumbly spill, a sticky hand,
  or a runny nose.
- The child or helper solves it with a tissue and a calm step-by-step fix.

The world is intentionally modest: no grand adventure, just a concrete little
problem and a practical resolution that changes the room from messy to neat.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    trigger: str
    mess: str
    symptom: str
    fix_hint: str
    zone: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    solves: set[str]
    use: str
    result: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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


def _join(parts: list[str]) -> str:
    return ", ".join(parts[:-1]) + " and " + parts[-1] if len(parts) > 1 else parts[0]


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"sneeze", "spill", "sticky"}),
    "bathroom": Setting(place="the bathroom", indoors=True, affords={"sneeze", "drip"}),
    "living_room": Setting(place="the living room", indoors=True, affords={"crumbs", "spill"}),
    "bedroom": Setting(place="the bedroom", indoors=True, affords={"sneeze", "sticky"}),
    "porch": Setting(place="the porch", indoors=False, affords={"dust", "spill"}),
}

PROBLEMS = {
    "sneeze": Problem(
        id="sneeze",
        trigger="sneezed",
        mess="a little dampness",
        symptom="a runny nose",
        fix_hint="wipe the nose and get comfortable again",
        zone="face",
        keyword="tissue",
        tags={"tissue", "nose", "clean"},
    ),
    "spill": Problem(
        id="spill",
        trigger="spilled juice",
        mess="a sticky puddle",
        symptom="sticky fingers",
        fix_hint="blot the spill before it spreads",
        zone="table",
        keyword="tissue",
        tags={"tissue", "juice", "clean"},
    ),
    "sticky": Problem(
        id="sticky",
        trigger="got jam on their hands",
        mess="a sticky smear",
        symptom="sticky hands",
        fix_hint="wipe the hands carefully",
        zone="hands",
        keyword="tissue",
        tags={"tissue", "jam", "clean"},
    ),
    "crumbs": Problem(
        id="crumbs",
        trigger="crumbled a cookie",
        mess="crumbs on the lap",
        symptom="a messy lap",
        fix_hint="brush the crumbs away",
        zone="lap",
        keyword="tissue",
        tags={"tissue", "cookie", "clean"},
    ),
    "drip": Problem(
        id="drip",
        trigger="got a drip on the shirt",
        mess="a wet spot",
        symptom="a damp shirt",
        fix_hint="pat the spot dry",
        zone="torso",
        keyword="tissue",
        tags={"tissue", "dry", "clean"},
    ),
    "dust": Problem(
        id="dust",
        trigger="tracked dust inside",
        mess="dusty footprints",
        symptom="dust on the floor",
        fix_hint="wipe the floor near the door",
        zone="floor",
        keyword="tissue",
        tags={"tissue", "dust", "clean"},
    ),
}

TOOLS = {
    "tissue": Tool(
        id="tissue",
        label="tissue",
        phrase="a soft tissue",
        solves={"sneeze", "spill", "sticky", "crumbs", "drip", "dust"},
        use="reach for the tissue and use it gently",
        result="the small mess was gone",
        plural=False,
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella", "Lucy"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Noah", "Finn", "Max", "Owen"]
TRAITS = ["gentle", "curious", "patient", "cheerful", "quiet", "careful"]


class Reasoner:
    @staticmethod
    def valid_combo(place: str, problem: str, tool: str) -> bool:
        s = SETTINGS[place]
        p = PROBLEMS[problem]
        t = TOOLS[tool]
        return problem in s.affords and problem in t.solves and p.keyword == "tissue"

    @staticmethod
    def explain_rejection(place: str, problem: str, tool: str) -> str:
        p = PROBLEMS[problem]
        t = TOOLS[tool]
        if problem not in SETTINGS[place].affords:
            return f"(No story: {place.replace('_', ' ')} does not naturally create this kind of problem.)"
        if problem not in t.solves:
            return f"(No story: {t.label} would not solve this problem in a believable way.)"
        return f"(No story: this setup does not fit the small tissue-based slice-of-life premise.)"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for problem in PROBLEMS:
            for tool in TOOLS:
                if Reasoner.valid_combo(place, problem, tool):
                    out.append((place, problem, tool))
    return out


def _do_problem(world: World, child: Entity, problem: Problem) -> None:
    child.meters[problem.id] = child.meters.get(problem.id, 0) + 1
    child.memes["concern"] = child.memes.get("concern", 0) + 1
    world.facts["active_problem"] = problem.id


def _use_tissue(world: World, child: Entity, helper: Entity, problem: Problem, tool: Tool) -> None:
    if child.meters.get(problem.id, 0) < THRESHOLD:
        return
    child.meters["mess"] = 0
    child.memes["concern"] = 0
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    helper.memes["care"] = helper.memes.get("care", 0) + 1
    world.fired.add(("solved", problem.id, tool.id))


def tell(setting: Setting, problem: Problem, tool: Tool,
         hero_name: str, hero_gender: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the helper"))
    tissue = world.add(Entity(id=tool.id, type="tissue", label=tool.label, phrase=tool.phrase, plural=tool.plural))
    tissue.held_by = helper.id

    world.facts.update(
        child=child,
        helper=helper,
        tool=tissue,
        problem=problem,
        setting=setting,
        trait=trait,
    )

    world.say(f"{child.id} was a {trait} {hero_gender} who liked ordinary mornings in {setting.place}.")
    world.say(f"One day, {child.id} {problem.trigger}, and {problem.symptom} made the room feel a little off.")
    world.say(f"{child.id} noticed the problem right away. {problem.fix_hint.capitalize()} sounded like the right thing to do.")

    world.para()
    world.say(f"{helper.label} saw what happened and picked up {article(tool.phrase)} {tool.label}.")
    world.say(f'The helper said, "Let\'s {tool.use}."')
    _do_problem(world, child, problem)
    _use_tissue(world, child, helper, problem, tool)
    world.say(f"{child.id} took the tissue and helped clean up. Soon {tool.result}, and the room felt calm again.")
    world.say(f"By the end, {child.id} was smiling, and {setting.place} looked neat and cozy.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    problem: Problem = f["problem"]
    setting: Setting = f["setting"]
    return [
        f'Write a short slice-of-life story for a young child about a small problem in {setting.place} and a tissue that helps.',
        f"Tell a gentle story where {child.id} has a tiny everyday trouble, {helper.label} stays calm, and a tissue makes things better.",
        f'Write a simple story about "{problem.keyword}" that ends with a clean, peaceful room.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    problem: Problem = f["problem"]
    setting: Setting = f["setting"]
    trait: str = f["trait"]
    qa = [
        QAItem(
            question=f"Where did {child.id} notice the problem?",
            answer=f"{child.id} noticed it in {setting.place}, where an ordinary day suddenly needed a little fixing.",
        ),
        QAItem(
            question=f"What problem happened to {child.id}?",
            answer=f"{child.id} {problem.trigger}, which left {problem.mess} and made things a bit messy.",
        ),
        QAItem(
            question=f"Who helped {child.id} solve the problem?",
            answer=f"{helper.label} helped by bringing a tissue and staying calm.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt better and relieved, because the little problem was handled kindly.",
        ),
        QAItem(
            question=f"Why did the tissue matter in this story?",
            answer=f"The tissue mattered because it was the simple tool that helped {child.id} clean up the problem and feel comfortable again.",
        ),
    ]
    if world.facts.get("active_problem") == problem.id:
        qa.append(QAItem(
            question=f"What did the tissue help with after {child.id} {problem.trigger}?",
            answer=f"It helped with {problem.fix_hint}, and that turned a small annoyance into a neat little solution.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tissue for?",
            answer="A tissue is a soft paper sheet people use to wipe noses, clean small spills, or dry little messes.",
        ),
        QAItem(
            question="Why do people keep tissues nearby?",
            answer="People keep tissues nearby because small problems like sneezes or drips can happen anytime, and tissues make it easy to clean up quickly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A problem is valid when the place can naturally produce it and the tool solves it.
valid(Place, Problem, Tool) :- affords(Place, Problem), solves(Tool, Problem), tissue_tool(Tool).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for p in sorted(s.affords):
            lines.append(asp.fact("affords", pid, p))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("trigger", pid, p.trigger))
        lines.append(asp.fact("solved_by_tissue", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tissue_tool", tid))
        for p in sorted(t.solves):
            lines.append(asp.fact("solves", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
    if clingo - py:
        print("  only in clingo:", sorted(clingo - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about tissue-based problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if args.problem and args.tool and not Reasoner.valid_combo(args.place or list(SETTINGS)[0], args.problem, args.tool):
        raise StoryError(Reasoner.explain_rejection(args.place or list(SETTINGS)[0], args.problem, args.tool))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, tool=tool, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PROBLEMS[params.problem], TOOLS[params.tool],
                 params.name, params.gender, params.helper, params.trait)
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
    StoryParams(place="kitchen", problem="spill", tool="tissue", name="Mia", gender="girl", helper="mother", trait="careful"),
    StoryParams(place="bathroom", problem="sneeze", tool="tissue", name="Leo", gender="boy", helper="father", trait="quiet"),
    StoryParams(place="living_room", problem="crumbs", tool="tissue", name="Nora", gender="girl", helper="mother", trait="cheerful"),
    StoryParams(place="bedroom", problem="sticky", tool="tissue", name="Ben", gender="boy", helper="father", trait="patient"),
    StoryParams(place="porch", problem="dust", tool="tissue", name="Ava", gender="girl", helper="mother", trait="gentle"),
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
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print("  ", row)
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
            header = f"### {p.name}: {p.problem} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
