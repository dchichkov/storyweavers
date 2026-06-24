#!/usr/bin/env python3
"""
A small pirate tale storyworld about a brave crew, a foreshadowed clue, and a
surprising barberry treasure.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pirate", "sailor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass
class Setting:
    place: str
    tide: str
    features: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    clue_text: str
    surprise_text: str
    at_risk: str
    foreshadow: str


@dataclass
class StoryParams:
    setting: str
    clue: str
    hero_name: str
    hero_type: str
    captain_type: str
    seed: Optional[int] = None


SETTINGS = {
    "harbor": Setting(place="the harbor", tide="high tide", features={"ship", "barberry"}),
    "island": Setting(place="a small island", tide="low tide", features={"cove", "barberry"}),
    "reef": Setting(place="the reef edge", tide="rising tide", features={"rocks", "barberry"}),
}

CLUES = {
    "barberry": Clue(
        id="barberry",
        label="barberry bush",
        phrase="a prickly barberry bush by the path",
        clue_text="a spray of red berries and a scratch of thorns",
        surprise_text="a hidden brass key tied under the roots",
        at_risk="the berry patch",
        foreshadow="the thorns looked like tiny warning teeth",
    ),
}

GIRL_NAMES = ["Mina", "Rae", "Nina", "Elsa", "Tia", "Pia"]
BOY_NAMES = ["Finn", "Jory", "Puck", "Milo", "Gus", "Tate"]

HERO_TYPES = ["girl", "boy"]
CAPTAIN_TYPES = ["captain", "pirate"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with foreshadowing, bravery, and surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--captain-type", choices=CAPTAIN_TYPES)
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


def valid_combos() -> list[tuple[str, str]]:
    return [("harbor", "barberry"), ("island", "barberry"), ("reef", "barberry")]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    clue = args.clue or "barberry"
    if clue != "barberry":
        raise StoryError("This tiny world only tells the barberry tale.")
    name = args.name or rng.choice(GIRL_NAMES if (args.hero_type or rng.choice(HERO_TYPES)) == "girl" else BOY_NAMES)
    hero_type = args.hero_type or ("girl" if name in GIRL_NAMES else "boy")
    captain_type = args.captain_type or rng.choice(CAPTAIN_TYPES)
    return StoryParams(setting=setting, clue=clue, hero_name=name, hero_type=hero_type, captain_type=captain_type)


def generate_world(params: StoryParams) -> World:
    w = World()
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]

    hero = w.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label=params.hero_name))
    captain = w.add(Entity(id="Captain", kind="character", type=params.captain_type, label="the captain"))
    bush = w.add(Entity(id="barberry", type="plant", label="barberry bush", phrase=clue.phrase, owner="island"))
    key = w.add(Entity(id="key", type="thing", label="brass key", phrase="a small brass key", owner="barberry"))

    hero.memes["curiosity"] = 1
    hero.memes["bravery"] = 0
    captain.memes["worry"] = 1

    w.say(f"At {setting.place}, {params.hero_name} sailed with {captain.label} and watched the {bush.label}.")
    w.say(f"The {bush.label} had {clue.foreshadow}, and {params.hero_name} remembered that little warning.")

    w.para()
    w.say(f"When the tide pulled back, {params.hero_name} saw {clue.clue_text} near the thorns.")
    w.say(f"{params.hero_name} took a careful breath and reached in anyway, because {params.hero_name} wanted to know what the bush was hiding.")
    hero.memes["bravery"] += 1

    w.para()
    w.say(f"The surprise was bigger than anyone guessed: {clue.surprise_text}.")
    w.say(f"{params.hero_name} held up the key, laughing, while {captain.label} said the old clue had been a true one after all.")
    w.say(f"By the end, the brave child had solved the mystery of the barberry bush, and the ship could sail on with a fresh bit of treasure.")
    w.facts.update(hero=hero, captain=captain, bush=bush, key=key, setting=setting, clue=clue)
    return w


def prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue"]
    setting = f["setting"]
    return [
        f"Write a short pirate tale for a young child set at {setting.place} with a barberry bush clue.",
        f"Tell a story where {hero.id} shows bravery after noticing {clue.foreshadow}.",
        f"Write a tiny adventure that ends with a surprising treasure hidden in the barberry bush.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    clue = f["clue"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Where did {hero.id} and {captain.label} go in the story?",
            answer=f"They went to {setting.place}, where the barberry bush was waiting beside the path.",
        ),
        QAItem(
            question=f"What foreshadowing detail did the story give about the barberry bush?",
            answer=f"The story said that {clue.foreshadow}, which hinted that something important was hidden there.",
        ),
        QAItem(
            question=f"What surprise did {hero.id} find in the barberry bush?",
            answer=f"{hero.id} found {clue.surprise_text}, and that was the treasure hidden under the roots.",
        ),
        QAItem(
            question=f"How did {hero.id} act when the clue looked risky?",
            answer=f"{hero.id} was brave, took a careful breath, and reached in to see what the bush was hiding.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a barberry bush?",
            answer="A barberry bush is a plant with prickly branches and small red berries.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives a small clue about something that may happen later.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something hard or scary even when you feel nervous.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that the characters did not know was coming.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], ""]
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
    bits = ["--- world model state ---"]
    for e in world.entities.values():
        bits.append(f"{e.id:10} {e.type:10} memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
    return "\n".join(bits)


ASP_RULES = r"""
setting(harbor). setting(island). setting(reef).
clue(barberry).
valid_story(S,C) :- setting(S), clue(C).
#show valid_story/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    lines.append(asp.fact("clue", "barberry"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(setting="harbor", clue="barberry", hero_name="Mina", hero_type="girl", captain_type="captain"),
    StoryParams(setting="island", clue="barberry", hero_name="Finn", hero_type="boy", captain_type="pirate"),
    StoryParams(setting="reef", clue="barberry", hero_name="Rae", hero_type="girl", captain_type="pirate"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for s, c in combos:
            print(f"  {s:8} {c:8}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.setting} ({p.clue})"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
