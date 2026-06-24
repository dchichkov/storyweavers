#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T082828Z_seed779406221_n50/hip_addition_inner_monologue_kindness_superhero_story.py
==============================================================================================================================

A tiny superhero storyworld about a young hero, a helpful new addition to the
costume, and a choice between showing off and being kind.

Seed tale sketch:
---
Mina wanted to be a superhero like the brave heroes in her comics. One day,
she found that her old cape kept slipping off her hip while she practiced. Her
little brother gave her a bright hip clip as an addition to her suit. Mina
first wanted to race off alone, but then she noticed a shy kid dropping
crayons. In her inner monologue, Mina decided that a true hero should help
first. She clipped on the new addition, helped the kid, and flew off smiling.

World model:
---
- Characters have both physical meters and emotional memes.
- A costume addition can be attached to the hero.
- A minor problem at the hip can make the hero notice a needed fix.
- Kindness resolves the tension and makes the ending feel heroic.
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
    attached_to: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    location: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.location)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    sidekick_name: str
    bystander_name: str
    location: str = "the city rooftop"
    seed: Optional[int] = None


HERO_NAMES = ["Mina", "Ivy", "Jude", "Nora", "Parker", "Tess"]
SIDEKICK_NAMES = ["Otto", "Ruby", "Finn", "June", "Sage"]
BYSTANDER_NAMES = ["Lulu", "Ben", "Milo", "Kira", "Nina"]
LOCATIONS = ["the city rooftop", "the park path", "the museum steps"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld about kindness and a hip addition.")
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--bystander")
    ap.add_argument("--location", choices=LOCATIONS)
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
    hero_type = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICK_NAMES)
    bystander = args.bystander or rng.choice(BYSTANDER_NAMES)
    location = args.location or rng.choice(LOCATIONS)
    if hero_name == sidekick or hero_name == bystander or sidekick == bystander:
        raise StoryError("Choose different names for the hero, sidekick, and bystander.")
    return StoryParams(hero_name=hero_name, hero_type=hero_type, sidekick_name=sidekick,
                       bystander_name=bystander, location=location)


def _inner_monologue(world: World, hero: Entity, line: str) -> None:
    world.say(f'[{hero.id} thought: "{line}"]')


def _hero_notice_problem(world: World, hero: Entity, accessory: Entity) -> None:
    hero.memes["concern"] = hero.memes.get("concern", 0) + 1
    world.say(
        f"{hero.id} noticed that the {accessory.label} kept slipping at the hip."
    )
    _inner_monologue(
        world,
        hero,
        "A real hero should fix this before flying off."
    )


def _kindness_event(world: World, hero: Entity, bystander: Entity) -> None:
    bystander.memes["helped"] = bystander.memes.get("helped", 0) + 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    world.say(
        f"Then {hero.id} saw {bystander.id} drop a stack of crayons on the steps."
    )
    _inner_monologue(
        world,
        hero,
        "I can help first. That is what a kind hero does."
    )
    world.say(
        f"{hero.id} knelt down, gathered the crayons, and handed them back with a smile."
    )


def _attach_addition(world: World, hero: Entity, accessory: Entity) -> None:
    accessory.attached_to = hero.id
    hero.meters["hip"] = max(0.0, hero.meters.get("hip", 0.0) - 1.0)
    hero.meters["balance"] = hero.meters.get("balance", 0.0) + 1.0
    world.say(
        f"{hero.id} clipped the new addition onto {hero.pronoun('possessive')} suit, and it sat neatly at the hip."
    )


def _flight_end(world: World, hero: Entity, accessory: Entity) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    world.say(
        f"With the addition in place, {hero.id} stood tall, the cape stayed steady, and {hero.pronoun()} felt ready to soar."
    )
    world.say(
        f"The {accessory.label} kept the hip secure, and {hero.id} flew home feeling like a true superhero."
    )


def tell(params: StoryParams) -> World:
    world = World(params.location)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type,
                            meters={"hip": 1.0, "balance": 0.0}, memes={"hope": 1.0}))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type="child"))
    bystander = world.add(Entity(id=params.bystander_name, kind="character", type="child"))
    accessory = world.add(Entity(
        id="hip_clip",
        kind="thing",
        type="gadget",
        label="hip clip",
        phrase="a bright hip clip as an addition to the suit",
        owner=hero.id,
    ))

    world.say(
        f"On {world.location}, {hero.id} was a young {hero.type} superhero who loved practicing brave poses."
    )
    world.say(
        f"{hero.id}'s {sidekick.id} had brought {hero.pronoun('possessive')} latest addition: {accessory.phrase}."
    )
    world.say(
        f"At first, {hero.id} wanted to race off and show off the new look."
    )
    _hero_notice_problem(world, hero, accessory)
    world.para()
    world.say(
        f"Just then, {sidekick.id} pointed at the steps and waved to get {hero.id}'s attention."
    )
    _kindness_event(world, hero, bystander)
    _attach_addition(world, hero, accessory)
    world.para()
    _flight_end(world, hero, accessory)

    world.facts.update(hero=hero, sidekick=sidekick, bystander=bystander, accessory=accessory)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short superhero story for a young child that includes the words "hip" and "addition".',
        f"Tell a gentle story about {hero.id}, a tiny superhero, who notices a hip problem, thinks about kindness, and uses a new addition to help.",
        f"Write a child-friendly superhero tale with inner monologue, a kind choice, and a cheerful ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    bystander = f["bystander"]
    accessory = f["accessory"]
    return [
        QAItem(
            question=f"What addition did {sidekick.id} bring to help {hero.id}?",
            answer=f"{sidekick.id} brought a bright hip clip, which was a small addition to the superhero suit."
        ),
        QAItem(
            question=f"What did {hero.id} think about before helping {bystander.id}?",
            answer=f"{hero.id} thought that a real hero should fix the hip problem and help someone first."
        ),
        QAItem(
            question=f"How did kindness change the end of the story?",
            answer=f"Kindness made {hero.id} stop showing off, pick up the crayons, and then fly away feeling proud and helpful."
        ),
        QAItem(
            question=f"What was special about the way the story showed {hero.id}'s thoughts?",
            answer="The story used inner monologue, so readers could hear the hero thinking in short, child-friendly lines."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a character who tries to help others and do brave things, often with a special costume or power."
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring about other people's feelings and needs."
        ),
        QAItem(
            question="What is a hip?",
            answer="A hip is the part of your body near where your leg joins your body."
        ),
        QAItem(
            question="What is an addition?",
            answer="An addition is something extra that is added to make something bigger, better, or more useful."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


ASP_RULES = r"""
hero(H).
addition(A).
problem(hip_slip) :- hero(H), addition(A).
kind_choice(help_first) :- problem(hip_slip).
resolved :- kind_choice(help_first).
#show problem/1.
#show kind_choice/1.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero", "mina"),
        asp.fact("addition", "hip_clip"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/0."))
    atoms = {str(sym) for sym in model}
    if "resolved" in atoms:
        print("OK: ASP story logic resolves kindness.")
        return 0
    print("MISMATCH: ASP did not resolve.")
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.attached_to:
            bits.append(f"attached_to={e.attached_to}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(hero_name="Mina", hero_type="girl", sidekick_name="Otto", bystander_name="Lulu", location="the city rooftop"),
    StoryParams(hero_name="Jude", hero_type="boy", sidekick_name="Ruby", bystander_name="Ben", location="the park path"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/0."))
        print(model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        rng = random.Random(base_seed)
        seen = set()
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
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
