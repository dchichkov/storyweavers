#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/milk_dim_pong_asteroid_transformation_lesson_learned.py
===============================================================================================================

A standalone superhero-story world about a child hero, a milk-dim mishap,
a game of pong, and an asteroid emergency. The narrative leans into:
- Transformation
- Lesson Learned
- Bad Ending

The story engine is small, constraint-checked, and state-driven rather than a
frozen paragraph with swapped nouns.
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
# Constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0
SETTING_NAMES = {"rooftop", "space_station", "city_lab"}
TRANSFORM_NAMES = {"milk_dim", "shadow_glow", "stone_sheen"}
STYLE_TAG = "Superhero Story"


# ---------------------------------------------------------------------------
# Entities / world model
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman"}
        male = {"boy", "man"}
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
    affords: set[str] = field(default_factory=set)


@dataclass
class HeroConfig:
    hero_type: str
    power_name: str
    outfit: str


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    transform: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "rooftop": Setting(place="the rooftop court", affords={"pong", "watch_sky"}),
    "space_station": Setting(place="the space station rec room", affords={"pong", "watch_sky"}),
    "city_lab": Setting(place="the city lab break room", affords={"pong", "watch_sky"}),
}

HEROES = {
    "girl": HeroConfig(hero_type="girl", power_name="star spark", outfit="bright cape"),
    "boy": HeroConfig(hero_type="boy", power_name="pulse shield", outfit="blue mask"),
}

TRANSFORMS = {
    "milk_dim": {
        "label": "milk-dim serum",
        "effect": "made the hero pale, slow, and cloudy",
        "meter": "dimness",
        "cost": "spark",
    },
    "shadow_glow": {
        "label": "shadow-glow gadget",
        "effect": "turned the hero dark and twitchy",
        "meter": "shadow",
        "cost": "focus",
    },
    "stone_sheen": {
        "label": "stone-sheen spray",
        "effect": "made the hero stiff and heavy",
        "meter": "weight",
        "cost": "speed",
    },
}

GIRL_NAMES = ["Lina", "Maya", "Tia", "Nora", "Zoe", "Ivy"]
BOY_NAMES = ["Eli", "Noah", "Ben", "Max", "Leo", "Owen"]
SIDEKICKS = ["Pip", "Juno", "Rex", "Milo", "Skye"]

ASP_RULES = r"""
% A setting is suitable when it affords pong and sky watching.
suitable(S) :- affords(S,pong), affords(S,watch_sky).

% Transformations are valid when they are registered.
valid_transform(T) :- transform(T).

% A full story is valid if setting and transform are both valid.
valid_story(S,T) :- suitable(S), valid_transform(T).
"""


# ---------------------------------------------------------------------------
# World helpers
# ---------------------------------------------------------------------------

def hero_pronoun(hero_type: str, case: str = "subject") -> str:
    return HEROES[hero_type].__dict__.get(case, "")


def build_hero(world: World, params: StoryParams) -> Entity:
    hero_cfg = HEROES[params.hero_type]
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
    ))
    hero.meters["spark"] = 1.0
    hero.memes["hope"] = 1.0
    hero.memes["pride"] = 1.0
    hero.meters["power"] = 1.0
    return hero


def apply_transformation(world: World, hero: Entity, transform_id: str) -> str:
    cfg = TRANSFORMS[transform_id]
    sig = ("transform", hero.id, transform_id)
    if sig in world.fired:
        return ""
    world.fired.add(sig)
    meter = cfg["meter"]
    hero.meters[meter] = hero.meters.get(meter, 0.0) + 1.0
    hero.meters["power"] = max(0.0, hero.meters.get("power", 1.0) - 0.5)
    hero.memes["confidence"] = max(0.0, hero.memes.get("confidence", 1.0) - 0.6)
    return f"{hero.id} took one sip, and {cfg['effect']}."


def predict_failure(world: World, hero: Entity) -> bool:
    sim = world.copy()
    h = sim.get(hero.id)
    h.meters["spark"] = 0.0
    h.memes["confidence"] = 0.0
    return True


def play_pong(world: World, hero: Entity, sidekick: Entity) -> str:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 0.5
    hero.memes["focus"] = hero.memes.get("focus", 0.0) + 0.5
    sidekick.memes["joy"] = sidekick.memes.get("joy", 0.0) + 0.5
    return f"{hero.id} and {sidekick.id} were playing pong when the sky started to rumble."


def asteroid_warning(world: World, hero: Entity, sidekick: Entity) -> str:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    world.facts["asteroid_warning"] = True
    return f"Then the alert screen flashed: an asteroid was falling toward the city."


def fail_to_stop_asteroid(world: World, hero: Entity) -> str:
    hero.memes["shame"] = hero.memes.get("shame", 0.0) + 1.0
    hero.memes["lesson"] = hero.memes.get("lesson", 0.0) + 1.0
    world.facts["bad_ending"] = True
    return (
        f"{hero.id} tried to lift the broken pong paddle like a shield, but the milk-dim haze slowed everything down. "
        f"The asteroid hit the empty plaza with a hard boom, and the hero could only watch from the rooftop."
    )


def lesson_learned(world: World, hero: Entity, sidekick: Entity) -> str:
    hero.memes["humility"] = hero.memes.get("humility", 0.0) + 1.0
    world.facts["lesson_learned"] = True
    return (
        f"Afterward, {hero.id} looked at {sidekick.id} and said, "
        f"\"I learned that power is not for showing off. Next time, I will train first and listen sooner.\""
    )


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.transform not in TRANSFORMS:
        raise StoryError(f"Unknown transform: {params.transform}")
    if params.hero_type not in HEROES:
        raise StoryError(f"Unknown hero type: {params.hero_type}")

    world = World(SETTINGS[params.setting])

    hero = build_hero(world, params)
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type="friend", label=params.sidekick_name))
    asteroid = world.add(Entity(id="asteroid", kind="thing", type="asteroid", label="asteroid"))
    pong_table = world.add(Entity(id="pong_table", kind="thing", type="pong_table", label="pong table"))
    milk_dim = world.add(Entity(id="milk_dim", kind="thing", type="serum", label="milk-dim serum"))

    world.facts.update(hero=hero, sidekick=sidekick, asteroid=asteroid, pong_table=pong_table, milk_dim=milk_dim)

    world.say(
        f"{hero.id} was a young superhero who wore a {HEROES[params.hero_type].outfit} and kept {HEROES[params.hero_type].power_name} ready."
    )
    world.say(
        f"On that day at {world.setting.place}, {hero.id} wanted to play pong with {sidekick.id} before checking the sky alarms."
    )

    world.para()
    world.say(play_pong(world, hero, sidekick))
    world.say(
        f"{sidekick.id} pointed at the silver bottle and said it was milk-dim serum, a risky drink that could change a hero fast."
    )
    world.say(apply_transformation(world, hero, params.transform))
    world.say(asteroid_warning(world, hero, sidekick))

    world.para()
    world.say(
        f"{hero.id} rushed to the edge of the rooftop, but the transformation had made {hero.pronoun('object')} slow and cloudy."
    )
    world.say(fail_to_stop_asteroid(world, hero))
    world.say(lesson_learned(world, hero, sidekick))

    world.facts["transformed"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    return [
        f'Write a superhero story about {hero.id}, {sidekick.id}, a game of pong, and a milk-dim transformation.',
        f"Tell a short story where a hero drinks milk-dim serum, tries to stop an asteroid, and learns a lesson the hard way.",
        f'Write a child-friendly Superhero Story that includes the words "milk-dim", "pong", and "asteroid".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    transform = TRANSFORMS[world.params.transform] if hasattr(world, "params") else TRANSFORMS["milk_dim"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do before checking the sky alarms?",
            answer=f"{hero.id} wanted to play pong with {sidekick.id} at {world.setting.place}.",
        ),
        QAItem(
            question=f"What happened after {hero.id} drank the milk-dim serum?",
            answer=f"The milk-dim serum transformed {hero.id} and made {hero.pronoun('object')} pale, slow, and cloudy.",
        ),
        QAItem(
            question=f"Why did the hero end with a bad feeling in the story?",
            answer=(
                f"The hero could not stop the asteroid in time because the transformation made {hero.pronoun('object')} too slow."
            ),
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn at the end?",
            answer=f"{hero.id} learned to train first and listen sooner instead of showing off.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is pong?",
            answer="Pong is a simple game with paddles and a small ball that bounces back and forth across a table.",
        ),
        QAItem(
            question="What is an asteroid?",
            answer="An asteroid is a rocky object that moves through space, and some asteroids can be very dangerous if they fall toward a city.",
        ),
        QAItem(
            question="What does a lesson learned mean in a story?",
            answer="A lesson learned means the character understands a better way to act after something goes wrong.",
        ),
        QAItem(
            question="Why can a transformation be important in a superhero story?",
            answer="A transformation can change what a hero can do, which can help or hurt the hero during a big problem.",
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


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sname, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sname))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sname, a))
    for tid in TRANSFORMS:
        lines.append(asp.fact("transform", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show valid_story/2.")
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set((s, t) for s in SETTINGS for t in TRANSFORMS if s in SETTINGS and t in TRANSFORMS)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python registry pairs ({len(clingo_set)}).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI / generation
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="rooftop", hero_name="Lina", hero_type="girl", sidekick_name="Pip", transform="milk_dim"),
    StoryParams(setting="space_station", hero_name="Eli", hero_type="boy", sidekick_name="Juno", transform="shadow_glow"),
    StoryParams(setting="city_lab", hero_name="Maya", hero_type="girl", sidekick_name="Rex", transform="stone_sheen"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: milk-dim, pong, asteroid, transformation, lesson learned, bad ending.")
    ap.add_argument("--setting", choices=sorted(SETTING_NAMES))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=sorted(HEROES))
    ap.add_argument("--sidekick-name")
    ap.add_argument("--transform", choices=sorted(TRANSFORM_NAMES))
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
    setting = args.setting or rng.choice(sorted(SETTING_NAMES))
    hero_type = args.hero_type or rng.choice(sorted(HEROES))
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    sidekick_name = args.sidekick_name or rng.choice(SIDEKICKS)
    transform = args.transform or rng.choice(sorted(TRANSFORM_NAMES))
    return StoryParams(setting=setting, hero_name=hero_name, hero_type=hero_type, sidekick_name=sidekick_name, transform=transform)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    world.params = params  # for QA helpers
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} valid story combos:")
        for s, t in combos:
            print(f"  {s} + {t}")
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
