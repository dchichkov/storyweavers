#!/usr/bin/env python3
"""
A standalone storyworld: a pirate tale on a muddy slope, with a mystery to
solve, a bit of sharing, and a touch of magic.

The seed tale behind this world:
---
A small pirate crew found a muddy slope beside the harbor. Their little chest
held a strange deposit stamped with a blue star. No one knew where it came
from. A pediatric healer nearby said the chest should be opened carefully, but
the crew first had to solve the mystery of the glowing deposit, share the tools
fairly, and trust a little magic to guide them uphill.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "girl-pirate"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "boy-pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the muddy slope"


@dataclass
class StoryParams:
    name: str
    crew_name: str
    helper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


SETTING = Setting(place="the muddy slope")

NAMES = ["Finn", "Mira", "Pip", "Nell", "Ari", "Cora", "Bo", "Tess"]
CREW = ["the little crew", "the salty crew", "the bright crew"]
HELPERS = ["Dr. Marina", "Nurse Nell", "Captain Reed", "Aunt June"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld: muddy slope, mystery, sharing, magic.")
    ap.add_argument("--name")
    ap.add_argument("--crew-name")
    ap.add_argument("--helper-name")
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
    name = args.name or rng.choice(NAMES)
    crew_name = args.crew_name or rng.choice(CREW)
    helper_name = args.helper_name or rng.choice(HELPERS)
    return StoryParams(name=name, crew_name=crew_name, helper_name=helper_name)


def _build_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id="hero", kind="character", type="boy-pirate", label=params.name))
    crew = world.add(Entity(id="crew", kind="character", type="pirate-crew", label=params.crew_name, plural=True))
    helper = world.add(Entity(id="helper", kind="character", type="doctor", label=params.helper_name))
    chest = world.add(Entity(id="chest", type="chest", label="little chest"))
    deposit = world.add(Entity(id="deposit", type="deposit", label="blue-star deposit"))
    map_piece = world.add(Entity(id="map", type="map", label="muddy map scrap"))
    lantern = world.add(Entity(id="lantern", type="lantern", label="gold lantern"))
    charm = world.add(Entity(id="charm", type="charm", label="glimmer charm"))

    hero.memes["curious"] = 1
    crew.memes["hope"] = 1
    helper.memes["calm"] = 1
    chest.meters["closed"] = 1
    deposit.meters["glow"] = 1
    deposit.meters["mystery"] = 1
    map_piece.meters["mud"] = 1
    lantern.meters["light"] = 1
    charm.meters["magic"] = 1

    world.facts.update(hero=hero, crew=crew, helper=helper, chest=chest,
                       deposit=deposit, map_piece=map_piece, lantern=lantern, charm=charm)
    return world


def tell(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    crew: Entity = f["crew"]
    helper: Entity = f["helper"]
    chest: Entity = f["chest"]
    deposit: Entity = f["deposit"]
    map_piece: Entity = f["map_piece"]
    lantern: Entity = f["lantern"]
    charm: Entity = f["charm"]

    world.say(f"On the muddy slope by the harbor, {hero.label} and {crew.label} found a little chest.")
    world.say(f"Inside it lay a strange deposit, a blue-star deposit that shimmered like moonlight on wet planks.")
    world.say(f"{hero.label} wanted to know where it came from, because every pirate likes a mystery to solve.")

    world.para()
    world.say(f"The crew shared the work fair and square: one held the chest, one held the lantern, and {hero.label} brushed mud from a map scrap.")
    world.say(f"The map scrap pointed uphill, where the mud slid under boots and the wind sang like a sea shanty.")
    world.say(f"Then {helper.label}, a pediatric doctor with a kind smile, said the glowing deposit should be checked carefully.")

    world.para()
    world.say(f"{hero.label} tapped the chest, but the lock only clicked when {crew.label} shared the lantern with the charm.")
    world.say(f"The charm gave a tiny flash of magic, and the blue-star deposit glowed brighter, as if it liked being noticed kindly.")
    world.say(f"That light showed a hidden path in the mud, and the mystery was not scary anymore.")

    world.para()
    world.say(f"Up the slope, the chest opened wide. The deposit was not treasure to hoard, but a safe hospital token for a child in need.")
    world.say(f"{helper.label} thanked the crew, and {hero.label} shared the token at once.")
    world.say(f"By sunset, the muddy slope looked shiny and calm, and the pirates sailed on with empty hands and happy hearts.")


def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a short pirate tale for a young child that takes place on {world.setting.place} and includes the word "deposit".',
        f"Tell a story where {world.facts['hero'].label} and {world.facts['crew'].label} solve a mystery, share their tools, and use magic on a muddy slope.",
        f'Write a gentle pirate story that includes a pediatric doctor, a glowing deposit, and a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    crew: Entity = f["crew"]
    helper: Entity = f["helper"]
    return [
        QAItem(
            question=f"Where did {hero.label} and {crew.label} find the chest?",
            answer=f"They found it on the muddy slope by the harbor.",
        ),
        QAItem(
            question=f"What was strange about the deposit in the chest?",
            answer="It was a blue-star deposit that shimmered and glowed like moonlight.",
        ),
        QAItem(
            question=f"Who told the crew to check the deposit carefully?",
            answer=f"{helper.label}, a pediatric doctor, told them to check it carefully.",
        ),
        QAItem(
            question="How did the crew solve the mystery?",
            answer="They shared the lantern and charm, and the magic flash showed a hidden path in the mud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a deposit?",
            answer="A deposit is something placed or left somewhere, like a kept token or a sum put in a safe place.",
        ),
        QAItem(
            question="What does pediatric mean?",
            answer="Pediatric means about children and their health or medical care.",
        ),
        QAItem(
            question="Why do people share tools?",
            answer="People share tools so everyone can help, and so one person does not have to do all the work alone.",
        ),
        QAItem(
            question="Why do stories use magic?",
            answer="Magic can make a story wonder-filled and help characters discover things they could not see before.",
        ),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% This world is small and deterministic; the ASP twin only checks a few
% reasonableness relations.
mystery_needed :- deposit(glow), deposit(mystery).
sharing_needed :- crew(shared,tools).
magic_needed :- charm(magic).
good_story :- mystery_needed, sharing_needed, magic_needed.
#show good_story/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("deposit", "glow"),
        asp.fact("deposit", "mystery"),
        asp.fact("crew", "shared", "tools"),
        asp.fact("charm", "magic"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/0."))
    ok = any(sym.name == "good_story" for sym in model)
    if ok:
        print("OK: ASP twin agrees the story has mystery, sharing, and magic.")
        return 0
    print("MISMATCH: ASP twin did not find a good_story.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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


CURATED = [
    StoryParams(name="Finn", crew_name="the little crew", helper_name="Dr. Marina"),
    StoryParams(name="Mira", crew_name="the salty crew", helper_name="Nurse Nell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_story/0."))
        print("good_story" if any(sym.name == "good_story" for sym in model) else "(none)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
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
        if args.all:
            p = sample.params
            header = f"### {p.name} on the muddy slope"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
