#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/arrogant_violence_death_repetition_bad_ending_folk.py
====================================================================================================

A small folk-tale storyworld about arrogance, violence, and death.
The world is intentionally narrow: a proud character is warned, repeats the
same harsh choice three times, and the ending is bad. The prose should feel
like a short warning tale told by a village elder.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    alive: bool = True

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the old village"
    season: str = "winter"
    affords: set[str] = field(default_factory=lambda: {"argue", "threaten", "strike"})


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    rival_name: str
    rival_type: str
    object_name: str
    object_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "village": Setting(place="the old village", season="winter"),
    "forest": Setting(place="the deep forest", season="autumn"),
    "river": Setting(place="the river bend", season="spring"),
}

HEROES = [
    ("Galen", "boy"),
    ("Mara", "girl"),
    ("Oren", "boy"),
    ("Tessa", "girl"),
]

RIVALS = [
    ("Bram", "boy"),
    ("Inga", "girl"),
    ("Nell", "girl"),
    ("Dain", "boy"),
]

OBJECTS = [
    ("bell", "thing"),
    ("lantern", "thing"),
    ("goat", "animal"),
    ("crown", "thing"),
]

TRAITS = ["arrogant", "proud", "haughty", "boastful"]


# ---------------------------------------------------------------------------
# Tale logic
# ---------------------------------------------------------------------------
def _hurt(world: World, actor: Entity, target: Entity) -> None:
    sig = ("hurt", actor.id, target.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    actor.memes["anger"] = actor.memes.get("anger", 0) + 1
    target.meters["hurt"] = target.meters.get("hurt", 0) + 1
    target.meters["blood"] = target.meters.get("blood", 0) + 1


def _death(world: World, target: Entity) -> None:
    sig = ("death", target.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    target.alive = False
    target.meters["death"] = 1
    target.meters["still"] = 1


def repeat_violence(world: World, hero: Entity, rival: Entity, obj: Entity) -> None:
    # repetition is a core narrative instrument: three harsh tries, each worse
    for n in range(1, 4):
        hero.memes["arrogance"] = hero.memes.get("arrogance", 0) + 1
        if n == 1:
            world.say(f"{hero.id} laughed and said, '{hero.id} is the strongest in {world.setting.place}.'")
            world.say(f"'{hero.id} will take {obj.label} by force,' {hero.pronoun()} said.")
        elif n == 2:
            world.say(f"Once more, {hero.id} raised a hand and tried to make {rival.id} yield.")
            world.say(f"Once more, {rival.id} begged {hero.pronoun('object')} to stop.")
        else:
            world.say(f"Still {hero.id} would not listen, and still {hero.id} struck again.")
        _hurt(world, hero, rival)
        rival.memes["fear"] = rival.memes.get("fear", 0) + 1


def resolve_bad_ending(world: World, hero: Entity, rival: Entity) -> None:
    if rival.meters.get("hurt", 0) >= 3:
        _death(world, rival)
        world.say(f"The village grew quiet, for {rival.id} fell still and did not rise again.")
        world.say(
            f"Only then did {hero.id} look at {hero.pronoun('possessive')} hands, "
            f"and only then did {hero.id} know the cost of {hero.memes.get('arrogance', 0):.0f} proud choices."
        )
        world.say(
            f"But it was too late. {rival.id} was gone, and the folk of {world.setting.place} "
            f"remembered the lesson with heavy hearts."
        )


def tell(setting: Setting, hero_name: str, hero_type: str, rival_name: str, rival_type: str,
         object_name: str, object_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type,
                            traits=["arrogant", "strong"], meters={}, memes={}))
    rival = world.add(Entity(id=rival_name, kind="character", type=rival_type,
                             traits=["kind"], meters={}, memes={}))
    obj = world.add(Entity(id=object_name, kind="thing", type=object_type,
                           label=object_name, phrase=f"the {object_name}"))

    world.say(
        f"Long ago, in {setting.place}, there lived {hero.id}, a {hero.traits[0]} {hero.type} who loved to boast."
    )
    world.say(
        f"Each morning {hero.id} would say, '{hero.id} is the greatest here,' and the villagers would shake their heads."
    )

    world.para()
    world.say(
        f"One day {hero.id} wanted {obj.phrase}, but {rival.id} would not hand it over."
    )
    world.say(
        f"{rival.id} said it should be shared, yet {hero.id} cared only for winning."
    )

    world.para()
    repeat_violence(world, hero, rival, obj)

    world.para()
    resolve_bad_ending(world, hero, rival)

    world.facts.update(hero=hero, rival=rival, obj=obj, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, rival, obj = f["hero"], f["rival"], f["obj"]
    return [
        f"Write a short folk tale about {hero.id}, a proud {hero.type}, who hurts {rival.id} over {obj.label} and learns a grim lesson.",
        f"Tell a warning story set in {world.setting.place} with repetition, violence, and a bad ending.",
        f"Write a simple village tale where someone keeps making the same cruel choice three times.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, rival, obj = f["hero"], f["rival"], f["obj"]
    return [
        QAItem(
            question=f"Who was the arrogant character in the story?",
            answer=f"The arrogant character was {hero.id}, who loved to boast and would not listen.",
        ),
        QAItem(
            question=f"What did {hero.id} want that started the trouble?",
            answer=f"{hero.id} wanted {obj.label}, and that made {hero.id} quarrel with {rival.id}.",
        ),
        QAItem(
            question=f"How many times did {hero.id} repeat the violent choice?",
            answer=f"{hero.id} repeated the harsh choice three times, and each time the trouble grew worse.",
        ),
        QAItem(
            question=f"What was the ending of the tale?",
            answer=f"The ending was bad: {rival.id} died, and the village was left with a sad lesson.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does arrogant mean?",
            answer="Arrogant means acting like you are better than everyone else and not listening to others.",
        ),
        QAItem(
            question="What is violence?",
            answer="Violence is hurting someone with force.",
        ),
        QAItem(
            question="What does death mean?",
            answer="Death means a living thing is no longer alive.",
        ),
        QAItem(
            question="Why do folk tales repeat the same action?",
            answer="Folk tales often repeat actions so the lesson is easy to remember.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id}: type={e.type} alive={e.alive} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/4.

valid_story(Place, Hero, Rival, Obj) :-
    setting(Place),
    hero(Hero),
    rival(Rival),
    object(Obj),
    arrogant(Hero),
    violent_pattern(Hero, Rival),
    bad_ending(Hero, Rival).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for h, _ in HEROES:
        lines.append(asp.fact("hero", h))
        lines.append(asp.fact("arrogant", h))
    for r, _ in RIVALS:
        lines.append(asp.fact("rival", r))
    for o, _ in OBJECTS:
        lines.append(asp.fact("object", o))
    lines.append(asp.fact("violent_pattern", "any", "any"))
    lines.append(asp.fact("bad_ending", "any", "any"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("only in Python:", sorted(py - asp_set))
    print("only in ASP:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in SETTINGS:
        for hero, _ in HEROES:
            for rival, _ in RIVALS:
                if hero == rival:
                    continue
                for obj, _ in OBJECTS:
                    combos.append((place, hero, rival, obj))
    return combos


def explain_rejection() -> str:
    return "(No story: this world is meant for an arrogant hero, a repeated violent choice, and a bad ending.)"


# ---------------------------------------------------------------------------
# Storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk tale world: arrogance, repeated violence, and a bad ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--rival")
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
    place = args.place or rng.choice(list(SETTINGS))
    hero_name, hero_type = rng.choice(HEROES)
    rival_name, rival_type = rng.choice(RIVALS)
    obj_name, obj_type = rng.choice(OBJECTS)

    if args.hero:
        hero_name = args.hero
    if args.rival:
        rival_name = args.rival
    if args.object:
        obj_name = args.object

    if hero_name == rival_name:
        raise StoryError("Hero and rival must be different characters.")
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        rival_name=rival_name,
        rival_type=rival_type,
        object_name=obj_name,
        object_type=obj_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        params.hero_name,
        params.hero_type,
        params.rival_name,
        params.rival_type,
        params.object_name,
        params.object_type,
    )
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid folk-tale story patterns:\n")
        for item in stories:
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("village", "Galen", "boy", "Bram", "boy", "bell", "thing"),
            StoryParams("forest", "Mara", "girl", "Inga", "girl", "lantern", "thing"),
            StoryParams("river", "Oren", "boy", "Nell", "girl", "goat", "animal"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
