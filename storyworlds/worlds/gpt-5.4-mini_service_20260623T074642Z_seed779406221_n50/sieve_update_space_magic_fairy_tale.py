#!/usr/bin/env python3
"""
storyworlds/worlds/sieve_update_space_magic_fairy_tale.py
=========================================================

A small fairy-tale storyworld about a magical sieve, a nervous update, and a
spacious wish that needs careful sorting.

Seed-influenced premise:
- sieve
- update
- space
- Magic
- Fairy Tale

The world models a tiny court of typed entities with physical meters and
emotional memes. A magical sieve can sort tiny sparkling things; an update can
change the plan; space can be crowded or roomy; and the story turns on whether
the characters trust the magic enough to use it wisely.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    magical: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        gender = self.type
        if gender in {"girl", "queen", "princess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender in {"boy", "king", "prince"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    spacious: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    type: str
    trait: str
    kind: str
    mess: str
    space_need: float
    magic_need: float
    keyword: str


@dataclass
class Charm:
    id: str
    label: str
    covers_space: bool = False
    clears_mess: bool = False
    blessing: str = ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.story: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
            self.story[-1].append(text)

    def para(self) -> None:
        if self.story[-1]:
            self.story.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.story if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.story = [[]]
        clone.facts = dict(self.facts)
        return clone


def _tick(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            if actor.meters.get("crowded", 0) >= THRESHOLD and actor.meters.get("need_space", 0) >= THRESHOLD:
                sig = ("restless", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    actor.memes["restless"] = actor.memes.get("restless", 0) + 1
                    world.say(f"{actor.pronoun().capitalize()} felt wiggly because there was not enough room to think.")
                    changed = True
            if actor.meters.get("sparkles", 0) >= THRESHOLD and actor.meters.get("messy", 0) >= THRESHOLD:
                sig = ("need_update", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    actor.memes["worry"] = actor.memes.get("worry", 0) + 1
                    world.say(f"{actor.pronoun().capitalize()} worried that the bright little bits would spill everywhere.")
                    changed = True
            if actor.meters.get("space_clear", 0) >= THRESHOLD and actor.memes.get("trust", 0) >= THRESHOLD:
                sig = ("calm", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    actor.memes["joy"] = actor.memes.get("joy", 0) + 1
                    actor.memes["worry"] = 0
                    world.say(f"{actor.pronoun().capitalize()} could breathe again in the open, quiet space.")
                    changed = True


def has_room(world: World, actor: Entity) -> bool:
    return world.setting.spacious or actor.meters.get("space_clear", 0) >= THRESHOLD


def can_update(world: World, thing: Thing) -> bool:
    return thing.keyword in {"sieve", "space", "update"}


def choose_charm(thing: Thing) -> Optional[Charm]:
    if thing.kind == "sparkles" and thing.space_need >= 1 and thing.magic_need >= 1:
        return CHARMES["shimmer_lid"]
    if thing.kind == "space" and thing.space_need >= 1:
        return CHARMES["wide_cloak"]
    return None


def foretell(world: World, actor: Entity, thing: Thing) -> bool:
    sim = world.copy()
    hero = sim.get(actor.id)
    hero.meters["sparkles"] = hero.meters.get("sparkles", 0) + 1
    hero.meters["messy"] = hero.meters.get("messy", 0) + thing.magic_need
    _tick(sim)
    return hero.meters.get("worry", 0) >= THRESHOLD


def introduce(world: World, hero: Entity, helper: Entity, thing: Thing) -> None:
    world.say(f"Once in a little kingdom, {hero.id} was a {hero.type} who loved {thing.keyword} and gentle magic.")
    world.say(f"{helper.id} kept a small {thing.label} on a cloth beside the hearth, where it could wait for its turn.")
    world.say(f"Everyone said the {thing.label} was special, because it could help sort light things without breaking them.")


def want(world: World, hero: Entity, thing: Thing) -> None:
    hero.meters["need_space"] = hero.meters.get("need_space", 0) + 1
    world.say(f"{hero.id} wanted to {thing.keyword} at once, but there was not enough space on the table for a fair try.")


def update_request(world: World, helper: Entity, hero: Entity, thing: Thing) -> None:
    if not can_update(world, thing):
        raise StoryError("This world only updates magical plans about sieve, space, or the tale's wish.")
    helper.memes["care"] = helper.memes.get("care", 0) + 1
    world.say(f"{helper.id} said, \"Let us make an update before we begin, so the magic knows the new plan.\"")


def warn(world: World, hero: Entity, thing: Thing) -> None:
    if foretell(world, hero, thing):
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        world.say(f"{hero.id} peered at the heap and saw that the glitter would be lost if they rushed.")
        world.say(f"\"We need more space,\" {hero.pronoun('subject')} whispered. \"And we need the sieve to be steady.\"")


def magic_sieve(world: World, hero: Entity, thing: Thing, charm: Charm) -> None:
    hero.meters["sparkles"] = hero.meters.get("sparkles", 0) + 1
    if charm.clears_mess:
        hero.meters["messy"] = 0
    if charm.covers_space:
        hero.meters["space_clear"] = hero.meters.get("space_clear", 0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    world.say(f"Then the {thing.label} shone softly, and the magical sieve listened like a wise old moon.")
    world.say(f"The sieve let the bright bits fall in a tidy line, and the dull bits stayed behind where they belonged.")


def resolve(world: World, hero: Entity, helper: Entity, thing: Thing, charm: Charm) -> None:
    if world.setting.spacious:
        world.say(f"At last, there was plenty of space for the work, and the update made the whole room feel calm.")
    else:
        world.say(f"They moved to the sunny window, where the little patch of space was just large enough for the spell.")
    world.say(
        f"{hero.id} smiled as the magic did its careful work, and {helper.id} tucked the finished {thing.label} into a neat basket."
    )
    world.say(f"In the end, the kingdom had tidy sparkles, a clearer plan, and room enough for one happy story.")




SETTINGS = {
    "tower_room": Setting(place="the tower room", indoors=True, spacious=False, affords={"sieve", "update", "space"}),
    "sunny_courtyard": Setting(place="the sunny courtyard", indoors=False, spacious=True, affords={"sieve", "update", "space"}),
    "market_stall": Setting(place="the market stall", indoors=False, spacious=False, affords={"sieve", "update"}),
}

THINGS = {
    "sieve": Thing(
        id="sieve",
        label="sieve",
        phrase="a silver sieve with tiny stars along the rim",
        type="thing",
        trait="magical",
        kind="sparkles",
        mess="glittery",
        space_need=1.0,
        magic_need=1.0,
        keyword="sieve",
    ),
    "update": Thing(
        id="update",
        label="update",
        phrase="a new update to the plan",
        type="thing",
        trait="careful",
        kind="update",
        mess="tangled",
        space_need=1.0,
        magic_need=0.0,
        keyword="update",
    ),
    "space": Thing(
        id="space",
        label="space",
        phrase="a wide space beside the window",
        type="thing",
        trait="open",
        kind="space",
        mess="crowded",
        space_need=1.0,
        magic_need=0.0,
        keyword="space",
    ),
}

CHARMES = {
    "wide_cloak": Charm(id="wide_cloak", label="a wide blue cloak", covers_space=True, blessing="room"),
    "shimmer_lid": Charm(id="shimmer_lid", label="a shimmer lid", clears_mess=True, blessing="sorting"),
}

HERO_NAMES = ["Ella", "Mina", "Rose", "Nora", "Luna", "Ivy"]
HELPER_NAMES = ["The Wise Aunt", "The Kindly Baker", "The Garden Maid", "The Old Weaver"]


@dataclass
class StoryParams:
    place: str
    thing: str
    hero: str
    helper: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale world about a magical sieve, an update, and space.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
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
    thing = args.thing or rng.choice(["sieve", "update", "space"])
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    if thing not in {"sieve", "update", "space"}:
        raise StoryError("This fairy-tale world only tells stories about sieve, update, and space.")
    return StoryParams(place=place, thing=thing, hero=hero, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero, kind="character", type="girl"))
    helper = world.add(Entity(id=params.helper, kind="character", type="queen", label=params.helper.lower()))
    thing = THINGS[params.thing]
    charm = CHARMES["shimmer_lid"] if params.thing == "sieve" else CHARMES["wide_cloak"]

    introduce(world, hero, helper, thing)
    world.para()
    want(world, hero, thing)
    update_request(world, helper, hero, thing)
    warn(world, hero, thing)
    magic_sieve(world, hero, thing, charm)
    world.para()
    resolve(world, hero, helper, thing, charm)
    world.facts = {"hero": hero, "helper": helper, "thing": thing, "charm": charm, "place": params.place}
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    thing = f["thing"]
    return [
        f"Write a fairy tale about a magical {thing.label} and a careful update that makes enough space.",
        f"Tell a short child-friendly story where someone uses a sieve, then changes the plan, then finds space for the magic.",
        f"Make a gentle fairy tale with a shining {thing.label}, a wise helper, and a tidy ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, thing = f["hero"], f["helper"], f["thing"]
    return [
        QAItem(
            question=f"Who wanted to use the {thing.label} in the story?",
            answer=f"{hero.id} wanted to use the {thing.label}, but first they needed a careful update and enough space.",
        ),
        QAItem(
            question="Why did the helper suggest an update before the magic began?",
            answer=f"{helper.id} suggested an update because rushing would have made the bright bits spill and the room feel crowded.",
        ),
        QAItem(
            question="What changed by the end of the tale?",
            answer=f"By the end, the magic had sorted the bright bits, the plan was clearer, and there was room enough for everyone.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sieve used for?",
            answer="A sieve is used to separate small pieces from larger ones, like letting fine bits fall through while keeping bigger things back.",
        ),
        QAItem(
            question="What does an update do?",
            answer="An update changes a plan or a story so it matches what is needed now.",
        ),
        QAItem(
            question="What is space?",
            answer="Space is room to move, work, or rest without bumping into everything else.",
        ),
        QAItem(
            question="What is magic in a fairy tale?",
            answer="Magic is a special power in fairy tales that can make unusual things happen, often in a wondrous and helpful way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"setting={world.setting.place} spacious={world.setting.spacious}")
    return "\n".join(lines)


ASP_RULES = r"""
#show compatible/3.

compatible(Place, Thing, Charm) :- setting(Place), thing(Thing), charm(Charm),
    affords(Place, Thing), needs_space(Thing), covers_space(Charm).
compatible(Place, Thing, Charm) :- setting(Place), thing(Thing), charm(Charm),
    affords(Place, Thing), needs_magic(Thing), clears_mess(Charm).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        if s.spacious:
            lines.append(asp.fact("spacious", sid))
        for item in sorted(s.affords):
            lines.append(asp.fact("affords", sid, item))
    for tid, t in THINGS.items():
        lines.append(asp.fact("thing", tid))
        lines.append(asp.fact("needs_space", tid) if t.space_need >= THRESHOLD else asp.fact("needs_space", tid, 0))
        if t.magic_need >= THRESHOLD:
            lines.append(asp.fact("needs_magic", tid))
    for cid, c in CHARMES.items():
        lines.append(asp.fact("charm", cid))
        if c.covers_space:
            lines.append(asp.fact("covers_space", cid))
        if c.clears_mess:
            lines.append(asp.fact("clears_mess", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatible() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def python_compatible() -> list[tuple]:
    out = []
    for place, s in SETTINGS.items():
        for thing_id, thing in THINGS.items():
            for charm_id, charm in CHARMES.items():
                if thing.space_need >= THRESHOLD and not charm.covers_space:
                    continue
                if thing.magic_need >= THRESHOLD and not charm.clears_mess:
                    continue
                if thing_id in s.affords:
                    out.append((place, thing_id, charm_id))
    return sorted(set(out))


def asp_verify() -> int:
    a = set(asp_compatible())
    b = set(python_compatible())
    if a == b:
        print(f"OK: ASP matches Python ({len(a)} compatible triples).")
        return 0
    print("MISMATCH between ASP and Python.")
    if a - b:
        print("only in ASP:", sorted(a - b))
    if b - a:
        print("only in Python:", sorted(b - a))
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


CURATED = [
    StoryParams(place="tower_room", thing="sieve", hero="Ella", helper="The Wise Aunt"),
    StoryParams(place="sunny_courtyard", thing="space", hero="Mina", helper="The Kindly Baker"),
    StoryParams(place="market_stall", thing="update", hero="Rose", helper="The Old Weaver"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_compatible()
        print(f"{len(triples)} compatible triples:")
        for t in triples:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
