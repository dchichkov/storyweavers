#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/trillion_construction_site_misunderstanding_ghost_story.py
==========================================================================================

A standalone storyworld for a tiny ghost-story-like misunderstanding set at a
construction site.

Premise:
- A child and a grown-up are near a construction site at dusk.
- Strange sounds, tarps, lights, and shadows create a ghost-story mood.
- The child misunderstands ordinary site noises as a ghost.
- A calm helper reveals the real cause.
- The ending proves the misunderstanding is resolved, with a concrete final image.

This script follows the Storyweavers storyworld contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, --show-asp
- includes Python validity checks and an inline ASP twin
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2

GHOST_WORDS = {"ghost", "haunt", "haunted", "spook", "spooky"}
NIGHT_WORDS = {"dusk", "dark", "moon", "lamp"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    details: str


@dataclass
class Clue:
    id: str
    label: str
    sound: str
    glow: str
    clue_type: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    fear: str
    explanation: str
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "construction_site": Setting(
        "construction_site",
        "the construction site",
        "spooky",
        "cones, steel beams, a tarp wall, and a tall crane that creaked in the wind",
    ),
}

CLUES = {
    "tarp": Clue("tarp", "a blue tarp", "flap-flap", "blue in the lamp light", "cloth",
                 {"tarp", "cloth"}),
    "bucket": Clue("bucket", "a metal bucket", "clang", "silver and round", "metal",
                   {"bucket", "metal"}),
    "signal_light": Clue("signal_light", "a blinking signal light", "beep-beep", "blinking red", "light",
                         {"light", "signal"}),
}

MISUNDERSTANDINGS = {
    "ghost": Misunderstanding(
        "ghost",
        "a ghost was hiding behind the tarp",
        "it was only the tarp snapping in the wind and a worker moving a bucket",
        3,
        {"ghost", "spooky", "misunderstanding"},
    ),
    "haunted_crane": Misunderstanding(
        "haunted_crane",
        "the crane was haunted",
        "it was only the crane cable and a blinking signal light",
        2,
        {"ghost", "crane", "misunderstanding"},
    ),
}

GENTLE_HELPERS = ["mother", "father"]
KID_NAMES = ["Mia", "Noah", "Luna", "Eli", "Ava", "Theo", "Zoe", "Finn"]
WORKER_NAMES = ["Marta", "Owen", "Riley", "Hana"]


@dataclass
class StoryParams:
    setting: str
    clue: str
    misunderstanding: str
    kid: str
    kid_gender: str
    helper: str
    helper_gender: str
    worker: str
    seed: Optional[int] = None


def reasonableness_gate(clue: Clue, misunderstanding: Misunderstanding) -> bool:
    return bool(clue.tags & misunderstanding.tags)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid, clue in CLUES.items():
            for mid, mis in MISUNDERSTANDINGS.items():
                if reasonableness_gate(clue, mis):
                    combos.append((sid, cid, mid))
    return combos


def explain_rejection(clue: Clue, misunderstanding: Misunderstanding) -> str:
    return (
        f"(No story: {clue.label} does not really support the misunderstanding "
        f"'{misunderstanding.fear}'. Pick a clue that fits the spooky idea better.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost-story style construction-site misunderstanding world."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--kid")
    ap.add_argument("--kid-gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=GENTLE_HELPERS)
    ap.add_argument("--helper-gender", choices=["mother", "father"])
    ap.add_argument("--worker")
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(KID_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.misunderstanding is None or c[2] == args.misunderstanding)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, misunderstanding = rng.choice(sorted(combos))
    if args.clue and args.misunderstanding:
        if not reasonableness_gate(CLUES[args.clue], MISUNDERSTANDINGS[args.misunderstanding]):
            raise StoryError(explain_rejection(CLUES[args.clue], MISUNDERSTANDINGS[args.misunderstanding]))
    kid_gender = args.kid_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    kid = args.kid or _pick_name(rng, kid_gender)
    helper = args.helper or helper_gender
    worker = args.worker or rng.choice(WORKER_NAMES)
    return StoryParams(setting, clue, misunderstanding, kid, kid_gender, helper, helper_gender, worker)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,M) :- setting(S), clue(C), misunderstanding(M), fits(C,M).
fits(C,M) :- clue(C), misunderstanding(M).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        assert sample.story.strip()
        print("OK: smoke test generated a story.")
    except Exception as e:
        rc = 1
        print("SMOKE TEST FAILED:", e)
    return rc


def _narrate_setup(world: World, kid: Entity, helper: Entity, worker: Entity, clue: Clue, mis: Misunderstanding) -> None:
    kid.memes["curiosity"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"At {world.setting.place}, the air was {world.setting.mood}. "
        f"{world.setting.details}."
    )
    world.say(
        f"{kid.id} stood beside {helper.pronoun('possessive')} {helper.label_word} "
        f"and watched {worker.id} move around the site."
    )
    world.say(
        f"Then {world.setting.details.split(',')[0]} and the {clue.label} made a strange sound: "
        f"'{clue.sound}' in the dark."
    )
    world.say(
        f"{kid.id} whispered, \"Is that a {mis.fear}?\""
    )


def _narrate_misunderstanding(world: World, kid: Entity, helper: Entity, clue: Clue, mis: Misunderstanding) -> None:
    kid.memes["fear"] += 1
    kid.memes["worry"] += 1
    world.say(
        f"{kid.id}'s eyes got wide. The {clue.label} looked {clue.glow}, and for a second "
        f"{kid.id} was sure the site was haunted."
    )
    world.say(
        f"\"I heard a ghost,\" {kid.id} said, clutching {helper.pronoun('possessive')} hand."
    )


def _narrate_fix(world: World, kid: Entity, helper: Entity, worker: Entity, clue: Clue, mis: Misunderstanding) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"{helper.id} knelt down and smiled. \"No ghost,\" {helper.pronoun()} said. "
        f"\"Look carefully.\""
    )
    world.say(
        f"{worker.id} lifted the {clue.label}, and the sound came back: '{clue.sound}'. "
        f"It was only {mis.explanation}."
    )
    kid.memes["fear"] = 0.0
    kid.memes["relief"] += 1
    world.say(
        f"{kid.id} laughed with relief, because the spooky feeling had a simple reason after all."
    )


def _narrate_ending(world: World, kid: Entity, helper: Entity, clue: Clue) -> None:
    world.say(
        f"By the end, the lamp light made the {clue.label} shine like a little silver star, "
        f"and the construction site sounded ordinary again."
    )
    world.say(
        f"{kid.id} walked home holding {helper.pronoun('possessive')} hand, "
        f"thinking that some ghosts are only shadows, tarps, and busy workers."
    )
    world.say(
        f"Behind them, the {clue.label} kept blinking or fluttering in the wind, "
        f"but now it just looked like part of the work."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    kid = world.add(Entity(id=params.kid, kind="character", type=params.kid_gender, role="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    worker = world.add(Entity(id=params.worker, kind="character", type="adult", role="worker"))
    clue = CLUES[params.clue]
    mis = MISUNDERSTANDINGS[params.misunderstanding]

    _narrate_setup(world, kid, helper, worker, clue, mis)
    world.para()
    _narrate_misunderstanding(world, kid, helper, clue, mis)
    world.para()
    _narrate_fix(world, kid, helper, worker, clue, mis)
    world.para()
    _narrate_ending(world, kid, helper, clue)

    world.facts.update(
        kid=kid, helper=helper, worker=worker, clue=clue, misunderstanding=mis,
        setting=world.setting, outcome="resolved",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost-story style tale for a 3-to-5-year-old set at {f["setting"].place} '
        f'and include the word "trillion".',
        f"Tell a construction-site misunderstanding story where {f['kid'].id} thinks a ghost is there, "
        f"but {f['helper'].id} explains the real cause.",
        f'Write a spooky-but-gentle story about a "trillion"-sounding noise at a construction site '
        f"that turns out to have an ordinary explanation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid = f["kid"]
    helper = f["helper"]
    clue = f["clue"]
    mis = f["misunderstanding"]
    return [
        QAItem(
            question=f"What did {kid.id} think at first?",
            answer=f"At first, {kid.id} thought a ghost was hiding near the construction site. The strange sound and the dark tarp made the idea feel real for a moment.",
        ),
        QAItem(
            question="What was the real explanation?",
            answer=f"The real explanation was ordinary: {mis.explanation}. The scary part turned out to be a normal part of work, not a ghost.",
        ),
        QAItem(
            question=f"How did {helper.id} help?",
            answer=f"{helper.id} stayed calm, knelt down, and pointed out the real cause. That gentle help turned the frightening guess into a simple answer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a construction site?",
            answer="A construction site is a place where people build or fix things. There are often tools, beams, lights, and loud work noises there.",
        ),
        QAItem(
            question="Why can a tarp look spooky at night?",
            answer="A tarp can flap and make shadows in the dark. When it moves in the wind, it can seem like something is hiding under it.",
        ),
        QAItem(
            question="Why do workers use signal lights?",
            answer="Workers use signal lights so people can see danger or movement clearly. Bright blinking lights help everyone stay safe.",
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("construction_site", "tarp", "ghost", "Mia", "girl", "mother", "mother", "Owen"),
    StoryParams("construction_site", "bucket", "ghost", "Noah", "boy", "father", "father", "Marta"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.misunderstanding is None or c[2] == args.misunderstanding)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, misunderstanding = rng.choice(sorted(combos))
    kid_gender = args.kid_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    kid = args.kid or _pick_name(rng, kid_gender)
    helper = args.helper or helper_gender
    worker = args.worker or rng.choice(WORKER_NAMES)
    return StoryParams(setting, clue, misunderstanding, kid, kid_gender, helper, helper_gender, worker)


def build_sample_from_default() -> StorySample:
    params = CURATED[0]
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, c, m in combos:
            print(f"  {s:18} {c:12} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.kid}: {p.clue} / {p.misunderstanding}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
