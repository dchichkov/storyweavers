#!/usr/bin/env python3
"""
A tiny ghost-story world: a teenage kid hears cautionary sounds, faces a small
problem, and solves it by listening carefully instead of rushing ahead.

Premise:
- A teenage protagonist explores a dim place at dusk.
- A periwinkle-colored object or glow marks the only friendly clue.
- Strange sound effects warn about a hidden problem.
- The resolution comes from careful listening, a helpful tool, and a smart fix.

The world is intentionally small and classical: one tension, one turn, one
resolution, with story state driving the prose.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old hall"
    indoors: bool = True
    affordances: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    name: str
    verb: str
    sound: str
    clue: str
    risk: str
    fix: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

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
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "old_hall": Setting(place="the old hall", indoors=True, affordances={"listen", "explore"}),
    "attic": Setting(place="the attic", indoors=True, affordances={"listen", "explore"}),
    "porch": Setting(place="the porch", indoors=True, affordances={"listen", "explore"}),
}

PROBLEMS = {
    "creak": Problem(
        id="creak",
        name="creaking step",
        verb="step onto the loose floorboard",
        sound="creeeak",
        clue="soft and steady",
        risk="it might startle somebody or make the floor worse",
        fix="step around it and find the safe board",
        zone={"feet"},
        keyword="creak",
        tags={"sound", "warning"},
    ),
    "rattle": Problem(
        id="rattle",
        name="rattling window",
        verb="touch the shaky window latch",
        sound="clack-clack",
        clue="tap-tap from the glass",
        risk="it might swing open and let in the cold",
        fix="close it gently and latch it properly",
        zone={"hands"},
        keyword="rattle",
        tags={"sound", "warning"},
    ),
    "whisper": Problem(
        id="whisper",
        name="whispering vent",
        verb="look into the narrow vent",
        sound="shhhhhh",
        clue="a thin little whisper",
        risk="it might hide a draft and a missing note",
        fix="follow the whisper to the loose note and tuck it back",
        zone={"eyes", "hands"},
        keyword="whisper",
        tags={"sound", "mystery"},
    ),
}

TOOLS = [
    Tool(
        id="lamp",
        label="a small lamp",
        phrase="a small lamp with a periwinkle shade",
        covers={"hands"},
        guards={"warning"},
        prep="turn on the small lamp first",
        tail="turned on the lamp and looked carefully",
    ),
    Tool(
        id="gloves",
        label="soft gloves",
        phrase="soft gloves with little cuffs",
        covers={"hands"},
        guards={"warning", "mystery"},
        prep="put on soft gloves first",
        tail="slipped on the gloves and checked every corner",
        plural=True,
    ),
    Tool(
        id="shoes",
        label="sturdy shoes",
        phrase="sturdy shoes with grippy soles",
        covers={"feet"},
        guards={"warning"},
        prep="lace up sturdy shoes first",
        tail="laced up the shoes and stepped more slowly",
        plural=True,
    ),
]

NAMES = ["Mina", "Theo", "June", "Eli", "Nora", "Kai", "Zoe", "Milo"]
TRAITS = ["careful", "curious", "quiet", "brave", "teenage"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A problem is reasonable when the setting affords the action and the clue is a warning.
reasonable(S, P) :- setting(S), problem(P), affords(S, A), action(P, A), warning(P).

% A tool is compatible if it protects the same body region the problem threatens
% and its guard matches the problem's tag.
compatible(T, P) :- tool(T), problem(P), guards(T, Tag), tag(P, Tag),
                    covers(T, R), zone(P, R).

has_fix(P) :- compatible(_, P).
valid_story(S, P) :- reasonable(S, P), has_fix(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("action", pid, p.id if p.id else pid))
        lines.append(asp.fact("warning", pid))
        lines.append(asp.fact("tag", pid, next(iter(p.tags)) if p.tags else "sound"))
        for z in sorted(p.zone):
            lines.append(asp.fact("zone", pid, z))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, c))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", t.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Reasonableness helpers
# ---------------------------------------------------------------------------

def problem_is_reasonable(setting: Setting, problem: Problem) -> bool:
    return "listen" in setting.affordances or "explore" in setting.affordances


def select_tool(problem: Problem) -> Optional[Tool]:
    for tool in TOOLS:
        if problem.keyword in tool.guards or "warning" in tool.guards or "mystery" in tool.guards:
            if problem.zone & tool.covers:
                return tool
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            if problem_is_reasonable(setting, problem) and select_tool(problem):
                combos.append((sid, pid))
    return combos


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def predict_problem(world: World, actor: Entity, problem: Problem) -> bool:
    sim = world.copy()
    _attempt(sim, sim.get(actor.id), problem, narrate=False)
    return bool(sim.facts.get("trouble"))


def _attempt(world: World, actor: Entity, problem: Problem, narrate: bool = True) -> None:
    world.zone = set(problem.zone)
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0) + 1
    actor.meters["risk"] = actor.meters.get("risk", 0) + 1
    world.facts["trouble"] = True
    if narrate:
        world.say(f"{problem.sound}! The {problem.name} answered with a warning hush.")


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.meters.get('age_word', 'teenage')} {hero.type} who liked quiet places after dark."
    )


def setting_line(world: World, problem: Problem) -> None:
    place = world.setting.place
    world.say(
        f"At {place}, the air felt still, and something in the walls made a little {problem.sound}."
    )


def caution(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["unease"] = hero.memes.get("unease", 0) + 1
    world.say(
        f"{hero.id} heard the sound and paused. It felt {problem.clue}, like the room was trying to give a warning."
    )


def ask_and_risk(world: World, hero: Entity, problem: Problem) -> None:
    world.say(
        f"{hero.id} wanted to {problem.verb}, but that could mean {problem.risk}."
    )


def solve(world: World, hero: Entity, problem: Problem, tool: Tool) -> None:
    hero.memes["resolve"] = hero.memes.get("resolve", 0) + 1
    world.say(
        f"Then {hero.id} found {tool.phrase}. {tool.prep.capitalize()}, {hero.id} listened again."
    )
    world.say(
        f"This time the sound made sense. {problem.fix.capitalize()}, and the spooky little trouble stopped."
    )
    world.say(
        f"By the end, {hero.id} was {problem.verb.replace('step onto ', 'stepping onto ').replace('touch ', 'touching ').replace('look into ', 'looking into ')} safely, with the periwinkle glow of {tool.label} making the dark feel less lonely."
    )


def tell(setting: Setting, problem: Problem, hero_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type="teen",
            meters={"age_word": 0},
            memes={},
        )
    )
    hero.meters["age_word"] = 0
    world.facts["hero"] = hero
    world.facts["problem"] = problem
    world.facts["setting"] = setting

    intro(world, hero)
    world.para()
    setting_line(world, problem)
    caution(world, hero, problem)
    ask_and_risk(world, hero, problem)

    world.para()
    tool = select_tool(problem)
    if tool is None:
        raise StoryError("No reasonable tool exists for this ghost-story problem.")
    solve(world, hero, problem, tool)

    world.facts["tool"] = tool
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    return [
        f'Write a short ghost story for a child featuring a teenage character, a periwinkle clue, and the sound "{problem.sound}".',
        f"Tell a cautious story where {hero.id} hears a warning in {world.setting.place} and solves the problem instead of rushing ahead.",
        f"Write a small spooky story with a gentle ending, using the word 'periwinkle' and a useful sound effect like '{problem.sound}'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    problem = world.facts["problem"]
    tool = world.facts["tool"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a teenage character who listens carefully in the dark and solves a small spooky problem.",
        ),
        QAItem(
            question=f"What warning sound did the story mention?",
            answer=f"The story mentioned {problem.sound}, which worked like a cautionary sound effect and helped {hero.id} notice trouble.",
        ),
        QAItem(
            question=f"What helped {hero.id} solve the problem?",
            answer=f"{tool.phrase} helped {hero.id} solve the problem by making it easier to see, listen, and choose the safe next step.",
        ),
        QAItem(
            question=f"Why did {hero.id} stop and think before moving ahead?",
            answer=f"{hero.id} stopped because the sound felt like a warning, and rushing could have made the problem worse.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and paying attention so you do not make a mistake or get hurt.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that help a reader imagine a sound, like creak, tap, whisper, or boom.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing what is wrong, thinking about choices, and picking a smart way to fix it.",
        ),
        QAItem(
            question="What is periwinkle?",
            answer="Periwinkle is a soft blue-purple color, a little like twilight sky or a pale flower petal.",
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


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python only:", sorted(py - clingo))
    print("clingo only:", sorted(clingo - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
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
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny ghost story world with cautionary sound effects and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name", choices=NAMES)
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
    if args.setting and args.problem:
        if (args.setting, args.problem) not in valid_combos():
            raise StoryError("That setting/problem pair does not make a reasonable ghost story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, problem = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, problem=problem, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], params.name, params.trait)
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


CURATED = [
    StoryParams(setting="old_hall", problem="creak", name="Mina", trait="careful"),
    StoryParams(setting="attic", problem="whisper", name="Theo", trait="curious"),
    StoryParams(setting="porch", problem="rattle", name="Nora", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
