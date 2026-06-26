#!/usr/bin/env python3
"""
A small humorous fable storyworld about honey, patience, and a clever turn.

The seed premise:
A hungry animal wants honey too quickly, makes a funny mess, and learns a
better way after a warning from a wiser helper.

This world keeps the prose child-facing and fable-like:
- short setup
- a comic problem
- a sensible turn
- a tidy ending with a small moral image
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"hungry": 0.0, "sticky": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "pride": 0.0, "conflict": 0.0, "curiosity": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        male = {"bear", "fox", "rabbit", "badger"}
        female = {"bee", "owl"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the sunny meadow"
    affords: set[str] = field(default_factory=lambda: {"honey"})


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    mess: str
    taste: str
    risk_zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class CharacterSpec:
    type: str
    label: str
    traits: list[str]


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


@dataclass
class StoryParams:
    setting: str
    hero: str
    helper: str
    food: str
    mood: str
    seed: Optional[int] = None


SETTINGS = {
    "meadow": Setting(place="the sunny meadow", affords={"honey"}),
    "orchard": Setting(place="the old orchard", affords={"honey"}),
    "grove": Setting(place="the quiet grove", affords={"honey"}),
}

FOODS = {
    "honey": Food(
        id="honey",
        label="honey",
        phrase="a little jar of golden honey",
        mess="sticky",
        taste="sweet",
        risk_zone={"mouth", "paws"},
        tags={"honey", "sweet", "sticky"},
    )
}

HEROES = {
    "bear": CharacterSpec(type="bear", label="bear", traits=["hungry", "cheerful"]),
    "fox": CharacterSpec(type="fox", label="fox", traits=["quick", "sly"]),
    "rabbit": CharacterSpec(type="rabbit", label="rabbit", traits=["small", "careful"]),
}

HELPERS = {
    "bee": CharacterSpec(type="bee", label="bee", traits=["wise", "busy"]),
    "owl": CharacterSpec(type="owl", label="owl", traits=["wise", "calm"]),
}

MOODS = ["greedy", "impatient", "gloomy", "glad"]

KNOWLEDGE = {
    "honey": [
        (
            "What is honey?",
            "Honey is a thick, sweet food made by bees from flower nectar. It is sticky and golden.",
        ),
        (
            "Why do bees make honey?",
            "Bees make honey to store sweet food for later, especially when flowers are hard to find.",
        ),
    ],
    "sticky": [
        (
            "What does sticky mean?",
            "Sticky means something clings to your skin or hands and is hard to wipe off quickly.",
        )
    ],
    "sweet": [
        (
            "What does sweet mean?",
            "Sweet is a taste like sugar or honey, and many children think it is very nice.",
        )
    ],
}


ASP_RULES = r"""
has_treat(F) :- food(F).
wants_fast(H, F) :- hungry(H), food(F), sweet(F).
makes_mess(H, F) :- wants_fast(H, F), sticky(F).
has_fix(H, F) :- wise_helper(X), warns(X, H, F), shares(X, H, F).
good_story(H, F) :- makes_mess(H, F), has_fix(H, F).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for fid, food in FOODS.items():
        lines.append(asp.fact("food", fid))
        lines.append(asp.fact("sticky", fid))
        lines.append(asp.fact("sweet", fid))
    for hid, spec in HEROES.items():
        lines.append(asp.fact("character", hid))
        if "hungry" in spec.traits:
            lines.append(asp.fact("hungry", hid))
    for xid, spec in HELPERS.items():
        lines.append(asp.fact("wise_helper", xid))
        lines.append(asp.fact("warns", xid, "bear", "honey"))
        lines.append(asp.fact("shares", xid, "bear", "honey"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting in SETTINGS:
        for hero in HEROES:
            for helper in HELPERS:
                for food in FOODS:
                    combos.append((setting, hero, helper, food))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_story/2."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = {(h, f) for _, h, _, f in valid_combos()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(cl)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A humorous honey fable storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--mood", choices=MOODS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(list(HEROES))
    helper = args.helper or rng.choice(list(HELPERS))
    food = args.food or "honey"
    mood = args.mood or rng.choice(MOODS)
    return StoryParams(setting=setting, hero=hero, helper=helper, food=food, mood=mood)


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero_spec = HEROES[params.hero]
    helper_spec = HELPERS[params.helper]
    food = FOODS[params.food]

    hero = world.add(Entity(id="hero", kind="character", type=hero_spec.type, label=hero_spec.label, traits=hero_spec.traits))
    helper = world.add(Entity(id="helper", kind="character", type=helper_spec.type, label=helper_spec.label, traits=helper_spec.traits))
    jar = world.add(Entity(id="honey", type="jar", label="jar", phrase=food.phrase, owner=hero.id, caretaker=helper.id))

    hero.memes["curiosity"] += 1
    hero.meters["hungry"] += 1
    hero.memes["pride"] += 1
    helper.memes["joy"] += 0.5
    world.facts.update(hero=hero, helper=helper, food=food, jar=jar, params=params)

    world.say(
        f"In {world.setting.place}, a hungry {hero.label} found {food.phrase} sitting in the grass."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted the honey right away, because hunger can make even a brave nose rush ahead."
    )
    return world


def _mess(world: World) -> None:
    hero: Entity = world.facts["hero"]
    food: Food = world.facts["food"]
    if ("mess", hero.id) in world.fired:
        return
    world.fired.add(("mess", hero.id))
    hero.meters[food.mess] = hero.meters.get(food.mess, 0.0) + 1
    hero.memes["conflict"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} poked at the honey too fast, and sticky gold clung to {hero.pronoun('possessive')} paws."
    )
    world.say("That made the hero look funny, like a snack trying to wear a necklace.")


def _warn(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    if ("warn", hero.id) in world.fired:
        return
    world.fired.add(("warn", hero.id))
    if hero.meters.get("sticky", 0.0) >= THRESHOLD:
        world.say(
            f"A wise {helper.label} buzzed, 'Slow paws are happier paws. If you rush honey, it will rush back.'"
        )
    else:
        world.say(
            f"A wise {helper.label} buzzed, 'Honey is sweet, but it likes patient hands.'"
        )


def _share(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    if ("share", hero.id) in world.fired:
        return
    world.fired.add(("share", hero.id))
    hero.memes["conflict"] = 0.0
    hero.memes["joy"] += 1
    hero.meters["safe"] += 1
    world.say(
        f"So the hero licked one sticky paw, laughed at the silly mess, and let the {helper.label} help."
    )
    world.say(
        f"They took turns, and the honey was sweeter when shared than when snatched."
    )


def tell_story(world: World) -> None:
    world.para()
    _mess(world)
    _warn(world)
    world.para()
    _share(world)
    world.para()
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    food: Food = world.facts["food"]
    world.say(
        f"In the end, {hero.label} was no longer hurrying, and the {helper.label} was smiling beside the empty jar."
    )
    world.say(
        f"The little fable ended with a sticky grin: {food.label} is nice, but patience makes it nicer."
    )


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        "Write a short humorous fable about honey, patience, and a silly mistake.",
        f"Tell a child-friendly story in which a {p.hero} learns not to rush honey in {world.setting.place}.",
        "Write a tiny fable with a comic mess, a wise helper, and a neat ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    food: Food = world.facts["food"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Who found the honey in {place}?",
            answer=f"The {hero.label} found the honey in {place}.",
        ),
        QAItem(
            question=f"Why did the {hero.label} get sticky?",
            answer=f"The {hero.label} got sticky because {hero.pronoun()} rushed at the honey too fast.",
        ),
        QAItem(
            question=f"What did the wise {helper.label} tell the hero?",
            answer=f"The wise {helper.label} told the hero to slow down, because honey is sweeter when handled patiently.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the {hero.label} sharing the honey and smiling beside the empty jar.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    food: Food = world.facts["food"]
    out: list[QAItem] = []
    for tag in food.tags:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE.get(tag, []))
    return out


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell_story(world)
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
    StoryParams(setting="meadow", hero="bear", helper="bee", food="honey", mood="greedy"),
    StoryParams(setting="orchard", hero="fox", helper="owl", food="honey", mood="impatient"),
    StoryParams(setting="grove", hero="rabbit", helper="bee", food="honey", mood="gloomy"),
]


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_story/2."))
    return sorted(set(asp.atoms(model, "good_story")))


def build_combo_list() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for h in HEROES:
            for hlp in HELPERS:
                combos.append((s, h, hlp))
    return combos


def asp_verify_model() -> int:
    py = {(h, f) for _, h, _, f in valid_combos()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(cl)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def explain_invalid() -> str:
    return "(No story: this world only tells honey fables with a helper and a little comic trouble.)"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify_model())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible stories ({len(stories)} with helper pairing):\n")
        for setting, hero, helper, food in triples:
            print(f"  {setting:8} {hero:8} {helper:8} {food:8}")
        return

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
            header = f"### {p.hero} in {p.setting} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
