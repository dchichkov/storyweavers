#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/poem_ginormous_twist_bedtime_story.py
===============================================================================================================

A small bedtime-story world about a child, a poem, and a ginormous twist in
the blankets that must be untangled before sleep.

The seed tale imagines a child who wants one more poem at bedtime, but a huge
twist in the blanket makes the room feel wrong and a little tense. A calm grownup
helps untwist the bed, the child shares a tiny poem, and the room settles into
quiet.

The world is intentionally small: one child, one caregiver, one cozy room,
one bedtime object that can tangle, and one gentle resolution.
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

TITLE_WORDS = ("poem", "ginormous")
FEATURE_WORD = "Twist"


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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    name: str = "the bedroom"
    quiet: bool = False
    cozy: bool = True


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.twist: float = 0.0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(copy.deepcopy(self.room))
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.twist = self.twist
        return clone


@dataclass
class StoryParams:
    name: str
    gender: str
    caregiver: str
    blanket: str
    toy: str
    seed: Optional[int] = None


NAMES = ["Mia", "Leo", "Nora", "Eli", "Ava", "Theo", "Luna", "Finn"]
CAREgIVERS = ["mother", "father"]
BLANKETS = {
    "blue_blanket": ("a soft blue blanket", "blanket"),
    "star_blanket": ("a blanket with tiny stars", "blanket"),
    "striped_blanket": ("a striped bedtime blanket", "blanket"),
}
TOYS = {
    "twist": ("Twist", "a curled toy snake named Twist"),
    "bunny": ("Bun", "a floppy bunny named Bun"),
    "bear": ("Milo", "a round bear named Milo"),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with a poem and a ginormous twist.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=CAREgIVERS)
    ap.add_argument("--blanket", choices=BLANKETS)
    ap.add_argument("--toy", choices=TOYS)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    caregiver = args.caregiver or rng.choice(CAREgIVERS)
    blanket = args.blanket or rng.choice(list(BLANKETS))
    toy = args.toy or "twist"
    return StoryParams(name=name, gender=gender, caregiver=caregiver, blanket=blanket, toy=toy)


def _make_world(params: StoryParams) -> World:
    world = World(Room())
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    adult = world.add(Entity(id="Caregiver", kind="character", type=params.caregiver, label=params.caregiver))
    blanket_label, _ = BLANKETS[params.blanket]
    toy_name, toy_phrase = TOYS[params.toy]
    blanket = world.add(Entity(
        id="blanket",
        label=blanket_label,
        phrase=blanket_label,
        owner=child.id,
        caretaker=adult.id,
        meters={"twist": 0.0, "cozy": 1.0},
        memes={"calm": 0.0},
    ))
    toy = world.add(Entity(
        id="toy",
        label=toy_name,
        phrase=toy_phrase,
        owner=child.id,
        meters={"twist": 0.0},
    ))
    toy.attrs["name"] = toy_name
    world.facts = {"child": child, "adult": adult, "blanket": blanket, "toy": toy, "params": params}
    return world


def _wish_for_poem(world: World) -> None:
    child = world.facts["child"]
    child.memes["sleepiness"] = child.memes.get("sleepiness", 0.0) + 0.5
    child.memes["want_poem"] = child.memes.get("want_poem", 0.0) + 1.0
    world.say(f"{child.id} was tucked into the bedroom and asked for one more poem before sleep.")
    world.say(f"The room was cozy, and the last little light made the shadows look soft.")


def _twist_grows(world: World) -> None:
    blanket = world.facts["blanket"]
    child = world.facts["child"]
    blanket.meters["twist"] += 1.0
    world.twist += 1.0
    child.memes["unease"] = child.memes.get("unease", 0.0) + 1.0
    world.say(
        f"But the blanket had a ginormous twist in it, and {child.id} kept kicking at the knot instead of settling down."
    )
    world.say(f"The twist made the bed feel lumpy, as if sleep had hidden under the sheets and refused to come out.")


def _calm_fix(world: World) -> None:
    child = world.facts["child"]
    adult = world.facts["adult"]
    blanket = world.facts["blanket"]
    toy = world.facts["toy"]
    blanket.meters["twist"] = 0.0
    world.twist = 0.0
    child.memes["unease"] = max(0.0, child.memes.get("unease", 0.0) - 1.0)
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1.0
    world.say(
        f"{adult.label.capitalize()} sat beside the bed, untwisted the blanket with gentle fingers, and picked up {toy.label}."
    )
    world.say(
        f'"Let’s make the twist smaller first," {adult.label} said, "and then we can keep the poem quiet and tiny."'
    )
    world.say(
        f"{child.id} smiled, whispered a short poem about a moonbeam, and tucked {toy.label} under the blanket."
    )


def _sleep_settles(world: World) -> None:
    child = world.facts["child"]
    adult = world.facts["adult"]
    blanket = world.facts["blanket"]
    child.memes["sleepiness"] = child.memes.get("sleepiness", 0.0) + 1.0
    world.room.quiet = True
    world.say(
        f"After that, the blanket lay smooth, the room turned still, and {child.id}'s eyelids grew heavy."
    )
    world.say(
        f"{adult.label.capitalize()} listened to the last sleepy breath, and the bedtime poem drifted away like a feather."
    )
    world.say(
        f"At the end, the ginormous twist was gone, the blanket was soft again, and the room was full of hush."
    )


def generate_world(params: StoryParams) -> World:
    world = _make_world(params)
    _wish_for_poem(world)
    world.para()
    _twist_grows(world)
    world.para()
    _calm_fix(world)
    _sleep_settles(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    toy = f["toy"].label
    return [
        f'Write a bedtime story for a young child that includes the words "{TITLE_WORDS[0]}" and "{TITLE_WORDS[1]}".',
        f"Tell a gentle story about {params.name}, a {params.gender} child, who wants one more poem at bedtime while {toy} and a blanket cause trouble.",
        f"Write a cozy story where a caregiver helps untwist a ginormous knot in a blanket so a child can fall asleep.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]
    child = f["child"]
    adult = f["adult"]
    toy = f["toy"]
    blanket = f["blanket"]
    return [
        QAItem(
            question=f"What did {child.id} want before sleep?",
            answer=f"{child.id} wanted one more poem before bedtime, because the room was still and the child was not ready to drift off yet.",
        ),
        QAItem(
            question=f"What made bedtime feel hard at first?",
            answer=f"A ginormous twist in the blanket made the bed lumpy and kept {child.id} from settling down.",
        ),
        QAItem(
            question=f"How did {adult.label} help?",
            answer=f"{adult.label.capitalize()} untwisted the blanket, calmed the room, and helped make the bedtime poem feel small and safe.",
        ),
        QAItem(
            question=f"What happened to {toy.label} by the end?",
            answer=f"{toy.label} was tucked under the blanket again, and the whole bed became soft and cozy.",
        ),
        QAItem(
            question=f"What changed in the room after the twist was fixed?",
            answer=f"The room grew quiet, the blanket lay smooth, and {params.name} grew sleepy enough to fall asleep.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a poem?",
            answer="A poem is a short piece of writing that may rhyme or have a special rhythm and can sound lovely when read aloud.",
        ),
        QAItem(
            question="What does ginormous mean?",
            answer="Ginormous means very, very big, much bigger than something ordinary.",
        ),
        QAItem(
            question="What does untwist mean?",
            answer="To untwist something is to turn it back the other way so it is no longer tangled or twisted up.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  twist={world.twist}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Mia", gender="girl", caregiver="mother", blanket="star_blanket", toy="twist"),
    StoryParams(name="Leo", gender="boy", caregiver="father", blanket="blue_blanket", toy="bunny"),
    StoryParams(name="Luna", gender="girl", caregiver="mother", blanket="striped_blanket", toy="bear"),
]


ASP_RULES = r"""
story_ready(C) :- child(C), wants_poem(C), twist(big_blanket), helped(C), calm_room.
calm_room :- untwisted(blanket), tucked(toy), quiet(room).
big_twist :- twist(blanket), ginormous(blanket).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in NAMES:
        lines.append(asp.fact("child", name))
    for k in BLANKETS:
        lines.append(asp.fact("blanket", k))
    for k in TOYS:
        lines.append(asp.fact("toy_kind", k))
    lines.append(asp.fact("word", TITLE_WORDS[0]))
    lines.append(asp.fact("word", TITLE_WORDS[1]))
    lines.append(asp.fact("feature", FEATURE_WORD))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Lazy import per contract.
    import asp
    program = asp_program("#show big_twist/0.")
    model = asp.one_model(program)
    if asp.atoms(model, "big_twist"):
        print("OK: ASP program compiles and derives big_twist/0.")
        return 0
    print("MISMATCH: ASP did not derive expected atom.")
    return 1


def build_story(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_validity(args: argparse.Namespace) -> None:
    if args.toy and args.toy not in TOYS:
        raise StoryError("Unknown toy choice.")
    if args.blanket and args.blanket not in BLANKETS:
        raise StoryError("Unknown blanket choice.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show big_twist/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show big_twist/0."))
        print(f"big_twist atoms: {asp.atoms(model, 'big_twist')}")
        return

    resolve_validity(args)
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [build_story(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = build_story(params)
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: bedtime with {p.blanket} and {p.toy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
