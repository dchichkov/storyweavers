#!/usr/bin/env python3
"""
A heartwarming storyworld about a small misunderstanding that is slowly
freshened by repeated gentle attempts until everyone ends happy.
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
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    parent_type: str
    item: str
    scent: str
    seed: Optional[int] = None


PLACES = {
    "kitchen": "the kitchen",
    "bedroom": "the bedroom",
    "laundry_room": "the laundry room",
    "porch": "the porch",
    "garden_shed": "the garden shed",
}

CHILD_NAMES = ["Mina", "Noah", "Lia", "Theo", "Sera", "Owen", "Maya", "Finn"]
CHILD_TYPES = {"girl", "boy"}
PARENT_TYPES = {"mother", "father", "grandparent"}

ITEMS = {
    "pillow": {
        "label": "pillow",
        "phrase": "a soft pillow with a faded blue cover",
        "state": "stale",
        "fresh_state": "fresh",
    },
    "blanket": {
        "label": "blanket",
        "phrase": "a warm blanket with little stitched stars",
        "state": "stuffy",
        "fresh_state": "fresh",
    },
    "curtains": {
        "label": "curtains",
        "phrase": "the curtains by the window",
        "state": "dusty",
        "fresh_state": "fresh",
    },
    "coat": {
        "label": "coat",
        "phrase": "a coat that had been kept in the closet too long",
        "state": "musty",
        "fresh_state": "fresh",
    },
}

SCENTS = {
    "lemon": "a bright lemon scent",
    "mint": "a cool mint smell",
    "lavender": "a soft lavender smell",
    "apple": "a sweet apple smell",
}

REPETITIONS = [
    "again and again",
    "one more time",
    "once more",
    "gently, and then gently again",
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% An item can be freshened when a place supports freshening and the scent is suitable.
can_freshen(P, I, S) :- place(P), item(I), scent(S), supports(P, freshen), scent_works(S, I).

% A misunderstanding happens when the child thinks the item is being taken away
% instead of being freshened.
misunderstanding(P, I) :- can_freshen(P, I, _), worry_about_taking(P, I).

% Repetition is part of the fix when the same careful action is done more than once.
repetition(P, I) :- can_freshen(P, I, _), repeat_twice(P, I).

% A happy ending occurs when the item becomes fresh and the misunderstanding is cleared.
happy_ending(P, I) :- fresh(P, I), not misunderstanding(P, I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("supports", pid, "freshen"))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("worry_about_taking", "kitchen", iid))
        lines.append(asp.fact("repeat_twice", "kitchen", iid))
        lines.append(asp.fact("scent_works", "lemon", iid))
        lines.append(asp.fact("scent_works", "mint", iid))
        lines.append(asp.fact("scent_works", "lavender", iid))
        lines.append(asp.fact("scent_works", "apple", iid))
    for sid in SCENTS:
        lines.append(asp.fact("scent", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show can_freshen/3. #show misunderstanding/2. #show repetition/2. #show happy_ending/2."))
    shown = set((s.name, len(s.arguments)) for s in model)
    expected = {("can_freshen", 3), ("misunderstanding", 2), ("repetition", 2), ("happy_ending", 2)}
    if expected.issubset(shown):
        print("OK: ASP rules load and produce the expected predicates.")
        return 0
    print("ASP verification failed.")
    return 1


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def choose_scent(rng: random.Random) -> str:
    return rng.choice(list(SCENTS))


def choose_item(rng: random.Random) -> str:
    return rng.choice(list(ITEMS))


def choose_place(rng: random.Random) -> str:
    return rng.choice(list(PLACES))


def make_world(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        meters={"hope": 1.0, "worry": 0.0, "joy": 0.0},
        memes={"hope": 1.0, "worry": 0.0, "joy": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_type,
        label=f"the {params.parent_type}",
        meters={"care": 1.0, "worry": 0.0, "joy": 0.0},
        memes={"care": 1.0, "worry": 0.0, "joy": 0.0},
    ))
    item_cfg = ITEMS[params.item]
    item = world.add(Entity(
        id="item",
        type=params.item,
        label=item_cfg["label"],
        phrase=item_cfg["phrase"],
        owner=child.id,
        caretaker=parent.id,
        meters={"stale": 1.0, "fresh": 0.0},
        memes={"stale": 1.0, "fresh": 0.0},
    ))
    world.facts.update(child=child, parent=parent, item=item, scent=params.scent, params=params)
    return world


def freshen_step(world: World, item: Entity, scent: str, repetition: bool) -> None:
    item.meters["stale"] = max(0.0, item.meters.get("stale", 0.0) - 0.6)
    item.meters["fresh"] = min(1.0, item.meters.get("fresh", 0.0) + (0.5 if repetition else 0.3))
    item.memes["fresh"] = item.meters["fresh"]


def tell_story(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    item: Entity = f["item"]
    scent = f["scent"]
    child_name = child.id
    parent_word = parent.label

    world.say(
        f"{child_name} loved the little room and loved the way {parent_word} made things feel cozy."
    )
    world.say(
        f"But one morning, {child_name} noticed {item.phrase} and thought it smelled too old."
    )
    world.say(
        f'"Let me help freshen it," {parent_word} said, and {child_name} smiled at the idea.'
    )

    world.para()
    world.say(
        f"At first, {child_name} misunderstood and worried that {parent_word} would take {item.label} away."
    )
    world.say(
        f"So {child_name} stood close, watching every movement, unsure what would happen next."
    )

    world.para()
    rep1 = REPETITIONS[0]
    rep2 = REPETITIONS[1]
    world.say(
        f"{parent_word} folded the item {rep1}, sprinkling {SCENTS[scent]} over it."
    )
    freshen_step(world, item, scent, repetition=False)
    world.say(
        f"Then {parent_word} smoothed it out and did it {rep2}, softly explaining that it was only being cared for."
    )
    freshen_step(world, item, scent, repetition=True)
    world.say(
        f"After the second careful pass, the misunderstanding began to fade."
    )

    world.para()
    item.meters["stale"] = 0.0
    item.meters["fresh"] = 1.0
    item.memes["fresh"] = 1.0
    child.meters["worry"] = 0.0
    child.memes["worry"] = 0.0
    child.meters["joy"] = 1.0
    child.memes["joy"] = 1.0
    parent.meters["joy"] = 1.0
    parent.memes["joy"] = 1.0

    world.say(
        f"In the end, {child_name} understood, laughed a little, and helped fluff the item until it felt new again."
    )
    world.say(
        f"The whole room seemed brighter, and {item.label} stayed safely with the family, now fresh and sweet-smelling."
    )
    world.facts["misunderstanding"] = True
    world.facts["resolved"] = True


def generate_story(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a heartwarming story about {p.child_name} at the {PLACES[p.place]} where a small misunderstanding gets fixed by repetition.",
        f"Tell a gentle story in which someone tries to freshen {ITEMS[p.item]['label']} with {SCENTS[p.scent]} and everything ends happily.",
        f"Create a child-friendly story about caring for {ITEMS[p.item]['label']} in the {PLACES[p.place]} without letting a misunderstanding linger.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    item: Entity = f["item"]
    scent = f["scent"]
    params: StoryParams = f["params"]

    return [
        QAItem(
            question=f"What did {child.id} first misunderstand about {parent.label} and {item.label}?",
            answer=f"{child.id} first worried that {parent.label} would take the {item.label} away, but that was not true.",
        ),
        QAItem(
            question=f"What did {parent.label} keep doing to freshen the {item.label}?",
            answer=f"{parent.label} kept doing the care steps again and again, using {SCENTS[scent]} and a gentle touch.",
        ),
        QAItem(
            question=f"How did the story end for {child.id} and the {item.label}?",
            answer=f"It ended happily, with {child.id} understanding the mistake and the {item.label} feeling fresh again.",
        ),
        QAItem(
            question=f"Where did the story take place?",
            answer=f"It took place in {PLACES[params.place]}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    out = []
    out.append(QAItem(
        question="What does it mean to freshen something?",
        answer="To freshen something means to make it feel cleaner, lighter, or nicer again, like giving it a pleasant new smell or a tidier look.",
    ))
    out.append(QAItem(
        question="Why can repetition help when someone is caring for something?",
        answer="Repetition can help because doing a gentle action more than once lets the care sink in and makes the result more even and complete.",
    ))
    out.append(QAItem(
        question="What is a misunderstanding?",
        answer="A misunderstanding happens when someone thinks the wrong thing at first, even though the real meaning is kinder or different.",
    ))
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld about freshening, misunderstanding, repetition, and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=sorted(CHILD_TYPES))
    ap.add_argument("--parent", choices=sorted(PARENT_TYPES))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--scent", choices=sorted(SCENTS))
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
    place = args.place or choose_place(rng)
    item = args.item or choose_item(rng)
    scent = args.scent or choose_scent(rng)
    gender = args.gender or rng.choice(sorted(CHILD_TYPES))
    parent = args.parent or rng.choice(sorted(PARENT_TYPES))
    name = args.name or rng.choice(CHILD_NAMES)
    return StoryParams(place=place, child_name=name, child_type=gender, parent_type=parent, item=item, scent=scent)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
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
        print(asp_program("#show can_freshen/3. #show misunderstanding/2. #show repetition/2. #show happy_ending/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show can_freshen/3. #show misunderstanding/2. #show repetition/2. #show happy_ending/2."))
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="kitchen", child_name="Mina", child_type="girl", parent_type="mother", item="pillow", scent="lavender"),
            StoryParams(place="bedroom", child_name="Noah", child_type="boy", parent_type="father", item="blanket", scent="mint"),
            StoryParams(place="laundry_room", child_name="Lia", child_type="girl", parent_type="grandparent", item="coat", scent="lemon"),
            StoryParams(place="porch", child_name="Theo", child_type="boy", parent_type="mother", item="curtains", scent="apple"),
        ]
        samples = [generate_story(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate_story(p)
            if sample.story not in seen:
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
