#!/usr/bin/env python3
"""
storyworlds/worlds/moose_kale_sharing_flashback_magic_adventure.py
===================================================================

A small standalone story world about a moose, kale, sharing, a flashback, and a
bit of magic in an adventure style.

Premise:
- A moose and a child adventurer find a crisp bundle of kale on a forest trail.
- The moose wants to keep it all.
- A flashback reminds them that sharing once led to a better outcome.
- A little magic makes the shared pile grow, so both can enjoy the meal.

The world model tracks:
- physical meters: hunger, kale_pile, sparkle, path, basket, fullness
- emotional memes: joy, greed, trust, memory, wonder, relief

The story is generated from state changes, not from a frozen paragraph template.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["hunger", "sparkle", "kale_pile", "path", "fullness"]:
            self.meters.setdefault(key, 0.0)
        for key in ["joy", "greed", "trust", "memory", "wonder", "relief"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man", "moose"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Magic:
    id: str
    label: str
    phrase: str
    trigger: str
    effect: str
    requires_sharing: bool = True


@dataclass
class StoryParams:
    place: str
    magic: str
    name: str
    gender: str
    moose_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.history: list[str] = []
        self.debug_trace: list[str] = []

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
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "forest": Setting("the forest", outdoors=True, affords={"trail", "glade", "moonlight"}),
    "riverbank": Setting("the riverbank", outdoors=True, affords={"trail", "glade", "moonlight"}),
    "hill": Setting("the windy hill", outdoors=True, affords={"trail", "moonlight"}),
}

MAGIC = {
    "moonbowl": Magic(
        id="moonbowl",
        label="moon bowl",
        phrase="a silver bowl that glimmered like a tiny moon",
        trigger="shared the kale",
        effect="the kale grew into two bright piles",
    ),
    "seedlamp": Magic(
        id="seedlamp",
        label="seed lamp",
        phrase="a lantern made from a glowing seed pod",
        trigger="took turns with the kale",
        effect="the lantern showed a hidden patch of fresh kale",
    ),
}

VALID_PLACES = set(SETTINGS)
VALID_MAGIC = set(MAGIC)

GIRL_NAMES = ["Mina", "Luna", "Pip", "Nia", "Tara", "Ivy"]
BOY_NAMES = ["Finn", "Jasper", "Oren", "Bram", "Eli", "Theo"]


def is_reasonable(place: str, magic_id: str) -> bool:
    return place in SETTINGS and magic_id in MAGIC


ASP_RULES = r"""
place(P) :- setting(P).
magic(M) :- magic_item(M).

shared_ok(P,M) :- place(P), magic(M).
valid_story(P,M) :- shared_ok(P,M).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
        for a in sorted(SETTINGS[p].affords):
            lines.append(asp.fact("affords", p, a))
    for m in MAGIC:
        lines.append(asp.fact("magic_item", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str]]:
    return [(p, m) for p in SETTINGS for m in MAGIC if is_reasonable(p, m)]


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A moose, kale, sharing, flashback, and magic adventure.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--magic", choices=sorted(MAGIC))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--moose-name")
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
    if args.place and args.magic and not is_reasonable(args.place, args.magic):
        raise StoryError("That place and magic do not make a sensible adventure together.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.magic is None or c[1] == args.magic)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, magic = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    moose_name = args.moose_name or rng.choice(["Moss", "Mabel", "Milo", "Mira", "Brindle"])
    return StoryParams(place=place, magic=magic, name=name, gender=gender, moose_name=moose_name)


def _flashback_line(hero: Entity, moose: Entity, kale: Entity) -> str:
    return (
        f"Then {hero.id} remembered a flashback: last spring, when {moose.id} had shared a "
        f"smaller bunch of {kale.label}, they had both ended up smiling under the trees."
    )


def simulate(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    magic = MAGIC[params.magic]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    moose = world.add(Entity(id=params.moose_name, kind="character", type="moose", label=params.moose_name))
    kale = world.add(Entity(
        id="kale",
        kind="thing",
        type="kale",
        label="kale",
        phrase="a pile of crisp green kale",
        plural=False,
    ))
    basket = world.add(Entity(id="basket", kind="thing", type="basket", label=magic.label, phrase=magic.phrase))

    hero.memes["wonder"] += 1
    moose.memes["greed"] += 1
    moose.meters["hunger"] += 1
    kale.meters["kale_pile"] = 1
    basket.meters["sparkle"] = 1

    world.say(f"One bright day, {hero.id} and {moose.id} followed a twisty trail into {setting.place}.")
    world.say(f"Near a mossy log, they found {kale.phrase}, and {moose.id}'s nose twitched with delight.")
    world.say(f"{moose.id} wanted to keep the kale all to {moose.pronoun('object')}, because {moose.pronoun('subject')} was very hungry.")
    world.para()

    if world.setting.outdoors:
        hero.memes["trust"] += 1
        world.say(f"{hero.id} took one small step closer and said, \"Let's share it so nobody goes hungry.\"")
        world.say(_flashback_line(hero, moose, kale))
        hero.memes["memory"] += 1
        moose.memes["memory"] += 1
        moose.memes["greed"] -= 0.5
        moose.memes["trust"] += 1
        world.say(f"The memory made {moose.id} pause, and the shiny {basket.label} gave a soft glow.")
        world.say(f"When they {magic.trigger}, {magic.effect}.")
        kale.meters["kale_pile"] = 2
        hero.memes["joy"] += 1
        moose.memes["joy"] += 1
        moose.meters["fullness"] += 1
        world.para()
        world.say(f"{hero.id} tucked one pile into the {basket.label}, and {moose.id} munched the other pile happily.")
        world.say(f"At the end of the adventure, the trail was quiet again, and the two friends walked on with full bellies and bright smiles.")
        hero.memes["relief"] += 1
        moose.memes["relief"] += 1

    world.facts = {
        "hero": hero,
        "moose": moose,
        "kale": kale,
        "basket": basket,
        "magic": magic,
        "setting": setting,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short adventure story for a young child about {f['hero'].id}, {f['moose'].id}, and shared kale in {f['setting'].place}.",
        f"Tell a gentle story where a moose named {f['moose'].id} learns to share kale with {f['hero'].id} after a flashback.",
        f"Write a magical outdoor tale that includes a {f['magic'].label} and ends with the kale being shared.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    moose: Entity = f["moose"]
    kale: Entity = f["kale"]
    basket: Entity = f["basket"]
    magic: Magic = f["magic"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who found the kale in {setting.place}?",
            answer=f"{hero.id} and {moose.id} found the kale together while exploring the trail in {setting.place}.",
        ),
        QAItem(
            question=f"Why did {moose.id} want to keep the kale at first?",
            answer=f"{moose.id} was hungry and wanted the whole pile of {kale.label} to {moose.pronoun('object')}self.",
        ),
        QAItem(
            question=f"What did {hero.id} remember before they shared?",
            answer=f"{hero.id} remembered a flashback about a smaller time when {moose.id} had shared kale and both of them were happy.",
        ),
        QAItem(
            question=f"How did the magic help in the story?",
            answer=f"When they {magic.trigger}, the {basket.label} glowed and {magic.effect}, so there was enough kale for both of them.",
        ),
        QAItem(
            question=f"What changed by the end of the adventure?",
            answer=f"By the end, {moose.id} was no longer trying to keep all the kale, and the friends walked on together with full bellies and smiling faces.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kale?",
            answer="Kale is a leafy green vegetable. People and animals can eat it when it is washed and fresh.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means giving some of what you have to someone else so both people can enjoy it.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that remembers something that happened earlier.",
        ),
        QAItem(
            question="What does magic mean in a tale?",
            answer="Magic means something special happens that cannot happen in normal life, like a glowing bowl making more food.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="forest", magic="moonbowl", name="Mina", gender="girl", moose_name="Moss"),
    StoryParams(place="riverbank", magic="seedlamp", name="Finn", gender="boy", moose_name="Milo"),
    StoryParams(place="hill", magic="moonbowl", name="Nia", gender="girl", moose_name="Brindle"),
]


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible story combos:\n")
        for place, magic in combos:
            print(f"  {place:10} {magic}")
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
