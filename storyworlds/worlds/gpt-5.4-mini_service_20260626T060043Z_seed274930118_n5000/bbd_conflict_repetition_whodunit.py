#!/usr/bin/env python3
"""
A small whodunit storyworld with conflict and repetition.

Seed premise:
A child detective keeps hearing the same three clues again and again while
searching for the missing bbd token. The suspects disagree, the clues repeat,
and the truth comes out through a careful, state-driven investigation.
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Location:
    id: str
    label: str
    detail: str
    hides: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    type: str
    label: str
    alibi: str
    tells: str
    lies_about: set[str] = field(default_factory=set)
    guilty_if: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    missing: str
    detective_name: str
    detective_gender: str
    sidekick: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Location):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.suspects: dict[str, Suspect] = {}
        self.clues_seen: list[str] = []
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_suspect(self, sus: Suspect) -> Suspect:
        self.suspects[sus.id] = sus
        return sus

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
LOCATIONS = {
    "library": Location("library", "the library", "rows of tall shelves and a whisper-quiet desk",
                        hides={"desk", "drawer", "book"}),
    "kitchen": Location("kitchen", "the kitchen", "a bright table and cupboards that clicked softly",
                        hides={"jar", "drawer", "basket"}),
    "museum": Location("museum", "the museum", "glass cases and a marble hallway",
                       hides={"case", "bench", "plinth"}),
}

MISSING_ITEMS = {
    "bbd": {
        "label": "bbd",
        "phrase": "a tiny brass bbd token",
        "where": {"book", "jar", "case"},
        "story_word": "bbd",
    }
}

DETECTIVES = {
    "girl": ["Mila", "Nina", "Rae", "Lina", "Tess"],
    "boy": ["Owen", "Milo", "Finn", "Jude", "Eli"],
}

SIDEKICKS = ["a kitten", "a notebook", "a flashlight", "a little map"]

SUSPECTS = [
    Suspect("librarian", "woman", "the librarian", "She was sorting returns.", "Her voice stayed very calm.",
            lies_about={"desk"}, guilty_if={"book"}),
    Suspect("cook", "man", "the cook", "He said he had been stirring soup.", "He kept wiping his hands.",
            lies_about={"jar"}, guilty_if={"jar"}),
    Suspect("guide", "woman", "the guide", "She said she was counting visitors.", "She pointed too often at the cases.",
            lies_about={"case"}, guilty_if={"case"}),
]

REPETITION_CLUES = [
    "the same scratch mark",
    "the same little brass shine",
    "the same dusty print",
]


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
def article(noun: str) -> str:
    return "an" if noun[:1].lower() in "aeiou" else "a"


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(DETECTIVES[gender])


def make_detective(world: World, params: StoryParams, rng: random.Random) -> Entity:
    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_gender,
        label=params.detective_name,
        phrase=f"curious little detective {params.detective_name}",
        meters={"focus": 0.0},
        memes={"worry": 0.0, "certainty": 0.0, "conflict": 0.0},
    ))
    sidekick = world.add(Entity(
        id="sidekick",
        kind="thing",
        type="thing",
        label=params.sidekick,
        phrase=params.sidekick,
        owner=detective.id,
        carried_by=detective.id,
    ))
    return detective


def make_world(params: StoryParams) -> World:
    place = LOCATIONS[params.place]
    world = World(place)
    return world


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def intro(world: World, detective: Entity, missing: str) -> None:
    world.say(
        f"{detective.id} was a curious little detective who liked quiet rooms and tidy clues. "
        f"One morning, {detective.pronoun('subject')} noticed that {article(missing)} {missing} token had gone missing from {world.place.label}."
    )
    world.say(
        f"It was not just any token; it was a small brass bbd, and everybody kept saying the same thing: "
        f"it had been here, then it was gone."
    )


def suspect_loop(world: World, detective: Entity, missing: str) -> None:
    world.para()
    world.say(
        f"{detective.id} walked past the shelves and asked the first suspect, then asked again, and then asked one more time."
    )
    for sus in world.suspects.values():
        world.say(f"{sus.label.capitalize()} said, '{sus.alibi}' {sus.tells}")
        world.trace.append(f"asked {sus.id}")
        detective.meters["focus"] = detective.meters.get("focus", 0.0) + 1
        detective.memes["worry"] = detective.memes.get("worry", 0.0) + 0.5
        if missing in sus.lies_about:
            detective.memes["conflict"] = detective.memes.get("conflict", 0.0) + 1


def repeated_clue(world: World, detective: Entity, clue: str) -> None:
    world.say(
        f"Each time {detective.id} looked again, {clue} was there again, just like before."
    )
    detective.meters["focus"] = detective.meters.get("focus", 0.0) + 1
    detective.memes["certainty"] = detective.memes.get("certainty", 0.0) + 1


def gather_trace(world: World, detective: Entity, missing: str) -> str:
    for sus in world.suspects.values():
        if world.place.id in sus.guilty_if:
            return sus.id
    return "cook" if missing == "bbd" else "librarian"


def reveal(world: World, detective: Entity, culprit_id: str, missing: str) -> None:
    culprit = world.suspects[culprit_id]
    world.para()
    world.say(
        f"At last, {detective.id} noticed that the clue kept repeating near the {culprit.label}."
    )
    world.say(
        f"{detective.id} pointed to {culprit.label} and said, "
        f"'{culprit.label.capitalize()}, you took the {missing} bbd token and hid it here because you wanted it for yourself.'"
    )
    world.say(
        f"{culprit.label.capitalize()} sighed. '{culprit.alibi}' But {culprit.tells} "
        f"Then {culprit.pronoun('subject')} opened the hiding place and the brass bbd token gleamed inside."
    )
    world.say(
        f"The room went quiet. The same clue had repeated again and again, but now it fit the truth."
    )


def finish(world: World, detective: Entity, missing: str) -> None:
    world.para()
    world.say(
        f"{detective.id} put the {missing} token back where it belonged. "
        f"After that, the shelves seemed less mysterious, and the little detective smiled at the solved case."
    )


def tell_story(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    world = make_world(params)
    detective = make_detective(world, params, rng)
    missing = params.missing

    intro(world, detective, missing)
    suspect_loop(world, detective, missing)
    for clue in REPETITION_CLUES:
        repeated_clue(world, detective, clue)
    culprit = gather_trace(world, detective, missing)
    reveal(world, detective, culprit, missing)
    finish(world, detective, missing)

    world.facts = {
        "detective": detective,
        "missing": missing,
        "culprit": culprit,
        "place": world.place.id,
    }
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A place contains a hiding spot when the world says so.
has_hide(Place, Spot) :- place(Place), hides(Place, Spot).

% A suspect is plausible as the culprit when their lie and guilty-place match
% the current location's hiding spot list.
plausible_culprit(Place, Suspect) :- suspect(Suspect), culprit_spot(Suspect, Spot),
                                     has_hide(Place, Spot).

% The whodunit is solved when exactly one culprit is plausible.
solved(Place, Suspect) :- plausible_culprit(Place, Suspect).

#show solved/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, loc in LOCATIONS.items():
        lines.append(asp.fact("place", pid))
        for spot in sorted(loc.hides):
            lines.append(asp.fact("hides", pid, spot))
    for sid, sus in [(s.id, s) for s in SUSPECTS]:
        lines.append(asp.fact("suspect", sid))
        for spot in sorted(sus.guilty_if):
            lines.append(asp.fact("culprit_spot", sid, spot))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_solved() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "solved")))


def asp_verify() -> int:
    py = set((place, culprit) for place in LOCATIONS for culprit in valid_culprits(place))
    cl = set(asp_solved())
    if py == cl:
        print(f"OK: clingo gate matches python reasoner ({len(py)} solutions).")
        return 0
    print("MISMATCH between ASP and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


def valid_culprits(place: str) -> list[str]:
    loc = LOCATIONS[place]
    out = []
    for sus in SUSPECTS:
        if any(spot in loc.hides for spot in sus.guilty_if):
            out.append(sus.id)
    return out


# ---------------------------------------------------------------------------
# Params, generation, QA
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    missing: str
    detective_name: str
    detective_gender: str
    sidekick: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with conflict and repetition.")
    ap.add_argument("--place", choices=LOCATIONS.keys())
    ap.add_argument("--missing", choices=MISSING_ITEMS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
    place = args.place or rng.choice(list(LOCATIONS.keys()))
    missing = args.missing or "bbd"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or choose_name(gender, rng)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    if missing not in MISSING_ITEMS:
        raise StoryError("Unknown missing item.")
    return StoryParams(place=place, missing=missing, detective_name=name, detective_gender=gender, sidekick=sidekick)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a child about the missing {f["missing"]} bbd token in {world.place.label}.',
        f"Tell a mystery where {f['detective'].id} keeps hearing the same clue again and again before solving the case.",
        f"Write a simple story with a small conflict, repeated clues, and a final reveal about who hid the bbd token.",
    ]


def story_qa(world: World) -> list[QAItem]:
    d = world.facts["detective"]
    culprit = world.facts["culprit"]
    missing = world.facts["missing"]
    place = world.place.label
    qa = [
        QAItem(
            question=f"What case was {d.id} trying to solve in {place}?",
            answer=f"{d.id} was trying to solve the mystery of the missing {missing} bbd token in {place}.",
        ),
        QAItem(
            question=f"Why did the clues make {d.id} feel mixed up at first?",
            answer=f"The clues made {d.id} feel mixed up because the same clue kept repeating and the suspects did not all tell the truth.",
        ),
        QAItem(
            question=f"Who hid the bbd token?",
            answer=f"The {culprit} hid the bbd token and tried to sound innocent, but the repeated clues gave the answer away.",
        ),
        QAItem(
            question=f"What finally changed at the end of the story?",
            answer=f"At the end, {d.id} found the token, proved who hid it, and put the bbd token back where it belonged.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues to solve a mystery.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means something happens or is said again and again.",
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where readers try to figure out who did something wrong.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  clues seen: {world.clues_seen}")
    lines.append(f"  trace: {world.trace}")
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, "bbd") for place in LOCATIONS]


def asp_program_shown() -> str:
    return asp_program() + "#show solved/2.\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_solved())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in LOCATIONS:
            params = StoryParams(
                place=place,
                missing="bbd",
                detective_name="Mila",
                detective_gender="girl",
                sidekick="a notebook",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
