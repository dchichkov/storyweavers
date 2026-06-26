#!/usr/bin/env python3
"""
storyworlds/worlds/fracas_hula_tostado_humor_dialogue_superhero_story.py
========================================================================

A compact superhero-style story world about a cheerful hero, a hula show,
a tostado snack, and a funny fracas that turns into a gentle rescue.

The seed story premise:
- A superhero team visits a festival.
- A playful fracas starts during a hula performance.
- One hero uses humor and dialogue to calm the crowd.
- The ending proves the city is safer, the snack is still tostado, and
  everyone laughs together.

This world models:
- physical meters: crowd chaos, spill, snack mess, saved order
- emotional memes: worry, pride, relief, joy, laughter

The prose is state-driven: the simulated world decides whether the fracas
happens, whether the hero fixes it, and which ending image is earned.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    label: str = ""
    type: str = "thing"
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    carried_by: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "heroine", "mother"}
        male = {"boy", "man", "hero", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoor: bool = False
    tag: str = "festival"


@dataclass
class HeroGear:
    label: str
    effect: str


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    villain_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "city_square": Place("the city square", indoor=False),
    "festival_stage": Place("the festival stage", indoor=False),
    "rooftop_garden": Place("the rooftop garden", indoor=False),
}

GEO = {
    "city_square": "city square",
    "festival_stage": "festival stage",
    "rooftop_garden": "rooftop garden",
}

GADGETS = {
    "laugh_ray": HeroGear(label="a laugh ray", effect="turn the fracas into giggles"),
    "hula_shield": HeroGear(label="a hula shield", effect="spin away the bumping crowd"),
}

NAMES = ["Ava", "Milo", "Zara", "Noah", "Iris", "Leo", "Maya", "Theo"]
VILLAINS = ["Grumble Mask", "Captain Clatter", "The Soggy Whisper", "Professor Poke"]
HERO_TYPES = ["hero", "heroine"]


@dataclass
class State:
    chaos: float = 0.0
    laughter: float = 0.0
    worry: float = 0.0
    relief: float = 0.0
    pride: float = 0.0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: humor, dialogue, hula, and a tostado fracas.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--sidekick")
    ap.add_argument("--villain")
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
    hero_name = args.name or rng.choice(NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    sidekick_name = args.sidekick or rng.choice([n for n in NAMES if n != hero_name])
    villain_name = args.villain or rng.choice(VILLAINS)
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, sidekick_name=sidekick_name, villain_name=villain_name)


def _safe_article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def introduce(world: World, hero: Entity, sidekick: Entity, villain: Entity) -> None:
    world.say(f"{hero.id} was a bright {hero.type} who protected {world.place.name} with a grin.")
    world.say(f"{sidekick.id} stayed close, because {sidekick.id} liked jokes almost as much as adventure.")
    world.say(f"Far across the {world.place.name}, {villain.id} watched the hula show with a sly little frown.")


def start_festival(world: World, hero: Entity) -> None:
    world.say(f"It was a sunny day at {world.place.name}, and a hula band was swaying under paper stars.")
    world.say(f"A vendor handed out {hero.memes.get('snack_name', 'a tostado')} and said, 'Keep your cape out of the salsa, please!'")


def trigger_fracas(world: World, villain: Entity, hero: Entity) -> None:
    state: State = world.facts["state"]
    state.chaos += 1.0
    state.worry += 1.0
    villain.meters["trouble"] = villain.meters.get("trouble", 0.0) + 1.0
    world.say(f"Then {villain.id} tossed a confetti net into the hula circle, and a fracas broke out.")
    world.say(f'"Hey!" shouted the crowd. "Not the hula floor!"')
    world.say(f"{hero.id} narrowed {hero.pronoun('possessive')} eyes and said, 'Nobody ruins a dance with confetti and bad manners.'")


def humor_turn(world: World, hero: Entity, sidekick: Entity) -> None:
    state: State = world.facts["state"]
    state.laughter += 1.0
    state.worry = max(0.0, state.worry - 0.5)
    world.say(f"{sidekick.id} pointed at the tangled net and said, 'That villain tied up the stage like a very dramatic spaghetti bowl.'")
    world.say(f"{hero.id} blinked, then laughed. 'A spaghetti bowl? Great. I know how to serve up justice.'")


def resolve(world: World, hero: Entity, sidekick: Entity, villain: Entity, gear: HeroGear) -> None:
    state: State = world.facts["state"]
    state.chaos = 0.0
    state.relief += 1.0
    state.pride += 1.0
    hero.meters["saved"] = hero.meters.get("saved", 0.0) + 1.0
    world.say(f"{hero.id} pressed {gear.label} to the floor and used it to spin the confetti net away from the hula dancers.")
    world.say(f'"Try a nicer hobby," {hero.id} said to {villain.id}, smiling. "Maybe knitting."')
    world.say(f'{villain.id} blinked. "I... I do like knitting," {villain.id} muttered, suddenly much less scary.')
    world.say(f"{sidekick.id} laughed so hard that even the tired band did too.")
    world.say(f"By the end, the hula dancers were twirling again, the tostado was still crisp, and {world.place.name} felt safe and shiny.")


def tell_story(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    world = World(SETTINGS[params.place])
    state = State()
    world.facts["state"] = state

    hero = world.add(Entity(id=params.hero_name, kind="character", label=params.hero_name, type=params.hero_type, meters={}, memes={}))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", label=params.sidekick_name, type="hero", meters={}, memes={}))
    villain = world.add(Entity(id=params.villain_name, kind="character", label=params.villain_name, type="man", meters={}, memes={}))

    hero.memes["snack_name"] = "a tostado"
    hero.memes["joy"] = 1.0
    sidekick.memes["humor"] = 1.0

    introduce(world, hero, sidekick, villain)
    world.para()
    start_festival(world, hero)
    trigger_fracas(world, villain, hero)
    world.para()
    humor_turn(world, hero, sidekick)
    gear = GADGETS["laugh_ray"] if world.place.name != "the rooftop garden" else GADGETS["hula_shield"]
    resolve(world, hero, sidekick, villain, gear)
    world.facts["hero"] = hero
    world.facts["sidekick"] = sidekick
    world.facts["villain"] = villain
    world.facts["gear"] = gear
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["hero"]
    return [
        f"Write a humorous superhero story with dialogue where {p.id} stops a fracas during a hula show.",
        f"Tell a child-friendly tale in which a tostado snack survives a superhero rescue in {world.place.name}.",
        f"Create a funny comic-style story about {p.id}, a hula performance, and a noisy fracas that ends well.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    villain = world.facts["villain"]
    state: State = world.facts["state"]
    return [
        QAItem(
            question=f"Who helped calm the fracas during the hula show?",
            answer=f"{hero.id} helped calm it, with {sidekick.id} adding jokes at just the right time.",
        ),
        QAItem(
            question=f"What did the crowd complain about when {villain.id} caused trouble?",
            answer="The crowd complained that the hula floor should stay clear, because the confetti net made a fracas.",
        ),
        QAItem(
            question=f"What snack stayed safe while the hero fixed the problem?",
            answer="The tostado stayed crisp and safe while the hero saved the show.",
        ),
        QAItem(
            question=f"How did the story end after the superhero team used humor?",
            answer=f"It ended with the dancers twirling again, the worry gone, and {world.place.name} feeling safe and bright.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is hula?",
            answer="Hula is a dance with smooth, swaying movements, often done to music and smiling faces.",
        ),
        QAItem(
            question="What is a fracas?",
            answer="A fracas is a noisy, messy fight or argument where lots of people get upset at once.",
        ),
        QAItem(
            question="What is a tostado?",
            answer="A tostado is something toasted until it is crisp, like bread or a simple snack with a crunchy bite.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    state: State = world.facts["state"]
    lines.append(f"place={world.place.name}")
    lines.append(f"state chaos={state.chaos} laughter={state.laughter} worry={state.worry} relief={state.relief} pride={state.pride}")
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
fracas_started :- villain_trouble.
humor_helps :- joke_spoken.
resolved :- fracas_started, humor_helps.
safe_end :- resolved.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("villain_trouble"),
        asp.fact("joke_spoken"),
        asp.fact("hula_show"),
        asp.fact("tostado"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe_end/0."))
    ok = any(sym.name == "safe_end" for sym in model)
    if ok:
        print("OK: ASP twin predicts a safe ending.")
        return 0
    print("MISMATCH: ASP twin failed to derive safe_end.")
    return 1


def asp_valid_story() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolved/0."))
    return [()] if any(sym.name == "resolved" for sym in model) else []


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
    StoryParams(place="city_square", hero_name="Ava", hero_type="heroine", sidekick_name="Milo", villain_name="Captain Clatter"),
    StoryParams(place="festival_stage", hero_name="Leo", hero_type="hero", sidekick_name="Iris", villain_name="Grumble Mask"),
    StoryParams(place="rooftop_garden", hero_name="Maya", hero_type="heroine", sidekick_name="Theo", villain_name="Professor Poke"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def resolve_all(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_end/0."))
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
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} at {p.place} against {p.villain_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
