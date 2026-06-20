#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    height: int
    stable: bool = True


@dataclass
class TowerPiece:
    id: str
    label: str
    complement: str
    weight: int
    stabilizes: int


@dataclass
class StoryParams:
    place: str
    mammoth: str
    piece: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_wobble(world: World) -> list[str]:
    out = []
    mast = world.get("tower")
    if mast.meters["stacked"] < THRESHOLD:
        return out
    if mast.meters["wobble"] >= THRESHOLD:
        return out
    sig = ("wobble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mast.meters["wobble"] += 1
    child = world.get("child")
    helper = world.get("helper")
    child.memes["suspense"] += 1
    helper.memes["alert"] += 1
    out.append("The tower swayed just a little, and everyone held their breath.")
    return out


def _r_complement(world: World) -> list[str]:
    out = []
    if world.get("tower").meters["wobble"] < THRESHOLD:
        return out
    sig = ("complement",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tower = world.get("tower")
    piece = world.get("piece")
    tower.meters["stable"] += piece.meters["support"]
    if tower.meters["stable"] >= 2:
        tower.meters["wobble"] = 0
        tower.memes["pride"] += 1
        out.append("Then the right complement slid into place and the tower stood steady again.")
    return out


def _r_warmth(world: World) -> list[str]:
    out = []
    if world.get("tower").meters["stable"] < 2:
        return out
    sig = ("warmth",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    helper = world.get("helper")
    mammoth = world.get("mammoth")
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    mammoth.memes["calm"] += 1
    out.append("The mammoth gave a soft, grateful rumble, as if it knew it had been helped in time.")
    return out


CAUSAL_RULES = [Rule("wobble", _r_wobble), Rule("complement", _r_complement), Rule("warmth", _r_warmth)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming tiny storyworld about a mammoth, a tower, and the right complement.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mammoth", choices=MAMMOTHS)
    ap.add_argument("--piece", choices=PIECES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def hazard_ok(place: Place, mammoth: str, piece: TowerPiece) -> bool:
    return place.height >= 1 and piece.weight <= 3


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, p in PLACES.items():
        for mid in MAMMOTHS:
            for piece_id, pc in PIECES.items():
                if hazard_ok(p, mid, pc):
                    out.append((pid, mid, piece_id))
    return out


def sensible_pieces() -> list[str]:
    return [pid for pid, p in PIECES.items() if p.stabilizes >= 1]


ASP_RULES = r"""
hazard(P, M, C) :- place(P), mammoth(M), piece(C).
valid(P, M, C) :- hazard(P, M, C), stable_piece(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid in MAMMOTHS:
        lines.append(asp.fact("mammoth", mid))
    for cid, c in PIECES.items():
        lines.append(asp.fact("piece", cid))
        if c.stabilizes >= 1:
            lines.append(asp.fact("stable_piece", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    c, p = set(asp_valid_combos()), set(valid_combos())
    if c == p:
        print(f"OK: clingo gate matches valid_combos() ({len(c)} combos).")
        return 0
    print("MISMATCH between clingo and python gates")
    if c - p:
        print("only in clingo:", sorted(c - p))
    if p - c:
        print("only in python:", sorted(p - c))
    return 1


def tell(place: Place, mammoth: str, piece: TowerPiece, child: Entity, helper: Entity) -> World:
    w = World()
    tower = w.add(Entity(id="tower", kind="thing", type="tower", label=place.label))
    m = w.add(Entity(id="mammoth", kind="thing", type="mammoth", label=mammoth))
    c = w.add(child)
    h = w.add(helper)
    tower.meters["stable"] = 1
    tower.meters["stacked"] = 1
    tower.memes["hope"] = 1
    m.memes["curious"] = 1
    w.say(f"On a bright afternoon, {c.id} and {h.id} built a little tower beside {mammoth}.")
    w.say(f"They chose a {piece.label} as the complement, because it fit the tower just right.")
    w.para()
    w.say(f"{mammoth} watched with wide, gentle eyes while the last block went on top.")
    w.say("For a moment, the stack looked almost too tall.")
    propagate(w, narrate=True)
    w.para()
    if tower.meters["wobble"] >= THRESHOLD:
        w.say(f"{h.id} touched the side of the tower and found the exact place where the complement belonged.")
        piece.meters["support"] = 1
        tower.meters["stable"] += piece.meters["support"]
        tower.meters["wobble"] = 0
        w.say(f"With one careful nudge, the tower grew steady again, and {mammoth} gave a happy rumble.")
        propagate(w, narrate=True)
    else:
        w.say(f"The tower stayed steady, and {mammoth} leaned in close to admire the work.")
    w.para()
    w.say(f"At the end, {c.id} and {h.id} smiled at the tower, the mammoth, and the neat little complement that made everything hold together.")
    w.facts.update(place=place, mammoth=mammoth, piece=piece, child=c, helper=h, outcome="steady" if tower.meters["wobble"] < THRESHOLD else "rescued")
    return w


PLACES = {
    "hill": Place("hill", "the hill", 3),
    "museum": Place("museum", "the little museum room", 2),
    "yard": Place("yard", "the sunny yard", 2),
}

MAMMOTHS = {
    "milo": "Milo",
    "mira": "Mira",
    "moss": "Moss",
}

PIECES = {
    "brace": TowerPiece("brace", "wooden brace", "complement", 2, 1),
    "ramp": TowerPiece("ramp", "small ramp", "complement", 1, 1),
    "flag": TowerPiece("flag", "bright flag", "complement", 1, 1),
}

CHILD_NAMES = ["Lina", "Noah", "Maya", "Eli", "Iris", "Theo"]
HELPER_NAMES = ["Grandma", "Grandpa", "Aunt June", "Uncle Ben", "Rina", "Owen"]

CURATED = [
    StoryParams("hill", "milo", "brace", "Lina", "girl", "Grandma", "girl"),
    StoryParams("museum", "mira", "ramp", "Noah", "boy", "Owen", "boy"),
    StoryParams("yard", "moss", "flag", "Maya", "girl", "Aunt June", "girl"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mammoth is None or c[1] == args.mammoth)
              and (args.piece is None or c[2] == args.piece)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mammoth, piece = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(place, mammoth, piece, name, child_gender, helper, helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story that includes the words mammoth, tower, and complement.',
        f"Tell a gentle suspense story about {f['child'].id} and {f['helper'].id} building a tower near a mammoth, then finding the right complement in time.",
        f"Write a story with foreshadowing and a sweet twist: a tower wobbles, but the unexpected complement saves the day.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    piece = f["piece"]
    mammoth = f["mammoth"]
    return [
        ("Who built the tower?", f"{child.id} built it with {helper.id}, and they worked together beside {mammoth}.") ,
        ("What was the complement?", f"The complement was {piece.label}, which fit the tower and helped it stay steady.") ,
        ("What was the suspense in the story?", f"The tower wobbled for a moment, so everyone had to wait and see if it would stay up. The worry turned into relief when the complement fixed the balance."),
        ("What was the twist?", f"The twist was that the thing they first thought was only decoration turned out to be exactly what the tower needed. It became the useful piece that saved the day."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a mammoth?", "A mammoth was a very large elephant-like animal with thick fur and big tusks. People know them from long ago."),
        ("What does complement mean?", "A complement is something that goes well with something else and helps make it complete. It can be the missing piece that fits just right."),
        ("Why do towers wobble?", "Tall towers can wobble if they are too heavy on top or not balanced well. A steady base helps keep them safe."),
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
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        MAMMOTHS[params.mammoth],
        PIECES[params.piece],
        Entity(id=params.child, kind="character", type=params.child_gender, role="child"),
        Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"),
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, mammoth, piece) combos:\n")
        for t in combos:
            print(f"  {t[0]:8} {t[1]:8} {t[2]}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.child} and {p.helper}: {p.mammoth}, {p.piece}, {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
