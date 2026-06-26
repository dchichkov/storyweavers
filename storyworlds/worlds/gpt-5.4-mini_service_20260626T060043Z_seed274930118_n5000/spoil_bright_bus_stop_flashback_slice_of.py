#!/usr/bin/env python3
"""
storyworlds/worlds/spoil_bright_bus_stop_flashback_slice_of.py
===============================================================

A small slice-of-life story world set at a bus stop.

Premise:
- A child and caregiver wait at a bus stop on a bright day.
- A bright snack or treat can spoil in the heat.
- A short flashback shows why the caregiver is careful.
- The story ends with a small, gentle solution: they keep the treat cool and
  wait together until the bus arrives.

This world is intentionally small and constraint-driven: the main tension is
whether the bright snack will spoil before the bus comes, and the turn is a
practical, child-friendly fix that changes the world state.
"""

from __future__ import annotations

import argparse
import copy
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    label: str
    shade: bool = False
    benches: bool = True


@dataclass
class Snack:
    label: str
    phrase: str
    spoil_kind: str
    sensitive_to_heat: bool = True
    bright: bool = True


@dataclass
class Cover:
    id: str
    label: str
    protects: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.flashback_used: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.flashback_used = self.flashback_used
        return clone


@dataclass
class StoryParams:
    place: str
    child: str
    child_type: str
    caregiver: str
    caregiver_type: str
    snack: str
    cover: str
    seed: Optional[int] = None


PLACES = {
    "bus_stop": Place(label="the bus stop", shade=False, benches=True),
}

CHILD_NAMES = ["Maya", "Noah", "Lina", "Eli", "Nora", "Theo", "Ava", "Finn"]
CARE_NAMES = ["Mom", "Dad", "Aunt Jo", "Uncle Ben", "Grandma", "Grandpa"]

SNACKS = {
    "fruit_cup": Snack(label="fruit cup", phrase="a bright fruit cup", spoil_kind="spoiled"),
    "yogurt": Snack(label="yogurt", phrase="a bright yogurt cup", spoil_kind="spoiled"),
    "sandwich": Snack(label="sandwich", phrase="a bright little sandwich", spoil_kind="soggy"),
}

COVERS = {
    "lunch_bag": Cover(
        id="lunch_bag",
        label="a lunch bag",
        protects={"heat"},
        prep="put the snack into a lunch bag and sit it in the shade",
        tail="kept the snack tucked inside the lunch bag",
    ),
    "thermos_pack": Cover(
        id="thermos_pack",
        label="an ice pack",
        protects={"heat"},
        prep="wrap the snack with an ice pack",
        tail="kept the snack cool beside the ice pack",
    ),
}

# Inline ASP twin. Small and declarative.
ASP_RULES = r"""
#show risky/1.
#show fix/2.

risky(S) :- snack(S), bright(S), heat_sensitive(S), waiting(bus_stop).

fix(S, C) :- risky(S), cover(C), protects(C, heat).
"""


def heat_risk(world: World, snack: Entity) -> bool:
    return world.place.label == "the bus stop" and snack.meters.get("heat", 0) >= THRESHOLD and snack.meters.get("safe", 0) < THRESHOLD


def choose_cover(snack: Snack) -> Optional[Cover]:
    for c in COVERS.values():
        if "heat" in c.protects:
            return c
    return None


def flashback(world: World, caregiver: Entity, child: Entity, snack: Entity) -> None:
    if world.flashback_used:
        return
    world.flashback_used = True
    world.say(
        f"For a moment, {caregiver.id} remembered another wait at a bus stop, "
        f"when {child.id}'s snack had been left out and turned spoiled before the bus came."
    )
    world.say(
        f"That memory made {caregiver.pronoun('subject')} reach for a cooler plan right away."
    )


def setup_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    child = world.add(Entity(id=params.child, kind="character", type=params.child_type))
    caregiver = world.add(Entity(id=params.caregiver, kind="character", type=params.caregiver_type))
    snack_cfg = SNACKS[params.snack]
    snack = world.add(Entity(
        id="snack",
        type="snack",
        label=snack_cfg.label,
        phrase=snack_cfg.phrase,
        owner=child.id,
        caretaker=caregiver.id,
        carried_by=child.id,
        meters={"heat": 0.0, "safe": 1.0},
    ))
    cover = world.add(Entity(
        id="cover",
        type="cover",
        label=COVERS[params.cover].label,
        owner=caregiver.id,
    ))
    cover.carried_by = caregiver.id
    world.facts.update(child=child, caregiver=caregiver, snack=snack, cover=cover, snack_cfg=snack_cfg)
    return world


def advance(world: World) -> None:
    snack = world.get("snack")
    child = world.get(world.facts["child"].id)
    caregiver = world.get(world.facts["caregiver"].id)

    world.say(
        f"{child.id} and {caregiver.id} waited at {world.place.label} under a bright sky."
    )
    world.say(
        f"{child.id} liked the bright {world.facts['snack_cfg'].label}, but the warm air made {snack.pronoun('object')} feel less safe."
    )

    snack.meters["heat"] += 1.0
    if heat_risk(world, snack):
        world.say(
            f"{caregiver.id} glanced at the snack and worried it might spoil before the bus arrived."
        )
        flashback(world, caregiver, child, snack)
        cover = world.get("cover")
        cover_def = COVERS[cover.id]
        if "heat" in cover_def.protects:
            snack.meters["heat"] = 0.0
            snack.meters["safe"] = 1.0
            world.say(
                f"{caregiver.id} smiled, opened {cover_def.label}, and helped {child.id} tuck the snack inside."
            )
            world.say(
                f"Then they sat together on the bench, and the bright snack stayed fresh while they waited."
            )
            world.facts["resolved"] = True
            world.facts["cover_def"] = cover_def
        else:
            raise StoryError("No sensible cover can keep the snack from spoiling.")
    else:
        world.say(f"The snack stayed fine while they listened for the bus.")
        world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    child = world.facts["child"]
    caregiver = world.facts["caregiver"]
    snack_cfg = world.facts["snack_cfg"]
    snack = world.facts["snack"]

    world.say(
        f"{child.id} had brought {snack_cfg.phrase} for the ride."
    )
    world.say(
        f"{caregiver.id} had packed it carefully, because bright snacks could spoil in warm weather."
    )
    world.para()
    advance(world)
    world.para()
    world.say(
        f"When the bus finally rolled up, {child.id} climbed aboard with a cool snack and a calmer smile."
    )
    return world


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for snack_id in SNACKS:
        for cover_id in COVERS:
            out.append(("bus_stop", snack_id, cover_id))
    return out


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("waiting", "bus_stop"))
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("bright", sid))
        lines.append(asp.fact("heat_sensitive", sid))
    for cid, cover in COVERS.items():
        lines.append(asp.fact("cover", cid))
        for p in sorted(cover.protects):
            lines.append(asp.fact("protects", cid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show risky/1.\n#show fix/2."))
    risky = sorted(set(asp.atoms(model, "risky")))
    fixes = sorted(set(asp.atoms(model, "fix")))
    return risky + fixes


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show risky/1.\n#show fix/2."))
    risky = set(asp.atoms(model, "risky"))
    fixes = set(asp.atoms(model, "fix"))
    py_risky = {("fruit_cup",), ("yogurt",), ("sandwich",)}
    py_fixes = {
        ("fruit_cup", "lunch_bag"),
        ("fruit_cup", "thermos_pack"),
        ("yogurt", "lunch_bag"),
        ("yogurt", "thermos_pack"),
        ("sandwich", "lunch_bag"),
        ("sandwich", "thermos_pack"),
    }
    if risky == py_risky and fixes == py_fixes:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH.")
    print("risky:", risky, "expected:", py_risky)
    print("fixes:", fixes, "expected:", py_fixes)
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story set at a bus stop that includes the words "bright" and "spoil".',
        f"Tell a gentle story about {f['child'].id} and {f['caregiver'].id} waiting at the bus stop with {f['snack_cfg'].phrase}.",
        f"Write a simple story where a bright snack might spoil, then a caregiver remembers something in a flashback and helps.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    snack = f["snack"]
    cover = f["cover"]
    return [
        QAItem(
            question=f"Where were {child.id} and {caregiver.id} waiting?",
            answer=f"They were waiting at the bus stop.",
        ),
        QAItem(
            question=f"What bright thing might have spoiled?",
            answer=f"The bright {snack.label} might have spoiled in the warm air.",
        ),
        QAItem(
            question=f"What did {caregiver.id} do after the flashback?",
            answer=f"{caregiver.id} used {cover.label} to keep the snack cool and safe.",
        ),
        QAItem(
            question="Why did the caregiver remember another bus stop wait?",
            answer="The caregiver remembered that a snack had spoiled before, so this time they wanted to protect it sooner.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bus stop?",
            answer="A bus stop is a place where people wait for a bus to come and pick them up.",
        ),
        QAItem(
            question="What does spoiled mean when talking about food?",
            answer="Spoiled food has gone bad and is no longer nice to eat.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story briefly remembers something that happened earlier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  flashback_used={world.flashback_used}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "bus_stop":
        raise StoryError("This world only supports the bus stop setting.")
    snack = args.snack or rng.choice(list(SNACKS))
    cover = args.cover or rng.choice(list(COVERS))
    child = args.child or rng.choice(CHILD_NAMES)
    caregiver = args.caregiver or rng.choice(CARE_NAMES)
    child_type = args.child_type or ("girl" if child in {"Maya", "Lina", "Nora", "Ava"} else "boy")
    caregiver_type = args.caregiver_type or ("mother" if caregiver in {"Mom", "Grandma", "Aunt Jo"} else "father")
    return StoryParams(
        place="bus_stop",
        child=child,
        child_type=child_type,
        caregiver=caregiver,
        caregiver_type=caregiver_type,
        snack=snack,
        cover=cover,
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life bus stop story world with a flashback.")
    ap.add_argument("--place", choices=["bus_stop"], default="bus_stop")
    ap.add_argument("--child", choices=CHILD_NAMES)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=CARE_NAMES)
    ap.add_argument("--caregiver-type", choices=["mother", "father"])
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--cover", choices=COVERS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show risky/1.\n#show fix/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for snack_id in SNACKS:
            for cover_id in COVERS:
                params = StoryParams(
                    place="bus_stop",
                    child="Maya",
                    child_type="girl",
                    caregiver="Mom",
                    caregiver_type="mother",
                    snack=snack_id,
                    cover=cover_id,
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            sample.params.seed = base_seed + i
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
