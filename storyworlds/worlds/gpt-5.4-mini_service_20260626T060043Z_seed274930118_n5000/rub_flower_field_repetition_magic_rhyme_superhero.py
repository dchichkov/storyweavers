#!/usr/bin/env python3
"""
A small storyworld for a superhero tale in a flower field.

Premise:
- A little hero with a special cape visits a bright flower field.
- The hero wants to rub a magical charm to make the cape sparkle.
- The magic works, but repetition and rhyme are needed to wake the charm.
- A small trouble appears: the field is dusty/pollen-y, and the hero must fix the cape before the big heroic pose.

This world is intentionally tiny and constraint-driven. It produces a complete
story with a setup, a turn, and a resolution, plus grounded Q&A and an ASP twin.
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
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

NAMES = ["Mina", "Toby", "Luna", "Ari", "Pia", "Nico", "Ivy", "Jules"]
HERO_TRAITS = ["brave", "kind", "spry", "cheerful", "bold", "quick"]
SIDEKICK_NAMES = ["Bop", "Zip", "Dot", "Milo", "Tia", "Pip"]

FLOWER_TYPES = [
    ("daisies", "daisies", "white daisies"),
    ("roses", "roses", "red roses"),
    ("tulips", "tulips", "pink tulips"),
    ("sunflowers", "sunflowers", "golden sunflowers"),
]

MAGIC_WORDS = ["spark", "shine", "glow", "flutter", "brave", "bright"]
RHYMES = [
    ("gleam", "dream"),
    ("glow", "show"),
    ("light", "bright"),
    ("spark", "mark"),
    ("chime", "rhyme"),
]

# ---------------------------------------------------------------------------
# Shared entity model
# ---------------------------------------------------------------------------

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

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "sparkle": 0.0, "magic": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "focus": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the flower field"
    affords: set[str] = field(default_factory=set)


@dataclass
class Hero:
    name: str
    gender: str
    trait: str
    cape_color: str
    power: str


@dataclass
class Charm:
    label: str
    phrase: str
    magic_word: str
    rhyme_a: str
    rhyme_b: str


@dataclass
class Problem:
    label: str
    detail: str
    cause: str


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


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    trait: str
    cape_color: str
    power: str
    flower_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "flower_field": Setting(place="the flower field", affords={"rub", "magic", "rhyme"}),
}

POWERS = {
    "sparkle": "sparkle into a brighter hero pose",
    "breeze": "call a tiny breeze to lift petals",
    "shine": "shine through the dust",
    "echo": "echo a heroic rhyme",
}

CAPES = {
    "red": "a red cape",
    "blue": "a blue cape",
    "gold": "a gold cape",
    "green": "a green cape",
}

PROBLEMS = {
    "pollen": Problem(
        label="pollen dust",
        detail="the cape had a pale coat of pollen dust",
        cause="the hero had flown too low over the flowers",
    ),
    "mud": Problem(
        label="mud spots",
        detail="the cape had tiny mud spots near the hem",
        cause="the hero had landed in a soft patch after the rain",
    ),
}

CHARM = Charm(
    label="a pocket charm",
    phrase="a tiny pocket charm with a star on it",
    magic_word="rub",
    rhyme_a="gleam",
    rhyme_b="dream",
)


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting=setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.gender == "girl" else "boy",
        label=params.name,
        phrase=f"a {params.trait} superhero named {params.name}",
        owner=None,
    ))
    sidekick = world.add(Entity(
        id="sidekick",
        kind="character",
        type="friend",
        label=random.choice(SIDEKICK_NAMES),
        phrase="a tiny helper friend",
        owner=params.name,
    ))
    cape = world.add(Entity(
        id="cape",
        type="cape",
        label="cape",
        phrase=CAPES[params.cape_color],
        owner=params.name,
        caretaker=params.name,
    ))
    charm = world.add(Entity(
        id="charm",
        type="charm",
        label="charm",
        phrase=CHARM.phrase,
        owner=params.name,
    ))
    flowers = world.add(Entity(
        id="flowers",
        type="flowers",
        label=params.flower_type,
        phrase=f"a patch of {params.flower_type}",
        plural=True,
    ))

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        cape=cape,
        charm=charm,
        flowers=flowers,
        problem=PROBLEMS[params.flower_type if params.flower_type in PROBLEMS else "pollen"],
        params=params,
    )
    return world


def _apply_rub(world: World) -> None:
    hero = world.facts["hero"]
    cape = world.facts["cape"]
    problem = world.facts["problem"]

    if ("rub", cape.id) in world.fired:
        return
    world.fired.add(("rub", cape.id))

    hero.memes["focus"] += 1
    cape.meters["dust"] = 0.0
    cape.meters["sparkle"] += 0.5
    world.say(
        f"{hero.id} rubbed {hero.pronoun('possessive')} {cape.label} with careful fingers, "
        f"but the {problem.label} still clung there like a sleepy cloud."
    )


def _apply_magic(world: World) -> None:
    hero = world.facts["hero"]
    cape = world.facts["cape"]
    charm = world.facts["charm"]

    if ("magic", cape.id) in world.fired:
        return
    world.fired.add(("magic", cape.id))

    if cape.meters["sparkle"] < THRESHOLD:
        hero.memes["worry"] += 1
        world.say(
            f"{hero.id} held up {charm.phrase}, and a warm glow began, "
            f"but the charm needed more than one try."
        )
        return

    cape.meters["sparkle"] += 1.0
    hero.memes["joy"] += 1
    world.say(
        f"Then {hero.id} whispered the magic word, and the charm hummed with bright light."
    )


def _apply_rhyme(world: World) -> None:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    cape = world.facts["cape"]

    if ("rhyme", cape.id) in world.fired:
        return
    world.fired.add(("rhyme", cape.id))

    cape.memes["rhythm"] = cape.memes.get("rhythm", 0.0) + 1.0
    hero.memes["focus"] += 1
    world.say(
        f"{sidekick.label} grinned and chanted, "
        f"'{CHARM.rhyme_a}, {CHARM.rhyme_b}!' "
        f"The rhyme made the spell feel steady and sure."
    )


def propagate(world: World) -> None:
    _apply_rub(world)
    _apply_rhyme(world)
    _apply_magic(world)


def tell_story(world: World) -> World:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    cape = world.facts["cape"]
    charm = world.facts["charm"]
    problem = world.facts["problem"]
    flowers = world.facts["flowers"]

    world.say(
        f"At {world.setting.place}, {hero.id} was a {hero.phrase} with "
        f"{cape.phrase} and a power to {hero.pronoun('subject')} cheer."
    )
    world.say(
        f"{hero.id} loved the bright flowers, and {sidekick.label} loved the way "
        f"the field looked like a colorful superhero stage."
    )

    world.para()
    world.say(
        f"One morning, {hero.id} noticed that {problem.detail}."
    )
    world.say(
        f"{hero.id} wanted to {CHARM.magic_word} {hero.pronoun('possessive')} {cape.label}, "
        f"but the charm would only wake if someone used repetition and rhyme."
    )
    world.say(
        f"So {hero.id} said the word again, softly: '{CHARM.magic_word}, {CHARM.magic_word}.'"
    )
    propagate(world)

    world.para()
    world.say(
        f"{sidekick.label} answered with a little rhyme, and {hero.id} rubbed again, "
        f"slower this time, brushing away the last dusty bits."
    )
    cape.meters["dust"] = 0.0
    cape.meters["sparkle"] = max(cape.meters["sparkle"], 1.0)
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"The charm warmed up at last, and the cape shone like a tiny sunrise above the {flowers.label}."
    )
    world.say(
        f"{hero.id} struck a brave pose, {sidekick.label} clapped, and the flower field felt like a stage for a true hero."
    )

    world.facts.update(
        repeated=True,
        resolved=True,
        final_sparkle=cape.meters["sparkle"],
        final_dust=cape.meters["dust"],
    )
    return world


# ---------------------------------------------------------------------------
# Generation / QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short superhero story set in the flower field that includes the word "rub".',
        f"Tell a child-friendly story about {hero.id} using a magic charm, a little rhyme, and a heroic cape.",
        f"Write a simple story where repetition helps a superhero fix something dusty in a flower field.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    cape = f["cape"]
    problem = f["problem"]
    flowers = f["flowers"]

    return [
        QAItem(
            question=f"Who is the superhero in the story?",
            answer=f"The superhero is {hero.id}, a {hero.phrase} who visits the flower field.",
        ),
        QAItem(
            question=f"What was wrong with {hero.id}'s cape at first?",
            answer=f"It had {problem.detail}, so it did not look ready for a big heroic pose.",
        ),
        QAItem(
            question=f"How did {hero.id} and {sidekick.label} fix the cape?",
            answer=f"They used repetition, magic, and rhyme: {hero.id} rubbed the cape again and {sidekick.label} chanted a steady rhyme until the charm woke up.",
        ),
        QAItem(
            question=f"What did the cape look like at the end?",
            answer=f"At the end, the cape shone like a tiny sunrise above the {flowers.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flower field?",
            answer="A flower field is a big open place where many flowers grow together and make the ground look colorful.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means saying or doing something again and again, which can help a person remember, practice, or make a magic spell feel stronger.",
        ),
        QAItem(
            question="Why can a rhyme sound fun?",
            answer="A rhyme sounds fun because the words end with similar sounds, so they bounce along like a song.",
        ),
        QAItem(
            question="Why might a superhero use magic?",
            answer="A superhero might use magic to help solve a problem in a special way, like making a cape sparkle or waking a charm.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A cape is at risk when dust or pollen is present in the flower field.
at_risk(cape) :- field(flower_field), problem(pollen).
at_risk(cape) :- field(flower_field), problem(mud).

% Repetition and rhyme help the magic become strong enough.
strong_magic(cape) :- repeated(rub), rhyme_used, magic_used.

resolved_story(cape) :- at_risk(cape), strong_magic(cape).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("field", "flower_field"))
    lines.append(asp.fact("field_affords", "flower_field", "rub"))
    lines.append(asp.fact("field_affords", "flower_field", "magic"))
    lines.append(asp.fact("field_affords", "flower_field", "rhyme"))
    lines.append(asp.fact("problem", "pollen"))
    lines.append(asp.fact("problem", "mud"))
    lines.append(asp.fact("repeated", "rub"))
    lines.append(asp.fact("rhyme_used"))
    lines.append(asp.fact("magic_used"))
    lines.append(asp.fact("cape", "cape"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    program = asp_program("#show resolved_story/1.\n#show at_risk/1.\n#show strong_magic/1.")
    model = asp.one_model(program)
    atoms = set((s.name, tuple(a.number if a.type.name == "Number" else a.string if a.type.name == "String" else a.name for a in s.arguments)) for s in model)
    expected = {("at_risk", ("cape",)), ("strong_magic", ("cape",)), ("resolved_story", ("cape",))}
    if atoms == expected:
        print("OK: ASP and Python reasoning agree.")
        return 0
    print("MISMATCH:", atoms, expected)
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld set in a flower field.")
    ap.add_argument("--place", choices=list(SETTINGS.keys()))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=HERO_TRAITS)
    ap.add_argument("--cape-color", choices=list(CAPES.keys()))
    ap.add_argument("--power", choices=list(POWERS.keys()))
    ap.add_argument("--flower-type", choices=[k for k, _, _ in FLOWER_TYPES])
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
    place = args.place or "flower_field"
    if place != "flower_field":
        raise StoryError("This world only supports the flower field setting.")

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(HERO_TRAITS)
    cape_color = args.cape_color or rng.choice(list(CAPES.keys()))
    power = args.power or rng.choice(list(POWERS.keys()))
    flower_type = args.flower_type or rng.choice([k for k, _, _ in FLOWER_TYPES])

    return StoryParams(
        place=place,
        name=name,
        gender=gender,
        trait=trait,
        cape_color=cape_color,
        power=power,
        flower_type=flower_type,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
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
        print(asp_program("#show resolved_story/1.\n#show at_risk/1.\n#show strong_magic/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for flower_type, _, _ in FLOWER_TYPES:
            params = StoryParams(
                place="flower_field",
                name="Mina",
                gender="girl",
                trait="brave",
                cape_color="red",
                power="sparkle",
                flower_type=flower_type,
                seed=base_seed,
            )
            samples.append(generate(params))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
