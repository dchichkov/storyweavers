#!/usr/bin/env python3
"""
storyworlds/worlds/sibling_popsicle_scotch_inner_monologue_dialogue_transformation.py
=====================================================================================

A small Tall Tale storyworld about a sibling, a popsicle, and a roll of scotch tape.

Source-tale seed:
---
Two siblings were out on a hot day with a bright popsicle. One sibling wanted to race ahead,
but the other knew the sun would make the treat drip all over their shirts. After a little
inner arguing and some quick talk, they used scotch tape and a paper sleeve to turn the
messy popsicle into a neat, parade-worthy treat. The worry transformed into pride, and the
siblings marched home like heroes.

World idea:
---
- Physical state tracks heat, drip, sticky hands, and the popsicle's shape.
- Emotional state tracks worry, pride, and togetherness between siblings.
- Inner monologue narrates the hero's private thoughts.
- Dialogue shows the siblings talking through the problem.
- Transformation is the visible change from a plain dripping popsicle to a
  wrapped "popsicle scepter" that can be carried without chaos.

The story remains small and classical: setup, worry, turn, and a transformed ending image.
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
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "sister", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "brother", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    hot: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str]
    guards: set[str]
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    prize: str
    hero_name: str
    hero_type: str
    sibling_name: str
    sibling_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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


PRIZES = {
    "popsicle": Prize(
        label="popsicle",
        phrase="a bright striped popsicle",
        region="hand",
        plural=False,
    )
}

SETTINGS = {
    "porch": Setting(place="the porch", hot=True, affords={"carry"}),
    "yard": Setting(place="the yard", hot=True, affords={"carry"}),
    "market": Setting(place="the market walk", hot=True, affords={"carry"}),
}

GEAR = [
    Gear(
        id="scotch_tape_sleeve",
        label="a scotch-tape sleeve",
        prep="tear a strip of scotch tape and wrap a paper sleeve around the popsicle",
        tail="taped the sleeve tight and held the popsicle like a little banner",
        covers={"hand"},
        guards={"drip", "sticky"},
    ),
]

TRAITS = ["bold", "curious", "cheerful", "stubborn", "quick-witted"]
NAMES = ["Mina", "Owen", "Tessa", "Ben", "Ruby", "Leo", "Nia", "Jude"]


def select_gear(setting: Setting, prize: Prize) -> Optional[Gear]:
    return GEAR[0] if setting.hot and prize.label == "popsicle" else None


def valid_combos() -> list[tuple[str, str]]:
    return [(place, "popsicle") for place in SETTINGS]


ASP_RULES = r"""
at_risk(P) :- prize(P).
fixable(P) :- at_risk(P), gear(g1).
valid(Place, P) :- setting(Place), at_risk(P), fixable(P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for gid in ["g1"]:
        lines.append(asp.fact("gear", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid/2."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = {(place, prize) for place, prize in valid_combos()}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall Tale story world: siblings, a popsicle, and scotch tape."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--sibling")
    ap.add_argument("--hero-type", choices=["sister", "brother"])
    ap.add_argument("--sibling-type", choices=["sister", "brother"])
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
    prize = args.prize or "popsicle"
    if prize not in PRIZES:
        raise StoryError("That prize is not part of this small world.")
    hero_type = args.hero_type or rng.choice(["sister", "brother"])
    sibling_type = args.sibling_type or ("brother" if hero_type == "sister" else "sister")
    hero_name = args.name or rng.choice(NAMES)
    sibling = args.sibling or rng.choice([n for n in NAMES if n != hero_name])
    return StoryParams(place=place, prize=prize, hero_name=hero_name, hero_type=hero_type,
                       sibling_name=sibling, sibling_type=sibling_type)


def _do_carry(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["wanting"] = hero.memes.get("wanting", 0.0) + 1
    prize.meters["heat"] = prize.meters.get("heat", 0.0) + 1
    prize.meters["drip"] = prize.meters.get("drip", 0.0) + 1
    if prize.meters["drip"] >= THRESHOLD:
        world.trace.append("The popsicle starts to melt into a sticky drip.")
    if hero.memes.get("worry", 0.0) >= THRESHOLD:
        hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1


def tell_story(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    sib = world.add(Entity(id=params.sibling_name, kind="character", type=params.sibling_type))
    prize = world.add(Entity(id="popsicle", kind="thing", type="popsicle", label="popsicle",
                             phrase="a bright striped popsicle", owner=hero.id))
    gear = select_gear(setting, prize)

    hero.memes["love"] = 1.0
    hero.memes["worry"] = 0.0
    sib.memes["calm"] = 1.0
    prize.meters["cold"] = 1.0
    prize.meters["drip"] = 0.0

    world.say(f"{hero.id} and {sib.id} came to {setting.place} with a bright popsicle big enough to make a shadow.")
    world.say(f"{hero.id} loved the treat, but the hot air was already licking at the edges like a fox after a pie.")

    world.para()
    world.say(
        f'({hero.id} thought, "If that popsicle melts on my fingers, the whole day will stick to me.")'
    )
    world.say(f'{hero.id} whispered, "We ought to hurry."')
    world.say(f'{sib.id} said, "Hurry, yes, but not like a whirlwind. Let me think."')

    hero.memes["worry"] += 1
    _do_carry(world, hero, prize)
    world.say(f"Then the popsicle gave a tiny shine and began to sag at the tip.")

    world.para()
    if gear:
        world.say(f'{sib.id} grinned like a lantern in July. "I have a scotch-tape fix."')
        world.say(f"{sib.id} helped by {gear.prep}.")
        prize.meters["drip"] = 0.0
        prize.meters["shape"] = 1.0
        prize.label = "popsicle scepter"
        prize.phrase = "a proud popsicle scepter wrapped in a paper sleeve"
        prize.memes = {"pride": 1.0}
        world.say(
            f"The little treat transformed right there in {setting.place}: not a droopy snack anymore, "
            f"but a popsicle scepter with a neat paper sleeve and a scotch-tape waist."
        )
        world.say(
            f'{hero.id} said, "Well butter my biscuit, it looks fit for a parade!" '
            f'And {sib.id} said, "Then parade we shall."'
        )
        world.say(
            f'Together they marched on, and {sib.id} {gear.tail}.'
        )
    else:
        world.say(f'{sib.id} could not find a fair fix, and the popsicle dripped into a sticky puddle.')

    world.para()
    if gear:
        hero.memes["worry"] = 0.0
        hero.memes["pride"] = 1.0
        sib.memes["pride"] = 1.0
        world.say(
            f"By the end, {hero.id} was carrying the transformed popsicle like a flag, "
            f"and not one shirt button had to suffer for it."
        )
        world.say(f"The hot wind kept blowing, but the story had already turned into a triumph.")
    else:
        world.say("The day ended with sticky fingers and a lesson about choosing a better trick next time.")

    world.facts.update(
        hero=hero,
        sibling=sib,
        prize=prize,
        gear=gear,
        place=params.place,
        hot=setting.hot,
        resolved=gear is not None,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sib = f["sibling"]
    return [
        f'Write a tall tale about {hero.id} and {sib.id}, a popsicle, and a roll of scotch tape.',
        f"Tell a child-friendly story where {hero.id} worries about a melting popsicle and {sib.id} finds a clever fix.",
        f"Create a funny, exaggerated story with inner monologue, dialogue, and a transformation from a messy treat to a neat one.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sib: Entity = f["sibling"]
    prize: Entity = f["prize"]
    gear: Optional[Gear] = f["gear"]
    place = f["place"]
    qa = [
        QAItem(
            question=f"What did {hero.id} and {sib.id} bring to {place}?",
            answer=f"They brought a bright popsicle that was so big it seemed almost like a tiny banner.",
        ),
        QAItem(
            question=f"Why did {hero.id} start to worry on the hot day?",
            answer=f"{hero.id} worried because the heat was making the popsicle drip, and nobody wanted sticky hands and a messy shirt.",
        ),
        QAItem(
            question=f"What did {sib.id} use to help if the popsicle started to melt?",
            answer=f"{sib.id} used scotch tape and a paper sleeve to make the popsicle easier to carry.",
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"How did the popsicle change by the end?",
                answer=f"It transformed from a droopy treat into a popsicle scepter wrapped in a neat sleeve, so it could be carried proudly.",
            )
        )
        qa.append(
            QAItem(
                question=f"How did {hero.id} feel after the fix?",
                answer=f"{hero.id} felt proud and relieved, because the worry turned into a parade mood instead of a sticky disaster.",
            )
        )
    return qa


WORLD_QA = [
    QAItem(
        question="What is scotch tape usually for?",
        answer="Scotch tape is usually used to stick paper or small things together, or to help hold a simple craft in place.",
    ),
    QAItem(
        question="Why do popsicles melt?",
        answer="Popsicles melt because they are frozen treats, and warm air makes the ice turn back into liquid.",
    ),
    QAItem(
        question="What does a sibling mean?",
        answer="A sibling is a brother or sister who belongs to the same family.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_QA


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
        lines.append(
            f"  {e.id:12} ({e.type:10}) meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.extend(f"  {x}" for x in world.trace)
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    StoryParams(place="porch", prize="popsicle", hero_name="Mina", hero_type="sister",
                sibling_name="Jude", sibling_type="brother"),
    StoryParams(place="yard", prize="popsicle", hero_name="Leo", hero_type="brother",
                sibling_name="Nia", sibling_type="sister"),
    StoryParams(place="market", prize="popsicle", hero_name="Ruby", hero_type="sister",
                sibling_name="Owen", sibling_type="brother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
