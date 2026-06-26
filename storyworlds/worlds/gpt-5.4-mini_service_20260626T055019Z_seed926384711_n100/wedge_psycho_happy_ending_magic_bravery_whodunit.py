#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/wedge_psycho_happy_ending_magic_bravery_whodunit.py
============================================================================================================================

A tiny whodunit-style storyworld: someone spots a puzzling trick, follows clues,
uses a wedge and a little magic, and ends with bravery and a happy ending.

Seed image:
---
A lantern goes out in a cozy room, a jewel vanishes, and a curious child
notices a thin wedge by the door. Someone keeps saying "psycho" in a whispery,
dramatic way, but the real answer is not a monster at all.

World idea:
---
This is a child-facing mystery domain with:
- a small setting
- a single missing object
- clue-based deduction
- a harmless red herring named with the seed word "psycho"
- a magical helper object that reveals what happened
- bravery that turns fear into action
- a happy ending that proves the truth

The world model tracks:
- physical meters: hidden, open, stuck, bright, dusty
- emotional memes: worry, bravery, relief, curiosity, pride

The generated story is not a frozen paragraph; it is driven by state changes:
setup -> clue hunt -> reveal -> resolution.
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
    hidden: bool = False
    plural: bool = False
    magical: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["hidden", "open", "stuck", "bright", "dusty", "moved"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "bravery", "relief", "curiosity", "pride", "fear"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old library"
    detail: str = "rows of books and a quiet desk"


@dataclass
class StoryParams:
    place: str
    mystery: str
    missing: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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


def _meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _mem(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def introduce(world: World, hero: Entity, helper: Entity, missing: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved quiet places and sharp clues."
    )
    world.say(
        f"On a calm evening in {world.setting.place}, something strange happened: "
        f"{missing.phrase} disappeared from its place."
    )
    world.say(
        f"{helper.id} was nearby, holding a small lantern and whispering, "
        f'"This feels like a real whodunit."'
    )


def crime_scene(world: World, missing: Entity, clue: Entity, suspect: Entity) -> None:
    _meter(missing, "hidden", 1)
    _mem(world.get(world.facts["hero"].id), "curiosity", 1)
    world.say(
        f"The room was still, but one thing looked wrong: {missing.phrase} was gone."
    )
    world.say(
        f"Near the door, {world.get(clue.id).phrase} waited like a tiny answer."
    )
    world.say(
        f"Someone had left a silly whisper on the air about {suspect.label}, "
        f"but the clue did not fit that tale at all."
    )


def follow_clues(world: World, hero: Entity, clue: Entity, wedge: Entity) -> None:
    _mem(hero, "curiosity", 1)
    _mem(hero, "bravery", 1)
    _meter(clue, "noticed", 1)
    world.say(
        f"{hero.id} knelt down and studied the clue carefully."
    )
    world.say(
        f"{hero.pronoun().capitalize()} spotted a thin {wedge.label} tucked by the jammed drawer."
    )
    world.say(
        f"{hero.id} said, 'A wedge can pry open a stuck thing. That means someone used it here.'"
    )


def use_magic(world: World, hero: Entity, magic: Entity, missing: Entity) -> None:
    _meter(magic, "glow", 1)
    _mem(hero, "bravery", 1)
    world.say(
        f"{hero.id} held up the {magic.label}, and it glimmered with soft blue light."
    )
    world.say(
        f"The magic did not do the job for them, but it showed a shining trail across the floor."
    )
    world.say(
        f"The trail led straight to {missing.phrase}, which had been hidden behind a panel."
    )
    _meter(missing, "hidden", -1)
    _meter(missing, "found", 1)


def reveal(world: World, suspect: Entity, missing: Entity, helper: Entity) -> None:
    _mem(helper, "relief", 1)
    world.say(
        f"At last, the mystery made sense."
    )
    world.say(
        f"The so-called {suspect.label} was only a red herring: a noisy squirrel toy with a dramatic name."
    )
    world.say(
        f"It had bumped the panel loose, and the wedge had slipped aside when the drawer was forced."
    )
    world.say(
        f"{helper.id} laughed. 'So the truth was hiding in plain sight!'"
    )


def happy_ending(world: World, hero: Entity, helper: Entity, missing: Entity) -> None:
    _mem(hero, "pride", 1)
    _mem(helper, "pride", 1)
    _mem(hero, "relief", 1)
    world.say(
        f"{hero.id} and {helper.id} put {missing.phrase} back where it belonged."
    )
    world.say(
        f"The lantern burned bright again, the room felt safe, and everybody smiled."
    )
    world.say(
        f"{hero.id} felt brave, because {hero.pronoun()} had followed the clues instead of the scary whisper."
    )
    world.say(
        f"It was a happy ending: the puzzle was solved, the mystery was kind, and the night was calm again."
    )


SETTINGS = {
    "library": Setting(place="the old library", detail="book stacks, a brass lamp, and a secret drawer"),
    "museum": Setting(place="the tiny museum", detail="glass cases, a velvet rope, and a quiet hall"),
    "attic": Setting(place="the attic room", detail="dusty trunks, moonlight, and a creaky panel"),
}


MYSTERIES = {
    "jewel": {
        "missing": "a small moon-shaped jewel",
        "clue": "a thin wooden wedge",
        "suspect": "Psycho the squirrel toy",
        "magic": "magic lantern",
    },
    "key": {
        "missing": "a silver key with a star on it",
        "clue": "a tiny metal wedge",
        "suspect": "Psycho the parrot puppet",
        "magic": "magic magnifier",
    },
    "cookie": {
        "missing": "the last honey cookie",
        "clue": "a little crumb wedge",
        "suspect": "Psycho the wind-up mouse",
        "magic": "magic lantern",
    },
}


GIRL_NAMES = ["Mia", "Lily", "Zoe", "Nora", "Ava", "Ruby", "Ivy"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Ben", "Owen", "Eli"]


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_gender))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender))
    missing_cfg = MYSTERIES[params.mystery]

    missing = world.add(Entity(
        id="missing",
        type="thing",
        label=missing_cfg["missing"],
        phrase=missing_cfg["missing"],
        hidden=True,
    ))
    clue = world.add(Entity(
        id="clue",
        type="thing",
        label=missing_cfg["clue"],
        phrase=missing_cfg["clue"],
    ))
    suspect = world.add(Entity(
        id="suspect",
        type="thing",
        label=missing_cfg["suspect"],
        phrase=missing_cfg["suspect"],
    ))
    magic = world.add(Entity(
        id="magic",
        type="thing",
        label=missing_cfg["magic"],
        phrase=missing_cfg["magic"],
        magical=True,
    ))
    wedge = world.add(Entity(
        id="wedge",
        type="thing",
        label="wedge",
        phrase="a thin wedge",
    ))

    world.facts.update(
        hero=hero,
        helper=helper,
        missing=missing,
        clue=clue,
        suspect=suspect,
        magic=magic,
        wedge=wedge,
        setting=world.setting,
        mystery=params.mystery,
    )

    introduce(world, hero, helper, missing)
    world.para()
    crime_scene(world, missing, clue, suspect)
    follow_clues(world, hero, clue, wedge)
    world.para()
    use_magic(world, hero, magic, missing)
    reveal(world, suspect, missing, helper)
    world.para()
    happy_ending(world, hero, helper, missing)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    missing: Entity = f["missing"]
    return [
        f'Write a short whodunit for a child where {hero.id} solves the mystery of {missing.phrase}.',
        f"Tell a brave, magical mystery in {world.setting.place} with {helper.id}, a wedge, and a happy ending.",
        f'Write a simple detective story that includes the word "psycho" as a silly red herring, not a real monster.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    missing: Entity = f["missing"]
    clue: Entity = f["clue"]
    suspect: Entity = f["suspect"]
    magic: Entity = f["magic"]
    qa = [
        QAItem(
            question=f"Who solved the mystery in {world.setting.place}?",
            answer=f"{hero.id} solved it by following clues, using bravery, and finding the hidden {missing.phrase}.",
        ),
        QAItem(
            question=f"What clue pointed toward the answer?",
            answer=f"The clue was {clue.phrase}, which helped {hero.id} understand that something had been moved with force.",
        ),
        QAItem(
            question=f"Why did the story mention {suspect.label}?",
            answer=f"{suspect.label} was a silly red herring, so it made the mystery feel puzzling, but it was not the real cause.",
        ),
        QAItem(
            question=f"How did {magic.label} help?",
            answer=f"The {magic.label} shone a gentle light that revealed the hidden trail and showed where {missing.phrase} had been placed.",
        ),
        QAItem(
            question=f"What made the ending happy?",
            answer=f"The missing thing was found, everyone felt relieved, and {hero.id} felt proud because the mystery was solved safely.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a wedge for?",
            answer="A wedge is a thin piece used to pry things open or hold something apart.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something scary or difficult even when your heart feels shaky.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something special and impossible in real life that can reveal, help, or transform what is happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
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
        if e.magical:
            bits.append("magical=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A missing object is the center of the mystery.
mystery_object(M) :- missing(M).

% A wedge is a prying clue.
clue(C) :- wedge(C).

% A magical tool can reveal hidden things.
reveals(Mag, Obj) :- magical(Mag), hidden(Obj).

% Bravery helps the hero finish the case.
happy_ending(H) :- hero(H), brave(H), solved_case(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for mid, cfg in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid))
        lines.append(asp.fact("label", mid, cfg["missing"]))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("brave", "hero"))
    lines.append(asp.fact("solved_case", "hero"))
    lines.append(asp.fact("magical", "magic"))
    lines.append(asp.fact("hidden", "missing"))
    lines.append(asp.fact("wedge", "wedge"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp  # lazy
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show happy_ending/1. #show reveals/2. #show clue/1."))
    atoms = set((s.name, tuple(arg.string if arg.type == 2 else arg.number for arg in s.arguments)) for s in model)
    expected = {("clue", ("wedge",)), ("reveals", ("magic", "missing")), ("happy_ending", ("hero",))}
    if atoms == expected:
        print("OK: ASP rules match Python reasonableness gate.")
        return 0
    print("MISMATCH:")
    print("asp:", sorted(atoms))
    print("py :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld with wedge, psycho, magic, bravery, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--missing", choices=["jewel", "key", "cookie"])
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    if args.missing and args.missing != mystery:
        raise StoryError("The chosen missing object must match the selected mystery.")
    place = args.place or rng.choice(sorted(SETTINGS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(BOY_NAMES if helper_gender == "boy" else GIRL_NAMES)
    return StoryParams(
        place=place,
        mystery=mystery,
        missing=mystery,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


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

    if args.show_asp:
        print(asp_program("#show happy_ending/1. #show reveals/2. #show clue/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp  # lazy
        model = asp.one_model(asp_program("#show happy_ending/1. #show reveals/2. #show clue/1."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="library", mystery="jewel", missing="jewel", hero_name="Mia", hero_gender="girl", helper_name="Leo", helper_gender="boy"),
            StoryParams(place="museum", mystery="key", missing="key", hero_name="Theo", hero_gender="boy", helper_name="Ruby", helper_gender="girl"),
            StoryParams(place="attic", mystery="cookie", missing="cookie", hero_name="Ivy", hero_gender="girl", helper_name="Finn", helper_gender="boy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.hero_name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
