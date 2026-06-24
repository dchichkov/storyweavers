#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/alcoholic_gentle_teamwork_suspense_fable.py
============================================================================================================================

A small fable-like storyworld about gentle teamwork under suspenseful pressure.

Seed tale idea:
---
In a quiet meadow, a squirrel, a rabbit, and a badger were asked to carry a bottle of
alcoholic plum cordial to the village feast. The path was narrow, the bottle was fragile,
and a small crack in the bridge made everyone nervous. The animals had to move carefully,
listen to one another, and work together so the cordial would arrive safely.

World model:
---
This world tracks:
- physical state: balance, distance, slippery ground, fragility, and whether a cargo item is safe
- emotional state: calm, worry, trust, and relief
- a teamwork beat: several helpers can steady the cargo together
- a suspense beat: the cargo can teeter when the path becomes risky, forcing cooperation

The prose is written as a gentle fable with a clear opening, middle tension, and a closing
image proving what changed.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "sister", "woman"}
        male = {"boy", "father", "brother", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    terrain: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    type: str
    fragility: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.path_risk: float = 0.0
        self.helpers_ready: int = 0

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.path_risk = self.path_risk
        clone.helpers_ready = self.helpers_ready
        return clone

    def cargo(self) -> Entity:
        for e in self.entities.values():
            if e.type == "cargo":
                return e
        raise KeyError("no cargo")

    def helpers(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    place: str
    cargo: str
    aid: str
    name1: str
    name2: str
    name3: str
    seed: Optional[int] = None


SETTINGS = {
    "meadow": Setting(place="the meadow path", terrain="grass", affords={"carrying"}),
    "bridge": Setting(place="the wooden bridge", terrain="wood", affords={"carrying"}),
    "grove": Setting(place="the grove road", terrain="roots", affords={"carrying"}),
}

CARGOS = {
    "cordial": Cargo(
        id="cordial",
        label="bottle",
        phrase="a bottle of alcoholic plum cordial",
        type="cargo",
        fragility="fragile",
        risk="spill",
        tags={"alcoholic", "cordial", "bottle"},
    ),
    "cider": Cargo(
        id="cider",
        label="jug",
        phrase="a jug of alcoholic apple cider",
        type="cargo",
        fragility="fragile",
        risk="slip",
        tags={"alcoholic", "cider", "jug"},
    ),
    "ink": Cargo(
        id="ink",
        label="jar",
        phrase="a jar of dark alcoholic cooking ink",
        type="cargo",
        fragility="fragile",
        risk="spill",
        tags={"alcoholic", "ink", "jar"},
    ),
}

AIDS = {
    "hands": Aid(
        id="hands",
        label="steady hands",
        prep="hold the cargo together with steady hands",
        tail="kept their hands under the cargo until the danger was past",
        helps={"spill", "slip"},
        plural=True,
    ),
    "rope": Aid(
        id="rope",
        label="a soft rope sling",
        prep="make a soft rope sling",
        tail="used the sling to balance the load",
        helps={"spill", "slip"},
    ),
    "lantern": Aid(
        id="lantern",
        label="a lantern",
        prep="carry a lantern first",
        tail="walked by the lantern's glow and watched each step",
        helps={"slip"},
    ),
}

NAMES = ["Pip", "Mina", "Tob", "Ria", "Hale", "Nell", "Bram", "Lila"]
TRAITS = ["gentle", "patient", "careful", "kind", "quiet", "steady"]


def cargo_at_risk(setting: Setting, cargo: Cargo) -> bool:
    return setting.place in {"the bridge", "the grove road", "the meadow path"}


def select_aid(setting: Setting, cargo: Cargo) -> Optional[Aid]:
    for aid in AIDS.values():
        if cargo.risk in aid.helps:
            return aid
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for cargo_id, cargo in CARGOS.items():
            if cargo_at_risk(setting, cargo) and select_aid(setting, cargo):
                for aid_id in AIDS:
                    if cargo.risk in AIDS[aid_id].helps:
                        out.append((place, cargo_id, aid_id))
    return sorted(set(out))


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    cargo = CARGOS[params.cargo]
    aid = AIDS[params.aid]
    world = World(setting)

    a = world.add(Entity(id=params.name1, kind="character", type="squirrel", traits=["gentle", "small"]))
    b = world.add(Entity(id=params.name2, kind="character", type="rabbit", traits=["gentle", "swift"]))
    c = world.add(Entity(id=params.name3, kind="character", type="badger", traits=["gentle", "strong"]))
    cargo_ent = world.add(Entity(
        id="cargo",
        kind="thing",
        type="cargo",
        label=cargo.label,
        phrase=cargo.phrase,
        owner=a.id,
        caretaker=c.id,
        carried_by=a.id,
        plural=False,
    ))
    world.facts.update(hero=a, helper1=b, helper2=c, cargo=cargo_ent, aid=aid, cargo_cfg=cargo)
    return world


def predict_safety(world: World, cargo: Cargo, aid: Aid) -> dict:
    sim = world.copy()
    sim.path_risk = 1.0
    helpers = sim.helpers()
    for h in helpers:
        h.memes["worry"] = h.memes.get("worry", 0) + 0.5
    safe = cargo.risk in aid.helps
    return {"safe": safe, "helpers": len(helpers)}


def tell(world: World) -> None:
    hero = world.facts["hero"]
    h1 = world.facts["helper1"]
    h2 = world.facts["helper2"]
    cargo = world.facts["cargo_cfg"]
    aid = world.facts["aid"]

    world.say(
        f"In a calm meadow, {hero.id}, {h1.id}, and {h2.id} found {cargo.phrase} waiting for the village feast."
    )
    world.say(
        f"They were a gentle little team, and each one knew that careful work can make a hard job feel light."
    )
    world.para()

    world.say(
        f"But the road to the village crossed {world.setting.place}, where one loose board and a slick patch could make the load {cargo.risk}."
    )
    world.path_risk = 1.0
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    h1.memes["worry"] = h1.memes.get("worry", 0) + 1
    h2.memes["worry"] = h2.memes.get("worry", 0) + 1
    world.say(
        f"{hero.id} slowed down and said they should not rush, because even a small wobble could trouble {cargo.label}."
    )
    world.say(
        f"{h1.id} peered ahead, and {h2.id} held the back end still, while everyone listened for the safest step."
    )

    world.para()
    world.say(
        f"Then {h2.id} suggested a clever plan: {aid.prep}."
    )
    world.helpers_ready = 3
    cargo_ent = world.get("cargo")
    cargo_ent.meters["balanced"] = 1
    cargo_ent.memes["hope"] = cargo_ent.memes.get("hope", 0) + 1
    world.say(
        f"They agreed at once, because teamwork is often the quiet answer when suspense hangs in the air."
    )
    world.say(
        f"So {hero.id} and {h1.id} steadied the front, {h2.id} guided the rear, and together they moved as slowly as a song."
    )

    world.para()
    safe_report = predict_safety(world, cargo, aid)
    if safe_report["safe"]:
        cargo_ent.meters["safe"] = 1
        cargo_ent.memes["relief"] = 1
        hero.memes["relief"] = hero.memes.get("relief", 0) + 1
        h1.memes["relief"] = h1.memes.get("relief", 0) + 1
        h2.memes["relief"] = h2.memes.get("relief", 0) + 1
        world.say(
            f"The risky board gave a tiny creak, but the load did not tilt, because three careful helpers were stronger than one scared moment."
        )
        world.say(
            f"By sunset they reached the village with {cargo.phrase} still safe, and the feast began with smiles instead of worry."
        )
        world.say(
            f"After that, the animals remembered that gentle teamwork can turn suspense into a happy ending."
        )
    else:
        raise StoryError("No reasonable ending: the chosen aid does not truly keep the cargo safe.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    cargo = f["cargo_cfg"]
    aid = f["aid"]
    return [
        f'Write a short fable for children that includes the word "alcoholic" and the word "gentle".',
        f"Tell a suspenseful but gentle story about {hero.id} and two friends carrying {cargo.phrase} safely together.",
        f"Write a teamwork fable where a small animal group solves a risky path by using {aid.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, h1, h2 = f["hero"], f["helper1"], f["helper2"]
    cargo = f["cargo_cfg"]
    aid = f["aid"]
    return [
        QAItem(
            question=f"Who worked together in the story?",
            answer=f"{hero.id}, {h1.id}, and {h2.id} worked together to carry {cargo.phrase} safely.",
        ),
        QAItem(
            question=f"What made the trip feel suspenseful?",
            answer=f"The trip felt suspenseful because the path by {world.setting.place} could make {cargo.label} {cargo.risk}.",
        ),
        QAItem(
            question=f"What plan helped the friends keep going?",
            answer=f"They used {aid.label} and moved carefully as one gentle team.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {cargo.phrase} arriving safely at the village feast.",
        ),
    ]


KNOWLEDGE = {
    "alcoholic": [
        (
            "What does alcoholic mean?",
            "Alcoholic means something has alcohol in it, which is a substance found in some drinks made for grown-ups.",
        )
    ],
    "gentle": [
        (
            "What does gentle mean?",
            "Gentle means soft, careful, and kind, like moving slowly so you do not hurt anyone or break anything.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people work together and help one another so a job is easier and goes better.",
        )
    ],
    "suspense": [
        (
            "What is suspense?",
            "Suspense is the feeling of waiting nervously to see what will happen next.",
        )
    ],
    "bridge": [
        (
            "Why can a bridge be tricky to cross?",
            "A bridge can be tricky because boards may wobble, and people must watch their steps carefully.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"alcoholic", "gentle", "teamwork", "suspense", "bridge"}
    out: list[QAItem] = []
    for tag in tags:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE.get(tag, []))
    return out


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  path_risk={world.path_risk}")
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(C, P) :- cargo(C), setting(S), place_has_risk(S), cargo_type(P), cargo_risk(P, R), risk_path(S, R).
good_aid(A, P) :- aid(A), cargo_type(P), cargo_risk(P, R), helps(A, R).
valid_story(S, C, A) :- setting(S), cargo(C), aid(A), at_risk(C, C), good_aid(A, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.place in {"the bridge", "the grove road"}:
            lines.append(asp.fact("place_has_risk", sid))
        for aff in s.affords:
            lines.append(asp.fact("affords", sid, aff))
    for cid, c in CARGOS.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("cargo_type", cid))
        lines.append(asp.fact("cargo_risk", cid, c.risk))
    for aid in AIDS.values():
        lines.append(asp.fact("aid", aid.id))
        for h in aid.helps:
            lines.append(asp.fact("helps", aid.id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


CURATED = [
    StoryParams(place="bridge", cargo="cordial", aid="hands", name1="Pip", name2="Mina", name3="Bram"),
    StoryParams(place="grove", cargo="cider", aid="rope", name1="Lila", name2="Tob", name3="Nell"),
    StoryParams(place="meadow", cargo="ink", aid="lantern", name1="Ria", name2="Hale", name3="Bram"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle teamwork fable with suspense and an alcoholic cargo.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--name3")
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.cargo:
        combos = [c for c in combos if c[1] == args.cargo]
    if args.aid:
        combos = [c for c in combos if c[2] == args.aid]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, cargo, aid = rng.choice(combos)
    return StoryParams(
        place=place,
        cargo=cargo,
        aid=aid,
        name1=args.name1 or rng.choice(NAMES),
        name2=args.name2 or rng.choice([n for n in NAMES if n != args.name1]),
        name3=args.name3 or rng.choice([n for n in NAMES if n not in {args.name1, args.name2}]),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, cargo, aid) combos:\n")
        for t in triples:
            print(f"  {t[0]:8} {t[1]:8} {t[2]:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name1}, {p.name2}, {p.name3}: {p.cargo} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
