#!/usr/bin/env python3
"""
A small adventure-style story world: a terrier on a quest for a neat taper
style, with dialogue and conflict driving the turn.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("dust", "snip", "style"):
            self.meters.setdefault(k, 0.0)
        for k in ("hope", "worry", "pride", "frustration", "resolve"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def is_a(self) -> str:
        art = "an" if self.label[:1].lower() in "aeiou" else "a"
        return f"{art} {self.label}" if self.label else self.type


@dataclass
class Place:
    label: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StylePlan:
    id: str
    label: str
    phrase: str
    prep: str
    finish: str
    needs: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    verb: str
    risk: str
    clue: str
    keywords: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
class StoryParams:
    place: str
    quest: str
    style: str
    hero: str
    seed: Optional[int] = None


PLACES = {
    "barn": Place("the barn", {"trim", "dialogue"}),
    "shop": Place("the little shop", {"trim", "dialogue"}),
    "garden": Place("the garden path", {"dialogue", "quest"}),
}

STYLE_PLANS = {
    "taper": StylePlan(
        id="taper",
        label="taper",
        phrase="a tidy taper style",
        prep="give the fur a careful taper",
        finish="came out neat and even",
        needs={"clipper", "mirror"},
    ),
}

QUESTS = {
    "showday": Quest(
        id="showday",
        goal="reach the ribbon show",
        verb="set out for the ribbon show",
        risk="look scruffy at the gate",
        clue="the ribbon gate was far beyond the hay bales",
        keywords={"show", "ribbon", "gate"},
    ),
    "mousetrail": Quest(
        id="mousetrail",
        goal="follow the mouse trail",
        verb="follow the mouse trail",
        risk="lose the map in the grass",
        clue="the trail curled past the toolshed",
        keywords={"mouse", "trail", "map"},
    ),
}

HEROES = {
    "terrier": {"label": "terrier", "type": "dog", "name": "Milo"},
    "spot": {"label": "terrier", "type": "dog", "name": "Spot"},
}


ASP_RULES = r"""
place(barn). place(shop). place(garden).
affords(barn,trim). affords(barn,dialogue).
affords(shop,trim). affords(shop,dialogue).
affords(garden,dialogue). affords(garden,quest).

style_plan(taper).
needs(taper,clipper).
needs(taper,mirror).

quest(showday).
quest(mousetrail).

compatible(P, S, Q) :- affords(P, trim), style_plan(S), quest(Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for sid in STYLE_PLANS:
        lines.append(asp.fact("style_plan", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for hid in HEROES:
        lines.append(asp.fact("hero_kind", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for style_id in STYLE_PLANS:
            for quest_id in QUESTS:
                if "trim" in place.affords:
                    out.append((place_id, style_id, quest_id))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(a - b))
    print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: a terrier, a taper, and a quest.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--style", choices=STYLE_PLANS)
    ap.add_argument("--hero", choices=HEROES)
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
    if args.place and args.quest and args.place not in PLACES:
        raise StoryError("Unknown place.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.style is None or c[1] == args.style)
              and (args.quest is None or c[2] == args.quest)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, style, quest = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(sorted(HEROES))
    return StoryParams(place=place, style=style, quest=quest, hero=hero)


def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero_cfg = HEROES[params.hero]
    hero = world.add(Entity(
        id=hero_cfg["name"],
        kind="character",
        type=hero_cfg["type"],
        label=hero_cfg["label"],
    ))
    stylist = world.add(Entity(id="Rina", kind="character", type="person", label="Rina"))
    scissors = world.add(Entity(id="scissors", label="silver scissors"))
    mirror = world.add(Entity(id="mirror", label="round mirror"))
    world.facts.update(hero=hero, stylist=stylist, scissors=scissors, mirror=mirror)
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    stylist: Entity = world.facts["stylist"]  # type: ignore[assignment]
    style = STYLE_PLANS[params.style]
    quest = QUESTS[params.quest]

    hero.memes["hope"] += 1
    world.say(f"{hero.label.capitalize()} the terrier loved adventure and kept a brave little style in {world.place.label}.")
    world.say(f"One day, {hero.label.capitalize()} wanted {style.phrase} before {quest.verb}.")
    world.para()
    world.say(f'“Can you {style.prep}?” {hero.pronoun("subject").capitalize()} asked {stylist.id} at {world.place.label}.')
    world.say(f'“Yes,” said {stylist.id}, “but we need a clipper and a mirror, and we must be careful not to nick the ears.”')
    world.para()
    hero.memes["worry"] += 1
    hero.meters["style"] += 1
    world.say(f"{quest.clue.capitalize()}. But a gust of wind shoved the towel aside, and {hero.label} began to wobble on the stool.")
    hero.memes["frustration"] += 1
    world.say(f'“I want to go now!” {hero.label.capitalize()} barked.')
    world.say(f'“We will,” said {stylist.id}, “if you hold still for the taper.”')
    world.para()
    hero.memes["resolve"] += 1
    hero.meters["snip"] += 1
    hero.meters["style"] += 1
    hero.memes["pride"] += 1
    hero.memes["worry"] = 0.0
    hero.memes["frustration"] = 0.0
    world.say(f"{stylist.id} finished the taper, and {hero.label}'s fur {style.finish}.")
    world.say(f"{hero.label.capitalize()} trotted out ready to {quest.verb}, proud of the neat line along the neck and ears.")
    world.facts.update(style=style, quest=quest, place=world.place, resolved=True)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=[
            f"Write an adventure story about a terrier, a taper style, and a quest.",
            f"Tell a child-friendly story where {hero.label} asks for {style.label} before a journey.",
            f"Write a short tale with dialogue, conflict, and a brave ending image.",
        ],
        story_qa=[
            QAItem(
                question=f"What did {hero.label.capitalize()} want before the quest?",
                answer=f"{hero.label.capitalize()} wanted {style.phrase} before {quest.verb}.",
            ),
            QAItem(
                question="Why was there conflict in the story?",
                answer=f"There was conflict because {hero.label} wanted to rush off, but the taper still needed careful trimming and the ears had to stay safe.",
            ),
            QAItem(
                question="How did the story end?",
                answer=f"It ended with {hero.label.capitalize()} looking neat and ready to {quest.verb} with a fresh taper style.",
            ),
        ],
        world_qa=[
            QAItem(
                question="What is a terrier?",
                answer="A terrier is a small, lively dog that often looks bold and ready to explore.",
            ),
            QAItem(
                question="What is a taper style?",
                answer="A taper style is a haircut or trim that gets shorter in a smooth, tidy way.",
            ),
            QAItem(
                question="Why are scissors used carefully near a dog's ears?",
                answer="Scissors are used carefully near a dog's ears because ears are sensitive and need gentle handling.",
            ),
        ],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            parts = []
            if meters:
                parts.append(f"meters={meters}")
            if memes:
                parts.append(f"memes={memes}")
            print(f"  {e.id:8} ({e.kind:9}) {' '.join(parts)}")
    if qa:
        print()
        print("== Q&A ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def asp_valid_stories() -> list[tuple]:
    return []


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in [
            StoryParams("barn", "taper", "showday", "terrier"),
            StoryParams("shop", "taper", "mousetrail", "spot"),
            StoryParams("garden", "taper", "showday", "terrier"),
        ]:
            samples.append(generate(p))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
