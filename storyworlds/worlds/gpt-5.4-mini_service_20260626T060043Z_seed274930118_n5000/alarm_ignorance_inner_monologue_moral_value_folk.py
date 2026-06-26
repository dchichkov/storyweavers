#!/usr/bin/env python3
"""
Story world: alarm, ignorance, inner monologue, moral value, folk-tale style.

A small child-facing folk tale domain about a villager who ignores a warning bell,
hears an inner monologue of doubt and conscience, and learns to value care over
carelessness.
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

TRYON_ACTIONS = {
    "feed_goose": "feed the goose",
    "close_gate": "close the gate",
    "light_lantern": "light the lantern",
    "bring_water": "bring water to the mill",
}

MORAL_VALUES = {
    "care": "care",
    "honesty": "honesty",
    "patience": "patience",
    "helpfulness": "helpfulness",
    "responsibility": "responsibility",
}

LOCATIONS = {
    "village_green": "the village green",
    "old_well": "the old well",
    "hill_path": "the hill path",
    "river_bank": "the river bank",
    "lantern_house": "the lantern house",
}

CHARACTER_NAMES = [
    "Mara", "Tobin", "Elin", "Perrin", "Sera", "Bram", "Nell", "Lio"
]

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    folk_marker: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Alarm:
    id: str
    label: str
    trigger: str
    effect: str
    warning: str
    consequence: str


@dataclass
class MoralValue:
    id: str
    label: str
    lesson: str
    opposite: str


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

        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


# ---------------------------------------------------------------------------
# World registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "village": Setting(place="the village green", folk_marker="village", affords={"alarm"}),
    "well": Setting(place="the old well", folk_marker="well", affords={"alarm"}),
    "path": Setting(place="the hill path", folk_marker="path", affords={"alarm"}),
}

ALARMS = {
    "bell": Alarm(
        id="bell",
        label="bronze bell",
        trigger="ring the bronze bell",
        effect="alarm",
        warning="the bell would wake the whole lane",
        consequence="people would be warned in time",
    ),
    "horn": Alarm(
        id="horn",
        label="hollow horn",
        trigger="blow the hollow horn",
        effect="alarm",
        warning="the horn would call everyone together",
        consequence="the village could gather quickly",
    ),
}

VALUES = {
    "care": MoralValue(
        id="care",
        label="care",
        lesson="look closely before acting",
        opposite="carelessness",
    ),
    "responsibility": MoralValue(
        id="responsibility",
        label="responsibility",
        lesson="do the needed thing when it matters",
        opposite="forgetfulness",
    ),
    "helpfulness": MoralValue(
        id="helpfulness",
        label="helpfulness",
        lesson="help others when you can",
        opposite="selfishness",
    ),
}

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------


@dataclass
class StoryParams:
    place: str
    alarm: str
    value: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.
#show warning/3.

valid(Place, Alarm, Value) :- place(Place), alarm(Alarm), value(Value).

warning(Place, Alarm, Value) :- valid(Place, Alarm, Value),
                               place_has_alarm(Place, Alarm),
                               alarm_teaches(Alarm, Value).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("place_has_alarm", pid, a))
    for aid, alarm in ALARMS.items():
        lines.append(asp.fact("alarm", aid))
        lines.append(asp.fact("alarm_teaches", aid, "care"))
        lines.append(asp.fact("alarm_teaches", aid, "responsibility"))
    for vid in VALUES:
        lines.append(asp.fact("value", vid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for alarm in ALARMS:
            for value in VALUES:
                combos.append((place, alarm, value))
    return combos


def reasonableness_gate(place: str, alarm: str, value: str) -> None:
    if place not in SETTINGS:
        raise StoryError(f"Unknown place: {place}")
    if alarm not in ALARMS:
        raise StoryError(f"Unknown alarm: {alarm}")
    if value not in VALUES:
        raise StoryError(f"Unknown moral value: {value}")


def predict_alarm(world: World, alarm: Alarm) -> dict[str, bool]:
    child = world.get("child")
    return {
        "warning_felt": child.memes.get("doubt", 0.0) > 0.0 or child.memes.get("alarm", 0.0) > 0.0,
        "harm_avoided": child.meters.get("harm", 0.0) < 1.0,
    }


def inner_monologue(child: Entity, alarm: Alarm, value: MoralValue) -> str:
    if child.memes.get("ignorance", 0.0) > 0.0:
        return (
            f"{child.id} thought, 'Maybe the bell is just making noise again. "
            f"But what if {alarm.warning}? I should remember {value.lesson}.'"
        )
    return (
        f"{child.id} thought, 'I hear the warning, and I should listen. "
        f"{value.lesson} is the wiser path.'"
    )


def tell_world(place: Setting, alarm: Alarm, value: MoralValue, name: str) -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type="child"))
    elder = world.add(Entity(id="Grandmother", kind="character", type="elder", label="grandmother"))
    bell = world.add(Entity(id=alarm.id, type="alarm", label=alarm.label, phrase=alarm.trigger))

    child.memes["ignorance"] = 1.0
    child.memes["curiosity"] = 1.0
    world.facts.update(child=child, elder=elder, alarm=alarm, value=value, bell=bell, place=place)

    world.say(
        f"Long ago, in {place.place}, there lived a child named {name} and a wise grandmother."
    )
    world.say(
        f"Every day the {alarm.label} stood near the lane, because it could {alarm.trigger} when danger came."
    )
    world.say(
        f"The old folk knew its meaning, but {name} had not yet learned the worth of {value.label}."
    )

    world.para()
    world.say(
        f"One bright morning, the bell began to ring. It was the kind of sound that said, "
        f"'{alarm.consequence}.'"
    )
    world.say(
        f"{name} hesitated. {inner_monologue(child, alarm, value)}"
    )
    world.say(
        f"Still, {name}'s ignorance was loud in the heart, and {name} walked on as if nothing mattered."
    )

    world.para()
    child.memes["alarm"] = 1.0
    child.memes["ignorance"] = 0.0
    child.memes["doubt"] = 1.0
    world.say(
        f"Then the grandmother called out, 'Child, listen when a warning comes!'"
    )
    world.say(
        f"At last {name} understood that {alarm.warning} if nobody paid attention."
    )
    world.say(
        f"{name} ran to help, and with a steady hand {name} chose to honor {value.label} instead of ignorance."
    )

    world.para()
    child.meters["harm"] = 0.0
    child.memes["wisdom"] = 1.0
    world.say(
        f"Together they sounded the {alarm.label} properly, and the lane filled with quick feet and careful hearts."
    )
    world.say(
        f"By evening, everyone was safe, and {name} knew that {value.lesson} was the best kind of magic."
    )
    return world


# ---------------------------------------------------------------------------
# QA and narration helpers
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    alarm = f["alarm"]
    value = f["value"]
    return [
        f"Write a short folk tale about {child.id}, an alarm, and a lesson about {value.label}.",
        f"Tell a child-friendly story where a warning bell matters more than ignorance.",
        f"Write a simple story in a folk-tale style about listening to {alarm.label} and learning {value.lesson}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    alarm = f["alarm"]
    value = f["value"]
    return [
        QAItem(
            question=f"Why did {child.id} ignore the bell at first?",
            answer=(
                f"{child.id} ignored it at first because of ignorance and because {child.id} had not yet learned how serious the warning was."
            ),
        ),
        QAItem(
            question=f"What did the grandmother want {child.id} to understand?",
            answer=(
                f"The grandmother wanted {child.id} to understand that {alarm.warning} and that {value.lesson} was the wiser choice."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=(
                f"By the end, {child.id} stopped acting from ignorance, listened to the alarm, and chose {value.label} instead."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    alarm = f["alarm"]
    value = f["value"]
    return [
        QAItem(
            question="What is an alarm for?",
            answer="An alarm is a warning signal that tells people to pay attention and act quickly.",
        ),
        QAItem(
            question="What does ignorance mean?",
            answer="Ignorance means not knowing something important yet.",
        ),
        QAItem(
            question=f"What is {value.label}?",
            answer=f"{value.label.capitalize()} means {value.lesson}.",
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
    lines.append("== (3) World knowledge ==")
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------


def build_story(params: StoryParams) -> StorySample:
    reasonableness_gate(params.place, params.alarm, params.value)
    world = tell_world(SETTINGS[params.place], ALARMS[params.alarm], VALUES[params.value], params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world with alarm and ignorance.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--alarm", choices=ALARMS.keys())
    ap.add_argument("--value", choices=VALUES.keys())
    ap.add_argument("--name", choices=CHARACTER_NAMES)
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
    place = args.place or rng.choice(list(SETTINGS))
    alarm = args.alarm or rng.choice(list(ALARMS))
    value = args.value or rng.choice(list(VALUES))
    reasonableness_gate(place, alarm, value)
    name = args.name or rng.choice(CHARACTER_NAMES)
    return StoryParams(place=place, alarm=alarm, value=value, name=name)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show warning/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for alarm in ALARMS:
                for value in VALUES:
                    params = StoryParams(place=place, alarm=alarm, value=value, name=CHARACTER_NAMES[0])
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
