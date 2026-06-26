#!/usr/bin/env python3
"""
storyworlds/worlds/search_shelter_motley_cautionary_adventure.py
================================================================

A small cautionary adventure world about a child who searches for shelter
when the sky turns motley with weather.

Premise:
- A curious child goes out on a bright trail with a basket of odds and ends.
- The day shifts into motley weather: wind, drizzle, and hard rumbles mixed together.
- The child keeps searching for a safe shelter instead of staying put.
- A wise helper points out the danger, and the child learns to choose a real
  shelter before the weather gets worse.

This world keeps the story grounded in a live model:
- meters track physical state like soaked, tired, windblown, safe, and dry
- memes track emotional state like worry, courage, caution, relief, and trust

The prose is generated from simulated state, not from a frozen template.
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


# ---------------------------------------------------------------------------
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    location: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Weather:
    name: str
    description: str
    danger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Shelter:
    id: str
    label: str
    phrase: str
    cover: set[str]
    safe_from: set[str]
    reliable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    weather: str
    shelter: str
    hero_name: str
    hero_gender: str
    companion: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, weather: Weather) -> None:
        self.setting = setting
        self.weather = weather
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.path_state: str = "clear"
        self.searching: bool = False

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        c = World(self.setting, self.weather)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.path_state = self.path_state
        c.searching = self.searching
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the meadow", outdoors=True, affords={"trail", "trees"}),
    "harbor": Setting(place="the harbor path", outdoors=True, affords={"dock", "trail"}),
    "hill": Setting(place="the windy hill trail", outdoors=True, affords={"trail"}),
    "orchard": Setting(place="the orchard lane", outdoors=True, affords={"trees", "trail"}),
}

WEATHERS = {
    "motley": Weather(
        name="motley",
        description="The sky turned motley, with bright patches, gray clouds, and quick hard gusts all mixed together.",
        danger="the weather could change at any moment",
        tags={"wind", "rain", "storm", "weather", "motley"},
    ),
    "drizzle": Weather(
        name="drizzle",
        description="Soft drizzle drifted down in a thin, steady curtain.",
        danger="the ground could turn slick",
        tags={"rain", "wet", "weather"},
    ),
    "gusts": Weather(
        name="gusts",
        description="Sharp gusts hopped across the path and tugged at coats and hats.",
        danger="small things could fly away",
        tags={"wind", "weather"},
    ),
}

SHELTERS = {
    "cave": Shelter(
        id="cave",
        label="a little stone cave",
        phrase="a little stone cave under the hill",
        cover={"wind", "rain"},
        safe_from={"wind", "rain"},
        tags={"cave", "shelter"},
    ),
    "shed": Shelter(
        id="shed",
        label="an old shed",
        phrase="an old shed with a squeaky door",
        cover={"wind", "rain"},
        safe_from={"wind", "rain"},
        tags={"shed", "shelter"},
    ),
    "porch": Shelter(
        id="porch",
        label="a covered porch",
        phrase="a covered porch beside a white house",
        cover={"rain", "wind"},
        safe_from={"rain", "wind"},
        tags={"porch", "shelter"},
    ),
    "tent": Shelter(
        id="tent",
        label="a striped tent",
        phrase="a striped tent with bright patches sewn onto it",
        cover={"rain"},
        safe_from={"rain"},
        tags={"tent", "motley", "shelter"},
    ),
}

HERO_NAMES = ["Mina", "Toby", "Lena", "Owen", "Pia", "Milo", "Nora", "Ari"]
COMPANIONS = ["mother", "father", "aunt", "uncle"]
GENDERS = ["girl", "boy"]
TRAITS = ["curious", "brave", "careful", "lively", "stubborn"]


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(S) :- setting_fact(S).
weather(W) :- weather_fact(W).
shelter(X) :- shelter_fact(X).

dangerous(W, rain) :- weather_tag(W, rain).
dangerous(W, wind) :- weather_tag(W, wind).
dangerous(W, storm) :- weather_tag(W, storm).

covers(S, rain) :- shelter_covers(S, rain).
covers(S, wind) :- shelter_covers(S, wind).

searches_for_shelter(W, S) :- weather(W), shelter(S), shelter_safe(S, rain), shelter_safe(S, wind).
valid_story(Set, W, S) :- setting(Set), weather(W), shelter(S), searches_for_shelter(W, S).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_fact", sid))
        if s.outdoors:
            lines.append(asp.fact("outdoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for wid, w in WEATHERS.items():
        lines.append(asp.fact("weather_fact", wid))
        for t in sorted(w.tags):
            lines.append(asp.fact("weather_tag", wid, t))
    for sid, sh in SHELTERS.items():
        lines.append(asp.fact("shelter_fact", sid))
        for c in sorted(sh.cover):
            lines.append(asp.fact("shelter_covers", sid, c))
        for s in sorted(sh.safe_from):
            lines.append(asp.fact("shelter_safe", sid, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def safe_shelter_for(weather: Weather, shelter: Shelter) -> bool:
    return "rain" in shelter.safe_from and "wind" in shelter.safe_from


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for wid, weather in WEATHERS.items():
            for shid, shelter in SHELTERS.items():
                if safe_shelter_for(weather, shelter):
                    out.append((sid, wid, shid))
    return out


def explain_rejection(weather: Weather, shelter: Shelter) -> str:
    return (
        f"(No story: {shelter.label} is not a good shelter for {weather.name}. "
        f"A cautionary adventure needs a real place to hide from wind and rain.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def _act_search(world: World, hero: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["caution"] = hero.memes.get("caution", 0) + 0.2
    world.searching = True
    world.say(
        f"{hero.id} looked down the trail and searched for shelter while the day still felt safe."
    )


def _raise_weather(world: World, hero: Entity) -> None:
    if world.weather.name == "motley":
        hero.meters["windblown"] = hero.meters.get("windblown", 0) + 1
        hero.meters["wet"] = hero.meters.get("wet", 0) + 1
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        world.say(world.weather.description)
        world.say(
            f"By the time {hero.id} reached the path, {world.weather.danger}."
        )
    elif world.weather.name == "drizzle":
        hero.meters["wet"] = hero.meters.get("wet", 0) + 1
        hero.memes["worry"] = hero.memes.get("worry", 0) + 0.5
        world.say(world.weather.description)


def _danger_check(world: World, hero: Entity, shelter: Shelter) -> bool:
    if hero.meters.get("wet", 0) >= THRESHOLD or hero.meters.get("windblown", 0) >= THRESHOLD:
        hero.memes["worry"] = hero.memes.get("worry", 0) + 0.5
        world.facts["risk"] = True
        world.say(
            f"{hero.id} saw that the path was turning rough, and {hero.pronoun('possessive')} heart began to beat faster."
        )
        return True
    return False


def _wise_warning(world: World, helper: Entity, hero: Entity, shelter: Shelter) -> None:
    helper.memes["caution"] = helper.memes.get("caution", 0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    world.say(
        f"{helper.id} pointed at {shelter.phrase} and said, "
        f"\"Let's not keep searching in this motley weather. We need shelter now.\""
    )


def _reach_shelter(world: World, hero: Entity, shelter: Shelter) -> None:
    hero.location = shelter.id
    hero.meters["safe"] = hero.meters.get("safe", 0) + 1
    hero.meters["dry"] = hero.meters.get("dry", 0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0) - 1.0)
    world.say(
        f"They hurried into {shelter.label}. The rough wind stayed outside, and {hero.id} felt the air grow calm."
    )
    world.say(
        f"In that safe place, {hero.id} could breathe again, and the search for shelter finally ended."
    )


def tell(setting: Setting, weather: Weather, shelter: Shelter,
         hero_name: str = "Mina", hero_gender: str = "girl",
         companion: str = "mother") -> World:
    world = World(setting, weather)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_gender,
        meters={"safe": 0.0, "wet": 0.0, "windblown": 0.0, "dry": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "trust": 0.0, "relief": 0.0, "caution": 0.0},
    ))
    helper = world.add(Entity(id=companion, kind="character", type=companion, label=companion))
    hut = world.add(Entity(id=shelter.id, type="shelter", label=shelter.label, phrase=shelter.phrase))

    world.say(
        f"{hero.id} was a {hero.pronoun('subject')} who liked adventure and noticed every little path."
    )
    world.say(
        f"On a bright morning, {hero.id} and {hero.pronoun('possessive')} {helper.label_word} set out near {setting.place}."
    )
    world.para()
    _act_search(world, hero)
    _raise_weather(world, hero)
    world.say(
        f"{hero.id} kept searching, but the motley sky made the trail feel less friendly with every step."
    )
    danger = _danger_check(world, hero, hut)
    if danger:
        _wise_warning(world, helper, hero, hut)
    world.para()
    if danger:
        _reach_shelter(world, hero, hut)
    else:
        world.say(
            f"They reached {hut.phrase} before trouble began, and the day stayed easy."
        )

    world.facts.update(hero=hero, helper=helper, shelter=hut, setting=setting, weather=weather)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    return [
        f'Write a short cautionary adventure for a child named {hero.id} who searches for shelter in motley weather.',
        f"Tell a gentle story where {hero.id} keeps looking for a safe place while the sky turns motley.",
        f"Write a child-facing adventure about the word 'shelter' and end with the hero reaching safety.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    shelter: Entity = f["shelter"]
    weather: Weather = f["weather"]
    return [
        QAItem(
            question=f"What was {hero.id} looking for when the weather turned motley?",
            answer=f"{hero.id} was searching for shelter because the sky changed fast and the path started to feel unsafe.",
        ),
        QAItem(
            question=f"Who warned {hero.id} about the danger?",
            answer=f"{helper.id} warned {hero.id} and pointed out {shelter.phrase} as a safe place to go.",
        ),
        QAItem(
            question=f"What happened after {hero.id} reached {shelter.label}?",
            answer=f"{hero.id} got out of the wind, felt relief, and could rest safely while the motley weather stayed outside.",
        ),
        QAItem(
            question=f"Why did the adventure feel cautionary?",
            answer=f"It felt cautionary because the weather was mixed and sharp, and the story showed that {hero.id} needed to choose shelter before the trail became risky.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "shelter": [
        QAItem(
            question="What is shelter?",
            answer="Shelter is a safe place that helps protect you from wind, rain, or other rough weather.",
        )
    ],
    "weather": [
        QAItem(
            question="Why do people look for shelter when storms start?",
            answer="People look for shelter so they can stay dry and safe when the weather turns rough.",
        )
    ],
    "motley": [
        QAItem(
            question="What does motley mean?",
            answer="Motley means mixed up in many colors or many kinds, all jumbled together.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.weather.tags)
    tags.add("shelter")
    out: list[QAItem] = []
    for tag in ("motley", "weather", "shelter"):
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    lines.append(f"  path_state={world.path_state}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="hill", weather="motley", shelter="cave", hero_name="Mina", hero_gender="girl", companion="mother"),
    StoryParams(setting="orchard", weather="motley", shelter="porch", hero_name="Owen", hero_gender="boy", companion="father"),
    StoryParams(setting="meadow", weather="drizzle", shelter="shed", hero_name="Nora", hero_gender="girl", companion="aunt"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary adventure about searching for shelter in motley weather.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--shelter", choices=SHELTERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--companion", choices=COMPANIONS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.weather is None or c[1] == args.weather)
              and (args.shelter is None or c[2] == args.shelter)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, wid, shid = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(HERO_NAMES)
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(setting=sid, weather=wid, shelter=shid, hero_name=name, hero_gender=gender, companion=companion)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], WEATHERS[params.weather], SHELTERS[params.shelter],
                 params.hero_name, params.hero_gender, params.companion)
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


# ---------------------------------------------------------------------------
# ASP verify
# ---------------------------------------------------------------------------
def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible setting/weather/shelter combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.hero_name}: {p.setting} / {p.weather} / {p.shelter}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
