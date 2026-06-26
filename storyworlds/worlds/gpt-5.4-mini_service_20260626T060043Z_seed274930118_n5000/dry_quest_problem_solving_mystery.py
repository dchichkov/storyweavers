#!/usr/bin/env python3
"""
A standalone storyworld about a dry quest: a child follows clues, solves a small
mystery, and finds something that had stayed dry all along.

The premise is built for a TinyStories-style mystery:
- a child wants to find a missing prize
- the search has clues, false leads, and a careful turn
- problem solving reveals where the prize was hidden
- the ending proves the prize is dry, safe, and recovered

The world model tracks:
- physical meters: dryness, hiddenness, clue strength, distance
- emotional memes: curiosity, worry, confidence, relief
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden_in: str = ""
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["dry", "hidden", "distance", "clue", "dust"]:
            self.meters.setdefault(key, 0.0)
        for key in ["curiosity", "worry", "confidence", "relief"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def name(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    hides: set[str] = field(default_factory=set)
    dry_spot: bool = True
    clue_kind: str = "none"


@dataclass
class Clue:
    id: str
    place: str
    text: str
    reveals: str
    strength: float = 1.0


@dataclass
class StoryParams:
    place: str
    missing: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.clues: list[Clue] = []
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        c = World(self.place)
        c.entities = _copy.deepcopy(self.entities)
        c.clues = _copy.deepcopy(self.clues)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


PLACE_REGISTRY = {
    "shed": Place(id="shed", label="the shed", hides={"box", "bucket"}, dry_spot=True, clue_kind="scratch"),
    "attic": Place(id="attic", label="the attic", hides={"trunk", "chest"}, dry_spot=True, clue_kind="dust"),
    "porch": Place(id="porch", label="the porch", hides={"boot", "umbrella"}, dry_spot=False, clue_kind="mud"),
    "library": Place(id="library", label="the little library corner", hides={"book", "map"}, dry_spot=True, clue_kind="bookmark"),
}

MISSING_REGISTRY = {
    "blue_box": {"label": "blue box", "phrase": "a small blue box with a silver latch", "type": "box"},
    "paper_map": {"label": "paper map", "phrase": "a folded paper map with a red star", "type": "map"},
    "toy_compass": {"label": "toy compass", "phrase": "a round toy compass in a yellow case", "type": "compass"},
    "gold_key": {"label": "gold key", "phrase": "a tiny gold key tied with string", "type": "key"},
}

CHILD_NAMES = ["Mina", "Leo", "Tia", "Noah", "Ari", "Zoe", "Ivy", "Ben"]
HELPER_NAMES = ["Nora", "Milo", "Ada", "Finn", "June", "Owen", "Lena", "Eli"]
TYPES = ["girl", "boy"]
HELPER_TYPES = {"mother", "father", "adult"}

CLUE_TEXT = {
    "scratch": "There was a thin scratch on the floor near the door.",
    "dust": "A little line of dust pointed toward the back shelf.",
    "mud": "A muddy print looked like someone had walked in and out quickly.",
    "bookmark": "A bookmark was sticking out from the wrong page.",
}


def _rule_follow_clue(world: World) -> list[str]:
    out = []
    child = world.get("child")
    item = world.get("missing")
    for clue in world.clues:
        sig = ("clue", clue.id)
        if sig in world.fired:
            continue
        if clue.reveals != item.hidden_in:
            continue
        world.fired.add(sig)
        child.meters["clue"] += clue.strength
        child.memes["confidence"] += 1
        out.append(f"{clue.text} {child.name} noticed it and felt sure the search was getting warmer.")
    return out


def _rule_worry_to_problem(world: World) -> list[str]:
    child = world.get("child")
    item = world.get("missing")
    if child.memes["worry"] < THRESHOLD:
        return []
    sig = ("problem", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["hidden"] += 1
    return [f"The mystery grew trickier, because the missing {item.label} still was not where it should have been."]


def _rule_find(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    item = world.get("missing")
    if child.meters["clue"] < THRESHOLD:
        return []
    sig = ("find", item.id)
    if sig in world.fired:
        return []
    if item.hidden_in != world.place.id:
        return []
    world.fired.add(sig)
    item.found = True
    item.meters["hidden"] = 0
    item.meters["dry"] = 1
    child.memes["relief"] += 1
    child.memes["confidence"] += 1
    helper.memes["relief"] += 1
    return [f"At last, the clues led straight to the {world.place.label}, where the missing thing was waiting in a dry little spot."]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in [_rule_follow_clue, _rule_worry_to_problem, _rule_find]:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_story_world(params: StoryParams) -> World:
    place = PLACE_REGISTRY[params.place]
    world = World(place)

    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    item_cfg = MISSING_REGISTRY[params.missing]
    item = world.add(Entity(
        id="missing",
        type=item_cfg["type"],
        label=item_cfg["label"],
        phrase=item_cfg["phrase"],
        hidden_in=place.id,
    ))
    item.meters["hidden"] = 1.0
    item.meters["dry"] = 1.0

    child.memes["curiosity"] = 1.0
    child.memes["worry"] = 1.0
    helper.memes["confidence"] = 1.0

    clue = Clue(
        id="main_clue",
        place=place.id,
        text=CLUE_TEXT[place.clue_kind],
        reveals=place.id,
        strength=1.0,
    )
    world.clues.append(clue)

    world.facts.update(child=child, helper=helper, item=item, clue=clue, place=place)
    return world


def tell(params: StoryParams) -> World:
    world = build_story_world(params)
    child = world.get("child")
    helper = world.get("helper")
    item = world.get("missing")
    place = world.place

    world.say(f"{child.name} had a small mystery to solve.")
    world.say(f"A missing {item.label} had vanished, and nobody wanted it to stay lost.")
    world.say(f"{child.name} and {helper.name} went to {place.label} to look for clues.")

    world.para()
    world.say(f"{child.name} looked under shelves and beside boxes, searching carefully.")
    world.say(f"{helper.name} pointed out the first clue: {world.clues[0].text.lower()}")
    propagate(world, narrate=True)

    world.para()
    world.say(f"For a moment, {child.name} worried the search might fail.")
    child.memes["worry"] += 1.0
    propagate(world, narrate=True)

    world.para()
    if item.found:
        world.say(
            f"Then {child.name} lifted the last cover, and there it was: {item.phrase}, safe and dry."
        )
        world.say(
            f"{child.name} grinned, and {helper.name} smiled too, because the little mystery was finally solved."
        )
    else:
        world.say(
            f"They kept following the clue until the missing thing turned up dry and safe at the end."
        )

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    item = f["item"]
    place = f["place"]
    return [
        f"Write a short mystery story for a young child about {child.label} searching for {item.label} at {place.label}.",
        f"Tell a gentle quest where {child.label} and {helper.label} solve a problem and find {item.phrase} dry and safe.",
        f"Write a simple story with clues, a worried moment, and a happy ending in {place.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    item = f["item"]
    place = f["place"]
    clue = f["clue"]

    return [
        QAItem(
            question=f"What mystery were {child.label} and {helper.label} trying to solve?",
            answer=f"They were trying to find the missing {item.label} and figure out where it had been hidden.",
        ),
        QAItem(
            question=f"What clue helped {child.label} keep searching in {place.label}?",
            answer=f"The clue was: {clue.text} That clue made the search feel closer to the answer.",
        ),
        QAItem(
            question=f"Where was the missing {item.label} found at the end?",
            answer=f"It was found in {place.label}, tucked into a dry little spot, safe and not damaged.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean if something is dry?",
            answer="Something dry does not have water on it. It can feel safe, clean, and not soggy.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone solve a mystery or a problem.",
        ),
        QAItem(
            question="What does a helper do in a quest?",
            answer="A helper supports the search, notices useful things, and helps the main character keep going.",
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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A missing item is at a place when it was hidden there.
at_place(I,P) :- item(I), hidden_in(I,P).

% A clue helps when it points to the same place.
helps(C,I) :- clue(C), item(I), points_to(C,P), hidden_in(I,P).

% A story is reasonable if the child gets at least one useful clue and the item
% is found in a dry place.
reasonable(P, I) :- place(P), item(I), hidden_in(I,P), dry_place(P), has_clue(P), found(I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACE_REGISTRY.items():
        lines.append(asp.fact("place", pid))
        if place.dry_spot:
            lines.append(asp.fact("dry_place", pid))
        if place.clue_kind != "none":
            lines.append(asp.fact("has_clue", pid))
    for mid, cfg in MISSING_REGISTRY.items():
        lines.append(asp.fact("item", mid))
    # Representative hidden-in placements; combinatorics are constrained by Python gate.
    for pid in PLACE_REGISTRY:
        for mid in MISSING_REGISTRY:
            lines.append(asp.fact("hidden_in", mid, pid))
    for cid, place in PLACE_REGISTRY.items():
        lines.append(asp.fact("clue", f"c_{cid}"))
        lines.append(asp.fact("points_to", f"c_{cid}", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_relevant() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def python_reasonable() -> list[tuple[str, str]]:
    out = []
    for pid, place in PLACE_REGISTRY.items():
        if not place.dry_spot or place.clue_kind == "none":
            continue
        for mid in MISSING_REGISTRY:
            out.append((pid, mid))
    return sorted(out)


def asp_verify() -> int:
    import asp
    a = set(asp_relevant())
    p = set(python_reasonable())
    if a == p:
        print(f"OK: clingo gate matches python gate ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A dry mystery quest storyworld with problem solving.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--missing", choices=MISSING_REGISTRY)
    ap.add_argument("--child-name", choices=CHILD_NAMES)
    ap.add_argument("--child-type", choices=TYPES)
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
    ap.add_argument("--helper-type", choices=["mother", "father"])
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
    places = list(PLACE_REGISTRY)
    missings = list(MISSING_REGISTRY)
    if args.place and args.place not in PLACE_REGISTRY:
        raise StoryError("Unknown place.")
    if args.missing and args.missing not in MISSING_REGISTRY:
        raise StoryError("Unknown missing item.")
    if args.place and not PLACE_REGISTRY[args.place].dry_spot:
        raise StoryError("This story needs a dry place so the ending can prove the prize stayed dry.")

    place = args.place or rng.choice(places)
    missing = args.missing or rng.choice(missings)
    child_type = args.child_type or rng.choice(TYPES)
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    helper_type = args.helper_type or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        missing=missing,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
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
    StoryParams(place="shed", missing="blue_box", child_name="Mina", child_type="girl", helper_name="Nora", helper_type="mother"),
    StoryParams(place="attic", missing="paper_map", child_name="Leo", child_type="boy", helper_name="Milo", helper_type="father"),
    StoryParams(place="library", missing="toy_compass", child_name="Ivy", child_type="girl", helper_name="Ada", helper_type="mother"),
    StoryParams(place="shed", missing="gold_key", child_name="Ben", child_type="boy", helper_name="Finn", helper_type="father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_relevant()
        print(f"{len(combos)} reasonable place/item pairs:\n")
        for place, item in combos:
            print(f"  {place:10} {item}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
