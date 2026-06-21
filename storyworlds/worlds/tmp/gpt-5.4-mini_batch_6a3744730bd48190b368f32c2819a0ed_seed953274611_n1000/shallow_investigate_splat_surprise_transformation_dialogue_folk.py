#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/shallow_investigate_splat_surprise_transformation_dialogue_folk.py
===================================================================================================

A tiny folk-tale storyworld about a child, a shallow stream, a surprise, a
transformation, and a splashy discovery.

Seed words: shallow, investigate, splat
Features: Surprise, Transformation, Dialogue
Style: Folk Tale
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    name: str
    shallow: bool
    has_bridge: bool
    has_reed: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Creature:
    id: str
    label: str
    kind: str
    surprise_sound: str
    transform_into: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    setting: str
    creature: str
    tool: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "brook": Setting(id="brook", name="a shallow brook", shallow=True, has_bridge=False, has_reed=True, tags={"shallow"}),
    "pond": Setting(id="pond", name="a shallow pond", shallow=True, has_bridge=True, has_reed=False, tags={"shallow"}),
    "marsh": Setting(id="marsh", name="a shallow marsh", shallow=True, has_bridge=False, has_reed=True, tags={"shallow"}),
}

CREATURES = {
    "fish": Creature(id="fish", label="silver fish", kind="fish", surprise_sound="splat", transform_into="frog", tags={"surprise", "splat", "transformation"}),
    "frog": Creature(id="frog", label="green frog", kind="frog", surprise_sound="splat", transform_into="princess", tags={"surprise", "transformation"}),
    "duck": Creature(id="duck", label="brown duck", kind="duck", surprise_sound="splat", transform_into="swan", tags={"surprise", "transformation"}),
}

TOOLS = {
    "lantern": Tool(id="lantern", label="lantern", phrase="a little lantern", tags={"dialogue"}),
    "net": Tool(id="net", label="net", phrase="a small net", tags={"investigate"}),
    "stick": Tool(id="stick", label="stick", phrase="a willow stick", tags={"investigate"}),
}

GIRL_NAMES = ["Mara", "Lina", "Tessa", "Nia", "Elin"]
BOY_NAMES = ["Pip", "Robin", "Jon", "Bram", "Rowan"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CREATURES:
            for t in TOOLS:
                combos.append((s, c, t))
    return combos


def make_child(world: World, name: str, gender: str, role: str) -> Entity:
    return world.add(Entity(id=name, kind="character", type=gender, role=role, traits=["curious"], tags={"dialogue"}))


def setup_story(world: World, setting: Setting, creature: Creature, tool: Tool, child: Entity, helper: Entity) -> None:
    child.memes["curiosity"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"Once in the old lane by {setting.name}, {child.id} and {helper.id} walked beside the water."
    )
    world.say(
        f"The stream was so shallow that pebbles shone through it, and {child.id} said, "
        f"“Let us {tool.label} and see what lives there.”"
    )


def investigate(world: World, setting: Setting, creature: Creature, tool: Tool, child: Entity, helper: Entity) -> None:
    child.meters["attention"] += 1
    helper.memes["caution"] += 1
    world.say(
        f'{helper.id} answered, “We may look, but we must go slowly.” Then they used {tool.phrase} to investigate.'
    )
    world.say(
        f"They leaned over the {setting.name}, and the water gave a soft shine back to their faces."
    )


def surprise_and_splat(world: World, creature: Creature, child: Entity, helper: Entity) -> None:
    child.memes["startle"] += 1
    helper.memes["startle"] += 1
    creature_ent = world.add(Entity(id="creature", kind="creature", type=creature.kind, label=creature.label, tags=creature.tags))
    creature_ent.meters["hidden"] += 1
    world.say(
        f"Then, from under a flat stone, {creature.label} popped out with a bright {creature.surprise_sound}!"
    )
    world.say(
        f'{child.id} cried, “What is that?” and {helper.id} laughed, “A shy one from the water!”'
    )
    world.say(
        f"The creature gave a joyful {creature.surprise_sound}, and the mud at the edge went splat."
    )
    child.meters["wet"] += 1
    helper.meters["wet"] += 1


def transform(world: World, creature: Creature, child: Entity, helper: Entity) -> None:
    creature_ent = world.get("creature")
    if creature_ent.meters["hidden"] < THRESHOLD:
        creature_ent.meters["revealed"] += 1
    creature_ent.type = creature.transform_into
    creature_ent.label = {
        "frog": "little frog",
        "princess": "water princess",
        "swan": "white swan",
    }.get(creature.transform_into, creature_ent.label)
    world.say(
        f"The wonder was not done: with one ripple, the {creature.label} changed into a {creature_ent.label}."
    )
    world.say(
        f'{helper.id} whispered, “Look how the stream keeps its secrets.” {child.id} smiled, no longer afraid.'
    )
    child.memes["wonder"] += 1
    helper.memes["wonder"] += 1


def ending(world: World, setting: Setting, child: Entity, helper: Entity, tool: Tool) -> None:
    world.say(
        f"They thanked the water, took up {tool.phrase}, and followed the lane home beside the reeds."
    )
    world.say(
        f"From then on, whenever {child.id} heard a small rustle near {setting.name}, {child.id} said, "
        f'“Let us investigate kindly.”'
    )


def tell(setting: Setting, creature: Creature, tool: Tool, child_name: str, child_gender: str, helper_name: str, helper_gender: str) -> World:
    world = World()
    child = make_child(world, child_name, child_gender, "hero")
    helper = make_child(world, helper_name, helper_gender, "helper")
    world.facts["setting"] = setting
    world.facts["creature_cfg"] = creature
    world.facts["tool_cfg"] = tool
    world.facts["child"] = child
    world.facts["helper"] = helper

    setup_story(world, setting, creature, tool, child, helper)
    world.para()
    investigate(world, setting, creature, tool, child, helper)
    surprise_and_splat(world, creature, child, helper)
    world.para()
    transform(world, creature, child, helper)
    ending(world, setting, child, helper, tool)
    world.facts["outcome"] = "transformed"
    return world


KNOWLEDGE = {
    "shallow": [("What does shallow mean?", "Shallow means not deep. A shallow place lets you see close to the bottom.")],
    "investigate": [("What does investigate mean?", "To investigate means to look carefully and try to find out what is happening.")],
    "splat": [("What is a splat?", "A splat is a wet, soft sound made when something lands with a little splash.")],
    "surprise": [("What is a surprise?", "A surprise is something you did not expect. It can make you gasp or smile.")],
    "transformation": [("What is a transformation?", "A transformation is a change from one form into another.")],
    "dialogue": [("What is dialogue?", "Dialogue is when characters speak to each other in the story.")],
}
KNOWLEDGE_ORDER = ["shallow", "investigate", "splat", "surprise", "transformation", "dialogue"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a child that uses the words "shallow", "investigate", and "splat".',
        f"Tell a gentle folk tale where {f['child'].id} and {f['helper'].id} go to {f['setting'].name}, investigate the water, and meet a surprise creature.",
        f"Write a short story with dialogue, a surprise in a shallow place, and a magical transformation at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    setting = f["setting"]
    creature = f["creature_cfg"]
    tool = f["tool_cfg"]
    qa = [
        QAItem(
            question="Where did the children go?",
            answer=f"They went to {setting.name}, where the water was shallow and easy to see through."
        ),
        QAItem(
            question="What did they want to do there?",
            answer=f"They wanted to investigate the water and use {tool.phrase} to see what was hiding there."
        ),
        QAItem(
            question=f"What surprised {child.id} and {helper.id}?",
            answer=f"{creature.label} surprised them by popping out with a bright splat, so both children jumped back."
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The creature transformed into a gentle new form, and the children changed too because they became calmer and wiser."
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["setting"].tags) | set(world.facts["creature_cfg"].tags) | set(world.facts["tool_cfg"].tags)
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            q, a = KNOWLEDGE[key][0]
            out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
shallow_place(S) :- setting(S), shallow(S).
investigation(I) :- tool(I), investigate_tool(I).
surprise(C) :- creature(C), surprise_kind(C).
transforms(C) :- creature(C), transform_target(C).

valid_story(S, C, T) :- shallow_place(S), surprise(C), transforms(C), tool(T).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.shallow:
            lines.append(asp.fact("shallow", sid))
        if s.has_bridge:
            lines.append(asp.fact("bridge", sid))
        if s.has_reed:
            lines.append(asp.fact("reed", sid))
    for cid, c in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        lines.append(asp.fact("surprise_kind", cid))
        lines.append(asp.fact("transform_target", cid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("investigate_tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if len(a) == len(p):
        print(f"OK: ASP gate matches valid_combos() ({len(a)} combos).")
    else:
        print("MISMATCH in valid combos:")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:
        print(f"FAIL: smoke test generation crashed: {exc}")
        return 1
    return rc


CURATED = [
    StoryParams(setting="brook", creature="fish", tool="net", child="Mara", child_gender="girl", helper="Robin", helper_gender="boy"),
    StoryParams(setting="pond", creature="frog", tool="stick", child="Pip", child_gender="boy", helper="Lina", helper_gender="girl"),
    StoryParams(setting="marsh", creature="duck", tool="lantern", child="Tessa", child_gender="girl", helper="Bram", helper_gender="boy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny folk-tale storyworld with shallow water, investigation, splat, surprise, transformation, and dialogue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.creature is None or c[1] == args.creature)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, creature, tool = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != child])
    return StoryParams(setting=setting, creature=creature, tool=tool, child=child, child_gender=child_gender, helper=helper, helper_gender=helper_gender)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.creature not in CREATURES or params.tool not in TOOLS:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], CREATURES[params.creature], TOOLS[params.tool], params.child, params.child_gender, params.helper, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q.question, answer=q.answer) for q in story_qa(world)],
        world_qa=[QAItem(question=q.question, answer=q.answer) for q in world_qa(world)],
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for item in combos:
            print("  ", item)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
