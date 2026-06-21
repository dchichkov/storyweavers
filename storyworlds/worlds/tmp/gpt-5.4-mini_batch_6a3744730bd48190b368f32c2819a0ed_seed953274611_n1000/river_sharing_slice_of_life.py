#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/river_sharing_slice_of_life.py
==============================================================

A small slice-of-life storyworld about children by a river, where one child
wants to keep something all to themselves, a gentle moment of sharing changes
the mood, and the day ends with a calmer, brighter feeling.

The world is deliberately tiny: a riverbank outing, a few shareable objects,
a simple reasonableness gate, and an ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
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
MOOD_GOOD = 1.5
MOOD_TENSE = -0.5


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    near_water: bool = False
    peaceful: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Shareable:
    id: str
    label: str
    phrase: str
    plural: bool = False
    comfort: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Offer:
    id: str
    sense: int
    helps: str
    text: str
    tags: set[str] = field(default_factory=set)


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
        import copy as _copy
        clone = World()
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    host = world.entities.get("host")
    helper = world.entities.get("helper")
    item = world.entities.get("item")
    river = world.entities.get("river")
    if not (host and helper and item and river):
        return out
    if host.meters["holding"] < THRESHOLD or helper.meters["asking"] < THRESHOLD:
        return out
    if (host.id, item.id) in world.fired:
        return out
    world.fired.add((host.id, item.id))
    host.memes["generous"] += 1
    helper.memes["warmth"] += 1
    river.memes["calm"] += 1
    out.append("__share__")
    return out


def _r_mood(world: World) -> list[str]:
    out: list[str] = []
    river = world.entities.get("river")
    host = world.entities.get("host")
    helper = world.entities.get("helper")
    if not (host and helper and river):
        return out
    if river.memes["calm"] < THRESHOLD:
        return out
    sig = ("mood",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    host.memes["peace"] += 1
    helper.memes["peace"] += 1
    out.append("__mood__")
    return out


CAUSAL_RULES = [Rule("share", "social", _r_share), Rule("mood", "emotional", _r_mood)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def kind_choice(place: Place, item: Shareable) -> bool:
    return place.near_water and item.comfort


def sensible_offers() -> list[Offer]:
    return [o for o in OFFERS.values() if o.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for iid, item in ITEMS.items():
            for oid, offer in OFFERS.items():
                if kind_choice(place, item) and offer.sense >= 2:
                    combos.append((pid, iid, oid))
    return combos


@dataclass
class StoryParams:
    place: str
    item: str
    offer: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str = "mother"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life river sharing storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--offer", choices=OFFERS)
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.item and args.place and not kind_choice(PLACES[args.place], ITEMS[args.item]):
        raise StoryError("This item doesn't fit the riverbank sharing story.")
    if args.offer and OFFERS[args.offer].sense < 2:
        raise StoryError("That offer is too flimsy for a sensible sharing story.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.offer is None or c[2] == args.offer)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, offer = rng.choice(sorted(combos))
    c1, g1 = rng.choice(NAMES)
    c2, g2 = rng.choice([x for x in NAMES if x[0] != c1])
    return StoryParams(
        place=place, item=item, offer=offer,
        child1=c1, child1_gender=g1, child2=c2, child2_gender=g2,
        parent=args.parent or rng.choice(["mother", "father"]),
    )


def tell(params: StoryParams) -> World:
    world = World()
    place = world.add(Entity(id="river", kind="place", type="place", label=PLACES[params.place].label))
    host = world.add(Entity(id="host", kind="character", type=params.child1_gender, label=params.child1))
    helper = world.add(Entity(id="helper", kind="character", type=params.child2_gender, label=params.child2))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label="the parent"))
    item = world.add(Entity(id="item", kind="thing", type="thing", label=ITEMS[params.item].label))
    host.meters["holding"] = 1
    helper.meters["asking"] = 1
    host.memes["possessive"] = 1
    world.say(f"By the river, {params.child1} and {params.child2} sat in the soft morning light.")
    world.say(f"They had {ITEMS[params.item].phrase}, and the day felt quiet and easy.")
    world.para()
    world.say(f"{params.child1} wanted to keep it close, but {params.child2} reached out with a shy smile.")
    world.say(f'"Can I have a turn?" {params.child2} asked. {params.child1} looked at the river and then at the {ITEMS[params.item].label}.')
    if params.offer == "turn":
        world.say(f"{params.child1} hesitated for a moment, then said, "{params.child2}, you can hold it next."")
    elif params.offer == "half":
        world.say(f"{params.child1} nodded and split the time in half, so each child could use it a little.")
    else:
        world.say(f"{params.child1} moved closer and held the {ITEMS[params.item].label} between them, ready to share.")
    propagate(world, narrate=False)
    world.para()
    host.meters["holding"] = 0
    helper.meters["holding"] = 1
    host.memes["content"] += 1
    helper.memes["content"] += 1
    world.say(f"The parent smiled and sat beside them, listening to the river water move over the stones.")
    world.say(f"Before long, both children were using the {ITEMS[params.item].label} together, and the riverbank felt peaceful again.")
    world.say(f"By the end, {params.child1} was no longer guarding the {ITEMS[params.item].label} alone; {params.child2} was laughing too.")
    world.facts.update(place=PLACES[params.place], item=ITEMS[params.item], offer=OFFERS[params.offer],
                       child1=host, child2=helper, parent=parent, river=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story about two children by a river, where sharing a {f["item"].label} changes the mood.',
        f"Tell a gentle story where {f['child1'].label} learns to share near the river and everyone ends up calmer.",
        f'Write a small everyday story that includes the word "river" and ends with a kind act of sharing.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c1, c2, item = f["child1"], f["child2"], f["item"]
    return [
        ("Where does the story happen?", f"It happens by the river, where the children are sitting in a quiet place."),
        ("What did the children share?", f"They shared {item.phrase}. That gave both children a turn and turned the moment gentler."),
        ("How did the story end?", f"It ended with both children using the {item.label} together and feeling calmer by the water."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a river?", "A river is a long, moving body of water that flows through land."),
        ("Why do people share?", "People share so everyone can have a turn and feel included."),
        ("What does sharing feel like?", "Sharing can feel kind and fair, and it often makes a small problem easier."),
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
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


PLACES = {
    "bank": Place(id="bank", label="the grassy riverbank", near_water=True, tags={"river"}),
    "dock": Place(id="dock", label="the little dock by the river", near_water=True, tags={"river"}),
    "path": Place(id="path", label="the path beside the river", near_water=True, tags={"river"}),
}
ITEMS = {
    "ball": Shareable(id="ball", label="red ball", phrase="a red ball", comfort=True, tags={"share"}),
    "book": Shareable(id="book", label="picture book", phrase="a picture book with bright pages", comfort=True, tags={"share"}),
    "kite": Shareable(id="kite", label="paper kite", phrase="a paper kite", comfort=True, tags={"share"}),
}
OFFERS = {
    "turn": Offer(id="turn", sense=3, helps="turn-taking", text="took turns", tags={"share"}),
    "half": Offer(id="half", sense=2, helps="splitting time", text="shared it in half", tags={"share"}),
    "together": Offer(id="together", sense=3, helps="doing it together", text="shared it together", tags={"share"}),
}
NAMES = [("Mia", "girl"), ("Luca", "boy"), ("Noah", "boy"), ("Ella", "girl"), ("Sami", "boy"), ("Nora", "girl")]

CURATED = [
    StoryParams(place="bank", item="ball", offer="turn", child1="Mia", child1_gender="girl", child2="Noah", child2_gender="boy", parent="mother"),
    StoryParams(place="dock", item="book", offer="together", child1="Ella", child1_gender="girl", child2="Luca", child2_gender="boy", parent="father"),
    StoryParams(place="path", item="kite", offer="half", child1="Sami", child1_gender="boy", child2="Nora", child2_gender="girl", parent="mother"),
]


ASP_RULES = r"""
valid(P,I,O) :- place(P), item(I), offer(O), near_water(P), comfort(I), sense(O,S), S >= 2.
"""


def asp_facts() -> str:
    import asp
    out = []
    for pid, p in PLACES.items():
        out.append(asp.fact("place", pid))
        if p.near_water:
            out.append(asp.fact("near_water", pid))
    for iid, item in ITEMS.items():
        out.append(asp.fact("item", iid))
        if item.comfort:
            out.append(asp.fact("comfort", iid))
    for oid, offer in OFFERS.items():
        out.append(asp.fact("offer", oid))
        out.append(asp.fact("sense", oid, offer.sense))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, item=None, offer=None, parent=None), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    else:
        print("OK: ASP parity and generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.item not in ITEMS or params.offer not in OFFERS:
        raise StoryError("Invalid params.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            sample = generate(p)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
