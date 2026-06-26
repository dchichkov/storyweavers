#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/surrender_problem_solving_flashback_bravery_myth.py
==============================================================================================================================

A small myth-style storyworld about surrender, problem solving, flashback, and
bravery.

Premise:
- A young hero wants to cross a blocked sacred road.
- A heavy stone gate and a stubborn boast create a problem.
- A remembered lesson from an earlier trial helps the hero choose the wiser path.
- Bravery is not fighting harder, but surrendering pride and solving the problem
  with the river, rope, and help from an elder.

The story model keeps both physical meters and emotional memes:
- meters: blocked, wet, moved, tied, open
- memes: courage, fear, pride, wisdom, hope, relief, memory

The prose is authored from state changes, not from a frozen paragraph template.
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
    role: str = ""
    location: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["blocked", "wet", "moved", "tied", "open"]:
            self.meters.setdefault(k, 0.0)
        for k in ["courage", "fear", "pride", "wisdom", "hope", "relief", "memory"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "goddess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "god"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    obstacle: str
    blocked_by: str
    remedy: str
    flashback_trigger: str
    brave_act: str
    surrender_act: str
    result_image: str


@dataclass
class StoryParams:
    place: str
    problem: str
    hero_name: str
    hero_type: str
    elder_name: str
    elder_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, problem: Problem) -> None:
        self.place = place
        self.problem = problem
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    world = World(place, problem)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        role="hero",
        location=place.label,
        memes={"courage": 1.0, "fear": 0.0, "pride": 1.0, "wisdom": 0.0, "hope": 1.0, "relief": 0.0, "memory": 0.0},
    ))
    elder = world.add(Entity(
        id=params.elder_name,
        kind="character",
        type=params.elder_type,
        label=params.elder_name,
        role="elder",
        location=place.label,
        memes={"courage": 0.5, "wisdom": 2.0, "hope": 1.0, "relief": 0.0, "memory": 0.0},
    ))
    obstacle = world.add(Entity(
        id="gate",
        kind="thing",
        type="stone_gate",
        label="stone gate",
        phrase="a stone gate",
        location=place.label,
        meters={"blocked": 1.0, "wet": 0.0, "moved": 0.0, "tied": 0.0, "open": 0.0},
    ))
    river = world.add(Entity(
        id="river",
        kind="thing",
        type="river",
        label="river",
        phrase="the river below",
        location=place.label,
        meters={"wet": 2.0},
    ))
    rope = world.add(Entity(
        id="rope",
        kind="thing",
        type="rope",
        label="rope",
        phrase="a long rope",
        location=place.label,
        meters={"tied": 0.0},
        owner=elder.id,
    ))
    world.facts.update(hero=hero, elder=elder, gate=obstacle, river=river, rope=rope)
    return world


def _narrate_setup(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    elder: Entity = f["elder"]  # type: ignore[assignment]
    world.say(
        f"Long ago, in {world.place.label}, {hero.label} stood before a stone gate that had shut the sacred road."
    )
    world.say(
        f"{hero.label} had a brave heart, but {world.problem.obstacle} was wider than a spear and heavier than a mule."
    )
    world.say(
        f"Beside {hero.label} stood {elder.label}, who had seen many hard days and never wasted a wise word."
    )


def _flashback(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    hero.memes["memory"] += 1
    hero.memes["wisdom"] += 1
    world.say(
        f"As {hero.label} stared at the gate, a flashback came like a drumbeat from an old night."
    )
    world.say(
        f"Once before, {hero.label} had tried to force a broken bridge and learned that strength alone can fail."
    )
    world.say(
        f"That memory did not make {hero.label} smaller; it made {hero.label} wiser."
    )


def _problem_solving(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    elder: Entity = world.facts["elder"]  # type: ignore[assignment]
    gate: Entity = world.facts["gate"]  # type: ignore[assignment]
    rope: Entity = world.facts["rope"]  # type: ignore[assignment]
    river: Entity = world.facts["river"]  # type: ignore[assignment]

    hero.memes["fear"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.label} wanted to strike the gate at once, but the rocks would not care about anger."
    )
    world.say(
        f"{elder.label} pointed to the river and said that a hard problem sometimes yields to a clever plan."
    )
    world.say(
        f"They tied {rope.label} to the gate and let the river pull where hands could not."
    )
    gate.meters["tied"] += 1
    gate.meters["wet"] += 1
    river.meters["wet"] += 0.5
    world.fired.add(("plan", gate.id))

    gate.meters["blocked"] = max(0.0, gate.meters["blocked"] - 1.0)
    gate.meters["moved"] += 1.0
    gate.meters["open"] += 1.0
    hero.memes["hope"] += 1
    world.say(
        f"The stone groaned, slid, and finally gave way."
    )


def _surrender_and_resolution(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    elder: Entity = world.facts["elder"]  # type: ignore[assignment]
    gate: Entity = world.facts["gate"]  # type: ignore[assignment]

    hero.memes["pride"] = max(0.0, hero.memes["pride"] - 1.0)
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
    hero.memes["courage"] += 1.0
    hero.memes["wisdom"] += 1.0
    hero.memes["relief"] += 1.0
    elder.memes["relief"] += 1.0
    world.say(
        f"Then {hero.label} did the truest brave thing of all: {hero.pronoun('subject')} surrendered pride."
    )
    world.say(
        f"{hero.label} thanked {elder.label}, and together they walked through the open gate."
    )
    world.say(
        f"By dusk, the sacred road shone clear, and {world.problem.result_image}."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    _narrate_setup(world)
    world.para()
    _flashback(world)
    world.say(
        f"{world.facts['hero'].label} remembered that bravery is not only rushing forward; sometimes it is listening."
    )
    world.para()
    _problem_solving(world)
    _surrender_and_resolution(world)
    return world


PLACES = {
    "mountain_pass": Place(
        id="mountain_pass",
        label="the mountain pass",
        mood="stern",
        affords={"blocked_road"},
    ),
    "river_ford": Place(
        id="river_ford",
        label="the river ford",
        mood="bright",
        affords={"blocked_road"},
    ),
    "temple_steps": Place(
        id="temple_steps",
        label="the temple steps",
        mood="holy",
        affords={"blocked_road"},
    ),
}

PROBLEMS = {
    "blocked_road": Problem(
        id="blocked_road",
        obstacle="the road",
        blocked_by="stone gate",
        remedy="river rope plan",
        flashback_trigger="broken bridge",
        brave_act="face the gate",
        surrender_act="surrender pride",
        result_image="the road was open again and the way to the shrine glittered in the sun",
    ),
    "flooded_bridge": Problem(
        id="flooded_bridge",
        obstacle="the bridge",
        blocked_by="flood water",
        remedy="rope and raft plan",
        flashback_trigger="sinking stones",
        brave_act="step back from the edge",
        surrender_act="yield to the river",
        result_image="the raft floated safely and the lantern light reached the far bank",
    ),
    "sleeping_sphinx": Problem(
        id="sleeping_sphinx",
        obstacle="the gate",
        blocked_by="sleeping sphinx",
        remedy="quiet riddle plan",
        flashback_trigger="a lesson in patience",
        brave_act="hold still",
        surrender_act="surrender noise",
        result_image="the sphinx opened one golden eye and the hidden path breathed free",
    ),
}

HEROES = {
    "boy": ["Arin", "Niko", "Tavian", "Leor", "Seth"],
    "girl": ["Mira", "Lyra", "Anya", "Kora", "Thea"],
}

ELDERS = {
    "man": ["Eamon", "Boros", "Ilan"],
    "woman": ["Sera", "Dione", "Mara"],
}

TYPES = {
    "boy": "boy",
    "girl": "girl",
    "man": "man",
    "woman": "woman",
}

CURATED = [
    StoryParams(place="mountain_pass", problem="blocked_road", hero_name="Arin", hero_type="boy", elder_name="Eamon", elder_type="man"),
    StoryParams(place="river_ford", problem="flooded_bridge", hero_name="Mira", hero_type="girl", elder_name="Sera", elder_type="woman"),
    StoryParams(place="temple_steps", problem="sleeping_sphinx", hero_name="Lyra", hero_type="girl", elder_name="Mara", elder_type="woman"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth story world about surrender, problem solving, flashback, and bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--elder-name")
    ap.add_argument("--elder-type", choices=["man", "woman"])
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
    place = args.place or rng.choice(list(PLACES))
    problem = args.problem or rng.choice(list(PROBLEMS))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    elder_type = args.elder_type or rng.choice(["man", "woman"])
    hero_name = args.hero_name or rng.choice(HEROES[hero_type])
    elder_name = args.elder_name or rng.choice(ELDERS[elder_type])
    return StoryParams(
        place=place,
        problem=problem,
        hero_name=hero_name,
        hero_type=hero_type,
        elder_name=elder_name,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    elder: Entity = world.facts["elder"]  # type: ignore[assignment]
    return [
        f"Write a short mythic story for a child about {hero.label} and {elder.label}, with a problem that can be solved without force.",
        f"Tell a story where a brave hero remembers an old failure, then surrenders pride and finds a wiser path.",
        f"Write a gentle myth about {world.place.label} that includes flashback, problem solving, and bravery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    elder: Entity = world.facts["elder"]  # type: ignore[assignment]
    gate: Entity = world.facts["gate"]  # type: ignore[assignment]
    problem: Problem = world.problem
    return [
        QAItem(
            question=f"Why couldn't {hero.label} just rush through {world.place.label} at the start?",
            answer=f"{hero.label} could not rush through because {gate.label} was blocking the road, and force alone would not move it.",
        ),
        QAItem(
            question=f"What did {hero.label} remember in the flashback?",
            answer=f"{hero.label} remembered an old night when trying to force a broken bridge had failed, so the memory taught {hero.pronoun('object')} to be wiser.",
        ),
        QAItem(
            question=f"How did {elder.label} help solve the problem?",
            answer=f"{elder.label} suggested a careful plan using the river and the rope, so the stone gate could be moved safely.",
        ),
        QAItem(
            question=f"What brave thing did {hero.label} do at the end?",
            answer=f"{hero.label} surrendered pride, thanked {elder.label}, and walked through the open gate with a braver heart.",
        ),
        QAItem(
            question=f"What changed after the problem was solved?",
            answer=f"At the end, the blocked road was open again, and {world.problem.result_image}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is surrender in this story?",
            answer="Surrender means the hero stops fighting pride and chooses the wiser path instead of forcing the problem.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a memory from earlier that comes into the story for a moment and helps the character understand what to do now.",
        ),
        QAItem(
            question="What is bravery here?",
            answer="Bravery is not only fighting hard. Here, bravery means listening, accepting help, and choosing the better plan.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully about what is blocking the way and finding a plan that actually works.",
        ),
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: {e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
% A road is blocked when the gate is blocked.
blocked_road(P) :- problem(P), gate_blocked(P).

% A plan is good when it uses rope and river to clear the gate.
good_plan(P) :- blocked_road(P), has_rope(P), has_river(P).

% Bravery can be shown by surrendering pride and accepting the wise plan.
brave_resolution(P) :- good_plan(P), surrender_pride(P), accepts_help(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("gate_blocked", pid))
        lines.append(asp.fact("has_rope", pid))
        lines.append(asp.fact("has_river", pid))
        lines.append(asp.fact("surrender_pride", pid))
        lines.append(asp.fact("accepts_help", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show brave_resolution/1."))
    asp_set = set(asp.atoms(model, "brave_resolution"))
    py_set = {(p,) for p in PROBLEMS}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python ({len(py_set)} problems).")
        return 0
    print("MISMATCH between clingo and Python:")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


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
        print(asp_program("#show brave_resolution/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
