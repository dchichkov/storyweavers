#!/usr/bin/env python3
"""
storyworlds/worlds/list_swimming_pool_rhyme_repetition_bedtime_story.py
=======================================================================

A small bedtime-style story world set at a swimming pool, with rhyme and
repetition built into the narration.

Premise:
- A child wants to go to the swimming pool.
- A parent checks a small list of pool things first.
- The child is impatient, then learns that the list helps them get ready.

The world is intentionally tiny and state-driven:
- physical meters: packed, wet, calm, skipped
- emotional memes: joy, worry, patience, excitement, snug

The story ends with a concrete image proving what changed: the list is checked,
the child is ready, and the pool outing feels calm and cozy.
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
# Domain registries
# ---------------------------------------------------------------------------

GIRL_NAMES = ["Mina", "Luna", "Nora", "Ivy", "Lila", "Maya"]
BOY_NAMES = ["Owen", "Finn", "Theo", "Milo", "Eli", "Noah"]
PARENT_NAMES = ["Mom", "Dad"]

POOL_ITEMS = {
    "towel": "a soft towel",
    "cap": "a bright swim cap",
    "goggles": "tiny goggles",
    "water": "a water bottle",
    "list": "a little list",
}

POOL_GEAR = {
    "towel": {"needed": True, "protects": "warmth"},
    "cap": {"needed": True, "protects": "hair"},
    "goggles": {"needed": True, "protects": "eyes"},
    "water": {"needed": True, "protects": "thirst"},
}

ASP_RULES = r"""
% A pool story is reasonable when the list includes the needed pool gear.
need(Item) :- gear(Item), needed(Item).
ready :- need(towel), need(cap), need(goggles), need(water), checked(list).

% A child gets worry if they want to go before the list is checked.
worry(child) :- wants_swim(child), not checked(list).

% A calm ending happens when the parent and child check the list together.
calm_end :- ready.
#show ready/0.
#show worry/1.
#show calm_end/0.
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def p(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    place: str = "swimming pool"
    name: str = "Mina"
    gender: str = "girl"
    parent: str = "Mom"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world at a swimming pool, with rhyme and repetition."
    )
    ap.add_argument("--place", default="swimming pool", choices=["swimming pool"])
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_NAMES)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    return StoryParams(place="swimming pool", name=name, gender=gender, parent=parent)


def pronoun(gender: str, case: str = "subject") -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def world_knowledge_qa(_: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a list?",
            answer="A list is a set of words written down to help someone remember what to do or bring."
        ),
        QAItem(
            question="Why do people use a towel at a swimming pool?",
            answer="People use a towel to dry off after swimming so they can feel warm and cozy again."
        ),
        QAItem(
            question="What are goggles for?",
            answer="Goggles help protect your eyes so water does not sting them while you swim."
        ),
    ]


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("gear", "towel"),
        asp.fact("gear", "cap"),
        asp.fact("gear", "goggles"),
        asp.fact("gear", "water"),
        asp.fact("needed", "towel"),
        asp.fact("needed", "cap"),
        asp.fact("needed", "goggles"),
        asp.fact("needed", "water"),
        asp.fact("wants_swim", "child"),
        asp.fact("checked", "list"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show ready/0. #show worry/1. #show calm_end/0."))
    shown = set((a.name, len(a.arguments)) for a in model)
    expected = {("ready", 0), ("calm_end", 0)}
    if shown == expected:
        print("OK: ASP gate matches the intended calm-ending story.")
        return 0
    print("MISMATCH: ASP output was", sorted(shown))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def make_world(params: StoryParams) -> World:
    w = World(place=params.place)
    child = w.add(Entity(
        id="child",
        kind="character",
        type=params.gender,
        label=params.name,
    ))
    parent = w.add(Entity(
        id="parent",
        kind="character",
        type="mother" if params.parent == "Mom" else "father",
        label=params.parent,
    ))
    list_obj = w.add(Entity(
        id="list",
        kind="thing",
        type="list",
        label="list",
        phrase="a little list",
    ))
    for item_id, phrase in POOL_ITEMS.items():
        if item_id != "list":
            w.add(Entity(
                id=item_id,
                kind="thing",
                type="gear",
                label=item_id,
                phrase=phrase,
                owner="child",
            ))

    child.meters.update({"excited": 1.0, "calm": 0.0, "skipped": 0.0})
    child.memes.update({"joy": 0.0, "worry": 0.0, "patience": 0.0, "snug": 0.0})
    parent.memes.update({"care": 1.0, "worry": 0.0, "patience": 1.0})

    w.facts.update(
        child=child,
        parent=parent,
        list=list_obj,
        items=[w.get(i) for i in ["towel", "cap", "goggles", "water"]],
        gender=params.gender,
        name=params.name,
        parent_name=params.parent,
        place=params.place,
    )
    return w


def generate_story(world: World) -> None:
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    list_obj: Entity = world.facts["list"]

    world.say(
        f"At the swimming pool, {child.label} liked the splashy, swishy sound. "
        f"Swish, swish, splash-splash, the water sang in a hush-hush hush."
    )
    world.say(
        f"{child.label} had a little list. "
        f"A list for the pool, a list for the cool, a list to help with each rule."
    )
    world.say(
        f"{parent.label} smiled and said, \"Let's check the list, nice and slow. "
        f"List first, swim next, that's the way to go.\""
    )

    world.para()
    child.memes["worry"] += 1.0
    child.meters["skipped"] += 1.0
    world.say(
        f"But {child.label} bounced on little toes and tried to dash away. "
        f"\"Pool now, pool now, I want to play!\""
    )
    world.say(
        f"{parent.label} held up the list and said it again, gentle and bright: "
        f"\"List first, swim next, we'll do it right.\""
    )

    world.para()
    world.say(
        f"So they checked the list together. "
        f"Towel, yes. Cap, yes. Goggles, yes. Water, yes. "
        f"One by one, one by one, they checked them all."
    )
    for item_id in ["towel", "cap", "goggles", "water"]:
        world.get(item_id).meters["packed"] = 1.0
    list_obj.meters["checked"] = 1.0
    child.memes["patience"] += 1.0
    child.memes["joy"] += 1.0
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)

    world.say(
        f"Then {child.label} laughed, because the list made the getting-ready part feel "
        f"like a little song. \"Pack it, stack it, quick-quick-quick,\" {child.label} said. "
        f"\"Check it, tuck it, click!\""
    )
    world.say(
        f"{parent.label} tucked the towel in the bag, and the bag felt snug and full."
    )

    world.para()
    child.meters["calm"] += 1.0
    child.memes["snug"] += 1.0
    world.say(
        f"At last, {child.label} stood by the pool, ready and steady. "
        f"The list was done, the list was clear, and the day felt soft and near."
    )
    world.say(
        f"Swish, swish, splash-splash, they went to the water at last, "
        f"and {child.label} smiled because the careful way made the fun come fast."
    )

    world.facts["ready"] = True
    world.facts["child_happy"] = True
    world.facts["list_checked"] = True


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    return [
        QAItem(
            question=f"What did {child.label} want to do at the swimming pool?",
            answer=f"{child.label} wanted to swim and play at the swimming pool."
        ),
        QAItem(
            question=f"What did {parent.label} ask {child.label} to do first?",
            answer=f"{parent.label} asked {child.label} to check the little list first."
        ),
        QAItem(
            question="What was on the list?",
            answer="The list had a towel, a swim cap, goggles, and a water bottle."
        ),
        QAItem(
            question=f"How did {child.label} feel after the list was checked?",
            answer=f"{child.label} felt calmer, happier, and ready to go to the pool."
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="By the end, the list was checked, the pool bag was packed, and the child was ready for a cozy swim."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    return [
        f"Write a bedtime story about {child.label} and {parent.label} at a swimming pool, with rhyme and repetition.",
        f"Tell a gentle pool story where a child checks a list before swimming.",
        "Write a cozy story that repeats a few soft phrases like a lullaby and ends with everyone ready for the pool.",
    ]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    generate_story(world)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
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


def resolve_from_curated(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


CURATED = [
    StoryParams(place="swimming pool", name="Mina", gender="girl", parent="Mom"),
    StoryParams(place="swimming pool", name="Owen", gender="boy", parent="Dad"),
    StoryParams(place="swimming pool", name="Lila", gender="girl", parent="Mom"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show ready/0. #show worry/1. #show calm_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show ready/0. #show worry/1. #show calm_end/0."))
        atoms = sorted((a.name, len(a.arguments)) for a in model)
        print("ASP model atoms:", atoms)
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
            params = resolve_from_curated(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} at the swimming pool"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
