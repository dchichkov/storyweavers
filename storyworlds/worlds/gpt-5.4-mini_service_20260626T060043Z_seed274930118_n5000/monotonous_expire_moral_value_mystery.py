#!/usr/bin/env python3
"""
storyworlds/worlds/monotonous_expire_moral_value_mystery.py
============================================================

A small mystery storyworld about a child investigator, a quiet place, and a
choice with moral value.

Seed premise:
- The days feel monotonous.
- A useful pass or note is about to expire.
- A missing object, a hush, and one honest choice turn the case.

The world is built to feel like a child-friendly mystery: a slow beginning,
small clues, a turn from suspicion to understanding, and an ending that proves
something changed.
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


MORAL_VALUE = "Moral Value"
SEED_WORDS = ("monotonous", "expire")


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "librarian"}
        male = {"boy", "man", "father", "guard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    light: str
    hush: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    focus: str
    clue: str
    suspect: str
    reveal: str
    turn: str
    moral_value: str
    keyword: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "archive": Setting(
        place="the old archive",
        light="dim lamp light",
        hush="monotonous silence",
        affords={"search", "read", "wait"},
    ),
    "hall": Setting(
        place="the school hall",
        light="soft afternoon light",
        hush="monotonous echo",
        affords={"search", "read", "wait"},
    ),
    "bookshop": Setting(
        place="the tiny bookshop",
        light="yellow shelf light",
        hush="monotonous hush",
        affords={"search", "read", "wait"},
    ),
}

MYSTERIES = {
    "expired_pass": Mystery(
        id="expired_pass",
        focus="a library pass",
        clue="the date stamp was almost expired",
        suspect="the clerk",
        reveal="the pass had to be renewed at the desk",
        turn="the child found the renewal card tucked behind a ledger",
        moral_value="honesty matters when a borrowed thing must be returned",
        keyword="expire",
    ),
    "missing_key": Mystery(
        id="missing_key",
        focus="a brass key",
        clue="a chalk line pointed to the wrong drawer",
        suspect="the janitor",
        reveal="the key had slipped under a rug by the reading chair",
        turn="the child noticed the tiny key-shaped dent in the dust",
        moral_value="telling the truth helps return what belongs to others",
        keyword="monotonous",
    ),
    "lost_note": Mystery(
        id="lost_note",
        focus="a folded note",
        clue="a pencil mark ended at the picture frame",
        suspect="the librarian",
        reveal="the note had blown into a storybook",
        turn="the child lifted the book and found the note hiding in plain sight",
        moral_value="kindness grows when someone helps before blaming",
        keyword="moral",
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Luna", "Ava", "Ivy", "Ruby", "Zoe"]
BOY_NAMES = ["Eli", "Noah", "Leo", "Milo", "Finn", "Owen", "Max"]
TRAITS = ["curious", "careful", "gentle", "brave", "patient", "quiet"]


def intro_line(setting: Setting, mystery: Mystery) -> str:
    return (
        f"In {setting.place}, the light was {setting.light}, and the air held a "
        f"{setting.hush}. That was where the strange case began: {mystery.focus} "
        f"was missing its answer."
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"curiosity": 0.0, "worry": 0.0, "relief": 0.0},
        memes={"trust": 0.0, "resolve": 0.0},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=params.adult,
        label="the grown-up",
        meters={"worry": 0.0, "patience": 0.0},
        memes={"care": 0.0},
    ))
    item = world.add(Entity(
        id="Item",
        type="thing",
        label=mystery.focus,
        phrase=mystery.focus,
        caretaker=adult.id,
        held_by=adult.id,
        meters={"clue": 0.0, "risk": 0.0, "found": 0.0},
    ))

    world.facts.update(hero=hero, adult=adult, item=item, mystery=mystery, setting=setting)

    world.say(intro_line(setting, mystery))
    world.say(
        f"{hero.id} liked the routine there even when it was monotonous. "
        f"{hero.pronoun().capitalize()} walked between the shelves and watched the same little dust motes "
        f"float in the same quiet air."
    )
    world.say(
        f"Then {hero.id} noticed something odd: {mystery.clue}. "
        f"{hero.pronoun().capitalize()} asked, 'What happened to {mystery.focus}?'"
    )

    world.para()
    hero.meters["curiosity"] += 1
    hero.memes["resolve"] += 1
    world.say(
        f"{hero.id} decided to look closer. {hero.pronoun().capitalize()} checked the desk, the rug, and "
        f"the shadowy corners where small things liked to hide."
    )
    world.say(
        f"The grown-up said the case had to be handled carefully because the borrowed {mystery.focus} would "
        f"{'expire' if mystery.keyword == 'expire' else 'go missing'} soon if nobody fixed the problem."
    )
    adult.meters["worry"] += 1

    world.para()
    world.say(
        f"For a while, nothing changed. The room stayed still, and the answer felt out of reach. "
        f"{hero.id} almost blamed {mystery.suspect}, but {hero.pronoun('possessive')} eyes kept returning to the dust."
    )
    hero.meters["worry"] += 1

    world.say(
        f"At last, {mystery.turn}. That tiny clue made the whole room make sense."
    )
    item.meters["found"] += 1
    hero.memes["trust"] += 1

    world.para()
    world.say(
        f"{hero.id} pointed to the hiding spot and told the truth about what {hero.pronoun('subject')} saw. "
        f"{mystery.reveal}."
    )
    world.say(
        f"The grown-up smiled with relief instead of suspicion. {mystery.suspect.capitalize()} was not in trouble; "
        f"the mystery had simply looked bigger than it was."
    )
    adult.memes["care"] += 1

    world.para()
    hero.meters["worry"] = max(0.0, hero.meters["worry"] - 1)
    hero.meters["relief"] += 1
    world.say(
        f"Together they fixed the problem, and {mystery.focus} was safe again. "
        f"That was the {MORAL_VALUE.lower()} of the case: {mystery.moral_value}."
    )
    world.say(
        f"By the end, the room still looked quiet and plain, but it did not feel empty anymore. "
        f"{hero.id} had solved a small mystery, and even the monotonous hush seemed kinder."
    )

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    setting = f["setting"]
    return [
        f'Write a short mystery for a child that takes place in {setting.place} and includes the word "{mystery.keyword}".',
        f"Tell a quiet detective story where {hero.id} notices a problem, follows a small clue, and learns a kind lesson.",
        f"Write a child-friendly mystery about {mystery.focus} with a gentle reveal and an ending that shows {MORAL_VALUE}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    adult: Entity = f["adult"]  # type: ignore[assignment]
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]

    qa = [
        QAItem(
            question=f"Where did {hero.id} notice the mystery?",
            answer=f"{hero.id} noticed it in {setting.place}, where the light was soft and the hush was monotonous.",
        ),
        QAItem(
            question=f"What was happening to {mystery.focus}?",
            answer=f"{mystery.focus.capitalize()} was in danger because it was about to {'expire' if mystery.keyword == 'expire' else 'be lost'} if nobody fixed the problem.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} solve the case?",
            answer=f"The clue was this: {mystery.clue}. That clue led {hero.id} toward the hidden answer.",
        ),
        QAItem(
            question=f"What did {hero.id} learn at the end?",
            answer=f"{hero.id} learned that {mystery.moral_value}. That was the moral value of the story.",
        ),
        QAItem(
            question=f"Who helped once the truth was found?",
            answer=f"The grown-up helped, and {mystery.suspect} was not the real problem after all.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a story about a puzzling problem that needs clues and careful thinking to solve.",
        ),
        QAItem(
            question="What does it mean for something to expire?",
            answer="If something expires, it reaches the end of the time it can be used, so it must be renewed or replaced.",
        ),
        QAItem(
            question="What does moral value mean?",
            answer="Moral value means the lesson about what is kind, honest, fair, or good to do.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("keyword", mid, mystery.keyword))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M) :- setting(S), mystery(M), affords(S, search), keyword(M, K), K = monotonous.
valid(S, M) :- setting(S), mystery(M), affords(S, search), keyword(M, K), K = expire.
valid(S, M) :- setting(S), mystery(M), affords(S, search), keyword(M, K), K = moral.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def reasonableness_gate(setting: str, mystery: str) -> bool:
    return setting in SETTINGS and mystery in MYSTERIES and "search" in SETTINGS[setting].affords


def asp_verify() -> int:
    py = {(s, m) for s in SETTINGS for m in MYSTERIES if reasonableness_gate(s, m)}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP parity matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print(" only in ASP:", sorted(cl - py))
    print(" only in Python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--adult", choices=["librarian", "guard", "mother", "father"])
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
    if args.setting and args.mystery and not reasonableness_gate(args.setting, args.mystery):
        raise StoryError("That setting and mystery do not make a workable story.")
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
    adult = args.adult or rng.choice(["librarian", "guard", "mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, adult=adult, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(setting="archive", mystery="expired_pass", name="Mia", gender="girl", adult="librarian", trait="curious"),
    StoryParams(setting="hall", mystery="missing_key", name="Eli", gender="boy", adult="guard", trait="patient"),
    StoryParams(setting="bookshop", mystery="lost_note", name="Nora", gender="girl", adult="mother", trait="quiet"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} valid setting/mystery pairs:\n")
        for s, m in triples:
            print(f"  {s:8} {m}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.setting} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
