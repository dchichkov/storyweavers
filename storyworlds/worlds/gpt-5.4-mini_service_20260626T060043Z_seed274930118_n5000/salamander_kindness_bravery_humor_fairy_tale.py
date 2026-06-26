#!/usr/bin/env python3
"""
Story world: a small fairy-tale domain about a salamander whose kindness,
bravery, and humor help solve a gentle problem.

Premise:
- A young salamander lives near a moonlit pond in a little old forest.
- The salamander wants to help a worried friend, but a small obstacle blocks
  the way.
- Kindness offers the first path, bravery is needed to cross the danger, and
  humor helps everyone keep heart.

This script is self-contained and follows the Storyweavers world contract:
- typed entities with meters and memes
- a deterministic simulated state driving prose
- a reasonableness gate and matching ASP twin
- story QA and generic world QA
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
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"safe": 0.0, "blocked": 0.0, "dry": 0.0}
        if not self.memes:
            self.memes = {"kindness": 0.0, "bravery": 0.0, "humor": 0.0, "worry": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "princess"}
        male = {"boy", "father", "man", "king", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the moonlit pond"
    detail: str = "The reeds whispered beside the water."


@dataclass
class Challenge:
    id: str
    obstacle: str
    danger: str
    ask: str
    crossing: str
    solution: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    help_line: str
    outcome: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    name: str
    gender: str
    role: str
    challenge: str
    seed: Optional[int] = None


SETTING = Setting()
CHALLENGES = {
    "stream": Challenge(
        id="stream",
        obstacle="a little stream",
        danger="the water is deep enough to splash the path",
        ask="cross the stream and bring a lantern to a lost mouse",
        crossing="tiptoe over the stepping stones",
        solution="place reeds as a bridge",
        keyword="stream",
        tags={"water", "bridge"},
    ),
    "bramble": Challenge(
        id="bramble",
        obstacle="a prickly bramble patch",
        danger="the thorns snag sleeves and slow tiny feet",
        ask="reach a basket of pears on the far side",
        crossing="slip between the thorny branches",
        solution="tie back the thorns with soft vines",
        keyword="bramble",
        tags={"thorns", "path"},
    ),
    "fog": Challenge(
        id="fog",
        obstacle="a curtain of silver fog",
        danger="the road disappears and even brave paws can wander",
        ask="guide a candle through the dark lane",
        crossing="walk by the moon glow",
        solution="tell a cheerful rhyme to keep the way in mind",
        keyword="fog",
        tags={"mist", "lantern"},
    ),
}

HELPERS = [
    Helper(
        id="reeds",
        label="bundles of reeds",
        phrase="soft bundles of reeds",
        help_line="They laid the reeds across the water like a tiny bridge.",
        outcome="The reeds held steady.",
        plural=True,
    ),
    Helper(
        id="vines",
        label="soft vines",
        phrase="soft green vines",
        help_line="They tied the vines around the brambles gently.",
        outcome="The thorns parted kindly.",
        plural=True,
    ),
    Helper(
        id="rhyme",
        label="a cheerful rhyme",
        phrase="a cheerful rhyme",
        help_line="The salamander told a merry rhyme, and the fog seemed less lonely.",
        outcome="The path felt easier to remember.",
    ),
]

NAMES = ["Milo", "Luna", "Pip", "Nora", "Fern", "Ivy", "Tilo", "Cleo"]
TRAITS = ["kind", "brave", "curious", "cheerful", "gentle"]


def reasonableness_gate(challenge: Challenge, helper: Helper) -> bool:
    if challenge.id == "stream" and helper.id == "reeds":
        return True
    if challenge.id == "bramble" and helper.id == "vines":
        return True
    if challenge.id == "fog" and helper.id == "rhyme":
        return True
    return False


def explain_rejection(challenge: Challenge, helper: Helper) -> str:
    return (
        f"(No story: {helper.label} does not sensibly solve {challenge.obstacle}. "
        f"Try the helper that fits the obstacle and its danger.)"
    )


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="salamander",
        label="young salamander",
        meters={"safe": 0.0, "blocked": 0.0, "dry": 1.0},
        memes={"kindness": 0.0, "bravery": 0.0, "humor": 0.0, "worry": 0.0, "joy": 0.0},
    ))
    friend = world.add(Entity(
        id="Mouse",
        kind="character",
        type="mouse",
        label="little mouse",
        meters={"safe": 0.0, "blocked": 0.0, "dry": 1.0},
        memes={"kindness": 0.0, "bravery": 0.0, "humor": 0.0, "worry": 1.0, "joy": 0.0},
    ))
    challenge = CHALLENGES[params.challenge]
    helper = next(h for h in HELPERS if reasonableness_gate(challenge, h))

    hero.memes["kindness"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"In the moonlit forest, {hero.id} was a young salamander with a bright heart. "
        f"{hero.id} loved to be kind, and even the frogs said {hero.id} had a gentle way of listening."
    )
    world.say(
        f"One evening, {hero.id} heard that a little mouse needed help with {challenge.ask}. "
        f"But the way led past {challenge.obstacle}, and that meant {challenge.danger}."
    )

    world.para()
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} did not turn away. {hero.id} took a breath, lifted a tiny chin, and said, "
        f"\"I can go carefully.\" That was bravery, small as a spark but strong enough to shine."
    )
    world.say(
        f"At the edge of the path, {hero.id} paused and looked at {helper.phrase}. "
        f"With a little humor, {hero.id} smiled and said, \"A fairy tale path should not be tricked by a grumpy problem!\""
    )
    hero.memes["humor"] += 1

    world.para()
    if challenge.id == "stream":
        world.say(
            f"Then {hero.id} and the mouse placed the reeds across the stream. "
            f"{helper.help_line} {helper.outcome}"
        )
    elif challenge.id == "bramble":
        world.say(
            f"Then {hero.id} and the mouse used the vines to tame the brambles. "
            f"{helper.help_line} {helper.outcome}"
        )
    else:
        world.say(
            f"Then {hero.id} told the rhyme in a clear little voice. "
            f"{helper.help_line} {helper.outcome}"
        )

    hero.memes["joy"] += 1
    hero.meters["safe"] += 1
    friend.meters["safe"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Together they reached the far side and finished the good deed. "
        f"The mouse carried the lantern with a happy smile, and {hero.id}'s eyes twinkled like stars."
    )
    world.say(
        f"That night, the pond stayed peaceful, the road was safe again, and everyone remembered that kindness, bravery, and humor can work like magic."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        challenge=challenge,
        helper=helper,
        params=params,
    )
    return world


def choose_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    challenge = args.challenge or rng.choice(list(CHALLENGES))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    role = args.role or rng.choice(TRAITS)
    helper = next(h for h in HELPERS if reasonableness_gate(CHALLENGES[challenge], h))
    if args.helper and args.helper != helper.id:
        raise StoryError(explain_rejection(CHALLENGES[challenge], helper))
    return StoryParams(name=name, gender=gender, role=role, challenge=challenge)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    challenge = f["challenge"]
    return [
        f"Write a fairy-tale story about a salamander named {hero.id} who shows kindness, bravery, and humor.",
        f"Tell a short children's story where {hero.id} must {challenge.ask}.",
        f"Write a gentle tale in a moonlit forest with a salamander, a small danger, and a happy fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    challenge = f["challenge"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a young salamander who is kind, brave, and funny in a gentle way.",
        ),
        QAItem(
            question=f"What problem did {hero.id} want to solve?",
            answer=f"{hero.id} wanted to {challenge.ask}, but {challenge.obstacle} stood in the way.",
        ),
        QAItem(
            question=f"How did {hero.id} and the mouse solve the problem?",
            answer=f"They used {helper.phrase} to help, and that made the path safe enough to cross.",
        ),
        QAItem(
            question=f"What did the salamander's humor do in the story?",
            answer=f"The humor helped everyone stay cheerful while they worked, so the hard path felt less scary.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a salamander?",
            answer="A salamander is a small amphibian with smooth skin that likes damp places and often lives near water.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is choosing to help, comfort, or care for someone in a gentle and thoughtful way.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing something scary or hard even when your heart is fluttering a little.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is the playful part of a story that makes people smile or laugh softly.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:8} ({e.type:10}) meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

valid(A,H) :- challenge(A), helper(H), fits(A,H).
valid_story(A,H,G) :- valid(A,H), gender_ok(G,A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("obstacle", cid, ch.obstacle))
        lines.append(asp.fact("keyword", cid, ch.keyword))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
    lines.append(asp.fact("fits", "stream", "reeds"))
    lines.append(asp.fact("fits", "bramble", "vines"))
    lines.append(asp.fact("fits", "fog", "rhyme"))
    for g in ["girl", "boy"]:
        for cid in CHALLENGES:
            lines.append(asp.fact("gender_ok", g, cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted((cid, h.id) for cid in CHALLENGES for h in HELPERS if reasonableness_gate(CHALLENGES[cid], h))
    cl = asp_valid()
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} pairs).")
        return 0
    print("MISMATCH:")
    print("python:", py)
    print("clingo :", cl)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale salamander world with kindness, bravery, and humor.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--role", choices=["kind", "brave", "curious", "cheerful", "gentle"])
    ap.add_argument("--challenge", choices=list(CHALLENGES))
    ap.add_argument("--helper", choices=[h.id for h in HELPERS])
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
    return choose_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible challenge/helper pairs:")
        for cid, hid in combos:
            print(f"  {cid:8} {hid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for i, cid in enumerate(CHALLENGES):
            params = StoryParams(name=NAMES[i % len(NAMES)], gender="girl" if i % 2 == 0 else "boy", role=TRAITS[i % len(TRAITS)], challenge=cid, seed=base_seed + i)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
