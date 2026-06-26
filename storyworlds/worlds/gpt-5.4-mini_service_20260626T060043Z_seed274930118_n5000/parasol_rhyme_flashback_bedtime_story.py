#!/usr/bin/env python3
"""
storyworlds/worlds/parasol_rhyme_flashback_bedtime_story.py
===========================================================

A tiny bedtime-style storyworld about a child, a parasol, and a memory that
teaches how to use it well.

Premise:
- A child loves a pretty parasol.
- A breeze or drizzle makes the parasol useful, but only if it is held right.
- A flashback reveals a lesson from a kindly helper.
- A gentle rhyme helps the child remember the safe, cheerful solution.

The world is intentionally small and constraint-checked: the parasol matters,
the weather matters, and the ending proves the child learned something useful.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "aunt", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the garden"
    indoor: bool = False
    breeze: str = "soft"


@dataclass
class Weather:
    name: str
    wet: bool
    windy: bool
    sky: str


@dataclass
class StoryParams:
    setting: str
    weather: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, weather: Weather):
        self.setting = setting
        self.weather = weather
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, breeze="soft"),
    "porch": Setting(place="the porch", indoor=False, breeze="gentle"),
    "path": Setting(place="the little path", indoor=False, breeze="sleepy"),
}

WEATHERS = {
    "drizzle": Weather(name="drizzle", wet=True, windy=False, sky="gray"),
    "breeze": Weather(name="breeze", wet=False, windy=True, sky="blue"),
    "evening_rain": Weather(name="evening rain", wet=True, windy=True, sky="silver"),
}

HERO_NAMES = ["Mia", "Lily", "Nora", "Ben", "Theo", "Ava", "Finn", "Zoe"]
HELPER_TYPES = {
    "grandmother": "grandmother",
    "mother": "mother",
    "father": "father",
    "aunt": "aunt",
}

TRAITS = ["gentle", "curious", "sleepy", "cheerful", "small", "brave"]


@dataclass
class Parasol:
    label: str = "parasol"
    phrase: str = "a bright little parasol"
    color: str = "yellow"
    can_guard: bool = True


PARASOL = Parasol()


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def story_is_reasonable(params: StoryParams) -> bool:
    if params.setting not in SETTINGS:
        return False
    if params.weather not in WEATHERS:
        return False
    weather = WEATHERS[params.weather]
    # Parasol stories need something for the parasol to do: rain or wind.
    return weather.wet or weather.windy


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    weather = WEATHERS[params.weather]
    world = World(setting, weather)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_gender,
        traits=["little", random.choice(TRAITS)],
        meters={"joy": 0.0, "soaked": 0.0},
        memes={"wonder": 1.0, "worry": 0.0, "memory": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        traits=["kind", "steady"],
        meters={"care": 1.0},
        memes={"warmth": 1.0},
    ))
    parasol = world.add(Entity(
        id="parasol",
        kind="thing",
        type="parasol",
        label=PARASOL.label,
        phrase=PARASOL.phrase,
        owner=hero.id,
        caretaker=helper.id,
        worn_by=hero.id,
        meters={"dry": 1.0},
    ))

    world.facts.update(hero=hero, helper=helper, parasol=parasol)
    return world


def intro(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    parasol: Entity = world.facts["parasol"]
    world.say(
        f"Little {hero.id} had {parasol.phrase}, and {hero.id} liked to twirl it "
        f"as if it were a flower that could float."
    )
    world.say(
        f"{helper.id}, {hero.pronoun('possessive')} {helper.type}, said it was "
        f"for shade, for drops, and for days when the sky felt wide."
    )


def rhyme_line(hero: Entity, weather: Weather) -> str:
    if weather.wet and weather.windy:
        return f"Up went the parasol, nice and slow; down came the drops in a merry row."
    if weather.wet:
        return f"Tip the parasol, hold it high; keep the raindrops out of your eye."
    return f"Spin the parasol, soft and light; make the shy blue evening bright."


def flashback(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    world.say(
        f"Then {hero.id} remembered something from before: once, on a breezy day, "
        f"{helper.id} had shown {hero.pronoun('object')} how to hold the parasol with "
        f"both hands so the wind would not flip it like a startled kite."
    )
    world.say(
        f"That little lesson came back like a lantern in the dark, warm and clear."
    )
    hero.memes["memory"] += 1.0


def tension(world: World) -> None:
    hero: Entity = world.facts["hero"]
    weather: Weather = world.weather
    if weather.windy:
        hero.memes["worry"] += 1.0
        world.say(
            f"The breeze gave a playful tug, and the parasol began to wobble. "
            f"{hero.id} blinked, because one wrong twist could send it spinning away."
        )
    if weather.wet:
        hero.meters["soaked"] += 0.5
        world.say(
            f"Soft drops tapped the ground, so the parasol had to stay close and steady."
        )


def choice(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    weather: Weather = world.weather
    parasol: Entity = world.facts["parasol"]

    if weather.windy:
        world.say(
            f"{helper.id} crouched beside {hero.id} and said, "
            f"“Hands at the handle, feet on the ground, and the parasol stays round.”"
        )
        world.say(
            f"{hero.id} listened, held on tight, and the wobble grew small."
        )
        hero.memes["worry"] = 0.0
    if weather.wet:
        parasol.meters["dry"] += 1.0
        hero.meters["soaked"] = max(0.0, hero.meters["soaked"] - 0.5)
        hero.meters["joy"] += 1.0
        world.say(
            f"The parasol made a tiny roof above {hero.id}, and the drops slid away "
            f"like silver beads on a leaf."
        )


def ending(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    world.say(
        f"{hero.id} smiled and hummed the lesson back: "
        f"“Hold it low, then hold it true; the parasol will shelter you.”"
    )
    world.say(
        f"And that was the bedtime kind of magic: {helper.id} walked beside {hero.id}, "
        f"the sky stayed soft, and the parasol stayed open and calm."
    )


def tell(params: StoryParams) -> World:
    world = make_world(params)
    intro(world)
    world.para()
    world.say(f"It was {world.weather.name} at {world.setting.place}, with the sky {world.weather.sky} and the air {world.setting.breeze}.")
    world.say(rhyme_line(world.facts["hero"], world.weather))
    flashback(world)
    tension(world)
    choice(world)
    world.para()
    ending(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    weather: Weather = world.weather
    return [
        f"Write a bedtime story about {hero.id} and a parasol on a {weather.name} day.",
        f"Tell a gentle story where {helper.id} reminds {hero.id} how to hold a parasol safely in the wind.",
        "Make the story include a small flashback and a little rhyme.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    weather: Weather = world.weather
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about little {hero.id}, who learns how to use a parasol on a {weather.name} day.",
        ),
        QAItem(
            question=f"What did {helper.id} teach {hero.id} in the flashback?",
            answer=f"{helper.id} taught {hero.id} to hold the parasol with both hands so the wind would not flip it away.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"By the end, {hero.id} felt calm and happy, and the parasol stayed open and useful instead of wobbling.",
        ),
    ]
    if weather.windy:
        qa.append(
            QAItem(
                question="Why was the parasol tricky at first?",
                answer="It was tricky because the breeze tugged at it, so the child had to hold it carefully.",
            )
        )
    if weather.wet:
        qa.append(
            QAItem(
                question="How did the parasol help with the drops?",
                answer="It made a tiny roof above the child, so the drops slid away instead of landing on the child.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parasol for?",
            answer="A parasol is a light umbrella made to give shade and help keep off sun or gentle rain.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that remembers something that happened before the current moment.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like light and night.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(garden).
setting(porch).
setting(path).

weather(drizzle).
weather(breeze).
weather(evening_rain).

uses_parasol(drizzle).
uses_parasol(breeze).
uses_parasol(evening_rain).

valid_story(S, W) :- setting(S), weather(W), uses_parasol(W).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for w in WEATHERS:
        lines.append(asp.fact("weather", w))
    for w, obj in WEATHERS.items():
        if obj.wet or obj.windy:
            lines.append(asp.fact("uses_parasol", w))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid_combos() -> list[tuple]:
    out = []
    for s in SETTINGS:
        for w, obj in WEATHERS.items():
            if obj.wet or obj.windy:
                out.append((s, w))
    return sorted(out)


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(python_valid_combos())
    if a == b:
        print(f"OK: clingo gate matches python gate ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    if a - b:
        print("only in ASP:", sorted(a - b))
    if b - a:
        print("only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld about a parasol, rhyme, and flashback.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--weather", choices=sorted(WEATHERS))
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=sorted(HELPER_TYPES))
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    weather = args.weather or rng.choice(list(WEATHERS))
    if not story_is_reasonable(StoryParams(setting, weather, "", "", "", "")):
        raise StoryError("This story needs weather that gives the parasol something to do.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(list(HELPER_TYPES))
    return StoryParams(
        setting=setting,
        weather=weather,
        hero_name=name,
        hero_gender=gender,
        helper_name={"mother": "Mom", "father": "Dad", "grandmother": "Grandma", "aunt": "Auntie"}[helper],
        helper_type=helper,
    )


def generate(params: StoryParams) -> StorySample:
    if not story_is_reasonable(params):
        raise StoryError("Invalid setting/weather combination for a parasol story.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} ({e.kind:9}) type={e.type} "
            f"meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"  setting={world.setting.place}")
    lines.append(f"  weather={world.weather.name}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
    StoryParams(setting="garden", weather="drizzle", hero_name="Mia", hero_gender="girl", helper_name="Grandma", helper_type="grandmother"),
    StoryParams(setting="porch", weather="breeze", hero_name="Ben", hero_gender="boy", helper_name="Mom", helper_type="mother"),
    StoryParams(setting="path", weather="evening_rain", hero_name="Ava", hero_gender="girl", helper_name="Auntie", helper_type="aunt"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid setting/weather combinations:\n")
        for s, w in combos:
            print(f"  {s:8} {w}")
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
                p = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
            header = f"### {p.hero_name} at {p.setting} in {p.weather}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
