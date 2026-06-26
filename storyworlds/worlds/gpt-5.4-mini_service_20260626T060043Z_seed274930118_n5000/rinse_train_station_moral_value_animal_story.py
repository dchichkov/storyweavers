#!/usr/bin/env python3
"""
storyworlds/worlds/rinse_train_station_moral_value_animal_story.py
==================================================================

A small animal-story world set in a train station, centered on rinse, moral
value, and a gentle compromise.

The seed tale:
---
A little rabbit named Miso lived near a busy train station. Miso loved helping
people carry lost things to the right platform, but one rainy morning Miso
hopped through a puddle and got muddy. Miso was proud of being useful, yet the
mud made the station floor slippery and the train bench messy.

A station cat named Tavi noticed and said, "If you rinse your paws first, you
can help without spreading mud everywhere." Miso felt embarrassed, then
thought about being considerate. So Miso rinsed at the station sink, dried off
carefully, and went back to helping. The floor stayed clean, the passengers
smiled, and Miso felt proud for doing the right thing.

World model:
- A small animal character has meters for mud and water, plus memes for pride,
  embarrassment, and consideration.
- The station has a sink, a bench, a platform, and a puddle near the entrance.
- Rinsing lowers mud and raises cleanliness; refusing to rinse risks making the
  station floor slick and messy.
- The story turns on a moral choice: clean up first, then help others.

This world keeps the prose child-facing and state-driven while allowing only a
small set of reasonable variations.
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
    kind: str = "thing"  # "animal" | "helper" | "place" | "thing"
    species: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "it"

    def poss(self) -> str:
        return "its"


@dataclass
class Station:
    name: str = "the train station"
    has_sink: bool = True
    has_bench: bool = True
    has_platform: bool = True


@dataclass
class CharacterCfg:
    species: str
    label: str
    phrase: str
    moral_value: str
    help_verb: str


@dataclass
class StoryParams:
    animal: str
    helper: str
    value: str
    seed: Optional[int] = None


class World:
    def __init__(self, station: Station) -> None:
        self.station = station
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


ANIMALS = {
    "rabbit": CharacterCfg(
        species="rabbit",
        label="rabbit",
        phrase="a little rabbit",
        moral_value="consideration",
        help_verb="help",
    ),
    "mouse": CharacterCfg(
        species="mouse",
        label="mouse",
        phrase="a tiny mouse",
        moral_value="kindness",
        help_verb="carry",
    ),
    "fox": CharacterCfg(
        species="fox",
        label="fox",
        phrase="a small fox",
        moral_value="patience",
        help_verb="guide",
    ),
}

HELPERS = {
    "cat": CharacterCfg(
        species="cat",
        label="cat",
        phrase="a calm station cat",
        moral_value="care",
        help_verb="show",
    ),
    "dog": CharacterCfg(
        species="dog",
        label="dog",
        phrase="a friendly station dog",
        moral_value="helpfulness",
        help_verb="show",
    ),
    "owl": CharacterCfg(
        species="owl",
        label="owl",
        phrase="a wise station owl",
        moral_value="thoughtfulness",
        help_verb="show",
    ),
}

VALUES = {
    "consideration": "consideration",
    "kindness": "kindness",
    "patience": "patience",
    "care": "care",
    "helpfulness": "helpfulness",
    "thoughtfulness": "thoughtfulness",
}

CURATED = [
    StoryParams(animal="rabbit", helper="cat", value="consideration"),
    StoryParams(animal="mouse", helper="dog", value="kindness"),
    StoryParams(animal="fox", helper="owl", value="patience"),
]

GREETINGS = {
    "rabbit": "hopped through the station with quick little steps",
    "mouse": "hurried along with a tiny satchel",
    "fox": "trotted past the ticket board",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world at a train station with a rinse-and-care moral."
    )
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--value", choices=VALUES)
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
    animal = args.animal or rng.choice(sorted(ANIMALS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    value = args.value or ANIMALS[animal].moral_value
    if value != ANIMALS[animal].moral_value:
        raise StoryError("This animal story only supports the animal's matched moral value.")
    if helper == animal:
        raise StoryError("The helper should be a different station animal.")
    return StoryParams(animal=animal, helper=helper, value=value)


def world_cfg(params: StoryParams) -> tuple[CharacterCfg, CharacterCfg]:
    return ANIMALS[params.animal], HELPERS[params.helper]


def make_world(params: StoryParams) -> World:
    animal_cfg, helper_cfg = world_cfg(params)
    w = World(Station())
    hero = w.add(Entity(
        id="hero",
        kind="animal",
        species=animal_cfg.species,
        label=animal_cfg.label,
        phrase=animal_cfg.phrase,
        role="hero",
        meters={"mud": 0.0, "clean": 1.0, "help": 0.0},
        memes={"pride": 0.5, "embarrassment": 0.0, "consideration": 0.0, "joy": 0.2},
    ))
    helper = w.add(Entity(
        id="helper",
        kind="helper",
        species=helper_cfg.species,
        label=helper_cfg.label,
        phrase=helper_cfg.phrase,
        role="guide",
        meters={"clean": 1.0},
        memes={"care": 0.5, "joy": 0.3},
    ))
    sink = w.add(Entity(id="sink", kind="place", label="sink", phrase="the station sink"))
    platform = w.add(Entity(id="platform", kind="place", label="platform", phrase="the platform"))
    bench = w.add(Entity(id="bench", kind="place", label="bench", phrase="a wooden bench"))
    puddle = w.add(Entity(id="puddle", kind="thing", label="puddle", phrase="a muddy puddle"))

    w.facts.update(hero=hero, helper=helper, sink=sink, platform=platform, bench=bench, puddle=puddle)
    return w


def intro(w: World) -> None:
    hero = w.facts["hero"]
    helper = w.facts["helper"]
    w.say(f"{hero.phrase.capitalize()} lived near {w.station.name} and always noticed when someone needed help.")
    w.say(f"Nearby, {helper.phrase} watched the crowds with a calm smile.")


def setup(w: World) -> None:
    hero = w.facts["hero"]
    puddle = w.facts["puddle"]
    hero.meters["mud"] += 1.0
    hero.meters["clean"] = 0.0
    hero.memes["pride"] += 0.2
    w.say(f"One rainy morning, {hero.id} {GREETINGS[hero.species]} and stepped into {puddle.phrase}.")
    w.say(f"Sticky mud clung to {hero.poss()} paws, and the station floor started to look messy.")


def warn_and_turn(w: World) -> None:
    hero = w.facts["hero"]
    helper = w.facts["helper"]
    sink = w.facts["sink"]
    hero.memes["embarrassment"] += 1.0
    hero.memes["consideration"] += 0.5
    w.say(f"{helper.phrase.capitalize()} noticed at once and said, 'If you rinse your paws first, everyone stays safer.'")
    w.say(f"{hero.id} looked at {sink.phrase}, then at the bench and the platform, and felt a little embarrassed.")
    w.say("The little animal understood that helping was kind, but helping without making a mess was kinder.")


def rinse(w: World) -> None:
    hero = w.facts["hero"]
    sink = w.facts["sink"]
    hero.meters["mud"] = max(0.0, hero.meters["mud"] - 1.0)
    hero.meters["clean"] = 1.0
    hero.memes["embarrassment"] = max(0.0, hero.memes["embarrassment"] - 0.5)
    hero.memes["consideration"] += 1.0
    w.say(f"So {hero.id} went to {sink.phrase} and gave {hero.poss()} paws a careful rinse.")
    w.say(f"The muddy drip-drip washed away, and {hero.id} felt fresh and ready to do the right thing.")


def help_others(w: World) -> None:
    hero = w.facts["hero"]
    helper = w.facts["helper"]
    platform = w.facts["platform"]
    bench = w.facts["bench"]
    hero.meters["help"] += 1.0
    hero.memes["joy"] += 1.0
    hero.memes["pride"] += 0.7
    w.say(f"After that, {hero.id} joined {helper.id} near {platform.phrase} and helped carry lost tickets to the right people.")
    w.say(f"The bench stayed clean, the floor stayed safe, and the passengers smiled as {hero.id} worked kindly beside {helper.id}.")
    w.say(f"By the time the train arrived, {hero.id} felt proud for being helpful and thoughtful at the same time.")


def tell(params: StoryParams) -> World:
    w = make_world(params)
    intro(w)
    w.lines.append("")
    setup(w)
    warn_and_turn(w)
    rinse(w)
    help_others(w)
    w.facts["resolved"] = True
    return w


def generation_prompts(w: World) -> list[str]:
    hero = w.facts["hero"]
    helper = w.facts["helper"]
    return [
        "Write a short, gentle animal story set at a train station about doing the right thing before helping others.",
        f"Tell a story where {hero.phrase} gets muddy, {helper.phrase} suggests rinsing, and the station stays clean.",
        "Write a child-friendly story with a clear moral about being considerate in a busy public place.",
    ]


def story_qa(w: World) -> list[QAItem]:
    hero = w.facts["hero"]
    helper = w.facts["helper"]
    return [
        QAItem(
            question=f"Why did {helper.phrase} ask {hero.phrase} to rinse first?",
            answer="Because the muddy paws could make the station floor messy and slippery, and rinsing first was the considerate choice.",
        ),
        QAItem(
            question=f"What did {hero.phrase} do at the sink?",
            answer=f"{hero.id} gave those muddy paws a careful rinse, and the water washed the mud away.",
        ),
        QAItem(
            question=f"How did {hero.phrase} feel after helping the passengers?",
            answer="The little animal felt proud and happy, because helping carefully was the right thing to do.",
        ),
    ]


def world_knowledge_qa(w: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a train station?",
            answer="A train station is a place where people wait for trains, buy tickets, and go to different destinations.",
        ),
        QAItem(
            question="Why do people rinse dirty paws or hands?",
            answer="People rinse dirty paws or hands to wash off mud or sticky dirt so they stay clean and do not spread mess around.",
        ),
        QAItem(
            question="What does consideration mean?",
            answer="Consideration means thinking about other people and choosing actions that do not cause them trouble.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(w: World) -> str:
    parts = ["--- world trace ---"]
    for e in w.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        parts.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(parts)


ASP_RULES = r"""
hero_needs_rinse(H) :- mud(H, M), M > 0.
considerate(H) :- rinsed(H), helped(H).
safe_station :- rinsed(hero), helped(hero).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("mud", "hero", 1),
        asp.fact("at", "hero", "station"),
        asp.fact("at", "helper", "station"),
        asp.fact("place", "station"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe_station/0. #show hero_needs_rinse/1. #show considerate/1."))
    atoms = set((sym.name, len(sym.arguments)) for sym in model)
    wanted = {("hero_needs_rinse", 1), ("considerate", 1), ("safe_station", 0)}
    if atoms == wanted:
        print("OK: ASP twin is present.")
        return 0
    print("MISMATCH in ASP twin.")
    return 1


def generate(params: StoryParams) -> StorySample:
    w = tell(params)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_knowledge_qa(w),
        world=w,
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


def resolve_from_curated(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    p = rng.choice(CURATED)
    return StoryParams(animal=p.animal, helper=p.helper, value=p.value, seed=p.seed)


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show safe_station/0."))
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
            rng = random.Random(seed)
            try:
                params = resolve_from_curated(args, rng) if not any(
                    getattr(args, x) is not None for x in ("animal", "helper", "value")
                ) else resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
