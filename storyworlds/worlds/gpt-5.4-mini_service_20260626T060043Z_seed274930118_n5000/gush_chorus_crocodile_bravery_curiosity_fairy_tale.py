#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gush_chorus_crocodile_bravery_curiosity_fairy_tale.py
==============================================================================================================

A small fairy-tale storyworld about a curious child, a royal chorus, a river
gush, and a crocodile who looks scary until the truth comes out.

Seed tale inspiration:
---
On a misty evening, a child heard a chorus singing by the river. The song was
so bright that the water began to gush over the stones. A crocodile rose from
the reeds, and everyone feared it. But the child stayed brave and curious,
followed the song, and discovered the crocodile was guarding a lost bell for
the chorus. The bell rang, the river calmed, and the crocodile became a friend.
---

This script turns that premise into a tiny simulated domain with:
- physical meters: river water, reeds, bell, distance, dusk
- emotional memes: bravery, curiosity, fear, relief, trust

The story is built from state changes rather than a frozen paragraph.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    river_name: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    chorus: str
    crocodile: str
    seed: Optional[int] = None


SETTINGS = {
    "old_bridge": Setting(place="the old bridge", river_name="the silver river", affords={"gush", "chorus"}),
    "lily_bank": Setting(place="the lily bank", river_name="the silver river", affords={"gush", "chorus"}),
}

HERO_NAMES = ["Mira", "Nell", "Pip", "Toby", "Wren", "Lina"]
HERO_TYPES = ["girl", "boy"]
CHORUS_NAMES = ["the moon chorus", "the lantern chorus", "the brook chorus"]
CROCODILE_NAMES = ["Glim", "Mossjaw", "Tilla", "Crook", "Bracken"]

# Small consistent palette of story options.
CURATED = [
    StoryParams(place="old_bridge", hero_name="Mira", hero_type="girl", chorus="moon", crocodile="Glim"),
    StoryParams(place="lily_bank", hero_name="Pip", hero_type="boy", chorus="lantern", crocodile="Mossjaw"),
]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

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

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def meter(x: float) -> float:
    return round(x, 3)


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []

    river = world.get("river")
    gorge = world.get("gorge")
    bell = world.get("bell")
    hero = world.get("hero")
    croc = world.get("crocodile")
    chorus = world.get("chorus")

    # If the gush is strong, the river rises and the bridge feels unsafe.
    if river.meters.get("gush", 0.0) >= THRESHOLD and "rising" not in world.fired:
        world.fired.add("rising")
        river.meters["water"] = meter(river.meters.get("water", 0.0) + 1.0)
        hero.memes["curiosity"] = meter(hero.memes.get("curiosity", 0.0) + 0.5)
        out.append("The silver river began to rise over the stones.")

    # If the chorus sings, the bell can be heard and trust can grow.
    if chorus.meters.get("song", 0.0) >= THRESHOLD and "heard_bell" not in world.fired:
        world.fired.add("heard_bell")
        bell.meters["ring"] = meter(bell.meters.get("ring", 0.0) + 1.0)
        out.append("A tiny bell sound answered the singing from the reeds.")

    # If the hero is brave and curious, they approach and discover the crocodile is guarding.
    if hero.memes.get("bravery", 0.0) >= THRESHOLD and hero.memes.get("curiosity", 0.0) >= THRESHOLD and "approach" not in world.fired:
        world.fired.add("approach")
        hero.meters["distance"] = meter(0.0)
        croc.memes["fear"] = meter(max(0.0, croc.memes.get("fear", 0.0) - 0.5))
        croc.memes["trust"] = meter(croc.memes.get("trust", 0.0) + 0.5)
        out.append("The child stepped closer instead of running away.")

    # If the bell is found, the crocodile relaxes and the chorus rejoices.
    if bell.meters.get("found", 0.0) >= THRESHOLD and "resolve" not in world.fired:
        world.fired.add("resolve")
        river.meters["gush"] = meter(0.0)
        croc.memes["trust"] = meter(croc.memes.get("trust", 0.0) + 1.0)
        hero.memes["relief"] = meter(hero.memes.get("relief", 0.0) + 1.0)
        chorus.meters["song"] = meter(chorus.meters.get("song", 0.0) + 1.0)
        out.append("The river settled, and the song grew warm and bright.")

    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity("hero", kind="character", type=params.hero_type, label=params.hero_name, traits=["curious", "brave"]))
    chorus = world.add(Entity("chorus", kind="group", type="chorus", label=f"the {params.chorus} chorus", plural=True))
    croc = world.add(Entity("crocodile", kind="character", type="crocodile", label=params.crocodile, traits=["quiet", "guarding"]))
    river = world.add(Entity("river", type="river", label=setting.river_name))
    bell = world.add(Entity("bell", type="thing", label="lost bell"))
    gorge = world.add(Entity("gorge", type="place", label=setting.place))

    river.meters["gush"] = 0.0
    river.meters["water"] = 0.0
    chorus.meters["song"] = 0.0
    hero.meters["distance"] = 3.0
    hero.memes["bravery"] = 0.0
    hero.memes["curiosity"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["relief"] = 0.0
    croc.memes["trust"] = 0.0
    croc.memes["fear"] = 0.0
    bell.meters["found"] = 0.0

    world.facts.update(hero=hero, chorus=chorus, crocodile=croc, river=river, bell=bell, gorge=gorge)
    return world


def setup(world: World) -> None:
    hero = world.get("hero")
    chorus = world.get("chorus")
    croc = world.get("crocodile")
    river = world.get("river")

    world.say(f"Once upon a time, {hero.label} came to {world.setting.place} beside {world.setting.river_name}.")
    world.say(f"At dusk, {chorus.label} began to sing in a soft, round chorus.")
    hero.memes["curiosity"] = meter(hero.memes.get("curiosity", 0.0) + 1.0)
    world.say(f"{hero.label} listened closely, because {hero.pronoun('subject')} had a curious heart and liked to learn where songs came from.")
    croc.memes["fear"] = meter(1.0)
    world.say(f"Then a crocodile named {croc.label} lifted its head from the reeds, and the bank fell quiet.")
    river.meters["gush"] = meter(1.0)
    world.say("The river answered with a sudden gush over the stones, as if the water itself had joined the song.")
    propagate(world, narrate=True)


def turn(world: World) -> None:
    hero = world.get("hero")
    croc = world.get("crocodile")
    chorus = world.get("chorus")
    bell = world.get("bell")

    hero.memes["bravery"] = meter(hero.memes.get("bravery", 0.0) + 1.0)
    world.say(f"Though the crocodile looked frightful, {hero.label} did not run. {hero.pronoun('subject').capitalize()} took one brave step, then another.")
    chorus.meters["song"] = meter(chorus.meters.get("song", 0.0) + 1.0)
    world.say("The chorus sang louder, and the tune pointed toward the reeds like a little lantern.")
    bell.meters["found"] = 1.0
    world.say(f"There, under a fern, {hero.label} found the lost bell the crocodile had been guarding.")
    croc.memes["trust"] = meter(croc.memes.get("trust", 0.0) + 1.0)
    propagate(world, narrate=True)


def end(world: World) -> None:
    hero = world.get("hero")
    croc = world.get("crocodile")
    chorus = world.get("chorus")
    river = world.get("river")
    bell = world.get("bell")

    world.say(f"{hero.label} rang the bell, and the chorus swelled into a glad, shimmering song.")
    world.say(f"The crocodile was not a monster at all; {croc.label} had been keeping the bell safe until someone kind and bold could find it.")
    world.say(f"The gush faded, the river settled, and {hero.label} smiled with relief and pride.")
    world.say(f"By the end, the child had more bravery in {hero.pronoun('possessive')} chest, more curiosity in {hero.pronoun('possessive')} mind, and a new friend by the riverbank.")
    world.say("And so the moon listened, the chorus sang, and the crocodile kept watch as a friend instead of a fright.")
    world.facts["ending"] = {
        "bravery": hero.memes.get("bravery", 0.0),
        "curiosity": hero.memes.get("curiosity", 0.0),
        "trust": croc.memes.get("trust", 0.0),
        "gush": river.meters.get("gush", 0.0),
        "bell_found": bell.meters.get("found", 0.0),
        "song": chorus.meters.get("song", 0.0),
    }


def generate_story(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params)
    setup(world)
    world.para()
    turn(world)
    world.para()
    end(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    chorus = f["chorus"]
    croc = f["crocodile"]
    return [
        f'Write a fairy-tale story for a young child about {hero.label}, a chorus, and a crocodile beside a river.',
        f"Tell a gentle story where {hero.label} uses bravery and curiosity to learn why {croc.label} is near the reeds.",
        f'Write a short tale that includes a sudden gush, a singing chorus, and a crocodile who turns out to be kind.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    chorus = f["chorus"]
    croc = f["crocodile"]
    river = f["river"]
    bell = f["bell"]
    ending = f["ending"]
    return [
        QAItem(
            question=f"Who followed the singing chorus near {river.label}?",
            answer=f"{hero.label} followed the singing chorus because {hero.pronoun('subject')} was both brave and curious.",
        ),
        QAItem(
            question="Why did the crocodile look scary at first?",
            answer=f"The crocodile looked scary because it rose from the reeds near the rushing river, before anyone knew it was guarding the bell.",
        ),
        QAItem(
            question="What was the crocodile really doing by the river?",
            answer=f"{croc.label} was guarding the lost bell for the chorus until a brave child could find it.",
        ),
        QAItem(
            question="What changed after the bell was found?",
            answer=f"The gush faded, the river settled, and the chorus sang a glad ending song. {hero.label} felt proud and relieved, and the crocodile became a friend.",
        ),
        QAItem(
            question="How did bravery and curiosity help in the story?",
            answer=f"Bravery helped {hero.label} keep moving toward the reeds, and curiosity helped {hero.pronoun('subject')} look closely enough to discover the bell and understand the crocodile.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chorus?",
            answer="A chorus is a group of voices singing together, often in a repeated and harmonious way.",
        ),
        QAItem(
            question="What does gush mean?",
            answer="To gush means to flow or pour out quickly and strongly, like water rushing over stones.",
        ),
        QAItem(
            question="What is a crocodile?",
            answer="A crocodile is a large reptile with strong jaws, a long tail, and a body that is well suited to living near water.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is the feeling that helps someone do what is right or needed even when they feel scared.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn, ask questions, and discover what is hidden or unknown.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {e.label} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
chorus(C) :- chorus_name(C).
crocodile(K) :- crocodile_name(K).

brave(H) :- bravery(H), curiosity(H).
gush_rises(R) :- gush(R), strong(R).
finds_bell(H) :- brave(H), curious(H), bell(B), found(B).
guarding(K) :- crocodile(K), bell(B), safe_until_found(K,B).

resolve(H,K) :- finds_bell(H), guarding(K).
good_story(H,K) :- resolve(H,K), chorus(C), song(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in HERO_NAMES:
        lines.append(asp.fact("hero_name", name))
    for c in CHORUS_NAMES:
        lines.append(asp.fact("chorus_name", c))
    for c in CROCODILE_NAMES:
        lines.append(asp.fact("crocodile_name", c))
    lines.append(asp.fact("theme", "bravery"))
    lines.append(asp.fact("theme", "curiosity"))
    lines.append(asp.fact("theme", "gush"))
    lines.append(asp.fact("theme", "chorus"))
    lines.append(asp.fact("theme", "crocodile"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    # Light parity check: program is syntactically valid and exposes intended atoms.
    model = asp.one_model(asp_program("#show theme/1."))
    themes = sorted(set(asp.atoms(model, "theme")))
    expected = [("bravery",), ("chorus",), ("crocodile",), ("gush",), ("curiosity",)]
    if themes == expected:
        print(f"OK: ASP facts expose {len(themes)} themes.")
        return 0
    print("MISMATCH between ASP themes and expected set:")
    print("  got:", themes)
    print("  expected:", expected)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about a gush, a chorus, and a crocodile.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name", dest="hero_name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--chorus")
    ap.add_argument("--crocodile")
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
    place = args.place or rng.choice(list(SETTINGS))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    chorus = args.chorus or rng.choice(["moon", "lantern", "brook"])
    crocodile = args.crocodile or rng.choice(CROCODILE_NAMES)
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, chorus=chorus, crocodile=crocodile)


def generate(params: StoryParams) -> StorySample:
    return generate_story(params)


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
        print(asp_program("#show theme/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = ""
        if len(samples) > 1:
            header = f"### story {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
