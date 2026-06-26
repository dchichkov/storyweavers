#!/usr/bin/env python3
"""
storyworlds/worlds/fort_velveteen_feather_bravery_slice_of_life.py
===================================================================

A cozy slice-of-life storyworld about a child building a small fort with a
velveteen blanket, a feather, and one brave little choice.

Premise:
- A child loves making a fort in an everyday room.
- A velveteen blanket makes the fort feel soft and special.
- A feather acts like a tiny brave charm or topper.
- A small worry appears: the child wants to do something new inside the fort
  but feels a little shy.
- A gentle helper suggests one practical, brave step.
- The child tries it, and the fort ends the day feeling warm, safe, and lived-in.

This world is intentionally small and constraint-checked. It avoids frozen
template prose by simulating a little world state:
- physical meters: comfort, tidiness, shelter, smallness
- emotional memes: joy, nerves, bravery, closeness

The result is a child-facing slice-of-life story with a clear setup, turn, and
resolution image.
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
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

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
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Fort:
    label: str
    requires: set[str] = field(default_factory=set)  # item ids
    cozy_boost: float = 1.0
    brave_boost: float = 1.0


@dataclass
class StoryParams:
    place: str
    fort: str
    blanket: str
    feather: str
    hero_name: str
    hero_gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _add_meter(e: Entity, key: str, amt: float) -> None:
    e.meters[key] = _meter(e, key) + amt


def _add_mem(e: Entity, key: str, amt: float) -> None:
    e.memes[key] = _mem(e, key) + amt


def _propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []

    hero = next((e for e in world.entities.values() if e.kind == "character"), None)
    if hero is None:
        return out

    if _mem(hero, "bravery") >= THRESHOLD and ("bravery_line", hero.id) not in world.fired:
        world.fired.add(("bravery_line", hero.id))
        _add_meter(hero, "comfort", 0.5)
        out.append(f"{hero.id} stood a little straighter inside the fort.")

    fort = next((e for e in world.entities.values() if e.type == "fort"), None)
    blanket = next((e for e in world.entities.values() if e.type == "blanket"), None)
    feather = next((e for e in world.entities.values() if e.type == "feather"), None)

    if fort and blanket and blanket.worn_by == fort.id and feather and feather.worn_by == fort.id:
        sig = ("cozy_fort", fort.id)
        if sig not in world.fired:
            world.fired.add(sig)
            _add_meter(fort, "shelter", 1.0)
            _add_meter(fort, "comfort", 1.0)
            if hero:
                _add_mem(hero, "joy", 0.5)
            out.append("The fort felt extra cozy with the velveteen blanket and the feather in place.")

    if hero and fort and _meter(fort, "comfort") >= 1.0 and _mem(hero, "nerves") >= THRESHOLD:
        sig = ("nerves_settle", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            _add_mem(hero, "nerves", -0.5)
            _add_mem(hero, "bravery", 0.5)
            out.append(f"The soft fort made {hero.id} feel a little braver.")

    if narrate:
        for s in out:
            world.say(s)
    return out


def _build_fort(world: World, hero: Entity, fort: Entity, blanket: Entity, feather: Entity) -> None:
    hero.meters["smallness"] = 1.0
    fort.worn_by = hero.id
    blanket.worn_by = fort.id
    feather.worn_by = fort.id
    _add_meter(fort, "shelter", 0.5)
    _add_mem(hero, "joy", 0.5)
    _add_mem(hero, "bravery", 0.25)
    world.say(
        f"{hero.id} built a {fort.label} in the {world.setting.place}, using {blanket.phrase} "
        f"and a tiny feather as a topper."
    )
    world.say(f"It was the kind of fort that made an ordinary afternoon feel special.")


def _arrive(world: World, hero: Entity, helper: Entity, fort: Entity) -> None:
    if world.setting.indoors:
        world.say(f"Later, {hero.id} and {helper.label} settled down near the fort in the {world.setting.place}.")
    else:
        world.say(f"Later, {hero.id} and {helper.label} came back to the fort in the {world.setting.place}.")
    _add_mem(hero, "nerves", 0.5)
    _propagate(world)


def _worry(world: World, hero: Entity, helper: Entity, fort: Entity, feather: Entity) -> None:
    _add_mem(hero, "nerves", 0.75)
    world.say(
        f"{hero.id} wanted to do something brave inside the fort, but the idea felt a little wobbly."
    )
    world.say(
        f"{helper.label} noticed {hero.id} looking at the feather and said, "
        f'"You can try one small brave thing first."'
    )
    _add_mem(hero, "bravery", 0.5)
    _propagate(world)


def _action(world: World, hero: Entity, helper: Entity, fort: Entity, blanket: Entity, feather: Entity) -> None:
    _add_mem(hero, "bravery", 0.75)
    _add_mem(hero, "joy", 0.5)
    _add_meter(fort, "comfort", 0.5)
    world.say(
        f"So {hero.id} took a breath, held the feather, and read the first page out loud."
    )
    world.say(
        f"{helper.label} listened, smiling, while the velveteen blanket kept the fort snug around them."
    )
    _propagate(world)


def _resolution(world: World, hero: Entity, helper: Entity, fort: Entity, blanket: Entity, feather: Entity) -> None:
    _add_mem(hero, "bravery", 0.25)
    _add_meter(fort, "comfort", 0.5)
    world.say(
        f"By the end, {hero.id} was laughing softly, and the feather sat on the fort like a tiny promise."
    )
    world.say(
        f"The velveteen blanket stayed smooth, the fort stayed standing, and {hero.id} stayed brave enough to try again tomorrow."
    )


SETTINGS = {
    "living_room": Setting(place="the living room", indoors=True, affords={"fort"}),
    "playroom": Setting(place="the playroom", indoors=True, affords={"fort"}),
    "sunroom": Setting(place="the sunroom", indoors=True, affords={"fort"}),
    "back_patio": Setting(place="the back patio", indoors=False, affords={"fort"}),
}

FORTS = {
    "reading_fort": Fort(label="reading fort", requires={"velveteen_blanket", "feather"}, cozy_boost=1.0, brave_boost=1.0),
    "nap_fort": Fort(label="nap fort", requires={"velveteen_blanket", "feather"}, cozy_boost=1.2, brave_boost=0.8),
    "story_fort": Fort(label="story fort", requires={"velveteen_blanket", "feather"}, cozy_boost=1.1, brave_boost=1.1),
}

BLANKETS = {
    "velveteen_blanket": {"label": "velveteen blanket", "phrase": "a velveteen blanket", "texture": "velveteen"},
}

FEATHERS = {
    "feather": {"label": "feather", "phrase": "a little feather", "kind": "feather"},
}

HERO_NAMES = ["Mina", "Luca", "Nora", "Toby", "Sana", "Eli", "Rae", "Iris"]
HELPERS = {
    "mom": {"label": "Mom", "gender": "mother", "type": "mother"},
    "dad": {"label": "Dad", "gender": "father", "type": "father"},
    "grandma": {"label": "Grandma", "gender": "mother", "type": "mother"},
    "older_sibling": {"label": "older sibling", "gender": "sibling", "type": "sibling"},
}

TRAITS = ["shy", "careful", "gentle", "curious", "quiet", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(place, fort, "velveteen_blanket", "feather") for place in SETTINGS for fort in FORTS]


def explain_rejection(place: str, fort: str, blanket: str, feather: str) -> str:
    return "(No story: this world needs a fort, a velveteen blanket, and a feather together in a supported room.)"


def explain_gender(_hero_name: str, _gender: str) -> str:
    return ""


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy slice-of-life fort story with velveteen, a feather, and bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--fort", choices=FORTS)
    ap.add_argument("--blanket", choices=BLANKETS)
    ap.add_argument("--feather", choices=FEATHERS)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.blanket and args.blanket != "velveteen_blanket":
        raise StoryError("This world only works with a velveteen blanket.")
    if args.feather and args.feather != "feather":
        raise StoryError("This world only works with a feather.")
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.fort:
        combos = [c for c in combos if c[1] == args.fort]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, fort, blanket, feather = rng.choice(sorted(combos))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(list(HELPERS))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, fort=fort, blanket=blanket, feather=feather,
                       hero_name=hero_name, hero_gender=hero_gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero_type = "girl" if params.hero_gender == "girl" else "boy"
    helper_info = HELPERS[params.helper]

    hero = world.add(Entity(id=params.hero_name, kind="character", type=hero_type, traits=[params.trait]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_info["type"], label=helper_info["label"]))
    fort = world.add(Entity(id="fort", type="fort", label=FORTS[params.fort].label))
    blanket = world.add(Entity(id=params.blanket, type="blanket", label=BLANKETS[params.blanket]["label"],
                               phrase=BLANKETS[params.blanket]["phrase"], owner=hero.id))
    feather = world.add(Entity(id=params.feather, type="feather", label=FEATHERS[params.feather]["label"],
                               phrase=FEATHERS[params.feather]["phrase"], owner=hero.id))

    # Act 1
    world.say(
        f"{hero.id} was a {params.trait} little {hero.type} who loved making forts."
    )
    world.say(
        f"One of {hero.pronoun('possessive')} favorite things was a soft {blanket.label} and a tiny feather."
    )
    _build_fort(world, hero, fort, blanket, feather)

    # Act 2
    world.para()
    _arrive(world, hero, helper, fort)
    _worry(world, hero, helper, fort, feather)

    # Act 3
    world.para()
    _action(world, hero, helper, fort, blanket, feather)
    _resolution(world, hero, helper, fort, blanket, feather)

    world.facts.update(
        hero=hero,
        helper=helper,
        fort=fort,
        blanket=blanket,
        feather=feather,
        place=params.place,
        trait=params.trait,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    fort = f["fort"]
    return [
        f"Write a cozy slice-of-life story about {hero.id} building a {fort.label} with a velveteen blanket and a feather.",
        f"Tell a gentle story where {hero.id} feels shy, gets a little braver, and finishes inside a small fort with {helper.label}.",
        f"Write a child-friendly story about a fort, a velveteen blanket, a feather, and one small brave choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    fort = f["fort"]
    blanket = f["blanket"]
    feather = f["feather"]
    return [
        QAItem(
            question=f"What did {hero.id} build?",
            answer=f"{hero.id} built a {fort.label} with {blanket.label} and a feather."
        ),
        QAItem(
            question=f"What made {hero.id} feel brave inside the fort?",
            answer=f"The soft fort, the velveteen blanket, and {helper.label}'s gentle encouragement helped {hero.id} feel brave."
        ),
        QAItem(
            question=f"What did {hero.id} do that was brave?",
            answer=f"{hero.id} took a breath, held the feather, and read the first page out loud."
        ),
        QAItem(
            question=f"What was the special blanket like?",
            answer=f"It was a velveteen blanket, which means it was soft and smooth and made the fort feel cozy."
        ),
        QAItem(
            question=f"What stayed special at the end of the story?",
            answer=f"The fort stayed standing, the feather stayed on top, and {hero.id} stayed brave enough to try again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fort?",
            answer="A fort is a small shelter or pretend hideout made from blankets, pillows, chairs, or boxes."
        ),
        QAItem(
            question="What is velveteen?",
            answer="Velveteen is a soft fabric that feels smooth and cozy, a little like velvet."
        ),
        QAItem(
            question="What is a feather?",
            answer="A feather is a light part of a bird that can float easily in the air."
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is being a little scared but still trying to do something kind, helpful, or new."
        ),
    ]


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="living_room", fort="reading_fort", blanket="velveteen_blanket", feather="feather",
                hero_name="Mina", hero_gender="girl", helper="mom", trait="shy"),
    StoryParams(place="playroom", fort="story_fort", blanket="velveteen_blanket", feather="feather",
                hero_name="Luca", hero_gender="boy", helper="dad", trait="careful"),
    StoryParams(place="sunroom", fort="nap_fort", blanket="velveteen_blanket", feather="feather",
                hero_name="Nora", hero_gender="girl", helper="grandma", trait="thoughtful"),
]


ASP_RULES = r"""
valid_combo(Place, Fort) :- place(Place), fort(Fort).
requires_velveteen(Fort) :- fort(Fort).
requires_feather(Fort) :- fort(Fort).
compatible_story(Place, Fort, blanket, feather) :- valid_combo(Place, Fort),
                                                   requires_velveteen(Fort),
                                                   requires_feather(Fort).
#show compatible_story/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for f in FORTS:
        lines.append(asp.fact("fort", f))
    lines.append(asp.fact("item", "velveteen_blanket"))
    lines.append(asp.fact("item", "feather"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/4."))
    return sorted(set(asp.atoms(model, "compatible_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = {(p, f, b, fe) for (p, f, b, fe) in asp_valid_combos()}
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_story(params: StoryParams) -> StorySample:
    return generate(params)


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
        print(asp_program("#show compatible_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for combo in combos:
            print("  ", combo)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.fort} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.blanket and args.blanket != "velveteen_blanket":
        raise StoryError("This world only supports a velveteen blanket.")
    if args.feather and args.feather != "feather":
        raise StoryError("This world only supports a feather.")
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.fort and args.fort not in FORTS:
        raise StoryError("Unknown fort kind.")
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError("Unknown gender.")

    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.fort:
        combos = [c for c in combos if c[1] == args.fort]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, fort, blanket, feather = rng.choice(sorted(combos))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(list(HELPERS))
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        place=place,
        fort=fort,
        blanket=blanket,
        feather=feather,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper=helper,
        trait=trait,
    )


if __name__ == "__main__":
    main()
