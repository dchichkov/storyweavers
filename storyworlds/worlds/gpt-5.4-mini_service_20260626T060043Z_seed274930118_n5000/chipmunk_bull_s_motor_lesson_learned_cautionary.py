#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/chipmunk_bull_s_motor_lesson_learned_cautionary.py
==============================================================================================================================

A small standalone story world for a cautionary, lesson-learned, problem-solving
nursery-rhyme tale about a chipmunk, a bull's motor, and a careful fix.

Story seed idea:
- A little chipmunk is curious about the bull's motor.
- The bull warns that the motor is not a toy.
- Something goes wrong when the chipmunk pokes at it anyway.
- The chipmunk and the bull solve the problem together.
- The ending leaves a clear lesson: ask first, and keep tiny paws away from
  moving parts.

This world is intentionally tiny and constraint-checked:
- typed entities with physical meters and emotional memes
- a state-driven story, not a swapped-noun template
- a reasonableness gate plus an inline ASP twin
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


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "chipmunk":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "bull":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str
    safe_for_motor: bool = True


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    risk: str
    bump: str
    keyword: str
    caution: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraph_bits: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraph_bits[-1].append(text)

    def para(self) -> None:
        if self.paragraph_bits[-1]:
            self.paragraph_bits.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(bits) for bits in self.paragraph_bits if bits)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraph_bits = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "barn": Setting(
        place="the barn",
        detail="The barn was warm and roomy, with hay that rustled like a soft song.",
    ),
    "shed": Setting(
        place="the shed",
        detail="The shed was small and tidy, with a shelf for tools and a sunlit door.",
    ),
    "yard": Setting(
        place="the yard",
        detail="The yard was bright and breezy, with clover and pebbles underfoot.",
    ),
}

ACTIVITIES = {
    "poke": Activity(
        id="poke",
        verb="poke the motor",
        gerund="poking the motor",
        mess="dusty",
        risk="the motor can jam",
        bump="a little clatter",
        keyword="motor",
        caution="motor parts are not toys",
    ),
    "hide": Activity(
        id="hide",
        verb="hide acorns near the motor",
        gerund="hiding acorns near the motor",
        mess="cluttered",
        risk="the motor can get blocked",
        bump="a little rattle",
        keyword="acorns",
        caution="small things can slip inside and cause trouble",
    ),
    "pull": Activity(
        id="pull",
        verb="pull at the motor cord",
        gerund="pulling at the motor cord",
        mess="tangled",
        risk="the cord can snag",
        bump="a little jerk",
        keyword="cord",
        caution="cords should be handled with care",
    ),
}

TRAITS = ["curious", "cheerful", "brave", "bouncy", "little"]


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="barn", activity="poke", name="Pip", trait="curious"),
    StoryParams(place="shed", activity="hide", name="Milo", trait="bouncy"),
    StoryParams(place="yard", activity="pull", name="Tia", trait="cheerful"),
]


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------
def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    chip = world.get("chipmunk")
    motor = world.get("motor")
    if chip.meters.get("mess", 0.0) < THRESHOLD:
        return out
    sig = ("mess",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    motor.meters["trouble"] = motor.meters.get("trouble", 0.0) + 1
    out.append(f"The bull's motor gave a tiny cough and then a worried hum.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    bull = world.get("bull")
    motor = world.get("motor")
    if motor.meters.get("trouble", 0.0) < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bull.memes["worry"] = bull.memes.get("worry", 0.0) + 1
    out.append("The bull frowned and said the motor needed a careful hand, not a playful push.")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    chip = world.get("chipmunk")
    bull = world.get("bull")
    motor = world.get("motor")
    if chip.memes.get("helpful", 0.0) < THRESHOLD:
        return out
    if motor.meters.get("trouble", 0.0) < THRESHOLD:
        return out
    sig = ("fix",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    motor.meters["trouble"] = 0.0
    motor.meters["running"] = 1.0
    chip.memes["lesson"] = 1.0
    bull.memes["pride"] = 1.0
    out.append("Together they brushed out the dust, straightened the cord, and the motor purred again.")
    return out


RULES = [_r_mess, _r_worry, _r_fix]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    lines: list[str] = []
    while changed:
        changed = False
        for rule in RULES:
            produced = rule(world)
            if produced:
                changed = True
                lines.extend(produced)
    if narrate:
        for line in lines:
            world.say(line)


def predict_trouble(world: World, activity: Activity) -> bool:
    sim = world.copy()
    chip = sim.get("chipmunk")
    chip.meters["mess"] = 1.0
    propagate(sim, narrate=False)
    return sim.get("motor").meters.get("trouble", 0.0) >= THRESHOLD


def valid_combo(place: str, activity: str) -> bool:
    return place in SETTINGS and activity in ACTIVITIES and SETTINGS[place].safe_for_motor


# ---------------------------------------------------------------------------
# Story telling
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    world = World(setting=setting)

    chip = world.add(Entity(
        id="chipmunk",
        kind="character",
        type="chipmunk",
        label=params.name,
        meters={"mess": 0.0},
        memes={"curious": 1.0},
    ))
    bull = world.add(Entity(
        id="bull",
        kind="character",
        type="bull",
        label="the bull",
        meters={},
        memes={},
    ))
    motor = world.add(Entity(
        id="motor",
        kind="thing",
        type="motor",
        label="motor",
        phrase="the bull's motor",
        owner="bull",
        caretaker="bull",
        meters={"running": 1.0, "trouble": 0.0},
        memes={},
    ))

    world.say(
        f"In {setting.place}, {chip.label} the little chipmunk went skipping by with a springy sort of grin, "
        f"and there in the light sat the bull's motor."
    )
    world.say(setting.detail)
    world.say(
        f"{chip.label} was curious, and {chip.pronoun().capitalize()} loved to {activity.verb} even when the bull said, "
        f'"Easy now, little friend; {activity.caution}."'
    )

    world.para()
    if predict_trouble(world, activity):
        world.say(
            f"But {chip.label} did not listen. {chip.pronoun().capitalize()} reached for the motor and began {activity.gerund}, "
            f"and there came {activity.bump}."
        )
    chip.meters["mess"] = 1.0
    propagate(world, narrate=True)

    world.para()
    bull.memes["worry"] = max(bull.memes.get("worry", 0.0), 1.0)
    world.say(
        f"The bull did not roar; {bull.pronoun().capitalize()} only said, "
        f'"A motor is not a toy. Let us fix this in a careful way."'
    )
    chip.memes["helpful"] = 1.0
    world.say(
        f"{chip.label} drooped, then nodded. {chip.pronoun().capitalize()} fetched a tiny brush and helped sweep away the dust."
    )
    propagate(world, narrate=True)

    world.para()
    if motor.meters.get("running", 0.0) >= THRESHOLD:
        world.say(
            f"At last the bull's motor hummed as smooth as a lullaby. {chip.label} smiled, and {chip.pronoun().capitalize()} said, "
            f'"I learned my lesson: ask first, and keep tiny paws away from moving parts."'
        )
    else:
        world.say(
            f"At last the bull's motor rested safe and still. {chip.label} smiled, and {chip.pronoun().capitalize()} said, "
            f'"I learned my lesson: ask first, and keep tiny paws away from moving parts."'
        )

    world.facts.update(
        chip=chip,
        bull=bull,
        motor=motor,
        activity=activity,
        setting=setting,
        lesson=True,
        trouble=motor.meters.get("trouble", 0.0) >= THRESHOLD,
        fixed=motor.meters.get("running", 0.0) >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act = f["activity"]
    return [
        f'Write a short nursery-rhyme-style story about a chipmunk and the bull\'s motor that includes "{act.keyword}".',
        f"Tell a cautionary story where a little chipmunk learns a lesson after {act.verb}, then helps solve the problem.",
        f"Write a gentle problem-solving tale about {act.keyword}, the bull's motor, and a wise ending lesson.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    chip = f["chip"]
    bull = f["bull"]
    act = f["activity"]
    place = f["setting"].place
    qa = [
        QAItem(
            question=f"Who is the story about in {place}?",
            answer=f"It is about {chip.label}, a little chipmunk, and the bull who owns the motor.",
        ),
        QAItem(
            question=f"What did {chip.label} want to do near the bull's motor?",
            answer=f"{chip.label} wanted to {act.verb}, even though the bull warned that {act.caution}.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer="They worked together: the chipmunk helped brush away the trouble, and the bull kept the motor safe while it was fixed.",
        ),
        QAItem(
            question="What lesson did the chipmunk learn?",
            answer="The chipmunk learned to ask first and not touch moving parts without permission.",
        ),
    ]
    if f["trouble"]:
        qa.append(
            QAItem(
                question=f"Why did the bull worry when {chip.label} got too close to the motor?",
                answer=f"The bull worried because {act.risk}, so the motor needed careful handling.",
            )
        )
    if f["fixed"]:
        qa.append(
            QAItem(
                question="What changed by the end of the story?",
                answer="By the end, the motor was working again, and the chipmunk understood how to be careful.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chipmunk?",
            answer="A chipmunk is a small, quick little animal with striped fur and busy paws.",
        ),
        QAItem(
            question="What is a motor?",
            answer="A motor is a machine that makes something move or turn when it runs.",
        ),
        QAItem(
            question="Why should you be careful around moving machine parts?",
            answer="Moving machine parts can catch, jam, or pinch, so people should ask a grown-up and keep fingers and paws back.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when a place and activity are available together.
valid_story(P,A) :- place(P), activity(A), affords(P,A).

% The cautionary turn happens when the chipmunk makes trouble for the motor.
causes_trouble(A) :- activity(A), risky(A).

% The ending lesson is present when the story includes a fix and a lesson.
good_ending(P,A) :- valid_story(P,A), fixable(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in ACTIVITIES:
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("risky", aid))
        lines.append(asp.fact("fixable", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    asp_set = set(asp_valid_combos())
    py_set = {(p, a) for p in SETTINGS for a in ACTIVITIES if valid_combo(p, a)}
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combo() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A nursery-rhyme-style chipmunk, bull, and motor story world."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    activity = args.activity or rng.choice(list(ACTIVITIES))
    if not valid_combo(place, activity):
        raise StoryError("That place and activity do not make a sensible cautionary story.")
    trait = rng.choice(TRAITS)
    name = args.name or rng.choice(["Pip", "Milo", "Tia", "Nibbles", "Penny"])
    return StoryParams(place=place, activity=activity, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(f"{len(asp.atoms(model, 'valid_story'))} compatible stories")
        for p, a in asp.atoms(model, "valid_story"):
            print(f"  {p} / {a}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            if sample.story in seen:
                i += 1
                continue
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
