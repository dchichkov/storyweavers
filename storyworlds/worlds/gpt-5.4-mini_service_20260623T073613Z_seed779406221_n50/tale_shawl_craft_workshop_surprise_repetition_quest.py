#!/usr/bin/env python3
"""
storyworlds/worlds/tale_shawl_craft_workshop_surprise_repetition_quest.py
=========================================================================

A small slice-of-life storyworld set in a craft workshop.

Seed idea:
- A child visits a craft workshop to make a shawl for a tale-night event.
- The child expects a simple project, but there is a surprise: a missing pattern
  or a twist in the yarn colors.
- Repetition matters because craft work often repeats: measure, fold, stitch.
- The quest is gentle and practical: finish a soft shawl, learn patience, and
  leave with a cozy result that proves what changed.

The world uses typed entities with physical meters and emotional memes, a simple
state-driven renderer, grounded Q&A, and a small ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Workshop:
    place: str = "the craft workshop"
    stations: tuple[str, ...] = ("table", "shelf", "sink")


@dataclass
class Project:
    id: str
    label: str
    phrase: str
    material: str
    steps: tuple[str, ...]
    repetitions: int
    surprise: str
    quest: str
    result_image: str


@dataclass
class StoryParams:
    project: str
    name: str
    child_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, workshop: Workshop) -> None:
        self.workshop = workshop
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        c = World(self.workshop)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


def meter_up(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def meme_up(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def as_line_list(text: str) -> list[str]:
    return [s.strip() for s in text.splitlines() if s.strip()]


PROJECTS = {
    "shawl_story": Project(
        id="shawl_story",
        label="shawl",
        phrase="a soft shawl",
        material="yarn",
        steps=("measure", "loop", "stitch"),
        repetitions=3,
        surprise="the blue yarn had slipped behind the basket",
        quest="find the missing yarn and finish the shawl for tale night",
        result_image="a warm shawl with tidy edges and a little blue border",
    ),
    "story_patch": Project(
        id="story_patch",
        label="patch",
        phrase="a patch for the shawl",
        material="felt",
        steps=("trace", "cut", "sew"),
        repetitions=2,
        surprise="the star button was missing from the ribbon box",
        quest="find the star button and patch the shawl before the guests arrive",
        result_image="a shawl with a bright star patch near the corner",
    ),
    "story_tassel": Project(
        id="story_tassel",
        label="tassel",
        phrase="a tasseled shawl edge",
        material="thread",
        steps=("twist", "tie", "trim"),
        repetitions=4,
        surprise="the green thread had tangled itself into a knot",
        quest="untangle the thread and make the tassels match",
        result_image="a shawl edge with even tassels swinging like little feathers",
    ),
}

WORKSHOP = Workshop()

GIRL_NAMES = ["Mina", "Lina", "Nora", "Ava", "Ivy", "Maya"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Milo", "Owen", "Eli"]


def tell(workshop: Workshop, project: Project, child_name: str, child_type: str,
         helper_name: str, helper_type: str) -> World:
    w = World(workshop)
    child = w.add(Entity(id=child_name, kind="character", type=child_type, label=child_name))
    helper = w.add(Entity(id=helper_name, kind="character", type=helper_type, label=helper_name))
    item = w.add(Entity(id=project.id, type=project.label, label=project.label, phrase=project.phrase, owner=child.id))
    basket = w.add(Entity(id="basket", type="thing", label="basket"))
    table = w.add(Entity(id="table", type="thing", label="table"))
    sink = w.add(Entity(id="sink", type="thing", label="sink"))

    meme_up(child, "curiosity", 1)
    meme_up(child, "hope", 1)
    w.say(f"{child.id} came to {workshop.place} with a small tale in mind and a wish to make {project.phrase}.")
    w.say(f"{helper.id} was already there, sorting yarn by color and smiling at the busy tables.")
    w.say(f'The day felt calm, with scissors, cups of thread, and soft scraps lying near the {table.label}.')

    w.para()
    meme_up(child, "desire", 1)
    w.say(f"{child.id} wanted to finish {project.label} for {project.quest}.")
    w.say(f"To begin, {child.id} followed the same little steps again and again: {', '.join(project.steps)}.")
    for i in range(project.repetitions):
        meter_up(item, "progress", 1)
        meter_up(child, "focus", 1)
        w.say(f"{child.id} repeated the motion one more time, and the shawl grew a little longer.")
    meter_up(item, "tidy", 1)

    w.para()
    meter_up(child, "surprise", 1)
    w.say(f"Then came the surprise: {project.surprise}.")
    w.say(f"{child.id} looked under the {basket.label}, checked the shelf, and even peered by the sink.")
    helper.memes["calm"] = helper.memes.get("calm", 0.0) + 1
    w.say(f"{helper.id} laughed softly and helped search, because the craft workshop liked shared puzzling as much as stitching.")
    meter_up(child, "search", 1)
    meter_up(helper, "help", 1)

    w.para()
    meter_up(child, "joy", 1)
    meme_up(child, "relief", 1)
    w.say(f"At last, {child.id} found the missing blue yarn tucked behind a jar of buttons.")
    w.say(f"The work became easier after that: {child.id} repeated the last stitches with steady hands, and {helper.id} counted the loops aloud.")
    w.say(f"When the final knot was tied, the shawl looked like {project.result_image}.")

    child.memes["pride"] = child.memes.get("pride", 0.0) + 1
    item.meters["finished"] = 1
    item.meters["beautiful"] = 1
    w.say(f"{child.id} held up {project.phrase}, and {helper.id} said it was just right for tale night.")
    w.facts.update(
        child=child,
        helper=helper,
        item=item,
        project=project,
        workshop=workshop,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    project = f["project"]
    return [
        f'Write a gentle slice-of-life story set in a craft workshop where {child.id} makes a {project.label}.',
        f'Write a story about a small quest for "{project.label}" that includes a surprise and a lot of repetition.',
        f'Write a child-friendly workshop story that ends with a finished {project.label} for tale night.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    project = f["project"]
    item = f["item"]
    qa = [
        QAItem(
            question=f"What did {child.id} go to the craft workshop to make?",
            answer=f"{child.id} went to the craft workshop to make {project.phrase}. The project was a {project.label} that needed patient hands.",
        ),
        QAItem(
            question=f"Who helped {child.id} at the workshop?",
            answer=f"{helper.id} helped {child.id} by looking for supplies and counting the stitches. That made the work feel calm and friendly.",
        ),
        QAItem(
            question=f"What was the quest in the story?",
            answer=f"The quest was to {project.quest}. That gave the day a clear goal and kept the story moving forward.",
        ),
        QAItem(
            question=f"What surprise happened during the work?",
            answer=f"The surprise was that {project.surprise}. {child.id} had to look around and search before the shawl could be finished.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {item.label} was finished and looked like {project.result_image}. {child.id} left the workshop with something cozy and complete.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shawl?",
            answer="A shawl is a soft piece of cloth you wear around your shoulders to feel warm and cozy.",
        ),
        QAItem(
            question="What does repetition mean in craft work?",
            answer="Repetition means doing the same step again and again, like stitching or looping yarn, until the project is ready.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a small goal or search, like trying to find a missing button or finish a project before the day ends.",
        ),
        QAItem(
            question="Why do people work in craft workshops?",
            answer="People work in craft workshops to make things with their hands, share tools, and finish projects together.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_projects() -> list[str]:
    return list(PROJECTS)


def explain_rejection(name: str) -> str:
    return f"(No story: unknown project '{name}'. Try one of: {', '.join(valid_projects())}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life craft workshop storyworld about a shawl, a surprise, repetition, and a gentle quest.")
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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
    project = args.project or rng.choice(valid_projects())
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    child_type = args.child_type or rng.choice(["girl", "boy"])
    helper = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    return StoryParams(project=project, name=name, child_type=child_type, helper=helper, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(WORKSHOP, PROJECTS[params.project], params.name, params.child_type, params.helper, params.helper_type)
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


ASP_RULES = r"""
project(P) :- project_name(P).
finished(P) :- progress(P, N), N >= reps(P).
quest_done(P) :- finished(P), surprise(P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, p in PROJECTS.items():
        lines.append(asp.fact("project_name", pid))
        lines.append(asp.fact("label", pid, p.label))
        lines.append(asp.fact("reps", pid, p.repetitions))
        lines.append(asp.fact("surprise", pid, p.surprise))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show project/1."))
    asp_projects = {p[0] for p in asp.atoms(model, "project")}
    py_projects = set(valid_projects())
    if asp_projects != py_projects:
        print("MISMATCH between ASP and Python project registry.")
        return 1
    print(f"OK: ASP and Python agree on {len(py_projects)} projects.")
    return 0


CURATED = [
    StoryParams(project="shawl_story", name="Mina", child_type="girl", helper="Iris", helper_type="girl"),
    StoryParams(project="story_patch", name="Theo", child_type="boy", helper="Lena", helper_type="girl"),
    StoryParams(project="story_tassel", name="Ava", child_type="girl", helper="Noah", helper_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show project/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show project/1."))
        print(sorted(asp.atoms(model, "project")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            i += 1
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
            header = f"### {p.name}: {p.project}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
