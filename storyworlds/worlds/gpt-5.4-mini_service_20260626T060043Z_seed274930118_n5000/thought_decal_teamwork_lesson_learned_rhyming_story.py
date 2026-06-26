#!/usr/bin/env python3
"""
A tiny Storyweavers world for a rhyming tale about a thought, a decal, teamwork,
and a lesson learned.

The seed premise:
- A child gets a decal and has a big thought about where to put it.
- The first choice goes wrong or feels wrong.
- Teamwork with a helper turns the mistake into a nicer plan.
- The ending lands on a lesson learned, in a child-facing rhyming style.
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
# Registries
# ---------------------------------------------------------------------------

HERO_NAMES = ["Milo", "Nina", "Luca", "Tia", "Remy", "Sage", "Pip", "Zuri"]
HELPER_NAMES = ["mom", "dad", "Aunt June", "Grandpa", "big sister", "big brother"]
TRAITS = ["bright", "brave", "cheery", "curious", "spry", "gentle"]

PLACES = {
    "playroom": {
        "label": "the playroom",
        "detail": "The room was warm, and the table was set for fun.",
    },
    "bedroom": {
        "label": "the bedroom",
        "detail": "The room was neat, with a box of crafts by the bed.",
    },
    "kitchen": {
        "label": "the kitchen",
        "detail": "The kitchen was bright, and the counter had plenty of space.",
    },
    "porch": {
        "label": "the porch",
        "detail": "The porch had fresh air and a sunny little breeze.",
    },
}

DECALS = {
    "star": {
        "label": "star decal",
        "phrase": "a shiny star decal",
        "color": "gold",
        "shine": "sparkled like a wink in the sky",
        "surface_ok": {"box", "notebook", "poster"},
    },
    "rocket": {
        "label": "rocket decal",
        "phrase": "a bright rocket decal",
        "color": "red",
        "shine": "looked ready to zoom and fly",
        "surface_ok": {"box", "notebook", "poster"},
    },
    "heart": {
        "label": "heart decal",
        "phrase": "a sweet heart decal",
        "color": "pink",
        "shine": "glowed like a tiny warm song",
        "surface_ok": {"box", "notebook", "poster"},
    },
    "smile": {
        "label": "smile decal",
        "phrase": "a cheerful smile decal",
        "color": "blue",
        "shine": "beamed like a friendly moon",
        "surface_ok": {"box", "notebook", "poster"},
    },
}

SURFACES = {
    "book": {
        "label": "book cover",
        "phrase": "the cover of a library book",
        "type": "book",
        "ruin": "would make the book look messy",
        "cleanable": False,
        "owned_by": "library",
    },
    "window": {
        "label": "window glass",
        "phrase": "the window glass",
        "type": "window",
        "ruin": "would leave a sticky spot on the glass",
        "cleanable": True,
        "owned_by": "home",
    },
    "toy": {
        "label": "toy box",
        "phrase": "the lid of a toy box",
        "type": "box",
        "ruin": "would make the toy box look plain and dull",
        "cleanable": True,
        "owned_by": "home",
    },
    "notebook": {
        "label": "notebook cover",
        "phrase": "the front of a notebook",
        "type": "notebook",
        "ruin": "would make the notebook look crooked",
        "cleanable": True,
        "owned_by": "school",
    },
}

# The decal can stick well only on some surfaces.
# The first thought may target the wrong surface, but teamwork can move it.
SAFE_SURFACES = {"box", "notebook", "poster"}

HELP_PLAN = {
    "book": "help peel it off gently and place it on a craft box instead",
    "window": "help wipe away the sticky mark and move it to a poster",
    "toy": "help smooth it onto the toy box lid instead",
    "notebook": "help press it onto the notebook cover just right",
}

# ---------------------------------------------------------------------------
# Shared-world entities
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
    surface: str = ""
    stickers: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "sister", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "brother", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
        return self.label or self.id


@dataclass
class SceneWorld:
    place: str
    detail: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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

    def copy(self) -> "SceneWorld":
        import copy
        return SceneWorld(
            place=self.place,
            detail=self.detail,
            entities=copy.deepcopy(self.entities),
            paragraphs=[[]],
            facts=dict(self.facts),
            fired=set(self.fired),
        )


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    decal: str
    surface: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------

def decal_surface_fit(decal: str, surface: str) -> bool:
    return surface in SAFE_SURFACES and decal in DECALS


def helper_can_fix(surface: str) -> bool:
    return surface in HELP_PLAN


# ---------------------------------------------------------------------------
# Prose helpers
# ---------------------------------------------------------------------------

def rhyme_pair(a: str, b: str) -> str:
    return f"{a}, {b}"


def intro_line(hero: Entity, decal: dict, place: dict, helper: Entity) -> str:
    return (
        f"{hero.ref()} was a {hero.memes.get('trait_word', 'bright')} little {hero.type} "
        f"with a thought that danced and spun; "
        f"{decal['shine']}, and {place['detail'].lower()} {helper.ref()} said, "
        f'"Let us make this fun."'
    )


def outcome_line(hero: Entity, decal: dict, target: Entity, helper: Entity) -> str:
    return (
        f"Together they laughed and worked as one, with teamwork neat and true; "
        f"the decal shone on the right surface at last, and the lesson learned was new."
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def predict_error(surface: str) -> bool:
    return surface == "book"


def run_story(params: StoryParams) -> SceneWorld:
    place = PLACES[params.place]
    world = SceneWorld(place=place["label"], detail=place["detail"])

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        label=params.name,
        meters={"mood": 1.0},
        memes={"curiosity": 1.0, "lesson": 0.0, "teamwork": 0.0, "thought": 1.0, "trait_word": params.trait},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="helper",
        label=params.helper,
        meters={"mood": 1.0},
        memes={"teamwork": 1.0},
    ))
    decal = world.add(Entity(
        id="decal",
        kind="thing",
        type="decal",
        label=DECALS[params.decal]["label"],
        phrase=DECALS[params.decal]["phrase"],
    ))
    target = world.add(Entity(
        id="target",
        kind="thing",
        type=SURFACES[params.surface]["type"],
        label=SURFACES[params.surface]["label"],
        phrase=SURFACES[params.surface]["phrase"],
        surface=params.surface,
        meters={"sticky_mark": 0.0},
        memes={"ruin": 0.0},
    ))

    world.facts.update(hero=hero, helper=helper, decal=decal, target=target, params=params)

    # Act 1: setup
    world.say(
        f"One bright little day in {world.place}, {hero.ref()} had a thought so spry, "
        f"to place {decal.phrase} where it could shine on high."
    )
    world.say(
        f"{decal['shine'].capitalize()}." if False else f"{DECALS[params.decal]['shine'].capitalize()}."
    )
    world.say(
        f"{hero.ref()} looked at {target.phrase} and gave a tiny grin; "
        f"the plan seemed fun, but it might go wrong if the fit was thin."
    )

    # Act 2: conflict
    world.para()
    if predict_error(params.surface):
        target.meters["sticky_mark"] += 1.0
        target.memes["ruin"] += 1.0
        hero.memes["worry"] = 1.0
        world.say(
            f"At first {hero.ref()} stuck it on the {target.label}, and oh, what a flop; "
            f"the decal would not sit well there, so the sticky edge had to stop."
        )
        world.say(
            f"{helper.ref()} came close and said, with a nod and a smile so wide, "
            f'"A wobble can teach us something; let us fix it side by side."'
        )
    else:
        world.say(
            f"{hero.ref()} reached for the {target.label}, and nearly chose too soon; "
            f"then {helper.ref()} paused the hand and saved the day like a tune."
        )
        world.say(
            f'"This surface is not the best one," {helper.ref()} said, in a calm little rhyme; '
            f'"A better spot will help it glow and save us time."'
        )

    # Act 3: teamwork and lesson learned
    world.para()
    world.facts["teamwork"] = 1
    world.facts["lesson_learned"] = 1
    hero.memes["teamwork"] += 1.0
    hero.memes["lesson"] += 1.0

    if params.surface == "book":
        world.say(
            f"With teamwork, they lifted it free, as gentle as a breeze; "
            f"they placed it on a craft box lid, where it could shine with ease."
        )
        world.say(
            f"The sticky little mark was wiped away, and no more trouble stayed; "
            f"{hero.ref()} learned to think ahead, and smiled at what they'd made."
        )
    else:
        plan = HELP_PLAN[params.surface]
        world.say(
            f"With teamwork, they did not rush; they chose a better spot; "
            f"they {plan}, and that made the decal pop."
        )
        world.say(
            f"Then the decal sat just right, like a star upon a shoe; "
            f"{hero.ref()} learned that asking for help can make a good plan true."
        )

    world.para()
    world.say(outcome_line(hero, DECALS[params.decal], target, helper))
    return world


# ---------------------------------------------------------------------------
# Generation and QA
# ---------------------------------------------------------------------------

def generation_prompts(world: SceneWorld) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short rhyming story for a child about {p.name} and a {p.decal} decal.',
        f"Tell a gentle teamwork tale where {p.name} has a thought about a decal, "
        f"makes a small mistake, and learns a lesson with {p.helper}.",
        f'Write a simple story with the words "thought" and "decal" that ends in a lesson learned.',
    ]


def story_qa(world: SceneWorld) -> list[QAItem]:
    p = world.facts["params"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    target: Entity = world.facts["target"]

    return [
        QAItem(
            question=f"What did {hero.ref()} think about at the start of the story?",
            answer=f"{hero.ref()} had a thought about where to put the {p.decal} decal.",
        ),
        QAItem(
            question=f"Who helped {hero.ref()} fix the decal choice?",
            answer=f"{helper.ref()} helped {hero.ref()} with teamwork and a kinder plan.",
        ),
        QAItem(
            question=f"What lesson did {hero.ref()} learn at the end?",
            answer=f"{hero.ref()} learned to ask for help and choose the right spot before sticking the decal down.",
        ),
        QAItem(
            question=f"Why was the first choice wrong?",
            answer=f"The first choice was wrong because the {target.label} was not the best place for the decal.",
        ),
    ]


def world_knowledge_qa(world: SceneWorld) -> list[QAItem]:
    p = world.facts["params"]
    decal = DECALS[p.decal]
    return [
        QAItem(
            question="What is a decal?",
            answer="A decal is a picture or design that can stick to a surface.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a task together.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="Learning a lesson means understanding something important that helps you do better next time.",
        ),
        QAItem(
            question=f"What kind of feeling does a {decal['label']} give?",
            answer=f"A {decal['label']} can make a surface look bright and cheerful.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- hero_name(H).
decal(D) :- decal_name(D).
surface(S) :- surface_name(S).

good_fit(D,S) :- decal(D), surface(S), safe_surface(S).
bad_fit(D,S) :- decal(D), surface(S), not safe_surface(S).

lesson_learned(P) :- player(P), teamwork(P), thought(P), decal_choice(P), bad_choice(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in HERO_NAMES:
        lines.append(asp.fact("hero_name", name))
        lines.append(asp.fact("player", name))
    for k in DECALS:
        lines.append(asp.fact("decal_name", k))
    for k in SURFACES:
        lines.append(asp.fact("surface_name", k))
        if k in SAFE_SURFACES:
            lines.append(asp.fact("safe_surface", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    # lightweight parity check: safe surfaces in Python must match ASP facts
    model = asp.one_model(asp_program("#show safe_surface/1."))
    asp_safe = set(asp.atoms(model, "safe_surface"))
    py_safe = {(s,) for s in sorted(SAFE_SURFACES)}
    if asp_safe != py_safe:
        print("MISMATCH between ASP and Python safe surfaces")
        print("only in asp:", sorted(asp_safe - py_safe))
        print("only in python:", sorted(py_safe - asp_safe))
        return 1
    print(f"OK: ASP parity holds for safe surfaces ({len(py_safe)}).")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming storyworld about thought, decal, teamwork, and lesson learned.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--decal", choices=sorted(DECALS))
    ap.add_argument("--surface", choices=sorted(SURFACES))
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for decal in DECALS:
            for surface in SURFACES:
                if decal_surface_fit(decal, surface) and helper_can_fix(surface):
                    combos.append((place, decal, surface))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.decal and args.surface and not decal_surface_fit(args.decal, args.surface):
        raise StoryError("That decal and surface do not make a reasonable story.")
    if args.surface and not helper_can_fix(args.surface):
        raise StoryError("There is no teamwork fix for that surface in this world.")

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.decal is None or c[1] == args.decal)
        and (args.surface is None or c[2] == args.surface)
    ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")

    place, decal, surface = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, decal=decal, surface=surface, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = run_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: SceneWorld) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.surface:
            bits.append(f"surface={e.surface}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="playroom", decal="star", surface="toy", name="Milo", helper="mom", trait="bright"),
    StoryParams(place="bedroom", decal="heart", surface="book", name="Tia", helper="dad", trait="curious"),
    StoryParams(place="kitchen", decal="rocket", surface="window", name="Luca", helper="Aunt June", trait="cheery"),
]


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
        print(asp_program("#show safe_surface/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show safe_surface/1."))
        safe = sorted(set(asp.atoms(model, "safe_surface")))
        print(f"{len(safe)} safe surfaces:")
        for s in safe:
            print(f"  {s[0]}")
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
            header = f"### {p.name}: {p.decal} on {p.surface} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
