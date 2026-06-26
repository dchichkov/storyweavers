#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/expressive_ambiguous_curiosity_bravery_surprise_nursery_rhyme.py
==============================================================================================================================

A tiny nursery-rhyme storyworld about a child, a puzzling thing, and the
gentle leap from curiosity to bravery to surprise.

The seed theme is intentionally expressive and ambiguous: the child sees
something partly hidden, wonders what it is, grows brave enough to look, and
finds a small, surprising truth that changes the mood of the whole scene.
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
    in_place: str = ""
    openable: bool = False
    opened: bool = False
    hidden: bool = False
    gentle: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
    indoors: bool = True
    cozy: bool = True


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    reveal: str
    reveal_label: str
    place: str
    hidden_kind: str
    surprise_kind: str
    requires_bravery: bool = True
    ambiguous_hint: str = ""


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    caretaker: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "nursery": Place(id="nursery", label="the nursery", indoors=True, cozy=True),
    "garden": Place(id="garden", label="the little garden", indoors=False, cozy=True),
    "attic": Place(id="attic", label="the attic corner", indoors=True, cozy=False),
}

MYSTERIES = {
    "curtain": Mystery(
        id="curtain",
        label="curtained nook",
        phrase="a soft curtain hiding a nook",
        reveal="a nest of ribbon-tied stars",
        reveal_label="a little star garland",
        place="nursery",
        hidden_kind="cloth",
        surprise_kind="stars",
        ambiguous_hint="It looked like a secret, or maybe a sleep-time game.",
    ),
    "box": Mystery(
        id="box",
        label="little box",
        phrase="a tiny box with a button on top",
        reveal="a sleepy mouse with a blue bow",
        reveal_label="a shy mouse friend",
        place="nursery",
        hidden_kind="wood",
        surprise_kind="mouse",
        ambiguous_hint="It rattled like a toy, but it could have held a treasure.",
    ),
    "bush": Mystery(
        id="bush",
        label="bushy mound",
        phrase="a round mound under the berry bush",
        reveal="a tucked-away kitten",
        reveal_label="a sleepy kitten",
        place="garden",
        hidden_kind="leaves",
        surprise_kind="kitten",
        ambiguous_hint="It wiggled like a leaf pile, but it might have been alive.",
    ),
    "trunk": Mystery(
        id="trunk",
        label="old trunk",
        phrase="an old trunk with a brass clasp",
        reveal="a pile of costume feathers and a tiny drum",
        reveal_label="a feathered costume drum",
        place="attic",
        hidden_kind="wood",
        surprise_kind="feathers",
        ambiguous_hint="It seemed dusty and dull, but it might have kept a stage inside.",
    ),
}

TRAITS = ["curious", "bright", "gentle", "spry", "expressive", "patient"]
GIRL_NAMES = ["Mia", "Lily", "Nora", "Ruby", "Ella", "Zoe", "Ada"]
BOY_NAMES = ["Pip", "Finn", "Theo", "Ben", "Leo", "Sam", "Jude"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, p in PLACES.items():
        for mid, m in MYSTERIES.items():
            if m.place == place:
                combos.append((place, mid))
    return combos


def reasonableness_gate(place: str, mystery: str) -> bool:
    return (place, mystery) in valid_combos()


def explain_rejection(place: str, mystery: str) -> str:
    if mystery not in MYSTERIES:
        return "(No story: that mystery isn't in the rhyme-box."
    m = MYSTERIES[mystery]
    return (
        f"(No story: {m.label} belongs in {m.place}, not in {place}. "
        f"The little tale needs a hidden thing that fits its own room.)"
    )


def build_story(world: World, hero: Entity, caretaker: Entity, mystery: Mystery) -> None:
    hidden = world.add(Entity(
        id="mystery",
        kind="thing",
        type=mystery.hidden_kind,
        label=mystery.label,
        phrase=mystery.phrase,
        owner=caretaker.id,
        caretaker=caretaker.id,
        in_place=world.place.id,
        openable=True,
        opened=False,
        hidden=True,
    ))
    reveal = world.add(Entity(
        id="reveal",
        kind="thing",
        type=mystery.surprise_kind,
        label=mystery.reveal_label,
        phrase=mystery.reveal,
        in_place=world.place.id,
        gentle=True,
        hidden=False,
    ))
    world.facts.update(hero=hero, caretaker=caretaker, mystery=mystery, hidden=hidden, reveal=reveal)

    hero.memes["curiosity"] = 1
    world.say(
        f"{hero.id} was a {hero.memes.get('trait', '') or hero.memes.get('style', '') or 'little'} {hero.type} with a merry, curious heart."
    )
    world.say(
        f"In {world.place.label}, {hero.id} found {mystery.phrase}. "
        f"{mystery.ambiguous_hint}"
    )
    world.say(
        f"{hero.id} wondered, “What can it be?” and tiptoed near, with wide eyes and a whisper-soft step."
    )

    world.para()
    hero.memes["bravery"] = 1
    world.say(
        f"{caretaker.pronoun('subject').capitalize()} smiled and said, “You may look, if you are brave and kind.”"
    )
    world.say(
        f"So {hero.id} took one brave breath, lifted the edge, and opened the little secret."
    )
    hidden.opened = True
    hidden.hidden = False
    hero.memes["surprise"] = 1

    world.para()
    world.say(
        f"Inside was {mystery.reveal}. {mystery.reveal} did not scare {hero.id}; it made {hero.pronoun('object')} laugh in delight."
    )
    world.say(
        f"{hero.id} clapped {hero.pronoun('possessive')} hands, and {caretaker.id} laughed too, "
        f"because the puzzling thing was only a gentle surprise."
    )
    world.say(
        f"By the end, the room felt brighter, and the hidden place was a happy place to remember."
    )
    world.facts["resolved"] = True


def tell(place: Place, mystery: Mystery, hero_name: str, hero_type: str, caretaker_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        meters={},
        memes={"trait": trait, "curiosity": 0.0, "bravery": 0.0, "surprise": 0.0},
    ))
    caretaker = world.add(Entity(
        id="Caretaker",
        kind="character",
        type=caretaker_type,
        label="the grown-up",
        meters={},
        memes={},
    ))
    build_story(world, hero, caretaker, mystery)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    mystery: Mystery = f["mystery"]
    return [
        f'Write a short nursery-rhyme story about a child named {hero.id} who sees {mystery.phrase} and wonders what is inside.',
        f'Tell a gentle story in a sing-song voice where curiosity leads {hero.id} to open {mystery.label} and find a surprise.',
        f'Write a child-friendly tale about being curious, then brave, then delighted when a hidden thing is revealed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    caretaker: Entity = f["caretaker"]
    mystery: Mystery = f["mystery"]
    reveal: Entity = f["reveal"]
    return [
        QAItem(
            question=f"What did {hero.id} find in {world.place.label}?",
            answer=f"{hero.id} found {mystery.phrase}, and it made {hero.id} wonder what was hiding inside.",
        ),
        QAItem(
            question=f"What helped {hero.id} open the hidden thing?",
            answer=f"{caretaker.label.capitalize()} gave permission, and {hero.id}'s own bravery helped {hero.id} lift it open.",
        ),
        QAItem(
            question=f"What was the surprise at the end?",
            answer=f"The surprise was {reveal.phrase}, a gentle little find that made the room feel merry instead of mysterious.",
        ),
        QAItem(
            question=f"How did {hero.id} feel after the secret was opened?",
            answer=f"{hero.id} felt happy and amazed, because the unknown thing turned into a friendly surprise.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    return [
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more about something, especially when it looks puzzly or hidden.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing a hard or scary thing with a steady heart.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that appears when you look or listen closely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        if e.openable:
            bits.append(f"openable={e.openable}")
        if e.opened:
            bits.append("opened=True")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place_valid(P) :- place(P).
mystery_valid(M) :- mystery(M).
valid_story(P,M) :- place_valid(P), mystery_valid(M), located_in(M,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("located_in", mid, m.place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld of curiosity, bravery, and surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--caretaker", choices=["mother", "father"])
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
    combos = valid_combos()
    if args.place and args.mystery and not reasonableness_gate(args.place, args.mystery):
        raise StoryError(explain_rejection(args.place, args.mystery))
    combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caretaker = args.caretaker or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, caretaker=caretaker, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MYSTERIES[params.mystery], params.name, params.gender, params.caretaker, params.trait)
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
    StoryParams(place="nursery", mystery="box", name="Pip", gender="boy", caretaker="mother", trait="curious"),
    StoryParams(place="nursery", mystery="curtain", name="Mia", gender="girl", caretaker="father", trait="expressive"),
    StoryParams(place="garden", mystery="bush", name="Ruby", gender="girl", caretaker="mother", trait="bright"),
    StoryParams(place="attic", mystery="trunk", name="Finn", gender="boy", caretaker="father", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for place, mystery in combos:
            print(f"  {place:8} {mystery}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
