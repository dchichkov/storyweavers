#!/usr/bin/env python3
"""
Whodunit-style winter storyworld: a small mystery in the frost, with a child
detective, a few plausible suspects, and a lesson learned about looking at
clues before guessing.

Seed premise:
---
On a frosty morning, a child finds that something important is missing. The
story follows a tiny investigation: noticing footprints, asking careful
questions, and learning that bravery means checking the dark little places
anyway. The child also hears some detective jargon and learns what it means.

This world is designed to produce complete child-facing stories with:
- a setup mystery,
- a clue-driven middle,
- a brave search,
- a solved ending,
- and a clear lesson learned.
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: Optional[str] = None
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    frosty: bool = True
    clue_style: str = "plain"


@dataclass
class Mystery:
    id: str
    missing_item: str
    phrase: str
    clue: str
    suspect: str
    culprit: str
    hiding_place: str
    lesson: str
    bravery_move: str
    jargon_word: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

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

    def note(self, text: str) -> None:
        self.trace.append(text)


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "cottage": Setting(place="the little cottage"),
    "garden": Setting(place="the frost-tipped garden"),
    "shed": Setting(place="the garden shed"),
    "library": Setting(place="the quiet library"),  # indoor but still frosty outside
}

MYSTERIES = {
    "cookie_tin": Mystery(
        id="cookie_tin",
        missing_item="cookie tin",
        phrase="a shiny cookie tin of star cookies",
        clue="tiny sugar crumbs on the floor",
        suspect="the cat",
        culprit="the windy front step",
        hiding_place="the porch bench",
        lesson="look at clues before guessing",
        bravery_move="check the dark porch by yourself",
        jargon_word="alibi",
    ),
    "lantern": Mystery(
        id="lantern",
        missing_item="lantern",
        phrase="a brass lantern with a warm little flame",
        clue="a trail of wax drops near the door",
        suspect="the gardener",
        culprit="the hook by the back wall",
        hiding_place="the coat rack",
        lesson="a mystery gets easier when you slow down",
        bravery_move="walk into the chilly shed",
        jargon_word="clue",
    ),
    "mitten": Mystery(
        id="mitten",
        missing_item="mitten",
        phrase="a knitted mitten with a blue snowflake",
        clue="one tiny blue thread stuck on a chair",
        suspect="the dog",
        culprit="the fireplace basket",
        hiding_place="the toy chest",
        lesson="being brave can also mean asking kindly",
        bravery_move="reach under the icy toy chest",
        jargon_word="suspect",
    ),
}

GENDERS = ["girl", "boy"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["curious", "careful", "brave", "bright", "patient", "sharp-eyed"]

GLOSSARY = {
    "alibi": "An alibi is a reason someone could not have done something, because they were somewhere else.",
    "clue": "A clue is a small piece of helpful information that can point to an answer.",
    "suspect": "A suspect is someone who might have done the missing thing, until the clues tell more of the story.",
    "mystery": "A mystery is something puzzling that needs careful thinking to solve.",
}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the setting can host the mystery and the mystery has a
% single hiding place and a plausible false suspect.
valid_story(S, M) :- setting(S), mystery(M), has_clue(M), has_culprit(M), has_suspect(M).

% Surface facts are enough for parity checking: each mystery needs its own set.
has_clue(M) :- clue_of(M, _).
has_suspect(M) :- suspect_of(M, _).
has_culprit(M) :- culprit_of(M, _).

#show valid_story/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.frosty:
            lines.append(asp.fact("frosty", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_of", mid, m.clue))
        lines.append(asp.fact("suspect_of", mid, m.suspect))
        lines.append(asp.fact("culprit_of", mid, m.culprit))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid in MYSTERIES:
            combos.append((sid, mid))
    return combos


def explain_rejection(setting: str, mystery: str) -> str:
    return f"(No story: {mystery} does not fit the {setting} mystery pattern.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        traits=[params.trait, "little"],
        meters={"courage": 0.0, "cold": 0.0, "certainty": 0.0},
        memes={"bravery": 0.0, "curiosity": 0.0, "lesson_learned": 0.0, "worry": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=params.helper,
        meters={"warmth": 1.0},
        memes={"trust": 1.0},
    ))
    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type=mystery.missing_item,
        label=mystery.missing_item,
        phrase=mystery.phrase,
        owner=child.id,
        location="unknown",
    ))

    world.facts.update(child=child, helper=helper, missing=missing, mystery=mystery)
    return world


def intro(world: World) -> None:
    c: Entity = world.facts["child"]
    m: Mystery = world.facts["mystery"]
    world.say(
        f"On a frosty morning at {world.setting.place}, {c.label} found that {m.missing_item} was gone."
    )
    world.say(
        f"{c.label.capitalize()} had loved that {m.phrase}, so the empty spot on the shelf felt strange."
    )


def suspicion(world: World) -> None:
    c: Entity = world.facts["child"]
    h: Entity = world.facts["helper"]
    m: Mystery = world.facts["mystery"]
    c.memes["curiosity"] += 1
    c.memes["worry"] += 1
    world.say(
        f"{c.label.capitalize()} and {h.label} began a little whodunit, using detective jargon like '{m.jargon_word}'."
    )
    world.say(
        f"The first guess was {m.suspect}, but {h.label} said a real mystery needs a clue before a suspect."
    )


def clue_scene(world: World) -> None:
    c: Entity = world.facts["child"]
    m: Mystery = world.facts["mystery"]
    c.meters["certainty"] += 1
    world.say(
        f"Near the door, they found {m.clue}, and that was better than any guess."
    )
    world.say(
        f"The frosty air made {c.label}'s nose chilly, but {c.label} kept looking instead of running inside."
    )


def brave_search(world: World) -> None:
    c: Entity = world.facts["child"]
    m: Mystery = world.facts["mystery"]
    c.meters["cold"] += 1
    c.memes["bravery"] += 1
    world.say(
        f"Then {c.label} decided to {m.bravery_move}, even though the shadows looked a little spooky."
    )
    world.say(
        f"That brave step mattered, because the {m.missing_item} was hiding where the cold could not hurt it."
    )


def reveal(world: World) -> None:
    c: Entity = world.facts["child"]
    h: Entity = world.facts["helper"]
    m: Mystery = world.facts["mystery"]
    missing: Entity = world.facts["missing"]
    missing.location = m.hiding_place
    c.meters["certainty"] += 1
    c.memes["lesson_learned"] += 1
    c.memes["worry"] = 0.0
    world.say(
        f"They finally looked at {m.hiding_place}, and there was the {m.missing_item} all along."
    )
    world.say(
        f"{h.label} laughed softly, because the answer had been simple: the {m.missing_item} had slipped into {m.culprit}."
    )


def ending(world: World) -> None:
    c: Entity = world.facts["child"]
    h: Entity = world.facts["helper"]
    m: Mystery = world.facts["mystery"]
    world.say(
        f"{c.label} tucked the {m.missing_item} back in its place and learned to {m.lesson}."
    )
    world.say(
        f"After that, {c.label} felt proud and brave, and the frosty morning seemed friendly again with {h.label} beside {c.label}."
    )


def tell_story(world: World) -> World:
    intro(world)
    world.para()
    suspicion(world)
    clue_scene(world)
    world.para()
    brave_search(world)
    reveal(world)
    ending(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    c: Entity = world.facts["child"]
    m: Mystery = world.facts["mystery"]
    return [
        f'Write a child-friendly whodunit story about "{m.missing_item}" in the frost, using the word "{m.jargon_word}".',
        f"Tell a short mystery where {c.label} is brave enough to follow clues and solve a small missing-item puzzle.",
        f"Write a gentle detective story with a frosty setting, a false suspect, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c: Entity = world.facts["child"]
    h: Entity = world.facts["helper"]
    m: Mystery = world.facts["mystery"]
    return [
        QAItem(
            question=f"What was missing at the start of the story?",
            answer=f"The missing thing was the {m.missing_item}.",
        ),
        QAItem(
            question=f"Who helped {c.label} look for it?",
            answer=f"{h.label} helped {c.label} look for the missing {m.missing_item}.",
        ),
        QAItem(
            question=f"What clue pointed them in the right direction?",
            answer=f"The clue was {m.clue}.",
        ),
        QAItem(
            question=f"Why did {c.label} feel brave in the story?",
            answer=f"{c.label} felt brave because {c.label} kept searching in the frosty place instead of giving up.",
        ),
        QAItem(
            question=f"What lesson did {c.label} learn?",
            answer=f"{c.label} learned to {m.lesson}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    m: Mystery = world.facts["mystery"]
    out = []
    for word in [m.jargon_word, "mystery", "clue", "suspect"]:
        out.append(QAItem(question=f"What is a {word}?", answer=GLOSSARY[word]))
    return out


# ---------------------------------------------------------------------------
# Serialization / trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.location:
            parts.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(parts)}")
    return "\n".join(lines)


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
# Generation helpers
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return prompts(world)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="cottage", mystery="cookie_tin", name="Mia", gender="girl", helper="mother", trait="careful"),
    StoryParams(setting="garden", mystery="lantern", name="Theo", gender="boy", helper="father", trait="curious"),
    StoryParams(setting="shed", mystery="mitten", name="Lena", gender="girl", helper="grandmother", trait="brave"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit-style frosty storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting and args.mystery and (args.setting, args.mystery) not in combos:
        raise StoryError(explain_rejection(args.setting, args.mystery))
    choices = [c for c in combos if (not args.setting or c[0] == args.setting) and (not args.mystery or c[1] == args.mystery)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery = rng.choice(sorted(choices))
    gender = args.gender or rng.choice(GENDERS)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or rng.choice(["Mia", "Theo", "Nina", "Owen", "Luna", "Finn", "Ava", "Eli"])
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, helper=helper, trait=trait)


def asp_show() -> str:
    return asp_program("#show valid_story/2.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible story combos:\n")
        for s, m in combos:
            print(f"  {s:10} {m}")
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
