#!/usr/bin/env python3
"""
storyworlds/worlds/cruller_surprise_folk_tale.py
=================================================

A small folk-tale storyworld about a cruller, a surprise, and a gentle turn
from worry to delight.

Seed tale:
---
Long ago, in a little village at the edge of a green wood, a child and a
grandmother baked a basket of crullers for the winter market. The child loved
the sweet spirals and wanted to carry them into town. But on the way, the wind
began to sing around the basket, and the child feared the crullers might be
lost.

Then a surprise came to pass: the basket held one cruller more than anyone had
counted, and inside the extra spiral was a tiny warm note that said, "Share
with the hungry." The child smiled, gave away the surprise cruller, and the
market night ended with full bellies and laughing hearts.

World model notes:
---
- A cruller is a sweet, twisted pastry.
- Surprise is modeled as a small, causal shift in emotional state and outcome.
- Folk-tale tone comes from the village, grandmother, wind, market, and sharing.
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

CRACK_THRESHOLD = 1.0


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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    precious: bool = True


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    elder_type: str
    prize: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character" and e.type in {"girl", "boy", "child"}]


PLACES = {
    "village": Place(id="village", label="the little village", tags={"market", "folk", "wind"}),
    "kitchen": Place(id="kitchen", label="the warm kitchen", indoors=True, tags={"baking", "folk"}),
    "market": Place(id="market", label="the market square", tags={"market", "folk"}),
}

PRIZES = {
    "basket": Prize(id="basket", label="basket of crullers", phrase="a basket of sweet crullers", region="hands"),
    "plate": Prize(id="plate", label="plate of crullers", phrase="a plate piled with crullers", region="table"),
}

CHILD_NAMES = ["Mina", "Tara", "Ola", "Nell", "Pia", "Eli", "Jon", "Niko"]
ELDER_TYPES = ["grandmother", "grandfather"]
CHILD_TYPES = ["girl", "boy"]
TRAITS = ["curious", "cheerful", "brave", "patient", "lively"]


def _say_intro(world: World, child: Entity, elder: Entity, prize: Entity) -> None:
    world.say(
        f"Once upon a time, {child.id} was a {random.choice(TRAITS)} little {child.type} "
        f"who lived near {world.place.label}."
    )
    world.say(
        f"{child.id} loved {prize.label} more than any other treat, and "
        f"{elder.pronoun('possessive')} {prize.label} was always made with care."
    )


def _bake(world: World, elder: Entity, child: Entity, prize: Entity) -> None:
    elder.memes["care"] = elder.memes.get("care", 0) + 1
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    prize.meters["warmth"] = prize.meters.get("warmth", 0) + 1
    world.say(
        f"In the warm hush of morning, {elder.id} baked {prize.phrase} with flour, honey, and a twist of patience."
    )
    world.say(
        f"The sweet smell drifted through the house, and {child.id} came running to the table with shining eyes."
    )


def _travel(world: World, child: Entity, elder: Entity, prize: Entity) -> None:
    child.memes["want"] = child.memes.get("want", 0) + 1
    world.para()
    world.say(
        f"By noon, {child.id} and {elder.id} set out for {world.place.label}, carrying the crullers in a covered basket."
    )
    world.say(
        f"The road was long and the wind was lively, singing around the lid like a fiddle in a folk song."
    )


def _worry(world: World, child: Entity, elder: Entity, prize: Entity) -> None:
    child.memes["fear"] = child.memes.get("fear", 0) + 1
    world.say(
        f"Then {child.id} peeked inside and worried that the basket might be lighter than it had been at home."
    )
    world.say(
        f"\"Oh no,\" {child.id} whispered, \"what if a cruller has slipped away into the wind?\""
    )
    elder.memes["calm"] = elder.memes.get("calm", 0) + 1
    world.say(
        f"But {elder.id} only smiled and said the world sometimes keeps a small surprise for those who travel kindly."
    )


def _surprise(world: World, child: Entity, elder: Entity, prize: Entity) -> None:
    key = "surprise"
    if key in world.fired:
        return
    world.fired.add(key)
    prize.meters["count"] = prize.meters.get("count", 3) + 1
    child.memes["surprise"] = child.memes.get("surprise", 0) + 1
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    world.say(
        f"When they opened the basket again, there was one cruller more than anyone had counted."
    )
    world.say(
        f"Inside the extra spiral lay a tiny warm note that read, \"Share with the hungry.\""
    )
    world.say(
        f"{child.id} gasped, then laughed, for the surprise felt like a gift tucked into the story itself."
    )


def _share(world: World, child: Entity, elder: Entity, prize: Entity) -> None:
    child.memes["generosity"] = child.memes.get("generosity", 0) + 1
    elder.memes["pride"] = elder.memes.get("pride", 0) + 1
    world.para()
    world.say(
        f"So {child.id} carried the surprise cruller to a hungry neighbor at the market gate."
    )
    world.say(
        f"That night, the village children ate sweet rings with sticky fingers, and the grown folk smiled at the full, warm table."
    )
    world.say(
        f"By the end, the basket was lighter, but {child.id}'s heart was fuller than before."
    )


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    prize = PRIZES[params.prize]
    world = World(place)

    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    elder = world.add(Entity(id="Elder", kind="character", type=params.elder_type))
    basket = world.add(Entity(
        id="basket",
        type="thing",
        label=prize.label,
        phrase=prize.phrase,
        owner=child.id,
        caretaker=elder.id,
    ))

    _say_intro(world, child, elder, basket)
    _bake(world, elder, child, basket)
    _travel(world, child, elder, basket)
    _worry(world, child, elder, basket)
    _surprise(world, child, elder, basket)
    _share(world, child, elder, basket)

    world.facts.update(
        child=child,
        elder=elder,
        prize=basket,
        place=place,
        surprise=True,
        shared=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    elder: Entity = f["elder"]  # type: ignore[assignment]
    prize: Entity = f["prize"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {child.id}, a little {child.type}, and {elder.id}, who baked crullers with care.",
        ),
        QAItem(
            question=f"What sweet food did they carry to {place.label}?",
            answer=f"They carried {prize.phrase} to {place.label}.",
        ),
        QAItem(
            question=f"What surprise happened in the basket?",
            answer="There was one cruller more than anyone had counted, and it came with a note about sharing.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{child.id} shared the extra cruller, and the village ended the day with full bellies and happy hearts.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cruller?",
            answer="A cruller is a sweet pastry, often twisted into a ring or spiral and sometimes covered with glaze or sugar.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes you pause, wonder, or laugh because it was not planned or counted on.",
        ),
        QAItem(
            question="Why do people share food in folk tales?",
            answer="Folk tales often say that sharing food helps people care for one another, and it can turn a small gift into a bigger one.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    return [
        f"Write a gentle folk tale about {child.id} carrying crullers to {place.label} and finding a surprise.",
        "Tell a short story where a cruller basket grows into a kind surprise and ends with sharing.",
        "Write a child-friendly folk tale with wind, a warm bake, and one unexpected cruller.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
place(village).
place(kitchen).
place(market).

child_name(mina).
child_name(tara).
child_name(ola).
child_name(nell).
child_name(pia).
child_name(eli).
child_name(jon).
child_name(niko).

child_type(girl).
child_type(boy).

elder_type(grandmother).
elder_type(grandfather).

prize(basket).

surprise_story(Place,Name,Child,Elder,Prize) :-
    place(Place), child_name(Name), child_type(Child), elder_type(Elder), prize(Prize).
#show surprise_story/5.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
    for n in CHILD_NAMES:
        lines.append(asp.fact("child_name", n.lower()))
    for t in CHILD_TYPES:
        lines.append(asp.fact("child_type", t))
    for e in ELDER_TYPES:
        lines.append(asp.fact("elder_type", e))
    for pr in PRIZES.values():
        lines.append(asp.fact("prize", pr.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_story_count() -> int:
    import asp
    model = asp.one_model(asp_program("#show surprise_story/5."))
    return len(asp.atoms(model, "surprise_story"))


def asp_verify() -> int:
    expected = len(PLACES) * len(CHILD_NAMES) * len(CHILD_TYPES) * len(ELDER_TYPES) * len(PRIZES)
    got = asp_story_count()
    if got != expected:
        print(f"MISMATCH: ASP found {got} possibilities, expected {expected}.")
        return 1
    print(f"OK: ASP found {got} possibilities.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale storyworld about a cruller and a surprise.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--elder-type", choices=ELDER_TYPES)
    ap.add_argument("--prize", choices=PRIZES.keys())
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
    place = args.place or rng.choice(list(PLACES.keys()))
    name = args.name or rng.choice(CHILD_NAMES)
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    elder_type = args.elder_type or rng.choice(ELDER_TYPES)
    prize = args.prize or "basket"
    if prize not in PRIZES:
        raise StoryError("unknown prize")
    if place not in PLACES:
        raise StoryError("unknown place")
    return StoryParams(place=place, child_name=name, child_type=child_type, elder_type=elder_type, prize=prize)


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="village", child_name="Mina", child_type="girl", elder_type="grandmother", prize="basket"),
    StoryParams(place="market", child_name="Eli", child_type="boy", elder_type="grandfather", prize="basket"),
    StoryParams(place="kitchen", child_name="Ola", child_type="girl", elder_type="grandmother", prize="basket"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show surprise_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show surprise_story/5."))
        stories = sorted(set(asp.atoms(model, "surprise_story")))
        for s in stories:
            print(s)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        tries = 0
        while len(samples) < args.n and tries < max(50, args.n * 20):
            tries += 1
            p = resolve_params(args, random.Random(rng.randrange(2**31)))
            sample = generate(p)
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
