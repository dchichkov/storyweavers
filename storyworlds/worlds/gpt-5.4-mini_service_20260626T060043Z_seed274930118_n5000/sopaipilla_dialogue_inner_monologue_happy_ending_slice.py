#!/usr/bin/env python3
"""
A standalone storyworld for a tiny slice-of-life tale about a sopaipilla,
a small worry, a quiet decision, and a happy ending.

Premise:
- A child loves a warm sopaipilla.
- Someone worries it might get messy or be eaten too soon.
- The child thinks to themself, talks it through, and chooses a gentle plan.
- The story ends with the sopaipilla shared and enjoyed safely.

The world model tracks:
- physical state in meters: warmth, crispness, sweetness, mess, fullness
- emotional state in memes: desire, worry, patience, comfort, joy
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
# Entities
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("warmth", "crispness", "sweetness", "mess", "fullness"):
            self.meters.setdefault(k, 0.0)
        for k in ("desire", "worry", "patience", "comfort", "joy"):
            self.memes.setdefault(k, 0.0)


@dataclass
class Setting:
    place: str = "the little kitchen"
    affords: set[str] = field(default_factory=lambda: {"cook", "talk", "share", "wait"})


@dataclass
class StoryParams:
    setting: str
    hero: str
    helper: str
    snack: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the little kitchen", affords={"cook", "talk", "share", "wait"}),
    "patio": Setting(place="the sunny patio", affords={"talk", "share", "wait"}),
    "bakery": Setting(place="the cozy bakery corner", affords={"cook", "talk", "share", "wait"}),
}

HEROES = ["Mina", "Leo", "Sofia", "Noah", "Luna", "Mateo"]
HELPERS = ["mom", "dad", "grandma", "grandpa", "auntie", "uncle"]

SOPAIPILLAS = {
    "sopaipilla": {
        "phrase": "a warm sopaipilla with a little honey",
        "label": "sopaipilla",
        "warmth": 2.0,
        "crispness": 1.5,
        "sweetness": 2.0,
    }
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid_story/3.

setting(kitchen). setting(patio). setting(bakery).
hero(mina). hero(leo). hero(sofia). hero(noah). hero(luna). hero(mateo).
helper(mom). helper(dad). helper(grandma). helper(grandpa). helper(auntie). helper(uncle).
snack(sopaipilla).

valid_story(S, H, P) :- setting(S), hero(H), snack(P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for x in HELPERS:
        lines.append(asp.fact("helper", x))
    for s in SOPAIPILLAS:
        lines.append(asp.fact("snack", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(s, h, p) for s in SETTINGS for h in HEROES for p in SOPAIPILLAS}
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: clingo gate matches python ({len(py)} combinations).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------


def validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.hero == params.helper:
        raise StoryError("The child and helper must be different characters.")
    if params.snack not in SOPAIPILLAS:
        raise StoryError("Unknown snack.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------


def _do_cook(world: World, hero: Entity, snack: Entity) -> None:
    snack.meters["warmth"] = 2.0
    snack.meters["crispness"] = 1.5
    snack.meters["sweetness"] = 2.0
    hero.memes["desire"] += 1.0
    hero.memes["joy"] += 0.5
    world.say(
        f"{hero.id} watched the sopaipilla turn golden and smelled the sweet honey drifting up."
    )


def _do_worry(world: World, helper: Entity, hero: Entity, snack: Entity) -> None:
    helper.memes["worry"] += 1.0
    hero.memes["worry"] += 0.5
    world.say(
        f'"Let\'s not rush it," {helper.id} said. "It\'s still hot, and we want it to stay nice."'
    )


def _inner_monologue(world: World, hero: Entity, snack: Entity) -> None:
    hero.memes["patience"] += 1.0
    world.say(
        f"{hero.id} thought, Maybe I can wait just a little. The sopaipilla will taste even better when it is safe to hold."
    )


def _do_share(world: World, hero: Entity, helper: Entity, snack: Entity) -> None:
    hero.memes["comfort"] += 1.0
    helper.memes["comfort"] += 1.0
    hero.memes["joy"] += 1.5
    helper.memes["joy"] += 1.0
    snack.meters["warmth"] = 1.2
    snack.meters["mess"] = 0.0
    snack.meters["fullness"] = 1.0
    world.say(
        f'{hero.id} smiled and said, "Okay, I can wait." Then they sat together and shared the sopaipilla in small, careful bites.'
    )
    world.say(
        f"The honey stayed on the plate, the table stayed clean, and the little kitchen felt warm and peaceful."
    )


def tell(setting: Setting, hero_name: str, helper_name: str, snack_key: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", label=helper_name))
    snack = world.add(
        Entity(
            id=snack_key,
            kind="thing",
            label="sopaipilla",
            phrase=SOPAIPILLAS[snack_key]["phrase"],
            owner=hero.id,
        )
    )

    world.say(
        f"At {setting.place}, {hero.id} could not stop looking at the warm sopaipilla on the plate."
    )
    world.say(
        f"{hero.id} wanted to eat it right away, because the honey smelled so sweet and the crust looked so crisp."
    )

    world.para()
    _do_cook(world, hero, snack)
    _do_worry(world, helper, hero, snack)

    world.para()
    _inner_monologue(world, hero, snack)

    world.para()
    _do_share(world, hero, helper, snack)

    world.facts.update(hero=hero, helper=helper, snack=snack, setting=setting)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story about {f["hero"].id}, a sopaipilla, and a gentle family moment.',
        f'Tell a story where {f["hero"].id} wants to eat a sopaipilla quickly, but {f["helper"].id} helps them wait.',
        f'Write a child-friendly story with dialogue, inner monologue, and a happy ending centered on a sopaipilla.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"What did {hero.id} want to eat?",
            answer=f"{hero.id} wanted to eat the sopaipilla.",
        ),
        QAItem(
            question=f"Who asked {hero.id} not to rush?",
            answer=f"{helper.id} asked {hero.id} to wait because the sopaipilla was still hot.",
        ),
        QAItem(
            question=f"What did {hero.id} think before the ending?",
            answer=f"{hero.id} thought that waiting a little would make the sopaipilla safer and tastier.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended happily with them sharing the sopaipilla in small, careful bites.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sopaipilla?",
            answer="A sopaipilla is a fried bread that can be warm, crisp, and often tasty with honey.",
        ),
        QAItem(
            question="Why should you wait before eating something hot?",
            answer="You should wait so you do not burn your mouth and can enjoy the food safely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about a sopaipilla.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--snack", choices=SOPAIPILLAS.keys())
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
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice([h for h in HELPERS if h != hero.lower()])
    snack = args.snack or "sopaipilla"
    params = StoryParams(setting=setting, hero=hero, helper=helper, snack=snack)
    validate_params(params)
    return params


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = tell(SETTINGS[params.setting], params.hero, params.helper, params.snack)
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
# Main / CLI
# ---------------------------------------------------------------------------


CURATED = [
    StoryParams(setting="kitchen", hero="Mina", helper="mom", snack="sopaipilla"),
    StoryParams(setting="patio", hero="Leo", helper="grandma", snack="sopaipilla"),
    StoryParams(setting="bakery", hero="Luna", helper="dad", snack="sopaipilla"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:\n")
        for s, h, p in stories:
            print(f"  {s:8} {h:8} {p:12}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.hero} and {p.helper} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
