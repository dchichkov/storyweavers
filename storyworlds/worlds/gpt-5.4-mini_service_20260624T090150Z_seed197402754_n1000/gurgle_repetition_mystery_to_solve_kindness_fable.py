#!/usr/bin/env python3
"""
A small fable-like storyworld about a repeated gurgle, a mystery to solve, and
a kind solution.

The story premise:
- A calm pond begins to make a strange gurgle again and again.
- The animals in the meadow worry about what is causing it.
- A kind helper investigates, discovers a simple cause, and fixes it gently.
- The repeated sound changes from worrying to pleasant by the end.

This file is standalone and uses only stdlib plus the shared storyworld helpers.
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


# ---------------------------------------------------------------------------
# Core domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "woman", "mother", "doe", "fox", "rabbit"}
        masculine = {"boy", "man", "father", "deer", "badger", "otter"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    detail: str
    repeated_sound: str = "gurgle"
    has_pond: bool = True


@dataclass
class Mystery:
    id: str
    label: str
    clue: str
    cause: str
    fix: str


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        return World(
            place=self.place,
            entities=copy.deepcopy(self.entities),
            paragraphs=[[]],
            facts=dict(self.facts),
            fired=set(self.fired),
        )


@dataclass
class StoryParams:
    place: str
    hero_kind: str
    helper_kind: str
    mystery: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "pond": Place(
        id="pond",
        label="the quiet pond",
        detail="The meadow was green, and the pond rested under a willow tree.",
        repeated_sound="gurgle",
    ),
    "brook": Place(
        id="brook",
        label="the little brook",
        detail="The brook ran past stones and reeds beside the field.",
        repeated_sound="gurgle",
    ),
    "spring": Place(
        id="spring",
        label="the spring by the hill",
        detail="The spring bubbled up from the earth beside soft moss.",
        repeated_sound="gurgle",
    ),
}

MYSTERIES = {
    "reed": Mystery(
        id="reed",
        label="a bent reed",
        clue="a narrow reed was leaning into the water",
        cause="the reed had caught a small leaf and pinched the flow",
        fix="lift the reed and free the leaf",
    ),
    "pebble": Mystery(
        id="pebble",
        label="a round pebble",
        clue="a pebble had rolled against a little opening",
        cause="the pebble had partly blocked the water path",
        fix="move the pebble aside with care",
    ),
    "root": Mystery(
        id="root",
        label="a tree root",
        clue="a root had pushed up near the bank",
        cause="the root had pressed on the water’s little channel",
        fix="clear away the loose mud around it",
    ),
}

HEROES = {
    "rabbit": {"type": "rabbit", "label": "rabbit", "phrase": "a quick rabbit"},
    "fox": {"type": "fox", "label": "fox", "phrase": "a clever fox"},
    "badger": {"type": "badger", "label": "badger", "phrase": "a sturdy badger"},
    "otter": {"type": "otter", "label": "otter", "phrase": "a playful otter"},
}

HELPERS = {
    "deer": {"type": "deer", "label": "deer", "phrase": "a kind deer"},
    "heron": {"type": "heron", "label": "heron", "phrase": "a careful heron"},
    "mouse": {"type": "mouse", "label": "mouse", "phrase": "a gentle mouse"},
}

NAMES = {
    "rabbit": ["Pip", "Luna", "Nim"],
    "fox": ["Sage", "Mira", "Tess"],
    "badger": ["Bram", "Tobin", "Moss"],
    "otter": ["River", "Lark", "Puddle"],
    "deer": ["Fern", "Rowan", "Willow"],
    "heron": ["Iris", "Bela", "Reed"],
    "mouse": ["Dot", "Pipkin", "Nettle"],
}


# ---------------------------------------------------------------------------
# World behavior
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.hero_kind not in HEROES:
        raise StoryError(f"Unknown hero kind: {params.hero_kind}")
    if params.helper_kind not in HELPERS:
        raise StoryError(f"Unknown helper kind: {params.helper_kind}")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery}")

    world = World(place=PLACES[params.place])
    hero_info = HEROES[params.hero_kind]
    helper_info = HELPERS[params.helper_kind]
    mystery = MYSTERIES[params.mystery]

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_info["type"],
        label=hero_info["label"],
        phrase=hero_info["phrase"],
        meters={"worry": 0.0, "joy": 0.0, "curiosity": 0.0, "kindness": 0.0},
        memes={"worry": 0.0, "joy": 0.0, "curiosity": 0.0, "kindness": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_info["type"],
        label=helper_info["label"],
        phrase=helper_info["phrase"],
        meters={"worry": 0.0, "joy": 0.0, "kindness": 0.0},
        memes={"worry": 0.0, "joy": 0.0, "kindness": 0.0},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=mystery.label,
        phrase=mystery.clue,
        owner=world.place.id,
    ))

    world.facts.update(
        hero=hero,
        helper=helper,
        clue=clue,
        mystery=mystery,
        place=world.place,
        hero_name=random.choice(NAMES[hero.type]),
        helper_name=random.choice(NAMES[helper.type]),
    )
    return world


def _repeat_gurgle(world: World) -> None:
    for _ in range(3):
        world.say("Gurgle, gurgle, gurgle.")


def tell_story(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    clue: Entity = world.facts["clue"]
    mystery: Mystery = world.facts["mystery"]
    place: Place = world.facts["place"]
    hero_name: str = world.facts["hero_name"]
    helper_name: str = world.facts["helper_name"]

    hero.id = hero_name
    helper.id = helper_name

    # Beginning
    world.say(f"{place.detail}")
    world.say(f"One morning, {hero.id} heard a strange {place.repeated_sound} coming from the water.")
    _repeat_gurgle(world)
    hero.meters["curiosity"] += 1
    hero.memes["curiosity"] += 1
    world.say(f"{hero.id} stopped to listen, because the sound came again and again.")

    # Middle: repetition + mystery
    world.para()
    world.say(f"'{place.repeated_sound.capitalize()}, {place.repeated_sound}?' {hero.id} said. 'What could be making that noise?'")
    hero.meters["worry"] += 1
    hero.memes["worry"] += 1
    world.say(f"{hero.id} looked near the bank and found {clue.phrase}.")
    world.say(f"That was the clue, but not yet the answer.")
    world.say(f"{hero.id} walked softly along the edge of {place.label} and called for help.")
    helper.meters["kindness"] += 1
    helper.memes["kindness"] += 1
    world.say(f"Kind {helper.id} came at once, because kind hearts like to help when something is puzzling.")

    # Turn: solve the mystery with kindness
    world.para()
    world.say(f"{helper.id} listened, then pointed to the water and smiled.")
    world.say(f"'{mystery.clue.capitalize()},' {helper.id} said. 'That may be the reason for the sound.'")
    world.say(f"Together they saw that {mystery.cause}.")
    world.say(f"With gentle paws and careful steps, they worked together to {mystery.fix}.")
    hero.meters["worry"] = max(0.0, hero.meters["worry"] - 1.0)
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    hero.meters["joy"] += 1
    hero.memes["joy"] += 1
    helper.meters["joy"] += 1
    helper.memes["joy"] += 1

    # Ending
    world.para()
    world.say("Then the water settled.")
    world.say("Gurgle... gurgle...")
    world.say("After that, the little sound became soft and friendly, like a song the pond was happy to sing.")
    world.say(f"{hero.id} smiled, and {helper.id} smiled too, because the mystery was solved and the kind deed had made the day calm again.")
    world.say(f"From then on, {place.label} felt peaceful, and the repeated gurgle was no longer a worry.")

    world.facts["resolved"] = True
    world.facts["ending_sound"] = "soft and friendly"


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    mystery: Mystery = f["mystery"]
    place: Place = f["place"]
    return [
        f"Write a short fable for a young child about {hero.phrase} at {place.label} hearing a repeated gurgle.",
        f"Tell a gentle mystery story where {hero.id} and {helper.id} investigate {mystery.label} and solve it kindly.",
        f"Write a child-friendly fable that repeats the word 'gurgle' and ends with a kind solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    mystery: Mystery = f["mystery"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"What strange sound did {hero.id} hear at {place.label}?",
            answer=f"{hero.id} heard a repeated gurgle coming from the water at {place.label}.",
        ),
        QAItem(
            question=f"What was the mystery in the story?",
            answer=f"The mystery was what was causing the repeated gurgle, and the answer was {mystery.cause}.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} solve the problem?",
            answer=f"They solved it with kindness by working together to {mystery.fix}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer="The gurgle became gentle and pleasant, and the pond felt calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not understood at first and needs careful thinking to solve.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping others gently and carefully, especially when they are worried or need support.",
        ),
        QAItem(
            question="Why can a repeated sound catch attention?",
            answer="A sound that happens again and again can make someone wonder what is causing it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: round(v, 2) for k, v in ent.meters.items() if v}
        memes = {k: round(v, 2) for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.phrase:
            bits.append(f"phrase={ent.phrase!r}")
        lines.append(f"  {ent.id:8} ({ent.kind:9}) {' '.join(bits)}")
    lines.append(f"  place: {world.place.label}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(pond).
place(brook).
place(spring).

hero_kind(rabbit).
hero_kind(fox).
hero_kind(badger).
hero_kind(otter).

helper_kind(deer).
helper_kind(heron).
helper_kind(mouse).

mystery(reed).
mystery(pebble).
mystery(root).

repeated_sound(gurgle).

kind_story(P, H, K, M) :- place(P), hero_kind(H), helper_kind(K), mystery(M).
#show kind_story/4.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for hid in HEROES:
        lines.append(asp.fact("hero_kind", hid))
    for kid in HELPERS:
        lines.append(asp.fact("helper_kind", kid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    lines.append(asp.fact("repeated_sound", "gurgle"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show kind_story/4."))
    return sorted(set(asp.atoms(model, "kind_story")))


def python_reasonable() -> list[tuple]:
    return sorted((p, h, k, m) for p in PLACES for h in HEROES for k in HELPERS for m in MYSTERIES)


def asp_verify() -> int:
    a = set(asp_reasonable())
    b = set(python_reasonable())
    if a == b:
        print(f"OK: ASP and Python agree on {len(a)} combinations.")
        return 0
    print("Mismatch between ASP and Python.")
    if a - b:
        print("Only in ASP:", sorted(a - b))
    if b - a:
        print("Only in Python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world about a repeated gurgle, a mystery, and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-kind", choices=HEROES)
    ap.add_argument("--helper-kind", choices=HELPERS)
    ap.add_argument("--mystery", choices=MYSTERIES)
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
    hero_kind = args.hero_kind or rng.choice(list(HEROES))
    helper_kind = args.helper_kind or rng.choice(list(HELPERS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    return StoryParams(place=place, hero_kind=hero_kind, helper_kind=helper_kind, mystery=mystery)


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
    StoryParams(place="pond", hero_kind="rabbit", helper_kind="deer", mystery="reed"),
    StoryParams(place="brook", hero_kind="fox", helper_kind="mouse", mystery="pebble"),
    StoryParams(place="spring", hero_kind="otter", helper_kind="heron", mystery="root"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show kind_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show kind_story/4."))
        print(sorted(set(asp.atoms(model, "kind_story"))))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
