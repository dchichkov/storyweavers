#!/usr/bin/env python3
"""
A small superhero storyworld about bravery, a worried family, and helping a
child recover from malnutrition in an Egyptian setting.

The world is constraint-checked and driven by state:
- a brave hero notices someone is weak and hungry
- the hero or caregiver predicts that a plan without food or rest will fail
- a fitting rescue plan supplies nourishment and care
- the ending proves what changed in the world

This script follows the Storyweavers contract.
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
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)
    mood: str = ""


@dataclass
class AidPlan:
    id: str
    label: str
    phrase: str
    supports: set[str]
    prep: str
    tail: str
    gives: dict[str, float]
    restores: dict[str, float]


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


@dataclass
class StoryParams:
    place: str
    aid: str
    hero_name: str
    hero_gender: str
    hero_parent: str
    child_name: str
    child_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "clinic": Setting("the neighborhood clinic", True, {"visit"}, "careful"),
    "market": Setting("the sunny market", False, {"fetch_food"}, "busy"),
    "home": Setting("the family home", True, {"cook"}, "warm"),
    "courtyard": Setting("the Egyptian courtyard", False, {"fetch_food", "visit"}, "bright"),
}

AIDS = {
    "meal": AidPlan(
        id="meal",
        label="meal box",
        phrase="a warm meal box with bread, beans, and fruit",
        supports={"hunger", "weakness"},
        prep="go to the kitchen and pack a warm meal box",
        tail="carried the meal box home",
        gives={"nutrition": 2.0, "hope": 1.0},
        restores={"hunger": -2.0, "strength": 1.5, "worry": -1.0},
    ),
    "water": AidPlan(
        id="water",
        label="water bottle",
        phrase="a cool water bottle",
        supports={"thirst"},
        prep="fetch a cool water bottle",
        tail="brought the water bottle back",
        gives={"hope": 0.5},
        restores={"thirst": -2.0},
    ),
    "visit": AidPlan(
        id="visit",
        label="clinic visit",
        phrase="a careful visit to the clinic",
        supports={"weakness", "hunger"},
        prep="ask the grown-up to visit the clinic",
        tail="walked to the clinic together",
        gives={"hope": 1.0},
        restores={"strength": 1.0, "worry": -1.5},
    ),
}

GIRL_NAMES = ["Amina", "Layla", "Mira", "Nadia", "Zahra", "Sara"]
BOY_NAMES = ["Omar", "Youssef", "Adam", "Hassan", "Bilal", "Kareem"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: bravery, care, and a better ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-parent", choices=["mother", "father"])
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
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
    if args.place and args.aid:
        if args.aid not in SETTINGS[args.place].affords:
            raise StoryError(f"(No story: {SETTINGS[args.place].place} does not fit the {AIDS[args.aid].label} plan.)")
    if args.place is None:
        args.place = rng.choice(list(SETTINGS))
    valid_aids = [aid for aid, plan in AIDS.items() if aid in SETTINGS[args.place].affords]
    if args.aid is None:
        args.aid = rng.choice(valid_aids)
    elif args.aid not in valid_aids:
        raise StoryError(f"(No story: {SETTINGS[args.place].place} cannot support that plan.)")
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    hero_parent = args.hero_parent or rng.choice(["mother", "father"])
    return StoryParams(args.place, args.aid, hero_name, hero_gender, hero_parent, child_name, child_gender)


def can_help(place: str, aid: str) -> bool:
    return aid in SETTINGS[place].affords


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, plan in AIDS.items():
        lines.append(asp.fact("aid", aid))
        for s in sorted(plan.supports):
            lines.append(asp.fact("supports", aid, s))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A) :- affords(P,A), aid(A), place(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(params.hero_name, kind="character", type=params.hero_gender))
    parent = world.add(Entity("Parent", kind="character", type=params.hero_parent, label="the parent"))
    child = world.add(Entity(params.child_name, kind="character", type=params.child_gender))

    plan = AIDS[params.aid]

    hero.memes["bravery"] += 1
    child.meters["nutrition"] = 0.0
    child.meters["strength"] = 0.5
    child.memes["hope"] = 0.0
    parent.memes["worry"] = 1.0

    world.say(
        f"{hero.id} was a brave little superhero who watched over {world.setting.place}. "
        f"One day, {hero.id} noticed that {child.id} looked tired and small, and the family said "
        f"{child.pronoun('subject')} had been struggling with malnutrition."
    )
    world.say(
        f"{hero.id}'s {parent.label_word if parent.label else 'parent'} had a gentle voice and said, "
        f'"We need a safe plan, because food and rest can help more than rushing."'
    )

    world.para()
    world.say(
        f"{hero.id} wanted to fix everything at once, but {child.id} was too weak for a wild rescue. "
        f"The best idea was to {plan.prep} at {world.setting.place}."
    )

    child.memes["need"] += 1
    world.facts.update(hero=hero, parent=parent, child=child, plan=plan, setting=world.setting)

    if plan.id == "meal":
        child.meters["nutrition"] += 2.0
        child.meters["strength"] += 1.5
        child.memes["hope"] += 1.0
        parent.memes["worry"] -= 1.0
        world.say(
            f"{hero.id} opened the cupboard, packed bread, beans, and fruit, and carried the meal to {child.id}. "
            f"{child.id} took small bites first, then bigger ones, until {child.pronoun('subject')} looked brighter."
        )
    elif plan.id == "water":
        child.meters["nutrition"] += 0.2
        child.meters["strength"] += 0.2
        child.memes["hope"] += 0.5
        world.say(
            f"{hero.id} brought a water bottle, and {child.id} drank slowly. "
            f"It helped a little, but the grown-ups still knew {child.id} needed real food, too."
        )
    else:
        child.meters["strength"] += 1.0
        parent.memes["worry"] -= 1.5
        child.memes["hope"] += 1.0
        world.say(
            f"{hero.id} and the parent walked to the clinic, where kind helpers checked {child.id}. "
            f"They explained that careful food, water, and rest would help {child.id} grow stronger again."
        )

    world.para()
    world.say(
        f"By the end, the brave superhero did not need thunder or flashing lights. "
        f"{child.id} sat up straighter, {hero.id} smiled, and the Egyptian home felt warm and safe again."
    )

    world.facts["resolved"] = child.meters["nutrition"] > 0.5
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    child = f["child"]
    plan = f["plan"]
    return [
        f'Write a short superhero story for a young child about bravery, Egypt, and helping {child.id}.',
        f"Tell a gentle story where {hero.id} notices malnutrition and chooses a caring plan instead of a reckless rescue.",
        f'Write an Egyptian superhero story that ends with {child.id} feeling stronger after a safe help plan.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    child = f["child"]
    plan = f["plan"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the brave superhero in the story?",
            answer=f"The brave superhero was {hero.id}. {hero.id} watched over {setting.place} and tried to help carefully.",
        ),
        QAItem(
            question=f"Why did {hero.id} worry about {child.id}?",
            answer=f"{hero.id} worried because {child.id} looked tired and weak from malnutrition, so {child.pronoun('subject')} needed care and nourishment.",
        ),
        QAItem(
            question=f"What did {hero.id} do to help {child.id}?",
            answer=f"{hero.id} chose the {plan.label} plan and used {plan.phrase} to help {child.id} feel better and stronger.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.id} sitting up straighter, {hero.id} smiling, and the home feeling safe and warm again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel worried or scared.",
        ),
        QAItem(
            question="What is a clinic for?",
            answer="A clinic is a place where kind helpers check on people and help them stay healthy.",
        ),
        QAItem(
            question="Why do children need food?",
            answer="Children need food so their bodies can grow, play, and stay strong.",
        ),
    ]


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
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
    StoryParams("courtyard", "meal", "Amina", "girl", "mother", "Omar", "boy"),
    StoryParams("clinic", "visit", "Kareem", "boy", "father", "Layla", "girl"),
    StoryParams("home", "meal", "Mira", "girl", "mother", "Hassan", "boy"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, a) for p, s in SETTINGS.items() for a in s.affords}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def build_sample_from_params(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} in {p.place} ({p.aid})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
