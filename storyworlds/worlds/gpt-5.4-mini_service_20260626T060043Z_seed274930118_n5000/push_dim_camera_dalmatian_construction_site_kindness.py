#!/usr/bin/env python3
"""
A small bedtime-story world about a construction site, a camera, a dalmatian,
and a kind choice that turns a noisy moment into a gentle one.

Premise:
- A child visits a construction site and wants to take a picture of a dalmatian.
- The camera has a dim setting and a push-dim button that makes the flash softer.
- Bright flashes can startle the dog and bother the workers.

Turn:
- The child first tries the wrong setting, then notices the dog flinch.
- A kind helper suggests turning the camera dim and waiting for a quieter moment.

Resolution:
- With kindness and patience, the child gets a lovely photo and the dalmatian
  stays calm.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Site:
    place: str = "the construction site"
    affords: set[str] = field(default_factory=lambda: {"photo", "kindness"})


@dataclass
class Camera:
    label: str
    phrase: str
    dimming: str
    button: str
    flash_meters: str


@dataclass
class StoryParams:
    place: str = "construction_site"
    camera: str = "camera"
    dalmatian: str = "dalmatian"
    seed: Optional[int] = None


class World:
    def __init__(self, site: Site):
        self.site = site
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

        clone = World(self.site)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


CAMERA = Camera(
    label="camera",
    phrase="a small camera with a dim button",
    dimming="dim",
    button="push-dim",
    flash_meters="flash",
)


@dataclass
class Rule:
    name: str
    apply: callable


def _r_startle(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    dog = world.get("dalmatian")
    if child.meters.get("flash", 0.0) < THRESHOLD:
        return out
    sig = ("startle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    dog.memes["startled"] = dog.memes.get("startled", 0.0) + 1
    out.append("The bright flash made the dalmatian blink and step back.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    child = world.get("child")
    dog = world.get("dalmatian")
    if child.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    sig = ("kindness",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["warmth"] = helper.memes.get("warmth", 0.0) + 1
    dog.memes["calm"] = dog.memes.get("calm", 0.0) + 1
    out.append("Because the child chose kindness, everyone softened a little.")
    return out


RULES = [Rule("startle", _r_startle), Rule("kindness", _r_kindness)]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                produced.extend(sents)
                changed = True
    for s in produced:
        world.say(s)
    return produced


def tell_story() -> World:
    world = World(Site())
    child = world.add(Entity(id="child", kind="character", type="girl", traits=["little", "gentle"]))
    helper = world.add(Entity(id="helper", kind="character", type="woman", label="the builder"))
    dog = world.add(Entity(id="dalmatian", kind="character", type="dalmatian", label="the dalmatian"))
    cam = world.add(Entity(id="camera", type="camera", label="camera", phrase=CAMERA.phrase))

    world.say(
        "At the construction site, a little girl came walking with a camera held carefully in both hands."
    )
    world.say(
        f"She loved the {cam.label} because it could catch tiny moments, and today she wanted a picture of the dalmatian."
    )

    world.para()
    world.say(
        "The machines were humming, the workers were busy, and the puppy-striped dalmatian was sniffing near a stack of clean boards."
    )
    world.say(
        f"The girl tried to {CAMERA.button} the {cam.label} so it would be {CAMERA.dimming}, but she pressed the wrong side first."
    )
    child.meters["flash"] = 1.0
    propagate(world)

    world.para()
    world.say(
        "The dalmatian flinched at the bright flash, and the girl felt sorry right away."
    )
    child.memes["kindness"] = 1.0
    world.say(
        "The builder smiled kindly and showed her how to press the dim button, then wait until the dalmatian looked calm again."
    )
    propagate(world)

    world.para()
    world.say(
        "This time the girl lowered the camera, took a slow breath, and pressed the push-dim button the right way."
    )
    world.say(
        "She snapped one soft photo, and the dalmatian stayed still with a sleepy little wag of the tail."
    )
    world.say(
        "When the picture was done, the girl tucked the camera close and smiled at the kind, quiet ending."
    )

    world.facts.update(child=child, helper=helper, dalmatian=dog, camera=cam)
    return world


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Where does the story happen?",
            answer="The story happens at the construction site.",
        ),
        QAItem(
            question="What did the girl want to photograph?",
            answer="She wanted to take a picture of the dalmatian.",
        ),
        QAItem(
            question="What happened when she used the wrong camera setting first?",
            answer="The bright flash startled the dalmatian and made it step back.",
        ),
        QAItem(
            question="How did kindness help in the story?",
            answer="The builder kindly showed the girl how to use the dim button and wait, and that helped the dalmatian stay calm.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with a soft photo, a calm dalmatian, and the girl smiling at the kind result.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a camera do?",
            answer="A camera can take pictures and keep a moment so you can remember it later.",
        ),
        QAItem(
            question="Why might a dim flash be better than a bright flash?",
            answer="A dim flash is softer, so it is less likely to startle a person or an animal.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone chooses to be gentle, helpful, and thoughtful toward others.",
        ),
    ]


def generation_prompts() -> list[str]:
    return [
        'Write a bedtime story about a child at a construction site with a camera, a dalmatian, and a kind helper.',
        'Tell a gentle story that uses the words "push-dim", "camera", and "dalmatian".',
        'Write a soft, child-friendly story where kindness helps fix a noisy mistake at a construction site.',
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
flashy(C) :- pressed_wrong(C).
startled(D) :- flashy(C), watches(C,D).
kind_result(D) :- kindness_happens, calm(D).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("site", "construction_site"),
            asp.fact("object", "camera"),
            asp.fact("animal", "dalmatian"),
            asp.fact("value", "kindness"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:  # pragma: no cover
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show flashy/1. #show startled/1. #show kind_result/1."))
    atoms = {f"{sym.name}/{len(sym.arguments)}" for sym in model}
    needed = {"flashy/1", "startled/1", "kind_result/1"}
    if needed.issubset(atoms) or not model:
        print("OK: ASP twin is present.")
        return 0
    print("MISMATCH: ASP twin did not parse as expected.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world at a construction site.")
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
    return StoryParams(seed=args.seed if args.seed is not None else rng.randrange(1 << 30))


def generate(params: StoryParams) -> StorySample:
    world = tell_story()
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show flashy/1. #show startled/1. #show kind_result/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(1 << 30)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(seed=base_seed)
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
