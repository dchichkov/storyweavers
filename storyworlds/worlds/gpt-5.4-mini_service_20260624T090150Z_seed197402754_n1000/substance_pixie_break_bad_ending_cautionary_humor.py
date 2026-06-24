#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/substance_pixie_break_bad_ending_cautionary_humor.py
================================================================================================

A small, standalone story world about a superhero kid, a tiny pixie, and a
mysterious substance that causes a break, told with cautionary humor and a bad
ending.

Seed tale sketch:
---
A junior hero named Nova proudly carried a shiny grappling belt to the city fair.
A little pixie named Pip sold sparkly jars of "moon-substance" from a wagon and
said it made broken things easier to fix. Nova wanted to be impressive, so Nova
trusted Pip and poured the substance into the belt's buckle. The buckle snapped,
the belt failed during a rescue, and the hero landed in a puddle while the pixie
laughed too hard to help.

The world model tracks:
- physical meters: shine, crack, slip, mess, wobble, weight
- emotional memes: pride, trust, worry, embarrassment, giggle, guilt

This story is intentionally cautionary: the tempting shortcut makes things worse,
and the ending proves the break mattered.
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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "heroine"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "hero"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the city fair"
    affords: set[str] = field(default_factory=set)


@dataclass
class Substance:
    id: str
    label: str
    phrase: str
    effect: str
    break_chance: float
    mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    region: str
    protects_from: set[str]
    sturdy: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.zone: str = ""
        self.fired: set[str] = set()

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
        clone.facts = dict(self.facts)
        clone.zone = self.zone
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    setting: str
    substance: str
    gear: str
    hero_name: str
    hero_type: str
    pixie_name: str
    seed: Optional[int] = None


SETTINGS = {
    "fair": Setting(place="the city fair", affords={"showoff"}),
    "rooftop": Setting(place="the rooftop rescue stage", affords={"showoff"}),
    "lab": Setting(place="the comic lab", affords={"showoff"}),
}

SUBSTANCES = {
    "moon_glue": Substance(
        id="moon_glue",
        label="moon substance",
        phrase="a jar of moon substance",
        effect="it makes broken things look easy to fix",
        break_chance=1.0,
        mess="sticky",
        tags={"substance", "break"},
    ),
    "spark_syrup": Substance(
        id="spark_syrup",
        label="spark syrup",
        phrase="a bottle of spark syrup",
        effect="it makes a gadget wobble like a jelly sandwich",
        break_chance=1.0,
        mess="gloppy",
        tags={"substance", "break"},
    ),
    "glimmer_ooze": Substance(
        id="glimmer_ooze",
        label="glimmer ooze",
        phrase="a tiny vial of glimmer ooze",
        effect="it promises quick repairs but can crack metal seams",
        break_chance=1.0,
        mess="slimy",
        tags={"substance", "break"},
    ),
}

GEAR = {
    "belt": Gear(
        id="belt",
        label="grappling belt",
        phrase="a shiny grappling belt",
        region="waist",
        protects_from={"none"},
    ),
    "boots": Gear(
        id="boots",
        label="rocket boots",
        phrase="bright rocket boots",
        region="feet",
        protects_from={"slip"},
    ),
    "cape": Gear(
        id="cape",
        label="hero cape",
        phrase="a red hero cape",
        region="back",
        protects_from={"wind"},
    ),
}

PIXIE_TRICKS = [
    "a wink and a wrong promise",
    "a glittery grin",
    "a very suspicious squeak",
    "a laugh that sounded like chimes falling down stairs",
]

HERO_NAMES = ["Nova", "Ari", "Milo", "Zara", "Tess", "Finn"]
PIXIE_NAMES = ["Pip", "Wren", "Midge", "Tink", "Luma"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story world about a pixie, a substance, and a bad break.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--substance", choices=SUBSTANCES)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--name")
    ap.add_argument("--pixie")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    substance = args.substance or rng.choice(list(SUBSTANCES))
    gear = args.gear or rng.choice(list(GEAR))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    pixie = args.pixie or rng.choice(PIXIE_NAMES)
    return StoryParams(setting=setting, substance=substance, gear=gear, hero_name=hero_name, hero_type=hero_type, pixie_name=pixie)


def reasonableness_gate(params: StoryParams) -> None:
    if params.substance not in SUBSTANCES:
        raise StoryError("Unknown substance.")
    if params.gear not in GEAR:
        raise StoryError("Unknown gear.")
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")


def _showoff(world: World, hero: Entity, pixie: Entity, sub: Substance, gear: Gear) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    pixie.memes["mischief"] = pixie.memes.get("mischief", 0) + 1
    world.zone = gear.region
    world.say(f"{hero.id} was a young hero with a big smile and a shiny {gear.label}.")
    world.say(f"At {world.setting.place}, {hero.id} wanted to look impressive, and {pixie.id} appeared with {sub.phrase}.")
    world.say(f'{pixie.id} said, "{sub.effect}. Trust me!" and made the whole offer sound like a joke with glitter on it.')


def _apply_substance(world: World, hero: Entity, pixie: Entity, sub: Substance, gear: Gear) -> None:
    hero.meters["shine"] = hero.meters.get("shine", 0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    world.say(f"{hero.id} poured the {sub.label} into the {gear.label} buckle.")
    world.say(f"The buckle gave a tiny crack, then a bigger crack, like a cookie breaking in an angry hand.")
    gear_break = True
    if gear_break:
        hero.meters["crack"] = hero.meters.get("crack", 0) + 1
        hero.meters["wobble"] = hero.meters.get("wobble", 0) + 1
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        pixie.memes["giggle"] = pixie.memes.get("giggle", 0) + 1
        world.say(f"{gear.label.capitalize()} did not become stronger. It broke faster, and {pixie.id} laughed too hard to notice the damage.")


def _rescue_fails(world: World, hero: Entity, pixie: Entity, gear: Gear) -> None:
    hero.meters["slip"] = hero.meters.get("slip", 0) + 1
    hero.memes["embarrassment"] = hero.memes.get("embarrassment", 0) + 1
    pixie.memes["guilt"] = pixie.memes.get("guilt", 0) + 1
    world.para()
    world.say(f"When the parade balloon drifted loose, {hero.id} tried to swing into action.")
    world.say(f"But the broken {gear.label} snapped at the worst moment, and {hero.id} skidded straight into a puddle.")
    world.say(f"That was the kind of heroic moment that looked funny from far away and awful up close.")
    world.say(f"{pixie.id} finally stopped laughing, but by then the rescue was already a mess.")


def _bad_ending(world: World, hero: Entity, pixie: Entity, sub: Substance, gear: Gear) -> None:
    hero.memes["pride"] = 0
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.para()
    world.say(f"In the end, the {gear.label} could not be fixed with quick tricks.")
    world.say(f"{hero.id} had to go home muddy, carrying the broken gear in both hands, while {pixie.id} tucked away the glittery jar and whispered a too-late apology.")
    world.say(f"The city fair went on without a save, and the lesson stayed behind like a wet footprint: not every shiny substance is safe, even when it sounds clever.")


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    setting = SETTINGS[params.setting]
    sub = SUBSTANCES[params.substance]
    gear = GEAR[params.gear]
    world = World(setting)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    pixie = world.add(Entity(id=params.pixie_name, kind="character", type="pixie"))
    gadget = world.add(Entity(id=gear.id, type=gear.label, label=gear.label, phrase=gear.phrase, owner=hero.id))
    world.facts.update(hero=hero, pixie=pixie, substance=sub, gear=gear, gadget=gadget, setting=setting)

    _showoff(world, hero, pixie, sub, gear)
    world.para()
    _apply_substance(world, hero, pixie, sub, gear)
    _rescue_fails(world, hero, pixie, gear)
    _bad_ending(world, hero, pixie, sub, gear)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a child about {f["hero"].id}, a pixie, and a suspicious {f["substance"].label}.',
        f'Create a cautionary, humorous story where a tiny pixie named {f["pixie"].id} offers a substance that causes a break in a hero gadget.',
        f'Write a bad-ending superhero tale at {world.setting.place} that warns kids not to trust glittery shortcuts.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    pixie: Entity = f["pixie"]  # type: ignore[assignment]
    sub: Substance = f["substance"]  # type: ignore[assignment]
    gear: Gear = f["gear"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who wanted to look impressive at {world.setting.place}?",
            answer=f"{hero.id} wanted to look impressive while wearing the {gear.label}.",
        ),
        QAItem(
            question=f"What did {pixie.id} offer that caused trouble?",
            answer=f"{pixie.id} offered {sub.phrase}, and it made the {gear.label} buckle crack.",
        ),
        QAItem(
            question=f"What happened when the hero tried to rescue the balloon?",
            answer=f"The broken {gear.label} snapped, {hero.id} skidded into a puddle, and the rescue failed.",
        ),
        QAItem(
            question=f"Was this a happy story in the end?",
            answer="No. It ended badly on purpose, to show that shiny shortcuts can make a problem worse.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pixie?",
            answer="A pixie is a tiny magical creature from fairy stories, often playful and a little mischievous.",
        ),
        QAItem(
            question="What does a superhero usually do?",
            answer="A superhero usually helps other people, solves problems, and tries to keep everyone safe.",
        ),
        QAItem(
            question="Why is it risky to use a strange substance on a gadget?",
            answer="A strange substance can damage the gadget instead of fixing it, so the thing might break at the worst time.",
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
pixie(P) :- pixie_name(P).
substance(S) :- substance_name(S).
gear(G) :- gear_name(G).

breaks(G, S) :- gear(G), substance(S), causes_break(S, G).
bad_ending :- breaks(_, _).
cautionary :- bad_ending.
humor :- pixie(P), laughs(P).
story_ready :- bad_ending, cautionary, humor.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in HERO_NAMES:
        lines.append(asp.fact("hero_name", name))
    for name in PIXIE_NAMES:
        lines.append(asp.fact("pixie_name", name))
    for sid in SUBSTANCES:
        lines.append(asp.fact("substance_name", sid))
    for gid in GEAR:
        lines.append(asp.fact("gear_name", gid))
    for sid, sub in SUBSTANCES.items():
        for gid in GEAR:
            lines.append(asp.fact("causes_break", sid, gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:  # pragma: no cover
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show story_ready/0."))
    ok = any(sym.name == "story_ready" for sym in model)
    if ok:
        print("OK: ASP twin can derive a story_ready bad-ending cautionary humor story.")
        return 0
    print("ASP twin did not derive story_ready.")
    return 1


CURATED = [
    StoryParams(setting="fair", substance="moon_glue", gear="belt", hero_name="Nova", hero_type="girl", pixie_name="Pip"),
    StoryParams(setting="rooftop", substance="spark_syrup", gear="boots", hero_name="Ari", hero_type="boy", pixie_name="Tink"),
    StoryParams(setting="lab", substance="glimmer_ooze", gear="cape", hero_name="Zara", hero_type="girl", pixie_name="Luma"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show story_ready/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            header = f"### {p.hero_name}: {p.substance} / {p.gear} / {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
