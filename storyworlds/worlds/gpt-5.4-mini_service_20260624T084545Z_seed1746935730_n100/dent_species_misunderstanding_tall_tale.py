#!/usr/bin/env python3
"""
storyworlds/worlds/dent_species_misunderstanding_tall_tale.py
=============================================================

A small, self-contained storyworld about a tall-tale misunderstanding:
someone sees a mysterious dent, starts guessing species, and the truth turns
out to be kinder and smaller than the rumor.

The world is built to support a few close variations of the same kind of tale:
- a curious child or grown-up notices a dent,
- a misunderstanding about species makes the story grow taller,
- a helper investigates by looking for physical clues,
- the ending reveals the real animal and shows what changed.

This script follows the Storyweavers contract:
- standalone stdlib script
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- inline ASP twin with parity verification
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
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

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affordance: str = "looking"


@dataclass
class Creature:
    id: str
    species: str
    label: str
    size: str
    clue: str
    sound: str
    truth_tag: str
    dangerous: bool = False


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    location: str
    could_dent: bool = False


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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _meter(d: dict, key: str) -> float:
    return d.get(key, 0.0)


def _add_meter(d: dict, key: str, amount: float = 1.0) -> None:
    d[key] = d.get(key, 0.0) + amount


SETTINGS = {
    "barn": Setting(place="the barn"),
    "dock": Setting(place="the river dock"),
    "museum": Setting(place="the little town museum", indoor=True),
    "canyon": Setting(place="the red canyon"),
}

CREATURES = {
    "goat": Creature(
        id="goat",
        species="goat",
        label="a mountain goat",
        size="small",
        clue="nibbled tracks near the dent",
        sound="bleat",
        truth_tag="goat",
    ),
    "beaver": Creature(
        id="beaver",
        species="beaver",
        label="a busy beaver",
        size="small",
        clue="wood chips and wet whisker marks",
        sound="chitter",
        truth_tag="beaver",
    ),
    "crane": Creature(
        id="crane",
        species="crane",
        label="a tall crane bird",
        size="tall",
        clue="long prints and a feather on the rail",
        sound="clatter",
        truth_tag="crane",
    ),
    "armadillo": Creature(
        id="armadillo",
        species="armadillo",
        label="an armadillo",
        size="small",
        clue="tiny hoofy scuffs and a round dust trail",
        sound="snuffle",
        truth_tag="armadillo",
    ),
}

OBJECTS = {
    "bucket": ObjectCfg(label="bucket", phrase="a tin bucket", location="the porch rail", could_dent=True),
    "bell": ObjectCfg(label="bell", phrase="a brass bell", location="the barn door", could_dent=True),
    "trough": ObjectCfg(label="trough", phrase="a feed trough", location="the fence line", could_dent=True),
    "sign": ObjectCfg(label="sign", phrase="a metal sign", location="the museum steps", could_dent=True),
}

NAMES = ["Mabel", "June", "Eli", "Nora", "Bo", "Hank", "Lily", "Otis"]
TYPES = ["girl", "boy", "woman", "man"]
TRAITS = ["curious", "brave", "quick-witted", "cheerful", "patient"]


@dataclass
class StoryParams:
    place: str
    creature: str
    object: str
    name: str
    type: str
    helper: str
    trait: str
    seed: Optional[int] = None


def tally_exaggeration(world: World, observer: Entity, creature: Creature) -> None:
    _add_meter(observer.memes, "wonder", 1)
    if creature.size == "tall":
        _add_meter(observer.memes, "awe", 1)
        world.say(f"{observer.id} said the creature was as tall as a ladder to the moon.")
    else:
        world.say(f"{observer.id} said the creature was as quick as a bead rolling downhill.")


def notice_dent(world: World, observer: Entity, obj: Entity, creature: Creature) -> None:
    _add_meter(obj.meters, "dent_seen", 1)
    _add_meter(observer.memes, "concern", 1)
    world.say(
        f"One morning at {world.setting.place}, {observer.id} noticed a fresh dent in the {obj.label}."
    )
    world.say(
        f"Near it were {creature.clue}, which made the whole thing feel like the start of a tall tale."
    )


def guess_species(world: World, observer: Entity, creature: Creature) -> None:
    _add_meter(observer.memes, "misunderstanding", 1)
    if creature.species == "goat":
        guess = "a cliff goat"
    elif creature.species == "beaver":
        guess = "a river beaver-beast"
    elif creature.species == "crane":
        guess = "a chicken with a ladder for legs"
    else:
        guess = "a round little desert boomer"
    world.say(
        f"{observer.id} whispered that the dent must have been made by {guess}, and the rumor grew taller than the fence."
    )


def investigate(world: World, helper: Entity, obj: Entity, creature: Creature) -> None:
    _add_meter(helper.memes, "calm", 1)
    _add_meter(helper.memes, "misunderstanding", 0.0)
    world.say(
        f"Then {helper.id} came along with a lantern, knelt by the {obj.label}, and looked for clues instead of guesses."
    )
    world.say(
        f"{helper.id} found {creature.clue} and said the dent was too neat for a monster story."
    )


def reveal_truth(world: World, observer: Entity, helper: Entity, creature: Creature, obj: Entity) -> None:
    _add_meter(observer.memes, "relief", 1)
    _add_meter(observer.memes, "understanding", 1)
    _add_meter(obj.meters, "dent_fixed", 1)
    world.say(
        f"At last, {helper.id} pointed to the tracks and laughed: it was really {creature.label}, not a giant beast at all."
    )
    world.say(
        f"The poor {creature.species} had only bumped the {obj.label} while reaching for crumbs, and that had left the dent."
    )
    world.say(
        f"{observer.id} set out a little bowl of feed, and the {creature.species} left happily, while the dent stayed behind as proof that stories can be bigger than the truth."
    )


def tell(setting: Setting, creature: Creature, obj_cfg: ObjectCfg, name: str, hero_type: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=hero_type, traits=["little", trait]))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the helper", traits=["steady"]))
    obj = world.add(Entity(id=obj_cfg.label, type=obj_cfg.label, label=obj_cfg.label, phrase=obj_cfg.phrase))
    world.facts.update(hero=hero, helper=helper, obj=obj, creature=creature, setting=setting, obj_cfg=obj_cfg)

    world.say(
        f"{hero.id} was a {trait} {hero.type} who loved a good tall tale and never walked past a mystery twice."
    )
    world.say(
        f"At {setting.place}, {hero.id} often watched the old {obj.label} because it sat by {obj_cfg.location} and shone like a little silver hill."
    )
    tally_exaggeration(world, hero, creature)

    world.para()
    notice_dent(world, hero, obj, creature)
    guess_species(world, hero, creature)
    world.say(f"The more {hero.id} thought about it, the bigger the story got, until the whole place felt one whisker away from a legend.")

    world.para()
    investigate(world, helper, obj, creature)
    reveal_truth(world, hero, helper, creature, obj)

    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    obj: Entity = f["obj"]
    creature: Creature = f["creature"]
    setting: Setting = f["setting"]

    return [
        QAItem(
            question=f"What did {hero.id} notice at {setting.place}?",
            answer=f"{hero.id} noticed a fresh dent in the {obj.label}, and the sight made the day feel like the start of a tall tale.",
        ),
        QAItem(
            question=f"Why did {hero.id} misunderstand the species near the {obj.label}?",
            answer=f"{hero.id} found strange clues near the {obj.label}, so {hero.pronoun('subject')} guessed a bigger and wilder species than the real one.",
        ),
        QAItem(
            question=f"Who solved the misunderstanding in the end?",
            answer=f"{helper.id} solved it by looking at the clues carefully and showing that the real visitor was {creature.label}, not a monster.",
        ),
        QAItem(
            question=f"What caused the dent?",
            answer=f"The dent was caused when {creature.label} bumped the {obj.label} while reaching for crumbs, which turned out to be a small accident instead of a huge mystery.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a species?",
            answer="A species is a group of living things that are the same kind, like goats, beavers, or cranes.",
        ),
        QAItem(
            question="What is a dent?",
            answer="A dent is a shallow hollow or dip in something hard, like metal or wood, after it gets pushed or bumped.",
        ),
        QAItem(
            question="Why do people make stories taller when they are surprised?",
            answer="People sometimes make stories taller when they are surprised because the mystery feels more exciting than the plain facts.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    creature: Creature = f["creature"]
    obj: Entity = f["obj"]
    return [
        f"Write a tall-tale story for a child who finds a dent in a {obj.label} and mistakes the nearby species for something grander than it is.",
        f"Tell a funny misunderstanding story where {hero.id} thinks {creature.label} made the dent, then learns the truth from a calm helper.",
        f"Write a short story about a dent, a species guess, and a careful discovery that sets the record straight.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for creature in CREATURES:
            for obj in OBJECTS:
                combos.append((place, creature, obj))
    return combos


@dataclass
class ASPChoice:
    place: str
    creature: str
    obj: str


ASP_RULES = r"""
place(P) :- setting(P).
creature(C) :- animal(C).
object(O) :- thing(O).

interesting(P,C,O) :- place(P), creature(C), object(O), dented(O), near(P,C,O), misunderstood(P,C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for cid, c in CREATURES.items():
        lines.append(asp.fact("animal", cid))
        lines.append(asp.fact("species", cid, c.species))
        lines.append(asp.fact("size", cid, c.size))
        lines.append(asp.fact("truth_tag", cid, c.truth_tag))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("thing", oid))
        if o.could_dent:
            lines.append(asp.fact("dented", oid))
    for pid in SETTINGS:
        for cid in CREATURES:
            for oid in OBJECTS:
                lines.append(asp.fact("near", pid, cid, oid))
                lines.append(asp.fact("misunderstood", pid, cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show interesting/3."))
    asp_set = set(asp.atoms(model, "interesting"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: dent, species, and a misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--object", dest="obj", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--type", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--helper", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.creature is None or c[1] == args.creature)
              and (args.obj is None or c[2] == args.obj)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, creature, obj = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    hero_type = args.type or rng.choice(["girl", "boy"])
    helper = args.helper or rng.choice(["woman", "man"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, creature=creature, object=obj, name=name, type=hero_type, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CREATURES[params.creature], OBJECTS[params.object], params.name, params.type, params.helper, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show interesting/3."))
    return sorted(set(asp.atoms(model, "interesting")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show interesting/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [
            generate(StoryParams(place=p, creature=c, object=o, name="Mabel", type="girl", helper="woman", trait="curious"))
            for p, c, o in valid_combos()
        ]
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
