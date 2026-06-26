#!/usr/bin/env python3
"""
storyworlds/worlds/leaf_lesson_learned_bad_ending_tall_tale.py
===============================================================

A small standalone story world in a tall-tale style about a leaf, a mistake,
and a hard-earned lesson learned. The ending is intentionally bittersweet:
the hero tries one grand idea, learns better, but still loses the prize to the
wind.

Seed inspiration:
- leaf
- Lesson Learned
- Bad Ending
- Tall Tale

World premise:
A child finds a remarkable leaf and tries to keep it safe and special. The
wind, however, has a longer memory and a stronger grip on the sky. The child
learns that some beautiful things are meant to be admired, not trapped.
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

LEAF_KINDS = {
    "maple": {
        "shape": "a maple leaf with five brave points",
        "color": "red-gold",
        "lesson": "some pretty things are best left free",
        "qa": "Maple leaves are broad and hand-shaped, with points along the edge.",
    },
    "oak": {
        "shape": "an oak leaf with wavy edges",
        "color": "amber",
        "lesson": "holding tight can be the fastest way to lose something",
        "qa": "Oak leaves often have rounded lobes that look like soft waves.",
    },
    "birch": {
        "shape": "a small birch leaf that shimmered like a coin",
        "color": "yellow-green",
        "lesson": "little things can still matter a great deal",
        "qa": "Birch leaves are usually small and simple, with a fine pointed shape.",
    },
}

WIND_STRENGTHS = {
    "breeze": {
        "verb": "whispered",
        "push": 1,
        "image": "a polite little breeze",
    },
    "gust": {
        "verb": "huffed",
        "push": 2,
        "image": "a grinning gust",
    },
    "blast": {
        "verb": "roared",
        "push": 3,
        "image": "a wild blast of wind",
    },
}

PLACES = {
    "yard": "the yard",
    "hill": "the hill",
    "lane": "the lane",
    "orchard": "the orchard",
    "field": "the field",
}

TRAITS = ["brave", "curious", "stubborn", "dreamy", "lively", "cheerful"]
NAMES = ["Milo", "Nina", "Toby", "Lena", "June", "Pip", "Rosa", "Eli"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"drift": 0.0, "damage": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "worry": 0.0, "resolve": 0.0, "lesson": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the field"
    wind_kind: str = "gust"
    leaf_kind: str = "maple"
    seed: str = "leaf"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.warnings = 0

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.warnings = self.warnings
        return clone


def leaf_name(leaf_kind: str) -> str:
    return LEAF_KINDS[leaf_kind]["shape"]


def wind_name(wind_kind: str) -> str:
    return WIND_STRENGTHS[wind_kind]["image"]


def make_world(params: "StoryParams") -> World:
    setting = Setting(
        place=PLACES[params.place],
        wind_kind=params.wind,
        leaf_kind=params.leaf,
    )
    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
    ))
    leaf = world.add(Entity(
        id="leaf",
        kind="thing",
        type="leaf",
        label="leaf",
        phrase=LEAF_KINDS[params.leaf]["shape"],
        owner=hero.id,
    ))
    wind = world.add(Entity(
        id="wind",
        kind="thing",
        type="wind",
        label=WIND_STRENGTHS[params.wind]["image"],
    ))
    world.facts.update(
        hero=hero,
        leaf=leaf,
        wind=wind,
        setting=setting,
        place=params.place,
        leaf_kind=params.leaf,
        wind_kind=params.wind,
        trait=params.trait,
    )
    return world


def _drift_rule(world: World) -> list[str]:
    out: list[str] = []
    wind = world.get("wind")
    leaf = world.get("leaf")
    if wind.meters.get("push", 0.0) <= 0:
        wind.meters["push"] = float(WIND_STRENGTHS[world.setting.wind_kind]["push"])
    if leaf.carried_by is None and leaf.meters["drift"] >= 1.0:
        sig = ("drift",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        leaf.memes["worry"] += 1.0
        out.append("The leaf twirled once, as if it had heard a secret from the sky.")
    return out


def _loss_rule(world: World) -> list[str]:
    out: list[str] = []
    leaf = world.get("leaf")
    wind = world.get("wind")
    if leaf.carried_by and wind.meters.get("push", 0.0) >= 2.0 and leaf.meters["damage"] < 1.0:
        sig = ("loss",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        leaf.meters["damage"] = 1.0
        leaf.carried_by = None
        out.append("The wind snatched the leaf straight out of the child's hands.")
    return out


def _lesson_rule(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"].id)
    leaf = world.get("leaf")
    if leaf.meters["damage"] >= 1.0 and hero.memes["lesson"] < 1.0:
        sig = ("lesson",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hero.memes["lesson"] = 1.0
        out.append("The child learned that a thing can be treasured without being trapped.")
    return out


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in (_drift_rule, _loss_rule, _lesson_rule):
            sents = rule(world)
            if sents:
                changed = True
                for s in sents:
                    world.say(s)


def scene_open(world: World) -> None:
    hero = world.facts["hero"]
    leaf = world.get("leaf")
    place = world.setting.place
    world.say(
        f"On {place}, there lived a {hero.type} named {hero.id} who was as {world.facts['trait']} "
        f"as a songbird on a fencepost."
    )
    world.say(
        f"One day, {hero.id} found {leaf.phrase}, shining like a coin dropped by the sun."
    )
    world.say(
        f"The child loved the leaf at once and promised to keep it safe."
    )


def scene_tension(world: World) -> None:
    hero = world.facts["hero"]
    leaf = world.get("leaf")
    wind = world.facts["wind"]
    wind_word = wind_name(world.setting.wind_kind)
    world.para()
    world.say(
        f"But then {wind_word} came striding over the grass, and the air began to "
        f"{WIND_STRENGTHS[world.setting.wind_kind]['verb']} around the child's ears."
    )
    world.say(
        f"{hero.id} tucked the leaf into {hero.pronoun('possessive')} hands and said, "
        f"\"Not a single breeze will steal you from me.\""
    )
    leaf.carried_by = hero.id
    leaf.meters["drift"] += 1.0
    hero.memes["hope"] += 1.0
    hero.memes["worry"] += 1.0
    propagate(world)


def scene_mistake(world: World) -> None:
    hero = world.facts["hero"]
    leaf = world.get("leaf")
    wind = world.facts["wind"]
    world.say(
        f"{hero.id} climbed a little stump to show the leaf the whole wide world, "
        f"thinking a higher view would make it safer."
    )
    if world.setting.wind_kind == "breeze":
        world.say("That was a small idea for a very large sky.")
    elif world.setting.wind_kind == "gust":
        world.say("That was a bold idea, but the wind was bolder.")
    else:
        world.say("That was a mighty idea, and the wind was a giant with quicker feet.")
    leaf.meters["drift"] += float(wind.meters.get("push", WIND_STRENGTHS[world.setting.wind_kind]["push"]))
    hero.memes["worry"] += 1.0
    propagate(world)


def scene_bad_ending(world: World) -> None:
    hero = world.facts["hero"]
    leaf = world.get("leaf")
    world.para()
    if leaf.meters["damage"] >= 1.0:
        world.say(
            f"The leaf spun away over the fence, then over the barn roof, and then over the moon-bright clouds."
        )
        world.say(
            f"{hero.id} chased it hard, but the wind had a longer stride and a louder laugh."
        )
        world.say(
            f"When the child came back, {hero.pronoun('possessive')} hands were empty."
        )
    else:
        world.say(
            f"The leaf trembled in {hero.id}'s hands until the child finally opened {hero.pronoun('possessive')} palms."
        )
        world.say(
            f"It rose anyway, as light as a wish, and vanished into the sky."
        )
        world.say(
            f"{hero.id} stood still, learning that not every loss can be wrestled back."
        )


def scene_lesson(world: World) -> None:
    hero = world.facts["hero"]
    leaf = world.get("leaf")
    world.para()
    world.say(
        f"At last, {hero.id} sat on the stump and watched a cousin leaf tumble past on the wind."
    )
    world.say(
        f"{hero.id} whispered, \"Next time I will admire beauty without trying to lock it in my pocket.\""
    )
    world.say(
        f"So the child learned the lesson the tall grass had been trying to teach all along."
    )
    hero.memes["resolve"] += 1.0
    hero.memes["lesson"] = 1.0
    leaf.carried_by = None


def tell_story(params: "StoryParams") -> World:
    world = make_world(params)
    scene_open(world)
    scene_tension(world)
    scene_mistake(world)
    scene_bad_ending(world)
    scene_lesson(world)
    return world


@dataclass
class StoryParams:
    place: str
    leaf: str
    wind: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in PLACES:
        for leaf in LEAF_KINDS:
            for wind in WIND_STRENGTHS:
                combos.append((place, leaf, wind))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tall-tale story world about a leaf, a loss, and a lesson learned.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--leaf", dest="leaf_kind", choices=sorted(LEAF_KINDS))
    ap.add_argument("--wind", choices=sorted(WIND_STRENGTHS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    leaf = args.leaf_kind or rng.choice(list(LEAF_KINDS))
    wind = args.wind or rng.choice(list(WIND_STRENGTHS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, leaf=leaf, wind=wind, name=name, gender=gender, trait=trait)


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    place = world.facts["place"]
    leaf = world.facts["leaf_kind"]
    wind = world.facts["wind_kind"]
    return [
        f'Write a tall-tale story for a child about a {leaf} leaf and a {wind} wind at {PLACES[place]}.',
        f'Tell a story where {hero.id} learns a lesson after trying to save a leaf from the wind.',
        f'Write a short, child-friendly story with a bad ending that still teaches a good lesson.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    leaf = world.facts["leaf"]
    place = world.facts["place"]
    trait = world.facts["trait"]
    leaf_kind = world.facts["leaf_kind"]
    wind_kind = world.facts["wind_kind"]
    return [
        QAItem(
            question=f"Who found the leaf at {PLACES[place]}?",
            answer=f"{hero.id}, the {trait} {hero.type}, found the leaf there.",
        ),
        QAItem(
            question="What kind of leaf was it?",
            answer=f"It was {LEAF_KINDS[leaf_kind]['shape']}.",
        ),
        QAItem(
            question="Why did the child lose the leaf?",
            answer=f"The {WIND_STRENGTHS[wind_kind]['image']} was too strong, so the leaf blew away before {hero.id} could keep it safe.",
        ),
        QAItem(
            question="What lesson did the child learn?",
            answer=LEAF_KINDS[leaf_kind]["lesson"].capitalize() + ".",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    leaf_kind = world.facts["leaf_kind"]
    wind_kind = world.facts["wind_kind"]
    return [
        QAItem(
            question="What is a leaf?",
            answer="A leaf is a flat part of a plant that grows from a stem or branch and helps the plant make food.",
        ),
        QAItem(
            question="What does wind do to leaves?",
            answer="Wind can lift leaves, spin them, and carry them through the air.",
        ),
        QAItem(
            question=f"What makes a {leaf_kind} leaf special?",
            answer=LEAF_KINDS[leaf_kind]["qa"],
        ),
        QAItem(
            question=f"What is a {wind_kind} like?",
            answer=f"{WIND_STRENGTHS[wind_kind]['image'].capitalize()} can push light things around and make trees sway.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:8} ({e.kind:7}) meters={dict(e.meters)} memes={dict(e.memes)} "
            f"owner={e.owner or '-'} carried_by={e.carried_by or '-'}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="field", leaf="maple", wind="gust", name="Milo", gender="boy", trait="curious"),
    StoryParams(place="orchard", leaf="oak", wind="blast", name="Nina", gender="girl", trait="stubborn"),
    StoryParams(place="hill", leaf="birch", wind="breeze", name="Toby", gender="boy", trait="dreamy"),
]


ASP_RULES = r"""
leaf_kind(L) :- leaf(L).
wind_kind(W) :- wind(W).
stronger(breeze,gust).
stronger(gust,blast).

bad_ending(L,W) :- leaf_kind(L), wind_kind(W), wind_strength(W,S), S >= 1.
lesson_learned(L) :- leaf_kind(L).

#show bad_ending/2.
#show lesson_learned/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for leaf in LEAF_KINDS:
        lines.append(asp.fact("leaf", leaf))
    for wind, info in WIND_STRENGTHS.items():
        lines.append(asp.fact("wind", wind))
        lines.append(asp.fact("wind_strength", wind, info["push"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show bad_ending/2.\n#show lesson_learned/1."))
    bad = set(asp.atoms(model, "bad_ending"))
    lesson = set(asp.atoms(model, "lesson_learned"))
    python_bad = {(leaf, wind) for leaf in LEAF_KINDS for wind in WIND_STRENGTHS}
    python_lesson = {(leaf,) for leaf in LEAF_KINDS}
    if bad == python_bad and lesson == python_lesson:
        print("OK: ASP parity verified.")
        return 0
    print("Mismatch in ASP parity.")
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show bad_ending/2."))
    return sorted(set(asp.atoms(model, "bad_ending")))


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show bad_ending/2.\n#show lesson_learned/1."))
        return
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show bad_ending/2.\n#show lesson_learned/1."))
        print("bad ending combos:", sorted(set(asp.atoms(model, "bad_ending"))))
        print("lesson learned:", sorted(set(asp.atoms(model, "lesson_learned"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, p in enumerate(CURATED):
            p.seed = base_seed + i
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            p = resolve_params(args, rng)
            p.seed = seed
            sample = generate(p)
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
