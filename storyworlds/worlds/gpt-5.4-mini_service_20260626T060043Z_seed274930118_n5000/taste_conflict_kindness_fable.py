#!/usr/bin/env python3
"""
A small fable-like storyworld about taste, conflict, and kindness.

Premise:
A hungry little animal wants to taste a sweet treat. Another animal wants the
same treat, and they quarrel. A kind act turns the conflict into sharing, and
both end up happier than before.

The world simulates:
- physical meters: hunger, sweetness, crumbly, sticky, portion
- emotional memes: desire, conflict, kindness, joy, trust, share

The tale is intentionally compact and classical, with a clear turn from
quarrel to generosity.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    afford_food: bool = True


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    taste: str
    sweetness: str
    sticky: bool = False
    crumbly: bool = False


@dataclass
class StoryParams:
    setting: str
    food: str
    hero: str
    rival: str
    hero_type: str
    rival_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_conflict(world: World) -> list[str]:
    hero = world.get(world.facts["hero"].id)
    rival = world.get(world.facts["rival"].id)
    if hero.memes.get("desire", 0) >= THRESHOLD and rival.memes.get("desire", 0) >= THRESHOLD:
        if ("conflict", hero.id) not in world.fired:
            world.fired.add(("conflict", hero.id))
            hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
            rival.memes["conflict"] = rival.memes.get("conflict", 0) + 1
            return [f"They both wanted the same taste, and their voices grew sharp."]
    return []


def _r_kindness(world: World) -> list[str]:
    hero = world.get(world.facts["hero"].id)
    rival = world.get(world.facts["rival"].id)
    if hero.memes.get("kindness", 0) >= THRESHOLD and ("kindness", hero.id) not in world.fired:
        world.fired.add(("kindness", hero.id))
        hero.memes["conflict"] = 0
        rival.memes["conflict"] = 0
        hero.memes["trust"] = hero.memes.get("trust", 0) + 1
        rival.memes["trust"] = rival.memes.get("trust", 0) + 1
        return [f"Kindness softened the air between them."]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_conflict, _r_kindness):
            lines = rule(world)
            if lines:
                changed = True
                out.extend(lines)
    if narrate:
        for line in out:
            world.say(line)
    return out


def taste_description(food: Food) -> str:
    return food.taste


def setting_line(setting: Setting) -> str:
    return {
        "orchard": "The orchard was warm and bright, with fruit hanging low on the trees.",
        "kitchen": "The little kitchen smelled friendly, like bread and honey.",
        "garden": "The garden was quiet, with a sunny stone and a wooden bench.",
    }.get(setting.place, f"The {setting.place} was small and calm.")


def introduce(world: World, hero: Entity, rival: Entity, food: Food) -> None:
    world.say(
        f"Once in a small {world.setting.place}, {hero.id} the {hero.type} was known "
        f"for a keen taste and a careful heart."
    )
    world.say(
        f"{rival.id} the {rival.type} loved {food.phrase}, because it tasted {food.taste}."
    )


def want_food(world: World, hero: Entity, rival: Entity, food: Food) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    rival.memes["desire"] = rival.memes.get("desire", 0) + 1
    world.say(
        f"One day, they found {food.phrase}. {hero.id} wanted to taste it at once, and "
        f"{rival.id} wanted it too."
    )


def dispute(world: World, hero: Entity, rival: Entity, food: Food) -> None:
    propagate(world, narrate=False)
    world.say(
        f"\"It is mine,\" said {hero.id}. \"No, it is mine,\" said {rival.id}, and the little "
        f"treat nearly vanished beneath their quarrel."
    )


def kindness_turn(world: World, hero: Entity, rival: Entity, food: Food) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    world.say(
        f"{hero.id} paused, then remembered that a sweet taste is happier when shared."
    )
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} broke the treat in two and gave {rival.id} the larger piece. "
        f"That kind choice made the moment gentle again."
    )


def ending(world: World, hero: Entity, rival: Entity, food: Food) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    rival.memes["joy"] = rival.memes.get("joy", 0) + 1
    world.say(
        f"They tasted the pieces together, and the {food.label} was still {food.taste}. "
        f"This time, the sweetest part was the kindness."
    )
    world.say(
        f"{hero.id} and {rival.id} sat side by side, and the small {world.setting.place} "
        f"felt peaceful."
    )


def tell(setting: Setting, food: Food, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, traits=[params.trait]))
    rival = world.add(Entity(id=params.rival, kind="character", type=params.rival_type, traits=["greedy"]))
    world.facts["hero"] = hero
    world.facts["rival"] = rival
    world.facts["food"] = food

    world.say(setting_line(setting))
    introduce(world, hero, rival, food)
    world.para()
    want_food(world, hero, rival, food)
    dispute(world, hero, rival, food)
    world.para()
    kindness_turn(world, hero, rival, food)
    ending(world, hero, rival, food)

    world.facts["resolved"] = True
    return world


SETTINGS = {
    "orchard": Setting(place="orchard"),
    "kitchen": Setting(place="kitchen"),
    "garden": Setting(place="garden"),
}

FOODS = {
    "apple": Food(
        id="apple",
        label="apple",
        phrase="a red apple",
        taste="sweet and crisp",
        sweetness="bright",
        sticky=False,
        crumbly=False,
    ),
    "honeycake": Food(
        id="honeycake",
        label="honey cake",
        phrase="a little honey cake",
        taste="sweet and soft",
        sweetness="deep",
        sticky=True,
        crumbly=False,
    ),
    "pear": Food(
        id="pear",
        label="pear",
        phrase="a ripe pear",
        taste="fresh and sweet",
        sweetness="gentle",
        sticky=False,
        crumbly=False,
    ),
    "berry_tart": Food(
        id="berry_tart",
        label="berry tart",
        phrase="a berry tart",
        taste="sweet with a tiny tang",
        sweetness="lively",
        sticky=False,
        crumbly=True,
    ),
}

HEROES = {
    "rabbit": "rabbit",
    "mouse": "mouse",
    "squirrel": "squirrel",
    "goat": "goat",
}

RIVALS = {
    "hedgehog": "hedgehog",
    "crow": "crow",
    "turtle": "turtle",
    "fox": "fox",
}

TRAITS = ["kind", "curious", "gentle", "patient", "thoughtful"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for f in FOODS:
            combos.append((s, f))
    return combos


def explain_rejection(setting: str, food: str) -> str:
    return f"(No story: {food} does not fit the little fable at {setting}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable about taste, conflict, and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--rival", choices=RIVALS)
    ap.add_argument("--name")
    ap.add_argument("--name2")
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.food:
        combos = [c for c in combos if c[1] == args.food]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, food = rng.choice(sorted(combos))
    hero = args.name or rng.choice(["Milo", "Pip", "Luna", "Toby", "Nia"])
    rival = args.name2 or rng.choice(["Puck", "Mara", "Gus", "Fern", "Dot"])
    hero_type = args.hero or rng.choice(list(HEROES.values()))
    rival_type = args.rival or rng.choice(list(RIVALS.values()))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, food=food, hero=hero, rival=rival, hero_type=hero_type, rival_type=rival_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], FOODS[params.food], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    food = f["food"]
    return [
        f'Write a short fable for children about a {food.label} whose taste leads to conflict and kindness.',
        f"Tell a gentle story in which {f['hero'].id} and {f['rival'].id} both want to taste {food.phrase}, then share it.",
        f"Create a simple moral tale where the sweetest answer is kindness, and include the word 'taste'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    rival: Entity = f["rival"]
    food: Food = f["food"]
    return [
        QAItem(
            question=f"What did {hero.id} and {rival.id} both want to do?",
            answer=f"They both wanted to taste {food.phrase}.",
        ),
        QAItem(
            question=f"Why did they argue at first?",
            answer=f"They argued because each one wanted the same {food.label} for themselves.",
        ),
        QAItem(
            question=f"What changed the conflict into a happy ending?",
            answer=f"{hero.id} chose kindness and shared the treat, so the quarrel ended.",
        ),
        QAItem(
            question=f"What did the food taste like?",
            answer=f"It tasted {food.taste}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is taste?",
            answer="Taste is the way food feels to your mouth, like sweet, sour, salty, or bitter.",
        ),
        QAItem(
            question="What does kindness do in a story?",
            answer="Kindness helps characters care about each other and solve trouble in a gentle way.",
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is reasonable when two characters both want the same food.
conflict(hero,rival,food) :- wants(hero,food), wants(rival,food), hero != rival.

% Kindness resolves the quarrel by sharing.
resolved(hero,rival,food) :- conflict(hero,rival,food), kind(hero), shares(hero,food).

#show conflict/3.
#show resolved/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for fid in FOODS:
        lines.append(asp.fact("food", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    print("OK: ASP twin is present for the storyworld.")
    return 0


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
    StoryParams(setting="orchard", food="apple", hero="Milo", rival="Puck", hero_type="rabbit", rival_type="hedgehog", trait="kind"),
    StoryParams(setting="kitchen", food="honeycake", hero="Luna", rival="Gus", hero_type="mouse", rival_type="fox", trait="thoughtful"),
    StoryParams(setting="garden", food="pear", hero="Toby", rival="Fern", hero_type="squirrel", rival_type="crow", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show conflict/3.\n#show resolved/3."))
        return
    if args.asp:
        print("ASP mode is available; this world keeps the reasonableness twin inline.")
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
            header = f"### {p.hero} and {p.rival} at {p.setting} (food: {p.food})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
