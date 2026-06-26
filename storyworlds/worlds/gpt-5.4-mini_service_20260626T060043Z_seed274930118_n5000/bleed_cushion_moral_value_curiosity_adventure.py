#!/usr/bin/env python3
"""
storyworlds/worlds/bleed_cushion_moral_value_curiosity_adventure.py
===================================================================

A small Adventure-style story world about curiosity, a moral choice, and a
careful rescue with a cushion.

Premise:
- A curious child wants to explore a risky place.
- Someone gets a small bleed from a scrape or prick.
- A cushion can help solve the problem in a gentle, practical way.

This world keeps the prose child-facing and state-driven: curiosity can push the
hero forward, but the story turns when the hero notices someone is hurt and
chooses a kinder, safer course.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Place:
    id: str
    label: str
    detail: str
    risky: bool = False


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    kind: str = "thing"


@dataclass
class Character:
    id: str
    name: str
    role: str
    curious: float = 0.0
    moral_value: float = 0.0
    hurt: float = 0.0
    bleed: float = 0.0
    fear: float = 0.0
    joy: float = 0.0
    carrying: list[str] = field(default_factory=list)

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class World:
    place: Place
    hero: Character
    friend: Character
    cushion: ObjectThing
    event: str = ""
    turned_back: bool = False
    helped: bool = False
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


@dataclass
class StoryParams:
    place: str
    seed: Optional[int] = None


PLACES = {
    "old_bridge": Place(
        id="old_bridge",
        label="the old bridge",
        detail="It creaked over a narrow stream and had a low ledge that could scratch a knee.",
        risky=True,
    ),
    "garden_wall": Place(
        id="garden_wall",
        label="the garden wall",
        detail="It had a rough stone edge and a hidden vine trail behind it.",
        risky=True,
    ),
    "camp_path": Place(
        id="camp_path",
        label="the camp path",
        detail="It wound between pine roots and a few sharp stones.",
        risky=True,
    ),
    "harbor_steps": Place(
        id="harbor_steps",
        label="the harbor steps",
        detail="The wet steps shone like silver and the rope post stood close by.",
        risky=True,
    ),
}

NAMES = ["Mina", "Toby", "Lina", "Noah", "Riya", "Eli"]
FRIEND_NAMES = ["Pip", "Sora", "Juno", "Ari", "Nell", "Milo"]
ROLES = ["explorer", "scout", "helper", "traveler"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure-style story world about curiosity, moral value, and a cushion.")
    ap.add_argument("--place", choices=sorted(PLACES))
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
    place = args.place or rng.choice(list(PLACES))
    return StoryParams(place=place)


def _choose_name(rng: random.Random, used: set[str]) -> str:
    pool = [n for n in NAMES if n not in used]
    if not pool:
        pool = NAMES[:]
    return rng.choice(pool)


def _choose_friend(rng: random.Random, used: set[str]) -> str:
    pool = [n for n in FRIEND_NAMES if n not in used]
    if not pool:
        pool = FRIEND_NAMES[:]
    return rng.choice(pool)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else 0)
    place = PLACES[params.place]

    hero = Character(
        id="hero",
        name=_choose_name(rng, set()),
        role=rng.choice(ROLES),
        curious=1.0,
        moral_value=0.2,
        joy=0.4,
    )
    friend = Character(
        id="friend",
        name=_choose_friend(rng, {hero.name}),
        role="friend",
        curious=0.3,
        moral_value=0.4,
        joy=0.2,
    )
    cushion = ObjectThing(
        id="cushion",
        label="cushion",
        phrase="a soft cushion",
    )

    world = World(place=place, hero=hero, friend=friend, cushion=cushion)

    # Act 1: setup
    world.say(
        f"{hero.name} was a curious little {hero.role} who loved finding hidden corners of {place.label}."
    )
    world.say(
        f"{friend.name} liked walking beside {hero.name}, and together they noticed every twig, stone, and shadow."
    )
    world.say(place.detail)

    # Act 2: the risky turn
    world.para()
    world.say(
        f"One day, {hero.name} spotted something tucked near the path and hurried closer, because curiosity pulled hard."
    )
    world.event = "explore"
    if place.risky:
        world.say(
            f"The ground shifted under {friend.name}'s foot, and a sharp edge gave a small bleed at the ankle."
        )
        friend.hurt = 1.0
        friend.bleed = 1.0
        hero.fear = 0.5
        hero.curious = 1.4
        hero.moral_value = 0.6
    else:
        world.say(
            f"There was no harm, but the moment still asked {hero.name} to think carefully before going farther."
        )

    # Act 3: moral choice and cushion aid
    world.para()
    if friend.bleed >= 1.0:
        world.say(
            f"{hero.name} stopped at once. Curiosity was still there, but moral value mattered more than rushing on."
        )
        world.say(
            f"{hero.name} fetched {cushion.phrase} and pressed it gently to the scrape while calling for help."
        )
        world.helped = True
        friend.bleed = 0.0
        friend.hurt = 0.2
        hero.moral_value = 1.0
        hero.joy = 0.9
        hero.fear = 0.1
        world.turned_back = True
        world.say(
            f"After that, {hero.name} guided {friend.name} to sit on the cushion, and the two of them waited safely until the bleeding stopped."
        )
        world.say(
            f"Then they walked home slowly, with the cushion tucked under one arm and a kinder kind of bravery in {hero.name}'s chest."
        )
    else:
        world.say(
            f"{hero.name} chose to stay back, and the cushion became a soft seat for a peaceful rest before the next adventure."
        )
        hero.moral_value = 0.9
        hero.joy = 0.8

    world.facts.update(
        hero=hero,
        friend=friend,
        place=place,
        cushion=cushion,
        helped=world.helped,
        turned_back=world.turned_back,
        bleed_fixed=(friend.bleed == 0.0),
    )

    story_qa = [
        QAItem(
            question=f"Who was the curious explorer in the story?",
            answer=f"{hero.name} was the curious {hero.role} who led the adventure.",
        ),
        QAItem(
            question=f"What happened when the ground shifted near {place.label}?",
            answer=f"{friend.name} got a small bleed at the ankle, so the adventure turned into a careful rescue.",
        ),
        QAItem(
            question=f"How did {hero.name} help after seeing the bleed?",
            answer=f"{hero.name} fetched {cushion.phrase} and used it to help {friend.name} sit safely while they waited.",
        ),
        QAItem(
            question=f"What did curiosity and moral value change in {hero.name}?",
            answer=f"Curiosity made {hero.name} want to explore, but moral value made {hero.name} stop and help instead of going on alone.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and discover new things.",
        ),
        QAItem(
            question="What does moral value mean?",
            answer="Moral value means caring about what is right and kind, even when it is tempting to do something else.",
        ),
        QAItem(
            question="What is a cushion for?",
            answer="A cushion is a soft object you can sit on or use to make something more comfortable and gentle.",
        ),
        QAItem(
            question="What should you do if someone is bleeding?",
            answer="You should get help from a grown-up or emergency helper right away and keep the person as safe and calm as possible.",
        ),
    ]

    prompts = [
        f"Write an adventure story about a curious child at {place.label} who makes a kind choice when someone gets hurt.",
        "Tell a short story that uses the words bleed and cushion and ends with a brave, caring decision.",
        "Write a child-friendly adventure where curiosity leads to trouble, but moral value helps fix it.",
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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


def dump_trace(world: World) -> str:
    h = world.hero
    f = world.friend
    lines = ["--- world model state ---"]
    lines.append(
        f"hero={h.name} curious={h.curious:.1f} moral_value={h.moral_value:.1f} fear={h.fear:.1f} joy={h.joy:.1f}"
    )
    lines.append(
        f"friend={f.name} hurt={f.hurt:.1f} bleed={f.bleed:.1f} joy={f.joy:.1f}"
    )
    lines.append(f"place={world.place.id} helped={world.helped} turned_back={world.turned_back}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
place(P) :- site(P).
curious(H) :- hero(H).
moral(H) :- hero(H).
risky(P) :- site(P), has_edge(P).
bleed(F) :- friend(F), injured(F).
helped(H) :- uses_cushion(H), moral(H), bleed(_).
safe_finish(H) :- helped(H), cushion(C), soft(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("site", pid))
        if place.risky:
            lines.append(asp.fact("has_edge", pid))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("friend", "friend"))
    lines.append(asp.fact("cushion", "cushion"))
    lines.append(asp.fact("soft", "cushion"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:  # pragma: no cover
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show risky/1. #show place/1."))
    risky = {args[0] for args in asp.atoms(model, "risky")}
    python_risky = {pid for pid, p in PLACES.items() if p.risky}
    if risky != python_risky:
        print("MISMATCH between ASP and Python.")
        print("ASP:", sorted(risky))
        print("Python:", sorted(python_risky))
        return 1
    print(f"OK: ASP matches Python for {len(risky)} risky places.")
    return 0


def _asp_summary() -> str:
    import asp
    model = asp.one_model(asp_program("#show risky/1."))
    risky = sorted(a[0] for a in asp.atoms(model, "risky"))
    return "\n".join(risky)


def resolve_all_samples(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        samples = []
        for i, pid in enumerate(sorted(PLACES)):
            p = StoryParams(place=pid, seed=(args.seed or 0) + i)
            samples.append(generate(p))
        return samples

    base = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base)
    samples = []
    seen = set()
    tries = 0
    while len(samples) < args.n and tries < max(50, args.n * 20):
        tries += 1
        params = resolve_params(args, random.Random(base + tries))
        params.seed = base + tries
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show risky/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as e:
            raise SystemExit(f"ASP mode unavailable: {e}")
        print(_asp_summary())
        return

    samples = resolve_all_samples(args)

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
