#!/usr/bin/env python3
"""
A small fable-style story world about an auditorium, a lima bean, and a bit of chaos.

The seed tale:
A young squirrel named Pip was asked to carry a shining lima bean to the school auditorium
for a lesson day. Pip thought the bean looked too plain to matter and wanted to race ahead
into the crowd. But in the auditorium, noisy footsteps, dropped programs, and a wobbling
chair caused chaos. The lima bean rolled under a seat, the teacher paused, and Pip had to
choose between pride and patience. With a little help, Pip found the bean, restored calm,
and learned that small things can matter a great deal.

The world emphasizes:
- physical state: where the lima bean is, whether the stage is tidy, whether the room is noisy
- emotional state: pride, worry, patience, relief
- a clear fable turn and a lesson learned / moral value ending
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

AUDITORIUMS = {
    "small_auditorium": {
        "name": "the school auditorium",
        "features": {"stage", "rows", "curtains", "echo"},
    },
    "town_auditorium": {
        "name": "the town auditorium",
        "features": {"stage", "rows", "balcony", "echo"},
    },
}

CHARACTER_TYPES = {
    "squirrel": {"subject": "he", "object": "him", "possessive": "his"},
    "mouse": {"subject": "she", "object": "her", "possessive": "her"},
    "rabbit": {"subject": "they", "object": "them", "possessive": "their"},
    "crow": {"subject": "he", "object": "him", "possessive": "his"},
}

NAMES = ["Pip", "Mina", "Toby", "Luna", "Nell", "Bram", "Tess", "Otto"]

LESSONS = [
    "listen first",
    "carry things carefully",
    "slow steps save trouble",
    "small jobs can matter most",
]

MORALS = [
    "A little care can prevent a lot of chaos.",
    "Small things deserve big respect.",
    "When everyone helps, the room grows calm again.",
    "Patience is often the best way to keep a promise.",
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        pron = CHARACTER_TYPES.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})
        return pron[case]


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


@dataclass
class Setting:
    name: str
    features: set[str]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        chunks = []
        buf = []
        for line in self.lines:
            if line == "":
                if buf:
                    chunks.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            chunks.append(" ".join(buf))
        return "\n\n".join(chunks)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: an auditorium fable with a lima bean and chaos.")
    ap.add_argument("--setting", choices=sorted(AUDITORIUMS))
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=sorted(CHARACTER_TYPES))
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=sorted(CHARACTER_TYPES))
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in AUDITORIUMS.items():
        lines.append(asp.fact("setting", sid))
        for feat in sorted(s["features"]):
            lines.append(asp.fact("has_feature", sid, feat))
    return "\n".join(lines)


ASP_RULES = r"""
% A story is reasonable when it has an auditorium and the seed words at its core.
reasonable(S) :- setting(S).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reasonable/1."))
    settings = set(asp.atoms(model, "reasonable"))
    python = {(sid,) for sid in AUDITORIUMS}
    if settings == python:
        print(f"OK: clingo gate matches settings ({len(settings)}).")
        return 0
    print("MISMATCH between clingo and python")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(AUDITORIUMS))
    hero_type = args.hero_type or rng.choice(list(CHARACTER_TYPES))
    helper_type = args.helper_type or rng.choice(list(CHARACTER_TYPES))
    hero_name = args.name or rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice([n for n in NAMES if n != hero_name])
    return StoryParams(
        setting=setting,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def make_world(params: StoryParams) -> World:
    setting = Setting(name=AUDITORIUMS[params.setting]["name"], features=set(AUDITORIUMS[params.setting]["features"]))
    world = World(setting=setting)

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    bean = world.add(Entity(id="lima", type="lima bean", label="lima bean", phrase="a shining lima bean", owner=hero.id, location="hero"))
    teacher = world.add(Entity(id="teacher", kind="character", type="mouse", label="the teacher"))

    hero.memes.update({"pride": 1.0, "worry": 0.0, "patience": 0.0, "relief": 0.0, "lesson": 0.0})
    helper.memes.update({"calm": 1.0})
    bean.meters.update({"clean": 1.0, "safe": 1.0})
    world.facts.update(hero=hero, helper=helper, bean=bean, teacher=teacher)
    return world


def propagate(world: World) -> None:
    hero = world.get("hero")
    bean = world.get("lima")
    teacher = world.get("teacher")

    if hero.memes["pride"] >= 1.0 and hero.meters.get("running", 0.0) >= 1.0:
        hero.memes["worry"] = 1.0
        bean.location = "under_seat"
        bean.meters["safe"] = 0.0
        bean.meters["clean"] = 0.0
        teacher.memes["worry"] = 1.0

    if bean.location == "under_seat":
        hero.memes["patience"] = 1.0
        hero.memes["pride"] = 0.0

    if hero.memes["patience"] >= 1.0 and bean.location == "under_seat":
        bean.location = "in_hand"
        bean.meters["safe"] = 1.0
        hero.memes["relief"] = 1.0
        hero.memes["lesson"] = 1.0
        teacher.memes["worry"] = 0.0


def tell_story(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    bean = world.get("lima")
    teacher = world.get("teacher")

    world.say(f"Once, in {world.setting.name}, there lived a small {hero.type} named {hero.label}.")
    world.say(f"{hero.label} carried {bean.phrase} to the auditorium and thought it looked too tiny to matter.")
    world.say(f"{helper.label} said, \"Even little things can hold a lesson.\"")
    world.para()

    world.say(f"On the way to the stage, {hero.label} hurried ahead.")
    hero.meters["running"] = 1.0
    world.say(f"The room filled with noise, for the chairs scraped, the programs fluttered, and the echo grew into chaos.")
    propagate(world)
    if bean.location == "under_seat":
        world.say(f"In the rush, the lima bean rolled under a seat and disappeared from sight.")
        world.say(f"The teacher paused, and {hero.label} felt the proud feeling turn into worry.")
    world.para()

    world.say(f"{helper.label} pointed to the dark space beneath the chair and asked {hero.label} to slow down.")
    world.say(f"{hero.label} knelt, reached carefully, and found the lima bean where the floor was still and quiet.")
    propagate(world)
    world.say(f"Then the noise softened, the bean was safe again, and the auditorium felt calm.")
    world.say(f"{hero.label} learned that careful hands can save small treasures, and that wisdom often walks more slowly than pride.")
    world.say(f"Moral value: {MORALS[0] if hero.memes['lesson'] else MORALS[1]}")
    world.facts["lesson"] = LESSONS[3]
    world.facts["moral"] = MORALS[0]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    helper = world.get("helper")
    bean = world.get("lima")
    return [
        QAItem(
            question=f"Who carried the lima bean into the auditorium?",
            answer=f"{hero.label} carried the lima bean into {world.setting.name}.",
        ),
        QAItem(
            question=f"What caused the chaos in the auditorium?",
            answer="The rushing footsteps, scraping chairs, fluttering programs, and echoing noise caused the chaos.",
        ),
        QAItem(
            question=f"What did {helper.label} tell {hero.label} about the little bean?",
            answer=f"{helper.label} said that even little things can hold a lesson.",
        ),
        QAItem(
            question=f"Where did the lima bean roll during the trouble?",
            answer=f"It rolled under a seat in the auditorium.",
        ),
        QAItem(
            question="What lesson was learned by the end?",
            answer="The lesson learned was that careful hands and patience can save small treasures from trouble.",
        ),
        QAItem(
            question="What moral value does the story leave behind?",
            answer=world.facts.get("moral", MORALS[0]),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an auditorium?",
            answer="An auditorium is a large room built for people to listen, watch, or gather together.",
        ),
        QAItem(
            question="What is a lima bean?",
            answer="A lima bean is a small bean that can be cooked and eaten, and it is easy to carry in a story.",
        ),
        QAItem(
            question="What does chaos mean?",
            answer="Chaos means noisy confusion, when things are hard to control and everyone feels unsettled.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    hero = world.get("hero")
    return [
        "Write a fable about an auditorium, a lima bean, and a lesson learned.",
        f"Tell a short moral story where {hero.label} must handle a tiny lima bean during auditorium chaos.",
        "Create a child-friendly fable that ends with a moral value about patience and care.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell_story(world)
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
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== (2) Story questions ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")
        print("\n== (3) World knowledge ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")


CURATED = [
    StoryParams(setting="small_auditorium", hero_name="Pip", hero_type="squirrel", helper_name="Mina", helper_type="mouse"),
    StoryParams(setting="town_auditorium", hero_name="Toby", hero_type="crow", helper_name="Luna", helper_type="rabbit"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
