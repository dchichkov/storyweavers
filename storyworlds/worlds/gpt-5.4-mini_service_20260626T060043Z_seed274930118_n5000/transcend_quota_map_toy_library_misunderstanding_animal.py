#!/usr/bin/env python3
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    species: str = "animal"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the toy library"
    affords: set[str] = field(default_factory=lambda: {"browse", "sort", "trade", "read"})


@dataclass
class MapItem:
    label: str
    phrase: str
    kind: str = "map"
    clue_kind: str = "route"
    leads_to: str = "the map shelf"


@dataclass
class Quota:
    label: str
    kind: str = "quota"
    limit: int = 3
    unit: str = "books"


@dataclass
class StoryParams:
    name: str
    species: str
    helper: str
    map_kind: str
    quota_kind: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


SETTING = Setting()

MAPS = {
    "map": MapItem(label="map", phrase="a bright paper map", clue_kind="route", leads_to="the map shelf"),
    "tide_map": MapItem(label="tide map", phrase="a tide map with shiny blue lines", clue_kind="route", leads_to="the back nook"),
    "sticker_map": MapItem(label="sticker map", phrase="a sticker map with paws and stars", clue_kind="route", leads_to="the reading rug"),
}

QUOTAS = {
    "quota": Quota(label="quota", limit=3, unit="books"),
    "book_quota": Quota(label="book quota", limit=2, unit="books"),
    "sticker_quota": Quota(label="sticker quota", limit=4, unit="stickers"),
}

ANIMAL_NAMES = ["Milo", "Pip", "Nina", "Tobi", "Luna", "Clover", "Bram", "Hazel"]
HELPERS = ["owl", "mouse", "fox", "rabbit", "cat"]


def reasonableness_gate(map_item: MapItem, quota: Quota) -> None:
    if "map" not in map_item.label and "map" not in map_item.phrase:
        raise StoryError("This world needs a map-like object so the misunderstanding has a clear clue.")
    if quota.limit < 1:
        raise StoryError("Quota must be at least 1 to create a meaningful limit.")


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "toy_library"), asp.fact("place", "toy_library")]
    for mid, m in MAPS.items():
        lines.append(asp.fact("map_item", mid))
        lines.append(asp.fact("label", mid, m.label))
    for qid, q in QUOTAS.items():
        lines.append(asp.fact("quota_item", qid))
        lines.append(asp.fact("limit", qid, q.limit))
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding(M,Q) :- map_item(M), quota_item(Q), label(M,"map"), limit(Q,L), L >= 1.
valid_story(M,Q) :- misunderstanding(M,Q).
#show valid_story/2.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story in a toy library with a misunderstanding about a quota and a map.")
    ap.add_argument("--name", choices=ANIMAL_NAMES)
    ap.add_argument("--species", choices=["cat", "mouse", "fox", "rabbit", "owl"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--map", dest="map_kind", choices=MAPS)
    ap.add_argument("--quota", dest="quota_kind", choices=QUOTAS)
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
    map_kind = args.map_kind or rng.choice(list(MAPS))
    quota_kind = args.quota_kind or rng.choice(list(QUOTAS))
    reasonableness_gate(MAPS[map_kind], QUOTAS[quota_kind])
    species = args.species or rng.choice(["cat", "mouse", "fox", "rabbit", "owl"])
    name = args.name or rng.choice(ANIMAL_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(name=name, species=species, helper=helper, map_kind=map_kind, quota_kind=quota_kind)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", species=params.species, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", species=params.helper, label=f"the {params.helper}"))
    map_item = world.add(Entity(id="map", kind="thing", species="thing", label=MAPS[params.map_kind].label, phrase=MAPS[params.map_kind].phrase, location="front table"))
    quota = world.add(Entity(id="quota", kind="thing", species="thing", label=QUOTAS[params.quota_kind].label, phrase=f"a sign about a {QUOTAS[params.quota_kind].label}", location="desk"))

    hero.memes["curious"] = 1
    hero.memes["wants_to_transcend"] = 1
    helper.memes["busy"] = 1

    world.say(f"In the toy library, {hero.id} the {hero.species} padded between the shelves and found {map_item.phrase}.")
    world.say(f"{hero.id} thought the map was a game path and wanted to {('transcend' if True else 'follow')} it, even though the little sign by the desk said {quota.label}.")

    world.para()
    world.say(f"{helper.label.capitalize()} saw {hero.id} staring at the map and said, \"The quota means how many books can go out at once.\"")
    world.say(f"But {hero.id} had misunderstood; {hero.id} thought the quota was a secret count for where the map could lead.")
    world.say(f"{hero.id} tapped the map and asked if it could transcend the shelf and point to the best treasure nook.")

    world.para()
    world.say(f"{helper.label.capitalize()} smiled, then showed how the map was only for finding the reading rug and the return basket.")
    world.say(f"They counted the books together, stayed under the quota, and used the map to pick the next cozy stop.")
    world.say(f"At the end, {hero.id} was reading quietly beside the rug, and the map stayed flat on the table where it belonged.")

    world.facts.update(hero=hero, helper=helper, map_item=map_item, quota=quota, params=params)
    prompts = [
        'Write an animal story in a toy library about a misunderstanding over a quota and a map.',
        f'Write a gentle story about {hero.species} named {hero.id} who wants to transcend a map clue but learns what a quota means.',
        'Tell a child-facing story where a helper explains a map and a quota in a toy library.',
    ]
    story_qa = [
        QAItem(
            question=f"What did {hero.id} misunderstand about the quota?",
            answer=f"{hero.id} misunderstood it as a secret rule for where the map could lead, instead of a simple limit on how many books could go out.",
        ),
        QAItem(
            question=f"Who helped {hero.id} understand the map and the quota?",
            answer=f"{helper.label.capitalize()} helped by explaining that the quota was about books and the map was for finding places in the toy library.",
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=f"{hero.id} stayed in the toy library, read quietly, and used the map the right way while keeping under the quota.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a map for?",
            answer="A map helps you find places and understand where things are in a room or outside.",
        ),
        QAItem(
            question="What is a quota?",
            answer="A quota is a limit that says how many things are allowed, such as books or toys.",
        ),
        QAItem(
            question="What is a toy library?",
            answer="A toy library is a place where children can look at, borrow, or share toys and books in a calm, friendly space.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


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


def asp_verify() -> int:
    pairs = set(asp_valid_pairs())
    expected = {("map", "quota")}
    if pairs == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH:")
    print(sorted(pairs), sorted(expected))
    return 1


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for pair in asp_valid_pairs():
            print(pair)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(name="Milo", species="cat", helper="owl", map_kind="map", quota_kind="quota"),
            StoryParams(name="Pip", species="mouse", helper="fox", map_kind="sticker_map", quota_kind="book_quota"),
            StoryParams(name="Luna", species="rabbit", helper="cat", map_kind="tide_map", quota_kind="sticker_quota"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
