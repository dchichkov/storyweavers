#!/usr/bin/env python3
"""
A small folk-tale story world about a shabby hood, a bit of bologna, and a
kind reconciliation.
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
# Core entities and world state
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the village lane"
    affords: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    region: str
    mess: str
    soil: str
    coverable: bool = True


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    pleasant: str
    plural: bool = False


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


# ---------------------------------------------------------------------------
# World vocabulary
# ---------------------------------------------------------------------------
SETTING = Setting(place="the village lane", affords={"trade", "gather", "share"})

ARTIFACTS = {
    "hood": Artifact(
        id="hood",
        label="hood",
        phrase="a deep blue hood",
        region="head",
        mess="soot",
        soil="unseemly and spotted",
    )
}

GIFTS = {
    "bologna": Gift(
        id="bologna",
        label="bologna",
        phrase="a round of bologna",
        pleasant="savory",
        plural=False,
    )
}

CHARACTER_TYPES = ["boy", "girl"]
NAMES = {
    "boy": ["Milo", "Ned", "Pip", "Tobin"],
    "girl": ["Hana", "Lina", "Mira", "Tessa"],
}


# ---------------------------------------------------------------------------
# Reasonable story gate
# ---------------------------------------------------------------------------
def hood_at_risk(artifact: Artifact) -> bool:
    return artifact.coverable and artifact.region == "head"


def select_companion_gift(artifact: Artifact, gift: Gift) -> bool:
    return artifact.id == "hood" and gift.id == "bologna"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in {"village": SETTING}.items():
        for act in setting.affords:
            for art in ARTIFACTS.values():
                for gift in GIFTS.values():
                    if hood_at_risk(art) and select_companion_gift(art, gift):
                        combos.append((place, act, art.id))
    return combos


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, elder: Entity, hood: Entity, bologna: Entity) -> None:
    world.say(
        f"In a village lane where old stories liked to linger, {hero.id} was a "
        f"small {hero.type} with {hero.pronoun('possessive')} {hood.label}. "
        f"{hero.pronoun().capitalize()} loved the smell of {bologna.label} from the bakery cart."
    )
    world.say(
        f"{elder.id} said the hood was useful in wind and rain, though it had grown a bit "
        f"unseemly with age."
    )


def conflict(world: World, hero: Entity, elder: Entity, hood: Entity, bologna: Entity) -> None:
    world.para()
    world.say(
        f"One blustery morning, {hero.id} hurried to the lane market, wanting to share "
        f"{bologna.phrase} with the neighbors."
    )
    world.say(
        f"But a wind came skirling round the corners and tugged at {hero.pronoun('possessive')} "
        f"{hood.label}, making it look more unseemly than before."
    )
    hero.memes["embarrassment"] = hero.memes.get("embarrassment", 0.0) + 1.0
    elder.memes["worry"] = elder.memes.get("worry", 0.0) + 1.0
    world.say(
        f"{hero.id} felt the sting of shame, and {elder.id} saw that a kind word would be needed."
    )


def reconciliation(world: World, hero: Entity, elder: Entity, hood: Entity, bologna: Entity) -> None:
    world.para()
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    elder.memes["kindness"] = elder.memes.get("kindness", 0.0) + 1.0
    world.say(
        f"{elder.id} sat with {hero.id} on the stone step and said, "
        f'"A hood can be mended, and a heart can be mended too."'
    )
    world.say(
        f"Together they trimmed the frayed edge, brushed away the soot, and tied the hood "
        f"so it sat straight again."
    )
    hood.meters["clean"] = hood.meters.get("clean", 0.0) + 1.0
    hood.meters["mended"] = hood.meters.get("mended", 0.0) + 1.0
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1.0
    elder.memes["peace"] = elder.memes.get("peace", 0.0) + 1.0
    world.say(
        f"Then {hero.id} carried the {bologna.label} to the neighbors, and the lane grew warm "
        f"with kindness."
    )


def ending(world: World, hero: Entity, elder: Entity, hood: Entity, bologna: Entity) -> None:
    world.para()
    world.say(
        f"By evening, {hero.id} wore {hero.pronoun('possessive')} hood proudly, no longer "
        f"ashamed of its old patches."
    )
    world.say(
        f"The neighbors shared the {bologna.label}, the wind passed on, and the little village "
        f"remembered that reconciliation can make even an unseemly thing seem dear."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    name: str
    gender: str
    elder: str
    seed: Optional[int] = None


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    elder = world.add(Entity(id=params.elder, kind="character", type="elder"))
    hood = world.add(Entity(id="hood", type="hood", label="hood", phrase="a deep blue hood", owner=hero.id, caretaker=elder.id))
    bologna = world.add(Entity(id="bologna", type="food", label="bologna", phrase="a round of bologna", owner=hero.id))

    world.facts.update(hero=hero, elder=elder, hood=hood, bologna=bologna)

    introduce(world, hero, elder, hood, bologna)
    conflict(world, hero, elder, hood, bologna)
    reconciliation(world, hero, elder, hood, bologna)
    ending(world, hero, elder, hood, bologna)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a folk tale about {hero.id}, a hood that looks unseemly, and a kind reconciliation.",
        f"Tell a short children's story where bologna helps repair hurt feelings in a village lane.",
        f"Write a gentle story about an old hood, a shared meal, and the way kindness mends embarrassment.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, hood, bologna = f["hero"], f["elder"], f["hood"], f["bologna"]
    return [
        QAItem(
            question=f"What was {hero.id} wearing in the village lane?",
            answer=f"{hero.id} was wearing {hero.pronoun('possessive')} {hood.label}, a deep blue hood that had grown a little unseemly.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel ashamed when the wind came?",
            answer=f"The wind tugged at {hero.pronoun('possessive')} {hood.label} and made it look more unseemly, so {hero.id} felt embarrassed.",
        ),
        QAItem(
            question=f"How did {elder.id} help make things right?",
            answer=f"{elder.id} spoke kindly, sat with {hero.id}, and helped mend and straighten the hood so {hero.id} could feel proud again.",
        ),
        QAItem(
            question=f"What did they share at the end of the story?",
            answer=f"They shared the {bologna.label}, and that sharing helped bring reconciliation and peace to the lane.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bologna?",
            answer="Bologna is a kind of sliced meat that people often eat in sandwiches or share as a simple meal.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after people feel upset, hurt, or embarrassed.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle, helpful, and caring toward someone else.",
        ),
        QAItem(
            question="What is a hood for?",
            answer="A hood is a piece of clothing that covers the head and helps keep it warm or dry.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- character(H).
hood_item(I) :- artifact(I), type(I,hood).
gift(G) :- gift_item(G).

at_risk(I) :- hood_item(I).
can_reconcile(H,I,G) :- hero(H), at_risk(I), gift(G), companion_gift(I,G).

valid_story(H,I,G) :- can_reconcile(H,I,G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name, setting in {"village": SETTING}.items():
        lines.append(asp.fact("setting", name))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", name, a))
    for aid, art in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        lines.append(asp.fact("type", aid, "hood"))
        lines.append(asp.fact("region", aid, art.region))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift_item", gid))
        lines.append(asp.fact("companion_gift", "hood", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale story world: hood, bologna, reconciliation.")
    ap.add_argument("--name", choices=sum(NAMES.values(), []))
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--elder", choices=["Old Mara", "Old Jonas", "Old Pella"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(CHARACTER_TYPES)
    if args.name:
        name = args.name
    else:
        name = rng.choice(NAMES[gender])
    elder = args.elder or rng.choice(["Old Mara", "Old Jonas", "Old Pella"])
    return StoryParams(name=name, gender=gender, elder=elder)


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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
    StoryParams(name="Milo", gender="boy", elder="Old Mara"),
    StoryParams(name="Hana", gender="girl", elder="Old Jonas"),
    StoryParams(name="Tobin", gender="boy", elder="Old Pella"),
]


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
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
