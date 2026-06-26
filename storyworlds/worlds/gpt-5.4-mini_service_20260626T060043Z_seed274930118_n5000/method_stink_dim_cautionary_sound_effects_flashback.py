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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher", "aunt"}
        male = {"boy", "father", "man", "teacher", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoor: bool
    clue: str
    smells: set[str] = field(default_factory=set)
    affords: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    verb: str
    clue_sound: str
    flashback: str
    caution: str
    smell: str
    dim: str
    place_tags: set[str] = field(default_factory=set)
    item_tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    smell_tag: str
    place_tags: set[str] = field(default_factory=set)
    method_tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    method: str
    item: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, method: Method, item: Item) -> None:
        self.place = place
        self.method = method
        self.item = item
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
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

    def copy(self) -> "World":
        clone = World(self.place, self.method, self.item)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label, "phrase": v.phrase,
            "owner": v.owner, "caretaker": v.caretaker, "worn_by": v.worn_by, "plural": v.plural,
            "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _m(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mm(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _addm(e: Entity, key: str, n: float) -> None:
    e.meters[key] = _m(e, key) + n


def _addmm(e: Entity, key: str, n: float) -> None:
    e.memes[key] = _mm(e, key) + n


def matches(place: Place, method: Method, item: Item) -> bool:
    return (
        method.id in place.affords
        and place.id in method.place_tags
        and item.id in method.item_tags
        and place.id in item.place_tags
        and item.smell_tag == method.smell
    )


def select_compatible(place_id: Optional[str], method_id: Optional[str], item_id: Optional[str], rng: random.Random):
    combos = [(p.id, m.id, i.id) for p in PLACES.values() for m in METHODS.values() for i in ITEMS.values() if matches(p, m, i)]
    if place_id:
        combos = [c for c in combos if c[0] == place_id]
    if method_id:
        combos = [c for c in combos if c[1] == method_id]
    if item_id:
        combos = [c for c in combos if c[2] == item_id]
    if not combos:
        raise StoryError("No valid whodunit combination matches the given options.")
    return rng.choice(sorted(combos))


def _culprit_method_reveal(world: World) -> None:
    culprit = world.get("culprit")
    helper = world.get("helper")
    culprit.meters["stink"] = culprit.meters.get("stink", 0.0) + 1
    culprit.meters["dim"] = culprit.meters.get("dim", 0.0) + 1
    helper.memes["suspicious"] = helper.memes.get("suspicious", 0.0) + 1


def _flashback(world: World) -> None:
    world.say(f"Flashback: {world.method.flashback}")
    world.say(f"{world.method.caution}")


def tell_story(world: World) -> World:
    hero = world.add(Entity(id="hero", kind="character", type="boy", label=world.facts["hero_name"]))
    helper = world.add(Entity(id="helper", kind="character", type="girl", label=world.facts["helper_name"]))
    culprit = world.add(Entity(id="culprit", kind="character", type="cat", label="Milo"))
    item = world.add(Entity(id="item", type="thing", label=world.item.label, phrase=world.item.phrase, owner=culprit.id))
    culprit.worn_by = None

    hero.memes["curiosity"] = 1
    helper.memes["care"] = 1

    world.say(f"{hero.label} and {helper.label} went into {world.place.label}.")
    world.say(f"Something was wrong: the room felt dim, and a stink-dim smell hung in the air.")
    world.say(f"{hero.label} sniffed. \"{world.method.clue_sound}!\" he said. \"That is a clue.\"")
    world.say(f"{helper.label} pointed at the floor. \"Let's use the {world.method.label} method,\" she said.")
    world.say(f"They checked the {world.place.clue} and followed the smell to {item.phrase}.")
    _flashback(world)
    world.para()
    world.say(f"{hero.label} remembered the last time {culprit.label} had carried {item.phrase}.")
    world.say(f"{world.method.clue_sound}! The clue fit: {culprit.label} had hidden the {item.label} where it could warm up and stink.")
    world.say(f"{helper.label} said, \"Caution: next time, put it away where it stays cool.\"")
    world.say(f"{hero.label} opened the bag, and the bad smell finally drifted out.")
    world.say(f"At last, the mystery was solved. The room was still a little dim, but it no longer smelled stink-dim.")
    culprit.meters["stink"] = 0.0
    culprit.meters["dim"] = 0.0
    helper.memes["relief"] = 1
    hero.memes["pride"] = 1
    world.facts.update(hero=hero, helper=helper, culprit=culprit, item=item)
    return world


PLACES = {
    "hall": Place(id="hall", label="the hallway", indoor=True, clue="shoe rack", smells={"stink"}, affords={"sniff", "search"}),
    "kitchen": Place(id="kitchen", label="the kitchen", indoor=True, clue="trash bin", smells={"stink"}, affords={"sniff", "search"}),
    "shed": Place(id="shed", label="the shed", indoor=True, clue="tool shelf", smells={"stink"}, affords={"sniff", "search"}),
}

METHODS = {
    "sniffing": Method(
        id="sniffing",
        label="sniffing",
        verb="sniff",
        clue_sound="sniff-sniff",
        flashback="Earlier, Milo had pushed the lunch bag behind the shelf and shut the lid tight.",
        caution="\"Don't leave food in a warm place,\" the helper warned. \"It can turn stinky fast.\"",
        smell="stink",
        dim="dim",
        place_tags={"hall", "kitchen", "shed"},
        item_tags={"lunch", "fish", "cheese"},
    ),
    "peeking": Method(
        id="peeking",
        label="peeking",
        verb="peek",
        clue_sound="peep-peep",
        flashback="Earlier, the cat had crouched by the bag while the door was half open.",
        caution="\"Look before you close the door,\" the helper said. \"A clue can hide in plain sight.\"",
        smell="stink",
        dim="dim",
        place_tags={"hall", "kitchen", "shed"},
        item_tags={"lunch", "fish", "cheese"},
    ),
    "listening": Method(
        id="listening",
        label="listening",
        verb="listen",
        clue_sound="tap-tap",
        flashback="Earlier, the hero heard a tiny clink when the container slipped under the bench.",
        caution="\"Be gentle with mystery clues,\" the helper said. \"A loud move can break the answer.\"",
        smell="stink",
        dim="dim",
        place_tags={"hall", "kitchen", "shed"},
        item_tags={"lunch", "fish", "cheese"},
    ),
}

ITEMS = {
    "lunch": Item(id="lunch", label="lunch", phrase="the lunch box", smell_tag="stink", place_tags={"hall", "kitchen"}, method_tags={"sniffing", "peeking", "listening"}),
    "fish": Item(id="fish", label="fish", phrase="the fish snack", smell_tag="stink", place_tags={"kitchen", "shed"}, method_tags={"sniffing", "peeking", "listening"}),
    "cheese": Item(id="cheese", label="cheese", phrase="the cheese wedge", smell_tag="stink", place_tags={"hall", "kitchen", "shed"}, method_tags={"sniffing", "peeking", "listening"}),
}

HERO_NAMES = ["Noah", "Maya", "Ivy", "Theo", "Lena", "Owen"]
HELPER_NAMES = ["June", "Aria", "Max", "Nia", "Ezra", "Ruth"]


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        if p.indoor:
            lines.append(asp.fact("indoor", p.id))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", p.id, a))
    for m in METHODS.values():
        lines.append(asp.fact("method", m.id))
        lines.append(asp.fact("method_smell", m.id, m.smell))
        for t in sorted(m.place_tags):
            lines.append(asp.fact("usable_in", m.id, t))
    for i in ITEMS.values():
        lines.append(asp.fact("item", i.id))
        lines.append(asp.fact("item_smell", i.id, i.smell_tag))
        for t in sorted(i.place_tags):
            lines.append(asp.fact("item_place", i.id, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, M, I) :- place(P), method(M), item(I), affords(P, M), usable_in(M, P), item_place(I, P), item_smell(I, S), method_smell(M, S).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return sorted((p.id, m.id, i.id) for p in PLACES.values() for m in METHODS.values() for i in ITEMS.values() if matches(p, m, i))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python valid_combos():")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly whodunit about a stink-dim mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
    combo = select_compatible(args.place, args.method, args.item, rng)
    place, method, item = combo
    return StoryParams(
        place=place,
        method=method,
        item=item,
        hero_name=args.name or rng.choice(HERO_NAMES),
        helper_name=args.helper_name or rng.choice(HELPER_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    method = METHODS[params.method]
    item = ITEMS[params.item]
    world = tell_story(World(place, method, item))
    world.facts.update(hero_name=params.hero_name, helper_name=params.helper_name)
    story = world.render()
    prompts = [
        f"Write a short whodunit for a young child about a stink-dim mystery using the method '{method.id}'.",
        f"Tell a gentle mystery story where {params.hero_name} and {params.helper_name} solve a smelly clue with a flashback.",
        f"Write a simple story that includes a cautionary note and the sound effect {method.clue_sound}.",
    ]
    story_qa = [
        QAItem(
            question=f"Who solved the mystery in {place.label}?",
            answer=f"{params.hero_name} and {params.helper_name} solved it together after following the clue and the smell.",
        ),
        QAItem(
            question="What sound clue helped them investigate?",
            answer=f"They heard {method.clue_sound}, which pointed them toward the hidden {item.label}.",
        ),
        QAItem(
            question="What did the flashback show?",
            answer=f"It showed that Milo had hidden {item.phrase} earlier, which is why the room smelled stink-dim.",
        ),
    ]
    world_qa = [
        QAItem(question="What is a cautionary note?", answer="A cautionary note is a warning that helps someone stay safe or avoid a mistake."),
        QAItem(question="What is a flashback?", answer="A flashback is a story moment that shows something that happened earlier."),
        QAItem(question="What are sound effects in a story?", answer="Sound effects are little words like sniff-sniff or tap-tap that help a reader hear the action."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], ""]
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
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
    StoryParams(place="kitchen", method="sniffing", item="lunch", hero_name="Maya", helper_name="June"),
    StoryParams(place="hall", method="peeking", item="cheese", hero_name="Noah", helper_name="Ruth"),
    StoryParams(place="shed", method="listening", item="fish", hero_name="Ivy", helper_name="Max"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for p, m, i in triples:
            print(f"  {p:8} {m:10} {i:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.method} in {p.place} (item: {p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
