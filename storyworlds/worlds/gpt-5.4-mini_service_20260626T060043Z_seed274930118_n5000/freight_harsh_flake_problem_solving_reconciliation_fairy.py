#!/usr/bin/env python3
"""
A fairy-tale storyworld about a little courier, a harsh wind, and a freight
problem that gets solved through careful thinking and reconciliation.

The seed words here are freight, harsh, and flake.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "princess", "woman"}
        male = {"boy", "father", "king", "prince", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bridge"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Load:
    label: str
    phrase: str
    weight: str
    region: str
    fragile: bool = False
    plural: bool = False


@dataclass
class Weather:
    name: str
    mood: str
    mess: str
    danger: str


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    protects: set[str]
    deflects: set[str]
    worn_region: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting, weather: Weather):
        self.setting = setting
        self.weather = weather
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "bridge": Setting(place="the old bridge", indoors=False, affords={"crossing"}),
    "lane": Setting(place="the lantern lane", indoors=False, affords={"crossing"}),
    "harbor": Setting(place="the little harbor", indoors=False, affords={"crossing"}),
}

WEATHERS = {
    "harsh_wind": Weather(
        name="harsh wind",
        mood="harsh",
        mess="rattle",
        danger="could tip the freight",
    ),
    "snow_flake": Weather(
        name="snow flake",
        mood="soft",
        mess="slip",
        danger="could make the path slick",
    ),
    "mist": Weather(
        name="mist",
        mood="cool",
        mess="dampen",
        danger="could blur the road",
    ),
}

LOADS = {
    "freight_box": Load(
        label="freight box",
        phrase="a small freight box tied with blue twine",
        weight="heavy",
        region="hands",
        fragile=True,
    ),
    "freight_crate": Load(
        label="freight crate",
        phrase="a tiny freight crate with a stamped seal",
        weight="heavy",
        region="back",
        fragile=False,
    ),
    "feather_basket": Load(
        label="feather basket",
        phrase="a feather basket of palace ribbons",
        weight="light",
        region="hands",
        fragile=True,
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="cloak",
        label="a warm cloak",
        phrase="a warm cloak with a deep hood",
        protects={"back", "hands"},
        deflects={"harsh", "mist"},
        worn_region="back",
    ),
    Gear(
        id="boots",
        label="tall boots",
        phrase="tall boots with firm soles",
        protects={"feet"},
        deflects={"mist"},
        worn_region="feet",
        plural=True,
    ),
    Gear(
        id="gloves",
        label="soft gloves",
        phrase="soft gloves stitched with wool",
        protects={"hands"},
        deflects={"harsh", "mist"},
        worn_region="hands",
        plural=True,
    ),
]

NAMES = ["Ella", "Mina", "Toby", "Pip", "Nora", "Finn"]
ROLES = ["girl", "boy"]
CARETAKERS = {"girl": "queen", "boy": "king"}


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    weather: str
    load: str
    name: str
    role: str
    caretaker: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def load_at_risk(weather: Weather, load: Load) -> bool:
    return weather.mess in {"rattle", "slip", "dampen"} and load.fragile


def select_gear(weather: Weather, load: Load) -> Optional[Gear]:
    for gear in GEAR:
        if weather.mood in gear.deflects and load.region in gear.protects:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for w in WEATHERS:
            for l in LOADS:
                if load_at_risk(WEATHERS[w], LOADS[l]) and select_gear(WEATHERS[w], LOADS[l]):
                    combos.append((s, w, l))
    return combos


def explain_rejection(setting: str, weather: str, load: str) -> str:
    return (
        f"(No story: {weather} and {load} do not make a strong enough puzzle for "
        f"the courier at {SETTINGS[setting].place}. Try a fragile freight load "
        f"that the weather can truly trouble.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    weather = WEATHERS[params.weather]
    world = World(setting, weather)

    hero = world.add(Entity(id=params.name, kind="character", type=params.role))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=params.caretaker, label=params.caretaker))
    load_cfg = LOADS[params.load]
    load = world.add(Entity(
        id="Load",
        type=load_cfg.label,
        label=load_cfg.label,
        phrase=load_cfg.phrase,
        owner=hero.id,
        caretaker=caretaker.id,
        plural=load_cfg.plural,
    ))

    gear = None

    world.say(
        f"Once upon a time, {hero.id} was a little {hero.type} who carried "
        f"{load_cfg.phrase} for the palace."
    )
    world.say(
        f"{hero.id} loved the road, even when the air was {weather.name} and the day felt like a fairy-tale test."
    )

    world.para()
    world.say(
        f"On that day, {hero.id} reached {setting.place}, where the path was narrow and {weather.name} was waiting."
    )
    world.say(
        f"The {weather.mood} air could {weather.danger}, and {hero.id} could feel the freight tugging at {hero.pronoun('possessive')} arms."
    )

    world.facts.update(hero=hero, caretaker=caretaker, load=load, setting=setting, weather=weather)

    if load_at_risk(weather, load_cfg):
        hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
        world.say(
            f"{hero.id} frowned and said, 'I cannot let the freight fall.'"
        )
        world.say(
            f"{hero.id} looked for a clever way forward, because the road was harsh and the box was fragile."
        )
        gear = select_gear(weather, load_cfg)
        if gear:
            gear_ent = world.add(Entity(
                id=gear.id,
                type=gear.label,
                label=gear.label,
                phrase=gear.phrase,
                owner=hero.id,
                worn_by=hero.id,
                plural=gear.plural,
            ))
            world.facts["gear"] = gear_ent
            world.para()
            world.say(
                f"Then {hero.id} remembered {gear.phrase} in a satchel by the gate."
            )
            world.say(
                f"{hero.id} put it on, and the {weather.mood} wind could not bother the freight so easily."
            )
            hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1
            hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1
            caretaker.memes["pride"] = caretaker.memes.get("pride", 0.0) + 1
            load.meters["safe"] = 1.0
            world.say(
                f"{hero.id} crossed the bridge step by step, and the freight stayed safe in the soft shelter."
            )
            world.say(
                f"When {hero.id} reached the other side, {hero.pronoun('subject')} bowed to {caretaker.label} and smiled."
            )
            world.say(
                f"The {caretaker.label} smiled back, and the little courier felt the whole road grow gentle again."
            )
        else:
            raise StoryError(explain_rejection(params.setting, params.weather, params.load))
    else:
        load.meters["safe"] = 1.0
        world.say(
            f"Nothing troubled the freight that day, so {hero.id} crossed with calm steps and an easy heart."
        )

    world.para()
    world.say(
        f"In the end, the harshness did not win. {hero.id} had solved the problem with a wise choice."
    )
    world.say(
        f"The freight arrived whole, and the courier and the caretaker were reconciled in the lantern light."
    )
    world.say(
        f"The last thing anyone saw was a tiny traveler carrying freight, while the wind turned quiet and the path shone clear."
    )

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale about {f["hero"].id}, a little courier who must carry freight through a harsh place.',
        f"Tell a child-friendly story in which a {f['hero'].type} solves a freight problem and makes peace with the palace caretaker.",
        f"Write a short fairy tale using the words freight, harsh, and flake, with a clever solution at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    caretaker: Entity = f["caretaker"]
    load: Entity = f["load"]
    setting: Setting = f["setting"]
    weather: Weather = f["weather"]
    gear: Optional[Entity] = f.get("gear")

    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.type} who carried freight for the palace.",
        ),
        QAItem(
            question=f"What made the trip hard at {setting.place}?",
            answer=f"The trip was hard because the weather was {weather.name}, and that could trouble the freight.",
        ),
        QAItem(
            question=f"What was the important load in the story?",
            answer=f"The important load was {load.phrase}. {hero.id} wanted to keep it safe.",
        ),
        QAItem(
            question=f"Why did {hero.id} need to solve a problem?",
            answer=f"{hero.id} needed a solution because the freight was fragile and the harsh weather could shake it up.",
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"What helped {hero.id} protect the freight?",
                answer=f"{gear.label} helped, because it gave {hero.id} safer shelter on the road.",
            )
        )
    qa.append(
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the freight arriving safely and {hero.id} making peace with the caretaker.",
        )
    )
    return qa


WORLD_KNOWLEDGE = {
    "freight": (
        "What is freight?",
        "Freight is goods or cargo that people carry or ship from one place to another.",
    ),
    "harsh": (
        "What does harsh mean?",
        "Harsh means rough, strong, or unpleasant, like a very cold wind or a hard rule.",
    ),
    "flake": (
        "What is a flake?",
        "A flake is a tiny, thin piece that can fall from something, like a snow flake.",
    ),
    "cloak": (
        "What does a cloak do?",
        "A cloak is a piece of clothing you wear over your clothes to keep warm and dry.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    topics = {"freight", "harsh", "flake"}
    if world.facts.get("gear"):
        topics.add("cloak")
    return [QAItem(question=WORLD_KNOWLEDGE[t][0], answer=WORLD_KNOWLEDGE[t][1]) for t in WORLD_KNOWLEDGE if t in topics]


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid(S,W,L) :- setting(S), weather(W), load(L),
                fragile(L), at_risk(W,L), has_gear(W,L).

at_risk(harsh_wind, freight_box).
at_risk(harsh_wind, feather_basket).
at_risk(snow_flake, freight_box).
at_risk(snow_flake, feather_basket).
at_risk(mist, freight_box).
at_risk(mist, feather_basket).

has_gear(harsh_wind, freight_box) :- gear(cloak), gear_protects(cloak,hands), gear_deflects(cloak,harsh).
has_gear(harsh_wind, feather_basket) :- gear(cloak), gear_protects(cloak,hands), gear_deflects(cloak,harsh).
has_gear(snow_flake, freight_box) :- gear(gloves), gear_protects(gloves,hands), gear_deflects(gloves,harsh).
has_gear(snow_flake, feather_basket) :- gear(gloves), gear_protects(gloves,hands), gear_deflects(gloves,harsh).
has_gear(mist, freight_box) :- gear(gloves), gear_protects(gloves,hands), gear_deflects(gloves,mist).
has_gear(mist, feather_basket) :- gear(gloves), gear_protects(gloves,hands), gear_deflects(gloves,mist).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for w in WEATHERS:
        lines.append(asp.fact("weather", w))
        if w == "harsh_wind":
            lines.append(asp.fact("weather_tag", w, "harsh"))
        if w == "snow_flake":
            lines.append(asp.fact("weather_tag", w, "flake"))
    for l, load in LOADS.items():
        lines.append(asp.fact("load", l))
        if load.fragile:
            lines.append(asp.fact("fragile", l))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for p in g.protects:
            lines.append(asp.fact("gear_protects", g.id, p))
        for d in g.deflects:
            lines.append(asp.fact("gear_deflects", g.id, d))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid combos.")
        return 0
    print("Mismatch between ASP and Python:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about freight, harsh weather, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--load", choices=LOADS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    if args.setting and args.weather and args.load:
        if (args.setting, args.weather, args.load) not in combos:
            raise StoryError(explain_rejection(args.setting, args.weather, args.load))
    choices = [c for c in combos
               if (not args.setting or c[0] == args.setting)
               and (not args.weather or c[1] == args.weather)
               and (not args.load or c[2] == args.load)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    s, w, l = rng.choice(sorted(choices))
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(ROLES)
    caretaker = CARETAKERS[role]
    return StoryParams(setting=s, weather=w, load=l, name=name, role=role, caretaker=caretaker)


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


CURATED = [
    StoryParams(setting="bridge", weather="harsh_wind", load="freight_box", name="Ella", role="girl", caretaker="queen"),
    StoryParams(setting="lane", weather="snow_flake", load="feather_basket", name="Pip", role="boy", caretaker="king"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        vals = asp_valid()
        print(f"{len(vals)} valid combos:")
        for row in vals:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
