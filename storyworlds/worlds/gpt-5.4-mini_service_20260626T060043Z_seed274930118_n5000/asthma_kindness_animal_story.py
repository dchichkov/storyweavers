#!/usr/bin/env python3
"""
Asthma Kindness Animal Story
============================

A small standalone storyworld about an animal child with asthma, a sudden
breathing problem, and a kind friend who helps them get relief and feel safe
again.

The story model keeps the world concrete:
- characters are animals with bodies, belongings, and feelings
- asthma can make breathing hard when a trigger is nearby
- a helpful friend can bring an inhaler, guide slow breathing, and call a grown-up
- kindness changes the ending from panic to calm

The goal is to produce complete, child-facing animal stories with a real turn:
something goes wrong, kindness intervenes, and the world ends in a calmer state.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    species: str = "animal"
    name: str = ""
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def subject_name(self) -> str:
        return self.name or self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    triggers: set[str] = field(default_factory=set)
    calm_spots: set[str] = field(default_factory=set)


@dataclass
class Trigger:
    id: str
    label: str
    symptom: str
    severity: float


@dataclass
class HelperAction:
    id: str
    label: str
    effect: str
    calm_gain: float
    breath_gain: float
    needs_grownup: bool = False


@dataclass
class StoryParams:
    place: str
    trigger: str
    hero: str
    friend: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.flags: dict[str, bool] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


ASTHMA_RULES = []


def _rule_trigger(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters.get("triggered", 0.0) < THRESHOLD:
        return out
    sig = ("symptom", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["breath"] = max(0.0, hero.meters.get("breath", 0.0) - 1.0)
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1.0
    out.append(f"{hero.subject_name()} started to wheeze and felt their chest tighten.")
    return out


def _rule_inhaler(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    inhaler = world.entities.get("inhaler")
    if not inhaler or inhaler.carried_by != hero.id:
        return out
    sig = ("relief", hero.id)
    if sig in world.fired:
        return out
    if hero.meters.get("breath", 0.0) >= 1.0:
        return out
    world.fired.add(sig)
    hero.meters["breath"] = hero.meters.get("breath", 0.0) + 1.5
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1.0)
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1.0
    out.append(f"After the puffer, {hero.subject_name()} could breathe more easily.")
    return out


def _rule_kindness(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if not world.flags.get("helper_done"):
        return out
    sig = ("kindness", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["safe"] = hero.memes.get("safe", 0.0) + 1.0
    friend.memes["kind"] = friend.memes.get("kind", 0.0) + 1.0
    out.append(f"{friend.subject_name()} stayed close and helped {hero.subject_name()} feel safe.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in ASTHMA_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


ASTHMA_RULES.extend([_rule_trigger, _rule_inhaler, _rule_kindness])


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        species="animal",
        name=params.hero,
        label=params.hero,
        traits=["small", "gentle", "brave"],
        meters={"breath": 2.0},
        memes={"happy": 1.0},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        species="animal",
        name=params.friend,
        label=params.friend,
        traits=["helpful", "kind"],
        meters={},
        memes={"kind": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        species="animal",
        name=params.helper,
        label=params.helper,
        traits=["grown-up", "calm"],
        meters={},
        memes={"care": 1.0},
    ))
    inhaler = world.add(Entity(
        id="inhaler",
        kind="thing",
        label="the inhaler",
        owner=hero.id,
        caretaker=helper.id,
        carried_by=None,
    ))
    _ = inhaler

    trigger = TRIGGERS[params.trigger]
    world.facts.update(place=place, trigger=trigger, hero=hero, friend=friend, helper=helper, params=params)

    world.say(
        f"{hero.subject_name()} was a little {hero.species} who loved quiet games and sunny walks."
    )
    world.say(
        f"{friend.subject_name()} was {hero.subject_name()}'s kind friend, and {helper.subject_name()} was nearby to help when needed."
    )
    world.say(
        f"They all knew that {trigger.label} could make {hero.subject_name()}'s breathing hard."
    )

    world.para()
    world.say(f"One day, the friends went to {place.label}.")
    if trigger.label:
        world.say(f"The air there held {trigger.label}, and that was enough to trouble {hero.subject_name()}.")
    hero.meters["triggered"] = 1.0
    propagate(world)

    world.para()
    world.say(f"{hero.subject_name()} stopped playing and looked scared.")
    world.say(f"{friend.subject_name()} saw the worry right away and rushed over with a gentle voice.")
    world.say(
        f"{friend.subject_name()} helped {hero.subject_name()} find the inhaler and sit still."
    )
    inhaler.carried_by = hero.id
    world.flags["helper_done"] = True
    propagate(world)

    world.say(
        f"{helper.subject_name()} came close, checked on {hero.subject_name()}, and praised {friend.subject_name()} for being so kind."
    )
    world.say(
        f"Together they took slow breaths until {hero.subject_name()}'s chest felt loose again."
    )

    world.para()
    world.say(
        f"In the end, {hero.subject_name()} could breathe спокойно and smile again."
    )
    world.say(
        f"{friend.subject_name()} stayed beside {hero.subject_name()}, and the day felt safe because kindness had helped."
    )

    world.facts["trigger_obj"] = trigger
    return world


def prize_is_risky(trigger: Trigger) -> bool:
    return trigger.severity >= 1.0


def select_help_action(trigger: Trigger) -> Optional[HelperAction]:
    if trigger.id == "dust":
        return HELPER_ACTIONS["inhaler"]
    if trigger.id == "flowers":
        return HELPER_ACTIONS["slow_breath"]
    if trigger.id == "smoke":
        return HELPER_ACTIONS["inhaler"]
    return HELPER_ACTIONS["slow_breath"]


def explain_invalid(trigger: Trigger) -> str:
    return (
        f"(No story: {trigger.label} is not a good asthma trigger for this world, "
        f"so there would be no honest breathing problem to solve.)"
    )


SETTINGS = {
    "garden": Place(
        id="garden",
        label="the garden",
        indoors=False,
        triggers={"flowers"},
        calm_spots={"bench", "shade"},
    ),
    "playground": Place(
        id="playground",
        label="the playground",
        indoors=False,
        triggers={"dust"},
        calm_spots={"bench"},
    ),
    "porch": Place(
        id="porch",
        label="the porch",
        indoors=True,
        triggers={"smoke"},
        calm_spots={"chair"},
    ),
}

PLACES = SETTINGS

TRIGGERS = {
    "flowers": Trigger(id="flowers", label="pollen from the flowers", symptom="wheeze", severity=1.0),
    "dust": Trigger(id="dust", label="dust from the dry path", symptom="cough", severity=1.0),
    "smoke": Trigger(id="smoke", label="smoke from a nearby fire pit", symptom="wheeze", severity=1.5),
}

HELPER_ACTIONS = {
    "inhaler": HelperAction(
        id="inhaler",
        label="the inhaler",
        effect="opens the airways",
        calm_gain=1.0,
        breath_gain=1.5,
        needs_grownup=True,
    ),
    "slow_breath": HelperAction(
        id="slow_breath",
        label="slow breaths",
        effect="helps the body settle",
        calm_gain=1.0,
        breath_gain=0.5,
        needs_grownup=False,
    ),
}


GENTLE_NAMES = [
    "Milo", "Luna", "Pip", "Nori", "Toby", "Mina", "Penny", "Rory", "Benny", "Kiki"
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld about asthma and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place_id, place in SETTINGS.items():
        for trig_id in place.triggers:
            out.append((place_id, trig_id))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place or args.trigger:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.trigger is None or c[1] == args.trigger)
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place_id, trig_id = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(GENTLE_NAMES)
    friend_choices = [n for n in GENTLE_NAMES if n != hero]
    friend = args.friend or rng.choice(friend_choices)
    helper_choices = [n for n in GENTLE_NAMES if n not in {hero, friend}]
    helper = args.helper or rng.choice(helper_choices)
    return StoryParams(place=place_id, trigger=trig_id, hero=hero, friend=friend, helper=helper)


def generate(params: StoryParams) -> StorySample:
    trigger = TRIGGERS[params.trigger]
    if not prize_is_risky(trigger):
        raise StoryError(explain_invalid(trigger))
    world = build_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    trigger = world.facts["trigger_obj"]
    place = world.place.label
    return [
        f"Write a short animal story for a young child about {hero.name}, {friend.name}, and kindness at {place}.",
        f"Tell a gentle story where {trigger.label} makes {hero.name} wheeze, but a friend helps with an inhaler.",
        f"Write an animal story that starts calm, has an asthma problem, and ends with kindness making the day safe again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    helper = world.facts["helper"]
    trigger = world.facts["trigger_obj"]
    place = world.place.label
    return [
        QAItem(
            question=f"Who was the little animal that had trouble breathing at {place}?",
            answer=f"{hero.name} was the little animal who had asthma trouble at {place}.",
        ),
        QAItem(
            question=f"What made {hero.name} start to wheeze?",
            answer=f"{trigger.label} made {hero.name} start to wheeze and feel scared.",
        ),
        QAItem(
            question=f"How did {friend.name} help {hero.name}?",
            answer=f"{friend.name} stayed calm, found the inhaler, and helped {hero.name} breathe more easily.",
        ),
        QAItem(
            question=f"Who else checked on {hero.name} in the end?",
            answer=f"{helper.name} checked on {hero.name} too and praised {friend.name} for being kind.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is asthma?",
            answer="Asthma is a breathing problem that can make it hard to get air into the lungs, especially when something in the air causes trouble.",
        ),
        QAItem(
            question="What does an inhaler do?",
            answer="An inhaler is a medicine tool that can help open the airways so breathing becomes easier.",
        ),
        QAItem(
            question="Why is kindness important when someone has asthma?",
            answer="Kindness helps the person stay calm, get help quickly, and feel safe while their breathing gets better.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.carried_by:
            bits.append(f"carried_by={ent.carried_by}")
        lines.append(f"  {ent.id}: {ent.label or ent.name} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
trigger(T) :- trigger_kind(T).
valid(P,T) :- place(P), trigger(T), allowed(P,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for trig in sorted(place.triggers):
            lines.append(asp.fact("allowed", pid, trig))
    for tid, trig in TRIGGERS.items():
        lines.append(asp.fact("trigger_kind", tid))
        lines.append(asp.fact("symptom", tid, trig.symptom))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="playground", trigger="dust", hero="Milo", friend="Luna", helper="Penny"),
    StoryParams(place="garden", trigger="flowers", hero="Kiki", friend="Toby", helper="Mina"),
    StoryParams(place="porch", trigger="smoke", hero="Nori", friend="Benny", helper="Rory"),
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b}" for a, b in asp_valid_combos()))
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
            header = f"### {p.hero} at {p.place} with {p.trigger}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
