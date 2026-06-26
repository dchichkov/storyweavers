#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/murder_belabor_kindness_misunderstanding_tall_tale.py
=====================================================================================================

A tiny tall-tale storyworld about a child, a murder of crows, a noisy
misunderstanding, and a kindness that settles the sky back down again.

The seed tale imagined for this world:
---
In a wind-brushed field beside a bright red barn, a child named June watched a
murder of crows gather on a fence rail. The crows mistook June's ribbon kite
for a giant hawk, and they belabored the danger with a storm of caws so loud
the horses blinked.

June's grandmother, who could belabor any warning into a sermon and then laugh
at herself, said the crows were not cruel, only frightened. So June put the
kite down, shared a shiny crust of berry pie, and bowed like a tiny mayor.
The crows learned the kite was only cloth and string, and their fear flew off
with the sunset. By supper time, the whole field was one calm, cackling
kindness.
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
        if self.type in {"girl", "woman", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    sky: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        return w


SETTINGS = {
    "barnyard": Setting(place="the barnyard", sky="windy", affords={"kite"}),
    "meadow": Setting(place="the meadow", sky="bright", affords={"kite"}),
    "orchard": Setting(place="the orchard", sky="golden", affords={"kite"}),
}

NAMES = ["June", "Milo", "Hazel", "Pip", "Nora", "Otis"]
HELPERS = ["grandmother", "grandfather"]
GENDERS = ["girl", "boy"]


@dataclass
class CrowPack:
    label: str
    phrase: str
    count: int
    fear: str
    chatter: str


@dataclass
class Kite:
    label: str
    phrase: str
    fear_caused: str


PACKS = {
    "small": CrowPack("murder of crows", "a murder of crows", 7, "hawk-sure fear", "a fuss"),
    "grand": CrowPack("murder of crows", "a murder of crows", 12, "thunder-sure fear", "a racket"),
}

KITES = {
    "ribbon": Kite("kite", "a ribbon kite with a tail like a scarf", "hawk-sure fear"),
    "paper": Kite("kite", "a paper kite with painted stars", "thunder-sure fear"),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: kindness, misunderstanding, and a crow-fuss.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--helper", choices=HELPERS)
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
    place = args.place or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(GENDERS)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, name=name, gender=gender, helper=helper)


def choose_pack(setting: Setting) -> CrowPack:
    return PACKS["grand"] if setting.place == "the orchard" else PACKS["small"]


def choose_kite(setting: Setting) -> Kite:
    return KITES["ribbon"] if setting.place != "the orchard" else KITES["paper"]


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    crows = choose_pack(setting)
    kite = choose_kite(setting)

    world.say(
        f"{child.id} lived near {setting.place}, where the wind could comb the grass flat as a pancake."
    )
    world.say(
        f"One day, {child.id} brought out {kite.phrase}, and a {crows.label} landed on the fence rail to watch."
    )
    world.say(
        f"The crows mistook the kite for a giant hawk, and they belabored their alarm with {crows.chatter} "
        f"until the barn cat forgot how to blink."
    )

    world.para()
    world.say(
        f"{child.id}'s {helper.label} saw the fuss and said, "
        f'"Those birds are not mean. They are only wearing a misunderstanding like a tight hat."'
    )
    child.memes["curiosity"] = 1
    child.memes["kindness"] = 1
    child.memes["understanding"] = 0
    child.meters["kite"] = 1
    world.facts["pack"] = crows
    world.facts["kite"] = kite
    world.facts["child"] = child
    world.facts["helper"] = helper

    world.para()
    child.memes["kindness"] += 1
    child.memes["understanding"] += 1
    world.say(
        f"So {child.id} set the kite down, broke off a shiny bite of berry pie, and held it out with an open palm."
    )
    world.say(
        f"The crows tilted their heads, noticed the cloth and string, and realized the sky was not attacking them after all."
    )
    world.say(
        f"Then the whole murder of crows came down to peck politely, and {child.id} bowed so low the grass kissed {child.pronoun('possessive')} shoes."
    )
    world.say(
        f"By supper time, the field was calm, the kite was safe, and the crows were only a black ribbon turning lazy circles over the barn."
    )

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    kite = f["kite"]
    pack = f["pack"]
    return [
        'Write a short tall tale for a child about kindness, misunderstanding, and a noisy flock.',
        f"Tell a child-friendly tall tale where {child.id} has {kite.phrase} and a {pack.label} mistakes it for danger.",
        'Write a simple story that includes the words "murder" and "belabor" and ends with a kind fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    kite = f["kite"]
    pack = f["pack"]
    return [
        QAItem(
            question=f"What did {child.id} bring out in the field?",
            answer=f"{child.id} brought out {kite.phrase}, which fluttered in the wind like a bright little banner."
        ),
        QAItem(
            question=f"Why did the {pack.label} belabor the alarm?",
            answer=f"The crows belabored the alarm because they mistook the kite for a giant hawk and thought the sky had turned dangerous."
        ),
        QAItem(
            question=f"How did {child.id} and the {helper.label} solve the misunderstanding?",
            answer=f"They solved it with kindness: {child.id} set the kite down, offered berry pie, and let the crows see that it was only cloth and string."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the fear was gone, the crows were calm, and the field felt gentle instead of noisy."
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a murder of crows?",
        answer="A murder of crows is a group of crows. It is a surprising old phrase for a flock of them."
    ),
    QAItem(
        question="What does it mean to belabor a point?",
        answer="To belabor a point means to keep talking about it again and again, more than is needed."
    ),
    QAItem(
        question="What is a misunderstanding?",
        answer="A misunderstanding happens when someone thinks the wrong thing because they do not have the right information."
    ),
    QAItem(
        question="What is kindness?",
        answer="Kindness means choosing gentle actions that help someone feel safe, seen, or cared for."
    ),
]


ASP_RULES = r"""
child_kind(C) :- child(C).
crow_pack(P) :- pack(P).
misunderstanding(C, P) :- child(C), pack(P), fears(P, hawk_like).
resolved(C, P) :- misunderstanding(C, P), kindness(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("place_name", pid, s.place))
    for kid in KITES:
        lines.append(asp.fact("kite", kid))
    for pid in PACKS:
        lines.append(asp.fact("pack", pid))
    lines.append(asp.fact("fears", "small", "hawk_like"))
    lines.append(asp.fact("fears", "grand", "thunder_like"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show misunderstanding/2. #show resolved/2."))
    atoms = set(asp.atoms(model, "resolved")) | set(asp.atoms(model, "misunderstanding"))
    if atoms:
        print("OK: ASP twin is present.")
        return 0
    print("MISMATCH: ASP twin produced no useful atoms.")
    return 1


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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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


def valid_combos() -> list[tuple[str, str]]:
    return [(p, "kite") for p in SETTINGS]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=WORLD_KNOWLEDGE,
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


def resolve_args_all(args: argparse.Namespace, rng: random.Random) -> list[StoryParams]:
    if args.all:
        return [StoryParams(place=p, name="June", gender="girl", helper="grandmother") for p in SETTINGS]
    return [resolve_params(args, random.Random((args.seed or 0) + i)) for i in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show misunderstanding/2. #show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show misunderstanding/2. #show resolved/2."))
        print(model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(place=p, name="June", gender="girl", helper="grandmother")) for p in SETTINGS]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
