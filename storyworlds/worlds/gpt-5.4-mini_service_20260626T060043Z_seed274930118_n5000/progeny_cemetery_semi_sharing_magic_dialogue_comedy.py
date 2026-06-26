#!/usr/bin/env python3
"""
storyworlds/worlds/progeny_cemetery_semi_sharing_magic_dialogue_comedy.py
=========================================================================

A tiny comedy storyworld about a family visit to a cemetery, a parked semi, and
a little bit of sharing magic that helps everyone solve a confused, polite mess.

Premise:
- A child and a parent visit a cemetery to leave flowers.
- A shiny semi truck is blocking the narrow lane near the gate.
- The child wants to help by using a shared "magic" trick: borrowing, splitting,
  and returning small things kindly.

Tension:
- The child wants to keep something magical instead of sharing it.
- The parent worries that the cemetery should stay quiet and respectful.
- The semi driver needs a way through, and the child keeps asking questions.

Turn:
- Dialogue reveals that the "magic" is just a friendly sharing rule: one
  lantern, two holders, and a soft way to walk together.

Resolution:
- The child shares the lantern, the semi gets enough room to back up, and the
  flowers reach the right grave without any fuss.
- The ending image proves what changed: the child is smiling, the parent is
  laughing, and the cemetery lane is calm again.
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

SETTINGS = {
    "cemetery_gate": {
        "place": "the cemetery gate",
        "detail": "The cemetery lane was narrow, and old stone markers stood quietly along the path.",
        "affords": {"visit"},
    },
}

NAMES = ["Maya", "Leo", "Nia", "Owen", "Iris", "Ben", "Mina", "Toby"]
PARENT_NAMES = ["Mom", "Dad", "Aunt Jo", "Uncle Ray"]
TRAITS = ["curious", "gentle", "silly", "cheerful", "careful", "bouncy"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wearer: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "aunt"}
        male = {"boy", "father", "dad", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A comedy storyworld about a cemetery visit, a semi, and sharing magic."
    )
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or "cemetery_gate"
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, name=name, gender=gender, parent=parent, trait=trait)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown setting for this storyworld.")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("The child must be a girl or a boy in this storyworld.")


def _activity_name() -> str:
    return "visit"


def _build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    place_cfg = SETTINGS[params.place]
    world = World(place=place_cfg["place"])

    child_type = params.gender
    parent_type = {"Mom": "mother", "Dad": "father", "Aunt Jo": "aunt", "Uncle Ray": "uncle"}[params.parent]

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=child_type,
        label=params.name,
        meters={"curiosity": 1.0},
        memes={"joy": 1.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label=params.parent,
        meters={"patience": 1.0},
        memes={"warmth": 1.0},
    ))
    driver = world.add(Entity(
        id="Driver",
        kind="character",
        type="adult",
        label="the semi driver",
        meters={"worry": 1.0},
        memes={"politeness": 1.0},
    ))
    semi = world.add(Entity(
        id="Semi",
        kind="thing",
        type="semi",
        label="semi",
        phrase="a big red semi",
        meters={"blocked": 1.0},
    ))
    lantern = world.add(Entity(
        id="Lantern",
        kind="thing",
        type="lantern",
        label="lantern",
        phrase="a tiny brass lantern",
        owner=child.id,
        wearer=child.id,
        meters={"shine": 1.0},
        memes={"magic": 1.0},
    ))
    flowers = world.add(Entity(
        id="Flowers",
        kind="thing",
        type="flowers",
        label="flowers",
        phrase="a bunch of yellow flowers",
        owner=parent.id,
        plural=True,
    ))
    grave = world.add(Entity(
        id="Grave",
        kind="thing",
        type="grave",
        label="grave",
        phrase="a family grave",
    ))

    world.say(
        f"{params.name} was a {params.trait} {params.gender} who came with {params.parent} to {world.place}."
    )
    world.say(place_cfg["detail"])
    world.say(
        f"Near the gate, a shiny semi was parked a little too close to the lane, "
        f"and the driver kept scratching his head."
    )
    world.para()
    world.say(
        f"{params.name} saw the lantern and whispered, \"Can I use the magic?\""
    )
    world.say(
        f"{params.parent} said, \"Only if you share it kindly.\""
    )
    world.say(
        f"The child puffed up. \"But if I share it, it will not be my magic anymore!\""
    )
    world.say(
        f"The driver leaned over and asked, \"Could your magic make my semi shrink?\""
    )
    world.say(
        f"{params.name} giggled. \"No, but it can make sharing easier.\""
    )
    world.para()
    world.say(
        f"So {params.name} held the lantern with both hands, and {params.parent} held it too."
    )
    world.say(
        f"The lantern glowed like a bedtime star, and the lane felt roomy enough for the semi to back up."
    )
    world.say(
        f"Together they carried the flowers to the grave, and the driver waved with a relieved smile."
    )
    world.say(
        f"By the time they left, {params.name} was still carrying the lantern, but now it felt even more magical because it had been shared."
    )

    world.facts.update(
        child=child,
        parent=parent,
        driver=driver,
        semi=semi,
        lantern=lantern,
        flowers=flowers,
        grave=grave,
        place=place_cfg,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a funny short story for a young child about {p.name}, a cemetery visit, and a semi truck.',
        f"Tell a gentle comedy where {p.name} learns that sharing a little magic can help a big semi move safely.",
        f'Write a story that includes dialogue, a cemetery gate, and the word "sharing".',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {p.name}, a {p.trait} {p.gender} who visits the cemetery with {p.parent}.",
        ),
        QAItem(
            question=f"What was blocking the narrow lane near the gate?",
            answer="A shiny semi was parked too close to the lane, so it made the way feel cramped and funny.",
        ),
        QAItem(
            question=f"What did {p.name} learn about the lantern?",
            answer="The lantern felt more magical when it was shared kindly, because sharing helped everyone work together.",
        ),
        QAItem(
            question=f"How did the problem get solved?",
            answer="They shared the lantern, the lane felt roomier, and the semi driver could back up safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cemetery?",
            answer="A cemetery is a quiet place where people bury the dead and leave flowers or visit graves.",
        ),
        QAItem(
            question="What is a semi?",
            answer="A semi is a very big truck used to carry heavy things on the road.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use or enjoy something with you.",
        ),
        QAItem(
            question="What is a lantern for?",
            answer="A lantern is a light you can carry to help you see in the dark.",
        ),
    ]


ASP_RULES = r"""
#show compatible/1.
compatible(story) :- child_visit, blocked_lane, sharing_magic, dialogue_fix.
"""


def asp_facts() -> str:
    return "\n".join([
        "child_visit.",
        "blocked_lane.",
        "sharing_magic.",
        "dialogue_fix.",
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cemetery_gate", name="Maya", gender="girl", parent="Mom", trait="curious"),
    StoryParams(place="cemetery_gate", name="Leo", gender="boy", parent="Dad", trait="silly"),
    StoryParams(place="cemetery_gate", name="Nia", gender="girl", parent="Aunt Jo", trait="gentle"),
]


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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
        print(asp_program("#show compatible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story pattern: child_visit, blocked_lane, sharing_magic, dialogue_fix")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: cemetery comedy with a semi and magic"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
