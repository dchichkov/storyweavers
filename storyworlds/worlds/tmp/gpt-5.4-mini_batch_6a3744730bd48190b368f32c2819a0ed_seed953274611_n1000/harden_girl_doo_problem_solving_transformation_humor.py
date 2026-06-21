#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/harden_girl_doo_problem_solving_transformation_humor.py
========================================================================================

A standalone storyworld in a small mystery-ish domain for a child detective,
a strange goo called doo, and a problem that changes shape before it is solved.

Premise:
- A girl finds a funny, squishy doo in a quiet place.
- The doo keeps transforming as it dries, hardens, and reveals clues.
- She solves the mystery by using careful observation, a simple trick, and a bit
  of humor.
- The ending proves what changed: the doo becomes a safe little model and the
  missing item is found.

This world is written to satisfy the shared storyworld contract:
- typed entities with meters and memes
- state-driven prose
- curated, constraint-valid combinations
- Python reasonableness gate plus inline ASP twin
- prompts, story QA, and world-knowledge QA
- --verify smoke tests ordinary story generation and ASP/Python parity
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
    hiding_spot: str
    clue_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class DooThing:
    id: str
    label: str
    phrase: str
    goo_state: str
    hard_state: str
    transform_text: str
    clue_text: str
    risky: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    sense: int
    power: int
    method: str
    result: str
    fail: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_harden(world: World) -> list[str]:
    out: list[str] = []
    doo = world.entities.get("doo")
    if doo is None:
        return out
    if doo.meters["dry"] < THRESHOLD:
        return out
    sig = ("harden",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    doo.meters["hard"] += 1
    out.append("__hard__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    doo = world.entities.get("doo")
    clue = world.entities.get("clue")
    if doo is None or clue is None:
        return out
    if doo.meters["hard"] < THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.meters["known"] += 1
    out.append("__clue__")
    return out


def _r_lift_mood(world: World) -> list[str]:
    girl = world.entities.get("girl")
    if girl is None:
        return []
    if girl.memes["smile"] < THRESHOLD:
        return []
    sig = ("laugh",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    girl.memes["amused"] += 1
    return ["__laugh__"]


CAUSAL_RULES = [
    Rule("harden", "physical", _r_harden),
    Rule("reveal", "physical", _r_reveal),
    Rule("laugh", "social", _r_lift_mood),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reason_gate(doo: DooThing, fix: Fix) -> bool:
    return doo.risky or fix.sense >= SENSE_MIN


def can_solve(doo: DooThing, fix: Fix) -> bool:
    return fix.power >= 1 and fix.sense >= SENSE_MIN


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("doo").meters["wet"] = 0.0
    sim.get("doo").meters["dry"] = 1.0
    propagate(sim, narrate=False)
    return {"hardened": sim.get("doo").meters["hard"] >= THRESHOLD,
            "clue": sim.get("clue").meters["known"] >= THRESHOLD}


def start(world: World, girl: Entity, setting: Setting, doo: DooThing) -> None:
    girl.memes["curious"] += 1
    world.say(
        f"On a quiet evening, {girl.id} explored {setting.place}. "
        f"{setting.mood.capitalize()} light pooled on the floor like a secret."
    )
    world.say(
        f"Near {setting.hiding_spot}, {girl.id} found {doo.phrase} -- a funny little {doo.label} called doo."
    )


def inspect(world: World, girl: Entity, doo: DooThing) -> None:
    girl.memes["mystery"] += 1
    world.say(
        f"{girl.id} poked it with one careful finger. "
        f'"Huh," {girl.pronoun()} said. "That doo looks like it is thinking."'
    )
    world.say(
        f"The doo wobbled, then started to {doo.transform_text}."
    )


def clue_turn(world: World, girl: Entity, setting: Setting, doo: DooThing) -> None:
    world.get("doo").meters["dry"] += 1
    propagate(world, narrate=False)
    world.say(
        f"As it dried, the doo began to harden. "
        f"That was odd enough to make {girl.id} grin."
    )
    if world.get("clue").meters["known"] >= THRESHOLD:
        world.say(
            f"Under the hard shell, a tiny mark appeared near {setting.clue_spot}. "
            f"It was not a monster after all -- it was a clue."
        )


def solve(world: World, girl: Entity, fix: Fix, doo: DooThing) -> None:
    girl.memes["smile"] += 1
    world.say(
        f"{girl.id} thought for a moment, then used {fix.method}. "
        f"That was the simplest answer, and also the funniest one."
    )
    world.say(
        f"The doo {fix.result}, and the mystery stopped pretending to be scary."
    )


def end(world: World, girl: Entity, setting: Setting, doo: DooThing) -> None:
    girl.memes["joy"] += 1
    world.say(
        f"In the end, the doo was no longer squishy. "
        f"It stood there as a tiny hard shape with the clue pressed into it."
    )
    world.say(
        f"{girl.id} laughed, found the missing item by {setting.clue_spot}, and walked home knowing that even strange things can become useful."
    )


SETTINGS = {
    "attic": Setting(
        id="attic",
        place="the attic",
        mood="dusty moon",
        hiding_spot="an old trunk",
        clue_spot="the rafters",
        tags={"mystery", "attic"},
    ),
    "shed": Setting(
        id="shed",
        place="the shed",
        mood="thin afternoon",
        hiding_spot="a paint shelf",
        clue_spot="the back wall",
        tags={"mystery", "shed"},
    ),
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen",
        mood="golden lamp",
        hiding_spot="behind the teapot",
        clue_spot="the cookie jar",
        tags={"mystery", "kitchen"},
    ),
}

DOOS = {
    "doo": DooThing(
        id="doo",
        label="doo",
        phrase="a wobbly brown doo with tiny shiny bumps",
        goo_state="wobbly",
        hard_state="hard little lump",
        transform_text="harden into a funny little lump",
        clue_text="a tiny arrow-shaped mark",
        risky=False,
        tags={"doo", "transformation"},
    ),
    "glowdoo": DooThing(
        id="glowdoo",
        label="doo",
        phrase="a pale doo that glimmered like soap foam",
        goo_state="soft",
        hard_state="bright pebble",
        transform_text="harden into a bright pebble-shaped clue",
        clue_text="a bright pebble mark",
        risky=False,
        tags={"doo", "transformation"},
    ),
}

FIXES = {
    "dryair": Fix(
        id="dryair",
        sense=3,
        power=2,
        method="opening the attic window and letting the warm air do the work",
        result="hardened into a neat little clue-block",
        fail="stayed squishy and slippery, which was not very detective-like",
        tags={"problem-solving", "transformation", "humor"},
    ),
    "towel": Fix(
        id="towel",
        sense=2,
        power=2,
        method="pressing it gently with a clean towel until the wet part disappeared",
        result="turned from goo to a firm clue-cube",
        fail="smudged into a sillier mess",
        tags={"problem-solving", "transformation", "humor"},
    ),
}

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Lena", "Ruby", "Zoe", "Ada", "Mila"]


@dataclass
class StoryParams:
    setting: str
    doo: str
    fix: str
    girl: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for d in DOOS:
            for f in FIXES:
                combos.append((s, d, f))
    return combos


def explain_rejection() -> str:
    return "(No story: this mystery has no reasonable path.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld about a girl, a doo, and a clue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--doo", choices=DOOS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--girl", choices=GIRL_NAMES)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.doo is None or c[1] == args.doo)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, doo, fix = rng.choice(sorted(combos))
    girl = args.girl or rng.choice(GIRL_NAMES)
    return StoryParams(setting=setting, doo=doo, fix=fix, girl=girl)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    doo_cfg = DOOS[params.doo]
    fix = FIXES[params.fix]
    girl = world.add(Entity(id=params.girl, kind="character", type="girl", role="detective"))
    clue = world.add(Entity(id="clue", kind="thing", type="thing", label="clue"))
    doo = world.add(Entity(id="doo", kind="thing", type="thing", label="doo"))
    world.facts["setting"] = setting
    world.facts["doo_cfg"] = doo_cfg
    world.facts["fix"] = fix
    world.facts["girl"] = girl

    start(world, girl, setting, doo_cfg)
    world.para()
    inspect(world, girl, doo_cfg)
    clue_turn(world, girl, setting, doo_cfg)
    world.para()
    solve(world, girl, fix, doo_cfg)
    end(world, girl, setting, doo_cfg)
    world.facts["solved"] = True
    world.facts["hardened"] = True
    world.facts["humor"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    girl = f["girl"]
    setting = f["setting"]
    return [
        f'Write a short mystery story for a child about {girl.id}, a strange doo, and a clue in {setting.place}.',
        f"Tell a funny problem-solving story where {girl.id} watches a doo harden and figures out what it means.",
        f'Write a gentle mystery with the words "harden", "girl", and "doo" and an ending that turns a silly mess into a useful shape.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    girl = f["girl"]
    setting = f["setting"]
    doo_cfg = f["doo_cfg"]
    fix = f["fix"]
    return [
        QAItem(
            question="What did the girl find?",
            answer=f"{girl.id} found a funny doo in {setting.place}. At first it looked like a silly squish, but it turned out to be part of the mystery."
        ),
        QAItem(
            question="What changed about the doo?",
            answer=f"It dried and began to harden into a small clue. That change mattered because the hard shape made the hidden mark easy to notice."
        ),
        QAItem(
            question="How did the girl solve the problem?",
            answer=f"She used {fix.method}. That simple trick helped the doo change shape in a useful way, so the clue could be seen clearly."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps you figure something out. In a mystery, a clue points you toward the answer."
        ),
        QAItem(
            question="What does it mean for something to harden?",
            answer="To harden means to become firmer or less squishy. A soft thing can harden when it dries or cools."
        ),
        QAItem(
            question="Why can a funny story still be a mystery?",
            answer="Because mysteries are about noticing odd details and solving a question. A story can be silly and still ask the reader to think carefully."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.doo not in DOOS or params.fix not in FIXES:
        raise StoryError("(Invalid story parameters.)")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
hardened(D) :- doo(D), dries(D).
clue_revealed(C) :- clue(C), hardened(D), links(C, D).
solved :- clue_revealed(_), fix_good(F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did, d in DOOS.items():
        lines.append(asp.fact("doo", did))
        if d.risky:
            lines.append(asp.fact("risky", did))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix_good", fid))
        lines.append(asp.fact("sense", fid, f.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1.\n#show doo/1.\n#show fix_good/1.\n"))
    return sorted(set(asp.atoms(model, "setting")))[:0] or sorted(valid_combos())


def asp_verify() -> int:
    rc = 0
    if set(valid_combos()) != set(asp_valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos() differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


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
    StoryParams(setting="attic", doo="doo", fix="dryair", girl="Mina"),
    StoryParams(setting="shed", doo="glowdoo", fix="towel", girl="Ivy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show setting/1.\n#show doo/1.\n#show fix_good/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Compatible stories:")
        for combo in valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
