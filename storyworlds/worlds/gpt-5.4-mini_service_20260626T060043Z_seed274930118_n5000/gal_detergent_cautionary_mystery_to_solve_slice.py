#!/usr/bin/env python3
"""
A small storyworld about a gal, a bottle of detergent, and a gentle mystery to solve.

Premise:
A child notices a strange soapy mess in the laundry room. Something spilled,
clothes are not getting clean, and the family has to figure out what happened
without making a bigger mess.

Cautionary turn:
Detergent is useful, but too much of it can leave slippery residue and make a
floor unsafe. The child has to investigate carefully, clean up, and choose the
right amount.

Slice-of-life style:
The story stays close to home and daily routines: sorting laundry, checking a
cap, wiping a counter, and asking a neighborly question.

World model:
- physical meters: spill, mess, wetness, cleanliness, safety, tiredness
- emotional memes: curiosity, worry, relief, pride, care
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("spill", "mess", "wetness", "cleanliness", "safety", "tiredness"):
            self.meters.setdefault(key, 0.0)
        for key in ("curiosity", "worry", "relief", "pride", "care"):
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = True


@dataclass
class StoryParams:
    place: str
    name: str
    parent: str
    helper: str
    detergent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _story_begins(world: World, gal: Entity, parent: Entity, detergent: Entity) -> None:
    world.say(
        f"{gal.id} liked the quiet hum of the laundry room and the warm smell of clean towels."
    )
    world.say(
        f"One afternoon, {gal.pronoun('possessive')} {parent.label} brought home a new bottle of {detergent.label}."
    )
    world.say(
        f"{gal.id} watched the bottle like it was a clue, because it said to use only a little."
    )


def _mystery_turn(world: World, gal: Entity, parent: Entity, detergent: Entity) -> None:
    gal.memes["curiosity"] += 1
    gal.memes["worry"] += 1
    detergent.meters["spill"] += 1
    detergent.meters["mess"] += 1
    world.say(
        f"Later, {gal.id} found a soapy streak on the floor and a drippy ring near the washer."
    )
    world.say(
        f"That was odd: {detergent.label} was useful for washing clothes, but a spill could make the tiles slippery."
    )
    world.say(
        f"{gal.id} knelt down and looked for the source instead of stepping right through it."
    )


def _solve(world: World, gal: Entity, parent: Entity, helper: Entity, detergent: Entity) -> None:
    gal.memes["care"] += 1
    parent.memes["care"] += 1
    helper.memes["care"] += 1
    detergent.meters["cleanliness"] += 1
    detergent.meters["spill"] = 0.0
    detergent.meters["mess"] = 0.0
    detergent.meters["safety"] += 1
    gal.memes["relief"] += 1
    gal.memes["pride"] += 1
    world.say(
        f"{gal.id} asked {parent.pronoun('possessive')} {parent.label} and {helper.id} what happened."
    )
    world.say(
        f"They found the answer: the cap had not been tightened all the way, so a little {detergent.label} had dripped out."
    )
    world.say(
        f"{helper.id} showed {gal.id} how to close the lid firmly, wipe the puddle, and keep the bottle high on the shelf."
    )


def _ending(world: World, gal: Entity, parent: Entity, detergent: Entity) -> None:
    world.say(
        f"After that, {gal.id} measured carefully, used only the right amount, and watched the suds vanish down the drain."
    )
    world.say(
        f"The laundry got clean, the floor stayed safe, and the shiny bottle of {detergent.label} waited quietly for next time."
    )
    world.say(
        f"{gal.id} felt proud because {gal.pronoun()} had solved the little mystery without making the room messier."
    )


SETTINGS = {
    "laundry_room": Setting(place="the laundry room", indoor=True),
    "bathroom": Setting(place="the bathroom", indoor=True),
    "basement": Setting(place="the basement laundry nook", indoor=True),
}

GIRL_NAMES = ["Nina", "Maya", "Lina", "Pia", "Rosa", "Tia", "Ivy", "Zuri"]
PARENT_LABELS = {
    "mother": "mom",
    "father": "dad",
    "guardian": "guardian",
}
HELPERS = {
    "neighbor": "Ms. Bell",
    "sibling": "Jules",
    "grandparent": "Grandma",
}
DETERGENT_LABELS = [
    "detergent",
    "laundry detergent",
    "a blue bottle of detergent",
    "a bottle of detergent",
]


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    gal = world.add(Entity(id=params.name, kind="character", type="girl", label="gal"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=PARENT_LABELS[params.parent]))
    helper = world.add(Entity(id="Helper", kind="character", type="woman", label=HELPERS[params.helper]))
    detergent = world.add(Entity(
        id="Detergent",
        kind="thing",
        type="detergent",
        label=params.detergent,
        phrase=params.detergent,
        caretaker=parent.id,
    ))

    world.facts.update(gal=gal, parent=parent, helper=helper, detergent=detergent, params=params)

    _story_begins(world, gal, parent, detergent)
    world.para()
    _mystery_turn(world, gal, parent, detergent)
    world.para()
    _solve(world, gal, parent, helper, detergent)
    world.para()
    _ending(world, gal, parent, detergent)

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    gal = f["gal"]
    parent = f["parent"]
    detergent = f["detergent"]
    return [
        f"Write a short slice-of-life story about a gal named {gal.id} who notices {detergent.label} in the laundry room.",
        f"Tell a gentle cautionary mystery where {gal.id} and {parent.label} solve a detergent spill safely.",
        f"Write a child-friendly story about careful cleaning, a small clue, and using {detergent.label} the right way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    gal: Entity = f["gal"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    detergent: Entity = f["detergent"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is about {gal.id}, a curious gal who notices a small mystery in the laundry room."
        ),
        QAItem(
            question=f"What odd thing did {gal.id} find?",
            answer=f"{gal.id} found a soapy streak and a little spill of {detergent.label} on the floor."
        ),
        QAItem(
            question=f"Why was the detergent spill a problem?",
            answer=(
                f"The spill was a problem because detergent can make the floor slippery, "
                f"so people needed to clean it up carefully before anyone slipped."
            ),
        ),
        QAItem(
            question=f"How did {gal.id} help solve the mystery?",
            answer=(
                f"{gal.id} asked questions, looked for the source of the drip, and helped fix the bottle cap "
                f"so the room could stay safe and clean."
            ),
        ),
        QAItem(
            question=f"Who showed {gal.id} the safer way to handle the bottle?",
            answer=f"{helper.id} showed {gal.id} how to close the lid firmly, wipe the spill, and put {detergent.label} back up high."
        ),
    ]


KNOWLEDGE = [
    QAItem(
        question="What is detergent used for?",
        answer="Detergent is used to wash clothes and help remove dirt and stains.",
    ),
    QAItem(
        question="Why should detergent be measured carefully?",
        answer="If you use too much detergent, it can leave sticky suds or make a slippery mess.",
    ),
    QAItem(
        question="What should you do if a cleaning bottle spills?",
        answer="If a cleaning bottle spills, you should ask an adult, wipe it up, and keep people away from the slippery spot.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}): {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life cautionary mystery about detergent.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name", choices=GIRL_NAMES)
    ap.add_argument("--parent", choices=PARENT_LABELS.keys())
    ap.add_argument("--helper", choices=HELPERS.keys())
    ap.add_argument("--detergent", choices=DETERGENT_LABELS)
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
    name = args.name or rng.choice(GIRL_NAMES)
    parent = args.parent or rng.choice(list(PARENT_LABELS.keys()))
    helper = args.helper or rng.choice(list(HELPERS.keys()))
    detergent = args.detergent or rng.choice(DETERGENT_LABELS)
    return StoryParams(place=place, name=name, parent=parent, helper=helper, detergent=detergent)


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
place(laundry_room). place(bathroom). place(basement).
detergent(detergent). detergent(laundry_detergent). detergent(blue_bottle). detergent(bottle).

careful(X) :- detergent(X).
mystery(X) :- detergent(X).
cautionary(X) :- detergent(X).
slice_of_life(X) :- place(X).

#show careful/1.
#show mystery/1.
#show cautionary/1.
#show slice_of_life/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for d in DETERGENT_LABELS:
        # normalize labels to stable atoms
        atom = d.replace(" ", "_").replace("a_", "").replace("an_", "")
        atom = atom.replace("a_", "")
        lines.append(asp.fact("detergent", atom))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show cautionary/1. #show mystery/1. #show slice_of_life/1."))
    atoms = asp.atoms(model, "cautionary")
    if atoms:
        print("OK: ASP loaded and produced a model.")
        return 0
    print("ASP verification failed.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show cautionary/1. #show mystery/1. #show slice_of_life/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams(place="laundry_room", name="Nina", parent="mother", helper="neighbor", detergent="detergent"),
            StoryParams(place="bathroom", name="Maya", parent="father", helper="sibling", detergent="laundry detergent"),
            StoryParams(place="basement", name="Lina", parent="mother", helper="grandparent", detergent="a blue bottle of detergent"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
