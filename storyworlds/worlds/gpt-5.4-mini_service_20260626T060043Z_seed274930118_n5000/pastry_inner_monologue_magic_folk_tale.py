#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pastry_inner_monologue_magic_folk_tale.py
======================================================================================================================

A small folk-tale story world about pastry, a little bit of magic, and a
hero's inner monologue.

Seed premise:
---
A young baker makes a special pastry for the village fair. The pastry keeps
spoiling, and the baker worries it will never be ready. A magical helper offers
a simple charm and a quieter way to think. The baker listens inwardly, calms
down, fixes the pastry, and brings it to the fair.

This file models the story as a tiny stateful simulation:
- physical meters: warmth, crispness, freshness, sweetness, dust
- emotional memes: worry, hope, courage, relief, pride

The narration is generated from the evolving world state, not from a frozen
template.
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
    owner: Optional[str] = None
    maker: Optional[str] = None
    magical: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "baker"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    name: str
    indoors: bool = False
    supports: set[str] = field(default_factory=set)


@dataclass
class PastryKind:
    id: str
    label: str
    phrase: str
    warmth_needed: str
    crispness_needed: str
    spoils_with: str
    spoil_meter: str
    flavor: str
    place_tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    effect: str
    line: str
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.active_charm: Optional[Charm] = None

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
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.active_charm = self.active_charm
        return w


@dataclass
class StoryParams:
    place: str
    pastry: str
    hero_name: str
    hero_type: str
    helper_name: str
    seed: Optional[int] = None


PLACES = {
    "bakery": Place(name="the village bakery", indoors=True, supports={"knead", "bake", "cool", "dust"}),
    "cottage": Place(name="the warm cottage kitchen", indoors=True, supports={"knead", "bake", "cool", "dust"}),
    "market": Place(name="the market square", indoors=False, supports={"carry", "dust", "magic"}),
}

PASTRIES = {
    "bun": PastryKind(
        id="bun",
        label="sweet bun",
        phrase="a sweet bun with a golden crust",
        warmth_needed="warm",
        crispness_needed="crispy",
        spoils_with="soggy",
        spoil_meter="sogginess",
        flavor="honey",
        place_tags={"knead", "bake", "cool"},
    ),
    "pie": PastryKind(
        id="pie",
        label="berry pie",
        phrase="a berry pie with a shiny top",
        warmth_needed="warm",
        crispness_needed="firm",
        spoils_with="soft",
        spoil_meter="softness",
        flavor="berry",
        place_tags={"knead", "bake", "cool"},
    ),
    "turnover": PastryKind(
        id="turnover",
        label="apple turnover",
        phrase="an apple turnover folded like a little moon",
        warmth_needed="warm",
        crispness_needed="flaky",
        spoils_with="limp",
        spoil_meter="limpness",
        flavor="apple",
        place_tags={"knead", "bake", "cool"},
    ),
}

CHARMS = {
    "whisper": Charm(
        id="whisper",
        label="whispering charm",
        effect="calm",
        line="Listen to the quiet inside you, and let the pastry rest.",
        helps={"worry", "rush"},
    ),
    "spark": Charm(
        id="spark",
        label="sparkle charm",
        effect="shine",
        line="A small spark can wake the crust without burning the heart.",
        helps={"worry", "fade"},
    ),
}

GIRL_NAMES = ["Mira", "Nina", "Elsa", "Lina", "Tilda", "Rose", "Anya"]
BOY_NAMES = ["Otto", "Pavel", "Rian", "Bram", "Sven", "Tomas"]
HELPER_NAMES = ["Hazel", "Moss", "Iris", "Rowan", "Wren"]


def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _bump_meter(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amt


def _bump_mem(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amt


def _clamp_nonnegative(e: Entity, key: str) -> None:
    if e.meters.get(key, 0.0) < 0:
        e.meters[key] = 0.0


def introduce(world: World, hero: Entity, pastry: Entity) -> None:
    world.say(
        f"{hero.name_or_label()} was a little {hero.type} baker who loved the smell of "
        f"butter and the shine of a fresh crust."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had made {hero.pronoun('possessive')} {pastry.label} "
        f"for the village fair."
    )


def setup_state(world: World, hero: Entity, pastry: Entity) -> None:
    _bump_meter(pastry, "warmth", 1.5)
    _bump_meter(pastry, "crispness", 0.5)
    _bump_meter(pastry, "freshness", 1.5)
    _bump_mem(hero, "hope", 0.5)
    _bump_mem(hero, "worry", 0.5)


def spoil_if_unset(world: World, hero: Entity, pastry: Entity, kind: PastryKind) -> None:
    if _meter(pastry, "freshness") < THRESHOLD:
        _bump_meter(pastry, kind.spoil_meter, 1.0)
        _bump_mem(hero, "worry", 1.0)
        world.say(
            f"But the {pastry.label} did not like the hot air. It began to grow {kind.spoils_with}."
        )


def inner_monologue(world: World, hero: Entity, pastry: Entity) -> None:
    hero.memes["inner_voice"] = hero.memes.get("inner_voice", 0.0) + 1
    worry = _mem(hero, "worry")
    if worry >= THRESHOLD:
        world.say(
            f"In {hero.pronoun('possessive')} own mind, {hero.name_or_label()} whispered, "
            f'"If I hurry, I may only make it worse."'
        )
        world.say(
            f"{hero.pronoun().capitalize()} took a slow breath and looked again at the pastry."
        )


def apply_charm(world: World, helper: Entity, hero: Entity, charm: Charm) -> None:
    world.active_charm = charm
    _bump_mem(hero, "hope", 1.0)
    world.say(
        f"Then {helper.name_or_label()} came by with a {charm.label} and said, "
        f'"{charm.line}"'
    )


def calm_turn(world: World, hero: Entity, pastry: Entity) -> None:
    if world.active_charm and world.active_charm.effect == "calm":
        if _mem(hero, "worry") >= THRESHOLD:
            hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0.0) - 1.0)
            _bump_mem(hero, "courage", 1.0)
            world.say(
                f"The quiet words settled in {hero.pronoun('possessive')} chest like a soft hand."
            )
            world.say(
                f"{hero.name_or_label()} understood that the pastry needed patient care, not panic."
            )


def fix_pastry(world: World, hero: Entity, pastry: Entity, kind: PastryKind) -> None:
    if _mem(hero, "courage") >= THRESHOLD:
        pastry.meters[kind.spoil_meter] = 0.0
        pastry.meters["freshness"] = max(pastry.meters.get("freshness", 0.0), 2.0)
        pastry.meters["crispness"] = max(pastry.meters.get("crispness", 0.0), 2.0)
        _bump_mem(hero, "pride", 1.0)
        _bump_mem(hero, "relief", 1.0)
        world.say(
            f"{hero.name_or_label()} brushed the tray clean, let the {pastry.label} cool, "
            f"and gave it one careful finish."
        )
        world.say(
            f"The crust turned crisp again, and the sweet smell rose up like a tiny blessing."
        )


def depart_for_fair(world: World, hero: Entity, pastry: Entity) -> None:
    world.para()
    world.say(
        f"At last, {hero.name_or_label()} carried the {pastry.label} to the fair."
    )
    world.say(
        f"It came on a wooden tray, golden and neat, while {hero.pronoun('subject')} walked "
        f"with a lighter step."
    )
    world.say(
        f"People smiled at the bright pastry, and {hero.name_or_label()} smiled too, because the quiet voice had helped."
    )


def tell(place: Place, pastry_kind: PastryKind, hero_name: str, hero_type: str, helper_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type="spirit", label=helper_name, magical=True))
    pastry = world.add(Entity(id="pastry", type="pastry", label=pastry_kind.label, phrase=pastry_kind.phrase, owner=hero.id))

    introduce(world, hero, pastry)
    setup_state(world, hero, pastry)

    world.para()
    world.say(
        f"The day was busy at {place.name}, and the oven heat made the kitchen smell sweet and sharp."
    )
    spoil_if_unset(world, hero, pastry, pastry_kind)
    inner_monologue(world, hero, pastry)
    apply_charm(world, helper, hero, CHARMS["whisper"])
    calm_turn(world, hero, pastry)
    fix_pastry(world, hero, pastry, pastry_kind)
    depart_for_fair(world, hero, pastry)

    world.facts.update(
        hero=hero,
        helper=helper,
        pastry=pastry,
        pastry_kind=pastry_kind,
        place=place,
        charm=world.active_charm,
        resolved=True,
    )
    return world


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for pastry_id, kind in PASTRIES.items():
            if {"bake", "cool"}.issubset(place.supports) and kind.flavor in {"honey", "berry", "apple"}:
                out.append((place_id, pastry_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world about pastry and inner magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--pastry", choices=PASTRIES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.pastry is None or c[1] == args.pastry)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, pastry = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, pastry=pastry, hero_name=name, hero_type=gender, helper_name=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a child about {f["hero"].label} and a magical pastry.',
        f"Tell a gentle story where {f['hero'].label} worries about a {f['pastry_kind'].label} but listens to an inner voice and a magical helper.",
        f'Write a simple story that includes a pastry, a quiet thought, and a helpful charm at {f["place"].name}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    pastry = f["pastry"]
    kind = f["pastry_kind"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who made the {kind.label} for the fair?",
            answer=f"{hero.label} made the {pastry.label} for the village fair.",
        ),
        QAItem(
            question=f"What did {hero.label} worry about when the pastry began to spoil?",
            answer=f"{hero.label} worried that the {pastry.label} would turn {kind.spoils_with} before the fair.",
        ),
        QAItem(
            question=f"What helped {hero.label} calm down and fix the pastry?",
            answer=f"The {f['charm'].label} from {helper.label} helped {hero.label} listen inwardly and take careful steps.",
        ),
        QAItem(
            question=f"Where did the story happen?",
            answer=f"It happened at {place.name}, where the oven heat and the fair-day bustle made everything feel busy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is pastry?",
            answer="Pastry is a soft dough or baked food made with flour and fat, often turned into buns, pies, or turnovers.",
        ),
        QAItem(
            question="What does it mean to listen to your inner voice?",
            answer="It means to think quietly inside yourself, notice your feelings, and choose carefully instead of rushing.",
        ),
        QAItem(
            question="What is a charm in a folk tale?",
            answer="A charm is a little bit of magic that can help, protect, or change a situation in a story.",
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
    lines.append("== (3) World knowledge ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.magical:
            bits.append("magical=True")
        lines.append(f"  {e.id:7} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place_ok(P) :- place(P).
pastry_ok(X) :- pastry(X).
valid_story(P, X) :- place_ok(P), pastry_ok(X), supports(P, bake), supports(P, cool).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for s in sorted(p.supports):
            lines.append(asp.fact("supports", pid, s))
    for xid, x in PASTRIES.items():
        lines.append(asp.fact("pastry", xid))
        lines.append(asp.fact("flavor", xid, x.flavor))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
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


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], PASTRIES[params.pastry], params.hero_name, params.hero_type, params.helper_name)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for a, b in combos:
            print(f"  {a:8} {b}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="bakery", pastry="bun", hero_name="Mira", hero_type="girl", helper_name="Hazel"),
            StoryParams(place="cottage", pastry="pie", hero_name="Otto", hero_type="boy", helper_name="Rowan"),
            StoryParams(place="market", pastry="turnover", hero_name="Lina", hero_type="girl", helper_name="Iris"),
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
