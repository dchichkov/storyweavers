#!/usr/bin/env python3
"""
storyworlds/worlds/rob_worm_dim_puzzle_problem_solving_adventure.py
====================================================================

A small storyworld about a robby little adventurer, a worm-dim puzzle, and a
problem that can only be solved by noticing clues, testing ideas, and trying a
different path.

The premise:
- A child explorer, Rob, finds a worm-dim puzzle in a curious place.
- The puzzle is not just a toy: it is a lock, a map, and a trick.
- Something important is hidden until the puzzle is solved.

The world model tracks:
- physical meters: progress, loose pieces, hidden-door state, repair state
- emotional memes: worry, curiosity, relief, pride

The story shape:
- Rob wants to solve the puzzle and reach the good thing behind it.
- The puzzle resists until Rob uses a clue, a method, and a helper.
- Solving the puzzle opens the path and ends the worry.

This file follows the Storyweavers contract:
- standalone stdlib script
- eager import of results containers
- lazy import of asp helper only inside ASP functions
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- --verify checks Python/ASP parity and exercises generated stories
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    opened: bool = False
    solved: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    obstacle: str
    clue: str
    method: str
    reward: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Puzzle:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    difficulty: str
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    fixes: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_unsolved(world: World) -> list[str]:
    out = []
    for puzzle in world.entities.values():
        if puzzle.kind != "thing":
            continue
        if puzzle.meters["progress"] >= THRESHOLD and not puzzle.solved:
            sig = ("solve", puzzle.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            puzzle.solved = True
            out.append(f"The puzzle clicked into place.")
    return out


def _r_reveal(world: World) -> list[str]:
    out = []
    for puzzle in world.entities.values():
        if puzzle.kind != "thing" or not puzzle.solved:
            continue
        if puzzle.opened:
            continue
        if puzzle.meters["opened"] < THRESHOLD:
            continue
        sig = ("reveal", puzzle.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        puzzle.opened = True
        out.append("A hidden path opened.")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    for ent in world.characters():
        if ent.memes["worry"] < THRESHOLD:
            continue
        if ent.memes["relief"] >= THRESHOLD:
            continue
        if any(p.solved for p in world.entities.values() if p.kind == "thing"):
            sig = ("relief", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["relief"] += 1
            out.append(f"{ent.id} felt relief.")
    return out


CAUSAL_RULES = [
    _r_unsolved,
    _r_reveal,
    _r_relief,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def explore(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["curiosity"] += 1
    hero.meters["progress"] += 1
    world.say(
        f"{hero.id} loved adventure and wanted to {activity.verb}. "
        f"{activity.gerund.capitalize()} made {hero.pronoun('object')} feel brave."
    )


def find_problem(world: World, hero: Entity, activity: Activity, puzzle: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"Then {hero.id} found the worm-dim puzzle: {puzzle.phrase}. "
        f"It would not open just because {hero.id} rushed at it."
    )
    world.say(
        f"The only way through was to notice the {activity.clue} and use a steady {activity.method}."
    )


def try_wrong_way(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters["stuck"] += 1
    world.say(
        f"{hero.id} tried to {activity.rush}, but that only made the puzzle stay shut."
    )


def use_tool(world: World, hero: Entity, tool: Entity, activity: Activity, puzzle: Entity) -> None:
    hero.meters["progress"] += 1
    hero.memes["curiosity"] += 1
    puzzle.meters["progress"] += 1
    puzzle.meters["opened"] += 1
    world.say(
        f"At last, {hero.id} used {tool.phrase} to follow the clue. "
        f"That helped {hero.pronoun('object')} {activity.method} the puzzle apart, one careful piece at a time."
    )
    propagate(world, narrate=True)


def celebrate(world: World, hero: Entity, activity: Activity, puzzle: Entity) -> None:
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"With a soft click, the worm-dim puzzle opened and showed {activity.reward}. "
        f"{hero.id} smiled, because the hard problem had turned into a new path."
    )
    world.say(
        f"In the end, {hero.id} was still adventurous, but now {hero.pronoun()} knew how to solve a tricky thing."
    )


SETTINGS = {
    "library": Setting(place="the old library", indoor=True, affords={"puzzle"}),
    "cave": Setting(place="the dim cave", indoor=False, affords={"puzzle"}),
    "attic": Setting(place="the dusty attic", indoor=True, affords={"puzzle"}),
    "garden": Setting(place="the moonlit garden", indoor=False, affords={"puzzle"}),
}

ACTIVITIES = {
    "puzzle": Activity(
        id="puzzle",
        verb="solve the worm-dim puzzle",
        gerund="solving puzzles",
        rush="pull the wrong lever",
        obstacle="a locked panel",
        clue="tiny worm-shaped mark",
        method="careful step-by-step thinking",
        reward="a map to the bright exit",
        keyword="puzzle",
        tags={"puzzle", "problem solving", "adventure"},
    ),
    "maze": Activity(
        id="maze",
        verb="cross the maze",
        gerund="crossing mazes",
        rush="dash into the first hallway",
        obstacle="a twisty passage",
        clue="chalk arrows",
        method="slow looking and checking",
        reward="a shortcut to the treasure room",
        keyword="maze",
        tags={"puzzle", "adventure"},
    ),
}

PUZZLES = {
    "wormdim_box": Puzzle(
        id="wormdim_box",
        label="worm-dim puzzle box",
        phrase="a small worm-dim puzzle box with twisty seams",
        type="puzzle_box",
        region="hands",
        difficulty="tricky",
        needs={"clue", "tool"},
        tags={"puzzle", "worm-dim"},
    ),
    "wormdim_gate": Puzzle(
        id="wormdim_gate",
        label="worm-dim gate puzzle",
        phrase="a gate of thin plates that only lined up by clues",
        type="gate",
        region="path",
        difficulty="hard",
        needs={"clue", "tool"},
        tags={"puzzle", "worm-dim"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="a lantern",
        phrase="a lantern",
        helps={"dark"},
        fixes={"puzzle", "maze"},
    ),
    "rope": Tool(
        id="rope",
        label="a rope",
        phrase="a sturdy rope",
        helps={"climb"},
        fixes={"maze"},
    ),
    "notebook": Tool(
        id="notebook",
        label="a notebook",
        phrase="a little notebook",
        helps={"clue"},
        fixes={"puzzle"},
    ),
}

NAMES = ["Rob", "Ria", "Ben", "Mina", "Toby", "Lila", "Nico", "Zara"]
TRAITS = ["curious", "brave", "careful", "lively", "steady"]


@dataclass
class StoryParams:
    place: str
    activity: str
    puzzle: str
    tool: str
    name: str = "Rob"
    trait: str = "curious"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for puzzle_id, puzzle in PUZZLES.items():
                if "puzzle" not in puzzle.tags:
                    continue
                for tool_id, tool in TOOLS.items():
                    if "puzzle" in tool.fixes:
                        combos.append((place, act_id, puzzle_id, tool_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small adventure storyworld about Rob and a worm-dim puzzle.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--puzzle", choices=PUZZLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.puzzle is None or c[2] == args.puzzle)
              and (args.tool is None or c[3] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, puzzle, tool = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        puzzle=puzzle,
        tool=tool,
        name=args.name or "Rob",
        trait=args.trait or rng.choice(TRAITS),
    )


def tell(setting: Setting, activity: Activity, puzzle_cfg: Puzzle, tool_cfg: Tool, hero_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", label=hero_name))
    puzzle = world.add(Entity(id=puzzle_cfg.id, type=puzzle_cfg.type, label=puzzle_cfg.label, phrase=puzzle_cfg.phrase))
    tool = world.add(Entity(id=tool_cfg.id, type="tool", label=tool_cfg.label, phrase=tool_cfg.phrase))

    world.say(f"{hero.id} was a {trait} little adventurer who loved adventure.")
    world.say(f"One day, {hero.id} came to {setting.place} and looked for a {activity.keyword}.")
    world.para()
    explore(world, hero, activity)
    find_problem(world, hero, activity, puzzle)
    try_wrong_way(world, hero, activity)
    world.para()
    use_tool(world, hero, tool, activity, puzzle)
    celebrate(world, hero, activity, puzzle)

    world.facts.update(hero=hero, activity=activity, puzzle=puzzle, tool=tool, setting=setting)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PUZZLES[params.puzzle], TOOLS[params.tool], params.name, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    puzzle = f["puzzle"]
    return [
        f'Write a short adventure story for a young child about {hero.id} and a worm-dim puzzle.',
        f"Tell a problem-solving story where {hero.id} must {act.verb} to open {puzzle.phrase}.",
        f'Write a simple story that includes a clue, a tool, and the word "puzzle".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    puzzle = f["puzzle"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a curious little adventurer who liked to solve tricky things.",
        ),
        QAItem(
            question=f"What problem did {hero.id} find?",
            answer=f"{hero.id} found {puzzle.phrase}, and it would not open until the clue was used the right way.",
        ),
        QAItem(
            question=f"What helped {hero.id} solve the puzzle?",
            answer=f"{tool.phrase} helped {hero.id} follow the clue and use careful thinking to solve the puzzle.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"At the end, the worm-dim puzzle opened and showed {act.reward}, so the hard problem became a new path.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a puzzle?",
            answer="A puzzle is a problem or game that needs careful thinking to solve.",
        ),
        QAItem(
            question="Why do explorers carry a lantern?",
            answer="Explorers carry a lantern so they can see in dark places like caves or attics.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find a way that makes the trouble go away.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
solved(P) :- puzzle(P), progress(P, N), N >= 1.
opened(P) :- solved(P), opened_req(P).
helped(T, P) :- tool(T), fixes(T, puzzle), uses(T, P).
valid_story(Place, Act, Puzzle, Tool) :- affords(Place, Act), puzzle(Puzzle), tool(Tool), helped(Tool, Puzzle).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PUZZLES:
        lines.append(asp.fact("puzzle", pid))
        lines.append(asp.fact("opened_req", pid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for fix in sorted(tool.fixes):
            lines.append(asp.fact("fixes", tid, fix))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple]:
    return [(p, a, pu, t) for (p, a, pu, t) in asp_valid_stories()]


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    sample = generate(resolve_params(argparse.Namespace(place=None, activity=None, puzzle=None, tool=None, name="Rob", trait=None), random.Random(7)))
    _ = sample.story
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
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


CURATED = [
    StoryParams(place="library", activity="puzzle", puzzle="wormdim_box", tool="notebook", name="Rob", trait="curious"),
    StoryParams(place="cave", activity="puzzle", puzzle="wormdim_gate", tool="lantern", name="Rob", trait="brave"),
    StoryParams(place="attic", activity="puzzle", puzzle="wormdim_box", tool="notebook", name="Rob", trait="careful"),
    StoryParams(place="garden", activity="puzzle", puzzle="wormdim_gate", tool="lantern", name="Rob", trait="steady"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for place, act, puzzle, tool in stories:
            print(f"  {place:10} {act:8} {puzzle:16} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.activity} at {p.place} (puzzle: {p.puzzle})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
