#!/usr/bin/env python3
"""
A small storyworld: a curious child at a planetarium, a friendly game of pong,
and a warm little twist about healing someone who seemed to be the helper.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class Place:
    name: str
    glow: str
    sounds: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    companion_name: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    hero: Entity
    companion: Entity
    orb: Entity
    ball: Entity
    cure: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "planetarium": Place(
        name="the planetarium",
        glow="soft blue light",
        sounds="a quiet hum from the ceiling stars",
        affords={"listen", "wonder", "pong"},
    )
}

HERO_NAMES = ["Mina", "Owen", "Lina", "Noah", "Tessa", "Ravi"]
COMPANION_NAMES = ["Dot", "Pip", "Sunny", "Moss", "Nova"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    hero = Entity(id=params.hero_name, kind="character", label=params.hero_name, type="child")
    companion = Entity(id=params.companion_name, kind="character", label=params.companion_name, type="friend")
    orb = Entity(id="orb", kind="thing", label="small guide orb", type="orb", meters={"cracked": 1.0, "dim": 1.0})
    ball = Entity(id="ball", kind="thing", label="pong ball", type="ball", meters={"bounce": 1.0})
    cure = Entity(id="cure", kind="thing", label="warm repair patch", type="patch")

    world = World(place=place, hero=hero, companion=companion, orb=orb, ball=ball, cure=cure)
    world.facts.update(params=params, place=place, hero=hero, companion=companion, orb=orb, ball=ball, cure=cure)
    return world


def heal_orb(world: World) -> None:
    if world.orb.meters.get("cracked", 0.0) < 1.0:
        return
    world.orb.meters["cracked"] = 0.0
    world.orb.meters["dim"] = 0.0
    world.orb.memes["relief"] = 1.0
    world.hero.memes["care"] = world.hero.memes.get("care", 0.0) + 1.0
    world.say(
        f"{world.hero.id} pressed the warm repair patch to the little guide orb, and the crack faded."
    )
    world.say(
        f"The orb gave a soft glow again, as if it had been waiting for someone kind enough to notice."
    )


def start_story(world: World) -> None:
    world.say(
        f"{world.hero.id} went to {world.place.name} with {world.companion.id} and looked up at the bright ceiling stars."
    )
    world.say(
        f"The room had {world.place.glow}, and there was {world.place.sounds} drifting through the air."
    )
    world.say(
        f"{world.hero.id} was full of curiosity and wanted to play pong beside the glass domes."
    )


def twist(world: World) -> None:
    world.para()
    world.say(
        f"Then {world.companion.id} nudged the tiny guide orb, and {world.hero.id} noticed a thin crack on its side."
    )
    world.say(
        f"\"Oh no,\" {world.hero.id} whispered. \"You were the one helping us, and now you're the one who needs help.\""
    )
    world.hero.memes["curiosity"] = world.hero.memes.get("curiosity", 0.0) + 1.0
    world.companion.memes["concern"] = world.companion.memes.get("concern", 0.0) + 1.0


def dialogue_and_fix(world: World) -> None:
    world.para()
    world.say(
        f"\"Can we heal it?\" {world.hero.id} asked."
    )
    world.say(
        f"\"Yes,\" said {world.companion.id}. \"Let's use the warm repair patch before we start the game.\""
    )
    heal_orb(world)
    world.say(
        f"{world.hero.id} smiled. \"Then we can still play pong, and the orb can shine with us.\""
    )
    world.hero.memes["joy"] = world.hero.memes.get("joy", 0.0) + 1.0
    world.companion.memes["joy"] = world.companion.memes.get("joy", 0.0) + 1.0


def end_scene(world: World) -> None:
    world.para()
    world.say(
        f"After that, the three of them watched the stars blink while the pong ball tapped softly back and forth."
    )
    world.say(
        f"The orb glowed, {world.hero.id} laughed, and the planetarium felt warmer than before."
    )


# ---------------------------------------------------------------------------
# Reasoning / ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/2.
#show fixed/1.
place(planetarium).
activity(pong).
feature(twist).
feature(dialogue).
feature(curiosity).
feature(heartwarming).

valid(planetarium,pong) :- place(planetarium), activity(pong), feature(twist), feature(dialogue), feature(curiosity), feature(heartwarming).
fixed(orb) :- valid(planetarium,pong).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "planetarium"),
        asp.fact("activity", "pong"),
        asp.fact("feature", "twist"),
        asp.fact("feature", "dialogue"),
        asp.fact("feature", "curiosity"),
        asp.fact("feature", "heartwarming"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate(params: StoryParams) -> None:
    if params.place != "planetarium":
        raise StoryError("This world only tells a story in the planetarium.")
    if not params.hero_name or not params.companion_name:
        raise StoryError("Both a curious child and a companion are needed.")


def asp_verify() -> int:
    import asp
    models = asp.solve(asp_program("#show valid/2.\n#show fixed/1."), models=1)
    if not models:
        print("MISMATCH: ASP produced no model.")
        return 1
    atoms = {(sym.name, tuple(a.string if a.type == a.type.String else a.number if a.type == a.type.Number else a.name for a in sym.arguments)) for sym in models[0]}
    needed = {("valid", ("planetarium", "pong")), ("fixed", ("orb",))}
    if needed.issubset(atoms):
        print("OK: ASP gate is consistent.")
        return 0
    print("MISMATCH: ASP result did not include expected atoms.")
    return 1


# ---------------------------------------------------------------------------
# Story building
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    start_story(world)
    twist(world)
    dialogue_and_fix(world)
    end_scene(world)

    story_qa = [
        QAItem(
            question="Why did the child stop and look closely at the guide orb?",
            answer=f"{world.hero.id} noticed a crack on the little guide orb and wanted to help it heal before playing pong."
        ),
        QAItem(
            question="What did the friend suggest doing first?",
            answer=f"{world.companion.id} suggested using the warm repair patch first, so the orb could be fixed before the game."
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The orb was healed, the friends felt happy, and the planetarium ended with a warm, glowing feeling."
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a planetarium?",
            answer="A planetarium is a place where people can look at stars, planets, and space shows indoors."
        ),
        QAItem(
            question="What is pong?",
            answer="Pong is a simple game where a ball bounces back and forth."
        ),
        QAItem(
            question="What does heal mean?",
            answer="To heal means to make something better after it is hurt, cracked, or unwell."
        ),
    ]

    prompts = [
        'Write a heartwarming story in a planetarium where a child wants to play pong, notices something broken, and helps heal it.',
        f"Tell a gentle story about {params.hero_name} and {params.companion_name} at the planetarium, with a twist and some dialogue.",
        "Write a curious, heartwarming story about stars, a pong game, and a small act of healing.",
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming planetarium storyworld with a twist, dialogue, and curiosity.")
    ap.add_argument("--place", choices=PLACES.keys(), default="planetarium")
    ap.add_argument("--name")
    ap.add_argument("--companion")
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
    hero_name = args.name or rng.choice(HERO_NAMES)
    companion_name = args.companion or rng.choice(COMPANION_NAMES)
    return StoryParams(place=args.place, hero_name=hero_name, companion_name=companion_name)


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in [world.hero, world.companion, world.orb, world.ball, world.cure]:
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
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
        print(asp_program("#show valid/2.\n#show fixed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2.\n#show fixed/1."))
        print("ASP atoms:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="planetarium", hero_name="Mina", companion_name="Nova", seed=base_seed),
            StoryParams(place="planetarium", hero_name="Owen", companion_name="Pip", seed=base_seed + 1),
            StoryParams(place="planetarium", hero_name="Lina", companion_name="Sunny", seed=base_seed + 2),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
