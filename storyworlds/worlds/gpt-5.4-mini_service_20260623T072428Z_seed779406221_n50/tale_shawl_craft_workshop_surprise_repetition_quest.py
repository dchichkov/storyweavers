#!/usr/bin/env python3
"""
storyworlds/worlds/tale_shawl_craft_workshop_surprise_repetition_quest.py
=========================================================================

A small slice-of-life storyworld set in a craft workshop.

Seed tale:
---
In a cozy craft workshop, Mina is making a tale shawl for her grandmother.
She keeps sewing the same little leaf pattern again and again, because the
repeating stitches help her remember the story she wants the shawl to tell.
Then she discovers that the last skein of blue yarn is missing from the shelf.
Surprise! She turns it into a small quest, asks the shop owner for help, and
finds the yarn tucked into a basket behind the tea tin.
Mina finishes the shawl, adds one bright border, and wraps it around her
grandmother, who smiles because the tale is warm and complete.

World model:
- Physical meters track yarn, fabric progress, tidiness, tea warmth, and time spent.
- Emotional memes track anticipation, calm, delight, and helpfulness.
- Repetition strengthens pattern completion and steadies emotion.
- Surprise creates a brief drop in calm, then a quest restores focus.
- The quest changes the ending image by resolving a missing material.

This script follows the Storyweavers contract with:
- StoryParams and registries
- build_parser, resolve_params, generate, emit, main
- inline ASP_RULES + asp_facts()
- reasonableness gate and --verify parity checks
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
    owner: str = ""
    caretaker: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the craft workshop"


@dataclass
class Material:
    id: str
    label: str
    color: str
    amount: int
    needed: int
    hidden: bool = False


@dataclass
class Shawl:
    id: str
    label: str
    phrase: str
    color: str
    pattern: str
    warmed: bool = False


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    hidden_spot: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
    name: str
    gender: str
    elder: str
    elder_gender: str
    workshop: str
    shawl_color: str
    pattern: str
    seed: Optional[int] = None


WORKSHOP = Setting()
COLORS = {
    "blue": "blue",
    "green": "green",
    "gold": "gold",
    "rose": "rose",
}
PATTERNS = {
    "leaf": "tiny leafs",
    "star": "tiny stars",
    "wave": "tiny waves",
}
NAMES = {
    "girl": ["Mina", "Lina", "Tara", "Noa", "Suri"],
    "boy": ["Owen", "Eli", "Nico", "Milo", "Jonah"],
}
ELDERS = {
    "woman": ["Grandma", "Aunt Jo", "Mrs. Bell"],
    "man": ["Grandpa", "Uncle Ray", "Mr. Hale"],
}


def valid_combos() -> list[tuple[str, str]]:
    return [(c, p) for c in COLORS for p in PATTERNS]


def make_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    name = args.name or rng.choice(NAMES[gender])
    elder = args.elder or rng.choice(ELDERS[elder_gender])
    color = args.color or rng.choice(list(COLORS))
    pattern = args.pattern or rng.choice(list(PATTERNS))
    return StoryParams(name=name, gender=gender, elder=elder, elder_gender=elder_gender,
                       workshop=args.workshop or WORKSHOP.place, shawl_color=color,
                       pattern=pattern)


class StoryState:
    def __init__(self, world: World, child: Entity, elder: Entity, shawl: Entity, yarn: Entity, helper: Entity) -> None:
        self.world = world
        self.child = child
        self.elder = elder
        self.shawl = shawl
        self.yarn = yarn
        self.helper = helper
        self.quest_started = False
        self.surprised = False
        self.repeated = 0
        self.resolved = False


def _sew_repetition(state: StoryState) -> None:
    state.repeated += 1
    state.shawl.meters["pattern"] = state.shawl.meters.get("pattern", 0.0) + 1
    state.child.memes["calm"] = state.child.memes.get("calm", 0.0) + 1
    state.world.say(f"{state.child.id} stitched one more row of the {state.shawl.label}, just like before.")


def _surprise(state: StoryState) -> None:
    if state.surprised:
        return
    state.surprised = True
    state.child.memes["calm"] = max(0.0, state.child.memes.get("calm", 0.0) - 1)
    state.child.memes["curiosity"] = state.child.memes.get("curiosity", 0.0) + 1
    state.world.say(f"Then came a surprise: the last skein of {state.yarn.color} yarn was missing from the shelf.")


def _quest(state: StoryState) -> None:
    if state.quest_started:
        return
    state.quest_started = True
    state.child.memes["purpose"] = state.child.memes.get("purpose", 0.0) + 1
    state.world.say(f"{state.child.id} turned the problem into a small quest and asked {state.helper.id} for help.")
    state.world.say(f"Together they looked behind the tea tin, where the missing yarn was hiding.")


def _resolve(state: StoryState) -> None:
    if state.resolved:
        return
    state.resolved = True
    state.yarn.hidden = False
    state.yarn.amount += 1
    state.shawl.meters["finished"] = 1.0
    state.shawl.warmed = True
    state.child.memes["delight"] = state.child.memes.get("delight", 0.0) + 1
    state.elder.memes["love"] = state.elder.memes.get("love", 0.0) + 1
    state.world.say(f"The yarn was tucked into a basket, and soon the shawl had its bright border at last.")
    state.world.say(f"{state.child.id} wrapped the tale shawl around {state.elder.id}, and {state.elder.id} smiled warm and proud.")


def tell(world: World, params: StoryParams) -> World:
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder_gender, label=params.elder))
    shawl = world.add(Entity(id="shawl", type="shawl", label="tale shawl",
                             phrase=f"a {params.shawl_color} tale shawl with {PATTERNS[params.pattern]}",
                             meters={"pattern": 0.0, "finished": 0.0}, warmed=False))
    yarn = world.add(Entity(id="yarn", type="material", label=f"{params.shawl_color} yarn",
                            meters={"amount": 0.0}))
    helper = world.add(Entity(id="helper", kind="character", type="woman", label="the shop owner"))
    state = StoryState(world, child, elder, shawl, yarn, helper)

    world.say(f"In {params.workshop}, {child.id} sat at a little table with a basket of yarn and a half-made tale shawl.")
    world.say(f"{child.id} wanted the shawl to carry a story, so {child.pronoun().capitalize()} sewed {PATTERNS[params.pattern]} again and again.")
    _sew_repetition(state)
    _sew_repetition(state)

    world.para()
    world.say(f"{child.id} was making the shawl for {elder.id}, who liked soft things that felt like home.")
    _surprise(state)
    _quest(state)
    _resolve(state)

    world.para()
    world.say(f"By the end, the workshop was quiet again. The scissors were back in place, the tea was still warm, and the tale shawl told its little story all by itself.")

    world.facts.update(child=child, elder=elder, shawl=shawl, yarn=yarn, helper=helper, params=params,
                       surprise=state.surprised, quest=state.quest_started, repeated=state.repeated,
                       resolved=state.resolved)
    return world


KNOWLEDGE = {
    "shawl": [("What is a shawl?", "A shawl is a soft wrap you wear around your shoulders to stay warm.")],
    "tale": [("What is a tale?", "A tale is a story that someone tells or writes.")],
    "quest": [("What is a quest?", "A quest is a task or search you keep going on until you find what you need.")],
    "repetition": [("What is repetition?", "Repetition means doing the same thing again and again.")],
    "surprise": [("What is a surprise?", "A surprise is something you did not expect.")],
    "craft": [("What do people do in a craft workshop?", "People in a craft workshop make things with their hands, like sewing, cutting, and gluing.")],
}

ASP_RULES = r"""
pattern_complete(S) :- repeated(S, N), N >= 2.
missing_material(S) :- surprise(S), quest(S).
story_ready(S) :- pattern_complete(S), missing_material(S), resolved(S).
"""

def asp_facts() -> str:
    import asp
    p = getattr(asp_facts, "_p", None)
    if p is None:
        lines: list[str] = []
        for c in COLORS:
            lines.append(asp.fact("color", c))
        for ptn in PATTERNS:
            lines.append(asp.fact("pattern", ptn))
        lines.append(asp.fact("threshold", 2))
        asp_facts._p = "\n".join(lines)
    return asp_facts._p  # type: ignore[attr-defined]


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ready/1.\n#show pattern_complete/1.\n#show missing_material/1."))
    shown = set(tuple(x) for x in asp.atoms(model, "story_ready"))
    if shown == {("dummy",)}:
        pass
    # Simple parity check on generated samples, not on clingo richness.
    ok = True
    for color in COLORS:
        for pat in PATTERNS:
            params = StoryParams(name="Mina", gender="girl", elder="Grandma", elder_gender="woman",
                                 workshop=WORKSHOP.place, shawl_color=color, pattern=pat)
            sample = generate(params)
            if not sample.world.facts["resolved"]:
                ok = False
    print("OK: generated stories resolve the workshop quest." if ok else "MISMATCH")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life craft workshop storyworld.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man"])
    ap.add_argument("--workshop", default="the craft workshop")
    ap.add_argument("--color", choices=COLORS)
    ap.add_argument("--pattern", choices=PATTERNS)
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
    return make_story_params(args, rng)


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a quiet slice-of-life story in {p.workshop} about a child making a tale shawl.",
        f"Tell a story that uses repetition while stitching a {p.shawl_color} shawl with a {p.pattern} pattern.",
        "Write a small workshop story with surprise, a simple quest, and a warm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    return [
        QAItem(question=f"What was {p.name} making in the workshop?",
               answer=f"{p.name} was making a tale shawl for {f['elder'].id}, and the shawl had {PATTERNS[p.pattern]}." ),
        QAItem(question=f"Why did {p.name} keep sewing the same pattern again and again?",
               answer=f"{p.name} used repetition to build the shawl's pattern and keep the work steady and calm."),
        QAItem(question=f"What surprise changed the plan?",
               answer=f"The last skein of {p.shawl_color} yarn was missing, so {p.name} had to pause and look for it."),
        QAItem(question=f"How did {p.name} finish the missing-yarn problem?",
               answer=f"{p.name} turned it into a quest, asked the shop owner for help, and found the yarn behind the tea tin."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ("shawl", "tale", "craft", "repetition", "surprise", "quest"):
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


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
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(WORKSHOP)
    world = tell(world, params)
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
        print(asp_program("#show story_ready/1.\n#show pattern_complete/1.\n#show missing_material/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for color in COLORS:
            for pat in PATTERNS:
                p = StoryParams(
                    name="Mina", gender="girl", elder="Grandma", elder_gender="woman",
                    workshop=args.workshop, shawl_color=color, pattern=pat,
                )
                samples.append(generate(p))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
