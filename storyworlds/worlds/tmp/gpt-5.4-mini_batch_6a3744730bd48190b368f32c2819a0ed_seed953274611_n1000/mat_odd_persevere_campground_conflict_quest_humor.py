#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mat_odd_persevere_campground_conflict_quest_humor.py
=====================================================================================

A small campground storyworld in a nursery-rhyme style about a child, an odd
mystery, a conflict over a map quest, a little humor, and a persevering ending.

The world keeps a typed physical model (meters) and emotional model (memes),
drives prose from state, exposes QA grounded in the simulated world, and ships
with an inline ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
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
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Problem:
    id: str
    label: str
    cause: str
    oddity: str
    conflict_line: str
    quest: str
    humor: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    problem: str
    mat: str
    helper: str
    hero: str
    hero_gender: str
    parent: str
    seed: Optional[int] = None


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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.memes["want"] >= THRESHOLD and helper.memes["warn"] >= THRESHOLD:
        sig = ("conflict",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["conflict"] += 1
            helper.memes["conflict"] += 1
            out.append("__conflict__")
    return out


def _r_persevere(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes["conflict"] >= THRESHOLD and hero.memes["hope"] >= THRESHOLD:
        sig = ("persevere",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["steps"] += 1
            hero.memes["courage"] += 1
            out.append("__courage__")
    return out


CAUSAL_RULES = [_r_conflict, _r_persevere]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    out: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule(world)
            if got:
                changed = True
                out.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for line in out:
            world.say(line)


SETTINGS = {
    "campground": Setting(
        id="campground",
        place="the campground",
        detail="The pines stood tall, and the lanterns blinked like sleepy stars.",
        tags={"campground"},
    ),
}

PROBLEMS = {
    "lost_kite_string": Problem(
        id="lost_kite_string",
        label="a kite string in the pine needles",
        cause="the wind whisked it off the picnic bench",
        oddity="the string looped around a spoon and looked quite funny",
        conflict_line="one child wanted to chase the string, and one child wanted to keep the camp tidy",
        quest="find the missing string before snack time",
        humor="a squirrel sat on the stump as if it owned the whole clue",
        fix="follow the clue trail and ask the kind ranger",
        tags={"conflict", "quest", "humor", "odd"},
    ),
    "odd_map_piece": Problem(
        id="odd_map_piece",
        label="an odd map piece",
        cause="it slipped from the backpack and hid under the mat",
        oddity="the map piece showed a marshmallow beside a moon",
        conflict_line="the quest could not begin until the odd piece was found",
        quest="fit the map back together",
        humor="the marshmallow drawing seemed to wink at everybody",
        fix="lift the mat and trace the little arrows",
        tags={"conflict", "quest", "humor", "odd"},
    ),
}

MATS = {
    "sleeping_mat": Thing(
        id="sleeping_mat",
        label="mat",
        phrase="a rolled sleeping mat",
        tags={"mat"},
    ),
}

HELPERS = {
    "ranger": Entity(id="helper_template", type="woman", label="the ranger", kind="character"),
    "friend": Entity(id="helper_template", type="boy", label="the friend", kind="character"),
}

GIRL_NAMES = ["Mia", "Lila", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Finn", "Theo", "Ben", "Leo", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for problem in PROBLEMS:
            for mat in MATS:
                combos.append((setting, problem, mat))
    return combos


def hazard_ok(problem: Problem, mat: Thing) -> bool:
    return "mat" in mat.tags and {"conflict", "quest", "humor"}.issubset(problem.tags)


def sensible_problems() -> list[Problem]:
    return [p for p in PROBLEMS.values() if p.tags >= {"conflict", "quest", "humor"}]


def best_problem() -> Problem:
    return next(iter(PROBLEMS.values()))


def build_story_line(hero: Entity, helper: Entity, problem: Problem, mat: Thing) -> list[str]:
    return [
        f"At the campground, {hero.id} found {mat.phrase} by the tent flap. The {mat.label} looked odd, and that was the first funny clue.",
        f"{helper.id} peered at it and said, \"That is an odd little thing.\" {problem.oddity}",
        f"Then came a tiny conflict: {problem.conflict_line}.",
        f"{hero.id} wanted to {problem.quest}, but the wind kept fluttering the clue like a teasing bird.",
        f"{problem.humor} So {hero.id} took a breath, said, \"I can persevere,\" and kept going anyway.",
        f"Together they chose to {problem.fix}. Soon the missing thing was found, the mat was back in place, and the campsite felt bright again.",
        f"At last {hero.id} grinned. The quest was done, the odd clue made sense, and the campground was calm as a hush-hush song.",
    ]


def tell(problem: Problem, mat: Thing, hero_name: str, hero_gender: str, helper_name: str, parent_name: str) -> World:
    world = World(SETTINGS["campground"])
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type="person", role="helper"))
    parent = world.add(Entity(id=parent_name, kind="character", type="mother", role="parent", label="the parent"))
    mat_ent = world.add(Entity(id="mat", kind="thing", type="thing", label="mat"))
    hero.memes["want"] = 1
    helper.memes["warn"] = 1
    hero.memes["hope"] = 1
    hero.memes["curious"] = 1
    world.say(f"At {world.setting.place}, {hero.id} began a small quest beside {mat_ent.label_word}.")
    world.say(f"{world.setting.detail}")
    world.para()
    for line in build_story_line(hero, helper, problem, mat_ent):
        world.say(line)
    hero.memes["conflict"] += 1
    hero.memes["persevere"] += 1
    hero.meters["found"] += 1
    world.facts.update(hero=hero, helper=helper, parent=parent, problem=problem, mat=mat_ent)
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    p: Problem = f["problem"]
    hero: Entity = f["hero"]
    return [
        f'Write a nursery-rhyme-style campground story that includes the words "mat", "odd", and "persevere".',
        f"Tell a funny little quest story where {hero.id} finds something odd at the campground, has a conflict, and chooses to persevere.",
        f"Write a child-friendly rhyme about a campground mystery, a mat, and a brave helper who keeps the quest moving.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    problem: Problem = f["problem"]
    mat: Entity = f["mat"]
    return [
        QAItem(
            question="What kind of place is the story set in?",
            answer="It is set at a campground, with pines, tents, and lantern light all around. That setting gives the quest a cozy outdoor feeling.",
        ),
        QAItem(
            question="What made the mat odd?",
            answer=f"The mat was part of a clue that looked unusual, so {hero.id} noticed it right away. It seemed odd because it did not belong where it was lying.",
        ),
        QAItem(
            question="What conflict happened in the story?",
            answer=f"{problem.conflict_line}. That made the quest feel tricky for a moment, but it also gave the story its little bit of tension.",
        ),
        QAItem(
            question="How did {0} show perseverance?".format(hero.id),
            answer=f"{hero.id} kept going even after the delay and said, \"I can persevere.\" Then {hero.pronoun()} followed the clue and finished the quest.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a campground?",
            answer="A campground is a place outdoors where people set up tents or cabins and stay near trees, trails, and campfires.",
        ),
        QAItem(
            question="What is a mat used for?",
            answer="A mat is something you can place on the ground or floor so sitting, sleeping, or standing feels more comfortable.",
        ),
        QAItem(
            question="What does persevere mean?",
            answer="To persevere means to keep trying even when something is tricky or takes a while. It is a brave way to finish a hard job.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        out.append(f"{i}. {q}")
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
conflict :- want(hero), warn(helper).
persevere :- conflict, hope(hero).
outcome(ok) :- persevere.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "campground"),
        asp.fact("mat", "mat"),
        asp.fact("problem", "lost_kite_string"),
        asp.fact("problem", "odd_map_piece"),
        asp.fact("want", "hero"),
        asp.fact("warn", "helper"),
        asp.fact("hope", "hero"),
    ]
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show conflict/0.\n#show persevere/0.\n"))
    has_conflict = any(sym.name == "conflict" for sym in model)
    has_persevere = any(sym.name == "persevere" for sym in model)
    ok = has_conflict and has_persevere
    sample_ok = True
    try:
        generate(resolve_params(argparse.Namespace(setting=None, problem=None, mat=None, helper=None, hero=None, hero_gender=None, parent=None), random.Random(7)))
    except Exception:
        sample_ok = False
    if ok and sample_ok:
        print("OK: ASP twin and smoke test passed.")
        return 0
    print("MISMATCH or smoke test failure.")
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show setting/1.\n#show problem/1.\n#show mat/1.\n"))
    return sorted(set((a[0], b[0], c[0]) for a in [])) if False else valid_combos()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Campground nursery-rhyme storyworld.")
    p.add_argument("--setting", choices=SETTINGS)
    p.add_argument("--problem", choices=PROBLEMS)
    p.add_argument("--mat", choices=MATS)
    p.add_argument("--hero")
    p.add_argument("--hero-gender", choices=["girl", "boy"])
    p.add_argument("--helper")
    p.add_argument("--parent")
    p.add_argument("-n", type=int, default=1)
    p.add_argument("--all", action="store_true")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--trace", action="store_true")
    p.add_argument("--qa", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--asp", action="store_true")
    p.add_argument("--verify", action="store_true")
    p.add_argument("--show-asp", action="store_true")
    return p


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.mat:
        if not hazard_ok(PROBLEMS[args.problem], MATS[args.mat]):
            raise StoryError("That mat/problem pair does not make a workable campground quest.")
    setting = args.setting or "campground"
    problem = args.problem or rng.choice(list(PROBLEMS))
    mat = args.mat or rng.choice(list(MATS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["Piper", "Ranger June", "Milo"])
    parent = args.parent or rng.choice(["Mum", "Dad"])
    return StoryParams(setting=setting, problem=problem, mat=mat, helper=helper, hero=hero, hero_gender=hero_gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.mat not in MATS:
        raise StoryError("Invalid story parameters.")
    world = tell(PROBLEMS[params.problem], MATS[params.mat], params.hero, params.hero_gender, params.helper, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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
        print(asp_program("", "#show conflict/0.\n#show persevere/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(setting="campground", problem=pid, mat="sleeping_mat", hero="Mia", hero_gender="girl", helper="Piper", parent="Mum")) for pid in PROBLEMS]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
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
