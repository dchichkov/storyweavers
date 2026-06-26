#!/usr/bin/env python3
"""
storyworlds/worlds/mince_vile_garb_surprise_detective_story.py
===============================================================

A small detective-style story world about a careful little sleuth, a vile smell,
a piece of garb, and a surprise clue that changes the case.

The seed-image:
A child detective notices that a costume room smells vile, a favorite piece of
garb is missing, and everyone assumes it was stolen. After following tiny clues
— a trail of minced herbs, a torn thread, and a surprise hiding place — the
detective learns the garb was not taken away at all. It had been tucked into a
different crate for safekeeping, and the surprise ending proves the room is safe
again.

The world is built as a small simulation:
- physical meters track smell, clutter, wetness, and concealment
- emotional memes track worry, confidence, surprise, and relief
- detective actions drive the state forward and determine the final story

This script follows the shared storyworld contract and includes an inline ASP
twin for reasonableness checks.
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
# World vocab
# ---------------------------------------------------------------------------

PLACE_NAMES = ["the costume room", "the backstage hall", "the old theater"]
DETECTIVE_NAMES = ["Mira", "Ned", "Ivy", "Pip", "Toby", "Rose"]
HELPER_NAMES = ["Aunt June", "Mr. Bell", "the stagehand", "the manager"]
TRAITS = ["sharp-eyed", "patient", "curious", "brave", "quiet", "clever"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the costume room"
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    kind: str
    label: str
    phrase: str
    reveal: str
    obscures: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    detective_name: str
    detective_type: str
    helper: str
    trait: str
    clue: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


MINCE = {
    "herbs": "minced herbs",
    "paper": "minced paper scraps",
    "chalk": "minced chalk dust",
}

CLUES = {
    "herbs": Clue(
        id="herbs",
        kind="food",
        label="a tiny bowl of minced herbs",
        phrase="a tiny bowl of minced herbs",
        reveal="the smell came from the snack basket, not from a thief",
        obscures={"smell"},
    ),
    "paper": Clue(
        id="paper",
        kind="paper",
        label="a strip of minced paper",
        phrase="a strip of minced paper",
        reveal="the torn paper matched a crate label",
        obscures={"label"},
    ),
    "chalk": Clue(
        id="chalk",
        kind="powder",
        label="a dusting of minced chalk",
        phrase="a dusting of minced chalk",
        reveal="the chalk trail led behind the curtain",
        obscures={"floor"},
    ),
}

GARBS = {
    "cape": {"phrase": "a blue stage cape", "kind": "garb"},
    "hat": {"phrase": "a black detective hat", "kind": "garb"},
    "coat": {"phrase": "a neat costume coat", "kind": "garb"},
}

SETTING = Setting(place="the costume room", affords={"look", "sniff", "search", "trace"})


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective story world about mince, vile garb, and surprise.")
    ap.add_argument("--place", choices=PLACE_NAMES)
    ap.add_argument("--name", choices=DETECTIVE_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--clue", choices=CLUES)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(p, c) for p in PLACE_NAMES for c in CLUES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [x for x in combos if x[0] == args.place]
    if args.clue:
        combos = [x for x in combos if x[1] == args.clue]
    if not combos:
        raise StoryError("No valid detective setup matches the given options.")
    place, clue = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        detective_name=args.name or rng.choice(DETECTIVE_NAMES),
        detective_type="girl" if (args.name or "").lower() in {"mira", "ivy", "rose"} else "boy",
        helper=args.helper or rng.choice(HELPER_NAMES),
        trait=args.trait or rng.choice(TRAITS),
        clue=clue,
    )


def _inc(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _mem(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    detective = world.add(Entity(
        id=params.detective_name, kind="character", type=params.detective_type,
        label=params.detective_name, meters={}, memes={"curiosity": 1.0}
    ))
    helper = world.add(Entity(
        id="helper", kind="character", type="adult", label=params.helper
    ))
    garb = world.add(Entity(
        id="garb", type="thing", label="garb",
        phrase=GARBS["cape"]["phrase"], owner=helper.id, caretaker=helper.id
    ))
    clue = world.add(Entity(
        id="clue", type="thing", label=CLUES[params.clue].label,
        phrase=CLUES[params.clue].phrase
    ))
    hidden = world.add(Entity(
        id="crate", type="thing", label="a crate",
        phrase="a wooden crate behind a curtain"
    ))

    # Act 1: the case begins.
    world.say(f"{detective.id} was a {params.trait} little detective who loved neat clues and tidy rooms.")
    world.say(f"One afternoon, {detective.id} went to {params.place} with {helper.label_word}.")
    world.say(f"Then they found that {params.place} smelled vile.")
    _inc(clue, "smell", 1.0)
    _mem(detective, "worry", 1.0)
    world.say(f"{helper.label_word} frowned because the favorite garb was missing from its hook.")

    world.para()

    # Act 2: detective work.
    world.say(f"{detective.id} did not rush. {detective.pronoun().capitalize()} began to look, sniff, and trace the room.")
    if params.clue == "herbs":
        world.say("A basket nearby held minced herbs, and that explained the vile smell.")
        _mem(detective, "surprise", 1.0)
        _inc(clue, "revealed", 1.0)
    elif params.clue == "paper":
        world.say("A scrap of minced paper lay on the floor, and it matched a crate label.")
        _mem(detective, "surprise", 1.0)
        _inc(clue, "revealed", 1.0)
    else:
        world.say("A little dust of minced chalk marked a path behind the curtain.")
        _mem(detective, "surprise", 1.0)
        _inc(clue, "revealed", 1.0)

    world.say(f"{detective.id} found a surprising trail and followed it without making a noise.")
    _mem(detective, "confidence", 1.0)
    _inc(hidden, "concealed", 1.0)

    world.para()

    # Act 3: surprise reveal.
    world.say(f"Behind the curtain, {detective.id} saw the missing garb tucked safely into {hidden.label_word}.")
    world.say(f"The garb had not been stolen at all; it had been moved so it would not get ruined.")
    _mem(detective, "relief", 1.0)
    _mem(helper, "relief", 1.0)
    _mem(detective, "surprise", 1.0)
    world.say(f"{helper.label_word} smiled at the surprise, and {detective.id} smiled too.")
    world.say(f"In the end, the room was neat, the smell made sense, and the garb was back where it belonged.")

    world.facts = {
        "detective": detective,
        "helper": helper,
        "garb": garb,
        "clue": clue,
        "hidden": hidden,
        "params": params,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short detective story for a child about {p.detective_name} finding a vile smell in {p.place}.",
        f"Tell a story where a little detective follows minced clues and discovers that the garb was not stolen.",
        f"Create a gentle mystery story with the words mince, vile, garb, and a surprise at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    detective: Entity = f["detective"]
    helper: Entity = f["helper"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {detective.id}, a {p.trait} little detective who worked with {helper.label_word}.",
        ),
        QAItem(
            question="Why did the room smell vile?",
            answer="The smell came from the clue in the room, especially the minced herbs or other tiny scraps, not from a bad person.",
        ),
        QAItem(
            question="What happened to the garb?",
            answer="The garb was found safely tucked into a crate behind the curtain, so it had not been stolen.",
        ),
        QAItem(
            question="What was the surprise?",
            answer="The surprise was that the missing garb was hiding in a crate all along, and the detective solved the case.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to mince something?",
            answer="To mince something means to cut it into very tiny pieces.",
        ),
        QAItem(
            question="What is garb?",
            answer="Garb is clothing or outfit pieces, especially clothes that fit a special role or style.",
        ),
        QAItem(
            question="Why can a smell seem vile?",
            answer="A smell seems vile when it is very bad, strong, or unpleasant to notice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(out)


ASP_RULES = r"""
valid_place(Place) :- place(Place).
valid_case(Place, Clue) :- valid_place(Place), clue(Clue).

% A vile-smell mystery is reasonable when the room can hold a clue and the
% missing garb can be found by tracing from that clue.
reasonable(Place, Clue) :- valid_case(Place, Clue).
#show reasonable/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACE_NAMES:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_reasonable())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos()")
    print("python only:", sorted(py - clingo))
    print("clingo only:", sorted(clingo - py))
    return 1


CURATED = [
    StoryParams(place="the costume room", detective_name="Mira", detective_type="girl", helper="Aunt June", trait="sharp-eyed", clue="herbs"),
    StoryParams(place="the backstage hall", detective_name="Ned", detective_type="boy", helper="the stagehand", trait="clever", clue="paper"),
    StoryParams(place="the old theater", detective_name="Ivy", detective_type="girl", helper="the manager", trait="patient", clue="chalk"),
]


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
        print(asp_program("#show reasonable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show reasonable/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: clue={p.clue} place={p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
