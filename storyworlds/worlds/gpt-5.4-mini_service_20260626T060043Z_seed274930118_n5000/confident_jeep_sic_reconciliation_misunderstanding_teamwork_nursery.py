#!/usr/bin/env python3
"""
storyworlds/worlds/confident_jeep_sic_reconciliation_misunderstanding_teamwork_nursery.py
========================================================================================

A tiny nursery-rhyme story world about a confident jeep, a small misunderstanding,
and a teamwork-fueled reconciliation.

Premise:
- A cheerful child and a friendly jeep want to visit a little hill.
- A misunderstanding blocks the way: the jeep thinks the bridge is too weak, while
  the others think the jeep is too proud to ask for help.

Turn:
- The group pauses, talks gently, and notices the real problem.
- One wheel is stuck in soft mud; nobody is in trouble, just stuck.

Resolution:
- With teamwork, they push, steer, and smooth the path.
- Everyone reconciles and goes home with a bright, rhyming ending image.

The script keeps the style child-facing and classical: beginning, middle turn,
and a concluding image that proves what changed.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the lane"
    detail: str = "a little lane with a small bridge and a muddy bend"


@dataclass
class StoryParams:
    setting: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _default_meters() -> dict[str, float]:
    return {"stuck": 0.0, "mud": 0.0, "joy": 0.0, "repair": 0.0}


def _default_memes() -> dict[str, float]:
    return {"confidence": 0.0, "misunderstanding": 0.0, "teamwork": 0.0, "reconciliation": 0.0}


def _r_stuck(world: World) -> list[str]:
    out: list[str] = []
    jeep = world.entities.get("jeep")
    if jeep and jeep.meters["stuck"] >= THRESHOLD and ("stuck",) not in world.fired:
        world.fired.add(("stuck",))
        out.append("The jeep gave a little squeak and stayed in the mud.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    jeep = world.entities.get("jeep")
    helper = world.entities.get("helper")
    if not child or not jeep or not helper:
        return out
    if child.memes["misunderstanding"] >= THRESHOLD and helper.memes["teamwork"] >= THRESHOLD:
        if ("reconcile",) in world.fired:
            return out
        world.fired.add(("reconcile",))
        child.memes["reconciliation"] += 1
        jeep.memes["reconciliation"] += 1
        out.append("The hard little worry melted into a warm hello.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_stuck, _r_reconcile):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING = Setting(
    place="the lane",
    detail="a little lane with a tiny bridge, a muddy bend, and reeds that nodded in the breeze",
)


def _build_world(params: StoryParams) -> World:
    world = World(SETTING)

    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.gender,
        label=params.name,
        meters=_default_meters(),
        memes=_default_memes(),
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label="the parent",
        meters=_default_meters(),
        memes=_default_memes(),
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="friend",
        label="the friend",
        meters=_default_meters(),
        memes=_default_memes(),
    ))
    jeep = world.add(Entity(
        id="jeep",
        kind="thing",
        type="jeep",
        label="jeep",
        phrase="a bright little jeep",
        meters=_default_meters(),
        memes=_default_memes(),
    ))

    child.memes["confidence"] += 1
    jeep.memes["confidence"] += 1
    world.facts["child"] = child
    world.facts["parent"] = parent
    world.facts["helper"] = helper
    world.facts["jeep"] = jeep
    world.facts["setting"] = params.setting
    world.facts["name"] = params.name

    world.say(
        f"Once upon a lane, there was {params.name}, a little {params.gender} with a brave heart, "
        f"and a bright little jeep that was always confident."
    )
    world.say(
        f"They loved to sing as they rolled by {world.setting.detail}, and the wheel tracks made a tidy little tune."
    )

    world.para()
    world.say(
        f"One day, {params.name} wanted to ride the jeep over the bridge, but the jeep stopped with a proud little hum."
    )
    world.say(
        f'“Sic, sic,” it seemed to say, as if the bridge were too small and the mud were too mean.'
    )
    jeep.memes["misunderstanding"] += 1
    child.memes["misunderstanding"] += 1
    world.facts["misunderstanding"] = True

    world.para()
    world.say(
        f"{params.name} thought the jeep was refusing to help, and the jeep thought everyone else was asking it to be too bold."
    )
    world.say(
        f"But the parent looked close and saw the real trouble: one wheel was sunk in soft mud."
    )
    jeep.meters["stuck"] += 1
    helper.memes["teamwork"] += 1
    child.memes["misunderstanding"] += 1
    propagate(world)

    world.para()
    world.say(
        f'The friend clapped and said, “Let us work together, little team, one push, one steer, one cheerful beam.”'
    )
    child.memes["teamwork"] += 1
    parent.memes["teamwork"] += 1
    jeep.memes["teamwork"] += 1
    jeep.meters["repair"] += 1
    world.say(
        f"{params.name} pushed from the back, the parent guided from the side, and the friend cleared the muddy bend."
    )
    world.say(
        f"The jeep’s wheel popped free, the misunderstanding slid away, and the whole group smiled at once."
    )
    jeep.meters["stuck"] = 0.0
    jeep.memes["misunderstanding"] = 0.0
    child.memes["misunderstanding"] = 0.0
    child.memes["reconciliation"] += 1
    jeep.memes["reconciliation"] += 1
    helper.memes["reconciliation"] += 1
    child.meters["joy"] += 1
    jeep.meters["joy"] += 1
    propagate(world)

    world.para()
    world.say(
        f"Then they rolled across the little bridge together, not rushed at all, just tidy and pleased."
    )
    world.say(
        f"And by the end of the day, the confident jeep and {params.name} were friends again, singing soft and slow beneath the sky."
    )

    world.facts["resolved"] = True
    return world


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    helper = world.facts["helper"]
    jeep = world.facts["jeep"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {child.label}, a little {child.type}, and a confident jeep on the lane.",
        ),
        QAItem(
            question=f"What went wrong with the jeep?",
            answer=f"The jeep got stuck in soft mud, and everyone first misunderstood what the trouble was.",
        ),
        QAItem(
            question=f"How did they fix the problem?",
            answer=f"{child.label}, the parent, and the friend used teamwork to push and steer the jeep free.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"The misunderstanding turned into reconciliation, and the confident jeep rolled on happily again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work together to do something that is hard alone.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people think the wrong thing about a problem or about each other.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset, make peace, and become friendly again.",
        ),
        QAItem(
            question="What is a jeep?",
            answer="A jeep is a sturdy little vehicle that can roll along rough paths and bumpy lanes.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    return [
        f"Write a nursery-rhyme story about {child.label}, a confident jeep, and a muddy lane.",
        "Tell a gentle tale where a misunderstanding is solved with teamwork and reconciliation.",
        "Write a short, rhyming, child-friendly story that includes the word sic and ends happily.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"{ent.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "lane"),
        asp.fact("theme", "nursery"),
        asp.fact("feature", "misunderstanding"),
        asp.fact("feature", "teamwork"),
        asp.fact("feature", "reconciliation"),
        asp.fact("entity", "child"),
        asp.fact("entity", "parent"),
        asp.fact("entity", "helper"),
        asp.fact("entity", "jeep"),
        asp.fact("confidence", "jeep"),
        asp.fact("vehicle", "jeep"),
        asp.fact("problem", "stuck"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
feature_present(F) :- feature(F).
story_valid :- feature_present(misunderstanding), feature_present(teamwork), feature_present(reconciliation).
#show story_valid/0.
#show feature_present/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_valid/0."))
    ok = any(sym.name == "story_valid" for sym in model)
    if ok:
        print("OK: ASP gate accepts the nursery-rhyme story world.")
        return 0
    print("MISMATCH: ASP gate rejected the story world.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme story world about a confident jeep.")
    ap.add_argument("--setting", choices=["lane"], default="lane")
    ap.add_argument("--name", default="Mina")
    ap.add_argument("--gender", choices=["girl", "boy"], default="girl")
    ap.add_argument("--parent", choices=["mother", "father"], default="mother")
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
    return StoryParams(
        setting=args.setting,
        name=args.name or rng.choice(["Mina", "Pip", "Lena", "Toby"]),
        gender=args.gender,
        parent=args.parent,
    )


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show story_valid/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(resolve_params(args, random.Random(base_seed + i))) for i in range(3)]
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
