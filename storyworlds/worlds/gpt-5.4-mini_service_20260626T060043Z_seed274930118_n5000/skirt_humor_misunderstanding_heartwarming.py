#!/usr/bin/env python3
"""
Story world: skirt_humor_misunderstanding_heartwarming

A tiny, self-contained story simulation about a child, a skirt, a funny
misunderstanding, and a warm ending.

Premise:
- A child loves a special skirt.
- Someone misunderstands what the skirt is for.
- The misunderstanding creates a small, funny problem.
- A kind explanation and a simple gesture turn it into a warm ending.

The simulated state tracks physical and emotional changes:
- meters: things like wrinkled, dusty, tidy, raised
- memes: feelings like joy, worry, embarrassment, relief, pride

The prose is generated from the world state, not from a frozen template.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["dusty", "wrinkled", "tidy", "raised", "mended"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "embarrassment", "relief", "pride", "confusion", "affection"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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
    fired: set[str] = field(default_factory=set)

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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
    skirt_style: str
    misunderstanding: str
    seed: Optional[int] = None


@dataclass
class Outfit:
    label: str
    phrase: str
    type: str = "skirt"


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class Misunderstanding:
    id: str
    mistaken_for: str
    funny_line: str
    fix_line: str


SETTINGS = {
    "schoolyard": Setting(place="the schoolyard", detail="The pavement was bright and busy, and the wind kept teasing little corners of cloth."),
    "garden": Setting(place="the garden", detail="The garden smelled like warm soil and mint, and a clothesline fluttered nearby."),
    "kitchen": Setting(place="the kitchen", detail="The kitchen was snug and sunny, with a chair by the window and a basket of folded laundry."),
}

OUTFITS = {
    "blue_skirt": Outfit(label="blue skirt", phrase="a twirly blue skirt with little stars"),
    "red_skirt": Outfit(label="red skirt", phrase="a red skirt with a soft ribbon"),
    "yellow_skirt": Outfit(label="yellow_skirt", phrase="a yellow skirt with tiny pockets"),
}

MISUNDERSTANDINGS = {
    "banner": Misunderstanding(
        id="banner",
        mistaken_for="a tiny banner",
        funny_line="Someone laughed and said it looked like a flag for a very small parade.",
        fix_line="Then they saw it was just a skirt for twirling, not a banner at all.",
    ),
    "picnic_blanket": Misunderstanding(
        id="picnic_blanket",
        mistaken_for="a picnic blanket",
        funny_line="A neighbor pointed and wondered why the child was carrying breakfast on their legs.",
        fix_line="Soon everyone could see it was a skirt, light and neat, not a blanket for lunch.",
    ),
    "cape": Misunderstanding(
        id="cape",
        mistaken_for="a superhero cape",
        funny_line="The child spun so fast that a friend whispered, 'Is that a flying hero costume?'",
        fix_line="They all giggled when the friend learned it was a skirt made for dancing, not flying.",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella", "Iris", "Maya"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Ben", "Eli", "Max", "Noah", "Sam"]
PARENT_NAMES = ["Mom", "Dad", "Aunt Jo", "Uncle Ray"]
STYLES = ["playful", "careful", "bright", "shy", "curious"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when a place, skirt, and misunderstanding are all present.
valid_story(P, S, M) :- place(P), skirt(S), misunderstanding(M).

% The humorous misunderstanding is acceptable only if the mistaken object is
% not the actual outfit and the fix line is available.
humorous(M) :- misunderstanding(M), mistaken_for(M, X), X != skirt.

% Heartwarming resolution requires a kind explanation and a relieved child.
warm_end(P, S, M) :- valid_story(P, S, M), humorous(M).
#show valid_story/3.
#show warm_end/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for sid in OUTFITS:
        lines.append(asp.fact("skirt", sid))
    for mid, m in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding", mid))
        lines.append(asp.fact("mistaken_for", mid, m.mistaken_for))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3.\n#show warm_end/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((p, s, m) for p in SETTINGS for s in OUTFITS for m in MISUNDERSTANDINGS)
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, s, m) for p in SETTINGS for s in OUTFITS for m in MISUNDERSTANDINGS]


def explain_rejection(place: str, skirt: str, misunderstanding: str) -> str:
    return f"(No story: the selected skirt and misunderstanding do not make a sensible, gentle joke at {place}.)"


# ---------------------------------------------------------------------------
# Story generation helpers
# ---------------------------------------------------------------------------
def _do_confusion(world: World, child: Entity, parent: Entity, m: Misunderstanding) -> None:
    child.memes["confusion"] += 1
    child.memes["embarrassment"] += 1
    parent.memes["worry"] += 1
    world.say(f"At first, {child.id} stood still and blinked when someone thought {m.mistaken_for}.")
    world.say(m.funny_line)


def _do_fix(world: World, child: Entity, parent: Entity, skirt: Entity, m: Misunderstanding) -> None:
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    child.memes["pride"] += 1
    child.memes["affection"] += 1
    parent.memes["relief"] += 1
    world.say(
        f"{parent.id} crouched beside {child.id} and smiled kindly. "
        f'"No, {skirt.label} is just {child.id}\'s {skirt.phrase.split("a ", 1)[-1] if skirt.phrase.startswith("a ") else skirt.phrase}," {parent.id} said.'
    )
    world.say(m.fix_line)
    world.say(
        f"Then {child.id} gave a small twirl, and the skirt swung neatly instead of making trouble."
    )
    skirt.meters["tidy"] += 1
    skirt.meters["mended"] += 1


def tell(place: Setting, outfit: Outfit, misunderstanding: Misunderstanding, child_name: str,
         child_gender: str, parent_name: str, parent_gender: str) -> World:
    world = World(place.place)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender))
    skirt = world.add(Entity(
        id="skirt",
        kind="thing",
        type="skirt",
        label=outfit.label,
        phrase=outfit.phrase,
        owner=child.id,
        caretaker=parent.id,
        worn_by=child.id,
    ))

    child.memes["joy"] += 1
    child.memes["pride"] += 1
    world.say(
        f"{child.id} loved a special {skirt.label}, because it spun like a little circle of happiness."
    )
    world.say(place.detail)

    world.para()
    world.say(f"One day at {place.place}, {child.id} wore {skirt.phrase} and went outside with {parent.id}.")
    world.say(f"That was when the funny misunderstanding began: someone thought it was {misunderstanding.mistaken_for}.")
    _do_confusion(world, child, parent, misunderstanding)

    world.para()
    _do_fix(world, child, parent, skirt, misunderstanding)

    world.facts.update(
        place=place,
        outfit=outfit,
        misunderstanding=misunderstanding,
        child=child,
        parent=parent,
        skirt=skirt,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    outfit = f["outfit"]
    place = f["place"]
    misunderstanding = f["misunderstanding"]
    return [
        f'Write a heartwarming story for a young child about {child.id}, a {outfit.label}, and a silly misunderstanding at {place.place}.',
        f'Tell a gentle, funny story set at {place.place} where a child wears {outfit.phrase} and someone mistakes it for {misunderstanding.mistaken_for}.',
        f'Write a short story with a skirt, a mix-up, and a kind fix that ends with everyone smiling.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    skirt = f["skirt"]
    misunderstanding = f["misunderstanding"]
    place = f["place"]
    return [
        QAItem(
            question=f"What was {child.id} wearing at {place.place}?",
            answer=f"{child.id} was wearing {skirt.phrase}, and it was the special skirt they loved.",
        ),
        QAItem(
            question=f"What funny mistake did someone make about the skirt?",
            answer=f"Someone thought it was {misunderstanding.mistaken_for}, which made the moment silly and a little confusing.",
        ),
        QAItem(
            question=f"How did {parent.id} help fix the mix-up?",
            answer=f"{parent.id} spoke kindly, explained that it was only {skirt.label}, and helped everyone understand the joke.",
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=f"{child.id} ended happy and proud, because the mix-up was cleared up and the skirt still looked lovely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a skirt?",
            answer="A skirt is a piece of clothing that hangs from the waist and can be light, swirly, and fun to wear.",
        ),
        QAItem(
            question="Why can a misunderstanding be funny?",
            answer="A misunderstanding can be funny when someone guesses wrong in a harmless way, and then the truth makes everyone smile.",
        ),
        QAItem(
            question="What does it mean to be heartwarming?",
            answer="Heartwarming means it makes people feel warm, kind, and happy inside.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small heartwarming skirt story world with humor and misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--skirt", choices=OUTFITS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--name")
    ap.add_argument("--parent-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-gender", choices=["mother", "father", "aunt", "uncle"])
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
    place = args.place or rng.choice(list(SETTINGS))
    skirt = args.skirt or rng.choice(list(OUTFITS))
    misunderstanding = args.misunderstanding or rng.choice(list(MISUNDERSTANDINGS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent_name = args.parent_name or rng.choice(PARENT_NAMES)
    if place not in SETTINGS or skirt not in OUTFITS or misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("(No valid combination matches the given options.)")
    return StoryParams(
        place=place,
        child_name=child_name,
        child_gender=child_gender,
        parent_name=parent_name,
        parent_gender=parent_gender,
        skirt_style=skirt,
        misunderstanding=misunderstanding,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        OUTFITS[params.skirt_style],
        MISUNDERSTANDINGS[params.misunderstanding],
        params.child_name,
        params.child_gender,
        params.parent_name,
        params.parent_gender,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3.\n#show warm_end/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:\n")
        for p, s, m in combos:
            print(f"  {p:12} {s:12} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("schoolyard", "Mia", "girl", "Mom", "mother", "blue_skirt", "banner"),
            StoryParams("garden", "Leo", "boy", "Dad", "father", "red_skirt", "cape"),
            StoryParams("kitchen", "Nora", "girl", "Aunt Jo", "aunt", "yellow_skirt", "picnic_blanket"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.skirt_style} at {p.place} ({p.misunderstanding})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
