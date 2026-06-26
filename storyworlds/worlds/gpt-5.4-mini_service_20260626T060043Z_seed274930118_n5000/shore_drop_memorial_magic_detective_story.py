#!/usr/bin/env python3
"""
storyworlds/worlds/shore_drop_memorial_magic_detective_story.py
===============================================================

A small detective storyworld with a magical shoreline mystery.

Premise:
- A child detective investigates a strange drop found near a memorial on the shore.
- Magic is real in this world, but it behaves like a concrete force with rules.
- The story turns when the detective follows clues, tests a spell, and learns
  whether the drop is a message, a trick, or a memory.

The world is built to produce one complete, child-facing detective story with a
clear clue, a middle turn, and a resolution image that proves what changed.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    touched_by_magic: bool = False
    suspicious: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    shore_name: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    place: str
    magic_kind: str
    reveal: str
    fit: str


@dataclass
class MagicTool:
    id: str
    label: str
    focus: str
    calm: str
    truth: str
    requires: str


@dataclass
class StoryParams:
    setting: str
    clue: str
    tool: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "shore": Setting(place="the shore", shore_name="the shoreline", affords={"inspect", "cast"}),
    "pier": Setting(place="the old pier", shore_name="the water below the pier", affords={"inspect", "cast"}),
    "cove": Setting(place="the little cove", shore_name="the smooth shore", affords={"inspect", "cast"}),
}

CLUES = {
    "drop": Clue(
        id="drop",
        label="a silver drop",
        place="near the memorial stone",
        magic_kind="glow",
        reveal="the drop was a tiny spell bead that answered to memory",
        fit="it shimmered when the detective asked about the memorial",
    ),
    "shell": Clue(
        id="shell",
        label="a curved shell",
        place="at the waterline",
        magic_kind="whisper",
        reveal="the shell held a hidden message in a spell-soft voice",
        fit="it hummed when held up to the breeze",
    ),
    "ribbon": Clue(
        id="ribbon",
        label="a blue ribbon",
        place="tied to the memorial railing",
        magic_kind="spark",
        reveal="the ribbon had been enchanted to point toward whoever left it",
        fit="it pulled gently toward the sea path",
    ),
}

TOOLS = {
    "lantern": MagicTool(
        id="lantern",
        label="a small magic lantern",
        focus="shine a warm beam on clues",
        calm="the light steadied the detective's thoughts",
        truth="the lantern could show which clue had been touched by a spell",
        requires="light",
    ),
    "glass": MagicTool(
        id="glass",
        label="a round magic looking glass",
        focus="see what ordinary eyes missed",
        calm="the glass made tiny details stand out",
        truth="the glass could reveal the shape of a hidden enchantment",
        requires="seeing",
    ),
    "chalk": MagicTool(
        id="chalk",
        label="a piece of chalky charm",
        focus="draw a safe circle for questions",
        calm="the circle kept nervous magic from scattering",
        truth="the chalk could wake a memory from a careful place",
        requires="drawing",
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ivy", "Zoe", "Ava", "Maya"]
BOY_NAMES = ["Eli", "Tobin", "Noah", "Finn", "Leo", "Sam", "Theo"]
TRAITS = ["careful", "curious", "brave", "quiet", "patient", "sharp-eyed"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


def determine_scene(setting: Setting, clue: Clue) -> bool:
    return clue.place in {"near the memorial stone", "at the waterline", "tied to the memorial railing"}


def valid_combo(setting: Setting, clue: Clue, tool: MagicTool) -> bool:
    if not determine_scene(setting, clue):
        return False
    if clue.id == "drop" and tool.requires not in {"light", "seeing"}:
        return False
    if clue.id == "shell" and tool.requires not in {"seeing", "drawing"}:
        return False
    if clue.id == "ribbon" and tool.requires not in {"light", "drawing"}:
        return False
    return True


def select_valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for cid, c in CLUES.items():
            for tid, t in TOOLS.items():
                if valid_combo(s, c, t):
                    combos.append((sid, cid, tid))
    return combos


def reasonableness_gate(setting: Setting, clue: Clue, tool: MagicTool) -> None:
    if not valid_combo(setting, clue, tool):
        raise StoryError(
            f"No reasonable detective story fits {setting.place}, {clue.label}, and {tool.label}."
        )


def tell(setting: Setting, clue: Clue, tool: MagicTool, hero_name: str, gender: str, parent: str, trait: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=hero_name, kind="character", type=gender, label=hero_name))
    grownup = world.add(Entity(id="Parent", kind="character", type=parent, label=f"the {parent}"))
    mystery = world.add(Entity(
        id="clue",
        type="thing",
        label=clue.label,
        phrase=clue.label,
        suspicious=True,
    ))
    magic = world.add(Entity(
        id=tool.id,
        type="thing",
        label=tool.label,
        phrase=tool.label,
        touched_by_magic=True,
    ))
    world.facts.update(hero=detective, parent=grownup, clue=mystery, tool=magic, clue_cfg=clue, tool_cfg=tool)

    world.say(f"{hero_name} was a {trait} little detective who loved solving mysteries by the shore.")
    world.say(f"One day, {hero_name} went to {setting.place} with {grownup.label} and noticed {clue.label} {clue.place}.")
    world.say(f"{hero_name} held up {tool.label}; {tool.focus}, and {tool.calm}.")

    world.say(f"The clue looked odd, because {clue.fit}.")
    world.say(f"{hero_name} asked a careful question, and the magic answered with a tiny sign.")
    if clue.id == "drop":
        world.say("The silver drop glowed brighter, as if it remembered something kind.")
    elif clue.id == "shell":
        world.say("The shell gave a soft whisper, like a secret tucked in sea foam.")
    else:
        world.say("The blue ribbon tugged once, pointing the detective toward the water path.")

    world.say(f"Then {hero_name} understood that {clue.reveal}.")
    world.say(
        f"{hero_name} showed {grownup.label} the answer, and together they placed the clue back where it belonged."
    )
    world.say(
        f"By sunset, the shore felt peaceful again, and {hero_name} walked home with a proud smile and a solved mystery."
    )
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue_cfg"]
    tool = f["tool_cfg"]
    return [
        f'Write a short detective story for a young child about {hero.label} finding {clue.label} by the shore.',
        f"Tell a magical mystery where a child detective uses {tool.label} to understand a clue near a memorial.",
        f'Write a simple story with the words "shore", "drop", and "memorial" that ends with a solved clue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    clue = f["clue_cfg"]
    tool = f["tool_cfg"]
    setting = world.setting
    return [
        QAItem(
            question=f"Who solved the mystery at {setting.place}?",
            answer=f"{hero.label} solved the mystery with {parent.label} nearby.",
        ),
        QAItem(
            question=f"What clue did {hero.label} find near the memorial?",
            answer=f"{hero.label} found {clue.label} near the memorial, and it turned out to be a magical clue.",
        ),
        QAItem(
            question=f"What did {hero.label} use to study the clue?",
            answer=f"{hero.label} used {tool.label} to study the clue and notice the magic hiding inside it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shore?",
            answer="A shore is the land next to a sea, lake, or river.",
        ),
        QAItem(
            question="What is a memorial?",
            answer="A memorial is a special place or object that helps people remember someone or something important.",
        ),
        QAItem(
            question="What can magic do in a story?",
            answer="Magic can make strange lights, hidden messages, or surprising changes happen in a story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.touched_by_magic:
            bits.append("magic=True")
        if e.suspicious:
            bits.append("suspicious=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    return select_valid_combos()


ASP_RULES = r"""
setting(S) :- setting_fact(S).
clue(C) :- clue_fact(C).
tool(T) :- tool_fact(T).

good_combo(S,C,T) :- scene_ok(S,C), tool_ok(C,T).

scene_ok(shore, drop).
scene_ok(shore, shell).
scene_ok(shore, ribbon).
scene_ok(pier, drop).
scene_ok(pier, shell).
scene_ok(pier, ribbon).
scene_ok(cove, drop).
scene_ok(cove, shell).
scene_ok(cove, ribbon).

tool_ok(drop, lantern).
tool_ok(drop, glass).
tool_ok(shell, glass).
tool_ok(shell, chalk).
tool_ok(ribbon, lantern).
tool_ok(ribbon, chalk).

#show good_combo/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_fact", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue_fact", cid))
    for tid in TOOLS:
        lines.append(asp.fact("tool_fact", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_combo/3."))
    return sorted(set(asp.atoms(model, "good_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Magical detective storyworld set by the shore.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
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
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.clue is None or c[1] == args.clue)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not filtered:
        raise StoryError("No valid magical detective story matches the given options.")
    setting, clue, tool = rng.choice(sorted(filtered))
    clue_cfg = CLUES[clue]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, clue=clue, tool=tool, name=name, gender=gender, parent=parent, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CLUES[params.clue],
        TOOLS[params.tool],
        params.name,
        params.gender,
        params.parent,
        random.choice(TRAITS),
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


CURATED = [
    StoryParams(setting="shore", clue="drop", tool="lantern", name="Mina", gender="girl", parent="mother"),
    StoryParams(setting="pier", clue="shell", tool="glass", name="Eli", gender="boy", parent="father"),
    StoryParams(setting="cove", clue="ribbon", tool="chalk", name="Nora", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (setting, clue, tool) combos:\n")
        for t in triples:
            print("  ", t)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.clue} at {p.setting} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
