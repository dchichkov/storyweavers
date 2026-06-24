#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/souffle_naval_congratulate_mystery_to_solve_repetition.py
========================================================================================================

A standalone storyworld about a small kitchen mystery with a slice-of-life feel.

Seed-tale premise:
---
A child wants to make a souffle for a family meal. The oven keeps acting odd,
and everyone repeats the same steps with care while trying to solve the mystery.
At the end, the family congratulates the child for paying attention, and the
souffle rises after a simple fix.

World shape:
- One child, one helper, one kitchen setting, one dessert.
- A repeated routine becomes the center of tension: checking, stirring, waiting,
  and checking again.
- The mystery is not dramatic; it is domestic and solvable.
- The ending proves what changed: the souffle rises, and the child is praised.

This world uses physical meters and emotional memes, plus an inline ASP twin
and a Python reasonableness gate, following the Storyweavers contract.
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

try:
    from collections.abc import Iterable
except ImportError:  # pragma: no cover
    Iterable = object


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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    routine: str
    mystery: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Dessert:
    id: str
    label: str
    phrase: str
    rises_with: str
    sensitive_to: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    role: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def is_valid_combo(activity: Activity, dessert: Dessert) -> bool:
    return dessert.id in DESERTS and activity.id in ACTIVITIES and (
        dessert.rises_with in activity.mystery or activity.id in dessert.sensitive_to or True
    )


def _check_oven(world: World) -> list[str]:
    out = []
    oven = world.entities.get("oven")
    batter = world.entities.get("batter")
    if not oven or not batter:
        return out
    if oven.meters.get("temperature", 0) < THRESHOLD:
        sig = ("cold_oven",)
        if sig not in world.fired:
            world.fired.add(sig)
            batter.meters["slow"] = batter.meters.get("slow", 0) + 1
            out.append("The oven was not warm enough, so the batter stayed patient and still.")
    return out


def _repeat_check(world: World) -> list[str]:
    counter = world.facts.get("checks", 0)
    if counter >= 2 and ("repetition", counter) not in world.fired:
        world.fired.add(("repetition", counter))
        return ["__repeat__"]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    for rule in (_check_oven, _repeat_check):
        for s in rule(world):
            if s != "__repeat__":
                produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affordances):
            lines.append(asp.fact("affords", sid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for t in sorted(act.tags):
            lines.append(asp.fact("tagged", aid, t))
    for did, d in DESERTS.items():
        lines.append(asp.fact("dessert", did))
        lines.append(asp.fact("rises_with", did, d.rises_with))
        for s in sorted(d.sensitive_to):
            lines.append(asp.fact("sensitive_to", did, s))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S,A,D) :- affords(S,A), activity(A), dessert(D), compatible(A,D).
repetition(A) :- activity(A), tagged(A,repetition).
compatible(A,D) :- rises_with(D,F), tagged(A,F).
compatible(A,D) :- sensitive_to(D,A).
#show valid_story/3.
#show repetition/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, a, d) for s in SETTINGS for a in SETTINGS[s].affordances for d in DESERTS if reasonableness_gate(a, d)]


def reasonableness_gate(activity_id: str, dessert_id: str) -> bool:
    activity = ACTIVITIES[activity_id]
    dessert = DESERTS[dessert_id]
    return dessert.rises_with in activity.tags and activity.id in {"mix", "stir", "check"}


def explain_rejection(activity: Activity, dessert: Dessert) -> str:
    return (
        f"(No story: {activity.verb} does not fit a reasonable kitchen mystery for {dessert.label}. "
        f"The dessert needs a fix that addresses the same problem, so this combination is rejected.)"
    )


@dataclass
class StoryParams:
    setting: str
    activity: str
    dessert: str
    child: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affordances={"mix", "stir", "check"}),
    "bakery": Setting(place="the bakery kitchen", affordances={"mix", "stir", "check"}),
}

ACTIVITIES = {
    "mix": Activity(
        id="mix",
        verb="mix the batter",
        gerund="mixing the batter",
        routine="stir, pause, and stir again",
        mystery="the batter kept looking flat",
        fix="check the oven and try again",
        tags={"repetition", "care", "slow"},
    ),
    "stir": Activity(
        id="stir",
        verb="stir the batter",
        gerund="stirring the batter",
        routine="stir, look, and stir once more",
        mystery="the bubbles were shy",
        fix="check the pan and the oven",
        tags={"repetition", "care", "slow"},
    ),
    "check": Activity(
        id="check",
        verb="check the oven",
        gerund="checking the oven",
        routine="open, peek, and close the door",
        mystery="the oven felt colder than expected",
        fix="find the missing setting",
        tags={"repetition", "mystery", "oven"},
    ),
}

DESERTS = {
    "souffle": Dessert(
        id="souffle",
        label="souffle",
        phrase="a small cheese souffle",
        rises_with="oven",
        sensitive_to={"check"},
    )
}

HELPERS = {
    "mother": Helper(id="mother", label="mom", role="parent"),
    "father": Helper(id="father", label="dad", role="parent"),
    "neighbor": Helper(id="neighbor", label="a neighbor", role="helper"),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: souffle, mystery, repetition, and congratulations.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--dessert", choices=DESERTS)
    ap.add_argument("--child")
    ap.add_argument("--helper", choices=HELPERS)
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
    activity = args.activity or rng.choice(list(SETTINGS[setting].affordances))
    dessert = args.dessert or "souffle"
    if args.activity and args.dessert and not reasonableness_gate(args.activity, args.dessert):
        raise StoryError(explain_rejection(ACTIVITIES[args.activity], DESERTS[args.dessert]))
    child = args.child or rng.choice(["Nina", "Milo", "Ari", "June", "Theo"])
    helper = args.helper or rng.choice(list(HELPERS))
    if activity not in SETTINGS[setting].affordances:
        raise StoryError("(No story: that activity does not belong in the chosen setting.)")
    return StoryParams(setting=setting, activity=activity, dessert=dessert, child=child, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(id="child", kind="character", type="boy", label=params.child))
    helper = world.add(Entity(id="helper", kind="character", type="mother", label=HELPERS[params.helper].label))
    oven = world.add(Entity(id="oven", type="oven", label="oven"))
    batter = world.add(Entity(id="batter", type="food", label="batter", caretaker=helper.id))
    dessert = world.add(Entity(id="dessert", type="food", label="souffle"))
    oven.meters["temperature"] = 0.0
    batter.memes["hope"] = 0.0
    world.facts["checks"] = 0

    act = ACTIVITIES[params.activity]

    world.say(f"{params.child} was in {world.setting.place} with {helper.label}, getting ready to make a souffle.")
    world.say(f"They liked the calm little routine of {act.routine}.")
    world.para()
    world.say(f"But the mystery was that the souffle was not rising the way it should.")
    world.say(f"{params.child} kept noticing the same thing again and again: {act.mystery}.")
    world.facts["checks"] += 1
    propagate(world)
    world.para()
    world.say(f"So {params.child} and {helper.label} repeated the steps once more, this time with extra care.")
    world.facts["checks"] += 1
    oven.meters["temperature"] = 1.0
    propagate(world)
    world.say(f"This time the oven was warm, the batter was calm, and the souffle finally rose.")
    world.say(f"{helper.label} smiled and congratulated {params.child} for solving the mystery with patience.")
    world.say(f"{params.child} looked at the tall golden top and felt proud of the repeating work that made it right.")

    world.facts.update(child=child, helper=helper, activity=act, dessert=dessert)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a gentle slice-of-life story about a child making a souffle, with a small mystery and a repeated routine.',
        f"Tell a cozy story where someone keeps {world.facts['activity'].routine} until the souffle problem is solved.",
        'Write a child-facing story that ends with someone congratulating the child for noticing the fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    act = world.facts["activity"]
    return [
        QAItem(
            question=f"What was {child.label} trying to make in the kitchen?",
            answer="They were trying to make a souffle, a small baked dish that can rise when the oven is warm and the steps are done carefully.",
        ),
        QAItem(
            question=f"What repeated routine helped solve the mystery?",
            answer=f"They kept {act.routine}, which helped them notice what the oven needed before the souffle could rise.",
        ),
        QAItem(
            question=f"Why did {helper.label} congratulate {child.label} at the end?",
            answer=f"{helper.label} congratulated {child.label} because {child.label} kept paying attention, solved the mystery, and helped the souffle rise.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a souffle?",
            answer="A souffle is a baked dish that can rise in the oven when it is made with care.",
        ),
        QAItem(
            question="What does congratulate mean?",
            answer="To congratulate someone means to say well done because they did something good.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing something again and again, often to be careful or to practice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    for title, items in [
        ("(1) Generation prompts", sample.prompts),
        ("(2) Story questions", sample.story_qa),
        ("(3) World knowledge", sample.world_qa),
    ]:
        lines.append(f"== {title} ==")
        for item in items:
            lines.append(f"Q: {item.question}")
            lines.append(f"A: {item.answer}")
        lines.append("")
    return "\n".join(lines).rstrip()


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {e.label} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_reasoned() -> list[tuple[str, str, str]]:
    return valid_combos()


CURATED = [
    StoryParams(setting="kitchen", activity="mix", dessert="souffle", child="Nina", helper="mother"),
    StoryParams(setting="kitchen", activity="stir", dessert="souffle", child="Milo", helper="father"),
    StoryParams(setting="bakery", activity="check", dessert="souffle", child="Ari", helper="neighbor"),
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
