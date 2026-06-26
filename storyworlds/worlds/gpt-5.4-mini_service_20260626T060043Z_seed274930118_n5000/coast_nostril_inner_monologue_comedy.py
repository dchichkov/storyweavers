#!/usr/bin/env python3
"""
A small Storyweavers world: a comedy of coastal confusion and a very talkative
inner monologue.

Premise:
A child at the coast wants to impress others, but a tiny problem with a nostril
turns the outing into a silly, state-driven mess. The child thinks through the
problem, tries a few bad ideas, gets help, and ends with a funny, relieved
resolution.

The world model tracks:
- physical meters: windblown sand, saltwater, tissue use, distance to shelter
- emotional memes: embarrassment, worry, relief, confidence, amusement

The prose is generated from the simulated world, not a frozen template.
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

NAME_POOL = ["Milo", "Nina", "Toby", "Luna", "Pip", "Ivy", "Theo", "Zara"]
ADJ_POOL = ["tiny", "curious", "bright-eyed", "silly", "careful", "cheerful"]
HELPER_POOL = ["mom", "dad", "a friend", "an older cousin"]
COAST_FEATURES = ["pier", "dunes", "boardwalk", "rocky shore", "shell path"]


@dataclass
class StoryParams:
    name: str = "Milo"
    helper: str = "mom"
    coast_feature: str = "pier"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["sand", "salt", "tissue", "distance"]:
            self.meters.setdefault(k, 0.0)
        for k in ["embarrassment", "worry", "relief", "confidence", "amusement"]:
            self.memes.setdefault(k, 0.0)


@dataclass
class World:
    place: str = "the coast"
    feature: str = "pier"
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        import copy as _copy

        w = World(place=self.place, feature=self.feature)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


def inner_thought(world: World, text: str) -> None:
    world.say(f'[{text}]')


def tell_world(params: StoryParams) -> World:
    w = World(feature=params.coast_feature)
    child = w.add(Entity(
        id=params.name,
        kind="character",
        label=params.name,
        traits=["little", random.choice(ADJ_POOL)],
    ))
    helper = w.add(Entity(id="helper", kind="character", label=params.helper))
    tissue = w.add(Entity(id="tissue", label="a crumpled tissue"))
    w.facts.update(child=child, helper=helper, tissue=tissue, params=params)

    # Act 1
    w.say(
        f"At the coast, {child.id} stood near the {w.feature} and felt the wind ruffle {child.id}'s hair."
    )
    w.say(
        f"{child.id} liked the salty air, the calling birds, and the way the shore looked like a long shiny grin."
    )
    inner_thought(w, f"Today I will look very cool. Nobody will notice my nose doing anything weird.")
    w.para()

    # Act 2
    child.memes["worry"] += 1
    child.memes["embarrassment"] += 1
    child.meters["salt"] += 1
    child.meters["distance"] = 6
    w.say(
        f"Then a burst of sea spray tickled {child.id}'s nostril, and {child.id} had to sniff twice in a row."
    )
    inner_thought(w, f"Uh-oh. That was not a cool nose sound. That was a trumpet with homework.")
    w.say(
        f"{child.id} tried to pretend nothing happened, but the breeze kept wagging the salty tickle back and forth."
    )
    inner_thought(w, f"If I rub my nose, maybe the whole coast will look away. Or applaud. Please applaud.")
    w.say(
        f"Instead of helping, the wind made {child.id}'s nostril twitch again, and {child.id} groaned softly."
    )
    w.facts["problem"] = "salty tickle in nostril"
    w.para()

    # Act 3
    child.memes["amusement"] += 1
    child.meters["tissue"] += 1
    child.memes["confidence"] += 1
    child.memes["worry"] = 0
    child.memes["embarrassment"] = 0
    child.meters["distance"] = 1

    w.say(
        f"{params.helper} noticed the squirmy face and held out the tissue with a grin."
    )
    inner_thought(w, f"A tissue. Of course. The mighty solution to a tiny nose drama.")
    w.say(
        f"{child.id} laughed, took the tissue, and wiped away the salty tickle."
    )
    w.say(
        f"Then {child.id} could breathe again without making mysterious sniffing music."
    )
    inner_thought(w, f"Victory. I have defeated the coast's sneakiest prank, and my nostril has been demoted.")
    w.say(
        f"By the time they walked past the {w.feature}, {child.id} was smiling, the wind felt playful instead of tricky, and the whole coast seemed to giggle along."
    )
    w.facts["resolved"] = True
    w.facts["inner_monologue"] = True
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a funny story about a child named {p.name} at the coast whose nostril gets tickled by sea spray.",
        f"Tell a comedy story with a strong inner monologue where {p.name} tries to stay cool at the shore, then needs help from {p.helper}.",
        f"Create a short seaside story about a silly nose problem, a tissue, and a relieved ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    return [
        QAItem(
            question=f"Where is {p.name} when the story begins?",
            answer=f"{p.name} is at the coast near the {p.coast_feature}, watching the windy shore.",
        ),
        QAItem(
            question=f"What tiny problem makes {p.name} feel embarrassed?",
            answer=f"A burst of sea spray tickles {p.name}'s nostril and makes {p.name} sniff and squirm.",
        ),
        QAItem(
            question=f"How does {p.helper} help {p.name}?",
            answer=f"{p.helper} offers a tissue, and that helps {p.name} wipe away the salty tickle and feel better.",
        ),
        QAItem(
            question=f"What changes by the end of the story?",
            answer=f"{p.name} stops worrying, starts laughing, and can breathe comfortably again while walking along the coast.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sea spray?",
            answer="Sea spray is tiny drops of salty water blown off the ocean by the wind.",
        ),
        QAItem(
            question="What is a tissue used for?",
            answer="A tissue is a soft piece of paper used for wiping a nose or cleaning little messes.",
        ),
        QAItem(
            question="Why can wind feel cold at the coast?",
            answer="Wind can feel cold at the coast because it carries cooler air and salty moisture across your skin.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.kind}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
% A child is amused if the salty tickle gets solved with a tissue.
solved(Child) :- problem(Child, nostril_tickle), has_tissue(Child).
amused(Child) :- solved(Child).

% The coast joke is valid only when the problem is about wind, salt, and a nostril.
valid_story(Place, Feature) :- place(Place), feature(Feature), coast(Place), feature_of(Place, Feature).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("coast", "the_coast"),
        asp.fact("place", "the_coast"),
        asp.fact("feature", "pier"),
        asp.fact("feature", "dunes"),
        asp.fact("feature", "boardwalk"),
        asp.fact("feature", "rocky_shore"),
        asp.fact("feature", "shell_path"),
    ]
    for f in COAST_FEATURES:
        lines.append(asp.fact("feature_of", "the_coast", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/2."))
    atoms = set(asp.atoms(model, "valid_story"))
    expected = {("the_coast", f) for f in COAST_FEATURES}
    if atoms == expected:
        print(f"OK: ASP parity matches ({len(atoms)} valid story features).")
        return 0
    print("MISMATCH between ASP and Python facts:")
    print("  ASP:", sorted(atoms))
    print("  PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedic coast storyworld with inner monologue.")
    ap.add_argument("--name", choices=NAME_POOL)
    ap.add_argument("--helper", choices=HELPER_POOL)
    ap.add_argument("--coast-feature", choices=COAST_FEATURES)
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
    return StoryParams(
        name=args.name or rng.choice(NAME_POOL),
        helper=args.helper or rng.choice(HELPER_POOL),
        coast_feature=args.coast_feature or rng.choice(COAST_FEATURES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(asp.atoms(model, "valid_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for i, feature in enumerate(COAST_FEATURES):
            p = StoryParams(
                name=NAME_POOL[i % len(NAME_POOL)],
                helper=HELPER_POOL[i % len(HELPER_POOL)],
                coast_feature=feature,
                seed=base_seed + i,
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
