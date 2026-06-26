#!/usr/bin/env python3
"""
A small fairy-tale storyworld about a wallaby, a misunderstanding, and teamwork.

The model keeps a tiny stateful domain:
- a wallaby hero with feelings and physical possession
- a second character who misreads the situation
- a shared task in a fairy-tale setting
- a turn where teamwork clears the misunderstanding

The story is generated from simulation, not from a fixed paragraph.
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
# Typed world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    label: str = ""
    type: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    wearing: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"wallaby"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    weather: str
    enchanted: bool = True


@dataclass
class StoryParams:
    setting: str
    seed: Optional[int] = None
    hero_name: str = "Willa"
    helper_name: str = "Moss"
    guardian_name: str = "Queen Briar"


@dataclass
class StoryState:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
    "moon_glen": Setting(place="Moon Glen", weather="misty"),
    "rose_bridge": Setting(place="Rose Bridge", weather="gentle rain"),
    "thistle_clearing": Setting(place="Thistle Clearing", weather="soft sunrise"),
}

TASKS = {
    "lanterns": {
        "label": "the lanterns",
        "needed": ["rope", "gleam", "balance"],
        "problem": "the lanterns would wobble in the wind",
        "fix": "steady them together",
    },
    "berries": {
        "label": "the berry basket",
        "needed": ["reach", "care", "sturdy paws"],
        "problem": "the basket was too high on the branch",
        "fix": "lift the basket together",
    },
    "bridge": {
        "label": "the little bridge",
        "needed": ["plank", "trust", "careful steps"],
        "problem": "the bridge could not be crossed alone",
        "fix": "cross it together",
    },
}

GIRL_NAMES = ["Willa", "Mina", "Luna", "Ivy", "Nora"]
HELPER_NAMES = ["Moss", "Pip", "Fern", "Perry", "Bram"]
GUARDIAN_NAMES = ["Queen Briar", "Lady Willow", "King Rowan"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def bless(state: StoryState, hero: Entity) -> None:
    state.say(
        f"In {state.setting.place}, there lived a little wallaby named {hero.id} "
        f"who loved every bright path and silver leaf."
    )
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1


def introduce_task(state: StoryState, hero: Entity, helper: Entity, guardian: Entity, task_key: str) -> None:
    task = TASKS[task_key]
    state.say(
        f"One day, {guardian.id} asked {hero.id} and {helper.id} to help with {task['label']}."
    )
    state.say(
        f"{task['problem'].capitalize()}, and the little kingdom needed careful paws and kind hearts."
    )
    state.facts.update(task_key=task_key, task=task, hero=hero, helper=helper, guardian=guardian)
    hero.memes["purpose"] = hero.memes.get("purpose", 0.0) + 1


def misunderstanding(state: StoryState, hero: Entity, helper: Entity, guardian: Entity) -> None:
    task = state.facts["task"]
    hero.memes["hurt"] = hero.memes.get("hurt", 0.0) + 1
    helper.memes["confused"] = helper.memes.get("confused", 0.0) + 1
    state.say(
        f"When {helper.id} saw {hero.id} hopping toward {task['label']}, {helper.id} thought "
        f"{hero.id} wanted the task all to {hero.pronoun('object')}self."
    )
    state.say(
        f"{helper.id} said, '{hero.id}, you are rushing ahead and leaving me behind!'"
    )
    state.say(
        f"{hero.id} froze. {hero.id} had only been trying to be brave, but now the words felt prickly."
    )
    state.facts["misunderstanding"] = True


def teamwork_turn(state: StoryState, hero: Entity, helper: Entity, guardian: Entity) -> None:
    task = state.facts["task"]
    hero.memes["care"] = hero.memes.get("care", 0.0) + 1
    helper.memes["care"] = helper.memes.get("care", 0.0) + 1
    helper.memes["trust"] = helper.memes.get("trust", 0.0) + 1
    state.say(
        f"Then {hero.id} took a slow breath and explained, '{hero.id} only wanted to help, not to push {helper.pronoun('object')} aside.'"
    )
    state.say(
        f"{guardian.id} smiled and gave them a simple plan: {task['fix']}."
    )
    state.say(
        f"So {hero.id} held one side, {helper.id} held the other, and together they were stronger than either one alone."
    )
    state.facts["teamwork"] = True


def resolution(state: StoryState, hero: Entity, helper: Entity, guardian: Entity) -> None:
    task = state.facts["task"]
    state.para()
    state.say(
        f"At last, {hero.id} and {helper.id} finished {task['label']} together, and the little kingdom glowed with relief."
    )
    state.say(
        f"{helper.id} laughed, because the misunderstanding was gone, and {hero.id} laughed too, because teamwork had turned the day gentle again."
    )
    state.say(
        f"By dusk, {state.setting.place} shone like a storybook painting, and {hero.id}'s heart felt light as a lantern flame."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 2
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 2


def build_world(params: StoryParams) -> StoryState:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    state = StoryState(setting=SETTINGS[params.setting])

    hero = state.add(Entity(id=params.hero_name, kind="character", type="wallaby"))
    helper = state.add(Entity(id=params.helper_name, kind="character", type="fairy"))
    guardian = state.add(Entity(id=params.guardian_name, kind="character", type="guardian"))

    task_key = random.choice(list(TASKS.keys()))
    bless(state, hero)
    state.para()
    introduce_task(state, hero, helper, guardian, task_key)
    state.para()
    misunderstanding(state, hero, helper, guardian)
    state.para()
    teamwork_turn(state, hero, helper, guardian)
    resolution(state, hero, helper, guardian)

    state.facts.update(hero=hero, helper=helper, guardian=guardian)
    return state


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: StoryState) -> list[str]:
    task = world.facts["task"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        f"Write a fairy tale about a wallaby named {hero.id}, a misunderstanding, and teamwork in {world.setting.place}.",
        f"Tell a gentle story where {helper.id} thinks {hero.id} is being selfish, but they fix it by working together.",
        f"Write a child-friendly fairy tale that includes {task['label']} and ends with the friends helping each other.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    guardian = world.facts["guardian"]
    task = world.facts["task"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little wallaby who learns how teamwork can clear up a misunderstanding.",
        ),
        QAItem(
            question=f"What did {helper.id} misunderstand about {hero.id}?",
            answer=f"{helper.id} thought {hero.id} wanted to do {task['label']} alone and leave {helper.id} behind.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} solve the problem?",
            answer=f"They talked kindly, listened to {guardian.id}, and worked together to {task['fix']}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The misunderstanding disappeared, and {hero.id} and {helper.id} ended the day feeling brave, close, and proud of their teamwork.",
        ),
    ]


def world_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            question="What kind of animal is a wallaby?",
            answer="A wallaby is a small hopping marsupial, like a kangaroo's smaller cousin.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people work together and help each other reach a goal.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing about what another person means.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{ent.id}: {ent.kind} {' '.join(bits)}")
    lines.append(f"facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid if it has a wallaby, a misunderstanding, and teamwork.
valid_story(S) :- setting(S), has_wallaby, has_misunderstanding, has_teamwork.

% The misunderstanding is meaningful when a helper and a wallaby both exist.
has_misunderstanding :- character(wallaby), character(helper).

% Teamwork is possible when the guardian provides a plan.
has_teamwork :- guardian_plan.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid, s.place))
    lines.append(asp.fact("character", "wallaby"))
    lines.append(asp.fact("character", "helper"))
    lines.append(asp.fact("guardian_plan"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about a wallaby, misunderstanding, and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--guardian")
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
    setting = args.setting or rng.choice(list(SETTINGS.keys()))
    return StoryParams(
        setting=setting,
        seed=args.seed,
        hero_name=args.name or rng.choice(GIRL_NAMES),
        helper_name=args.helper or rng.choice(HELPER_NAMES),
        guardian_name=args.guardian or rng.choice(GUARDIAN_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    if params.seed is not None:
        random.seed(params.seed)
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_verify() -> int:
    import asp
    models = asp.solve(asp_program("#show valid_story/1."), models=1)
    if not models:
        print("MISMATCH: ASP produced no valid story model.")
        return 1
    print("OK: ASP model exists.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print("ASP model:", asp.atoms(model, "valid_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, setting in enumerate(SETTINGS.keys()):
            params = StoryParams(setting=setting, seed=base_seed + i)
            samples.append(generate(params))
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

    for idx, sample in enumerate(samples):
        if idx:
            print("\n" + "=" * 70 + "\n")
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)


if __name__ == "__main__":
    main()
