#!/usr/bin/env python3
"""
A bedtime-style storyworld about a child, a careful warning, a surprise, and
the little sounds of a cozy evening.

Seed idea:
- conditioner
- breaker
- Cautionary
- Surprise
- Sound Effects
- Bedtime Story

The domain is a simple home evening: a child wants to use or move a bottle of
conditioner near an electrical breaker box, a parent notices the risk, and the
story turns on a safe, surprising alternative. The world model tracks both
physical state (meters) and feelings (memes), and the prose is driven by those
state changes rather than by a frozen template.
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
    location: str = ""
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    name: str
    cozy: bool = True
    sounds: list[str] = field(default_factory=list)


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        w = World(self.room)
        w.entities = copy.deepcopy(self.entities)
        w.lines = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    name: str
    is_night: bool = True


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    risky: bool = False


@dataclass
class Gear:
    id: str
    label: str
    description: str
    protects_against: set[str] = field(default_factory=set)


SETTINGS = {
    "hallway": Setting(name="the hallway", is_night=True),
    "bathroom": Setting(name="the bathroom", is_night=True),
    "laundry_room": Setting(name="the laundry room", is_night=True),
}

ITEMS = {
    "conditioner": Item(
        id="conditioner",
        label="conditioner",
        phrase="a smooth bottle of conditioner",
        kind="bath bottle",
        risky=True,
    ),
    "breaker": Item(
        id="breaker",
        label="breaker",
        phrase="the little breaker panel door",
        kind="electric panel",
        risky=True,
    ),
    "nightlight": Item(
        id="nightlight",
        label="nightlight",
        phrase="a tiny nightlight",
        kind="lamp",
        risky=False,
    ),
}

GEAR = {
    "basket": Gear(
        id="basket",
        label="a basket",
        description="put the bottle in a basket and carry it with two hands",
        protects_against={"drop", "spill"},
    ),
    "stool": Gear(
        id="stool",
        label="a step stool",
        description="use a step stool so nobody reaches the breaker box alone",
        protects_against={"reach"},
    ),
    "gloves": Gear(
        id="gloves",
        label="soft gloves",
        description="wear soft gloves while moving bottles in the dark",
        protects_against={"slip"},
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ivy", "Ada"]
BOY_NAMES = ["Theo", "Ben", "Finn", "Owen", "Max"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    hero_name: str
    hero_type: str
    parent_type: str
    item: str
    surprise: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Cause and effect
# ---------------------------------------------------------------------------
def _fire_sounds(world: World) -> None:
    for s in world.room.sounds:
        if s == "click":
            world.say("Click.")
        elif s == "tap":
            world.say("Tap tap.")
        elif s == "whoosh":
            world.say("Whoosh.")
        elif s == "soft rattle":
            world.say("A soft rattle answered from the shelf.")


def _check_risk(world: World) -> None:
    child = next(e for e in world.entities.values() if e.kind == "character" and e.type in {"girl", "boy"})
    item = world.get(world.facts["item_id"])
    if world.facts["scene"] == "breaker" and child.memes.get("curiosity", 0) >= THRESHOLD:
        sig = ("risk", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] = child.memes.get("worry", 0) + 1
            world.say(
                f"{child.pronoun().capitalize()} got a little too close to the breaker box."
            )


def simulate_touch(world: World, child: Entity, item: Entity) -> None:
    if world.facts["scene"] == "breaker":
        child.meters["near_breaker"] = child.meters.get("near_breaker", 0) + 1
        child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
        _check_risk(world)


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(setting: str, item: str) -> bool:
    if setting not in SETTINGS or item not in ITEMS:
        return False
    if setting == "bathroom" and item == "conditioner":
        return True
    if setting == "hallway" and item in {"conditioner", "nightlight"}:
        return True
    if setting == "laundry_room" and item == "conditioner":
        return True
    return False


def explain_rejection(setting: str, item: str) -> str:
    return (
        f"(No story: {ITEMS[item].label} does not make a convincing bedtime worry in {SETTINGS[setting].name}. "
        f"Try the bathroom or hallway, where the little risk can feel real.)"
    )


# ---------------------------------------------------------------------------
# Story language
# ---------------------------------------------------------------------------
def room_detail(setting: Setting) -> str:
    if setting.name == "the bathroom":
        return "The bathroom was sleepy and bright with a tiny light."
    if setting.name == "the hallway":
        return "The hallway was quiet, with soft shadows along the wall."
    return "The laundry room was warm and full of folded towels."


def intro(world: World, child: Entity, parent: Entity, item: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.type} who loved bedtime because everything in the house sounded gentle and small."
    )
    world.say(
        f"{child.pronoun().capitalize()} liked {item.label} because it looked silky and smooth in the dim light."
    )


def desire(world: World, child: Entity, item: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    world.say(
        f"One night, {child.id} wanted to carry the {item.label} down the hall just to hear it make a tiny sound."
    )


def caution(world: World, parent: Entity, child: Entity, item: Entity) -> None:
    child.memes["warning"] = child.memes.get("warning", 0) + 1
    world.say(
        f'"Careful," {parent.label} said softly. "The breaker box is not a toy. Let\'s keep the {item.label} away from it."'
    )


def surprise(world: World, child: Entity, parent: Entity, gear: Gear) -> None:
    child.memes["surprise"] = child.memes.get("surprise", 0) + 1
    world.say(
        f"Then {parent.label} smiled and surprised {child.id} with {gear.label}."
    )
    world.say(f'"How about we {gear.description}?"')


def resolution(world: World, child: Entity, parent: Entity, item: Entity, gear: Gear) -> None:
    child.memes["worry"] = 0
    child.memes["calm"] = child.memes.get("calm", 0) + 1
    item.meters["safe"] = item.meters.get("safe", 0) + 1
    world.say(
        f"So {child.id} helped {parent.label} tuck the {item.label} into {gear.label}, and the night felt safe again."
    )
    world.say(
        f"In the hush after that, the house made only soft little sounds, and {child.id} felt sleepy and proud."
    )


# ---------------------------------------------------------------------------
# World building
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    room = Room(name=setting.name, cozy=True, sounds=["click", "tap", "soft rattle"])
    if params.surprise == "surprise":
        room.sounds.append("whoosh")
    world = World(room)

    child = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={},
        memes={"curiosity": 0.0, "worry": 0.0, "surprise": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_type,
        label="the parent",
        meters={},
        memes={},
    ))
    item = world.add(Entity(
        id=params.item,
        kind="thing",
        type=ITEMS[params.item].kind,
        label=ITEMS[params.item].label,
        phrase=ITEMS[params.item].phrase,
        caretaker=parent.id,
        meters={"safe": 0.0},
        memes={},
    ))
    gear = GEAR["basket"] if params.item == "conditioner" else GEAR["stool"]

    world.facts.update(
        scene="breaker" if params.setting in {"hallway", "bathroom"} else "home",
        item_id=item.id,
        gear_id=gear.id,
        parent_id=parent.id,
        child_id=child.id,
    )

    intro(world, child, parent, item)
    world.para()
    world.say(room_detail(setting))
    desire(world, child, item)
    simulate_touch(world, child, item)
    caution(world, parent, child, item)
    world.say("Click. Tap tap.")
    surprise(world, child, parent, gear)
    world.say("Whoosh.")
    resolution(world, child, parent, item, gear)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    child = world.get(world.facts["child_id"])
    item = world.get(world.facts["item_id"])
    return [
        f"Write a cozy bedtime story about {child.id} and a {item.label}, with a careful warning and a happy surprise.",
        f"Tell a child-friendly story where a {child.type} wants to touch a {item.label} near the breaker box but learns a safer way.",
        f"Write a bedtime tale with soft sound effects like 'click' and 'whoosh' that ends with everyone feeling safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.get(world.facts["child_id"])
    parent = world.get(world.facts["parent_id"])
    item = world.get(world.facts["item_id"])
    gear = GEAR[world.facts["gear_id"]]
    return [
        QAItem(
            question=f"Why did {parent.label} tell {child.id} to be careful about the {item.label}?",
            answer=(
                f"{parent.label} was careful because the {item.label} was near the breaker box, and that is not a toy. "
                f"{child.id} needed a safer plan for bedtime."
            ),
        ),
        QAItem(
            question=f"What surprise helped {child.id} stay safe with the {item.label}?",
            answer=(
                f"{parent.label} surprised {child.id} with {gear.label}, which helped keep the {item.label} away from the breaker box."
            ),
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=(
                f"It ended with {child.id} feeling calm and proud, while the house stayed quiet and safe for bedtime."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a breaker box for?",
            answer="A breaker box helps protect a house's electrical wires by turning power off when something goes wrong.",
        ),
        QAItem(
            question="Why should conditioner be kept away from electrical things?",
            answer="Conditioner belongs in the bathroom and should be kept away from electrical things so the house stays safe and dry.",
        ),
        QAItem(
            question="Why are soft sound effects nice in a bedtime story?",
            answer="Soft sound effects make a bedtime story feel cozy, gentle, and sleepy instead of loud or scary.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world qa ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"room={world.room.name} sounds={world.room.sounds}")
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(hallway).
setting(bathroom).
setting(laundry_room).

valid(S, conditioner) :- setting(S), (S = hallway; S = bathroom; S = laundry_room).
valid_story(S, conditioner, bedtime) :- valid(S, conditioner).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(asp.fact("setting", s) for s in SETTINGS)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid/2."))
    asp_vals = set(asp.atoms(model, "valid"))
    py_vals = {(s, "conditioner") for s in SETTINGS}
    if asp_vals == py_vals:
        print(f"OK: ASP matches Python ({len(py_vals)} valid combos).")
        return 0
    print("Mismatch:")
    print("ASP:", sorted(asp_vals))
    print("PY :", sorted(py_vals))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime storyworld about conditioner, breaker, caution, surprise, and gentle sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def valid_combos() -> list[tuple[str, str]]:
    return [(s, i) for s in SETTINGS for i in ITEMS if valid_combo(s, i)]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.item:
        combos = [c for c in combos if c[1] == args.item]
    if not combos:
        raise StoryError("(No valid story combination matches the given options.)")
    setting, item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, hero_name=name, hero_type=gender, parent_type=parent, item=item, surprise="surprise")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} valid combos:")
        for v in vals:
            print(v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting, item in sorted(valid_combos()):
            params = StoryParams(
                setting=setting,
                hero_name="Mia" if item == "conditioner" else "Theo",
                hero_type="girl" if item == "conditioner" else "boy",
                parent_type="mother",
                item=item,
                surprise="surprise",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as exc:
                print(exc)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.setting} / {p.item}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
