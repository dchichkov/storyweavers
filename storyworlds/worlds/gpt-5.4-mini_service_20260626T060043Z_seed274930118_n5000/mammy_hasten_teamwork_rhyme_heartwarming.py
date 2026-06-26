#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mammy_hasten_teamwork_rhyme_heartwarming.py
===============================================================================================================

A small heartwarming story world about a child, Mammy, a little hurry, and a
shared rhyme project that only succeeds through teamwork.

Seed idea:
- A child and Mammy need to hasten to finish a rhyme before bedtime.
- The child feels worried about the deadline.
- Mammy turns the rush into teamwork: each one does a different part.
- The rhyme is finished, the pressure softens, and the final image proves the
  work was done together.

The world model tracks:
- physical meters: ink, pages, crumbs, tidiness, elapsed_time, completed_parts
- emotional memes: worry, calm, pride, affection, teamwork, haste

The prose is state-driven: the story changes depending on whether the rhyme is
completed, whether the room is tidy, and how the characters feel as they work.
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
# Registries
# ---------------------------------------------------------------------------

NAMES = ["Mina", "Lulu", "Noa", "Tilly", "Pip", "Rosa", "June", "Mabel"]
CHILD_TYPES = ["girl", "boy"]
MAMMY_TYPES = ["mother", "mammy"]

SETTINGS = {
    "kitchen": {
        "place": "the kitchen table",
        "details": "The lamp made a soft circle of light on the table.",
        "rush": "the supper bell was almost ready",
        "messy": False,
    },
    "bedroom": {
        "place": "the bedroom floor",
        "details": "A blanket fort made the room feel cozy and small.",
        "rush": "bedtime was close",
        "messy": False,
    },
    "porch": {
        "place": "the porch bench",
        "details": "The porch had fresh air and a view of the darkening sky.",
        "rush": "the evening breeze was growing cool",
        "messy": False,
    },
}

PROJECTS = {
    "rhyme_card": {
        "label": "rhyme card",
        "phrase": "a bright rhyme card",
        "pieces": ["line", "picture", "border"],
        "goal": "finish the rhyme card",
        "complete_image": "the rhyme card stood straight and proud",
        "need": "write a rhyme and decorate the card",
        "tool": "pencil",
    },
    "birthday_rhyme": {
        "label": "birthday rhyme",
        "phrase": "a birthday rhyme for a friend",
        "pieces": ["first line", "second line", "ending"],
        "goal": "finish the birthday rhyme",
        "complete_image": "the page held a happy rhyme that sounded like a tiny song",
        "need": "make the rhyme sound cheerful and true",
        "tool": "crayon",
    },
    "bedtime_rhyme": {
        "label": "bedtime rhyme",
        "phrase": "a sleepy bedtime rhyme",
        "pieces": ["soft line", "gentle line", "last line"],
        "goal": "finish the bedtime rhyme",
        "complete_image": "the final rhyme was soft enough to tuck into a dream",
        "need": "make the rhyme feel warm and calm",
        "tool": "ink pen",
    },
}

HELPERS = {
    "sticker_sheet": {
        "label": "a sticker sheet",
        "protects": ["tidiness"],
        "helps": "decorate the page quickly",
    },
    "mug_of_water": {
        "label": "a mug of water",
        "protects": ["tidiness"],
        "helps": "keep the crayons from drying out",
    },
    "snack_plate": {
        "label": "a snack plate",
        "protects": ["worry"],
        "helps": "keep their tummies happy while they worked",
    },
}

RHYME_ENDINGS = {
    "card": "spark and shine",
    "friend": "bright and fine",
    "dream": "soft and kind",
}


# ---------------------------------------------------------------------------
# Core data model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mammy", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    key: str
    place: str
    details: str
    rush: str
    messy: bool = False


@dataclass
class Project:
    key: str
    label: str
    phrase: str
    pieces: list[str]
    goal: str
    complete_image: str
    need: str
    tool: str


@dataclass
class Helper:
    key: str
    label: str
    protects: list[str]
    helps: str


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# World parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    project: str
    child_name: str
    child_type: str
    mammy_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(setting_key: str, project_key: str) -> bool:
    return setting_key in SETTINGS and project_key in PROJECTS


def valid_story(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.project in PROJECTS


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the setting and project need to be one of the registered, sensible choices.)"


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def project_piece_name(project: Project, idx: int) -> str:
    return project.pieces[min(idx, len(project.pieces) - 1)]


def build_rhyme(project: Project, child: Entity, mammy: Entity) -> str:
    end = RHYME_ENDINGS.get(project.key, "sweet and bright")
    return (
        f"{child.id} and {mammy.pronoun('possessive')} mammy made their words line up so the last part ended {end}."
    )


def predict_finish(world: World, child: Entity, mammy: Entity, project: Project) -> bool:
    sim = world.copy()
    do_work(sim, sim.get(child.id), sim.get(mammy.id), project, narrate=False)
    return sim.facts.get("finished", False)


def do_work(world: World, child: Entity, mammy: Entity, project: Project, narrate: bool = True) -> None:
    if world.facts.get("finished"):
        return
    add_meter(child, "completed_parts", 1)
    add_meter(mammy, "completed_parts", 1)
    add_meter(child, "elapsed_time", 1)
    add_meter(mammy, "elapsed_time", 1)
    add_meme(child, "teamwork", 1)
    add_meme(mammy, "teamwork", 1)
    add_meme(child, "worry", -1)
    add_meme(mammy, "worry", -1)
    add_meme(child, "calm", 1)
    add_meme(mammy, "calm", 1)
    add_meter(child, "ink", 1)
    add_meter(mammy, "ink", 1)
    add_meter(child, "tidiness", 1)
    add_meter(mammy, "tidiness", 1)
    if child.meters.get("completed_parts", 0) >= 2 and mammy.meters.get("completed_parts", 0) >= 2:
        world.facts["finished"] = True
    if narrate:
        world.say(
            f"{child.id} wrote one part while {mammy.type} checked the next. "
            f"Together they kept going, and the {project.label} moved forward."
        )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    setting = Setting(**SETTINGS[params.setting])
    project = Project(key=params.project, **PROJECTS[params.project])
    world = World(setting)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        meters={"worry": 1.0, "calm": 0.0, "completed_parts": 0.0, "elapsed_time": 0.0},
        memes={"worry": 1.0, "calm": 0.0, "teamwork": 0.0, "pride": 0.0, "affection": 0.0, "haste": 1.0},
    ))
    mammy = world.add(Entity(
        id="Mammy",
        kind="character",
        type=params.mammy_type,
        meters={"worry": 0.0, "calm": 1.0, "completed_parts": 0.0, "elapsed_time": 0.0},
        memes={"worry": 0.0, "calm": 1.0, "teamwork": 0.0, "pride": 0.0, "affection": 1.0, "haste": 0.5},
    ))
    paper = world.add(Entity(
        id="paper",
        type="paper",
        label=project.label,
        phrase=project.phrase,
        owner=child.id,
        caretaker=mammy.id,
        meters={"tidiness": 1.0},
    ))
    tool = world.add(Entity(
        id="tool",
        type=project.tool,
        label=project.tool,
        owner=child.id,
        caretaker=mammy.id,
    ))

    helper_key = random.choice(list(HELPERS))
    helper = Helper(key=helper_key, **HELPERS[helper_key])
    world.add(Entity(
        id=helper.key,
        type="helper",
        label=helper.label,
        phrase=helper.helps,
        caretaker=mammy.id,
    ))

    # Act 1: setup.
    world.say(f"{child.id} had a {project.label} to finish, and {setting.rush} had already begun.")
    world.say(f"The room was ready at {setting.place}. {setting.details}")
    world.say(f"{child.id} wanted to {project.goal}, but the words were not settling into place.")
    world.say(f"Then {mammy.type} smiled and said they could do it together.")
    world.facts.update(child=child, mammy=mammy, paper=paper, tool=tool, project=project, helper=helper)

    # Act 2: tension and teamwork.
    world.para()
    add_meme(child, "worry", 1)
    world.say(
        f"{child.id} looked at the page and began to hasten, but the faster {child.id} tried to go, "
        f"the more the rhyme wobbled."
    )
    world.say(
        f"{mammy.id} put {helper.label} beside the paper because small helpful things make busy work easier."
    )
    world.say(
        f"'{child.id}, you say one line, and I will say the next,' {mammy.pronoun()} said, and that made the hurry feel softer."
    )
    do_work(world, child, mammy, project, narrate=True)
    do_work(world, child, mammy, project, narrate=True)

    # Act 3: resolution.
    world.para()
    if world.facts.get("finished"):
        child.meters["worry"] = max(0.0, child.meters.get("worry", 0.0) - 1)
        add_meme(child, "pride", 1)
        add_meme(mammy, "pride", 1)
        add_meme(child, "affection", 1)
        add_meme(mammy, "affection", 1)
        world.say(
            f"At last, the last words clicked into place, and {build_rhyme(project, child, mammy)}"
        )
        world.say(
            f"{child.id} grinned because the {project.label} was done, and {mammy.id} gave a warm hug."
        )
        world.say(
            f"On the table, {paper.phrase} was neat and complete, and the little helper things still sat nearby like quiet friends."
        )
    else:
        world.say(
            f"They were still working, but {mammy.id} kept {child.id} steady, and the page was no longer lonely."
        )

    world.facts["setting"] = setting
    world.facts["project"] = project
    world.facts["helper_obj"] = helper
    return world


# ---------------------------------------------------------------------------
# Registries / sampling
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="kitchen", project="rhyme_card", child_name="Mina", child_type="girl", mammy_type="mammy"),
    StoryParams(setting="bedroom", project="bedtime_rhyme", child_name="Pip", child_type="boy", mammy_type="mother"),
    StoryParams(setting="porch", project="birthday_rhyme", child_name="Rosa", child_type="girl", mammy_type="mammy"),
]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, p) for s in SETTINGS for p in PROJECTS if valid_combo(s, p)]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    mammy = world.facts["mammy"]
    project = world.facts["project"]
    setting = world.facts["setting"]
    return [
        f"Write a heartwarming story about {child.id} and {mammy.type} finishing {project.phrase} at {setting.place}.",
        f"Tell a short story where {child.id} has to hasten, but teamwork helps the rhyme come together.",
        f"Write a gentle story with the words 'mammy' and 'hasten' and an ending that proves the work was shared.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    mammy = world.facts["mammy"]
    project = world.facts["project"]
    setting = world.facts["setting"]
    helper = world.facts["helper_obj"]
    finished = world.facts.get("finished", False)

    out = [
        QAItem(
            question=f"Who worked together on the {project.label}?",
            answer=f"{child.id} and {mammy.type} worked together on the {project.label}, taking turns and helping each other."
        ),
        QAItem(
            question=f"Where did {child.id} and {mammy.type} work?",
            answer=f"They worked at {setting.place}, where the light and quiet made the job feel calm."
        ),
        QAItem(
            question=f"What helped the work feel easier?",
            answer=f"{helper.label} helped because it could {helper.helps}."
        ),
    ]
    if finished:
        out.append(
            QAItem(
                question=f"How did the story end for the {project.label}?",
                answer=f"It ended with the {project.label} finished, neat on the table, and everyone feeling proud and close."
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do different parts of a job together."
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when the ends of words sound alike, like a little echo in a song or poem."
        ),
        QAItem(
            question="Why do people hasten sometimes?",
            answer="People hasten when they want to finish something before time runs out or before bedtime."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(kitchen).
setting(bedroom).
setting(porch).

project(rhyme_card).
project(birthday_rhyme).
project(bedtime_rhyme).

valid(S,P) :- setting(S), project(P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PROJECTS:
        lines.append(asp.fact("project", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in python:", sorted(py - asp_set))
    print("only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Core interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming teamwork-rhyme story world.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--project", choices=sorted(PROJECTS))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--mammy-type", choices=MAMMY_TYPES)
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
    if args.setting and args.project and not valid_combo(args.setting, args.project):
        raise StoryError(explain_rejection(StoryParams(args.setting, args.project, "Mina", "girl", "mammy")))
    setting = args.setting or rng.choice(list(SETTINGS))
    project = args.project or rng.choice(list(PROJECTS))
    name = args.name or rng.choice(NAMES)
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    mammy_type = args.mammy_type or "mammy"
    return StoryParams(setting=setting, project=project, child_name=name, child_type=child_type, mammy_type=mammy_type)


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
    lines = ["--- world model ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, p in combos:
            print(f"  {s:8} {p}")
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
            header = f"### {p.child_name}: {p.project} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
