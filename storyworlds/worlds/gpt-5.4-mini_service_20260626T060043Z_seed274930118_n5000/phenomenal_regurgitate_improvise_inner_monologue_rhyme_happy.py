#!/usr/bin/env python3
"""
A tiny slice-of-life story world about a child performing a short rhyme at a
show-and-tell table, stumbling a little, then improvising a happier ending.

Seed words woven into the world:
- phenomenal
- regurgitate
- improvise

Narrative instruments:
- Inner Monologue
- Rhyme
- Happy Ending
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
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Scene:
    place: str
    audience: str
    prompt: str
    theme: str
    ending: str


@dataclass
class StoryParams:
    place: str
    audience: str
    prompt: str
    theme: str
    ending: str
    name: str = "Mina"
    seed: Optional[int] = None


PLACES = {
    "classroom": Scene(
        place="the classroom",
        audience="a circle of classmates",
        prompt="show-and-tell",
        theme="a tiny song about a rainy day",
        ending="the bell rang softly",
    ),
    "library": Scene(
        place="the library corner",
        audience="a pair of quiet friends",
        prompt="story time",
        theme="a rhyme about a brave paper boat",
        ending="the librarian smiled",
    ),
    "kitchen": Scene(
        place="the sunny kitchen",
        audience="a parent and a grandparent",
        prompt="a breakfast recital",
        theme="a song about pancakes and strawberries",
        ending="the toast popped up",
    ),
}

NAMES = ["Mina", "Toby", "Jun", "Lena", "Owen", "Nina"]
AUDIENCES = ["a circle of classmates", "a pair of quiet friends", "a parent and a grandparent"]
PROMPTS = ["show-and-tell", "story time", "a breakfast recital"]
THEMES = [
    "a tiny song about a rainy day",
    "a rhyme about a brave paper boat",
    "a song about pancakes and strawberries",
]
ENDINGS = [
    "the bell rang softly",
    "the librarian smiled",
    "the toast popped up",
]


class World:
    def __init__(self, place: Scene) -> None:
        self.scene = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world with rhyme and an inner monologue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_key = args.place or rng.choice(list(PLACES))
    scene = PLACES[place_key]
    return StoryParams(
        place=scene.place,
        audience=args.place and scene.audience or scene.audience,
        prompt=scene.prompt,
        theme=scene.theme,
        ending=scene.ending,
        name=args.name or rng.choice(NAMES),
    )


def inner_monologue(world: World, name: str) -> str:
    return (
        f"{name} thought, 'Be calm. If the words wobble, I can still "
        f"improvise and make them phenomenal.'"
    )


def tell(params: StoryParams) -> World:
    scene = next(s for s in PLACES.values() if s.place == params.place)
    world = World(scene)
    child = world.add(Entity(id="child", kind="character", label=params.name, type="child"))
    teacher = world.add(Entity(id="teacher", kind="character", label="Ms. Park", type="adult"))
    audience = world.add(Entity(id="audience", kind="group", label=params.audience, type="group"))

    child.meters["nervous"] = 1.0
    child.memes["hope"] = 1.0

    world.say(f"At {scene.place}, {params.name} stepped up for {scene.prompt}.")
    world.say(f"The plan was {scene.theme}, and the room felt very still.")
    world.say(inner_monologue(world, params.name))

    world.say(
        f"{params.name} began to rhyme: 'A cloud up high, a puddle below, / "
        f"I can sing my words even when they go slow.'"
    )
    child.meters["nervous"] = 0.4
    child.memes["pride"] = 1.0

    world.say(
        f"Then {params.name} forgot one line and had to regurgitate the next part in a quick, funny way."
    )
    world.say(
        f"That made a few smiles appear, because the mistake sounded playful instead of scary."
    )
    world.say(
        f"{params.name} decided to improvise: 'If the line slips free, I’ll chase it like a kite, / "
        f"and every small mistake can still turn out right.'"
    )
    child.meters["nervous"] = 0.0
    child.memes["joy"] = 1.0
    teacher.memes["warmth"] = 1.0

    world.say(
        f"{scene.audience.capitalize()} laughed kindly, and {scene.ending} just as the last rhyme landed."
    )
    world.say(
        f"{params.name} stood a little taller, because the whole moment had become a happy ending."
    )

    world.facts.update(
        name=params.name,
        place=scene.place,
        audience=scene.audience,
        prompt=scene.prompt,
        theme=params.theme,
        ending=params.ending,
        child=child,
        teacher=teacher,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    name = f["name"]
    return [
        QAItem(
            question=f"What was {name} trying to do at {f['place']}?",
            answer=f"{name} was trying to take part in {f['prompt']} with a small rhyme.",
        ),
        QAItem(
            question=f"What did {name} do after forgetting a line?",
            answer=f"{name} chose to improvise, which helped the performance keep going.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily, with everyone smiling and the final moment feeling calm and proud.",
        ),
    ]


def world_qa(_: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does improvise mean?",
            answer="To improvise means to make up a new way forward right away when the original plan slips.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like cat and hat.",
        ),
        QAItem(
            question="What does phenomenal mean?",
            answer="Phenomenal means very impressive or wonderful.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a slice-of-life story where {f['name']} performs at {f['place']} and uses a rhyme.",
        f"Tell a child-friendly story that includes the words phenomenal, regurgitate, and improvise.",
        f"Make a gentle story about a small mistake during {f['prompt']} and a happy ending.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"  {ent.id:8} ({ent.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
name(child,mina).
place(classroom).
place(library).
place(kitchen).
good_story(P) :- place(P).
#show good_story/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for key in PLACES:
        lines.append(asp.fact("place", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
        print(asp_program("#show good_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for key, scene in PLACES.items():
            params = StoryParams(
                place=scene.place,
                audience=scene.audience,
                prompt=scene.prompt,
                theme=scene.theme,
                ending=scene.ending,
                name="Mina",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
