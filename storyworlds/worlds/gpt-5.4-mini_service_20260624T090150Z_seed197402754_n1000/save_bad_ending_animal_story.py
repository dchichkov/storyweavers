#!/usr/bin/env python3
"""
storyworlds/worlds/save_bad_ending_animal_story.py
==================================================

A small animal-story world about a rescue that does *not* end well.

Seed tale:
---
A little mouse saw a duckling in trouble near a rain ditch. The mouse wanted to
save the duckling, but the ditch was too deep and the rain kept falling. The
mouse called for help and tried hard, yet the duckling drifted away before help
could arrive. The mouse went home wet and sad, wishing things had gone better.

World model:
---
- Characters are small animals with body and mood state.
- A risky place holds one animal in danger.
- A helper may try to save the animal using a tool.
- The rescue can fail if the helper is too small, too late, or lacks the right
  tool.
- The ending is intentionally bad, but still complete and causal: the world
  changes because the rescue fails.

Narrative instruments:
---
- premise: the helper notices danger
- tension: the helper tries and the rescue is not enough
- turn: rain, distance, or a broken tool makes the problem worse
- resolution: a sad ending image shows what changed
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


@dataclass
class Animal:
    id: str
    species: str
    name: str
    size: str
    home: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    depth: str
    slippery: bool = False
    water: bool = False


@dataclass
class Tool:
    id: str
    label: str
    kind: str
    helps: set[str]


@dataclass
class StoryParams:
    helper: str
    helper_name: str
    helper_size: str
    helper_home: str
    victim: str
    victim_name: str
    victim_size: str
    victim_home: str
    place: str
    tool: str
    seed: Optional[int] = None


@dataclass
class World:
    helper: Animal
    victim: Animal
    place: Place
    tool: Tool
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts["story"]

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for a in (self.helper, self.victim):
            meters = {k: v for k, v in a.meters.items() if v}
            memes = {k: v for k, v in a.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            lines.append(f"  {a.name:10} ({a.species}) {' '.join(bits)}")
        lines.append(f"  place={self.place.label} depth={self.place.depth} slippery={self.place.slippery}")
        lines.append(f"  tool={self.tool.label}")
        return "\n".join(lines)


ANIMALS = {
    "mouse": ("mouse", "little mouse", "small", "burrow"),
    "rabbit": ("rabbit", "little rabbit", "small", "warren"),
    "squirrel": ("squirrel", "little squirrel", "small", "nest"),
    "cat": ("cat", "young cat", "small", "home"),
    "badger": ("badger", "small badger", "medium", "den"),
}

PLACES = {
    "ditch": Place("ditch", "the rain ditch", "deep", slippery=True, water=True),
    "creek": Place("creek", "the creek bank", "shallow", slippery=True, water=True),
    "pond": Place("pond", "the pond edge", "deep", slippery=True, water=True),
    "fence": Place("fence", "the muddy fence line", "high", slippery=False, water=False),
}

TOOLS = {
    "stick": Tool("stick", "a long stick", "reach", {"reach"}),
    "leaf": Tool("leaf", "a wide leaf", "cover", {"cover"}),
    "net": Tool("net", "a tiny net", "catch", {"catch"}),
    "rope": Tool("rope", "a short rope", "pull", {"pull"}),
}

CURATED = [
    StoryParams("mouse", "Milo", "small", "burrow", "duckling", "Daisy", "small", "nest", "ditch", "stick"),
    StoryParams("rabbit", "Ruby", "small", "warren", "kitten", "Pip", "small", "home", "creek", "net"),
    StoryParams("squirrel", "Nib", "small", "nest", "froglet", "Finn", "small", "pond", "leaf"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal rescue story world with a bad ending.")
    ap.add_argument("--helper", choices=sorted(ANIMALS))
    ap.add_argument("--victim", choices=sorted(ANIMALS))
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--helper-name")
    ap.add_argument("--victim-name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    helper = args.helper or rng.choice(list(ANIMALS))
    victim = args.victim or rng.choice([a for a in ANIMALS if a != helper])
    place = args.place or rng.choice(list(PLACES))
    tool = args.tool or rng.choice(list(TOOLS))
    if helper == victim:
        raise StoryError("helper and victim must be different animals")
    if place not in PLACES:
        raise StoryError("unknown place")
    if tool not in TOOLS:
        raise StoryError("unknown tool")
    h = ANIMALS[helper]
    v = ANIMALS[victim]
    return StoryParams(
        helper=helper,
        helper_name=args.helper_name or rng.choice(["Milo", "Ruby", "Nip", "Pip", "Tess", "Sage"]),
        helper_size=h[2],
        helper_home=h[3],
        victim=victim,
        victim_name=args.victim_name or rng.choice(["Daisy", "Finn", "Nora", "Luna", "Otto", "Bea"]),
        victim_size=v[2],
        victim_home=v[3],
        place=place,
        tool=tool,
    )


def simulate(params: StoryParams) -> World:
    helper = Animal(params.helper, ANIMALS[params.helper][0], params.helper_name, params.helper_size, params.helper_home)
    victim = Animal(params.victim, ANIMALS[params.victim][0], params.victim_name, params.victim_size, params.victim_home)
    place = PLACES[params.place]
    tool = TOOLS[params.tool]
    world = World(helper=helper, victim=victim, place=place, tool=tool)

    helper.memes["worry"] = 1
    helper.memes["hope"] = 1
    victim.memes["fear"] = 1
    victim.meters["wet"] = 1 if place.water else 0
    victim.meters["stuck"] = 1
    helper.meters["tired"] = 0

    if tool.kind == "reach":
        helper.meters["reach"] = 1
    elif tool.kind == "catch":
        helper.meters["catch"] = 1
    elif tool.kind == "pull":
        helper.meters["pull"] = 1

    story = []
    story.append(f"Little {helper.name} was a {helper.species} who loved quiet mornings near {place.label}.")
    story.append(f"One rainy day, {helper.name} spotted {victim.name} the {victim.species} in trouble by the water.")
    story.append(f"{victim.name} was stuck close to the edge and could not get back to safe ground.")
    story.append(f"{helper.name} wanted to save {victim.name}, so {helper.pronoun().capitalize()} hurried to get {tool.label}.")

    helper.meters["tired"] += 1
    helper.memes["brave"] = 1
    victim.memes["hope"] = 1

    if place.depth == "deep":
        helper.memes["fear"] += 1
        story.append(f"But the water was too deep, and the muddy ground kept slipping under little feet.")
    elif place.depth == "high":
        story.append(f"But the ledge was too high, and the small animals could not reach each other well.")
    else:
        story.append(f"But the bank was slick, and every careful step felt wobbly.")

    if tool.kind == "reach":
        story.append(f"{helper.name} stretched the long stick out as far as {helper.pronoun('possessive')} paws could go.")
    elif tool.kind == "catch":
        story.append(f"{helper.name} held out the tiny net, but it was too small to do the job.")
    elif tool.kind == "pull":
        story.append(f"{helper.name} tried to tug with the short rope, but it slid right through the wet grass.")
    else:
        story.append(f"{helper.name} tried to use the big leaf, but it only wobbled in the rain.")

    helper.meters["tired"] += 1
    victim.meters["drifted"] = 1

    if place.water:
        story.append(f"Then a cold gust pushed the water along, and {victim.name} drifted farther away.")
    else:
        story.append(f"Then the rain came harder, and {victim.name} slipped out of view behind the mud.")

    helper.memes["sad"] = 1
    helper.memes["failed"] = 1
    victim.memes["hope"] = 0

    story.append(f"By the time help arrived, it was too late.")
    story.append(f"{helper.name} went home wet and shaking, with {tool.label} hanging useless by {helper.pronoun('possessive')} side.")
    story.append(f"The last thing {helper.name} saw was the empty water and the dark, rainy path back home.")

    world.facts.update(
        story=" ".join(story),
        helper=helper,
        victim=victim,
        place=place,
        tool=tool,
        failed=True,
        wet=bool(place.water),
    )
    return world


def generate_prompts(world: World) -> list[str]:
    h = world.facts["helper"]
    v = world.facts["victim"]
    p = world.facts["place"]
    t = world.facts["tool"]
    return [
        f"Write a short animal story about {h.name} the {h.species} trying to save {v.name} near {p.label}.",
        f"Tell a gentle rescue story using {t.label}, but let the rescue end badly.",
        f"Write an animal story with rain, worry, and a failed save at {p.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.facts["helper"]
    v = world.facts["victim"]
    p = world.facts["place"]
    t = world.facts["tool"]
    return [
        QAItem(
            question=f"Who tried to save {v.name}?",
            answer=f"{h.name} the {h.species} tried to save {v.name}."
        ),
        QAItem(
            question=f"What tool did {h.name} use?",
            answer=f"{h.name} tried to use {t.label}."
        ),
        QAItem(
            question=f"Why did the rescue fail at {p.label}?",
            answer=f"The rescue failed because {p.label} was slippery and the danger moved away before help could reach {v.name}."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does it mean to save someone?", answer="To save someone means to help them get out of danger and back to safety."),
        QAItem(question="Why can rain make ground slippery?", answer="Rain makes dirt and stone wet, and wet ground can be slippery and hard to stand on."),
        QAItem(question="Why is it hard for a small animal to rescue another animal alone?", answer="A small animal may be too weak, too short, or too slow to move danger away by itself."),
    ]


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
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
helper(helper).
victim(victim).
place(place).
tool(tool).

bad_ending :- failed, slippery(place).
bad_ending :- failed, deep(place).
save_attempt(helper, victim) :- helper(helper), victim(victim), failed.
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("failed"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/0."))
    has = any(sym.name == "bad_ending" for sym in model)
    if has:
        print("OK: ASP twin produces a bad ending.")
        return 0
    print("MISMATCH: ASP twin did not produce bad_ending.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    return StorySample(
        params=params,
        story=world.facts["story"],
        prompts=generate_prompts(world),
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


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show bad_ending/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, p in enumerate(CURATED):
            p.seed = (base_seed + i)
            samples.append(generate(p))
    else:
        seen = set()
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
