#!/usr/bin/env python3
"""
storyworlds/worlds/digital_happy_ending_rhyming_story.py
=========================================================

A tiny storyworld about a child, a digital delight, and a happy ending that
arrives with a gentle rhyme.

Seed impression:
---
A little child loves a glowing digital book and asks for "just one more" rhyme.
The battery dips low, the parent worries the story will go dark, and a charger
becomes the calm fix. The child waits, the device wakes, and the bedtime ends
bright and sweet.

The world model tracks:
- physical meters: battery, charged, screen_light, clean, plugged
- emotional memes: joy, worry, patience, love, relief

The narration is intentionally child-facing and lightly rhyming, with a clear
beginning, middle turn, and happy ending.
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

    def __post_init__(self) -> None:
        for k in ("battery", "charged", "screen_light", "clean", "plugged"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "patience", "love", "relief"):
            self.memes.setdefault(k, 0.0)

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
    place: str = "the bedroom"
    indoors: bool = True


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    low_battery: float = 1.0
    charge_gain: float = 2.0


@dataclass
class Charger:
    id: str
    label: str
    phrase: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_low_battery(world: World) -> list[str]:
    out = []
    child = world.get("child")
    device = world.get("device")
    if device.meters["battery"] > 0.0:
        return out
    sig = ("low",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    out.append(f"The glow went dim, a hush in the room, and the little screen felt like evening gloom.")
    return out


def _r_charge(world: World) -> list[str]:
    out = []
    device = world.get("device")
    charger = world.get("charger")
    if device.meters["plugged"] < THRESHOLD:
        return out
    sig = ("charge",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    device.meters["battery"] = min(3.0, device.meters["battery"] + 2.0)
    device.meters["charged"] = 1.0
    charger.meters["clean"] += 0.0
    out.append(f"The charger gave juice with a snug little buzz, and the screen woke up sparkling just because.")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    child = world.get("child")
    device = world.get("device")
    if device.meters["charged"] < THRESHOLD:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["joy"] += 1
    child.memes["relief"] += 1
    child.memes["worry"] = 0.0
    out.append(f"The worry drifted away on a soft little breeze, and the child smiled with a happy seize.")
    return out


RULES = [_r_low_battery, _r_charge, _r_relief]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=hero_type, label=hero_name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    device = world.add(Entity(
        id="device",
        type="thing",
        label="tablet",
        phrase="a little digital tablet",
        owner=child.id,
        caretaker=parent.id,
    ))
    charger = world.add(Entity(
        id="charger",
        type="thing",
        label="charger",
        phrase="a tiny charger cord",
        owner=parent.id,
    ))
    world.facts.update(child=child, parent=parent, device=device, charger=charger)

    child.memes["love"] += 1
    child.memes["joy"] += 1
    device.meters["battery"] = 1.0
    world.say(f"{hero_name} was a bright little {hero_type} who loved a digital light, so shiny and bright.")
    world.say(f"{hero_name} liked a story that sang through the screen, with rhymes like a dream in the moonlight sheen.")
    world.say(f"At {setting.place}, {hero_name} held {device.phrase} close and grinned with delight, then tapped for a tale that felt just right.")

    world.para()
    child.memes["worry"] += 1
    world.say(f"But the battery winked and grew very small, and the glow went soft in the middle of all.")
    world.say(f"'{hero_name},' said {parent_type} {parent.label}, 'if it goes dark, the song cannot stay; let's save a bit of power for later today.'")
    world.say(f"{hero_name} pouted a moment, then paused in the hush, because waiting awhile can be kinder than rush.")
    world.para()

    child.memes["patience"] += 1
    device.meters["plugged"] = 1.0
    world.say(f"So {hero_name} plugged in the charger with a tiny click-clack, and the room kept its sparkle while the juice came back.")
    propagate(world, narrate=True)
    world.say(f"Then the tablet glowed brighter, the story rang true, and the last little rhyme sparkled all the way through.")
    world.say(f"{hero_name} cuddled up smiling, all cozy and warm, with a happy ending snug as a charm.")
    return world


SETTINGS = {
    "bedroom": Setting(place="the bedroom", indoors=True),
    "reading_nook": Setting(place="the reading nook", indoors=True),
    "couch": Setting(place="the couch", indoors=True),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Leo", "Ben", "Noah", "Finn", "Max"]
TRAITS = ["curious", "cheerful", "gentle", "playful", "brave"]


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


ASP_RULES = r"""
place(bedroom). place(reading_nook). place(couch).
character(girl). character(boy).
parent(mother). parent(father).
device(tablet).
charger(charger).

compatible(Place,Device,Charger) :- place(Place), device(Device), charger(Charger).
#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    lines.append(asp.fact("device", "tablet"))
    lines.append(asp.fact("charger", "charger"))
    lines.append(asp.fact("character", "girl"))
    lines.append(asp.fact("character", "boy"))
    lines.append(asp.fact("parent", "mother"))
    lines.append(asp.fact("parent", "father"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Digital happy-ending rhyming story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(
        place=args.place or rng.choice(list(SETTINGS)),
        name=name,
        gender=gender,
        parent=args.parent or rng.choice(["mother", "father"]),
        trait=args.trait or rng.choice(TRAITS),
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    device = f["device"]
    return [
        QAItem(
            question=f"What did {child.label} love in the story?",
            answer=f"{child.label} loved a digital tablet that could glow with a story and sing out rhymes.",
        ),
        QAItem(
            question=f"Why did the {parent.type} ask them to save power?",
            answer=f"The {parent.type} worried the tablet's battery would run low and the story would go dark.",
        ),
        QAItem(
            question=f"What fixed the problem in the end?",
            answer=f"They plugged in the charger, the tablet woke up again, and the happy ending could keep shining.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a battery for in a digital device?",
            answer="A battery stores energy so a digital device can glow, play, or show a story without staying plugged in all the time.",
        ),
        QAItem(
            question="What does a charger do?",
            answer="A charger sends energy into a device so its battery can fill back up again.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    return [
        "Write a short rhyming story about a child and a digital device with a happy ending.",
        f"Tell a gentle bedtime tale where {child.label} loves a digital story but the battery gets low and {parent.label} helps.",
        "Make the story sound musical and simple, with a calm problem and a bright ending.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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
        print(format_qa(sample))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for gender in ("girl", "boy"):
            for device in ("tablet",):
                combos.append((place, gender, device))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(f"{asp_facts()}\n{ASP_RULES}\n#show compatible/3.\n")
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = {tuple(x) for x in valid_combos()}
    cl = {tuple(x) for x in asp_valid_combos()}
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="bedroom", name="Mia", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="reading_nook", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="couch", name="Nora", gender="girl", parent="mother", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(f"{asp_facts()}\n{ASP_RULES}\n#show compatible/3.\n")
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
