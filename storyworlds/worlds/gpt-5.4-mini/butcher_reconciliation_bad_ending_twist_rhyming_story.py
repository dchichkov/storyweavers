#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/butcher_reconciliation_bad_ending_twist_rhyming_story.py
========================================================================================

A small standalone storyworld about a child, a butcher, a lost treat, and a
twist that ends in a bittersweet reconciliation. The prose is written in a
light rhyming style, with simulated state driving the plot beats.

This world is built for a tiny TinyStories-style domain:
- a child visits a butcher shop,
- a small misunderstanding causes hurt feelings,
- the child and butcher reconcile,
- a twist changes what the child expected,
- the ending is sad rather than triumphant, but still emotionally complete.

The story quality goal is not to be cheerful; it is to be clear, concrete, and
state-driven, with a real ending image that proves what changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    scent: str
    sound: str


@dataclass
class Offer:
    id: str
    label: str
    phrase: str
    taste: str
    rarity: int
    kind: str = "treat"


@dataclass
class Twist:
    id: str
    reveal: str
    effect: str
    sadness: int


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_hurt(world: World) -> list[str]:
    out = []
    child = world.get("child")
    butcher = world.get("butcher")
    if child.memes["hurt"] >= THRESHOLD and ("hurt",) not in world.fired:
        world.fired.add(("hurt",))
        butcher.memes["worry"] += 1
        out.append("")
    return out


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True


CAUSAL_RULES: list[Rule] = [Rule("hurt", _r_hurt)]


def child_name_pool(rng: random.Random) -> tuple[str, str]:
    girl = ["Maya", "Lily", "Nora", "Zoe"]
    boy = ["Finn", "Theo", "Leo", "Max"]
    gender = rng.choice(["girl", "boy"])
    return rng.choice(girl if gender == "girl" else boy), gender


def reasonableness_ok(place: Place, offer: Offer, twist: Twist) -> bool:
    return offer.rarity >= 1 and twist.sadness >= 1 and bool(place.label)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid in PLACES:
        for oid in OFFERS:
            for tid in TWISTS:
                if reasonableness_ok(PLACES[pid], OFFERS[oid], TWISTS[tid]):
                    combos.append((pid, oid, tid))
    return combos


@dataclass
class StoryParams:
    place: str
    offer: str
    twist: str
    child: str
    gender: str
    parent: str
    seed: Optional[int] = None


PLACES = {
    "shop": Place("shop", "the butcher shop", "salt and pepper", "the clink of knives"),
    "counter": Place("counter", "the long counter", "warm bread and spice", "the tap of a block"),
}

OFFERS = {
    "bone": Offer("bone", "a soup bone", "a soup bone", "savory", 2),
    "sausage": Offer("sausage", "a sausage roll", "a sausage roll", "peppery", 2),
    "slice": Offer("slice", "a pink ham slice", "a pink ham slice", "smoky", 1),
}

TWISTS = {
    "sold_out": Twist("sold_out", "the last tray was already sold out", "no treat remained", 2),
    "dog_eats_it": Twist("dog_eats_it", "the family dog had eaten the parcel on the way home", "the prize was gone", 3),
    "wrong_wrap": Twist("wrong_wrap", "the parcel held a note, not the snack", "the surprise changed", 1),
}

DEFAULTS = [StoryParams("shop", "bone", "dog_eats_it", "Mia", "girl", "mother")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming butcher storyworld with reconciliation and a sad twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--offer", choices=OFFERS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.offer and args.twist and args.offer == "slice" and args.twist == "dog_eats_it":
        pass
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.offer is None or c[1] == args.offer)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, offer, twist = rng.choice(sorted(combos))
    child, gender = child_name_pool(rng)
    return StoryParams(place, offer, twist, args.name or child, args.gender or gender,
                       args.parent or rng.choice(["mother", "father"]))


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity("child", "character", params.gender, params.child, "child"))
    parent = world.add(Entity("parent", "character", params.parent, "the parent", "parent"))
    butcher = world.add(Entity("butcher", "character", "man", "the butcher", "butcher"))
    place = PLACES[params.place]
    offer = OFFERS[params.offer]
    twist = TWISTS[params.twist]

    child.memes["hope"] += 1
    butcher.memes["kindness"] += 1
    world.say(
        f"At {place.label}, where the air smelled of {place.scent}, a small bell sang a bright refrain."
    )
    world.say(
        f"{child.id} came in with {parent.label_word} and dreamed of {offer.phrase}; "
        f"the glass case gleamed in a silver lane."
    )
    world.para()
    world.say(
        f'"Please," said {child.id}, with cheeks gone red. "I want {offer.label} for home tonight."'
    )
    world.say(
        f"The butcher smiled, then shook {butcher.pronoun('possessive')} head. "
        f"That last one was promised to someone else, and the answer felt less than bright."
    )
    child.memes["hurt"] += 1
    butcher.memes["sadness"] += 1
    world.say(
        f"{child.id} frowned at the counter and looked at the floor; the moment felt small but sharp."
    )
    world.para()
    world.say(
        f"Then {parent.id} knelt close and said, \"We can still be kind.\" "
        f"{child.id} took a breath, and the grumpy cloud began to depart."
    )
    child.memes["sorry"] += 1
    butcher.memes["forgiven"] += 1
    world.say(
        f'{child.id} said, "I am sorry for my pout." The butcher nodded once, with a gentle grin.'
    )
    world.say(
        f'"I am sorry too," said the butcher, "for the wait and the doubt." '
        f"So the three of them mended the mood and let calmness come in."
    )
    world.para()
    if params.twist == "dog_eats_it":
        world.say(
            f"Twist in the mist: {twist.reveal}."
        )
        world.say(
            f"{child.id} stared as the parcel was gone; the nice little snack had run out of sight."
        )
        child.memes["loss"] += 2
        world.say(
            f"The family walked home with empty hands, and dinner was quieter that night."
        )
    elif params.twist == "sold_out":
        world.say(
            f"Twist in the mist: {twist.reveal}."
        )
        world.say(
            f"The butcher opened the tray, then shut it slow; there was nothing left to sell."
        )
        child.memes["loss"] += 1
        world.say(
            f"{child.id} got one small free herb sprig, but the supper dream fell through the well."
        )
    else:
        world.say(
            f"Twist in the mist: {twist.reveal}."
        )
        world.say(
            f"The paper held a note from the butcher: \"Thank you for waiting, and come back soon.\""
        )
        child.memes["softness"] += 1
        world.say(
            f"{child.id} smiled a tiny smile, though the missing snack still made the evening feel blue."
        )
    world.facts.update(child=child, parent=parent, butcher=butcher, place=place,
                       offer=offer, twist=twist, outcome=params.twist)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child that includes the word "butcher".',
        f"Tell a sad-but-kind story where {f['child'].id} visits a butcher, reconciles after a small hurt, and then a twist changes the ending.",
        f"Write a short rhyming story with reconciliation and a bad ending, set around a butcher shop.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    butcher = f["butcher"]
    offer = f["offer"]
    twist = f["twist"]
    return [
        QAItem(
            question="Why did the child feel sad?",
            answer=f"{child.id} felt sad because {butcher.label_word} could not give {child.pronoun('object')} {offer.label}. The wish was gentle, but the answer was no."
        ),
        QAItem(
            question="How did they reconcile?",
            answer=f"{child.id} apologized first, and then the butcher apologized too. Their kind words made the hurt feel smaller, even before the twist arrived."
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {twist.reveal}. It changed the ending from a hoped-for snack into a quiet loss."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does a butcher do?", "A butcher cuts and sells meat, and keeps the shop tidy and ready for customers."),
        QAItem("Why can a lost treat feel disappointing?", "A treat can be special because someone was looking forward to it. When it is gone, the day can feel emptier."),
        QAItem("What does reconcile mean?", "To reconcile means to make peace again after a disagreement or hurt feeling."),
    ]


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, O, T) :- place(P), offer(O), twist(T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid in OFFERS:
        lines.append(asp.fact("offer", oid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    if rc == 0:
        print("OK: verify passed and smoke test succeeded.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming butcher reconciliation world with a sad twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--offer", choices=OFFERS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in DEFAULTS]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


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


if __name__ == "__main__":
    main()
