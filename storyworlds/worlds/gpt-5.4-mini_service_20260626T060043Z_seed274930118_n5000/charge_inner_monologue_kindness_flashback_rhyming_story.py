#!/usr/bin/env python3
"""
storyworlds/worlds/charge_inner_monologue_kindness_flashback_rhyming_story.py
===============================================================================

A compact storyworld about a child, a low charge, a kind choice, and a flashback
that nudges the turn toward sharing.

Premise:
- A child wants to use a glowing gadget.
- The gadget is nearly out of charge.
- Another little device is also low.
- The child remembers a kinder moment from before, then shares the charger.

Style:
- Rhyming-story cadence with short, child-facing lines.
- Inner monologue is written as a thought.
- Flashback appears as a remembered earlier scene.
- Kindness changes the world state and closes the story with a bright image.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    chargeable: bool = False
    charged: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    afford_charge: bool
    mood: str


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    charge_gain: float = 1.0


@dataclass
class StoryParams:
    setting: str
    device: str
    helper_device: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_low_charge(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.chargeable and e.meters.get("charge", 0.0) < THRESHOLD:
            sig = ("low", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["worry"] = e.memes.get("worry", 0.0) + 1.0
            out.append(f"{e.label_word.capitalize()} looked dim and small.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    helper = world.facts.get("helper_device")
    if not hero or not helper:
        return out
    if hero.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    sig = ("kindness", hero.id, helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.meters["charge"] = helper.meters.get("charge", 0.0) + 1.0
    out.append(f"That kind choice made room for a better glow.")
    return out


CAUSAL_RULES = [Rule("low_charge", _r_low_charge), Rule("kindness", _r_kindness)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTINGS = {
    "bedroom": Setting(place="the bedroom", afford_charge=True, mood="soft"),
    "campsite": Setting(place="the campsite", afford_charge=True, mood="sparkly"),
    "kitchen": Setting(place="the kitchen", afford_charge=True, mood="warm"),
}

DEVICES = {
    "lantern": Device(id="lantern", label="little lantern", phrase="a little lantern with a round glass face", charge_gain=1.2),
    "tablet": Device(id="tablet", label="tiny tablet", phrase="a tiny tablet with a bright screen", charge_gain=1.0),
    "radio": Device(id="radio", label="pocket radio", phrase="a pocket radio with a red button", charge_gain=1.1),
    "toycar": Device(id="toycar", label="toy car", phrase="a toy car that hummed and zoomed", charge_gain=0.9),
}

HELPERS = {
    "flashlight": Device(id="flashlight", label="flashlight", phrase="a small flashlight with a sleepy battery", charge_gain=1.0),
    "musicbox": Device(id="musicbox", label="music box", phrase="a music box that could still sing softly", charge_gain=1.0),
}

GIRL_NAMES = ["Mia", "Luna", "Ivy", "Zoe", "Nora", "Ada"]
BOY_NAMES = ["Leo", "Finn", "Milo", "Theo", "Ben", "Owen"]
TRAITS = ["gentle", "brave", "curious", "cheery", "patient", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for d in DEVICES:
            for h in HELPERS:
                combos.append((s, d, h))
    return combos


def explain_rejection(device: str, helper: str) -> str:
    return f"(No story: the {DEVICES[device].label} and {HELPERS[helper].label} do not make a convincing charge-sharing problem here.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a child, charge, kindness, and a flashback.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--helper-device", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.device is None or c[1] == args.device)
              and (args.helper_device is None or c[2] == args.helper_device)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, device, helper_device = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, device=device, helper_device=helper_device,
                       name=name, gender=gender, parent=parent, trait=trait)


def tell(setting: Setting, device: Device, helper: Device, hero_name: str, hero_gender: str,
         parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, memes={"kindness": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    prize = world.add(Entity(id=device.id, type=device.id, label=device.label, phrase=device.phrase,
                             owner=hero.id, caretaker=parent.id, chargeable=True, charged=False,
                             meters={"charge": 0.35}, memes={"worry": 0.0}))
    side = world.add(Entity(id=helper.id, type=helper.id, label=helper.label, phrase=helper.phrase,
                            owner=hero.id, caretaker=parent.id, chargeable=True, charged=False,
                            meters={"charge": 0.25}, memes={"worry": 0.0}))

    world.say(f"{hero.id} was a {trait} little {hero_gender} who liked a soft little rhyme.")
    world.say(f"{hero.id} had {prize.phrase}, and {prize.label_word} was low on charge, oh my.")
    world.say(f'“I want my {prize.label_word} to shine,” {hero.pronoun("subject")} thought with a sigh, '
              f'“so I can go play before the day goes by.”')

    world.para()
    world.say(f"On a cozy day in {setting.place}, the lights were warm and the air was spry.")
    world.say(f"{hero.id} reached for the charger, but then saw {side.phrase}, so dim nearby.")
    world.say(f"“I could charge mine first,” {hero.pronoun('subject')} thought, “but that would not be kind.”")
    world.say(f"Then a flashback fluttered back in {hero.id}'s mind.")

    world.para()
    world.say(f"{hero.id} remembered a rainy time, clear as pie.")
    world.say(f"Once, {hero.id} had been gloomy and blue, with a toy that would not even try.")
    world.say(f"Back then, a friend had shared a charger and smiled right by.")
    world.say(f"That kindness had helped {hero.id} feel brave, and the memory made {hero.id} nod and try.")

    world.para()
    hero.memes["kindness"] += 1.0
    world.say(f"“First you,” {hero.id} said, and gave the charger to {side.label_word}, neat and nigh.")
    propagate(world)
    side.meters["charge"] = 1.0
    world.say(f"{side.label_word.capitalize()} brightened up, and the little room felt light.")
    world.say(f"Then {side.label_word} shared the charger back, because sharing made the moment right.")
    prize.meters["charge"] = 1.0
    prize.charged = True
    world.say(f"Soon {prize.label_word} glowed and hummed, as happy as a kite.")
    world.say(f"{hero.id} smiled and held it high: a little glow to end the night.")

    world.facts.update(hero=hero, parent=parent, device=prize, helper_device=side, setting=setting,
                       trait=trait, device_def=device, helper_def=helper)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    device = f["device_def"]
    helper = f["helper_def"]
    return [
        f'Write a short rhyming story for a young child about charge, kindness, and a remembered flashback.',
        f"Tell a gentle story where {hero.id} wants to charge {device.label} but first notices {helper.label} needs help too.",
        f'Write a simple story that includes a flashback and ends with a glowing device and a kind choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    device = f["device"]
    helper = f["helper_device"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {device.label_word}?",
            answer=f"{hero.id} wanted to charge the {device.label_word} so it could shine and chime.",
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=f"{hero.id} remembered a time when a friend shared a charger, and that kindness helped a lot.",
        ),
        QAItem(
            question=f"How did {hero.id} show kindness in the story?",
            answer=f"{hero.id} let {helper.label_word} charge first, and then the charger came back around so both could glow.",
        ),
        QAItem(
            question=f"What was the ending image?",
            answer=f"The {device.label_word} glowed bright in {world.setting.place}, and {hero.id} smiled at the warm light.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean for a battery to be charged?",
            answer="A charged battery has energy stored in it, so the device can light up, play, or work for a while.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means choosing to help, share, or be gentle so someone else feels cared for.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a moment when the story remembers something that happened before the present scene.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.chargeable:
            bits.append("chargeable=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
low_charge(E) :- chargeable(E), charge(E,C), C < 1.
kind_choice(H,H2) :- kindness(H), helper(H2).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for d in DEVICES:
        lines.append(asp.fact("device", d))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show low_charge/1."))
    _ = asp.atoms(model, "low_charge")
    print("OK: ASP twin loads and produces a model.")
    return 0


CURATED = [
    StoryParams(setting="bedroom", device="lantern", helper_device="flashlight", name="Mia", gender="girl", parent="mother", trait="gentle"),
    StoryParams(setting="kitchen", device="tablet", helper_device="musicbox", name="Leo", gender="boy", parent="father", trait="curious"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], DEVICES[params.device], HELPERS[params.helper_device],
                 params.name, params.gender, params.parent, params.trait)
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

    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
