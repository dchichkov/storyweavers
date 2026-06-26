#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/cheese_solar_abc_twist_sharing_bedtime_story.py
==============================================================================================================

A small bedtime-story world about a child, a bright solar night-light, an ABC
book, and a cheese snack that helps turn a twisty bedtime into a shared one.

Premise:
- A child wants to stay up for one more page, one more bite, one more look at
  the glowing solar lamp.
- The room feels a little too bright and a little too busy.
- Sharing the book, the snack, and the soft light helps the child settle down.

The world model tracks:
- physical meters: brightness, hunger, coziness, sleepiness, tidy
- emotional memes: desire, worry, comfort, sharing, connection, calm

The prose is driven by state changes, not a frozen template.
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

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"brightness": 0.0, "hunger": 0.0, "coziness": 0.0, "sleepiness": 0.0, "tidy": 0.0}
        if not self.memes:
            self.memes = {"desire": 0.0, "worry": 0.0, "comfort": 0.0, "sharing": 0.0, "connection": 0.0, "calm": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bedroom"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class ItemDef:
    id: str
    label: str
    phrase: str
    kind: str
    risk: str
    fix: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    gender: str
    parent: str
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
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _say_sleepy_opening(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"At bedtime, {child.id} was a little {child.type} who liked one more story, one more snack, and one more hug."
    )
    world.say(f"{child.pronoun().capitalize()} snuggled beside {parent.pronoun('possessive')} {parent.type} and looked at the glowing night-light.")


def _say_items(world: World, child: Entity, item: Entity) -> None:
    if item.type == "abc_book":
        world.say(f"On the blanket lay {item.phrase}, and {child.id} loved pointing at the letters.")
    elif item.type == "cheese_snack":
        world.say(f"On the little plate waited {item.phrase}, warm and soft and very hard to ignore.")
    elif item.type == "solar_lamp":
        world.say(f"Near the pillow stood {item.phrase}, a tiny solar lamp that kept a gentle glow after sunset.")


def _tick_worry(world: World, child: Entity, item: Entity) -> None:
    if item.type == "solar_lamp":
        child.memes["worry"] += 1
        child.meters["brightness"] += 1
    elif item.type == "cheese_snack":
        child.meters["hunger"] += 1
        child.memes["desire"] += 1
    elif item.type == "abc_book":
        child.memes["desire"] += 1
        child.meters["sleepiness"] += 0.25


def _rule_brightness(world: World) -> list[str]:
    out: list[str] = []
    for child in world.characters():
        if child.meters["brightness"] < THRESHOLD:
            continue
        sig = ("bright", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["worry"] += 1
        out.append(f"The lamp felt a little too bright for sleepy eyes.")
    return out


def _rule_shared_comfort(world: World) -> list[str]:
    out: list[str] = []
    for child in world.characters():
        if child.memes["sharing"] < THRESHOLD:
            continue
        sig = ("shared", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.meters["coziness"] += 1
        child.meters["sleepiness"] += 1
        child.memes["comfort"] += 1
        child.memes["calm"] += 1
        out.append(f"Sharing made the room feel softer and warmer.")
    return out


def _rule_sleep(world: World) -> list[str]:
    out: list[str] = []
    for child in world.characters():
        if child.meters["sleepiness"] < 1.5 or child.memes["calm"] < THRESHOLD:
            continue
        sig = ("sleep", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{child.id} grew sleepy at last.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_rule_brightness, _rule_shared_comfort, _rule_sleep):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING = Setting(place="the bedroom", indoors=True, affords={"reading", "snacking", "glow"})
ITEMS = {
    "abc": ItemDef(
        id="abc",
        label="ABC book",
        phrase="a bright ABC book with big round letters",
        kind="abc_book",
        risk="too much excitement",
        fix="reading together slowly",
        keyword="abc",
        tags={"abc", "book", "letters"},
    ),
    "cheese": ItemDef(
        id="cheese",
        label="cheese snack",
        phrase="a tiny cheese snack on a blue plate",
        kind="cheese_snack",
        risk="hunger that keeps a child up",
        fix="sharing a snack",
        keyword="cheese",
        tags={"cheese", "snack", "food"},
    ),
    "solar": ItemDef(
        id="solar",
        label="solar lamp",
        phrase="a little solar lamp on the windowsill",
        kind="solar_lamp",
        risk="a light that is too bright",
        fix="turning it to a soft glow and sharing the blanket",
        keyword="solar",
        tags={"solar", "light", "lamp"},
    ),
}
GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Ben", "Max"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in {"bedroom": SETTING}.items():
        for item_id in ITEMS:
            combos.append((place, item_id))
    return combos


def reasonableness_check(item: ItemDef) -> None:
    if item.id not in ITEMS:
        raise StoryError("Unknown item.")
    # All three are bedtime-appropriate; this is a tiny, constraint-checked world.
    if item.kind not in {"abc_book", "cheese_snack", "solar_lamp"}:
        raise StoryError("That item does not belong in this bedtime storyworld.")


def build_world(params: StoryParams) -> World:
    setting = SETTING
    item_def = ITEMS[params.item]
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    book = world.add(Entity(id="abc_item", type="abc_book", label="ABC book", phrase="a bright ABC book with big round letters", owner=child.id))
    cheese = world.add(Entity(id="cheese_item", type="cheese_snack", label="cheese snack", phrase="a tiny cheese snack on a blue plate", owner=child.id))
    lamp = world.add(Entity(id="solar_item", type="solar_lamp", label="solar lamp", phrase="a little solar lamp on the windowsill", owner=child.id))
    world.facts.update(child=child, parent=parent, item=item_def, book=book, cheese=cheese, lamp=lamp)
    return world


def tell_story(world: World, params: StoryParams) -> None:
    child = world.get(params.name)
    parent = world.get("Parent")
    item_def = ITEMS[params.item]
    _say_sleepy_opening(world, child, parent)
    world.para()
    _say_items(world, child, world.facts["book"])
    _say_items(world, child, world.facts["cheese"])
    _say_items(world, child, world.facts["lamp"])

    if item_def.id == "solar":
        _tick_worry(world, child, world.facts["lamp"])
        world.say(f"{child.id} wanted the glowing lamp on all night, but {parent.id} worried it would keep {child.pronoun('object')} awake.")
        propagate(world)
        world.para()
        world.say(f"Then {parent.id} showed {child.id} how to turn the solar lamp toward the wall so it became a soft moonlike dot.")
        child.memes["sharing"] += 1
        child.memes["connection"] += 1
        child.meters["coziness"] += 1
        child.meters["sleepiness"] += 1
        propagate(world)
        world.say(f"{child.id} whispered good night to the little light, and the room finally felt quiet.")
    elif item_def.id == "abc":
        _tick_worry(world, child, world.facts["book"])
        world.say(f"{child.id} wanted one more page of the ABC book, and one page turned into two.")
        child.memes["desire"] += 1
        child.memes["worry"] += 0.5
        world.say(f"{parent.id} smiled and suggested sharing the reading: one letter for {child.id}, then one letter for {parent.id}.")
        child.memes["sharing"] += 1
        child.memes["connection"] += 1
        child.meters["coziness"] += 1
        child.meters["sleepiness"] += 1
        propagate(world)
        world.para()
        world.say(f"They reached the letter Z and closed the book with a soft pat. {child.id} felt ready for dreams.")
    else:
        _tick_worry(world, child, world.facts["cheese"])
        world.say(f"{child.id} kept looking at the cheese snack because a small hungry tummy does not like bedtime.")
        child.memes["desire"] += 1
        world.say(f"{parent.id} sat beside {child.id} and split the snack into two little bites, so they could share it.")
        child.memes["sharing"] += 1
        child.memes["connection"] += 1
        child.meters["coziness"] += 1
        child.meters["hunger"] -= 1
        child.meters["sleepiness"] += 1
        propagate(world)
        world.para()
        world.say(f"With the cheese finished and the blanket tucked in, {child.id} yawned a very long yawn and drifted off.")


def generation_prompts(world: World) -> list[str]:
    item = world.facts["item"]
    child = world.facts["child"]
    return [
        f'Write a bedtime story for a small child that includes "{item.keyword}", "Twist", and "Sharing".',
        f"Tell a gentle story about {child.id} and a {item.label} that starts with a twist and ends with sharing.",
        f"Write a cozy story where bedtime feels tricky at first, then becomes calm through sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    item = world.facts["item"]
    qa = [
        QAItem(
            question=f"What kind of story is this about {child.id} at bedtime?",
            answer=f"It is a cozy bedtime story about {child.id} and {parent.id} in the bedroom.",
        ),
        QAItem(
            question=f"What important thing did the story include: {item.keyword}, Twist, or Sharing?",
            answer=f"It included all three: {item.keyword}, a twist, and sharing.",
        ),
        QAItem(
            question=f"Why did {child.id} need help at first?",
            answer=f"{child.id} had a bedtime twist: the {item.label} was exciting, bright, or tasty enough to make settling down harder.",
        ),
    ]
    if item.id == "solar":
        qa.append(QAItem(
            question=f"How did the solar lamp stop being a problem?",
            answer="The lamp was turned toward the wall so it became a soft glow instead of a bright light.",
        ))
    elif item.id == "abc":
        qa.append(QAItem(
            question=f"How did the ABC book help the child get sleepy?",
            answer="They shared the reading slowly, and the last page helped the child feel calm and ready for sleep.",
        ))
    else:
        qa.append(QAItem(
            question=f"How did the cheese snack change the bedtime mood?",
            answer="Sharing the snack made the child feel cared for, and that comfort helped bedtime become peaceful.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    item = world.facts["item"]
    out = []
    if "cheese" in item.tags:
        out.append(QAItem(question="What is cheese?", answer="Cheese is a food made from milk. People often eat it as a snack or on bread."))
    if "solar" in item.tags:
        out.append(QAItem(question="What does solar mean?", answer="Solar means related to the sun or powered by sunlight."))
    if "abc" in item.tags:
        out.append(QAItem(question="What are the ABCs?", answer="The ABCs are the letters of the alphabet, starting with A, B, and C."))
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 2) for k, v in e.memes.items() if abs(v) > 1e-9}
        lines.append(f"  {e.id:10} ({e.type:10}) meters={meters} memes={memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld with cheese, solar, and abc.")
    ap.add_argument("--place", choices=["bedroom"], default=None)
    ap.add_argument("--item", choices=sorted(ITEMS))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item:
        reasonableness_check(ITEMS[args.item])
    item = args.item or rng.choice(sorted(ITEMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    if gender == "girl":
        name = args.name or rng.choice(GIRL_NAMES)
        parent = args.parent or rng.choice(["mother", "father"])
    else:
        name = args.name or rng.choice(BOY_NAMES)
        parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place="bedroom", item=item, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
item_kind(abc, abc_book).
item_kind(cheese, cheese_snack).
item_kind(solar, solar_lamp).

valid_story(Item) :- item_kind(Item, abc_book).
valid_story(Item) :- item_kind(Item, cheese_snack).
valid_story(Item) :- item_kind(Item, solar_lamp).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_items() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    python_set = {(k,) for k in ITEMS}
    clingo_set = set(asp_valid_items())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} items).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for item_id in sorted(ITEMS):
            params = StoryParams(place="bedroom", item=item_id, name="Mia", gender="girl", parent="mother")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
