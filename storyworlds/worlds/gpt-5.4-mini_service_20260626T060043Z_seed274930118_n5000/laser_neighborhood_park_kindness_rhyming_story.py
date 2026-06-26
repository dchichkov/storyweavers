#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/laser_neighborhood_park_kindness_rhyming_story.py
===========================================================================================================

A small story world for a rhyming kindness tale in a neighborhood park.
The seed word is laser: a child has a tiny laser light, and the story turns
on sharing it kindly with a neighbor child.

The world is intentionally compact:
- one fixed setting: neighborhood park
- one key object: a laser light
- one social tension: keep it / share it
- one emotional resolution: kindness becomes joy

The narration is meant to read like a gentle rhyming story for children.
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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    name: str
    gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None


@dataclass
class World:
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


NAMES_GIRL = ["Mia", "Zoe", "Lily", "Nora", "Ava", "Ruby", "Ella"]
NAMES_BOY = ["Leo", "Finn", "Max", "Noah", "Eli", "Jack", "Owen"]


def _r_shine(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    laser = world.get("laser")
    if child.memes.get("play", 0.0) >= THRESHOLD and laser.held_by == child.id:
        child.meters["spark"] = child.meters.get("spark", 0.0) + 1
        out.append("The laser made a tiny bright dash, like a star on a windy splash.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    friend = world.get("friend")
    laser = world.get("laser")
    if child.memes.get("kindness", 0.0) >= THRESHOLD and laser.held_by == friend.id:
        friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1
        out.append("Kindness bloomed and lit the air; the two friends smiled and shared.")
    return out


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    produced.extend(_r_shine(world))
    produced.extend(_r_kindness(world))
    for s in produced:
        world.say(s)
    return produced


def rhyming_opening(hero: Entity, friend: Entity) -> str:
    return (
        f"In the neighborhood park, where the day felt bright, "
        f"{hero.id} came skipping with a laser light. "
        f"{friend.id} came near with a hopeful grin, "
        f"and the little green grass waved them both right in."
    )


def rhyming_conflict(hero: Entity, friend: Entity) -> str:
    return (
        f"{hero.id} wanted the laser to whirl and glow, "
        f"to zig and zag in a zigzag show. "
        f"But {friend.id} looked down with a quiet face, "
        f"and the park felt still in that little space."
    )


def rhyming_turn(hero: Entity, friend: Entity) -> str:
    return (
        f"{hero.id} saw {friend.id} and chose to care, "
        f"so {hero.pronoun('subject')} held out the laser with open air. "
        f'"You may have a turn," {hero.id} said sweetly and true, '
        f'"because kindness is nicer than only me and you."'
    )


def rhyming_end(hero: Entity, friend: Entity) -> str:
    return (
        f"Then the laser danced in a looping line, "
        f"while {hero.id} and {friend.id} felt warm and fine. "
        f"They laughed till the lamplight began to sway, "
        f"and kindness made the whole park bright that day."
    )


def tell(world: World) -> World:
    hero = world.add(Entity(id="child", kind="character", type=world.facts["hero_gender"], label="the child"))
    friend = world.add(Entity(id="friend", kind="character", type=world.facts["friend_gender"], label="the friend"))
    laser = world.add(Entity(id="laser", kind="thing", type="laser", label="laser light", phrase="a tiny laser light", owner=hero.id, held_by=hero.id))
    hero.memes["play"] = 1.0
    hero.memes["want"] = 1.0
    hero.memes["kindness"] = 0.0
    friend.memes["wish"] = 1.0

    world.say(rhyming_opening(hero, friend))
    world.para()
    world.say(rhyming_conflict(hero, friend))
    hero.memes["kindness"] = 1.0
    hero.memes["want"] = 0.0
    laser.held_by = friend.id
    world.para()
    world.say(rhyming_turn(hero, friend))
    propagate(world)
    world.para()
    world.say(rhyming_end(hero, friend))

    world.facts.update(hero=hero, friend=friend, laser=laser, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short rhyming story for children about a laser light in a neighborhood park.',
        f"Tell a gentle story where {world.facts['hero'].id} learns kindness by sharing a laser with a friend.",
        "Write a simple rhyming story that begins in a neighborhood park and ends with two children smiling together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        QAItem(
            question=f"Where does {hero.id}'s story happen?",
            answer="It happens in the neighborhood park, where the grass is bright and the air feels light.",
        ),
        QAItem(
            question=f"What did {hero.id} want to play with?",
            answer=f"{hero.id} wanted to play with a laser light, making a little bright dash in the air.",
        ),
        QAItem(
            question=f"How did {hero.id} show kindness to {friend.id}?",
            answer=f"{hero.id} showed kindness by sharing the laser light and giving {friend.id} a turn.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended with both children happy, laughing, and enjoying the park together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a laser light?",
            answer="A laser light is a very narrow beam of light that can make a small bright dot or line.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, caring, and willing to share or help someone else.",
        ),
        QAItem(
            question="What is a neighborhood park?",
            answer="A neighborhood park is a shared outdoor place where people can walk, play, and meet friends.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming kindness story world: laser in a neighborhood park.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    friend_name = args.friend_name or rng.choice(NAMES_BOY if friend_gender == "boy" else NAMES_GIRL)
    if name == friend_name:
        friend_name = next(n for n in (NAMES_BOY + NAMES_GIRL) if n != name)
    return StoryParams(name=name, gender=gender, friend_name=friend_name, friend_gender=friend_gender)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "neighborhood_park"),
        asp.fact("theme", "kindness"),
        asp.fact("object", "laser"),
        asp.fact("can_share", "laser"),
        asp.fact("makes", "laser", "bright_dot"),
        asp.fact("location", "neighborhood_park"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
shareable(X) :- can_share(X).
child_story(P,O) :- setting(P), object(O), theme(kindness), shareable(O).
#show child_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show child_story/2."))
    ok = bool(model)
    if ok:
        print("OK: ASP model exists for the kindness laser park story.")
        return 0
    print("MISMATCH: no ASP model found.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = World()
    world.facts["hero_gender"] = params.gender
    world.facts["friend_gender"] = params.friend_gender
    world = tell(world)
    hero = world.facts["hero"]
    friend = world.facts["friend"]
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
        print(asp_program("#show child_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show child_story/2."))
        print("ASP model:", asp.atoms(model, "child_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(name="Mia", gender="girl", friend_name="Leo", friend_gender="boy", seed=base_seed)
        samples = [generate(params)]
    else:
        for i in range(max(1, args.n)):
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
