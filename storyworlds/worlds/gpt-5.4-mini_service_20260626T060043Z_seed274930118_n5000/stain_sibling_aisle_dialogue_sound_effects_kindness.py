#!/usr/bin/env python3
"""
Tall-tale storyworld: a sibling, an aisle, a stain, and a kindly fix.

A short source-tale seed:
A little kid and their older sibling went down a grocery aisle to find cereal.
A jar bumped the cart, splat! Sauce stained the little kid's shirt.
The older sibling spoke kindly, used a cloth, and helped rinse the stain away.
A cheerful sound effect and a gentle joke turned the mishap into a funny memory.

This world models:
- physical meters: stain, wetness, cleanliness, noise
- emotional memes: worry, embarrassment, kindness, relief, pride
- dialogue as authored speech
- sound effects as concrete narrative beats
- kindness as the causal turn that resolves the stain

The story generator keeps a tall-tale flavor: exaggeration, lively dialogue,
and a clear before/middle/after arc centered on the aisle mishap.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Person:
    name: str
    role: str
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def subj(self) -> str:
        return "they"

    def obj(self) -> str:
        return "them"

    def poss(self) -> str:
        return "their"


@dataclass
class Item:
    name: str
    kind: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the grocery store"
    aisle: str = "the cereal aisle"
    sound_effects: list[str] = field(default_factory=lambda: ["clatter", "splat", "swish"])


@dataclass
class World:
    setting: Setting
    people: dict[str, Person] = field(default_factory=dict)
    items: dict[str, Item] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def trace(self) -> str:
        out = ["--- world model state ---"]
        for p in self.people.values():
            meters = {k: v for k, v in p.meters.items() if v}
            memes = {k: v for k, v in p.memes.items() if v}
            out.append(f"  {p.name:10} ({p.role:9}) meters={meters} memes={memes}")
        for i in self.items.values():
            meters = {k: v for k, v in i.meters.items() if v}
            memes = {k: v for k, v in i.memes.items() if v}
            out.append(f"  {i.name:10} ({i.kind:9}) meters={meters} memes={memes}")
        return "\n".join(out)


# ---------------------------------------------------------------------------
# Parameters / registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    seed: Optional[int] = None
    setting: str = "grocery"
    aisle_kind: str = "cereal"
    hero_name: str = "Milo"
    sibling_name: str = "June"
    stain_source: str = "sauce"
    sound: str = "SPLAT"
    kind_act: str = "helped clean the stain"


SETTINGS = {
    "grocery": Setting(place="the grocery store", aisle="the cereal aisle", sound_effects=["clatter", "splat", "swish"]),
    "market": Setting(place="the market", aisle="the snack aisle", sound_effects=["plink", "plop", "swoosh"]),
    "supermarket": Setting(place="the supermarket", aisle="the soup aisle", sound_effects=["clink", "splot", "wipe"]),
}

HERO_NAMES = ["Milo", "Ruby", "Finn", "Poppy", "Theo", "Maya", "Luna", "Eli"]
SIBLING_NAMES = ["June", "Nico", "Wren", "Iris", "Otto", "Sage", "Bea", "Toby"]
STAINS = ["sauce", "juice", "jam", "yogurt", "gravy"]
SOUNDS = ["SPLAT", "WHUMP", "PLOP", "SQUISH", "CLATTER"]


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"unknown setting: {params.setting}")
    setting = SETTINGS[params.setting]
    world = World(setting=setting)

    hero = Person(name=params.hero_name, role="younger sibling")
    sibling = Person(name=params.sibling_name, role="older sibling")
    shirt = Item(name="shirt", owner=hero.name)

    world.people[hero.name] = hero
    world.people[sibling.name] = sibling
    world.items[shirt.name] = shirt

    # Opening: introduce the pair and the aisle.
    world.say(f"{hero.name} and {sibling.name} went into {setting.place} as grand as a courthouse and headed for {setting.aisle}.")
    world.say(f"{hero.name} was humming like a busy bee, while {sibling.name} kept a watchful eye on the cart.")

    # The mishap.
    hero.memes["hope"] = 1
    hero.memes["calm"] = 1
    sibling.memes["care"] = 1
    world.say(f"Then there came a mighty {params.sound.lower()}—a jar tipped, a lid slipped, and {params.stain_source} flew like a tiny meteor.")
    shirt.meters["stain"] = 1
    shirt.meters["wet"] = 1
    hero.memes["worry"] = 1
    hero.memes["embarrassment"] = 1
    sibling.memes["alert"] = 1
    world.say(f"A bold stain landed right on {hero.name}'s shirt.")
    world.say(f'"Oh no!" {hero.name} cried. "My shirt got a stain!"')
    world.say(f'"Fear not," said {sibling.name}. "A stain is not a dragon, and we have hands, towels, and time."')

    # Kindness turn.
    sibling.memes["kindness"] = 1
    hero.memes["worry"] = 0
    world.say(f"{sibling.name} took a napkin from the cart, dipped it in water, and worked carefully at the spot.")
    shirt.meters["stain"] = 0
    shirt.meters["wet"] = 0
    shirt.meters["clean"] = 1
    hero.memes["relief"] = 1
    hero.memes["pride"] = 1
    world.say(f"Swish, swish went the napkin, and the stain faded as if it had never been invited.")
    world.say(f'"See?" said {sibling.name}. "A little kindness can hush a big mess."')
    world.say(f"{hero.name} grinned. " f'"You are the best sibling in the aisle," {hero.name} said, and {sibling.name} bowed like a knight in a bright hallway.')

    # Ending image.
    world.say(f"They rolled the cart onward through {setting.aisle}, and {hero.name}'s shirt shone clean again, as neat as a new snowflake.")
    world.say(f"The whole aisle seemed to sing a cheerful little song: {params.sound}, swish, hooray.")
    world.facts.update(hero=hero.name, sibling=sibling.name, stain=params.stain_source, aisle=setting.aisle, place=setting.place)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale style story about siblings in {f["aisle"]} where a {f["stain"]} stain needs a kind fix.',
        f"Tell a child-friendly story set in {f['place']} with dialogue and a sound effect like {world.setting.sound_effects[1]}.",
        f'Write a short story for little kids that includes the words "stain", "sibling", and "aisle".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Where did {f['hero']} and {f['sibling']} go in the story?",
            answer=f"They went to {f['place']} and headed down {f['aisle']}.",
        ),
        QAItem(
            question=f"What happened to {f['hero']}'s shirt?",
            answer=f"A {f['stain']} stain landed on {f['hero']}'s shirt and made them worry for a moment.",
        ),
        QAItem(
            question=f"How was the stain fixed?",
            answer=f"{f['sibling']} used a napkin, water, and kindness to clean the stain away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stain?",
            answer="A stain is a mark or spot that gets on cloth or other surfaces and can be hard to wash away.",
        ),
        QAItem(
            question="What is a sibling?",
            answer="A sibling is a brother or sister, or another child in the same family.",
        ),
        QAItem(
            question="What is an aisle?",
            answer="An aisle is a path between rows of shelves or seats, like the walkway in a store.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means doing something gentle and helpful for someone else.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin and reasonableness gate
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is reasonable when there are two siblings, an aisle, and a stain event.
has_story(S) :- sibling(S), aisle(A), stain(SP), event(SP).

% Kindness resolves the problem if the older sibling cleans it.
resolved(S) :- has_story(S), kind_action(S), cleaned(SP).

#show has_story/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("sibling", "pair"))
    lines.append(asp.fact("aisle", "store_aisle"))
    lines.append(asp.fact("stain", "spot"))
    lines.append(asp.fact("event", "spot"))
    lines.append(asp.fact("kind_action", "pair"))
    lines.append(asp.fact("cleaned", "spot"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_check() -> int:
    import asp
    model = asp.one_model(asp_program("#show has_story/1.\n#show resolved/1."))
    atoms = {(s.name, tuple(getattr(a, "name", getattr(a, "string", getattr(a, "number", None))) for a in s.arguments)) for s in model}
    expected = {("has_story", ("pair",)), ("resolved", ("pair",))}
    if atoms == expected:
        print("OK: ASP twin is consistent with the simple reasonableness gate.")
        return 0
    print("MISMATCH in ASP verification.")
    print("got:", sorted(atoms))
    print("expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Generator API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about a stain, a sibling, and an aisle.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--sibling-name", choices=SIBLING_NAMES)
    ap.add_argument("--stain-source", choices=STAINS)
    ap.add_argument("--sound", choices=SOUNDS)
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
    setting = args.setting or rng.choice(list(SETTINGS.keys()))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    sibling_name = args.sibling_name or rng.choice(SIBLING_NAMES)
    if sibling_name == hero_name:
        raise StoryError("hero and sibling must have different names")
    return StoryParams(
        seed=None,
        setting=setting,
        aisle_kind="cereal",
        hero_name=hero_name,
        sibling_name=sibling_name,
        stain_source=args.stain_source or rng.choice(STAINS),
        sound=args.sound or rng.choice(SOUNDS),
        kind_act="helped clean the stain",
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show has_story/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_check())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show has_story/1.\n#show resolved/1."))
        print("ASP model:", [str(a) for a in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="grocery", hero_name="Milo", sibling_name="June", stain_source="sauce", sound="SPLAT"),
            StoryParams(setting="market", hero_name="Ruby", sibling_name="Nico", stain_source="jam", sound="PLOP"),
            StoryParams(setting="supermarket", hero_name="Theo", sibling_name="Wren", stain_source="juice", sound="CLATTER"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero_name} and {sample.params.sibling_name}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
