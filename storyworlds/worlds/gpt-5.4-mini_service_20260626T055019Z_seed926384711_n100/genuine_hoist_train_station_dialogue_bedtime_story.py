#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/genuine_hoist_train_station_dialogue_bedtime_story.py
==============================================================================================================

A small, standalone storyworld for a bedtime-story style tale set in a train
station, with dialogue, a gentle tension, and a safe, reasonable resolution.

Seed premise:
- A child is waiting in a train station at bedtime.
- The child wants to hoist a bundle onto the luggage shelf.
- The adult worries about a genuine sleepy treasure getting jostled.
- A helpful compromise uses the right gear and a kind helper.

This world keeps the story child-facing, concrete, and state-driven.
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

STATION_NAMES = [
    "the little train station",
    "the quiet station",
    "the old station by the tracks",
]

CHILD_NAMES = ["Mina", "Toby", "Lina", "Arlo", "Nora", "Ezra"]
ADULT_NAMES = ["Mum", "Dad", "Aunt June", "Uncle Ben", "Gran"]
TRAITS = ["sleepy", "gentle", "curious", "patient", "brave"]

ITEMS = {
    "lunchbox": {
        "label": "lunchbox",
        "phrase": "a genuine red lunchbox",
        "type": "lunchbox",
        "region": "hands",
        "plural": False,
    },
    "blanket": {
        "label": "blanket",
        "phrase": "a soft blue blanket",
        "type": "blanket",
        "region": "arms",
        "plural": False,
    },
    "teddy": {
        "label": "teddy bear",
        "phrase": "a genuine teddy bear with a stitched smile",
        "type": "teddy",
        "region": "arms",
        "plural": False,
    },
    "pillow": {
        "label": "pillow",
        "phrase": "a little pillow for the ride",
        "type": "pillow",
        "region": "arms",
        "plural": False,
    },
}

ACTIONS = {
    "hoist_bag": {
        "verb": "hoist the bundle onto the shelf",
        "gerund": "hoisting the bundle onto the shelf",
        "rush": "pull the bundle up quickly",
        "risk": "wobbly",
        "soil": "bumped and dusty",
        "zone": {"arms", "hands"},
        "keyword": "hoist",
        "tags": {"hoist"},
    }
}

GEAR = {
    "helper_step": {
        "label": "a small step stool",
        "covers": {"arms", "hands"},
        "guards": {"wobbly"},
        "prep": "use a small step stool",
        "tail": "used the small step stool",
        "needs_helper": True,
    },
    "two_hand_strap": {
        "label": "a two-handed strap",
        "covers": {"hands", "arms"},
        "guards": {"wobbly"},
        "prep": "use a two-handed strap together",
        "tail": "held the strap with both hands",
        "needs_helper": False,
    },
}

SETTING = {
    "station": {
        "place": "the little train station",
        "affords": {"hoist_bag"},
        "indoor": True,
    }
}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wobble": 0.0, "dust": 0.0, "sleepiness": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "love": 0.0, "conflict": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "aunt", "woman"}
        male = {"boy", "father", "dad", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
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
        import copy as _copy

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.paragraphs = [[]]
        return w

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


def _propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters["wobble"] >= 1 and actor.memes["worry"] >= 1:
            for item in world.worn_items(actor):
                if item.region in world.zone and not item.protective:
                    sig = ("dust", actor.id, item.id)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    item.meters["dust"] += 1
                    out.append(f"{item.label.capitalize()} got bumped and dusty.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def _predict(world: World, actor: Entity, action_key: str, item_id: str) -> dict:
    sim = world.copy()
    action = ACTIONS[action_key]
    sim.zone = set(action["zone"])
    sim.get(actor.id).meters["wobble"] += 1
    _propagate(sim, narrate=False)
    item = sim.get(item_id)
    return {"dusty": item.meters["dust"] >= 1, "wobble": sim.get(actor.id).meters["wobble"]}


def _choose_gear(action_key: str, item: Entity) -> Optional[dict]:
    action = ACTIONS[action_key]
    for gear in GEAR.values():
        if action["risk"] in gear["guards"] and item.region in gear["covers"]:
            return gear
    return None


def tell(name: str, trait: str, adult_name: str, item_key: str, action_key: str) -> World:
    world = World(SETTING["station"]["place"])
    child = world.add(Entity(id=name, kind="character", type="girl" if name in {"Mina", "Lina", "Nora"} else "boy", traits=["little", trait]))
    adult = world.add(Entity(id=adult_name, kind="character", type="mother" if adult_name in {"Mum", "Aunt June", "Gran"} else "father", label=adult_name.lower()))
    item_cfg = ITEMS[item_key]
    item = world.add(Entity(
        id="treasure",
        type=item_cfg["type"],
        label=item_cfg["label"],
        phrase=item_cfg["phrase"],
        owner=child.id,
        caretaker=adult.id,
        region=item_cfg["region"],
        plural=item_cfg["plural"],
    ))
    action = ACTIONS[action_key]

    world.say(
        f"{child.id} sat on the bench at {world.place}, where the lights glowed warm and soft. "
        f"{child.pronoun().capitalize()} was a {trait} little child who felt sleepy but not quite ready for bed."
    )
    world.say(
        f"{child.id} had {item.phrase}, and {child.pronoun('possessive')} {adult.label} smiled and said, "
        f'"That looks genuine, like a treasure for the ride."'
    )

    world.para()
    world.say(
        f"{child.id} peeked up at the high shelf and whispered, "
        f'"Can I {action["verb"]}?"'
    )
    world.say(
        f'"We can, but not in a wild rush," said {adult_name}. '
        f'"This station is sleepy now, and things can get bumped."'
    )

    pred = _predict(world, child, action_key, "treasure")
    if pred["dusty"]:
        world.facts["predicted_risk"] = action["soil"]
        world.say(
            f'"If you {action["verb"]} too fast, {item.label} could get {action["soil"]}," '
            f"said {adult_name}. \"Let's find a kinder way.\""
        )

    child.memes["worry"] += 1
    child.meters["wobble"] += 1
    world.say(
        f"{child.id} frowned and tried to {action['rush']}, but {adult_name} gently held up a hand."
    )
    world.say(
        f'"I want to do it myself," {child.id} said. "I know," said {adult_name}, "and I want your {item.label} to stay genuine and safe."'
    )

    world.para()
    gear = _choose_gear(action_key, item)
    if gear is None:
        raise StoryError("No reasonable gear for this story.")
    world.say(
        f'"How about we {gear["prep"]}?" asked {adult_name}. '
        f'"Then you can hoist it without a tumble."'
    )
    if gear["needs_helper"]:
        world.say(
            f'A kind station helper came over and said, "I can help with the lift."'
        )
    child.memes["joy"] += 1
    child.memes["love"] += 1
    child.memes["conflict"] = 0.0
    child.meters["wobble"] = 0.0
    world.say(
        f'{child.id} nodded, and together they {gear["tail"]}. '
        f"{child.id} lifted the treasure carefully, and it stayed clean and cozy."
    )
    world.say(
        f'"Good night, little station," {child.id} whispered, as the train sighed on the tracks and the bench stayed warm behind {child.pronoun('object')}."'
    )

    world.facts.update(
        child=child,
        adult=adult,
        item=item,
        action=action,
        gear=gear,
        resolved=True,
    )
    return world


def _qa(world: World) -> tuple[list[str], list[QAItem], list[QAItem]]:
    f = world.facts
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    item: Entity = f["item"]
    action = f["action"]
    gear = f["gear"]

    prompts = [
        f'Write a bedtime story set in a train station about a child who wants to use the word "{action["keyword"]}" and keep a genuine treasure safe.',
        f"Tell a gentle dialogue story where {child.id} asks to {action['verb']} and {adult.label} helps with a safer plan.",
        f'Write a short bedtime story about "{action["keyword"]}", a train station, and a kind helper who makes the lift safer.',
    ]

    story_qa = [
        QAItem(
            question=f"Where does {child.id} want to {action['verb']}?",
            answer=f"{child.id} wants to {action['verb']} at {world.place}, where the station feels quiet and sleepy."
        ),
        QAItem(
            question=f"Why does {adult.id} worry about {item.label}?",
            answer=f"{adult.id} worries because if {child.id} tried to {action['verb']} too fast, {item.label} could get {action['soil']}."
        ),
        QAItem(
            question=f"What helped {child.id} hoist the treasure safely?",
            answer=f"They used {gear['label']} and, because this was a helpful lift, a station helper could join in too."
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a train station?",
            answer="A train station is a place where people wait for trains, listen for announcements, and get ready to travel."
        ),
        QAItem(
            question="What does genuine mean?",
            answer="Genuine means real and not fake."
        ),
        QAItem(
            question="What does hoist mean?",
            answer="To hoist something means to lift it up, often with care if it is heavy or high."
        ),
    ]
    return prompts, story_qa, world_qa


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
risk(A,I) :- action(A), item(I), zone(A,R), region(I,R).
needs_help(A,I) :- risk(A,I), gear(G), guards(G,M), action_risk(A,M), covers(G,R), region(I,R).
valid(A,I) :- needs_help(A,I).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("action_risk", aid, a["risk"]))
        for r in sorted(a["zone"]):
            lines.append(asp.fact("zone", aid, r))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("region", iid, item["region"]))
    for gid, gear in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for g in sorted(gear["guards"]):
            lines.append(asp.fact("guards", gid, g))
        for c in sorted(gear["covers"]):
            lines.append(asp.fact("covers", gid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def resolve_params(args: argparse.Namespace, rng: random.Random):
    action = args.action or "hoist_bag"
    item = args.item or rng.choice(list(ITEMS))
    if action == "hoist_bag" and item not in ITEMS:
        raise StoryError("Unknown item.")
    name = args.name or rng.choice(CHILD_NAMES)
    adult = args.adult or rng.choice(ADULT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, adult=adult, trait=trait, item=item, action=action, seed=args.seed)


@dataclass
class StoryParams:
    name: str
    adult: str
    trait: str
    item: str
    action: str
    seed: Optional[int] = None


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.trait, params.adult, params.item, params.action)
    prompts, story_qa, world_qa = _qa(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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


CURATED = [
    StoryParams(name="Mina", adult="Mum", trait="sleepy", item="teddy", action="hoist_bag"),
    StoryParams(name="Toby", adult="Dad", trait="curious", item="blanket", action="hoist_bag"),
    StoryParams(name="Lina", adult="Aunt June", trait="gentle", item="lunchbox", action="hoist_bag"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime-story train station world with dialogue and a safe hoist.")
    ap.add_argument("--name")
    ap.add_argument("--adult")
    ap.add_argument("--trait")
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--action", choices=ACTIONS)
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


def verify_asp() -> int:
    import asp

    py = {("hoist_bag", "teddy"), ("hoist_bag", "blanket"), ("hoist_bag", "lunchbox"), ("hoist_bag", "pillow")}
    cl = set(asp_valid())
    expected = {("hoist_bag", item) for item in ITEMS}
    if cl == expected:
        print(f"OK: ASP matches Python gate ({len(cl)} valid pairs).")
        return 0
    print("MISMATCH:")
    print("python:", sorted(expected))
    print("clingo:", sorted(cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(verify_asp())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} valid story pairs")
        for a, i in vals:
            print(a, i)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
