#!/usr/bin/env python3
"""
A standalone story world for a tiny rhyming tale about a figurine and an
aerial toy, with a bad ending.

Premise:
- A small child treasures a figurine.
- They want to join an aerial show with a kite or balloon-like toy.
- The toy escapes or the figurine falls, and the ending is sad.

The story is state-driven:
- physical meters track height, breakage, wind, and hold
- emotional memes track joy, worry, and loss
- the prose is assembled from the simulated sequence

The world is intentionally narrow so that every generated story has a clear
beginning, tension, turn, and ending image.
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
# Domain constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the hill"
    airy: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    type: str
    risky: str
    sees: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    toy: str
    place: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "hill": Setting(place="the hill", airy=True, affords={"kite", "balloon"}),
    "roof": Setting(place="the roof", airy=True, affords={"kite", "balloon"}),
    "field": Setting(place="the field", airy=True, affords={"kite"}),
}

TOYS = {
    "kite": Toy(
        id="kite",
        label="kite",
        phrase="a bright kite with a long string",
        type="kite",
        risky="too high",
        sees="soaring",
        keyword="aerial",
        tags={"aerial", "wind", "sky"},
    ),
    "balloon": Toy(
        id="balloon",
        label="balloon",
        phrase="a round balloon with a ribbon",
        type="balloon",
        risky="too far",
        sees="floating",
        keyword="aerial",
        tags={"aerial", "wind", "sky"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora"]
BOY_NAMES = ["Leo", "Finn", "Max", "Sam", "Theo"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def toy_risky_in_place(toy: Toy, setting: Setting) -> bool:
    return toy.id in setting.affords


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for toy_id in setting.affords:
            combos.append((place, toy_id))
    return combos


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def _make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    toy = TOYS[params.toy]
    world = World(setting)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"reach": 0.0, "grip": 1.0, "balance": 1.0},
        memes={"joy": 1.0, "want": 1.0, "worry": 0.0, "loss": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        meters={"watch": 1.0},
        memes={"care": 1.0, "worry": 0.0},
    ))
    figurine = world.add(Entity(
        id="figurine",
        type="figurine",
        label="figurine",
        phrase="a little painted figurine",
        owner=child.id,
        caretaker=parent.id,
        meters={"clean": 1.0, "high": 0.0, "safe": 1.0, "break": 0.0},
        memes={"love": 1.0},
    ))
    toy_ent = world.add(Entity(
        id=toy.id,
        type=toy.type,
        label=toy.label,
        phrase=toy.phrase,
        owner=child.id,
        caretaker=child.id,
        meters={"high": 0.0, "wind": 0.0, "gone": 0.0},
        memes={"fun": 1.0},
    ))
    world.facts.update(child=child, parent=parent, figurine=figurine, toy=toy_ent, toy_cfg=toy)
    return world


def _intro(world: World) -> None:
    f = world.facts["child"]
    figurine = world.facts["figurine"]
    world.say(
        f"{f.id} had a tiny figurine, neat and sweet, "
        f"with painted shoes and a shiny seat."
    )
    world.say(
        f"{f.id} loved that figurine so very much, "
        f"like a treasure held with a gentle touch."
    )
    world.say(
        f"It sat on a shelf and looked so bright, "
        f"a little brave spark in the morning light."
    )


def _desire(world: World, toy: Toy) -> None:
    c = world.facts["child"]
    c.memes["joy"] += 0.5
    c.memes["want"] += 1.0
    world.say(
        f"But {c.id} saw {toy.phrase} in the air, "
        f"and wanted to send it up there."
    )
    world.say(
        f"'{toy.keyword.capitalize()} fun!' {c.id} said with a grin, "
        f"as the breeze said, 'Come on in.'"
    )


def _warning(world: World, toy: Toy) -> None:
    c = world.facts["child"]
    p = world.facts["parent"]
    fig = world.facts["figurine"]
    c.memes["worry"] += 0.5
    p.memes["worry"] += 1.0
    world.say(
        f"The {p.type} looked up and frowned a bit, "
        f"for air can tug and twist and spit."
    )
    world.say(
        f'"If the {toy.label} slips, it may fly away, '
        f'and your figurine could fall today," {p.pronoun("subject")} said.'
    )
    fig.meters["safe"] -= 0.2
    fig.meters["high"] += 0.2


def _attempt(world: World, toy: Toy) -> None:
    c = world.facts["child"]
    fig = world.facts["figurine"]
    c.meters["reach"] += 0.4
    toy_ent = world.facts["toy"]
    toy_ent.meters["high"] += 1.0
    toy_ent.meters["wind"] += 1.0
    fig.meters["high"] += 0.4
    world.say(
        f"{c.id} held the string and ran with cheer, "
        f"to send the {toy.label} sailing near."
    )
    world.say(
        f"It went up, up, with a twirl and sway, "
        f"and the sky looked wide and far away."
    )


def _bad_turn(world: World, toy: Toy) -> None:
    c = world.facts["child"]
    p = world.facts["parent"]
    fig = world.facts["figurine"]
    toy_ent = world.facts["toy"]
    c.memes["joy"] -= 0.5
    c.memes["worry"] += 1.0
    toy_ent.meters["gone"] = 1.0
    fig.meters["break"] = 1.0
    fig.meters["safe"] = 0.0
    world.say(
        f"Then the wind gave a sneaky twist, "
        f"and the string slipped out of {c.id}'s fist."
    )
    world.say(
        f"The {toy.label} flew off with a final spin, "
        f"and the figurine toppled in."
    )
    world.say(
        f"It hit the ground with a tiny crack, "
        f"and there was no easy way back."
    )
    p.memes["worry"] += 1.0


def _ending(world: World) -> None:
    c = world.facts["child"]
    fig = world.facts["figurine"]
    toy_ent = world.facts["toy"]
    world.say(
        f"{c.id} stood still in the quiet air, "
        f"with teary eyes and a solemn stare."
    )
    world.say(
        f"The aerial toy was gone from sight, "
        f"and the figurine was broken that night."
    )
    world.say(
        f"So {c.id} held the shards so small, "
        f"and the windy game felt sad for all."
    )
    fig.memes["love"] += 0.0
    toy_ent.meters["gone"] = 1.0


def tell(setting: Setting, toy: Toy, hero_name: str, hero_gender: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        meters={"reach": 0.0, "grip": 1.0, "balance": 1.0},
        memes={"joy": 1.0, "want": 1.0, "worry": 0.0, "loss": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label=f"the {parent_type}",
        meters={"watch": 1.0},
        memes={"care": 1.0, "worry": 0.0},
    ))
    figurine = world.add(Entity(
        id="figurine",
        type="figurine",
        label="figurine",
        phrase="a little painted figurine",
        owner=child.id,
        caretaker=parent.id,
        meters={"clean": 1.0, "high": 0.0, "safe": 1.0, "break": 0.0},
        memes={"love": 1.0},
    ))
    toy_ent = world.add(Entity(
        id=toy.id,
        type=toy.type,
        label=toy.label,
        phrase=toy.phrase,
        owner=child.id,
        caretaker=child.id,
        meters={"high": 0.0, "wind": 0.0, "gone": 0.0},
        memes={"fun": 1.0},
    ))
    world.facts.update(child=child, parent=parent, figurine=figurine, toy=toy_ent, toy_cfg=toy)

    _intro(world)
    world.para()
    _desire(world, toy)
    _warning(world, toy)
    _attempt(world, toy)
    _bad_turn(world, toy)
    world.para()
    _ending(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["child"]
    toy = f["toy_cfg"]
    return [
        f'Write a short rhyming story for a young child about {c.id}, a figurine, and an {toy.keyword} toy.',
        f"Tell a simple rhyming tale where {c.id} tries to enjoy an aerial {toy.label} but the ending goes badly.",
        f'Write a child-friendly story that includes the words "figurine" and "{toy.keyword}" and ends sadly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c = f["child"]
    p = f["parent"]
    toy = f["toy_cfg"]
    fig = f["figurine"]
    return [
        QAItem(
            question=f"What did {c.id} love at the start of the story?",
            answer=f"{c.id} loved a little painted figurine that sat safe and bright at first.",
        ),
        QAItem(
            question=f"What aerial thing did {c.id} want to send up into the air?",
            answer=f"{c.id} wanted to send the {toy.label} up into the air.",
        ),
        QAItem(
            question=f"Why did the {p.type} worry?",
            answer=f"The {p.type} worried because the wind could make the {toy.label} slip away and the figurine could fall and break.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The {toy.label} flew away, the figurine broke, and the ending was sad.",
        ),
    ]


KNOWLEDGE = {
    "figurine": [
        (
            "What is a figurine?",
            "A figurine is a small figure made to be looked at or kept as a treasure.",
        )
    ],
    "aerial": [
        (
            "What does aerial mean?",
            "Aerial means high in the air or made for the sky, like a kite or a floating balloon.",
        )
    ],
    "wind": [
        (
            "What can wind do?",
            "Wind is moving air, and it can push light things like kites and balloons.",
        )
    ],
    "kite": [
        (
            "What does a kite need?",
            "A kite needs wind and a string so someone can guide it in the sky.",
        )
    ],
    "balloon": [
        (
            "Why do balloons float?",
            "A balloon can float because the air inside it helps it rise and drift upward.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["toy_cfg"].tags) | {"figurine"}
    out: list[QAItem] = []
    for tag in ["figurine", "aerial", "wind", "kite", "balloon"]:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/2.
risk(T) :- toy(T), aerial(T).
valid(P,T) :- setting(P), toy(T), affords(P,T), risk(T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, t in TOYS.items():
        lines.append(asp.fact("toy", tid))
        if "aerial" in t.tags:
            lines.append(asp.fact("aerial", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world about a figurine and an aerial toy.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = valid_combos()
    if args.place or args.toy:
        combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.toy is None or c[1] == args.toy)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, toy = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(toy=toy, place=place, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TOYS[params.toy], params.name, params.gender, params.parent)
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
    StoryParams(toy="kite", place="hill", name="Mia", gender="girl", parent="mother"),
    StoryParams(toy="balloon", place="roof", name="Leo", gender="boy", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:\n")
        for place, toy in combos:
            print(f"  {place:6} {toy}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
