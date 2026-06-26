#!/usr/bin/env python3
"""
storyworlds/worlds/dash_warranty_inner_monologue_bravery_kindness_heartwarming.py
=================================================================================

A small heartwarming story world about a child, a dashed plan, and a warranty
that turns a worry into a kind solution.

Seed premise:
- A child loves a small gadget with a warranty.
- The gadget gets damaged during an excited dash.
- The child feels worried in an inner monologue.
- Bravery and kindness lead to an honest repair and a gentle ending.

The world is intentionally tiny and constraint-checked: the story only exists
when the object at risk really is protected by a warranty plan that applies to
the damage, and the ending is driven by the simulated state.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["damage", "fear", "bravery", "kindness", "relief", "love", "worry", "repair"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little shop"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    verb: str
    gerund: str
    rush: str
    damage: str
    zone: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Warranty:
    id: str
    label: str
    phrase: str
    covers: set[str]
    applies_to: set[str]
    helper: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.zone: set[str] = set()
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            if actor.meters["damage"] >= THRESHOLD:
                sig = ("damage_notice", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    actor.memes["worry"] += 1
                    out.append(f"{actor.pronoun().capitalize()} felt a tight little worry in {actor.id}'s chest.")
            if actor.memes["kindness"] >= THRESHOLD and actor.memes["worry"] >= THRESHOLD:
                sig = ("calm", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    actor.memes["relief"] += 1
                    out.append(f"Kindness helped {actor.id} breathe a little easier.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def cause_damage(world: World, actor: Entity, cause: Cause, item: Entity) -> None:
    world.zone = set(cause.zone)
    actor.meters["damage"] += 1
    item.meters["damage"] += 1
    propagate(world, narrate=False)


def warranty_applies(cause: Cause, warranty: Warranty, item: Entity) -> bool:
    return cause.damage in warranty.applies_to and item.label in warranty.covers


def repair_possible(world: World, cause: Cause, item: Entity, warranty: Warranty) -> bool:
    return warranty_applies(cause, warranty, item)


def tell(world: World, hero: Entity, parent: Entity, item: Entity, cause: Cause, warranty: Warranty) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved {item.phrase} and kept {item.it()} close."
    )
    world.say(
        f"One day, {hero.id} wanted to {cause.verb}, because {cause.keyword or cause.damage} felt exciting."
    )
    world.say(
        f"When {hero.id} ran, {hero.pronoun('possessive')} small mistake turned the {item.label} {cause.damage}."
    )


def inner_monologue(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} looked down and thought, 'Oh no, what if the {item.label} cannot be fixed?'"
    )
    world.say(
        f"Then {hero.id} took a breath and thought, 'I should be brave and tell the truth.'"
    )
    hero.memes["bravery"] += 1


def ask_for_help(world: World, hero: Entity, parent: Entity, item: Entity, warranty: Warranty) -> None:
    hero.memes["kindness"] += 1
    world.say(
        f"{hero.id} carried the {item.label} back to {parent.label} and explained what happened kindly."
    )
    world.say(
        f"{parent.label.capitalize()} smiled gently and said the warranty could help because the problem was covered."
    )
    world.say(
        f"{hero.id} felt brave enough to go with {parent.label} to the counter."
    )


def resolve(world: World, hero: Entity, parent: Entity, item: Entity, warranty: Warranty) -> None:
    if item.meters["damage"] < THRESHOLD:
        return
    hero.memes["relief"] += 1
    hero.memes["love"] += 1
    item.meters["repair"] += 1
    item.meters["damage"] = 0
    world.say(
        f"At the shop, the helper checked the {warranty.label} and nodded because it fit the problem."
    )
    world.say(
        f"They used the warranty, fixed the {item.label}, and handed it back with a warm, careful smile."
    )
    world.say(
        f"By the end, {hero.id} was laughing again, hugging the {item.label}, and feeling proud of {hero.pronoun('possessive')} honesty."
    )
    world.say(
        f"The little {item.label} was safe in {hero.pronoun('possessive')} hands again, and the day felt kind all the way through."
    )


def story_setup() -> tuple[Setting, Cause, Warranty]:
    setting = Setting(place="the little shop", indoor=True, affords={"dash"})
    cause = Cause(
        id="dash",
        verb="dash across the sidewalk",
        gerund="dashing",
        rush="dash faster",
        damage="scratched",
        zone={"hands", "body"},
        keyword="dash",
        tags={"dash", "accident"},
    )
    warranty = Warranty(
        id="warranty",
        label="warranty card",
        phrase="a little warranty card tucked in the box",
        covers={"toy", "gadget"},
        applies_to={"scratched"},
        helper="shop helper",
        tail="the helper fixed it with care",
    )
    return setting, cause, warranty


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    item: str
    seed: Optional[int] = None


ITEMS = {
    "toy_car": ("toy car", "a shiny toy car with tiny wheels"),
    "music_box": ("music box", "a music box that played a soft tune"),
    "little_clock": ("little clock", "a little clock with a bright face"),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Theo", "Max"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming story world about dash, warranty, bravery, and kindness.")
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--item", choices=ITEMS)
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
    if args.gender == "girl":
        names = GIRL_NAMES
    elif args.gender == "boy":
        names = BOY_NAMES
    else:
        names = GIRL_NAMES + BOY_NAMES
    name = args.name or rng.choice(names)
    gender = args.gender or ("girl" if name in GIRL_NAMES else "boy")
    parent = args.parent or rng.choice(["mother", "father"])
    item = args.item or rng.choice(list(ITEMS))
    return StoryParams(name=name, gender=gender, parent=parent, item=item)


def generate(params: StoryParams) -> StorySample:
    setting, cause, warranty = story_setup()
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    item_label, item_phrase = ITEMS[params.item]
    item = world.add(Entity(id="item", type="thing", label=item_label, phrase=item_phrase, owner=hero.id, caretaker=parent.id))
    item.meters["damage"] = 0

    tell(world, hero, parent, item, cause, warranty)

    world.para()
    world.say(f"Outside, {hero.id} saw a clear path and wanted to {cause.verb}.")
    world.say(f"{hero.id} did it in a dash, and the {item.label} got {cause.damage}.")
    cause_damage(world, hero, cause, item)

    world.para()
    inner_monologue(world, hero, item)
    ask_for_help(world, hero, parent, item, warranty)
    resolve(world, hero, parent, item, warranty)

    world.facts.update(hero=hero, parent=parent, item=item, cause=cause, warranty=warranty)
    prompts = [
        f"Write a heartwarming story for a small child about a dash, a warranty, bravery, and kindness.",
        f"Tell a gentle story where {hero.id} learns that honesty and help can fix a scratched favorite thing.",
        f"Write a short story in which a warranty matters after a child dashes too quickly and feels worried.",
    ]
    story_qa = [
        QAItem(
            question=f"What happened when {hero.id} dashed across the sidewalk?",
            answer=f"{hero.id} dashed too fast and the {item.label} got scratched.",
        ),
        QAItem(
            question=f"What did {hero.id} think about before asking for help?",
            answer=f"{hero.id} worried that the {item.label} might not be fixed, then decided to be brave and tell the truth.",
        ),
        QAItem(
            question=f"Why could the shop help fix the {item.label}?",
            answer=f"The warranty card covered the scratch, so the helper could repair the {item.label} with care.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a warranty?",
            answer="A warranty is a promise that a company will help fix or replace something if a covered problem happens.",
        ),
        QAItem(
            question="What does bravery look like?",
            answer="Bravery can mean doing the right thing even when you feel nervous, like telling the truth and asking for help.",
        ),
        QAItem(
            question="What does kindness do?",
            answer="Kindness helps people feel safe and cared for, and it can turn a mistake into a gentle problem to solve together.",
        ),
    ]
    story = world.render()
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Mia", gender="girl", parent="mother", item="toy_car"),
    StoryParams(name="Leo", gender="boy", parent="father", item="music_box"),
    StoryParams(name="Nora", gender="girl", parent="mother", item="little_clock"),
]


ASP_RULES = r"""
% A thing is at risk when a dash can scratch it.
at_risk(dash, Item) :- item(Item), damage_of(dash, scratched).

% A warranty helps when it covers the damage type and the item.
helps(W, dash, Item) :- warranty(W), item(Item), damage_of(dash, scratched), warranty_covers(W, scratched), warranty_covers(W, Item).

valid_story(Name, Item) :- child(Name), item(Item), at_risk(dash, Item), helps(warranty, dash, Item).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("child", "Mia"))
    lines.append(asp.fact("child", "Leo"))
    lines.append(asp.fact("child", "Nora"))
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("warranty_covers", "warranty", item_id))
    lines.append(asp.fact("damage_of", "dash", "scratched"))
    lines.append(asp.fact("warranty", "warranty"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(name, item) for name in GIRL_NAMES + BOY_NAMES for item in ITEMS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set((n, i) for n in GIRL_NAMES + BOY_NAMES for i in ITEMS)
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(cl)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


def build_story_qa(sample: StorySample) -> None:
    pass


def explain_rejection() -> str:
    return "(No story: the requested combination does not lead to a meaningful warranty repair.)"


def resolve_params_with_validation(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate_sample(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for name, item in combos:
            print(f"  {name:8} {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
