#!/usr/bin/env python3
"""
Fairy-tale storyworld: curiosity, a quest, and a bad ending.

A small, self-contained simulation for a cautionary fairy tale. The world is
built from a curious heroine, a delicate dress, a sweetwilliam garden, and a
quest that goes wrong when she follows her curiosity too far.

The story is state-driven:
- curiosity rises when a locked or mysterious thing appears
- a quest begins when the child decides to seek the hidden thing
- risk, damage, and loss follow from the chosen path
- the ending proves what changed

This world intentionally supports a bad ending feature: the quest may fail, and
the final image shows the cost of curiosity.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "maid"}
        male = {"boy", "prince", "king", "knight"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the rose path"
    landmark: str = "the sweetwilliam hedge"


@dataclass
class Hero:
    name: str
    gender: str
    trait: str


@dataclass
class Prize:
    label: str = "dress"
    phrase: str = "a blue dress with pearl buttons"
    type: str = "dress"
    region: str = "torso"
    plural: bool = False


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    danger: str
    promise: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def _moneyless_risk(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    dress = world.get("dress")
    thorn = world.get("thorn")
    if hero.memes.get("curiosity", 0) < THRESHOLD:
        return out
    if dress.meters.get("torn", 0) >= THRESHOLD:
        return out
    if hero.meters.get("near_thorn", 0) < THRESHOLD:
        return out
    sig = ("torn", dress.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    dress.meters["torn"] = 1
    dress.meters["dirty"] = 1
    thorn.meters["used"] = 1
    out.append("The thorn snagged the dress and left a long jagged tear.")
    return out


def _loss_after_torn(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    dress = world.get("dress")
    if dress.meters.get("torn", 0) < THRESHOLD:
        return out
    sig = ("loss", dress.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["sorrow"] = hero.memes.get("sorrow", 0) + 1
    out.append("After that, the dress could not be made whole again.")
    return out


CAUSAL_RULES = [_moneyless_risk, _loss_after_torn]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    name: str
    gender: str
    trait: str
    place: str
    seed: Optional[int] = None


SETTINGS = {
    "rose path": Setting(place="the rose path", landmark="the sweetwilliam hedge"),
    "moon garden": Setting(place="the moon garden", landmark="the sweetwilliam hedge"),
    "brook lane": Setting(place="the brook lane", landmark="the sweetwilliam hedge"),
}

HERO_NAMES = ["Lina", "Mira", "Eira", "Nora", "Elin", "Tessa"]
TRAITS = ["curious", "gentle", "brave", "dreamy"]

ASP_RULES = r"""
curious(H) :- hero(H), curiosity(H).
near_thorn(H) :- hero(H), chooses_quest(H).
torn(D) :- dress(D), near_thorn(hero), curiosity(hero).
lost(D) :- torn(D).
bad_ending :- lost(dress).
#show curious/1.
#show near_thorn/1.
#show torn/1.
#show lost/1.
#show bad_ending/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "hero"),
        asp.fact("dress", "dress"),
        asp.fact("thorn", "thorn"),
        asp.fact("curiosity", "hero"),
        asp.fact("chooses_quest", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/0."))
    bad = any(a.name == "bad_ending" for a in model)
    if bad:
        print("OK: ASP predicts the bad ending.")
        return 0
    print("MISMATCH: ASP did not predict the bad ending.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy tale of curiosity, a quest, and a bad ending.")
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--place", choices=sorted(SETTINGS))
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    place = args.place or rng.choice(list(SETTINGS))
    if args.gender is None and name in {"Eira", "Lina", "Mira", "Nora", "Elin", "Tessa"}:
        pass
    return StoryParams(name=name, gender=gender, trait=trait, place=place)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name, traits=[params.trait]))
    dress = world.add(Entity(id="dress", kind="thing", type="dress", label="dress", phrase="a blue dress with pearl buttons", owner=hero.id))
    hedge = world.add(Entity(id="hedge", kind="thing", type="hedge", label="sweetwilliam hedge"))
    thorn = world.add(Entity(id="thorn", kind="thing", type="thorn", label="thorn", owner=hedge.id))
    world.facts.update(hero=hero, dress=dress, hedge=hedge, thorn=thorn, setting=world.setting)

    world.say(
        f"Once in {world.setting.place}, there was a little {params.trait} {params.gender} named {params.name}."
    )
    world.say(
        f"{params.name} wore a dress and loved the sweetwilliam hedge, because its pink blossoms looked like tiny crowns."
    )

    world.para()
    hero.memes["curiosity"] = 1
    world.say(
        f"One day, {params.name} noticed a silver glimmer tucked behind {world.setting.landmark}."
    )
    world.say(
        f"Curiosity stirred in {params.name}'s chest, and {params.name} decided on a quest to see what hid there."
    )

    hero.meters["near_thorn"] = 1
    world.say(
        f"{params.name} slipped closer, stepping between the leaves to follow the little glimmer."
    )
    propagate(world)
    if dress.meters.get("torn", 0) >= THRESHOLD:
        world.say(
            f"The pretty dress caught on the thorn, and the bright cloth split before {params.name} could save it."
        )

    world.para()
    world.say(
        f"{params.name} stood very still beside the sweetwilliam hedge, holding the torn dress and the ended quest."
    )
    world.say(
        f"The blossoms were still sweet, but the day had turned into a bad ending, and {params.name} learned to heed careful warnings."
    )
    world.facts["bad_ending"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a fairy tale about {hero.label} and a dress, where curiosity leads to a quest and a bad ending.",
        f"Tell a short fairy story set near the sweetwilliam hedge and the rose path.",
        f"Write a child-facing cautionary tale in which a curious girl or boy follows a glimmer and loses a dress.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    qas = [
        QAItem(
            question=f"Who was the curious child in the story?",
            answer=f"The curious child was {hero.label}, a little {hero.traits[0]} {hero.type}.",
        ),
        QAItem(
            question="What did the child set out to do?",
            answer="The child began a quest to look behind the sweetwilliam hedge and find the silver glimmer.",
        ),
        QAItem(
            question="What happened to the dress?",
            answer="The dress caught on a thorn and tore, so it could not be saved.",
        ),
        QAItem(
            question="Was the ending happy?",
            answer="No. The story ended badly, with the torn dress and the child learning too late to be careful.",
        ),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sweetwilliam?",
            answer="Sweetwilliam is a garden flower with many small blossoms, often pink or red, growing in clusters.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the feeling that makes someone want to know more about something hidden or strange.",
        ),
        QAItem(
            question="What is a quest in a fairy tale?",
            answer="A quest is a journey or search for something important, often with a goal that is hard to reach.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {e.label} {' '.join(parts)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Lina", gender="girl", trait="curious", place="rose path"),
    StoryParams(name="Mira", gender="girl", trait="dreamy", place="moon garden"),
    StoryParams(name="Tessa", gender="girl", trait="brave", place="brook lane"),
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
        print(asp_program("#show bad_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show bad_ending/0."))
        print("bad ending:" , any(a.name == "bad_ending" for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
