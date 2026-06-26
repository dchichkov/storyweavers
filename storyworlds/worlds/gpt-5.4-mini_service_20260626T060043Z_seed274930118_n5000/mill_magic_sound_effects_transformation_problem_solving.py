#!/usr/bin/env python3
"""
storyworlds/worlds/mill_magic_sound_effects_transformation_problem_solving.py
=============================================================================

A small slice-of-life storyworld about a working mill, a little bit of magic,
sound effects, and a practical problem that gets solved by a transformation.

The premise:
- A child or helper visits a mill with a grown-up.
- They hear the mill make lively sounds: whirr, clack, rumble, whoosh.
- A magical mishap causes something ordinary to transform into something hard
  to use.
- The characters solve the problem with calm, hands-on thinking.

This world is intentionally modest and grounded: the magic is playful, the
conflict is small, and the ending returns to ordinary life with one useful
change in the world state.
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
    held_by: Optional[str] = None
    transformed: bool = False
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


@dataclass
class Setting:
    place: str = "the old mill"
    indoor: bool = True
    soundscape: list[str] = field(default_factory=lambda: ["whirr", "clack", "rumble"])


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    type: str
    category: str
    transform_to: str
    sound: str
    fix: str
    helps_with: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class StoryParams:
    thing: str
    hero_name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.magic_noise: str = ""

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


def sound_line(sound: str) -> str:
    return {
        "whirr": "whirr-whirr",
        "clack": "clack-clack",
        "rumble": "rumble-rumble",
        "whoosh": "whoosh",
        "ping": "ping!",
        "pop": "pop!",
        "sparkle": "tinkle-tinkle",
    }.get(sound, sound)


def introduce(world: World, hero: Entity, helper: Entity, thing: Thing) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a careful eye and a bright "
        f"curious smile."
    )
    world.say(
        f"One morning, {hero.id} went to {world.setting.place} with {helper.pronoun('possessive')} "
        f"{helper.type} to see the {thing.label} work."
    )
    world.say(
        f"Inside, the air filled with {', '.join(sound_line(s) for s in world.setting.soundscape)}."
    )


def observe(world: World, hero: Entity, thing: Thing) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    world.say(
        f"{hero.id} loved the {thing.sound} sound of the {thing.label}; it made the room feel busy and alive."
    )


def magical_misfire(world: World, hero: Entity, thing: Thing) -> None:
    hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
    thing_entity = world.get(thing.id)
    thing_entity.transformed = True
    thing_entity.type = thing.transform_to
    thing_entity.label = thing.transform_to
    world.magic_noise = sound_line("sparkle")
    world.say(
        f"Then the magic went {world.magic_noise} and the {thing.label} changed into a {thing.transform_to}."
    )


def problem(world: World, hero: Entity, helper: Entity, thing: Thing) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"But the {thing.transform_to} was too {thing.helps_with} to use for the work they needed to do."
    )
    world.say(
        f"{helper.pronoun('subject').capitalize()} frowned and said they would need a simple fix."
    )


def solution(world: World, hero: Entity, helper: Entity, thing: Thing) -> None:
    thing_entity = world.get(thing.id)
    thing_entity.transformed = False
    thing_entity.type = thing.category
    thing_entity.label = thing.label
    thing_entity.meters["fixed"] = 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"{hero.id} thought for a moment, then pointed to the little lever by the side of the mill."
    )
    world.say(
        f"They turned it together, and the gears gave a friendly clack-clack."
    )
    world.say(
        f"The magic settled down, the {thing.label} turned back to normal, and the work could go on."
    )


def ending(world: World, hero: Entity, helper: Entity, thing: Thing) -> None:
    world.say(
        f"By the end of the morning, {hero.id} was smiling beside {helper.pronoun('possessive')} {helper.type}, "
        f"and the {thing.label} was making its steady {thing.sound} sound again."
    )
    world.say(
        f"It was just an ordinary day at the mill, but now everyone knew how to calm a sudden spell."
    )


MILL_THINGS = {
    "flour": Thing(
        id="thing",
        label="flour sack",
        phrase="a flour sack",
        type="sack",
        category="sack",
        transform_to="balloon",
        sound="soft puff",
        fix="heavy",
        helps_with="floaty",
    ),
    "gear": Thing(
        id="thing",
        label="gear wheel",
        phrase="a gear wheel",
        type="wheel",
        category="wheel",
        transform_to="toy pinwheel",
        sound="clack",
        fix="spinning",
        helps_with="tiny and wobbly",
    ),
    "cloth": Thing(
        id="thing",
        label="cloth bundle",
        phrase="a cloth bundle",
        type="bundle",
        category="bundle",
        transform_to="paper bird",
        sound="swish",
        fix="flimsy",
        helps_with="light as a feather",
    ),
}

HELPERS = {
    "mother": "mother",
    "father": "father",
    "aunt": "aunt",
    "uncle": "uncle",
    "baker": "baker",
}

GIRL_NAMES = ["Mia", "Nina", "Lena", "Tara", "Ivy", "June"]
BOY_NAMES = ["Owen", "Eli", "Noah", "Finn", "Theo", "Ben"]
TRAITS = ["patient", "curious", "gentle", "careful", "cheerful"]


def build_world(params: StoryParams) -> World:
    world = World(Setting())
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.gender))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper))
    thing = MILL_THINGS[params.thing]
    target = world.add(Entity(
        id="thing",
        kind="thing",
        type=thing.category,
        label=thing.label,
        phrase=thing.phrase,
        owner=helper.id,
    ))
    world.facts.update(hero=hero, helper=helper, thing_cfg=thing, thing=target, params=params)
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    thing: Thing = world.facts["thing_cfg"]

    introduce(world, hero, helper, thing)
    world.para()
    observe(world, hero, thing)
    magical_misfire(world, hero, thing)
    problem(world, hero, helper, thing)
    world.para()
    solution(world, hero, helper, thing)
    ending(world, hero, helper, thing)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    thing: Thing = world.facts["thing_cfg"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    return [
        f"Write a short slice-of-life story about {hero.id} at the mill, with the sound of a {thing.label} and a tiny magic mishap.",
        f"Tell a gentle story where {hero.id} and the {helper.type} solve a problem after the {thing.label} turns into something unexpected.",
        f"Write a child-friendly story that includes the words mill, magic, and {thing.sound} sound effects.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    thing: Thing = world.facts["thing_cfg"]
    return [
        QAItem(
            question=f"Where did {hero.id} go with the {helper.type}?",
            answer=f"{hero.id} went to {world.setting.place} with {helper.pronoun('possessive')} {helper.type}.",
        ),
        QAItem(
            question=f"What sound did the {thing.label} make before the magic happened?",
            answer=f"The {thing.label} made a {thing.sound} sound before the magic spell changed it.",
        ),
        QAItem(
            question=f"What changed after the magic went off?",
            answer=f"The {thing.label} turned into a {thing.transform_to}, which made the work harder for a moment.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They turned the little lever together, which calmed the spell and changed the {thing.label} back.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    thing: Thing = world.facts["thing_cfg"]
    return [
        QAItem(
            question="What is a mill?",
            answer="A mill is a place where people use tools or machines to grind or prepare things like grain.",
        ),
        QAItem(
            question="What does magic usually do in a story?",
            answer="Magic in a story can make surprising changes happen, like transforming one thing into another.",
        ),
        QAItem(
            question="Why do machines make sound effects?",
            answer="Machines make sound effects because their parts move and bump and spin while they work.",
        ),
        QAItem(
            question=f"What does {thing.sound} sound like?",
            answer=f"It sounds like a small lively noise, the kind you might hear when something light or busy is moving.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.transformed:
            bits.append("transformed=True")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "mill")]
    lines.append(asp.fact("feature", "sound_effects"))
    lines.append(asp.fact("feature", "transformation"))
    lines.append(asp.fact("feature", "problem_solving"))
    for key, thing in MILL_THINGS.items():
        lines.append(asp.fact("thing", key))
        lines.append(asp.fact("transforms_to", key, thing.transform_to))
        lines.append(asp.fact("sound", key, thing.sound))
        lines.append(asp.fact("helps_with", key, thing.helps_with))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


ASP_RULES = r"""
can_tell_story(T) :- thing(T), transforms_to(T, _), sound(T, _), helps_with(T, _).
problem(T) :- thing(T), transforms_to(T, X), X != T.
solution(T) :- can_tell_story(T), problem(T).
#show can_tell_story/1.
#show problem/1.
#show solution/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_tell_story/1. #show problem/1. #show solution/1."))
    atoms = set(asp.atoms(model, "can_tell_story"))
    expected = set((k,) for k in MILL_THINGS)
    if atoms != expected:
        print("MISMATCH between ASP and Python registry")
        print("ASP:", sorted(atoms))
        print("PY :", sorted(expected))
        return 1
    print(f"OK: clingo gate matches registry ({len(expected)} things).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mill storyworld with magic sound effects and problem solving.")
    ap.add_argument("--thing", choices=sorted(MILL_THINGS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=sorted(HELPERS))
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
    thing = args.thing or rng.choice(sorted(MILL_THINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(sorted(HELPERS))
    trait = args.trait or rng.choice(TRAITS)
    if thing not in MILL_THINGS:
        raise StoryError("Unknown thing.")
    if gender not in MILL_THINGS[thing].genders:
        raise StoryError("That thing does not fit the chosen child in this world.")
    return StoryParams(thing=thing, hero_name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show can_tell_story/1. #show problem/1. #show solution/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show can_tell_story/1. #show problem/1. #show solution/1."))
        print("ASP atoms:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    curated = [
        StoryParams(thing="flour", hero_name="Mia", gender="girl", helper="mother", trait="curious"),
        StoryParams(thing="gear", hero_name="Owen", gender="boy", helper="father", trait="careful"),
        StoryParams(thing="cloth", hero_name="Lena", gender="girl", helper="aunt", trait="gentle"),
    ]

    if args.all:
        samples = [generate(p) for p in curated]
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
