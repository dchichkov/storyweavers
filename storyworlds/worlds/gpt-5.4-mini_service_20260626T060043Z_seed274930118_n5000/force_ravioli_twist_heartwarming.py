#!/usr/bin/env python3
"""
storyworlds/worlds/force_ravioli_twist_heartwarming.py
=======================================================

A small, heartwarming story world about a child, a stubborn problem,
and a cozy ravioli-shaped twist.

Seed tale:
---
Mina wanted to make ravioli with her grandma, but the dough kept springing
back when she tried to force it flat. Then Twist, the tiny kitchen cat,
knocked a spoon into the flour and made a funny heart-shaped mess. Mina
laughed, stopped forcing the dough, and learned to press it gently instead.
Grandma showed her how to pinch the edges with care, and the ravioli came
out sweet, tidy, and just right for dinner.

World idea:
- Physical meters: dough firmness, mess, warmth, fullness
- Emotional memes: frustration, patience, joy, tenderness
- The "twist" feature is a small helper/cat who turns tension into a kinder
  method.
- The story always starts with a forcey attempt, turns on a gentle correction,
  and ends with shared warmth and a finished bowl of ravioli.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandma"}
        male = {"boy", "father", "dad", "man", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Kitchen:
    place: str = "the kitchen"
    warmth: str = "cozy"
    affords: set[str] = field(default_factory=lambda: {"ravioli"})


@dataclass
class Tool:
    id: str
    label: str
    role: str
    method: str
    kind: str = "tool"


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, kitchen: Kitchen) -> None:
        self.kitchen = kitchen
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


def _name_label(name: str, fallback: str) -> str:
    return name if name else fallback


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming force-vs-gentleness ravioli story world.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "grandma", "grandpa"])
    ap.add_argument("--helper", choices=["Twist"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = ["Mina", "Luca", "Pia", "Noah", "Ada", "Eli", "Sana", "Theo"]
    parent_pool = ["mother", "father", "grandma", "grandpa"]
    return StoryParams(
        name=args.name or rng.choice(name_pool),
        gender=gender,
        parent=args.parent or rng.choice(parent_pool),
        helper=args.helper or "Twist",
    )


def make_world(params: StoryParams) -> World:
    w = World(Kitchen())
    child = w.add(Entity(id=params.name, kind="character", type=params.gender, membranes if False else None))
    # Above line intentionally invalid? No. Let's create cleanly below by reassigning.
    return w


def _init_world(params: StoryParams) -> World:
    w = World(Kitchen())
    child = w.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"dough": 0.0},
        memes={"frustration": 0.0, "patience": 0.0, "joy": 0.0, "tenderness": 0.0},
    ))
    parent_type = params.parent
    parent = w.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label=params.parent,
        meters={"warmth": 1.0},
        memes={"calm": 1.0, "joy": 0.0, "tenderness": 1.0},
    ))
    helper = w.add(Entity(
        id="Twist",
        kind="character",
        type="cat",
        label="Twist",
        meters={"mischief": 1.0},
        memes={"curiosity": 1.0, "love": 1.0},
    ))
    dough = w.add(Entity(
        id="dough",
        type="dough",
        label="dough",
        phrase="soft pasta dough",
        owner=child.id,
        caretaker=parent.id,
        meters={"firmness": 1.0, "mess": 0.0, "shape": 0.0},
        memes={"frustration": 0.0, "patience": 0.0},
    ))
    filling = w.add(Entity(
        id="filling",
        type="filling",
        label="cheese filling",
        phrase="soft cheese filling",
        owner=parent.id,
        caretaker=parent.id,
        meters={"tidy": 1.0},
    ))
    w.facts.update(child=child, parent=parent, helper=helper, dough=dough, filling=filling, params=params)
    return w


def run_story(w: World) -> None:
    f = w.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    helper: Entity = f["helper"]
    dough: Entity = f["dough"]

    w.say(f"{child.id} stood in {w.kitchen.place}, where everything felt warm and safe.")
    w.say(f"{child.id} loved helping make ravioli, because the little pasta pillows felt like tiny gifts.")
    w.say(f"{parent.label.capitalize()} set out flour, filling, and a bowl, and {helper.label} curled nearby like a comma.")
    w.para()

    # tension
    w.say(f"{child.id} tried to force the dough flat with both hands.")
    dough.meters["firmness"] += 1.0
    child.memes["frustration"] += 1.0
    child.meters["dough"] += 1.0

    if dough.meters["firmness"] >= THRESHOLD:
        w.say("But the dough kept springing back, as if it wanted a gentler answer.")
        w.say(f"{child.id} frowned and pressed harder, and the flour puffed up in a snowy cloud.")
        dough.meters["mess"] += 1.0
        child.memes["frustration"] += 1.0
    w.para()

    # twist turn
    w.say("Then Twist hopped onto the table and batted a spoon in a little swirl.")
    w.say("The spoon spun, the flour made a funny heart shape, and everybody laughed.")
    child.memes["joy"] += 1.0
    helper.memes["love"] += 1.0
    parent.memes["joy"] += 1.0

    w.say(f"{parent.label.capitalize()} said, “Try not to force it. Press it gently, like a hug.”")
    child.memes["patience"] += 1.0
    child.memes["frustration"] = 0.0
    dough.meters["firmness"] = 0.3
    w.say(f"{child.id} slowed down, touched the dough softly, and saw it relax under careful fingers.")

    # resolution
    w.para()
    dough.meters["shape"] += 1.0
    dough.meters["mess"] = 0.0
    child.memes["tenderness"] += 1.0
    parent.memes["tenderness"] += 1.0
    w.say(f"Together they tucked in the filling, pinched the edges, and made tidy ravioli with little ridges.")
    w.say(f"At dinner, the bowl came to the table steaming and sweet, and {helper.label} watched from a chair like a proud, fluffy judge.")
    w.say(f"{child.id} smiled because the best part was not forcing anything at all. It was learning the gentle way.")

    w.facts["resolved"] = True
    w.facts["heartwarming"] = True


def generate_story_text(params: StoryParams) -> World:
    w = _init_world(params)
    run_story(w)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    return [
        f'Write a heartwarming story for a young child about {child.id}, ravioli, and a tiny twist of luck.',
        f"Tell a gentle kitchen story where {child.id} tries to force ravioli dough, then learns a kinder way with Twist.",
        "Write a warm story about making ravioli, a mistake in the flour, and a happy ending at dinner.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    helper: Entity = f["helper"]
    dough: Entity = f["dough"]
    return [
        QAItem(
            question=f"What did {child.id} first try to do with the ravioli dough?",
            answer=f"{child.id} first tried to force the dough flat with both hands, but it kept springing back.",
        ),
        QAItem(
            question=f"Who made the funny little twist that changed the mood in the kitchen?",
            answer=f"Twist the cat batted a spoon in a little swirl, and that turned the mistake into a sweet laugh.",
        ),
        QAItem(
            question=f"What did {parent.label} teach {child.id} to do instead of forcing the dough?",
            answer=f"{parent.label.capitalize()} taught {child.id} to press the dough gently, like a hug, so it would relax.",
        ),
        QAItem(
            question=f"How did the ravioli turn out at the end?",
            answer="The ravioli turned out tidy, sweet, and just right for dinner, with neat pinched edges.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ravioli?",
            answer="Ravioli are little pockets of pasta that are usually filled with cheese, meat, or vegetables.",
        ),
        QAItem(
            question="Why is gentle pressure better than forcing dough?",
            answer="Gentle pressure lets dough stretch without tearing or snapping back, so it stays soft and easy to shape.",
        ),
        QAItem(
            question="Why do people use flour on a table when making pasta?",
            answer="Flour helps keep dough from sticking to hands and the table while you shape it.",
        ),
        QAItem(
            question="What does a heartwarming story feel like?",
            answer="A heartwarming story feels kind, cozy, and hopeful, with people helping each other in a caring way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
child_forces_dough(C) :- child(C), attempts_force(C).
turns_gentle(C) :- child(C), hears_advice(C).
heartwarming_story(C) :- child(C), turns_gentle(C), twist_helps(T), helper(T).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("child", "Mina"),
        asp.fact("helper", "Twist"),
        asp.fact("attempts_force", "Mina"),
        asp.fact("twist_helps", "Twist"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show heartwarming_story/1."))
    atoms = asp.atoms(model, "heartwarming_story")
    if atoms:
        print("OK: ASP program recognizes the heartwarming twist.")
        return 0
    print("MISMATCH: ASP program did not produce the expected result.")
    return 1


def resolve_params_and_generate(args: argparse.Namespace, rng: random.Random) -> StorySample:
    params = resolve_params(args, rng)
    params.seed = args.seed
    world = generate(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> World:
    return generate_story_text(params)


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
        print(asp_program("#show heartwarming_story/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        cur = StoryParams(name="Mina", gender="girl", parent="grandma", helper="Twist")
        samples = [StorySample(
            params=cur,
            story=generate_story_text(cur).render(),
            prompts=generation_prompts(generate_story_text(cur)),
            story_qa=story_qa(generate_story_text(cur)),
            world_qa=world_knowledge_qa(generate_story_text(cur)),
            world=generate_story_text(cur),
        )]
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            world = generate_story_text(params)
            samples.append(StorySample(
                params=params,
                story=world.render(),
                prompts=generation_prompts(world),
                story_qa=story_qa(world),
                world_qa=world_knowledge_qa(world),
                world=world,
            ))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### sample {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
