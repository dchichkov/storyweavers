#!/usr/bin/env python3
"""
storyworlds/worlds/segment_reconciliation_fairy_tale.py
======================================================

A small fairy-tale story world about a shared segment, a quarrel, and a
reconciliation that makes the kingdom whole again.

Seed premise:
- Two children discover a magical segment of a fairy bridge.
- Each believes the segment belongs to them alone.
- A small helper encourages apology and sharing.
- Reconciliation restores both the bridge and their bond.

The domain is intentionally tiny and classical: one scene, one dispute, one
turn, and one ending image proving the change.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("brightness", "broken", "mended", "glow"):
            self.meters.setdefault(k, 0.0)
        for k in ("hurt", "pride", "care", "apology", "joy", "peace", "stubborn"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "sister"}
        male = {"boy", "prince", "king", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the moonlit grove"
    affords: set[str] = field(default_factory=lambda: {"find_segment", "quarrel", "reconcile"})


@dataclass
class Treasure:
    label: str
    phrase: str
    type: str
    is_segment: bool = True


@dataclass
class StoryParams:
    place: str
    hero: str
    sibling: str
    helper: str
    treasure: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        clone = World(copy.deepcopy(self.setting))
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("hero")
    b = world.get("sibling")
    seg = world.get("treasure")
    if a.memes["apology"] >= THRESHOLD and b.memes["apology"] >= THRESHOLD and seg.meters["mended"] < THRESHOLD:
        sig = ("reconcile",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        seg.meters["broken"] = 0.0
        seg.meters["mended"] = 1.0
        seg.meters["glow"] = 1.0
        a.memes["hurt"] = 0.0
        b.memes["hurt"] = 0.0
        a.memes["peace"] = 1.0
        b.memes["peace"] = 1.0
        a.memes["joy"] += 1.0
        b.memes["joy"] += 1.0
        out.append("__reconciled__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for sent in _r_reconcile(world):
            changed = True
            if sent != "__reconciled__":
                produced.append(sent)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def settle_story(world: World) -> None:
    hero = world.get("hero")
    sibling = world.get("sibling")
    treas = world.get("treasure")
    helper = world.get("helper")

    world.say(
        f"Long ago, in {world.setting.place}, there lived a little {hero.type} named {hero.id} and "
        f"its dear {sibling.type} named {sibling.id}."
    )
    world.say(
        f"They loved to wander where the moss was soft, because there they found {treas.phrase}, "
        f"the brightest {treas.label} in the kingdom."
    )

    world.para()
    treas.meters["brightness"] = 1.0
    hero.memes["joy"] += 1.0
    sibling.memes["joy"] += 1.0
    world.say(
        f"One evening they found a shining {treas.label}, and it was only a single segment of the old fairy bridge."
    )
    world.say(
        f"{hero.id} wanted to keep the segment. {sibling.id} wanted it too, for each thought the sparkle had chosen them alone."
    )

    world.para()
    hero.memes["stubborn"] += 1.0
    sibling.memes["stubborn"] += 1.0
    hero.memes["hurt"] += 1.0
    sibling.memes["hurt"] += 1.0
    treas.meters["broken"] = 1.0
    treas.meters["glow"] = 0.0
    world.say(
        f"Their voices grew sharp like thorns. They tugged the {treas.label} between them until the little segment bent and dimmed."
    )
    world.say(
        f"Then {helper.id}, a gentle {helper.type} from the lanes of dew, stepped forward and said, "
        f'"A treasure shared is a treasure that can shine twice."'
    )

    world.para()
    helper.memes["care"] += 1.0
    hero.memes["apology"] += 1.0
    sibling.memes["apology"] += 1.0
    world.say(
        f"{hero.id} lowered its head and said sorry. {sibling.id} looked at the broken segment, and its own eyes filled with tears."
    )
    world.say(
        f"One by one they apologized, and {helper.id} tied a silver thread around the crack so the segment could be mended."
    )
    propagate(world, narrate=False)
    world.say(
        f"At last they held the repaired {treas.label} together, and it lit up like a small moon."
    )
    world.say(
        f"{hero.id} and {sibling.id} walked home side by side, no longer divided, with the glowing segment resting safely between them."
    )

    world.facts.update(hero=hero, sibling=sibling, helper=helper, treasure=treas)


SETTINGS = {
    "grove": Setting(place="the moonlit grove"),
    "bridge": Setting(place="the old stone bridge"),
    "garden": Setting(place="the rose garden"),
}

TREASURES = {
    "segment": Treasure(
        label="segment",
        phrase="a magic segment of the fairy bridge",
        type="treasure",
        is_segment=True,
    ),
    "lantern": Treasure(
        label="lantern",
        phrase="a tiny lantern with a silver handle",
        type="treasure",
        is_segment=False,
    ),
}

CHAR_TYPES = {
    "girl": ["princess", "girl"],
    "boy": ["prince", "boy"],
    "helper": ["fairy", "elf", "mole"],
}

NAMES = {
    "hero": ["Lina", "Mira", "Nora", "Elsa", "Rosa"],
    "sibling": ["Tobin", "Finn", "Jules", "Pip", "Wren"],
    "helper": ["Iris", "Poppy", "Bramble", "Lumi", "Moss"],
}


def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p in SETTINGS for t in TREASURES if t == "segment"]


@dataclass
class StoryState:
    world: World


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale about a child who finds a "{f["treasure"].label}" and must reconcile after a quarrel.',
        f"Tell a short story in which {f['hero'].id} and {f['sibling'].id} argue over a segment, then make peace.",
        f"Write a gentle tale set in {world.setting.place} that ends with a repaired shared treasure and two friends smiling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, sibling, helper, treas = f["hero"], f["sibling"], f["helper"], f["treasure"]
    return [
        QAItem(
            question=f"Who found the {treas.label} in {world.setting.place}?",
            answer=f"{hero.id} and {sibling.id} found the {treas.label} together in {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {hero.id} and {sibling.id} start to quarrel?",
            answer=f"They both wanted to keep the shiny {treas.label} for themselves, so they tugged and argued over the little segment.",
        ),
        QAItem(
            question=f"How did they reconcile by the end?",
            answer=f"They both apologized, and {helper.id} helped mend the broken segment so they could hold it together again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does reconcile mean?",
            answer="To reconcile means to make peace again after a quarrel or hurt feelings.",
        ),
        QAItem(
            question="What is a segment?",
            answer="A segment is one piece of a larger whole.",
        ),
        QAItem(
            question="Why can a shared treasure be special in a fairy tale?",
            answer="A shared treasure can be special because it teaches kindness, fairness, and how people can care for one another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(place: str, treasure: str) -> str:
    return f"(No story: only the segment treasure is built for a reconciliation tale in {place}.)"


def build_story(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero_type = "princess"
    sibling_type = "prince"
    helper_type = "fairy"

    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=params.hero))
    sibling = world.add(Entity(id="sibling", kind="character", type=sibling_type, label=params.sibling))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=params.helper))
    treasure = world.add(Entity(
        id="treasure",
        kind="thing",
        type="treasure",
        label="segment",
        phrase="a magic segment of the fairy bridge",
    ))

    settle_story(world)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.treasure and args.treasure != "segment":
        raise StoryError(explain_rejection(args.place or "the grove", args.treasure))
    place = args.place or rng.choice(list(SETTINGS))
    treasure = args.treasure or "segment"
    if (place, treasure) not in valid_combos():
        raise StoryError(explain_rejection(place, treasure))
    return StoryParams(
        place=place,
        hero=args.hero or rng.choice(NAMES["hero"]),
        sibling=args.sibling or rng.choice(NAMES["sibling"]),
        helper=args.helper or rng.choice(NAMES["helper"]),
        treasure=treasure,
    )


ASP_RULES = r"""
% A treasure is segment-shaped in this world.
segment_treasure(T) :- treasure(T), is_segment(T).

% Reconciliation happens when both children apologize and the helper is kind.
reconciled(H, S, T) :- child(H), child(S), helper_ok(T),
                       apology(H), apology(S), shared(T).

valid(Place, Treasure) :- setting(Place), segment_treasure(Treasure), place_supports(Place, Treasure).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
        lines.append(asp.fact("place_supports", place, "segment"))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        if t.is_segment:
            lines.append(asp.fact("is_segment", tid))
        lines.append(asp.fact("shared", tid))
    lines.append(asp.fact("child", "hero"))
    lines.append(asp.fact("child", "sibling"))
    lines.append(asp.fact("helper_ok", "helper"))
    lines.append(asp.fact("apology", "hero"))
    lines.append(asp.fact("apology", "sibling"))
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
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale reconciliation story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--hero")
    ap.add_argument("--sibling")
    ap.add_argument("--helper")
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


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for place, treasure in combos:
            print(f"  {place:12} {treasure}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, treasure in valid_combos():
            params = StoryParams(
                place=place,
                hero="Lina",
                sibling="Tobin",
                helper="Iris",
                treasure=treasure,
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.hero} and {p.sibling} in {p.place} ({p.treasure})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
