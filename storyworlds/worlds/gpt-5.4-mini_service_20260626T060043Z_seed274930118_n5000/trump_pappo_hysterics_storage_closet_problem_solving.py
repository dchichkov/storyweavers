#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/trump_pappo_hysterics_storage_closet_problem_solving.py
==================================================================================

A standalone storyworld for a tiny Tall Tale in a storage closet, where a
mystery, a bit of suspense, and a problem-solving turn lead from hysterics to
a bright ending.

Core premise:
- Trump and Pappo are stuck in a storage closet.
- Something important is missing or hidden.
- Suspense grows from a strange sound or a jammed thing.
- Hysterics flare up, then cool down when Pappo solves the mystery.
"""

from __future__ import annotations

import argparse
import copy
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
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    hidden_in: Optional[str] = None
    openable: bool = False
    closed: bool = False
    locked: bool = False
    searchable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the storage closet"
    cramped: bool = True
    affords: set[str] = field(default_factory=lambda: {"search", "peek", "listen"})


@dataclass
class Mystery:
    id: str
    label: str
    clue: str
    source: str
    hiding_spot: str
    suspense_line: str
    reveal_line: str
    solved_by: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use_line: str
    helps_with: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    mystery: str
    tool: str
    name_a: str
    name_b: str
    seed: Optional[int] = None


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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTING = Setting()

MYSTERIES = {
    "missing_lantern": Mystery(
        id="missing_lantern",
        label="the missing lantern",
        clue="a pale yellow glow behind the boxes",
        source="lantern",
        hiding_spot="top shelf",
        suspense_line="Something in the dark gave a tiny clink-clink, and that made the whole closet feel as wide as a storm cellar.",
        reveal_line="The lantern had been tucked behind a rolled rug on the top shelf, where the dust looked like moon powder.",
        solved_by="reach",
    ),
    "jammed_door": Mystery(
        id="jammed_door",
        label="the jammed closet door",
        clue="a crooked broom handle near the latch",
        source="door",
        hiding_spot="floor crack",
        suspense_line="The door gave one stubborn groan, then held fast, and the quiet after that sounded like a secret holding its breath.",
        reveal_line="A broom handle had slid into the latch, and once Pappo nudged it free, the door swung open with a grand old creak.",
        solved_by="wiggle",
    ),
    "mystery_noise": Mystery(
        id="mystery_noise",
        label="the mystery noise",
        clue="a thump from inside the toy crate",
        source="noise",
        hiding_spot="toy crate",
        suspense_line="From the toy crate came a thump-thump-thump, and even the mop looked like it was listening.",
        reveal_line="The noise was only a tin ball rolling under a stack of mittens, thumping the sides of the crate like a tiny drum.",
        solved_by="peek",
    ),
}

TOOLS = {
    "flashlight": Tool(
        id="flashlight",
        label="a flashlight",
        phrase="a little flashlight with a bright belly",
        use_line="Pappo clicked on the flashlight and pointed the beam along the shelves like a river of daylight.",
        helps_with={"missing_lantern", "mystery_noise"},
    ),
    "broom": Tool(
        id="broom",
        label="a broom",
        phrase="a long broom with a straw tail",
        use_line="Pappo used the broom to nudge boxes aside and poke the latch gently, never once losing their calm.",
        helps_with={"jammed_door", "missing_lantern"},
    ),
    "step_stool": Tool(
        id="step_stool",
        label="a step stool",
        phrase="a sturdy step stool",
        use_line="Pappo set up the step stool and climbed up as careful as a cat on a fence rail.",
        helps_with={"missing_lantern"},
    ),
}

NAMES = ["Trump", "Pappo", "Milo", "Rita", "Nora", "Toby", "Luna", "Bram"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld in a storage closet.")
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for mid, m in MYSTERIES.items():
        for tid, t in TOOLS.items():
            if mid in t.helps_with:
                out.append((mid, tid))
    return out


def explain_invalid(mystery: Mystery, tool: Tool) -> str:
    return f"(No story: {tool.label} does not help solve {mystery.label} in this little closet tale.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mystery and args.tool:
        if (args.mystery, args.tool) not in valid_combos():
            raise StoryError(explain_invalid(MYSTERIES[args.mystery], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.mystery is None or c[0] == args.mystery)
              and (args.tool is None or c[1] == args.tool)]
    if not combos:
        raise StoryError("(No valid combo matches those options.)")
    mystery, tool = rng.choice(sorted(combos))
    name_a = args.name_a or "Trump"
    name_b = args.name_b or "Pappo"
    return StoryParams(mystery=mystery, tool=tool, name_a=name_a, name_b=name_b)


def _tension(world: World, who: Entity, mystery: Mystery) -> None:
    who.memes["suspense"] = who.memes.get("suspense", 0.0) + 1.0
    if mystery.id == "mystery_noise":
        who.memes["hysterics"] = who.memes.get("hysterics", 0.0) + 1.0


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    mystery = MYSTERIES[params.mystery]
    tool = TOOLS[params.tool]

    trump = world.add(Entity(id=params.name_a, kind="character", label=params.name_a))
    pappo = world.add(Entity(id=params.name_b, kind="character", label=params.name_b))
    hidden = world.add(Entity(
        id="hidden_object",
        kind="thing",
        label=mystery.label,
        phrase=mystery.label,
        hidden_in=mystery.hiding_spot,
        searchable=True,
    ))
    world.add(Entity(
        id=tool.id,
        kind="thing",
        label=tool.label,
        phrase=tool.phrase,
        held_by=pappo.id,
    ))

    world.say(
        f"In the storage closet, {trump.label} and {pappo.label} stood under shelves "
        f"that reached high as a courthouse roof, though the place was only a closet."
    )
    world.say(
        f"They were looking for {mystery.label}, and {mystery.clue} was the first clue."
    )

    world.para()
    world.say(mystery.suspense_line)
    _tension(world, trump, mystery)
    _tension(world, pappo, mystery)
    if mystery.id == "missing_lantern":
        world.say(f"{trump.label} got the start of hysterics, because the dark felt thicker without any light.")
    elif mystery.id == "jammed_door":
        world.say(f"{trump.label} started with hysterics, because the closet door would not budge an inch.")
    else:
        world.say(f"{trump.label} nearly burst into hysterics, because nobody likes a mystery noise with no clue attached.")

    world.para()
    world.say(tool.use_line)
    if tool.id == "step_stool" and mystery.id == "missing_lantern":
        world.say("Pappo climbed up, peered behind the rolled rug, and stretched one careful hand into the dust.")
    elif tool.id == "broom" and mystery.id == "jammed_door":
        world.say("Pappo slid the broom tip into the latch and gave it the gentlest wiggle in the world.")
    elif tool.id == "flashlight" and mystery.id == "mystery_noise":
        world.say("The beam swept the crate, and the shiny ball winked back like a hidden star.")
    else:
        world.say("Pappo worked the tool with steady paws and a steady head, as calm as a river in summer.")

    world.say(mystery.reveal_line)
    trump.memes["hysterics"] = 0.0
    trump.memes["relief"] = trump.memes.get("relief", 0.0) + 1.0
    pappo.memes["pride"] = pappo.memes.get("pride", 0.0) + 1.0
    world.facts.update(mystery=mystery, tool=tool, trump=trump, pappo=pappo, hidden=hidden, solved=True)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    m: Mystery = f["mystery"]
    t: Tool = f["tool"]
    return [
        f"Write a tall tale for young children about {f['trump'].label} and {f['pappo'].label} in a storage closet, with a {m.label} to solve.",
        f"Tell a suspenseful but gentle story where {f['pappo'].label} uses {t.label} to solve a mystery in the storage closet.",
        f"Write a child-friendly tall tale that begins with hysterics and ends with a clever reveal in a storage closet.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    m: Mystery = f["mystery"]
    t: Tool = f["tool"]
    trump: Entity = f["trump"]
    pappo: Entity = f["pappo"]
    return [
        QAItem(
            question=f"Where did {trump.label} and {pappo.label} look for {m.label}?",
            answer="They looked in the storage closet, where the shelves stood tall and the clues felt slippery.",
        ),
        QAItem(
            question=f"What made {trump.label} feel hysterics before the problem was solved?",
            answer=f"{m.suspense_line} That strange moment made {trump.label} feel hysterics until {pappo.label} could solve it.",
        ),
        QAItem(
            question=f"How did {pappo.label} use {t.label} to solve the mystery?",
            answer=f"{t.use_line} Then the hidden thing was found, and the mystery finally made sense.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The mystery was solved, {trump.label}'s hysterics calmed down, and the closet stopped feeling spooky.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a storage closet?",
            answer="A storage closet is a small room or cupboard where people keep boxes, tools, brooms, and other things they want to tuck away.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the nervous wondering that happens when something is not known yet, so you keep listening to find out what will happen.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or secret that needs clues and careful thinking to solve.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means noticing what is wrong, thinking of a useful plan, and trying it step by step until the trouble is fixed.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
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
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(mystery="missing_lantern", tool="step_stool", name_a="Trump", name_b="Pappo"),
    StoryParams(mystery="jammed_door", tool="broom", name_a="Trump", name_b="Pappo"),
    StoryParams(mystery="mystery_noise", tool="flashlight", name_a="Trump", name_b="Pappo"),
]


ASP_RULES = r"""
valid(Mystery, Tool) :- mystery(Mystery), tool(Tool), helps(Tool, Mystery).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("solved_by", mid, m.solved_by))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for mid in sorted(t.helps_with):
            lines.append(asp.fact("helps", tid, mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    if a - b:
        print(" only in clingo:", sorted(a - b))
    if b - a:
        print(" only in python:", sorted(b - a))
    return 1


def build_parser_placeholder() -> None:
    pass


def valid_combos() -> list[tuple[str, str]]:
    return [(m, t) for m in MYSTERIES for t in TOOLS if m in TOOLS[t].helps_with]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld in a storage closet.")
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid mystery/tool combos:\n")
        for mid, tid in combos:
            print(f"  {mid:16} {tid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.mystery} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
