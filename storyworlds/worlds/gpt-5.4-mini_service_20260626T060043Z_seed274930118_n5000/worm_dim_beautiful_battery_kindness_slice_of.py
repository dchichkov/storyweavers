#!/usr/bin/env python3
"""
A small slice-of-life story world about a child, a beautiful battery toy, and a
kind choice that changes the afternoon.

The seed tale:
- A child loves a beautiful little light-up toy.
- The toy's battery gets weak at the wrong moment.
- A parent, sibling, or neighbor suggests a kind, practical fix.
- The child learns to share, wait, or help, and the day ends gently.

The world is deliberately small and constraint-checked:
- not every toy works with every battery
- a kind fix only exists when the situation is genuinely solvable
- the story is driven by simulated state, not a frozen template
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

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    battery_kind: str
    needs: str
    glow_word: str
    bedroom_scale: bool = True


@dataclass
class Battery:
    id: str
    label: str
    phrase: str
    kind: str
    charge: float
    beautiful: bool = False
    tiny: bool = False


@dataclass
class KindFix:
    id: str
    label: str
    prep: str
    tail: str
    restored_charge: float
    requires_help: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"repair", "share"}),
    "living_room": Setting(place="the living room", indoors=True, affords={"repair", "share"}),
    "porch": Setting(place="the porch", indoors=False, affords={"repair", "share"}),
}

TOYS = {
    "lantern": Toy(
        id="lantern",
        label="little lantern",
        phrase="a beautiful little lantern with a warm glass globe",
        battery_kind="aa",
        needs="bright",
        glow_word="glow",
    ),
    "bunny": Toy(
        id="bunny",
        label="music bunny",
        phrase="a beautiful music bunny with a soft button nose",
        battery_kind="aaa",
        needs="play",
        glow_word="chime",
    ),
    "robot": Toy(
        id="robot",
        label="robot buddy",
        phrase="a beautiful robot buddy with shiny blue eyes",
        battery_kind="aa",
        needs="bright",
        glow_word="blink",
    ),
}

BATTERIES = {
    "aa": Battery(
        id="aa",
        label="AA battery",
        phrase="a fresh AA battery",
        kind="aa",
        charge=1.0,
        beautiful=True,
    ),
    "aaa": Battery(
        id="aaa",
        label="AAA battery",
        phrase="a fresh AAA battery",
        kind="aaa",
        charge=1.0,
        beautiful=True,
    ),
    "weak_aa": Battery(
        id="weak_aa",
        label="weak AA battery",
        phrase="a weak AA battery",
        kind="aa",
        charge=0.2,
        beautiful=False,
    ),
}

KINDFIXES = {
    "share": KindFix(
        id="share",
        label="share a spare battery",
        prep="look in the drawer and share a spare battery",
        tail="shared the spare battery and the toy came back to life",
        restored_charge=1.0,
        requires_help=False,
    ),
    "wait": KindFix(
        id="wait",
        label="wait for the charger",
        prep="wait for the charger to be free",
        tail="waited a little while and the battery filled back up",
        restored_charge=0.9,
        requires_help=False,
    ),
    "help_neighbor": KindFix(
        id="help_neighbor",
        label="ask the neighbor for help",
        prep="knock on the neighbor's door and ask for help",
        tail="the neighbor helped and the battery was ready again",
        restored_charge=1.0,
        requires_help=True,
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Zoe", "Maya"]
BOY_NAMES = ["Leo", "Finn", "Sam", "Noah", "Eli"]
ADULT_NAMES = ["Mom", "Dad", "Aunt June", "Mr. Hall", "Mrs. Park"]
TRAITS = ["gentle", "curious", "cheerful", "quiet", "thoughtful"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    toy: str
    battery: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
toy_needs_battery(T, B) :- toy(T), battery_kind(T, Bk), battery(B), kind(B, Bk).
battery_works(T, B) :- toy_needs_battery(T, B), charge(B, C), C >= 1.
valid_story(P, T, B, H) :- place(P), toy(T), battery(B), helper(H), toy_needs_battery(T, B), battery_works(T, B).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TOYS.items():
        lines.append(asp.fact("toy", tid))
        lines.append(asp.fact("battery_kind", tid, t.battery_kind))
    for bid, b in BATTERIES.items():
        lines.append(asp.fact("battery", bid))
        lines.append(asp.fact("kind", bid, b.kind))
        lines.append(asp.fact("charge", bid, int(b.charge * 10)))
    for hid in KINDFIXES:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def valid_combo(place: str, toy: str, battery: str) -> bool:
    return TOYS[toy].battery_kind == BATTERIES[battery].kind and BATTERIES[battery].charge >= 0.9

def choose_fix(world: World, toy: Toy, battery: Battery, helper: Entity) -> Optional[KindFix]:
    if battery.charge >= 1.0:
        return None
    if helper.type == "neighbor":
        return KINDFIXES["help_neighbor"]
    if world.setting.indoors:
        return KINDFIXES["share"]
    return KINDFIXES["wait"]

def set_charge(battery: Entity, value: float) -> None:
    battery.meters["charge"] = max(0.0, min(1.0, value))

def introduce(world: World, hero: Entity, helper: Entity, toy: Toy, battery: Battery) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait_word', 'kind')} little {hero.type} "
        f"who loved quiet afternoons at {world.setting.place}."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} had {toy.phrase}, and {battery.phrase} "
        f"was sitting nearby in a small dish."
    )

def setup_scene(world: World, hero: Entity, helper: Entity, toy: Toy, battery: Battery) -> None:
    world.say(
        f"The toy's {toy.glow_word} made the room feel beautiful when the battery was fresh."
    )
    world.say(
        f"{hero.id} liked to carry {hero.pronoun('possessive')} {toy.label} from room to room, "
        f"listening for its tiny sound."
    )

def battery_fades(world: World, hero: Entity, toy: Entity, battery: Entity) -> None:
    battery.meters["charge"] = 0.0
    toy.memes["sad"] = 1.0
    hero.memes["worry"] = 1.0
    world.say(
        f"One afternoon, the {toy.label} blinked once, then went dim."
    )
    world.say(
        f"{hero.id} frowned because the battery had become too weak for the toy's next {toy.noun()}."
    )

def kind_turn(world: World, hero: Entity, helper: Entity, toy: Entity, battery: Entity, fix: KindFix) -> None:
    world.say(
        f"{hero.id} could have cried, but {hero.pronoun('subject')} took a breath and stayed gentle."
    )
    world.say(
        f"{helper.id} smiled and said, \"Let's {fix.prep}.\""
    )
    if fix.requires_help:
        helper.memes["kindness"] = 1.0
        hero.memes["trust"] = 1.0
    else:
        hero.memes["kindness"] = 1.0
    set_charge(battery, fix.restored_charge)
    toy.memes["sad"] = 0.0
    hero.memes["worry"] = 0.0
    world.say(
        f"They {fix.tail}."
    )
    world.say(
        f"After that, the {toy.label} could {toy.glow_word} again, and the room felt cozy."
    )

def ending(world: World, hero: Entity, helper: Entity, toy: Entity, battery: Entity) -> None:
    world.say(
        f"{hero.id} put the {toy.label} on the table and thanked {helper.id} for being so kind."
    )
    world.say(
        f"The battery stayed in the toy, the little light stayed bright, and the afternoon felt peaceful."
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        memes={"trait_word": params.trait},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type="neighbor" if params.helper == "neighbor" else "adult",
    ))
    toy_cfg = TOYS[params.toy]
    battery_cfg = BATTERIES[params.battery]
    toy = world.add(Entity(
        id=toy_cfg.id,
        type="toy",
        label=toy_cfg.label,
        phrase=toy_cfg.phrase,
        owner=hero.id,
    ))
    battery = world.add(Entity(
        id=battery_cfg.id,
        type="battery",
        label=battery_cfg.label,
        phrase=battery_cfg.phrase,
    ))
    battery.meters["charge"] = battery_cfg.charge

    world.facts.update(hero=hero, helper=helper, toy=toy, battery=battery, toy_cfg=toy_cfg, battery_cfg=battery_cfg)
    return world

def tell(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    toy: Entity = world.facts["toy"]
    battery: Entity = world.facts["battery"]
    toy_cfg: Toy = world.facts["toy_cfg"]
    battery_cfg: Battery = world.facts["battery_cfg"]

    introduce(world, hero, helper, toy_cfg, battery_cfg)
    setup_scene(world, hero, helper, toy_cfg, battery_cfg)
    world.para()
    battery_fades(world, hero, toy, battery)
    fix = choose_fix(world, toy_cfg, battery_cfg, helper)
    if fix is None:
        raise StoryError("No kind fix fits this toy and battery situation.")
    world.para()
    kind_turn(world, hero, helper, toy, battery, fix)
    ending(world, hero, helper, toy, battery)

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    toy_cfg: Toy = f["toy_cfg"]
    battery_cfg: Battery = f["battery_cfg"]
    return [
        f'Write a short slice-of-life story for a small child named {hero.id} about a beautiful {toy_cfg.label} and a battery that goes dim.',
        f"Tell a gentle story where {hero.id} notices that {toy_cfg.phrase} needs {battery_cfg.phrase}, and someone answers with kindness.",
        f"Write a quiet everyday story about a toy, a battery, and a kind fix that ends with the room feeling peaceful.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    toy: Entity = f["toy"]
    battery: Entity = f["battery"]
    toy_cfg: Toy = f["toy_cfg"]
    battery_cfg: Battery = f["battery_cfg"]
    return [
        QAItem(
            question=f"What did {hero.id} love in the story?",
            answer=f"{hero.id} loved {toy_cfg.phrase}, and the toy's little sound made the day feel beautiful.",
        ),
        QAItem(
            question=f"What problem happened with the {toy.label}?",
            answer=f"The {toy.label} went dim because {battery_cfg.phrase} became too weak to keep it going.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with kindness?",
            answer=f"{helper.id} helped by suggesting a kind, practical fix instead of letting the moment turn sad.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the toy glowing again, the battery working, and {hero.id} feeling peaceful and thankful.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a battery for?",
            answer="A battery gives power to a toy or gadget so it can light up, play music, or move.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing a caring way to treat someone, like helping, sharing, or speaking gently.",
        ),
        QAItem(
            question="What does it mean when a light goes dim?",
            answer="When a light goes dim, it becomes weaker and harder to see because it does not have as much power.",
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


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world: a beautiful battery, a dim toy, and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--battery", choices=BATTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["Mom", "Dad", "neighbor"])
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
    toy = args.toy or rng.choice(list(TOYS))
    battery = args.battery or rng.choice(list(BATTERIES))
    if args.toy and args.battery and not valid_combo(args.place or "kitchen", args.toy, args.battery):
        raise StoryError("That toy and battery do not match well enough for a kind fix story.")

    place = args.place or rng.choice(list(SETTINGS))
    if args.place and not SETTINGS[place].affords:
        raise StoryError("That setting does not fit the gentle slice-of-life setup.")

    if TOYS[toy].battery_kind != BATTERIES[battery].kind:
        raise StoryError("That toy needs a different battery kind.")

    if BATTERIES[battery].charge < 0.9:
        # still okay; story is about dimming
        pass

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(ADULT_NAMES if gender in {"girl", "boy"} else ["neighbor"])
    if helper not in {"Mom", "Dad", "neighbor"}:
        helper = "neighbor"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, toy=toy, battery=battery, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:12} ({e.type}) {' '.join(bits)}")
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


# ---------------------------------------------------------------------------
# ASP / verify
# ---------------------------------------------------------------------------

def asp_verify() -> int:
    import asp
    py = set((p, t, b, h) for p in SETTINGS for t in TOYS for b in BATTERIES for h in KINDFIXES if TOYS[t].battery_kind == BATTERIES[b].kind and BATTERIES[b].charge >= 0.9)
    cl = set(asp.atoms(asp.one_model(asp_program("#show valid_story/4.")), "valid_story"))
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH:")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Curated examples
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="kitchen", toy="lantern", battery="aa", name="Mina", gender="girl", helper="Mom", trait="gentle"),
    StoryParams(place="living_room", toy="robot", battery="aa", name="Leo", gender="boy", helper="Dad", trait="curious"),
    StoryParams(place="porch", toy="bunny", battery="aaa", name="Nora", gender="girl", helper="neighbor", trait="thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible ASP stories")
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            seed = base_seed + i
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.toy} at {p.place} with {p.battery}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
