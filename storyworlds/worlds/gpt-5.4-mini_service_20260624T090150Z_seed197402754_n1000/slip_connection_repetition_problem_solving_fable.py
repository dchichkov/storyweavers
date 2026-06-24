#!/usr/bin/env python3
"""
storyworlds/worlds/slip_connection_repetition_problem_solving_fable.py
======================================================================

A small fable-style story world about a slippery crossing, a broken
connection, and the patient repetition that solves it.

Initial tale:
---
A little fox wanted to carry berries to a sleepy hedgehog across a stream.
But the stones near the water were slick, and every time the fox hurried,
its paws slipped. The fox tried again and again, but the gap between the
banks still broke the connection.

A wise turtle watched and said, "Do not rush what must be joined. Tie
the reeds together first, then step where the stones are dry." So the fox
and the hedgehog repeated the work carefully: tie, test, step, and tie
again. At last they made a small reed bridge. The berries crossed safely,
and the friends learned that steady work can mend what haste breaks.
"""

from __future__ import annotations

import argparse
import copy
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"fox", "boy", "father", "man", "turtle"}
        female = {"girl", "mother", "woman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the riverbank"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    slip_kind: str
    problem: str
    repeated_step: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str]
    covers: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []
        self.attempts: int = 0
        self.connection_fixed: bool = False

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.attempts = self.attempts
        clone.connection_fixed = self.connection_fixed
        return clone


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("slip", 0.0) < THRESHOLD:
            continue
        sig = ("slip", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["frustration"] = actor.memes.get("frustration", 0.0) + 1
        out.append(f"{actor.id} slipped on the slick stones.")
    return out


def _r_connection(world: World) -> list[str]:
    out: list[str] = []
    bridge = world.entities.get("bridge")
    if not bridge:
        return out
    if bridge.meters.get("connected", 0.0) >= THRESHOLD and not world.connection_fixed:
        world.connection_fixed = True
        out.append("The little bridge finally held the two banks together.")
    return out


CAUSAL_RULES = [
    _r_slip,
    _r_connection,
]


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
    place: str
    hero: str
    helper: str
    prize: str
    seed: Optional[int] = None


SETTINGS = {
    "riverbank": Setting(place="the riverbank", affords={"crossing"}),
    "orchard": Setting(place="the orchard", affords={"crossing"}),
    "meadow": Setting(place="the meadow stream", affords={"crossing"}),
}

ACTIVITIES = {
    "crossing": Activity(
        id="crossing",
        verb="cross the stream",
        gerund="crossing the stream",
        rush="rush across the stones",
        slip_kind="slip",
        problem="the stones were slick",
        repeated_step="tie, test, step, and tie again",
        keyword="slip",
        tags={"slip", "connection", "repetition", "problem_solving"},
    )
}

PRIZES = {
    "berries": Prize(
        label="berries",
        phrase="a basket of bright berries",
        type="berries",
        region="banks",
        plural=True,
    ),
    "bread": Prize(
        label="bread",
        phrase="a warm loaf of bread",
        type="bread",
        region="banks",
    ),
}

GEAR = [
    Gear(
        id="reeds",
        label="reeds",
        prep="tie the reeds together first",
        tail="the friends repeated the work until the reeds held tight",
        helps={"connection"},
    ),
    Gear(
        id="stones",
        label="dry stepping stones",
        prep="set the dry stepping stones in a careful line",
        tail="each step became safer",
        helps={"slip"},
        covers={"feet"},
    ),
]

HEROES = ["Fox", "Mole", "Squirrel", "Hare"]
HELPERS = ["Turtle", "Badger", "Heron", "Otter"]
TRAITS = ["swift", "curious", "proud", "patient", "small", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize in PRIZES:
                combos.append((place, act_id, prize))
    return combos


def _moral() -> str:
    return "Steady paws make a stronger path than hurried ones."


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, helper_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="fox" if hero_name == "Fox" else "animal"))
    helper = world.add(Entity(id=helper_name, kind="character", type="turtle" if helper_name == "Turtle" else "animal"))
    bridge = world.add(Entity(id="bridge", type="bridge", label="a reed bridge"))

    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        plural=prize_cfg.plural,
    ))

    world.say(f"{hero.id} lived near {setting.place} and liked to carry {prize.label} across the water.")
    world.say(f"But {activity.problem}, so each hurried step risked a slip.")
    world.say(f"{hero.id} wanted to {activity.verb}, even though the way was narrow and wet.")

    world.para()
    world.say(f"{hero.id} tried once.")
    hero.meters["slip"] = 1
    world.attempts += 1
    propagate(world)
    world.say(f"{hero.id} tried again.")
    world.attempts += 1
    hero.meters["slip"] = 2
    propagate(world)
    world.say(f"{hero.id} still could not make the connection.")

    world.para()
    world.say(f"Then {helper.id} watched, calm and wise, and said, \"Do not rush what must be joined.\"")
    world.say(f'"{activity.repeated_step}," said {helper.id}.')
    gear = GEAR[0]
    world.say(f"Together they chose to {gear.prep}.")
    bridge.meters["connected"] = 1
    world.connection_fixed = True
    propagate(world)
    world.say(f"{gear.tail}.")
    world.say(f"At last, {hero.id} carried {prize.phrase} across without a slip.")
    world.say(_moral())

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        activity=activity,
        gear=gear,
        attempts=world.attempts,
        fixed=world.connection_fixed,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short fable for a young child about "{act.keyword}" and a broken connection that is solved by patient repetition.',
        f"Tell a gentle animal story where {hero.id} wants to {act.verb} but needs help from {helper.id} to keep {prize.label} safe.",
        f'Write a simple fable that repeats the idea of "try, think, and try again" until the connection is fixed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prize = f["prize"]
    act = f["activity"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do near {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb} while carrying {prize.phrase}.",
        ),
        QAItem(
            question=f"Why did {hero.id} keep having trouble?",
            answer=f"{act.problem}, so {hero.id} slipped when the steps got hurried.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} fix the problem?",
            answer=f"They used {gear.label} and repeated the careful work until the connection held.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The crossing became safe, the bridge connected the banks, and {hero.id} carried the berries across without slipping.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to repeat something?",
            answer="To repeat something means to do it again and again.",
        ),
        QAItem(
            question="What is a connection?",
            answer="A connection is a joining together of two things so they can work or travel between them.",
        ),
        QAItem(
            question="Why is slipping dangerous on wet stones?",
            answer="Wet stones can be slick, so feet may slide and lose balance.",
        ),
        QAItem(
            question="Why is problem solving useful?",
            answer="Problem solving helps you find a smart way to fix trouble instead of giving up.",
        ),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  attempts={world.attempts}")
    lines.append(f"  fixed={world.connection_fixed}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="riverbank", hero="Fox", helper="Turtle", prize="berries"),
    StoryParams(place="orchard", hero="Squirrel", helper="Badger", prize="bread"),
    StoryParams(place="meadow", hero="Hare", helper="Heron", prize="berries"),
]


ASP_RULES = r"""
% A story is valid when the place affords crossing.
valid_story(Place, Hero, Helper, Prize) :- affords(Place, crossing), hero(Hero), helper(Helper), prize(Prize).

% The tale centers on slip when the activity is crossing the stream.
problem(crossing, slip).
connection_needed(crossing).

% Repetition is the remedy when the connection is broken and a helper can assist.
solution(crossing, repetition) :- connection_needed(crossing), helper(_).

valid_combo(Place, crossing, Prize) :- affords(Place, crossing), prize(Prize).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for prid in PRIZES:
        lines.append(asp.fact("prize", prid))
    for h in HEROES:
        lines.append(asp.fact("hero", h.lower()))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.lower()))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    clingo_set = set(asp.atoms(model, "valid_combo"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about slip, connection, repetition, and problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    hero = args.name or rng.choice(HEROES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, hero=hero, helper=helper, prize=prize)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES["crossing"], PRIZES[params.prize], params.hero, params.helper)
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
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_combo/3."))
        combos = sorted(set(asp.atoms(model, "valid_combo")))
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
            header = f"### {p.hero} at {p.place} with {p.helper} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
