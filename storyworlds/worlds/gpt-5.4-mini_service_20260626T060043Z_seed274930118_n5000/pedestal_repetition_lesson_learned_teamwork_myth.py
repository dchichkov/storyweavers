#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pedestal_repetition_lesson_learned_teamwork_myth.py
================================================================================================

A small mythic storyworld about a pedestal, repetition, a lesson learned,
and teamwork.

Seed tale:
---
Long ago, in a bright temple courtyard, a young apprentice named Ilya wanted to
lift a shining stone idol onto a pedestal. The pedestal stood waiting in the sun,
but the idol was heavy, and each solo attempt ended in a wobble and a thud.
Ilya tried again and again, growing frustrated. Then the elder priest smiled and
said the idol did not ask for strength alone; it asked for patience and friends.

So Ilya gathered two helpers. One steadied the base, one guided the top, and
Ilya counted the steps out loud. Together they lifted the idol, placed it on the
pedestal, and the whole courtyard seemed to breathe easier. Ilya learned that
some tasks need repetition to teach the hands, and teamwork to finish the work.

This script turns that premise into a tiny simulated world with meters and
memes, a reasonableness gate, and an inline ASP twin.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    on: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "priest", "apprentice"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the temple courtyard"
    light: str = "golden"
    affords: set[str] = field(default_factory=lambda: {"lift", "carry", "place"})


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    attempt: str
    outcome_fail: str
    outcome_success: str
    strain: str
    requires_teamwork: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    position: str = "floor"
    plural: bool = False


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    role: str
    assistance: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


TASKS = {
    "lift_idol": Task(
        id="lift_idol",
        verb="lift the idol onto the pedestal",
        gerund="lifting the idol",
        attempt="try to lift the idol again",
        outcome_fail="wobble and thud back down",
        outcome_success="rest on the pedestal",
        strain="heavy",
        tags={"idol", "pedestal", "teamwork", "repetition"},
    ),
    "raise_brazier": Task(
        id="raise_brazier",
        verb="raise the brazier onto the pedestal",
        gerund="raising the brazier",
        attempt="try to raise the brazier again",
        outcome_fail="slip and clang on the stone",
        outcome_success="rest safely on the pedestal",
        strain="awkward",
        tags={"brazier", "pedestal", "teamwork", "repetition"},
    ),
    "set_crown": Task(
        id="set_crown",
        verb="set the crown upon the pedestal",
        gerund="setting the crown",
        attempt="try to set the crown again",
        outcome_fail="tilt and slide to the floor",
        outcome_success="sit bright and still",
        strain="delicate",
        tags={"crown", "pedestal", "teamwork", "repetition"},
    ),
}

PRIZES = {
    "idol": Prize(label="idol", phrase="a shining stone idol", type="idol", position="floor"),
    "brazier": Prize(label="brazier", phrase="a bronze brazier", type="brazier", position="floor"),
    "crown": Prize(label="crown", phrase="a small moon-crown", type="crown", position="table"),
}

HELPERS = {
    "elder": Helper(id="elder", label="elder", phrase="the elder priest", role="wise guide", assistance="counted the steps"),
    "friend": Helper(id="friend", label="friend", phrase="a strong friend", role="steady helper", assistance="held the base"),
    "singer": Helper(id="singer", label="singer", phrase="a clear-voiced singer", role="timing helper", assistance="kept the rhythm"),
}

NAMES = ["Ilya", "Mara", "Tavi", "Niko", "Sera", "Anya", "Dorian", "Lumen"]
TITLES = ["apprentice", "boy", "girl"]
TRAITS = ["patient", "brave", "earnest", "stubborn", "humble", "curious"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for task in TASKS:
        for prize in PRIZES:
            if task == "lift_idol" and prize == "idol":
                combos.append(("courtyard", task))
            elif task == "raise_brazier" and prize == "brazier":
                combos.append(("courtyard", task))
            elif task == "set_crown" and prize == "crown":
                combos.append(("courtyard", task))
    return combos


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    helper1: str
    helper2: str
    name: str
    title: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld about a pedestal, repetition, lesson learned, and teamwork.")
    ap.add_argument("--place", choices=["courtyard"])
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--helper1", choices=HELPERS)
    ap.add_argument("--helper2", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--title", choices=TITLES)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.task and args.prize:
        if (args.task, args.prize) not in [(t, p) for _, t in valid_combos() for p in [args.prize]]:
            pass
    place = args.place or "courtyard"
    combos = valid_combos()
    if args.task:
        combos = [c for c in combos if c[1] == args.task]
    if args.prize:
        combos = [c for c in combos if args.prize == ("idol" if c[1] == "lift_idol" else "brazier" if c[1] == "raise_brazier" else "crown")]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    _, task = rng.choice(combos)
    prize = "idol" if task == "lift_idol" else "brazier" if task == "raise_brazier" else "crown"
    name = args.name or rng.choice(NAMES)
    title = args.title or rng.choice(TITLES)
    trait = args.trait or rng.choice(TRAITS)
    helper_ids = list(HELPERS)
    h1 = args.helper1 or rng.choice(helper_ids)
    h2 = args.helper2 or rng.choice([h for h in helper_ids if h != h1])
    return StoryParams(place=place, task=task, prize=prize, helper1=h1, helper2=h2, name=name, title=title, trait=trait)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place != "courtyard":
        raise StoryError("This mythic lesson belongs in the temple courtyard.")
    if params.task not in TASKS:
        raise StoryError("Unknown task.")
    if params.prize not in PRIZES:
        raise StoryError("Unknown prize.")


def _repeat_attempts(world: World, hero: Entity, task: Task, prize: Entity) -> None:
    hero.memes["frustration"] += 1
    world.say(f"{hero.id} tried to {task.verb}, but the work was too {task.strain}; {task.outcome_fail}.")
    world.say(f"{hero.id} stepped back and said, 'I will try again.'")
    world.say(f"Then {hero.id} tried again, and again, and again.")
    hero.memes["repetition"] += 3


def _teamwork_succeeds(world: World, hero: Entity, task: Task, prize: Entity, helper1: Entity, helper2: Entity) -> None:
    hero.memes["teamwork"] += 1
    helper1.memes["teamwork"] += 1
    helper2.memes["teamwork"] += 1
    world.say(f"{helper1.pronoun().capitalize()} {world.facts['helper1_phrase']} while {helper2.pronoun().capitalize()} {world.facts['helper2_phrase']}.")
    world.say(f"At last, the three of them counted together, lifted together, and the {prize.label} could {task.outcome_success}.")
    hero.memes["lesson"] += 1
    hero.memes["joy"] += 1


def tell(params: StoryParams) -> World:
    world = World(Setting())
    hero = world.add(Entity(id=params.name, kind="character", type=params.title, traits=["little", params.trait]))
    helper1 = world.add(Entity(id=params.helper1, kind="character", type="priest" if params.helper1 == "elder" else "friend", label=HELPERS[params.helper1].phrase))
    helper2 = world.add(Entity(id=params.helper2, kind="character", type="priest" if params.helper2 == "elder" else "singer", label=HELPERS[params.helper2].phrase))
    task = TASKS[params.task]
    prize = world.add(Entity(id=params.prize, type=params.prize, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase, owner=hero.id))
    pedestal = world.add(Entity(id="pedestal", type="pedestal", label="pedestal", phrase="a sun-warm pedestal", position="center"))
    prize.on = None
    world.facts["helper1_phrase"] = HELPERS[params.helper1].assistance
    world.facts["helper2_phrase"] = HELPERS[params.helper2].assistance

    world.say(f"Long ago, in {world.setting.place}, {hero.id} was a {hero.trait := hero.traits[1]} {hero.type} who looked up at the pedestal and the {prize.label}.")
    world.say(f"{hero.id} wanted to {task.verb}, because the {prize.label} belonged where light could find it.")
    world.para()
    _repeat_attempts(world, hero, task, prize)
    world.say(f"The pedestal stayed still, as old stone does, and the {prize.label} did not move.")
    world.para()
    world.say(f"Then {HELPERS[params.helper1].phrase} arrived, and {HELPERS[params.helper2].phrase} came beside {hero.pronoun('object')}.")
    world.say(f"They did not laugh at the failed tries; they taught {hero.id} that repetition can train the hands, but teamwork finishes the job.")
    _teamwork_succeeds(world, hero, task, prize, helper1, helper2)
    prize.on = pedestal.id

    world.facts.update(hero=hero, helper1=helper1, helper2=helper2, prize=prize, pedestal=pedestal, task=task, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    prize = f["prize"]
    return [
        f'Write a short myth for a child about {hero.id}, a pedestal, and how {task.gerund} taught patience.',
        f"Tell a gentle legend where {hero.id} keeps trying to {task.verb} until helpers arrive.",
        f'Write a mythic story that ends with {prize.label} safely on the pedestal and a lesson learned about teamwork.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    prize = f["prize"]
    h1 = f["helper1"]
    h2 = f["helper2"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {prize.label} and the pedestal?",
            answer=f"{hero.id} wanted to {task.verb}. The pedestal was waiting for the {prize.label} to rest on it.",
        ),
        QAItem(
            question=f"What happened before the helpers arrived?",
            answer=f"{hero.id} tried again and again to {task.verb}, but the work was too {task.strain} to finish alone.",
        ),
        QAItem(
            question=f"Who helped {hero.id} in the end?",
            answer=f"{h1.id} and {h2.id} helped {hero.id}, and together they completed the task.",
        ),
        QAItem(
            question="What lesson did the hero learn?",
            answer="The hero learned that repetition can teach the hands, but teamwork can finish the hardest work.",
        ),
        QAItem(
            question=f"Where was the {prize.label} at the end?",
            answer=f"At the end, the {prize.label} rested on the pedestal.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "pedestal": [
        QAItem(
            question="What is a pedestal?",
            answer="A pedestal is a raised stone or wooden stand that holds something important up high.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help one another and do a job together.",
        )
    ],
    "repetition": [
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing something again and again, often to learn or to improve.",
        )
    ],
    "lesson": [
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a helpful idea someone understands after what happened to them.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [qa for key in ["pedestal", "repetition", "lesson", "teamwork"] for qa in WORLD_KNOWLEDGE[key]]


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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.on:
            bits.append(f"on={e.on}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
repeated(hero) :- repetition(hero, N), N >= 3.
needs_teamwork(task) :- teamwork_task(task).
lesson_learned(hero) :- repeated(hero), helped(hero).
completed(task) :- success(task), teamwork_task(task).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for tid, task in TASKS.items():
        lines.append(asp.fact("teamwork_task", tid))
        for tag in task.tags:
            lines.append(asp.fact("tag", tid, tag))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    lines.append(asp.fact("pedestal", "pedestal"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show teamwork_task/1.\n#show prize/1.\n#show pedestal/1.")
    model = asp.one_model(program)
    seen_tasks = {a[0] for a in asp.atoms(model, "teamwork_task")}
    seen_prizes = {a[0] for a in asp.atoms(model, "prize")}
    if seen_tasks == set(TASKS) and seen_prizes == set(PRIZES):
        print("OK: ASP facts match registries.")
        return 0
    print("MISMATCH between ASP and registries.")
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show teamwork_task/1."))
    return sorted(set(asp.atoms(model, "teamwork_task")))


def build_story(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
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


CURATED = [
    StoryParams(place="courtyard", task="lift_idol", prize="idol", helper1="elder", helper2="friend", name="Ilya", title="apprentice", trait="patient"),
    StoryParams(place="courtyard", task="raise_brazier", prize="brazier", helper1="friend", helper2="singer", name="Mara", title="girl", trait="earnest"),
    StoryParams(place="courtyard", task="set_crown", prize="crown", helper1="elder", helper2="singer", name="Tavi", title="boy", trait="curious"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = CURATED[:]
    if args.task:
        combos = [p for p in combos if p.task == args.task]
    if args.prize:
        combos = [p for p in combos if p.prize == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    base = rng.choice(combos)
    return StoryParams(
        place=base.place,
        task=args.task or base.task,
        prize=args.prize or base.prize,
        helper1=args.helper1 or base.helper1,
        helper2=args.helper2 or base.helper2,
        name=args.name or base.name,
        title=args.title or base.title,
        trait=args.trait or base.trait,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show teamwork_task/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show teamwork_task/1."))
        print("Compatible mythic tasks:")
        for t in sorted(asp.atoms(model, "teamwork_task")):
            print(f"  {t[0]}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
