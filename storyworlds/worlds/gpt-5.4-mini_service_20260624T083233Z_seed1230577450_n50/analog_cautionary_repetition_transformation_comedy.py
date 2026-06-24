#!/usr/bin/env python3
"""
Storyworld: analog cautionary repetition transformation comedy.

A small, self-contained story world about a child, an old analog machine, a
parent's caution, a funny repeated mistake, and a playful transformation that
turns the trouble into a harmless game.
"""

from __future__ import annotations

import argparse
import copy
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the attic"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    effect: str
    caution: str
    transform: str
    repeat: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        c.paragraphs = [[]]
        return c


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for ent in list(world.entities.values()):
            if ent.kind != "device":
                continue
            if ent.meters.get("repeat", 0.0) >= THRESHOLD and ent.meters.get("tangled", 0.0) < THRESHOLD:
                sig = ("tangle", ent.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    ent.meters["tangled"] = 1.0
                    out.append(f"The old machine hiccuped and made the same squeaky sound again.")
                    changed = True
            if ent.meters.get("tangled", 0.0) >= THRESHOLD and ent.meters.get("decorated", 0.0) >= THRESHOLD:
                sig = ("transform", ent.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    ent.memes["pride"] = 1.0
                    ent.meters["useful"] = 1.0
                    out.append(f"With the ribbons and labels on it, the machine became a cheerful message box.")
                    changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def can_transform(device: Device) -> bool:
    return bool(device.transform)


def build_setting() -> Setting:
    return Setting(place="the attic", indoors=True, affords={"listen", "repeat", "decorate"})


def build_device() -> Device:
    return Device(
        id="machine",
        label="analog cassette player",
        phrase="an old analog cassette player with a tiny speaker",
        effect="made a funny echo",
        caution="it could chew the tape if pushed too hard",
        transform="message box",
        repeat="play the same sample again",
        tags={"analog", "repeat", "transform", "caution"},
    )


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


NAMES = {
    "girl": ["Mina", "Lola", "Tia", "Nora", "Pia"],
    "boy": ["Finn", "Milo", "Ben", "Ollie", "Theo"],
}
PARENTS = ["mother", "father"]


def tell(params: StoryParams) -> World:
    world = World(build_setting())
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    device_def = build_device()
    device = world.add(Entity(
        id=device_def.id,
        kind="device",
        type="device",
        label=device_def.label,
        phrase=device_def.phrase,
        owner=hero.id,
    ))

    world.say(f"{hero.id} found {device.phrase} in {world.setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} loved the way {device.label} could make ordinary sounds seem silly.")

    world.para()
    world.say(f"{hero.id} wanted to use it right away and kept pressing the button to {device_def.repeat}.")
    device.meters["repeat"] = 1.0
    propagate(world)

    world.para()
    world.say(f"{parent.label_word if hasattr(parent, 'label_word') else 'the parent'} warned, \"Be careful; {device_def.caution}.\"")
    hero.memes["curiosity"] = 1.0
    hero.memes["caution_heard"] = 1.0
    world.say(f"But {hero.id} tried once more, just to hear the squeak one more time.")
    device.meters["repeat"] += 1.0
    propagate(world)

    world.para()
    world.say(f"Then {hero.id} had a bright idea: instead of fighting the old noise, {hero.pronoun('subject')} would turn it into a joke.")
    device.meters["decorated"] = 1.0
    world.say(f"{hero.id} added paper arrows, bright tape, and a hand-written label that said \"PLEASE LEAVE A FUNNY MESSAGE.\"")
    if can_transform(device_def):
        propagate(world)

    world.para()
    hero.memes["joy"] = 1.0
    hero.memes["pride"] = 1.0
    device.meters["useful"] = 1.0
    world.say(f"Now the analog player sat on the shelf like a little comedy booth, ready for family notes instead of tangled trouble.")
    world.say(f"{hero.id} laughed, {parent.label if parent.label else 'the parent'} laughed, and the old machine stayed safe because everyone remembered the warning.")

    world.facts.update(hero=hero, parent=parent, device=device, device_def=device_def)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    device = f["device_def"]
    return [
        f'Write a short comedy story for a child about an "{device.id}" that makes repeated sounds.',
        f"Tell a cautionary story where {hero.id} is warned not to push the analog button too much.",
        f"Write a funny story where repetition causes trouble, then a transformation makes the machine helpful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    device = f["device_def"]
    return [
        QAItem(
            question=f"What did {hero.id} find in the attic?",
            answer=f"{hero.id} found {device.phrase} in the attic.",
        ),
        QAItem(
            question=f"Why did {parent.label if parent.label else 'the parent'} warn {hero.id} to be careful?",
            answer=f"The parent warned {hero.id} because {device.caution}.",
        ),
        QAItem(
            question=f"How did the machine change by the end?",
            answer=f"It changed into a cheerful message box after {hero.id} decorated it.",
        ),
        QAItem(
            question=f"What made the story funny?",
            answer=f"The same squeaky sound kept happening again and again, which made the old machine feel silly instead of scary.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does analog mean?",
            answer="Analog usually means something that uses continuous, old-fashioned signals or moving parts instead of digital bits.",
        ),
        QAItem(
            question="Why can repeating a button press be a problem?",
            answer="Repeating the same action too many times can wear out a machine or make it jam.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is when something changes into a new form or becomes useful in a new way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story q&a ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world q&a ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "attic"),
        asp.fact("affords", "attic", "listen"),
        asp.fact("affords", "attic", "repeat"),
        asp.fact("affords", "attic", "decorate"),
        asp.fact("device", "machine"),
        asp.fact("analog", "machine"),
        asp.fact("cautionary", "machine"),
        asp.fact("repetition", "machine"),
        asp.fact("transformation", "machine"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
safe_to_story(S) :- setting(S).
interesting(D) :- device(D), analog(D), cautionary(D), repetition(D), transformation(D).
valid_story(S,D) :- safe_to_story(S), interesting(D).
#show valid_story/2.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    got = set(asp_valid())
    want = {("attic", "machine")}
    if got == want:
        print("OK: ASP parity matches python story gate.")
        return 0
    print(f"MISMATCH: {got} != {want}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: analog cautionary repetition transformation comedy.")
    ap.add_argument("--name", choices=NAMES["girl"] + NAMES["boy"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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
    if args.name and args.name not in NAMES[gender]:
        raise StoryError("Chosen name does not match the selected gender.")
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(name=name, gender=gender, parent=parent)


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for gender in ["girl", "boy"]:
            params = StoryParams(name=NAMES[gender][0], gender=gender, parent="mother")
            samples.append(generate(params))
    else:
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
