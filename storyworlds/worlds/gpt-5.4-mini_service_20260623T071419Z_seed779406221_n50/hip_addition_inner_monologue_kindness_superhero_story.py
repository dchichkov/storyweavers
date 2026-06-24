#!/usr/bin/env python3
"""
storyworlds/worlds/hip_addition_inner_monologue_kindness_superhero_story.py
==========================================================================

A small superhero-flavored story world about a kid hero, a tricky hip injury,
and the kind addition of help, with inner monologue and kindness driving the
turn. The premise is simple: a young hero wants to keep helping in the city, but
their sore hip makes one fast rescue feel impossible until they add the right
helpful step and choose kindness over pride.

Seed words: hip, addition
Features: inner monologue, kindness
Style: superhero story
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Scene:
    place: str
    sky: str = "clear"
    sounds: str = ""
    afford_help: bool = True


@dataclass
class Problem:
    id: str
    label: str
    danger: str
    has_weight: bool = True
    needs_balance: bool = True


@dataclass
class Help:
    id: str
    label: str
    action: str
    addition: str
    kindness: str
    fixes_problem: bool = True


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


def _default_meters() -> dict[str, float]:
    return {"pain": 0.0, "balance": 0.0, "kindness": 0.0, "help": 0.0}


def _default_memes() -> dict[str, float]:
    return {"worry": 0.0, "hope": 0.0, "pride": 0.0, "relief": 0.0, "joy": 0.0}


def propagate(world: World) -> None:
    hero = world.get("hero")
    problem = world.get("problem")
    helper = world.get("helper")
    if hero.meters["pain"] >= THRESHOLD and ("pain_notice",) not in world.fired:
        world.fired.add(("pain_notice",))
        hero.memes["worry"] += 1
    if helper.meters["help"] >= THRESHOLD and ("help_land",) not in world.fired:
        world.fired.add(("help_land",))
        problem.meters["balance"] += helper.meters["help"]
        hero.meters["pain"] = max(0.0, hero.meters["pain"] - helper.meters["help"])
        hero.memes["relief"] += 1
        helper.meters["kindness"] += 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for problem in PROBLEMS:
            for help_id in HELPS:
                if problem_supports_help(PROBLEMS[problem], HELPS[help_id]):
                    combos.append((place, problem, help_id))
    return combos


def problem_supports_help(problem: Problem, help_item: Help) -> bool:
    return problem.needs_balance and help_item.fixes_problem


def reasonableness_gate(problem: Problem, help_item: Help) -> bool:
    return problem_supports_help(problem, help_item)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with inner monologue and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--help", dest="help_item", choices=HELPS)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.help_item is None or c[2] == args.help_item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, help_id = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    hero_type = args.__dict__.get("hero_type") or rng.choice(["girl", "boy"])
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    return StoryParams(
        place=place,
        problem=problem,
        help_item=help_id,
        hero=hero,
        hero_type=hero_type,
        sidekick=sidekick,
    )


@dataclass
class StoryParams:
    place: str
    problem: str
    help_item: str
    hero: str
    hero_type: str
    sidekick: str
    seed: Optional[int] = None


def tell(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero,
                            meters=_default_meters(), memes=_default_memes()))
    sidekick = world.add(Entity(id="sidekick", kind="character", type="girl", label=params.sidekick,
                                meters=_default_meters(), memes=_default_memes()))
    helper = world.add(Entity(id="helper", kind="character", type="woman", label="the kind medic",
                              role="helper", meters=_default_meters(), memes=_default_memes()))
    problem = world.add(Entity(id="problem", kind="thing", type="problem", label=PROBLEMS[params.problem].label,
                               meters={"danger": 1.0}, memes=_default_memes()))
    helper_item = HELPS[params.help_item]

    hero.meters["pain"] = 1.0
    hero.memes["pride"] = 1.0
    hero.memes["hope"] = 1.0
    sidekick.memes["hope"] = 1.0

    world.say(f"In {world.scene.place}, {hero.label} ran across the rooftop with {sidekick.label} beside {hero.pronoun('object')}.")
    world.say(f"{hero.label.capitalize()} wanted to keep the city safe, but {hero.pronoun('possessive')} hip gave a sharp ache.")
    world.say(f'Inside {hero.pronoun("possessive")} head, {hero.pronoun()} thought, "I can still help. I just need a better way."')
    world.para()
    world.say(f"Then {problem.label} tipped into danger, and {sidekick.label} called for help.")
    world.say(f"{helper.label.capitalize()} arrived with {helper_item.label} and said, \"We can add {helper_item.addition} to the plan.\"")
    if reasonableness_gate(PROBLEMS[params.problem], helper_item):
        helper.meters["help"] = 1.0
        propagate(world)
        world.para()
        world.say(f"{hero.label.capitalize()} took a careful breath and let {helper.label} help with {helper_item.action}.")
        world.say(f"The kind addition worked: {problem.label} was steady again, and {hero.label}'s hip stopped hurting so much.")
        world.say(f"{hero.label} smiled at {sidekick.label}. Together they looked over the bright city, ready for the next rescue.")
    world.facts.update(hero=hero, sidekick=sidekick, helper=helper, problem=problem, helper_item=helper_item, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a young child set in {f["params"].place} that includes a sore hip, an addition to the plan, and a kind helper.',
        f"Tell a gentle superhero story where {f['hero'].label} thinks out loud, asks for help, and makes a kind addition instead of pushing through the pain.",
        f'Write a child-friendly superhero tale that uses the words "hip" and "addition" and ends with kindness helping the hero.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    problem: Entity = f["problem"]
    item: Help = f["helper_item"]
    return [
        QAItem(
            question=f"Who is the story about in {f['params'].place}?",
            answer=f"It is about {hero.label}, a young superhero who wanted to help the city even with a sore hip.",
        ),
        QAItem(
            question=f"What did {hero.label} think inside {hero.pronoun('possessive')} head?",
            answer=f"{hero.label} thought that {hero.pronoun()} could still help if {hero.pronoun()} found a better way. That inner monologue kept the story moving instead of stopping the hero completely.",
        ),
        QAItem(
            question=f"How did {helper.label} help with the problem?",
            answer=f"{helper.label.capitalize()} brought {item.label} and added {item.addition} to the rescue plan. That kind addition steadied {problem.label} and helped {hero.label}'s hip feel better.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{problem.label.capitalize()} was safe again, and {hero.label} did not have to prove anything alone. The hero chose kindness, accepted help, and stood tall over the city with a lighter heart.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hip?",
            answer="A hip is part of your body near your waist and upper leg. You use it when you walk, run, and bend.",
        ),
        QAItem(
            question="What does addition mean?",
            answer="Addition means putting more of something together to make a bigger total. In a story, it can also mean adding a helpful step to a plan.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping, speaking gently, and caring about someone else's feelings. Kindness makes a hard moment feel less heavy.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the voice in a character's head that tells what they are thinking and feeling. It lets readers hear worry, hope, and brave ideas.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    bits = ["--- world model state ---"]
    for e in world.entities.values():
        bits.append(f"{e.id}: meters={e.meters} memes={e.memes} attrs={e.attrs}")
    return "\n".join(bits)


PLACES = {
    "city": Scene(place="the city", sky="bright", sounds="sirens and wind"),
    "tower": Scene(place="the hero tower", sky="clear", sounds="echoes and footsteps"),
    "bridge": Scene(place="the river bridge", sky="windy", sounds="traffic humming"),
}
PROBLEMS = {
    "stuck_door": Problem(id="stuck_door", label="a stuck door", danger="locked tight"),
    "fallen_sign": Problem(id="fallen_sign", label="a fallen sign", danger="toppling"),
    "scooter_chain": Problem(id="scooter_chain", label="a broken scooter chain", danger="jammed"),
}
HELPS = {
    "brace": Help(id="brace", label="a soft hip brace", action="fit the brace snugly", addition="a steady squeeze", kindness="gentle care"),
    "stepstool": Help(id="stepstool", label="a step stool", action="lift the sign safely", addition="a careful boost", kindness="patient help"),
    "bandage": Help(id="bandage", label="a cool bandage", action="wrap the sore spot", addition="a calm touch", kindness="warm kindness"),
}
HERO_NAMES = ["Nova", "Piper", "Rio", "Zara", "Milo", "Tess"]
SIDEKICKS = ["Bean", "Juno", "Sky", "Pepper"]


CURATED = [
    StoryParams(place="city", problem="fallen_sign", help_item="brace", hero="Nova", hero_type="girl", sidekick="Bean"),
    StoryParams(place="tower", problem="scooter_chain", help_item="bandage", hero="Milo", hero_type="boy", sidekick="Sky"),
    StoryParams(place="bridge", problem="stuck_door", help_item="stepstool", hero="Tess", hero_type="girl", sidekick="Juno"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for pid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if pr.needs_balance:
            lines.append(asp.fact("needs_balance", pid))
    for hid, h in HELPS.items():
        lines.append(asp.fact("help", hid))
        if h.fixes_problem:
            lines.append(asp.fact("fixes_problem", hid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Problem, Help) :- place(Place), problem(Problem), help(Help), needs_balance(Problem), fixes_problem(Help).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py != asp_set:
        print("Mismatch between Python and ASP valid combos.")
        return 1
    print(f"OK: ASP matches Python ({len(py)} combos).")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("Smoke test failed: empty story.")
        return 1
    print("OK: smoke test generated a non-empty story.")
    return 0


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
