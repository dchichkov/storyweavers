#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/moray_dead_naval_sound_effects_bedtime_story.py
================================================================================================

A tiny bedtime-story world about a child at a naval harbor, a sleepy soundscape,
and the discovery of a dead moray that changes the mood of the night.

The world is intentionally small and classical:
- one child
- one grown-up helper
- one place near the water
- one marine object of concern
- one gentle sound effect motif
- one emotional turn from curiosity to calm understanding

The story is generated from a simulated world state rather than a frozen template.
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
# Domain registries
# ---------------------------------------------------------------------------

CHILD_NAMES = ["Mina", "Theo", "Lena", "Owen", "Nora", "Ivy", "Eli", "June"]
GUARDIAN_NAMES = ["Captain Reed", "Aunt Elia", "Uncle Bram", "Mara", "Captain Vale"]
MOOD_WORDS = ["sleepy", "gentle", "curious", "quiet", "cuddly", "brave"]
SFX_CHOICES = ["splash", "bloop", "plip", "whoosh", "hush", "tap-tap"]

PLACE_CHOICES = {
    "naval_dock": "the naval dock",
    "naval_bay": "the naval bay",
    "naval_museum": "the naval museum",
}

LIGHT_CHOICES = {
    "lantern": "a soft lantern",
    "moon": "the moon",
    "dock_lights": "the dock lights",
}

# ---------------------------------------------------------------------------
# Shared entity model
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle", "captain"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    naval: bool = True
    water: bool = True
    quiet: bool = False


@dataclass
class ObjectSpec:
    id: str
    label: str
    phrase: str
    sound: str
    place: str
    is_dead: bool = False
    marine: bool = False


@dataclass
class StoryParams:
    place: str
    child_name: str
    guardian_name: str
    mood: str
    light: str
    sound: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    child: Entity
    guardian: Entity
    object: Entity
    light: str
    sound: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Simulation rules
# ---------------------------------------------------------------------------

def _sfx(text: str) -> str:
    return f"*{text}*"


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    child = Entity(
        id=params.child_name,
        kind="character",
        type="girl" if params.child_name in {"Mina", "Lena", "Nora", "Ivy", "June"} else "boy",
        meters={"sleepiness": 1.0},
        memes={"curiosity": 1.0, "calm": 1.0 if params.mood == "gentle" else 0.5},
    )
    guardian = Entity(
        id=params.guardian_name,
        kind="character",
        type="captain" if "Captain" in params.guardian_name else ("aunt" if "Aunt" in params.guardian_name else "uncle"),
        meters={"tiredness": 1.0},
        memes={"care": 1.0, "calm": 1.0},
    )
    obj = Entity(
        id="moray",
        kind="thing",
        type="moray",
        label="moray",
        phrase="a dead moray with silver-green spots",
        owner=None,
        caretaker=params.guardian_name,
        meters={"wetness": 1.0, "stillness": 1.0, "salinity": 1.0},
        memes={"mystery": 1.0},
    )
    world = World(place=place, child=child, guardian=guardian, object=obj, light=params.light, sound=params.sound)
    world.facts.update(params=params, place=place, child=child, guardian=guardian, object=obj)
    return world


def narrate_setup(world: World) -> None:
    c, g, o = world.child, world.guardian, world.object
    world.say(
        f"{c.id} was a {world.facts['params'].mood} little child who loved quiet nights by {world.place.label}."
    )
    world.say(
        f"{g.id} kept watch nearby, and {world.light} glowed over the water like a sleepy star."
    )
    world.say(
        f"The air was full of little sounds, and every now and then {world.sound} came from the harbor."
    )
    world.say(
        f"Then {c.id} spotted {o.phrase} near the edge of the dock."
    )


def narrate_turn(world: World) -> None:
    c, g, o = world.child, world.guardian, world.object
    c.memes["curiosity"] += 1.0
    c.meters["leaning"] = c.meters.get("leaning", 0.0) + 1.0
    world.say(
        f"{c.id} whispered, “What happened to the moray?” and the question hung in the hush."
    )
    world.say(
        f"{g.id} knelt beside {c.id} and said the moray was dead, so they should be gentle and let it rest."
    )
    g.memes["care"] += 1.0
    c.memes["sadness"] = c.memes.get("sadness", 0.0) + 1.0
    world.say(
        f"{c.id} felt a small pinch of sadness, because even a dead fish could make the dark water seem lonelier."
    )
    world.say(
        f"{_sfx(world.sound)} went the water again, and {g.id} pointed to the sea, where the moon made a silver path."
    )


def narrate_resolution(world: World) -> None:
    c, g, o = world.child, world.guardian, world.object
    c.memes["calm"] += 1.0
    c.memes["curiosity"] += 0.5
    c.meters["leaning"] = max(0.0, c.meters.get("leaning", 0.0) - 1.0)
    world.say(
        f"{g.id} wrapped an arm around {c.id} and explained that sailors and harbor helpers would take care of the moray in the morning."
    )
    world.say(
        f"{c.id} nodded, listening to the soft {world.sound} and the sleepy slap of water against the wood."
    )
    world.say(
        f"At last {c.id} looked back at the dead moray one more time, then let the night grow quiet again."
    )
    world.say(
        f"By the time they walked home, {c.id} was sleepy instead of scared, and the harbor behind them was only a dark, calm shimmer."
    )
    world.facts["resolved"] = True


def tell_story(world: World) -> World:
    narrate_setup(world)
    world.para()
    narrate_turn(world)
    world.para()
    narrate_resolution(world)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when it has a naval setting, a moray, a dead object,
% and a sound effect that helps keep the bedtime tone gentle.
valid_story(P) :- place(P), naval(P), water(P), has_moray(P), dead(moray), sound_fx(P).

% This tiny world explicitly prefers calm bedtime scenes.
bedtime_ok(P) :- valid_story(P), quiet(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.naval:
            lines.append(asp.fact("naval", pid))
        if p.water:
            lines.append(asp.fact("water", pid))
        if p.quiet:
            lines.append(asp.fact("quiet", pid))
    for sid, s in SFX_LIBRARY.items():
        lines.append(asp.fact("sound", sid))
    lines.append(asp.fact("has_moray", "naval_dock"))
    lines.append(asp.fact("dead", "moray"))
    lines.append(asp.fact("sound_fx", "naval_dock"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_story_places())
    cl = set(place for (place,) in asp_valid_stories())
    if py == cl:
        print(f"OK: ASP matches Python story gate ({len(py)} places).")
        return 0
    print("MISMATCH between ASP and Python.")
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "naval_dock": Place(id="naval_dock", label="the naval dock", naval=True, water=True, quiet=True),
    "naval_bay": Place(id="naval_bay", label="the naval bay", naval=True, water=True, quiet=False),
    "naval_museum": Place(id="naval_museum", label="the naval museum", naval=True, water=False, quiet=True),
}

SFX_LIBRARY = {
    "splash": "splash",
    "bloop": "bloop",
    "plip": "plip",
    "hush": "hush",
    "tap": "tap-tap",
}

CURATED = [
    StoryParams(
        place="naval_dock",
        child_name="Mina",
        guardian_name="Captain Reed",
        mood="sleepy",
        light="lantern",
        sound="hush",
    ),
    StoryParams(
        place="naval_bay",
        child_name="Theo",
        guardian_name="Mara",
        mood="curious",
        light="moon",
        sound="splash",
    ),
    StoryParams(
        place="naval_museum",
        child_name="June",
        guardian_name="Captain Vale",
        mood="gentle",
        light="dock_lights",
        sound="tap",
    ),
]


# ---------------------------------------------------------------------------
# Gates / parameter resolution
# ---------------------------------------------------------------------------

def valid_story_places() -> list[str]:
    return [pid for pid, p in PLACES.items() if p.naval and (p.water or p.quiet)]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: a child, a naval place, a dead moray, and a gentle sound effect."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--child-name", choices=CHILD_NAMES)
    ap.add_argument("--guardian-name", choices=GUARDIAN_NAMES)
    ap.add_argument("--mood", choices=MOOD_WORDS)
    ap.add_argument("--light", choices=LIGHT_CHOICES)
    ap.add_argument("--sound", choices=SFX_LIBRARY)
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
    if args.place is not None and args.place not in PLACES:
        raise StoryError("Unknown place.")
    place = args.place or rng.choice(valid_story_places())
    if place not in valid_story_places():
        raise StoryError("That place does not fit the naval bedtime story gate.")

    return StoryParams(
        place=place,
        child_name=args.child_name or rng.choice(CHILD_NAMES),
        guardian_name=args.guardian_name or rng.choice(GUARDIAN_NAMES),
        mood=args.mood or rng.choice(MOOD_WORDS),
        light=args.light or rng.choice(list(LIGHT_CHOICES)),
        sound=args.sound or rng.choice(list(SFX_LIBRARY)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a bedtime story for a small child at {world.place.label} with the word "moray".',
        f"Tell a gentle naval nighttime story where {p.child_name} finds a dead moray and hears soft sound effects.",
        f'Create a calm bedtime tale with a naval setting, a dead moray, and the sound "{p.sound}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    c, g, o = world.child, world.guardian, world.object
    return [
        QAItem(
            question=f"Who found the moray at {world.place.label}?",
            answer=f"{c.id} found the dead moray near the dock while watching the calm water with {g.id}.",
        ),
        QAItem(
            question=f"Why did {c.id} feel sad for a moment?",
            answer=f"{c.id} felt sad because {g.id} said the moray was dead, and that made the night feel lonelier for a moment.",
        ),
        QAItem(
            question=f"What helped the story stay gentle and sleepy?",
            answer=f"The soft {p.sound} sound effect, the lantern light, and {g.id}'s calm voice kept the story gentle and sleepy.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {c.id} felt sleepy instead of scared and walked home calm with {g.id}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a moray?",
            answer="A moray is a kind of eel that lives in the sea and often hides in rocks or reefy places.",
        ),
        QAItem(
            question="What does dead mean?",
            answer="Dead means something is no longer alive. It does not move or breathe anymore.",
        ),
        QAItem(
            question="What does naval mean?",
            answer="Naval means it has to do with ships, sailors, or the navy near the sea.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are short noises like splash, hush, or tap-tap that help a story feel alive.",
        ),
    ]


def world_qa_filter(world: World) -> list[QAItem]:
    return world_qa(world)


# ---------------------------------------------------------------------------
# Trace / output
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in [world.child, world.guardian, world.object]:
        meters = ", ".join(f"{k}={v}" for k, v in sorted(e.meters.items()))
        memes = ", ".join(f"{k}={v}" for k, v in sorted(e.memes.items()))
        lines.append(f"{e.id} ({e.type}) meters[{meters}] memes[{memes}]")
    lines.append(f"place={world.place.id} label={world.place.label} naval={world.place.naval} water={world.place.water}")
    lines.append(f"light={world.light} sound={world.sound}")
    lines.append(f"facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
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


# ---------------------------------------------------------------------------
# ASP helpers and CLI
# ---------------------------------------------------------------------------

def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a moray?",
            answer="A moray is a kind of eel that lives in the sea and often hides in rocks or reefy places.",
        ),
        QAItem(
            question="What does dead mean?",
            answer="Dead means something is no longer alive. It does not move or breathe anymore.",
        ),
        QAItem(
            question="What does naval mean?",
            answer="Naval means it has to do with ships, sailors, or the navy near the sea.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are short noises like splash, hush, or tap-tap that help a story feel alive.",
        ),
    ]


def build_params_list(args: argparse.Namespace, base_seed: int) -> list[StoryParams]:
    if args.all:
        return CURATED
    rng = random.Random(base_seed)
    return [resolve_params(args, random.Random(base_seed + i)) for i in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        rows = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(rows)} valid story places:")
        for (place,) in rows:
            print(f"  {place}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.child_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
