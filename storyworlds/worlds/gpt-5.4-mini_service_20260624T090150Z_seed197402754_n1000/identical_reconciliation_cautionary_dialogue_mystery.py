#!/usr/bin/env python3
"""
Story world: identical_reconciliation_cautionary_dialogue_mystery

A small mystery domain about two identical siblings, a missing clue, cautious
dialogue, and a gentle reconciliation at the end.
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    taken_by: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    clue: str
    hiding_place: str
    mood: str


@dataclass
class StoryParams:
    place: str
    clue: str
    culprit: str
    hero: str
    sibling: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        import copy as _copy
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


IDENTICAL_PAIRS = [
    ("Mia", "Lia"),
    ("Nora", "Cora"),
    ("Ava", "Eva"),
    ("Tessa", "Nessa"),
    ("Milo", "Nilo"),
    ("Ben", "Finn"),
]

PLACES = [
    Setting(place="the library", clue="a silver key", hiding_place="under a red chair", mood="quiet"),
    Setting(place="the attic", clue="a striped map", hiding_place="inside a toy box", mood="dusty"),
    Setting(place="the garden shed", clue="a tiny bell", hiding_place="behind the paint cans", mood="still"),
    Setting(place="the school closet", clue="a blue note", hiding_place="inside a rain boot", mood="hushed"),
]

CULPRITS = {
    "mouse": "a small mouse",
    "wind": "a windy draft",
    "prank": "a careful prank",
    "cat": "a sleepy cat",
}

ASP_RULES = r"""
culprit(mouse).
culprit(wind).
culprit(prank).
culprit(cat).

setting(library).
setting(attic).
setting(shed).
setting(closet).

clue_for(library,key).
clue_for(attic,map).
clue_for(shed,bell).
clue_for(closet,note).

valid(Place, Clue, Culprit) :- setting(Place), clue_for(Place, Clue), culprit(Culprit).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in PLACES:
        pid = s.place.replace("the ", "").replace(" ", "_")
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("clue_for", pid, s.clue.split()[-1]))
    for c in CULPRITS:
        lines.append(asp.fact("culprit", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p.place.replace("the ", "").replace(" ", "_"), s.clue.split()[-1], c) for p in PLACES for c in CULPRITS}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery about identical siblings and a lost clue.")
    ap.add_argument("--place", choices=[p.place for p in PLACES])
    ap.add_argument("--clue")
    ap.add_argument("--culprit", choices=list(CULPRITS))
    ap.add_argument("--hero")
    ap.add_argument("--sibling")
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
    place = next((p for p in PLACES if p.place == args.place), None) if args.place else rng.choice(PLACES)
    culprit = args.culprit or rng.choice(list(CULPRITS))
    hero, sibling = (args.hero, args.sibling) if args.hero and args.sibling else rng.choice(IDENTICAL_PAIRS)
    clue = args.clue or place.clue
    if args.clue and args.clue != place.clue:
        raise StoryError("This clue does not belong in the chosen place.")
    if hero == sibling:
        raise StoryError("The siblings must be different people, even if they look identical.")
    return StoryParams(place=place.place, clue=clue, culprit=culprit, hero=hero, sibling=sibling)


def _said(world: World, speaker: Entity, text: str) -> None:
    world.say(f'"{text}" {speaker.id} said.')


def generate(params: StoryParams) -> StorySample:
    setting = next(p for p in PLACES if p.place == params.place)
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type="girl"))
    sibling = world.add(Entity(id=params.sibling, kind="character", type="girl"))
    clue = world.add(Entity(id="clue", label=params.clue, phrase=params.clue, hidden=True))
    culprit = world.add(Entity(id=params.culprit, label=CULPRITS[params.culprit], kind="thing"))

    world.say(f"{hero.id} and {sibling.id} were identical twins, and everyone in {setting.place} mixed them up.")
    world.say(f"One quiet day, a strange thing happened at {setting.place}: {setting.clue} was missing.")
    world.para()
    world.say(f"{hero.id} frowned and looked at {sibling.id}. {sibling.id} looked back, just as surprised.")
    _said(world, hero, f"Did you take the {setting.clue.split()[-1]}?")
    _said(world, sibling, f"No. And we should not guess without looking first.")
    world.say(f"They searched carefully. Behind the scenes, the mystery felt {setting.mood}, and every tiny sound seemed important.")
    world.para()
    if params.culprit == "mouse":
        world.say(f"Then they noticed a small trail near {setting.hiding_place}.")
        world.say(f"A little mouse had dragged the {setting.clue} there to make a nest.")
    elif params.culprit == "wind":
        world.say(f"A draft had nudged the {setting.clue} away from its spot and tucked it near {setting.hiding_place}.")
    elif params.culprit == "prank":
        world.say(f"It was only a careful prank, and the prankster had hidden the {setting.clue} near {setting.hiding_place}.")
    else:
        world.say(f"A sleepy cat had pushed the {setting.clue} toward {setting.hiding_place} with a soft paw.")
    world.say(f"{hero.id} and {sibling.id} followed the clue together and found it.")
    world.para()
    world.say(f"{hero.id} turned to {sibling.id} and said sorry for the quick guess.")
    world.say(f"{sibling.id} smiled back and said it was all right.")
    world.say(f"Because they were identical on the outside, they chose to be extra careful with their words on the inside.")
    world.say(f"At the end, the {setting.clue} was back where it belonged, and the twins walked home side by side, finally in agreement.")

    world.facts.update(setting=setting, hero=hero, sibling=sibling, clue=clue, culprit=culprit)
    story = world.render()
    prompts = [
        f"Write a short mystery story for a young child about identical twins at {setting.place}.",
        f"Tell a gentle story where {hero.id} and {sibling.id} solve a missing {setting.clue.split()[-1]} mystery with cautious dialogue.",
        f"Write a child-friendly mystery with the word identical and a happy reconciliation at the end.",
    ]
    story_qa = [
        QAItem(
            question=f"Why did {hero.id} and {sibling.id} think carefully before blaming each other?",
            answer="Because they looked identical, they knew it would be easy to guess wrong, so they decided to search first and speak gently.",
        ),
        QAItem(
            question=f"What was missing at {setting.place}?",
            answer=f"The {setting.clue} was missing.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {sibling.id}?",
            answer=f"They found the {setting.clue}, apologized for the quick guess, and reconciled by the end.",
        ),
    ]
    world_qa = [
        QAItem(question="What does identical mean?", answer="Identical means that two things look exactly the same, or almost exactly the same."),
        QAItem(question="Why is it unkind to accuse someone without checking?", answer="It can hurt their feelings, so it is better to look for clues first and ask carefully."),
        QAItem(question="What is a mystery?", answer="A mystery is something puzzling that needs clues and careful thinking to solve."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", ""]
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
        if e.label:
            bits.append(f"label={e.label}")
        if e.hidden:
            bits.append("hidden=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) " + " ".join(bits))
    return "\n".join(lines)


CURATED = [
    StoryParams(place="the library", clue="a silver key", culprit="mouse", hero="Mia", sibling="Lia"),
    StoryParams(place="the attic", clue="a striped map", culprit="wind", hero="Nora", sibling="Cora"),
    StoryParams(place="the garden shed", clue="a tiny bell", culprit="cat", hero="Ava", sibling="Eva"),
    StoryParams(place="the school closet", clue="a blue note", culprit="prank", hero="Milo", sibling="Nilo"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in PLACES:
        for c in CULPRITS:
            out.append((s.place, s.clue, c))
    return out


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible triples:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
