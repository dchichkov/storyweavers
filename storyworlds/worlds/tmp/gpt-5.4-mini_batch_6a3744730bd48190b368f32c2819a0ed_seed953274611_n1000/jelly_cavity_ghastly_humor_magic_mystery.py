#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/jelly_cavity_ghastly_humor_magic_mystery.py
============================================================================

A tiny mystery storyworld about a child, a puzzling cavity, and a very strange
jelly clue. The stories are child-facing, lightly humorous, and gently magical:
something eerie looks ghastly at first, then the clue is decoded and the mystery
turns into a small, satisfying reveal.

The world keeps a concrete state with meters and memes, uses a simple causal
engine, supports grounded QA, and includes an inline ASP twin for parity checks.
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MAGIC_MIN = 2
MYSTERY_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    weird: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    hum: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Reveal:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_ghastly(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    if clue.meters["weird"] < THRESHOLD:
        return out
    sig = ("ghastly",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ch in world.characters():
        ch.memes["spook"] += 1
    world.get("room").meters["mystery"] += 1
    out.append("The hallway suddenly felt ghastly and full of questions.")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    for ch in world.characters():
        if ch.memes["relief"] < THRESHOLD:
            continue
        sig = ("laugh", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ch.memes["joy"] += 1
        out.append(f"{ch.id} could not help but giggle.")
    return out


CAUSAL_RULES = [Rule("ghastly", _r_ghastly), Rule("laugh", _r_laugh)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def clue_at_risk(clue: Clue, tool: MagicTool) -> bool:
    return "magic" in tool.tags and "mystery" in clue.tags


def sensible_tools() -> list[MagicTool]:
    return [t for t in TOOLS.values() if t.sense >= MAGIC_MIN]


def answer_power(tool: MagicTool, clue: Clue) -> int:
    return tool.power + (1 if "ghost" in clue.tags else 0)


def predict_reveal(world: World, clue_id: str) -> dict:
    sim = world.copy()
    _use_tool(sim, sim.get("tool"), sim.get(clue_id), narrate=False)
    return {
        "revealed": sim.get("clue").meters["solved"] >= THRESHOLD,
        "spook": sim.get("kid").memes["spook"],
    }


def _use_tool(world: World, tool: Entity, clue: Entity, narrate: bool = True) -> None:
    clue.meters["weird"] += 1
    clue.meters["solved"] += 1
    tool.meters["glow"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, kid: Entity, helper: Entity, clue: Clue) -> None:
    kid.memes["curiosity"] += 1
    world.say(
        f"On a rainy afternoon, {kid.id} and {helper.id} followed a mystery to "
        f"the old cabinet. Inside was {clue.phrase}, and it looked oddly weird."
    )
    world.say(
        f'"It seems ghastly," {kid.id} whispered, "but I think it wants to tell us something."'
    )


def hint(world: World, helper: Entity, kid: Entity, clue: Clue, tool: MagicTool) -> None:
    helper.memes["mystery"] += 1
    world.say(
        f"{helper.id} peered at the clue. " 
        f'"If magic can make a door squeak, maybe it can make this {clue.label} speak," '
        f"{helper.pronoun()} said, with a smile hiding in {helper.pronoun('possessive')} voice."
    )
    world.say(
        f'Then {helper.id} noticed {tool.phrase}; it {tool.hum} and made the dust wiggle like tiny feet.'
    )


def reveal(world: World, kid: Entity, helper: Entity, clue: Clue, tool: MagicTool) -> None:
    _use_tool(world, world.get("tool"), world.get("clue"))
    kid.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{kid.id} tapped the {clue.label}, and {tool.phrase} {tool.hum}. "
        f"The weirdness peeled away like a sticker. The {clue.label} was only "
        f"a jelly-filled cavity in the old cabinet, not a ghost at all."
    )
    world.say(
        f"Under the jelly was a tiny metal key, and the key fit the cabinet lock with a cheerful click."
    )
    world.say(
        f'{kid.id} and {helper.id} laughed, because the "ghost" was just a silly secret with a sticky snack hiding inside.'
    )


def ending(world: World, kid: Entity, helper: Entity) -> None:
    kid.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At the end, the cabinet stood open, the key was found, and the jelly jar went to the kitchen instead of the mystery room."
    )
    world.say(
        f"{kid.id} grinned at {helper.id}. The ghastly look was gone, and the whole puzzle had turned into a joke they could tell again and again."
    )


def tell(clue: Clue, tool: MagicTool, kid_name: str = "Mina", helper_name: str = "Ollie",
         kid_type: str = "girl", helper_type: str = "boy") -> World:
    world = World()
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_type, role="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    room = world.add(Entity(id="room", type="room", label="the room"))
    clue_ent = world.add(Entity(id="clue", type="clue", label=clue.label, tags=set(clue.tags)))
    tool_ent = world.add(Entity(id="tool", type="tool", label=tool.label, tags=set(tool.tags)))
    world.facts["clue"] = clue
    world.facts["tool"] = tool
    world.facts["room"] = room
    opening(world, kid, helper, clue)
    world.para()
    hint(world, helper, kid, clue, tool)
    world.para()
    reveal(world, kid, helper, clue, tool)
    ending(world, kid, helper)
    world.facts.update(kid=kid, helper=helper, clue_ent=clue_ent, tool_ent=tool_ent)
    world.facts["solved"] = clue_ent.meters["solved"] >= THRESHOLD
    return world


CLUES = {
    "cabinet": Clue(
        id="cabinet",
        label="cavity",
        phrase="a cavity in the old cabinet",
        weird="strangely hollow",
        tags={"mystery", "ghost", "jelly"},
    ),
    "drawer": Clue(
        id="drawer",
        label="drawer gap",
        phrase="a gap behind the drawer",
        weird="oddly squishy",
        tags={"mystery", "jelly"},
    ),
    "box": Clue(
        id="box",
        label="box hole",
        phrase="a hole inside the toy box",
        weird="wobbly and eerie",
        tags={"mystery", "ghost"},
    ),
}

TOOLS = {
    "wand": MagicTool(
        id="wand",
        label="sparkly wand",
        phrase="a sparkly wand",
        hum="hummed softly",
        tags={"magic"},
    ),
    "mirror": MagicTool(
        id="mirror",
        label="moon mirror",
        phrase="a moon mirror",
        hum="blinked with moonlight",
        tags={"magic"},
    ),
    "lantern": MagicTool(
        id="lantern",
        label="tiny lantern",
        phrase="a tiny lantern",
        hum="glowed with a warm hum",
        tags={"magic"},
    ),
}

CURATED = [
    StoryParams if False else None
]

# Replace placeholder below after StoryParams is defined.

GIRL_NAMES = ["Mina", "Lina", "Zoe", "Ava", "Nia", "Ivy"]
BOY_NAMES = ["Ollie", "Milo", "Theo", "Ben", "Finn", "Noah"]
HELPER_TRAITS = ["curious", "careful", "cheerful", "silly", "patient"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for cid, clue in CLUES.items():
        for tid, tool in TOOLS.items():
            if clue_at_risk(clue, tool):
                combos.append((cid, tid))
    return combos


@dataclass
class StoryParams:
    clue: str
    tool: str
    kid_name: str
    kid_type: str
    helper_name: str
    helper_type: str
    trait: str = "curious"
    seed: Optional[int] = None


CURATED = [
    StoryParams(clue="cabinet", tool="wand", kid_name="Mina", kid_type="girl", helper_name="Ollie", helper_type="boy", trait="curious"),
    StoryParams(clue="drawer", tool="mirror", kid_name="Lina", kid_type="girl", helper_name="Milo", helper_type="boy", trait="silly"),
    StoryParams(clue="box", tool="lantern", kid_name="Theo", kid_type="boy", helper_name="Ava", helper_type="girl", trait="careful"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue, tool, kid, helper = f["clue"], f["tool"], f["kid"], f["helper"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes the words "jelly", "cavity", and "ghastly".',
        f"Tell a funny magical mystery about {kid.id} and {helper.id} solving a strange {clue.label} clue with {tool.label}.",
        f"Write a child-friendly story where something looks ghastly, but the answer is playful, magical, and a little silly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid, helper, clue, tool = f["kid"], f["helper"], f["clue"], f["tool"]
    qa = [
        ("Who solved the mystery?",
         f"{kid.id} and {helper.id} solved it together. They looked carefully, asked questions, and followed the magical clue all the way to the answer."),
        ("Why did the clue seem ghastly at first?",
         f"It looked ghastly because it was odd and dim in the cabinet. The strange shape and sticky jelly made it feel spooky until they checked it more closely."),
        ("What was really inside the cavity?",
         f"It was a jelly-filled hiding spot, and under the jelly they found a tiny key. The cavity was not a ghost at all; it was just a strange little place where something had been tucked away."),
        ("How did the magic help?",
         f"{tool.phrase} helped reveal the clue. Its glow made the hidden key easy to see, so the mystery could be solved without any fear."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = []
    tags = set(world.facts["clue"].tags) | set(world.facts["tool"].tags)
    if "jelly" in tags:
        out.append(("What is jelly?",
                     "Jelly is a soft, wobbly sweet food. It jiggles when you move it and can be eaten on bread or with a spoon."))
    if "mystery" in tags:
        out.append(("What is a mystery?",
                     "A mystery is something you do not understand yet. You solve it by looking for clues and asking good questions."))
    if "magic" in tags:
        out.append(("What is magic in a story?",
                     "Magic in a story is a pretend power that can make surprising things happen. It often helps characters solve problems in fun ways."))
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


def explain_rejection(clue: Clue, tool: MagicTool) -> str:
    return (
        f"(No story: {tool.label} can do magic, but this clue does not pass the mystery gate. "
        f"Try a clue that really feels spooky and hidden.)"
    )


def sensible_choices() -> list[MagicTool]:
    return [t for t in TOOLS.values() if t.sense >= MAGIC_MIN]


def outcome_of(params: StoryParams) -> str:
    return "solved"


ASP_RULES = r"""
clue(C) :- clue_id(C).
tool(T) :- tool_id(T).
magic(T) :- tool(T), magic_tool(T).
mystery(C) :- clue(C), mystery_clue(C).
valid(C, T) :- clue(C), tool(T), magic(T), mystery(C).
solved :- chosen_clue(C), chosen_tool(T), valid(C, T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for cid in CLUES:
        lines.append(asp.fact("clue_id", cid))
    for cid, clue in CLUES.items():
        if "mystery" in clue.tags:
            lines.append(asp.fact("mystery_clue", cid))
    for tid in TOOLS:
        lines.append(asp.fact("tool_id", tid))
        lines.append(asp.fact("magic_tool", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a magical humorous mystery.")
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--parent", choices=["mother", "father"])  # accepted but unused style-wise
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
              if (args.clue is None or c[0] == args.clue)
              and (args.tool is None or c[1] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    clue, tool = rng.choice(sorted(combos))
    clue_obj = CLUES[clue]
    if args.tool and args.tool not in TOOLS:
        raise StoryError("(Unknown tool.)")
    kid_type = rng.choice(["girl", "boy"])
    kid_name = args.name or rng.choice(GIRL_NAMES if kid_type == "girl" else BOY_NAMES)
    helper_type = "boy" if kid_type == "girl" else "girl"
    helper_name = args.helper or rng.choice(BOY_NAMES if helper_type == "boy" else GIRL_NAMES)
    return StoryParams(clue=clue, tool=tool, kid_name=kid_name, kid_type=kid_type,
                       helper_name=helper_name, helper_type=helper_type,
                       trait=rng.choice(HELPER_TRAITS))


def generate(params: StoryParams) -> StorySample:
    if params.clue not in CLUES:
        raise StoryError(f"Unknown clue '{params.clue}'.")
    if params.tool not in TOOLS:
        raise StoryError(f"Unknown tool '{params.tool}'.")
    world = tell(CLUES[params.clue], TOOLS[params.tool],
                 kid_name=params.kid_name, helper_name=params.helper_name,
                 kid_type=params.kid_type, helper_type=params.helper_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (clue, tool) combos:")
        for c, t in asp_valid_combos():
            print(f"  {c:10} {t}")
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
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
