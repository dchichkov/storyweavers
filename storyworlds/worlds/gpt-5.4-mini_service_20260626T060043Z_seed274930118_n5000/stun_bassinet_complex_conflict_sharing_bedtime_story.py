#!/usr/bin/env python3
"""
storyworlds/worlds/stun_bassinet_complex_conflict_sharing_bedtime_story.py
=========================================================================

A small bedtime-story world about a child, a shared bassinet, and a gentle
conflict that turns into sharing.

Seed image:
---
In a quiet apartment complex, a sleepy child wanted to help with the baby’s
bedtime. The child loved the soft bassinet by the window and wanted to share it
with a stuffed friend named Stun. But the bassinet was only big enough for the
baby, and the child felt upset. After a small pause, the parent found a kind
way to share: the child could rock the bassinet, sing the lullaby, and keep
Stun in a blanket nest nearby.

World model:
---
    setting.charge            -> how bright/busy the place feels at bedtime
    child.memes["want_share"]  -> desire to share the bassinet or bedtime task
    child.memes["conflict"]    -> feeling when the wish meets a limit
    baby.meters["rest"]        -> how sleepy and settled the baby is
    bassinet.meters["sway"]    -> how much the bassinet has been rocked
    shared.memes["warmth"]     -> how safe and cozy the sharing feels

Story instruments:
---
    conflict -> a warning, a disappointed pause, and a need for a better plan
    sharing  -> taking turns, making a cozy nest, and helping the baby sleep
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the apartment complex"
    cozy: bool = True


@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_type: str
    parent_type: str
    baby_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


SETTING = Setting(place="the apartment complex", cozy=True)

CHILDREN = {
    "girl": ["Mina", "Lily", "Nora", "Ella", "Maya"],
    "boy": ["Theo", "Leo", "Finn", "Noah", "Ben"],
}

PARENTS = ["mother", "father"]

BABY_NAMES = ["Ollie", "Ivy", "June", "Pip", "Toby"]


@dataclass
class Bassinet:
    label: str = "bassinet"
    phrase: str = "a soft little bassinet by the window"


@dataclass
class Companion:
    label: str = "Stun"
    phrase: str = "a stuffed bunny named Stun"


ASP_RULES = r"""
% A shared bedtime plan is valid when the bassinet is for the baby and the
% child can help without crowding the baby.
can_share(B, Child) :- bassinet(B), child(Child), not too_small(B).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "apartment_complex"))
    lines.append(asp.fact("bassinet", "bassinet"))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("baby", "baby"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bedtime story world about sharing a bassinet in an apartment complex."
    )
    ap.add_argument("--setting", choices=["apartment_complex"], default="apartment_complex")
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=PARENTS)
    ap.add_argument("--baby-name")
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
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILDREN[child_type])
    parent_type = args.parent_type or rng.choice(PARENTS)
    baby_name = args.baby_name or rng.choice(BABY_NAMES)
    return StoryParams(
        setting=args.setting,
        child_name=child_name,
        child_type=child_type,
        parent_type=parent_type,
        baby_name=baby_name,
    )


def _build_world(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.child_type,
        label=params.child_name,
        meters={"sleepiness": 0.0},
        memes={"want_share": 0.0, "conflict": 0.0, "care": 1.0, "joy": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent_type,
        label=params.parent_type,
        meters={"tiredness": 0.0},
        memes={"warmth": 1.0, "patience": 1.0},
    ))
    baby = world.add(Entity(
        id="baby",
        kind="character",
        type="baby",
        label=params.baby_name,
        meters={"rest": 0.0},
        memes={"coziness": 0.0},
        owner="parent",
    ))
    bassinet = world.add(Entity(
        id="bassinet",
        kind="thing",
        type="bassinet",
        label="bassinet",
        phrase="a soft little bassinet by the window",
        caretaker="parent",
        owner="baby",
        meters={"sway": 0.0},
        memes={"coziness": 1.0},
    ))
    stun = world.add(Entity(
        id="stun",
        kind="thing",
        type="stuffed-toy",
        label="Stun",
        phrase="a stuffed bunny named Stun",
        owner="child",
        meters={"softness": 1.0},
        memes={"comfort": 1.0},
    ))
    world.facts.update(child=child, parent=parent, baby=baby, bassinet=bassinet, stun=stun)
    return world


def _predict_overfull(world: World) -> bool:
    return world.get("child").memes["want_share"] >= THRESHOLD


def _do_story(world: World) -> None:
    c = world.get("child")
    p = world.get("parent")
    b = world.get("baby")
    bs = world.get("bassinet")
    st = world.get("stun")

    world.say(
        f"{c.label} lived in {world.setting.place} and loved bedtime because the halls got quiet and the windows turned blue."
    )
    world.say(
        f"Each night, {c.label} liked to help with {b.label}'s sleep, especially near {bs.phrase}."
    )
    world.say(
        f"{c.label} also loved {st.label}, the {st.phrase}, and wanted to share the bassinet with {st.label}."
    )
    c.memes["want_share"] += 1.0
    world.para()

    world.say(
        f"That night, {c.label} came close to the bassinet and asked to tuck {st.label} inside too."
    )
    if _predict_overfull(world):
        world.say(
            f"{p.label.capitalize()} shook their head gently. 'The bassinet is just right for {b.label},' {p.label} said."
        )
        c.memes["conflict"] += 1.0
        c.meters["stillness"] = 0.0
        world.say(
            f"{c.label} felt a little stunned by the answer and held {st.label} tight."
        )
        world.say(
            f"For a moment, the room went quiet and the wish to share turned into a small frown."
        )
    world.para()

    c.memes["care"] += 1.0
    p.memes["warmth"] += 1.0
    b.meters["rest"] += 1.0
    bs.meters["sway"] += 1.0

    world.say(
        f"Then {p.label} found a sweeter way to share."
    )
    world.say(
        f"{c.label} could rock the bassinet, sing the soft song, and keep {st.label} in a little blanket nest beside the bed."
    )
    c.memes["conflict"] = 0.0
    c.memes["joy"] += 1.0
    b.meters["rest"] += 1.0
    bs.meters["sway"] += 1.0
    world.say(
        f"{c.label} smiled, because now {c.pronoun()} was helping, {st.label} had a cozy place, and {b.label} drifted off without a peep."
    )
    world.say(
        f"In the apartment complex, the blue night stayed calm, and the shared bedtime felt warm as a tucked-in hug."
    )

    world.facts.update(resolved=True)


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    _do_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["child"]
    b = f["baby"]
    return [
        f'Write a gentle bedtime story about {c.label} in {world.setting.place} who wants to share a bassinet with a stuffed friend named Stun.',
        f"Tell a bedtime story where {c.label} feels a small conflict, then learns a kind way to share {b.label}'s bassinet.",
        "Write a child-friendly story that uses the words stun, bassinet, and complex, and ends with a cozy sharing idea.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c = f["child"]
    p = f["parent"]
    b = f["baby"]
    bs = f["bassinet"]
    st = f["stun"]
    return [
        QAItem(
            question=f"Where did {c.label} live in this story?",
            answer=f"{c.label} lived in {world.setting.place}, and it felt quiet and cozy at bedtime.",
        ),
        QAItem(
            question=f"What did {c.label} want to share with {st.label}?",
            answer=f"{c.label} wanted to share the bassinet with {st.label}, even though the bassinet was really for {b.label}.",
        ),
        QAItem(
            question=f"Why was there a small conflict at bedtime?",
            answer=f"There was a small conflict because {c.label} wanted {st.label} in the bassinet, but {p.label} said the bassinet was just right for {b.label}.",
        ),
        QAItem(
            question=f"How did the family solve the problem?",
            answer=f"They solved it by letting {c.label} rock the bassinet and keep {st.label} in a blanket nest beside the bed, so everyone could share the bedtime calmly.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {c.label} felt happy, {b.label} was sleepy, and the bassinet kept swaying gently in the warm, quiet room.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bassinet for?",
            answer="A bassinet is a small bed for a baby to sleep in during the night.",
        ),
        QAItem(
            question="What does it mean to share something?",
            answer="To share means to let more than one person use, enjoy, or help with something in a kind way.",
        ),
        QAItem(
            question="What is an apartment complex?",
            answer="An apartment complex is a place with many homes close together, where many families live.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {e.label} {' '.join(bits)}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_share/2."))
    _ = model
    print("OK: ASP twin loaded and solved.")
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        setting=args.setting,
        child_name=args.child_name or rng.choice(CHILDREN[args.child_type or rng.choice(["girl", "boy"])]),
        child_type=args.child_type or rng.choice(["girl", "boy"]),
        parent_type=args.parent_type or rng.choice(PARENTS),
        baby_name=args.baby_name or rng.choice(BABY_NAMES),
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_share/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show can_share/2."))
        print(asp.atoms(model, "can_share"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
