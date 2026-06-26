#!/usr/bin/env python3
"""
A standalone storyworld: law, jujube, flashback, nursery-rhyme style.

This world tells a tiny, child-facing tale about a careful hare who wants to
share a jujube cake, but a stern little law at the gate says no crumbly treats
during the drum parade. A flashback explains why the law was made, and the
ending shows a kinder rule in action.
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
class MeteredEntity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def get_meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.get_meter(key) + amount

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class Place:
    name: str
    has_gate: bool = True
    has_drum_parade: bool = True
    has_jujube_tree: bool = True


@dataclass
class StoryParams:
    place: str = "green_lane"
    seed: Optional[int] = None
    name: str = "Hare"
    friend: str = "Mole"
    law_name: str = "crumb law"
    jujube_name: str = "jujube"
    flashback_age: int = 1


@dataclass
class World:
    place: Place
    hero: MeteredEntity
    friend: MeteredEntity
    law: MeteredEntity
    jujube: MeteredEntity
    memory_opened: bool = False
    law_softened: bool = False
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

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for e in [self.hero, self.friend, self.law, self.jujube]:
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            lines.append(f"  {e.id:8} ({e.kind:6}) {' '.join(bits)}")
        lines.append(f"  memory_opened={self.memory_opened}")
        lines.append(f"  law_softened={self.law_softened}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "green_lane": Place(name="Green Lane", has_gate=True, has_drum_parade=True, has_jujube_tree=True),
    "moon_court": Place(name="Moon Court", has_gate=True, has_drum_parade=False, has_jujube_tree=True),
    "hush_hollow": Place(name="Hush Hollow", has_gate=False, has_drum_parade=True, has_jujube_tree=True),
}

NAMES = ["Hare", "Pip", "Mina", "Toby", "Lulu", "Nell"]
FRIENDS = ["Mole", "Pip", "Pidge", "Wren", "Otter"]
LAW_NAMES = ["crumb law", "tiny law", "gate law", "drum law"]
JUJUBE_NAMES = ["jujube", "jujube cake", "jujube bun", "jujube tart"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A law is strict when a parade is on and the gate wants the crumbs kept tidy.
strict(L) :- law(L), parade(P), gate(G), guards(G,L), P.

% A jujube treat is at risk when it is crumbly and the law is strict.
at_risk(J, L) :- jujube(J), strict(L), crumbly(J).

% A flashback opens when a child remembers why the law began.
flashback_open(H) :- hero(H), remembers(H).

% A softer law appears when the old reason is understood.
softened(L) :- law(L), flashback_open(_), kind_reason(_).

#show strict/1.
#show at_risk/2.
#show flashback_open/1.
#show softened/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    parts: list[str] = []
    for pid, place in PLACES.items():
        parts.append(asp.fact("place", pid))
        if place.has_gate:
            parts.append(asp.fact("gate", pid))
        if place.has_drum_parade:
            parts.append(asp.fact("parade", pid))
        if place.has_jujube_tree:
            parts.append(asp.fact("tree", pid))
    for name in LAW_NAMES:
        parts.append(asp.fact("law", name.replace(" ", "_")))
        parts.append(asp.fact("guards", "gate", name.replace(" ", "_")))
    for j in JUJUBE_NAMES:
        parts.append(asp.fact("jujube", j.replace(" ", "_")))
        parts.append(asp.fact("crumbly", j.replace(" ", "_")))
    parts.append(asp.fact("hero", "hare"))
    parts.append(asp.fact("remembers", "hare"))
    parts.append(asp.fact("kind_reason", "old_mess"))
    return "\n".join(parts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show strict/1.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "strict"))
    expected = {("crumb_law",), ("tiny_law",), ("gate_law",), ("drum_law",)}
    if atoms == expected:
        print("OK: ASP facts and rules agree.")
        return 0
    print("MISMATCH:")
    print("  asp:", sorted(atoms))
    print("  py :", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if not params.law_name.strip():
        raise StoryError("The law must have a name.")
    if not params.jujube_name.strip():
        raise StoryError("The jujube must have a name.")


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    hero = MeteredEntity(id=params.name, kind="character", label=params.name)
    friend = MeteredEntity(id=params.friend, kind="character", label=params.friend)
    law = MeteredEntity(id="law", kind="thing", label=params.law_name)
    jujube = MeteredEntity(id="jujube", kind="thing", label=params.jujube_name)
    return World(place=place, hero=hero, friend=friend, law=law, jujube=jujube)


def narrate_setup(world: World) -> None:
    h, f, l, j = world.hero, world.friend, world.law, world.jujube
    world.say(
        f"{h.label} went to {world.place.name}, where the little gate-law stood tall and neat."
    )
    world.say(
        f"{h.label} held a warm jujube cake, and {f.label} hummed a tune so sweet."
    )
    world.say(
        f"But the law said, \"No crumbly treats at the drum parade gate.\""
    )
    world.facts["law_strict"] = True
    world.facts["jujube_name"] = j.label


def narrate_conflict(world: World) -> None:
    h = world.hero
    h.add_meme("worry", 1)
    h.add_meme("want", 1)
    world.say(
        f"{h.label} looked down at the jujube and felt a tiny ache of dismay."
    )
    world.say(
        f"{h.label} wanted to nibble right then, but the law blocked the way."
    )


def narrate_flashback(world: World, age: int) -> None:
    world.para()
    world.memory_opened = True
    h = world.hero
    h.add_meme("remember", 1)
    world.say(
        f"Then came a flashback, small as a bell: when {h.label} was {age}, the street was a mess."
    )
    world.say(
        f"Jujube crumbs had rolled into the drum lane, and little feet had slipped on the rest."
    )
    world.say(
        f"The gate-law was made to keep the parade bright, not to spoil a child's play."
    )
    world.facts["remembered_reason"] = True


def narrate_resolution(world: World) -> None:
    h, f = world.hero, world.friend
    world.para()
    world.law_softened = True
    world.say(
        f"{h.label} smiled and bowed to the law, then offered to eat the jujube at the tree."
    )
    world.say(
        f"{f.label} brought a napkin and a plate, and the crumbs fell gently, one-two-three."
    )
    world.say(
        f"So the gate stayed tidy, the drum parade rang clear, and the jujube tasted like joy."
    )
    world.say(
        f"{h.label} learned that a law can be kind when it keeps a small world safe for every girl and boy."
    )


def generate_story(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = build_world(params)
    narrate_setup(world)
    narrate_conflict(world)
    narrate_flashback(world, params.flashback_age)
    narrate_resolution(world)
    world.facts.update(
        hero=world.hero,
        friend=world.friend,
        law=world.law,
        jujube=world.jujube,
        place=world.place,
        params=params,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a nursery-rhyme style story about {p.name}, a jujube, and a law at {world.place.name}.",
        f"Tell a child-friendly tale where a little law stops crumbly jujube treats near a parade gate, then a flashback explains why.",
        f"Make a tiny rhyming story with a flashback, a law, and a jujube ending in a kinder choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h, f, l, j = world.hero, world.friend, world.law, world.jujube
    return [
        QAItem(
            question=f"Who wanted to eat the jujube at {world.place.name}?",
            answer=f"{h.label} wanted to eat the {j.label} there.",
        ),
        QAItem(
            question=f"What did the law say at the gate?",
            answer=f"The law said, \"No crumbly treats at the drum parade gate.\"",
        ),
        QAItem(
            question="Why did the story have a flashback?",
            answer="The flashback showed that crumbs had once made the parade lane slippery, so the law was made to keep everyone safe.",
        ),
        QAItem(
            question=f"How did {h.label} solve the problem?",
            answer=f"{h.label} waited to eat the {j.label} by the tree, with {f.label} and a plate, so the gate stayed tidy.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a law?",
            answer="A law is a rule that helps people stay safe and know what to do.",
        ),
        QAItem(
            question="What is a jujube?",
            answer="A jujube is a small sweet fruit, and people may also use the word for a baked treat made with it.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a memory scene that goes back to an earlier time to explain something in the story.",
        ),
        QAItem(
            question="Why do parade places like clean paths?",
            answer="Clean paths help little feet walk safely, and they keep the drums and dancing from getting messy.",
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme storyworld with law, jujube, and a flashback.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--law-name", choices=LAW_NAMES, dest="law_name")
    ap.add_argument("--jujube-name", choices=JUJUBE_NAMES, dest="jujube_name")
    ap.add_argument("--flashback-age", type=int, default=1, dest="flashback_age")
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
    place = args.place or rng.choice(list(PLACES.keys()))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    law_name = args.law_name or rng.choice(LAW_NAMES)
    jujube_name = args.jujube_name or rng.choice(JUJUBE_NAMES)
    flashback_age = args.flashback_age
    if flashback_age < 1:
        raise StoryError("flashback-age must be at least 1.")
    return StoryParams(
        place=place,
        seed=args.seed,
        name=name,
        friend=friend,
        law_name=law_name,
        jujube_name=jujube_name,
        flashback_age=flashback_age,
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_story(params)
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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def asp_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show strict/1."))
    return sorted(set(asp.atoms(model, "strict")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show strict/1.\n#show at_risk/2.\n#show flashback_open/1.\n#show softened/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP strict laws:", asp_stories())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="green_lane", name="Hare", friend="Mole", law_name="crumb law", jujube_name="jujube cake", flashback_age=1),
            StoryParams(place="moon_court", name="Lulu", friend="Wren", law_name="gate law", jujube_name="jujube tart", flashback_age=2),
            StoryParams(place="hush_hollow", name="Mina", friend="Pidge", law_name="tiny law", jujube_name="jujube bun", flashback_age=1),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
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
