#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/submit_sharing_superhero_story.py
==================================================================

A tiny standalone storyworld for a superhero sharing tale: a kid-superhero team
wants to submit a shared comic or rescue plan, but a small snag makes them
choose between grabbing the glory or sharing the credit. The world simulates
meters and memes, then renders a complete child-facing story with grounded QA.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2

HERO_NAMES = ["Maya", "Leo", "Nina", "Eli", "Zoey", "Owen", "Ava", "Finn"]
PARTNER_NAMES = ["Jade", "Milo", "Ivy", "Noah", "Ruth", "Theo", "Luna", "Ben"]
ADULT_NAMES = ["Mom", "Dad", "Coach Kim", "Captain Ray"]
SUPER_NAMES = ["Spark Star", "Rocket Kid", "Crimson Comet", "Bright Bolt"]
PLACES = ["the city park", "the school hall", "the rooftop garden", "the rescue club room"]
MISSIONS = ["the poster", "the rescue plan", "the comic page", "the badge idea"]
PROBLEMS = ["ink smudge", "missing sticker", "torn corner", "crumpled page"]
TOOLS = ["glue stick", "fresh marker", "silver tape", "big eraser"]
GIFTS = ["shared badge", "team star", "pair of capes", "bright thank-you note"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"tired": 0.0, "damage": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"joy": 0.0, "pride": 0.0, "sting": 0.0, "share": 0.0})

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
@dataclass
class StoryParams:
    hero: str
    hero_type: str
    partner: str
    partner_type: str
    adult: str
    place: str
    mission: str
    problem: str
    tool: str
    gift: str
    submit: bool = True
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


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

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


def _r_sting(world: World) -> list[str]:
    out = []
    for hero in [e for e in list(world.entities.values()) if e.role in {"hero", "partner"}]:
        if hero.memes["sting"] < THRESHOLD:
            continue
        sig = ("sting", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["share"] += 1
        out.append("__sting__")
    return out


CAUSAL_RULES = [Rule("sting", _r_sting)]


def predict_submit(world: World, hero_id: str) -> dict:
    sim = world.copy()
    sim.get(hero_id).memes["pride"] += 1
    sim.get(hero_id).memes["sting"] += 1
    propagate(sim, narrate=False)
    return {
        "shared": sim.get("hero").memes["share"] >= THRESHOLD and sim.get("partner").memes["share"] >= THRESHOLD
    }


def setup(world: World, hero: Entity, partner: Entity, adult: Entity, place: str, mission: str) -> None:
    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"On a bright day at {place}, {hero.id} and {partner.id} worked like tiny superheroes on {mission}."
    )
    world.say(
        f'{hero.id} wore {hero.pronoun("possessive")} cape and said, "Today we can save the day!" '
        f'{partner.id} nodded, and {adult.label or adult.id} smiled nearby.'
    )


def problem_beats(world: World, problem: str, tool: str) -> None:
    world.say(f"Then a small problem popped up: {problem}.")
    world.say(f"{tool.capitalize()} could help, but only if they used it carefully.")


def want_submit(world: World, hero: Entity, partner: Entity, mission: str) -> None:
    hero.memes["pride"] += 1
    partner.memes["pride"] += 1
    world.say(
        f'{hero.id} wanted to submit {mission} all by {hero.id.lower()}self, because it felt like a big hero moment.'
    )
    world.say(
        f'But {partner.id} gently said, "{hero.id}, we made it together."'
    )


def struggle(world: World, hero: Entity, partner: Entity) -> None:
    hero.memes["sting"] += 1
    partner.memes["sting"] += 1
    world.say(
        f"{hero.id} frowned for a moment, and {partner.id} looked a little sad too."
    )
    propagate(world, narrate=False)
    world.say(
        f"That little sting reminded them that a team win is sweeter when it is shared."
    )


def fix_and_submit(world: World, adult: Entity, hero: Entity, partner: Entity, tool: str, mission: str, gift: str) -> None:
    world.say(
        f"{adult.label or adult.id} came over with {tool} and helped fix the small problem."
    )
    world.say(
        f"Together, they finished {mission} and submit it with both names on the page."
    )
    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    hero.memes["share"] += 1
    partner.memes["share"] += 1
    world.say(
        f"At the end, {hero.id} and {partner.id} held up {gift} and grinned like true superheroes."
    )


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, role="hero", traits=["brave"]))
    partner = world.add(Entity(id=params.partner, kind="character", type=params.partner_type, role="partner", traits=["kind"]))
    adult = world.add(Entity(id="adult", kind="character", type="adult", label=params.adult))
    setup(world, hero, partner, adult, params.place, params.mission)
    world.para()
    problem_beats(world, params.problem, params.tool)
    want_submit(world, hero, partner, params.mission)
    struggle(world, hero, partner)
    world.para()
    fix_and_submit(world, adult, hero, partner, params.tool, params.mission, params.gift)
    world.facts.update(hero=hero, partner=partner, adult=adult, params=params)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, m, pr) for p in PLACES for m in MISSIONS for pr in PROBLEMS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny superhero sharing story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hero")
    ap.add_argument("--partner")
    ap.add_argument("--adult", choices=ADULT_NAMES)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mission:
        combos = [c for c in combos if c[1] == args.mission]
    if args.problem:
        combos = [c for c in combos if c[2] == args.problem]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mission, problem = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    partner_pool = [n for n in PARTNER_NAMES if n != hero]
    partner = args.partner or rng.choice(partner_pool)
    adult = args.adult or rng.choice(ADULT_NAMES)
    return StoryParams(hero, "girl" if hero in {"Maya", "Nina", "Zoey", "Ava"} else "boy",
                       partner, "girl" if partner in {"Jade", "Ivy", "Ruth", "Luna"} else "boy",
                       adult, place, mission, problem, rng.choice(TOOLS), rng.choice(GIFTS))


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a superhero story for a young child that includes the word "submit" and a sharing moment.',
        f"Tell a story where {p.hero} and {p.partner} try to submit {p.mission} together, learn to share, and finish as a team.",
        f"Write a gentle superhero tale where a small problem is fixed with help, and the heroes submit their work with both names."
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(f"Who is the story about?", f"It is about {p.hero} and {p.partner}, two little superheroes who worked as a team. They learned that sharing the win makes the mission feel even bigger."),
        QAItem(f"What did they want to submit?", f"They wanted to submit {p.mission}. It was their shared project, so both of them helped finish it."),
        QAItem(f"How did they solve the problem?", f"They used {p.tool} with help from {p.adult} and fixed the small problem together. That way, the work stayed shared instead of becoming one person's job."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does it mean to share?", "To share means to let other people help, use, or enjoy something with you. Sharing makes teamwork kinder and more fair."),
        QAItem("What is a superhero?", "A superhero is a made-up hero who uses courage, kindness, and special gear or powers to help others."),
        QAItem("Why is teamwork good?", "Teamwork is good because two helpers can do more than one alone. It also helps people solve hard problems together."),
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
        lines.append(f"  {e.id:8} ({e.type}) role={e.role} memes={dict(e.memes)} meters={dict(e.meters)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
valid(P, M, R) :- place(P), mission(M), problem(R).
"""


def asp_facts() -> str:
    try:
        import asp  # lazy
    except Exception:
        return ""
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m in MISSIONS:
        lines.append(asp.fact("mission", m))
    for r in PROBLEMS:
        lines.append(asp.fact("problem", r))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    # Smoke test ordinary generation
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story.strip()
    except Exception as e:
        print(f"SMOKE FAIL: {e}")
        return 1
    if "submit" not in sample.story.lower():
        print("SMOKE FAIL: expected 'submit' in story.")
        return 1
    # ASP parity is intentionally simple for this small world
    print("OK: smoke test passed.")
    return 0


CURATED = [
    StoryParams("Maya", "girl", "Jade", "girl", "Mom", "the city park", "the poster", "ink smudge", "fresh marker", "shared badge"),
    StoryParams("Leo", "boy", "Theo", "boy", "Dad", "the school hall", "the rescue plan", "torn corner", "silver tape", "pair of capes"),
    StoryParams("Ava", "girl", "Luna", "girl", "Coach Kim", "the rooftop garden", "the comic page", "crumpled page", "big eraser", "team star"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program(show="#show valid/3."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
