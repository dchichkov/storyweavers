#!/usr/bin/env python3
"""
storyworlds/worlds/diffuse_line_ammonia_problem_solving_inner_monologue.py
===========================================================================

A small whodunit-style storyworld about a puzzling ammonia smell, a tricky line
on the floor, and a careful little act of problem solving. The hero thinks aloud
in inner monologue, follows clues, tests a reasonable fix, and ends with a happy
quiet room.

Core premise:
- Something sharp-smelling spreads through a room.
- A suspicious line on the floor points toward a source.
- The character investigates, reasons step by step, and diffuses the problem.
- The ending proves the room is safer and calmer.

This script is a standalone Storyweavers world file.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the laundry room"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Puzzle:
    id: str
    clue: str
    symptom: str
    source: str
    smell: str
    spread: str
    action: str
    fix: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    action: str
    outcome: str
    plural: bool = False


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_smell_spread(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("ammonia", 0.0) < THRESHOLD:
            continue
        sig = ("smell", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["alarm"] = actor.memes.get("alarm", 0.0) + 1
        out.append("The sharp smell filled the room.")
    return out


def _r_line_hint(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("line_seen") and not world.facts.get("line_noted"):
        world.facts["line_noted"] = True
        out.append("The pale line on the floor looked like a clue.")
    return out


def _r_fix_clear(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("fixed") and not world.facts.get("cleared_narrated"):
        world.facts["cleared_narrated"] = True
        out.append("The room felt fresh again.")
    return out


CAUSAL_RULES = [
    Rule("smell_spread", "physical", _r_smell_spread),
    Rule("line_hint", "social", _r_line_hint),
    Rule("fix_clear", "physical", _r_fix_clear),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def trace_problem(world: World) -> list[str]:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


SETTINGS = {
    "laundry": Setting(place="the laundry room", indoors=True, affords={"investigate"}),
    "hall": Setting(place="the hallway", indoors=True, affords={"investigate"}),
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"investigate"}),
}

PUZZLES = {
    "ammonia": Puzzle(
        id="ammonia",
        clue="a sharp ammonia smell",
        symptom="the air stung a little",
        source="a tipped cleaning bottle",
        smell="ammonia",
        spread="diffused through the room",
        action="look carefully for the source",
        fix="open the window and clean up the spill",
        reveal="the bottle had leaked near the baseboard",
        tags={"ammonia", "diffuse", "line"},
    ),
    "line": Puzzle(
        id="line",
        clue="a pale line across the floor",
        symptom="it ran like a thin trail",
        source="a track from the spill",
        smell="ammonia",
        spread="spread along the line",
        action="follow the line to see where it went",
        fix="wipe the line and air out the room",
        reveal="the line pointed straight to the source",
        tags={"line", "diffuse", "ammonia"},
    ),
}

TOOLS = [
    Tool("window", "the window", {"ammonia", "diffuse"}, "open", "let the bad smell drift away"),
    Tool("cloth", "a clean cloth", {"line"}, "wipe", "erase the suspicious line"),
    Tool("bowl", "a bowl of baking soda", {"ammonia"}, "set out", "help soak up the smell"),
]


@dataclass
class StoryParams:
    place: str
    puzzle: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


NAMES_GIRL = ["Mina", "Ivy", "Ada", "Nora", "Lila", "June"]
NAMES_BOY = ["Eli", "Noah", "Milo", "Finn", "Arlo", "Theo"]
TRAITS = ["careful", "curious", "brave", "quiet", "clever"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for pid in PUZZLES:
            if "investigate" in setting.affords:
                combos.append((place, pid))
    return combos


def choose_tool(puzzle: Puzzle) -> Optional[Tool]:
    for tool in TOOLS:
        if puzzle.id in tool.helps or puzzle.tags & tool.helps:
            return tool
    return None


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.puzzle not in PUZZLES:
        raise StoryError("Unknown puzzle.")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("Unknown gender.")
    if params.puzzle == "line" and params.place == "laundry":
        return
    if not choose_tool(PUZZLES[params.puzzle]):
        raise StoryError("No reasonable fix exists for this puzzle.")


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PUZZLES.items():
        lines.append(asp.fact("puzzle", pid))
        lines.append(asp.fact("smell", pid, p.smell))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag", pid, t))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", t.id, h))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S, P) :- affords(S, investigate), puzzle(P), smell(P, ammonia), tag(P, diffuse).
has_tool(P) :- puzzle(P), helps(T, ammonia).
valid_story(S, P) :- compatible(S, P), has_tool(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(s, p) for s, p in valid_combos() if choose_tool(PUZZLES[p])}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def investigate(world: World, hero: Entity, puzzle: Puzzle) -> None:
    world.say(f"{hero.id} frowned and took a slow breath.")
    world.say(
        f"In {world.setting.place}, {hero.pronoun('subject')} thought, "
        f'"If the smell is ammonia, then something nearby must be leaking."'
    )
    world.facts["line_seen"] = True
    world.say(
        f"{hero.id} noticed {puzzle.clue} and followed it with careful steps."
    )
    if puzzle.id == "ammonia":
        world.say(
            f"{hero.id}'s inner voice whispered, 'A line can point to where a spill started.'"
        )
    else:
        world.say(
            f"{hero.id}'s inner voice whispered, 'The line itself might be the clue.'"
        )
    propagate(world, narrate=True)


def solve(world: World, hero: Entity, puzzle: Puzzle, tool: Tool) -> None:
    if tool.id == "window":
        world.say(
            f"{hero.id} opened the window and let fresh air move through the room."
        )
        world.say(
            f"{hero.id} thought, 'If the smell can diffuse away, the room can become safe again.'"
        )
    elif tool.id == "cloth":
        world.say(f"{hero.id} wiped the line until it faded from view.")
        world.say(f"{hero.id} thought, 'A clue is useful, but a clean floor is better.'")
    elif tool.id == "bowl":
        world.say(f"{hero.id} set out a bowl to help the smell settle down.")
    world.facts["fixed"] = True
    propagate(world, narrate=True)
    world.say(
        f"It worked: {puzzle.reveal}, and the sharp smell was gone."
    )
    world.say(
        f"By the end, {hero.id} smiled at the quiet room. The little mystery was solved."
    )


def tell(setting: Setting, puzzle: Puzzle, hero_name: str, hero_type: str, helper: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait]))
    helper_ent = world.add(Entity(id="Helper", kind="character", type=helper, label="the helper"))
    clue = world.add(Entity(id="Clue", type="thing", label="the line", phrase="a pale line"))
    source = world.add(Entity(id="Source", type="thing", label="the bottle", phrase=puzzle.source))
    source.meters["ammonia"] = 1.0

    world.say(
        f"{hero.id} was a little {trait} {hero.type} who liked solving puzzling things."
    )
    world.say(
        f"One afternoon in {setting.place}, {hero.id} noticed {puzzle.clue}."
    )
    world.say(
        f"{puzzle.symptom.capitalize()}, and the air carried {puzzle.smell}."
    )
    world.para()
    investigate(world, hero, puzzle)
    tool = choose_tool(puzzle)
    if tool is None:
        raise StoryError("No reasonable tool exists for this puzzle.")
    world.para()
    world.say(
        f"{hero.id} chose {tool.label} because {tool.outcome}."
    )
    solve(world, hero, puzzle, tool)
    world.facts.update(hero=hero, helper=helper_ent, clue=clue, source=source, puzzle=puzzle, tool=tool)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    puzzle = f["puzzle"]
    return [
        f'Write a child-friendly whodunit story about "{puzzle.id}" with a careful clue and a happy ending.',
        f"Tell a short mystery where {hero.id} notices {puzzle.clue} and solves it with inner monologue.",
        f"Write a simple story that uses the words diffuse, line, and ammonia, and ends with the room feeling safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    puzzle = f["puzzle"]
    tool = f["tool"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"What kind of smell did {hero.id} notice in the room?",
            answer=f"{hero.id} noticed a sharp ammonia smell that made the room feel odd at first.",
        ),
        QAItem(
            question=f"What clue did {hero.id} follow to solve the mystery?",
            answer=f"{hero.id} followed a pale line on the floor because it seemed to point toward the source.",
        ),
        QAItem(
            question=f"How did {hero.id} fix the problem?",
            answer=f"{hero.id} used {tool.label} and careful problem solving to deal with the spill and freshen the room.",
        ),
        QAItem(
            question=f"Who helped keep the story calm and safe?",
            answer=f"{helper.id} was there as a helper, and {hero.id} did the thinking and the fixing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when something diffuses?",
            answer="When something diffuses, it spreads out and becomes less concentrated over a larger space.",
        ),
        QAItem(
            question="What is ammonia?",
            answer="Ammonia is a sharp-smelling substance often found in some cleaning products.",
        ),
        QAItem(
            question="Why can a line on the floor be a clue?",
            answer="A line can be a clue because it may point toward where something moved or leaked from.",
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world about diffuse, line, and ammonia.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--puzzle", choices=PUZZLES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place and args.puzzle and args.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.puzzle is None or c[1] == args.puzzle)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, puzzle_id = rng.choice(sorted(combos))
    puzzle = PUZZLES[puzzle_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, puzzle=puzzle_id, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PUZZLES[params.puzzle], params.name, params.gender, params.helper, params.trait)
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
        print(trace_problem(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="laundry", puzzle="ammonia", name="Mina", gender="girl", helper="mother", trait="careful"),
    StoryParams(place="hall", puzzle="line", name="Eli", gender="boy", helper="father", trait="curious"),
    StoryParams(place="kitchen", puzzle="ammonia", name="Nora", gender="girl", helper="father", trait="clever"),
]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify_gate() -> int:
    import asp
    cl = set(asp_valid_stories())
    py = {(s, p) for s, p in valid_combos() if choose_tool(PUZZLES[p])}
    if cl == py:
        print(f"OK: clingo gate matches valid_combos() ({len(cl)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify_gate())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:\n")
        for s, p in combos:
            print(f"  {s:10} {p}")
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.puzzle} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
