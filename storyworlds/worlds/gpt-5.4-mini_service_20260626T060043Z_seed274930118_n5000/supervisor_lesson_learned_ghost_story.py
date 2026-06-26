#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/supervisor_lesson_learned_ghost_story.py
===============================================================================================================

A compact storyworld: a supervisor, a ghostly scare, and a lesson learned.

Seed tale idea:
- A night supervisor walks the quiet halls.
- A strange ghostly chill makes everyone jump.
- The supervisor notices the ghost is not trying to hurt anyone.
- The ghost needs help with one small lost thing.
- The story ends with a gentle lesson learned: calm thinking and kindness can turn a scare into help.

The story is written in a child-facing ghost-story style: a little eerie at first,
then safe, warm, and resolved with a clear lesson learned.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "mother", "supervisor"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Scenario:
    ghost_name: str
    ghost_kind: str
    missing_item: str
    missing_phrase: str
    setting_key: str
    lesson: str


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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "library": Setting(place="the library", mood="quiet", affords={"ghost", "search"}),
    "museum": Setting(place="the museum", mood="still", affords={"ghost", "search"}),
    "school": Setting(place="the school hallway", mood="echoing", affords={"ghost", "search"}),
    "hotel": Setting(place="the hotel lobby", mood="sleepy", affords={"ghost", "search"}),
}

SCENARIOS = {
    "library": Scenario(
        ghost_name="Milo",
        ghost_kind="bookish ghost",
        missing_item="book",
        missing_phrase="a tiny library book with a blue ribbon",
        setting_key="library",
        lesson="when something seems spooky, it helps to look carefully before you panic",
    ),
    "museum": Scenario(
        ghost_name="Pip",
        ghost_kind="shy ghost",
        missing_item="key",
        missing_phrase="a little brass key to the old display case",
        setting_key="museum",
        lesson="a calm voice can help a worried ghost feel safe",
    ),
    "school": Scenario(
        ghost_name="Dot",
        ghost_kind="lonely ghost",
        missing_item="note",
        missing_phrase="a folded note that fell near the lockers",
        setting_key="school",
        lesson="kind helpers can solve a problem better than scared footsteps",
    ),
    "hotel": Scenario(
        ghost_name="Moss",
        ghost_kind="gentle ghost",
        missing_item="bell",
        missing_phrase="a silver bell from the front desk",
        setting_key="hotel",
        lesson="if you listen first, even a spooky moment can turn into help",
    ),
}

SUPERVISOR_NAMES = ["Mrs. Lee", "Mr. Alvarez", "Ms. Kim", "Mr. Stone"]
HELPER_NAMES = ["Tia", "Ben", "Nina", "Omar"]


@dataclass
class StoryParams:
    setting: str
    scenario: str
    supervisor: str
    helper: str
    seed: Optional[int] = None


ASP_RULES = r"""
valid_story(S) :- setting(S), scenario_ok(S).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for k in SETTINGS:
        lines.append(asp.fact("setting", k))
    for k in SCENARIOS:
        lines.append(asp.fact("scenario_ok", k))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    py = {(k,) for k in SCENARIOS}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} scenarios).")
        return 0
    print("MISMATCH between clingo and Python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with a supervisor and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--scenario", choices=SCENARIOS)
    ap.add_argument("--supervisor", choices=SUPERVISOR_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    scenario = args.scenario or setting
    if scenario not in SCENARIOS:
        raise StoryError("No valid ghost story scenario matches the requested setting.")
    supervisor = args.supervisor or rng.choice(SUPERVISOR_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(setting=setting, scenario=scenario, supervisor=supervisor, helper=helper)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    scenario = SCENARIOS[params.scenario]
    if params.setting != scenario.setting_key:
        raise StoryError("That scenario only works in its matching setting.")
    world = World(setting)

    supervisor = world.add(Entity(id="supervisor", kind="character", type="supervisor", label=params.supervisor))
    helper = world.add(Entity(id="helper", kind="character", type="child", label=params.helper))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label=scenario.ghost_name))
    item = world.add(Entity(
        id="lost_item",
        kind="thing",
        type=scenario.missing_item,
        label=scenario.missing_item,
        phrase=scenario.missing_phrase,
        caretaker=supervisor.id,
    ))

    world.facts.update(setting=params.setting, scenario=params.scenario, supervisor=supervisor,
                       helper=helper, ghost=ghost, item=item, lesson=scenario.lesson)

    # Act 1: quiet setup.
    world.say(
        f"Late one night, {params.supervisor} was making a careful round through {setting.place}, "
        f"where everything felt {setting.mood} and still."
    )
    world.say(
        f"{params.helper} came along with a little flashlight, and the beam slid over shelves and doors like a silver ribbon."
    )
    world.para()

    # Act 2: spooky turn.
    world.say(
        f"Then a cold puff of air drifted down the hall, and a pale shape shimmered near the corner."
    )
    world.say(
        f"It was {scenario.ghost_name}, a {scenario.ghost_kind}, and it looked very lost."
    )
    ghost.memes["sad"] = 1.0
    helper.memes["fear"] = 1.0
    supervisor.memes["alert"] = 1.0
    world.say(
        f"{params.helper} took a tiny step back, but {params.supervisor} lifted a hand and whispered, "
        f'"Wait. Let us look first."'
    )
    world.para()

    # Act 3: lesson learned / resolution.
    world.say(
        f"{params.supervisor} shone the flashlight lower, and there, under a bench, was {scenario.missing_phrase}."
    )
    item.meters["found"] = 1.0
    ghost.memes["hope"] = 1.0
    ghost.memes["sad"] = 0.0
    world.say(
        f"{scenario.ghost_name} drifted closer and gave a soft, chilly sigh. The little {scenario.missing_item} had been missing all along."
    )
    world.say(
        f"{params.helper} handed it over, and {params.supervisor} smiled. "
        f'"See?" {params.supervisor} said. "A spooky moment can have a simple answer."'
    )
    world.say(
        f"{scenario.ghost_name} tucked the {scenario.missing_item} away, the cold in the hall melted into a warm hush, "
        f"and the night felt safe again."
    )
    world.say(
        f"The lesson learned was that {scenario.lesson}."
    )

    prompts = [
        f'Write a gentle ghost story set in {setting.place} with a supervisor named {params.supervisor}.',
        f"Tell a spooky-but-safe story where {scenario.ghost_name} the ghost loses {scenario.missing_phrase}.",
        f"Write a child-friendly story that ends with a lesson learned about {scenario.lesson}.",
    ]

    story_qa = [
        QAItem(
            question=f"Who was watching over {setting.place} that night?",
            answer=f"{params.supervisor} was the supervisor making a careful round through {setting.place}.",
        ),
        QAItem(
            question=f"What did the ghost need help finding?",
            answer=f"{scenario.ghost_name} needed help finding {scenario.missing_phrase}.",
        ),
        QAItem(
            question=f"How did the supervisor help the ghost?",
            answer=f"{params.supervisor} stayed calm, looked carefully, and found the lost {scenario.missing_item} under a bench.",
        ),
        QAItem(
            question="What lesson was learned at the end?",
            answer=f"The lesson learned was that {scenario.lesson}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a supervisor?",
            answer="A supervisor is someone who watches over a place or a group and helps keep things safe and organized.",
        ),
        QAItem(
            question="Why can a ghost story be scary but still safe for children?",
            answer="A ghost story can feel spooky because of shadows and cold air, but it is safe for children when the story is friendly, calm, and ends with help.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid ghost-story scenario(s):")
        for (scenario,) in stories:
            print(f"  {scenario}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for key in sorted(SCENARIOS):
            p = StoryParams(
                setting=SCENARIOS[key].setting_key,
                scenario=key,
                supervisor=SUPERVISOR_NAMES[0],
                helper=HELPER_NAMES[0],
                seed=base_seed,
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
