#!/usr/bin/env python3
"""
storyworlds/worlds/wrench_bumble_reconciliation_sharing_conflict_heartwarming.py
=================================================================================

A small heartwarming story world about a child, a bumble of feelings, a shared
wrench, and a reconciliation that leaves everyone closer together.

Seed tale:
---
Two children find a wobbly garden cart with a loose bolt. Both want to help fix
it with the same little wrench. They bumble into a conflict, then learn to share
the tool and work together. The cart is repaired, the argument softens, and the
ending image is warm: siblings side by side, proud of what they made together.
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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the garden shed"
    affords: set[str] = field(default_factory=lambda: {"fix_cart"})


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    trouble: str
    repair: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    plural: bool = False


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    name1: str
    name2: str
    gender1: str
    gender2: str
    parent: str
    trait1: str
    trait2: str
    seed: Optional[int] = None


SETTING = Setting()
TASK = Task(
    id="fix_cart",
    verb="fix the wobbly garden cart",
    gerund="fixing the wobbly garden cart",
    trouble="the cart wheel kept bumping sideways",
    repair="the loose bolt could be tightened",
    keyword="wrench",
    tags={"wrench", "bumble", "sharing", "conflict", "reconciliation", "heartwarming"},
)
TOOL = Tool(
    id="wrench",
    label="little wrench",
    phrase="a little silver wrench",
    helps={"fix_cart"},
)


GIRL_NAMES = ["Mia", "Luna", "Ava", "Nora", "Zoe", "Ivy", "Maya", "Rose"]
BOY_NAMES = ["Eli", "Finn", "Leo", "Ben", "Noah", "Theo", "Max", "Sam"]
TRAITS = ["careful", "curious", "gentle", "brave", "lively", "thoughtful"]


def _do_fix(world: World, actor: Entity, narrate: bool = True) -> None:
    actor.meters["work"] = actor.meters.get("work", 0.0) + 1
    actor.meters["fix"] = actor.meters.get("fix", 0.0) + 1
    if narrate:
        world.say(f"{actor.id} leaned in and turned the bolt with care.")


def predict_conflict(world: World, first: Entity, second: Entity) -> bool:
    sim = world.copy()
    sim.get(first.id).memes["want_tool"] = 1.0
    sim.get(second.id).memes["want_tool"] = 1.0
    return True


def introduce(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"{child.id} was a little {next(t for t in [child.type] if t)} who liked "
        f"helping around {world.setting.place}."
    )
    world.say(
        f"{child.pronoun().capitalize()} had a patient {parent.type} who kept the tools tidy."
    )


def setup(world: World, child1: Entity, child2: Entity, parent: Entity) -> None:
    world.say(
        f"One afternoon, {child1.id} and {child2.id} found a wobbly garden cart near {world.setting.place}."
    )
    world.say(
        f"{TASK.trouble}, and {TASK.repair}."
    )
    child1.memes["curious"] = 1.0
    child2.memes["curious"] = 1.0
    world.facts["trouble"] = TASK.trouble
    world.facts["repair"] = TASK.repair


def want_tool(world: World, child: Entity) -> None:
    child.memes["want_tool"] = child.memes.get("want_tool", 0.0) + 1
    world.say(f"{child.id} wanted the little wrench first.")


def bumble_conflict(world: World, child1: Entity, child2: Entity) -> None:
    child1.memes["conflict"] = child1.memes.get("conflict", 0.0) + 1
    child2.memes["conflict"] = child2.memes.get("conflict", 0.0) + 1
    world.say(
        f"They both bumbled forward at once, and for a moment the air felt tight with conflict."
    )
    world.say(
        f"{child1.id} held the wrench. {child2.id} reached for it too, and neither wanted to let go."
    )


def reconcile(world: World, parent: Entity, child1: Entity, child2: Entity, tool: Tool) -> None:
    child1.memes["conflict"] = 0.0
    child2.memes["conflict"] = 0.0
    child1.memes["joy"] = child1.memes.get("joy", 0.0) + 1
    child2.memes["joy"] = child2.memes.get("joy", 0.0) + 1
    child1.memes["love"] = child1.memes.get("love", 0.0) + 1
    child2.memes["love"] = child2.memes.get("love", 0.0) + 1
    world.say(
        f"{parent.id} smiled and said they could share the wrench, one turn at a time."
    )
    world.say(
        f"{child1.id} handed {child2.pronoun('object')} the wrench after the first turn, and the argument softened."
    )
    world.say(
        f"They looked at each other, nodded, and let the work become a small reconciliation."
    )


def finish(world: World, child1: Entity, child2: Entity, parent: Entity) -> None:
    world.say(
        f"Together they tightened the bolt, and the cart stopped wobbling."
    )
    world.say(
        f"{child1.id} and {child2.id} laughed, wiping their hands on their sleeves while {parent.id} beamed beside them."
    )
    world.say(
        f"By the end, the little wrench had helped build more than a cart: it had helped the siblings share, make peace, and stay close."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    child1 = world.add(Entity(
        id=params.name1,
        kind="character",
        type="girl" if params.gender1 == "girl" else "boy",
        meters={"work": 0.0},
        memes={"curious": 1.0},
    ))
    child2 = world.add(Entity(
        id=params.name2,
        kind="character",
        type="girl" if params.gender2 == "girl" else "boy",
        meters={"work": 0.0},
        memes={"curious": 1.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label="parent",
    ))
    tool = world.add(Entity(
        id=TOOL.id,
        type="tool",
        label=TOOL.label,
        phrase=TOOL.phrase,
        owner=parent.id,
    ))

    introduce(world, child1, parent)
    world.para()
    setup(world, child1, child2, parent)
    want_tool(world, child1)
    want_tool(world, child2)
    bumble_conflict(world, child1, child2)
    world.para()
    reconcile(world, parent, child1, child2, tool)
    finish(world, child1, child2, parent)

    world.facts.update(
        child1=child1,
        child2=child2,
        parent=parent,
        tool=tool,
        task=TASK,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c1, c2, task = f["child1"], f["child2"], f["task"]
    return [
        f'Write a warm story for a young child about "{task.keyword}" and sharing a tool.',
        f"Tell a heartwarming story where {c1.id} and {c2.id} both want the same wrench while fixing a cart.",
        f"Write a gentle story with conflict, sharing, and reconciliation in a garden shed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c1, c2, parent, task, tool = f["child1"], f["child2"], f["parent"], f["task"], f["tool"]
    return [
        QAItem(
            question=f"What were {c1.id} and {c2.id} trying to do in the story?",
            answer=f"They were trying to {task.verb}. The cart had a wobble, so they needed the wrench.",
        ),
        QAItem(
            question=f"Why did the story have a conflict?",
            answer=f"There was conflict because both children wanted the same wrench at the same time.",
        ),
        QAItem(
            question=f"How did {parent.id} help?",
            answer=f"{parent.id} helped by reminding them to share the wrench one turn at a time.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, the children had reconciled, shared the wrench, and fixed the cart together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a wrench for?",
            answer="A wrench is a hand tool used to turn nuts and bolts tighter or looser.",
        ),
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let more than one person use the same thing kindly and fairly.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop arguing and make peace again.",
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    name1: str
    name2: str
    gender1: str
    gender2: str
    parent: str
    trait1: str
    trait2: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming story world about sharing a wrench.")
    ap.add_argument("--name1", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--name2", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--gender2", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait1", choices=TRAITS)
    ap.add_argument("--trait2", choices=TRAITS)
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
    gender1 = args.gender1 or rng.choice(["girl", "boy"])
    gender2 = args.gender2 or rng.choice(["girl", "boy"])
    name1 = args.name1 or rng.choice(GIRL_NAMES if gender1 == "girl" else BOY_NAMES)
    name2 = args.name2 or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != name1])
    parent = args.parent or rng.choice(["mother", "father"])
    trait1 = args.trait1 or rng.choice(TRAITS)
    trait2 = args.trait2 or rng.choice([t for t in TRAITS if t != trait1])
    return StoryParams(name1=name1, name2=name2, gender1=gender1, gender2=gender2,
                       parent=parent, trait1=trait1, trait2=trait2)


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


ASP_RULES = r"""
child(C) :- named(C).
wants_tool(C) :- child(C).
conflict(C1,C2) :- wants_tool(C1), wants_tool(C2), C1 != C2.
shares_tool(C1,C2) :- conflict(C1,C2), parent(P), shares(P,C1,C2).
reconciled(C1,C2) :- shares_tool(C1,C2).
heartwarming :- reconciled(C1,C2).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in GIRL_NAMES:
        lines.append(asp.fact("named", name))
    for name in BOY_NAMES:
        lines.append(asp.fact("named", name))
    lines.append(asp.fact("tool", TOOL.id))
    lines.append(asp.fact("parent", "parent"))
    lines.append(asp.fact("shares", "parent", "child1", "child2"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reconciled/2."))
    if asp.atoms(model, "reconciled"):
        print("OK: ASP model produced reconciliation.")
        return 0
    print("MISMATCH: ASP model did not produce reconciliation.")
    return 1


CURATED = [
    StoryParams("Mia", "Leo", "girl", "boy", "mother", "gentle", "curious"),
    StoryParams("Ava", "Nora", "girl", "girl", "father", "thoughtful", "lively"),
    StoryParams("Eli", "Ben", "boy", "boy", "mother", "brave", "careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reconciled/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
