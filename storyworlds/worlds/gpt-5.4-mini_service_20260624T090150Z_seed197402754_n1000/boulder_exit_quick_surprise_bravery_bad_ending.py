#!/usr/bin/env python3
"""
A compact storyworld for a space-adventure style scene:
a stranded crew member faces a sudden surprise, shows bravery, and reaches an
exit that may or may not lead to a bad ending.

The world is intentionally small and constraint-checked.  The story grows from
a simulated state: a ship corridor, a boulder, an exit, and a quick choice that
can change the outcome.
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
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the asteroid tunnel"
    view: str = "the stars"
    exit_name: str = "the exit hatch"


@dataclass
class Obstacle:
    label: str
    size: str
    blocks_exit: bool = True
    surprise: bool = True


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_role: str
    obstacle: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "asteroid": Setting(place="the asteroid tunnel", view="the stars", exit_name="the exit hatch"),
    "station": Setting(place="the silent station corridor", view="the blinking panels", exit_name="the airlock exit"),
    "cavern": Setting(place="the moon cavern", view="the far moonlight", exit_name="the narrow exit"),
}

OBSTACLES = {
    "boulder": Obstacle(label="boulder", size="huge"),
    "rockfall": Obstacle(label="rockfall", size="messy"),
    "iceblock": Obstacle(label="ice block", size="heavy"),
}

HEROES = ["Nova", "Milo", "Zed", "Luna", "Rae", "Iris", "Kian", "Tess"]
ROLES = ["pilot", "scanner", "engineer", "cadet", "ranger"]


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def _move_quickly(world: World, hero: Entity) -> None:
    hero.meters["speed"] = hero.meters.get("speed", 0) + 1
    hero.memes["quick"] = hero.memes.get("quick", 0) + 1


def _discover_surprise(world: World, hero: Entity, obstacle: Obstacle) -> None:
    if "surprise" in world.fired:
        return
    world.fired.add("surprise")
    hero.memes["surprised"] = hero.memes.get("surprised", 0) + 1
    world.say(
        f"Then, without warning, a {obstacle.label} was there, blocking {world.setting.exit_name}."
    )
    world.say("It was a sudden surprise in the quiet dark tunnel.")


def _show_bravery(world: World, hero: Entity) -> None:
    hero.memes["brave"] = hero.memes.get("brave", 0) + 1
    world.say(f"{hero.id} took a slow breath and stayed brave.")


def _attempt_exit(world: World, hero: Entity, obstacle: Obstacle) -> None:
    if obstacle.label == "boulder":
        if hero.meters.get("speed", 0) >= 1:
            world.say(
                f"{hero.id} tried to slip past the boulder and reach {world.setting.exit_name} quickly."
            )
        else:
            world.say(f"{hero.id} stepped toward {world.setting.exit_name}, but the boulder still stood in the way.")
    elif obstacle.label == "rockfall":
        world.say(f"{hero.id} hurried toward {world.setting.exit_name}, but loose stone kept falling down.")
    else:
        world.say(f"{hero.id} pushed at the ice block near {world.setting.exit_name}, but it did not budge.")


def _bad_ending(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.memes["hope"] = max(0.0, hero.memes.get("hope", 1.0) - 1)
    world.say(
        f"In the end, the way stayed shut, and the little crew member had to turn back."
    )
    world.say(
        f"The final view was {world.setting.view} beyond the {obstacle.label}, while {world.setting.exit_name} stayed closed."
    )
    world.say("That was a bad ending for the quick mission, even though the brave heart had not quit.")


def tell(setting: Setting, obstacle: Obstacle, hero_name: str, hero_role: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", label=hero_role, phrase=f"a {hero_role}"))
    world.add(Entity(id="obstacle", label=obstacle.label, phrase=f"a {obstacle.size} {obstacle.label}"))

    world.say(
        f"{hero.id} was a young {hero_role} on {setting.place}, where {setting.view} glimmered beyond the dark."
    )
    world.say(f"{hero.id} wanted to get to {setting.exit_name}.")

    world.para()
    _discover_surprise(world, hero, obstacle)
    _show_bravery(world, hero)
    _move_quickly(world, hero)
    _attempt_exit(world, hero, obstacle)

    world.para()
    _bad_ending(world, hero, obstacle)

    world.facts.update(
        hero=hero,
        obstacle=obstacle,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place in SETTINGS:
        for obs in OBSTACLES:
            combos.append((place, obs))
    return combos


def explain_rejection(place: str, obstacle: str) -> str:
    return f"(No story: the chosen space scene on {place} cannot support obstacle '{obstacle}'.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
obstacle(O) :- obstacle_kind(O).
compatible(P,O) :- place(P), obstacle(O), setting_place(P), obstacle_kind(O).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
        lines.append(asp.fact("setting_place", p))
    for o in OBSTACLES:
        lines.append(asp.fact("obstacle_kind", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    obstacle = f["obstacle"]
    setting = f["setting"]
    return [
        f'Write a short space-adventure story for a child about {hero.id}, a {hero.label}, in {setting.place}, with a surprise and a bad ending.',
        f"Tell a simple story where {hero.id} is brave, acts quick, and faces a {obstacle.label} near {setting.exit_name}.",
        f'Write a small story that includes the words "boulder", "exit", and "quick".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    obstacle = f["obstacle"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, who is a {hero.label} on {setting.place}.",
        ),
        QAItem(
            question=f"What surprised {hero.id} near {setting.exit_name}?",
            answer=f"A {obstacle.label} suddenly blocked {setting.exit_name}, so it was a surprise.",
        ),
        QAItem(
            question=f"How did {hero.id} act when the path was blocked?",
            answer=f"{hero.id} stayed brave and moved quick toward the exit, even though the way was blocked.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended badly because the exit stayed closed and the hero had to turn back.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a boulder?", answer="A boulder is a very large rock."),
        QAItem(question="What is an exit?", answer="An exit is a way out of a place."),
        QAItem(question="What does quick mean?", answer="Quick means fast or done in little time."),
        QAItem(question="What is bravery?", answer="Bravery is staying steady and trying even when something feels scary."),
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.obstacle and args.obstacle not in OBSTACLES:
        raise StoryError("Unknown obstacle.")
    combos = valid_combos()
    combos = [c for c in combos if (args.place is None or c[0] == args.place)
              and (args.obstacle is None or c[1] == args.obstacle)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obstacle = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(HEROES)
    hero_role = args.role or rng.choice(ROLES)
    return StoryParams(place=place, hero_name=hero_name, hero_role=hero_role, obstacle=obstacle)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], OBSTACLES[params.obstacle], params.hero_name, params.hero_role)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with a surprise, bravery, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
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


CURATED = [
    StoryParams(place="asteroid", hero_name="Nova", hero_role="pilot", obstacle="boulder"),
    StoryParams(place="station", hero_name="Milo", hero_role="engineer", obstacle="rockfall"),
    StoryParams(place="cavern", hero_name="Luna", hero_role="scanner", obstacle="iceblock"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
