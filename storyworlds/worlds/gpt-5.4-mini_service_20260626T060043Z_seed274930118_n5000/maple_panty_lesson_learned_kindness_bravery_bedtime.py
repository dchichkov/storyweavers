#!/usr/bin/env python3
"""
A bedtime storyworld about a little child named Maple, a soft toy named Panty,
and a lesson learned about kindness and bravery at bedtime.

The world models a small nighttime domain:
- Maple wants comfort and sleep.
- Panty is a tiny plush with a brave little role.
- A worried moment at bedtime creates a chance to choose kindness.
- The ending proves a lesson learned by the changed state of the world.
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

BEDTIME_PLACES = {
    "bedroom": "the bedroom",
    "nursery": "the nursery",
    "attic_room": "the attic room",
    "treehouse": "the treehouse",
}

MOOD_WORDS = ["sleepy", "gentle", "quiet", "warm", "brave", "kind"]

ASP_RULES = r"""
% A bedtime worry can be soothed by kindness.
soothed(C) :- child(C), worried(C), kindness(K), K >= 1.

% A lesson learned appears when the child is brave and soothed.
lesson_learned(C) :- child(C), brave(C), soothed(C).

#show soothed/1.
#show lesson_learned/1.
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "child":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "toy":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    window_moonlight: bool = True
    bedtime: bool = True


@dataclass
class StoryParams:
    place: str
    name: str = "Maple"
    toy: str = "Panty"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime storyworld about kindness and bravery.")
    ap.add_argument("--place", choices=BEDTIME_PLACES)
    ap.add_argument("--name", default=None)
    ap.add_argument("--toy", default=None)
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


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("The child needs a name.")
    if not params.toy.strip():
        raise StoryError("The toy needs a name.")
    if params.place not in BEDTIME_PLACES:
        raise StoryError("That place does not belong in this bedtime world.")


def asp_facts() -> str:
    import asp
    lines = []
    for place in BEDTIME_PLACES:
        lines.append(asp.fact("place", place))
    lines.append(asp.fact("child", "Maple"))
    lines.append(asp.fact("toy", "Panty"))
    lines.append(asp.fact("kindness", 1))
    lines.append(asp.fact("brave", "Maple"))
    lines.append(asp.fact("worried", "Maple"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show soothed/1.\n#show lesson_learned/1."))
    atoms = set((sym.name, tuple(a.name if a.type != 2 else a.string for a in sym.arguments)) for sym in model)
    expected = {("soothed", ("Maple",)), ("lesson_learned", ("Maple",))}
    if atoms == expected:
        print("OK: ASP twin matches Python gate.")
        return 0
    print("MISMATCH:", atoms, expected)
    return 1


def setup_world(params: StoryParams) -> World:
    setting = Setting(place=BEDTIME_PLACES[params.place])
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="child", label=params.name, phrase=f"little {params.name}"))
    toy = world.add(Entity(id=params.toy, kind="toy", label=params.toy, phrase=f"soft toy {params.toy}", owner=child.id))
    child.carries = toy.id
    child.meters["sleepy"] = 0.0
    child.memes["kindness"] = 0.0
    child.memes["bravery"] = 0.0
    child.memes["worry"] = 0.0
    toy.memes["comfort"] = 1.0
    world.facts.update(child=child, toy=toy, place=setting.place)
    return world


def tell(world: World) -> None:
    child = world.get(world.facts["child"].id)
    toy = world.get(world.facts["toy"].id)

    world.say(
        f"At {world.setting.place}, Maple was getting sleepy, and the room felt soft and still."
    )
    world.say(
        f"Maple hugged {toy.label} close. The little toy had a silly name, but it felt safe in Maple's hands."
    )
    world.say(
        f"Then the moonlight slid across the floor, and Maple noticed {toy.label} had fallen near the bed."
    )
    child.memes["worry"] += 1
    child.memes["bravery"] += 1
    world.say(
        f"Maple felt a small bump of worry, but took a brave breath and reached down gently."
    )
    world.say(
        f"Instead of grabbing in a rush, Maple used kindness: {child.pronoun('subject').capitalize()} lifted {toy.label} carefully and brushed off the blanket fuzz."
    )
    child.memes["kindness"] += 1
    child.memes["worry"] = 0.0
    child.meters["sleepy"] += 1.0
    world.say(
        f"{toy.label} was back where it belonged, tucked beside Maple like a tiny guard for the dark."
    )
    world.say(
        f"Maple smiled into the pillow and learned a quiet lesson: kindness can make a brave heart feel calm."
    )
    world.facts["resolved"] = True
    world.facts["lesson_learned"] = True


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a bedtime story about Maple and {world.facts['toy'].label} that ends with a lesson learned.",
        "Tell a gentle bedtime tale where kindness helps a child feel brave.",
        "Write a short child-friendly story set in a quiet bedroom with a soft, comforting toy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    toy = world.facts["toy"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about Maple, a little child, and the soft toy {toy.label}.",
        ),
        QAItem(
            question=f"What did Maple learn at bedtime?",
            answer="Maple learned that kindness can help a brave heart feel calm and ready for sleep.",
        ),
        QAItem(
            question=f"How did Maple pick up {toy.label}?",
            answer=f"Maple picked up {toy.label} gently, instead of rushing, and that was the kind choice.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why do people keep a soft toy near the bed?",
            answer="A soft toy can feel comforting at bedtime and help a child feel safe.",
        ),
        QAItem(
            question="What does bravery mean in a bedtime story?",
            answer="Bravery means doing something a little scary or hard even when you feel nervous.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, caring, and helpful to someone or something.",
        ),
    ]


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
        lines.append(f"  {e.id} ({e.kind}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(BEDTIME_PLACES))
    name = args.name or "Maple"
    toy = args.toy or "Panty"
    params = StoryParams(place=place, name=name, toy=toy)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
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
        print(asp_program("#show soothed/1.\n#show lesson_learned/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show soothed/1.\n#show lesson_learned/1."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    samples: list[StorySample] = []
    if args.all:
        for place in BEDTIME_PLACES:
            params = StoryParams(place=place, name="Maple", toy="Panty", seed=base_seed)
            samples.append(generate(params))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### story {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
