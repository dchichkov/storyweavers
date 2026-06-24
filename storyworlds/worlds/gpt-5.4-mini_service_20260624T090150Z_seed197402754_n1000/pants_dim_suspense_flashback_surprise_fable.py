#!/usr/bin/env python3
"""
storyworlds/worlds/pants_dim_suspense_flashback_surprise_fable.py
=================================================================

A small fable-style storyworld about a child-sized problem with pants that are
too small, a worried helper, a remembered past, and a surprise fix.

Seed tale sketch:
---
A little fox named Pip was proud of a pair of striped pants that his grandma
had sewn for him. One day, Pip tried to climb a big pear tree, but the pants
felt too tight, and he worried they might rip. He remembered how his grandma
had once patched his coat when it tore. At the end, his grandma surprised him
by turning the pants into short play pants, and Pip could climb happily.

This world models:
- physical size and fit of clothing
- emotional suspense, memory, surprise, relief
- a fable-like lesson about patience and practical kindness
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "fox": {"subject": "he", "object": "him", "possessive": "his"},
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "mother": {"subject": "she", "object": "her", "possessive": "her"},
            "grandmother": {"subject": "she", "object": "her", "possessive": "her"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the pear orchard"
    time: str = "golden afternoon"


@dataclass
class Challenge:
    id: str
    action: str
    later_action: str
    risk: str
    suit: str
    flashback: str
    keyword: str = "pants-dim"


@dataclass
class Repair:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    fits: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
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


@dataclass
class StoryParams:
    place: str
    challenge: str
    repair: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "orchard": Setting(place="the pear orchard", time="golden afternoon"),
    "hill": Setting(place="the windy hill", time="bright morning"),
    "garden": Setting(place="the garden gate", time="late afternoon"),
}

CHALLENGES = {
    "tree": Challenge(
        id="tree",
        action="climb the pear tree",
        later_action="reach the pears",
        risk="the pants might split",
        suit="too small",
        flashback="He remembered how his helper had once mended his scarf with steady hands.",
        keyword="pants-dim",
    ),
    "fence": Challenge(
        id="fence",
        action="jump the garden fence",
        later_action="land on the other side",
        risk="the pants might pinch and tear",
        suit="too tight",
        flashback="She remembered a winter day when a torn sleeve was neatly patched up.",
        keyword="pants-dim",
    ),
}

REPAIRS = {
    "shorts": Repair(
        id="shorts",
        label="short play shorts",
        phrase="a pair of short play shorts",
        prep="snip the pant legs into short play shorts",
        tail="trimmed the pants into neat shorts",
    ),
    "patch": Repair(
        id="patch",
        label="a careful patch",
        phrase="a careful patch for the seam",
        prep="sew in a careful patch",
        tail="stitched the seam so it would hold",
    ),
}

NAMES = ["Pip", "Milo", "Luna", "Nell", "Toby", "Bram"]
HELPERS = ["grandmother", "mother", "father"]
TRAITS = ["patient", "proud", "curious", "gentle", "spirited"]


def reasonableness_gate(challenge: Challenge, repair: Repair) -> bool:
    if challenge.id == "tree" and repair.id == "shorts":
        return True
    if challenge.id == "fence" and repair.id == "patch":
        return True
    return False


def select_valid_combo(args: argparse.Namespace, rng: random.Random) -> tuple[str, str]:
    combos = []
    for place in SETTINGS:
        for challenge in CHALLENGES:
            for repair in REPAIRS:
                if reasonableness_gate(CHALLENGES[challenge], REPAIRS[repair]):
                    combos.append((place, challenge, repair))
    if args.place and args.place not in SETTINGS:
        raise StoryError("(No valid setting matches the given place.)")
    if args.challenge and args.challenge not in CHALLENGES:
        raise StoryError("(No valid challenge matches the given challenge.)")
    if args.repair and args.repair not in REPAIRS:
        raise StoryError("(No valid repair matches the given repair.)")
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.repair is None or c[2] == args.repair)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    return rng.choice(sorted(combos))


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    challenge = CHALLENGES[params.challenge]
    repair = REPAIRS[params.repair]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name, kind="character", type="fox", traits=["small", params.trait, "fable-hero"],
        meters={"fit_worry": 0.0, "steps": 0.0}, memes={"pride": 1.0, "hope": 0.0, "relief": 0.0}
    ))
    helper = world.add(Entity(
        id="Helper", kind="character", type=params.helper, label=f"the {params.helper}",
        meters={"time": 0.0}, memes={"care": 1.0, "memory": 1.0}
    ))
    pants = world.add(Entity(
        id="pants", type="pants", label="striped pants", phrase="striped pants",
        owner=hero.id, caretaker=helper.id, worn_by=hero.id, plural=True,
        meters={"tightness": 1.0, "strain": 0.0, "length": 1.0}, memes={"value": 1.0}
    ))
    world.facts.update(hero=hero, helper=helper, pants=pants, challenge=challenge, repair=repair)
    return world


def propagate(world: World) -> None:
    hero = world.facts["hero"]
    pants = world.facts["pants"]
    challenge = world.facts["challenge"]
    if pants.meters["tightness"] >= THRESHOLD and ("strain", pants.id) not in world.fired:
        world.fired.add(("strain", pants.id))
        pants.meters["strain"] += 1.0
        hero.memes["hope"] += 0.5
        hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1.0
    if hero.meters.get("steps", 0.0) >= THRESHOLD and pants.meters["strain"] >= THRESHOLD:
        hero.memes["suspense"] += 0.5
    if hero.memes.get("memory", 0.0) >= THRESHOLD:
        hero.memes["flashback"] = hero.memes.get("flashback", 0.0) + 1.0
    if pants.meters.get("length", 1.0) < 1.0 and ("relief", hero.id) not in world.fired:
        world.fired.add(("relief", hero.id))
        hero.memes["relief"] += 1.0
        hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1.0
        hero.memes["suspense"] = 0.0


def tell_story(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    pants = world.facts["pants"]
    challenge = world.facts["challenge"]
    repair = world.facts["repair"]

    world.say(
        f"{hero.id} was a little fox with a proud heart and {pants.phrase} that belonged to {helper.label_word if hasattr(helper, 'label_word') else helper.label}."
        if False else
        f"{hero.id} was a little fox with a proud heart and {pants.phrase} that belonged to {helper.label}."
    )
    world.say(
        f"At {world.setting.place}, {hero.id} longed to {challenge.action}, because {hero.pronoun('subject').capitalize()} loved brave climbs."
    )
    world.say(
        f"But the pants felt {challenge.suit}, and {challenge.risk}."
    )
    world.para()
    world.say(
        f"{hero.id} took a careful step, then another, and the cloth pulled tight as the path rose higher."
    )
    world.say(
        f"For a moment the orchard felt quiet and suspenseful, as if even the leaves were waiting."
    )
    world.say(
        challenge.flashback
    )
    world.para()
    world.say(
        f"Then {helper.label} smiled in surprise and said, \"We can make them fit better.\""
    )
    world.say(
        f"{helper.label.capitalize()} chose to {repair.prep}, and soon the old pants became {repair.label}."
    )
    pants.meters["length"] = 0.5
    pants.meters["tightness"] = 0.0
    pants.meters["strain"] = 0.0
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1.0
    hero.memes["relief"] += 1.0
    hero.memes["hope"] += 1.0
    hero.meters["steps"] += 1.0
    propagate(world)
    world.say(
        f"With the short pants on, {hero.id} could {challenge.action} at last."
    )
    world.say(
        f"{hero.id} reached the pears, and the fox learned that a small change can save a proud thing from breaking."
    )
    world.facts["resolved"] = True


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for young children that includes the word "{f["challenge"].keyword}" and ends with a kind surprise.',
        f"Tell a suspenseful little story about {f['hero'].id}, who wants to {f['challenge'].action} but worries the {f['pants'].label} are too tight.",
        f"Write a simple animal fable with a flashback, where {f['helper'].label} remembers how to help and turns a problem into a better fit.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    challenge = f["challenge"]
    repair = f["repair"]
    pants = f["pants"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {challenge.action}."
        ),
        QAItem(
            question=f"Why did {hero.id} feel suspense before the climb?",
            answer=f"{hero.id} felt suspense because the {pants.label} were {challenge.suit}, and {challenge.risk}."
        ),
        QAItem(
            question=f"What memory did {helper.label} have before helping?",
            answer=challenge.flashback
        ),
        QAItem(
            question=f"What surprising change did {helper.label} make to the pants?",
            answer=f"{helper.label.capitalize()} helped by {repair.tail}, so the pants fit much better."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling you get when you wonder what will happen next and you are waiting to find out."
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a remembered moment from the past that comes back into the story."
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes a story feel new and exciting."
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story, often with animals, that teaches a lesson."
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
        lines.append(f"  {e.id:8} ({e.type:10}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("action", cid, c.action))
        lines.append(asp.fact("risk", cid, c.risk))
    for rid, r in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("makes_fit", rid, "tree") if rid == "shorts" else asp.fact("makes_fit", rid, "fence"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(Place, Challenge, Repair) :- setting(Place), challenge(Challenge), repair(Repair),
    compatible(Challenge, Repair).
compatible(tree, shorts).
compatible(fence, patch).
#show valid_combo/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = {(p, c, r) for p in SETTINGS for c in CHALLENGES for r in REPAIRS if reasonableness_gate(CHALLENGES[c], REPAIRS[r])}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about suspense, flashback, and surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    place, challenge, repair = select_valid_combo(args, rng)
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, repair=repair, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
    StoryParams(place="orchard", challenge="tree", repair="shorts", name="Pip", helper="grandmother", trait="proud"),
    StoryParams(place="garden", challenge="fence", repair="patch", name="Luna", helper="mother", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_combo/3."))
        print(sorted(set(asp.atoms(model, "valid_combo"))))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
