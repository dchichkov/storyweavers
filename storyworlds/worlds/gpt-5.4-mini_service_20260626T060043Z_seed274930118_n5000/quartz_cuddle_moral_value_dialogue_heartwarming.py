#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/quartz_cuddle_moral_value_dialogue_heartwarming.py
=========================================================================================================

A small heartwarming story world about a child, a special quartz stone, and a
gentle moral turn through dialogue and kindness.

Premise:
- A child treasures a shiny quartz.
- Another child wants to cuddle with the same blanket/spot.
- A small hurt feeling appears when the quartz is not shared.
- A parent guides the child toward a kinder choice.
- The child shares the quartz and a cuddle, and the story ends with warmth.

This is a standalone Storyweavers world script.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    holds: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = False


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    sparkle: str
    value: str


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    trait: str
    treasure: str = "quartz"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "windowseat": Setting(place="the window seat", indoor=True),
    "gardenbench": Setting(place="the garden bench", indoor=False),
    "bedroom": Setting(place="the bedroom", indoor=True),
}

TREASURES = {
    "quartz": Treasure(
        id="quartz",
        label="quartz",
        phrase="a smooth pink quartz",
        sparkle="sparkled like a tiny morning star",
        value="precious",
    )
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Noah", "Ben", "Theo", "Finn", "Max"]
TRAITS = ["gentle", "curious", "kind", "quiet", "bright", "careful"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_story_state(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.trait],
        meters={"joy": 0.0, "hurt": 0.0, "sharing": 0.0},
        memes={"love": 0.0, "stinginess": 0.0, "warmth": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        meters={"calm": 1.0},
        memes={"wisdom": 1.0},
    ))
    friend = world.add(Entity(
        id="Friend",
        kind="character",
        type="girl" if params.gender == "boy" else "boy",
        label="the friend",
        meters={"lonely": 0.0, "joy": 0.0},
        memes={"hope": 0.0},
    ))
    treasure = world.add(Entity(
        id="treasure",
        type="thing",
        label="quartz",
        phrase=TREASURES["quartz"].phrase,
        owner=hero.id,
        carries=hero.id,
        meters={"clean": 1.0, "shine": 1.0},
        memes={"special": 1.0},
    ))
    world.facts.update(hero=hero, parent=parent, friend=friend, treasure=treasure, params=params)
    return world


def predict_outcome(world: World) -> dict:
    sim = world.copy()
    hero = sim.get(sim.facts["hero"].id)
    friend = sim.get(sim.facts["friend"].id)
    treasure = sim.get(sim.facts["treasure"].id)
    hero.meters["sting"] = hero.meters.get("sting", 0.0) + 1.0
    friend.meters["lonely"] = friend.meters.get("lonely", 0.0) + 1.0
    treasure.memes["special"] = treasure.memes.get("special", 0.0) + 0.0
    return {
        "share_needed": True,
        "hurt_risk": friend.meters["lonely"] >= THRESHOLD,
    }


def tell(world: World) -> None:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    friend = world.facts["friend"]
    treasure = world.facts["treasure"]
    place = world.setting.place

    world.say(
        f"{hero.id} was a little {next(t for t in hero.traits if t != 'little')} {hero.type} "
        f"who loved {treasure.label} because {treasure.phrase} {treasure.sparkle}."
    )
    world.say(
        f"{hero.id} kept {treasure.pronoun('object') if hasattr(treasure, 'pronoun') else 'it'} close "
        f"and felt proud of how special it was."
    )

    world.para()
    world.say(f"One afternoon at {place}, {friend.id} came close with open arms and a sleepy smile.")
    world.say(f'"Can I cuddle next to you?" {friend.id} asked. "Your quartz looks so pretty."')

    world.para()
    pred = predict_outcome(world)
    hero.memes["stinginess"] += 1.0
    hero.meters["hurt"] += 1.0
    world.say(
        f"{hero.id} hugged the quartz tighter and said, "
        f"'"No, this is mine."'
    )
    if pred["hurt_risk"]:
        world.say(
            f"{parent.id} saw {friend.id}'s smile fade and said, "
            f'"A treasure can be shared without disappearing."'
        )
        world.say(
            f'"If you let {friend.id} cuddle beside you, the quartz will still be yours," '
            f"{parent.id} said softly."
        )

    world.para()
    hero.meters["hurt"] = 0.0
    hero.meters["sharing"] = 1.0
    hero.meters["joy"] = 1.0
    hero.memes["warmth"] = 1.0
    friend.meters["joy"] = 1.0
    world.say(
        f"{hero.id} looked at the glowing stone, then at {friend.id}, and took a small breath."
    )
    world.say(
        f'"You can cuddle with me," {hero.id} said. "We can share the cozy spot, and I will still keep my quartz."'
    )
    world.say(
        f"{friend.id} curled up beside {hero.id}, and the two of them sat together while the quartz rested safely in {hero.id}'s hands."
    )
    world.say(
        f"By the end, {hero.id} felt warmer from being kind, and the quartz seemed to shine even brighter."
    )

    world.facts.update(resolved=True)


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    return [
        f'Write a heartwarming story for young children about a child named {hero.id}, a quartz, and a cuddle.',
        f"Tell a gentle story where {hero.id} learns a moral value about sharing a special quartz when a friend wants to cuddle nearby.",
        f"Write a short dialogue-driven story that ends with kindness, warmth, and a shining quartz.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    treasure: Entity = f["treasure"]  # type: ignore[assignment]
    place = world.setting.place

    return [
        QAItem(
            question=f"What special thing did {hero.id} love in the story?",
            answer=f"{hero.id} loved a quartz stone that stayed close in {hero.id}'s hands.",
        ),
        QAItem(
            question=f"Who wanted to cuddle near {hero.id} at {place}?",
            answer=f"{friend.id} wanted to cuddle beside {hero.id} and enjoy the cozy spot.",
        ),
        QAItem(
            question=f"What did {parent.id} teach {hero.id} about the quartz?",
            answer="The parent taught that something special can be shared without being lost.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} sharing a cuddle, keeping the quartz safe, and feeling kinder.",
        ),
        QAItem(
            question=f"Why did the quartz still matter at the end?",
            answer=f"The quartz still mattered because it was {hero.id}'s treasure, even after {hero.id} shared the cozy moment.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is quartz?",
            answer="Quartz is a hard mineral found in rocks, and it can look clear, pink, or white and shine in the light.",
        ),
        QAItem(
            question="What does cuddle mean?",
            answer="To cuddle means to hold someone close in a warm, gentle way.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good idea about how to treat others, like sharing, kindness, and honesty.",
        ),
        QAItem(
            question="What is dialogue in a story?",
            answer="Dialogue is the words characters say to each other in the story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World QA ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(windowseat).
place(gardenbench).
place(bedroom).

treasure(quartz).
feature(moral_value).
feature(dialogue).
style(heartwarming).

want_share(H) :- hero(H), treasure(quartz), feature(moral_value).
can_cuddle(H) :- hero(H), feature(dialogue).

good_story(P, quartz, cuddle) :- place(P), treasure(quartz), style(heartwarming), feature(moral_value), feature(dialogue).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "child"),
        asp.fact("treasure", "quartz"),
        asp.fact("feature", "moral_value"),
        asp.fact("feature", "dialogue"),
        asp.fact("style", "heartwarming"),
    ]
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/3."))
    asp_set = set(asp.atoms(model, "good_story"))
    py_set = {(place, "quartz", "cuddle") for place in SETTINGS}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python registry ({len(py_set)} places).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  only in clingo:", sorted(asp_set - py_set))
    print("  only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Resolution and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming quartz-and-cuddle story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    if args.name and not args.gender:
        raise StoryError("If you specify a name, please also specify --gender so the story can sound natural.")
    return StoryParams(place=place, name=name, gender=gender, parent=parent, trait=trait, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = build_story_state(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show good_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_story/3."))
        combos = sorted(set(asp.atoms(model, "good_story")))
        print(f"{len(combos)} compatible stories:")
        for place, treasure, feature in combos:
            print(f"  {place} {treasure} {feature}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(
                place=place,
                name="Mia",
                gender="girl",
                parent="mother",
                trait="kind",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
