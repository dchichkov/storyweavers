#!/usr/bin/env python3
"""
A tiny fairy-tale story world about a twig that transforms.

Premise:
- A small creature finds a plain twig.
- The twig is cherished, then a wish for beauty or use causes a transformation.
- The transformation creates a tension: the new form is wonderful, but it may not fit the need, or it changes the owner’s feelings.
- A gentle helper or magical choice resolves the problem, yielding a finished fairy-tale ending image.

The world is built as a small state simulation with physical meters and emotional memes.
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
# Registries
# ---------------------------------------------------------------------------

NAMES = ["Mina", "Pip", "Tilda", "Nell", "Bram", "Luna", "Rowan", "Elsie"]
KINDS = ["child", "fox", "rabbit", "mouse", "bird", "sprite"]
GENDERS = ["girl", "boy"]
PLACES = ["the birch grove", "the mossy glade", "the old well", "the willow lane", "the garden gate"]

TRANSFORMATIONS = {
    "flower": {
        "result": "a silver flower",
        "spark": "a shimmer of moonlight",
        "effect": "beauty",
        "risk": "it might wilt before dawn",
        "turn": "The twig became a silver flower, delicate and bright.",
    },
    "wand": {
        "result": "a little wand",
        "spark": "a twinkle of starlight",
        "effect": "magic",
        "risk": "it might be too small to hold",
        "turn": "The twig became a little wand, smooth and ready for spells.",
    },
    "bridge": {
        "result": "a tiny bridge",
        "spark": "a warm hum of oak-leaf magic",
        "effect": "help",
        "risk": "it might be too high for a small friend",
        "turn": "The twig became a tiny bridge, sturdy over a trickling brook.",
    },
    "crown": {
        "result": "a bright crown",
        "spark": "a golden ring of sunrise",
        "effect": "joy",
        "risk": "it might slide off in the wind",
        "turn": "The twig became a bright crown, light as a feather.",
    },
}

HELPERS = {
    "fairy": "a kind fairy",
    "owl": "an old owl",
    "deer": "a gentle deer",
    "grandmother": "a wise grandmother",
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    transformed: bool = False
    form: str = "twig"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    hero: Entity
    helper: Entity
    twig: Entity
    transformation: str
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

    def copy(self) -> "World":
        import copy
        return World(
            place=self.place,
            hero=copy.deepcopy(self.hero),
            helper=copy.deepcopy(self.helper),
            twig=copy.deepcopy(self.twig),
            transformation=self.transformation,
            paragraphs=[[]],
            facts=copy.deepcopy(self.facts),
        )


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    kind: str
    transformation: str
    helper_kind: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def create_world(params: StoryParams) -> World:
    hero = Entity(
        id=params.name,
        kind="character",
        label=params.kind,
        phrase=f"a little {params.kind}",
        meters={"wandering": 0.0},
        memes={"wonder": 0.0, "hope": 0.0, "worry": 0.0, "delight": 0.0},
    )
    helper = Entity(
        id=params.helper_kind,
        kind="character",
        label=params.helper_kind,
        phrase=f"a {params.helper_kind}",
        meters={"magic": 0.0},
        memes={"kindness": 1.0},
    )
    twig = Entity(
        id="twig",
        kind="thing",
        label="twig",
        phrase="a plain twig",
        owner=hero.id,
        form="twig",
        meters={"plain": 1.0, "magic": 0.0, "useful": 0.0},
        memes={"special": 0.0, "hope": 0.0},
    )
    return World(
        place=params.place,
        hero=hero,
        helper=helper,
        twig=twig,
        transformation=params.transformation,
    )


def predict_transformation(world: World) -> bool:
    sim = world.copy()
    apply_moment(sim, narrate=False)
    return sim.twig.transformed


def apply_moment(world: World, narrate: bool = True) -> None:
    hero = world.hero
    helper = world.helper
    twig = world.twig
    info = TRANSFORMATIONS[world.transformation]

    if not twig.transformed:
        hero.meters["wandering"] += 1
        hero.memes["wonder"] += 1
        twig.memes["special"] += 1
        if narrate:
            world.say(f"In {world.place}, {hero.id} found {twig.phrase} lying among the leaves.")
            world.say(
                f"{hero.id} held the twig carefully, as if it already knew a secret."
            )

    if twig.memes["special"] >= 1.0 and not twig.transformed:
        twig.meters["magic"] += 1
        helper.meters["magic"] += 1
        hero.memes["hope"] += 1
        twig.transformed = True
        twig.form = info["result"]
        twig.label = info["result"]
        twig.phrase = info["result"]
        twig.meters["plain"] = 0.0
        twig.meters["useful"] = 1.0

        if narrate:
            world.say(
                f"Then {info['spark']} drifted down from the air, and {helper.id} smiled."
            )
            world.say(info["turn"])

    if twig.transformed:
        if world.transformation == "flower":
            hero.memes["delight"] += 1
            hero.meters["wandering"] += 0.5
        elif world.transformation == "wand":
            hero.memes["hope"] += 1
            hero.meters["wandering"] += 0.5
        elif world.transformation == "bridge":
            hero.memes["worry"] += 1
            twig.meters["useful"] += 1
        elif world.transformation == "crown":
            hero.memes["delight"] += 1

        if narrate:
            if world.transformation == "bridge":
                world.say(
                    f"It helped a tiny path cross the brook, and {hero.id} watched in wonder."
                )
            elif world.transformation == "wand":
                world.say(
                    f"{hero.id} waved it once, and the air felt full of tiny wishes."
                )
            elif world.transformation == "crown":
                world.say(
                    f"{hero.id} wore it like a treasure, and the grove seemed to bow."
                )
            else:
                world.say(
                    f"{hero.id} tucked it near {hero.pronoun('possessive')} heart, "
                    f"and the whole glade looked brighter."
                )


def resolve_story(world: World) -> None:
    hero = world.hero
    twig = world.twig
    trans = world.transformation
    info = TRANSFORMATIONS[trans]

    if trans == "bridge":
        world.para()
        world.say(
            f"But the bridge was a little too high for the smallest friend nearby, so "
            f"{hero.id} and {world.helper.id} laid down moss at its ends."
        )
        twig.meters["useful"] += 1
        hero.memes["delight"] += 1
        world.say(
            f"After that, the bridge fit just right, and the path could be crossed with a grin."
        )
    elif trans == "wand":
        world.para()
        world.say(
            f"It was so tiny that {hero.id} almost worried it would be lost, until "
            f"{world.helper.id} tied a soft ribbon around the handle."
        )
        twig.meters["magic"] += 0.5
        world.say(
            f"Then it stayed safe, and the little wand could carry wishes wherever {hero.id} went."
        )
    elif trans == "flower":
        world.para()
        world.say(
            f"The flower looked fragile, but {world.helper.id} whispered a bedtime charm over it."
        )
        world.say(
            f"By morning it still shone, and {hero.id} smiled at the bright petal-light."
        )
    elif trans == "crown":
        world.para()
        world.say(
            f"The crown slipped once in the breeze, so {hero.id} pressed it down with a ribbon of grass."
        )
        world.say(
            f"After that it stayed on straight, and the grove looked like a fairy-tale hall."
        )

    world.facts.update(
        transformation=trans,
        helper_kind=world.helper.id,
        hero_kind=hero.label,
        place=world.place,
        twig_form=twig.form,
        resolved=True,
    )


def tell(params: StoryParams) -> World:
    world = create_world(params)
    world.say(
        f"Once in {world.place}, {world.hero.id} was a little {world.hero.label} who loved quiet paths and small surprises."
    )
    world.say(
        f"One day {world.hero.id} found {world.twig.phrase}, and {world.hero.pronoun('subject')} felt it was not an ordinary stick at all."
    )
    world.para()
    world.say(
        f"{world.hero.id} wished for {TRANSFORMATIONS[params.transformation]['effect']} enough to change it."
    )
    world.say(
        f"{world.helper.id.capitalize()} came close, and a soft spell began to glow around the twig."
    )
    apply_moment(world, narrate=True)
    world.para()
    resolve_story(world)
    return world


# ---------------------------------------------------------------------------
# Registries and validation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for trans in TRANSFORMATIONS:
            for kind in KINDS:
                out.append((place, trans, kind))
    return out


def explain_rejection(transformation: str) -> str:
    return f"(No story: unknown transformation '{transformation}'.)"


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a short fairy tale about a twig that becomes {TRANSFORMATIONS[world.transformation]["result"]}.',
        f"Tell a gentle story in which {world.hero.id} finds a twig in {world.place} and a helper changes it by magic.",
        f'Write a child-friendly fairy tale using the word "twig" and a transformation that feels magical.',
    ]


def story_qa(world: World) -> list[QAItem]:
    trans = world.transformation
    info = TRANSFORMATIONS[trans]
    return [
        QAItem(
            question=f"What did {world.hero.id} find in {world.place}?",
            answer=f"{world.hero.id} found a plain twig in {world.place}.",
        ),
        QAItem(
            question=f"What did the twig become?",
            answer=f"It became {info['result']}.",
        ),
        QAItem(
            question=f"Who helped the transformation?",
            answer=f"{world.helper.id.capitalize()} helped with a gentle bit of magic.",
        ),
        QAItem(
            question=f"Why was there a problem after the change?",
            answer=(
                f"The new form was lovely, but {info['risk']}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a twig?",
            answer="A twig is a small, thin branch that has fallen from a tree.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a different form.",
        ),
        QAItem(
            question="Why do fairy tales often include magic?",
            answer="Fairy tales often use magic to make ordinary things become wonderful or surprising.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A twig may transform when it is cherished and magic is nearby.
can_transform(T) :- twig(T), cherished(T), magic_nearby(T).

% The result depends on the chosen transformation kind.
result(T, flower) :- can_transform(T), wants(T, flower).
result(T, wand) :- can_transform(T), wants(T, wand).
result(T, bridge) :- can_transform(T), wants(T, bridge).
result(T, crown) :- can_transform(T), wants(T, crown).

% The story is reasonable when a helper can make the change and the twig exists.
reasonable_story(P, X, H) :- place(P), twig(X), helper(H), can_transform(X).
#show reasonable_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for trans in TRANSFORMATIONS:
        lines.append(asp.fact("wants", "twig", trans))
    lines.append(asp.fact("twig", "twig"))
    lines.append(asp.fact("cherished", "twig"))
    lines.append(asp.fact("magic_nearby", "twig"))
    for helper in HELPERS:
        lines.append(asp.fact("helper", helper))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reasonable_story/3."))
    asp_set = set(asp.atoms(model, "reasonable_story"))
    py_set = {(p, "twig", h) for p in PLACES for h in HELPERS}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python registry ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python registry:")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world about a twig that transforms.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--kind", choices=KINDS)
    ap.add_argument("--transformation", choices=sorted(TRANSFORMATIONS))
    ap.add_argument("--helper-kind", choices=sorted(HELPERS))
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
    trans = args.transformation or rng.choice(sorted(TRANSFORMATIONS))
    if trans not in TRANSFORMATIONS:
        raise StoryError(explain_rejection(trans))
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        name=args.name or rng.choice(NAMES),
        gender=args.gender or rng.choice(GENDERS),
        kind=args.kind or rng.choice(KINDS),
        transformation=trans,
        helper_kind=args.helper_kind or rng.choice(list(HELPERS)),
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in [world.hero, world.helper, world.twig]:
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show reasonable_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    curated = [
        StoryParams(place="the birch grove", name="Mina", gender="girl", kind="child", transformation="flower", helper_kind="fairy"),
        StoryParams(place="the mossy glade", name="Pip", gender="boy", kind="mouse", transformation="wand", helper_kind="owl"),
        StoryParams(place="the willow lane", name="Luna", gender="girl", kind="fox", transformation="bridge", helper_kind="deer"),
        StoryParams(place="the garden gate", name="Bram", gender="boy", kind="rabbit", transformation="crown", helper_kind="grandmother"),
    ]

    if args.all:
        samples = [generate(p) for p in curated]
    elif args.asp:
        import asp
        model = asp.one_model(asp_program("#show reasonable_story/3."))
        combos = sorted(set(asp.atoms(model, "reasonable_story")))
        print(f"{len(combos)} reasonable stories:\n")
        for c in combos:
            print(" ", c)
        return
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i - 1
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
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
