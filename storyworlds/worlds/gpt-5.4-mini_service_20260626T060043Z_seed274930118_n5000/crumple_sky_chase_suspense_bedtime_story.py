#!/usr/bin/env python3
"""
Storyworld: crumple_sky_chase_suspense_bedtime_story
=====================================================

A small bedtime-story world about a sleepy child, a crumpled sky picture,
and a gentle chase that turns suspense into a calm ending.

Premise:
- A child loves a paper star map of the sky.
- The map gets crumpled, which hides a tiny moon drawing.
- A lost little glow slips away, and the child must chase it before bedtime.

Resolution:
- The child follows soft clues through the room.
- A parent helps by holding the lamp and smoothing the map.
- The glow is found, the sky picture is fixed, and bedtime feels safe again.

This world models:
- physical meters: crumple, glow, tiredness, neatness, distance
- emotional memes: worry, suspense, relief, love, calm
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"crumple": 0.0, "glow": 0.0, "distance": 0.0, "neatness": 0.0, "tiredness": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"worry": 0.0, "suspense": 0.0, "relief": 0.0, "love": 0.0, "calm": 0.0})

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
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    label: str
    phrase: str
    type: str
    helps: set[str]
    plural: bool = False


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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_crumple(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    map_ = world.get("sky_map")
    lamp = world.get("lamp")
    if child.meters["crumple"] < THRESHOLD:
        return out
    sig = ("crumple",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    map_.meters["crumple"] += 1
    map_.meters["neatness"] -= 1
    child.memes["worry"] += 1
    child.memes["suspense"] += 1
    out.append("The sky map folded into a wrinkly ball, and the tiny moon drawing vanished in the folds.")
    if lamp.meters["glow"] < THRESHOLD:
        child.memes["suspense"] += 1
        out.append("The lamp light looked smaller, so the room felt extra hush-quiet.")
    return out


def _r_chase(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    glow = world.get("glow")
    if child.memes["worry"] < THRESHOLD:
        return out
    sig = ("chase",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["distance"] += 1
    glow.meters["distance"] += 1
    out.append("The child tiptoed after the little glow, chasing it from the pillow to the curtain and back again.")
    return out


def _r_find(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    glow = world.get("glow")
    parent = world.get("parent")
    map_ = world.get("sky_map")
    if child.meters["distance"] < THRESHOLD:
        return out
    sig = ("find",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    glow.meters["glow"] += 1
    map_.meters["neatness"] += 1
    child.memes["relief"] += 1
    child.memes["calm"] += 1
    child.memes["suspense"] = 0.0
    parent.memes["love"] += 1
    out.append("With a soft sigh, the glow stopped beside the bed, where the parent could scoop it up and smile.")
    return out


CAUSAL_RULES = [
    _r_crumple,
    _r_chase,
    _r_find,
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


SETTINGS = {
    "bedroom": Setting(place="the bedroom", affords={"crumple", "chase"}),
    "nursery": Setting(place="the nursery", affords={"crumple", "chase"}),
    "hallway": Setting(place="the hallway", affords={"chase"}),
}

ITEMS = {
    "star_map": Item(
        label="sky map",
        phrase="a paper sky map with a tiny moon",
        type="map",
        helps={"calm"},
    ),
    "blanket": Item(
        label="blanket",
        phrase="a soft blanket with stitched stars",
        type="blanket",
        helps={"calm"},
        plural=False,
    ),
    "lamp": Item(
        label="lamp",
        phrase="a small lamp with warm light",
        type="lamp",
        helps={"glow"},
    ),
}

GIRL_NAMES = ["Luna", "Mira", "Nora", "Ivy", "Maya", "Zoe"]
BOY_NAMES = ["Finn", "Leo", "Owen", "Eli", "Noah", "Theo"]
TRAITS = ["gentle", "curious", "sleepy", "brave", "quiet"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about a crumpled sky map and a gentle chase.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS))
    item = args.item or "star_map"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    if place not in SETTINGS[item if False else place]:
        pass
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    if "crumple" not in SETTINGS[place].affords and item == "star_map":
        raise StoryError("(No story: this place does not support the crumpled-sky-map bedtime scene.)")
    return StoryParams(place=place, item=item, name=name, gender=gender, parent=parent)


def _do_crumple(world: World, child: Entity, item: Entity) -> None:
    if world.setting.place not in {"the bedroom", "the nursery"}:
        raise StoryError("This bedtime crumple scene needs a bedroom or nursery.")
    child.meters["crumple"] += 1
    child.meters["tiredness"] += 0.5
    propagate(world)


def _do_chase(world: World, child: Entity) -> None:
    child.memes["worry"] += 1
    child.memes["suspense"] += 1
    propagate(world)


def tell(setting: Setting, item_cfg: Item, name: str, gender: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=gender, label=name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=parent_type))
    sky_map = world.add(Entity(id="sky_map", label=item_cfg.label, phrase=item_cfg.phrase))
    lamp = world.add(Entity(id="lamp", label="lamp", phrase="a small lamp with warm light"))
    glow = world.add(Entity(id="glow", label="little glow", phrase="a little wandering glow"))
    world.facts.update(child=child, parent=parent, sky_map=sky_map, lamp=lamp, glow=glow, item=item_cfg, setting=setting)

    world.say(f"{name} was a little {gender} who loved bedtime stories about the sky.")
    world.say(f"On the night table sat {item_cfg.phrase}, and {name} liked to trace the tiny moon with a sleepy finger.")
    world.para()
    world.say(f"One night, {name} reached for the sky map too fast and crumpled it into a soft little ball.")
    _do_crumple(world, child, sky_map)
    world.say(f"The room grew hushed, and {name} worried that the moon drawing had gone missing.")
    world.para()
    world.say(f"Then {name} saw a small glow slip away across the blanket, as if it had heard a secret and wanted to hide.")
    _do_chase(world, child)
    world.say(f"{name} chased the glow past the pillow and the curtain while {parent_type} held the lamp steady.")
    world.para()
    world.say(f"At last, {name} found the glow by the bed and helped smooth the sky map flat again.")
    propagate(world)
    world.say(f"The tiny moon came back into view, and {name} curled up beside {parent_type} with a calm, warm smile.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    item = f["item"]
    return [
        'Write a bedtime story for a small child about a crumpled sky map and a soft chase.',
        f"Tell a gentle suspense story where {child.label} crumples {item.label}, chases a little glow, and feels calm again.",
        'Write a child-facing story with the words "crumple", "sky", and "chase" that ends peacefully at bedtime.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    sky_map = f["sky_map"]
    glow = f["glow"]
    return [
        QAItem(
            question=f"What did {child.label} crumple in the story?",
            answer=f"{child.label} crumpled {sky_map.phrase}, the paper sky map with the tiny moon.",
        ),
        QAItem(
            question=f"Why did {child.label} chase the little glow?",
            answer=f"{child.label} chased the little glow because the crumpled sky map made the moon drawing feel lost and the room felt suspenseful.",
        ),
        QAItem(
            question=f"Who helped keep things calm while {child.label} chased the glow?",
            answer=f"{parent.label} held the lamp steady while {child.label} chased the glow, and that helped the room feel safe.",
        ),
        QAItem(
            question=f"What happened after the glow was found?",
            answer=f"After the glow was found, {child.label} smoothed the sky map flat again and the bedtime feeling turned calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is the sky?",
            answer="The sky is the wide space above us where you can see clouds, the sun, the moon, and stars.",
        ),
        QAItem(
            question="What does crumple mean?",
            answer="To crumple something means to bend and crush it into a wrinkly shape.",
        ),
        QAItem(
            question="What is a chase?",
            answer="A chase is when someone moves quickly after something that is going away.",
        ),
        QAItem(
            question="Why do bedtime stories feel soothing?",
            answer="Bedtime stories feel soothing because they are calm, gentle, and help children settle down for sleep.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: {e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="bedroom", item="star_map", name="Luna", gender="girl", parent="mother"),
    StoryParams(place="nursery", item="star_map", name="Noah", gender="boy", parent="father"),
]


ASP_RULES = r"""
% A sky map can be crumpled in a bedtime setting.
can_crumple(P) :- place(P), affords(P, crumple).

% The story has suspense when the map is crumpled and the child worries.
suspense(P) :- place(P), can_crumple(P), item(star_map).

% The chase is valid when the glow is present and the parent helps with light.
can_chase(P) :- place(P), affords(P, chase), glow_present, lamp_present.

% Resolution occurs when the map is smoothed and calm returns.
resolved(P) :- can_chase(P), map_fixed, calm_returns.

#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for h in sorted(item.helps):
            lines.append(asp.fact("helps", iid, h))
    lines.append(asp.fact("glow_present"))
    lines.append(asp.fact("lamp_present"))
    lines.append(asp.fact("map_fixed"))
    lines.append(asp.fact("calm_returns"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "crumple" in setting.affords and "chase" in setting.affords:
            combos.append((place, "star_map"))
    return combos


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set((p, i) for p, i in valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("ASP:", sorted(asp_set))
    print("PY :", sorted(py_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ITEMS[params.item], params.name, params.gender, params.parent)
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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.asp:
        print(f"{len(valid_combos())} valid bedtime combos:")
        for place, item in valid_combos():
            print(f"  {place} / {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
