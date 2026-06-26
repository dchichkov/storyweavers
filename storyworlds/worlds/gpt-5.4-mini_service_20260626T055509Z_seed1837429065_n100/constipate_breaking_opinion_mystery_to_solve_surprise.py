#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100/constipate_breaking_opinion_mystery_to_solve_surprise.py
===============================================================================================================

A small superhero-story world about a puzzling city problem, a careful
investigation, and a surprise ending that changes what the hero understands.

The seed words are woven into the world as a comic-book newspaper headline
("Breaking Opinion"), a goofy villain codename ("Constipate"), and the central
idea that heroes must still notice what people think and feel ("opinion").

This world models:
- a hero with courage and curiosity
- a city setting with physical danger and social trust
- a mystery that can be solved by collecting clues
- a surprise reveal that resolves the mystery in a satisfying way

The story keeps a superhero tone: capes, rooftop chases, city lights, and a
gentle final victory.
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

HINT_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "heroine", "mother"}
        male = {"boy", "man", "hero", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    vibe: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    clue: str
    cause: str
    danger: str
    solved_by: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    label: str
    reveal: str
    fix: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


def pair_ok(mystery: Mystery, surprise: Surprise) -> bool:
    return mystery.solved_by in surprise.tags or mystery.id in surprise.tags


SETTINGS = {
    "city": Setting(place="Metro City", vibe="bright rooftops", affords={"chase", "investigate", "rescue"}),
    "museum": Setting(place="the city museum", vibe="quiet halls", affords={"investigate", "rescue"}),
    "harbor": Setting(place="the harbor", vibe="windy docks", affords={"chase", "investigate"}),
}

MYSTERIES = {
    "broken_statue": Mystery(
        id="broken_statue",
        label="the cracked hero statue",
        clue="a tiny silver bolt",
        cause="a runaway cleaning drone",
        danger="the whole plaza might close",
        solved_by="drone",
        tags={"city", "drone", "metal"},
    ),
    "missing_mask": Mystery(
        id="missing_mask",
        label="the missing moon mask",
        clue="chalk dust on the balcony",
        cause="a secret attic door",
        danger="the gala might begin without the mask",
        solved_by="hidden_door",
        tags={"museum", "secret", "door"},
    ),
    "silent_signal": Mystery(
        id="silent_signal",
        label="the silent sky signal",
        clue="a flicker on the harbor tower",
        cause="a jammed antenna",
        danger="the rescue team could miss the alert",
        solved_by="antenna",
        tags={"harbor", "signal", "tower"},
    ),
}

SURPRISES = {
    "tiny_helper": Surprise(
        id="tiny_helper",
        label="a tiny helper robot",
        reveal="the robot was not the culprit; it was trying to show the clue",
        fix="it pointed the hero toward the real problem",
        tags={"drone", "robot", "city"},
    ),
    "hidden_door": Surprise(
        id="hidden_door",
        label="a hidden attic door",
        reveal="the strange noise came from a secret door behind a painting",
        fix="opening it led straight to the missing mask",
        tags={"hidden_door", "secret", "door", "museum"},
    ),
    "friendly_wind": Surprise(
        id="friendly_wind",
        label="a gust of helpful wind",
        reveal="the hero realized the tower was whispering a path through the fog",
        fix="the wind carried the signal past the jammed spot",
        tags={"antenna", "signal", "tower", "harbor"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    mystery: str
    surprise: str
    hero_name: str
    hero_type: str
    helper_name: str
    seed: Optional[int] = None


HERO_NAMES = ["Nova", "Spark", "Comet", "Mira", "Atlas", "Jett", "Vega"]
HELPER_NAMES = ["Pip", "Rook", "Nim", "Bea", "Zee"]
HERO_TYPES = ["hero", "heroine", "boy", "girl"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero mystery story world with a surprise ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper-name")
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for m in MYSTERIES.values():
            if s in m.tags or "city" in m.tags or "museum" in m.tags or "harbor" in m.tags:
                for u in SURPRISES.values():
                    if pair_ok(m, u):
                        out.append((s, m.id, u.id))
    return sorted(set(out))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, surprise = rng.choice(combos)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(setting=setting, mystery=mystery, surprise=surprise, hero_name=hero_name, hero_type=hero_type, helper_name=helper_name)


def _setup(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(
        f"On a glittering night in {world.setting.place}, {hero.id} swept across the rooftops in a bright cape."
    )
    world.say(
        f"{hero.pronoun().capitalize()} cared about every opinion the city held, because heroes need trust as much as courage."
    )
    world.say(
        f"That evening, a mystery arrived: {mystery.label} had gone wrong, and the whole plaza listened to the worried whisper of {mystery.danger}."
    )
    world.say(
        f"{helper.id}, {helper.pronoun('object')} little sidekick, hurried along with a notebook and flashlight."
    )


def _investigate(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["resolve"] = hero.memes.get("resolve", 0) + 1
    world.para()
    world.say(
        f"{hero.id} followed the first clue, {mystery.clue}, from the fountain steps to the alley behind the comic shop."
    )
    world.say(
        f"{helper.id} found a second hint and said it was like a headline in the paper: Breaking Opinion, the kind that makes everyone stop and look up."
    )
    world.say(
        f"The clue trail pointed to {mystery.cause}, but it did not yet explain why the city had gone quiet."
    )


def _turn(world: World, hero: Entity, helper: Entity, surprise: Surprise, mystery: Mystery) -> None:
    world.para()
    world.say(
        f"Then came the surprise: {surprise.label} blinked out of the shadows."
    )
    world.say(
        f"At first, {hero.id} thought it was the culprit, but {surprise.reveal}."
    )
    world.say(
        f"That changed everything, because the real answer fit the mystery better than the first guess did."
    )
    world.say(
        f"{helper.id} grinned and pointed at the last clue, showing how the surprise could {surprise.fix}."
    )


def _resolution(world: World, hero: Entity, helper: Entity, mystery: Mystery, surprise: Surprise) -> None:
    world.para()
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    world.say(
        f"With one careful move, {hero.id} solved the mystery and fixed the problem before the city had to fear the dark."
    )
    world.say(
        f"The cracked statue was mended, the missing signal answered, or the hidden door opened exactly where it needed to be, depending on the case."
    )
    world.say(
        f"By dawn, {helper.id} was laughing beside {hero.id}, and the city had a new opinion: its heroes could solve even a strange surprise."
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    surprise = SURPRISES[params.surprise]
    world = World(setting)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, traits=["brave", "curious"]))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="sidekick", traits=["quick", "smart"]))

    world.facts.update(setting=setting, mystery=mystery, surprise=surprise, hero=hero, helper=helper)

    _setup(world, hero, helper, mystery)
    _investigate(world, hero, helper, mystery)
    _turn(world, hero, helper, surprise, mystery)
    _resolution(world, hero, helper, mystery, surprise)

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
    return [
        f'Write a superhero mystery story for a young child set in {f["setting"].place} that includes the words "constipate", "breaking", and "opinion".',
        f"Tell a gentle comic-style story where {f['hero'].id} follows a clue, discovers a surprise, and solves {f['mystery'].label}.",
        "Write a short action story with a mystery to solve, a surprise reveal, and a happy ending in a city full of capes.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mystery = f["mystery"]
    surprise = f["surprise"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Where did {hero.id} begin solving the mystery?",
            answer=f"{hero.id} began in {setting.place}, where the rooftops and streets gave the hero a place to search for clues.",
        ),
        QAItem(
            question=f"What clue started the search for {mystery.label}?",
            answer=f"The first clue was {mystery.clue}, and it helped {hero.id} and {helper.id} follow the mystery step by step.",
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer=f"The surprise was {surprise.label}, and it changed the hero's first guess into the true answer.",
        ),
        QAItem(
            question=f"How was the mystery solved in the end?",
            answer=f"{hero.id} used the clues, listened carefully, and applied the surprise to fix the real problem behind {mystery.label}.",
        ),
        QAItem(
            question=f"Why did the city care about the mystery?",
            answer=f"The mystery mattered because {mystery.danger}, so everyone needed a hero to find the truth quickly.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a mystery mean in a superhero story?",
            answer="A mystery is a problem with a hidden cause, so the hero has to gather clues and think carefully to find the truth.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is a new reveal that changes what the characters thought before, often making the ending more exciting or kind.",
        ),
        QAItem(
            question="Why do heroes listen to opinions?",
            answer="Heroes listen to opinions because people in the city need to trust them, and good heroes care about how their actions affect others.",
        ),
        QAItem(
            question="What is a sidekick for?",
            answer="A sidekick helps the hero notice clues, stay brave, and keep the mission moving when the mystery is tricky.",
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
        bits = []
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="city", mystery="broken_statue", surprise="tiny_helper", hero_name="Nova", hero_type="hero", helper_name="Pip"),
    StoryParams(setting="museum", mystery="missing_mask", surprise="hidden_door", hero_name="Mira", hero_type="heroine", helper_name="Nim"),
    StoryParams(setting="harbor", mystery="silent_signal", surprise="friendly_wind", hero_name="Comet", hero_type="hero", helper_name="Zee"),
]


ASP_RULES = r"""
setting(city).
setting(museum).
setting(harbor).

mystery(broken_statue).
mystery(missing_mask).
mystery(silent_signal).

surprise(tiny_helper).
surprise(hidden_door).
surprise(friendly_wind).

solves(broken_statue, tiny_helper).
solves(missing_mask, hidden_door).
solves(silent_signal, friendly_wind).

valid(S, M, U) :- setting(S), mystery(M), surprise(U), solves(M, U).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for u in SURPRISES:
        lines.append(asp.fact("surprise", u))
    for m, surp in [("broken_statue", "tiny_helper"), ("missing_mask", "hidden_door"), ("silent_signal", "friendly_wind")]:
        lines.append(asp.fact("solves", m, surp))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_reasonable_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MYSTERIES.values():
            if s in m.tags or s == "city" or s == "museum" or s == "harbor":
                for u in SURPRISES.values():
                    if pair_ok(m, u):
                        combos.append((s, m.id, u.id))
    return sorted(set(combos))


def valid_combos() -> list[tuple[str, str, str]]:
    return build_reasonable_combos()


def resolve_all_filtered(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    s, m, u = rng.choice(combos)
    return StoryParams(
        setting=s,
        mystery=m,
        surprise=u,
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        hero_type=args.hero_type or rng.choice(HERO_TYPES),
        helper_name=args.helper_name or rng.choice(HELPER_NAMES),
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story combos:")
        for s, m, u in asp_valid_combos():
            print(f"  {s:8} {m:14} {u:13}")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_all_filtered(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
            header = f"### {p.hero_name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
