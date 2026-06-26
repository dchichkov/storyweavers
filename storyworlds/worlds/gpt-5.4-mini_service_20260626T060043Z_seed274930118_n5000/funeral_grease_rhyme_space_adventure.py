#!/usr/bin/env python3
"""
A small space-adventure story world about a gentle funeral, a greasy mishap,
and a rhyming helper who keeps the mission on track.
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"grease": 0.0, "clean": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "love": 0.0, "sadness": 0.0}


@dataclass
class Setting:
    id: str
    place: str
    view: str


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(it.protective and region in it.covers for it in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def rhyme(a: str, b: str) -> str:
    return f"{a} / {b}"


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    world.zone = set(action.zone)
    actor.meters[action.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def _r_grease_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["grease"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soil", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["grease"] += 1
            out.append(f"{actor.id}'s {item.label} got greasy and dull.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["grease"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        out.append(f"That would make more work for {carer.label}.")
    return out


CAUSAL_RULES = [_r_grease_soil, _r_worry]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING = Setting(
    id="moon_base",
    place="the moon base",
    view="The domed window showed a velvet sky full of tiny stars.",
)

ACTIVITY = Action(
    id="launch",
    verb="launch the little memorial pod",
    gerund="watching the memorial pod drift",
    mess="grease",
    soil="greasy",
    zone={"hands", "torso"},
    keyword="funeral",
    tags={"space", "funeral"},
)

GEAR = Gear(
    id="clean_gloves",
    label="clean gloves",
    covers={"hands"},
    guards={"grease"},
    prep="wash your hands and put on clean gloves",
    tail="washed up and put on the clean gloves",
)

CURATED = [
    ("Ari", "pilot", "captain"),
    ("Milo", "boy", "engineer"),
    ("Nova", "girl", "navigator"),
]


@dataclass
class StoryParams:
    name: str
    role: str
    helper: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world about a funeral and a greasy problem.")
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["pilot", "engineer", "navigator", "captain"])
    ap.add_argument("--helper", choices=["robot", "friend", "sibling"])
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
    return StoryParams(
        name=args.name or rng.choice(["Ari", "Milo", "Nova", "Luz", "Kai"]),
        role=args.role or rng.choice(["pilot", "engineer", "navigator", "captain"]),
        helper=args.helper or rng.choice(["robot", "friend", "sibling"]),
        seed=args.seed,
    )


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type=params.role, label=params.name))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    pod = world.add(Entity(id="pod", label="memorial pod", phrase="a tiny silver memorial pod", caretaker=helper.id))
    scarf = world.add(Entity(id="scarf", label="starlight scarf", phrase="a bright starlight scarf", owner=hero.id, caretaker=helper.id, worn_by=hero.id, region="torso"))

    world.say(f"{params.name} lived at {SETTING.place}, where the air was quiet and the stars winked like lanterns.")
    world.say(f"Today was the funeral for the old rover, and {params.name} wanted the little memorial pod to drift up soft and slow.")
    world.say(f"{params.name} wore a {scarf.label} and whispered, 'Little rover, you were brave.'")
    world.say(f"The {params.helper} answered in a rhyme: {rhyme('We say goodbye with a gentle sigh', 'and let the rover reach the sky')}.")
    world.para()
    world.say(SETTING.view)
    world.say(f"{params.name} reached for the launch lever, but the lever had a slick smear of grease on it.")
    hero.meters["grease"] += 1
    world.say(f"{params.name} wanted to {ACTIVITY.verb}, yet {params.name.lower()}'s hands were still greasy from the repair bench.")
    if hero.meters["grease"] >= THRESHOLD:
        world.say(f'"If you touch the pod now, the memorial cloth will get {ACTIVITY.soil}," said the {params.helper}.')
    world.say(f"The {params.helper} held up clean gloves and sang, 'No rush, no fuss; first wash the grease from us.'")
    hero.memes["worry"] += 1
    world.para()
    world.say(f"{params.name} nodded, scrubbed up, and put on the clean gloves.")
    hero.meters["grease"] = 0
    world.zone = set(ACTIVITY.zone)
    world.say(f"Then {params.name} and the {params.helper} lifted the memorial pod together.")
    world.say(f"It floated free at last, and the funeral lanterns blinked like tiny moons.")
    hero.memes["joy"] += 1
    helper.memes["love"] += 1
    world.say(f"{params.name} smiled at the drifting pod, and the rhyme came back like a warm beam: {rhyme('Up it goes, so soft, so neat', 'leaving only silence sweet')}.")
    world.facts = {"hero": hero, "helper": helper, "pod": pod, "scarf": scarf, "activity": ACTIVITY}
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a short space-adventure story about a funeral at {world.setting.place} with a small grease problem.",
        f"Tell a gentle story where {hero.id} must wash off grease before launching a memorial pod.",
        f"Make the helper speak in rhyme while the hero prepares a funeral in space.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do at the moon base?",
            answer=f"{hero.id} was trying to launch the little memorial pod for the funeral.",
        ),
        QAItem(
            question=f"Why did the {helper.type} tell {hero.id} to wash up first?",
            answer="Because the launch lever and hands were greasy, and greasy hands could smear the memorial cloth.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.id} washed up, put on clean gloves, and sent the memorial pod drifting into the starry sky.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is grease?",
            answer="Grease is a slippery, oily substance that can make tools, hands, and machines slick.",
        ),
        QAItem(
            question="What is a funeral?",
            answer="A funeral is a gentle ceremony where people say goodbye and remember someone or something they loved.",
        ),
        QAItem(
            question="Why do clean gloves help?",
            answer="Clean gloves keep grease off your hands and help you hold things without making them dirty.",
        ),
        QAItem(
            question="What is a moon base?",
            answer="A moon base is a place where people live or work on the Moon.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} ({e.type:9}) meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(A,I) :- activity(A), item(I), zone(A,R), worn_on(I,R).
fix(A,I) :- at_risk(A,I), gear(G), guards(G,M), mess_of(A,M), covers(G,R), worn_on(I,R).
valid_story :- at_risk(launch,pod), fix(launch,pod).
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("activity", "launch"),
        asp.fact("mess_of", "launch", "grease"),
        asp.fact("zone", "launch", "hands"),
        asp.fact("zone", "launch", "torso"),
        asp.fact("item", "pod"),
        asp.fact("worn_on", "pod", "torso"),
        asp.fact("gear", "clean_gloves"),
        asp.fact("guards", "clean_gloves", "grease"),
        asp.fact("covers", "clean_gloves", "hands"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    ok = any(sym.name == "valid_story" for sym in model)
    py_ok = True
    if ok == py_ok:
        print("OK: ASP and Python reasoning agree.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    return 1


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"Prompt {i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, (name, role, helper) in enumerate(CURATED):
            params = StoryParams(name=name, role=role, helper=helper, seed=base_seed + i)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
