#!/usr/bin/env python3
"""
A heartwarming storyworld about a small team preparing a final surprise.

Premise:
- A child wants to dedicate a final handmade gift to someone they love.
- The work is shared with helpers, and tiny foreshadowing details hint at the ending.
- Kindness and teamwork turn a near-miss into a warm resolution.

This script is self-contained and uses a small simulation with physical meters
and emotional memes to drive the story, QA, and ASP parity checks.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Project:
    id: str
    noun: str
    verb: str
    gerund: str
    material: str
    mess: str
    risk: str
    foreshadow: str
    end_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    covers: set[str]
    offer: str
    ending: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen_table": Setting(place="the kitchen table", indoors=True, affords={"bake", "craft"}),
    "classroom": Setting(place="the classroom art corner", indoors=True, affords={"craft", "decorate"}),
    "workbench": Setting(place="the sunny workbench", indoors=True, affords={"build", "craft"}),
}

PROJECTS = {
    "cake": Project(
        id="cake",
        noun="cake",
        verb="decorate the cake",
        gerund="decorating the cake",
        material="icing",
        mess="sticky",
        risk="the frosting could smear",
        foreshadow="A little crack in the icing kept showing up, like the cake was waiting for a kinder fix.",
        end_image="the cake sat neat and bright in the middle of the table",
        tags={"cake", "sweet", "family"},
    ),
    "lantern": Project(
        id="lantern",
        noun="lantern",
        verb="fold the paper lantern",
        gerund="folding the paper lantern",
        material="paper",
        mess="creased",
        risk="the paper could tear",
        foreshadow="One corner kept folding back, as if the lantern was quietly asking for careful hands.",
        end_image="the lantern glowed softly beside the window",
        tags={"lantern", "paper", "light"},
    ),
    "banner": Project(
        id="banner",
        noun="banner",
        verb="paint the final banner",
        gerund="painting the final banner",
        material="paint",
        mess="paint-splattered",
        risk="the letters could blur",
        foreshadow="A tiny drip slid toward the edge, warning everyone that rushing would not help.",
        end_image="the banner hung straight and cheerful above the doorway",
        tags={"banner", "paint", "party"},
    ),
}

TOOLS = [
    Tool(
        id="cloth",
        label="a clean cloth",
        helps={"sticky", "paint-splattered"},
        covers={"table", "hands"},
        offer="wipe the table and hold the paper steady",
        ending="They wiped away the mess before it could spread",
    ),
    Tool(
        id="clip",
        label="a wooden clip",
        helps={"creased", "paint-splattered"},
        covers={"paper", "edge"},
        offer="hold the paper flat while they folded",
        ending="The clip kept the paper calm and straight",
    ),
    Tool(
        id="stencil",
        label="a little stencil",
        helps={"paint-splattered"},
        covers={"letters"},
        offer="guide the final letters so they stayed neat",
        ending="The stencil helped the letters stay bold and clear",
    ),
]

GIVERS = ["mother", "father", "grandmother", "grandfather"]
NAMES = {
    "girl": ["Mia", "Nora", "Lina", "Maya", "Ruby"],
    "boy": ["Leo", "Ben", "Owen", "Theo", "Finn"],
}
TRAITS = ["kind", "gentle", "curious", "patient", "thoughtful"]
HELPERS = ["a sister", "a brother", "a neighbor", "a classmate"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A project is reasonable when its venue affords it.
reasonable(P) :- project(P), setting(S), affords(S, P).

% A tool is a useful fix when it helps the project's risky material.
helps_fix(T, P) :- tool(T), project(P), helps(T, P).

compatible(P) :- reasonable(P), helps_fix(_, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for p in sorted(s.affords):
            lines.append(asp.fact("affords", sid, p))
    for pid, p in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        lines.append(asp.fact("risk", pid, p.mess))
        for t in sorted(p.tags):
            lines.append(asp.fact("tags", pid, t))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", t.id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable_projects() -> set[str]:
    import asp
    model = asp.one_model(asp_program("#show compatible/1."))
    return {x[0] for x in asp.atoms(model, "compatible")}


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    project: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def choose_tool(project: Project) -> Optional[Tool]:
    for tool in TOOLS:
        if project.mess in tool.helps:
            return tool
    return None


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    project = PROJECTS[params.project]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper))
    prize = world.add(Entity(id="project", type=project.id, label=project.noun, caretaker=helper.id))

    world.facts.update(hero=hero, helper=helper, project=project, prize=prize, params=params)
    return world


def start_story(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    project: Project = world.facts["project"]  # type: ignore[assignment]
    trait = world.facts["params"].trait  # type: ignore[assignment]

    world.say(
        f"{hero.id} was a {trait} little {hero.type} who wanted to dedicate the final {project.noun} "
        f"to someone special."
    )
    world.say(project.foreshadow)
    world.say(
        f"{hero.id} and {helper.label if helper.label else helper.id} smiled at the work ahead, "
        f"because small careful jobs felt big when shared kindly."
    )


def work_toward_finish(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    project: Project = world.facts["project"]  # type: ignore[assignment]
    tool = choose_tool(project)
    if tool is None:
        raise StoryError("No reasonable tool exists for this project.")

    # state changes
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    helper.memes["care"] = helper.memes.get("care", 0) + 1
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0) + 1
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0) + 1
    world.facts["tool"] = tool

    world.para()
    world.say(
        f"At first, {hero.id} almost rushed, and the {project.material} wobbled in a messy way."
    )
    world.say(
        f"Then {helper.id} offered {tool.label} so they could {tool.offer}, and that made the work easier."
    )
    world.say(tool.ending + f", so the {project.noun} could become the final gift they hoped for."
    )

    # physical/emotional resolution
    prize: Entity = world.facts["prize"]  # type: ignore[assignment]
    prize.meters["done"] = 1
    prize.memes["warmth"] = 1
    hero.memes["relief"] = 1
    helper.memes["joy"] = 1
    world.facts["resolved"] = True

    world.para()
    world.say(
        f"At last, {hero.id} tied in the last careful touch and dedicated the final {project.noun} with a grin."
    )
    world.say(
        f"{project.end_image}, and {hero.id} and {helper.id} stood side by side, feeling proud of their kindness and teamwork."
    )


def generate_story_text(params: StoryParams) -> World:
    world = build_world(params)
    start_story(world)
    work_toward_finish(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p: Project = world.facts["project"]  # type: ignore[assignment]
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        f"Write a heartwarming story about a child who wants to dedicate the final {p.noun} to someone they love.",
        f"Tell a gentle story where {params.name} and a helper use teamwork to finish {p.gerund}.",
        f"Make a simple story with foreshadowing, kindness, and a warm ending image involving a final {p.noun}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    project: Project = world.facts["project"]  # type: ignore[assignment]
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    tool: Tool = world.facts["tool"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the final {project.noun}?",
            answer=f"{hero.id} wanted to dedicate the final {project.noun} to someone special.",
        ),
        QAItem(
            question=f"Why did the work get easier for {hero.id}?",
            answer=f"The work got easier because {helper.id} offered {tool.label} and they used teamwork kindly.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and the project?",
            answer=f"It ended with {project.end_image}, and {hero.id} felt proud and warm-hearted.",
        ),
        QAItem(
            question=f"What was one foreshadowing detail in the story?",
            answer=f"The story hinted that {project.foreshadow.lower()}",
        ),
        QAItem(
            question=f"What words best describe how {params.name} and the helper worked together?",
            answer="They were kind, patient, and full of teamwork.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p: Project = world.facts["project"]  # type: ignore[assignment]
    tool: Tool = world.facts["tool"]  # type: ignore[assignment]
    out = [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small hint that gives readers a clue about what may happen later.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do a job together.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward others.",
        ),
    ]
    if "cake" in p.tags:
        out.append(QAItem(
            question="Why should icing be handled carefully?",
            answer="Icing can smear if it is rushed, so careful hands help keep a cake neat.",
        ))
    if "paper" in p.tags:
        out.append(QAItem(
            question="Why is paper easier to tear when people rush?",
            answer="Paper can bend and tear if it is folded too quickly or too hard.",
        ))
    if "paint" in p.tags:
        out.append(QAItem(
            question="Why can paint be messy?",
            answer="Paint can drip or splatter, so it helps to move slowly and use a steady hand.",
        ))
    out.append(QAItem(
        question=f"What does {tool.label} help with in this kind of story?",
        answer=f"{tool.label.capitalize()} helps the characters do careful work and keep the final result neat.",
    ))
    return out


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Validation and parameter resolution
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="kitchen_table", project="cake", name="Mia", gender="girl", helper="mother", trait="kind"),
    StoryParams(place="classroom", project="banner", name="Leo", gender="boy", helper="father", trait="thoughtful"),
    StoryParams(place="workbench", project="lantern", name="Nora", gender="girl", helper="grandmother", trait="gentle"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld about a final gift, kindness, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
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
    if args.place and args.project and args.project not in SETTINGS[args.place].affords:
        raise StoryError("That place does not reasonably support that project.")
    if args.gender and args.name is None:
        pass
    place = args.place or rng.choice(list(SETTINGS))
    project = args.project or rng.choice(sorted(list(asp_reasonable_projects()) or list(PROJECTS)))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(GIVERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, project=project, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = generate_story_text(params)
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


# ---------------------------------------------------------------------------
# ASP verification
# ---------------------------------------------------------------------------

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/1."))
    asp_set = {x[0] for x in asp.atoms(model, "compatible")}
    py_set = {pid for pid, p in PROJECTS.items() if any(t.mess == p.mess for t in TOOLS) and pid in PROJECTS}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(asp_set)} projects).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("only in asp:", sorted(asp_set - py_set))
    print("only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Main / ASP modes
# ---------------------------------------------------------------------------

def asp_valid_projects() -> list[str]:
    return sorted(asp_reasonable_projects())


def asp_show_all() -> str:
    return asp_program("#show compatible/1.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_show_all())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(asp_valid_projects()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.project} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
