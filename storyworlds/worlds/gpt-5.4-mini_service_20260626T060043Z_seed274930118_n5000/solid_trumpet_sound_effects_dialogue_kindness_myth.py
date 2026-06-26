#!/usr/bin/env python3
"""
A small mythic storyworld about a solid trumpet, a kind choice, and a sound
that wakes something ancient.

The story premise:
- A child or young hero finds a solid trumpet in a quiet mythic place.
- They want to blow it right away, but a guardian or spirit warns that the
  trumpet only sings when the hero first shows kindness.
- The hero helps someone small or lonely.
- The trumpet rings with bright sound effects, the guardian softens, and the
  hidden path or sleeping wonder opens.

The world model tracks:
- physical meters: polish, hush, closed, open, heard
- emotional memes: wonder, worry, pride, trust, kindness, joy

The script supports the standard Storyweavers CLI:
- default run
- -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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

THRESHOLD = 1.0


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

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "sister"}
        male = {"boy", "father", "man", "king", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    atmosphere: str
    kind: str = "mythic"


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    sound: str
    requires_kindness: bool = True


@dataclass
class KindAct:
    id: str
    verb: str
    gerund: str
    effect: str
    target: str


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "hill": Place("hill", "the moonlit hill", "wind whispered over grass"),
    "cave": Place("cave", "the echoing cave", "drops of water ticked in the dark"),
    "shore": Place("shore", "the silver shore", "waves sighed at the edge of the world"),
}

RELICS = {
    "solid_trumpet": Relic(
        "solid_trumpet",
        "a solid trumpet",
        "a solid trumpet with a bright mouth and a heavy shine",
        "toot-TOOT!",
        requires_kindness=True,
    ),
}

KIND_ACTS = {
    "share": KindAct(
        "share",
        "share bread",
        "sharing bread",
        "softened the guardian's heart",
        "a small hungry child",
    ),
    "help": KindAct(
        "help",
        "help the lost lamb",
        "helping the lost lamb",
        "made the path safe",
        "a lost lamb",
    ),
    "comfort": KindAct(
        "comfort",
        "comfort the crying bird",
        "comforting the crying bird",
        "brought calm to the air",
        "a crying bird",
    ),
    "carry": KindAct(
        "carry",
        "carry the old basket",
        "carrying the old basket",
        "showed steady hands",
        "an old basket",
    ),
}

HERO_NAMES = ["Mira", "Theo", "Lina", "Kai", "Nora", "Eli"]
HERO_TYPES = ["girl", "boy"]
GUARDIAN_TYPES = ["old woman", "old man", "river spirit", "stone owl"]

# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    guardian: str
    kindness: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES:
        for k in KIND_ACTS:
            combos.append((place, k))
    return combos


def explain_rejection(_: str, __: str) -> str:
    return "(No story: this myth needs a kindness act that the world can actually show.)"


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"wonder": 1.0, "worry": 0.0, "heard": 0.0},
        memes={"wonder": 1.0, "worry": 0.0, "pride": 0.0, "trust": 0.0, "kindness": 0.0, "joy": 0.0},
    ))
    guardian = world.add(Entity(
        id="guardian",
        kind="character",
        type=params.guardian,
        label=params.guardian,
        meters={"hush": 1.0, "closed": 1.0, "open": 0.0},
        memes={"trust": 0.0, "worry": 1.0, "joy": 0.0},
    ))
    relic = world.add(Entity(
        id="relic",
        kind="thing",
        type="trumpet",
        label="trumpet",
        phrase=RELICS["solid_trumpet"].phrase,
        owner=hero.id,
        meters={"polish": 1.0, "heard": 0.0},
        memes={"wonder": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="child",
        label="a small child",
        meters={"need": 1.0},
        memes={"hope": 1.0, "worry": 1.0},
    ))

    world.facts.update(hero=hero, guardian=guardian, relic=relic, helper=helper,
                       kindness=KIND_ACTS[params.kindness], place=world.place,
                       relic_cfg=RELICS["solid_trumpet"])
    return world


def sound_effect(text: str) -> str:
    return text


def do_kindness(world: World) -> None:
    hero: Entity = world.facts["hero"]
    guardian: Entity = world.facts["guardian"]
    helper: Entity = world.facts["helper"]
    act: KindAct = world.facts["kindness"]

    hero.memes["kindness"] += 1
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    helper.memes["hope"] += 1
    helper.meters["need"] = 0.0
    guardian.memes["trust"] += 1
    guardian.memes["worry"] = 0.0
    guardian.meters["closed"] = 0.0
    guardian.meters["open"] = 1.0

    world.say(
        f"{hero.label} saw {act.target} and said, "
        f"'{act.verb.capitalize()} first,' because {hero.pronoun('subject')} knew a kind heart was wiser than a hurried toot."
    )
    world.say(
        f"So {hero.label} went {act.gerund}, and at once the air felt softer."
    )


def wake_trumpet(world: World) -> None:
    hero: Entity = world.facts["hero"]
    guardian: Entity = world.facts["guardian"]
    relic: Entity = world.facts["relic"]

    if hero.memes["kindness"] < THRESHOLD:
        raise StoryError("The trumpet stays silent until kindness happens first.")

    relic.meters["heard"] = 1.0
    hero.meters["heard"] = 1.0
    guardian.meters["hush"] = 0.0
    hero.memes["wonder"] += 1
    guardian.memes["joy"] += 1
    hero.memes["trust"] += 1

    world.say(
        f"Then {hero.label} lifted the {relic.label} and breathed in."
    )
    world.say(
        f'"{sound_effect(relic_cfg_sound())}" went the solid trumpet, bright as a star waking.'
    )
    world.say(
        f'The guardian smiled and said, "Now the hill may answer."'
    )


def relic_cfg_sound() -> str:
    return RELICS["solid_trumpet"].sound


def open_mythic_path(world: World) -> None:
    guardian: Entity = world.facts["guardian"]
    hero: Entity = world.facts["hero"]

    guardian.meters["closed"] = 0.0
    guardian.meters["open"] = 1.0
    hero.memes["joy"] += 1
    hero.meters["heard"] = 1.0

    world.say(
        f"The earth answered with a low hum, and a hidden path opened where the stones had looked solid as sleep."
    )
    world.say(
        f"{hero.label} stepped forward, and the guardian walked beside {hero.pronoun('object')} without fear."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero: Entity = world.facts["hero"]
    guardian: Entity = world.facts["guardian"]
    relic: Entity = world.facts["relic"]
    place = world.place

    world.say(
        f"On {place.label}, where {place.atmosphere}, {hero.label} found {relic.phrase} resting in the grass."
    )
    world.say(
        f'The guardian said, "{relic.label.capitalize()} is not for greedy noise. It sings for a kind hand."'
    )
    world.para()
    world.say(
        f"{hero.label} wanted to blow it at once, for the trumpet looked strong and shining."
    )
    world.say(
        f'But {guardian.label} lifted a finger and warned, "Wait. First do one kind thing."'  # dialogue
    )
    world.say(
        f"{hero.label} looked at the lonely little one nearby and chose to help instead of boasting."
    )

    world.para()
    do_kindness(world)
    wake_trumpet(world)
    open_mythic_path(world)

    world.facts["resolved"] = True
    world.facts["conflict"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    kindness: KindAct = f["kindness"]
    return [
        f'Write a short myth for a young child about {hero.label}, {RELICS["solid_trumpet"].label}, and a kind choice that unlocks a hidden path.',
        f'Create a gentle mythic story with dialogue and a sound effect where {hero.label} must {kindness.verb} before the trumpet can sing.',
        f'Write a child-facing myth where kindness matters more than rushing, and the trumpet sounds "TOOT-TOOT!" after someone helps.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    guardian: Entity = f["guardian"]
    relic: Entity = f["relic"]
    kindness: KindAct = f["kindness"]
    place: Place = f["place"]

    return [
        QAItem(
            question=f"What did {hero.label} find on {place.label}?",
            answer=f"{hero.label} found {relic.phrase} on {place.label}, shining in the quiet grass.",
        ),
        QAItem(
            question=f"What did the guardian ask before the trumpet could sing?",
            answer=f"The guardian asked {hero.label} to {kindness.verb} first, because kindness was the key to waking the trumpet.",
        ),
        QAItem(
            question=f"How did the story end after the trumpet sounded?",
            answer=f"It ended with a hidden path opening and {hero.label} walking forward with the guardian beside {hero.pronoun('object')}.",
        ),
        QAItem(
            question=f"Why did {hero.label} choose to help the little one?",
            answer=f"{hero.label} chose to help because the myth said a solid trumpet only answers a kind heart, and {hero.label} wanted the world to wake gently.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a trumpet?",
            answer="A trumpet is a brass wind instrument. When someone blows into it, the trumpet can make a loud, bright sound.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping, sharing, or comforting someone in a gentle way.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a little written sound like toot-toot or splash that helps you imagine what you would hear.",
        ),
    ]


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


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid_place(P) :- place(P).
valid_kindness(K) :- kindness(K).
valid_story(P, K) :- valid_place(P), valid_kindness(K).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for kid in KIND_ACTS:
        lines.append(asp.fact("kindness", kid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
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
# CLI helpers
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny myth world of a solid trumpet and a kind choice.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--kindness", choices=sorted(KIND_ACTS))
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--guardian", choices=GUARDIAN_TYPES)
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
    place = args.place or rng.choice(list(PLACES))
    kindness = args.kindness or rng.choice(list(KIND_ACTS))
    name = args.name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    guardian = args.guardian or rng.choice(GUARDIAN_TYPES)
    if (place, kindness) not in valid_combos():
        raise StoryError(explain_rejection(place, kindness))
    return StoryParams(place=place, hero_name=name, hero_type=hero_type, guardian=guardian, kindness=kindness)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="hill", hero_name="Mira", hero_type="girl", guardian="river spirit", kindness="share"),
    StoryParams(place="cave", hero_name="Theo", hero_type="boy", guardian="stone owl", kindness="help"),
    StoryParams(place="shore", hero_name="Lina", hero_type="girl", guardian="old woman", kindness="comfort"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for place, kindness in combos:
            print(f"  {place:8} {kindness}")
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
            header = f"### {p.hero_name}: {p.kindness} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
