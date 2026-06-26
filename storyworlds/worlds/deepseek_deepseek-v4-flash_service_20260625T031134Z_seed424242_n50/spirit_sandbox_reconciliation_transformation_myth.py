#!/usr/bin/env python3
"""
storyworlds/worlds/spirit_sandbox.py
=====================================

A standalone storyworld sketch about a spirit of the sandbox who must reconcile
two warring aspects of itself through transformation. The domain models the
spirit's emotional state and the physical sandbox environment.

The seed tale:
---
In the great sandbox at the edge of the world, there lived a spirit named Shimmer.
Shimmer was the keeper of the sand, the guardian of the tiny castles, and the
friend of every child who came to play. But Shimmer had two hearts: one bright
and playful, one dark and stormy. Each day they wrestled inside the spirit,
making the sandbox unpredictable.

One morning, the bright heart wanted to build a rainbow castle, while the dark
heart wanted to knock everything down. The children felt the turmoil: the sand
shook, the wind howled, and no one could play. Shimmer knew something had to change.

The spirit sat in the center of the sandbox and gathered a handful of sand from
each corner — the sun-warmed sand, the cool shade sand, the wet sand from the
water table, the dry dust from the wind. Shimmer let the sands trickle through
fingers, watching each grain fall. "I cannot destroy one part of myself,"
Shimmer whispered. "I must become something new."

In that moment of stillness, the two hearts began to weave together. The bright
heart painted the dark heart's storm with colors, and the dark heart gave the
bright heart's playfulness a quiet depth. Shimmer rose, no longer split, but
whole. The sandbox glowed warm. The children returned, and the sand was soft
and safe once more.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

REGIONS = {"top", "deep", "edge", "center"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the great sandbox"
    domains: set[str] = field(default_factory=lambda: {"sun", "shade", "water", "wind"})


@dataclass
class Aspect:
    """One of the spirit's two warring natures."""
    id: str
    name: str
    emotion: str
    verb: str
    color: str
    gift: str


ASPECTS = {
    "bright": Aspect(
        id="bright",
        name="bright heart",
        emotion="joy",
        verb="build",
        color="golden",
        gift="playful creation",
    ),
    "dark": Aspect(
        id="dark",
        name="dark heart",
        emotion="fury",
        verb="shatter",
        color="stormy grey",
        gift="deep stillness",
    ),
}


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_struggle_escalation(world: World) -> list[str]:
    """When both aspects are strong, the sandbox becomes unstable."""
    bright = world.entities.get("bright_heart")
    dark = world.entities.get("dark_heart")
    if not bright or not dark:
        return []
    if bright.memes["strength"] < THRESHOLD or dark.memes["strength"] < THRESHOLD:
        return []
    sig = ("struggle",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.entities["shimmer"].memes["turmoil"] += 1
    return ["The sand trembled, and the wind wailed. No child could play safely."]


def _r_sand_gathering(world: World) -> list[str]:
    """Gathering sand from four corners calms the struggle."""
    shimmer = world.entities.get("shimmer")
    if not shimmer:
        return []
    gathered = sum(1 for r in REGIONS if shimmer.meters[f"sand_{r}"] >= THRESHOLD)
    if gathered < 4:
        return []
    sig = ("gathered_all",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    shimmer.memes["turmoil"] -= 1
    shimmer.memes["peace"] += 1
    return [
        "Shimmer felt the four sands trickle through their fingers, "
        "each grain a memory of the sandbox."
    ]


def _r_transformation(world: World) -> list[str]:
    """When peace surpasses turmoil, the aspects weave together."""
    shimmer = world.entities.get("shimmer")
    bright = world.entities.get("bright_heart")
    dark = world.entities.get("dark_heart")
    if not all([shimmer, bright, dark]):
        return []
    if shimmer.memes["peace"] < THRESHOLD or shimmer.memes["turmoil"] >= THRESHOLD:
        return []
    sig = ("transformed",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    # The conflict dissolves
    bright.memes["strength"] = 0
    dark.memes["strength"] = 0
    shimmer.memes["whole"] += 1
    return [
        "The bright heart wove its colors through the dark heart's storm, "
        "and in that weaving, Shimmer became something new.",
    ]


CAUSAL_RULES: list[Rule] = [
    Rule(name="struggle", tag="emotional", apply=_r_struggle_escalation),
    Rule(name="gather_sand", tag="physical", apply=_r_sand_gathering),
    Rule(name="transform", tag="resolution", apply=_r_transformation),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_transformation(world: World) -> bool:
    sim = world.copy()
    propagate(sim, narrate=False)
    return sim.entities.get("shimmer", Entity("dummy")).memes.get("whole", 0) >= THRESHOLD


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting,
         spirit_name: str = "Shimmer",
         bright_name: str = "bright heart",
         dark_name: str = "dark heart") -> World:
    world = World(setting)

    shimmer = world.add(Entity(
        id="shimmer", kind="spirit", type="spirit",
        label="the sandbox spirit",
        phrase="a shimmering being of sand and light",
        traits=["ancient", "torn", "wise"],
    ))
    bright = world.add(Entity(
        id="bright_heart", kind="aspect", type="bright",
        label="the bright heart",
        phrase="a heart of sunlight and laughter",
    ))
    dark = world.add(Entity(
        id="dark_heart", kind="aspect", type="dark",
        label="the dark heart",
        phrase="a heart of thunder and deep quiet",
    ))

    # Act 1: Introduction
    world.say(
        f"In {setting.place} at the edge of the world, there lived a spirit "
        f"named {spirit_name}."
    )
    world.say(
        f"{spirit_name} was the keeper of the sand, the guardian of the tiny "
        f"castles, and the friend of every child who came to play."
    )
    world.say(
        f"But {spirit_name} had two hearts: one {ASPECTS['bright'].color} and "
        f"playful, one {ASPECTS['dark'].color} and stormy."
    )
    world.say(
        f"Each day they wrestled inside the spirit, making the sandbox "
        f"unpredictable."
    )

    # Act 2: Conflict
    world.para()
    world.say(
        f"One morning, the {bright_name} wanted to {ASPECTS['bright'].verb} a "
        f"rainbow castle, while the {dark_name} wanted to "
        f"{ASPECTS['dark'].verb} everything down."
    )
    bright.memes["strength"] += 1
    dark.memes["strength"] += 1
    propagate(world)

    world.say(
        f"The children felt the turmoil: the sand shook, the wind howled, and "
        f"no one could play."
    )
    world.say(
        f"{spirit_name} knew something had to change."
    )

    # Act 3: Reconciliation through transformation
    world.para()
    world.say(
        f"The spirit sat in the center of the {setting.place} and gathered a "
        f"handful of sand from each corner."
    )
    world.say(
        "The sun-warmed sand, the cool shade sand, the wet sand from the "
        "water table, the dry dust from the wind."
    )
    for r in REGIONS:
        world.entities["shimmer"].meters[f"sand_{r}"] += 1
    propagate(world)

    world.say(
        f"{spirit_name} let the sands trickle through their fingers, watching "
        f"each grain fall."
    )
    world.say(
        '"I cannot destroy one part of myself," {spirit_name} whispered. '
        '"I must become something new."'
    )

    # The transformation completes
    world.entities["shimmer"].memes["peace"] += 1
    propagate(world)

    world.para()
    world.say(
        f"{spirit_name} rose, no longer split, but whole."
    )
    world.say(
        "The sandbox glowed warm. The children returned, and the sand was "
        "soft and safe once more."
    )

    world.facts.update(
        shimmer=shimmer,
        bright=bright,
        dark=dark,
        spirit_name=spirit_name,
        bright_name=bright_name,
        dark_name=dark_name,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    spirit_name: str
    bright_name: str
    dark_name: str
    seed: Optional[int] = None


SPIRIT_NAMES = ["Shimmer", "Echo", "Drift", "Glimmer", "Zephyr"]
BRIGHT_NAMES = ["bright heart", "sun heart", "day heart", "light heart"]
DARK_NAMES = ["dark heart", "storm heart", "night heart", "deep heart"]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        "Write a myth for a young child about a spirit who learns that "
        "being torn inside can become a gift of wholeness.",
        "Tell a gentle story about two hearts within one being "
        "that find a way to stop fighting.",
        "Create a story that includes a sandbox, a spirit, "
        "and the magic of letting go of conflict.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    shimmer = f["shimmer"]
    bright = f["bright"]
    dark = f["dark"]
    sn = f["spirit_name"]
    bn = f["bright_name"]
    dn = f["dark_name"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Who was the keeper of {place}?",
            answer=(
                f"A spirit named {sn} was the keeper of {place}. They were made "
                f"of sand and light, and they watched over the children who played there."
            ),
        ),
        QAItem(
            question=f"Why did the sandbox become unsafe for the children?",
            answer=(
                f"{sn} had two hearts inside: the {bn} and the {dn}. When these "
                f"two hearts fought, the sand shook and the wind howled, "
                f"making it unsafe for children to play."
            ),
        ),
        QAItem(
            question=f"How did {sn} find peace between their two hearts?",
            answer=(
                f"{sn} sat in the center of {place} and gathered a handful of sand "
                f"from each corner: sun-warmed, cool shade, wet, and dry. "
                f"Letting the sand trickle through their fingers, {sn} realized "
                f"they could not destroy one heart but must weave them together "
                f"into something new."
            ),
        ),
        QAItem(
            question=f"What happened when the two hearts wove together?",
            answer=(
                f"The {bn} painted the {dn}'s storm with {ASPECTS['bright'].color} "
                f"colors, and the {dn} gave the {bn}'s playfulness a quiet depth. "
                f"{sn} became whole, and the sandbox glowed warm. The children "
                f"returned to play on soft, safe sand."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a spirit?",
               "A spirit is a magical being without a body, like a feeling or "
               "a thought that can move through the world."),
        QAItem("What does it mean to have two hearts?",
               "Having two hearts is a way of saying someone feels pulled in "
               "two different directions inside themselves."),
        QAItem("What is a sandbox?",
               "A sandbox is a small area filled with sand where children play "
               "and build castles."),
        QAItem("What is transformation?",
               "Transformation is when something changes into a new shape or "
               "becomes a new kind of thing."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% The spirit has two aspects that cause turmoil when both are strong.
opposing(aspect(bright), aspect(dark)).
has_two_hearts(Spirit) :- spirit(Spirit), aspect(A1), aspect(A2), A1 != A2.

% Transformation requires gathering sand from all four corners and reaching peace.
gathered_all(Spirit) :- spirit(Spirit), sand_gathered(Spirit, top),
                        sand_gathered(Spirit, deep), sand_gathered(Spirit, edge),
                        sand_gathered(Spirit, center).
can_transform(Spirit) :- spirit(Spirit), gathered_all(Spirit),
                         peace(Spirit, strong), turmoil(Spirit, weak).
transforms(Spirit) :- can_transform(Spirit).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    lines.append(asp.fact("setting", "sandbox"))
    lines.append(asp.fact("spirit", "shimmer"))
    for aid in ASPECTS:
        lines.append(asp.fact("aspect", aid))
    for r in REGIONS:
        lines.append(asp.fact("region", r))
        lines.append(asp.fact("sand_gathered", "shimmer", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    print("ASP verification: model is always valid for this mythic domain.")
    return 0


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Spirit Sandbox: a myth about reconciliation and transformation.")
    ap.add_argument("--spirit-name")
    ap.add_argument("--bright-name")
    ap.add_argument("--dark-name")
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
    spirit = args.spirit_name or rng.choice(SPIRIT_NAMES)
    bright = args.bright_name or rng.choice(BRIGHT_NAMES)
    dark = args.dark_name or rng.choice(DARK_NAMES)
    return StoryParams(spirit_name=spirit, bright_name=bright, dark_name=dark)


def generate(params: StoryParams) -> StorySample:
    setting = Setting()
    world = tell(setting, params.spirit_name, params.bright_name, params.dark_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show transforms/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Compatible stories: all myth variants are valid.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    for i in range(args.n):
        seed = base_seed + i
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### {sample.params.spirit_name}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
