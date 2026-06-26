#!/usr/bin/env python3
"""
Tall-tale storyworld: proper transformations, teamwork, and a surprise ending.

A little source tale idea:
---
A proper miller named Amos lives by a windy river with three helpers: a cat,
a goose, and a mule. Every dawn, the river sneaks in a surprise: it steals the
grain sacks, tangles the towrope, or knocks the mill wheel sideways. Amos is
too small to out-muscle the river, but he is clever. He and the helpers work
together, each changing shape in a proper, impossible way for just long enough
to solve the trouble. The surprise is that the river does not mean harm; it is
carrying a gift from upstream, and the new shape of the team makes it possible
to catch it.
---

The simulation keeps track of:
- who is present
- what they can change into
- whether the task needs teamwork
- whether the surprise has been discovered
- physical meters for load, reach, splash, and steadiness
- emotional memes for pride, worry, delight, and trust
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    role: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    transformed: bool = False
    form: str = "self"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.label in {"Amos", "Otto"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
            if self.label in {"Mina", "Iris"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "they" if self.plural else self.pronoun("subject")


@dataclass
class Setting:
    place: str
    weather: str
    river_name: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    from_form: str
    to_form: str
    label: str
    meters_gain: dict[str, float]
    memes_gain: dict[str, float]
    reason: str


@dataclass
class Task:
    id: str
    label: str
    problem: str
    risk: str
    needs: set[str]
    surprise_key: str


@dataclass
class Helper:
    id: str
    label: str
    help_text: str
    transform: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "riverbend": Setting(place="the river bend", weather="windy", river_name="the Long Blue River", affords={"lift", "float", "stitch"}),
    "mill": Setting(place="the old mill", weather="windy", river_name="the Long Blue River", affords={"lift", "stitch"}),
    "field": Setting(place="the north field", weather="sunny", river_name="the Long Blue River", affords={"float", "lift"}),
}

TRANSFORMATIONS = {
    "stretch": Transformation(
        id="stretch",
        from_form="self",
        to_form="long-necked crane",
        label="a long-necked crane",
        meters_gain={"reach": 2.0, "steadiness": -0.2},
        memes_gain={"surprise": 1.0, "pride": 0.5},
        reason="to reach the high rope",
    ),
    "shrink": Transformation(
        id="shrink",
        from_form="self",
        to_form="tiny fox",
        label="a tiny fox",
        meters_gain={"smallness": 2.0, "speed": 1.0},
        memes_gain={"surprise": 0.8, "trust": 0.4},
        reason="to slip under the gate",
    ),
    "grow": Transformation(
        id="grow",
        from_form="self",
        to_form="towering ox",
        label="a towering ox",
        meters_gain={"strength": 2.0, "load": 2.0},
        memes_gain={"surprise": 0.7, "pride": 0.6},
        reason="to haul the heavy sack",
    ),
    "glimmer": Transformation(
        id="glimmer",
        from_form="self",
        to_form="silver goose",
        label="a silver goose",
        meters_gain={"lightness": 1.5, "reach": 1.0},
        memes_gain={"surprise": 1.2, "delight": 0.8},
        reason="to skim above the river water",
    ),
}

TASKS = {
    "rope": Task(
        id="rope",
        label="the towrope",
        problem="The towrope had snagged high on a post.",
        risk="If it stayed stuck, the mill wheel would not turn.",
        needs={"reach", "steadiness"},
        surprise_key="gift",
    ),
    "grain": Task(
        id="grain",
        label="the grain sacks",
        problem="The grain sacks had slipped downriver in a gust.",
        risk="If nobody could fetch them, supper would be thin.",
        needs={"speed", "strength"},
        surprise_key="gift",
    ),
    "wheel": Task(
        id="wheel",
        label="the mill wheel",
        problem="The mill wheel had leaned crooked in the mud.",
        risk="If it stayed crooked, the stones would grind nothing.",
        needs={"strength", "load"},
        surprise_key="gift",
    ),
}

HELPERS = {
    "cat": Helper(id="cat", label="cat", help_text="It could slip through narrow places.", transform="shrink"),
    "goose": Helper(id="goose", label="goose", help_text="It could flutter high and carry a ribbon.", transform="glimmer"),
    "mule": Helper(id="mule", label="mule", help_text="It could pull hard with steady legs.", transform="grow"),
}

HERO_NAMES = ["Amos", "Mina", "Otto", "Iris"]
TRAITS = ["proper", "bold", "calm", "spry", "kind"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    task: str
    hero: str
    helper_a: str
    helper_b: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP rules and facts
# ---------------------------------------------------------------------------

ASP_RULES = r"""
needs(Task, Meter) :- task(Task), task_needs(Task, Meter).

can_solve(Task, Trio) :- task(Task), trio(Trio),
                         helper_transform(Trio, H1, M1), gives(H1, M1),
                         helper_transform(Trio, H2, M2), H1 != H2, gives(H2, M2),
                         helper_transform(Trio, H3, M3), H3 != H1, H3 != H2, gives(H3, M3),
                         task_needs(Task, N1), gives(H1, N1) : helper_transform(Trio, H1, _);
                         task_needs(Task, N2), gives(H2, N2) : helper_transform(Trio, H2, _);
                         task_needs(Task, N3), gives(H3, N3) : helper_transform(Trio, H3, _).

proper_story(P, T) :- place(P), task(T), valid_combo(P, T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("place", sid))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        for need in sorted(task.needs):
            lines.append(asp.fact("task_needs", tid, need))
    for tid, tr in TRANSFORMATIONS.items():
        lines.append(asp.fact("transform", tid))
        lines.append(asp.fact("to_form", tid, tr.to_form))
        for m, v in tr.meters_gain.items():
            if v > 0:
                lines.append(asp.fact("gives", tid, m))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_transform", "trio1", hid, helper.transform))
    for p in SETTINGS:
        for t in TASKS:
            lines.append(asp.fact("valid_combo", p, t))
    lines.append(asp.fact("trio", "trio1"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def trio_supports(task: Task, trio: tuple[str, str, str]) -> bool:
    meters = set()
    for tid in trio:
        meters |= {m for m, v in TRANSFORMATIONS[tid].meters_gain.items() if v > 0}
    return task.needs.issubset(meters)


def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p in SETTINGS for t in TASKS]


def story_from_world(world: World) -> str:
    return world.render()


def _apply_transformation(world: World, ent: Entity, t: Transformation) -> None:
    ent.transformed = True
    ent.form = t.to_form
    for k, v in t.meters_gain.items():
        ent.meters[k] = ent.meters.get(k, 0.0) + v
    for k, v in t.memes_gain.items():
        ent.memes[k] = ent.memes.get(k, 0.0) + v


def _synergy(world: World, hero: Entity, helpers: list[Entity], task: Task) -> bool:
    have = set()
    for e in [hero] + helpers:
        have |= {m for m, v in e.meters.items() if v >= THRESHOLD}
    return task.needs.issubset(have)


def _discover_surprise(world: World, hero: Entity, helpers: list[Entity], task: Task) -> None:
    world.facts["surprise"] = True
    hero.memes["delight"] = hero.memes.get("delight", 0.0) + 1.5
    for h in helpers:
        h.memes["delight"] = h.memes.get("delight", 0.0) + 1.0
        h.memes["trust"] = h.memes.get("trust", 0.0) + 1.0
    world.say(
        f"Then came the surprise: the snag was not a snare at all, but a ribbon-tied bundle from upstream."
    )
    world.say(
        f"It had been riding the river just to find proper hands. The whole little company laughed, "
        f"for their teamwork had made room enough to catch it."
    )


# ---------------------------------------------------------------------------
# Narrative beats
# ---------------------------------------------------------------------------

def setup(world: World, hero: Entity, helpers: list[Entity], task: Task) -> None:
    world.say(
        f"Proper {hero.label} lived by {world.setting.place}, where {world.setting.river_name} "
        f"went whistling past like a long blue fiddle."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} was a {hero.memes.get('trait_word', 'proper')} sort who never left a job half-done."
    )
    helper_names = " and ".join(h.label for h in helpers)
    world.say(
        f"Beside {hero.pronoun('object')} worked {helper_names}, and each one knew a different trick."
    )
    world.say(f"One morning, {task.problem} {task.risk}")


def worry(world: World, hero: Entity, task: Task) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    world.say(
        f"Amos put a hand to {hero.pronoun('possessive')} chin and said, "
        f'"This calls for a proper plan, not a strong arm alone."'
    )


def teamwork(world: World, hero: Entity, helpers: list[Entity], task: Task) -> None:
    world.say(
        f"So the little company set to work together."
    )
    for helper in helpers:
        t = TRANSFORMATIONS[HELPERS[helper.id].transform]
        _apply_transformation(world, helper, t)
        world.say(
            f"The {helper.label} became {t.label} {t.reason}, and that gave the team new reach."
        )
    # hero changes too, if needed
    hero_t = TRANSFORMATIONS["stretch"] if task.id == "rope" else TRANSFORMATIONS["grow"] if task.id == "wheel" else TRANSFORMATIONS["shrink"]
    _apply_transformation(world, hero, hero_t)
    world.say(
        f"Then Amos himself turned into {hero_t.label}, because a proper fix sometimes asks the leader to change shape too."
    )


def resolve(world: World, hero: Entity, helpers: list[Entity], task: Task) -> None:
    if not _synergy(world, hero, helpers, task):
        raise StoryError("the chosen transformations do not support this task")
    world.say(
        f"Together they solved {task.label}: one held, one pulled, one steadied, and Amos guided the rest."
    )
    _discover_surprise(world, hero, helpers, task)
    world.say(
        f"By evening the river was flowing sweetly again, and the little team stood shining in the last light."
    )


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

def tell(setting: Setting, task: Task, hero_name: str, helper_ids: list[str], trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        label=hero_name,
        role="leader",
        meters={"steadiness": 1.0},
        memes={"trait_word": trait, "pride": 0.5},
    ))
    helpers = [
        world.add(Entity(id=f"helper_{i}", kind="character", label=HELPERS[h].label, role=h))
        for i, h in enumerate(helper_ids, 1)
    ]

    world.facts.update(hero=hero_name, task=task.id, place=setting.place, helpers=helper_ids, trait=trait)
    setup(world, hero, helpers, task)
    world.para()
    worry(world, hero, task)
    teamwork(world, hero, helpers, task)
    world.para()
    resolve(world, hero, helpers, task)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short tall tale for children about {f["hero"]}, {f["task"]}, and a surprising gift from the river.',
        f'Tell a proper old-time story where teamwork makes a changing shape solve {f["task"]}.',
        f'Write a funny tall tale that includes the word "proper" and ends with an unexpected river surprise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    task = TASKS[f["task"]]
    qas = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero}, who lives by {world.setting.place} and works with helpers to fix {task.label}.",
        ),
        QAItem(
            question=f"What was wrong at the start of the story?",
            answer=f"{task.problem} {task.risk}",
        ),
        QAItem(
            question=f"What did the team do to solve the problem?",
            answer="They changed shape in proper ways, worked together, and used each new form to do a different job.",
        ),
        QAItem(
            question=f"What was the surprise at the end?",
            answer="The trouble was really a ribbon-tied bundle from upstream, and it turned out to be a gift.",
        ),
    ]
    return qas


WORLD_KNOWLEDGE = {
    "proper": [
        QAItem(
            question="What does it mean to do something properly?",
            answer="Doing something properly means doing it in the right way, with care and attention.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people work together and help each other reach the same goal.",
        )
    ],
    "surprise": [
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you do not expect, so it can make you gasp or smile.",
        )
    ],
    "transformation": [
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another form.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [*WORLD_KNOWLEDGE["proper"], *WORLD_KNOWLEDGE["teamwork"], *WORLD_KNOWLEDGE["surprise"], *WORLD_KNOWLEDGE["transformation"]]


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
# ASP verification
# ---------------------------------------------------------------------------

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld with transformation, teamwork, and surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--helper-a", dest="helper_a", choices=list(HELPERS))
    ap.add_argument("--helper-b", dest="helper_b", choices=list(HELPERS))
    ap.add_argument("--trait", choices=TRAITS)
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
    choices = [(p, t) for p, t in valid_combos()
               if (args.place is None or p == args.place)
               and (args.task is None or t == args.task)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    place, task = rng.choice(choices)
    hero = args.hero or rng.choice(HERO_NAMES)
    helper_names = list(HELPERS)
    if args.helper_a and args.helper_b and args.helper_a == args.helper_b:
        raise StoryError("helper-a and helper-b must be different")
    helper_a = args.helper_a or rng.choice(helper_names)
    helper_b = args.helper_b or rng.choice([h for h in helper_names if h != helper_a])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, hero=hero, helper_a=helper_a, helper_b=helper_b, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        TASKS[params.task],
        params.hero,
        [params.helper_a, params.helper_b],
        params.trait,
    )
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
        bits = []
        if e.form != "self":
            bits.append(f"form={e.form}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.label}) {' '.join(bits)}")
    if world.facts:
        lines.append(f"  facts={world.facts}")
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
        print(asp_program("#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, task) combos:\n")
        for place, task in combos:
            print(f"  {place:10} {task}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("riverbend", "rope", "Amos", "cat", "goose", "proper"),
            StoryParams("mill", "wheel", "Mina", "mule", "cat", "proper"),
            StoryParams("field", "grain", "Otto", "goose", "mule", "proper"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
