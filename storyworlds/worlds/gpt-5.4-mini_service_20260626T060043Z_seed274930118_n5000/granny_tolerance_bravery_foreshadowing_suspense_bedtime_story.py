#!/usr/bin/env python3
"""
A small bedtime-story world about a child, a granny, and a little night-time
worry that turns into bravery, tolerance, and a calm ending.

The source tale behind this world:
- A child visits Granny at bedtime.
- A creaky house, a shadow, and a missing nightlight create suspense.
- Granny gently encourages tolerance of small scary feelings.
- The child uses bravery, checks the clue, and discovers the "monster" is only
  a coat on a chair.
- The room feels safe again, and the child falls asleep with Granny nearby.
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
# Parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    name: str = "Mina"
    child_role: str = "grandchild"
    granny_name: str = "Granny"
    setting: str = "granny's cozy house"
    bedtime_object: str = "nightlight"
    spooky_clue: str = "a long shadow"
    comfort_item: str = "a warm blanket"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they" if self.kind == "child" else "she"


@dataclass
class World:
    params: StoryParams
    child: Entity
    granny: Entity
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        chunks: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    chunks.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            chunks.append(" ".join(buf))
        return "\n\n".join(chunks)


CHARACTER_NAMES = [
    "Mina", "Owen", "Lila", "Noah", "Rosa", "Theo", "Ivy", "Eli"
]

GRANNY_NAMES = [
    "Granny", "Nana", "Grandma", "Granny Rose"
]

SETTINGS = [
    "granny's cozy house",
    "the little blue guest room",
    "the softly lit bedroom",
]

BEDTIME_OBJECTS = [
    "nightlight",
    "bedside lamp",
    "small lantern",
]

SPooky_CLUES = [
    "a long shadow",
    "a tiny bump in the hallway",
    "a creaky sound from the closet",
    "a shape on the wall",
]

COMFORT_ITEMS = [
    "a warm blanket",
    "a sleepy pillow",
    "a soft stuffed bunny",
    "a cup of warm milk",
]


# ---------------------------------------------------------------------------
# Core world logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    child = Entity(id=params.name, kind="child", label=params.name)
    granny = Entity(id=params.granny_name, kind="granny", label=params.granny_name)
    return World(params=params, child=child, granny=granny)


def foreshadow(world: World) -> None:
    p = world.params
    world.child.memes["unease"] = 1
    world.say(
        f"At {p.setting}, bedtime felt extra quiet. The {p.bedtime_object} gave a little blink, "
        f"and {p.spooky_clue} waited in the corner like it knew a secret."
    )
    world.say(
        f"{p.granny_name} smiled and said the house was only making sleepy sounds, but it was okay "
        f"to feel a little uneasy before a good night's rest."
    )
    world.facts["foreshadow_clue"] = p.spooky_clue


def suspense(world: World) -> None:
    p = world.params
    world.child.meters["curiosity"] = 1
    world.say(
        f"When the light suddenly went dim, {p.name} held still. The room seemed bigger for a moment, "
        f"and the shadow on the wall looked almost like it was breathing."
    )
    world.say(
        f"{p.granny_name} did not rush the feeling away. Instead, she held {p.name}'s hand and said, "
        f"\"Let's look carefully together.\""
    )
    world.facts["suspense_peak"] = True


def brave_check(world: World) -> None:
    p = world.params
    world.child.memes["bravery"] = world.child.memes.get("bravery", 0) + 1
    world.child.memes["tolerance"] = world.child.memes.get("tolerance", 0) + 1
    world.say(
        f"{p.name} took one brave breath and walked closer. That was hard, but {p.name} kept going, "
        f"because brave hearts can wait with a worried feeling without letting it win."
    )
    world.say(
        f"Behind the chair, the spooky shape turned out to be only a hanging coat. The creak was just the floorboards "
        f"settling in the night."
    )
    world.facts["truth_revealed"] = "coat_on_chair"


def resolve(world: World) -> None:
    p = world.params
    world.child.memes["fear"] = 0
    world.child.memes["peace"] = 1
    comfort = p.comfort_item
    world.say(
        f"{p.granny_name} tucked {p.name} under {comfort} and turned the {p.bedtime_object} back on."
    )
    world.say(
        f"{p.name} smiled, because the room was safe again. With {p.granny_name} nearby and the mystery solved, "
        f"{p.name} drifted into sleep as softly as a little boat on a calm lake."
    )
    world.facts["ending_safe"] = True


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    p = world.params
    world.say(
        f"{p.name} was spending the night at {p.granny_name}'s cozy house."
    )
    world.say(
        f"{p.name} loved bedtime stories, soft quilts, and the safe feeling of listening to {p.granny_name}'s gentle voice."
    )
    world.para()
    foreshadow(world)
    world.para()
    suspense(world)
    world.para()
    brave_check(world)
    resolve(world)
    world.facts.update(
        child=world.child,
        granny=world.granny,
        setting=p.setting,
        bedtime_object=p.bedtime_object,
        spooky_clue=p.spooky_clue,
        comfort_item=p.comfort_item,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        "Write a gentle bedtime story about a child staying with Granny, with a small scare that ends safely.",
        f"Tell a bedtime story where {p.name} shows bravery, tolerance, and calm thinking when a shadow appears.",
        f"Write a cozy story set in {p.setting} that uses foreshadowing and suspense before the happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question=f"Why did {p.name} feel worried before bedtime?",
            answer=(
                f"{p.name} felt worried because the room got quiet, the light dimmed, and "
                f"{p.spooky_clue} made the moment feel spooky."
            ),
        ),
        QAItem(
            question=f"How did {p.granny_name} help {p.name} stay calm?",
            answer=(
                f"{p.granny_name} stayed close, spoke gently, and asked {p.name} to look carefully instead "
                f"of guessing right away."
            ),
        ),
        QAItem(
            question=f"What showed that {p.name} was brave?",
            answer=(
                f"{p.name} was brave by taking a careful breath, walking closer, and checking the scary shape "
                f"instead of running away."
            ),
        ),
        QAItem(
            question=f"What did the scary shape turn out to be?",
            answer="It was only a hanging coat on a chair, not a real monster.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer=(
                "Bravery means doing something hard or a little scary while still trying your best and "
                "not giving up."
            ),
        ),
        QAItem(
            question="What does tolerance mean?",
            answer=(
                "Tolerance means being patient with a feeling, a person, or a situation that is a little uncomfortable, "
                "instead of getting upset right away."
            ),
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer=(
                "Foreshadowing is when a story drops a small clue early so readers can sense that something important "
                "may happen later."
            ),
        ),
        QAItem(
            question="What is suspense in a story?",
            answer=(
                "Suspense is the feeling of waiting to find out what will happen next, especially when something seems "
                "uncertain or mysterious."
            ),
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin and facts
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Child experiences worry when the scene gets spooky.
worry(child) :- foreshadowing(clue), suspense(scene).

% Granny supports tolerance by staying close and speaking gently.
support(granny, child) :- comfort(granny, child), tolerance(child).

% Bravery resolves suspense when the child checks the clue and learns the truth.
resolved(child) :- bravery(child), check(child), truth(coat_on_chair).

#show worry/1.
#show support/2.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("foreshadowing", "clue"),
        asp.fact("suspense", "scene"),
        asp.fact("comfort", "granny", "child"),
        asp.fact("tolerance", "child"),
        asp.fact("bravery", "child"),
        asp.fact("check", "child"),
        asp.fact("truth", "coat_on_chair"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show worry/1. #show support/2. #show resolved/1."))
    atoms = {
        "worry": set(asp.atoms(model, "worry")),
        "support": set(asp.atoms(model, "support")),
        "resolved": set(asp.atoms(model, "resolved")),
    }
    expected = {
        "worry": {("child",)},
        "support": {("granny", "child")},
        "resolved": {("child",)},
    }
    if atoms == expected:
        print("OK: ASP and Python logic agree.")
        return 0
    print("MISMATCH:")
    print("got:", atoms)
    print("expected:", expected)
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(CHARACTER_NAMES)
    granny_name = args.granny_name or rng.choice(GRANNY_NAMES)
    setting = args.setting or rng.choice(SETTINGS)
    bedtime_object = args.bedtime_object or rng.choice(BEDTIME_OBJECTS)
    spooky_clue = args.spooky_clue or rng.choice(SPooky_CLUES)
    comfort_item = args.comfort_item or rng.choice(COMFORT_ITEMS)
    return StoryParams(
        name=name,
        granny_name=granny_name,
        setting=setting,
        bedtime_object=bedtime_object,
        spooky_clue=spooky_clue,
        comfort_item=comfort_item,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print()
        print("--- world trace ---")
        print(json.dumps(
            {
                "params": sample.params.__dict__,
                "facts": {
                    "foreshadow_clue": sample.world.facts.get("foreshadow_clue"),
                    "suspense_peak": sample.world.facts.get("suspense_peak"),
                    "truth_revealed": sample.world.facts.get("truth_revealed"),
                    "ending_safe": sample.world.facts.get("ending_safe"),
                },
                "child": {
                    "meters": sample.world.child.meters,
                    "memes": sample.world.child.memes,
                },
                "granny": {
                    "meters": sample.world.granny.meters,
                    "memes": sample.world.granny.memes,
                },
            },
            indent=2,
            ensure_ascii=False,
        ))
    if qa:
        print()
        print("== (1) Generation prompts ==")
        for i, q in enumerate(sample.prompts, 1):
            print(f"{i}. {q}")
        print()
        print("== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== (3) World knowledge ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about Granny, tolerance, bravery, foreshadowing, and suspense.")
    ap.add_argument("--name")
    ap.add_argument("--granny-name")
    ap.add_argument("--setting")
    ap.add_argument("--bedtime-object")
    ap.add_argument("--spooky-clue")
    ap.add_argument("--comfort-item")
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


CURATED = [
    StoryParams(name="Mina", granny_name="Granny", setting="granny's cozy house", bedtime_object="nightlight", spooky_clue="a long shadow", comfort_item="a warm blanket"),
    StoryParams(name="Owen", granny_name="Nana", setting="the softly lit bedroom", bedtime_object="bedside lamp", spooky_clue="a creaky sound from the closet", comfort_item="a soft stuffed bunny"),
    StoryParams(name="Ivy", granny_name="Grandma", setting="the little blue guest room", bedtime_object="small lantern", spooky_clue="a tiny bump in the hallway", comfort_item="a cup of warm milk"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show worry/1. #show support/2. #show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show worry/1. #show support/2. #show resolved/1."))
        print("worry:", asp.atoms(model, "worry"))
        print("support:", asp.atoms(model, "support"))
        print("resolved:", asp.atoms(model, "resolved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
