#!/usr/bin/env python3
"""
storyworlds/worlds/fund_puzzle_analog_sharing_bad_ending_adventure.py
=====================================================================

A small adventure-style storyworld about a shared fund, an analog puzzle,
and a bad ending that comes from unfair sharing.

Seed-tale inspiration:
---
Three kids planned an adventure to unlock a tiny cave door. They needed a fund
to buy a sturdy analog map wheel and a puzzle box key. At first, they promised
to share everything fairly. But one child hid the fund pouch and kept the map
wheel, so the puzzle could not be solved. The adventure ended badly, and the
group had to leave with the cave still closed.

Domain shape:
- Physical meters: money, distance, wear, damage, lock_progress.
- Emotional memes: trust, hope, worry, greed, shame.
- Story logic: sharing choices affect whether tools are available and whether
  the puzzle can be solved. Bad sharing can produce a bad ending.
- Adventure tone: a journey to a place, a tool, a challenge, a turn, and an
  ending image that proves what changed.

This world intentionally includes a "bad ending" feature: the story can resolve
with a failed adventure when sharing breaks down or the needed analog tool is
withheld. The prose remains child-facing and concrete.
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
    carried_by: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("money", "distance", "wear", "damage", "lock_progress"):
            self.meters.setdefault(key, 0.0)
        for key in ("trust", "hope", "worry", "greed", "shame", "joy"):
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the old hill path"
    destination: str = "the little cave"
    outdoors: bool = True
    mood: str = "windy"
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    kind: str
    use: str
    requirement: str
    protects: bool = False


@dataclass
class Puzzle:
    id: str
    label: str
    phrase: str
    requires: str
    clue_kind: str
    difficulty: int
    analog: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    trait: str
    tool: str
    puzzle: str
    seed: Optional[int] = None


SETTINGS = {
    "trail": Setting(place="the old hill path", destination="the little cave", mood="windy", affords={"travel", "puzzle"}),
    "woods": Setting(place="the pine woods", destination="the stone arch", mood="quiet", affords={"travel", "puzzle"}),
    "harbor": Setting(place="the harbor lane", destination="the dock door", mood="saltly", affords={"travel", "puzzle"}),
}

TOOLS = {
    "mapwheel": Tool(
        id="mapwheel",
        label="an analog map wheel",
        phrase="a round analog map wheel with painted arrows",
        kind="analog",
        use="read the turning arrows",
        requirement="the wheel must be shared openly",
        protects=False,
    ),
    "lantern": Tool(
        id="lantern",
        label="a lantern",
        phrase="a bright lantern",
        kind="light",
        use="shine on the lock",
        requirement="someone must carry it",
        protects=True,
    ),
    "rope": Tool(
        id="rope",
        label="a rope",
        phrase="a strong rope",
        kind="aid",
        use="pull the latch",
        requirement="the team must hold it together",
        protects=False,
    ),
}

PUZZLES = {
    "cave": Puzzle(
        id="cave",
        label="the cave puzzle",
        phrase="a puzzle lock with four spinning rings",
        requires="mapwheel",
        clue_kind="analog",
        difficulty=2,
        analog=True,
    ),
    "dock": Puzzle(
        id="dock",
        label="the dock puzzle",
        phrase="a gate puzzle with a moving code wheel",
        requires="mapwheel",
        clue_kind="analog",
        difficulty=2,
        analog=True,
    ),
}

NAMES = ["Mina", "Toby", "Rae", "Iris", "Noah", "Pip", "Jules", "Nia"]
TRAITS = ["brave", "curious", "spry", "bold", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for tool_id, tool in TOOLS.items():
            for puzzle_id, puzzle in PUZZLES.items():
                if "puzzle" in setting.affords and tool.kind == "analog" and puzzle.analog:
                    out.append((place, tool_id, puzzle_id))
    return out


def can_share(tool: Tool, puzzle: Puzzle) -> bool:
    return tool.kind == puzzle.clue_kind and tool.analog if hasattr(tool, "analog") else tool.kind == "analog"


def reason_gate(tool: Tool, puzzle: Puzzle) -> bool:
    return tool.kind == "analog" and puzzle.analog and tool.id == puzzle.requires


def explain_rejection(tool: Tool, puzzle: Puzzle) -> str:
    return f"(No story: the {tool.label} does not fit the {puzzle.label}'s analog clues.)"


def introduce(world: World, hero: Entity, helper: Entity) -> None:
    world.say(f"{hero.id} was a {world.facts['trait']} child who loved adventures.")
    world.say(f"{helper.id} came along because {hero.pronoun('possessive')} {helper.type} liked helping on long walks.")


def journey(world: World, hero: Entity, setting: Setting) -> None:
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} friend set off along {setting.place}.")
    world.say(f"The air felt {setting.mood}, and {setting.destination} waited at the end of the path.")


def fund_story(world: World, hero: Entity) -> None:
    fund = world.get("fund")
    hero.memes["hope"] += 1
    fund.meters["money"] += 5
    world.say(f"They had a small fund for the trip, and it held just enough coins for one good tool.")
    world.say(f"{hero.id} promised to share the fund so everyone could help choose what to buy.")


def purchase(world: World, tool: Tool, hero: Entity, helper: Entity) -> None:
    item = world.add(Entity(id=tool.id, type=tool.kind, label=tool.label, phrase=tool.phrase, owner=hero.id, carried_by=hero.id))
    world.facts["tool"] = item
    world.say(f"They bought {tool.phrase}, because the adventure needed something steady and real.")
    world.say(f"{hero.id} carried it first, then said they would share it with {helper.id} when the puzzle began.")


def predict_failure(world: World, puzzle: Puzzle) -> bool:
    fund = world.get("fund")
    tool = world.get(world.facts["tool"].id)
    if fund.meters["money"] < 1:
        return True
    if tool.carried_by is None:
        return True
    if tool.id != puzzle.requires:
        return True
    return False


def dispute(world: World, hero: Entity, helper: Entity) -> None:
    fund = world.get("fund")
    fund.memes["greed"] += 1
    hero.memes["trust"] -= 1
    helper.memes["worry"] += 1
    world.say(f"But when the path got steep, {hero.id} hid the fund pouch inside a pocket.")
    world.say(f"{helper.id} reached out, yet {hero.id} would not share the money or the map wheel.")


def attempt_puzzle(world: World, hero: Entity, helper: Entity, puzzle: Puzzle) -> bool:
    tool = world.get(world.facts["tool"].id)
    if tool.id != puzzle.requires or tool.carried_by != hero.id:
        world.say(f"At {world.setting.destination}, the {puzzle.label} would not open.")
        return False
    world.say(f"They tried the {tool.label} on {puzzle.phrase}, turning the arrows together.")
    return True


def bad_ending(world: World, hero: Entity, helper: Entity, puzzle: Puzzle) -> None:
    hero.memes["shame"] += 1
    helper.memes["worry"] += 1
    world.say(f"The wheel never lined up, and the door stayed shut.")
    world.say(f"In the end, they went home in silence, leaving {puzzle.phrase} unsolved and the cave dark.")


def tell(setting: Setting, tool: Tool, puzzle: Puzzle, hero_name: str, helper_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy" if hero_name in {"Toby", "Noah", "Pip"} else "girl"))
    helper = world.add(Entity(id=helper_name, kind="character", type="boy" if helper_name in {"Toby", "Noah", "Pip"} else "girl"))
    fund = world.add(Entity(id="fund", type="thing", label="fund pouch", phrase="a small fund pouch"))
    world.facts.update(hero=hero, helper=helper, trait=trait, setting=setting, puzzle=puzzle, tool=None, fund=fund)

    introduce(world, hero, helper)
    journey(world, hero, setting)
    fund_story(world, hero)
    world.para()
    purchase(world, tool, hero, helper)
    dispute(world, hero, helper)
    world.para()
    if not attempt_puzzle(world, hero, helper, puzzle):
        bad_ending(world, hero, helper, puzzle)
    else:
        world.say(f"For a moment, the rings turned, but the sharing had already gone wrong.")
        bad_ending(world, hero, helper, puzzle)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child about a shared fund, an analog tool, and a puzzle.',
        f"Tell a short story where {f['hero'].id} and {f['helper'].id} travel to {world.setting.destination} with a fund and an analog map wheel.",
        f'Write a gentle adventure that includes the words "fund", "puzzle", and "analog", and ends badly because the sharing fails.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    puzzle: Puzzle = f["puzzle"]
    tool: Optional[Entity] = f["tool"]
    return [
        QAItem(
            question=f"Who went on the adventure to {world.setting.destination}?",
            answer=f"{hero.id} went with {helper.id} on the adventure to {world.setting.destination}.",
        ),
        QAItem(
            question="What did the fund help them buy?",
            answer=f"The fund helped them buy {tool.label if tool else 'an important tool'} for the trip.",
        ),
        QAItem(
            question=f"Why did the {puzzle.label} stay closed?",
            answer=f"It stayed closed because the {tool.label if tool else 'tool'} was not shared fairly and the team could not use it together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does analog mean?",
            answer="Analog means something works with a real physical object or dial instead of a digital screen.",
        ),
        QAItem(
            question="What is a fund?",
            answer="A fund is money kept together for a purpose, like buying something the group needs.",
        ),
        QAItem(
            question="What is a puzzle?",
            answer="A puzzle is a problem or lock that needs careful thinking to solve.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use or enjoy something too, not keeping it all for yourself.",
        ),
    ]


ASP_RULES = r"""
% A story is valid when the place affords travel and puzzle work, and the tool
% matches the puzzle's analog requirement.
valid_story(P, T, Z) :- place(P), tool(T), puzzle(Z),
    affords(P, travel), affords(P, puzzle),
    analog_tool(T), analog_puzzle(Z), requires(Z, T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.kind == "analog":
            lines.append(asp.fact("analog_tool", tid))
        lines.append(asp.fact("tool_kind", tid, t.kind))
    for zid, z in PUZZLES.items():
        lines.append(asp.fact("puzzle", zid))
        if z.analog:
            lines.append(asp.fact("analog_puzzle", zid))
        lines.append(asp.fact("requires", zid, z.requires))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about a fund, an analog puzzle, and sharing gone wrong.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--puzzle", choices=PUZZLES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    choices = [(p, t, z) for p, t, z in valid_combos()
               if (args.place is None or p == args.place)
               and (args.tool is None or t == args.tool)
               and (args.puzzle is None or z == args.puzzle)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    place, tool, puzzle = rng.choice(choices)
    hero = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, hero=hero, helper=helper, trait=trait, tool=tool, puzzle=puzzle)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    tool = TOOLS[params.tool]
    puzzle = PUZZLES[params.puzzle]
    world = tell(setting, tool, puzzle, params.hero, params.helper, params.trait)
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
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, dict(e.meters), dict(e.memes))
    if qa:
        print()
        for group, items in (("prompts", sample.prompts), ("story_qa", sample.story_qa), ("world_qa", sample.world_qa)):
            print(f"== {group} ==")
            if group == "prompts":
                for i, p in enumerate(items, 1):
                    print(f"{i}. {p}")
            else:
                for item in items:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")


CURATED = [
    StoryParams(place="trail", hero="Mina", helper="Toby", trait="brave", tool="mapwheel", puzzle="cave"),
    StoryParams(place="woods", hero="Iris", helper="Rae", trait="curious", tool="mapwheel", puzzle="cave"),
    StoryParams(place="harbor", hero="Noah", helper="Pip", trait="bold", tool="mapwheel", puzzle="dock"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        print(asp_program("#show valid_story/3."))
        print()
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
