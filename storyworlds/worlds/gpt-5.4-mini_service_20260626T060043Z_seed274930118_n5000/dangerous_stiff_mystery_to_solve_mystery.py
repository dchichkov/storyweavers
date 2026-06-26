#!/usr/bin/env python3
"""
Standalone storyworld: a small Mystery-to-Solve domain with dangerous, stiff
obstacles, a careful clue trail, and a child-sized resolution.

The world is intentionally compact:
- a curious child,
- a worrying location,
- a missing object,
- a useful tool,
- and a reveal that changes the final state.

The story engine simulates suspicion, searching, discovery, and repair so the
prose is driven by world state rather than a fixed template.
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
    place: str = ""
    portable: bool = True
    fixed: bool = False
    locked: bool = False
    dangerous: bool = False
    stiff: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "mom", "woman", "sister"}
        masculine = {"boy", "father", "dad", "man", "brother"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    risk: str
    clue: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing: str
    missing_phrase: str
    hidden_in: str
    clue_noun: str
    clue_phrase: str
    danger: str
    solution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    solves: str
    safe_for: set[str] = field(default_factory=set)
    tells: str = ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


@dataclass
class StoryParams:
    setting: str
    mystery: str
    tool: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "attic": Setting(
        place="the attic",
        mood="dusty",
        risk="the floorboards were dangerous and the stairs were steep",
        clue="a line of dust",
        affords={"search", "listen", "unlock"},
    ),
    "cellar": Setting(
        place="the cellar",
        mood="cool",
        risk="the steps were dangerous and the room felt dark",
        clue="a wet footprint",
        affords={"search", "listen", "unlock"},
    ),
    "shed": Setting(
        place="the garden shed",
        mood="dim",
        risk="the shelf looked dangerous because it wobbled",
        clue="a bent nail",
        affords={"search", "listen", "unlock"},
    ),
}

MYSTERIES = {
    "music_box": Mystery(
        id="music_box",
        missing="music box",
        missing_phrase="a little silver music box",
        hidden_in="under a loose board",
        clue_noun="dust",
        clue_phrase="a neat trail of dust that pointed to one corner",
        danger="the old board could crack if they stepped too hard",
        solution="the missing music box was tucked under the board",
        tags={"music", "dust"},
    ),
    "key_ring": Mystery(
        id="key_ring",
        missing="key ring",
        missing_phrase="a brass key ring",
        hidden_in="behind a jar",
        clue_noun="footprint",
        clue_phrase="a small footprint near the shelf",
        danger="the jar shelf was dangerous because it shook when touched",
        solution="the missing key ring was behind the jar",
        tags={"keys", "footprint"},
    ),
    "lantern": Mystery(
        id="lantern",
        missing="lantern",
        missing_phrase="a tiny lantern with a red handle",
        hidden_in="inside an old box",
        clue_noun="scratch",
        clue_phrase="a scratch mark by the box lid",
        danger="the lid felt stiff and might pinch fingers",
        solution="the missing lantern was inside the old box",
        tags={"light", "scratch"},
    ),
}

TOOLS = {
    "oil": Tool(
        id="oil",
        label="a bottle of oil",
        phrase="a small bottle of oil",
        solves="stiff",
        safe_for={"stiff"},
        tells="The oil could loosen a stiff lock or lid.",
    ),
    "gloves": Tool(
        id="gloves",
        label="work gloves",
        phrase="a pair of work gloves",
        solves="dangerous",
        safe_for={"dangerous"},
        tells="The gloves could keep careful hands safe.",
    ),
    "lamp": Tool(
        id="lamp",
        label="a bright lamp",
        phrase="a bright little lamp",
        solves="dark",
        safe_for={"dark"},
        tells="The lamp could make the clues easier to see.",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella", "Maya"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Sam", "Noah", "Eli", "Max"]
TRAITS = ["curious", "careful", "brave", "patient", "sharp-eyed", "quiet"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, setting in SETTINGS.items():
        for m_id, mystery in MYSTERIES.items():
            if s_id in {"attic", "cellar", "shed"} and any(
                tool.solves in {"stiff", "dangerous", "dark"} for tool in TOOLS.values()
            ):
                for t_id, tool in TOOLS.items():
                    if (
                        (mystery.id == "lantern" and t_id == "lamp")
                        or (mystery.id == "music_box" and t_id == "oil")
                        or (mystery.id == "key_ring" and t_id in {"oil", "lamp"})
                    ):
                        combos.append((s_id, m_id, t_id))
    return combos


def _story_rule_search(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    mystery = world.facts["mystery"]
    if hero.memes.get("searching", 0) >= THRESHOLD and not world.facts.get("found"):
        clue = mystery.clue_phrase
        world.facts["noticed_clue"] = True
        out.append(f"{hero.id} spotted {clue}.")
    return out


def _story_rule_reveal(world: World) -> list[str]:
    out = []
    if world.facts.get("used_tool") and world.facts.get("noticed_clue") and not world.facts.get("found"):
        mystery = world.facts["mystery"]
        hero = world.get("hero")
        world.facts["found"] = True
        out.append(f"That was enough to reveal {mystery.solution}.")
        hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    return out


CAUSAL_RULES = [_story_rule_search, _story_rule_reveal]


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small mystery storyworld with dangerous, stiff clues."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.setting and args.mystery and args.tool:
        if (args.setting, args.mystery, args.tool) not in valid_combos():
            raise StoryError("That mystery and tool do not fit together in this setting.")
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("No valid story matches those choices.")
    setting, mystery, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, mystery=mystery, tool=tool, name=name, gender=gender, parent=parent, trait=trait)


def tell(setting: Setting, mystery: Mystery, tool: Tool, name: str, gender: str, parent: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=name))
    adult = world.add(Entity(id="adult", kind="character", type=parent, label=parent))
    missing = world.add(Entity(id="missing", type=mystery.missing, label=mystery.missing, phrase=mystery.missing_phrase, owner=name))
    tool_ent = world.add(Entity(id="tool", type=tool.id, label=tool.label, phrase=tool.phrase))
    world.facts.update(hero=hero, adult=adult, mystery=mystery, missing=missing, tool=tool, setting=setting)

    world.say(f"{name} was a {trait} little {gender} who loved solving puzzles.")
    world.say(f"One day, something important went missing: {mystery.missing_phrase}.")
    world.say(f"It made the room feel unsettled, because the place was {setting.mood} and {setting.risk}.")

    world.para()
    hero.memes["searching"] = 1
    world.say(f"{name} and {parent} went into {setting.place} to look for clues.")
    world.say(f"The first thing they noticed was {setting.clue}, and that felt like the start of a mystery.")
    world.say(f"{name} remembered that {mystery.danger}.")

    if tool.id == "lamp":
        world.say(f"So {name} held up {tool.phrase} to see better.")
    elif tool.id == "gloves":
        world.say(f"So {name} put on {tool.phrase} to stay safe.")
    else:
        world.say(f"So {name} reached for {tool.phrase} to help with the stiff parts.")

    world.facts["used_tool"] = True
    propagate(world, narrate=True)

    world.para()
    if mystery.id == "music_box":
        world.say(f"{name} found a stiff board and carefully lifted it with {tool.label}.")
    elif mystery.id == "key_ring":
        world.say(f"{name} noticed the shelf was dangerous, so they moved slowly and looked behind the jar.")
    else:
        world.say(f"{name} saw a stiff lid and used {tool.label} to open it without rushing.")

    propagate(world, narrate=True)

    world.para()
    if world.facts.get("found"):
        hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
        world.say(f"{name} smiled when the missing thing turned up at last.")
        world.say(f"{parent} praised {name} for being careful and paying attention to the clue.")
        world.say(f"In the end, the dangerous, stiff mystery was solved, and the room felt calm again.")
    else:
        world.say(f"{name} kept looking, but the mystery stayed unsolved for now.")
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        MYSTERIES[params.mystery],
        TOOLS[params.tool],
        params.name,
        params.gender,
        params.parent,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    return [
        f'Write a short mystery story for a young child about {hero.label} and a missing {mystery.missing}.',
        f"Tell a gentle detective story set in {f['setting'].place} where a dangerous, stiff problem becomes solvable with a helpful tool.",
        f'Write a simple mystery that includes the words "dangerous" and "stiff" and ends with the missing thing being found.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    tool = f["tool"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What was missing in {setting.place}?",
            answer=f"The missing thing was {mystery.missing_phrase}.",
        ),
        QAItem(
            question=f"Why did {hero.label} need {tool.label}?",
            answer=f"{hero.label} needed {tool.label} because the clue led to a stiff or dangerous part of the room, and the tool helped with that.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"It ended when {hero.label} found {mystery.solution}, and the room felt calm again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery = f["mystery"]
    tool = f["tool"]
    return [
        QAItem(
            question="What does stiff mean in this story world?",
            answer="Stiff means something is hard to move, hard to open, or hard to use because it has gotten stuck or old.",
        ),
        QAItem(
            question="Why can a place be dangerous in this kind of story?",
            answer="A place can be dangerous when the stairs, shelves, boards, or lids might hurt someone if they rush or touch them carelessly.",
        ),
        QAItem(
            question=f"What is {tool.label} for?",
            answer=tool.tells,
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        lines.append(f"{e.id}: {e.kind}/{e.type} " + " ".join(bits))
    lines.append(f"facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


CURATED = [
    StoryParams("attic", "music_box", "oil", "Mia", "girl", "mother", "curious"),
    StoryParams("cellar", "key_ring", "gloves", "Leo", "boy", "father", "careful"),
    StoryParams("shed", "lantern", "lamp", "Nora", "girl", "father", "sharp-eyed"),
]


ASP_RULES = r"""
% A mystery is compatible when the setting, mystery, and tool work together.
compatible(S, M, T) :- setting(S), mystery(M), tool(T), fits(S, M, T).

% The reveal is possible when the tool is actually suited to the mystery.
solvable(M, T) :- mystery(M), tool(T), fits(_, M, T).

% A story is valid when it is compatible and solvable.
valid_story(S, M, T) :- compatible(S, M, T), solvable(M, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for s, m, t in valid_combos():
        lines.append(asp.fact("fits", s, m, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for s, m, t in combos:
            print(f"  {s:8} {m:10} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.setting}/{p.mystery}/{p.tool}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
