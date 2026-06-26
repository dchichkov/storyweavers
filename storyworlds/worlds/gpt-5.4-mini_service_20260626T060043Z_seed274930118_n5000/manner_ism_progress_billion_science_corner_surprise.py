#!/usr/bin/env python3
"""
A fairy-tale storyworld in the science corner.

Seed idea:
A child in the science corner keeps making a tiny, careful project more and more
precise. The child learns that progress does not need a billion steps, and a
surprise from the experiment turns worry into delight.

This world is intentionally small and constraint-checked: one child, one helper,
one science-corner project, one surprising result, and one gentle resolution.
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

SCENE = "science corner"
THEME_WORDS = ("manner-ism", "progress", "billion")


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def get(self, eid: str) -> Entity:
        return self.entities[eid]


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    project: str
    seed: Optional[int] = None


NAMES = {
    "girl": ["Mina", "Lila", "Nora", "Ava", "Elsa"],
    "boy": ["Theo", "Finn", "Ezra", "Owen", "Ivo"],
}
HELPERS = [
    ("grandmother", "an old grandmother with kind eyes"),
    ("teacher", "a gentle teacher with a bright apron"),
    ("caretaker", "a smiling caretaker with soft steps"),
]
PROJECTS = [
    ("seed_lens", "a seed lens"),
    ("star_jar", "a star jar"),
    ("bubble_map", "a bubble map"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld set in the science corner.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=[h[0] for h in HELPERS])
    ap.add_argument("--project", choices=[p[0] for p in PROJECTS])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice([h[0] for h in HELPERS])
    project = args.project or rng.choice([p[0] for p in PROJECTS])
    return StoryParams(name=name, gender=gender, helper=helper, project=project)


def project_phrase(project_id: str) -> str:
    return dict(PROJECTS)[project_id]


def helper_phrase(helper_id: str) -> str:
    return dict(HELPERS)[helper_id]


def introduce(world: World, child: Entity, helper: Entity, project: Entity) -> None:
    world.say(
        f"In the {SCENE}, little {child.id} kept a careful {project.label}, "
        f"and {helper.phrase} watched nearby."
    )
    world.say(
        f"{child.pronoun().capitalize()} loved tiny neat habits, the kind that felt like a "
        f"manner-ism in a fairy tale, and {child.pronoun('possessive')} heart was full of progress."
    )


def build_setup(world: World, child: Entity, project: Entity) -> None:
    child.memes["hope"] = 1
    child.meters["care"] = 1
    project.meters["finished"] = 0
    project.meters["steps"] = 0
    world.say(
        f"{child.id} said, \"I can make it perfect if I do a billion little steps.\" "
        f"{child.pronoun('possessive').capitalize()} fingers moved slowly over the table."
    )


def work_on_project(world: World, child: Entity, project: Entity) -> None:
    child.meters["care"] += 1
    project.meters["steps"] += 3
    project.meters["finished"] += 1
    child.memes["confidence"] = child.memes.get("confidence", 0) + 1
    world.say(
        f"{child.id} worked and worked, and every small try turned into a bit more progress."
    )
    world.say(
        f"The project began to glow with patient order, as if the room itself were listening."
    )


def surprise_turn(world: World, child: Entity, helper: Entity, project: Entity) -> None:
    child.memes["surprise"] = 1
    project.meters["surprise"] = 1
    world.say(
        f"Then, with a tiny pop, the {project.label} gave a surprise: a silver sprout poked out, "
        f"as if a hidden moonbeam had been waiting inside the jar."
    )
    world.say(
        f"{helper.id} laughed softly and said, \"Not a billion steps, dear one. Sometimes one kind step is enough.\""
    )
    child.memes["worry"] = 0


def resolve(world: World, child: Entity, helper: Entity, project: Entity) -> None:
    child.memes["joy"] = child.memes.get("joy", 0) + 2
    child.memes["confidence"] = child.memes.get("confidence", 0) + 1
    world.say(
        f"{child.id} smiled so wide that the whole {SCENE} seemed to brighten."
    )
    world.say(
        f"Together they set the {project.label} by the window, where the little sprout could shine."
    )


def tell_story(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"care": 0},
        memes={"hope": 1},
    ))
    helper_id, helper_desc = helper_phrase(params.helper).split(";", 1) if ";" in helper_phrase(params.helper) else (params.helper, helper_phrase(params.helper))
    helper = world.add(Entity(
        id=helper_id,
        kind="character",
        type="adult",
        phrase=helper_phrase(params.helper),
        meters={"patience": 1},
        memes={"kindness": 1},
    ))
    project = world.add(Entity(
        id=params.project,
        type="project",
        label=project_phrase(params.project),
        owner=child.id,
        caretaker=helper.id,
        meters={"finished": 0, "steps": 0},
        memes={"wonder": 1},
    ))

    world.facts = {
        "child": child.id,
        "helper": helper.id,
        "project": project.label,
        "scene": SCENE,
    }

    introduce(world, child, helper, project)
    world.para()
    build_setup(world, child, project)
    work_on_project(world, child, project)
    world.para()
    surprise_turn(world, child, helper, project)
    resolve(world, child, helper, project)
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a fairy-tale story set in the {f['scene']} about {f['child']} and a small surprise.",
        f"Tell a child-friendly story where {f['child']} wants progress, notices a manner-ism, and learns that a billion steps are not always needed.",
        f"Write a gentle story about {f['project']} in the science corner, ending with a surprise and a happy smile.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = world.get(f["child"])
    project = next(e for e in world.entities.values() if e.label == f["project"])
    helper = next(e for e in world.entities.values() if e.id == f["helper"])
    return [
        QAItem(
            question=f"Where did {child.id} work on the {project.label}?",
            answer=f"{child.id} worked in the {SCENE}, where the little table and careful tools waited.",
        ),
        QAItem(
            question=f"What did {child.id} think would help the most at first?",
            answer=f"{child.id} thought a billion tiny steps would help make the project perfect.",
        ),
        QAItem(
            question=f"What surprise appeared in the {project.label}?",
            answer=f"A silver sprout popped out of the {project.label}, which surprised everyone in the room.",
        ),
        QAItem(
            question=f"How did {helper.id} help {child.id} feel better?",
            answer=f"{helper.id} spoke gently and reminded {child.id} that one kind step can matter more than a billion imagined ones.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a science corner?",
            answer="A science corner is a small place where children can look closely, ask questions, and try simple experiments.",
        ),
        QAItem(
            question="What does progress mean?",
            answer="Progress means getting a little farther or a little better as you keep trying.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that happens when you do not know it is coming.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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


ASP_RULES = r"""
story(child, helper, project) :- child_name(child), helper_name(helper), project_name(project).
#show story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for gender, names in NAMES.items():
        for n in names:
            lines.append(asp.fact("child_name", n))
            lines.append(asp.fact("gender", n, gender))
    for hid, _ in HELPERS:
        lines.append(asp.fact("helper_name", hid))
    for pid, _ in PROJECTS:
        lines.append(asp.fact("project_name", pid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    if asp.atoms(model, "story"):
        print("OK: ASP rules produced a model.")
        return 0
    print("MISMATCH: ASP rules produced no story atoms.")
    return 1


CURATED = [
    StoryParams(name="Mina", gender="girl", helper="grandmother", project="seed_lens"),
    StoryParams(name="Theo", gender="boy", helper="teacher", project="star_jar"),
    StoryParams(name="Nora", gender="girl", helper="caretaker", project="bubble_map"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())

    if args.show_asp:
        print(asp_program())
        return

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
        print(sorted(asp.atoms(model, "story")))
        return

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
