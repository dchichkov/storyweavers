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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type == "ghost":
                return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
        return self.label or self.id

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    mood: str
    has_echo: bool = False


@dataclass
class Coupon:
    label: str
    phrase: str
    shareable: bool
    expires: str
    redeem_for: str


@dataclass
class Duel:
    name: str
    verb: str
    spark: str
    confusion: str


@dataclass
class StoryParams:
    place: str
    coupon: str
    duel: str
    name1: str
    name2: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w.paragraphs = [[]]
        return w


def _r_confusion(world: World) -> list[str]:
    out = []
    p = world.facts.get("protagonist")
    coupon = world.facts.get("coupon")
    if not p or not coupon:
        return out
    for e in world.entities.values():
        if e.kind != "character":
            continue
        if e.memes.get("misunderstanding", 0) >= THRESHOLD and ("explain", e.id) not in world.fired:
            world.fired.add(("explain", e.id))
            out.append(f"{e.ref().capitalize()} paused, because the coupon did not mean what they first thought.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_confusion,):
            got = rule(world)
            if got:
                changed = True
                out.extend(got)
    if narrate:
        for s in out:
            world.say(s)
    return out


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    g1 = world.add(Entity(id=params.name1, kind="character", type="ghost", label=params.name1, meters={"float": 1.0}, memes={"curiosity": 1.0}))
    g2 = world.add(Entity(id=params.name2, kind="character", type="ghost", label=params.name2, meters={"float": 1.0}, memes={"curiosity": 1.0}))
    c = COUPONS[params.coupon]
    d = DUELS[params.duel]
    coupon = world.add(Entity(id="coupon", type="coupon", label=c.label, phrase=c.phrase, owner=g1.id))

    world.facts.update(protagonist=g1, partner=g2, coupon=c, duel=d, place=place)

    world.say(f"In the {place.name}, {g1.ref()} found {c.phrase}.")
    world.say(f"{g2.ref().capitalize()} drifted closer, because the coupon looked like a tiny promise for {c.redeem_for}.")
    world.para()
    world.say(f"Then the two ghosts began a playful {d.name}, circling the coupon with soft whooshes and bright eyes.")
    g1.memes["want"] = 1.0
    g2.memes["want"] = 1.0
    g1.memes["misunderstanding"] = 1.0
    g2.memes["misunderstanding"] = 1.0
    world.say(f"Each ghost thought the other wanted to keep it all, and that was the misunderstanding.")
    propagate(world, narrate=True)
    world.para()
    if c.shareable:
        g1.memes["sharing"] = 1.0
        g2.memes["sharing"] = 1.0
        g1.memes["misunderstanding"] = 0.0
        g2.memes["misunderstanding"] = 0.0
        world.say(f"At last, {g1.ref()} pointed at the tiny print: the coupon was for sharing {c.redeem_for} together.")
        world.say(f"The duel stopped at once, and the two ghosts split the treat and the coupon's joy right down the middle.")
        world.say(f"They floated home side by side, still glowing, with the coupon folded safely between them like a secret smile.")
    else:
        world.say(f"But the coupon could not be shared, so the ghosts had to wait for a different ending.")
    return world


PLACES = {
    "attic": Place(name="the attic", mood="dusty", has_echo=True),
    "hall": Place(name="the old hall", mood="quiet", has_echo=True),
    "garden": Place(name="the moonlit garden", mood="soft", has_echo=False),
}

COUPONS = {
    "candies": Coupon(label="candy coupon", phrase="a candy coupon", shareable=True, expires="by midnight", redeem_for="sparkly candies"),
    "cakes": Coupon(label="cake coupon", phrase="a bakery coupon", shareable=True, expires="tomorrow", redeem_for="tiny moon cakes"),
    "lanterns": Coupon(label="lantern coupon", phrase="a lantern-shop coupon", shareable=True, expires="before sunrise", redeem_for="glow lanterns"),
}

DUELS = {
    "whoosh": Duel(name="whoosh duel", verb="whoosh", spark="a swirl of air", confusion="who should keep the coupon"),
    "stare": Duel(name="staring duel", verb="stare", spark="a long hush", confusion="whether the coupon was only for one ghost"),
    "hover": Duel(name="hover duel", verb="hover", spark="a floating ring", confusion="if the coupon was a prize or an invitation"),
}

NAMES = ["Milo", "Nina", "Pip", "Ivy", "Jules", "Bree", "Otto", "Luna"]
CURATED = [
    StoryParams(place="attic", coupon="candies", duel="whoosh", name1="Milo", name2="Nina"),
    StoryParams(place="hall", coupon="cakes", duel="stare", name1="Ivy", name2="Pip"),
    StoryParams(place="garden", coupon="lanterns", duel="hover", name1="Luna", name2="Otto"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world: coupon, duel, misunderstanding, sharing, resolution.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--coupon", choices=COUPONS)
    ap.add_argument("--duel", choices=DUELS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
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
    place = args.place or rng.choice(list(PLACES))
    coupon = args.coupon or rng.choice(list(COUPONS))
    duel = args.duel or rng.choice(list(DUELS))
    name1 = args.name1 or rng.choice(NAMES)
    name2 = args.name2 or rng.choice([n for n in NAMES if n != name1])
    return StoryParams(place=place, coupon=coupon, duel=duel, name1=name1, name2=name2)


def generation_prompts(world: World) -> list[str]:
    p = world.facts["protagonist"]
    q = world.facts["partner"]
    c = world.facts["coupon"]
    d = world.facts["duel"]
    return [
        f"Write a short ghost story about {p.ref()} and {q.ref()} in {world.place.name} involving a {c.label} and a {d.name}.",
        f"Tell a gentle story where a coupon causes a misunderstanding and ends with sharing.",
        f"Write a child-friendly ghost tale that begins with a duel and ends in resolution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["protagonist"]
    q = world.facts["partner"]
    c = world.facts["coupon"]
    d = world.facts["duel"]
    return [
        QAItem(question=f"Who found the coupon?", answer=f"{p.ref()} found the {c.label} in {world.place.name}."),
        QAItem(question=f"What made the ghosts start the duel?", answer=f"They thought the coupon meant one ghost should keep it, which caused a misunderstanding."),
        QAItem(question=f"How did the story end?", answer=f"They realized the coupon was for sharing, so the duel ended and they made peace together."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(question="What is a coupon?", answer="A coupon is a small paper or digital note that helps you get something special, often with a discount or deal."),
        QAItem(question="What is a misunderstanding?", answer="A misunderstanding happens when someone thinks something means one thing, but it really means something else."),
        QAItem(question="What is sharing?", answer="Sharing means letting more than one person use, enjoy, or have a turn with something."),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding(X) :- ghost(X), wants_coupon(X), not understands_coupon(X).
resolution :- understanding, sharing.
sharing :- shareable(coupon).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for k in PLACES:
        lines.append(asp.fact("place", k))
    for k in COUPONS:
        lines.append(asp.fact("coupon", k))
        if COUPONS[k].shareable:
            lines.append(asp.fact("shareable", "coupon"))
    for k in DUELS:
        lines.append(asp.fact("duel", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show sharing/0. #show resolution/0."))
    atoms = {s.name for s in model}
    if "sharing" in atoms and "resolution" in atoms:
        print("OK: ASP rules support sharing and resolution.")
        return 0
    print("MISMATCH: ASP rules did not derive expected atoms.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show sharing/0. #show resolution/0."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            p = resolve_params(args, rng)
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
