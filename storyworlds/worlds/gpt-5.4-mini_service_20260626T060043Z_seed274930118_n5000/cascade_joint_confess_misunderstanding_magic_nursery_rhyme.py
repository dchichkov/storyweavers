#!/usr/bin/env python3
"""
storyworlds/worlds/cascade_joint_confess_misunderstanding_magic_nursery_rhyme.py
=================================================================================

A tiny nursery-rhyme story world about a magical cascade, a joint toy, and a
misunderstanding that clears only after someone confesses.

The source seed imagines a child-sized scene:

- a soft little setting
- a shining magic cascade
- a shared joint object
- a misunderstanding that makes two friends feel wobbly
- a gentle confession that turns the rhyme toward peace

The world model tracks both:
- physical meters: sparkle, damp, tangled, safe
- emotional memes: joy, worry, misunderstanding, relief, trust

The story is always authored from simulated state, not from a frozen template.
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
    shared_with: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False


@dataclass
class StoryParams:
    setting: str
    name_a: str
    name_b: str
    gender_a: str
    gender_b: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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


def _mget(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _em(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _addm(e: Entity, key: str, val: float = 1.0) -> None:
    e.meters[key] = _mget(e, key) + val


def _adde(e: Entity, key: str, val: float = 1.0) -> None:
    e.memes[key] = _em(e, key) + val


SETTING = Setting(place="the moonlit nursery garden", indoor=False)

CHARACTER_NAMES = ["Lina", "Pip", "Milo", "Tessa", "Ned", "Mina"]
TRAITS = ["little", "bright-eyed", "curious", "gentle", "cheerful"]


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    shared: bool = True
    kind: str = "toy"


PRIZE = Toy(
    id="joint_toy",
    label="joint kite",
    phrase="a joint kite with a ribbon tail",
    shared=True,
)

MAGIC = {
    "cascade": {
        "label": "cascade",
        "verb": "cascade down",
        "noun": "a silver cascade",
        "sparkle": 1.0,
    },
    "magic": {
        "label": "magic",
        "verb": "glow",
        "noun": "a magic lantern",
        "sparkle": 1.0,
    },
}

ASP_RULES = r"""
#show valid_story/1.
setting(nursery_garden).
magic(cascade).
magic(magic).
shared(joint_toy).

valid_story(cascade_joint_confess_misunderstanding_magic_nursery_rhyme).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "nursery_garden"),
        asp.fact("setting_label", "nursery_garden", "the moonlit nursery garden"),
        asp.fact("magic", "cascade"),
        asp.fact("magic", "magic"),
        asp.fact("shared", "joint_toy"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _characters(world: World) -> list[Entity]:
    return [e for e in world.entities.values() if e.kind == "character"]


def _story_premise(world: World, a: Entity, b: Entity, toy: Entity) -> None:
    world.say(
        f"In {world.setting.place}, {a.id} and {b.id} were two little friends who loved to share {toy.phrase}."
    )
    world.say(
        f"Each night, a magic cascade of bright droplets could be seen near the old willow, and the air felt like a nursery rhyme."
    )
    _adde(a, "joy", 1)
    _adde(b, "joy", 1)
    _addm(toy, "safe", 1)
    _addm(toy, "sparkle", 1)


def _misunderstanding(world: World, a: Entity, b: Entity, toy: Entity) -> None:
    _adde(a, "misunderstanding", 1)
    _adde(b, "worry", 1)
    _addm(toy, "tangled", 1)
    world.para()
    world.say(
        f"One day, {a.id} saw the joint kite by the cascade and thought {b.id} had kept it all alone."
    )
    world.say(
        f"{a.id}'s heart grew small and cloudy, and {a.id} whispered, \"That does not feel kind at all.\""
    )
    world.say(
        f"But {b.id} had only tied the ribbon to stop it from slipping into the water."
    )


def _confess(world: World, a: Entity, b: Entity, toy: Entity) -> None:
    _adde(b, "courage", 1)
    _adde(a, "listening", 1)
    world.para()
    world.say(
        f"Then {b.id} took a breath and chose to confess."
    )
    world.say(
        f"\"I did not mean to hide our joint kite,\" {b.id} said. \"I thought the cascade would wash it away.\""
    )
    world.say(
        f"{a.id} blinked, then saw the ribbon knot and understood the mistake."
    )
    _adde(a, "relief", 1)
    _adde(b, "relief", 1)
    _adde(a, "trust", 1)
    _adde(b, "trust", 1)
    a.memes["misunderstanding"] = max(0.0, _em(a, "misunderstanding") - 1)
    b.memes["worry"] = max(0.0, _em(b, "worry") - 1)
    toy.meters["tangled"] = 0.0
    toy.meters["safe"] = 1.0


def _resolution(world: World, a: Entity, b: Entity, toy: Entity) -> None:
    world.para()
    world.say(
        f"Together they lifted the joint kite high, away from the wet grass and the shining cascade."
    )
    world.say(
        f"They laughed a soft little laugh, and the magic made the ribbon dance like a line in a rhyme."
    )
    world.say(
        f"In the end, {a.id} and {b.id} shared the kite, and the misunderstanding drifted off like mist."
    )
    _adde(a, "joy", 1)
    _adde(b, "joy", 1)
    _addm(toy, "sparkle", 1)
    _addm(toy, "safe", 1)


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    a = world.add(Entity(id=params.name_a, kind="character", type=params.gender_a))
    b = world.add(Entity(id=params.name_b, kind="character", type=params.gender_b))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    toy = world.add(Entity(id=PRIZE.id, kind="thing", label=PRIZE.label, phrase=PRIZE.phrase, plural=False))
    world.facts.update(a=a, b=b, parent=parent, toy=toy, setting=params.setting)
    _story_premise(world, a, b, toy)
    _misunderstanding(world, a, b, toy)
    _confess(world, a, b, toy)
    _resolution(world, a, b, toy)
    return world


def story_prompt(world: World) -> list[str]:
    a = world.facts["a"]
    b = world.facts["b"]
    return [
        "Write a gentle nursery rhyme about a magic cascade and a shared kite.",
        f"Tell a short story where {a.id} and {b.id} have a misunderstanding, then confess and make peace.",
        "Create a child-friendly rhyme with the words cascade, joint, confess, and magic.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a = world.facts["a"]
    b = world.facts["b"]
    toy = world.facts["toy"]
    return [
        QAItem(
            question=f"What did {a.id} and {b.id} share in the story?",
            answer=f"They shared {toy.phrase}, a joint kite that belonged to both of them.",
        ),
        QAItem(
            question=f"Why did {a.id} think there was a problem near the cascade?",
            answer=f"{a.id} misunderstood the scene and thought {b.id} had kept the kite all alone.",
        ),
        QAItem(
            question=f"What changed the feeling in the story after the misunderstanding?",
            answer=f"{b.id} confessed the truth, and that honest confession turned worry into relief.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cascade?",
            answer="A cascade is a flowing fall of water, like a small waterfall spilling down in a shining stream.",
        ),
        QAItem(
            question="What does confess mean?",
            answer="To confess means to tell the truth about something, especially when you need to admit a mistake.",
        ),
        QAItem(
            question="What does joint mean in this story?",
            answer="Joint means shared by two people, so the kite belonged to both friends together.",
        ),
        QAItem(
            question="What does magic do in a nursery rhyme kind of story?",
            answer="Magic makes the scene feel wondrous and unusual, like the moonlight itself is helping the rhyme along.",
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
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="garden", name_a="Lina", name_b="Pip", gender_a="girl", gender_b="boy", parent="mother"),
    StoryParams(setting="nursery", name_a="Mina", name_b="Milo", gender_a="girl", gender_b="boy", parent="father"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about cascade, joint, confess.")
    ap.add_argument("--setting", choices=["garden", "nursery"], default=None)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--gender-b", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    setting = args.setting or rng.choice(["garden", "nursery"])
    name_a = args.name_a or rng.choice(CHARACTER_NAMES)
    name_b = args.name_b or rng.choice([n for n in CHARACTER_NAMES if n != name_a])
    gender_a = args.gender_a or rng.choice(["girl", "boy"])
    gender_b = args.gender_b or ("boy" if gender_a == "girl" else "girl")
    parent = args.parent or rng.choice(["mother", "father"])
    if name_a == name_b:
        raise StoryError("The two friends must have different names.")
    return StoryParams(setting=setting, name_a=name_a, name_b=name_b, gender_a=gender_a, gender_b=gender_b, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=story_prompt(world),
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


def asp_valid() -> list[tuple[str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("cascade_joint_confess_misunderstanding_magic_nursery_rhyme",)}
    cl = set(asp_valid())
    if py == cl:
        print("OK: clingo gate matches Python gate (1 story).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 10):
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
