#!/usr/bin/env python3
"""
A standalone story world for a small Animal Story domain with a nightmare, a
flashback, and a comforting turn.

Premise:
- A young animal has a cozy day, then a frightening nightmare.
- A flashback reminds the animal of a previous brave moment.
- The remembered action helps the animal recover and end safe.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib story generator
- typed entities with meters and memes
- inline ASP twin and Python reasonableness gate
- story + QA + trace + JSON + verify modes
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
# Entities / world model
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "bunny", "hare", "kitten", "cat"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    cozy: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Feeling:
    name: str
    meter: str


@dataclass
class Memory:
    id: str
    cue: str
    brave_action: str
    helper: str
    object: str


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
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "nest": Setting(place="the little nest", cozy=True, affords={"sleep", "hide"}),
    "den": Setting(place="the warm den", cozy=True, affords={"sleep", "hide"}),
    "barn": Setting(place="the quiet barn", cozy=True, affords={"sleep", "hide"}),
    "meadow": Setting(place="the sunny meadow", cozy=False, affords={"run", "play"}),
}

ACTIONS = {
    "sleep": "fall asleep",
    "hide": "hide under a blanket",
    "run": "run fast",
    "play": "play softly",
}

FEARS = {
    "dark": Feeling(name="darkness", meter="fear"),
    "wind": Feeling(name="wind", meter="fear"),
    "noise": Feeling(name="loud noise", meter="fear"),
    "shadows": Feeling(name="shadows", meter="fear"),
}

MEMORIES = {
    "rain": Memory(
        id="rain",
        cue="the soft tapping of rain on the roof",
        brave_action="stayed under a leaf with a friend until the storm passed",
        helper="an older rabbit",
        object="leaf",
    ),
    "storm": Memory(
        id="storm",
        cue="a stormy night with the barn door creaking",
        brave_action="held still and listened until the wind calmed",
        helper="a gentle mouse",
        object="blanket",
    ),
    "lost": Memory(
        id="lost",
        cue="being alone for a moment in tall grass",
        brave_action="followed a friendly song back home",
        helper="a singing bird",
        object="path",
    ),
}

CHARACTERS = {
    "bunny": {"types": {"bunny", "rabbit"}, "name": ["Milo", "Nina", "Pip", "Luna", "Toby"]},
    "kitten": {"types": {"kitten", "cat"}, "name": ["Mimi", "Kiko", "Tia", "Moss", "Bello"]},
    "fox": {"types": {"fox"}, "name": ["Faro", "Saffy", "Rill", "Jun", "Poco"]},
}

DEFAULT_NAMES = ["Milo", "Nina", "Pip", "Luna", "Toby", "Mimi", "Kiko"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    protagonist: str
    memory: str
    fear: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------
def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.protagonist not in CHARACTER_TYPES:
        raise StoryError("Unknown protagonist type.")
    if params.memory not in MEMORIES:
        raise StoryError("Unknown memory.")
    if params.fear not in FEARS:
        raise StoryError("Unknown fear.")
    if params.setting == "meadow" and params.fear == "dark":
        raise StoryError("This story needs a cozy place for a nighttime nightmare flashback.")
    if params.setting == "meadow" and params.memory == "rain":
        raise StoryError("The flashback needs a sheltered place where the sound can be remembered safely.")


def _narrate_nightmare(world: World, hero: Entity, fear: Feeling) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    world.say(
        f"At bedtime, {hero.id} tried to curl up and rest, but a nightmare slid into the dark. "
        f"It felt like {fear.name} was too big to fit in the room."
    )
    world.say(
        f"{hero.id} woke with a tiny gasp and clung to the blanket, shaking and wide awake."
    )


def _narrate_flashback(world: World, hero: Entity, memory: Memory) -> None:
    hero.memes["remembering"] = hero.memes.get("remembering", 0.0) + 1
    world.say(
        f"Then a flashback flickered through {hero.id}'s mind: {memory.cue}."
    )
    world.say(
        f"{hero.id} remembered how {memory.helper} helped, and how {hero.id} had once {memory.brave_action}."
    )


def _narrate_turn(world: World, hero: Entity, memory: Memory) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1)
    world.say(
        f"That memory made the nightmare feel smaller. {hero.id} took a slow breath, counted to three, and hugged the {memory.object} close."
    )


def _narrate_resolution(world: World, hero: Entity) -> None:
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    world.say(
        f"By the end, {hero.id} was sleepy again. The room stayed quiet, the dark stayed outside, and the little animal rested safely at last."
    )


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    setting = SETTINGS[params.setting]
    world = World(setting)

    hero_name = params.protagonist_name
    hero_type = params.protagonist
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            label=hero_name,
            meters={"sleepiness": 0.5},
            memes={"comfort": 1.0},
        )
    )

    memory = MEMORIES[params.memory]
    fear = FEARS[params.fear]

    world.say(
        f"{hero.id} was a little {hero.type} who loved the cozy place called {setting.place}."
    )
    world.say(
        f"When the day was soft and calm, {hero.id} played a little, then got ready for bed."
    )

    world.para()
    _narrate_nightmare(world, hero, fear)

    world.para()
    _narrate_flashback(world, hero, memory)
    _narrate_turn(world, hero, memory)

    world.para()
    _narrate_resolution(world, hero)

    world.facts.update(
        hero=hero,
        setting=setting,
        memory=memory,
        fear=fear,
        resolved=True,
        nightmare=True,
        flashback=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    memory: Memory = f["memory"]
    fear: Feeling = f["fear"]
    return [
        f'Write a short Animal Story about {hero.id}, a little {hero.type}, who has a nightmare and remembers a brave moment in a flashback.',
        f"Tell a gentle bedtime story where {hero.id} feels scared of {fear.name} but then remembers {memory.cue}.",
        f'Write a cozy story for a young child that uses the word "nightmare" and includes a flashback that helps the hero calm down.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    memory: Memory = f["memory"]
    fear: Feeling = f["fear"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.type} who starts out cozy and then gets frightened by a nightmare.",
        ),
        QAItem(
            question=f"What scared {hero.id} in the nightmare?",
            answer=f"The nightmare made {fear.name} feel huge and scary to {hero.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=f"{hero.id} remembered {memory.cue}, and that memory helped {hero.id} feel braver.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} calm, sleepy, and safe again in the cozy place.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nightmare?",
            answer="A nightmare is a very scary dream that can wake someone up feeling frightened.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when a memory suddenly comes back into your mind like a small scene from the past.",
        ),
        QAItem(
            question="Why can a cozy place help after a scary dream?",
            answer="A cozy place can help because warm blankets, quiet sounds, and a safe bed make it easier to relax again.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting_ok(S) :- setting(S).
fear_ok(F) :- fear(F).
memory_ok(M) :- memory(M).

valid_story(S, P, M, F) :- setting_ok(S), protagonist(P), memory_ok(M), fear_ok(F),
                           cozy(S), not bad_combo(S, M, F).
bad_combo(meadow, _, _, dark).
bad_combo(meadow, rain, _, _).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.cozy:
            lines.append(asp.fact("cozy", sid))
    for pid in CHARACTER_TYPES:
        lines.append(asp.fact("protagonist", pid))
    for fid in FEARS:
        lines.append(asp.fact("fear", fid))
    for mid in MEMORIES:
        lines.append(asp.fact("memory", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_stories())
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def valid_stories() -> list[tuple]:
    out = []
    for sid in SETTINGS:
        for pid in CHARACTER_TYPES:
            for mid in MEMORIES:
                for fid in FEARS:
                    if sid == "meadow" and fid == "dark":
                        continue
                    if sid == "meadow" and mid == "rain":
                        continue
                    if SETTINGS[sid].cozy:
                        out.append((sid, pid, mid, fid))
    return out


# ---------------------------------------------------------------------------
# CLI / generation
# ---------------------------------------------------------------------------
CHARACTER_TYPES = {"bunny", "kitten", "fox"}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world with a nightmare flashback.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--protagonist", choices=sorted(CHARACTER_TYPES))
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--fear", choices=FEARS)
    ap.add_argument("--name")
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
    settings = [args.setting] if args.setting else list(SETTINGS)
    prots = [args.protagonist] if args.protagonist else list(CHARACTER_TYPES)
    mems = [args.memory] if args.memory else list(MEMORIES)
    fears = [args.fear] if args.fear else list(FEARS)
    combos = []
    for s in settings:
        for p in prots:
            for m in mems:
                for f in fears:
                    cand = StoryParams(setting=s, protagonist=p, memory=m, fear=f)
                    try:
                        reasonableness_gate(cand)
                    except StoryError:
                        continue
                    combos.append(cand)
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    pick = rng.choice(combos)
    name = args.name or rng.choice(DEFAULT_NAMES)
    pick.protagonist_name = name  # type: ignore[attr-defined]
    return pick


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
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


def curated_params() -> list[StoryParams]:
    return [
        StoryParams(setting="nest", protagonist="bunny", memory="rain", fear="dark"),
        StoryParams(setting="den", protagonist="kitten", memory="storm", fear="wind"),
        StoryParams(setting="barn", protagonist="fox", memory="lost", fear="shadows"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_stories())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p in curated_params():
            p.protagonist_name = "Milo"  # type: ignore[attr-defined]
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
