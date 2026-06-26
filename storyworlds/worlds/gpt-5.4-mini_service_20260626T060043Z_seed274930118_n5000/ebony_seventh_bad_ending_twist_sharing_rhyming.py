#!/usr/bin/env python3
"""
storyworlds/worlds/ebony_seventh_bad_ending_twist_sharing_rhyming.py
====================================================================

A tiny story world in a rhyming style about ebony, the seventh thing, sharing,
and a twist that leads to a bad ending.

Premise:
- A child owns or finds something ebony and special.
- The child must share it with others.
- A twist changes the plan.
- The ending is a bad ending, but still feels like a complete little story.

This world is built as a small simulation with physical meters and emotional
memes. It includes an ASP twin for reasonableness checks and story generation
parity.
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
    carried_by: Optional[str] = None
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


@dataclass
class Place:
    name: str
    light: str
    echo: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    mess: str
    region: str
    is_ebony: bool = False
    fragile: bool = False
    plural: bool = False


@dataclass
class Rule:
    name: str
    apply: callable


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.item_defs: dict[str, Item] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.twist_triggered: bool = False
        self.bad_end: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.item_defs[item.id] = item
        return item

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.item_defs = copy.deepcopy(self.item_defs)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.twist_triggered = self.twist_triggered
        clone.bad_end = self.bad_end
        return clone


def _r_drop(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("spill", 0.0) < THRESHOLD:
            continue
        carried = [e for e in world.entities.values() if e.carried_by == actor.id]
        for item in carried:
            sig = ("drop", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["loss"] = actor.memes.get("loss", 0.0) + 1
            out.append(f"The {item.label} slipped from {actor.pronoun('possessive')} grip.")
    return out


def _r_laugh_hurt(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("shame", 0.0) < THRESHOLD:
            continue
        sig = ("hurt", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["sad"] = actor.memes.get("sad", 0.0) + 1
        out.append(f"That made {actor.id} feel small and blue.")
    return out


def _r_twist(world: World) -> list[str]:
    if world.twist_triggered:
        return []
    for actor in world.characters():
        if actor.memes.get("share", 0.0) >= THRESHOLD and actor.meters.get("want", 0.0) >= THRESHOLD:
            sig = ("twist", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            world.twist_triggered = True
            actor.memes["surprise"] = actor.memes.get("surprise", 0.0) + 1
            actor.memes["trust"] = actor.memes.get("trust", 0.0) - 0.5
            return [f"But then came a twist in the light, quick as a kite."]
    return []


CAUSAL_RULES = [
    Rule("drop", _r_drop),
    Rule("hurt", _r_laugh_hurt),
    Rule("twist", _r_twist),
]


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


def rhyming_open(place: Place) -> str:
    return f"In {place.name}, where the dim light would gleam, a small tale began like a half-finished dream."


def rhyming_set(scene: str) -> str:
    return scene


def predict_drop(world: World, actor: Entity) -> bool:
    sim = world.copy()
    sim.get(actor.id).memes["spill"] = 1.0
    propagate(sim, narrate=False)
    return any(e.carried_by == actor.id for e in sim.entities.values()) is False


def tell(world: World, hero: Entity, friend: Entity, prize: Entity, spare: Entity) -> World:
    world.say(rhyming_open(world.place))
    world.say(
        f"{hero.id} had the {prize.label}, so ebony and fine, "
        f"and called it the {prize.phrase}, all shiny and mine."
    )
    world.say(
        f"{friend.id} came along with a grin and a tune, "
        f"and asked for a turn by the edge of the moon."
    )

    world.para()
    hero.memes["share"] = hero.memes.get("share", 0.0) + 1
    hero.meters["want"] = hero.meters.get("want", 0.0) + 1
    world.say(
        f"{hero.id} wanted to share, like a song with a rhyme, "
        f"but also held tight to it, half the time."
    )
    world.say(
        f"{friend.id} reached out slowly, with soft careful care, "
        f"and the room felt so still it could hang in the air."
    )
    if predict_drop(world, hero):
        world.say(
            f"{hero.id} saw the prize could go clack on the floor, "
            f"so {hero.pronoun('subject')} promised a turn, then one turn more."
        )

    world.para()
    hero.memes["shame"] = hero.memes.get("shame", 0.0) + 1
    world.say(
        f"But a twist made things tingle, then tangle, then sway: "
        f"{spare.label} bumped the prize right out of the way."
    )
    hero.memes["spill"] = hero.memes.get("spill", 0.0) + 1
    prize.carried_by = None
    propagate(world, narrate=True)

    world.say(
        f"{friend.id} laughed by mistake, not cruel, just too near, "
        f"and {hero.id} felt the laugh land sharp in the ear."
    )
    world.bad_end = True
    hero.memes["sad"] = hero.memes.get("sad", 0.0) + 1

    world.para()
    world.say(
        f"No fix came at once, and the night stayed unkind; "
        f"the prize sat all lonely, with worry behind."
    )
    world.say(
        f"{hero.id} picked up the pieces and stared at the scene, "
        f"while ebony dusk turned the windowpane green."
    )

    world.facts.update(hero=hero, friend=friend, prize=prize, spare=spare)
    return world


def story_intro(world: World, hero: Entity, friend: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.type} who loved little bright things, "
        f"and the {prize.label} was the seventh of all favorite springs."
    )
    world.say(
        f"{friend.id} was a {friend.type} who liked songs and sways, "
        f"and both of them counted their steps in small ways."
    )


SETTINGS = {
    "lantern_room": Place(name="the lantern room", light="dim", echo="soft", affords={"sharing"}),
    "porch": Place(name="the porch", light="gray", echo="gentle", affords={"sharing"}),
    "treehouse": Place(name="the treehouse", light="gold", echo="wooden", affords={"sharing"}),
}

ITEMS = {
    "ebony_token": Item(
        id="ebony_token",
        label="ebony token",
        phrase="seventh ebony token",
        mess="smudge",
        region="hand",
        is_ebony=True,
        fragile=True,
    ),
    "seventh_marble": Item(
        id="seventh_marble",
        label="seventh marble",
        phrase="seventh marble",
        mess="chip",
        region="hand",
        fragile=True,
    ),
    "sharing_spoon": Item(
        id="sharing_spoon",
        label="sharing spoon",
        phrase="sharing spoon",
        mess="spill",
        region="hand",
        plural=False,
    ),
    "bad_charm": Item(
        id="bad_charm",
        label="bad charm",
        phrase="bad charm",
        mess="scratch",
        region="pocket",
        fragile=True,
    ),
}

NAMES = ["Mina", "Noa", "Lio", "Zuri", "Pip", "Tara", "Bela", "Kian"]
FRIEND_NAMES = ["June", "Rae", "Sol", "Milo", "Nia", "Otto"]
TRAITS = ["gentle", "curious", "brave", "hasty", "cheery"]


@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    friend: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world with ebony, seventh, sharing, and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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


def reasonableness_gate(params: StoryParams) -> None:
    if params.item not in ITEMS:
        raise StoryError("Unknown item.")
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.item == "bad_charm":
        raise StoryError("(No story: the bad charm is too abstract for a concrete child story.)")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    item = args.item or rng.choice(["ebony_token", "seventh_marble", "sharing_spoon"])
    place = args.place or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    params = StoryParams(place=place, item=item, name=name, friend=friend, trait=trait)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="boy" if params.name in {"Lio", "Pip", "Kian", "Noa"} else "girl"))
    friend = world.add(Entity(id=params.friend, kind="character", type="boy" if params.friend in {"Milo", "Otto", "Sol"} else "girl"))
    prize_def = ITEMS[params.item]
    prize = world.add(Entity(id="prize", kind="thing", type="thing", label=prize_def.label, owner=hero.id, carried_by=hero.id, plural=prize_def.plural))
    spare = world.add(Entity(id="spare", kind="thing", type="thing", label="tiny spoon", plural=False))
    world.add_item(prize_def)

    story_intro(world, hero, friend, prize)
    world.para()
    tell(world, hero, friend, prize, spare)

    prompts = [
        f"Write a short rhyming story for young children about {params.name}, {params.friend}, and an {prize_def.label}.",
        f"Tell a gentle rhyming tale that includes the words ebony and seventh, with sharing and a twist.",
        f"Write a child-friendly rhyme where a small object is shared, but the ending turns bad.",
    ]

    story_qa_items = [
        QAItem(
            question=f"What did {params.name} want to do with the {prize.label}?",
            answer=f"{params.name} wanted to share the {prize.label} with {params.friend}, but also wanted to keep it safe.",
        ),
        QAItem(
            question=f"What made the story twisty?",
            answer=f"The twist came when the spare little item bumped the {prize.label} and made the moment go wrong.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended badly, with worry and no quick fix, as the {prize.label} sat lonely at the end.",
        ),
    ]

    world_qa_items = [
        QAItem(
            question="What does ebony mean?",
            answer="Ebony is a very dark black color, often used to describe wood or other things that look deep and dark.",
        ),
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let someone else use, hold, or enjoy something too.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise change that makes the story go in a different direction than expected.",
        ),
        QAItem(
            question="What is a bad ending?",
            answer="A bad ending is when things do not turn out nicely, and the problem stays sad or messy at the end.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa_items,
        world_qa=world_qa_items,
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
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  twist_triggered: {world.twist_triggered}")
    lines.append(f"  bad_end: {world.bad_end}")
    return "\n".join(lines)


ASP_RULES = r"""
share_turn(H) :- wants(H), holding(H).
twist(H) :- share_turn(H), spill(H).
bad_end :- twist(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.is_ebony:
            lines.append(asp.fact("ebony", iid))
        if item.label.startswith("seventh"):
            lines.append(asp.fact("seventh", iid))
        if item.plural:
            lines.append(asp.fact("plural", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bad_end/0."))
    asp_bad = bool(asp.atoms(model, "bad_end"))
    py_bad = True
    if asp_bad == py_bad:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def explain_rejection(params: StoryParams) -> str:
    if params.item == "bad_charm":
        return "(No story: the bad charm is too abstract for a child-sized rhyming tale.)"
    return "(No story: the requested choices do not make a simple, concrete rhyming story.)"


CURATED = [
    StoryParams(place="lantern_room", item="ebony_token", name="Mina", friend="June", trait="gentle"),
    StoryParams(place="porch", item="seventh_marble", name="Lio", friend="Rae", trait="curious"),
    StoryParams(place="treehouse", item="sharing_spoon", name="Zuri", friend="Sol", trait="hasty"),
]


def resolve_explicit_or_random(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = resolve_params(args, rng)
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    return params


def generate_many(args: argparse.Namespace, base_seed: int) -> list[StorySample]:
    samples: list[StorySample] = []
    if args.all:
        return [generate(p) for p in CURATED]
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(args.n * 50, 50):
        seed = base_seed + i
        i += 1
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show bad_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show bad_end/0."))
        print("bad_end" if asp.atoms(model, "bad_end") else "no bad_end")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = generate_many(args, base_seed)

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
