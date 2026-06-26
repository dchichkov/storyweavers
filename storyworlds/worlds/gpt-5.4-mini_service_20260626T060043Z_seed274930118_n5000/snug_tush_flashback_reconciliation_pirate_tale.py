#!/usr/bin/env python3
"""
Storyworld: a pirate tale with a snug little shipboard problem, a flashback,
and a reconciliation.

A small crew sails to a hidden cove. The first half of the story builds a
simple conflict: one pirate wants to keep a snug seat or hiding place for a
special thing, another pirate wants to share it. A flashback reveals why the
object matters, and the ending resolves the tension with a kind compromise.

This world is intentionally small and constraint-checked so that every generated
story has:
- a clear beginning on the ship,
- a middle turn with a flashback,
- an ending reconciliation image,
- and child-facing pirate prose.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("safe", 0.0)
        self.meters.setdefault("lost", 0.0)
        self.meters.setdefault("found", 0.0)
        self.memes.setdefault("longing", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("shame", 0.0)
        self.memes.setdefault("love", 0.0)
        self.memes.setdefault("joy", 0.0)
        self.memes.setdefault("softness", 0.0)
        self.memes.setdefault("grudge", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    captain: str
    mate: str
    prize: str
    place: str
    seed: Optional[int] = None


@dataclass
class World:
    captain: Entity
    mate: Entity
    prize: Entity
    place: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    flashback_done: bool = False
    reconciled: bool = False
    fired: set[str] = field(default_factory=set)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


NAMES = {
    "captain": ["Mara", "Ned", "Ivy", "Jory", "Lola", "Finn"],
    "mate": ["Bea", "Oren", "Pip", "Tess", "Milo", "June"],
}
PLACES = {
    "harbor": "the harbor",
    "cove": "the hidden cove",
    "bay": "the moonlit bay",
    "reef": "the coral reef",
}

PRIZES = {
    "snug_tush": {
        "label": "snug cushion",
        "phrase": "a snug little cushion with a red stripe",
        "kind": "cushion",
    },
    "shell_coin": {
        "label": "shell coin pouch",
        "phrase": "a tiny shell coin pouch tied with blue string",
        "kind": "pouch",
    },
    "tush_blanket": {
        "label": "tush blanket",
        "phrase": "a soft tush blanket for the captain's chair",
        "kind": "blanket",
    },
}


ASP_RULES = r"""
% An item is snug when it is kept safe on the ship.
snug(Item) :- kept_on_ship(Item).

% A flashback is needed when one pirate worries over a cherished thing.
needs_flashback(C, M, I) :- cherishes(C, I), wants_share(M, I), worried(C, I).

% Reconciliation happens when both pirates speak kindly and share the item.
reconcile(C, M, I) :- needs_flashback(C, M, I), remembers(C, I), shares(C, M, I).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("named_place", place_id, place))
    for pid, pdata in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_label", pid, pdata["label"]))
        lines.append(asp.fact("prize_kind", pid, pdata["kind"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonableness_ok(params: StoryParams) -> bool:
    return params.prize in PRIZES and params.place in PLACES and params.captain != params.mate


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show prize/1."))
    asp_prizes = {args[0] for args in asp.atoms(model, "prize")}
    py_prizes = set(PRIZES)
    if asp_prizes != py_prizes:
        print("MISMATCH between ASP and Python prize registry")
        return 1
    print(f"OK: ASP and Python agree on {len(py_prizes)} prizes.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with flashback and reconciliation.")
    ap.add_argument("--captain", choices=list(NAMES["captain"]))
    ap.add_argument("--mate", choices=list(NAMES["mate"]))
    ap.add_argument("--prize", choices=list(PRIZES))
    ap.add_argument("--place", choices=list(PLACES))
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
    captain = args.captain or rng.choice(NAMES["captain"])
    mate = args.mate or rng.choice([n for n in NAMES["mate"] if n != captain])
    prize = args.prize or rng.choice(list(PRIZES))
    place = args.place or rng.choice(list(PLACES))
    params = StoryParams(captain=captain, mate=mate, prize=prize, place=place)
    if not asp_reasonableness_ok(params):
        raise StoryError("The requested pirate story does not make sense.")
    return params


def make_world(params: StoryParams) -> World:
    captain = Entity(id=params.captain, kind="character", type="pirate", traits=["brave", "sturdy"])
    mate = Entity(id=params.mate, kind="character", type="pirate", traits=["curious", "kind"])
    prize_info = PRIZES[params.prize]
    prize = Entity(
        id=params.prize,
        type=prize_info["kind"],
        label=prize_info["label"],
        phrase=prize_info["phrase"],
        owner=captain.id,
        caretaker=captain.id,
        location="ship",
    )
    world = World(captain=captain, mate=mate, prize=prize, place=PLACES[params.place])
    world.facts.update(params=params, captain=captain, mate=mate, prize=prize)
    return world


def intro(world: World) -> None:
    c, m, p = world.captain, world.mate, world.prize
    world.say(
        f"Captain {c.id} sailed aboard the Sea Mirth, where every rope was coiled snug and every crate sat neat."
    )
    world.say(
        f"{c.id} kept {c.pronoun('possessive')} {p.label} tucked on a bench by the wheel, and {c.id} liked how it made the ship feel tidy."
    )
    world.say(
        f"Mate {m.id} peered at the bench and said the cushion looked soft enough for a tired tush after a long watch."
    )
    p.meters["safe"] += 1
    c.memes["love"] += 1
    p.memes["softness"] += 1


def conflict(world: World) -> None:
    c, m, p = world.captain, world.mate, world.prize
    world.para()
    world.say(
        f"One windy afternoon, {m.id} asked, \"May I sit on it for a spell? My legs are all wobbly from the waves.\""
    )
    c.memes["worry"] += 1
    c.memes["grudge"] += 1
    world.say(
        f"{c.id} shook {c.pronoun('possessive')} head. \"Nay, that {p.label} is kept for a special reason,\" {c.id} said."
    )
    world.say(
        f"{m.id} frowned, and the deck felt smaller. {m.id} wanted comfort, but {c.id} wanted the snug thing left untouched."
    )


def flashback(world: World) -> None:
    c, p = world.captain, world.prize
    world.para()
    world.flashback_done = True
    world.say(
        f"Then {c.id} remembered the old day that had first made the {p.label} important."
    )
    world.say(
        f"In that flashback, a storm had slapped the sails, and {c.id} had slipped on the slick boards."
    )
    world.say(
        f"The {p.label} had been there to soften the fall, so {c.id} had kept it close ever after, almost like a lucky charm."
    )
    c.memes["love"] += 1
    c.memes["softness"] += 1
    p.meters["safe"] += 1


def reconciliation(world: World) -> None:
    c, m, p = world.captain, world.mate, world.prize
    world.para()
    world.say(
        f"{m.id} looked down, then spoke softly. \"I did not mean to take your lucky thing,\" {m.id} said."
    )
    world.say(
        f"{c.id}'s face went gentle. \"And I did not mean to keep you sore on the deck,\" {c.id} answered."
    )
    world.say(
        f"So {c.id} placed the {p.label} by the helm for both of them to use, one at a time, and {m.id} promised to fold it snug after each watch."
    )
    world.say(
        f"Soon they were side by side, and the old worry drifted away like foam from the wake."
    )
    c.memes["joy"] += 1
    m.memes["joy"] += 1
    c.memes["grudge"] = 0
    m.memes["grudge"] = 0
    world.reconciled = True
    p.meters["found"] += 1


def ending(world: World) -> None:
    c, m, p = world.captain, world.mate, world.prize
    world.para()
    world.say(
        f"By sunset, the sea was gold, {m.id} had a rested tush, and the {p.label} sat snug between them like a little shared treasure."
    )
    world.say(
        f"{c.id} smiled at {m.id}, and {m.id} smiled back, because a good pirate crew can keep things safe and still be kind."
    )


def tell(params: StoryParams) -> World:
    world = make_world(params)
    intro(world)
    conflict(world)
    flashback(world)
    reconciliation(world)
    ending(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.prize
    return [
        f"Write a short pirate tale for young children that includes a snug {p.label} and a flashback.",
        f"Tell a story about two pirates who quarrel over {p.phrase} and then make up kindly.",
        f"Create a gentle pirate adventure where a captain remembers why a snug little thing mattered and shares it in the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c, m, p = world.captain, world.mate, world.prize
    return [
        QAItem(
            question=f"Who kept the {p.label} safe at the start of the story?",
            answer=f"Captain {c.id} kept the {p.label} safe at first, because {c.id} wanted it to stay snug on the ship.",
        ),
        QAItem(
            question=f"Why did {c.id} not want {m.id} to sit on the {p.label}?",
            answer=f"{c.id} worried because the {p.label} was special to {c.id}, and a flashback showed it had once softened a bad slip during a storm.",
        ),
        QAItem(
            question=f"How did {c.id} and {m.id} solve their problem in the end?",
            answer=f"They reconciled by sharing the {p.label} at the helm and promising to keep it snug after each watch.",
        ),
        QAItem(
            question="What word in the story hints that something was tucked in a comfortable way?",
            answer="The word snug shows that the cushion or blanket was kept cozy, safe, and neatly in place.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a boat that sails the sea, carries a crew, and can travel to bays, coves, and harbors.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people who were upset make up, speak kindly, and choose peace again.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part where the story briefly remembers something that happened earlier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in [world.captain, world.mate, world.prize]:
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"flashback_done={world.flashback_done} reconciled={world.reconciled}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(captain="Mara", mate="Bea", prize="snug_tush", place="harbor"),
    StoryParams(captain="Ivy", mate="Pip", prize="shell_coin", place="cove"),
    StoryParams(captain="Ned", mate="June", prize="tush_blanket", place="bay"),
]


def asp_valid_prizes() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show prize/1."))
    return sorted(set(asp.atoms(model, "prize")))


def build_sample_pool(args: argparse.Namespace, rng: random.Random) -> list[StorySample]:
    samples = []
    seen = set()
    i = 0
    while len(samples) < args.n and i < max(args.n * 50, 50):
        i += 1
        params = resolve_params(args, random.Random(rng.randrange(2**31)))
        params.seed = args.seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show prize/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show prize/1."))
        print(f"{len(asp_valid_prizes())} prizes available")
        for atom in asp.atoms(model, "prize"):
            print(atom[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = build_sample_pool(args, rng)

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
            header = f"### {p.captain} and {p.mate} at {p.place} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
