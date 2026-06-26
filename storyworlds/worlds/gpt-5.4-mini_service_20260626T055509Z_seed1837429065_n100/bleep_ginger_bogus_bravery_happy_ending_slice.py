#!/usr/bin/env python3
"""
A small slice-of-life storyworld built from the seed words
"bleep", "ginger", and "bogus", with bravery and a happy ending.

The domain:
- A child notices a weird "bleep" sound from a pantry gadget.
- A ginger cookie recipe looks tempting.
- A bogus note claims the cookie maker is broken.
- The child shows bravery by checking the truth, fixing the small problem,
  and ending with a warm happy ending.

The world is intentionally compact: one setting, one kid, one helper, one
small source of tension, and one concrete resolution.
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
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "daughter"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "son"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    fix_kind: str
    helps_with: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    helper_type: str
    tool: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"bake"}),
    "bakery": Setting(place="the bakery", affords={"bake"}),
    "breakroom": Setting(place="the little breakroom", affords={"bake"}),
}

TOOLS = {
    "timer": Tool(
        id="timer",
        label="timer",
        phrase="a tiny kitchen timer",
        fix_kind="truth",
        helps_with={"fake_alarm"},
    ),
    "note": Tool(
        id="note",
        label="note",
        phrase="a bright sticky note",
        fix_kind="truth",
        helps_with={"bogus_note"},
    ),
    "spoon": Tool(
        id="spoon",
        label="wooden spoon",
        phrase="a smooth wooden spoon",
        fix_kind="mix",
        helps_with={"stuck_mix"},
    ),
}

HELPER_LINES = {
    "mother": "mom",
    "father": "dad",
    "baker": "baker",
}

NAMES = ["Mina", "Theo", "Pip", "Luna", "Ben", "Ivy", "Noah", "June"]
CHILD_TYPES = ["girl", "boy"]
HELPERS = ["mother", "father", "baker"]


def _bool_text(v: bool) -> str:
    return "yes" if v else "no"


def _warn_if_bogus(world: World, child: Entity, helper: Entity, tool: Tool) -> bool:
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    child.memes["bravery"] = child.memes.get("bravery", 0.0) + 1
    if tool.fix_kind != "truth":
        return False
    world.say(
        f"{child.id} heard a small bleep from the counter and noticed a bogus note "
        f"that said the baking machine was broken."
    )
    world.say(
        f"{helper.label} frowned, because the note did not match the little bleep at all."
    )
    world.facts["bogus"] = True
    return True


def _act_bake(world: World, child: Entity, helper: Entity, tool: Tool) -> None:
    child.meters["busy"] = child.meters.get("busy", 0.0) + 1
    child.memes["hope"] = child.memes.get("hope", 0.0) + 1
    world.say(
        f"{child.id} wanted to bake ginger cookies anyway, because the warm smell "
        f"of ginger always made the room feel kind."
    )
    world.say(
        f"{helper.label} let {child.pronoun('object')} look closely, and {child.id} chose to be brave."
    )


def _fix_machine(world: World, child: Entity, helper: Entity, tool: Tool) -> None:
    world.say(
        f"{child.id} used {tool.phrase} to test the machine. The bleep only came from "
        f"a low battery, not from any real problem."
    )
    world.say(
        f"{helper.label} changed the battery and smiled at the small, honest fix."
    )
    world.facts["fixed"] = True


def _finish(world: World, child: Entity, helper: Entity) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    child.memes["bravery"] = child.memes.get("bravery", 0.0) + 1
    world.say(
        f"Soon the oven was warm, the ginger cookies were baking, and the bogus note "
        f"was tossed in the scrap bin."
    )
    world.say(
        f"When the cookies came out golden, {child.id} laughed with {helper.label}; "
        f"it was a happy ending made of crumbs, heat, and a very real good smell."
    )


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        meters={"busy": 0.0},
        memes={"curiosity": 0.0, "bravery": 0.0, "hope": 0.0, "joy": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper_type,
        label=HELPER_LINES[params.helper_type],
        meters={"busy": 0.0},
        memes={"worry": 0.0, "relief": 0.0},
    ))
    tool = TOOLS[params.tool]
    world.add(Entity(
        id=tool.id,
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
    ))

    world.say(
        f"In {setting.place}, {child.id} noticed a strange little bleep while standing near the counter."
    )
    world.say(
        f"On the counter sat a ginger recipe card, and beside it was a bogus note that seemed too confident."
    )
    world.para()
    _warn_if_bogus(world, child, helper, tool)
    _act_bake(world, child, helper, tool)
    world.para()
    _fix_machine(world, child, helper, tool)
    _finish(world, child, helper)

    world.facts.update(
        child=child,
        helper=helper,
        tool=tool,
        setting=setting,
    )
    return world


def valid_combos() -> list[tuple[str, str]]:
    return [(place, tool_id) for place in SETTINGS for tool_id in TOOLS]


@dataclass
class StoryContext:
    params: StoryParams
    world: World
    story: str
    prompts: list[str]
    story_qa: list[QAItem]
    world_qa: list[QAItem]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["child"]
    h = f["helper"]
    return [
        'Write a short slice-of-life story for a small child about a bleeping kitchen moment, a ginger snack, and a bogus note.',
        f"Tell a gentle story about {c.id} in {world.setting.place} where {c.id} shows bravery with help from {h.label}.",
        'Write a simple happy-ending story that includes the words bleep, ginger, and bogus.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c: Entity = f["child"]
    h: Entity = f["helper"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"What did {c.id} hear near the counter?",
            answer=f"{c.id} heard a small bleep from the counter, which made {c.pronoun('object')} look closer.",
        ),
        QAItem(
            question=f"Why was the note bogus?",
            answer="It was bogus because it blamed the machine, but the bleep turned out to be only a low battery.",
        ),
        QAItem(
            question=f"How did {c.id} show bravery?",
            answer=f"{c.id} showed bravery by checking the problem instead of hiding from it and by using {tool.phrase} to help find the truth.",
        ),
        QAItem(
            question=f"What made the ending happy?",
            answer=f"The ending was happy because the battery was changed, the ginger cookies baked well, and {h.label} laughed with {c.id}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ginger?",
            answer="Ginger is a root with a warm, sharp taste. People use it in cookies, tea, and other foods.",
        ),
        QAItem(
            question="What does bleep usually mean?",
            answer="A bleep is a short electronic sound, like a tiny beep from a machine or timer.",
        ),
        QAItem(
            question="What does bogus mean?",
            answer="Bogus means not true or not real.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something scary or uncertain while still trying your best.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: bleep, ginger, bogus, bravery, happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--helper-type", choices=HELPERS)
    ap.add_argument("--tool", choices=TOOLS)
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
    place = args.place or rng.choice(sorted(SETTINGS))
    tool = args.tool or rng.choice(sorted(TOOLS))
    if (place, tool) not in combos:
        raise StoryError("No valid combination matches the requested options.")
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    helper_type = args.helper_type or rng.choice(HELPERS)
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, child_name=name, child_type=child_type, helper_type=helper_type, tool=tool)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(P, T) :- place(P), tool(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
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
    StoryParams(place="kitchen", child_name="Mina", child_type="girl", helper_type="mother", tool="note"),
    StoryParams(place="bakery", child_name="Theo", child_type="boy", helper_type="baker", tool="timer"),
    StoryParams(place="breakroom", child_name="Ivy", child_type="girl", helper_type="father", tool="spoon"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
