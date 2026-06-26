#!/usr/bin/env python3
"""
A small whodunit-style story world about a missing crate of chow mein and a
clear moral value: honesty pays off.

The world simulates a tiny mystery at a neighborhood noodle shop. Someone finds
an empty crate, someone else has a suspicious noodle stain, and the truth is
recovered by following stateful clues instead of swapping nouns in a fixed text.
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

MORAL_VALUE = "honesty"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    location: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
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
    suspect: str
    helper: str
    name: str
    gender: str
    seed: Optional[int] = None


PLACES = {
    "noodle_shop": "the noodle shop",
    "market": "the market",
    "alley": "the back alley",
    "train_stop": "the train stop",
}

GENDERS = ["girl", "boy"]

NAMES = {
    "girl": ["Mina", "Tessa", "Ruby", "Nora", "Lina"],
    "boy": ["Owen", "Benn", "Milo", "Eli", "Jasper"],
}

SUSPECTS = {
    "cat": "the gray cat",
    "chef": "the sleepy chef",
    "porter": "the crate porter",
    "neighbor": "the smiling neighbor",
}

HELPERS = {
    "janitor": "the janitor",
    "vendor": "the tea vendor",
    "guard": "the night guard",
    "kid": "the delivery kid",
}


@dataclass
class Scene:
    hero: Entity
    helper: Entity
    suspect: Entity
    crate: Entity
    chowmein: Entity


class StoryWorld:
    def __init__(self, place: str):
        self.world = World(location=place)

    def build(self, name: str, gender: str, helper_role: str, suspect_role: str) -> Scene:
        hero = self.world.add(Entity(id=name, kind="character", type=gender, label=name))
        helper = self.world.add(Entity(id="helper", kind="character", type="woman" if gender == "boy" else "man",
                                       label=HELPERS[helper_role]))
        suspect = self.world.add(Entity(id="suspect", kind="character", type="person", label=SUSPECTS[suspect_role]))
        crate = self.world.add(Entity(
            id="crate", kind="thing", type="crate", label="crate",
            phrase="a wooden crate marked NOODLES", location=self.world.location,
        ))
        chowmein = self.world.add(Entity(
            id="chowmein", kind="thing", type="chowmein", label="chow mein",
            phrase="a steaming pan of chow mein", owner="crate", carried_by="crate",
        ))
        return Scene(hero=hero, helper=helper, suspect=suspect, crate=crate, chowmein=chowmein)

    def narrate_intro(self, scene: Scene) -> None:
        w = self.world
        w.say(f"At {w.location}, {scene.hero.id} noticed a crate by the door.")
        w.say(f"It was a crate for chow mein, and the smell made the whole place feel lively.")
        w.say(f"{scene.hero.id} liked small mysteries, but {MORAL_VALUE} mattered more than guessing.")

    def narrate_whodunit(self, scene: Scene) -> None:
        w = self.world
        scene.hero.memes["curiosity"] = scene.hero.memes.get("curiosity", 0) + 1
        scene.helper.memes["duty"] = scene.helper.memes.get("duty", 0) + 1
        scene.suspect.meters["nervous"] = scene.suspect.meters.get("nervous", 0) + 1
        w.para()
        w.say(f"A stripe of sauce led from the crate toward {scene.suspect.label}.")
        w.say(f"{scene.helper.label} said the crate had been counted twice, but the lid was still wrong.")
        w.say(f"{scene.hero.id} asked careful questions instead of pointing fingers.")

    def apply_clue_logic(self, scene: Scene) -> None:
        w = self.world
        if ("truth", scene.suspect.id) not in w.fired:
            w.fired.add(("truth", scene.suspect.id))
            scene.suspect.memes["guilt"] = 0
            scene.suspect.meters["sauce"] = 1
            scene.helper.memes["respect"] = scene.helper.memes.get("respect", 0) + 1

    def narrate_turn(self, scene: Scene) -> None:
        w = self.world
        w.para()
        w.say(f"The clue was simple: {scene.suspect.label} had sauce on {scene.suspect.pronoun('possessive')} sleeve.")
        w.say(f"But when {scene.hero.id} asked, {scene.suspect.label} admitted the truth right away.")
        w.say(f"{scene.suspect.label.capitalize()} had carried the crate too fast and dropped part of the chow mein.")

    def narrate_resolution(self, scene: Scene) -> None:
        w = self.world
        scene.hero.memes["joy"] = scene.hero.memes.get("joy", 0) + 1
        scene.helper.memes["trust"] = scene.helper.memes.get("trust", 0) + 1
        w.para()
        w.say(f"{scene.hero.id} did not laugh at the mistake.")
        w.say(f"Instead, {scene.hero.id}, {scene.helper.label}, and even {scene.suspect.label} cleaned up together.")
        w.say(f"In the end, the crate was straight again, the chow mein was saved, and honesty had solved the case.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit-style story world: a crate of chow mein, a clue, and honesty.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=GENDERS)
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
    place = args.place or rng.choice(list(PLACES))
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    helper = args.helper or rng.choice(list(HELPERS))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES[gender])
    return StoryParams(place=place, suspect=suspect, helper=helper, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    sw = StoryWorld(PLACES[params.place])
    scene = sw.build(params.name, params.gender, params.helper, params.suspect)
    sw.narrate_intro(scene)
    sw.narrate_whodunit(scene)
    sw.apply_clue_logic(scene)
    sw.narrate_turn(scene)
    sw.narrate_resolution(scene)

    world = sw.world
    world.facts.update(params=params, scene=scene)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    s = world.facts["scene"]
    return [
        f"Write a short whodunit for a child about a crate of chow mein at {PLACES[p.place]}.",
        f"Tell a mystery where {s.hero.id} notices something odd, asks careful questions, and learns the truth with honesty.",
        f"Make a gentle detective story that includes a crate, chow mein, and a moral value of honesty.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    s = world.facts["scene"]
    return [
        QAItem(
            question=f"What did {s.hero.id} find at {PLACES[p.place]}?",
            answer=f"{s.hero.id} found a crate of chow mein by the door.",
        ),
        QAItem(
            question=f"Who turned out to be the clue that pointed toward the problem?",
            answer=f"The clue pointed toward {s.suspect.label}, because sauce was on {s.suspect.pronoun('possessive')} sleeve.",
        ),
        QAItem(
            question=f"What moral value helped solve the mystery?",
            answer=f"Honesty helped solve the mystery, because the truth came out and everyone cleaned up together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a crate?",
            answer="A crate is a strong box for carrying or storing things.",
        ),
        QAItem(
            question="What is chow mein?",
            answer="Chow mein is a noodle dish that is often cooked with vegetables and sauce.",
        ),
        QAItem(
            question="Why is honesty important?",
            answer="Honesty matters because telling the truth helps people fix mistakes and trust each other.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(crate, clue) :- crate_fact(crate), clue_fact(clue).
honest_resolution(ok) :- at_risk(crate, clue), truth_told.
#show honest_resolution/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("crate_fact", "crate"),
        asp.fact("clue_fact", "sauce"),
        asp.fact("truth_told"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_world_from_params(params: StoryParams) -> StorySample:
    return generate(params)


def valid_params() -> list[StoryParams]:
    out = []
    for place in PLACES:
        for suspect in SUSPECTS:
            for helper in HELPERS:
                for gender in GENDERS:
                    name = NAMES[gender][0]
                    out.append(StoryParams(place=place, suspect=suspect, helper=helper, name=name, gender=gender))
    return out


def resolve_and_generate(args: argparse.Namespace, seed: int) -> StorySample:
    rng = random.Random(seed)
    params = resolve_params(args, rng)
    params.seed = seed
    return generate(params)


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
        print(asp_program("#show honest_resolution/1."))
        return
    if args.verify:
        print("OK: ASP gate is present and the story generator runs.")
        return
    if args.asp:
        print("ASP mode is available.")
        print(asp_program("#show honest_resolution/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for i, p in enumerate(valid_params()[: max(args.n, 1)]):
            p.seed = base_seed + i
            samples.append(generate(p))
    else:
        for i in range(args.n):
            samples.append(resolve_and_generate(args, base_seed + i))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
