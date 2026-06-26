#!/usr/bin/env python3
"""
storyworlds/worlds/veal_fast_twist_rhyming_story.py
====================================================

A tiny storyworld in a rhyming-story style about a child who wants to make veal
fast, hits a careful cooking snag, and finds a Twist that keeps the dinner
tender.

Premise:
- A child loves helping in the kitchen.
- They want to make veal fast for supper.
- A parent worries that rushing will make the veal tough or uneven.

Turn:
- The child tries to hurry.
- The parent explains that veal needs a calmer pace.
- The Twist is a gentler method: lower the heat, add a bright finish, and wait
  for the pan to sing instead of hiss.

Resolution:
- The child slows down, stirs carefully, and the veal comes out tender.
- The ending image proves the change: fast became careful, and the meal became
  ready and right.
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
    worn_by: Optional[str] = None
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


@dataclass
class Setting:
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Helper:
    id: str
    label: str
    prep: str
    finish: str
    tags: set[str] = field(default_factory=set)


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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_rush(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("kid")
    if kid.memes.get("rush", 0.0) < THRESHOLD:
        return out
    sig = ("rush",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.meters["heat"] = kid.meters.get("heat", 0.0) + 1
    kid.memes["impatience"] = kid.memes.get("impatience", 0.0) + 1
    out.append("The pan got hot and the hurry felt harder to hide.")
    return out


def _r_tough(world: World) -> list[str]:
    kid = world.get("kid")
    stew = world.get("veal")
    if kid.meters.get("heat", 0.0) < THRESHOLD:
        return []
    sig = ("tough",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    stew.meters["toughness"] = stew.meters.get("toughness", 0.0) + 1
    return ["Rushing made the veal fear becoming tough and dry."]


def _r_soothe(world: World) -> list[str]:
    kid = world.get("kid")
    helper = world.get("twist")
    if kid.memes.get("calm", 0.0) < THRESHOLD:
        return []
    sig = ("soothe",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    kid.meters["heat"] = max(0.0, kid.meters.get("heat", 0.0) - 1)
    kid.memes["joy"] = kid.memes.get("joy", 0.0) + 1
    return [f"The Twist of {helper.label} turned the sizzle soft and bright."]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_rush, _r_tough, _r_soothe):
            s = rule(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING = Setting(place="the kitchen", affords={"cook"})
ACTIVITY = Activity(
    id="cook",
    verb="cook veal",
    gerund="cooking veal",
    rush="rush the pan",
    mess="scorch",
    soil="too dry",
    keyword="veal",
    tags={"veal", "fast", "cook"},
)
PRIZE = Prize(label="veal", phrase="a small veal cutlet", type="veal")
HELPERS = {
    "twist": Helper(
        id="twist",
        label="a lemon twist",
        prep="add a lemon twist",
        finish="the Twist made the dish taste light and bright",
        tags={"twist", "lemon"},
    )
}

GIRL_NAMES = ["Mia", "Luna", "Zoe", "Nora", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Ben", "Max"]
TRAITS = ["cheerful", "curious", "brave", "spry", "playful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def can_story(place: str, activity: str, prize: str) -> bool:
    return place == "kitchen" and activity == "cook" and prize == "veal"


ASP_RULES = r"""
place(kitchen).
activity(cook).
prize(veal).
helper(twist).

compatible(P,A,R) :- place(P), activity(A), prize(R), P = kitchen, A = cook, R = veal.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "kitchen"),
            asp.fact("activity", "cook"),
            asp.fact("prize", "veal"),
            asp.fact("helper", "twist"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [("kitchen", "cook", "veal")]


def tell(name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(SETTING)
    kid = world.add(Entity(id="kid", kind="character", type=gender, label=name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=parent_type))
    veal = world.add(Entity(id="veal", type="veal", label="veal", phrase="a small veal cutlet", owner="kid"))
    twist = world.add(Entity(id="twist", type="thing", label="lemon twist", phrase="a bright lemon twist"))
    world.facts.update(kid=kid, parent=parent, veal=veal, twist=twist)

    kid.memes["love"] = 1
    world.say(f"{name} was a {trait} little {gender} who loved the kitchen and the clink of pans.")
    world.say(f"{name} wanted to cook veal fast, with a quick step and a nimble clasp.")
    world.say(f"{name} liked the smell of supper time and wished dinner would happen in a flash.")
    world.para()
    world.say(f"One bright evening, {name} and the {parent_type} went to the kitchen.")
    world.say(f"{name} said, 'I can cook veal fast!' but the {parent_type} gave a careful glance.")
    kid.memes["rush"] = 1
    propagate(world, narrate=True)
    world.say(f'"If you rush, the veal may go tough," the {parent_type} said with a soft hush.')
    world.say(f"{name} tried to hurry the pan and stir in a spin, but the heat only hissed from within.")
    world.para()

    world.say(f"Then came the Twist: the {parent_type} showed {name} a lemon twist with a sunny shine.")
    kid.memes["calm"] = 1
    propagate(world, narrate=True)
    world.say(f'"Let it cook low and slow," the {parent_type} said, "then the veal will taste fine."')
    world.say(f"{name} slowed down, used a gentle hand, and watched the juices turn clear and grand.")
    world.say(f"At last the veal was tender, not hurried or hard, and the kitchen smelled sweet all around the yard.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid = f["kid"]
    return [
        'Write a short rhyming story for a small child about veal, fast, and a Twist in the kitchen.',
        f"Tell a rhyming tale where {kid.label} wants to cook veal fast, but the parent insists on a gentler pace.",
        "Write a gentle kitchen story that ends with tender veal and a bright Twist.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid = f["kid"]
    parent = f["parent"]
    return [
        QAItem(
            question=f"What did {kid.label} want to do fast in the kitchen?",
            answer=f"{kid.label} wanted to cook veal fast in the kitchen, because supper sounded exciting and quick.",
        ),
        QAItem(
            question=f"Why did the {parent.type} worry about hurrying the veal?",
            answer="The parent worried that rushing would make the veal tough and dry instead of tender.",
        ),
        QAItem(
            question="What was the Twist in the story?",
            answer="The Twist was a bright lemon twist and a calmer way of cooking that helped the veal taste better.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The veal cooked gently, stayed tender, and the kitchen ended in a happy, warm dinner image.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does fast mean?",
            answer="Fast means happening quickly, with little waiting.",
        ),
        QAItem(
            question="Why do cooks sometimes lower the heat?",
            answer="Cooks lower the heat so food can cook more gently and not burn or turn tough.",
        ),
        QAItem(
            question="What is a twist of lemon used for?",
            answer="A twist of lemon can add a bright smell and flavor to food or drinks.",
        ),
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "kitchen":
        raise StoryError("This storyworld only supports the kitchen setting.")
    if args.activity and args.activity != "cook":
        raise StoryError("This storyworld only supports the cook activity.")
    if args.prize and args.prize != "veal":
        raise StoryError("This storyworld only supports veal as the prize ingredient.")
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError("Gender must be girl or boy.")

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place="kitchen",
        activity="cook",
        prize="veal",
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.gender, params.parent, params.trait)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming kitchen storyworld about veal, fast, and a Twist.")
    ap.add_argument("--place", choices=["kitchen"])
    ap.add_argument("--activity", choices=["cook"])
    ap.add_argument("--prize", choices=["veal"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        params = resolve_params(args, random.Random(base_seed))
        params.seed = base_seed
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        for i in range(max(args.n, 1)):
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
