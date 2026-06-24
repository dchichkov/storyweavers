#!/usr/bin/env python3
"""
virtual_conflict_mystery.py
===========================

A small storyworld about a virtual place where a child follows clues, faces a
gentle conflict, and solves a mystery by noticing what changed.

Seed idea:
- A child enters a virtual space.
- Something important seems lost, hidden, or scrambled.
- Another character disagrees or blocks the search.
- The child gathers clues, learns the truth, and resolves the conflict.

The world is deliberately small and state-driven: the prose is assembled from
the simulated model rather than from a frozen template.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    place: str = ""
    mood: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title(self) -> str:
        if self.label:
            return self.label
        return self.type


@dataclass
class Setting:
    place: str = "the virtual gallery"
    theme: str = "mystery"
    affordances: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    kind: str
    label: str
    phrase: str
    detail: str
    reveals: str


@dataclass
class Problem:
    id: str
    label: str
    hidden_clue: str
    blocked_by: str
    tension: str


@dataclass
class Fix:
    id: str
    label: str
    verb: str
    result: str
    helps: str


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

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "gallery": Setting(place="the virtual gallery", affordances={"scan", "search", "listen"}),
    "library": Setting(place="the virtual library", affordances={"scan", "search", "read"}),
    "garden": Setting(place="the virtual garden", affordances={"scan", "search", "follow"}),
}

HEROES = {
    "girl": ["Mia", "Nora", "Lily", "Ava", "Zoe"],
    "boy": ["Leo", "Finn", "Max", "Ben", "Theo"],
}

HELPERS = {
    "girl": ["Ada", "Iris", "June"],
    "boy": ["Owen", "Ezra", "Noah"],
}

CLUES = {
    "glow": Clue(
        id="glow",
        kind="light",
        label="a tiny glow",
        phrase="a tiny glow near the corner",
        detail="the glow came from a hidden button",
        reveals="a secret panel",
    ),
    "echo": Clue(
        id="echo",
        kind="sound",
        label="a soft echo",
        phrase="a soft echo behind the shelf",
        detail="the echo repeated when someone tapped the wall",
        reveals="a hidden door",
    ),
    "pixel": Clue(
        id="pixel",
        kind="pattern",
        label="a broken pixel trail",
        phrase="a broken pixel trail across the floor",
        detail="the trail pointed to a missing tile",
        reveals="the missing tile",
    ),
    "note": Clue(
        id="note",
        kind="message",
        label="a short note",
        phrase="a short note tucked under a screen",
        detail="the note gave one careful hint",
        reveals="the next clue",
    ),
}

PROBLEMS = {
    "lost_key": Problem(
        id="lost_key",
        label="the missing key",
        hidden_clue="echo",
        blocked_by="helper",
        tension="they could not open the last door",
    ),
    "scrambled_map": Problem(
        id="scrambled_map",
        label="the scrambled map",
        hidden_clue="pixel",
        blocked_by="helper",
        tension="the path kept changing shape",
    ),
    "quiet_note": Problem(
        id="quiet_note",
        label="the quiet note",
        hidden_clue="glow",
        blocked_by="helper",
        tension="the message was easy to miss",
    ),
}

FIXES = {
    "share": Fix(
        id="share",
        label="share the clue",
        verb="show the clue together",
        result="the search made sense again",
        helps="both children could see the same hint",
    ),
    "listen": Fix(
        id="listen",
        label="listen closely",
        verb="listen for the faint sound",
        result="the hidden place became clear",
        helps="the echo pointed the way",
    ),
    "scan": Fix(
        id="scan",
        label="scan carefully",
        verb="scan the room one more time",
        result="the missing piece stood out at last",
        helps="the smallest detail could not hide anymore",
    ),
}

TRAITS = ["curious", "quiet", "brave", "thoughtful", "patient", "careful"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    problem: str
    clue: str
    fix: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for problem_id, problem in PROBLEMS.items():
            if problem.hidden_clue not in CLUES:
                continue
            for clue_id in CLUES:
                if clue_id != problem.hidden_clue:
                    continue
                for fix_id in FIXES:
                    combos.append((setting_id, problem_id, clue_id, fix_id))
    return combos


def explain_rejection(problem: Problem, clue: Clue) -> str:
    return (
        f"(No story: {problem.label} needs the clue {clue.label}, so this combination "
        f"would not make a clear mystery.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A virtual mystery storyworld with a gentle conflict and a clue-based turn."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if args.problem and args.clue:
        problem = PROBLEMS[args.problem]
        clue = CLUES[args.clue]
        if problem.hidden_clue != clue.id:
            raise StoryError(explain_rejection(problem, clue))

    settings = [args.setting] if args.setting else list(SETTINGS)
    problems = [args.problem] if args.problem else list(PROBLEMS)
    clues = [args.clue] if args.clue else list(CLUES)
    fixes = [args.fix] if args.fix else list(FIXES)

    combos = [
        c for c in valid_combos()
        if c[0] in settings and c[1] in problems and c[2] in clues and c[3] in fixes
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, problem_id, clue_id, fix_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HEROES[gender])
    helper = args.helper or rng.choice(HELPERS[gender])
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        setting=setting_id,
        problem=problem_id,
        clue=clue_id,
        fix=fix_id,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity, helper: Entity, problem: Problem, clue: Clue) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait', hero.type)} {hero.type} who loved exploring "
        f"{world.setting.place}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} and {helper.id} had entered the virtual world because "
        f"something was missing: {problem.label}."
    )
    world.say(
        f"Everyone said the place felt calm, but {problem.tension}."
    )
    world.say(
        f"The first hint was {clue.phrase}."
    )


def look_for_clue(world: World, hero: Entity, helper: Entity, clue: Clue, problem: Problem) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.id} wanted to {world.facts['search_verb']} right away."
    )
    if problem.blocked_by == "helper":
        helper.memes["doubt"] = helper.memes.get("doubt", 0) + 1
        world.say(
            f"But {helper.id} frowned and said they should wait."
        )
        hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
        world.say(
            f"{hero.id} did not like waiting, and the two children started to disagree."
        )
    world.say(
        f"Still, {clue.detail}."
    )


def resolve_mystery(world: World, hero: Entity, helper: Entity, clue: Clue, fix: Fix) -> None:
    hero.memes["resolve"] = hero.memes.get("resolve", 0) + 1
    helper.memes["trust"] = helper.memes.get("trust", 0) + 1
    world.say(
        f"Then {hero.id} decided to {fix.verb}."
    )
    if fix.id == "share":
        world.say(
            f"{helper.id} looked again, and this time the hint was easy to understand."
        )
    elif fix.id == "listen":
        world.say(
            f"Both children went still, and the quiet sound led them forward."
        )
    else:
        world.say(
            f"{hero.id} scanned the room again, and the last piece finally stood out."
        )
    world.say(
        f"That is when they found {clue.reveals}."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["conflict"] = 0
    helper.memes["doubt"] = 0
    world.say(
        f"In the end, {fix.result}, and {hero.id} and {helper.id} smiled at the answer."
    )


def tell(setting: Setting, problem: Problem, clue: Clue, fix: Fix, hero_name: str, gender: str,
         helper_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender))
    helper = world.add(Entity(id=helper_name, kind="character", type=gender))
    hero.memes["trait"] = trait
    helper.memes["trait"] = "helpful"

    world.facts["search_verb"] = {
        "gallery": "search the glowing frames",
        "library": "look between the quiet shelves",
        "garden": "follow the winding paths",
    }[setting.place.split()[-2] if setting.place.startswith("the ") else setting.place]

    world.facts.update(
        hero=hero,
        helper=helper,
        problem=problem,
        clue=clue,
        fix=fix,
        setting=setting,
    )

    introduce(world, hero, helper, problem, clue)
    world.para()
    look_for_clue(world, hero, helper, clue, problem)
    world.para()
    resolve_mystery(world, hero, helper, clue, fix)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    problem: Problem = f["problem"]
    clue: Clue = f["clue"]
    return [
        f'Write a short mystery story for a child about {hero.id} in {world.setting.place} '
        f"where {problem.label} causes a small conflict.",
        f"Tell a virtual mystery where {hero.id} and {helper.id} disagree at first, then "
        f"find {clue.label}.",
        f"Write a gentle story with a clue, a misunderstanding, and a happy ending in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    problem: Problem = f["problem"]
    clue: Clue = f["clue"]
    fix: Fix = f["fix"]

    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, who explored {world.setting.place} with {helper.id}.",
        ),
        QAItem(
            question=f"What was the problem in the virtual place?",
            answer=f"The problem was {problem.label}, and it made the search harder.",
        ),
        QAItem(
            question=f"What clue helped them?",
            answer=f"{clue.label} helped them, because it pointed to {clue.reveals}.",
        ),
        QAItem(
            question=f"How did the conflict get calmer?",
            answer=f"They used {fix.label.lower()} and kept looking until the answer became clear.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does virtual mean?",
            answer="Virtual means something is made with a computer and appears on a screen, like a pretend place or game world.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a story or problem where something is not clear at first, and clues help you understand it.",
        ),
        QAItem(
            question="Why do people look for clues?",
            answer="People look for clues because clues help them figure out what happened or where something is hidden.",
        ),
    ]


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(virtual_gallery).
setting(virtual_library).
setting(virtual_garden).

affords(virtual_gallery,scan).
affords(virtual_gallery,search).
affords(virtual_gallery,listen).
affords(virtual_library,scan).
affords(virtual_library,search).
affords(virtual_library,read).
affords(virtual_garden,scan).
affords(virtual_garden,search).
affords(virtual_garden,follow).

problem(lost_key).
problem(scrambled_map).
problem(quiet_note).

clue(glow).
clue(echo).
clue(pixel).
clue(note).

fix(share).
fix(listen).
fix(scan).

hidden_clue(lost_key,echo).
hidden_clue(scrambled_map,pixel).
hidden_clue(quiet_note,glow).

valid(Place,Problem,Clue,Fix) :- setting(Place), problem(Problem), clue(Clue), fix(Fix), hidden_clue(Problem,Clue).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [asp.fact("setting", sid) for sid in SETTINGS]
        + [asp.fact("problem", pid) for pid in PROBLEMS]
        + [asp.fact("clue", cid) for cid in CLUES]
        + [asp.fact("fix", fid) for fid in FIXES]
        + [asp.fact("hidden_clue", pid, p.hidden_clue) for pid, p in PROBLEMS.items()]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Serialization / CLI
# ---------------------------------------------------------------------------

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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        PROBLEMS[params.problem],
        CLUES[params.clue],
        FIXES[params.fix],
        params.name,
        params.gender,
        params.helper,
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


CURATED = [
    StoryParams(setting="gallery", problem="lost_key", clue="echo", fix="listen", name="Mia", gender="girl", helper="Ada", trait="curious"),
    StoryParams(setting="library", problem="quiet_note", clue="glow", fix="scan", name="Leo", gender="boy", helper="Owen", trait="careful"),
    StoryParams(setting="garden", problem="scrambled_map", clue="pixel", fix="share", name="Nora", gender="girl", helper="June", trait="thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.name}: {p.problem} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
