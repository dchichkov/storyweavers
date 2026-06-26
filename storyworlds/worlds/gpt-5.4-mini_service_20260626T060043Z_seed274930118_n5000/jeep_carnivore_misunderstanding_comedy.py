#!/usr/bin/env python3
"""
Jeep + carnivore misunderstanding comedy world.

A small child hears the word "carnivore" and makes a very funny mistake:
they think it means a creature that likes jeeps. The grown-up has to explain
that carnivores eat meat, not cars, while the child keeps trying to rescue
the jeep from the pretend monster. In the end, the confusion turns into a
ride and a laugh.
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
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    sits_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"dust": 0.0, "bumps": 0.0, "dirty": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "fear": 0.0, "embarrassment": 0.0, "confusion": 0.0, "amusement": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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

@dataclass
class StoryParams:
    setting: str = "safari"
    name: str = "Milo"
    gender: str = "boy"
    parent: str = "mom"
    seed: Optional[int] = None


SETTINGS = {
    "safari": "the safari lot",
    "zoo": "the zoo gate",
    "parking": "the sunny parking lot",
}

CHILD_NAMES = {
    "boy": ["Milo", "Toby", "Finn", "Leo", "Noah", "Ben"],
    "girl": ["Luna", "Mia", "Zoe", "Ivy", "Nora", "Ada"],
}

PARENTS = {
    "mom": "mom",
    "dad": "dad",
}

CARNIVORE_FACTS = [
    "A carnivore is an animal that eats meat.",
    "Lions, wolves, and cats are carnivores.",
    "The word does not mean 'car eater' or 'jeep eater'.",
]

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A misunderstanding happens when the child hears "carnivore" and invents a wrong meaning.
misunderstanding(child, carnivore) :- hears(child, carnivore), wrong_guess(child, jeep_eater).

% A joke resolution happens when the parent explains the real meaning and the child laughs.
resolved(child) :- misunderstanding(child, carnivore), explains(parent, carnivore), laughs(child).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("hears", "child", "carnivore"))
    lines.append(asp.fact("wrong_guess", "child", "jeep_eater"))
    lines.append(asp.fact("explains", "parent", "carnivore"))
    lines.append(asp.fact("laughs", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show misunderstanding/2. #show resolved/1."))
    seen_m = set(asp.atoms(model, "misunderstanding"))
    seen_r = set(asp.atoms(model, "resolved"))
    py_m = {("child", "carnivore")}
    py_r = {("child",)}
    if seen_m == py_m and seen_r == py_r:
        print("OK: clingo gate matches Python gate.")
        return 0
    print("MISMATCH:")
    print("  clingo misunderstanding:", sorted(seen_m))
    print("  python misunderstanding:", sorted(py_m))
    print("  clingo resolved:", sorted(seen_r))
    print("  python resolved:", sorted(py_r))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def reasonableness_gate(params: StoryParams) -> None:
    if params.gender not in CHILD_NAMES:
        raise StoryError("Unsupported gender.")
    if params.setting not in SETTINGS:
        raise StoryError("Unsupported setting.")
    if params.parent not in PARENTS:
        raise StoryError("Unsupported parent role.")


def build_world(params: StoryParams) -> World:
    world = World(setting=SETTINGS[params.setting])

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        owner=None,
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=PARENTS[params.parent],
    ))
    jeep = world.add(Entity(
        id="jeep",
        kind="thing",
        type="jeep",
        label="jeep",
        phrase="a shiny red jeep",
        caretaker=parent.id,
        sits_in=world.setting,
    ))

    # Act 1: setup.
    child.memes["joy"] += 1
    world.say(
        f"{child.name_or_label()} was at {world.setting} with {parent.label}. "
        f"They saw a shiny red jeep and smiled at how bouncy it looked."
    )
    world.say(
        f"Nearby, someone said the word 'carnivore'. {child.name_or_label()} froze, "
        f"because it sounded like a creature that might want to nibble the jeep."
    )

    # Act 2: misunderstanding.
    world.para()
    child.memes["confusion"] += 2
    child.memes["fear"] += 1
    jeep.meters["bumps"] += 0.5
    world.say(
        f"{child.name_or_label()} pointed at the jeep and whispered, "
        f'"Is that a carnivore?"'
    )
    world.say(
        f"{parent.label.capitalize()} laughed so hard {parent.pronoun('subject')} had to hold "
        f"{parent.pronoun('possessive')} stomach. "
        f'"No, sweetie," {parent.pronoun("subject")} said. "A carnivore eats meat, not cars."'
    )

    # Act 3: explanation and joke payoff.
    world.para()
    child.memes["amusement"] += 2
    child.memes["fear"] = 0
    child.memes["confusion"] = 0
    child.memes["joy"] += 1
    world.say(
        f"{child.name_or_label()} looked at the jeep again, then at {parent.label}, "
        f"and made a tiny gasping laugh. "
        f'"Oh! So a carnivore is not a car-nivore!"'
    )
    world.say(
        f"{parent.label.capitalize()} nodded. "
        f"Together they read a quick fact: {random.choice(CARNIVORE_FACTS)} "
        f"Then {child.name_or_label()} climbed into the jeep, grinning at the silly mistake."
    )

    world.facts = {
        "child": child,
        "parent": parent,
        "jeep": jeep,
        "setting": params.setting,
    }
    return world


def story_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    return [
        f"Write a funny story for a young child named {child.name_or_label()} who misunderstands the word 'carnivore'.",
        f"Tell a short comedy about a jeep, a grown-up, and a child who thinks a carnivore might eat cars.",
        "Write a playful misunderstanding story that ends with an explanation and a laugh.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    jeep = world.facts["jeep"]
    setting = world.facts["setting"]

    return [
        QAItem(
            question=f"Who thought the carnivore might want to nibble the jeep?",
            answer=f"{child.name_or_label()} thought that at first, because {child.pronoun('subject')} misunderstood the word.",
        ),
        QAItem(
            question=f"What did {parent.label} explain about a carnivore?",
            answer="The parent explained that a carnivore is an animal that eats meat, not cars.",
        ),
        QAItem(
            question=f"What was the shiny vehicle at {setting}?",
            answer=f"It was {jeep.phrase}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a carnivore?",
            answer="A carnivore is an animal that eats meat.",
        ),
        QAItem(
            question="What is a jeep?",
            answer="A jeep is a sturdy vehicle with big wheels that can drive on rough roads.",
        ),
        QAItem(
            question="Why was the mistake funny?",
            answer="It was funny because the child mixed up a science word with a silly idea about cars.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy story world about jeep + carnivore misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--parent", choices=list(PARENTS))
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
    setting = args.setting or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(CHILD_NAMES[gender])
    parent = args.parent or rng.choice(list(PARENTS))
    return StoryParams(setting=setting, name=name, gender=gender, parent=parent)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show misunderstanding/2. #show resolved/1."))
    return sorted(set(asp.atoms(model, "misunderstanding")) | set(asp.atoms(model, "resolved")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show misunderstanding/2. #show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        model = asp_valid_combos()
        print(f"{len(model)} ASP facts about the misunderstanding story.")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for setting in SETTINGS:
            for gender in ["boy", "girl"]:
                params = StoryParams(setting=setting, name=CHILD_NAMES[gender][0], gender=gender, parent="mom")
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
