#!/usr/bin/env python3
"""
storyworlds/worlds/siamese_rhyme_foreshadowing_rhyming_story.py
===============================================================

A tiny storyworld for a rhyming, foreshadowed tale about a siamese cat.

Premise:
- A little siamese cat wants something shiny, cozy, or playful.
- A clue early in the story foreshadows a later problem.
- A helper or the cat itself solves the problem in a gentle way.
- The ending image proves what changed.

This world keeps the story child-facing and small, while still driving prose
from a stateful simulation with physical meters and emotional memes.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    helper_of: Optional[str] = None
    worn_by: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"cat", "kitten"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    indoors: bool = False
    has_window: bool = False
    has_table: bool = False
    has_bed: bool = False
    has_rain: bool = False
    has_lamp: bool = False


@dataclass
class Want:
    id: str
    verb: str
    noun: str
    rhyme_a: str
    rhyme_b: str
    clue: str
    risk: str
    spoil: str
    fix: str
    ending_image: str
    mess_kind: str
    risk_meter: str
    zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    want: str
    name: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


PLACES = {
    "window_room": Place("the window room", indoors=True, has_window=True, has_table=True, has_lamp=True),
    "garden": Place("the garden", indoors=False, has_rain=True),
    "bedroom": Place("the bedroom", indoors=True, has_bed=True, has_window=True),
}

WANTS = {
    "ribbon": Want(
        id="ribbon",
        verb="chase the ribbon",
        noun="ribbon",
        rhyme_a="twitch and swish",
        rhyme_b="dash and swish",
        clue="A loose red ribbon lay near the window sill.",
        risk="it might slip into the rain and get soggy",
        spoil="soggy and stuck",
        fix="close the window and keep the ribbon on the table",
        ending_image="the ribbon stayed bright and dry",
        mess_kind="wet",
        risk_meter="wetness",
        zone="window_sill",
        tags={"ribbon", "window"},
    ),
    "milk": Want(
        id="milk",
        verb="sip a bowl of milk",
        noun="milk",
        rhyme_a="drip and sip",
        rhyme_b="slip and sip",
        clue="A little bowl sat near the bed, white as moonlight.",
        risk="it might tip and spill across the blanket",
        spoil="spilled and milky",
        fix="carry the bowl to the table first",
        ending_image="the bowl rested neat and still",
        mess_kind="spill",
        risk_meter="spillness",
        zone="bed",
        tags={"milk", "bed"},
    ),
    "ball": Want(
        id="ball",
        verb="bat the blue ball",
        noun="ball",
        rhyme_a="roll and toll",
        rhyme_b="bounce and pounce",
        clue="A tiny blue ball waited beside the lamp.",
        risk="it might roll under the couch and hide",
        spoil="lost from sight",
        fix="move it to the open rug before play",
        ending_image="the ball bounced in plain view",
        mess_kind="lost",
        risk_meter="wanderness",
        zone="floor",
        tags={"ball", "play"},
    ),
}

NAMES = ["Mimi", "Nori", "Kiki", "Suri", "Lumi", "Tavi"]
HELPERS = ["mother", "father", "child", "friend"]


class RhymeWorld:
    pass


def rhyme_line(a: str, b: str) -> str:
    return f"{a} ... {b}."


def tell(place: Place, want: Want, name: str, helper: str) -> World:
    world = World(place)
    cat = world.add(Entity(
        id=name,
        kind="character",
        type="cat",
        label="siamese cat",
        phrase=f"a small siamese cat named {name}",
        meters={want.risk_meter: 0.0, "joy": 0.0, "safe": 0.0},
        memes={"curiosity": 1.0, "hope": 1.0},
    ))
    helper_ent = world.add(Entity(
        id=helper,
        kind="character",
        type=helper,
        label=helper,
        meters={"calm": 1.0},
        memes={"care": 1.0},
    ))
    object_id = want.id
    obj = world.add(Entity(
        id=object_id,
        kind="thing",
        type=want.id,
        label=want.noun,
        phrase=want.noun,
        owner=cat.id,
        meters={want.risk_meter: 0.0},
    ))

    world.facts.update(cat=cat, helper=helper_ent, obj=obj, want=want, place=place)

    # Act 1: setup with rhyme and foreshadowing.
    world.say(f"{cat.phrase} had fur like cream and cinnamon ice.")
    world.say(f"{want.clue} That was a clue, small but nice.")
    world.say(f"{cat.id} liked to {want.verb}; the wish went zoom, then went quick.")
    world.say(f"It loved the sound of {want.rhyme_a}, soft as a stick.")
    world.para()

    # Act 2: tension turns from clue into problem.
    world.say(f"{cat.id} peered around and gave a sniff.")
    world.say(f"The little clue said trouble might arrive with a little biff.")
    world.say(f"When {cat.id} tried to play, the risk was plain to see:")
    world.say(f"{want.risk}, and that would not be kind to {want.noun}.")
    world.say(f"So {helper_ent.label} smiled and said, “Let's make it safe and bright.”")
    world.para()

    # Act 3: fix and ending image.
    world.say(f"They chose to {want.fix}.")
    cat.meters["safe"] += 1.0
    cat.meters["joy"] += 1.0
    cat.memes["curiosity"] += 0.5
    obj.meters[want.risk_meter] = 0.0
    world.say(f"Then {cat.id} could {want.verb} with a happy little glide.")
    world.say(f"At the end, {want.ending_image}, and {cat.id} sat warm inside.")
    world.say(f"{want.rhyme_b} made the day feel neat and sweet.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cat = f["cat"]
    want = f["want"]
    place = f["place"].name
    return [
        f'Write a short rhyming story for a child about a siamese cat named {cat.id} at {place}.',
        f"Tell a foreshadowing story where {cat.id} notices a small clue before trying to {want.verb}.",
        f'Write a gentle cat story that uses the word "{want.noun}" and ends with a safe, happy fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cat: Entity = f["cat"]
    want: Want = f["want"]
    place: Place = f["place"]
    helper: Entity = f["helper"]
    return [
        QAItem(
            question=f"Who is the story about at {place.name}?",
            answer=f"The story is about {cat.phrase}.",
        ),
        QAItem(
            question=f"What clue foreshadowed trouble before {cat.id} tried to {want.verb}?",
            answer=f"{want.clue} It hinted that {want.risk}.",
        ),
        QAItem(
            question=f"Who helped {cat.id} keep the {want.noun} safe?",
            answer=f"{helper.label} helped by choosing to {want.fix}.",
        ),
        QAItem(
            question=f"How did the story end after the fix?",
            answer=f"It ended with {want.ending_image}, so {cat.id} could stay happy and safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a siamese cat?",
            answer="A siamese cat is a kind of cat with short fur and a light body with darker ears, paws, face, or tail.",
        ),
        QAItem(
            question="What does foreshadowing mean in a story?",
            answer="Foreshadowing is when a story gives a little clue early on that hints at something important later.",
        ),
        QAItem(
            question="What is rhyme?",
            answer="Rhyme is when words sound alike at the end, like cat and hat.",
        ),
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
cat(C) :- siamese_cat(C).
want(W) :- desire(W).
foreshadow(C, W) :- clue(C, W).
at_risk(W) :- clue_risk(W).
safe_resolution(C, W) :- foreshadow(C, W), fix(W).
valid_story(P, W, H) :- place(P), want(W), helper(H), safe_resolution(cat, W).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        if p.has_window:
            lines.append(asp.fact("windowed", pid))
        if p.has_table:
            lines.append(asp.fact("table", pid))
        if p.has_bed:
            lines.append(asp.fact("bed", pid))
        if p.has_rain:
            lines.append(asp.fact("rain_nearby", pid))
        if p.has_lamp:
            lines.append(asp.fact("lamp", pid))
    for wid, w in WANTS.items():
        lines.append(asp.fact("desire", wid))
        lines.append(asp.fact("clue", "cat", wid))
        lines.append(asp.fact("clue_risk", wid))
        lines.append(asp.fact("fix", wid))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    lines.append(asp.fact("siamese_cat", "cat"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    ok = bool(asp_valid_stories())
    if ok:
        print("OK: ASP twin produced at least one valid story shape.")
        return 0
    print("MISMATCH: ASP twin produced no valid stories.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming storyworld about a siamese cat.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--want", choices=WANTS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
    place = args.place or rng.choice(list(PLACES))
    want = args.want or rng.choice(list(WANTS))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, want=want, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], WANTS[params.want], params.name, params.helper)
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
    StoryParams(place="window_room", want="ribbon", name="Mimi", helper="mother"),
    StoryParams(place="bedroom", want="milk", name="Nori", helper="father"),
    StoryParams(place="window_room", want="ball", name="Kiki", helper="friend"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_stories():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
            header = f"### {p.name}: {p.want} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
