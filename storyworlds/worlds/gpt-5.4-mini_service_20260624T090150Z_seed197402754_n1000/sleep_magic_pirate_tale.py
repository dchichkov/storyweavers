#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/sleep_magic_pirate_tale.py
=========================================================================================================

A small storyworld in a pirate-tale style: a sleepy young pirate, a bit of
magic, and a gentle bedtime turn.

The world model tracks:
- physical meters: tiredness, glow, comfort, sparkle, mess
- emotional memes: excitement, worry, bravery, calm, love

The story premise is simple: a young pirate wants to stay awake for a magical
night, but sleep is pulling their eyelids down. A clever helper uses magic to
make bedtime feel safe and wondrous, turning the struggle into a cozy ending.
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})
    plural: bool = False

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
    place: str = "the moonlit ship"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Magic:
    id: str
    label: str
    spell: str
    effect: str
    helps_with: set[str]
    prepares: str
    closes: str


@dataclass
class StoryParams:
    place: str
    magic: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _speak(world: World, text: str) -> None:
    world.say(text)


def introduce(world: World, hero: Entity) -> None:
    _speak(world, f"{hero.id} was a little {hero.type} pirate who loved the night sea and shiny treasure.")


def love_magic(world: World, hero: Entity, magic: Magic) -> None:
    hero.memes["excitement"] = hero.memes.get("excitement", 0) + 1
    _speak(world, f"{hero.pronoun().capitalize()} loved {magic.label}, because {magic.effect}.")


def sleepy_signal(world: World, hero: Entity) -> None:
    hero.meters["tiredness"] = hero.meters.get("tiredness", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    _speak(world, f"But as the stars climbed higher, {hero.id}'s eyes grew heavy, and sleep kept tugging at {hero.pronoun('possessive')} lashes.")


def arrive_night(world: World, hero: Entity, helper: Entity, magic: Magic) -> None:
    _speak(world, f"One quiet night, {hero.id} and {hero.pronoun('possessive')} {helper.label} stood on {world.setting.place}.")
    _speak(world, f"The {magic.label} was there too, glowing softly under the lantern light.")


def wants_to_stay_up(world: World, hero: Entity, magic: Magic) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    _speak(world, f"{hero.id} wanted to stay up and see the {magic.label} work until the very end.")


def warning(world: World, helper: Entity, hero: Entity) -> None:
    if hero.meters.get("tiredness", 0) >= THRESHOLD:
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        _speak(world, f"{helper.pronoun().capitalize()} smiled and said, \"A tired pirate needs rest, or the treasure hunt will feel gloomy.\"")


def magic_bedtime(world: World, helper: Entity, hero: Entity, magic: Magic) -> None:
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    hero.meters["comfort"] = hero.meters.get("comfort", 0) + 1
    hero.meters["glow"] = hero.meters.get("glow", 0) + 1
    _speak(world, f"{helper.pronoun().capitalize()} lifted the {magic.label} and whispered, \"{magic.spell}\"")
    _speak(world, f"At once, {magic.effect}, and the deck felt warm instead of wild.")
    _speak(world, f"Then {helper.pronoun('possessive')} {helper.label} guided {hero.id} to a cozy cot and tucked {hero.pronoun('object')} in tight.")


def fall_asleep(world: World, hero: Entity, helper: Entity, magic: Magic) -> None:
    hero.meters["tiredness"] = 0
    hero.memes["worry"] = 0
    hero.memes["calm"] = hero.memes.get("calm", 0) + 2
    _speak(world, f"{hero.id} yawned a great big yawn, snuggled under the blanket, and drifted off to sleep.")
    _speak(world, f"The {magic.label} dimmed to a tiny sparkle while {helper.pronoun('possessive')} {helper.label} kept watch by the lantern.")
    _speak(world, f"At last, the ship was quiet, and {hero.id} slept with a soft smile on {hero.pronoun('possessive')} face.")


SETTINGS = {
    "ship": Setting(place="the moonlit ship", affords={"sleep", "magic"}),
    "harbor": Setting(place="the harbor dock", affords={"sleep", "magic"}),
    "cabin": Setting(place="the captain's cabin", affords={"sleep", "magic"}),
}

MAGICS = {
    "lantern": Magic(
        id="lantern",
        label="magic lantern",
        spell="Twinkle low, twinkle slow",
        effect="the lantern painted the deck with gold stars",
        helps_with={"sleep"},
        prepares="held the lantern close",
        closes="let the lantern glow like a sleepy firefly",
    ),
    "shell": Magic(
        id="shell",
        label="magic seashell",
        spell="Sea-splash hush, and rest will rush",
        effect="the seashell sang a hushy tune that made the waves feel gentle",
        helps_with={"sleep"},
        prepares="picked up the seashell",
        closes="set the seashell beside the pillow",
    ),
}

NAMES = {
    "girl": ["Mira", "Ruby", "Nia", "Luna", "Ivy"],
    "boy": ["Finn", "Rowan", "Jett", "Owen", "Toby"],
}

TRAITS = ["brave", "curious", "cheery", "bold", "lively"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, magic) for place in SETTINGS for magic in MAGICS]


def explain_rejection(place: str, magic: str) -> str:
    return f"(No story: the chosen pirate tale needs both sleep and magic, and {place} with {magic} does not fit the tiny bedtime adventure.)"


def build_story_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    magic = MAGICS[params.magic]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=f"old {params.helper}"))
    relic = world.add(Entity(id="relic", type="thing", label=magic.label, phrase=magic.label))
    world.facts.update(hero=hero, helper=helper, magic=magic, relic=relic)

    introduce(world, hero)
    love_magic(world, hero, magic)
    sleepy_signal(world, hero)
    world.para()
    arrive_night(world, hero, helper, magic)
    wants_to_stay_up(world, hero, magic)
    warning(world, helper, hero)
    magic_bedtime(world, helper, hero, magic)
    world.para()
    fall_asleep(world, hero, helper, magic)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    magic = f["magic"]
    return [
        "Write a short pirate tale for a young child about sleep and magic.",
        f"Tell a gentle story where {hero.id} the pirate feels sleepy but still wants to use the {magic.label}.",
        f"Write a cozy bedtime adventure with {helper.label}, a glowing {magic.label}, and a little pirate who learns to sleep.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    magic = f["magic"]
    return [
        QAItem(
            question=f"Who wanted to stay up and see the {magic.label} work?",
            answer=f"{hero.id} wanted to stay up and see the {magic.label} work.",
        ),
        QAItem(
            question=f"Why did {helper.label} tell {hero.id} that a tired pirate needs rest?",
            answer=f"{hero.id} was getting sleepy, so {helper.label} reminded {hero.id} that rest would make the treasure hunt feel better.",
        ),
        QAItem(
            question="What happened at the end of the story?",
            answer=f"{hero.id} fell asleep in a cozy cot while the {magic.label} dimmed to a tiny sparkle.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sleep for?",
            answer="Sleep helps the body and mind rest so a child can feel better and have energy for the next day.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic is something wondrous and impossible in real life, like a spell or a glowing object that can make surprising things happen in a story.",
        ),
        QAItem(
            question="Why do pirates often travel at night in stories?",
            answer="Pirates in stories may travel at night because the moon and stars make the sea look mysterious and exciting.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
magic(M) :- magic_item(M).

valid(P, M) :- place(P), magic(M).
sleep_story(P, M) :- valid(P, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for m in MAGICS:
        lines.append(asp.fact("magic_item", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show valid/2.\n#show sleep_story/2.\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


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
    ap = argparse.ArgumentParser(description="A tiny pirate tale world with sleep and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["captain", "mother", "father"])
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
    if args.place and args.magic:
        if (args.place, args.magic) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.magic))
    place = args.place or rng.choice(list(SETTINGS))
    magic = args.magic or rng.choice(list(MAGICS))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper = args.helper or rng.choice(["captain", "mother", "father"])
    name = args.name or rng.choice(NAMES[gender])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, magic=magic, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_story_world(params)
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
    StoryParams(place="ship", magic="lantern", name="Mira", gender="girl", helper="captain", trait="brave"),
    StoryParams(place="cabin", magic="shell", name="Finn", gender="boy", helper="father", trait="curious"),
    StoryParams(place="harbor", magic="lantern", name="Luna", gender="girl", helper="mother", trait="cheery"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show sleep_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
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
            header = f"### {p.name}: {p.magic} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
