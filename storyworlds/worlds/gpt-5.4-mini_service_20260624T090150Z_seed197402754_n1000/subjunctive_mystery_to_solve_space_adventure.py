#!/usr/bin/env python3
"""
A tiny space-adventure storyworld with a mystery to solve.

Premise:
A child astronaut hears a strange clue in a starship or moon-base setting.
They wonder what caused the mystery, test a few possibilities, and discover
the true cause with help from a tool, a map, or a friendly robot.

The world is intentionally small and state-driven:
- physical meters: fuel, damage, signal, dust, curiosity, relief
- emotional memes: worry, hope, bravery, surprise, joy

The model can tell short complete stories with a beginning, a tense middle,
and a resolution image that proves what changed.
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
# Core data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["fuel", "damage", "signal", "dust", "curiosity", "relief"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "hope", "bravery", "surprise", "joy"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def name(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    kind: str  # "ship" | "moonbase" | "station" | "lab"
    clue_source: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    wrong_guess: str
    cause: str
    fix: str
    reveal: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
    solves: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "moonbase": Setting(
        place="the moon base",
        kind="moonbase",
        clue_source="the observation dome",
        affords={"scan", "repair", "follow-signal"},
    ),
    "starship": Setting(
        place="the starship",
        kind="ship",
        clue_source="the engine hall",
        affords={"scan", "repair", "follow-signal"},
    ),
    "station": Setting(
        place="the space station",
        kind="station",
        clue_source="the airlock corridor",
        affords={"scan", "repair", "follow-signal"},
    ),
    "lab": Setting(
        place="the tiny space lab",
        kind="lab",
        clue_source="the glass window",
        affords={"scan", "repair"},
    ),
}

MYSTERIES = {
    "flicker": Mystery(
        id="flicker",
        clue="a blinking blue light",
        wrong_guess="a broken star",
        cause="a loose wire behind the panel",
        fix="tighten the wire and reset the panel",
        reveal="the blue light became steady and calm",
    ),
    "missing-beep": Mystery(
        id="missing-beep",
        clue="a beep that had gone missing",
        wrong_guess="a sleepy robot",
        cause="a dusty speaker inside the console",
        fix="brush away the dust and open the speaker cover",
        reveal="the beep came back bright and clear",
    ),
    "drift": Mystery(
        id="drift",
        clue="a slow drift of map lines",
        wrong_guess="a sneaky moon ghost",
        cause="a tiny magnet near the chart",
        fix="move the magnet away and trace the lines again",
        reveal="the map lines stopped sliding and pointed true",
    ),
}

TOOLS = {
    "scanner": Tool(
        id="scanner",
        label="a small scanner",
        phrase="a little scanner with a round light",
        helps="look for hidden clues",
        solves="scan",
    ),
    "lamp": Tool(
        id="lamp",
        label="a bright lamp",
        phrase="a bright lamp that could shine into dark corners",
        helps="see behind panels",
        solves="repair",
    ),
    "brush": Tool(
        id="brush",
        label="a soft brush",
        phrase="a soft brush for dust and tiny crumbs",
        helps="clear away dust",
        solves="repair",
    ),
}

NAMES = ["Mina", "Toby", "Rin", "Kai", "Luna", "Noah", "Ivy", "Zed"]
TYPES = ["girl", "boy"]
PARENTS = ["captain", "pilot", "engineer", "helper"]
TRAITS = ["curious", "brave", "careful", "bright", "subjunctive"]


# ---------------------------------------------------------------------------
# ASP twin / reasonableness gate
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(moonbase). setting(starship). setting(station). setting(lab).

mystery(flicker). mystery(missing_beep). mystery(drift).

tool(scanner). tool(lamp). tool(brush).

solves(scanner, scan).
solves(lamp, repair).
solves(brush, repair).

affords(moonbase, scan). affords(moonbase, repair). affords(moonbase, follow_signal).
affords(starship, scan). affords(starship, repair). affords(starship, follow_signal).
affords(station, scan). affords(station, repair). affords(station, follow_signal).
affords(lab, scan). affords(lab, repair).

compatible(S, M, T) :- affords(S, solve_mode(M)), solves(T, solve_mode(M)).
solve_mode(flicker, repair).
solve_mode(missing_beep, repair).
solve_mode(drift, scan).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for a in sorted(SETTINGS[sid].affords):
            lines.append(asp.fact("affords", sid, a))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("solves", tid, tool.solves))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatible() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    mystery: str
    tool: str
    name: str
    role: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for t, tool in TOOLS.items():
                if (
                    (m == "flicker" and tool.solves == "repair")
                    or (m == "missing-beep" and tool.solves == "repair")
                    or (m == "drift" and tool.solves == "scan")
                ):
                    if tool.solves in SETTINGS[s].affords:
                        combos.append((s, m, t))
    return combos


class StoryWorld:
    def __init__(self, setting: Setting, mystery: Mystery, tool: Tool, hero: Entity, parent: Entity) -> None:
        self.setting = setting
        self.mystery = mystery
        self.tool = tool
        self.hero = hero
        self.parent = parent
        self.fixed = False
        self.clue_found = False
        self.wrong_guess_made = False
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def introduce(world: StoryWorld) -> None:
    world.say(
        f"{world.hero.name} was a little {world.hero.type} on {world.setting.place}, "
        f"and {world.hero.pronoun('subject')} loved quiet space days full of questions."
    )
    world.say(
        f"Near {world.setting.clue_source}, {world.hero.name} noticed {world.mystery.clue}."
    )
    world.hero.memes["curiosity"] += 1
    world.hero.memes["hope"] += 1


def wonder(world: StoryWorld) -> None:
    world.para()
    world.say(
        f"{world.hero.name} wondered what could make it happen. "
        f"If the clue was real, then something hidden must be waiting nearby."
    )
    world.hero.memes["worry"] += 1
    world.hero.memes["bravery"] += 1


def wrong_guess(world: StoryWorld) -> None:
    world.wrong_guess_made = True
    world.para()
    world.say(
        f"{world.hero.name} peered at the dark corner and thought it might be "
        f"{world.mystery.wrong_guess}, but that guess did not fit the whole clue."
    )
    world.hero.memes["surprise"] += 1


def use_tool(world: StoryWorld) -> None:
    world.para()
    if world.tool.solves == "scan":
        world.say(
            f"{world.hero.name} held up {world.tool.phrase} and scanned the walls. "
            f"The light traced a hidden pattern behind the map."
        )
    else:
        world.say(
            f"{world.hero.name} used {world.tool.phrase} to look behind the panel. "
            f"The small beam made the dust shine like tiny stars."
        )
    world.clue_found = True
    world.hero.memes["hope"] += 1
    world.hero.meters["signal"] += 1


def reveal(world: StoryWorld) -> None:
    world.para()
    world.say(
        f"At last, {world.hero.name} found the true cause: {world.mystery.cause}."
    )
    world.say(
        f"If {world.hero.pronoun('subject')} had not checked carefully, the clue might "
        f"have stayed a mystery forever."
    )


def fix_it(world: StoryWorld) -> None:
    world.para()
    world.say(
        f"Together with {world.parent.name}, {world.hero.name} did the right thing: "
        f"{world.mystery.fix}."
    )
    world.fixed = True
    world.hero.memes["joy"] += 1
    world.hero.memes["relief"] += 1
    world.hero.memes["worry"] = 0.0
    world.hero.meters["dust"] = 0.0
    world.hero.meters["damage"] = 0.0


def ending(world: StoryWorld) -> None:
    world.say(
        f"After that, {world.mystery.reveal}, and the room felt bright again."
    )
    world.say(
        f"{world.hero.name} smiled at {world.parent.name}, knowing that a careful guess "
        f"and a brave check can solve a space mystery."
    )


def tell(setting: Setting, mystery: Mystery, tool: Tool, hero_name: str, hero_type: str,
         parent_role: str, trait: str) -> StoryWorld:
    hero = Entity(id=hero_name, kind="character", type=hero_type, label=hero_name, memes={"curiosity": 1.0, "hope": 1.0, "worry": 0.0, "bravery": 1.0, "surprise": 0.0, "joy": 0.0, "relief": 0.0}, meters={"fuel": 0.0, "damage": 0.0, "signal": 0.0, "dust": 0.0, "curiosity": 1.0, "relief": 0.0})
    parent = Entity(id=parent_role, kind="character", type=parent_role, label=f"the {parent_role}")
    world = StoryWorld(setting, mystery, tool, hero, parent)
    world.facts = {"setting": setting, "mystery": mystery, "tool": tool, "hero": hero, "parent": parent}
    introduce(world)
    wonder(world)
    wrong_guess(world)
    use_tool(world)
    reveal(world)
    fix_it(world)
    ending(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: StoryWorld) -> list[str]:
    return [
        f'Write a short space-adventure story for a young child that includes the word "subjunctive" and a mystery to solve.',
        f"Tell a gentle story where {world.hero.name}, a {world.hero.type}, notices {world.mystery.clue} at {world.setting.place} and learns what caused it.",
        f"Write a simple mystery story set on a spaceship or moon base, where a brave child uses {world.tool.label} to solve the problem.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    hero = world.hero
    parent = world.parent
    m = world.mystery
    s = world.setting
    t = world.tool
    return [
        QAItem(
            question=f"What mystery did {hero.name} notice at {s.place}?",
            answer=f"{hero.name} noticed {m.clue} near {s.clue_source}, and that started the mystery.",
        ),
        QAItem(
            question=f"What did {hero.name} first think might be causing the clue?",
            answer=f"{hero.name} first thought it might be {m.wrong_guess}, but that guess did not fit.",
        ),
        QAItem(
            question=f"What tool helped {hero.name} solve the mystery?",
            answer=f"{t.phrase} helped {hero.name} look closely and find the real cause.",
        ),
        QAItem(
            question=f"What was the real cause of the mystery?",
            answer=f"The real cause was {m.cause}.",
        ),
        QAItem(
            question=f"How did the story end after the problem was fixed?",
            answer=f"After {m.fix}, {m.reveal}, and {hero.name} felt happy and relieved with {parent.name}.",
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that you do not understand at first, so you look for clues to find the answer.",
        ),
        QAItem(
            question="What does a scanner do?",
            answer="A scanner helps you look for hidden clues by using a light or a sensor to check carefully.",
        ),
        QAItem(
            question="What does subjunctive mean in a sentence?",
            answer="Subjunctive is a grammar style used for wishes, guesses, or things that are not certain, like saying what might happen if something were true.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_compatible())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} compatible combos.")
        return 0
    print("Mismatch between ASP and Python:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=TYPES)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.setting or args.mystery or args.tool:
        combos = [
            c for c in combos
            if (args.setting is None or c[0] == args.setting)
            and (args.mystery is None or c[1] == args.mystery)
            and (args.tool is None or c[2] == args.tool)
        ]
    if not combos:
        raise StoryError("No valid space-mystery combination matches those options.")
    setting, mystery, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(TYPES)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, mystery=mystery, tool=tool, name=name, role=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        MYSTERIES[params.mystery],
        TOOLS[params.tool],
        params.name,
        params.role,
        params.parent,
        params.trait,
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
        print()
        print("--- trace ---")
        for k, v in sample.world.facts.items():
            if isinstance(v, (Setting, Mystery, Tool, Entity)):
                print(f"{k}: {v}")
            else:
                print(f"{k}: {v}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_compatible()
        for row in combos:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("moonbase", "flicker", "lamp", "Mina", "girl", "engineer", "curious"),
            StoryParams("starship", "missing-beep", "brush", "Toby", "boy", "pilot", "brave"),
            StoryParams("station", "drift", "scanner", "Luna", "girl", "captain", "careful"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
