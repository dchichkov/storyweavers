#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/continuity_gigantic_envelope_crowded_market_happy_ending.py
===========================================================================================

A small slice-of-life storyworld about a crowded market, a gigantic envelope,
and a curious child who follows a twist to a happy ending.

Premise:
- In a crowded market, a child notices a gigantic envelope with a careful note
  about continuity and wonders what it means.
- Curiosity pulls the child toward the envelope, but the market crowd creates
  small tension: bumping, confusion, and a near-loss.
- The twist reveals the envelope is a community parcel meant to reconnect a
  letter with its owner.
- The happy ending proves continuity by returning the envelope and leaving the
  child with a small, bright sense of wonder.

This file is self-contained and follows the storyworld contract:
- typed entities with meters and memes
- Python reasonableness gate plus inline ASP twin
- prompts, story QA, world QA from simulated state
- build_parser / resolve_params / generate / emit / main
- --verify exercises normal generation and compares ASP/Python parity
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ivy", "Sana", "Mina"]
BOY_NAMES = ["Owen", "Theo", "Leo", "Bram", "Ravi", "Noah"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    crowd: str
    sounds: str
    color: str


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    size: str
    weight: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    reveal: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_gender: str
    parent_type: str
    item: str
    twist: str
    seed: Optional[int] = None


SETTINGS = {
    "crowded_market": Setting(
        id="crowded_market",
        place="a crowded market",
        crowd="busy shoppers",
        sounds="bells, wheels, and cheerful calls",
        color="bright awnings",
    )
}

ITEMS = {
    "gigantic_envelope": Item(
        id="gigantic_envelope",
        label="gigantic envelope",
        phrase="a gigantic envelope with a red string tie",
        size="gigantic",
        weight="light",
        tags={"gigantic", "envelope", "continuity"},
    ),
}

TWISTS = {
    "parcel_mistake": Twist(
        id="parcel_mistake",
        reveal="the giant envelope was not for a store at all",
        effect="it belonged to a neighbor who had been waiting for it all morning",
        tags={"twist", "continuity"},
    ),
}

CURATED = [
    StoryParams(
        setting="crowded_market",
        child_name="Maya",
        child_gender="girl",
        parent_type="mother",
        item="gigantic_envelope",
        twist="parcel_mistake",
        seed=7,
    ),
    StoryParams(
        setting="crowded_market",
        child_name="Owen",
        child_gender="boy",
        parent_type="father",
        item="gigantic_envelope",
        twist="parcel_mistake",
        seed=8,
    ),
]


class Reasonable:
    def __init__(self, item: Item, twist: Twist) -> None:
        self.item = item
        self.twist = twist


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for iid, item in ITEMS.items():
            for tid, tw in TWISTS.items():
                if "gigantic" in item.tags and "envelope" in item.tags and "continuity" in item.tags:
                    combos.append((sid, iid, tid))
    return combos


def _story_items() -> tuple[Item, Twist]:
    return ITEMS["gigantic_envelope"], TWISTS["parcel_mistake"]


def _setup(world: World, child: Entity, parent: Entity, item: Item) -> None:
    child.memes["curiosity"] += 1
    child.memes["delight"] += 0.5
    world.say(
        f"In {world.setting.place}, {child.id} walked beside {parent.label_word} under "
        f"{world.setting.color}. {world.setting.sounds} drifted through the air, and "
        f"the whole market felt alive."
    )
    world.say(
        f"Near a stall of folded cloth sat {item.phrase}. It was so big that it looked "
        f"like it could hold a tiny story all by itself."
    )
    world.say(
        f'{child.id} blinked at it. "Continuity," {child.pronoun()} said softly, '
        f'like {child.pronoun("possessive")} mouth wanted to test the word.'
    )


def _curiosity(world: World, child: Entity, item: Item) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} leaned closer, because curiosity made {child.pronoun('object')} want "
        f"to know what was inside the envelope and who it was for."
    )
    world.say(
        f"{child.id} reached out, then paused when a shopper brushed past and the crowd "
        f"shuffled around {child.pronoun('object')}."
    )


def _twist(world: World, child: Entity, parent: Entity, item: Item, twist: Twist) -> None:
    child.memes["surprise"] += 1
    world.say(
        f"Then the twist arrived: a stallkeeper laughed kindly and explained that "
        f"{twist.reveal}. {twist.effect}."
    )
    world.say(
        f"The gigantic envelope held a letter, a ribbon, and a note with an address "
        f"written in careful looping letters. It was a parcel for someone nearby, not "
        f"junk to be lost in the crowd."
    )


def _return(world: World, child: Entity, parent: Entity, item: Item) -> None:
    child.memes["care"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{child.id} carried the envelope with both hands while {parent.id} walked close "
        f"beside {child.pronoun('object')}, making sure the busy feet around them did not "
        f"knock it away."
    )
    world.say(
        f'Together they found the waiting neighbor at the next stall. "I was hoping '
        f"this would come back," the neighbor said, and the whole face brightened at once."
    )
    world.say(
        f"{child.id} grinned, because the right thing had found its right person again."
    )


def _ending(world: World, child: Entity, parent: Entity) -> None:
    child.memes["contentment"] += 1
    world.say(
        f"When they left the market, the crowd was still noisy, but now it felt gentle "
        f"instead of confusing. {child.id} held {parent.pronoun('possessive')} hand and "
        f"looked back once at the stalls, smiling at the little bit of continuity they had "
        f"helped keep alive."
    )


def tell(setting: Setting, child_name: str, child_gender: str, parent_type: str,
         item: Item, twist: Twist) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent", role="parent"))
    world.add(Entity(id=item.id, type="thing", label=item.label, role="object"))
    world.facts.update(item=item, twist=twist, child=child, parent=parent, setting=setting)

    _setup(world, child, parent, item)
    world.para()
    _curiosity(world, child, item)
    world.para()
    _twist(world, child, parent, item, twist)
    world.para()
    _return(world, child, parent, item)
    world.para()
    _ending(world, child, parent)
    world.facts["outcome"] = "happy"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item: Item = f["item"]
    return [
        f'Write a slice-of-life story set in {f["setting"].place} that includes the words '
        f'"continuity" and "{item.label}".',
        f"Tell a gentle story about a child named {f['child'].id} in a crowded market who "
        f"becomes curious about {item.phrase}, then discovers a small twist and a happy ending.",
        f"Write a warm market story where curiosity leads to a useful surprise and the word "
        f'"continuity" matters to the ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    item: Item = f["item"]
    twist: Twist = f["twist"]
    qa = [
        QAItem(
            question="What was the child curious about?",
            answer=(
                f"{child.id} was curious about the gigantic envelope and wanted to know what "
                f"was inside it. The crowded market made the mystery feel even bigger."
            ),
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=(
                f"The twist was that the envelope was a parcel for a neighbor, not something "
                f"to be left behind. That surprise turned the search into a good deed."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended happily when the envelope reached the right person and the market "
                f"felt calm again. {child.id} left with a bright feeling of continuity, "
                f"because the parcel and the person were connected at last."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an envelope?",
            answer="An envelope is a paper holder used for letters and small papers.",
        ),
        QAItem(
            question="Why can a crowded market feel confusing?",
            answer="A crowded market has many people, sounds, and moving parts, so it can be easy to get distracted.",
        ),
        QAItem(
            question="What does continuity mean?",
            answer="Continuity means a smooth connection that stays unbroken from one part to the next.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        parts = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.role:
            parts.append(f"role={e.role}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
item(gigantic_envelope).
twist(parcel_mistake).
setting(crowded_market).

contains(gigantic_envelope, gigantic).
contains(gigantic_envelope, envelope).
contains(gigantic_envelope, continuity).

valid(S, I, T) :- setting(S), item(I), twist(T),
                  contains(I, gigantic), contains(I, envelope), contains(I, continuity).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "crowded_market"), asp.fact("item", "gigantic_envelope"), asp.fact("twist", "parcel_mistake")]
    for tag in ("gigantic", "envelope", "continuity"):
        lines.append(asp.fact("contains", "gigantic_envelope", tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos")
        print("python-only:", sorted(py - cl))
        print("asp-only:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, child_name=None, child_gender=None, parent_type=None, item=None, twist=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld in a crowded market.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    setting = args.setting or "crowded_market"
    item = args.item or "gigantic_envelope"
    twist = args.twist or "parcel_mistake"
    if setting != "crowded_market" or item != "gigantic_envelope" or twist != "parcel_mistake":
        raise StoryError("This world only tells a crowded-market story with the gigantic envelope twist.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, child_name=name, child_gender=gender, parent_type=parent, item=item, twist=twist)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.item not in ITEMS or params.twist not in TWISTS:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], params.child_name, params.child_gender, params.parent_type, ITEMS[params.item], TWISTS[params.twist])
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
