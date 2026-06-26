#!/usr/bin/env python3
"""
A standalone story world for a tiny superhero tale with flair, a centipede
transformation, and a bad ending.

The seed premise is:
- a flashy superhero-style character wants to show off their flair
- a strange centipede-themed device or spell transforms them
- the transformation goes wrong and ends badly

This file keeps the story small, classical, and state-driven.
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
# Registries
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HeroKind:
    key: str
    noun: str
    plural: bool = False


@dataclass(frozen=True)
class Setting:
    key: str
    name: str
    indoors: bool
    flair: str


@dataclass(frozen=True)
class Power:
    key: str
    name: str
    flair: str
    risk: str


@dataclass(frozen=True)
class Transformation:
    key: str
    name: str
    trigger: str
    result: str
    bad_end: str
    clue: str
    mess: str


HEROES = {
    "girl": HeroKind("girl", "girl"),
    "boy": HeroKind("boy", "boy"),
    "kid": HeroKind("kid", "kid"),
}

SETTINGS = {
    "rooftop": Setting("rooftop", "the rooftop", False, "high above the city"),
    "alley": Setting("alley", "the narrow alley", False, "between brick walls"),
    "lab": Setting("lab", "the superhero lab", True, "under bright lights"),
    "parade": Setting("parade", "the street parade", False, "under colorful banners"),
}

POWERS = {
    "spark": Power("spark", "spark bursts", "bright orange sparkles", "they can ignite anything dry"),
    "glide": Power("glide", "wind gliding", "silver swooshes", "they can slip too close to danger"),
    "shield": Power("shield", "force shields", "blue flashes", "they can block the wrong thing"),
}

TRANSFORMATIONS = {
    "centipede": Transformation(
        "centipede",
        "centipede transformation",
        trigger="a glittering centipede charm",
        result="a long centipede with many tiny legs",
        bad_end="stuck in the vents while the city cheered for someone else",
        clue="tiny shoes and a trail of glitter",
        mess="hundreds of little legs",
    ),
    "crawl": Transformation(
        "crawl",
        "crawl-critter transformation",
        trigger="a crawling hero serum",
        result="a crawling centipede-thing",
        bad_end="lost in the dark under the stage",
        clue="a shiver of legs and a dropped mask",
        mess="too many legs to control",
    ),
    "anthem": Transformation(
        "anthem",
        "anthem-to-insect transformation",
        trigger="a humming centipede amulet",
        result="a centipede-shaped hero no one could recognize",
        bad_end="forgotten by the crowd after the lights went out",
        clue="a strange buzzing in the cape",
        mess="a tangled cape and skittering feet",
    ),
}

NAMES = ["Nova", "Ruby", "Milo", "Aria", "Beck", "Luna", "Zane", "Iris"]


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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: Setting
    hero: Entity
    mentor: Entity
    power: Power
    transformation: Transformation
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    hero_kind: str
    power: str
    transformation: str
    name: str
    mentor: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Inline world logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    hero_kind = HEROES[params.hero_kind]
    power = POWERS[params.power]
    trans = TRANSFORMATIONS[params.transformation]

    hero = Entity(id=params.name, kind="character", type=hero_kind.key)
    mentor = Entity(id="mentor", kind="character", type=params.mentor, label=f"the {params.mentor}")
    world = World(setting=setting, hero=hero, mentor=mentor, power=power, transformation=trans)
    world.entities[hero.id] = hero
    world.entities[mentor.id] = mentor

    # state
    hero.memes["flair"] = 1
    hero.memes["pride"] = 1
    mentor.memes["worry"] = 1

    # Act 1
    world.say(
        f"{hero.id} was a little {hero_kind.noun} superhero with lots of flair, "
        f"and {hero.pronoun()} loved showing off {power.flair} at {setting.name}."
    )
    world.say(
        f"{mentor.label_word if hasattr(mentor, 'label_word') else mentor.label} watched closely, "
        f"because {power.risk} could turn a flashy day into trouble."
    )
    world.para()

    # Act 2
    world.say(
        f"One day, {hero.id} found {trans.trigger} tucked near the hero gear."
    )
    world.say(
        f"{hero.id} touched it just to look cool, and a {trans.mess} shiver ran through {hero.pronoun('possessive')} cape."
    )
    hero.meters["transformed"] = 1
    hero.meters["centipede"] = 1
    hero.memes["alarm"] = 1
    world.say(
        f"In a blink, {hero.id} changed into {trans.result}."
    )
    world.para()

    # Act 3: bad ending
    hero.meters["bad_ending"] = 1
    hero.memes["fear"] = 1
    hero.memes["lost"] = 1
    world.say(
        f"{hero.id} tried to call for help, but {trans.clue} made {hero.pronoun('possessive')} voice tiny and strange."
    )
    world.say(
        f"The hero team could not tell who was under the sparkly blur, and {hero.id} ended up {trans.bad_end}."
    )
    world.say(
        f"By nightfall, the city still had its heroes, but {hero.id} had lost {hero.pronoun('possessive')} flair, {hero.pronoun('possessive')} name, and the parade."
    )

    world.facts = {
        "hero": hero,
        "mentor": mentor,
        "power": power,
        "transformation": trans,
        "setting": setting,
        "bad_ending": True,
    }
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sk in SETTINGS:
        for hk in HEROES:
            for pk in POWERS:
                combos.append((sk, hk, pk))
    return combos


def explain_invalid(params: StoryParams) -> str:
    return "(No story: the chosen options do not make a believable superhero-flair centipede transformation tale.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- hero_kind(H).
setting(S) :- setting_name(S).
power(P) :- power_name(P).
trans(T) :- trans_name(T).

valid(S,H,P,T) :- setting(S), hero(H), power(P), trans(T).
bad_story(S,H,P,T) :- valid(S,H,P,T), centipede(T).
#show valid/4.
#show bad_story/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for k in SETTINGS:
        lines.append(asp.fact("setting_name", k))
    for k in HEROES:
        lines.append(asp.fact("hero_kind", k))
    for k in POWERS:
        lines.append(asp.fact("power_name", k))
    for k in TRANSFORMATIONS:
        lines.append(asp.fact("trans_name", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set((s, h, p, t) for s, h, p in valid_combos() for t in TRANSFORMATIONS)
    if clingo_set == python_set:
        print(f"OK: ASP matches Python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in ASP:", sorted(clingo_set - python_set))
    print("only in Python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a child with the word "flair" and a centipede transformation.',
        f"Tell a comic superhero story where {f['hero'].id} shows {f['power'].flair} at {f['setting'].name} and gets turned into a centipede.",
        f"Write a simple bad-ending superhero tale about {f['hero'].id}, {f['power'].name}, and a centipede charm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    power = f["power"]
    trans = f["transformation"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little superhero who loved showing off {power.flair} at {setting.name}.",
        ),
        QAItem(
            question=f"What caused the transformation?",
            answer=f"The transformation started when {hero.id} touched {trans.trigger}.",
        ),
        QAItem(
            question=f"What kind of ending did the story have?",
            answer=f"It had a bad ending, because {hero.id} became {trans.result} and ended up {trans.bad_end}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is flair?",
            answer="Flair is a showy, stylish way of doing something so it looks exciting and impressive.",
        ),
        QAItem(
            question="What is a centipede?",
            answer="A centipede is a long little animal with many legs.",
        ),
        QAItem(
            question="Why can transformations be scary in a superhero story?",
            answer="A transformation can be scary because it can change how someone moves, talks, or looks, and they may lose control.",
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


# ---------------------------------------------------------------------------
# Params resolution and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero flair + centipede transformation storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero-kind", choices=HEROES)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--name")
    ap.add_argument("--mentor", choices=["teacher", "guardian", "scientist"])
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
    hero_kind = args.hero_kind or rng.choice(list(HEROES))
    power = args.power or rng.choice(list(POWERS))
    transformation = args.transformation or rng.choice(list(TRANSFORMATIONS))
    name = args.name or rng.choice(NAMES)
    mentor = args.mentor or rng.choice(["teacher", "guardian", "scientist"])
    return StoryParams(setting=setting, hero_kind=hero_kind, power=power, transformation=transformation, name=name, mentor=mentor)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: meters={meters} memes={memes}")
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


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_bad_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show bad_story/4."))
    return sorted(set(asp.atoms(model, "bad_story")))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4.\n#show bad_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        stories = asp_valid_bad_stories()
        print(f"{len(stories)} bad superhero combos:")
        for item in stories[:50]:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            for hero_kind in HEROES:
                for power in POWERS:
                    for transformation in TRANSFORMATIONS:
                        params = StoryParams(
                            setting=setting,
                            hero_kind=hero_kind,
                            power=power,
                            transformation=transformation,
                            name=NAMES[(hash((setting, hero_kind, power, transformation)) % len(NAMES))],
                            mentor="scientist",
                            seed=base_seed,
                        )
                        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
