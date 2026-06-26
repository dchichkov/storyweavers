#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/stimulate_pose_shrub_friendship_slice_of_life.py
============================================================================================

A small slice-of-life story world about friendship, a gentle garden task, and
the kind of tiny social turn that can change an ordinary afternoon.

Seed tale used to shape the world:
---
Two friends, Mina and Jun, spent a quiet afternoon near a small shrub by the
courtyard. Mina wanted to pose for a picture, but the shrub looked dull and
droopy after a dry week. Jun suggested they stimulate it with water, a little
care, and some cheerful talk first. They watered the roots, straightened the
soil, and waited together. Soon the shrub looked brighter, Mina posed beside
it, and both friends felt proud of what they had done together.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    present: bool = True

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    outdoors: bool = True
    has_shrub: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    mood: str
    effect: str
    need_shrub: bool = False
    need_friend: bool = False
    keyword: str = ""


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    type: str
    helpful_for: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _narrate_join(world: World, a: Entity, b: Entity) -> None:
    a.memes["warmth"] = a.memes.get("warmth", 0) + 1
    b.memes["warmth"] = b.memes.get("warmth", 0) + 1
    a.memes["trust"] = a.memes.get("trust", 0) + 1
    b.memes["trust"] = b.memes.get("trust", 0) + 1
    world.say(f"{a.id} and {b.id} had the easy kind of friendship that made quiet afternoons feel bright.")


def _narrate_shrub(world: World, shrub: Entity) -> None:
    feel = "droopy" if shrub.meters.get("dry", 0) >= THRESHOLD else "fresh"
    world.say(f"Near the path, a little {shrub.label} looked {feel} and still waited for some care.")


def _do_stimulate(world: World, actor: Entity, helper: Entity, shrub: Entity, prop: Optional[Entity]) -> None:
    sig = ("stimulate", actor.id, helper.id, shrub.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    actor.meters["care"] = actor.meters.get("care", 0) + 1
    helper.meters["care"] = helper.meters.get("care", 0) + 1
    shrub.meters["dry"] = max(0.0, shrub.meters.get("dry", 0) - 1.0)
    shrub.meters["fresh"] = shrub.meters.get("fresh", 0) + 1.0
    if prop is not None and prop.id == "watering_can":
        shrub.meters["watered"] = shrub.meters.get("watered", 0) + 1.0


def _do_pose(world: World, actor: Entity, helper: Entity, shrub: Entity) -> None:
    sig = ("pose", actor.id, helper.id, shrub.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    actor.memes["joy"] = actor.memes.get("joy", 0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1
    actor.memes["pride"] = actor.memes.get("pride", 0) + 1
    helper.memes["pride"] = helper.memes.get("pride", 0) + 1


def render_shrub_mood(shrub: Entity) -> str:
    if shrub.meters.get("fresh", 0) >= THRESHOLD:
        return "brighter"
    if shrub.meters.get("dry", 0) >= THRESHOLD:
        return "less droopy"
    return "quiet and green"


def tell(world: World) -> World:
    hero = world.add(Entity(id="Mina", kind="character", type="girl", traits=["quiet", "kind"]))
    friend = world.add(Entity(id="Jun", kind="character", type="boy", traits=["thoughtful", "gentle"]))
    shrub = world.add(Entity(
        id="shrub",
        kind="thing",
        type="shrub",
        label="shrub",
        phrase="a small shrub by the courtyard wall",
        meters={"dry": 1.0, "fresh": 0.0},
    ))

    prop = world.add(Entity(
        id="watering_can",
        kind="thing",
        type="watering can",
        label="watering can",
        phrase="a blue watering can",
    ))
    camera = world.add(Entity(
        id="camera",
        kind="thing",
        type="camera",
        label="camera",
        phrase="a small camera with a silver strap",
    ))

    world.say(f"One calm afternoon, {hero.id} and {friend.id} met in {world.setting.place}.")
    _narrate_join(world, hero, friend)
    _narrate_shrub(world, shrub)

    world.para()
    world.say(
        f"{hero.id} wanted to pose beside the shrub for a picture, but {friend.id} noticed it looked tired from the dry week."
    )
    world.say(
        f'"Let’s stimulate it a little first," {friend.id} said, lifting the {prop.label} with a smile.'
    )

    _do_stimulate(world, hero, friend, shrub, prop)
    world.say(
        f"They watered the roots, smoothed the soil, and stayed nearby until the {shrub.label} looked {render_shrub_mood(shrub)}."
    )

    world.para()
    _do_pose(world, hero, friend, shrub)
    world.say(
        f"Then {hero.id} stood by the {shrub.label} and posed while {friend.id} held the camera steady."
    )
    world.say(
        f"The picture came out lovely, and the little {shrub.label} seemed to shine in the background."
    )
    world.say(
        f"{hero.id} grinned at {friend.id}; helping the shrub had made the pose feel even better."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        shrub=shrub,
        prop=prop,
        camera=camera,
        setting=world.setting,
    )
    return world


SETTINGS = {
    "courtyard": Setting(place="the apartment courtyard", outdoors=True, has_shrub=True, affords={"pose", "stimulate"}),
    "backyard": Setting(place="the backyard", outdoors=True, has_shrub=True, affords={"pose", "stimulate"}),
    "porch": Setting(place="the front porch", outdoors=True, has_shrub=True, affords={"pose", "stimulate"}),
}

ACTIONS = {
    "pose": Action(
        id="pose",
        verb="pose for a picture",
        gerund="posing for a picture",
        mood="proud",
        effect="joy",
        need_shrub=True,
        need_friend=True,
        keyword="pose",
    ),
    "stimulate": Action(
        id="stimulate",
        verb="stimulate the shrub",
        gerund="stimulating the shrub",
        mood="careful",
        effect="care",
        need_shrub=True,
        need_friend=True,
        keyword="stimulate",
    ),
}

PROPS = {
    "watering_can": Prop(
        id="watering_can",
        label="watering can",
        phrase="a blue watering can",
        type="watering can",
        helpful_for={"stimulate"},
    ),
    "camera": Prop(
        id="camera",
        label="camera",
        phrase="a small camera",
        type="camera",
        helpful_for={"pose"},
    ),
}

NAMES = ["Mina", "Jun", "Iris", "Nico", "Leah", "Owen", "Rita", "Eli"]
TRAITS = ["kind", "thoughtful", "gentle", "quiet", "patient", "cheerful"]


@dataclass
class StoryParams:
    place: str
    action: str
    name1: str
    name2: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for aid, action in ACTIONS.items():
            if setting.has_shrub and aid in setting.affords:
                combos.append((place, aid))
    return combos


def explain_rejection(place: str, action: str) -> str:
    return f"(No story: {action} doesn't fit naturally in {place} for this small friendship scene.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life friendship story world with a shrub, a pose, and a gentle turn.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
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
    if args.action:
        combos = [c for c in combos if c[1] == args.action]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action = rng.choice(sorted(combos))
    name1 = args.name1 or rng.choice(NAMES)
    name2 = args.name2 or rng.choice([n for n in NAMES if n != name1])
    return StoryParams(place=place, action=action, name1=name1, name2=name2)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story about friendship, a {f["shrub"].label}, and the word "stimulate".',
        f"Tell a gentle story where {f['hero'].id} and {f['friend'].id} spend a calm afternoon in {f['setting'].place}.",
        f'Write a child-friendly story in which friends first care for a shrub and then pose for a picture.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, shrub = f["hero"], f["friend"], f["shrub"]
    return [
        QAItem(
            question=f"Who were the friends in the story?",
            answer=f"The friends were {hero.id} and {friend.id}. They spent a calm afternoon together and helped each other.",
        ),
        QAItem(
            question=f"What did they do for the shrub before posing?",
            answer=f"They stimulated the shrub by watering the roots and smoothing the soil so it looked better.",
        ),
        QAItem(
            question=f"Why did the picture feel nice at the end?",
            answer=f"It felt nice because the friends cared for the shrub first, and then {hero.id} posed beside it while {friend.id} held the camera.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to stimulate a plant?",
            answer="In a garden, to stimulate a plant usually means to give it care that helps it grow or perk up, like water, light, or gentle tending.",
        ),
        QAItem(
            question="What is a shrub?",
            answer="A shrub is a small woody plant that grows lower than a tree and often has many branches close to the ground.",
        ),
        QAItem(
            question="What is posing for a picture?",
            answer="Posing for a picture means standing or sitting in a chosen way so someone can take a photograph.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
friend(A,B) :- paired(A,B).
needs_care(S) :- shrub(S), dry(S), dry_level(S, N), N >= 1.
good_pose(A,S) :- pose(A), shrub(S), fresh(S), paired(A,_).
valid(P,Act) :- setting(P), affords(P,Act), pairable(Act).
pairable(pose).
pairable(stimulate).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.has_shrub:
            lines.append(asp.fact("has_shrub", pid))
        for act in sorted(s.affords):
            lines.append(asp.fact("affords", pid, act))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name1, kind="character", type="girl", traits=["kind", "quiet"]))
    friend = world.add(Entity(id=params.name2, kind="character", type="boy", traits=["gentle", "thoughtful"]))
    shrub = world.add(Entity(id="shrub", kind="thing", type="shrub", label="shrub", phrase="a small shrub by the courtyard wall", meters={"dry": 1.0, "fresh": 0.0}))
    prop = world.add(Entity(id="watering_can", kind="thing", type="watering can", label="watering can"))
    camera = world.add(Entity(id="camera", kind="thing", type="camera", label="camera"))

    tell(world)
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


CURATED = [
    StoryParams(place="courtyard", action="stimulate", name1="Mina", name2="Jun"),
    StoryParams(place="backyard", action="pose", name1="Iris", name2="Owen"),
    StoryParams(place="porch", action="stimulate", name1="Leah", name2="Eli"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, action in combos:
            print(f"  {place:10} {action}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name1} and {p.name2} at {p.place} ({p.action})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
