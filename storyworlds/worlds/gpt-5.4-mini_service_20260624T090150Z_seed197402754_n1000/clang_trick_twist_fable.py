#!/usr/bin/env python3
"""
clang_trick_twist_fable.py
==========================

A small fable-style story world about a bell's clang, a trick, and a Twist.

Premise:
- A proud little fox keeps a shiny bell for the market path.
- A clever crow plays a harmless trick that turns into a trouble.
- A Twist in the road and a timely clang teach everyone a gentler lesson.

The world is intentionally small and constraint-checked:
- One animal wants one thing.
- One trick creates a visible problem.
- One twist in the plan resolves it in a fable-like ending.
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
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"fox", "vixen"}
        male = {"crow", "wolf", "fox"}
        # Keep animal storytelling simple and child-facing:
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the lane"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
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
    genders: set[str] = field(default_factory=lambda: {"fox", "crow"})


@dataclass
class Twist:
    id: str
    label: str
    method: str
    ending: str


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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "lane": Setting(place="the lane", affords={"clang", "trick"}),
    "market": Setting(place="the market road", affords={"clang", "trick"}),
    "barn": Setting(place="the barn path", affords={"clang", "trick"}),
}

ACTIONS = {
    "clang": Action(
        id="clang",
        verb="ring the bell",
        gerund="ringing the bell",
        rush="dash to the bell rope",
        mess="noise",
        soil="loud and foolish",
        keyword="clang",
        tags={"clang", "sound"},
    ),
    "trick": Action(
        id="trick",
        verb="play a trick",
        gerund="playing a trick",
        rush="run away laughing",
        mess="trouble",
        soil="mischief",
        keyword="trick",
        tags={"trick", "mischief"},
    ),
}

PRIZES = {
    "bell": Prize(
        label="bell",
        phrase="a shiny little bell",
        type="bell",
    ),
    "basket": Prize(
        label="basket",
        phrase="a woven basket of apples",
        type="basket",
    ),
}

TWISTS = {
    "kind_turn": Twist(
        id="kind_turn",
        label="a kind twist",
        method="used the bell to call everyone back",
        ending="shared the apples and laughed together",
    ),
    "honest_turn": Twist(
        id="honest_turn",
        label="an honest twist",
        method="told the truth about the trick",
        ending="fixed the trouble before it grew",
    ),
}

NAMES = ["Fox", "Crow", "Bramble", "Moss", "Pip", "Wren"]
TRAITS = ["proud", "clever", "small", "quick", "gentle"]


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------
def prize_at_risk(action: Action, prize: Prize) -> bool:
    if action.id == "clang":
        return prize.type == "bell"
    if action.id == "trick":
        return prize.type == "basket"
    return False


def reasonableness_check(action: Action, prize: Prize, twist: Twist) -> bool:
    if action.id == "clang" and prize.type != "bell":
        return False
    if action.id == "trick" and prize.type != "basket":
        return False
    return twist.id in TWISTS


def predict_problem(world: World, hero: Entity, action: Action, prize: Entity) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["push"] = 1.0
    if action.id == "clang":
        prize.meters["shaken"] = 1.0
    else:
        prize.meters["stolen"] = 1.0
    return {
        "risk": prize_at_risk(action, PRIZES[prize.type]),
        "stress": 1.0 if action.id == "trick" else 0.5,
    }


def lead_in(world: World, hero: Entity, friend: Entity, prize: Entity, action: Action) -> None:
    world.say(
        f"{hero.id} was a small {hero.type} who loved {action.gerund} and "
        f"liked the look of {prize.phrase}."
    )
    world.say(
        f"{friend.id} watched from the fence and thought a quick trick might be funny."
    )


def conflict(world: World, hero: Entity, friend: Entity, prize: Entity, action: Action) -> None:
    world.para()
    world.say(
        f"One day at {world.setting.place}, {hero.id} reached for {prize.label}, "
        f"but {friend.id} made a trick."
    )
    if action.id == "clang":
        world.say(
            f"The bell gave a bright clang, and the sound startled every feather and foot."
        )
        prize.meters["shaken"] = 1.0
        hero.memes["surprise"] = 1.0
    else:
        world.say(
            f"The trick nudged the {prize.label}, and the basket tilted toward trouble."
        )
        prize.meters["tilted"] = 1.0
        hero.memes["worry"] = 1.0
    world.fired.add(("conflict", hero.id, friend.id, prize.id, action.id))


def twist_resolution(world: World, hero: Entity, friend: Entity, prize: Entity, action: Action, twist: Twist) -> None:
    world.para()
    if twist.id == "kind_turn":
        world.say(
            f"Then came a Twist: {hero.id} did not scold. Instead, {hero.pronoun()} "
            f"{twist.method}."
        )
        hero.memes["kindness"] = 1.0
        friend.memes["shame"] = 0.5
        world.say(
            f"{friend.id} hopped down, helped steady the {prize.label}, and the two of them "
            f"{twist.ending}."
        )
    else:
        world.say(
            f"Then came a Twist: {friend.id} stopped laughing and {twist.method}."
        )
        friend.memes["honesty"] = 1.0
        hero.memes["forgive"] = 1.0
        world.say(
            f"{hero.id} listened, and together they {twist.ending}."
        )
    world.say(
        f"In the end, the lane grew quiet again, and the little bell still gave a soft clang in the breeze."
    )


def tell(setting: Setting, action: Action, prize_cfg: Prize, twist: Twist,
         hero_name: str, friend_name: str, hero_type: str = "fox") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type="crow", label=friend_name))
    prize = world.add(Entity(id=prize_cfg.type, type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))

    lead_in(world, hero, friend, prize, action)
    conflict(world, hero, friend, prize, action)
    twist_resolution(world, hero, friend, prize, action, twist)

    world.facts.update(
        hero=hero,
        friend=friend,
        prize=prize,
        action=action,
        twist=twist,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    twist: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="lane", action="clang", prize="bell", twist="kind_turn", hero_name="Pip", friend_name="Wren"),
    StoryParams(place="market", action="trick", prize="basket", twist="honest_turn", hero_name="Moss", friend_name="Crow"),
]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a young child that includes the words "{f["action"].keyword}" and "Twist".',
        f"Tell a gentle story where {f['hero'].id} and {f['friend'].id} face a small problem at {f['setting'].place}.",
        f"Write a simple fable ending that shows how a trick can be fixed kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, action, twist = f["hero"], f["friend"], f["prize"], f["action"], f["twist"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {hero.type}, and {friend.id}, who made a small trick.",
        ),
        QAItem(
            question=f"What did the bell or basket mean in the story?",
            answer=f"The {prize.label} was the thing that mattered most, because the {action.id} could upset it.",
        ),
        QAItem(
            question=f"What happened when the trouble began at {f['setting'].place}?",
            answer=f"The trick caused a problem, and then a Twist helped everyone make things right again.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {twist.label.lower()} and a calm, happy moment in the lane.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clang?",
            answer="A clang is a loud, ringing sound, like a bell or metal striking something hard.",
        ),
        QAItem(
            question="What is a trick?",
            answer="A trick is a playful act that can be funny, but it can also cause trouble if it is unkind.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a change in the plan that can surprise the characters and help the story turn in a new way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(lane).
setting(market).
setting(barn).

affords(lane,clang).
affords(lane,trick).
affords(market,clang).
affords(market,trick).
affords(barn,clang).
affords(barn,trick).

action(clang).
action(trick).

prize(bell).
prize(basket).

worn_on(bell,bell).
worn_on(basket,basket).

can_pair(clang,bell).
can_pair(trick,basket).

valid_story(Place,Action,Prize) :- affords(Place,Action), can_pair(Action,Prize).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
        for a in sorted(SETTINGS[s].affords):
            lines.append(asp.fact("affords", s, a))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
        lines.append(asp.fact("worn_on", p, p))
    lines.append(asp.fact("can_pair", "clang", "bell"))
    lines.append(asp.fact("can_pair", "trick", "basket"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {
        (place, act, prize)
        for place in SETTINGS
        for act in SETTINGS[place].affords
        for prize in PRIZES
        if (act == "clang" and prize == "bell") or (act == "trick" and prize == "basket")
    }
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print(" only in python:", sorted(py - asp_set))
    print(" only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about a clang, a trick, and a Twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--twist", choices=TWISTS)
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
    if args.action and args.prize:
        if not reasonableness_check(ACTIONS[args.action], PRIZES[args.prize], TWISTS[args.twist or "kind_turn"] if args.twist else TWISTS["kind_turn"]):
            raise StoryError("That action and prize do not make a sensible fable pair.")
    place = args.place or rng.choice(list(SETTINGS))
    action = args.action or rng.choice(list(SETTINGS[place].affords))
    if action not in SETTINGS[place].affords:
        raise StoryError("That place does not support the chosen action.")
    prize = args.prize or ("bell" if action == "clang" else "basket")
    twist = args.twist or rng.choice(list(TWISTS))
    hero_name = args.name or rng.choice(NAMES)
    friend_name = args.friend or rng.choice([n for n in NAMES if n != hero_name])
    return StoryParams(place=place, action=action, prize=prize, twist=twist, hero_name=hero_name, friend_name=friend_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], PRIZES[params.prize], TWISTS[params.twist], params.hero_name, params.friend_name)
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
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for place, action, prize in stories:
            print(f"  {place:8} {action:6} {prize}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.action} at {p.place} with {p.prize} ({p.twist})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
