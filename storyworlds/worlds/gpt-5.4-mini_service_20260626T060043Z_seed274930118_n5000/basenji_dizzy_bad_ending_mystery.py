#!/usr/bin/env python3
"""
A small story world for a mystery tale with a basenji, a dizzy child, and a bad ending.

Premise:
- A child notices something missing in a quiet home.
- A basenji is nearby, acting odd and slippery with clues.
- The child follows signs, gets dizzy, and the search turns into a small mystery.

World model:
- Physical meters: missingness, dirt, movement, dizziness, worry.
- Emotional memes: curiosity, fear, relief, disappointment.

The story is intentionally a "bad ending": the mystery does not resolve cleanly,
and the final image shows what was lost or ruined.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Scene:
    place: str = "the front room"
    clue_place: str = "the hallway"
    weather: str = "rainy"
    mystery: str = "the missing blue ribbon"
    bad_ending: bool = True


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        import copy

        w = World(self.scene)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    basenji_name: str
    seed: Optional[int] = None


NAMES_GIRL = ["Mia", "Nora", "Lina", "Ava", "Zoe", "Iris"]
NAMES_BOY = ["Theo", "Ben", "Leo", "Max", "Finn", "Owen"]
BASENJI_NAMES = ["Pip", "Tiki", "Juno", "Bix", "Momo"]
PARENTS = ["mother", "father"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world with a basenji and a dizzy child.")
    ap.add_argument("--name", choices=NAMES_GIRL + NAMES_BOY)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--basenji-name", choices=BASENJI_NAMES)
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
    if args.name:
        name = args.name
    else:
        name = rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(PARENTS)
    basenji_name = args.basenji_name or rng.choice(BASENJI_NAMES)
    return StoryParams(name=name, gender=gender, parent=parent, basenji_name=basenji_name)


def _child_label(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def tell(params: StoryParams) -> World:
    scene = Scene()
    w = World(scene)

    child = w.add(Entity(id="child", kind="character", type=_child_label(params.gender), label=params.name))
    parent = w.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    dog = w.add(Entity(id="dog", kind="character", type="basenji", label=params.basenji_name))
    missing = w.add(Entity(
        id="mystery",
        kind="thing",
        type="ribbon",
        label="blue ribbon",
        phrase="the blue ribbon from the chair",
        owner=child.id,
        caretaker=parent.id,
        meters={"missing": 1.0},
    ))
    shiny = w.add(Entity(
        id="key",
        kind="thing",
        type="key",
        label="silver key",
        phrase="a small silver key",
        owner=parent.id,
        caretaker=parent.id,
        meters={"hidden": 1.0},
    ))

    # Act 1: setup
    w.say(f"{child.label} was a little {_child_label(params.gender)} who loved quiet rooms and small clues.")
    w.say(f"{params.basenji_name} was a basenji with bright eyes and a nose that never stopped working.")
    w.say(f"One gray afternoon, {child.label}'s {params.parent} noticed that {scene.mystery} was gone from the chair.")
    w.say(f"The room felt still, but something about {params.basenji_name} looked too lively to ignore.")

    # Act 2: mystery builds
    w.para()
    child.memes["curiosity"] = 1.0
    parent.memes["worry"] = 1.0
    dog.meters["movement"] = 1.0
    dog.memes["mischief"] = 1.0
    child.meters["searching"] = 1.0
    w.say(f"{child.label} checked under the table, behind the couch, and next to the basket.")
    w.say(f"Near the hallway, there was a soft tug of air and a tiny silver flash.")
    w.say(f"{params.basenji_name} bounced past the doorway with a little scrap of ribbon on {dog.pronoun('possessive')} nose.")

    # Dizziness turn
    child.meters["spinning"] = 1.0
    child.meters["dizzy"] = 1.0
    child.memes["fear"] = 1.0
    w.say(f"{child.label} hurried after {params.basenji_name}, but the turns around the hall made {child.pronoun()} dizzy.")
    w.say(f"The hallway seemed to loop and loop, and the clue kept slipping out of sight.")

    # Bad ending: the ribbon is ruined and the mystery stays partly unsolved
    w.para()
    missing.meters["dirty"] = 1.0
    missing.meters["torn"] = 1.0
    dog.meters["chewed"] = 1.0
    child.memes["disappointment"] = 1.0
    parent.memes["sadness"] = 1.0
    w.say(f"At last, {params.basenji_name} dropped the ribbon near the door, but it was crumpled and damp.")
    w.say(f"The {params.parent} found the silver key later inside a coat pocket, yet the blue ribbon stayed torn on the floor.")
    if scene.bad_ending:
        w.say(f"{child.label} sat very still while {params.basenji_name} curled up by the mat, and the room felt less like a mystery than a little loss.")

    w.facts.update(
        child=child,
        parent=parent,
        dog=dog,
        missing=missing,
        shiny=shiny,
        scene=scene,
        bad_ending=True,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    dog = f["dog"]
    return [
        f'Write a short mystery story for a young child about {child.label} and a basenji named {dog.label}.',
        f'Write a gentle but sad mystery where a dizzy child follows a clue and the ending is not fully happy.',
        f'Write a story that includes a basenji, a missing ribbon, and a dizzy search through a quiet house.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    dog = f["dog"]
    missing = f["missing"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {child.label}, {child.pronoun('subject')} {parent.label}, and a basenji named {dog.label}.",
        ),
        QAItem(
            question=f"What mystery started the story?",
            answer=f"The mystery was that {missing.label} was missing from the chair.",
        ),
        QAItem(
            question=f"Why did {child.label} feel dizzy?",
            answer=f"{child.label} felt dizzy because {dog.label} led the search around and around the hallway, and the turns made {child.pronoun()} wobble.",
        ),
        QAItem(
            question=f"What happened to the blue ribbon at the end?",
            answer=f"The blue ribbon was found, but it was crumpled, damp, and torn, so the ending stayed sad.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a basenji?",
            answer="A basenji is a dog breed known for being quick, alert, and hard to ignore when it finds something interesting.",
        ),
        QAItem(
            question="What does it mean to feel dizzy?",
            answer="Feeling dizzy means the room feels as if it is turning or wobbling, so standing and walking can feel hard.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:8} ({e.type:8}) meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"  facts: bad_ending={world.facts.get('bad_ending')}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("kind", "basenji"),
            asp.fact("feels", "dizzy"),
            asp.fact("story_mode", "mystery"),
            asp.fact("ending", "bad"),
        ]
    )


ASP_RULES = r"""
#show kind/1.
#show feels/1.
#show story_mode/1.
#show ending/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show kind/1. #show feels/1. #show story_mode/1. #show ending/1."))
    atoms = set((a.name, tuple(str(x) for x in a.arguments)) for a in model)
    want = {
        ("kind", ("basenji",)),
        ("feels", ("dizzy",)),
        ("story_mode", ("mystery",)),
        ("ending", ("bad",)),
    }
    if atoms != want:
        print("MISMATCH")
        print("got:", sorted(atoms))
        print("want:", sorted(want))
        return 1
    print("OK: ASP parity verified.")
    return 0


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
        print(format_qa(sample))


CURATED = [
    StoryParams(name="Mia", gender="girl", parent="mother", basenji_name="Pip"),
    StoryParams(name="Theo", gender="boy", parent="father", basenji_name="Juno"),
    StoryParams(name="Ava", gender="girl", parent="father", basenji_name="Bix"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show kind/1. #show feels/1. #show story_mode/1. #show ending/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                samples.append(s)
                seen.add(s.story)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
