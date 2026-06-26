#!/usr/bin/env python3
"""
Standalone storyworld: a bedtime tale with a witch, a small twist, and a gentle ending.

The seed idea is simple:
A witch is trying to settle in for bedtime, but a tiny twist in the routine
changes the mood. The story should feel cozy, child-facing, concrete, and
state-driven, with a clear turn and resolution.
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
# Typed world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"witch", "girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Scene:
    place: str = "a cozy little cottage"
    setting_detail: str = "The moon was round and bright outside the window."
    bedtime_item: str = "a storybook"
    twist_item: str = "a tiny teacup"
    twist_name: str = "twist"
    weather: str = "quiet night"


@dataclass
class StoryParams:
    place: str
    bedtime_item: str
    twist_item: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.lines: list[str] = []
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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.scene)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "cottage": Scene(
        place="a cozy little cottage",
        setting_detail="The moon shone through the window, and the room felt soft and still.",
        bedtime_item="a storybook",
        twist_item="a tiny teacup",
    ),
    "tower": Scene(
        place="a tall sleepy tower",
        setting_detail="The tower was quiet, and the stairs whispered with every step.",
        bedtime_item="a quilt",
        twist_item="a crooked pillow",
    ),
    "garden_house": Scene(
        place="a little house by the garden",
        setting_detail="Crickets sang outside, and the curtains moved in the night breeze.",
        bedtime_item="a night lamp",
        twist_item="a teacup of warm milk",
    ),
}

BEDTIME_ITEMS = {
    "storybook": ("storybook", "a bedtime storybook"),
    "quilt": ("quilt", "a soft quilt"),
    "lamp": ("lamp", "a little night lamp"),
    "pillow": ("pillow", "a puffed-up pillow"),
}

TWIST_ITEMS = {
    "teacup": ("teacup", "a tiny teacup"),
    "sock": ("sock", "one missing sock"),
    "cat": ("cat", "a sleepy cat"),
    "star": ("star", "a paper star"),
}

NAMES = ["Mina", "Luna", "Ivy", "Wren", "Nora", "Tess", "Mara", "Poppy"]
TRAITS = ["gentle", "curious", "brave", "quiet", "cheerful", "sleepy"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def predict_twist(world: World, witch: Entity, bedtime_item: Entity, twist_item: Entity) -> bool:
    sim = world.copy()
    _twist(sim, sim.get(witch.id), sim.get(bedtime_item.id), sim.get(twist_item.id), narrate=False)
    item = sim.get(bedtime_item.id)
    return bool(item.meters.get("disrupted", 0.0) >= 1.0)


def _twist(world: World, witch: Entity, bedtime_item: Entity, twist_item: Entity, narrate: bool = True) -> None:
    if "twist" in world.fired:
        return
    world.fired.add("twist")
    _add_meter(bedtime_item, "disrupted", 1.0)
    _add_meter(witch, "surprised", 1.0)
    _add_meter(witch, "worry", 1.0)
    if narrate:
        world.say(
            f"Just then, the {twist_item.label} caused a tiny twist in the bedtime plan."
        )
        world.say(
            f"The {bedtime_item.label} would not settle the same easy way now."
        )


def _soften(world: World, witch: Entity, bedtime_item: Entity, twist_item: Entity) -> None:
    if "soften" in world.fired:
        return
    if witch.meters.get("worry", 0.0) < 1.0:
        return
    world.fired.add("soften")
    _add_meter(witch, "calm", 1.0)
    _add_meter(witch, "love", 1.0)
    world.say(
        f"The witch took one slow breath, patted the {twist_item.label}, and smiled."
    )
    world.say(
        f"She found a gentler way to keep bedtime cozy."
    )


def _solve(world: World, witch: Entity, bedtime_item: Entity, twist_item: Entity) -> None:
    if "solve" in world.fired:
        return
    if witch.meters.get("calm", 0.0) < 1.0:
        return
    world.fired.add("solve")
    _add_meter(bedtime_item, "ready", 1.0)
    _add_meter(witch, "joy", 1.0)
    world.say(
        f"She tucked the {twist_item.label} beside the {bedtime_item.label} and tried again."
    )
    world.say(
        f"This time, bedtime worked just right."
    )


def propagate(world: World, witch: Entity, bedtime_item: Entity, twist_item: Entity, narrate: bool = True) -> None:
    _twist(world, witch, bedtime_item, twist_item, narrate=narrate)
    _soften(world, witch, bedtime_item, twist_item)
    _solve(world, witch, bedtime_item, twist_item)


def tell(scene: Scene, bedtime_item_key: str, twist_item_key: str, name: str) -> World:
    world = World(scene)
    witch = world.add(Entity(
        id=name,
        kind="character",
        type="witch",
        label="witch",
        phrase=f"a witch named {name}",
    ))
    bedtime_label, bedtime_phrase = BEDTIME_ITEMS[bedtime_item_key]
    twist_label, twist_phrase = TWIST_ITEMS[twist_item_key]
    bedtime_item = world.add(Entity(
        id="bedtime_item",
        type=bedtime_label,
        label=bedtime_label,
        phrase=bedtime_phrase,
        caretaker=witch.id,
    ))
    twist_item = world.add(Entity(
        id="twist_item",
        type=twist_label,
        label=twist_label,
        phrase=twist_phrase,
    ))

    world.say(f"{witch.id} was a little witch who lived in {scene.place}.")
    world.say(f"She loved bedtime, especially {bedtime_phrase.lower()}.")
    world.say(scene.setting_detail)
    world.para()
    world.say(
        f"Tonight, she tried to settle down with {bedtime_phrase.lower()}, but {twist_phrase.lower()} waited nearby."
    )
    if predict_twist(world, witch, bedtime_item, twist_item):
        world.say(
            f"The witch noticed the tiny change and paused before it could make her grumpy."
        )
    propagate(world, witch, bedtime_item, twist_item, narrate=True)
    world.para()
    world.say(
        f"In the end, {witch.id} was calm, {bedtime_phrase.lower()} was ready, and the room felt sleepy and safe again."
    )

    world.facts.update(
        witch=witch,
        bedtime_item=bedtime_item,
        twist_item=twist_item,
        scene=scene,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    witch: Entity = f["witch"]
    return [
        f'Write a bedtime story for a young child about a witch named {witch.id} and a tiny twist.',
        f"Tell a gentle story where {witch.id} tries to settle down but a small change makes bedtime different.",
        f'Write a cozy story with the word "twist" where a witch finds a calm way to end the night.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    witch: Entity = f["witch"]
    bedtime_item: Entity = f["bedtime_item"]
    twist_item: Entity = f["twist_item"]
    scene: Scene = f["scene"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {witch.phrase} living in {scene.place}.",
        ),
        QAItem(
            question=f"What small thing caused the bedtime twist?",
            answer=f"The tiny twist came from {twist_item.phrase.lower()}, which made bedtime change a little.",
        ),
        QAItem(
            question=f"What did the witch want to do before the twist?",
            answer=f"She wanted to settle down with {bedtime_item.phrase.lower()} and make the night cozy.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended with the witch calm, the bedtime item ready, and the room quiet again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a witch in a bedtime story?",
            answer="A witch is a magical character in a story. In a bedtime tale, a witch can be gentle, kind, and sleepy too.",
        ),
        QAItem(
            question="What does a twist mean?",
            answer="A twist is a small change in what was expected. In a story, it can make the moment different without being scary.",
        ),
        QAItem(
            question="Why do people like bedtime routines?",
            answer="Bedtime routines help the night feel calm and familiar, which makes it easier to rest.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts:
% place(P).
% bedtime_item(B).
% twist_item(T).
% can_story(P,B,T).

can_story(P,B,T) :- place(P), bedtime_item(B), twist_item(T).

#show can_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for bid in BEDTIME_ITEMS:
        lines.append(asp.fact("bedtime_item", bid))
    for tid in TWIST_ITEMS:
        lines.append(asp.fact("twist_item", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show can_story/3."))
    return sorted(set(asp.atoms(model, "can_story")))


def asp_verify() -> int:
    python_set = {(p, b, t) for p in PLACES for b in BEDTIME_ITEMS for t in TWIST_ITEMS}
    asp_set = set(asp_valid_combos())
    if asp_set == python_set:
        print(f"OK: ASP matches Python ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if asp_set - python_set:
        print("only in ASP:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("only in Python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Generation / params
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: a witch and a tiny twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--bedtime-item", choices=BEDTIME_ITEMS)
    ap.add_argument("--twist-item", choices=TWIST_ITEMS)
    ap.add_argument("--name", choices=NAMES)
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
    place = args.place or rng.choice(list(PLACES))
    scene = PLACES[place]
    bedtime_item = args.bedtime_item or rng.choice(list(BEDTIME_ITEMS))
    twist_item = args.twist_item or rng.choice(list(TWIST_ITEMS))
    if args.name:
        name = args.name
    else:
        name = rng.choice(NAMES)
    return StoryParams(
        place=place,
        bedtime_item=bedtime_item,
        twist_item=twist_item,
        name=name,
    )


def generate(params: StoryParams) -> StorySample:
    scene = PLACES[params.place]
    world = tell(scene, params.bedtime_item, params.twist_item, params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
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


CURATED = [
    StoryParams(place="cottage", bedtime_item="storybook", twist_item="teacup", name="Mina"),
    StoryParams(place="tower", bedtime_item="quilt", twist_item="sock", name="Luna"),
    StoryParams(place="garden_house", bedtime_item="lamp", twist_item="cat", name="Ivy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for p, b, t in combos:
            print(f"  {p:12} {b:12} {t:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
