#!/usr/bin/env python3
"""
storyworlds/worlds/versatile_mystery_to_solve_reconciliation_detective_story.py
===============================================================================

A small detective-story world about a versatile little mystery that gets solved
through careful clue-hunting and a reconciliation at the end.

Premise:
- A child detective notices something missing or mixed up.
- The detective follows concrete clues in a tiny setting.
- The problem is not a real villain; it is a misunderstanding or misplaced item.
- The turn comes when the detective connects the clues.
- The ending gives back the item, repairs feelings, and proves the world changed.

This script follows the storyworld contract:
- typed entities with meters and memes
- state-driven prose
- reasonableness gate + inline ASP twin
- QA prompts, story QA, world QA
- CLI with --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    suspicious: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Location:
    place: str
    indoor: bool = True
    clues: set[str] = field(default_factory=set)
    atmosphere: str = "quiet"


@dataclass
class Mystery:
    id: str
    missing: str
    trail: list[str]
    reveal_by: str
    false_lead: str = ""
    tension: str = ""


@dataclass
class World:
    location: Location
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    clue_log: list[str] = field(default_factory=list)

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
        clone = World(self.location)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.clue_log = list(self.clue_log)
        return clone


@dataclass
class StoryParams:
    place: str
    mystery: str
    detective_name: str
    detective_type: str
    friend_name: str
    friend_type: str
    item: str
    seed: Optional[int] = None


PLACES = {
    "library": Location(place="the library", indoor=True, clues={"paper", "ink", "bookmark"}, atmosphere="quiet"),
    "kitchen": Location(place="the kitchen", indoor=True, clues={"crumbs", "drawer", "spoon"}, atmosphere="busy"),
    "classroom": Location(place="the classroom", indoor=True, clues={"desk", "chalk", "note"}, atmosphere="still"),
    "yard": Location(place="the yard", indoor=False, clues={"mud", "shoeprint", "leaf"}, atmosphere="bright"),
}

MYSTERIES = {
    "missing_book": Mystery(
        id="missing_book",
        missing="book",
        trail=["paper", "bookmark", "ink"],
        reveal_by="under a cushion",
        false_lead="the tall shelf",
        tension="worries",
    ),
    "missing_cookie": Mystery(
        id="missing_cookie",
        missing="cookie",
        trail=["crumbs", "spoon", "napkin"],
        reveal_by="inside a tin box",
        false_lead="the open counter",
        tension="feels puzzled",
    ),
    "missing_key": Mystery(
        id="missing_key",
        missing="key",
        trail=["drawer", "metal", "tap"],
        reveal_by="on a string near the door",
        false_lead="the pocket",
        tension="is a little upset",
    ),
    "missing_crayon": Mystery(
        id="missing_crayon",
        missing="crayon",
        trail=["chalk", "note", "color"],
        reveal_by="in a pencil cup",
        false_lead="the floor",
        tension="feels cross",
    ),
}

ITEMS = {
    "book": ("book", "a bright library book", "book"),
    "cookie": ("cookie", "a small cookie with a smiley face", "cookie"),
    "key": ("key", "a brass key with a round top", "key"),
    "crayon": ("crayon", "a red crayon with a chewed tip", "crayon"),
}

DETECTIVE_NAMES = ["Mina", "Jules", "Ada", "Nico", "Riley", "Toby", "Lena", "Pip"]
FRIEND_NAMES = ["Ben", "Sara", "Owen", "Tia", "Mia", "Noah", "June", "Ivy"]
TRAITS = ["curious", "careful", "brave", "patient", "clever", "kind"]


def reasonableness_gate(place: str, mystery_id: str, item_id: str) -> bool:
    mystery = MYSTERIES[mystery_id]
    return mystery.missing == item_id and item_id in ITEMS and place in PLACES


def explain_rejection(place: str, mystery_id: str, item_id: str) -> str:
    mystery = MYSTERIES.get(mystery_id)
    if mystery is None:
        return "(No story: that mystery is not in this little detective world.)"
    if item_id not in ITEMS:
        return "(No story: that item is not available in this little detective world.)"
    return (
        f"(No story: a missing {item_id} story only works when the lost item is actually a {mystery.missing}. "
        f"Try a matching pair.)"
    )


def build_world(params: StoryParams) -> World:
    loc = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(loc)

    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        traits=["little", "versatile", "observant"],
        meters={"attention": 0.0},
        memes={"curiosity": 1.0, "resolve": 1.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_type,
        traits=["little", "shy"],
        meters={"attention": 0.0},
        memes={"worry": 1.0, "hurt": 0.0, "relief": 0.0},
    ))
    item_type, item_phrase, item_label = ITEMS[params.item]
    lost_item = world.add(Entity(
        id="missing_item",
        kind="thing",
        type=item_type,
        label=item_label,
        phrase=item_phrase,
        owner=friend.id,
        hidden_in="somewhere",
        suspicious=False,
        meters={"clean": 1.0},
        memes={"importance": 1.0},
    ))
    world.facts.update(
        detective=detective,
        friend=friend,
        item=lost_item,
        mystery=mystery,
        location=loc,
        trail=list(mystery.trail),
    )
    return world


def _rule_attention(world: World) -> list[str]:
    out: list[str] = []
    det = world.facts["detective"]
    det.meters["attention"] += 1.0
    sig = ("attention", det.id)
    if sig not in world.fired:
        world.fired.add(sig)
        out.append(f"{det.id} looked closely at the room and noticed the tiny details.")
    return out


def _rule_clue_chain(world: World) -> list[str]:
    out: list[str] = []
    mystery: Mystery = world.facts["mystery"]
    trail = mystery.trail
    for clue in trail:
        if clue in world.location.clues and clue not in world.clue_log:
            world.clue_log.append(clue)
            sig = ("clue", clue)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(f"A small clue stood out: {clue}.")
    return out


def _rule_reveal(world: World) -> list[str]:
    out: list[str] = []
    mystery: Mystery = world.facts["mystery"]
    item: Entity = world.facts["item"]
    if len(world.clue_log) >= 2 and item.hidden_in != mystery.reveal_by:
        sig = ("reveal", mystery.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        item.hidden_in = mystery.reveal_by
        out.append(f"The clues pointed toward {mystery.reveal_by}.")
    return out


def _rule_reconciliation(world: World) -> list[str]:
    out: list[str] = []
    detective: Entity = world.facts["detective"]
    friend: Entity = world.facts["friend"]
    item: Entity = world.facts["item"]
    sig = ("reconcile", item.id)
    if item.hidden_in and item.hidden_in != "somewhere" and sig not in world.fired:
        world.fired.add(sig)
        friend.memes["worry"] = 0.0
        friend.memes["hurt"] = 0.0
        friend.memes["relief"] = 1.0
        detective.memes["resolve"] += 1.0
        out.append(f"{detective.id} brought the item back, and the misunderstanding finally melted away.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_rule_attention, _rule_clue_chain, _rule_reveal, _rule_reconciliation):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(params: StoryParams) -> World:
    world = build_world(params)
    det = world.facts["detective"]
    friend = world.facts["friend"]
    item = world.facts["item"]
    mystery: Mystery = world.facts["mystery"]

    world.say(
        f"On a quiet day at {world.location.place}, {det.id} was the little detective, clever and versatile."
    )
    world.say(
        f"{det.pronoun().capitalize()} noticed that {friend.id} {mystery.tension} because the {item.label} was missing."
    )
    world.para()
    world.say(
        f"{det.id} searched carefully around the room, checking the obvious places first."
    )
    world.say(
        f"{friend.id} pointed toward {mystery.false_lead}, but {det.id} kept following the small clues instead."
    )
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"At last, {det.id} found the {item.label} {mystery.reveal_by}."
    )
    world.say(
        f"{det.id} gave it back, and {friend.id} smiled with relief."
    )
    world.say(
        f"The two friends apologized to each other, laughed a little, and walked away together."
    )

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det = f["detective"]
    friend = f["friend"]
    item = f["item"]
    mystery = f["mystery"]
    return [
        f'Write a short detective story for a young child with the word "versatile" in it.',
        f"Tell a gentle mystery where {det.id} notices that {friend.id}'s {item.label} is missing and solves the clue trail.",
        f"Write a simple reconciliation story where two little friends misunderstand each other and then make things right.",
        f"Make the ending show how the lost {item.label} was found and the friends felt better afterward.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"]
    friend = f["friend"]
    item = f["item"]
    mystery = f["mystery"]
    loc = f["location"]
    return [
        QAItem(
            question=f"Who was the little detective at {loc.place}?",
            answer=f"{det.id} was the little detective at {loc.place}. {det.id} was curious, careful, and versatile."
        ),
        QAItem(
            question=f"What was missing from {friend.id}?",
            answer=f"The missing thing was {item.label}. That was the item {friend.id} cared about."
        ),
        QAItem(
            question=f"How did {det.id} solve the mystery?",
            answer=(
                f"{det.id} followed the clues one by one, noticed where they pointed, and found the {item.label} "
                f"{mystery.reveal_by}."
            ),
        ),
        QAItem(
            question=f"Why did {friend.id} feel better at the end?",
            answer=(
                f"{friend.id} felt better because the lost {item.label} came back, the misunderstanding was fixed, "
                f"and the two friends made up."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer=(
                "A detective looks carefully for clues, asks questions, and tries to figure out what really happened."
            ),
        ),
        QAItem(
            question="What is a clue?",
            answer=(
                "A clue is a small piece of information that helps someone solve a mystery."
            ),
        ),
        QAItem(
            question="What is reconciliation?",
            answer=(
                "Reconciliation is when people stop being upset and make peace again."
            ),
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
        if e.kind == "thing":
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:14} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  clues found: {world.clue_log}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, loc in PLACES.items():
        lines.append(asp.fact("place", pid))
        if loc.indoor:
            lines.append(asp.fact("indoor", pid))
        for clue in sorted(loc.clues):
            lines.append(asp.fact("has_clue", pid, clue))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, mystery.missing))
        lines.append(asp.fact("reveal_by", mid, mystery.reveal_by))
        for clue in mystery.trail:
            lines.append(asp.fact("trail", mid, clue))
    for iid, (itype, _, _) in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_type", iid, itype))
    return "\n".join(lines)


ASP_RULES = r"""
mystery_solved(M) :- missing(M, I), trail(M, C1), trail(M, C2), C1 != C2.
compatible_story(P, M, I) :- place(P), mystery(M), missing(M, I), item(I).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/3."))
    return sorted(set(asp.atoms(model, "compatible_story")))


def asp_verify() -> int:
    python_set = {
        (place, mid, item)
        for place in PLACES
        for mid, mystery in MYSTERIES.items()
        for item in ITEMS
        if reasonableness_gate(place, mid, item)
    }
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python gate ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective-story world about a versatile mystery and reconciliation.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
    ap.add_argument("--item", choices=ITEMS.keys())
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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
    if args.mystery and args.item and not reasonableness_gate(args.place or "library", args.mystery, args.item):
        raise StoryError(explain_rejection(args.place or "library", args.mystery, args.item))
    combos = [
        (p, m, i)
        for p in PLACES
        for m in MYSTERIES
        for i in ITEMS
        if reasonableness_gate(p, m, i)
        and (args.place is None or p == args.place)
        and (args.mystery is None or m == args.mystery)
        and (args.item is None or i == args.item)
    ]
    if not combos:
        raise StoryError("(No valid detective mystery matches the given options.)")
    place, mystery, item = rng.choice(sorted(combos))
    det_type = args.detective_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or rng.choice(["girl", "boy"])
    det_name = args.detective_name or rng.choice(DETECTIVE_NAMES)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    if det_name == friend_name:
        friend_name = rng.choice([n for n in FRIEND_NAMES if n != det_name])
    return StoryParams(
        place=place,
        mystery=mystery,
        detective_name=det_name,
        detective_type=det_type,
        friend_name=friend_name,
        friend_type=friend_type,
        item=item,
    )


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
    StoryParams(place="library", mystery="missing_book", detective_name="Mina", detective_type="girl", friend_name="Ben", friend_type="boy", item="book"),
    StoryParams(place="kitchen", mystery="missing_cookie", detective_name="Jules", detective_type="boy", friend_name="Tia", friend_type="girl", item="cookie"),
    StoryParams(place="classroom", mystery="missing_crayon", detective_name="Ada", detective_type="girl", friend_name="Noah", friend_type="boy", item="crayon"),
    StoryParams(place="yard", mystery="missing_key", detective_name="Nico", detective_type="boy", friend_name="Ivy", friend_type="girl", item="key"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible_story/3."))
        combos = sorted(set(asp.atoms(model, "compatible_story")))
        print(f"{len(combos)} compatible story combos:\n")
        for place, mystery, item in combos:
            print(f"  {place:10} {mystery:14} {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.detective_name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
