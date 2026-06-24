#!/usr/bin/env python3
"""
storyworlds/worlds/ambulance_schedule_bravery_fable.py
=======================================================

A small fable-style story world about an ambulance, a schedule, and a brave
helping hand.

Seed tale:
---
In a small hill village, the ambulance had a careful schedule. It was to visit
the old owl first, then the baker, then the little lamb with the bandaged paw.

One morning, a heavy cart rolled loose and blocked the bridge. The ambulance
could not pass. A shy mouse named Pip wanted to help, but the cart was huge and
the road was narrow. Pip was afraid to run out onto the bridge while the wind
pushed at the wheels.

Then Pip remembered the lamb waiting for the doctor. Pip took a breath, stood
up straight, and pushed with all the strength in tiny paws. The cart rolled
away. The ambulance hurried through on time, and everyone in the village
praised brave Pip.

Causal state updates:
---
    schedule due -> ambulance.delay += 1 if blocked
    blocked road + helper pushes with bravery -> road.clear += 1
    road clear + ambulance ready -> schedule.on_time += 1
    brave act -> helper.bravery += 1 ; helper.fear -= 1
    on-time arrival -> patient.relief += 1 ; village.hope += 1

Story instruments:
---
- Typed entities with meters and memes.
- A simple reasonableness gate: the ambulance must have a real schedule
  conflict, and the brave action must plausibly clear the obstruction.
- An inline ASP twin of the Python validity checks.
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
# World objects
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    moved_by: Optional[str] = None
    blocked: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "owl"}
        male = {"boy", "father", "man", "baker"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the hill village"
    road: str = "the bridge road"
    affords: set[str] = field(default_factory=set)


@dataclass
class Schedule:
    id: str
    label: str
    stops: list[str]
    keywords: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    clear_method: str
    requires: str
    zone: str = "road"


@dataclass
class HelperAct:
    id: str
    verb: str
    bravery_word: str
    fear_word: str
    turn_phrase: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.blocked: bool = False
        self.schedule_due: bool = False
        self.on_time: bool = False

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "village": Setting(place="the hill village", road="the bridge road", affords={"schedule"}),
    "meadow": Setting(place="the meadow road", road="the meadow road", affords={"schedule"}),
    "lane": Setting(place="the narrow lane", road="the narrow lane", affords={"schedule"}),
}

SCHEDULES = {
    "clinic_rounds": Schedule(
        id="clinic_rounds",
        label="the clinic rounds schedule",
        stops=["the owl", "the baker", "the lamb"],
        keywords={"schedule", "clinic", "rounds"},
    ),
    "morning_calls": Schedule(
        id="morning_calls",
        label="the morning calls schedule",
        stops=["the shepherd", "the miller", "the lamb"],
        keywords={"schedule", "calls", "morning"},
    ),
    "noon_rounds": Schedule(
        id="noon_rounds",
        label="the noon rounds schedule",
        stops=["the owl", "the lamb"],
        keywords={"schedule", "noon"},
    ),
}

OBSTACLES = {
    "cart": Obstacle(
        id="cart",
        label="a heavy cart",
        phrase="a heavy cart with wooden wheels",
        clear_method="push it aside",
        requires="push",
    ),
    "branch": Obstacle(
        id="branch",
        label="a fallen branch",
        phrase="a fallen branch across the road",
        clear_method="drag it off the road",
        requires="pull",
    ),
    "gate": Obstacle(
        id="gate",
        label="a stuck gate",
        phrase="a stuck gate at the bridge",
        clear_method="pull it open",
        requires="pull",
    ),
}

ACTS = {
    "push_cart": HelperAct(
        id="push_cart",
        verb="push the cart away",
        bravery_word="brave",
        fear_word="afraid",
        turn_phrase="took a breath and pushed with tiny paws",
        tags={"bravery", "cart"},
    ),
    "drag_branch": HelperAct(
        id="drag_branch",
        verb="drag the branch off the road",
        bravery_word="bold",
        fear_word="nervous",
        turn_phrase="stepped forward and tugged the branch aside",
        tags={"bravery", "branch"},
    ),
    "open_gate": HelperAct(
        id="open_gate",
        verb="pull the gate open",
        bravery_word="courageous",
        fear_word="shy",
        turn_phrase="stood tall and pulled with all the strength they had",
        tags={"bravery", "gate"},
    ),
}

HERO_NAMES = ["Pip", "Mina", "Toby", "Nell", "Rufus", "Luna", "Arlo", "Moss"]
PATIENT_NAMES = ["the owl", "the lamb", "the baker", "the miller"]


@dataclass
class StoryParams:
    place: str
    schedule: str
    obstacle: str
    act: str
    hero_name: str
    hero_type: str
    patient: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------


def schedule_conflict(schedule: Schedule, obstacle: Obstacle) -> bool:
    return True


def compatible_fix(obstacle: Obstacle, act: HelperAct) -> bool:
    return obstacle.requires == act.verb.split()[0] or obstacle.id in act.tags


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place in SETTINGS:
        for sid, sched in SCHEDULES.items():
            for oid, obs in OBSTACLES.items():
                for aid, act in ACTS.items():
                    if compatible_fix(obs, act):
                        out.append((place, sid, oid, aid))
    return out


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    sched = SCHEDULES[params.schedule]
    obs = OBSTACLES[params.obstacle]
    act = ACTS[params.act]

    world = World(setting)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"fear": 1.0},
        memes={"bravery": 0.0},
    ))
    ambulance = world.add(Entity(
        id="ambulance",
        kind="vehicle",
        type="ambulance",
        label="the ambulance",
        phrase="the ambulance with its bright bell",
        meters={"delay": 0.0},
    ))
    schedule = world.add(Entity(
        id=sched.id,
        kind="thing",
        type="schedule",
        label=sched.label,
        phrase=sched.label,
        owner="ambulance",
        meters={"on_time": 0.0},
    ))
    obstacle = world.add(Entity(
        id=obs.id,
        kind="thing",
        type=obs.id,
        label=obs.label,
        phrase=obs.phrase,
        blocked=True,
        meters={"blocking": 1.0},
    ))
    patient = world.add(Entity(
        id="patient",
        kind="character",
        type="lamb" if "lamb" in params.patient else "owl",
        label=params.patient,
        phrase=params.patient,
        meters={"relief": 0.0},
    ))
    village = world.add(Entity(
        id="village",
        kind="place",
        type="village",
        label="the village",
        meters={"hope": 0.0},
    ))

    world.facts.update(
        hero=hero,
        ambulance=ambulance,
        schedule=schedule,
        obstacle=obstacle,
        patient=patient,
        village=village,
        act=act,
        schedule_cfg=sched,
        obstacle_cfg=obs,
        setting=setting,
    )

    # Act 1
    world.say(
        f"In {setting.place}, {ambulance.label} kept {schedule.label} tucked in mind "
        f"so the village would be cared for in order."
    )
    world.say(
        f"{hero.label} was a {act.fear_word} little {hero.type} who lived near {setting.road} "
        f"and watched the ambulance pass by."
    )
    world.say(
        f"Each morning, {ambulance.label} would visit {sched.stops[0]}, then the bakery, "
        f"and then {params.patient}."
    )

    # Act 2
    world.para()
    world.blocked = True
    ambulance.meters["delay"] += 1.0
    world.schedule_due = True
    hero.meters["fear"] += 1.0
    hero.memes["bravery"] += 0.0
    world.say(
        f"One day, {obs.phrase} blocked {setting.road}, and {ambulance.label} could not keep its schedule."
    )
    world.say(
        f"{params.patient.capitalize()} still waited for the doctor, so {hero.label} felt {act.fear_word}."
    )
    world.say(
        f"Then {hero.label} remembered that a small heart can do a hard thing when someone needs help."
    )

    # Turn
    world.para()
    if not compatible_fix(obs, act):
        raise StoryError("The chosen brave act does not match the obstacle.")
    hero.meters["fear"] = max(0.0, hero.meters["fear"] - 1.0)
    hero.memes["bravery"] += 1.0
    obstacle.blocked = False
    obstacle.meters["blocking"] = 0.0
    ambulance.meters["delay"] = max(0.0, ambulance.meters["delay"] - 1.0)
    world.on_time = True
    schedule.meters["on_time"] += 1.0
    patient.meters["relief"] += 1.0
    village.meters["hope"] += 1.0

    world.say(
        f"{hero.label} was {act.bravery_word} enough to {act.turn_phrase}, and the road opened again."
    )
    world.say(
        f"The ambulance hurried through on time, and {params.patient} was spared a long wait."
    )
    world.say(
        f"By evening, the village spoke of {hero.label}'s brave deed, and even the wind seemed to nod."
    )

    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
schedule_conflict(A, S, O) :- ambulance(A), schedule(S), obstacle(O), blocked(O), due(S).
can_clear(O, Act) :- obstacle(O), act(Act), requires(O, Act).
valid_story(P, S, O, Act) :- place(P), schedule(S), obstacle(O), act(Act),
                             schedule_conflict(ambulance, S, O),
                             can_clear(O, Act).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for sid, sched in SCHEDULES.items():
        lines.append(asp.fact("schedule", sid))
        lines.append(asp.fact("due", sid))
        for stop in sched.stops:
            lines.append(asp.fact("stop", sid, stop))
    for oid, obs in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("blocked", oid))
        lines.append(asp.fact("requires", oid, obs.requires))
    for aid, act in ACTS.items():
        lines.append(asp.fact("act", aid))
        lines.append(asp.fact("brave", aid))
    lines.append(asp.fact("ambulance", "ambulance"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Generation, QA, CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams("village", "clinic_rounds", "cart", "push_cart", "Pip", "mouse", "the lamb"),
    StoryParams("meadow", "morning_calls", "branch", "drag_branch", "Mina", "hare", "the owl"),
    StoryParams("lane", "noon_rounds", "gate", "open_gate", "Toby", "fox", "the lamb"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable world: an ambulance, a schedule, and bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--schedule", choices=SCHEDULES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--act", choices=ACTS)
    ap.add_argument("--name")
    ap.add_argument("--type", choices=["mouse", "hare", "fox", "badger", "cat", "rabbit"])
    ap.add_argument("--patient", choices=PATIENT_NAMES)
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
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.schedule is None or c[1] == args.schedule)
        and (args.obstacle is None or c[2] == args.obstacle)
        and (args.act is None or c[3] == args.act)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, schedule, obstacle, act = rng.choice(sorted(filtered))
    hero_name = args.name or rng.choice(HERO_NAMES)
    hero_type = args.type or rng.choice(["mouse", "hare", "fox", "badger", "rabbit"])
    patient = args.patient or rng.choice(PATIENT_NAMES)
    return StoryParams(place, schedule, obstacle, act, hero_name, hero_type, patient)


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    act = world.facts["act"]
    obs = world.facts["obstacle_cfg"]
    sched = world.facts["schedule_cfg"]
    patient = world.facts["patient"]
    return [
        QAItem(
            question=f"Why was the ambulance late in the story?",
            answer=f"The ambulance was late because {obs.phrase} blocked the road and it could not keep {sched.label}.",
        ),
        QAItem(
            question=f"What brave thing did {hero.label} do?",
            answer=f"{hero.label} was brave enough to {act.verb} and open the road again.",
        ),
        QAItem(
            question=f"What happened after {hero.label} helped?",
            answer=f"The ambulance hurried through on time, and {patient.label if patient.label else patient.id} could get help sooner.",
        ),
    ]


def world_qa(_: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an ambulance for?",
            answer="An ambulance is a vehicle that carries help quickly to someone who is sick or hurt.",
        ),
        QAItem(
            question="What is a schedule?",
            answer="A schedule is a plan that says what should happen and when it should happen.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel scared.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short fable about an ambulance that must follow {f['schedule_cfg'].label} through a blocked road.",
        f"Tell a child-friendly story where {f['hero'].label} finds bravery and helps the ambulance keep its schedule.",
        f"Write a gentle fable using the words ambulance and schedule, and end with a brave helper making the road clear.",
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
        if e.blocked:
            bits.append("blocked=True")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible story combos:\n")
        for t in triples:
            print(" ", t)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.act} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
