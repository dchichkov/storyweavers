#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/investigative_curiosity_nursery_rhyme.py
===============================================================================================================

A small storyworld with an investigative, curious, nursery-rhyme feel.

Seed tale:
- In a quiet nursery, a curious little child notices a missing bell.
- The child follows tiny clues under the rug, beside the chair, and near the toy box.
- The parent worries about wandering in the dim room, then offers a lantern and help.
- Together they find the bell tucked in a slipper, and the room ends bright and calm.

The world model tracks:
- physical meters: search, clue, and brightness
- emotional memes: curiosity, worry, relief, joy

The prose aims for a simple, rhythmic, child-facing tone while still being driven
by simulated world state rather than a fixed paragraph with swapped nouns.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    hidden_in: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("search", "clue", "brightness"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "worry", "relief", "joy"):
            self.memes.setdefault(k, 0.0)

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


@dataclass
class Setting:
    place: str = "the nursery"
    dim: bool = True
    affords: set[str] = field(default_factory=lambda: {"investigate"})


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    hidden_in: str
    trail: list[str]
    ending_spot: str


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.path: list[str] = []

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


SETTINGS = {
    "nursery": Setting(place="the nursery", dim=True, affords={"investigate"}),
}

CLUES = {
    "bell": Clue(
        id="bell",
        label="little bell",
        phrase="a bright little bell",
        hidden_in="slipper",
        trail=["under the rug", "beside the chair", "by the toy box"],
        ending_spot="inside a slipper",
    ),
    "ribbon": Clue(
        id="ribbon",
        label="blue ribbon",
        phrase="a soft blue ribbon",
        hidden_in="basket",
        trail=["under the cot", "near the blocks", "under the blanket"],
        ending_spot="in the doll basket",
    ),
    "spoon": Clue(
        id="spoon",
        label="silver spoon",
        phrase="a shiny silver spoon",
        hidden_in="sock",
        trail=["under the pillow", "by the rocking chair", "next to the book"],
        ending_spot="inside a sock",
    ),
}

GEAR = {
    "lantern": Gear(
        id="lantern",
        label="a little lantern",
        prep="lift up a little lantern",
        tail="held the lantern high",
    )
}

GIRL_NAMES = ["Pip", "Mia", "Luna", "Tia", "Nina"]
BOY_NAMES = ["Tom", "Max", "Finn", "Noah", "Ollie"]
TRAITS = ["curious", "bright-eyed", "gentle", "tiny", "cheery"]


@dataclass
class StoryParams:
    place: str
    clue: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


ASP_RULES = r"""
setting(nursery).
affords(nursery,investigate).

clue(bell). clue(ribbon). clue(spoon).

valid_story(Place, Clue, Gender) :- setting(Place), affords(Place, investigate), clue(Clue), gender_ok(Clue, Gender).

gender_ok(bell, girl). gender_ok(bell, boy).
gender_ok(ribbon, girl). gender_ok(ribbon, boy).
gender_ok(spoon, girl). gender_ok(spoon, boy).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "investigate" in setting.affords:
            for clue in CLUES:
                combos.append((place, clue))
    return combos


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {(p, c) for p, c in valid_combos()}
    cl = {(p, c) for (p, c, g) in asp_valid_stories()}
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
    ap = argparse.ArgumentParser(description="Investigative curiosity in a nursery-rhyme style.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.clue and args.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if args.place and args.clue:
        if (args.place, args.clue) not in valid_combos():
            raise StoryError("No valid combination matches the given options.")

    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if not combos:
        raise StoryError("No valid combination matches the given options.")

    place, clue = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, clue=clue, name=name, gender=gender, parent=parent, trait=trait)


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    clue = world.add(Entity(
        id=params.clue,
        type="thing",
        label=CLUES[params.clue].label,
        phrase=CLUES[params.clue].phrase,
        hidden_in=CLUES[params.clue].hidden_in,
    ))
    lantern = world.add(Entity(
        id="lantern",
        type="thing",
        label="little lantern",
        protective=True,
        covers={"dark"},
    ))

    # Act 1
    world.say(f"In {world.setting.place}, soft and light, {hero.id} was {params.trait} and bright.")
    world.say(f"{hero.id} loved to look and loved to see; {hero.pronoun('subject').capitalize()} had great { 'curiosity' } in {hero.pronoun('possessive')} little knee.")
    world.say(f"Then one small thing went out of sight: {clue.phrase} was missing from the night.")

    # Act 2
    world.para()
    hero.memes["curiosity"] += 1
    world.say(f"{hero.id} tiptoed near the rug so thin, and looked for where the clue tucked in.")
    world.path = CLUES[params.clue].trail[:]
    for step in world.path:
        hero.meters["search"] += 1
        hero.meters["clue"] += 1
        world.say(f"{hero.id} found a sign {step}, but not the prize to bring back home.")
    parent.memes["worry"] += 1
    world.say(f'"Stay gentle now," {parent.pronoun("subject")} said, "for sleepy heads are close to rest."')
    world.say(f"So {hero.id} held still and dim; the room felt hushy, soft, and trim.")
    world.say(f"Then {parent.pronoun('subject')} {GEAR['lantern'].prep}, and the glow grew gold and warm.')
    ')
    world.say(f"{hero.id} and {parent.pronoun('subject')} looked once more, from floor to chair and bedspread shore.")

    # Act 3
    world.para()
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    clue.meters["search"] = 1
    lantern.meters["brightness"] = 1
    world.say(f"At last they peeked where slippers stay, and found {clue.phrase} tucked away.")
    world.say(f"It sat {clue.ending_spot}, snug and neat; no more lost note, no more lost beat.")
    world.say(f"{hero.id} laughed a little, soft and sweet. {parent.pronoun('subject').capitalize()} smiled back in the nursery seat.")
    world.say(f"{hero.id} was curious still, but calm at last; the little hunt was done so fast.")
    world.say(f"And so the room went quiet and bright, with {clue.label} found and all feels right.")

    world.facts.update(hero=hero, parent=parent, clue=clue, lantern=lantern, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, clue, parent = f["hero"], f["clue"], f["parent"]
    return [
        f'Write a short nursery-rhyme style story about a curious child named {hero.id} who investigates a missing {clue.label}.',
        f"Tell a gentle story where {hero.id} and {parent.label} search the nursery together until they find the {clue.label}.",
        f'Create a child-friendly investigative tale with soft rhythm, a lantern, and a happy ending in {world.setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, clue, parent = f["hero"], f["clue"], f["parent"]
    return [
        QAItem(
            question=f"What was {hero.id} looking for in {world.setting.place}?",
            answer=f"{hero.id} was looking for {clue.phrase}. It was missing at first, so the little search began.",
        ),
        QAItem(
            question=f"Why did {parent.label} speak up while {hero.id} was investigating?",
            answer=f"{parent.pronoun('subject').capitalize()} wanted {hero.id} to stay gentle and safe in the dim nursery while searching.",
        ),
        QAItem(
            question=f"Where was the missing {clue.label} found?",
            answer=f"It was found {clue.ending_spot}, after the lantern made the nursery bright enough to see clearly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn about what is going on.",
        ),
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives off light, so it helps people see better in a dark place.",
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="nursery", clue="bell", name="Pip", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="nursery", clue="ribbon", name="Tom", gender="boy", parent="father", trait="bright-eyed"),
    StoryParams(place="nursery", clue="spoon", name="Luna", gender="girl", parent="mother", trait="gentle"),
]


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for place, clue, gender in stories:
            print(f"  {place:8} {clue:8} {gender}")
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
            header = f"### {p.name}: {p.clue} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
