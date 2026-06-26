#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/coop_seam_cautionary_foreshadowing_space_adventure.py
==============================================================================================================================

A small space-adventure story world about a child crew, a tiny coop module,
and a seam that starts as a warning and ends as a lesson.

The seed premise:
- A young astronaut loves a cozy animal coop on a compact ship.
- A narrow seam in the coop hatch has begun to hiss.
- A careful helper notices the first foreshadowing signs.
- A cautionary choice is made: slow down, patch the seam, and avoid a bigger
  problem in space.

The domain is intentionally small and constraint-checked:
- One ship, one critical seam, one warning, one repair, one resolution.
- The story should read like a complete miniature adventure, not an event log.
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
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"leak": 0.0, "damage": 0.0, "workload": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "caution": 0.0, "relief": 0.0, "hope": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    name: str
    place: str = "the ship"
    parts: set[str] = field(default_factory=lambda: {"cockpit", "coop", "hall", "airlock"})
    facts: dict = field(default_factory=dict)
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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

    def copy(self) -> "Ship":
        import copy
        c = Ship(self.name, self.place, set(self.parts))
        c.facts = dict(self.facts)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def _narrate(entity: Entity) -> str:
    return entity.label or entity.type


def foreshadow_text() -> str:
    return "The small hiss had been there for a while, like a whisper asking to be checked."


def caution_text() -> str:
    return "That was the kind of problem that could grow fast if nobody listened."


def repair_text() -> str:
    return "A patched seam can keep air where it belongs."


def inspect_seam(world: Ship, child: Entity, helper: Entity, seam: Entity) -> None:
    world.say(
        f"{child.id} and {helper.id} floated past the coop hatch and noticed the seam."
    )
    world.say(foreshadow_text())


def warn_about_seam(world: Ship, helper: Entity, child: Entity, seam: Entity) -> None:
    helper.memes["caution"] += 1
    child.memes["worry"] += 1
    world.say(
        f'"We should not ignore that seam," {helper.id} said. "{caution_text()}"'
    )


def get_tools(world: Ship, helper: Entity) -> Entity:
    tools = world.add(Entity(
        id="patch_kit",
        type="tool",
        label="patch kit",
        phrase="a small patch kit with tape and seal foam",
    ))
    tools.worn_by = helper.id
    return tools


def repair_seam(world: Ship, helper: Entity, seam: Entity, tools: Entity) -> None:
    if seam.meters["leak"] < THRESHOLD:
        return
    seam.meters["leak"] = 0.0
    seam.meters["damage"] = 0.0
    helper.memes["hope"] += 1
    world.say(
        f"{helper.id} used the {tools.label} to seal the seam."
    )
    world.say(repair_text())


def small_adventure(world: Ship, child: Entity, helper: Entity, coop: Entity, seam: Entity) -> None:
    world.say(
        f"{child.id} loved the little coop module because the rescued space chicks peeped softly there."
    )
    world.say(
        f"Even so, the seam by the hatch made the corridor feel careful and still."
    )


def pressure_event(world: Ship, seam: Entity) -> None:
    if seam.meters["leak"] >= THRESHOLD:
        world.say(
            "A cold breeze slipped through the crack, and the coop feathers fluttered."
        )


def resolve(world: Ship, child: Entity, helper: Entity, seam: Entity) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"After the patch, the coop stayed warm, the seam stayed closed, and {child.id} smiled at the safe little ship."
    )


def tell_story() -> Ship:
    world = Ship(name="Aurora Pebble", place="the ship")
    child = world.add(Entity(id="Mina", kind="character", type="girl", label="Mina"))
    helper = world.add(Entity(id="Rook", kind="character", type="pilot", label="Rook"))
    coop = world.add(Entity(
        id="coop", type="module", label="coop",
        phrase="a tiny animal coop built into the ship wall"
    ))
    seam = world.add(Entity(
        id="seam", type="fault", label="seam",
        phrase="a narrow seam near the hatch", meters={"leak": 1.0, "damage": 0.0, "workload": 0.0},
        memes={"worry": 0.0, "caution": 0.0, "relief": 0.0, "hope": 0.0}
    ))

    small_adventure(world, child, helper, coop, seam)
    world.para()
    inspect_seam(world, child, helper, seam)
    warn_about_seam(world, helper, child, seam)
    world.say("They stopped the game and listened carefully.")
    tools = get_tools(world, helper)
    world.say(f"{helper.id} fetched the {tools.label} before the leak could spread.")
    pressure_event(world, seam)
    repair_seam(world, helper, seam, tools)
    world.para()
    resolve(world, child, helper, seam)

    world.facts.update(child=child, helper=helper, coop=coop, seam=seam, tools=tools)
    return world


@dataclass
class StoryParams:
    seed: Optional[int] = None


def story_prompts(world: Ship) -> list[str]:
    return [
        "Write a short space-adventure story for a young child about a coop module and a seam that needs attention.",
        "Tell a gentle cautionary tale where a small leak is noticed early and repaired before it becomes a bigger problem.",
        "Write a foreshadowing-driven story about a child crew member who hears a hiss and learns to check the seam."
    ]


def story_qa(world: Ship) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    seam = f["seam"]
    coop = f["coop"]
    return [
        QAItem(
            question=f"What did {child.id} and {helper.id} notice near the coop hatch?",
            answer=f"They noticed the seam near the coop hatch, and it was making a tiny hiss."
        ),
        QAItem(
            question=f"Why did {helper.id} say not to ignore the seam?",
            answer="Because a small leak in space can grow into a bigger problem if nobody fixes it early."
        ),
        QAItem(
            question=f"What changed after the repair?",
            answer=f"The seam stopped leaking, the coop stayed warm, and the little ship felt safe again."
        ),
        QAItem(
            question=f"What was the coop for?",
            answer=f"It was a tiny animal coop for the rescued space chicks."
        ),
    ]


def world_knowledge_qa(world: Ship) -> list[QAItem]:
    return [
        QAItem(
            question="Why is a seam important on a ship?",
            answer="A seam is a joined line between parts. If it opens, air or water can leak through."
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful because something might be risky or go wrong."
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small hint that something important may happen later."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: Ship) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
coop(C) :- coop_module(C).
seam(S) :- seam_line(S).

risk(S) :- seam_line(S), leak(S, L), L > 0.
warn(C) :- observes(C, S), risk(S).
repair(S) :- risk(S), patch_kit(K), uses(K, S).
safe(S) :- seam_line(S), not risk(S).
"""

def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("coop_module", "coop"))
    lines.append(asp.fact("seam_line", "seam"))
    lines.append(asp.fact("leak", "seam", 1))
    lines.append(asp.fact("observes", "Mina", "seam"))
    lines.append(asp.fact("patch_kit", "patch_kit"))
    lines.append(asp.fact("uses", "patch_kit", "seam"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show risk/1. #show safe/1."))
    return sorted(set((a[0],) for a in asp.atoms(model, "risk")))


def asp_verify() -> int:
    python_risk = {"seam"} if tell_story().facts["seam"].meters["leak"] > 0 else set()
    clingo_risk = {x[0] for x in asp_valid()}
    if python_risk == clingo_risk:
        print("OK: ASP and Python agree on the seam risk.")
        return 0
    print("MISMATCH:")
    print("python:", sorted(python_risk))
    print("asp:", sorted(clingo_risk))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world about a coop seam and a careful repair.")
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
    return StoryParams(seed=args.seed if args.seed is not None else rng.randrange(1 << 30))


def generate(params: StoryParams) -> StorySample:
    world = tell_story()
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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
        print(asp_program("#show risk/1. #show safe/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show risk/1. #show safe/1."))
        print("risk:", asp.atoms(model, "risk"))
        print("safe:", asp.atoms(model, "safe"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(1 << 30)
    samples = []
    for i in range(args.n):
        params = resolve_params(args, random.Random(base_seed + i))
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
