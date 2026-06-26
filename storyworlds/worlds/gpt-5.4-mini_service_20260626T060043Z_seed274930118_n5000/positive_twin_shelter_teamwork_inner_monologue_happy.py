#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about twin helpers, shelter-building, teamwork,
and a bright happy ending.

The seed image:
Two twins are out when the sky turns splashy. They notice a little friend in
need of shelter. One twin thinks aloud, the other gathers materials, and both
work together to build a cozy place to stay dry. The story ends with warmth,
kindness, and a cheerful shared feeling.

This world keeps the domain intentionally small:
- entities have physical meters and emotional memes
- the plot is driven by a simple causal simulation
- the prose is child-facing and rhyme-leaning
- the ASP twin mirrors the reasonableness gate
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
# Core model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("dry", "rain", "build", "shelter"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "hope", "pride", "calm", "teamwork", "thought"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    weather: str
    affords: set[str] = field(default_factory=set)


@dataclass
class ShelterPlan:
    id: str
    label: str
    phrase: str
    materials: list[str]
    cover: str
    cozy: str


@dataclass
class StoryParams:
    setting: str
    plan: str
    helper1: str
    helper2: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "green_hill": Setting(place="the green hill", weather="windy", affords={"build_shelter"}),
    "rainy_lane": Setting(place="the rainy lane", weather="rainy", affords={"build_shelter"}),
    "woodland": Setting(place="the woodland path", weather="rainy", affords={"build_shelter"}),
}

PLANS = {
    "leaf_hut": ShelterPlan(
        id="leaf_hut",
        label="a leaf hut",
        phrase="a little leaf hut",
        materials=["big leaves", "twigs", "soft moss"],
        cover="rain",
        cozy="soft and snug",
    ),
    "cloth_tent": ShelterPlan(
        id="cloth_tent",
        label="a cloth tent",
        phrase="a small cloth tent",
        materials=["a blanket", "sticks", "string"],
        cover="rain",
        cozy="warm and dry",
    ),
    "branch_roof": ShelterPlan(
        id="branch_roof",
        label="a branch roof",
        phrase="a tiny branch roof",
        materials=["branches", "long grass", "a shared blanket"],
        cover="rain",
        cozy="dry and bright",
    ),
}

CHARACTERS = {
    "twin_a": ("Tia", "girl"),
    "twin_b": ("Tom", "boy"),
    "twin_c": ("Mina", "girl"),
    "twin_d": ("Milo", "boy"),
    "friend": ("Pip", "thing"),
}

NAMES = ["Tia", "Tom", "Mina", "Milo", "Nia", "Noa"]


# ---------------------------------------------------------------------------
# Cause and effect
# ---------------------------------------------------------------------------

def _rain(world: World, friend: Entity) -> None:
    friend.meters["rain"] += 1
    friend.memes["worry"] += 1
    world.say(f"The little sky let down rain, and {friend.id} felt a tiny shiver.")


def _inner_monologue(world: World, helper: Entity, friend: Entity, plan: ShelterPlan) -> None:
    helper.memes["thought"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"{helper.id} thought, 'We can help our friend stay dry if we work as one.'"
    )
    world.say(
        f"{helper.id} looked at {friend.id} and whispered, 'A {plan.label} would be a kind and cozy nest.'"
    )


def _gather(world: World, helper: Entity, plan: ShelterPlan) -> None:
    helper.meters["build"] += 1
    helper.memes["teamwork"] += 1
    world.say(f"{helper.id} gathered {plan.materials[0]}, and then the next thing, too, with careful feet.")


def _assist(world: World, helper: Entity, plan: ShelterPlan) -> None:
    helper.meters["build"] += 1
    helper.memes["teamwork"] += 1
    world.say(f"{helper.id} helped fit in {plan.materials[1]} and held the shape just right.")


def _build_shelter(world: World, helper1: Entity, helper2: Entity, friend: Entity, plan: ShelterPlan) -> None:
    key = ("build_shelter", plan.id)
    if key in world.fired:
        return
    world.fired.add(key)
    if world.setting.place not in {"the green hill", "the rainy lane", "the woodland path"}:
        raise StoryError("This setting cannot support a shelter story.")
    if friend.meters["rain"] < THRESHOLD:
        raise StoryError("The friend must first need shelter from the rain.")
    helper1.meters["shelter"] += 1
    helper2.meters["shelter"] += 1
    friend.meters["shelter"] += 1
    friend.meters["dry"] += 2
    friend.memes["calm"] += 1
    friend.memes["joy"] += 1
    helper1.memes["joy"] += 1
    helper2.memes["joy"] += 1
    helper1.memes["pride"] += 1
    helper2.memes["pride"] += 1
    world.say(f"Together they made {plan.phrase}, and it stood like a small poem in the rain.")
    world.say(f"Inside, {friend.id} was {plan.cozy}, with no more shiver at all.")


def tell(world: World, helper1: Entity, helper2: Entity, friend: Entity, plan: ShelterPlan) -> None:
    world.say(
        f"On {world.setting.place}, two twins went walking with a friend, and the wind sang a silver song."
    )
    world.say(
        f"{helper1.id} and {helper2.id} were twins with bright eyes and kind hands, and they liked doing good together."
    )
    world.say(f"{friend.id} watched the clouds and hoped the wet would pass.")

    world.para()
    _rain(world, friend)
    _inner_monologue(world, helper1, friend, plan)
    _gather(world, helper1, plan)
    _assist(world, helper2, plan)
    _build_shelter(world, helper1, helper2, friend, plan)

    world.para()
    world.say(
        f"When the work was done, the rain still fell, but the shelter stood firm, and the three of them smiled."
    )
    world.say(
        f"The twins sat side by side, feeling warm in their hearts, while {friend.id} stayed snug and dry."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.plan not in PLANS:
        raise StoryError(f"Unknown shelter plan: {params.plan}")
    setting = SETTINGS[params.setting]
    plan = PLANS[params.plan]

    world = World(setting)

    h1_name, h1_type = CHARACTERS[params.helper1]
    h2_name, h2_type = CHARACTERS[params.helper2]
    fr_name, fr_type = CHARACTERS[params.friend]

    helper1 = world.add(Entity(id=h1_name, kind="character", type=h1_type))
    helper2 = world.add(Entity(id=h2_name, kind="character", type=h2_type))
    friend = world.add(Entity(id=fr_name, kind="character", type=fr_type))

    world.facts.update(helper1=helper1, helper2=helper2, friend=friend, plan=plan)
    tell(world, helper1, helper2, friend, plan)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    plan: ShelterPlan = f["plan"]
    helper1: Entity = f["helper1"]
    friend: Entity = f["friend"]
    return [
        f"Write a nursery-rhyme-style story about twin helpers building {plan.phrase} for a friend in the rain.",
        f"Tell a gentle happy-ending story where {helper1.id} thinks aloud and the twins use teamwork to make shelter.",
        f"Write a short child-friendly story with the words positive, twin, and shelter, ending with everyone dry and smiling.",
        f"Make the story feel like a little rhyme: rain comes, twins help, and a cozy shelter saves the day.",
        f"Write a story about {helper1.id}, a twin, and {friend.id} finding shelter together through teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h1: Entity = f["helper1"]
    h2: Entity = f["helper2"]
    friend: Entity = f["friend"]
    plan: ShelterPlan = f["plan"]
    setting = world.setting.place
    return [
        QAItem(
            question=f"Who helped build the shelter on {setting}?",
            answer=f"The twins {h1.id} and {h2.id} helped together, and they worked as a team.",
        ),
        QAItem(
            question=f"What did {h1.id} think of to keep {friend.id} dry?",
            answer=f"{h1.id} thought they could make {plan.phrase} so {friend.id} could stay safe and dry.",
        ),
        QAItem(
            question=f"What did the twins build in the rain?",
            answer=f"They built {plan.phrase}, a little shelter that kept the friend dry.",
        ),
        QAItem(
            question=f"How did {friend.id} feel at the end?",
            answer=f"{friend.id} felt calm, dry, and happy because the shelter was cozy and the twins helped kindly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together to do something good.",
        ),
        QAItem(
            question="What is shelter?",
            answer="A shelter is a place that protects someone from rain, wind, or sun.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet thinking in a character's mind, like a secret little voice.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending is when the problem gets solved and the characters finish feeling safe and glad.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A shelter story is reasonable when the friend needs rain protection,
% two distinct twins help, and the chosen shelter plan can cover that need.

needs_shelter(F) :- rain(F), friend(F).
teamwork(H1,H2) :- twin(H1), twin(H2), H1 != H2.
has_help(F) :- teamwork(H1,H2), helps(H1,F), helps(H2,F).

valid_story(Setting,Plan,H1,H2,F) :-
    place(Setting),
    plan(Plan),
    friend(F),
    needs_shelter(F),
    has_help(F),
    fits(Plan, rain).

#show valid_story/5.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        if setting.weather == "rainy":
            lines.append(asp.fact("rain_place", sid))
    for pid, plan in PLANS.items():
        lines.append(asp.fact("plan", pid))
        for m in plan.materials:
            lines.append(asp.fact("material", pid, m))
        lines.append(asp.fact("fits", pid, plan.cover))
    # simple role facts
    lines.append(asp.fact("twin", "twin_a"))
    lines.append(asp.fact("twin", "twin_b"))
    lines.append(asp.fact("twin", "twin_c"))
    lines.append(asp.fact("twin", "twin_d"))
    lines.append(asp.fact("friend", "friend"))
    lines.append(asp.fact("rain", "friend"))
    for t in ("twin_a", "twin_b", "twin_c", "twin_d"):
        lines.append(asp.fact("helps", t, "friend"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    # Compare Python reasonableness with ASP twin on the compact set.
    py = set(valid_stories())
    import asp

    clingo = set(asp_valid_stories())
    if py == clingo:
        print(f"OK: ASP matches Python reasonableness gate ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
    if clingo - py:
        print("  only in clingo:", sorted(clingo - py))
    return 1


def valid_stories() -> list[tuple[str, str, str, str, str]]:
    stories: list[tuple[str, str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for plan_id, plan in PLANS.items():
            if plan.cover != "rain":
                continue
            for h1 in ("twin_a", "twin_c"):
                for h2 in ("twin_b", "twin_d"):
                    if h1 == h2:
                        continue
                    stories.append((setting_id, plan_id, h1, h2, "friend"))
    return stories


# ---------------------------------------------------------------------------
# Resolution and rendering
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about twins, shelter, teamwork, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--helper1", choices=tuple(CHARACTERS))
    ap.add_argument("--helper2", choices=tuple(CHARACTERS))
    ap.add_argument("--friend", choices=tuple(CHARACTERS))
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
    setting = args.setting or rng.choice(list(SETTINGS))
    plan = args.plan or rng.choice(list(PLANS))
    helper1 = args.helper1 or rng.choice(["twin_a", "twin_c"])
    helper2 = args.helper2 or rng.choice(["twin_b", "twin_d"])
    if helper1 == helper2:
        raise StoryError("The twins must be two different helpers.")
    friend = args.friend or "friend"
    return StoryParams(setting=setting, plan=plan, helper1=helper1, helper2=helper2, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="rainy_lane", plan="cloth_tent", helper1="twin_a", helper2="twin_b", friend="friend"),
    StoryParams(setting="woodland", plan="leaf_hut", helper1="twin_c", helper2="twin_d", friend="friend"),
    StoryParams(setting="green_hill", plan="branch_roof", helper1="twin_a", helper2="twin_d", friend="friend"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print(" ", row)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
