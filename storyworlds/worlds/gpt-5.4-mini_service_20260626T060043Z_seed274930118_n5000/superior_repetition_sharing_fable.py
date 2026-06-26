#!/usr/bin/env python3
"""
A small fable-style story world about repetition, sharing, and a superior result.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "hare", "crow", "mouse", "badger", "squirrel"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    repeat: str
    share: str
    result: str
    challenge: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str = "hands"
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"fox", "hare", "crow", "mouse", "badger", "squirrel"})


@dataclass
class Tool:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.zone = set(self.zone)
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ("messy",):
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.entities.values():
                if item.caretaker != actor.id and item.owner != actor.id:
                    continue
                if item.plural:
                    continue
                sig = ("spill", actor.id, item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["ruined"] += 1
                out.append(f"{actor.id}'s work on the thing turned clumsy.")
    return out


CAUSAL_RULES = [
    _r_spill,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_result(world: World, actor: Entity, activity: Activity) -> bool:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.facts["prize"]
    return prize.meters["finished"] >= THRESHOLD and sim.facts.get("shared", False)


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    actor.meters["practice"] += 1
    actor.memes["joy"] += 1
    world.zone = {activity.keyword}
    if actor.meters["practice"] >= 2:
        actor.meters["skill"] += 1
    if narrate:
        world.say(f"{actor.id} kept at the task again and again, and the little motions began to fit together.")
    propagate(world, narrate=narrate)


def ask_for_help(world: World, actor: Entity, helper: Entity, activity: Activity) -> None:
    actor.memes["need"] += 1
    world.say(
        f"{actor.id} saw that trying it alone was slow, so {actor.pronoun('possessive')} "
        f"voice grew small. {helper.id} listened carefully."
    )


def share_materials(world: World, actor: Entity, helper: Entity, prize: Entity) -> None:
    helper.meters["shared"] += 1
    actor.meters["shared"] += 1
    prize.meters["finished"] += 1
    world.facts["shared"] = True
    world.say(
        f"{helper.id} shared a few good pieces, and {actor.id} shared the rest. "
        f"Together they made the {prize.label} stronger and neater."
    )


def conclude(world: World, actor: Entity, helper: Entity, activity: Activity, prize: Entity) -> None:
    prize.meters["finished"] += 1
    actor.memes["pride"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"At last, after the repeated tries and the shared pieces, the {prize.label} was finished. "
        f"It looked superior to anything {actor.id} could have made alone."
    )
    world.say(
        f"{actor.id} smiled at {helper.id}. The little lesson was clear: repetition taught the hands, "
        f"and sharing helped the work become better than before."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str, hero_type: str, helper_name: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, owner=hero.id, caretaker=hero.id,
                             plural=prize_cfg.plural))
    world.facts.update(hero=hero, helper=helper, activity=activity, prize=prize, setting=setting)

    world.say(
        f"{hero.id} was a small {hero.type} who loved making things with careful paws."
    )
    world.say(
        f"One day {hero.id} wanted to {activity.verb} {prize.phrase}, because {activity.keyword} work "
        f"looked simple only from far away."
    )
    world.say(
        f"But the first try was crooked, and the second try was not much better."
    )

    world.para()
    _do_activity(world, hero, activity, narrate=True)
    _do_activity(world, hero, activity, narrate=True)
    ask_for_help(world, hero, helper, activity)
    share_materials(world, hero, helper, prize)
    conclude(world, hero, helper, activity, prize)
    return world


SETTINGS = {
    "meadow": Setting(place="the meadow", affords={"weave", "mix"}),
    "cottage": Setting(place="the cottage", affords={"weave", "mix"}),
    "barn": Setting(place="the barn", affords={"weave"}),
}

ACTIVITIES = {
    "weave": Activity(
        id="weave",
        verb="weave",
        gerund="weaving",
        repeat="weaving again and again",
        share="share reeds",
        result="a sturdy nest",
        challenge="the strips kept slipping apart",
        keyword="reeds",
        tags={"reeds", "nest", "share", "repetition"},
    ),
    "mix": Activity(
        id="mix",
        verb="mix",
        gerund="mixing",
        repeat="mixing the bowl many times",
        share="share honey",
        result="a sweet little cake",
        challenge="the batter stayed lumpy",
        keyword="honey",
        tags={"honey", "cake", "share", "repetition"},
    ),
}

PRIZES = {
    "nest": Prize(label="nest", phrase="a snug nest", type="nest"),
    "cake": Prize(label="cake", phrase="a small cake", type="cake"),
}

ANIMALS = ["fox", "hare", "crow", "mouse", "badger", "squirrel"]
NAMES = {
    "fox": ["Fenn", "Ruby", "Sable"],
    "hare": ["Pip", "Milo", "Tansy"],
    "crow": ["Keen", "Onyx", "Mara"],
    "mouse": ["Nip", "Lulu", "Tiko"],
    "badger": ["Bran", "Moss", "Hugh"],
    "squirrel": ["Twig", "Nori", "Penny"],
}


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    kind: str
    helper_name: str
    helper_kind: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about repetition, sharing, and a superior result.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=ANIMALS)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-kind", choices=ANIMALS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, a, pr) for p, s in SETTINGS.items() for a in s.affords for pr in PRIZES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    kind = args.kind or rng.choice(ANIMALS)
    helper_kind = args.helper_kind or rng.choice([a for a in ANIMALS if a != kind])
    name = args.name or rng.choice(NAMES[kind])
    helper_name = args.helper_name or rng.choice(NAMES[helper_kind])
    return StoryParams(place=place, activity=activity, prize=prize, name=name, kind=kind,
                       helper_name=helper_name, helper_kind=helper_kind)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.kind, params.helper_name, params.helper_kind)
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
    return [
        f'Write a fable for young children about {f["hero"].id} learning that repetition helps with {f["activity"].keyword}.',
        f"Tell a short story where {f['hero'].id} asks {f['helper'].id} to share, and the result becomes superior.",
        f'Write a gentle animal story using the word "superior" and ending with a lesson about sharing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, activity, prize = f["hero"], f["helper"], f["activity"], f["prize"]
    return [
        QAItem(
            question=f"What did {hero.id} keep doing again and again?",
            answer=f"{hero.id} kept {activity.gerund} so the little motions could become steady and skilled.",
        ),
        QAItem(
            question=f"Why did {helper.id} help {hero.id} with the {prize.label}?",
            answer=f"{helper.id} helped because sharing the good pieces made the work stronger and neater.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The {prize.label} became finished and superior, and {hero.id} learned that repetition and sharing can make work better.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing something again and again, which can help a skill grow stronger.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means giving some of what you have to someone else so you can help each other.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place,Act,Prize) :- affords(Place,Act), prize(Prize), activity(Act).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
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
    print("MISMATCH:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="meadow", activity="weave", prize="nest", name="Fenn", kind="fox",
                helper_name="Pip", helper_kind="hare"),
    StoryParams(place="cottage", activity="mix", prize="cake", name="Twig", kind="squirrel",
                helper_name="Mara", helper_kind="crow"),
]


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for x in combos:
            print(" ", x)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
