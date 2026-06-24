#!/usr/bin/env python3
"""
Story world: leukemia task, with a heartwarming happy ending, rhyme, and humor.

This world models a small family helping a child through a leukemia treatment day
by turning a hard task into a playful rhyme-making mission. The story is driven
by simulated state: tiredness, worry, courage, and comfort rise and fall as the
family completes the task and ends with a warm, cheerful image.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen table"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class TaskDef:
    id: str
    verb: str
    noun: str
    cause: str
    helper_tool: str
    humor_bit: str
    rhyme_line1: str
    rhyme_line2: str
    turn_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_worry(world: World) -> list[str]:
    out = []
    child = world.get("child")
    task = world.facts["task"]
    if child.memes.get("worry", 0.0) >= THRESHOLD and ("worry", task.id) not in world.fired:
        world.fired.add(("worry", task.id))
        child.memes["courage"] = child.memes.get("courage", 0.0) + 1
        out.append("The worry tried to grow, but courage grew too.")
    return out


def _r_laughter(world: World) -> list[str]:
    out = []
    child = world.get("child")
    parent = world.get("parent")
    if child.memes.get("joy", 0.0) >= THRESHOLD and ("laugh",) not in world.fired:
        world.fired.add(("laugh",))
        parent.memes["warmth"] = parent.memes.get("warmth", 0.0) + 1
        out.append("Their laughter made the room feel softer.")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("laughter", _r_laughter)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen table", indoors=True, affords={"rhyme_task"}),
    "bedroom": Setting(place="the bedroom window", indoors=True, affords={"rhyme_task"}),
    "hospital_room": Setting(place="the hospital window seat", indoors=True, affords={"rhyme_task"}),
}

TASKS = {
    "rhyme_task": TaskDef(
        id="rhyme_task",
        verb="make a silly rhyme poster",
        noun="rhyme poster",
        cause="leukemia treatment day",
        helper_tool="marker set",
        humor_bit="one marker had drawn a moustache on the star",
        rhyme_line1="A brave kid sat by the bed with a grin,",
        rhyme_line2="Then giggled at the marker with a dorky chin.",
        turn_line="The silly rhyme made the hard day feel small enough to carry.",
        tags={"leukemia", "rhyme", "humor", "heartwarming"},
    ),
}

PROPS = {
    "poster": "a bright paper poster",
    "markers": "a box of fat markers",
    "blanket": "a soft blue blanket",
}

GIRL_NAMES = ["Maya", "Nora", "Lily", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Ben", "Leo", "Max", "Theo", "Finn", "Sam"]
TRAITS = ["brave", "gentle", "cheerful", "curious", "kind"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    task: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _name_pronoun(gender: str) -> tuple[str, str, str]:
    if gender == "girl":
        return ("she", "her", "her")
    if gender == "boy":
        return ("he", "him", "his")
    return ("they", "them", "their")


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    task = TASKS[params.task]
    world = World(setting)

    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    poster = world.add(Entity(id="poster", type="thing", label="poster", phrase=PROPS["poster"], owner=child.id))
    markers = world.add(Entity(id="markers", type="thing", label="markers", phrase=PROPS["markers"], owner=parent.id))
    blanket = world.add(Entity(id="blanket", type="thing", label="blanket", phrase=PROPS["blanket"], owner=parent.id))

    child.memes.update(worry=0.0, joy=0.0, courage=0.0)
    parent.memes.update(warmth=0.0, worry=0.0)

    world.facts.update(
        child=child,
        parent=parent,
        poster=poster,
        markers=markers,
        blanket=blanket,
        task=task,
        setting=setting,
    )

    return world


def predict_task(world: World, child: Entity, task: TaskDef) -> dict:
    sim = world.copy()
    sim_child = sim.get("child")
    sim_child.memes["worry"] = sim_child.memes.get("worry", 0.0) + 1
    sim_child.memes["joy"] = sim_child.memes.get("joy", 0.0) + 1
    propagate(sim, narrate=False)
    return {
        "soothing": sim_child.memes.get("courage", 0.0) >= THRESHOLD,
        "warmth": sim.get("parent").memes.get("warmth", 0.0),
    }


def say_setup(world: World, params: StoryParams) -> None:
    child = world.facts["child"]
    parent = world.facts["parent"]
    task = world.facts["task"]
    world.say(f"{params.name} was a {params.trait} little {params.gender} with leukemia, and {child.pronoun()} had a hard task to do.")
    world.say(
        f"On a quiet day at {world.setting.place}, {child.label} and {parent.label} sat down to {task.verb}."
    )
    world.say(
        f"{parent.label.capitalize()} brought out {PROPS['markers']} and {PROPS['blanket']}, because little comforts can help big days."
    )


def say_turn(world: World, params: StoryParams) -> None:
    child = world.facts["child"]
    parent = world.facts["parent"]
    task = world.facts["task"]
    child.memes["worry"] += 1
    world.say(
        f"{child.label} worried at first, because {task.cause} can feel long and strange."
    )
    world.say(
        f'{parent.label.capitalize()} smiled and said, "We can make a rhyme, climb this climb, and beat the grump in time."'
    )
    world.say(
        f"{task.rhyme_line1} {task.rhyme_line2}"
    )
    world.say(
        f'Then {parent.label} joked, "That marker really must think it is the boss of the box!"'
    )
    world.say(task.humor_bit + ".")
    child.memes["joy"] += 1
    child.memes["worry"] += 1
    propagate(world)


def say_resolution(world: World, params: StoryParams) -> None:
    child = world.facts["child"]
    parent = world.facts["parent"]
    task = world.facts["task"]
    child.memes["joy"] += 1
    child.memes["courage"] += 1
    parent.memes["warmth"] += 1
    world.say(task.turn_line)
    world.say(
        f"{child.label} finished the {task.noun}, and the picture showed a tiny hero wearing a big grin."
    )
    world.say(
        f"At the end, {child.label} leaned against {parent.label}'s shoulder under the blanket, and the room felt bright and safe."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    say_setup(world, params)
    world.para()
    say_turn(world, params)
    world.para()
    say_resolution(world, params)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task: TaskDef = f["task"]
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    return [
        f'Write a heartwarming story for a young child about "{task.id}" and the word "leukemia".',
        f"Tell a gentle, funny story where {child.label} and {parent.label} turn a hard treatment-day task into a rhyme.",
        f"Write a happy-ending story that includes a playful rhyme, a joke, and a warm family moment.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    task: TaskDef = f["task"]
    return [
        QAItem(
            question=f"What hard task did {child.label} and {parent.label} try to do?",
            answer=f"They tried to {task.verb}, which meant making a {task.noun} during a leukemia treatment day.",
        ),
        QAItem(
            question=f"Why did {child.label} worry at first?",
            answer=(
                f"{child.label} worried because leukemia treatment days can feel long and strange, "
                f"and the task seemed hard at the start."
            ),
        ),
        QAItem(
            question=f"What helped {child.label} feel better?",
            answer=(
                f"The silly rhyme, the joke about the markers, and the soft blanket helped {child.label} feel better."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended happily, with {child.label} finished and leaning against {parent.label}'s shoulder in a bright, safe room."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is leukemia?",
            answer="Leukemia is a serious illness that affects the blood and needs treatment from doctors.",
        ),
        QAItem(
            question="Why can rhyme make a hard day feel lighter?",
            answer="Rhyme can feel playful and musical, which can help people smile and feel braver during a hard moment.",
        ),
        QAItem(
            question="Why can humor help in a hospital room?",
            answer="A small joke can make people relax, laugh, and remember that they are still together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
task_valid(T) :- task(T).
story_valid(Place, T) :- setting(Place), task(T), affords(Place, T).
heartwarming(T) :- task(T), tag(T, heartwarming).
rhymeful(T) :- task(T), tag(T, rhyme).
humorous(T) :- task(T), tag(T, humor).
happy_ending(T) :- task(T), tag(T, happy_ending).
compatible_story(Place, T) :- story_valid(Place, T), heartwarming(T), rhymeful(T), humorous(T), happy_ending(T).
#show compatible_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
        for task_id in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, task_id))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(task.tags | {"happy_ending"}):
            lines.append(asp.fact("tag", tid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/2."))
    return sorted(set(asp.atoms(model, "compatible_story")))


def asp_verify() -> int:
    py = {(place, task) for place in SETTINGS for task in SETTINGS[place].affords if is_reasonable(place, task)}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("only in Python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def is_reasonable(place: str, task: str) -> bool:
    return place in SETTINGS and task in TASKS and task in SETTINGS[place].affords


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming leukemia task storyworld with rhyme and humor.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--task", choices=sorted(TASKS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=sorted(TRAITS))
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
    place = args.place or rng.choice(list(SETTINGS))
    task = args.task or rng.choice(list(SETTINGS[place].affords))
    if not is_reasonable(place, task):
        raise StoryError("That setting and task do not fit together.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, name=name, gender=gender, parent=parent, trait=trait)


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
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{ent.id}: {ent.type} {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="hospital_room", task="rhyme_task", name="Maya", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="kitchen", task="rhyme_task", name="Leo", gender="boy", parent="father", trait="gentle"),
    StoryParams(place="bedroom", task="rhyme_task", name="Nora", gender="girl", parent="mother", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combinations:\n")
        for place, task in combos:
            print(f"  {place:14} {task}")
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
            header = f"### {p.name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
