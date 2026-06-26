#!/usr/bin/env python3
"""
storyworlds/worlds/willing_wad_sharing_myth.py
==============================================

A tiny mythic story world about willing sharing and a precious wad.

Premise:
- A small community has a scarce wad of grain, clay, or honey.
- The hero is asked to share it during a hard moment.
- If the hero is willing, the wad is divided with care and a blessing follows.
- If the hero refuses, the community stays hungry or uneasy, so the script rejects
  that setup as unreasonable for this world.

The story is built from a live state model with physical meters and emotional
memes, so the prose follows what the world does rather than repeating a frozen
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
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mass": 0.0, "shared": 0.0, "scarce": 0.0}
        if not self.memes:
            self.memes = {"willing": 0.0, "hope": 0.0, "hunger": 0.0, "joy": 0.0, "trust": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    kind: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class WadKind:
    id: str
    label: str
    phrase: str
    material: str
    weight: str
    share_effect: str
    bless: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    wad: str
    name: str
    title: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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


PLACES = {
    "hall": Place("hall", "the old hall", "hall", "solemn", affords={"share"}),
    "well": Place("well", "the stone well", "well", "cool", affords={"share"}),
    "grove": Place("grove", "the moonlit grove", "grove", "soft", affords={"share"}),
}

WADS = {
    "grain": WadKind(
        id="grain",
        label="wad of grain",
        phrase="a warm wad of grain",
        material="grain",
        weight="small",
        share_effect="the porridge could be cooked for many bowls",
        bless="the children would not sleep hungry",
        tags={"grain", "hunger"},
    ),
    "honey": WadKind(
        id="honey",
        label="wad of honey",
        phrase="a sticky wad of honey",
        material="honey",
        weight="small",
        share_effect="the cakes could be sweetened for the whole table",
        bless="the feast would feel bright again",
        tags={"honey", "sweet"},
    ),
    "clay": WadKind(
        id="clay",
        label="wad of clay",
        phrase="a cool wad of clay",
        material="clay",
        weight="small",
        share_effect="the potter could shape many cups",
        bless="the village could drink with fuller hands",
        tags={"clay", "craft"},
    ),
}

NAMES = ["Ari", "Mira", "Soren", "Tala", "Niko", "Lina"]
TITLES = ["guardian", "mother", "father", "sister", "brother", "keeper"]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, w) for p in PLACES for w in WADS if "share" in PLACES[p].affords]


class Artifact:
    def __init__(self, wad: WadKind) -> None:
        self.kind = wad
        self.entity = Entity(
            id="wad",
            type=wad.id,
            label=wad.label,
            phrase=wad.phrase,
            meters={"mass": 1.0, "shared": 0.0, "scarce": 1.0},
            memes={"willing": 0.0, "hope": 0.0, "hunger": 0.0, "joy": 0.0, "trust": 0.0},
        )


def split_wad(world: World, hero: Entity, wad: Entity) -> None:
    wad.meters["shared"] = 1.0
    wad.meters["scarce"] = 0.0
    hero.memes["willing"] += 1.0
    hero.memes["joy"] += 1.0
    hero.memes["trust"] += 1.0
    if wad.type == "grain":
        hero.memes["hope"] += 1.0
    elif wad.type == "honey":
        hero.memes["joy"] += 0.5
    else:
        hero.memes["trust"] += 0.5


def reasonableness_gate(place: Place, wad: WadKind) -> None:
    if "share" not in place.affords:
        raise StoryError(f"(No story: {place.label} is not a place where this mythic sharing can happen.)")
    if wad.id not in WADS:
        raise StoryError("(No story: the requested wad is unknown.)")


def setup_story(world: World, hero_name: str, title: str, wad_kind: WadKind) -> None:
    hero = world.add(Entity(id=hero_name, kind="character", type=title, label=title))
    crowd = world.add(Entity(id="crowd", kind="character", type="villagers", label="the villagers", plural=True))
    wad = world.add(Entity(
        id="wad",
        type=wad_kind.id,
        label=wad_kind.label,
        phrase=wad_kind.phrase,
        owner=hero.id,
        caretaker=crowd.id,
        meters={"mass": 1.0, "shared": 0.0, "scarce": 1.0},
        memes={"willing": 0.0, "hope": 0.0, "hunger": 1.0, "joy": 0.0, "trust": 0.0},
    ))
    world.facts.update(hero=hero, crowd=crowd, wad=wad, wad_kind=wad_kind)


def tell(world: World) -> None:
    hero: Entity = world.facts["hero"]
    crowd: Entity = world.facts["crowd"]
    wad: Entity = world.facts["wad"]
    wad_kind: WadKind = world.facts["wad_kind"]

    world.say(
        f"In {world.place.label}, {hero.id} was a gentle {hero.type} known for a steady hand and a willing heart."
    )
    world.say(
        f"{hero.id} kept {hero.pronoun('possessive')} {wad.label}, and the little bundle mattered because "
        f"{wad_kind.share_effect}."
    )

    world.para()
    world.say(
        f"But one hard evening, the villagers gathered with empty bowls and quiet faces."
    )
    world.say(
        f"They looked at {wad.label}, then at {hero.id}, because there was almost nothing else left to give."
    )

    world.para()
    hero.memes["hunger"] += 0.0
    hero.memes["willing"] += 1.0
    world.say(
        f"{hero.id} stayed still for a breath, and then {hero.pronoun()} was willing to share."
    )
    split_wad(world, hero, wad)
    world.say(
        f"{hero.id} divided the {wad.label} carefully, and {wad_kind.bless}."
    )
    crowd.memes["trust"] += 1.0
    crowd.memes["joy"] += 1.0
    world.say(
        f"The villagers ate together, and their faces softened like dawn over water."
    )
    world.say(
        f"At the end, {hero.id} held only a small crumb of the old fear, while the {wad.label} had become a blessing for everyone."
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    wad_kind: WadKind = f["wad_kind"]
    return [
        f'Write a short myth for a child about {hero.id}, a willing heart, and a {wad_kind.label}.',
        f'Tell a simple legend where someone is willing to share a {wad_kind.label} and the whole village changes.',
        f'Write a gentle mythic story that includes the word "willing" and the noun "{wad_kind.label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    crowd: Entity = f["crowd"]
    wad: Entity = f["wad"]
    wad_kind: WadKind = f["wad_kind"]
    return [
        QAItem(
            question=f"Who was willing to share the {wad.label}?",
            answer=f"{hero.id} was willing to share the {wad.label} with the villagers.",
        ),
        QAItem(
            question=f"What did the villagers need before {hero.id} shared the {wad.label}?",
            answer="They had empty bowls and quiet faces, so they were waiting for help and food.",
        ),
        QAItem(
            question=f"What changed after the {wad.label} was divided?",
            answer=f"The villagers ate together, their trust grew, and the {wad.label} became a blessing instead of something held alone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    wad_kind: WadKind = f["wad_kind"]
    qa = [
        QAItem(
            question="What does it mean to share something?",
            answer="To share means to let other people use or enjoy part of it too.",
        ),
    ]
    if wad_kind.id == "grain":
        qa.append(QAItem(
            question="What can grain be used for?",
            answer="Grain can be ground or cooked into food like bread or porridge.",
        ))
    elif wad_kind.id == "honey":
        qa.append(QAItem(
            question="Why do people use honey in food?",
            answer="People use honey to make food sweet.",
        ))
    else:
        qa.append(QAItem(
            question="What can clay be used for?",
            answer="Clay can be shaped into bowls, cups, and pots before it hardens.",
        ))
    return qa


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,W) :- place(P), wad(W), affords(P,share).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for wid in WADS:
        lines.append(asp.fact("wad", wid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    if a - b:
        print(" only in ASP:", sorted(a - b))
    if b - a:
        print(" only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world about willing sharing and a precious wad.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--wad", choices=WADS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--title", choices=TITLES)
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
    if args.wad:
        combos = [c for c in combos if c[1] == args.wad]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, wad = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    title = args.title or rng.choice(TITLES)
    return StoryParams(place=place, wad=wad, name=name, title=title)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(PLACES[params.place], WADS[params.wad])
    world = World(PLACES[params.place])
    world.facts["wad_kind"] = WADS[params.wad]
    setup_story(world, params.name, params.title, WADS[params.wad])
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


CURATED = [
    StoryParams(place="hall", wad="grain", name="Ari", title="guardian"),
    StoryParams(place="well", wad="honey", name="Mira", title="keeper"),
    StoryParams(place="grove", wad="clay", name="Tala", title="sister"),
]


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
        for p, w in combos:
            print(f"  {p} {w}")
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
            header = f"### {p.name}: {p.wad} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
