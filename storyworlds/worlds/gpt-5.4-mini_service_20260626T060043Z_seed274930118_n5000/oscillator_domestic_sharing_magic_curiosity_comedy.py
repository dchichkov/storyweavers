#!/usr/bin/env python3
"""
A small comedic domestic storyworld about sharing a curious magical oscillator.

The seed premise:
- In a cozy home, a child discovers a magical oscillator that hums, bounces, and
  makes funny little surprises.
- The child wants to keep it, but sharing becomes the real challenge.
- Curiosity causes mischief; magic makes it lively; a domestic routine turns it
  into a shared delight.

This script follows the Storyweavers contract with:
- a simulated world model (meters + memes),
- a reasonableness gate,
- an inline ASP twin,
- story-grounded Q&A,
- and a trace mode for inspecting state.
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    used_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

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
    place: str = "the apartment kitchen"
    domestic: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    noise: str
    magic: str
    turn_effect: str
    shares_well: bool = True


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    charge: float = 0.0
    sparkle: float = 0.0

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
        import copy
        return World(
            setting=self.setting,
            entities=copy.deepcopy(self.entities),
            facts=dict(self.facts),
            paragraphs=[[]],
            fired=set(self.fired),
            charge=self.charge,
            sparkle=self.sparkle,
        )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the apartment kitchen", domestic=True, affords={"oscillator"}),
    "living_room": Setting(place="the living room", domestic=True, affords={"oscillator"}),
    "laundry_room": Setting(place="the laundry room", domestic=True, affords={"oscillator"}),
}

DEVICES = {
    "oscillator": Device(
        id="oscillator",
        label="magic oscillator",
        phrase="a small brass magic oscillator with a wobbling knob",
        noise="bzzzt-bloop",
        magic="made tiny sparkles hop in circles",
        turn_effect="it hummed, bounced, and rang like a giggling spoon",
        shares_well=True,
    )
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ella", "Ava", "Ivy"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Owen", "Ben"]
PARENT_NAMES = ["mom", "dad"]
TRAITS = ["curious", "cheerful", "silly", "impish", "bright"]


@dataclass
class StoryParams:
    place: str
    device: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for dev in DEVICES:
            if dev in setting.affords:
                combos.append((place, dev))
    return combos


def explain_rejection(device: Device) -> str:
    return f"(No story: this world only has a domestic magic oscillator, so {device.label} is not a valid match.)"


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def setting_detail(setting: Setting) -> str:
    if setting.place == "the apartment kitchen":
        return "The table was sticky with juice, and the fridge hummed softly in the corner."
    if setting.place == "the living room":
        return "The couch made a soft hill of cushions, and a toy basket waited by the rug."
    return "The room smelled like warm soap, and the hamper stood beside the dryer."


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {next((t for t in hero.memes.get('traits', []) if t != 'little'), 'curious')} {hero.type} who noticed every odd sound in the house.")


def discover(world: World, hero: Entity, device: Device) -> None:
    hero.memes["curiosity"] += 1
    world.facts["device_label"] = device.label
    world.say(
        f"One afternoon, {hero.id} found {device.phrase} on a low shelf."
    )
    world.say(
        f"{device.noise.capitalize()}! {device.turn_effect.capitalize()}, and {device.magic}."
    )


def want_keep(world: World, hero: Entity, device: Device) -> None:
    hero.memes["want"] += 1
    world.say(
        f"{hero.id} wanted to keep the {device.label} all to {hero.pronoun('object')}self."
    )


def predict_share(world: World, device: Device) -> dict:
    sim = world.copy()
    sim.charge += 1
    sim.sparkle += 1
    child = next(e for e in sim.entities.values() if e.kind == "character")
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    child.memes["greedy"] = child.memes.get("greedy", 0) + 1
    if device.shares_well:
        return {"messy": False, "boring": False}
    return {"messy": True, "boring": False}


def warn(world: World, parent: Entity, hero: Entity, device: Device) -> bool:
    pred = predict_share(world, device)
    if not pred["messy"]:
        world.say(
            f'"Let\'s share it carefully," {parent.pronoun("possessive")} {parent.type} said, "so nobody ends up with sparkles in their cereal."'
        )
        return True
    return False


def cling(world: World, hero: Entity, device: Device) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0) + 1
    world.say(
        f"{hero.id} clutched the {device.label} and tried to hide it behind {hero.pronoun('possessive')} back."
    )


def share_turn(world: World, parent: Entity, hero: Entity, device: Device) -> None:
    hero.memes["sharing"] = hero.memes.get("sharing", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.charge += 1
    world.sparkle += 1
    world.say(
        f"{parent.id} pointed to the clock and said, \"You get one turn, then I get one turn, and then we can both watch.\""
    )
    world.say(
        f"{hero.id} gave a grin, passed the {device.label} over, and listened as it went {device.noise} again."
    )


def resolution(world: World, hero: Entity, parent: Entity, device: Device) -> None:
    world.say(
        f"Together they watched the little brass machine wobble on the table, and the sparkles landed harmlessly in the sugar bowl."
    )
    world.say(
        f"{hero.id} laughed so hard {hero.pronoun('subject')} nearly dropped a spoon, and {parent.pronoun('possessive')} {parent.type} laughed too."
    )


def tell(setting: Setting, device: Device, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting=setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        memes={"traits": ["little", trait], "curiosity": 0.0, "want": 0.0, "sharing": 0.0, "joy": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label=f"the {parent_type}",
        memes={"patience": 0.0},
    ))
    oscillator = world.add(Entity(
        id=device.id,
        type="device",
        label=device.label,
        phrase=device.phrase,
        owner=hero.id,
        caretaker=parent.id,
    ))
    world.facts.update(hero=hero, parent=parent, device=oscillator, device_cfg=device)

    introduce(world, hero)
    discover(world, hero, device)
    world.para()
    world.say(setting_detail(setting))
    world.say(f"The {device.label} sat on the counter like it was waiting for a joke.")
    want_keep(world, hero, device)
    warn(world, parent, hero, device)
    cling(world, hero, device)
    world.para()
    share_turn(world, parent, hero, device)
    resolution(world, hero, parent, device)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    device = f["device_cfg"]
    return [
        f'Write a short comedic story for a young child about sharing a {device.label} in a home.',
        f"Tell a funny domestic story where {hero.id} gets curious about {device.phrase} and learns to share it.",
        f'Write a child-friendly story that includes a magical oscillator, curiosity, and a happy sharing ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    device = f["device"]
    device_cfg = f["device_cfg"]
    place = world.setting.place

    return [
        QAItem(
            question=f"What did {hero.id} find in {place}?",
            answer=f"{hero.id} found {device_cfg.phrase} there, and it was a magic oscillator.",
        ),
        QAItem(
            question=f"Why did {hero.id} want to keep the {device.label}?",
            answer=f"{hero.id} was curious and wanted to keep the {device.label} all to {hero.pronoun('object')}self at first.",
        ),
        QAItem(
            question=f"How did {parent.id} help the two of them use the {device.label}?",
            answer=f"{parent.id} suggested taking turns, so {hero.id} and {parent.pronoun('subject')} could share it without arguing.",
        ),
        QAItem(
            question=f"What funny thing happened when they watched the {device.label} together?",
            answer=f"The little machine went {device_cfg.noise}, sparkles landed in the sugar bowl, and everybody laughed.",
        ),
    ]


KNOWLEDGE = {
    "oscillator": [
        (
            "What is an oscillator?",
            "An oscillator is something that moves or repeats back and forth in a pattern, like a swing or a humming machine.",
        ),
    ],
    "magic": [
        (
            "What does magic mean in a story?",
            "Magic in a story means something surprising and impossible happens, like sparkles appearing or toys moving in funny ways.",
        ),
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes you want to look, ask questions, and learn how something works.",
        ),
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting other people use or enjoy something too, instead of keeping it only for yourself.",
        ),
    ],
    "domestic": [
        (
            "What does domestic mean?",
            "Domestic means something about home, like the kitchen, the couch, laundry, or other everyday family places.",
        ),
    ],
    "comedy": [
        (
            "Why are funny stories nice?",
            "Funny stories are nice because they make people laugh, and laughter can make a small problem feel lighter.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for items in KNOWLEDGE.values() for q, a in items]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid_story(P, D) :- place(P), device(D), affords(P, D).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.domestic:
            lines.append(asp.fact("domestic", pid))
        for d in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, d))
    for did, device in DEVICES.items():
        lines.append(asp.fact("device", did))
        lines.append(asp.fact("magic", did))
        lines.append(asp.fact("oscillator", did))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedic domestic storyworld about sharing a magical oscillator.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_NAMES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.device is None or c[1] == args.device)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, device = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, device=device, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], DEVICES[params.device], params.name, params.gender, params.parent, params.trait)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and k != "traits"}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  charge={world.charge}")
    lines.append(f"  sparkle={world.sparkle}")
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
    StoryParams(place="kitchen", device="oscillator", name="Mia", gender="girl", parent="mom", trait="curious"),
    StoryParams(place="living_room", device="oscillator", name="Leo", gender="boy", parent="dad", trait="silly"),
    StoryParams(place="laundry_room", device="oscillator", name="Nora", gender="girl", parent="mom", trait="bright"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for p, d in combos:
            print(f"  {p:14} {d}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.device} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
