#!/usr/bin/env python3
"""
storyworlds/worlds/symbol_scowl_transformation_fable.py
=======================================================

A small fable-world about a proud symbol, a heavy scowl, and a gentle
transformation.

Seed tale:
---
A little badger found a bright carved symbol on a gate and thought it made him
more important than the other forest animals. Whenever the rabbits or mice came
near, he scowled and stood in the way. The symbol on the gate grew dull and
cold.

One windy morning, a hare tried to carry home a fallen basket of berries. The
badger scowled at first, but the berries kept rolling away. When he finally
helped, the badger's scowl faded. The carved symbol warmed, then shone like a
small sun.

The animals remembered that a symbol means little unless the one who carries it
acts kindly.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"doe", "girl", "mother", "woman", "hare"}
        male = {"badger", "boy", "father", "man", "fox", "wolf"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = False


@dataclass
class Relic:
    label: str
    phrase: str
    type: str = "symbol"
    mood: str = "glow"
    can_transform: bool = True


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    relic: str
    seed: Optional[int] = None


SETTINGS = {
    "forest_gate": Setting(place="the forest gate"),
    "meadow": Setting(place="the meadow"),
    "lantern_path": Setting(place="the lantern path"),
}

RELICS = {
    "carved_symbol": Relic(
        label="carved symbol",
        phrase="a bright carved symbol",
        mood="glow",
        can_transform=True,
    ),
    "badge": Relic(
        label="badge",
        phrase="a polished badge with a little mark",
        mood="glow",
        can_transform=True,
    ),
    "stone_token": Relic(
        label="stone token",
        phrase="a smooth stone token",
        mood="glow",
        can_transform=True,
    ),
}

HERO_NAMES = ["Milo", "Bram", "Pip", "Toby", "Nell", "Mira", "Roo", "Hob"]
HELPER_NAMES = ["Hare", "Penny", "Wren", "Sage", "Moss", "Tilly", "Fern"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.transform_level: float = 0.0

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


def _moral() -> str:
    return "The animals learned that a proud scowl can make a symbol dim, but kindness can make it shine."


def _transform(world: World, relic: Entity, hero: Entity) -> None:
    if hero.memes.get("kindness", 0.0) >= THRESHOLD and hero.memes.get("scowl", 0.0) < THRESHOLD:
        sig = ("transform", relic.id)
        if sig not in world.fired:
            world.fired.add(sig)
            relic.meters["glow"] = 1.0
            relic.meters["warm"] = 1.0
            world.transform_level = 1.0
            world.say(f"The {relic.label} warmed and shone like a small sun.")


def tell(setting: Setting, relic_cfg: Relic, hero_name: str, hero_type: str,
         helper_name: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label=helper_name))
    relic = world.add(Entity(
        id="relic",
        type=relic_cfg.type,
        label=relic_cfg.label,
        phrase=relic_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))
    relic.meters["glow"] = 0.5
    relic.meters["warm"] = 0.0

    world.say(
        f"At {setting.place}, {hero.id} found {relic_cfg.phrase} and thought it made {hero.pronoun('object')} more important than the other animals."
    )
    world.say(
        f"Whenever little neighbors came near, {hero.id} would scowl and stand in the way."
    )
    hero.memes["pride"] = 1.0
    hero.memes["scowl"] = 1.0
    relic.meters["glow"] = 0.0
    relic.meters["cold"] = 1.0
    world.say(f"After many hard looks, the {relic.label} grew dull and cold.")

    world.para()
    world.say(
        f"One windy morning, {helper.id} tried to carry home a basket of berries, but the berries kept rolling across the path."
    )
    world.say(
        f"{hero.id} scowled at first, because helping did not feel as grand as guarding the gate."
    )
    hero.memes["hesitation"] = 1.0
    if world.setting.place == "the forest gate":
        world.say(
            f"Yet the berries rolled beneath the gate, and {helper.id} could not gather them alone."
        )
    else:
        world.say(
            f"Yet the path was uneven, and {helper.id} could not gather them alone."
        )

    world.para()
    hero.memes["kindness"] = 1.0
    hero.memes["scowl"] = 0.0
    world.say(
        f"At last, {hero.id} lowered {hero.pronoun('possessive')} eyes, picked up the berries, and carried them carefully back."
    )
    world.say(
        f"{helper.id} smiled, and the other animals stopped to watch."
    )
    _transform(world, relic, hero)

    world.para()
    world.say(
        f"{hero.id} no longer guarded the symbol as if it were a crown. {hero.pronoun().capitalize()} wore {hero.pronoun('object')} like a promise to be useful."
    )
    world.say(_moral())

    world.facts.update(
        hero=hero,
        helper=helper,
        relic=relic,
        setting=setting,
        transformed=world.transform_level >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    relic = f["relic"]
    return [
        f'Write a short fable about {hero.id}, a {hero.type}, a {relic.label}, and a scowl that changes into kindness.',
        f"Tell a child-friendly story where {helper.id} needs help, and {hero.id} learns what the symbol really means.",
        "Write a simple fable about pride softening into helpfulness, with a glowing symbol at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    relic = f["relic"]
    qa = [
        QAItem(
            question=f"What did {hero.id} find at {world.setting.place}?",
            answer=f"{hero.id} found {relic.phrase} at {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did the {relic.label} grow dull at first?",
            answer=f"It grew dull because {hero.id} kept scowling and acting proud instead of being kind.",
        ),
        QAItem(
            question=f"What happened when {hero.id} helped {helper.id} with the berries?",
            answer=f"{hero.id} stopped scowling, helped carry the berries, and the {relic.label} warmed and shone.",
        ),
    ]
    if f.get("transformed"):
        qa.append(
            QAItem(
                question=f"How did the symbol change by the end?",
                answer=f"It changed from dull and cold into a warm symbol that shone like a small sun.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a symbol?",
            answer="A symbol is a sign or mark that can stand for an idea, a place, or a promise.",
        ),
        QAItem(
            question="What does scowling look like?",
            answer="Scowling looks like a face with tight eyebrows and a frown, as if someone is cross or unhappy.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a new form or becomes very different.",
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
    lines.append("== World knowledge ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  transform_level={world.transform_level}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="forest_gate", hero="Bram", hero_type="badger", helper="Hare", helper_type="hare", relic="carved_symbol"),
    StoryParams(place="meadow", hero="Pip", hero_type="fox", helper="Wren", helper_type="bird", relic="badge"),
    StoryParams(place="lantern_path", hero="Toby", hero_type="badger", helper="Moss", helper_type="mouse", relic="stone_token"),
]


ASP_RULES = r"""
% A story is reasonable if a proud hero can become kind and the relic can transform.
proud_hero(H) :- hero(H), pride(H), scowl(H).
kind_hero(H) :- hero(H), kindness(H), not scowl(H).
transforms(R) :- relic(R), kind_hero(H), holds(R,H).
valid_story(P,H,R) :- setting(P), hero(H), relic(R), transforms(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        if r.can_transform:
            lines.append(asp.fact("can_transform", rid))
    for name in HERO_NAMES:
        lines.append(asp.fact("hero", name.lower()))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    if not asp_valid_stories():
        print("MISMATCH: ASP produced no valid stories.")
        return 1
    print(f"OK: ASP produced {len(asp_valid_stories())} valid-story atoms.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about symbol, scowl, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["badger", "fox", "rabbit", "hare", "mouse", "bird"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["badger", "fox", "rabbit", "hare", "mouse", "bird"])
    ap.add_argument("--relic", choices=RELICS)
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
    place = args.place or rng.choice(list(SETTINGS))
    hero_type = args.hero_type or rng.choice(["badger", "fox", "hare"])
    helper_type = args.helper_type or rng.choice(["hare", "mouse", "bird"])
    if args.helper_type is None and helper_type == hero_type:
        helper_type = "hare" if hero_type != "hare" else "mouse"
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    if hero == helper:
        helper = random.choice([n for n in HELPER_NAMES if n != hero])
    relic = args.relic or rng.choice(list(RELICS))
    return StoryParams(place=place, hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type, relic=relic)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], RELICS[params.relic], params.hero, params.hero_type, params.helper, params.helper_type)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(f"{len(asp.atoms(model, 'valid_story'))} valid_story atoms")
        for atom in sorted(set(asp.atoms(model, "valid_story"))):
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.hero} at {p.place} ({p.relic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
