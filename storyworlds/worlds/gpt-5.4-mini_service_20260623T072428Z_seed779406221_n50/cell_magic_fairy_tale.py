#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T072428Z_seed779406221_n50/cell_magic_fairy_tale.py
====================================================================================================

A small fairy-tale storyworld about a cell, a little spell of magic, and a
careful choice that turns trouble into a blessing.

Seed tale:
---
Once there was a tiny cell in a mossy hill. The cell loved to make glow-drops
for the village lanterns. One day the cell found a cracked moonstone that made
wild magic spill everywhere. The cell worried the magic would leak into the well.
A gentle fairy taught the cell to use a leaf bowl and sing the spell softly.
The magic settled into bright, safe pearls, and the village shone kindly that
night.

This file models a compact world with:
- one small character cell with physical meters and emotional memes,
- one magical source that can leak or be guided,
- a fairy helper and a village setting,
- a reasonableness gate that only allows stories where the magic can actually
  threaten something and a believable fix exists.

The tone aims for fairy tale: simple, concrete, and a little luminous.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False
    magical: bool = False
    can_hold_magic: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fairy", "woman", "girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    affords: set[str] = field(default_factory=set)


@dataclass
class MagicSource:
    id: str
    label: str
    phrase: str
    spark: str
    leak: str
    color: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Vessel:
    id: str
    label: str
    phrase: str
    holds: set[str]
    kind: str = "vessel"
    magical: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    offer: str
    finish: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.mood: str = "soft"

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
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.mood = self.mood
        return w


@dataclass
class StoryParams:
    place: str
    source: str
    vessel: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "hill": Place("hill", "the mossy hill", "the mossy hill", {"magic", "cell"}),
    "garden": Place("garden", "the moon garden", "the moon garden", {"magic", "cell"}),
    "village": Place("village", "the little village", "the little village", {"magic", "cell"}),
}

SOURCES = {
    "moonstone": MagicSource(
        "moonstone",
        "cracked moonstone",
        "a cracked moonstone",
        "glow",
        "spill",
        "silver",
        {"magic", "glow", "spill"},
    ),
    "wand": MagicSource(
        "wand",
        "twisting wand",
        "a twisting wand",
        "spark",
        "leak",
        "gold",
        {"magic", "spark", "spill"},
    ),
    "feather": MagicSource(
        "feather",
        "star feather",
        "a star feather",
        "shine",
        "drift",
        "white",
        {"magic", "shine", "spill"},
    ),
}

VESSELS = {
    "leaf_bowl": Vessel("leaf_bowl", "leaf bowl", "a leaf bowl", {"spill", "glow"}, tags={"leaf", "bowl"}),
    "glass_jar": Vessel("glass_jar", "glass jar", "a glass jar", {"spill", "spark"}, tags={"glass", "jar"}),
    "lantern": Vessel("lantern", "lantern", "a lantern", {"glow", "shine"}, magical=True, tags={"lantern", "light"}),
}

HELPERS = {
    "fairy": Helper("fairy", "fairy", "a gentle fairy", "taught the cell to use a leaf bowl and sing the spell softly",
                    "the magic settled into bright, safe pearls", tags={"fairy", "magic"}),
    "miller": Helper("miller", "miller", "a kind miller", "showed the cell a linen pouch and a slow counting song",
                     "the magic turned into a tidy ribbon of light", tags={"miller", "song"}),
    "weaver": Helper("weaver", "weaver", "a weaving woman", "held up a silver thread and asked the cell to breathe with it",
                      "the magic braided itself into gentle beads", tags={"weaver", "thread"}),
}

CELL_NAMES = ["Pip", "Mina", "Wren", "Lio", "Nell", "Toby"]
CELL_TRAITS = ["small", "brave", "curious", "kind", "careful", "bright"]


def magic_at_risk(source: MagicSource, place: Place) -> bool:
    return "cell" in place.affords and "spill" in source.tags


def select_vessel(source: MagicSource, vessel: Vessel) -> bool:
    return any(tag in vessel.holds for tag in source.tags if tag in {"spill", "glow", "spark", "shine"})


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for s in SOURCES:
            for v in VESSELS:
                if magic_at_risk(SOURCES[s], PLACES[p]) and select_vessel(SOURCES[s], VESSELS[v]):
                    combos.append((p, s, v))
    return combos


def explain_rejection(source: MagicSource, vessel: Vessel) -> str:
    return (
        f"(No story: {source.label} needs a vessel that can hold its kind of magic, "
        f"but {vessel.label} would not make a believable fix.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about a cell and a little magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.source and args.vessel:
        if not select_vessel(SOURCES[args.source], VESSELS[args.vessel]):
            raise StoryError(explain_rejection(SOURCES[args.source], VESSELS[args.vessel]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.source is None or c[1] == args.source)
              and (args.vessel is None or c[2] == args.vessel)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, source, vessel = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(place=place, source=source, vessel=vessel, helper=helper)


def introduce(world: World, cell: Entity, helper: Entity) -> None:
    world.say(
        f"In {world.place.phrase}, there lived a tiny cell named {cell.id}, "
        f"small as a seed and bright as a dew drop."
    )
    world.say(
        f"{cell.id} loved to make glow-drops for the village lanterns, and {helper.label} "
        f"watched kindly from the path."
    )


def source_warning(world: World, source: MagicSource) -> None:
    world.say(
        f"One day {world.facts['cell'].id} found {source.phrase}. It shimmered with {source.color} magic, "
        f"and the air began to {source.leak} like a restless dream."
    )


def predict_spill(world: World, source: MagicSource, vessel: Vessel) -> bool:
    sim = world.copy()
    sim.get("source").meters["magic"] += 1
    return magic_at_risk(source, sim.place)


def offer_fix(world: World, helper: Helper, vessel: Vessel, source: MagicSource) -> bool:
    if not select_vessel(source, vessel):
        return False
    world.say(
        f"Then {helper.phrase} stepped near and {helper.offer}."
    )
    return True


def resolve(world: World, cell: Entity, helper: Entity, vessel: Vessel, source: MagicSource) -> None:
    cell.memes["relief"] += 1
    cell.memes["love"] += 1
    cell.memes["joy"] += 1
    cell.memes["fear"] = 0.0
    world.say(
        f"{helper.label.capitalize()} smiled, and together they guided the magic into {vessel.phrase}."
    )
    world.say(
        f"{helper.factsafe if False else ''}".strip()
    )
    world.say(
        f"At last, the wild shine became little safe pearls, and {cell.id} carried them to the village "
        f"where they glowed kindly through the night."
    )


def tell(place: Place, source: MagicSource, vessel: Vessel, helper_cfg: Helper, name: str = "Pip") -> World:
    world = World(place)
    cell = world.add(Entity(id=name, kind="character", type="cell", label="cell"))
    helper = world.add(Entity(id=helper_cfg.id, kind="character", type="fairy", label=helper_cfg.label))
    world.add(Entity(id="source", kind="thing", type="source", label=source.label, magical=True))
    world.add(Entity(id="vessel", kind="thing", type="vessel", label=vessel.label, magical=True, can_hold_magic=True))
    world.facts.update(cell=cell, helper=helper, source=source, vessel=vessel, place=place)

    introduce(world, cell, helper)
    world.para()
    source_warning(world, source)
    if offer_fix(world, helper_cfg, vessel, source):
        world.para()
        resolve(world, cell, helper, vessel, source)
    else:
        world.say(
            f"But {vessel.phrase} could not hold that kind of magic, so the shine slipped toward the well."
        )
        world.say(
            f"{helper.label.capitalize()} hurried to teach {cell.id} a safer way, before the village could be muddled."
        )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale for a young child about a cell named {f["cell"].id} who finds {f["source"].phrase} and learns to guide the magic safely.',
        f'Tell a gentle story where {f["cell"].id} in {f["place"].label} uses {f["vessel"].phrase} with help from {f["helper"].label}.',
        'Write a small, magical fairy tale ending with bright safe light in the village.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cell = f["cell"]
    helper = f["helper"]
    source = f["source"]
    vessel = f["vessel"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who is the story about in {place.label}?",
            answer=f"It is about {cell.id}, a tiny cell living in {place.label}, and the kind helper {helper.label}.",
        ),
        QAItem(
            question=f"What magical thing did {cell.id} find?",
            answer=f"{cell.id} found {source.phrase}, and it shimmered with {source.color} magic.",
        ),
        QAItem(
            question=f"What did {helper.label} use to help the magic?",
            answer=f"{helper.label.capitalize()} helped guide the magic with {vessel.phrase}, so the shine could stay safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cell?",
            answer="In this fairy tale, a cell is a tiny living thing. It is so small that you need imagination to picture it walking in the world.",
        ),
        QAItem(
            question="What is magic in a fairy tale?",
            answer="Magic in a fairy tale is a special power that can glow, change, or move in surprising ways.",
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
        if e.magical:
            bits.append("magical=True")
        if e.can_hold_magic:
            bits.append("can_hold_magic=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
risk(Source, Place) :- source(Source), place(Place), place_affords(Place, cell), source_tags(Source, spill).
fix(Source, Vessel) :- source(Source), vessel(Vessel), vessel_holds(Vessel, spill), source_tags(Source, spill).
valid(Place, Source, Vessel) :- risk(Source, Place), fix(Source, Vessel).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("place_affords", pid, a))
    for sid, s in SOURCES.items():
        lines.append(asp.fact("source", sid))
        for tag in sorted(s.tags):
            lines.append(asp.fact("source_tags", sid, tag))
    for vid, v in VESSELS.items():
        lines.append(asp.fact("vessel", vid))
        for h in sorted(v.holds):
            lines.append(asp.fact("vessel_holds", vid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], SOURCES[params.source], VESSELS[params.vessel], HELPERS[params.helper])
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
    StoryParams(place="hill", source="moonstone", vessel="leaf_bowl", helper="fairy"),
    StoryParams(place="garden", source="wand", vessel="lantern", helper="miller"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
