#!/usr/bin/env python3
"""
storyworlds/worlds/few_growl_paste_happy_ending_folk_tale.py
=============================================================

A small folk-tale storyworld about a few helpers, a growling troublemaker,
and a jar of paste that turns a near-miss into a happy ending.

Premise:
- A child and a few villagers need to mend something simple and important.
- A growling forest creature scares them, but it is not truly cruel.
- Paste is the useful material that lets the helpers fix the problem.

The stories are short, concrete, and state-driven:
- physical meters track brokenness, mess, and repair
- emotional memes track fear, courage, trust, and joy

The style leans folk-tale: simple roles, a little repetition, a mild test,
and a warm ending image showing what changed.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    is_actor: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    keyword: str
    calm: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    title: str
    verb: str
    sound: str
    risk: str
    mess: str
    breaks: str
    zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    phrase: str
    fixes: set[str]
    covers: set[str]
    step: str
    ending: str
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.history: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def actors(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.is_actor]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        clone.history = list(self.history)
        return clone


def _r_break(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.actors():
        if actor.meter("bother") < THRESHOLD:
            continue
        for obj in world.entities.values():
            if obj.kind != "thing":
                continue
            if obj.owner and obj.owner != actor.id:
                continue
            if obj.meter("broken") >= THRESHOLD:
                continue
            sig = ("break", actor.id, obj.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            obj.meters["broken"] = obj.meter("broken") + 1.0
            out.append(f"{obj.label.capitalize()} was broken by the trouble.")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.actors():
        if actor.meter("mess") < THRESHOLD:
            continue
        sig = ("spill", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fluster"] = actor.meme("fluster") + 1.0
        out.append(f"{actor.id} felt flustered by the mess.")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    repair = world.facts.get("repair")
    if repair is None:
        return out
    for obj in world.entities.values():
        if obj.kind != "thing" or obj.meter("broken") < THRESHOLD:
            continue
        sig = ("repair", obj.id, repair.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if obj.label in repair.fixes:
            obj.meters["broken"] = 0.0
            obj.meters["mended"] = 1.0
            out.append(f"The {obj.label} was mended with {repair.label}.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    creature = world.facts.get("creature")
    if creature is None:
        return out
    if creature.meme("fear") < THRESHOLD or creature.meme("trust") < THRESHOLD:
        return out
    sig = ("calm", creature.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creature.memes["growl"] = 0.0
    creature.memes["joy"] = creature.meme("joy") + 1.0
    out.append(f"The growling creature settled and listened.")
    return out


RULES = [_r_break, _r_spill, _r_repair, _r_calm]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            produced = rule(world)
            if produced:
                changed = True
                lines.extend(produced)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


def tale_opening(world: World, hero: Entity, helpers: list[Entity], place: Place) -> None:
    world.say(
        f"Once in a little land, {hero.id} lived by {place.name}, where the path smelled calm and the trees stood close."
    )
    world.say(
        f"There were only a few helpers that morning, and they were glad of one another's hands."
    )
    world.say(
        f"They had a jar of paste, because in folk tales a small thing can save a whole day."
    )
    if helpers:
        names = ", ".join(h.id for h in helpers)
        world.say(f"{names.capitalize()} came along beside {hero.id} to help.")
    world.say(f"{place.calm.capitalize()} was the kind of quiet that made even little jobs feel important.")


def set_problem(world: World, hero: Entity, object_: Entity, trouble: Trouble, creature: Entity) -> None:
    hero.memes["hope"] = hero.meme("hope") + 1.0
    hero.memes["fear"] = hero.meme("fear") + 1.0
    creature.memes["growl"] = 1.0
    world.say(
        f"But the {object_.label} had a crack, and the crack made a thin {trouble.sound} when the wind slipped through it."
    )
    world.say(
        f"{hero.id} knew it would not last long unless someone fixed it."
    )
    world.say(
        f"Then, from the brambles, came a growl."
    )
    world.say(
        f"A {creature.label} with bright eyes stood there and gave a low growl as if it guarded the whole lane."
    )
    world.say(
        f"{hero.id} held still, because the growl sounded fierce even if the eyes did not."
    )
    hero.meters["bother"] = 1.0
    propagate(world, narrate=True)


def choose_fix(world: World, repair: Repair, hero: Entity, creature: Entity) -> None:
    world.facts["repair"] = repair
    world.say(
        f"Still, {hero.id} remembered the jar of {repair.label}."
    )
    world.say(
        f"It was sticky and pale, and folk-tale folks knew it could mend a split thing if they worked gently."
    )
    hero.memes["courage"] = hero.meme("courage") + 1.0
    creature.memes["fear"] = 1.0
    world.say(
        f"{hero.id} whispered to the creature, 'We are only a few, but we can mend this together.'"
    )
    world.say(
        f"The creature's ears twitched, and its growl grew softer."
    )
    creature.memes["trust"] = creature.meme("trust") + 1.0
    creature.memes["growl"] = 0.0
    propagate(world, narrate=True)


def mend_and_end(world: World, hero: Entity, helpers: list[Entity], object_: Entity, repair: Repair, creature: Entity) -> None:
    object_.meters["broken"] = 0.0
    object_.meters["mended"] = 1.0
    hero.memes["joy"] = hero.meme("joy") + 1.0
    hero.memes["fear"] = 0.0
    creature.memes["joy"] = creature.meme("joy") + 1.0
    world.say(
        f"At once, {hero.id} and the few helpers spread the {repair.label} along the crack, just as {repair.step}."
    )
    world.say(
        f"The {object_.label} held firm again."
    )
    world.say(
        f"The growling creature watched the work, then nodded and helped hold the piece steady."
    )
    world.say(
        f"When the paste dried, the lane was whole, the creature was calm, and everyone laughed under the trees."
    )
    world.say(
        f"In the end, the little land was quiet again, except for happy feet and the soft tap of a finished day."
    )
    world.say(
        f"{repair.ending.capitalize()}, and the few helpers went home with bright hands and light hearts."
    )


@dataclass
class StoryParams:
    place: str
    hero: str
    helper1: str
    helper2: str
    creature: str
    object_name: str
    trouble: str
    repair: str
    seed: Optional[int] = None


PLACES = {
    "bridge_lane": Place(
        name="the bridge lane",
        keyword="bridge",
        calm="the river below ran slow",
        affords={"mend"},
    ),
    "garden_path": Place(
        name="the garden path",
        keyword="path",
        calm="the bees were asleep in the flowers",
        affords={"mend"},
    ),
    "mill_road": Place(
        name="the mill road",
        keyword="road",
        calm="the mill wheel turned soft and slow",
        affords={"mend"},
    ),
}

TROUBLES = {
    "crack": Trouble(
        id="crack",
        title="a crack",
        verb="split",
        sound="hush-hiss",
        risk="it might widen in the wind",
        mess="splinters",
        breaks="the old board",
        zone="wood",
        tags={"wood"},
    ),
}

REPAIRS = {
    "paste": Repair(
        id="paste",
        label="paste",
        phrase="a jar of paste",
        fixes={"bridge", "gate", "sign"},
        covers={"wood"},
        step="they pressed the paste into the crack with careful fingers",
        ending="the paste dried to a steady seal",
    ),
}

HERO_NAMES = ["Mara", "Tobin", "Elin", "Nell", "Bram", "Ivo"]
HELPER_NAMES = ["Pip", "Sia", "Lark", "Roan", "Wren", "Tess"]
CREATURE_NAMES = ["the old badger", "the grey fox", "the burly boar", "the hill hound"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for t in TROUBLES:
            for r in REPAIRS:
                out.append((p, t, r))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld with a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--hero")
    ap.add_argument("--helper1")
    ap.add_argument("--helper2")
    ap.add_argument("--creature")
    ap.add_argument("--object")
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
    place = args.place or rng.choice(list(PLACES))
    trouble = args.trouble or rng.choice(list(TROUBLES))
    repair = args.repair or rng.choice(list(REPAIRS))
    if args.object and args.object != "bridge":
        raise StoryError("This world only tells a bridge-mending folk tale right now.")
    hero = args.hero or rng.choice(HERO_NAMES)
    helper1 = args.helper1 or rng.choice([n for n in HELPER_NAMES if n != hero])
    helper2 = args.helper2 or rng.choice([n for n in HELPER_NAMES if n not in {hero, helper1}])
    creature = args.creature or rng.choice(CREATURE_NAMES)
    obj = "bridge"
    return StoryParams(place=place, hero=hero, helper1=helper1, helper2=helper2, creature=creature, object_name=obj, trouble=trouble, repair=repair)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.hero, kind="character", type="girl", is_actor=True))
    helper1 = world.add(Entity(id=params.helper1, kind="character", type="boy", is_actor=True))
    helper2 = world.add(Entity(id=params.helper2, kind="character", type="girl", is_actor=True))
    creature = world.add(Entity(id=params.creature, kind="character", type="creature", is_actor=True))
    object_ = world.add(Entity(id="bridge", kind="thing", type="bridge", label="bridge", phrase="the little bridge", caretaker=hero.id))
    world.facts["hero"] = hero
    world.facts["helpers"] = [helper1, helper2]
    world.facts["creature"] = creature
    world.facts["object"] = object_
    trouble = TROUBLES[params.trouble]
    repair = REPAIRS[params.repair]

    tale_opening(world, hero, [helper1, helper2], world.place)
    world.para()
    set_problem(world, hero, object_, trouble, creature)
    world.para()
    choose_fix(world, repair, hero, creature)
    world.para()
    mend_and_end(world, hero, [helper1, helper2], object_, repair, creature)

    world.facts.update(params=params, trouble=trouble, repair=repair, place=world.place)
    story = world.render()
    prompts = [
        "Write a short folk tale about a few helpers, a growling creature, and a jar of paste.",
        f"Tell a child-friendly story where {params.hero} and a few friends mend a bridge after hearing a growl.",
        "Write a happy-ending tale in which paste helps turn a scary moment into a kind one.",
    ]
    story_qa = [
        QAItem(
            question="What problem did the little group need to fix?",
            answer="They needed to mend the crack in the bridge before it got worse in the wind.",
        ),
        QAItem(
            question="Why did the creature seem scary at first?",
            answer="It came out with a growl, so everyone thought it might be guarding the lane or mean trouble.",
        ),
        QAItem(
            question="What did the helpers use to repair the bridge?",
            answer="They used a jar of paste to seal the crack and make the bridge hold firm again.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The bridge was mended, the creature was calm, and everyone went home happy.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is paste used for?",
            answer="Paste is a sticky material that helps hold pieces together or cover a crack so something can be repaired.",
        ),
        QAItem(
            question="Why can a growl sound frightening?",
            answer="A growl is a low rough sound, and people often hear it as a warning before they know what is really happening.",
        ),
    ]
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
trouble(T) :- trouble_kind(T).
repair(R) :- repair_kind(R).

compatible(P,T,R) :- setting(P), trouble_kind(T), repair_kind(R).
#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble_kind", tid))
    for rid in REPAIRS:
        lines.append(asp.fact("repair_kind", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    clingo_set = set(asp.atoms(model, "compatible"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short folk tale about a few helpers, a growling creature, and a jar of paste.",
        "Tell a child-friendly story where a bridge is repaired after a scary growl.",
        "Write a happy-ending tale in which paste helps turn a frightening moment into kindness.",
    ]


CURATED = [
    StoryParams(place="bridge_lane", hero="Mara", helper1="Pip", helper2="Sia", creature="the old badger", object_name="bridge", trouble="crack", repair="paste"),
    StoryParams(place="garden_path", hero="Tobin", helper1="Lark", helper2="Wren", creature="the grey fox", object_name="bridge", trouble="crack", repair="paste"),
    StoryParams(place="mill_road", hero="Elin", helper1="Roan", helper2="Tess", creature="the burly boar", object_name="bridge", trouble="crack", repair="paste"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/3."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(combos)} compatible combos:")
        for item in combos:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.hero}: {p.place} / {p.trouble} / {p.repair}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
