#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/furnish_mulch_glance_suspense_happy_ending_problem.py
======================================================================================

A small mythic story world about a sacred grove, a shaky omen, a practical problem,
and a happy ending: a young hero tries to furnish a shrine for a rite, notices a
bad sign in the mulch, and solves the problem before the ceremony is ruined.

Seed words:
- furnish
- mulch
- glance

Narrative instruments:
- Suspense
- Problem Solving
- Happy Ending

Style:
- Mythic, child-facing, concrete, and state-driven
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "queen", "mother", "priestess"}
        male = {"boy", "man", "king", "father", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Shrine:
    id: str
    label: str
    need: str
    adorn: str
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Problem:
    id: str
    label: str
    risk: str
    fix: str
    power: int
    sense: int

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["risk"] < THRESHOLD:
            continue
        sig = ("tension", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ch in list(world.entities.values()):
            if ch.kind == "character":
                ch.memes["worry"] += 1
        out.append("__tension__")
    return out


CAUSAL_RULES = [Rule("tension", "social", _r_tension)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def risk_at_hand(furnish: str, mulch: str) -> bool:
    return furnish == "shrine" and mulch in {"wet", "loose", "thorny"}


def solve_power(problem: Problem) -> bool:
    return problem.sense >= 2 and problem.power >= 1


def _glance_omen(world: World, shrine: Shrine, mulch: str) -> dict:
    sim = world.copy()
    sim.get("shrine").meters["risk"] += 1
    if mulch == "wet":
        sim.get("shrine").meters["slip"] += 1
    propagate(sim, narrate=False)
    return {"risk": sim.get("shrine").meters["risk"], "worry": sim.get("hero").memes["worry"]}


def open_story(world: World, hero: Entity, guide: Entity, shrine: Shrine) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"In the old grove, {hero.id} and {guide.id} came before the shrine of stone. "
        f"The shrine had been empty all winter, and the rite could not begin until it was furnished."
    )
    world.say(
        f"{hero.id} carried fresh cloth, a small lamp, and a bowl for seed. "
        f"{guide.id} watched the path beneath the trees, where the mulch lay dark after the rain."
    )


def suspense(world: World, hero: Entity, guide: Entity, mulch: str) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} bent close and gave the mulch a quick glance. "
        f"Something about it was wrong: if the ground stayed slick, the sacred bowl could tip."
    )
    world.say(
        f'{guide.id} lowered {guide.pronoun("possessive")} voice. "We must be careful," '
        f'{guide.pronoun()} said. "A fine offering is no good if the path fails beneath it."'
    )


def problem_solving(world: World, hero: Entity, guide: Entity, shrine: Shrine, problem: Problem) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"{hero.id} did not waste a breath. {hero.pronoun().capitalize()} looked again at the mulch, "
        f"then chose a steadier way."
    )
    world.say(
        f"Together they moved stones to the slippery places, raked the mulch back into even rows, "
        f"and set the lamp where the wind could not reach it."
    )
    shrine.meters["risk"] = 0
    shrine.meters["order"] += 1
    world.say(
        f"The problem was solved with patient hands. What had seemed like a bad sign became a safe path."
    )


def happy_ending(world: World, hero: Entity, guide: Entity, shrine: Shrine) -> None:
    hero.memes["joy"] += 1
    guide.memes["joy"] += 1
    world.say(
        f"At last the shrine was furnished in bright order, and the offering could rest without fear."
    )
    world.say(
        f"The old grove grew quiet and kind. The lamp glowed, the mulch lay smooth, and {hero.id} smiled "
        f"as the rite began in peace."
    )


def tell(hero_name: str, guide_name: str, mulch: str, problem_id: str, seed: Optional[int] = None) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", role="hero"))
    guide = world.add(Entity(id=guide_name, kind="character", type="priestess", role="guide"))
    shrine = world.add(Entity(id="shrine", type="thing", label="the shrine"))
    shrine_obj = Shrine("shrine_cfg", "the shrine", need="furnish", adorn="cloth and lamp", fragile=True)
    problem = PROBLEMS[problem_id]

    open_story(world, hero, guide, shrine_obj)
    world.para()
    suspense(world, hero, guide, mulch)
    omen = _glance_omen(world, shrine_obj, mulch)
    world.facts["omen"] = omen
    if risk_at_hand("shrine", mulch):
        shrine.meters["risk"] += 1
        propagate(world, narrate=False)
    world.para()
    problem_solving(world, hero, guide, shrine_obj, problem)
    world.para()
    happy_ending(world, hero, guide, shrine_obj)

    world.facts.update(hero=hero, guide=guide, shrine=shrine_obj, mulch=mulch, problem=problem)
    return world


THEMES = ["myth"]
MULCHES = {
    "wet": "wet mulch",
    "loose": "loose mulch",
    "thorny": "thorny mulch",
}
PROBLEMS = {
    "slippery_path": Problem("slippery_path", "a slippery path", "the bowl might slip", "stone steps", 1, 3),
    "wind_gust": Problem("wind_gust", "a wind gust", "the lamp could wobble", "a windbreak", 1, 2),
    "crowd_jam": Problem("crowd_jam", "a crowd jam", "people might bump the offering", "a clearer lane", 1, 2),
}

NAMES = ["Ari", "Mira", "Koa", "Nia", "Tala", "Leif", "Dara", "Soren"]
GUIDES = ["Iris", "Orin", "Bela", "Aster", "Maren"]


@dataclass
@dataclass
class StoryParams:
    theme: str
    hero: str
    guide: str
    mulch: str
    problem: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme in THEMES:
        for mulch in MULCHES:
            for problem in PROBLEMS:
                if risk_at_hand("shrine", mulch):
                    combos.append((theme, mulch, problem))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic story that includes the words "furnish", "{f["mulch"]}", and "glance".',
        f"Tell a suspenseful myth where {f['hero'].id} must furnish a shrine, notices trouble in the mulch, and solves the problem before the rite begins.",
        "Write a child-friendly myth with a scary moment, a clever fix, and a happy ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, guide, problem = f["hero"], f["guide"], f["problem"]
    qa = [
        ("What did the hero want to do?",
         f"{hero.id} wanted to furnish the shrine so the rite could begin. The shrine needed cloth, light, and a steady place to rest the offering."),
        ("What made the hero worried?",
         f"{hero.id} gave the mulch a glance and saw that it was unsafe. The ground looked slick, so the offering might have slipped."),
        ("How was the problem solved?",
         f"{guide.id} and {hero.id} moved the stones, raked the mulch into safer rows, and set the lamp where the wind could not reach it. That careful work fixed the problem before the rite started."),
        ("How did the story end?",
         f"It ended happily, with the shrine furnished and the rite beginning in peace. The scary sign in the mulch became part of a safe and bright ending."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is mulch?",
         "Mulch is plant matter or bark spread on the ground to help cover soil and keep it neat."),
        ("What does it mean to glance?",
         "To glance means to look quickly for a moment."),
        ("What does it mean to furnish something?",
         "To furnish something means to supply it with what it needs, like cloth, tools, or decorations."),
        ("Why can a slippery path be dangerous?",
         "A slippery path can make someone slide or fall, so people often fix it before carrying something fragile."),
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("myth", "Ari", "Iris", "wet", "slippery_path"),
    StoryParams("myth", "Mira", "Orin", "thorny", "wind_gust"),
    StoryParams("myth", "Koa", "Bela", "loose", "crowd_jam"),
]


def explain_rejection(mulch: str) -> str:
    return f"(No story: the mulch must be risky enough to make the shrine path unsafe; '{mulch}' does not fit.)"


def asp_facts() -> str:
    import asp
    lines = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for m in MULCHES:
        lines.append(asp.fact("mulch", m))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(T, M, P) :- theme(T), mulch(M), problem(P), risky(M).
risky(M) :- mulch(M), M = wet.
risky(M) :- mulch(M), M = loose.
risky(M) :- mulch(M), M = thorny.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
        print("python-only:", sorted(py - cl))
        print("clingo-only:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        assert sample.story.strip()
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world: furnish, mulch, glance.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--hero")
    ap.add_argument("--guide")
    ap.add_argument("--mulch", choices=MULCHES)
    ap.add_argument("--problem", choices=PROBLEMS)
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
    if args.mulch and args.mulch not in MULCHES:
        raise StoryError(explain_rejection(args.mulch))
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.mulch is None or c[1] == args.mulch)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, mulch, problem = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(NAMES)
    guide = args.guide or rng.choice(GUIDES)
    return StoryParams(theme, hero, guide, mulch, problem)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.hero, params.guide, params.mulch, params.problem, params.seed)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for t, m, p in combos:
            print(f"  {t:8} {m:8} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.guide}: {p.mulch} / {p.problem}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
