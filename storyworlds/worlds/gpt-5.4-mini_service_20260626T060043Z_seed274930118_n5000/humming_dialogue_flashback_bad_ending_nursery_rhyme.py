#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/humming_dialogue_flashback_bad_ending_nursery_rhyme.py
===============================================================================================================================

A tiny nursery-rhyme storyworld about humming, where a little character tries
to keep a tune gentle, remembers an earlier mistake in a flashback, speaks with
someone in dialogue, and sometimes reaches a bad ending.

The world is intentionally small and constraint-checked:
- a child or small creature in one place
- a beloved object or companion that can be soothed or upset
- humming as the central action
- dialogue to create a turn
- flashback to explain the worry
- a bad ending that is still complete and state-driven

This script follows the storyworld contract:
- standalone stdlib script
- lazy ASP import inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- QA items and trace support
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


@dataclass
class Setting:
    id: str
    place: str
    indoors: bool = False
    helps_hum: bool = True


@dataclass
class StoryParams:
    setting: str
    hero: str
    hero_type: str
    companion: str
    mood: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "nursery": Setting(id="nursery", place="the nursery", indoors=True, helps_hum=True),
    "porch": Setting(id="porch", place="the porch", indoors=False, helps_hum=False),
    "garden": Setting(id="garden", place="the garden gate", indoors=False, helps_hum=True),
}

HEROES = {
    "lily": ("Lily", "girl"),
    "tom": ("Tom", "boy"),
    "milo": ("Milo", "boy"),
    "pippa": ("Pippa", "girl"),
}

COMPANIONS = {
    "bunny": ("a little bunny", "bunny"),
    "duck": ("a sleepy duckling", "duckling"),
    "cat": ("a small cat", "cat"),
}

MOODS = ["brave", "gentle", "cheery", "curious"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny nursery-rhyme storyworld about humming, dialogue, flashback, and a bad ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _compat(setting: str, hero: str, companion: str) -> bool:
    if setting == "porch" and companion == "cat":
        return False
    return True


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(list(HEROES))
    companion = args.companion or rng.choice(list(COMPANIONS))
    mood = args.mood or rng.choice(MOODS)

    if not _compat(setting, hero, companion):
        raise StoryError("(No story: the cat will not stay calm on the porch in this tiny tale.)")

    return StoryParams(setting=setting, hero=hero, hero_type=HEROES[hero][1], companion=companion, mood=mood)


def _dialogue_line(speaker: str, line: str) -> str:
    return f'"{line}," said {speaker}.'


def _flashback(hero: Entity, companion: Entity) -> str:
    return (
        f"Before that, {hero.id} had hummed too loud near {companion.label}. "
        f"{companion.id} had jumped behind a chair, and the room had gone quiet."
    )


def _bad_ending(hero: Entity, companion: Entity, setting: Setting) -> str:
    return (
        f"So {hero.id} hummed softer and softer, but the little tune was already lost. "
        f"{companion.label} stayed hidden, and the day turned still at {setting.place}, "
        f"with only one lonely hum left in the air."
    )


def tell(setting: Setting, hero_name: str, hero_type: str, companion_key: str, mood: str) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"volume": 0.0},
        memes={"hope": 1.0, "worry": 0.0, "regret": 0.0},
    ))
    comp_phrase, comp_type = COMPANIONS[companion_key]
    companion = world.add(Entity(
        id=companion_key,
        kind="character",
        type=comp_type,
        label=comp_phrase,
        meters={"hiding": 0.0, "trust": 0.0},
        memes={"calm": 0.0, "fright": 0.0},
    ))
    book = world.add(Entity(
        id="songbook",
        type="songbook",
        label="a tiny songbook",
        phrase="a tiny songbook with a gold star",
        owner=hero.id,
        meters={"held": 1.0},
    ))

    world.say(f"Once in {setting.place}, little {hero.id} was {mood} and full of a hum.")
    world.say(f"{hero.id} had {book.phrase}, and {hero.pronoun('subject').capitalize()} liked to keep the pages neat.")
    world.say(f"{hero.id} said, {_dialogue_line(comp_phrase, 'If I hum, will you come out and play')}")
    world.say(f"The hum was soft at first, like a bee in a mitten.")

    world.para()
    world.say(_flashback(hero, companion))
    hero.memes["worry"] += 1.0
    companion.memes["fright"] += 1.0
    companion.meters["hiding"] += 1.0
    hero.meters["volume"] += 1.0

    world.say(
        f"{hero.id} remembered that old moment and whispered, {_dialogue_line(hero.id, 'I did not mean to startle you')}"
    )
    world.say(_dialogue_line(comp_phrase, "Then keep it low, like a moth on a leaf"))
    world.say(f"So {hero.id} tried to hum low, with {book.label} pressed close to the chest.")

    world.para()
    if setting.helps_hum:
        world.say(
            f"The place helped a little, for {setting.place} was quiet enough to hear a tiny tune."
        )
    else:
        world.say(
            f"But {setting.place} was windy, and the wind kept tugging the tune apart."
        )

    companion.meters["trust"] += 0.0
    if not setting.helps_hum:
        hero.meters["volume"] += 1.0
        hero.memes["regret"] += 1.0
        companion.memes["fright"] += 1.0
        world.say(f"{hero.id} hummed anyway, and the sound wobbled in the air.")
    else:
        hero.meters["volume"] += 0.5
        world.say(f"{hero.id} hummed again, but the little sound could not reach {companion.label}.")

    world.para()
    world.say(f"{hero.id} called, {_dialogue_line(comp_phrase, 'Please do not hide forever')}")
    world.say(f"But {companion.label} only stayed still and small.")
    world.say(_bad_ending(hero, companion, setting))

    world.facts.update(
        hero=hero,
        companion=companion,
        setting=setting,
        book=book,
        mood=mood,
        heard=False,
        flashback=True,
        bad_ending=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    setting: Setting = f["setting"]
    return [
        f"Write a nursery-rhyme-style story about {hero.id} humming in {setting.place} and speaking to {companion.label}.",
        f"Tell a short child-friendly tale with dialogue and a flashback where {hero.id} tries to hum gently but gets a bad ending.",
        f"Create a tiny rhyming story about humming, remembering an old scare, and not quite fixing the problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who was humming in {setting.place}?",
            answer=f"{hero.id} was humming in {setting.place}. {hero.pronoun('subject').capitalize()} tried to keep the tune soft.",
        ),
        QAItem(
            question=f"Why did {hero.id} hum softly?",
            answer=f"{hero.id} hummed softly because {hero.pronoun('subject')} remembered that humming too loud had frightened {companion.label} before.",
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=f"It ended badly: {companion.label} stayed hidden, and {hero.id} was left with only a lonely little hum.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is humming?",
            answer="Humming is making a soft sound with your voice while your mouth stays mostly closed.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story remembers something that happened earlier.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is when characters speak to each other in a story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="nursery", hero="lily", hero_type="girl", companion="bunny", mood="gentle"),
    StoryParams(setting="garden", hero="tom", hero_type="boy", companion="duck", mood="curious"),
    StoryParams(setting="porch", hero="pippa", hero_type="girl", companion="cat", mood="brave"),
]


ASP_RULES = r"""
setting(nursery). setting(porch). setting(garden).
place(nursery,"the nursery"). place(porch,"the porch"). place(garden,"the garden gate").
helps_hum(nursery). helps_hum(garden).
hero(lily). hero(tom). hero(milo). hero(pippa).
companion(bunny). companion(duck). companion(cat).

valid(S,H,C) :- setting(S), hero(H), companion(C), not bad_combo(S,H,C).
bad_combo(porch,_,cat).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        if SETTINGS[sid].helps_hum:
            lines.append(asp.fact("helps_hum", sid))
        lines.append(asp.fact("place", sid, SETTINGS[sid].place))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for cid in COMPANIONS:
        lines.append(asp.fact("companion", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = {
        (s, h, c)
        for s in SETTINGS
        for h in HEROES
        for c in COMPANIONS
        if _compat(s, h, c)
    }
    clingo_set = set(asp_valid())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python gate ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def build_story(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], HEROES[params.hero][0], params.hero_type, params.companion, params.mood)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


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
        vals = asp_valid()
        print(f"{len(vals)} valid triples:")
        for t in vals:
            print("  ", t)
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
            header = f"### {p.hero} in {p.setting} with {p.companion}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
