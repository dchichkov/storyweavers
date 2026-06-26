#!/usr/bin/env python3
"""
storyworlds/worlds/soda_misunderstanding_bad_ending_whodunit.py
===============================================================

A small whodunit-style story world about soda, clues, and a bad ending.

Premise:
- A child notices a soda is missing or spoiled.
- A misleading clue makes the wrong person look guilty.
- The truth is stranger and sadder than the guess.
- The story ends badly: trust is hurt, and the soda is ruined or flat.

This world models a tiny mystery domain with:
- typed entities
- physical meters and emotional memes
- a deliberate misunderstanding
- a bad ending that follows from the wrong conclusion
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    clue: str
    true_role: str
    alibi: str
    suspicion: str
    tells: set[str] = field(default_factory=set)


@dataclass
class Soda:
    id: str
    label: str
    phrase: str
    flavor: str
    container: str
    mess: str
    spoil: str
    clues: set[str] = field(default_factory=set)
    requires_care: bool = True


@dataclass
class StoryParams:
    place: str
    soda: str
    suspect: str
    name: str
    gender: str
    parent: str
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"spill", "hide", "search"}),
    "porch": Setting(place="the porch", indoors=False, affords={"spill", "hide", "search"}),
    "picnic": Setting(place="the picnic table", indoors=False, affords={"spill", "hide", "search"}),
}

SODAS = {
    "cola": Soda(
        id="cola",
        label="cola",
        phrase="a cold can of cola",
        flavor="cola",
        container="can",
        mess="sticky",
        spoil="flat",
        clues={"fizz", "ring", "sticky"},
    ),
    "orange": Soda(
        id="orange",
        label="orange soda",
        phrase="a bright bottle of orange soda",
        flavor="orange soda",
        container="bottle",
        mess="sticky",
        spoil="flat",
        clues={"cap", "ring", "sticky"},
    ),
    "root": Soda(
        id="root",
        label="root beer",
        phrase="a fizzy bottle of root beer",
        flavor="root beer",
        container="bottle",
        mess="sticky",
        spoil="flat",
        clues={"cap", "fizz", "sticky"},
    ),
}

SUSPECTS = {
    "brother": Suspect(
        id="brother",
        label="older brother",
        type="boy",
        clue="crumbs",
        true_role="helper",
        alibi="he was in the hallway with a book",
        suspicion="he had sticky fingers from jam",
        tells={"jam", "napkin"},
    ),
    "friend": Suspect(
        id="friend",
        label="best friend",
        type="girl",
        clue="napkin",
        true_role="helper",
        alibi="she was drawing at the table",
        suspicion="she had a damp sleeve",
        tells={"napkin", "straw"},
    ),
    "neighbor": Suspect(
        id="neighbor",
        label="neighbor kid",
        type="boy",
        clue="spoon",
        true_role="helper",
        alibi="he was outside chasing a ball",
        suspicion="he had a shiny spoon",
        tells={"spoon", "cap"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Finn", "Noah", "Eli", "Theo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for soda in SODAS:
            for suspect in SUSPECTS:
                combos.append((place, soda, suspect))
    return combos


def reasonableness_gate(place: str, soda: Soda, suspect: Suspect) -> None:
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    if soda.id not in SODAS:
        raise StoryError("Unknown soda.")
    if suspect.id not in SUSPECTS:
        raise StoryError("Unknown suspect.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit about soda, misunderstanding, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--soda", choices=SODAS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.soda is None or c[1] == args.soda)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, soda_id, suspect_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, soda=soda_id, suspect=suspect_id, name=name, gender=gender, parent=parent)


def _owner_word(parent: str) -> str:
    return "mom" if parent == "mother" else "dad"


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    soda = SODAS[params.soda]
    suspect = SUSPECTS[params.suspect]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=_owner_word(params.parent)))
    suspect_ent = world.add(Entity(id=suspect.id, kind="character", type=suspect.type, label=suspect.label))
    drink = world.add(Entity(
        id="soda",
        kind="thing",
        type=soda.container,
        label=soda.label,
        phrase=soda.phrase,
        owner=parent.id,
        held_by=hero.id,
    ))

    hero.memes["curious"] = 1
    hero.memes["doubt"] = 0
    suspect_ent.memes["nervous"] = 0
    drink.meters["full"] = 1
    drink.meters["fizz"] = 1

    world.say(f"{hero.id} was a little {params.gender} who liked solving small mysteries.")
    world.say(f"One afternoon, {hero.id}'s {parent.label} brought home {drink.phrase}.")
    world.say(f"{hero.id} watched {drink.label} sparkle on the table and wanted to know who would get to open it.")

    world.para()
    world.say(f"At {setting.place}, the air felt still, and the soda waited like a secret.")
    world.say(f"Then the bottle moved, and nobody seemed to own the moment anymore.")

    # Mystery turn: a misleading clue.
    clue = suspect.clue
    world.facts["clue"] = clue
    world.facts["soda"] = soda
    world.facts["suspect"] = suspect_ent
    world.facts["hero"] = hero
    world.facts["parent"] = parent

    hero.memes["suspicion"] += 1
    suspect_ent.memes["nervous"] += 1
    world.say(
        f"{hero.id} noticed a {clue} near the table and a sticky ring by the cup. "
        f"It looked as if {suspect_ent.label} had touched the soda."
    )

    world.para()
    world.say(f"But that was the wrong guess.")
    world.say(
        f"{suspect_ent.label} had only been helping. {suspect.alibi}. "
        f"{suspect.suspicion} made the clue look worse than it was."
    )

    # Bad ending: the misunderstanding damages trust and ruins the soda.
    hero.memes["guilt"] = 1
    suspect_ent.memes["hurt"] = 1
    drink.meters["opened"] = 1
    drink.meters["flat"] = 1
    drink.meters["spilled"] = 0 if place == "kitchen" else 1

    if place == "kitchen":
        ending = (
            f"By the time {hero.id} finally opened the soda, it had gone flat. "
            f"{suspect_ent.label} turned away, quiet and sad, because nobody had listened first."
        )
    else:
        ending = (
            f"When {hero.id} pointed at {suspect_ent.label}, the real clue was lost, and the soda went flat in the warm air. "
            f"{suspect_ent.label} walked off with a hurt face, and the mystery ended in the wrong place."
        )
    world.say(ending)

    world.facts["ending"] = "bad"
    world.facts["resolved"] = False
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    soda: Soda = f["soda"]
    suspect: Entity = f["suspect"]
    hero: Entity = f["hero"]
    return [
        f'Write a short whodunit for a small child about a {soda.label} and a mistaken clue.',
        f"Tell a gentle mystery story where {hero.id} sees a {suspect.label} near {soda.phrase}, but the guess is wrong.",
        f'Write a sad little mystery that includes the word "{soda.label}" and ends with a bad misunderstanding.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    suspect: Entity = f["suspect"]
    soda: Soda = f["soda"]
    clue = f["clue"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, who tried to figure out what happened to the {soda.label}.",
        ),
        QAItem(
            question=f"What clue made {hero.id} guess the wrong person?",
            answer=f"A {clue} near the table and a sticky ring made {hero.id} think {suspect.label} had done it.",
        ),
        QAItem(
            question=f"Why was {suspect.label} upset at the end?",
            answer=f"{suspect.label} was only helping, but {hero.id} made the wrong guess and did not listen in time.",
        ),
        QAItem(
            question=f"What happened to the soda?",
            answer=f"The soda went flat, so the story ended badly instead of with a happy fix.",
        ),
    ]
    if not world.facts.get("resolved"):
        qa.append(
            QAItem(
                question=f"Did the mystery end well?",
                answer="No. The mystery ended badly because the wrong person was blamed and the soda was ruined.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    soda: Soda = f["soda"]
    return [
        QAItem(
            question="What does soda do when it is fresh and closed?",
            answer="Fresh soda is fizzy and bubbly when it is still closed.",
        ),
        QAItem(
            question="Why can soda go flat?",
            answer="Soda can go flat when the bubbles escape after it is opened or left out too long.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that can help someone guess what happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions ==",]
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(kitchen).
valid_place(porch).
valid_place(picnic).

valid_soda(cola).
valid_soda(orange).
valid_soda(root).

valid_suspect(brother).
valid_suspect(friend).
valid_suspect(neighbor).

combo(P,S,SU) :- valid_place(P), valid_soda(S), valid_suspect(SU).
#show combo/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("valid_place", p))
    for s in SODAS:
        lines.append(asp.fact("valid_soda", s))
    for su in SUSPECTS:
        lines.append(asp.fact("valid_suspect", su))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show combo/3."))
    return sorted(set(asp.atoms(model, "combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in python:", sorted(py - asp_set))
    print("only in asp:", sorted(asp_set - py))
    return 1


CURATED = [
    StoryParams(place="kitchen", soda="cola", suspect="brother", name="Mia", gender="girl", parent="mother"),
    StoryParams(place="porch", soda="orange", suspect="friend", name="Leo", gender="boy", parent="father"),
    StoryParams(place="picnic", soda="root", suspect="neighbor", name="Nora", gender="girl", parent="mother"),
]


def asp_show_program() -> str:
    return asp_program("#show combo/3.")


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
        print(asp_show_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_combos()
        print(f"{len(combos)} combinations:")
        for item in combos:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.soda} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
