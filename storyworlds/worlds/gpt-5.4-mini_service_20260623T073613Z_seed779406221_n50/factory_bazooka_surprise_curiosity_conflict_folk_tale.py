#!/usr/bin/env python3
"""
storyworlds/worlds/factory_bazooka_surprise_curiosity_conflict_folk_tale.py
===========================================================================

A small folk-tale-style storyworld about a curious child at a factory, a
surprising bazooka-shaped machine part, a conflict with a patient grown-up,
and a safe turn toward making something useful.

The seed words are preserved as story elements: factory, bazooka, surprise,
curiosity, conflict. The premise is intentionally tiny and classical: a child
finds a strange thing in a factory, wants to use it, is warned, then learns the
thing is for making loud harmless puffs that help the factory work.

This world models physical meters and emotional memes, supports QA, trace, JSON,
and an ASP twin for parity checks.
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    sound: str
    purpose: str
    safe_use: str
    noisy: bool = True


@dataclass
class Machine:
    id: str
    label: str
    phrase: str
    can_burst: bool = False
    kind: str = "machine"


@dataclass
class StoryParams:
    factory: str
    tool: str
    machine: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


FACTORY = Setting(place="the little factory", afford={"work", "repair"})
TOOLS = {
    "bazooka": Tool(
        id="bazooka",
        label="bazooka-shaped air tube",
        phrase="a bazooka-shaped air tube",
        sound="whuff!",
        purpose="blast dust off the gears",
        safe_use="aim it at the dusty gears and give them one careful puff",
        noisy=True,
    ),
    "bellows": Tool(
        id="bellows",
        label="bellows",
        phrase="a pair of bellows",
        sound="fwoof!",
        purpose="send air into the furnace",
        safe_use="pump them at the warm stove",
        noisy=True,
    ),
}
MACHINES = {
    "gear": Machine(id="gear", label="gear wheel", phrase="the gear wheel", can_burst=False),
    "chimney": Machine(id="chimney", label="chimney vent", phrase="the chimney vent", can_burst=True),
}
NAMES = {
    "girl": ["Mina", "Luna", "Anya", "Suri", "Iris"],
    "boy": ["Pip", "Tomas", "Rafi", "Niko", "Evan"],
}
TRAITS = ["curious", "brave", "gentle", "bright", "thoughtful"]


def valid_combos() -> list[tuple[str, str]]:
    return [(t, m) for t in TOOLS for m in MACHINES if TOOLS[t].noisy and MACHINES[m].can_burst]


def asp_facts() -> str:
    import asp

    lines = [asp.fact("setting", "factory"), asp.fact("can_afford", "factory", "work")]
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.noisy:
            lines.append(asp.fact("noisy", tid))
    for mid, m in MACHINES.items():
        lines.append(asp.fact("machine", mid))
        if m.can_burst:
            lines.append(asp.fact("can_burst", mid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(T, M) :- tool(T), machine(M), noisy(T), can_burst(M).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, p = set(asp_valid_combos()), set(valid_combos())
    if a == p:
        print(f"OK: ASP gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    if a - p:
        print("  only in ASP:", sorted(a - p))
    if p - a:
        print("  only in Python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale about a factory surprise and a safe bazooka.")
    ap.add_argument("--factory", choices=["factory"])
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--machine", choices=MACHINES)
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
    if args.tool and args.machine:
        if (args.tool, args.machine) not in valid_combos():
            raise StoryError("That bazooka-shaped tool would not be a sensible fit for that machine.")
    combos = valid_combos()
    if args.tool:
        combos = [c for c in combos if c[0] == args.tool]
    if args.machine:
        combos = [c for c in combos if c[1] == args.machine]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    tool, machine = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    return StoryParams(
        factory="factory",
        tool=tool,
        machine=machine,
        name=name,
        gender=gender,
        parent=args.parent or rng.choice(["mother", "father"]),
        trait=rng.choice(TRAITS),
    )


def tell(setting: Setting, tool: Tool, machine: Machine, name: str, gender: str, parent: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, role="child", memes={"curiosity": 0, "surprise": 0, "conflict": 0}))
    grownup = world.add(Entity(id="Parent", kind="character", type=parent, role="parent"))
    device = world.add(Entity(id=tool.id, kind="thing", type="tool", label=tool.label, phrase=tool.phrase, attrs={"purpose": tool.purpose}))
    mach = world.add(Entity(id=machine.id, kind="thing", type="machine", label=machine.label, phrase=machine.phrase))
    child.memes["curiosity"] += 1
    child.memes["surprise"] += 1
    world.say(f"In {setting.place}, a little {trait} {gender} named {name} found {tool.phrase} beside {machine.phrase}.")
    world.say(f"It was a strange surprise, like a flute made for giants, and {name} could not stop looking at it.")
    world.para()
    child.memes["curiosity"] += 1
    world.say(f"{name} wanted to try {tool.label} at once, because {tool.purpose}.")
    world.say(f'But {grownup.label_word} said, "{tool.label} is for helping, not for showing off. Let us think first."')
    child.memes["conflict"] += 1
    world.say(f"{name} crossed {child.pronoun('possessive')} arms and felt the tug of conflict.")
    world.para()
    child.memes["surprise"] += 1
    child.memes["curiosity"] += 1
    world.say(f"Then {grownup.label_word} lifted {tool.phrase} and showed how {tool.safe_use}.")
    world.say(f"{tool.sound.capitalize()} The old machine sighed, dust flew away, and the factory looked bright again.")
    child.memes["conflict"] = 0
    child.memes["surprise"] += 1
    world.say(f"{name} laughed in surprise, because the bazooka-shaped thing was not a weapon at all, only a helper.")
    world.say(f"By the end, {name} was proud to stand beside {grownup.label_word}, and {machine.phrase} turned easy and smooth.")
    world.facts.update(child=child, parent=grownup, tool=device, machine=mach, trait=trait, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["child"]
    return [
        f'Write a folk-tale story for a small child about a factory, a surprising tool, and a kind warning, using the word "bazooka".',
        f"Tell a gentle story where {c.id} finds a bazooka-shaped tool in the factory, feels curiosity and conflict, and learns a safe use for it.",
        f'Write a short story in a folk-tale style about surprise, curiosity, and conflict in a factory, ending with a useful machine helper.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c, p, tool, mach = f["child"], f["parent"], f["tool"], f["machine"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about a little {f['trait']} {c.type} named {c.id} and {p.label_word}, who are both at the factory.",
        ),
        QAItem(
            question=f"What did {c.id} find in the factory?",
            answer=f"{c.id} found {tool.phrase} near {mach.phrase}. It looked surprising, but it was meant to help the factory work.",
        ),
        QAItem(
            question=f"Why did {c.id} feel conflict at first?",
            answer=f"{c.id} felt curiosity and wanted to try the tool right away, but {p.label_word} asked for patience, so the two wishes pulled against each other.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{p.label_word.capitalize()} showed how to use {tool.label} safely, the machine got its dust cleared away, and {c.id} ended happy and proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a factory?",
            answer="A factory is a place where people make things or fix things with machines and careful work.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn about something new.",
        ),
        QAItem(
            question="What is conflict?",
            answer="Conflict is when two wants pull in different directions, like wanting to rush ahead and also wanting to be careful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("\n== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(factory="factory", tool="bazooka", machine="gear", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(factory="factory", tool="bellows", machine="chimney", name="Pip", gender="boy", parent="father", trait="thoughtful"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(FACTORY, TOOLS[params.tool], MACHINES[params.machine], params.name, params.gender, params.parent, params.trait)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (tool, machine) combos:\n")
        for tool, machine in combos:
            print(f"  {tool:10} {machine}")
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.tool} at {p.factory} ({p.machine})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
