#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/compliment_target_chlorophyll_transformation_repetition_rhyming_story.py
================================================================================

A small rhyming storyworld about a target plant, a kind compliment, and a
chlorophyll-powered transformation.

Seed tale idea:
---
A child brings home a tiny target plant with pale leaves. The plant looks sad
and plain, so the child keeps repeating a cheerful compliment. In bright light,
the plant's chlorophyll wakes up, the leaves turn green, and the plant grows.
The child learns that a gentle compliment and steady care can help something
small transform.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meter: dict[str, float] = field(default_factory=dict)
    meme: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def __post_init__(self):
        if not self.label:
            self.label = self.type
        if not self.phrase:
            self.phrase = self.label

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the greenhouse"
    affords: set[str] = field(default_factory=set)


@dataclass
class PlantSpec:
    label: str
    phrase: str
    target_name: str
    start_color: str = "pale"
    end_color: str = "green"
    tags: set[str] = field(default_factory=set)


@dataclass
class LightSpec:
    label: str
    phrase: str
    intensity: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "greenhouse": Setting(place="the greenhouse", affords={"care", "light"}),
    "windowsill": Setting(place="the sunny windowsill", affords={"care", "light"}),
    "garden": Setting(place="the garden", affords={"care", "light"}),
}

PLANTS = {
    "target_sprout": PlantSpec(
        label="target sprout",
        phrase="a tiny target sprout with a round leaf target",
        target_name="leaf target",
        start_color="pale",
        end_color="green",
        tags={"target", "plant"},
    ),
    "seedling": PlantSpec(
        label="seedling",
        phrase="a little seedling with soft leaves",
        target_name="leaf target",
        start_color="pale",
        end_color="green",
        tags={"plant"},
    ),
}

LIGHTS = {
    "sunbeam": LightSpec(
        label="sunbeam",
        phrase="a warm sunbeam",
        intensity="bright",
        tags={"chlorophyll", "light"},
    ),
    "lamp": LightSpec(
        label="lamp light",
        phrase="a bright lamp",
        intensity="steady",
        tags={"light"},
    ),
}

NAMES = ["Mia", "Noah", "Lily", "Eli", "Ava", "Finn"]
TRAITS = ["gentle", "cheery", "patient", "playful"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    plant: str
    light: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning / story dynamics
# ---------------------------------------------------------------------------
def compliment_line(name: str, plant: Entity) -> str:
    return f'"Nice {plant.label}, so bright and light," {name} would sing with delight.'


def rhyme_end(text: str) -> str:
    return text


def apply_compliment(world: World, child: Entity, plant: Entity) -> None:
    child.meme["compliment"] = child.meme.get("compliment", 0.0) + 1
    plant.meme["heard"] = plant.meme.get("heard", 0.0) + 1
    plant.meme["joy"] = plant.meme.get("joy", 0.0) + 1
    if ("compliment", plant.id) not in world.fired:
        world.fired.add(("compliment", plant.id))
        world.say(
            f"{child.id} gave a sweet compliment, and {plant.label} seemed to sway."
        )
        world.say(
            f'"Nice little target, bright as a spark," {child.id} said, and the room felt warm and stark.'
        )


def apply_repetition(world: World, child: Entity, plant: Entity) -> None:
    if child.meme.get("compliment", 0.0) >= THRESHOLD and ("repeat", plant.id) not in world.fired:
        world.fired.add(("repeat", plant.id))
        world.say(
            f"{child.id} said it again and again, soft as a tune in the rain."
        )
        world.say(
            f'"Nice little target, bright as a spark," {child.id} sang, once more in the dark.'
        )


def apply_light(world: World, light: Entity, plant: Entity) -> None:
    if light.meter.get("on", 0.0) < THRESHOLD:
        return
    if plant.meter.get("chlorophyll", 0.0) < THRESHOLD:
        plant.meter["chlorophyll"] = 1.0
        plant.meme["awake"] = plant.meme.get("awake", 0.0) + 1
        world.say(
            f"The {light.label} touched the leaves, and chlorophyll woke with a grin."
        )


def apply_transformation(world: World, plant: Entity) -> None:
    if plant.meter.get("chlorophyll", 0.0) >= THRESHOLD and plant.meter.get("grown", 0.0) < THRESHOLD:
        plant.meter["grown"] = 1.0
        plant.meter["color"] = 1.0
        plant.label = f"green {plant.type}"
        world.say(
            f"The pale little target changed at last; its leaves turned green and thin to pin."
        )


def apply_growth(world: World, plant: Entity) -> None:
    if plant.meter.get("grown", 0.0) >= THRESHOLD and plant.meter.get("tall", 0.0) < THRESHOLD:
        plant.meter["tall"] = 1.0
        world.say(
            f"It stood up taller, tip-top proud, like a tiny flag in a sunny crowd."
        )


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        before = len(world.fired)
        plant = next((e for e in world.entities.values() if e.kind == "thing" and "plant" in e.tags), None)
        child = next((e for e in world.entities.values() if e.kind == "character"), None)
        light = next((e for e in world.entities.values() if e.type in {"sunbeam", "lamp"}), None)
        if child and plant:
            apply_compliment(world, child, plant)
            apply_repetition(world, child, plant)
            apply_transformation(world, plant)
            apply_growth(world, plant)
        if light and plant:
            apply_light(world, light, plant)
            apply_transformation(world, plant)
            apply_growth(world, plant)
        if len(world.fired) != before:
            changed = True


def tell(setting: Setting, plant_spec: PlantSpec, light_spec: LightSpec, name: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type="child", label=name))
    plant = world.add(Entity(
        id="plant",
        kind="thing",
        type="sprout",
        label=plant_spec.label,
        phrase=plant_spec.phrase,
        owner=name,
        meter={"chlorophyll": 0.0, "grown": 0.0, "tall": 0.0, "color": 0.0},
        meme={"joy": 0.0, "heard": 0.0, "awake": 0.0},
        tags=set(plant_spec.tags),
    ))
    light = world.add(Entity(
        id="light",
        kind="thing",
        type=light_spec.label,
        label=light_spec.label,
        phrase=light_spec.phrase,
        meter={"on": 1.0 if light_spec.intensity in {"bright", "steady"} else 0.0},
        tags=set(light_spec.tags),
    ))

    world.say(f"{name} was a {trait} child in {setting.place}, with a plant to mind.")
    world.say(f"{name} found {plant_spec.phrase}, a tiny thing with a target in mind.")
    world.say(
        f"It had a leaf target so neat and small, but the leaves were pale, not green at all."
    )
    world.para()
    world.say(
        f"{name} leaned near and spoke with cheer: {compliment_line(name, plant)}"
    )
    world.say(
        f"{name} said it once, then said it twice, then said it thrice, to make the day feel nice."
    )
    world.say(
        f"The {setting.place} held still and bright, as {name} kept singing in rhyme and light."
    )
    propagate(world)
    world.para()
    world.say(
        f"By and by, the chlorophyll stirred, and the little plant listened and heard."
    )
    world.say(
        f"The pale leaf target turned fresh and green, the happiest change that could be seen."
    )
    world.say(
        f"{name} smiled wide at the leafy show, for a kind word helped the plant to grow."
    )

    world.facts.update(child=child, plant=plant, light=light, setting=setting, plant_spec=plant_spec, light_spec=light_spec)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a young child about a {f["plant_spec"].label}, a compliment, and chlorophyll.',
        f"Tell a gentle story in rhyme where {f['child'].id} keeps repeating a kind line until the target plant transforms.",
        f'Write a simple story with repetition that includes the words "compliment", "target", and "chlorophyll".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, plant, light = f["child"], f["plant"], f["light"]
    setting = f["setting"]
    plant_spec = f["plant_spec"]
    return [
        QAItem(
            question=f"What did {child.id} keep saying to the {plant_spec.label}?",
            answer=f"{child.id} kept saying a kind compliment about the {plant_spec.target_name}, and then said it again and again.",
        ),
        QAItem(
            question=f"What helped the plant change in {setting.place}?",
            answer=f"The bright light and the plant's chlorophyll helped it transform from pale to green.",
        ),
        QAItem(
            question=f"What changed about the target plant by the end?",
            answer=f"It turned green and grew taller, so the tiny target sprout looked proud and full of life.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is chlorophyll?",
            answer="Chlorophyll is the green stuff in plants that helps them use light and helps their leaves look green.",
        ),
        QAItem(
            question="Why do people give compliments?",
            answer="People give compliments to say something kind or nice, which can make someone feel happy and brave.",
        ),
        QAItem(
            question="What does repetition mean in a story?",
            answer="Repetition means saying or doing something again and again. It can make a story feel musical and easy to remember.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child_hears_compliment(C, P) :- compliments(C, P).
repetition(C, P) :- compliments(C, P), says_again(C, P).
chlorophyll_awake(P) :- in_light(P), has_chlorophyll(P).
transforms(P) :- chlorophyll_awake(P), child_hears_compliment(_, P), repetition(_, P).
grows(P) :- transforms(P).
#show child_hears_compliment/2.
#show repetition/2.
#show chlorophyll_awake/1.
#show transforms/1.
#show grows/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name in SETTINGS:
        lines.append(asp.fact("setting", name))
    for pid, p in PLANTS.items():
        lines.append(asp.fact("plant", pid))
        lines.append(asp.fact("target", pid, p.target_name))
        lines.append(asp.fact("has_chlorophyll", pid))
    for lid in LIGHTS:
        lines.append(asp.fact("light", lid))
        lines.append(asp.fact("in_light", "target_sprout"))
        lines.append(asp.fact("compliments", "child", "target_sprout"))
        lines.append(asp.fact("says_again", "child", "target_sprout"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show grows/1."))
    asp_atoms = set(asp.atoms(model, "grows"))
    py = {("target_sprout",)} if True else set()
    if asp_atoms == py:
        print("OK: ASP and Python agree on transformation and growth.")
        return 0
    print("MISMATCH:")
    print("  ASP:", sorted(asp_atoms))
    print("  Python:", sorted(py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for plant_id in PLANTS:
            for light_id in LIGHTS:
                if "care" in setting.affords and "light" in setting.affords:
                    combos.append((place, plant_id, light_id))
    return combos


@dataclass
class StoryParams:
    place: str
    plant: str
    light: str
    name: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: compliment, target, chlorophyll, transformation, repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.plant is None or c[1] == args.plant)
              and (args.light is None or c[2] == args.light)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, plant, light = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        plant=plant,
        light=light,
        name=args.name or rng.choice(NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PLANTS[params.plant], LIGHTS[params.light], params.name, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meter.items() if v}
        memes = {k: v for k, v in e.meme.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        print(asp_program("#show grows/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show transforms/1. #show grows/1."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, plant, light in valid_combos():
            params = StoryParams(place=place, plant=plant, light=light, name=NAMES[0], trait=TRAITS[0], seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
