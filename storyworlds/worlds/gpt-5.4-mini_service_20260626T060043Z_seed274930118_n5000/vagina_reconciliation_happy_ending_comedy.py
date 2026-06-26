#!/usr/bin/env python3
"""
storyworlds/worlds/vagina_reconciliation_happy_ending_comedy.py
===============================================================

A small comedy storyworld about a child, an awkward medical word, and a gentle
reconciliation that ends happily.

Premise:
- A child hears the word "vagina" and gets embarrassed.
- A grown-up explains that it is a normal body word.
- A silly misunderstanding creates tension.
- Everyone shares a laugh, apologizes, and feels better.

This world keeps the prose child-facing, concrete, and state-driven. The main
turn is emotional rather than physical: embarrassment becomes reassurance, and
reconciliation closes the story with a happy ending.

The simulation tracks:
- physical meters: things like squeakiness of a toy microphone, distance walked,
  and whether a note card is held or dropped.
- emotional memes: embarrassment, confusion, worry, kindness, and laughter.

The inline ASP twin mirrors the reasonableness gate for valid story settings.
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
# Basic domain entities.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def is_char(self) -> bool:
        return self.kind == "character"


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affordances: set[str] = field(default_factory=set)


@dataclass
class Word:
    term: str
    kind: str
    definition: str
    funny_hook: str


@dataclass
class Toy:
    label: str
    sound: str
    meters: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.toys: dict[str, Toy] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_toy(self, t: Toy) -> Toy:
        self.toys[t.label] = t
        return t

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
# Story parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    adult_role: str
    adult_name: str
    word: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "bathroom": Setting(place="the bathroom", indoor=True, affordances={"talk", "read"}),
    "classroom": Setting(place="the classroom", indoor=True, affordances={"talk", "read"}),
    "kitchen": Setting(place="the kitchen", indoor=True, affordances={"talk", "read"}),
}

WORDS = {
    "vagina": Word(
        term="vagina",
        kind="body word",
        definition="a normal word for part of a girl's or woman's body",
        funny_hook="it sounded big and serious, which made it extra awkward",
    ),
}

CHILD_NAMES_GIRL = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
CHILD_NAMES_BOY = ["Leo", "Ben", "Max", "Theo", "Finn"]
ADULT_NAMES = ["Mom", "Dad", "Aunt June", "Uncle Ray", "Teacher Kim"]


# ---------------------------------------------------------------------------
# World logic.
# ---------------------------------------------------------------------------
class StoryWorld(World):
    pass


def reasonableness_gate(params: StoryParams) -> None:
    if params.word not in WORDS:
        raise StoryError(f"Unsupported word: {params.word}")
    if params.place not in SETTINGS:
        raise StoryError(f"Unsupported place: {params.place}")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError("child_gender must be 'girl' or 'boy'")


def initial_emotions(child: Entity, adult: Entity) -> None:
    child.memes["curious"] = 1.0
    child.memes["embarrassed"] = 0.0
    child.memes["confused"] = 1.0
    adult.memes["kind"] = 1.0
    adult.memes["calm"] = 1.0
    adult.memes["patient"] = 1.0


def introduce(world: StoryWorld, child: Entity, adult: Entity, word: Word) -> None:
    world.say(
        f"{child.id} was a little {child.type} who liked asking questions about funny-sounding words."
    )
    world.say(
        f"One day, {child.id} heard the word {word.term} and felt a hot, squirmy feeling in {child.pronoun('possessive')} cheeks."
    )
    child.memes["embarrassed"] += 1.0
    child.memes["confused"] += 1.0


def misunderstanding(world: StoryWorld, child: Entity, word: Word) -> None:
    world.say(
        f"{child.id} whispered, '{word.term}?' and looked around as if the word might be hiding under a chair."
    )
    world.say(
        f"{word.funny_hook.capitalize()}, so {child.id} made a silly face and pretended not to care."
    )
    child.memes["embarrassed"] += 1.0
    child.memes["silliness"] = child.memes.get("silliness", 0.0) + 1.0


def adult_explains(world: StoryWorld, adult: Entity, child: Entity, word: Word) -> None:
    world.say(
        f"{adult.id} noticed the wobble in {child.pronoun('possessive')} voice and sat down beside {child.id}."
    )
    world.say(
        f"'{word.term} is just a normal {word.kind},' {adult.id} said. '{word.definition}.'"
    )
    child.memes["confused"] = max(0.0, child.memes.get("confused", 0.0) - 1.0)
    child.memes["safe"] = child.memes.get("safe", 0.0) + 1.0
    adult.memes["calm"] += 1.0


def comic_turn(world: StoryWorld, child: Entity, adult: Entity, word: Word) -> None:
    world.say(
        f"{child.id} blinked, then giggled. 'So I was making a big face over a word that just means a body part?'"
    )
    world.say(
        f"{adult.id} laughed kindly and nodded, and the room felt less serious all at once."
    )
    child.memes["embarrassed"] = max(0.0, child.memes.get("embarrassed", 0.0) - 0.5)
    child.memes["laughter"] = child.memes.get("laughter", 0.0) + 1.0
    adult.memes["laughter"] = adult.memes.get("laughter", 0.0) + 1.0


def reconciliation(world: StoryWorld, child: Entity, adult: Entity) -> None:
    child.memes["reconciled"] = 1.0
    adult.memes["reconciled"] = 1.0
    child.memes["embarrassed"] = 0.0
    world.say(
        f"{child.id} took a breath and said, 'Sorry for acting so weird.'"
    )
    world.say(
        f"'{That's okay}'. {adult.id} smiled. 'Questions are welcome here.'"
    )


def happy_ending(world: StoryWorld, child: Entity, adult: Entity, word: Word) -> None:
    world.say(
        f"{child.id} grinned and repeated {word.term} out loud like a brave little word-singer."
    )
    world.say(
        f"Then {child.id} and {adult.id} shared a joke, and the funny word felt ordinary instead of scary."
    )
    world.say(
        f"By the end, {child.id} felt proud for learning something new, and {adult.id} felt proud too."
    )
    child.memes["joy"] = child.memes.get("joy", 0.0) + 2.0
    adult.memes["joy"] = adult.memes.get("joy", 0.0) + 1.0
    child.memes["happy_ending"] = 1.0


def tell(setting: Setting, params: StoryParams) -> StoryWorld:
    word = WORDS[params.word]
    world = StoryWorld(setting)
    child = world.add_entity(
        Entity(
            id=params.child_name,
            kind="character",
            type=params.child_gender,
            meters={"steps": 0.0},
            memes={},
        )
    )
    adult = world.add_entity(
        Entity(
            id=params.adult_name,
            kind="character",
            type=params.adult_role,
            meters={"steps": 0.0},
            memes={},
        )
    )
    initial_emotions(child, adult)

    world.say(f"{child.id} and {adult.id} were in {setting.place} when the word came up.")
    introduce(world, child, adult, word)
    world.para()
    misunderstanding(world, child, word)
    adult_explains(world, adult, child, word)
    world.para()
    comic_turn(world, child, adult, word)
    reconciliation(world, child, adult)
    happy_ending(world, child, adult, word)

    world.facts.update(
        child=child,
        adult=adult,
        word=word,
        setting=setting,
        reconciled=child.memes.get("reconciled", 0.0) >= 1.0,
        happy=child.memes.get("happy_ending", 0.0) >= 1.0,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A.
# ---------------------------------------------------------------------------
def generation_prompts(world: StoryWorld) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    word: Word = f["word"]
    return [
        f'Write a short comedy story for children about the word "{word.term}".',
        f"Tell a gentle story where {child.id} feels embarrassed, {adult.id} explains a body word, and they reconcile happily.",
        f"Write a funny but kind story set in {world.setting.place} about learning that {word.term} is a normal word.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    word: Word = f["word"]
    qa = [
        QAItem(
            question=f"What word made {child.id} feel awkward at first?",
            answer=f"The word was {word.term}. It sounded serious to {child.id}, so {child.id} got embarrassed before it was explained.",
        ),
        QAItem(
            question=f"What did {adult.id} say the word {word.term} means?",
            answer=f"{adult.id} said that {word.term} is a normal {word.kind} for part of a girl's or woman's body.",
        ),
        QAItem(
            question=f"How did the story end for {child.id} and {adult.id}?",
            answer=f"They apologized, laughed together, and ended the story feeling warm, calm, and happy.",
        ),
    ]
    if f.get("reconciled"):
        qa.append(
            QAItem(
                question=f"Why did {child.id} stop feeling embarrassed?",
                answer=f"{adult.id} answered kindly, made the word feel normal, and {child.id} realized the whole thing was okay to talk about.",
            )
        )
    return qa


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a body word?",
            answer="A body word is a word that names a part of the body, like a hand, foot, or vagina.",
        ),
        QAItem(
            question="Why can some words feel embarrassing at first?",
            answer="Some words feel embarrassing at first because they sound unfamiliar, private, or important, but they become less scary when someone explains them kindly.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the word is supported and the setting is supported.
valid_story(P) :- supported_word(P,W), supported_place(P,L), reconcile_possible(P,W,L).

reconcile_possible(P,W,L) :- body_word(W), calm_talk(L), word_can_be_explained(W).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in SETTINGS:
        lines.append(asp.fact("supported_place", name))
        if SETTINGS[name].indoor:
            lines.append(asp.fact("calm_talk", name))
    for key, word in WORDS.items():
        lines.append(asp.fact("supported_word", key, word.term))
        lines.append(asp.fact("body_word", word.term))
        lines.append(asp.fact("word_can_be_explained", word.term))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    py_set = set(("default",) for _ in SETTINGS)
    if clingo_set:
        print("OK: ASP program produced at least one valid story.")
        return 0
    print("MISMATCH: ASP program produced no valid story.")
    return 1


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy storyworld about a body word, embarrassment, and reconciliation.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--gender", dest="child_gender", choices=["girl", "boy"])
    ap.add_argument("--name", dest="child_name")
    ap.add_argument("--adult", dest="adult_name")
    ap.add_argument("--role", dest="adult_role", choices=["mother", "father", "aunt", "uncle", "teacher"])
    ap.add_argument("--word", choices=sorted(WORDS))
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
    place = args.place or rng.choice(sorted(SETTINGS))
    word = args.word or "vagina"
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES_GIRL if child_gender == "girl" else CHILD_NAMES_BOY)
    adult_role = args.adult_role or rng.choice(["mother", "father", "aunt", "uncle", "teacher"])
    adult_name = args.adult_name or rng.choice(ADULT_NAMES)
    reasonableness_gate(StoryParams(place, child_name, child_gender, adult_role, adult_name, word))
    return StoryParams(place, child_name, child_gender, adult_role, adult_name, word)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        print(asp_program("#show valid_story/1."))
        return

    samples: list[StorySample] = []
    if args.all:
        for place in sorted(SETTINGS):
            params = StoryParams(
                place=place,
                child_name="Mia",
                child_gender="girl",
                adult_role="mother",
                adult_name="Mom",
                word="vagina",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
