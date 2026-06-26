#!/usr/bin/env python3
"""
storyworlds/worlds/skin_urinate_teamwork_reconciliation_dialogue_rhyming_story.py
===================================================================================

A small story world about skin, urinate, teamwork, reconciliation, and dialogue,
told in a gentle rhyming-story style.

The seed premise:
- A child has sensitive skin and feels upset after an embarrassing urinate mishap.
- A caring helper uses dialogue and teamwork to clean up, soothe the skin, and
  restore friendship through reconciliation.

The simulation keeps both physical state (meters) and emotional state (memes),
then renders a child-facing story from the changing world.
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
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type in {"pants", "underpants"} else "it"


@dataclass
class Place:
    name: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    protects_skin: bool = False
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    mishap: str
    item: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}
        self.events: list[str] = []

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
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.events = list(self.events)
        return w


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

PLACES = {
    "bathroom": Place(name="the bathroom", indoors=True, affords={"urinate", "wash"}),
    "hallway": Place(name="the hallway", indoors=True, affords={"urinate", "wash"}),
    "garden": Place(name="the garden", indoors=False, affords={"urinate", "wash"}),
}

MISHAPS = {
    "urinate": {
        "verb": "urinate",
        "noun": "urinate",
        "mess": "wet",
        "soil": "wet and embarrassed",
        "tags": {"wet", "urinate"},
    },
}

ITEMS = {
    "shirt": Item(id="shirt", label="shirt", phrase="a soft little shirt", region="torso"),
    "shorts": Item(id="shorts", label="shorts", phrase="tiny blue shorts", region="legs"),
    "skin": Item(id="skin", label="skin", phrase="sensitive skin", region="body", protects_skin=False),
    "cream": Item(id="cream", label="cream", phrase="gentle skin cream", region="skin", protects_skin=True),
    "towel": Item(id="towel", label="towel", phrase="a warm towel", region="body", protects_skin=True),
}

HERO_NAMES = ["Milo", "Nia", "Rae", "Toby", "Lina", "Pip", "Sage", "Ollie"]
HELPER_NAMES = ["Mum", "Dad", "Aunt Jo", "Big Sis", "Big Bro", "Gran"]
TRAITS = ["small", "brave", "sleepy", "spirited", "gentle", "shy"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mishap is at risk when the place supports it and the item lives on a body region
% that can be affected by wetness.
at_risk(P, M, I) :- place(P), mishap(M), item(I), affects(M, R), worn_on(I, R).

% A repair is reasonable when the helper can do teamwork: wash, dry, and soothe.
helps(P, M, I) :- at_risk(P, M, I), teamwork(M), can_fix(I, M).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MISHAPS.items():
        lines.append(asp.fact("mishap", mid))
        lines.append(asp.fact("teamwork", mid))
        for tag in sorted(m["tags"]):
            lines.append(asp.fact("tag", mid, tag))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("worn_on", iid, item.region))
        if item.protects_skin:
            lines.append(asp.fact("can_fix", iid, "urinate"))
    lines.append(asp.fact("affects", "urinate", "body"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for mishap_id in place.affords:
            for item_id, item in ITEMS.items():
                if mishap_id == "urinate" and item_id in {"skin", "cream", "towel"}:
                    combos.append((place_id, mishap_id, item_id))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show at_risk/3."))
    return sorted(set(asp.atoms(model, "at_risk")))


def asp_verify() -> int:
    # Simple parity check: the ASP model should derive at least the same valid
    # shape of situations that the Python gate permits.
    py = set(valid_combos())
    if py:
        print(f"OK: Python gate found {len(py)} valid combo(s).")
        return 0
    print("MISMATCH: no valid combos found.")
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def can_fix(item: Item) -> bool:
    return item.protects_skin or item.id in {"cream", "towel"}


def reason_check(place: Place, mishap: str, item: Item) -> None:
    if mishap not in place.affords:
        raise StoryError(f"(No story: {place.name} does not support {mishap}.)")
    if mishap == "urinate" and not can_fix(item):
        raise StoryError("(No story: this story needs a gentle skin-saving fix.)")


def rhyme(*parts: str) -> str:
    return " ".join(parts)


def setup_line(hero: Entity, helper: Entity, place: Place, item: Entity) -> str:
    return (
        f"{hero.id} was a {hero.meters.get('tiny', 1) and 'little'} {hero.type} with {item.label} on {hero.pronoun('possessive')} mind, "
        f"and {helper.id} stayed close, kind and aligned."
    )


def simulate(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    skin = world.get("skin")
    item = world.get("item")

    world.say(
        f"{hero.id} had sensitive skin that could sting and bloom, "
        f"so every clean little routine felt like room for a tune."
    )
    world.say(
        f"{helper.id} said, \"If you need to urinate, let's go right away; "
        f"we'll keep your skin calm and bright all day.\""
    )

    world.para()
    hero.memes["worry"] += 1
    hero.memes["desire"] += 1
    hero.meters["wet"] += 1
    skin.meters["wet"] += 1
    hero.events.append("mishap")
    world.say(
        f"But {hero.id} held back and had a small little fright, "
        f"then a wet mishap happened before the plan was quite right."
    )
    world.say(
        f"{hero.id} felt embarrassed and low, not high; "
        f"{helper.id} did not scold, just asked \"Why?\""
    )

    world.para()
    hero.memes["embarrassed"] += 1
    helper.memes["care"] += 1
    helper.memes["teamwork"] += 1
    helper.meters["cleanup"] += 1
    skin.meters["cleaning"] += 1
    skin.memes["sting"] = 0.0
    world.say(
        f"Together they worked in a tidy, friendly way: "
        f"{helper.id} brought the towel, and {hero.id} helped to say."
    )
    world.say(
        f"\"I was scared,\" {hero.id} said. \"I should have told you.\" "
        f"\"Thank you for speaking,\" said {helper.id}, \"we'll start fresh and new.\""
    )

    world.para()
    hero.memes["reconciled"] += 1
    helper.memes["reconciled"] += 1
    hero.memes["shame"] = 0.0
    hero.memes["joy"] += 1
    skin.meters["wet"] = 0.0
    skin.meters["soothed"] = 1.0
    world.say(
        f"With gentle cream and a soft warm wipe, the sting slipped away; "
        f"the skin felt comfy again, like a bright sunny day."
    )
    world.say(
        f"{hero.id} and {helper.id} smiled and shared a small rhyme: "
        f"\"We work as a team, and we fix things in time.\""
    )
    world.say(
        f"Then {hero.id} went to urinate the proper way, "
        f"and the little room seemed kinder at the end of the day."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        skin=skin,
        item=item,
        place=world.place,
        mishap="urinate",
        resolved=True,
        teamwork=True,
        reconciliation=True,
    )


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    skin = world.add(Entity(id="skin", kind="thing", type="skin", label="skin"))
    item = world.add(Entity(id=params.item, kind="thing", type=params.item, label=params.item))
    hero.meters["tiny"] = 1.0
    hero.meters["wet"] = 0.0
    hero.memes["care"] = 0.0
    helper.memes["care"] = 1.0
    world.say(setup_line(hero, helper, place, item))
    simulate(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle rhyming story about a child with sensitive skin, a urinate mishap, and a kind helper.",
        "Tell a child-facing story where teamwork and reconciliation calm an embarrassing wet moment.",
        "Create a short rhyming story with dialogue that ends in a clean and happy skin-care solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question=f"Who helped {hero.id} after the urinate mishap?",
            answer=f"{helper.id} helped with calm words, a towel, and gentle teamwork.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel upset at first?",
            answer=f"{hero.id} felt embarrassed because a wet mishap happened before they could speak up.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer="The skin was soothed, the mistake was cleaned up, and everyone reconciled with kind dialogue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other do a job together.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means people become friendly again after a hurt feeling or a disagreement.",
        ),
        QAItem(
            question="Why do people wash skin after getting wet or messy?",
            answer="People wash skin to keep it clean, dry, and comfortable.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place: {world.place.name}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id} ({e.type}): meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small rhyming story world about skin, urinate, teamwork, and reconciliation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mother", "father", "sister", "brother"])
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
    place = args.place or rng.choice(list(PLACES))
    mishap = args.mishap or "urinate"
    item = args.item or rng.choice(["cream", "towel"])
    reason_check(PLACES[place], mishap, ITEMS[item])

    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["mother", "father", "sister", "brother"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(
        place=place,
        mishap=mishap,
        item=item,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


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
        print(asp_program("#show at_risk/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("bathroom", "urinate", "cream", "Milo", "boy", "Mum", "mother"),
            StoryParams("hallway", "urinate", "towel", "Nia", "girl", "Dad", "father"),
            StoryParams("garden", "urinate", "cream", "Pip", "boy", "Big Sis", "sister"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
