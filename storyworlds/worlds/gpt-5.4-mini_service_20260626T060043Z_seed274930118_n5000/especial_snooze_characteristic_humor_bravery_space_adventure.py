#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/especial_snooze_characteristic_humor_bravery_space_adventure.py
=================================================================================================

A small story world for a gentle Space Adventure: a child on a spaceship wants
something especial, gets sleepy in a snooze pod, shows bravery, and uses humor
to solve a tiny problem before drifting safely to the next stop.

The world model tracks physical meters and emotional memes for a few typed
entities. The story is generated from state changes, not a frozen paragraph.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wearable: bool = False
    worn_by: Optional[str] = None
    portable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def title(self) -> str:
        return self.label or self.type


@dataclass
class Ship:
    name: str = "the starship"
    place: str = "the quiet moon corridor"
    asleep_zone: str = "snooze bay"
    engine_zone: str = "engine hall"
    rescued: bool = False
    hazard: bool = False


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        import copy as _copy

        clone = World(self.ship)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class CharacterSpec:
    id: str
    type: str
    label: str
    trait: str


@dataclass
class ItemSpec:
    id: str
    label: str
    phrase: str
    kind: str
    portable: bool = True


@dataclass
class SettingSpec:
    place: str
    detail: str


CHARACTERS = {
    "aya": CharacterSpec("Aya", "girl", "Aya", "curious"),
    "timo": CharacterSpec("Timo", "boy", "Timo", "cheerful"),
    "captain": CharacterSpec("Captain", "captain", "Captain", "steady"),
}

ITEMS = {
    "especial_star": ItemSpec(
        id="especial_star",
        label="especial star badge",
        phrase="an especial star badge",
        kind="badge",
    ),
    "snooze_pillow": ItemSpec(
        id="snooze_pillow",
        label="snooze pillow",
        phrase="a soft snooze pillow",
        kind="pillow",
    ),
    "humor_chip": ItemSpec(
        id="humor_chip",
        label="humor chip",
        phrase="a tiny humor chip",
        kind="chip",
    ),
    "bravery_patch": ItemSpec(
        id="bravery_patch",
        label="bravery patch",
        phrase="a bright bravery patch",
        kind="patch",
    ),
}

SETTINGS = {
    "orbit": SettingSpec(place="the station orbit room", detail="The stars slid past the window like tiny silver fish."),
    "docking": SettingSpec(place="the docking hall", detail="The hall hummed softly, as if the ship were whispering."),
    "moonwalk": SettingSpec(place="the moon corridor", detail="The floor glowed with pale moonlight and little blue arrows."),
}

TRAITS = ["curious", "cheerful", "brave", "funny", "gentle"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    hero: str
    sidekick: str
    treasure: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(setting: str, treasure: str) -> bool:
    return setting in SETTINGS and treasure in ITEMS


def explain_rejection(setting: str, treasure: str) -> str:
    return f"(No story: setting={setting!r} or treasure={treasure!r} is not supported by this space adventure.)"


# ---------------------------------------------------------------------------
# Story world actions
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, sidekick: Entity, treasure: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} child aboard {world.ship.name}, and {sidekick.id} was always nearby with a grin."
    )
    world.say(
        f"Together they guarded {treasure.phrase}, an especial thing that made the cabin feel like a tiny celebration."
    )


def love_snooze(world: World, hero: Entity) -> None:
    hero.memes["sleepy"] = hero.memes.get("sleepy", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f"{hero.id} loved the soft snooze time before launch, when the lights dimmed and the ship grew kind and quiet."
    )


def space_problem(world: World, hero: Entity, sidekick: Entity, treasure: Entity) -> None:
    world.ship.hazard = True
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    sidekick.memes["humor"] = sidekick.memes.get("humor", 0.0) + 1
    world.say(
        f"One day, a tiny alarm chirped from the engine hall, and {hero.id} hugged {treasure.label} a little tighter."
    )
    world.say(
        f"{sidekick.id} whispered, 'That alarm sounds like a grumpy robot hiccup,' and the silly line made {hero.id} blink, then smile."
    )


def brave_step(world: World, hero: Entity) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    hero.meters["distance"] = hero.meters.get("distance", 0.0) + 1
    world.say(
        f"Even with the alarm still blinking, {hero.id} took one brave step down the corridor instead of hiding."
    )


def help_fix(world: World, hero: Entity, sidekick: Entity, treasure: Entity) -> None:
    hero.memes["humor"] = hero.memes.get("humor", 0.0) + 1
    world.ship.rescued = True
    world.ship.hazard = False
    world.say(
        f"{hero.id} told a tiny joke about a sneezy moon rock, and {sidekick.id} laughed so hard they both felt steady again."
    )
    world.say(
        f"Then they used the humor chip to calm the blinking panel, and the especial {treasure.label} stayed safe in {hero.id}'s hands."
    )


def ending(world: World, hero: Entity, sidekick: Entity, treasure: Entity) -> None:
    world.say(
        f"After that, the ship felt peaceful again. {hero.id} rested on the snooze pillow, holding {treasure.label}, while {sidekick.id} smiled at the dark window and the patient stars."
    )


# ---------------------------------------------------------------------------
# Build and generate
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    ship = Ship(place=SETTINGS[params.setting].place)
    world = World(ship)

    hero_spec = CHARACTERS[params.hero]
    side_spec = CHARACTERS[params.sidekick]
    tre_spec = ITEMS[params.treasure]

    hero = world.add(Entity(
        id=hero_spec.label,
        kind="character",
        type=hero_spec.type,
        label=hero_spec.label,
        traits=[hero_spec.trait, "little"],
    ))
    sidekick = world.add(Entity(
        id=side_spec.label,
        kind="character",
        type=side_spec.type,
        label=side_spec.label,
        traits=[side_spec.trait, "helpful"],
    ))
    treasure = world.add(Entity(
        id=tre_spec.id,
        type=tre_spec.kind,
        label=tre_spec.label,
        phrase=tre_spec.phrase,
        portable=tre_spec.portable,
    ))

    introduce(world, hero, sidekick, treasure)
    world.para()
    love_snooze(world, hero)
    world.say(SETTINGS[params.setting].detail)
    world.para()
    space_problem(world, hero, sidekick, treasure)
    brave_step(world, hero)
    help_fix(world, hero, sidekick, treasure)
    world.para()
    ending(world, hero, sidekick, treasure)

    world.facts = {
        "hero": hero,
        "sidekick": sidekick,
        "treasure": treasure,
        "setting": params.setting,
        "resolved": world.ship.rescued,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    treasure: Entity = f["treasure"]
    return [
        'Write a gentle space adventure story with the words "especial", "snooze", and "characteristic".',
        f"Tell a child-friendly story about {hero.id} on a spaceship who loves snooze time and protects {treasure.label}.",
        "Write a short story where humor and bravery help fix a tiny spaceship problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    treasure: Entity = f["treasure"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who took the brave step when the alarm chirped in {SETTINGS[setting].place}?",
            answer=f"{hero.id} took the brave step, because {hero.id} wanted to help instead of hiding.",
        ),
        QAItem(
            question=f"What did {sidekick.id} say that used humor?",
            answer=f"{sidekick.id} said the alarm sounded like a grumpy robot hiccup, and that funny idea helped everyone relax.",
        ),
        QAItem(
            question=f"What especial thing did they keep safe?",
            answer=f"They kept safe {treasure.phrase}, which stayed with {hero.id} through the whole story.",
        ),
        QAItem(
            question=f"How did the story end after the problem was fixed?",
            answer=f"It ended with the ship peaceful again, {hero.id} resting on the snooze pillow, and {sidekick.id} smiling at the stars.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a snooze pod for?",
            answer="A snooze pod is a cozy place where a traveler can rest and sleep during a long trip in space.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is when someone feels scared or unsure but still does the helpful thing anyway.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is when something is funny and helps people smile or laugh.",
        ),
        QAItem(
            question="What is a characteristic?",
            answer="A characteristic is a special feature or trait that helps describe what someone or something is like.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting_ok(S) :- setting(S).
item_ok(T) :- treasure(T).

valid_story(S, T) :- setting_ok(S), item_ok(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in ITEMS:
        lines.append(asp.fact("treasure", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {(s, t) for s in SETTINGS for t in ITEMS if valid_combo(s, t)}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combo() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combo():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with humor and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=CHARACTERS)
    ap.add_argument("--sidekick", choices=[k for k in CHARACTERS if k != "captain"])
    ap.add_argument("--treasure", choices=ITEMS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    treasure = args.treasure or rng.choice(list(ITEMS))
    if not valid_combo(setting, treasure):
        raise StoryError(explain_rejection(setting, treasure))
    hero = args.hero or rng.choice(["aya", "timo"])
    sidekick = args.sidekick or ("timo" if hero == "aya" else "aya")
    return StoryParams(setting=setting, hero=hero, sidekick=sidekick, treasure=treasure)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  ship.rescued={world.ship.rescued}")
    lines.append(f"  ship.hazard={world.ship.hazard}")
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
    StoryParams(setting="orbit", hero="aya", sidekick="timo", treasure="especial_star"),
    StoryParams(setting="docking", hero="timo", sidekick="aya", treasure="humor_chip"),
    StoryParams(setting="moonwalk", hero="aya", sidekick="timo", treasure="bravery_patch"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/2."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} compatible combos:")
        for s, t in vals:
            print(f"  {s:10} {t}")
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
