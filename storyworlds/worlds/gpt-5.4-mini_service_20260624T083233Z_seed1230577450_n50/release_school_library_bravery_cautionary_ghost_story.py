#!/usr/bin/env python3
"""
A small storyworld: bravery and caution in a school library ghost story.

This world models a child who wants to help a shy ghost "release" a lost
page back into a library book, but the library has a few rules: keep voices
low, respect fragile things, and do not chase a ghost deeper into the stacks
without a lamp. The tension comes from bravery that is careful rather than
reckless, and the ending shows the page returned, the ghost soothed, and the
library calm again.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    keeper: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the school library"


@dataclass
class Problem:
    id: str
    concern: str
    noise_risk: bool
    search_zone: str
    caution_rule: str
    bravery_rule: str
    ghost_word: str = "ghost"
    keyword: str = "release"


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    guards_noise: bool
    helps_search: bool
    reason: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    problem: str
    fix: str
    seed: Optional[int] = None


SETTING = Setting(place="the school library")

PROBLEMS = {
    "lost_page": Problem(
        id="lost_page",
        concern="a torn page slipped out of a book",
        noise_risk=True,
        search_zone="the tall shelves",
        caution_rule="never shout in the library",
        bravery_rule="be brave enough to look where the page vanished",
        ghost_word="ghost",
        keyword="release",
    ),
    "whisper_ghost": Problem(
        id="whisper_ghost",
        concern="a shy ghost was fluttering between the books",
        noise_risk=True,
        search_zone="the reading nook",
        caution_rule="keep the lights steady and your voice soft",
        bravery_rule="be brave enough to offer help",
        ghost_word="ghost",
        keyword="release",
    ),
    "book_breeze": Problem(
        id="book_breeze",
        concern="a draft kept lifting the pages of a forgotten book",
        noise_risk=False,
        search_zone="the study table",
        caution_rule="hold the pages carefully",
        bravery_rule="be brave enough to tidy the mess",
        ghost_word="ghost",
        keyword="release",
    ),
}

FIXES = {
    "lamp": Fix(
        id="lamp",
        label="a small lamp",
        phrase="a small lamp with a warm yellow glow",
        guards_noise=True,
        helps_search=True,
        reason="its calm light helps the child search without stumbling",
    ),
    "bookmark": Fix(
        id="bookmark",
        label="a ribbon bookmark",
        phrase="a ribbon bookmark with a bright red end",
        guards_noise=True,
        helps_search=False,
        reason="it holds the page in place and keeps the book from closing hard",
    ),
    "gloves": Fix(
        id="gloves",
        label="white cotton gloves",
        phrase="white cotton gloves for careful hands",
        guards_noise=False,
        helps_search=True,
        reason="they help touch fragile paper without creasing it",
    ),
}

NAMES = {
    "girl": ["Maya", "Nora", "Lina", "Ivy", "Ruby"],
    "boy": ["Eli", "Noah", "Theo", "Finn", "Max"],
}

TRAITS = ["brave", "careful", "quiet", "curious", "gentle"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid, p in PROBLEMS.items():
        for fid, f in FIXES.items():
            if p.noise_risk and f.guards_noise:
                out.append((pid, fid))
            elif not p.noise_risk and (f.helps_search or f.guards_noise):
                out.append((pid, fid))
    return out


def explain_rejection(problem: Problem, fix: Fix) -> str:
    return (
        f"(No story: {fix.label} does not fit {problem.concern} in a way that "
        f"matches the library's caution rules.)"
    )


def tell(problem: Problem, fix: Fix, hero_name: str, gender: str, parent: str, trait: str) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, label=hero_name))
    grownup = world.add(Entity(id="Parent", kind="character", type=parent, label=f"the {parent}"))
    problem_ent = world.add(Entity(id=problem.id, type="problem", label=problem.concern))
    fix_ent = world.add(Entity(id=fix.id, type="thing", label=fix.label, phrase=fix.phrase))
    world.facts.update(hero=hero, grownup=grownup, problem=problem, problem_ent=problem_ent, fix=fix, fix_ent=fix_ent)

    hero.memes["bravery"] = 1.0
    hero.memes["caution"] = 1.0

    world.say(f"{hero.name if hasattr(hero,'name') else hero.id} was a {trait} {gender} who loved the school library.")
    world.say(f"{hero_name} had heard that {problem.concern}, and the room felt a little spooky in the soft hush of the shelves.")
    world.say(f"{hero_name} wanted to {problem.keyword} the trouble, but {hero.pronoun().capitalize()} also remembered that {problem.caution_rule}.")
    world.para()

    world.say(f"Near the reading nook, {hero_name} saw {fix.phrase}.")
    if fix.guards_noise:
        world.say(f"{hero_name} lifted {fix_ent.it()} carefully because its warm glow could guide a search without making the ghosts stir.")
    else:
        world.say(f"{hero_name} reached for {fix_ent.it()} with gentle hands so the paper would not crease.")
    world.say(f"That gave {hero_name} the brave idea to look for the missing page without rushing.")
    world.para()

    if problem.noise_risk:
        world.say(f"{hero_name} moved between the tall shelves, slow as a mouse, until the page gave a tiny rustle.")
        world.say(f"A shy ghost peeked out, and it did not seem scary anymore; it seemed lonely.")
        world.say(f"{hero_name} stayed calm and placed the page back in the book, letting the last little flutter {problem.keyword} away.")
    else:
        world.say(f"{hero_name} straightened the pages and tucked the loose corner under the ribbon bookmark.")
        world.say(f"The draft lost interest, and the room settled down like a sleepy cat.")
    world.para()

    hero.memes["bravery"] += 1.0
    hero.memes["caution"] += 1.0
    world.say(f"In the end, the library was quiet again, the book was safe, and {hero_name} felt proud for being brave and careful at the same time.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    return [
        f"Write a gentle ghost story for a young child set in a school library where {hero.id} must show {problem.bravery_rule}.",
        f"Tell a story about {hero.id} in the school library, using the word release, where caution matters and a spooky problem gets solved kindly.",
        f"Write a short school library story with a ghostly feeling, a careful helper, and an ending where {hero.id} safely fixes the trouble.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    fix = f["fix"]
    return [
        QAItem(
            question=f"Where did {hero.id} have the spooky problem?",
            answer=f"{hero.id} had the spooky problem in the school library, among the shelves and reading places.",
        ),
        QAItem(
            question=f"What did {hero.id} need to do with the problem?",
            answer=f"{hero.id} needed to {problem.keyword} the trouble by fixing it carefully and not making the library noisy.",
        ),
        QAItem(
            question=f"What helped {hero.id} stay safe and careful?",
            answer=f"{fix.label} helped because {fix.reason}. That made it easier to solve the problem without breaking the library's rules.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt proud and brave, but also careful, because the book was safe and the ghostly trouble was gone.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a school library?",
            answer="A school library is a quiet room in a school where children can read books, look things up, and borrow stories.",
        ),
        QAItem(
            question="Why should people keep their voices low in a library?",
            answer="People keep their voices low in a library so everyone can read and think without getting distracted.",
        ),
        QAItem(
            question="What does it mean to be cautious?",
            answer="Being cautious means moving carefully and thinking ahead so you do not cause harm or trouble.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel a little scared.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
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


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if p.noise_risk:
            lines.append(asp.fact("noise_risk", pid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        if f.guards_noise:
            lines.append(asp.fact("guards_noise", fid))
        if f.helps_search:
            lines.append(asp.fact("helps_search", fid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,F) :- problem(P), fix(F), noise_risk(P), guards_noise(F).
valid(P,F) :- problem(P), fix(F), not noise_risk(P), (guards_noise(F); helps_search(F)).
#show valid/2.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world set in a school library.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
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
    combos = valid_combos()
    if args.problem and args.fix:
        if (args.problem, args.fix) not in combos:
            raise StoryError(explain_rejection(PROBLEMS[args.problem], FIXES[args.fix]))
    choices = [(p, f) for p, f in combos
               if (not args.problem or p == args.problem)
               and (not args.fix or f == args.fix)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    problem, fix = rng.choice(sorted(choices))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait, problem=problem, fix=fix)


def generate(params: StoryParams) -> StorySample:
    world = tell(PROBLEMS[params.problem], FIXES[params.fix], params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


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
    StoryParams(name="Maya", gender="girl", parent="mother", trait="careful", problem="lost_page", fix="lamp"),
    StoryParams(name="Eli", gender="boy", parent="father", trait="brave", problem="whisper_ghost", fix="bookmark"),
    StoryParams(name="Nora", gender="girl", parent="mother", trait="gentle", problem="book_breeze", fix="gloves"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
