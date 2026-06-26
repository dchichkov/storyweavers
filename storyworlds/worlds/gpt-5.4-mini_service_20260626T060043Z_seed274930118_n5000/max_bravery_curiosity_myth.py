#!/usr/bin/env python3
"""
A small myth-style storyworld about a brave, curious child named Max who faces
a simple wonder, learns the right question to ask, and wins a gentle victory.
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
# World data
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Place:
    id: str
    name: str
    epithet: str
    wonder: str
    sound: str
    offers: str
    danger: str


@dataclass(frozen=True)
class Relic:
    id: str
    name: str
    epithet: str
    glimmer: str
    use: str
    owner: str


@dataclass(frozen=True)
class Guide:
    id: str
    name: str
    title: str
    advice: str


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"distance": 0.0}
        if not self.memes:
            self.memes = {"bravery": 0.0, "curiosity": 0.0, "wonder": 0.0, "fear": 0.0}


@dataclass
class World:
    place: Place
    relic: Relic
    guide: Guide
    hero: Entity
    history: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, line: str) -> None:
        if line:
            self.history.append(line)

    def render(self) -> str:
        return "\n\n".join(self.history)


@dataclass
class StoryParams:
    place: str
    relic: str
    guide: str
    name: str = "Max"
    seed: Optional[int] = None


PLACES: dict[str, Place] = {
    "mountain": Place(
        id="mountain",
        name="the silver mountain",
        epithet="old as a song",
        wonder="a door of blue stone",
        sound="the wind sang through the cracks like a flute",
        offers="a path that only the humble could see",
        danger="a steep black ledge",
    ),
    "forest": Place(
        id="forest",
        name="the whispering forest",
        epithet="deep with moss and moon-shadow",
        wonder="a pool that showed tomorrow's moon",
        sound="the leaves kept a secret murmuring",
        offers="a trail of bright shells under the roots",
        danger="a circle of thorny briars",
    ),
    "shore": Place(
        id="shore",
        name="the moonlit shore",
        epithet="bright with foam",
        wonder="a shell that held a star's echo",
        sound="the tide tapped softly on the stones",
        offers="a path drawn in silver foam",
        danger="a sudden wave over the black rocks",
    ),
}

RELICS: dict[str, Relic] = {
    "torch": Relic(
        id="torch",
        name="a cedar torch",
        epithet="wrapped in red thread",
        glimmer="a warm gold flame",
        use="light the hidden way",
        owner="the village elder",
    ),
    "water": Relic(
        id="water",
        name="a cup of spring water",
        epithet="clear as a promise",
        glimmer="a cold bright shimmer",
        use="wake a sleeping gate",
        owner="the sleeping gate",
    ),
    "feather": Relic(
        id="feather",
        name="a hawk feather",
        epithet="white at the tip",
        glimmer="a sharp silver sheen",
        use="call the wind to turn",
        owner="the wind itself",
    ),
}

GUIDES: dict[str, Guide] = {
    "owl": Guide(
        id="owl",
        name="an owl",
        title="moon-eyed guide",
        advice="Ask the mountain what it is hiding before you try to climb it.",
    ),
    "stream": Guide(
        id="stream",
        name="a stream",
        title="clear-voiced guide",
        advice="Follow the smallest sound, because small sounds often lead to great doors.",
    ),
    "moss": Guide(
        id="moss",
        name="moss on a stone",
        title="soft-handed guide",
        advice="Kneel first, and you will notice the safe path under the proud one.",
    ),
}

CURATED = [
    StoryParams(place="mountain", relic="torch", guide="owl", name="Max"),
    StoryParams(place="forest", relic="water", guide="stream", name="Max"),
    StoryParams(place="shore", relic="feather", guide="moss", name="Max"),
]


# ---------------------------------------------------------------------------
# Logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    relic = RELICS[params.relic]
    guide = GUIDES[params.guide]
    hero = Entity(
        id=params.name,
        kind="character",
        label=params.name,
        phrase=f"little brave {params.name}",
        meters={"distance": 0.0},
        memes={"bravery": 1.0, "curiosity": 1.0, "wonder": 0.0, "fear": 0.0},
    )
    return World(place=place, relic=relic, guide=guide, hero=hero)


def tell_story(world: World) -> None:
    h = world.hero
    p = world.place
    r = world.relic
    g = world.guide

    world.say(
        f"Long ago, little {h.label} wandered to {p.name}, {p.epithet}, "
        f"where {p.sound}."
    )
    world.say(
        f"There, {h.label} found {r.name}, {r.epithet}, glowing with {r.glimmer}."
    )
    h.memes["curiosity"] += 1.0
    h.memes["wonder"] += 1.0
    world.say(
        f"{h.label} wanted to know who had left it there, for {r.name} seemed to "
        f"promise a task: {r.use}."
    )
    world.say(
        f"Then {g.name}, the {g.title}, came softly from the shadows and said, "
        f'"{g.advice}"'
    )
    world.say(
        f"{h.label} looked toward {p.danger}, and fear rose like a dark wave."
    )
    h.memes["fear"] += 1.0
    h.memes["bravery"] += 1.0
    world.say(
        f"But {h.label} remembered that bravery is not the absence of fear; it is "
        f"taking one careful step while fear still watches."
    )
    h.meters["distance"] += 1.0
    world.say(
        f"So {h.label} asked the right question, followed {p.offers}, and reached "
        f"the hidden place without falling."
    )
    world.say(
        f"When the {r.name} was lifted, the door opened, and a warm road of light "
        f"shone out over {p.name}."
    )
    world.say(
        f"{h.label} went home with an easier heart, and the myth of the small door "
        f"became a story the village could tell by firelight."
    )
    world.facts.update(
        place=p,
        relic=r,
        guide=g,
        hero=h,
        danger=p.danger,
        task=r.use,
        ending="door opened",
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    h = world.hero
    p = world.place
    r = world.relic
    return [
        f'Write a short myth for children about {h.label} finding {r.name} at {p.name}.',
        f"Tell a gentle legend where bravery and curiosity help {h.label} face a hidden danger.",
        f'Write a tiny mythic story that includes "{h.label}", a wonder, and a wise guide.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.place
    r = world.relic
    g = world.guide
    h = world.hero
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {h.label}, a little hero who is both brave and curious.",
        ),
        QAItem(
            question=f"What did {h.label} find at {p.name}?",
            answer=f"{h.label} found {r.name}, which glimmered and promised to {r.use}.",
        ),
        QAItem(
            question=f"Who gave {h.label} advice?",
            answer=f"{g.name}, the {g.title}, gave advice and told {h.label} to ask before acting.",
        ),
        QAItem(
            question=f"What problem did {h.label} face?",
            answer=f"{h.label} had to pass {p.danger} to reach the hidden wonder.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {h.label} succeeding, the hidden door opening, and the village gaining a new tale.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing what is right or needed even when you feel afraid.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to learn, explore, and ask questions.",
        ),
        QAItem(
            question="What makes a myth special?",
            answer="A myth often feels ancient and magical, with wonders, wise voices, and a lesson inside the tale.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(X) :- hero_name(X).
place(X) :- place_name(X).
relic(X) :- relic_name(X).
guide(X) :- guide_name(X).

combination(P, R, G) :- place(P), relic(R), guide(G).
valid_story(P, R, G) :- combination(P, R, G).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    lines.append(asp.fact("hero_name", "max"))
    for p in PLACES:
        lines.append(asp.fact("place_name", p))
    for r in RELICS:
        lines.append(asp.fact("relic_name", r))
    for g in GUIDES:
        lines.append(asp.fact("guide_name", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show combination/3."))
    return sorted(set(asp.atoms(model, "combination")))


def asp_verify() -> int:
    py = {(p, r, g) for p in PLACES for r in RELICS for g in GUIDES}
    asp_set = set(asp_valid_combos())
    if py != asp_set:
        print("MISMATCH between Python and ASP.")
        if py - asp_set:
            print("Only in Python:", sorted(py - asp_set))
        if asp_set - py:
            print("Only in ASP:", sorted(asp_set - py))
        return 1
    print(f"OK: ASP parity verified for {len(py)} combinations.")
    return 0


# ---------------------------------------------------------------------------
# Story interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld of bravery and curiosity.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--name", default="Max")
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
    place = args.place or rng.choice(list(PLACES))
    relic = args.relic or rng.choice(list(RELICS))
    guide = args.guide or rng.choice(list(GUIDES))
    if args.name and args.name != "Max" and args.name.strip().lower() != "max":
        raise StoryError("This world is centered on Max; use the default name Max.")
    return StoryParams(place=place, relic=relic, guide=guide, name="Max", seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
        print()
        print("--- trace ---")
        print(sample.world.facts)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show combination/3.\n#show valid_story/3."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} combinations:")
        for p, r, g in combos:
            print(f"  {p} / {r} / {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} / {p.relic} / {p.guide}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
