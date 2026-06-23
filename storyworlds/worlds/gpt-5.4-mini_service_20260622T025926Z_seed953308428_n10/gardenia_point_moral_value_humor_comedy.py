#!/usr/bin/env python3
"""
A small comedy storyworld about a windy seaside garden at Gardenia Point.

The seed tale:
- A child visits Gardenia Point.
- A silly mix-up turns into a comic problem.
- A moral choice matters: tell the truth, share, help, or make amends.
- Humor comes from the setting, the mishap, and the characters' reactions.

This script follows the Storyweavers contract:
- stdlib-only
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily in ASP helpers
- provides StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports --verify, --asp, --show-asp, --json, --qa, --trace, --all, --seed,
  and -n
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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


@dataclass
class Place:
    id: str
    name: str
    mood: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    verb: str
    mess: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MoralFix:
    id: str
    label: str
    action: str
    result: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

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

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    problem: str
    fix: str
    seed: Optional[int] = None


PLACES = {
    "lookout": Place("lookout", "Gardenia Point lookout", "bright and windy", affords={"sign", "kite", "bench"}, tags={"gardenia", "point"}),
    "garden": Place("garden", "the garden path at Gardenia Point", "sweet and sunny", affords={"sign", "watering", "bench"}, tags={"gardenia", "point"}),
    "cafe": Place("cafe", "the little cafe at Gardenia Point", "busy and cheerful", affords={"cup", "menu", "bench"}, tags={"gardenia", "point"}),
}

PROBLEMS = {
    "wind_sign": Problem("wind_sign", "windy sign", "paint the sign", "the sign got crooked", "the sign would point the wrong way", tags={"sign", "wind"}),
    "cake_kite": Problem("cake_kite", "kite cake", "carry the cake", "the cake got wobbly", "the frosting would slide off", tags={"kite", "cake"}),
    "spilled_juice": Problem("juice_spill", "spilled juice", "carry the juice", "the tray got sloshy", "the cups would wobble and laugh at them", tags={"cup", "juice"}),
}

FIXES = {
    "steady": MoralFix("steady", "hold it steady", "hold it with two hands", "everything stayed neat", tags={"help", "honest"}),
    "admit": MoralFix("admit", "admit the mix-up", "tell the truth right away", "the problem got smaller", tags={"truth", "moral"}),
    "share": MoralFix("share", "share the job", "ask for help politely", "the job got easier", tags={"kindness", "help"}),
}

GIRL_NAMES = ["Mina", "Lily", "Ava", "Nora", "Zoe", "Maya"]
BOY_NAMES = ["Theo", "Ben", "Leo", "Finn", "Sam", "Eli"]
TRAITS = ["cheerful", "curious", "silly", "careful", "lively", "polite"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for prob_id, prob in PROBLEMS.items():
            for fix_id, fix in FIXES.items():
                if place_id == "lookout" and prob_id == "wind_sign":
                    combos.append((place_id, prob_id, fix_id))
                if place_id == "garden" and prob_id == "cake_kite":
                    combos.append((place_id, prob_id, fix_id))
                if place_id == "cafe" and prob_id == "spilled_juice":
                    combos.append((place_id, prob_id, fix_id))
    return combos


def _say_truth(world: World, hero: Entity, helper: Entity, fix: MoralFix) -> None:
    hero.memes["honesty"] += 1
    helper.memes["trust"] += 1
    world.say(f'{hero.id} took a breath and {fix.action}. {fix.result.capitalize()}.')


def _comic_beat(world: World, problem: Problem) -> None:
    world.say(
        f"It was the kind of trouble that made even the gulls look interested: "
        f"{problem.mess}."
    )


def _solve(world: World, hero: Entity, helper: Entity, problem: Problem, fix: MoralFix) -> None:
    if problem.id == "wind_sign":
        world.say(
            f"{helper.id} held the sign while {hero.id} reached up, and the letters stopped wobbling."
        )
    elif problem.id == "cake_kite":
        world.say(
            f"{helper.id} laughed, then lifted the cake plate like a tiny parade float."
        )
    else:
        world.say(
            f"{helper.id} steadied the tray while {hero.id} carried it like a sleepy turtle."
        )
    _say_truth(world, hero, helper, fix)
    world.say(
        f"By the end, {hero.id} was smiling at {world.place.name}, and the whole place seemed to nod back."
    )


def tell(place: Place, hero_name: str, hero_gender: str, helper_name: str, helper_gender: str,
         problem: Problem, fix: MoralFix) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    sign = world.add(Entity(id="sign", type="thing", label="the sign", phrase="a wooden sign"))
    hero.meters["flutter"] += 1
    helper.memes["patience"] += 1

    world.say(
        f"At {place.name}, {hero.id} and {helper.id} arrived with the sort of mood that "
        f"could turn into laughter without warning."
    )
    world.say(
        f"{place.name.capitalize()} felt {place.mood}, and the air kept giving everybody a funny haircut."
    )
    world.say(
        f"{hero.id} wanted to {problem.verb}, but the wind kept nudging {sign.label_word if hasattr(sign, 'label_word') else 'it'} around."
    )
    world.para()
    _comic_beat(world, problem)
    hero.meters["trouble"] += 1
    helper.memes["concern"] += 1
    world.say(
        f"{hero.id} pointed at the mess and said, 'That is not a masterpiece. That is a wobbly noodle.'"
    )
    world.say(
        f"{helper.id} snorted a laugh, because even the problem sounded like it had slipped on a banana peel."
    )
    world.para()
    _solve(world, hero, helper, problem, fix)
    world.facts.update(hero=hero, helper=helper, problem=problem, fix=fix, sign=sign, place=place, solved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, problem = f["hero"], f["helper"], f["problem"]
    return [
        f'Write a short comedy story for a young child set at {f["place"].name} that includes the words "gardenia" and "point".',
        f"Tell a funny story where {hero.id} and {helper.id} fix a silly problem at {f['place'].name} by being honest and kind.",
        f"Write a gentle comedy with a moral lesson about telling the truth when a windy little problem causes a mix-up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, problem, fix, place = f["hero"], f["helper"], f["problem"], f["fix"], f["place"]
    return [
        QAItem(
            question=f"Why did {hero.id} need help at {place.name}?",
            answer=(
                f"{hero.id} had a wobbly problem to fix, and the wind kept making it harder. "
                f"{helper.id} helped steady things so the job could be done without more silliness."
            ),
        ),
        QAItem(
            question=f"What good choice did {hero.id} make when the joke of a mess showed up?",
            answer=(
                f"{hero.id} chose to {fix.action}. That honest choice made the problem smaller and kept the story kind."
            ),
        ),
        QAItem(
            question=f"What made the story funny at {place.name}?",
            answer=(
                f"The wind kept acting like a naughty stage manager, and the problem looked almost too silly to be serious. "
                f"That comic bit made the cleanup feel playful instead of mean."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["place"].tags) | set(world.facts["problem"].tags) | set(world.facts["fix"].tags)
    out = []
    if "gardenia" in tags:
        out.append(QAItem(
            question="What is Gardenia Point?",
            answer="Gardenia Point is a place name for a scenic spot where people might walk, look around, or meet up. It sounds like a cheerful place with a nice view."
        ))
    if "point" in tags:
        out.append(QAItem(
            question="What does the word point mean in a place name?",
            answer="In a place name, point often means a piece of land that sticks out a little, like a lookout or corner by water. It helps name a real place people can visit."
        ))
    if "truth" in tags:
        out.append(QAItem(
            question="Why is telling the truth a good choice?",
            answer="Telling the truth helps people understand what really happened. It lets everyone fix the problem together instead of making the mix-up bigger."
        ))
    if "help" in tags:
        out.append(QAItem(
            question="Why is it nice to ask for help politely?",
            answer="Asking for help politely shows respect and makes teamwork easier. A kind request can turn a hard job into a shared job."
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: meters={meters} memes={memes} role={e.role}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="lookout", hero="Mina", hero_gender="girl", helper="Theo", helper_gender="boy", problem="wind_sign", fix="admit"),
    StoryParams(place="garden", hero="Ava", hero_gender="girl", helper="Leo", helper_gender="boy", problem="cake_kite", fix="share"),
    StoryParams(place="cafe", hero="Finn", hero_gender="boy", helper="Nora", helper_gender="girl", problem="spilled_juice", fix="steady"),
]


def explain_rejection(place_id: str, problem_id: str) -> str:
    return f"(No story: {problem_id} does not fit {place_id} in this small comedy world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld at Gardenia Point.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, fix = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if hero_gender == "girl" else "girl"
    hero_pool = GIRL_NAMES if hero_gender == "girl" else BOY_NAMES
    helper_pool = BOY_NAMES if helper_gender == "boy" else GIRL_NAMES
    hero = args.name or rng.choice(hero_pool)
    helper_candidates = [n for n in helper_pool if n != hero]
    helper = args.helper or rng.choice(helper_candidates)
    return StoryParams(place=place, hero=hero, hero_gender=hero_gender, helper=helper, helper_gender=helper_gender, problem=problem, fix=fix)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.problem not in PROBLEMS or params.fix not in FIXES:
        raise StoryError("Invalid params.")
    if (params.place, params.problem, params.fix) not in valid_combos():
        raise StoryError(explain_rejection(params.place, params.problem))
    world = tell(PLACES[params.place], params.hero, params.hero_gender, params.helper, params.helper_gender, PROBLEMS[params.problem], FIXES[params.fix])
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


ASP_RULES = r"""
valid(P, R, F) :- place(P), problem(R), fix(F), compatible(P, R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
    lines.append(asp.fact("compatible", "lookout", "wind_sign"))
    lines.append(asp.fact("compatible", "garden", "cake_kite"))
    lines.append(asp.fact("compatible", "cafe", "spilled_juice"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = py == cl
    if not ok:
        print("MISMATCH between ASP and Python.")
        print("python:", sorted(py))
        print("asp:", sorted(cl))
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, problem=None, fix=None, name=None, helper=None), random.Random(777)))
        _ = sample.to_json()
        _ = sample.story
        _ = sample.prompts
        _ = sample.story_qa
        _ = sample.world_qa
    except Exception as exc:  # pragma: no cover - verification gate
        print(f"SMOKE TEST FAILED: {exc}")
        return 1

    seeds = [1, 7, 42]
    for s in seeds:
        params = resolve_params(argparse.Namespace(place=None, problem=None, fix=None, name=None, helper=None), random.Random(s))
        sample = generate(params)
        if not sample.story.strip():
            print("Empty story produced.")
            return 1

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        args = argparse.Namespace(place=None, problem=None, fix=None, name=None, helper=None)
        samples = []
        for i in range(3):
            p = resolve_params(args, random.Random(777 + i))
            samples.append(generate(p))
        print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
    if not buf.getvalue().strip():
        print("JSON smoke failed.")
        return 1

    if len(valid_combos()) <= 6:
        for p in CURATED:
            _ = generate(p)

    print("OK: ASP parity and smoke tests passed.")
    return 0


def build_sample_list(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        return [generate(p) for p in CURATED]
    seen: set[str] = set()
    for i in range(max(args.n * 50, 50)):
        if len(samples) >= args.n:
            break
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print("  ", row)
        return

    samples = build_sample_list(args)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} at {p.place} ({p.problem} -> {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
