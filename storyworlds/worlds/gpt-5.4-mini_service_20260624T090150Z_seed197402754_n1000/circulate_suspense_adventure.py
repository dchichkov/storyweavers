#!/usr/bin/env python3
"""
storyworlds/worlds/circulate_suspense_adventure.py
===================================================

A small adventure storyworld about a precious item that must circulate safely
from one helper to another before a suspenseful mistake can happen.

Seed tale:
---
A young child sets out on a breezy adventure trail with a special lantern note.
The note must circulate through a few hands to reach the dock keeper before
nightfall. A gust, a narrow bridge, and a missing pouch add suspense. In the end,
the child and a helper find a safer way to carry the note, and the path opens
again.

World idea:
---
- One precious object must circulate among trusted helpers.
- Suspense rises when the object is almost lost, delayed, or damaged.
- The adventure resolves when the group uses a careful route or protective pouch.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    protective: bool = False
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
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Place:
    label: str
    detail: str
    risky: bool = False
    helps: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    danger: str
    region: str
    needs_pouch: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    helps: set[str]
    prep: str
    finish: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.route: list[str] = []
        self.suspense: float = 0.0

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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.route = list(self.route)
        clone.suspense = self.suspense
        clone.paragraphs = [[]]
        return clone


def _step_suspense(world: World, amount: float, note: str = "") -> None:
    world.suspense += amount
    if note:
        world.say(note)


def _r_delay(world: World) -> list[str]:
    out = []
    token = ("delay", tuple(world.route))
    if token in world.fired:
        return out
    if len(world.route) >= 2 and world.suspense >= THRESHOLD:
        world.fired.add(token)
        out.append("The path felt slower now, as if the day were holding its breath.")
    return out


def _r_loss(world: World) -> list[str]:
    out = []
    note = world.facts.get("note")
    courier = world.facts.get("courier")
    if not note or not courier:
        return out
    if world.get(note.id).carried_by is None and world.suspense >= 2 * THRESHOLD:
        sig = ("lost", note.id)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("A sharp gust nearly snatched the note away.")
    return out


CAUSAL_RULES = [
    _r_delay,
    _r_loss,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_risk(world: World, carrier: Entity, item: Item, gear_on: bool) -> dict:
    sim = world.copy()
    sim.get(carrier.id).memes["worry"] = sim.get(carrier.id).memes.get("worry", 0) + 1
    if not gear_on:
        sim.suspense += 2
    else:
        sim.suspense += 1
    return {
        "lost": sim.suspense >= 2 * THRESHOLD and not gear_on,
        "delayed": sim.suspense >= THRESHOLD,
    }


def can_help(item: Item, gear: Gear) -> bool:
    return item.id in gear.helps or item.tags & gear.helps


def select_gear(item: Item) -> Optional[Gear]:
    for gear in GEAR:
        if can_help(item, gear):
            return gear
    return None


def introduce(world: World, hero: Entity, companion: Entity) -> None:
    world.say(
        f"{hero.id} was a small {hero.traits[0]} {hero.type} with a brave step, "
        f"and {companion.id} was ready to help."
    )


def setup_object(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    item.carried_by = hero.id
    world.say(
        f"{hero.id} carried {hero.pronoun('possessive')} {item.label} because "
        f"the note had to circulate to the dock keeper before nightfall."
    )


def arrive(world: World) -> None:
    world.say(world.place.detail)


def offer_warning(world: World, hero: Entity, companion: Entity, item: Entity) -> None:
    pred = predict_risk(world, hero, world.facts["item_cfg"], gear_on=False)
    if pred["lost"]:
        world.facts["predicted_lost"] = True
        world.say(
            f'"Keep a grip on the {item.label}," {companion.id} said. '
            f'"The wind is getting bold."'
        )
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        world.suspense += 1
    else:
        world.say(f"{companion.id} glanced at the trail and stayed watchful.")


def cross_bridge(world: World, hero: Entity, companion: Entity, item: Entity) -> None:
    hero.memes["courage"] = hero.memes.get("courage", 0) + 1
    world.route.append("bridge")
    _step_suspense(world, 1, f"{hero.id} stepped onto the narrow bridge.")
    propagate(world)


def almost_drop(world: World, hero: Entity, item: Entity) -> None:
    if world.suspense >= 2 * THRESHOLD:
        world.say(
            f"A gust flicked the {item.label}, and {hero.id} nearly dropped it."
        )
        hero.memes["alarm"] = hero.memes.get("alarm", 0) + 1


def choose_fix(world: World, hero: Entity, companion: Entity, item: Entity) -> Optional[Gear]:
    gear = select_gear(world.facts["item_cfg"])
    if gear is None:
        return None
    if not can_help(world.facts["item_cfg"], gear):
        return None
    world.say(
        f"{companion.id} smiled and suggested {gear.prep}."
    )
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    return gear


def accept_fix(world: World, hero: Entity, companion: Entity, item: Entity, gear: Gear) -> None:
    pouch = world.add(Entity(
        id=gear.id,
        kind="thing",
        type="gear",
        label=gear.label,
        protective=True,
        owner=hero.id,
    ))
    pouch.carried_by = hero.id
    item.carried_by = hero.id
    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0) - 1)
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.suspense = max(0.0, world.suspense - 1)
    world.say(
        f"{hero.id} tucked the {item.label} safely inside {gear.label}. "
        f"Then they kept going, and {gear.finish}."
    )
    world.say(
        f"The note kept circulating without trouble, and the trail felt open again."
    )


def tell(place: Place, item_cfg: Item, hero_name: str, hero_type: str, companion_name: str,
         companion_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["curious", "brave"]))
    companion = world.add(Entity(id=companion_name, kind="character", type=companion_type, traits=["careful"]))
    item = world.add(Entity(id="note", kind="thing", type="note", label=item_cfg.label, phrase=item_cfg.phrase, owner=hero.id))
    world.facts.update(hero=hero, companion=companion, note=item, item_cfg=item_cfg, place=place)

    introduce(world, hero, companion)
    world.para()
    setup_object(world, hero, item)
    arrive(world)
    offer_warning(world, hero, companion, item)
    cross_bridge(world, hero, companion, item)
    almost_drop(world, hero, item)
    world.para()
    gear = choose_fix(world, hero, companion, item)
    if gear:
        accept_fix(world, hero, companion, item, gear)
        world.facts["gear"] = gear
        world.facts["resolved"] = True
    else:
        world.say(f"{hero.id} kept the note close and chose the safest steps instead.")
        world.facts["gear"] = None
        world.facts["resolved"] = False
    return world


SETTINGS = {
    "docks": Place(
        label="the docks",
        detail="The docks were bright with ropes, gulls, and a long wooden path over the water.",
        risky=True,
        helps={"pouch", "lantern"},
    ),
    "forest": Place(
        label="the forest trail",
        detail="The forest trail wound under tall trees, where the wind could hide behind every bend.",
        risky=True,
        helps={"pouch", "map"},
    ),
    "hills": Place(
        label="the hill road",
        detail="The hill road climbed hard and wide, with one narrow bridge near the top.",
        risky=True,
        helps={"pouch", "map"},
    ),
}

ITEMS = {
    "lantern_note": Item(
        id="lantern_note",
        label="lantern note",
        phrase="a folded note wrapped in yellow paper",
        danger="blown away",
        region="hands",
        needs_pouch=True,
        tags={"lantern", "note", "wind"},
    ),
    "map_scroll": Item(
        id="map_scroll",
        label="map scroll",
        phrase="a small map rolled tight with a red ribbon",
        danger="torn",
        region="hands",
        needs_pouch=True,
        tags={"map", "trail", "paper"},
    ),
    "dock_key": Item(
        id="dock_key",
        label="dock key",
        phrase="a brass key for the gate at the dock",
        danger="lost",
        region="pocket",
        needs_pouch=False,
        tags={"key", "dock", "brass"},
    ),
}

GEAR = [
    Gear(
        id="pouch",
        label="a soft pouch",
        helps={"lantern", "note", "paper", "key", "dock_key", "map"},
        prep="put it in a soft pouch first",
        finish="the pouch stayed shut against the wind",
    ),
    Gear(
        id="lantern_case",
        label="a lantern case",
        helps={"lantern", "note"},
        prep="use the lantern case for the note",
        finish="its lid clicked tight as they walked",
    ),
    Gear(
        id="map_tube",
        label="a map tube",
        helps={"map", "paper"},
        prep="slide the map into a map tube",
        finish="the tube kept the paper straight and safe",
    ),
]

HERO_NAMES = ["Mia", "Noah", "Ava", "Eli", "Luna", "Theo"]
COMPANION_NAMES = ["Pip", "Rae", "Jori", "Ned", "Tess", "Milo"]
TRAITS = ["curious", "bold", "cheerful", "spirited", "patient"]


@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    gender: str
    companion: str
    companion_gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in SETTINGS.items():
        for item_id, item in ITEMS.items():
            if item.needs_pouch and select_gear(item) is not None:
                combos.append((place_id, item_id))
            elif not item.needs_pouch and place.risky:
                combos.append((place_id, item_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["note"]
    place = f["place"]
    return [
        f'Write a short adventure story for a young child where a {hero.type} named {hero.id} helps a {item.label} circulate safely at {place.label}.',
        f"Tell a suspenseful but gentle tale where {hero.id} carries {item.phrase} through {place.label} and solves a problem with a careful helper.",
        f'Write a story in an adventure style that uses the word "circulate" and ends with the note reaching the right person.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, companion, note, place = f["hero"], f["companion"], f["note"], f["place"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who carried the {note.label} at first?",
            answer=f"{hero.id} carried the {note.label} at first so it could circulate along the trail.",
        ),
        QAItem(
            question=f"Why did the day feel suspenseful at {place.label}?",
            answer=f"It felt suspenseful because the wind and the narrow path could have made the {note.label} get lost before it reached the dock keeper.",
        ),
        QAItem(
            question=f"Who gave the careful warning to {hero.id}?",
            answer=f"{companion.id} gave the warning and helped {hero.id} notice the danger on the path.",
        ),
    ]
    if gear:
        qa.append(QAItem(
            question=f"How did {gear.label} help the story end well?",
            answer=f"{gear.label.capitalize()} kept the {note.label} safe, so the note could keep circulating without being lost.",
        ))
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"What changed for {hero.id} at the end?",
            answer=f"{hero.id} felt braver and calmer at the end, because the note was safe and the trail opened up again.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does circulate mean?",
            answer="To circulate means to move from one person to another, or from one place to another, in a path that keeps going.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next, especially when something important might be lost or go wrong.",
        ),
        QAItem(
            question="What is an adventure story?",
            answer="An adventure story is a story about a brave journey, a problem to solve, and a place that feels exciting to explore.",
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
        if e.protective:
            bits.append("protective=True")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  route={world.route}")
    lines.append(f"  suspense={world.suspense}")
    return "\n".join(lines)


ASP_RULES = r"""
need_fix(Item) :- item(Item), needs_pouch(Item).
compatible(G, Item) :- gear(G), item(Item), helps(G, Tag), tagged(Item, Tag).
valid(Place, Item) :- place(Place), item(Item), place_risky(Place), compatible(_, Item).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if p.risky:
            lines.append(asp.fact("place_risky", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.needs_pouch:
            lines.append(asp.fact("needs_pouch", iid))
        for tag in sorted(item.tags):
            lines.append(asp.fact("tagged", iid, tag))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for tag in sorted(gear.helps):
            lines.append(asp.fact("helps", gear.id, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with circulating suspense.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.item:
        combos = [c for c in combos if c[1] == args.item]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    companion_gender = args.companion_gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    companion = args.companion or rng.choice(COMPANION_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        item=item,
        name=name,
        gender=gender,
        companion=companion,
        companion_gender=companion_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ITEMS[params.item],
        params.name,
        params.gender,
        params.companion,
        params.companion_gender,
    )
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item) combos:\n")
        for place, item in combos:
            print(f"  {place:10} {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, item in sorted(valid_combos()):
            p = StoryParams(
                place=place,
                item=item,
                name="Mia",
                gender="girl",
                companion="Pip",
                companion_gender="boy",
                trait="curious",
            )
            samples.append(generate(p))
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
            header = f"### {p.name}: {p.item} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
