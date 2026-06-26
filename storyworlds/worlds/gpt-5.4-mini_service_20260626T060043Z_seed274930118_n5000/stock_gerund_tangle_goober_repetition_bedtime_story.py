#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/stock_gerund_tangle_goober_repetition_bedtime_story.py
=============================================================================================================

A small bedtime-story world about a sleepy child, a favorite goober toy,
and a tangle that gets in the way of settling down.

Seeded premise:
- A child loves a repeated soothing routine.
- A soft thing gets tangled at bedtime.
- A parent helps untangle the problem with a gentle, plausible fix.

The world is intentionally small and classical: a few entities, a few meters
and memes, one tension turn, one resolution image.
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

# Physical/emotional thresholds for narrated changes.
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
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bedroom"
    affords: set[str] = field(default_factory=set)


@dataclass
class Routine:
    id: str
    gerund: str
    refrain: str
    cozy: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tangle:
    label: str
    phrase: str
    region: str
    causes: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
SETTINGS = {
    "bedroom": Setting(place="the bedroom", affords={"tuck", "story", "song"}),
    "nursery": Setting(place="the nursery", affords={"tuck", "story", "song"}),
    "cabin": Setting(place="the little cabin room", affords={"tuck", "story", "song"}),
}

ROUTINES = {
    "tucking": Routine(
        id="tucking",
        gerund="tucking in",
        refrain="the blanket, the pillow, the pillow, the blanket",
        cozy="soft and warm",
        keyword="blanket",
        tags={"bedtime", "repetition"},
    ),
    "story": Routine(
        id="story",
        gerund="reading the same story again",
        refrain="one page, one smile, one sleepy blink, one page",
        cozy="quiet and cozy",
        keyword="story",
        tags={"bedtime", "repetition"},
    ),
    "song": Routine(
        id="song",
        gerund="singing the same lullaby again",
        refrain="hush now, hush now, softly and slowly",
        cozy="gentle and sleepy",
        keyword="lullaby",
        tags={"bedtime", "repetition"},
    ),
}

TANGLES = {
    "sheet": Tangle(
        label="sheet tangle",
        phrase="a twist in the sheet",
        region="legs",
        causes={"tuck"},
    ),
    "ribbon": Tangle(
        label="ribbon tangle",
        phrase="a knot in the ribbon",
        region="arms",
        causes={"story", "song"},
    ),
    "hair": Tangle(
        label="hair tangle",
        phrase="a snarl in the hair",
        region="head",
        causes={"song", "story"},
    ),
}

HELPERS = {
    "straighten": Helper(
        id="straighten",
        label="smooth hands",
        prep="lift the corner and smooth it flat",
        tail="smoothed the bedding flat again",
        helps={"sheet"},
    ),
    "comb": Helper(
        id="comb",
        label="a soft brush",
        prep="find the brush and gently comb the snarl away",
        tail="brushed the little snarl out",
        helps={"hair"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "June", "Ella", "Rose"]
BOY_NAMES = ["Theo", "Ben", "Leo", "Sam", "Finn", "Max"]
TRAITS = ["sleepy", "gentle", "curious", "cuddly", "patient"]


@dataclass
class StoryParams:
    setting: str
    routine: str
    tangle: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def routine_at_risk(routine: Routine, tangle: Tangle) -> bool:
    return tangle.label.split()[0] in routine.keyword or tangle.region in {"legs", "arms", "head"}


def select_helper(routine: Routine, tangle: Tangle) -> Optional[Helper]:
    for helper in HELPERS.values():
        if tangle.label.split()[0] in helper.helps:
            return helper
    return None


def explain_rejection(routine: Routine, tangle: Tangle) -> str:
    return (
        f"(No story: the {routine.gerund} does not make a believable tangle with "
        f"{tangle.phrase} in this tiny bedtime world.)"
    )


def explain_gender(gender: str, tangle: Tangle) -> str:
    return (
        f"(No story: this version doesn't require a special gender, but the current "
        f"tangle '{tangle.label}' does not care about that choice.)"
    )


def setup_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    routine = ROUTINES[params.routine]
    tangle = TANGLES[params.tangle]

    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"sleep": 0.0},
        memes={"cozy": 0.0, "worry": 0.0, "repetition": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label="the parent",
        meters={"sleep": 0.0},
        memes={"care": 0.0},
    ))
    blanket = world.add(Entity(
        id="Blanket",
        type="blanket",
        label="blanket",
        phrase="a soft blanket",
        owner=hero.id,
        caretaker=parent.id,
        meters={"tangle": 0.0, "smooth": 0.0},
    ))
    toy = world.add(Entity(
        id="Goober",
        type="goober",
        label="goober",
        phrase="a silly little goober",
        owner=hero.id,
        caretaker=hero.id,
        meters={"loved": 0.0},
        memes={"comfort": 0.0},
    ))

    world.facts.update(hero=hero, parent=parent, blanket=blanket, toy=toy, routine=routine, tangle=tangle)
    return world


def do_routine(world: World, hero: Entity, routine: Routine, tangle: Tangle) -> None:
    hero.memes["repetition"] += 1
    hero.memes["cozy"] += 1
    world.say(
        f"{hero.id} liked bedtime best when it went the same way each night: "
        f"{routine.refrain}."
    )
    world.say(
        f"That made the room feel {routine.cozy}, and {hero.id} held {hero.pronoun('possessive')} "
        f"goober close while getting ready for sleep."
    )
    world.say(
        f"Again and again, {hero.id} whispered, \"{routine.refrain}.\""
    )
    if tangle.label == "sheet tangle":
        hero.memes["worry"] += 1


def introduce_tangle(world: World, hero: Entity, parent: Entity, tangle: Tangle) -> None:
    hero.memes["worry"] += 1
    parent.memes["care"] += 1
    world.say(
        f"But one soft night, a {tangle.phrase} made the bed feel stuck."
    )
    world.say(
        f"{hero.id} tried to settle down, but the covers tugged and pulled, and the bedtime rhythm wobbled."
    )


def resolve_tangle(world: World, hero: Entity, parent: Entity, tangle: Tangle, routine: Routine) -> Optional[Helper]:
    helper = select_helper(routine, tangle)
    if helper is None:
        return None
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label} smiled and said, "
        f"\"Let's {helper.prep}.\""
    )
    return helper


def finish(world: World, hero: Entity, parent: Entity, helper: Helper, routine: Routine, tangle: Tangle) -> None:
    hero.memes["worry"] = 0.0
    hero.memes["cozy"] += 1
    world.say(
        f"They {helper.tail}, and the bed became still again."
    )
    world.say(
        f"Then {hero.id} went back to {routine.gerund}, with {hero.pronoun('possessive')} goober tucked beside {hero.pronoun('object')}."
    )
    world.say(
        f"At last, the room was quiet, and the little tangle was only a memory."
    )


def tell(setting: Setting, routine: Routine, tangle: Tangle,
         hero_name: str = "Mia", hero_type: str = "girl",
         parent_type: str = "mother", hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"sleep": 0.0},
        memes={"cozy": 0.0, "worry": 0.0, "repetition": 0.0},
        label=hero_name.lower(),
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        meters={"sleep": 0.0},
        memes={"care": 0.0},
    ))
    world.add(Entity(id="Blanket", type="blanket", label="blanket", phrase="a soft blanket", owner=hero.id, caretaker=parent.id))
    world.add(Entity(id="Goober", type="goober", label="goober", phrase="a silly little goober", owner=hero.id, caretaker=hero.id))

    world.say(f"{hero.id} was a {hero_traits[0] if hero_traits else 'sleepy'} little {hero.type} who loved bedtime.")
    do_routine(world, hero, routine, tangle)
    world.para()
    introduce_tangle(world, hero, parent, tangle)
    helper = resolve_tangle(world, hero, parent, tangle, routine)
    if helper:
        world.para()
        finish(world, hero, parent, helper, routine, tangle)

    world.facts.update(hero=hero, parent=parent, routine=routine, tangle=tangle, helper=helper)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
routine_at_risk(R, T) :- routine(R), tangle(T), affects(R, K), causes(T, K).
has_helper(R, T) :- routine_at_risk(R, T), helper(H), helps(H, T).
valid_story(S, R, T) :- setting(S), routine(R), tangle(T), routine_at_risk(R, T), has_helper(R, T).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid, r in ROUTINES.items():
        lines.append(asp.fact("routine", rid))
        for tag in sorted(r.tags):
            lines.append(asp.fact("affects", rid, tag))
    for tid, t in TANGLES.items():
        lines.append(asp.fact("tangle", tid))
        for c in sorted(t.causes):
            lines.append(asp.fact("causes", tid, c))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for need in sorted(h.helps):
            lines.append(asp.fact("helps", hid, need))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for routine in ROUTINES:
            for tangle in TANGLES:
                r = ROUTINES[routine]
                t = TANGLES[tangle]
                if routine_at_risk(r, t) and select_helper(r, t):
                    combos.append((setting, routine, tangle))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, routine, tangle = f["hero"], f["routine"], f["tangle"]
    return [
        f'Write a gentle bedtime story for a young child about "{routine.gerund}" and a "goober".',
        f"Tell a cozy story where {hero.id} repeats {routine.refrain!r} until a tangle needs help.",
        f'Write a short bedtime story that includes the words "goober" and "{tangle.label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, routine, tangle = f["hero"], f["parent"], f["routine"], f["tangle"]
    helper = f.get("helper")
    qa = [
        QAItem(
            question=f"What did {hero.id} keep doing at bedtime?",
            answer=f"{hero.id} kept {routine.gerund}, and the repeated words made the room feel cozy.",
        ),
        QAItem(
            question=f"What problem made the bedtime routine wobble?",
            answer=f"A {tangle.phrase} made settling down tricky, so the bed did not feel smooth at first.",
        ),
        QAItem(
            question=f"Who helped fix the trouble?",
            answer=f"{parent.label.capitalize()} helped by staying calm and using gentle hands.",
        ),
    ]
    if helper:
        qa.append(
            QAItem(
                question=f"How did the helper solve the tangle?",
                answer=f"They used {helper.label} to {helper.prep.lower()}, and that made the bed feel right again.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a goober in a bedtime story?",
            answer="A goober is a silly little toy or plush friend that a child might hug at night.",
        ),
        QAItem(
            question="Why do repeated bedtime routines help children?",
            answer="Repeated bedtime routines help because the same calm steps feel familiar and make it easier to relax.",
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
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="bedroom", routine="tucking", tangle="sheet", name="Mia", gender="girl", parent="mother", trait="sleepy"),
    StoryParams(setting="nursery", routine="story", tangle="ribbon", name="Theo", gender="boy", parent="father", trait="gentle"),
    StoryParams(setting="cabin", routine="song", tangle="hair", name="Lily", gender="girl", parent="mother", trait="cuddly"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny bedtime story world with repetition and a tangle.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--routine", choices=ROUTINES)
    ap.add_argument("--tangle", choices=TANGLES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
              and (args.routine is None or c[1] == args.routine)
              and (args.tangle is None or c[2] == args.tangle)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, routine, tangle = rng.choice(sorted(combos))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError("invalid gender")
    if args.gender and args.gender not in ["girl", "boy"]:
        raise StoryError(explain_gender(args.gender, TANGLES[tangle]))
    name = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, routine=routine, tangle=tangle, name=name, gender=hero_gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ROUTINES[params.routine],
        TANGLES[params.tangle],
        hero_name=params.name,
        hero_type=params.gender,
        parent_type=params.parent,
        hero_traits=[params.trait],
    )
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = valid_combos()
        print(f"{len(combos)} compatible stories:")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
