#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/odor_discern_neighborhood_park_happy_ending_humor.py
============================================================================================================================

A small slice-of-life storyworld set in a neighborhood park.

Premise:
- A child and parent visit the neighborhood park.
- A strange odor drifts across the playground.
- The child and parent try to discern where it is coming from.
- They find the source, fix it with a simple, kind action, and end with a
  happy, lightly humorous image.

This script follows the Storyweavers storyworld contract:
- standalone stdlib script
- typed entities with meters and memes
- lazy ASP import only inside ASP helpers
- Python reasonableness gate plus inline ASP twin
- supports default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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

ODOR_THRESHOLD = 1.0
DISCERN_THRESHOLD = 1.0


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    name: str
    affords: set[str] = field(default_factory=set)
    neighborhood: str = "neighborhood park"


@dataclass
class OdorSource:
    id: str
    label: str
    phrase: str
    odor_kind: str
    location: str
    fix: str
    humor_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    source: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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

        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SOURCES = {
    "trash": OdorSource(
        id="trash",
        label="trash can",
        phrase="a wobbly trash can near the swings",
        odor_kind="stinky",
        location="near the swings",
        fix="put the lid back on and move the bag to the bin",
        humor_line="even the picnic ants seemed to point and whisper, 'Not that one!'",
        tags={"odor", "cleanup", "humor"},
    ),
    "snack": OdorSource(
        id="snack",
        label="lunch bag",
        phrase="a dropped lunch bag under the bench",
        odor_kind="sour",
        location="under the bench",
        fix="pick it up, seal it, and toss the old banana peel",
        humor_line="the banana peel looked offended that it had become the main character",
        tags={"odor", "snack", "humor"},
    ),
    "dog": OdorSource(
        id="dog",
        label="dog puddle",
        phrase="a muddy patch where a dog had rolled",
        odor_kind="musky",
        location="by the path",
        fix="tell the dog owner, then step around it and wash hands later",
        humor_line="the dog wore the proud face of someone who had invented the smell on purpose",
        tags={"odor", "animal", "humor"},
    ),
}

PEOPLE = {
    "girl": ["Maya", "Lily", "Nora", "Zoe", "Mia"],
    "boy": ["Finn", "Leo", "Theo", "Ben", "Sam"],
}

TRAITS = ["curious", "cheerful", "careful", "playful", "quiet", "bright"]


def valid_sources() -> list[str]:
    return list(SOURCES.keys())


def odor_is_noticeable(src: OdorSource) -> bool:
    return src.id in SOURCES and src.odor_kind in {"stinky", "sour", "musky"}


def should_discern(src: OdorSource) -> bool:
    return odor_is_noticeable(src)


def build_world(params: StoryParams) -> World:
    place = Place(id="park", name="the neighborhood park", affords={"walking", "play", "sniffing"})
    world = World(place)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"odor": 0.0},
        memes={"curiosity": 1.0, "joy": 1.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        meters={"odor": 0.0},
        memes={"calm": 1.0, "discern": 1.0},
    ))
    source = SOURCES[params.source]
    culprit = world.add(Entity(
        id="source",
        kind="thing",
        type=source.label,
        label=source.label,
        phrase=source.phrase,
        meters={"odor": 2.0},
        memes={"embarrass": 0.0},
    ))
    bin_ = world.add(Entity(
        id="bin",
        kind="thing",
        type="bin",
        label="trash bin",
        phrase="the park trash bin",
        meters={"odor": 0.0},
    ))
    world.facts.update(child=child, parent=parent, source=source, culprit=culprit, bin=bin_, trait=params.trait)
    return world


def setup_story(world: World) -> None:
    c: Entity = world.facts["child"]  # type: ignore[assignment]
    p: Entity = world.facts["parent"]  # type: ignore[assignment]
    s: OdorSource = world.facts["source"]  # type: ignore[assignment]
    world.say(
        f"On a bright afternoon at {world.place.name}, {c.id} wandered from the slide to the sandbox "
        f"with {p.label_word if hasattr(p, 'label_word') else p.noun()} beside {c.pronoun('object')}."
    )
    world.say(
        f"{c.id} was a {world.facts['trait']} little {c.type} who liked noticing small things, "
        f"like bees, chalk lines, and crooked hats."
    )
    world.say(
        f"Then a funny odor drifted over from {s.location}, and {c.id} made a face so serious it looked almost polite."
    )


def detect_odor(world: World) -> None:
    c: Entity = world.facts["child"]  # type: ignore[assignment]
    p: Entity = world.facts["parent"]  # type: ignore[assignment]
    s: OdorSource = world.facts["source"]  # type: ignore[assignment]
    c.meters["odor"] += 1.0
    c.memes["curiosity"] += 1.0
    p.memes["discern"] += 1.0
    world.say(
        f"{c.id} sniffed once, then twice. {c.pronoun().capitalize()} could tell the smell was strong, "
        f"but not yet where it came from."
    )
    world.say(
        f"{p.label if p.label else 'the parent'} looked around carefully, because {p.pronoun('subject')} could discern "
        f"that the odor was real and close by."
    )
    world.say(
        f'"Let’s follow our noses," {p.pronoun("subject")} said, and {c.id} giggled because that sounded like a tiny parade.'
    )
    world.facts["odor_detected"] = True
    world.facts["source_hint"] = s.location


def find_source(world: World) -> None:
    c: Entity = world.facts["child"]  # type: ignore[assignment]
    p: Entity = world.facts["parent"]  # type: ignore[assignment]
    s: OdorSource = world.facts["source"]  # type: ignore[assignment]
    if not world.facts.get("odor_detected"):
        raise StoryError("cannot find the source before the odor is detected")
    world.say(
        f"Near the swings, {c.id} spotted {s.phrase}. {c.id} pointed, and {p.pronoun('subject')} smiled, "
        f"because the clue finally matched the smell."
    )
    world.say(
        f"It turned out the mystery odor came from {s.label}, and the answer was simple enough to feel almost silly."
    )


def fix_source(world: World) -> None:
    c: Entity = world.facts["child"]  # type: ignore[assignment]
    p: Entity = world.facts["parent"]  # type: ignore[assignment]
    s: OdorSource = world.facts["source"]  # type: ignore[assignment]
    bin_: Entity = world.facts["bin"]  # type: ignore[assignment]
    bin_.meters["odor"] = 0.0
    world.say(
        f"{p.id} helped {c.id} tie the loose bag, put the lid back on, and carry the messy bit to {bin_.label}."
    )
    world.say(
        f"{s.fix.capitalize()}. The smell began to fade, as if it had been embarrassed to be caught."
    )
    world.say(s.humor_line)
    world.facts["fixed"] = True


def happy_ending(world: World) -> None:
    c: Entity = world.facts["child"]  # type: ignore[assignment]
    p: Entity = world.facts["parent"]  # type: ignore[assignment]
    world.say(
        f"After that, the neighborhood park smelled like sunshine again. {c.id} ran back to the swings, "
        f"and {p.label if p.label else 'the parent'} laughed at how a bad smell had turned into a small adventure."
    )
    world.say(
        f"By the time they left, {c.id} was smiling, the air was fresh, and the park looked ordinary in the nicest way."
    )


def tell_story(world: World) -> World:
    setup_story(world)
    world.para()
    detect_odor(world)
    find_source(world)
    world.para()
    fix_source(world)
    happy_ending(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p: Entity = world.facts["parent"]  # type: ignore[assignment]
    c: Entity = world.facts["child"]  # type: ignore[assignment]
    s: OdorSource = world.facts["source"]  # type: ignore[assignment]
    return [
        f"Write a slice-of-life story for a young child about a mysterious odor in a neighborhood park.",
        f"Tell a gentle humorous story where {c.id} and {p.label if p.label else 'a parent'} discern where a smell is coming from.",
        f"Write a happy ending story that starts with an odd odor and ends with the park feeling pleasant again.",
        f"Create a short child-friendly story about {s.label} and how a family solves the smell without a big fuss.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c: Entity = world.facts["child"]  # type: ignore[assignment]
    p: Entity = world.facts["parent"]  # type: ignore[assignment]
    s: OdorSource = world.facts["source"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question="Where does the story happen?",
            answer=f"It happens at the neighborhood park, where {c.id} and {p.label if p.label else 'the parent'} are spending a normal day together.",
        ),
        QAItem(
            question=f"What did {c.id} notice first?",
            answer=f"{c.id} noticed a strange odor drifting through the park before {c.id} knew exactly where it came from.",
        ),
        QAItem(
            question="What was the smell source?",
            answer=f"The smell came from {s.phrase}, which turned out to be the little mystery everyone had to discern.",
        ),
        QAItem(
            question="How was the problem fixed?",
            answer=f"They tidied the source by following {s.fix.lower()}, and that made the odor fade away.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily, with {c.id} smiling, the park smelling better, and everyone laughing at the tiny mystery.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "odor": [
        (
            "What is an odor?",
            "An odor is a smell you notice with your nose. Some odors are pleasant, and some are not.",
        )
    ],
    "discern": [
        (
            "What does discern mean?",
            "To discern something means to notice it clearly or figure out what it is by paying close attention.",
        )
    ],
    "cleanup": [
        (
            "Why do people clean up a park?",
            "People clean up a park so it stays pleasant, safe, and nice for everyone to use.",
        )
    ],
    "snack": [
        (
            "What should you do with old food outside?",
            "Old food should be thrown away or put away so it does not smell bad and attract bugs.",
        )
    ],
    "animal": [
        (
            "Why can a dog smell funny after rolling in mud?",
            "Mud, grass, and water can leave a strong smell on a dog, even when the dog looks very proud of it.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    s: OdorSource = world.facts["source"]  # type: ignore[assignment]
    tags = set(s.tags) | {"odor"}
    out: list[QAItem] = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


ASP_RULES = r"""
odor_noticeable(S) :- source(S), odor_kind(S, K), K = stinky.
odor_noticeable(S) :- source(S), odor_kind(S, K), K = sour.
odor_noticeable(S) :- source(S), odor_kind(S, K), K = musky.

needs_discern(S) :- odor_noticeable(S).

valid_story(S) :- source(S), odor_noticeable(S), fixable(S), humorous(S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, src in SOURCES.items():
        lines.append(asp.fact("source", sid))
        lines.append(asp.fact("odor_kind", sid, src.odor_kind))
        lines.append(asp.fact("fixable", sid))
        lines.append(asp.fact("humorous", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_sources() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {sid for sid, src in SOURCES.items() if odor_is_noticeable(src) and should_discern(src)}
    cl = {a[0] for a in asp_valid_sources()}
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} sources).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life park storyworld about odor, discernment, and a happy ending.")
    ap.add_argument("--source", choices=valid_sources())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    source = args.source or rng.choice(valid_sources())
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(PEOPLE[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    src = SOURCES[source]
    if not odor_is_noticeable(src):
        raise StoryError("the selected source does not make a noticeable odor")
    return StoryParams(source=source, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
    StoryParams(source="trash", name="Maya", gender="girl", parent="mother", trait="curious"),
    StoryParams(source="snack", name="Finn", gender="boy", parent="father", trait="playful"),
    StoryParams(source="dog", name="Nora", gender="girl", parent="father", trait="careful"),
]


def asp_valid_sources_report() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    return [a[0] for a in asp.atoms(model, "valid_story")]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid_sources_report()
        print(f"{len(vals)} valid sources:")
        for v in vals:
            print(f"  {v}")
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
            except StoryError as e:
                print(e)
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
            header = f"### {p.name}: {p.source}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
