#!/usr/bin/env python3
"""
A standalone storyworld for a small whodunit about curiosity, blame, and a
reconciliation that reveals a moral value.

Premise:
- A child notices something missing from a bin.
- Curiosity drives a careful search.
- Suspicion briefly falls on the wrong person.
- The true cause turns out to be ordinary, not sinister.
- The ending restores trust and shows a moral value: honesty over hasty blame.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    id: str
    type: str
    label: str
    age_word: str = "young"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = True


@dataclass
class ObjectItem:
    id: str
    label: str
    owner: Optional[str] = None
    hidden_in: Optional[str] = None
    found: bool = False
    damaged: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Character | ObjectItem] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    suspect: str
    suspect_type: str
    bin_item: str
    seed: Optional[int] = None


PLACES = {
    "hallway": Setting(place="the hallway"),
    "classroom": Setting(place="the classroom"),
    "library": Setting(place="the library"),
    "kitchen": Setting(place="the kitchen"),
}

HEROES = [
    ("Mina", "girl"),
    ("Eli", "boy"),
    ("Nora", "girl"),
    ("Toby", "boy"),
]

HELPERS = [
    ("Ms. Reed", "woman"),
    ("Mr. Cole", "man"),
]

SUSPECTS = [
    ("Jules", "girl"),
    ("Finn", "boy"),
]

BIN_ITEMS = [
    "toy train",
    "red marker",
    "glitter pencil",
    "cookie tin key",
    "paper star",
]

KNOWLEDGE = {
    "bin": [("What is a bin?", "A bin is a container that holds things together in one place.")],
    "curiosity": [("What does curiosity mean?", "Curiosity means wanting to look, ask, and learn more about something.")],
    "reconciliation": [("What is reconciliation?", "Reconciliation is when people make up after a mistake or a misunderstanding.")],
    "honesty": [("Why is honesty important?", "Honesty helps people tell the truth, trust each other, and fix problems sooner.")],
    "moral": [("What is a moral value?", "A moral value is an important idea about how to treat other people well, like honesty or kindness.")],
}


ASP_RULES = r"""
#show valid/4.
place(hallway). place(classroom). place(library). place(kitchen).
hero(mina). hero(eli). hero(nora). hero(toby).
helper(ms_reed). helper(mr_cole).
suspect(jules). suspect(finn).
item(toy_train). item(red_marker). item(glitter_pencil). item(cookie_tin_key). item(paper_star).

curious(H) :- hero(H).
can_misplace(I) :- item(I).
reconciles(H, S) :- hero(H), suspect(S).
moral_value(honesty).

valid(P,H,He,S) :- place(P), hero(H), helper(He), suspect(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for h, _ in HEROES:
        lines.append(asp.fact("hero", h.lower()))
    for h, _ in HELPERS:
        lines.append(asp.fact("helper", h.lower().replace(". ", "_").replace(" ", "_")))
    for s, _ in SUSPECTS:
        lines.append(asp.fact("suspect", s.lower()))
    for item in BIN_ITEMS:
        lines.append(asp.fact("item", item.lower().replace(" ", "_")))
    lines.append(asp.fact("moral_value", "honesty"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for hero, _ in HEROES:
            for helper, _ in HELPERS:
                for suspect, _ in SUSPECTS:
                    combos.append((place, hero, helper, suspect))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with bin, curiosity, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--suspect")
    ap.add_argument("--bin-item", choices=BIN_ITEMS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    hero, hero_type = rng.choice(HEROES)
    helper, helper_type = rng.choice(HELPERS)
    suspect, suspect_type = rng.choice(SUSPECTS)
    bin_item = args.bin_item or rng.choice(BIN_ITEMS)
    if args.hero:
        hero = args.hero
    if args.helper:
        helper = args.helper
    if args.suspect:
        suspect = args.suspect
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    return StoryParams(place=place, hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type, suspect=suspect, suspect_type=suspect_type, bin_item=bin_item)


def generate(params: StoryParams) -> StorySample:
    setting = PLACES[params.place]
    world = World(setting=setting)
    hero = world.add(Character(id=params.hero, type=params.hero_type, label=params.hero))
    helper = world.add(Character(id=params.helper, type=params.helper_type, label=params.helper))
    suspect = world.add(Character(id=params.suspect, type=params.suspect_type, label=params.suspect))
    item = world.add(ObjectItem(id="item", label=params.bin_item, owner=suspect.id, hidden_in="bin", found=False))

    hero.memes["curiosity"] = 1.0
    helper.memes["calm"] = 1.0
    suspect.memes["worry"] = 0.4

    world.say(f"{hero.id} noticed that the bin in {setting.place} looked wrong.")
    world.say(f"The lid was crooked, and one thing was missing: the {item.label}.")
    world.say(f"{hero.pronoun().capitalize()} felt curiosity tug hard and began to ask careful questions.")

    world.para()
    world.say(f"{hero.id} looked under the table, behind the chairs, and inside the bin again.")
    world.say(f"For a moment, {hero.pronoun('object')} wondered if {suspect.id} had taken it.")
    world.say(f"But {helper.id} told {hero.pronoun('object')} not to jump to blame without proof.")

    world.para()
    world.say(f"Together, they checked a narrow shelf by the window.")
    item.found = True
    item.hidden_in = "shelf"
    world.say(f"There it was: the {item.label}, tucked where it had fallen and rolled out of sight.")
    world.say(f"{suspect.id} had not stolen anything at all.")

    world.para()
    world.say(f"{hero.id} apologized to {suspect.id}, and {suspect.id} smiled and accepted the apology.")
    world.say(f"The three of them put the {item.label} back in the bin, this time with care.")
    world.say(f"{helper.id} said the best clue was honesty, because honest questions can solve a mystery without hurting a friend.")

    world.facts.update(
        hero=hero,
        helper=helper,
        suspect=suspect,
        item=item,
        place=params.place,
        setting=setting,
        moral_value="honesty",
        curiosity=True,
        reconciliation=True,
    )

    prompts = [
        f"Write a short whodunit for a child about a missing object in a bin at {setting.place}.",
        f"Tell a gentle mystery story where {hero.id} uses curiosity before making a guess.",
        f"Write a story about a bin, a mistaken suspicion, and a reconciliation that shows honesty matters.",
    ]

    story_qa = [
        QAItem(
            question=f"What was missing from the bin in {setting.place}?",
            answer=f"The {item.label} was missing from the bin in {setting.place}.",
        ),
        QAItem(
            question=f"Why did {hero.id} think something was wrong?",
            answer=f"{hero.id} noticed the bin looked crooked and saw that the {item.label} was gone, so curiosity made {hero.pronoun('object')} start looking carefully.",
        ),
        QAItem(
            question=f"Why did {hero.id} stop blaming {suspect.id}?",
            answer=f"{helper.id} reminded {hero.id} to check for proof first, and the missing {item.label} was found stuck on a shelf instead of being taken by {suspect.id}.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {suspect.id}?",
            answer=f"{hero.id} apologized, {suspect.id} accepted the apology, and they put the {item.label} back in the bin together.",
        ),
        QAItem(
            question="What moral value did the helper talk about?",
            answer="The helper talked about honesty, saying it helps solve problems without unfair blame.",
        ),
    ]

    world_qa = [
        QAItem(*KNOWLEDGE["bin"][0]),
        QAItem(*KNOWLEDGE["curiosity"][0]),
        QAItem(*KNOWLEDGE["reconciliation"][0]),
        QAItem(*KNOWLEDGE["honesty"][0]),
        QAItem(*KNOWLEDGE["moral"][0]),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        if isinstance(e, Character):
            bits = []
            if e.memes:
                bits.append(f"memes={e.memes}")
            if e.meters:
                bits.append(f"meters={e.meters}")
            lines.append(f"{e.id}: character {e.type} {' '.join(bits)}")
        else:
            lines.append(f"{e.id}: item label={e.label} hidden_in={e.hidden_in} found={e.found}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: the requested options do not make a reasonable whodunit.)"


def asp_verify() -> int:
    import asp
    a = set(asp_valid())
    b = set(valid_combos())
    if a == b:
        print(f"OK: ASP matches Python ({len(a)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    if a - b:
        print("Only in ASP:", sorted(a - b))
    if b - a:
        print("Only in Python:", sorted(b - a))
    return 1


def asp_valid_combos() -> list[tuple]:
    return asp_valid()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} valid combinations:")
        for row in vals:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="library", hero="Mina", hero_type="girl", helper="Ms. Reed", helper_type="woman", suspect="Jules", suspect_type="girl", bin_item="cookie tin key"),
            StoryParams(place="classroom", hero="Eli", hero_type="boy", helper="Mr. Cole", helper_type="man", suspect="Finn", suspect_type="boy", bin_item="red marker"),
        ]
        for p in curated:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
