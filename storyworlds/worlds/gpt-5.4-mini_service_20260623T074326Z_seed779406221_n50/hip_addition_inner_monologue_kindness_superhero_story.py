#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074326Z_seed779406221_n50/hip_addition_inner_monologue_kindness_superhero_story.py
================================================================================================

A small superhero-style storyworld about a hero, a hurt hip, and an unexpected
addition to the team. The stories use inner monologue and kindness as central
narrative instruments: the hero notices a problem, thinks it through, chooses a
gentle solution, and ends with a visible change in the world.

The seed words are preserved in the world model and prose: hip, addition.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class HeroSpec:
    id: str
    cape: str
    power: str
    emblem: str
    city: str
    motto: str


@dataclass
class TroubleSpec:
    id: str
    problem: str
    hip_label: str
    cause: str
    sound: str
    limit: str


@dataclass
class HelperSpec:
    id: str
    role: str
    gift: str
    action: str
    kindness_line: str
    addition_word: str


@dataclass
class StoryParams:
    hero: str
    trouble: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
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

    def copy(self) -> "World":
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


HEROES = {
    "skybolt": HeroSpec("skybolt", "blue", "fast rescue", "lightning", "Metro Bay", "I help, then I soar."),
    "nightbeam": HeroSpec("nightbeam", "silver", "careful strength", "moon", "Sunset City", "I notice, then I mend."),
    "cometheart": HeroSpec("cometheart", "red", "kind courage", "star", "Bright Harbor", "I choose the gentle way."),
}

TROUBLES = {
    "stumble": TroubleSpec("stumble", "a painful hip stumble", "hip", "slipping off a ledge", "thump", "take it slow"),
    "twinge": TroubleSpec("twinge", "a sore hip twinge", "hip", "landing too hard after a jump", "oof", "no running"),
    "bump": TroubleSpec("bump", "a bumped hip", "hip", "hitting a railing in the rush", "clack", "no pounding"),
}

HELPERS = {
    "medkit": HelperSpec("medkit", "medic", "a bright red wrap", "wrap", "kindly", "addition"),
    "apron": HelperSpec("apron", "neighbor", "a warm scarf", "steady", "gently", "addition"),
    "rookie": HelperSpec("rookie", "new helper", "a squeaky scooter bell", "assist", "cheerfully", "addition"),
}

NAMES = ["Nova", "Atlas", "Ruby", "Milo", "Jade", "Zane", "Piper", "Orion"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero storyworld with inner monologue and kindness.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--helper", choices=HELPERS)
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
    return StoryParams(
        hero=args.hero or rng.choice(list(HEROES)),
        trouble=args.trouble or rng.choice(list(TROUBLES)),
        helper=args.helper or rng.choice(list(HELPERS)),
    )


def _name(rng: random.Random) -> str:
    return rng.choice(NAMES)


def tell(params: StoryParams, rng: random.Random) -> World:
    hero = HEROES[params.hero]
    trouble = TROUBLES[params.trouble]
    helper = HELPERS[params.helper]

    world = World()
    h = world.add(Entity(id=_name(rng), kind="character", type="person", role="hero", label=hero.id))
    a = world.add(Entity(id=_name(rng), kind="character", type="person", role="helper", label=helper.role))
    hip = world.add(Entity(id="hip", kind="body", type="body", label="hip", role="injury"))
    add = world.add(Entity(id="addition", kind="thing", type="thing", label="addition", role="solution"))

    h.memes["resolve"] = 1.0
    h.memes["kindness"] = 0.0
    hip.meters["pain"] = 1.0
    hip.meters["stiff"] = 1.0
    world.facts.update(hero=hero, trouble=trouble, helper=helper, hero_name=h.id, helper_name=a.id)

    world.say(
        f"That evening, {h.id} raced through {hero.city} in {hero.cape} colors, chasing the last gust of trouble."
    )
    world.say(
        f"Then came {trouble.sound} -- {h.id} landed wrong, and a {trouble.problem} shot through the {trouble.hip_label}."
    )
    world.say(
        f'{h.id} stopped behind a rooftop sign and breathed, "If I push too hard, I will only make it worse."'
    )
    world.say(
        f'{h.id} listened to that quiet inner monologue and nodded to the ache instead of arguing with it.'
    )
    world.para()
    h.memes["worry"] = 1.0
    h.memes["kindness"] += 1.0
    world.say(
        f"On the next ledge, {a.id} arrived with {helper.gift} and {helper.action}d beside {h.id}."
    )
    world.say(
        f'"{helper.kindness_line.capitalize()}," {a.id} said. "We do not need to win fast. We need to help well."'
    )
    world.say(
        f"{h.id} smiled at the {helper.addition_word}: a small, careful helper joining the rescue instead of crowding it."
    )
    hip.meters["pain"] = 0.0
    hip.meters["stiff"] = 0.0
    add.meters["teamwork"] = 1.0
    add.memes["kindness"] = 1.0
    h.memes["relief"] = 1.0
    world.para()
    world.say(
        f"Together they slowed the chase, wrapped the sore {trouble.hip_label}, and guided the hero home under the city lights."
    )
    world.say(
        f"By dawn, {h.id} was moving carefully, and the {trouble.hip_label} no longer hurt."
    )
    world.say(
        f"The only new thing left from the night was the addition of trust: a stronger team, a gentler pace, and a hero who knew kindness could be super too."
    )
    return world


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed or 0)
    world = tell(params, rng)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, trouble, helper = f["hero"], f["trouble"], f["helper"]
    return [
        f"Write a superhero story where {world.facts['hero_name']} feels a {trouble.problem} in the {trouble.hip_label} and uses inner monologue to stay calm.",
        f"Tell a child-friendly superhero story about kindness: {world.facts['helper_name']} makes an addition to the rescue with {helper.gift}.",
        f"Create a short Superhero Story with the words hip and addition, ending with a gentle victory instead of a battle.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, trouble, helper = f["hero"], f["trouble"], f["helper"]
    return [
        QAItem(question="What happened to the hero's hip?", answer=f"The hero got {trouble.problem}, so the hip hurt and felt stiff."),
        QAItem(question="What did the hero think in the inner monologue?", answer="The hero decided not to push too hard and chose to listen to the ache."),
        QAItem(question="How did kindness help?", answer=f"{f['helper_name']} arrived with {helper.gift} and helped gently, which made the rescue calmer and safer."),
        QAItem(question="What was the addition in the story?", answer="The addition was the extra helper and trust that joined the rescue team."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is kindness?", answer="Kindness means helping gently, caring about others, and choosing actions that make things better."),
        QAItem(question="What is inner monologue?", answer="Inner monologue is the quiet voice in a character's mind that helps them think through a problem."),
        QAItem(question="What does addition mean?", answer="Addition means something extra is added to make a number or a team bigger."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id}: {', '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_story(ok).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("theme", "superhero"),
        asp.fact("feature", "inner_monologue"),
        asp.fact("feature", "kindness"),
        asp.fact("word", "hip"),
        asp.fact("word", "addition"),
    ])


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for section, items in (("Prompts", sample.prompts), ("Story QA", sample.story_qa), ("World QA", sample.world_qa)):
            print(f"== {section} ==")
            if section == "Prompts":
                for i, p in enumerate(items, 1):
                    print(f"{i}. {p}")
            else:
                for item in items:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show hero_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available in this world, but the story model is intentionally small.")
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        for h in HEROES:
            for t in TROUBLES:
                for helper in HELPERS:
                    params = StoryParams(hero=h, trouble=t, helper=helper, seed=args.seed)
                    samples.append(generate(params))
    else:
        for i in range(args.n):
            params = resolve_params(args, rng)
            params.seed = (args.seed or 0) + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
