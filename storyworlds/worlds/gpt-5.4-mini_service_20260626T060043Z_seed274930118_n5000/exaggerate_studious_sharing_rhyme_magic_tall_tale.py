#!/usr/bin/env python3
"""
storyworlds/worlds/exaggerate_studious_sharing_rhyme_magic_tall_tale.py
======================================================================

A small tall-tale story world about a studious child, a magical rhyme, and
the surprising power of sharing.

Premise:
- A very studious child treasures a magic rhyme object.
- Someone else wants to borrow it.
- The child worries the magic will be used up.

Turn:
- The child sees that the magic grows brighter when it is shared.

Resolution:
- They share it in a little rhyme circle, and the magic becomes bigger than
  before.

This world keeps the prose child-facing and state-driven, with exaggerated
tall-tale flavor.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    kind: str
    spark: str
    shares: bool
    rhythm: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    artifact: str
    name: str
    gender: str
    companion: str
    keeper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.magic_glow = 0.0

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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.magic_glow = self.magic_glow
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "library": Setting(place="the little library", indoors=True, affords={"reading", "sharing", "rhyme"}),
    "school": Setting(place="the schoolroom", indoors=True, affords={"reading", "sharing", "rhyme"}),
    "attic": Setting(place="the dusty attic", indoors=True, affords={"sharing", "rhyme"}),
    "garden": Setting(place="the garden bench", indoors=False, affords={"sharing", "rhyme"}),
}

ARTIFACTS = {
    "rhymebook": Artifact(
        id="rhymebook",
        label="rhyme book",
        phrase="a sturdy little rhyme book",
        kind="book",
        spark="the pages jangled with bright rhymes",
        shares=True,
        rhythm="reading aloud",
    ),
    "magic_chalk": Artifact(
        id="magic_chalk",
        label="magic chalk",
        phrase="a blue piece of magic chalk",
        kind="chalk",
        spark="it left glittering words in the air",
        shares=True,
        rhythm="chalking and chanting",
    ),
    "singing_card": Artifact(
        id="singing_card",
        label="singing card",
        phrase="a singing card with golden corners",
        kind="card",
        spark="it hummed like a tiny hive of bees",
        shares=True,
        rhythm="passing it hand to hand",
    ),
}

NAMES = {
    "girl": ["Nora", "Mia", "Lila", "Zoe", "Ava"],
    "boy": ["Theo", "Ben", "Finn", "Leo", "Max"],
}
TRAITS = ["studious", "careful", "bright-eyed", "earnest", "patient"]
COMPANIONS = ["little friend", "classmate", "neighbor", "cousin"]
KEEPERS = ["teacher", "mother", "father", "librarian"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for art_id, art in ARTIFACTS.items():
            if "sharing" in setting.affords and art.shares:
                combos.append((place, art_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.artifact and args.place:
        if (args.place, args.artifact) not in valid_combos():
            raise StoryError("(No reasonable story: that place cannot support sharing this magic item.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.artifact is None or c[1] == args.artifact)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, artifact = rng.choice(sorted(combos))
    art = ARTIFACTS[artifact]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    companion = args.companion or rng.choice(COMPANIONS)
    keeper = args.keeper or rng.choice(KEEPERS)
    trait = args.trait or "studious"
    return StoryParams(place=place, artifact=artifact, name=name, gender=gender, companion=companion, keeper=keeper, trait=trait)


def tell(setting: Setting, art: Artifact, hero_name: str, gender: str, companion: str, keeper: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, meters={"attention": 2.0}, memes={"study": 2.0, "care": 1.0}))
    pal = world.add(Entity(id="Companion", kind="character", type="child", label=companion, memes={"hope": 1.0}))
    adult = world.add(Entity(id="Keeper", kind="character", type=keeper, label=keeper, memes={"patience": 1.0}))
    item = world.add(Entity(id="Artifact", type=art.kind, label=art.label, phrase=art.phrase, owner=hero.id, caretaker=adult.id))

    hero.meters["treasure"] = 1.0
    item.worn_by = hero.id

    world.say(f"{hero.id} was a {trait} child who could read faster than a rabbit can wink, and {hero.pronoun('possessive')} nose was always in a book.")
    world.say(f"One day {hero.id} found {hero.pronoun('possessive')} {item.label} in {setting.place}. {art.spark.capitalize()}, and that made {hero.id} grin from ear to ear.")
    world.say(f"{hero.id} loved {art.rhythm}, and {hero.pronoun('possessive')} {keeper} said the little treasure was wonderful for learning by heart.")

    world.para()
    world.say(f"Then {companion} asked, \"May I share it too?\"")
    hero.memes["protective"] = 1.0
    hero.memes["worry"] = 1.0
    world.say(f"{hero.id} held the {item.label} close. {hero.pronoun().capitalize()} worried that if it was shared, the magic might get smaller instead of bigger.")
    world.magic_glow = 1.0

    world.para()
    world.say(f"{keeper.capitalize()} smiled a big, slow smile. \"A rhyme is a lantern,\" {hero.pronoun('possessive')} {keeper} said. \"It shines brighter when more voices carry it.\"")
    hero.memes["wonder"] = 1.0
    world.say(f"{hero.id} listened like a mouse listening for crumbs, then opened the {item.label} and let {companion} peek at the first line.")
    world.magic_glow += 1.0
    world.say(f"The words twinkled, and the room felt taller than a barn and brighter than a noon-day pond.")

    world.para()
    hero.memes["sharing"] = 1.0
    hero.memes["joy"] = 2.0
    hero.memes["worry"] = 0.0
    world.say(f"So {hero.id} and {companion} shared the {item.label} aloud, one line at a time, while {keeper} tapped a steady beat on the table.")
    world.say(f"The rhyme hopped from mouth to mouth, and the little magic did not disappear at all; it grew.")
    world.say(f"By the end, {hero.id} was beaming, {companion} was laughing, and the {item.label} seemed as grand as a moonlit quilt full of stars.")

    world.facts.update(hero=hero, pal=pal, keeper=adult, item=item, art=art, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, art = f["hero"], f["art"]
    return [
        f'Write a short tall tale for a child named {hero.id} about {art.label}, sharing, and a magic rhyme.',
        f"Tell a studious story where {hero.id} learns that {art.label} gets better when it is shared.",
        f'Create a gentle tall tale in which a child and a companion use "{art.rhythm}" to make magic grow.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, pal, keeper, art = f["hero"], f["pal"], f["keeper"], f["art"]
    return [
        QAItem(
            question=f"What kind of child was {hero.id}?",
            answer=f"{hero.id} was a {hero.memes and 'studious'} child who loved learning and paying close attention.",
        ),
        QAItem(
            question=f"What did {hero.id} find in {world.setting.place}?",
            answer=f"{hero.id} found {hero.pronoun('possessive')} {art.label}, and it sparkled with magic.",
        ),
        QAItem(
            question=f"What did {pal.label} ask to do?",
            answer=f"{pal.label} asked to share the {art.label} too.",
        ),
        QAItem(
            question=f"Why did {hero.id} worry at first?",
            answer=f"{hero.id} worried that sharing the {art.label} might make the magic smaller, because {hero.id} was still holding it close.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} shared the {art.label} with {pal.label}, and the magic grew bigger instead of smaller.",
        ),
    ]


WORLD_QA = {
    "sharing": [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use, enjoy, or have a turn with something too.",
        )
    ],
    "rhyme": [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a word or line that sounds like another word or line at the end.",
        )
    ],
    "magic": [
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a make-believe thing in a story that can do surprising and impossible-feeling things.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_QA["sharing"] + WORLD_QA["rhyme"] + WORLD_QA["magic"]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


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
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    lines.append(f"  magic_glow={world.magic_glow}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(P) :- place(P).
affords(P, sharing) :- place(P), share_place(P).
artifact(A) :- art(A).
shareable(A) :- artifact(A), shares(A).
valid(P, A) :- affords(P, sharing), shareable(A).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p, s in SETTINGS.items():
        lines.append(asp.fact("place", p))
        if "sharing" in s.affords:
            lines.append(asp.fact("share_place", p))
    for a, art in ARTIFACTS.items():
        lines.append(asp.fact("art", a))
        if art.shares:
            lines.append(asp.fact("shares", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


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
    ap = argparse.ArgumentParser(description="A tall-tale story world about studious sharing and magic rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion")
    ap.add_argument("--keeper")
    ap.add_argument("--trait")
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


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ARTIFACTS[params.artifact], params.name, params.gender, params.companion, params.keeper, params.trait)
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
    StoryParams(place="library", artifact="rhymebook", name="Nora", gender="girl", companion="classmate", keeper="librarian", trait="studious"),
    StoryParams(place="school", artifact="magic_chalk", name="Theo", gender="boy", companion="neighbor", keeper="teacher", trait="studious"),
    StoryParams(place="garden", artifact="singing_card", name="Mia", gender="girl", companion="cousin", keeper="mother", trait="studious"),
]


def resolve(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.artifact and (args.place, args.artifact) not in valid_combos():
        raise StoryError("(No reasonable story: that artifact is not a good sharing-magic fit for that place.)")
    combos = [c for c in valid_combos() if (args.place is None or c[0] == args.place) and (args.artifact is None or c[1] == args.artifact)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, artifact = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    return StoryParams(
        place=place,
        artifact=artifact,
        name=args.name or rng.choice(NAMES[gender]),
        gender=gender,
        companion=args.companion or rng.choice(COMPANIONS),
        keeper=args.keeper or rng.choice(KEEPERS),
        trait=args.trait or "studious",
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, a in combos:
            print(f"  {p:10} {a}")
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
            params = resolve(args, random.Random(seed))
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
            header = f"### {p.name}: {p.artifact} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
