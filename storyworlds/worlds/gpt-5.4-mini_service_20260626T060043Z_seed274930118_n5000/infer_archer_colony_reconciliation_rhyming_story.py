#!/usr/bin/env python3
"""
A small story world for a rhyming tale about an archer, a colony, and
reconciliation after a shared misunderstanding.

The domain is intentionally narrow:
- a colony of tiny creatures with a shared hall
- one archer who can shoot practice arrows into marked rings
- a mistaken accusation that causes hurt feelings
- a reconciliation turn where the archer helps fix the problem

The prose engine uses world state to drive a complete story with a beginning,
middle turn, and ending image. An ASP twin checks the reasonableness gate.
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
    plural: bool = False
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"archer", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the meadow edge"
    colony_name: str = "the Bramble Colony"


@dataclass
class StoryParams:
    place: str
    colony_name: str
    archer_name: str
    colony_name2: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


ARCHER_NAMES = ["Arin", "Milo", "Nia", "Tess", "Rook", "Lina", "Pip", "Sera"]
COLONY_NAMES = ["the Clover Colony", "the Moss Colony", "the Pebble Colony"]
PLACES = ["the meadow edge", "the little stone arch", "the apple lane"]


@dataclass
class Archer:
    name: str
    steadiness: float = 1.0


@dataclass
class Colony:
    name: str
    trust: float = 1.0
    harmony: float = 1.0


@dataclass
class Ring:
    id: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


THRESHOLD = 1.0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world: archer, colony, reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--archer-name", choices=ARCHER_NAMES)
    ap.add_argument("--colony-name", choices=COLONY_NAMES)
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


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "meadow"),
        asp.fact("feature", "reconciliation"),
        asp.fact("topic", "archer"),
        asp.fact("topic", "colony"),
        asp.fact("topic", "infer"),
        asp.fact("place", "meadow_edge"),
        asp.fact("colony", "bramble"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
valid_story :- setting(meadow), feature(reconciliation), topic(archer), topic(colony), topic(infer).
#show valid_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    ok = any(sym.name == "valid_story" for sym in model)
    if ok:
        print("OK: ASP gate accepted the reconciliation archer-colony story.")
        return 0
    print("Mismatch: ASP gate rejected the intended story.")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(PLACES)
    archer_name = args.archer_name or rng.choice(ARCHER_NAMES)
    colony_name = args.colony_name or rng.choice(COLONY_NAMES)
    if place not in PLACES:
        raise StoryError("Unknown place.")
    return StoryParams(place=place, colony_name=colony_name, archer_name=archer_name, colony_name2=colony_name)


def make_world(params: StoryParams) -> World:
    world = World(Setting(place=params.place, colony_name=params.colony_name))
    archer = world.add(Entity(id="archer", kind="character", type="archer", label=params.archer_name))
    colony = world.add(Entity(id="colony", kind="group", type="colony", label=params.colony_name))
    target = world.add(Entity(id="ring", type="ring", label="bright ring", role="practice target"))
    bridge = world.add(Entity(id="bridge", type="thing", label="reed bridge"))
    world.facts.update(archer=archer, colony=colony, target=target, bridge=bridge)
    return world


def infer_misread(world: World) -> None:
    archer = world.get("archer")
    colony = world.get("colony")
    colony.memes["worry"] = 1.0
    archer.memes["pride"] = 1.0
    world.say(
        f"At {world.setting.place}, {archer.label} the archer could not quite infer the colony's cheer;"
    )
    world.say(
        f"he heard their busy buzz as blame, though it was only their workday near and dear."
    )


def conflict(world: World) -> None:
    colony = world.get("colony")
    archer = world.get("archer")
    colony.memes["hurt"] = 1.0
    archer.memes["regret"] = 1.0
    world.say(
        f"The colony felt stung and slighted, and the little hall went dim and drear;"
    )
    world.say(
        f"the archer's words had landed wrong, and nothing sounded clear."
    )


def reconciliation(world: World) -> None:
    archer = world.get("archer")
    colony = world.get("colony")
    target = world.get("ring")
    archer.memes["humility"] = 1.0
    colony.memes["trust"] = 1.0
    colony.memes["hurt"] = 0.0
    archer.memes["regret"] = 0.0
    world.say(
        f"Then {archer.label} brought back the reeds and fixed the bridge with careful art;"
    )
    world.say(
        f"'I guessed too fast,' he said at last, 'please let me mend my part.'"
    )
    world.say(
        f"The colony forgave his haste, and lanterns lit the evening sky;"
    )
    world.say(
        f"he shot one soft, clean practice arrow, and it sang a gentle rhyme nearby."
    )
    world.say(
        f"By moonlight, all were side by side; the bridge was sound, the ring was bright,"
    )
    world.say(
        f"and even the shyest beetle smiled to see the friendship mended right."
    )
    world.facts["resolved"] = True
    world.facts["ending_image"] = f"{archer.label} and {colony.label} standing together beside the bright ring"


def tell(params: StoryParams) -> World:
    world = make_world(params)
    world.say(
        f"In {world.setting.place}, where the {world.setting.colony_name.lower()} hummed in a hidden row,"
    )
    world.say(
        f"there lived {world.get('archer').label}, an archer who liked to aim and glow."
    )
    world.para()
    infer_misread(world)
    world.para()
    conflict(world)
    world.para()
    reconciliation(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    archer = f["archer"]
    colony = f["colony"]
    return [
        f"Write a rhyming story about {archer.label}, an archer, and {colony.label}, a colony, ending in reconciliation.",
        "Tell a short child-friendly rhyming tale where someone first misreads a small community, then makes amends.",
        "Write a sweet story with the words infer, archer, and colony, and end with everyone feeling friendly again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a = world.facts["archer"].label
    c = world.facts["colony"].label
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {a}, an archer, and {c}, a colony of tiny neighbors.",
        ),
        QAItem(
            question="What problem happened first?",
            answer="The archer misread the colony's busy sounds and thought they were upset, so feelings got hurt.",
        ),
        QAItem(
            question="How did they fix things at the end?",
            answer="The archer apologized, repaired the bridge, and the colony forgave him, so they became friends again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an archer do?",
            answer="An archer uses a bow to shoot arrows, usually at a target for practice or sport.",
        ),
        QAItem(
            question="What is a colony?",
            answer="A colony is a group of living things that stay together and share a home or place.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop arguing, make peace, and become friendly again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {e.label} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="the meadow edge", colony_name="the Bramble Colony", archer_name="Arin", colony_name2="the Bramble Colony"),
    StoryParams(place="the little stone arch", colony_name="the Clover Colony", archer_name="Milo", colony_name2="the Clover Colony"),
    StoryParams(place="the apple lane", colony_name="the Moss Colony", archer_name="Nia", colony_name2="the Moss Colony"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/0."))
        print("compatible story:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.archer_name} at {p.place} with {p.colony_name}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
