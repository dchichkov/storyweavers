#!/usr/bin/env python3
"""
A small story world about a fallen tree trail, a strange bulb, a smear of ketchup,
and a spooky little misunderstanding that turns into a surprise.

The world is built to feel like a gentle ghost story:
- a dim trail
- a repeated sound or phrase
- a mistaken idea about what a glowing object means
- a surprise ending that proves what changed
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

@dataclass
class Item:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    held_by: Optional[str] = None
    glowing: bool = False
    sticky: bool = False


@dataclass
class Entity:
    id: str
    kind: str = "character"
    label: str = ""
    type: str = "child"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    fallen_tree: bool = True
    trail: bool = True
    dimness: float = 0.0


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity | Item] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity | Item) -> Entity | Item:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity | Item:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    name: str
    kind: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

NAMES = ["Mina", "Owen", "Piper", "Nico", "Tess", "Levi", "Ruby", "Jules"]
KINDS = ["girl", "boy"]
HELPERS = ["grandpa", "older sister", "neighbor", "aunt", "dad", "mom"]

PLACE = Place(
    id="fallen_tree_trail",
    label="the fallen tree trail",
    fallen_tree=True,
    trail=True,
    dimness=1.0,
)

BULB = {
    "id": "bulb",
    "label": "a tiny glass bulb",
}
KETCHUP = {
    "id": "ketchup",
    "label": "a ketchup bottle",
}
GIMMICK = {
    "id": "gimmick",
    "label": "a little gimmick",
}


# ---------------------------------------------------------------------------
# Core story logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(PLACE)
    child = world.add(Entity(id="child", label=params.name, type=params.kind))
    helper = world.add(Entity(id="helper", label=params.helper, type="adult"))
    bulb = world.add(Item(id="bulb", kind="object", label=BULB["label"], glowing=True))
    ketchup = world.add(Item(id="ketchup", kind="object", label=KETCHUP["label"], sticky=True))
    gimmick = world.add(Item(id="gimmick", kind="object", label=GIMMICK["label"]))

    world.facts.update(child=child, helper=helper, bulb=bulb, ketchup=ketchup, gimmick=gimmick)
    return world


def remember_repetition(world: World, phrase: str) -> None:
    world.say(phrase)
    world.say(phrase)


def story_intro(world: World) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    world.say(
        f"{child.label} and {helper.label} walked onto {world.place.label} where a fallen tree lay across the trail."
    )
    world.say(
        f"The branches were still and dark, and the trail looked like it was holding its breath."
    )


def story_misunderstanding(world: World) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    bulb: Item = world.facts["bulb"]  # type: ignore[assignment]
    ketchup: Item = world.facts["ketchup"]  # type: ignore[assignment]
    gimmick: Item = world.facts["gimmick"]  # type: ignore[assignment]

    world.say(
        f"Then {child.label} found {bulb.label}, and its tiny glow blinked in the leaves."
    )
    remember_repetition(world, "Tap. Tap.")
    world.say(
        f"{child.label} whispered, 'A ghost light.'"
    )
    world.say(
        f"But {gimmick.label} had a trick: when it was squeezed, it made a red trail like {ketchup.label}."
    )
    world.say(
        f"{child.label} saw the red shine and thought the trail was haunted by someone hungry."
    )
    world.facts["misunderstanding"] = True
    world.facts["repetition"] = "Tap. Tap."


def story_turn(world: World) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    bulb: Item = world.facts["bulb"]  # type: ignore[assignment]
    gimmick: Item = world.facts["gimmick"]  # type: ignore[assignment]

    world.say(
        f"{helper.label} knelt beside the log and smiled. 'That is not a ghost,' {helper.label} said."
    )
    world.say(
        f"'The bulb is only a bulb, and the red mark is only the gimmick doing its job.'"
    )
    world.say(
        f"{child.label} blinked at the little glow again."
    )
    remember_repetition(world, "Tap. Tap.")
    world.say(
        f"This time the sound was just the bulb bumping softly against the wood."
    )
    world.facts["misunderstanding"] = False
    world.facts["surprise"] = "the light was friendly"


def story_resolution(world: World) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    bulb: Item = world.facts["bulb"]  # type: ignore[assignment]
    ketchup: Item = world.facts["ketchup"]  # type: ignore[assignment]

    world.say(
        f"Then came the surprise: under the log, {helper.label} found a snack with {ketchup.label} for everyone."
    )
    world.say(
        f"The red smear was from lunch, not from a ghost at all."
    )
    world.say(
        f"{child.label} laughed, and the trail did not feel spooky anymore."
    )
    world.say(
        f"The little bulb still glowed, but now it looked like a cozy night light on a walk home."
    )
    world.facts["resolved"] = True
    world.facts["ending_image"] = "a cozy bulb on the fallen tree trail"


def generate_world(params: StoryParams) -> World:
    world = build_world(params)
    story_intro(world)
    world.para()
    story_misunderstanding(world)
    world.para()
    story_turn(world)
    world.para()
    story_resolution(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    return [
        "Write a gentle ghost story for a small child with a strange glow, a red smear, and a happy ending.",
        f"Tell a story about {child.label} on the fallen tree trail where a bulb and a ketchup bottle cause a misunderstanding.",
        "Use repetition and a surprise reveal, and keep the story cozy instead of scary.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question=f"Where did {child.label} and {helper.label} walk?",
            answer=f"They walked onto the fallen tree trail, where a tree lay across the path and made the place feel dim.",
        ),
        QAItem(
            question=f"What made {child.label} think something ghostly was there?",
            answer=f"{child.label} saw the tiny bulb glow in the leaves and heard the repeated 'Tap. Tap.' sound, so it seemed spooky at first.",
        ),
        QAItem(
            question="What did the red mark turn out to be?",
            answer="It turned out to be ketchup from a snack, not a ghost at all.",
        ),
    ]
    if world.facts.get("misunderstanding") is False:
        qa.append(
            QAItem(
                question="How was the misunderstanding fixed?",
                answer=f"{helper.label} explained that the bulb was only a bulb and the gimmick was only making the red mark, so {child.label} stopped being worried.",
            )
        )
    if world.facts.get("resolved"):
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended with {child.label} laughing, the bulb glowing softly, and the trail feeling cozy instead of spooky.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bulb?",
            answer="A bulb is a glass thing that can shine with light when it is turned on or made to glow.",
        ),
        QAItem(
            question="What is ketchup?",
            answer="Ketchup is a thick red sauce that often goes on food like fries or sandwiches.",
        ),
        QAItem(
            question="What is a gimmick?",
            answer="A gimmick is a trick or special device meant to get attention or make something work in a clever way.",
        ),
        QAItem(
            question="What makes a fallen tree trail feel spooky?",
            answer="A fallen tree trail can feel spooky because the path is darker, quieter, and more crowded with branches than a normal trail.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
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
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        if isinstance(ent, Entity):
            lines.append(f"{ent.id}: Entity(label={ent.label!r}, type={ent.type!r}, meters={ent.meters}, memes={ent.memes})")
        else:
            lines.append(
                f"{ent.id}: Item(label={ent.label!r}, glowing={ent.glowing}, sticky={ent.sticky}, meters={ent.meters}, memes={ent.memes})"
            )
    lines.append(f"facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts:
% place(fallen_tree_trail).
% child(Name, Kind).
% helper(Label).
% bulb.
% ketchup.
% gimmick.

misunderstanding(A) :- sees(A, bulb), hears(A, tap_twice), red_mark(ketchup).
repetition(tap_twice) :- hears(A, tap_twice).
surprise(revealed_snack) :- explained(helper), not ghost_true.
cozy_end(A) :- not misunderstanding(A), surprise(revealed_snack).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("place", "fallen_tree_trail"),
        asp.fact("trail", "fallen_tree_trail"),
        asp.fact("fallen_tree", "fallen_tree_trail"),
        asp.fact("bulb"),
        asp.fact("ketchup"),
        asp.fact("gimmick"),
    ]
    for name in NAMES:
        lines.append(asp.fact("name", name))
    for kind in KINDS:
        lines.append(asp.fact("kind", kind))
    for helper in HELPERS:
        lines.append(asp.fact("helper", helper))
    lines.append(asp.fact("hears", "child", "tap_twice"))
    lines.append(asp.fact("sees", "child", "bulb"))
    lines.append(asp.fact("red_mark", "ketchup"))
    lines.append(asp.fact("explained", "helper"))
    lines.append(asp.fact("ghost_true", "false"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show misunderstanding/1.\n#show repetition/1.\n#show surprise/1.\n#show cozy_end/1."))
    shown = set((sym.name, tuple(getattr(a, "name", getattr(a, "string", getattr(a, "number", None))) for a in sym.arguments)) for sym in model)

    expected = {
        ("misunderstanding", ("child",)),
        ("repetition", ("tap_twice",)),
        ("surprise", ("revealed_snack",)),
        ("cozy_end", ("child",)),
    }
    if shown == expected:
        print("OK: ASP parity looks reasonable.")
        sample = generate(StoryParams(name="Mina", kind="girl", helper="dad", seed=1))
        if "bulb" not in sample.story or "ketchup" not in sample.story or "gimmick" not in sample.story:
            print("ERROR: generated story missing required seed words.")
            return 1
        return 0
    print("ASP mismatch:")
    print("shown:", sorted(shown))
    print("expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world on a fallen tree trail.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--kind", choices=KINDS)
    ap.add_argument("--helper", choices=HELPERS)
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
    name = args.name or rng.choice(NAMES)
    kind = args.kind or rng.choice(KINDS)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(name=name, kind=kind, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(name="Mina", kind="girl", helper="dad"),
    StoryParams(name="Owen", kind="boy", helper="older sister"),
    StoryParams(name="Ruby", kind="girl", helper="grandpa"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show misunderstanding/1.\n#show repetition/1.\n#show surprise/1.\n#show cozy_end/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show misunderstanding/1.\n#show repetition/1.\n#show surprise/1.\n#show cozy_end/1."))
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
