#!/usr/bin/env python3
"""
storyworlds/worlds/flick_eatie_dialogue_moral_value_inner_monologue.py
======================================================================

A small detective-story world with dialogue, moral value, and inner monologue.

Seed premise:
- Flick is a tiny child detective who notices little things.
- Eatie is a nervous helper who loves snacks and knows the neighborhood.
- A small missing item creates a moral problem: should someone hide the truth,
  or admit a mistake and make it right?

The world simulates:
- a clue trail made of physical meters
- suspicion, worry, relief, and honesty as memes
- dialogue that can reveal, mislead, or repair trust
- inner monologue that drives the detective's reasoning
- a moral turn where the best choice is to tell the truth

This file is standalone and follows the Storyweavers storyworld contract.
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
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0
SUSPICION_LIMIT = 2.0
TRUTH_LIMIT = 1.0

PLACES = {
    "alley": "the quiet alley",
    "bakery": "the little bakery",
    "library": "the bright library",
    "garden": "the old garden",
}

MORAL_VALUES = [
    "honesty",
    "kindness",
    "fairness",
]

CLUES = {
    "crumb": "crumb",
    "flicker": "flicker",
    "smudge": "smudge",
    "footprint": "footprint",
}

MISSING_THINGS = {
    "jam_tart": "a jam tart",
    "silver_key": "a silver key",
    "red_note": "a red note",
}

SUSPECTS = {
    "eatie": "Eatie",
    "mira": "Mira",
    "otto": "Otto",
}


# ---------------------------------------------------------------------------
# Entity model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.id in {"flick", "eatie", "mira", "otto"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name(self) -> str:
        return self.label or self.id


@dataclass
class Scene:
    place: str = "the alley"
    clue: str = "crumb"
    missing: str = "jam_tart"
    suspect: str = "eatie"
    moral_value: str = "honesty"


@dataclass
class StoryParams:
    place: str
    clue: str
    missing: str
    suspect: str
    moral_value: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        w = World(self.scene)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Reasoning / state updates
# ---------------------------------------------------------------------------
def add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def story_truth(world: World, flick: Entity, suspect: Entity, missing: Entity) -> bool:
    return suspect.memes.get("guilt", 0.0) >= TRUTH_LIMIT and missing.meters.get("found", 0.0) >= THRESHOLD


def clue_strength(world: World) -> float:
    total = 0.0
    for ent in world.entities.values():
        total += ent.meters.get("clue", 0.0)
    return total


def suspect_pressure(suspect: Entity) -> float:
    return suspect.memes.get("worry", 0.0) + suspect.memes.get("guilt", 0.0)


def make_scene(place: str, clue: str, missing: str, suspect: str, moral_value: str) -> Scene:
    return Scene(place=PLACES[place], clue=clue, missing=missing, suspect=suspect, moral_value=moral_value)


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def intro(world: World, flick: Entity, eatie: Entity, missing: Entity) -> None:
    world.say(
        f"Flick was a small detective who loved neat clues and quiet corners."
    )
    world.say(
        f"One morning, {eatie.name()} found that {missing.phrase} had gone missing."
    )
    add_meme(flick, "curiosity", 1)
    add_meme(eatie, "worry", 1)


def arrive(world: World, flick: Entity, place: str) -> None:
    world.para()
    world.say(f"Flick hurried to {PLACES[place]}.")
    world.say("The place looked ordinary, which made Flick even more careful.")


def inspect_clue(world: World, flick: Entity, clue: Entity) -> None:
    add_meter(clue, "clue", 1)
    add_meme(flick, "focus", 1)
    world.say(
        f'Flick knelt beside a tiny {clue.label}. "That did not get here by magic," '
        f'Flick thought.'
    )
    world.say("In Flick's head, the story began to line up: someone had passed this way in a hurry.")


def dialogue_question(world: World, flick: Entity, suspect: Entity, clue: Entity) -> None:
    add_meme(suspect, "worry", 1)
    world.say(
        f'"Did you see who came by?" Flick asked. "{suspect.name()}, I mean."'
    )
    world.say(
        f'"Maybe," {suspect.name()} said, "but I was only looking for crumbs."'
    )
    world.say(
        f'Flick watched the answer the way a cat watches a mouse hole.'
    )


def inner_monologue(world: World, flick: Entity, suspect: Entity, clue: Entity, missing: Entity) -> None:
    add_meme(flick, "suspicion", 1)
    world.say(
        f'Flick thought, "A crumb near a missing {missing.label} is not a coincidence."'
    )
    world.say(
        f'"But a frightened voice can hide a mistake, not always a crime," Flick thought next.'
    )
    if clue_strength(world) >= 1:
        world.say(
            f'Another thought followed: "If I keep listening, the truth may walk right into the light."'
        )


def reveal(world: World, flick: Entity, suspect: Entity, missing: Entity, clue: Entity) -> None:
    add_meme(suspect, "guilt", 1)
    add_meter(missing, "found", 1)
    world.say(
        f'Flick pointed to the {clue.label}. "You came here with {missing.phrase}, didn\'t you?"'
    )
    world.say(
        f'{suspect.name()} looked down. "I did," they admitted. "I took it because I was hungry."'
    )
    world.say(
        f'"That was wrong," Flick said softly, "but telling the truth now is the brave part."'
    )


def moral_turn(world: World, flick: Entity, suspect: Entity, missing: Entity) -> None:
    add_meme(flick, "fairness", 1)
    add_meme(suspect, "relief", 1)
    world.para()
    world.say(
        f'Flick took a breath and chose {world.scene.moral_value}.'
    )
    world.say(
        f'"Let\'s make it right," Flick said. "We can return {missing.phrase} and say what happened."'
    )
    world.say(
        f'{suspect.name()} nodded, and their shoulders stopped hunching.'
    )


def resolution(world: World, flick: Entity, suspect: Entity, missing: Entity) -> None:
    world.para()
    add_meme(flick, "pride", 1)
    add_meme(suspect, "trust", 1)
    world.say(
        f'Together they brought back {missing.phrase}.'
    )
    world.say(
        f'The grown-up thanked them for the honesty, and the room felt lighter.'
    )
    world.say(
        f'By the end, Flick had solved the case, and {suspect.name()} had learned that truth can be kinder than hiding.'
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    scene = make_scene(params.place, params.clue, params.missing, params.suspect, params.moral_value)
    world = World(scene)

    flick = world.add(Entity(
        id="flick",
        kind="character",
        label="Flick",
        traits=["careful", "sharp-eyed", "small"],
    ))
    eatie = world.add(Entity(
        id="eatie",
        kind="character",
        label="Eatie",
        traits=["nervous", "hungry", "kind"],
    ))
    suspect = eatie if params.suspect == "eatie" else world.add(Entity(
        id=params.suspect,
        kind="character",
        label=SUSPECTS.get(params.suspect, params.suspect.title()),
        traits=["shifty", "uneasy"],
    ))
    missing = world.add(Entity(
        id=params.missing,
        kind="thing",
        label=params.missing.replace("_", " "),
        phrase=MISSING_THINGS[params.missing],
        owner="bakery",
    ))
    clue = world.add(Entity(
        id=params.clue,
        kind="thing",
        label=CLUES[params.clue],
        phrase=f"a small {CLUES[params.clue]}",
    ))

    world.facts.update(
        flick=flick,
        eatie=eatie,
        suspect=suspect,
        missing=missing,
        clue=clue,
        scene=scene,
    )

    intro(world, flick, eatie, missing)
    arrive(world, flick, params.place)
    inspect_clue(world, flick, clue)
    dialogue_question(world, flick, suspect, clue)
    inner_monologue(world, flick, suspect, clue, missing)
    reveal(world, flick, suspect, missing, clue)
    moral_turn(world, flick, suspect, missing)
    resolution(world, flick, suspect, missing)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene: Scene = f["scene"]
    return [
        f'Write a short detective story for a young child set in {scene.place}, with a tiny clue and a gentle moral lesson.',
        f"Tell a mystery story where Flick uses dialogue and inner monologue to help {f['suspect'].name()} tell the truth about {f['missing'].phrase}.",
        f'Write a child-friendly detective story that includes the word "{scene.clue}" and ends with a moral choice about {scene.moral_value}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    flick: Entity = f["flick"]
    suspect: Entity = f["suspect"]
    missing: Entity = f["missing"]
    clue: Entity = f["clue"]
    scene: Scene = f["scene"]

    return [
        QAItem(
            question="Who solved the mystery in the story?",
            answer="Flick solved the mystery by following the clue, asking careful questions, and listening to the truth.",
        ),
        QAItem(
            question=f"What clue did Flick notice in {scene.place}?",
            answer=f"Flick noticed a tiny {clue.label}, and that clue helped point toward what had happened.",
        ),
        QAItem(
            question=f"What was missing at the start of the story?",
            answer=f"{missing.phrase.capitalize()} was missing, which made the mystery begin.",
        ),
        QAItem(
            question=f"Why did {suspect.name()} admit what happened?",
            answer=f"{suspect.name()} admitted it because Flick kept asking gently and chose honesty instead of harsh blame.",
        ),
        QAItem(
            question=f"What did Flick say should be done at the end?",
            answer=f"Flick said they should make it right by returning {missing.phrase} and telling the truth.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone figure something out.",
        ),
        QAItem(
            question="Why is honesty important?",
            answer="Honesty is important because telling the truth helps people fix mistakes and trust each other.",
        ),
    ]
    return out


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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/4.
#show valid_story/5.

place(alley). place(bakery). place(library). place(garden).
clue(crumb). clue(flicker). clue(smudge). clue(footprint).
missing(jam_tart). missing(silver_key). missing(red_note).
suspect(eatie). suspect(mira). suspect(otto).
moral(honesty). moral(kindness). moral(fairness).

at_risk(C, M) :- clue(C), missing(M).
truthful_story(P, C, M, S, V) :- place(P), clue(C), missing(M), suspect(S), moral(V),
                                 at_risk(C, M), V = honesty.
valid(P, C, M, S) :- place(P), clue(C), missing(M), suspect(S), at_risk(C, M).
valid_story(P, C, M, S, V) :- truthful_story(P, C, M, S, V).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for m in MISSING_THINGS:
        lines.append(asp.fact("missing", m))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    for v in MORAL_VALUES:
        lines.append(asp.fact("moral", v))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
    if clingo - py:
        print("  only in clingo:", sorted(clingo - py))
    return 1


# ---------------------------------------------------------------------------
# Registries / validation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for clue in CLUES:
            for missing in MISSING_THINGS:
                for suspect in SUSPECTS:
                    combos.append((place, clue, missing, suspect))
    return combos


def explain_rejection() -> str:
    return "(No story: invalid combination.)"


# ---------------------------------------------------------------------------
# Public contract
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective story world with flick, eatie, dialogue, moral value, and inner monologue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--missing", choices=MISSING_THINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--moral-value", choices=MORAL_VALUES, dest="moral_value")
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
    combos = valid_combos()
    combos = [c for c in combos if (args.place is None or c[0] == args.place)]
    combos = [c for c in combos if (args.clue is None or c[1] == args.clue)]
    combos = [c for c in combos if (args.missing is None or c[2] == args.missing)]
    combos = [c for c in combos if (args.suspect is None or c[3] == args.suspect)]
    if not combos:
        raise StoryError(explain_rejection())
    place, clue, missing, suspect = rng.choice(sorted(combos))
    moral_value = args.moral_value or rng.choice(MORAL_VALUES)
    return StoryParams(
        place=place,
        clue=clue,
        missing=missing,
        suspect=suspect,
        moral_value=moral_value,
    )


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:\n")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("bakery", "crumb", "jam_tart", "eatie", "honesty"),
            StoryParams("library", "smudge", "red_note", "mira", "kindness"),
            StoryParams("garden", "footprint", "silver_key", "otto", "fairness"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
