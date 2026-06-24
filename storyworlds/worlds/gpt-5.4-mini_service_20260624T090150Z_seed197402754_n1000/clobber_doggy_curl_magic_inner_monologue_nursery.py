#!/usr/bin/env python3
"""
A tiny nursery-rhyme story world about a little child, a clumsy clobber,
a doggy with a curl, and a bit of magic that helps them make things right.

The world is intentionally small and classical:
- one setting
- one problem
- one feeling beat via inner monologue
- one magical turn
- one gentle resolution
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


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
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
    place: str = "the little cottage"
    vibe: str = "warm and snug"


@dataclass
class StoryParams:
    place: str = "cottage"
    child_name: str = "Mia"
    child_type: str = "girl"
    pet_name: str = "Pip"
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Reasonable tiny domain
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Toy:
    id: str
    label: str
    kind: str


@dataclass(frozen=True)
class MagicTool:
    id: str
    label: str
    effect: str
    poem: str


SETTINGS = {
    "cottage": Setting(place="the little cottage", vibe="warm and snug"),
    "garden": Setting(place="the tiny garden", vibe="bright and breezy"),
}

TOYS = {
    "ball": Toy(id="ball", label="red ball", kind="round toy"),
    "balloon": Toy(id="balloon", label="blue balloon", kind="floaty toy"),
    "ribbon": Toy(id="ribbon", label="silver ribbon", kind="shiny ribbon"),
}

MAGIC = MagicTool(
    id="sparkle",
    label="a sprinkle of magic",
    effect="unclobber",
    poem="Twinkle, twinkle, little spark, make the bumping neat and dark",
)

GENTLE_VERBS = [
    "bounced",
    "tapped",
    "nudged",
    "clapped",
]


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(Setting(place=SETTINGS[params.place].place, vibe=SETTINGS[params.place].vibe))

    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    pet = world.add(Entity(id=params.pet_name, kind="character", type="dog"))
    toy = world.add(Entity(id="toy", kind="thing", type=TOYS["ribbon"].kind, label=TOYS["ribbon"].label))
    magic = world.add(Entity(id="magic", kind="thing", type="magic", label=MAGIC.label))

    child.memes["joy"] = 1
    pet.memes["tail_wag"] = 1
    pet.meters["curl"] = 1
    toy.meters["held"] = 1
    world.facts.update(child=child, pet=pet, toy=toy, magic=magic)
    return world


def clobber_event(world: World) -> None:
    child = world.get(world.facts["child"].id)
    pet = world.get(world.facts["pet"].id)
    toy = world.get(world.facts["toy"].id)

    child.memes["oops"] = child.memes.get("oops", 0) + 1
    pet.memes["startled"] = pet.memes.get("startled", 0) + 1
    toy.meters["bent"] = toy.meters.get("bent", 0) + 1

    world.say(
        f"In {world.setting.place}, {child.id} gave a little {random.choice(GENTLE_VERBS)} and went "
        f"clobber-clatter by mistake."
    )
    world.say(
        f"{pet.id} curled up tight, and the shiny ribbon got a wrinkly bend."
    )


def inner_monologue(world: World) -> None:
    child = world.get(world.facts["child"].id)
    pet = world.get(world.facts["pet"].id)
    toy = world.get(world.facts["toy"].id)

    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(
        f"{child.id} thought, 'Oh dear, I clobbered the pretty ribbon. "
        f"{pet.id} looks small and sad. I should help now.'"
    )
    world.say(
        f"{child.id} thought again, 'A kind fix is better than a noisy fuss.'"
    )
    world.facts["need_fix"] = toy.meters.get("bent", 0) > 0


def magic_fix(world: World) -> None:
    child = world.get(world.facts["child"].id)
    pet = world.get(world.facts["pet"].id)
    toy = world.get(world.facts["toy"].id)
    magic = world.get(world.facts["magic"].id)

    child.memes["hope"] = child.memes.get("hope", 0) + 1
    toy.meters["bent"] = 0
    toy.meters["bright"] = toy.meters.get("bright", 0) + 1
    pet.memes["startled"] = 0
    pet.memes["cozy"] = pet.memes.get("cozy", 0) + 1

    world.say(
        f"{child.id} whispered, '{MAGIC.poem}.'"
    )
    world.say(
        f"With {magic.label}, the ribbon straightened soft and neat, "
        f"as if it had never been clobbered at all."
    )
    world.say(
        f"{pet.id} unc curled, gave a happy woof, and wagged right by {child.id}'s feet."
    )


def ending_image(world: World) -> None:
    child = world.get(world.facts["child"].id)
    pet = world.get(world.facts["pet"].id)
    toy = world.get(world.facts["toy"].id)

    world.say(
        f"So {child.id} sat in {world.setting.place}, holding the red ball and the shiny ribbon, "
        f"while {pet.id} curled up nearby with a sleepy grin."
    )
    world.say(
        f"And the little cottage felt warm and snug, with a tidy toy, a happy doggy, and no more clobber at all."
    )
    world.facts["resolved"] = True
    world.facts["toy_fixed"] = toy.meters.get("bent", 0) == 0


def tell(params: StoryParams) -> World:
    world = build_world(params)
    world.say(
        f"{params.child_name} lived in {world.setting.place}, where every nook felt {world.setting.vibe}."
    )
    world.say(
        f"{params.child_name} loved a doggy named {params.pet_name}, and {params.pet_name} loved to curl into a round, soft ball."
    )
    world.para()
    clobber_event(world)
    world.para()
    inner_monologue(world)
    magic_fix(world)
    world.para()
    ending_image(world)
    return world


# ---------------------------------------------------------------------------
# Registries and parameters
# ---------------------------------------------------------------------------
NAMES = ["Mia", "Lily", "Nora", "Theo", "Finn", "Ava"]
DOGGY_NAMES = ["Pip", "Buddy", "Mochi", "Clover", "Poppy"]

PARAMS = {
    "place": ["cottage", "garden"],
    "child_type": ["girl", "boy"],
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child_worries(C) :- child(C), clobbers(C, T), pet(P), curled(P), toy(T).
toy_fixed(T) :- toy(T), clobbers(C, T), magic(M), chant(C, M).
resolved(C, T) :- child(C), toy_fixed(T), pet(P), curled(P), magic(M), chant(C, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for tid in TOYS:
        lines.append(asp.fact("toy", tid))
    lines.append(asp.fact("magic", MAGIC.id))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("pet", "pet"))
    lines.append(asp.fact("curled", "pet"))
    lines.append(asp.fact("clobbers", "child", "toy"))
    lines.append(asp.fact("chant", "child", MAGIC.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolved/2."))
    return sorted(set(asp.atoms(model, "resolved")))


def asp_verify() -> int:
    py = {("child", "toy")}
    cl = set(asp_valid())
    if cl == py:
        print("OK: ASP and Python agree on the tiny resolution.")
        return 0
    print("Mismatch between ASP and Python:", sorted(cl), sorted(py))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    c = world.facts["child"]
    p = world.facts["pet"]
    return [
        f"Write a nursery-rhyme story about {c.id}, a doggy named {p.id}, and a little clobber that gets fixed by magic.",
        f"Tell a soft story where {c.id} has an inner monologue after clobbering {p.id}'s ribbon.",
        f"Write a rhyme about a doggy who curls up, a mistake, and a magical kind ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    p = world.facts["pet"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {c.id}, a little child who lived with a doggy named {p.id}.",
        ),
        QAItem(
            question=f"What happened after {c.id} clobbered the ribbon?",
            answer=f"{p.id} curled up, the ribbon got wrinkly, and {c.id} felt sorry and thought kindly about what to do next.",
        ),
        QAItem(
            question=f"How was the problem fixed?",
            answer=f"{c.id} used a sprinkle of magic, and the ribbon straightened soft and neat again.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {p.id} cozy and happy, and the toy and ribbon all tidy again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a doggy?",
            answer="A doggy is a dog, a friendly animal that can wag its tail, curl up, and stay close to people.",
        ),
        QAItem(
            question="What does it mean to clobber something?",
            answer="To clobber something means to bump or hit it hard enough to mess it up.",
        ),
        QAItem(
            question="What can magic do in a nursery story?",
            answer="Magic can help fix trouble in a gentle, pretend way, like making a wrinkled ribbon straight again.",
        ),
        QAItem(
            question="What is a curl?",
            answer="A curl is a bend or round shape, like a doggy curling up into a cozy little ball.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme story world with clobber, doggy, curl, magic, and inner monologue.")
    ap.add_argument("--place", choices=PARAMS["place"])
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--pet-name", choices=DOGGY_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    place = args.place or rng.choice(PARAMS["place"])
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice([n for n in NAMES if (gender == "girl") == (n in {"Mia", "Lily", "Nora", "Ava"})])
    pet_name = args.pet_name or rng.choice(DOGGY_NAMES)
    return StoryParams(place=place, child_name=name, child_type=gender, pet_name=pet_name)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in PARAMS["place"]:
            for name in NAMES[:2]:
                p = StoryParams(place=place, child_name=name, child_type="girl" if name in {"Mia", "Lily", "Nora", "Ava"} else "boy", pet_name="Pip")
                samples.append(generate(p))
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
