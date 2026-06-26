#!/usr/bin/env python3
"""
storyworlds/worlds/explanatory_stir_kindness_friendship_foreshadowing_space_adventure.py
=======================================================================================

A small Space Adventure story world about kindness, friendship, and a gentle
foreshadowed rescue in orbit.

Premise used to build the world model:
---
On a bright training day at the Moon Harbor station, a young spacer named Nova
loved to visit the observation deck and feed the tiny seed-garden that floated
there in clear pods. Nova had a best friend named Pip, a little maintenance
drone with a soft voice and bright blue lights. The two of them always worked
side by side.

One afternoon, Nova found a drifting cargo pod with a cracked latch and a
sleepy starling-bot inside. The bot could not get back to its shuttle. Nova's
friend Pip noticed something important: the pod's warning light had flickered
twice earlier, which meant the latch might fail completely later. Nova wanted to
hurry past, but Pip reminded Nova to be kind and slow down. Together they fixed
the latch, guided the bot home, and shared a quiet wave under the stars.

World model summary:
---
- meters measure physical changes like charge, drift, damage, and seal
- memes measure emotional changes like kindness, friendship, worry, and trust
- foreshadowing is represented by earlier warning lights and later payoff
- the story resolves when a helpful repair prevents a worse drift in space

This script keeps the prose child-facing and concrete, while the state machine
drives the shape of the story.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
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

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Station:
    name: str = "Moon Harbor"
    place: str = "the observation deck"
    ring: str = "the quiet orbit ring"


@dataclass
class StoryParams:
    station: str = "moon_harbor"
    hero_name: str = "Nova"
    hero_type: str = "girl"
    friend_name: str = "Pip"
    friend_type: str = "drone"
    seed: Optional[int] = None


class World:
    def __init__(self, station: Station) -> None:
        self.station = station
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _mget(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _eget(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _madd(ent: Entity, key: str, amt: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _eadd(ent: Entity, key: str, amt: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def _eset(ent: Entity, key: str, value: float) -> None:
    ent.memes[key] = value


def _say_name(ent: Entity) -> str:
    return ent.id


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _setup_world(params: StoryParams) -> World:
    station = Station()
    world = World(station)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"calm": 1.0},
        memes={"kindness": 1.0, "friendship": 1.0, "curiosity": 1.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_type,
        label="tiny helper",
        meters={"battery": 1.0},
        memes={"friendship": 1.0, "trust": 1.0},
    ))
    pod = world.add(Entity(
        id="cargo_pod",
        type="pod",
        label="cargo pod",
        phrase="a drifting cargo pod",
        meters={"drift": 1.0, "damage": 0.0, "seal": 0.0},
        memes={"worry": 1.0},
    ))
    bot = world.add(Entity(
        id="starling_bot",
        kind="character",
        type="bot",
        label="starling-bot",
        phrase="a sleepy starling-bot",
        owner=pod.id,
        meters={"drift": 1.0, "charge": 0.4},
        memes={"worry": 1.0, "hope": 0.5},
    ))
    world.facts.update(hero=hero, friend=friend, pod=pod, bot=bot)
    return world


def _foreshadow(world: World) -> None:
    pod = world.facts["pod"]
    friend = world.facts["friend"]
    _madd(pod, "damage", 0.4)
    _eadd(friend, "foreshadowing", 1.0)
    world.say(
        f"At {world.station.name}, the warning light on {pod.label} blinked twice. "
        f"{friend.id} noticed it and gave a small beep, as if it was trying to say the latch might fail later."
    )


def _problem(world: World) -> None:
    hero = world.facts["hero"]
    pod = world.facts["pod"]
    bot = world.facts["bot"]
    _eadd(hero, "stir", 1.0)
    _eadd(hero, "worry", 1.0)
    _madd(bot, "drift", 0.7)
    world.say(
        f"Then {hero.id} saw {bot.phrase} spinning near {pod.label}. "
        f"{hero.id} wanted to rush past and grab the pod at once, but the cold stars made the moment feel very big."
    )


def _repair(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    pod = world.facts["pod"]
    bot = world.facts["bot"]

    if ("repair", pod.id) in world.fired:
        return
    world.fired.add(("repair", pod.id))

    _eadd(hero, "kindness", 1.0)
    _eadd(friend, "friendship", 1.0)
    _eadd(hero, "friendship", 1.0)
    _madd(pod, "seal", 1.0)
    _madd(pod, "damage", -0.4)
    _madd(bot, "drift", -0.7)
    _madd(bot, "charge", 0.4)
    _eset(hero, "worry", 0.0)
    _eset(friend, "worry", 0.0)

    world.say(
        f"{friend.id} flashed a calm blue light and reminded {hero.id} to be kind and slow. "
        f"Together they lined up the cracked latch, pressed it shut, and sealed the pod before it could drift away."
    )
    world.say(
        f"The little starling-bot blinked awake, its charge returning as it settled safely home."
    )


def _ending(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    bot = world.facts["bot"]
    pod = world.facts["pod"]
    world.say(
        f"After that, {hero.id} and {friend.id} shared a gentle wave under the round station window. "
        f"The warning light stayed dark, {bot.id} was safe, and {pod.label} no longer drifted like a lost little moon."
    )


def tell(params: StoryParams) -> World:
    world = _setup_world(params)
    hero = world.facts["hero"]
    friend = world.facts["friend"]

    world.say(
        f"At {world.station.name}, {hero.id} loved the quiet {world.station.place} because it looked out over the shining stars."
    )
    world.say(
        f"{hero.id} and {friend.id} were best friends. {hero.id} liked the way {friend.id} flickered kindly whenever help was needed."
    )
    world.para()

    _foreshadow(world)
    _problem(world)
    world.para()
    _repair(world)
    _ending(world)

    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    pod = world.facts["pod"]
    return [
        "Write a short space adventure story for a young child about kindness and friendship.",
        f"Tell a gentle story where {hero.id} and {friend.id} notice a warning sign and help a drifting {pod.label}.",
        "Use a small foreshadowing clue early in the story, then pay it off with a helpful repair later.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    pod = world.facts["pod"]
    bot = world.facts["bot"]
    return [
        QAItem(
            question=f"Who was the story mainly about?",
            answer=f"It was mainly about {hero.id}, who stayed gentle and brave at Moon Harbor.",
        ),
        QAItem(
            question=f"What did {friend.id} notice that hinted trouble later?",
            answer=f"{friend.id} noticed that the warning light on {pod.label} blinked twice, which hinted the latch might fail later.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} help {bot.id}?",
            answer=f"They worked together to close and seal the drifting pod so {bot.id} could be safe again.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The pod was sealed, the drifting stopped, and the friends ended the story calm and happy under the station window.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a spaceship or station window for?",
            answer="A station window lets people look out into space and see stars, planets, and faraway ships.",
        ),
        QAItem(
            question="Why is kindness useful during a rescue?",
            answer="Kindness helps people stay calm, listen to each other, and work together without making the problem worse.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a clue early in the story that hints something important may happen later.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: v for k, v in e.memes.items() if abs(v) > 1e-9}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(parts)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("station", "moon_harbor"))
    lines.append(asp.fact("place", "observation_deck"))
    lines.append(asp.fact("hero", "nova"))
    lines.append(asp.fact("friend", "pip"))
    lines.append(asp.fact("pod", "cargo_pod"))
    lines.append(asp.fact("bot", "starling_bot"))
    lines.append(asp.fact("foreshadow", "warning_light"))
    lines.append(asp.fact("trait", "kindness"))
    lines.append(asp.fact("trait", "friendship"))
    lines.append(asp.fact("trait", "foreshadowing"))
    return "\n".join(lines)


ASP_RULES = r"""
hero_story(H) :- hero(H).
friendship_story(H,F) :- hero(H), friend(F).
foreshadows(P) :- foreshadow(P).
kind_rescue(H,F,P) :- hero(H), friend(F), pod(P), foreshadows(warning_light).
safe_end(H,F,P) :- kind_rescue(H,F,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe_end/3."))
    shown = set(asp.atoms(model, "safe_end"))
    expected = {("nova", "pip", "cargo_pod")}
    if shown == expected:
        print("OK: ASP and Python story gate agree.")
        return 0
    print("MISMATCH:")
    print("  ASP:", sorted(shown))
    print("  PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small space-adventure story world about kindness and friendship.")
    ap.add_argument("--station", choices=["moon_harbor"], default="moon_harbor")
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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
    hero_name = args.name or rng.choice(["Nova", "Luna", "Orion", "Mira", "Kite"])
    friend_name = args.friend_name or rng.choice(["Pip", "Beep", "Dot", "Zing"])
    if hero_name == friend_name:
        raise StoryError("The hero and friend need different names.")
    return StoryParams(
        station=args.station,
        hero_name=hero_name,
        friend_name=friend_name,
    )


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
        print(asp_program("#show safe_end/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show safe_end/3."))
        print(asp.atoms(model, "safe_end"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        params = StoryParams()
        params.seed = base_seed
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
