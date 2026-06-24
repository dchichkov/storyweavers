#!/usr/bin/env python3
"""
A small comedy storyworld about a child, a scrap, a surprising dilating helper,
and a flashback that helps fix a transformation gone silly.

Seed idea:
---
A child finds a tiny scrap in a drawer and tries to use a curious dilating
machine. The scrap grows into a funny, wiggly thing, and a flashback reminds the
child how to guide the machine more carefully. In the end, the scrap becomes a
neat new useful object.

World idea:
- Physical state tracks size, mess, and completion.
- Emotional state tracks delight, surprise, worry, and embarrassment.
- A flashback can reveal a remembered mistake that explains the better choice.
- Comedy comes from exaggerated, harmless transformation and a cheerful fix.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford_flashback: bool = True


@dataclass
class Tool:
    id: str
    label: str
    verb: str
    result: str
    mess: str
    risk: str
    can_fix: bool = True


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    time: str = "now"

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

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.time = self.time
        return w


@dataclass
class StoryParams:
    place: str
    tool: str
    scrap: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "workshop": Setting(place="the workshop"),
    "kitchen_table": Setting(place="the kitchen table"),
    "garage": Setting(place="the garage"),
}

TOOLS = {
    "dilator": Tool(
        id="dilator",
        label="dilating gadget",
        verb="dilate",
        result="bloomed into a giant floppy shape",
        mess="wobbly",
        risk="too huge",
        can_fix=True,
    ),
    "stretcher": Tool(
        id="stretcher",
        label="stretching wand",
        verb="stretch",
        result="grew long and twisty",
        mess="crooked",
        risk="all tangled",
        can_fix=True,
    ),
}

SCRAPS = {
    "paper": {
        "label": "scrap of paper",
        "phrase": "a tiny scrap of lined paper",
        "type": "paper",
        "fragile": True,
    },
    "cloth": {
        "label": "scrap of cloth",
        "phrase": "a small scrap of bright cloth",
        "type": "cloth",
        "fragile": False,
    },
    "foil": {
        "label": "scrap of foil",
        "phrase": "a shiny scrap of foil",
        "type": "foil",
        "fragile": False,
    },
}

NAMES = {
    "girl": ["Mia", "Nora", "Lily", "Zoe", "Ava"],
    "boy": ["Ben", "Leo", "Max", "Theo", "Finn"],
}

HELPERS = ["grandpa", "aunt", "big sibling", "neighbor"]
TRAITS = ["cheerful", "curious", "silly", "bouncy", "brave"]


def flashback_text(scrap: Entity, tool: Tool) -> str:
    return (
        f"Flashback: {scrap.label} remembered the last time {tool.label} was used "
        f"too fast, and everything puffed up like a joke balloon."
    )


def reasonableness_gate(tool: Tool, scrap_key: str) -> bool:
    return tool.can_fix and scrap_key in SCRAPS


def select_combo(rng: random.Random, args: argparse.Namespace) -> tuple[str, str]:
    options = [(p, t) for p in SETTINGS for t in TOOLS]
    if args.place:
        options = [c for c in options if c[0] == args.place]
    if args.tool:
        options = [c for c in options if c[1] == args.tool]
    if not options:
        raise StoryError("No valid place/tool combination matches the given options.")
    return rng.choice(sorted(options))


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        memes={"delight": 0.0, "worry": 0.0, "embarrassment": 0.0, "joy": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type="helper",
        label=params.helper,
        memes={"delight": 0.0, "worry": 0.0, "joy": 0.0},
    ))
    scrap_cfg = SCRAPS[params.scrap]
    scrap = world.add(Entity(
        id="scrap",
        kind="thing",
        type=scrap_cfg["type"],
        label=scrap_cfg["label"],
        phrase=scrap_cfg["phrase"],
        owner=hero.id,
        meters={"size": 1.0, "completeness": 0.3},
        memes={"plain": 1.0},
    ))
    tool = TOOLS[params.tool]

    world.say(
        f"{hero.id} was a {rng_choice([t for t in TRAITS])} little {hero.type} who "
        f"found {scrap.phrase} on {world.setting.place}."
    )
    world.say(
        f"{hero.id} loved curious fixes, and {hero.pronoun('possessive')} "
        f"{helper.label} brought out a {tool.label} that could {tool.verb} things."
    )
    world.para()

    scrap.memes["hope"] = 1.0
    world.say(
        f"{hero.id} put {scrap.it()} under the {tool.label} and pressed the shiny button."
    )
    scrap.meters["size"] += 2.0
    scrap.meters["completeness"] += 0.2
    scrap.memes["wobbly"] = 1.0
    hero.memes["delight"] += 1.0
    world.say(
        f"With a soft pop, the scrap {tool.result}. {hero.id} blinked and then "
        f"laughed, because it looked funny enough to wear a hat."
    )

    world.para()
    world.say(flashback_text(scrap, tool))
    hero.memes["worry"] += 1.0
    world.say(
        f"{hero.id} giggled anyway, but {hero.pronoun('possessive')} {helper.label} "
        f"said that a slower round might make the trick neat instead of wiggly."
    )

    world.para()
    world.say(
        f"So {hero.id} turned the {tool.label} to gentle mode, held the scrap flat, "
        f"and tried again."
    )
    scrap.meters["size"] = 2.5
    scrap.meters["completeness"] = 1.0
    scrap.memes["wobbly"] = 0.0
    scrap.memes["pride"] = 1.0
    hero.memes["joy"] += 2.0
    hero.memes["worry"] = 0.0
    world.say(
        f"This time the scrap became a tidy new label, wide enough to read and "
        f"small enough to fit in {hero.id}'s hand."
    )
    world.say(
        f"{hero.id} grinned at the silly before-and-after, and {helper.label} "
        f"laughed so hard that the table shook a little."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        scrap=scrap,
        tool=tool,
        setting=world.setting,
        resolved=True,
        flashback=True,
    )
    return world


def rng_choice(seq):
    return random.choice(seq)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    tool = f["tool"]
    scrap = f["scrap"]
    return [
        f'Write a funny story for a young child about {hero.id}, a {tool.verb}-happy machine, and {scrap.label}.',
        f"Tell a comedy story in which a small scrap changes size, then a flashback helps the hero make the fix.",
        f'Write a simple tale that includes the words "dilate" and "scrap" and ends with a cheerful improvement.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    scrap = f["scrap"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What did {hero.id} find at {world.setting.place}?",
            answer=f"{hero.id} found {scrap.phrase} and decided to try a funny experiment with it.",
        ),
        QAItem(
            question=f"What happened when {hero.id} used the {tool.label} the first time?",
            answer=f"The scrap grew into a wobbly silly shape, which made {hero.id} laugh.",
        ),
        QAItem(
            question=f"What helped {hero.id} make the scrap better the second time?",
            answer=f"A flashback reminded {hero.id} to use the {tool.label} more gently, and {helper.label} helped too.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The scrap became a neat new useful thing, and everyone laughed at how silly the first try had been.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does dilate mean?",
            answer="To dilate means to make something wider or bigger.",
        ),
        QAItem(
            question="What is a scrap?",
            answer="A scrap is a small leftover piece, like a tiny bit of paper or cloth.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part that shows something from earlier, to help explain what is happening now.",
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
    out = ["--- world trace ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        s = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if s:
            bits.append(f"memes={s}")
        out.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
% A scrap is eligible for the comedy fix if it exists and the tool can help.
eligible_scrap(S) :- scrap(S).

% A tool is helpful if it can fix and the scrap is real.
can_transform(T,S) :- tool(T), eligible_scrap(S), fixable(T).

% The first pass makes the scrap wobbly.
wobbly_result(S) :- can_transform(T,S).

% The flashback suggests a second, gentler pass.
safe_second_pass(S) :- flashback(S), eligible_scrap(S).

% The final story is valid when the scrap can be transformed and the flashback
% is present to justify the improvement.
valid_story(P,T,S) :- place(P), tool(T), scrap(S), can_transform(T,S), safe_second_pass(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for t in TOOLS.values():
        lines.append(asp.fact("tool", t.id))
        if t.can_fix:
            lines.append(asp.fact("fixable", t.id))
    for s in SCRAPS:
        lines.append(asp.fact("scrap", s))
    lines.append(asp.fact("flashback", "yes"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: dilate a scrap, then fix it with a flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--scrap", choices=SCRAPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    place, tool = select_combo(rng, args)
    scrap = args.scrap or rng.choice(sorted(SCRAPS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    if not reasonableness_gate(TOOLS[tool], scrap):
        raise StoryError("The requested tool and scrap cannot make a sensible story here.")
    return StoryParams(place=place, tool=tool, scrap=scrap, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/3.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "valid_story"))
    expected = set()
    for p in SETTINGS:
        for t in TOOLS:
            for s in SCRAPS:
                if reasonableness_gate(TOOLS[t], s):
                    expected.add((p, t, s))
    if atoms == expected:
        print(f"OK: ASP matches Python gate ({len(atoms)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP only:", sorted(atoms - expected))
    print("Python only:", sorted(expected - atoms))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="workshop", tool="dilator", scrap="paper", name="Mia", gender="girl", helper="grandpa"),
            StoryParams(place="garage", tool="dilator", scrap="cloth", name="Ben", gender="boy", helper="aunt"),
            StoryParams(place="kitchen_table", tool="stretcher", scrap="foil", name="Lily", gender="girl", helper="big sibling"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
                params.seed = base_seed + i
                sample = generate(params)
                if sample.story in seen:
                    i += 1
                    continue
                seen.add(sample.story)
                samples.append(sample)
            except StoryError as e:
                print(e)
                return
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
