#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about an attentive guard, a bit of licorice,
and a small mystery that is gently foreshadowed before it is solved.

The domain is intentionally small:
- a child visits a garden gate
- an attentive guard watches for trouble
- a licorice treat goes missing
- soft clues appear earlier in the tale
- the child solves the mystery with careful noticing
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
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    inside: bool = False
    gentle_detail: str = ""


@dataclass
class Mystery:
    id: str
    clue_word: str
    missing_word: str
    culprit_word: str
    trail_word: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "garden_gate": Setting(
        place="the garden gate",
        inside=False,
        gentle_detail="The roses nodded near the gate, and the path was tidy and bright.",
    ),
    "porch": Setting(
        place="the porch",
        inside=False,
        gentle_detail="The porch had a little bench and a basket by the steps.",
    ),
    "kitchen": Setting(
        place="the kitchen",
        inside=True,
        gentle_detail="The kitchen was warm, with a small table and a sunny window.",
    ),
}

MYSTERIES = {
    "missing_licorice": Mystery(
        id="missing_licorice",
        clue_word="licorice",
        missing_word="licorice",
        culprit_word="mouse",
        trail_word="crumbs",
    )
}

GIRL_NAMES = ["Mia", "Nina", "Lily", "Poppy", "Ada", "Mimi"]
BOY_NAMES = ["Finn", "Theo", "Max", "Pip", "Ned", "Ollie"]
TRAITS = ["attentive", "gentle", "cheerful", "curious"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
mystery(missing_licorice).
setting(garden_gate).
setting(porch).
setting(kitchen).

clue(crumbs).
clue(smell).
clue(tiny_prints).

attentive(child).
guard(guard).
licorice(licorice).

solve(M) :- mystery(M), clue(crumbs), clue(smell), attentive(child), guard(guard).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("mystery", "missing_licorice"),
        asp.fact("setting", "garden_gate"),
        asp.fact("setting", "porch"),
        asp.fact("setting", "kitchen"),
        asp.fact("clue", "crumbs"),
        asp.fact("clue", "smell"),
        asp.fact("clue", "tiny_prints"),
        asp.fact("attentive", "child"),
        asp.fact("guard", "guard"),
        asp.fact("licorice", "licorice"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show solve/1."))
    found = set(asp.atoms(model, "solve"))
    expected = {("missing_licorice",)}
    if found == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH: ASP twin disagrees with Python.")
    print("  ASP:", sorted(found))
    print("  PY :", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    return [(place, mystery_id) for place in SETTINGS for mystery_id in MYSTERIES]


def explain_rejection(place: str, mystery: str) -> str:
    return f"(No story: the place '{place}' and mystery '{mystery}' do not make a gentle nursery-rhyme scene.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def _cue_smell(world: World, child: Entity) -> None:
    if "smell" in world.fired:
        return
    world.fired.add("smell")
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1.0
    world.say(
        f"Before the day was done, {child.id} caught a sweet smell of licorice on the air."
    )


def _cue_crumbs(world: World, child: Entity) -> None:
    if "crumbs" in world.fired:
        return
    world.fired.add("crumbs")
    world.say(
        f"Then {child.id} found tiny crumbs by the step, like little black buttons in a row."
    )


def _guard_notice(world: World, guard: Entity, child: Entity) -> None:
    if "guard_notice" in world.fired:
        return
    world.fired.add("guard_notice")
    guard.memes["attentive"] = guard.memes.get("attentive", 0.0) + 1.0
    world.say(
        f"The attentive guard watched the gate and said, \"Keep your eyes on the path, little one.\""
    )


def _mystery_turn(world: World, child: Entity, mystery: Mystery) -> None:
    if "mystery_turn" in world.fired:
        return
    world.fired.add("mystery_turn")
    child.memes["mystery"] = child.memes.get("mystery", 0.0) + 1.0
    world.say(
        f"{child.id} wondered who had taken the licorice, and the question felt as big as a moonbeam."
    )


def _solve_mystery(world: World, child: Entity, guard: Entity, mystery: Mystery, treat: Entity) -> None:
    if "solve" in world.fired:
        return
    world.fired.add("solve")
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
    guard.memes["relief"] = guard.memes.get("relief", 0.0) + 1.0
    treat.carried_by = child.id
    world.say(
        f"At last, {child.id} followed the crumbs to a little mouse hole under the bench, "
        f"where the licorice had been tucked away by a hungry mouse."
    )
    world.say(
        f"The attentive guard smiled, and {child.id} brought the licorice back safe and sound."
    )


def tell(setting: Setting, mystery: Mystery, hero_name: str, hero_gender: str, trait: str) -> World:
    world = World(setting)

    child = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name))
    guard = world.add(Entity(id="Guard", kind="character", type="adult", label="the guard"))
    treat = world.add(Entity(id="Licorice", kind="thing", type="licorice", label="licorice", phrase="a piece of licorice"))
    treat.carried_by = guard.id

    child.memes["curiosity"] = 0.0
    child.memes["joy"] = 0.0
    guard.memes["attentive"] = 1.0

    # Act 1: gentle setup.
    world.say(
        f"At {setting.place}, there lived an attentive guard who watched with a steady eye."
    )
    world.say(
        f"One small {hero_gender} named {hero_name} came strolling by, {trait} and bright."
    )
    world.say(setting.gentle_detail)
    world.say(
        f"Near the bench lay a sweet piece of licorice, and the air felt soft as a lullaby."
    )

    # Act 2: foreshadowing and mystery.
    world.para()
    _guard_notice(world, guard, child)
    _cue_smell(world, child)
    _mystery_turn(world, child, mystery)
    world.say(
        f"Yet when {hero_name} looked again, the licorice was gone from the little plate."
    )
    _cue_crumbs(world, child)

    # Act 3: resolution.
    world.para()
    _solve_mystery(world, child, guard, mystery, treat)

    world.facts.update(
        child=child,
        guard=guard,
        treat=treat,
        setting=setting,
        mystery=mystery,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    return [
        "Write a short nursery-rhyme story about an attentive guard and a mystery with licorice.",
        f"Tell a gentle story where {child.id} notices clues, follows them, and solves a small mystery.",
        "Write a child-friendly rhyme with a foreshadowed clue, a missing treat, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    guard: Entity = f["guard"]
    treat: Entity = f["treat"]
    mystery: Mystery = f["mystery"]
    return [
        QAItem(
            question=f"Who was attentive at the gate?",
            answer=f"The guard was attentive at the gate and watched carefully the whole time.",
        ),
        QAItem(
            question=f"What sweet thing was missing in the story?",
            answer=f"The missing thing was licorice, which had been on the little plate before it disappeared.",
        ),
        QAItem(
            question=f"What clues helped {child.id} solve the mystery?",
            answer=f"{child.id} used the smell of licorice and the tiny crumbs to follow the trail and solve the mystery.",
        ),
        QAItem(
            question=f"Who had taken the licorice?",
            answer=f"A hungry mouse had tucked the licorice away under the bench.",
        ),
        QAItem(
            question=f"How did the story end for {child.id} and the guard?",
            answer=f"{child.id} brought the licorice back safe and sound, and the attentive guard smiled with relief.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is licorice?",
            answer="Licorice is a sweet treat that can be chewy and a little twisty.",
        ),
        QAItem(
            question="What does an attentive guard do?",
            answer="An attentive guard watches carefully and notices small changes or trouble.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that you need clues to understand.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives little hints about what may happen later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A nursery-rhyme storyworld about an attentive guard, licorice, and a small mystery."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy", "child"])
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
    combos = valid_combos()
    combos = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.mystery is None or c[1] == args.mystery)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MYSTERIES[params.mystery], params.name, params.gender, params.trait)
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
    StoryParams(place="garden_gate", mystery="missing_licorice", name="Mia", gender="girl", trait="attentive"),
    StoryParams(place="porch", mystery="missing_licorice", name="Finn", gender="boy", trait="curious"),
    StoryParams(place="kitchen", mystery="missing_licorice", name="Lily", gender="girl", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solve/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show solve/1."))
        print(sorted(asp.atoms(model, "solve")))
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
            header = f"### {p.name}: {p.place} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
