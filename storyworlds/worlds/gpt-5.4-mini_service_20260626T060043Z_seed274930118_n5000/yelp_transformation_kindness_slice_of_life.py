#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/yelp_transformation_kindness_slice_of_life.py
===============================================================================================================

A small slice-of-life story world built from the seed word "yelp" with
transformation through kindness.

Premise:
- A child or small helper goes about an ordinary day.
- A brief yelp marks a tiny mishap: a prick, a spill, or a bump.
- A kind response changes the mood and the scene.
- The ending should prove the change in both meters and memes:
  hurt becomes comfort, worry becomes calm, and the day turns gentle again.

This world is deliberately compact: it keeps the variants tight so each story
reads like a believable little moment rather than a random event log.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    indoors: bool
    gives: set[str]


@dataclass
class Mishap:
    id: str
    trigger: str
    yelp: str
    hurt: str
    meter: str
    zone: str
    places: set[str]
    tags: set[str]


@dataclass
class Kindness:
    id: str
    tool: str
    action: str
    result: str
    fixs: set[str]
    kind_words: set[str]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    place: str
    mishap: str
    kindness: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "garden": Place("the garden", False, {"thorn", "bee"}),
    "kitchen": Place("the kitchen", True, {"hot_soup", "spill"}),
    "sidewalk": Place("the sidewalk", False, {"trip", "scrape"}),
    "laundry": Place("the laundry room", True, {"sock", "snap"}),
}

MISHAPS = {
    "thorn": Mishap(
        id="thorn",
        trigger="step on a tiny thorn",
        yelp="yelp",
        hurt="pricked",
        meter="pain",
        zone="foot",
        places={"garden"},
        tags={"garden", "pain", "plant"},
    ),
    "trip": Mishap(
        id="trip",
        trigger="trip on a curb",
        yelp="yelp",
        hurt="scraped",
        meter="pain",
        zone="knee",
        places={"sidewalk"},
        tags={"street", "pain"},
    ),
    "hot_soup": Mishap(
        id="hot_soup",
        trigger="brush a hot soup spoon",
        yelp="yelp",
        hurt="startled",
        meter="shock",
        zone="hand",
        places={"kitchen"},
        tags={"kitchen", "warm"},
    ),
    "snap": Mishap(
        id="snap",
        trigger="hear a hanger snap in the laundry room",
        yelp="yelp",
        hurt="shaken",
        meter="shock",
        zone="shoulder",
        places={"laundry"},
        tags={"laundry", "noise"},
    ),
}

KINDNESSES = {
    "bandage": Kindness(
        id="bandage",
        tool="a small bandage",
        action="wrap the sore spot carefully",
        result="the hurt spot felt better",
        fixs={"pain"},
        kind_words={"gentle", "care"},
    ),
    "cool_cloth": Kindness(
        id="cool_cloth",
        tool="a cool damp cloth",
        action="press the cloth softly on the hand",
        result="the surprise settled down",
        fixs={"shock"},
        kind_words={"gentle", "calm"},
    ),
    "tea": Kindness(
        id="tea",
        tool="a warm mug of tea",
        action="bring a warm mug and sit together",
        result="the room felt quiet and safe again",
        fixs={"shock", "pain"},
        kind_words={"quiet", "care"},
    ),
}

GIRL_NAMES = ["Maya", "Nora", "Lily", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Theo", "Finn", "Ben", "Leo", "Jack", "Max"]
TRAITS = ["curious", "gentle", "shy", "playful", "quiet", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for mishap_id, mishap in MISHAPS.items():
            if place_id not in mishap.places:
                continue
            for kindness_id, kind in KINDNESSES.items():
                if mishap.meter in kind.fixs:
                    out.append((place_id, mishap_id, kindness_id))
    return out


def _select_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def _select_helper(gender: str, rng: random.Random) -> str:
    return rng.choice(["mother", "father", "grandma", "grandpa"]) if gender in {"girl", "boy"} else "helper"


def explain_rejection(mishap: Mishap, kindness: Kindness, place_id: str) -> str:
    return (
        f"(No story: at {PLACES[place_id].name}, a {mishap.id} mishap and "
        f"{kindness.id} kindness do not fit together. The kindness has to match "
        f"the kind of hurt or surprise the mishap creates.)"
    )


def story_can_happen(place_id: str, mishap_id: str, kindness_id: str) -> bool:
    mishap = MISHAPS[mishap_id]
    kindness = KINDNESSES[kindness_id]
    return place_id in mishap.places and mishap.meter in kindness.fixs


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mishap and args.kindness:
        if not story_can_happen(args.place, args.mishap, args.kindness):
            raise StoryError(explain_rejection(MISHAPS[args.mishap], KINDNESSES[args.kindness], args.place))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mishap is None or c[1] == args.mishap)
              and (args.kindness is None or c[2] == args.kindness)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, mishap, kindness = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    return StoryParams(
        place=place,
        mishap=mishap,
        kindness=kindness,
        name=args.name or _select_name(gender, rng),
        gender=gender,
        helper=args.helper or _select_helper(gender, rng),
        trait=args.trait or rng.choice(TRAITS),
    )


def _apply_mishap(world: World, child: Entity, mishap: Mishap) -> None:
    child.meters[mishap.meter] = child.meters.get(mishap.meter, 0.0) + 1.0
    child.memes["surprise"] = child.memes.get("surprise", 0.0) + 1.0
    world.trace.append(f"{child.id} {mishap.trigger} and {mishap.yelp}.")

def _apply_kindness(world: World, child: Entity, helper: Entity, kindness: Kindness, mishap: Mishap) -> None:
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1.0
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1.0
    child.memes["trust"] = child.memes.get("trust", 0.0) + 1.0
    if mishap.meter in child.meters:
        child.meters[mishap.meter] = max(0.0, child.meters[mishap.meter] - 1.0)
    world.trace.append(f"{helper.id} used {kindness.tool}.")


def tell(place: Place, mishap: Mishap, kindness: Kindness, name: str, gender: str, helper_type: str, trait: str) -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={}))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_type, meters={}, memes={}))
    thing = world.add(Entity(id="tool", type="thing", label=kindness.tool, phrase=kindness.tool))

    world.say(
        f"{child.id} was a {trait} little {gender} who liked the ordinary rhythm of {place.name}."
    )
    world.say(
        f"One day, {child.id} was there with {helper.id}, taking a simple moment one step at a time."
    )

    world.para()
    _apply_mishap(world, child, mishap)
    world.say(
        f"Then {child.id} {mishap.trigger} and let out a sharp yelp."
    )
    world.say(
        f"{helper.id} turned right away, because a small yelp can make a quiet day feel very big."
    )

    world.para()
    _apply_kindness(world, child, helper, kindness, mishap)
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
    child.memes["fear"] = max(0.0, child.memes.get("fear", 0.0) - 1.0)
    world.say(
        f"{helper.id} answered with kindness, using {kindness.tool} to {kindness.action}."
    )
    world.say(
        f"Soon {kindness.result}, and {child.id}'s face changed from startled to soft and relieved."
    )
    world.say(
        f"By the end, the little moment had transformed: the yelp was gone, the worry had faded, and {child.id} was ready to smile again."
    )

    world.facts.update(
        child=child,
        helper=helper,
        tool=thing,
        mishap=mishap,
        kindness=kindness,
        place=place,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, helper, mishap, kindness = f["child"], f["helper"], f["mishap"], f["kindness"]
    return [
        f'Write a small slice-of-life story that includes the word "yelp" and shows kindness turning a rough moment gentle again.',
        f"Tell a short story about {child.id}, {helper.id}, and a {mishap.id} mishap that is soothed with {kindness.tool}.",
        f"Write a child-friendly story where a quick yelp leads to a kind response and a calm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, mishap, kindness, place = f["child"], f["helper"], f["mishap"], f["kindness"], f["place"]
    return [
        QAItem(
            question=f"Why did {child.id} yelp at {place.name}?",
            answer=f"{child.id} yelped because {child.pronoun('subject')} {mishap.trigger}, which felt {mishap.hurt}.",
        ),
        QAItem(
            question=f"What did {helper.id} do to show kindness?",
            answer=f"{helper.id} used {kindness.tool} and helped {child.id} feel better by being gentle and calm.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The hurt and surprise faded, and the moment transformed into a peaceful one where {child.id} felt safe again.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "bandage": [
        QAItem(
            question="What is a bandage for?",
            answer="A bandage is used to cover a small hurt spot so it can be protected and feel better.",
        )
    ],
    "cool_cloth": [
        QAItem(
            question="Why can a cool cloth help?",
            answer="A cool cloth can make a sore or startled feeling settle down a little.",
        )
    ],
    "tea": [
        QAItem(
            question="Why do people sometimes bring tea when someone is upset?",
            answer="A warm drink can be comforting, and comfort is part of being kind.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    kind = world.facts["kindness"].id
    return list(WORLD_KNOWLEDGE.get(kind, []))


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(parts)}")
    lines.append(f"  trace: {world.trace}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        MISHAPS[params.mishap],
        KINDNESSES[params.kindness],
        params.name,
        params.gender,
        params.helper,
        params.trait,
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life story world: a yelp, a kind response, and a small transformation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandma", "grandpa"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


ASP_RULES = r"""
place(P) :- place_fact(P).
mishap(M) :- mishap_fact(M).
kindness(K) :- kindness_fact(K).

valid(P,M,K) :- place(P), mishap(M), kindness(K), place_mishap(P,M), mishap_kindness(M,K).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place_fact", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for g in sorted(p.gives):
            lines.append(asp.fact("place_gives", pid, g))
    for mid, m in MISHAPS.items():
        lines.append(asp.fact("mishap_fact", mid))
        lines.append(asp.fact("place_mishap", list(sorted(m.places))[0], mid)) if len(m.places) == 1 else None
        lines.append(asp.fact("mishap_meter", mid, m.meter))
        lines.append(asp.fact("mishap_zone", mid, m.zone))
        for p in sorted(m.places):
            lines.append(asp.fact("place_mishap", p, mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("mishap_tag", mid, t))
    for kid, k in KINDNESSES.items():
        lines.append(asp.fact("kindness_fact", kid))
        lines.append(asp.fact("kindness_tool", kid, k.tool))
        for f in sorted(k.fixs):
            lines.append(asp.fact("kindness_fixs", kid, f))
        for w in sorted(k.kind_words):
            lines.append(asp.fact("kindness_word", kid, w))
        for m in MISHAPS:
            if MISHAPS[m].meter in k.fixs:
                lines.append(asp.fact("mishap_kindness", m, kid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def resolve_asp_story(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def explain_invalid(mishap: Mishap, kindness: Kindness, place_id: str) -> str:
    return explain_rejection(mishap, kindness, place_id)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible (place, mishap, kindness) combos:")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, mishap, kindness in valid_combos():
            params = StoryParams(
                place=place,
                mishap=mishap,
                kindness=kindness,
                name="Maya",
                gender="girl",
                helper="mother",
                trait="gentle",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < max(args.n, 1) and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.mishap} at {p.place} with {p.kindness}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
