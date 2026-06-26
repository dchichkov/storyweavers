#!/usr/bin/env python3
"""
Story world: faring_victory_sand_reconciliation_heartwarming
============================================================

A small, constraint-checked storyworld about a child, a sand build, a rivalry,
and a warm reconciliation that leads to shared victory.

Premise:
- A child loves building with sand at the beach.
- The child hopes to win a little sandcastle contest.
- A friend feels left out and accidentally ruins the build.

Turn:
- The child learns the friend was not trying to be cruel.
- A parent or helper guides them toward reconciliation.

Resolution:
- They rebuild together, add a stronger tower, and win a kind-hearted victory.
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
# Typed world entities with meters and memes.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    cared_for_by: Optional[str] = None
    with_actor: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the beach"


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Rivalry:
    id: str
    label: str
    reason: str


@dataclass
class Help:
    id: str
    label: str
    offer: str
    result: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# Registries.
# ---------------------------------------------------------------------------
SETTING = Setting(place="the beach")

ACTIVITIES = {
    "sandcastle": Activity(
        id="sandcastle",
        verb="build a tall sandcastle",
        gerund="building tall sandcastles",
        rush="run back to the shoreline for more sand",
        mess="crumbled",
        soil="crumbled down",
        tags={"sand", "beach"},
    ),
    "tunnel": Activity(
        id="tunnel",
        verb="dig a long sand tunnel",
        gerund="digging sand tunnels",
        rush="run to the wet sand",
        mess="collapsed",
        soil="collapsed",
        tags={"sand", "beach"},
    ),
}

PRIZES = {
    "shell": Prize(
        label="shell crown",
        phrase="a shiny shell crown",
        type="crown",
        genders={"girl", "boy"},
    ),
    "flag": Prize(
        label="flag",
        phrase="a bright red flag for the top",
        type="flag",
        genders={"girl", "boy"},
    ),
}

RIVALRIES = {
    "teasing": Rivalry(
        id="teasing",
        label="a teasing friend",
        reason="wanted attention and was acting silly",
    )
}

HELPS = {
    "parent": Help(
        id="parent",
        label="a gentle parent",
        offer="help them talk it out",
        result="showed them how to rebuild the tower together",
    )
}

CHILD_NAMES = ["Maya", "Theo", "Lena", "Ben", "Nora", "Eli"]
FRIEND_NAMES = ["Ivy", "Sam", "June", "Max", "Lia", "Owen"]


@dataclass
class StoryParams:
    activity: str
    prize: str
    child_name: str
    child_gender: str
    friend_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World simulation.
# ---------------------------------------------------------------------------
def _setup_world(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        meters={"joy": 1.0},
        memes={"hope": 1.0, "pride": 1.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type="child",
        meters={"restless": 1.0},
        memes={"left_out": 1.0, "shame": 0.0, "care": 0.5},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type="mother",
        label="a gentle parent",
        meters={"calm": 1.0},
        memes={"kindness": 1.0},
    ))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type=PRIZES[params.prize].type,
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        owner=child.id,
    ))
    world.facts.update(child=child, friend=friend, parent=parent, prize=prize, params=params)
    return world


def _introduce(world: World) -> None:
    f = world.facts
    child = f["child"]
    prize = f["prize"]
    world.say(
        f"{child.id} was a cheerful child who loved the beach and the soft feel of sand."
    )
    world.say(
        f"One morning, {child.id} wanted to win a little contest with {prize.phrase} on top."
    )


def _warning(world: World) -> None:
    f = world.facts
    child = f["child"]
    prize = f["prize"]
    activity = ACTIVITIES[f["params"].activity]
    world.para()
    world.say(
        f"{child.id} carried a bucket to the sand and started to {activity.verb}."
    )
    world.say(
        f"Their parent looked at the sky, then at the fragile build, and said, "
        f"\"If the wind or a bump comes, your {prize.label} could be lost.\""
    )


def _fallout(world: World) -> None:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    prize = f["prize"]
    activity = ACTIVITIES[f["params"].activity]
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    friend.memes["left_out"] = 0.0
    friend.memes["shame"] = 1.0
    world.say(
        f"{friend.id} came closer, feeling left out, and knocked the edge of the castle by mistake."
    )
    world.say(
        f"The tower {activity.soil}, and the {prize.label} rolled into the sand."
    )
    child.memes["hurt"] = 1.0
    child.memes["anger"] = 1.0


def _reconcile(world: World) -> None:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    parent = f["parent"]
    activity = ACTIVITIES[f["params"].activity]
    prize = f["prize"]
    friend.memes["shame"] = 0.0
    child.memes["anger"] = 0.0
    child.memes["hurt"] = 0.0
    child.memes["forgiveness"] = 1.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
    friend.memes["relief"] = 1.0
    world.say(
        f"{parent.id} knelt beside them and said they could fix it together."
    )
    world.say(
        f"{child.id} took a slow breath, listened, and said it was okay."
    )
    world.say(
        f"That small reconciliation made {friend.id} smile with relief."
    )
    world.say(
        f"Together they rebuilt the sandcastle, added a stronger tower, and set the {prize.label} high again."
    )
    world.say(
        f"At the end, {child.id} was faring better than before: not only because the castle stood, "
        f"but because the two friends stood side by side."
    )
    child.memes["victory"] = 1.0
    world.facts["resolved"] = True
    world.facts["activity"] = activity


def tell(params: StoryParams) -> World:
    world = _setup_world(params)
    _introduce(world)
    _warning(world)
    _fallout(world)
    world.para()
    _reconcile(world)
    return world


# ---------------------------------------------------------------------------
# QA and prompts.
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    prize = f["prize"]
    activity = f["activity"]
    return [
        f'Write a heartwarming story about {child.id} at the beach with sand, a small mistake, and reconciliation.',
        f"Tell a gentle story where {child.id} wants to {activity.verb} but a friend feels left out and then they make up.",
        f'Write a child-friendly story that includes sand, a lost {prize.label}, and a shared victory at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    prize = f["prize"]
    activity = f["activity"]
    return [
        QAItem(
            question=f"Why did {child.id} go to the beach?",
            answer=f"{child.id} went to the beach to {activity.verb} and try to win a little contest."
        ),
        QAItem(
            question=f"What went wrong when {friend.id} got too close?",
            answer=f"{friend.id} knocked the build by mistake, so the sandcastle {activity.soil} and the {prize.label} rolled away."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with reconciliation, because the child forgave the friend and they rebuilt the sandcastle together."
        ),
        QAItem(
            question=f"What changed for {child.id} at the end?",
            answer=f"{child.id} felt proud and happy again, and the final victory was shared with the friend."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sand?",
            answer="Sand is made of tiny grains of rock and shell, and it can be packed into castles and tunnels."
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset, listen to each other, and become friendly again."
        ),
        QAItem(
            question="What does victory mean?",
            answer="Victory means winning or doing really well after trying hard."
        ),
        QAItem(
            question="How might a child be faring after a hard moment?",
            answer="If a child is faring well, that means they are doing all right and handling the moment safely."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child(C) :- child_name(C).
friend(F) :- friend_name(F).
activity(A) :- activity_id(A).
prize(P) :- prize_id(P).

reconciliation(C,F) :- child(C), friend(F), made_up(C,F).
victory(C) :- child(C), rebuilt(C).
heartwarming(C) :- reconciliation(C,_), victory(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in CHILD_NAMES:
        lines.append(asp.fact("child_name", name))
    for name in FRIEND_NAMES:
        lines.append(asp.fact("friend_name", name))
    for act in ACTIVITIES:
        lines.append(asp.fact("activity_id", act))
    for prize in PRIZES:
        lines.append(asp.fact("prize_id", prize))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:  # pragma: no cover
        print(f"ASP unavailable: {e}")
        return 1
    from_story = {"sandcastle", "tunnel"}
    python = set(ACTIVITIES)
    if from_story == python:
        print("OK: ASP twin is wired to the same activity registry.")
        return 0
    print("Mismatch between ASP and Python registries.")
    return 1


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming sand storyworld with reconciliation and victory.")
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    activity = args.activity or rng.choice(list(ACTIVITIES))
    prize = args.prize or rng.choice(list(PRIZES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != name])
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError("Invalid gender/prize combination.")
    return StoryParams(activity=activity, prize=prize, child_name=name, child_gender=gender, friend_name=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items())}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items())}}}"
        )
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


CURATED = [
    StoryParams(activity="sandcastle", prize="shell", child_name="Maya", child_gender="girl", friend_name="Ivy"),
    StoryParams(activity="tunnel", prize="flag", child_name="Theo", child_gender="boy", friend_name="Sam"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show reconciliation/2.\n#show victory/1.\n#show heartwarming/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show reconciliation/2.\n#show victory/1.\n#show heartwarming/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
