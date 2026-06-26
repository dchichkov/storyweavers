#!/usr/bin/env python3
"""
storyworlds/worlds/sunburned_fender_bad_ending_whodunit.py
===========================================================

A small whodunit storyworld with a bad ending: someone dented the car's fender,
a child detective follows clues, and the case ends unresolved under a hot sun.
The story stays state-driven, but the ending is deliberately disappointing.

Seed image:
- A bright afternoon.
- A sunburned kid detective.
- A damaged fender.
- Clues that point in more than one direction.
- A bad ending where the truth is not cleanly solved.

This world is intentionally compact: one mystery premise, a few suspect sources,
and a final twist that leaves the detective sunburned, wrong-footed, and no
closer to a tidy answer.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad", "son"}
        female = {"girl", "woman", "mother", "mom", "daughter"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    sunlight: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    clue: str
    motive: str
    alibi: str
    makes_trace: str
    plausible: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "driveway": Setting(place="the driveway", sunlight="bright"),
    "street": Setting(place="the street", sunlight="blazing"),
    "garage": Setting(place="the garage", sunlight="thin"),
}

SUSPECTS = {
    "bike": Suspect(
        id="bike",
        label="the blue bike",
        type="bike",
        clue="a blue paint scratch",
        motive="it had brushed too close in a hurry",
        alibi="the bike was leaned up all morning",
        makes_trace="a curved tire mark",
        plausible=True,
    ),
    "basketball": Suspect(
        id="basketball",
        label="the red basketball",
        type="ball",
        clue="a red rubber scuff",
        motive="it had bounced wild in the heat",
        alibi="the ball was in the side yard later",
        makes_trace="a round rubber smear",
        plausible=True,
    ),
    "mail_truck": Suspect(
        id="mail_truck",
        label="the mail truck",
        type="truck",
        clue="a white dust streak",
        motive="it had backed up too close",
        alibi="the driver waved from down the block",
        makes_trace="a straight pale scrape",
        plausible=True,
    ),
    "wind": Suspect(
        id="wind",
        label="the hot wind",
        type="weather",
        clue="dust in the crack",
        motive="it had blown grit against the car",
        alibi="the wind cannot own a fender dent",
        makes_trace="a bit of grit",
        plausible=False,
    ),
}

GIRL_NAMES = ["Mina", "Lila", "June", "Nora", "Tess", "Ivy"]
BOY_NAMES = ["Owen", "Finn", "Eli", "Noah", "Milo", "Jude"]
TRAITS = ["sharp", "curious", "careful", "persistent", "quiet", "brave"]


@dataclass
class StoryParams:
    place: str
    suspect: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny whodunit storyworld with a bad ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    choices = list(valid_combos())
    if args.place:
        choices = [c for c in choices if c[0] == args.place]
    if args.suspect:
        choices = [c for c in choices if c[1] == args.suspect]
    if not choices:
        raise StoryError("(No valid mystery matches the given options.)")
    place, suspect = rng.choice(sorted(choices))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError("Invalid gender.")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, suspect=suspect, name=name, gender=gender, trait=trait)


def valid_combos() -> list[tuple[str, str]]:
    return [(p, s) for p in SETTINGS for s in SUSPECTS]


ASP_RULES = r"""
suspect(P,S) :- place(P), culprit(S).
valid(P,S) :- suspect(P,S), has_clue(S), has_burn(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("culprit", sid))
        lines.append(asp.fact("has_clue", sid))
        if s.plausible:
            lines.append(asp.fact("has_burn", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def world_detail(setting: Setting) -> str:
    return f"{setting.place.capitalize()} sat under {setting.sunlight} sun."


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    suspect = SUSPECTS[params.suspect]
    fender = world.add(Entity(
        id="fender",
        kind="thing",
        type="car_part",
        label="fender",
        phrase="the front fender",
        owner="car",
    ))
    world.facts.update(hero=hero, suspect=suspect, fender=fender, params=params)

    hero.memes["curiosity"] = 1.0
    hero.meters["sun"] = 0.0
    hero.meters["dust"] = 0.0
    fender.meters["dented"] = 1.0
    fender.meters["scratched"] = 0.6
    return world


def investigate(world: World) -> None:
    hero: Entity = world.facts["hero"]
    suspect: Suspect = world.facts["suspect"]
    fender: Entity = world.facts["fender"]

    world.say(
        f"On {world.setting.place}, {hero.id} noticed the car's {fender.label} had a fresh dent."
    )
    world.say(
        f'{hero.id} was the sort of {hero.type} who liked a puzzle, so {hero.pronoun()} crouched '
        f'low and studied the shine around the dent.'
    )

    world.para()
    hero.memes["focus"] = 1.0
    hero.meters["sun"] += 1.0
    world.say(
        f"{hero.id} followed a little clue: {suspect.clue}. "
        f"That looked honest for a moment, and then another clue tugged the other way."
    )
    hero.meters["sun"] += 1.0
    hero.meters["sunburned"] = 1.0
    hero.meters["thirst"] = 1.0
    world.say(
        f"The sun kept climbing, and by the time {hero.id} checked the curb again, "
        f"{hero.pronoun('subject')} was sunburned and thirsty."
    )

    world.para()
    if suspect.id == "wind":
        world.say(
            f"{hero.id} tried to blame the hot wind, but the wind's alibi was too strange: "
            f"it left dust, not a tidy dent."
        )
        world.say(
            f"Still, {hero.id} had no better answer, so the case began to feel slippery."
        )
        world.facts["wrong_guess"] = True
    else:
        world.say(
            f"{hero.id} found {suspect.label} near the block and thought the case was solved."
        )
        world.say(
            f"But {suspect.alibi} sounded neat enough to make the answer wobble."
        )
        world.facts["wrong_guess"] = True

    world.para()
    hero.memes["frustration"] = 1.0
    world.say(
        f"At last {hero.id} pointed at the suspect and announced the guess with a firm voice."
    )
    world.say(
        f"Nobody could prove it. The truth stayed hidden, and the dent stayed in the {fender.label}."
    )
    fender.meters["fixed"] = 0.0
    world.facts["bad_ending"] = True
    world.facts["resolved"] = False
    world.facts["sunburned"] = True


def tell(params: StoryParams) -> World:
    world = build_world(params)
    investigate(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    suspect: Suspect = world.facts["suspect"]
    return [
        f'Write a short whodunit for a young child about a dented fender and a clue on {world.setting.place}.',
        f"Tell a mystery where {p.name} notices a damaged fender, follows {suspect.clue}, and gets sunburned while investigating.",
        f"Write a bad-ending detective story in which a child tries to solve who dented the fender but never quite gets the answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    suspect: Suspect = world.facts["suspect"]
    return [
        QAItem(
            question=f"What did {hero.id} notice first on {world.setting.place}?",
            answer=f"{hero.id} noticed that the car's fender had a fresh dent.",
        ),
        QAItem(
            question=f"What clue did {hero.id} follow during the mystery?",
            answer=f"{hero.id} followed the clue about {suspect.clue}.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"It ended badly: {hero.id} got sunburned, and the dent in the fender was never solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fender?",
            answer="A fender is a car part near the wheel that can get dented or scratched.",
        ),
        QAItem(
            question="What does sunburn mean?",
            answer="Sunburn means your skin gets red and sore after too much sun.",
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where readers try to figure out who did the bad thing.",
        ),
    ]


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(place="driveway", suspect="bike", name="Mina", gender="girl", trait="curious"),
    StoryParams(place="street", suspect="basketball", name="Owen", gender="boy", trait="persistent"),
    StoryParams(place="garage", suspect="mail_truck", name="Lila", gender="girl", trait="careful"),
    StoryParams(place="driveway", suspect="wind", name="Finn", gender="boy", trait="sharp"),
]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, suspect in combos:
            print(f"  {place:9} {suspect:12}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.suspect} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
