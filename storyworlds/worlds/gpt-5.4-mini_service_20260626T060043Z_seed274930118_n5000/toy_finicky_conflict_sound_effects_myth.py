#!/usr/bin/env python3
"""
toy_finicky_conflict_sound_effects_myth.py
==========================================

A small mythic story world about a beloved toy, a finicky problem, a conflict,
and the sounds that mark the turning point.

The world is built from a simple seed-tale shape:
a child or small hero loves a special toy; the toy is fussy or finicky in some
way; conflict grows when the toy will not work as expected; then a clever,
gentle fix restores peace and ends with a satisfying sound image.

The simulation models both physical meters and emotional memes:
- meters track the toy's state, distance, wear, and sound-making
- memes track annoyance, worry, pride, delight, and reconciliation

The prose is generated from world state, not from a frozen paragraph shell.
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
    caretakers: list[str] = field(default_factory=list)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "goddess"}
        male = {"boy", "father", "man", "king", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    sound: str
    finicky: str
    problem: str
    fix: str
    matters: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Setting:
    place: str
    time: str
    light: str
    affords: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.sound_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.sound_log = list(self.sound_log)
        return clone


@dataclass
class StoryParams:
    place: str
    toy: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "courtyard": Setting(place="the moonlit courtyard", time="night", light="silver", affords={"wind", "bells"}),
    "forest": Setting(place="the pine forest", time="dusk", light="gold", affords={"wind", "drums"}),
    "hall": Setting(place="the stone hall", time="morning", light="bright", affords={"bells", "echo"}),
}

TOYS = {
    "drum": Toy(
        id="drum",
        label="drum",
        phrase="a small drum with a red strap",
        sound="boom",
        finicky="it only liked a soft touch",
        problem="its skin went dull when struck too hard",
        fix="a gentle tap with warm hands",
        matters={"drums", "echo"},
        tags={"sound", "toy", "finicky", "conflict"},
    ),
    "flute": Toy(
        id="flute",
        label="flute",
        phrase="a silver flute with tiny holes",
        sound="toot",
        finicky="it would squeak if breathed on too sharply",
        problem="its song turned thin when rushed",
        fix="a slow breath and careful fingers",
        matters={"wind", "echo"},
        tags={"sound", "toy", "finicky", "conflict"},
    ),
    "bell": Toy(
        id="bell",
        label="bell",
        phrase="a bright bell on a blue cord",
        sound="ding",
        finicky="it only sang when swung at the right pace",
        problem="it gave a dull clack when shaken in anger",
        fix="a calm swing from a steady wrist",
        matters={"bells", "echo"},
        tags={"sound", "toy", "finicky", "conflict"},
    ),
}

HERO_NAMES = ["Mira", "Tavi", "Nilo", "Sera", "Arin", "Luma", "Pax", "Ivo"]
HELPER_NAMES = ["Grandmother", "Uncle", "Sister", "Brother", "Friend", "Aunt"]
TRAITS = ["brave", "curious", "gentle", "stubborn", "eager", "dreamy"]


def story_intro(hero: Entity, toy: Toy, setting: Setting) -> str:
    return (
        f"In {setting.place}, {hero.id} was a {hero.traits[0]} little {hero.type} "
        f"who loved {toy.phrase}."
    )


def toy_love(hero: Entity, toy: Toy) -> str:
    hero.memes["love"] = hero.memes.get("love", 0) + 1
    return f"{hero.pronoun().capitalize()} listened for its {toy.sound} sound as if it were a secret."


def setting_detail(setting: Setting, toy: Toy) -> str:
    if "bells" in toy.matters and "bells" in setting.affords:
        return f"The {setting.place} held a hush that made every tiny ring seem important."
    if "drums" in toy.matters and "drums" in setting.affords:
        return f"The {setting.place} felt wide enough for a brave beat to travel far."
    return f"Even the air there seemed to wait for a careful little tune."


def predict_problem(world: World, hero: Entity, toy: Toy) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["impatience"] = 1.0
    return True


def play_attempt(world: World, hero: Entity, toy: Toy) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.meters["use"] = hero.meters.get("use", 0) + 1
    hero.meters["noise"] = hero.meters.get("noise", 0) + 1
    world.sound_log.append(toy.sound)
    if "soft touch" in toy.finicky:
        hero.memes["frustration"] = hero.memes.get("frustration", 0) + 1
        world.sound_log.append("clack")
        hero.meters["problem"] = hero.meters.get("problem", 0) + 1


def conflict_turn(world: World, hero: Entity, helper: Entity, toy: Toy) -> None:
    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    helper.memes["worry"] = helper.memes.get("worry", 0) + 1
    world.say(
        f"But when {hero.id} tried to hurry, the {toy.label} answered with a sad {toy.sound} and then a sharp clack."
    )
    world.say(
        f"{hero.id} frowned. {hero.pronoun().capitalize()} wanted the toy to behave like magic right away."
    )


def repair(world: World, hero: Entity, helper: Entity, toy: Toy) -> None:
    hero.memes["conflict"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    helper.memes["relief"] = helper.memes.get("relief", 0) + 1
    toy_state = world.facts.setdefault("toy_state", {})
    toy_state["fixed"] = True
    world.sound_log.append(toy.sound)
    world.sound_log.append(toy.sound)
    world.say(
        f"{helper.id} showed {hero.id} a gentler way: {toy.fix}."
    )
    world.say(
        f"This time the {toy.label} made a clean {toy.sound}, and the clack disappeared like a bad dream."
    )


def tell_story(world: World, hero: Entity, helper: Entity, toy: Toy) -> None:
    world.say(story_intro(hero, toy, world.setting))
    world.say(toy_love(hero, toy))
    world.say(setting_detail(world.setting, toy))
    world.para()
    world.say(
        f"One day, {hero.id} carried the {toy.label} into {world.setting.place} and wanted to make it sing at once."
    )
    world.say(
        f"But {toy.finicky.capitalize()}, and that was the trouble."
    )
    play_attempt(world, hero, toy)
    conflict_turn(world, hero, helper, toy)
    world.para()
    repair(world, hero, helper, toy)
    world.say(
        f"After that, the little music flowed again, and {hero.id} laughed at the soft {toy.sound}-{toy.sound} echo."
    )


def valid_combo(place: str, toy_id: str) -> bool:
    return toy_id in TOYS and place in SETTINGS and TOYS[toy_id].matters.intersection(SETTINGS[place].affords)


def valid_story_triples() -> list[tuple[str, str]]:
    return sorted((place, toy_id) for place in SETTINGS for toy_id in TOYS if valid_combo(place, toy_id))


def explain_rejection(place: str, toy_id: str) -> str:
    toy = TOYS[toy_id]
    setting = SETTINGS[place]
    return (
        f"(No story: {toy.label} belongs in a place that supports {sorted(toy.matters)}, "
        f"but {setting.place} supports {sorted(setting.affords)}. The finicky trouble would not feel like a true conflict there.)"
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    toy = TOYS[params.toy]
    world = World(setting)
    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type=params.hero_type,
        traits=[params.trait, "small"],
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type=params.helper_type,
        traits=["kind"],
    ))
    toy_ent = world.add(Entity(
        id=toy.id,
        type="toy",
        label=toy.label,
        phrase=toy.phrase,
        owner=hero.id,
    ))
    world.facts.update(hero=hero, helper=helper, toy=toy, toy_ent=toy_ent, setting=setting)
    tell_story(world, hero, helper, toy)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, toy, setting = f["hero"], f["helper"], f["toy"], f["setting"]
    return [
        f'Write a short myth-like story for a child about a {hero.type} named {hero.id}, a finicky {toy.label}, and a careful helper.',
        f"Tell a gentle legend where {hero.id} wants to use {toy.phrase} in {setting.place}, but it only works with patience and a softer touch.",
        f"Write a tiny myth with the word '{toy.label}' that ends in a happy sound instead of a clash.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, toy, setting = f["hero"], f["helper"], f["toy"], f["setting"]
    return [
        QAItem(
            question=f"What did {hero.id} love in {setting.place}?",
            answer=f"{hero.id} loved {toy.phrase}, and listened for its {toy.sound} sound.",
        ),
        QAItem(
            question=f"Why was the {toy.label} hard to use?",
            answer=f"It was finicky because {toy.finicky}, so hurrying made it stumble into a clack.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the trouble?",
            answer=f"{helper.id} helped by showing {hero.id} {toy.fix}.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The conflict settled, and the {toy.label} made a clean {toy.sound} again instead of a sad clack.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    toy: Toy = f["toy"]
    qa = [
        QAItem(
            question="What does finicky mean?",
            answer="Finicky means something is picky, fussy, or hard to please unless you do things just right.",
        ),
        QAItem(
            question="What is a toy?",
            answer="A toy is something people play with, like a drum, a bell, or a flute.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a special noise that helps tell what is happening, like a boom, ding, or clack.",
        ),
    ]
    if "sound" in toy.tags:
        qa.append(
            QAItem(
                question=f"What kind of sound did the {toy.label} make in the story?",
                answer=f"It made a {toy.sound} sound when things went well, and a clack when the conflict got worse.",
            )
        )
    return qa


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
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  sounds: {world.sound_log}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/2.
valid(Place, Toy) :- setting(Place), toy(Toy), affords(Place, SoundKind), matters(Toy, SoundKind).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", place, a))
    for toy_id, toy in TOYS.items():
        lines.append(asp.fact("toy", toy_id))
        for m in sorted(toy.matters):
            lines.append(asp.fact("matters", toy_id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_story_triples())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_story_triples() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


CURATED = [
    StoryParams(place="courtyard", toy="bell", hero="Mira", hero_type="girl", helper="Grandmother", helper_type="woman", trait="curious"),
    StoryParams(place="forest", toy="drum", hero="Tavi", hero_type="boy", helper="Uncle", helper_type="man", trait="stubborn"),
    StoryParams(place="hall", toy="flute", hero="Sera", hero_type="girl", helper="Friend", helper_type="boy", trait="gentle"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic toy story world with finicky conflict and sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["woman", "man", "girl", "boy"])
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
    if args.place and args.toy and not valid_combo(args.place, args.toy):
        raise StoryError(explain_rejection(args.place, args.toy))
    place = args.place or rng.choice(list(SETTINGS))
    toy = args.toy or rng.choice([t for t in TOYS if valid_combo(place, t)])
    if not valid_combo(place, toy):
        raise StoryError(explain_rejection(place, toy))
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["woman", "man", "girl", "boy"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, toy=toy, hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type, trait=trait)


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} valid (place, toy) pairs:\n")
        for place, toy in triples:
            print(f"  {place:10} {toy}")
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
            header = f"### {p.hero}: {p.toy} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
