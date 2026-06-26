#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/victor_surround_misunderstanding_flashback_repetition_heartwarming.py
===============================================================================================================

A small heartwarming storyworld about Victor, a misunderstood protective gesture,
and a tender flashback that turns worry into gratitude.

Core premise:
- Victor wants to surround something fragile with a careful, cozy ring.
- Another character misunderstands the intent and thinks Victor is making a mess or blocking things in.
- A flashback reveals why Victor learned this habit.
- Repetition of a soothing phrase helps turn the moment warm and memorable.

This script is standalone and uses only the standard library plus the shared
Storyweavers result containers.
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
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Project:
    id: str
    verb: str
    gerund: str
    rush: str
    purpose: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ComfortItem:
    id: str
    label: str
    phrase: str
    covers: set[str]
    helps: set[str]
    plural: bool = False


@dataclass
class StoryParams:
    setting: str
    project: str
    comfort: str
    name: str
    sibling: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"surround"}),
    "bedroom": Setting(place="the bedroom", indoors=True, affords={"surround"}),
    "porch": Setting(place="the porch", indoors=True, affords={"surround"}),
}

PROJECTS = {
    "nest": Project(
        id="nest",
        verb="surround the tiny bird with soft cloth rings",
        gerund="surrounding the tiny bird with soft cloth rings",
        rush="hurry to the table with the cloth rings",
        purpose="keep it safe and snug",
        risk="blocked-in",
        keyword="nest",
        tags={"soft", "safe", "bird", "snug"},
    ),
    "garden": Project(
        id="garden",
        verb="surround the seedlings with cups",
        gerund="surrounding the seedlings with cups",
        rush="hurry to the windowsill with the cups",
        purpose="protect them from a cold draft",
        risk="messy",
        keyword="seedlings",
        tags={"plant", "garden", "safe"},
    ),
    "castle": Project(
        id="castle",
        verb="surround the toy animals with pillows",
        gerund="surrounding the toy animals with pillows",
        rush="carry the pillows to the rug",
        purpose="make them a cozy fort",
        risk="crowded",
        keyword="fort",
        tags={"play", "cozy", "safe"},
    ),
}

COMFORTS = {
    "blanket": ComfortItem(
        id="blanket",
        label="a soft blanket",
        phrase="a soft blanket",
        covers={"center"},
        helps={"safe", "snug", "cozy"},
    ),
    "cups": ComfortItem(
        id="cups",
        label="paper cups",
        phrase="paper cups",
        covers={"around"},
        helps={"safe", "protected", "gentle"},
    ),
    "pillows": ComfortItem(
        id="pillows",
        label="little pillows",
        phrase="little pillows",
        covers={"around"},
        helps={"cozy", "soft", "safe"},
        plural=True,
    ),
}

NAMES = ["Victor", "Maya", "Noah", "Lina", "Eli", "Iris"]
SIBLINGS = ["sister", "brother", "cousin"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
project_ok(P) :- project(P).
comfort_ok(C) :- comfort(C).

supports(C, P) :- comfort(C), project(P), needs(P, N), helps(C, N).
valid(P, C) :- project_ok(P), comfort_ok(C), supports(C, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        lines.append(asp.fact("needs", pid, "safe"))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag", pid, t))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        for h in sorted(c.helps):
            lines.append(asp.fact("helps", cid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_pairs())
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} valid pairs).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in python:", sorted(py - cl))
    print("only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def supports(project: Project, comfort: ComfortItem) -> bool:
    return bool(project.tags & comfort.helps)


def valid_pairs() -> list[tuple[str, str]]:
    return [(p, c) for p in PROJECTS for c in COMFORTS if supports(PROJECTS[p], COMFORTS[c])]


def explain_rejection(project: Project, comfort: ComfortItem) -> str:
    return (
        f"(No story: {comfort.label} does not help with {project.keyword}. "
        f"The heart of this tale is a real misunderstanding and a real helpful fix.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type="boy" if params.name == "Victor" else "child"))
    sibling = world.add(Entity(id=params.sibling, kind="character", type=params.sibling))
    project = world.add(Entity(
        id="project",
        type="thing",
        label=PROJECTS[params.project].keyword,
        phrase=PROJECTS[params.project].verb,
        owner=hero.id,
    ))
    comfort = COMFORTS[params.comfort]
    item = world.add(Entity(
        id="comfort",
        type="thing",
        label=comfort.label,
        phrase=comfort.phrase,
        owner=hero.id,
        protective=True,
        covers=set(comfort.covers),
    ))

    world.facts.update(hero=hero, sibling=sibling, project_cfg=PROJECTS[params.project], comfort_cfg=comfort, project=project, comfort=item)
    return world


def flashback_line(hero: Entity) -> str:
    return (
        f"Victor remembered a rainy afternoon with Grandma, when she had said, "
        f'"If something is small and worried, surround it gently."'
    )


def tell_story(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    sibling: Entity = f["sibling"]
    project: Entity = f["project"]
    comfort: Entity = f["comfort"]
    proj_cfg: Project = f["project_cfg"]
    comfort_cfg: ComfortItem = f["comfort_cfg"]

    hero.memes["care"] = 1
    hero.memes["hope"] = 1
    world.say(
        f"{hero.id} was in {world.setting.place} with {sibling.id}, "
        f"thinking about something small that needed kindness."
    )
    world.say(
        f"{hero.id} wanted to {proj_cfg.verb}, because {proj_cfg.purpose}."
    )
    world.say(
        f"So {hero.id} got {comfort_cfg.phrase} and began to surround the little center with a careful ring."
    )

    world.para()
    sibling.memes["worry"] = 1
    sibling.memes["misunderstanding"] = 1
    world.say(
        f"{sibling.id} frowned and looked surprised. "
        f'"Are you trapping it?" {sibling.id} asked.'
    )
    world.say(
        f"{hero.id} shook {hero.pronoun('possessive')} head. "
        f'"No, no. Safe and snug, safe and snug," {hero.id} said, repeating the words like a little song.'
    )

    world.para()
    world.say(flashback_line(hero))
    world.say(
        f"That memory made the choice feel steady. {hero.id} placed each piece more gently, "
        f"and the ring became a soft promise instead of a puzzle."
    )
    sibling.memes["worry"] = 0
    sibling.memes["understanding"] = 1
    hero.memes["joy"] = 1
    hero.memes["love"] = 1
    world.say(
        f"{sibling.id} stepped closer and saw it clearly. "
        f'"Safe and snug," {sibling.id} whispered, smiling now. "Oh."'
    )
    world.say(
        f"Together they checked the tiny space again: safe and snug, safe and snug, "
        f"until it looked warm and kind."
    )
    world.say(
        f"At the end, {hero.id} stood back beside {sibling.id}, and the little thing was "
        f"surrounded by care."
    )


# ---------------------------------------------------------------------------
# Parameter resolution and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming misunderstanding storyworld about Victor and a gentle surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--name")
    ap.add_argument("--sibling", choices=SIBLINGS)
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
    if args.project and args.comfort:
        if not supports(PROJECTS[args.project], COMFORTS[args.comfort]):
            raise StoryError(explain_rejection(PROJECTS[args.project], COMFORTS[args.comfort]))

    combos = valid_pairs()
    combos = [
        (p, c) for p, c in combos
        if (args.project is None or p == args.project)
        and (args.comfort is None or c == args.comfort)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project, comfort = rng.choice(sorted(combos))
    setting = args.setting or rng.choice(sorted(SETTINGS))
    name = args.name or "Victor"
    sibling = args.sibling or rng.choice(SIBLINGS)
    return StoryParams(setting=setting, project=project, comfort=comfort, name=name, sibling=sibling)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short heartwarming story for a young child about {f["hero"].id} and a misunderstanding that turns kind.',
        f'Write a gentle story where {f["hero"].id} wants to {f["project_cfg"].verb} in {world.setting.place} and uses a flashback to explain why.',
        f'Use the phrase "safe and snug" more than once in a comforting story about helping something small.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sibling: Entity = f["sibling"]
    proj_cfg: Project = f["project_cfg"]
    comfort_cfg: ComfortItem = f["comfort_cfg"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in {world.setting.place}?",
            answer=f"{hero.id} wanted to {proj_cfg.verb}, because {proj_cfg.purpose}.",
        ),
        QAItem(
            question=f"Why did {sibling.id} misunderstand what {hero.id} was doing?",
            answer=f"{sibling.id} thought {hero.id} might be trapping or crowding the little thing, but {hero.id} was really trying to help it feel safe.",
        ),
        QAItem(
            question=f"What did the flashback remind {hero.id} about?",
            answer="It reminded Victor of Grandma saying that small, worried things should be surrounded gently.",
        ),
        QAItem(
            question=f"What repeated words helped the moment feel calm?",
            answer='The words "safe and snug" were repeated to show that the plan was caring, not mean.',
        ),
        QAItem(
            question=f"What did {hero.id} use to make the careful ring?",
            answer=f"{hero.id} used {comfort_cfg.phrase} to build the soft ring around the center.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to surround something?",
            answer="To surround something means to place things all around it so it sits in the middle.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something means one thing, but it really means something different.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly shows something that happened earlier, so the reader can understand why a character feels the way they do.",
        ),
        QAItem(
            question="Why do writers repeat words in a story?",
            answer="Writers repeat words to make them feel important, musical, or calming, and to help the reader remember them.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="kitchen", project="nest", comfort="blanket", name="Victor", sibling="sister"),
    StoryParams(setting="bedroom", project="castle", comfort="pillows", name="Victor", sibling="brother"),
    StoryParams(setting="porch", project="garden", comfort="cups", name="Victor", sibling="sister"),
]


def asp_valid_stories() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def build_asp_program() -> str:
    return asp_program("#show valid/2.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid (project, comfort) pairs:\n")
        for p, c in pairs:
            print(f"  {p:8} {c}")
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
            header = f"### {p.name}: {p.project} in {p.setting} (comfort: {p.comfort})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
