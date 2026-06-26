#!/usr/bin/env python3
"""
Stand-alone storyworld: a brave superhero misunderstanding caused by sound effects.

Seed words: less, boat, bulge
Features: misunderstanding, sound effects, bravery
Style: superhero story
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
# Model
# ---------------------------------------------------------------------------

@dataclass
class Character:
    name: str
    role: str
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=lambda: {
        "bravery": 0.0,
        "worry": 0.0,
        "understanding": 0.0,
        "less": 0.0,
    })
    memes: dict[str, float] = field(default_factory=lambda: {
        "hope": 0.0,
        "confusion": 0.0,
        "pride": 0.0,
        "friendship": 0.0,
    })


@dataclass
class Thing:
    name: str
    label: str
    kind: str = "thing"
    meters: dict[str, float] = field(default_factory=lambda: {
        "bulge": 0.0,
        "sound": 0.0,
        "damage": 0.0,
    })
    owner: Optional[str] = None


@dataclass
class World:
    setting: str
    hero: Character
    friend: Character
    city: str
    boat: Thing
    bulge_source: Thing
    sound_effects: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts["story"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "harbor": "the bright harbor",
    "rooftops": "the rooftop docks",
    "pier": "the moonlit pier",
    "cove": "the hidden cove",
}

HEROES = [
    ("Nova", "superhero"),
    ("Spark", "superhero"),
    ("Comet", "superhero"),
    ("Captain Lantern", "superhero"),
]

FRIENDS = [
    ("Pip", "kid"),
    ("Milo", "kid"),
    ("Tess", "kid"),
    ("Ari", "kid"),
]

SOUND_EFFECTS = [
    "BANG!",
    "WHIRR!",
    "KAPOW!",
    "BOINK!",
    "SPLASH!",
    "THOOM!",
]

BOATS = {
    "rescue_boat": "a small rescue boat",
    "police_boat": "a blue patrol boat",
    "toy_boat": "a little toy boat",
    "ferry_boat": "a narrow ferry boat",
}

BULGE_SOURCES = {
    "life_vest": "a life vest with a bulge in the pocket",
    "crate": "a crate with a strange bulge under a tarp",
    "cape_bundle": "a cape bundle with a bulge at the middle",
    "tool_bag": "a tool bag with a round bulge inside",
}

TITLES = [
    "The Bulge on the Boat",
    "Boom in the Harbor",
    "The Brave Superhero and the Funny Sound",
    "Less Worry, More Courage",
]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    hero: str
    friend: str
    boat: str
    bulge_source: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is reasonable when a bulge can be mistaken for trouble,
% the sound effects can trigger the misunderstanding, and bravery resolves it.
misunderstanding(S) :- sound(S), bulge_seen, not explained.
can_resolve :- misunderstanding(S), brave_hero, calm_friend.
valid_story(Setting, Hero, Friend, Boat, Bulge) :-
    place(Setting), hero(Hero), friend(Friend), boat(Boat), bulge(Bulge),
    can_resolve.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for key in SETTINGS:
        lines.append(asp.fact("place", key))
    for name, _ in HEROES:
        lines.append(asp.fact("hero", name))
    for name, _ in FRIENDS:
        lines.append(asp.fact("friend", name))
    for key in BOATS:
        lines.append(asp.fact("boat", key))
    for key in BULGE_SOURCES:
        lines.append(asp.fact("bulge", key))
    for sfx in SOUND_EFFECTS:
        lines.append(asp.fact("sound", sfx.replace("!", "").lower()))
    lines.append(asp.fact("bulge_seen"))
    lines.append(asp.fact("brave_hero"))
    lines.append(asp.fact("calm_friend"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for hero, _ in HEROES:
            for friend, _ in FRIENDS:
                if hero == friend:
                    continue
                for boat in BOATS:
                    for bulge in BULGE_SOURCES:
                        combos.append((setting, hero, friend, boat, bulge))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story world of misunderstanding, sound effects, and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=[n for n, _ in HEROES])
    ap.add_argument("--friend", choices=[n for n, _ in FRIENDS])
    ap.add_argument("--boat", choices=BOATS)
    ap.add_argument("--bulge-source", choices=BULGE_SOURCES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    if args.hero:
        combos = [c for c in combos if c[1] == args.hero]
    if args.friend:
        combos = [c for c in combos if c[2] == args.friend]
    if args.boat:
        combos = [c for c in combos if c[3] == args.boat]
    if args.bulge_source:
        combos = [c for c in combos if c[4] == args.bulge_source]
    if args.hero and args.friend and args.hero == args.friend:
        raise StoryError("The hero and friend must be different people.")
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hero, friend, boat, bulge = rng.choice(sorted(combos))
    return StoryParams(setting=setting, hero=hero, friend=friend, boat=boat, bulge_source=bulge)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def sound_line(effect: str) -> str:
    return random.choice([
        f"{effect} it went across the water.",
        f"{effect} echoed between the docks.",
        f"The air popped with {effect}",
    ])

def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    hero_role = "superhero"
    friend_role = "kid"

    hero = Character(name=params.hero, role=hero_role)
    friend = Character(name=params.friend, role=friend_role)
    boat = Thing(name=params.boat, label=BOATS[params.boat], owner=params.hero)
    bulge = Thing(name=params.bulge_source, label=BULGE_SOURCES[params.bulge_source], owner=params.friend)

    # World state
    hero.meters["bravery"] += 2
    hero.memes["hope"] += 1
    friend.memes["confusion"] += 1
    boat.meters["sound"] += 1
    bulge.meters["bulge"] += 1

    setting_text = SETTINGS[params.setting]
    effect = rng.choice(SOUND_EFFECTS)
    world = World(
        setting=params.setting,
        hero=hero,
        friend=friend,
        city=setting_text,
        boat=boat,
        bulge_source=bulge,
        sound_effects=[effect],
    )

    misunderstanding = True
    less_worry = False
    resolved = False

    story = []
    story.append(
        f"In {setting_text}, {hero.name} was a brave superhero who kept watch over the water."
    )
    story.append(
        f"One day, {hero.name} saw {bulge.label} on {boat.label} and heard {effect} from the dock."
    )
    story.append(
        f"Because of the loud sound, {hero.name} thought the boat might be in trouble."
    )
    story.append(
        f"{hero.name} flew closer and cried, 'Less worry, I will help!'"
    )
    story.append(
        f"But then {friend.name} waved and laughed. '{bulge.label} is only {bulge.label.split(' with ')[0]},' said {friend.name}."
    )
    story.append(
        f"The sound was just {effect} from a loose sign banging in the breeze."
    )
    story.append(
        f"{hero.name} smiled, because the mistake was a misunderstanding, not a disaster."
    )
    story.append(
        f"With brave hands and a calm heart, {hero.name} fixed the sign, and the boat rocked safely in the quiet water."
    )
    story.append(
        f"By the end, the harbor felt less scary, and {friend.name} cheered for the brave superhero."
    )

    world.facts.update(
        story=" ".join(story),
        misunderstanding=misunderstanding,
        resolved=True,
        less_worry=True,
        sound_effect=effect,
        hero=hero,
        friend=friend,
        boat=boat,
        bulge=bulge,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a short superhero story in {setting_text} with a mistaken sound effect and a brave rescue.",
            f"Tell a children's story where {params.hero} hears {effect} near a boat and learns the bulge is harmless.",
            f"Create a gentle action story that uses the words less, boat, and bulge.",
        ],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Character = f["hero"]
    friend: Character = f["friend"]
    boat: Thing = f["boat"]
    bulge: Thing = f["bulge"]
    sfx = f["sound_effect"]
    return [
        QAItem(
            question=f"Why did {hero.name} think there was a problem near the boat?",
            answer=f"{hero.name} heard {sfx} and saw {bulge.label}, so {hero.name} thought the boat might be in danger."
        ),
        QAItem(
            question=f"What was the mistake in the story?",
            answer=f"The mistake was a misunderstanding: the bulge was harmless, and the loud sound was only from a loose sign in the wind."
        ),
        QAItem(
            question=f"How did {hero.name} show bravery?",
            answer=f"{hero.name} flew closer, checked carefully, and fixed the sign instead of running away."
        ),
        QAItem(
            question=f"How did the story end for the boat?",
            answer=f"The boat stayed safe, rocked gently in the water, and did not get hurt at all."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a boat?",
            answer="A boat is a vehicle that moves on water and carries people or things."
        ),
        QAItem(
            question="What is a bulge?",
            answer="A bulge is a round part that sticks out and can make something look bigger in one spot."
        ),
        QAItem(
            question="Why do sound effects matter in stories?",
            answer="Sound effects help readers hear action in their imagination, like a bang, splash, or boom."
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel scared or unsure."
        ),
    ]


def generation_prompts(sample: StorySample) -> list[str]:
    return list(sample.prompts)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace / emission
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for obj in [world.hero, world.friend, world.boat, world.bulge_source]:
        lines.append(f"{obj.name} ({obj.kind}) meters={obj.meters} memes={obj.memes}")
    lines.append(f"setting={world.setting}")
    lines.append(f"sound_effects={world.sound_effects}")
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
# ASP query helpers
# ---------------------------------------------------------------------------

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="harbor", hero="Nova", friend="Pip", boat="rescue_boat", bulge_source="life_vest"),
    StoryParams(setting="pier", hero="Spark", friend="Milo", boat="police_boat", bulge_source="crate"),
    StoryParams(setting="cove", hero="Comet", friend="Tess", boat="toy_boat", bulge_source="cape_bundle"),
]

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.hero} at {p.setting} (boat: {p.boat}, bulge: {p.bulge_source})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
