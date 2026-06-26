#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/movement_competition_dialogue_problem_solving_sound_effects.py
========================================================================================================================

A small animal-story world about movement, competition, dialogue, problem solving,
and sound effects.

Premise:
- A young animal wants to move faster than a rival in a simple contest.
- A hurdle makes the first plan fail.
- A helper or self-made fix solves the problem.
- The ending proves the change with a clear finish image and a satisfying sound.

This script follows the Storyweavers world contract:
- typed entities with meters and memes
- a world model drives the prose
- child-facing story text
- inline ASP twin plus Python reasonableness gate
- generation, QA, trace, JSON, and verification support
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("speed", "stumble", "tired", "blocked"):
            self.meters.setdefault(k, 0.0)
        for k in ("hope", "worry", "pride", "frustration", "joy", "teamwork"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        table = {"subject": "it", "object": "it", "possessive": "its"}
        return table[case]


@dataclass
class Race:
    name: str
    movement: str
    sound: str
    obstacle: str
    fix: str
    keyword: str
    pace_gain: float
    obstacle_kind: str
    obstacle_meter: str


@dataclass
class Track:
    place: str
    surface: str
    sound: str
    affords: set[str] = field(default_factory=set)


@dataclass
class FixTool:
    id: str
    label: str
    use_line: str
    sound: str
    clears: set[str]
    helps: set[str]


class World:
    def __init__(self, track: Track) -> None:
        self.track = track
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def animals(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "animal"]

    def items(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "thing"]

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
    track: str
    race: str
    hero: str
    rival: str
    helper: str
    tool: str
    seed: Optional[int] = None


TRACKS = {
    "lane": Track(place="the grassy lane", surface="grass", sound="swish", affords={"dash", "hop"}),
    "bridge": Track(place="the little bridge", surface="wood", sound="tap", affords={"run", "dash"}),
    "meadow": Track(place="the open meadow", surface="dirt", sound="thump", affords={"run", "hop", "dash"}),
}

RACES = {
    "dash": Race(
        name="dash",
        movement="dash",
        sound="pitter-patter",
        obstacle="a muddy patch",
        fix="step around the mud and keep going",
        keyword="movement",
        pace_gain=1.0,
        obstacle_kind="mud",
        obstacle_meter="blocked",
    ),
    "hop": Race(
        name="hop",
        movement="hop",
        sound="boing",
        obstacle="a row of twigs",
        fix="hop over the twigs one by one",
        keyword="competition",
        pace_gain=1.0,
        obstacle_kind="twigs",
        obstacle_meter="stumble",
    ),
    "run": Race(
        name="run",
        movement="run",
        sound="pound-pound",
        obstacle="a wobbling gate",
        fix="push the gate open carefully",
        keyword="movement",
        pace_gain=1.0,
        obstacle_kind="gate",
        obstacle_meter="blocked",
    ),
}

TOOLS = {
    "stick": FixTool(
        id="stick",
        label="a smooth stick",
        use_line="use the stick like a little pointer",
        sound="click",
        clears={"blocked"},
        helps={"gate"},
    ),
    "mat": FixTool(
        id="mat",
        label="a flat mat",
        use_line="lay the mat over the mud",
        sound="plop",
        clears={"blocked"},
        helps={"mud"},
    ),
    "ladder": FixTool(
        id="ladder",
        label="a tiny ladder",
        use_line="lean the ladder against the twigs",
        sound="clack",
        clears={"stumble"},
        helps={"twigs"},
    ),
}

ANIMALS = {
    "rabbit": {"type": "rabbit", "label": "Rabbit", "phrase": "a quick white rabbit"},
    "turtle": {"type": "turtle", "label": "Turtle", "phrase": "a careful green turtle"},
    "fox": {"type": "fox", "label": "Fox", "phrase": "a bright red fox"},
    "mouse": {"type": "mouse", "label": "Mouse", "phrase": "a tiny gray mouse"},
    "bear": {"type": "bear", "label": "Bear", "phrase": "a sturdy brown bear"},
}

HEROES = ["Pip", "Milo", "Tala", "Nico", "Benny", "Luna", "Otto", "Kiki"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for t_name, track in TRACKS.items():
        for r_name, race in RACES.items():
            if r_name not in track.affords:
                continue
            for tool_id, tool in TOOLS.items():
                if race.obstacle_kind in tool.helps:
                    out.append((t_name, r_name, tool_id))
    return out


ASP_RULES = r"""
valid(T,R,Tool) :- track(T), race(R), affords(T,R), tool(Tool), obstacle(R,O), helps(Tool,O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for t_name, track in TRACKS.items():
        lines.append(asp.fact("track", t_name))
        for r in sorted(track.affords):
            lines.append(asp.fact("affords", t_name, r))
    for r_name, race in RACES.items():
        lines.append(asp.fact("race", r_name))
        lines.append(asp.fact("obstacle", r_name, race.obstacle_kind))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for o in sorted(tool.helps):
            lines.append(asp.fact("helps", tool_id, o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def choose_name(rng: random.Random, gender: str = "animal") -> str:
    return rng.choice(HEROES)


def pick_animal(rng: random.Random) -> str:
    return rng.choice(list(ANIMALS))


def reasonableness_gate(track: Track, race: Race, tool: FixTool) -> None:
    if race.name not in track.affords:
        raise StoryError("This track does not support that kind of movement.")
    if race.obstacle_kind not in tool.helps:
        raise StoryError("The chosen tool does not meaningfully solve the obstacle.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about movement and competition.")
    ap.add_argument("--track", choices=TRACKS)
    ap.add_argument("--race", choices=RACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--rival", choices=list(ANIMALS))
    ap.add_argument("--helper", choices=list(ANIMALS))
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
    combos = valid_combos()
    if args.track and args.race and args.tool:
        reasonableness_gate(TRACKS[args.track], RACES[args.race], TOOLS[args.tool])
    valid = [
        c for c in combos
        if (not args.track or c[0] == args.track)
        and (not args.race or c[1] == args.race)
        and (not args.tool or c[2] == args.tool)
    ]
    if not valid:
        raise StoryError("No valid combination matches the given options.")
    track, race, tool = rng.choice(sorted(valid))
    hero = args.hero or choose_name(rng)
    rival = args.rival or pick_animal(rng)
    helper = args.helper or pick_animal(rng)
    if helper == rival:
        helper = "mouse" if rival != "mouse" else "fox"
    return StoryParams(track=track, race=race, hero=hero, rival=rival, helper=helper, tool=tool)


def _move(world: World, animal: Entity, race: Race, narrate: bool = True) -> None:
    animal.meters["speed"] += race.pace_gain
    animal.memes["joy"] += 0.5
    if narrate:
        world.say(f"{animal.label} moved fast with a {race.sound} sound.")


def _meet_obstacle(world: World, animal: Entity, race: Race, tool: FixTool, narrate: bool = True) -> None:
    if animal.meters["blocked"] < THRESHOLD and animal.meters["stumble"] < THRESHOLD:
        return
    if narrate:
        world.say(f"{animal.label} stopped at {race.obstacle}.")
        world.say(f'"We need a new plan," said {world.facts["helper"].label}.')


def _solve(world: World, hero: Entity, helper: Entity, race: Race, tool: FixTool) -> None:
    if race.obstacle_kind == "mud":
        hero.meters["blocked"] = 0.0
    if race.obstacle_kind == "twigs":
        hero.meters["stumble"] = 0.0
    if race.obstacle_kind == "gate":
        hero.meters["blocked"] = 0.0
    hero.memes["frustration"] = max(0.0, hero.memes["frustration"] - 1.0)
    hero.memes["teamwork"] += 1.0
    helper.memes["pride"] += 1.0
    world.say(f'"{tool.use_line}," said {helper.label}. {tool.sound}!')
    world.say(f"{hero.label} tried it, and the problem got smaller right away.")


def tell(track: Track, race: Race, tool: FixTool, hero_name: str, rival_kind: str, helper_kind: str) -> World:
    world = World(track)
    hero = world.add(Entity(id=hero_name, kind="animal", type=hero_name.lower(), label=hero_name, phrase=f"a small {hero_name.lower()}"))
    rival_info = ANIMALS[rival_kind]
    helper_info = ANIMALS[helper_kind]
    rival = world.add(Entity(id="Rival", kind="animal", type=rival_info["type"], label=rival_info["label"], phrase=rival_info["phrase"]))
    helper = world.add(Entity(id="Helper", kind="animal", type=helper_info["type"], label=helper_info["label"], phrase=helper_info["phrase"]))
    tool_ent = world.add(Entity(id=tool.id, kind="thing", type="tool", label=tool.label, phrase=tool.label, caretaker=hero.id))

    world.facts.update(hero=hero, rival=rival, helper=helper, tool=tool_ent, race=race, track=track)

    world.say(f"At {track.place}, {hero.label} and {rival.label} started a small competition.")
    world.say(f'{hero.label} said, "I want to {race.movement} first!"')
    world.say(f'{rival.label} said, "Then let’s go!" The track went {track.sound}, {track.sound}.')
    _move(world, hero, race, narrate=True)
    if race.obstacle_meter == "blocked":
        hero.meters["blocked"] += 1
    else:
        hero.meters["stumble"] += 1
    world.say(f"Then {hero.label} met {race.obstacle}.")
    world.say(f'{helper.label} said, "I have an idea."')
    _meet_obstacle(world, hero, race, tool, narrate=True)
    _solve(world, hero, helper, race, tool)
    _move(world, hero, race, narrate=True)
    world.say(f"In the end, {hero.label} finished with a happy {race.sound} and a bright grin.")
    hero.memes["joy"] += 1.0
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story for young children about movement and competition at {f["track"].place}.',
        f'Tell a gentle story where {f["hero"].label} wants to {f["race"].movement} but needs help with {f["race"].obstacle}.',
        f'Write a story with dialogue, a problem, a clever fix, and a {f["race"].sound} ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, rival, helper, race, track = f["hero"], f["rival"], f["helper"], f["race"], f["track"]
    return [
        QAItem(
            question=f"Who was the story mainly about at {track.place}?",
            answer=f"The story was mainly about {hero.label}, who wanted to {race.movement} in the competition.",
        ),
        QAItem(
            question=f"What problem got in the way of {hero.label}'s race?",
            answer=f"{hero.label} ran into {race.obstacle}, so the first plan did not work.",
        ),
        QAItem(
            question=f"How did {helper.label} help {hero.label}?",
            answer=f"{helper.label} gave a simple idea and helped solve the problem with {f['tool'].label}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.label} finishing happily after the fix worked, and the track went {track.sound} again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is competition?",
            answer="Competition is when two or more animals try their best to do something, like win a race or do a task well.",
        ),
        QAItem(
            question="What does a helper do?",
            answer="A helper gives support, ideas, or tools that make a problem easier to solve.",
        ),
        QAItem(
            question="What is a sound effect in a story?",
            answer="A sound effect is a word that helps you imagine a noise, like tap, swish, or clack.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.kind:6}) meters={meters} memes={memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(track="lane", race="dash", hero="Pip", rival="rabbit", helper="mouse", tool="mat"),
    StoryParams(track="bridge", race="run", hero="Milo", rival="fox", helper="bear", tool="stick"),
    StoryParams(track="meadow", race="hop", hero="Tala", rival="turtle", helper="mouse", tool="ladder"),
]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def generate(params: StoryParams) -> StorySample:
    world = tell(
        TRACKS[params.track],
        RACES[params.race],
        TOOLS[params.tool],
        params.hero,
        params.rival,
        params.helper,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (track, race, tool) combos:\n")
        for t, r, tool in combos:
            print(f"  {t:8} {r:8} {tool:8}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.race} at {p.track}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
