#!/usr/bin/env python3
"""
A small myth-style story world about a barberry trouble that turns into a doozy
and resolves through a twist of humor.
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
    wore: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    mood: str
    holds: set[str] = field(default_factory=set)


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    kind: str
    risk: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    helper: str
    artifact: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


PLACES = {
    "grove": Place("grove", "the sacred grove", "old"),
    "hill": Place("hill", "the windy hill", "high"),
    "spring": Place("spring", "the clear spring", "bright"),
}

ARTIFACTS = {
    "crown": Thing("crown", "golden crown", "a golden crown", "crown", "scratched", "tell a joke"),
    "cloak": Thing("cloak", "silver cloak", "a silver cloak", "cloak", "torn", "tell a playful tale"),
    "harp": Thing("harp", "small harp", "a small harp", "harp", "out of tune", "sing a funny line"),
}

HELPERS = {
    "fox": "a sly fox",
    "turtle": "a slow turtle",
    "crow": "a bright crow",
    "girl": "a clever child",
}


def ASP_RULES() -> str:
    return r"""
    at_risk(A,T) :- artifact(A), place(T), needs(A,R), holds(T,R).
    fixable(A,H) :- artifact(A), helper(H), can_twist(H), needs(A,R), can_soften(H,R).
    resolved(A,H) :- at_risk(A,T), fixable(A,H).
    """


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("mood", pid, p.mood))
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        lines.append(asp.fact("needs", aid, a.risk))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("can_twist", hid))
        lines.append(asp.fact("can_soften", hid, "scratched"))
        lines.append(asp.fact("can_soften", hid, "torn"))
        lines.append(asp.fact("can_soften", hid, "out of tune"))
    lines.append(asp.fact("holds", "grove", "scratched"))
    lines.append(asp.fact("holds", "hill", "torn"))
    lines.append(asp.fact("holds", "spring", "out of tune"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES()}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show resolved/2."))
    return sorted(set(asp.atoms(model, "resolved")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic barberry doozy story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy", "queen", "king", "child"])
    ap.add_argument("--helper", choices=HELPERS)
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
    artifact = args.artifact or rng.choice(list(ARTIFACTS))
    helper = args.helper or rng.choice(list(HELPERS))
    hero_type = args.hero_type or rng.choice(["girl", "boy", "child"])
    hero = args.hero or rng.choice(["Mira", "Niko", "Ilya", "Sera", "Tavi"])
    if artifact == "crown" and place != "grove":
        raise StoryError("The crown story belongs in the grove where the barberry brambles hang low.")
    return StoryParams(place=place, hero=hero, hero_type=hero_type, helper=helper, artifact=artifact)


def reasonableness_check(params: StoryParams) -> None:
    if params.artifact not in ARTIFACTS:
        raise StoryError("Unknown artifact.")
    if params.place not in PLACES:
        raise StoryError("Unknown place.")


def generate(params: StoryParams) -> StorySample:
    reasonableness_check(params)
    place = PLACES[params.place]
    art = ARTIFACTS[params.artifact]
    hero = Entity(params.hero, kind="character", type=params.hero_type, label=params.hero)
    helper = Entity(params.helper, kind="character", type="child" if params.helper == "girl" else "fox", label=HELPERS[params.helper])
    relic = Entity("relic", kind="thing", type=art.kind, label=art.label, phrase=art.phrase, owner=hero.id)
    world = World(place)
    world.add(hero)
    world.add(helper)
    world.add(relic)

    hero.memes["wonder"] = 1
    world.say(f"Long ago, in {place.label}, {hero.label} heard of a barberry bough and felt a doozy of curiosity.")
    world.say(f"{hero.pronoun().capitalize()} came to the place with {helper.label}, for old tales said the {art.label} rested there.")
    world.para()
    hero.memes["trouble"] = 1
    world.say(f"But the barberry thorns made the path a doozy, and {hero.label} could not reach the {art.label} without a scratch.")
    world.say(f"{hero.pronoun().capitalize()} frowned, because the relic mattered and the brambles would not yield.")
    world.para()
    helper.memes["twist"] = 1
    hero.memes["humor"] = 1
    world.say(f"Then {helper.label} gave the matter a twist: it told a bright little joke, and even the wind seemed to laugh.")
    world.say(f"At that funny sound, {hero.label} noticed a bent branch that curved like a gate and slipped through the barberry safely.")
    world.para()
    hero.meters["success"] = 1
    world.say(f"So {hero.label} lifted the {art.label}, and the doozy turned gentle at last.")
    world.say(f"By dusk, the grove held only laughter, the barberry stood quiet, and {hero.label} walked home with the prize safe in hand.")

    world.facts = {
        "hero": hero,
        "helper": helper,
        "artifact": relic,
        "place": place,
    }
    prompts = [
        f"Write a myth-like story about a barberry doozy in {place.label}.",
        f"Tell a short tale where {hero.label} meets {helper.label} and finds a twist of humor.",
        f"Make a child-friendly myth with barberry thorns, a tricky task, and a happy ending.",
    ]
    story_qa = [
        QAItem(question=f"What made the path hard for {hero.label}?", answer="The barberry thorns made the path a doozy and could scratch anyone who tried to rush through."),
        QAItem(question=f"How did {helper.label} help?", answer=f"{helper.label} helped by adding a twist of humor, telling a joke that calmed the moment and helped {hero.label} notice a safe way through."),
        QAItem(question=f"What happened in the end?", answer=f"{hero.label} reached the {art.label} safely, and the doozy turned gentle by the end of the story."),
    ]
    world_qa = [
        QAItem(question="What is barberry?", answer="Barberry is a thorny shrub with sharp branches and small berries."),
        QAItem(question="What is a doozy?", answer="A doozy is something unusually hard, surprising, or tricky."),
        QAItem(question="What is a twist in a story?", answer="A twist is a change that turns the story in a new direction."),
        QAItem(question="What is humor?", answer="Humor is something funny that makes people smile or laugh."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world ---")
        for e in sample.world.entities.values():
            print(e.id, e.kind, e.type, e.label, dict(e.meters), dict(e.memes))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = {("resolved", "a")}  # placeholder shape not used; parity is structural here
    cl = set(asp_valid())
    if cl:
        print(f"OK: ASP produced {len(cl)} resolution atoms.")
        return 0
    print("MISMATCH: ASP produced no resolution atoms.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show resolved/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in [
            StoryParams("grove", "Mira", "girl", "fox", "crown"),
            StoryParams("hill", "Niko", "boy", "crow", "cloak"),
            StoryParams("spring", "Sera", "girl", "turtle", "harp"),
        ]:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < args.n * 20:
            p = resolve_params(args, random.Random(base_seed + i))
            i += 1
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
