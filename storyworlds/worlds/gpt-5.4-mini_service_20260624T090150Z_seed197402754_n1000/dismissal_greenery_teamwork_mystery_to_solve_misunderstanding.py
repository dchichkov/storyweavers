#!/usr/bin/env python3
"""
A small bedtime-story world about a child, a little mystery, a misunderstanding,
and the teamwork that solves it in a garden full of greenery.

The child-facing premise:
- A small group is caring for a patch of greenery.
- Someone thinks they have been dismissed from the job.
- That misunderstanding makes the work go lopsided.
- The group searches for the truth, solves the mystery, and restores trust.
- Teamwork turns worry into a gentle ending image.

This file is a self-contained Storyweavers storyworld.
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


@dataclass
class Character:
    name: str
    role: str
    pronoun_subject: str
    pronoun_object: str
    pronoun_possessive: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def subject(self) -> str:
        return self.pronoun_subject

    def object(self) -> str:
        return self.pronoun_object

    def possessive(self) -> str:
        return self.pronoun_possessive


@dataclass
class Place:
    name: str
    greenery: str
    detail: str
    night_detail: str


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    caretaker: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.characters: dict[str, Character] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, character: Character) -> Character:
        self.characters[character.name] = character
        return character

    def get(self, name: str) -> Character:
        return self.characters[name]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World(self.place)
        other.characters = {
            n: Character(
                name=c.name,
                role=c.role,
                pronoun_subject=c.pronoun_subject,
                pronoun_object=c.pronoun_object,
                pronoun_possessive=c.pronoun_possessive,
                meters=dict(c.meters),
                memes=dict(c.memes),
            )
            for n, c in self.characters.items()
        }
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        return other


PLACES = {
    "garden": Place(
        name="the garden",
        greenery="the soft greenery",
        detail="The leaves were glossy, and the little paths were quiet under the moon.",
        night_detail="At night, the garden looked like a sleepy quilt of leaves and stems.",
    ),
    "courtyard": Place(
        name="the courtyard",
        greenery="the climbing vines",
        detail="The vines leaned over the fence, and the little pots waited in a neat row.",
        night_detail="At night, the courtyard held a hush around its pots and vines.",
    ),
    "greenhouse": Place(
        name="the greenhouse",
        greenery="the bright seedlings",
        detail="The glass walls kept the air warm, and every leaf looked pleased to be there.",
        night_detail="At night, the greenhouse glowed softly, like a lantern for plants.",
    ),
}

NAMES = ["Mina", "Toby", "Lina", "Noah", "Iris", "Ari", "Maya", "Finn"]
ROLES = ["girl", "boy"]
TASKS = {
    "watering": "water the greenery",
    "weeding": "pull the weeds",
    "trimming": "trim the stems",
}


def make_char(name: str, role: str) -> Character:
    if role == "girl":
        return Character(name=name, role=role, pronoun_subject="she", pronoun_object="her", pronoun_possessive="her")
    return Character(name=name, role=role, pronoun_subject="he", pronoun_object="him", pronoun_possessive="his")


def bedtime_opening(world: World) -> None:
    world.say(f"{world.place.name.capitalize()} was full of {world.place.greenery}, and everything looked ready for a kind little evening job.")
    world.say(world.place.detail)


def story_turn(world: World, hero: Character, helper: Character, caretaker: Character, task: str) -> None:
    hero.memes["eager"] = 1
    helper.memes["eager"] = 1
    caretaker.memes["watchful"] = 1
    world.say(f"{hero.name} and {helper.name} wanted to {task} together, because teamwork made the job feel light.")
    world.say(f"But then a small misunderstanding slipped in: {caretaker.name} thought {hero.name} had been dismissed from the work for the evening.")
    world.say(f"{hero.name} felt a little hurt and stood very still beside the pots, as if the moon had gone dim for a moment.")
    world.facts["misunderstanding"] = True
    world.facts["dismissal"] = True


def solve_mystery(world: World, hero: Character, helper: Character, caretaker: Character, task: str) -> None:
    world.para()
    world.say(f"{helper.name} noticed a stray note under a watering can and read it out loud.")
    world.say(f"It was not a dismissal after all. It was a reminder list, and one line had been smudged by a wet thumb.")
    world.say(f"{caretaker.name} blinked, then smiled with relief. The mystery to solve was simply a muddled message.")
    world.say(f"{hero.name} felt the hurt ease away, because nobody wanted to send {hero.object()} away.")
    world.say(f"With the misunderstanding fixed, the three of them worked side by side, and the little job became easy again.")
    world.say(f"They finished by sharing the tools, straightening the pots, and {task} until the greenery looked tidy and cared for.")
    world.facts["misunderstanding"] = False
    world.facts["dismissal"] = False
    world.facts["solved"] = True
    hero.memes["relief"] = 1
    hero.memes["trust"] = 1
    helper.memes["pride"] = 1
    caretaker.memes["relief"] = 1


def closing_image(world: World, hero: Character, helper: Character, caretaker: Character) -> None:
    world.para()
    world.say(f"At the end of the bedtime hour, {world.place.night_detail}")
    world.say(f"{hero.name}, {helper.name}, and {caretaker.name} stood together beside the sleeping plants.")
    world.say(f"The garden stayed green, the little worry was gone, and teamwork had turned the whole evening gentle again.")


def tell_story(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    rng = random.Random(params.seed)
    world = World(PLACES[params.place])

    hero_role = rng.choice(ROLES)
    helper_role = "girl" if hero_role == "boy" else "boy"

    hero = world.add(make_char(params.hero, hero_role))
    helper = world.add(make_char(params.helper, helper_role))
    caretaker = world.add(make_char(params.caretaker, rng.choice(ROLES)))

    task = rng.choice(list(TASKS.values()))
    world.facts.update(
        place=world.place.name,
        hero=hero,
        helper=helper,
        caretaker=caretaker,
        task=task,
    )

    bedtime_opening(world)
    world.para()
    story_turn(world, hero, helper, caretaker, task)
    solve_mystery(world, hero, helper, caretaker, task)
    closing_image(world, hero, helper, caretaker)
    return world


def story_qa(world: World) -> list[QAItem]:
    hero: Character = world.facts["hero"]  # type: ignore[assignment]
    helper: Character = world.facts["helper"]  # type: ignore[assignment]
    caretaker: Character = world.facts["caretaker"]  # type: ignore[assignment]
    task: str = world.facts["task"]  # type: ignore[assignment]
    place: str = world.facts["place"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Why did {hero.name} feel sad for a moment in {place}?",
            answer=f"{caretaker.name} thought {hero.name} had been dismissed from the work, but that was a misunderstanding.",
        ),
        QAItem(
            question=f"What helped solve the mystery about the note in {place}?",
            answer=f"{helper.name} read the smudged note out loud, and the group saw that it was only a reminder list, not a dismissal.",
        ),
        QAItem(
            question=f"What did the friends do together after the misunderstanding was fixed?",
            answer=f"They worked side by side to {task} and tidy the greenery, so the place looked cared for and calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is greenery?",
            answer="Greenery means lots of green plants and leaves, like grass, vines, or little seedlings.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together instead of all by themselves.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing for a little while.",
        ),
        QAItem(
            question="What does it mean to be dismissed?",
            answer="To be dismissed means to be told you do not need to stay or keep doing a job for now.",
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a little puzzle where people look for clues to find out what is really going on.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    place: str = world.facts["place"]  # type: ignore[assignment]
    hero: Character = world.facts["hero"]  # type: ignore[assignment]
    helper: Character = world.facts["helper"]  # type: ignore[assignment]
    caretaker: Character = world.facts["caretaker"]  # type: ignore[assignment]
    task: str = world.facts["task"]  # type: ignore[assignment]
    return [
        f"Write a bedtime story set in {place} with greenery, teamwork, a misunderstanding, and a mystery to solve.",
        f"Tell a gentle story where {hero.name} and {helper.name} help {caretaker.name} and discover that nobody was truly dismissed.",
        f"Write a child-friendly story about a small garden mystery where friends work together to {task} and make things right.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for c in world.characters.values():
        meters = {k: v for k, v in c.meters.items() if v}
        memes = {k: v for k, v in c.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {c.name:8} ({c.role:3}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
place(garden).
place(courtyard).
place(greenhouse).

greenery(garden, plants).
greenery(courtyard, vines).
greenery(greenhouse, seedlings).

theme(teamwork).
theme(misunderstanding).
theme(mystery_to_solve).

dismissal_possible(garden).
dismissal_possible(courtyard).
dismissal_possible(greenhouse).

mystery_solved(P) :- place(P), greenery(P,_), dismissal_possible(P), theme(teamwork), theme(misunderstanding), theme(mystery_to_solve).
#show mystery_solved/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import
    lines = []
    for name in PLACES:
        lines.append(asp.fact("place", name))
    for name, place in PLACES.items():
        lines.append(asp.fact("greenery", name, place.greenery))
    lines.append(asp.fact("theme", "teamwork"))
    lines.append(asp.fact("theme", "misunderstanding"))
    lines.append(asp.fact("theme", "mystery_to_solve"))
    for name in PLACES:
        lines.append(asp.fact("dismissal_possible", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import storyworlds.asp as asp  # lazy import
    model = asp.one_model(asp_program("#show mystery_solved/1."))
    return sorted(set(asp.atoms(model, "mystery_solved")))


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if not params.hero or not params.helper or not params.caretaker:
        raise StoryError("Hero, helper, and caretaker names must be provided or resolvable.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: dismissal, greenery, teamwork, and a mystery to solve.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--caretaker")
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
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    caretaker = args.caretaker or rng.choice([n for n in NAMES if n not in {hero, helper}])
    return StoryParams(place=place, hero=hero, helper=helper, caretaker=caretaker, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
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


def valid_params() -> list[StoryParams]:
    out = []
    for place in PLACES:
        out.append(StoryParams(place=place, hero="Mina", helper="Toby", caretaker="Lina"))
    return out


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy import
    py = {p.place for p in valid_params()}
    cl = {t[0] for t in asp_valid_places()}
    if py == cl:
        print(f"OK: ASP parity matches Python gate ({len(py)} places).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python:", sorted(py))
    print("asp:", sorted(cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery_solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp  # lazy import
        model = asp.one_model(asp_program("#show mystery_solved/1."))
        print(sorted(set(asp.atoms(model, "mystery_solved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams(place=place, hero="Mina", helper="Toby", caretaker="Lina", seed=base_seed + i)
            for i, place in enumerate(PLACES)
        ]
        samples = [generate(p) for p in params_list]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
