#!/usr/bin/env python3
"""
storyworlds/worlds/spoon_ful_problem_solving_transformation_pirate_tale.py
============================================================================

A standalone story world for a small pirate-tale domain built from the seed
word "spoon-ful", with a gentle Problem Solving / Transformation arc.

Premise:
- A child pirate on a little ship faces a practical problem at sea.
- A useful spoonful of tar, soup, or paint is not magical, but it helps in a
  concrete way.
- The fix changes the ship, the object, and the hero's feelings by the end.

Story shape:
- Beginning: introduce the pirate crew, the ship, and the fragile problem.
- Middle: the problem gets in the way of the voyage; worry rises.
- Turn: the crew notices that a spoonful can solve the issue in a small,
  careful way.
- Resolution: the object is transformed, the ship is ready, and the ending
  image proves the change.

The world is intentionally small, state-driven, and child-facing.
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
# Core world model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"               # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"broken": 0.0, "sticky": 0.0, "safe": 0.0, "full": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "hope": 0.0, "pride": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    issue: str
    risk: str
    zone: set[str]
    keyword: str = "spoon-ful"
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    action: str
    result: str
    guards: set[str]
    covers: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "deck": Setting(place="the deck", indoor=False, affords={"mend_sail", "patch_hull"}),
    "cabin": Setting(place="the cabin", indoor=True, affords={"mix_tar", "stir_soup"}),
    "dock": Setting(place="the dock", indoor=False, affords={"mend_sail", "paint_flag"}),
}

PROBLEMS = {
    "torn_sail": Problem(
        id="torn_sail",
        verb="mend the sail",
        gerund="mending the sail",
        issue="a torn sail flapped hard in the wind",
        risk="the ship could not catch the breeze",
        zone={"sail"},
        keyword="spoon-ful",
        tags={"sail", "wind", "cloth"},
    ),
    "stuck_rope": Problem(
        id="stuck_rope",
        verb="free the rope",
        gerund="freeing the rope",
        issue="a sticky rope had knotted itself on the cleat",
        risk="the ship could not turn neatly",
        zone={"rope"},
        keyword="spoon-ful",
        tags={"rope", "sticky", "deck"},
    ),
    "dull_lantern": Problem(
        id="dull_lantern",
        verb="brighten the lantern",
        gerund="brightening the lantern",
        issue="the lantern glass was dull and smoky",
        risk="the crew could not see the rocks ahead",
        zone={"lantern"},
        keyword="spoon-ful",
        tags={"lantern", "light", "smoke"},
    ),
}

FIXES = {
    "tar_spoonful": Fix(
        id="tar_spoonful",
        label="a spoonful of warm tar",
        phrase="a spoonful of warm tar",
        action="spread",
        result="sealed the tear",
        guards={"cloth", "sticky"},
        covers={"sail", "rope"},
    ),
    "soap_spoonful": Fix(
        id="soap_spoonful",
        label="a spoonful of soapy water",
        phrase="a spoonful of soapy water",
        action="wipe",
        result="cleared the grime",
        guards={"smoke"},
        covers={"lantern"},
    ),
    "honey_spoonful": Fix(
        id="honey_spoonful",
        label="a spoonful of honey",
        phrase="a spoonful of honey",
        action="smooth",
        result="made the knot easier to untangle",
        guards={"sticky"},
        covers={"rope"},
    ),
}

HERO_NAMES = ["Pip", "Mara", "Jory", "Nell", "Toby", "Sana"]
PARTNER_NAMES = ["Captain Reed", "Old Finn", "Aunt Brine", "Mate Blue"]
TRAITS = ["brave", "curious", "spry", "cheerful", "clever"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    problem: str
    fix: str
    name: str
    partner: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def prize_at_risk(problem: Problem, fix: Fix) -> bool:
    return bool(problem.zone & fix.covers)


def select_fix(problem: Problem) -> Optional[Fix]:
    for fix in FIXES.values():
        if prize_at_risk(problem, fix):
            return fix
    return None


def reasonableness_check(place: str, problem: str, fix: str) -> bool:
    return problem in SETTINGS[place].affords and prize_at_risk(PROBLEMS[problem], FIXES[fix])


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "character":
            bits.append("character")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(P, F) :- problem_zone(P, R), fix_covers(F, R).
valid_story(Place, Problem, Fix) :- affords(Place, Problem), prize_at_risk(Problem, Fix).
"""


def asp_facts() -> str:
    import asp
    out: list[str] = []
    for sid, s in SETTINGS.items():
        out.append(asp.fact("setting", sid))
        if s.indoor:
            out.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            out.append(asp.fact("affords", sid, a))
    for pid, p in PROBLEMS.items():
        out.append(asp.fact("problem", pid))
        for r in sorted(p.zone):
            out.append(asp.fact("problem_zone", pid, r))
    for fid, f in FIXES.items():
        out.append(asp.fact("fix", fid))
        for r in sorted(f.covers):
            out.append(asp.fact("fix_covers", fid, r))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_stories())
    py_set = set(
        (place, problem, fix)
        for place in SETTINGS
        for problem in SETTINGS[place].affords
        for fix in FIXES
        if reasonableness_check(place, problem, fix)
    )
    if clingo_set == py_set:
        print(f"OK: clingo gate matches python gate ({len(py_set)} stories).")
        return 0
    print("MISMATCH:")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def _do_problem(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["worry"] += 1
    hero.meters["trouble"] += 1
    if problem.id == "torn_sail":
        world.say(f"{hero.id} saw {problem.issue}, and {problem.risk}.")
    elif problem.id == "stuck_rope":
        world.say(f"{hero.id} saw {problem.issue}, and {problem.risk}.")
    else:
        world.say(f"{hero.id} saw {problem.issue}, and {problem.risk}.")


def _apply_fix(world: World, hero: Entity, partner: Entity, problem: Problem, fix: Fix) -> None:
    hero.memes["hope"] += 1
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    if problem.id == "torn_sail":
        world.say(
            f"{partner.id} showed {hero.id} how to use {fix.phrase}. "
            f"{hero.id} spread it along the rip, and it {fix.result}."
        )
        world.say(
            f"The sail grew firm again, and the ship leaned into the wind like a happy gull."
        )
    elif problem.id == "stuck_rope":
        world.say(
            f"{partner.id} pointed to {fix.phrase}. {hero.id} used it to loosen the knot, "
            f"and the rope slid free."
        )
        world.say("The deck felt open again, and the ship could turn cleanly.")
    else:
        world.say(
            f"{partner.id} said a tiny spoonful could still help. {hero.id} wiped the glass, "
            f"and the lantern shone through the smoke."
        )
        world.say("A bright little circle of light danced across the water.")


def tell(setting: Setting, problem: Problem, fix: Fix, hero_name: str, partner_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", label=hero_name))
    partner = world.add(Entity(id=partner_name, kind="character", type="captain", label=partner_name))
    ship = world.add(Entity(id="ship", type="ship", label="ship"))
    problem_ent = world.add(Entity(id=problem.id, type=problem.id, label=problem.id))
    fix_ent = world.add(Entity(id=fix.id, type="thing", label=fix.label, phrase=fix.phrase))

    world.facts.update(hero=hero, partner=partner, ship=ship, problem=problem_ent, fix=fix_ent,
                       setting=setting, problem_cfg=problem, fix_cfg=fix, trait=trait)

    world.say(f"{hero.id} was a little {trait} pirate who loved the {setting.place}.")
    world.say(f"{hero.id} also loved the phrase spoon-ful, because it sounded small and useful.")
    world.say(f"One day, the crew found {problem.issue}.")

    world.para()
    _do_problem(world, hero, problem)
    world.say(f"{hero.id} wondered if a spoon-ful could help.")

    world.para()
    _apply_fix(world, hero, partner, problem, fix)
    hero.memes["pride"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"In the end, {hero.id} held the little spoon up like a treasure, "
        f"and the ship sailed on with a sound, fixed sail and a brighter crew."
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate tale for a young child that includes the word "spoon-ful" and a clever fix.',
        f"Tell a story where {f['hero'].id} uses {f['fix_cfg'].phrase} to solve {f['problem_cfg'].issue}.",
        f"Write a gentle sea adventure about a small problem, a spoon-ful, and a happy transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    problem = f["problem_cfg"]
    fix = f["fix_cfg"]
    return [
        QAItem(
            question=f"What problem did {hero.id} face on the ship?",
            answer=f"{hero.id} faced {problem.issue}, which made the ship's trip harder.",
        ),
        QAItem(
            question=f"What did {hero.id} use to solve the problem?",
            answer=f"{hero.id} used {fix.phrase} with help from {partner.id}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The problem was fixed, the ship was ready again, and the crew felt proud and happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a spoonful?",
            answer="A spoonful is the amount that fits in one spoon.",
        ),
        QAItem(
            question="Why do sailors fix a torn sail?",
            answer="They fix a torn sail so the wind can fill it and help the ship move well.",
        ),
        QAItem(
            question="What does it mean to transform something?",
            answer="To transform something means to change it into a different state or make it work in a new way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with spoon-ful problem solving and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--partner", choices=PARTNER_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place and args.problem and args.fix:
        if not reasonableness_check(args.place, args.problem, args.fix):
            raise StoryError("No story: the chosen place/problem/fix do not fit together.")
    places = [p for p in SETTINGS if args.place in (None, p)]
    combos = []
    for place in places:
        for problem in SETTINGS[place].affords:
            if args.problem and problem != args.problem:
                continue
            for fix in FIXES:
                if args.fix and fix != args.fix:
                    continue
                if reasonableness_check(place, problem, fix):
                    combos.append((place, problem, fix))
    if not combos:
        raise StoryError("No valid pirate story matches the requested options.")
    place, problem, fix = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        problem=problem,
        fix=fix,
        name=args.name or rng.choice(HERO_NAMES),
        partner=args.partner or rng.choice(PARTNER_NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        PROBLEMS[params.problem],
        FIXES[params.fix],
        params.name,
        params.partner,
        params.trait,
    )
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for place, problem, fix in stories:
            print(f"  {place:6} {problem:12} {fix:12}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("deck", "torn_sail", "tar_spoonful", "Pip", "Captain Reed", "curious"),
            StoryParams("dock", "dull_lantern", "soap_spoonful", "Mara", "Old Finn", "brave"),
            StoryParams("deck", "stuck_rope", "honey_spoonful", "Jory", "Aunt Brine", "cheerful"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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


if __name__ == "__main__":
    main()
