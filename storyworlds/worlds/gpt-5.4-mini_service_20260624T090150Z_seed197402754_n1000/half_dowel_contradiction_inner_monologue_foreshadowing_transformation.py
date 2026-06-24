#!/usr/bin/env python3
"""
storyworlds/worlds/half_dowel_contradiction_inner_monologue_foreshadowing_transformation.py
=========================================================================================

A small bedtime-story world about a child, a wooden dowel, a gentle
contradiction, and a quiet transformation.

Premise:
- A child wants to make a moon-mobile before sleep.
- The craft needs a dowel, but the long dowel is too big for the little bed.
- The child faces a contradiction: half can mean "not enough," but it can also mean
  "just right" when something is shared or transformed.

Narrative instruments:
- Inner monologue: the child thinks through the worry.
- Foreshadowing: the parent notices the dowel's future use before the turn.
- Transformation: the long dowel becomes two useful parts, and the craft changes.

The story model is state-driven: meters track the physical dowel and craft pieces;
memes track worry, comfort, curiosity, and wonder. The ending image proves the
change by showing the finished bedtime scene.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    worn_by: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    bedtime: bool = True


@dataclass
class Dowel:
    id: str
    length: str
    meter_length: int
    can_split: bool = True


@dataclass
class CraftPlan:
    id: str
    label: str
    need: str
    result: str
    transform: str


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


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    parent_role: str
    seed: Optional[int] = None


SETTINGS = {
    "nursery": Setting("the nursery", bedtime=True),
    "worktable": Setting("the kitchen table", bedtime=True),
    "porch": Setting("the porch", bedtime=True),
}

CHILD_NAMES_GIRL = ["Mia", "Luna", "Nora", "Ivy", "Ella"]
CHILD_NAMES_BOY = ["Theo", "Milo", "Owen", "Ezra", "Noah"]
PARENT_ROLES = ["mother", "father"]

# Registries for the small domain
DOWELS = {
    "half_dowel": Dowel(id="half_dowel", length="half as long", meter_length=1, can_split=False),
    "long_dowel": Dowel(id="long_dowel", length="long and smooth", meter_length=2, can_split=True),
}

CRAFTS = {
    "moon_mobile": CraftPlan(
        id="moon_mobile",
        label="a moon mobile",
        need="a dowel",
        result="a little hanging moon",
        transform="turned into two smaller pieces that could hold the moons",
    ),
}


class ReasoningError(StoryError):
    pass


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise ReasoningError("The story needs a gentle bedtime place.")
    if params.child_gender not in {"girl", "boy"}:
        raise ReasoningError("The child should be a girl or a boy for this tiny world.")


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        label=params.child_name,
        memes={"curiosity": 1.0, "worry": 0.0, "comfort": 0.0, "wonder": 0.0, "sleepiness": 0.4},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent_role,
        label=f"the {params.parent_role}",
        memes={"calm": 1.0, "foresight": 1.0, "warmth": 1.0},
    ))
    dowel = world.add(Entity(
        id="dowel",
        type="dowel",
        label="wooden dowel",
        phrase="a smooth wooden dowel",
        meters={"length": 2.0, "whole": 1.0},
    ))
    moon = world.add(Entity(
        id="moon",
        type="moon",
        label="paper moon",
        phrase="a paper moon with a gold string",
        meters={"finished": 0.0},
    ))

    # Beginning
    world.say(
        f"At {world.setting.place}, {child.label} wanted to make {CRAFTS['moon_mobile'].label} before sleep."
    )
    world.say(
        f"{child.label} found {dowel.phrase} on the table and held {dowel.it()} like a secret."
    )

    # Foreshadowing
    world.para()
    parent.memes["foresight"] += 1.0
    world.say(
        f"The {params.parent_role} looked at the dowel and said softly, "
        f'"It may seem small later, but it can still become something useful."'
    )
    world.say(
        f"{child.label} nodded, yet a tiny contradiction tickled {child.pronoun('possessive')} mind: "
        f"how could half of a thing be enough?"
    )

    # Inner monologue + tension
    world.para()
    child.memes["worry"] += 1.0
    child.memes["curiosity"] += 1.0
    world.say(
        f"Inside, {child.label} thought, {repr('If I use half, will the moon mobile break?')}"
    )
    world.say(
        f"{child.label} stared at the long dowel and imagined it hanging above the bed like a quiet branch."
    )
    world.say(
        f"Then {child.label} noticed the nursery shelf, already waiting for little things to rest on it."
    )

    # Transformation
    world.para()
    if dowel.meters["whole"] >= THRESHOLD:
        dowel.meters["whole"] = 0.0
        dowel.meters["length"] = 1.0
        world.add(Entity(
            id="left_piece",
            type="dowel_piece",
            label="one half of the dowel",
            phrase="one neat half",
            meters={"length": 1.0, "useful": 1.0},
        ))
        world.add(Entity(
            id="right_piece",
            type="dowel_piece",
            label="the other half",
            phrase="the other neat half",
            meters={"length": 1.0, "useful": 1.0},
        ))
        world.say(
            f"The {params.parent_role} showed {child.label} that the dowel could be transformed instead of wasted."
        )
        world.say(
            f"They made two tidy halves, and each half found a job: one held the moons, and the other became a little hanger."
        )
    else:
        raise StoryError("This bedtime story needs a whole dowel so the transformation can happen.")

    # Resolution
    world.para()
    child.memes["worry"] = 0.0
    child.memes["comfort"] += 1.0
    child.memes["wonder"] += 1.0
    moon.meters["finished"] = 1.0
    world.say(
        f"At last, {child.label} smiled at the contradiction and understood it: half was not always less; sometimes it was just shared shape."
    )
    world.say(
        f"The moon mobile drifted gently above the bed, and {child.label} felt sleepy and proud as the room turned quiet and gold."
    )
    world.say(
        f"Before {child.label} closed {child.pronoun('possessive')} eyes, the two halves of the dowel hung like soft little lines under the moon."
    )

    world.facts.update(
        child=child,
        parent=parent,
        dowel=dowel,
        moon=moon,
        setting=world.setting,
        transformed=True,
        contradiction_resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f'Write a bedtime story for a young child named {child.label} about a half dowel and a gentle contradiction.',
        f"Tell a soothing story where {child.label} wonders whether half of a dowel can still help make something beautiful.",
        "Write a small bedtime tale that uses the words half, dowel, and contradiction, and ends with a cozy transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, dowel = f["child"], f["parent"], f["dowel"]
    return [
        QAItem(
            question=f"What did {child.label} want to make before sleep?",
            answer=f"{child.label} wanted to make a moon mobile before sleep.",
        ),
        QAItem(
            question=f"Why was there a contradiction in {child.label}'s mind about the dowel?",
            answer=(
                f"{child.label} wondered how half of a thing could be enough, even though the dowel still had a useful shape."
            ),
        ),
        QAItem(
            question=f"What did the {parent.type} say that foreshadowed the ending?",
            answer=(
                f"The {parent.type} said the dowel might seem small later, but it could still become something useful."
            ),
        ),
        QAItem(
            question=f"How did the dowel change in the story?",
            answer=(
                "The long dowel was transformed into two tidy halves, and each half got a job in the moon mobile."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dowel?",
            answer="A dowel is a straight wooden rod that people can use for building or craft projects.",
        ),
        QAItem(
            question="What does half mean?",
            answer="Half means one of two equal parts of a whole thing.",
        ),
        QAItem(
            question="What is a contradiction?",
            answer="A contradiction is when two ideas seem opposite, like thinking something is too small and also just right.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a new form or a new use.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA ==",]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "nursery"),
        asp.fact("place", "worktable"),
        asp.fact("place", "porch"),
        asp.fact("dowel", "half_dowel"),
        asp.fact("dowel", "long_dowel"),
        asp.fact("can_split", "long_dowel"),
        asp.fact("not_split", "half_dowel"),
        asp.fact("craft", "moon_mobile"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
% A dowel is in a contradiction when it is both too little for a worry and still
% useful after a transformation.
can_transform(D) :- dowel(D), can_split(D).
half_ok(D) :- dowel(D), not_split(D).

useful_half(D) :- half_ok(D).
useful_half(D) :- can_transform(D).

contradiction(D) :- half_ok(D), can_transform(D).

transformed(D) :- can_transform(D), useful_half(D).
#show contradiction/1.
#show transformed/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show contradiction/1.\n#show transformed/1."))
    atoms = set((a.name, tuple(str(x) for x in a.arguments)) for a in model)
    expected = {("contradiction", ("half_dowel",)), ("transformed", ("long_dowel",))}
    if atoms == expected:
        print("OK: ASP twin matches the Python reasoning gate.")
        return 0
    print("MISMATCH in ASP twin.")
    print("got:", sorted(atoms))
    print("expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime storyworld about half, a dowel, and a contradiction.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_ROLES)
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES_GIRL if gender == "girl" else CHILD_NAMES_BOY)
    parent = args.parent or rng.choice(PARENT_ROLES)
    return StoryParams(place=place, child_name=name, child_gender=gender, parent_role=parent)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
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
    StoryParams(place="nursery", child_name="Mia", child_gender="girl", parent_role="mother"),
    StoryParams(place="worktable", child_name="Theo", child_gender="boy", parent_role="father"),
    StoryParams(place="porch", child_name="Luna", child_gender="girl", parent_role="father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show contradiction/1.\n#show transformed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show contradiction/1.\n#show transformed/1."))
        print(sorted((a.name, tuple(str(x) for x in a.arguments)) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
