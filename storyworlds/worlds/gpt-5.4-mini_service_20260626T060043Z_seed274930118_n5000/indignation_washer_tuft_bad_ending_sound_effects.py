#!/usr/bin/env python3
"""
A small comedy storyworld about a washer, a tuft, and a very bad laundry day.

Premise:
- A child or small character has a beloved tufted item or pet with a tuft.
- A washer machine is supposed to clean something.
- Something goes wrong, causing indignation, sound effects, and a bad ending.
- The tone stays playful and rhyme-friendly, with a comic sting at the end.

This world intentionally keeps the "bad ending" as a funny, child-safe disaster:
the laundry comes out weird, the tuft goes floppy, and the hero learns that not
every plan ends with a win.
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
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the laundry room"
    affordances: set[str] = field(default_factory=lambda: {"wash", "sort", "dry"})


@dataclass
class StoryParams:
    place: str = "laundry_room"
    hero_name: str = "Milo"
    hero_type: str = "boy"
    caretaker_type: str = "mother"
    tuft_kind: str = "hat"
    washer_kind: str = "washer"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.flags: set[str] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "laundry_room": Setting(place="the laundry room"),
}

TUFTS = {
    "hat": {
        "label": "tufted hat",
        "phrase": "a soft tufted hat with a silly puff on top",
        "place": "on the hook by the washer",
    },
    "blanket": {
        "label": "tufted blanket",
        "phrase": "a cozy blanket with one brave tuft at the corner",
        "place": "in the basket",
    },
    "toy": {
        "label": "tufted toy",
        "phrase": "a stuffed toy with a tiny tuft like a whisker",
        "place": "on the shelf",
    },
}

WASHERS = {
    "washer": {
        "label": "washer",
        "phrase": "the big washer",
    },
}

HERO_NAMES = ["Milo", "Nina", "Pip", "Luna", "Theo", "Maya"]
TRAITS = ["cheerful", "curious", "silly", "stubborn", "bouncy"]


# ---------------------------------------------------------------------------
# Reasonableness / gating
# ---------------------------------------------------------------------------

def valid_combo(params: StoryParams) -> bool:
    return params.place in SETTINGS and params.tuft_kind in TUFTS and params.washer_kind in WASHERS


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the requested washer-and-tuft setup is invalid for this tiny laundry room.)"


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def rhyme(line: str) -> str:
    return line


def sound_effect(kind: str) -> str:
    return {
        "start": "WHIRR-CHIRR-DRUMM!",
        "clank": "CLANK-CLANK!",
        "splash": "SPLOOSH!",
        "sputter": "SPIT-SPAT-SPLUTTER!",
        "stop": "THUNK.",
    }[kind]


def intro(world: World, hero: Entity, caretaker: Entity, tuft: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait', 'silly')} {hero.type} who loved neat things and noisy chores."
    )
    world.say(
        f"One day, {hero.id} found {tuft.phrase} and felt a tiny spark of {hero.memes.get('feeling', 'pride')}."
    )
    world.say(
        f"{caretaker.label.capitalize()} pointed at {world.setting.place} and said, "
        f'"Let’s wash it before it turns into a puff of fuzz and dust."'
    )


def start_washer(world: World, washer: Entity) -> None:
    washer.meters["running"] = 1
    world.say(f"The {washer.label} went {sound_effect('start')} and began to spin like a happy wheel.")


def add_item(world: World, hero: Entity, tuft: Entity) -> None:
    tuft.meters["wet"] = 1
    tuft.meters["spun"] = 1
    world.say(
        f"{hero.id} tucked the {tuft.label} inside. It looked brave at first, like a captain on a tiny ship."
    )


def bad_turn(world: World, hero: Entity, tuft: Entity) -> None:
    world.say(sound_effect("clank"))
    world.say(sound_effect("splash"))
    world.say(
        f"Then the washer found the loose tuft and made a mess of the whole plan."
    )
    tuft.memes["indignation"] = 1
    hero.memes["indignation"] = 1
    world.flags.add("bad_ending")
    world.say(
        f"{hero.id} frowned with indignation. 'That was my best tuft!' {hero.pronoun().capitalize()} said."
    )


def rhyme_response(world: World, hero: Entity, caretaker: Entity, tuft: Entity) -> None:
    world.say(
        "No neat repeat, just a soggy defeat; "
        f"the tuft went limp, and the wash felt incomplete."
    )
    world.say(
        f"{caretaker.label.capitalize()} tried to grin, but the dryer gave a sputter and a thin little spin."
    )
    world.say(sound_effect("sputter"))
    world.say(
        f"{hero.id} held up the sad tuft and said, 'Oh no, my fluff is in a huff.'"
    )


def ending(world: World, hero: Entity, caretaker: Entity, tuft: Entity) -> None:
    tuft.meters["floppy"] = 1
    hero.memes["indignation"] = 2
    world.say(
        f"In the end, the tuft was still there, but it looked flat and funny, not proud and square."
    )
    world.say(
        f"{hero.id} had to wear the grumpy grin of a child who lost a laundry win."
    )
    world.say(
        f"And the washer, smug and humming, sat still while everyone else went glumming."
    )


# ---------------------------------------------------------------------------
# Build / story generation
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    if not valid_combo(params):
        raise StoryError(explain_rejection(params))

    world = World(SETTINGS[params.place])
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        memes={"trait": random.choice(TRAITS), "feeling": "hope"},
    ))
    caretaker = world.add(Entity(
        id="caretaker",
        kind="character",
        type=params.caretaker_type,
        label={"mother": "mom", "father": "dad"}.get(params.caretaker_type, "caretaker"),
    ))
    tuft_def = TUFTS[params.tuft_kind]
    tuft = world.add(Entity(
        id="tuft",
        kind="thing",
        type=params.tuft_kind,
        label=tuft_def["label"],
        phrase=tuft_def["phrase"],
        owner=hero.id,
        caretaker=caretaker.id,
    ))
    washer = world.add(Entity(
        id="washer",
        kind="thing",
        type="washer",
        label="washer",
        phrase="the big washer",
    ))

    world.say(f"{hero.id} was in {world.setting.place} with {caretaker.label}.")
    world.say(f"They noticed {tuft_def['phrase']} waiting {tuft_def['place']}.")
    world.para()
    intro(world, hero, caretaker, tuft)
    world.para()
    add_item(world, hero, tuft)
    start_washer(world, washer)
    bad_turn(world, hero, tuft)
    rhyme_response(world, hero, caretaker, tuft)
    ending(world, hero, caretaker, tuft)

    world.facts.update(
        hero=hero,
        caretaker=caretaker,
        tuft=tuft,
        washer=washer,
        setting=world.setting,
        bad_ending=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    tuft = world.facts["tuft"]
    return [
        'Write a short comedy story about indignation, a washer, and a tuft, with sound effects and a rhyme.',
        f"Tell a playful story where {hero.id} tries to clean {tuft.label} in a washer and it goes hilariously wrong.",
        "Write a tiny rhyming story that ends with a bad ending for the tuft but a funny mood.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    caretaker = world.facts["caretaker"]
    tuft = world.facts["tuft"]
    return [
        QAItem(
            question=f"What did {hero.id} try to put in the washer?",
            answer=f"{hero.id} tried to put {tuft.phrase} into the washer.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel indignation?",
            answer=f"{hero.id} felt indignation because the washer squashed the tufty plan and left {tuft.label} looking sad and flat.",
        ),
        QAItem(
            question=f"What sound did the washer make when things went wrong?",
            answer=f"It went {sound_effect('clank')} and then {sound_effect('sputter')}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended badly for the tuft, because {tuft.label} came out floppy, but the story stayed funny instead of scary.",
        ),
        QAItem(
            question=f"Who was with {hero.id} in the laundry room?",
            answer=f"{hero.id} was with {caretaker.label} in the laundry room.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a washer usually do?",
            answer="A washer spins clothes or other washable things in water and soap to help clean them.",
        ),
        QAItem(
            question="What is a tuft?",
            answer="A tuft is a small bunch of hair, fibers, or fluff that sticks up from something.",
        ),
        QAItem(
            question="What is indignation?",
            answer="Indignation is a strong feeling of being annoyed or offended because something seems unfair or wrong.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(laundry_room).
place(laundry_room).

thing(washer).
thing(tuft).

bad_ending(laundry_room) :- setting(laundry_room), thing(washer), thing(tuft).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("setting", "laundry_room"),
        asp.fact("place", "laundry_room"),
        asp.fact("thing", "washer"),
        asp.fact("thing", "tuft"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show bad_ending/1."))
    asp_set = set(asp.atoms(model, "bad_ending"))
    py_set = {("laundry_room",)} if True else set()
    if asp_set == py_set:
        print("OK: ASP and Python agree on the bad ending.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("ASP:", sorted(asp_set))
    print("PY :", sorted(py_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy laundry storyworld with a bad ending.")
    ap.add_argument("--place", choices=SETTINGS.keys(), default="laundry_room")
    ap.add_argument("--name", default=None)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--parent", choices=["mother", "father"], default=None)
    ap.add_argument("--tuft", choices=TUFTS.keys(), default="hat")
    ap.add_argument("--washer", choices=WASHERS.keys(), default="washer")
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
    name = args.name or rng.choice(HERO_NAMES)
    gender = args.gender or rng.choice(["boy", "girl"])
    hero_type = "boy" if gender == "boy" else "girl"
    caretaker = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=args.place,
        hero_name=name,
        hero_type=hero_type,
        caretaker_type=caretaker,
        tuft_kind=args.tuft,
        washer_kind=args.washer,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind}, type={e.type}, label={e.label}")
    lines.append(f"flags={sorted(world.flags)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show bad_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show bad_ending/1."))
        print(asp.atoms(model, "bad_ending"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            place="laundry_room",
            hero_name="Milo",
            hero_type="boy",
            caretaker_type="mother",
            tuft_kind="hat",
            washer_kind="washer",
            seed=base_seed,
        )
        samples = [generate(params)]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
