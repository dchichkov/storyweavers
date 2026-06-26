#!/usr/bin/env python3
"""
storyworlds/worlds/row_moral_value_superhero_story.py
=====================================================

A small superhero story world built around a row, a moral value, and a choice
to use power kindly instead of selfishly.

Premise:
- A hero is in a row of people waiting for a community event.
- Someone tries to cut ahead or push through the line.
- The hero can react with force, but the better choice is fairness and patience.
- The ending proves the moral value changed the outcome.

The model tracks physical meters and emotional memes:
- meters: distance, disarray, saved items, line order, interruption
- memes: patience, fairness, pride, anger, kindness, relief

The stories are intentionally simple, child-facing, and state-driven.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    event: str


@dataclass
class Problem:
    id: str
    verb: str
    rush: str
    mess: str
    risk: str
    moral: str


@dataclass
class Aid:
    id: str
    label: str
    action: str
    effect: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


SETTINGS = {
    "city": Setting(place="the city plaza", event="community day"),
    "station": Setting(place="the train station", event="toy drive"),
    "school": Setting(place="the school gym", event="talent show"),
    "market": Setting(place="the market hall", event="help day"),
}

PROBLEMS = {
    "row": Problem(
        id="row",
        verb="stand patiently in the row",
        rush="push ahead in the row",
        mess="the line gets jumbled",
        risk="someone gets bumped and the waiting kids get upset",
        moral="fairness means letting each person have a turn",
    ),
}

AIDS = {
    "calm": Aid(
        id="calm",
        label="calm words",
        action="remind everyone to breathe and wait",
        effect="the row becomes steady again",
    ),
    "sign": Aid(
        id="sign",
        label="a clear sign",
        action="hold up a sign that points to the end of the row",
        effect="the crowd knows where to stand",
    ),
    "escort": Aid(
        id="escort",
        label="a gentle escort",
        action="walk the lost person to the back of the row",
        effect="the line stops twisting and straightens out",
    ),
}

HERO_TYPES = ["girl", "boy"]
HERO_NAMES = {
    "girl": ["Maya", "Lina", "Zoe", "Ava", "Nia"],
    "boy": ["Leo", "Noah", "Eli", "Max", "Finn"],
}
ALLY_NAMES = ["Captain Sun", "Night Kite", "Blue Lantern", "Spark Shield"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    hero_name: str
    hero_type: str
    ally: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero story about a row and a moral value.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--ally", choices=ALLY_NAMES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or "row"
    if problem != "row":
        raise StoryError("Only the row story is valid in this world.")

    gender = args.gender or rng.choice(HERO_TYPES)
    name = args.name or rng.choice(HERO_NAMES[gender])
    ally = args.ally or rng.choice(ALLY_NAMES)
    return StoryParams(setting=setting, problem=problem, hero_name=name, hero_type=gender, ally=ally)


def _do_help(world: World, hero: Entity, ally: Entity, aid: Aid) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    hero.memes["patience"] = hero.memes.get("patience", 0.0) + 1
    world.say(f"{ally.id} showed up beside {hero.id}, and together they chose {aid.label}.")
    world.say(f"They {aid.action}, and soon {aid.effect}.")


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"order": 1.0},
        memes={"patience": 0.0, "fairness": 0.0, "anger": 0.0, "relief": 0.0},
    ))
    ally = world.add(Entity(
        id=params.ally,
        kind="character",
        type="hero",
        label=params.ally,
        memes={"wisdom": 1.0},
    ))
    villain = world.add(Entity(
        id="Rusher",
        kind="character",
        type="villain",
        label="the pushy rusher",
        meters={"distance": 0.0},
        memes={"impulse": 1.0, "impatience": 1.0},
    ))

    problem = PROBLEMS[params.problem]

    world.say(f"At {setting.place}, it was {setting.event}, and a long row waited under the bright sky.")
    world.say(f"{hero.id} was in the row because {hero.pronoun('subject')} wanted to do the right thing and wait for {hero.pronoun('possessive')} turn.")
    world.say(f"{hero.id} loved being a small hero, and {hero.pronoun('subject')} knew that {problem.moral}.")

    world.para()
    world.say(f"Then {villain.label} tried to {problem.rush} and skip the line.")
    hero.memes["anger"] += 1
    hero.memes["fairness"] += 1
    world.say(f"The row got tense, and {problem.risk}.")
    world.say(f"{hero.id} felt the hot tug of anger, but {hero.pronoun('subject')} remembered that {problem.moral}.")

    world.para()
    aid = AIDS["calm"] if params.setting in {"city", "school"} else AIDS["escort"]
    if params.setting == "market":
        aid = AIDS["sign"]
    _do_help(world, hero, ally, aid)
    hero.memes["anger"] = 0.0
    hero.memes["relief"] += 1

    world.say(f"{villain.label} looked down at the straightened row and finally moved to the back.")
    world.say(f"{hero.id} stood taller, not because {hero.pronoun('subject')} used force, but because {hero.pronoun('subject')} used fairness.")
    world.say(f"By the time the turn came, the row was calm again, and {hero.id} smiled at the good ending.")

    world.facts.update(
        hero=hero,
        ally=ally,
        villain=villain,
        setting=setting,
        problem=problem,
        aid=aid,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    setting = f["setting"]
    return [
        f"Write a short superhero story about {hero.id} waiting in a row at {setting.place}.",
        f"Tell a child-friendly tale where a hero chooses fairness over anger during {setting.event}.",
        f"Write a gentle story about a row, a moral value, and a superhero who helps the line stay fair.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    ally = f["ally"]
    villain = f["villain"]
    setting = f["setting"]
    aid = f["aid"]
    problem = f["problem"]
    return [
        QAItem(
            question=f"Where was {hero.id} waiting when the row trouble started?",
            answer=f"{hero.id} was waiting at {setting.place} during {setting.event}.",
        ),
        QAItem(
            question=f"What did {villain.label} try to do in the row?",
            answer=f"{villain.label} tried to {problem.rush}.",
        ),
        QAItem(
            question=f"How did {hero.id} and {ally.id} fix the row problem?",
            answer=f"They used {aid.label} and chose to {aid.action}, which made {aid.effect}.",
        ),
        QAItem(
            question=f"What moral value helped {hero.id} make the right choice?",
            answer=f"Fairness helped {hero.id} stay calm and wait for a turn instead of getting pushed into anger.",
        ),
    ]


WORLD_QA = [
    QAItem(
        question="What is fairness?",
        answer="Fairness means giving people a fair turn and treating them kindly and equally.",
    ),
    QAItem(
        question="What does a superhero do?",
        answer="A superhero uses brave actions to help others and protect people from trouble.",
    ),
    QAItem(
        question="What is a row?",
        answer="A row is a line of people or things waiting one behind another.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_QA)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_waiting(H) :- hero(H).
row_problem(row).
moral_value(fairness).
fix(H) :- hero(H), uses(H, fairness).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid))
    lines.append(asp.fact("moral_value", "fairness"))
    lines.append(asp.fact("row_topic", "row"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Lazy import inside ASP helpers
    import asp
    model = asp.one_model(asp_program("#show moral_value/1."))
    atoms = set(asp.atoms(model, "moral_value"))
    expected = {("fairness",)}
    if atoms != expected:
        print("MISMATCH between ASP and Python gate")
        print("  asp:", sorted(atoms))
        print("  py :", sorted(expected))
        return 1
    print("OK: ASP twin recognizes the moral value gate.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


CURATED = [
    StoryParams(setting="city", problem="row", hero_name="Maya", hero_type="girl", ally="Captain Sun"),
    StoryParams(setting="school", problem="row", hero_name="Leo", hero_type="boy", ally="Blue Lantern"),
    StoryParams(setting="market", problem="row", hero_name="Nia", hero_type="girl", ally="Night Kite"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show moral_value/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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
            samples.append(generate(params))

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
            header = f"### {p.hero_name}: {p.problem} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
