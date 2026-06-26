#!/usr/bin/env python3
"""
storyworlds/worlds/wacko_rent_transformation_folk_tale.py
=========================================================

A small folk-tale storyworld about a wacko little deal: someone rents a magic
thing, uses it for a transformation, and learns a sensible lesson.

The domain is intentionally tiny and constraint-checked. It centers on:
- a village setting,
- a rented object,
- a transformation with clear before/after state,
- a slightly wacky helper or seeker,
- a folk-tale cadence with a beginning, turn, and ending image.

The story is built from a simulated world model, not from a frozen paragraph.
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
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "witch"}
        male = {"boy", "man", "father", "grandfather", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = False
    allows: set[str] = field(default_factory=set)


@dataclass
class MagicItem:
    id: str
    label: str
    phrase: str
    effect: str
    transform_to: str
    transform_label: str
    requires: set[str] = field(default_factory=set)
    safe_if_returned: bool = True


@dataclass
class StoryParams:
    place: str
    item: str
    seeker: str
    companion: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    seeker = world.get(world.facts["seeker"].id)
    item: MagicItem = world.facts["magic_item"]
    if seeker.memes.get("wonder", 0.0) < THRESHOLD:
        return out
    if seeker.meters.get("cost", 0.0) < THRESHOLD:
        return out
    sig = ("transformed", seeker.id, item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seeker.type = item.transform_to
    seeker.label = item.transform_label
    seeker.phrase = item.transform_label
    seeker.memes["joy"] = seeker.memes.get("joy", 0.0) + 1
    seeker.memes["self_trust"] = seeker.memes.get("self_trust", 0.0) + 1
    out.append(f"By the glow of the {item.label}, {seeker.id} became {item.transform_label}.")
    return out


def _r_return(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("returned"):
        return out
    seeker = world.get(world.facts["seeker"].id)
    companion = world.get(world.facts["companion"].id)
    sig = ("returned", seeker.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seeker.memes["relief"] = seeker.memes.get("relief", 0.0) + 1
    companion.memes["peace"] = companion.memes.get("peace", 0.0) + 1
    out.append(f"When the borrowed wonder was given back, the village grew calm again.")
    return out


CAUSAL_RULES = [_r_transformation, _r_return]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_transform(world: World, seeker: Entity, item: MagicItem) -> bool:
    sim = world.copy()
    sim.get(seeker.id).memes["wonder"] = 1
    sim.get(seeker.id).meters["cost"] = 1
    sim.facts["magic_item"] = item
    sim.facts["seeker"] = seeker
    propagate(sim, narrate=False)
    return sim.get(seeker.id).type == item.transform_to


def place_detail(place: Place) -> str:
    if place.indoors:
        return f"The {place.name} was snug, with a little fire and a round wooden table."
    return f"The {place.name} sat under the sky, with wind in the grass and paths through the trees."


def intro(world: World, seeker: Entity) -> None:
    world.say(
        f"In a little village, there lived a {seeker.type} named {seeker.id}, and {seeker.id} was a bit wacko in the kindest way."
    )


def desire(world: World, seeker: Entity, item: MagicItem) -> None:
    seeker.memes["wonder"] = seeker.memes.get("wonder", 0.0) + 1
    world.say(
        f"{seeker.id} loved strange little marvels, and {seeker.pronoun()} could not stop staring at {item.phrase}."
    )


def borrow(world: World, seeker: Entity, companion: Entity, item: MagicItem) -> None:
    seeker.meters["cost"] = seeker.meters.get("cost", 0.0) + 1
    world.say(
        f"So {seeker.id} asked {companion.pronoun('object')} to rent {item.phrase} for one night, and {companion.id} agreed."
    )


def travel(world: World, seeker: Entity, item: MagicItem) -> None:
    world.say(place_detail(world.place))
    world.say(
        f"At dusk, {seeker.id} carried {item.label} to the old lane behind the bakery, where the air smelled of bread and moss."
    )


def warn(world: World, companion: Entity, seeker: Entity, item: MagicItem) -> bool:
    if not predict_transform(world, seeker, item):
        return False
    world.say(
        f'"Mind the return, little one," said {companion.id}. "A rented wonder must come home by morning."'
    )
    return True


def use_magic(world: World, seeker: Entity, item: MagicItem) -> None:
    world.say(
        f"{seeker.id} touched the {item.label}, and the {item.effect} began to hum like bees in a jar."
    )
    propagate(world, narrate=True)


def return_item(world: World, seeker: Entity, companion: Entity, item: MagicItem) -> None:
    world.facts["returned"] = True
    world.say(
        f"Before the sun climbed high, {seeker.id} brought back the {item.label}, bowing low to {companion.id}."
    )
    propagate(world, narrate=True)
    world.say(
        f"After that, {seeker.id} remained changed, but the borrowed magic was safely home."
    )


def tell(place: Place, item: MagicItem, seeker_name: str, companion_name: str) -> World:
    world = World(place)
    seeker = world.add(Entity(id=seeker_name, kind="character", type="child"))
    companion = world.add(Entity(id=companion_name, kind="character", type="elder"))
    world.facts["seeker"] = seeker
    world.facts["companion"] = companion
    world.facts["magic_item"] = item

    intro(world, seeker)
    desire(world, seeker, item)
    borrow(world, seeker, companion, item)

    world.para()
    travel(world, seeker, item)
    warned = warn(world, companion, seeker, item)
    if warned:
        world.say(f"But {seeker.id} was too delighted to be frightened.")
    use_magic(world, seeker, item)

    world.para()
    return_item(world, seeker, companion, item)
    return world


PLACES = {
    "village": Place(name="the village", indoors=False, allows={"mirror", "cloak", "bell"}),
    "cottage": Place(name="the cottage", indoors=True, allows={"mirror", "cloak"}),
    "market": Place(name="the market square", indoors=False, allows={"bell", "cloak"}),
}

ITEMS = {
    "mirror": MagicItem(
        id="mirror",
        label="moon mirror",
        phrase="the moon mirror",
        effect="silver light",
        transform_to="fox",
        transform_label="a quick fox with bright eyes",
        requires={"wonder"},
    ),
    "cloak": MagicItem(
        id="cloak",
        label="spell cloak",
        phrase="the spell cloak",
        effect="soft green sparks",
        transform_to="bird",
        transform_label="a small bird with gold feathers",
        requires={"wonder"},
    ),
    "bell": MagicItem(
        id="bell",
        label="rented bell",
        phrase="the rented bell",
        effect="a ringing laugh",
        transform_to="cat",
        transform_label="a clever cat with a curled tail",
        requires={"wonder"},
    ),
}

SEEKERS = ["Pip", "Milo", "Nina", "Tavi", "Lena", "Orin"]
COMPANIONS = ["Grandma", "Grandpa", "Auntie", "Uncle"]
GENDERS = {"Pip": "boy", "Milo": "boy", "Orin": "boy", "Nina": "girl", "Tavi": "girl", "Lena": "girl"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for item_id in place.allows:
            combos.append((place_id, item_id, "seeker"))
    return combos


@dataclass
class WorldSampleMeta:
    place: str
    item: str
    seeker: str
    companion: str


KNOWLEDGE = {
    "mirror": [
        ("What is a mirror?", "A mirror is a shiny surface that shows an image of whoever stands in front of it."),
    ],
    "cloak": [
        ("What is a cloak?", "A cloak is a loose piece of clothing that hangs over your shoulders like a covering."),
    ],
    "bell": [
        ("What is a bell?", "A bell is a metal object that makes a ringing sound when it is moved or struck."),
    ],
    "rent": [
        ("What does it mean to rent something?", "To rent something means to borrow it for a short time and give it back later."),
    ],
    "wacko": [
        ("What does wacko mean?", "Wacko means very odd or silly in a way that makes people notice and smile."),
    ],
    "transformation": [
        ("What is a transformation?", "A transformation is a change from one form into another."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    item: MagicItem = f["magic_item"]
    return [
        f'Write a short folk tale about a wacko child who rents "{item.label}" and becomes transformed.',
        f"Tell a gentle village story where {seeker.id} borrows {item.phrase} and changes shape at dusk.",
        f'Write a simple transformation story that includes the words "rent" and "{seeker.id}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker = f["seeker"]
    companion = f["companion"]
    item: MagicItem = f["magic_item"]
    return [
        QAItem(
            question=f"Who is the folk tale about?",
            answer=f"It is about {seeker.id}, a wacko little seeker who wanted to rent {item.phrase} from {companion.id}.",
        ),
        QAItem(
            question=f"What did {seeker.id} rent?",
            answer=f"{seeker.id} rented {item.phrase}, which glowed when it was used for the transformation.",
        ),
        QAItem(
            question=f"What did {seeker.id} become after using the {item.label}?",
            answer=f"{seeker.id} became {item.transform_label}. That was the transformation the magic brought about.",
        ),
        QAItem(
            question=f"Why did {seeker.id} bring the {item.label} back?",
            answer="The borrowed wonder had to be returned, because it was only rented for a short time.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    item: MagicItem = f["magic_item"]
    out = [QAItem(question=q, answer=a) for q, a in KNOWLEDGE["rent"] + KNOWLEDGE["transformation"]]
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[item.id])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["wacko"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        if e.kind == "character":
            bits.append("character")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="village", item="mirror", seeker="Pip", companion="Grandma"),
    StoryParams(place="cottage", item="cloak", seeker="Nina", companion="Auntie"),
    StoryParams(place="market", item="bell", seeker="Milo", companion="Grandpa"),
]


def explain_rejection(place: str, item: str) -> str:
    return f"(No story: the {item} does not fit this setting well enough for a borrowed transformation tale.)"


ASP_RULES = r"""
place(P) :- setting(P).
item(I) :- magic_item(I).

rented(I) :- item(I).
can_use(P,I) :- place(P), place_allows(P,I), rented(I).
valid(P,I) :- can_use(P,I).

transforms(S,I) :- seeker(S), item(I), wonder(S), cost_paid(S), valid(P,I).
returned(S) :- seeker(S), item(I), gave_back(S,I).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for item in sorted(p.allows):
            lines.append(asp.fact("place_allows", pid, item))
    for iid in ITEMS:
        lines.append(asp.fact("magic_item", iid))
    for name in SEEKERS:
        lines.append(asp.fact("seeker", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set((p, i) for p, i, _ in valid_combos())
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld about rent and transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--seeker")
    ap.add_argument("--companion")
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
    combos = [(p, i) for p in PLACES for i in PLACES[p].allows]
    if args.place:
        combos = [(p, i) for p, i in combos if p == args.place]
    if args.item:
        combos = [(p, i) for p, i in combos if i == args.item]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item = rng.choice(sorted(combos))
    seeker = args.seeker or rng.choice(SEEKERS)
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(place=place, item=item, seeker=seeker, companion=companion)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        ITEMS[params.item],
        params.seeker,
        params.companion,
    )
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item) combos:\n")
        for p, i in combos:
            print(f"  {p:8} {i}")
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
            header = f"### {p.seeker}: {p.item} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
