#!/usr/bin/env python3
"""
A compact Storyweavers world: a tiny realm mystery built from a misunderstanding,
light humor, and a transformation that solves the puzzle.

The seed premise is simple:
- In a small realm, someone believes a strange noise means trouble.
- The "clue" turns out to be funny and harmless.
- The truth transforms something ordinary into something wonderful.

The prose engine simulates the state of the realm, the rumor, the clues, and the
final change so the ending is earned rather than swapped in.
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
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Realm:
    name: str
    mood: str = "quiet"
    clues: list[str] = field(default_factory=list)
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

    def copy(self) -> "Realm":
        import copy as _copy

        clone = Realm(self.name, self.mood)
        clone.clues = list(self.clues)
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    realm: str
    hero_name: str
    hero_type: str
    keeper_name: str
    keeper_type: str
    clue: str
    object: str
    seed: Optional[int] = None


@dataclass
class Mystery:
    id: str
    clue: str
    noisy: str
    false_meaning: str
    true_meaning: str
    transform_target: str
    transform_result: str
    location: str


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
REALMS = {
    "moon_glen": "Moon Glen",
    "copper_court": "Copper Court",
    "willow_hall": "Willow Hall",
    "blue_crypt": "Blue Crypt",
}

HERO_NAMES = ["Nia", "Toby", "Mina", "Pip", "Lena", "Arlo", "June", "Soren"]
KEEPER_NAMES = ["Queen Mira", "Sir Bram", "Aunt Tilda", "Old Rowan"]
HERO_TYPES = ["girl", "boy"]
KEEPER_TYPES = ["queen", "king", "woman", "man"]

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        clue="a tiny silver bell",
        noisy="a little ringing sound",
        false_meaning="a trapped mouse warning everyone",
        true_meaning="a moth bumping the bell by accident",
        transform_target="an old banner",
        transform_result="a bright map",
        location="the archway",
    ),
    "mirror": Mystery(
        id="mirror",
        clue="a foggy mirror",
        noisy="a shimmery flash",
        false_meaning="a ghost hiding in the hall",
        true_meaning="moonlight on glass",
        transform_target="a plain stone",
        transform_result="a glowing clue-stone",
        location="the long corridor",
    ),
    "kettle": Mystery(
        id="kettle",
        clue="a dented kettle",
        noisy="a puffing hiss",
        false_meaning="a dragon in the kitchen",
        true_meaning="steam escaping from tea",
        transform_target="a dull key",
        transform_result="a brass key that shines like sun",
        location="the hearth room",
    ),
}

# ASP helpers
ASP_RULES = r"""
% A mystery is valid when a clue, a false meaning, and a transformation all belong together.
valid_mystery(R, M) :- realm(R), mystery(M).

% The realm is curious when a noisy clue can be mistaken for something scary or silly.
misunderstood(M) :- mystery(M), false_meaning(M, _).

% The ending resolves when the transformed object becomes useful and bright.
resolved(M) :- mystery(M), transform_result(M, _).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for rid in REALMS:
        lines.append(asp.fact("realm", rid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("noisy", mid, m.noisy))
        lines.append(asp.fact("false_meaning", mid, m.false_meaning))
        lines.append(asp.fact("true_meaning", mid, m.true_meaning))
        lines.append(asp.fact("transform_target", mid, m.transform_target))
        lines.append(asp.fact("transform_result", mid, m.transform_result))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    program = asp_program("#show valid_mystery/2.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "valid_mystery"))
    py = set((rid, mid) for rid in REALMS for mid in MYSTERIES)
    if atoms == py:
        print(f"OK: clingo gate matches Python registry ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python registry.")
    print("only in clingo:", sorted(atoms - py))
    print("only in python:", sorted(py - atoms))
    return 1


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def _say_intro(world: Realm, hero: Entity, keeper: Entity, mystery: Mystery) -> None:
    world.say(
        f"In {world.name}, {hero.id} loved quiet corners, curious shelves, and secret little puzzles."
    )
    world.say(
        f"One evening, {hero.pronoun()} and {keeper.id} heard {mystery.noisy} near {mystery.location}."
    )
    world.say(
        f"{hero.id} thought the sound meant {mystery.false_meaning}, but {keeper.id} only raised an eyebrow."
    )


def _investigate(world: Realm, hero: Entity, keeper: Entity, mystery: Mystery) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"{hero.id} tiptoed closer with {hero.pronoun('possessive')} candle, trying not to laugh at the wobble in {hero.pronoun('possessive')} knees."
    )
    world.say(
        f"{keeper.id} looked too serious for a moment, then noticed that the 'monster sign' was only {mystery.clue}."
    )
    world.say(
        f"That made {hero.id} blink. The grand mystery was already starting to look a little silly."
    )


def _reveal(world: Realm, hero: Entity, keeper: Entity, mystery: Mystery) -> None:
    world.say(
        f"When {hero.id} touched {mystery.clue}, the {mystery.noisy} came again, and at last everyone saw the truth: {mystery.true_meaning}."
    )
    world.say(
        f"{keeper.id} laughed and said the realm had nearly been frightened by a very unscary mistake."
    )


def _transform(world: Realm, hero: Entity, keeper: Entity, mystery: Mystery) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"Then {hero.id} lifted {mystery.transform_target}, and the old thing changed into {mystery.transform_result}."
    )
    world.say(
        f"The new shine showed the way to the hidden door, and the whole hall felt brighter than before."
    )
    world.say(
        f"{hero.id} grinned at {keeper.id}; the mystery was solved, the joke was shared, and the realm looked a little kinder."
    )


def tell_story(params: StoryParams) -> Realm:
    if params.realm not in REALMS:
        raise StoryError("Unknown realm.")
    if params.clue not in MYSTERIES:
        raise StoryError("Unknown mystery clue.")
    mystery = MYSTERIES[params.clue]

    world = Realm(REALMS[params.realm])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    keeper = world.add(Entity(id=params.keeper_name, kind="character", type=params.keeper_type))
    world.facts.update(hero=hero, keeper=keeper, mystery=mystery, params=params)

    _say_intro(world, hero, keeper, mystery)
    world.para()
    _investigate(world, hero, keeper, mystery)
    world.para()
    _reveal(world, hero, keeper, mystery)
    _transform(world, hero, keeper, mystery)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: Realm) -> list[str]:
    p = world.facts["params"]
    m = world.facts["mystery"]
    return [
        f"Write a short mystery story set in a small realm called {p.realm} with a funny misunderstanding and a real transformation.",
        f"Tell a child-friendly mystery where {p.hero_name} mistakes {m.noisy} for danger, then learns the truth and sees something transform.",
        f"Create a gentle realm mystery that starts with {m.clue}, includes humor, and ends with a surprising change.",
    ]


def story_qa(world: Realm) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    m: Mystery = f["mystery"]
    return [
        QAItem(
            question=f"What made {p.hero_name} think something scary was happening in {world.name}?",
            answer=f"{m.noisy} near {m.location} made {p.hero_name} think {m.false_meaning}.",
        ),
        QAItem(
            question=f"What was the funny mistake in the story?",
            answer=f"The funny mistake was that everyone first thought {m.false_meaning}, but it was really {m.true_meaning}.",
        ),
        QAItem(
            question=f"What changed at the end of the mystery?",
            answer=f"{m.transform_target} transformed into {m.transform_result}, which helped solve the puzzle.",
        ),
        QAItem(
            question=f"How did the story end for {p.hero_name} and {p.keeper_name}?",
            answer=f"They laughed together, solved the mystery, and left {world.name} feeling brighter and safer.",
        ),
    ]


def world_knowledge_qa(world: Realm) -> list[QAItem]:
    m: Mystery = world.facts["mystery"]
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something means one thing, but the real meaning is different.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is when something is funny and makes people smile or laugh.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another.",
        ),
        QAItem(
            question=f"Why was {m.clue} important?",
            answer=f"It was the clue that led the characters to the real answer instead of the wrong one.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: Realm) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"mood={world.mood}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery realm with misunderstanding, humor, and transformation.")
    ap.add_argument("--realm", choices=sorted(REALMS))
    ap.add_argument("--clue", choices=sorted(MYSTERIES))
    ap.add_argument("--name")
    ap.add_argument("--keeper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--keeper-type", choices=sorted(set(KEEPER_TYPES)))
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
    realm = args.realm or rng.choice(sorted(REALMS))
    clue = args.clue or rng.choice(sorted(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    keeper_name = args.keeper or rng.choice(KEEPER_NAMES)
    hero_type = gender
    keeper_type = args.keeper_type or rng.choice(KEEPER_TYPES)
    return StoryParams(
        realm=realm,
        hero_name=hero_name,
        hero_type=hero_type,
        keeper_name=keeper_name,
        keeper_type=keeper_type,
        clue=clue,
        object=MYSTERIES[clue].transform_target,
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def curated() -> list[StoryParams]:
    return [
        StoryParams(realm="moon_glen", hero_name="Nia", hero_type="girl", keeper_name="Queen Mira", keeper_type="queen", clue="mirror", object=MYSTERIES["mirror"].transform_target),
        StoryParams(realm="copper_court", hero_name="Toby", hero_type="boy", keeper_name="Sir Bram", keeper_type="man", clue="bell", object=MYSTERIES["bell"].transform_target),
        StoryParams(realm="blue_crypt", hero_name="Lena", hero_type="girl", keeper_name="Aunt Tilda", keeper_type="woman", clue="kettle", object=MYSTERIES["kettle"].transform_target),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_mystery/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show valid_mystery/2."))
        items = sorted(set(asp.atoms(model, "valid_mystery")))
        print(f"{len(items)} compatible mysteries:")
        for rid, mid in items:
            print(f"  {rid} {mid}")
        return

    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
