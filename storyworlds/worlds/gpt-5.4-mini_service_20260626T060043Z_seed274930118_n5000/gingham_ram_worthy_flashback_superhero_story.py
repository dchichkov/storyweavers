#!/usr/bin/env python3
"""
A standalone storyworld for a tiny superhero tale with a flashback.

Seed premise:
A small hero is not sure they are worthy of the town's trust. In a flashback,
they remember an old gingham cape and a stubborn ram blocking the way to a
helpful rescue. In the present, they use that memory to choose a brave, kind
solution.

This world is intentionally small and constraint-driven:
- The hero wants to do something heroic.
- The flashback explains why they know the right move.
- The ram creates a concrete problem to solve.
- The ending proves the hero became worthy through action, not swagger.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    problem: str
    gear: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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


SETTINGS = {
    "city": Setting(place="the city square", indoor=False, affords={"ram"}),
    "ridge": Setting(place="the windy ridge", indoor=False, affords={"ram"}),
    "barn": Setting(place="the old barnyard", indoor=False, affords={"ram"}),
}

PROBLEMS = {
    "ram": Problem(
        id="ram",
        verb="help the trapped parade goat",
        gerund="helping the trapped parade goat",
        rush="charge toward the gate",
        mess="bump",
        soil="sent sprawling",
        zone={"legs", "torso"},
        keyword="ram",
    ),
}

GEAR = {
    "cape": Gear(
        id="cape",
        label="a gingham cape",
        covers={"torso"},
        guards={"bump"},
        prep="put on the gingham cape",
        tail="tied the gingham cape tight",
    ),
    "boots": Gear(
        id="boots",
        label="sturdy boots",
        covers={"feet", "legs"},
        guards={"bump"},
        prep="lace up the sturdy boots",
        tail="pulled on the sturdy boots",
        plural=True,
    ),
}

GIRL_NAMES = ["Mina", "Nora", "Ivy", "Lena", "June"]
BOY_NAMES = ["Tate", "Owen", "Finn", "Jace", "Eli"]


def reasonableness_gate(problem: Problem, gear: Gear) -> bool:
    return bool(problem.zone & gear.covers and problem.mess in gear.guards)


def explain_rejection(problem: Problem, gear: Gear) -> str:
    return (
        f"(No story: {gear.label} would not honestly protect the hero from {problem.gerund}. "
        f"It needs to cover the right body part and guard the right kind of bump.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with a flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--sidekick-name")
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for prob in setting.affords:
            for gid, gear in GEAR.items():
                if reasonableness_gate(PROBLEMS[prob], gear):
                    out.append((place, prob, gid))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.gear:
        prob = PROBLEMS[args.problem]
        gear = GEAR[args.gear]
        if not reasonableness_gate(prob, gear):
            raise StoryError(explain_rejection(prob, gear))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.problem is None or c[1] == args.problem)
        and (args.gear is None or c[2] == args.gear)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, gear = rng.choice(sorted(combos))
    if args.gender is None:
        gender = rng.choice(["girl", "boy"])
    else:
        gender = args.gender
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sidekick_name = args.sidekick_name or rng.choice(["Pip", "Rae", "Milo", "Bea"])
    hero_type = "girl" if gender == "girl" else "boy"
    return StoryParams(place=place, problem=problem, gear=gear, hero_name=name, hero_type=hero_type, sidekick_name=sidekick_name)


def _setup_world(params: StoryParams) -> tuple[World, Entity, Entity, Entity, Entity, Gear, Problem]:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, meters={}, memes={}))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type="girl", label="sidekick"))
    mayor = world.add(Entity(id="Mayor", kind="character", type="woman", label="the mayor"))
    problem = PROBLEMS[params.problem]
    gear = GEAR[params.gear]
    gear_ent = world.add(Entity(
        id=gear.id,
        kind="thing",
        type="gear",
        label=gear.label,
        protective=True,
    ))
    gear_ent.meters["clean"] = 1
    gear_ent.worn_by = hero.id
    cape_color = world.add(Entity(
        id="CapeNote",
        kind="thing",
        type="cloth",
        label="the gingham cape",
        phrase="a red-and-white gingham cape",
        owner=hero.id,
    ))
    cape_color.meters["special"] = 1
    return world, hero, sidekick, mayor, gear_ent, gear, problem


def propagate(world: World) -> None:
    hero = next(e for e in world.entities.values() if e.kind == "character" and e.label == "")
    sidekick = next(e for e in world.entities.values() if e.id != hero.id and e.kind == "character" and e.id != "Mayor")
    if hero.memes.get("doubt", 0) >= THRESHOLD and hero.memes.get("memory", 0) >= THRESHOLD:
        sig = ("worthy", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worthy"] = hero.memes.get("worthy", 0) + 1
            hero.memes["fear"] = 0


def tell(params: StoryParams) -> World:
    world, hero, sidekick, mayor, gear_ent, gear, problem = _setup_world(params)
    hero.memes["doubt"] = 1
    hero.memes["hope"] = 1
    sidekick.memes["admiration"] = 1

    world.say(f"{hero.id} was a small hero with a big heart, but {hero.pronoun('possessive')} confidence wobbled on some days.")
    world.say(f"{hero.id} loved the red-and-white gingham cape because it looked brave, even when {hero.id} did not always feel brave.")
    world.say(f"{params.sidekick_name} said {hero.id} could help the town, and {hero.id} wanted to believe that.")

    world.para()
    world.say(f"One afternoon, the mayor pointed to {world.setting.place} and asked for help.")
    world.say(f"A stubborn ram had blocked the way, and the crowd could not get through.")
    world.say(f"{hero.id} wanted to {problem.verb}, but the ram stamped its hoof and kept the path shut.")

    world.para()
    world.say(f"Then came a flashback.")
    world.say(f"{hero.id} remembered a rainy day when the gingham cape snagged on a fence while a young ram pushed into the yard.")
    world.say(f"Back then, {hero.id} had been scared at first, but {params.sidekick_name} had shown {hero.id} how to stay calm and move slowly.")
    hero.memes["memory"] = 1
    propagate(world)

    world.para()
    world.say(f"{hero.id} took a breath and remembered that being worthy meant helping without showing off.")
    if gear == GEAR["cape"]:
        world.say(f"{hero.id} {gear.prep}, because the cape helped {hero.pronoun('object')} stay steady while {hero.id} moved near the ram.")
    else:
        world.say(f"{hero.id} {gear.prep}, because careful steps would matter more than a flashy entrance.")
    world.say(f"Instead of charging, {hero.id} spoke softly, opened a path, and let the ram step aside on its own.")
    world.say(f"At last, the crowd could cross, and the mayor smiled at the calm little hero.")

    world.para()
    world.say(f"By the end, {hero.id} was not just wearing the gingham cape.")
    world.say(f"{hero.id} had become worthy of it.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        'Write a short superhero story for a young child that includes the word "gingham".',
        f"Tell a gentle flashback story where {hero.id} remembers an old cape and learns to be worthy.",
        'Write a simple superhero tale with a ram, a flashback, and a brave but kind ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    sidekick: Entity = f["sidekick"]  # type: ignore[assignment]
    problem: Problem = f["problem"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a small superhero who learns to be worthy by helping calmly.",
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=f"{hero.id} remembered an old day with the gingham cape and a younger ram, when {sidekick.id} helped {hero.id} stay calm.",
        ),
        QAItem(
            question=f"Why did the ram matter in the story?",
            answer=f"The ram blocked the way, so {hero.id} had to solve the problem without rushing into it.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, {hero.id} proved that being worthy comes from helping kindly, and the town could cross again.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gingham?",
            answer="Gingham is a cloth pattern made of neat checks or squares, often seen on clothes like shirts or dresses.",
        ),
        QAItem(
            question="What is a ram?",
            answer="A ram is a male sheep with strong horns, and it can be stubborn and pushy when it wants to go somewhere.",
        ),
        QAItem(
            question="What does worthy mean?",
            answer="Worthy means good enough for trust or praise because of actions, like helping others in a careful and kind way.",
        ),
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
        bits = []
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.protective:
            bits.append("protective=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A problem is compatible with gear if the gear covers the right region and
% guards the right kind of mess.
compatible(P,G) :- problem(P), gear(G), problem_zone(P,R), gear_covers(G,R), problem_mess(P,M), gear_guards(G,M).
valid_story(Place,P,G) :- setting(Place), affords(Place,P), compatible(P,G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for p in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, p))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("problem_mess", pid, prob.mess))
        for r in sorted(prob.zone):
            lines.append(asp.fact("problem_zone", pid, r))
    for gid, gear in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for r in sorted(gear.covers):
            lines.append(asp.fact("gear_covers", gid, r))
        for m in sorted(gear.guards):
            lines.append(asp.fact("gear_guards", gid, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


CURATED = [
    StoryParams(place="city", problem="ram", gear="cape", hero_name="Mina", hero_type="girl", sidekick_name="Pip"),
    StoryParams(place="ridge", problem="ram", gear="boots", hero_name="Tate", hero_type="boy", sidekick_name="Rae"),
    StoryParams(place="barn", problem="ram", gear="cape", hero_name="Ivy", hero_type="girl", sidekick_name="Milo"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    world.facts.update(
        hero=world.get(params.hero_name),
        sidekick=world.get(params.sidekick_name),
        problem=PROBLEMS[params.problem],
        gear=GEAR[params.gear],
        params=params,
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
        models = asp_valid_combos()
        print(f"{len(models)} compatible story combos:")
        for combo in models:
            print(" ", combo)
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
            header = f"### {p.hero_name}: {p.problem} at {p.place} (gear: {p.gear})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
