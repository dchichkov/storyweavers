#!/usr/bin/env python3
"""
A standalone storyworld for a small fable-like bravery tale with psychology,
foreshadowing, and inner monologue.

The world simulates a timid character facing a small but real danger, learns to
name the fear inside, and chooses brave action with help from a hint the world
has already given.
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
# World data
# ---------------------------------------------------------------------------

@dataclass
class Character:
    name: str
    species: str
    role: str
    trait: str
    place: str
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {
        "fear": 0.0,
        "bravery": 0.0,
        "hope": 0.0,
        "calm": 0.0,
        "doubt": 0.0,
        "pride": 0.0,
        "inner_voice": 0.0,
    })

    def subj(self) -> str:
        return "he" if self.species in {"fox", "wolf", "boy", "rabbit"} else "she"

    def obj(self) -> str:
        return "him" if self.subj() == "he" else "her"

    def poss(self) -> str:
        return "his" if self.subj() == "he" else "her"


@dataclass
class Threat:
    name: str
    kind: str
    clue: str
    danger_level: int
    is_real: bool = True


@dataclass
class StoryParams:
    name: str
    species: str
    role: str
    trait: str
    place: str
    threat: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Character
    threat: Threat
    setting: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

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

PLACES = {
    "wood": "the wood",
    "river": "the river",
    "hill": "the hill",
    "path": "the narrow path",
    "bridge": "the old bridge",
}

TRAITS = ["timid", "small", "quiet", "careful", "gentle", "watchful"]

HEROES = {
    "mouse": "mouse",
    "rabbit": "rabbit",
    "fox": "fox",
    "sparrow": "sparrow",
}

THREATS = {
    "owl-shadow": Threat(
        name="owl-shadow",
        kind="shadow",
        clue="a round shadow moved across the ground before the owl landed",
        danger_level=2,
        is_real=True,
    ),
    "river-wind": Threat(
        name="river-wind",
        kind="wind",
        clue="the reeds bent first, as if the wind were speaking before the gust arrived",
        danger_level=2,
        is_real=True,
    ),
    "fallen-log": Threat(
        name="fallen-log",
        kind="barrier",
        clue="a log had already cracked the path, making it look unsafe from the start",
        danger_level=1,
        is_real=True,
    ),
    "night-rumor": Threat(
        name="night-rumor",
        kind="rumor",
        clue="the dark corner only seemed full of danger because the wind rustled twice",
        danger_level=1,
        is_real=False,
    ),
}

VALID_COMBOS = [
    ("wood", "mouse", "owl-shadow"),
    ("river", "rabbit", "river-wind"),
    ("path", "fox", "fallen-log"),
    ("bridge", "sparrow", "night-rumor"),
    ("hill", "mouse", "fallen-log"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(wood;river;hill;path;bridge).
species(mouse;rabbit;fox;sparrow).
threat(owl_shadow;river_wind;fallen_log;night_rumor).

valid(wood,mouse,owl_shadow).
valid(river,rabbit,river_wind).
valid(path,fox,fallen_log).
valid(bridge,sparrow,night_rumor).
valid(hill,mouse,fallen_log).

real_threat(owl_shadow).
real_threat(river_wind).
real_threat(fallen_log).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for s in HEROES:
        lines.append(asp.fact("species", s))
    for t in THREATS:
        lines.append(asp.fact("threat", t.replace("-", "_")))
        if THREATS[t].is_real:
            lines.append(asp.fact("real_threat", t.replace("-", "_")))
    for p, s, t in VALID_COMBOS:
        lines.append(asp.fact("valid", p, s, t.replace("-", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((p, s, t.replace("-", "_")) for p, s, t in VALID_COMBOS)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like bravery storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--species", choices=HEROES)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["farmer", "shepherd", "messenger", "watcher", "child"])
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
    if args.place and args.species and args.threat:
        if (args.place, args.species, args.threat) not in VALID_COMBOS:
            raise StoryError("That setting, hero, and threat do not make a believable fable.")
    combos = [c for c in VALID_COMBOS
              if (args.place is None or c[0] == args.place)
              and (args.species is None or c[1] == args.species)
              and (args.threat is None or c[2] == args.threat)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, species, threat = rng.choice(sorted(combos))
    role = args.role or rng.choice(["farmer", "shepherd", "messenger", "watcher", "child"])
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or rng.choice({
        "mouse": ["Milo", "Nia", "Tavi"],
        "rabbit": ["Pip", "Lina", "Bram"],
        "fox": ["Jun", "Tess", "Orin"],
        "sparrow": ["Sia", "Pico", "Miri"],
    }[species])
    return StoryParams(name=name, species=species, role=role, trait=trait, place=place, threat=threat)


def _hero_article(species: str) -> str:
    return "a" if species[0] not in "aeiou" else "an"


def generate(params: StoryParams) -> StorySample:
    threat = THREATS[params.threat]
    hero = Character(
        name=params.name,
        species=params.species,
        role=params.role,
        trait=params.trait,
        place=PLACES[params.place],
    )
    world = World(hero=hero, threat=threat, setting=PLACES[params.place])

    hero.memes["fear"] += 1.0
    hero.memes["inner_voice"] += 1.0
    hero.memes["doubt"] += 0.5

    world.say(
        f"On {world.setting}, {params.name} was { _hero_article(params.species) } "
        f"{params.trait} {params.species} who worked as {params.role}."
    )
    world.say(
        f"{params.name} liked to listen to the quiet parts of the world, because small things often mattered most."
    )
    world.say(
        f"Still, {params.name} had heard a story about the {threat.kind} called {threat.name.replace('-', ' ')}."
    )

    world.para()
    world.say(
        f"Before the day was done, {params.name} noticed {threat.clue}."
    )
    hero.meters["distance"] = 1.0
    hero.memes["fear"] += 1.0
    hero.memes["hope"] += 0.5
    world.facts["foreshadow"] = threat.clue

    world.para()
    world.say(
        f"{params.name} stopped and listened to {hero.poss()} own thoughts."
    )
    world.say(
        f'"If I turn back now," {params.name} thought, "I will keep myself safe, but I will also stay small in my own eyes."'
    )
    world.say(
        f'"If I move forward with care, I may be scared, yet I can still be brave."'
    )
    hero.memes["inner_voice"] += 1.0
    hero.memes["bravery"] += 1.0

    if threat.is_real:
        world.say(
            f"The danger was real, and the air felt sharp around {params.name}."
        )
        hero.memes["fear"] += 0.5
    else:
        world.say(
            f"The danger only seemed larger than it was, because shadows can fool a worried heart."
        )
        hero.memes["calm"] += 1.0

    world.para()
    world.say(
        f"Then {params.name} took one careful step, and then another."
    )
    world.say(
        f"{params.name} used a slow breath, watched the ground, and chose the safer way."
    )
    hero.meters["distance"] += 2.0
    hero.memes["bravery"] += 1.0
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 0.5)
    hero.memes["calm"] += 1.0
    hero.memes["pride"] += 1.0

    world.para()
    if threat.is_real:
        world.say(
            f"In the end, the {threat.kind} passed by, and {params.name} was already beyond it."
        )
    else:
        world.say(
            f"In the end, the dark corner was only a corner, and {params.name} had walked through it bravely."
        )
    world.say(
        f"{params.name} stood a little taller, because courage had not made the world smaller; it had made the heart wider."
    )
    world.say(
        f"That was how {params.name} learned that bravery means acting well while fear is still nearby."
    )

    world.facts.update(
        hero=hero,
        threat=threat,
        params=params,
    )
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short fable about {p.name}, {p.species}, and the meaning of bravery.',
        f"Tell a child-sized story where a {p.trait} {p.species} hears a warning, thinks privately, and chooses courage.",
        f'Write a gentle story with foreshadowing about "{world.threat.clue}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    h = world.facts["hero"]
    t = world.facts["threat"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {p.name}, {h.species}, who lives near {world.setting} and works as {p.role}.",
        ),
        QAItem(
            question=f"What warning was hinted at before the main brave moment?",
            answer=f"The hint was that {t.clue}. That foreshadowing made the later choice feel important.",
        ),
        QAItem(
            question=f"What did {p.name} think to themselves before moving forward?",
            answer=(
                f"{p.name} thought that turning back would keep {h.obj()} safe, but stepping forward with care might be brave. "
                f"That inner monologue helped {h.subj()} choose courage."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended with {p.name} moving past the danger, standing taller, and learning that bravery means acting well while fear is still nearby."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is choosing the right action even when you feel afraid.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a hint early in a story that something important may happen later.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the quiet thinking a character does inside their own mind.",
        ),
        QAItem(
            question="Why do fables often use animals?",
            answer="Fables often use animals so a simple story can teach a clear lesson about how to act.",
        ),
    ]


def dump_trace(world: World) -> str:
    h = world.hero
    lines = ["--- world model state ---"]
    lines.append(f"hero={h.name} species={h.species} role={h.role} place={world.setting}")
    lines.append(f"threat={world.threat.name} real={world.threat.is_real}")
    lines.append(f"meters={h.meters}")
    lines.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in sorted(h.memes.items()) if v)}}}")
    lines.append(f"foreshadow={world.facts.get('foreshadow')}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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


def asp_program_text() -> str:
    return asp_program("#show valid/3.")


def asp_list() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_story_from_params(params: StoryParams) -> StorySample:
    return generate(params)


CURATED = [
    StoryParams(name="Milo", species="mouse", role="watcher", trait="timid", place="wood", threat="owl-shadow"),
    StoryParams(name="Pip", species="rabbit", role="messenger", trait="careful", place="river", threat="river-wind"),
    StoryParams(name="Jun", species="fox", role="shepherd", trait="quiet", place="path", threat="fallen-log"),
    StoryParams(name="Sia", species="sparrow", role="child", trait="watchful", place="bridge", threat="night-rumor"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_text())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_list()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.name}: {p.species} at {p.place} (threat: {p.threat})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
