#!/usr/bin/env python3
"""
storyworlds/worlds/wooden_problem_solving_twist_superhero_story.py
==================================================================

A standalone storyworld for a small superhero tale with a wooden object, a
problem-solving turn, and a twist ending.

Premise:
- A young superhero spots a problem in a town square.
- The problem seems like a simple rescue, but it turns into a trickier puzzle.
- The hero uses thinking, a tool, and a helper to solve it.
- The twist is that the "villain" is not a real villain at all, and the wooden
  object matters to the solution.

This file follows the Storyweavers contract:
- self-contained stdlib script
- imports storyworlds/results.py eagerly
- lazily imports storyworlds/asp.py inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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

    def __post_init__(self) -> None:
        for k in ("damage", "repair", "noise", "worry", "joy", "curiosity", "trust"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    light: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    title: str
    verb: str
    thing: str
    source: str
    clue: str
    twist_clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    fixes: set[str] = field(default_factory=set)
    carries: set[str] = field(default_factory=set)
    hint: str = ""
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    hero_name: str
    sidekick_name: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
    "city_square": Setting(place="the city square", light="bright", affords={"stuck_gate", "low_bridge", "lost_signal"}),
    "rooftop": Setting(place="the rooftop", light="golden", affords={"stuck_gate", "lost_signal"}),
    "harbor": Setting(place="the harbor", light="windy", affords={"low_bridge", "lost_signal"}),
}

PROBLEMS = {
    "stuck_gate": Problem(
        id="stuck_gate",
        title="stuck gate",
        verb="open the gate",
        thing="gate",
        source="a jammed latch",
        clue="It would not budge, even with two hard pushes.",
        twist_clue="The latch was not broken at all; it was tied shut from the inside with string.",
        tags={"metal", "string", "twist"},
    ),
    "low_bridge": Problem(
        id="low_bridge",
        title="low bridge",
        verb="reach the bridge button",
        thing="bridge",
        source="a missing lever",
        clue="The button was too high for anyone to tap from the walkway.",
        twist_clue="The bridge was not stuck; it was designed for a hidden wooden pedal below.",
        tags={"wooden", "bridge", "twist"},
    ),
    "lost_signal": Problem(
        id="lost_signal",
        title="lost signal",
        verb="find the beacon",
        thing="beacon",
        source="a foggy roof horn",
        clue="The red light kept blinking in the wrong place.",
        twist_clue="The blinking was not an alarm; it was a trail pointing to a wooden box.",
        tags={"light", "wooden", "twist"},
    ),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="rope",
        phrase="a long rope",
        fixes={"stuck_gate"},
        carries={"stuck_gate"},
        hint="It can pull a stuck thing without breaking it.",
    ),
    "mirror": Tool(
        id="mirror",
        label="mirror",
        phrase="a bright mirror",
        fixes={"lost_signal"},
        carries={"lost_signal"},
        hint="It can bounce light where eyes cannot reach.",
    ),
    "wooden_wedge": Tool(
        id="wooden_wedge",
        label="wooden wedge",
        phrase="a smooth wooden wedge",
        fixes={"low_bridge", "stuck_gate"},
        carries={"low_bridge"},
        hint="It can fit into a small gap and press a hidden switch.",
    ),
}

HEROES = ["Nova", "Mira", "Arlo", "Zane", "Luna", "Kai"]
SIDEKICKS = ["Zip", "Pip", "Toto", "Bea", "Dot", "Finn"]


def story_allowed(problem: Problem, tool: Tool) -> bool:
    return problem.id in tool.fixes or problem.id in tool.carries


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for pid in setting.affords:
            for tid, tool in TOOLS.items():
                if story_allowed(PROBLEMS[pid], tool):
                    out.append((place, pid, tid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld with a wooden twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, tool = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        problem=problem,
        tool=tool,
        hero_name=args.name or rng.choice(HEROES),
        sidekick_name=args.sidekick or rng.choice(SIDEKICKS),
    )


def _act_problem(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["curiosity"] += 1
    if problem.id == "stuck_gate":
        hero.memes["worry"] += 1
    world.say(f"{hero.id} spotted {problem.title} at {world.setting.place}.")
    world.say(problem.clue)


def _solve(world: World, hero: Entity, sidekick: Entity, problem: Problem, tool: Tool) -> None:
    hero.memes["trust"] += 1
    sidekick.memes["trust"] += 1
    world.say(f"{hero.id} and {sidekick.id} looked closely and decided to solve it together.")
    if tool.id == "wooden_wedge":
        world.say(f"They slid the wooden wedge into a tiny crack and pressed the hidden switch.")
    elif tool.id == "mirror":
        world.say(f"They used the mirror to send a bright flash where the clue pointed.")
    else:
        world.say(f"They used the rope to pull the jammed piece free, slowly and carefully.")
    world.say(f"Then the problem changed shape in a surprising way.")
    if problem.id == "stuck_gate":
        world.say("The gate opened, and the 'locked' side was only a puppet prop tied from inside.")
        world.say("The twist was that no villain was trapped there at all; someone had set up a practice puzzle.")
    elif problem.id == "low_bridge":
        world.say("The bridge lowered, and the hidden wooden pedal clicked under the boardwalk.")
        world.say("The twist was that the bridge had never been broken; it needed the secret wooden step.")
    else:
        world.say("The blinking light led them to a small wooden box, and inside was a rescue map.")
        world.say("The twist was that the signal was a clue, not a warning.")
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1


def tell(setting: Setting, problem: Problem, tool: Tool, hero_name: str, sidekick_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="hero", label="superhero"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="sidekick", label="sidekick"))
    gadget = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, owner=hero.id))
    world.facts.update(hero=hero, sidekick=sidekick, problem=problem, tool=tool, gadget=gadget)

    world.say(f"{hero.id} was a small superhero who loved helping people.")
    world.say(f"{sidekick.id} stayed close, because every good rescue worked better with two pairs of eyes.")
    world.say(f"One afternoon at {setting.place}, there was a {problem.title}.")
    world.para()
    _act_problem(world, hero, problem)
    world.say(f"{hero.id} held up {gadget.phrase} and thought hard.")
    world.say(f"{tool.hint}")
    world.para()
    _solve(world, hero, sidekick, problem, tool)
    world.say(f"In the end, {hero.id} and {sidekick.id} stood beside the fixed {problem.thing}, smiling at the clever answer.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    tool = f["tool"]
    return [
        f"Write a short superhero story for young children about {hero.id} solving {problem.title} with {tool.label}.",
        f"Tell a gentle rescue story that includes a wooden object and ends with a twist.",
        f"Write a simple story where a hero thinks carefully, uses {tool.phrase}, and discovers the problem was not what it seemed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    problem = f["problem"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a small superhero, and {sidekick.id}, who helped with the rescue.",
        ),
        QAItem(
            question=f"What problem did they have to solve?",
            answer=f"They had to deal with the {problem.title} at {world.setting.place}.",
        ),
        QAItem(
            question=f"What tool helped them?",
            answer=f"{tool.phrase} helped them think through the problem and find the clever answer.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the problem was not a real villain problem at all; it was a puzzle with a hidden answer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave helper who tries to protect others and solve hard problems.",
        ),
        QAItem(
            question="Why can a wooden object be useful?",
            answer="Wooden things can be strong, simple, and helpful for making tools or hidden puzzle pieces.",
        ),
        QAItem(
            question="Why do helpers look closely at a problem before acting?",
            answer="Looking closely can show the real cause, so they can choose the best way to fix it.",
        ),
    ]
    if any("wooden" in p.tags for p in PROBLEMS.values()):
        out.append(QAItem(
            question="What is a wooden wedge?",
            answer="A wooden wedge is a small piece of wood that can fit into a crack or gap and help move something.",
        ))
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:12} ({e.kind:9}) meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PROBLEMS[params.problem], TOOLS[params.tool], params.hero_name, params.sidekick_name)
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
problem(place,problem_id) :- affords(place,problem_id).
wooden_tool(tool_id) :- tool(tool_id), carries(tool_id,problem_id), problem(place,problem_id).
valid(place,problem_id,tool_id) :- problem(place,problem_id), tool(tool_id), story_ok(place,problem_id,tool_id).
story_ok(place,problem_id,tool_id) :- affords(place,problem_id), fixes(tool_id,problem_id).
twist(place,problem_id) :- valid(place,problem_id,tool_id), problem_id = low_bridge.
#show valid/3.
#show twist/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for p in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, p))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem_id", pid))
        for t in sorted(prob.tags):
            lines.append(asp.fact("tag", pid, t))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(tool.fixes):
            lines.append(asp.fact("fixes", tid, p))
        for p in sorted(tool.carries):
            lines.append(asp.fact("carries", tid, p))
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
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


CURATED = [
    StoryParams(place="city_square", problem="stuck_gate", tool="wooden_wedge", hero_name="Nova", sidekick_name="Zip"),
    StoryParams(place="harbor", problem="low_bridge", tool="wooden_wedge", hero_name="Mira", sidekick_name="Pip"),
    StoryParams(place="rooftop", problem="lost_signal", tool="mirror", hero_name="Arlo", sidekick_name="Dot"),
]


def resolve_invalid(args: argparse.Namespace, rng: random.Random) -> None:
    if args.tool == "rope" and args.problem == "low_bridge":
        raise StoryError("Rope cannot solve the low bridge puzzle in this world.")
    if args.tool == "mirror" and args.problem == "stuck_gate":
        raise StoryError("The mirror does not help with the stuck gate in this story.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    resolve_invalid(args, rng)
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, tool = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        problem=problem,
        tool=tool,
        hero_name=args.name or rng.choice(HEROES),
        sidekick_name=args.sidekick or rng.choice(SIDEKICKS),
    )


def build_parser() -> argparse.ArgumentParser:
    return build_parser.__wrapped__()  # type: ignore


def _build_parser_impl() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with a wooden twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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


build_parser.__wrapped__ = _build_parser_impl  # type: ignore


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show twist/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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
            header = f"### {p.hero_name}: {p.problem} at {p.place} ({p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
