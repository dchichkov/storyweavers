#!/usr/bin/env python3
"""
Standalone storyworld: a Rhyming Story set on a loading dock, with ruby,
yoyo, and a surprise turn.

The seed image:
A small child finds a ruby yoyo near a loading dock, follows a rhyme-like
trail of clues, and discovers a surprise that changes the mood from puzzled
to delighted.

The world model tracks:
- physical state: meters like dust, shine, wobble, open, hidden
- emotional state: memes like curiosity, worry, surprise, joy

The narration is state-driven: setup, a small snag, a reveal, and a finishing
image that proves what changed.
"""

from __future__ import annotations

import argparse
import dataclasses
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    hidden: bool = False
    opened: bool = False
    carried_by: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the loading dock"
    sound: str = "the dock went thump and bump"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
# Parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


GIRL_NAMES = ["Ruby", "Mia", "Luna", "Ivy", "Nora"]
BOY_NAMES = ["Finn", "Leo", "Max", "Theo", "Jack"]
TRAITS = ["curious", "brave", "tiny", "cheery", "bouncy"]

SETTINGS = {
    "loading_dock": Setting(place="the loading dock", sound="the dock went thump and bump"),
}


# ---------------------------------------------------------------------------
# ASP twin facts/rules
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show surprise_story/1.

surprise_story(loading_dock) :- place(loading_dock), has(ruby), has(yoyo), surprise(dock_box).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("place", "loading_dock"))
    lines.append(asp.fact("has", "ruby"))
    lines.append(asp.fact("has", "yoyo"))
    lines.append(asp.fact("surprise", "dock_box"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show surprise_story/1."))
    atoms = set(asp.atoms(model, "surprise_story"))
    expected = {("loading_dock",)}
    if atoms == expected:
        print("OK: ASP gate matches Python story rule (1 surprise story).")
        return 0
    print("MISMATCH between ASP and Python story rule.")
    print("  ASP:", sorted(atoms))
    print("  PY :", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(SETTINGS["loading_dock"])

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"curiosity": 1.0, "joy": 0.0, "worry": 0.0, "surprise": 0.0},
        memes={"curiosity": 1.0, "joy": 0.0, "worry": 0.0, "surprise": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
    ))
    ruby = world.add(Entity(
        id="ruby",
        kind="thing",
        type="gem",
        label="ruby",
        phrase="a shiny red ruby",
        owner=child.id,
        carried_by=child.id,
        meters={"shine": 1.0},
    ))
    yoyo = world.add(Entity(
        id="yoyo",
        kind="thing",
        type="toy",
        label="yoyo",
        phrase="a little yoyo",
        owner=child.id,
        carried_by=child.id,
        meters={"wobble": 1.0},
    ))
    box = world.add(Entity(
        id="dock_box",
        kind="thing",
        type="box",
        label="box",
        phrase="a cardboard box by the dock door",
        hidden=True,
        meters={"closed": 1.0},
    ))
    ribbon = world.add(Entity(
        id="ribbon",
        kind="thing",
        type="ribbon",
        label="ribbon",
        phrase="a bright ribbon tied in a bow",
        hidden=True,
        meters={"hidden": 1.0},
    ))

    world.facts.update(
        child=child,
        parent=parent,
        ruby=ruby,
        yoyo=yoyo,
        box=box,
        ribbon=ribbon,
        place=world.setting.place,
        sound=world.setting.sound,
    )

    # Act 1: setup
    world.say(
        f"{params.name} was a {params.trait} little {params.gender} who loved a ruby yoyo."
    )
    world.say(
        f"At the loading dock, {world.setting.sound}, and {params.name} liked the lively hop of the string."
    )
    world.say(
        f"{params.name} held the ruby yoyo and gave it a spin; the red gleam flashed like a tiny sun."
    )

    # Act 2: tension
    world.para()
    child.memes["curiosity"] += 1.0
    child.meters["curiosity"] += 1.0
    world.say(
        f"Then {params.name} spotted a box near the dock door and wondered why it sat so still."
    )
    child.memes["worry"] += 1.0
    child.meters["worry"] += 1.0
    world.say(
        f"The box looked sealed tight, and that made {params.name} feel a little puzzled and small."
    )
    world.say(
        f"{params.name} tugged the string, and the yoyo went zip-zap, tip-tap, over the rough dock boards."
    )

    # Reveal
    box.hidden = False
    box.opened = True
    ribbon.hidden = False
    world.para()
    child.memes["surprise"] += 1.0
    child.meters["surprise"] += 1.0
    child.memes["joy"] += 2.0
    child.meters["joy"] += 2.0
    world.say(
        f"Surprise! The box was not empty at all."
    )
    world.say(
        f"Inside was a bright ribbon, and it was wound around a note that said, 'For a happy spin.'"
    )
    world.say(
        f"{params.name} smiled wide, because the surprise turned the dock from plain and gray to bright and sweet."
    )

    # Resolution image
    world.para()
    world.say(
        f"So {params.name} tied the ribbon to the yoyo, gave it one last whirl, and watched the ruby twirl."
    )
    world.say(
        f"The loading dock still went thump and bump, but now it sounded like a drum for a cheerful rhyme."
    )
    world.say(
        f"{params.name} laughed with {parent.label}, and the ruby yoyo shone as the sun slipped low."
    )

    world.facts["resolved"] = True
    return world


def generate_story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short rhyming story about a ruby yoyo, a loading dock, and a surprise.",
        "Tell a child-friendly tale where a small character finds a shiny ruby yoyo near a loading dock and discovers a surprise in a box.",
        "Create a gentle rhyming story with bumping dock sounds, a spinning yoyo, and a happy surprise ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    ruby = f["ruby"]
    yoyo = f["yoyo"]
    box = f["box"]

    return [
        QAItem(
            question=f"What did {child.id} love at the loading dock?",
            answer=f"{child.id} loved a ruby yoyo and liked how the red ruby gleamed when it spun.",
        ),
        QAItem(
            question=f"What did {child.id} find near the dock door?",
            answer=f"{child.id} found a box near the dock door, and it held a surprise inside.",
        ),
        QAItem(
            question=f"How did the surprise change {child.id}'s mood?",
            answer=f"The surprise made {child.id} feel delighted, less puzzled, and much more joyful.",
        ),
        QAItem(
            question=f"What made the loading dock sound lively?",
            answer=f"The dock went thump and bump, and the yoyo made a zip-zap, tip-tap sound too.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a yoyo?",
            answer="A yoyo is a small toy that goes up and down on a string when you move your hand.",
        ),
        QAItem(
            question="What is a ruby?",
            answer="A ruby is a bright red gemstone that can shine like a tiny light.",
        ),
        QAItem(
            question="What is a loading dock?",
            answer="A loading dock is a place where boxes and goods are brought in or moved out near doors and trucks.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you do not expect, so it can make you gasp, smile, or laugh.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        bits = []
        if ent.label:
            bits.append(f"label={ent.label}")
        if ent.phrase:
            bits.append(f"phrase={ent.phrase}")
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if ent.carried_by:
            bits.append(f"carried_by={ent.carried_by}")
        if ent.hidden:
            bits.append("hidden=True")
        if ent.opened:
            bits.append("opened=True")
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"  {ent.id} ({ent.kind}/{ent.type}) " + " ".join(bits))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Storyworld interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story world set on a loading dock with ruby, yoyo, and surprise.")
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=generate_story_text(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show surprise_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show surprise_story/1."))
        atoms = sorted(set(asp.atoms(model, "surprise_story")))
        print(f"{len(atoms)} ASP story facts:")
        for a in atoms:
            print(" ", a)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [
            generate(StoryParams(name="Ruby", gender="girl", parent="mother", trait="curious")),
            generate(StoryParams(name="Finn", gender="boy", parent="father", trait="bouncy")),
            generate(StoryParams(name="Ivy", gender="girl", parent="mother", trait="cheery")),
        ]
    else:
        samples = []
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
