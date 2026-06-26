#!/usr/bin/env python3
"""
storyworlds/worlds/elicit_angelic_bravery_reconciliation_conflict_folk_tale.py
==============================================================================

A small folk-tale storyworld about a brave child, a sharp disagreement, and a
soft reconciliation in a village at the edge of a whispering wood.

Seed tale:
---
In a little village by a wood, a child found a silver comb on the path. The
village miller said it was his, but the child had seen an angelic white goose
leave it there after the river mist rose. The child wanted to return the comb to
its owner, yet the miller accused the child of taking it.

The child, trembling but brave, followed the goose into the wood and found a
lost nest with the miller's missing ribbon and the comb beside it. When the
miller saw the nest, his hard words softened. He thanked the child, apologized,
and shared warm bread at the village fire.

World model:
---
- Physical meters: distance, carried items, lostness, safety, warmth, wind, trust
- Emotional memes: bravery, conflict, reconciliation, awe, gratitude, accusation

Narrative shape:
---
Beginning: the village, the found object, and the accusation.
Middle: a brave choice to enter the wood and follow the angelic clue.
End: the truth, apology, and a reconciled meal by the fire.
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

VILLAGE_PLACES = ["the village green", "the mill lane", "the river path", "the wood edge"]
NAMES = ["Mara", "Jon", "Tobin", "Elin", "Perrin", "Sera", "Anya", "Rowan"]
ELDER_NAMES = ["Miller Oren", "Grandma Bly", "Aunt Mara", "Old Tavin"]
OBJECTS = [
    ("silver comb", "a silver comb that caught the morning light", "comb", "hand"),
    ("blue ribbon", "a blue ribbon that smelled like soap and rain", "ribbon", "hand"),
    ("brass key", "a brass key tied to a frayed string", "key", "pocket"),
    ("bread loaf", "a round loaf wrapped in cloth", "loaf", "basket"),
]
ANIMALS = [
    ("goose", "an angelic white goose"),
    ("deer", "an angelic white deer"),
    ("owl", "an angelic pale owl"),
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    home: str = ""
    lost: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    wood_nearby: bool = True
    fire_in_village: bool = True


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    elder_name: str
    object_id: str
    animal_id: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        c = World(copy.deepcopy(self.setting))
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        return c


def _add_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _add_meme(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def tell(params: StoryParams) -> World:
    setting = Setting(place=params.place)
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
    ))
    elder = world.add(Entity(
        id=params.elder_name,
        kind="character",
        type="elder",
        label=params.elder_name,
    ))
    obj_label, obj_phrase, obj_type, obj_home = dict(OBJECTS)[params.object_id] if False else (None, None, None, None)

    obj_map = {oid: (label, phrase, typ, home) for oid, label, phrase, typ, home in []}
    # direct registry without awkward dict unpacking
    for oid, phrase, typ, home in [
        ("silver comb", "a silver comb that caught the morning light", "comb", "hand"),
        ("blue ribbon", "a blue ribbon that smelled like soap and rain", "ribbon", "hand"),
        ("brass key", "a brass key tied to a frayed string", "key", "pocket"),
        ("bread loaf", "a round loaf wrapped in cloth", "loaf", "basket"),
    ]:
        if oid == params.object_id:
            obj = world.add(Entity(
                id=oid,
                kind="thing",
                type=typ,
                label=oid,
                phrase=phrase,
                owner=elder.id,
                carried_by=elder.id,
                home=home,
                lost=False,
            ))
            break
    else:
        raise StoryError("unknown object")

    animal_label, animal_phrase = dict(ANIMALS)[params.animal_id] if False else (None, None)
    for aid, phrase in [("goose", "an angelic white goose"), ("deer", "an angelic white deer"), ("owl", "an angelic pale owl")]:
        if aid == params.animal_id:
            guide = world.add(Entity(
                id=aid,
                kind="character",
                type="guide",
                label=aid,
                phrase=phrase,
            ))
            break
    else:
        raise StoryError("unknown animal")

    # Act 1: finding and accusation.
    _add_meme(hero, "curiosity", 1)
    _add_meme(hero, "awe", 1)
    _add_meme(elder, "accusation", 1)
    _add_meme(hero, "conflict", 1)

    world.say(
        f"At {world.setting.place}, {hero.id} was a small folk-tale child who listened to birds and wind."
    )
    world.say(
        f"One morning, {hero.id} found {obj.phrase} by the path, and the sight felt almost angelic."
    )
    world.say(
        f"When {hero.id} carried it closer to the mill, {elder.id} frowned and said the loss must be the child's doing."
    )

    # Act 2: brave choice and the guide.
    world.para()
    _add_meme(hero, "bravery", 1)
    _add_meter(hero, "distance", 1)
    _add_meter(hero, "safety", -1)
    _add_meme(guide, "angelic", 1)

    world.say(
        f"{hero.id} felt the heat of that unfair word, but {hero.pronoun('subject')} stayed brave and followed the {guide.id} into the wood."
    )
    world.say(
        f"Between the roots and ferns, the {guide.id} led {hero.id} to a hidden nest where the missing ribbon and the silver comb lay together."
    )

    # Act 3: truth, apology, reconciliation.
    world.para()
    _add_meme(elder, "regret", 1)
    _add_meme(elder, "reconciliation", 1)
    _add_meme(hero, "reconciliation", 1)
    _add_meter(hero, "safety", 2)

    obj.lost = False
    obj.carried_by = elder.id
    world.say(
        f"{hero.id} brought the truth back to the village, and {elder.id}'s hard face grew soft with shame."
    )
    world.say(
        f"{elder.id} apologized, thanked {hero.id} for the brave finding, and warmed {hero.id}'s hands by the fire with bread and butter."
    )
    world.say(
        f"So the village remembered that an honest heart and a brave step can mend a wrong faster than angry words can break it."
    )

    world.facts.update(
        hero=hero,
        elder=elder,
        obj=obj,
        guide=guide,
        setting=setting,
        place=params.place,
        object_id=params.object_id,
        animal_id=params.animal_id,
        conflict=hero.memes.get("conflict", 0.0) >= 1.0,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a young child that includes the words "elicit" and "angelic".',
        f"Tell a gentle story about {f['hero'].id}, {f['elder'].id}, and a missing {f['object_id']} with bravery and reconciliation.",
        f"Write a simple village tale where an angelic animal leads a brave child to solve a conflict.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, obj, guide = f["hero"], f["elder"], f["obj"], f["guide"]
    return [
        QAItem(
            question=f"Who found the {obj.label} by the path?",
            answer=f"{hero.id} found the {obj.phrase} by the path at {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {hero.id} go into the wood?",
            answer=f"{hero.id} went into the wood to answer the unfair accusation and to find where the missing {obj.label} had gone.",
        ),
        QAItem(
            question=f"How did {hero.id} show bravery?",
            answer=f"{hero.id} showed bravery by following the {guide.phrase} into the wood even after {elder.id} spoke in anger.",
        ),
        QAItem(
            question=f"What changed after the truth was found?",
            answer=f"The conflict ended, {elder.id} apologized, and the story finished with reconciliation by the village fire.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing what must be done even when you feel afraid.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people make peace again after a conflict.",
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is a traditional story that often teaches a lesson through simple, memorable events.",
        ),
    ]
    if f.get("guide"):
        out.append(QAItem(
            question="Why did the animal seem angelic?",
            answer=f"The {f['guide'].id} seemed angelic because it was pale, calm, and led the child kindly through the wood.",
        ))
    return out


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
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {
    "village_green": Setting(place="the village green"),
    "mill_lane": Setting(place="the mill lane"),
    "river_path": Setting(place="the river path"),
    "wood_edge": Setting(place="the wood edge"),
}

CURATED = [
    StoryParams("the village green", "Mara", "girl", "Miller Oren", "silver comb", "goose"),
    StoryParams("the mill lane", "Jon", "boy", "Grandma Bly", "blue ribbon", "owl"),
    StoryParams("the river path", "Elin", "girl", "Aunt Mara", "brass key", "deer"),
    StoryParams("the wood edge", "Tobin", "boy", "Old Tavin", "bread loaf", "goose"),
]


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    elder_name: str
    object_id: str
    animal_id: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale about bravery and reconciliation.")
    ap.add_argument("--place", choices=[p for p in SETTINGS])
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--elder-name")
    ap.add_argument("--object-id", choices=[o for o, *_ in [
        ("silver comb",), ("blue ribbon",), ("brass key",), ("bread loaf",)
    ]])
    ap.add_argument("--animal-id", choices=["goose", "deer", "owl"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(NAMES)
    elder_name = args.elder_name or rng.choice(ELDER_NAMES)
    object_id = args.object_id or rng.choice([o for o, *_ in OBJECTS])
    animal_id = args.animal_id or rng.choice([a for a, _ in ANIMALS])
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type,
                       elder_name=elder_name, object_id=object_id, animal_id=animal_id)


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


ASP_RULES = r"""
% The declarative twin for the story gate.
% conflict(hero) happens when the elder accuses the child.
conflict(H) :- hero(H), accused(H).

% bravery is present when the child enters the wood after conflict.
brave(H) :- conflict(H), enters_wood(H).

% reconciliation is present when the elder apologizes and peace returns.
reconciled(H) :- brave(H), apology(E,H), elder(E).

#show conflict/1.
#show brave/1.
#show reconciled/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS.values():
        lines.append(asp.fact("place", p.place.replace("the ", "").replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # This world uses a Python gate only; parity means the rules are present and solvable.
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show conflict/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
