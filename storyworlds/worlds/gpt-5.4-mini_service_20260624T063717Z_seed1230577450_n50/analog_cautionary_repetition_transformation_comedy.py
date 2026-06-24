#!/usr/bin/env python3
"""
storyworlds/worlds/analog_cautionary_repetition_transformation_comedy.py
========================================================================

A small storyworld about an analog machine, a cautionary warning, a repeated
mistake, and a comic transformation.

Seed-image tale:
---
A child keeps winding an old analog music box too hard. A parent warns that
cranking it again will snap the spring. The child tries three times anyway,
each try making a funny clank-clank cough. At last they stop, loosen the knob,
and the music box turns into a gentle little tune.

Story instruments:
- Cautionary: a warning about over-winding.
- Repetition: the child repeats the risky action a few times.
- Transformation: the analog thing changes from jammed to smooth.
- Comedy: the machine's silly noises and the parent's deadpan help.
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
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"child", "kid", "girl", "boy"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = True


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    kind: str
    risk: str
    safe_action: str
    comic_noise: str
    transform_from: str
    transform_to: str


@dataclass
class StoryParams:
    place: str
    device: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True),
    "workshop": Setting(place="the workshop", indoors=True),
    "living_room": Setting(place="the living room", indoors=True),
}

DEVICES = {
    "music_box": Device(
        id="music_box",
        label="music box",
        phrase="an old analog music box with a brass knob",
        kind="music box",
        risk="snap the spring",
        safe_action="wind it gently",
        comic_noise="clank-clank cough",
        transform_from="stiff and grumpy",
        transform_to="gentle and shiny",
    ),
    "clock": Device(
        id="clock",
        label="clock",
        phrase="a round analog clock with a sleepy bell",
        kind="clock",
        risk="bend the hands",
        safe_action="turn the knob slowly",
        comic_noise="tick-tick hiccup",
        transform_from="cross-eyed and stuck",
        transform_to="steady and cheerful",
    ),
    "toy_car": Device(
        id="toy_car",
        label="toy car",
        phrase="a little analog toy car with a hand crank",
        kind="toy car",
        risk="jam the gears",
        safe_action="spin the crank softly",
        comic_noise="vroom-uh-oh",
        transform_from="bumpy and rude",
        transform_to="smooth and speedy",
    ),
}

NAMES = ["Mina", "Theo", "Lina", "Noah", "Pia", "Owen", "Ivy", "Sam"]
TRAITS = ["curious", "silly", "careful", "brave", "bouncy"]


class World:
    def __init__(self, setting: Setting, device: Device) -> None:
        self.setting = setting
        self.device = device
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting, self.device)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for s in _rules(world):
            if s not in world.fired:
                world.fired.add(s)
                out.append(s)
                changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def _rules(world: World) -> list[str]:
    out: list[str] = []
    child = next(e for e in world.entities.values() if e.kind == "character")
    device = world.get("device")
    if child.memes.get("winding", 0) >= THRESHOLD and device.meters.get("strain", 0) >= THRESHOLD:
        out.append("device_nearly_breaks")
    if device.meters.get("strain", 0) >= 3 * THRESHOLD:
        out.append("device_stuck")
    if device.meters.get("repair", 0) >= THRESHOLD and device.meters.get("strain", 0) <= THRESHOLD:
        out.append("device_transform")
    return out


def present(world: World, hero: Entity, parent: Entity, device: Entity) -> None:
    world.say(
        f"{hero.id} found {device.phrase} on a shelf in {world.setting.place}."
    )
    world.say(
        f"{hero.id} loved the little analog clicks, and {hero.pronoun('possessive')} "
        f"{parent.label} said it was old but still useful."
    )


def caution(world: World, parent: Entity, hero: Entity, device: Entity) -> None:
    world.say(
        f'"If you crank it too hard, you might {world.device.risk}," '
        f'{parent.id} warned. "Just {world.device.safe_action}."'
    )


def repeat_mistake(world: World, hero: Entity, device: Entity) -> None:
    for i in range(3):
        hero.memes["winding"] = hero.memes.get("winding", 0) + 1
        device.meters["strain"] = device.meters.get("strain", 0) + 1
        world.say(f"{hero.id} tried again. The {device.label} answered with {world.device.comic_noise}.")
        if i < 2:
            world.say(f"{hero.id} squinted and said, 'Maybe that was the wrong kind of careful.'")
    propagate(world, narrate=True)


def transform(world: World, hero: Entity, parent: Entity, device: Entity) -> None:
    device.meters["repair"] = device.meters.get("repair", 0) + 1
    device.meters["strain"] = max(0, device.meters.get("strain", 0) - 2)
    world.say(
        f"At last {parent.id} showed {hero.id} how to loosen the knob and start over."
    )
    world.say(
        f"The {device.label} changed from {world.device.transform_from} to {world.device.transform_to}, "
        f"and its music came out soft and sweet."
    )
    propagate(world, narrate=True)


def tell(setting: Setting, device: Device, name: str, parent_kind: str, trait: str) -> World:
    world = World(setting, device)
    hero = world.add(Entity(id=name, kind="character", type="child", traits=[trait, "stubborn"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_kind, label=f"their {parent_kind}"))
    thing = world.add(Entity(id="device", type=device.kind, label=device.label, phrase=device.phrase))
    world.facts.update(hero=hero, parent=parent, device=thing)
    present(world, hero, parent, thing)
    world.para()
    caution(world, parent, hero, thing)
    repeat_mistake(world, hero, thing)
    world.para()
    transform(world, hero, parent, thing)
    world.say(
        f"{hero.id} laughed, because the {device.label} sounded silly before it sounded pretty."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedy for a small child about an analog {f["device"].label} that needs gentle handling.',
        f"Tell a cautionary story where {f['hero'].id} is warned not to wind the {f['device'].label} too hard.",
        f"Write a story with repetition and a happy transformation in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    device = f["device"]
    return [
        QAItem(
            question=f"What did {hero.id} keep doing to the {device.label}?",
            answer=f"{hero.id} kept winding the {device.label} too hard, even after being warned to be gentle.",
        ),
        QAItem(
            question=f"Why did {hero.id}'s parent warn them about the {device.label}?",
            answer=f"The warning was because cranking it too hard could {world.device.risk}, so it needed a gentle touch.",
        ),
        QAItem(
            question=f"How did the {device.label} change at the end?",
            answer=f"It changed from {world.device.transform_from} to {world.device.transform_to}, and then it played a soft tune.",
        ),
        QAItem(
            question=f"What funny sound did the {device.label} make when {hero.id} tried again?",
            answer=f"It made a {world.device.comic_noise} sound, which fit the comic mood of the story.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does analog mean?",
            answer="Analog means something uses continuous moving parts, like hands, knobs, gears, or springs, instead of only numbers on a screen.",
        ),
        QAItem(
            question="Why can a spring-powered machine stop working?",
            answer="A spring-powered machine can stop working if the spring gets too tight, bent, or worn out.",
        ),
        QAItem(
            question="What is a knob used for?",
            answer="A knob is a little part you turn with your fingers to change how something works.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
made_warning(P) :- parent(P), risk(R), can_hurt(R).
repeated_attempt(C) :- child(C), attempt(C,1), attempt(C,2), attempt(C,3).
transformed(D) :- device(D), repaired(D), less_strain(D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did in DEVICES:
        lines.append(asp.fact("device", did))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show made_warning/1. #show repeated_attempt/1. #show transformed/1.")
    model = asp.one_model(program)
    atoms = set((sym.name, len(sym.arguments)) for sym in model)
    expected = {("made_warning", 1), ("repeated_attempt", 1), ("transformed", 1)}
    if atoms == expected:
        print("OK: ASP twin is present.")
        return 0
    print("Mismatch in ASP twin.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy storyworld about analog things, caution, repetition, and change.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--parent", choices=["mother", "father", "grandparent"])
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
    place = args.place or rng.choice(list(SETTINGS))
    device = args.device or rng.choice(list(DEVICES))
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father", "grandparent"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, device=device, name=name, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], DEVICES[params.device], params.name, params.parent, params.trait)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show made_warning/1. #show repeated_attempt/1. #show transformed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show transformed/1."))
        print(model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            for device in DEVICES:
                params = StoryParams(place=place, device=device, name="Mina", parent="mother", trait="curious")
                samples.append(generate(params))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
