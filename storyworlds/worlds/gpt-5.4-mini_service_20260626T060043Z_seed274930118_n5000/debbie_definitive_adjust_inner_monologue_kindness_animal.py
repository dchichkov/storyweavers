#!/usr/bin/env python3
"""
A tiny animal-story world about a helper who makes a definitive choice,
adjusts their plan, and uses kindness to fix a hurt feeling.

The seed tale is imagined as follows:
A squirrel named Debbie wants to lead a picnic. She makes a very definite
plan, but then notices a small rabbit is left out. Debbie listens to her
inner monologue, realizes the plan needs adjusting, and chooses kindness.
She changes the game, includes the rabbit, and the picnic ends happily.

World shape:
- typed entities with physical meters and emotional memes
- one causal turn: a firm plan creates a social problem
- one resolution: Debbie adjusts and acts kindly
- child-facing prose, animal-story style
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


@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "animal"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]


@dataclass
class Setting:
    place: str = "the meadow"
    weather: str = "soft morning"


@dataclass
class Plan:
    label: str
    action: str
    adjust_action: str
    kind_act: str
    risk: str
    result: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


STORY_PLANS = {
    "picnic": Plan(
        label="picnic",
        action="set the picnic rules and keep them the same",
        adjust_action="move the picnic blanket closer and make room for one more friend",
        kind_act="share the berry muffins",
        risk="the little rabbit would be left out",
        result="everyone ate together under the trees",
    ),
    "game": Plan(
        label="game",
        action="pick the rules and refuse to change them",
        adjust_action="slow the game down and explain the turns kindly",
        kind_act="let the shy hedgehog go first",
        risk="the shy hedgehog would feel shut out",
        result="the game turned warm and fair",
    ),
}


HERO_NAMES = ["Debbie", "Mina", "Poppy", "Ruby", "Hazel"]
SIDE_NAMES = ["Benny", "Tilly", "Nico", "Luna", "Milo"]


@dataclass
class StoryParams:
    plan: str
    name: str = "Debbie"
    friend: str = "Benny"
    seed: Optional[int] = None


ASP_RULES = r"""
hero(debbie).
plan(picnic).
plan(game).

requires_adjust(picnic).
requires_adjust(game).

kindness_help(picnic).
kindness_help(game).

adjusted(picnic) :- requires_adjust(picnic), kindness_help(picnic).
adjusted(game) :- requires_adjust(game), kindness_help(game).

#show adjusted/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [asp.fact("hero", "debbie")]
        + [asp.fact("plan", p) for p in STORY_PLANS]
        + [asp.fact("requires_adjust", p) for p in STORY_PLANS]
        + [asp.fact("kindness_help", p) for p in STORY_PLANS]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show adjusted/1."))
    got = sorted(set(asp.atoms(model, "adjusted")))
    exp = [("picnic",), ("game",)]
    if got == exp:
        print("OK: clingo gate matches Python reasonableness.")
        return 0
    print("MISMATCH:", got, exp)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal-story world about Debbie, kindness, and adjustment.")
    ap.add_argument("--plan", choices=STORY_PLANS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    plan = args.plan or rng.choice(list(STORY_PLANS))
    name = args.name or "Debbie"
    friend = args.friend or rng.choice(SIDE_NAMES)
    return StoryParams(plan=plan, name=name, friend=friend)


def inner_monologue(world: World, hero: Entity, plan: Plan, friend: Entity) -> None:
    world.say(
        f"{hero.id} looked at the {plan.label} and thought, "
        f"“I want this to go the right way.”"
    )
    world.say(
        f"Inside, {hero.pronoun('possessive')} own thoughts nudged her: "
        f"maybe the first idea was too definite."
    )


def setup_story(world: World, hero: Entity, friend: Entity, plan: Plan) -> None:
    hero.memes["purpose"] = 1
    hero.memes["certainty"] = 1
    friend.memes["hope"] = 1
    world.say(
        f"Debbie was a clever squirrel who loved tidy plans at {world.setting.place}."
    )
    world.say(
        f"She had a very definite idea for the {plan.label}, and {friend.id} came along to join her."
    )
    world.say(
        f"{hero.id} wanted to {plan.action}, and that felt important to her."
    )


def conflict(world: World, hero: Entity, friend: Entity, plan: Plan) -> None:
    hero.memes["worry"] = 1
    friend.memes["left_out"] = 1
    world.para()
    world.say(
        f"Then {hero.id} noticed something quiet and uncomfortable: {plan.risk}."
    )
    world.say(
        f"{hero.id} paused and listened to her inner monologue."
    )
    inner_monologue(world, hero, plan, friend)
    world.say(
        f"She could tell that keeping everything the same would not feel kind."
    )


def resolve(world: World, hero: Entity, friend: Entity, plan: Plan) -> None:
    hero.memes["kindness"] = 1
    hero.memes["certainty"] = 0
    hero.memes["adjusted"] = 1
    friend.memes["left_out"] = 0
    friend.memes["joy"] = 1
    world.para()
    world.say(
        f"So Debbie adjusted her plan."
    )
    world.say(
        f"She chose kindness and did something gentle instead: she decided to {plan.adjust_action}."
    )
    world.say(
        f"That let her {plan.kind_act}, and soon {plan.result}."
    )
    world.say(
        f"{friend.id} smiled, Debbie smiled, and the day felt soft and right."
    )


def tell(plan_key: str, name: str, friend_name: str) -> World:
    setting = Setting()
    world = World(setting)
    plan = STORY_PLANS[plan_key]
    hero = world.add(Entity(id=name, kind="character", type="squirrel", traits=["clever", "kind"]))
    friend = world.add(Entity(id=friend_name, kind="character", type="rabbit", traits=["small", "gentle"]))
    setup_story(world, hero, friend, plan)
    conflict(world, hero, friend, plan)
    resolve(world, hero, friend, plan)
    world.facts.update(hero=hero, friend=friend, plan=plan_key, adjusted=True)
    return world


def generation_prompts(world: World) -> list[str]:
    plan = world.facts["plan"]
    return [
        f'Write a short animal story about Debbie making a {plan} plan, then adjusting it kindly.',
        "Tell a gentle story where a squirrel listens to inner monologue and chooses kindness.",
        f'Write a small story for children that includes the word "definitive" and ends with Debbie adjusting her idea.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    plan = f["plan"]
    return [
        QAItem(
            question=f"Who is the main animal in the story?",
            answer=f"The main animal is {hero.id}, a squirrel named Debbie who learns to adjust her plan."
        ),
        QAItem(
            question=f"What did Debbie need to do when her idea felt too definite?",
            answer=f"She needed to adjust her plan so her friend would not be left out."
        ),
        QAItem(
            question=f"How did Debbie show kindness?",
            answer=f"She listened to her inner monologue, changed the plan, and made room for {friend.id}."
        ),
        QAItem(
            question=f"What changed by the end of the {plan} story?",
            answer=f"The plan changed from being too definite to being kinder and more shared."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to adjust something?",
            answer="To adjust something means to change it a little so it fits better or works better."
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, caring, and thoughtful about how other creatures feel."
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice of thoughts a character hears inside their own mind."
        ),
        QAItem(
            question="What does definitive mean?",
            answer="Definitive means sure, firm, and not changing easily."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.plan, params.name, params.friend)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show adjusted/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show adjusted/1."))
        atoms = sorted(set(asp.atoms(model, "adjusted")))
        print(f"{len(atoms)} compatible story patterns:")
        for (plan,) in atoms:
            print(f"  {plan}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for plan in STORY_PLANS:
            p = StoryParams(plan=plan, name="Debbie", friend="Benny")
            samples.append(generate(p))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            p = resolve_params(args, rng)
            p.seed = base_seed + i
            samples.append(generate(p))

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
