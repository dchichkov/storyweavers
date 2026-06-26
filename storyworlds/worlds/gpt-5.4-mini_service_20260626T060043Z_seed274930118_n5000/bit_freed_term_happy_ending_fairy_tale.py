#!/usr/bin/env python3
"""
storyworlds/worlds/bit_freed_term_happy_ending_fairy_tale.py
=============================================================

A small fairy-tale storyworld about a tiny enchanted term, a brave child, and
the happy ending that comes when a bit of kindness frees what was trapped.

Seed image:
---
A little fairy-tale kingdom has a story term sealed inside a thorny glass
lantern. A child notices that the lantern is only held shut by a bit of twine
and a tired old charm. With help from a kind bee, the child loosens the knot,
the term is freed, and the castle's song returns.

World model:
---
- Physical meters track things like tightness, light, and bloom.
- Emotional memes track hope, worry, relief, and joy.
- A sealed term can be trapped, then freed by a careful, gentle action.
- The ending is happy only when the released term is shared aloud and the
  world visibly brightens.

The story stays close to a fairy tale tone: a little castle, a lantern, a
helper, a spelllike obstacle, and a peaceful ending image.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    trapped_in: Optional[str] = None
    free: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "queen", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "king", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
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


@dataclass
class StoryParams:
    place: str
    hero_type: str
    hero_name: str
    helper_type: str
    helper_name: str
    seed: Optional[int] = None


SETTINGS = {
    "castle_lane": "the lane beside the old castle",
    "rose_garden": "the rose garden by the stone wall",
    "brook_bridge": "the little bridge over the brook",
    "tower_room": "the bright room at the top of the tower",
}

HEROES = {
    "girl": ["Mina", "Luna", "Tessa", "Nora", "Elin"],
    "boy": ["Oren", "Finn", "Pip", "Milo", "Bram"],
}

HELPERS = {
    "bee": ["Bibi", "Bea", "Bramble"],
    "sparrow": ["Suri", "Tiko", "Merri"],
    "mouse": ["Moss", "Nip", "Pippa"],
}

TRAITS = ["gentle", "curious", "brave", "cheerful", "kind"]


def _ent(root: str, **kwargs) -> Entity:
    return Entity(id=root, **kwargs)


class FairyWorld:
    def __init__(self, place: str) -> None:
        self.world = World(place=place)

    def build(self, params: StoryParams) -> World:
        w = self.world
        child = w.add(Entity(
            id=params.hero_name,
            kind="character",
            type=params.hero_type,
            traits=["little", random.choice(TRAITS)],
            memes={"hope": 1.0, "joy": 0.0, "worry": 0.0, "relief": 0.0},
        ))
        helper = w.add(Entity(
            id=params.helper_name,
            kind="character",
            type=params.helper_type,
            traits=["small", "helpful"],
            memes={"hope": 1.0, "joy": 0.0},
        ))
        lantern = w.add(Entity(
            id="lantern",
            type="lantern",
            label="glass lantern",
            phrase="a glass lantern with a thorny clasp",
            trapped_in="thorn_knot",
            free=False,
            meters={"tightness": 1.0, "light": 0.2},
        ))
        term = w.add(Entity(
            id="term",
            type="term",
            label="term",
            phrase="a tiny story term",
            trapped_in="lantern",
            free=False,
            meters={"tightness": 1.0, "light": 0.0},
            memes={"quiet": 1.0, "hope": 0.0},
        ))
        bit = w.add(Entity(
            id="bit",
            type="bit",
            label="bit of twine",
            phrase="a small bit of twine",
            free=False,
            meters={"tightness": 0.4, "fray": 0.0},
        ))
        castle = w.add(Entity(
            id="castle",
            type="place",
            label="castle",
            phrase="the old castle",
            meters={"silence": 1.0, "shadow": 1.0},
            memes={"sleep": 1.0},
        ))

        w.facts.update(child=child, helper=helper, lantern=lantern, term=term,
                       bit=bit, castle=castle, place=params.place)
        return w


def _free_bit(w: World) -> bool:
    bit = w.get("bit")
    lantern = w.get("lantern")
    if bit.free:
        return False
    bit.free = True
    bit.meters["tightness"] = 0.0
    lantern.meters["tightness"] = max(0.0, lantern.meters.get("tightness", 0.0) - 0.6)
    w.say("The child noticed that only a small bit of twine held the lantern shut.")
    return True


def _loosen_clasp(w: World) -> bool:
    lantern = w.get("lantern")
    term = w.get("term")
    if lantern.meters.get("tightness", 0.0) >= THRESHOLD:
        lantern.meters["tightness"] = 0.0
        term.free = True
        term.trapped_in = None
        term.meters["light"] = 1.0
        term.memes["quiet"] = 0.0
        term.memes["hope"] = 1.0
        return True
    return False


def _spark_release(w: World) -> bool:
    term = w.get("term")
    child = w.get("term")  # placeholder overwritten below
    return False


def _update_release(w: World) -> None:
    term = w.get("term")
    child = w.facts["child"]
    helper = w.facts["helper"]
    lantern = w.get("lantern")
    if term.free and w.facts.get("released"):
        return
    if term.free:
        w.facts["released"] = True
        child.memes["joy"] += 1.0
        child.memes["hope"] += 1.0
        child.memes["relief"] += 1.0
        helper.memes["joy"] += 1.0
        lantern.meters["light"] = 1.0
        w.say("With one careful tug, the knot gave way, and the term was freed.")
        w.say("The castle windows woke with gold, as if they had been waiting for that word all along.")


def _bloom_evening(w: World) -> None:
    child = w.facts["child"]
    term = w.get("term")
    if not term.free:
        return
    if w.facts.get("ending") == "done":
        return
    w.facts["ending"] = "done"
    child.memes["joy"] += 1.0
    w.say(
        f"{child.id} whispered the freed term aloud, and the lane grew bright. "
        f"Even the roses seemed to lift their faces to listen."
    )
    w.say(
        "So the little kingdom kept its gentle secret: a bit of kindness can free "
        "a trapped word, and a freed word can make a whole evening feel new."
    )


def tell_story(params: StoryParams) -> World:
    if params.hero_type not in HEROES:
        raise StoryError("hero_type must be girl or boy")
    if params.helper_type not in HELPERS:
        raise StoryError("helper_type must be bee, sparrow, or mouse")
    if params.place not in SETTINGS:
        raise StoryError("unknown place")

    fw = FairyWorld(SETTINGS[params.place])
    w = fw.build(params)
    child = w.facts["child"]
    helper = w.facts["helper"]
    term = w.get("term")

    w.say(
        f"Once upon a time, in {w.place}, there was a little {child.type} named {child.id} "
        f"who loved fairy tales and happy endings."
    )
    w.say(
        f"That day, {child.id} met {helper.id}, a kindly {helper.type}, beside a glass lantern "
        f"that held a tiny term inside."
    )

    w.para()
    w.say(
        f"The lantern looked stubborn, but {child.id} saw a small bit of twine around the clasp."
    )
    _free_bit(w)
    w.say(
        f"{helper.id} buzzed or fluttered or padded close, and together they watched the bit loosen."
    )
    w.say(
        f"{term.id} stayed quiet at first, because it was still trapped and a little lonely."
    )

    w.para()
    if _loosen_clasp(w):
        child.memes["worry"] = max(0.0, child.memes.get("worry", 0.0) - 1.0)
        w.say(
            f"Then {child.id} gave the clasp one gentle twist, and the old charm slipped apart."
        )
    _update_release(w)
    _bloom_evening(w)

    w.facts["resolved"] = term.free
    return w


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    return [
        "Write a short fairy tale about a tiny term that is trapped and then freed.",
        f"Tell a happy-ending story where {child.id} and {helper.id} use a small bit of help to open a lantern.",
        "Write a gentle story with the words bit, freed, and term, ending in a bright and peaceful image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    term = world.facts["term"]
    bit = world.facts["bit"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"Who was the story about in {SETTINGS[place]}?",
            answer=f"It was about {child.id}, a little {child.type}, and {helper.id}, a kind {helper.type}, in a fairy-tale place.",
        ),
        QAItem(
            question="What small thing helped open the lantern?",
            answer=f"A small bit of twine helped, because the lantern was held shut by only a bit.",
        ),
        QAItem(
            question="What happened to the term at the end?",
            answer="The term was freed from the lantern, and the story ended happily with the castle bright again.",
        ),
        QAItem(
            question=f"Why did {child.id} feel happy at the end?",
            answer=f"{child.id} felt happy because the term was freed, the lantern was open, and the evening turned bright and peaceful.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a term?",
        answer="A term is a word or phrase that means something in a sentence, a lesson, or a story.",
    ),
    QAItem(
        question="What does freed mean?",
        answer="Freed means let out, opened, or no longer trapped.",
    ),
    QAItem(
        question="What is a bit?",
        answer="A bit is a small piece of something.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.free:
            bits.append("free=True")
        if e.trapped_in:
            bits.append(f"trapped_in={e.trapped_in}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A term is freed when the lantern is no longer tight.
freed(term) :- bit_free(bit), loosened(lantern).

% A happy ending exists if the term is freed and the castle brightens.
happy_ending :- freed(term), bright(castle).

% The bit is considered free after the child notices and loosens it.
bit_free(bit) :- notice(bit), gentle_tug(bit).

% The lantern loosens when the twine is opened.
loosened(lantern) :- bit_free(bit).

% Brightness follows freedom.
bright(castle) :- freed(term).
#show freed/1.
#show happy_ending/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("notice", "bit"),
        asp.fact("gentle_tug", "bit"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_check() -> int:
    import asp
    model = asp.one_model(asp_program("#show freed/1. #show happy_ending/0."))
    atoms = set((sym.name, len(sym.arguments), tuple(a.name if a.type != a.type.Number else a.number for a in sym.arguments)) for sym in model)
    expected = {("freed", 1, ("term",)), ("happy_ending", 0, ())}
    if atoms == expected:
        print("OK: ASP and Python gate agree on the happy ending.")
        return 0
    print("MISMATCH: ASP and Python gate disagree.")
    print("model:", atoms)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about a bit, a freed term, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=list(HELPERS))
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(list(HELPERS))
    name = args.name or rng.choice(HEROES[hero_type])
    helper_name = args.helper_name or rng.choice(HELPERS[helper_type])
    place = args.place or rng.choice(list(SETTINGS))
    return StoryParams(place=place, hero_type=hero_type, hero_name=name,
                       helper_type=helper_type, helper_name=helper_name)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show freed/1. #show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_check())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show freed/1. #show happy_ending/0."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="castle_lane", hero_type="girl", hero_name="Mina", helper_type="bee", helper_name="Bibi"),
            StoryParams(place="rose_garden", hero_type="boy", hero_name="Oren", helper_type="sparrow", helper_name="Suri"),
            StoryParams(place="brook_bridge", hero_type="girl", hero_name="Luna", helper_type="mouse", helper_name="Moss"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
