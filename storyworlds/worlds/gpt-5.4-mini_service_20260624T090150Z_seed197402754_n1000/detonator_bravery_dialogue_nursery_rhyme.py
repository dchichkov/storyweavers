#!/usr/bin/env python3
"""
A tiny story world for a nursery-rhyme style tale about bravery, dialogue, and
a careful little detonator that starts a harmless rocket lantern show.

Initial seed tale:
---
In a snug little town, Pip the mouse found a brass detonator on a toy stage.
Pip was scared to touch it, because it had a stern little label: "Press me to
start the show."
Pip's sister Dot said, "You can do it. I'll stand beside you."
Pip took a brave breath, pressed the detonator, and the lanterns popped up
into the sky like bright flowers. Pip laughed, and the whole crowd sang.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "girl", "boy", "child"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    indoors: bool = True
    sound: str = ""


@dataclass
class Switch:
    id: str
    label: str
    phrase: str
    effect: str
    safe: bool = True
    story_label: str = "detonator"


@dataclass
class StoryParams:
    place: str
    switch: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


PLACES = {
    "stage": Place(name="the toy stage", indoors=True, sound="a tiny brass chime"),
    "garden": Place(name="the moonlit garden", indoors=False, sound="soft rustles"),
    "hall": Place(name="the candle hall", indoors=True, sound="a warm echo"),
}

SWITCHES = {
    "detonator": Switch(
        id="detonator",
        label="detonator",
        phrase="a little brass detonator with a red button",
        effect="the lanterns leapt up and bloomed like flowers",
        safe=True,
        story_label="detonator",
    ),
}

HEROES = ["Pip", "Mina", "Toby", "Luna", "Ned", "Dot"]
HELPERS = ["Dot", "Bee", "Moss", "Juno", "Wren", "Kit"]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


def rhyme_end(word: str) -> str:
    return {
        "scared": "hearts",
        "brave": "wave",
        "night": "light",
        "show": "glow",
        "flowers": "showers",
        "start": "heart",
    }.get(word, word)


def _resolve_prompt_thought(world: World, hero: Entity, sw: Switch) -> None:
    if "fear" in hero.memes and hero.memes["fear"] >= THRESHOLD:
        world.say(
            f"{hero.id} peeped at {sw.label} and whispered, "
            f"\"What if I make a big mistake?\""
        )


def _helper_dialogue(world: World, helper: Entity, hero: Entity) -> None:
    helper.memes["support"] = helper.memes.get("support", 0) + 1
    hero.memes["courage"] = hero.memes.get("courage", 0) + 1
    world.say(
        f"\"Take my paw,\" said {helper.id}. \"A brave step is only one small try.\""
    )


def _press_switch(world: World, hero: Entity, sw: Switch) -> None:
    if sw.id in world.fired:
        return
    world.fired.add(sw.id)
    hero.meters["action"] = hero.meters.get("action", 0) + 1
    hero.memes["courage"] = hero.memes.get("courage", 0) + 1
    world.facts["effect"] = sw.effect
    world.say(
        f"{hero.id} took a breath, pressed the {sw.label}, and "
        f"{sw.effect}."
    )


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    sw = SWITCHES[params.switch]
    world = World(place)

    hero = world.add(Entity(id=params.hero_name, kind="character", type="mouse"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="mouse"))
    switch = world.add(Entity(
        id="switch",
        kind="thing",
        type="switch",
        label=sw.label,
        phrase=sw.phrase,
        owner=hero.id,
    ))

    hero.memes["fear"] = 1.0
    world.facts.update(hero=hero, helper=helper, switch=switch, place=place, switch_def=sw)

    world.say(
        f"At {place.name}, where the air held {place.sound}, lived little {hero.id}."
    )
    world.say(
        f"{hero.id} found {sw.phrase} beside a painted sign that said, "
        f"\"Press me to start the show.\""
    )
    world.say(
        f"{hero.id} shook their whiskers and said, \"Oh dear, that looks quite bold.\""
    )

    world.para()
    _resolve_prompt_thought(world, hero, sw)
    _helper_dialogue(world, helper, hero)

    world.para()
    world.say(
        f"\"I can be brave,\" said {hero.id}. \"I will try, and I will try slow.\""
    )
    _press_switch(world, hero, sw)
    world.say(
        f"Then the crowd cheered, \"Hooray!\" and the lanterns danced in a row."
    )
    world.say(
        f"{hero.id} laughed, {helper.id} clapped, and the little show shone on and on."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    sw = f["switch_def"]
    return [
        'Write a short nursery-rhyme story about a child who fears a "detonator" but finds courage.',
        f'Tell a gentle rhyme where {hero.id} and {helper.id} talk together and press a {sw.label}.',
        f'Write a story for little children that includes the word "{sw.story_label}" and ends in brave cheering.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    sw = f["switch_def"]
    place = f["place"]
    return [
        QAItem(
            question=f"What did {hero.id} find at {place.name}?",
            answer=f"{hero.id} found {sw.phrase} at {place.name}.",
        ),
        QAItem(
            question=f"Why did {hero.id} hesitate before pressing the {sw.label}?",
            answer=f"{hero.id} hesitated because the {sw.label} looked bold, and {hero.id} was scared of making a mistake.",
        ),
        QAItem(
            question=f"What did {helper.id} say to help {hero.id} be brave?",
            answer=f"{helper.id} said, \"Take my paw. A brave step is only one small try.\"",
        ),
        QAItem(
            question=f"What happened after {hero.id} pressed the {sw.label}?",
            answer=f"After {hero.id} pressed the {sw.label}, {f['effect']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does brave mean?",
            answer="Brave means doing something scary or hard even though you feel worried.",
        ),
        QAItem(
            question="What is dialogue in a story?",
            answer="Dialogue is when characters speak to each other using words in quotation marks.",
        ),
        QAItem(
            question="What is a detonator?",
            answer="A detonator is a small device or switch that starts something bigger. In a safe story, it can simply begin a show.",
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_brave(H) :- courage(H).
show_starts(S) :- pressed(S), safe(S).
resolved_story :- hero_brave(H), helper_support(H2), show_starts(S).
#show hero_brave/1.
#show show_starts/1.
#show resolved_story/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("courage", "hero"),
        asp.fact("helper_support", "helper"),
        asp.fact("pressed", "switch"),
        asp.fact("safe", "switch"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show hero_brave/1."))
    atoms = set(asp.atoms(model, "hero_brave"))
    ok = atoms == {("hero",)}
    if ok:
        print("OK: ASP gate matches Python reasonableness.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme story world about bravery and a detonator.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--switch", choices=SWITCHES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    switch = args.switch or "detonator"
    if switch not in SWITCHES:
        raise StoryError("Only the safe story-world detonator is available.")
    name = args.name or rng.choice(HEROES)
    helper = args.helper or rng.choice([h for h in HELPERS if h != name])
    if helper == name:
        helper = "Dot"
    return StoryParams(place=place, switch=switch, hero_name=name, helper_name=helper)


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
        print(asp_program("#show resolved_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show resolved_story/0."))
        print("ASP model:")
        print(sorted(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [
            generate(StoryParams(place=p, switch="detonator", hero_name=h, helper_name=hh))
            for p in PLACES
            for h, hh in [("Pip", "Dot")]
        ]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        if len(samples) > 1:
            p = sample.params
            header = f"### {p.hero_name} at {p.place}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
