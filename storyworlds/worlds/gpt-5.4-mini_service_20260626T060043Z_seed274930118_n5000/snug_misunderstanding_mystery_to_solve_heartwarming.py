#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/snug_misunderstanding_mystery_to_solve_heartwarming.py
============================================================================================================================

A small heartwarming story world about a snug missing thing, a misunderstanding,
and a gentle mystery to solve.

Premise:
- A child loves a cozy item that makes bedtime feel safe and snug.
- The item goes missing.
- The child and grown-up briefly misunderstand where it went.
- They solve the mystery by following kind, simple clues.
- The ending proves the item was found and the worry melted away.
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
# Core world model
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
    location: str = ""
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"present": 0.0}
        if not self.memes:
            self.memes = {
                "warmth": 0.0,
                "worry": 0.0,
                "curiosity": 0.0,
                "relief": 0.0,
                "love": 0.0,
                "misunderstanding": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the cottage"
    cozy_spots: list[str] = field(default_factory=lambda: ["the couch", "the basket", "the windowsill"])


@dataclass
class Mystery:
    item_id: str
    item_label: str
    item_phrase: str
    clue_spot: str
    snug_spot: str
    misread_spot: str
    reason: str
    keyword: str = "snug"


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    place: str
    mystery: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.lines: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "cottage": Setting(place="the cottage", cozy_spots=["the couch", "the basket", "the blanket fort"]),
    "bedroom": Setting(place="the bedroom", cozy_spots=["the bed", "the pillow pile", "the toy chest"]),
    "living_room": Setting(place="the living room", cozy_spots=["the sofa", "the armchair", "the rug by the lamp"]),
}

MYSTERIES = {
    "blanket": Mystery(
        item_id="blanket",
        item_label="blanket",
        item_phrase="a soft blue blanket",
        clue_spot="the basket by the couch",
        snug_spot="tucked inside the basket",
        misread_spot="on the couch",
        reason="the child had folded it up to make the room tidy",
    ),
    "stuffie": Mystery(
        item_id="stuffie",
        item_label="stuffie",
        item_phrase="a bunny stuffie with floppy ears",
        clue_spot="the pillow pile",
        snug_spot="nestled under the pillows",
        misread_spot="on the floor",
        reason="the grown-up moved it while straightening the bed",
    ),
    "scarf": Mystery(
        item_id="scarf",
        item_label="scarf",
        item_phrase="a striped scarf",
        clue_spot="the armchair",
        snug_spot="wrapped around the armchair",
        misread_spot="near the door",
        reason="the child had draped it there after coming in from the cold",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ruby", "Ava", "Ella", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Theo", "Ben", "Max", "Eli"]
TRAITS = ["gentle", "curious", "quiet", "cheerful", "thoughtful", "brave"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(place: str, mystery: str) -> bool:
    return place in SETTINGS and mystery in MYSTERIES


def explain_rejection(place: str, mystery: str) -> str:
    return f"(No story: {place!r} and {mystery!r} do not make a valid snug mystery.)"


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def intro(world: World, child: Entity, parent: Entity, mystery: Mystery) -> None:
    child.memes["love"] += 1
    child.memes["warmth"] += 1
    world.say(
        f"{child.id} was a {rng_trait(world)} {child.type} who loved {mystery.item_phrase} "
        f"because it made bedtime feel snug."
    )
    world.say(
        f"{parent.label} always kept the room calm and cozy, and {child.id} liked "
        f"that soft little world."
    )


def rng_trait(world: World) -> str:
    return world.facts.get("trait", "gentle")


def missing_scene(world: World, child: Entity, parent: Entity, mystery: Mystery) -> None:
    child.memes["worry"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"One evening, {mystery.item_label} was suddenly missing."
    )
    world.say(
        f"{child.id} looked in {mystery.misread_spot} and said, "
        f'"It was here before!"'
    )
    parent = world.get("parent")
    parent.memes["misunderstanding"] += 1
    parent.memes["worry"] += 1
    world.say(
        f"{parent.label} thought {child.id} might have left {child.pronoun('object')} "
        f"somewhere careless, so they both paused with a little misunderstanding between them."
    )


def search_scene(world: World, child: Entity, parent: Entity, mystery: Mystery) -> None:
    child.memes["curiosity"] += 1
    parent = world.get("parent")
    world.say(
        f"Then {child.id} and {parent.label} searched together, checking the quiet places first."
    )
    world.say(
        f"They looked near {mystery.clue_spot}, because that was the kind of place where "
        f"snug things liked to hide."
    )
    world.say(
        f"{child.id} noticed the little clue: {mystery.reason}."
    )
    mystery_item = world.get(mystery.item_id)
    mystery_item.hidden = False
    mystery_item.location = mystery.snug_spot
    mystery_item.meters["present"] = 1.0
    world.facts["found"] = True
    world.facts["resolved_by"] = mystery.snug_spot


def reveal_scene(world: World, child: Entity, parent: Entity, mystery: Mystery) -> None:
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    child.memes["love"] += 1
    parent = world.get("parent")
    parent.memes["misunderstanding"] = 0.0
    parent.memes["relief"] += 1
    parent.memes["love"] += 1
    world.say(
        f"At last, they found {mystery.item_phrase} {mystery.snug_spot}."
    )
    world.say(
        f"{child.id} hugged {parent.pronoun('object')} and grinned, and {parent.label} smiled back, "
        f"happy that the mystery was solved."
    )
    world.say(
        f"By bedtime, the room felt even warmer, and {mystery.item_label} was snug again where it belonged."
    )


# ---------------------------------------------------------------------------
# World builder
# ---------------------------------------------------------------------------

def tell(world_setting: Setting, mystery: Mystery, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(world_setting)
    world.facts["trait"] = trait

    child = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the " + ("mom" if parent_type == "mother" else "dad"),
    ))
    item = world.add(Entity(
        id=mystery.item_id,
        kind="thing",
        type=mystery.item_label,
        label=mystery.item_label,
        phrase=mystery.item_phrase,
        owner=child.id,
        caretaker=parent.id,
        location=mystery.misread_spot,
        hidden=True,
        plural=False,
        meters={"present": 0.0},
    ))

    world.facts.update(
        child=child,
        parent=parent,
        item=item,
        mystery=mystery,
        setting=world_setting,
    )

    world.say(f"{child.id} lived in {world_setting.place}, where everything felt soft and safe.")
    world.say(f"{child.id} loved {mystery.item_phrase}, especially on quiet nights.")

    world.say("")
    intro(world, child, parent, mystery)
    world.say("")
    missing_scene(world, child, parent, mystery)
    world.say("")
    search_scene(world, child, parent, mystery)
    world.say("")
    reveal_scene(world, child, parent, mystery)

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    mystery = f["mystery"]
    setting = f["setting"]
    return [
        f"Write a heartwarming story about {child.id} in {setting.place} when {mystery.item_label} goes missing.",
        f"Tell a gentle mystery-to-solve story where a snug {mystery.item_label} is found after a misunderstanding.",
        f"Make a child-friendly story about a cozy search that ends with everyone feeling relieved and snug.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    mystery: Mystery = f["mystery"]
    item: Entity = f["item"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"What was the mystery in {setting.place}?",
            answer=f"The mystery was where {mystery.item_phrase} had gone.",
        ),
        QAItem(
            question=f"Why did {child.id} and {parent.label} feel worried at first?",
            answer=f"They felt worried because {mystery.item_label} was missing, and they had a little misunderstanding about where it might be.",
        ),
        QAItem(
            question=f"Where did they find {item.label}?",
            answer=f"They found it {mystery.snug_spot}.",
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=f"It ended with {child.id} feeling relieved, hugging {parent.pronoun('object')}, and enjoying the snug feeling again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does snug mean?",
            answer="Snug means warm, cozy, and comfortable in a way that feels safe and nice.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that people try to figure out, usually by looking for clues.",
        ),
        QAItem(
            question="What helps solve a misunderstanding?",
            answer="Kind talking and careful listening help solve a misunderstanding.",
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
# Trace
# ---------------------------------------------------------------------------

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
        if e.hidden:
            bits.append("hidden=True")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts.get('found', False)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid_story(P, M) :- place(P), mystery(M), cozy_place(P), snug_mystery(M).
misunderstanding(M) :- mystery(M).
mystery_to_solve(M) :- mystery(M).
heartwarming(P, M) :- valid_story(P, M), misunderstanding(M), mystery_to_solve(M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
        lines.append(asp.fact("cozy_place", place))
    for mystery in MYSTERIES:
        lines.append(asp.fact("mystery", mystery))
        lines.append(asp.fact("snug_mystery", mystery))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(p, m) for p in SETTINGS for m in MYSTERIES if valid_combo(p, m)}
    clingo_set = set(asp_valid_pairs())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combo() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combo():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A heartwarming snug mystery story world."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    if not valid_combo(place, mystery):
        raise StoryError(explain_rejection(place, mystery))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or choose_name(gender, rng)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        name=name,
        gender=gender,
        parent=parent,
        place=place,
        mystery=mystery,
    ), trait


def generate(params: StoryParams) -> StorySample:
    mystery = MYSTERIES[params.mystery]
    world = tell(
        SETTINGS[params.place],
        mystery,
        params.name,
        params.gender,
        params.parent,
        getattr(params, "_trait", "gentle"),
    )
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


CURATED = [
    StoryParams(name="Mia", gender="girl", parent="mother", place="cottage", mystery="blanket"),
    StoryParams(name="Leo", gender="boy", parent="father", place="bedroom", mystery="stuffie"),
    StoryParams(name="Nora", gender="girl", parent="mother", place="living_room", mystery="scarf"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid snug mysteries:\n")
        for p, m in pairs:
            print(f"  {p:12} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            setattr(p, "_trait", "gentle")
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params, trait = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            setattr(params, "_trait", trait)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
