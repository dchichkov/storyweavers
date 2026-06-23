#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/barn_mediocre_wooded_problem_solving_reconciliation_bravery.py
=============================================================================================================================

A standalone storyworld for a small slice-of-life tale around a barn, a wooded
path, everyday problem solving, reconciliation, and a little bravery.

This world is intentionally compact and reliable:
- a few registries with many valid combinations
- a state-driven story engine
- grounded QA sets
- a Python reasonableness gate with an inline ASP twin
- verify mode that checks parity and runs a generation smoke test
"""

from __future__ import annotations

import argparse
import contextlib
import io
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.label or self.type)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    what_goes_wrong: str
    risk: str
    zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    tool: str
    use: str
    fix: str
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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


@dataclass
class StoryParams:
    setting: str
    problem: str
    method: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    adult_name: str
    adult_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "barnyard": Setting(id="barnyard", place="the barn", detail="the big red barn stood at the edge of a wooded field", affords={"stuck_gate", "missing_bucket", "muddy_boot", "fallen_plank"}),
    "wooded_path": Setting(id="wooded_path", place="the wooded path by the barn", detail="the wooded path beside the barn was quiet and full of pine needles", affords={"lost_key", "fallen_plank", "stuck_gate"}),
    "hayloft": Setting(id="hayloft", place="the hayloft", detail="the hayloft smelled warm and dusty above the barn floor", affords={"missing_bucket", "loose_rope", "fallen_plank"}),
}

PROBLEMS = {
    "stuck_gate": Problem(id="stuck_gate", label="stuck gate", what_goes_wrong="the barn gate would not swing open", risk="they could not bring the feed in", zone="gate", tags={"barn", "problem"}),
    "missing_bucket": Problem(id="missing_bucket", label="missing bucket", what_goes_wrong="the water bucket had rolled out of reach", risk="the animals would go thirsty", zone="bucket", tags={"barn", "problem"}),
    "muddy_boot": Problem(id="muddy_boot", label="muddy boot", what_goes_wrong="one boot was packed with wet mud", risk="it kept slipping and slowing the walk", zone="boot", tags={"mud", "problem"}),
    "fallen_plank": Problem(id="fallen_plank", label="fallen plank", what_goes_wrong="a plank had dropped across the path", risk="the path was blocked", zone="path", tags={"wooden", "problem"}),
}

METHODS = {
    "oil_hinge": Method(id="oil_hinge", label="a little oil", tool="oil can", use="soften the hinge", fix="the gate swung open again", power=2, tags={"barn", "gate"}),
    "find_bucket": Method(id="find_bucket", label="the spare bucket", tool="shed shelf", use="fetch a spare bucket", fix="the animals had water again", power=2, tags={"water", "bucket"}),
    "scrape_mud": Method(id="scrape_mud", label="a stick and some patience", tool="short stick", use="scrape the mud from the boot", fix="the boot came loose and fit right", power=1, tags={"mud"}),
    "move_plank": Method(id="move_plank", label="two strong hands", tool="gloves", use="lift the plank aside", fix="the path was clear again", power=2, tags={"wood", "path"}),
}

NAMES = {
    "girl": ["Mina", "Lila", "Ivy", "Sora", "Nora"],
    "boy": ["Eli", "Theo", "Noah", "Milo", "Ben"],
    "adult": ["Mara", "Jon", "Paula", "Hank"],
}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for pid in setting.affords:
            for mid, method in METHODS.items():
                if pid == "stuck_gate" and mid == "oil_hinge":
                    out.append((sid, pid, mid))
                elif pid == "missing_bucket" and mid == "find_bucket":
                    out.append((sid, pid, mid))
                elif pid == "muddy_boot" and mid == "scrape_mud":
                    out.append((sid, pid, mid))
                elif pid == "fallen_plank" and mid == "move_plank":
                    out.append((sid, pid, mid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Storyworld: a barn, a wooded path, a problem, and a small reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--adult-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--adult-gender", choices=["woman", "man", "mother", "father"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.method is None or c[2] == args.method)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, method = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    adult_gender = args.adult_gender or rng.choice(["woman", "man", "mother", "father"])
    hero_name = args.hero_name or rng.choice(NAMES[hero_gender])
    friend_name = args.friend_name or rng.choice([n for n in NAMES[friend_gender] if n != hero_name] or NAMES[friend_gender])
    adult_name = args.adult_name or rng.choice(NAMES["adult"])
    return StoryParams(setting=setting, problem=problem, method=method,
                       hero_name=hero_name, hero_gender=hero_gender,
                       friend_name=friend_name, friend_gender=friend_gender,
                       adult_name=adult_name, adult_gender=adult_gender)


def _can_solve(problem: Problem, method: Method) -> bool:
    pairs = {
        ("stuck_gate", "oil_hinge"),
        ("missing_bucket", "find_bucket"),
        ("muddy_boot", "scrape_mud"),
        ("fallen_plank", "move_plank"),
    }
    return (problem.id, method.id) in pairs


def _build_world(params: StoryParams) -> World:
    setting = SETTINGS.get(params.setting)
    problem = PROBLEMS.get(params.problem)
    method = METHODS.get(params.method)
    if setting is None or problem is None or method is None:
        raise StoryError("Unknown setting, problem, or method.")
    if not _can_solve(problem, method):
        raise StoryError("That method does not solve that problem.")
    w = World(setting=setting)
    hero = w.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero_name, meters={}, memes={"bravery": 0.0, "frustration": 0.0, "warmth": 0.0}, attrs={"name": params.hero_name}))
    friend = w.add(Entity(id="friend", kind="character", type=params.friend_gender, label=params.friend_name, meters={}, memes={"bravery": 0.0, "frustration": 0.0, "warmth": 0.0}, attrs={"name": params.friend_name}))
    adult = w.add(Entity(id="adult", kind="character", type=params.adult_gender, label=params.adult_name, meters={}, memes={"calm": 0.0, "relief": 0.0}, attrs={"name": params.adult_name}))
    site = w.add(Entity(id="site", kind="thing", type="thing", label=problem.label, meters={"blocked": 1.0, "fixed": 0.0}, memes={}, attrs={"zone": problem.zone}))
    tool = w.add(Entity(id="tool", kind="thing", type="thing", label=method.tool, meters={}, memes={}, attrs={"method": method.id}))
    w.facts = {"hero": hero, "friend": friend, "adult": adult, "problem": problem, "method": method, "site": site, "tool": tool, "setting": setting, "solved": False, "reconciled": False}
    return w


def _solve(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    adult = world.facts["adult"]
    problem = world.facts["problem"]
    method = world.facts["method"]
    site = world.facts["site"]
    sig = ("solve", problem.id, method.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    site.meters["blocked"] = 0.0
    site.meters["fixed"] = 1.0
    world.facts["solved"] = True
    hero.memes["bravery"] += 1.0
    friend.memes["frustration"] += 1.0
    adult.memes["relief"] += 1.0


def generate_story_text(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    adult = world.facts["adult"]
    problem = world.facts["problem"]
    method = world.facts["method"]
    setting = world.facts["setting"]
    site = world.facts["site"]

    world.say(f"{hero.label} and {friend.label} were spending a quiet day around {setting.place}. {setting.detail}.")
    world.say(f"They noticed {problem.what_goes_wrong}, and that made the whole afternoon feel a little mediocre.")
    world.para()
    world.say(f"{hero.label} wanted to help, but {friend.label} frowned and said the problem looked too annoying to fix.")
    world.say(f"{hero.label} took a breath, then walked closer and said {hero.pronoun('possessive')} plan out loud: {method.use}.")
    _solve(world)
    world.para()
    world.say(f"Together they tried it, and {method.fix}.")
    world.say(f"{friend.label} looked up, sighed, and said sorry for being grumpy.")
    world.say(f"{hero.label} shrugged, then smiled back. {adult.label_word.capitalize()} nodded from the doorway, glad the two kids had worked it out.")
    world.say(f"By the end, the {site.label} was neat again, and the barn and wooded path felt calm and ordinary.")

    world.facts["reconciled"] = True
    hero.memes["warmth"] += 1.0
    friend.memes["warmth"] += 1.0


def tell(setting: Setting, problem: Problem, method: Method, hero_name: str, hero_gender: str,
         friend_name: str, friend_gender: str, adult_name: str, adult_gender: str) -> World:
    params = StoryParams(setting=setting.id, problem=problem.id, method=method.id,
                         hero_name=hero_name, hero_gender=hero_gender,
                         friend_name=friend_name, friend_gender=friend_gender,
                         adult_name=adult_name, adult_gender=adult_gender)
    world = _build_world(params)
    generate_story_text(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    problem = f["problem"]
    method = f["method"]
    setting = f["setting"]
    return [
        f"Write a gentle slice-of-life story about {hero.label} and {friend.label} around {setting.place}, where a small problem gets solved by {method.use}.",
        f"Tell a child-friendly story that includes the words barn and wooded, with {problem.label} as the obstacle and a calm ending.",
        f"Write a short story where {hero.label} is brave, {friend.label} is grumpy at first, and they fix {problem.label} together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    adult = f["adult"]
    problem = f["problem"]
    method = f["method"]
    setting = f["setting"]
    site = f["site"]
    return [
        QAItem(
            question=f"What were {hero.label} and {friend.label} trying to do near the barn?",
            answer=f"They were trying to spend a normal day around {setting.place} and deal with {problem.label}. The problem made the day feel annoying, but it was still just an ordinary slice-of-life moment.",
        ),
        QAItem(
            question=f"How did {hero.label} help solve the {problem.label}?",
            answer=f"{hero.label} stayed brave and used {method.use}. That worked because {method.fix}, so the kids could keep going without fuss.",
        ),
        QAItem(
            question=f"Why did {friend.label} apologize at the end?",
            answer=f"{friend.label} had been grumpy at first and doubted the plan. After the problem was fixed, {friend.label} felt better and said sorry, which helped the two friends feel close again.",
        ),
        QAItem(
            question=f"What did {adult.label_word} think when the work was finished?",
            answer=f"{adult.label_word.capitalize()} was relieved and pleased. {adult.label_word.capitalize()} could see that the children solved the problem together instead of turning the day into a bigger mess.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The {site.label} was fixed and calm again. The children were no longer stuck on the problem, and the barn and wooded path felt peaceful once more.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a barn?", "A barn is a big building on a farm where people keep animals, feed, and tools."),
        QAItem("What does wooded mean?", "Wooded means there are lots of trees growing in the area."),
        QAItem("What is a mediocre day?", "A mediocre day is just an ordinary day that is neither very bad nor especially exciting."),
        QAItem("What does problem solving mean?", "Problem solving means figuring out a way to fix something that is not working right."),
        QAItem("What does reconciliation mean?", "Reconciliation means making up after a disagreement so everyone feels friendly again."),
        QAItem("What does bravery mean?", "Bravery means doing something hard or a little scary even when you feel nervous."),
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
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} label={e.label} meters={e.meters} memes={e.memes} attrs={e.attrs}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="barnyard", problem="stuck_gate", method="oil_hinge", hero_name="Mina", hero_gender="girl", friend_name="Eli", friend_gender="boy", adult_name="Mara", adult_gender="mother"),
    StoryParams(setting="wooded_path", problem="fallen_plank", method="move_plank", hero_name="Noah", hero_gender="boy", friend_name="Lila", friend_gender="girl", adult_name="Jon", adult_gender="father"),
    StoryParams(setting="hayloft", problem="missing_bucket", method="find_bucket", hero_name="Ivy", hero_gender="girl", friend_name="Theo", friend_gender="boy", adult_name="Paula", adult_gender="woman"),
    StoryParams(setting="barnyard", problem="muddy_boot", method="scrape_mud", hero_name="Ben", hero_gender="boy", friend_name="Nora", friend_gender="girl", adult_name="Hank", adult_gender="man"),
]


def explain_rejection(setting: Setting, problem: Problem, method: Method) -> str:
    return f"(No story: {method.label} does not solve {problem.label} in {setting.place}.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for pid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, pid))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
    for mid, meth in METHODS.items():
        lines.append(asp.fact("method", mid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,M) :- affords(S,P), solve_pair(P,M).
solve_pair(stuck_gate, oil_hinge).
solve_pair(missing_bucket, find_bucket).
solve_pair(muddy_boot, scrape_mud).
solve_pair(fallen_plank, move_plank).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = 0
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        ok = 1
        print("MISMATCH between clingo and valid_combos():")
        print("  only in clingo:", sorted(cl - py))
        print("  only in python:", sorted(py - cl))
    # Smoke test ordinary generation/emit.
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, method=None, hero_name=None, friend_name=None, adult_name=None, hero_gender=None, friend_gender=None, adult_gender=None), random.Random(777)))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: smoke test generation and emit succeeded.")
    return ok


def build_sample(params: StoryParams) -> StorySample:
    world = _build_world(params)
    generate_story_text(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    if any(v is None for v in (params.setting, params.problem, params.method)):
        raise StoryError("Missing StoryParams fields.")
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.method not in METHODS:
        raise StoryError("Unknown setting, problem, or method.")
    if not _can_solve(PROBLEMS[params.problem], METHODS[params.method]):
        raise StoryError(explain_rejection(SETTINGS[params.setting], PROBLEMS[params.problem], METHODS[params.method]))
    return build_sample(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def _can_solve(problem: Problem, method: Method) -> bool:
    return (
        (problem.id == "stuck_gate" and method.id == "oil_hinge")
        or (problem.id == "missing_bucket" and method.id == "find_bucket")
        or (problem.id == "muddy_boot" and method.id == "scrape_mud")
        or (problem.id == "fallen_plank" and method.id == "move_plank")
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (setting, problem, method) combos:")
        for row in asp_valid_combos():
            print(" ", row)
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
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.problem} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
