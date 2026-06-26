#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/fracture_sicken_spit_dialogue_rhyme_rhyming_story.py
===============================================================================================================================

A small rhyming storyworld about a child, a fragile prize, a sour mistake, and
a gentle fix. The seed words are woven into the premise and outcomes:

- fracture: something fragile can crack or break
- sicken: something sour or spoiled can make a child feel ill
- spit: the child may spit out something bitter or yucky

The story is told in a child-facing, rhyming style with dialogue and a
state-driven turn-and-resolution arc.
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    fragile: bool = False
    edible: bool = False
    bitter: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def __post_init__(self) -> None:
        for k in ("fracture", "sicken", "spit", "care", "joy", "worry", "relief"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    weather: str = "soft"
    affords: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    verb: str
    rhyme: str
    risk: str
    consequence: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    rhyme: str
    guards: set[str] = field(default_factory=set)
    cures: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", weather="warm", affords={"sip", "stir"}),
    "garden": Setting(place="the garden", weather="breezy", affords={"sip", "stir"}),
    "porch": Setting(place="the porch", weather="soft", affords={"sip", "stir"}),
}

EVENTS = {
    "sour_sip": Event(
        id="sour_sip",
        verb="sip the sour pink drink",
        rhyme="sip and trip",
        risk="sicken",
        consequence="it made the tummy flip and sicken",
        keyword="sour",
        tags={"sour", "spit", "sicken"},
    ),
    "sharp_bite": Event(
        id="sharp_bite",
        verb="try the sharp berry pie",
        rhyme="bite and plight",
        risk="spit",
        consequence="it was so sharp that the child had to spit",
        keyword="berry",
        tags={"berry", "spit", "sour"},
    ),
    "brittle_bowl": Event(
        id="brittle_bowl",
        verb="lift the brittle blue bowl",
        rhyme="lift and shift",
        risk="fracture",
        consequence="it could crack and fracture with one hard shift",
        keyword="brittle",
        tags={"fracture"},
    ),
}

REMEDIES = {
    "honey": Remedy(
        id="honey",
        label="honey toast",
        phrase="warm honey toast",
        rhyme="sweet and neat",
        guards={"sicken", "spit"},
        cures={"sicken", "spit"},
    ),
    "wrap": Remedy(
        id="wrap",
        label="a soft cloth wrap",
        phrase="a soft cloth wrap",
        rhyme="neat and seat",
        guards={"fracture"},
        cures={"fracture"},
    ),
    "milk": Remedy(
        id="milk",
        label="cool milk",
        phrase="cool milk",
        rhyme="kind and mild",
        guards={"sicken"},
        cures={"sicken"},
    ),
}

NAMES = ["Mila", "Pip", "Nora", "Toby", "Luna", "Finn", "Zee", "Bea"]
PARENTS = ["mother", "father"]
TRAITS = ["brave", "tiny", "cheery", "spry", "gentle", "bright"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    event: str
    remedy: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helper logic
# ---------------------------------------------------------------------------
def event_risk(event: Event, remedy: Remedy) -> bool:
    return bool(event.risk in remedy.cures or event.risk in remedy.guards)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for ev in EVENTS.values():
            if "sip" not in setting.affords:
                continue
            for rm in REMEDIES.values():
                if event_risk(ev, rm):
                    combos.append((place, ev.id, rm.id))
    return combos


def explain_rejection(event: Event, remedy: Remedy) -> str:
    return (
        f"(No story: {remedy.label} does not reasonably fix a {event.risk} problem "
        f"caused by {event.verb}. Choose a remedy that actually guards the same risk.)"
    )


def explain_gender(gender: str, name: str) -> str:
    return f"(No story: {name} is not a natural fit for gender={gender} in this tiny cast.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
event_risk(E,R) :- event(E), risk(E,X), remedy(R), cures(R,X).
valid(Place,E,R) :- setting(Place), event(E), remedy(R), afford(Place,sip), event_risk(E,R).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
        lines.append(asp.fact("afford", place, "sip"))
    for ev in EVENTS.values():
        lines.append(asp.fact("event", ev.id))
        lines.append(asp.fact("risk", ev.id, ev.risk))
    for rm in REMEDIES.values():
        lines.append(asp.fact("remedy", rm.id))
        for c in rm.cures:
            lines.append(asp.fact("cures", rm.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))

    event = EVENTS[params.event]
    remedy = REMEDIES[params.remedy]

    fragile_item = world.add(Entity(
        id="bowl",
        type="bowl",
        label="blue bowl",
        phrase="a blue bowl",
        owner=hero.id,
        caretaker=parent.id,
        fragile=True,
    ))

    world.facts.update(hero=hero, parent=parent, event=event, remedy=remedy, item=fragile_item)

    # Opening rhyme
    world.say(
        f"In {setting.place}, where the warm light gleamed, {hero.id} had a day that sparkled and dreamed."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} was a {params.trait} little {params.gender}, all quick with delight, "
        f"and {hero.pronoun('possessive')} {fragile_item.label} looked shiny and bright."
    )

    # Dialogue setup
    world.say(
        f'"May I {event.verb}?" {hero.id} sang with glee. "It looks like a rhyme made for you and me!"'
    )
    world.say(
        f'"Not yet," said the {parent.label}, with a soft little sigh. '
        f'"That choice could {event.consequence}, and then you might cry."'
    )

    # Tension
    hero.memes["worry"] += 1
    hero.meters["sicken"] += 1 if event.risk == "sicken" else 0
    hero.meters["fracture"] += 1 if event.risk == "fracture" else 0
    hero.meters["spit"] += 1 if event.risk == "spit" else 0

    if event.risk == "sicken":
        world.say(
            f"{hero.id} took one sip, then wrinkled {hero.pronoun('possessive')} nose in a frown. "
            f'"Blech! I feel a bit sickened," {hero.pronoun("subject")} said.'
        )
    elif event.risk == "spit":
        world.say(
            f"{hero.id} took one bite, then made a face so grim. "
            f'"Yuck! I must spit this out," {hero.pronoun("subject")} said to him.'
        )
    else:
        world.say(
            f"{hero.id} gave the bowl one careful lift, but it shivered and shook. "
            f'"Crack!" went the rim with a tiny sharp look.'
        )

    # Parent sees the problem and offers a fix
    if event.risk == "fracture":
        world.say(
            f'"That bowl is too brittle," said the {parent.label}. "Let\'s wrap it with care, '
            f"so it will not fracture in there.""
        )
    elif event.risk == "sicken":
        world.say(
            f'"That drink is too sour," said the {parent.label}. "Let\'s add something sweet, '
            f"so your tummy can meet a treat.""
        )
    else:
        world.say(
            f'"That bite is too sharp," said the {parent.label}. "Let\'s trade it for something soft, '
            f"so your mouth can smile off the chart.""
        )

    # Resolution
    remedy_obj = world.add(Entity(
        id=remedy.id,
        type=remedy.label,
        label=remedy.label,
        phrase=remedy.phrase,
        caretaker=parent.id,
    ))

    if event.risk in remedy.cures:
        hero.memes["relief"] += 1
        hero.memes["joy"] += 1
        world.say(
            f"The {parent.label} brought {remedy.phrase}, and the mood turned kind and light."
        )
        if event.risk == "fracture":
            world.say(
                f"They set the {fragile_item.label} in a soft cloth wrap; it sat snug and neat."
            )
        elif event.risk == "sicken":
            world.say(
                f"{hero.id} sipped the gentle treat and smiled, for the sour was now sweet."
            )
        else:
            world.say(
                f"{hero.id} chose a softer bite, and there was no need to spit at all."
            )
        world.say(
            f'"Ahhh," said {hero.id}. "That feels just right!" And the day stayed merry till evening fall.'
        )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, event, remedy = f["hero"], f["event"], f["remedy"]
    return [
        f'Write a short rhyming story for a small child where {hero.id} wants to {event.verb}.',
        f'Create a gentle dialogue story that uses the words fracture, sicken, and spit in a child-friendly way.',
        f'Write a tiny story with rhyme, where a parent and child choose {remedy.label} to fix a problem caused by {event.keyword}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, event, remedy = f["hero"], f["parent"], f["event"], f["remedy"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {event.verb}.",
        ),
        QAItem(
            question=f"Why did the {parent.label} worry?",
            answer=f"The {parent.label} worried because {event.consequence}.",
        ),
        QAItem(
            question=f"What helped the child feel better or safer?",
            answer=f"{remedy.label} helped, because it was the gentle fix for the problem.",
        ),
        QAItem(
            question=f"What did the story say about fracture, sicken, or spit?",
            answer=(
                f"The story used all three words: something could fracture, the child could feel sicken, "
                f"and the child might spit out something yucky."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does fragile mean?",
            answer="Fragile means something can break or crack easily, so it needs careful hands.",
        ),
        QAItem(
            question="What does sour food sometimes make people do?",
            answer="Sour food can make people pucker, spit it out, or want something sweeter instead.",
        ),
        QAItem(
            question="Why do people use a soft wrap for a breakable thing?",
            answer="A soft wrap can help protect a breakable thing from bumps and knocks.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming storyworld with dialogue.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--event", choices=EVENTS.keys())
    ap.add_argument("--remedy", choices=REMEDIES.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.event and args.remedy:
        ev = EVENTS[args.event]
        rm = REMEDIES[args.remedy]
        if not event_risk(ev, rm):
            raise StoryError(explain_rejection(ev, rm))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.event is None or c[1] == args.event)
        and (args.remedy is None or c[2] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, event, remedy = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, event=event, remedy=remedy, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} valid combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in [
            StoryParams("kitchen", "sour_sip", "honey", "Mila", "girl", "mother", "bright"),
            StoryParams("garden", "sharp_bite", "honey", "Pip", "boy", "father", "cheery"),
            StoryParams("porch", "brittle_bowl", "wrap", "Nora", "girl", "mother", "gentle"),
        ]:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
