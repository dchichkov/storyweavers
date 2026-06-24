#!/usr/bin/env python3
"""
A tall-tale style storyworld about a deep puddle, a stubborn barrier, a
magnetic kind of enthrallment, and a curious child who remembers a flashback
that changes the day.

This script is self-contained and follows the storyworld contract:
- typed physical meters and emotional memes
- a reasonableness gate in Python
- an inline ASP twin
- story, prompts, story QA, world QA, trace, JSON, verify, and ASP modes
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
    protective: bool = False
    plural: bool = False
    barrier: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the deep puddle"
    affords: set[str] = field(default_factory=lambda: {"splash", "wade"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class BarrierDef:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    guards: set[str]
    covers: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    activity: str
    prize: str
    barrier: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def note(self, text: str) -> None:
        self.trace.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        return w


SETTINGS = {"deep_puddle": Setting()}

ACTIVITIES = {
    "splash": Activity(
        id="splash",
        verb="splash in the deep puddle",
        gerund="splashing in the deep puddle",
        rush="dash into the deep puddle",
        mess="wet",
        soil="soaking wet",
        zone={"feet", "legs", "torso"},
        keyword="deep puddle",
        tags={"puddle", "wet", "curiosity"},
    )
}

PRIZES = {
    "chiffonier": Prize(
        label="chiffonier",
        phrase="a shiny little chiffonier with brass pulls",
        type="chiffonier",
        region="torso",
    )
}

BARRIERS = {
    "fence": BarrierDef(
        id="fence",
        label="a fence board",
        phrase="a stubborn fence board",
        prep="lift the board aside and peek through",
        tail="set the board back where it belonged",
        guards={"wet"},
        covers={"torso", "legs"},
        tags={"barrier"},
    ),
}

NAMES = ["Mabel", "Nora", "Ivy", "Ruby", "Willa", "Hazel", "Clara", "Otis", "Elmer", "Bea"]
TAGS = ["curious", "bold", "lively", "cheerful", "stubborn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize_id, prize in PRIZES.items():
                a = ACTIVITIES[act]
                if prize.region in a.zone:
                    combos.append((place, act, prize_id))
    return combos


def reasonableness_gate(activity: Activity, prize: Prize, barrier: BarrierDef) -> bool:
    return prize.region in activity.zone and "wet" in barrier.guards and prize.region in barrier.covers


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} reaches the {prize.region}, but nothing in the barrier "
        f"catalog can honestly protect a {prize.label} there.)"
    )


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS["deep_puddle"])
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"wet": 0.0},
        memes={"curiosity": 0.0, "joy": 0.0, "conflict": 0.0, "enthrall": 0.0},
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    prize = world.add(Entity(
        id=params.prize,
        type=PRIZES[params.prize].type,
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        owner=hero.id,
        caretaker=parent.id,
        worn_by=hero.id,
        meters={"wet": 0.0, "dirty": 0.0},
    ))
    barrier = world.add(Entity(
        id="barrier",
        type="thing",
        label=BARRIERS[params.barrier].label,
        phrase=BARRIERS[params.barrier].phrase,
        barrier=True,
        protective=True,
        tags=set(BARRIERS[params.barrier].tags),
        meters={},
        memes={},
    ))
    world.facts.update(hero=hero, parent=parent, prize=prize, barrier=barrier, activity=ACTIVITIES[params.activity])
    return world


def simulate(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    prize: Entity = f["prize"]
    barrier: Entity = f["barrier"]
    act: Activity = f["activity"]

    world.say(f"{hero.id} was a little {hero.type} with a curious nose for trouble and a bright eye for wonder.")
    world.say(
        f"{hero.id} loved the {act.keyword}, for the water in the deep puddle glittered like a mirror "
        f"laid down by a sky-hungry giant."
    )
    world.say(
        f"One day {hero.id} noticed {hero.pronoun('possessive')} {prize.label}, and it shone so proudly "
        f"that even the mud seemed to tip its hat."
    )
    world.say(
        f"Then came a flashback: {hero.id} remembered a smaller day when a slipper sank in wet ground "
        f"and the whole house had to hunt for it with a lantern."
    )
    hero.memes["curiosity"] += 1.0
    hero.memes["enthrall"] += 1.0
    world.say(
        f"That memory did not scare {hero.id}; it enthralled {hero.pronoun('object')}, the way a fiddle tune "
        f"can catch a rabbit by the ears."
    )
    world.say(
        f"{hero.id} wanted to {act.verb}, but {parent.label} raised {hero.pronoun('possessive')} hand and pointed "
        f"to the {barrier.label} at the edge of the water."
    )
    world.say(
        f'"That puddle is deep enough to swallow a boot," {parent.label} warned. "If you go barreling in, '
        f"your {prize.label} will come out {act.soil}."'
    )
    hero.memes["conflict"] += 1.0
    world.say(f"{hero.id} almost rushed ahead anyway, because curiosity can tug harder than a kite string in a storm.")
    world.say(
        f"Then the {barrier.label} gave a squeak in the wind, and {hero.id} had an idea as quick as a minnowskip."
    )
    if not reasonableness_gate(act, prize, BARRIERS[world.facts["barrier"].id]):
        raise StoryError(explain_rejection(act, prize))
    hero.memes["joy"] += 1.0
    hero.memes["conflict"] = 0.0
    prize.meters["wet"] = 0.0
    world.say(
        f"{hero.id} and {parent.label} used the {barrier.label} as a stepping rail, never a road, and chose the safer way."
    )
    world.say(
        f"They set the {barrier.label} back where it belonged, then {hero.id} got to {act.verb} without ruining "
        f"{hero.pronoun('possessive')} {prize.label}."
    )
    world.say(
        f"By sunset, the deep puddle still sparkled, the {prize.label} still glowed, and {hero.id} laughed like a "
        f"bell in a barn wind."
    )


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
fix_ok(B, A, P) :- barrier(B), prize_at_risk(A, P), guards(B, wet), covers(B, R), worn_on(P, R).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), fix_ok(_, A, P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for bid, b in BARRIERS.items():
        lines.append(asp.fact("barrier", bid))
        for g in sorted(b.guards):
            lines.append(asp.fact("guards", bid, g))
        for c in sorted(b.covers):
            lines.append(asp.fact("covers", bid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a tall tale for a child about a deep puddle, a barrier, and a curious turn of mind.',
        f"Tell a story where {f['hero'].id} wants to {f['activity'].verb} but must keep {f['prize'].label} safe.",
        'Make the story include a flashback and end with a clever safer choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at the deep puddle?",
            answer=f"{hero.id} wanted to {act.verb}. The water looked dazzling, and curiosity kept pulling {hero.pronoun('object')} closer.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about {hero.pronoun('possessive')} {prize.label}?",
            answer=f"{parent.label} worried because a deep puddle could make the {prize.label} {act.soil}, and then it would need cleaning.",
        ),
        QAItem(
            question=f"What helped {hero.id} choose a safer way?",
            answer=f"The {f['barrier'].label} helped by giving {hero.id} a careful place to pause, think, and keep the {prize.label} dry.",
        ),
        QAItem(
            question=f"What did the flashback remind {hero.id} of?",
            answer=f"It reminded {hero.id} of a smaller day when something sank in wet ground and the house had to search for it with a lantern.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a barrier?",
            answer="A barrier is something that stands in the way or helps keep people from going where they should not go.",
        ),
        QAItem(
            question="What does it mean to enthrall someone?",
            answer="To enthrall someone means to catch their attention so strongly that they can hardly think about anything else.",
        ),
        QAItem(
            question="What is a chiffonier?",
            answer="A chiffonier is a tall piece of furniture with drawers, often used for keeping clothes or small treasures.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and find out more.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes} tags={sorted(e.tags)}")
    out.append(f"fired={sorted(world.fired)}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld set in a deep puddle.")
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--barrier", choices=BARRIERS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.activity and args.prize:
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not reasonableness_gate(act, prize, BARRIERS[args.barrier or "fence"]):
            raise StoryError(explain_rejection(act, prize))
    activity = args.activity or "splash"
    prize = args.prize or "chiffonier"
    barrier = args.barrier or "fence"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(activity=activity, prize=prize, barrier=barrier, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()

    if args.all:
        params_list = [
            StoryParams(activity="splash", prize="chiffonier", barrier="fence", name="Mabel", gender="girl", parent="mother")
        ]
    else:
        params_list = []
        i = 0
        while len(params_list) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
                p.seed = seed
            except StoryError as e:
                print(e)
                return
            params_list.append(p)

    for p in params_list:
        s = generate(p)
        if s.story in seen:
            continue
        seen.add(s.story)
        samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(s, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
