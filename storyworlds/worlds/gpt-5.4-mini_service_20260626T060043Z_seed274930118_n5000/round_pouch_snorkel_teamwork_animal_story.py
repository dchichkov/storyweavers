#!/usr/bin/env python3
"""
A small animal teamwork story world: a group of animals learns to use a round
pouch and a snorkel together to solve a watery problem.

The story is built from a simulated world model:
- animals have meters (physical state) and memes (feelings/social state)
- the round pouch can carry or float things
- the snorkel helps when water is deep
- teamwork is the turning point
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
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"rabbit", "mouse", "squirrel", "fox", "bear", "otter"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    water: str
    depth: str


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    floats: bool = False
    breathable: bool = False


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    task: str
    seed: Optional[int] = None


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
    "pond": Setting(place="the pond", water="water", depth="deep"),
    "riverbank": Setting(place="the riverbank", water="river water", depth="deep"),
    "creek": Setting(place="the creek", water="water", depth="shallow"),
    "lagoon": Setting(place="the lagoon", water="blue water", depth="deep"),
}

ANIMALS = {
    "rabbit": {"names": ["Pip", "Milo", "Nina", "Toby"], "traits": ["small", "quick", "kind"]},
    "otter": {"names": ["Ollie", "Luna", "Rae", "Mina"], "traits": ["playful", "curious", "brave"]},
    "squirrel": {"names": ["Coco", "Bram", "Penny", "Juno"], "traits": ["busy", "spirited", "clever"]},
    "bear": {"names": ["Moss", "Tara", "Hugo", "June"], "traits": ["strong", "gentle", "steady"]},
    "fox": {"names": ["Fenn", "Ivy", "Rory", "Sage"], "traits": ["sharp", "careful", "swift"]},
    "mouse": {"names": ["Dot", "Pip", "Tess", "Remy"], "traits": ["tiny", "helpful", "bright"]},
}

TASKS = {
    "fetch_shell": "fetch a shiny shell from the water",
    "carry_berries": "carry berries across the water",
    "reach_lily": "reach a lily drifting far out",
    "rescue_toy": "rescue a toy boat stuck in the reeds",
}

PROPS = {
    "round_pouch": Prop(
        id="round_pouch",
        label="round pouch",
        phrase="a round pouch with a soft strap",
        helps={"carry", "float"},
        floats=True,
    ),
    "snorkel": Prop(
        id="snorkel",
        label="snorkel",
        phrase="a long snorkel",
        helps={"breathe"},
        breathable=True,
    ),
    "berries": Prop(
        id="berries",
        label="berries",
        phrase="a small bundle of berries",
        helps={"carry"},
    ),
}


ASP_RULES = r"""
animal(A) :- animal_kind(A, _).
teamwork_needed(T) :- task(T), needs(T, carry), needs(T, breathe).
compatible(T, P) :- task(T), prop(P), needs(T, carry), carries(P).
compatible(T, P) :- task(T), prop(P), needs(T, breathe), breathes(P).
valid_story(Place, Hero, Helper, Task) :- setting(Place), animal_kind(Hero, _), animal_kind(Helper, _), Hero != Helper, task(Task).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("water", sid, s.water))
        lines.append(asp.fact("depth", sid, s.depth))
    for aid, a in ANIMALS.items():
        lines.append(asp.fact("animal_kind", aid, aid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if "carry" in p.helps:
            lines.append(asp.fact("carries", pid))
        if "breathe" in p.helps:
            lines.append(asp.fact("breathes", pid))
    lines.append(asp.fact("teamwork", "teamwork"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def one_teamwork_model() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    if not one_teamwork_model():
        print("MISMATCH: ASP produced no valid stories.")
        return 1
    print("OK: ASP produced valid story patterns.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal teamwork story world with a round pouch and snorkel.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--hero", choices=ANIMALS.keys())
    ap.add_argument("--helper", choices=ANIMALS.keys())
    ap.add_argument("--task", choices=TASKS.keys())
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
    hero = args.hero or rng.choice(list(ANIMALS))
    helper = args.helper or rng.choice([a for a in ANIMALS if a != hero])
    task = args.task or rng.choice(list(TASKS))
    if helper == hero:
        raise StoryError("The helper must be a different animal than the hero.")
    return StoryParams(place=place, hero=hero, helper=helper, task=task)


def story_name(hero: str) -> str:
    return ANIMALS[hero]["names"][0]


def trait(hero: str, rng: random.Random) -> str:
    return rng.choice(ANIMALS[hero]["traits"])


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero_name = story_name(params.hero)
    helper_name = story_name(params.helper)
    hero = world.add(Entity(id=hero_name, kind="character", type=params.hero, meters={"worry": 0.0}, memes={"hope": 0.0}))
    helper = world.add(Entity(id=helper_name, kind="character", type=params.helper, meters={"worry": 0.0}, memes={"hope": 0.0}))
    pouch = world.add(Entity(id="pouch", type="round_pouch", label="round pouch", phrase="the round pouch"))
    snorkel = world.add(Entity(id="snorkel", type="snorkel", label="snorkel", phrase="the snorkel"))

    hero.memes["curiosity"] = 1.0
    helper.memes["friendship"] = 1.0
    task_text = TASKS[params.task]

    world.say(f"{hero_name} was a {trait(params.hero, random.Random(7))} little {params.hero} who loved helping friends.")
    world.say(f"One day, {hero_name} and {helper_name} went to {setting.place}. They had a {pouch.label} and a {snorkel.label} ready for {task_text}.")
    world.para()
    world.say(f"The water was {setting.depth}, and the thing they needed was just out of reach.")
    hero.meters["problem"] = 1.0
    helper.meters["problem"] = 1.0
    hero.memes["worry"] = 1.0
    helper.memes["worry"] = 1.0

    if params.task in {"fetch_shell", "reach_lily", "rescue_toy"}:
        world.say(f"{hero_name} tried first, but the water was too deep.")
    else:
        world.say(f"{hero_name} could carry the berries alone, but it would be slow and wobbly.")

    world.para()
    hero.memes["teamwork"] = 1.0
    helper.memes["teamwork"] = 1.0
    if params.task == "carry_berries":
        world.say(f"{helper_name} held the {pouch.label} open while {hero_name} filled it with berries.")
        world.say(f"Then {hero_name} tucked the {pouch.label} under a paw and {helper_name} swam beside with the {snorkel.label} ready if splashes came up.")
    else:
        world.say(f"{helper_name} slipped on the {snorkel.label} and looked under the water while {hero_name} floated the {pouch.label} nearby.")
        world.say(f"Together they found the missing thing and brought it back safely.")

    hero.meters["success"] = 1.0
    helper.meters["success"] = 1.0
    hero.memes["joy"] = 1.0
    helper.memes["joy"] = 1.0
    world.para()
    world.say(f"At the end, the friends smiled at the {pouch.label} and the {snorkel.label}. Teamwork had made the hard job feel easy.")

    world.facts.update(
        hero=hero,
        helper=helper,
        pouch=pouch,
        snorkel=snorkel,
        task=params.task,
        setting=params.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story for a young child about teamwork, a {f["pouch"].label}, and a {f["snorkel"].label}.',
        f"Tell a gentle story where {f['hero'].id} and {f['helper'].id} solve a watery problem together.",
        f"Write a simple teamwork story set at {f['setting']} that ends with friends smiling beside a {f['pouch'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The story was about {hero.id} and {helper.id}, two animals who worked together.",
        ),
        QAItem(
            question=f"What tools did they have with them?",
            answer=f"They had a round pouch and a snorkel to help with the job.",
        ),
        QAItem(
            question=f"What made the ending happy?",
            answer=f"The ending was happy because the two animals used teamwork and solved the problem together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a snorkel for?",
            answer="A snorkel helps someone breathe while their face is in or near water.",
        ),
        QAItem(
            question="What can a round pouch be used for?",
            answer="A round pouch can carry small things and keep them together.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means two or more helpers work together to do something hard.",
        ),
    ]


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
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
    StoryParams(place="pond", hero="otter", helper="rabbit", task="fetch_shell"),
    StoryParams(place="creek", hero="squirrel", helper="otter", task="carry_berries"),
    StoryParams(place="lagoon", hero="mouse", helper="bear", task="reach_lily"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} + {p.helper} at {p.place} ({p.task})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
