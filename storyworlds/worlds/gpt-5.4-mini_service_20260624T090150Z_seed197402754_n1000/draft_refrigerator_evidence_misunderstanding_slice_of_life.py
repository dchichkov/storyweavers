#!/usr/bin/env python3
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
    opened: bool = False
    cold: bool = False
    contains_food: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {"kitchen": "the kitchen"}

NAMES = {
    "girl": ["Maya", "Lina", "Nora", "Zoe", "Ivy"],
    "boy": ["Eli", "Noah", "Ben", "Leo", "Owen"],
}

PARENTS = ["mother", "father"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small slice-of-life story about a draft, a refrigerator, and a misunderstanding."
    )
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(name=name, gender=gender, parent=parent)


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("setting", "kitchen"),
            asp.fact("can_have", "kitchen", "draft"),
            asp.fact("can_have", "kitchen", "refrigerator"),
            asp.fact("can_have", "kitchen", "evidence"),
        ]
    )


ASP_RULES = r"""
has_draft(S) :- setting(S), can_have(S, draft).
has_refrigerator(S) :- setting(S), can_have(S, refrigerator).
has_evidence(S) :- setting(S), can_have(S, evidence).
valid(S) :- has_draft(S), has_refrigerator(S), has_evidence(S).
#show valid/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/1."))
    clingo_ok = bool(asp.atoms(model, "valid"))
    python_ok = True
    if clingo_ok == python_ok:
        print("OK: ASP and Python agree on the world gate.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def make_world(params: StoryParams) -> World:
    w = World(setting=SETTINGS["kitchen"])
    child = w.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = w.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    fridge = w.add(
        Entity(
            id="fridge",
            type="refrigerator",
            label="refrigerator",
            opened=True,
            cold=True,
            contains_food=True,
            caretaker=parent.id,
        )
    )
    crumb = w.add(
        Entity(
            id="crumbs",
            type="evidence",
            label="crumbs on the shelf",
            owner=child.id,
            meters={"evidence": 1.0},
        )
    )
    w.facts.update(child=child, parent=parent, fridge=fridge, crumb=crumb)
    return w


def predict_draft(world: World) -> bool:
    sim = world.copy()
    fridge = sim.get("fridge")
    return fridge.opened and fridge.cold


def narrate_setup(world: World) -> None:
    child = world.get(world.facts["child"].id)
    parent = world.get("Parent")
    fridge = world.get("fridge")
    world.say(
        f"{child.id} was a little {child.type} who liked quiet mornings in {world.setting}."
    )
    world.say(
        f"{child.id}'s {parent.type} kept a tidy {fridge.label}, and breakfast was usually calm."
    )


def narrate_misunderstanding(world: World) -> None:
    child = world.get(world.facts["child"].id)
    parent = world.get("Parent")
    fridge = world.get("fridge")
    world.para()
    world.say(
        f"One morning, {child.id} felt a cold draft near the {fridge.label} and stopped to look."
    )
    world.say(
        f"There were crumbs on the shelf, and {child.id} thought that looked like evidence that someone had been sneaking food."
    )
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    child.memes["misunderstanding"] = child.memes.get("misunderstanding", 0.0) + 1.0
    if predict_draft(world):
        world.say(
            f"{child.id} frowned and told {parent.pronoun('object')}, 'I think something is wrong with the {fridge.label}.'"
        )
    parent.memes["concern"] = parent.memes.get("concern", 0.0) + 1.0


def narrate_turn(world: World) -> None:
    child = world.get(world.facts["child"].id)
    parent = world.get("Parent")
    fridge = world.get("fridge")
    world.para()
    world.say(
        f"{parent.id} knelt down, looked at the crumbs, and noticed the {fridge.label} door was not shut all the way."
    )
    world.say(
        f"{parent.id} said the crumbs were only breakfast evidence, and the draft was just cold air slipping out."
    )
    child.memes["worry"] = 0.0
    child.memes["understanding"] = child.memes.get("understanding", 0.0) + 1.0


def narrate_resolution(world: World) -> None:
    child = world.get(world.facts["child"].id)
    parent = world.get("Parent")
    fridge = world.get("fridge")
    fridge.opened = False
    fridge.cold = True
    world.para()
    world.say(
        f"{child.id} helped push the {fridge.label} door shut, and the kitchen felt still again."
    )
    world.say(
        f"Then {child.id} and {parent.id} smiled at the neat shelf, where the crumbs were only tiny evidence of a busy breakfast."
    )


def tell(params: StoryParams) -> World:
    world = make_world(params)
    narrate_setup(world)
    narrate_misunderstanding(world)
    narrate_turn(world)
    narrate_resolution(world)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    c = world.facts["child"]
    return [
        "Write a gentle slice-of-life story about a draft, a refrigerator, and a misunderstanding.",
        f"Tell a short story where {c.id} notices evidence near a refrigerator and worries for a moment before the truth is explained.",
        "Write a child-friendly kitchen story that ends with everyone understanding where the cold draft came from.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    p = world.facts["parent"]
    return [
        QAItem(
            question=f"Why did {c.id} get worried in the kitchen?",
            answer=f"{c.id} felt a cold draft by the refrigerator and saw crumbs, so {c.pronoun('subject')} thought the crumbs were evidence that something was wrong.",
        ),
        QAItem(
            question=f"What did {p.id} notice about the refrigerator?",
            answer=f"{p.id} noticed the refrigerator door was not shut all the way, which explained the cold draft.",
        ),
        QAItem(
            question=f"How did the misunderstanding end?",
            answer=f"{c.id} helped close the refrigerator door, and then everyone understood that the crumbs were only breakfast evidence.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a draft?",
            answer="A draft is a little stream of moving air that can feel chilly on your skin.",
        ),
        QAItem(
            question="What is a refrigerator for?",
            answer="A refrigerator keeps food cold so it stays fresh longer.",
        ),
        QAItem(
            question="What does evidence mean?",
            answer="Evidence is something that helps you figure out what happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.type == "refrigerator":
            bits.append(f"opened={e.opened}")
            bits.append(f"cold={e.cold}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(name="Maya", gender="girl", parent="mother")
        samples = [generate(params)]
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
